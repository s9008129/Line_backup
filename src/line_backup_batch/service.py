"""Canonical batch transitions. No GUI code, no imported historical operator."""
import copy
import json
import os
from pathlib import Path
import uuid
from line_backup_acceptance.common import json_bytes,utc_now,_check_calibration
from line_backup_acceptance.project_binding import ProjectReader,strict_json,history_decision,integer,sha
from .schema import require,POLICY
from .store import Store
from .observations import artifact,catalog,card_target,frame,point,rect
from . import content

class Service:
    def __init__(self,root,owner,artifact_dir,authorization_path=None):
        require(isinstance(owner,str) and owner,'OWNER_REQUIRED')
        require(isinstance(artifact_dir,str) and artifact_dir.startswith('harness-development/') and '..' not in artifact_dir.split('/'),
            'ARTIFACT_SCOPE_REQUIRED')
        self.store=Store(root,authorization_path);self.owner=owner;self.artifact_dir=artifact_dir
        reader=ProjectReader(root)
        try:fd=reader.open(artifact_dir,directory=True);os.close(fd)
        finally:reader.close()

    def publish(self,name,value):
        require('/' not in name and name not in ('.','..'),'UNSAFE_ARTIFACT_NAME')
        reader=ProjectReader(self.store.root);fd=None;parent=None;raw=json_bytes(value)
        try:
            parent=reader.open(self.artifact_dir,directory=True)
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            Store._write(fd,raw);os.fsync(fd);os.close(fd);fd=None;os.fsync(parent)
            path=self.artifact_dir+'/'+name;actual,_=reader.read(path)
            require(actual==raw,'ARTIFACT_READBACK')
            return dict(path=path,bytes=len(raw),sha256=sha(raw))
        finally:
            if fd is not None:os.close(fd)
            if parent is not None:os.close(parent)
            reader.close()

    def batch(self,s):
        b=s['active_batch'];require(b is not None and b['owner_execution_id']==self.owner,'FOREIGN_BATCH_OWNER')
        require(b['phase'] not in ('STOPPED','COMPLETED'),'TERMINAL_BATCH_OWNER')
        return b

    def begin(self,expected,mode,limit):
        require(mode in ('catalog_only','backup_batch') and integer(limit),'INVALID_BATCH_SCOPE')
        require(limit==0 if mode=='catalog_only' else limit>0,'INVALID_BATCH_SCOPE')
        batch_id='BATCH-'+uuid.uuid4().hex
        def acquire(cfg,s):
            require(s['active_batch'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'BATCH_BUSY')
            require(all(r['workflow_outcome']=='VERIFIED' or (r['workflow_outcome']=='SAFE_ABORT' and r['intent'] is None
                and r['manual_reconciliation_required'] is False) for r in s['runs']),'UNRESOLVED_HISTORY')
            s['active_batch']=dict(batch_id=batch_id,owner_execution_id=self.owner,group_key=cfg['group_key'],mode=mode,
                phase='CATALOG',policy_version=POLICY,config_sha256=expected['config_sha256'],source_sha256=expected['source_sha256'],
                created_at=utc_now(),authorized_new_download_limit=limit,configured_new_download_limit=cfg['max_albums_per_run'],
                new_transactions_reserved=0,manifest_reference=None,next_index=0,current_album_run_id=None,stop_reason=None)
            return dict(batch_id=batch_id,status='BATCH_OWNED')
        return self.store.update(expected,acquire)

    def manifest(self,b,reader,cfg):
        require(b['manifest_reference'] is not None,'MANIFEST_REQUIRED')
        m=strict_json(artifact(reader,b['manifest_reference']),'INVALID_MANIFEST')
        require(set(m)=={'version','project_root','group_key','config_sha256','source_sha256','session_id','identities','frames','policy'},'INVALID_MANIFEST')
        require(m['version']==1 and m['policy']==POLICY and m['project_root']==self.store.root and m['group_key']==cfg['group_key']
            and m['config_sha256']==b['config_sha256'] and m['source_sha256']==b['source_sha256'],'MANIFEST_AUTHORITY_DRIFT')
        # Coverage was classified before admission; retained images/proofs rehash every use.
        for observation in m['frames']:
            artifact(reader,observation['frame']);artifact(reader,observation['mapping']['evidence']);artifact(reader,observation['boundary']['evidence'])
        require(isinstance(m['identities'],list) and m['identities'],'EMPTY_MANIFEST')
        return m

    def admit(self,expected,records,session):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            identities=catalog(reader,records,snap['config'],session)
        finally:reader.close()
        m=dict(version=1,project_root=self.store.root,group_key=snap['config']['group_key'],config_sha256=expected['config_sha256'],
            source_sha256=expected['source_sha256'],session_id=session,identities=identities,frames=records,policy=POLICY)
        ref=self.publish('catalog-'+uuid.uuid4().hex+'.json',m)
        def admit(cfg,s):
            b=self.batch(s);require(b['phase']=='CATALOG' and b['manifest_reference'] is None,'ALREADY_ADMITTED')
            require(b['config_sha256']==expected['config_sha256'] and b['source_sha256']==expected['source_sha256'],'BATCH_AUTHORITY_DRIFT')
            b['manifest_reference']=ref;b['phase']='ADMITTED'
            return dict(status='ADMITTED',manifest_reference=ref,identities=identities)
        return self.store.update(expected,admit)

    @staticmethod
    def eligible(s,target):
        view=copy.deepcopy(s);view['active_batch']=None
        return history_decision(view,dict(fingerprint=target),{r['run_id']:r for r in view['runs']})[0]

    @staticmethod
    def event(r,phase,evidence):
        e=dict(phase=phase,at=utc_now(),evidence=json.dumps(evidence,ensure_ascii=False,sort_keys=True))
        r['phase']=phase;r['checkpoint']=e;r['events'].append(e)

    def prepare(self,expected,observation):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            b=self.batch(snap['state']);m=self.manifest(b,reader,snap['config'])
            require(b['mode']=='backup_batch' and b['phase'] in ('ADMITTED','RUNNING'),'CATALOG_DISPATCH_REFUSED')
            require(b['current_album_run_id'] is None,'ALBUM_BUSY')
            index=b['next_index'];require(index<len(m['identities']),'MANIFEST_END')
            target=m['identities'][index];decision=self.eligible(snap['state'],target)
            click=None
            if decision=='PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION':
                require(b['new_transactions_reserved']<min(b['authorized_new_download_limit'],b['configured_new_download_limit']),'LIMIT_REACHED')
                click=card_target(reader,observation,snap['config'],target,m['session_id'])
            else:require(decision=='SKIP_VERIFIED',decision)
        finally:reader.close()
        run_id='RUN-v3-'+uuid.uuid4().hex
        def prepare(cfg,s):
            b=self.batch(s)
            require(b['next_index']==index and b['current_album_run_id'] is None,'ALBUM_BUSY')
            require(self.eligible(s,target)==decision,'HISTORY_DRIFT')
            if decision=='SKIP_VERIFIED':
                b['next_index']+=1;return dict(status='SKIP_VERIFIED',fingerprint=target)
            relative=f"backups/{cfg['group_name']}/{target['start_date']}_{target['end_date']}_{target['expected_images']}張"
            p=ProjectReader(self.store.root)
            try:
                parent=p.open('backups',directory=True)
                try:
                    try:os.mkdir(cfg['group_name'],0o700,dir_fd=parent)
                    except FileExistsError:pass
                finally:os.close(parent)
                parent=p.open('backups/'+cfg['group_name'],directory=True)
                try:
                    try:os.mkdir(relative.split('/')[-1],0o700,dir_fd=parent)
                    except FileExistsError:pass
                finally:os.close(parent)
                fd=p.open(relative,directory=True)
                try:require(not os.listdir(fd),'DESTINATION_NONEMPTY')
                finally:os.close(fd)
            finally:p.close()
            destination=self.store.root+'/'+relative
            event=dict(phase='OPEN_ALBUM',at=utc_now(),evidence=json.dumps(dict(observation=observation,click=click),ensure_ascii=False,sort_keys=True))
            r=dict(run_id=run_id,mode='backup_batch',group_key=cfg['group_key'],album_id=None,fingerprint=target,
                observed_title=cfg['group_name'],title_confidence='HIGH',destination=destination,destination_initially_empty=True,
                phase='OPEN_ALBUM',checkpoint=event,events=[event],intent=None,recovery_used={},runtime_errors=[],verification=None,
                workflow_outcome='IN_PROGRESS',stop_reason=None,batch_id=b['batch_id'],intent_state='INTENT_NONE',
                manual_reconciliation_required=False,reconciliation_reason=None,contract_revision='1.0-rc2',
                dispatch_state='NOT_ATTEMPTED',dispatch_evidence=None,reconciliations=[])
            s['runs'].append(r);s['current_run_id']=run_id;s['active_writer_id']=self.owner
            b['current_album_run_id']=run_id;b['phase']='RUNNING'
            return dict(status='ALBUM_OPEN_READY',run_id=run_id,fingerprint=target,destination=destination,click=click,
                frame_id=observation['frame_id'],session_id=m['session_id'])
        return self.store.update(expected,prepare)

    def run(self,s):
        b=self.batch(s);require(b['current_album_run_id'] is not None,'NO_ACTIVE_ALBUM')
        r=next(r for r in s['runs'] if r['run_id']==b['current_album_run_id'])
        require(r['workflow_outcome']=='IN_PROGRESS' and s['active_writer_id']==self.owner,'FOREIGN_ALBUM_OWNER')
        return b,r

    def calibrate(self,expected,detail,calibration,menu,closure):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            b,r=self.run(snap['state']);m=self.manifest(b,reader,snap['config'])
            require(r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            for record in (detail,closure):
                frame(reader,record,snap['config'],session=m['session_id'])
                require(record['surface']=='ALBUM_DETAIL' and len(record['cards'])==1
                    and record['cards'][0]['fingerprint']==r['fingerprint'],'TARGET_MISMATCH')
            _check_calibration(calibration)
            require(menu['label'] in ('儲存全部','Save All') and menu['frame_id']==detail['frame_id']
                and menu['layout_key']==detail['layout_key'],'SAVE_ALL_ROW_MISMATCH')
            artifact(reader,menu['evidence'])
            safe=rect(menu['safe_bounds'],detail['width'],detail['height'])
            point(calibration['save_all_point'],safe,detail['mapping']['uncertainty'])
            require(calibration['screenshot_width']==closure['width'] and calibration['screenshot_height']==closure['height'],
                'CALIBRATION_LAYOUT_DRIFT')
            point(calibration['ellipsis'],menu['ellipsis_bounds'],detail['mapping']['uncertainty'])
            require(menu['closure_trace']==['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH'],
                'MENU_CLOSURE_UNPROVEN')
        finally:reader.close()
        def calibrate(cfg,s):
            b,r=self.run(s);require(r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            s['context_lock']=dict(group_key=cfg['group_key'],source='RELIABLE_VISUAL_NAVIGATION',confirmed_at=utc_now(),
                execution_id=self.owner,continuity_evidence=json.dumps(closure,ensure_ascii=False,sort_keys=True))
            self.event(r,'SAVE_ALL_CALIBRATION',dict(detail=detail,calibration=calibration,menu=menu,closure=closure))
            return dict(status='CALIBRATED',run_id=r['run_id'])
        return self.store.update(expected,calibrate)

    def intent(self,expected,fresh):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            b,r=self.run(snap['state']);m=self.manifest(b,reader,snap['config'])
            frame(reader,fresh,snap['config'],session=m['session_id'])
            require(fresh['surface']=='ALBUM_DETAIL' and len(fresh['cards'])==1 and fresh['cards'][0]['fingerprint']==r['fingerprint'],'TARGET_MISMATCH')
        finally:reader.close()
        def intent(cfg,s):
            b,r=self.run(s);require(r['phase']=='SAVE_ALL_CALIBRATION' and r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            require(b['new_transactions_reserved']<min(b['authorized_new_download_limit'],b['configured_new_download_limit']),'LIMIT_REACHED')
            require(content.inventory(self.store.root,r['destination'])==[],'DESTINATION_NONEMPTY')
            previous=strict_json(r['checkpoint']['evidence'].encode(),'INVALID_CALIBRATION_RECORD')
            require(previous['closure']['layout_key']==fresh['layout_key'] and previous['closure']['pid']==fresh['pid']
                and previous['closure']['window_id']==fresh['window_id'],'CALIBRATION_LAYOUT_DRIFT')
            cal=previous['calibration'];action='ACTION-'+uuid.uuid4().hex
            r['intent']=dict(action_id=action,committed_at=utc_now(),owner_execution_id=self.owner,group_key=cfg['group_key'],
                fingerprint=r['fingerprint'],destination=r['destination'],calibration=cal,save_all_retry_allowed=False,
                dispatch_outcome='NOT_ATTEMPTED',trigger_outcome='NOT_APPLICABLE')
            r['intent_state']='INTENT_COMMITTED';b['new_transactions_reserved']+=1
            self.event(r,'SAVE_ALL_INTENT_COMMITTED',dict(fresh=fresh,action_id=action))
            return dict(status='ORIGINAL_INTENT_COMMITTED',run_id=r['run_id'],action_id=action,owner=self.owner,
                fingerprint=r['fingerprint'],destination=r['destination'],frame_id=fresh['frame_id'],session_id=m['session_id'],
                ellipsis=cal['ellipsis'],save_all=cal['save_all_point'])
        result=self.store.update(expected,intent);result['new_intent']=True
        return result

    def dispatch(self,expected,evidence,chooser,download_started):
        def record(cfg,s):
            b,r=self.run(s);require(r['intent'] is not None and r['dispatch_evidence'] is None,'DISPATCH_ALREADY_RECORDED')
            d=evidence
            require(d['run_id']==r['run_id'] and d['action_id']==r['intent']['action_id'] and d['execution_id']==self.owner,'DISPATCH_IDENTITY')
            r['dispatch_evidence']=copy.deepcopy(d)
            confirmed=(d['save_all_click_count']==1 and d['save_all_invocation_attempted'] is True
                and d['folder_chooser_appeared'] is True and d['download_started'] is True and download_started is True)
            require(chooser['destination']==r['destination'] and chooser['confirmation_attempts']==1
                and chooser['full_path']==r['destination'] and chooser['leaf']==Path(r['destination']).name,'CHOOSER_DESTINATION_MISMATCH')
            require(chooser['action_id']==r['intent']['action_id'] and chooser['session_id']==b['owner_execution_id'],'FOREIGN_CHOOSER')
            r['intent']['dispatch_outcome']='RETURNED' if confirmed else 'UNKNOWN'
            r['intent']['trigger_outcome']='TRIGGER_CONFIRMED' if confirmed else 'UNKNOWN'
            r['intent_state']='TRIGGER_CONFIRMED' if confirmed else 'TRIGGER_UNKNOWN'
            r['dispatch_state']='SAVE_ALL_RETURNED' if confirmed else 'UNKNOWN'
            r['manual_reconciliation_required']=not confirmed
            r['reconciliation_reason']=None if confirmed else 'Dispatch uncertain; original intent never authorizes replay.'
            self.event(r,'DOWNLOAD_STARTED' if confirmed else 'TRIGGER_UNKNOWN',dict(dispatch=evidence,chooser=chooser))
            return dict(status='DOWNLOAD_STARTED' if confirmed else 'UNRESOLVED_STOP')
        return self.store.update(expected,record)

    def finalize(self,expected,decoder,decoder_sha,*,verify_options=None):
        if verify_options is not None:
            installed=Path(__file__).resolve().parents[2]
            require(Path(self.store.root).is_relative_to(installed/'harness-development') and '/fixtures/' in self.store.root,
                'FIXTURE_IO_REFUSED_FOR_LIVE_PROJECT')
        snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
        b,r=self.run(snap['state'])
        require(r['intent_state']=='TRIGGER_CONFIRMED' and r['phase']=='DOWNLOAD_STARTED','DOWNLOAD_NOT_CONFIRMED')
        verification,proof=content.verify(self.store.root,r['destination'],r['fingerprint']['expected_images'],snap['config'],decoder,decoder_sha,
            **(verify_options or {}))
        evidence_dir=self.artifact_dir+'/album-'+r['run_id']
        reader=ProjectReader(self.store.root)
        try:
            parent=reader.open(self.artifact_dir,directory=True)
            try:os.mkdir('album-'+r['run_id'],0o700,dir_fd=parent)
            finally:os.close(parent)
        finally:reader.close()
        evidence=Service(self.store.root,self.owner,evidence_dir,self.store.authorization_path)
        vref=evidence.publish('filesystem-verification.json',verification)
        pref=evidence.publish('pixel-and-stability.json',proof)
        join=dict(record_version='1.0',kind='actual_cua_source_identity_join',join_authority='authoritative_exact_join',
            app_identifier=snap['config']['app_identifier'],group_key=r['group_key'],run_id=r['run_id'],fingerprint=r['fingerprint'],
            destination=r['destination'],evidence=[dict(path=self.store.root+'/'+ref['path'],bytes=ref['bytes'],sha256=ref['sha256']) for ref in (vref,pref)],
            transaction=copy.deepcopy(r['events']),test_mode=verify_options is not None)
        jref=evidence.publish('source-identity-join.json',join)
        reference='join:'+jref['path']+':'+jref['sha256']
        def finish(cfg,s):
            b,current=self.run(s)
            require(current['run_id']==r['run_id'] and current['intent_state']=='TRIGGER_CONFIRMED','FINALIZE_IDENTITY')
            require(content.inventory(self.store.root,current['destination'])==verification['inventory'],'CONTENT_CHANGED_BEFORE_COMMIT')
            current['verification']=verification;current['workflow_outcome']='VERIFIED';current['stop_reason']='COMPLETED'
            event=dict(phase='VERIFIED',at=utc_now(),evidence=reference)
            current['events'].append(event);current['phase']='VERIFIED';current['checkpoint']=event
            s['verified_albums'].append(dict(group_key=current['group_key'],fingerprint=current['fingerprint'],
                verified_run_id=current['run_id'],destinations=[current['destination']],source_kind='filesystem_verification',evidence=reference))
            s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None;b['next_index']+=1
            return dict(status='VERIFIED',run_id=current['run_id'],fingerprint=current['fingerprint'],verification_reference=vref)
        return self.store.update(expected,finish)

    def stop(self,expected,reason):
        def stop(cfg,s):
            b=self.batch(s)
            if b['current_album_run_id'] is not None:
                _,r=self.run(s);r['workflow_outcome']='SAFE_ABORT';r['stop_reason']=reason
                r['manual_reconciliation_required']=r['intent'] is not None
                r['reconciliation_reason']='Stopped with non-retryable intent; reconcile only.' if r['intent'] else None
                self.event(r,'SAFE_ABORT',dict(reason=reason))
                s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None
            b['phase']='STOPPED';b['stop_reason']=reason
            return dict(status='STOPPED',reason=reason,replay_allowed=False)
        return self.store.update(expected,stop)

    def finish(self,expected,final_records,session):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            b=self.batch(snap['state']);m=self.manifest(b,reader,snap['config'])
            final=catalog(reader,final_records,snap['config'],session)
            require(final==m['identities'],'FINAL_COLLECTION_DRIFT')
            all_done=all(self.eligible(snap['state'],fp)=='SKIP_VERIFIED' for fp in final)
        finally:reader.close()
        def finish(cfg,s):
            b=self.batch(s);require(b['current_album_run_id'] is None,'ALBUM_BUSY')
            b['phase']='COMPLETED' if all_done else 'STOPPED'
            exhausted=b['new_transactions_reserved']>=min(b['authorized_new_download_limit'],b['configured_new_download_limit'])
            b['stop_reason']='ALL_COMPLETE' if all_done else ('LIMIT_REACHED' if exhausted else 'INCOMPLETE')
            return dict(status=b['stop_reason'],live_acceptance_required=True)
        return self.store.update(expected,finish)

    def resume(self):
        snapshot=self.store.snapshot()
        return dict(receipt=snapshot['receipt'],status='RECONCILE_ONLY',dispatch_authorized=False,
            additional_save_all_calls=0,active_batch=snapshot['state']['active_batch'])

    def release(self,expected):
        def release(cfg,s):
            b=s['active_batch']
            require(b is not None and b['owner_execution_id']==self.owner and b['phase'] in ('STOPPED','COMPLETED'),
                'TERMINAL_BATCH_REQUIRED')
            require(b['current_album_run_id'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'ALBUM_BUSY')
            require(all(r['workflow_outcome']=='VERIFIED' or (r['workflow_outcome']=='SAFE_ABORT' and r['intent'] is None
                and not r['manual_reconciliation_required']) for r in s['runs']),'UNRESOLVED_BARRIER')
            result=dict(status='BATCH_RELEASED',batch_id=b['batch_id'],prior_phase=b['phase'],stop_reason=b['stop_reason'])
            s['active_batch']=None
            return result
        return self.store.update(expected,release)
