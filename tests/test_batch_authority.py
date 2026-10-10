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
from line_backup_batch.store import Store
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
    def test_missing_lock_refuses_before_creation(self):
        expected=self.f.receipt();raw=(self.f.root/'state/backup_state.json').read_bytes()
        (self.f.root/'state/.line-backup-state.lock').unlink()
        with self.assertRaisesRegex(AcceptanceError,'SHARED_LOCK_UNAVAILABLE'):self.f.svc.begin(expected,'backup_batch',1)
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
            store.update(store.snapshot()['receipt'],lambda cfg,s:None)
        self.assertEqual((ROOT/'state/backup_state.json').read_bytes(),before)
    def test_legacy_canonical_replacement_refused(self):
        before=(ROOT/'state/backup_state.json').read_bytes()
        with self.assertRaisesRegex(AcceptanceError,'Canonical state requires'):
            atomic_write_json(ROOT/'state/backup_state.json',{})
        self.assertEqual((ROOT/'state/backup_state.json').read_bytes(),before)
