"""Project-local permanent records. Photos and immutable history have separate lives."""
import contextlib
import fcntl
import os
from pathlib import Path
import stat
import uuid

from .daily import (CORE_ROOT, DailyRecords, DailyError, create_json, directory,
                    digest, encoded, need, read_file, reference, strict_json, sync_dir)

STORE_ROOT = CORE_ROOT / 'backup-records'
STORE_SCHEMA = 'line-backup-store/v1'


def history_expected(collection, *, include_legacy=True):
    active = CORE_ROOT / '.local/line-backup/active-task.json'
    if active.exists():
        task = strict_json(read_file(active), 'INVALID_ACTIVE_TASK')
        saved = Path(task.get('records_root', ''))
        if saved.is_absolute() and saved.is_relative_to(collection):
            return True
    return include_legacy and collection == STORE_ROOT and any((CORE_ROOT / 'backup').glob('**/backup-records/group.json'))


def local_path(value):
    path = Path(value).expanduser().absolute()
    need(path.is_relative_to(CORE_ROOT) and path != CORE_ROOT and
         path == path.resolve(), 'PROJECT_LOCAL_CANONICAL_RECORDS_REQUIRED')
    return path


@contextlib.contextmanager
def collection_lock(collection, *, create=False, migrating=False):
    collection = local_path(collection)
    if create and not collection.exists():
        need(not history_expected(collection, include_legacy=not migrating), 'KNOWN_RECORDS_MISSING_NO_EMPTY_HISTORY')
        directory(collection.parent)
        collection.mkdir(mode=0o700)
        sync_dir(collection.parent)
    directory(collection)
    fd = os.open(str(collection / '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'UNSAFE_LOCK')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield collection
    finally:
        os.close(fd)


def index(collection, *, allow_new=False):
    path = collection / 'index.json'
    if not path.exists():
        need(allow_new and set(p.name for p in collection.iterdir()) <= {'.lock', '.DS_Store'},
             'RECORD_INDEX_MISSING_NO_EMPTY_HISTORY')
        return dict(schema=STORE_SCHEMA, groups={})
    result = strict_json(read_file(path), 'INVALID_RECORD_INDEX')
    need(result.get('schema') == STORE_SCHEMA and isinstance(result.get('groups'), dict),
         'INVALID_RECORD_INDEX')
    for key, row in result['groups'].items():
        need(str(uuid.UUID(key)) == key and row.get('records_root') == str(collection / key),
             'INVALID_RECORD_INDEX')
        need(directory(collection / key) == collection / key, 'REGISTERED_RECORDS_MISSING')
    return result


def publish_index(collection, value):
    # A pending file is evidence of an interrupted publish, never an empty store.
    temporary = collection / '.index-pending.json'
    if temporary.exists():
        need(read_file(temporary) == encoded(value), 'RECORD_INDEX_PENDING_CONFLICT')
    else:
        create_json(temporary, value)
    os.replace(str(temporary), str(collection / 'index.json'))
    sync_dir(collection)
    need(read_file(collection / 'index.json') == encoded(value), 'RECORD_INDEX_READBACK_FAILED')


def load_metadata(records):
    metadata = strict_json(read_file(records / 'store.json'), 'INVALID_RECORD_STORE')
    need(metadata.get('schema') == STORE_SCHEMA and metadata.get('records_root') == str(records),
         'RECORD_STORE_BINDING_CHANGED')
    idx = index(records.parent)
    row = idx['groups'].get(metadata['local_group_id'])
    need(row is not None and row['metadata_sha256'] == digest(read_file(records / 'store.json')),
         'RECORD_STORE_NOT_REGISTERED')
    for name, sha in metadata.get('baseline', {}).items():
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts and
             digest(read_file(records / relative)) == sha, 'MIGRATED_RECORD_CHANGED')
    return metadata


def register(collection, idx, records):
    metadata = strict_json(read_file(records / 'store.json'), 'INVALID_RECORD_STORE')
    key = metadata['local_group_id']
    row = dict(records_root=str(records), metadata_sha256=digest(read_file(records / 'store.json')))
    need(key not in idx['groups'] or idx['groups'][key] == row, 'DUPLICATE_GROUP_RECORDS')
    updated = dict(idx, groups=dict(idx['groups'], **{key: row}))
    publish_index(collection, updated)


def preserve_reference(records, path):
    ref = reference(path)
    evidence = records / 'evidence'
    if Path(path).parent == evidence:
        return ref
    if not evidence.exists():
        evidence.mkdir(mode=0o700)
        sync_dir(records)
    need(directory(evidence) == evidence, 'PERMANENT_EVIDENCE_DIRECTORY_CHANGED')
    # Distinct observations may have identical pixels; retain source identity.
    target = evidence / digest(encoded(ref))
    raw = read_file(path)
    need(digest(raw) == ref['sha256'], 'EVIDENCE_DRIFT')
    if not target.exists():
        # create_json would alter source bytes, so publish the blob exclusively.
        temporary = evidence / ('.pending-' + uuid.uuid4().hex)
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(os.dup(fd), 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(str(temporary), str(target), follow_symlinks=False)
        finally:
            os.close(fd)
        temporary.unlink()
        sync_dir(evidence)
    need(read_file(target) == raw, 'PERMANENT_EVIDENCE_CHANGED')
    return reference(target)


def create_group(root, data, collection=STORE_ROOT):
    root = directory(root)
    need(not root.is_relative_to(local_path(collection)) and
         not local_path(collection).is_relative_to(root), 'RECORDS_MUST_BE_OUTSIDE_PHOTOS')
    # Never silently initialize over any legacy history in the chosen destination.
    need(not (root / 'backup-records').exists(), 'LEGACY_RECORDS_REQUIRE_MIGRATION')
    with collection_lock(collection, create=True) as collection:
        idx = index(collection, allow_new=True)
        need(not (collection / '.index-pending.json').exists(), 'RECORD_INDEX_PENDING')
        known = set(idx['groups']) | {'index.json', '.lock', '.DS_Store'}
        need(set(p.name for p in collection.iterdir()) <= known, 'UNREGISTERED_RECORDS_REQUIRE_RECONCILIATION')
        records = collection / str(uuid.uuid4())
        store = DailyRecords(root, records_root=records)
        group = store.initialize(**data)
        metadata = dict(schema=STORE_SCHEMA, records_root=str(records),
                        local_group_id=group['local_group_id'],
                        baseline={'group.json': digest(read_file(records / 'group.json'))})
        create_json(records / 'store.json', metadata)
        register(collection, idx, records)
        return dict(group, records_root=str(records))


def groups(collection=STORE_ROOT):
    collection = local_path(collection)
    if not collection.exists():
        need(not history_expected(collection), 'KNOWN_RECORDS_MISSING_NO_EMPTY_HISTORY')
        return dict(schema=STORE_SCHEMA, groups=[])
    with collection_lock(collection) as collection:
        idx = index(collection)
        need(not (collection / '.index-pending.json').exists(), 'RECORD_INDEX_PENDING')
        need(set(p.name for p in collection.iterdir()) - {'.DS_Store'} == set(idx['groups']) | {'index.json', '.lock'},
             'UNREGISTERED_RECORDS_REQUIRE_RECONCILIATION')
        result = []
        for key, row in sorted(idx['groups'].items()):
            memory = DailyRecords(records_root=row['records_root']).memory()
            result.append(dict(local_group_id=key, records_root=row['records_root'],
                               group=memory['group'], albums=memory['albums']))
        return dict(schema=STORE_SCHEMA, groups=result)


def migrate(root, collection=STORE_ROOT):
    """Copy and seal legacy records; the source is retained and redirected read-only.

    A maintenance window excluding legacy programs is required. Only this tool's
    locks are enforceable; no OS isolation or external-writer guarantees are made.
    """
    root = directory(root)
    collection = local_path(collection)
    need(not collection.is_relative_to(root) and not root.is_relative_to(collection),
         'RECORDS_MUST_BE_OUTSIDE_PHOTOS')
    source = root / 'backup-records'
    # Raw source access is deliberate here; ordinary entrypoints refuse redirects.
    store = DailyRecords(root, _maintenance=True)
    with collection_lock(collection, create=True, migrating=True) as collection, store.locked():
        # Validate the existing protection states before changing any entrypoint.
        store.status_map()
        key = store.group['local_group_id']
        records = collection / key
        plan_path = collection / ('.migration-' + key + '.json')
        if not (collection / 'index.json').exists() and plan_path.exists():
            need(set(p.name for p in collection.iterdir()) <= {'.lock', '.DS_Store', plan_path.name, key},
                 'RECORD_INDEX_MISSING_NO_EMPTY_HISTORY')
            idx = dict(schema=STORE_SCHEMA, groups={})
        else:
            idx = index(collection, allow_new=True)
        files = {}
        for path in source.rglob('*'):
            need(not path.is_symlink(), 'MIGRATION_SYMLINK_REFUSED')
            if path.is_file() and path.name not in ('.lock', '.DS_Store', 'record-store.json'):
                files[str(path.relative_to(source))] = read_file(path)
        baseline = {name: digest(raw) for name, raw in files.items()}
        plan = dict(schema=STORE_SCHEMA, source=str(source), records_root=str(records),
                    local_group_id=key, baseline=baseline)
        if key in idx['groups'] and not plan_path.exists():
            metadata = load_metadata(records)
            need(metadata.get('baseline') == baseline and
                 (source / 'record-store.json').exists(), 'MIGRATION_SOURCE_CHANGED')
            return dict(status='ALREADY_MIGRATED', local_group_id=key, records_root=str(records),
                        source_preserved=True)
        if plan_path.exists():
            need(strict_json(read_file(plan_path), 'INVALID_MIGRATION_PLAN') == plan,
                 'MIGRATION_SOURCE_CHANGED')
        else:
            need(key not in idx['groups'] and not records.exists(), 'DUPLICATE_GROUP_RECORDS')
            create_json(plan_path, plan)
        if not records.exists():
            records.mkdir(mode=0o700)
        for name, raw in files.items():
            target = records / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            directory(target.parent)
            if target.exists():
                need(read_file(target) == raw, 'MIGRATION_COPY_CONFLICT')
            else:
                fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_dir(target.parent)
        references = {}
        seen = set()

        def collect(value):
            if isinstance(value, dict):
                if {'path', 'bytes', 'sha256'} <= set(value):
                    token = (value['path'], value['sha256'])
                    if token not in seen:
                        seen.add(token)
                        path = Path(value['path'])
                        # Expired provenance is not upgraded into runtime evidence.
                        if path.is_relative_to(CORE_ROOT) and path.exists():
                            ref = reference(path)
                            need(ref == {k: value[k] for k in ('path', 'bytes', 'sha256')}, 'EVIDENCE_DRIFT')
                            references[value['path']] = preserve_reference(records, path)
                            raw = read_file(path)
                            if raw.lstrip()[:1] in (b'{', b'['):
                                try:
                                    nested = strict_json(raw, 'NON_JSON_PROVENANCE')
                                except DailyError:
                                    pass
                                else:
                                    collect(nested)
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(store.group)
        collect(store.events)
        # Preserve relocation anchor evidence too, without changing its bytes.
        for name, raw in files.items():
            if name.endswith('.json') and not name.startswith('events/'):
                collect(strict_json(raw, 'INVALID_MIGRATION_RECORD'))
        metadata = dict(plan, references=references,
                        relocation=store.relocation, historical_root=str(root))
        metadata.pop('source')
        if (records / 'store.json').exists():
            need(read_file(records / 'store.json') == encoded(metadata), 'MIGRATION_METADATA_CONFLICT')
        else:
            create_json(records / 'store.json', metadata)
        current_names = {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file() and
                         p.name not in ('.lock', '.DS_Store', 'record-store.json')}
        need(current_names == set(baseline) and
             all(digest(read_file(source / name)) == sha for name, sha in baseline.items()),
             'MIGRATION_SOURCE_CHANGED')
        redirect = dict(schema=STORE_SCHEMA, records_root=str(records), local_group_id=key)
        if (source / 'record-store.json').exists():
            need(read_file(source / 'record-store.json') == encoded(redirect), 'MIGRATION_REDIRECT_CONFLICT')
        else:
            create_json(source / 'record-store.json', redirect)
        register(collection, idx, records)
        plan_path.unlink()
        sync_dir(collection)
        return dict(status='MIGRATED', local_group_id=key, records_root=str(records),
                    source_preserved=True)
