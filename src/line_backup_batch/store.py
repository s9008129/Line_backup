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
PROJECT_LEDGER_VERSION='line-two-album-gui-ledger-1'
PROJECT_SLOTS={
    'A.CARD':'CARD','A.CAL_OPEN':'CAL_OPEN','A.CAL_DISMISS':'CAL_DISMISS','A.ATOMIC_ELLIPSIS':'ATOMIC_ELLIPSIS',
    'A.SAVE_ALL':'SAVE_ALL','A.GO_TO_FOLDER':'GO_TO_FOLDER','A.SET_PATH':'SET_PATH','A.PATH_RETURN':'PATH_RETURN',
    'A.CHOOSER_CONFIRM':'CHOOSER_CONFIRM','B.CARD':'CARD','B.CAL_OPEN':'CAL_OPEN','B.CAL_DISMISS':'CAL_DISMISS',
    'B.ATOMIC_ELLIPSIS':'ATOMIC_ELLIPSIS','B.SAVE_ALL':'SAVE_ALL','B.GO_TO_FOLDER':'GO_TO_FOLDER',
    'B.SET_PATH':'SET_PATH','B.PATH_RETURN':'PATH_RETURN','B.CHOOSER_CONFIRM':'CHOOSER_CONFIRM',
    'RETURN_A_TO_LIST':'RETURN_A_TO_LIST','SCROLL_1':'SCROLL','SCROLL_2':'SCROLL','SCROLL_3':'SCROLL','SCROLL_4':'SCROLL'}
PROJECT_SLOT_COUNTS={'CARD':1,'CAL_OPEN':1,'CAL_DISMISS':1,'ATOMIC_ELLIPSIS':1,'SAVE_ALL':1,
    'GO_TO_FOLDER':1,'SET_PATH':1,'PATH_RETURN':1,'CHOOSER_CONFIRM':1,'RETURN_A_TO_LIST':1,'SCROLL':1}
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
                if grant.get('grant_version')=='line-two-album-project-grant-1':
                    for field in ('owner_decision','external_review','live_readiness','runtime_binding',
                        'producer_binary','decoder_binding','entry_binding'):
                        ref=grant[field]
                        evidence_raw,_=r.read(ref['path'],'PROJECT_GRANT_EVIDENCE_DRIFT')
                        require(len(evidence_raw)==ref['bytes'] and sha(evidence_raw)==ref['sha256'],
                            'PROJECT_GRANT_EVIDENCE_DRIFT')
                    contract_raw,_=r.read(grant['contract_path'],'PROJECT_CONTRACT_DRIFT')
                    require(sha(contract_raw)==grant['contract_sha256'],'PROJECT_CONTRACT_DRIFT')
                else:
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
            owner=None;replaced=False
            try:
                owner=self._temp_owner(fd)
                self._write(fd,body);os.fsync(fd)
                if fault=='BEFORE_REPLACE':raise AcceptanceError('WRITE_BEFORE_REPLACE','fixture fault',4)
                check_lock()
                require(ProjectReader.ident(os.stat('backup_state.json',dir_fd=parent,follow_symlinks=False))==tuple(actual['state_identity']),
                    'STATE_INODE_DRIFT')
                self._require_temp_owner(parent,temporary,owner)
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
                try:
                    if not replaced:self._cleanup_temp(parent,temporary,owner)
                finally:os.close(fd)

    @staticmethod
    def _write(fd,body):
        offset=0
        while offset<len(body):
            size=os.write(fd,body[offset:]);require(size>0,'SHORT_WRITE');offset+=size

    @staticmethod
    def _temp_owner(fd):
        opened=os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode),'TEMP_NOT_REGULAR')
        return opened.st_dev,opened.st_ino

    @staticmethod
    def _require_temp_owner(parent,temporary,owner):
        try:current=os.stat(temporary,dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:require(False,'TEMP_OWNERSHIP_LOST')
        require(stat.S_ISREG(current.st_mode) and (current.st_dev,current.st_ino)==owner,
            'TEMP_OWNERSHIP_LOST')

    @staticmethod
    def _cleanup_temp(parent,temporary,owner):
        if owner is None:return
        try:current=os.stat(temporary,dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:return
        require(stat.S_ISREG(current.st_mode) and (current.st_dev,current.st_ino)==owner,
            'TEMP_OWNERSHIP_LOST')
        os.unlink(temporary,dir_fd=parent)
        os.fsync(parent)

    def ledger_path(self,grant):
        """Task-local cooperative GUI ledger path; CLI pins the live location."""
        path=grant.get('gui_ledger')
        require(isinstance(path,str) and path.startswith('harness-development/') and path.endswith('gui-ledger.json')
            and all(part not in ('','.','..') for part in path.split('/')),'GUI_LEDGER_SCOPE')
        return path

    def _authorize_project_mutation(self,grant,operation):
        require(grant.get('grant_version')=='line-two-album-project-grant-1','PROJECT_SCOPE_REQUIRED')
        require(self.authorization_path is not None,'PROJECT_GRANT_REQUIRED')
        from .cli import authorize
        require(authorize(self.root,self.authorization_path,False,operation)==grant,'GRANT_DRIFT')

    @staticmethod
    def _ledger_read(r,path):
        parts=path.split('/');parent=r.open('/'.join(parts[:-1]),directory=True)
        os.close(parent)
        try:fd=r.open(path)
        except FileNotFoundError:return None
        except OSError as exc:raise AcceptanceError('GUI_LEDGER_UNSAFE','ledger is unreadable or unsafe',4) from exc
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_size<=16*1024*1024,'GUI_LEDGER_UNSAFE')
            chunks=[]
            while True:
                chunk=os.read(fd,65536)
                if not chunk:break
                chunks.append(chunk)
                require(sum(map(len,chunks))<=16*1024*1024,'GUI_LEDGER_UNSAFE')
            after=os.fstat(fd);raw=b''.join(chunks)
            require(ProjectReader.ident(before)==ProjectReader.ident(after) and len(raw)==before.st_size,
                'GUI_LEDGER_UNSAFE')
            ident=ProjectReader.ident(after)
            if path in r.observations:require(r.observations[path]==(raw,ident),'PROJECT_SNAPSHOT_CHANGED')
            r.observations[path]=(raw,ident)
        finally:os.close(fd)
        return strict_json(raw,'INVALID_GUI_LEDGER')

    @staticmethod
    def _ledger_write(r,path,ledger):
        parts=path.split('/');parent=r.open('/'.join(parts[:-1]),directory=True)
        temporary='.'+parts[-1]+'-'+uuid.uuid4().hex+'.tmp'
        fd=None;owner=None;replaced=False
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            owner=Store._temp_owner(fd)
            Store._write(fd,json_bytes(ledger));os.fsync(fd)
            Store._require_temp_owner(parent,temporary,owner)
            os.replace(temporary,parts[-1],src_dir_fd=parent,dst_dir_fd=parent);replaced=True;os.fsync(parent)
        finally:
            try:
                if not replaced:Store._cleanup_temp(parent,temporary,owner)
            finally:
                if fd is not None:os.close(fd)
                os.close(parent)
        back=ProjectReader(r.root)
        try:
            raw,_=back.read(path,'GUI_LEDGER_READBACK')
            require(raw==json_bytes(ledger),'GUI_LEDGER_READBACK')
        finally:back.close()

    def _ledger_open(self,r,grant):
        path=self.ledger_path(grant);cap=grant['reversible_gui_invocation_limit']
        ledger=self._ledger_read(r,path)
        if grant.get('grant_version')=='line-two-album-project-grant-1':
            receipt_path=path[:-len('gui-ledger.json')]+'gui-ledger-initialization.json'
            try:
                receipt_fd=r.open(receipt_path)
            except FileNotFoundError as exc:
                raise AcceptanceError('PROJECT_LEDGER_INITIALIZATION_REQUIRED','ledger initialization receipt missing',4) from exc
            except OSError as exc:raise AcceptanceError('PROJECT_LEDGER_INITIALIZATION_UNSAFE','receipt unavailable or unsafe',4) from exc
            else:os.close(receipt_fd)
            receipt_raw,_=r.read(receipt_path,'PROJECT_LEDGER_INITIALIZATION_UNSAFE')
            receipt=strict_json(receipt_raw,'PROJECT_LEDGER_INITIALIZATION_INVALID')
            require(set(receipt)=={'version','task_id','profile','cap','ledger_path','ledger_sha256','created_at'}
                and receipt.get('version')==PROJECT_LEDGER_VERSION and receipt.get('task_id')==grant['task_id']
                and receipt.get('profile')=='LINE_TWO_ALBUM_PILOT/1' and receipt.get('cap')==23
                and receipt.get('ledger_path')==path,'PROJECT_LEDGER_INITIALIZATION_INVALID')
            require(ledger is not None,'PROJECT_LEDGER_MISSING')
            require(isinstance(ledger,dict) and set(ledger)=={'version','task_id','profile','cap','owner',
                'entries','observation_counts','workflow_phase','failure_latched','c1_verified','a_run_id','c1_reference',
                'lifecycle_count','last_batch_id','lifecycle_batch_ids','initial_ledger_sha256','paired_checkpoints'}
                and ledger.get('version')==PROJECT_LEDGER_VERSION and ledger.get('task_id')==grant['task_id']
                and ledger.get('profile')=='LINE_TWO_ALBUM_PILOT/1' and ledger.get('cap')==23
                and ledger.get('owner')==grant['owner'],'PROJECT_LEDGER_DRIFT')
            self._validate_project_ledger(ledger,grant,receipt)
            return path,ledger,cap
        if ledger is None:
            ledger=dict(version=GUI_LEDGER_VERSION,task_id=grant['task_id'],cap=cap,entries=[])
        require(isinstance(ledger,dict) and set(ledger)=={'version','task_id','cap','entries'}
            and ledger['version']==GUI_LEDGER_VERSION and isinstance(ledger['entries'],list)
            and ledger['task_id']==grant['task_id'] and ledger['cap']==cap,'GUI_LEDGER_DRIFT')
        return path,ledger,cap

    def initialize_project_ledger(self,grant,data):
        self._authorize_project_mutation(grant,'gui_initialize')
        require(data=={'confirm_initialization':True},'PROJECT_LEDGER_INITIALIZATION_REFUSED')
        path=self.ledger_path(grant);receipt_path=path[:-len('gui-ledger.json')]+'gui-ledger-initialization.json'
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            require(self._ledger_read(r,path) is None,'PROJECT_LEDGER_ALREADY_EXISTS')
            try:receipt_fd=r.open(receipt_path)
            except FileNotFoundError:pass
            except OSError as exc:raise AcceptanceError('PROJECT_LEDGER_INITIALIZATION_UNSAFE','receipt path is unsafe',4) from exc
            else:
                os.close(receipt_fd);require(False,'PROJECT_LEDGER_ALREADY_INITIALIZED')
            ledger=dict(version=PROJECT_LEDGER_VERSION,task_id=grant['task_id'],profile='LINE_TWO_ALBUM_PILOT/1',
                cap=23,owner=grant['owner'],entries=[],observation_counts=dict(app=0,paired=0,extra_ax=0,popup=dict(A=0,B=0)),
                workflow_phase='A',failure_latched=False,c1_verified=False,a_run_id=None,c1_reference=None,
                lifecycle_count=0,last_batch_id=None,lifecycle_batch_ids=[],paired_checkpoints={})
            ledger['initial_ledger_sha256']=sha(json_bytes(ledger))
            receipt=dict(version=PROJECT_LEDGER_VERSION,task_id=grant['task_id'],profile='LINE_TWO_ALBUM_PILOT/1',
                cap=23,ledger_path=path,ledger_sha256=ledger['initial_ledger_sha256'],created_at=utc_now())
            parts=receipt_path.split('/');p=r.open('/'.join(parts[:-1]),directory=True);fd=None
            try:
                fd=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=p)
                self._write(fd,json_bytes(receipt));os.fsync(fd);os.close(fd);fd=None;os.fsync(p)
            finally:
                if fd is not None:os.close(fd)
                os.close(p)
            receipt_readback,_=r.read(receipt_path,'PROJECT_LEDGER_INITIALIZATION_READBACK')
            require(receipt_readback==json_bytes(receipt),'PROJECT_LEDGER_INITIALIZATION_READBACK')
            self._ledger_create(r,path,ledger)
            return dict(status='PROJECT_LEDGER_INITIALIZED',ledger_path=path,receipt_path=receipt_path,
                ledger_sha256=receipt['ledger_sha256'])

    @staticmethod
    def _ledger_create(r,path,ledger):
        parts=path.split('/');parent=r.open('/'.join(parts[:-1]),directory=True);fd=None
        try:
            fd=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            Store._write(fd,json_bytes(ledger));os.fsync(fd);os.close(fd);fd=None;os.fsync(parent)
        finally:
            if fd is not None:os.close(fd)
            os.close(parent)
        check=ProjectReader(r.root)
        try:
            raw,_=check.read(path,'PROJECT_LEDGER_READBACK')
            require(raw==json_bytes(ledger),'PROJECT_LEDGER_READBACK')
        finally:check.close()

    @staticmethod
    def _validate_project_ledger(ledger,grant,receipt):
        baseline=dict(ledger);initial=baseline.pop('initial_ledger_sha256',None)
        require(initial==receipt.get('ledger_sha256') and isinstance(initial,str) and len(initial)==64
            and all(char in '0123456789abcdef' for char in initial),
            'PROJECT_LEDGER_INITIALIZATION_BINDING')
        entries=ledger['entries'];require(isinstance(entries,list),'PROJECT_LEDGER_ENTRIES')
        seen=set();ids=set();used=0
        for index,item in enumerate(entries,1):
            require(isinstance(item,dict) and set(item)=={'seq','id','kind','count','run_id','owner','at','state',
                'outcome','consumed_at','slots','workflow_phase'} and item.get('seq')==index
                and isinstance(item.get('id'),str) and item['id'] and item['id'] not in ids
                and item.get('owner')==grant['owner'] and item.get('state') in ('RESERVED','CONSUMED')
                and isinstance(item.get('at'),str) and isinstance(item.get('slots'),list)
                and type(item.get('count')) is int,'PROJECT_LEDGER_ENTRY')
            ids.add(item['id']);slots=item['slots'];used+=item['count']
            require(item['count']==len(slots) and len(set(slots))==len(slots)
                and all(slot in PROJECT_SLOTS for slot in slots) and not seen.intersection(slots),'PROJECT_LEDGER_SLOTS')
            seen.update(slots)
            require(all(PROJECT_SLOT_COUNTS[PROJECT_SLOTS[slot]]==1 for slot in slots),'PROJECT_LEDGER_SLOTS')
            kinds={'CARD':'album_open','CAL_OPEN':'menu_calibration','CAL_DISMISS':'menu_calibration',
                'ATOMIC_ELLIPSIS':'dispatch_inputs','SAVE_ALL':'dispatch_inputs','GO_TO_FOLDER':'chooser_inputs',
                'SET_PATH':'chooser_inputs','PATH_RETURN':'chooser_inputs','CHOOSER_CONFIRM':'chooser_inputs',
                'RETURN_A_TO_LIST':'return_navigation','SCROLL':'scroll'}
            require(len({kinds[PROJECT_SLOTS[slot]] for slot in slots})==1
                and item['kind']==kinds[PROJECT_SLOTS[slots[0]]],'PROJECT_LEDGER_KIND')
            scoped=[slot.split('.',1)[1] for slot in slots if slot.startswith(('A.','B.'))]
            if scoped:
                album=slots[0].split('.',1)[0]
                require(all(slot.startswith(album+'.') for slot in slots) and item['run_id'] is not None,
                    'PROJECT_LEDGER_RUN_BINDING')
                family={PROJECT_SLOTS[slot] for slot in slots}
                require(family not in ({'CAL_OPEN'},{'CAL_DISMISS'},{'ATOMIC_ELLIPSIS'},{'SAVE_ALL'})
                    and (not family.intersection({'CAL_OPEN','CAL_DISMISS'}) or family=={'CAL_OPEN','CAL_DISMISS'} and len(slots)==2)
                    and (not family.intersection({'ATOMIC_ELLIPSIS','SAVE_ALL'}) or family=={'ATOMIC_ELLIPSIS','SAVE_ALL'} and len(slots)==2)
                    and (not family.intersection({'GO_TO_FOLDER','SET_PATH','PATH_RETURN','CHOOSER_CONFIRM'})
                        or family=={'GO_TO_FOLDER','SET_PATH','PATH_RETURN','CHOOSER_CONFIRM'} and len(slots)==4),
                    'PROJECT_LEDGER_BUNDLE')
            else:require(item['run_id'] is None,'PROJECT_LEDGER_RUN_BINDING')
            if item['state']=='RESERVED':require(item['outcome'] is None and item['consumed_at'] is None,'PROJECT_LEDGER_RESERVED')
            else:require(isinstance(item['consumed_at'],str),'PROJECT_LEDGER_CONSUMED')
        require(used==len(seen) and used<=23 and len(entries)<=23,'PROJECT_LEDGER_COUNT')
        counters=ledger['observation_counts'];require(isinstance(counters,dict) and set(counters)=={'app','paired','extra_ax','popup'}
            and type(counters['app']) is int and 0<=counters['app']<=3
            and type(counters['paired']) is int and 0<=counters['paired']<=80
            and type(counters['extra_ax']) is int and 0<=counters['extra_ax']<=23
            and isinstance(counters['popup'],dict) and set(counters['popup'])=={'A','B'}
            and all(type(value) is int and 0<=value<=2 for value in counters['popup'].values()),
            'PROJECT_OBSERVATION_QUOTA')
        checkpoints=ledger['paired_checkpoints']
        require(isinstance(checkpoints,dict) and all(isinstance(k,str) and k and type(v) is int and 0<=v<=2
            for k,v in checkpoints.items()) and sum(checkpoints.values())==counters['paired'],
            'PROJECT_PAIRED_CHECKPOINT_QUOTA')
        require(ledger['workflow_phase'] in ('A','C1','B','DONE','FAILED') and type(ledger['failure_latched']) is bool
            and type(ledger['c1_verified']) is bool and type(ledger['lifecycle_count']) is int
            and 0<=ledger['lifecycle_count']<=2,'PROJECT_WORKFLOW_LEDGER')
        require(isinstance(ledger['lifecycle_batch_ids'],list) and len(ledger['lifecycle_batch_ids'])==ledger['lifecycle_count']
            and len(set(ledger['lifecycle_batch_ids']))==len(ledger['lifecycle_batch_ids'])
            and ledger['last_batch_id']==(ledger['lifecycle_batch_ids'][-1] if ledger['lifecycle_batch_ids'] else None),
            'PROJECT_WORKFLOW_LEDGER')
        require(((ledger['workflow_phase'] in ('A','C1') and ledger['lifecycle_count']<=1)
            or (ledger['workflow_phase'] in ('B','DONE') and ledger['lifecycle_count']>=1
                and ledger['c1_verified']))
            or (ledger['workflow_phase']=='FAILED' and ledger['failure_latched'] is True),
            'PROJECT_WORKFLOW_LEDGER')

    def reserve_gui(self,grant,data):
        """Reserve GUI inputs before they happen; reservations are never refunded."""
        kind=data.get('kind');count=data.get('count');run_id=data.get('run_id');owner=data.get('owner')
        require(isinstance(kind,str) and kind in GUI_LEDGER_KINDS,'GUI_LEDGER_KIND')
        require(type(count) is int and count>=1,'GUI_LEDGER_COUNT')
        require(isinstance(owner,str) and owner==grant['owner'],'GUI_LEDGER_OWNER')
        require(run_id is None or isinstance(run_id,str),'GUI_LEDGER_RUN')
        slot=data.get('slot')
        project=grant.get('grant_version')=='line-two-album-project-grant-1'
        if project:
            self._authorize_project_mutation(grant,'gui_reserve')
            slots=data.get('slots',[slot])
            require(isinstance(slots,list) and len(slots)==count and len(set(slots))==count
                and all(item in PROJECT_SLOTS for item in slots),'PROJECT_LEDGER_SLOT')
            slot=slots[0]
            expected_kind={'CARD':'album_open','CAL_OPEN':'menu_calibration','CAL_DISMISS':'menu_calibration',
                'ATOMIC_ELLIPSIS':'dispatch_inputs','SAVE_ALL':'dispatch_inputs','GO_TO_FOLDER':'chooser_inputs',
                'SET_PATH':'chooser_inputs','PATH_RETURN':'chooser_inputs','CHOOSER_CONFIRM':'chooser_inputs',
                'RETURN_A_TO_LIST':'return_navigation','SCROLL':'scroll'}[PROJECT_SLOTS[slot]]
            require(all(PROJECT_SLOT_COUNTS[PROJECT_SLOTS[item]]==1 for item in slots)
                and all({'CARD':'album_open','CAL_OPEN':'menu_calibration','CAL_DISMISS':'menu_calibration',
                    'ATOMIC_ELLIPSIS':'dispatch_inputs','SAVE_ALL':'dispatch_inputs','GO_TO_FOLDER':'chooser_inputs',
                    'SET_PATH':'chooser_inputs','PATH_RETURN':'chooser_inputs','CHOOSER_CONFIRM':'chooser_inputs',
                    'RETURN_A_TO_LIST':'return_navigation','SCROLL':'scroll'}[PROJECT_SLOTS[item]]==kind for item in slots),
                'PROJECT_LEDGER_SLOT_KIND')
        if not project and not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            live=authorize(self.root,self.authorization_path,False,'gui_reserve')
            require(live==grant,'GRANT_DRIFT')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            used=sum(entry['count'] for entry in ledger['entries'])
            require(used+count<=cap,'GUI_LEDGER_EXHAUSTED')
            if project:
                require(not ledger['failure_latched'],'PROJECT_WORKFLOW_HALTED')
                require(not any(item.get('state')=='RESERVED' for item in ledger['entries']),'PROJECT_UNKNOWN_RESERVATION')
                reserved={slot for item in ledger['entries'] for slot in item.get('slots',[])}
                require(not reserved.intersection(slots),'PROJECT_SLOT_ALREADY_RESERVED')
                slot=slots[0]
                prefix='A.' if all(item.startswith('A.') for item in slots) else 'B.' if all(item.startswith('B.') for item in slots) else ''
                phase=ledger['workflow_phase']
                require((prefix=='A.' and phase=='A') or (prefix=='B.' and phase=='B')
                    or (slot=='RETURN_A_TO_LIST' and phase=='C1') or (slot.startswith('SCROLL_') and phase in ('A','C1')),
                    'PROJECT_WORKFLOW_PHASE')
                if any(item.startswith('B.') for item in slots):
                    require(ledger.get('c1_verified') is True,'PROJECT_C1_REQUIRED')
                self._validate_new_project_slots(ledger,slots)
            entry=dict(seq=len(ledger['entries'])+1,id=uuid.uuid4().hex,kind=kind,count=count,run_id=run_id,
                owner=owner,at=utc_now(),state='RESERVED',outcome=None,consumed_at=None)
            if project:entry.update(slots=slots,workflow_phase=ledger['workflow_phase'])
            ledger['entries'].append(entry)
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=kind,count=count),used=used+count,cap=cap)

    @staticmethod
    def _validate_new_project_slots(ledger,slots):
        used_set={slot for entry in ledger['entries'] for slot in entry.get('slots',[])}
        phase=ledger['workflow_phase']
        scrolls=sorted(int(item.split('_')[1]) for item in used_set if item.startswith('SCROLL_'))
        for slot in slots:
            if slot.startswith('SCROLL_'):
                number=int(slot.split('_')[1])
                require(number==len(scrolls)+1 and number<=4,'PROJECT_SCROLL_SLOT_ORDER')
                if phase=='A':require(number<=3 and 'A.CARD' not in used_set,'PROJECT_PRE_ALBUM_SCROLL_LIMIT')
                else:require(phase=='C1' and 'RETURN_A_TO_LIST' in used_set,'PROJECT_POST_A_SCROLL_REQUIRED')
                scrolls.append(number);used_set.add(slot);continue
            if slot=='RETURN_A_TO_LIST':
                require(phase=='C1' and 'RETURN_A_TO_LIST' not in used_set,'PROJECT_RETURN_SLOT_ORDER')
                used_set.add(slot);continue
            prefix='A' if slot.startswith('A.') else 'B'
            if prefix=='B':require(phase=='B' and ledger['c1_verified'] and scrolls,'PROJECT_C1_REQUIRED')
            prior={item for item in used_set if item.startswith(prefix+'.')}
            groups=[(f'{prefix}.CARD',),(f'{prefix}.CAL_OPEN',f'{prefix}.CAL_DISMISS'),
                (f'{prefix}.ATOMIC_ELLIPSIS',f'{prefix}.SAVE_ALL'),
                (f'{prefix}.GO_TO_FOLDER',f'{prefix}.SET_PATH',f'{prefix}.PATH_RETURN',f'{prefix}.CHOOSER_CONFIRM')]
            expected=next((group for group in groups if not set(group)<=prior),None)
            require(expected is not None and slot in expected,'PROJECT_ACTION_SLOT_ORDER')
            if len(expected)>1:
                require(slots==list(expected),'PROJECT_ACTION_BUNDLE_REQUIRED')
            else:require(slots==[slot],'PROJECT_ACTION_SLOT_REQUIRED')
            used_set.add(slot)

    def consume_gui(self,grant,data):
        """Mark one reservation consumed; a consumed or unknown reservation never refunds."""
        reservation_id=data.get('reservation_id');outcome=data.get('outcome')
        require(isinstance(reservation_id,str) and reservation_id,'GUI_LEDGER_RESERVATION')
        project=grant.get('grant_version')=='line-two-album-project-grant-1'
        if project:self._authorize_project_mutation(grant,'gui_consume')
        if not project and not self.fixture:
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
            if project:
                if outcome!='RETURNED':ledger['failure_latched']=True
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=entry['kind'],count=entry['count'],state='CONSUMED'))

    def advance_project_phase(self,grant,phase,*,c1_evidence=None,a_run_id=None):
        self._authorize_project_mutation(grant,'gui_phase')
        require(phase in ('C1','B','DONE','FAILED'),'PROJECT_WORKFLOW_PHASE')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock();path,ledger,cap=self._ledger_open(r,grant)
            if phase=='FAILED':
                require(ledger['workflow_phase'] not in ('DONE','FAILED'),'PROJECT_WORKFLOW_PHASE')
                ledger['failure_latched']=True;ledger['workflow_phase']='FAILED'
                self._ledger_write(r,path,ledger)
                return dict(status='PROJECT_WORKFLOW_PHASE',phase='FAILED',failure_latched=True)
            require(not ledger['failure_latched'] and not any(item.get('state')=='RESERVED' for item in ledger['entries']),
                'PROJECT_WORKFLOW_HALTED')
            if phase=='C1' and ledger['workflow_phase']=='A':
                state=strict_json(r.read(STATE)[0],'INVALID_STATE')
                a=next((run for run in state['runs'] if run.get('run_id')==a_run_id),None)
                require(a is not None and a.get('workflow_outcome')=='VERIFIED'
                    and ledger['lifecycle_count']==1 and a.get('batch_id')==ledger['lifecycle_batch_ids'][0],
                    'PROJECT_A_NOT_VERIFIED')
                require(any(item.get('verified_run_id')==a_run_id for item in state['verified_albums']),
                    'PROJECT_A_READBACK_REQUIRED')
                require(state.get('active_batch') is None and state.get('active_writer_id') is None
                    and state.get('context_lock') is None,'PROJECT_A_NOT_RELEASED')
                close_path=f"{grant['artifact_dir']}/lease-close-{a_run_id}.json"
                close=strict_json(r.read(close_path,'PROJECT_A_LEASE_CLOSE')[0],'PROJECT_A_LEASE_CLOSE')
                require(close.get('run_id')==a_run_id and close.get('state')=='CLOSED','PROJECT_A_LEASE_OPEN')
                ledger.update(workflow_phase='C1',a_run_id=a_run_id)
            elif phase=='C1':
                require(ledger['workflow_phase']=='C1' and ledger['lifecycle_count']==1,'PROJECT_WORKFLOW_PHASE')
                from .observations import artifact
                evidence=strict_json(artifact(r,c1_evidence),'PROJECT_C1_EVIDENCE')
                state=strict_json(r.read(STATE)[0],'INVALID_STATE')
                require(state.get('active_batch') is None and state.get('active_writer_id') is None
                    and state.get('context_lock') is None,'PROJECT_A_NOT_RELEASED')
                a=next((run for run in state['runs'] if run.get('run_id')==a_run_id),None)
                require(evidence.get('kind')=='LINE_TWO_ALBUM_C1' and evidence.get('status')=='PASS'
                    and evidence.get('a_run_id')==a_run_id and a_run_id==ledger.get('a_run_id')
                    and isinstance(evidence.get('scrolls'),list) and 1<=len(evidence['scrolls'])<=4,
                    'PROJECT_C1_EVIDENCE')
                require(isinstance(a,dict) and evidence.get('group_key')==a['group_key']
                    and isinstance(evidence.get('new_candidates'),list) and evidence['new_candidates']
                    and evidence.get('verified_scroll_count')==len(evidence['scrolls'])
                    and any(proof.get('new_candidates')==evidence['new_candidates'] for proof in evidence['scrolls']),
                    'PROJECT_C1_TARGET_GROUNDING')
                project_entries=ledger['entries']
                returns=[entry for entry in project_entries if entry.get('workflow_phase')=='C1'
                    and entry.get('slots')==['RETURN_A_TO_LIST']]
                expected_scroll_entries=[entry for entry in project_entries if entry.get('workflow_phase')=='C1'
                    and entry.get('slots') and entry['slots'][0].startswith('SCROLL_')]
                proof_slots=[proof.get('slot') for proof in evidence['scrolls'] if isinstance(proof,dict)]
                require(len(returns)==1 and returns[0].get('owner')==grant['owner']
                    and returns[0].get('state')=='CONSUMED' and returns[0].get('count')==1
                    and len(expected_scroll_entries)==len(proof_slots)
                    and [entry['slots'][0] for entry in expected_scroll_entries]==proof_slots
                    and all(entry.get('owner')==grant['owner'] and entry.get('state')=='CONSUMED'
                        and entry.get('count')==1 for entry in expected_scroll_entries),
                    'PROJECT_C1_INPUT_RESERVATIONS')
                for proof in evidence['scrolls']:
                    require(isinstance(proof,dict) and set(proof)=={'slot','before_frame','after_frame','before_ax',
                        'after_ax','overlap','overlap_count','new_candidate','new_candidates','identity_continuity','context','movement'}
                        and isinstance(proof.get('slot'),str) and proof.get('identity_continuity') is True
                        and proof.get('movement')=='UPWARD_BEYOND_UNCERTAINTY'
                        and proof.get('overlap')=='ORDERED_SUFFIX_PREFIX' and type(proof.get('overlap_count')) is int
                        and proof['overlap_count']>=1 and isinstance(proof.get('context'),dict)
                        and proof['context'].get('session_id')==grant['owner']
                        and proof['context'].get('group_key')==a['group_key']
                        and proof['context'].get('provider')=='HOSTED_CUA' and proof['context'].get('pid')
                        and proof['context'].get('list_window_id') and proof['context'].get('layout_key')
                        and type(proof['context'].get('width')) is int and type(proof['context'].get('height')) is int
                        and type(proof['context'].get('native_scale')) in (int,float),
                        'PROJECT_C1_SCROLL_PROOF')
                    require(isinstance(proof.get('new_candidates'),list) and proof['new_candidate'] in proof['new_candidates'],
                        'PROJECT_C1_NEW_CANDIDATES')
                    for name in ('before_frame','after_frame','before_ax','after_ax'):
                        artifact(r,proof[name])
                ledger.update(workflow_phase='B',c1_verified=True,a_run_id=a_run_id,
                    c1_reference=dict(path=c1_evidence['path'],sha256=c1_evidence['sha256']))
            else:
                require(ledger['workflow_phase']==('B' if phase=='DONE' else 'A'),'PROJECT_WORKFLOW_PHASE')
                if phase=='DONE':
                    state=strict_json(r.read(STATE)[0],'INVALID_STATE')
                    require(ledger['lifecycle_count']==2 and ledger['c1_verified'] is True
                        and state.get('active_batch') is None and state.get('active_writer_id') is None
                        and state.get('context_lock') is None,'PROJECT_B_NOT_RELEASED')
                    b_batch=ledger['lifecycle_batch_ids'][1]
                    b=next((run for run in state['runs'] if run.get('batch_id')==b_batch),None)
                    require(isinstance(b,dict) and b.get('workflow_outcome')=='VERIFIED'
                        and any(item.get('verified_run_id')==b.get('run_id') for item in state['verified_albums']),
                        'PROJECT_B_NOT_VERIFIED')
                    close_path=f"{grant['artifact_dir']}/lease-close-{b['run_id']}.json"
                    close=strict_json(r.read(close_path,'PROJECT_B_LEASE_CLOSE')[0],'PROJECT_B_LEASE_CLOSE')
                    require(close.get('run_id')==b['run_id'] and close.get('state')=='CLOSED','PROJECT_B_LEASE_OPEN')
                ledger['workflow_phase']=phase
            self._ledger_write(r,path,ledger)
            return dict(status='PROJECT_WORKFLOW_PHASE',phase=ledger['workflow_phase'])

    def start_project_lifecycle(self,grant,batch_id):
        self._authorize_project_mutation(grant,'begin')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock();path,ledger,cap=self._ledger_open(r,grant)
            require(not ledger['failure_latched'] and ledger['lifecycle_count']<2,'PROJECT_LIFECYCLE_CAP')
            expected_phase='A' if ledger['lifecycle_count']==0 else 'B'
            require(ledger['workflow_phase']==expected_phase,'PROJECT_WORKFLOW_PHASE')
            require(batch_id not in ledger['lifecycle_batch_ids'],'PROJECT_BATCH_REUSED')
            state=strict_json(r.read(STATE)[0],'INVALID_STATE');batch=state.get('active_batch')
            require(isinstance(batch,dict) and batch.get('batch_id')==batch_id
                and batch.get('owner_execution_id')==grant['owner'] and batch.get('mode')=='backup_batch'
                and batch.get('authorized_new_download_limit')==1 and batch.get('new_transactions_reserved')==0,
                'PROJECT_BATCH_BINDING')
            ledger['lifecycle_count']+=1;ledger['last_batch_id']=batch_id
            ledger['lifecycle_batch_ids'].append(batch_id)
            self._ledger_write(r,path,ledger)
            return dict(status='PROJECT_LIFECYCLE_STARTED',ordinal=ledger['lifecycle_count'])

    def project_album_slot(self,grant):
        require(grant.get('grant_version')=='line-two-album-project-grant-1','PROJECT_SCOPE_REQUIRED')
        reader=ProjectReader(self.root)
        try:
            path=self.ledger_path(grant);ledger=self._ledger_read(reader,path)
            require(ledger is not None and ledger.get('lifecycle_count') in (1,2),'PROJECT_LIFECYCLE_REQUIRED')
            return 'A' if ledger['lifecycle_count']==1 else 'B'
        finally:reader.close()

    def project_batch_ids(self,grant):
        reader=ProjectReader(self.root)
        try:
            ledger=self._ledger_read(reader,self.ledger_path(grant))
            require(ledger is not None,'PROJECT_LEDGER_MISSING')
            return list(ledger['lifecycle_batch_ids'])
        finally:reader.close()

    def reserve_observation(self,grant,kind,*,checkpoint=None,album=None):
        self._authorize_project_mutation(grant,'gui_observe')
        require(kind in ('app','paired','extra_ax','popup'),'PROJECT_OBSERVATION_KIND')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock();path,ledger,cap=self._ledger_open(r,grant);counts=ledger['observation_counts']
            if kind=='app':require(counts['app']<3,'PROJECT_APP_ACQUISITION_QUOTA');counts['app']+=1
            elif kind=='paired':
                require(isinstance(checkpoint,str) and checkpoint and len(checkpoint)<=120,'PROJECT_CHECKPOINT_REQUIRED')
                require(counts['paired']<80,'PROJECT_PAIRED_OBSERVATION_QUOTA')
                current=ledger['paired_checkpoints'].get(checkpoint,0)
                require(current<2,'PROJECT_CHECKPOINT_RECAPTURE_QUOTA')
                ledger['paired_checkpoints'][checkpoint]=current+1;counts['paired']+=1
            elif kind=='extra_ax':require(counts['extra_ax']<23,'PROJECT_EXTRA_AX_QUOTA');counts['extra_ax']+=1
            else:
                require(album in ('A','B') and counts['popup'][album]<2,'PROJECT_POPUP_QUOTA')
                counts['popup'][album]+=1
            self._ledger_write(r,path,ledger)
            return dict(status='PROJECT_OBSERVATION_RESERVED',kind=kind,counts=copy.deepcopy(counts))

    def gui_reservation_fact(self,path,reservation_id):
        """Read-only cross-check used by live dispatch receipt verification."""
        r=ProjectReader(self.root)
        try:
            ledger=self._ledger_read(r,path)
            require(ledger is not None and isinstance(ledger,dict) and isinstance(ledger.get('entries'),list),'GUI_LEDGER_UNAVAILABLE')
            entry=next((item for item in ledger['entries'] if isinstance(item,dict) and item.get('id')==reservation_id),None)
            require(entry is not None and entry.get('state')=='CONSUMED','GUI_LEDGER_STATE')
            outcome=None
            if entry.get('outcome') is not None:
                try:outcome=json.loads(entry['outcome'])
                except (TypeError,ValueError):raise AcceptanceError('GUI_LEDGER_OUTCOME','reservation outcome is malformed',4)
            fact=dict(kind=entry.get('kind'),count=entry.get('count'),owner=entry.get('owner'),run_id=entry.get('run_id'),
                state=entry['state'],slots=entry.get('slots'))
            if ledger.get('profile')=='LINE_TWO_ALBUM_PILOT/1':fact['outcome']=outcome
            return fact
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
