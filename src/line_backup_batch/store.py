"""Single existing-lock CAS authority, retaining raw bytes and nanosecond ints."""
import contextlib
import copy
import fcntl
import hashlib
import os
from pathlib import Path
import stat
from line_backup_acceptance.common import AcceptanceError,json_bytes
from line_backup_acceptance.project_binding import ProjectReader,strict_json,validate_config,validate_history,sha
from .schema import require

STATE='state/backup_state.json'
CONFIG='config/line_backup_config.json'
PACKAGE_NAMES=['__init__.py','__main__.py','cli.py','content.py','coordinator.py','image_decode.swift',
               'observations.py','schema.py','service.py','state_v3.schema.json','store.py']
SOURCE_PATHS=[f'src/line_backup_acceptance/{n}' for n in
    ['__init__.py','__main__.py','authority.py','cli.py','common.py','project_binding.py','status.py','transaction.py','verifier.py']]
SOURCE_PATHS += [f'src/line_backup_batch/{n}' for n in PACKAGE_NAMES]+['scripts/line_backup_cua_adapter.mjs']

def sources(reader):
    require([n for n in reader.directory_names('src/line_backup_batch') if n!='__pycache__']==PACKAGE_NAMES,'SOURCE_MEMBERSHIP_DRIFT')
    records=[];digest=hashlib.sha256()
    for path in SOURCE_PATHS:
        raw,_=reader.read(path,'SOURCE_DRIFT')
        records.append(dict(path=path,bytes=len(raw),sha256=sha(raw)))
        digest.update(path.encode()+b'\0'+raw+b'\0')
    return digest.hexdigest(),records

class Store:
    def __init__(self,project_root,authorization_path=None):
        # No cwd, search, initialization, or alternative-root fallback.
        self.root=str(project_root)
        self.authorization_path=authorization_path
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

    def update(self,expected,transform,*,migration=False,snapshot_path=None,fault=None):
        installed=Path(__file__).resolve().parents[2]
        fixture=Path(self.root).is_relative_to(installed/'harness-development') and '/fixtures/' in self.root
        if not fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            authorize(self.root,self.authorization_path,False,'migrate' if migration else 'mutate')
        with self.guard() as (r,parent,check_lock,lock_identity):
            cfg,before,actual,raw,_=self.load(r)
            require(actual==expected,'STALE_CAS')
            require(before['schema_version']==(2 if migration else 3),'STATE_VERSION_READ_ONLY')
            candidate=copy.deepcopy(before)
            result=transform(cfg,candidate)
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
        return self.update(expected,migrate,migration=True,snapshot_path=snapshot_path,fault=fault)
