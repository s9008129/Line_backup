"""Run Python regression groups with task-local outputs and exact argv/environment receipts."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PYTHON = Path('/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python')
FIXTURES = TASK / 'fixtures'

COMMANDS = [
    ('batch', ['-B', '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-p', 'test_batch_*.py', '-v']),
    ('project_binding', ['-B', '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-p', 'test_project_binding.py', '-v']),
    ('transaction_core', ['-B', '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-p', 'test_transaction_core.py', '-v']),
]

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    run_id = uuid.uuid4().hex
    env = os.environ.copy()
    overrides = {
        'LINE_BACKUP_BATCH_TASK': str(TASK),
        'LINE_BACKUP_INSPECTION_TEST_ROOT': str(FIXTURES),
        'PYTHONPATH': str(ROOT / 'src'),
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONHASHSEED': '0',
        'TMPDIR': str(FIXTURES),
        'GIT_OPTIONAL_LOCKS': '0',
    }
    env.update(overrides)
    records = []
    for name, args in COMMANDS:
        argv = [str(PYTHON), *args]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True)
        ended = dt.datetime.now(dt.timezone.utc).isoformat()
        prefix = TASK / 'evidence' / f'python-{name}-{run_id}'
        (prefix.with_suffix('.stdout')).write_bytes(p.stdout)
        (prefix.with_suffix('.stderr')).write_bytes(p.stderr)
        record = {'name': name, 'argv': argv, 'cwd': str(ROOT), 'started_at': started, 'ended_at': ended,
                  'exit_code': p.returncode, 'timed_out': False, 'environment_overrides': overrides,
                  'stdout_path': str(prefix.with_suffix('.stdout').relative_to(ROOT)),
                  'stdout_bytes': len(p.stdout), 'stdout_sha256': digest(p.stdout),
                  'stderr_path': str(prefix.with_suffix('.stderr').relative_to(ROOT)),
                  'stderr_bytes': len(p.stderr), 'stderr_sha256': digest(p.stderr)}
        records.append(record)
    summary = {'attempt_id': run_id, 'python': str(PYTHON), 'groups': records,
               'overall_exit_code': 0 if all(r['exit_code'] == 0 for r in records) else 1}
    path = TASK / 'evidence' / f'python-attempt-{run_id}.json'
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'attempt_id': run_id, 'overall_exit_code': summary['overall_exit_code'],
                      'groups': [{'name': r['name'], 'exit_code': r['exit_code'], 'stderr_sha256': r['stderr_sha256']} for r in records]}, sort_keys=True))
    return summary['overall_exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
