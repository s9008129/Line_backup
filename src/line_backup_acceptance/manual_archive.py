"""Fail-closed MANUAL_DIAGNOSTIC exclusion registry.

The registry records bytes already downloaded outside the formal transaction
lifecycle. It never claims VERIFIED state and never authorizes a dispatch.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from .common import AcceptanceError

REGISTRY_PATH = 'state/manual_archives.json'
REGISTRY_VERSION = 1
PROVENANCE = 'MANUAL_DIAGNOSTIC'

A56 = {'start_date': '2024-05-27', 'end_date': '2024-05-31', 'expected_images': 56}
B53 = {'start_date': '2024-05-20', 'end_date': '2024-05-24', 'expected_images': 53}
A45 = {'start_date': '2024-04-22', 'end_date': '2024-04-26', 'expected_images': 45}
B78 = {'start_date': '2024-04-21', 'end_date': '2024-04-21', 'expected_images': 78}
EXCLUDED_65 = {'start_date': '2024-06-02', 'end_date': '2024-06-07', 'expected_images': 65}

REQUIRED_MANUAL_FINGERPRINTS = (A56, B53)
OWNER_ALLOWED_FINGERPRINTS = (A45, B78)
OWNER_EXCLUDED_FINGERPRINTS = (EXCLUDED_65,)

ENTRY_KEYS = {
    'fingerprint', 'provenance', 'recorded_at', 'manifest_path', 'manifest_sha256',
    'verification_path', 'verification_sha256', 'file_count', 'total_bytes',
}
RECORD_KEYS = {'fingerprint', 'destination', 'manifest_path', 'verification_path'}
FINGERPRINT_KEYS = {'start_date', 'end_date', 'expected_images'}
SHA256 = re.compile(r'[0-9a-f]{64}')
MANIFEST_LINE = re.compile(r'([0-9a-f]{64})  ([^\r\n]+)')


def _fail(code, message):
    raise AcceptanceError(code, message, 4)


def _fingerprint_key(value):
    if not isinstance(value, dict) or set(value) != FINGERPRINT_KEYS:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Invalid fingerprint shape')
    if not all(isinstance(value[k], str) for k in ('start_date', 'end_date')):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Invalid fingerprint dates')
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value['start_date']) or not re.fullmatch(
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value['end_date']):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Invalid fingerprint date format')
    try:
        start = dt.date.fromisoformat(value['start_date'])
        end = dt.date.fromisoformat(value['end_date'])
    except ValueError:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Invalid Gregorian fingerprint date')
    if start > end:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Fingerprint start is after end')
    count = value['expected_images']
    if type(count) is not int or count < 1 or count > 2**53 - 1:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Invalid fingerprint image count')
    return value['start_date'], value['end_date'], count


def fingerprint_tuple(value):
    return _fingerprint_key(value)


def owner_target_allowed(value):
    allowed = {_fingerprint_key(item) for item in OWNER_ALLOWED_FINGERPRINTS}
    return _fingerprint_key(value) in allowed


def owner_target_excluded(value):
    excluded = {_fingerprint_key(item) for item in OWNER_EXCLUDED_FINGERPRINTS}
    return _fingerprint_key(value) in excluded


def require_owner_target(value):
    if not owner_target_allowed(value):
        _fail('BOUNDED_TARGET_INELIGIBLE', 'Target is outside the Owner-bound A45/B78 allowlist')


def required_for_root(project_root):
    """The local A56/B53 registry is mandatory for the installed project, not fixtures."""
    installed = Path(__file__).resolve().parents[2]
    root = Path(project_root).resolve()
    return root == installed and 'fixtures' not in root.parts


def _relative_path(reader, value):
    if not isinstance(value, str) or not value:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive path is missing')
    if value.startswith('/'):
        prefix = reader.root.rstrip('/') + '/'
        if not value.startswith(prefix):
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive path escapes the selected project')
        value = value[len(prefix):]
    if not value or any(part in ('', '.', '..') for part in value.split('/')):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive path is not canonical')
    return value


def _read_bound(reader, value, code):
    relative = _relative_path(reader, value)
    return reader.read(relative, code)


def _read_registry(reader, required):
    try:
        fd = reader.open(REGISTRY_PATH)
    except FileNotFoundError:
        if required:
            _fail('MANUAL_ARCHIVE_REGISTRY_REQUIRED', 'Required manual archive registry is missing')
        return None
    except OSError:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive registry is unsafe')
    else:
        import os
        os.close(fd)
    raw, _ = reader.read(REGISTRY_PATH, 'MANUAL_ARCHIVE_REGISTRY_INVALID')
    return raw


def _strict_json(raw, code):
    import json

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail(code, 'Duplicate JSON object key')
            result[key] = value
        return result

    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: _fail(code, 'Nonfinite JSON number'))
    except (ValueError, UnicodeError, RecursionError):
        _fail(code, 'Invalid JSON')


def _validate_manifest(raw, verification_entries, file_count):
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest is not UTF-8')
    lines = text.splitlines()
    if len(lines) != file_count:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest line count does not match file_count')
    manifest = {}
    for line in lines:
        match = MANIFEST_LINE.fullmatch(line)
        if match is None:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest line is malformed')
        digest, name = match.groups()
        if name in manifest:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest contains a duplicate filename')
        manifest[name] = digest
    if manifest != verification_entries:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest and verification file hashes disagree')


def _validate_entry(reader, entry, *, app_identifier, group_key, group_name):
    if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive entry shape is invalid')
    start, end, expected = _fingerprint_key(entry['fingerprint'])
    if (start, end, expected) not in {_fingerprint_key(item) for item in REQUIRED_MANUAL_FINGERPRINTS}:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive fingerprint is outside the A56/B53 scope')
    if (start, end, expected) in {_fingerprint_key(item) for item in OWNER_EXCLUDED_FINGERPRINTS}:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Owner-excluded albums cannot be manual archives')
    if entry['provenance'] != PROVENANCE:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive provenance is invalid')
    try:
        recorded = dt.datetime.fromisoformat(entry['recorded_at'].replace('Z', '+00:00'))
    except (AttributeError, ValueError):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive recorded_at is invalid')
    if recorded.tzinfo is None:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive recorded_at lacks a timezone')
    for key in ('manifest_sha256', 'verification_sha256'):
        if not isinstance(entry[key], str) or SHA256.fullmatch(entry[key]) is None:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive digest is invalid')
    count = entry['file_count']
    total_bytes = entry['total_bytes']
    if type(count) is not int or count != expected:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive file_count disagrees with fingerprint')
    if type(total_bytes) is not int or total_bytes < 1:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive total_bytes is invalid')

    manifest_raw, _ = _read_bound(reader, entry['manifest_path'], 'MANUAL_ARCHIVE_REGISTRY_INVALID')
    verification_raw, _ = _read_bound(reader, entry['verification_path'], 'MANUAL_ARCHIVE_REGISTRY_INVALID')
    from .common import sha256_bytes
    if sha256_bytes(manifest_raw) != entry['manifest_sha256']:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manifest SHA-256 does not match the registry')
    if sha256_bytes(verification_raw) != entry['verification_sha256']:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification SHA-256 does not match the registry')

    verification = _strict_json(verification_raw, 'MANUAL_ARCHIVE_REGISTRY_INVALID')
    if (not isinstance(verification, dict)
            or verification.get('schema') != 'MANUAL_DIAGNOSTIC_ALBUM_VERIFICATION/1'
            or verification.get('mode') != 'MANUAL_DIAGNOSTIC_NOT_FORMAL_E2E'):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification identity is invalid')
    album = verification.get('album')
    if not isinstance(album, dict) or album.get('expected_images') != expected:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification album count disagrees with fingerprint')
    expected_label = f"{start.replace('-', '/')}～{end[5:].replace('-', '/')}"
    if 'dates' in album and album['dates'] != expected_label:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification album dates disagree with fingerprint')
    expected_destination = f"backups/{group_name}/{start}_{end}_{expected}張"
    if verification.get('destination_workspace_relative') != expected_destination:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification destination is not the canonical local archive path')
    files = verification.get('files')
    if not isinstance(files, dict) or set(files) != {'count', 'total_bytes', 'entries'}:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification files summary is invalid')
    if files['count'] != count or files['total_bytes'] != total_bytes:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification count or bytes disagree with the registry')
    entries = files['entries']
    if not isinstance(entries, list) or len(entries) != count:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification entries do not match file_count')
    by_name = {}
    rows_by_name = {}
    byte_total = 0
    for item in entries:
        if not isinstance(item, dict) or set(item) != {'file', 'bytes', 'sha256'}:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification file entry is invalid')
        name = item['file']
        if (not isinstance(name, str) or not name or name in ('.', '..') or '/' in name or '\x00' in name
                or type(item['bytes']) is not int or item['bytes'] < 1
                or not isinstance(item['sha256'], str) or SHA256.fullmatch(item['sha256']) is None
                or name in by_name):
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification file entry is unsafe or duplicated')
        by_name[name] = item['sha256']
        rows_by_name[name] = item
        byte_total += item['bytes']
    if byte_total != total_bytes:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Verification entry bytes do not sum to total_bytes')
    _validate_manifest(manifest_raw, by_name, count)
    names = reader.directory_names(expected_destination)
    if names != sorted(by_name):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive destination inventory differs from verification')
    for name in names:
        raw, _ = reader.read(expected_destination + '/' + name, 'MANUAL_ARCHIVE_REGISTRY_INVALID')
        row = rows_by_name[name]
        if len(raw) != row['bytes'] or sha256_bytes(raw) != row['sha256']:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive bytes differ from verification')
    return by_name


def _validate_registry_shape(registry, *, app_identifier, group_key):
    if not isinstance(registry, dict) or set(registry) != {
            'schema_version', 'kind', 'app_identifier', 'group_key', 'entries'}:
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive registry shape is invalid')
    if (registry['schema_version'] != REGISTRY_VERSION
            or registry['kind'] != 'manual_archive_registry'
            or registry['app_identifier'] != app_identifier
            or registry['group_key'] != group_key):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive registry identity is invalid')
    prefix = f'line:{app_identifier}:'
    if not isinstance(group_key, str) or not group_key.startswith(prefix) or len(group_key) == len(prefix):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive group key is invalid')
    if not isinstance(registry['entries'], list):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive entries are invalid')
    return group_key[len(prefix):]


def _write_registry(root, registry):
    import os
    import stat
    import uuid

    from .common import json_bytes
    from .project_binding import ProjectReader

    reader = ProjectReader(root)
    parent = None
    fd = None
    temporary = None
    replaced = False
    try:
        parent = reader.open('state', directory=True)
        temporary = '.manual_archives.json-' + uuid.uuid4().hex + '.tmp'
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        owner = os.fstat(fd)
        raw = json_bytes(registry)
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
        current = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (owner.st_dev, owner.st_ino):
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive registry temporary file changed')
        os.replace(temporary, 'manual_archives.json', src_dir_fd=parent, dst_dir_fd=parent)
        replaced = True
        os.fsync(parent)
    finally:
        if fd is not None:
            os.close(fd)
        if parent is not None and temporary is not None and not replaced:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        if parent is not None:
            os.close(parent)
        reader.close()


def record_manual_archives(project_root, records, *, recorded_at=None):
    """Record exact local manual archives, then reload the written registry."""
    from .common import sha256_bytes
    from .project_binding import CONFIG_PATH, ProjectReader, strict_json, validate_config

    if not isinstance(records, list) or not records:
        _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'At least one manual archive record is required')
    reader = ProjectReader(project_root)
    try:
        cfg = strict_json(reader.read(CONFIG_PATH)[0], 'INVALID_CONFIG')
        validate_config(cfg, project_root)
        group_name = _validate_registry_shape({
            'schema_version': REGISTRY_VERSION,
            'kind': 'manual_archive_registry',
            'app_identifier': cfg['app_identifier'],
            'group_key': cfg['group_key'],
            'entries': [],
        }, app_identifier=cfg['app_identifier'], group_key=cfg['group_key'])
        existing = _read_registry(reader, False)
        entries = {}
        if existing is not None:
            current = _strict_json(existing, 'MANUAL_ARCHIVE_REGISTRY_INVALID')
            _validate_registry_shape(current, app_identifier=cfg['app_identifier'], group_key=cfg['group_key'])
            for entry in current['entries']:
                _validate_entry(reader, entry, app_identifier=cfg['app_identifier'],
                                group_key=cfg['group_key'], group_name=group_name)
                key = _fingerprint_key(entry['fingerprint'])
                if key in entries:
                    _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive fingerprint is duplicated')
                entries[key] = entry
        required_keys = {_fingerprint_key(item) for item in REQUIRED_MANUAL_FINGERPRINTS}
        incoming = set()
        for record in records:
            if not isinstance(record, dict) or set(record) != RECORD_KEYS:
                _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'Manual archive record shape is invalid')
            key = _fingerprint_key(record['fingerprint'])
            if key not in required_keys:
                _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'Manual archive record is outside the A56/B53 scope')
            if key in incoming:
                _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'Manual archive record fingerprint is duplicated')
            incoming.add(key)
            start, end, expected = key
            destination = _relative_path(reader, record['destination'])
            expected_destination = f"backups/{group_name}/{start}_{end}_{expected}張"
            if destination != expected_destination:
                _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'Manual archive destination is not canonical')
            manifest_path = _relative_path(reader, record['manifest_path'])
            verification_path = _relative_path(reader, record['verification_path'])
            manifest_raw, _ = reader.read(manifest_path, 'MANUAL_ARCHIVE_RECORD_INVALID')
            verification_raw, _ = reader.read(verification_path, 'MANUAL_ARCHIVE_RECORD_INVALID')
            stamp = recorded_at or dt.datetime.now(dt.timezone.utc).isoformat()
            entry = {
                'fingerprint': dict(record['fingerprint']),
                'provenance': PROVENANCE,
                'recorded_at': stamp,
                'manifest_path': manifest_path,
                'manifest_sha256': sha256_bytes(manifest_raw),
                'verification_path': verification_path,
                'verification_sha256': sha256_bytes(verification_raw),
                'file_count': expected,
                'total_bytes': 0,
            }
            verification = _strict_json(verification_raw, 'MANUAL_ARCHIVE_RECORD_INVALID')
            files = verification.get('files') if isinstance(verification, dict) else None
            if not isinstance(files, dict) or set(files) != {'count', 'total_bytes', 'entries'}:
                _fail('MANUAL_ARCHIVE_RECORD_INVALID', 'Verification files summary is invalid')
            entry['total_bytes'] = files['total_bytes']
            _validate_entry(reader, entry, app_identifier=cfg['app_identifier'],
                            group_key=cfg['group_key'], group_name=group_name)
            entries[key] = entry
        registry = {
            'schema_version': REGISTRY_VERSION,
            'kind': 'manual_archive_registry',
            'app_identifier': cfg['app_identifier'],
            'group_key': cfg['group_key'],
            'entries': [entries[key] for key in sorted(entries)],
        }
    finally:
        reader.close()
    _write_registry(project_root, registry)
    check = ProjectReader(project_root)
    try:
        fingerprints = load_manual_archives(check, app_identifier=cfg['app_identifier'], group_key=cfg['group_key'],
                                            required=True, required_fingerprints=tuple(dict(record['fingerprint']) for record in records))
    finally:
        check.close()
    return dict(status='MANUAL_ARCHIVE_REGISTRY_RECORDED', fingerprints=[list(item) for item in sorted(fingerprints)],
                state_modified=False)


def load_manual_archives(reader, *, app_identifier, group_key, required=False,
                         required_fingerprints=()):
    """Return the exact manual fingerprints after re-reading every bound byte."""
    raw = _read_registry(reader, required)
    if raw is None:
        return frozenset()
    registry = _strict_json(raw, 'MANUAL_ARCHIVE_REGISTRY_INVALID')
    group_name = _validate_registry_shape(registry, app_identifier=app_identifier, group_key=group_key)
    entries = registry['entries']
    if not isinstance(entries, list):
        _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive entries are invalid')
    fingerprints = set()
    for entry in entries:
        _validate_entry(reader, entry, app_identifier=app_identifier,
                        group_key=group_key, group_name=group_name)
        key = _fingerprint_key(entry['fingerprint'])
        if key in fingerprints:
            _fail('MANUAL_ARCHIVE_REGISTRY_INVALID', 'Manual archive fingerprint is duplicated')
        fingerprints.add(key)
    required_keys = {_fingerprint_key(item) for item in required_fingerprints}
    if required and not required_keys.issubset(fingerprints):
        _fail('MANUAL_ARCHIVE_REGISTRY_REQUIRED', 'Required manual archive fingerprints are missing')
    return frozenset(fingerprints)
