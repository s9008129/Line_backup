import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from unittest import mock
import uuid
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,Provider,TASK,ROOT,identity,json_bytes,png,utc_now
from line_backup_batch.coordinator import Coordinator
from line_backup_batch import content as content_module
from line_backup_batch.service import DISPATCH_EVENT_ORDER_V1
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
        with (TASK/f"evidence/coordinator-positive-oracles-{uuid.uuid4().hex}.json").open('x') as f:
            json.dump(dict(status=result['status'],opens=p.opens,dispatches=p.dispatches,confirms=p.confirms,
                verified_runs=[r['run_id'] for r in s['runs']],prior_runs_preserved=s['runs'][:2]==before),f,indent=2)
    def test_cap_one_does_not_loop_around_limit(self):
        self.f.close();self.f=Fixture(cap=1)
        result,p=self.run_batch([identity(2,1),identity(3,2)],2)
        self.assertEqual(result['status'],'CAP_REACHED');self.assertEqual(len(p.dispatches),1)
        state=self.f.state();self.assertEqual(state['active_batch']['new_transactions_reserved'],1)
        self.assertEqual(state['active_batch']['phase'],'STOPPED')
        released=self.f.svc.release(self.f.receipt())
        self.assertEqual(released['result']['status'],'BATCH_RELEASED')
        self.assertIsNone(self.f.state()['active_batch'])
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

def open_intent(f,target):
    f.start([target],1);f.prepare(target);return f.intent(target)

def dispatch_io(f,committed):
    action=committed['result']
    for i in range(action['fingerprint']['expected_images']):
        (Path(action['destination'])/f'{i}.png').write_bytes(png(4,4,i))
    evidence=dict(run_id=action['run_id'],action_id=action['action_id'],execution_id=f.owner,observed_at=utc_now(),
        save_all_click_count=1,save_all_invocation_attempted=True,failure_boundary='NONE',folder_chooser_appeared=True,
        download_started=True,provenance='external fixture provider; no real GUI')
    chooser=dict(action_id=action['action_id'],session_id=f.owner,destination=action['destination'],
        full_path=action['destination'],leaf=Path(action['destination']).name,confirmation_attempts=1)
    return evidence,chooser

def receipt_payload(f,committed,chooser,*,mutate_support=None,mutate_receipt=None,events=None,reservations=None):
    action=committed['result']
    obs=f.observation([action['fingerprint']])
    support_ref=obs['mapping']['sck_support']
    support=json.loads((f.root/support_ref['path']).read_bytes())
    if mutate_support is not None:
        mutate_support(support);support_ref=f.ref('support-'+uuid.uuid4().hex+'.json',json_bytes(support))
    popup=support['sck_frame']['sha256']
    receipt=dict(version='cua-dispatch-receipt-1',run_id=action['run_id'],action_id=action['action_id'],execution_id=f.owner,
        session_id=f.session,pair_frame_id=support['frame_id'],popup_frame_id=popup,support=support_ref,
        guard=dict(verdict='PASS',provider='SCREEN_CAPTURE_KIT',pairFrameId=support['frame_id'],popupFrameId=popup,
            supportSha256=support_ref['sha256'],actionPoint=list(action['save_all'])),
        reservations=reservations if reservations is not None else [
            dict(kind='dispatch_inputs',count=2,state='CONSUMED',reservation_id='RES-dispatch'),
            dict(kind='chooser_inputs',count=4,state='CONSUMED',reservation_id='RES-chooser')],
        events=events if events is not None else [dict(event=n) for n in DISPATCH_EVENT_ORDER_V1],
        chooser=copy.deepcopy(chooser),download_started=True,save_all_click_count=1,cease_input=True)
    if mutate_receipt is not None:mutate_receipt(receipt)
    return f.ref('receipt-'+uuid.uuid4().hex+'.json',json_bytes(receipt))

def verification_options():
    clock=[0]
    def sleep(seconds):clock[0]+=seconds
    return dict(clock=lambda:clock[0],sleep=sleep)

def dispatched(f):
    target=identity();committed=open_intent(f,target)
    evidence,chooser=dispatch_io(f,committed)
    ref=receipt_payload(f,committed,chooser)
    f.svc.dispatch(f.receipt(),evidence,chooser,True,receipt=ref)
    return committed,evidence,chooser

class DispatchReceiptTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def setup_intent(self):
        target=identity();committed=open_intent(self.f,target)
        evidence,chooser=dispatch_io(self.f,committed)
        return target,committed,evidence,chooser
    def test_dispatch_receipt_valid_records_download_started(self):
        target,committed,evidence,chooser=self.setup_intent()
        ref=receipt_payload(self.f,committed,chooser)
        out=self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
        self.assertEqual(out['result']['status'],'DOWNLOAD_STARTED')
        s=self.f.state();r=next(r for r in s['runs'] if r['run_id']==committed['result']['run_id'])
        self.assertEqual(r['dispatch_state'],'SAVE_ALL_RETURNED')
        self.assertEqual(r['intent_state'],'TRIGGER_CONFIRMED')
        self.assertEqual(r['dispatch_evidence']['run_id'],committed['result']['run_id'])
        self.assertTrue((self.f.root/ref['path']).exists())
    def test_dispatch_receipt_tampered_bytes_and_hash_refused(self):
        for mode in ('bytes','hash'):
            with self.subTest(mode=mode):
                self.f.close();self.f=Fixture()
                target,committed,evidence,chooser=self.setup_intent()
                ref=receipt_payload(self.f,committed,chooser)
                if mode=='bytes':(self.f.root/ref['path']).write_bytes((self.f.root/ref['path']).read_bytes()+b' ')
                else:ref=dict(ref);ref['sha256']='0'*64
                with self.assertRaises(AcceptanceError) as caught:
                    self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
                self.assertEqual(caught.exception.code,'ARTIFACT_DRIFT')
                self.assertIsNone(self.f.state()['runs'][-1]['dispatch_evidence'])
    def test_dispatch_receipt_replay_same_run_refused(self):
        target,committed,evidence,chooser=self.setup_intent()
        ref=receipt_payload(self.f,committed,chooser)
        self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
        revision=self.f.receipt()['revision']
        ref2=receipt_payload(self.f,committed,chooser)
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref2)
        self.assertEqual(caught.exception.code,'DISPATCH_ALREADY_RECORDED')
        self.assertEqual(self.f.receipt()['revision'],revision)
    def test_dispatch_receipt_stale_or_wrong_identity_refused(self):
        for name,mutate in (('run_id',lambda r:r.__setitem__('run_id','RUN-v3-stale')),
            ('action_id',lambda r:r.__setitem__('action_id','ACTION-stale')),
            ('execution_id',lambda r:r.__setitem__('execution_id','foreign'))):
            with self.subTest(name=name):
                self.f.close();self.f=Fixture()
                target,committed,evidence,chooser=self.setup_intent()
                ref=receipt_payload(self.f,committed,chooser,mutate_receipt=mutate)
                with self.assertRaises(AcceptanceError) as caught:
                    self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
                self.assertEqual(caught.exception.code,'RECEIPT_IDENTITY')
                self.assertIsNone(self.f.state()['runs'][-1]['dispatch_evidence'])
        self.f.close();self.f=Fixture()
        target,committed,evidence,chooser=self.setup_intent()
        ref=receipt_payload(self.f,committed,chooser,mutate_support=lambda s:s.__setitem__('session_id','old-session'),
            mutate_receipt=lambda r:r.__setitem__('session_id','old-session'))
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
        self.assertEqual(caught.exception.code,'RECEIPT_IDENTITY')
    def test_dispatch_receipt_structure_and_bindings_refused(self):
        cases=[
            ('missing_cease',dict(mutate_receipt=lambda r:r.pop('cease_input')),'INVALID_DISPATCH_RECEIPT'),
            ('cease_false',dict(mutate_receipt=lambda r:r.__setitem__('cease_input',False)),'RECEIPT_TRIGGER_UNPROVEN'),
            ('click_two',dict(mutate_receipt=lambda r:r.__setitem__('save_all_click_count',2)),'RECEIPT_TRIGGER_UNPROVEN'),
            ('download_false',dict(mutate_receipt=lambda r:r.__setitem__('download_started',False)),'RECEIPT_TRIGGER_UNPROVEN'),
            ('reversed_events',dict(events=[dict(event=n) for n in reversed(DISPATCH_EVENT_ORDER_V1)]),'RECEIPT_EVENT_ORDER'),
            ('extra_event',dict(events=[dict(event=n) for n in DISPATCH_EVENT_ORDER_V1]+[dict(event='UNKNOWN_EVENT')]),'RECEIPT_EVENTS'),
            ('bad_reservations',dict(reservations=[dict(kind='dispatch_inputs',count=2,state='CONSUMED',reservation_id='RES-dispatch')]),'RECEIPT_RESERVATIONS'),
            ('guard_fail',dict(mutate_receipt=lambda r:r['guard'].__setitem__('verdict','FAIL')),'RECEIPT_GUARD_UNPROVEN'),
            ('pair_mismatch',dict(mutate_receipt=lambda r:r.__setitem__('pair_frame_id','0'*64)),'RECEIPT_SUPPORT_BINDING'),
            ('popup_equals_pair',dict(mutate_receipt=lambda r:r.__setitem__('popup_frame_id',r['pair_frame_id'])),'RECEIPT_POPUP_BINDING'),
            ('chooser_leaf',dict(mutate_receipt=lambda r:r['chooser'].__setitem__('leaf','Other')),'RECEIPT_CHOOSER_MISMATCH'),
            ('guard_point',dict(mutate_receipt=lambda r:r['guard'].__setitem__('actionPoint',[101,50])),'RECEIPT_GUARD_POINT'),
        ]
        for name,kwargs,code in cases:
            with self.subTest(name=name):
                self.f.close();self.f=Fixture()
                target,committed,evidence,chooser=self.setup_intent()
                ref=receipt_payload(self.f,committed,chooser,**kwargs)
                before=len(self.f.state()['verified_albums'])
                with self.assertRaises(AcceptanceError) as caught:
                    self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
                self.assertEqual(caught.exception.code,code)
                s=self.f.state();self.assertIsNone(s['runs'][-1]['dispatch_evidence'])
                self.assertEqual(len(s['verified_albums']),before)
        self.f.close();self.f=Fixture()
        target,committed,evidence,chooser=self.setup_intent()
        evidence=dict(evidence,save_all_click_count=2)
        ref=receipt_payload(self.f,committed,chooser)
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.dispatch(self.f.receipt(),evidence,chooser,True,receipt=ref)
        self.assertEqual(caught.exception.code,'RECEIPT_CLICK_COUNT')
        self.assertIsNone(self.f.state()['runs'][-1]['dispatch_evidence'])

class PrepareTransactionTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def destination(self,target):
        return self.f.root/'backups'/'FixtureGroup'/f"{target['start_date']}_{target['end_date']}_{target['expected_images']}張"
    def test_after_intent_fault_records_effects_without_run_or_destination(self):
        target=identity();self.f.start([target],1);revision=self.f.receipt()['revision']
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.prepare(self.f.receipt(),self.f.observation([target]),fault='AFTER_INTENT')
        self.assertEqual(caught.exception.code,'FIXTURE_FAULT_AFTER_INTENT')
        evidence=self.f.root/'harness-development/evidence'
        intents=sorted(evidence.glob('filesystem-intent-*.json'));leases=sorted(evidence.glob('lease-*.json'));sides=sorted(evidence.glob('side-effect-*.json'))
        self.assertEqual((len(intents),len(leases),len(sides)),(1,1,1))
        intent=json.loads(intents[0].read_bytes());lease=json.loads(leases[0].read_bytes())
        self.assertEqual((intent['version'],intent['state']),('line-backup-filesystem-intent-1','PUBLISHED'))
        self.assertEqual((lease['version'],lease['state']),('line-backup-transaction-lease-1','OPEN'))
        side=json.loads(sides[0].read_bytes())
        self.assertTrue(side['intent_published']);self.assertTrue(side['lease_published']);self.assertFalse(side['destination_created'])
        s=self.f.state();self.assertEqual(s['runs'],[]);self.assertEqual(s['revision'],revision);self.assertIsNone(s['active_writer_id'])
        self.assertFalse(self.destination(target).exists())
    def test_after_mkdir_fault_leaves_empty_destination_and_no_run(self):
        target=identity();self.f.start([target],1);revision=self.f.receipt()['revision']
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.prepare(self.f.receipt(),self.f.observation([target]),fault='AFTER_MKDIR')
        self.assertEqual(caught.exception.code,'FIXTURE_FAULT_AFTER_MKDIR')
        destination=self.destination(target)
        self.assertTrue(destination.is_dir());self.assertEqual(list(destination.iterdir()),[])
        side=json.loads(sorted((self.f.root/'harness-development/evidence').glob('side-effect-*.json'))[0].read_bytes())
        self.assertTrue(side['destination_created'])
        s=self.f.state();self.assertEqual(s['runs'],[]);self.assertEqual(s['revision'],revision)
    def test_unknown_prepare_fault_is_refused(self):
        target=identity();self.f.start([target],1)
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.prepare(self.f.receipt(),self.f.observation([target]),fault='AFTER_DISPATCH')
        self.assertEqual(caught.exception.code,'INVALID_PREPARE_FAULT')
        self.assertEqual(self.f.state()['runs'],[])

class FinalizeFenceTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def test_finalize_commits_verified_and_closes_lease(self):
        committed,_,_=dispatched(self.f)
        out=self.f.svc.finalize(self.f.receipt(),self.f.binding['binary_path'],self.f.binding['binary_sha256'],verify_options=verification_options())
        self.assertEqual(out['result']['status'],'VERIFIED')
        s=self.f.state();r=next(r for r in s['runs'] if r['run_id']==committed['result']['run_id'])
        self.assertEqual(r['workflow_outcome'],'VERIFIED');self.assertEqual(r['phase'],'VERIFIED')
        self.assertEqual(len(s['verified_albums']),1);self.assertIsNone(s['active_writer_id'])
        close=self.f.root/self.f.artifacts/('lease-close-'+r['run_id']+'.json')
        self.assertTrue(close.exists());self.assertEqual(json.loads(close.read_bytes())['state'],'CLOSED')
        self.assertEqual(s['active_batch']['next_index'],1)
    def test_missing_or_mutated_lease_refuses(self):
        committed,_,_=dispatched(self.f)
        lease=self.f.root/self.f.artifacts/('lease-'+committed['result']['run_id']+'.json')
        original=lease.read_bytes();lease.unlink()
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.finalize(self.f.receipt(),self.f.binding['binary_path'],self.f.binding['binary_sha256'],verify_options=verification_options())
        self.assertEqual(caught.exception.code,'LEASE_REQUIRED')
        self.assertEqual(self.f.state()['runs'][-1]['workflow_outcome'],'IN_PROGRESS')
        lease.write_bytes(json_bytes(dict(json.loads(original),destination='/other')))
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.finalize(self.f.receipt(),self.f.binding['binary_path'],self.f.binding['binary_sha256'],verify_options=verification_options())
        self.assertEqual(caught.exception.code,'LEASE_MISMATCH')
        self.assertEqual(len(self.f.state()['verified_albums']),0)
    def test_replaced_destination_directory_before_commit_refuses(self):
        committed,_,_=dispatched(self.f)
        destination=Path(committed['result']['destination'])
        evidence_dir=self.f.root/self.f.artifacts/('album-'+committed['result']['run_id'])
        original=content_module.inventory;swapped=[False]
        def swap_after_verification(root,path):
            rows=original(root,path)
            if Path(path)==destination and evidence_dir.exists() and not swapped[0]:
                moved=destination.with_name(destination.name+'.moved')
                os.rename(destination,moved);destination.mkdir(mode=0o700)
                for entry in moved.iterdir():os.link(entry,destination/entry.name)
                swapped[0]=True
            return rows
        with mock.patch.object(content_module,'inventory',swap_after_verification):
            with self.assertRaises(AcceptanceError) as caught:
                self.f.svc.finalize(self.f.receipt(),self.f.binding['binary_path'],self.f.binding['binary_sha256'],verify_options=verification_options())
        self.assertTrue(swapped[0])
        self.assertEqual(caught.exception.code,'DESTINATION_IDENTITY_DRIFT')
        s=self.f.state();self.assertEqual(s['runs'][-1]['workflow_outcome'],'IN_PROGRESS')
        self.assertEqual(len(s['verified_albums']),0)
    def test_post_commit_drift_is_readback_uncertain_not_verified(self):
        committed,_,_=dispatched(self.f)
        with self.assertRaises(AcceptanceError) as caught:
            self.f.svc.finalize(self.f.receipt(),self.f.binding['binary_path'],self.f.binding['binary_sha256'],
                verify_options=verification_options(),fault='DRIFT_AFTER_COMMIT')
        self.assertEqual(caught.exception.code,'FINALIZE_READBACK_UNCERTAIN')
        s=self.f.state();r=next(r for r in s['runs'] if r['run_id']==committed['result']['run_id'])
        self.assertEqual(r['workflow_outcome'],'VERIFIED');self.assertEqual(len(s['verified_albums']),1)
        drift=sorted((self.f.root/self.f.artifacts).glob('finalize-drift-*.json'))
        self.assertEqual(len(drift),1);self.assertTrue(json.loads(drift[0].read_bytes())['state_committed'])
        closes=sorted((self.f.root/self.f.artifacts).glob('lease-close-*.json'))
        self.assertEqual(len(closes),1);self.assertEqual(json.loads(closes[0].read_bytes())['state'],'UNVERIFIED')
