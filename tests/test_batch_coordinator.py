import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,Provider,TASK,ROOT,identity,json_bytes
from line_backup_batch.coordinator import Coordinator
from line_backup_acceptance.common import AcceptanceError

class CoordinatorTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def run_batch(self,targets,limit):
        p=Provider(self.f,targets)
        c=Coordinator(self.f.svc,p,self.f.binding['binary_path'],self.f.binding['binary_sha256'])
        return c.run(limit),p
    def test_true_service_two_dynamic_albums_plus_verified_skips(self):
        old1,old2=identity(57,13),identity(182,14);a,b=identity(2,1),identity(3,2)
        self.f.seed(old1);self.f.seed(old2);before=copy.deepcopy(self.f.state()['runs'])
        result,p=self.run_batch([old1,a,b,old2],2)
        self.assertEqual(result['status'],'ALL_COMPLETE');self.assertEqual(p.opens,[a,b])
        self.assertEqual(len(p.dispatches),2);self.assertEqual(len(set(p.dispatches)),2);self.assertEqual(len(p.confirms),2)
        s=self.f.state();self.assertEqual(s['runs'][:2],before);self.assertEqual(len(s['verified_albums']),4)
        self.assertIsNone(s['active_writer_id']);self.assertEqual(s['active_batch']['phase'],'COMPLETED')
        self.assertEqual(s['active_batch']['new_transactions_reserved'],2)
        with (TASK/'evidence/coordinator-positive-oracles-01.json').open('x') as f:
            json.dump(dict(status=result['status'],opens=p.opens,dispatches=p.dispatches,confirms=p.confirms,
                verified_runs=[r['run_id'] for r in s['runs']],prior_runs_preserved=s['runs'][:2]==before),f,indent=2)
    def test_cap_one_does_not_loop_around_limit(self):
        self.f.close();self.f=Fixture(cap=1)
        result,p=self.run_batch([identity(2,1),identity(3,2)],2)
        self.assertEqual(result['status'],'LIMIT_REACHED');self.assertEqual(len(p.dispatches),1)
        self.assertEqual(self.f.state()['active_batch']['new_transactions_reserved'],1)
    def test_loaded_intent_and_fresh_ids_never_get_second_permission(self):
        target=identity();self.f.start([target],1);self.f.prepare(target);committed=self.f.intent(target)
        self.assertTrue(committed['new_intent']);self.assertEqual(self.f.state()['active_batch']['new_transactions_reserved'],1)
        with self.assertRaisesRegex(AcceptanceError,'LOADED_INTENT_NO_PERMISSION'):
            self.f.svc.intent(self.f.receipt(),self.f.observation([target],'ALBUM_DETAIL'))
        p,_=self.f.cli('resume');self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['additional_save_all_calls'],0)
        self.f.svc.stop(self.f.receipt(),'CRASH_AFTER_INTENT')
        with self.assertRaises(AcceptanceError):self.f.svc.release(self.f.receipt())
        with self.assertRaises(AcceptanceError):self.f.svc.begin(self.f.receipt(),'backup_batch',1)
    def test_final_scan_drift_is_not_all_complete(self):
        targets=[identity(2,1)];self.f.start(targets,1)
        with self.assertRaisesRegex(AcceptanceError,'FINAL_COLLECTION_DRIFT'):
            self.f.svc.finish(self.f.receipt(),self.f.frames([identity(3,1)]),self.f.session)
    def test_wrong_detail_before_intent_creates_no_barrier(self):
        target=identity();self.f.start([target],1);self.f.prepare(target)
        detail,cal,menu,closed=self.f.calibration(identity(3,1))
        with self.assertRaisesRegex(AcceptanceError,'TARGET_MISMATCH'):
            self.f.svc.calibrate(self.f.receipt(),detail,cal,menu,closed)
        self.assertIsNone(self.f.state()['runs'][-1]['intent'])
