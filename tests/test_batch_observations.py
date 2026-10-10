import copy
import datetime as dt
import json
import os
import sys
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,identity,json_bytes,sha
from line_backup_acceptance.project_binding import ProjectReader
from line_backup_acceptance.common import AcceptanceError
from line_backup_batch.observations import frame,card_target,catalog

class ObservationTests(unittest.TestCase):
    def setUp(self):self.f=Fixture();self.reader=ProjectReader(str(self.f.root))
    def tearDown(self):self.reader.close();self.f.close()
    def test_same_frame_full_card_safe_metadata(self):
        observation=self.f.observation([identity()])
        p=card_target(self.reader,observation,self.f.cfg,identity(),self.f.session)
        self.assertEqual(p,[40,36])
    def test_partial_card_prohibits_click(self):
        observation=self.f.observation([identity()]);observation['cards'][0]['fully_visible']=False
        with self.assertRaisesRegex(AcceptanceError,'CARD_NOT_FULLY_VISIBLE'):
            card_target(self.reader,observation,self.f.cfg,identity(),self.f.session)
    def test_wrong_group_session_stale_mapping_and_focus_refuse(self):
        original=self.f.observation([identity()])
        for key,value in [('group_key','foreign'),('session_id','old'),('editable_focus','HIGH_EDITABLE'),
            ('occlusion','UNKNOWN'),('frame_id','0'*64),('width',127),('captured_at','2000-01-01T00:00:00Z')]:
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
    def test_complete_overlapping_catalog_and_negative_gap_boundaries(self):
        a,b,c=identity(2,1),identity(3,2),identity(4,3)
        observations=self.f.frames([a,b,c]);self.assertEqual(catalog(self.reader,observations,self.f.cfg,self.f.session),[a,b,c])
        for field in ('top','bottom'):
            altered=copy.deepcopy(observations);altered[0 if field=='top' else -1]['boundary'][field]=False
            with self.subTest(field=field),self.assertRaises(AcceptanceError):catalog(self.reader,altered,self.f.cfg,self.f.session)
        gap=[self.f.observation([a],top=True),self.f.observation([c],bottom=True)]
        with self.assertRaisesRegex(AcceptanceError,'COLLECTION_COVERAGE_GAP'):catalog(self.reader,gap,self.f.cfg,self.f.session)
    def test_duplicate_identity_count_drift_and_non_date_refuse(self):
        obs=self.f.observation([identity(),identity()])
        with self.assertRaisesRegex(AcceptanceError,'AMBIGUOUS'):frame(self.reader,obs,self.f.cfg,session=self.f.session)
        obs=self.f.observation([identity()]);obs['cards'][0]['title']='Vacation'
        with self.assertRaisesRegex(AcceptanceError,'NON_DATE_TITLE'):frame(self.reader,obs,self.f.cfg,session=self.f.session)
