"""Build and test Rev28 with the explicitly selected macOS 26.5 SDK."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
SWIFT = Path('/usr/bin/swift')
SDK = Path('/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    run_id = uuid.uuid4().hex
    overrides = {'PATH': '/usr/bin:/bin:/opt/homebrew/bin', 'TMPDIR': str(TASK / 'fixtures'),
        'SWIFTPM_MODULECACHE_OVERRIDE': str(TASK / 'module-cache-26.5'),
        'CLANG_MODULE_CACHE_PATH': str(TASK / 'module-cache-26.5/clang'),
        'LINE_BACKUP_INSPECTION_FIXTURES': str(TASK / 'fixtures/swift-inspection'), 'LC_ALL': 'C'}
    env = dict(overrides)
    argv = [str(SWIFT), 'test', '--package-path', str(ROOT / 'rev28'), '--sdk', str(SDK),
        '--scratch-path', str(TASK / 'swift-build-26.5')]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=1800)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    prefix = TASK / 'evidence' / f'swift-26.5-{run_id}'
    stdout_path = Path(str(prefix) + '.stdout')
    stderr_path = Path(str(prefix) + '.stderr')
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    receipt = {'attempt_id': run_id, 'argv': argv, 'cwd': str(ROOT), 'started_at': started, 'ended_at': ended,
        'environment': overrides, 'sdk': str(SDK), 'sdk_version': '26.5', 'exit_code': result.returncode,
        'timed_out': False, 'stdout_path': str(stdout_path.relative_to(ROOT)), 'stdout_bytes': len(result.stdout),
        'stdout_sha256': sha(result.stdout), 'stderr_path': str(stderr_path.relative_to(ROOT)),
        'stderr_bytes': len(result.stderr), 'stderr_sha256': sha(result.stderr)}
    receipt_path = TASK / 'evidence' / f'swift-26.5-{run_id}.json'
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'attempt_id': run_id, 'exit_code': result.returncode,
        'stdout_sha256': receipt['stdout_sha256'], 'stderr_sha256': receipt['stderr_sha256']}, sort_keys=True))
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
