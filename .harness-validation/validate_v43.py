#!/usr/bin/env python3
import argparse, pathlib, sys

REQ = {
    'VERSION': '4.3.0',
    'MAX_MATERIAL_ATTEMPTS_PER_BLOCKER': '3',
    'MAX_CONSECUTIVE_NO_INFORMATION_GAIN': '2',
    'MAX_CONSECUTIVE_SAME_BLOCKER_GOAL_TURNS_AT_IMPASSE': '3',
}

def die(msg):
    print(f'FAIL: {msg}', file=sys.stderr)
    raise SystemExit(1)

def check_static(root: pathlib.Path):
    if (root/'VERSION').read_text().strip() != REQ['VERSION']:
        die('VERSION mismatch')
    c = (root/'dot-codex/policies/convergence-escalation.md').read_text()
    impl = (root/'dot-codex/prompts/04_implement_prompt.md').read_text()
    e2e = (root/'dot-codex/prompts/05_e2e_test_prompt.md').read_text()
    high = (root/'dot-codex/prompts/06_high_reasoning_review_prompt.md').read_text()
    routing = (root/'dot-codex/policies/workflow-routing.md').read_text()
    agents = (root/'dot-codex/AGENTS.md').read_text()

    required = [
        'MAX_MATERIAL_ATTEMPTS_PER_BLOCKER = 3',
        'MAX_CONSECUTIVE_NO_INFORMATION_GAIN = 2',
        'OSCILLATION_PATTERN = A -> B -> A',
        'budget belongs to `TASK_ID + BLOCKER_FINGERPRINT`',
        'Changing models does not reset it',
        'IMPLEMENTATION_STATUS: ESCALATED',
        'TASK_CLOSURE_STATUS: HIGH_REASONING_REVIEW_REQUIRED',
        'paused` only when the **user explicitly requests**',
        'blocked` when the same blocking condition',
    ]
    for needle in required:
        if needle not in c:
            die(f'missing convergence contract clause: {needle}')

    for needle in [
        'Codex usage: this is the primary stage where persistent `/goal` is appropriate.',
        'progress.md',
        'do not start a fourth local attempt',
        'Budget persists across model/provider/session switches.',
        'NEXT_STAGE: INDEPENDENT_ACCEPTANCE',
    ]:
        if needle not in impl:
            die(f'missing Stage04 clause: {needle}')

    for needle in [
        'Product mutation: forbidden',
        'Persistent implementation `/goal`: do not use for this stage',
        'Do not modify product code.',
        'one bounded targeted diagnostic replay',
        'Do not enter repair loops.',
    ]:
        if needle not in e2e:
            die(f'missing Stage05 clause: {needle}')

    for needle in [
        'logical capability role, not a fixed model product',
        'ESCALATION_DECISION: IMPLEMENTER_FIX',
        'ESCALATION_DECISION: TARGETED_DIAGNOSTIC',
        'ESCALATION_DECISION: PLANNER_REPLAN',
        'ESCALATION_DECISION: EXTERNAL_BLOCKER',
        'Do not reset budget merely because this reviewer is stronger or a different model.',
    ]:
        if needle not in high:
            die(f'missing Stage06 clause: {needle}')

    for field in [
        'PRIMARY_OUTCOME_STATUS', 'IMPLEMENTATION_STATUS', 'CORE_ACCEPTANCE_STATUS',
        'REQUIRED_VERIFICATION_STATUS', 'INDEPENDENT_ACCEPTANCE_STATUS', 'TASK_CLOSURE_STATUS'
    ]:
        if field not in routing:
            die(f'V4.2 status field lost: {field}')

    canonical = '\n'.join([
        agents, c, impl, e2e, high, routing,
        (root/'dot-codex/policies/model-routing.md').read_text(),
    ]).lower()
    forbidden = ['muse-spark-', 'deepseek-v', 'glm-', 'gpt-6-', 'gpt-5.6']
    hits = [x for x in forbidden if x in canonical]
    if hits:
        die('concrete model IDs leaked into canonical harness: ' + ', '.join(hits))

    def decision(attempts, no_gain, history, resolved=False):
        if resolved:
            return 'CONTINUE_OR_COMPLETE'
        if len(history) >= 3 and history[-3] == history[-1] and history[-2] != history[-1]:
            return 'ESCALATE_OSCILLATION'
        if no_gain >= 2:
            return 'ESCALATE_NO_INFORMATION_GAIN'
        if attempts >= 3:
            return 'ESCALATE_ATTEMPT_CEILING'
        return 'CONTINUE'

    fixtures = [
        ('attempt ceiling', decision(3,0,['A','A','A']), 'ESCALATE_ATTEMPT_CEILING'),
        ('no gain early stop', decision(2,2,['A','A']), 'ESCALATE_NO_INFORMATION_GAIN'),
        ('oscillation', decision(2,0,['A','B','A']), 'ESCALATE_OSCILLATION'),
        ('normal continue', decision(1,0,['A']), 'CONTINUE'),
        ('resolved', decision(3,2,['A','B','A'], True), 'CONTINUE_OR_COMPLETE'),
    ]
    for name, got, want in fixtures:
        if got != want:
            die(f'fixture {name}: got {got} want {want}')

    print('STATIC_CONTRACT=PASS')
    print('V42_STATUS_COMPATIBILITY=PASS')
    print('MODEL_AGNOSTIC=PASS')
    print('DETERMINISTIC_CONVERGENCE_FIXTURES=PASS')

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('root')
    args=ap.parse_args()
    check_static(pathlib.Path(args.root))
