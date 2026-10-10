#!/usr/bin/env python3
"""Archive exactly the obsolete implementation named by the user's handoff."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
OLD = ROOT / 'harness-development/catalog-diagnostic-continuity-replan-20261010'
TARGETS = [OLD / 'repair-01', OLD / 'tmp/smoke-repair']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(path):
    records = []
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            entry = Path(directory) / name
            info = entry.lstat()
            record = {'path': entry.relative_to(path).as_posix(),
                      'mode': stat.S_IMODE(info.st_mode)}
            if stat.S_ISDIR(info.st_mode):
                record['kind'] = 'directory'
            elif stat.S_ISREG(info.st_mode):
                record.update(kind='file', bytes=info.st_size, sha256=digest(entry))
            else:
                raise RuntimeError(f'Unsupported entry; no move: {entry}')
            records.append(record)
    return sorted(records, key=lambda record: record['path'])


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    if (TASK / 'archive-manifest.json').exists():
        raise RuntimeError('A cleanup manifest already exists; do not repeat this cleanup.')
    for path in TARGETS:
        assert path.is_dir() and not path.is_symlink(), path
        tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', str(path)], cwd=ROOT)
        assert not tracked, f'Tracked files would be moved: {path}'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = ROOT.parent / 'Line_backup_local_archives' / ('catalog-continuation-' + stamp)
    assert not archive.is_relative_to(ROOT) and not archive.exists()
    archive.mkdir(parents=True)
    assert archive.stat().st_dev == ROOT.stat().st_dev, 'Atomic same-volume move required'
    bindings = json.loads((ROOT / 'harness-development/line-e2e-fullscreen-repair-20261010/source-manifest.json').read_text())['records']
    protected = {row['path']: digest(ROOT / row['path']) for row in bindings}
    for raw in subprocess.check_output(['git', 'diff', '--name-only', '-z'], cwd=ROOT).split(b'\0'):
        if raw:
            relative = raw.decode()
            protected[relative] = digest(ROOT / relative)
    # Existing backup bytes are checked, without opening them through LINE.
    for file in (ROOT / 'backups').rglob('*'):
        if file.is_file():
            protected[str(file.relative_to(ROOT))] = digest(file)
    mappings = []
    for path in TARGETS:
        relative = str(path.relative_to(ROOT))
        mappings.append({'source_relative': relative,
                         'archive_relative': relative,
                         'entries': inventory(path)})
    manifest = {
        'format': 'user-authorized-local-archive-1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'repository': str(ROOT), 'archive_root': str(archive),
        'baseline_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'authorization': 'User: remove implementation related to results/implement-continuation-handoff/handoff.md safely.',
        'handoff_sha256': digest(OLD / 'results/implement-continuation-handoff/handoff.md'),
        'mappings': mappings, 'protected_sha256': protected,
        'historical_catalog_total': 5,
        'historical_result': 'Existing ledger records exit 2, 18 PASS / R17 FAIL / R20 NOT_RUN. No test rerun by this cleanup.',
        'status': 'PREPARED',
    }
    write_json(TASK / 'archive-manifest.json', manifest)
    write_json(archive / 'archive-manifest.json', manifest)
    copies = TASK / 'historical-ledger'
    copies.mkdir()
    for name in ['repair-ledger.json', 'repair-ledger.run-01.result.json']:
        source = OLD / 'repair-01/results' / name
        shutil.copy2(source, copies / name)
        assert digest(source) == digest(copies / name)
    moved = []
    try:
        for mapping in mappings:
            source = ROOT / mapping['source_relative']
            destination = archive / mapping['archive_relative']
            assert inventory(source) == mapping['entries'], 'Source changed before move'
            destination.parent.mkdir(parents=True, exist_ok=True)
            assert not destination.exists()
            os.rename(source, destination)
            moved.append((source, destination))
            assert inventory(destination) == mapping['entries'], 'Archive verification failed'
        changed = [relative for relative, before in protected.items()
                   if not (ROOT / relative).is_file() or digest(ROOT / relative) != before]
        if changed:
            raise RuntimeError('Protected content changed concurrently: ' + repr(changed))
    except Exception as error:
        for source, destination in reversed(moved):
            if destination.exists() and not source.exists():
                os.rename(destination, source)
        write_json(TASK / 'cleanup-failed.json', {'error': repr(error), 'rollback_attempted': True})
        raise
    files = [entry for mapping in mappings for entry in mapping['entries'] if entry['kind'] == 'file']
    receipt = {'format': 'local-cleanup-receipt-1', 'status': 'ARCHIVED',
               'archive_root': str(archive), 'files': len(files),
               'bytes': sum(entry['bytes'] for entry in files),
               'archive_files_hashes_and_modes_match': True,
               'original_implementation_paths_absent': all(not path.exists() for path in TARGETS),
               'protected_file_count': len(protected), 'protected_content_unchanged': True,
               'ocr_or_ui_or_e2e_performed': False, 'historical_budget_reset': False}
    write_json(TASK / 'cleanup-receipt.json', receipt)
    write_json(archive / 'cleanup-receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
