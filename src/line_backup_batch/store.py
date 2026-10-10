"""Single existing-lock CAS authority, retaining raw bytes and nanosecond ints."""
import contextlib
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid
from line_backup_acceptance.common import AcceptanceError,json_bytes,utc_now
from line_backup_acceptance.project_binding import ProjectReader,strict_json,validate_config,validate_history,sha
from .schema import require

STATE='state/backup_state.json'
CONFIG='config/line_backup_config.json'
GUI_LEDGER_VERSION='line-backup-gui-ledger-1'
GUI_LEDGER_KINDS={'album_open','dispatch_inputs','chooser_inputs','scroll','menu_calibration','return_navigation'}
PACKAGE_NAMES=['__init__.py','__main__.py','cli.py','content.py','coordinator.py','image_decode.swift',
               'observations.py','schema.py','service.py','state_v3.schema.json','store.py']
SOURCE_PATHS=[f'src/line_backup_acceptance/{n}' for n in
    ['__init__.py','__main__.py','authority.py','cli.py','common.py','project_binding.py','status.py','transaction.py','verifier.py']]
SOURCE_PATHS += [f'src/line_backup_batch/{n}' for n in PACKAGE_NAMES]+['scripts/line_backup_cua_adapter.mjs']
TRANSITION_FIELDS={
    'migrate': {'schema_version','active_batch'},
    'begin': {'active_batch'},
    'admit': {'active_batch'},
    'prepare': {'active_batch','runs','current_run_id','active_writer_id'},
    'calibrate': {'runs','context_lock'},
    'intent': {'runs','active_batch'},
    'dispatch': {'runs'},
    'finalize': {'runs','active_batch','verified_albums','active_writer_id','context_lock'},
    'stop': {'runs','active_batch','active_writer_id','context_lock'},
    'finish': {'active_batch'},
    'release': {'active_batch'},
}

# Nested authority: which fields a specific operation may change inside the current run or
# the active batch. Historical runs and verified albums are append-only/immutable.
RUN_FIELDS={
    'calibrate': {'phase','checkpoint','events'},
    'intent': {'phase','checkpoint','events','intent','intent_state'},
    'dispatch': {'phase','checkpoint','events','intent','intent_state','dispatch_state','dispatch_evidence',
        'manual_reconciliation_required','reconciliation_reason'},
    'finalize': {'phase','checkpoint','events','verification','workflow_outcome','stop_reason'},
    'stop': {'phase','checkpoint','events','workflow_outcome','stop_reason','manual_reconciliation_required','reconciliation_reason'},
}
BATCH_FIELDS={
    'admit': {'manifest_reference','phase'},
    'prepare': {'current_album_run_id','phase','next_index'},
    'intent': {'new_transactions_reserved'},
    'finalize': {'current_album_run_id','next_index'},
    'stop': {'current_album_run_id','phase','stop_reason'},
    'finish': {'phase','stop_reason'},
}

def changed_keys(before,candidate):
    """Type-exact per-key comparison; JSON bytes keep big integers and 1 vs True distinct."""
    return {key for key in set(before)|set(candidate)
        if key not in before or key not in candidate or json_bytes(before[key])!=json_bytes(candidate[key])}

def _events_ok(old,new):
    oe=old.get('events',[]) if isinstance(old,dict) else []
    ne=new.get('events',[])
    require(isinstance(oe,list) and isinstance(ne,list) and len(ne)>=len(oe)
        and all(json_bytes(a)==json_bytes(b) for a,b in zip(oe,ne)),'EVENTS_NOT_APPEND_ONLY')
    require(bool(ne) and json_bytes(new.get('checkpoint'))==json_bytes(ne[-1]),'CHECKPOINT_EVENT_MISMATCH')
    if isinstance(old,dict):
        require(bool(oe) and json_bytes(old.get('checkpoint'))==json_bytes(oe[-1]),'CHECKPOINT_EVENT_MISMATCH')

def validate_nested_delta(before,candidate,operation):
    """Reject any nested mutation outside the current run/batch and the operation's legal fields."""
    br,cr=before.get('runs',[]),candidate.get('runs',[])
    require(isinstance(br,list) and isinstance(cr,list),'TRANSITION_SCOPE')
    if len(cr)==len(br)+1:
        require(operation=='prepare','TRANSITION_SCOPE')
        for old,new in zip(br,cr):
            require(json_bytes(old)==json_bytes(new),'HISTORICAL_RUN_IMMUTABLE')
        fresh=cr[-1];batch=candidate.get('active_batch')
        require(isinstance(batch,dict) and fresh.get('run_id')==batch.get('current_album_run_id')
            and fresh.get('batch_id')==batch.get('batch_id'),'TRANSITION_SCOPE')
        _events_ok(None,fresh)
    else:
        require(len(cr)==len(br),'TRANSITION_SCOPE')
        allowed=RUN_FIELDS.get(operation,set())
        batch=before.get('active_batch')
        current=batch.get('current_album_run_id') if isinstance(batch,dict) else None
        if current is None:current=before.get('current_run_id')
        for old,new in zip(br,cr):
            if json_bytes(old)==json_bytes(new):continue
            require(isinstance(old,dict) and isinstance(new,dict) and old.get('run_id')==new.get('run_id')
                and old.get('run_id')==current,'HISTORICAL_RUN_IMMUTABLE')
            require(changed_keys(old,new)<=allowed,'TRANSITION_SCOPE')
            _events_ok(old,new)
    bv,cv=before.get('verified_albums',[]),candidate.get('verified_albums',[])
    require(isinstance(bv,list) and isinstance(cv,list) and len(cv)>=len(bv)
        and all(json_bytes(a)==json_bytes(b) for a,b in zip(bv,cv)),'VERIFIED_ALBUMS_NOT_APPEND_ONLY')
    require(len(cv)-len(bv)<=1 and (len(cv)==len(bv) or operation=='finalize'),'TRANSITION_SCOPE')
    bb,bc=before.get('active_batch'),candidate.get('active_batch')
    if bb is None and bc is not None:
        require(operation in ('begin','migrate'),'TRANSITION_SCOPE')
    elif bb is not None and bc is None:
        require(operation=='release','TRANSITION_SCOPE')
    elif isinstance(bb,dict) and isinstance(bc,dict):
        require(changed_keys(bb,bc)<=BATCH_FIELDS.get(operation,set()),'TRANSITION_SCOPE')
    if changed_keys({'writer':before.get('active_writer_id')},{'writer':candidate.get('active_writer_id')}):
        was,now=before.get('active_writer_id'),candidate.get('active_writer_id')
        require((operation=='prepare' and was is None and isinstance(now,str))
            or (operation in ('finalize','stop') and now is None),'WRITER_AUTHORITY')
    if changed_keys({'lock':before.get('context_lock')},{'lock':candidate.get('context_lock')}):
        was,now=before.get('context_lock'),candidate.get('context_lock')
        require((operation=='calibrate' and was is None and isinstance(now,dict))
            or (operation in ('finalize','stop') and now is None),'CONTEXT_LOCK_AUTHORITY')
    if changed_keys({'run':before.get('current_run_id')},{'run':candidate.get('current_run_id')}):
        batch=candidate.get('active_batch')
        require(operation=='prepare' and isinstance(candidate.get('current_run_id'),str)
            and isinstance(batch,dict) and batch.get('current_album_run_id')==candidate['current_run_id'],
            'CURRENT_RUN_AUTHORITY')

def sources(reader):
    require([n for n in reader.directory_names('src/line_backup_batch') if n!='__pycache__']==PACKAGE_NAMES,'SOURCE_MEMBERSHIP_DRIFT')
    records=[];digest=hashlib.sha256()
    for path in SOURCE_PATHS:
        raw,_=reader.read(path,'SOURCE_DRIFT')
        records.append(dict(path=path,bytes=len(raw),sha256=sha(raw)))
        digest.update(path.encode()+b'\0'+raw+b'\0')
    return digest.hexdigest(),records

def enforce_grant_quota(grant,operation,state):
    """Conservatively count persisted original intents across separate lifecycle batches."""
    used=sum(1 for item in state['runs'] if item.get('batch_id') is not None and item.get('intent') is not None)
    allowance=min(grant['album_quota'],grant['save_all_dispatch_limit'],grant['chooser_confirmation_limit'])
    if operation=='begin':
        batch=state['active_batch']
        require(batch is not None and batch.get('owner_execution_id')==grant['owner']
            and batch.get('authorized_new_download_limit',0)<=grant['lifecycle_album_limit']
            and batch.get('authorized_new_download_limit',0)<=max(0,allowance-used),'GRANT_ALBUM_QUOTA')
    if operation=='intent':
        require(used<=allowance,'GRANT_DISPATCH_QUOTA')
    return used

class Store:
    def __init__(self,project_root,authorization_path=None):
        # No cwd, search, initialization, or alternative-root fallback.
        self.root=str(project_root)
        self.authorization_path=authorization_path
        installed=Path(__file__).resolve().parents[2]
        self.fixture=Path(self.root).is_relative_to(installed/'harness-development') and '/fixtures/' in self.root
        r=ProjectReader(self.root)
        try:
            cfg,_=r.read(CONFIG);validate_config(strict_json(cfg,'INVALID_CONFIG'),self.root)
            r.read(STATE)
        finally:r.close()

    def load(self,r):
        cfg_raw,cfg_id=r.read(CONFIG);raw,identity=r.read(STATE)
        cfg=strict_json(cfg_raw,'INVALID_CONFIG');s=strict_json(raw,'INVALID_STATE')
        validate_config(cfg,self.root);validate_history(s,cfg,r,allow_v3=True)
        source_hash,inventory=sources(r)
        if s.get('active_batch') is not None:
            b=s['active_batch']
            require(b['group_key']==cfg['group_key'] and b['config_sha256']==sha(cfg_raw)
                and b['source_sha256']==source_hash and b['configured_new_download_limit']==cfg['max_albums_per_run'],
                'BATCH_AUTHORITY_DRIFT')
        return cfg,s,dict(project_root=self.root,revision=s['revision'],state_sha256=sha(raw),
            state_identity=list(identity),config_sha256=sha(cfg_raw),source_sha256=source_hash),raw,inventory

    def snapshot(self):
        r=ProjectReader(self.root)
        try:
            cfg,s,receipt,_,inventory=self.load(r);r.fresh_root()
            return dict(receipt=receipt,config=cfg,state=s,source_files=inventory,dispatch_authorized=False)
        finally:r.close()

    @contextlib.contextmanager
    def guard(self):
        r=ProjectReader(self.root);parent=lock=None
        try:
            # Read before lock acquisition, never create a missing lock.
            self.load(r)
            parent=r.open('state',directory=True)
            lock=os.open('.line-backup-state.lock',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            require(stat.S_ISREG(os.fstat(lock).st_mode),'UNSAFE_SHARED_LOCK')
            fcntl.flock(lock,fcntl.LOCK_EX)
            def check_lock():
                held=os.fstat(lock);named=os.stat('.line-backup-state.lock',dir_fd=parent,follow_symlinks=False)
                require((held.st_dev,held.st_ino,held.st_mode)==(named.st_dev,named.st_ino,named.st_mode),'LOCK_REPLACED')
                r.fresh_root()
                fresh=r.open('state',directory=True)
                try:require(ProjectReader.ident(os.fstat(fresh))[:3]==ProjectReader.ident(os.fstat(parent))[:3],'STATE_PARENT_REPLACED')
                finally:os.close(fresh)
            check_lock()
            # New reader after wait: first preflight is not a lease or fresh CAS.
            fresh=ProjectReader(self.root)
            try:yield fresh,parent,check_lock,[os.fstat(lock).st_dev,os.fstat(lock).st_ino]
            finally:fresh.close()
        except OSError as exc:raise AcceptanceError('SHARED_LOCK_UNAVAILABLE',str(exc),4) from exc
        finally:
            if lock is not None:fcntl.flock(lock,fcntl.LOCK_UN);os.close(lock)
            if parent is not None:os.close(parent)
            r.close()

    def _update(self,expected,transform,*,operation=None,migration=False,snapshot_path=None,fault=None):
        """Internal operation-scoped commit primitive; public callers use Service transitions."""
        grant=None
        require(operation in TRANSITION_FIELDS,'OPERATION_REQUIRED')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            require(migration==(operation=='migrate'),'OPERATION_MISMATCH')
            grant=authorize(self.root,self.authorization_path,False,operation)
        with self.guard() as (r,parent,check_lock,lock_identity):
            cfg,before,actual,raw,_=self.load(r)
            require(actual==expected,'STALE_CAS')
            require(before['schema_version']==(2 if migration else 3),'STATE_VERSION_READ_ONLY')
            if grant is not None:
                grant_raw,_=r.read(self.authorization_path,'GRANT_DRIFT')
                require(strict_json(grant_raw,'INVALID_GRANT')==grant,'GRANT_DRIFT')
                for field in ('authorization_evidence','acceptance_evidence'):
                    ref=grant[field]
                    if ref is None:continue
                    evidence_raw,_=r.read(ref['path'],'GRANT_EVIDENCE_DRIFT')
                    require(len(evidence_raw)==ref['bytes'] and sha(evidence_raw)==ref['sha256'],'GRANT_EVIDENCE_DRIFT')
            candidate=copy.deepcopy(before)
            result=transform(cfg,candidate)
            changed=changed_keys(before,candidate)
            require(changed<=TRANSITION_FIELDS[operation],'TRANSITION_SCOPE')
            if operation=='migrate':
                require(changed=={'schema_version','active_batch'} and candidate['schema_version']==3
                    and candidate['active_batch'] is None,'MIGRATION_DELTA')
                require('active_batch' not in before,'MIGRATION_EXTRA_AUTHORITY')
            validate_nested_delta(before,candidate,operation)
            if grant is not None:
                enforce_grant_quota(grant,operation,candidate)
            candidate['revision']=before['revision']+1
            from line_backup_acceptance.common import validate_state_strict
            validate_state_strict(candidate)
            validate_history(candidate,cfg,r,allow_v3=True)
            body=json_bytes(candidate)
            # Source/config/inode observations must still match while holding lock.
            for path,value in list(r.observations.items()):
                require(r.read(path)==value,'AUTHORITY_DRIFT')
            require(ProjectReader.ident(os.stat('backup_state.json',dir_fd=parent,follow_symlinks=False))==tuple(actual['state_identity']),
                'STATE_INODE_DRIFT')
            check_lock()
            if snapshot_path is not None:
                rel=snapshot_path
                require(rel.startswith('harness-development/') and '..' not in rel.split('/'),'UNSAFE_SNAPSHOT')
                parts=rel.split('/');p=r.open('/'.join(parts[:-1]),directory=True)
                try:
                    fd=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=p)
                    try:self._write(fd,raw);os.fsync(fd)
                    finally:os.close(fd)
                    os.fsync(p)
                finally:os.close(p)
            temporary='.line-backup-migration-v3.tmp' if migration else '.line-backup-v3.tmp'
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            replaced=False
            try:
                try:self._write(fd,body);os.fsync(fd)
                finally:os.close(fd)
                if fault=='BEFORE_REPLACE':raise AcceptanceError('WRITE_BEFORE_REPLACE','fixture fault',4)
                check_lock()
                require(ProjectReader.ident(os.stat('backup_state.json',dir_fd=parent,follow_symlinks=False))==tuple(actual['state_identity']),
                    'STATE_INODE_DRIFT')
                os.replace(temporary,'backup_state.json',src_dir_fd=parent,dst_dir_fd=parent);replaced=True
                os.fsync(parent)
                if fault=='AFTER_REPLACE':raise AcceptanceError('READBACK_UNCERTAIN','fixture fault',4)
                check_lock()
                back=ProjectReader(self.root)
                try:
                    written,_=back.read(STATE)
                    require(written==body,'READBACK_UNCERTAIN')
                    _,_,receipt,_,_=self.load(back)
                finally:back.close()
                return dict(receipt=receipt,result=result,lock_identity=lock_identity,new_intent=False)
            except Exception as exc:
                if replaced:raise AcceptanceError('READBACK_UNCERTAIN',str(exc),4) from exc
                raise
            finally:
                if not replaced:
                    with contextlib.suppress(FileNotFoundError):os.unlink(temporary,dir_fd=parent)

    @staticmethod
    def _write(fd,body):
        offset=0
        while offset<len(body):
            size=os.write(fd,body[offset:]);require(size>0,'SHORT_WRITE');offset+=size

    def ledger_path(self,grant):
        """Task-local cooperative GUI ledger path; CLI pins the live location."""
        path=grant.get('gui_ledger')
        require(isinstance(path,str) and path.startswith('harness-development/') and path.endswith('gui-ledger.json')
            and all(part not in ('','.','..') for part in path.split('/')),'GUI_LEDGER_SCOPE')
        return path

    @staticmethod
    def _ledger_read(r,path):
        try: raw,_=r.read(path,'GUI_LEDGER_UNAVAILABLE')
        except AcceptanceError as exc:
            if exc.code!='GUI_LEDGER_UNAVAILABLE': raise
            return None
        return strict_json(raw,'INVALID_GUI_LEDGER')

    @staticmethod
    def _ledger_write(r,path,ledger):
        parts=path.split('/');parent=r.open('/'.join(parts[:-1]),directory=True)
        temporary='.'+parts[-1]+'-'+uuid.uuid4().hex+'.tmp'
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:Store._write(fd,json_bytes(ledger));os.fsync(fd)
            finally:os.close(fd)
            os.replace(temporary,parts[-1],src_dir_fd=parent,dst_dir_fd=parent);os.fsync(parent)
        finally:
            with contextlib.suppress(FileNotFoundError):os.unlink(temporary,dir_fd=parent)
            os.close(parent)
        back=ProjectReader(r.root)
        try:
            raw,_=back.read(path,'GUI_LEDGER_READBACK')
            require(raw==json_bytes(ledger),'GUI_LEDGER_READBACK')
        finally:back.close()

    def _ledger_open(self,r,grant):
        path=self.ledger_path(grant);cap=grant['reversible_gui_invocation_limit']
        ledger=self._ledger_read(r,path)
        if ledger is None:
            ledger=dict(version=GUI_LEDGER_VERSION,task_id=grant['task_id'],cap=cap,entries=[])
        require(isinstance(ledger,dict) and set(ledger)=={'version','task_id','cap','entries'}
            and ledger['version']==GUI_LEDGER_VERSION and isinstance(ledger['entries'],list)
            and ledger['task_id']==grant['task_id'] and ledger['cap']==cap,'GUI_LEDGER_DRIFT')
        return path,ledger,cap

    def reserve_gui(self,grant,data):
        """Reserve GUI inputs before they happen; reservations are never refunded."""
        kind=data.get('kind');count=data.get('count');run_id=data.get('run_id');owner=data.get('owner')
        require(isinstance(kind,str) and kind in GUI_LEDGER_KINDS,'GUI_LEDGER_KIND')
        require(type(count) is int and count>=1,'GUI_LEDGER_COUNT')
        require(isinstance(owner,str) and owner==grant['owner'],'GUI_LEDGER_OWNER')
        require(run_id is None or isinstance(run_id,str),'GUI_LEDGER_RUN')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            live=authorize(self.root,self.authorization_path,False,'gui_reserve')
            require(live==grant,'GRANT_DRIFT')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            used=sum(entry['count'] for entry in ledger['entries'])
            require(used+count<=cap,'GUI_LEDGER_EXHAUSTED')
            entry=dict(seq=len(ledger['entries'])+1,id=uuid.uuid4().hex,kind=kind,count=count,run_id=run_id,
                owner=owner,at=utc_now(),state='RESERVED',outcome=None,consumed_at=None)
            ledger['entries'].append(entry)
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=kind,count=count),used=used+count,cap=cap)

    def consume_gui(self,grant,data):
        """Mark one reservation consumed; a consumed or unknown reservation never refunds."""
        reservation_id=data.get('reservation_id');outcome=data.get('outcome')
        require(isinstance(reservation_id,str) and reservation_id,'GUI_LEDGER_RESERVATION')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            live=authorize(self.root,self.authorization_path,False,'gui_consume')
            require(live==grant,'GRANT_DRIFT')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            entry=next((item for item in ledger['entries'] if item['id']==reservation_id),None)
            require(entry is not None and entry['owner']==grant['owner'],'GUI_LEDGER_UNKNOWN_RESERVATION')
            require(entry['state']=='RESERVED','GUI_LEDGER_STATE')
            entry['state']='CONSUMED';entry['consumed_at']=utc_now()
            entry['outcome']=json.dumps(outcome,ensure_ascii=False,sort_keys=True) if outcome is not None else None
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=entry['kind'],count=entry['count'],state='CONSUMED'))

    def gui_reservation_fact(self,path,reservation_id):
        """Read-only cross-check used by live dispatch receipt verification."""
        r=ProjectReader(self.root)
        try:
            ledger=self._ledger_read(r,path)
            require(ledger is not None and isinstance(ledger,dict) and isinstance(ledger.get('entries'),list),'GUI_LEDGER_UNAVAILABLE')
            entry=next((item for item in ledger['entries'] if isinstance(item,dict) and item.get('id')==reservation_id),None)
            require(entry is not None and entry.get('state')=='CONSUMED','GUI_LEDGER_STATE')
            return dict(kind=entry.get('kind'),count=entry.get('count'),owner=entry.get('owner'),run_id=entry.get('run_id'),state=entry['state'])
        finally:r.close()

    def migrate(self,expected,snapshot_path,*,fixture=False,fault=None):
        require(type(fixture) is bool,'INVALID_FIXTURE_MODE')
        if fixture:
            installed=Path(__file__).resolve().parents[2]
            rel=Path(self.root).relative_to(installed/'harness-development')
            require('fixtures' in rel.parts and len(rel.parts)>rel.parts.index('fixtures')+1,'FIXTURE_ROOT_REQUIRED')
        if not fixture:
            require(expected['revision']==34 and expected['state_sha256']=='ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9'
                and expected['config_sha256']=='5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362','MIGRATION_CHECKPOINT_DRIFT')
        def migrate(cfg,s):
            require(s['active_writer_id'] is None and s['context_lock'] is None,'MIGRATION_BUSY')
            require(all(r['workflow_outcome']=='VERIFIED' for r in s['runs']),'MIGRATION_UNRESOLVED')
            require(cfg['max_albums_per_run']==1 if not fixture else True,'MIGRATION_CAP_CHANGED')
            require('active_batch' not in s,'MIGRATION_EXTRA_AUTHORITY')
            s.update(schema_version=3,active_batch=None)
            return dict(status='MIGRATED',old_raw_sha256=expected['state_sha256'],snapshot_path=snapshot_path)
        return self._update(expected,migrate,operation='migrate',migration=True,snapshot_path=snapshot_path,fault=fault)
