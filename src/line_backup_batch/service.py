"""Canonical batch transitions. No GUI code, no imported historical operator."""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import uuid
from line_backup_acceptance.common import AcceptanceError,json_bytes,utc_now,_check_calibration
from line_backup_acceptance.project_binding import ProjectReader,strict_json,history_decision,integer,sha
from .schema import require,POLICY
from .store import Store
from .observations import artifact,catalog,card_target,chooser_observation,validate_download_start,frame,point,rect,_support
from . import content

DISPATCH_RECEIPT_V1_KEYS={'version','run_id','action_id','execution_id','session_id','pair_frame_id','popup_frame_id',
    'support','guard','reservations','events','chooser','download_started','save_all_click_count','cease_input'}
DISPATCH_RECEIPT_V2_KEYS=(DISPATCH_RECEIPT_V1_KEYS-{'download_started'})|{'chooser_phases','confirmation_frame',
    'confirmation_point','download_evidence'}
DISPATCH_EVENT_ORDER_V1=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
    'SAVE_ALL_RETURNED','CONFIRM_INVOCATION','CEASE_INPUT_AFTER_DOWNLOAD_START']
DISPATCH_EVENT_ORDER_V2=['ELLIPSIS_INVOCATION','ELLIPSIS_RETURNED','SCK_MENU_GUARD_PASS','SAVE_ALL_INVOCATION',
    'SAVE_ALL_RETURNED','CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED',
    'CONFIRM_INVOCATION','CONFIRM_ATTEMPTED','DOWNLOAD_EVIDENCE_OBSERVED','CEASE_INPUT_AFTER_DOWNLOAD_START']

def run_barrier_ok(run):
    return (run['workflow_outcome']=='VERIFIED' or (run['workflow_outcome']=='SAFE_ABORT'
        and run['intent'] is None and not run['manual_reconciliation_required']))

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
        return self.store._update(expected,acquire,operation='begin')

    def manifest(self,b,reader,cfg):
        require(b['manifest_reference'] is not None,'MANIFEST_REQUIRED')
        m=strict_json(artifact(reader,b['manifest_reference']),'INVALID_MANIFEST')
        require(set(m)=={'version','project_root','group_key','config_sha256','source_sha256','session_id','identities','frames','policy'},'INVALID_MANIFEST')
        require(m['version']==1 and m['policy']==POLICY and m['project_root']==self.store.root and m['group_key']==cfg['group_key']
            and m['config_sha256']==b['config_sha256'] and m['source_sha256']==b['source_sha256'],'MANIFEST_AUTHORITY_DRIFT')
        # Coverage was classified before admission; retained images/proofs rehash every use.
        for observation in m['frames']:
            frame(reader,observation,cfg,session=m['session_id'],max_age=None)
            artifact(reader,observation['boundary']['evidence'])
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
        return self.store._update(expected,admit,operation='admit')

    @staticmethod
    def eligible(s,target):
        view=copy.deepcopy(s);view['active_batch']=None
        return history_decision(view,dict(fingerprint=target),{r['run_id']:r for r in view['runs']})[0]

    @staticmethod
    def event(r,phase,evidence):
        e=dict(phase=phase,at=utc_now(),evidence=json.dumps(evidence,ensure_ascii=False,sort_keys=True))
        r['phase']=phase;r['checkpoint']=e;r['events'].append(e)

    def prepare(self,expected,observation,*,fault=None):
        if fault is not None:
            require(self.store.fixture and fault in ('AFTER_INTENT','AFTER_MKDIR'),'INVALID_PREPARE_FAULT')
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
        relative=f"backups/{snap['config']['group_name']}/{target['start_date']}_{target['end_date']}_{target['expected_images']}張"
        effects=dict(intent=False,lease=False,destination=False)
        def prepare(cfg,s):
            b=self.batch(s)
            require(b['next_index']==index and b['current_album_run_id'] is None,'ALBUM_BUSY')
            require(self.eligible(s,target)==decision,'HISTORY_DRIFT')
            if decision=='SKIP_VERIFIED':
                b['next_index']+=1;return dict(status='SKIP_VERIFIED',fingerprint=target)
            require(cfg['group_name']==snap['config']['group_name'],'CONFIG_GROUP_DRIFT')
            destination=self.store.root+'/'+relative
            self.publish('filesystem-intent-'+run_id+'.json',dict(version='line-backup-filesystem-intent-1',run_id=run_id,
                batch_id=b['batch_id'],owner=self.owner,destination=destination,expected_images=target['expected_images'],
                created_at=utc_now(),state='PUBLISHED'))
            effects['intent']=True
            self.publish('lease-'+run_id+'.json',dict(version='line-backup-transaction-lease-1',run_id=run_id,
                batch_id=b['batch_id'],owner=self.owner,destination=destination,acquired_at=utc_now(),state='OPEN'))
            effects['lease']=True
            if fault=='AFTER_INTENT':raise AcceptanceError('FIXTURE_FAULT_AFTER_INTENT','fixture fault after intent',4)
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
            effects['destination']=True
            if fault=='AFTER_MKDIR':raise AcceptanceError('FIXTURE_FAULT_AFTER_MKDIR','fixture fault after mkdir',4)
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
        try:
            return self.store._update(expected,prepare,operation='prepare')
        except Exception as exc:
            if any(effects.values()):
                try:
                    self.publish('side-effect-'+run_id+'-'+uuid.uuid4().hex+'.json',dict(version='line-backup-side-effect-1',
                        run_id=run_id,intent_published=effects['intent'],lease_published=effects['lease'],
                        destination_created=effects['destination'],destination=self.store.root+'/'+relative,at=utc_now(),
                        failure=f'{type(exc).__name__}:{exc}',code=getattr(exc,'code',None)))
                except Exception:pass
            raise

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
            if not self.store.fixture:
                claim=strict_json(artifact(reader,menu['evidence']),'INVALID_MENU_CALIBRATION_EVIDENCE')
                ckeys={'version','kind','run_id','session_id','detail','menu_frame','trigger','label','support','guard',
                    'save_all','safe_bounds','opened_at','closed_at','latency_ms','reservation_id','reservation_state'}
                require(isinstance(claim,dict) and set(claim)==ckeys and claim.get('version')==1
                    and claim.get('kind')=='menu-calibration' and claim.get('run_id')==r['run_id']
                    and claim.get('session_id')==m['session_id'] and claim.get('detail')==detail
                    and claim.get('label')==menu['label'] and claim.get('label') in ('儲存全部','Save All')
                    and claim.get('safe_bounds')==safe and claim.get('save_all')==calibration['save_all_point']
                    and calibration.get('evidence')==claim.get('support',{}).get('sha256')
                    and claim.get('reservation_state')=='CONSUMED' and type(claim.get('latency_ms')) in (int,float)
                    and 0<=claim['latency_ms']<=5000,'MENU_CALIBRATION_BINDING')
                closed=dt.datetime.fromisoformat(claim['closed_at'].replace('Z','+00:00'))
                opened=dt.datetime.fromisoformat(claim['opened_at'].replace('Z','+00:00'))
                require(opened.tzinfo is not None and closed.tzinfo is not None and closed>=opened
                    and (closed-opened).total_seconds()<=6,
                    'MENU_CALIBRATION_TIME')
                frame(reader,claim['detail'],snap['config'],session=m['session_id'])
                frame(reader,claim['menu_frame'],snap['config'],session=m['session_id'])
                trigger=claim['trigger'];guard=claim['guard']
                require(isinstance(trigger,dict) and trigger.get('frameId')==detail['frame_id']
                    and trigger.get('point')==calibration['ellipsis'] and trigger.get('bounds_px')==menu['ellipsis_bounds']
                    and isinstance(guard,dict) and set(guard)=={'verdict','provider','pairFrameId','popupFrameId','supportSha256','actionPoint'}
                    and guard.get('verdict')=='PASS' and guard.get('provider')=='SCREEN_CAPTURE_KIT'
                    and guard.get('pairFrameId')==claim['menu_frame']['frame_id']
                    and guard.get('supportSha256')==claim['support']['sha256']
                    and guard.get('actionPoint')==calibration['save_all_point'],'MENU_NATIVE_GUARD_REQUIRED')
                menu_support=_support(reader,claim['support'],claim['menu_frame'],snap['config'],
                    now=closed.astimezone(dt.timezone.utc),max_age=5)
                popup_raw=artifact(reader,menu_support['sidecar']['sck_frame'])
                require(guard.get('popupFrameId')==sha(popup_raw),'MENU_NATIVE_POPUP_BINDING')
                require(self.store.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
                from .cli import authorize
                grant=authorize(self.store.root,self.store.authorization_path,False,'calibrate')
                reservation=self.store.gui_reservation_fact(grant['gui_ledger'],claim['reservation_id'])
                require(reservation['kind']=='menu_calibration' and reservation['count']==2
                    and reservation['owner']==self.owner and reservation['run_id']==r['run_id'],
                    'MENU_CALIBRATION_RESERVATION')
        finally:reader.close()
        def calibrate(cfg,s):
            b,r=self.run(s);require(r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            s['context_lock']=dict(group_key=cfg['group_key'],source='RELIABLE_VISUAL_NAVIGATION',confirmed_at=utc_now(),
                execution_id=self.owner,continuity_evidence=json.dumps(closure,ensure_ascii=False,sort_keys=True))
            self.event(r,'SAVE_ALL_CALIBRATION',dict(detail=detail,calibration=calibration,menu=menu,closure=closure))
            return dict(status='CALIBRATED',run_id=r['run_id'])
        return self.store._update(expected,calibrate,operation='calibrate')

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
                ellipsis=cal['ellipsis'],save_all=cal['save_all_point'],dispatch_authorized=not self.store.fixture,
                fixture=self.store.fixture)
        result=self.store._update(expected,intent,operation='intent');result['new_intent']=True
        return result

    def dispatch(self,expected,evidence,chooser,download_started,receipt=None):
        receipt_data=None;download_proven=False;download_ref=None
        if receipt is not None:
            reader=ProjectReader(self.store.root)
            try:
                receipt_data=strict_json(artifact(reader,receipt),'INVALID_DISPATCH_RECEIPT')
                require(isinstance(receipt_data,dict),'INVALID_DISPATCH_RECEIPT')
                version=receipt_data.get('version')
                if version=='cua-dispatch-receipt-1':
                    require(self.store.fixture and set(receipt_data)==DISPATCH_RECEIPT_V1_KEYS,'INVALID_DISPATCH_RECEIPT')
                    require(receipt_data['download_started'] is True and receipt_data['cease_input'] is True
                        and receipt_data['save_all_click_count']==1,'RECEIPT_TRIGGER_UNPROVEN')
                    event_order=DISPATCH_EVENT_ORDER_V1;download_proven=True
                else:
                    require(version=='cua-dispatch-receipt-2' and set(receipt_data)==DISPATCH_RECEIPT_V2_KEYS,
                        'INVALID_DISPATCH_RECEIPT')
                    require(receipt_data['cease_input'] is True and receipt_data['save_all_click_count']==1,
                        'RECEIPT_TRIGGER_UNPROVEN')
                    event_order=DISPATCH_EVENT_ORDER_V2
                    require(self.store.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
                    from .cli import authorize
                    grant=authorize(self.store.root,self.store.authorization_path,False,'dispatch')
                    require(grant['grant_version']=='line-batch-execution-grant-2','LIVE_RECEIPT_V2_REQUIRED')
                    events=receipt_data['events']
                    require(isinstance(events,list) and all(isinstance(e,dict) and set(e)=={'event','at'}
                        and isinstance(e.get('event'),str) and isinstance(e.get('at'),str) for e in events),
                        'RECEIPT_EVENTS')
                    actual_now=dt.datetime.now(dt.timezone.utc)
                    try:
                        parsed_event_times=[dt.datetime.fromisoformat(e['at'].replace('Z','+00:00')) for e in events]
                    except (TypeError,ValueError):
                        raise AcceptanceError('RECEIPT_EVENT_TIME','receipt event time is invalid',4)
                    require(all(value.tzinfo is not None and value<=actual_now for value in parsed_event_times)
                        and all(a<=b for a,b in zip(parsed_event_times,parsed_event_times[1:])),
                        'RECEIPT_EVENT_TIME_ORDER')
                    phase_event_names=['CHOOSER_APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED']
                    phase_events={event['event']:parsed_event_times[index] for index,event in enumerate(events)
                        if event['event'] in phase_event_names}
                    require(set(phase_events)==set(phase_event_names),'CHOOSER_PHASE_EVENTS')
                    proofs=receipt_data['chooser_phases']
                    require(isinstance(proofs,list) and len(proofs)==len(('APPEARED','GO_TO_FOLDER','PATH_FILLED',
                        'DESTINATION_SELECTED','CONFIRM_ATTEMPTED')),'CHOOSER_PHASE_PROOFS')
                    envelopes=[];previous=None
                    for index,ref in enumerate(proofs):
                        envelope=strict_json(artifact(reader,ref),'INVALID_CHOOSER_PHASE')
                        expected_phase=('APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED')[index]
                        require(envelope.get('phase')==expected_phase,'CHOOSER_PHASE_ORDER')
                        event_time=phase_events[phase_event_names[index]]
                        try:
                            captured_time=dt.datetime.fromisoformat(envelope['frame']['captured_at'].replace('Z','+00:00'))
                        except (AttributeError,TypeError,ValueError):
                            raise AcceptanceError('CHOOSER_PHASE_TIME','chooser frame time is invalid',4)
                        require(captured_time.tzinfo is not None and event_time.tzinfo is not None
                            and captured_time<=event_time<=actual_now and (event_time-captured_time).total_seconds()<=5
                            and (actual_now-captured_time).total_seconds()<=5,
                            'CHOOSER_PHASE_STALE')
                        chooser_observation(reader,envelope,self.store.snapshot()['config'],session=receipt_data['session_id'],
                            owner=self.owner,run_id=receipt_data['run_id'],action_id=receipt_data['action_id'],
                            destination=receipt_data['chooser']['destination'],previous=previous,now=actual_now)
                        require(envelope['dispatch']['original_frame_id']==receipt_data['pair_frame_id'],
                            'CHOOSER_ORIGINAL_FRAME_BINDING')
                        envelopes.append(envelope);previous=envelope
                    appeared,selected,attempted=envelopes[0],envelopes[3],envelopes[4]
                    require(receipt_data['chooser'].get('frame_id')==appeared['frame']['frame_id']
                        and receipt_data['chooser'].get('confirmation_frame_id')==selected['frame']['frame_id']
                        and attempted['control'].get('confirmation_frame_id')==selected['frame']['frame_id'],
                        'RECEIPT_CHOOSER_SUMMARY_BINDING')
                    require(receipt_data['confirmation_frame']==selected['frame']['frame'],
                        'CHOOSER_CONFIRMATION_FRAME_BINDING')
                    require(receipt_data['confirmation_point']==selected['control'].get('confirm_point')
                        and isinstance(receipt_data['confirmation_point'],list)
                        and len(receipt_data['confirmation_point'])==2
                        and all(type(v) is int for v in receipt_data['confirmation_point']),
                        'CHOOSER_CONFIRMATION_POINT_BINDING')
                    confirm_events=[e for e in events if isinstance(e,dict) and e.get('event')=='CONFIRM_INVOCATION']
                    observed_events=[e for e in events if isinstance(e,dict) and e.get('event')=='DOWNLOAD_EVIDENCE_OBSERVED']
                    require(len(confirm_events)==len(observed_events)==1 and isinstance(confirm_events[0].get('at'),str)
                        and isinstance(observed_events[0].get('at'),str),'RECEIPT_DOWNLOAD_ORDER')
                    download_ref=receipt_data['download_evidence']
                    validate_download_start(reader,download_ref,run_id=receipt_data['run_id'],
                        action_id=receipt_data['action_id'],owner=self.owner,session=receipt_data['session_id'],
                        destination=receipt_data['chooser']['destination'],confirmation_frame_id=selected['frame']['frame_id'],
                        confirmation_invoked_at=confirm_events[0]['at'],now=actual_now)
                    require(observed_events[0]['at']==strict_json(artifact(reader,download_ref),
                        'INVALID_DOWNLOAD_EVIDENCE')['observed_at'],'RECEIPT_DOWNLOAD_TIME_BINDING')
                    download_proven=True
                require(receipt_data['run_id'] and receipt_data['action_id'] and receipt_data['execution_id']==self.owner
                    and receipt_data['session_id'],'RECEIPT_IDENTITY')
                support=strict_json(artifact(reader,receipt_data['support']),'INVALID_SCK_SUPPORT')
                require(support.get('frame_id')==receipt_data['pair_frame_id']
                    and support.get('session_id')==receipt_data['session_id'],'RECEIPT_SUPPORT_BINDING')
                popup_raw=artifact(reader,support.get('sck_frame'))
                require(sha(popup_raw)==receipt_data['popup_frame_id']
                    and receipt_data['popup_frame_id']!=receipt_data['pair_frame_id'],'RECEIPT_POPUP_BINDING')
                guard=receipt_data['guard']
                require(isinstance(guard,dict) and guard.get('verdict')=='PASS' and guard.get('provider')=='SCREEN_CAPTURE_KIT'
                    and guard.get('pairFrameId')==receipt_data['pair_frame_id']
                    and guard.get('popupFrameId')==receipt_data['popup_frame_id']
                    and guard.get('supportSha256')==receipt_data['support']['sha256'],'RECEIPT_GUARD_UNPROVEN')
                events=receipt_data['events']
                allowed_event_shapes=({'event'},{'event','at'}) if version=='cua-dispatch-receipt-1' else ({'event','at'},)
                require(isinstance(events,list) and all(isinstance(item,dict) and set(item) in allowed_event_shapes
                    and isinstance(item.get('event'),str) for item in events),'RECEIPT_EVENTS')
                names=[item['event'] for item in events]
                expected_names=event_order
                if version=='cua-dispatch-receipt-1':
                    require(set(names)<=set(event_order)|{'ALBUM_OPEN_INVOCATION'},'RECEIPT_EVENTS')
                    names=[name for name in names if name!='ALBUM_OPEN_INVOCATION']
                require(names==expected_names,'RECEIPT_EVENT_ORDER')
                if version=='cua-dispatch-receipt-2':
                    try:event_times=[dt.datetime.fromisoformat(item['at'].replace('Z','+00:00')) for item in events]
                    except (TypeError,ValueError):raise AcceptanceError('RECEIPT_EVENT_TIME','receipt event time is invalid',4)
                    require(all(value.tzinfo is not None for value in event_times)
                        and all(a<=b for a,b in zip(event_times,event_times[1:])),'RECEIPT_EVENT_TIME_ORDER')
                reservations=receipt_data['reservations']
                require(isinstance(reservations,list) and len(reservations)==2
                    and all(isinstance(item,dict) for item in reservations),'RECEIPT_RESERVATIONS')
                by_kind={item.get('kind'):item for item in reservations}
                require(set(by_kind)=={'dispatch_inputs','chooser_inputs'} and by_kind['dispatch_inputs'].get('count')==2
                    and by_kind['chooser_inputs'].get('count')==4,'RECEIPT_RESERVATIONS')
                require(all(item.get('state')=='CONSUMED' and isinstance(item.get('reservation_id'),str) and item['reservation_id']
                    for item in reservations),'RECEIPT_RESERVATIONS')
                if not self.store.fixture:
                    for item in reservations:
                        fact=self.store.gui_reservation_fact(grant['gui_ledger'],item['reservation_id'])
                        require(fact['kind']==item['kind'] and fact['count']==item['count']
                            and fact['owner']==self.owner and fact['run_id']==receipt_data['run_id'],'RECEIPT_RESERVATION_DRIFT')
            finally:reader.close()
        elif not self.store.fixture:
            raise AcceptanceError('RETAINED_RECEIPT_REQUIRED','live dispatch requires a retained adapter receipt',4)
        def record(cfg,s):
            b,r=self.run(s);require(r['intent'] is not None and r['dispatch_evidence'] is None,'DISPATCH_ALREADY_RECORDED')
            d=copy.deepcopy(evidence)
            require(d['run_id']==r['run_id'] and d['action_id']==r['intent']['action_id'] and d['execution_id']==self.owner,'DISPATCH_IDENTITY')
            if receipt_data is not None:
                require(receipt_data['run_id']==r['run_id'] and receipt_data['action_id']==r['intent']['action_id']
                    and receipt_data['execution_id']==self.owner and receipt_data['session_id']==b['owner_execution_id'],'RECEIPT_IDENTITY')
                require(json_bytes(receipt_data['chooser'])==json_bytes(chooser),'RECEIPT_CHOOSER_MISMATCH')
                point=receipt_data['guard']['actionPoint']
                require(json_bytes(point)==json_bytes(r['intent']['calibration']['save_all_point']),'RECEIPT_GUARD_POINT')
                require(d['save_all_click_count']==receipt_data['save_all_click_count'],'RECEIPT_CLICK_COUNT')
            if receipt_data is not None and receipt_data['version']=='cua-dispatch-receipt-2':
                intent_events=[event for event in r['events'] if event.get('phase')=='SAVE_ALL_INTENT_COMMITTED']
                require(len(intent_events)==1,'INTENT_CONTEXT_EVIDENCE')
                intent_evidence=strict_json(intent_events[0]['evidence'].encode(),'INTENT_CONTEXT_EVIDENCE')
                fresh=intent_evidence.get('fresh')
                origin={'frame_id':fresh.get('frame_id'),'pid':fresh.get('pid'),'window_id':fresh.get('window_id'),
                    'layout_key':fresh.get('layout_key')} if isinstance(fresh,dict) else None
                require(origin is not None and origin['frame_id']==receipt_data['pair_frame_id']
                    and all(envelope['dispatch']['original_context']==origin for envelope in envelopes)
                    and all(envelope['frame']['pid']==origin['pid'] for envelope in envelopes),
                    'CHOOSER_ORIGIN_CONTEXT')
                chooser_phases=envelopes[:4]
                require(all(envelope['frame']['window_id']==chooser_phases[0]['frame']['window_id']
                    and envelope['frame']['layout_key']==chooser_phases[0]['frame']['layout_key']
                    for envelope in chooser_phases),'CHOOSER_CONTEXT_DRIFT')
                d['download_started']=download_proven
                d['folder_chooser_appeared']=True
                require(d['download_started'] is True,'DOWNLOAD_START_NOT_OBSERVED')
            r['dispatch_evidence']=copy.deepcopy(d)
            confirmed=(d['save_all_click_count']==1 and d['save_all_invocation_attempted'] is True
                and d['folder_chooser_appeared'] is True and d['download_started'] is True
                and (download_proven if receipt_data and receipt_data['version']=='cua-dispatch-receipt-2' else download_started is True))
            require(chooser['destination']==r['destination'] and chooser['confirmation_attempts']==1
                and chooser['full_path']==r['destination'] and chooser['leaf']==Path(r['destination']).name,'CHOOSER_DESTINATION_MISMATCH')
            require(chooser['action_id']==r['intent']['action_id'] and chooser['session_id']==b['owner_execution_id'],'FOREIGN_CHOOSER')
            r['intent']['dispatch_outcome']='RETURNED' if confirmed else 'UNKNOWN'
            r['intent']['trigger_outcome']='TRIGGER_CONFIRMED' if confirmed else 'UNKNOWN'
            r['intent_state']='TRIGGER_CONFIRMED' if confirmed else 'TRIGGER_UNKNOWN'
            r['dispatch_state']='SAVE_ALL_RETURNED' if confirmed else 'UNKNOWN'
            r['manual_reconciliation_required']=not confirmed
            r['reconciliation_reason']=None if confirmed else 'Dispatch uncertain; original intent never authorizes replay.'
            self.event(r,'DOWNLOAD_STARTED' if confirmed else 'TRIGGER_UNKNOWN',dict(dispatch=d,chooser=chooser,
                receipt=receipt,download_evidence=download_ref))
            return dict(status='DOWNLOAD_STARTED' if confirmed else 'UNRESOLVED_STOP')
        return self.store._update(expected,record,operation='dispatch')

    def task_json(self,path,code):
        reader=ProjectReader(self.store.root)
        try:raw,_=reader.read(path,code)
        finally:reader.close()
        return strict_json(raw,code)

    def finalize(self,expected,decoder,decoder_sha,*,verify_options=None,fault=None):
        if verify_options is not None:
            installed=Path(__file__).resolve().parents[2]
            require(Path(self.store.root).is_relative_to(installed/'harness-development') and '/fixtures/' in self.store.root,
                'FIXTURE_IO_REFUSED_FOR_LIVE_PROJECT')
        if fault is not None:
            require(self.store.fixture and fault=='DRIFT_AFTER_COMMIT','INVALID_FINALIZE_FAULT')
        snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
        b,r=self.run(snap['state'])
        require(r['intent_state']=='TRIGGER_CONFIRMED' and r['phase']=='DOWNLOAD_STARTED','DOWNLOAD_NOT_CONFIRMED')
        verification,proof=content.verify(self.store.root,r['destination'],r['fingerprint']['expected_images'],snap['config'],decoder,decoder_sha,
            **(verify_options or {}))
        lease=self.task_json(self.artifact_dir+'/lease-'+r['run_id']+'.json','LEASE_REQUIRED')
        require(isinstance(lease,dict) and lease.get('version')=='line-backup-transaction-lease-1'
            and lease.get('run_id')==r['run_id'] and lease.get('batch_id')==b['batch_id'] and lease.get('owner')==self.owner
            and lease.get('destination')==r['destination'] and lease.get('state')=='OPEN','LEASE_MISMATCH')
        relative=r['destination'][len(self.store.root)+1:]
        identity_reader=ProjectReader(self.store.root)
        try:
            fd=identity_reader.open(relative,directory=True)
            try:dest_ident=ProjectReader.ident(os.fstat(fd))
            finally:os.close(fd)
        finally:identity_reader.close()
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
            identity=ProjectReader(self.store.root)
            try:
                fd=identity.open(relative,directory=True)
                try:require(ProjectReader.ident(os.fstat(fd))==tuple(dest_ident),'DESTINATION_IDENTITY_DRIFT')
                finally:os.close(fd)
            finally:identity.close()
            current['verification']=verification;current['workflow_outcome']='VERIFIED';current['stop_reason']='COMPLETED'
            event=dict(phase='VERIFIED',at=utc_now(),evidence=reference)
            current['events'].append(event);current['phase']='VERIFIED';current['checkpoint']=event
            s['verified_albums'].append(dict(group_key=current['group_key'],fingerprint=current['fingerprint'],
                verified_run_id=current['run_id'],destinations=[current['destination']],source_kind='filesystem_verification',evidence=reference))
            s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None;b['next_index']+=1
            return dict(status='VERIFIED',run_id=current['run_id'],fingerprint=current['fingerprint'],verification_reference=vref)
        outcome=self.store._update(expected,finish,operation='finalize')
        if fault=='DRIFT_AFTER_COMMIT':
            (Path(r['destination'])/'post-commit-drift.png').write_bytes(b'\x89PNG\r\n\x1a\npost-commit fixture drift')
        try:
            post=content.inventory(self.store.root,r['destination'])
            require(post==verification['inventory'],'FINALIZE_READBACK_UNCERTAIN')
        except Exception as exc:
            failure=getattr(exc,'code',None) or str(exc)
            self.publish('finalize-drift-'+r['run_id']+'.json',dict(version='line-backup-finalize-drift-1',run_id=r['run_id'],
                state_committed=True,state_revision=outcome['receipt']['revision'],
                pre_inventory_sha256=sha(json_bytes(verification['inventory'])),post_inventory_sha256=None,
                at=utc_now(),failure=failure))
            self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
                state='UNVERIFIED',state_revision=outcome['receipt']['revision'],at=utc_now()))
            raise AcceptanceError('FINALIZE_READBACK_UNCERTAIN',str(exc),4) from exc
        self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
            state='CLOSED',post_inventory_sha256=sha(json_bytes(post)),state_revision=outcome['receipt']['revision'],at=utc_now()))
        return outcome

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
        return self.store._update(expected,stop,operation='stop')

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
            completed=sum(1 for r in s['runs'] if r.get('batch_id')==b['batch_id'] and r['workflow_outcome']=='VERIFIED')
            unresolved=any(not run_barrier_ok(r) for r in s['runs'])
            exhausted=b['new_transactions_reserved']>=min(b['authorized_new_download_limit'],b['configured_new_download_limit'])
            if all_done:
                b['phase']='COMPLETED';b['stop_reason']='ALL_COMPLETE'
            elif b['new_transactions_reserved']==1 and completed==1 and not unresolved:
                b['phase']='STOPPED';b['stop_reason']='CAP_REACHED'
            elif exhausted:
                b['phase']='STOPPED';b['stop_reason']='LIMIT_REACHED'
            else:
                b['phase']='STOPPED';b['stop_reason']='INCOMPLETE'
            return dict(status=b['stop_reason'],live_acceptance_required=True)
        return self.store._update(expected,finish,operation='finish')

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
            require(all(run_barrier_ok(r) for r in s['runs']),'UNRESOLVED_BARRIER')
            result=dict(status='BATCH_RELEASED',batch_id=b['batch_id'],prior_phase=b['phase'],stop_reason=b['stop_reason'])
            s['active_batch']=None
            return result
        return self.store._update(expected,release,operation='release')
