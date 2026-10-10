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

def load_input(root,path):
    require(isinstance(path,str) and path.startswith('harness-development/'),'UNSAFE_INPUT_PATH')
    reader=ProjectReader(root)
    try:raw,_=reader.read(path)
    finally:reader.close()
    return strict_json(raw,'INVALID_INPUT')

def authorize(root,path,fixture,operation):
    grant=load_input(root,path)
    require(set(grant)=={'project_root','fixture','artifact_dir','owner','operations','config_sha256','source_sha256','approval','acceptance'},
        'INVALID_GRANT')
    require(grant['project_root']==root and grant['fixture'] is fixture and operation in grant['operations'],'GRANT_SCOPE')
    installed=Path(__file__).resolve().parents[2]
    if fixture:
        require(Path(root).is_relative_to(installed/'harness-development') and '/fixtures/' in root and root!=str(installed),
            'FIXTURE_ROOT_REQUIRED')
        require(grant['approval'] is None and grant['acceptance'] is None,'FIXTURE_PRODUCTION_CREDENTIALS')
    else:
        require(root==str(installed),'SELECTED_ROOT_REQUIRED')
        require(grant['approval'] is not None and grant['acceptance'] is not None,'ACCEPTANCE_REQUIRED')
        reader=ProjectReader(root)
        try:
            from .observations import artifact
            approval=strict_json(artifact(reader,grant['approval']),'INVALID_APPROVAL')
            accepted=strict_json(artifact(reader,grant['acceptance']),'INVALID_ACCEPTANCE')
            require(grant['approval']['path']==grant['artifact_dir']+'/authorization.json'
                and grant['acceptance']['path']==grant['artifact_dir']+'/acceptance.result.json','FOREIGN_APPROVAL')
            require(approval['project_root']==root and approval['config_cap']==1
                and approval['user_message']=='批准改版，MUST use BEST practice to do all tasks','APPROVAL_SCOPE')
            require(accepted['role']=='ACCEPTANCE_REVIEWER' and accepted['statuses']['INDEPENDENT_ACCEPTANCE_STATUS']=='PASS',
                'ACCEPTANCE_REQUIRED')
            passed={g['gate_id'] for g in accepted['gate_results'] if g['verdict']=='PASS'}
            require(set(['I0','I1','I2','I3','I4','A1'])<=passed,'ACCEPTANCE_GATES_MISSING')
            for entry in accepted['evidence_manifests']:
                raw,_=reader.read(entry['path'])
                require(len(raw)==entry['bytes'] and sha(raw)==entry['sha256'],'ACCEPTANCE_ARTIFACT_DRIFT')
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
