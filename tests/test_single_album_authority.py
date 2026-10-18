import contextlib
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.project_binding import ProjectReader
from line_backup_batch import cli, store, service
from line_backup_batch.observations import artifact


HUMAN_CLI_PROJECT_ROOT='/project'
HUMAN_CLI_AUTHORIZATION='harness-development/test/private/grant.json'
HUMAN_CLI_INPUT='harness-development/test/private/input.json'


def _human_cli_receipt(grant):
    return {'project_root':HUMAN_CLI_PROJECT_ROOT,'config_sha256':grant['config_sha256'],
        'source_sha256':grant['source_sha256']}


def _human_cli_token(value):
    return base64.b64encode(json.dumps(value,separators=(',',':')).encode()).decode('ascii')


def _human_cli_namespace(operation):
    return SimpleNamespace(operation=operation,project_root=HUMAN_CLI_PROJECT_ROOT,
        authorization=HUMAN_CLI_AUTHORIZATION,input=HUMAN_CLI_INPUT,fixture=False)


def _human_cli_grant():
    return {
        'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True,
        'execution_mode':cli.HUMAN_EXECUTION_MODE,'input_actor':cli.HUMAN_INPUT_ACTOR,
        'observer_session_id':'deepseek-session-01','task_id':'PILOT-human-cli',
        'owner':'owner-1','project_root':HUMAN_CLI_PROJECT_ROOT,'source_sha256':'a'*64,
        'config_sha256':'b'*64,'artifact_dir':'harness-development/test/private',
        'decoder_binding':{'path':'rev28/.build/release/rev28ctl','bytes':1,'sha256':'f'*64}}


def _human_cli_binding(grant):
    return {
        'destination':'/Users/tester/Downloads/album-a56',
        'grant_sha256':'9'*64,
        'observer_session_id':grant['observer_session_id'],
        'source_sha256':grant['source_sha256'],
        'task_id':grant['task_id']}


def _human_cli_evidence_ref(name):
    return {'path':f'harness-development/test/private/{name}.json','bytes':1,'sha256':'c'*64}


def _human_cli_calibration(grant):
    return {
        'kind':'human-menu-attestation-1','execution_mode':cli.HUMAN_EXECUTION_MODE,
        'input_actor':cli.HUMAN_INPUT_ACTOR,'observer_session_id':grant['observer_session_id'],
        'observed_at':'2026-10-18T00:00:00Z','detail_ref':_human_cli_evidence_ref('detail'),
        'menu_ref':_human_cli_evidence_ref('menu'),'closure_ref':_human_cli_evidence_ref('closure'),
        'attestation_ref':_human_cli_evidence_ref('attestation')}


class _HumanCliRecordingService:
    instances=[]
    def __init__(self,*args):
        self.init_args=args;self.calls=[];self.instances.append(self)
    def __getattr__(self,name):
        if name.startswith('__'):raise AttributeError(name)
        def record(*args,**kwargs):
            self.calls.append((name,args,kwargs));return {'method':name,'args':args}
        return record
    @staticmethod
    def eligible(state,target):
        return True


class _HumanCliSilentStore:
    instances=[]
    def __init__(self,root):
        self.root=root;self.authorization_path=None;self.calls=[];self.instances.append(self)


class _HumanCliInspectStore(_HumanCliSilentStore):
    snapshot_value=None
    def snapshot(self):
        self.snapshot_calls=getattr(self,'snapshot_calls',0)+1
        return self.snapshot_value
    def human_reservation_fact(self,*args):
        self.calls.append(('human_reservation_fact',args));return {'kind':'reservation-fact','args':args}
    def human_intent_fact(self,*args):
        self.calls.append(('human_intent_fact',args));return {'kind':'intent-fact','args':args}
    def human_verified_fact(self,*args):
        self.calls.append(('human_verified_fact',args));return {'kind':'verified-fact','args':args}


class One56AuthorityTests(unittest.TestCase):
    HUMAN_GRANT_SHA='9'*64
    HUMAN_OBSERVER='deepseek-v4.1-flash:1017-session-01'

    def _human_grant(self):
        bundle=cli.PROJECT_DIR+'/private/authority-bundles/ONE56-human-test'
        return {
            'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True,
            'execution_mode':cli.HUMAN_EXECUTION_MODE,'input_actor':cli.HUMAN_INPUT_ACTOR,
            'observer_session_id':self.HUMAN_OBSERVER,
            'task_id':'PILOT-human-1','owner':'owner-1','project_root':'/project',
            'source_sha256':'a'*64,'config_sha256':'b'*64,
            'entry_binding':{'path':cli.PROJECT_DIR+'/two_album_entry.mjs','bytes':1,'sha256':'c'*64},
            'runtime_binding':{'path':bundle+'/runtime-binding.json','bytes':1,'sha256':'d'*64},
            'producer_binary':{'path':bundle+'/producer','bytes':1,'sha256':'e'*64},
            'decoder_binding':{'path':'rev28/.build/release/rev28ctl','bytes':1,'sha256':'f'*64},
        }

    def _human_artifact(self,grant,**extra):
        document={
            'execution_mode':cli.HUMAN_EXECUTION_MODE,'input_actor':cli.HUMAN_INPUT_ACTOR,
            'observer_session_id':grant['observer_session_id'],'grant_sha256':self.HUMAN_GRANT_SHA,
            'task_id':grant['task_id'],'owner':grant['owner'],'project_root':grant['project_root'],
            'source_sha256':grant['source_sha256'],'config_sha256':grant['config_sha256'],
            'entry_method':cli.ONE56_HUMAN_ENTRY,'entry_sha256':grant['entry_binding']['sha256'],
            'runtime_binding_sha256':grant['runtime_binding']['sha256'],
            'producer_binary_sha256':grant['producer_binary']['sha256'],
            'decoder_sha256':grant['decoder_binding']['sha256'],
            'fingerprint':dict(cli.ONE56_HUMAN_FINGERPRINT),
        }
        document.update(extra)
        return document

    def _human_contract(self,grant,grant_sha=None):
        return self._human_artifact(grant,status='ACTIVE',closed=False,
            implementation_head='1'*40,operations=sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS),
            grant_sha256=grant_sha or self.HUMAN_GRANT_SHA)

    def _human_review(self,grant,reviewer='ChatGPT Chief',disposition='review:123'):
        return self._human_artifact(grant,profile=cli.PROJECT_SCOPE,
            verdict='APPROVE_IMPLEMENTATION',review_method='OWNER_TRANSFERRED_EXTERNAL_PR_REVIEW',
            reviewer=reviewer,implementation_head='1'*40,
            approved_operations=sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS),
            disposition_ref=disposition)

    def _human_original(self,grant,reviewer='ChatGPT Chief',disposition='review:123'):
        return self._human_artifact(grant,verdict='APPROVE_IMPLEMENTATION',reviewer=reviewer,
            disposition_ref=disposition,implementation_head='1'*40,
            approved_operations=sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS))

    def _human_provider_review(self,grant):
        review_id=987654322
        scope={
            'decision':'APPROVE_IMPLEMENTATION','external_reviewer':'ChatGPT Chief',
            'task_id':grant['task_id'],'owner':grant['owner'],'project_root':grant['project_root'],
            'implementation_head':'1'*40,'source_sha256':grant['source_sha256'],
            'config_sha256':grant['config_sha256'],
            'runtime_binding_sha256':grant['runtime_binding']['sha256'],
            'producer_binary_sha256':grant['producer_binary']['sha256'],
            'entry_sha256':grant['entry_binding']['sha256'],'entry_method':cli.ONE56_HUMAN_ENTRY,
            'approved_operations':sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS),
            'fingerprint':dict(cli.ONE56_HUMAN_FINGERPRINT),
            'execution_mode':cli.HUMAN_EXECUTION_MODE,'input_actor':cli.HUMAN_INPUT_ACTOR,
            'observer_session_id':grant['observer_session_id'],'grant_sha256':self.HUMAN_GRANT_SHA,
            'decoder_sha256':grant['decoder_binding']['sha256'],
        }
        raw={'id':review_id,'pull_request_url':cli.ONE56_PULL_REQUEST_API,
            'html_url':cli.ONE56_PULL_REQUEST_HTML+f'#pullrequestreview-{review_id}',
            'state':'APPROVED','user':{'login':'s9008129','id':129814822},'commit_id':'1'*40,
            'body':'External Chief exact-source approval.\n<!-- ONE56_REVIEW_SCOPE_V1\n'
                +json.dumps(scope)+'\nONE56_REVIEW_SCOPE_END -->'}
        review=self._human_artifact(grant,provider_review_id=review_id,
            provider_review_url=cli.ONE56_PROVIDER_REPOSITORY+f'/pulls/10/reviews/{review_id}',
            pull_request_url=cli.ONE56_PULL_REQUEST_API,pull_request_html_url=cli.ONE56_PULL_REQUEST_HTML,
            provider_state='APPROVED',provider_actor='s9008129',implementation_head='1'*40,
            reviewer='ChatGPT Chief',disposition_ref=raw['html_url'])
        return raw,review,self._human_contract(grant)

    def test_human_execution_mode_is_explicit_and_partial_human_fields_fail_closed(self):
        auto={'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True}
        self.assertEqual(cli.one56_execution_mode(auto),'AUTO')
        human={'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True,
            'execution_mode':cli.HUMAN_EXECUTION_MODE,'input_actor':cli.HUMAN_INPUT_ACTOR,
            'observer_session_id':self.HUMAN_OBSERVER}
        self.assertEqual(cli.one56_execution_mode(human),cli.HUMAN_EXECUTION_MODE)
        for field in sorted(cli.HUMAN_GRANT_FIELDS):
            candidate=dict(human);candidate.pop(field)
            with self.subTest(missing=field),self.assertRaises(AcceptanceError):
                cli.one56_execution_mode(candidate)
        for key,value in (('execution_mode','AUTO'),('execution_mode',cli.HUMAN_EXECUTION_MODE+' '),
            ('input_actor','AGENT'),('observer_session_id',''),('observer_session_id',' '+self.HUMAN_OBSERVER),
            ('observer_session_id',self.HUMAN_OBSERVER+'\n'),('observer_session_id',7)):
            with self.subTest(key=key,value=value),self.assertRaises(AcceptanceError):
                cli.one56_execution_mode({**human,key:value})
        with self.assertRaises(AcceptanceError):
            cli.one56_execution_mode({**auto,'execution_mode':cli.HUMAN_EXECUTION_MODE})

    def test_human_contract_review_and_provider_scope_bind_exact_grant_and_entry(self):
        grant=self._human_grant()
        contract=self._human_contract(grant)
        review=self._human_review(grant)
        original=self._human_original(grant)
        raw,provider_review,provider_contract=self._human_provider_review(grant)
        cli.validate_one56_contract(contract,grant,'/project',grant_sha256=self.HUMAN_GRANT_SHA)
        cli.validate_one56_review(review,original,grant,grant_sha256=self.HUMAN_GRANT_SHA)
        cli.validate_one56_provider_review(raw,provider_review,provider_contract,grant,
            grant_sha256=self.HUMAN_GRANT_SHA)
        contract_cases=[
            {**contract,'execution_mode':'AUTO'},{**contract,'input_actor':'AGENT'},
            {**contract,'observer_session_id':'other'},{**contract,'grant_sha256':'0'*64},
            {**contract,'task_id':'PILOT-other'},{**contract,'source_sha256':'0'*64},
            {**contract,'entry_method':cli.ONE56_ENTRY},
            {**contract,'operations':sorted(cli.ONE56_REQUIRED_OPERATIONS)},
            {**contract,'fingerprint':{'start_date':'2024-05-27','end_date':'2024-05-31','expected_images':65}},
        ]
        for changed in contract_cases:
            with self.subTest(contract=changed),self.assertRaises(AcceptanceError):
                cli.validate_one56_contract(changed,grant,'/project',grant_sha256=self.HUMAN_GRANT_SHA)
        review_cases=[
            {**review,'execution_mode':'AUTO'},{**review,'input_actor':'AGENT'},
            {**review,'observer_session_id':'other'},{**review,'grant_sha256':'0'*64},
            {**review,'entry_method':cli.ONE56_ENTRY},
            {**review,'approved_operations':sorted(cli.ONE56_REQUIRED_OPERATIONS)},
            {**review,'fingerprint':{'start_date':'2024-05-27','end_date':'2024-05-31','expected_images':65}},
        ]
        for changed in review_cases:
            with self.subTest(review=changed),self.assertRaises(AcceptanceError):
                cli.validate_one56_review(changed,original,grant,grant_sha256=self.HUMAN_GRANT_SHA)
        scope=cli._one56_scope_from_body(raw['body'])
        scope_cases=[('execution_mode','AUTO'),('input_actor','AGENT'),('observer_session_id','other'),
            ('grant_sha256','0'*64),('entry_method',cli.ONE56_ENTRY),
            ('approved_operations',sorted(cli.ONE56_REQUIRED_OPERATIONS)),
            ('fingerprint',{'start_date':'2024-05-27','end_date':'2024-05-31','expected_images':65}),
            ('decoder_sha256','0'*64)]
        for key,value in scope_cases:
            bad_scope={**scope,key:value}
            bad_raw={**raw,'body':'External Chief exact-source approval.\n<!-- ONE56_REVIEW_SCOPE_V1\n'
                +json.dumps(bad_scope)+'\nONE56_REVIEW_SCOPE_END -->'}
            with self.subTest(scope=key),self.assertRaises(AcceptanceError):
                cli.validate_one56_provider_review(bad_raw,provider_review,provider_contract,grant,
                    grant_sha256=self.HUMAN_GRANT_SHA)

    def test_auto_provider_review_and_payload_reject_human_mode_markers(self):
        raw,wrapper,contract,grant=self._synthetic_github_review()
        auto_cases=[
            ({**raw,'execution_mode':cli.HUMAN_EXECUTION_MODE},wrapper,contract),
            (raw,{**wrapper,'input_actor':cli.HUMAN_INPUT_ACTOR},contract),
            (raw,wrapper,{**contract,'execution_mode':cli.HUMAN_EXECUTION_MODE}),
            (raw,wrapper,{**contract,'operations':sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS)}),
        ]
        for raw_case,wrapper_case,contract_case in auto_cases:
            with self.subTest(case=(raw_case is not raw,wrapper_case is not wrapper,contract_case is not contract)), \
                    self.assertRaises(AcceptanceError):
                cli.validate_one56_provider_review(raw_case,wrapper_case,contract_case,grant)
        auto_grant={'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True}
        cli.validate_one56_payload(auto_grant,'prepare',{'data':{'workflow_link':{'phase':'B'},'gui_phase':'C1'}})
        for data in ({'execution_mode':cli.HUMAN_EXECUTION_MODE},{'input_actor':cli.HUMAN_INPUT_ACTOR},
            {'request_stage':'SAVE_ALL'},{'entry_method':cli.ONE56_HUMAN_ENTRY},
            {'kind':'human-input-request-1'},
            {'operations':sorted(cli.ONE56_HUMAN_REQUIRED_OPERATIONS)}):
            with self.subTest(data=data),self.assertRaises(AcceptanceError):
                cli.validate_one56_payload(auto_grant,'prepare',{'data':data})
        cli.validate_one56_payload(auto_grant,'prepare',{'data':{'execution_mode':'AUTO'}})

    def test_bundle_path_has_one_normalized_unique_layout(self):
        expected='harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-run_17'
        self.assertEqual(cli.one56_bundle(expected+'/project-grant.json'),expected)
        for path in (
            '/'+expected+'/project-grant.json',
            expected+'//project-grant.json',
            expected+'/../ONE56-other/project-grant.json',
            expected.replace('ONE56-run_17','ONE56-../bad')+'/project-grant.json',
            expected.replace('ONE56-run_17','one56-run_17')+'/project-grant.json',
            expected.replace('ONE56-run_17','ONE56-x')+'/other.json',
            expected.replace('authority-bundles/','private/authority-bundles/')+'/project-grant.json',
        ):
            with self.subTest(path=path), self.assertRaises(AcceptanceError):
                cli.one56_bundle(path)

    def test_project_reader_rejects_symlinked_bundle_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            base=root/'harness-development/line-two-album-pilot-20261014/private'
            base.mkdir(parents=True)
            real=base/'real-bundles';real.mkdir()
            (base/'authority-bundles').symlink_to(real,target_is_directory=True)
            reader=ProjectReader(str(root))
            try:
                with self.assertRaises(AcceptanceError):
                    reader.read('harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-x/project-grant.json')
            finally:
                reader.close()

    def test_new_bundle_refs_must_be_exact_siblings(self):
        bundle='harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-run_17'
        cli._one56_ref({'path':bundle+'/implementation-review.json','bytes':1,'sha256':'a'*64},
            bundle,'implementation-review.json')
        for ref in (
            {'path':bundle+'/../implementation-review.json','bytes':1,'sha256':'a'*64},
            {'path':bundle.replace('ONE56-run_17','ONE56-other')+'/implementation-review.json','bytes':1,'sha256':'a'*64},
            {'path':bundle+'/implementation-review.json','bytes':True,'sha256':'a'*64},
        ):
            with self.subTest(ref=ref), self.assertRaises(AcceptanceError):
                cli._one56_ref(ref,bundle,'implementation-review.json')

    def test_owner_confirmed_display_title_alias_is_exact_and_same_bundle(self):
        bundle='harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-test'
        ref={'path':bundle+'/display-title-alias-confirmation.json','bytes':72,'sha256':'a'*64}
        decision={'display_title_alias':'OCR variant','display_title_alias_confirmation_ref':ref}
        consent={'display_title_alias':'OCR variant','display_title_alias_confirmation_ref':ref}
        confirmation={'version':1,'task_id':'PILOT-1','owner':'owner-1','project_root':'/project',
            'canonical_group_name':'Canonical group','display_title_alias':'OCR variant',
            'owner_statement':'- 是，同一群組；保留原備份名稱\n這是視覺辨識的中文字差異'}
        self.assertEqual(cli.validate_one56_display_title_alias(decision,consent,confirmation,task_id='PILOT-1',
            owner='owner-1',root='/project',canonical_group='Canonical group',alias_ref=ref),
            'OCR variant')
        bad_cases=[
            ({**decision,'display_title_alias':'OCR variant '},consent,confirmation,ref),
            (decision,{**consent,'display_title_alias_confirmation_ref':{**ref,'path':bundle+'/other.json'}},confirmation,ref),
            (decision,consent,{**confirmation,'owner_statement':'同一群組'},ref),
            (decision,consent,{**confirmation,'project_root':'/other'},ref),
            (decision,consent,{**confirmation,'canonical_group_name':'other'},ref),
        ]
        for dec,con,doc,alias_ref in bad_cases:
            with self.subTest(doc=doc),self.assertRaises(AcceptanceError):
                cli.validate_one56_display_title_alias(dec,con,doc,task_id='PILOT-1',owner='owner-1',
                    root='/project',canonical_group='Canonical group',alias_ref=alias_ref)

    def test_bundle_artifact_requires_exact_hash_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            relative='harness-development/pilot/private/authority-bundles/ONE56-test/implementation-review.json'
            target=root/relative;target.parent.mkdir(parents=True);target.write_bytes(b'{"verdict":"PENDING"}')
            raw=target.read_bytes();ref={'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            reader=ProjectReader(str(root))
            try:
                self.assertEqual(artifact(reader,ref),raw)
                with self.assertRaises(AcceptanceError):
                    artifact(reader,{**ref,'sha256':'0'*64})
                with self.assertRaises(AcceptanceError):
                    artifact(reader,{**ref,'bytes':len(raw)+1})
            finally:
                reader.close()

    def test_contract_requires_active_open_owner_task_source_and_single_entry(self):
        grant={'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','source_sha256':'a'*64,
            'config_sha256':'b'*64,'entry_binding':{'sha256':'c'*64},
            'runtime_binding':{'sha256':'d'*64},'producer_binary':{'sha256':'e'*64}}
        contract={'status':'ACTIVE','closed':False,'task_id':'PILOT-1','owner':'owner-1','project_root':'/project',
            'source_sha256':'a'*64,'config_sha256':'b'*64,'entry_method':'runSingleAlbumPilot',
            'operations':sorted(cli.ONE56_REQUIRED_OPERATIONS),'entry_sha256':'c'*64,
            'runtime_binding_sha256':'d'*64,'producer_binary_sha256':'e'*64}
        cli.validate_one56_contract(contract,grant,'/project')
        for key,value in (('closed',True),('owner','foreign'),('task_id','PILOT-other'),
            ('source_sha256','f'*64),('entry_method','runTwoAlbumPilot'),
            ('operations',contract['operations']+['begin'])):
            with self.subTest(key=key):
                changed={**contract,key:value}
                with self.assertRaises(AcceptanceError):
                    cli.validate_one56_contract(changed,grant,'/project')

    def test_review_must_be_external_and_cover_exact_task_runtime_and_operation_scope(self):
        grant={'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','source_sha256':'a'*64,
            'config_sha256':'b'*64,
            'entry_binding':{'sha256':'c'*64},'runtime_binding':{'sha256':'d'*64},
            'producer_binary':{'sha256':'e'*64}}
        review={'profile':cli.PROJECT_SCOPE,'verdict':'APPROVE_IMPLEMENTATION',
            'review_method':'OWNER_TRANSFERRED_EXTERNAL_PR_REVIEW','reviewer':'External Chief',
            'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','source_sha256':'a'*64,
            'config_sha256':'b'*64,'implementation_head':'1'*40,
            'entry_method':'runSingleAlbumPilot','approved_operations':sorted(cli.ONE56_REQUIRED_OPERATIONS),
            'fingerprint':cli.ONE56_FINGERPRINT,'runtime_binding_sha256':'d'*64,
            'producer_binary_sha256':'e'*64,'disposition_ref':'review:123'}
        original={'verdict':'APPROVE_IMPLEMENTATION','reviewer':'External Chief','disposition_ref':'review:123',
            'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','config_sha256':'b'*64,
            'implementation_head':'1'*40,
            'source_sha256':'a'*64,
            'runtime_binding_sha256':'d'*64,'producer_binary_sha256':'e'*64,'entry_method':'runSingleAlbumPilot',
            'approved_operations':sorted(cli.ONE56_REQUIRED_OPERATIONS),'fingerprint':cli.ONE56_FINGERPRINT}
        cli.validate_one56_review(review,original,grant)
        for key,value in (('reviewer','Luna'),('task_id','PILOT-other'),('source_sha256','f'*64),
            ('entry_method','runTwoAlbumPilot'),('approved_operations',['gui_observe']),
            ('runtime_binding_sha256','0'*64),('producer_binary_sha256','0'*64),('disposition_ref','')):
            with self.subTest(key=key):
                with self.assertRaises(AcceptanceError):
                    cli.validate_one56_review({**review,key:value},original,grant)
        with self.assertRaises(AcceptanceError):
            cli.validate_one56_review(review,{**original,'source_sha256':'0'*64},grant)
        with self.assertRaises(AcceptanceError):
            cli.validate_one56_review(review,{**original,'verdict':'PENDING'},grant)

    def _synthetic_github_review(self):
        grant={'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','source_sha256':'a'*64,
            'config_sha256':'b'*64,'runtime_binding':{'sha256':'d'*64},
            'producer_binary':{'sha256':'e'*64},'entry_binding':{'sha256':'c'*64}}
        contract={'implementation_head':'1'*40}
        review_id=987654321
        raw={'id':review_id,
            'pull_request_url':cli.ONE56_PULL_REQUEST_API,
            'html_url':cli.ONE56_PULL_REQUEST_HTML+f'#pullrequestreview-{review_id}',
            'state':'APPROVED','user':{'login':'s9008129','id':129814822},'commit_id':'1'*40}
        scope={'decision':'APPROVE_IMPLEMENTATION','external_reviewer':'ChatGPT Chief',
            'task_id':'PILOT-1','owner':'owner-1','project_root':'/project','implementation_head':'1'*40,
            'source_sha256':'a'*64,'config_sha256':'b'*64,'runtime_binding_sha256':'d'*64,
            'producer_binary_sha256':'e'*64,'entry_sha256':'c'*64,'entry_method':'runSingleAlbumPilot',
            'approved_operations':sorted(cli.ONE56_REQUIRED_OPERATIONS),'fingerprint':cli.ONE56_FINGERPRINT}
        raw['body']='External Chief exact-source approval.\n<!-- ONE56_REVIEW_SCOPE_V1\n'+json.dumps(scope)+'\nONE56_REVIEW_SCOPE_END -->'
        wrapper={'provider_review_id':review_id,
            'provider_review_url':cli.ONE56_PROVIDER_REPOSITORY+f'/pulls/10/reviews/{review_id}',
            'pull_request_url':cli.ONE56_PULL_REQUEST_API,'pull_request_html_url':cli.ONE56_PULL_REQUEST_HTML,
            'provider_state':'APPROVED','provider_actor':'s9008129','implementation_head':'1'*40,
            'reviewer':'ChatGPT Chief','task_id':'PILOT-1','owner':'owner-1','project_root':'/project',
            'source_sha256':'a'*64,'config_sha256':'b'*64,'runtime_binding_sha256':'d'*64,
            'producer_binary_sha256':'e'*64,'entry_sha256':'c'*64,'disposition_ref':raw['html_url']}
        return raw,wrapper,contract,grant

    def test_synthetic_provider_review_must_match_actor_commit_urls_state_and_body_scope(self):
        raw,wrapper,contract,grant=self._synthetic_github_review()
        cli.validate_one56_provider_review(raw,wrapper,contract,grant)
        # Owner-transferred PR10 comments are the provider record for a Chief
        # approval; the machine-readable body, not GitHub's label, carries verdict.
        commented={**raw,'state':'COMMENTED'}
        cli.validate_one56_provider_review(commented,{**wrapper,'provider_state':'COMMENTED'},contract,grant)
        changed_cases=[
            ({**raw,'state':'COMMENTED'},wrapper,contract,grant),
            ({**raw,'state':'CHANGES_REQUESTED'},wrapper,contract,grant),
            ({**raw,'state':'DISMISSED'},wrapper,contract,grant),
            ({**raw,'state':'PENDING'},wrapper,contract,grant),
            ({**raw,'commit_id':'2'*40},wrapper,contract,grant),
            ({**raw,'user':{'login':'other','id':1}},wrapper,contract,grant),
            ({**raw,'pull_request_url':'https://github.com/other/repo/pull/10'},wrapper,contract,grant),
            ({**raw,'body':'Design review only'},wrapper,contract,grant),
        ]
        changed_cases.append((raw,{**wrapper,'disposition_ref':'review:unrelated'},contract,grant))
        design=dict(raw)
        scope=cli._one56_scope_from_body(raw['body']);scope['decision']='DESIGN_ONLY'
        design['body']='<!-- ONE56_REVIEW_SCOPE_V1\n'+json.dumps(scope)+'\nONE56_REVIEW_SCOPE_END -->'
        changed_cases.append((design,wrapper,contract,grant))
        stale_contract={**contract,'implementation_head':'2'*40}
        changed_cases.append((raw,wrapper,stale_contract,grant))
        for args in changed_cases:
            with self.subTest(raw_state=args[0].get('state'),raw_user=args[0].get('user')):
                with self.assertRaises(AcceptanceError):
                    cli.validate_one56_provider_review(*args)

    def test_one56_runtime_callback_membership_requires_all_exact_paths_and_roles(self):
        valid=[{'path':path,'roles':sorted(roles),'bytes':1,'sha256':'a'*64}
            for path,roles in cli.ONE56_CALLBACK_ROLES.items()]
        cli.validate_one56_callback_membership(valid)
        omitted=[item for item in valid if not item['path'].endswith('/mac_runtime.mjs')]
        replaced=[dict(item) for item in valid]
        replaced[0]['path']='harness-development/line-two-album-pilot-20261014/mac/other.mjs'
        wrong_roles=[dict(item) for item in valid]
        wrong_roles[0]['roles']=['cli_bridge']
        for candidate in (omitted,replaced,wrong_roles):
            with self.subTest(paths=[x['path'] for x in candidate]), self.assertRaises(AcceptanceError):
                cli.validate_one56_callback_membership(candidate)

    def test_second_lifecycle_refuses_inside_cas_guard_before_transform(self):
        empty=hashlib.sha256(b'').hexdigest()
        bundle='harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-test'
        grant={
            'grant_version':'line-two-album-project-grant-1','single_album_route':True,
            'owner_decision':{'path':bundle+'/owner-decision.json','bytes':0,'sha256':empty},
            'external_review':{'path':bundle+'/implementation-review.json','bytes':0,'sha256':empty},
            'live_readiness':{'path':bundle+'/live-readiness.json','bytes':0,'sha256':empty},
            'runtime_binding':{'path':bundle+'/runtime-binding.json','bytes':0,'sha256':empty},
            'producer_binary':{'path':'producer','bytes':0,'sha256':empty},
            'decoder_binding':{'path':'decoder','bytes':0,'sha256':empty},
            'entry_binding':{'path':'entry','bytes':0,'sha256':empty},
            'contract_path':bundle+'/project-contract.json',
            'contract_sha256':empty,
        }
        grant_raw=json.dumps(grant).encode()

        class Reader:
            def read(self,path,*_args):
                return (grant_raw if path=='harness-development/test/project-grant.json' else b'',None)

        @contextlib.contextmanager
        def guarded():
            yield Reader(),None,lambda:None,[]

        instance=store.Store.__new__(store.Store)
        instance.root='/tmp/project'
        instance.authorization_path='harness-development/test/project-grant.json'
        instance.fixture=False
        instance.load=lambda _reader:({}, {'schema_version':3}, {'revision':0}, b'{}', [])
        instance.guard=guarded
        transform_called=[]
        expected={'revision':0}
        with patch('line_backup_batch.cli.authorize',return_value=grant), \
             patch.object(instance,'_ledger_open',return_value=('ledger',{
                 'workflow_phase':'A','lifecycle_count':1,'failure_latched':False,'entries':[]},23)):
            with self.assertRaises(AcceptanceError) as caught:
                instance._update(expected,lambda *_:transform_called.append(True),operation='begin')
        self.assertEqual(caught.exception.code,'ONE56_LIFECYCLE_ALREADY_USED')
        self.assertEqual(transform_called,[])

    def test_one56_admission_rejects_every_other_fingerprint(self):
        instance=service.Service.__new__(service.Service)
        instance.owner='owner'
        grant={'grant_version':'line-two-album-project-grant-1','single_album_route':True,'owner':'owner'}
        instance._project_grant=lambda:grant
        wrong={'start_date':'2024-06-02','end_date':'2024-06-07','expected_images':65}
        with self.assertRaises(AcceptanceError) as caught:
            instance._validate_bounded_lifecycle(None,{}, {},wrong,None)
        self.assertEqual(caught.exception.code,'ONE56_TARGET_MISMATCH')


class HumanCliRoutingTests(unittest.TestCase):
    def setUp(self):
        _HumanCliRecordingService.instances=[]
        _HumanCliSilentStore.instances=[]
        _HumanCliInspectStore.instances=[]

    def execute(self,grant,operation,data,store=_HumanCliSilentStore):
        payload={'expected_token':_human_cli_token(_human_cli_receipt(grant)),'data':data}
        with patch.object(cli,'authorize',return_value=grant) as authorize, \
                patch.object(cli,'load_input',return_value=payload), \
                patch.object(cli,'Store',store), \
                patch.object(cli,'Service',_HumanCliRecordingService):
            result=cli.execute(_human_cli_namespace(operation))
        return result,authorize,_HumanCliRecordingService.instances[-1] \
            if _HumanCliRecordingService.instances else None

    def test_human_operations_route_only_to_dedicated_service_methods(self):
        grant=_human_cli_grant();binding=_human_cli_binding(grant)
        readiness={'status':'OBSERVED','raw_evidence_refs':[_human_cli_evidence_ref('readiness')]}
        begin={'batch_id':'BATCH-1'};admitted={'status':'ADMITTED_BOUNDED_CANDIDATE'}
        request={'request_id':'REQUEST-CARD'};result={'result_id':'RESULT-CARD'}
        evidence={'status':'OBSERVED'};cal=_human_cli_calibration(grant)
        request_ref=_human_cli_evidence_ref('request');result_ref=_human_cli_evidence_ref('result')
        intent={'action_id':'ACTION-1'};intent_readback={'action_id':'ACTION-1','durable':True}
        save_all={'stage':'SAVE_ALL'};chooser_path={'stage':'CHOOSER_PATH'}
        chooser_confirm={'stage':'CHOOSER_CONFIRM'}
        chooser_readback={'reference':_human_cli_evidence_ref('chooser-readback')}
        cases=[
            ('begin',{'binding':binding,'ledger':{'status':'INITIALIZED'},'readiness':readiness},
                'human_begin',(_human_cli_receipt(grant),binding,readiness)),
            ('admit',{'binding':binding,'readiness':readiness,'begin':begin},
                'human_admit',(_human_cli_receipt(grant),binding,readiness,begin)),
            ('prepare',{'binding':binding,'readiness':readiness,'begin':begin,'admitted':admitted},
                'human_prepare',(_human_cli_receipt(grant),binding,readiness,begin,admitted)),
            ('calibrate',{'binding':binding,'run_id':'RUN-1','request':request,'result':result,
                'evidence':evidence,'calibration':cal,'request_ref':request_ref,'result_ref':result_ref},
                'human_commit_calibration',(_human_cli_receipt(grant),binding,'RUN-1',request,result,
                    evidence,cal,request_ref,result_ref)),
            ('intent',{'binding':binding,'run_id':'RUN-1','calibration':cal,'fresh_evidence':evidence},
                'human_commit_intent',(_human_cli_receipt(grant),binding,'RUN-1',cal,evidence)),
            ('dispatch',{'binding':binding,'run_id':'RUN-1','intent':intent,
                'intent_readback':intent_readback,'save_all':save_all,'chooser_path':chooser_path,
                'chooser_confirm':chooser_confirm,'chooser_readback':chooser_readback},
                'human_record_dispatch',(_human_cli_receipt(grant),binding,'RUN-1',intent,
                    intent_readback,save_all,chooser_path,chooser_confirm,chooser_readback)),
            ('finalize',{'binding':binding,'run_id':'RUN-1','decoder':grant['decoder_binding']['path'],
                'decoder_sha256':grant['decoder_binding']['sha256']},
                'human_finalize',(_human_cli_receipt(grant),binding,'RUN-1',
                    grant['decoder_binding']['path'],grant['decoder_binding']['sha256'])),
            ('stop',{'binding':binding,'run_id':'RUN-1','reason':'VERIFIED_HUMAN_ASSISTED_SINGLE_ALBUM'},
                'human_stop',(_human_cli_receipt(grant),binding,'RUN-1',
                    'VERIFIED_HUMAN_ASSISTED_SINGLE_ALBUM')),
            ('release',{'binding':binding,'run_id':'RUN-1'},
                'human_release',(_human_cli_receipt(grant),binding,'RUN-1')),
        ]
        for operation,data,method,expected_args in cases:
            with self.subTest(operation=operation):
                payload={'expected_token':_human_cli_token(_human_cli_receipt(grant)),'data':data}
                with patch.object(cli,'authorize',return_value=grant), \
                        patch.object(cli,'load_input',return_value=payload), \
                        patch.object(cli,'Store',_HumanCliSilentStore), \
                        patch.object(cli,'Service',_HumanCliRecordingService):
                    routed=cli.execute(_human_cli_namespace(operation))
                routed_service=_HumanCliRecordingService.instances[-1]
                self.assertEqual(routed_service.calls,[(method,expected_args,{})])
                self.assertEqual(routed['method'],method)
                self.assertFalse(any(name in ('dispatch','begin','admit','prepare','calibrate','intent',
                    'finalize','stop','release') for name,_,_ in routed_service.calls))

    def test_human_calibrate_without_explicit_calibration_fails_closed_before_service(self):
        grant=_human_cli_grant();binding=_human_cli_binding(grant)
        request={'request_id':'REQUEST-CAL'};result={'result_id':'RESULT-CAL'}
        evidence={'status':'OBSERVED','raw_evidence_refs':[_human_cli_evidence_ref('one')]}
        data={'binding':binding,'run_id':'RUN-1','request':request,'result':result,
            'evidence':evidence,'request_ref':_human_cli_evidence_ref('request'),
            'result_ref':_human_cli_evidence_ref('result')}
        payload={'expected_token':_human_cli_token(_human_cli_receipt(grant)),'data':data}
        with patch.object(cli,'authorize',return_value=grant), \
                patch.object(cli,'load_input',return_value=payload), \
                patch.object(cli,'Store',_HumanCliSilentStore), \
                patch.object(cli,'Service',_HumanCliRecordingService):
            with self.assertRaises(AcceptanceError) as caught:
                cli.execute(_human_cli_namespace('calibrate'))
        self.assertEqual(caught.exception.code,'HUMAN_CALIBRATION_REQUIRED')
        self.assertEqual(_HumanCliRecordingService.instances[-1].calls,[])

    def test_auto_operations_keep_existing_service_routes(self):
        grant={'owner':'owner-1','source_sha256':'a'*64,'config_sha256':'b'*64,'artifact_dir':'artifacts'}
        receipt_value=_human_cli_receipt(grant)
        cases=[
            ('begin',{'mode':'backup_batch','limit':2},'begin',(receipt_value,'backup_batch',2)),
            ('admit',{'records':[{'record':1}],'session':'session'},'admit',
                (receipt_value,[{'record':1}],'session')),
            ('prepare',{'observation':{'observation':1}},'prepare',(receipt_value,{'observation':1})),
            ('calibrate',{'detail':{'detail':1},'calibration':{'calibration':1},'menu':{'menu':1},
                'closure':{'closure':1}},'calibrate',(receipt_value,{'detail':1},{'calibration':1},
                    {'menu':1},{'closure':1})),
            ('intent',{'fresh':{'fresh':1}},'intent',(receipt_value,{'fresh':1})),
            ('dispatch',{'evidence':{'evidence':1},'chooser':{'chooser':1},'download_started':True,
                'receipt':{'receipt':1}},'dispatch',(receipt_value,{'evidence':1},{'chooser':1},True,
                    {'receipt':1})),
            ('finalize',{'decoder':'decoder','decoder_sha256':'d'*64},'finalize',
                (receipt_value,'decoder','d'*64)),
            ('stop',{'reason':'STOPPED'},'stop',(receipt_value,'STOPPED')),
            ('release',{},'release',(receipt_value,)),
        ]
        for operation,data,method,expected_args in cases:
            with self.subTest(operation=operation):
                _HumanCliRecordingService.instances=[]
                routed,_,routed_service=self.execute(grant,operation,data)
                self.assertEqual(routed_service.calls,[(method,expected_args,{})])
                self.assertEqual(routed['method'],method)
                self.assertFalse(any(name.startswith('human_') for name,_,_ in routed_service.calls))

    def test_partial_human_grant_and_mixed_payloads_fail_before_service_calls(self):
        grant=_human_cli_grant();binding=_human_cli_binding(grant)
        with patch.object(cli,'authorize',return_value={'execution_mode':cli.HUMAN_EXECUTION_MODE}), \
                patch.object(cli,'load_input',return_value={}), \
                patch.object(cli,'Store',_HumanCliSilentStore), \
                patch.object(cli,'Service',_HumanCliRecordingService):
            with self.assertRaises(AcceptanceError) as caught:
                cli.execute(_human_cli_namespace('begin'))
        self.assertEqual(caught.exception.code,'HUMAN_GRANT_BINDING')
        self.assertFalse(_HumanCliRecordingService.instances)

        auto_grant={'grant_version':cli.ONE56_GRANT_VERSION,'single_album_route':True,
            'project_root':HUMAN_CLI_PROJECT_ROOT,'source_sha256':'a'*64,'config_sha256':'b'*64,
            'owner':'owner-1','artifact_dir':'harness-development/test/private'}
        with self.assertRaises(AcceptanceError) as caught:
            self.execute(auto_grant,'begin',{'binding':binding})
        self.assertEqual(caught.exception.code,'ONE56_MODE_MIXED')

        with self.assertRaises(AcceptanceError) as caught:
            self.execute(_human_cli_grant(),'dispatch',{'binding':binding,'run_id':'RUN-1',
                'intent':{'action_id':'ACTION-1'},'save_all':{'stage':'SAVE_ALL'},
                'chooser_path':{'stage':'CHOOSER_PATH'},'chooser_confirm':{'stage':'CHOOSER_CONFIRM'},
                'receipt':{'auto':True}})
        self.assertEqual(caught.exception.code,'ONE56_MODE_MIXED')

    def test_human_binding_is_exact_and_canonical_before_service_dispatch(self):
        grant=_human_cli_grant();binding=_human_cli_binding(grant)
        invalid=[
            (None,'HUMAN_INPUT_BINDING_REQUIRED'),
            ({'destination':binding['destination'],'grant_sha256':binding['grant_sha256'],
                'observer_session_id':binding['observer_session_id'],'source_sha256':binding['source_sha256']},
             'HUMAN_INPUT_BINDING_REQUIRED'),
            (dict(binding,destination='relative/album-a56'),'HUMAN_INPUT_BINDING'),
            (dict(binding,destination=binding['destination']+'/'),'HUMAN_INPUT_BINDING'),
            (dict(binding,task_id='PILOT-foreign'),'HUMAN_INPUT_BINDING'),
            (dict(binding,source_sha256='0'*64),'HUMAN_INPUT_BINDING'),
            (dict(binding,observer_session_id='foreign-session'),'ONE56_MODE_MIXED'),
            (dict(binding,extra='field'),'HUMAN_INPUT_BINDING_REQUIRED'),
        ]
        for candidate,code in invalid:
            with self.subTest(code=code,candidate=candidate):
                _HumanCliRecordingService.instances=[]
                data={'run_id':'RUN-1','reason':'STOPPED'}
                if candidate is not None:data['binding']=candidate
                with self.assertRaises(AcceptanceError) as caught:
                    self.execute(grant,'stop',data)
                self.assertEqual(caught.exception.code,code)
                self.assertEqual(_HumanCliRecordingService.instances[-1].calls,[])

    def test_human_dispatch_never_uses_auto_dispatch_or_receipt_path(self):
        grant=_human_cli_grant();binding=_human_cli_binding(grant)
        data={'binding':binding,'run_id':'RUN-1','intent':{'action_id':'ACTION-1'},
            'intent_readback':{'action_id':'ACTION-1'},'save_all':{'stage':'SAVE_ALL'},
            'chooser_path':{'stage':'CHOOSER_PATH'},'chooser_confirm':{'stage':'CHOOSER_CONFIRM'},
            'chooser_readback':{'reference':_human_cli_evidence_ref('chooser-readback')}}
        _,_,routed_service=self.execute(grant,'dispatch',data)
        self.assertEqual(len(routed_service.calls),1)
        self.assertEqual(routed_service.calls[0][0],'human_record_dispatch')
        self.assertNotIn('dispatch',[name for name,_,_ in routed_service.calls])

    def test_inspect_human_reads_route_to_read_only_store_fact_methods(self):
        grant=_human_cli_grant()
        _HumanCliInspectStore.snapshot_value={'state':{'schema_version':3,'revision':1,
            'active_batch':None,'active_writer_id':None,'verified_albums':[]},
            'receipt':_human_cli_receipt(grant),'config':{'group_key':'group'}}
        cases=[
            ({'kind':'reservation','reservation_id':'RES-1'},'human_reservation_fact','reservation-fact',
                (grant,'RES-1')),
            ({'kind':'intent','run_id':'RUN-1','action_id':'ACTION-1'},'human_intent_fact','intent-fact',
                (grant,'RUN-1','ACTION-1')),
            ({'kind':'verified','run_id':'RUN-1'},'human_verified_fact','verified-fact',(grant,'RUN-1')),
        ]
        for selector,method,fact_kind,args in cases:
            with self.subTest(kind=selector['kind']):
                _HumanCliInspectStore.instances=[];_HumanCliRecordingService.instances=[]
                payload={'expected_token':_human_cli_token(_human_cli_receipt(grant)),
                    'data':{'human_read':selector}}
                with patch.object(cli,'authorize',return_value=grant) as authorize, \
                        patch.object(cli,'load_input',return_value=payload), \
                        patch.object(cli,'Store',_HumanCliInspectStore), \
                        patch.object(cli,'Service',_HumanCliRecordingService):
                    routed=cli.execute(_human_cli_namespace('inspect'))
                inspect_store=_HumanCliInspectStore.instances[-1]
                self.assertEqual(inspect_store.calls,[(method,args)])
                self.assertEqual(routed['human_read'],{'kind':fact_kind,'args':args})
                self.assertEqual(inspect_store.snapshot_calls,1)
                self.assertFalse(_HumanCliRecordingService.instances)
                authorize.assert_called_once_with(HUMAN_CLI_PROJECT_ROOT,HUMAN_CLI_AUTHORIZATION,
                    False,'gui_observe')

    def test_inspect_read_selectors_and_authority_fail_closed_without_store_reads(self):
        grant=_human_cli_grant()
        _HumanCliInspectStore.snapshot_value={'state':{'schema_version':3,'revision':1,
            'active_batch':None,'active_writer_id':None,'verified_albums':[]},
            'receipt':_human_cli_receipt(grant),'config':{}}
        bad_selectors=[
            {'kind':'reservation','reservation_id':'RES-1','extra':True},
            {'kind':'intent','run_id':'RUN-1'},
            {'kind':'verified','run_id':''},
            {'kind':'unknown','run_id':'RUN-1'},
            None,
        ]
        for selector in bad_selectors:
            with self.subTest(selector=selector):
                _HumanCliInspectStore.instances=[]
                payload={'expected_token':_human_cli_token(_human_cli_receipt(grant)),
                    'data':{'human_read':selector}}
                with patch.object(cli,'authorize',return_value=grant) as authorize, \
                        patch.object(cli,'load_input',return_value=payload), \
                        patch.object(cli,'Store',_HumanCliInspectStore), \
                        patch.object(cli,'Service',_HumanCliRecordingService):
                    with self.assertRaises(AcceptanceError) as caught:
                        cli.execute(_human_cli_namespace('inspect'))
                self.assertEqual(caught.exception.code,'HUMAN_READ_SELECTOR')
                self.assertEqual(_HumanCliInspectStore.instances[-1].calls,[])
                authorize.assert_not_called()

        payload={'expected_token':_human_cli_token({'project_root':'/foreign',
            'config_sha256':grant['config_sha256'],'source_sha256':grant['source_sha256']}),
            'data':{'human_read':{'kind':'verified','run_id':'RUN-1'}}}
        with patch.object(cli,'authorize',return_value=grant), \
                patch.object(cli,'load_input',return_value=payload), \
                patch.object(cli,'Store',_HumanCliInspectStore), \
                patch.object(cli,'Service',_HumanCliRecordingService):
            with self.assertRaises(AcceptanceError) as caught:
                cli.execute(_human_cli_namespace('inspect'))
        self.assertEqual(caught.exception.code,'REQUEST_AUTHORITY_MISMATCH')
        self.assertEqual(_HumanCliInspectStore.instances[-1].calls,[])

        auto_grant={'source_sha256':'a'*64,'config_sha256':'b'*64}
        payload={'expected_token':_human_cli_token(_human_cli_receipt(auto_grant)),
            'data':{'human_read':{'kind':'verified','run_id':'RUN-1'}}}
        with patch.object(cli,'authorize',return_value=auto_grant), \
                patch.object(cli,'load_input',return_value=payload), \
                patch.object(cli,'Store',_HumanCliInspectStore), \
                patch.object(cli,'Service',_HumanCliRecordingService):
            with self.assertRaises(AcceptanceError) as caught:
                cli.execute(_human_cli_namespace('inspect'))
        self.assertEqual(caught.exception.code,'ONE56_MODE_MIXED')
        self.assertEqual(_HumanCliInspectStore.instances[-1].calls,[])


if __name__=='__main__':
    unittest.main()
