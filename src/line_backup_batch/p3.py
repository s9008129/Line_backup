"""Fail-closed scoped P3 authorization adapter for daily album records.

This module never controls LINE. Production authority verification is deliberately
an interface only until a genuine human/reviewer channel is installed.
"""
from __future__ import annotations

import fcntl
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
import uuid
import re
import shutil
import sys

from line_backup_acceptance.project_binding import strict_json
from . import daily

SCHEMA = 'line-backup-p3-scoped-authorization/v1'
def _source_paths(repo):
    paths = {str(path.relative_to(repo)) for folder in
             ('src/line_backup_batch', 'src/line_backup_acceptance')
             for path in (repo / folder).rglob('*.py') if path.is_file() and not path.is_symlink()}
    skill = repo / '.agents/skills/line-album-agent-cua'
    paths.update(str(path.relative_to(repo)) for path in skill.rglob('*.md')
                 if path.is_file() and not path.is_symlink())
    paths.update(('scripts/line_backup_cua_adapter.mjs', 'src/line_backup_batch/image_decode.swift',
                  'src/line_backup_batch/p3.py'))
    return tuple(sorted(paths))


def _runtime_roles():
    roles = {'python': str(Path(sys.executable).resolve(strict=True))}
    for name in ('node', 'openssl', 'security'):
        resolved = shutil.which(name)
        require(resolved is not None, 'RUNTIME_' + name.upper() + '_MISSING')
        roles[name] = str(Path(resolved).resolve(strict=True))
    return roles


class P3Error(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise P3Error(code)


def _source_closure(repo):
    result = {}
    for relative in _source_paths(repo):
        path = repo / relative
        raw = daily.read_file(path)
        result[relative] = {'bytes': len(raw), 'sha256': daily.digest(raw)}
    return result


def _commit(repo):
    try:
        value = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                               check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        require(False, 'IMPLEMENTATION_COMMIT_UNAVAILABLE')
    require(len(value) == 40 and all(c in '0123456789abcdef' for c in value),
            'IMPLEMENTATION_COMMIT_UNAVAILABLE')
    return value


def _source_is_clean(repo):
    result = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain', '--', *_source_paths(repo)],
                            capture_output=True, text=True, timeout=5)
    require(result.returncode == 0, 'GIT_SOURCE_STATUS_UNAVAILABLE')
    require(not result.stdout.strip(), 'IMPLEMENTATION_SOURCE_NOT_COMMITTED')


def _uuid(value, code):
    require(isinstance(value, str) and re.fullmatch(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value), code)


def _verify_runtime(repo, manifest_path, source_closure):
    manifest = strict_json(daily.read_file(manifest_path), 'INVALID_RUNTIME_MANIFEST')
    require(isinstance(manifest, dict) and set(manifest) == {'version', 'files', 'runtime_roles'} and
            manifest.get('version') == 1 and isinstance(manifest.get('files'), list), 'RUNTIME_MANIFEST_SCHEMA')
    roles = manifest.get('runtime_roles')
    require(isinstance(roles, dict) and roles.get('image_decoder'), 'RUNTIME_MANIFEST_SCHEMA')
    decoder_path = Path(roles['image_decoder'])
    require(decoder_path == decoder_path.resolve(strict=True) and decoder_path.name == 'image_decode'
            and decoder_path.is_file() and os.access(decoder_path, os.X_OK), 'IMAGE_DECODER_RUNTIME_INVALID')
    expected_roles = dict(_runtime_roles(), image_decoder=str(decoder_path))
    require(roles == expected_roles, 'RUNTIME_MANIFEST_SCHEMA')
    found = {}
    for item in manifest['files']:
        require(isinstance(item, dict) and set(item) == {'path', 'bytes', 'sha256'}, 'RUNTIME_FILE_SCHEMA')
        name = item['path']
        require(isinstance(name, str) and name not in found, 'RUNTIME_DUPLICATE_PATH')
        path = Path(name) if Path(name).is_absolute() else repo / name
        require(path == path.resolve(strict=True) and path.is_file(), 'RUNTIME_FILE_PATH_INVALID')
        raw = daily.read_file(path)
        require(type(item['bytes']) is int and item['bytes'] == len(raw) and
                item['sha256'] == daily.digest(raw), 'RUNTIME_FILE_HASH_MISMATCH')
        found[name] = item
    for name, fact in source_closure.items():
        require(found.get(name) == {'path': name, **fact}, 'RUNTIME_CLOSURE_INCOMPLETE')
    role_paths = list(manifest['runtime_roles'].values())
    require(len(role_paths) == len(set(role_paths)), 'RUNTIME_ROLE_PATH_COLLISION')
    for name in role_paths:
        require(name in found, 'RUNTIME_EXECUTABLE_NOT_HASHED')
    return manifest


def mount_identity(path):
    """Return a stable path/device/inode mount witness; fail if lookup is unclear."""
    path = Path(path).resolve(strict=True)
    info = path.stat()
    current = path
    mountpoint = None
    while current.parent != current:
        if current.parent.stat().st_dev != info.st_dev:
            mountpoint = str(current)
            break
        current = current.parent
    if mountpoint is None:
        mountpoint = str(current)
    return {'canonical_path': str(path), 'device': info.st_dev, 'inode': info.st_ino,
            'mountpoint': mountpoint, 'mounted': os.path.ismount(mountpoint)}


def prepare(root, *, session_id, identity, owner_request, foreground_evidence,
            history_scope_evidence, runtime_manifest, recovery_authorization=None):
    """Build review input only. Does not mint authority or create an intent."""
    store = daily.DailyRecords(root)
    with store.locked():
        store.bound(session_id)
        key = daily.album_key(identity)
        require(key in {k for page in store.pages() for k in page['keys']}, 'TARGET_NOT_IN_CURRENT_SCAN')
        require(store.status_map().get(key) == 'INCOMPLETE', 'TARGET_NOT_ELIGIBLE_FOR_REQUEST')
        prior = [item for item in store.matching('intent') if item['album_key'] == key]
        recovery_ref = None
        recovery_of = None
        if prior:
            outcomes = [item for item in store.matching('outcome')
                        if item['attempt_id'] == prior[-1]['attempt_id']]
            require(outcomes and outcomes[-1]['outcome'] in ('STOPPED', 'NOT_SENT'),
                    'UNKNOWN_OR_RUNNING_NO_REPLAY')
            daily.check_ref(outcomes[-1]['evidence'])
            require(recovery_authorization is not None, 'ALBUM_RECOVERY_AUTHORIZATION_REQUIRED')
            recovery_doc = strict_json(daily.read_file(recovery_authorization), 'INVALID_RECOVERY_AUTHORIZATION')
            require(recovery_doc.get('decision') == 'AUTHORIZE_ALBUM_RECOVERY' and
                    recovery_doc.get('local_group_id') == store.group['local_group_id'] and
                    recovery_doc.get('album_key') == key and
                    recovery_doc.get('previous_attempt_id') == prior[-1]['attempt_id'] and
                    recovery_doc.get('preserve_existing') is True, 'RECOVERY_AUTHORIZATION_SCOPE_MISMATCH')
            daily.check_ref(recovery_doc['owner_source'])
            recovery_ref = daily.reference(recovery_authorization)
            recovery_of = prior[-1]['attempt_id']
        else:
            require(recovery_authorization is None, 'NO_PRIOR_ATTEMPT_TO_RECOVER')
        require(store.matching('history'), 'HISTORY_RECONCILIATION_REQUIRED')
        _reject_incomplete_reservations(store.records)
        root_path = store.root
        closure = _source_closure(Path(__file__).resolve().parents[2])
        runtime_ref = daily.reference(runtime_manifest)
        _verify_runtime(Path(__file__).resolve().parents[2], runtime_manifest, closure)
        runtime_doc = strict_json(daily.read_file(runtime_manifest), 'INVALID_RUNTIME_MANIFEST')
        decoder_path = runtime_doc['runtime_roles']['image_decoder']
        decoder_ref = daily.reference(decoder_path)
        require(runtime_doc['runtime_roles']['image_decoder'] == decoder_ref['path'],
                'IMAGE_DECODER_RUNTIME_INVALID')
        destination = mount_identity(root_path)
        require(destination['mounted'], 'DESTINATION_VOLUME_NOT_MOUNTED')
        return {'schema': SCHEMA, 'phase': 'PREPARED_FOR_EXTERNAL_REVIEW',
                'grant_id': str(uuid.uuid4()), 'nonce': str(uuid.uuid4()),
                'issued_at_epoch': int(time.time()), 'max_save_all_dispatches': 1,
                'attempt_scope': 'ONE_NEW_ALBUM_ATTEMPT',
                'implementation_commit_sha': _commit(Path(__file__).resolve().parents[2]),
                'local_group_id': store.group['local_group_id'], 'session_id': session_id,
                'identity': identity, 'album_key': key,
                'recovery_of': recovery_of, 'recovery_authorization': recovery_ref,
                'destination': destination,
                'owner_request': daily.reference(owner_request),
                'foreground_evidence': daily.reference(foreground_evidence),
                'history_scope_evidence': daily.reference(history_scope_evidence),
                'record_head_sha256': store.previous, 'source_closure': closure,
                'runtime_manifest': runtime_ref,
                'runtime_closure_sha256': daily.digest(daily.read_file(runtime_manifest)),
                'runtime_decoder': decoder_ref,
                'external_implementation_review': None, 'owner_l2': None,
                'dispatch_authorized': False}


class ProductionAuthorityVerifier:
    """Verify separated Ed25519 roles against public keys installed in macOS Keychain.

    A caller cannot supply keys or replace this verifier through the production CLI.
    Until the owner/reviewer public keys are installed, the operation fails closed.
    """
    def __init__(self):
        self._fingerprints = {}
        self._role_keys = None

    def _trusted_role_keys(self):
        if self._role_keys is not None:
            return self._role_keys
        result = {}
        for role in ('reviewer', 'owner', 'runtime'):
            try:
                key = subprocess.run(['security', 'find-generic-password', '-s',
                                      'line-backup-p3-' + role + '-public-key', '-w'],
                                     check=True, capture_output=True, timeout=5).stdout
            except (OSError, subprocess.SubprocessError):
                raise P3Error('TRUSTED_' + role.upper() + '_KEY_UNAVAILABLE')
            require(key.startswith(b'-----BEGIN PUBLIC KEY-----'), 'TRUSTED_KEY_FORMAT_INVALID')
            result[role] = key
        fingerprints = {role: hashlib.sha256(key).hexdigest() for role, key in result.items()}
        require(len(set(fingerprints.values())) == 3, 'AUTHORITY_ROLE_COLLISION')
        self._fingerprints = fingerprints
        self._role_keys = result
        return result

    def _verify(self, role, evidence, expected):
        require(isinstance(evidence, dict) and set(evidence) == {'claims', 'signature_base64'},
                'SIGNED_AUTHORITY_EVIDENCE_REQUIRED')
        claims = evidence['claims']
        require(isinstance(claims, dict) and claims.get('bindings') == expected,
                'SIGNED_AUTHORITY_BINDING_MISMATCH')
        key = self._trusted_role_keys()[role]
        try:
            signature = base64.b64decode(evidence['signature_base64'], validate=True)
        except (ValueError, TypeError):
            require(False, 'AUTHORITY_SIGNATURE_INVALID')
        raw = daily.encoded(claims)
        with tempfile.TemporaryDirectory(prefix='line-p3-verify-') as temp:
            key_path, data_path, sig_path = (Path(temp) / name for name in ('key.pem', 'claims.json', 'sig.bin'))
            key_path.write_bytes(key)
            data_path.write_bytes(raw)
            sig_path.write_bytes(signature)
            try:
                checked = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(key_path),
                                          '-rawin', '-in', str(data_path), '-sigfile', str(sig_path)],
                                         capture_output=True, timeout=5)
            except (OSError, subprocess.SubprocessError):
                raise P3Error('SIGNATURE_VERIFIER_UNAVAILABLE')
        require(checked.returncode == 0, 'AUTHORITY_SIGNATURE_INVALID')
        require(claims.get('role') == role, 'AUTHORITY_ROLE_MISMATCH')
        return claims

    def verify_review(self, evidence, expected):
        return self._verify('reviewer', evidence, expected)

    def verify_owner_l2(self, evidence, expected):
        return self._verify('owner', evidence, expected)

    def verify_runtime_receipt(self, evidence, expected):
        return self._verify('runtime', evidence, expected)


def _destination_still_matches(store, expected):
    observed = mount_identity(store.root)
    require(observed == expected, 'DESTINATION_MOUNT_OR_INODE_CHANGED')


def _probe_filesystem(path):
    """Exercise exclusive create, hard-link no-replace, file/dir fsync, and readback."""
    path = Path(path)
    require(path == path.resolve(strict=True) and path.is_dir(), 'P3_DIRECTORY_REPLACED')
    probe = path / ('.probe-' + uuid.uuid4().hex)
    linked = path / ('.probe-link-' + uuid.uuid4().hex)
    raw = b'line-backup-p3-fs-capability/v1\n'
    fd = os.open(str(probe), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        before = os.fstat(fd)
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(probe, linked, follow_symlinks=False)
        daily.sync_dir(path)
        require(linked.read_bytes() == raw, 'P3_FILESYSTEM_PROBE_READBACK')
        require(os.stat(probe, follow_symlinks=False).st_ino == before.st_ino and
                os.stat(linked, follow_symlinks=False).st_ino == before.st_ino,
                'P3_FILESYSTEM_PROBE_LINK_MISMATCH')
    finally:
        os.close(fd)
        for item in (linked, probe):
            try:
                item.unlink()
            except FileNotFoundError:
                pass
        daily.sync_dir(path)


def _validate_bundle(repo, store, prepared, bundle, verifier, now):
    require(prepared.get('schema') == SCHEMA and prepared.get('phase') == 'PREPARED_FOR_EXTERNAL_REVIEW',
            'PREPARED_SCHEMA_INVALID')
    require(prepared.get('dispatch_authorized') is False, 'PREPARED_AUTHORITY_INVALID')
    require(type(prepared.get('issued_at_epoch')) is int and prepared['issued_at_epoch'] <= now,
            'PREPARED_ISSUED_IN_FUTURE')
    if not getattr(verifier, 'test_only', False):
        _source_is_clean(repo)
    require(prepared.get('implementation_commit_sha') == _commit(repo), 'IMPLEMENTATION_COMMIT_MISMATCH')
    require(prepared.get('source_closure') == _source_closure(repo), 'SOURCE_CLOSURE_MISMATCH')
    require(prepared.get('local_group_id') == store.group['local_group_id'], 'WRONG_LOCAL_GROUP')
    require(prepared.get('destination') == mount_identity(store.root), 'DESTINATION_MOUNT_OR_INODE_CHANGED')
    require(prepared['destination'].get('mounted') is True, 'DESTINATION_VOLUME_NOT_MOUNTED')
    _uuid(prepared.get('grant_id'), 'GRANT_ID_INVALID')
    _uuid(prepared.get('nonce'), 'NONCE_INVALID')
    require(type(prepared.get('max_save_all_dispatches')) is int and prepared.get('max_save_all_dispatches') == 1 and
            prepared.get('attempt_scope') == 'ONE_NEW_ALBUM_ATTEMPT', 'ATTEMPT_SCOPE_INVALID')
    for name in ('owner_request', 'foreground_evidence', 'history_scope_evidence', 'runtime_manifest'):
        daily.check_ref(prepared[name])
    runtime_raw = daily.read_file(prepared['runtime_manifest']['path'])
    require(daily.digest(runtime_raw) == prepared.get('runtime_closure_sha256'), 'RUNTIME_CLOSURE_MISMATCH')
    runtime_doc = _verify_runtime(repo, prepared['runtime_manifest']['path'], prepared['source_closure'])
    require(prepared.get('runtime_decoder') == daily.reference(runtime_doc['runtime_roles']['image_decoder']),
            'IMAGE_DECODER_RUNTIME_MISMATCH')
    require(bundle.get('schema') == SCHEMA and bundle.get('nonce') == prepared.get('nonce'), 'NONCE_MISMATCH')
    require(bundle.get('grant_id') == prepared['grant_id'], 'GRANT_ID_MISMATCH')
    require(type(bundle.get('expires_at_epoch')) is int and now <= bundle['expires_at_epoch']
            and bundle['expires_at_epoch'] > prepared['issued_at_epoch'], 'AUTHORIZATION_EXPIRED')
    expected = {key: prepared[key] for key in (
        'implementation_commit_sha', 'local_group_id', 'session_id', 'album_key', 'destination',
        'runtime_closure_sha256', 'runtime_decoder', 'source_closure', 'nonce', 'grant_id', 'issued_at_epoch',
        'owner_request', 'foreground_evidence', 'history_scope_evidence', 'record_head_sha256')}
    expected['recovery_of'] = prepared.get('recovery_of')
    expected['recovery_authorization'] = prepared.get('recovery_authorization')
    expected['expires_at_epoch'] = bundle['expires_at_epoch']
    expected['max_save_all_dispatches'] = prepared['max_save_all_dispatches']
    expected['attempt_scope'] = prepared['attempt_scope']
    review = verifier.verify_review(bundle.get('implementation_review'), expected)
    require(isinstance(review, dict) and review.get('decision') == 'APPROVE_IMPLEMENTATION',
            'IMPLEMENTATION_REVIEW_NOT_APPROVED')
    require(review.get('implementation_commit_sha') == expected['implementation_commit_sha'] and
            review.get('source_closure') == expected['source_closure'], 'REVIEW_BINDING_MISMATCH')
    owner = verifier.verify_owner_l2(bundle.get('owner_l2'), expected)
    require(isinstance(owner, dict) and owner.get('decision') == 'AUTHORIZE_SCOPED_L2',
            'OWNER_L2_NOT_AUTHORIZED')
    for key in ('local_group_id', 'session_id', 'album_key', 'destination', 'nonce'):
        require(owner.get(key) == expected[key], 'OWNER_L2_SCOPE_MISMATCH')
    require(type(owner.get('expires_at_epoch')) is int and now <= owner['expires_at_epoch']
            and owner['expires_at_epoch'] == bundle['expires_at_epoch'], 'OWNER_L2_EXPIRED')
    return review, owner


def reserve(root, prepared_path, bundle_path, *, verifier=None, now=None,
            recovery_authorization=None):
    """Validate all bindings, burn nonce durably, then create one daily reservation.

    A failure after nonce burn is intentionally non-replayable. This operation never
    authorizes GUI dispatch; it only reserves one attempt for an external runtime.
    """
    verifier = verifier or ProductionAuthorityVerifier()
    now = int(time.time()) if now is None else now
    store = daily.DailyRecords(root)
    prepared = strict_json(daily.read_file(prepared_path), 'INVALID_PREPARED_REQUEST')
    bundle = strict_json(daily.read_file(bundle_path), 'INVALID_AUTHORITY_BUNDLE')
    # Read-only validation runs before either attempt record or destination mutation.
    with store.locked():
        store.bound(prepared.get('session_id'))
        _reject_incomplete_reservations(store.records)
        _uuid(prepared.get('nonce'), 'NONCE_INVALID')
        review, owner = _validate_bundle(Path(__file__).resolve().parents[2], store,
                                         prepared, bundle, verifier, now)
        entries = _reservation_entries(store.records / 'p3-reservations')
        require(not any(entry.get('nonce') == prepared['nonce'] for entry in entries), 'NONCE_ALREADY_RESERVED')
        require(not any(entry.get('grant_id') == prepared['grant_id'] for entry in entries),
                'GRANT_ALREADY_RESERVED')
        require(store.previous == prepared.get('record_head_sha256'), 'PREPARED_RECORD_HEAD_STALE')
        require(prepared.get('identity') and daily.album_key(prepared['identity']) == prepared.get('album_key'),
                'ALBUM_BINDING_MISMATCH')
        require(store.status_map().get(prepared['album_key']) == 'INCOMPLETE', 'TARGET_NOT_ELIGIBLE_FOR_REQUEST')
        details = store.matching('detail')
        require(details and details[-1]['album_key'] == prepared['album_key'], 'FRESH_DETAIL_REQUIRED')
        daily.check_ref(details[-1]['evidence'])
        _destination_still_matches(store, prepared['destination'])
    p3dir = store.records / 'p3-reservations'
    if not p3dir.exists():
        p3dir.mkdir(mode=0o700)
        daily.sync_dir(store.records)
    require(p3dir == p3dir.resolve(strict=True) and p3dir.parent == p3dir.parent.resolve(strict=True),
            'P3_DIRECTORY_SYMLINK_OR_REPLACEMENT')
    _probe_filesystem(p3dir)
    lock_path = p3dir / '.lock'
    lockfd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        require(stat.S_ISREG(os.fstat(lockfd).st_mode) and os.fstat(lockfd).st_nlink == 1, 'UNSAFE_P3_LOCK')
        fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked_identity = p3dir.stat()
        require(locked_identity.st_ino == os.stat(p3dir, follow_symlinks=False).st_ino and
                p3dir == p3dir.resolve(strict=True), 'P3_DIRECTORY_REPLACED')
        require(not any(entry.get('nonce') == prepared['nonce'] for entry in _reservation_entries(p3dir)),
                'NONCE_ALREADY_RESERVED')
        require(not any(entry.get('grant_id') == prepared['grant_id'] for entry in _reservation_entries(p3dir)),
                'GRANT_ALREADY_RESERVED')
        if prepared.get('recovery_authorization'):
            daily.check_ref(prepared['recovery_authorization'])
            require(recovery_authorization == prepared['recovery_authorization']['path'],
                    'RECOVERY_AUTHORIZATION_MISMATCH')
        else:
            require(recovery_authorization is None, 'RECOVERY_AUTHORIZATION_MISMATCH')
        # Persist nonce burn before asking DailyRecords to create an intent.
        marker = {'schema': SCHEMA, 'grant_id': prepared['grant_id'],
                  'nonce': prepared['nonce'], 'status': 'RESERVATION_STARTED',
                  'local_group_id': prepared['local_group_id'], 'album_key': prepared['album_key'],
                  'session_id': prepared['session_id'], 'implementation_commit_sha': prepared['implementation_commit_sha'],
                  'destination': prepared['destination'],
                  'runtime_closure_sha256': prepared['runtime_closure_sha256'],
                  'runtime_decoder': prepared['runtime_decoder'],
                  'runtime_manifest': prepared['runtime_manifest'],
                  'source_closure': prepared['source_closure'],
                  'owner_request': prepared['owner_request'],
                  'foreground_evidence': prepared['foreground_evidence'],
                  'history_scope_evidence': prepared['history_scope_evidence'],
                  'record_head_sha256': prepared['record_head_sha256'],
                  'recovery_of': prepared.get('recovery_of'),
                  'review_sha256': daily.digest(daily.encoded(bundle['implementation_review'])),
                  'owner_l2_sha256': daily.digest(daily.encoded(bundle['owner_l2'])),
                  'created_at_epoch': now, 'dispatch_authorized': False}
        _exclusive_durable(p3dir / (prepared['nonce'] + '.json'), marker)
        intent = store.intent(session_id=prepared['session_id'], identity=prepared['identity'],
                              recovery_authorization=recovery_authorization)
        # Marker is append-only: complete binding as second event rather than replace.
        _exclusive_durable(p3dir / (prepared['nonce'] + '.reserved.json'),
                           {'schema': SCHEMA, 'nonce': prepared['nonce'],
                            'attempt_id': intent['attempt_id'], 'destination': intent['destination'],
                            'review_decision': review['decision'], 'owner_decision': owner['decision'],
                            'dispatch_authorized': False})
        return {'status': 'RESERVED_NO_DISPATCH', 'attempt': intent,
                'dispatch_authorized': False, 'save_all_dispatch_allowed': False}
    finally:
        os.close(lockfd)


def _exclusive_durable(path, value):
    """Hard-link publish + fsync file and parent; never overwrite a receipt."""
    raw = daily.encoded(value)
    pending = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(pending), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(str(pending), str(path), follow_symlinks=False)
        daily.sync_dir(path.parent)
    finally:
        os.close(fd)
    pending.unlink()
    daily.sync_dir(path.parent)
    require(daily.read_file(path) == raw, 'P3_RESERVATION_READBACK_FAILED')


def _reservation_entries(path):
    if not path.exists():
        return []
    result = []
    for entry in path.glob('*.json'):
        if entry.name.endswith('.reserved.json'):
            continue
        result.append(strict_json(daily.read_file(entry), 'P3_RESERVATION_CORRUPT'))
    return result


def _reject_incomplete_reservations(records):
    path = Path(records) / 'p3-reservations'
    if not path.exists():
        return
    require(path == path.resolve(strict=True) and path.is_dir(), 'P3_DIRECTORY_SYMLINK_OR_REPLACEMENT')
    for marker_path in sorted(path.glob('*.json')):
        if marker_path.name.endswith(('.reserved.json', '.verified.json')):
            continue
        marker = strict_json(daily.read_file(marker_path), 'P3_RESERVATION_CORRUPT')
        if marker.get('status') == 'RESERVATION_STARTED':
            require((path / (marker['nonce'] + '.reserved.json')).is_file(),
                    'P3_RESERVATION_INCOMPLETE_NO_REPLAY')


def finalize(root, *, nonce, receipt_path, decoder, decoder_sha256, verifier=None):
    """Validate a signed runtime receipt, use existing ImageIO verification, read back.

    This records MANUAL_DIAGNOSTIC completion in daily records. It never changes
    the formal VERIFIED store or creates LINE GUI input capability.
    """
    verifier = verifier or ProductionAuthorityVerifier()
    _uuid(nonce, 'NONCE_INVALID')
    store = daily.DailyRecords(root)
    p3dir = store.records / 'p3-reservations'
    started_path = p3dir / (nonce + '.json')
    reserved_path = p3dir / (nonce + '.reserved.json')
    started = strict_json(daily.read_file(started_path), 'P3_RESERVATION_MISSING')
    reserved = strict_json(daily.read_file(reserved_path), 'P3_ATTEMPT_RESERVATION_MISSING')
    require(started.get('nonce') == nonce and started.get('status') == 'RESERVATION_STARTED' and
            reserved.get('nonce') == nonce and reserved.get('attempt_id'), 'P3_RESERVATION_BINDING_MISMATCH')
    attempt_id = reserved['attempt_id']
    repo = Path(__file__).resolve().parents[2]
    require(started.get('schema') == SCHEMA, 'P3_RESERVATION_BINDING_MISMATCH')
    require(started.get('destination') == mount_identity(store.root), 'DESTINATION_MOUNT_OR_INODE_CHANGED')
    require(started.get('source_closure') == _source_closure(repo), 'SOURCE_CLOSURE_MISMATCH')
    runtime_ref = started.get('runtime_manifest')
    daily.check_ref(runtime_ref)
    runtime_raw = daily.read_file(runtime_ref['path'])
    require(daily.digest(runtime_raw) == started.get('runtime_closure_sha256'), 'RUNTIME_CLOSURE_MISMATCH')
    _verify_runtime(repo, runtime_ref['path'], started['source_closure'])
    decoder_ref = started.get('runtime_decoder')
    require(isinstance(decoder_ref, dict) and daily.reference(decoder) == decoder_ref,
            'IMAGE_DECODER_RUNTIME_MISMATCH')
    require(decoder_sha256 == decoder_ref['sha256'], 'IMAGE_DECODER_RUNTIME_MISMATCH')
    with store.locked():
        require(started.get('local_group_id') == store.group['local_group_id'],
                'P3_RESERVATION_BINDING_MISMATCH')
        attempts = store.matching('intent')
        require(attempts and attempts[-1]['attempt_id'] == attempt_id, 'ONLY_LATEST_ATTEMPT_CAN_COMPLETE')
        target = attempts[-1]
        require(target['destination'] == reserved.get('destination') and
                target['album_key'] == started.get('album_key') and
                target['session_id'] == started.get('session_id'), 'P3_ATTEMPT_BINDING_MISMATCH')
        expected = {'nonce': nonce, 'attempt_id': attempt_id,
                    'local_group_id': store.group['local_group_id'],
                    'album_key': target['album_key'], 'destination': target['destination'],
                    'runtime_closure_sha256': started['runtime_closure_sha256'],
                    'dispatch_count': 1, 'outcome': 'DOWNLOAD_FINISHED'}
    receipt_ref = daily.reference(receipt_path)
    receipt = strict_json(daily.read_file(receipt_path), 'INVALID_RUNTIME_RECEIPT')
    claims = verifier.verify_runtime_receipt(receipt, expected)
    require(isinstance(claims, dict) and claims.get('outcome') == 'DOWNLOAD_FINISHED' and
            claims.get('dispatch_count') == 1 and claims.get('nonce') == nonce and
            claims.get('attempt_id') == attempt_id, 'RUNTIME_RECEIPT_SCOPE_MISMATCH')
    store.outcome(session_id=target['session_id'], attempt_id=attempt_id,
                  outcome='DOWNLOAD_FINISHED', evidence=receipt_path)
    completed = store.complete(session_id=target['session_id'], attempt_id=attempt_id,
                               decoder=decoder, decoder_sha256=decoder_sha256)
    result_path = p3dir / (nonce + '.verified.json')
    _exclusive_durable(result_path, {'schema': SCHEMA, 'nonce': nonce, 'attempt_id': attempt_id,
        'receipt': receipt_ref, 'completion_event_sequence': len(store.events),
        'completion_manifest_sha256': completed['proof']['manifest_sha256'],
        'execution_lane': 'MANUAL_DIAGNOSTIC', 'formal_auto_verified': False,
        'dispatch_authorized': False})
    reread_store = daily.DailyRecords(root)
    reread = reread_store.summary()
    with reread_store.locked():
        reread_status = reread_store.status_map().get(target['album_key'])
    require(reread_status == 'COMPLETED' and
            reread['COMPLETED'] >= 1 and reread['real_line_e2e'] == 'NOT_TESTED' and
            reread['formal_auto_verified'] is False, 'COMPLETION_READBACK_FAILED')
    return {'status': 'FILES_VERIFIED_READBACK', 'attempt_id': attempt_id,
            'execution_lane': 'MANUAL_DIAGNOSTIC', 'formal_auto_verified': False,
            'dispatch_authorized': False, 'summary': reread}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'reserve', 'finalize'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--input', required=True)
    ns = parser.parse_args(argv)
    try:
        data = strict_json(daily.read_file(ns.input), 'INVALID_INPUT')
        if ns.operation == 'reserve':
            result = reserve(ns.root, data['prepared_path'], data['bundle_path'],
                             recovery_authorization=data.get('recovery_authorization'))
        elif ns.operation == 'finalize':
            result = finalize(ns.root, **data)
        else:
            result = prepare(ns.root, **data)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (P3Error, daily.DailyError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'REFUSED', 'reason': str(exc), 'dispatch_authorized': False}))
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
