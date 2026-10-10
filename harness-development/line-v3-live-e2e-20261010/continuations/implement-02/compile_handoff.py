"""Deterministic local document compilation; no native admission or role dispatch."""
from pathlib import Path
import datetime as dt
import hashlib
import json
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
ORIGIN = HERE.parents[1]
RELEASE = Path('/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write_exact(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise RuntimeError(f'Frozen output differs: {path}')
    else:
        with path.open('xb') as stream:
            stream.write(raw)

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

original = (ORIGIN / 'plan-contract.json').read_bytes()
assert digest(original) == 'ffef63e5ce295910cf0b07a5cc5615bc2719dc651e425306677666b5d8a68ab1'
contract = json.loads(original)
# Sole scope addition was explicitly named in the accepted continuation plan.
extra = 'state/.line-backup-v3.tmp'
if extra not in contract['allowed_paths']:
    contract['allowed_paths'].insert(contract['allowed_paths'].index('state/.line-backup-migration-v3.tmp') + 1, extra)
assert contract['workflow_policy']['max_parallel_writers'] == 0
assert contract['workflow_policy']['handoff_review_required'] is False
resources = []
for path in sorted((RELEASE / 'schemas/v3').glob('*.json')):
    value = json.loads(path.read_bytes())
    if '$id' in value:
        resources.append((value['$id'], Resource.from_contents(value)))
registry = Registry().with_resources(resources)
schema = json.loads((RELEASE / 'schemas/v3/task.schema.json').read_bytes())
Draft202012Validator(schema, registry=registry).validate(contract)
raw = encoded(contract)
write_exact(HERE / 'plan-contract.json', raw)
write_exact(HERE / 'handoff.json', raw)
contract_hash = digest(raw)
plan_hash = digest((HERE / 'plan.md').read_bytes())

policy = {
    'task_id': contract['task_id'], 'continuation': 'implement-02',
    'original_contract_sha256': digest(original), 'contract_sha256': contract_hash,
    'plan_sha256': plan_hash,
    'decision_provenance': 'Actual request_user_input tool responses in this conversation; not inferred from a timeout or assistant prose.',
    'swift_attempt_exception': {
        'authority': 'USER', 'question_id': 'swift_attempt_exception',
        'actual_answer': '核准單次例外 (Recommended)', 'decision': 'AUTHORIZED_ONE_EXTRA_PACKAGE_VALIDATION',
        'original_limit': 3, 'retained_actual_runs': 4, 'unknown_earlier_history': 'UNKNOWN',
        'extra_allowance': 1, 'extra_consumed_by_this_document_task': 0,
        'retained_attempt_ids': ['668ea46f205c42f1b5d5ba5aa3f966e4', '5b37804c7b314bdeb80238d415d2fc1f',
                                 '85355bab929e445c8719cd6056e3c591', '24fbfc8ff57743af97e60a9edc25ba23'],
        'consume_before_subprocess': True, 'failure_or_unknown_consumes': True,
        'stop_after_extra_failure_or_unknown': True, 'package_build_or_filtered_prerun_allowed': False,
        'history_reset_allowed': False
    },
    'plan_review': {
        'authority': 'USER', 'question_id': 'updated_plan_review_route',
        'actual_answer': '直接 Handoff (Recommended)', 'status': 'WAIVED/NOT_RUN',
        'subsequent_user_instruction': '本次計劃不需要獨立審查',
        'post_implementation_independent_acceptance_required': True
    },
    'gui_limits': {'save_all': 2, 'chooser_confirmation': 2, 'additional_reversible_gui_invocations': 1000,
                   'per_lifecycle_albums': 1, 'lifecycle_count': 2, 'shared_task_ledger': True},
    'native_admission': 'NOT_RUN', 'native_controller_validation': 'NOT_RUN',
    'schema_structural_review_flag': 'CRITICAL immutable schema retains plan_review_required=true; actual user waiver is separately bound.',
    'product_implementation_by_this_document_task': 'NOT_RUN', 'live_e2e_by_this_document_task': 'NOT_RUN',
    'documentation_delivery_authorization': 'User explicitly requested GPT-6 luna context synthesis and detailed commit message, then add/commit/push for completed documents.'
}
write_exact(HERE / 'continuation-policy.json', encoded(policy))
waiver = {
    'waiver_format_version': '1', 'source': 'TRUSTED_OPERATOR', 'task_id': contract['task_id'],
    'gate_id': 'G_PLAN_REVIEW_WAIVER', 'contract_sha256': contract_hash,
    'decision': 'WAIVE_GATE', 'authority': 'USER',
    'reason': 'Actual user decision directly hands this updated plan to Implement; review stays WAIVED/NOT_RUN and post-implementation Acceptance remains required.',
    'user_confirmation': 'updated_plan_review_route = 直接 Handoff (Recommended); 本次計劃不需要獨立審查',
    'observation_sha256': None,
    'created_at': '2026-10-10T00:00:00Z'
}
# Do not invent a decision timestamp. Omit the placeholder and use current capture time
# only as record creation time, preserved on subsequent deterministic checks.
if (HERE / 'plan-review-waiver.json').exists():
    waiver['created_at'] = json.loads((HERE / 'plan-review-waiver.json').read_bytes())['created_at']
else:
    waiver['created_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
write_exact(HERE / 'plan-review-waiver.json', encoded(waiver))
waiver_schema = json.loads((RELEASE / 'schemas/v3/waiver.schema.json').read_bytes())
Draft202012Validator(waiver_schema, registry=registry).validate(waiver)

prompt = (HERE / 'handoff-prompt.txt').read_text()
gates = '\n'.join(f"| {g['gate_id']} | {g['phase']} | {g['owner']} | {g['goal_criticality']} | {g['evidence_role']} | {g['closure_gate']} |" for g in contract['gate_specs'])
summary = prompt + '\n\n# 執行交接封包\n\n' + (
    f'Plan SHA-256：`{plan_hash}`。Contract/Handoff SHA-256：`{contract_hash}`。\n\n'
    '這是本次已確認計畫的 deterministic local Handoff；不是 03 prompt 的可選 Handoff Reviewer 結果。'
    'native stage packet/emitted validators 尚未提供，controller admission/validation 保持 NOT_RUN。'
    '直接 JSON Schema 檢查只證明文件結構，不認證產品或 E2E。\n\n'
    '本次交接只完成文件；所有產品／實機 gates 的 PASS 仍需接手者產生原始證據。'
    'Plan Review waiver 是獨立 user decision，不是 reviewer PASS。\n\n'
    '## 凍結 gates\n\n| Gate | Phase | Owner | Criticality | Evidence role | Closure |\n'
    '|---|---|---|---|---|---|\n' + gates + '\n\n'
    '## 完整機器契約\n\n下面的 JSON 與 plan-contract.json / handoff.json 內容一致；'
    'allowed_paths、required_evidence、gate_specs 及 writer limits 不得由接手者自行擴張。\n\n'
    '```json\n' + raw.decode() + '```\n'
)
write_exact(HERE / 'handoff.md', summary.encode())
files = ['plan.md', 'plan-contract.json', 'handoff.json', 'handoff-prompt.txt', 'handoff.md',
         'continuation-policy.json', 'plan-review-waiver.json', 'compile_handoff.py']
records = []
for name in files:
    content = (HERE / name).read_bytes()
    records.append({'path': name, 'bytes': len(content), 'sha256': digest(content)})
receipt = {
    'kind': 'local_deterministic_handoff_document_verification', 'task_id': contract['task_id'],
    'original_contract_sha256': digest(original), 'contract_sha256': contract_hash,
    'contract_handoff_byte_equality': True, 'direct_task_schema_validation': 'PASS',
    'direct_waiver_schema_validation': 'PASS',
    'schema_resource_root': str(RELEASE / 'schemas/v3'),
    'native_stage_contract_validation': 'NOT_RUN', 'native_stage_result_validation': 'NOT_RUN',
    'native_admission': 'NOT_RUN', 'reason': 'No actual stage packet/emitted commands; local checks do not substitute for controller validation.',
    'files': records
}
write_exact(HERE / 'compile-handoff.receipt.json', encoded(receipt))
print(json.dumps({'contract_handoff_equal': True, 'direct_schema_validation': 'PASS',
                  'native_controller_validation': 'NOT_RUN', 'contract_sha256': contract_hash,
                  'handoff_path': str(HERE / 'handoff.md')}, ensure_ascii=False))
