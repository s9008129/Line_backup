"""Public canonical entry. Fixture authority never admits the live project."""
import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys
import unicodedata
from line_backup_acceptance.common import AcceptanceError,HUMAN_EXECUTION_MODE,HUMAN_INPUT_ACTOR
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
ONE56_GRANT_KEYS=PROJECT_GRANT_KEYS|{'single_album_route'}
HUMAN_GRANT_FIELDS={'execution_mode','input_actor','observer_session_id'}
ONE56_HUMAN_GRANT_KEYS=ONE56_GRANT_KEYS|HUMAN_GRANT_FIELDS
PROJECT_SCOPE='LINE_TWO_ALBUM_PILOT/1'
PROJECT_DIR='harness-development/line-two-album-pilot-20261014'
ONE56_GRANT_VERSION='line-two-album-project-grant-1'
ONE56_DECISION='AUTHORIZE_ONE_REAL_56_PHOTO_TRANSACTION'
ONE56_ENTRY='runSingleAlbumPilot'
ONE56_HUMAN_ENTRY='runHumanAssistedSingleAlbumPilot'
ONE56_FINGERPRINT={'start_date':'2024-05-27','end_date':'2024-05-31','expected_images':56}
ONE56_HUMAN_FINGERPRINT={'start_date':'2024-05-27','end_date':'2024-05-31','expected_images':56}
ONE56_PROVIDER_ACTOR='s9008129'
ONE56_PROVIDER_REPOSITORY='https://api.github.com/repos/s9008129/Line_backup'
ONE56_PULL_REQUEST_API=ONE56_PROVIDER_REPOSITORY+'/pulls/10'
ONE56_PULL_REQUEST_HTML='https://github.com/s9008129/Line_backup/pull/10'
ONE56_REQUIRED_OPERATIONS={'begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','release',
    'gui_reserve','gui_consume','gui_phase','gui_observe'}
ONE56_HUMAN_REQUIRED_OPERATIONS=ONE56_REQUIRED_OPERATIONS-{'gui_phase'}
ONE56_HUMAN_INPUT_STAGES=('CARD','CALIBRATION','SAVE_ALL','CHOOSER_PATH','CHOOSER_CONFIRM')
ONE56_HUMAN_STAGE_RESERVATIONS={
    'CARD':('album_open',1,['A.CARD']),
    'CALIBRATION':('menu_calibration',2,['A.CAL_OPEN','A.CAL_DISMISS']),
    'SAVE_ALL':('dispatch_inputs',2,['A.ATOMIC_ELLIPSIS','A.SAVE_ALL']),
    'CHOOSER_PATH':('chooser_inputs',4,['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM']),
    'CHOOSER_CONFIRM':('chooser_inputs',4,['A.GO_TO_FOLDER','A.SET_PATH','A.PATH_RETURN','A.CHOOSER_CONFIRM'])}
ONE56_HUMAN_RESERVATION_KEYS={'stage','kind','count','run_id','owner','slots'}
ONE56_HUMAN_CONSUME_KEYS={'reservation_id','outcome','request_ref','result_ref','request_id','result_id',
    'evidence_refs','execution_mode','input_actor','observer_session_id'}
ONE56_HUMAN_REQUEST_KEYS={'version','kind','task_id','grant_sha256','execution_mode','input_actor',
    'observer_session_id','source_sha256','run_id','action_id','request_stage','fingerprint',
    'destination','reservation_ids','request_id','issued_at','instruction','raw_evidence_refs'}
ONE56_HUMAN_RESULT_KEYS={'version','kind','task_id','grant_sha256','execution_mode','input_actor',
    'observer_session_id','source_sha256','run_id','action_id','request_stage','fingerprint',
    'destination','reservation_ids','request_id','result_id','recorded_at','operator_reported',
    'observed','outcome','raw_evidence_refs'}
ONE56_HUMAN_STAGE_INSTRUCTIONS={
    'CARD':'Open only the bound A56 album card; do not use Save All in this step.',
    'CALIBRATION':'Open the album menu, verify the Save All row is present, then close the menu without choosing Save All.',
    'SAVE_ALL':'Use Save All exactly once. If the result is uncertain, stop; never repeat it.',
    'CHOOSER_PATH':"Enter the exact bound destination in LINE's folder chooser and return to the chooser; do not confirm yet.",
    'CHOOSER_CONFIRM':'Confirm the exact empty destination once. If confirmation is uncertain, stop; never repeat it.'}
ONE56_HUMAN_ACTION_SLOTS={slot for _,_,slots in ONE56_HUMAN_STAGE_RESERVATIONS.values() for slot in slots}
ONE56_HUMAN_MENU_ATTESTATION_KEYS={'kind','execution_mode','input_actor','observer_session_id','observed_at',
    'detail_ref','menu_ref','closure_ref','attestation_ref'}
ONE56_HUMAN_BINDING_KEYS={'destination','grant_sha256','observer_session_id','source_sha256','task_id'}
ONE56_HUMAN_BOUND_OPERATIONS={'begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','release'}
ONE56_HUMAN_READ_KEYS={
    'reservation':{'kind','reservation_id'},
    'intent':{'kind','run_id','action_id'},
    'verified':{'kind','run_id'}}
ONE56_HUMAN_FAKE_TOKENS=('cuareturned','classifierpass','precision','exactlyonce','fullautomaticpass',
    'scksupportpass','framesupportpass')
ONE56_CALLBACK_ROLES={
    PROJECT_DIR+'/mac_runtime.mjs':{'cli_bridge','menu_lineage','retainer'},
    PROJECT_DIR+'/mac/analyzer.mjs':{'capture_analyzer'},
    PROJECT_DIR+'/mac/classifier.mjs':{'classifier_chooser'},
    PROJECT_DIR+'/mac/chooser.mjs':{'classifier_chooser'},
    PROJECT_DIR+'/mac/producer.mjs':{'capture_analyzer','menu_lineage'},
    PROJECT_DIR+'/mac/visual_diagnostic.mjs':{'capture_analyzer'},
}
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

def one56_bundle(path):
    """Return the exact ONE56 bundle directory, rejecting aliases and path tricks."""
    require(isinstance(path,str) and not path.startswith('/') and '\\' not in path
        and all(part not in ('','.','..') for part in path.split('/')),'ONE56_BUNDLE_PATH')
    match=re.fullmatch(re.escape(PROJECT_DIR)+r'/private/authority-bundles/ONE56-[A-Za-z0-9][A-Za-z0-9_-]{0,63}/project-grant\.json',path)
    require(match is not None,'ONE56_BUNDLE_PATH')
    return path.rsplit('/',1)[0]

def _one56_ref(ref,bundle,name):
    require(isinstance(ref,dict) and set(ref)=={'path','bytes','sha256'}
        and ref.get('path')==bundle+'/'+name and type(ref.get('bytes')) is int and ref['bytes']>0
        and isinstance(ref.get('sha256'),str) and re.fullmatch(r'[0-9a-f]{64}',ref['sha256']) is not None,
        'ONE56_BUNDLE_MIXED')

def _one56_normalized(value):
    return ''.join(char for char in value.lower() if char.isalnum())

def _one56_has_fabricated_token(value):
    normalized=_one56_normalized(value)
    return any(token in normalized for token in ONE56_HUMAN_FAKE_TOKENS)

def one56_execution_mode(grant):
    """Classify the explicit A56 mode. Partial or contradictory bindings fail closed."""
    present=HUMAN_GRANT_FIELDS.intersection(grant) if isinstance(grant,dict) else set()
    if not present:return 'AUTO'
    require(present==HUMAN_GRANT_FIELDS and grant.get('grant_version')==ONE56_GRANT_VERSION
        and grant.get('single_album_route') is True
        and grant.get('execution_mode')==HUMAN_EXECUTION_MODE
        and grant.get('input_actor')==HUMAN_INPUT_ACTOR
        and isinstance(grant.get('observer_session_id'),str) and grant['observer_session_id']
        and grant['observer_session_id']==grant['observer_session_id'].strip()
        and not any(ord(char)<32 for char in grant['observer_session_id']),'HUMAN_GRANT_BINDING')
    return HUMAN_EXECUTION_MODE

def _one56_expected_operations(mode):
    return ONE56_HUMAN_REQUIRED_OPERATIONS if mode==HUMAN_EXECUTION_MODE else ONE56_REQUIRED_OPERATIONS

def _one56_expected_entry(mode):
    return ONE56_HUMAN_ENTRY if mode==HUMAN_EXECUTION_MODE else ONE56_ENTRY

def _one56_expected_fingerprint(mode):
    return ONE56_HUMAN_FINGERPRINT if mode==HUMAN_EXECUTION_MODE else ONE56_FINGERPRINT

def _one56_reject_fabricated_claims(value,path='human-document'):
    if isinstance(value,dict):
        for key,child in value.items():
            require(isinstance(key,str) and not _one56_has_fabricated_token(key),
                'HUMAN_INPUT_FABRICATED_CLAIM')
            if isinstance(child,str):
                require(not _one56_has_fabricated_token(child),
                    'HUMAN_INPUT_FABRICATED_CLAIM')
            _one56_reject_fabricated_claims(child,f'{path}.{key}')
    elif isinstance(value,list):
        for index,child in enumerate(value):
            if isinstance(child,str):
                require(not _one56_has_fabricated_token(child),
                    'HUMAN_INPUT_FABRICATED_CLAIM')
            _one56_reject_fabricated_claims(child,f'{path}[{index}]')
    elif isinstance(value,str):
        require(not _one56_has_fabricated_token(value),'HUMAN_INPUT_FABRICATED_CLAIM')

def _one56_reject_human_markers(value):
    """AUTO authority must not carry any human-mode marker in a reused artifact."""
    if isinstance(value,dict):
        for key,child in value.items():
            normalized=_one56_normalized(key) if isinstance(key,str) else ''
            require(normalized not in ('observersessionid','inputactor'),'ONE56_MODE_MIXED')
            if normalized=='executionmode':
                require(isinstance(child,str) and _one56_normalized(child)=='auto','ONE56_MODE_MIXED')
            if normalized=='operations' and isinstance(child,list):
                require(not (all(isinstance(item,str) for item in child)
                    and set(child)==ONE56_HUMAN_REQUIRED_OPERATIONS),'ONE56_MODE_MIXED')
            if normalized=='kind' and isinstance(child,str):
                require(_one56_normalized(child) not in ('humaninputrequest1','humaninputresult1',
                    'humaninputunknownlatch1','humanmenuattestation1'),'ONE56_MODE_MIXED')
            if normalized=='requeststage' and isinstance(child,str):
                require(child.upper() not in ONE56_HUMAN_INPUT_STAGES,'ONE56_MODE_MIXED')
            if normalized=='entrymethod' and isinstance(child,str):
                require(_one56_normalized(child)!=_one56_normalized(ONE56_HUMAN_ENTRY),
                    'ONE56_MODE_MIXED')
            if normalized=='binding' and isinstance(child,dict) and set(child)==ONE56_HUMAN_BINDING_KEYS:
                require(False,'ONE56_MODE_MIXED')
        for child in value.values():_one56_reject_human_markers(child)
    elif isinstance(value,list):
        for child in value:_one56_reject_human_markers(child)

def _one56_human_evidence_ref(ref,*,json_required=False):
    return (isinstance(ref,dict) and set(ref)=={'path','bytes','sha256'}
        and isinstance(ref.get('path'),str) and ref['path'].startswith('harness-development/')
        and '/private/' in ref['path'] and (not json_required or ref['path'].endswith('.json'))
        and all(part not in ('','.','..') for part in ref['path'].split('/'))
        and type(ref.get('bytes')) is int and ref['bytes']>0
        and isinstance(ref.get('sha256'),str) and re.fullmatch(r'[0-9a-f]{64}',ref['sha256']) is not None)

def _one56_human_hash(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None

def _one56_human_refs(value,*,json_required=False):
    return (isinstance(value,list) and value
        and all(_one56_human_evidence_ref(ref,json_required=json_required) for ref in value)
        and len({(ref['path'],ref['bytes'],ref['sha256']) for ref in value})==len(value))

def _one56_human_action_matches(stage,action_id):
    if stage in ('CARD','CALIBRATION'):return action_id is None
    return stage in ONE56_HUMAN_INPUT_STAGES and isinstance(action_id,str) and bool(action_id)

def _one56_validate_human_input_document(value,grant):
    kind=value.get('kind')
    keys=ONE56_HUMAN_REQUEST_KEYS if kind=='human-input-request-1' else ONE56_HUMAN_RESULT_KEYS
    require(set(value)==keys and value.get('version')==1 and kind in
        ('human-input-request-1','human-input-result-1'),'ONE56_MODE_MIXED')
    require(value.get('execution_mode')==HUMAN_EXECUTION_MODE
        and value.get('input_actor')==HUMAN_INPUT_ACTOR
        and value.get('observer_session_id')==grant['observer_session_id']
        and value.get('task_id')==grant['task_id']
        and _one56_human_hash(value.get('grant_sha256'))
        and value.get('source_sha256')==grant['source_sha256'],
        'HUMAN_INPUT_BINDING')
    for key in ('run_id','request_id','request_stage','destination'):
        require(isinstance(value.get(key),str) and value[key],'HUMAN_INPUT_BINDING')
    require(value['request_stage'] in ONE56_HUMAN_INPUT_STAGES
        and _one56_human_action_matches(value['request_stage'],value.get('action_id'))
        and value.get('fingerprint')==ONE56_HUMAN_FINGERPRINT
        and _one56_human_destination(value['destination'])
        and isinstance(value.get('reservation_ids'),list) and len(value['reservation_ids'])==1
        and isinstance(value['reservation_ids'][0],str) and value['reservation_ids'][0]
        and _one56_human_refs(value.get('raw_evidence_refs')),'HUMAN_INPUT_BINDING')
    _one56_reject_fabricated_claims(value,'human-input')
    if kind=='human-input-request-1':
        require(isinstance(value.get('issued_at'),str) and value['issued_at']
            and value.get('instruction')==ONE56_HUMAN_STAGE_INSTRUCTIONS[value['request_stage']],
            'HUMAN_INPUT_BINDING')
        return
    require(isinstance(value.get('result_id'),str) and value['result_id']
        and value['result_id']!=value['request_id']
        and isinstance(value.get('recorded_at'),str) and value['recorded_at']
        and value.get('outcome') in ('HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'),
        'HUMAN_INPUT_OUTCOME')
    operator=value.get('operator_reported');observed=value.get('observed')
    require(isinstance(operator,dict)
        and set(operator)=={'status','outcome','reported_at','statement','raw_response_ref'}
        and operator.get('status')=='OPERATOR_REPORTED'
        and operator.get('outcome') in ('HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED')
        and isinstance(operator.get('reported_at'),str) and operator['reported_at']
        and isinstance(operator.get('statement'),str) and operator['statement']
        and _one56_human_evidence_ref(operator.get('raw_response_ref')),
        'HUMAN_INPUT_OPERATOR_REPORT')
    require(isinstance(observed,dict)
        and set(observed)=={'status','facts','observed_at','raw_evidence_refs'}
        and observed.get('status') in ('OBSERVED','UNKNOWN')
        and isinstance(observed.get('facts'),dict)
        and (observed.get('observed_at') is None if observed.get('status')=='UNKNOWN'
            else isinstance(observed.get('observed_at'),str) and observed['observed_at'])
        and _one56_human_refs(observed.get('raw_evidence_refs')),'HUMAN_INPUT_OBSERVED')
    combined=('REFUSED' if operator['outcome']=='REFUSED' else 'UNKNOWN'
        if operator['outcome']=='UNKNOWN' else 'HUMAN_REPORTED_RETURNED'
        if observed['status']=='OBSERVED' else 'UNKNOWN')
    require(value['outcome']==combined,'HUMAN_INPUT_OUTCOME')
    expected=[];seen=set()
    for ref in [operator['raw_response_ref'],*observed['raw_evidence_refs']]:
        key=(ref['path'],ref['bytes'],ref['sha256'])
        if key not in seen:seen.add(key);expected.append(ref)
    require(value['raw_evidence_refs']==expected,'HUMAN_INPUT_EVIDENCE_BINDING')

def _one56_human_artifact_binding(document,grant,grant_sha256,code):
    require(isinstance(grant_sha256,str) and re.fullmatch(r'[0-9a-f]{64}',grant_sha256) is not None
        and isinstance(document,dict),code)
    require(document.get('execution_mode')==HUMAN_EXECUTION_MODE
        and document.get('input_actor')==HUMAN_INPUT_ACTOR
        and document.get('observer_session_id')==grant['observer_session_id']
        and document.get('grant_sha256')==grant_sha256
        and document.get('task_id')==grant['task_id'] and document.get('owner')==grant['owner']
        and document.get('project_root')==grant['project_root']
        and document.get('source_sha256')==grant['source_sha256']
        and document.get('config_sha256')==grant['config_sha256']
        and document.get('entry_method')==ONE56_HUMAN_ENTRY
        and document.get('entry_sha256')==grant['entry_binding']['sha256']
        and document.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
        and document.get('producer_binary_sha256')==grant['producer_binary']['sha256']
        and document.get('decoder_sha256')==grant['decoder_binding']['sha256']
        and document.get('fingerprint')==ONE56_HUMAN_FINGERPRINT,code)
    _one56_reject_fabricated_claims(document)

def _one56_require_auto_artifact(document):
    require(isinstance(document,dict),'PROJECT_MODE_REQUIRED')
    _one56_reject_human_markers(document)

def validate_one56_display_title_alias(decision,consent,confirmation,*,task_id,owner,root,canonical_group,alias_ref):
    alias=decision.get('display_title_alias') if isinstance(decision,dict) else None
    require(isinstance(alias,str) and alias and alias!=canonical_group
        and decision.get('display_title_alias_confirmation_ref')==alias_ref
        and isinstance(consent,dict) and consent.get('display_title_alias')==alias
        and consent.get('display_title_alias_confirmation_ref')==alias_ref
        and confirmation=={'version':1,'task_id':task_id,'owner':owner,'project_root':root,
            'canonical_group_name':canonical_group,'display_title_alias':alias,
            'owner_statement':'- 是，同一群組；保留原備份名稱\n這是視覺辨識的中文字差異'},
        'PROJECT_DISPLAY_TITLE_ALIAS_REQUIRED')
    return alias

def validate_one56_human_decision(decision,grant,grant_sha256):
    _one56_human_artifact_binding(decision,grant,grant_sha256,'PROJECT_OWNER_DECISION_MISMATCH')
    require(decision.get('decision')==ONE56_DECISION,'PROJECT_OWNER_DECISION_MISMATCH')

def validate_one56_human_readiness(readiness,grant,grant_sha256):
    _one56_human_artifact_binding(readiness,grant,grant_sha256,'PROJECT_LIVE_READINESS_REQUIRED')
    require(readiness.get('profile')==PROJECT_SCOPE and readiness.get('gui_ready') is True
        and readiness.get('owner_foreground_handoff') is True
        and readiness.get('independent_acceptance_access') is True
        and readiness.get('physical_delivery') in ('SUPPORTED','POLICY_ACCEPTED_LOGICAL_ONLY'),
        'PROJECT_LIVE_READINESS_REQUIRED')

def validate_one56_human_consent(consent,grant,grant_sha256):
    _one56_human_artifact_binding(consent,grant,grant_sha256,'PROJECT_OWNER_CONSENT_MISMATCH')
    require(consent.get('profile')==PROJECT_SCOPE and consent.get('gui_authorized') is True,
        'PROJECT_OWNER_CONSENT_MISMATCH')

def validate_one56_contract(contract,grant,root,*,grant_sha256=None):
    mode=one56_execution_mode(grant)
    operations=contract.get('operations') if isinstance(contract,dict) else None
    require(isinstance(operations,list) and all(isinstance(op,str) for op in operations)
        and len(operations)==len(set(operations)),'PROJECT_CONTRACT_SCOPE')
    if mode==HUMAN_EXECUTION_MODE:
        _one56_human_artifact_binding(contract,grant,grant_sha256,'PROJECT_CONTRACT_SCOPE')
    else:_one56_require_auto_artifact(contract)
    require(contract.get('status')=='ACTIVE' and contract.get('closed') is False
        and contract.get('task_id')==grant['task_id'] and contract.get('owner')==grant['owner']
        and contract.get('project_root')==root and contract.get('source_sha256')==grant['source_sha256']
        and contract.get('config_sha256')==grant['config_sha256']
        and contract.get('entry_method')==_one56_expected_entry(mode)
        and set(operations)==_one56_expected_operations(mode)
        and contract.get('entry_sha256')==grant['entry_binding']['sha256']
        and contract.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
        and contract.get('producer_binary_sha256')==grant['producer_binary']['sha256'],
        'PROJECT_CONTRACT_SCOPE')

def validate_one56_review(review,original,grant,*,grant_sha256=None):
    mode=one56_execution_mode(grant)
    expected_operations=sorted(_one56_expected_operations(mode))
    expected_entry=_one56_expected_entry(mode)
    expected_fingerprint=_one56_expected_fingerprint(mode)
    require(isinstance(review,dict) and isinstance(original,dict),'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    if mode==HUMAN_EXECUTION_MODE:
        _one56_human_artifact_binding(review,grant,grant_sha256,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
        _one56_human_artifact_binding(original,grant,grant_sha256,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    else:
        _one56_require_auto_artifact(review);_one56_require_auto_artifact(original)
    require(review.get('profile')==PROJECT_SCOPE
        and review.get('verdict')=='APPROVE_IMPLEMENTATION'
        and review.get('review_method')=='OWNER_TRANSFERRED_EXTERNAL_PR_REVIEW'
        and isinstance(review.get('reviewer'),str) and review['reviewer'].strip()
        and review['reviewer'].strip().lower() not in ('owner','implementer','local agent','local reviewer',
            'luna','gpt-6-luna','sol','codex')
        and review.get('task_id')==grant['task_id'] and review.get('owner')==grant['owner']
        and review.get('project_root')==grant['project_root'] and review.get('source_sha256')==grant['source_sha256']
        and review.get('implementation_head') is not None
        and review.get('entry_method')==expected_entry
        and review.get('approved_operations')==expected_operations
        and review.get('fingerprint')==expected_fingerprint
        and review.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
        and review.get('producer_binary_sha256')==grant['producer_binary']['sha256']
        and isinstance(review.get('disposition_ref'),str) and review['disposition_ref'].strip(),
        'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    require(original.get('verdict')=='APPROVE_IMPLEMENTATION'
        and original.get('reviewer')==review['reviewer']
        and original.get('disposition_ref')==review['disposition_ref']
        and original.get('task_id')==grant['task_id'] and original.get('owner')==grant['owner']
        and original.get('project_root')==grant['project_root']
        and original.get('config_sha256')==grant['config_sha256']
        and original.get('implementation_head')==review.get('implementation_head')
        and original.get('source_sha256')==grant['source_sha256']
        and original.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
        and original.get('producer_binary_sha256')==grant['producer_binary']['sha256']
        and original.get('entry_method')==expected_entry
        and original.get('approved_operations')==expected_operations
        and original.get('fingerprint')==expected_fingerprint,
        'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')

def _one56_scope_from_body(body):
    start='<!-- ONE56_REVIEW_SCOPE_V1\n'
    end='\nONE56_REVIEW_SCOPE_END -->'
    require(isinstance(body,str) and body.count(start)==1 and body.count(end)==1
        and body.index(start)<body.index(end),'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    payload=body.split(start,1)[1].split(end,1)[0]
    return strict_json(payload.encode(),'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')

def validate_one56_provider_review(raw,review,contract,grant,*,grant_sha256=None):
    mode=one56_execution_mode(grant)
    if mode==HUMAN_EXECUTION_MODE:
        _one56_human_artifact_binding(review,grant,grant_sha256,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
        _one56_human_artifact_binding(contract,grant,grant_sha256,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    else:
        _one56_require_auto_artifact(raw);_one56_require_auto_artifact(review)
        _one56_require_auto_artifact(contract)
    require(isinstance(raw,dict) and type(raw.get('id')) is int and raw['id']>0
        and type(review.get('provider_review_id')) is int and review['provider_review_id']==raw['id']
        and review.get('provider_review_url')==ONE56_PROVIDER_REPOSITORY+f"/pulls/10/reviews/{raw['id']}"
        and raw.get('pull_request_url')==ONE56_PULL_REQUEST_API
        and review.get('pull_request_url')==ONE56_PULL_REQUEST_API
        and raw.get('html_url')==ONE56_PULL_REQUEST_HTML+f"#pullrequestreview-{raw['id']}"
        and review.get('disposition_ref')==raw.get('html_url')
        and review.get('pull_request_html_url')==ONE56_PULL_REQUEST_HTML
        and raw.get('state') in ('APPROVED','COMMENTED')
        and review.get('provider_state')==raw.get('state')
        and isinstance(raw.get('user'),dict) and raw['user'].get('login')==ONE56_PROVIDER_ACTOR
        and type(raw['user'].get('id')) is int and raw['user']['id']==129814822
        and review.get('provider_actor')==ONE56_PROVIDER_ACTOR
        and isinstance(review.get('implementation_head'),str)
        and re.fullmatch(r'[0-9a-f]{40}',review['implementation_head']) is not None
        and raw.get('commit_id')==review['implementation_head']
        and contract.get('implementation_head')==review['implementation_head'],
        'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    scope=_one56_scope_from_body(raw.get('body'))
    expected={'decision':'APPROVE_IMPLEMENTATION','external_reviewer':'ChatGPT Chief',
        'task_id':grant['task_id'],'owner':grant['owner'],'project_root':grant['project_root'],
        'implementation_head':contract['implementation_head'],'source_sha256':grant['source_sha256'],
        'config_sha256':grant['config_sha256'],'runtime_binding_sha256':grant['runtime_binding']['sha256'],
        'producer_binary_sha256':grant['producer_binary']['sha256'],'entry_sha256':grant['entry_binding']['sha256'],
        'entry_method':_one56_expected_entry(mode),'approved_operations':sorted(_one56_expected_operations(mode)),
        'fingerprint':_one56_expected_fingerprint(mode)}
    if mode==HUMAN_EXECUTION_MODE:
        expected.update(execution_mode=HUMAN_EXECUTION_MODE,input_actor=HUMAN_INPUT_ACTOR,
            observer_session_id=grant['observer_session_id'],grant_sha256=grant_sha256,
            decoder_sha256=grant['decoder_binding']['sha256'])
    require(scope==expected and review.get('reviewer')==scope['external_reviewer']
        and review.get('task_id')==grant['task_id'] and review.get('owner')==grant['owner']
        and review.get('project_root')==grant['project_root']
        and review.get('source_sha256')==grant['source_sha256']
        and review.get('config_sha256')==grant['config_sha256']
        and review.get('runtime_binding_sha256')==grant['runtime_binding']['sha256']
        and review.get('producer_binary_sha256')==grant['producer_binary']['sha256']
        and review.get('entry_sha256')==grant['entry_binding']['sha256'],
        'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
    if mode==HUMAN_EXECUTION_MODE:
        _one56_reject_fabricated_claims(raw,'provider-review')
        _one56_reject_fabricated_claims(scope,'provider-scope')
    return scope

def validate_one56_callback_membership(callback_sources):
    require(isinstance(callback_sources,list),'PROJECT_CALLBACK_SOURCE_BINDING')
    indexed={}
    for item in callback_sources:
        require(isinstance(item,dict) and set(item)=={'roles','path','bytes','sha256'}
            and isinstance(item.get('path'),str) and item['path'] not in indexed,
            'PROJECT_CALLBACK_SOURCE_BINDING')
        indexed[item['path']]=item
    require(set(indexed)==set(ONE56_CALLBACK_ROLES)
        and all(indexed[path].get('roles')==sorted(roles) for path,roles in ONE56_CALLBACK_ROLES.items()),
        'PROJECT_CALLBACK_SOURCE_COVERAGE')

def _one56_human_destination(value):
    return (isinstance(value,str) and value.startswith('/') and value!='/'
        and not value.endswith('/') and '\\' not in value and '\0' not in value
        and not any(ord(char)<32 for char in value)
        and unicodedata.normalize('NFC',value)==value and posixpath.normpath(value)==value)

def _one56_human_binding(value,grant):
    return (isinstance(value,dict) and set(value)==ONE56_HUMAN_BINDING_KEYS
        and value.get('task_id')==grant.get('task_id')
        and _one56_human_hash(value.get('grant_sha256'))
        and value.get('source_sha256')==grant.get('source_sha256')
        and isinstance(value.get('observer_session_id'),str)
        and value.get('observer_session_id')==grant.get('observer_session_id')
        and _one56_human_destination(value.get('destination')))

def _one56_human_read_selector(value):
    require(isinstance(value,dict) and isinstance(value.get('kind'),str),'HUMAN_READ_SELECTOR')
    kind=value['kind'];keys=ONE56_HUMAN_READ_KEYS.get(kind)
    require(keys is not None and set(value)==keys,'HUMAN_READ_SELECTOR')
    for key in keys-{'kind'}:
        child=value.get(key)
        require(isinstance(child,str) and child and child==child.strip()
            and not any(ord(char)<32 for char in child),'HUMAN_READ_SELECTOR')
    return kind

def _one56_inspect_expected(root,request,grant):
    try:expected_raw=base64.b64decode(request.get('expected_token',''),validate=True)
    except (binascii.Error,ValueError,TypeError):require(False,'INVALID_RECEIPT_TOKEN')
    expected=strict_json(expected_raw,'INVALID_RECEIPT_TOKEN')
    require(expected.get('project_root')==root
        and expected.get('config_sha256')==grant['config_sha256']
        and expected.get('source_sha256')==grant['source_sha256'],'REQUEST_AUTHORITY_MISMATCH')
    return expected

def _one56_validate_human_tree(value,grant):
    if isinstance(value,dict):
        for key,child in value.items():
            require(isinstance(key,str),'ONE56_MODE_MIXED')
            normalized=_one56_normalized(key)
            require('workflowlink' not in normalized,'ONE56_MODE_MIXED')
            require('guiphase' not in normalized,'ONE56_HUMAN_PHASE_FORBIDDEN')
            require(not any(marker in normalized for marker in
                ('cuadispatchreceipt','cuareceipt','framesupport','scksupport')),'ONE56_MODE_MIXED')
            require(not normalized.startswith('classifier'),'HUMAN_INPUT_FABRICATED_CLAIM')
            require(normalized not in ('ellipsis','dotspacing','saveallpoint','confidence'),
                'ONE56_MODE_MIXED')
            if normalized=='executionmode':require(child==HUMAN_EXECUTION_MODE,'ONE56_MODE_MIXED')
            if normalized=='inputactor':require(child==HUMAN_INPUT_ACTOR,'ONE56_MODE_MIXED')
            if normalized=='observersessionid':require(child==grant['observer_session_id'],'ONE56_MODE_MIXED')
            if normalized=='entrymethod':require(child==ONE56_HUMAN_ENTRY,'ONE56_MODE_MIXED')
            if normalized=='taskid':require(child==grant['task_id'],'HUMAN_INPUT_BINDING')
            if normalized=='sourcesha256':require(child==grant['source_sha256'],'HUMAN_INPUT_BINDING')
            if normalized=='configsha256':require(child==grant['config_sha256'],'HUMAN_INPUT_BINDING')
            if normalized=='grantsha256':require(_one56_human_hash(child),'HUMAN_INPUT_BINDING')
            if normalized=='owner':require(child==grant['owner'],'HUMAN_INPUT_BINDING')
            if normalized=='operation':require(isinstance(child,str)
                and child in ONE56_HUMAN_REQUIRED_OPERATIONS,'ONE56_HUMAN_PHASE_FORBIDDEN')
            if normalized=='operations':
                require(isinstance(child,list) and all(isinstance(item,str) for item in child)
                    and len(child)==len(set(child))
                    and set(child)==ONE56_HUMAN_REQUIRED_OPERATIONS,'ONE56_HUMAN_PHASE_FORBIDDEN')
            if normalized=='kind' and isinstance(child,str):
                kind=_one56_normalized(child)
                require(not kind.startswith(('cuadispatchreceipt','framesupport')),'ONE56_MODE_MIXED')
                if kind in ('humaninputrequest1','humaninputresult1'):
                    _one56_validate_human_input_document(value,grant)
                elif kind=='humanmenuattestation1':
                    require(set(value)==ONE56_HUMAN_MENU_ATTESTATION_KEYS
                        and value.get('execution_mode')==HUMAN_EXECUTION_MODE
                        and value.get('input_actor')==HUMAN_INPUT_ACTOR
                        and value.get('observer_session_id')==grant['observer_session_id']
                        and isinstance(value.get('observed_at'),str) and value['observed_at']
                        and _one56_human_refs([value.get(key) for key in
                            ('detail_ref','menu_ref','closure_ref','attestation_ref')],json_required=True),
                        'HUMAN_CALIBRATION_REQUIRED')
                elif kind=='humaninputunknownlatch1':
                    require(set(value)=={'version','kind','task_id','grant_sha256','observer_session_id',
                        'source_sha256','run_id','action_id','request_stage','request_id','issuance_key',
                        'reason','recorded_at'} and value.get('version')==1
                        and value.get('task_id')==grant['task_id']
                        and _one56_human_hash(value.get('grant_sha256'))
                        and value.get('observer_session_id')==grant['observer_session_id']
                        and value.get('source_sha256')==grant['source_sha256']
                        and isinstance(value.get('run_id'),str) and value['run_id']
                        and _one56_human_action_matches(value.get('request_stage'),value.get('action_id'))
                        and all(isinstance(value.get(key),str) and value[key] for key in
                            ('request_id','issuance_key','reason','recorded_at')),'HUMAN_INPUT_BINDING')
                elif kind.startswith('humaninput'):
                    require(False,'ONE56_MODE_MIXED')
            if normalized=='requeststage':require(isinstance(child,str)
                and child in ONE56_HUMAN_INPUT_STAGES,'HUMAN_INPUT_STAGE_REQUIRED')
            if normalized=='fingerprint':require(child==ONE56_HUMAN_FINGERPRINT,'HUMAN_INPUT_FINGERPRINT')
            if normalized=='destination':require(_one56_human_destination(child),'HUMAN_INPUT_BINDING')
            if normalized=='reservationids':
                require(isinstance(child,list) and child and all(isinstance(item,str) and item for item in child)
                    and len(child)==len(set(child)),'HUMAN_INPUT_RESERVATIONS')
            if normalized in ('reservationid','requestid','resultid','runid'):
                require(isinstance(child,str) and child,'HUMAN_INPUT_BINDING')
            if normalized=='actionid':
                stage=value.get('request_stage')
                if stage in ('CARD','CALIBRATION'):require(child is None,'HUMAN_INPUT_ACTION_BINDING')
                elif stage in ONE56_HUMAN_INPUT_STAGES:require(isinstance(child,str) and child,'HUMAN_INPUT_ACTION_BINDING')
                else:require(child is None or isinstance(child,str) and child,'HUMAN_INPUT_ACTION_BINDING')
            if normalized=='slots':
                require(isinstance(child,list) and child and all(item in ONE56_HUMAN_ACTION_SLOTS for item in child),
                    'ONE56_MODE_MIXED')
                require(len(child)==len(set(child)),'ONE56_MODE_MIXED')
            if normalized in ('album','projectalbumslot','runalbumslot'):
                require(child in (None,'A'),'ONE56_MODE_MIXED')
            if normalized in ('phase','workflowphase'):
                require(not (isinstance(child,str) and _one56_normalized(child) in
                    ('b','c1','done','pairb','pairc1')),'ONE56_MODE_MIXED')
            if normalized=='checkpoint' and isinstance(child,str):
                marker=_one56_normalized(child)
                require(not any(token in marker for token in ('pairb','pairc1','scroll','returnatolist')),
                    'ONE56_MODE_MIXED')
            if normalized=='rawevidencerefs':require(_one56_human_refs(child),'HUMAN_INPUT_EVIDENCE_BINDING')
            _one56_validate_human_tree(child,grant)
    elif isinstance(value,list):
        for child in value:_one56_validate_human_tree(child,grant)

def _one56_validate_human_payload(grant,operation,payload):
    require(operation in ONE56_HUMAN_REQUIRED_OPERATIONS,'ONE56_MODE_MIXED')
    require(operation not in ('gui_phase','gui_initialize'),'ONE56_HUMAN_PHASE_FORBIDDEN')
    require(isinstance(payload,dict),'INVALID_INPUT')
    _one56_reject_fabricated_claims(payload,'payload')
    _one56_validate_human_tree(payload,grant)
    require(isinstance(payload.get('data',{}),dict),'INVALID_INPUT')
    data=payload.get('data') if isinstance(payload.get('data'),dict) else {}
    if operation in ONE56_HUMAN_BOUND_OPERATIONS:
        require(_one56_human_binding(data.get('binding'),grant),'HUMAN_INPUT_BINDING_REQUIRED')
    if operation=='gui_reserve':
        stage=data.get('stage');require(stage in ONE56_HUMAN_INPUT_STAGES,'HUMAN_INPUT_STAGE_REQUIRED')
        require(stage!='CHOOSER_CONFIRM','HUMAN_CHOOSER_CONFIRM_REQUIRED')
        kind,count,slots=ONE56_HUMAN_STAGE_RESERVATIONS[stage]
        require(set(data)==ONE56_HUMAN_RESERVATION_KEYS and data.get('kind')==kind
            and type(data.get('count')) is int and data.get('count')==count
            and data.get('slots')==slots and isinstance(data.get('run_id'),str) and data.get('run_id')
            and data.get('owner')==grant['owner'],'HUMAN_RESERVATION_BINDING')
    elif operation=='gui_observe':
        require(data.get('album') in (None,'A'),'ONE56_MODE_MIXED')
        checkpoint=data.get('checkpoint')
        require(checkpoint is None or (isinstance(checkpoint,str)
            and not any(token in _one56_normalized(checkpoint)
                for token in ('pairb','pairc1','scroll','returnatolist'))),'ONE56_MODE_MIXED')
    elif operation=='admit':
        require('workflow_link' not in data,'ONE56_MODE_MIXED')
    elif operation=='calibrate':
        calibration=data.get('calibration')
        require(isinstance(calibration,dict) and set(calibration)==ONE56_HUMAN_MENU_ATTESTATION_KEYS
            and calibration.get('kind')=='human-menu-attestation-1'
            and calibration.get('execution_mode')==HUMAN_EXECUTION_MODE
            and calibration.get('input_actor')==HUMAN_INPUT_ACTOR
            and calibration.get('observer_session_id')==grant['observer_session_id']
            and isinstance(calibration.get('observed_at'),str) and calibration['observed_at']
            and _one56_human_refs([calibration.get(key) for key in
                ('detail_ref','menu_ref','closure_ref','attestation_ref')],json_required=True),
            'HUMAN_CALIBRATION_REQUIRED')
    elif operation=='dispatch':
        require('receipt' not in data or data.get('receipt') is None,'ONE56_MODE_MIXED')
        readback=data.get('chooser_readback')
        require(isinstance(readback,dict) and set(readback)=={'reference'}
            and _one56_human_refs([readback.get('reference')],json_required=True),
            'HUMAN_CHOOSER_RESERVATION_READBACK')
    elif operation=='finalize':
        decoder_path=grant['decoder_binding']['path']
        decoder_absolute=str(Path(grant['project_root'],decoder_path).resolve())
        require(data.get('decoder') in (decoder_path,decoder_absolute)
            and data.get('decoder_sha256')==grant['decoder_binding']['sha256'],
            'HUMAN_DECODER_BINDING')
    elif operation=='gui_consume':
        require(set(data)<=ONE56_HUMAN_CONSUME_KEYS
            and isinstance(data.get('reservation_id'),str) and data['reservation_id']
            and data.get('execution_mode')==HUMAN_EXECUTION_MODE
            and data.get('input_actor')==HUMAN_INPUT_ACTOR
            and data.get('observer_session_id')==grant['observer_session_id'],'ONE56_MODE_MIXED')
        require(data.get('outcome') in (None,'HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED'),
            'HUMAN_INPUT_OUTCOME')
        request_ref=data.get('request_ref');result_ref=data.get('result_ref')
        require(request_ref is None or _one56_human_evidence_ref(request_ref,json_required=True),
            'HUMAN_INPUT_REQUEST_ARTIFACT')
        require(result_ref is None or _one56_human_evidence_ref(result_ref,json_required=True),
            'HUMAN_INPUT_RESULT_ARTIFACT')
        if request_ref is None:
            require(result_ref is None and data.get('request_id') is None and data.get('result_id') is None
                and data.get('evidence_refs') is None
                and data.get('outcome') in (None,'UNKNOWN','REFUSED'),'HUMAN_INPUT_REQUEST_REF_REQUIRED')
        if data.get('outcome')=='HUMAN_REPORTED_RETURNED':
            require(request_ref is not None and result_ref is not None,'HUMAN_INPUT_RESULT_REF_REQUIRED')
        if result_ref is not None:
            require(data.get('outcome') in ('HUMAN_REPORTED_RETURNED','UNKNOWN','REFUSED')
                and request_ref is not None and request_ref['path']!=result_ref['path'],
                'HUMAN_INPUT_RESULT_REF_REQUIRED')
        elif request_ref is not None:
            require(data.get('outcome') in ('UNKNOWN','REFUSED') and data.get('result_id') is None
                and data.get('evidence_refs') is None,'HUMAN_INPUT_RESULT_REF_REQUIRED')
        if request_ref is not None:
            require(isinstance(data.get('request_id'),str) and data['request_id'],
                'HUMAN_INPUT_REQUEST_BINDING')
        if result_ref is not None:
            require(isinstance(data.get('request_id'),str) and data['request_id']
                and isinstance(data.get('result_id'),str) and data['result_id']
                and data['result_id']!=data['request_id'],
                'HUMAN_INPUT_RESULT_BINDING')
        evidence_refs=data.get('evidence_refs')
        if evidence_refs is not None:
            require(result_ref is not None and _one56_human_refs(evidence_refs),
                'HUMAN_INPUT_EVIDENCE_BINDING')

def validate_one56_payload(grant,operation,payload):
    """Per-mode admission before any A56 service or canonical-state mutation."""
    require(isinstance(grant,dict) and grant.get('single_album_route') is True,'PROJECT_GRANT_REQUIRED')
    mode=one56_execution_mode(grant)
    if mode==HUMAN_EXECUTION_MODE:_one56_validate_human_payload(grant,operation,payload)
    else:_one56_reject_human_markers(payload)

def authorize_project(root,path,grant,fixture,operation):
    """Separate owner-managed project route. Design approval alone never enables live work."""
    if isinstance(grant,dict) and grant.get('single_album_route') is True:
        return authorize_one56_project(root,path,grant,fixture,operation)
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
        # The source-only bootstrap review may support a future G1 observation
        # after the unchanged live-readiness/Owner-consent checks below. It must
        # never authorize an action-capable grant or be relabelled as approval
        # of the full pilot.
        review_approved=(review.get('verdict')=='APPROVE_IMPLEMENTATION'
            or (review.get('verdict')=='APPROVE_FOR_PRIVATE_AUTHORITY_BOOTSTRAP_ONLY'
                and operation=='gui_observe' and grant['operations']==['gui_observe']))
        require(review.get('profile')==PROJECT_SCOPE and review_approved
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

def authorize_one56_project(root,path,grant,fixture,operation):
    """Immutable, single-transaction authority. Legacy project grants keep their original route."""
    mode=one56_execution_mode(grant)
    expected_keys=ONE56_HUMAN_GRANT_KEYS if mode==HUMAN_EXECUTION_MODE else ONE56_GRANT_KEYS
    expected_operations=_one56_expected_operations(mode)
    require(not fixture and isinstance(grant,dict) and set(grant)==expected_keys
        and grant.get('grant_version')==ONE56_GRANT_VERSION and grant.get('single_album_route') is True,
        'INVALID_PROJECT_GRANT')
    bundle=one56_bundle(path)
    require(grant['project_root']==root and grant['fixture'] is False
        and root==str(Path(__file__).resolve().parents[2])
        and grant['artifact_dir']==PROJECT_DIR+'/private' and grant['project_profile']==PROJECT_SCOPE
        and isinstance(grant['task_id'],str) and grant['task_id'].startswith('PILOT-')
        and isinstance(grant['owner'],str) and grant['owner'],'PROJECT_GRANT_SCOPE')
    require(isinstance(grant['operations'],list) and operation in grant['operations']
        and len(grant['operations'])==len(set(grant['operations']))
        and set(grant['operations'])==expected_operations,'PROJECT_GRANT_OPERATIONS')
    require((grant['album_quota'],grant['lifecycle_album_limit'],grant['save_all_dispatch_limit'],
        grant['chooser_confirmation_limit'])==(1,1,1,1)
        and grant['reversible_gui_invocation_limit']==23,'PROJECT_GRANT_QUOTA')
    require(grant['contract_path']==bundle+'/project-contract.json'
        and grant['gui_ledger']==PROJECT_DIR+'/private/gui-ledger.json'
        and grant['sensor_scope']=={'bundle_id':'jp.naver.line.mac','provider':'SCREEN_CAPTURE_KIT',
            'capture_scope':'FULL_DISPLAY','surfaces':['ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER']},
        'PROJECT_GRANT_BINDING')
    for field in ('config_sha256','source_sha256','contract_sha256','native_binary_sha256'):
        require(isinstance(grant[field],str) and re.fullmatch(r'[0-9a-f]{64}',grant[field]) is not None,
            'PROJECT_GRANT_BINDING')
    require(isinstance(grant['producer_binary'],dict) and set(grant['producer_binary'])=={'path','bytes','sha256'}
        and isinstance(grant['decoder_binding'],dict) and set(grant['decoder_binding'])=={'path','bytes','sha256'}
        and isinstance(grant['runtime_binding'],dict) and set(grant['runtime_binding'])=={'path','bytes','sha256'}
        and isinstance(grant['entry_binding'],dict) and set(grant['entry_binding'])=={'path','bytes','sha256'}
        and grant['entry_binding']['path']==PROJECT_DIR+'/two_album_entry.mjs','PROJECT_RUNTIME_BINDING')
    require(grant['native_binary_sha256']==grant['decoder_binding']['sha256'],'PROJECT_DECODER_BINDING')
    for field,name in (('owner_decision','owner-decision.json'),('external_review','implementation-review.json'),
        ('live_readiness','live-readiness.json'),('runtime_binding','runtime-binding.json')):
        _one56_ref(grant[field],bundle,name)
    _one56_ref({'path':grant['contract_path'],'bytes':1,'sha256':grant['contract_sha256']},bundle,'project-contract.json')
    reader=ProjectReader(root)
    try:
        from .observations import artifact
        grant_raw,_=reader.read(path,'PROJECT_GRANT_DRIFT')
        require(strict_json(grant_raw,'INVALID_PROJECT_GRANT')==grant,'PROJECT_GRANT_DRIFT')
        grant_sha256=sha(grant_raw)
        refs=('owner_decision','external_review','live_readiness','runtime_binding')
        raw_refs={field:artifact(reader,grant[field]) for field in refs}
        contract_raw,_=reader.read(grant['contract_path'],'PROJECT_CONTRACT_UNAVAILABLE')
        require(sha(contract_raw)==grant['contract_sha256'],'PROJECT_CONTRACT_DRIFT')
        contract=strict_json(contract_raw,'PROJECT_CONTRACT_INVALID')
        decision=strict_json(raw_refs['owner_decision'],'PROJECT_OWNER_DECISION_REQUIRED')
        review=strict_json(raw_refs['external_review'],'PROJECT_REVIEW_REQUIRED')
        readiness=strict_json(raw_refs['live_readiness'],'PROJECT_READINESS_REQUIRED')
        runtime=validate_project_runtime_binding(reader,grant,one56_bundle=bundle)
        validate_one56_contract(contract,grant,root,grant_sha256=grant_sha256)
        require(isinstance(contract.get('implementation_head'),str)
            and re.fullmatch(r'[0-9a-f]{40}',contract['implementation_head']) is not None,
            'PROJECT_CONTRACT_SCOPE')
        if mode==HUMAN_EXECUTION_MODE:
            validate_one56_human_decision(decision,grant,grant_sha256)
        else:
            _one56_require_auto_artifact(decision)
            require(decision.get('decision')==ONE56_DECISION and decision.get('task_id')==grant['task_id']
                and decision.get('owner')==grant['owner'] and decision.get('project_root')==root
                and decision.get('source_sha256')==grant['source_sha256']
                and decision.get('config_sha256')==grant['config_sha256']
                and decision.get('entry_method')==ONE56_ENTRY
                and decision.get('fingerprint')==ONE56_FINGERPRINT,
                'PROJECT_OWNER_DECISION_MISMATCH')
        original_ref=review.get('original_review_ref')
        _one56_ref(original_ref,bundle,'external-review-original.json')
        original_raw=artifact(reader,original_ref)
        original=strict_json(original_raw,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
        validate_one56_review(review,original,grant,grant_sha256=grant_sha256)
        provider_ref=review.get('provider_response_ref')
        _one56_ref(provider_ref,bundle,'github-review-response.json')
        provider_raw=artifact(reader,provider_ref)
        provider_response=strict_json(provider_raw,'PROJECT_IMPLEMENTATION_REVIEW_REQUIRED')
        validate_one56_provider_review(provider_response,review,contract,grant,grant_sha256=grant_sha256)
        alias_ref=decision.get('display_title_alias_confirmation_ref')
        _one56_ref(alias_ref,bundle,'display-title-alias-confirmation.json')
        alias_raw=artifact(reader,alias_ref)
        alias_confirmation=strict_json(alias_raw,'PROJECT_DISPLAY_TITLE_ALIAS_REQUIRED')
        canonical_group=reader.read('config/line_backup_config.json')[0]
        canonical_group=strict_json(canonical_group,'PROJECT_CONFIG_INVALID').get('group_name')
        alias=decision.get('display_title_alias')
        if mode==HUMAN_EXECUTION_MODE:
            validate_one56_human_readiness(readiness,grant,grant_sha256)
        else:
            _one56_require_auto_artifact(readiness)
            require(readiness.get('profile')==PROJECT_SCOPE and readiness.get('gui_ready') is True
                and readiness.get('owner_foreground_handoff') is True
                and readiness.get('independent_acceptance_access') is True
                and readiness.get('physical_delivery') in ('SUPPORTED','POLICY_ACCEPTED_LOGICAL_ONLY')
                and readiness.get('source_sha256')==grant['source_sha256']
                and readiness.get('config_sha256')==grant['config_sha256']
                and readiness.get('entry_sha256')==grant['entry_binding']['sha256']
                and readiness.get('runtime_binding_sha256')==grant['runtime_binding']['sha256'],
                'PROJECT_LIVE_READINESS_REQUIRED')
        consent_ref=readiness.get('owner_consent_ref')
        require(isinstance(consent_ref,dict) and consent_ref.get('path')==bundle+'/owner-consent.json',
            'PROJECT_OWNER_CONSENT_REQUIRED')
        consent_raw=artifact(reader,consent_ref)
        consent=strict_json(consent_raw,'PROJECT_OWNER_CONSENT_REQUIRED')
        if mode==HUMAN_EXECUTION_MODE:
            validate_one56_human_consent(consent,grant,grant_sha256)
        else:_one56_require_auto_artifact(consent)
        validate_one56_display_title_alias(decision,consent,alias_confirmation,task_id=grant['task_id'],
            owner=grant['owner'],root=root,canonical_group=canonical_group,alias_ref=alias_ref)
        require(reader.read(alias_ref['path'])[0]==alias_raw,'PROJECT_DISPLAY_TITLE_ALIAS_DRIFT')
        if operation in PROJECT_MUTATING:
            require(decision.get('live_gui_authorized') is True,'PROJECT_LIVE_CONSENT_REQUIRED')
            if mode!=HUMAN_EXECUTION_MODE:
                require(consent.get('profile')==PROJECT_SCOPE and consent.get('gui_authorized') is True
                    and consent.get('task_id')==grant['task_id'] and consent.get('owner')==grant['owner']
                    and consent.get('source_sha256')==grant['source_sha256']
                    and consent.get('config_sha256')==grant['config_sha256']
                    and consent.get('fingerprint')==ONE56_FINGERPRINT,'PROJECT_OWNER_CONSENT_MISMATCH')
        require(grant['config_sha256']==sha(reader.read('config/line_backup_config.json')[0]),'PROJECT_CONFIG_DRIFT')
        snapshot=Store(root).snapshot()
        require(snapshot['receipt']['source_sha256']==grant['source_sha256'],'PROJECT_SOURCE_DRIFT')
        # Re-read all signed material and grant from the same no-follow reader; its
        # observations reject replacement or byte changes during validation.
        require(reader.read(path,'PROJECT_GRANT_DRIFT')[0]==grant_raw,'PROJECT_GRANT_DRIFT')
        for field in refs:
            require(reader.read(grant[field]['path'])[0]==raw_refs[field],'PROJECT_GRANT_EVIDENCE_DRIFT')
        require(reader.read(original_ref['path'])[0]==original_raw,'PROJECT_GRANT_EVIDENCE_DRIFT')
        require(reader.read(provider_ref['path'])[0]==provider_raw,'PROJECT_GRANT_EVIDENCE_DRIFT')
        require(reader.read(alias_ref['path'])[0]==alias_raw,'PROJECT_GRANT_EVIDENCE_DRIFT')
        require(reader.read(consent_ref['path'])[0]==consent_raw,'PROJECT_GRANT_EVIDENCE_DRIFT')
        require(reader.read(grant['contract_path'])[0]==contract_raw,'PROJECT_CONTRACT_DRIFT')
    finally:reader.close()
    return grant

def validate_project_runtime_binding(reader,grant,one56_bundle=None):
    """Bind the full product source closure and exact private producer/decoder/entry bytes."""
    from .store import SOURCE_PATHS
    from .observations import artifact
    runtime_ref=grant['runtime_binding']
    runtime_path=(one56_bundle+'/runtime-binding.json') if one56_bundle else PROJECT_DIR+'/private/runtime-binding.json'
    require(runtime_ref['path']==runtime_path,'PROJECT_RUNTIME_BINDING')
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
    if one56_bundle:
        validate_one56_callback_membership(callback_sources)
    return manifest

def execute(ns):
    if ns.operation=='native_authorize':
        # Read-only reuse of the complete live project authority check. This
        # never initializes the GUI ledger, acquires an owner or observes LINE.
        grant=authorize(ns.project_root,ns.authorization,ns.fixture,'gui_observe')
        require(grant.get('grant_version') in ('line-two-album-project-grant-1',ONE56_GRANT_VERSION),'PROJECT_GRANT_REQUIRED')
        display_title_alias=None
        if grant.get('single_album_route') is True:
            from .observations import artifact
            bundle=one56_bundle(ns.authorization);reader=ProjectReader(ns.project_root)
            try:
                decision=strict_json(artifact(reader,grant['owner_decision']),'PROJECT_OWNER_DECISION_REQUIRED')
                alias_ref=decision['display_title_alias_confirmation_ref']
                alias_doc=strict_json(artifact(reader,alias_ref),'PROJECT_DISPLAY_TITLE_ALIAS_REQUIRED')
                display_title_alias=alias_doc['display_title_alias']
            finally:reader.close()
        return dict(status='PROJECT_NATIVE_AUTHORIZED',project_root=grant['project_root'],
            owner=grant['owner'],task_id=grant['task_id'],source_sha256=grant['source_sha256'],
            display_title_alias=display_title_alias,dispatch_authorized=False,native_controller_admission=False)
    store=Store(ns.project_root)
    if ns.operation=='inspect':
        snapshot=store.snapshot();s=snapshot['state']
        request=load_input(ns.project_root,ns.input) if ns.input else {}
        candidate_data=request.get('data',{})
        ledger_status=None;human_read=None
        human_read_requested='human_read' in candidate_data
        read_kind=_one56_human_read_selector(candidate_data['human_read']) if human_read_requested else None
        if candidate_data.get('include_gui_ledger_status') is True or read_kind is not None:
            grant=authorize(ns.project_root,ns.authorization,False,'gui_observe')
            _one56_inspect_expected(ns.project_root,request,grant)
            store.authorization_path=ns.authorization
            if read_kind is not None:
                require(one56_execution_mode(grant)==HUMAN_EXECUTION_MODE,'ONE56_MODE_MIXED')
                selector=candidate_data['human_read']
                if read_kind=='reservation':
                    human_read=store.human_reservation_fact(grant,selector['reservation_id'])
                elif read_kind=='intent':
                    human_read=store.human_intent_fact(grant,selector['run_id'],selector['action_id'])
                else:human_read=store.human_verified_fact(grant,selector['run_id'])
            if candidate_data.get('include_gui_ledger_status') is True:
                ledger_status=store.project_gui_ledger_status(grant)
        candidates=candidate_data.get('candidates',[])
        require(isinstance(candidates,list),'INSPECT_CANDIDATES_INVALID')
        eligible=[target for target in candidates if Service.eligible(s,target)]
        # JS may consume this safe summary; never roundtrip raw canonical history.
        result=dict(receipt=snapshot['receipt'],config=snapshot['config'],dispatch_authorized=False,
            state_facts=dict(schema_version=s['schema_version'],revision=s['revision'],active_batch=s.get('active_batch'),
                active_writer_id=s['active_writer_id'],verified_count=len(s['verified_albums'])),
            eligible_candidates=eligible)
        if ledger_status is not None:result['gui_ledger_status']=ledger_status
        if human_read_requested:result['human_read']=human_read
        return result
    grant=authorize(ns.project_root,ns.authorization,ns.fixture,ns.operation)
    mode=one56_execution_mode(grant)
    store.authorization_path=ns.authorization
    service=Service(ns.project_root,grant['owner'],grant['artifact_dir'],ns.authorization)
    if ns.operation=='resume':return service.resume()
    payload=load_input(ns.project_root,ns.input)
    if grant.get('single_album_route') is True:validate_one56_payload(grant,ns.operation,payload)
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
    if mode==HUMAN_EXECUTION_MODE:
        if ns.operation=='begin':
            return service.human_begin(expected,data['binding'],data.get('readiness'))
        if ns.operation=='admit':
            return service.human_admit(expected,data['binding'],data.get('readiness'),data.get('begin'))
        if ns.operation=='prepare':
            return service.human_prepare(expected,data['binding'],data.get('readiness'),data.get('begin'),data.get('admitted'))
        if ns.operation=='calibrate':
            return service.human_commit_calibration(expected,data['binding'],data['run_id'],data['request'],
                data['result'],data['evidence'],data['calibration'],data.get('request_ref'),data.get('result_ref'))
        if ns.operation=='intent':
            return service.human_commit_intent(expected,data['binding'],data['run_id'],data['calibration'],
                data.get('fresh_evidence'))
        if ns.operation=='dispatch':
            return service.human_record_dispatch(expected,data['binding'],data['run_id'],data['intent'],
                data.get('intent_readback'),data['save_all'],data['chooser_path'],data['chooser_confirm'],
                data.get('chooser_readback'))
        if ns.operation=='finalize':
            return service.human_finalize(expected,data['binding'],data['run_id'],data['decoder'],
                data['decoder_sha256'])
        if ns.operation=='stop':
            return service.human_stop(expected,data['binding'],data['run_id'],data['reason'])
        if ns.operation=='release':
            return service.human_release(expected,data['binding'],data['run_id'])
    if ns.operation=='migrate':return store.migrate(expected,data['snapshot_path'],fixture=ns.fixture)
    if ns.operation=='begin':
        if grant.get('grant_version') in ('line-two-album-project-grant-1',ONE56_GRANT_VERSION):
            require(data.get('mode')=='backup_batch' and data.get('limit')==1,'PROJECT_BEGIN_SCOPE')
        return service.begin(expected,data['mode'],data['limit'])
    if ns.operation=='admit':
        if grant.get('grant_version') in ('line-two-album-project-grant-1',ONE56_GRANT_VERSION):
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
    p.add_argument('operation',choices=['inspect','migrate','begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','finish','release','resume','gui_reserve','gui_consume','gui_initialize','gui_phase','gui_observe','native_authorize'])
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
