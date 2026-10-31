"""Explicit, project-local relocation receipts; original records remain immutable."""
from pathlib import Path
from .daily import (CORE_ROOT, need, directory, read_file, digest, strict_json,
                    create_json, image_inventory, reference, check_ref)


def load_receipt(root, group_raw):
    path = root / 'backup-records' / 'relocation.json'
    if not path.exists():
        return None
    raw = read_file(path)
    anchor = strict_json(read_file(root / 'backup-records/relocation-anchor.json'),
                         'INVALID_RELOCATION_ANCHOR')
    check_ref(anchor)
    need(anchor['sha256'] == digest(raw), 'RELOCATION_RECEIPT_CHANGED')
    receipt = strict_json(raw, 'INVALID_RELOCATION_RECEIPT')
    need(receipt['schema'] == 'line-backup-relocation/v1' and
         receipt['group_sha256'] == digest(group_raw) and
         receipt['destination'] == str(root) and
         receipt['device'] == root.stat().st_dev and
         receipt['inode'] == root.stat().st_ino, 'RELOCATION_BINDING_CHANGED')
    for relative, sha in receipt['records'].items():
        path = root / relative
        need(path.is_relative_to(root) and '..' not in Path(relative).parts and
             digest(read_file(path)) == sha, 'RELOCATED_RECORD_CHANGED')
    return receipt


def project(value, receipt):
    if isinstance(value, str):
        for old, new in receipt['prefixes']:
            if value == old or value.startswith(old + '/'):
                return new + value[len(old):]
    if isinstance(value, list):
        return [project(item, receipt) for item in value]
    if isinstance(value, dict):
        return {key: project(item, receipt) for key, item in value.items()}
    return value


def prepare(source, current, destination, evidence):
    """Compare both copies, preserve raw records, then publish a relocation receipt.

    Does not move directories, change task index, or grant foreground authority.
    Caller must hold an exclusive maintenance window (no concurrent GUI task).
    """
    source, current = directory(source), directory(current)
    need(not (source / 'backup-records/record-store.json').exists() and
         not (current / 'backup-records/record-store.json').exists(),
         'LEGACY_RECORDS_READ_ONLY_USE_RECORDS_ROOT')
    destination = Path(destination).absolute()
    evidence = Path(evidence).absolute()
    need(current.is_relative_to(CORE_ROOT) and destination.parent == CORE_ROOT and
         not destination.exists(), 'RELOCATION_TARGET_UNSAFE')
    need(evidence.is_relative_to(CORE_ROOT) and evidence == evidence.resolve() and
         not evidence.exists(), 'PROJECT_LOCAL_NEW_EVIDENCE_REQUIRED')
    def snapshot(root):
        result = {}
        for path in root.rglob('*'):
            need(not path.is_symlink(), 'RELOCATION_SYMLINK_REFUSED')
            if path.is_file() and path.name not in ('.DS_Store', '.lock'):
                result[str(path.relative_to(root))] = digest(read_file(path))
        return result
    before = snapshot(source)
    need(before == snapshot(current), 'RELOCATION_COPIES_DIFFER')
    group_raw = read_file(current / 'backup-records/group.json')
    group = strict_json(group_raw, 'INVALID_GROUP_RECORD')
    old = Path(group['destination'])
    need(old == source, 'RELOCATION_SOURCE_MISMATCH')
    records = {p: sha for p, sha in before.items() if p.startswith('backup-records/')}
    events = sorted((current / 'backup-records/events').iterdir())
    need(all(strict_json(read_file(p), 'INVALID_EVENT')['kind'] not in
             ('group-name', 'album-name', 'name-transaction', 'name-correction-plan')
             for p in events), 'NAMED_RELOCATION_REQUIRES_SEPARATE_PLAN')
    metadata = {}
    previous = None
    for index, path in enumerate(events, 1):
        raw = read_file(path)
        event = strict_json(raw, 'INVALID_EVENT')
        need(path.name == '%08d.json' % index and event['sequence'] == index and
             event['previous_sha256'] == previous and
             event['local_group_id'] == group['local_group_id'], 'EVENT_BINDING_CHANGED')
        previous = digest(raw)
        if event['kind'] == 'completion':
            data = event['data']
            relative = Path(data['destination']).relative_to(source)
            actual = image_inventory(current / relative)
            proof = data['proof']['manifest']
            need([(r['name'], r['size'], r['sha256']) for r in actual] ==
                 [(r['name'], r['size'], r['sha256']) for r in proof],
                 'RELOCATION_COMPLETION_CONTENT_CHANGED')
            for row in actual:
                metadata[str(destination / relative / row['name'])] = row
    evidence.mkdir(mode=0o700, parents=True, exist_ok=False)
    for relative in records:
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(read_file(current / relative))
    receipt = dict(schema='line-backup-relocation/v1', group_sha256=digest(group_raw),
        source=str(source), destination=str(destination), device=current.stat().st_dev,
        inode=current.stat().st_ino, records=records, through_sequence=len(events),
        prefixes=[[str(source), str(destination)], [str(source.parent), str(CORE_ROOT)]],
        completion_metadata=metadata, layout='FLAT_V1', old_copy_preserved=True)
    need(snapshot(source) == before and snapshot(current) == before, 'RELOCATION_CONTENT_CHANGED')
    create_json(evidence / 'receipt.json', receipt)
    create_json(current / 'backup-records/relocation.json', receipt)
    create_json(current / 'backup-records/relocation-anchor.json', reference(evidence / 'receipt.json'))
    return receipt
