import copy
from contextlib import nullcontext
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
import jsonschema,referencing,attrs,rpds
from unittest.mock import patch
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,Provider,ROOT,TASK,identity,sha,json_bytes,token,png
from line_backup_batch.store import Store,enforce_grant_quota
from line_backup_batch.service import Service,DISPATCH_RECEIPT_V3_KEYS,DISPATCH_EVENT_ORDER_V3
from line_backup_batch.coordinator import Coordinator
import line_backup_batch.cli as batch_cli
from line_backup_acceptance.common import AcceptanceError,atomic_write_json
from line_backup_acceptance.project_binding import ProjectReader

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

def project_native_shaped_observation(f,identities,surface='ALBUMS',top=False,bottom=False,focus='NONE',extra_elements=(),
    focused_index=None,window_identifier='LINE-window',window_label='LINE'):
    """Synthetic retained native-shaped records for copied production validators; never LINE evidence."""
    record=f.observation(identities,surface,top,bottom);record['editable_focus']=focus
    structure=[dict(role='window',surface=surface,layout='fixture-native-shaped')]
    structure_sha=sha(json_bytes(structure))
    layout=dict(line_version='fixture LINE build',language='en',window_class='LINE_MAIN',frame_width_px=128,
        frame_height_px=128,native_scale=1,structure_sha256=structure_sha)
    record['layout_key']=sha(json_bytes(layout));record['mapping']['layout_key']=record['layout_key']
    frame_raw=(f.root/record['frame']['path']).read_bytes()
    side_ref=record['mapping']['sck_support'];side=json.loads((f.root/side_ref['path']).read_bytes())
    side.update(provider='SCREEN_CAPTURE_KIT',fixture=False,layout_key=record['layout_key'])
    side['interactive_intersection_px']=[0,0,128,128]
    ocr=json.loads((f.root/side['ocr']['path']).read_bytes())
    card_witnesses=[];elements=[]
    for index,card in enumerate(record['cards']):
        x,y,w,h=card['card_bounds'];title_box=[card['metadata_bounds'][0]+2,card['metadata_bounds'][1]+1,30,4]
        count_box=[card['metadata_bounds'][0]+34,card['metadata_bounds'][1]+1,12,4]
        title_text=card['title'];count_text=str(card['fingerprint']['expected_images'])
        for items in (ocr['cua'],ocr['sck']):
            items.extend([dict(text=title_text,confidence=0.99,candidate_count=1,bounds=title_box),
                dict(text=count_text,confidence=0.99,candidate_count=1,bounds=count_box)])
        card_index=10+index*2;image_index=card_index+1;thumbnail=[x+2,y+2,8,8]
        elements.extend([dict(index=card_index,role='row',subrole='AXRow',identifier=f'album-{index}',label=title_text,
            value=None,bounds_px=card['card_bounds'],parent_index=0,enabled=True),
            dict(index=image_index,role='image',subrole='AXImage',identifier=f'thumbnail-{index}',label='',value=None,
                bounds_px=thumbnail,parent_index=card_index,enabled=True)])
        card_witnesses.append(dict(fingerprint=card['fingerprint'],title=title_text,card_bounds=card['card_bounds'],
            metadata_bounds=card['metadata_bounds'],safe_metadata_bounds=card['safe_metadata_bounds'],
            neighbor_bounds=card['neighbor_bounds'],thumbnail_bounds=thumbnail,
            title_ocr=dict(text=title_text,bounds=title_box),count_ocr=dict(text=count_text,bounds=count_box),
            card_ax_index=card_index,thumbnail_ax_index=image_index))
    elements.extend(extra_elements)
    if surface=='ALBUMS':
        scroll_value=0.5
        elements.append(dict(index=90,role='scroll bar',subrole='AXScrollBar',identifier='albums-scroll',label='',
            value=scroll_value,bounds_px=[120,0,8,128],parent_index=0,enabled=True))
        boundary_proof=dict(version=1,frame_id=record['frame_id'],session_id=record['session_id'],source='AX_SCROLLBAR',
            indicator_index=90,minimum=0.0,maximum=1.0,value=scroll_value)
    else:
        boundary_proof=dict(version=1,frame_id=record['frame_id'],session_id=record['session_id'],source='NOT_APPLICABLE')
    boundary_ref=f.ref('native-shaped-boundary-'+uuid.uuid4().hex+'.json',json_bytes(boundary_proof))
    record['boundary']['evidence']=boundary_ref
    ax=dict(version=1,frame_id=record['frame_id'],session_id=f.session,pid=record['pid'],window_id=record['window_id'],
        surface=surface,focused_index=focused_index,elements=[dict(index=0,role='window',subrole='AXWindow',
            identifier=window_identifier,label=window_label,value=None,bounds_px=[0,0,128,128],parent_index=None,enabled=True),*elements])
    ax_ref=f.ref('native-shaped-ax-'+uuid.uuid4().hex+'.json',json_bytes(ax))
    focus_value=(dict(version=1,frame_id=record['frame_id'],session_id=f.session,kind='NONE',focused_index=focused_index)
        if focus=='NONE' else dict(version=1,frame_id=record['frame_id'],session_id=f.session,kind='HIGH_EDITABLE',
            focused_index=focused_index,element_identifier='path-text'))
    focus_ref=f.ref('native-shaped-focus-'+uuid.uuid4().hex+'.json',json_bytes(focus_value))
    classifier=dict(version=1,frame_id=record['frame_id'],session_id=f.session,ax_state_sha256=sha(json_bytes(ax)),
        screenshot_sha256=record['frame_id'],cards=card_witnesses,boundary=record['boundary'],structure_sha256=structure_sha,
        surface_structure=structure,focus_evidence=focus_ref)
    classifier_ref=f.ref('native-shaped-classifier-'+uuid.uuid4().hex+'.json',json_bytes(classifier))
    side['ocr']=f.ref('native-shaped-ocr-'+uuid.uuid4().hex+'.json',json_bytes(ocr))
    timing_start=dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
    timing_finish=(dt.datetime.fromisoformat(timing_start.replace('Z','+00:00'))+dt.timedelta(milliseconds=1)).isoformat(timespec='microseconds').replace('+00:00','Z')
    side['captured_at']=timing_start
    side_ref=f.ref('native-shaped-support-'+uuid.uuid4().hex+'.json',json_bytes(side));record['mapping']['sck_support']=side_ref
    timing=dict(requestStartedAtISO8601=timing_start,requestFinishedAtISO8601=timing_finish,
        requestStartMonotonicNanoseconds=1_000_000,requestEndMonotonicNanoseconds=2_000_000)
    record['mapping']['evidence']=None
    geometry=dict(version=1,frame_id=record['frame_id'],session_id=f.session,surface=surface,pid=record['pid'],
        window_id=record['window_id'],layout_key=record['layout_key'],captured_at=record['captured_at'],
        cua_capture_bounds_points=[0,0,128,128],surface_bounds_px=side['interactive_intersection_px'],ax_state=ax_ref,
        layout_signature=layout,structure_sha256=structure_sha)
    geometry_ref=f.ref('native-shaped-geometry-'+uuid.uuid4().hex+'.json',json_bytes(geometry))
    capture_record=dict(capturedAtISO8601=timing_start,fullDisplayCaptureTiming=timing,imageWidthPx=128,imageHeightPx=128,
        imageSHA256=side['sck_frame']['sha256'],scale=1,backingScaleFactor=1,
        fullDisplayWitness=dict(displayID=1,displayBoundsPoints=[0,0,128,128],contentRectPoints=[0,0,128,128],
            imageWidthPx=128,imageHeightPx=128,pointPixelScale=1,backingScaleFactor=1,includeMenuBar=True,sourceRectAbsent=True))
    manifest=dict(version=1,producer='rev28ctl frame-support',projectRoot=str(f.root),output=record['frame'],surface=surface,
        pairFrameId=record['frame_id'],sckFrameId=side['sck_frame']['sha256'],sessionId=f.session,pid=record['pid'],
        windowId=record['window_id'],displayId=1,layoutKey=record['layout_key'],captureKind='fullDisplayFrame',includeMenuBar=True,
        sourceRectAbsent=True,imageWidthPx=128,imageHeightPx=128,pointPixelScale=1,backingScaleFactor=1,
        contentRect=[0,0,128,128],displayBounds=[0,0,128,128],surfaceBoundsPx=side['interactive_intersection_px'],
        anchorTexts=['anchor-left','anchor-right','anchor-low'],maximumAnchorResidualPx=0,uncertaintyPx=side['uncertainty_px'],
        safeMarginPx=side['safe_margin_px'],interactiveIntersectionPx=side['interactive_intersection_px'],
        geometryEvidence=geometry_ref,sckFrame=side['sck_frame'],ocr=side['ocr'],support=side_ref,captureRecord=capture_record,
        captureTiming=timing)
    manifest_ref=f.ref('native-shaped-manifest-'+uuid.uuid4().hex+'.json',json_bytes(manifest))
    record['mapping']['evidence']=f.ref('native-shaped-grounding-'+uuid.uuid4().hex+'.json',json_bytes(dict(version=1,
        geometry=geometry_ref,manifest=manifest_ref,classifier=classifier_ref)))
    return record,ax_ref

def rebind_project_native_support(f,record):
    envelope=json.loads((f.root/record['mapping']['evidence']['path']).read_bytes())
    geometry=json.loads((f.root/envelope['geometry']['path']).read_bytes())
    manifest=json.loads((f.root/envelope['manifest']['path']).read_bytes())
    support_ref=record['mapping']['sck_support'];support=json.loads((f.root/support_ref['path']).read_bytes())
    geometry['surface_bounds_px']=support['interactive_intersection_px']
    geometry_ref=f.ref('native-shaped-geometry-rebound-'+uuid.uuid4().hex+'.json',json_bytes(geometry))
    manifest['geometryEvidence']=geometry_ref;manifest['support']=support_ref;manifest['ocr']=support['ocr']
    manifest['surfaceBoundsPx']=support['interactive_intersection_px']
    manifest_ref=f.ref('native-shaped-manifest-rebound-'+uuid.uuid4().hex+'.json',json_bytes(manifest))
    envelope['geometry']=geometry_ref;envelope['manifest']=manifest_ref
    record['mapping']['evidence']=f.ref('native-shaped-grounding-rebound-'+uuid.uuid4().hex+'.json',json_bytes(envelope))

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
        return patch.object(batch_cli,'__file__',str(self.f.root/'src/line_backup_batch/cli.py'))
    def run_project_cli(self,operation,grant_path,expected,data,expected_code=None):
        payload=self.f.ref('cli-input-'+operation+'-'+uuid.uuid4().hex+'.json',json_bytes(
            dict(expected_token=token(expected),data=data)))
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',LINE_BACKUP_BATCH_TASK=str(TASK),
            PYTHONPATH=os.pathsep.join([str(self.f.root/'src'),str(ROOT/'src'),*SCHEMA_PATHS]))
        argv=[sys.executable,'-B','-m','line_backup_batch',operation,'--project-root',str(self.f.root),
            '--authorization',grant_path,'--input',payload['path']]
        completed=subprocess.run(argv,capture_output=True,text=True,env=env,timeout=30)
        if expected_code is not None:
            self.assertEqual(completed.returncode,4,completed.stdout)
            error=json.loads(completed.stderr);self.assertEqual(error['code'],expected_code)
            return error,argv
        self.assertEqual(completed.returncode,0,completed.stderr)
        result=json.loads(completed.stdout)
        if 'receipt_token' in result:
            result['receipt']=json.loads(__import__('base64').b64decode(result.pop('receipt_token'),validate=True))
        return result,argv
    def bind_pinned_decoder(self,grant,grant_ref,runtime_ref):
        source=Path(self.f.binding['binary_path'])
        raw=source.read_bytes();self.assertEqual(sha(raw),self.f.binding['binary_sha256'])
        executable=self.f.root/grant['artifact_dir']/'image_decode'
        shutil.copyfile(source,executable);executable.chmod(0o700)
        decoder=dict(path=str(executable.relative_to(self.f.root)),bytes=len(raw),sha256=sha(raw))
        runtime_path=self.f.root/runtime_ref['path'];runtime=json.loads(runtime_path.read_bytes())
        runtime['runtime_files']=[dict(role=item['role'],**(decoder if item['role']=='decoder_binding' else
            {key:item[key] for key in ('path','bytes','sha256')})) for item in runtime['runtime_files']]
        runtime_raw=json_bytes(runtime);runtime_path.write_bytes(runtime_raw)
        runtime_ref=dict(path=runtime_ref['path'],bytes=len(runtime_raw),sha256=sha(runtime_raw))
        review_path=self.f.root/grant['external_review']['path'];review=json.loads(review_path.read_bytes())
        review['runtime_binding_sha256']=runtime_ref['sha256'];review_raw=json_bytes(review);review_path.write_bytes(review_raw)
        review_ref=dict(path=grant['external_review']['path'],bytes=len(review_raw),sha256=sha(review_raw))
        readiness_path=self.f.root/grant['live_readiness']['path'];readiness=json.loads(readiness_path.read_bytes())
        readiness['runtime_binding_sha256']=runtime_ref['sha256'];readiness_raw=json_bytes(readiness);readiness_path.write_bytes(readiness_raw)
        readiness_ref=dict(path=grant['live_readiness']['path'],bytes=len(readiness_raw),sha256=sha(readiness_raw))
        grant['decoder_binding']=decoder;grant['native_binary_sha256']=decoder['sha256']
        grant['runtime_binding']=runtime_ref;grant['external_review']=review_ref;grant['live_readiness']=readiness_ref
        grant_path=self.f.root/grant_ref['path'];grant_raw=json_bytes(grant);grant_path.write_bytes(grant_raw)
        grant_ref=dict(path=grant_ref['path'],bytes=len(grant_raw),sha256=sha(grant_raw))
        return grant_ref,runtime_ref,executable
    def project_service(self):
        grant,grant_ref,_=project_authority_fixture(self.f)
        store=Store(str(self.f.root),grant_ref['path']);store.fixture=False
        service=Service(str(self.f.root),self.f.owner,grant['artifact_dir'],grant_ref['path']);service.store=store
        return grant,store,service,grant_ref['path']
    def test_bounded_a_admission_uses_current_lifecycle_after_verified_history(self):
        self.f.cfg['max_albums_per_run']=1;self.f.save(self.f.state())
        historical=identity(1,7);new_target=identity(2,8)
        coordinator=Coordinator(self.f.svc,Provider(self.f,[historical]),self.f.binding['binary_path'],
            self.f.binding['binary_sha256'])
        self.assertEqual(coordinator.run(1)['status'],'ALL_COMPLETE')
        self.f.svc.release(self.f.receipt())
        grant,store,service,grant_path=self.project_service()
        with self.root_boundary():
            store.initialize_project_ledger(batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize'),
                {'confirm_initialization':True})
            begun=service.begin(store.snapshot()['receipt'],'backup_batch',1)
            record=self.f.observation([historical,new_target],top=False,bottom=False)
            with self.assertRaises(AcceptanceError) as duplicate:
                service.admit_bounded(begun['receipt'],record,historical,self.f.session)
            self.assertEqual(duplicate.exception.code,'BOUNDED_TARGET_INELIGIBLE')
            admitted=service.admit_bounded(begun['receipt'],record,new_target,self.f.session)
            manifest=json.loads((self.f.root/admitted['result']['manifest_reference']['path']).read_bytes())
            self.assertEqual(manifest['identities'],[new_target])
            self.assertEqual(manifest['coverage'],'BOUNDED_CANDIDATE_ONLY')
            self.assertFalse(manifest['complete_catalog'])
            self.assertEqual(manifest['frames'][0]['boundary'],record['boundary'])
            self.assertEqual(len(manifest['frames'][0]['cards']),2)
            self.assertFalse(manifest['frames'][0]['boundary']['top'])
            self.assertFalse(manifest['frames'][0]['boundary']['bottom'])
            state_after_admit=(self.f.root/'state/backup_state.json').read_bytes()
            with self.assertRaisesRegex(AcceptanceError,'BOUNDED_LIFECYCLE_ALREADY_ADMITTED'):
                service.admit_bounded(admitted['receipt'],record,new_target,self.f.session)
            self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),state_after_admit)
        self.assertEqual(admitted['result']['status'],'ADMITTED_BOUNDED_CANDIDATE')
        self.assertEqual(admitted['result']['coverage'],'BOUNDED_CANDIDATE_ONLY')
        state=store.snapshot()['state']
        self.assertEqual(sum(run.get('intent') is not None for run in state['runs']),1)
        self.assertIsNone(json.loads((self.f.root/'harness-development/line-two-album-pilot-20261014/private/gui-ledger.json')
            .read_bytes())['c1_reference'])

    def test_bounded_a_ledger_binding_is_rechecked_inside_state_cas(self):
        grant,store,service,grant_path=self.project_service()
        with self.root_boundary():
            store.initialize_project_ledger(batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize'),
                {'confirm_initialization':True})
            begun=service.begin(store.snapshot()['receipt'],'backup_batch',1)
            batch_id=begun['result']['batch_id'];target=identity(1,day=14)
            before=store.snapshot();publish=service.publish
            def replace_current_lifecycle(name,value):
                ref=publish(name,value)
                path=self.f.root/grant['gui_ledger'];ledger=json.loads(path.read_bytes())
                ledger['lifecycle_batch_ids'][0]='BATCH-foreign-current-lifecycle'
                ledger['last_batch_id']='BATCH-foreign-current-lifecycle'
                path.write_bytes(json_bytes(ledger))
                return ref
            with patch.object(service,'publish',side_effect=replace_current_lifecycle),self.assertRaises(AcceptanceError) as caught:
                service.admit_bounded(begun['receipt'],self.f.observation([target]),target,self.f.session)
            self.assertEqual(caught.exception.code,'BOUNDED_A_LIFECYCLE_BINDING')
        after=store.snapshot()
        self.assertEqual(after['receipt'],before['receipt'])
        self.assertEqual(after['state']['active_batch']['batch_id'],batch_id)
        self.assertIsNone(after['state']['active_batch']['manifest_reference'])

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

    def test_authenticated_inspect_reads_validated_initialized_ledger_without_writing(self):
        grant,grant_ref,_=project_authority_fixture(self.f);grant_path=grant_ref['path']
        store=Store(str(self.f.root),grant_path);store.fixture=False
        with self.root_boundary():
            current=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            absent=store.project_gui_ledger_status(current)
            self.assertEqual(absent['status'],'NOT_INITIALIZED')
            authorized=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize')
            store.initialize_project_ledger(authorized,{'confirm_initialization':True})
            before=(self.f.root/grant['gui_ledger']).read_bytes()
            current=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            status=store.project_gui_ledger_status(current)
        self.assertEqual(status['status'],'INITIALIZED')
        self.assertEqual(status['task_id'],grant['task_id']);self.assertEqual(status['owner'],grant['owner'])
        self.assertEqual(status['source_sha256'],grant['source_sha256'])
        self.assertEqual(status['workflow_phase'],'A');self.assertFalse(status['failure_latched'])
        self.assertFalse(status['scroll_1_used']);self.assertEqual(status['reserved_entry_count'],0)
        self.assertEqual((self.f.root/grant['gui_ledger']).read_bytes(),before)

        snapshot=store.snapshot()
        inspected,_=self.run_project_cli('inspect',grant_path,snapshot['receipt'],{'include_gui_ledger_status':True})
        self.assertEqual(inspected['gui_ledger_status'],status)
        public,_=self.run_project_cli('inspect',grant_path,snapshot['receipt'],{})
        self.assertNotIn('gui_ledger_status',public)

        with self.root_boundary():
            reserve_grant=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_reserve')
            first=store.reserve_gui(reserve_grant,dict(kind='scroll',count=1,run_id=None,owner=grant['owner'],
                slots=['SCROLL_1']))['reservation']
            store.consume_gui(reserve_grant,dict(reservation_id=first['id'],outcome='RETURNED'))
            current=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            consumed=store.project_gui_ledger_status(current)
            with self.assertRaises(AcceptanceError) as replay:
                store.reserve_gui(reserve_grant,dict(kind='scroll',count=1,run_id=None,owner=grant['owner'],
                    slots=['SCROLL_1']))
        self.assertTrue(consumed['scroll_1_used']);self.assertEqual(consumed['reserved_entry_count'],0)
        self.assertEqual(replay.exception.code,'PROJECT_SLOT_ALREADY_RESERVED')

    def test_authenticated_ledger_status_fails_closed_for_authority_drift_and_tombstone(self):
        grant,grant_ref,_=project_authority_fixture(self.f);grant_path=grant_ref['path']
        store=Store(str(self.f.root),grant_path);store.fixture=False
        with self.root_boundary():
            authorized=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_initialize')
            store.initialize_project_ledger(authorized,{'confirm_initialization':True})
            current=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            ledger_path=self.f.root/grant['gui_ledger']
            valid_raw=ledger_path.read_bytes();valid_ledger=json.loads(valid_raw)
            ledger_path.unlink()
            with self.assertRaises(AcceptanceError) as tombstone:
                store.project_gui_ledger_status(current)
            self.assertEqual(tombstone.exception.code,'PROJECT_LEDGER_MISSING')

            for field,value,code in (('task_id','foreign-task','PROJECT_LEDGER_DRIFT'),
                ('owner','foreign-owner','PROJECT_LEDGER_DRIFT'),
                ('initial_ledger_sha256','0'*64,'PROJECT_LEDGER_INITIALIZATION_BINDING')):
                invalid=copy.deepcopy(valid_ledger);invalid[field]=value;ledger_path.write_bytes(json_bytes(invalid))
                with self.assertRaises(AcceptanceError) as caught:store.project_gui_ledger_status(current)
                self.assertEqual(caught.exception.code,code)
            ledger_path.write_bytes(valid_raw)

            grant_file=self.f.root/grant_path;grant_raw=grant_file.read_bytes()
            decision_path=self.f.root/grant['owner_decision']['path'];decision_raw=decision_path.read_bytes()
            decision=json.loads(decision_raw);decision['live_gui_authorized']=False
            closed_raw=json_bytes(decision);decision_path.write_bytes(closed_raw)
            changed=copy.deepcopy(grant);changed['owner_decision']['bytes']=len(closed_raw)
            changed['owner_decision']['sha256']=sha(closed_raw);grant_file.write_bytes(json_bytes(changed))
            with self.assertRaises(AcceptanceError) as closed:
                batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            self.assertEqual(closed.exception.code,'PROJECT_LIVE_CONSENT_REQUIRED')
            decision['live_gui_authorized']=True;decision_path.write_bytes(json_bytes(decision))
            changed['owner_decision']['bytes']=len(json_bytes(decision))
            changed['owner_decision']['sha256']=sha(json_bytes(decision));grant_file.write_bytes(json_bytes(changed))

            readiness_path=self.f.root/grant['live_readiness']['path'];readiness_raw=readiness_path.read_bytes()
            readiness=json.loads(readiness_raw);readiness['gui_ready']=False
            not_ready_raw=json_bytes(readiness);readiness_path.write_bytes(not_ready_raw)
            changed['live_readiness']['bytes']=len(not_ready_raw);changed['live_readiness']['sha256']=sha(not_ready_raw)
            grant_file.write_bytes(json_bytes(changed))
            with self.assertRaises(AcceptanceError) as readiness_error:
                batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            self.assertEqual(readiness_error.exception.code,'PROJECT_LIVE_READINESS_REQUIRED')
            readiness_path.write_bytes(readiness_raw);grant_file.write_bytes(grant_raw)

            changed=copy.deepcopy(grant);changed['source_sha256']='0'*64
            grant_file.write_bytes(json_bytes(changed))
            with self.assertRaises(AcceptanceError) as source:
                batch_cli.authorize(str(self.f.root),grant_path,False,'gui_observe')
            self.assertEqual(source.exception.code,'PROJECT_RUNTIME_BINDING_MISMATCH')
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
    def test_project_receipt3_download_and_pinned_decode_finalize_positive(self):
        self.f.cfg['max_albums_per_run']=1;self.f.save(self.f.state())
        grant,grant_ref,runtime_ref=project_authority_fixture(self.f)
        grant_ref,runtime_ref,decoder=self.bind_pinned_decoder(grant,grant_ref,runtime_ref)
        grant_path=grant_ref['path'];store=Store(str(self.f.root),grant_path);store.fixture=False
        service=Service(str(self.f.root),self.f.owner,grant['artifact_dir'],grant_path);service.store=store
        target=identity(1,day=7);neighbor=identity(1,day=8)
        self.assertEqual((grant['lifecycle_album_limit'],self.f.cfg['max_albums_per_run']),(1,1))
        with nullcontext():
            self.run_project_cli('gui_initialize',grant_path,store.snapshot()['receipt'],{'confirm_initialization':True})
            checkpoint='PAIR-A-LIST_GROUNDING'
            self.run_project_cli('gui_observe',grant_path,store.snapshot()['receipt'],dict(kind='paired',checkpoint=checkpoint,album='A'))
            begun,_=self.run_project_cli('begin',grant_path,store.snapshot()['receipt'],{'mode':'backup_batch','limit':1})
            self.assertEqual((store.snapshot()['state']['active_batch']['authorized_new_download_limit'],
                store.snapshot()['state']['active_batch']['configured_new_download_limit']),(1,1))
            self.run_project_cli('gui_observe',grant_path,store.snapshot()['receipt'],dict(kind='paired',checkpoint=checkpoint,album='A'))
            third_observe,_=self.run_project_cli('gui_observe',grant_path,store.snapshot()['receipt'],
                dict(kind='paired',checkpoint=checkpoint,album='A'),expected_code='PROJECT_CHECKPOINT_RECAPTURE_QUOTA')
            self.assertEqual(third_observe['code'],'PROJECT_CHECKPOINT_RECAPTURE_QUOTA')
            logical_counts=json.loads((self.f.root/grant['gui_ledger']).read_bytes())
            self.assertEqual(logical_counts['paired_checkpoints'][checkpoint],2)
            self.assertEqual(logical_counts['observation_counts']['paired'],2)
            albums,_=project_native_shaped_observation(self.f,[target,neighbor],top=False,bottom=False)
            admitted,_=self.run_project_cli('admit',grant_path,begun['receipt'],dict(record=albums,target=target,session=self.f.session))
            fresh_list,_=project_native_shaped_observation(self.f,[target,neighbor],top=False,bottom=False)
            prepared,_=self.run_project_cli('prepare',grant_path,admitted['receipt'],dict(observation=fresh_list))
            run_id=prepared['result']['run_id']
            card_result,_=self.run_project_cli('gui_reserve',grant_path,store.snapshot()['receipt'],
                dict(kind='album_open',count=1,run_id=run_id,owner=self.f.owner,slots=['A.CARD']))
            card=card_result['reservation']
            self.run_project_cli('gui_consume',grant_path,store.snapshot()['receipt'],dict(reservation_id=card['id'],outcome='RETURNED'))
            cal_result,_=self.run_project_cli('gui_reserve',grant_path,store.snapshot()['receipt'],dict(kind='menu_calibration',count=2,
                run_id=run_id,owner=self.f.owner,slots=['A.CAL_OPEN','A.CAL_DISMISS']))
            cal_res=cal_result['reservation']
            self.run_project_cli('gui_consume',grant_path,store.snapshot()['receipt'],dict(reservation_id=cal_res['id'],outcome='RETURNED'))
            detail,_=project_native_shaped_observation(self.f,[target],'ALBUM_DETAIL')
            closure,_=project_native_shaped_observation(self.f,[target],'ALBUM_DETAIL')
            support=detail['mapping']['sck_support'];support_data=json.loads((self.f.root/support['path']).read_bytes())
            cal=dict(observed_at=detail['captured_at'],screenshot_width=128,screenshot_height=128,ellipsis=[115,15],
                dot_spacing=5,save_all_point=[100,50],confidence='HIGH',evidence=support['sha256'])
            applicability=service.publish('positive-applicability.json',dict(kind='LINE_MENU_APPLICABILITY',provider='SCREEN_CAPTURE_KIT',
                line_version='LINE fixture',language='en',window_class='LINE_MAIN',layout_key=detail['layout_key'],
                dimensions=[128,128],native_scale=2,menu_order=['Save All']))
            closure_ref=service.publish('positive-closure.json',dict(kind='LINE_MENU_CLOSURE',frame_id=closure['frame_id'],
                menu_closed=True,no_activation=True,detail_fingerprint=target))
            claim=dict(version=2,kind='menu-calibration-no-io-pair',run_id=run_id,session_id=self.f.session,
                detail=detail,menu_frame=detail,trigger=dict(frameId=detail['frame_id'],point=cal['ellipsis'],role='button',
                    dot_spacing=cal['dot_spacing'],bounds_px=[112,12,6,6]),label='Save All',support=support,
                guard=dict(verdict='PASS',provider='SCREEN_CAPTURE_KIT',pairFrameId=detail['frame_id'],
                    popupFrameId=support_data['sck_frame']['sha256'],supportSha256=support['sha256'],actionPoint=cal['save_all_point']),
                calibration=cal,closure_reference=closure_ref,applicability_reference=applicability,
                reservation_id=cal_res['id'],reservation_ids=[cal_res['id']],reservation_state='CONSUMED',
                opened_at=detail['captured_at'],closed_at=closure['captured_at'])
            claim_ref=service.publish('positive-calibration2.json',claim)
            menu=dict(label='Save All',frame_id=detail['frame_id'],layout_key=detail['layout_key'],evidence=claim_ref,
                safe_bounds=[90,40,20,20],ellipsis_bounds=[112,12,6,6],
                closure_trace=['OPEN_MENU','OBSERVE_SAVE_ALL','CLOSE_WITHOUT_COMMAND','DETAIL_MATCH'],
                closure_reference=closure_ref,applicability_reference=applicability)
            calibrated,_=self.run_project_cli('calibrate',grant_path,prepared['receipt'],dict(detail=detail,calibration=cal,menu=menu,closure=closure))
            fresh_intent,_=project_native_shaped_observation(self.f,[target],'ALBUM_DETAIL')
            intent,_=self.run_project_cli('intent',grant_path,calibrated['receipt'],dict(fresh=fresh_intent));action=intent['result']
            self.assertEqual(action['status'],'ORIGINAL_INTENT_COMMITTED')
            dispatch_result,_=self.run_project_cli('gui_reserve',grant_path,store.snapshot()['receipt'],dict(kind='dispatch_inputs',count=2,
                run_id=run_id,owner=self.f.owner,slots=['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']))
            dispatch_res=dispatch_result['reservation']
            self.run_project_cli('gui_consume',grant_path,store.snapshot()['receipt'],dict(reservation_id=dispatch_res['id'],outcome='RETURNED'))
            chooser_result,_=self.run_project_cli('gui_reserve',grant_path,store.snapshot()['receipt'],dict(kind='chooser_inputs',count=4,
                run_id=run_id,owner=self.f.owner,slots=['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM']))
            chooser_res=chooser_result['reservation']
            destination=action['destination'];phases=('APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED')
            original_context=dict(frame_id=fresh_intent['frame_id'],pid=fresh_intent['pid'],window_id=fresh_intent['window_id'],
                layout_key=fresh_intent['layout_key'])
            dispatch_claim=dict(run_id=run_id,action_id=action['action_id'],session_id=self.f.session,owner=self.f.owner,
                destination=destination,original_frame_id=fresh_intent['frame_id'],original_context=original_context)
            envelopes=[];previous=None
            for phase in phases:
                surface='ALBUM_DETAIL' if phase=='CONFIRM_ATTEMPTED' else 'FOLDER_CHOOSER'
                focused=1 if phase in ('GO_TO_FOLDER','PATH_FILLED') else None
                field=dict(index=1,role='text field',subrole='PathTextField',identifier='path-text',label='Go to Folder',
                    value=destination if phase in ('PATH_FILLED','DESTINATION_SELECTED') else '',bounds_px=[10,20,100,15],parent_index=0,enabled=True)
                button=dict(index=2,role='button',subrole='AXButton',identifier='confirm',label='Open',value=None,
                    bounds_px=[90,45,20,10],parent_index=0,enabled=True)
                leaf=dict(index=3,role='static text',subrole='AXStaticText',identifier='selected-folder',label=Path(destination).name,
                    value=None,bounds_px=[10,30,100,20],parent_index=0,enabled=True)
                obs,ax_ref=project_native_shaped_observation(self.f,[target],surface,
                    focus='HIGH_EDITABLE' if phase in ('GO_TO_FOLDER','PATH_FILLED') else 'NONE',
                    extra_elements=[field,button,leaf],focused_index=focused,
                    window_identifier='folder-window',window_label='Go to Folder')
                if phase=='DESTINATION_SELECTED':
                    support_ref=obs['mapping']['sck_support'];support_value=json.loads((self.f.root/support_ref['path']).read_bytes())
                    ocr_ref=support_value['ocr'];ocr_value=json.loads((self.f.root/ocr_ref['path']).read_bytes())
                    ocr_value['cua'].append(dict(text=Path(destination).name,bounds=[12,32,24,10],confidence=0.95,candidate_count=1))
                    ocr_value['sck'].append(dict(text=Path(destination).name,bounds=[12,32,24,10],confidence=0.95,candidate_count=1))
                    support_value['ocr']=self.f.ref('positive-leaf-ocr-'+uuid.uuid4().hex+'.json',json_bytes(ocr_value))
                    obs['mapping']['sck_support']=self.f.ref('positive-leaf-support-'+uuid.uuid4().hex+'.json',json_bytes(support_value))
                    rebind_project_native_support(self.f,obs)
                if phase=='APPEARED':control={'chooser_index':0,'chooser_identifier':'folder-window'}
                elif phase=='GO_TO_FOLDER':control={'path_field_index':1,'path_field_role':'text field','path_field_subrole':'PathTextField',
                    'path_field_identifier':'path-text','path_field_bounds_px':[10,20,100,15],'path_field_enabled':True,'focused':True}
                elif phase=='PATH_FILLED':control={'path_field_index':1,'path_field_role':'text field','path_field_subrole':'PathTextField',
                    'path_field_identifier':'path-text','path_field_bounds_px':[10,20,100,15],'path_field_enabled':True,
                    'value':destination,'focused':True}
                elif phase=='DESTINATION_SELECTED':control={'path_field_index':1,'path_field_identifier':'path-text',
                    'path_field_role':'text field','path_field_subrole':'PathTextField','value':destination,'selected_leaf':Path(destination).name,
                    'selected_leaf_index':3,'selected_leaf_identifier':'selected-folder','selected_leaf_bounds_px':[10,30,100,20],
                    'selected_leaf_ocr':{'text':Path(destination).name,'bounds':[12,32,24,10]},'confirm_index':2,
                    'confirm_role':'button','confirm_identifier':'confirm','confirm_bounds_px':[90,45,20,10],
                    'confirm_enabled':True,'confirm_point':[100,50]}
                else:control={'confirmation_frame_id':previous['frame']['frame_id'],'attempted':True,'invocation_count':1}
                envelope=dict(version=1,phase=phase,frame=obs,ax_state=ax_ref,sck_support=obs['mapping']['sck_support'],
                    dispatch=dispatch_claim,control=control)
                envelopes.append(envelope);previous=envelope
            event_start=dt.datetime.now(dt.timezone.utc)
            times=[event_start for _ in range(12)]
            # All chooser frames were captured before this fixed event checkpoint.
            for envelope in envelopes:
                captured=dt.datetime.fromisoformat(envelope['frame']['captured_at'].replace('Z','+00:00'))
                self.assertLessEqual(captured,event_start)
            destination_path=Path(destination);baseline_time=(times[9]-dt.timedelta(milliseconds=1)).isoformat().replace('+00:00','Z')
            destination_stat=os.lstat(destination_path)
            dest_identity=dict(device=destination_stat.st_dev,inode=destination_stat.st_ino,mode=destination_stat.st_mode,realpath=str(destination_path))
            baseline=service.publish('positive-download-baseline.json',dict(version=1,run_id=run_id,execution_id=self.f.owner,
                destination=destination,captured_at=baseline_time,destination_identity=dest_identity,inventory=[]))
            image_path=destination_path/'fixture.png';image_raw=png(8,8,19);image_path.write_bytes(image_raw)
            image_stat=os.lstat(image_path);observed_at=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
            confirmation_at=times[9].isoformat().replace('+00:00','Z')
            download=service.publish('positive-download-start.json',dict(version=1,source_kind='FILESYSTEM_DELTA',run_id=run_id,
                action_id=action['action_id'],execution_id=self.f.owner,session_id=self.f.session,destination=destination,baseline=baseline,
                confirmation_frame_id=envelopes[3]['frame']['frame_id'],confirmation_invoked_at=confirmation_at,observed_at=observed_at,
                destination_identity=dest_identity,before_inventory=[],after_inventory=[dict(name=image_path.name,bytes=len(image_raw),
                    mtime_ns=image_stat.st_mtime_ns,inode=image_stat.st_ino,sha256=sha(image_raw),recognized_image=True)],
                sampling=dict(sample_count=2,interval_ms=1000,elapsed_ms=1000)))
            observed_time=dt.datetime.fromisoformat(observed_at.replace('Z','+00:00'))
            times[10]=observed_time;times[11]=observed_time
            events=[dict(event=name,at=at.isoformat().replace('+00:00','Z')) for name,at in zip(DISPATCH_EVENT_ORDER_V3,times)]
            phase_refs=[service.publish(f'positive-chooser-{i}.json',envelope) for i,envelope in enumerate(envelopes)]
            chooser=dict(action_id=action['action_id'],session_id=self.f.session,destination=destination,full_path=destination,
                leaf=Path(destination).name,confirmation_attempts=1,frame_id=envelopes[0]['frame']['frame_id'],
                confirmation_frame_id=envelopes[3]['frame']['frame_id'],confirmation_attempted=True)
            receipt_data=dict(version='cua-dispatch-receipt-3',run_id=run_id,action_id=action['action_id'],execution_id=self.f.owner,
                session_id=self.f.session,pair_frame_id=fresh_intent['frame_id'],dispatch_policy='LOGICAL_AT_MOST_ONCE_DURABLE_PRE_INPUT_RESERVATION_NO_REPLAY',
                calibration_reference=claim_ref,calibration_closure_reference=closure_ref,applicability_reference=applicability,
                reservations=[dict(kind='dispatch_inputs',count=2,state='CONSUMED',reservation_id=dispatch_res['id']),
                    dict(kind='chooser_inputs',count=4,state='CONSUMED',reservation_id=chooser_res['id'])],events=events,chooser=chooser,
                chooser_phases=phase_refs,confirmation_frame=envelopes[3]['frame']['frame'],confirmation_point=[100,50],
                download_evidence=download,save_all_click_count=1,cease_input=True)
            receipt_ref=service.publish('positive-receipt3.json',receipt_data)
            self.assertEqual(receipt_data['pair_frame_id'],fresh_intent['frame_id'])
            self.assertEqual(events[4]['at'],events[5]['at'])
            evidence=dict(run_id=run_id,action_id=action['action_id'],execution_id=self.f.owner,observed_at=observed_at,
                save_all_click_count=1,save_all_invocation_attempted=True,failure_boundary='NONE',folder_chooser_appeared=True,
                download_started=True,provenance='Synthetic isolated fixture only; no LINE input or native receipt')
            missing,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=None),expected_code='RETAINED_RECEIPT_REQUIRED')
            self.assertEqual(missing['code'],'RETAINED_RECEIPT_REQUIRED')
            unconsumed,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=receipt_ref),expected_code='GUI_LEDGER_STATE')
            self.assertEqual(unconsumed['code'],'GUI_LEDGER_STATE')
            self.run_project_cli('gui_consume',grant_path,store.snapshot()['receipt'],
                dict(reservation_id=chooser_res['id'],outcome='RETURNED'))
            altered=copy.deepcopy(receipt_data);altered['support']=dict(path='fixture/forbidden.json',bytes=1,sha256='0'*64)
            altered_ref=service.publish('negative-receipt3-altered-schema.json',altered)
            altered_result,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=altered_ref),expected_code='INVALID_DISPATCH_RECEIPT')
            self.assertEqual(altered_result['code'],'INVALID_DISPATCH_RECEIPT')
            bad_reservation=copy.deepcopy(receipt_data);bad_reservation['reservations'][0]['reservation_id']='missing-reservation'
            bad_reservation_ref=service.publish('negative-receipt3-missing-reservation.json',bad_reservation)
            reservation_result,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_reservation_ref),expected_code='GUI_LEDGER_STATE')
            self.assertEqual(reservation_result['code'],'GUI_LEDGER_STATE')
            bad_download_ref=copy.deepcopy(receipt_data);bad_download_ref['download_evidence']=baseline
            bad_download_ref_path=service.publish('negative-receipt3-download-reference.json',bad_download_ref)
            download_reference_result,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_download_ref_path),expected_code='INVALID_DOWNLOAD_EVIDENCE')
            self.assertEqual(download_reference_result['code'],'INVALID_DOWNLOAD_EVIDENCE')
            bad_order=copy.deepcopy(receipt_data);bad_order['chooser_phases'][1],bad_order['chooser_phases'][2]=(
                bad_order['chooser_phases'][2],bad_order['chooser_phases'][1])
            bad_order_ref=service.publish('negative-receipt3-phase-order.json',bad_order)
            phase_order,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_order_ref),expected_code='CHOOSER_PHASE_ORDER')
            self.assertEqual(phase_order['code'],'CHOOSER_PHASE_ORDER')
            bad_event_order=copy.deepcopy(receipt_data)
            bad_event_order['events'][4]['event'],bad_event_order['events'][5]['event']=(
                bad_event_order['events'][5]['event'],bad_event_order['events'][4]['event'])
            bad_event_ref=service.publish('negative-receipt3-event-order.json',bad_event_order)
            event_order,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_event_ref),expected_code='RECEIPT_EVENT_ORDER')
            self.assertEqual(event_order['code'],'RECEIPT_EVENT_ORDER')
            bad_future=copy.deepcopy(receipt_data);bad_future['events'][-1]['at']='2099-10-14T00:00:00Z'
            bad_future_ref=service.publish('negative-receipt3-future-event.json',bad_future)
            future,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_future_ref),expected_code='RECEIPT_EVENT_TIME_ORDER')
            self.assertEqual(future['code'],'RECEIPT_EVENT_TIME_ORDER')
            bad_time=copy.deepcopy(receipt_data);bad_time['events'][0]['at']='not-a-time'
            bad_time_ref=service.publish('negative-receipt3-invalid-event-time.json',bad_time)
            invalid_time,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_time_ref),expected_code='RECEIPT_EVENT_TIME')
            self.assertEqual(invalid_time['code'],'RECEIPT_EVENT_TIME')
            bad_stale=copy.deepcopy(receipt_data)
            stale_envelope=copy.deepcopy(envelopes[0])
            stale_envelope['frame']['captured_at']=(dt.datetime.fromisoformat(
                stale_envelope['frame']['captured_at'].replace('Z','+00:00'))-dt.timedelta(seconds=10)).isoformat().replace('+00:00','Z')
            bad_stale['chooser_phases'][0]=service.publish('negative-receipt3-stale-phase.json',stale_envelope)
            bad_stale_ref=service.publish('negative-receipt3-stale-boundary.json',bad_stale)
            stale,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_stale_ref),expected_code='CHOOSER_PHASE_STALE')
            self.assertEqual(stale['code'],'CHOOSER_PHASE_STALE')
            bad_destination=copy.deepcopy(receipt_data);bad_destination['chooser']['destination']=destination+'/other'
            bad_destination_ref=service.publish('negative-receipt3-destination.json',bad_destination)
            destination_mismatch,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=bad_destination_ref),expected_code='CHOOSER_DISPATCH_BINDING')
            self.assertEqual(destination_mismatch['code'],'CHOOSER_DISPATCH_BINDING')
            original_path=destination_path.parent/'held-original.png'
            os.replace(image_path,original_path);image_path.write_bytes(png(8,8,20))
            replaced,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=receipt_ref),expected_code='DOWNLOAD_FILE_CHANGED')
            self.assertEqual(replaced['code'],'DOWNLOAD_FILE_CHANGED')
            image_path.unlink();os.replace(original_path,image_path)
            committed,_=self.run_project_cli('dispatch',grant_path,intent['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=receipt_ref))
            self.assertEqual(committed['result']['status'],'DOWNLOAD_STARTED')
            replay,_=self.run_project_cli('dispatch',grant_path,committed['receipt'],dict(evidence=evidence,chooser=chooser,
                download_started=True,receipt=receipt_ref),expected_code='DISPATCH_ALREADY_RECORDED')
            self.assertEqual(replay['code'],'DISPATCH_ALREADY_RECORDED')
            expected=committed['receipt']
            finished,_=self.run_project_cli('finalize',grant_path,expected,dict(decoder=str(decoder),decoder_sha256=sha(decoder.read_bytes())))
        self.assertEqual(finished['result']['status'],'VERIFIED')
        final_snapshot=store.snapshot()
        self.assertEqual(final_snapshot['receipt'],finished['receipt'])
        self.assertEqual(final_snapshot['state']['runs'][-1]['phase'],'VERIFIED')
        self.assertEqual(final_snapshot['state']['runs'][-1]['intent_state'],'TRIGGER_CONFIRMED')
        self.assertEqual(final_snapshot['state']['runs'][-1]['verification']['inventory'][0]['sha256'],sha(image_raw))
        self.assertEqual(len(final_snapshot['state']['verified_albums']),1)
        a_run=final_snapshot['state']['runs'][-1];a_batch=a_run['batch_id'];a_run_id=a_run['run_id']
        with self.root_boundary():
            stopped=service.stop(final_snapshot['receipt'],'fixture A release before C1')
            released=service.release(stopped['receipt'])
            a_phase=store.advance_project_phase(batch_cli.authorize(str(self.f.root),grant_path,False,'gui_phase'),
                'C1',a_run_id=a_run_id)
            self.assertEqual(a_phase['phase'],'C1')
            project_grant=batch_cli.authorize(str(self.f.root),grant_path,False,'gui_reserve')
            returned=store.reserve_gui(project_grant,dict(kind='return_navigation',count=1,owner=self.f.owner,
                slots=['RETURN_A_TO_LIST']))['reservation']
            store.consume_gui(project_grant,dict(reservation_id=returned['id'],outcome='RETURNED'))
            scrolled=store.reserve_gui(project_grant,dict(kind='scroll',count=1,owner=self.f.owner,
                slots=['SCROLL_1']))['reservation']
            store.consume_gui(project_grant,dict(reservation_id=scrolled['id'],outcome='RETURNED'))
            next_target=identity(2,day=9)
            before_scroll,before_ax=project_native_shaped_observation(self.f,[target,neighbor],top=False,bottom=False)
            after_scroll,after_ax=project_native_shaped_observation(self.f,[neighbor,next_target],top=False,bottom=False)
            # Synthetic C1 fixture binds the service transition; it is not live scroll evidence.
            scroll_proof=dict(slot='SCROLL_1',before_frame=before_scroll['frame'],after_frame=after_scroll['frame'],
                before_ax=before_ax,after_ax=after_ax,
                overlap='ORDERED_SUFFIX_PREFIX',overlap_count=1,new_candidate=next_target,new_candidates=[next_target],
                identity_continuity=True,context=dict(session_id=self.f.owner,group_key=self.f.cfg['group_key'],
                    provider='HOSTED_CUA',pid=2,list_window_id='fixture-list',layout_key='fixture-layout',
                    width=128,height=128,native_scale=1),movement='UPWARD_BEYOND_UNCERTAINTY')
            c1=dict(kind='LINE_TWO_ALBUM_C1',status='PASS',a_run_id=a_run_id,group_key=self.f.cfg['group_key'],
                new_candidates=[next_target],verified_scroll_count=1,scrolls=[scroll_proof])
            c1_ref=service.publish('history-admission-c1-fixture.json',c1)
            advanced=store.advance_project_phase(batch_cli.authorize(str(self.f.root),grant_path,False,'gui_phase'),
                'C1',c1_evidence=c1_ref,a_run_id=a_run_id)
            self.assertEqual(advanced['phase'],'B')
            ledger_path=self.f.root/grant['gui_ledger'];ledger=json.loads(ledger_path.read_bytes())
            self.assertEqual((ledger['lifecycle_count'],ledger['workflow_phase']),(1,'B'))
            b_begin=service.begin(released['receipt'],'backup_batch',1)
            b_active=store.snapshot()['state']['active_batch']
            self.assertEqual((b_active['owner_execution_id'],b_active['authorized_new_download_limit'],
                b_active['configured_new_download_limit']),(self.f.owner,1,1))
            ledger=json.loads(ledger_path.read_bytes());batch_ids=ledger['lifecycle_batch_ids']
            self.assertEqual((ledger['lifecycle_count'],ledger['workflow_phase']),(2,'B'))
            self.assertEqual(batch_ids,[a_batch,b_begin['result']['batch_id']])
            self.assertEqual(len(set(batch_ids)),2)
            self.assertEqual(ledger['owner'],grant['owner'])
            self.assertEqual(ledger['cap'],23)
            used=sum(entry['count'] for entry in ledger['entries'])
            self.assertEqual(used,11)
            link=dict(a_run_id=a_run_id,a_fingerprint=a_run['fingerprint'],
                lease_close=dict(path=f"{grant['artifact_dir']}/lease-close-{a_run_id}.json",
                    bytes=len((self.f.root/grant['artifact_dir']/f'lease-close-{a_run_id}.json').read_bytes()),
                    sha256=sha((self.f.root/grant['artifact_dir']/f'lease-close-{a_run_id}.json').read_bytes())),
                c1_evidence=c1_ref,released_batch_id=a_batch,workflow_owner=self.f.owner,scroll_count=1,b_target=next_target)
            b_observation=self.f.observation([next_target])
            with self.assertRaises(AcceptanceError) as missing:
                service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session)
            self.assertEqual(missing.exception.code,'BOUNDED_WORKFLOW_LINK_INVALID')
            foreign=dict(link,workflow_owner='different-owner')
            with self.assertRaises(AcceptanceError) as wrong_owner:
                service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session,foreign)
            self.assertEqual(wrong_owner.exception.code,'BOUNDED_WORKFLOW_LINK_INVALID')
            stale=dict(link,released_batch_id='BATCH-stale')
            with self.assertRaises(AcceptanceError) as stale_link:
                service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session,stale)
            self.assertEqual(stale_link.exception.code,'BOUNDED_A_BATCH_RELEASE_REQUIRED')
            forged_run=dict(link,a_run_id='another-a-run')
            with self.assertRaises(AcceptanceError) as forged_run_link:
                service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session,forged_run)
            self.assertEqual(forged_run_link.exception.code,'BOUNDED_C1_LEDGER_BINDING')
            forged_c1=dict(link,c1_evidence=service.publish('history-admission-forged-c1.json',dict(
                kind='LINE_TWO_ALBUM_C1',status='PASS',a_run_id=a_run_id,group_key=self.f.cfg['group_key'],
                new_candidates=[next_target],verified_scroll_count=1,scrolls=[scroll_proof])))
            with self.assertRaises(AcceptanceError) as forged_c1_link:
                service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session,forged_c1)
            self.assertEqual(forged_c1_link.exception.code,'BOUNDED_C1_LEDGER_BINDING')
            admitted_b=service.admit_bounded(b_begin['receipt'],b_observation,next_target,self.f.session,link)
            self.assertEqual(admitted_b['result']['status'],'ADMITTED_BOUNDED_CANDIDATE')
            self.assertEqual(admitted_b['result']['identity'],next_target)
            after=json.loads(ledger_path.read_bytes())
            self.assertEqual(sum(entry['count'] for entry in after['entries']),used)
            self.assertEqual(after['lifecycle_batch_ids'],batch_ids)

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
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_UNKNOWN_RESERVATION'):
            self.store.reserve_gui(self.grant,dict(kind='dispatch_inputs',count=2,run_id='RUN-A',owner=self.f.owner,
                slots=['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']))
        second.consume_gui(self.grant,dict(reservation_id=cal['id'],outcome='UNKNOWN'))
        reopened=Store(str(self.f.root));reopened._authorize_project_mutation=lambda *args:None
        ledger=json.loads((self.f.root/'harness-development/evidence/gui-ledger.json').read_bytes())
        self.assertEqual([slot for item in ledger['entries'] for slot in item['slots']],['A.CARD','A.CAL_OPEN','A.CAL_DISMISS'])
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_WORKFLOW_HALTED'):
            reopened.reserve_gui(self.grant,dict(kind='dispatch_inputs',count=2,run_id='RUN-A',owner=self.f.owner,
                slots=['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']))
        self.assertEqual(len(ledger['entries']),2)
    def test_paired_observation_checkpoint_cap_is_durable_and_stage_scoped(self):
        checkpoint='PAIR-A-LIST_GROUNDING'
        self.store.reserve_observation(self.grant,'paired',checkpoint=checkpoint,album='A')
        ledger_path=self.f.root/'harness-development/evidence/gui-ledger.json'
        ledger=json.loads(ledger_path.read_bytes())
        # A new cap-1 run identity cannot reset this scope-wide logical-stage counter.
        ledger.update(workflow_phase='A',lifecycle_count=1,
            lifecycle_batch_ids=['BATCH-A-RESTARTED'],last_batch_id='BATCH-A-RESTARTED')
        ledger_path.write_bytes(json_bytes(ledger))
        reopened=Store(str(self.f.root));reopened._authorize_project_mutation=lambda *args:None
        reopened.reserve_observation(self.grant,'paired',checkpoint=checkpoint,album='A')
        third=Store(str(self.f.root));third._authorize_project_mutation=lambda *args:None
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_CHECKPOINT_RECAPTURE_QUOTA'):
            third.reserve_observation(self.grant,'paired',checkpoint=checkpoint,album='A')
        reopened.reserve_observation(self.grant,'paired',checkpoint='PAIR-A-PREPARED_LIST',album='A')
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_CHECKPOINT_REQUIRED'):
            reopened.reserve_observation(self.grant,'paired',checkpoint='PAIR-A-LIST_GROUNDING-3',album='A')
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_CHECKPOINT_SCOPE'):
            reopened.reserve_observation(self.grant,'paired',checkpoint=checkpoint,album='B')
        counts=json.loads((self.f.root/'harness-development/evidence/gui-ledger.json').read_bytes())['observation_counts']
        self.assertEqual(counts['paired'],3)
        self.assertEqual(counts['paired'],sum(json.loads((self.f.root/'harness-development/evidence/gui-ledger.json')
            .read_bytes())['paired_checkpoints'].values()))
        ledger=json.loads((self.f.root/'harness-development/evidence/gui-ledger.json').read_bytes())
        ledger['paired_checkpoints']={'PAIR-A-1':1,'PAIR-A-2':2}
        ledger_path.write_bytes(json_bytes(ledger))
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_PAIRED_CHECKPOINT_QUOTA'):
            reopened.reserve_observation(self.grant,'paired',checkpoint=checkpoint,album='A')
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
