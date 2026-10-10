import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,ROOT,TASK,identity,sha,json_bytes,token
from line_backup_batch.store import Store,enforce_grant_quota
from line_backup_batch.service import Service
from line_backup_acceptance.common import AcceptanceError,atomic_write_json

class AuthorityTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def test_cli_explicit_authority_and_opaque_receipt(self):
        p,_=self.f.cli('begin',dict(mode='backup_batch',limit=1))
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout);self.assertNotIn('receipt',result);self.assertIn('receipt_token',result)
        self.assertEqual(self.f.state()['active_batch']['new_transactions_reserved'],0)
    def test_fixture_grant_is_operation_exact_and_cannot_dispatch(self):
        before=(self.f.root/'state/backup_state.json').read_bytes()
        p,_=self.f.cli('begin',dict(mode='backup_batch',limit=1),grant_operations=['admit'])
        self.assertEqual(p.returncode,4);self.assertIn(b'GRANT_SCOPE',p.stderr)
        p,_=self.f.cli('dispatch',grant_operations=['dispatch'])
        self.assertEqual(p.returncode,4);self.assertIn(b'FIXTURE_LIVE_OPERATION_REFUSED',p.stderr)
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
        store=Store(str(ROOT));before=(ROOT/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'LIVE_AUTHORITY_REQUIRED'):
            store._update(store.snapshot()['receipt'],lambda cfg,s:None,operation='begin')
        self.assertEqual((ROOT/'state/backup_state.json').read_bytes(),before)
    def test_generic_mutation_has_no_production_authorization_fallback(self):
        store=Store(str(ROOT))
        before=(ROOT/'state/backup_state.json').read_bytes()
        self.assertFalse(hasattr(store,'update'))
        with self.assertRaises(AcceptanceError) as caught:
            store._update(store.snapshot()['receipt'],lambda cfg,s:None,operation='mutate')
        self.assertEqual(caught.exception.code,'OPERATION_REQUIRED')
        self.assertEqual((ROOT/'state/backup_state.json').read_bytes(),before)
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
        before=(ROOT/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'Canonical state requires'):
            atomic_write_json(ROOT/'state/backup_state.json',{})
        self.assertEqual((ROOT/'state/backup_state.json').read_bytes(),before)
