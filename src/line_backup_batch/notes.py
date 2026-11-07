"""LINE Notes media ledger and offline verification.

This module records Agent-grounded observations. It never observes LINE,
clicks controls, grants GUI authority, or treats a filename/hash as source
identity. The permanent event log is the only business-state source.
"""
import argparse
import contextlib
import datetime
import errno
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

from . import media_verify, notes_evidence
from .daily import (DailyError, create_json, digest, encoded, read_file,
                    safe_component, strict_json, sync_dir)
from .notes_evidence import NotesEvidenceError


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
READ_ONLY_COMMANDS = frozenset(('lists', 'memory', 'summary',
                                'evidence-audit'))

RESTART_PATH_POLICY = 'SIBLING_VERSION_COPY'
RESTART_SCOPE_SCHEMA = 'line-notes-restart-scope/v1'
RESTART_CONFIRM_SCHEMA = 'line-notes-restart-confirm/v1'
RESTART_COPY_PLAN_SCHEMA = 'line-notes-restart-copy-plan/v1'
RESTART_CANDIDATE_SCHEMA = 'line-notes-restart-candidate/v1'
RESTART_ACTIVATION_SCHEMA = 'line-notes-restart-activation/v1'

PHOTO_SUFFIXES = frozenset(('.jpg', '.jpeg', '.png', '.heic', '.heif',
                            '.webp', '.tif', '.tiff', '.gif'))
VIDEO_SUFFIXES = frozenset(('.mp4', '.mov', '.m4v', '.avi', '.mkv'))
FFMPEG = media_verify.FFMPEG_PATH
FFPROBE = media_verify.FFPROBE_PATH
DEFAULT_STABILITY_INTERVAL = 0.2
DEFAULT_STALL_SECONDS = 120.0


class NotesError(ValueError):
    pass


class NotesLockBusy(NotesError):
    def __init__(self, scope):
        super().__init__('NOTES_LOCK_BUSY')
        self.scope = scope


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
def _file_lock(path, create=False, scope='records'):
    fd = _open_lock(path, create)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                raise
            raise NotesLockBusy(scope) from exc
        yield
    finally:
        os.close(fd)


def _evidence_directory(records, create=False):
    path = Path(records) / 'evidence'
    if create and _entry(path) is None:
        os.mkdir(str(path), 0o700)
        sync_dir(Path(records))
    return _canonical_existing_directory(path, 'EVIDENCE_DIRECTORY_CHANGED')


def _preflight_evidence(source, expected_context=None):
    try:
        return notes_evidence.inspect_source_bundle(
            source, expected_context, verify_sources=True)
    except notes_evidence.NotesEvidenceError as exc:
        raise NotesError(exc.code) from exc


def _preserve_evidence(records, source, expected_context=None,
                       expected_reference=None):
    try:
        return notes_evidence.preserve_bundle(
            records, source, expected_context, expected_reference)
    except notes_evidence.NotesEvidenceError as exc:
        raise NotesError(exc.code) from exc


def _check_evidence(records, ref, code='EVIDENCE_DRIFT', expected_context=None):
    _check_exact(ref, ('path', 'bytes', 'sha256'), code)
    path = Path(ref['path'])
    evidence = _evidence_directory(records)
    need(path.parent == evidence and path.name == ref['sha256'],
         'EVIDENCE_BINDING_CHANGED')
    try:
        return notes_evidence.load_saved_evidence(
            evidence, ref, expected_context)
    except notes_evidence.NotesEvidenceError as exc:
        raise NotesError(exc.code) from exc


def _check_scan_context_evidence(records, ref, expected_context):
    loaded = _check_evidence(records, ref, expected_context=expected_context)
    if loaded['classification'] == 'REFERENCE_VERIFIED':
        need(expected_context['scan_id'] != notes_evidence.UNKNOWN,
             'EVIDENCE_SCAN_CONTEXT_REQUIRED')
    return loaded


def _evidence_context(**values):
    try:
        return notes_evidence.normalize_context(values)
    except notes_evidence.NotesEvidenceError as exc:
        raise NotesError(exc.code) from exc


def _event_sha256(event):
    return digest(encoded(event))


def _event_ref(event):
    return dict(sequence=event['sequence'], sha256=_event_sha256(event))


def _check_event_ref(value, code):
    need(isinstance(value, dict) and
         set(value) == {'sequence', 'sha256'} and
         type(value['sequence']) is int and value['sequence'] >= 1,
         code)
    _hex(value['sha256'], code)
    return value


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
        with _file_lock(collection / '.lock', scope='collection'):
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
        key = list_key(identity)
        context = dict(list_key=key)
        binding_preflight = _preflight_evidence(binding_evidence, context)
        history_preflight = _preflight_evidence(
            history_scope_evidence, context)
        binding_source = binding_preflight['path']
        history_source = history_preflight['path']
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
            binding_ref = _preserve_evidence(
                records, binding_source, context,
                binding_preflight['reference'])
            history_ref = _preserve_evidence(
                records, history_source, context,
                history_preflight['reference'])
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
    def locked(self, *, audit_rows=None):
        records = _canonical_existing_directory(
            self.records, 'CANONICAL_NOTES_RECORDS_REQUIRED')
        need((records / 'events').is_dir() and
             (records / 'evidence').is_dir(), 'NOTES_RECORDS_STRUCTURE_CHANGED')
        with _file_lock(records / '.lock', scope='records'):
            try:
                self._load(records, audit_rows=audit_rows)
            except NotesError:
                raise
            except (ArithmeticError, RecursionError) as exc:
                raise NotesError('NOTES_LEDGER_NUMERIC_INVALID') from exc
            yield

    def _load(self, records, *, audit_rows=None):
        self._audit_rows = audit_rows
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
        self.events = events
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

    def _event_evidence(self, event, field, ref, expected_context,
                        *, require_v2=False, require_scan_context=False):
        if self._audit_rows is not None:
            row = notes_evidence.audit_saved_evidence(
                _evidence_directory(self.records), ref, expected_context)
            row = dict(row, event_sequence=event.get('sequence'),
                       event_kind=event['kind'], field=field)
            if 'page_sequence' in event.get('data', {}):
                row['event_page_sequence'] = event['data']['page_sequence']
            if require_v2 and (row['classification'] != 'V2' or
                               row['reference_check'] != 'VERIFIED'):
                row['integrity_ok'] = False
                row['errors'] = sorted(set(row['errors'] +
                                           ['EVIDENCE_BUNDLE_REQUIRED']))
            if (require_scan_context and row['classification'] == 'V2' and
                    expected_context['scan_id'] == notes_evidence.UNKNOWN):
                row['integrity_ok'] = False
                row['errors'] = sorted(set(row['errors'] +
                                           ['EVIDENCE_SCAN_CONTEXT_REQUIRED']))
            self._audit_rows.append(row)
            return row
        loaded = _check_evidence(
            self.records, ref, expected_context=expected_context)
        if require_v2:
            need(loaded['classification'] == 'REFERENCE_VERIFIED',
                 'EVIDENCE_BUNDLE_REQUIRED')
        if require_scan_context and loaded['classification'] == 'REFERENCE_VERIFIED':
            need(expected_context['scan_id'] != notes_evidence.UNKNOWN,
                 'EVIDENCE_SCAN_CONTEXT_REQUIRED')
        return loaded

    def _intent_evidence_context(self, attempt_id):
        for event in self.events:
            if event['kind'] != 'intent':
                continue
            data = event['data']
            if data['attempt_id'] == attempt_id:
                return _evidence_context(
                    list_key=self.list_data['list_key'],
                    post_key=data['post_key'], media_key=data['media_key'],
                    attempt_id=attempt_id, scan_id=data.get('scan_id'))
        raise NotesError('EVIDENCE_ATTEMPT_CONTEXT_MISSING')

    def _media_evidence_context(self, media_key_value):
        for event in reversed(self.events):
            if event['kind'] != 'media':
                continue
            data = event['data']
            keys = {row['media_key'] for row in data['items']}
            keys |= {row['media_key'] for row in data['missing']}
            if media_key_value in keys:
                return _evidence_context(
                    list_key=self.list_data['list_key'],
                    post_key=data['post_key'], media_key=media_key_value,
                    scan_id=data.get('scan_id'))
        raise NotesError('EVIDENCE_MEDIA_CONTEXT_MISSING')

    def _restart_list_directories(self):
        directories = {Path(self.events[0]['data']['list_directory'])}
        for event in self.events[1:]:
            if event['kind'] == 'destination':
                directories.add(Path(event['data']['list_directory']))
        return directories

    def _list_directory_at(self, sequence):
        need(type(sequence) is int and sequence >= 1,
             'INVALID_EVENT_SEQUENCE')
        current = Path(self.events[0]['data']['list_directory'])
        for event in self.events:
            if event['sequence'] >= sequence:
                break
            if event['kind'] == 'destination':
                candidate = Path(event['data']['list_directory'])
                need(candidate in self._restart_list_directories(),
                     'INVALID_DESTINATION_CHAIN')
                current = candidate
        return current

    def _validate_restart_scope_shape(self, scope, generation):
        need(type(generation) is int and generation >= 1,
             'INVALID_RESTART_GENERATION')
        _check_exact(scope, ('schema', 'list_key', 'scan', 'scan_id',
                             'path_policy', 'posts'),
                     'INVALID_RESTART_SCOPE')
        need(scope['schema'] == RESTART_SCOPE_SCHEMA and
             scope['list_key'] == self.list_data['list_key'] and
             isinstance(scope['scan_id'], str) and
             bool(scope['scan_id']) and
             scope['path_policy'] == RESTART_PATH_POLICY and
             isinstance(scope['posts'], list), 'INVALID_RESTART_SCOPE')
        _check_event_ref(scope['scan'], 'INVALID_RESTART_SCOPE')
        seen_posts = set()
        seen_media = set()
        seen_missing = set()
        seen_directories = set()
        scan_event = self._event_by_sequence(scope['scan']['sequence'])
        need(scan_event is not None and scan_event['kind'] == 'scan' and
             _event_ref(scan_event) == scope['scan'] and
             scan_event['data']['action'] == 'COMPLETE' and
             scan_event['data']['scan_id'] == scope['scan_id'],
             'INVALID_RESTART_SCOPE')
        scan_posts = {row['post_key']: row
                      for row in scan_event['data']['posts']}
        list_directories = self._restart_list_directories()
        need(bool(scope['posts']), 'INVALID_RESTART_SCOPE')
        for post in scope['posts']:
            _check_exact(post, ('post_key', 'identity', 'version_directory',
                                'reasons', 'media', 'missing'),
                         'INVALID_RESTART_SCOPE')
            _hex(post['post_key'], 'INVALID_RESTART_SCOPE')
            _check_identity_shape(post['identity'], 'POST')
            scan_post = scan_posts.get(post['post_key'])
            need(scan_post is not None and
                 scan_post['identity'] == post['identity'],
                 'INVALID_RESTART_SCOPE')
            version_directory = Path(post['version_directory'])
            parent_match = re.fullmatch(r'g([0-9]{8})',
                                        version_directory.parent.name)
            directory_generation = (
                int(parent_match.group(1)) if parent_match is not None
                else None)
            version_list_directory = (version_directory.parents[2]
                                      if len(version_directory.parents) >= 3
                                      else None)
            need(post_key(self.list_data['list_key'], post['identity']) ==
                 post['post_key'] and post['post_key'] not in seen_posts and
                 isinstance(post['version_directory'], str) and
                 version_directory.is_absolute() and
                 str(version_directory) == os.path.normpath(
                     str(version_directory)) and
                 version_directory == version_directory.absolute() and
                 version_directory.parent.parent.name == 'versions' and
                 version_list_directory in list_directories and
                 directory_generation is not None and
                 directory_generation >= 1 and
                 directory_generation == generation and
                 isinstance(post['reasons'], list) and post['reasons'] and
                 post['reasons'] == sorted(set(post['reasons'])) and
                 set(post['reasons']) <= {'LOCAL_CHANGED', 'UNKNOWN_ATTEMPT',
                                           'UNFINISHED_ATTEMPT',
                                           'PENDING_NAMING'} and
                 isinstance(post['media'], list) and bool(post['media']) and
                 isinstance(post['missing'], list), 'INVALID_RESTART_SCOPE')
            expected_directory = self._restart_version_directory(
                directory_generation, post['post_key'],
                scan_post['date_summary'], version_list_directory)
            need(version_directory == expected_directory and
                 version_directory not in seen_directories,
                 'INVALID_RESTART_SCOPE')
            for existing_path in (version_list_directory,
                                  version_directory.parent.parent,
                                  version_directory.parent,
                                  version_directory):
                existing = _entry(existing_path)
                if existing is None:
                    continue
                need(stat.S_ISDIR(existing.st_mode) and
                     not existing_path.is_symlink() and
                     existing_path == existing_path.resolve(strict=True),
                     'INVALID_RESTART_SCOPE')
            seen_directories.add(version_directory)
            seen_posts.add(post['post_key'])
            media_orders = set()
            for row in post['media']:
                _check_exact(row, ('media_key', 'identity', 'effective_kind',
                                   'source_order', 'prior_attempt',
                                   'prior_completion', 'prior_pending_plan',
                                   'local_files'), 'INVALID_RESTART_SCOPE')
                _hex(row['media_key'], 'INVALID_RESTART_SCOPE')
                _check_identity_shape(row['identity'], 'MEDIA')
                need(media_key(self.list_data['list_key'], post['post_key'],
                               row['identity']) == row['media_key'] and
                     row['media_key'] not in seen_media and
                     row['effective_kind'] in MEDIA_KINDS and
                     _is_nonnegative_int(row['source_order']) and
                     row['source_order'] not in media_orders and
                     row['local_files'] in (LOCAL_VERIFIED, LOCAL_MISSING,
                                            LOCAL_CHANGED,
                                            LOCAL_NOT_APPLICABLE),
                     'INVALID_RESTART_SCOPE')
                if row['prior_attempt'] is not None:
                    _check_event_ref(row['prior_attempt'],
                                     'INVALID_RESTART_SCOPE')
                if row['prior_completion'] is not None:
                    _check_event_ref(row['prior_completion'],
                                     'INVALID_RESTART_SCOPE')
                if row['prior_pending_plan'] is not None:
                    _check_event_ref(row['prior_pending_plan'],
                                     'INVALID_RESTART_SCOPE')
                seen_media.add(row['media_key'])
                media_orders.add(row['source_order'])
            for row in post['missing']:
                _check_exact(row, ('media_key', 'source_order', 'reason'),
                             'INVALID_RESTART_SCOPE')
                need(_is_hex(row['media_key']) and
                     _is_nonnegative_int(row['source_order']) and
                     row['media_key'] not in seen_media and
                     row['media_key'] not in seen_missing and
                     row['source_order'] not in media_orders and
                     isinstance(row['reason'], str) and bool(row['reason']),
                     'INVALID_RESTART_SCOPE')
                seen_missing.add(row['media_key'])
                media_orders.add(row['source_order'])
        return scope

    @staticmethod
    def _restart_scope_digest(restart_id, generation, expected_tip, scope):
        _hex(restart_id, 'INVALID_RESTART_ID')
        need(type(generation) is int and generation >= 1,
             'INVALID_RESTART_GENERATION')
        _check_event_ref(expected_tip, 'INVALID_RESTART_EXPECTED_TIP')
        return digest(encoded(dict(
            schema=RESTART_SCOPE_SCHEMA, restart_id=restart_id,
            generation=generation, expected_tip=expected_tip, scope=scope)))

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
            context = _evidence_context(list_key=data['list_key'])
            self._event_evidence(event, 'binding_evidence',
                                 data['binding_evidence'], context)
            self._event_evidence(event, 'history_scope_evidence',
                                 data['history_scope_evidence'], context)
            need(Path(data['list_directory']).parent == Path(data['photo_root']),
                 'INVALID_CREATED_EVENT')
        elif kind == 'binding':
            _check_exact(data, ('schema', 'session_id', 'context_id',
                                'observation', 'handoff'),
                         'INVALID_BINDING_EVENT')
            need(data['schema'] == 'line-notes-binding/v1' and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_BINDING_EVENT')
            context = _evidence_context(list_key=self.list_data['list_key'])
            self._event_evidence(event, 'observation', data['observation'],
                                 context)
            self._event_evidence(event, 'handoff', data['handoff'], context)
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
            self._event_evidence(
                event, 'evidence', data['evidence'],
                _evidence_context(list_key=self.list_data['list_key']))
        elif kind == 'scan':
            need(data.get('schema') == 'line-notes-scan/v1' and
                 data.get('action') in ('START', 'COMPLETE', 'INTERRUPTED') and
                 isinstance(data.get('scan_id'), str) and
                 bool(data.get('scan_id')) and
                 isinstance(data.get('session_id'), str) and
                 bool(data.get('session_id')), 'INVALID_SCAN_EVENT')
            self._event_evidence(
                event, 'evidence', data.get('evidence'),
                _evidence_context(
                    list_key=self.list_data['list_key'],
                    scan_id=(data.get('scan_id')
                             if data.get('action') != 'START' else None)))
            if data['action'] == 'START':
                required = {'schema', 'action', 'scan_id', 'session_id',
                            'evidence'}
                need(required <= set(data) and
                     set(data) <= required | {'purpose'},
                     'INVALID_SCAN_EVENT')
                if 'purpose' in data:
                    need(data['purpose'] == 'RECOVERY_EVALUATION',
                         'INVALID_SCAN_EVENT')
            elif data['action'] == 'INTERRUPTED':
                _check_exact(data, ('schema', 'action', 'scan_id',
                                    'session_id', 'reason', 'evidence'),
                             'INVALID_SCAN_EVENT')
                need(isinstance(data['reason'], str) and
                     bool(data['reason'].strip()), 'INVALID_SCAN_EVENT')
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
            _validate_evidence_ref_shape(data['evidence'],
                                         'INVALID_PAGE_EVENT')
            if self._audit_rows is not None:
                self._event_evidence(
                    event, 'evidence', data['evidence'],
                    _evidence_context(list_key=self.list_data['list_key'],
                                      scan_id=data['scan_id']),
                    require_scan_context=True)
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
            self._event_evidence(
                event, 'evidence', data['evidence'],
                _evidence_context(list_key=self.list_data['list_key'],
                                  post_key=data['post_key'],
                                  scan_id=data.get('scan_id')),
                require_scan_context=True)
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
            self._event_evidence(
                event, 'evidence', data['evidence'],
                _evidence_context(list_key=self.list_data['list_key'],
                                  post_key=data['post_key'],
                                  scan_id=data.get('scan_id')),
                require_scan_context=True)
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
            common = {'schema', 'media_key', 'post_key', 'identity',
                      'attempt_id', 'session_id', 'destination',
                      'directory_device', 'directory_inode',
                      'save_all_limit', 'save_all_count', 'recovery_of',
                      'recovery_evidence'}
            v2_fields = common | {'scan_id', 'effective_kind',
                                  'kind_correction_ref'}
            v3_fields = {'schema', 'restart_id', 'generation',
                         'confirmation_ref', 'prior_attempt',
                         'media_key', 'post_key', 'identity',
                         'effective_kind', 'kind_correction_ref',
                         'attempt_id', 'session_id', 'scan_id',
                         'destination', 'directory_device',
                         'directory_inode', 'save_all_limit',
                         'save_all_count'}
            need(isinstance(data, dict) and
                 ((data.get('schema') == 'line-notes-intent/v1' and
                   common <= set(data) and set(data) <= common | {'scan_id'}) or
                  (data.get('schema') == 'line-notes-intent/v2' and
                   set(data) == v2_fields) or
                  (data.get('schema') == 'line-notes-intent/v3' and
                   set(data) == v3_fields)), 'INVALID_INTENT_EVENT')
            if 'scan_id' in data:
                need(isinstance(data['scan_id'], str) and
                     bool(data['scan_id'].strip()), 'INVALID_INTENT_EVENT')
            need(_is_hex(data['media_key']) and _is_hex(data['post_key']) and
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
            earlier_corrections = [
                candidate for candidate in self.events
                if candidate['kind'] == 'media-kind-correction' and
                candidate['data']['media_key'] == data['media_key']]
            if data['schema'] == 'line-notes-intent/v1':
                need(not earlier_corrections,
                     'V1_INTENT_AFTER_KIND_CORRECTION')
            else:
                need(data['effective_kind'] in MEDIA_KINDS,
                     'INVALID_INTENT_EVENT')
                if data['kind_correction_ref'] is not None:
                    _check_event_ref(data['kind_correction_ref'],
                                     'INVALID_INTENT_EVENT')
            if data['schema'] == 'line-notes-intent/v3':
                _hex(data['restart_id'], 'INVALID_INTENT_EVENT')
                need(type(data['generation']) is int and data['generation'] >= 1,
                     'INVALID_INTENT_EVENT')
                _check_event_ref(data['confirmation_ref'],
                                 'INVALID_INTENT_EVENT')
                if data['prior_attempt'] is not None:
                    _check_event_ref(data['prior_attempt'],
                                     'INVALID_INTENT_EVENT')
            elif data['recovery_evidence'] is not None:
                self._event_evidence(
                    event, 'recovery_evidence', data['recovery_evidence'],
                    self._intent_evidence_context(data['recovery_of']))
        elif kind == 'outcome':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'outcome', 'evidence'), 'INVALID_OUTCOME_EVENT')
            need(data['schema'] == 'line-notes-outcome/v1' and
                 isinstance(data['attempt_id'], str) and
                 _is_hex(data['media_key']) and
                 data['outcome'] in OUTCOMES, 'INVALID_OUTCOME_EVENT')
            self._event_evidence(
                event, 'evidence', data['evidence'],
                self._intent_evidence_context(data['attempt_id']))
        elif kind == 'reconcile':
            _check_exact(data, ('schema', 'attempt_id', 'media_key',
                                'result', 'evidence'), 'INVALID_RECONCILE_EVENT')
            need(data['schema'] == 'line-notes-reconcile/v1' and
                 isinstance(data['attempt_id'], str) and
                 _is_hex(data['media_key']) and
                 data['result'] in OUTCOMES, 'INVALID_RECONCILE_EVENT')
            self._event_evidence(
                event, 'evidence', data['evidence'],
                self._intent_evidence_context(data['attempt_id']))
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
        elif kind == 'restart-confirm':
            _check_exact(data, ('schema', 'restart_id', 'generation',
                                'scope_digest', 'expected_tip', 'scope',
                                'evidence', 'session_id'),
                         'INVALID_RESTART_CONFIRM')
            need(data['schema'] == RESTART_CONFIRM_SCHEMA and
                 _is_hex(data['restart_id']) and
                 type(data['generation']) is int and data['generation'] >= 1 and
                 _is_hex(data['scope_digest']) and
                 isinstance(data['session_id'], str) and bool(data['session_id']),
                 'INVALID_RESTART_CONFIRM')
            _check_event_ref(data['expected_tip'], 'INVALID_RESTART_CONFIRM')
            self._validate_restart_scope_shape(
                data['scope'], data['generation'])
            expected_event = self._event_by_sequence(
                data['expected_tip']['sequence'])
            current_sequence = event.get('sequence', len(self.events) + 1)
            need(expected_event is not None and
                 _event_ref(expected_event) == data['expected_tip'] and
                 data['expected_tip']['sequence'] == current_sequence - 1,
                 'RESTART_EXPECTED_TIP_CHANGED')
            scan_event = self._event_by_sequence(data['scope']['scan']['sequence'])
            need(scan_event is not None and scan_event['kind'] == 'scan' and
                 scan_event['data']['action'] == 'COMPLETE' and
                 _event_ref(scan_event) == data['scope']['scan'] and
                 scan_event['data']['scan_id'] == data['scope']['scan_id'],
                 'RESTART_SCOPE_SCAN_CHANGED')
            need(data['scope_digest'] == self._restart_scope_digest(
                     data['restart_id'], data['generation'],
                     data['expected_tip'], data['scope']),
                 'RESTART_SCOPE_DIGEST_CHANGED')
            self._event_evidence(
                event, 'evidence', data['evidence'],
                _evidence_context(list_key=self.list_data['list_key'],
                                  scan_id=data['scope']['scan_id']),
                require_v2=True, require_scan_context=True)
        elif kind == 'restart-copy-plan':
            _check_exact(data, ('schema', 'plan_id', 'restart_id',
                                'generation', 'confirmation_ref',
                                'attempt_id', 'media_key', 'post_key',
                                'source', 'list_directory',
                                'target_directory', 'target_name',
                                'number', 'extension',
                                'target_directory_existed', 'created_at'),
                         'INVALID_RESTART_COPY_PLAN')
            need(data['schema'] == RESTART_COPY_PLAN_SCHEMA and
                 isinstance(data['plan_id'], str) and
                 re.fullmatch(r'[0-9a-f]{32}', data['plan_id']) is not None and
                 _is_hex(data['restart_id']) and
                 type(data['generation']) is int and data['generation'] >= 1 and
                 isinstance(data['attempt_id'], str) and bool(data['attempt_id']) and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 isinstance(data['list_directory'], str) and
                 isinstance(data['target_directory'], str) and
                 isinstance(data['target_name'], str) and
                 Path(data['target_name']).name == data['target_name'] and
                 type(data['number']) is int and data['number'] > 0 and
                 isinstance(data['extension'], str) and
                 data['target_name'].endswith(data['extension']) and
                 type(data['target_directory_existed']) is bool and
                 isinstance(data['created_at'], str) and bool(data['created_at']),
                 'INVALID_RESTART_COPY_PLAN')
            _check_event_ref(data['confirmation_ref'],
                             'INVALID_RESTART_COPY_PLAN')
            self._validate_source_row(data['source'],
                                      'INVALID_RESTART_SOURCE')
        elif kind == 'restart-candidate':
            _check_exact(data, ('schema', 'restart_id', 'generation',
                                'plan_ref', 'attempt_id', 'media_key',
                                'post_key', 'kind', 'source', 'candidate',
                                'manifest', 'manifest_sha256',
                                'verification', 'verified_at'),
                         'INVALID_RESTART_CANDIDATE')
            need(data['schema'] == RESTART_CANDIDATE_SCHEMA and
                 _is_hex(data['restart_id']) and
                 type(data['generation']) is int and data['generation'] >= 1 and
                 isinstance(data['attempt_id'], str) and bool(data['attempt_id']) and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 data['kind'] in MEDIA_KINDS and
                 isinstance(data['source'], dict) and
                 isinstance(data['candidate'], dict) and
                 isinstance(data['manifest'], list) and
                 data['manifest'] == [data['candidate']] and
                 data['manifest_sha256'] == digest(encoded(data['manifest'])) and
                 isinstance(data['verification'], dict) and
                 bool(data['verification']) and
                 isinstance(data['verified_at'], str) and
                 bool(data['verified_at']), 'INVALID_RESTART_CANDIDATE')
            _check_event_ref(data['plan_ref'], 'INVALID_RESTART_CANDIDATE')
            self._validate_source_row(data['source'],
                                      'INVALID_RESTART_CANDIDATE')
            self._validate_source_row(data['candidate'],
                                      'INVALID_RESTART_CANDIDATE')
            _json_value(data['verification'], 'INVALID_VERIFICATION_RESULT')
            _validate_verification_payload(
                data['kind'], data['candidate'], data['verification'],
                allow_injected=self._allow_injected_verification)
        elif kind == 'restart-activation':
            _check_exact(data, ('schema', 'restart_id', 'generation',
                                'confirmation_ref', 'scope_digest',
                                'candidates', 'session_id', 'activated_at'),
                         'INVALID_RESTART_ACTIVATION')
            need(data['schema'] == RESTART_ACTIVATION_SCHEMA and
                 _is_hex(data['restart_id']) and
                 type(data['generation']) is int and data['generation'] >= 1 and
                 _is_hex(data['scope_digest']) and
                 isinstance(data['candidates'], list) and
                 isinstance(data['session_id'], str) and bool(data['session_id']) and
                 isinstance(data['activated_at'], str) and bool(data['activated_at']),
                 'INVALID_RESTART_ACTIVATION')
            _check_event_ref(data['confirmation_ref'],
                             'INVALID_RESTART_ACTIVATION')
            seen = set()
            previous_key = None
            for row in data['candidates']:
                _check_exact(row, ('media_key', 'post_key',
                                   'candidate_ref', 'candidate'),
                             'INVALID_RESTART_ACTIVATION')
                need(_is_hex(row['media_key']) and _is_hex(row['post_key']) and
                     row['media_key'] not in seen and
                     (previous_key is None or previous_key < row['media_key']),
                     'INVALID_RESTART_ACTIVATION')
                _check_event_ref(row['candidate_ref'],
                                 'INVALID_RESTART_ACTIVATION')
                self._validate_source_row(row['candidate'],
                                          'INVALID_RESTART_ACTIVATION')
                seen.add(row['media_key'])
                previous_key = row['media_key']
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
        elif kind == 'evidence-correction':
            _check_exact(data, ('schema', 'page_sequence', 'page_sha256',
                                'original_evidence_sha256',
                                'replacement_ref', 'reason', 'session_id',
                                'previous_correction_ref'),
                         'INVALID_EVIDENCE_CORRECTION')
            need(data['schema'] == 'line-notes-evidence-correction/v1' and
                 type(data['page_sequence']) is int and
                 data['page_sequence'] >= 1 and
                 _is_hex(data['page_sha256']) and
                 _is_hex(data['original_evidence_sha256']) and
                 isinstance(data['reason'], str) and
                 bool(data['reason'].strip()) and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_EVIDENCE_CORRECTION')
            target = self._event_by_sequence(data['page_sequence'])
            need(target is not None and target['kind'] == 'page' and
                 digest(encoded(target)) == data['page_sha256'],
                 'EVIDENCE_CORRECTION_TARGET_CHANGED')
            original = _validate_evidence_ref_shape(
                target['data']['evidence'], 'INVALID_EVIDENCE_CORRECTION')
            need(original['sha256'] == data['original_evidence_sha256'],
                 'EVIDENCE_CORRECTION_ORIGINAL_CHANGED')
            if data['previous_correction_ref'] is not None:
                _check_event_ref(data['previous_correction_ref'],
                                 'INVALID_EVIDENCE_CORRECTION')
            self._event_evidence(
                event, 'replacement_ref', data['replacement_ref'],
                _evidence_context(list_key=self.list_data['list_key'],
                                  scan_id=target['data']['scan_id']),
                require_v2=True, require_scan_context=True)
        elif kind == 'media-kind-correction':
            _check_exact(data, ('schema', 'media_key', 'post_key', 'scan_id',
                                'inventory_sequence', 'inventory_sha256',
                                'from_kind', 'to_kind',
                                'previous_correction', 'evidence',
                                'session_id'),
                         'INVALID_MEDIA_KIND_CORRECTION')
            need(data['schema'] == 'line-notes-media-kind-correction/v1' and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 isinstance(data['scan_id'], str) and
                 bool(data['scan_id'].strip()) and
                 type(data['inventory_sequence']) is int and
                 data['inventory_sequence'] >= 1 and
                 _is_hex(data['inventory_sha256']) and
                 data['from_kind'] in MEDIA_KINDS and
                 data['to_kind'] in MEDIA_KINDS and
                 data['from_kind'] != data['to_kind'] and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_MEDIA_KIND_CORRECTION')
            if data['previous_correction'] is not None:
                _check_event_ref(data['previous_correction'],
                                 'INVALID_MEDIA_KIND_CORRECTION')
            self._event_evidence(
                event, 'evidence', data['evidence'],
                _evidence_context(list_key=self.list_data['list_key'],
                                  post_key=data['post_key'],
                                  media_key=data['media_key'],
                                  scan_id=data['scan_id']),
                require_v2=True, require_scan_context=True)
        elif kind == 'source-unavailable':
            _check_exact(data, ('schema', 'media_key', 'post_key',
                                'attempt_id', 'reason', 'evidence',
                                'session_id'),
                         'INVALID_SOURCE_UNAVAILABLE')
            need(data['schema'] == 'line-notes-source-unavailable/v1' and
                 _is_hex(data['media_key']) and _is_hex(data['post_key']) and
                 isinstance(data['attempt_id'], str) and
                 bool(data['attempt_id']) and
                 data['reason'] == 'SOURCE_EXPIRED' and
                 isinstance(data['session_id'], str) and
                 bool(data['session_id']), 'INVALID_SOURCE_UNAVAILABLE')
            self._event_evidence(
                event, 'evidence', data['evidence'],
                self._intent_evidence_context(data['attempt_id']),
                require_v2=True, require_scan_context=True)
        elif kind in ('exclusion', 'protection'):
            _check_exact(data, ('schema', 'media_key', 'reason', 'evidence'),
                         'INVALID_%s_EVENT' % kind.upper())
            need(data['schema'] == 'line-notes-%s/v1' % kind and
                 _is_hex(data['media_key']) and
                 isinstance(data['reason'], str) and
                 bool(data['reason'].strip()), 'INVALID_%s_EVENT' % kind.upper())
            self._event_evidence(
                event, 'evidence', data['evidence'],
                self._media_evidence_context(data['media_key']))
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

    def _evidence_correction_projection(self):
        by_page = {}
        latest = {}
        for event in self.events:
            if event['kind'] != 'evidence-correction':
                continue
            data = event['data']
            page_sequence = data['page_sequence']
            previous = latest.get(page_sequence)
            prior_ref = data['previous_correction_ref']
            if previous is None:
                need(prior_ref is None,
                     'EVIDENCE_CORRECTION_FORK')
            else:
                need(prior_ref == _event_ref(previous),
                     'EVIDENCE_CORRECTION_CHAIN_CHANGED')
            by_page.setdefault(page_sequence, []).append(event)
            latest[page_sequence] = event
        return by_page, latest

    def _media_kind_correction_projection(self):
        by_media = {}
        latest = {}
        terminal = {'intent', 'verification', 'completion', 'exclusion',
                    'protection'}
        for event in self.events:
            if event['kind'] != 'media-kind-correction':
                continue
            data = event['data']
            key = data['media_key']
            need(data['inventory_sequence'] < event['sequence'],
                 'MEDIA_KIND_INVENTORY_CHANGED')
            prefix = self.events[:event['sequence'] - 1]
            inventory = self._event_by_sequence(data['inventory_sequence'])
            need(inventory is not None and inventory['kind'] == 'media' and
                 _event_sha256(inventory) == data['inventory_sha256'],
                 'MEDIA_KIND_INVENTORY_CHANGED')
            inventory_data = inventory['data']
            need(inventory_data['post_key'] == data['post_key'] and
                 inventory_data.get('scan_id') == data['scan_id'] and
                 any(row['media_key'] == key
                     for row in inventory_data['items']),
                 'MEDIA_KIND_INVENTORY_CHANGED')
            prefix_latest, prefix_scans = self._open_scan(prefix)
            scan = prefix_scans.get(data['scan_id'])
            need(scan is not None and scan['complete'] is not None and
                 scan['complete']['sequence'] < event['sequence'] and
                 prefix_latest == data['scan_id'],
                 'MEDIA_KIND_SCAN_CHANGED')
            prefix_media, prefix_snapshots = self._media_projection(prefix)
            current = [
                snapshot for snapshot in prefix_snapshots.get(
                    data['post_key'], [])
                if snapshot['data'].get('scan_id') == data['scan_id']]
            need(current and current[-1]['sequence'] ==
                 data['inventory_sequence'], 'MEDIA_KIND_INVENTORY_CHANGED')
            row = prefix_media.get(key)
            need(row is not None and row['post_key'] == data['post_key'] and
                 not row.get('missing') and
                 row.get('scan_id') == data['scan_id'],
                 'MEDIA_KIND_SCOPE_CHANGED')
            prior = latest.get(key)
            if prior is None:
                need(data['previous_correction'] is None and
                     data['from_kind'] == row['identity']['kind'],
                     'MEDIA_KIND_CHAIN_CHANGED')
            else:
                need(data['previous_correction'] == _event_ref(prior) and
                     data['from_kind'] == prior['data']['to_kind'],
                     'MEDIA_KIND_CHAIN_CHANGED')
            for earlier in self.events[:event['sequence'] - 1]:
                if (earlier['kind'] in terminal and
                        earlier['data'].get('media_key') == key):
                    raise NotesError('MEDIA_KIND_AFTER_ATTEMPT')
            by_media.setdefault(key, []).append(event)
            latest[key] = event
        return by_media, latest

    def _source_unavailable_projection(self):
        result = {}
        for event in self.events:
            if event['kind'] != 'source-unavailable':
                continue
            data = event['data']
            key = data['media_key']
            need(key not in result, 'DUPLICATE_SOURCE_UNAVAILABLE')
            prefix = self.events[:event['sequence'] - 1]
            attempts = self._attempt_projection(prefix)
            attempt_id = attempts['latest_by_media'].get(key)
            need(attempt_id == data['attempt_id'] and
                 attempts['attempts'][attempt_id]['post_key'] ==
                 data['post_key'], 'SOURCE_UNAVAILABLE_ATTEMPT_CHANGED')
            need(self._attempt_result(attempt_id, attempts) == 'STOPPED',
                 'SOURCE_UNAVAILABLE_REQUIRES_STOPPED')
            for earlier in prefix:
                if (earlier['kind'] in ('completion', 'publish-plan') and
                        earlier['data'].get('media_key') == key):
                    raise NotesError('SOURCE_UNAVAILABLE_WITH_TERMINAL_WORK')
            for later in self.events[event['sequence']:]:
                need(not (later['kind'] == 'intent' and
                          later['data'].get('media_key') == key),
                     'INTENT_AFTER_SOURCE_UNAVAILABLE')
            result[key] = event
        return result

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

        evidence_corrections, latest_evidence_correction = (
            self._evidence_correction_projection())
        if self._audit_rows is None:
            for event in self.events:
                if event['kind'] != 'page':
                    continue
                correction = latest_evidence_correction.get(event['sequence'])
                ref = (correction['data']['replacement_ref']
                       if correction is not None
                       else event['data']['evidence'])
                if correction is None:
                    self._event_evidence(
                        event, 'evidence', ref,
                        _evidence_context(list_key=self.list_data['list_key'],
                                          scan_id=event['data']['scan_id']),
                        require_scan_context=True)

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

        kind_corrections, _latest_kind_correction = (
            self._media_kind_correction_projection())
        media, _ = self._media_projection()
        for event in self.events:
            if event['kind'] == 'media':
                need(event['data']['post_key'] in seen_posts,
                     'MEDIA_POST_NOT_IN_OBSERVED_SCAN')
                need(self._post_detail(event['data']['post_key']) is not None,
                     'POST_DETAIL_REQUIRED_BEFORE_MEDIA')

        attempts = self._attempt_projection()
        self._source_unavailable_projection()
        for event in self.events:
            if event['kind'] != 'intent' or event['data']['schema'] not in (
                    'line-notes-intent/v2', 'line-notes-intent/v3'):
                continue
            data = event['data']
            corrections = [
                correction for correction in kind_corrections.get(
                    data['media_key'], [])
                if correction['sequence'] < event['sequence']]
            if corrections:
                latest = corrections[-1]
                need(data['kind_correction_ref'] == _event_ref(latest) and
                     data['effective_kind'] == latest['data']['to_kind'],
                     'INTENT_KIND_CORRECTION_CHANGED')
            else:
                need(data['kind_correction_ref'] is None and
                     data['effective_kind'] == data['identity']['kind'],
                     'INTENT_KIND_CORRECTION_CHANGED')
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
            if data['schema'] == 'line-notes-intent/v3':
                continue
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
            prefix_attempts = self._attempt_projection(
                self.events[:event['sequence'] - 1])
            need(data['attempt_id'] in prefix_attempts['attempts'] and
                 data['attempt_id'] not in verifications,
                 'DUPLICATE_OR_ORPHAN_VERIFICATION')
            attempt = prefix_attempts['attempts'][data['attempt_id']]
            need(data['media_key'] == attempt['media_key'] and
                 data['post_key'] == attempt['post_key'] and
                 data['kind'] == self._attempt_kind(attempt),
                 'VERIFICATION_ATTEMPT_CHANGED')
            need(self._attempt_result(data['attempt_id'], prefix_attempts) ==
                 'DOWNLOAD_FINISHED',
                 'VERIFICATION_REQUIRES_DOWNLOAD_FINISHED')
            need(prefix_attempts['latest_by_media'].get(data['media_key']) ==
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
            prefix_attempts = self._attempt_projection(
                self.events[:event['sequence'] - 1])
            verification = self._event_by_sequence(
                data['verification_sequence'])
            need(verification is not None and
                 verification['kind'] == 'verification' and
                 verification['data']['attempt_id'] == data['attempt_id'] and
                 digest(encoded(verification)) == data['verification_sha256'] and
                 data['source'] == verification['data']['source'],
                 'PUBLISH_VERIFICATION_CHANGED')
            attempt = prefix_attempts['attempts'].get(data['attempt_id'])
            need(attempt is not None and
                 data['media_key'] == attempt['media_key'] and
                 data['post_key'] == attempt['post_key'],
                 'PUBLISH_ATTEMPT_CHANGED')
            need(prefix_attempts['latest_by_media'].get(data['media_key']) ==
                 data['attempt_id'], 'PUBLISH_PLAN_NOT_LATEST_ATTEMPT')
            target_directory = Path(data['target_directory'])
            list_directory = Path(data['list_directory'])
            need(data['list_directory'] in list_directories and
                 (target_directory.parent == list_directory or
                  (target_directory.parent.parent.name == 'versions' and
                   target_directory.parent.parent.parent == list_directory)),
                 'PUBLISH_DIRECTORY_CHANGED')
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
        for completion_event in completions.values():
            event = completion_event
            data = event['data']
            prefix_attempts = self._attempt_projection(
                self.events[:event['sequence'] - 1])
            attempt = prefix_attempts['attempts'].get(data['attempt_id'])
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
            need(prefix_attempts['latest_by_media'].get(data['media_key']) ==
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
        self._restart_projection()
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
            expected = self.list_data.get('context_id')
            if expected is not None:
                need(context_id == expected, 'WRONG_NOTES_CONTEXT')
            need(not any(event['kind'] == 'binding' and
                         event['data']['session_id'] == session_id
                         for event in self.events),
                 'SESSION_ID_ALREADY_BOUND')
            context = _evidence_context(list_key=self.list_data['list_key'])
            data = dict(schema='line-notes-binding/v1',
                        session_id=session_id, context_id=context_id,
                        observation=_preserve_evidence(
                            self.records, observation, context),
                        handoff=_preserve_evidence(
                            self.records, handoff, context))
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
                        evidence=_preserve_evidence(
                            self.records, evidence,
                            _evidence_context(
                                list_key=self.list_data['list_key'])))
            self.append('destination', data)
            return data

    def _open_scan(self, events=None):
        starts = {}
        latest = None
        open_scan_id = None
        for event in (self.events if events is None else events):
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
                                                interrupted=None, pages=[])
                latest = data['scan_id']
                open_scan_id = data['scan_id']
            else:
                need(open_scan_id == data['scan_id'] and
                     data['scan_id'] in starts and
                     starts[data['scan_id']]['complete'] is None and
                     starts[data['scan_id']]['interrupted'] is None,
                     'SCAN_COMPLETION_WITHOUT_OPEN_SCAN')
                if data['action'] == 'COMPLETE':
                    need(data['session_id'] ==
                         starts[data['scan_id']]['start']['data']['session_id'],
                         'SCAN_SESSION_CHANGED')
                    starts[data['scan_id']]['complete'] = event
                else:
                    starts[data['scan_id']]['interrupted'] = event
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

    def start_scan(self, *, session_id, evidence, recovery=False):
        with self.locked():
            self._require_session(session_id)
            latest, scans = self._open_scan()
            if not recovery:
                need(not self._pending_publish_plans(),
                     'PENDING_NAMING_TRANSACTION')
                self._assert_no_unknown_attempts()
            if latest is not None:
                need(scans[latest]['complete'] is not None or
                     scans[latest]['interrupted'] is not None,
                     'SCAN_ALREADY_OPEN')
                if scans[latest]['complete'] is not None and not recovery:
                    coverage_errors = self._coverage_errors()
                    need(not coverage_errors, 'SCAN_COVERAGE_INCOMPLETE')
            scan_id = uuid.uuid4().hex
            context = _evidence_context(
                list_key=self.list_data['list_key'])
            data = dict(schema='line-notes-scan/v1', action='START',
                        scan_id=scan_id, session_id=session_id,
                        evidence=_preserve_evidence(
                            self.records, evidence, context))
            if recovery:
                data['purpose'] = 'RECOVERY_EVALUATION'
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
            need(scan['complete'] is None and scan['interrupted'] is None,
                 'SCAN_ALREADY_COMPLETE')
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
                        evidence=_preserve_evidence(
                            self.records, evidence,
                            _evidence_context(
                                list_key=self.list_data['list_key'],
                                scan_id=scan_id)))
            self.append('page', data)
            return data

    def finish_scan(self, *, session_id, scan_id, evidence):
        with self.locked():
            latest, scans = self._open_scan()
            need(latest is not None and latest == scan_id,
                 'CURRENT_SCAN_REQUIRED')
            scan = scans[scan_id]
            need(scan['complete'] is None, 'SCAN_ALREADY_COMPLETE')
            need(scan['interrupted'] is None, 'SCAN_ALREADY_INTERRUPTED')
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
                        evidence=_preserve_evidence(
                            self.records, evidence,
                            _evidence_context(
                                list_key=self.list_data['list_key'],
                                scan_id=scan_id)),
                        posts=ordered)
            self.append('scan', data)
            return data

    def interrupt_scan(self, *, session_id, scan_id, reason, evidence):
        need(isinstance(reason, str) and bool(reason.strip()),
             'SCAN_INTERRUPTION_REASON_REQUIRED')
        with self.locked():
            latest, scans = self._open_scan()
            need(latest is not None and latest == scan_id,
                 'CURRENT_SCAN_REQUIRED')
            scan = scans[scan_id]
            need(scan['complete'] is None, 'SCAN_ALREADY_COMPLETE')
            if scan['interrupted'] is not None:
                existing = scan['interrupted']['data']
                need(existing['session_id'] == session_id and
                     existing['reason'] == reason,
                     'SCAN_INTERRUPTION_CHANGED')
                return existing
            self._require_session(session_id)
            context = _evidence_context(list_key=self.list_data['list_key'],
                                        scan_id=scan_id)
            data = dict(schema='line-notes-scan/v1', action='INTERRUPTED',
                        scan_id=scan_id, session_id=session_id,
                        reason=reason,
                        evidence=_preserve_evidence(
                            self.records, evidence, context))
            self.append('scan', data)
            return data

    def scan(self, *, session_id, action, scan_id=None, evidence,
             recovery=False, reason=None):
        need(action in ('START', 'FINISH', 'INTERRUPT'),
             'INVALID_SCAN_ACTION')
        if action == 'START':
            need(scan_id is None, 'SCAN_ID_NOT_ACCEPTED_FOR_START')
            need(reason is None, 'SCAN_REASON_NOT_ACCEPTED_FOR_START')
            return self.start_scan(session_id=session_id, evidence=evidence,
                                   recovery=recovery)
        need(scan_id is not None, 'SCAN_ID_REQUIRED')
        need(not recovery, 'SCAN_RECOVERY_ONLY_FOR_START')
        if action == 'INTERRUPT':
            return self.interrupt_scan(
                session_id=session_id, scan_id=scan_id, reason=reason,
                evidence=evidence)
        need(reason is None, 'SCAN_REASON_ONLY_FOR_INTERRUPT')
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

    def _attempt_scan_binding_matches(self, intent_data):
        bound = intent_data.get('scan_id')
        if bound is None:
            return False
        latest, scans = self._open_scan()
        if (latest is None or scans[latest]['complete'] is None or
                bound != latest):
            return False
        complete_posts = {
            row['post_key']
            for row in scans[bound]['complete']['data']['posts']
        }
        if intent_data['post_key'] not in complete_posts:
            return False
        detail = self._post_detail_for_scan(intent_data['post_key'], bound)
        if detail is None or detail.get('scan_id') != bound:
            return False
        media, _ = self._media_projection()
        target = media.get(intent_data['media_key'])
        return (target is not None and
                target.get('post_key') == intent_data['post_key'] and
                target.get('scan_id') == bound)

    def _require_attempt_scan_binding(
            self, intent_data, code='ATTEMPT_SCAN_BINDING_CHANGED',
            missing_code='INTENT_SCAN_BINDING_REQUIRED'):
        need(intent_data.get('scan_id') is not None,
             missing_code)
        need(self._attempt_scan_binding_matches(intent_data), code)
        return intent_data['scan_id']

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
            context = _evidence_context(
                list_key=self.list_data['list_key'],
                post_key=post_key_value, scan_id=current_scan_id)
            data = dict(schema='line-notes-post/v1',
                        post_key=post_key_value,
                        date_summary=date_summary,
                        text_sha256=text_sha256,
                        media_count=media_count,
                        no_media=bool(no_media),
                        scan_id=current_scan_id,
                        evidence=_preserve_evidence(
                            self.records, evidence, context))
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

    def _media_projection(self, events=None):
        media = {}
        snapshots = {}
        for event in (self.events if events is None else events):
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
            context = _evidence_context(
                list_key=self.list_data['list_key'],
                post_key=post_key_value, scan_id=current_scan_id)
            data = dict(schema='line-notes-media-inventory/v1',
                        post_key=post_key_value,
                        items=normalized,
                        missing=missing_rows,
                        scan_id=current_scan_id,
                        evidence=_preserve_evidence(
                            self.records, evidence, context))
            self.append('media', data)
            return data

    def _attempt_projection(self, events=None):
        attempts = {}
        order = {}
        outcomes = {}
        reconciles = {}
        for event in (self.events if events is None else events):
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

    @staticmethod
    def _attempt_kind(intent_data):
        return (intent_data.get('effective_kind')
                if intent_data['schema'] in ('line-notes-intent/v2',
                                             'line-notes-intent/v3')
                else intent_data['identity']['kind'])

    def _restart_projection(self, events=None):
        """Validate restart events and project the latest activated versions."""
        source_events = list(self.events if events is None else events)
        by_sequence = {event['sequence']: event for event in source_events}
        need(len(by_sequence) == len(source_events),
             'DUPLICATE_EVENT_SEQUENCE')

        def event_for_ref(ref, code, kind=None):
            _check_event_ref(ref, code)
            event = by_sequence.get(ref['sequence'])
            need(event is not None and _event_ref(event) == ref and
                 (kind is None or event['kind'] == kind), code)
            return event

        def prefix(sequence):
            return [event for event in source_events
                    if event['sequence'] < sequence]

        confirmations = {}
        plans = {}
        candidates_by_plan = {}
        candidates = {}
        activations = {}
        active_by_media = {}
        activated_restarts = set()
        seen_targets = set()

        for event in source_events:
            kind = event['kind']
            data = event['data']
            sequence = event['sequence']

            if kind == 'completion':
                seen_targets.add((data['destination'],
                                  data['target_file']['name']))
                continue
            if kind == 'publish-plan':
                seen_targets.add((data['target_directory'],
                                  data['target_name']))
                continue

            if kind == 'restart-confirm':
                restart_id = data['restart_id']
                need(restart_id not in confirmations,
                     'DUPLICATE_RESTART_CONFIRMATION')
                need(not any(existing_id not in activated_restarts
                             for existing_id in confirmations),
                     'MULTIPLE_OPEN_RESTART_BATCHES')
                need(data['generation'] == len(confirmations) + 1,
                     'RESTART_GENERATION_CHANGED')
                self._validate_restart_scope_shape(
                    data['scope'], data['generation'])
                need(data['scope_digest'] == self._restart_scope_digest(
                    restart_id, data['generation'], data['expected_tip'],
                    data['scope']), 'RESTART_SCOPE_DIGEST_CHANGED')
                expected = event_for_ref(
                    data['expected_tip'], 'RESTART_EXPECTED_TIP_CHANGED')
                need(expected['sequence'] == sequence - 1,
                     'RESTART_EXPECTED_TIP_CHANGED')
                scan = event_for_ref(
                    data['scope']['scan'], 'RESTART_SCOPE_SCAN_CHANGED',
                    kind='scan')
                need(scan['data']['action'] == 'COMPLETE' and
                     scan['data']['scan_id'] == data['scope']['scan_id'] and
                     scan['sequence'] < expected['sequence'],
                     'RESTART_SCOPE_SCAN_CHANGED')
                scan_posts = {
                    row['post_key']: row
                    for row in scan['data']['posts']}
                prefix_media = self._media_projection(prefix(sequence))
                media_by_post = {}
                for key, row in prefix_media[0].items():
                    if row.get('scan_id') == data['scope']['scan_id']:
                        media_by_post.setdefault(
                            row['post_key'], set()).add(key)
                for post in data['scope']['posts']:
                    need(post['post_key'] in scan_posts,
                         'RESTART_SCOPE_POST_CHANGED')
                    scope_keys = {row['media_key']
                                  for row in post['media']}
                    missing_keys = {row['media_key']
                                    for row in post['missing']}
                    need(scope_keys | missing_keys ==
                         media_by_post.get(post['post_key'], set()),
                         'RESTART_SCOPE_POST_INCOMPLETE')
                confirmations[restart_id] = event
                continue

            if kind == 'intent' and data['schema'] == 'line-notes-intent/v3':
                confirmation = confirmations.get(data['restart_id'])
                need(confirmation is not None and
                     confirmation['sequence'] < sequence and
                     confirmation['data']['generation'] == data['generation'],
                     'RESTART_INTENT_WITHOUT_CONFIRMATION')
                need(data['restart_id'] not in activated_restarts,
                     'RESTART_ALREADY_ACTIVATED')
                confirmation_data = confirmation['data']
                need(data['confirmation_ref'] == _event_ref(confirmation),
                     'RESTART_CONFIRMATION_CHANGED')
                scope_media = {
                    row['media_key']: (post, row)
                    for post in confirmation_data['scope']['posts']
                    for row in post['media']
                }
                scoped = scope_media.get(data['media_key'])
                need(scoped is not None and
                     scoped[0]['post_key'] == data['post_key'] and
                     scoped[1]['identity'] == data['identity'] and
                     scoped[1]['effective_kind'] == data['effective_kind'],
                     'RESTART_INTENT_OUTSIDE_SCOPE')
                prior_attempts = self._attempt_projection(prefix(sequence))
                expected_prior = prior_attempts['latest_by_media'].get(
                    data['media_key'])
                expected_ref = (
                    _event_ref(by_sequence[prior_attempts['order'][
                        expected_prior]])
                    if expected_prior is not None else None)
                need(data['prior_attempt'] == expected_ref,
                     'RESTART_PRIOR_ATTEMPT_CHANGED')
                continue

            if kind == 'restart-copy-plan':
                confirmation = confirmations.get(data['restart_id'])
                need(confirmation is not None and
                     confirmation['sequence'] < sequence and
                     confirmation['data']['generation'] == data['generation'] and
                     data['confirmation_ref'] == _event_ref(confirmation),
                     'RESTART_COPY_WITHOUT_CONFIRMATION')
                need(data['restart_id'] not in activated_restarts,
                     'RESTART_ALREADY_ACTIVATED')
                need(data['plan_id'] not in plans,
                     'DUPLICATE_RESTART_COPY_PLAN')
                scope_media = {
                    row['media_key']: (post, row)
                    for post in confirmation['data']['scope']['posts']
                    for row in post['media']
                }
                scoped = scope_media.get(data['media_key'])
                need(scoped is not None and
                     scoped[0]['post_key'] == data['post_key'] and
                     scoped[0]['version_directory'] ==
                     data['target_directory'] and
                     data['list_directory'] == str(
                         Path(scoped[0]['version_directory']).parents[2]),
                     'RESTART_COPY_OUTSIDE_SCOPE')
                prefix_attempts = self._attempt_projection(prefix(sequence))
                intent_data = prefix_attempts['attempts'].get(
                    data['attempt_id'])
                need(intent_data is not None and
                     intent_data['schema'] == 'line-notes-intent/v3' and
                     intent_data['restart_id'] == data['restart_id'] and
                     intent_data['generation'] == data['generation'] and
                     intent_data['media_key'] == data['media_key'] and
                     intent_data['post_key'] == data['post_key'] and
                     intent_data['confirmation_ref'] ==
                     data['confirmation_ref'] and
                     prefix_attempts['latest_by_media'].get(
                         data['media_key']) == data['attempt_id'] and
                     self._attempt_result(
                         data['attempt_id'], prefix_attempts) ==
                     'DOWNLOAD_FINISHED',
                     'RESTART_COPY_ATTEMPT_CHANGED')
                need(Path(data['source']['path']).parent ==
                     Path(intent_data['destination']),
                     'RESTART_COPY_SOURCE_CHANGED')
                kind_value = self._attempt_kind(intent_data)
                match = re.fullmatch(r'media_([0-9]+)(\.[^./]+)',
                                     data['target_name'])
                need(match is not None and
                     int(match.group(1)) == data['number'] and
                     match.group(2) == data['extension'] and
                     data['extension'].lower() in
                     (PHOTO_SUFFIXES if kind_value == PHOTO
                      else VIDEO_SUFFIXES),
                     'RESTART_COPY_TARGET_CHANGED')
                key = (data['target_directory'], data['target_name'])
                need(key not in seen_targets, 'DUPLICATE_TARGET_NAME')
                seen_targets.add(key)
                plans[data['plan_id']] = event
                continue

            if kind == 'restart-candidate':
                confirmation = confirmations.get(data['restart_id'])
                need(confirmation is not None and
                     confirmation['sequence'] < sequence and
                     confirmation['data']['generation'] == data['generation'],
                     'RESTART_CANDIDATE_WITHOUT_CONFIRMATION')
                need(data['restart_id'] not in activated_restarts,
                     'RESTART_ALREADY_ACTIVATED')
                plan = event_for_ref(
                    data['plan_ref'],
                    'RESTART_CANDIDATE_PLAN_CHANGED',
                    kind='restart-copy-plan')
                plan_data = plan['data']
                need(plan['sequence'] < sequence and
                     plan_data['plan_id'] in plans and
                     plan_data['plan_id'] not in candidates_by_plan,
                     'DUPLICATE_RESTART_CANDIDATE')
                need(data['restart_id'] == plan_data['restart_id'] and
                     data['generation'] == plan_data['generation'] and
                     data['attempt_id'] == plan_data['attempt_id'] and
                     data['media_key'] == plan_data['media_key'] and
                     data['post_key'] == plan_data['post_key'] and
                     data['source'] == plan_data['source'] and
                     data['candidate']['path'] == str(
                         Path(plan_data['target_directory']) /
                         plan_data['target_name']) and
                     data['candidate']['name'] == plan_data['target_name'],
                     'RESTART_CANDIDATE_TARGET_CHANGED')
                need((data['candidate']['device'], data['candidate']['inode']) !=
                     (data['source']['device'], data['source']['inode']),
                     'RESTART_CANDIDATE_NOT_ISOLATED')
                prefix_attempts = self._attempt_projection(prefix(sequence))
                intent_data = prefix_attempts['attempts'].get(
                    data['attempt_id'])
                need(intent_data is not None and
                     data['kind'] == self._attempt_kind(intent_data),
                     'RESTART_CANDIDATE_KIND_CHANGED')
                extension = plan_data['extension'].lower()
                extension_kind = (
                    PHOTO if extension in PHOTO_SUFFIXES else
                    VIDEO if extension in VIDEO_SUFFIXES else None)
                need(extension_kind == data['kind'],
                     'RESTART_CANDIDATE_KIND_CHANGED')
                need(data['manifest'] == [data['candidate']] and
                     data['manifest_sha256'] ==
                     digest(encoded(data['manifest'])),
                     'RESTART_CANDIDATE_MANIFEST_CHANGED')
                candidates_by_plan[plan_data['plan_id']] = event
                candidates[data['media_key']] = event
                continue

            if kind == 'restart-activation':
                restart_id = data['restart_id']
                confirmation = confirmations.get(restart_id)
                need(confirmation is not None and
                     confirmation['sequence'] < sequence and
                     confirmation['data']['generation'] == data['generation'] and
                     data['confirmation_ref'] == _event_ref(confirmation) and
                     data['scope_digest'] ==
                     confirmation['data']['scope_digest'],
                     'RESTART_ACTIVATION_CONFIRMATION_CHANGED')
                need(restart_id not in activations,
                     'DUPLICATE_RESTART_ACTIVATION')
                expected_rows = sorted(
                    (row['media_key'], post['post_key'])
                    for post in confirmation['data']['scope']['posts']
                    for row in post['media'])
                actual_rows = [(row['media_key'], row['post_key'])
                               for row in data['candidates']]
                need(actual_rows == expected_rows,
                     'RESTART_ACTIVATION_SCOPE_CHANGED')
                active_post_directories = {}
                for existing_key, existing in active_by_media.items():
                    existing_post = existing['candidate']['data']['post_key']
                    existing_directory = str(Path(
                        existing['candidate']['data']['candidate']['path']).parent)
                    active_post_directories.setdefault(
                        existing_post, set()).add(existing_directory)
                for row in data['candidates']:
                    candidate = event_for_ref(
                        row['candidate_ref'],
                        'RESTART_ACTIVATION_CANDIDATE_CHANGED',
                        kind='restart-candidate')
                    need(candidate['sequence'] < sequence and
                         candidate is candidates.get(row['media_key']) and
                         candidate['data']['restart_id'] == restart_id and
                         candidate['data']['generation'] ==
                         data['generation'] and
                         candidate['data']['post_key'] == row['post_key'] and
                         candidate['data']['candidate'] == row['candidate'],
                         'RESTART_ACTIVATION_CANDIDATE_CHANGED')
                    need(row['media_key'] not in active_by_media,
                         'RESTART_MEDIA_ALREADY_ACTIVE')
                    active_by_media[row['media_key']] = dict(
                        activation=event, candidate=candidate,
                        confirmation=confirmation, row=row)
                    active_post_directories.setdefault(
                        row['post_key'], set()).add(str(Path(
                            row['candidate']['path']).parent))
                need(all(len(directories) <= 1
                         for directories in active_post_directories.values()),
                     'MULTIPLE_ACTIVE_VERSION_DIRECTORIES')
                activations[restart_id] = event
                activated_restarts.add(restart_id)
                continue

        return dict(confirmations=confirmations, plans=plans,
                    candidates_by_plan=candidates_by_plan,
                    candidates=candidates, activations=activations,
                    active_by_media=active_by_media)

    def _active_media_versions(self, events=None):
        return self._restart_projection(events)['active_by_media']

    def _active_candidate_availability(self, media_key_value):
        active = self._active_media_versions().get(media_key_value)
        if active is None:
            return None
        return self._candidate_file_availability(
            active['candidate']['data']['candidate'])

    @staticmethod
    def _candidate_file_availability(candidate):
        path = Path(candidate['path'])
        entry = _entry(path)
        if entry is None:
            return LOCAL_MISSING
        try:
            need(stat.S_ISREG(entry.st_mode) and entry.st_nlink == 1 and
                 not path.is_symlink(), 'ACTIVE_CANDIDATE_CHANGED')
            info = os.stat(str(path), follow_symlinks=False)
            need((info.st_dev, info.st_ino, info.st_size,
                  info.st_mtime_ns, info.st_ctime_ns) ==
                 (candidate['device'], candidate['inode'], candidate['size'],
                  candidate['mtime_ns'], candidate['ctime_ns']),
                 'ACTIVE_CANDIDATE_CHANGED')
            need(digest(read_file(path)) == candidate['sha256'],
                 'ACTIVE_CANDIDATE_CHANGED')
            return LOCAL_VERIFIED
        except (NotesError, DailyError, OSError, ValueError):
            return LOCAL_CHANGED

    def _restart_target_rows(self, confirmation):
        posts = []
        estimated = 0
        for post in confirmation['data']['scope']['posts']:
            media_rows = []
            for number, row in enumerate(
                    sorted(post['media'], key=lambda item: item['source_order']),
                    start=1):
                media_rows.append(dict(
                    media_key=row['media_key'],
                    effective_kind=row['effective_kind'],
                    source_order=row['source_order'],
                    target_stem='media_%03d' % number))
                prior = row.get('prior_completion')
                if prior is not None:
                    event = self._event_by_sequence(prior['sequence'])
                    if event is not None and event['kind'] == 'completion':
                        estimated += event['data']['target_file']['size']
            posts.append(dict(post_key=post['post_key'],
                              version_directory=post['version_directory'],
                              media=media_rows,
                              missing=list(post['missing'])))
        return posts, estimated

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

    def _completion_projection(self, events=None):
        completions = {}
        by_attempt = {}
        for event in (self.events if events is None else events):
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

    def _pending_publish_plans(self, events=None):
        source_events = self.events if events is None else events
        completions, _ = self._completion_projection(source_events)
        completed_transactions = {event['data']['transaction_id']
                                  for event in completions.values()}
        suppressed = set()
        for event in source_events:
            if event['kind'] != 'restart-confirm':
                continue
            for post in event['data']['scope']['posts']:
                for row in post['media']:
                    prior = row.get('prior_pending_plan')
                    if prior is not None:
                        suppressed.add(prior['sequence'])
        plans = {}
        for event in source_events:
            if event['kind'] != 'publish-plan':
                continue
            data = event['data']
            need(data['transaction_id'] not in plans,
                 'DUPLICATE_PUBLISH_TRANSACTION')
            plans[data['transaction_id']] = event
        return [event for transaction, event in plans.items()
                if transaction not in completed_transactions and
                event['sequence'] not in suppressed]

    def _assert_no_unknown_attempts(self):
        projection = self._attempt_projection()
        resolved = set(self._completion_projection()[0])
        resolved |= set(self._active_media_versions())
        for media_key_value, attempt_id in projection['latest_by_media'].items():
            if media_key_value in resolved:
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
        active_names = {}
        for version in self._active_media_versions().values():
            candidate = version['candidate']['data']['candidate']
            active_names.setdefault(
                str(Path(candidate['path']).parent), set()).add(
                    candidate['name'])
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
                expected_names |= active_names.get(directory_string, set())
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

    def _effective_local_availability(self):
        availability = self._completion_availability()
        for key in self._active_media_versions():
            availability[key] = self._active_candidate_availability(key)
        return availability

    def _assert_no_local_changed(self, allowing=()):
        availability = self._effective_local_availability()
        changed = {key for key, value in availability.items()
                   if value == LOCAL_CHANGED}
        need(changed <= set(allowing),
             'COMPLETED_FILES_CHANGED_NO_REDOWNLOAD')

    def _status_map(self):
        media, _ = self._media_projection()
        attempts = self._attempt_projection()
        completions, _ = self._completion_projection()
        active = self._active_media_versions()
        exclusions = self._exclusion_projection()
        protections = self._protection_projection()
        result = {}
        for key, row in media.items():
            if key in active:
                result[key] = 'COMPLETED'
                continue
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

    def _coverage_errors(self):
        latest, scans = self._open_scan()
        if latest is None or scans[latest]['complete'] is None:
            return ['COMPLETE_NOTES_SCAN_REQUIRED']
        posts = scans[latest]['complete']['data']['posts']
        if not posts:
            return ['POST_COVERAGE_INCOMPLETE']
        _media, snapshots = self._media_projection()
        errors = set()
        for row in posts:
            detail = self._post_detail_for_scan(row['post_key'], latest)
            if detail is None:
                errors.add('POST_DETAIL_PENDING')
                continue
            current = [event for event in snapshots.get(row['post_key'], [])
                       if event['data'].get('scan_id') == latest]
            if detail['no_media']:
                if detail['media_count'] != 0:
                    errors.add('POST_COVERAGE_INCOMPLETE')
                continue
            if not current:
                errors.add('POST_COVERAGE_INCOMPLETE')
                continue
            snapshot = current[-1]['data']
            if (len(snapshot['items']) + len(snapshot['missing']) !=
                    detail['media_count']):
                errors.add('POST_COVERAGE_INCOMPLETE')
        return sorted(errors)

    def _assert_dispatch_coverage(self):
        errors = self._coverage_errors()
        if errors:
            raise NotesError(errors[0])

    def _current_restart_scope(self):
        latest, scans = self._open_scan()
        need(latest is not None and scans[latest]['complete'] is not None,
             'COMPLETE_NOTES_SCAN_REQUIRED')
        complete = scans[latest]['complete']
        complete_posts = complete['data']['posts']
        list_directory_at_scan = self._list_directory_at(complete['sequence'])
        media, _ = self._media_projection()
        attempts = self._attempt_projection()
        completions, _ = self._completion_projection()
        exclusions = self._exclusion_projection()
        protections = self._protection_projection()
        unavailable = self._source_unavailable_projection()
        availability = self._effective_local_availability()
        media_rows = {row['media_key']: row for row in self._media_rows()}
        statuses = self._status_map()
        current_keys = {
            key for key, row in media.items()
            if row.get('scan_id') == latest and
            row.get('post_key') in {post['post_key'] for post in complete_posts}
        }
        pending_by_key = {}
        for plan in self._pending_publish_plans():
            pending_by_key.setdefault(plan['data']['media_key'], plan)
        generation = 1 + max(
            (event['data']['generation'] for event in self.events
             if event['kind'] == 'restart-confirm'), default=0)
        by_post = {}
        for key in current_keys:
            by_post.setdefault(media[key]['post_key'], []).append(key)
        posts = []
        target_rows = []
        for post in complete_posts:
            keys = sorted(by_post.get(post['post_key'], []),
                          key=lambda key: media[key]['source_order'])
            reasons = set()
            for key in keys:
                row = media_rows[key]
                status = statuses[key]
                if row['local_files'] == LOCAL_CHANGED:
                    reasons.add('LOCAL_CHANGED')
                if status == 'UNKNOWN':
                    reasons.add('UNKNOWN_ATTEMPT')
                elif status == 'PREVIOUSLY_INCOMPLETE':
                    reasons.add('UNFINISHED_ATTEMPT')
                if key in pending_by_key:
                    reasons.add('PENDING_NAMING')
            if not reasons:
                continue
            media_scope = []
            missing_scope = []
            for key in keys:
                row = media_rows[key]
                reason = None
                if row['missing']:
                    reason = 'SOURCE_MISSING'
                elif row['source_availability'] == 'EXPIRED':
                    reason = 'SOURCE_EXPIRED'
                elif row['status'] == 'EXCLUDED':
                    reason = 'EXCLUDED'
                elif row['status'] == 'PROTECTED_HISTORY':
                    reason = 'PROTECTED_HISTORY'
                if reason is not None:
                    missing_scope.append(dict(
                        media_key=key, source_order=row['source_order'],
                        reason=reason))
                    continue
                prior_attempt = None
                attempt_id = attempts['latest_by_media'].get(key)
                if attempt_id is not None:
                    prior_attempt = _event_ref(self._event_by_sequence(
                        attempts['order'][attempt_id]))
                prior_completion = None
                if key in completions:
                    prior_completion = _event_ref(completions[key])
                pending = pending_by_key.get(key)
                media_scope.append(dict(
                    media_key=key, identity=row['identity'],
                    effective_kind=row['effective_kind'],
                    source_order=row['source_order'],
                    prior_attempt=prior_attempt,
                    prior_completion=prior_completion,
                    prior_pending_plan=(_event_ref(pending)
                                        if pending is not None else None),
                    local_files=row['local_files']))
            posts.append(dict(post_key=post['post_key'],
                              identity=post['identity'],
                              version_directory=str(
                                  self._restart_version_directory(
                                      generation, post['post_key'],
                                      post['date_summary'],
                                      list_directory_at_scan)),
                              reasons=sorted(reasons),
                              media=sorted(media_scope,
                                           key=lambda row: row['source_order']),
                              missing=sorted(missing_scope,
                                             key=lambda row: row['source_order'])))
        expected_tip = _event_ref(self.events[-1])
        scope = dict(schema=RESTART_SCOPE_SCHEMA,
                     list_key=self.list_data['list_key'],
                     scan=_event_ref(complete), scan_id=latest,
                     path_policy=RESTART_PATH_POLICY, posts=posts)
        restart_id = digest(encoded(dict(
            list_key=self.list_data['list_key'], expected_tip=expected_tip,
            generation=generation, scope=scope)))
        scope_digest = self._restart_scope_digest(
            restart_id, generation, expected_tip, scope)
        estimated = 0
        for post in posts:
            for row in post['media']:
                prior = row['prior_completion']
                if prior is not None:
                    event = self._event_by_sequence(prior['sequence'])
                    if event is not None and event['kind'] == 'completion':
                        estimated += event['data']['target_file']['size']
        for post in posts:
            target_rows.append(dict(
                post_key=post['post_key'],
                version_directory=post['version_directory']))
        return dict(restart_id=restart_id, generation=generation,
                    expected_tip=expected_tip, scope=scope,
                    scope_digest=scope_digest,
                    estimated_extra_bytes=estimated,
                    targets=target_rows)

    def _restart_version_directory(self, generation, post_key_value,
                                   date_summary, list_directory):
        need(type(generation) is int and generation >= 1,
             'INVALID_RESTART_GENERATION')
        _hex(post_key_value, 'INVALID_POST_KEY')
        need(isinstance(date_summary, str), 'INVALID_RESTART_SCOPE')
        list_directory = Path(list_directory).expanduser().absolute()
        need(list_directory.is_absolute() and
             str(list_directory) == os.path.normpath(str(list_directory)),
             'INVALID_RESTART_SCOPE')
        base = safe_component(date_summary or 'post')
        while len(base.encode('utf-8')) > 120:
            base = base[:-1]
        generation_name = 'g%08d' % generation
        version_directory = (list_directory / 'versions' /
                             generation_name /
                             (base + '_' + post_key_value[:8]))
        need(version_directory.is_relative_to(list_directory),
             'INVALID_RESTART_SCOPE')
        return version_directory

    def _restart_open_confirmation(self):
        restart = self._restart_projection()
        open_rows = [event for event in restart['confirmations'].values()
                     if event['data']['restart_id'] not in
                     restart['activations']]
        open_rows.sort(key=lambda event: event['sequence'])
        need(len(open_rows) <= 1, 'MULTIPLE_OPEN_RESTART_BATCHES')
        return open_rows[0] if open_rows else None

    def _restart_progress(self, confirmation_event):
        confirmation = confirmation_event['data']
        restart_id = confirmation['restart_id']
        restart = self._restart_projection()
        activated = restart_id in restart['activations']
        plans_by_media = {}
        for plan in restart['plans'].values():
            if plan['data']['restart_id'] == restart_id:
                plans_by_media.setdefault(plan['data']['media_key'], []).append(plan)
        candidates = {
            event['data']['media_key']: event
            for event in restart['candidates'].values()
            if event['data']['restart_id'] == restart_id
        }
        attempts = self._attempt_projection()
        rows = []
        for post in confirmation['scope']['posts']:
            for row in post['media']:
                key = row['media_key']
                attempt_ids = [
                    attempt_id for attempt_id in
                    attempts['attempts_by_media'].get(key, [])
                    if attempts['attempts'][attempt_id]['schema'] ==
                    'line-notes-intent/v3' and
                    attempts['attempts'][attempt_id]['restart_id'] == restart_id]
                latest_attempt = None
                if attempt_ids:
                    latest_attempt = max(attempt_ids,
                                         key=lambda value: attempts['order'][value])
                result = (self._attempt_result(latest_attempt, attempts)
                          if latest_attempt is not None else None)
                if key in candidates:
                    availability = self._candidate_file_availability(
                        candidates[key]['data']['candidate'])
                    action = ('ACTIVE' if activated else
                              'CANDIDATE_VERIFIED'
                              if availability == LOCAL_VERIFIED else
                              'CANDIDATE_RECHECK_REQUIRED')
                elif (activated and key in restart['active_by_media'] and
                      restart['active_by_media'][key]['activation']['data'][
                          'restart_id'] == restart_id):
                    action = 'ACTIVE'
                elif latest_attempt is None:
                    action = 'INTENT_REQUIRED'
                elif result in (None, 'UNKNOWN'):
                    action = 'RECONCILE_OR_NEW_INTENT'
                elif result == 'DOWNLOAD_FINISHED':
                    action = 'COPY_AND_VERIFY_REQUIRED'
                else:
                    action = 'NEW_INTENT_REQUIRED'
                rows.append(dict(media_key=key, post_key=post['post_key'],
                                 attempt_id=latest_attempt, result=result,
                                 plan_count=len(plans_by_media.get(key, [])),
                                 candidate_ref=(_event_ref(candidates[key])
                                                if key in candidates else None),
                                 action=action))
        return dict(restart_id=restart_id,
                    generation=confirmation['generation'],
                    confirmation_ref=_event_ref(confirmation_event),
                    scope_digest=confirmation['scope_digest'],
                    activated=activated,
                    activation_ref=(_event_ref(restart['activations'][restart_id])
                                    if activated else None),
                    media=rows)

    def restart_preview(self):
        with self.locked():
            open_confirmation = self._restart_open_confirmation()
            if open_confirmation is not None:
                data = open_confirmation['data']
                targets, estimated = self._restart_target_rows(data)
                return dict(
                    schema='line-notes-restart-preview/v1',
                    status='OPEN_BATCH', restart_required=True,
                    restart_id=data['restart_id'], generation=data['generation'],
                    expected_tip=data['expected_tip'], scope=data['scope'],
                    scope_digest=data['scope_digest'], targets=targets,
                    estimated_extra_bytes=estimated,
                    open_batch=self._restart_progress(open_confirmation),
                    dispatch_authorized=False,
                    external_copy_verified=False,
                    real_line_e2e='NOT_TESTED')
            preview = self._current_restart_scope()
            return dict(schema='line-notes-restart-preview/v1',
                        status=('RESTART_REQUIRED' if preview['scope']['posts']
                                else 'NO_RESTART_REQUIRED'),
                        restart_required=bool(preview['scope']['posts']),
                        **preview, open_batch=None,
                        dispatch_authorized=False,
                        external_copy_verified=False,
                        real_line_e2e='NOT_TESTED')

    def restart_confirm(self, *, session_id, preview, evidence):
        need(isinstance(preview, dict), 'INVALID_RESTART_PREVIEW')
        required = {'restart_id', 'generation', 'expected_tip', 'scope',
                    'scope_digest'}
        need(required <= set(preview), 'INVALID_RESTART_PREVIEW')
        with self.locked():
            self._require_session(session_id)
            restart_id = preview['restart_id']
            existing = self._restart_projection()['confirmations'].get(restart_id)
            if existing is not None:
                data = existing['data']
                need(data['generation'] == preview['generation'] and
                     data['expected_tip'] == preview['expected_tip'] and
                     data['scope'] == preview['scope'] and
                     data['scope_digest'] == preview['scope_digest'],
                     'RESTART_CONFIRMATION_CHANGED')
                return dict(data, status='CONFIRMED', replayed=True,
                            progress=self._restart_progress(existing),
                            dispatch_authorized=False,
                            external_copy_verified=False,
                            real_line_e2e='NOT_TESTED')
            open_confirmation = self._restart_open_confirmation()
            need(open_confirmation is None,
                 'RESTART_BATCH_ALREADY_OPEN')
            need(preview['expected_tip'] == _event_ref(self.events[-1]),
                 'RESTART_EXPECTED_TIP_CHANGED')
            current = self._current_restart_scope()
            need(current['scope']['posts'], 'RESTART_NOT_REQUIRED')
            need(preview['restart_id'] == current['restart_id'] and
                 preview['generation'] == current['generation'] and
                 preview['expected_tip'] == current['expected_tip'] and
                 preview['scope'] == current['scope'] and
                 preview['scope_digest'] == current['scope_digest'],
                 'RESTART_PREVIEW_CHANGED')
            self._validate_restart_scope_shape(
                current['scope'], current['generation'])
            context = _evidence_context(list_key=self.list_data['list_key'],
                                        scan_id=current['scope']['scan_id'])
            data = dict(schema=RESTART_CONFIRM_SCHEMA,
                        restart_id=current['restart_id'],
                        generation=current['generation'],
                        scope_digest=current['scope_digest'],
                        expected_tip=current['expected_tip'],
                        scope=current['scope'],
                        evidence=_preserve_evidence(
                            self.records, evidence, context),
                        session_id=session_id)
            self.append('restart-confirm', data)
            return dict(data, status='CONFIRMED', replayed=False,
                        progress=self._restart_progress(self.events[-1]),
                        dispatch_authorized=False,
                        external_copy_verified=False,
                        real_line_e2e='NOT_TESTED')

    def _restart_intent(self, *, session_id, media_key_value, restart_id):
        with self.locked():
            self._require_session(session_id)
            confirmation = self._restart_projection()['confirmations'].get(
                restart_id)
            need(confirmation is not None, 'RESTART_CONFIRMATION_REQUIRED')
            need(restart_id not in self._restart_projection()['activations'],
                 'RESTART_ALREADY_ACTIVATED')
            confirmation_data = confirmation['data']
            scope_media = {
                row['media_key']: (post, row)
                for post in confirmation_data['scope']['posts']
                for row in post['media']}
            scope_row = scope_media.get(media_key_value)
            need(scope_row is not None, 'RESTART_INTENT_OUTSIDE_SCOPE')
            post, scoped = scope_row
            list_directory = self._require_current_list_directory()
            latest_scan_id = self._latest_complete_scan_id()
            latest_scan = self._event_by_sequence(
                self._open_scan()[1][latest_scan_id]['start']['sequence'])
            need(latest_scan is not None and
                 latest_scan['sequence'] > confirmation['sequence'],
                 'POST_CONFIRMATION_RECOVERY_SCAN_REQUIRED')
            posts = self._assert_dispatch_inventory()
            observed_posts = {row['post_key'] for row in posts}
            media, _ = self._media_projection()
            need(media_key_value in media, 'MEDIA_NOT_OBSERVED')
            target = media[media_key_value]
            need(target['post_key'] == post['post_key'] and
                 target['identity'] == scoped['identity'] and
                 target['post_key'] in observed_posts,
                 'RESTART_MEDIA_IDENTITY_CHANGED')
            need(not target.get('missing'), 'MEDIA_CURRENTLY_MISSING')
            need(target.get('scan_id') == latest_scan_id,
                 'STALE_MEDIA_INVENTORY')
            detail = self._post_detail_for_scan(target['post_key'], latest_scan_id)
            need(detail is not None and not detail['no_media'],
                 'POST_MEDIA_DETAIL_REQUIRED')
            need(media_key_value not in self._source_unavailable_projection(),
                 'SOURCE_UNAVAILABLE_NO_RECOVERY')
            status = self._status_map()[media_key_value]
            need(status not in ('EXCLUDED', 'PROTECTED_HISTORY'),
                 'EXCLUDED_OR_PROTECTED_NO_REDOWNLOAD')
            need(status != 'COMPLETED' or media_key_value in scope_media,
                 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD')
            need(not self._pending_publish_plans(),
                 'PENDING_NAMING_TRANSACTION')
            self._assert_no_local_changed(allowing=scope_media)
            attempts = self._attempt_projection()
            prior = attempts['latest_by_media'].get(media_key_value)
            if prior is not None:
                prior_data = attempts['attempts'][prior]
                if (prior_data['schema'] == 'line-notes-intent/v3' and
                        prior_data.get('restart_id') == restart_id):
                    prior_result = self._attempt_result(prior, attempts)
                    need(prior_result in (None, 'UNKNOWN', 'STOPPED', 'NOT_SENT'),
                         'RESTART_ATTEMPT_ALREADY_OPEN_OR_FINISHED')
            resolved = set(self._completion_projection()[0])
            resolved |= set(self._active_media_versions())
            for other_key, attempt_id in attempts['latest_by_media'].items():
                if other_key in scope_media:
                    continue
                if other_key in resolved:
                    continue
                result = self._attempt_result(attempt_id, attempts)
                need(result in ('STOPPED', 'NOT_SENT'),
                     'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED')
            self._assert_dispatch_coverage()
            staging = _new_unique_directory(list_directory,
                                             '.line-notes-incoming-')
            need(not any(staging.iterdir()), 'EMPTY_STAGING_REQUIRED')
            info = staging.stat()
            effective_kind, kind_correction_ref = self._effective_media_kind(
                media_key_value, target['identity']['kind'])
            data = dict(schema='line-notes-intent/v3',
                        restart_id=restart_id,
                        generation=confirmation_data['generation'],
                        confirmation_ref=_event_ref(confirmation),
                        prior_attempt=(_event_ref(self._event_by_sequence(
                            attempts['order'][prior])) if prior is not None else None),
                        media_key=media_key_value,
                        post_key=target['post_key'],
                        identity=target['identity'],
                        effective_kind=effective_kind,
                        kind_correction_ref=kind_correction_ref,
                        attempt_id=uuid.uuid4().hex,
                        session_id=session_id,
                        scan_id=latest_scan_id,
                        destination=str(staging),
                        directory_device=info.st_dev,
                        directory_inode=info.st_ino,
                        save_all_limit=1,
                        save_all_count=0)
            self.append('intent', data)
            return dict(data, status='UNKNOWN', restart_id=restart_id,
                        dispatch_authorized=False)

    def intent(self, *, session_id, media_key_value, recovery_evidence=None,
               restart_id=None):
        if restart_id is not None:
            need(recovery_evidence is None,
                 'RESTART_EVIDENCE_BELONGS_TO_CONFIRMATION')
            return self._restart_intent(
                session_id=session_id, media_key_value=media_key_value,
                restart_id=restart_id)
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
            need(media_key_value not in self._source_unavailable_projection(),
                 'SOURCE_UNAVAILABLE_NO_RECOVERY')
            status = self._status_map()[media_key_value]
            need(status not in ('COMPLETED', 'EXCLUDED'),
                 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD')
            need(status != 'PROTECTED_HISTORY',
                 'PROTECTED_HISTORY_NO_REDOWNLOAD')
            detail = self._post_detail(target['post_key'])
            need(detail is not None and not detail['no_media'],
                 'POST_MEDIA_DETAIL_REQUIRED')
            need(detail.get('scan_id') == latest_scan_id,
                 'STALE_POST_DETAIL')
            need(target.get('scan_id') == latest_scan_id,
                 'STALE_MEDIA_INVENTORY')
            self._assert_dispatch_coverage()
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
            resolved = set(self._completion_projection()[0])
            resolved |= set(self._active_media_versions())
            for other_key, attempt_id in attempts['latest_by_media'].items():
                if other_key == media_key_value:
                    continue
                if other_key in resolved:
                    continue
                other_result = self._attempt_result(attempt_id, attempts)
                need(other_result in ('STOPPED', 'NOT_SENT'),
                     'ANOTHER_MEDIA_ATTEMPT_UNRESOLVED')
            staging = _new_unique_directory(list_directory,
                                             '.line-notes-incoming-')
            need(not any(staging.iterdir()), 'EMPTY_STAGING_REQUIRED')
            info = staging.stat()
            recovery_ref = (
                _preserve_evidence(
                    self.records, recovery_evidence,
                    self._intent_evidence_context(prior))
                if recovery_evidence is not None else None)
            effective_kind, kind_correction_ref = self._effective_media_kind(
                media_key_value, target['identity']['kind'])
            data = dict(schema='line-notes-intent/v2',
                        media_key=media_key_value,
                        post_key=target['post_key'],
                        identity=target['identity'],
                        effective_kind=effective_kind,
                        kind_correction_ref=kind_correction_ref,
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

    def _restart_attempt_scope(self, attempt_id, projection=None):
        projection = projection or self._attempt_projection()
        attempt = projection['attempts'].get(attempt_id)
        if attempt is None or attempt['schema'] != 'line-notes-intent/v3':
            return None
        restart = self._restart_projection()
        restart_id = attempt['restart_id']
        confirmation = restart['confirmations'].get(restart_id)
        need(confirmation is not None, 'RESTART_CONFIRMATION_REQUIRED')
        need(restart_id not in restart['activations'],
             'RESTART_ALREADY_ACTIVATED')
        for post in confirmation['data']['scope']['posts']:
            for row in post['media']:
                if (row['media_key'] == attempt['media_key'] and
                        post['post_key'] == attempt['post_key'] and
                        row['identity'] == attempt['identity']):
                    return dict(confirmation=confirmation, post=post, row=row)
        raise NotesError('RESTART_INTENT_OUTSIDE_SCOPE')

    def outcome(self, *, session_id, attempt_id, outcome, evidence):
        need(outcome in OUTCOMES, 'INVALID_OUTCOME')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            need(attempt_id not in projection['outcomes'] and
                 attempt_id not in projection['reconciles'],
                 'OUTCOME_ALREADY_RECORDED')
            restart_scope = self._restart_attempt_scope(attempt_id, projection)
            need(media_key_value not in self._completion_projection()[0] or
                 restart_scope is not None,
                 'COMPLETION_IMMUTABLE')
            data = dict(schema='line-notes-outcome/v1',
                        attempt_id=attempt_id,
                        media_key=media_key_value,
                        outcome=outcome,
                        evidence=_preserve_evidence(
                            self.records, evidence,
                            self._intent_evidence_context(attempt_id)))
            self.append('outcome', data)
            return data

    def reconcile(self, *, session_id, attempt_id, result, evidence):
        need(result in OUTCOMES, 'INVALID_RECONCILE_RESULT')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            current = self._attempt_result(attempt_id, projection)
            need(current == 'UNKNOWN', 'UNKNOWN_OUTCOME_REQUIRED_FOR_RECONCILE')
            restart_scope = self._restart_attempt_scope(attempt_id, projection)
            need(media_key_value not in self._completion_projection()[0] or
                 restart_scope is not None,
                 'COMPLETION_IMMUTABLE')
            data = dict(schema='line-notes-reconcile/v1',
                        attempt_id=attempt_id,
                        media_key=media_key_value,
                        result=result,
                        evidence=_preserve_evidence(
                            self.records, evidence,
                            self._intent_evidence_context(attempt_id)))
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
            context = self._media_evidence_context(media_key_value)
            data = dict(schema='line-notes-%s/v1' % kind,
                        media_key=media_key_value,
                        reason=reason,
                        evidence=_preserve_evidence(
                            self.records, evidence, context))
            self.append(kind, data)
            return data

    def exclude(self, *, session_id, media_key_value, reason, evidence):
        return self._record_terminal_media_state(
            'exclusion', media_key_value, reason, evidence,
            session_id=session_id)

    def protect(self, *, media_key_value, reason, evidence):
        return self._record_terminal_media_state(
            'protection', media_key_value, reason, evidence)

    def evidence_audit(self):
        rows = []
        with self.locked(audit_rows=rows):
            corrections, _latest = self._evidence_correction_projection()
            correction_rows = [
                dict(event['data'], sequence=event['sequence'],
                     event_sha256=_event_sha256(event))
                for events in corrections.values() for event in events]
            return dict(
                schema='line-notes-evidence-audit/v1',
                local_list_id=self.records.name,
                event_count=len(self.events),
                event_chain='VERIFIED',
                integrity_ok=all(row['integrity_ok'] for row in rows),
                references=rows,
                evidence_corrections=correction_rows,
                business_projection_omitted=True)

    def evidence_correct(self, *, session_id, page_sequence, page_sha256,
                         original_evidence_sha256, replacement,
                         reason, previous_correction_ref=None):
        audit_rows = []
        with self.locked(audit_rows=audit_rows):
            self._require_session(session_id)
            _hex(page_sha256, 'INVALID_EVIDENCE_CORRECTION')
            _hex(original_evidence_sha256, 'INVALID_EVIDENCE_CORRECTION')
            need(isinstance(reason, str) and bool(reason.strip()),
                 'INVALID_EVIDENCE_CORRECTION')
            if previous_correction_ref is not None:
                _check_event_ref(previous_correction_ref,
                                 'INVALID_EVIDENCE_CORRECTION')
            target = self._event_by_sequence(page_sequence)
            need(target is not None and target['kind'] == 'page',
                 'EVIDENCE_CORRECTION_TARGET_CHANGED')
            need(digest(encoded(target)) == page_sha256,
                 'EVIDENCE_CORRECTION_TARGET_CHANGED')
            original = _validate_evidence_ref_shape(
                target['data']['evidence'], 'EVIDENCE_CORRECTION_ORIGINAL_CHANGED')
            need(original['sha256'] == original_evidence_sha256,
                 'EVIDENCE_CORRECTION_ORIGINAL_CHANGED')
            prior = [
                event for event in self.events
                if event['kind'] == 'evidence-correction' and
                event['data']['page_sequence'] == page_sequence]
            if prior:
                need(previous_correction_ref == _event_ref(prior[-1]),
                     'EVIDENCE_CORRECTION_CHAIN_CHANGED')
            else:
                need(previous_correction_ref is None,
                     'EVIDENCE_CORRECTION_CHAIN_CHANGED')
            for row in audit_rows:
                if row['integrity_ok']:
                    continue
                if row.get('event_sequence') == page_sequence:
                    continue
                if (row.get('event_kind') == 'evidence-correction' and
                        row.get('event_page_sequence') == page_sequence):
                    continue
                raise NotesError('EVIDENCE_REPAIR_SCOPE_MISMATCH')
            context = _evidence_context(
                list_key=self.list_data['list_key'],
                scan_id=target['data']['scan_id'])
            data = dict(
                schema='line-notes-evidence-correction/v1',
                page_sequence=page_sequence,
                page_sha256=page_sha256,
                original_evidence_sha256=original_evidence_sha256,
                replacement_ref=_preserve_evidence(
                    self.records, replacement, context),
                reason=reason,
                session_id=session_id,
                previous_correction_ref=previous_correction_ref)
            self.append('evidence-correction', data)
            return dict(data, correction_ref=_event_ref(self.events[-1]))

    def media_kind_correct(self, *, session_id, media_key_value,
                           inventory_sequence, to_kind, evidence,
                           inventory_sha256=None):
        with self.locked():
            self._require_session(session_id)
            latest, scans = self._open_scan()
            need(latest is not None and scans[latest]['complete'] is not None,
                 'COMPLETE_NOTES_SCAN_REQUIRED')
            inventory = self._event_by_sequence(inventory_sequence)
            need(inventory is not None and inventory['kind'] == 'media',
                 'MEDIA_KIND_INVENTORY_CHANGED')
            data = inventory['data']
            need(data.get('scan_id') == latest,
                 'MEDIA_KIND_SCAN_CHANGED')
            rows = [row for row in data['items']
                    if row['media_key'] == media_key_value]
            need(len(rows) == 1, 'MEDIA_KIND_SCOPE_CHANGED')
            media, snapshots = self._media_projection()
            target = media.get(media_key_value)
            need(target is not None and not target.get('missing') and
                 target['post_key'] == data['post_key'] and
                 target['scan_id'] == latest,
                 'MEDIA_KIND_SCOPE_CHANGED')
            current = [event for event in snapshots.get(data['post_key'], [])
                       if event['data'].get('scan_id') == latest]
            need(current and current[-1]['sequence'] == inventory_sequence,
                 'MEDIA_KIND_INVENTORY_CHANGED')
            for earlier in self.events:
                if (earlier['kind'] in ('intent', 'verification', 'completion',
                                        'exclusion', 'protection') and
                        earlier['data'].get('media_key') == media_key_value):
                    raise NotesError('MEDIA_KIND_AFTER_ATTEMPT')
            from_kind, _prior_ref = self._effective_media_kind(
                media_key_value, target['identity']['kind'])
            need(to_kind in MEDIA_KINDS and to_kind != from_kind,
                 'INVALID_MEDIA_KIND_CORRECTION')
            actual_inventory_sha256 = _event_sha256(inventory)
            if inventory_sha256 is not None:
                _hex(inventory_sha256, 'INVALID_MEDIA_KIND_CORRECTION')
                need(inventory_sha256 == actual_inventory_sha256,
                     'MEDIA_KIND_INVENTORY_CHANGED')
            corrections = [event for event in self.events
                           if event['kind'] == 'media-kind-correction' and
                           event['data']['media_key'] == media_key_value]
            previous = _event_ref(corrections[-1]) if corrections else None
            context = _evidence_context(
                list_key=self.list_data['list_key'],
                post_key=data['post_key'], media_key=media_key_value,
                scan_id=latest)
            correction = dict(
                schema='line-notes-media-kind-correction/v1',
                media_key=media_key_value,
                post_key=data['post_key'],
                scan_id=latest,
                inventory_sequence=inventory_sequence,
                inventory_sha256=actual_inventory_sha256,
                from_kind=from_kind,
                to_kind=to_kind,
                previous_correction=previous,
                evidence=_preserve_evidence(self.records, evidence, context),
                session_id=session_id)
            self.append('media-kind-correction', correction)
            return dict(correction, correction_ref=_event_ref(self.events[-1]))

    def source_unavailable(self, *, session_id, media_key_value,
                           attempt_id, evidence):
        with self.locked():
            self._require_session(session_id)
            attempts = self._attempt_projection()
            need(attempts['latest_by_media'].get(media_key_value) == attempt_id,
                 'SOURCE_UNAVAILABLE_ATTEMPT_CHANGED')
            intent_data = attempts['attempts'][attempt_id]
            need(self._attempt_result(attempt_id, attempts) == 'STOPPED',
                 'SOURCE_UNAVAILABLE_REQUIRES_STOPPED')
            need(media_key_value not in self._completion_projection()[0] and
                 media_key_value not in self._exclusion_projection() and
                 media_key_value not in self._protection_projection(),
                 'SOURCE_UNAVAILABLE_WITH_TERMINAL_WORK')
            need(not any(event['data'].get('attempt_id') == attempt_id
                         for event in self._pending_publish_plans()),
                 'SOURCE_UNAVAILABLE_WITH_TERMINAL_WORK')
            need(media_key_value not in self._source_unavailable_projection(),
                 'DUPLICATE_SOURCE_UNAVAILABLE')
            context = self._intent_evidence_context(attempt_id)
            data = dict(
                schema='line-notes-source-unavailable/v1',
                media_key=media_key_value,
                post_key=intent_data['post_key'],
                attempt_id=attempt_id,
                reason='SOURCE_EXPIRED',
                evidence=_preserve_evidence(self.records, evidence, context),
                session_id=session_id)
            self.append('source-unavailable', data)
            return data

    def _media_rows(self):
        media, _ = self._media_projection()
        statuses = self._status_map()
        availability = self._effective_local_availability()
        active = self._active_media_versions()
        unavailable = self._source_unavailable_projection()
        rows = []
        for key, row in media.items():
            status = statuses[key]
            local = availability.get(key, LOCAL_NOT_APPLICABLE)
            effective_kind, correction_ref = self._effective_media_kind(
                key, row['identity']['kind'])
            current = dict(
                media_key=key, post_key=row['post_key'],
                identity=row['identity'], kind=row['identity']['kind'],
                effective_kind=effective_kind,
                kind_correction_ref=correction_ref,
                source_order=row['source_order'],
                missing=bool(row.get('missing')),
                missing_reason=row.get('missing_reason'),
                status=status, local_files=local,
                source_availability=('EXPIRED' if key in unavailable
                                     else 'UNKNOWN'))
            if key in active:
                version = active[key]
                current.update(
                    active_restart_id=version['confirmation']['data']['restart_id'],
                    active_generation=version['confirmation']['data']['generation'],
                    active_candidate_ref=_event_ref(version['candidate']),
                    version_directory=str(Path(
                        version['candidate']['data']['candidate']['path']).parent))
            rows.append(current)
        return rows

    def _effective_media_kind(self, media_key_value, original_kind):
        corrections = [event for event in self.events
                       if event['kind'] == 'media-kind-correction' and
                       event['data']['media_key'] == media_key_value]
        if not corrections:
            return original_kind, None
        latest = corrections[-1]
        return latest['data']['to_kind'], _event_ref(latest)

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

    def _unresolved_attempts(self):
        attempts = self._attempt_projection()
        completions, _ = self._completion_projection()
        exclusions = self._exclusion_projection()
        protections = self._protection_projection()
        pending = {event['data']['attempt_id']:
                   event['data']['transaction_id']
                   for event in self._pending_publish_plans()}
        unavailable = self._source_unavailable_projection()
        rows = []
        for key, attempt_id in attempts['latest_by_media'].items():
            if key in completions or key in exclusions or key in protections:
                continue
            data = attempts['attempts'][attempt_id]
            rows.append(dict(
                media_key=key,
                attempt_id=attempt_id,
                scan_id=data.get('scan_id'),
                has_outcome=attempt_id in attempts['outcomes'],
                last_result=self._attempt_result(attempt_id, attempts),
                destination=data['destination'],
                pending_naming=attempt_id in pending,
                scan_binding_match=self._attempt_scan_binding_matches(data),
                source_availability=('EXPIRED' if key in unavailable
                                     else 'UNKNOWN')))
        return sorted(rows, key=lambda row: row['media_key'])

    def _project_summary(self):
        media_rows = self._media_rows()
        post_rows = self._post_rows()
        open_restart = self._restart_open_confirmation()
        open_restart_progress = (
            self._restart_progress(open_restart)
            if open_restart is not None else None)
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
        if open_restart_progress is not None:
            blockers.append('RESTART_BATCH_OPEN')
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
        corrections, _latest_correction = (
            self._evidence_correction_projection())
        correction_rows = [dict(event['data'],
                                sequence=event['sequence'],
                                event_sha256=_event_sha256(event))
                           for events in corrections.values()
                           for event in events]
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
                    unresolved_attempts=self._unresolved_attempts(),
                    restart_batch_open=open_restart_progress is not None,
                    open_restart=open_restart_progress,
                    evidence_corrections=correction_rows,
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
        active = self._active_media_versions()
        active_directories = set()
        for key, version in active.items():
            candidate = version['candidate']['data']['candidate']
            if version['candidate']['data']['post_key'] != post_key_value:
                continue
            directory = Path(candidate['path']).parent
            need(directory.is_relative_to(list_directory),
                 'ACTIVE_VERSION_DIRECTORY_CHANGED')
            entry = _entry(directory)
            need(entry is not None and stat.S_ISDIR(entry.st_mode) and
                 not directory.is_symlink() and
                 directory == directory.resolve(strict=True),
                 'ACTIVE_VERSION_DIRECTORY_CHANGED')
            active_directories.add(directory)
        need(len(active_directories) <= 1,
             'MULTIPLE_ACTIVE_VERSION_DIRECTORIES')
        if active_directories:
            return active_directories.pop(), True
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

    def _next_media_number(self, post_key_value, directory):
        maximum = 0
        for event in self.events:
            if event['kind'] == 'completion':
                data = event['data']
                if data['destination'] != str(directory):
                    continue
            elif event['kind'] == 'publish-plan':
                data = event['data']
                if data['target_directory'] != str(directory):
                    continue
            elif event['kind'] == 'restart-copy-plan':
                data = event['data']
                if data['target_directory'] != str(directory):
                    continue
            elif event['kind'] == 'restart-candidate':
                data = event['data']
                if str(Path(data['candidate']['path']).parent) != str(directory):
                    continue
            else:
                continue
            if data['post_key'] != post_key_value:
                continue
            if event['kind'] == 'completion':
                name = data['target_file']['name']
            elif event['kind'] == 'restart-candidate':
                name = data['candidate']['name']
            else:
                name = data['target_name']
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
        number = self._next_media_number(
            intent_data['post_key'], target_directory)
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

    def _target_names_for_directory(self, directory):
        names = set()
        directory_string = str(directory)
        for event in self.events:
            if event['kind'] == 'completion' and \
                    event['data']['destination'] == directory_string:
                names.add(event['data']['target_file']['name'])
            elif event['kind'] == 'publish-plan' and \
                    event['data']['target_directory'] == directory_string:
                names.add(event['data']['target_name'])
            elif event['kind'] == 'restart-copy-plan' and \
                    event['data']['target_directory'] == directory_string:
                names.add(event['data']['target_name'])
            elif event['kind'] == 'restart-candidate' and \
                    str(Path(event['data']['candidate']['path']).parent) == \
                    directory_string:
                names.add(event['data']['candidate']['name'])
        return names

    def _ensure_publish_directory(self, plan):
        target_directory = Path(plan['target_directory'])
        list_directory = Path(plan['list_directory'])
        current = self._require_current_list_directory()
        active_directories = {
            Path(version['candidate']['data']['candidate']['path']).parent
            for version in self._active_media_versions().values()}
        active_target = target_directory in active_directories
        need(list_directory == current and
             (target_directory.parent == current or
              (active_target and target_directory.is_relative_to(current) and
               target_directory.parent.parent.name == 'versions' and
               target_directory.parent.parent.parent == current)),
             'PUBLISH_DIRECTORY_OUTSIDE_CURRENT_LIST')
        entry = _entry(target_directory)
        if entry is None:
            need(plan['target_directory_existed'] is False and not active_target,
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
        expected_names = self._target_names_for_directory(target_directory)
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

    @staticmethod
    def _restart_scope_media(confirmation):
        return {
            row['media_key']: (post, row)
            for post in confirmation['scope']['posts']
            for row in post['media']}

    def _restart_superseded_attempt(self, attempt_id, projection=None):
        projection = projection or self._attempt_projection()
        sequence = projection['order'].get(attempt_id)
        if sequence is None:
            return False
        for confirmation in self._restart_projection()['confirmations'].values():
            for post in confirmation['data']['scope']['posts']:
                for row in post['media']:
                    prior = row.get('prior_attempt')
                    if prior is not None and prior['sequence'] == sequence:
                        return True
        return False

    def _validate_attempt_origin_scan(self, intent_data):
        scan_id = intent_data.get('scan_id')
        need(isinstance(scan_id, str) and bool(scan_id),
             'INTENT_SCAN_BINDING_REQUIRED')
        _latest, scans = self._open_scan()
        scan = scans.get(scan_id)
        need(scan is not None and scan['complete'] is not None,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        posts = {row['post_key']: row
                 for row in scan['complete']['data']['posts']}
        need(intent_data['post_key'] in posts,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        detail = self._post_detail_for_scan(
            intent_data['post_key'], scan_id)
        need(detail is not None and detail.get('scan_id') == scan_id,
             'ATTEMPT_SCAN_BINDING_CHANGED')
        media, _ = self._media_projection()
        target = media.get(intent_data['media_key'])
        need(target is not None and
             target.get('post_key') == intent_data['post_key'] and
             target.get('scan_id') == scan_id,
             'ATTEMPT_SCAN_BINDING_CHANGED')

    def _validate_restart_scope_current(self, confirmation):
        latest, scans = self._open_scan()
        need(latest is not None and scans[latest]['complete'] is not None,
             'COMPLETE_NOTES_SCAN_REQUIRED')
        complete = scans[latest]['complete']
        need(complete['sequence'] > confirmation['sequence'],
             'POST_CONFIRMATION_RECOVERY_SCAN_REQUIRED')
        scan_posts = {row['post_key']: row
                      for row in complete['data']['posts']}
        media, _ = self._media_projection()
        for post in confirmation['data']['scope']['posts']:
            need(post['post_key'] in scan_posts and
                 scan_posts[post['post_key']]['identity'] == post['identity'],
                 'RESTART_SCOPE_POST_CHANGED')
            expected = {row['media_key'] for row in post['media']}
            expected |= {row['media_key'] for row in post['missing']}
            current = {
                key for key, row in media.items()
                if row.get('post_key') == post['post_key'] and
                row.get('scan_id') == latest}
            need(current == expected, 'RESTART_SCOPE_MEDIA_CHANGED')
            for key in expected:
                row = media.get(key)
                need(row is not None and row.get('post_key') == post['post_key'],
                     'RESTART_SCOPE_MEDIA_CHANGED')
                scope_row = next(
                    (item for item in post['media'] + post['missing']
                     if item['media_key'] == key), None)
                need(scope_row is not None, 'RESTART_SCOPE_MEDIA_CHANGED')
                if 'identity' in scope_row:
                    need(row.get('identity') == scope_row['identity'],
                         'RESTART_SCOPE_MEDIA_CHANGED')
        return latest

    def _restart_version_target_directory(self, confirmation, post):
        version_directory = Path(post['version_directory'])
        list_directory = self._require_current_list_directory()
        need(version_directory.parent.parent.name == 'versions' and
             version_directory.parent.parent.parent == list_directory and
             version_directory.parent.name.startswith('g') and
             version_directory.parent.name == 'g%08d' %
             confirmation['generation'],
             'RESTART_VERSION_DIRECTORY_CHANGED')
        return version_directory

    def _next_restart_media_number(self, target_directory):
        maximum = 0
        for name in self._target_names_for_directory(target_directory):
            match = re.fullmatch(r'media_([0-9]+)(\.[^./]+)', name)
            need(match is not None, 'PUBLISHED_MEDIA_NAME_CHANGED')
            maximum = max(maximum, int(match.group(1)))
        return maximum + 1

    def _ensure_restart_version_directory(self, plan):
        list_directory = self._require_current_list_directory()
        need(plan['list_directory'] == str(list_directory),
             'RESTART_LIST_DIRECTORY_CHANGED')
        target_directory = Path(plan['target_directory'])
        need(target_directory.is_absolute() and
             target_directory.is_relative_to(list_directory) and
             target_directory.parent.parent.name == 'versions' and
             target_directory.parent.parent.parent == list_directory,
             'RESTART_VERSION_DIRECTORY_CHANGED')
        for directory in (list_directory / 'versions',
                          target_directory.parent,
                          target_directory):
            entry = _entry(directory)
            if entry is None:
                try:
                    os.mkdir(str(directory), 0o700)
                except FileExistsError:
                    pass
                sync_dir(directory.parent)
                entry = _entry(directory)
            need(entry is not None and stat.S_ISDIR(entry.st_mode) and
                 not directory.is_symlink() and
                 directory == directory.resolve(strict=True),
                 'RESTART_VERSION_DIRECTORY_CHANGED')
        expected = self._target_names_for_directory(target_directory)
        actual = {path.name for path in target_directory.iterdir()}
        need(actual <= expected, 'RESTART_VERSION_DIRECTORY_UNEXPECTED_CONTENT')
        return target_directory

    def _append_restart_copy_plan(self, *, confirmation_event, intent_data,
                                  source):
        confirmation = confirmation_event['data']
        scope = self._restart_scope_media(confirmation)
        entry = scope.get(intent_data['media_key'])
        need(entry is not None, 'RESTART_INTENT_OUTSIDE_SCOPE')
        post, _scope_row = entry
        target_directory = self._restart_version_target_directory(
            confirmation, post)
        target_directory_existed = _entry(target_directory) is not None
        number = self._next_restart_media_number(target_directory)
        width = max(3, len(str(number)))
        suffix = Path(source['name']).suffix
        _validate_media_suffix(self._attempt_kind(intent_data), source['name'])
        target_name = 'media_%0*d%s' % (width, number, suffix)
        target_path = target_directory / target_name
        need(_entry(target_path) is None, 'TARGET_ALREADY_EXISTS')
        data = dict(schema=RESTART_COPY_PLAN_SCHEMA,
                    plan_id=uuid.uuid4().hex,
                    restart_id=intent_data['restart_id'],
                    generation=intent_data['generation'],
                    confirmation_ref=_event_ref(confirmation_event),
                    attempt_id=intent_data['attempt_id'],
                    media_key=intent_data['media_key'],
                    post_key=intent_data['post_key'],
                    source=source,
                    list_directory=str(self._require_current_list_directory()),
                    target_directory=str(target_directory),
                    target_name=target_name,
                    number=number,
                    extension=suffix,
                    target_directory_existed=target_directory_existed,
                    created_at=_utc_now())
        self.append('restart-copy-plan', data)
        return self.events[-1], target_path

    def _stable_candidate_file(self, path, interval):
        samples = []
        for sample in range(3):
            if sample and interval:
                time.sleep(interval)
            row = _inventory_row(path)
            need(not samples or row == samples[-1],
                 'RESTART_CANDIDATE_NOT_STABLE')
            samples.append(row)
        return samples[-1]

    def _restart_verify_locked(self, *, session_id, attempt_id, decoder=None,
                               decoder_sha256=None, verifier=None,
                               stability_interval=DEFAULT_STABILITY_INTERVAL,
                               progress_callback=None,
                               stall_seconds=DEFAULT_STALL_SECONDS):
        need(verifier is None or self._allow_injected_verification,
             'INJECTED_VERIFICATION_NOT_ALLOWED')
        self._require_session(session_id)
        projection, media_key_value = self._require_latest_attempt(attempt_id)
        intent_data = projection['attempts'][attempt_id]
        need(intent_data['schema'] == 'line-notes-intent/v3',
             'RESTART_INTENT_REQUIRED')
        restart = self._restart_projection()
        restart_id = intent_data['restart_id']
        confirmation = restart['confirmations'].get(restart_id)
        need(confirmation is not None, 'RESTART_CONFIRMATION_REQUIRED')
        need(restart_id not in restart['activations'],
             'RESTART_ALREADY_ACTIVATED')
        scope = self._restart_scope_media(confirmation['data'])
        entry = scope.get(media_key_value)
        need(entry is not None and
             entry[0]['post_key'] == intent_data['post_key'] and
             entry[1]['identity'] == intent_data['identity'],
             'RESTART_INTENT_OUTSIDE_SCOPE')
        existing = restart['candidates'].get(media_key_value)
        if existing is not None:
            need(existing['data']['restart_id'] == restart_id,
                 'RESTART_CANDIDATE_ATTEMPT_CHANGED')
            if (existing['data']['attempt_id'] == attempt_id and
                    self._candidate_file_availability(
                        existing['data']['candidate']) == LOCAL_VERIFIED):
                return dict(existing['data'], status='CANDIDATE_VERIFIED',
                            replayed=True,
                            candidate_ref=_event_ref(existing),
                            dispatch_authorized=False)
        need(self._attempt_result(attempt_id, projection) ==
             'DOWNLOAD_FINISHED', 'KNOWN_DOWNLOAD_FINISH_REQUIRED')
        self._validate_attempt_origin_scan(intent_data)
        self._assert_no_local_changed(allowing=scope)
        need(not self._pending_publish_plans(),
             'PENDING_NAMING_TRANSACTION')
        staging = self._validate_staging(intent_data)
        stable = _stable_media_inventory(
            staging, expected=1, interval=stability_interval)
        source = stable[0]
        kind = self._attempt_kind(intent_data)
        _validate_media_suffix(kind, source['name'])
        plans = [
            event for event in restart['plans'].values()
            if event['data']['attempt_id'] == attempt_id and
            event['data']['media_key'] == media_key_value and
            event['data']['plan_id'] not in restart['candidates_by_plan']]
        plans.sort(key=lambda event: event['sequence'])
        plan_event = plans[-1] if plans else None
        target_path = None
        if plan_event is not None:
            need(plan_event['data']['source'] == source,
                 'RESTART_COPY_SOURCE_CHANGED')
            candidate_path = (Path(plan_event['data']['target_directory']) /
                              plan_event['data']['target_name'])
            if _entry(candidate_path) is None:
                target_path = candidate_path
        if target_path is None:
            plan_event, target_path = self._append_restart_copy_plan(
                confirmation_event=confirmation, intent_data=intent_data,
                source=source)
        target_directory = self._ensure_restart_version_directory(
            plan_event['data'])
        need(target_path.parent == target_directory,
             'RESTART_COPY_TARGET_CHANGED')
        try:
            media_verify.copy_exclusive(
                Path(source['path']), target_path, source)
        except media_verify.MediaVerificationError as exc:
            raise NotesMediaVerificationError(exc.code, exc.evidence) from exc
        candidate = self._stable_candidate_file(
            target_path, stability_interval)
        need(candidate['size'] == source['size'] and
             candidate['sha256'] == source['sha256'],
             'ISOLATED_COPY_MISMATCH')
        verification = _verify_media(
            kind=kind, path=target_path, row=candidate,
            identity=intent_data['identity'], records=self.records,
            decoder=decoder, decoder_sha256=decoder_sha256,
            verifier=verifier, progress_callback=progress_callback,
            stall_seconds=stall_seconds,
            stability_interval=stability_interval)
        after = _inventory_row(target_path)
        need(after == candidate, 'RESTART_CANDIDATE_CHANGED')
        data = dict(schema=RESTART_CANDIDATE_SCHEMA,
                    restart_id=restart_id,
                    generation=intent_data['generation'],
                    plan_ref=_event_ref(plan_event),
                    attempt_id=attempt_id,
                    media_key=media_key_value,
                    post_key=intent_data['post_key'],
                    kind=kind,
                    source=source,
                    candidate=candidate,
                    manifest=[candidate],
                    manifest_sha256=digest(encoded([candidate])),
                    verification=verification,
                    verified_at=_utc_now())
        self.append('restart-candidate', data)
        return dict(data, status='CANDIDATE_VERIFIED', replayed=False,
                    candidate_ref=_event_ref(self.events[-1]),
                    dispatch_authorized=False)

    def _restart_activate_locked(self, *, session_id):
        self._require_session(session_id)
        restart = self._restart_projection()
        confirmation = self._restart_open_confirmation()
        need(confirmation is not None, 'NO_OPEN_RESTART_BATCH')
        restart_id = confirmation['data']['restart_id']
        need(restart_id not in restart['activations'],
             'RESTART_ALREADY_ACTIVATED')
        self._validate_restart_scope_current(confirmation)
        need(not self._pending_publish_plans(),
             'PENDING_NAMING_TRANSACTION')
        candidates = {
            event['data']['media_key']: event
            for event in restart['candidates'].values()
            if event['data']['restart_id'] == restart_id}
        rows = []
        for post in confirmation['data']['scope']['posts']:
            for scope_row in sorted(post['media'],
                                    key=lambda item: item['media_key']):
                key = scope_row['media_key']
                candidate = candidates.get(key)
                need(candidate is not None,
                     'RESTART_CANDIDATE_REQUIRED')
                need(candidate['data']['post_key'] == post['post_key'] and
                     candidate['data']['media_key'] == key,
                     'RESTART_CANDIDATE_SCOPE_CHANGED')
                availability = self._candidate_file_availability(
                    candidate['data']['candidate'])
                need(availability == LOCAL_VERIFIED,
                     'RESTART_CANDIDATE_CHANGED')
                rows.append(dict(media_key=key,
                                 post_key=post['post_key'],
                                 candidate_ref=_event_ref(candidate),
                                 candidate=candidate['data']['candidate']))
        rows.sort(key=lambda row: row['media_key'])
        data = dict(schema=RESTART_ACTIVATION_SCHEMA,
                    restart_id=restart_id,
                    generation=confirmation['data']['generation'],
                    confirmation_ref=_event_ref(confirmation),
                    scope_digest=confirmation['data']['scope_digest'],
                    candidates=rows,
                    session_id=session_id,
                    activated_at=_utc_now())
        self.append('restart-activation', data)
        return dict(data, status='ACTIVATED', replayed=False,
                    activation_ref=_event_ref(self.events[-1]),
                    progress=self._restart_progress(confirmation),
                    dispatch_authorized=False,
                    external_copy_verified=False,
                    real_line_e2e='NOT_TESTED')

    def restart_resume(self, *, session_id, decoder=None,
                       decoder_sha256=None, verifier=None,
                       stability_interval=DEFAULT_STABILITY_INTERVAL,
                       progress_callback=None,
                       stall_seconds=DEFAULT_STALL_SECONDS):
        with self.locked():
            self._require_session(session_id)
            restart = self._restart_projection()
            confirmation = self._restart_open_confirmation()
            if confirmation is None:
                activated = [
                    event for event in restart['activations'].values()]
                if activated:
                    event = max(activated, key=lambda row: row['sequence'])
                    return dict(action='ALREADY_ACTIVATED',
                                activation=event['data'],
                                activation_ref=_event_ref(event),
                                dispatch_authorized=False)
                return dict(action='NO_OPEN_RESTART_BATCH',
                            dispatch_authorized=False)
            restart_id = confirmation['data']['restart_id']
            scope = self._restart_scope_media(confirmation['data'])
            for key in sorted(scope):
                candidate = restart['candidates'].get(key)
                if (candidate is not None and
                        self._candidate_file_availability(
                            candidate['data']['candidate']) == LOCAL_VERIFIED):
                    continue
                attempt_id = self._attempt_projection()['latest_by_media'].get(key)
                if attempt_id is None:
                    continue
                attempt = self._attempt_projection()['attempts'][attempt_id]
                if (attempt.get('schema') == 'line-notes-intent/v3' and
                        attempt.get('restart_id') == restart_id and
                        self._attempt_result(attempt_id) ==
                        'DOWNLOAD_FINISHED'):
                    self._restart_verify_locked(
                        session_id=session_id, attempt_id=attempt_id,
                        decoder=decoder, decoder_sha256=decoder_sha256,
                        verifier=verifier,
                        stability_interval=stability_interval,
                        progress_callback=progress_callback,
                        stall_seconds=stall_seconds)
            restart = self._restart_projection()
            candidates = {
                event['data']['media_key']: event
                for event in restart['candidates'].values()
                if event['data']['restart_id'] == restart_id}
            ready = all(
                key in candidates and self._candidate_file_availability(
                    candidates[key]['data']['candidate']) == LOCAL_VERIFIED
                for key in scope)
            progress = self._restart_progress(confirmation)
            if ready:
                activated = self._restart_activate_locked(
                    session_id=session_id)
                return dict(action='RESTART_ACTIVATED',
                            activation=activated, progress=progress,
                            dispatch_authorized=False,
                            external_copy_verified=False,
                            real_line_e2e='NOT_TESTED')
            return dict(action='RESTART_IN_PROGRESS', progress=progress,
                        dispatch_authorized=False,
                        external_copy_verified=False,
                        real_line_e2e='NOT_TESTED')

    def verify(self, *, session_id, attempt_id, decoder=None,
               decoder_sha256=None, verifier=None,
               stability_interval=DEFAULT_STABILITY_INTERVAL,
               progress_callback=None, stall_seconds=DEFAULT_STALL_SECONDS):
        need(verifier is None or self._allow_injected_verification,
             'INJECTED_VERIFICATION_NOT_ALLOWED')
        with self.locked():
            self._require_session(session_id)
            projection, media_key_value = self._require_latest_attempt(attempt_id)
            if projection['attempts'][attempt_id]['schema'] == \
                    'line-notes-intent/v3':
                return self._restart_verify_locked(
                    session_id=session_id, attempt_id=attempt_id,
                    decoder=decoder, decoder_sha256=decoder_sha256,
                    verifier=verifier,
                    stability_interval=stability_interval,
                    progress_callback=progress_callback,
                    stall_seconds=stall_seconds)
            need(not self._restart_superseded_attempt(
                     attempt_id, projection), 'RESTART_SUPERSEDED_ATTEMPT')
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
                kind = self._attempt_kind(intent_data)
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
                need(not self._restart_superseded_attempt(
                         attempt_id, attempts), 'RESTART_SUPERSEDED_ATTEMPT')
                intent_data = attempts['attempts'].get(attempt_id)
                need(intent_data is not None, 'PUBLISH_ATTEMPT_CHANGED')
                self._require_attempt_scan_binding(
                    intent_data, code='SCAN_BINDING_REVIEW_REQUIRED',
                    missing_code='SCAN_BINDING_REVIEW_REQUIRED')
                completion = self._execute_publish(plans[0])
                return dict(action='PUBLISH_RESUMED',
                            completion=completion['data'],
                            dispatch_authorized=False)
            projection = self._attempt_projection()
            unavailable = self._source_unavailable_projection()
            actions = []
            for media_key_value, attempt_id in projection['latest_by_media'].items():
                if media_key_value in self._completion_projection()[0]:
                    continue
                intent_data = projection['attempts'][attempt_id]
                if media_key_value in unavailable:
                    action = 'SOURCE_UNAVAILABLE'
                elif not self._attempt_scan_binding_matches(intent_data):
                    action = 'SCAN_BINDING_REVIEW_REQUIRED'
                else:
                    result = self._attempt_result(attempt_id, projection)
                    if result in (None, 'UNKNOWN'):
                        action = 'RECONCILE_REQUIRED'
                    elif result == 'DOWNLOAD_FINISHED':
                        action = 'VERIFY_REQUIRED'
                    else:
                        action = 'RECOVERY_REVIEW_REQUIRED'
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


def _list_identity_cli(parser, args):
    return list_identity(
        visual_key=args.visual_key,
        context_id=args.context_id,
        signals=_json_cli_argument(parser, args.signals, '--signals', None))


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

    evidence_pack = sub.add_parser(
        'evidence-pack',
        help='Create one immutable line-notes-evidence/v2 bundle')
    evidence_pack.add_argument('--statement', required=True,
                               help='Non-empty absolute project-local statement file')
    evidence_pack.add_argument(
        '--asset', action='append', nargs=2, default=[],
        metavar=('ROLE', 'PATH'),
        help='Repeatable absolute project-local asset role/path pair')
    evidence_pack.add_argument('--output-dir', required=True,
                               help=('New absolute project-private evidence directory '
                                     'under .local/line-backup/tasks; parent must exist'))
    evidence_pack.add_argument('--list-key')
    evidence_pack.add_argument('--post-key')
    evidence_pack.add_argument('--media-key')
    evidence_pack.add_argument('--attempt-id')
    evidence_pack.add_argument('--scan-id')

    list_key_command = sub.add_parser(
        'list-key',
        help='Compute one list key from identity inputs without a ledger')
    list_key_command.add_argument(
        '--visual-key', required=True,
        help='Agent-grounded visual identity key; whitespace and Unicode are preserved')
    list_key_command.add_argument(
        '--context-id',
        help='Optional foreground context identity; whitespace and Unicode are preserved')
    list_key_command.add_argument(
        '--signals', help='Optional strict JSON identity signals or @JSON-file')

    init = sub.add_parser('init', help='Create a new notes ledger')
    init.add_argument('--collection', help='Notes collection (default: project notes-backup-records)')
    init.add_argument('--photo-root', required=True,
                      help='Project-local photo/video destination root')
    init.add_argument('--name', required=True, help='Observed list display name')
    init.add_argument('--visual-key', required=True,
                      help='Agent-grounded visual identity key')
    init.add_argument('--context-id', help='Optional foreground context identity')
    init.add_argument('--signals',
                      help='Optional strict JSON identity signals or @JSON-file')
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

    scan = sub.add_parser(
        'scan', help='Start, finish, or interrupt a complete list scan')
    add_records(scan, 'Start, finish, or interrupt a complete list scan')
    scan.add_argument('action', choices=('start', 'finish', 'interrupt'))
    scan.add_argument('--session-id', required=True)
    scan.add_argument('--scan-id',
                      help='Required for finish/interrupt; forbidden for start')
    scan.add_argument('--recovery', action='store_true',
                      help='Mark a recovery-evaluation scan (start only)')
    scan.add_argument('--reason',
                      help='Required interruption reason (interrupt only)')
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
    intent.add_argument('--restart-id',
                        help='Confirmed restart batch for this attempt')
    intent.add_argument('--recovery-evidence',
                        help='Required only when recovering a STOPPED/NOT_SENT attempt')

    restart = sub.add_parser(
        'restart', help='Preview, confirm, or resume one restart batch')
    add_records(restart, 'Preview, confirm, or resume one restart batch')
    restart.add_argument('action', choices=('preview', 'confirm', 'resume'))
    restart.add_argument('--session-id',
                         help='Required for confirm/resume')
    restart.add_argument('--preview',
                         help='JSON preview object or @JSON-file for confirm')
    restart.add_argument('--evidence',
                         help='Owner confirmation evidence for confirm')
    restart.add_argument('--decoder', help='Photo ImageIO decoder executable')
    restart.add_argument('--decoder-sha256', help='Expected decoder SHA-256')
    restart.add_argument('--stall-seconds', type=float,
                         default=DEFAULT_STALL_SECONDS,
                         help='Video decode progress watchdog seconds')

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

    evidence_audit = sub.add_parser(
        'evidence-audit', help='Audit saved evidence references without projection')
    add_records(evidence_audit, 'Audit saved evidence references')

    evidence_correct = sub.add_parser(
        'evidence-correct', help='Append one page evidence correction')
    add_records(evidence_correct, 'Append one page evidence correction')
    evidence_correct.add_argument('--session-id', required=True)
    evidence_correct.add_argument('--page-sequence', required=True, type=int)
    evidence_correct.add_argument('--page-sha256', required=True)
    evidence_correct.add_argument('--original-evidence-sha256', required=True)
    evidence_correct.add_argument('--replacement', required=True,
                                  help='Replacement line-notes-evidence/v2 bundle')
    evidence_correct.add_argument('--reason', required=True)
    evidence_correct.add_argument(
        '--previous-correction-ref',
        help='JSON {sequence,sha256} for a repeated correction')

    media_kind_correct = sub.add_parser(
        'media-kind-correct', help='Correct kind before any attempt is dispatched')
    add_records(media_kind_correct, 'Correct kind before dispatch')
    media_kind_correct.add_argument('--session-id', required=True)
    media_kind_correct.add_argument('--media-key', required=True)
    media_kind_correct.add_argument('--inventory-sequence', required=True,
                                    type=int)
    media_kind_correct.add_argument('--inventory-sha256')
    media_kind_correct.add_argument('--to-kind', required=True, type=str.upper,
                                    choices=MEDIA_KINDS)
    media_kind_correct.add_argument('--evidence', required=True)

    source_unavailable = sub.add_parser(
        'source-unavailable', help='Record an explicitly expired media source')
    add_records(source_unavailable, 'Record one expired media source')
    source_unavailable.add_argument('--session-id', required=True)
    source_unavailable.add_argument('--media-key', required=True)
    source_unavailable.add_argument('--attempt-id', required=True)
    source_unavailable.add_argument('--evidence', required=True)

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
        if args.command == 'list-key':
            identity = _list_identity_cli(parser, args)
            result = dict(identity=identity, list_key=list_key(identity))
        elif args.command == 'evidence-pack':
            context = dict(
                list_key=args.list_key, post_key=args.post_key,
                media_key=args.media_key, attempt_id=args.attempt_id,
                scan_id=args.scan_id)
            result = notes_evidence.create_bundle(
                statement=args.statement, assets=args.asset,
                context=context, output_dir=args.output_dir)
        elif args.command == 'lists':
            result = NotesCollection(args.collection).lists()
        elif args.command == 'init':
            identity = _list_identity_cli(parser, args)
            result = NotesCollection(args.collection).create(
                photo_root=args.photo_root,
                display_name=args.name,
                identity=identity,
                binding_evidence=args.binding_evidence,
                history_scope_evidence=args.history_scope_evidence,
                recovery_authorized=args.recovery_authorized)
        elif args.command in ('memory', 'bind', 'scan', 'page', 'post',
                              'media', 'intent', 'outcome', 'reconcile',
                              'verify', 'resume', 'summary', 'evidence-audit',
                              'evidence-correct', 'media-kind-correct',
                              'source-unavailable', 'destination', 'exclude',
                              'protect', 'restart'):
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
                    if args.reason is not None:
                        parser.error('--reason is only accepted for scan interrupt')
                else:
                    if args.scan_id is None:
                        parser.error('--scan-id is required for scan ' + args.action)
                    if args.recovery:
                        parser.error('--recovery is only accepted for scan start')
                    if args.action == 'finish' and args.reason is not None:
                        parser.error('--reason is only accepted for scan interrupt')
                result = records.scan(
                    session_id=args.session_id, action=args.action.upper(),
                    scan_id=args.scan_id, evidence=args.evidence,
                    recovery=args.recovery, reason=args.reason)
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
                    recovery_evidence=args.recovery_evidence,
                    restart_id=args.restart_id)
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
            elif args.command == 'evidence-audit':
                result = records.evidence_audit()
            elif args.command == 'evidence-correct':
                previous = _json_cli_argument(
                    parser, args.previous_correction_ref,
                    '--previous-correction-ref', None)
                result = records.evidence_correct(
                    session_id=args.session_id,
                    page_sequence=args.page_sequence,
                    page_sha256=args.page_sha256,
                    original_evidence_sha256=args.original_evidence_sha256,
                    replacement=args.replacement,
                    reason=args.reason,
                    previous_correction_ref=previous)
            elif args.command == 'media-kind-correct':
                result = records.media_kind_correct(
                    session_id=args.session_id,
                    media_key_value=args.media_key,
                    inventory_sequence=args.inventory_sequence,
                    inventory_sha256=args.inventory_sha256,
                    to_kind=args.to_kind,
                    evidence=args.evidence)
            elif args.command == 'source-unavailable':
                result = records.source_unavailable(
                    session_id=args.session_id,
                    media_key_value=args.media_key,
                    attempt_id=args.attempt_id,
                    evidence=args.evidence)
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
            elif args.command == 'restart':
                if args.action == 'preview':
                    if any(value is not None for value in (
                            args.session_id, args.preview, args.evidence,
                            args.decoder, args.decoder_sha256)):
                        parser.error('restart preview accepts only --records-root')
                    result = records.restart_preview()
                elif args.action == 'confirm':
                    if not args.session_id or args.preview is None or \
                            args.evidence is None:
                        parser.error('restart confirm requires --session-id, '
                                     '--preview, and --evidence')
                    if args.decoder is not None or \
                            args.decoder_sha256 is not None:
                        parser.error('restart confirm does not accept decoder options')
                    preview = _json_cli_argument(parser, args.preview, '--preview')
                    result = records.restart_confirm(
                        session_id=args.session_id, preview=preview,
                        evidence=args.evidence)
                else:
                    if not args.session_id:
                        parser.error('restart resume requires --session-id')
                    if args.preview is not None or args.evidence is not None:
                        parser.error('restart resume does not accept preview/evidence')
                    if bool(args.decoder) != bool(args.decoder_sha256):
                        parser.error('--decoder and --decoder-sha256 must be '
                                     'provided together')
                    stall_seconds = _positive_cli_float(
                        parser, args.stall_seconds, '--stall-seconds')
                    result = records.restart_resume(
                        session_id=args.session_id, decoder=args.decoder,
                        decoder_sha256=args.decoder_sha256,
                        progress_callback=_cli_progress,
                        stall_seconds=stall_seconds)
        else:
            parser.error('unknown command')
        _print_cli_result(result)
        if args.command == 'evidence-audit' and not result['integrity_ok']:
            return 4
        return 0
    except NotesLockBusy as exc:
        read_only = (args.command in READ_ONLY_COMMANDS or
                     (args.command == 'restart' and args.action == 'preview'))
        payload = dict(status='REFUSED', reason='NOTES_LOCK_BUSY',
                       scope=exc.scope, dispatch_authorized=False,
                       retry_safe=read_only)
        print(json.dumps(payload,
                         ensure_ascii=False, separators=(',', ':')))
        return 4
    except (NotesError, NotesEvidenceError, DailyError,
            NotesMediaVerificationError, OSError,
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
