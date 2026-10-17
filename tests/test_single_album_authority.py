import contextlib
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.project_binding import ProjectReader
from line_backup_batch import cli, store, service
from line_backup_batch.observations import artifact


class One56AuthorityTests(unittest.TestCase):
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


if __name__=='__main__':
    unittest.main()
