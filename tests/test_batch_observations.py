import copy
import datetime as dt
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,identity,json_bytes,sha,png
from line_backup_acceptance.project_binding import ProjectReader
from line_backup_acceptance.common import AcceptanceError
from line_backup_batch.observations import frame,card_target,catalog,chooser_observation,validate_download_start,name_target_point,ocr_date_identity

class ObservationTests(unittest.TestCase):
    def setUp(self):self.f=Fixture();self.reader=ProjectReader(str(self.f.root))
    def tearDown(self):self.reader.close();self.f.close()
    def test_same_frame_full_card_safe_metadata(self):
        observation=self.f.observation([identity()])
        p=card_target(self.reader,observation,self.f.cfg,identity(),self.f.session)
        self.assertEqual(p,[40,36])
    def test_name_target_uses_exact_ocr_text_center_and_preserves_two_pixel_margin(self):
        bounds=[31,1136,258,30]
        self.assertEqual(name_target_point(bounds,2),[160,1151])
        with self.assertRaisesRegex(AcceptanceError,'CARD_NAME_TARGET_CONTROL_OVERLAP'):
            name_target_point(bounds,2,[[120,1140,40,20]])
        with self.assertRaisesRegex(AcceptanceError,'CARD_NAME_TARGET_UNSAFE'):
            name_target_point(bounds,2.01)
        with self.assertRaisesRegex(AcceptanceError,'CARD_NAME_TARGET_UNSAFE'):
            name_target_point([31,1136,258,4],2)
    def test_detail_ocr_date_identity_preserves_raw_separator_and_normalizes_fingerprint(self):
        self.assertEqual(ocr_date_identity('2024/05/27~05/31'),
            {'start_date':'2024-05-27','end_date':'2024-05-31'})
        self.assertEqual(ocr_date_identity('2024/05/27～05/31'),
            {'start_date':'2024-05-27','end_date':'2024-05-31'})
        self.assertEqual(ocr_date_identity('2024/4/21'),
            {'start_date':'2024-04-21','end_date':'2024-04-21'})
        self.assertEqual(ocr_date_identity('2024/4/21～4/21'),
            {'start_date':'2024-04-21','end_date':'2024-04-21'})
        self.assertEqual(ocr_date_identity('2024/12/30～01/02'),
            {'start_date':'2024-12-30','end_date':'2025-01-02'})
        self.assertIsNone(ocr_date_identity('2024/05/27~02/31'))
        self.assertIsNone(ocr_date_identity('2024/2/30'))
        self.assertIsNone(ocr_date_identity('2023/2/29'))
        self.assertIsNone(ocr_date_identity('2024/4/21(1/78)'))
    def test_partial_card_prohibits_click(self):
        observation=self.f.observation([identity()]);observation['cards'][0]['fully_visible']=False
        with self.assertRaisesRegex(AcceptanceError,'CARD_NOT_FULLY_VISIBLE'):
            card_target(self.reader,observation,self.f.cfg,identity(),self.f.session)
    def test_wrong_group_session_stale_mapping_and_focus_refuse(self):
        original=self.f.observation([identity()])
        for key,value in [('group_key','foreign'),('session_id','old'),('editable_focus','HIGH_EDITABLE'),
            ('editable_focus','LOW_GHOST'),('occlusion','UNKNOWN'),('frame_id','0'*64),('width',127),
            ('captured_at','2000-01-01T00:00:00Z')]:
            obs=copy.deepcopy(original);obs[key]=value
            with self.subTest(key=key),self.assertRaises(AcceptanceError):frame(self.reader,obs,self.f.cfg,session=self.f.session)
        obs=copy.deepcopy(original);obs['mapping']['frame_id']='old'
        with self.assertRaises(AcceptanceError):frame(self.reader,obs,self.f.cfg,session=self.f.session)
    def test_sck_support_is_typed_hashed_and_fixture_only(self):
        obs=self.f.observation([identity()]);frame(self.reader,obs,self.f.cfg,session=self.f.session)
        broken=copy.deepcopy(obs);broken['mapping']['sck_support']['path']='harness-development/missing-support.json'
        with self.assertRaises(AcceptanceError):frame(self.reader,broken,self.f.cfg,session=self.f.session)
        support_path=self.f.root/obs['mapping']['sck_support']['path']
        support_path.write_bytes(support_path.read_bytes()+b' ')
        with self.assertRaisesRegex(AcceptanceError,'changed between reads'):
            frame(self.reader,obs,self.f.cfg,session=self.f.session)
    def test_sck_support_rejects_wrong_provider_or_unmatched_ocr(self):
        obs=self.f.observation([identity()]);support_ref=obs['mapping']['sck_support']
        support_path=self.f.root/support_ref['path'];support=json.loads(support_path.read_bytes())
        wrong=copy.deepcopy(support);wrong['provider']='HOSTED_CUA'
        wrong_ref=self.f.ref('wrong-provider.json',json_bytes(wrong));bad=copy.deepcopy(obs);bad['mapping']['sck_support']=wrong_ref
        with self.assertRaisesRegex(AcceptanceError,'SCK_PROVIDER_MISMATCH'):
            frame(self.reader,bad,self.f.cfg,session=self.f.session)
        ocr_ref=support['ocr'];ocr_path=self.f.root/ocr_ref['path'];ocr=json.loads(ocr_path.read_bytes())
        ocr['cua']=ocr['cua'][:2]
        replacement_ocr=self.f.ref('short-ocr.json',json_bytes(ocr))
        support['ocr']=replacement_ocr
        replacement_support=self.f.ref('short-support.json',json_bytes(support));bad=copy.deepcopy(obs)
        bad['mapping']['sck_support']=replacement_support
        with self.assertRaisesRegex(AcceptanceError,'SCK_ANCHOR_COVERAGE'):
            frame(self.reader,bad,self.f.cfg,session=self.f.session)
    def test_metadata_cross_pair_and_neighbor_overlap_refuse(self):
        obs=self.f.observation([identity()]);obs['cards'][0]['metadata_bounds']=[0,0,10,10]
        with self.assertRaises(AcceptanceError):frame(self.reader,obs,self.f.cfg,session=self.f.session)
        obs=self.f.observation([identity()]);obs['cards'][0]['neighbor_bounds']=[obs['cards'][0]['metadata_bounds']]
        with self.assertRaises(AcceptanceError):frame(self.reader,obs,self.f.cfg,session=self.f.session)

    def test_native_uncertainty_cannot_be_understated_by_mapping(self):
        obs=self.f.observation([identity()]);ref=obs['mapping']['sck_support']
        sidecar=json.loads((self.f.root/ref['path']).read_bytes())
        sidecar['uncertainty_px']=4;sidecar['safe_margin_px']=8
        obs['mapping']['sck_support']=self.f.ref('higher-native-uncertainty.json',json_bytes(sidecar))
        with self.assertRaisesRegex(AcceptanceError,'MAPPING_UNCERTAINTY_UNDERSTATED'):
            frame(self.reader,obs,self.f.cfg,session=self.f.session)
    def test_complete_overlapping_catalog_and_negative_gap_boundaries(self):
        a,b,c=identity(2,1),identity(3,2),identity(4,3)
        observations=self.f.frames([a,b,c]);self.assertEqual(catalog(self.reader,observations,self.f.cfg,self.f.session),[a,b,c])
        for field in ('top','bottom'):
            altered=copy.deepcopy(observations);altered[0 if field=='top' else -1]['boundary'][field]=False
            with self.subTest(field=field),self.assertRaises(AcceptanceError):catalog(self.reader,altered,self.f.cfg,self.f.session)
        gap=[self.f.observation([a],top=True),self.f.observation([c],bottom=True)]
        with self.assertRaisesRegex(AcceptanceError,'COLLECTION_COVERAGE_GAP'):catalog(self.reader,gap,self.f.cfg,self.f.session)

    def test_bounded_admission_requires_pilot_grant_even_for_grounded_candidate(self):
        first,second=identity(),identity(day=2)
        record=self.f.observation([first,second],top=False,bottom=False)
        begun=self.f.svc.begin(self.f.receipt(),'backup_batch',1)
        before=(self.f.root/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'PROJECT_SCOPE_REQUIRED'):
            self.f.svc.admit_bounded(begun['receipt'],record,first,self.f.session)
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),before)
    def test_duplicate_identity_count_drift_and_non_date_refuse(self):
        obs=self.f.observation([identity(),identity()])
        with self.assertRaisesRegex(AcceptanceError,'AMBIGUOUS'):frame(self.reader,obs,self.f.cfg,session=self.f.session)
        obs=self.f.observation([identity()]);obs['cards'][0]['title']='Vacation'
        with self.assertRaisesRegex(AcceptanceError,'NON_DATE_TITLE'):frame(self.reader,obs,self.f.cfg,session=self.f.session)

    def test_typed_chooser_allows_high_focus_only_on_fresh_go_to_folder_field(self):
        destination='/fixture/new';phases=('APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED')
        first=self.f.observation([identity()],'FOLDER_CHOOSER')
        origin=dict(frame_id=first['frame_id'],pid=first['pid'],window_id=first['window_id'],layout_key=first['layout_key'])
        dispatch=dict(run_id='RUN-1',action_id='ACTION-1',session_id=self.f.session,owner=self.f.owner,
            destination=destination,original_frame_id=first['frame_id'],original_context=origin)
        previous=None;result=[]
        for phase in phases:
            surface='ALBUM_DETAIL' if phase=='CONFIRM_ATTEMPTED' else 'FOLDER_CHOOSER'
            obs=first if phase=='APPEARED' else self.f.observation([identity()],surface)
            focus='HIGH_EDITABLE' if phase in ('GO_TO_FOLDER','PATH_FILLED') else 'NONE'
            obs['editable_focus']=focus
            root=dict(index=0,role='window',subrole='AXWindow',identifier='folder-window',label='Go to Folder',
                value=None,bounds_px=[0,0,128,128],parent_index=None,enabled=True)
            field=dict(index=1,role='text field',subrole='PathTextField',identifier='path-text',label='Go to Folder',
                value=destination if phase in ('PATH_FILLED','DESTINATION_SELECTED') else '',bounds_px=[10,20,100,15],
                parent_index=0,enabled=True)
            button=dict(index=2,role='button',subrole='AXButton',identifier='confirm',label='Open',value=None,
                bounds_px=[90,45,20,10],parent_index=0,enabled=True)
            leaf=dict(index=3,role='static text',subrole='AXStaticText',identifier='selected-folder',label='new',value=None,
                bounds_px=[10,30,100,20],parent_index=0,enabled=True)
            focused=1 if focus=='HIGH_EDITABLE' else None
            ax=dict(version=1,frame_id=obs['frame_id'],session_id=self.f.session,pid=obs['pid'],window_id=obs['window_id'],
                surface=surface,focused_index=focused,elements=[root,field,button,leaf])
            if phase=='DESTINATION_SELECTED':
                support_ref=obs['mapping']['sck_support'];support=json.loads((self.f.root/support_ref['path']).read_bytes())
                support['interactive_intersection_px']=[88,38,24,24]
                ocr=json.loads((self.f.root/support['ocr']['path']).read_bytes())
                ocr['cua'].append(dict(text='new',bounds=[12,32,24,10],confidence=0.95,candidate_count=1))
                support['ocr']=self.f.ref('chooser-leaf-ocr-'+uuid.uuid4().hex+'.json',json_bytes(ocr))
                obs['mapping']['sck_support']=self.f.ref('chooser-leaf-support-'+uuid.uuid4().hex+'.json',json_bytes(support))
            ax_ref=self.f.ref('chooser-ax-'+uuid.uuid4().hex+'.json',json_bytes(ax))
            if phase=='APPEARED':control={'chooser_index':0,'chooser_identifier':'folder-window'}
            elif phase=='GO_TO_FOLDER':control={'path_field_index':1,'path_field_role':'text field',
                'path_field_subrole':'PathTextField','path_field_identifier':'path-text','path_field_bounds_px':[10,20,100,15],
                'path_field_enabled':True,'focused':True}
            elif phase=='PATH_FILLED':control={'path_field_index':1,'path_field_role':'text field',
                'path_field_subrole':'PathTextField','path_field_identifier':'path-text','path_field_bounds_px':[10,20,100,15],
                'path_field_enabled':True,'value':destination,'focused':True}
            elif phase=='DESTINATION_SELECTED':control={'path_field_index':1,'path_field_identifier':'path-text',
                'path_field_role':'text field','path_field_subrole':'PathTextField','value':destination,'selected_leaf':'new',
                'selected_leaf_index':3,'selected_leaf_identifier':'selected-folder','selected_leaf_bounds_px':[10,30,100,20],
                'selected_leaf_ocr':{'text':'new','bounds':[12,32,24,10]},'confirm_index':2,'confirm_role':'button',
                'confirm_identifier':'confirm','confirm_bounds_px':[90,45,20,10],'confirm_enabled':True,'confirm_point':[100,50]}
            else:control={'confirmation_frame_id':previous['frame']['frame_id'],'attempted':True,'invocation_count':1}
            envelope=dict(version=1,phase=phase,frame=obs,ax_state=ax_ref,
                sck_support=obs['mapping']['sck_support'],dispatch=dispatch,control=control)
            result.append(chooser_observation(self.reader,envelope,self.f.cfg,session=self.f.session,owner=self.f.owner,
                run_id='RUN-1',action_id='ACTION-1',destination=destination,previous=previous))
            previous=envelope
        self.assertEqual([item['phase'] for item in result],
            ['APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED'])

    def test_download_start_requires_empty_baseline_new_image_and_immutable_inventory(self):
        destination=Path(self.f.cfg['backup_root'])/'download-evidence';destination.mkdir()
        image=destination/'new.png';raw=png(4,4,8);image.write_bytes(raw)
        st=os.lstat(destination);image_stat=os.lstat(image)
        identity=dict(device=st.st_dev,inode=st.st_ino,mode=st.st_mode,realpath=str(destination))
        now=dt.datetime.now(dt.timezone.utc);confirmed=(now-dt.timedelta(seconds=0.5)).isoformat().replace('+00:00','Z')
        observed=now.isoformat().replace('+00:00','Z')
        baseline_value=dict(version=1,run_id='RUN-1',execution_id=self.f.owner,destination=str(destination),
            captured_at=(now-dt.timedelta(seconds=1)).isoformat().replace('+00:00','Z'),
            destination_identity=identity,inventory=[])
        baseline=self.f.ref('download-baseline.json',json_bytes(baseline_value))
        evidence=dict(version=1,source_kind='FILESYSTEM_DELTA',run_id='RUN-1',action_id='ACTION-1',
            execution_id=self.f.owner,session_id=self.f.session,destination=str(destination),baseline=baseline,
            confirmation_frame_id='a'*64,confirmation_invoked_at=confirmed,observed_at=observed,
            destination_identity=identity,before_inventory=[],after_inventory=[dict(name=image.name,bytes=len(raw),
                mtime_ns=image_stat.st_mtime_ns,inode=image_stat.st_ino,sha256=sha(raw),recognized_image=True)],
            sampling=dict(sample_count=2,interval_ms=1000,elapsed_ms=1000))
        evidence_ref=self.f.ref('download-start.json',json_bytes(evidence))
        validated=validate_download_start(self.reader,evidence_ref,run_id='RUN-1',action_id='ACTION-1',owner=self.f.owner,
            session=self.f.session,destination=str(destination),confirmation_frame_id='a'*64,
            confirmation_invoked_at=confirmed,now=now+dt.timedelta(seconds=1))
        self.assertEqual(validated['after_inventory'][0]['sha256'],sha(raw))

        bad=copy.deepcopy(evidence);bad['before_inventory']=[dict(name='old.png')]
        bad_ref=self.f.ref('download-start-nonempty-before.json',json_bytes(bad))
        with self.assertRaisesRegex(AcceptanceError,'DOWNLOAD_START_NOT_OBSERVED'):
            validate_download_start(self.reader,bad_ref,run_id='RUN-1',action_id='ACTION-1',owner=self.f.owner,
                session=self.f.session,destination=str(destination),confirmation_frame_id='a'*64,
                confirmation_invoked_at=confirmed,now=now+dt.timedelta(seconds=1))

        os.utime(image,ns=(image_stat.st_atime_ns,image_stat.st_mtime_ns-2_000_000_000))
        stale_stat=os.lstat(image);bad=copy.deepcopy(evidence)
        bad['after_inventory'][0]['mtime_ns']=stale_stat.st_mtime_ns
        bad['after_inventory'][0]['inode']=stale_stat.st_ino
        bad_ref=self.f.ref('download-start-preexisting-file.json',json_bytes(bad))
        with self.assertRaisesRegex(AcceptanceError,'DOWNLOAD_FILE_PREEXISTED_CONFIRMATION'):
            validate_download_start(self.reader,bad_ref,run_id='RUN-1',action_id='ACTION-1',owner=self.f.owner,
                session=self.f.session,destination=str(destination),confirmation_frame_id='a'*64,
                confirmation_invoked_at=confirmed,now=now+dt.timedelta(seconds=1))

def support_variant(f,obs,mutate_support=None,mutate_ocr=None):
    ref=obs['mapping']['sck_support'];support=json.loads((f.root/ref['path']).read_bytes())
    if mutate_ocr is not None:
        ocr_ref=support['ocr'];ocr=json.loads((f.root/ocr_ref['path']).read_bytes());mutate_ocr(ocr)
        support['ocr']=f.ref('sck-ocr-'+uuid.uuid4().hex+'.json',json_bytes(ocr))
    if mutate_support is not None:mutate_support(support)
    return f.ref('sck-support-'+uuid.uuid4().hex+'.json',json_bytes(support))

class SckIdentityTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture();self.reader=ProjectReader(str(self.f.root))
        self.obs=self.f.observation([identity()])
        frame(self.reader,self.obs,self.f.cfg,session=self.f.session)
    def tearDown(self):self.reader.close();self.f.close()
    def variant(self,**kwargs):
        bad=copy.deepcopy(self.obs);bad['mapping']['sck_support']=support_variant(self.f,bad,**kwargs);return bad
    def assert_code(self,code,**kwargs):
        with self.assertRaises(AcceptanceError) as caught:
            frame(self.reader,self.variant(**kwargs),self.f.cfg,session=self.f.session)
        self.assertEqual(caught.exception.code,code)
    def test_support_requires_fixture_provider_in_fixture_root(self):
        self.assert_code('SCK_PROVIDER_MISMATCH',
            mutate_support=lambda s:(s.__setitem__('fixture',False),s.__setitem__('provider','SCREEN_CAPTURE_KIT')))
    def test_support_binding_and_capture_time_identity(self):
        for key,value in (('pid',99),('session_id','old-session'),('layout_key','drift')):
            with self.subTest(key=key):
                self.assert_code('SCK_BINDING_MISMATCH',mutate_support=lambda s,k=key,v=value:s.__setitem__(k,v))
        captured=dt.datetime.fromisoformat(self.obs['captured_at'].replace('Z','+00:00'))
        self.assert_code('SCK_CAPTURE_TIME_MISMATCH',
            mutate_support=lambda s:s.__setitem__('captured_at',(captured-dt.timedelta(seconds=6)).isoformat()))
    def test_stale_support_refused(self):
        captured=dt.datetime.fromisoformat(self.obs['captured_at'].replace('Z','+00:00'))
        bad=self.variant(mutate_support=lambda s:s.__setitem__('captured_at',(captured-dt.timedelta(seconds=5)).isoformat()))
        with self.assertRaises(AcceptanceError) as caught:
            frame(self.reader,bad,self.f.cfg,session=self.f.session,now=captured+dt.timedelta(seconds=0.2))
        self.assertEqual(caught.exception.code,'STALE_SCK_SUPPORT')
    def test_ocr_and_native_binding_identity(self):
        self.assert_code('SCK_OCR_BINDING_MISMATCH',mutate_ocr=lambda o:o.__setitem__('cua_frame_id','x'))
        self.assert_code('SCK_NATIVE_BINDING_MISMATCH',mutate_support=lambda s:s['native_binding'].__setitem__('cua_size_px',[127,128]))
        def drop_display(s):del s['native_binding']['display_id']
        self.assert_code('SCK_NATIVE_BINDING_MISMATCH',mutate_support=drop_display)
        self.assert_code('SCK_WINDOW_BOUNDS_DRIFT',
            mutate_support=lambda s:s['native_binding'].__setitem__('sck_window_bounds_points',[0,0,120,128]))
        self.assert_code('INVALID_SCK_SUPPORT',mutate_support=lambda s:s.__setitem__('extra',1))
    def test_anchor_distribution_residual_margin_intersection(self):
        def collapse(o):
            for item in o['cua']:item['bounds']=[60,60,8,8]
        self.assert_code('SCK_ANCHOR_DISTRIBUTION',mutate_ocr=collapse)
        def low(o):
            for item in o['sck']:
                if item['text']=='anchor-low':item['bounds']=[23,100,8,8]
        self.assert_code('SCK_TRANSFORM_RESIDUAL',mutate_ocr=low)
        self.assert_code('SCK_SAFE_MARGIN',mutate_support=lambda s:s.__setitem__('safe_margin_px',5))
        self.assert_code('SCK_INTERACTIVE_INTERSECTION',
            mutate_support=lambda s:s.__setitem__('interactive_intersection_px',[90,40,10,20]))
    def test_sck_bytes_identity(self):
        support_path=self.f.root/self.obs['mapping']['sck_support']['path']
        support_path.write_bytes(support_path.read_bytes()+b' ')
        fresh=ProjectReader(str(self.f.root))
        try:
            with self.assertRaises(AcceptanceError) as caught:
                frame(fresh,self.obs,self.f.cfg,session=self.f.session)
            self.assertEqual(caught.exception.code,'ARTIFACT_DRIFT')
        finally:fresh.close()
