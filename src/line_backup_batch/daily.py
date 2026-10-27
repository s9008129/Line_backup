"""Destination-bound records for the foreground CUA Agent; never grants GUI authority.

The Agent grounds cards and boundary observations. This module checks accounting,
durably reserves attempts and verifies files. It neither finds nor clicks controls.
Historical formal state/grants are deliberately outside its write surface.
"""
import argparse
import contextlib
import ctypes
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
import time
import sys
import unicodedata
import uuid

NORMALIZED_HISTORY_SCHEMA = 'line-backup-daily-history/v1'
MEMORY_SCHEMA = 'line-backup-memory/v1'
NAMING_SCHEMA = 'line-backup-naming/v1'
NAMING_FORMAT = 'GROUPED_V1'
SAFE_COMPONENT_MAX_BYTES = 180
CORE_ROOT = Path(__file__).resolve().parents[2]


try:
    _LIBC = ctypes.CDLL(None, use_errno=True)
    _RENAMEX_NP = _LIBC.renamex_np
    _RENAMEX_NP.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    _RENAMEX_NP.restype = ctypes.c_int
except (AttributeError, OSError):
    _RENAMEX_NP = None

RENAME_EXCL = 0x00000004


class DailyError(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise DailyError(code)


def strict_json(data, code):
    """Read the existing record format without duplicate keys or nonfinite numbers."""
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, code)
            result[key] = value
        return result

    def invalid(_):
        raise DailyError(code)

    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise DailyError(code) from exc


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(',', ':')) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _truncate_utf8(text, limit):
    while len(text.encode('utf-8')) > limit:
        text = text[:-1]
    return text.rstrip(' .')


def safe_component(value):
    """Return one deterministic, display-derived macOS path component."""
    need(isinstance(value, str) and bool(value.strip()), 'NAME_REQUIRES_USER_INPUT')
    text = unicodedata.normalize('NFC', value)
    cleaned = []
    for character in text:
        if character in '/\\:' or character == '\x00' or unicodedata.category(character).startswith('C'):
            cleaned.append(' ')
        else:
            cleaned.append(character)
    text = re.sub(r'\s+', ' ', ''.join(cleaned)).strip(' .')
    text = text.lstrip('. ').rstrip(' .')
    need(bool(text) and text not in ('.', '..'), 'NAME_REQUIRES_USER_INPUT')
    text = _truncate_utf8(text, SAFE_COMPONENT_MAX_BYTES)
    need(bool(text) and text not in ('.', '..'), 'NAME_REQUIRES_USER_INPUT')
    return text


def _suffixed_component(base, suffix):
    need(isinstance(suffix, str), 'INVALID_NAME_SUFFIX')
    available = SAFE_COMPONENT_MAX_BYTES - len(suffix.encode('utf-8'))
    need(available > 0, 'NAME_COMPONENT_TOO_LONG')
    return _truncate_utf8(base, available) + suffix


def _collision_key(name):
    return unicodedata.normalize('NFC', name).casefold()


def allocate_component(parent, base, *, taken=(), reserved=(), replace=None):
    """Allocate a readable component without claiming a name-only identity."""
    base = safe_component(base)
    parent = Path(parent)
    existing = [entry.name for entry in parent.iterdir()
                if parent.exists() and entry.name != replace] if parent.exists() else []
    occupied = {_collision_key(name) for name in [*existing, *taken, *reserved]}
    for number in range(1, 10001):
        candidate = base if number == 1 else _suffixed_component(base, ' (%d)' % number)
        key = _collision_key(candidate)
        if key not in occupied:
            return candidate
    raise DailyError('NAME_ALLOCATION_EXHAUSTED')


def validate_component(value):
    need(isinstance(value, str) and value and Path(value).name == value and
         not value.startswith('.') and safe_component(value) == value,
         'INVALID_NAME_COMPONENT')
    return value


def planned_photo_names(prefix, source_names):
    """Map stable Python-name order to deterministic target names."""
    validate_component(prefix)
    need(isinstance(source_names, list) and source_names and
         all(isinstance(name, str) and Path(name).name == name and not name.startswith('.')
             for name in source_names), 'INVALID_DOWNLOAD_NAMES')
    need(len({_collision_key(name) for name in source_names}) == len(source_names),
         'AMBIGUOUS_DOWNLOAD_NAMES')
    ordered = sorted(source_names)
    width = max(3, len(str(len(ordered))))
    result = []
    targets = set()
    for index, source_name in enumerate(ordered, 1):
        suffix = Path(source_name).suffix
        need(suffix.lower() in ('.jpg', '.jpeg', '.png'), 'UNSUPPORTED_IMAGE_EXTENSION')
        target_name = '%s_%0*d%s' % (prefix, width, index, suffix)
        need(len(target_name.encode('utf-8')) <= 255, 'PHOTO_NAME_TOO_LONG')
        key = _collision_key(target_name)
        need(key not in targets, 'AMBIGUOUS_PHOTO_TARGET_NAMES')
        targets.add(key)
        result.append(dict(index=index, source_name=source_name,
                           target_name=target_name, extension=suffix))
    return result


def directory(value):
    path = Path(value).expanduser().absolute()
    need(path == path.resolve(strict=True) and path.is_dir(), 'CANONICAL_DIRECTORY_REQUIRED')
    return path


def read_file(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'REGULAR_SINGLE_LINK_FILE_REQUIRED')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read()
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'FILE_CHANGED')
        need(os.stat(path, follow_symlinks=False).st_ino == after.st_ino, 'FILE_REPLACED')
        return raw
    finally:
        os.close(fd)


def reference(value):
    path = Path(value).expanduser().absolute()
    need(path == path.resolve(strict=True), 'EVIDENCE_SYMLINK_REFUSED')
    need(path.is_relative_to(CORE_ROOT), 'PROJECT_LOCAL_EVIDENCE_REQUIRED')
    raw = read_file(path)
    need(bool(raw), 'EMPTY_EVIDENCE')
    return dict(path=str(path), bytes=len(raw), sha256=digest(raw))


def check_ref(ref):
    need(isinstance(ref, dict) and reference(ref['path']) == ref, 'EVIDENCE_DRIFT')


def sync_dir(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _entry(path):
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def exclusive_rename(source, target):
    """Atomically rename one regular file or directory without replacing anything."""
    need(_RENAMEX_NP is not None, 'ATOMIC_NO_OVERWRITE_RENAME_UNAVAILABLE')
    source, target = Path(source), Path(target)
    need(source.parent == target.parent or source.is_dir() and target.parent.is_dir(),
         'UNSUPPORTED_RENAME_PARENTS')
    before = _entry(source)
    need(before is not None and stat.S_ISREG(before.st_mode) or
         before is not None and stat.S_ISDIR(before.st_mode), 'SAFE_SOURCE_REQUIRED')
    need(_entry(target) is None, 'TARGET_ALREADY_EXISTS')
    need(directory(source.parent) == source.parent and directory(target.parent) == target.parent,
         'CANONICAL_RENAME_PARENT_REQUIRED')
    result = _RENAMEX_NP(os.fsencode(source), os.fsencode(target), RENAME_EXCL)
    if result:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise DailyError('TARGET_ALREADY_EXISTS')
        raise OSError(code, os.strerror(code), str(source))
    after = _entry(target)
    need(after is not None and
         (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode)) ==
         (before.st_dev, before.st_ino, stat.S_IFMT(before.st_mode)),
         'RENAME_BINDING_CHANGED')
    need(_entry(source) is None, 'SOURCE_REMAINS_AFTER_RENAME')
    sync_dir(source.parent)
    if source.parent != target.parent:
        sync_dir(target.parent)
    return before


def create_json(path, value):
    """Publish complete bytes exclusively; a failed write never replaces old data."""
    temporary = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        raw = encoded(value)
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(str(temporary), str(path), follow_symlinks=False)
    finally:
        os.close(fd)
    temporary.unlink()
    sync_dir(path.parent)
    need(read_file(path) == raw, 'RECORD_READBACK_FAILED')


def album_key(identity):
    need(isinstance(identity, dict) and set(identity) ==
         {'start_date', 'end_date', 'expected_images', 'visual_key'}, 'ALBUM_IDENTITY_REQUIRED')
    need(type(identity['expected_images']) is int and identity['expected_images'] > 0,
         'PHOTO_COUNT_REQUIRED')
    for name in ('start_date', 'end_date', 'visual_key'):
        need(isinstance(identity[name], str) and bool(identity[name].strip()), 'VISUAL_IDENTITY_REQUIRED')
    # visual_key is a persisted Agent-grounded disambiguator, not Chinese OCR.
    return digest(encoded(identity))


def boundary_reference(path, edge, session_id, key, screenshot, previous_screenshot=None):
    ref = reference(path)
    observation = strict_json(read_file(path), 'INVALID_BOUNDARY_OBSERVATION')
    need(observation.get('edge') == edge and observation.get('session_id') == session_id and
         observation.get('edge_key') == key, 'BOUNDARY_CONTEXT_MISMATCH')
    before, after = observation.get('before_offset'), observation.get('after_offset')
    need(type(before) in (int, float) and type(after) in (int, float) and
         math.isfinite(before) and math.isfinite(after) and before >= 0 and before == after,
         'BOUNDARY_MOVEMENT_OBSERVED')
    if edge == 'top':
        need(after == 0, 'TOP_NOT_REACHED')
    for name in ('before_screenshot', 'after_screenshot', 'input_receipt'):
        check_ref(observation[name])
    need(observation['after_screenshot'] == screenshot, 'BOUNDARY_FRAME_MISMATCH')
    if previous_screenshot is not None:
        need(observation['before_screenshot'] == previous_screenshot, 'BOUNDARY_BEFORE_FRAME_MISMATCH')
    return ref


class DailyRecords:
    def __init__(self, root):
        self.root = directory(root)
        need(self.root.is_relative_to(CORE_ROOT), 'PROJECT_LOCAL_ROOT_REQUIRED')
        self.records = self.root / 'backup-records'

    def initialize(self, *, binding_evidence, history_scope_evidence, context_id=None):
        """Only after current foreground handoff and history-scope inspection.

        context_id is an optional reliable opaque LINE id. An OCR title is not one.
        Evidence is an observation/Owner source reference, never manufactured consent.
        """
        binding = reference(binding_evidence)
        history = reference(history_scope_evidence)
        need(context_id is None or isinstance(context_id, str) and bool(context_id), 'INVALID_CONTEXT_ID')
        need(not self.records.exists() and not self.records.is_symlink(), 'RECORDS_ALREADY_EXIST')
        self.records.mkdir(mode=0o700)
        (self.records / 'events').mkdir(mode=0o700)
        identity = self.root.stat()
        group = dict(version=1, local_group_id=str(uuid.uuid4()), destination=str(self.root),
                     destination_device=identity.st_dev, destination_inode=identity.st_ino,
                     context_id=context_id, binding_evidence=binding, history_scope_evidence=history,
                     recovery_strategy='ALBUM_LEVEL', photo_level_resume='FUTURE_RESEARCH')
        create_json(self.records / 'group.json', group)
        sync_dir(self.root)
        return group

    @contextlib.contextmanager
    def locked(self):
        directory(self.root)
        need(directory(self.records) == self.records, 'RECORD_DIRECTORY_CHANGED')
        need(directory(self.records / 'events') == self.records / 'events', 'EVENT_DIRECTORY_CHANGED')
        fd = os.open(str(self.records / '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            need(stat.S_ISREG(os.fstat(fd).st_mode) and os.fstat(fd).st_nlink == 1, 'UNSAFE_LOCK')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.group = strict_json(read_file(self.records / 'group.json'), 'INVALID_GROUP_RECORD')
            identity = self.root.stat()
            need(self.group['destination'] == str(self.root) and
                 self.group['destination_device'] == identity.st_dev and
                 self.group['destination_inode'] == identity.st_ino, 'DESTINATION_BINDING_CHANGED')
            self.events = []
            memory_hashes = {}
            previous = None
            for index, path in enumerate(sorted((self.records / 'events').iterdir()), 1):
                need(path.name == '%08d.json' % index, 'EVENT_SEQUENCE_OR_PENDING_WRITE')
                raw = read_file(path)
                event = strict_json(raw, 'INVALID_EVENT')
                need(event['sequence'] == index and event['previous_sha256'] == previous and
                     event['local_group_id'] == self.group['local_group_id'], 'EVENT_BINDING_CHANGED')
                self.events.append(event)
                if event['kind'] == 'memory' or (event['kind'] == 'history' and
                                                'memory_schema' in event['data']):
                    memory_hashes[path.name] = digest(raw)
                previous = digest(raw)
            self.previous = previous
            anchors = self.records / 'memory-anchors'
            if memory_hashes or anchors.exists() or anchors.is_symlink():
                need(anchors.exists() and directory(anchors) == anchors, 'MEMORY_ANCHOR_REQUIRED')
                need(sorted(p.name for p in anchors.iterdir()) == sorted(memory_hashes),
                     'MEMORY_ANCHOR_SET_CHANGED')
                for name, expected in memory_hashes.items():
                    anchor = strict_json(read_file(anchors / name), 'INVALID_MEMORY_ANCHOR')
                    need(anchor == dict(schema=MEMORY_SCHEMA, event_sha256=expected), 'MEMORY_DIGEST_CHANGED')
            yield
        finally:
            os.close(fd)

    def append(self, kind, data):
        event = dict(sequence=len(self.events) + 1, previous_sha256=self.previous,
                     local_group_id=self.group['local_group_id'], kind=kind, data=data)
        create_json(self.records / 'events' / ('%08d.json' % event['sequence']), event)
        self.events.append(event)
        self.previous = digest(encoded(event))
        if kind == 'memory' or kind == 'history' and 'memory_schema' in data:
            anchors = self.records / 'memory-anchors'
            if not anchors.exists():
                anchors.mkdir(mode=0o700)
                sync_dir(self.records)
            create_json(anchors / ('%08d.json' % event['sequence']),
                        dict(schema=MEMORY_SCHEMA, event_sha256=self.previous))
        return data

    def matching(self, kind):
        return [e['data'] for e in self.events if e['kind'] == kind]

    def bound(self, session_id):
        bindings = self.matching('binding')
        need(bindings and bindings[-1]['session_id'] == session_id, 'FRESH_FOREGROUND_BINDING_REQUIRED')
        for ref in bindings[-1]['evidence'].values():
            check_ref(ref)

    def bind(self, *, session_id, local_group_id, observation, handoff, context_id=None):
        with self.locked():
            need(local_group_id == self.group['local_group_id'], 'WRONG_LOCAL_GROUP')
            need(context_id == self.group['context_id'], 'WRONG_CONTEXT')
            need(isinstance(session_id, str) and bool(session_id), 'SESSION_REQUIRED')
            return self.append('binding', dict(session_id=session_id,
                evidence=dict(observation=reference(observation), handoff=reference(handoff))))

    def _validate_group_name_data(self, data):
        need(isinstance(data, dict) and data.get('schema') == NAMING_SCHEMA and
             data.get('local_group_id') == self.group['local_group_id'] and
             isinstance(data.get('display_name'), str) and bool(data['display_name'].strip()) and
             data.get('action') in ('CAPTURE', 'CORRECT') and
             type(data.get('directory_device')) is int and type(data.get('directory_inode')) is int,
             'INVALID_GROUP_NAME_EVENT')
        validate_component(data.get('path_name'))
        need(isinstance(data.get('source'), dict), 'INVALID_GROUP_NAME_EVENT')
        if data['action'] == 'CORRECT':
            need(isinstance(data.get('plan_id'), str) and isinstance(data.get('correction'), dict),
                 'INVALID_GROUP_CORRECTION_EVENT')
        return data

    def _validate_album_name_data(self, data):
        need(isinstance(data, dict) and data.get('schema') == NAMING_SCHEMA and
             data.get('action') in ('CAPTURE', 'CORRECT') and
             isinstance(data.get('album_key'), str) and isinstance(data.get('identity'), dict) and
             album_key(data['identity']) == data['album_key'] and
             isinstance(data.get('display_name'), str) and bool(data['display_name'].strip()) and
             isinstance(data.get('source'), dict), 'INVALID_ALBUM_NAME_EVENT')
        validate_component(data.get('path_name'))
        if data['action'] == 'CORRECT':
            need(isinstance(data.get('plan_id'), str) and isinstance(data.get('correction'), dict),
                 'INVALID_ALBUM_CORRECTION_EVENT')
        return data

    def _group_name_event(self):
        events = [(event, event['data']) for event in self.events if event['kind'] == 'group-name']
        for _, data in events:
            self._validate_group_name_data(data)
        return events[-1] if events else None

    def _album_name_event(self, key):
        events = [(event, event['data']) for event in self.events if event['kind'] == 'album-name'
                  and event['data'].get('album_key') == key]
        for _, data in events:
            self._validate_album_name_data(data)
        return events[-1] if events else None

    def _group_directory(self, data):
        path = self.root / validate_component(data['path_name'])
        need(directory(path) == path and path.stat().st_dev == data['directory_device'] and
             path.stat().st_ino == data['directory_inode'], 'GROUP_DIRECTORY_BINDING_CHANGED')
        return path

    def capture_group_name(self, *, session_id, name, source):
        """Persist an Agent-observed display name; it is never identity evidence."""
        name_ref = reference(source)
        with self.locked():
            self.bound(session_id)
            existing = self._group_name_event()
            if existing:
                existing = existing[1]
                need(existing['display_name'] == name, 'GROUP_NAME_ALREADY_CAPTURED_USE_CORRECTION')
                self._group_directory(existing)
                return existing
            need(isinstance(name, str) and bool(name.strip()), 'NAME_REQUIRES_USER_INPUT')
            component = allocate_component(self.root, safe_component(name), reserved=('backup-records', 'albums'))
            group_path = self.root / component
            group_path.mkdir(mode=0o700)
            info = group_path.stat()
            data = dict(schema=NAMING_SCHEMA, action='CAPTURE', local_group_id=self.group['local_group_id'],
                        display_name=name, path_name=component, source=name_ref,
                        directory_device=info.st_dev, directory_inode=info.st_ino)
            return self.append('group-name', data)

    def capture_album_name(self, *, session_id, identity, name, source):
        """Persist a display name separately from visual album identity."""
        name_ref = reference(source)
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            current_keys = {item for page in self.pages() for item in page['keys']}
            need(key in current_keys, 'TARGET_NOT_IN_CURRENT_SCAN')
            existing = self._album_name_event(key)
            if existing:
                existing = existing[1]
                need(existing['display_name'] == name, 'ALBUM_NAME_ALREADY_CAPTURED_USE_CORRECTION')
                return existing
            group_event = self._group_name_event()
            need(group_event, 'GROUP_NAME_REQUIRED')
            group_dir = self._group_directory(group_event[1])
            taken = [event['data']['path_name'] for event in self.events
                     if event['kind'] == 'album-name' and event['data'].get('album_key') != key]
            component = allocate_component(group_dir, safe_component(name), taken=taken)
            data = dict(schema=NAMING_SCHEMA, action='CAPTURE', album_key=key, identity=identity,
                        display_name=name, path_name=component, source=name_ref)
            return self.append('album-name', data)

    def history(self, *, session_id, scope_evidence, entries):
        """Import explicitly group-mapped barriers; no implicit date/count match.

        Assess sources once and persist the decision and necessary facts inline.
        Source digests are provenance, never runtime file dependencies.
        """
        with self.locked():
            self.bound(session_id)
            need(not self.matching('history'), 'HISTORY_ALREADY_RECONCILED')
            result = []
            for entry in entries:
                key = album_key(entry['identity'])
                need(entry['local_group_id'] == self.group['local_group_id'], 'CROSS_GROUP_HISTORY_REFUSED')
                need(entry['status'] in ('COMPLETED', 'EXCLUDED', 'UNKNOWN', 'PROTECTED_HISTORY'),
                     'INVALID_HISTORY_STATUS')
                need(key not in [r['album_key'] for r in result], 'AMBIGUOUS_HISTORY')
                result.append(self._freeze_history_entry(dict(entry, album_key=key,
                    declared_status=entry['status'], source=reference(entry['source']))))
            scope = reference(scope_evidence)
            return self.append('history', dict(memory_schema=MEMORY_SCHEMA,
                scope_digest=dict(bytes=scope['bytes'], sha256=scope['sha256']), entries=result))

    def _freeze_history_entry(self, entry):
        """Snapshot assessed facts, retaining unknowns and never upgrading old barriers."""
        status = entry['status']
        source = entry['source']
        result = dict(album_key=entry['album_key'], identity=entry['identity'],
                      declared_status=entry.get('declared_status', status),
                      source_digest=dict(bytes=source['bytes'], sha256=source['sha256']))
        if status in ('UNKNOWN', 'PROTECTED_HISTORY'):
            return dict(result, status=status, assessment='PRESERVED_BARRIER')
        try:
            check_ref(source)
            supported = self._normalized_history(source['path'], entry['identity'])
            if supported != status:
                return dict(result, status='PROTECTED_HISTORY', assessment='INSUFFICIENT_IDENTITY_OR_PROOF')
            document = strict_json(read_file(source['path']), 'INVALID_HISTORY_SOURCE')
            if status == 'COMPLETED':
                proof = document['photo_verification']
                result['photo_verification'] = dict(expected_images=proof['expected_images'],
                    manifest=strict_json(read_file(proof['manifest_evidence']['path']), 'INVALID_MANIFEST'),
                    imageio=strict_json(read_file(proof['imageio_evidence']['path']), 'INVALID_IMAGEIO'))
                for ref in (source, proof['manifest_evidence'], proof['imageio_evidence']):
                    check_ref(ref)
            else:
                exclusion = strict_json(read_file(document['exclusion_evidence']['path']), 'INVALID_EXCLUSION')
                result['exclusion'] = dict(decision=exclusion['decision'],
                    owner_source_digest={k: exclusion['owner_source'][k] for k in ('bytes', 'sha256')})
                check_ref(document['exclusion_evidence'])
                check_ref(exclusion['owner_source'])
                check_ref(source)
            return dict(result, status=status, assessment='VALIDATED_AT_IMPORT')
        except (DailyError, OSError, ValueError, KeyError, TypeError):
            return dict(result, status='PROTECTED_HISTORY', assessment='SOURCE_UNAVAILABLE_OR_CHANGED')

    def _validate_legacy_albums(self, legacy_albums):
        need(isinstance(legacy_albums, list), 'INVALID_LEGACY_ALBUMS')
        seen = set()
        for album in legacy_albums:
            need(isinstance(album, dict) and isinstance(album.get('id'), str) and
                 album['id'] and album['id'] not in seen, 'AMBIGUOUS_LEGACY_ALBUM')
            seen.add(album['id'])
            need(album.get('local_group_id') in (None, self.group['local_group_id']), 'CROSS_GROUP_HISTORY_REFUSED')
            need(album.get('status') in ('UNKNOWN', 'PROTECTED_HISTORY'), 'LEGACY_CLAIM_CANNOT_COMPLETE')
            hint = album.get('identity_hint', {})
            need(isinstance(hint, dict) and set(hint) == {'start_date', 'end_date', 'expected_images'} and
                 type(hint['expected_images']) is int and hint['expected_images'] > 0 and
                 all(isinstance(hint[k], str) and hint[k].strip() for k in ('start_date', 'end_date')),
                 'LEGACY_IDENTITY_HINT_REQUIRED')
            need(isinstance(album.get('reason'), str) and bool(album['reason'].strip()),
                 'LEGACY_PROTECTION_REASON_REQUIRED')

    def import_memory(self, *, local_group_id, legacy_albums, coverage, provenance):
        """One-time local data migration. No foreground binding or GUI authority."""
        with self.locked():
            need(local_group_id == self.group['local_group_id'], 'WRONG_LOCAL_GROUP')
            need(not self.matching('memory'), 'MEMORY_ALREADY_IMPORTED')
            need(self.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
            need(isinstance(coverage, str) and bool(coverage.strip()), 'MEMORY_COVERAGE_REQUIRED')
            need(isinstance(provenance, list), 'MEMORY_PROVENANCE_REQUIRED')
            self._validate_legacy_albums(legacy_albums)
            history = []
            for event in self.matching('history'):
                history.extend(event['entries'] if event.get('memory_schema') == MEMORY_SCHEMA else
                               [self._freeze_history_entry(e) for e in event['entries']])
            return self.append('memory', dict(schema=MEMORY_SCHEMA, history=history,
                legacy_albums=legacy_albums, coverage=coverage, provenance=provenance))

    def memory(self):
        """Read-only structured view; events remain the sole mutable source of truth."""
        with self.locked():
            states = self.status_map()
            projection = self._naming_projection()
            identities = {}
            for event in self.events:
                data = event['data']
                if event['kind'] == 'history':
                    identities.update((e['album_key'], e['identity']) for e in data['entries'])
                elif event['kind'] == 'page':
                    identities.update(zip(data['keys'], data['cards']))
                elif event['kind'] == 'album-name':
                    identities[data['album_key']] = data['identity']
            snapshots = self.matching('memory')
            albums = []
            for key, status in states.items():
                completion_events = [event for event in self.events if event['kind'] == 'completion' and
                                     event['data']['album_key'] == key]
                completions = []
                current_destination = None
                for event in completion_events:
                    effective = self._effective_completion(event, projection)
                    current_destination = effective['destination']
                    completions.append(dict(event['data'], current_destination=effective['destination']))
                name_data = projection['albums'].get(key)
                albums.append(dict(album_key=key, identity=identities[key], status=status,
                    display_name=name_data['display_name'] if name_data else None,
                    path_name=name_data['path_name'] if name_data else None,
                    current_destination=current_destination,
                    attempts=[i for i in self.matching('intent') if i['album_key'] == key],
                    completions=completions))
            group_data = projection['group']
            return dict(schema=MEMORY_SCHEMA, local_group_id=self.group['local_group_id'],
                group=dict(local_group_id=self.group['local_group_id'],
                    display_name=group_data['display_name'] if group_data else None,
                    path_name=group_data['path_name'] if group_data else None,
                    current_path=str(self.root / group_data['path_name']) if group_data else None),
                naming_schema=NAMING_SCHEMA, albums=albums,
                legacy_albums=snapshots[0]['legacy_albums'] if snapshots else [],
                coverage=snapshots[0]['coverage'] if snapshots else 'CURRENT_RECORDS_ONLY',
                history=snapshots[0]['history'] if snapshots else
                    [e for h in self.matching('history') for e in h['entries']])

    def _normalized_history(self, source_path, identity):
        """Return a supported normalized status; preserve every other legacy source.

        Normalization verifies the stated local group and full album identity, and,
        for a completion, the manifest and ImageIO evidence files. It does not turn
        historical provenance into a fresh download or formal verification.
        """
        try:
            document = json.loads(read_file(source_path))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(document, dict) or document.get('schema') != NORMALIZED_HISTORY_SCHEMA:
            return None
        if (document.get('local_group_id') != self.group['local_group_id'] or
                document.get('identity') != identity or
                document.get('album_key') != album_key(identity)):
            return None
        status = document.get('status')
        if status == 'EXCLUDED':
            try:
                exclusion_ref = document['exclusion_evidence']
                check_ref(exclusion_ref)
                exclusion = json.loads(read_file(exclusion_ref['path']))
                if (not isinstance(exclusion, dict) or
                        exclusion.get('schema') != 'line-backup-exclusion/v1' or
                        exclusion.get('local_group_id') != self.group['local_group_id'] or
                        exclusion.get('identity') != identity or
                        exclusion.get('album_key') != album_key(identity) or
                        exclusion.get('decision') != 'EXCLUDE_ALBUM'):
                    return None
                check_ref(exclusion['owner_source'])
            except (KeyError, DailyError, OSError, ValueError, TypeError):
                return None
            return status
        if status != 'COMPLETED':
            return None
        try:
            proof = document['photo_verification']
            expected = identity['expected_images']
            if proof['expected_images'] != expected:
                return None
            manifest_ref = proof['manifest_evidence']
            imageio_ref = proof['imageio_evidence']
            check_ref(manifest_ref)
            check_ref(imageio_ref)
            manifest_doc = json.loads(read_file(manifest_ref['path']))
            imageio = json.loads(read_file(imageio_ref['path']))
            manifest = manifest_doc['manifest']
            if (manifest_doc.get('manifest_sha256') != digest(encoded(manifest)) or
                    proof.get('manifest_sha256') != manifest_doc['manifest_sha256'] or
                    not isinstance(manifest, list) or len(manifest) != expected):
                return None
            names = set()
            for row in manifest:
                name = row['name']
                if (not isinstance(name, str) or not name or Path(name).name != name or
                        name.startswith('.') or name in names or type(row['size']) is not int or
                        row['size'] <= 0 or not isinstance(row['sha256'], str) or
                        len(row['sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['sha256'])):
                    return None
                names.add(name)
            decoded = imageio.get('entries')
            if (imageio.get('verdict') != 'PASS' or imageio.get('readOnly') is not True or
                    imageio.get('expected') != expected or imageio.get('actualEntries') != expected or
                    not isinstance(decoded, list) or len(decoded) != expected):
                return None
            decoded_by_name = {}
            for row in decoded:
                if row.get('decoded') is not True or row.get('name') in decoded_by_name:
                    return None
                decoded_by_name[row['name']] = row.get('sha256')
            if decoded_by_name != {row['name']: row['sha256'] for row in manifest}:
                return None
            return status
        except (AttributeError, KeyError, DailyError, OSError, ValueError, TypeError):
            return None

    def start_scan(self, *, session_id):
        with self.locked():
            self.bound(session_id)
            need(self.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
            return self.append('scan', dict(scan_id=str(uuid.uuid4()), session_id=session_id))

    def pages(self):
        scans = self.matching('scan')
        return [p for p in self.matching('page') if scans and p['scan_id'] == scans[-1]['scan_id']]

    def page(self, *, session_id, cards, screenshot, ax, boundary_evidence=None,
             top_confirmed=False, bottom_stationary=False, scroll_evidence=None, unresolved=0):
        with self.locked():
            self.bound(session_id)
            scans = self.matching('scan')
            need(scans and scans[-1]['session_id'] == session_id, 'NEW_SCAN_REQUIRED_AFTER_HANDOFF')
            need(type(unresolved) is int and unresolved >= 0, 'INVALID_UNRESOLVED_COUNT')
            need(isinstance(cards, list) and cards, 'NO_GROUNDED_CARDS')
            keys = [album_key(card) for card in cards]
            need(len(keys) == len(set(keys)), 'AMBIGUOUS_SAME_PAGE_CARDS')
            pages = self.pages()
            evidence = dict(screenshot=reference(screenshot), ax=reference(ax))
            if not pages:
                need(top_confirmed is True and boundary_evidence, 'TOP_BOUNDARY_REQUIRED')
                evidence['boundary'] = boundary_reference(boundary_evidence, 'top', session_id,
                                                           keys[0], evidence['screenshot'])
                need(not bottom_stationary, 'SEPARATE_BOTTOM_OBSERVATION_REQUIRED')
            else:
                need(not pages[-1]['bottom_stationary'], 'SCAN_ALREADY_AT_BOTTOM')
                previous = pages[-1]['keys']
                need(scroll_evidence, 'SCROLL_OBSERVATION_REQUIRED')
                evidence['scroll'] = reference(scroll_evidence)
                need(evidence['screenshot'] != pages[-1]['evidence']['screenshot'], 'FRESH_OBSERVATION_REQUIRED')
                # The overlapping suffix/prefix must preserve order. A mere set
                # intersection cannot prove that no rows were skipped.
                overlap = max((n for n in range(1, min(len(previous), len(keys)) + 1)
                               if previous[-n:] == keys[:n]), default=0)
                need(overlap > 0, 'LIST_OVERLAP_GAP')
                seen = {key for p in pages for key in p['keys']}
                need(not (set(keys[overlap:]) & seen), 'LIST_REORDER_OR_LOOP')
                if bottom_stationary:
                    need(previous == keys and unresolved == 0 and boundary_evidence,
                         'BOTTOM_NOT_STATIONARY')
                    evidence['boundary'] = boundary_reference(boundary_evidence, 'bottom', session_id,
                        keys[-1], evidence['screenshot'], pages[-1]['evidence']['screenshot'])
                else:
                    need(previous != keys, 'NO_MOVEMENT_IS_NOT_A_NEW_PAGE')
            return self.append('page', dict(scan_id=scans[-1]['scan_id'], cards=cards, keys=keys,
                unresolved=unresolved, bottom_stationary=bottom_stationary, evidence=evidence))

    def _validate_proof(self, proof, expected):
        need(isinstance(proof, dict) and isinstance(proof.get('manifest'), list) and
             len(proof['manifest']) == expected and isinstance(proof.get('imageio'), dict) and
             proof['imageio'].get('verdict') == 'PASS' and proof['imageio'].get('readOnly') is True,
             'INVALID_COMPLETION_PROOF')
        need(proof.get('manifest_sha256') == digest(encoded(proof['manifest'])),
             'INVALID_COMPLETION_PROOF')
        names = set()
        for row in proof['manifest']:
            need(isinstance(row, dict) and isinstance(row.get('name'), str) and
                 Path(row['name']).name == row['name'] and not row['name'].startswith('.') and
                 type(row.get('size')) is int and row['size'] > 0 and
                 isinstance(row.get('sha256'), str) and len(row['sha256']) == 64 and
                 type(row.get('mtime_ns')) is int and type(row.get('ctime_ns')) is int and
                 row['name'] not in names, 'INVALID_COMPLETION_PROOF')
            names.add(row['name'])
        return proof

    def _completion_by_sequence(self, sequence):
        rows = [event for event in self.events if event['sequence'] == sequence and event['kind'] == 'completion']
        need(len(rows) == 1, 'CORRECTION_COMPLETION_REFERENCE_CHANGED')
        return rows[0]

    def _naming_projection(self):
        group_view = None
        album_views = {}
        pending = {}
        completion_overrides = {}
        protected = set()
        for event in self.events:
            kind, data = event['kind'], event['data']
            if kind == 'group-name':
                self._validate_group_name_data(data)
                if data['action'] == 'CORRECT':
                    plan = pending.get(data['plan_id'])
                    need(plan is not None and plan['kind'] == 'GROUP_CORRECTION' and
                         plan['new_group_display_name'] == data['display_name'] and
                         plan['new_group_path_name'] == data['path_name'],
                         'GROUP_CORRECTION_CHAIN_CHANGED')
                    correction = data['correction']
                    need(isinstance(correction.get('albums'), list) and
                         len(correction['albums']) == len(plan['albums']), 'GROUP_CORRECTION_CHAIN_CHANGED')
                    planned = {row['completion_sequence']: row for row in plan['albums']}
                    seen = set()
                    for row in correction['albums']:
                        sequence = row.get('completion_sequence')
                        need(sequence in planned and sequence not in seen, 'GROUP_CORRECTION_CHAIN_CHANGED')
                        seen.add(sequence)
                        completion = self._completion_by_sequence(sequence)
                        need(completion['data']['album_key'] == planned[sequence]['album_key'] and
                             Path(row['destination']).parent == self.root / data['path_name'] and
                             Path(row['destination']).name == planned[sequence]['directory_name'],
                             'GROUP_CORRECTION_CHAIN_CHANGED')
                        self._validate_proof(row.get('proof'),
                            completion['data']['identity']['expected_images']
                            if 'identity' in completion['data'] else
                            len(completion['data']['proof']['manifest']))
                        completion_overrides[sequence] = dict(album_key=completion['data']['album_key'],
                            destination=row['destination'], proof=row['proof'])
                    pending.pop(data['plan_id'])
                group_view = data
            elif kind == 'album-name':
                self._validate_album_name_data(data)
                if data['action'] == 'CORRECT':
                    plan = pending.get(data['plan_id'])
                    need(plan is not None and plan['kind'] == 'ALBUM_CORRECTION' and
                         plan['album_key'] == data['album_key'] and
                         plan['new_album_display_name'] == data['display_name'] and
                         plan['new_album_path_name'] == data['path_name'],
                         'ALBUM_CORRECTION_CHAIN_CHANGED')
                    correction = data['correction']
                    need(isinstance(correction.get('albums'), list) and len(correction['albums']) == 1,
                         'ALBUM_CORRECTION_CHAIN_CHANGED')
                    row = correction['albums'][0]
                    completion = self._completion_by_sequence(plan['completion_sequence'])
                    need(row.get('completion_sequence') == plan['completion_sequence'] and
                         completion['data']['album_key'] == data['album_key'] and
                         row.get('destination') == plan['new_destination'],
                         'ALBUM_CORRECTION_CHAIN_CHANGED')
                    expected = len(completion['data']['proof']['manifest'])
                    self._validate_proof(row.get('proof'), expected)
                    completion_overrides[plan['completion_sequence']] = dict(album_key=data['album_key'],
                        destination=row['destination'], proof=row['proof'])
                    pending.pop(data['plan_id'])
                album_views[data['album_key']] = data
            elif kind == 'name-correction-plan':
                need(data.get('schema') == NAMING_SCHEMA and
                     data.get('kind') in ('GROUP_CORRECTION', 'ALBUM_CORRECTION') and
                     isinstance(data.get('transaction_id'), str) and data['transaction_id'] not in pending,
                     'INVALID_NAMING_CORRECTION_PLAN')
                self._validate_correction_plan(data)
                pending[data['transaction_id']] = data
        for plan in pending.values():
            rows = plan.get('albums', [])
            if plan.get('kind') == 'ALBUM_CORRECTION':
                rows = [plan]
            for row in rows:
                sequence = row.get('completion_sequence')
                if sequence is not None:
                    completion = self._completion_by_sequence(sequence)
                    protected.add(completion['data']['album_key'])
        return dict(group=group_view, albums=album_views, pending=pending,
                    completion_overrides=completion_overrides, protected=protected)

    def _check_completion_files(self, destination, proof, code='COMPLETED_FILES_CHANGED_NO_REDOWNLOAD'):
        destination = Path(destination)
        need(directory(destination) == destination, code)
        for row in proof['manifest']:
            path = destination / row['name']
            need(path.exists() and not path.is_symlink(), code)
            info = path.stat()
            need(stat.S_ISREG(info.st_mode) and info.st_size == row['size'] and
                 info.st_mtime_ns == row['mtime_ns'] and info.st_ctime_ns == row['ctime_ns'],
                 code)
            need(digest(read_file(path)) == row['sha256'], code)
        need(sorted(p.name for p in destination.iterdir()) ==
             [row['name'] for row in proof['manifest']], code)

    def status_map(self):
        if not hasattr(self, 'events'):
            with self.locked():
                return self.status_map()
        result = {}
        projection = self._naming_projection()
        snapshots = self.matching('memory')
        need(len(snapshots) <= 1, 'AMBIGUOUS_MEMORY')
        if snapshots:
            need(snapshots[0]['schema'] == MEMORY_SCHEMA, 'UNSUPPORTED_MEMORY_SCHEMA')
            self._validate_legacy_albums(snapshots[0]['legacy_albums'])
            result.update((e['album_key'], e['status']) for e in snapshots[0]['history'])
        for event in self.events:
            data = event['data']
            if event['kind'] == 'history':
                if not snapshots:
                    need(data.get('memory_schema') == MEMORY_SCHEMA or not data['entries'],
                         'MEMORY_MIGRATION_REQUIRED')
                    result.update((e['album_key'], e['status']) for e in data['entries'])
            elif event['kind'] == 'page':
                for key in data['keys']:
                    result.setdefault(key, 'INCOMPLETE')
            elif event['kind'] == 'intent':
                result[data['album_key']] = 'UNKNOWN'
            elif event['kind'] == 'outcome':
                result[data['album_key']] = 'UNKNOWN' if data['outcome'] == 'UNKNOWN' else 'INCOMPLETE'
            elif event['kind'] == 'completion':
                result[data['album_key']] = 'COMPLETED'
        for event in self.events:
            if event['kind'] != 'completion':
                continue
            data = event['data']
            if data['album_key'] in projection['protected']:
                result[data['album_key']] = 'PROTECTED_HISTORY'
                continue
            if result.get(data['album_key']) != 'COMPLETED':
                continue
            projected = projection['completion_overrides'].get(event['sequence'])
            destination = projected['destination'] if projected else data['destination']
            proof = projected['proof'] if projected else data['proof']
            if not projection['pending']:
                self._assert_album_attempts_safe(data['album_key'], data['attempt_id'])
                if (isinstance(data.get('naming'), dict) and
                        data['naming'].get('schema') == NAMING_SCHEMA):
                    self._assert_completion_directory_identity(event, Path(destination))
            self._check_completion_files(destination, proof)
        # A legacy hint only raises an ambiguity barrier. It never assigns an
        # album to a group or supersedes real completion/dispatch events.
        if snapshots:
            identities = {key: card for page in self.matching('page')
                          for key, card in zip(page['keys'], page['cards'])}
            for key, identity in identities.items():
                if result.get(key) != 'INCOMPLETE':
                    continue
                for album in snapshots[0]['legacy_albums']:
                    hint = album['identity_hint']
                    if (identity['start_date'], identity['end_date']) == (hint['start_date'], hint['end_date']):
                        result[key] = 'PROTECTED_HISTORY'
                        break
        return result

    def detail(self, *, session_id, identity, evidence):
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            need(key in {k for p in self.pages() for k in p['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
            return self.append('detail', dict(session_id=session_id, album_key=key,
                                              evidence=reference(evidence)))

    def intent(self, *, session_id, identity, recovery_authorization=None):
        """Local reservation only. Caller must also pass real transaction gates.

        RESERVED immediately means UNKNOWN until a separately observed outcome.
        A crash between this durable write and GUI input cannot allow replay.
        """
        with self.locked():
            self.bound(session_id)
            key = album_key(identity)
            need(not self._naming_projection()['pending'], 'PENDING_NAMING_TRANSACTION')
            states = self.status_map()
            need(states.get(key) != 'PROTECTED_HISTORY', 'PROTECTED_NO_REDOWNLOAD')
            need(states.get(key) not in ('COMPLETED', 'EXCLUDED'), 'COMPLETED_OR_EXCLUDED_NO_REDOWNLOAD')
            need(key in {k for p in self.pages() for k in p['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
            attempts = self.matching('intent')
            if attempts and attempts[-1]['album_key'] != key:
                need(states[attempts[-1]['album_key']] == 'COMPLETED', 'PENDING_OTHER_ALBUM_NO_DISPATCH')
            need(self.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
            details = self.matching('detail')
            need(details and details[-1]['session_id'] == session_id and details[-1]['album_key'] == key,
                 'FRESH_DETAIL_REQUIRED')
            check_ref(details[-1]['evidence'])
            prior = [i for i in self.matching('intent') if i['album_key'] == key]
            need(states.get(key) != 'UNKNOWN' or prior, 'UNKNOWN_OR_RUNNING_NO_REPLAY')
            recovery = None
            if prior:
                outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == prior[-1]['attempt_id']]
                need(outcomes and outcomes[-1]['outcome'] in ('STOPPED', 'NOT_SENT'), 'UNKNOWN_OR_RUNNING_NO_REPLAY')
                check_ref(outcomes[-1]['evidence'])
                need(recovery_authorization, 'ALBUM_RECOVERY_AUTHORIZATION_REQUIRED')
                recovery = reference(recovery_authorization)
                decision = strict_json(read_file(recovery_authorization), 'INVALID_RECOVERY_AUTHORIZATION')
                need(decision.get('decision') == 'AUTHORIZE_ALBUM_RECOVERY' and
                     decision.get('local_group_id') == self.group['local_group_id'] and
                     decision.get('album_key') == key and
                     decision.get('previous_attempt_id') == prior[-1]['attempt_id'] and
                     decision.get('preserve_existing') is True, 'RECOVERY_AUTHORIZATION_SCOPE_MISMATCH')
                check_ref(decision['owner_source'])
            else:
                need(recovery_authorization is None, 'NO_PRIOR_ATTEMPT_TO_RECOVER')
            attempt_id = uuid.uuid4().hex
            group_event = self._group_name_event()
            album_event = self._album_name_event(key)
            need(group_event and album_event, 'GROUP_AND_ALBUM_NAMES_REQUIRED')
            group_data = group_event[1]
            album_data = album_event[1]
            need(album_data['identity'] == identity, 'ALBUM_NAME_IDENTITY_MISMATCH')
            group_dir = self._group_directory(group_data)
            if prior:
                recovery_base = _suffixed_component(album_data['path_name'], ' (恢復 %d)' % (len(prior) + 1))
                taken = [event['data']['path_name'] for event in self.events
                         if event['kind'] == 'album-name']
                album_path_name = allocate_component(group_dir, recovery_base, taken=taken)
            else:
                album_path_name = validate_component(album_data['path_name'])
            destination = group_dir / album_path_name
            need(_entry(destination) is None, 'TARGET_ALREADY_EXISTS')
            destination.mkdir(mode=0o700)
            sync_dir(group_dir)
            info = destination.stat()
            naming = dict(schema=NAMING_SCHEMA, format=NAMING_FORMAT,
                group_name_sequence=group_event[0]['sequence'],
                album_name_sequence=album_event[0]['sequence'],
                group_display_name=group_data['display_name'],
                group_path_name=group_data['path_name'],
                album_display_name=album_data['display_name'],
                album_path_name=album_path_name,
                group_directory_device=group_data['directory_device'],
                group_directory_inode=group_data['directory_inode'],
                destination_device=info.st_dev, destination_inode=info.st_ino)
            need(not list(destination.iterdir()), 'EMPTY_DESTINATION_REQUIRED')
            return self.append('intent', dict(album_key=key, identity=identity, attempt_id=attempt_id,
                session_id=session_id, destination=str(destination),
                recovery_of=prior[-1]['attempt_id'] if prior else None, recovery_authorization=recovery,
                naming=naming, save_all_retry_allowed=False, dispatch_authorized=False))

    def outcome(self, *, session_id, attempt_id, outcome, evidence):
        with self.locked():
            self.bound(session_id)
            need(not self._naming_projection()['pending'], 'PENDING_NAMING_TRANSACTION')
            need(outcome in ('UNKNOWN', 'NOT_SENT', 'STOPPED', 'DOWNLOAD_FINISHED'), 'INVALID_OUTCOME')
            attempts = self.matching('intent')
            need(attempts and attempts[-1]['attempt_id'] == attempt_id, 'ONLY_LATEST_ATTEMPT_CAN_CHANGE')
            target = attempts[-1]
            need(self.status_map()[target['album_key']] != 'COMPLETED', 'COMPLETION_IMMUTABLE')
            outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == attempt_id]
            need(not outcomes, 'OUTCOME_ALREADY_KNOWN')
            return self.append('outcome', dict(attempt_id=attempt_id, album_key=target['album_key'],
                                               outcome=outcome, evidence=reference(evidence)))

    def _named_destination(self, attempt, expected_device=None, expected_inode=None):
        naming = attempt.get('naming')
        need(isinstance(naming, dict) and naming.get('schema') == NAMING_SCHEMA and
             naming.get('format') == NAMING_FORMAT, 'INVALID_NAMING_BINDING')
        group_name = validate_component(naming.get('group_path_name'))
        album_name = validate_component(naming.get('album_path_name'))
        destination = self.root / group_name / album_name
        need(str(destination) == attempt['destination'] and directory(destination) == destination,
             'NAMING_DESTINATION_CHANGED')
        info = destination.stat()
        device = naming.get('destination_device', expected_device)
        inode = naming.get('destination_inode', expected_inode)
        need(info.st_dev == device and info.st_ino == inode, 'NAMING_DESTINATION_IDENTITY_CHANGED')
        return destination, naming

    def _transaction_events(self, transaction_id, kind=None):
        rows = []
        for event in self.events:
            if event['kind'] != 'name-transaction':
                continue
            data = event['data']
            if data.get('transaction_id') == transaction_id and (kind is None or data.get('kind') == kind):
                rows.append((event, data))
        need(len(rows) <= 1, 'DUPLICATE_NAMING_TRANSACTION')
        return rows[0] if rows else None

    def _progress_event(self, transaction_id, action, index):
        rows = [event['data'] for event in self.events if event['kind'] == 'name-progress' and
                event['data'].get('transaction_id') == transaction_id and
                event['data'].get('action') == action and event['data'].get('index') == index]
        need(len(rows) <= 1, 'DUPLICATE_NAMING_PROGRESS')
        return rows[0] if rows else None

    def _progress_recorded(self, transaction_id, action, index):
        return self._progress_event(transaction_id, action, index) is not None

    def _record_progress(self, transaction, action, row, reconciled=False, observed_path=None):
        existing = self._progress_event(transaction['transaction_id'], action, row['index'])
        if existing is not None:
            return None
        from_name, to_name = {
            'SOURCE_TO_TEMP': (row['source_name'], row['temp_name']),
            'TEMP_TO_TARGET': (row['temp_name'], row['target_name']),
        }[action]
        data = dict(schema=NAMING_SCHEMA,
            transaction_id=transaction['transaction_id'], transaction_kind=transaction['kind'],
            action=action, index=row['index'], from_name=from_name, to_name=to_name,
            reconciled=reconciled)
        if observed_path is not None:
            entry = _entry(observed_path)
            need(entry is not None and stat.S_ISREG(entry.st_mode), 'NAMING_FILE_CHANGED')
            data.update(mtime_ns=entry.st_mtime_ns, ctime_ns=entry.st_ctime_ns)
        return self.append('name-progress', data)

    def _entry_matches(self, path, row, *, source=False, progress=None):
        entry = _entry(path)
        need(entry is not None and stat.S_ISREG(entry.st_mode), 'NAMING_FILE_CHANGED')
        raw = read_file(path)
        if len(raw) != row['size'] or digest(raw) != row['sha256'] or \
                entry.st_mtime_ns != row['source_mtime_ns']:
            return False
        if source:
            return entry.st_ctime_ns == row['source_ctime_ns']
        if progress is not None:
            return (entry.st_mtime_ns == progress.get('mtime_ns') and
                    entry.st_ctime_ns == progress.get('ctime_ns'))
        return True

    def _naming_row_is_valid(self, row):
        return (type(row.get('index')) is int and row['index'] > 0 and
                isinstance(row.get('source_name'), str) and
                Path(row['source_name']).name == row['source_name'] and
                isinstance(row.get('target_name'), str) and
                Path(row['target_name']).name == row['target_name'] and
                not row['target_name'].startswith('.') and
                isinstance(row.get('temp_name'), str) and
                Path(row['temp_name']).name == row['temp_name'] and
                row['temp_name'].startswith('.line-naming-') and
                type(row.get('size')) is int and row['size'] > 0 and
                isinstance(row.get('sha256'), str) and len(row['sha256']) == 64 and
                type(row.get('source_mtime_ns')) is int and
                type(row.get('source_ctime_ns')) is int)

    def _execute_file_rows(self, directory_path, transaction, rows):
        directory_path = directory(directory_path)
        need(isinstance(rows, list) and rows, 'INVALID_NAMING_TRANSACTION')
        source_names = [row['source_name'] for row in rows]
        target_names = [row['target_name'] for row in rows]
        temp_names = [row['temp_name'] for row in rows]
        need(len({_collision_key(name) for name in source_names}) == len(source_names) and
             len({_collision_key(name) for name in target_names}) == len(target_names) and
             len({_collision_key(name) for name in temp_names}) == len(temp_names),
             'AMBIGUOUS_NAMING_TRANSACTION')
        for row in rows:
            need(self._naming_row_is_valid(row), 'INVALID_NAMING_ROW')

        allowed_names = {_collision_key(name) for name in (*source_names, *temp_names, *target_names)}
        actual_names = {_collision_key(entry.name) for entry in directory_path.iterdir()}
        need(actual_names <= allowed_names, 'FOREIGN_NAMING_CONTENT')

        states = []
        for row in rows:
            source = directory_path / row['source_name']
            temporary = directory_path / row['temp_name']
            target = directory_path / row['target_name']
            source_entry, temp_entry, target_entry = _entry(source), _entry(temporary), _entry(target)
            need(not (source_entry and temp_entry), 'AMBIGUOUS_NAMING_STATE')
            if source_entry:
                need(stat.S_ISREG(source_entry.st_mode) and
                     self._entry_matches(source, row, source=True), 'NAMING_FILE_CHANGED')
            if temp_entry:
                need(stat.S_ISREG(temp_entry.st_mode) and self._entry_matches(temporary, row,
                     progress=self._progress_event(transaction['transaction_id'], 'SOURCE_TO_TEMP', row['index'])),
                     'NAMING_FILE_CHANGED')
            if target_entry:
                need(stat.S_ISREG(target_entry.st_mode), 'NAMING_TARGET_NOT_REGULAR')
                same_as_source = source_entry is not None and source_entry.st_ino == target_entry.st_ino
                if not same_as_source:
                    need(source_entry is None, 'TARGET_ALREADY_EXISTS')
                    need(self._entry_matches(target, row,
                         progress=self._progress_event(transaction['transaction_id'], 'TEMP_TO_TARGET', row['index'])),
                         'NAMING_TARGET_CHANGED')
            states.append((source, temporary, target, source_entry, temp_entry, target_entry))

        any_source = any(state[3] is not None for state in states)
        if any_source:
            for row, (source, temporary, target, source_entry, temp_entry, target_entry) in zip(rows, states):
                need(not (source_entry and temp_entry), 'AMBIGUOUS_NAMING_STATE')
                if source_entry:
                    need(temp_entry is None and _entry(temporary) is None, 'TARGET_ALREADY_EXISTS')
                    exclusive_rename(source, temporary)
                    self._record_progress(transaction, 'SOURCE_TO_TEMP', row, observed_path=temporary)
                elif temp_entry:
                    self._record_progress(transaction, 'SOURCE_TO_TEMP', row, reconciled=True,
                                          observed_path=temporary)
            need(not any(_entry(directory_path / row['source_name']) for row in rows),
                 'SOURCE_REMAINS_AFTER_NAMING')

        if not any(
                phase.get('transaction_id') == transaction['transaction_id'] and
                phase.get('phase') == 'TEMPS_READY' for phase in self.matching('name-phase')):
            self.append('name-phase', dict(schema=NAMING_SCHEMA,
                transaction_id=transaction['transaction_id'], transaction_kind=transaction['kind'],
                phase='TEMPS_READY'))

        for row in rows:
            temporary = directory_path / row['temp_name']
            target = directory_path / row['target_name']
            temp_entry, target_entry = _entry(temporary), _entry(target)
            need(not (temp_entry and target_entry), 'AMBIGUOUS_NAMING_STATE')
            if temp_entry:
                need(target_entry is None, 'TARGET_ALREADY_EXISTS')
                exclusive_rename(temporary, target)
                self._record_progress(transaction, 'TEMP_TO_TARGET', row, observed_path=target)
            elif target_entry:
                need(self._entry_matches(target, row,
                     progress=self._progress_event(transaction['transaction_id'], 'TEMP_TO_TARGET', row['index'])),
                     'NAMING_TARGET_CHANGED')
                self._record_progress(transaction, 'TEMP_TO_TARGET', row, reconciled=True,
                                      observed_path=target)
            else:
                raise DailyError('NAMING_FILE_MISSING')

        need(not any(_entry(directory_path / row['temp_name']) for row in rows),
             'TEMP_REMAINS_AFTER_NAMING')
        return [directory_path / row['target_name'] for row in rows]

    def _pending_initial_transactions(self):
        completed = {event['data']['attempt_id'] for event in self.events if event['kind'] == 'completion'}
        return [event['data'] for event in self.events if event['kind'] == 'name-transaction' and
                event['data'].get('kind') == 'INITIAL' and event['data'].get('attempt_id') not in completed]

    def _effective_completion(self, event, projection=None):
        projection = projection or self._naming_projection()
        projected = projection['completion_overrides'].get(event['sequence'])
        if projected:
            return dict(album_key=projected['album_key'], destination=projected['destination'],
                        proof=projected['proof'], raw=event['data'])
        return dict(album_key=event['data']['album_key'], destination=event['data']['destination'],
                    proof=event['data']['proof'], raw=event['data'])

    def _ordered_completion_files(self, completion, proof):
        naming = completion.get('naming')
        need(isinstance(naming, dict) and naming.get('schema') == NAMING_SCHEMA and
             naming.get('format') == NAMING_FORMAT and isinstance(naming.get('rows'), list),
             'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
        source_rows = sorted(naming['rows'], key=lambda row: row['index'])
        manifest = {row['name']: row for row in proof['manifest']}
        by_index = {}
        for name, row in manifest.items():
            match = re.search(r'_(\d+)(\.[^.]+)$', name)
            need(match is not None, 'CORRECTION_FILE_ORDER_CHANGED')
            index = int(match.group(1))
            need(index > 0 and index not in by_index, 'CORRECTION_FILE_ORDER_CHANGED')
            by_index[index] = row
        need(sorted(by_index) == list(range(1, len(source_rows) + 1)), 'CORRECTION_FILE_ORDER_CHANGED')
        result = []
        for original in source_rows:
            current = by_index[original['index']]
            need(Path(current['name']).suffix == original['extension'], 'CORRECTION_EXTENSION_CHANGED')
            result.append(dict(index=original['index'], source_name=current['name'],
                extension=original['extension'], size=current['size'], sha256=current['sha256'],
                source_mtime_ns=current['mtime_ns'], source_ctime_ns=current['ctime_ns']))
        return result

    def _record_directory_progress(self, transaction_id, action, from_name, to_name, reconciled=False):
        if self._progress_recorded(transaction_id, action, 0):
            return None
        return self.append('name-progress', dict(schema=NAMING_SCHEMA,
            transaction_id=transaction_id, transaction_kind='CORRECTION', action=action,
            index=0, from_name=from_name, to_name=to_name, reconciled=reconciled))

    def _move_directory_chain(self, parent, old_name, temp_name, new_name,
                              device, inode, transaction_id):
        parent = directory(parent)
        old_path, temp_path, new_path = parent / old_name, parent / temp_name, parent / new_name
        if old_name == new_name:
            need(directory(old_path) == old_path and old_path.stat().st_dev == device and
                 old_path.stat().st_ino == inode, 'CORRECTION_DIRECTORY_CHANGED')
            return old_path
        same_key = _collision_key(old_name) == _collision_key(new_name)
        old_entry, temp_entry = _entry(old_path), _entry(temp_path)
        new_entry = None if same_key and old_entry else _entry(new_path)
        if old_entry and not temp_entry:
            need(not new_entry, 'CORRECTION_TARGET_EXISTS')
            need(directory(old_path) == old_path and old_path.stat().st_dev == device and
                 old_path.stat().st_ino == inode, 'CORRECTION_DIRECTORY_CHANGED')
            exclusive_rename(old_path, temp_path)
            self._record_directory_progress(transaction_id, 'DIRECTORY_TO_TEMP', old_name, temp_name)
            temp_entry = _entry(temp_path)
        elif temp_entry and not old_entry:
            self._record_directory_progress(transaction_id, 'DIRECTORY_TO_TEMP', old_name,
                                            temp_name, reconciled=True)
        elif not temp_entry and new_entry and not old_entry:
            need(directory(new_path) == new_path and new_path.stat().st_dev == device and
                 new_path.stat().st_ino == inode, 'CORRECTION_DIRECTORY_CHANGED')
            self._record_directory_progress(transaction_id, 'DIRECTORY_TO_TEMP', old_name,
                                            temp_name, reconciled=True)
            self._record_directory_progress(transaction_id, 'TEMP_TO_DIRECTORY', temp_name,
                                            new_name, reconciled=True)
            return new_path
        else:
            raise DailyError('CORRECTION_PATH_STATE_AMBIGUOUS')
        need(temp_entry and _entry(temp_path) is not None, 'CORRECTION_DIRECTORY_MISSING')
        need(not _entry(new_path), 'CORRECTION_TARGET_EXISTS')
        need(directory(temp_path) == temp_path and temp_path.stat().st_dev == device and
             temp_path.stat().st_ino == inode, 'CORRECTION_DIRECTORY_CHANGED')
        exclusive_rename(temp_path, new_path)
        self._record_directory_progress(transaction_id, 'TEMP_TO_DIRECTORY', temp_name, new_name)
        return new_path

    def _validate_correction_plan(self, plan):
        need(isinstance(plan, dict) and plan.get('schema') == NAMING_SCHEMA and
             isinstance(plan.get('transaction_id'), str) and isinstance(plan.get('source'), dict),
             'INVALID_NAMING_CORRECTION_PLAN')
        if plan.get('kind') == 'GROUP_CORRECTION':
            for key in ('old_group_path_name', 'new_group_path_name'):
                validate_component(plan.get(key))
            need(isinstance(plan.get('temp_group_path_name'), str) and
                 plan['temp_group_path_name'].startswith('.line-naming-') and
                 Path(plan['temp_group_path_name']).name == plan['temp_group_path_name'] and
                 isinstance(plan.get('albums'), list) and plan['albums'], 'INVALID_NAMING_CORRECTION_PLAN')
            need(type(plan.get('group_directory_device')) is int and
                 type(plan.get('group_directory_inode')) is int and
                 isinstance(plan.get('before_proofs'), list) and
                 len(plan['before_proofs']) == len(plan['albums']), 'INVALID_NAMING_CORRECTION_PLAN')
            album_sequences = set()
            for row in plan['albums']:
                need(isinstance(row, dict) and isinstance(row.get('album_key'), str) and
                     type(row.get('completion_sequence')) is int and
                     row['completion_sequence'] not in album_sequences,
                     'INVALID_NAMING_CORRECTION_PLAN')
                album_sequences.add(row['completion_sequence'])
                validate_component(row.get('directory_name'))
                need(type(row.get('directory_device')) is int and
                     type(row.get('directory_inode')) is int, 'INVALID_NAMING_CORRECTION_PLAN')
            proof_sequences = set()
            for row in plan['before_proofs']:
                need(isinstance(row, dict) and type(row.get('completion_sequence')) is int and
                     row['completion_sequence'] not in proof_sequences and
                     isinstance(row.get('proof'), dict) and isinstance(row['proof'].get('manifest'), list) and
                     row['proof']['manifest'], 'INVALID_NAMING_CORRECTION_PLAN')
                proof_sequences.add(row['completion_sequence'])
                self._validate_proof(row['proof'], len(row['proof']['manifest']))
            need(proof_sequences == album_sequences, 'INVALID_NAMING_CORRECTION_PLAN')
        elif plan.get('kind') == 'ALBUM_CORRECTION':
            for key in ('old_group_path_name', 'old_album_path_name', 'new_album_path_name'):
                validate_component(plan.get(key))
            need(isinstance(plan.get('temp_album_path_name'), str) and
                 plan['temp_album_path_name'].startswith('.line-naming-') and
                 Path(plan['temp_album_path_name']).name == plan['temp_album_path_name'] and
                 isinstance(plan.get('rows'), list) and plan['rows'], 'INVALID_NAMING_CORRECTION_PLAN')
            need(isinstance(plan.get('album_key'), str) and isinstance(plan.get('identity'), dict) and
                 album_key(plan['identity']) == plan['album_key'] and
                 type(plan.get('completion_sequence')) is int and
                 type(plan.get('group_directory_device')) is int and
                 type(plan.get('group_directory_inode')) is int and
                 type(plan.get('album_directory_device')) is int and
                 type(plan.get('album_directory_inode')) is int and
                 isinstance(plan.get('new_destination'), str) and
                 isinstance(plan.get('before_proof'), dict) and
                 isinstance(plan['before_proof'].get('manifest'), list) and
                 plan['before_proof']['manifest'], 'INVALID_NAMING_CORRECTION_PLAN')
            self._validate_proof(plan['before_proof'], len(plan['before_proof']['manifest']))
            for row in plan['rows']:
                need(self._naming_row_is_valid(row), 'INVALID_NAMING_CORRECTION_PLAN')
        else:
            raise DailyError('INVALID_NAMING_CORRECTION_PLAN')

    def _correction_candidate(self, parent, names, device, inode):
        parent = directory(parent)
        first_identity = None
        for name in dict.fromkeys(names):
            path = parent / name
            entry = _entry(path)
            if entry is None:
                continue
            identity = (entry.st_dev, entry.st_ino)
            need(first_identity in (None, identity), 'CORRECTION_PATH_STATE_AMBIGUOUS')
            first_identity = identity
        need(first_identity is not None, 'CORRECTION_PATH_STATE_AMBIGUOUS')
        actual = [entry.name for entry in os.scandir(parent)
                  if (entry.stat(follow_symlinks=False).st_dev,
                      entry.stat(follow_symlinks=False).st_ino) == first_identity]
        need(len(actual) == 1, 'CORRECTION_PATH_STATE_AMBIGUOUS')
        path = parent / actual[0]
        need(directory(path) == path, 'CORRECTION_DIRECTORY_CHANGED')
        info = path.stat()
        need(info.st_dev == device and info.st_ino == inode, 'CORRECTION_DIRECTORY_CHANGED')
        return path

    def _completions_under_group(self, group_path, projection=None):
        projection = projection or self._naming_projection()
        group_path = Path(group_path)
        result = []
        for event in self.events:
            if event['kind'] != 'completion':
                continue
            effective = self._effective_completion(event, projection)
            if Path(effective['destination']).parent == group_path:
                need(isinstance(effective['raw'].get('naming'), dict) and
                     effective['raw']['naming'].get('schema') == NAMING_SCHEMA,
                     'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
                result.append((event, effective))
        return result

    def _assert_group_attempts_safe(self, selected, projection=None):
        projection = projection or self._naming_projection()
        selected_sequences = {event['sequence'] for event, _ in selected}
        selected_attempts = {event['data']['attempt_id'] for event, _ in selected}
        album_keys = [effective['album_key'] for _, effective in selected]
        need(len(album_keys) == len(set(album_keys)), 'AMBIGUOUS_GROUP_CONTENTS')
        for event in self.events:
            if event['kind'] != 'completion' or event['sequence'] in selected_sequences:
                continue
            need(isinstance(event['data'].get('naming'), dict) and
                 event['data']['naming'].get('schema') == NAMING_SCHEMA,
                 'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
            raise DailyError('FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')
        intents = [event['data'] for event in self.events if event['kind'] == 'intent']
        selected_intents = [intent for intent in intents if intent['attempt_id'] in selected_attempts]
        need(len(selected_intents) == len(selected), 'GROUP_HAS_UNRESOLVED_ALBUMS')
        for intent in intents:
            if intent['attempt_id'] in selected_attempts:
                self._validated_attempt_outcome(intent['attempt_id'], ('DOWNLOAD_FINISHED',),
                                                'GROUP_HAS_UNRESOLVED_ALBUMS')
                continue
            need(isinstance(intent.get('naming'), dict) and
                 intent['naming'].get('schema') == NAMING_SCHEMA,
                 'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
            self._validated_attempt_outcome(intent['attempt_id'], ('STOPPED', 'NOT_SENT'),
                                            'GROUP_HAS_UNRESOLVED_ALBUMS')

    def _validated_attempt_outcome(self, attempt_id, allowed, error):
        outcomes = [event['data'] for event in self.events if event['kind'] == 'outcome' and
                    event['data']['attempt_id'] == attempt_id]
        need(len(outcomes) == 1 and outcomes[0]['outcome'] in allowed, error)
        check_ref(outcomes[0]['evidence'])
        return outcomes[0]

    def _assert_album_attempts_safe(self, album_key, completed_attempt_id):
        for attempt in [event['data'] for event in self.events
                        if event['kind'] == 'intent' and event['data']['album_key'] == album_key]:
            allowed = ('DOWNLOAD_FINISHED',) if attempt['attempt_id'] == completed_attempt_id else \
                ('STOPPED', 'NOT_SENT')
            self._validated_attempt_outcome(attempt['attempt_id'], allowed, 'UNRESOLVED_ALBUM_ATTEMPT')

    def _precheck_group_plan(self, group_path, plan):
        selected = []
        for row in plan['albums']:
            completion = self._completion_by_sequence(row['completion_sequence'])
            selected.append((completion, self._effective_completion(completion)))
        self._assert_group_attempts_safe(selected)
        before = {row['completion_sequence']: row['proof'] for row in plan['before_proofs']}
        expected = sorted(row['directory_name'] for row in plan['albums'])
        actual = sorted(entry.name for entry in group_path.iterdir())
        need(actual == expected, 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')
        for row in plan['albums']:
            completion = self._completion_by_sequence(row['completion_sequence'])
            need(completion['data']['album_key'] == row['album_key'], 'CORRECTION_COMPLETION_REFERENCE_CHANGED')
            effective = self._effective_completion(completion)
            prior = before[row['completion_sequence']]
            need(prior['manifest'] == effective['proof']['manifest'] and
                 prior['manifest_sha256'] == effective['proof']['manifest_sha256'],
                 'CORRECTION_CONTENT_CHANGED')
            child = group_path / row['directory_name']
            entry = _entry(child)
            need(entry is not None and stat.S_ISDIR(entry.st_mode) and directory(child) == child and
                 entry.st_dev == row['directory_device'] and entry.st_ino == row['directory_inode'],
                 'CORRECTION_DIRECTORY_CHANGED')
            self._check_completion_files(child, prior, 'CORRECTION_CONTENT_CHANGED')

    def _verify_group_children(self, group_path, plan, decoder, decoder_sha256):
        before = {row['completion_sequence']: row['proof'] for row in plan['before_proofs']}
        expected = sorted(row['directory_name'] for row in plan['albums'])
        actual = sorted(entry.name for entry in group_path.iterdir())
        need(actual == expected, 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')
        albums = []
        for row in plan['albums']:
            completion = self._completion_by_sequence(row['completion_sequence'])
            prior = before[row['completion_sequence']]
            child = group_path / row['directory_name']
            entry = _entry(child)
            need(entry is not None and stat.S_ISDIR(entry.st_mode) and directory(child) == child and
                 entry.st_dev == row['directory_device'] and entry.st_ino == row['directory_inode'],
                 'CORRECTION_DIRECTORY_CHANGED')
            proof = verify_directory(child, len(prior['manifest']), decoder, decoder_sha256)
            need(proof['manifest'] == prior['manifest'] and
                 proof['manifest_sha256'] == prior['manifest_sha256'],
                 'CORRECTION_CONTENT_CHANGED')
            albums.append(dict(album_key=row['album_key'],
                               completion_sequence=row['completion_sequence'],
                               destination=str(child), proof=proof))
        return albums

    def _execute_group_correction(self, plan, decoder, decoder_sha256):
        self._validate_correction_plan(plan)
        new_path = self.root / plan['new_group_path_name']
        current_path = self._correction_candidate(self.root,
            (plan['old_group_path_name'], plan['temp_group_path_name'], plan['new_group_path_name']),
            plan['group_directory_device'], plan['group_directory_inode'])
        self._precheck_group_plan(current_path, plan)
        group_path = self._move_directory_chain(self.root, plan['old_group_path_name'],
            plan['temp_group_path_name'], plan['new_group_path_name'],
            plan['group_directory_device'], plan['group_directory_inode'], plan['transaction_id'])
        need(group_path == new_path, 'GROUP_CORRECTION_PATH_CHANGED')
        albums = self._verify_group_children(group_path, plan, decoder, decoder_sha256)
        self._precheck_group_plan(group_path, plan)
        info = new_path.stat()
        result = self.append('group-name', dict(schema=NAMING_SCHEMA, action='CORRECT',
            local_group_id=self.group['local_group_id'], display_name=plan['new_group_display_name'],
            path_name=plan['new_group_path_name'], source=plan['source'],
            directory_device=info.st_dev, directory_inode=info.st_ino,
            plan_id=plan['transaction_id'], correction=dict(albums=albums)))
        self._precheck_group_plan(group_path, plan)
        return result

    def _plan_group_correction(self, *, name, source, decoder, decoder_sha256):
        name_ref = reference(source)
        group_event = self._group_name_event()
        need(group_event, 'GROUP_NAME_REQUIRED')
        group_data = group_event[1]
        need(group_data['display_name'] != name, 'NO_NAME_CHANGE')
        self._group_directory(group_data)
        projection = self._naming_projection()
        need(not projection['pending'], 'PENDING_NAMING_TRANSACTION')
        need(not self._pending_initial_transactions(), 'PENDING_NAMING_TRANSACTION')
        group_path = self.root / group_data['path_name']
        completions = self._completions_under_group(group_path, projection)
        expected_dirs = [Path(effective['destination']).name for _, effective in completions]
        need(len(expected_dirs) == len(set(expected_dirs)), 'AMBIGUOUS_GROUP_CONTENTS')
        actual = sorted(entry.name for entry in group_path.iterdir())
        need(actual == sorted(expected_dirs), 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')
        self._assert_group_attempts_safe(completions, projection)
        need(completions, 'NO_COMPLETED_ALBUMS')
        states = self.status_map()
        for event, effective in completions:
            need(states.get(effective['album_key']) == 'COMPLETED', 'GROUP_HAS_UNRESOLVED_ALBUMS')
        before = []
        albums = []
        for event, effective in completions:
            need(directory(Path(effective['destination'])) == Path(effective['destination']),
                 'CORRECTION_DIRECTORY_CHANGED')
            expected = len(effective['proof']['manifest'])
            proof = verify_directory(effective['destination'], expected, decoder, decoder_sha256)
            need(proof['manifest'] == effective['proof']['manifest'] and
                 proof['manifest_sha256'] == effective['proof']['manifest_sha256'],
                 'CORRECTION_CONTENT_CHANGED')
            info = Path(effective['destination']).stat()
            before.append(dict(completion_sequence=event['sequence'], proof=proof))
            albums.append(dict(album_key=effective['album_key'], completion_sequence=event['sequence'],
                               directory_name=Path(effective['destination']).name,
                               directory_device=info.st_dev, directory_inode=info.st_ino))
        transaction_id = uuid.uuid4().hex
        new_component = allocate_component(self.root, safe_component(name),
            replace=group_data['path_name'], reserved=('backup-records', 'albums'))
        temp_component = '.line-naming-%s-group' % transaction_id
        need(_entry(self.root / temp_component) is None, 'TARGET_ALREADY_EXISTS')
        plan = dict(schema=NAMING_SCHEMA, kind='GROUP_CORRECTION', transaction_id=transaction_id,
            old_group_display_name=group_data['display_name'], new_group_display_name=name,
            old_group_path_name=group_data['path_name'], new_group_path_name=new_component,
            temp_group_path_name=temp_component, group_directory_device=group_data['directory_device'],
            group_directory_inode=group_data['directory_inode'], source=name_ref,
            albums=albums, before_proofs=before)
        self.append('name-correction-plan', plan)
        return self._execute_group_correction(plan, decoder, decoder_sha256)

    def correct_group_name(self, *, name, source, decoder, decoder_sha256):
        """Rename one captured group and every completed new-format album beneath it."""
        with self.locked():
            projection = self._naming_projection()
            if projection['pending']:
                pending = list(projection['pending'].values())
                need(len(pending) == 1 and pending[0]['kind'] == 'GROUP_CORRECTION' and
                     pending[0]['new_group_display_name'] == name and
                     Path(pending[0]['old_group_path_name']).name == pending[0]['old_group_path_name'],
                     'PENDING_NAMING_TRANSACTION')
                plan = pending[0]
                result = self._execute_group_correction(plan, decoder, decoder_sha256)
                return result
            return self._plan_group_correction(name=name, source=source,
                decoder=decoder, decoder_sha256=decoder_sha256)

    def _check_album_group_entries(self, group_path, plan, album_name, projection=None):
        projection = projection or self._naming_projection()
        expected = []
        for event, effective in self._completions_under_group(group_path, projection):
            if event['sequence'] == plan['completion_sequence']:
                continue
            expected.append(Path(effective['destination']).name)
        expected.append(album_name)
        need(len(expected) == len(set(expected)), 'AMBIGUOUS_GROUP_CONTENTS')
        actual = sorted(entry.name for entry in group_path.iterdir())
        need(actual == sorted(expected), 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')

    def _album_correction_group_completions(self, group_path, completion_sequence, projection=None):
        projection = projection or self._naming_projection()
        result = []
        for event in self.events:
            if event['kind'] != 'completion':
                continue
            effective = self._effective_completion(event, projection)
            if (event['sequence'] == completion_sequence or
                    Path(effective['destination']).parent == group_path):
                result.append((event, effective))
        return result

    def _assert_completion_directory_identity(self, completion, path):
        attempt_id = completion['data']['attempt_id']
        intents = [event['data'] for event in self.events if event['kind'] == 'intent' and
                   event['data']['attempt_id'] == attempt_id]
        need(len(intents) == 1, 'CORRECTION_DIRECTORY_CHANGED')
        naming = intents[0].get('naming')
        need(isinstance(naming, dict) and naming.get('schema') == NAMING_SCHEMA and
             naming.get('format') == NAMING_FORMAT and type(naming.get('destination_device')) is int and
             type(naming.get('destination_inode')) is int, 'CORRECTION_DIRECTORY_CHANGED')
        entry = _entry(path)
        need(entry is not None and stat.S_ISDIR(entry.st_mode) and directory(path) == path and
             entry.st_dev == naming['destination_device'] and entry.st_ino == naming['destination_inode'],
             'CORRECTION_DIRECTORY_CHANGED')

    def _assert_album_rows_proof(self, plan, proof):
        proof_by_name = {row['name']: row for row in proof['manifest']}
        need(len(proof_by_name) == len(proof['manifest']) and
             set(proof_by_name) == {row['target_name'] for row in plan['rows']},
             'ALBUM_CORRECTION_CONTENT_CHANGED')
        for row in plan['rows']:
            final = proof_by_name[row['target_name']]
            need(final['size'] == row['size'] and final['sha256'] == row['sha256'] and
                 final['mtime_ns'] == row['source_mtime_ns'],
                 'ALBUM_CORRECTION_CONTENT_CHANGED')

    def _precheck_album_plan(self, plan, group_path, album_path, *, target_proof=None,
                             projection=None):
        projection = projection or self._naming_projection()
        self._check_album_group_entries(group_path, plan, album_path.name, projection=projection)
        entry = _entry(album_path)
        need(entry is not None and stat.S_ISDIR(entry.st_mode) and directory(album_path) == album_path and
             entry.st_dev == plan['album_directory_device'] and
             entry.st_ino == plan['album_directory_inode'], 'CORRECTION_DIRECTORY_CHANGED')
        completion = self._completion_by_sequence(plan['completion_sequence'])
        need(completion['data']['album_key'] == plan['album_key'],
             'CORRECTION_COMPLETION_REFERENCE_CHANGED')
        effective = self._effective_completion(completion, projection)
        self._assert_album_attempts_safe(plan['album_key'], completion['data']['attempt_id'])
        group_completions = self._album_correction_group_completions(
            group_path, plan['completion_sequence'], projection)
        self._assert_group_attempts_safe(group_completions, projection)
        for event, sibling in group_completions:
            if event['sequence'] == plan['completion_sequence']:
                continue
            sibling_path = Path(sibling['destination'])
            self._assert_completion_directory_identity(event, sibling_path)
            self._check_completion_files(sibling_path, sibling['proof'], 'CORRECTION_CONTENT_CHANGED')
        if target_proof is not None:
            need(Path(effective['destination']) == album_path, 'ALBUM_CORRECTION_PATH_CHANGED')
            self._assert_album_rows_proof(plan, target_proof)
            self._check_completion_files(album_path, target_proof,
                                         'ALBUM_CORRECTION_CONTENT_CHANGED')
            return
        need(plan['before_proof']['manifest'] == effective['proof']['manifest'] and
             plan['before_proof']['manifest_sha256'] == effective['proof']['manifest_sha256'],
             'CORRECTION_CONTENT_CHANGED')
        allowed = {_collision_key(name) for row in plan['rows']
                   for name in (row['source_name'], row['temp_name'], row['target_name'])}
        actual = {_collision_key(entry.name) for entry in album_path.iterdir()}
        need(actual <= allowed, 'FOREIGN_NAMING_CONTENT')
        has_progress = any(event['kind'] == 'name-progress' and
                           event['data'].get('transaction_id') == plan['transaction_id']
                           for event in self.events)
        if not has_progress:
            self._check_completion_files(album_path, plan['before_proof'],
                                         'CORRECTION_CONTENT_CHANGED')

    def _execute_album_correction(self, plan, decoder, decoder_sha256):
        self._validate_correction_plan(plan)
        group_path = self.root / plan['old_group_path_name']
        need(directory(group_path) == group_path and
             group_path.stat().st_dev == plan['group_directory_device'] and
             group_path.stat().st_ino == plan['group_directory_inode'], 'CORRECTION_DIRECTORY_CHANGED')
        current_album = self._correction_candidate(group_path,
            (plan['old_album_path_name'], plan['temp_album_path_name'], plan['new_album_path_name']),
            plan['album_directory_device'], plan['album_directory_inode'])
        self._precheck_album_plan(plan, group_path, current_album)
        album_path = self._move_directory_chain(group_path, plan['old_album_path_name'],
            plan['temp_album_path_name'], plan['new_album_path_name'],
            plan['album_directory_device'], plan['album_directory_inode'], plan['transaction_id'])
        need(str(album_path) == plan['new_destination'], 'ALBUM_CORRECTION_PATH_CHANGED')
        self._precheck_album_plan(plan, group_path, album_path)
        transaction = dict(kind='ALBUM_CORRECTION', transaction_id=plan['transaction_id'])
        self._execute_file_rows(album_path, transaction, plan['rows'])
        expected = len(plan['before_proof']['manifest'])
        proof = verify_directory(album_path, expected, decoder, decoder_sha256)
        self._assert_album_rows_proof(plan, proof)
        self._precheck_album_plan(plan, group_path, album_path)
        result = self.append('album-name', dict(schema=NAMING_SCHEMA, action='CORRECT',
            album_key=plan['album_key'], identity=plan['identity'],
            display_name=plan['new_album_display_name'], path_name=plan['new_album_path_name'],
            source=plan['source'], plan_id=plan['transaction_id'],
            correction=dict(albums=[dict(album_key=plan['album_key'],
                completion_sequence=plan['completion_sequence'],
                destination=str(album_path), proof=proof)])))
        self._precheck_album_plan(plan, group_path, album_path, target_proof=proof)
        return result

    def _plan_album_correction(self, *, album_key, name, source, decoder, decoder_sha256):
        name_ref = reference(source)
        album_event = self._album_name_event(album_key)
        need(album_event, 'ALBUM_NAME_REQUIRED')
        album_data = album_event[1]
        need(album_data['display_name'] != name, 'NO_NAME_CHANGE')
        projection = self._naming_projection()
        need(not projection['pending'], 'PENDING_NAMING_TRANSACTION')
        need(not self._pending_initial_transactions(), 'PENDING_NAMING_TRANSACTION')
        completions = [event for event in self.events if event['kind'] == 'completion' and
                       event['data']['album_key'] == album_key]
        need(len(completions) == 1, 'CORRECTION_REQUIRES_ONE_COMPLETION')
        completion_event = completions[0]
        completion = completion_event['data']
        need(isinstance(completion.get('naming'), dict) and
             completion['naming'].get('schema') == NAMING_SCHEMA, 'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
        effective = self._effective_completion(completion_event, projection)
        current_destination = Path(effective['destination'])
        group_event = self._group_name_event()
        need(group_event, 'GROUP_NAME_REQUIRED')
        group_data = group_event[1]
        group_path = self.root / group_data['path_name']
        need(current_destination.parent == group_path and directory(current_destination) == current_destination,
             'ALBUM_CORRECTION_PATH_CHANGED')
        group_completions = self._completions_under_group(group_path, projection)
        need(completion_event['sequence'] in {event['sequence'] for event, _ in group_completions},
             'ALBUM_CORRECTION_PATH_CHANGED')
        expected_dirs = [Path(effective_row['destination']).name
                         for _, effective_row in group_completions]
        need(len(expected_dirs) == len(set(expected_dirs)), 'AMBIGUOUS_GROUP_CONTENTS')
        actual = sorted(entry.name for entry in group_path.iterdir())
        need(actual == sorted(expected_dirs), 'FOREIGN_OR_INCOMPLETE_GROUP_CONTENT')
        self._assert_group_attempts_safe(group_completions, projection)
        need(self.status_map().get(album_key) == 'COMPLETED', 'ALBUM_NOT_COMPLETED')
        self._assert_album_attempts_safe(album_key, completion['attempt_id'])
        expected = len(effective['proof']['manifest'])
        before_proof = verify_directory(current_destination, expected, decoder, decoder_sha256)
        need(before_proof['manifest'] == effective['proof']['manifest'] and
             before_proof['manifest_sha256'] == effective['proof']['manifest_sha256'],
             'CORRECTION_CONTENT_CHANGED')
        current_files = self._ordered_completion_files(completion,
            dict(manifest=before_proof['manifest']))
        taken = [event['data']['path_name'] for event in self.events if event['kind'] == 'album-name'
                 and event['data'].get('album_key') != album_key]
        for event in self.events:
            if event['kind'] != 'completion' or event['data']['album_key'] == album_key:
                continue
            other = self._effective_completion(event, projection)
            if Path(other['destination']).parent == group_path:
                taken.append(Path(other['destination']).name)
        new_component = allocate_component(group_path, safe_component(name),
            taken=taken, replace=current_destination.name)
        transaction_id = uuid.uuid4().hex
        temp_component = '.line-naming-%s-album' % transaction_id
        need(_entry(group_path / temp_component) is None, 'TARGET_ALREADY_EXISTS')
        width = max(3, len(str(len(current_files))))
        rows = []
        for row in current_files:
            temporary = '.line-naming-%s-%0*d.tmp' % (transaction_id, width, row['index'])
            target_name = '%s_%0*d%s' % (new_component, width, row['index'], row['extension'])
            need(len(target_name.encode('utf-8')) <= 255, 'PHOTO_NAME_TOO_LONG')
            rows.append(dict(row, temp_name=temporary, target_name=target_name))
        info = current_destination.stat()
        new_destination = group_path / new_component
        plan = dict(schema=NAMING_SCHEMA, kind='ALBUM_CORRECTION', transaction_id=transaction_id,
            album_key=album_key, identity=album_data['identity'],
            completion_sequence=completion_event['sequence'],
            old_album_display_name=album_data['display_name'], new_album_display_name=name,
            old_group_path_name=group_data['path_name'], group_directory_device=group_data['directory_device'],
            group_directory_inode=group_data['directory_inode'],
            old_album_path_name=current_destination.name, new_album_path_name=new_component,
            temp_album_path_name=temp_component, old_destination=str(current_destination),
            new_destination=str(new_destination), album_directory_device=info.st_dev,
            album_directory_inode=info.st_ino, source=name_ref,
            before_proof=before_proof, rows=rows)
        self.append('name-correction-plan', plan)
        return self._execute_album_correction(plan, decoder, decoder_sha256)

    def correct_album_name(self, *, album_key, name, source, decoder, decoder_sha256):
        """Correct one completed album's folder/prefix using an album_key from memory."""
        with self.locked():
            projection = self._naming_projection()
            if projection['pending']:
                pending = list(projection['pending'].values())
                need(len(pending) == 1 and pending[0]['kind'] == 'ALBUM_CORRECTION' and
                     pending[0]['album_key'] == album_key and
                     pending[0]['new_album_display_name'] == name, 'PENDING_NAMING_TRANSACTION')
                return self._execute_album_correction(pending[0], decoder, decoder_sha256)
            return self._plan_album_correction(album_key=album_key, name=name, source=source,
                decoder=decoder, decoder_sha256=decoder_sha256)

    def resume_naming(self, *, decoder, decoder_sha256):
        """Resume one durable naming or correction plan without redispatching downloads."""
        with self.locked():
            projection = self._naming_projection()
            need(len(projection['pending']) <= 1, 'MULTIPLE_PENDING_NAMING_TRANSACTIONS')
            if projection['pending']:
                plan = next(iter(projection['pending'].values()))
                if plan['kind'] == 'GROUP_CORRECTION':
                    return self._execute_group_correction(plan, decoder, decoder_sha256)
                if plan['kind'] == 'ALBUM_CORRECTION':
                    return self._execute_album_correction(plan, decoder, decoder_sha256)
                raise DailyError('INVALID_NAMING_CORRECTION_PLAN')
            pending = self._pending_initial_transactions()
            need(len(pending) <= 1, 'MULTIPLE_PENDING_NAMING_TRANSACTIONS')
            intents = [event['data'] for event in self.events if event['kind'] == 'intent']
            if not intents:
                need(not pending, 'NAMING_ATTEMPT_CHANGED')
                return dict(status='NOTHING_TO_RESUME')
            target = intents[-1]
            if pending:
                need(pending[0]['attempt_id'] == target['attempt_id'], 'NAMING_ATTEMPT_CHANGED')
            elif any(event['kind'] == 'completion' and
                     event['data'].get('attempt_id') == target['attempt_id'] for event in self.events):
                return dict(status='NOTHING_TO_RESUME')
            outcomes = [event['data'] for event in self.events if event['kind'] == 'outcome' and
                        event['data']['attempt_id'] == target['attempt_id']]
            need(len(outcomes) <= 1, 'AMBIGUOUS_DOWNLOAD_OUTCOME')
            need(outcomes, 'KNOWN_DOWNLOAD_FINISH_REQUIRED')
            latest_outcome = outcomes[0]['outcome']
            if latest_outcome == 'UNKNOWN':
                raise DailyError('UNKNOWN_OR_RUNNING_NO_REPLAY')
            if latest_outcome != 'DOWNLOAD_FINISHED':
                raise DailyError('NO_DOWNLOAD_FINISHED_TO_RESUME')
            check_ref(outcomes[0]['evidence'])
            need(target.get('naming'), 'UNSUPPORTED_OLDER_FORMAT_CORRECTION')
            return self._complete_named(target, decoder, decoder_sha256)

    def _build_initial_name_transaction(self, target):
        destination, naming = self._named_destination(target)
        rows = stable_image_inventory(destination, target['identity']['expected_images'])
        image_rows = [row['name'] for row in rows]
        photo_plan = planned_photo_names(naming['album_path_name'], image_rows)
        by_name = {row['name']: row for row in rows}
        transaction_id = uuid.uuid4().hex
        width = max(3, len(str(len(photo_plan))))
        mapped = []
        for item in photo_plan:
            source = by_name[item['source_name']]
            temporary = '.line-naming-%s-%0*d.tmp' % (transaction_id, width, item['index'])
            need(_entry(destination / temporary) is None, 'TARGET_ALREADY_EXISTS')
            mapped.append(dict(index=item['index'], source_name=item['source_name'],
                temp_name=temporary, target_name=item['target_name'], extension=item['extension'],
                size=source['size'], sha256=source['sha256'],
                source_mtime_ns=source['mtime_ns'], source_ctime_ns=source['ctime_ns']))
        existing_targets = set(image_rows)
        for row in mapped:
            target_path = destination / row['target_name']
            if _collision_key(row['target_name']) not in {_collision_key(name) for name in existing_targets}:
                need(_entry(target_path) is None, 'TARGET_ALREADY_EXISTS')
        info = destination.stat()
        data = dict(schema=NAMING_SCHEMA, kind='INITIAL', transaction_id=transaction_id,
            attempt_id=target['attempt_id'], album_key=target['album_key'],
            destination=str(destination), destination_device=info.st_dev, destination_inode=info.st_ino,
            source_inventory_sha256=digest(encoded(rows)), rows=mapped)
        return self.append('name-transaction', data)

    def _complete_named(self, target, decoder, decoder_sha256):
        need(not any(event['kind'] == 'completion' and
                     event['data'].get('attempt_id') == target['attempt_id'] and
                     event['data'].get('album_key') == target['album_key'] for event in self.events),
             'COMPLETION_IMMUTABLE')
        destination, intent_naming = self._named_destination(target)
        transactions = [event['data'] for event in self.events if event['kind'] == 'name-transaction'
                        and event['data'].get('kind') == 'INITIAL' and
                        event['data'].get('attempt_id') == target['attempt_id']]
        need(len(transactions) <= 1, 'DUPLICATE_NAMING_TRANSACTION')
        transaction = transactions[0] if transactions else self._build_initial_name_transaction(target)
        need(transaction['album_key'] == target['album_key'] and transaction['attempt_id'] == target['attempt_id'] and
             Path(transaction['destination']) == destination, 'NAMING_TRANSACTION_BINDING_CHANGED')
        info = destination.stat()
        need(info.st_dev == transaction['destination_device'] and info.st_ino == transaction['destination_inode'],
             'NAMING_TRANSACTION_DIRECTORY_CHANGED')
        self._execute_file_rows(destination, transaction, transaction['rows'])
        proof = verify_directory(destination, target['identity']['expected_images'],
                                 decoder, decoder_sha256)
        proof_by_name = {row['name']: row for row in proof['manifest']}
        for row in transaction['rows']:
            final = proof_by_name.get(row['target_name'])
            need(final and final['size'] == row['size'] and final['sha256'] == row['sha256'] and
                 final['mtime_ns'] == row['source_mtime_ns'],
                 'NAMING_CONTENT_CHANGED')
        naming = dict(intent_naming, transaction_id=transaction['transaction_id'],
            source_inventory_sha256=transaction['source_inventory_sha256'],
            rows=[{key: row[key] for key in ('index', 'source_name', 'target_name', 'extension', 'size', 'sha256')}
                  for row in transaction['rows']])
        return self.append('completion', dict(attempt_id=target['attempt_id'], album_key=target['album_key'],
            destination=str(destination), proof=proof, naming=naming,
            execution_lane='MANUAL_DIAGNOSTIC', formal_auto_verified=False))

    def complete(self, *, session_id, attempt_id, decoder, decoder_sha256):
        with self.locked():
            self.bound(session_id)
            need(not self._naming_projection()['pending'], 'PENDING_NAMING_TRANSACTION')
            attempts = self.matching('intent')
            need(attempts and attempts[-1]['attempt_id'] == attempt_id, 'ONLY_LATEST_ATTEMPT_CAN_COMPLETE')
            target = attempts[-1]
            need(not any(event['kind'] == 'completion' and
                         event['data'].get('album_key') == target['album_key'] for event in self.events),
                 'COMPLETION_IMMUTABLE')
            need(self.status_map()[target['album_key']] != 'COMPLETED', 'COMPLETION_IMMUTABLE')
            outcomes = [o for o in self.matching('outcome') if o['attempt_id'] == attempt_id]
            need(outcomes and outcomes[-1]['outcome'] == 'DOWNLOAD_FINISHED', 'KNOWN_DOWNLOAD_FINISH_REQUIRED')
            check_ref(outcomes[-1]['evidence'])
            if target.get('naming'):
                return self._complete_named(target, decoder, decoder_sha256)
            proof = verify_directory(target['destination'], target['identity']['expected_images'],
                                     decoder, decoder_sha256)
            return self.append('completion', dict(attempt_id=attempt_id, album_key=target['album_key'],
                destination=target['destination'], proof=proof, execution_lane='MANUAL_DIAGNOSTIC',
                formal_auto_verified=False))

    def summary(self):
        with self.locked():
            pages = self.pages()
            current = {key for page in pages for key in page['keys']}
            ever_seen = {key for page in self.matching('page') for key in page['keys']}
            states = self.status_map()
            counts = {status: sum(states.get(key) == status for key in current)
                      for status in ('COMPLETED', 'EXCLUDED', 'INCOMPLETE', 'UNKNOWN', 'PROTECTED_HISTORY')}
            counts['UNKNOWN'] += sum(p['unresolved'] for p in pages) + len(ever_seen - current)
            covered = bool(pages and pages[-1]['bottom_stationary'])
            return dict(local_group_id=self.group['local_group_id'], total=len(current), **counts,
                list_coverage='OBSERVED' if covered else 'INCOMPLETE',
                ALL_ELIGIBLE_ALBUMS_BACKED_UP='PASS' if covered and current and
                    counts['INCOMPLETE'] == counts['UNKNOWN'] == counts['PROTECTED_HISTORY'] == 0 else 'INCOMPLETE',
                dispatch_authorized=False, formal_auto_verified=False,
                recovery_strategy='ALBUM_LEVEL', photo_level_resume='FUTURE_RESEARCH',
                evidence_role='AGENT_ATTESTED_OBSERVATIONS', sensor_verified=False,
                real_line_e2e='NOT_TESTED', pass_scope='AGENT_ATTESTED_ACCOUNTING_ONLY')

def stable_image_inventory(destination, expected):
    need(type(expected) is int and expected > 0, 'PHOTO_COUNT_REQUIRED')
    samples = []
    for sample in range(3):
        if sample:
            time.sleep(1)
        rows = image_inventory(destination)
        need(len(rows) == expected, 'DOWNLOAD_COUNT_MISMATCH')
        need(not samples or rows == samples[-1], 'DOWNLOAD_NOT_STABLE')
        samples.append(rows)
    return samples[-1]


def image_inventory(destination):
    root = directory(destination)
    result = []
    for path in sorted(root.iterdir()):
        need(not path.name.startswith('.') and path.suffix.lower() in ('.jpg', '.jpeg', '.png'),
             'UNEXPECTED_DOWNLOAD_ENTRY')
        entry = _entry(path)
        need(entry is not None and stat.S_ISREG(entry.st_mode), 'DOWNLOAD_NOT_REGULAR')
        raw = read_file(path)
        need(bool(raw), 'EMPTY_DOWNLOAD')
        info = path.stat()
        result.append(dict(name=path.name, size=len(raw), sha256=digest(raw),
                           mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns))
    return result


def verify_directory(destination, expected, decoder, decoder_sha256):
    need(type(expected) is int and expected > 0, 'PHOTO_COUNT_REQUIRED')
    binary = reference(decoder)
    need(binary['sha256'] == decoder_sha256, 'DECODER_DRIFT')
    rows = stable_image_inventory(destination, expected)
    run = subprocess.run([str(decoder), str(destination), str(expected)], capture_output=True, timeout=120)
    need(run.returncode == 0, 'IMAGEIO_DECODE_FAILED')
    result = strict_json(run.stdout, 'INVALID_IMAGEIO_RESULT')
    need(result.get('verdict') == 'PASS' and result.get('readOnly') is True and
         result.get('destination') == str(destination) and result.get('expected') == expected and
         result.get('actualEntries') == expected, 'IMAGEIO_BINDING_MISMATCH')
    decoded = result.get('entries', [])
    need(len(decoded) == expected and len({r['name'] for r in decoded}) == expected and
         {r['name']: r.get('sha256') for r in decoded if r.get('decoded') is True} ==
         {r['name']: r['sha256'] for r in rows}, 'IMAGEIO_CONTENT_MISMATCH')
    need(reference(decoder) == binary and image_inventory(destination) == rows, 'CONTENT_CHANGED_AFTER_DECODE')
    return dict(manifest=rows, manifest_sha256=digest(encoded(rows)), imageio=result,
                imageio_stdout_sha256=digest(run.stdout), decoder=binary, stable_samples=3)


DIRECT_KEYS = ('session_id', 'album_key', 'name', 'source', 'decoder', 'decoder_sha256',
               'attempt_id', 'outcome', 'evidence', 'recovery_authorization')
DIRECT_PATH_KEYS = ('source', 'decoder', 'evidence', 'recovery_authorization')
DIRECT_OPERATIONS = {
    'capture-group-name': dict(method='capture_group_name',
                               required={'session_id', 'name', 'source'}, optional=set()),
    'capture-album-name': dict(method='capture_album_name',
                               required={'session_id', 'album_key', 'name', 'source'}, optional=set()),
    'correct-group-name': dict(method='correct_group_name',
                               required={'name', 'source', 'decoder', 'decoder_sha256'}, optional=set()),
    'correct-album-name': dict(method='correct_album_name',
                               required={'album_key', 'name', 'source', 'decoder', 'decoder_sha256'},
                               optional=set()),
    'resume-naming': dict(method='resume_naming',
                          required={'decoder', 'decoder_sha256'}, optional=set()),
    'intent': dict(method='intent', dual=True,
                   required={'session_id', 'album_key'}, optional={'recovery_authorization'}),
    'outcome': dict(method='outcome', dual=True,
                    required={'session_id', 'attempt_id', 'outcome', 'evidence'}, optional=set()),
    'verify': dict(method='complete', dual=True,
                   required={'session_id', 'attempt_id', 'decoder', 'decoder_sha256'}, optional=set()),
}


def _direct_cli_data(parser, namespace):
    spec = DIRECT_OPERATIONS[namespace.operation]
    data = {key: getattr(namespace, key) for key in DIRECT_KEYS
            if getattr(namespace, key) is not None}
    unexpected = sorted(set(data) - spec['required'] - spec['optional'])
    if unexpected:
        parser.error('unexpected arguments for %s: %s' %
                     (namespace.operation, ', '.join('--' + key.replace('_', '-') for key in unexpected)))
    required = spec['required']
    missing = sorted(required - set(data))
    if missing:
        parser.error('missing arguments for %s: %s' %
                     (namespace.operation, ', '.join('--' + key.replace('_', '-') for key in missing)))
    for key in DIRECT_PATH_KEYS:
        if key in data:
            data[key] = reference(data[key])['path']
    return data


def _direct_args_present(namespace):
    return any(getattr(namespace, key) is not None for key in DIRECT_KEYS)


def _operation_help(operation):
    spec = DIRECT_OPERATIONS.get(operation)
    if not spec:
        return ('usage: python3 -m line_backup_batch.daily %s --root ROOT [--input PRIVATE_JSON]\n\n'
                'This operation uses the private JSON form described in daily.py. --help is read-only.'
                % operation)
    direct = ' '.join('--%s %s' % (key.replace('_', '-'), key.upper())
                      for key in sorted(spec['required']))
    if spec['optional']:
        direct += ' ' + ' '.join('[--%s PATH]' % key.replace('_', '-') for key in sorted(spec['optional']))
    lines = ['usage: python3 -m line_backup_batch.daily %s --root ROOT %s'
             % (operation, direct)]
    if spec.get('dual'):
        lines.append('       python3 -m line_backup_batch.daily %s --root ROOT --input PRIVATE_JSON'
                     % operation)
    lines.append('')
    lines.append('Direct arguments cannot be combined with --input. Paths must be regular files inside this project.')
    return '\n'.join(lines)


def _album_identity(records, key):
    matches = [album['identity'] for album in records.memory()['albums']
               if album['album_key'] == key]
    need(len(matches) == 1, 'ALBUM_KEY_NOT_UNIQUE')
    return matches[0]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    operations = ['init', 'bind', 'history', 'scan', 'page', 'detail', 'summary',
                  'memory-import', 'memory', *DIRECT_OPERATIONS]
    if argv and argv[0] in operations and any(arg in ('-h', '--help') for arg in argv[1:]):
        print(_operation_help(argv[0]))
        return 0
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='Correction commands take direct --name/--source/--decoder arguments; no hand-edited JSON is needed.')
    parser.add_argument('operation', choices=operations)
    parser.add_argument('--root', required=True)
    parser.add_argument('--input', help='Private JSON input, using the method argument names in daily.py')
    parser.add_argument('--session-id', help='Current foreground session id for name capture')
    parser.add_argument('--album-key', help='Album key from the read-only memory projection')
    parser.add_argument('--name', help='Observed or replacement display name')
    parser.add_argument('--source', help='Private evidence file for name capture or correction')
    parser.add_argument('--decoder', help='Compiled image_decode binary')
    parser.add_argument('--decoder-sha256', help='Expected SHA-256 of the image_decode binary')
    parser.add_argument('--attempt-id', help='Current attempt id from the intent result')
    parser.add_argument('--outcome', help='Observed dispatch outcome')
    parser.add_argument('--evidence', help='Private evidence file for an observed outcome')
    parser.add_argument('--recovery-authorization', help='Private Owner authorization for album recovery')
    ns = parser.parse_args(argv)
    try:
        methods = {'init': 'initialize', 'scan': 'start_scan', 'verify': 'complete', 'memory-import': 'import_memory'}
        direct_spec = DIRECT_OPERATIONS.get(ns.operation)
        direct_present = _direct_args_present(ns)
        if direct_spec and ns.input:
            if direct_present:
                parser.error('--input cannot be combined with direct arguments')
            data = strict_json(read_file(reference(ns.input)['path']), 'INVALID_INPUT')
            method = getattr(DailyRecords(ns.root), methods.get(ns.operation, direct_spec['method']))
        elif direct_spec:
            data = _direct_cli_data(parser, ns)
            records = DailyRecords(ns.root)
            if ns.operation in ('capture-album-name', 'intent'):
                data['identity'] = _album_identity(records, data['album_key'])
                data.pop('album_key')
            method = getattr(records, direct_spec['method'])
        else:
            if direct_present:
                parser.error('direct arguments are not accepted with %s' % ns.operation)
            data = strict_json(read_file(reference(ns.input)['path']), 'INVALID_INPUT') if ns.input else {}
            method = getattr(DailyRecords(ns.root), methods.get(ns.operation, ns.operation))
        result = method(**data)
        print(json.dumps(dict(result=result, dispatch_authorized=False), ensure_ascii=False))
        return 0
    except (DailyError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='REFUSED', reason=str(exc), dispatch_authorized=False)))
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
