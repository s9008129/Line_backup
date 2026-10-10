"""Frozen v3 structure plus semantic authority checks; no state initialization."""
import copy
from pathlib import Path
from line_backup_acceptance.common import AcceptanceError
from line_backup_acceptance.project_binding import strict_json,sha,integer

SCHEMA_SHA='d30ff068623f7dc6c9988387935beabbd5347e4b3a5e2c3a784daf8197db2a37'
POLICY='batch-policy-1'

def require(ok,code):
    if not ok:raise AcceptanceError(code,code,4)

def validate(state):
    from jsonschema import Draft202012Validator,FormatChecker
    from referencing import Registry
    raw=Path(__file__).with_name('state_v3.schema.json').read_bytes()
    require(sha(raw)==SCHEMA_SHA,'SCHEMA_DRIFT')
    try:
        Draft202012Validator(strict_json(raw,'INVALID_SCHEMA'),format_checker=FormatChecker(),
            registry=Registry(retrieve=lambda uri:require(False,'EXTERNAL_SCHEMA_REFUSED'))).validate(state)
    except AcceptanceError:raise
    except Exception as exc:raise AcceptanceError('INVALID_STATE_V3',str(exc),4) from exc
    require(type(state['schema_version']) is int and state['schema_version']==3,'INVALID_STATE_V3')
    b=state['active_batch']
    if b is None:
        require(state['active_writer_id'] is None and state['context_lock'] is None,'ORPHAN_ALBUM_OWNER')
        return
    require(b['policy_version']==POLICY,'POLICY_VERSION')
    cap=min(b['authorized_new_download_limit'],b['configured_new_download_limit'])
    require(b['new_transactions_reserved']<=cap,'QUOTA_OVERFLOW')
    require(b['group_key'].startswith('line:jp.naver.line.mac:'),'BATCH_GROUP')
    if b['mode']=='catalog_only':
        require(b['authorized_new_download_limit']==0 and b['new_transactions_reserved']==0
            and b['current_album_run_id'] is None,'CATALOG_DISPATCH_REFUSED')
    if b['phase'] in ('ADMITTED','RUNNING'):
        require(b['manifest_reference'] is not None,'MANIFEST_REQUIRED')
    if b['current_album_run_id'] is None:
        require(state['active_writer_id'] is None and state['context_lock'] is None,'ORPHAN_ALBUM_OWNER')
    else:
        current=[r for r in state['runs'] if r['run_id']==b['current_album_run_id']]
        require(len(current)==1 and current[0]['workflow_outcome']=='IN_PROGRESS','BATCH_RUN_LINK')
        require(state['current_run_id']==b['current_album_run_id'] and state['active_writer_id']==b['owner_execution_id'],
            'BATCH_OWNER_LINK')
        require(current[0]['batch_id']==b['batch_id'] and current[0]['group_key']==b['group_key'],'BATCH_RUN_LINK')

def legacy_view(state):
    result=copy.deepcopy(state);result.pop('active_batch');result['schema_version']=2
    return result
