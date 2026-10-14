"""Public canonical entry. Fixture authority never admits the live project."""
import argparse
import base64
import json
import os
from pathlib import Path
import stat
import sys
from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.project_binding import ProjectReader,strict_json,sha
from .schema import require
from .store import Store
from .service import Service

GRANT_V1_KEYS={
    'grant_version','task_id','project_root','fixture','artifact_dir','owner','operations',
    'config_sha256','source_sha256','album_quota','lifecycle_album_limit','save_all_dispatch_limit',
    'chooser_confirmation_limit','reversible_gui_invocation_limit',
    'authorization_evidence','acceptance_evidence',
    'contract_sha256','native_binary_sha256','gui_ledger'
}
GRANT_V2_KEYS=GRANT_V1_KEYS|{'contract_path','producer_binary','runtime_binding','sensor_scope'}
PROJECT_GRANT_KEYS={
    'grant_version','task_id','project_root','fixture','artifact_dir','owner','operations',
    'config_sha256','source_sha256','album_quota','lifecycle_album_limit','save_all_dispatch_limit',
    'chooser_confirmation_limit','reversible_gui_invocation_limit','contract_path','contract_sha256',
    'native_binary_sha256','gui_ledger','producer_binary','runtime_binding','sensor_scope',
    'project_profile','owner_decision','external_review','live_readiness','decoder_binding','entry_binding'
}
PROJECT_SCOPE='LINE_TWO_ALBUM_PILOT/1'
PROJECT_DIR='harness-development/line-two-album-pilot-20261014'
PROJECT_OPERATIONS={'begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','release','resume',
    'gui_reserve','gui_consume','gui_initialize','gui_phase','gui_observe'}
PROJECT_MUTATING={'begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','release','gui_reserve','gui_consume','gui_initialize','gui_phase','gui_observe'}
OPERATIONS={'migrate','begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','finish','release','resume',
    'gui_reserve','gui_consume','gui_initialize','gui_phase','gui_observe','frame_support'}
CONTRACT_PATH='harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/controller/TASK-4acb4326ea2a4c50ace6f333f2de8751/plan-contract.json'
CONTRACT_SHA256='a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc'
NATIVE_BINARY_PATH='harness-development/line-v3-live-e2e-20261010/bin/image_decode'
NATIVE_BINARY_SHA256='1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf'
GUI_LEDGER_PATH='harness-development/line-v3-live-e2e-20261010/gui-ledger.json'
CONTINUATION='harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08'

def load_input(root,path):
    require(isinstance(path,str) and path.startswith('harness-development/'),'UNSAFE_INPUT_PATH')
    reader=ProjectReader(root)
    try:raw,_=reader.read(path)
    finally:reader.close()
    return strict_json(raw,'INVALID_INPUT')

def _swift_source_members(reader,root):
    result=[]
    def visit(directory):
        for name in reader.directory_names(directory):
            path=f'{directory}/{name}'
            try:
                reader.directory_names(path)
            except (AcceptanceError,NotADirectoryError):
                if path.endswith('.swift'):result.append(path)
            else:visit(path)
    for directory in ('rev28/Sources/Rev28Core','rev28/Sources/rev28ctl'):
        visit(directory)
    return sorted(result)

def validate_runtime_binding(reader,grant):
    """Verify the complete frozen task source closure before live authority is used."""
    from .observations import artifact
    from .store import SOURCE_PATHS
    ref=grant.get('runtime_binding')
    require(isinstance(ref,dict) and set(ref)=={'path','bytes','sha256'}
        and ref.get('path')==CONTINUATION+'/runtime-binding.json','RUNTIME_BINDING_REQUIRED')
    raw=artifact(reader,ref)
    manifest=strict_json(raw,'INVALID_RUNTIME_BINDING')
    require(isinstance(manifest,dict) and set(manifest)=={'version','task_id','project_root','contract_path',
        'contract_sha256','source_sha256','memberships','files'} and manifest.get('version')==1
        and manifest.get('task_id')==grant['task_id'] and manifest.get('project_root')==grant['project_root']
        and manifest.get('contract_path')==CONTRACT_PATH and manifest.get('contract_sha256')==CONTRACT_SHA256
        and manifest.get('source_sha256')==grant['source_sha256'],'RUNTIME_BINDING_MISMATCH')
    binary=grant.get('producer_binary')
    require(isinstance(binary,dict) and set(binary)=={'path','bytes','sha256'}
        and binary.get('path')==CONTINUATION+'/bin/rev28ctl','PRODUCER_BINARY_BINDING')
    binary_path=Path(reader.root,binary['path']).resolve(strict=True)
    require(binary_path.is_file() and os.access(binary_path,os.X_OK),'PRODUCER_BINARY_UNAVAILABLE')
    python_path=Path(sys.executable).resolve(strict=True)
    memberships={
        'product_sources_21':sorted(SOURCE_PATHS),
        'task_modules':sorted([*SOURCE_PATHS[-1:],CONTINUATION+'/host_io.mjs',
            CONTINUATION+'/live_analyzer.mjs',CONTINUATION+'/live_classifier.mjs',
            CONTINUATION+'/live_runner.mjs',CONTINUATION+'/live_entry.mjs',
            CONTINUATION+'/chooser_locators.mjs',CONTINUATION+'/tools/retain_payload.py',
            CONTINUATION+'/tools/host_process.py',CONTINUATION+'/checks/validate_real_frame.py']),
        'swift_sources':_swift_source_members(reader,reader.root),
        'package_manifest':['rev28/Package.swift'],
        'python_runtime':[str(python_path)],
        'producer_binary':[binary['path']],
    }
    require(isinstance(manifest.get('memberships'),dict)
        and manifest['memberships']==memberships,'RUNTIME_MEMBERSHIP_DRIFT')
    expected={}
    for group,paths in memberships.items():
        for path in paths:expected.setdefault(path,set()).add(group)
    files=manifest.get('files')
    require(isinstance(files,list) and files,'RUNTIME_FILES_REQUIRED')
    actual={}
    for entry in files:
        require(isinstance(entry,dict) and set(entry)=={'path','bytes','sha256','member_of'}
            and isinstance(entry.get('path'),str) and type(entry.get('bytes')) is int and entry['bytes']>0
            and isinstance(entry.get('sha256'),str) and len(entry['sha256'])==64
            and isinstance(entry.get('member_of'),list),'RUNTIME_FILE_ENTRY')
        path=entry['path'];require(path not in actual,'RUNTIME_DUPLICATE_PATH')
        require(set(entry['member_of'])==expected.get(path,set()),'RUNTIME_FILE_MEMBERSHIP')
        if path.startswith('/'):
            resolved=Path(path).resolve(strict=True)
            require(path==str(resolved) and resolved.is_file(),'RUNTIME_EXTERNAL_PATH')
            data=resolved.read_bytes()
        else:
            require(path in expected,'RUNTIME_UNEXPECTED_PATH')
            data,_=reader.read(path,'RUNTIME_FILE_UNAVAILABLE')
        require(len(data)==entry['bytes'] and sha(data)==entry['sha256'],'RUNTIME_FILE_DRIFT')
        actual[path]=entry
    require(set(actual)==set(expected),'RUNTIME_CLOSURE_INCOMPLETE')
    require(actual[binary['path']]['bytes']==binary['bytes'] and actual[binary['path']]['sha256']==binary['sha256'],
        'PRODUCER_BINARY_DRIFT')
    require(sha(binary_path.read_bytes())==binary['sha256'],'PRODUCER_BINARY_DRIFT')
    require(str(python_path) in actual,'PYTHON_RUNTIME_DRIFT')
    return manifest

def authorize(root,path,fixture,operation):
    grant=load_input(root,path)
    if isinstance(grant,dict) and grant.get('grant_version')=='line-two-album-project-grant-1':
        return authorize_project(root,path,grant,fixture,operation)
    expected_keys=GRANT_V1_KEYS if fixture else GRANT_V2_KEYS
    expected_version='line-batch-execution-grant-1' if fixture else 'line-batch-execution-grant-2'
    require(isinstance(grant,dict) and set(grant)==expected_keys and grant['grant_version']==expected_version,'INVALID_GRANT')
    require(isinstance(grant.get('operations'),list),'GRANT_OPERATIONS')
    require(grant['project_root']==root and grant['fixture'] is fixture and operation in grant['operations'],'GRANT_SCOPE')
    require(isinstance(grant['task_id'],str) and grant['task_id'].startswith('TASK-')
        and isinstance(grant['owner'],str) and grant['owner'] and isinstance(grant['artifact_dir'],str),
        'GRANT_SCOPE')
    if fixture:
        require(grant['artifact_dir']=='harness-development/evidence','GRANT_SCOPE')
    else:
        require(grant['artifact_dir']==CONTINUATION,'GRANT_SCOPE')
    require(isinstance(grant['operations'],list) and len(grant['operations'])==len(set(grant['operations']))
        and set(grant['operations'])<=OPERATIONS and 'mutate' not in grant['operations'],'GRANT_OPERATIONS')
    for field in ('config_sha256','source_sha256'):
        require(isinstance(grant[field],str) and len(grant[field])==64
            and all(c in '0123456789abcdef' for c in grant[field]),'GRANT_AUTHORITY')
    for field in ('album_quota','lifecycle_album_limit','save_all_dispatch_limit','chooser_confirmation_limit','reversible_gui_invocation_limit'):
        require(type(grant[field]) is int and grant[field]>=0,'GRANT_QUOTA')
    installed=Path(__file__).resolve().parents[2]
    if fixture:
        require(Path(root).is_relative_to(installed/'harness-development') and '/fixtures/' in root and root!=str(installed),
            'FIXTURE_ROOT_REQUIRED')
        require(grant['authorization_evidence'] is None and grant['acceptance_evidence'] is None
            and grant['contract_sha256'] is None and grant['native_binary_sha256'] is None and grant['gui_ledger'] is None
            and all(grant[k]==0 for k in ('album_quota','lifecycle_album_limit','save_all_dispatch_limit','chooser_confirmation_limit',
                'reversible_gui_invocation_limit')),'FIXTURE_PRODUCTION_CREDENTIALS')
        require(set(grant['operations'])<= {'migrate','begin','resume'},'FIXTURE_LIVE_OPERATION_REFUSED')
    else:
        require(root==str(installed),'SELECTED_ROOT_REQUIRED')
        reader=ProjectReader(root)
        try:
            from .observations import artifact
            require(grant['contract_path']==CONTRACT_PATH and grant['contract_sha256']==CONTRACT_SHA256
                and grant['native_binary_sha256']==NATIVE_BINARY_SHA256 and grant['gui_ledger']==GUI_LEDGER_PATH,
                'GRANT_LIVE_BINDING_REQUIRED')
            contract_raw,_=reader.read(CONTRACT_PATH,'GRANT_CONTRACT_DRIFT')
            require(sha(contract_raw)==CONTRACT_SHA256,'GRANT_CONTRACT_DRIFT')
            binary_raw,_=reader.read(NATIVE_BINARY_PATH,'GRANT_BINARY_DRIFT')
            require(sha(binary_raw)==NATIVE_BINARY_SHA256,'GRANT_BINARY_DRIFT')
            require({'gui_reserve','gui_consume'}<=set(grant['operations']),'GRANT_GUI_LEDGER_REQUIRED')
            scope={'bundle_id':'jp.naver.line.mac','provider':'SCREEN_CAPTURE_KIT','capture_scope':'FULL_DISPLAY',
                'surfaces':['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'],'menu_capture_guard':True}
            require(grant.get('sensor_scope')==scope,'GRANT_SENSOR_SCOPE')
            validate_runtime_binding(reader,grant)
            producer=grant.get('producer_binary')
            require(isinstance(producer,dict) and set(producer)=={'path','bytes','sha256'}
                and producer.get('path')==CONTINUATION+'/bin/rev28ctl' and type(producer.get('bytes')) is int
                and producer['bytes']>0 and isinstance(producer.get('sha256'),str)
                and len(producer['sha256'])==64,'PRODUCER_BINARY_BINDING')
            producer_path=Path(root,producer['path']).resolve(strict=True)
            require(producer_path.is_file() and os.access(producer_path,os.X_OK)
                and producer_path.stat().st_size==producer['bytes'] and sha(producer_path.read_bytes())==producer['sha256'],
                'PRODUCER_BINARY_DRIFT')
            auth_ref=grant['authorization_evidence']
            require(isinstance(auth_ref,dict) and auth_ref.get('path')==CONTINUATION+'/authorization.json',
                'AUTHORIZATION_EVIDENCE_REQUIRED')
            authorization=strict_json(artifact(reader,auth_ref),'INVALID_AUTHORIZATION_EVIDENCE')
            auth_keys={'format_version','task_id','project_root','artifact_dir','contract_path','contract_sha256',
                'source_sha256','config_sha256','authorized_owners','decision_code','decision_ref','plan_review_decision',
                'plan_review_waiver_ref','sensor_scope','album_quota','config_albums_per_lifecycle',
                'save_all_dispatch_cap','chooser_confirmation_cap','additional_reversible_gui_invocation_cap',
                'independent_acceptance_required'}
            require(isinstance(authorization,dict) and set(authorization)==auth_keys
                and authorization.get('format_version')=='3' and authorization.get('task_id')==grant['task_id']
                and authorization.get('project_root')==root and authorization.get('artifact_dir')==CONTINUATION
                and grant['artifact_dir']==authorization.get('artifact_dir')
                and authorization.get('contract_path')==CONTRACT_PATH and authorization.get('contract_sha256')==CONTRACT_SHA256
                and authorization.get('source_sha256')==grant['source_sha256']
                and authorization.get('config_sha256')==grant['config_sha256']
                and isinstance(authorization.get('authorized_owners'),list)
                and len(authorization['authorized_owners'])==2
                and all(isinstance(owner,str) and owner for owner in authorization['authorized_owners'])
                and len(set(authorization['authorized_owners']))==2,
                'AUTHORIZATION_SCOPE_MISMATCH')
            grant_slot={CONTINUATION+'/live-grant-1.json':0,CONTINUATION+'/live-grant-2.json':1}.get(path)
            require(grant_slot is not None and grant['owner']==authorization['authorized_owners'][grant_slot],
                'GRANT_OWNER_SLOT_MISMATCH')
            require(authorization.get('decision_code')=='A'
                and authorization.get('plan_review_decision')=='USER_WAIVED_NOT_RUN'
                and authorization.get('sensor_scope')==scope
                and authorization.get('album_quota')==grant['album_quota']
                and authorization.get('save_all_dispatch_cap')==grant['save_all_dispatch_limit']
                and authorization.get('chooser_confirmation_cap')==grant['chooser_confirmation_limit']
                and authorization.get('additional_reversible_gui_invocation_cap')==grant['reversible_gui_invocation_limit']
                and authorization.get('config_albums_per_lifecycle')==grant['lifecycle_album_limit']==1
                and authorization.get('independent_acceptance_required') is True,
                'AUTHORIZATION_SCOPE_MISMATCH')
            require(grant['album_quota']==2 and grant['lifecycle_album_limit']==1 and grant['save_all_dispatch_limit']==2
                and grant['chooser_confirmation_limit']==2 and grant['reversible_gui_invocation_limit']==1000,
                'GRANT_QUOTA_MISMATCH')
            decision_ref=authorization['decision_ref']
            require(isinstance(decision_ref,dict) and decision_ref.get('path')==
                'harness-development/line-v3-live-e2e-20261010/continuations/implement-02/user-decision-A.json',
                'USER_DECISION_REQUIRED')
            decision=strict_json(artifact(reader,decision_ref),'INVALID_USER_DECISION')
            require(decision.get('task_id')==grant['task_id'] and decision.get('decision',{}).get('id')=='A'
                and decision.get('decision',{}).get('decided_by')=='user','USER_DECISION_MISMATCH')
            waiver_ref=authorization['plan_review_waiver_ref']
            require(isinstance(waiver_ref,dict) and waiver_ref.get('path')==CONTINUATION+'/plan-review-waiver.json',
                'PLAN_REVIEW_WAIVER_REQUIRED')
            waiver=strict_json(artifact(reader,waiver_ref),'INVALID_PLAN_REVIEW_WAIVER')
            require(waiver.get('task_id')==grant['task_id'] and waiver.get('gate_id')=='G_PLAN_REVIEW_WAIVER'
                and waiver.get('contract_sha256')==CONTRACT_SHA256 and waiver.get('decision')=='WAIVE_GATE'
                and waiver.get('authority')=='USER','PLAN_REVIEW_WAIVER_MISMATCH')
            acceptance_ref=grant['acceptance_evidence']
            if acceptance_ref is not None:
                require(isinstance(acceptance_ref,dict)
                    and acceptance_ref.get('path')==CONTINUATION+'/acceptance.result.json','FOREIGN_ACCEPTANCE')
                accepted=strict_json(artifact(reader,acceptance_ref),'INVALID_ACCEPTANCE')
                require(accepted.get('role')=='ACCEPTANCE_REVIEWER'
                    and accepted.get('statuses',{}).get('INDEPENDENT_ACCEPTANCE_STATUS')=='PASS','ACCEPTANCE_REQUIRED')
                passed={g.get('gate_id') for g in accepted.get('gate_results',[]) if g.get('verdict')=='PASS'}
                require('G_ACCEPTANCE' in passed,'ACCEPTANCE_GATES_MISSING')
        finally:reader.close()
    snap=Store(root).snapshot()
    require(snap['receipt']['config_sha256']==grant['config_sha256'] and snap['receipt']['source_sha256']==grant['source_sha256'],
        'GRANT_AUTHORITY_DRIFT')
    return grant

def authorize_project(root,path,grant,fixture,operation):
    """Separate owner-managed project route. Design approval alone never enables live work."""
    require(not fixture and isinstance(grant,dict) and set(grant)==PROJECT_GRANT_KEYS
        and grant.get('grant_version')=='line-two-album-project-grant-1','INVALID_PROJECT_GRANT')
    require(grant['project_root']==root and grant['fixture'] is False and root==str(Path(__file__).resolve().parents[2])
        and grant['artifact_dir']==PROJECT_DIR+'/private' and grant['project_profile']==PROJECT_SCOPE
        and isinstance(grant['task_id'],str) and grant['task_id'].startswith('PILOT-')
        and isinstance(grant['owner'],str) and grant['owner'],'PROJECT_GRANT_SCOPE')
    require(isinstance(grant['operations'],list) and operation in grant['operations']
        and len(grant['operations'])==len(set(grant['operations']))
        and set(grant['operations'])<=PROJECT_OPERATIONS,'PROJECT_GRANT_OPERATIONS')
    require((grant['album_quota'],grant['lifecycle_album_limit'],grant['save_all_dispatch_limit'],
        grant['chooser_confirmation_limit'],grant['reversible_gui_invocation_limit'])==(2,1,2,2,23),
        'PROJECT_GRANT_QUOTA')
    require(grant['contract_path']==PROJECT_DIR+'/private/project-contract.json'
        and grant['gui_ledger']==PROJECT_DIR+'/private/gui-ledger.json'
        and grant['sensor_scope']=={'bundle_id':'jp.naver.line.mac','provider':'SCREEN_CAPTURE_KIT',
            'capture_scope':'FULL_DISPLAY','surfaces':['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER']},
        'PROJECT_GRANT_BINDING')
    for field in ('config_sha256','source_sha256','contract_sha256','native_binary_sha256'):
        require(isinstance(grant[field],str) and len(grant[field])==64
            and all(c in '0123456789abcdef' for c in grant[field]),'PROJECT_GRANT_BINDING')
    require(isinstance(grant['producer_binary'],dict) and set(grant['producer_binary'])=={'path','bytes','sha256'}
        and isinstance(grant['decoder_binding'],dict) and set(grant['decoder_binding'])=={'path','bytes','sha256'}
        and isinstance(grant['runtime_binding'],dict) and set(grant['runtime_binding'])=={'path','bytes','sha256'}
        and isinstance(grant['entry_binding'],dict) and set(grant['entry_binding'])=={'path','bytes','sha256'}
        and grant['entry_binding']['path']==PROJECT_DIR+'/two_album_entry.mjs','PROJECT_RUNTIME_BINDING')
    require(grant['native_binary_sha256']==grant['decoder_binding']['sha256'],'PROJECT_DECODER_BINDING')
    reader=ProjectReader(root)
    try:
        from .observations import artifact
        contract_raw,_=reader.read(grant['contract_path'],'PROJECT_CONTRACT_UNAVAILABLE')
        require(sha(contract_raw)==grant['contract_sha256'],'PROJECT_CONTRACT_DRIFT')
        require(grant['owner_decision'].get('path')==PROJECT_DIR+'/private/owner-decision.json'
            and grant['external_review'].get('path')==PROJECT_DIR+'/private/implementation-review.json'
            and grant['live_readiness'].get('path')==PROJECT_DIR+'/private/live-readiness.json',
            'PROJECT_DECISION_PATH')
        decision=strict_json(artifact(reader,grant['owner_decision']),'PROJECT_OWNER_DECISION_REQUIRED')
        review=strict_json(artifact(reader,grant['external_review']),'PROJECT_REVIEW_REQUIRED')
        readiness=strict_json(artifact(reader,grant['live_readiness']),'PROJECT_READINESS_REQUIRED')
        runtime=validate_project_runtime_binding(reader,grant)
        require(decision.get('profile')==PROJECT_SCOPE and decision.get('decision')=='AUTHORIZE_SCOPED_NON_GUI_IMPLEMENTATION'
            and decision.get('non_gui_authorized') is True,'PROJECT_OWNER_DECISION_MISMATCH')
        require(review.get('profile')==PROJECT_SCOPE and review.get('verdict')=='APPROVE_IMPLEMENTATION'
            and review.get('head_source_sha256')==grant['source_sha256']
            and review.get('entry_sha256')==grant['entry_binding']['sha256']
            and review.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
            and review.get('review_method')=='OWNER_TRANSFERRED_EXTERNAL_PR_REVIEW'
            and isinstance(review.get('disposition_ref'),str) and review.get('disposition_ref')
            and review.get('reviewer') not in (None,'owner','implementer'),'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
        require(readiness.get('profile')==PROJECT_SCOPE and readiness.get('gui_ready') is True
            and readiness.get('owner_foreground_handoff') is True
            and readiness.get('independent_acceptance_access') is True
            and readiness.get('physical_delivery') in ('SUPPORTED','POLICY_ACCEPTED_LOGICAL_ONLY')
            and readiness.get('source_sha256')==grant['source_sha256']
            and readiness.get('config_sha256')==grant['config_sha256']
            and readiness.get('entry_sha256')==grant['entry_binding']['sha256']
            and readiness.get('runtime_binding_sha256')==grant['runtime_binding']['sha256'],
            'PROJECT_LIVE_READINESS_REQUIRED')
        if operation in PROJECT_MUTATING:
            require(decision.get('live_gui_authorized') is True and isinstance(readiness.get('owner_consent_ref'),dict),
                'PROJECT_LIVE_CONSENT_REQUIRED')
            consent=strict_json(artifact(reader,readiness['owner_consent_ref']),'PROJECT_OWNER_CONSENT_REQUIRED')
            require(consent.get('profile')==PROJECT_SCOPE and consent.get('gui_authorized') is True
                and consent.get('source_sha256')==grant['source_sha256']
                and consent.get('config_sha256')==grant['config_sha256'],'PROJECT_OWNER_CONSENT_MISMATCH')
        require(grant['config_sha256']==sha(reader.read('config/line_backup_config.json')[0]),'PROJECT_CONFIG_DRIFT')
        snapshot=Store(root).snapshot()
        require(snapshot['receipt']['source_sha256']==grant['source_sha256'],'PROJECT_SOURCE_DRIFT')
    finally:reader.close()
    return grant

def validate_project_runtime_binding(reader,grant):
    """Bind the full product source closure and exact private producer/decoder/entry bytes."""
    from .store import SOURCE_PATHS
    from .observations import artifact
    runtime_ref=grant['runtime_binding']
    require(runtime_ref['path']==PROJECT_DIR+'/private/runtime-binding.json','PROJECT_RUNTIME_BINDING')
    raw=artifact(reader,runtime_ref);manifest=strict_json(raw,'PROJECT_RUNTIME_BINDING_INVALID')
    keys={'version','profile','project_root','source_sha256','config_sha256','source_files','runtime_files','callback_sources'}
    require(isinstance(manifest,dict) and set(manifest)==keys and manifest.get('version')==1
        and manifest.get('profile')==PROJECT_SCOPE and manifest.get('project_root')==grant['project_root']
        and manifest.get('source_sha256')==grant['source_sha256']
        and manifest.get('config_sha256')==grant['config_sha256'],'PROJECT_RUNTIME_BINDING_MISMATCH')
    snap=Store(grant['project_root']).snapshot()
    source_files=[{k:item[k] for k in ('path','bytes','sha256')} for item in snap['source_files']]
    require(source_files==manifest['source_files'] and [item['path'] for item in source_files]==SOURCE_PATHS,
        'PROJECT_SOURCE_CLOSURE_MISMATCH')
    expected={'producer_binary':grant['producer_binary'],'decoder_binding':grant['decoder_binding'],
        'entry_binding':grant['entry_binding']}
    actual=manifest['runtime_files']
    require(isinstance(actual,list) and len(actual)==len(expected),'PROJECT_RUNTIME_MEMBERSHIP')
    indexed={}
    for item in actual:
        require(isinstance(item,dict) and set(item)=={'role','path','bytes','sha256'} and item['role'] not in indexed,
            'PROJECT_RUNTIME_MEMBERSHIP')
        indexed[item['role']]=item
    require(set(indexed)==set(expected),'PROJECT_RUNTIME_MEMBERSHIP')
    for role,binding in expected.items():
        item=indexed[role]
        require(item['path']==binding['path'] and item['bytes']==binding['bytes'] and item['sha256']==binding['sha256'],
            'PROJECT_RUNTIME_BINDING_MISMATCH')
        require(isinstance(item['path'],str) and not item['path'].startswith('/')
            and all(part not in ('','.','..') for part in item['path'].split('/')),'PROJECT_RUNTIME_PATH')
        data,_=reader.read(item['path'],'PROJECT_RUNTIME_FILE_UNAVAILABLE')
        require(len(data)==item['bytes'] and sha(data)==item['sha256'],'PROJECT_RUNTIME_FILE_DRIFT')
        if role in ('producer_binary','decoder_binding'):
            fd=reader.open(item['path'])
            try:require(stat.S_ISREG(os.fstat(fd).st_mode)
                and bool(os.fstat(fd).st_mode&(stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)),
                'PROJECT_RUNTIME_EXECUTABLE_UNAVAILABLE')
            finally:os.close(fd)
    required_callbacks={'cli_bridge','capture_analyzer','classifier_chooser','menu_lineage','retainer'}
    callback_sources=manifest['callback_sources']
    require(isinstance(callback_sources,list) and callback_sources,'PROJECT_CALLBACK_SOURCE_BINDING_REQUIRED')
    covered=set()
    for item in callback_sources:
        require(isinstance(item,dict) and set(item)=={'roles','path','bytes','sha256'}
            and isinstance(item['roles'],list) and item['roles']
            and len(item['roles'])==len(set(item['roles']))
            and set(item['roles'])<=required_callbacks and isinstance(item['path'],str)
            and not item['path'].startswith('/') and all(part not in ('','.','..') for part in item['path'].split('/'))
            and type(item['bytes']) is int and item['bytes']>0 and isinstance(item['sha256'],str)
            and len(item['sha256'])==64 and all(c in '0123456789abcdef' for c in item['sha256']),
            'PROJECT_CALLBACK_SOURCE_BINDING')
        data,_=reader.read(item['path'],'PROJECT_CALLBACK_SOURCE_UNAVAILABLE')
        require(len(data)==item['bytes'] and sha(data)==item['sha256'],'PROJECT_CALLBACK_SOURCE_DRIFT')
        covered.update(item['roles'])
    require(covered==required_callbacks,'PROJECT_CALLBACK_SOURCE_COVERAGE')
    return manifest

def execute(ns):
    store=Store(ns.project_root)
    if ns.operation=='inspect':
        snapshot=store.snapshot();s=snapshot['state']
        candidate_data=load_input(ns.project_root,ns.input).get('data',{}) if ns.input else {}
        candidates=candidate_data.get('candidates',[])
        require(isinstance(candidates,list),'INSPECT_CANDIDATES_INVALID')
        eligible=[target for target in candidates if Service.eligible(s,target)]
        # JS may consume this safe summary; never roundtrip raw canonical history.
        return dict(receipt=snapshot['receipt'],config=snapshot['config'],dispatch_authorized=False,
            state_facts=dict(schema_version=s['schema_version'],revision=s['revision'],active_batch=s.get('active_batch'),
                active_writer_id=s['active_writer_id'],verified_count=len(s['verified_albums'])),
            eligible_candidates=eligible)
    grant=authorize(ns.project_root,ns.authorization,ns.fixture,ns.operation)
    store.authorization_path=ns.authorization
    service=Service(ns.project_root,grant['owner'],grant['artifact_dir'],ns.authorization)
    if ns.operation=='resume':return service.resume()
    payload=load_input(ns.project_root,ns.input)
    if ns.operation=='gui_initialize':return store.initialize_project_ledger(grant,payload.get('data',{}))
    if ns.operation=='gui_phase':
        data=payload.get('data',{})
        return store.advance_project_phase(grant,data.get('phase'),c1_evidence=data.get('c1_evidence'),a_run_id=data.get('a_run_id'))
    if ns.operation=='gui_observe':
        data=payload.get('data',{})
        return store.reserve_observation(grant,data.get('kind'),checkpoint=data.get('checkpoint'),album=data.get('album'))
    if ns.operation=='gui_reserve':return store.reserve_gui(grant,payload.get('data',{}))
    if ns.operation=='gui_consume':return store.consume_gui(grant,payload.get('data',{}))
    expected=strict_json(base64.b64decode(payload['expected_token'],validate=True),'INVALID_RECEIPT_TOKEN')
    require(expected['project_root']==ns.project_root and expected['config_sha256']==grant['config_sha256']
        and expected['source_sha256']==grant['source_sha256'],'REQUEST_AUTHORITY_MISMATCH')
    data=payload.get('data',{})
    if ns.operation=='migrate':return store.migrate(expected,data['snapshot_path'],fixture=ns.fixture)
    if ns.operation=='begin':
        if grant.get('grant_version')=='line-two-album-project-grant-1':
            require(data.get('mode')=='backup_batch' and data.get('limit')==1,'PROJECT_BEGIN_SCOPE')
        return service.begin(expected,data['mode'],data['limit'])
    if ns.operation=='admit':
        if grant.get('grant_version')=='line-two-album-project-grant-1':
            return service.admit_bounded(expected,data['record'],data['target'],data['session'],data.get('workflow_link'))
        return service.admit(expected,data['records'],data['session'])
    if ns.operation=='prepare':return service.prepare(expected,data.get('observation'))
    if ns.operation=='calibrate':return service.calibrate(expected,data['detail'],data['calibration'],data['menu'],data['closure'])
    if ns.operation=='intent':return service.intent(expected,data['fresh'])
    if ns.operation=='dispatch':return service.dispatch(expected,data['evidence'],data['chooser'],data['download_started'],data.get('receipt'))
    if ns.operation=='finalize':return service.finalize(expected,data['decoder'],data['decoder_sha256'])
    if ns.operation=='stop':return service.stop(expected,data['reason'])
    if ns.operation=='finish':return service.finish(expected,data['records'],data['session'])
    if ns.operation=='release':return service.release(expected)
    require(False,'UNKNOWN_OPERATION')

def main(argv=None):
    p=argparse.ArgumentParser(prog='line_backup_batch')
    p.add_argument('operation',choices=['inspect','migrate','begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','finish','release','resume','gui_reserve','gui_consume','gui_initialize','gui_phase','gui_observe'])
    p.add_argument('--project-root',required=True);p.add_argument('--authorization');p.add_argument('--input')
    p.add_argument('--fixture',action='store_true');ns=p.parse_args(argv)
    try:
        result=execute(ns)
        if 'receipt' in result:
            from line_backup_acceptance.common import json_bytes
            result['receipt_token']=base64.b64encode(json_bytes(result.pop('receipt'))).decode('ascii')
        print(json.dumps(result,ensure_ascii=False,allow_nan=False));return 0
    except Exception as exc:
        code=exc.code if isinstance(exc,AcceptanceError) else 'INVALID_REQUEST'
        print(json.dumps(dict(status='REFUSED',code=code,message=str(exc),dispatch_authorized=False)),file=sys.stderr);return 4

if __name__=='__main__':raise SystemExit(main())
