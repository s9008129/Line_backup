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

class LiveRootAuthorityTests(unittest.TestCase):
    def live_service(self):
        return Service(str(ROOT),'live-guard-owner','harness-development/line-v3-live-e2e-20261010/evidence',None)
    def state_bytes(self):return (ROOT/'state/backup_state.json').read_bytes()
    def test_live_dispatch_without_retained_receipt_refuses(self):
        before=self.state_bytes();svc=self.live_service()
        with self.assertRaises(AcceptanceError) as caught:
            svc.dispatch(svc.store.snapshot()['receipt'],{}, {}, True)
        self.assertEqual(caught.exception.code,'RETAINED_RECEIPT_REQUIRED')
        self.assertEqual(self.state_bytes(),before)
    def test_live_finalize_with_fixture_options_or_fault_refused(self):
        before=self.state_bytes();svc=self.live_service();receipt=svc.store.snapshot()['receipt']
        with self.assertRaises(AcceptanceError) as caught:
            svc.finalize(receipt,'/usr/bin/false','0'*64,verify_options={})
        self.assertEqual(caught.exception.code,'FIXTURE_IO_REFUSED_FOR_LIVE_PROJECT')
        with self.assertRaises(AcceptanceError) as caught:
            svc.finalize(receipt,'/usr/bin/false','0'*64,fault='DRIFT_AFTER_COMMIT')
        self.assertEqual(caught.exception.code,'INVALID_FINALIZE_FAULT')
        self.assertEqual(self.state_bytes(),before)
