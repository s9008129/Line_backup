"""Capture a task-local, reproducible Node adapter test receipt."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
NODE = Path('/opt/homebrew/bin/node')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    run_id = uuid.uuid4().hex
    overrides = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'TMPDIR': str(TASK / 'fixtures'), 'LC_ALL': 'C'}
    env = dict(overrides)
    argv = [str(NODE), '--test', str(ROOT / 'tests/test_cua_adapter.mjs')]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    prefix = TASK / 'evidence' / f'node-adapter-{run_id}'
    stdout_path = prefix.with_suffix('.stdout')
    stderr_path = prefix.with_suffix('.stderr')
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    receipt = {
        'attempt_id': run_id, 'argv': argv, 'cwd': str(ROOT), 'started_at': started, 'ended_at': ended,
        'environment': overrides, 'exit_code': result.returncode, 'timed_out': False,
        'stdout_path': str(stdout_path.relative_to(ROOT)), 'stdout_bytes': len(result.stdout), 'stdout_sha256': sha(result.stdout),
        'stderr_path': str(stderr_path.relative_to(ROOT)), 'stderr_bytes': len(result.stderr), 'stderr_sha256': sha(result.stderr),
    }
    receipt_path = TASK / 'evidence' / f'node-adapter-{run_id}.json'
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'attempt_id': run_id, 'exit_code': result.returncode,
        'stdout_sha256': receipt['stdout_sha256'], 'stderr_sha256': receipt['stderr_sha256']}, sort_keys=True))
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
