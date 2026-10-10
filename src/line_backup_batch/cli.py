"""Public canonical entry. Fixture authority never admits the live project."""
import argparse
import base64
import json
from pathlib import Path
import sys
from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.project_binding import ProjectReader,strict_json,sha
from .schema import require
from .store import Store
from .service import Service

GRANT_KEYS={
    'grant_version','task_id','project_root','fixture','artifact_dir','owner','operations',
    'config_sha256','source_sha256','album_quota','lifecycle_album_limit','save_all_dispatch_limit',
    'chooser_confirmation_limit','reversible_gui_invocation_limit',
    'authorization_evidence','acceptance_evidence'
}
OPERATIONS={'migrate','begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','finish','release','resume'}

def load_input(root,path):
    require(isinstance(path,str) and path.startswith('harness-development/'),'UNSAFE_INPUT_PATH')
    reader=ProjectReader(root)
    try:raw,_=reader.read(path)
    finally:reader.close()
    return strict_json(raw,'INVALID_INPUT')

def authorize(root,path,fixture,operation):
    grant=load_input(root,path)
    require(isinstance(grant,dict) and set(grant)==GRANT_KEYS and grant['grant_version']=='line-batch-execution-grant-1',
        'INVALID_GRANT')
    require(isinstance(grant.get('operations'),list),'GRANT_OPERATIONS')
    require(grant['project_root']==root and grant['fixture'] is fixture and operation in grant['operations'],'GRANT_SCOPE')
    require(isinstance(grant['task_id'],str) and grant['task_id'].startswith('TASK-')
        and isinstance(grant['owner'],str) and grant['owner'] and isinstance(grant['artifact_dir'],str)
        and grant['artifact_dir'].startswith('harness-development/') and '..' not in grant['artifact_dir'].split('/'),
        'GRANT_SCOPE')
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
            and all(grant[k]==0 for k in ('album_quota','lifecycle_album_limit','save_all_dispatch_limit','chooser_confirmation_limit',
                'reversible_gui_invocation_limit')),'FIXTURE_PRODUCTION_CREDENTIALS')
        require(set(grant['operations'])<= {'migrate','begin','resume'},'FIXTURE_LIVE_OPERATION_REFUSED')
    else:
        require(root==str(installed),'SELECTED_ROOT_REQUIRED')
        reader=ProjectReader(root)
        try:
            from .observations import artifact
            auth_ref=grant['authorization_evidence']
            require(isinstance(auth_ref,dict) and auth_ref.get('path')==grant['artifact_dir']+'/authorization.json',
                'AUTHORIZATION_EVIDENCE_REQUIRED')
            authorization=strict_json(artifact(reader,auth_ref),'INVALID_AUTHORIZATION_EVIDENCE')
            require(authorization.get('task_id')==grant['task_id'] and authorization.get('project_root')==root
                and authorization.get('save_all_dispatch_cap')==grant['save_all_dispatch_limit']
                and authorization.get('chooser_confirmation_cap')==grant['chooser_confirmation_limit']
                and authorization.get('additional_reversible_gui_invocation_cap')==grant['reversible_gui_invocation_limit']
                and authorization.get('config_albums_per_lifecycle')==1
                and authorization.get('independent_acceptance_required') is True,
                'AUTHORIZATION_SCOPE_MISMATCH')
            decisions=authorization.get('locked_decisions')
            require(isinstance(decisions,dict) and decisions.get('canonical_writer_and_migration')
                and decisions.get('canonical_writer_and_migration')=='唯一 v3 writer；保留歷史的 schema 2→3 migration；完整 catalog admission'
                and decisions.get('acceptance_and_lifecycle')=='execution grant 與事後 independent Acceptance 分離；config cap 維持 1；兩本採兩個獨立 lifecycle'
                and authorization.get('plan_review_decision')=='Explicit user waiver; NOT a reviewer PASS'
                and authorization.get('independent_acceptance_required') is True
                and authorization.get('decision_answers')==[
                    {'decision':'Canonical writer, migration, and catalog','answer':'Use the unique v3 writer, preserve schema 2 history during schema 2 to 3 migration, and require complete catalog admission.'},
                    {'decision':'Review route and lifecycle scope','answer':'Use the explicit Plan Review waiver while retaining independent post-implementation Acceptance; run two separate cap-one lifecycles.'}
                ],'AUTHORIZATION_DECISIONS_MISSING')
            require(grant['album_quota']==2 and grant['lifecycle_album_limit']==1 and grant['save_all_dispatch_limit']==2
                and grant['chooser_confirmation_limit']==2 and grant['reversible_gui_invocation_limit']==1000,
                'GRANT_QUOTA_MISMATCH')
            acceptance_ref=grant['acceptance_evidence']
            if acceptance_ref is not None:
                require(isinstance(acceptance_ref,dict)
                    and acceptance_ref.get('path')==grant['artifact_dir']+'/acceptance.result.json','FOREIGN_ACCEPTANCE')
                accepted=strict_json(artifact(reader,acceptance_ref),'INVALID_ACCEPTANCE')
                require(accepted.get('role')=='ACCEPTANCE_REVIEWER'
                    and accepted.get('statuses',{}).get('INDEPENDENT_ACCEPTANCE_STATUS')=='PASS','ACCEPTANCE_REQUIRED')
                passed={g.get('gate_id') for g in accepted.get('gate_results',[]) if g.get('verdict')=='PASS'}
                require({'I0','I1','I2','I3','I4','A1'}<=passed,'ACCEPTANCE_GATES_MISSING')
        finally:reader.close()
    snap=Store(root).snapshot()
    require(snap['receipt']['config_sha256']==grant['config_sha256'] and snap['receipt']['source_sha256']==grant['source_sha256'],
        'GRANT_AUTHORITY_DRIFT')
    return grant

def execute(ns):
    store=Store(ns.project_root)
    if ns.operation=='inspect':
        snapshot=store.snapshot();s=snapshot['state']
        # JS may consume this safe summary; never roundtrip raw canonical history.
        return dict(receipt=snapshot['receipt'],config=snapshot['config'],dispatch_authorized=False,
            state_facts=dict(schema_version=s['schema_version'],revision=s['revision'],active_batch=s.get('active_batch'),
                active_writer_id=s['active_writer_id'],verified_count=len(s['verified_albums'])))
    grant=authorize(ns.project_root,ns.authorization,ns.fixture,ns.operation)
    store.authorization_path=ns.authorization
    service=Service(ns.project_root,grant['owner'],grant['artifact_dir'],ns.authorization)
    if ns.operation=='resume':return service.resume()
    payload=load_input(ns.project_root,ns.input)
    expected=strict_json(base64.b64decode(payload['expected_token'],validate=True),'INVALID_RECEIPT_TOKEN')
    require(expected['project_root']==ns.project_root and expected['config_sha256']==grant['config_sha256']
        and expected['source_sha256']==grant['source_sha256'],'REQUEST_AUTHORITY_MISMATCH')
    data=payload.get('data',{})
    if ns.operation=='migrate':return store.migrate(expected,data['snapshot_path'],fixture=ns.fixture)
    if ns.operation=='begin':return service.begin(expected,data['mode'],data['limit'])
    if ns.operation=='admit':return service.admit(expected,data['records'],data['session'])
    if ns.operation=='prepare':return service.prepare(expected,data.get('observation'))
    if ns.operation=='calibrate':return service.calibrate(expected,data['detail'],data['calibration'],data['menu'],data['closure'])
    if ns.operation=='intent':return service.intent(expected,data['fresh'])
    if ns.operation=='dispatch':return service.dispatch(expected,data['evidence'],data['chooser'],data['download_started'])
    if ns.operation=='finalize':return service.finalize(expected,data['decoder'],data['decoder_sha256'])
    if ns.operation=='stop':return service.stop(expected,data['reason'])
    if ns.operation=='finish':return service.finish(expected,data['records'],data['session'])
    if ns.operation=='release':return service.release(expected)
    require(False,'UNKNOWN_OPERATION')

def main(argv=None):
    p=argparse.ArgumentParser(prog='line_backup_batch')
    p.add_argument('operation',choices=['inspect','migrate','begin','admit','prepare','calibrate','intent','dispatch','finalize','stop','finish','release','resume'])
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
