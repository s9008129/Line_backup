import copy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
from unittest.mock import patch
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,Provider,identity,json_bytes,sha
from line_backup_batch.coordinator import Coordinator
from line_backup_acceptance.common import AcceptanceError,utc_now
from line_backup_batch import cli as batch_cli
from line_backup_batch import service as service_module
from line_backup_batch.service import Service
from line_backup_batch.store import (HUMAN_A56_FINGERPRINT,HUMAN_STAGE_INSTRUCTIONS,
    HUMAN_STAGE_RESERVATIONS,Store)


class BatchLifecycleTests(unittest.TestCase):
    def setUp(self):self.f=Fixture(cap=1)
    def tearDown(self):self.f.close()

    def run_batch(self,targets):
        provider=Provider(self.f,targets)
        coordinator=Coordinator(self.f.svc,provider,self.f.binding['binary_path'],self.f.binding['binary_sha256'])
        return coordinator.run(1),provider

    def test_second_cap_one_lifecycle_starts_only_after_release(self):
        first,second=identity(2,1),identity(3,2)
        first_result,first_provider=self.run_batch([first])
        self.assertEqual(first_result['status'],'ALL_COMPLETE')
        self.assertEqual(first_provider.opens,[first])
        self.assertEqual(len(first_provider.dispatches),1)
        state=self.f.state()
        self.assertEqual(state['active_batch']['phase'],'COMPLETED')
        self.assertEqual(state['active_batch']['new_transactions_reserved'],1)
        self.assertIsNone(state['active_writer_id'])

        with self.assertRaisesRegex(AcceptanceError,'BATCH_BUSY'):
            self.f.svc.begin(self.f.receipt(),'backup_batch',1)
        self.f.svc.release(self.f.receipt())
        self.assertIsNone(self.f.state()['active_batch'])

        second_result,second_provider=self.run_batch([first,second])
        self.assertEqual(second_result['status'],'ALL_COMPLETE')
        self.assertEqual(second_provider.opens,[second])
        self.assertEqual(len(second_provider.dispatches),1)
        self.assertEqual(len(second_provider.confirms),1)
        final=self.f.state()
        self.assertEqual(final['active_batch']['phase'],'COMPLETED')
        self.assertEqual(final['active_batch']['new_transactions_reserved'],1)
        self.assertEqual(final['runs'][0]['fingerprint'],first)
        self.assertEqual(final['runs'][1]['fingerprint'],second)
        self.assertEqual(final['runs'][1]['batch_id'],final['active_batch']['batch_id'])
        self.assertEqual(final['active_batch']['next_index'],2)

    def test_unresolved_intent_history_refuses_a_new_cap_one_begin(self):
        target=identity()
        admitted=self.f.svc.begin(self.f.receipt(),'backup_batch',1)['receipt']
        admitted=self.f.svc.admit(admitted,self.f.frames([target]),self.f.session)['receipt']
        self.f.svc.prepare(admitted,self.f.observation([target]))
        self.f.intent(target)
        self.f.svc.stop(self.f.receipt(),'fixture unresolved intent')
        # Isolate the begin history barrier after the terminal lease has been
        # represented as released; the SAFE_ABORT intent remains unresolved.
        state=self.f.state();state['active_batch']=None;self.f.save(state)
        with self.assertRaisesRegex(AcceptanceError,'UNRESOLVED_HISTORY'):
            self.f.svc.begin(self.f.receipt(),'backup_batch',1)


class HumanServiceFlowTests(unittest.TestCase):
    def setUp(self):
        self.fixtures=[]
        self.authorized_grants={}
        self.authorize_patch=patch.object(batch_cli,'authorize',side_effect=self.authorize)
        self.authorize_patch.start()
        fixture=Fixture(version=3,cap=1);self.fixtures.append(fixture)
        fixture.cfg['max_albums_per_run']=1;fixture.save(fixture.state())
        self.fixture=fixture
        project='harness-development/line-two-album-pilot-20261018/private'
        (fixture.root/project).mkdir(parents=True)
        receipt=fixture.receipt()
        self.grant=dict(grant_version='line-two-album-project-grant-1',
            task_id='PILOT-human-service-'+uuid.uuid4().hex,project_root=str(fixture.root),fixture=False,
            artifact_dir=project,owner=fixture.owner,
            operations=['begin','admit','prepare','calibrate','intent','dispatch','finalize','stop',
                'release','gui_reserve','gui_consume'],
            config_sha256=receipt['config_sha256'],source_sha256=receipt['source_sha256'],
            album_quota=1,lifecycle_album_limit=1,save_all_dispatch_limit=1,chooser_confirmation_limit=1,
            reversible_gui_invocation_limit=23,authorization_evidence=None,acceptance_evidence=None,
            contract_sha256=None,native_binary_sha256=None,gui_ledger=project+'/gui-ledger.json',
            single_album_route=True,execution_mode='HUMAN_ASSISTED',input_actor='OWNER_HUMAN',
            observer_session_id='human-session-'+uuid.uuid4().hex)
        grant_path=project+'/grant.json';grant_raw=json_bytes(self.grant)
        (fixture.root/grant_path).write_bytes(grant_raw)
        self.grant_path=grant_path;self.grant_sha256=sha(grant_raw)
        self.authorized_grants[(os.path.realpath(str(fixture.root)),grant_path)]=self.grant
        self.store=Store(str(fixture.root),grant_path);self.store.fixture=False
        self.store.initialize_project_ledger(self.grant,{'confirm_initialization':True})
        self.service=Service(str(fixture.root),fixture.owner,project,grant_path)
        self.destination=(f"{fixture.root}/backups/{fixture.cfg['group_name']}/"
            "2024-05-27_2024-05-31_56張")
        self.binding=dict(task_id=self.grant['task_id'],grant_sha256=self.grant_sha256,
            observer_session_id=self.grant['observer_session_id'],
            source_sha256=self.grant['source_sha256'],destination=self.destination)
        self.readiness=dict(status='OBSERVED',observed_at='2026-10-18T00:00:00+00:00',
            facts={'album_a_eligible':True},
            raw_evidence_refs=[self.put_json('readiness/readiness.json',{'kind':'human-readiness'})])
        self.stage_sequence=0

    def tearDown(self):
        self.authorize_patch.stop()
        for fixture in reversed(self.fixtures):fixture.close()

    def authorize(self,root,path,fixture,operation):
        return self.authorized_grants.get((os.path.realpath(os.fspath(root)),path))

    def put(self,name,raw):
        relative=self.grant['artifact_dir']+'/human-evidence/'+name
        target=self.fixture.root/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        return dict(path=relative,bytes=len(raw),sha256=sha(raw))

    def put_json(self,name,value):
        return self.put(name,json_bytes(value))

    @staticmethod
    def body(response):
        return response['result']

    def start(self):
        begin=self.service.human_begin(self.fixture.receipt(),self.binding,self.readiness)
        admitted=self.service.human_admit(begin['receipt'],self.binding,self.readiness,self.body(begin))
        prepared=self.service.human_prepare(admitted['receipt'],self.binding,self.readiness,
            self.body(begin),self.body(admitted))
        return begin,admitted,prepared

    def stage(self,stage,run_id,action_id,facts,pre_refs,reservation=None,consume=True,
            observed_refs=None,issued=None,reported=None,observed_at=None,recorded=None):
        if reservation is None:
            kind,slots=HUMAN_STAGE_RESERVATIONS[stage]
            reserved=self.store.reserve_gui(self.grant,dict(stage=stage,kind=kind,
                count=len(slots),run_id=run_id,owner=self.grant['owner'],slots=slots))
            reservation=reserved['reservation']
        request_id='REQUEST-'+uuid.uuid4().hex;result_id='RESULT-'+uuid.uuid4().hex
        if issued is None:
            self.stage_sequence+=1
            base=datetime(2026,10,18,0,10,tzinfo=timezone.utc)+timedelta(seconds=self.stage_sequence*10)
            issued=base.isoformat();reported=(base+timedelta(seconds=1)).isoformat()
            observed_at=(base+timedelta(seconds=2)).isoformat()
            recorded=(base+timedelta(seconds=3)).isoformat()
        request=dict(version=1,kind='human-input-request-1',task_id=self.grant['task_id'],
            grant_sha256=self.grant_sha256,execution_mode='HUMAN_ASSISTED',input_actor='OWNER_HUMAN',
            observer_session_id=self.grant['observer_session_id'],source_sha256=self.grant['source_sha256'],
            run_id=run_id,action_id=action_id,request_stage=stage,
            fingerprint=copy.deepcopy(HUMAN_A56_FINGERPRINT),
            destination=self.destination,reservation_ids=[reservation['id']],request_id=request_id,
            issued_at=issued,instruction=HUMAN_STAGE_INSTRUCTIONS[stage],
            raw_evidence_refs=copy.deepcopy(pre_refs))
        operator_ref=self.put('responses/'+uuid.uuid4().hex+'.json',json_bytes({'operator':'returned'}))
        evidence_refs=observed_refs or [self.put_json('observations/'+uuid.uuid4().hex+'.json',
            dict(kind='human-stage-observation',stage=stage,facts=facts))]
        observed=dict(status='OBSERVED',facts=copy.deepcopy(facts),observed_at=observed_at,
            raw_evidence_refs=copy.deepcopy(evidence_refs))
        result=dict(version=1,kind='human-input-result-1',task_id=self.grant['task_id'],
            grant_sha256=self.grant_sha256,execution_mode='HUMAN_ASSISTED',input_actor='OWNER_HUMAN',
            observer_session_id=self.grant['observer_session_id'],source_sha256=self.grant['source_sha256'],
            run_id=run_id,action_id=action_id,request_stage=stage,
            fingerprint=copy.deepcopy(HUMAN_A56_FINGERPRINT),destination=self.destination,
            reservation_ids=[reservation['id']],request_id=request_id,result_id=result_id,
            recorded_at=recorded,operator_reported=dict(status='OPERATOR_REPORTED',
                outcome='HUMAN_REPORTED_RETURNED',reported_at=reported,statement='observed and returned',
                raw_response_ref=operator_ref),observed=observed,outcome='HUMAN_REPORTED_RETURNED',
            raw_evidence_refs=[operator_ref,*copy.deepcopy(evidence_refs)])
        request_ref=self.put_json('requests/'+uuid.uuid4().hex+'.json',request)
        result_ref=self.put_json('results/'+uuid.uuid4().hex+'.json',result)
        if consume:
            self.store.consume_gui(self.grant,dict(reservation_id=reservation['id'],
                outcome='HUMAN_REPORTED_RETURNED',request_ref=request_ref,result_ref=result_ref,
                request_id=request_id,result_id=result_id,evidence_refs=result['raw_evidence_refs'],
                execution_mode='HUMAN_ASSISTED',input_actor='OWNER_HUMAN',
                observer_session_id=self.grant['observer_session_id']))
        return dict(request=request,result=result,requestReference=request_ref,
            resultReference=result_ref,reservation=reservation,observed=observed)

    def verify_once(self,service):
        real_inventory=service_module.content.inventory
        calls=[]
        def verify(root,destination,expected,cfg,decoder,decoder_sha):
            calls.append((destination,expected,decoder,decoder_sha))
            inventory=real_inventory(root,destination)
            verification=dict(observed_at=utc_now(),outcome='PASS',regular_files=expected,
                image_files=expected,subdirectories=[],total_bytes=sum(item['size'] for item in inventory),
                extensions={'.png':expected},metadata_files=[],zero_byte_files=[],partial_temp_files=[],
                unrecognized_files=[],other_entries=[],stable_samples=2,inventory=inventory,
                evidence='test full inventory count')
            return verification,dict(kind='test-proof')
        return verify,calls

    def test_human_admit_prepare_do_not_use_auto_frames_or_card_target(self):
        with patch.object(service_module,'card_target',
                side_effect=AssertionError('AUTO card_target called')), \
                patch.object(service_module,'frame',side_effect=AssertionError('AUTO frame called')), \
                patch.object(Service,'manifest',side_effect=AssertionError('AUTO manifest called')):
            begin,admitted,prepared=self.start()
        self.assertEqual(self.body(begin)['status'],'BATCH_OWNED')
        self.assertEqual(self.body(admitted)['status'],'ADMITTED_BOUNDED_CANDIDATE')
        prepared_body=self.body(prepared)
        self.assertEqual(prepared_body['status'],'ALBUM_OPEN_READY')
        self.assertEqual(prepared_body['project_album_slot'],'A')
        self.assertEqual(prepared_body['destination'],self.destination)
        run=[item for item in self.store.snapshot()['state']['runs']
            if item['run_id']==prepared_body['run_id']][0]
        self.assertIsNone(run['intent']);self.assertEqual(run['intent_state'],'INTENT_NONE')
        self.assertEqual(run['fingerprint'],HUMAN_A56_FINGERPRINT)

    def test_wrong_binding_and_destination_are_rejected(self):
        wrong=copy.deepcopy(self.binding);wrong['destination']=str(self.fixture.root/'backups/elsewhere')
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_begin(self.fixture.receipt(),wrong,self.readiness)
        self.assertEqual(caught.exception.code,'HUMAN_DESTINATION_BINDING')
        extra=copy.deepcopy(self.binding);extra['extra']='not-allowed'
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_begin(self.fixture.receipt(),extra,self.readiness)
        self.assertEqual(caught.exception.code,'HUMAN_BINDING_SHAPE')
        wrong_grant=copy.deepcopy(self.binding);wrong_grant['grant_sha256']='0'*64
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_begin(self.fixture.receipt(),wrong_grant,self.readiness)
        self.assertEqual(caught.exception.code,'HUMAN_GRANT_SHA256')

    def test_missing_human_evidence_is_rejected(self):
        reader=service_module.ProjectReader(str(self.fixture.root))
        try:
            fake=dict(status='OBSERVED',observed_at='2026-10-18T00:00:00+00:00',
                facts={'download_started':True},raw_evidence_refs=[dict(
                    path=self.grant['artifact_dir']+'/missing.json',bytes=1,sha256='f'*64)])
            with self.assertRaises(AcceptanceError):
                self.service._human_observed(reader,self.grant,fake,('download_started',))
        finally:reader.close()

    def test_human_evidence_must_stay_inside_the_grant_artifact_scope(self):
        reader=service_module.ProjectReader(str(self.fixture.root))
        try:
            foreign=self.fixture.root/'harness-development/foreign/private/evidence.json'
            foreign.parent.mkdir(parents=True)
            foreign.write_bytes(json_bytes({'kind':'foreign'}))
            raw=foreign.read_bytes()
            fake=dict(status='OBSERVED',observed_at='2026-10-18T00:00:00+00:00',
                facts={'download_started':True},raw_evidence_refs=[dict(
                    path='harness-development/foreign/private/evidence.json',bytes=len(raw),sha256=sha(raw))])
            with self.assertRaises(AcceptanceError) as caught:
                self.service._human_observed(reader,self.grant,fake,('download_started',))
            self.assertEqual(caught.exception.code,'HUMAN_INPUT_OBSERVED')
        finally:reader.close()

    def test_full_human_flow_uses_real_bindings_and_inventory_count(self):
        begin,admitted,prepared=self.start()
        prepared_body=self.body(prepared);run_id=prepared_body['run_id']

        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_release(prepared['receipt'],self.binding,run_id)
        self.assertEqual(caught.exception.code,'TERMINAL_BATCH_REQUIRED')

        card=self.stage('CARD',run_id,None,dict(album_detail_observed=True),
            self.readiness['raw_evidence_refs'])
        calibration_refs=[self.put_json('calibration/'+name+'.json',dict(kind=name,human=True))
            for name in ('detail','menu','closure','attestation')]
        calibration_stage=self.stage('CALIBRATION',run_id,None,dict(menu_closed=True,no_activation=True),
            card['result']['raw_evidence_refs'],observed_refs=calibration_refs)
        cal=dict(kind='human-menu-attestation-1',execution_mode='HUMAN_ASSISTED',
            input_actor='OWNER_HUMAN',observer_session_id=self.grant['observer_session_id'],
            observed_at=calibration_stage['observed']['observed_at'],detail_ref=calibration_refs[0],
            menu_ref=calibration_refs[1],closure_ref=calibration_refs[2],attestation_ref=calibration_refs[3])
        calibrated=self.service.human_commit_calibration(prepared['receipt'],self.binding,run_id,
            calibration_stage['request'],calibration_stage['result'],calibration_stage['observed'],
            cal,calibration_stage['requestReference'],calibration_stage['resultReference'])
        self.assertEqual(self.body(calibrated)['status'],'CALIBRATED')

        pre_intent=dict(status='OBSERVED',observed_at='2026-10-18T00:11:00+00:00',
            facts={'album_detail_observed':True},
            raw_evidence_refs=[self.put_json('pre-intent/detail.json',dict(kind='pre-intent-detail'))])
        committed=self.service.human_commit_intent(calibrated['receipt'],self.binding,run_id,
            self.body(calibrated),pre_intent)
        intent_body=self.body(committed)
        self.assertEqual(intent_body['status'],'ORIGINAL_INTENT_COMMITTED')
        action_id=intent_body['action_id']

        revision_before=self.store.snapshot()['receipt']['revision']
        intent_readback=self.service.human_read_intent(committed['receipt'],self.binding,run_id,action_id)
        self.assertEqual(intent_readback['action_id'],action_id)
        self.assertEqual(self.store.snapshot()['receipt']['revision'],revision_before)

        save_all=self.stage('SAVE_ALL',run_id,action_id,dict(folder_chooser_observed=True),
            pre_intent['raw_evidence_refs'])
        chooser_path=self.stage('CHOOSER_PATH',run_id,action_id,
            dict(full_path_exact=True,empty_target=True,same_window_lineage=True),
            save_all['result']['raw_evidence_refs'],consume=False)
        chooser_fact=self.store.human_reservation_fact(self.grant,chooser_path['reservation']['id'])
        self.assertEqual(chooser_fact['state'],'RESERVED')
        chooser_readback=self.put_json('chooser/readback.json',dict(
            kind='HUMAN_CHOOSER_RESERVATION_READBACK',stage='CHOOSER_PATH',
            read_at='2026-10-18T00:10:45+00:00',readback=chooser_fact))
        chooser_confirm=self.stage('CHOOSER_CONFIRM',run_id,action_id,dict(download_started=True),
            [*chooser_path['result']['raw_evidence_refs'],chooser_readback],
            reservation=chooser_path['reservation'],consume=True)

        revision_before=self.store.snapshot()['receipt']['revision']
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
                intent_body,intent_readback,save_all,chooser_path,chooser_confirm,None)
        self.assertEqual(caught.exception.code,'HUMAN_CHOOSER_RESERVATION_READBACK')
        self.assertEqual(self.store.snapshot()['receipt']['revision'],revision_before)
        forged_fact=copy.deepcopy(chooser_fact);forged_fact['state']='CONSUMED'
        forged=self.put_json('chooser/readback-forged.json',dict(
            kind='HUMAN_CHOOSER_RESERVATION_READBACK',stage='CHOOSER_PATH',
            read_at='2026-10-18T00:10:45+00:00',readback=forged_fact))
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
                intent_body,intent_readback,save_all,chooser_path,chooser_confirm,{'reference':forged})
        self.assertEqual(caught.exception.code,'HUMAN_CHOOSER_RESERVATION_READBACK')
        late=self.put_json('chooser/readback-late.json',dict(
            kind='HUMAN_CHOOSER_RESERVATION_READBACK',stage='CHOOSER_PATH',
            read_at='2026-10-18T00:10:55+00:00',readback=chooser_fact))
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
                intent_body,intent_readback,save_all,chooser_path,chooser_confirm,{'reference':late})
        self.assertEqual(caught.exception.code,'HUMAN_CHOOSER_RESERVATION_READBACK')
        foreign=self.put_json('chooser/readback-foreign.json',dict(
            kind='HUMAN_CHOOSER_RESERVATION_READBACK',stage='CHOOSER_PATH',
            read_at='2026-10-18T00:10:45+00:00',readback=chooser_fact))
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
                intent_body,intent_readback,save_all,chooser_path,chooser_confirm,{'reference':foreign})
        self.assertEqual(caught.exception.code,'HUMAN_CHOOSER_RESERVATION_READBACK')
        self.assertEqual(self.store.snapshot()['receipt']['revision'],revision_before)

        bad=copy.deepcopy(chooser_confirm);bad['result']=copy.deepcopy(bad['result'])
        bad['result']['observed']['facts']['download_started']=False
        with self.assertRaises(AcceptanceError):
            self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
                intent_body,intent_readback,save_all,chooser_path,bad,{'reference':chooser_readback})

        dispatched=self.service.human_record_dispatch(committed['receipt'],self.binding,run_id,
            intent_body,intent_readback,save_all,chooser_path,chooser_confirm,
            {'reference':chooser_readback})
        self.assertEqual(self.body(dispatched)['status'],'DOWNLOAD_STARTED')

        destination=Path(self.destination);destination.mkdir(parents=True,exist_ok=True)
        for index in range(55):
            (destination/f'{index:02d}.png').write_bytes(b'\x89PNG\r\n\x1a\n'+index.to_bytes(2,'big'))
        verify,_=self.verify_once(self.service)
        with patch.object(service_module.content,'verify',side_effect=verify):
            with self.assertRaises(AcceptanceError) as caught:
                self.service.human_finalize(dispatched['receipt'],self.binding,run_id,
                    '/decoder',self.grant_sha256)
        self.assertEqual(caught.exception.code,'HUMAN_VERIFICATION_REQUIRED')
        (destination/'55.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'55')
        verify,calls=self.verify_once(self.service)
        with patch.object(service_module.content,'verify',side_effect=verify):
            finalized=self.service.human_finalize(dispatched['receipt'],self.binding,run_id,
                '/decoder',self.grant_sha256)
        self.assertEqual(self.body(finalized)['status'],'VERIFIED')
        self.assertEqual(self.body(finalized)['files_verified'],56)
        self.assertEqual(self.body(finalized)['expected_images'],56)
        self.assertEqual(calls[-1][1],56)

        revision_before=self.store.snapshot()['receipt']['revision']
        verified=self.service.human_read_verified(finalized['receipt'],self.binding,run_id)
        self.assertEqual(verified['status'],'VERIFIED')
        self.assertEqual(verified['files_verified'],56)
        self.assertEqual(self.store.snapshot()['receipt']['revision'],revision_before)

        stopped=self.service.human_stop(finalized['receipt'],self.binding,run_id,
            'VERIFIED_HUMAN_ASSISTED_SINGLE_ALBUM')
        self.assertEqual(self.body(stopped)['status'],'STOPPED')
        with self.assertRaises(AcceptanceError) as caught:
            self.service.human_stop(stopped['receipt'],self.binding,run_id,'DIFFERENT_REASON')
        self.assertEqual(caught.exception.code,'HUMAN_STOP_IDEMPOTENCY_CONFLICT')
        again=self.service.human_stop(stopped['receipt'],self.binding,run_id,
            'VERIFIED_HUMAN_ASSISTED_SINGLE_ALBUM')
        self.assertEqual(again['status'],'STOPPED')
        released=self.service.human_release(stopped['receipt'],self.binding,run_id)
        self.assertEqual(self.body(released)['status'],'BATCH_RELEASED')
        self.assertIsNone(self.store.snapshot()['state']['active_batch'])


if __name__=='__main__':unittest.main()
