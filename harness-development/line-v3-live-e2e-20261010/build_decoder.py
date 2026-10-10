"""Build the frozen ImageIO decoder into this task package and preserve exact receipts."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
EVIDENCE = TASK / 'evidence'
COMPILER = Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc')
SDK = Path('/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk')
SOURCE = ROOT / 'src/line_backup_batch/image_decode.swift'
OUTPUT = TASK / 'bin/image_decode'
CACHE = TASK / 'module-cache'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(COMPILER), '-sdk', str(SDK), '-target', 'arm64-apple-macosx26.5',
            '-module-cache-path', str(CACHE), '-O', str(SOURCE), '-o', str(OUTPUT)]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=180)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    (EVIDENCE / 'decoder-build.stdout').write_bytes(p.stdout)
    (EVIDENCE / 'decoder-build.stderr').write_bytes(p.stderr)
    receipt = {'argv': argv, 'cwd': str(ROOT), 'started_at': started, 'ended_at': ended,
               'exit_code': p.returncode, 'timed_out': False,
               'environment': {k: os.environ.get(k) for k in ('DEVELOPER_DIR', 'SDKROOT', 'TMPDIR', 'PATH') if k in os.environ},
               'source': {'path': str(SOURCE), 'sha256': digest(SOURCE)},
               'compiler': {'path': str(COMPILER), 'sha256': digest(COMPILER)},
               'sdk': {'path': str(SDK), 'resolved_path': str(SDK.resolve()), 'symlink': os.readlink(SDK) if SDK.is_symlink() else None}}
    if p.returncode == 0:
        receipt['output'] = {'path': str(OUTPUT), 'sha256': digest(OUTPUT), 'bytes': OUTPUT.stat().st_size}
        write_json(TASK / 'evidence/decoder-binding.json', {
            'binary_path': str(OUTPUT), 'binary_sha256': digest(OUTPUT),
            'source_sha256': digest(SOURCE), 'compiler_sha256': digest(COMPILER),
            'sdk_path': str(SDK), 'sdk_resolved_path': str(SDK.resolve()),
            'target': 'arm64-apple-macosx26.5'})
    write_json(EVIDENCE / 'decoder-build.receipt.json', receipt)
    print(json.dumps({'exit_code': p.returncode, 'timed_out': False,
                      'stdout_sha256': hashlib.sha256(p.stdout).hexdigest(),
                      'stderr_sha256': hashlib.sha256(p.stderr).hexdigest()}, sort_keys=True))
    return p.returncode

if __name__ == '__main__':
    raise SystemExit(main())
