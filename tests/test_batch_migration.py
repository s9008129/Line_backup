import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,TASK,ROOT,identity,token,json_bytes,sha
from line_backup_acceptance.common import AcceptanceError
from line_backup_batch.store import Store

class MigrationTests(unittest.TestCase):
    def setUp(self):self.f=Fixture(version=2,cap=1)
    def tearDown(self):self.f.close()
    def test_true_cli_migration_preserves_large_integers_and_history(self):
        self.f.seed(identity(57));before=self.f.state();raw=(self.f.root/'state/backup_state.json').read_bytes()
        p,_=self.f.cli('migrate',dict(snapshot_path=self.f.artifacts+'/original.json'))
        self.assertEqual(p.returncode,0,p.stderr);after=self.f.state()
        self.assertEqual(after['schema_version'],3);self.assertEqual(after['revision'],before['revision']+1);self.assertIsNone(after['active_batch'])
        for k,v in before.items():
            if k not in ('schema_version','revision'):self.assertEqual(after[k],v)
        self.assertEqual(after['runs'][0]['verification']['inventory'][0]['mtime_ns'],9223372036854775000)
        self.assertEqual((self.f.root/self.f.artifacts/'original.json').read_bytes(),raw)
    def test_active_owner_refuses(self):
        s=self.f.state();s['active_writer_id']='foreign';self.f.save(s)
        p,_=self.f.cli('migrate',dict(snapshot_path=self.f.artifacts+'/original.json'))
        self.assertNotEqual(p.returncode,0);self.assertIn(b'MIGRATION_BUSY',p.stderr)
    def test_uncertain_readback_keeps_committed_candidate_and_no_retry(self):
        expected=self.f.receipt()
        with self.assertRaisesRegex(AcceptanceError,'fixture fault'):
            self.f.svc.store.migrate(expected,self.f.artifacts+'/original.json',fixture=True,fault='AFTER_REPLACE')
        self.assertEqual(self.f.state()['schema_version'],3)
        with self.assertRaises(AcceptanceError):self.f.svc.store.migrate(expected,self.f.artifacts+'/second.json',fixture=True)
        self.assertFalse((self.f.root/self.f.artifacts/'second.json').exists())
    def test_before_replace_failure_preserves_raw(self):
        raw=(self.f.root/'state/backup_state.json').read_bytes()
        with self.assertRaises(AcceptanceError):self.f.svc.store.migrate(self.f.receipt(),self.f.artifacts+'/original.json',fixture=True,fault='BEFORE_REPLACE')
        self.assertEqual((self.f.root/'state/backup_state.json').read_bytes(),raw)
    def test_two_cli_processes_one_stable_lock_cas_winner(self):
        # Real public actors, same existing inode and same initial expected token.
        self.f=Fixture(version=3,cap=1)
        receipt=self.f.receipt();p,argv=self.f.cli('inspect')
        grant=dict(project_root=str(self.f.root),fixture=True,artifact_dir=self.f.artifacts,owner=self.f.owner,operations=['begin','mutate'],
            config_sha256=receipt['config_sha256'],source_sha256=receipt['source_sha256'],approval=None,acceptance=None)
        g=self.f.ref('actors-grant.json',json_bytes(grant));inp=self.f.ref('actors-input.json',json_bytes(dict(expected_token=token(receipt),data=dict(mode='backup_batch',limit=1))))
        argv=[sys.executable,'-B','-m','line_backup_batch','begin','--project-root',str(self.f.root),'--authorization',g['path'],'--input',inp['path'],'--fixture']
        actors=[subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PYTHONPATH':str(ROOT/'src')}) for _ in range(2)]
        rows=[]
        for actor in actors:
            out,err=actor.communicate(timeout=30);rows.append(dict(pid=actor.pid,exit_code=actor.returncode,stdout=out.decode(),stderr=err.decode(),argv=argv))
        with (TASK/'evidence/two-cli-actor-receipts-01.json').open('x') as f:json.dump(rows,f,indent=2)
        self.assertEqual(sorted(r['exit_code'] for r in rows),[0,4],rows)
        self.assertEqual(sum('STALE_CAS' in r['stderr'] for r in rows),1,rows)
        winner=json.loads(next(r['stdout'] for r in rows if r['exit_code']==0))
        lock=(self.f.root/'state/.line-backup-state.lock').stat()
        self.assertEqual(winner['lock_identity'],[lock.st_dev,lock.st_ino])
        self.assertEqual(self.f.state()['revision'],1)
