"""Deterministic local documents. Does not replace native Harness validators."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CON = str(HERE.relative_to(ROOT))
TP = 'harness-development/line-v3-live-e2e-20261010'
TASK = 'TASK-20261010-line-v3-live-e2e'
RELEASE = '/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source'
NATIVE_PYTHON = '/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def write_new(name, value):
    raw = value if isinstance(value, bytes) else encoded(value)
    target = HERE / name
    if target.exists():
        raise RuntimeError(f'Frozen output already exists: {name}')
    with target.open('xb') as stream:
        stream.write(raw)
    if target.read_bytes() != raw:
        raise RuntimeError(f'Readback failed: {name}')

def load(name):
    return json.loads((HERE / name).read_bytes())

def ref(name):
    raw = (HERE / name).read_bytes()
    return {'path': f'{CON}/{name}', 'relative_path': f'{CON}/{name}',
            'absolute_path': str(HERE / name), 'bytes': len(raw), 'sha256': sha(raw)}

def source_digest():
    acceptance = ['__init__.py', '__main__.py', 'authority.py', 'cli.py', 'common.py',
                  'project_binding.py', 'status.py', 'transaction.py', 'verifier.py']
    batch = ['__init__.py', '__main__.py', 'cli.py', 'content.py', 'coordinator.py',
             'image_decode.swift', 'observations.py', 'schema.py', 'service.py',
             'state_v3.schema.json', 'store.py']
    paths = [f'src/line_backup_acceptance/{n}' for n in acceptance]
    paths += [f'src/line_backup_batch/{n}' for n in batch]
    paths += ['scripts/line_backup_cua_adapter.mjs']
    digest = hashlib.sha256()
    for relative in paths:
        raw = (ROOT / relative).read_bytes()
        digest.update(relative.encode() + b'\0' + raw + b'\0')
    return digest.hexdigest()

def create():
    run = load('document-run.json')
    gates = []
    for name in ['G_PLAN_REVIEW_WAIVER', 'G_AUTH', 'G_OFFLINE', 'G_MIGRATION', 'G_CATALOG',
                 'G_MENU', 'G_FIRST', 'G_SCROLL', 'G_SECOND', 'G_PRESERVE', 'G_REPORT',
                 'G_ACCEPTANCE', 'G_DELIVERY']:
        waiver = name == 'G_PLAN_REVIEW_WAIVER'
        preserve = name == 'G_PRESERVE'
        gates.append({'gate_id': name, 'required': True, 'owner': 'HUMAN' if waiver else 'ROLE',
                      'phase': 'PLAN' if waiver else 'ACCEPTANCE' if name == 'G_ACCEPTANCE' else 'IMPLEMENT',
                      'evidence_source': 'HUMAN_OBSERVATION' if waiver else 'ROLE_OBSERVATION',
                      'goal_criticality': 'SUPPORTING' if waiver or name == 'G_DELIVERY' else 'CORE',
                      'evidence_role': 'DIAGNOSTIC' if waiver else 'MUST_NOT_BREAK' if name in
                      ['G_AUTH', 'G_OFFLINE', 'G_MIGRATION', 'G_PRESERVE'] else 'OUTCOME',
                      'closure_gate': 'BASELINE_DELTA' if preserve else 'HARD_CLEAN', 'reuse': 'NEVER'})
    contract = {
        'format_version': '3', 'task_id': TASK,
        'goal': 'Repair cross-realm CUA byte retention, repo-owned passive native context, strict v2 visual/AX grounding, production callbacks, chooser phases and runtime bindings; preserve the canonical schema-3 writer and complete two different cap-one album lifecycles with actual post-first-release bounded scroll, content/state verification, reporting and independent Acceptance.',
        'task_class': 'CRITICAL',
        'allowed_paths': [
            'scripts/line_backup_cua_adapter.mjs', 'src/line_backup_batch/cli.py',
            'src/line_backup_batch/observations.py', 'src/line_backup_batch/service.py',
            'rev28/Sources/rev28ctl/main.swift',
            'rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift',
            'rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift',
            'rev28/Tests/Rev28CoreTests/FrameSupportTests.swift',
            'tests/test_cua_adapter.mjs', 'tests/test_batch_authority.py',
            'tests/test_batch_observations.py', 'tests/test_batch_lifecycle.py',
            'state/backup_state.json', 'state/.line-backup-state.lock', 'state/.line-backup-v3.tmp',
            'backups/旻謙允禎成長日記', f'{TP}/gui-ledger.json', CON],
        'required_evidence': ['E_BASELINE', 'E_AUTH', 'E_OFFLINE', 'E_MIGRATION', 'E_LIVE_CATALOG',
            'E_MENU', 'E_FIRST', 'E_SCROLL', 'E_SECOND', 'E_PRESERVATION', 'E_REPORT', 'E_ACCEPTANCE',
            'E_DELIVERY', 'E_PLAN_REVIEW_WAIVER', 'E_NATIVE_CONTEXT', 'E_BYTE_RETENTION',
            'E_FRAME_SUPPORT', 'E_V2_CLASSIFIER', 'E_CHOOSER', 'E_RUNTIME_BINDING', 'E_LATENCY',
            'E_SESSION_LIFECYCLE', 'E_PRODUCTION_WIRING', 'E_LAYOUT_FEASIBILITY'],
        'gate_specs': gates,
        'capability_policy': {'network': 'PROXY_ALLOWLIST', 'browser': False,
            'destinations': ['https://developer.apple.com', 'https://support.apple.com',
                             'https://nodejs.org', 'https://github.com/s9008129/Line_backup.git']},
        'retry_policy': {'transient_read_only_retries': 2, 'delays_seconds': [10, 30]},
        'resource_policy': {'prompt_bytes': 65536, 'state_bytes': 524288,
                            'inspect_bytes': 16384, 'log_bytes': 134217728},
        'workflow_policy': {'plan_review_required': True, 'independent_acceptance_required': True,
            'max_parallel_read_only_helpers': 1, 'max_parallel_writers': 0, 'handoff_review_required': False}}
    write_new('plan-contract.json', contract)
    contract_ref = ref('plan-contract.json')
    plan_ref = ref('plan.md')
    write_new('plan-freeze.json', {'kind': 'LOCAL_PLAN_FREEZE_NOT_NATIVE_PUBLICATION',
        'created_at': now(), 'local_run_id': run['local_run_id'], 'plan': plan_ref,
        'contract': contract_ref, 'native_stage_publication': 'NOT_RUN'})
    write_new('user-decisions.json', {'record_created_at': now(), 'authority': 'USER',
        'source': 'Actual conversation user messages and request_user_input responses',
        'decisions': {'acceptance_scope': '橋接修復＋兩本 E2E (Recommended)',
                      'evidence_contract': '加入 v2 證據 (Recommended)',
                      'layout_precondition': '允許調整版面 (Recommended)',
                      'plan_review': '本次修正計劃不需要獨立審查',
                      'document_delivery': '同意文件落檔與 add,commit,push'},
        'decision_timestamp': None, 'decision_timestamp_note': 'Creation time is not an invented user decision time.',
        'contract_sha256': contract_ref['sha256'], 'product_implementation_this_document_turn': False})
    write_new('plan-review-waiver.json', {'waiver_format_version': '1', 'source': 'TRUSTED_OPERATOR',
        'task_id': TASK, 'gate_id': 'G_PLAN_REVIEW_WAIVER', 'contract_sha256': contract_ref['sha256'],
        'decision': 'WAIVE_GATE', 'authority': 'USER',
        'reason': 'User explicitly waived independent Plan Review. The immutable CRITICAL policy flag remains true; local Handoff records WAIVED_NOT_RUN and preserves independent post-implementation Acceptance.',
        'user_confirmation': '本次修正計劃不需要獨立審查；同意文件落檔與 add,commit,push',
        'observation_sha256': None, 'created_at': now()})
    write_new('research-facts.json', {'version': 1, 'kind': 'PLANNER_READ_ONLY_RESEARCH',
        'record_created_at': now(), 'raw_file_manifest': ref('input-manifest.json'),
        'memory_capture': {'request_started_at': '2026-10-10T15:23:02.304Z',
            'request_returned_at': '2026-10-10T15:23:02.381Z', 'duration_ms_observed': 76.28191700000025,
            'screenshot_bytes': 183645,
            'screenshot_sha256': '2e93f01caf5ade784f7e409f91a376fe99badcd828dc9aa266439692d3b297d6',
            'ax_bytes': 1299, 'ax_sha256': '511c6cf8ad8709ca1fc5b595e26ebcec9e02d0bd73dc9e42e32b92e2b0eb90f2',
            'constructor_name': 'Buffer', 'tag': '[object Uint8Array]', 'is_view': True,
            'instanceof_uint8array': False, 'normalized_instanceof_uint8array': True,
            'normalized_hash_identical': True, 'workspace_raw_frame': None, 'workspace_raw_ax': None,
            'evidence_classification': 'OBSERVED_NON_GATE_TOOL_MEMORY_RESULT',
            'fresh_live_gate_pass': False},
        'helper': run['research_helper'], 'product_attempts_this_document_turn': 0,
        'line_inputs_this_document_turn': 0, 'source_digest_algorithm': 'store.sources ordered path NUL bytes NUL',
        'current_product_source_sha256': source_digest(),
        'known_defects': ['cross-realm Buffer strict instanceof refusal', 'ALBUMS boundary key ordering mismatch',
            'frameSupport hook omits intersectionPx used by chooser', 'chooser requires phase-inapplicable PathTextField',
            'production analyzer/navigation callbacks missing', 'frozen Python3.14 path absent',
            'one-complete-card viewport cannot alone establish required scroll evidence'],
        'unknowns': ['installed probe build/source equivalence', 'current native AX/screen permissions',
            'production visual geometry accuracy', 'capture/mapping/chooser/latency live gates'],
        'prior_attempts': f'{TP}/continuations/live-grounding-03/attempt-ledger.json',
        'prior_attempt_counts_reset': False})
    write_new('native-admission.json', {'controller_release': '4.8.0', 'controller_path': f'{RELEASE}/tools/task-orchestrator.py',
        'fixed_runtime': NATIVE_PYTHON, 'fixed_runtime_exists': Path(NATIVE_PYTHON).exists(),
        'native_admission': 'NOT_RUN', 'native_stage_publication': 'NOT_RUN',
        'native_contract_validation': 'NOT_RUN', 'native_result_validation': 'NOT_RUN',
        'controller_run_id': None, 'invitation': None, 'fixed_validation_command': None,
        'local_route': 'USER_WAIVED_PLAN_REVIEW_DETERMINISTIC_LOCAL_DOCUMENT_HANDOFF',
        'reason': 'Fixed Python3.14 runtime is missing and no admitted stage packet/emitted validator is available. No substitute validator, invitation, global runtime repair or native PASS is claimed.',
        'os_sandbox_enforcement': 'UNKNOWN', 'network_denial_enforcement': 'UNKNOWN'})
    write_new('handoff.json', (HERE / 'plan-contract.json').read_bytes())
    prompt = (HERE / 'handoff-prompt.txt').read_text().strip()
    gate_table = '\n'.join(f"| {g['gate_id']} | {g['phase']} | {g['owner']} | {g['goal_criticality']} | {g['evidence_role']} | {g['closure_gate']} |" for g in gates)
    handoff = (prompt + '\n\n# live-grounding-04 實作交接\n\n'
        + f"Plan SHA-256：{plan_ref['sha256']}。Contract／handoff.json SHA-256：{contract_ref['sha256']}。\n\n"
        + '本交接在Plan與contract freeze後deterministic編譯。03 prompt的可選Reviewer未啟動。原生stage/publication/schema validators未執行，不能把下方契約當成native admission receipt。文件已獲落檔與Git授權；產品尚未實作。\n\n'
        + '## 先讀與執行順序\n\n'
        + 'plan.md、research.md、input-manifest.json、baseline.json、native-admission.json → 原報告與attempt ledger → 核對head/dirty/state/runtime → production wiring與隔離回歸 → final source/binary/grants freeze → 有效前景與版面 → catalog/menu/第一本 → release/actual scroll → 不同第二本 → 報告與獨立Acceptance。\n\n'
        + 'code/state/GUI授權、failure routes、檢查命令與界面見plan.md。config cap固定1，兩owner共享quota／ledger；不得自行增加額度。human observation及waiver分開記，不是工具PASS。\n\n'
        + '## 凍結 gates\n\n| Gate | Phase | Owner | Criticality | Evidence role | Closure |\n|---|---|---|---|---|---|\n'
        + gate_table + '\n\n## 精確 allowed paths\n\n'
        + '\n'.join('- ' + p for p in contract['allowed_paths'])
        + '\n\n## 完整機器契約\n\n```json\n' + (HERE / 'plan-contract.json').read_text() + '```\n')
    write_new('handoff.md', handoff.encode())
    write_new('compile-handoff.receipt.json', {'kind': 'DETERMINISTIC_LOCAL_HANDOFF_NOT_NATIVE_CONTROLLER',
        'created_at': now(), 'plan': plan_ref, 'contract': contract_ref,
        'handoff_json': ref('handoff.json'), 'handoff_markdown': ref('handoff.md'),
        'exact_contract_copy': (HERE / 'handoff.json').read_bytes() == (HERE / 'plan-contract.json').read_bytes(),
        'handoff_review_required': False, 'handoff_reviewer_invoked': False, 'native_admission': 'NOT_RUN'})
    source = source_digest()
    for name, role, stage in [('planner.result.json', 'PLANNER', 'PLAN'),
                              ('handoff.result.json', 'HANDOFF_COMPILER', 'HANDOFF')]:
        evidence = []
        for eid, artifact in [('E_BASELINE', 'baseline.json'), ('E_RESEARCH', 'research-facts.json'),
                              ('E_DECISIONS', 'user-decisions.json'), ('E_NATIVE_LIMIT', 'native-admission.json')]:
            artifact_ref = ref(artifact)
            evidence.append({'task_id': TASK, 'run_id': run['local_run_id'], 'stage': stage,
                'role': role, 'source_sha256': source, 'evidence_id': eid, 'path': artifact_ref['path'],
                'bytes': artifact_ref['bytes'], 'sha256': artifact_ref['sha256'],
                'contract_sha256': contract_ref['sha256'],
                'observation': 'Local retained document evidence; does not certify a future live gate.'})
        result = {'result_format_version': '3', 'task_id': TASK, 'run_id': run['local_run_id'],
            'role': role, 'stage': stage, 'candidate_fact': 'PARTIAL', 'validation_fact': 'NOT_RUN',
            'routing_fact': 'EXTERNAL_BLOCKER',
            'statuses': {'PRIMARY_OUTCOME_STATUS': 'NOT_ACHIEVED', 'IMPLEMENTATION_STATUS': 'BLOCKED',
                'CORE_ACCEPTANCE_STATUS': 'BLOCKED', 'REQUIRED_VERIFICATION_STATUS': 'INCOMPLETE',
                'INDEPENDENT_ACCEPTANCE_STATUS': 'PENDING', 'TASK_CLOSURE_STATUS': 'IMPLEMENTATION_BLOCKED'},
            'gate_results': [{'gate_id': g['gate_id'], 'verdict': 'NOT_RUN',
                'evidence_manifest': f'{CON}/plan-review-waiver.json' if g['gate_id'] == 'G_PLAN_REVIEW_WAIVER' else None} for g in gates],
            'evidence_ids': [e['evidence_id'] for e in evidence], 'plan_sha256': plan_ref['sha256'],
            'handoff_sha256': ref('handoff.md')['sha256'], 'source_sha256': source,
            'evidence_manifests': evidence, 'plan_contract_sha256': contract_ref['sha256'],
            'analysis': {'facts': ['User approved full two-album scope, strict v2 evidence, layout preparation and document add/commit/push.',
                'Local plan and byte-identical deterministic Handoff persisted with actual source/file hashes.',
                'No product edits, LINE input, download or state/config mutation in this document phase.'],
                'inferences': ['Repo-owned passive context and byte normalization target the observed production evidence gap.'],
                'unknowns': ['Formal native schema/admission unavailable', 'Native live geometry/classifier/chooser/latency gates unrun'],
                'evidence': [e['path'] for e in evidence], 'confidence': 'HIGH_FOR_OBSERVED_LOCAL_FACTS; LIVE_UNKNOWN',
                'document_package_status': 'LOCAL_HANDOFF_COMPILED', 'underlying_plan_review': 'USER_WAIVED_NOT_RUN',
                'native_stage_run_id': None, 'convergence_scope': 'Preserves known prior NON_MENU_SCK_SUPPORT three attempts; other prior counts remain original ledger, not reset.'},
            'handoff_summary': '本地Plan及精確deterministic Handoff已落檔；接手者依凍結路徑修復bytes/native/v2/chooser/wiring並實驗兩本。Plan Review已由使用者豁免，Acceptance保留。原生Harness固定runtime失效，native驗證仍NOT_RUN；本輪產品與E2E尚未執行。',
            'needs_human': False, 'human_decisions': [],
            'convergence': {'meaningful_attempts': 3, 'consecutive_no_progress': 0,
                'last_attempt': 'Inherited NON_MENU_SCK_SUPPORT attempt-03 offline PASS; current document phase product/GUI attempts=0. Other issue counts stay in prior ledger.',
                'information_gain': True, 'stuck': True},
            'blocker_fingerprint': 'NATIVE_STAGE_FIXED_PYTHON314_MISSING_AND_LIVE_GROUNDING_UNRUN', 'information_gain': True}
        write_new(name, result)
    print(json.dumps({'plan': plan_ref, 'contract': contract_ref, 'handoff': ref('handoff.md'),
                      'native_schema_validation': 'NOT_RUN'}, ensure_ascii=False))

def verify(*, publication=False):
    baseline = load('baseline.json')
    for item in baseline['tracked_dirty']:
        file = ROOT / item['path']
        raw = file.read_bytes()
        if len(raw) != item['bytes'] or sha(raw) != item['sha256'] or oct(os.stat(file).st_mode & 0o777) != item['mode']:
            raise RuntimeError('Preexisting dirty work changed: ' + item['path'])
    for key in ['state', 'config', 'gui_ledger']:
        item = baseline[key]
        raw = (ROOT / item['path']).read_bytes()
        if len(raw) != item['bytes'] or sha(raw) != item['sha256']:
            raise RuntimeError('Protected input changed: ' + key)
    original = set((HERE / '.local/preexisting-status.z').read_bytes().split(b'\0')) - {b''}
    current = set(subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT).split(b'\0')) - {b''}
    outside = {entry for entry in current if not entry[3:].decode().startswith(CON + '/')}
    if outside != original:
        raise RuntimeError('Unexpected outside-scope Git status difference')
    contract_raw = (HERE / 'plan-contract.json').read_bytes()
    if (HERE / 'handoff.json').read_bytes() != contract_raw:
        raise RuntimeError('Handoff contract not byte-identical')
    freeze = load('plan-freeze.json')
    if freeze['plan']['sha256'] != ref('plan.md')['sha256'] or freeze['contract']['sha256'] != sha(contract_raw):
        raise RuntimeError('Frozen document drift')
    if not (HERE / 'handoff.md').read_text().startswith((HERE / 'handoff-prompt.txt').read_text().strip() + '\n\n'):
        raise RuntimeError('Handoff first paragraph does not equal prompt')
    for item in load('input-manifest.json')['entries']:
        raw = Path(item['absolute_path']).read_bytes()
        if len(raw) != item['bytes'] or sha(raw) != item['sha256']:
            raise RuntimeError('Input artifact drift: ' + item['absolute_path'])
    parsed = []
    for path in sorted(HERE.glob('*.json')):
        json.loads(path.read_bytes())
        parsed.append(path.name)
    for name in ['planner.result.json', 'handoff.result.json']:
        result = load(name)
        if result['plan_contract_sha256'] != sha(contract_raw) or result['validation_fact'] != 'NOT_RUN':
            raise RuntimeError('Result binding or native-status mismatch')
        for evidence in result['evidence_manifests']:
            raw = (ROOT / evidence['path']).read_bytes()
            if len(raw) != evidence['bytes'] or sha(raw) != evidence['sha256']:
                raise RuntimeError('Result evidence drift')
    result = {'kind': 'DOCUMENT_CONSISTENCY_ONLY_NOT_SCHEMA_OR_NATIVE_GATE', 'captured_at': now(),
        'contract_handoff_byte_equality': True, 'handoff_first_paragraph_exact_prompt': True,
        'plan_freeze_hashes_match': True, 'input_manifest_readback_pass': True,
        'preexisting_tracked_dirty_hashes_unchanged': len(baseline['tracked_dirty']),
        'outside_scope_git_status_unchanged': True, 'state_config_gui_ledger_unchanged': True,
        'json_parsed_documents': parsed, 'native_contract_validation': 'NOT_RUN',
        'native_result_validation': 'NOT_RUN', 'schema_validity': 'NOT_TOOL_VERIFIED',
        'product_tests_this_document_phase': 'NOT_RUN', 'live_e2e_this_document_phase': 'NOT_RUN'}
    output = HERE / ('.local/post-publication-verification.json' if publication else 'document-verification.json')
    output.write_bytes(encoded(result))
    print(json.dumps(result, ensure_ascii=False))

def manifest():
    entries = [ref(path.name) for path in sorted(HERE.iterdir())
               if path.is_file() and path.name not in ['document-manifest.json', 'git-publication.receipt.json']]
    (HERE / 'document-manifest.json').write_bytes(encoded({'kind': 'LOCAL_DOCUMENT_PACKAGE_MANIFEST',
        'created_at': now(), 'self_reference': False, 'git_publication_receipt_separate': True, 'entries': entries}))
    print(json.dumps({'manifest_entries': len(entries), 'manifest': ref('document-manifest.json')}))

if __name__ == '__main__':
    if ROOT != Path('/Users/hsiaojohnny/Documents/ChatGPT/Line_backup'):
        raise SystemExit('Unexpected root')
    action = sys.argv[1:]
    if action == ['create']:
        create()
    elif action == ['verify']:
        verify()
    elif action == ['verify-publication']:
        verify(publication=True)
    elif action == ['manifest']:
        manifest()
    else:
        raise SystemExit('usage: publish_documents.py create|verify|verify-publication|manifest')
