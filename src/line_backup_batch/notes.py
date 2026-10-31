"""LINE Notes media ledger and offline verification.

This module records Agent-grounded observations. It never observes LINE,
clicks controls, grants GUI authority, or treats a filename/hash as source
identity. The permanent event log is the only business-state source.
"""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

from . import media_verify
from .daily import (DailyError, create_json, digest, encoded, read_file,
                    safe_component, strict_json, sync_dir)


CORE_ROOT = Path(__file__).resolve().parents[2]
COLLECTION_NAME = 'notes-backup-records'
ACTIVE_TASK_NAME = 'active-notes-task.json'
INDEX_SCHEMA = 'line-notes-index/v1'
STORE_SCHEMA = 'line-notes-store/v1'
LIST_SCHEMA = 'line-notes-list/v1'
IDENTITY_SCHEMA = 'line-notes-identity/v1'
MEMORY_SCHEMA = 'line-notes-memory/v1'

PHOTO = 'PHOTO'
VIDEO = 'VIDEO'
MEDIA_KINDS = (PHOTO, VIDEO)
STATUSES = ('COMPLETED', 'EXCLUDED', 'PENDING', 'PREVIOUSLY_INCOMPLETE',
            'UNKNOWN', 'PROTECTED_HISTORY')
OUTCOMES = ('STOPPED', 'NOT_SENT', 'DOWNLOAD_FINISHED', 'UNKNOWN')
LOCAL_VERIFIED = 'VERIFIED_PRESENT'
LOCAL_MISSING = 'LOCAL_MISSING'
LOCAL_CHANGED = 'LOCAL_CHANGED'
LOCAL_NOT_APPLICABLE = 'NOT_APPLICABLE'

PHOTO_SUFFIXES = frozenset(('.jpg', '.jpeg', '.png', '.heic', '.heif',
                            '.webp', '.tif', '.tiff', '.gif'))
VIDEO_SUFFIXES = frozenset(('.mp4', '.mov', '.m4v', '.avi', '.mkv'))
FFMPEG = media_verify.FFMPEG_PATH
FFPROBE = media_verify.FFPROBE_PATH
DEFAULT_STABILITY_INTERVAL = 0.2
DEFAULT_STALL_SECONDS = 120.0


class NotesError(ValueError):
    pass


class NotesMediaVerificationError(NotesError, DailyError):
    def __init__(self, code, evidence=None):
        super().__init__(code)
        self.code = code
        self.evidence = evidence if evidence is not None else {}


def need(condition, code):
    if not condition:
        raise NotesError(code)


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _entry(path):
    try:
        return os.lstat(str(path))
    except FileNotFoundError:
        return None


def _hex(value, code):
    need(isinstance(value, str) and bool(re.fullmatch(r'[0-9a-f]{64}', value)), code)
    return value


def _json_value(value, code):
    try:
        raw = encoded(value)
    except (TypeError, ValueError, UnicodeError, ArithmeticError,
            RecursionError) as exc:
        raise NotesError(code) from exc
    need(len(raw) <= 256 * 1024, code)
    return value


def _identity_key(namespace, payload):
    return digest(encoded(dict(schema=IDENTITY_SCHEMA, namespace=namespace,
                               payload=payload)))


def _validate_signals(signals):
    if signals is None:
        return None
    return _json_value(signals, 'INVALID_IDENTITY_SIGNALS')


def list_identity(*, visual_key, context_id=None, signals=None):
    need(isinstance(visual_key, str) and bool(visual_key.strip()) and
         len(visual_key) <= 4096, 'LIST_VISUAL_KEY_REQUIRED')
    identity = {'visual_key': visual_key}
    if context_id is not None:
        need(isinstance(context_id, str) and bool(context_id.strip()) and
             len(context_id) <= 4096, 'INVALID_CONTEXT_ID')
        identity['context_id'] = context_id
    if signals is not None:
        identity['signals'] = _validate_signals(signals)
    return _json_value(identity, 'INVALID_LIST_IDENTITY')


def post_identity(*, visual_key, signals=None):
    need(isinstance(visual_key, str) and bool(visual_key.strip()) and
         len(visual_key) <= 4096, 'POST_VISUAL_KEY_REQUIRED')
    identity = {'visual_key': visual_key}
    if signals is not None:
        identity['signals'] = _validate_signals(signals)
    return _json_value(identity, 'INVALID_POST_IDENTITY')


def media_identity(*, kind, visual_key, signals=None):
    need(kind in MEDIA_KINDS, 'INVALID_MEDIA_KIND')
    need(isinstance(visual_key, str) and bool(visual_key.strip()) and
         len(visual_key) <= 4096, 'MEDIA_VISUAL_KEY_REQUIRED')
    identity = {'kind': kind, 'visual_key': visual_key}
    if signals is not None:
        identity['signals'] = _validate_signals(signals)
    return _json_value(identity, 'INVALID_MEDIA_IDENTITY')


def list_key(identity):
    _check_identity_shape(identity, 'LIST')
    return _identity_key('LIST', identity)


def post_key(list_key_value, identity):
    _hex(list_key_value, 'INVALID_LIST_KEY')
    _check_identity_shape(identity, 'POST')
    return _identity_key('POST', dict(list_key=list_key_value, identity=identity))


def media_key(list_key_value, post_key_value, identity):
    _hex(list_key_value, 'INVALID_LIST_KEY')
    _hex(post_key_value, 'INVALID_POST_KEY')
    _check_identity_shape(identity, 'MEDIA')
    return _identity_key('MEDIA', dict(list_key=list_key_value,
                                       post_key=post_key_value,
                                       identity=identity))


def _check_identity_shape(identity, scope):
    need(isinstance(identity, dict), 'INVALID_%s_IDENTITY' % scope)
    allowed = {'visual_key', 'signals'}
    if scope == 'LIST':
        allowed.add('context_id')
    if scope == 'MEDIA':
        allowed.add('kind')
        need(identity.get('kind') in MEDIA_KINDS, 'INVALID_MEDIA_IDENTITY')
    need(set(identity) <= allowed and
         {'visual_key'} <= set(identity), 'INVALID_%s_IDENTITY' % scope)
    need(isinstance(identity['visual_key'], str) and
         bool(identity['visual_key'].strip()), 'INVALID_%s_IDENTITY' % scope)
    _json_value(identity, 'INVALID_%s_IDENTITY' % scope)


def _canonical_existing_directory(value, code):
    path = Path(value).expanduser().absolute()
    need(path == path.resolve(strict=True) and path.is_dir(), code)
    return path


def directory_info(path):
    path = Path(path).expanduser().absolute()
    before = _entry(path)
    need(before is not None and stat.S_ISDIR(before.st_mode),
         'CANONICAL_DIRECTORY_REQUIRED')
    need(path == path.resolve(strict=True), 'CANONICAL_DIRECTORY_REQUIRED')
    after = os.stat(str(path), follow_symlinks=False)
    need((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
         'DIRECTORY_CHANGED')
    return dict(path=str(path), device=after.st_dev, inode=after.st_ino)


def _ensure_core_directory(value):
    raw = Path(value).expanduser().absolute()
    need(not raw.is_symlink(), 'NOTES_PATH_SYMLINK_REFUSED')
    path = raw.resolve(strict=False)
    core = Path(CORE_ROOT).resolve(strict=True)
    need(path.is_relative_to(core) and path != core,
         'PROJECT_LOCAL_NOTES_PATH_REQUIRED')
    current = core
    for part in path.relative_to(core).parts:
        need(part not in ('', '.', '..'), 'INVALID_NOTES_PATH')
        candidate = current / part
        if _entry(candidate) is None:
            os.mkdir(str(candidate), 0o700)
            sync_dir(current)
        current = _canonical_existing_directory(
            candidate, 'CANONICAL_NOTES_PATH_REQUIRED')
    return current


def _read_json(path, code):
    return strict_json(read_file(path), code)


def _check_exact(data, keys, code):
    need(isinstance(data, dict) and set(data) == set(keys), code)
    return data


def _validate_page_overlap(previous_posts, current_posts, overlap_keys,
                           prior_keys=None):
    previous = [row['post_key'] for row in previous_posts]
    current = [row['post_key'] for row in current_posts]
    overlap = list(overlap_keys)
    need(bool(current), 'EMPTY_PAGE_NOT_ALLOWED')
    need(bool(previous), 'EMPTY_PAGE_NOT_ALLOWED')
    need(bool(overlap), 'PAGE_OVERLAP_EVIDENCE_REQUIRED')
    need(len(set(overlap)) == len(overlap), 'INVALID_OVERLAP_KEYS')
    need(len(overlap) <= len(previous) and len(overlap) <= len(current),
         'PAGE_OVERLAP_LENGTH_CHANGED')
    need(previous[-len(overlap):] == overlap,
         'OVERLAP_NOT_PREVIOUS_TAIL')
    need(current[:len(overlap)] == overlap, 'OVERLAP_NOT_NEXT_HEAD')
    earlier = set(prior_keys) if prior_keys is not None else set(previous)
    need((set(current) & earlier) <= set(overlap),
         'PAGE_DUPLICATE_REQUIRES_OVERLAP')


def _atomic_replace_json(path, value):
    path = Path(path)
    raw = encoded(value)
    existing = _entry(path)
    need(existing is None or stat.S_ISREG(existing.st_mode),
         'UNSAFE_JSON_TARGET')
    temporary = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(temporary),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(path))
    finally:
        os.close(fd)
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
    sync_dir(path.parent)
    need(read_file(path) == raw, 'JSON_READBACK_FAILED')


def _open_lock(path, create):
    path = Path(path)
    if not create:
        before = _entry(path)
        need(before is not None and stat.S_ISREG(before.st_mode) and
             before.st_nlink == 1, 'SAFE_LOCK_REQUIRED')
    fd = os.open(str(path),
                 os.O_RDWR | (os.O_CREAT if create else 0) | os.O_NOFOLLOW,
                 0o600)
    info = os.fstat(fd)
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'UNSAFE_LOCK')
    return fd


@contextlib.contextmanager
def _file_lock(path, create=False):
    fd = _open_lock(path, create)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def _evidence_directory(records, create=False):
    path = Path(records) / 'evidence'
    if create and _entry(path) is None:
        os.mkdir(str(path), 0o700)
        sync_dir(Path(records))
    return _canonical_existing_directory(path, 'EVIDENCE_DIRECTORY_CHANGED')


def _preserve_evidence(records, source):
    source = _evidence_source(source)
    raw = read_file(source)
    need(bool(raw), 'EMPTY_EVIDENCE')
    sha = digest(raw)
    evidence = _evidence_directory(records, create=True)
    target = evidence / sha
    if _entry(target) is None:
        temporary = evidence / ('.pending-' + uuid.uuid4().hex)
        fd = os.open(str(temporary),
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600)
        try:
            with os.fdopen(os.dup(fd), 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(str(temporary), str(target), follow_symlinks=False)
        finally:
            os.close(fd)
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()
        sync_dir(evidence)
    need(read_file(target) == raw, 'EVIDENCE_STORAGE_CHANGED')
    return dict(path=str(target), bytes=len(raw), sha256=sha)


def _evidence_source(value):
    """Validate and canonicalize one evidence source without writing a record."""
    source = Path(value).expanduser().absolute()
    core = Path(CORE_ROOT).resolve(strict=True)
    need(not source.is_symlink(), 'EVIDENCE_SYMLINK_REFUSED')
    source = source.resolve(strict=True)
    need(source.is_relative_to(core), 'PROJECT_LOCAL_EVIDENCE_REQUIRED')
    need(bool(read_file(source)), 'EMPTY_EVIDENCE')
    return source


def _check_evidence(records, ref, code='EVIDENCE_DRIFT'):
    _check_exact(ref, ('path', 'bytes', 'sha256'), code)
    path = Path(ref['path'])
    evidence = _evidence_directory(records)
    need(path.parent == evidence and path.name == ref['sha256'],
         'EVIDENCE_BINDING_CHANGED')
    raw = read_file(path)
    need(len(raw) == ref['bytes'] and digest(raw) == ref['sha256'], code)


def _read_regular(path, *, allowed_nlinks=(1,), code='FILE_CHANGED'):
    """Read one regular no-follow file while allowing a declared link count.

    Completion publication temporarily has two links to the same inode. The
    normal daily.read_file primitive deliberately refuses that state, so the
    publish transaction needs a bounded local reader that still checks that the
    opened inode and the path binding did not move while bytes were read.
    """
    path = Path(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and
             before.st_nlink in allowed_nlinks, code)
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read()
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size,
              before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size,
              after.st_mtime_ns, after.st_ctime_ns), code)
        current = os.stat(str(path), follow_symlinks=False)
        need((current.st_dev, current.st_ino) ==
             (after.st_dev, after.st_ino) and
             not Path(path).is_symlink(), code)
        return raw, after
    finally:
        os.close(fd)


def _new_unique_directory(parent, prefix):
    parent = _canonical_existing_directory(parent, 'NEW_DIRECTORY_PARENT_REQUIRED')
    for _ in range(100):
        path = parent / (prefix + uuid.uuid4().hex)
        try:
            os.mkdir(str(path), 0o700)
        except FileExistsError:
            continue
        sync_dir(parent)
        return _canonical_existing_directory(path, 'NEW_DIRECTORY_CHANGED')
    raise NotesError('NEW_DIRECTORY_ALLOCATION_EXHAUSTED')


def _unlink_regular(path, code):
    info = _entry(path)
    need(info is not None and stat.S_ISREG(info.st_mode), code)
    os.unlink(str(path))
    sync_dir(Path(path).parent)


def _link_no_replace(source, target):
    source, target = Path(source), Path(target)
    before = _entry(source)
    need(before is not None and stat.S_ISREG(before.st_mode) and
         before.st_nlink == 1, 'STAGING_FILE_CHANGED')
    need(_entry(target) is None, 'TARGET_ALREADY_EXISTS')
    need(source.parent.stat().st_dev == target.parent.stat().st_dev,
         'CROSS_DEVICE_PUBLISH_UNAVAILABLE')
    try:
        os.link(str(source), str(target), follow_symlinks=False)
    except FileExistsError as exc:
        raise NotesError('TARGET_ALREADY_EXISTS') from exc
    after_source = os.stat(str(source), follow_symlinks=False)
    after_target = os.stat(str(target), follow_symlinks=False)
    need((after_source.st_dev, after_source.st_ino) ==
         (after_target.st_dev, after_target.st_ino) and
         after_source.st_nlink == 2, 'PUBLISH_LINK_BINDING_CHANGED')
    sync_dir(source.parent)
    sync_dir(target.parent)
    return after_target


def _validate_evidence_ref_shape(ref, code):
    return _check_exact(ref, ('path', 'bytes', 'sha256'), code)


def _active_task_path():
    return Path(CORE_ROOT) / '.local/line-backup' / ACTIVE_TASK_NAME


def _read_active_hint():
    path = _active_task_path()
    if _entry(path) is None:
        return None
    need(not path.is_symlink(), 'ACTIVE_NOTES_TASK_SYMLINK_REFUSED')
    data = _read_json(path, 'INVALID_ACTIVE_NOTES_TASK')
    _check_exact(data, ('schema', 'records_root', 'local_list_id',
                        'session_id', 'updated_at'),
                 'INVALID_ACTIVE_NOTES_TASK')
    need(data['schema'] == 'line-notes-active-task/v1' and
         isinstance(data['records_root'], str) and
         isinstance(data['local_list_id'], str) and
         isinstance(data['session_id'], str) and
         isinstance(data['updated_at'], str), 'INVALID_ACTIVE_NOTES_TASK')
    return data


def _write_active_hint(records_root, local_list_id, session_id):
    path = _active_task_path()
    _ensure_core_directory(path.parent)
    data = dict(schema='line-notes-active-task/v1',
                records_root=str(Path(records_root)),
                local_list_id=local_list_id,
                session_id=session_id,
                updated_at=_utc_now())
    _atomic_replace_json(path, data)
    return data


def _active_references_within(collection):
    hint = _read_active_hint()
    if hint is None:
        return False
    records = Path(hint['records_root'])
    return records.is_absolute() and records.is_relative_to(collection)


def allocate_notes_component(parent, base):
    parent = _canonical_existing_directory(parent, 'CANONICAL_DIRECTORY_REQUIRED')
    base = safe_component(base)
    occupied = {path.name.casefold() for path in parent.iterdir()}
    for number in range(1, 10001):
        suffix = '' if number == 1 else ' (%d)' % number
        limit = 180 - len(suffix.encode('utf-8'))
        candidate = base
        while len(candidate.encode('utf-8')) > limit:
            candidate = candidate[:-1]
        candidate = candidate.rstrip(' .') + suffix
        need(bool(candidate), 'NAME_REQUIRES_USER_INPUT')
        if candidate.casefold() not in occupied:
            return candidate
    raise NotesError('NAME_ALLOCATION_EXHAUSTED')


class NotesCollection:
    """Collection of independent Notes list ledgers."""

    def __init__(self, collection=None):
        if collection is None:
            collection = Path(CORE_ROOT) / COLLECTION_NAME
        raw = Path(collection).expanduser().absolute()
        need(not raw.is_symlink(), 'NOTES_COLLECTION_SYMLINK_REFUSED')
        self.path = raw.resolve(strict=False)

    @contextlib.contextmanager
    def locked(self, create=False):
        collection = self.path
        if _entry(collection) is None:
            need(create, 'NOTES_COLLECTION_MISSING')
            need(not _active_references_within(collection),
                 'KNOWN_NOTES_RECORDS_MISSING_NO_EMPTY_HISTORY')
            _ensure_core_directory(collection)
            os.close(_open_lock(collection / '.lock', create=True))
            sync_dir(collection)
        collection = _canonical_existing_directory(
            collection, 'CANONICAL_NOTES_COLLECTION_REQUIRED')
        core = Path(CORE_ROOT).resolve(strict=True)
        need(collection.is_relative_to(core),
             'PROJECT_LOCAL_NOTES_PATH_REQUIRED')
        with _file_lock(collection / '.lock'):
            yield collection

    def _index_unlocked(self, collection):
        index_path = collection / 'index.json'
        need(_entry(index_path) is not None, 'NOTES_INDEX_MISSING')
        need(not (collection / '.index-pending.json').exists(),
             'NOTES_INDEX_PENDING')
        data = _read_json(index_path, 'INVALID_NOTES_INDEX')
        _check_exact(data, ('schema', 'lists'), 'INVALID_NOTES_INDEX')
        need(data['schema'] == INDEX_SCHEMA and isinstance(data['lists'], dict),
             'INVALID_NOTES_INDEX')
        for local_list_id, row in data['lists'].items():
            need(str(uuid.UUID(local_list_id)) == local_list_id,
                 'INVALID_NOTES_INDEX')
            _check_exact(row, ('records_root', 'store_sha256'),
                         'INVALID_NOTES_INDEX')
            records = Path(row['records_root'])
            need(records == collection / local_list_id,
                 'INVALID_NOTES_INDEX')
            need(records.is_dir() and records == records.resolve(strict=True),
                 'REGISTERED_NOTES_RECORDS_MISSING')
            _hex(row['store_sha256'], 'INVALID_NOTES_INDEX')
            need(digest(read_file(records / 'store.json')) ==
                 row['store_sha256'], 'NOTES_STORE_NOT_REGISTERED')
        known = set(data['lists']) | {'index.json', '.lock', '.DS_Store'}
        need(set(path.name for path in collection.iterdir()) <= known,
             'UNREGISTERED_NOTES_RECORDS_REQUIRE_RECONCILIATION')
        return data

    def _publish_index_unlocked(self, collection, value):
        raw = encoded(value)
        pending = collection / '.index-pending.json'
        if _entry(pending) is not None:
            need(read_file(pending) == raw, 'NOTES_INDEX_PENDING_CONFLICT')
        else:
            create_json(pending, value)
        os.replace(str(pending), str(collection / 'index.json'))
        sync_dir(collection)
        need(read_file(collection / 'index.json') == raw,
             'NOTES_INDEX_READBACK_FAILED')

    def _empty_index(self):
        return dict(schema=INDEX_SCHEMA, lists={})

    def lists(self):
        collection = self.path
        if _entry(collection) is None:
            need(not _active_references_within(collection),
                 'KNOWN_NOTES_RECORDS_MISSING_NO_EMPTY_HISTORY')
            return dict(schema=INDEX_SCHEMA, lists=[],
                        collection=str(collection),
                        active_hint=_read_active_hint())
        with self.locked() as collection:
            index = self._index_unlocked(collection)
            rows = []
            for local_list_id, row in sorted(index['lists'].items()):
                records = NotesRecords(row['records_root'],
                                       _collection_checked=True)
                rows.append(records.summary())
            return dict(schema=INDEX_SCHEMA, lists=rows,
                        collection=str(collection),
                        active_hint=_read_active_hint())

    def create(self, *, photo_root, display_name, identity, binding_evidence,
               history_scope_evidence, recovery_authorized=False):
        _check_identity_shape(identity, 'LIST')
        need(isinstance(display_name, str) and bool(display_name.strip()),
             'NAME_REQUIRES_USER_INPUT')
        collection = self.path
        photo_candidate = Path(photo_root).expanduser().absolute()
        need(not photo_candidate.is_relative_to(collection) and
             not collection.is_relative_to(photo_candidate),
             'RECORDS_MUST_BE_OUTSIDE_PHOTOS')
        binding_source = _evidence_source(binding_evidence)
        history_source = _evidence_source(history_scope_evidence)
        photo_root = _ensure_core_directory(photo_root)
        with self.locked(create=True) as collection:
            index_path = collection / 'index.json'
            if _entry(index_path) is None:
                need(set(path.name for path in collection.iterdir()) <=
                     {'.lock', '.DS_Store'},
                     'NOTES_INDEX_MISSING_NO_EMPTY_HISTORY')
                index = self._empty_index()
            else:
                index = self._index_unlocked(collection)
            key = list_key(identity)
            for row in index['lists'].values():
                store = _read_json(Path(row['records_root']) / 'store.json',
                                   'INVALID_NOTES_STORE')
                need(store.get('list_key') != key,
                     'NOTES_LIST_ALREADY_REGISTERED')
            local_list_id = str(uuid.uuid4())
            records = collection / local_list_id
            need(_entry(records) is None, 'NOTES_RECORDS_COLLISION')
            need(not photo_root.is_relative_to(collection) and
                 not collection.is_relative_to(photo_root),
                 'RECORDS_MUST_BE_OUTSIDE_PHOTOS')
            os.mkdir(str(records), 0o700)
            os.mkdir(str(records / 'events'), 0o700)
            os.mkdir(str(records / 'evidence'), 0o700)
            os.close(_open_lock(records / '.lock', create=True))
            sync_dir(records)
            sync_dir(collection)
            component = allocate_notes_component(
                photo_root, safe_component(display_name) + '_' + key[:8])
            list_directory = photo_root / component
            os.mkdir(str(list_directory), 0o700)
            sync_dir(photo_root)
            directory_binding = directory_info(list_directory)
            binding_ref = _preserve_evidence(records, binding_source)
            history_ref = _preserve_evidence(records, history_source)
            list_data = dict(schema=LIST_SCHEMA, version=1,
                             local_list_id=local_list_id, list_key=key,
                             identity=identity, display_name=display_name,
                             context_id=identity.get('context_id'),
                             recovery_authorized=bool(recovery_authorized),
                             created_at=_utc_now())
            create_json(records / 'list.json', list_data)
            list_sha = digest(read_file(records / 'list.json'))
            created = dict(schema='line-notes-created/v1', list_key=key,
                           identity=identity, display_name=display_name,
                           context_id=identity.get('context_id'),
                           recovery_authorized=bool(recovery_authorized),
                           photo_root=str(photo_root),
                           list_directory=str(list_directory),
                           directory_device=directory_binding['device'],
                           directory_inode=directory_binding['inode'],
                           binding_evidence=binding_ref,
                           history_scope_evidence=history_ref)
            event = dict(sequence=1, previous_sha256=None,
                         local_list_id=local_list_id, kind='created',
                         data=created)
            create_json(records / 'events/00000001.json', event)
            created_sha = digest(encoded(event))
            store = dict(schema=STORE_SCHEMA, version=1,
                         records_root=str(records),
                         local_list_id=local_list_id, list_key=key,
                         list_json_sha256=list_sha,
                         created_event_sha256=created_sha)
            create_json(records / 'store.json', store)
            row = dict(records_root=str(records),
                       store_sha256=digest(read_file(records / 'store.json')))
            index = dict(index, lists=dict(index['lists'],
                                           **{local_list_id: row}))
            self._publish_index_unlocked(collection, index)
            return NotesRecords(str(records),
                                _collection_checked=True).summary()


class NotesRecords:
    """One independent Notes list ledger rooted outside the photo area."""

    def __init__(self, records_root, _collection_checked=False,
                 _allow_injected_verification=False):
        need(type(_allow_injected_verification) is bool,
             'INVALID_INJECTED_VERIFICATION_SWITCH')
        self.records = Path(records_root).expanduser().absolute()
        self._loaded = False
        self._allow_injected_verification = _allow_injected_verification
        if not _collection_checked:
            self._check_registration()

    def _check_registration(self):
        need(self.records.is_dir() and
             self.records == self.records.resolve(strict=True),
             'CANONICAL_NOTES_RECORDS_REQUIRED')
        need(str(uuid.UUID(self.records.name)) == self.records.name,
             'INVALID_NOTES_RECORDS_DIRECTORY')
        collection = self.records.parent
        with NotesCollection(str(collection)).locked() as collection:
            index = NotesCollection(str(collection))._index_unlocked(collection)
            row = index['lists'].get(self.records.name)
            need(row is not None and Path(row['records_root']) == self.records,
                 'NOTES_RECORDS_NOT_REGISTERED')

    @contextlib.contextmanager
    def locked(self):
        records = _canonical_existing_directory(
            self.records, 'CANONICAL_NOTES_RECORDS_REQUIRED')
        need((records / 'events').is_dir() and
             (records / 'evidence').is_dir(), 'NOTES_RECORDS_STRUCTURE_CHANGED')
        with _file_lock(records / '.lock'):
            try:
                self._load(records)
            except NotesError:
                raise
            except (ArithmeticError, RecursionError) as exc:
                raise NotesError('NOTES_LEDGER_NUMERIC_INVALID') from exc
            yield

    def _load(self, records):
        list_data = _read_json(records / 'list.json', 'INVALID_NOTES_LIST')
        store = _read_json(records / 'store.json', 'INVALID_NOTES_STORE')
        _check_exact(list_data, ('schema', 'version', 'local_list_id',
                                 'list_key', 'identity', 'display_name',
                                 'context_id', 'recovery_authorized',
                                 'created_at'), 'INVALID_NOTES_LIST')
        _check_exact(store, ('schema', 'version', 'records_root',
                             'local_list_id', 'list_key',
                             'list_json_sha256', 'created_event_sha256'),
                     'INVALID_NOTES_STORE')
        need(list_data['schema'] == LIST_SCHEMA and list_data['version'] == 1 and
             store['schema'] == STORE_SCHEMA and store['version'] == 1,
             'UNSUPPORTED_NOTES_RECORD_SCHEMA')
        need(list_data['local_list_id'] == records.name and
             store['local_list_id'] == records.name and
             store['records_root'] == str(records) and
             store['list_key'] == list_data['list_key'] and
             store['list_json_sha256'] == digest(read_file(records / 'list.json')),
             'NOTES_METADATA_BINDING_CHANGED')
        _hex(list_data['list_key'], 'INVALID_NOTES_LIST')
        need(list_key(list_data['identity']) == list_data['list_key'],
             'NOTES_LIST_IDENTITY_CHANGED')
        need(isinstance(list_data['display_name'], str) and
             bool(list_data['display_name'].strip()), 'INVALID_NOTES_LIST')
        need(list_data['context_id'] == list_data['identity'].get('context_id') and
             type(list_data['recovery_authorized']) is bool,
             'INVALID_NOTES_LIST')
        self.records = records
        self.list_data = list_data
        self.store = store
        event_root = records / 'events'
        need(not event_root.is_symlink(),
             'NOTES_EVENT_PATH_SYMLINK_REFUSED')
        event_root = _canonical_existing_directory(
            event_root, 'NOTES_EVENT_DIRECTORY_CHANGED')
        event_files = []
        for path in sorted(event_root.iterdir()):
            event_files.append(path)
        need(event_files, 'EMPTY_NOTES_LEDGER')
        events = []
        previous = None
        for index, path in enumerate(event_files, 1):
            need(path.name == '%08d.json' % index,
                 'NOTES_EVENT_SEQUENCE_OR_PENDING_WRITE')
            raw = read_file(path)
            event = strict_json(raw, 'INVALID_NOTES_EVENT')
            _check_exact(event, ('sequence', 'previous_sha256',
                                 'local_list_id', 'kind', 'data'),
                         'INVALID_NOTES_EVENT')
            need(event['sequence'] == index and
                 event['previous_sha256'] == previous and
                 event['local_list_id'] == records.name,
                 'NOTES_EVENT_BINDING_CHANGED')
            self._validate_event(event)
            events.append(event)
            previous = digest(raw)
        need(events[0]['kind'] == 'created' and
             store['created_event_sha256'] == digest(encoded(events[0])),
             'NOTES_CREATED_EVENT_CHANGED')
        need(sum(event['kind'] == 'created' for event in events) == 1,
             'NOTES_CREATED_EVENT_CHANGED')
        created = events[0]['data']
        need(created['list_key'] == list_data['list_key'] and
             created['identity'] == list_data['identity'] and
             created['display_name'] == list_data['display_name'] and
             created['context_id'] == list_data['context_id'] and
             created['recovery_authorized'] ==
             list_data['recovery_authorized'],
             'NOTES_CREATED_EVENT_CHANGED')
        self.records = records
        self.list_data = list_data
        self.store = store
        self.events = events
        self.previous = previous
        self._loaded = True
        self._validate_destination_chain()
        self._validate_event_graph()

    def _validate_event(self, event):
        kind, data = event['kind'], event['data']
        need(isinstance(kind, str) and isinstance(data, dict),
             'INVALID_NOTES_EVENT')
        if kind == 'created':
            _check_exact(data, ('schema', 'list_key', 'identity',
                                'display_name', 'context_id',
                                'recovery_authorized', 'photo_root',
                                'list_directory', 'directory_device',
                                'directory_inode', 'binding_evidence',
                                'history_scope_evidence'),
                         'INVALID_CREATED_EVENT')
            need(data['schema'] == 'line-notes-created/v1' and
                 list_key(data['identity']) == data['list_key'] and
                 isinstance(data['display_name'], str) and
                 isinstance(data['context_id'], (str, type(None))) and
                 type(data['recovery_authorized']) is bool and
                 type(data['directory_device']) is int and
                 type(data['directory_inode']) is int and
                 isinstance(data['photo_root'], str) and
                 isinstance(data['list_directory'], str),
                 'INVALID_CREATED_EVENT')
            _check_evidence(self.records, data['binding_evidence'])
            _check_evidence(self.records, data['history_scope_evidence'])
            need(Path(data['list_directory']).parent == Path(data['photo_root']),
                 'INVALID_CREATED_EVENT')
        elif kind == 'binding':
            _check_exact(data, ('schema', 'session_id', 'context_id',
                                'observation', 'handoff'),
                         'INVALID_BINDING_EVENT')
            need(data['schema'] == 'line-notes-binding/v1' and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_BINDING_EVENT')
            _check_evidence(self.records, data['observation'])
            _check_evidence(self.records, data['handoff'])
        elif kind == 'destination':
            _check_exact(data, ('schema', 'photo_root', 'previous_root',
                                'list_directory', 'previous_list_directory',
                                'directory_device', 'directory_inode',
                                'session_id', 'evidence'),
                         'INVALID_DESTINATION_EVENT')
            need(data['schema'] == 'line-notes-destination/v1' and
                 Path(data['list_directory']).parent == Path(data['photo_root']) and
                 isinstance(data['previous_root'], str) and
                 isinstance(data['previous_list_directory'], str) and
                 Path(data['previous_list_directory']).parent ==
                 Path(data['previous_root']) and
                 type(data['directory_device']) is int and
                 type(data['directory_inode']) is int and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_DESTINATION_EVENT')
            _check_evidence(self.records, data['evidence'])
        elif kind == 'scan':
            need(data.get('schema') == 'line-notes-scan/v1' and
                 data.get('action') in ('START', 'COMPLETE') and
                 isinstance(data.get('scan_id'), str) and
                 bool(data.get('scan_id')) and
                 isinstance(data.get('session_id'), str) and
                 bool(data.get('session_id')), 'INVALID_SCAN_EVENT')
            _check_evidence(self.records, data.get('evidence'))
            if data['action'] == 'START':
                _check_exact(data, ('schema', 'action', 'scan_id',
                                    'session_id', 'evidence'),
                             'INVALID_SCAN_EVENT')
            else:
                _check_exact(data, ('schema', 'action', 'scan_id',
                                    'session_id', 'evidence', 'posts'),
                             'INVALID_SCAN_EVENT')
                need(isinstance(data['posts'], list), 'INVALID_SCAN_EVENT')
                for order, row in enumerate(data['posts']):
                    _check_exact(row, ('post_key', 'identity',
                                       'date_summary', 'source_order'),
                                 'INVALID_SCAN_EVENT')
                    need(row['source_order'] == order and
                         post_key(self.list_data['list_key'], row['identity']) ==
                         row['post_key'] and
                         isinstance(row['date_summary'], str),
                         'INVALID_SCAN_EVENT')
        elif kind == 'page':
            _check_exact(data, ('schema', 'scan_id', 'session_id',
                                'page_index', 'top_reached',
                                'bottom_reached', 'overlap_keys',
                                'posts', 'evidence'), 'INVALID_PAGE_EVENT')
            need(data['schema'] == 'line-notes-page/v1' and
                 isinstance(data['scan_id'], str) and
                 bool(data['scan_id']) and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']) and
                 type(data['page_index']) is int and data['page_index'] >= 0 and
                 type(data['top_reached']) is bool and
                 type(data['bottom_reached']) is bool and
                 isinstance(data['overlap_keys'], list) and
                 all(isinstance(key, str) for key in data['overlap_keys']),
                 'INVALID_PAGE_EVENT')
            _check_evidence(self.records, data['evidence'])
            need(isinstance(data['posts'], list), 'INVALID_PAGE_EVENT')
            seen = set()
            for row in data['posts']:
                _check_exact(row, ('post_key', 'identity', 'date_summary',
                                   'source_order'), 'INVALID_PAGE_EVENT')
                need(row['post_key'] not in seen and
                     post_key(self.list_data['list_key'], row['identity']) ==
                     row['post_key'] and
                     type(row['source_order']) is int and
                     row['source_order'] >= 0 and
                     isinstance(row['date_summary'], str),
                     'INVALID_PAGE_EVENT')
                seen.add(row['post_key'])
            need(len(set(data['overlap_keys'])) == len(data['overlap_keys']),
                 'INVALID_PAGE_EVENT')
        elif kind == 'post':
            required = {'schema', 'post_key', 'date_summary',
                        'text_sha256', 'media_count', 'no_media', 'evidence'}
            need(isinstance(data, dict) and required <= set(data) and
                 set(data) <= required | {'scan_id'},
                 'INVALID_POST_EVENT')
            need(data['schema'] == 'line-notes-post/v1' and
                 _is_hex(data['post_key']) and
                 isinstance(data['date_summary'], str) and
                 (data['text_sha256'] is None or _is_hex(data['text_sha256'])) and
                 type(data['media_count']) is int and data['media_count'] >= 0 and
                 type(data['no_media']) is bool and
                 data['no_media'] == (data['media_count'] == 0),
                 'INVALID_POST_EVENT')
            if 'scan_id' in data:
                need(isinstance(data['scan_id'], str) and
                     bool(data['scan_id'].strip()), 'INVALID_POST_EVENT')
            _check_evidence(self.records, data['evidence'])
        elif kind == 'media':
            required = {'schema', 'post_key', 'items', 'missing', 'evidence'}
            need(isinstance(data, dict) and required <= set(data) and
                 set(data) <= required | {'scan_id'},
                 'INVALID_MEDIA_EVENT')
            need(data['schema'] == 'line-notes-media-inventory/v1' and
                 _is_hex(data['post_key']) and
                 isinstance(data['items'], list) and
                 isinstance(data['missing'], list), 'INVALID_MEDIA_EVENT')
            if 'scan_id' in data:
                need(isinstance(data['scan_id'], str) and
                     bool(data['scan_id'].strip()), 'INVALID_MEDIA_EVENT')
            _check_evidence(self.records, data['evidence'])
            seen = set()
            seen_orders = set()
            for order, row in enumerate(data['items']):
                _check_exact(row, ('media_key', 'identity', 'source_order'),
                             'INVALID_MEDIA_EVENT')
                need(row['media_key'] not in seen and
                     _is_nonnegative_int(row['source_order']) and
                     row['source_order'] not in seen_orders and
                     media_key(self.list_data['list_key'], data['post_key'],
                               row['identity']) == row['media_key'],
                     'INVALID_MEDIA_EVENT')
                seen.add(row['media_key'])
                seen_orders.add(row['source_order'])
            for row in data['missing']:
                _check_exact(row, ('media_key', 'source_order', 'reason'),
                             'INVALID_MEDIA_EVENT')
                need(_is_hex(row['media_key']) and
                     _is_nonnegative_int(row['source_order']) and
                     row['source_order'] not in seen_orders and
                     isinstance(row['reason'], str) and
                     bool(row['reason'].strip()), 'INVALID_MEDIA_EVENT')
                seen_orders.add(row['source_order'])
        elif kind == 'intent':
            required = ('schema', 'media_key', 'post_key', 'identity',
                        'attempt_id', 'session_id', 'destination',
                        'directory_device', 'directory_inode',
                        'save_all_limit', 'save_all_count', 'recovery_of',
                        'recovery_evidence')
            need(isinstance(data, dict) and
                 set(required) <= set(data) and
                 set(data) <= set(required) | {'scan_id'},
                 'INVALID_INTENT_EVENT')
            if 'scan_id' in data:
                need(isinstance(data['scan_id'], str) and
                     bool(data['scan_id'].strip()), 'INVALID_INTENT_EVENT')
            need(data['schema'] == 'line-notes-intent/v1' and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 media_key(self.list_data['list_key'], data['post_key'],
                           data['identity']) == data['media_key'] and
                 isinstance(data['attempt_id'], str) and
                 isinstance(data['session_id'], str) and
                 type(data['directory_device']) is int and
                 type(data['directory_inode']) is int and
                 isinstance(data['destination'], str) and
                 Path(data['destination']).is_absolute() and
                 Path(data['destination']).name.startswith('.line-notes-incoming-') and
                 data['save_all_limit'] == 1 and
                 data['save_all_count'] == 0,
                 'INVALID_INTENT_EVENT')
            if data['recovery_evidence'] is not None:
                _check_evidence(self.records, data['recovery_evidence'])
        elif kind == 'outcome':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'outcome', 'evidence'), 'INVALID_OUTCOME_EVENT')
            need(data['schema'] == 'line-notes-outcome/v1' and
                 isinstance(data['attempt_id'], str) and
                 _is_hex(data['media_key']) and
                 data['outcome'] in OUTCOMES, 'INVALID_OUTCOME_EVENT')
            _check_evidence(self.records, data['evidence'])
        elif kind == 'reconcile':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'result', 'evidence'), 'INVALID_RECONCILE_EVENT')
            need(data['schema'] == 'line-notes-reconcile/v1' and
                 isinstance(data['attempt_id'], str) and
                 _is_hex(data['media_key']) and
                 data['result'] in OUTCOMES, 'INVALID_RECONCILE_EVENT')
            _check_evidence(self.records, data['evidence'])
        elif kind == 'verification':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'post_key', 'kind', 'source', 'manifest',
                                'manifest_sha256', 'verification',
                                'verified_at'), 'INVALID_VERIFICATION_EVENT')
            need(data['schema'] == 'line-notes-verification/v1' and
                 isinstance(data['attempt_id'], str) and
                 bool(data['attempt_id']) and
                 _is_hex(data['media_key']) and
                 _is_hex(data['post_key']) and
                 data['kind'] in MEDIA_KINDS and
                 isinstance(data['source'], dict) and
                 isinstance(data['manifest'], list) and
                 len(data['manifest']) == 1 and
                 data['manifest'][0] == data['source'] and
                 isinstance(data['verification'], dict) and
                 bool(data['verification']) and
                 isinstance(data['verified_at'], str) and
                 bool(data['verified_at']) and
                 data['manifest_sha256'] ==
                 digest(encoded(data['manifest'])), 'INVALID_VERIFICATION_EVENT')
            self._validate_source_row(data['source'],
                                      'INVALID_VERIFICATION_SOURCE')
            _json_value(data['verification'], 'INVALID_VERIFICATION_RESULT')
            _validate_verification_payload(
                data['kind'], data['source'], data['verification'],
                allow_injected=self._allow_injected_verification)
        elif kind == 'publish-plan':
            _check_exact(data, ('schema', 'transaction_id', 'attempt_id',
                                'media_key', 'post_key', 'verification_sequence',
                                'verification_sha256', 'source',
                                'list_directory', 'target_directory',
                                'target_name', 'number', 'extension',
                                'target_directory_existed'),
                         'INVALID_PUBLISH_PLAN')
            need(data['schema'] == 'line-notes-publish-plan/v1' and
                 isinstance(data['transaction_id'], str) and
                 isinstance(data['attempt_id'], str) and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 type(data['verification_sequence']) is int and
                 type(data['number']) is int and data['number'] > 0 and
                 isinstance(data['target_name'], str) and
                 Path(data['target_name']).name == data['target_name'] and
                 isinstance(data['source'], dict) and
                 isinstance(data['list_directory'], str) and
                 isinstance(data['target_directory'], str) and
                 isinstance(data['extension'], str) and
                 data['target_name'].endswith(data['extension']) and
                 _is_hex(data['verification_sha256']) and
                 type(data['target_directory_existed']) is bool,
                 'INVALID_PUBLISH_PLAN')
        elif kind == 'publish-progress':
            need(data.get('schema') == 'line-notes-publish-progress/v1' and
                 isinstance(data.get('transaction_id'), str) and
                 data.get('action') in ('DIRECTORY_READY', 'FILE_LINKED',
                                        'SOURCE_REMOVED'),
                 'INVALID_PUBLISH_PROGRESS')
            _json_value(data, 'INVALID_PUBLISH_PROGRESS')
        elif kind == 'completion':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'post_key', 'transaction_id',
                                'verification_sequence',
                                'verification_sha256', 'destination',
                                'target_file', 'target_directory', 'naming',
                                'source_manifest', 'verification'),
                         'INVALID_COMPLETION_EVENT')
            need(data['schema'] == 'line-notes-completion/v1' and
                 isinstance(data['target_file'], dict) and
                 isinstance(data['target_directory'], dict) and
                 isinstance(data['naming'], dict), 'INVALID_COMPLETION_EVENT')
        elif kind in ('exclusion', 'protection'):
            _check_exact(data, ('schema', 'media_key', 'reason', 'evidence'),
                         'INVALID_%s_EVENT' % kind.upper())
            need(data['schema'] == 'line-notes-%s/v1' % kind and
                 _is_hex(data['media_key']) and
                 isinstance(data['reason'], str) and
                 bool(data['reason'].strip()), 'INVALID_%s_EVENT' % kind.upper())
            _check_evidence(self.records, data['evidence'])
        else:
            raise NotesError('UNKNOWN_NOTES_EVENT_KIND')

    def _validate_destination_chain(self):
        created = self.events[0]['data']
        root = created['photo_root']
        list_directory = created['list_directory']
        for event in self.events[1:]:
            if event['kind'] != 'destination':
                continue
            data = event['data']
            need(data['previous_root'] == root and
                 data['previous_list_directory'] == list_directory,
                 'DESTINATION_CHAIN_CHANGED')
            root, list_directory = data['photo_root'], data['list_directory']
        self.current_photo_root = Path(root)
        self.current_list_directory = Path(list_directory)

    def _validate_source_row(self, row, code):
        _check_exact(row, ('path', 'name', 'device', 'inode', 'nlink',
                           'size', 'sha256', 'mtime_ns', 'ctime_ns'), code)
        need(isinstance(row['path'], str) and Path(row['path']).is_absolute() and
             isinstance(row['name'], str) and Path(row['name']).name ==
             row['name'] and not row['name'].startswith('.') and
             type(row['device']) is int and type(row['inode']) is int and
             row['nlink'] == 1 and type(row['size']) is int and row['size'] > 0 and
             _is_hex(row['sha256']) and type(row['mtime_ns']) is int and
             type(row['ctime_ns']) is int, code)
        return row

    def _validate_event_graph(self):
        """Reject internally inconsistent event graphs before projecting them."""
        latest, scans = self._open_scan()
        for scan_id, scan in scans.items():
            if scan['complete'] is None:
                continue
            pages = scan['pages']
            need(pages, 'EMPTY_SCAN_COMPLETION')
            need(pages[0]['data']['top_reached'] is True,
                 'SCAN_TOP_NOT_REACHED')
            need(pages[-1]['data']['bottom_reached'] is True,
                 'SCAN_BOTTOM_NOT_REACHED')

        complete_posts = {}
        for scan_id, scan in scans.items():
            if scan['complete'] is not None:
                complete_posts[scan_id] = {
                    row['post_key']
                    for row in scan['complete']['data']['posts']
                }

        bound_details = {}
        bound_media = set()
        for event in self.events:
            data = event['data']
            if event['kind'] == 'post':
                bound = data.get('scan_id')
                if bound is None:
                    continue
                binding = (data['post_key'], bound)
                need(binding not in bound_details,
                     'POST_DETAIL_ALREADY_RECORDED')
                bound_details[binding] = data
            elif event['kind'] == 'media':
                bound = data.get('scan_id')
                if bound is None:
                    continue
                binding = (data['post_key'], bound)
                need(binding not in bound_media,
                     'MEDIA_INVENTORY_ALREADY_RECORDED')
                bound_media.add(binding)
                detail = bound_details.get(binding)
                need(detail is not None,
                     'POST_DETAIL_SCAN_BINDING_REQUIRED')
                need(len(data['items']) + len(data['missing']) ==
                     detail['media_count'],
                     'MEDIA_COUNT_DETAIL_CHANGED')
                orders = sorted(
                    row['source_order']
                    for row in data['items'] + data['missing'])
                need(orders == list(range(detail['media_count'])),
                     'MEDIA_COUNT_DETAIL_CHANGED')

        for event in self.events:
            if event['kind'] not in ('post', 'media'):
                continue
            data = event['data']
            bound = data.get('scan_id')
            if bound is None:
                # Pre-scan_id ledgers remain readable, but intent() below
                # refuses to dispatch from an unbound detail/inventory.
                continue
            scan = scans.get(bound)
            code = '%s_SCAN_BINDING_CHANGED' % event['kind'].upper()
            need(scan is not None and scan['complete'] is not None,
                 code)
            need(scan['complete']['sequence'] < event['sequence'],
                 code)
            need(data['post_key'] in complete_posts.get(bound, set()),
                 code)
            if event['kind'] == 'media':
                details = [
                    candidate for candidate in self.events
                    if candidate['kind'] == 'post' and
                    candidate['data']['post_key'] == data['post_key'] and
                    candidate['sequence'] < event['sequence']
                ]
                detail = details[-1]['data'] if details else None
                need(detail is not None and detail.get('scan_id') == bound,
                     'POST_DETAIL_SCAN_BINDING_REQUIRED')

        for event in self.events:
            if event['kind'] != 'intent':
                continue
            bound = event['data'].get('scan_id')
            if bound is None:
                # Legacy intents remain readable, but verify/resume refuse to
                # use them because their target scan cannot be proven.
                continue
            scan = scans.get(bound)
            need(scan is not None and scan['complete'] is not None and
                 scan['complete']['sequence'] < event['sequence'],
                 'INTENT_SCAN_BINDING_CHANGED')

        seen_posts = set()
        for event in self.events:
            if event['kind'] == 'page':
                seen_posts.update(row['post_key']
                                  for row in event['data']['posts'])
            elif event['kind'] == 'scan' and event['data']['action'] == 'COMPLETE':
                seen_posts.update(row['post_key']
                                  for row in event['data']['posts'])
        for event in self.events:
            if event['kind'] == 'post':
                need(event['data']['post_key'] in seen_posts,
                     'POST_NOT_IN_OBSERVED_SCAN')

        list_directories = {self.events[0]['data']['list_directory']}
        for event in self.events:
            if event['kind'] == 'destination':
                list_directories.add(event['data']['list_directory'])

        media, _ = self._media_projection()
        for event in self.events:
            if event['kind'] == 'media':
                need(event['data']['post_key'] in seen_posts,
                     'MEDIA_POST_NOT_IN_OBSERVED_SCAN')
                need(self._post_detail(event['data']['post_key']) is not None,
                     'POST_DETAIL_REQUIRED_BEFORE_MEDIA')

        attempts = self._attempt_projection()
        for attempt_id, data in attempts['attempts'].items():
            row = media.get(data['media_key'])
            need(row is not None and row['post_key'] == data['post_key'] and
                 row['identity'] == data['identity'],
                 'ATTEMPT_MEDIA_CHANGED')
            destination = Path(data['destination'])
            need(destination.is_absolute() and
                 destination.name.startswith('.line-notes-incoming-') and
                 str(destination.parent) in list_directories,
                 'INTENT_DESTINATION_CHANGED')
            earlier = [other for other in attempts['attempts_by_media'][
                data['media_key']]
                if attempts['order'][other] < attempts['order'][attempt_id]]
            recovery_of = data['recovery_of']
            if recovery_of is None:
                need(not earlier, 'RECOVERY_OF_REQUIRED')
                need(data['recovery_evidence'] is None,
                     'RECOVERY_EVIDENCE_WITHOUT_PRIOR')
                continue
            need(isinstance(recovery_of, str), 'RECOVERY_ATTEMPT_CHANGED')
            prior = attempts['attempts'].get(recovery_of)
            need(prior is not None and prior['media_key'] == data['media_key'] and
                 attempts['order'][recovery_of] < attempts['order'][attempt_id],
                 'RECOVERY_ATTEMPT_CHANGED')
            latest_prior = max(earlier, key=lambda item: attempts['order'][item])
            need(recovery_of == latest_prior, 'RECOVERY_OF_NOT_LATEST')
            need(self._attempt_result(recovery_of, attempts) in
                 ('STOPPED', 'NOT_SENT'), 'RECOVERY_ATTEMPT_NOT_STOPPED')
            need(self.list_data['recovery_authorized'] is True,
                 'NOTES_RECOVERY_NOT_AUTHORIZED')
            need(data['recovery_evidence'] is not None,
                 'RECOVERY_EVIDENCE_REQUIRED')
        for attempt_id in attempts['attempts']:
            outcome = attempts['outcomes'].get(attempt_id)
            reconciles = attempts['reconciles'].get(attempt_id, [])
            if reconciles:
                need(outcome is not None and
                     outcome['data']['outcome'] == 'UNKNOWN',
                     'RECONCILE_REQUIRES_UNKNOWN_OUTCOME')
                _ = self._attempt_result(attempt_id, attempts)

        verifications = {}
        for event in self.events:
            if event['kind'] != 'verification':
                continue
            data = event['data']
            need(data['attempt_id'] in attempts['attempts'] and
                 data['attempt_id'] not in verifications,
                 'DUPLICATE_OR_ORPHAN_VERIFICATION')
            attempt = attempts['attempts'][data['attempt_id']]
            need(data['media_key'] == attempt['media_key'] and
                 data['post_key'] == attempt['post_key'] and
                 data['kind'] == attempt['identity']['kind'],
                 'VERIFICATION_ATTEMPT_CHANGED')
            need(self._attempt_result(data['attempt_id'], attempts) ==
                 'DOWNLOAD_FINISHED',
                 'VERIFICATION_REQUIRES_DOWNLOAD_FINISHED')
            need(attempts['latest_by_media'].get(data['media_key']) ==
                 data['attempt_id'], 'VERIFICATION_NOT_LATEST_ATTEMPT')
            self._validate_source_row(data['source'], 'INVALID_VERIFICATION_SOURCE')
            need(Path(data['source']['path']).parent ==
                 Path(attempt['destination']), 'VERIFICATION_SOURCE_CHANGED')
            _validate_media_suffix(data['kind'], data['source']['name'])
            _json_value(data['verification'], 'INVALID_VERIFICATION_RESULT')
            _validate_verification_payload(
                data['kind'], data['source'], data['verification'],
                allow_injected=self._allow_injected_verification)
            verifications[data['attempt_id']] = event

        plans = {}
        plan_names = set()
        for event in self.events:
            if event['kind'] != 'publish-plan':
                continue
            data = event['data']
            need(data['transaction_id'] not in plans,
                 'DUPLICATE_PUBLISH_TRANSACTION')
            verification = self._event_by_sequence(
                data['verification_sequence'])
            need(verification is not None and
                 verification['kind'] == 'verification' and
                 verification['data']['attempt_id'] == data['attempt_id'] and
                 digest(encoded(verification)) == data['verification_sha256'] and
                 data['source'] == verification['data']['source'],
                 'PUBLISH_VERIFICATION_CHANGED')
            attempt = attempts['attempts'].get(data['attempt_id'])
            need(attempt is not None and
                 data['media_key'] == attempt['media_key'] and
                 data['post_key'] == attempt['post_key'],
                 'PUBLISH_ATTEMPT_CHANGED')
            need(attempts['latest_by_media'].get(data['media_key']) ==
                 data['attempt_id'], 'PUBLISH_PLAN_NOT_LATEST_ATTEMPT')
            need(data['list_directory'] in list_directories and
                 Path(data['target_directory']).parent ==
                 Path(data['list_directory']), 'PUBLISH_DIRECTORY_CHANGED')
            match = re.fullmatch(r'media_(\d+)(\.[^./]+)',
                                 data['target_name'])
            need(match is not None and int(match.group(1)) == data['number'] and
                 match.group(2) == data['extension'] and
                 data['extension'].lower() in
                 (PHOTO_SUFFIXES if verification['data']['kind'] == PHOTO
                  else VIDEO_SUFFIXES),
                 'PUBLISH_NAME_CHANGED')
            name_key = (data['target_directory'], data['target_name'])
            need(name_key not in plan_names, 'DUPLICATE_TARGET_NAME')
            plan_names.add(name_key)
            plans[data['transaction_id']] = event

        progress = {}
        for event in self.events:
            if event['kind'] != 'publish-progress':
                continue
            data = event['data']
            plan = plans.get(data['transaction_id'])
            need(plan is not None, 'PROGRESS_WITHOUT_PUBLISH_PLAN')
            action = data['action']
            need((data['transaction_id'], action) not in progress,
                 'DUPLICATE_PUBLISH_PROGRESS')
            progress[(data['transaction_id'], action)] = event
            if action == 'DIRECTORY_READY':
                need(data.get('target_directory') ==
                     plan['data']['target_directory'] and
                     type(data.get('directory_device')) is int and
                     type(data.get('directory_inode')) is int and
                     isinstance(data.get('recorded_at'), str),
                     'INVALID_PUBLISH_PROGRESS')
            else:
                need(data.get('target_file') ==
                     str(Path(plan['data']['target_directory']) /
                         plan['data']['target_name']) and
                     type(data.get('target_device')) is int and
                     type(data.get('target_inode')) is int and
                     _is_hex(data.get('sha256')) and
                     isinstance(data.get('recorded_at'), str),
                     'INVALID_PUBLISH_PROGRESS')
                if action == 'FILE_LINKED':
                    need(type(data.get('size')) is int and data['size'] > 0,
                         'INVALID_PUBLISH_PROGRESS')

        completions, _ = self._completion_projection()
        for event in completions.values():
            data = event['data']
            attempt = attempts['attempts'].get(data['attempt_id'])
            plan = plans.get(data['transaction_id'])
            need(attempt is not None and plan is not None and
                 data['media_key'] == plan['data']['media_key'] and
                 data['post_key'] == plan['data']['post_key'] and
                 data['destination'] == plan['data']['target_directory'] and
                 data['verification_sequence'] ==
                 plan['data']['verification_sequence'] and
                 data['verification_sha256'] ==
                 plan['data']['verification_sha256'] and
                 data['source_manifest'] == plan['data']['source'],
                 'COMPLETION_PLAN_CHANGED')
            target_row = self._completion_file_row(data['target_file'])
            need(target_row['name'] == plan['data']['target_name'],
                 'COMPLETION_TARGET_CHANGED')
            need(target_row['sha256'] == plan['data']['source']['sha256'] and
                 target_row['size'] == plan['data']['source']['size'],
                 'COMPLETION_TARGET_CONTENT_CHANGED')
            target_directory = _check_exact(
                data['target_directory'], ('path', 'device', 'inode'),
                'INVALID_COMPLETION_DIRECTORY')
            need(target_directory['path'] == data['destination'] and
                 type(target_directory['device']) is int and
                 type(target_directory['inode']) is int,
                 'INVALID_COMPLETION_DIRECTORY')
            naming = _check_exact(
                data['naming'], ('transaction_id', 'number', 'target_name',
                                 'extension', 'list_directory',
                                 'target_directory'),
                'INVALID_COMPLETION_NAMING')
            need(naming['transaction_id'] == plan['data']['transaction_id'] and
                 naming['number'] == plan['data']['number'] and
                 naming['target_name'] == plan['data']['target_name'] and
                 naming['extension'] == plan['data']['extension'] and
                 naming['list_directory'] == plan['data']['list_directory'] and
                 naming['target_directory'] == plan['data']['target_directory'],
                 'COMPLETION_NAMING_CHANGED')
            verification = verifications.get(data['attempt_id'])
            need(verification is not None and
                 data['verification'] == verification['data']['verification'],
                 'COMPLETION_VERIFICATION_CHANGED')
            need(attempts['latest_by_media'].get(data['media_key']) ==
                 data['attempt_id'], 'COMPLETION_NOT_LATEST_ATTEMPT')
            need((data['transaction_id'], 'SOURCE_REMOVED') in progress,
                 'COMPLETION_WITHOUT_SOURCE_REMOVED')

        exclusive = {}
        protected = set()
        for event in self.events:
            if event['kind'] not in ('exclusion', 'protection'):
                continue
            key = event['data']['media_key']
            need(key in media and key not in completions,
                 'TERMINAL_MEDIA_WITHOUT_MEDIA')
            attempt_id = attempts['latest_by_media'].get(key)
            if attempt_id is not None:
                need(self._attempt_result(attempt_id, attempts) in
                     ('STOPPED', 'NOT_SENT'),
                     'TERMINAL_MEDIA_WITH_ACTIVE_ATTEMPT')
            if event['kind'] == 'exclusion':
                need(key not in exclusive and key not in protected,
                     'MEDIA_ALREADY_TERMINALLY_CLASSIFIED')
                exclusive[key] = event
            else:
                need(key not in exclusive and key not in protected,
                     'MEDIA_ALREADY_TERMINALLY_CLASSIFIED')
                protected.add(key)
        return True

    def append(self, kind, data):
        self._validate_event(dict(kind=kind, data=data))
        event = dict(sequence=len(self.events) + 1,
                     previous_sha256=self.previous,
                     local_list_id=self.records.name,
                     kind=kind, data=data)
        create_json(self.records / 'events' / ('%08d.json' % event['sequence']),
                    event)
        self.events.append(event)
        self.previous = digest(encoded(event))
        return data

    def _latest_binding(self):
        bindings = [event['data'] for event in self.events
                    if event['kind'] == 'binding']
        return bindings[-1] if bindings else None

    def _require_session(self, session_id, context_id=None):
        need(isinstance(session_id, str) and bool(session_id),
             'SESSION_REQUIRED')
        binding = self._latest_binding()
        need(binding is not None and binding['session_id'] == session_id,
             'FRESH_FOREGROUND_BINDING_REQUIRED')
        if context_id is not None:
            need(binding['context_id'] == context_id, 'WRONG_NOTES_CONTEXT')
        expected = self.list_data.get('context_id')
        if expected is not None:
            need(binding['context_id'] == expected, 'WRONG_NOTES_CONTEXT')

    def bind(self, *, session_id, observation, handoff, context_id=None):
        need(isinstance(session_id, str) and bool(session_id),
             'SESSION_REQUIRED')
        with self.locked():
            latest, scans = self._open_scan()
            if latest is not None:
                need(scans[latest]['complete'] is not None,
                     'SCAN_ALREADY_OPEN')
            expected = self.list_data.get('context_id')
            if expected is not None:
                need(context_id == expected, 'WRONG_NOTES_CONTEXT')
            need(not any(event['kind'] == 'binding' and
                         event['data']['session_id'] == session_id
                         for event in self.events),
                 'SESSION_ID_ALREADY_BOUND')
            data = dict(schema='line-notes-binding/v1',
                        session_id=session_id, context_id=context_id,
                        observation=_preserve_evidence(self.records, observation),
                        handoff=_preserve_evidence(self.records, handoff))
            self.append('binding', data)
            _write_active_hint(self.records, self.records.name, session_id)
            return data

    def _current_destination_state(self):
        for event in reversed(self.events):
            if event['kind'] == 'destination':
                return event['data']
        return self.events[0]['data']

    def _require_current_list_directory(self):
        state = self._current_destination_state()
        root = Path(state['photo_root'])
        list_directory = Path(state['list_directory'])
        root_entry = _entry(root)
        need(root_entry is not None, 'CURRENT_NOTES_ROOT_MISSING')
        need(not root.is_symlink() and root == root.resolve(strict=True) and
             root.is_dir(), 'CURRENT_NOTES_ROOT_CHANGED')
        list_entry = _entry(list_directory)
        need(list_entry is not None, 'CURRENT_NOTES_LIST_DIRECTORY_MISSING')
        need(not list_directory.is_symlink() and
             list_directory == list_directory.resolve(strict=True) and
             list_directory.is_dir(), 'CURRENT_NOTES_LIST_DIRECTORY_CHANGED')
        info = list_directory.stat()
        need(info.st_dev == state['directory_device'] and
             info.st_ino == state['directory_inode'],
             'CURRENT_NOTES_LIST_DIRECTORY_CHANGED')
        return list_directory

    def destination(self, *, photo_root, session_id, evidence):
        with self.locked():
            self._require_session(session_id)
            need(not self._pending_publish_plans(), 'PENDING_NAMING_TRANSACTION')
            self._assert_no_unknown_attempts()
            self._assert_no_local_changed()
            old = self._current_destination_state()
            root = _ensure_core_directory(photo_root)
            need(root != Path(old['photo_root']),
                 'NEW_NOTES_ROOT_REQUIRED')
            collection = self.records.parent
            need(not root.is_relative_to(collection) and
                 not collection.is_relative_to(root),
                 'RECORDS_MUST_BE_OUTSIDE_PHOTOS')
            component = allocate_notes_component(
                root,
                safe_component(self.list_data['display_name']) + '_' +
                self.list_data['list_key'][:8])
            list_directory = root / component
            os.mkdir(str(list_directory), 0o700)
            sync_dir(root)
            info = directory_info(list_directory)
            data = dict(schema='line-notes-destination/v1',
                        photo_root=str(root),
                        previous_root=old['photo_root'],
                        list_directory=str(list_directory),
                        previous_list_directory=old['list_directory'],
                        directory_device=info['device'],
                        directory_inode=info['inode'],
                        session_id=session_id,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('destination', data)
            return data

    def _open_scan(self):
        starts = {}
        latest = None
        open_scan_id = None
        for event in self.events:
            if event['kind'] == 'page':
                data = event['data']
                need(open_scan_id is not None and
                     data['scan_id'] == open_scan_id,
                     'PAGE_WITHOUT_OPEN_SCAN')
                scan = starts[open_scan_id]
                need(data['session_id'] ==
                     scan['start']['data']['session_id'],
                     'PAGE_SESSION_CHANGED')
                need(data['page_index'] == len(scan['pages']),
                     'PAGE_SEQUENCE_CHANGED')
                page_keys = {row['post_key'] for row in data['posts']}
                need(page_keys, 'EMPTY_PAGE_NOT_ALLOWED')
                overlap = list(data['overlap_keys'])
                need(set(overlap) <= page_keys, 'OVERLAP_NOT_IN_PAGE')
                prior_keys = {
                    row['post_key']
                    for page_event in scan['pages']
                    for row in page_event['data']['posts']
                }
                if scan['pages']:
                    previous = scan['pages'][-1]['data']
                    _validate_page_overlap(
                        previous['posts'], data['posts'], overlap,
                        prior_keys=prior_keys)
                    need(not previous['bottom_reached'],
                         'BOTTOM_MUST_BE_LAST_PAGE')
                else:
                    need(not overlap, 'FIRST_PAGE_CANNOT_OVERLAP')
                if data['page_index'] > 0:
                    need(data['top_reached'] is False,
                         'TOP_ONLY_ON_FIRST_PAGE')
                scan['pages'].append(event)
                continue
            if event['kind'] != 'scan':
                continue
            data = event['data']
            if data['action'] == 'START':
                need(open_scan_id is None, 'SCAN_ALREADY_OPEN')
                need(data['scan_id'] not in starts, 'DUPLICATE_SCAN_START')
                starts[data['scan_id']] = dict(start=event, complete=None,
                                                pages=[])
                latest = data['scan_id']
                open_scan_id = data['scan_id']
            else:
                need(open_scan_id == data['scan_id'] and
                     data['scan_id'] in starts and
                     starts[data['scan_id']]['complete'] is None,
                     'SCAN_COMPLETION_WITHOUT_OPEN_SCAN')
                need(data['session_id'] ==
                     starts[data['scan_id']]['start']['data']['session_id'],
                     'SCAN_SESSION_CHANGED')
                starts[data['scan_id']]['complete'] = event
                open_scan_id = None
        for scan in starts.values():
            if scan['complete'] is None:
                continue
            expected = []
            seen = set()
            for page_event in scan['pages']:
                for row in page_event['data']['posts']:
                    if row['post_key'] in seen:
                        continue
                    seen.add(row['post_key'])
                    expected.append(dict(
                        post_key=row['post_key'], identity=row['identity'],
                        date_summary=row['date_summary'],
                        source_order=len(expected)))
            need(scan['complete']['data']['posts'] == expected,
                 'SCAN_COMPLETION_POSTS_CHANGED')
        if latest is None:
            return None, starts
        return latest, starts

    def _latest_scan_complete(self):
        latest, scans = self._open_scan()
        if latest is None:
            return False
        return scans[latest]['complete'] is not None

    def start_scan(self, *, session_id, evidence):
        with self.locked():
            self._require_session(session_id)
            latest, scans = self._open_scan()
            if latest is not None:
                need(scans[latest]['complete'] is not None,
                     'SCAN_ALREADY_OPEN')
            data = dict(schema='line-notes-scan/v1', action='START',
                        scan_id=uuid.uuid4().hex, session_id=session_id,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('scan', data)
            return data

    def page(self, *, session_id, scan_id, page_index, posts,
             top_reached, bottom_reached, overlap_keys, evidence):
        need(type(page_index) is int and page_index >= 0,
             'INVALID_PAGE_INDEX')
        need(isinstance(posts, list), 'INVALID_PAGE_POSTS')
        need(isinstance(overlap_keys, list) and
             all(isinstance(key, str) for key in overlap_keys),
             'INVALID_OVERLAP_KEYS')
        with self.locked():
            latest, scans = self._open_scan()
            need(latest is not None and latest == scan_id,
                 'CURRENT_SCAN_REQUIRED')
            scan = scans[scan_id]
            need(scan['complete'] is None, 'SCAN_ALREADY_COMPLETE')
            need(scan['start']['data']['session_id'] == session_id,
                 'PAGE_SESSION_CHANGED')
            self._require_session(session_id)
            need(page_index == len(scan['pages']), 'PAGE_SEQUENCE_CHANGED')
            prior_posts = {}
            next_order = 0
            for page_event in scan['pages']:
                for row in page_event['data']['posts']:
                    if row['post_key'] not in prior_posts:
                        prior_posts[row['post_key']] = row
                        next_order = max(next_order, row['source_order'] + 1)
            page_posts = []
            page_keys = set()
            for row in posts:
                need(isinstance(row, dict) and
                     set(row) <= {'identity', 'date_summary'} and
                     {'identity', 'date_summary'} <= set(row),
                     'INVALID_PAGE_POSTS')
                identity = row['identity']
                key = post_key(self.list_data['list_key'], identity)
                need(key not in page_keys, 'DUPLICATE_POST_IN_PAGE')
                page_keys.add(key)
                date_summary = row['date_summary']
                need(isinstance(date_summary, str) and
                     len(date_summary) <= 200, 'INVALID_POST_DATE_SUMMARY')
                if key in prior_posts:
                    order = prior_posts[key]['source_order']
                else:
                    order = next_order
                    next_order += 1
                page_posts.append(dict(post_key=key, identity=identity,
                                       date_summary=date_summary,
                                       source_order=order))
            overlap = list(overlap_keys)
            need(bool(page_posts), 'EMPTY_PAGE_NOT_ALLOWED')
            need(len(set(overlap)) == len(overlap), 'INVALID_OVERLAP_KEYS')
            need(set(overlap) <= page_keys, 'OVERLAP_NOT_IN_PAGE')
            if scan['pages']:
                _validate_page_overlap(
                    scan['pages'][-1]['data']['posts'], page_posts, overlap,
                    prior_keys=set(prior_posts))
                need(not scan['pages'][-1]['data']['bottom_reached'],
                     'BOTTOM_MUST_BE_LAST_PAGE')
            else:
                need(not overlap, 'FIRST_PAGE_CANNOT_OVERLAP')
            if page_index > 0:
                need(top_reached is False, 'TOP_ONLY_ON_FIRST_PAGE')
            if bottom_reached:
                for prior_page in scan['pages']:
                    need(prior_page['data']['bottom_reached'] is False,
                         'BOTTOM_MUST_BE_LAST_PAGE')
            data = dict(schema='line-notes-page/v1', scan_id=scan_id,
                        session_id=session_id, page_index=page_index,
                        top_reached=bool(top_reached),
                        bottom_reached=bool(bottom_reached),
                        overlap_keys=overlap, posts=page_posts,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('page', data)
            return data

    def finish_scan(self, *, session_id, scan_id, evidence):
        with self.locked():
            latest, scans = self._open_scan()
            need(latest is not None and latest == scan_id,
                 'CURRENT_SCAN_REQUIRED')
            scan = scans[scan_id]
            need(scan['complete'] is None, 'SCAN_ALREADY_COMPLETE')
            need(scan['start']['data']['session_id'] == session_id,
                 'SCAN_SESSION_CHANGED')
            self._require_session(session_id)
            need(scan['pages'], 'SCAN_REQUIRES_PAGE')
            need(scan['pages'][0]['data']['top_reached'] is True,
                 'SCAN_TOP_NOT_REACHED')
            need(scan['pages'][-1]['data']['bottom_reached'] is True,
                 'SCAN_BOTTOM_NOT_REACHED')
            ordered = []
            seen = set()
            for page_event in scan['pages']:
                for row in page_event['data']['posts']:
                    if row['post_key'] in seen:
                        continue
                    seen.add(row['post_key'])
                    ordered.append(dict(post_key=row['post_key'],
                                        identity=row['identity'],
                                        date_summary=row['date_summary'],
                                        source_order=len(ordered)))
            data = dict(schema='line-notes-scan/v1', action='COMPLETE',
                        scan_id=scan_id, session_id=session_id,
                        evidence=_preserve_evidence(self.records, evidence),
                        posts=ordered)
            self.append('scan', data)
            return data

    def scan(self, *, session_id, action, scan_id=None, evidence):
        need(action in ('START', 'FINISH'), 'INVALID_SCAN_ACTION')
        if action == 'START':
            need(scan_id is None, 'SCAN_ID_NOT_ACCEPTED_FOR_START')
            return self.start_scan(session_id=session_id, evidence=evidence)
        need(scan_id is not None, 'SCAN_ID_REQUIRED')
        return self.finish_scan(session_id=session_id, scan_id=scan_id,
                                evidence=evidence)

    def _post_identity(self, key):
        _hex(key, 'INVALID_POST_KEY')
        latest, scans = self._open_scan()
        need(latest is not None and scans[latest]['complete'] is not None,
             'POST_NOT_IN_OBSERVED_SCAN')
        found = {
            row['post_key']: row['identity']
            for row in scans[latest]['complete']['data']['posts']
        }
        need(key in found, 'POST_NOT_IN_OBSERVED_SCAN')
        return found[key]

    def _latest_complete_scan_id(self):
        latest, scans = self._open_scan()
        need(latest is not None and scans[latest]['complete'] is not None,
             'COMPLETE_NOTES_SCAN_REQUIRED')
        return latest

    def _require_attempt_scan_binding(self, intent_data):
        bound = intent_data.get('scan_id')
        need(bound is not None, 'INTENT_SCAN_BINDING_REQUIRED')
        latest, scans = self._open_scan()
        need(latest is not None and scans[latest]['complete'] is not None and
             bound == latest, 'ATTEMPT_SCAN_BINDING_CHANGED')
        complete_posts = {
            row['post_key']
            for row in scans[bound]['complete']['data']['posts']
        }
        need(intent_data['post_key'] in complete_posts,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        detail = self._post_detail_for_scan(intent_data['post_key'], bound)
        need(detail is not None and detail.get('scan_id') == bound,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        media, _ = self._media_projection()
        target = media.get(intent_data['media_key'])
        need(target is not None and
             target.get('post_key') == intent_data['post_key'] and
             target.get('scan_id') == bound,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        return bound

    def record_post(self, *, session_id, post_key_value, date_summary,
                    media_count, text_sha256, evidence, no_media=False,
                    scan_id=None):
        need(type(media_count) is int and media_count >= 0,
             'INVALID_POST_MEDIA_COUNT')
        need(bool(no_media) == (media_count == 0),
             'NO_MEDIA_COUNT_MISMATCH')
        need(isinstance(date_summary, str) and date_summary and
             len(date_summary) <= 200, 'INVALID_POST_DATE_SUMMARY')
        need(text_sha256 is None or _is_hex(text_sha256),
             'INVALID_TEXT_SHA256')
        with self.locked():
            self._require_session(session_id)
            current_scan_id = self._latest_complete_scan_id()
            if scan_id is not None:
                need(scan_id == current_scan_id, 'POST_SCAN_BINDING_CHANGED')
            self._post_identity(post_key_value)
            need(not any(
                event['kind'] == 'post' and
                event['data']['post_key'] == post_key_value and
                event['data'].get('scan_id') == current_scan_id
                for event in self.events), 'POST_DETAIL_ALREADY_RECORDED')
            data = dict(schema='line-notes-post/v1',
                        post_key=post_key_value,
                        date_summary=date_summary,
                        text_sha256=text_sha256,
                        media_count=media_count,
                        no_media=bool(no_media),
                        scan_id=current_scan_id,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('post', data)
            return data

    def _post_detail(self, post_key_value):
        rows = [event['data'] for event in self.events
                if event['kind'] == 'post' and
                event['data']['post_key'] == post_key_value]
        return rows[-1] if rows else None

    def _post_detail_for_scan(self, post_key_value, scan_id):
        rows = [event['data'] for event in self.events
                if event['kind'] == 'post' and
                event['data']['post_key'] == post_key_value and
                event['data'].get('scan_id') == scan_id]
        return rows[-1] if rows else None

    def _media_projection(self):
        media = {}
        snapshots = {}
        for event in self.events:
            if event['kind'] != 'media':
                continue
            data = event['data']
            post_rows = snapshots.setdefault(data['post_key'], [])
            post_rows.append(event)
            present = {row['media_key'] for row in data['items']}
            for row in data['items']:
                current = media.setdefault(row['media_key'], {})
                current.update(identity=row['identity'],
                               post_key=data['post_key'],
                               source_order=row['source_order'],
                               missing=False,
                               missing_reason=None,
                               scan_id=data.get('scan_id'),
                               last_seen_sequence=event['sequence'])
            for row in data['missing']:
                current = media.get(row['media_key'])
                need(current is not None and
                     current.get('post_key') == data['post_key'] and
                     row['media_key'] not in present,
                     'INVALID_MEDIA_MISSING')
                current['missing'] = True
                current['missing_reason'] = row['reason']
                current['source_order'] = row['source_order']
                current['scan_id'] = data.get('scan_id')
            for key, current in list(media.items()):
                if current.get('post_key') == data['post_key'] and key not in present:
                    if key not in {row['media_key'] for row in data['missing']}:
                        # The writer validates this; this is a load-time guard.
                        raise NotesError('IMPLICIT_MEDIA_DISAPPEARANCE')
        return media, snapshots

    def record_media(self, *, session_id, post_key_value, items, missing,
                     evidence, scan_id=None):
        need(isinstance(items, list), 'INVALID_MEDIA_ITEMS')
        need(isinstance(missing, list), 'INVALID_MEDIA_MISSING')
        with self.locked():
            self._require_session(session_id)
            current_scan_id = self._latest_complete_scan_id()
            if scan_id is not None:
                need(scan_id == current_scan_id, 'MEDIA_SCAN_BINDING_CHANGED')
            need(not any(
                event['kind'] == 'media' and
                event['data']['post_key'] == post_key_value and
                event['data'].get('scan_id') == current_scan_id
                for event in self.events), 'MEDIA_INVENTORY_ALREADY_RECORDED')
            detail = self._post_detail(post_key_value)
            need(detail is not None, 'POST_DETAIL_REQUIRED_BEFORE_MEDIA')
            need(detail.get('scan_id') == current_scan_id,
                 'POST_DETAIL_SCAN_BINDING_REQUIRED')
            self._post_identity(post_key_value)
            prior, _ = self._media_projection()
            prior_keys = {key for key, row in prior.items()
                          if row.get('post_key') == post_key_value}
            normalized = []
            present = set()
            for row in items:
                need(isinstance(row, dict) and
                     set(row) == {'identity'}, 'INVALID_MEDIA_ITEMS')
                identity = row['identity']
                key = media_key(self.list_data['list_key'],
                                post_key_value, identity)
                need(key not in present, 'DUPLICATE_MEDIA_IN_POST')
                present.add(key)
                normalized.append(dict(media_key=key, identity=identity))
            missing_rows = []
            missing_keys = set()
            for row in missing:
                need(isinstance(row, dict) and
                     set(row) == {'media_key', 'source_order', 'reason'},
                     'INVALID_MEDIA_MISSING')
                key = row['media_key']
                _hex(key, 'INVALID_MEDIA_KEY')
                need(key in prior_keys and key not in present and
                     key not in missing_keys,
                     'MEDIA_MISSING_SCOPE_MISMATCH')
                need(isinstance(row['reason'], str) and
                     bool(row['reason'].strip()), 'INVALID_MEDIA_MISSING')
                source_order = row['source_order']
                need(_is_nonnegative_int(source_order) and
                     source_order < detail['media_count'],
                     'INVALID_MEDIA_MISSING')
                missing_keys.add(key)
                missing_rows.append(dict(media_key=key,
                                         source_order=source_order,
                                         reason=row['reason']))
            need(len(normalized) + len(missing_rows) == detail['media_count'],
                 'POST_MEDIA_COUNT_MISMATCH')
            missing_orders = [row['source_order'] for row in missing_rows]
            need(len(set(missing_orders)) == len(missing_orders),
                 'INVALID_MEDIA_MISSING')
            missing_order_set = set(missing_orders)
            present_orders = [
                order for order in range(detail['media_count'])
                if order not in missing_order_set
            ]
            need(len(present_orders) == len(normalized),
                 'POST_MEDIA_COUNT_MISMATCH')
            for source_order, row in zip(present_orders, normalized):
                row['source_order'] = source_order
            need(prior_keys <= present | missing_keys,
                 'IMPLICIT_MEDIA_DISAPPEARANCE')
            data = dict(schema='line-notes-media-inventory/v1',
                        post_key=post_key_value,
                        items=normalized,
                        missing=missing_rows,
                        scan_id=current_scan_id,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('media', data)
            return data

    def _attempt_projection(self):
        attempts = {}
        order = {}
        outcomes = {}
        reconciles = {}
        for event in self.events:
            data = event['data']
            if event['kind'] == 'intent':
                attempt_id = data['attempt_id']
                need(attempt_id not in attempts, 'DUPLICATE_ATTEMPT_ID')
                attempts[attempt_id] = data
                order[attempt_id] = event['sequence']
            elif event['kind'] == 'outcome':
                need(data['attempt_id'] in attempts, 'OUTCOME_WITHOUT_INTENT')
                need(data['attempt_id'] not in outcomes,
                     'DUPLICATE_ATTEMPT_OUTCOME')
                need(attempts[data['attempt_id']]['media_key'] ==
                     data['media_key'], 'ATTEMPT_MEDIA_CHANGED')
                outcomes[data['attempt_id']] = event
            elif event['kind'] == 'reconcile':
                need(data['attempt_id'] in attempts, 'RECONCILE_WITHOUT_INTENT')
                need(attempts[data['attempt_id']]['media_key'] ==
                     data['media_key'], 'ATTEMPT_MEDIA_CHANGED')
                reconciles.setdefault(data['attempt_id'], []).append(event)
        latest_by_media = {}
        attempts_by_media = {}
        for attempt_id, data in attempts.items():
            attempts_by_media.setdefault(data['media_key'], []).append(attempt_id)
            current = latest_by_media.get(data['media_key'])
            if current is None or order[attempt_id] > order[current]:
                latest_by_media[data['media_key']] = attempt_id
        return dict(attempts=attempts, order=order, outcomes=outcomes,
                    reconciles=reconciles, latest_by_media=latest_by_media,
                    attempts_by_media=attempts_by_media)

    def _attempt_result(self, attempt_id, projection=None):
        projection = projection or self._attempt_projection()
        need(attempt_id in projection['attempts'], 'UNKNOWN_ATTEMPT_ID')
        outcome = projection['outcomes'].get(attempt_id)
        reconciles = projection['reconciles'].get(attempt_id, [])
        if outcome is not None and outcome['data']['outcome'] != 'UNKNOWN':
            need(not reconciles, 'RECONCILE_AFTER_TERMINAL_OUTCOME')
            return outcome['data']['outcome']
        result = 'UNKNOWN' if outcome is not None else None
        terminal = False
        for event in reconciles:
            need(not terminal, 'RECONCILE_AFTER_TERMINAL_RESULT')
            row = event['data']['result']
            result = row
            if row != 'UNKNOWN':
                terminal = True
        return result

    def _completion_projection(self):
        completions = {}
        by_attempt = {}
        for event in self.events:
            if event['kind'] != 'completion':
                continue
            data = event['data']
            need(data['media_key'] not in completions,
                 'COMPLETION_IMMUTABLE')
            need(data['attempt_id'] not in by_attempt,
                 'COMPLETION_IMMUTABLE')
            completions[data['media_key']] = event
            by_attempt[data['attempt_id']] = event
        return completions, by_attempt

    def _exclusion_projection(self):
        result = {}
        for event in self.events:
            if event['kind'] == 'exclusion':
                need(event['data']['media_key'] not in result,
                     'DUPLICATE_EXCLUSION')
                result[event['data']['media_key']] = event
        return result

    def _protection_projection(self):
        result = {}
        for event in self.events:
            if event['kind'] == 'protection':
                need(event['data']['media_key'] not in result,
                     'DUPLICATE_PROTECTION')
                result[event['data']['media_key']] = event
        return result

    def _pending_publish_plans(self):
        completions, _ = self._completion_projection()
        completed_transactions = {event['data']['transaction_id']
                                  for event in completions.values()}
        plans = {}
        for event in self.events:
            if event['kind'] != 'publish-plan':
                continue
            data = event['data']
            need(data['transaction_id'] not in plans,
                 'DUPLICATE_PUBLISH_TRANSACTION')
            plans[data['transaction_id']] = event
        return [event for transaction, event in plans.items()
                if transaction not in completed_transactions]

    def _assert_no_unknown_attempts(self):
        projection = self._attempt_projection()
        for media_key_value, attempt_id in projection['latest_by_media'].items():
            if media_key_value in self._completion_projection()[0]:
                continue
            result = self._attempt_result(attempt_id, projection)
            need(result in ('STOPPED', 'NOT_SENT'),
                 'UNRESOLVED_ATTEMPT_BLOCKS_CHANGE')

    def _completion_file_row(self, row):
        _check_exact(row, ('name', 'device', 'inode', 'size', 'sha256',
                           'mtime_ns', 'ctime_ns'), 'INVALID_COMPLETION_FILE')
        need(isinstance(row['name'], str) and
             Path(row['name']).name == row['name'] and
             not row['name'].startswith('.') and
             type(row['device']) is int and type(row['inode']) is int and
             type(row['size']) is int and row['size'] > 0 and
             _is_hex(row['sha256']) and type(row['mtime_ns']) is int and
             type(row['ctime_ns']) is int, 'INVALID_COMPLETION_FILE')
        return row

    def _completion_availability(self):
        completions, _ = self._completion_projection()
        plans = self._pending_publish_plans()
        by_directory = {}
        for event in completions.values():
            data = event['data']
            directory = Path(data['destination'])
            row = self._completion_file_row(data['target_file'])
            target_directory = _check_exact(
                data['target_directory'], ('path', 'device', 'inode'),
                'INVALID_COMPLETION_DIRECTORY')
            need(Path(target_directory['path']) == directory and
                 row['name'] == Path(data['target_file']['name']).name,
                 'INVALID_COMPLETION_BINDING')
            by_directory.setdefault(str(directory), []).append(event)
        plan_names = {}
        for event in plans:
            data = event['data']
            plan_names.setdefault(data['target_directory'], set()).add(
                data['target_name'])
        availability = {}
        changed_directories = set()
        missing_directories = set()
        for directory_string, entries in by_directory.items():
            directory = Path(directory_string)
            entry = _entry(directory)
            if entry is None:
                missing_directories.add(directory_string)
                for event in entries:
                    availability[event['data']['media_key']] = LOCAL_MISSING
                continue
            try:
                need(stat.S_ISDIR(entry.st_mode) and
                     not directory.is_symlink() and
                     directory == directory.resolve(strict=True),
                     'COMPLETED_DIRECTORY_CHANGED')
                info = directory.stat()
                expected_names = set()
                for event in entries:
                    target_directory = event['data']['target_directory']
                    need(info.st_dev == target_directory['device'] and
                         info.st_ino == target_directory['inode'],
                         'COMPLETED_DIRECTORY_CHANGED')
                    expected_names.add(event['data']['target_file']['name'])
                expected_names |= plan_names.get(directory_string, set())
                actual_names = {path.name for path in directory.iterdir()}
                need(actual_names == expected_names,
                     'COMPLETED_DIRECTORY_CONTENTS_CHANGED')
                for event in entries:
                    data = event['data']
                    row = data['target_file']
                    path = directory / row['name']
                    file_entry = _entry(path)
                    need(file_entry is not None and
                         stat.S_ISREG(file_entry.st_mode) and
                         file_entry.st_nlink == 1 and
                         not path.is_symlink(), 'COMPLETED_FILE_CHANGED')
                    file_info = os.stat(str(path), follow_symlinks=False)
                    need((file_info.st_dev, file_info.st_ino,
                          file_info.st_size, file_info.st_mtime_ns,
                          file_info.st_ctime_ns) ==
                         (row['device'], row['inode'], row['size'],
                          row['mtime_ns'], row['ctime_ns']),
                         'COMPLETED_FILE_CHANGED')
                    need(digest(read_file(path)) == row['sha256'],
                         'COMPLETED_FILE_CHANGED')
                    availability[data['media_key']] = LOCAL_VERIFIED
            except (NotesError, DailyError, OSError, ValueError):
                changed_directories.add(directory_string)
                for event in entries:
                    availability[event['data']['media_key']] = LOCAL_CHANGED
        for event in plans:
            data = event['data']
            if data['target_directory'] in changed_directories:
                continue
            if data['target_directory'] in missing_directories:
                continue
        return availability

    def _assert_no_local_changed(self):
        availability = self._completion_availability()
        need(not any(value == LOCAL_CHANGED
                     for value in availability.values()),
             'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD')

    def _status_map(self):
        media, _ = self._media_projection()
        attempts = self._attempt_projection()
        completions, _ = self._completion_projection()
        exclusions = self._exclusion_projection()
        protections = self._protection_projection()
        result = {}
        for key, row in media.items():
            if key in completions:
                result[key] = 'COMPLETED'
                continue
            if key in exclusions:
                result[key] = 'EXCLUDED'
                continue
            if key in protections:
                result[key] = 'PROTECTED_HISTORY'
                continue
            attempt_id = attempts['latest_by_media'].get(key)
            if attempt_id is None:
                result[key] = ('PREVIOUSLY_INCOMPLETE'
                               if row.get('missing') else 'PENDING')
                continue
            outcome = self._attempt_result(attempt_id, attempts)
            if outcome is None or outcome == 'UNKNOWN':
                result[key] = 'UNKNOWN'
            elif outcome in ('STOPPED', 'NOT_SENT'):
                result[key] = 'PREVIOUSLY_INCOMPLETE'
            elif row.get('missing'):
                result[key] = 'PREVIOUSLY_INCOMPLETE'
            else:
                result[key] = 'PENDING'
        return result

    def _latest_complete_scan_posts(self):
        latest, scans = self._open_scan()
        if latest is None or scans[latest]['complete'] is None:
            return None
        return scans[latest]['complete']['data']['posts']

    def _assert_dispatch_inventory(self):
        posts = self._latest_complete_scan_posts()
        need(posts is not None, 'COMPLETE_NOTES_SCAN_REQUIRED')
        return posts

    def intent(self, *, session_id, media_key_value, recovery_evidence=None):
        with self.locked():
            self._require_session(session_id)
            list_directory = self._require_current_list_directory()
            self._assert_no_local_changed()
            need(not self._pending_publish_plans(), 'PENDING_NAMING_TRANSACTION')
            latest_scan_id = self._latest_complete_scan_id()
            posts = self._assert_dispatch_inventory()
            observed_posts = {row['post_key'] for row in posts}
            media, _ = self._media_projection()
            need(media_key_value in media, 'MEDIA_NOT_OBSERVED')
            target = media[media_key_value]
            need(target['post_key'] in observed_posts,
                 'MEDIA_POST_NOT_IN_COMPLETE_SCAN')
            need(not target.get('missing'), 'MEDIA_CURRENTLY_MISSING')
            detail = self._post_detail(target['post_key'])
            need(detail is not None and not detail['no_media'],
                 'POST_MEDIA_DETAIL_REQUIRED')
            need(detail.get('scan_id') == latest_scan_id,
                 'STALE_POST_DETAIL')
            need(target.get('scan_id') == latest_scan_id,
                 'STALE_MEDIA_INVENTORY')
            status = self._status_map()[media_key_value]
            need(status not in ('COMPLETED', 'EXCLUDED'),
                 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD')
            need(status != 'PROTECTED_HISTORY',
                 'PROTECTED_HISTORY_NO_REDOWNLOAD')
            attempts = self._attempt_projection()
            prior = attempts['latest_by_media'].get(media_key_value)
            if prior is not None:
                result = self._attempt_result(prior, attempts)
                need(result in ('STOPPED', 'NOT_SENT'),
                     'UNKNOWN_OR_RUNNING_NO_REPLAY')
                need(self.list_data['recovery_authorized'] is True,
                     'NOTES_RECOVERY_NOT_AUTHORIZED')
                need(recovery_evidence is not None,
                     'NOTES_RECOVERY_EVIDENCE_REQUIRED')
            else:
                need(recovery_evidence is None,
                     'NO_PRIOR_ATTEMPT_TO_RECOVER')
            for other_key, attempt_id in attempts['latest_by_media'].items():
                if other_key == media_key_value:
                    continue
                if other_key in self._completion_projection()[0]:
                    continue
                other_result = self._attempt_result(attempt_id, attempts)
                need(other_result in ('STOPPED', 'NOT_SENT'),
                     'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED')
            staging = _new_unique_directory(list_directory,
                                             '.line-notes-incoming-')
            need(not any(staging.iterdir()), 'EMPTY_STAGING_REQUIRED')
            info = staging.stat()
            recovery_ref = (_preserve_evidence(self.records, recovery_evidence)
                            if recovery_evidence is not None else None)
            data = dict(schema='line-notes-intent/v1',
                        media_key=media_key_value,
                        post_key=target['post_key'],
                        identity=target['identity'],
                        attempt_id=uuid.uuid4().hex,
                        session_id=session_id,
                        scan_id=latest_scan_id,
                        destination=str(staging),
                        directory_device=info.st_dev,
                        directory_inode=info.st_ino,
                        save_all_limit=1,
                        save_all_count=0,
                        recovery_of=prior,
                        recovery_evidence=recovery_ref)
            self.append('intent', data)
            return dict(data, status='UNKNOWN', dispatch_authorized=False)

    def _require_latest_attempt(self, attempt_id):
        projection = self._attempt_projection()
        need(attempt_id in projection['attempts'], 'UNKNOWN_ATTEMPT_ID')
        media_key_value = projection['attempts'][attempt_id]['media_key']
        need(projection['latest_by_media'].get(media_key_value) == attempt_id,
             'ONLY_LATEST_ATTEMPT_CAN_CHANGE')
        return projection, media_key_value

    def outcome(self, *, session_id, attempt_id, outcome, evidence):
        need(outcome in OUTCOMES, 'INVALID_OUTCOME')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            need(attempt_id not in projection['outcomes'] and
                 attempt_id not in projection['reconciles'],
                 'OUTCOME_ALREADY_RECORDED')
            need(media_key_value not in self._completion_projection()[0],
                 'COMPLETION_IMMUTABLE')
            data = dict(schema='line-notes-outcome/v1',
                        attempt_id=attempt_id,
                        media_key=media_key_value,
                        outcome=outcome,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('outcome', data)
            return data

    def reconcile(self, *, session_id, attempt_id, result, evidence):
        need(result in OUTCOMES, 'INVALID_RECONCILE_RESULT')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            current = self._attempt_result(attempt_id, projection)
            need(current == 'UNKNOWN', 'UNKNOWN_OUTCOME_REQUIRED_FOR_RECONCILE')
            need(media_key_value not in self._completion_projection()[0],
                 'COMPLETION_IMMUTABLE')
            data = dict(schema='line-notes-reconcile/v1',
                        attempt_id=attempt_id,
                        media_key=media_key_value,
                        result=result,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append('reconcile', data)
            return data

    def _record_terminal_media_state(self, kind, media_key_value, reason,
                                     evidence, session_id=None):
        need(isinstance(reason, str) and bool(reason.strip()),
             'REASON_REQUIRED')
        with self.locked():
            if session_id is not None:
                self._require_session(session_id)
            media, _ = self._media_projection()
            need(media_key_value in media, 'MEDIA_NOT_OBSERVED')
            need(media_key_value not in self._completion_projection()[0],
                 'COMPLETION_IMMUTABLE')
            existing_terminal = set(self._exclusion_projection())
            existing_terminal |= set(self._protection_projection())
            need(media_key_value not in existing_terminal,
                 'MEDIA_ALREADY_TERMINALLY_CLASSIFIED')
            need(not self._pending_publish_plans(), 'PENDING_NAMING_TRANSACTION')
            attempts = self._attempt_projection()
            attempt_id = attempts['latest_by_media'].get(media_key_value)
            if attempt_id is not None:
                result = self._attempt_result(attempt_id, attempts)
                need(result in ('STOPPED', 'NOT_SENT'),
                     'ACTIVE_ATTEMPT_CANNOT_BE_CLOSED')
            data = dict(schema='line-notes-%s/v1' % kind,
                        media_key=media_key_value,
                        reason=reason,
                        evidence=_preserve_evidence(self.records, evidence))
            self.append(kind, data)
            return data

    def exclude(self, *, session_id, media_key_value, reason, evidence):
        return self._record_terminal_media_state(
            'exclusion', media_key_value, reason, evidence,
            session_id=session_id)

    def protect(self, *, media_key_value, reason, evidence):
        return self._record_terminal_media_state(
            'protection', media_key_value, reason, evidence)

    def _media_rows(self):
        media, _ = self._media_projection()
        statuses = self._status_map()
        availability = self._completion_availability()
        rows = []
        for key, row in media.items():
            status = statuses[key]
            local = availability.get(key, LOCAL_NOT_APPLICABLE)
            rows.append(dict(media_key=key, post_key=row['post_key'],
                             identity=row['identity'],
                             kind=row['identity']['kind'],
                             source_order=row['source_order'],
                             missing=bool(row.get('missing')),
                             missing_reason=row.get('missing_reason'),
                             status=status, local_files=local))
        return rows

    def _post_rows(self):
        media_rows = self._media_rows()
        media, _ = self._media_projection()
        posts = {}
        latest, scans = self._open_scan()
        current_complete = (
            latest is not None and scans[latest]['complete'] is not None)
        if current_complete:
            for row in scans[latest]['complete']['data']['posts']:
                posts[row['post_key']] = dict(
                    post_key=row['post_key'], identity=row['identity'],
                    date_summary=row['date_summary'],
                    source_order=row['source_order'])
        else:
            for event in self.events:
                if event['kind'] == 'page':
                    for row in event['data']['posts']:
                        posts.setdefault(row['post_key'], dict(
                            post_key=row['post_key'], identity=row['identity'],
                            date_summary=row['date_summary'],
                            source_order=row['source_order']))
                elif event['kind'] == 'scan' and \
                        event['data']['action'] == 'COMPLETE':
                    for row in event['data']['posts']:
                        posts[row['post_key']] = dict(
                            post_key=row['post_key'], identity=row['identity'],
                            date_summary=row['date_summary'],
                            source_order=row['source_order'])
        for row in media_rows:
            if current_complete and row['post_key'] not in posts:
                continue
            if current_complete and media.get(row['media_key'], {}).get(
                    'scan_id') != latest:
                continue
            current = posts.setdefault(row['post_key'], dict(
                post_key=row['post_key'], identity=None,
                date_summary='', source_order=row['source_order'],
                media=[]))
            current.setdefault('media', []).append(row)
        result = []
        for key, row in posts.items():
            detail = (self._post_detail_for_scan(key, latest)
                      if current_complete else self._post_detail(key))
            children = list(row.get('media', []))
            result.append(dict(row,
                text_sha256=detail['text_sha256'] if detail else None,
                media_count=detail['media_count'] if detail else None,
                no_media=detail['no_media'] if detail else None,
                state=('NO_MEDIA' if detail and detail['no_media']
                       else 'MEDIA' if detail else 'DETAIL_PENDING'),
                media=children))
        return sorted(result, key=lambda item: (item['source_order'],
                                                item['post_key']))

    def summary(self):
        with self.locked():
            return self._project_summary()

    def _project_summary(self):
        media_rows = self._media_rows()
        post_rows = self._post_rows()
        latest, scans = self._open_scan()
        current_scan_id = (
            latest if latest is not None and
            scans[latest]['complete'] is not None else None)
        current_posts = (
            scans[current_scan_id]['complete']['data']['posts']
            if current_scan_id is not None else [])
        media, snapshots = self._media_projection()
        current_post_keys = {row['post_key'] for row in current_posts}
        current_media_keys = {
            key for key, row in media.items()
            if row.get('post_key') in current_post_keys and
            row.get('scan_id') == current_scan_id
        }
        scoped_media_rows = (
            [row for row in media_rows
             if row['media_key'] in current_media_keys]
            if current_scan_id is not None else media_rows)
        counts = {status: 0 for status in STATUSES}
        for row in scoped_media_rows:
            counts[row['status']] += 1
        local_counts = {LOCAL_VERIFIED: 0, LOCAL_MISSING: 0,
                        LOCAL_CHANGED: 0, LOCAL_NOT_APPLICABLE: 0}
        for row in scoped_media_rows:
            local_counts[row['local_files']] += 1
        stale_post_detail = False
        stale_media_inventory = False
        for event in self.events:
            if (event['kind'] == 'post' and
                    'scan_id' not in event['data']):
                stale_post_detail = True
            elif (event['kind'] == 'media' and
                  'scan_id' not in event['data']):
                stale_media_inventory = True
        if current_scan_id is not None:
            for row in current_posts:
                key = row['post_key']
                detail = self._post_detail_for_scan(key, current_scan_id)
                post_snapshots = snapshots.get(key, [])
                current_snapshots = [
                    event for event in post_snapshots
                    if event['data'].get('scan_id') == current_scan_id]
                old_snapshots = [
                    event for event in post_snapshots
                    if event['data'].get('scan_id') != current_scan_id]
                if not current_snapshots and old_snapshots:
                    stale_media_inventory = True
                if detail is None:
                    if any(event['kind'] == 'post' and
                           event['data']['post_key'] == key
                           for event in self.events):
                        stale_post_detail = True
                    continue
                if current_snapshots:
                    snapshot = current_snapshots[-1]['data']
                    if (len(snapshot['items']) + len(snapshot['missing']) !=
                            detail['media_count']):
                        stale_media_inventory = True
        if latest is None:
            scan_coverage = 'NOT_STARTED'
        elif scans[latest]['complete'] is None:
            scan_coverage = 'IN_PROGRESS'
        else:
            scan_coverage = 'COMPLETE'
        blockers = []
        if scan_coverage != 'COMPLETE':
            blockers.append('SCAN_' + scan_coverage)
        if self._pending_publish_plans():
            blockers.append('PENDING_NAMING')
        if any(row['local_files'] == LOCAL_CHANGED
               for row in scoped_media_rows):
            blockers.append('COMPLETED_FILES_CHANGED')
        post_detail_pending = any(row['state'] == 'DETAIL_PENDING'
                                  for row in post_rows)
        post_coverage_incomplete = (
            not post_rows or
            any(row['state'] != 'DETAIL_PENDING' and
                row['media_count'] != len(row['media']) for row in post_rows))
        if post_detail_pending:
            blockers.append('POST_DETAIL_PENDING')
        if post_coverage_incomplete:
            blockers.append('POST_COVERAGE_INCOMPLETE')
        if stale_post_detail:
            blockers.append('STALE_POST_DETAIL')
        if stale_media_inventory:
            blockers.append('STALE_MEDIA_INVENTORY')
        attempts = self._attempt_projection()
        status_by_key = {row['media_key']: row['status'] for row in media_rows}
        for media_key_value, attempt_id in attempts['latest_by_media'].items():
            if media_key_value in self._completion_projection()[0]:
                continue
            if status_by_key.get(media_key_value) in (
                    'COMPLETED', 'EXCLUDED', 'PROTECTED_HISTORY'):
                continue
            result = self._attempt_result(attempt_id, attempts)
            if result in (None, 'UNKNOWN'):
                blockers.append('UNKNOWN_ATTEMPT')
            elif result == 'DOWNLOAD_FINISHED':
                blockers.append('VERIFY_REQUIRED')
        blockers = sorted(set(blockers))
        current_incomplete = sum(
            1 for row in scoped_media_rows
            if row['status'] in ('PENDING', 'PREVIOUSLY_INCOMPLETE',
                                 'UNKNOWN', 'PROTECTED_HISTORY'))
        post_coverage_complete = (bool(post_rows) and
                                  not post_detail_pending and
                                  not post_coverage_incomplete)
        all_media_complete = (scan_coverage == 'COMPLETE' and
                              post_coverage_complete and
                              current_incomplete == 0 and not blockers)
        return dict(schema=MEMORY_SCHEMA,
                    local_list_id=self.records.name,
                    records_root=str(self.records),
                    list_key=self.list_data['list_key'],
                    identity=self.list_data['identity'],
                    display_name=self.list_data['display_name'],
                    context_id=self.list_data.get('context_id'),
                    recovery_authorized=self.list_data['recovery_authorized'],
                    photo_root=str(self.current_photo_root),
                    list_directory=str(self.current_list_directory),
                    scan_coverage=scan_coverage,
                    posts=post_rows,
                    media=media_rows,
                    status_counts=counts,
                    local_counts=local_counts,
                    current_incomplete=current_incomplete,
                    dispatch_blockers=blockers,
                    all_known_media_complete=all_media_complete,
                    external_copy_verified=False,
                    real_line_e2e='NOT_TESTED')

    def memory(self):
        return self.summary()

    def _verification_for_attempt(self, attempt_id):
        rows = [event for event in self.events
                if event['kind'] == 'verification' and
                event['data']['attempt_id'] == attempt_id]
        need(len(rows) <= 1, 'DUPLICATE_VERIFICATION_EVENT')
        return rows[0] if rows else None

    def _validate_staging(self, intent_data):
        staging = Path(intent_data['destination'])
        need(staging.is_dir() and staging == staging.resolve(strict=True) and
             not staging.is_symlink(), 'STAGING_DIRECTORY_CHANGED')
        info = staging.stat()
        need(info.st_dev == intent_data['directory_device'] and
             info.st_ino == intent_data['directory_inode'],
             'STAGING_DIRECTORY_CHANGED')
        list_directory = self._require_current_list_directory()
        need(staging.parent == list_directory,
             'STAGING_OUTSIDE_CURRENT_LIST')
        return staging

    def _post_directory_for_publish(self, post_key_value):
        list_directory = self._require_current_list_directory()
        completions, _ = self._completion_projection()
        directories = set()
        for event in completions.values():
            data = event['data']
            if data['post_key'] != post_key_value:
                continue
            directory = Path(data['destination'])
            if directory.parent == list_directory:
                directories.add(directory)
        need(len(directories) <= 1, 'MULTIPLE_POST_DIRECTORIES')
        if directories:
            directory = directories.pop()
            need(_entry(directory) is not None,
                 'PRIOR_POST_DIRECTORY_MISSING_USE_DESTINATION')
            need(directory.is_dir() and
                 directory == directory.resolve(strict=True) and
                 not directory.is_symlink(), 'PRIOR_POST_DIRECTORY_CHANGED')
            return directory, True
        detail = self._post_detail(post_key_value)
        need(detail is not None, 'POST_DETAIL_REQUIRED_BEFORE_PUBLISH')
        base = safe_component(detail['date_summary'] or 'post')
        while len(base.encode('utf-8')) > 150:
            base = base[:-1]
        candidate = list_directory / (base + '_' + post_key_value[:8])
        entry = _entry(candidate)
        if entry is None:
            return candidate, False
        need(candidate.is_dir() and
             candidate == candidate.resolve(strict=True) and
             not candidate.is_symlink(), 'POST_DIRECTORY_CHANGED')
        need(not any(candidate.iterdir()), 'POST_DIRECTORY_UNEXPECTED_CONTENT')
        return candidate, True

    def _next_media_number(self, post_key_value):
        maximum = 0
        for event in self.events:
            if event['kind'] == 'completion':
                data = event['data']
            elif event['kind'] == 'publish-plan':
                data = event['data']
            else:
                continue
            if data['post_key'] != post_key_value:
                continue
            name = (data['target_file']['name'] if event['kind'] == 'completion'
                    else data['target_name'])
            match = re.fullmatch(r'media_(\d+)(\.[^./]+)', name)
            need(match is not None, 'PUBLISHED_MEDIA_NAME_CHANGED')
            maximum = max(maximum, int(match.group(1)))
        return maximum + 1

    def _append_publish_plan(self, attempt_id, intent_data,
                             verification_event):
        need(not self._pending_publish_plans(), 'PENDING_NAMING_TRANSACTION')
        verification = verification_event['data']
        source = verification['manifest'][0]
        suffix = Path(source['name']).suffix
        expected_suffixes = (PHOTO_SUFFIXES if verification['kind'] == PHOTO
                             else VIDEO_SUFFIXES)
        need(suffix and suffix.lower() in expected_suffixes,
             'UNSUPPORTED_MEDIA_EXTENSION')
        target_directory, existed = self._post_directory_for_publish(
            intent_data['post_key'])
        number = self._next_media_number(intent_data['post_key'])
        width = max(3, len(str(number)))
        target_name = 'media_%0*d%s' % (width, number, suffix)
        need(_entry(target_directory / target_name) is None,
             'TARGET_ALREADY_EXISTS')
        verification_raw = encoded(verification_event)
        data = dict(schema='line-notes-publish-plan/v1',
                    transaction_id=uuid.uuid4().hex,
                    attempt_id=attempt_id,
                    media_key=intent_data['media_key'],
                    post_key=intent_data['post_key'],
                    verification_sequence=verification_event['sequence'],
                    verification_sha256=digest(verification_raw),
                    source=source,
                    list_directory=str(self._require_current_list_directory()),
                    target_directory=str(target_directory),
                    target_name=target_name,
                    number=number,
                    extension=suffix,
                    target_directory_existed=existed)
        self.append('publish-plan', data)
        return self.events[-1]

    def _progress_events(self, transaction_id, action=None):
        rows = [event for event in self.events
                if event['kind'] == 'publish-progress' and
                event['data']['transaction_id'] == transaction_id]
        if action is not None:
            rows = [event for event in rows if event['data']['action'] == action]
        return rows

    def _append_progress(self, transaction_id, action, details):
        existing = self._progress_events(transaction_id, action)
        need(len(existing) <= 1, 'DUPLICATE_PUBLISH_PROGRESS')
        if existing:
            return existing[0]
        data = dict(details, schema='line-notes-publish-progress/v1',
                    transaction_id=transaction_id, action=action,
                    recorded_at=_utc_now())
        self.append('publish-progress', data)
        return self.events[-1]

    def _target_names_for_directory(self, directory, transaction_id=None):
        names = set()
        for event in self.events:
            if event['kind'] == 'completion' and \
                    event['data']['destination'] == str(directory):
                names.add(event['data']['target_file']['name'])
            elif event['kind'] == 'publish-plan' and \
                    event['data']['target_directory'] == str(directory):
                names.add(event['data']['target_name'])
        return names

    def _ensure_publish_directory(self, plan):
        target_directory = Path(plan['target_directory'])
        list_directory = Path(plan['list_directory'])
        current = self._require_current_list_directory()
        need(list_directory == current and
             target_directory.parent == current,
             'PUBLISH_DIRECTORY_OUTSIDE_CURRENT_LIST')
        entry = _entry(target_directory)
        if entry is None:
            need(plan['target_directory_existed'] is False,
                 'PRIOR_POST_DIRECTORY_MISSING_USE_DESTINATION')
            try:
                os.mkdir(str(target_directory), 0o700)
            except FileExistsError:
                pass
            sync_dir(current)
        entry = _entry(target_directory)
        need(entry is not None and stat.S_ISDIR(entry.st_mode) and
             not target_directory.is_symlink() and
             target_directory == target_directory.resolve(strict=True),
             'POST_DIRECTORY_CHANGED')
        expected_names = self._target_names_for_directory(
            target_directory, plan['transaction_id'])
        actual_names = {path.name for path in target_directory.iterdir()}
        need(actual_names <= expected_names,
             'POST_DIRECTORY_UNEXPECTED_CONTENT')
        info = target_directory.stat()
        directory_progress = self._progress_events(
            plan['transaction_id'], 'DIRECTORY_READY')
        if directory_progress:
            previous = directory_progress[0]['data']
            need(previous.get('directory_device') == info.st_dev and
                 previous.get('directory_inode') == info.st_ino,
                 'PUBLISH_DIRECTORY_IDENTITY_CHANGED')
        else:
            self._append_progress(plan['transaction_id'], 'DIRECTORY_READY',
                                  dict(target_directory=str(target_directory),
                                       directory_device=info.st_dev,
                                       directory_inode=info.st_ino))
        return target_directory, info

    def _source_row_matches(self, path, row, *, allow_link_change=False,
                            allowed_nlinks=(1,)):
        entry = _entry(path)
        need(entry is not None and stat.S_ISREG(entry.st_mode) and
             not path.is_symlink(), 'PUBLISH_SOURCE_CHANGED')
        info = os.stat(str(path), follow_symlinks=False)
        need((info.st_dev, info.st_ino, info.st_size,
              info.st_mtime_ns) ==
             (row['device'], row['inode'], row['size'], row['mtime_ns']) and
             info.st_nlink in allowed_nlinks,
             'PUBLISH_SOURCE_CHANGED')
        if not allow_link_change:
            need(info.st_ctime_ns == row['ctime_ns'],
                 'PUBLISH_SOURCE_CHANGED')
        raw, after = _read_regular(path, allowed_nlinks=allowed_nlinks,
                                   code='PUBLISH_SOURCE_CHANGED')
        need(digest(raw) == row['sha256'],
             'PUBLISH_SOURCE_CHANGED')
        return after

    def _execute_publish(self, plan_event):
        plan = plan_event['data']
        attempts = self._attempt_projection()
        intent_data = attempts['attempts'].get(plan['attempt_id'])
        need(intent_data is not None, 'PUBLISH_ATTEMPT_CHANGED')
        self._require_attempt_scan_binding(intent_data)
        verification_event = self._event_by_sequence(
            plan['verification_sequence'])
        need(verification_event is not None and
             verification_event['kind'] == 'verification' and
             verification_event['data']['attempt_id'] == plan['attempt_id'] and
             digest(encoded(verification_event)) == plan['verification_sha256'],
             'VERIFICATION_EVENT_CHANGED')
        verification = verification_event['data']
        source = plan['source']
        need(verification['manifest'] == [source] and
             verification['source'] == source,
             'PUBLISH_SOURCE_MANIFEST_CHANGED')
        target_directory, directory_info_value = \
            self._ensure_publish_directory(plan)
        source_path = Path(source['path'])
        target_path = target_directory / plan['target_name']
        source_entry = _entry(source_path)
        target_entry = _entry(target_path)
        if source_entry is not None and target_entry is not None:
            self._source_row_matches(
                source_path, source, allow_link_change=True,
                allowed_nlinks=(2,))
            source_info = os.stat(str(source_path), follow_symlinks=False)
            target_info = os.stat(str(target_path), follow_symlinks=False)
            need((source_info.st_dev, source_info.st_ino) ==
                 (target_info.st_dev, target_info.st_ino) and
                 target_info.st_nlink == 2,
                 'PUBLISH_PATH_STATE_AMBIGUOUS')
            self._source_row_matches(
                target_path, source, allow_link_change=True,
                allowed_nlinks=(2,))
        elif source_entry is None and target_entry is not None:
            target_info = self._source_row_matches(
                target_path, source, allow_link_change=True,
                allowed_nlinks=(1,))
            need((target_info.st_dev, target_info.st_ino) ==
                 (source['device'], source['inode']),
                 'PUBLISH_PATH_STATE_AMBIGUOUS')
        elif source_entry is not None:
            self._source_row_matches(
                source_path, source, allowed_nlinks=(1,))
            _link_no_replace(source_path, target_path)
        else:
            raise NotesError('PUBLISH_SOURCE_AND_TARGET_MISSING')
        linked_progress = self._progress_events(
            plan['transaction_id'], 'FILE_LINKED')
        target_info = os.stat(str(target_path), follow_symlinks=False)
        if not linked_progress:
            self._append_progress(plan['transaction_id'], 'FILE_LINKED',
                                  dict(target_file=str(target_path),
                                       target_device=target_info.st_dev,
                                       target_inode=target_info.st_ino,
                                       size=source['size'],
                                       sha256=source['sha256']))
        else:
            linked = linked_progress[0]['data']
            need(linked.get('target_device') == target_info.st_dev and
                 linked.get('target_inode') == target_info.st_ino and
                 linked.get('sha256') == source['sha256'],
                 'PUBLISH_TARGET_BINDING_CHANGED')
        if _entry(source_path) is not None:
            source_info = os.stat(str(source_path), follow_symlinks=False)
            target_info = os.stat(str(target_path), follow_symlinks=False)
            need((source_info.st_dev, source_info.st_ino) ==
                 (target_info.st_dev, target_info.st_ino),
                 'PUBLISH_UNLINK_BINDING_CHANGED')
            need(source_info.st_nlink == 2, 'PUBLISH_LINK_COUNT_CHANGED')
            _unlink_regular(source_path, 'PUBLISH_SOURCE_CHANGED')
        removed_progress = self._progress_events(
            plan['transaction_id'], 'SOURCE_REMOVED')
        if not removed_progress:
            target_info = os.stat(str(target_path), follow_symlinks=False)
            self._append_progress(plan['transaction_id'], 'SOURCE_REMOVED',
                                  dict(target_file=str(target_path),
                                       target_device=target_info.st_dev,
                                       target_inode=target_info.st_ino,
                                       sha256=source['sha256']))
        staging = source_path.parent
        if _entry(staging) is not None:
            need(staging.is_dir() and not staging.is_symlink() and
                 not any(staging.iterdir()), 'STAGING_NOT_EMPTY_AFTER_PUBLISH')
            os.rmdir(str(staging))
            sync_dir(staging.parent)
        target_info = os.stat(str(target_path), follow_symlinks=False)
        need(target_info.st_nlink == 1 and target_info.st_size == source['size'] and
             (target_info.st_dev, target_info.st_ino) ==
             (source['device'], source['inode']),
             'PUBLISH_TARGET_CHANGED')
        need(digest(read_file(target_path)) == source['sha256'],
             'PUBLISH_TARGET_CHANGED')
        directory_after = directory_info(target_directory)
        need(directory_after['device'] == directory_info_value.st_dev and
             directory_after['inode'] == directory_info_value.st_ino,
             'PUBLISH_DIRECTORY_IDENTITY_CHANGED')
        target_file = dict(name=plan['target_name'],
                           device=target_info.st_dev,
                           inode=target_info.st_ino,
                           size=target_info.st_size,
                           sha256=source['sha256'],
                           mtime_ns=target_info.st_mtime_ns,
                           ctime_ns=target_info.st_ctime_ns)
        naming = dict(transaction_id=plan['transaction_id'],
                      number=plan['number'],
                      target_name=plan['target_name'],
                      extension=plan['extension'],
                      list_directory=plan['list_directory'],
                      target_directory=plan['target_directory'])
        data = dict(schema='line-notes-completion/v1',
                    attempt_id=plan['attempt_id'],
                    media_key=plan['media_key'],
                    post_key=plan['post_key'],
                    transaction_id=plan['transaction_id'],
                    verification_sequence=plan['verification_sequence'],
                    verification_sha256=plan['verification_sha256'],
                    destination=plan['target_directory'],
                    target_file=target_file,
                    target_directory=directory_after,
                    naming=naming,
                    source_manifest=source,
                    verification=verification['verification'])
        self.append('completion', data)
        return self.events[-1]

    def _event_by_sequence(self, sequence):
        if type(sequence) is not int or sequence < 1 or sequence > len(self.events):
            return None
        event = self.events[sequence - 1]
        return event if event['sequence'] == sequence else None

    def verify(self, *, session_id, attempt_id, decoder=None,
               decoder_sha256=None, verifier=None,
               stability_interval=DEFAULT_STABILITY_INTERVAL,
               progress_callback=None, stall_seconds=DEFAULT_STALL_SECONDS):
        need(verifier is None or self._allow_injected_verification,
             'INJECTED_VERIFICATION_NOT_ALLOWED')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            self._require_attempt_scan_binding(
                projection['attempts'][attempt_id])
            need(media_key_value not in self._completion_projection()[0],
                 'COMPLETION_IMMUTABLE')
            result = self._attempt_result(attempt_id, projection)
            need(result == 'DOWNLOAD_FINISHED',
                 'KNOWN_DOWNLOAD_FINISH_REQUIRED')
            self._assert_no_local_changed()
            plans = [event for event in self._pending_publish_plans()
                     if event['data']['attempt_id'] == attempt_id]
            need(len(plans) <= 1, 'DUPLICATE_PUBLISH_PLAN')
            if plans:
                return self._execute_publish(plans[0])
            intent_data = projection['attempts'][attempt_id]
            staging = self._validate_staging(intent_data)
            verification_event = self._verification_for_attempt(attempt_id)
            if verification_event is None:
                stable = _stable_media_inventory(
                    staging, expected=1, interval=stability_interval)
                source = stable[0]
                kind = intent_data['identity']['kind']
                _validate_media_suffix(kind, source['name'])
                verification = _verify_media(
                    kind=kind, path=Path(source['path']),
                    row=source, identity=intent_data['identity'],
                    records=self.records, decoder=decoder,
                    decoder_sha256=decoder_sha256, verifier=verifier,
                    progress_callback=progress_callback,
                    stall_seconds=stall_seconds,
                    stability_interval=stability_interval)
                after = _inventory_once(staging)
                need(after == stable, 'CONTENT_CHANGED_AFTER_VERIFICATION')
                verification_data = dict(
                    schema='line-notes-verification/v1',
                    attempt_id=attempt_id,
                    media_key=media_key_value,
                    post_key=intent_data['post_key'],
                    kind=kind,
                    source=source,
                    manifest=[source],
                    manifest_sha256=digest(encoded([source])),
                    verification=verification,
                    verified_at=_utc_now())
                self.append('verification', verification_data)
                verification_event = self.events[-1]
            else:
                stable = _stable_media_inventory(
                    staging, expected=1, interval=stability_interval)
                need(stable[0] == verification_event['data']['manifest'][0],
                     'VERIFICATION_SOURCE_CHANGED')
            plan_event = self._append_publish_plan(
                attempt_id, intent_data, verification_event)
            return self._execute_publish(plan_event)

    def resume(self, *, progress_callback=None):
        with self.locked():
            plans = self._pending_publish_plans()
            need(len(plans) <= 1, 'AMBIGUOUS_PENDING_NAMING')
            self._assert_no_local_changed()
            if plans:
                attempt_id = plans[0]['data']['attempt_id']
                attempts = self._attempt_projection()
                intent_data = attempts['attempts'].get(attempt_id)
                need(intent_data is not None, 'PUBLISH_ATTEMPT_CHANGED')
                self._require_attempt_scan_binding(intent_data)
                completion = self._execute_publish(plans[0])
                return dict(action='PUBLISH_RESUMED',
                            completion=completion['data'],
                            dispatch_authorized=False)
            projection = self._attempt_projection()
            actions = []
            for media_key_value, attempt_id in projection['latest_by_media'].items():
                if media_key_value in self._completion_projection()[0]:
                    continue
                self._require_attempt_scan_binding(
                    projection['attempts'][attempt_id])
                result = self._attempt_result(attempt_id, projection)
                if result in (None, 'UNKNOWN'):
                    action = 'RECONCILE_REQUIRED'
                elif result == 'DOWNLOAD_FINISHED':
                    action = 'VERIFY_REQUIRED'
                else:
                    action = 'RECOVERY_AVAILABLE'
                actions.append(dict(media_key=media_key_value,
                                    attempt_id=attempt_id, action=action))
            return dict(action='NO_NAMING_TRANSACTION', pending=actions,
                        summary=self._project_summary(),
                        dispatch_authorized=False)


def _is_hex(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[0-9a-f]{64}', value))


def _public_media_source(source):
    return {key: source[key] for key in
            ('name', 'size', 'sha256', 'mtime_ns', 'ctime_ns')}


def _is_nonnegative_int(value):
    return type(value) is int and value >= 0


def _is_positive_json_number(value):
    if type(value) is int:
        return value > 0
    return type(value) is float and math.isfinite(value) and value > 0


def _validate_video_decode_stream(row, probe_stream):
    code = 'INVALID_VIDEO_DECODE_EVIDENCE'
    required = ('index', 'codec_type', 'codec_name', 'duration',
                'nb_frames', 'decode', 'coverage')
    need(isinstance(row, dict) and set(required) <= set(row), code)
    index = row.get('index')
    need(_is_nonnegative_int(index), code)
    need(row.get('codec_type') in ('video', 'audio'), code)
    need(isinstance(row.get('codec_name'), str) and bool(row['codec_name']),
         code)
    duration = row.get('duration')
    need(duration is None or _is_positive_json_number(duration), code)
    nb_frames = row.get('nb_frames')
    need(nb_frames is None or (type(nb_frames) is int and nb_frames > 0), code)
    need(duration is not None or nb_frames is not None, code)

    decode = row.get('decode')
    need(isinstance(decode, dict), code)
    need(type(decode.get('exit_code')) is int and decode['exit_code'] == 0,
         code)
    need(decode.get('stream_index') == index, code)
    command = decode.get('command')
    need(isinstance(command, list) and bool(command) and
         all(isinstance(value, str) for value in command) and
         '0:{}'.format(index) in command, code)
    need(decode.get('stdout_eof') is True, code)
    need(type(decode.get('stdout_bytes')) is int and
         decode['stdout_bytes'] > 0, code)
    need(_is_hex(decode.get('stdout_sha256')), code)
    need(decode.get('stderr_empty') is True and
         type(decode.get('stderr_bytes')) is int and
         decode['stderr_bytes'] == 0, code)
    need(_is_hex(decode.get('stderr_sha256')), code)
    if 'stderr_preview' in decode:
        need(isinstance(decode['stderr_preview'], str), code)
    progress = decode.get('progress')
    need(isinstance(progress, dict), code)
    need(progress.get('final_progress') == 'end', code)
    need(isinstance(progress.get('last'), dict) and
         progress['last'].get('progress') == 'end', code)
    final_out_time = progress.get('final_out_time_us')
    final_frame = progress.get('final_frame')
    need(final_out_time is None or _is_nonnegative_int(final_out_time), code)
    need(final_frame is None or _is_nonnegative_int(final_frame), code)
    need(final_out_time is not None or final_frame is not None, code)

    coverage = row.get('coverage')
    need(isinstance(coverage, dict), code)
    need(coverage.get('duration_covered') is True and
         coverage.get('frames_covered') is True, code)
    need(coverage.get('duration_seconds') == duration and
         coverage.get('expected_frames') == nb_frames, code)
    observed_out_time = coverage.get('observed_out_time_us')
    observed_frames = coverage.get('observed_frames')
    need(observed_out_time is None or _is_nonnegative_int(observed_out_time),
         code)
    need(observed_frames is None or _is_nonnegative_int(observed_frames), code)
    if duration is not None:
        need(_is_nonnegative_int(observed_out_time), code)
        try:
            duration_covered = media_verify._duration_coverage(
                duration, observed_out_time)
        except media_verify.MediaVerificationError as exc:
            raise NotesError(code) from exc
        need(duration_covered is True, code)
    if nb_frames is not None:
        need(_is_nonnegative_int(observed_frames) and
             observed_frames >= nb_frames, code)
    need(observed_out_time == final_out_time and
         observed_frames == final_frame, code)

    need(isinstance(probe_stream, dict), 'INVALID_VIDEO_PROBE_EVIDENCE')
    need(probe_stream.get('index') == index and
         probe_stream.get('codec_type') == row['codec_type'] and
         probe_stream.get('codec_name') == row['codec_name'] and
         probe_stream.get('duration_seconds') == duration and
         probe_stream.get('expected_frames') == nb_frames,
         'INVALID_VIDEO_PROBE_EVIDENCE')


def _validate_verification_payload(kind, source, verification, *,
                                   allow_injected=False):
    need(isinstance(verification, dict) and bool(verification),
         'INVALID_VERIFICATION_EVIDENCE')
    verifier = verification.get('verifier')
    if verifier == 'INJECTED':
        need(allow_injected, 'INJECTED_VERIFICATION_NOT_ALLOWED')
        result = verification.get('result')
        need(isinstance(result, dict) and result.get('verdict') == 'PASS',
             'INVALID_INJECTED_VERIFICATION')
        need(verification.get('source_sha256') == source['sha256'],
             'INVALID_INJECTED_VERIFICATION')
        return

    need(verifier in ('IMAGEIO', 'FFMPEG_NULL_DECODE'),
         'UNKNOWN_VERIFICATION_METHOD')
    public_source = _public_media_source(source)
    need(verification.get('verdict') == 'PASS' and
         verification.get('kind') == kind and
         verification.get('source') == public_source and
         verification.get('manifest') == [public_source] and
         verification.get('manifest_sha256') ==
         digest(encoded([public_source])),
         'INVALID_VERIFICATION_MANIFEST')
    need(type(verification.get('stable_sample_count')) is int and
         verification['stable_sample_count'] >= 2 and
         isinstance(verification.get('stable_samples'), list) and
         len(verification['stable_samples']) >= 2,
         'INVALID_VERIFICATION_STABILITY')
    need(verification.get('dispatch_authorized') is False and
         verification.get('sensor_verified') is False and
         verification.get('real_line_e2e') == 'NOT_TESTED',
         'INVALID_VERIFICATION_SCOPE')

    if kind == PHOTO:
        need(verifier == 'IMAGEIO' and
             _is_nonnegative_int(verification.get('returncode')) and
             verification['returncode'] == 0 and
             _is_hex(verification.get('stdout_sha256')) and
             _is_hex(verification.get('stderr_sha256')),
             'INVALID_PHOTO_VERIFICATION')
        evidence = verification.get('full_decode_evidence')
        need(isinstance(evidence, dict) and
             _is_nonnegative_int(evidence.get('exit_code')) and
             evidence['exit_code'] == 0 and
             isinstance(evidence.get('command'), list) and
             bool(evidence['command']) and
             _is_hex(evidence.get('stdout_sha256')) and
             _is_hex(evidence.get('stderr_sha256')),
             'INVALID_PHOTO_DECODE_EVIDENCE')
        imageio = verification.get('result')
        need(isinstance(imageio, dict) and imageio.get('verdict') == 'PASS' and
             imageio.get('readOnly') is True and
             type(imageio.get('expected')) is int and
             imageio.get('expected') == 1 and
             type(imageio.get('actualEntries')) is int and
             imageio.get('actualEntries') == 1,
             'INVALID_PHOTO_DECODE_EVIDENCE')
        entries = imageio.get('entries')
        need(isinstance(entries, list) and len(entries) == 1 and
             isinstance(entries[0], dict) and
             entries[0].get('name') == public_source['name'] and
             entries[0].get('sha256') == public_source['sha256'] and
             entries[0].get('decoded') is True and
             type(entries[0].get('width')) is int and entries[0]['width'] > 0 and
             type(entries[0].get('height')) is int and entries[0]['height'] > 0,
             'INVALID_PHOTO_DECODE_ENTRY')
        return

    need(verifier == 'FFMPEG_NULL_DECODE' and
         verification.get('completed') is True and
         type(verification.get('valid_video_streams')) is int and
         verification['valid_video_streams'] > 0 and
         verification.get('source_sha256') == public_source['sha256'],
         'INVALID_VIDEO_VERIFICATION')
    tools = verification.get('tools')
    expected_tools = {
        'ffmpeg': (str(FFMPEG), media_verify.FFMPEG_SHA256),
        'ffprobe': (str(FFPROBE), media_verify.FFPROBE_SHA256),
    }
    need(isinstance(tools, dict) and set(tools) == set(expected_tools),
         'INVALID_VIDEO_TOOL_EVIDENCE')
    for name, (path, sha256) in expected_tools.items():
        tool = tools.get(name)
        need(isinstance(tool, dict) and
             tool.get('configured_path') == path and
             tool.get('path') == path and
             tool.get('sha256') == sha256 and
             tool.get('expected_sha256') == sha256 and
             _is_hex(tool.get('sha256')) and
             _is_hex(tool.get('expected_sha256')) and
             tool.get('executable') is True and
             isinstance(tool.get('version'), dict) and
             tool['version'] == {'first_line': tool.get('version_first_line')} and
             isinstance(tool.get('version_first_line'), str) and
             bool(tool['version_first_line']),
             'INVALID_VIDEO_TOOL_EVIDENCE')
    probe = verification.get('probe')
    need(isinstance(probe, dict) and
         isinstance(probe.get('streams'), list) and
         bool(probe['streams']) and
         isinstance(probe.get('result'), dict) and
         _is_nonnegative_int(probe.get('exit_code')) and
         probe['exit_code'] == 0 and
         probe.get('stderr_empty') is True,
         'INVALID_VIDEO_PROBE_EVIDENCE')
    probe_streams = {}
    valid_video_streams = 0
    for probe_stream in probe['streams']:
        need(isinstance(probe_stream, dict) and
             _is_nonnegative_int(probe_stream.get('index')) and
             probe_stream['index'] not in probe_streams and
             probe_stream.get('codec_type') in ('video', 'audio') and
             isinstance(probe_stream.get('codec_name'), str) and
             bool(probe_stream['codec_name']) and
             type(probe_stream.get('attached_pic')) is bool and
             (probe_stream.get('duration_seconds') is None or
              _is_positive_json_number(probe_stream['duration_seconds'])) and
             (probe_stream.get('expected_frames') is None or
              (type(probe_stream['expected_frames']) is int and
               probe_stream['expected_frames'] > 0)),
             'INVALID_VIDEO_PROBE_EVIDENCE')
        if (probe_stream['codec_type'] == 'video' and
                not probe_stream['attached_pic']):
            valid_video_streams += 1
        probe_streams[probe_stream['index']] = probe_stream
    need(valid_video_streams > 0, 'INVALID_VIDEO_STREAM_EVIDENCE')
    streams = verification.get('decoded_streams')
    need(isinstance(streams, list) and bool(streams),
         'INVALID_VIDEO_DECODE_EVIDENCE')
    decoded_indexes = set()
    for row in streams:
        need(isinstance(row, dict) and
             _is_nonnegative_int(row.get('index')) and
             row['index'] not in decoded_indexes,
             'INVALID_VIDEO_DECODE_EVIDENCE')
        decoded_indexes.add(row['index'])
        _validate_video_decode_stream(
            row, probe_streams.get(row['index']))
    need(decoded_indexes == set(probe_streams) and
         verification.get('all_audio_video_streams_decoded') ==
         len(probe_streams) and
         verification.get('valid_video_streams') == valid_video_streams,
         'INVALID_VIDEO_DECODE_EVIDENCE')


def _validate_media_suffix(kind, name):
    suffix = Path(name).suffix
    allowed = PHOTO_SUFFIXES if kind == PHOTO else VIDEO_SUFFIXES
    need(bool(suffix) and suffix.lower() in allowed,
         'UNSUPPORTED_MEDIA_EXTENSION')
    return suffix


def _inventory_row(path):
    path = Path(path)
    entry = _entry(path)
    need(entry is not None and stat.S_ISREG(entry.st_mode) and
         entry.st_nlink == 1 and not path.is_symlink(),
         'DOWNLOADED_FILE_NOT_REGULAR')
    before = os.stat(str(path), follow_symlinks=False)
    raw = read_file(path)
    after = os.stat(str(path), follow_symlinks=False)
    need((before.st_dev, before.st_ino, before.st_size,
          before.st_mtime_ns, before.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size,
          after.st_mtime_ns, after.st_ctime_ns) and bool(raw),
         'DOWNLOADED_FILE_CHANGED')
    return dict(path=str(path), name=path.name, device=after.st_dev,
                inode=after.st_ino, nlink=after.st_nlink,
                size=after.st_size, sha256=digest(raw),
                mtime_ns=after.st_mtime_ns, ctime_ns=after.st_ctime_ns)


def _inventory_once(directory):
    root = _canonical_existing_directory(directory,
                                         'DOWNLOAD_DIRECTORY_CHANGED')
    rows = []
    for path in sorted(root.iterdir()):
        need(not path.name.startswith('.') and not path.is_symlink() and
             path.is_file(), 'UNEXPECTED_DOWNLOAD_ENTRY')
        rows.append(_inventory_row(path))
    return rows


def _stable_media_inventory(directory, *, expected, interval):
    need(type(expected) is int and expected > 0, 'MEDIA_COUNT_REQUIRED')
    samples = []
    for sample in range(3):
        if sample and interval:
            time.sleep(interval)
        rows = _inventory_once(directory)
        need(len(rows) == expected, 'DOWNLOAD_COUNT_MISMATCH')
        need(not samples or rows == samples[-1], 'DOWNLOAD_NOT_STABLE')
        samples.append(rows)
    return samples[-1]


def _verify_photo(path, row, records, decoder, decoder_sha256, *,
                  stability_interval=DEFAULT_STABILITY_INTERVAL):
    return _verify_photo_strict(
        path, row, records, decoder, decoder_sha256,
        stability_interval=stability_interval)


def _verify_video(path, row, stall_seconds, progress_callback, *,
                  stability_interval=DEFAULT_STABILITY_INTERVAL):
    return _verify_video_strict(
        path, row, None, progress_callback, stall_seconds,
        stability_interval)


def _strict_media_result(kind, path, row, records, decoder, decoder_sha256,
                         progress_callback, stall_seconds,
                         stability_interval):
    need(kind in MEDIA_KINDS, 'INVALID_MEDIA_KIND')
    try:
        if kind == PHOTO:
            result = media_verify.verify_media(
                str(path), kind, decoder=decoder,
                decoder_sha256=decoder_sha256,
                stable_interval=stability_interval,
                isolation_parent=records)
        else:
            callback = None
            if progress_callback is not None:
                def callback(event):
                    progress = event.get('progress')
                    stream = event.get('stream')
                    need(isinstance(progress, dict) and
                         isinstance(stream, dict), 'INVALID_VERIFIER_PROGRESS')
                    stream_index = stream.get('index')
                    for key, value in progress.items():
                        progress_callback(dict(stream_index=stream_index,
                                               key=key, value=value))
            result = media_verify.verify_media(
                str(path), kind, stable_interval=stability_interval,
                stall_timeout=stall_seconds,
                progress_callback=callback)
    except media_verify.MediaVerificationError as exc:
        raise NotesMediaVerificationError(exc.code, exc.evidence) from exc
    need(isinstance(result, dict), 'MEDIA_VERIFICATION_RESULT_REQUIRED')
    need(result.get('verdict') == 'PASS' and result.get('kind') == kind,
         'MEDIA_VERIFICATION_NOT_PASSED')
    source = result.get('source')
    manifest = result.get('manifest')
    need(isinstance(source, dict) and isinstance(manifest, list) and
         manifest == [source], 'MEDIA_VERIFICATION_MANIFEST_CHANGED')
    for key in ('name', 'size', 'sha256', 'mtime_ns', 'ctime_ns'):
        need(source.get(key) == row[key],
             'MEDIA_VERIFICATION_SOURCE_CHANGED')
    need(result.get('dispatch_authorized') is False and
         result.get('sensor_verified') is False and
         result.get('real_line_e2e') == 'NOT_TESTED',
         'MEDIA_VERIFICATION_SCOPE_CHANGED')
    need(type(result.get('stable_sample_count')) is int and
         result['stable_sample_count'] >= 2,
         'MEDIA_VERIFICATION_STABILITY_REQUIRED')
    return result


def _verify_photo_strict(path, row, records, decoder, decoder_sha256,
                         *, stability_interval):
    result = _strict_media_result(
        PHOTO, path, row, records, decoder, decoder_sha256, None,
        DEFAULT_STALL_SECONDS, stability_interval)
    imageio = result.get('imageio')
    evidence = result.get('full_decode_evidence')
    need(isinstance(imageio, dict) and isinstance(evidence, dict),
         'PHOTO_VERIFICATION_EVIDENCE_REQUIRED')
    return dict(result,
                verifier='IMAGEIO',
                command=evidence.get('command'),
                returncode=evidence.get('exit_code'),
                stdout_sha256=evidence.get('stdout_sha256'),
                stderr_sha256=evidence.get('stderr_sha256'),
                result=imageio)


def _verify_video_strict(path, row, records, progress_callback,
                         stall_seconds, stability_interval):
    result = _strict_media_result(
        VIDEO, path, row, records, None, None, progress_callback,
        stall_seconds, stability_interval)
    tools = result.get('tools')
    probe = result.get('probe')
    streams = result.get('streams')
    need(isinstance(tools, dict) and isinstance(probe, dict) and
         isinstance(streams, list), 'VIDEO_VERIFICATION_EVIDENCE_REQUIRED')
    for name in ('ffmpeg', 'ffprobe'):
        tool = tools.get(name)
        need(isinstance(tool, dict) and
             isinstance(tool.get('configured_path'), str) and
             isinstance(tool.get('version'), str) and
             isinstance(tool.get('version_first_line'), str),
             'VIDEO_TOOL_EVIDENCE_REQUIRED')
        tool['path'] = tool['configured_path']
        tool['version'] = {'first_line': tool['version_first_line']}
    probe_streams = probe.get('streams')
    need(isinstance(probe_streams, list), 'VIDEO_PROBE_EVIDENCE_REQUIRED')
    valid_video_streams = sum(
        stream.get('codec_type') == 'video' and
        stream.get('attached_pic') is False for stream in probe_streams
        if isinstance(stream, dict))
    decoded_streams = []
    for item in streams:
        need(isinstance(item, dict) and isinstance(item.get('stream'), dict) and
             isinstance(item.get('decode'), dict), 'VIDEO_DECODE_EVIDENCE_REQUIRED')
        stream = item['stream']
        decoded_streams.append(dict(
            index=stream.get('index'),
            codec_type=stream.get('codec_type'),
            codec_name=stream.get('codec_name'),
            duration=stream.get('duration_seconds'),
            nb_frames=stream.get('expected_frames'),
            decode=item['decode'],
            coverage=item.get('coverage')))
    return dict(result,
                verifier='FFMPEG_NULL_DECODE',
                tools=tools,
                valid_video_streams=valid_video_streams,
                decoded_streams=decoded_streams,
                completed=True,
                source_sha256=row['sha256'])


def _verify_media(*, kind, path, row, identity, records, decoder,
                  decoder_sha256, verifier, progress_callback,
                  stall_seconds, stability_interval):
    try:
        if verifier is not None:
            result = verifier(path, row, identity)
            need(isinstance(result, dict), 'INJECTED_VERIFIER_RESULT_REQUIRED')
            _json_value(result, 'INVALID_INJECTED_VERIFIER_RESULT')
            need(result.get('verdict') == 'PASS',
                 'INJECTED_VERIFIER_FAILED')
            if 'sha256' in result:
                need(result['sha256'] == row['sha256'],
                     'INJECTED_VERIFIER_CONTENT_MISMATCH')
            return dict(verifier='INJECTED', result=result,
                        source_sha256=row['sha256'])
        if kind == PHOTO:
            return _verify_photo_strict(
                path, row, records, decoder, decoder_sha256,
                stability_interval=stability_interval)
        need(kind == VIDEO, 'INVALID_MEDIA_KIND')
        return _verify_video_strict(
            path, row, records, progress_callback, stall_seconds,
            stability_interval)
    except media_verify.MediaVerificationError as exc:
        raise NotesMediaVerificationError(exc.code, exc.evidence) from exc


def _json_cli_argument(parser, value, label, default=None):
    if value is None:
        return default
    try:
        if value.startswith('@'):
            raw = Path(value[1:]).expanduser().read_bytes()
        else:
            raw = value.encode('utf-8')
        return strict_json(raw, 'INVALID_%s' % label.upper())
    except (OSError, ValueError, UnicodeError, DailyError) as exc:
        parser.error('%s must be valid JSON text or @JSON-file (%s)' %
                     (label, exc))


def _positive_cli_float(parser, value, label):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        parser.error('%s must be a positive number' % label)
    if not math.isfinite(number) or number <= 0:
        parser.error('%s must be a positive number' % label)
    return number


def _build_notes_parser():
    parser = argparse.ArgumentParser(
        prog='python -m line_backup_batch.notes',
        description='LINE Notes media ledger; records only, never grants GUI authority.',
        epilog=('JSON success output always includes dispatch_authorized=false. '
                'Syntax errors exit 2, business refusals exit 4, and '
                'unexpected internal errors exit 70 with '
                'status=INTERNAL_ERROR.'))
    sub = parser.add_subparsers(dest='command', required=True)

    def add_records(command, help_text):
        command.add_argument('--records-root', required=True,
                             help='One registered notes ledger directory')
        command.set_defaults(_records=True)
        return command

    lists = sub.add_parser('lists', help='List all registered notes ledgers')
    lists.add_argument('--collection', help='Notes collection (default: project notes-backup-records)')

    memory = sub.add_parser('memory', help='Read one ledger projection')
    add_records(memory, 'Read one ledger projection')

    init = sub.add_parser('init', help='Create a new notes ledger')
    init.add_argument('--collection', help='Notes collection (default: project notes-backup-records)')
    init.add_argument('--photo-root', required=True,
                      help='Project-local photo/video destination root')
    init.add_argument('--name', required=True, help='Observed list display name')
    init.add_argument('--visual-key', required=True,
                      help='Agent-grounded visual identity key')
    init.add_argument('--context-id', help='Optional foreground context identity')
    init.add_argument('--signals', help='Optional canonical JSON identity signals')
    init.add_argument('--binding-evidence', required=True,
                      help='Private list binding evidence file')
    init.add_argument('--history-scope-evidence', required=True,
                      help='Private complete-history scope evidence file')
    init.add_argument('--recovery-authorized', action='store_true',
                      help='Persist Owner recovery authorization for this ledger')

    bind = sub.add_parser('bind', help='Bind a fresh foreground/session')
    add_records(bind, 'Bind a fresh foreground/session')
    bind.add_argument('--session-id', required=True)
    bind.add_argument('--observation', required=True,
                      help='Private fresh list observation evidence')
    bind.add_argument('--handoff', required=True,
                      help='Private foreground handoff evidence')
    bind.add_argument('--context-id')

    scan = sub.add_parser('scan', help='Start or finish a complete list scan')
    add_records(scan, 'Start or finish a complete list scan')
    scan.add_argument('action', choices=('start', 'finish'))
    scan.add_argument('--session-id', required=True)
    scan.add_argument('--scan-id', help='Required for finish; forbidden for start')
    scan.add_argument('--evidence', required=True,
                      help='Private scan boundary/top-bottom evidence')

    page = sub.add_parser('page', help='Append one overlapping list page')
    add_records(page, 'Append one overlapping list page')
    page.add_argument('--session-id', required=True)
    page.add_argument('--scan-id', required=True)
    page.add_argument('--page-index', required=True, type=int)
    page.add_argument('--posts', required=True,
                      help='JSON array of {identity,date_summary} objects')
    page.add_argument('--overlap-keys', default='[]',
                      help='JSON array of post keys overlapping previous page')
    page.add_argument('--top-reached', action='store_true')
    page.add_argument('--bottom-reached', action='store_true')
    page.add_argument('--evidence', required=True,
                      help='Private page inventory evidence')

    post = sub.add_parser('post', help='Append post-level inventory and NO_MEDIA')
    add_records(post, 'Append post-level inventory and NO_MEDIA')
    post.add_argument('--session-id', required=True)
    post.add_argument('--post-key', required=True)
    post.add_argument('--date-summary', required=True)
    post.add_argument('--media-count', type=int)
    post.add_argument('--text-sha256')
    post.add_argument('--no-media', action='store_true')
    post.add_argument('--evidence', required=True)

    media = sub.add_parser('media', help='Append per-media inventory and source order')
    add_records(media, 'Append per-media inventory and source order')
    media.add_argument('--session-id', required=True)
    media.add_argument('--post-key', required=True)
    media.add_argument('--items', required=True,
                       help='JSON array of {identity} objects in source order')
    media.add_argument(
        '--missing', default='[]',
        help='JSON array of {media_key,source_order,reason} prior-media omissions')
    media.add_argument('--evidence', required=True)

    intent = sub.add_parser('intent', help='Persist one download attempt before dispatch')
    add_records(intent, 'Persist one download attempt before dispatch')
    intent.add_argument('--session-id', required=True)
    intent.add_argument('--media-key', required=True)
    intent.add_argument('--recovery-evidence',
                        help='Required only when recovering a STOPPED/NOT_SENT attempt')

    outcome = sub.add_parser('outcome', help='Append the first observed attempt outcome')
    add_records(outcome, 'Append the first observed attempt outcome')
    outcome.add_argument('--session-id', required=True)
    outcome.add_argument('--attempt-id', required=True)
    outcome.add_argument('--outcome', required=True, type=str.upper,
                         choices=OUTCOMES)
    outcome.add_argument('--evidence', required=True)

    reconcile = sub.add_parser('reconcile', help='Append evidence resolving UNKNOWN')
    add_records(reconcile, 'Append evidence resolving UNKNOWN')
    reconcile.add_argument('--session-id', required=True)
    reconcile.add_argument('--attempt-id', required=True)
    reconcile.add_argument('--result', required=True, type=str.upper,
                           choices=OUTCOMES)
    reconcile.add_argument('--evidence', required=True)

    verify = sub.add_parser('verify', help='Verify a DOWNLOAD_FINISHED attempt and publish')
    add_records(verify, 'Verify a DOWNLOAD_FINISHED attempt and publish')
    verify.add_argument('--session-id', required=True)
    verify.add_argument('--attempt-id', required=True)
    verify.add_argument('--decoder', help='Photo ImageIO decoder executable')
    verify.add_argument('--decoder-sha256', help='Expected decoder SHA-256')
    verify.add_argument('--stall-seconds', type=float,
                        default=DEFAULT_STALL_SECONDS,
                        help='Video decode progress watchdog seconds')

    resume = sub.add_parser('resume', help='Resume one pending naming/publish transaction')
    add_records(resume, 'Resume one pending naming/publish transaction')

    summary = sub.add_parser('summary', help='Project one ledger summary')
    add_records(summary, 'Project one ledger summary')

    destination = sub.add_parser('destination', help='Append a new destination root')
    add_records(destination, 'Append a new destination root')
    destination.add_argument('--photo-root', required=True)
    destination.add_argument('--session-id', required=True)
    destination.add_argument('--evidence', required=True)

    exclude = sub.add_parser('exclude', help='Mark observed media EXCLUDED with evidence')
    add_records(exclude, 'Mark observed media EXCLUDED with evidence')
    exclude.add_argument('--media-key', required=True)
    exclude.add_argument('--session-id', required=True)
    exclude.add_argument('--reason', required=True)
    exclude.add_argument('--evidence', required=True)

    protect = sub.add_parser('protect', help='Mark observed media PROTECTED_HISTORY with evidence')
    add_records(protect, 'Mark observed media PROTECTED_HISTORY with evidence')
    protect.add_argument('--media-key', required=True)
    protect.add_argument('--reason', required=True)
    protect.add_argument('--evidence', required=True)
    return parser


def _print_cli_result(value):
    if isinstance(value, dict):
        output = dict(value)
    else:
        output = {'result': value}
    output['dispatch_authorized'] = False
    print(json.dumps(output, ensure_ascii=False, separators=(',', ':')))


def _cli_progress(row):
    print(json.dumps(dict(progress=row), ensure_ascii=False,
                     separators=(',', ':')), file=sys.stderr, flush=True)


def main(argv=None):
    parser = _build_notes_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == 'lists':
            result = NotesCollection(args.collection).lists()
        elif args.command == 'init':
            identity = list_identity(
                visual_key=args.visual_key,
                context_id=args.context_id,
                signals=_json_cli_argument(parser, args.signals,
                                           '--signals', None))
            result = NotesCollection(args.collection).create(
                photo_root=args.photo_root,
                display_name=args.name,
                identity=identity,
                binding_evidence=args.binding_evidence,
                history_scope_evidence=args.history_scope_evidence,
                recovery_authorized=args.recovery_authorized)
        elif args.command in ('memory', 'bind', 'scan', 'page', 'post',
                              'media', 'intent', 'outcome', 'reconcile',
                              'verify', 'resume', 'summary', 'destination',
                              'exclude', 'protect'):
            records = NotesRecords(args.records_root)
            if args.command == 'memory':
                result = records.memory()
            elif args.command == 'bind':
                result = records.bind(
                    session_id=args.session_id,
                    observation=args.observation,
                    handoff=args.handoff,
                    context_id=args.context_id)
            elif args.command == 'scan':
                if args.action == 'start':
                    if args.scan_id is not None:
                        parser.error('--scan-id is not accepted for scan start')
                elif args.scan_id is None:
                    parser.error('--scan-id is required for scan finish')
                result = records.scan(
                    session_id=args.session_id, action=args.action.upper(),
                    scan_id=args.scan_id, evidence=args.evidence)
            elif args.command == 'page':
                posts = _json_cli_argument(parser, args.posts, '--posts')
                overlap = _json_cli_argument(parser, args.overlap_keys,
                                             '--overlap-keys', [])
                result = records.page(
                    session_id=args.session_id, scan_id=args.scan_id,
                    page_index=args.page_index, posts=posts,
                    top_reached=args.top_reached,
                    bottom_reached=args.bottom_reached,
                    overlap_keys=overlap, evidence=args.evidence)
            elif args.command == 'post':
                if args.no_media:
                    if args.media_count not in (None, 0):
                        parser.error('--no-media conflicts with nonzero --media-count')
                    media_count = 0
                elif args.media_count is None:
                    parser.error('--media-count is required unless --no-media is used')
                else:
                    media_count = args.media_count
                result = records.record_post(
                    session_id=args.session_id,
                    post_key_value=args.post_key,
                    date_summary=args.date_summary,
                    media_count=media_count,
                    text_sha256=args.text_sha256,
                    evidence=args.evidence,
                    no_media=args.no_media)
            elif args.command == 'media':
                items = _json_cli_argument(parser, args.items, '--items')
                missing = _json_cli_argument(parser, args.missing, '--missing', [])
                result = records.record_media(
                    session_id=args.session_id,
                    post_key_value=args.post_key,
                    items=items, missing=missing, evidence=args.evidence)
            elif args.command == 'intent':
                result = records.intent(
                    session_id=args.session_id,
                    media_key_value=args.media_key,
                    recovery_evidence=args.recovery_evidence)
            elif args.command == 'outcome':
                result = records.outcome(
                    session_id=args.session_id, attempt_id=args.attempt_id,
                    outcome=args.outcome, evidence=args.evidence)
            elif args.command == 'reconcile':
                result = records.reconcile(
                    session_id=args.session_id, attempt_id=args.attempt_id,
                    result=args.result, evidence=args.evidence)
            elif args.command == 'verify':
                if bool(args.decoder) != bool(args.decoder_sha256):
                    parser.error('--decoder and --decoder-sha256 must be provided together')
                stall_seconds = _positive_cli_float(
                    parser, args.stall_seconds, '--stall-seconds')
                result = records.verify(
                    session_id=args.session_id, attempt_id=args.attempt_id,
                    decoder=args.decoder,
                    decoder_sha256=args.decoder_sha256,
                    progress_callback=_cli_progress,
                    stall_seconds=stall_seconds)
            elif args.command == 'resume':
                result = records.resume(progress_callback=_cli_progress)
            elif args.command == 'summary':
                result = records.summary()
            elif args.command == 'destination':
                result = records.destination(
                    photo_root=args.photo_root, session_id=args.session_id,
                    evidence=args.evidence)
            elif args.command == 'exclude':
                result = records.exclude(
                    session_id=args.session_id,
                    media_key_value=args.media_key,
                    reason=args.reason, evidence=args.evidence)
            elif args.command == 'protect':
                result = records.protect(
                    media_key_value=args.media_key,
                    reason=args.reason, evidence=args.evidence)
        else:
            parser.error('unknown command')
        _print_cli_result(result)
        return 0
    except (NotesError, DailyError, NotesMediaVerificationError, OSError,
            subprocess.SubprocessError) as exc:
        payload = dict(status='REFUSED', reason=str(exc),
                       dispatch_authorized=False)
        if isinstance(exc, NotesMediaVerificationError):
            payload['verification_code'] = exc.code
            payload['evidence'] = exc.evidence
        print(json.dumps(payload,
                         ensure_ascii=False, separators=(',', ':')))
        return 4
    except Exception:
        print(json.dumps(dict(status='INTERNAL_ERROR',
                              reason='UNEXPECTED_EXCEPTION',
                              dispatch_authorized=False),
                         ensure_ascii=False, separators=(',', ':')))
        return 70


if __name__ == '__main__':
    raise SystemExit(main())
