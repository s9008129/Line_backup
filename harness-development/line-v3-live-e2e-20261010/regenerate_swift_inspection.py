#!/usr/bin/env python3
"""Deterministic rebuild of the six Swift inspection packets.

Why: the on-disk inner joins were stale byte copies from the old task (their
entry paths pointed at the old repo), so the Swift ProjectBackupBinding loader
rejected them ("Join evidence entries are malformed or outside the selected
project").  This script regenerates everything below <packet>/project through
the canonical builder in tests/test_project_binding.py::fixture(), replays each
case's mutation, re-runs the acceptance producer, asserts the expected
decision, rewrites the outer config/state/stdout copies and the
swift-inspection-inventory.json.

Run:  /Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python \
        harness-development/line-v3-live-e2e-20261010/regenerate_swift_inspection.py
"""
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TASK = REPO / 'harness-development' / 'line-v3-live-e2e-20261010'
FIXTURES = TASK / 'fixtures'
PACKETS = FIXTURES / 'swift-inspection'
INVENTORY = FIXTURES / 'swift-inspection-inventory.json'
CASES = ['eligible', 'verified', 'busy', 'unresolved', 'ambiguous', 'destination']
REQUESTS = {
    'eligible': ('2024-05-06', '2024-05-10', 182),
    'verified': ('2024-05-13', '2024-05-17', 57),
    'busy': ('2024-05-06', '2024-05-10', 182),
    'unresolved': ('2024-05-06', '2024-05-10', 182),
    'ambiguous': ('2024-05-13', '2024-05-17', 58),
    'destination': ('2024-05-06', '2024-05-10', 182),
}
EXPECTED = {
    'eligible': 'PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION',
    'verified': 'SKIP_VERIFIED',
    'busy': 'PROJECT_BUSY',
    'unresolved': 'BLOCKED_UNRESOLVED',
    'ambiguous': 'AMBIGUOUS_FINGERPRINT',
    'destination': 'BLOCKED_DESTINATION',
}
UNRESOLVED_TARGET = dict(start_date='2024-05-06', end_date='2024-05-10', expected_images=182)
DESTINATION_NAME = '2024-05-06_2024-05-10_182張'

os.environ['LINE_BACKUP_BATCH_TASK'] = str(TASK)
os.environ['LINE_BACKUP_INSPECTION_TEST_ROOT'] = str(FIXTURES)
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
sys.path.insert(0, str(REPO / 'src'))

spec = importlib.util.spec_from_file_location('fixture_builder', REPO / 'tests' / 'test_project_binding.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
assert builder.SEED == FIXTURES / 'project_binding_seed', builder.SEED
assert builder.REPO == REPO, builder.REPO
from line_backup_acceptance import project_binding as pb  # noqa: E402


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode() + b'\n'


def rebuild_case(case):
    packet = PACKETS / case
    project = packet / 'project'
    if project.exists():
        shutil.rmtree(project)
    project.mkdir()
    cfg, state = builder.fixture(project)
    start, end, count = REQUESTS[case]
    if case == 'busy':
        assert 'active_writer_id' in state, sorted(state)
        state['active_writer_id'] = 'writer'
    elif case == 'unresolved':
        run = copy.deepcopy(state['runs'][0])
        run.update(run_id='unresolved', workflow_outcome='FAILED', verification=None,
            fingerprint=dict(UNRESOLVED_TARGET))
        run['intent']['fingerprint'] = dict(UNRESOLVED_TARGET)
        state['runs'].append(run)
    elif case == 'destination':
        target = project / 'backups' / cfg['group_name'] / DESTINATION_NAME
        target.mkdir(parents=True)
        (target / 'existing').write_bytes(b'existing')
    (project / pb.CONFIG_PATH).write_bytes(canonical(cfg))
    (project / pb.STATE_PATH).write_bytes(canonical(state))
    report, code = pb.inspect(str(project), start, end, count)
    assert report.get('decision') == EXPECTED[case], (case, report.get('decision'), report)
    (packet / 'stdout.json').write_bytes(canonical(report))
    shutil.copyfile(project / pb.CONFIG_PATH, packet / 'config.json')
    shutil.copyfile(project / pb.STATE_PATH, packet / 'state.json')
    print(f'{case}: {report["decision"]} (exit {code})')


def strip_caches():
    for path in sorted(PACKETS.rglob('__pycache__'), reverse=True):
        shutil.rmtree(path)
    for path in PACKETS.rglob('*.pyc'):
        path.unlink()


def rebuild_inventory():
    previous = json.loads(INVENTORY.read_bytes())
    files = []
    for path in sorted(PACKETS.rglob('*')):
        if not (path.is_file() and not path.is_symlink()):
            continue
        raw = path.read_bytes()
        files.append(dict(bytes=len(raw), path=str(path.relative_to(REPO)), sha256=hashlib.sha256(raw).hexdigest()))
    files.sort(key=lambda entry: entry['path'])
    # 97 = 6 packets x (3 outer + inner config/state + 9 acceptance modules + join + proof)
    # plus the destination packet's extra 'existing' file.
    assert len(files) == 97, len(files)
    payload = dict(files=files, source_fixture_sha256=previous['source_fixture_sha256'],
        source_fixture_task=previous['source_fixture_task'])
    INVENTORY.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode() + b'\n')
    print(f'inventory: {len(files)} files')


def main():
    for case in CASES:
        rebuild_case(case)
    strip_caches()
    rebuild_inventory()


if __name__ == '__main__':
    main()
