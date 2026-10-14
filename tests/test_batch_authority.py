import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import jsonschema,referencing,attrs,rpds
from unittest.mock import patch
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,ROOT,TASK,identity,sha,json_bytes,token
from line_backup_batch.store import Store,enforce_grant_quota
from line_backup_batch.service import Service,DISPATCH_RECEIPT_V3_KEYS,DISPATCH_EVENT_ORDER_V3
import line_backup_batch.cli as batch_cli
from line_backup_acceptance.common import AcceptanceError,atomic_write_json

SCHEMA_PATHS=sorted({str(Path(module.__file__).resolve().parent.parent)
    for module in (jsonschema,referencing,attrs,rpds)})

def project_authority_fixture(f):
    root=f.root;project='harness-development/line-two-album-pilot-20261014'
    private=root/project/'private';private.mkdir(parents=True)
    (root/project).mkdir(parents=True,exist_ok=True)
    def put(relative,raw,mode=None):
        target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if mode is not None:target.chmod(mode)
        return dict(path=relative,bytes=len(raw),sha256=sha(raw))
    snapshot=Store(str(root)).snapshot();source_sha=snapshot['receipt']['source_sha256']
    config_sha=snapshot['receipt']['config_sha256']
    contract=put(project+'/private/project-contract.json',b'fixture-only project contract')
    producer=put(project+'/private/producer',b'fixture executable producer',0o700)
    decoder=put(project+'/private/decoder',b'fixture executable decoder',0o700)
    entry_bytes=(ROOT/'harness-development/line-two-album-pilot-20261014/two_album_entry.mjs').read_bytes()
    entry=put(project+'/two_album_entry.mjs',entry_bytes)
    callback_sources=[]
    callback_mapping={
        'cli_bridge':'scripts/line_backup_cua_adapter.mjs',
        'capture_analyzer':'src/line_backup_batch/observations.py',
        'classifier_chooser':'scripts/line_backup_cua_adapter.mjs',
        'menu_lineage':'scripts/line_backup_cua_adapter.mjs',
        'retainer':'src/line_backup_batch/cli.py'}
    for role,relative in callback_mapping.items():
        raw=(root/relative).read_bytes()
        callback_sources.append(put(project+f'/private/callback-{role}.mjs',raw)|dict(roles=[role]))
    runtime=dict(version=1,profile='LINE_TWO_ALBUM_PILOT/1',project_root=str(root),source_sha256=source_sha,
        config_sha256=config_sha,source_files=[{k:item[k] for k in ('path','bytes','sha256')} for item in snapshot['source_files']],
        runtime_files=[dict(role='producer_binary',**producer),dict(role='decoder_binding',**decoder),
            dict(role='entry_binding',**entry)],callback_sources=callback_sources)
    runtime_ref=put(project+'/private/runtime-binding.json',json_bytes(runtime))
    consent=put(project+'/private/owner-consent.json',json_bytes(dict(profile='LINE_TWO_ALBUM_PILOT/1',gui_authorized=True,
        source_sha256=source_sha,config_sha256=config_sha)))
    decision=put(project+'/private/owner-decision.json',json_bytes(dict(profile='LINE_TWO_ALBUM_PILOT/1',
        decision='AUTHORIZE_SCOPED_NON_GUI_IMPLEMENTATION',non_gui_authorized=True,live_gui_authorized=True)))
    review_value=dict(profile='LINE_TWO_ALBUM_PILOT/1',verdict='APPROVE_IMPLEMENTATION',head_source_sha256=source_sha,
        entry_sha256=entry['sha256'],runtime_binding_sha256=runtime_ref['sha256'],
        review_method='OWNER_TRANSFERRED_EXTERNAL_PR_REVIEW',disposition_ref='fixture://review',reviewer='independent-fixture-reviewer')
    review=put(project+'/private/implementation-review.json',json_bytes(review_value))
    readiness=put(project+'/private/live-readiness.json',json_bytes(dict(profile='LINE_TWO_ALBUM_PILOT/1',gui_ready=True,
        owner_foreground_handoff=True,independent_acceptance_access=True,physical_delivery='POLICY_ACCEPTED_LOGICAL_ONLY',
        source_sha256=source_sha,config_sha256=config_sha,entry_sha256=entry['sha256'],
        runtime_binding_sha256=runtime_ref['sha256'],owner_consent_ref=consent)))
    grant=dict(grant_version='line-two-album-project-grant-1',task_id='PILOT-runtime-fixture',project_root=str(root),
        fixture=False,artifact_dir=project+'/private',owner=f.owner,operations=['begin','gui_initialize','admit','prepare','calibrate',
            'intent','dispatch','finalize','stop','release','resume','gui_reserve','gui_consume','gui_phase','gui_observe'],config_sha256=config_sha,
        source_sha256=source_sha,album_quota=2,lifecycle_album_limit=1,save_all_dispatch_limit=2,
        chooser_confirmation_limit=2,reversible_gui_invocation_limit=23,contract_path=project+'/private/project-contract.json',
        contract_sha256=contract['sha256'],native_binary_sha256=decoder['sha256'],gui_ledger=project+'/private/gui-ledger.json',
        producer_binary=producer,runtime_binding=runtime_ref,sensor_scope=dict(bundle_id='jp.naver.line.mac',
            provider='SCREEN_CAPTURE_KIT',capture_scope='FULL_DISPLAY',surfaces=['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER']),
        project_profile='LINE_TWO_ALBUM_PILOT/1',owner_decision=decision,external_review=review,live_readiness=readiness,
        decoder_binding=decoder,entry_binding=entry)
    grant_ref=put(project+'/private/grant.json',json_bytes(grant))
    return grant,grant_ref,runtime_ref

class AuthorityTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def test_cli_explicit_authority_and_opaque_receipt(self):
        run=subprocess.run
        def with_schema_env(argv,**kwargs):
            env=dict(kwargs.get('env',{}));env['PYTHONPATH']=os.pathsep.join([str(ROOT/'src'),*SCHEMA_PATHS])
            kwargs['env']=env;return run(argv,**kwargs)
        with patch('subprocess.run',side_effect=with_schema_env):p,_=self.f.cli('begin',dict(mode='backup_batch',limit=1))
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout);self.assertNotIn('receipt',result);self.assertIn('receipt_token',result)
        self.assertEqual(self.f.state()['active_batch']['new_transactions_reserved'],0)
    def test_fixture_grant_is_operation_exact_and_cannot_dispatch(self):
        before=(self.f.root/'state/backup_state.json').read_bytes()
        run=subprocess.run
        def with_schema_env(argv,**kwargs):
            env=dict(kwargs.get('env',{}));env['PYTHONPATH']=os.pathsep.join([str(ROOT/'src'),*SCHEMA_PATHS])
            kwargs['env']=env;return run(argv,**kwargs)
        with patch('subprocess.run',side_effect=with_schema_env):
            p,_=self.f.cli('begin',dict(mode='backup_batch',limit=1),grant_operations=['admit'])
            p2,_=self.f.cli('dispatch',grant_operations=['dispatch'])
        self.assertEqual(p.returncode,4);self.assertIn(b'GRANT_SCOPE',p.stderr)
        self.assertEqual(p2.returncode,4);self.assertIn(b'FIXTURE_LIVE_OPERATION_REFUSED',p2.stderr)
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_missing_lock_refuses_before_creation(self):
        expected=self.f.receipt();raw=(self.f.root/'state/backup_state.json').read_bytes()
        (self.f.root/'state/.line-backup-state.lock').unlink()
        with self.assertRaises(AcceptanceError) as caught:self.f.svc.begin(expected,'backup_batch',1)
        self.assertEqual(caught.exception.code,'SHARED_LOCK_UNAVAILABLE')
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),raw)
        self.assertFalse((self.f.root/'state/.line-backup-state.lock').exists())
    def test_missing_state_never_initializes(self):
        (self.f.root/'state/backup_state.json').unlink()
        with self.assertRaises(AcceptanceError):Store(str(self.f.root))
        self.assertFalse((self.f.root/'state/backup_state.json').exists())
    def test_symlink_state_and_root_refused(self):
        path=self.f.root/'state/backup_state.json';path.unlink();path.symlink_to(ROOT/'state/backup_state.json')
        with self.assertRaises(AcceptanceError):Store(str(self.f.root))
    def test_foreign_owner_has_no_inter_album_window(self):
        self.f.start([identity()],1);s=self.f.state();self.assertIsNone(s['active_writer_id'])
        other=Service(str(self.f.root),'foreign',self.f.artifacts)
        before=(self.f.root/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'BATCH_BUSY'):other.begin(self.f.receipt(),'backup_batch',1)
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_config_drift_blocks_even_fresh_receipt(self):
        self.f.start([identity()],1);self.f.cfg['max_albums_per_run']=3;self.f.save(self.f.state())
        with self.assertRaisesRegex(AcceptanceError,'BATCH_AUTHORITY_DRIFT'):self.f.receipt()
    def test_source_drift_blocks(self):
        self.f.start([identity()],1)
        p=self.f.root/'src/line_backup_batch/service.py';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaisesRegex(AcceptanceError,'BATCH_AUTHORITY_DRIFT'):self.f.receipt()
    def test_stale_revision_hash_and_inode_refused(self):
        expected=self.f.receipt();path=self.f.root/'state/backup_state.json';raw=path.read_bytes()
        temp=path.with_suffix('.other');temp.write_bytes(raw);os.replace(temp,path)
        with self.assertRaisesRegex(AcceptanceError,'STALE_CAS'):self.f.svc.begin(expected,'backup_batch',1)
        self.assertEqual(path.read_bytes(),raw)
    def test_old_operator_idle_v3_refuses_before_lock_or_destination(self):
        old_path=ROOT/'harness-development/rev28-download182/TASK-20261009-download182/operator.py'
        if not old_path.exists():self.skipTest('frozen old operator source is not present in the isolated fixture worktree')
        original=old_path.read_bytes();spec=importlib.util.spec_from_file_location('frozen_old_operator',old_path)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        old.TASK=TASK  # Only external fixture destination authority is rebased.
        op=old.Operator(self.f.root,self.f.receipt()['config_sha256'],run_id='fresh-id',owner_id='fresh-owner',fp=identity(65),test_mode=True)
        expected=self.f.receipt();(self.f.root/'state/.line-backup-state.lock').unlink()
        before=(self.f.root/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'V3 history is read-only'):op.commit('acquire',expected)
        self.assertFalse((self.f.root/'state/.line-backup-state.lock').exists())
        self.assertEqual(list((self.f.root/'backups').iterdir()),[])
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
        self.assertEqual(old_path.read_bytes(),original)
    def test_production_api_without_grant_refuses(self):
        store=Store(str(self.f.root));store.fixture=False;before=(self.f.root/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'LIVE_AUTHORITY_REQUIRED'):
            store._update(store.snapshot()['receipt'],lambda cfg,s:None,operation='begin')
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_generic_mutation_has_no_production_authorization_fallback(self):
        store=Store(str(self.f.root))
        before=(self.f.root/'state/backup_state.json').read_bytes()
        self.assertFalse(hasattr(store,'update'))
        with self.assertRaises(AcceptanceError) as caught:
            store._update(store.snapshot()['receipt'],lambda cfg,s:None,operation='mutate')
        self.assertEqual(caught.exception.code,'OPERATION_REQUIRED')
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_operation_label_cannot_mutate_an_unrelated_state_section(self):
        expected=self.f.receipt();before=(self.f.root/'state/backup_state.json').read_bytes()
        def wrong_transition(cfg,state):
            state['verified_albums'].append({'fabricated':True})
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.store._update(expected,wrong_transition,operation='begin')
        self.assertEqual(caught.exception.code,'TRANSITION_SCOPE')
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_fixture_service_intent_is_not_live_dispatch_capability(self):
        target=identity();self.f.start([target],1);self.f.prepare(target)
        committed=self.f.intent(target)
        self.assertTrue(committed['new_intent'])
        self.assertFalse(committed['result']['dispatch_authorized'])
        self.assertTrue(committed['result']['fixture'])
    def test_persisted_intents_bound_two_separate_lifecycles(self):
        grant=dict(owner='execution',album_quota=2,lifecycle_album_limit=1,
            save_all_dispatch_limit=2,chooser_confirmation_limit=2)
        state=dict(active_batch=dict(owner_execution_id='execution',authorized_new_download_limit=1),
            runs=[dict(batch_id=f'b{i}',intent={'action_id':f'a{i}'}) for i in range(2)])
        with self.assertRaisesRegex(AcceptanceError,'GRANT_ALBUM_QUOTA'):
            enforce_grant_quota(grant,'begin',state)
        state['runs'].pop()
        self.assertEqual(enforce_grant_quota(grant,'begin',state),1)
        state['runs'].append(dict(batch_id='b1',intent={'action_id':'a1'}))
        self.assertEqual(enforce_grant_quota(grant,'intent',state),2)
        state['runs'].append(dict(batch_id='b2',intent={'action_id':'a2'}))
        with self.assertRaisesRegex(AcceptanceError,'GRANT_DISPATCH_QUOTA'):
            enforce_grant_quota(grant,'intent',state)
    def test_legacy_canonical_replacement_refused(self):
        path=self.f.root/'state/backup_state.json';before=path.read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'Canonical state requires'):
            atomic_write_json(path,{'schema_version':3})
        self.assertEqual(path.read_bytes(),before)

class ProjectRuntimeBindingTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def root_boundary(self):
        from types import SimpleNamespace
        return patch.object(batch_cli,'Path',side_effect=lambda _:
            SimpleNamespace(resolve=lambda:SimpleNamespace(parents=[None,None,Path(self.f.root)])))
    def project_service(self):
        grant,grant_ref,_=project_authority_fixture(self.f)
        store=Store(str(self.f.root),grant_ref['path']);store.fixture=False
        service=Service(str(self.f.root),self.f.owner,grant['artifact_dir'],grant_ref['path']);service.store=store
        return grant,store,service,grant_ref['path']
    def test_authorize_and_store_update_rehash_project_callback_closure(self):
        grant,grant_ref,runtime_ref=project_authority_fixture(self.f)
        grant_path=grant_ref['path']
        with self.root_boundary():
            authorized=batch_cli.authorize(str(self.f.root),grant_path,False,'begin')
        self.assertEqual(authorized['runtime_binding'],runtime_ref)
        store=Store(str(self.f.root),grant_path);store.fixture=False
        svc=Service(str(self.f.root),self.f.owner,self.f.artifacts);svc.store=store
        with self.root_boundary():
            store.initialize_project_ledger(batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize'),
                {'confirm_initialization':True})
            result=svc.begin(store.snapshot()['receipt'],'backup_batch',1)
        self.assertEqual(result['result']['status'],'BATCH_OWNED')
        callback_ref=json.loads((self.f.root/runtime_ref['path']).read_bytes())['callback_sources'][0]
        callback=self.f.root/callback_ref['path'];original=callback.read_bytes()
        callback.write_bytes(original+b'\nchanged callback source')
        with self.root_boundary(),self.assertRaises(AcceptanceError) as caught:
            store._update(store.snapshot()['receipt'],lambda cfg,state:None,operation='begin')
        self.assertEqual(caught.exception.code,'PROJECT_CALLBACK_SOURCE_DRIFT')
    def test_runtime_binding_refuses_missing_callback_source_refs(self):
        grant,_,runtime_ref=project_authority_fixture(self.f)
        runtime_path=self.f.root/runtime_ref['path'];manifest=json.loads(runtime_path.read_bytes())
        manifest['callback_sources']=[];raw=json_bytes(manifest);runtime_path.write_bytes(raw)
        grant['runtime_binding']=dict(path=runtime_ref['path'],bytes=len(raw),sha256=sha(raw))
        from line_backup_acceptance.project_binding import ProjectReader
        reader=ProjectReader(str(self.f.root))
        try:
            with self.assertRaises(AcceptanceError) as caught:
                batch_cli.validate_project_runtime_binding(reader,grant)
            self.assertEqual(caught.exception.code,'PROJECT_CALLBACK_SOURCE_BINDING_REQUIRED')
        finally:reader.close()
    def test_service_accepts_adapter_equivalent_project_calibration_claim(self):
        grant,store,service,grant_path=self.project_service();target=identity()
        with self.root_boundary():
            authorized=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize')
            store.initialize_project_ledger(authorized,{'confirm_initialization':True})
            begun=service.begin(store.snapshot()['receipt'],'backup_batch',1)
            albums=self.f.observation([target])
            admitted=service.admit_bounded(begun['receipt'],albums,target,self.f.session)
            prepared=service.prepare(admitted['receipt'],albums)
            run_id=prepared['result']['run_id']
            project_grant=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_reserve')
            card=store.reserve_gui(project_grant,dict(kind='album_open',count=1,run_id=run_id,owner=self.f.owner,slots=['A.CARD']))
            store.consume_gui(project_grant,dict(reservation_id=card['reservation']['id'],outcome='RETURNED'))
            calibration_reservation=store.reserve_gui(project_grant,dict(kind='menu_calibration',count=2,run_id=run_id,
                owner=self.f.owner,slots=['A.CAL_OPEN','A.CAL_DISMISS']))
            store.consume_gui(project_grant,dict(reservation_id=calibration_reservation['reservation']['id'],outcome='RETURNED'))
            detail=self.f.observation([target],'ALBUM_DETAIL')
            closure=self.f.observation([target],'ALBUM_DETAIL')
            cal=dict(observed_at='2026-10-14T00:00:00+00:00',screenshot_width=128,screenshot_height=128,
                ellipsis=[115,15],dot_spacing=5,save_all_point=[100,50],confidence='HIGH',evidence='')
            applicability=service.publish('adapter-applicability.json',dict(kind='LINE_MENU_APPLICABILITY',
                provider='SCREEN_CAPTURE_KIT',line_version='LINE 9',language='en',window_class='LINE_MAIN',
                layout_key=detail['layout_key'],dimensions=[128,128],native_scale=2,menu_order=['Save All']))
            closure_ref=service.publish('adapter-closure.json',dict(kind='LINE_MENU_CLOSURE',frame_id=closure['frame_id'],
                menu_closed=True,no_activation=True,detail_fingerprint=target))
            support=detail['mapping']['sck_support'];cal['evidence']=support['sha256']
            support_data=json.loads((self.f.root/support['path']).read_bytes())
            now=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
            claim=dict(version=2,kind='menu-calibration-no-io-pair',run_id=run_id,session_id=self.f.session,
                detail=detail,menu_frame=detail,trigger=dict(frameId=detail['frame_id'],point=cal['ellipsis'],
                    role='button',dot_spacing=cal['dot_spacing']),label='Save All',support=support,
                guard=dict(verdict='PASS',provider='SCREEN_CAPTURE_KIT',pairFrameId=detail['frame_id'],
                    popupFrameId=support_data['sck_frame']['sha256'],supportSha256=support['sha256'],
                    actionPoint=cal['save_all_point']),calibration=cal,
                closure_reference=closure_ref,applicability_reference=applicability,
                reservation_id=calibration_reservation['reservation']['id'],
                reservation_ids=[calibration_reservation['reservation']['id']],reservation_state='CONSUMED',
                opened_at=detail['captured_at'],closed_at=now)
            claim_ref=service.publish('adapter-calibration2.json',claim)
            menu=dict(label='Save All',frame_id=detail['frame_id'],layout_key=detail['layout_key'],evidence=claim_ref,
                safe_bounds=[90,40,20,20],ellipsis_bounds=[112,12,6,6],
                closure_trace=['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH'],
                closure_reference=closure_ref,applicability_reference=applicability)
            claim['trigger']['bounds_px']=menu['ellipsis_bounds']
            claim_path=self.f.root/claim_ref['path'];claim_raw=json_bytes(claim);claim_path.write_bytes(claim_raw)
            claim_ref=dict(path=claim_ref['path'],bytes=len(claim_raw),sha256=sha(claim_raw));menu['evidence']=claim_ref
            claim_path=self.f.root/claim_ref['path'];good_raw=claim_path.read_bytes()
            bad_claim=dict(claim);bad_claim['detail']={**detail,'viewport_bounds':[0,0,128,128]}
            bad_raw=json_bytes(bad_claim);claim_path.write_bytes(bad_raw)
            bad_menu=dict(menu,evidence=dict(path=claim_ref['path'],bytes=len(bad_raw),sha256=sha(bad_raw)))
            with self.assertRaises(AcceptanceError) as caught:
                service.calibrate(prepared['receipt'],detail,cal,bad_menu,closure)
            self.assertEqual(caught.exception.code,'PROJECT_CALIBRATION_BINDING')
            claim_path.write_bytes(good_raw)
            result=service.calibrate(prepared['receipt'],detail,cal,menu,closure)
        self.assertEqual(result['result']['status'],'CALIBRATED')
        with self.root_boundary():
            committed=service.intent(result['receipt'],detail)
            action=committed['result'];project_grant=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_reserve')
            dispatch_res=store.reserve_gui(project_grant,dict(kind='dispatch_inputs',count=2,run_id=action['run_id'],
                owner=self.f.owner,slots=['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']))['reservation']
            store.consume_gui(project_grant,dict(reservation_id=dispatch_res['id'],outcome='RETURNED'))
            chooser_res=store.reserve_gui(project_grant,dict(kind='chooser_inputs',count=4,run_id=action['run_id'],
                owner=self.f.owner,slots=['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM']))['reservation']
            store.consume_gui(project_grant,dict(reservation_id=chooser_res['id'],outcome='UNKNOWN'))
            at='2026-10-14T00:00:00+00:00'
            receipt_data={key:None for key in DISPATCH_RECEIPT_V3_KEYS}
            receipt_data.update(version='cua-dispatch-receipt-3',run_id=action['run_id'],action_id=action['action_id'],
                execution_id=self.f.owner,session_id=self.f.session,pair_frame_id=detail['frame_id'],cease_input=True,
                save_all_click_count=1,dispatch_policy='LOGICAL_AT_MOST_ONCE_DURABLE_PRE_INPUT_RESERVATION_NO_REPLAY',
                calibration_reference=claim_ref,calibration_closure_reference=closure_ref,
                applicability_reference=applicability,reservations=[
                    dict(kind='dispatch_inputs',count=2,state='CONSUMED',reservation_id=dispatch_res['id']),
                    dict(kind='chooser_inputs',count=4,state='CONSUMED',reservation_id=chooser_res['id'])],
                events=[dict(event=name,at=at) for name in DISPATCH_EVENT_ORDER_V3])
            schema_bad=copy.deepcopy(receipt_data);schema_bad['support']=dict(path='synthetic',bytes=1,sha256='0'*64)
            schema_ref=service.publish('receipt3-forbidden-sck-field.json',schema_bad)
            with self.assertRaises(AcceptanceError) as caught:
                service.dispatch(committed['receipt'],{}, {},False,receipt=schema_ref)
            self.assertEqual(caught.exception.code,'INVALID_DISPATCH_RECEIPT')
            bad_events=copy.deepcopy(receipt_data['events']);bad_events.insert(2,dict(event='SCK_MENU_GUARD_PASS',at=at))
            receipt_data['events']=bad_events
            receipt_ref=service.publish('receipt3-unexpected-sck.json',receipt_data)
            with self.assertRaises(AcceptanceError) as caught:
                service.dispatch(committed['receipt'],{}, {},False,receipt=receipt_ref)
            self.assertEqual(caught.exception.code,'RECEIPT_EVENT_ORDER')
            receipt_data['events']=[dict(event=name,at='2099-10-14T00:00:00+00:00') for name in DISPATCH_EVENT_ORDER_V3]
            receipt_ref=service.publish('receipt3-future-event.json',receipt_data)
            with self.assertRaises(AcceptanceError) as caught:
                service.dispatch(committed['receipt'],{}, {},False,receipt=receipt_ref)
            self.assertEqual(caught.exception.code,'RECEIPT_EVENT_TIME_ORDER')
            receipt_data['events']=[dict(event=name,at=at) for name in DISPATCH_EVENT_ORDER_V3]
            receipt_ref=service.publish('receipt3-unknown-reservation.json',receipt_data)
            with self.assertRaises(AcceptanceError) as caught:
                service.dispatch(committed['receipt'],{}, {},False,receipt=receipt_ref)
            self.assertEqual(caught.exception.code,'RECEIPT3_RESERVATION_OUTCOME')
            with self.assertRaises(AcceptanceError) as caught:
                store.reserve_gui(project_grant,dict(kind='scroll',count=1,owner=self.f.owner,slots=['SCROLL_1']))
            self.assertEqual(caught.exception.code,'PROJECT_WORKFLOW_HALTED')
        run=next(run for run in self.f.state()['runs'] if run['run_id']==action['run_id'])
        self.assertIsNone(run['dispatch_evidence'])

class GuiLedgerTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def gui_grant(self,cap):
        grant=self.f.grant([]);grant['gui_ledger']=self.f.artifacts+'/gui-ledger.json'
        grant['reversible_gui_invocation_limit']=cap;return grant
    def reserve(self,grant,**overrides):
        data=dict(kind='dispatch_inputs',count=1,run_id='RUN-gui',owner=self.f.owner);data.update(overrides)
        return self.f.svc.store.reserve_gui(grant,data)
    def ledger(self):return json.loads((self.f.root/'harness-development/evidence/gui-ledger.json').read_bytes())
    def test_reserve_consume_and_fact(self):
        grant=self.gui_grant(5);out=self.reserve(grant,count=2)
        self.assertEqual((out['used'],out['cap']),(2,5))
        reservation=out['reservation']
        consumed=self.f.svc.store.consume_gui(grant,dict(reservation_id=reservation['id'],outcome='RETURNED'))
        self.assertEqual(consumed['reservation'],dict(id=reservation['id'],kind='dispatch_inputs',count=2,state='CONSUMED'))
        fact=self.f.svc.store.gui_reservation_fact('harness-development/evidence/gui-ledger.json',reservation['id'])
        self.assertEqual(fact,dict(kind='dispatch_inputs',count=2,owner=self.f.owner,run_id='RUN-gui',state='CONSUMED',slots=None))
        ledger=self.ledger()
        self.assertEqual(ledger['version'],'line-backup-gui-ledger-1');self.assertEqual(ledger['task_id'],'TASK-20261010-line-v3-live-e2e')
        self.assertEqual((ledger['cap'],len(ledger['entries'])),(5,1))
        self.assertEqual(ledger['entries'][0]['outcome'],json.dumps('RETURNED'))
    def test_exhaustion_counts_reserved_and_consumed_and_never_refunds(self):
        grant=self.gui_grant(3);first=self.reserve(grant,count=2)
        with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,count=2)
        self.assertEqual(caught.exception.code,'GUI_LEDGER_EXHAUSTED')
        self.f.svc.store.consume_gui(grant,dict(reservation_id=first['reservation']['id']))
        with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,count=2)
        self.assertEqual(caught.exception.code,'GUI_LEDGER_EXHAUSTED')
        self.assertEqual(sum(entry['count'] for entry in self.ledger()['entries']),2)
    def test_consume_unknown_double_and_missing_refused(self):
        grant=self.gui_grant(3)
        with self.assertRaises(AcceptanceError) as caught:self.f.svc.store.consume_gui(grant,dict(reservation_id='nope'))
        self.assertEqual(caught.exception.code,'GUI_LEDGER_UNKNOWN_RESERVATION')
        out=self.reserve(grant,count=1)
        self.f.svc.store.consume_gui(grant,dict(reservation_id=out['reservation']['id']))
        with self.assertRaises(AcceptanceError) as caught:self.f.svc.store.consume_gui(grant,dict(reservation_id=out['reservation']['id']))
        self.assertEqual(caught.exception.code,'GUI_LEDGER_STATE')
        with self.assertRaises(AcceptanceError) as caught:self.f.svc.store.consume_gui(grant,{})
        self.assertEqual(caught.exception.code,'GUI_LEDGER_RESERVATION')
        with self.assertRaises(AcceptanceError) as caught:self.f.svc.store.gui_reservation_fact('harness-development/evidence/gui-ledger.json','nope')
        self.assertEqual(caught.exception.code,'GUI_LEDGER_STATE')
    def test_second_grant_with_same_task_and_cap_shares_the_ledger(self):
        grant=self.gui_grant(4);self.reserve(grant,count=3)
        second=copy.deepcopy(grant)
        out=self.reserve(second,count=1)
        self.assertEqual(out['used'],4)
        with self.assertRaises(AcceptanceError) as caught:self.reserve(second,count=1)
        self.assertEqual(caught.exception.code,'GUI_LEDGER_EXHAUSTED')
    def test_task_or_cap_change_is_ledger_drift(self):
        grant=self.gui_grant(4);self.reserve(grant,count=1)
        for name,mutate in (('cap',lambda g:g.__setitem__('reversible_gui_invocation_limit',5)),
            ('task',lambda g:g.__setitem__('task_id','TASK-other'))):
            with self.subTest(name=name):
                changed=copy.deepcopy(grant);mutate(changed)
                with self.assertRaises(AcceptanceError) as caught:self.reserve(changed,count=1)
                self.assertEqual(caught.exception.code,'GUI_LEDGER_DRIFT')
    def test_scope_kind_count_owner_and_run_validation(self):
        grant=self.gui_grant(4)
        scoped=copy.deepcopy(grant);scoped['gui_ledger']='harness-development/evidence/other.json'
        with self.assertRaises(AcceptanceError) as caught:self.reserve(scoped)
        self.assertEqual(caught.exception.code,'GUI_LEDGER_SCOPE')
        with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,kind='bogus')
        self.assertEqual(caught.exception.code,'GUI_LEDGER_KIND')
        for bad in (0,True,'2'):
            with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,count=bad)
            self.assertEqual(caught.exception.code,'GUI_LEDGER_COUNT')
        with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,owner='someone-else')
        self.assertEqual(caught.exception.code,'GUI_LEDGER_OWNER')
        with self.assertRaises(AcceptanceError) as caught:self.reserve(grant,run_id=5)
        self.assertEqual(caught.exception.code,'GUI_LEDGER_RUN')
        self.assertFalse((self.f.root/'harness-development/evidence/gui-ledger.json').exists())

class ProjectGuiLedgerTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture();self.store=self.f.svc.store
        self.grant=dict(grant_version='line-two-album-project-grant-1',task_id='PILOT-test',owner=self.f.owner,
            gui_ledger='harness-development/evidence/gui-ledger.json',reversible_gui_invocation_limit=23)
        self.auth_patch=patch.object(self.store,'_authorize_project_mutation',return_value=None);self.auth_patch.start()
        self.store.initialize_project_ledger(self.grant,{'confirm_initialization':True})
    def tearDown(self):self.auth_patch.stop();self.f.close()
    def reserve(self,kind,count,run,slots):
        return self.store.reserve_gui(self.grant,dict(kind=kind,count=count,run_id=run,owner=self.f.owner,slots=slots))
    def test_reserved_slot_burns_across_restart_and_unknown_never_replays(self):
        first=self.reserve('album_open',1,'RUN-A',['A.CARD'])['reservation']
        self.store.consume_gui(self.grant,dict(reservation_id=first['id'],outcome='RETURNED'))
        second=Store(str(self.f.root));second._authorize_project_mutation=lambda *args:None
        cal=second.reserve_gui(self.grant,dict(kind='menu_calibration',count=2,run_id='RUN-A',owner=self.f.owner,
            slots=['A.CAL_OPEN','A.CAL_DISMISS']))['reservation']
        ledger=json.loads((self.f.root/'harness-development/evidence/gui-ledger.json').read_bytes())
        self.assertEqual([slot for item in ledger['entries'] for slot in item['slots']],['A.CARD','A.CAL_OPEN','A.CAL_DISMISS'])
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_UNKNOWN_RESERVATION'):
            self.store.reserve_gui(self.grant,dict(kind='dispatch_inputs',count=2,run_id='RUN-A',owner=self.f.owner,
                slots=['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']))
        self.assertEqual(len(ledger['entries']),2)
    def test_initialization_tombstone_prevents_reinitialize_and_missing_ledger_stops(self):
        ledger_path=self.f.root/'harness-development/evidence/gui-ledger.json'
        ledger_path.unlink()
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_LEDGER_MISSING'):
            self.store.reserve_gui(self.grant,dict(kind='album_open',count=1,run_id='RUN-A',owner=self.f.owner,slots=['A.CARD']))
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_LEDGER_ALREADY_INITIALIZED'):
            self.store.initialize_project_ledger(self.grant,{'confirm_initialization':True})
    def test_incomplete_reserved_bundle_is_rejected_after_restart(self):
        raw=self.f.root/'harness-development/evidence/gui-ledger.json'
        card=self.reserve('album_open',1,'RUN-A',['A.CARD'])['reservation']
        self.store.consume_gui(self.grant,dict(reservation_id=card['id'],outcome='RETURNED'))
        self.reserve('menu_calibration',2,'RUN-A',['A.CAL_OPEN','A.CAL_DISMISS'])
        ledger=json.loads(raw.read_bytes());entry=ledger['entries'][1];entry['slots']=['A.CAL_OPEN'];entry['count']=1
        raw.write_bytes(json_bytes(ledger))
        fresh=Store(str(self.f.root));fresh._authorize_project_mutation=lambda *args:None
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_LEDGER_BUNDLE'):
            fresh.reserve_gui(self.grant,dict(kind='album_open',count=1,run_id='RUN-A',owner=self.f.owner,slots=['A.CARD']))
    def test_all_23_fixed_slots_remain_burned_across_fixture_phase_restarts(self):
        def fresh_store():
            store=Store(str(self.f.root));store._authorize_project_mutation=lambda *args:None
            return store
        def reserve(store,kind,slots,run):
            item=store.reserve_gui(self.grant,dict(kind=kind,count=len(slots),run_id=run,
                owner=self.f.owner,slots=slots))['reservation']
            store.consume_gui(self.grant,dict(reservation_id=item['id'],outcome='RETURNED'))
        a=fresh_store()
        for n in (1,2,3):reserve(a,'scroll',[f'SCROLL_{n}'],None)
        reserve(a,'album_open',['A.CARD'],'RUN-A')
        reserve(a,'menu_calibration',['A.CAL_OPEN','A.CAL_DISMISS'],'RUN-A')
        reserve(a,'dispatch_inputs',['A.ATOMIC_ELLIPSIS','A.SAVE_ALL'],'RUN-A')
        reserve(a,'chooser_inputs',['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM'],'RUN-A')
        ledger_path=self.f.root/'harness-development/evidence/gui-ledger.json'
        ledger=json.loads(ledger_path.read_bytes())
        # Controlled fixture phase transition: this test isolates fixed-slot conservation;
        # real A verification and C1 proof are exercised by the service/coordinator paths.
        ledger.update(workflow_phase='C1',lifecycle_count=1,c1_verified=False,
            lifecycle_batch_ids=['BATCH-A'],last_batch_id='BATCH-A')
        ledger_path.write_bytes(json_bytes(ledger))
        c1=fresh_store()
        reserve(c1,'return_navigation',['RETURN_A_TO_LIST'],None)
        reserve(c1,'scroll',['SCROLL_4'],None)
        ledger=json.loads(ledger_path.read_bytes());ledger.update(workflow_phase='B',c1_verified=True,lifecycle_count=2,
            lifecycle_batch_ids=['BATCH-A','BATCH-B'],last_batch_id='BATCH-B')
        ledger_path.write_bytes(json_bytes(ledger))
        b=fresh_store()
        reserve(b,'album_open',['B.CARD'],'RUN-B')
        reserve(b,'menu_calibration',['B.CAL_OPEN','B.CAL_DISMISS'],'RUN-B')
        reserve(b,'dispatch_inputs',['B.ATOMIC_ELLIPSIS','B.SAVE_ALL'],'RUN-B')
        reserve(b,'chooser_inputs',['B.GO_TO_FOLDER','B.SET_PATH','B.PATH_RETURN','B.CHOOSER_CONFIRM'],'RUN-B')
        fresh=fresh_store();ledger=json.loads(ledger_path.read_bytes())
        slots=[slot for entry in ledger['entries'] for slot in entry['slots']]
        self.assertEqual(len(slots),23);self.assertEqual(len(set(slots)),23)
        self.assertEqual(ledger['task_id'],self.grant['task_id'])
        self.assertEqual(ledger['lifecycle_count'],2)
        self.assertEqual([entry['run_id'] for entry in ledger['entries'] if entry['slots'][0].startswith('B.')],
            ['RUN-B']*4)
        with self.assertRaisesRegex(AcceptanceError,'GUI_LEDGER_EXHAUSTED'):
            fresh.reserve_gui(self.grant,dict(kind='album_open',count=1,run_id='RUN-A',owner=self.f.owner,
                slots=['A.CARD']))
        changed=dict(self.grant,task_id='PILOT-replacement')
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_LEDGER_INITIALIZATION_INVALID'):
            fresh.reserve_gui(changed,dict(kind='album_open',count=1,run_id='RUN-A',owner=self.f.owner,
                slots=['A.CARD']))

class LiveRootAuthorityTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def live_service(self):
        return Service(str(self.f.root),'live-guard-owner',self.f.artifacts,None)
    def state_bytes(self):return (self.f.root/'state/backup_state.json').read_bytes()
    def test_live_dispatch_without_retained_receipt_refuses(self):
        before=self.state_bytes();svc=self.live_service();target=identity();self.f.start([target],1);self.f.prepare(target);self.f.intent(target)
        svc=self.f.svc;svc.store.fixture=False;before_attempt=self.state_bytes()
        with self.assertRaises(AcceptanceError) as caught:
            svc.dispatch(svc.store.snapshot()['receipt'],{}, {}, True)
        self.assertEqual(caught.exception.code,'RETAINED_RECEIPT_REQUIRED')
        self.assertEqual(self.state_bytes(),before_attempt)
    def test_live_finalize_with_fixture_options_or_fault_refused(self):
        before=self.state_bytes();svc=self.f.svc;svc.store.fixture=False;receipt=svc.store.snapshot()['receipt']
        with self.assertRaises(AcceptanceError) as caught:
            svc.finalize(receipt,'/usr/bin/false','0'*64,fault='DRIFT_AFTER_COMMIT')
        self.assertEqual(caught.exception.code,'INVALID_FINALIZE_FAULT')
        self.assertEqual(self.state_bytes(),before)
