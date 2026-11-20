"""Immutable, one-level evidence bundles for the Notes ledger.

Evidence bundles describe mechanical byte references. They do not prove that a
GUI observation is true, that a control was hit, or that a terminal outcome
occurred. The Notes event log remains the business-state source.
"""
import json
import os
from pathlib import Path
import stat
import uuid

from .daily import DailyError, digest, encoded, strict_json, sync_dir


CORE_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_TASK_ROOT = CORE_ROOT / '.local' / 'line-backup' / 'tasks'
SCHEMA = 'line-notes-evidence/v2'
SCHEMA_FAMILY = 'line-notes-evidence/'
UNKNOWN = 'UNKNOWN'
CONTEXT_FIELDS = ('list_key', 'post_key', 'media_key', 'attempt_id', 'scan_id')
ASSET_ROLES = ('screenshot', 'ax', 'input_receipt', 'command_stdout',
               'command_stderr', 'observation')
STATEMENT_ROLE = 'statement'
REF_FIELDS = ('role', 'source_path', 'bytes', 'sha256')
OUTER_FIELDS = ('path', 'bytes', 'sha256')
EMPTY_ALLOWED_ROLES = frozenset(('command_stdout', 'command_stderr'))


class NotesEvidenceError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def need(condition, code):
    if not condition:
        raise NotesEvidenceError(code)


def _entry(path):
    try:
        return os.lstat(str(path))
    except FileNotFoundError:
        return None


def _canonical_directory(value, code):
    path = Path(value).expanduser()
    need(path.is_absolute(), code)
    entry = _entry(path)
    need(entry is not None and stat.S_ISDIR(entry.st_mode) and
         not stat.S_ISLNK(entry.st_mode), code)
    resolved = path.resolve(strict=True)
    need(resolved == path, code)
    return resolved


def _read_regular(path, code):
    path = Path(path)
    need(path.is_absolute(), code)
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise NotesEvidenceError(code) from exc
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, code)
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read()
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size,
              before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size,
              after.st_mtime_ns, after.st_ctime_ns), code)
        current = os.stat(str(path), follow_symlinks=False)
        need((current.st_dev, current.st_ino) == (after.st_dev, after.st_ino),
             code)
        return raw
    except NotesEvidenceError:
        raise
    except OSError as exc:
        raise NotesEvidenceError(code) from exc
    finally:
        os.close(fd)


def _project_source(value):
    path = Path(value).expanduser()
    need(path.is_absolute(), 'PROJECT_LOCAL_EVIDENCE_REQUIRED')
    try:
        resolved = path.resolve(strict=True)
    except (FileNotFoundError, NotADirectoryError, RuntimeError) as exc:
        raise NotesEvidenceError('EVIDENCE_SOURCE_MISSING') from exc
    need(resolved == path, 'EVIDENCE_SYMLINK_REFUSED')
    core = CORE_ROOT.resolve(strict=True)
    need(path.is_relative_to(core), 'PROJECT_LOCAL_EVIDENCE_REQUIRED')
    cursor = core
    for part in path.relative_to(core).parts:
        cursor = cursor / part
        info = _entry(cursor)
        need(info is not None and not stat.S_ISLNK(info.st_mode),
             'EVIDENCE_SYMLINK_REFUSED')
    need(stat.S_ISREG(resolved.stat().st_mode), 'REGULAR_EVIDENCE_REQUIRED')
    return resolved


def _write_new(path, raw, code='EVIDENCE_WRITE_FAILED'):
    path = Path(path)
    temporary = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(temporary),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        need(_read_regular(temporary, code) == raw, 'EVIDENCE_READBACK_FAILED')
        try:
            os.link(str(temporary), str(path), follow_symlinks=False)
        except FileExistsError as exc:
            raise NotesEvidenceError('EVIDENCE_TARGET_EXISTS') from exc
        os.unlink(str(temporary))
        sync_dir(path.parent)
        need(_read_regular(path, code) == raw, 'EVIDENCE_READBACK_FAILED')
    except Exception as exc:
        if isinstance(exc, NotesEvidenceError):
            raise
        raise NotesEvidenceError(code) from exc
    finally:
        os.close(fd)
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _write_or_verify(path, raw):
    path = Path(path)
    if _entry(path) is None:
        try:
            _write_new(path, raw)
        except NotesEvidenceError as exc:
            if exc.code != 'EVIDENCE_TARGET_EXISTS':
                raise
            need(_read_regular(path, 'EVIDENCE_STORAGE_CHANGED') == raw,
                 'EVIDENCE_STORAGE_CHANGED')
    else:
        need(_read_regular(path, 'EVIDENCE_STORAGE_CHANGED') == raw,
             'EVIDENCE_STORAGE_CHANGED')


def _decode_object(raw, code):
    try:
        return strict_json(raw, code)
    except DailyError as exc:
        raise NotesEvidenceError(code) from exc


def _is_evidence_family_payload(raw):
    """Recognize only a top-level JSON object with a family schema key.

    This deliberately does not search arbitrary opaque bytes for the schema
    string. It is used after strict JSON parsing rejects duplicate keys so a
    malformed v2 bundle stays rejected without misclassifying legacy evidence
    that merely mentions the schema name.
    """
    try:
        pairs = json.loads(raw, object_pairs_hook=lambda value: value)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(pairs, list) or not all(
            isinstance(item, tuple) and len(item) == 2 for item in pairs):
        return False
    return any(key == 'schema' and isinstance(value, str) and
               value.startswith(SCHEMA_FAMILY) for key, value in pairs)


def _decode_import_bundle(raw):
    try:
        data = strict_json(raw, 'INVALID_EVIDENCE_BUNDLE')
    except DailyError as exc:
        code = ('INVALID_EVIDENCE_BUNDLE'
                if _is_evidence_family_payload(raw)
                else 'EVIDENCE_BUNDLE_REQUIRED')
        raise NotesEvidenceError(code) from exc
    if not isinstance(data, dict) or not isinstance(data.get('schema'), str) \
            or not data['schema'].startswith(SCHEMA_FAMILY):
        raise NotesEvidenceError('EVIDENCE_BUNDLE_REQUIRED')
    return data


def normalize_context(values=None, *, allow_unknown=False):
    values = {} if values is None else values
    need(isinstance(values, dict), 'INVALID_EVIDENCE_CONTEXT')
    need(set(values) <= set(CONTEXT_FIELDS), 'INVALID_EVIDENCE_CONTEXT')
    result = {}
    for field in CONTEXT_FIELDS:
        value = values.get(field)
        if value is None:
            result[field] = UNKNOWN
            continue
        need(isinstance(value, str) and bool(value.strip()) and
             len(value) <= 4096 and (allow_unknown or value != UNKNOWN),
             'INVALID_EVIDENCE_CONTEXT')
        result[field] = value
    return result


def _validate_ref(ref, *, allow_statement=False):
    need(isinstance(ref, dict) and set(ref) == set(REF_FIELDS),
         'INVALID_EVIDENCE_REF')
    role = ref['role']
    allowed = ASSET_ROLES + ((STATEMENT_ROLE,) if allow_statement else ())
    need(role in allowed, 'INVALID_EVIDENCE_ROLE')
    source_path = ref['source_path']
    need(isinstance(source_path, str) and Path(source_path).is_absolute(),
         'INVALID_EVIDENCE_REF')
    need(type(ref['bytes']) is int and ref['bytes'] >= 0,
         'INVALID_EVIDENCE_REF')
    need(isinstance(ref['sha256'], str) and len(ref['sha256']) == 64 and
         all(character in '0123456789abcdef' for character in ref['sha256']),
         'INVALID_EVIDENCE_REF')
    need(role in EMPTY_ALLOWED_ROLES or ref['bytes'] > 0, 'EMPTY_EVIDENCE')
    return ref


def _validate_bundle(data, expected_context=None):
    need(isinstance(data, dict) and
         set(data) == {'schema', 'context', 'statement_ref', 'assets'},
         'INVALID_EVIDENCE_BUNDLE')
    need(data['schema'] == SCHEMA, 'UNSUPPORTED_EVIDENCE_SCHEMA')
    context = normalize_context(data['context'], allow_unknown=True)
    need(data['context'] == context, 'INVALID_EVIDENCE_CONTEXT')
    _validate_ref(data['statement_ref'], allow_statement=True)
    need(data['statement_ref']['role'] == STATEMENT_ROLE,
         'INVALID_EVIDENCE_STATEMENT')
    need(isinstance(data['assets'], list), 'INVALID_EVIDENCE_BUNDLE')
    for ref in data['assets']:
        _validate_ref(ref)
    if expected_context is not None:
        expected = normalize_context(expected_context, allow_unknown=True)
        need(context == expected, 'EVIDENCE_CONTEXT_MISMATCH')
    return data


def _bundle_refs(data):
    return [data['statement_ref'], *data['assets']]


def _verify_child_path(parent, ref):
    path = Path(parent) / ref['sha256']
    raw = _read_regular(path, 'EVIDENCE_CHILD_MISSING')
    need(len(raw) == ref['bytes'] and digest(raw) == ref['sha256'],
         'EVIDENCE_CHILD_DRIFT')
    return path, raw


def _verify_source_path(ref):
    source = _project_source(ref['source_path'])
    raw = _read_regular(source, 'EVIDENCE_SOURCE_CHANGED')
    need(len(raw) == ref['bytes'] and digest(raw) == ref['sha256'],
         'EVIDENCE_SOURCE_CHANGED')
    return raw


def inspect_source_bundle(value, expected_context=None, *, verify_sources=True):
    bundle = _project_source(value)
    raw = _read_regular(bundle, 'EVIDENCE_BUNDLE_CHANGED')
    need(bool(raw), 'EMPTY_EVIDENCE')
    data = _validate_bundle(_decode_import_bundle(raw), expected_context)
    for ref in _bundle_refs(data):
        _verify_child_path(bundle.parent, ref)
        if verify_sources:
            _verify_source_path(ref)
    return dict(path=bundle, raw=raw, data=data,
                reference=dict(path=str(bundle), bytes=len(raw),
                               sha256=digest(raw)))


def load_saved_evidence(evidence_dir, outer_ref, expected_context=None):
    need(isinstance(outer_ref, dict) and set(outer_ref) == set(OUTER_FIELDS),
         'INVALID_EVIDENCE_REF')
    need(isinstance(outer_ref['path'], str) and
         outer_ref['path'].startswith('/') and
         type(outer_ref['bytes']) is int and outer_ref['bytes'] >= 0 and
         isinstance(outer_ref['sha256'], str) and
         len(outer_ref['sha256']) == 64 and
         all(character in '0123456789abcdef'
             for character in outer_ref['sha256']),
         'INVALID_EVIDENCE_REF')
    evidence_dir = _canonical_directory(evidence_dir,
                                        'EVIDENCE_DIRECTORY_CHANGED')
    path = Path(outer_ref['path'])
    need(path.parent == evidence_dir and path.name == outer_ref['sha256'],
         'EVIDENCE_BINDING_CHANGED')
    raw = _read_regular(path, 'EVIDENCE_DRIFT')
    need(len(raw) == outer_ref['bytes'] and digest(raw) == outer_ref['sha256'],
         'EVIDENCE_DRIFT')
    need(bool(raw), 'EMPTY_EVIDENCE')
    try:
        data = strict_json(raw, 'INVALID_EVIDENCE_BUNDLE')
    except DailyError as exc:
        if _is_evidence_family_payload(raw):
            raise NotesEvidenceError('INVALID_EVIDENCE_BUNDLE') from exc
        return dict(classification='LEGACY_OPAQUE', outer_ref=outer_ref)
    if isinstance(data, dict) and isinstance(data.get('schema'), str) and \
            data['schema'].startswith(SCHEMA_FAMILY):
        _validate_bundle(data, expected_context)
        for ref in _bundle_refs(data):
            _verify_child_path(evidence_dir, ref)
        return dict(classification='REFERENCE_VERIFIED', outer_ref=outer_ref,
                    data=data)
    return dict(classification='LEGACY_OPAQUE', outer_ref=outer_ref)


def audit_saved_evidence(evidence_dir, outer_ref, expected_context=None):
    """Inspect one saved evidence reference without stopping at child drift.

    This uses the same strict bundle parser and digest checks as the normal
    loader. It is intentionally audit-only: callers must not project business
    state from an audit result whose ``integrity_ok`` is false.
    """
    evidence_dir = _canonical_directory(evidence_dir,
                                        'EVIDENCE_DIRECTORY_CHANGED')
    row = dict(outer_ref=outer_ref, classification='UNVERIFIED',
               integrity_ok=False, errors=[], child_assets=[],
               reference_check='REFERENCE_CHECK_NOT_AVAILABLE')

    if not isinstance(outer_ref, dict) or set(outer_ref) != set(OUTER_FIELDS):
        row['errors'].append('INVALID_EVIDENCE_REF')
        return row
    if not (isinstance(outer_ref['path'], str) and
            outer_ref['path'].startswith('/') and
            type(outer_ref['bytes']) is int and outer_ref['bytes'] >= 0 and
            isinstance(outer_ref['sha256'], str) and
            len(outer_ref['sha256']) == 64 and
            all(character in '0123456789abcdef'
                for character in outer_ref['sha256'])):
        row['errors'].append('INVALID_EVIDENCE_REF')
        return row

    path = Path(outer_ref['path'])
    if path.parent != evidence_dir or path.name != outer_ref['sha256']:
        row['errors'].append('EVIDENCE_BINDING_CHANGED')
        return row
    try:
        raw = _read_regular(path, 'EVIDENCE_DRIFT')
    except NotesEvidenceError as exc:
        row['errors'].append(exc.code)
        return row
    if len(raw) != outer_ref['bytes'] or digest(raw) != outer_ref['sha256']:
        row['errors'].append('EVIDENCE_DRIFT')
        return row
    if not raw:
        row['errors'].append('EMPTY_EVIDENCE')
        return row

    try:
        data = strict_json(raw, 'INVALID_EVIDENCE_BUNDLE')
    except DailyError:
        if _is_evidence_family_payload(raw):
            row['errors'].append('INVALID_EVIDENCE_BUNDLE')
        else:
            row['classification'] = 'LEGACY_OPAQUE'
            row['integrity_ok'] = True
        return row
    if not (isinstance(data, dict) and isinstance(data.get('schema'), str) and
            data['schema'].startswith(SCHEMA_FAMILY)):
        row['classification'] = 'LEGACY_OPAQUE'
        row['integrity_ok'] = True
        return row

    row['classification'] = 'V2'
    try:
        _validate_bundle(data, expected_context)
    except NotesEvidenceError as exc:
        row['errors'].append(exc.code)
        return row
    for ref in _bundle_refs(data):
        child = dict(role=ref['role'], sha256=ref['sha256'],
                     bytes=ref['bytes'], status='VERIFIED', error=None,
                     actual_sha256=None, actual_bytes=None)
        try:
            _, child_raw = _verify_child_path(evidence_dir, ref)
            child['actual_sha256'] = digest(child_raw)
            child['actual_bytes'] = len(child_raw)
        except NotesEvidenceError as exc:
            child['status'] = 'DRIFT'
            child['error'] = exc.code
        row['child_assets'].append(child)
    row['integrity_ok'] = not row['errors'] and all(
        child['status'] == 'VERIFIED' for child in row['child_assets'])
    if row['integrity_ok']:
        row['reference_check'] = 'VERIFIED'
    return row


def preserve_bundle(records, source, expected_context=None,
                    expected_reference=None):
    inspected = inspect_source_bundle(source, expected_context, verify_sources=True)
    if expected_reference is not None:
        need(inspected['reference'] == expected_reference,
             'EVIDENCE_SOURCE_CHANGED')
    evidence_dir = _canonical_directory(Path(records) / 'evidence',
                                        'EVIDENCE_DIRECTORY_CHANGED')
    unique = {}
    for ref in _bundle_refs(inspected['data']):
        unique.setdefault(ref['sha256'], ref)
    for sha256, ref in unique.items():
        _, raw = _verify_child_path(inspected['path'].parent, ref)
        _write_or_verify(evidence_dir / sha256, raw)
    _write_or_verify(evidence_dir / inspected['reference']['sha256'],
                     inspected['raw'])
    for sha256, ref in unique.items():
        _verify_child_path(evidence_dir, ref)
    need(_read_regular(evidence_dir / inspected['reference']['sha256'],
                       'EVIDENCE_STORAGE_CHANGED') == inspected['raw'],
         'EVIDENCE_STORAGE_CHANGED')
    return dict(path=str(evidence_dir / inspected['reference']['sha256']),
                bytes=inspected['reference']['bytes'],
                sha256=inspected['reference']['sha256'])


def create_bundle(*, statement, assets, context, output_dir):
    need(isinstance(statement, str) and statement, 'EVIDENCE_STATEMENT_REQUIRED')
    statement_source = _project_source(statement)
    statement_raw = _read_regular(statement_source, 'EVIDENCE_SOURCE_CHANGED')
    need(bool(statement_raw), 'EMPTY_EVIDENCE')
    statement_ref = dict(role=STATEMENT_ROLE, source_path=str(statement_source),
                          bytes=len(statement_raw), sha256=digest(statement_raw))
    _validate_ref(statement_ref, allow_statement=True)

    refs = []
    raws = {digest(statement_raw): statement_raw}
    for role, value in assets:
        need(role in ASSET_ROLES, 'INVALID_EVIDENCE_ROLE')
        source = _project_source(value)
        raw = _read_regular(source, 'EVIDENCE_SOURCE_CHANGED')
        need(role in EMPTY_ALLOWED_ROLES or bool(raw), 'EMPTY_EVIDENCE')
        ref = dict(role=role, source_path=str(source), bytes=len(raw),
                   sha256=digest(raw))
        _validate_ref(ref)
        refs.append(ref)
        raws[ref['sha256']] = raw

    data = dict(schema=SCHEMA, context=normalize_context(context),
                statement_ref=statement_ref, assets=refs)
    _validate_bundle(data)
    bundle_raw = encoded(data)
    need(bool(bundle_raw), 'EMPTY_EVIDENCE')

    target = Path(output_dir).expanduser()
    need(target.is_absolute(), 'NEW_EVIDENCE_DIRECTORY_REQUIRED')
    parent = _canonical_directory(target.parent, 'EVIDENCE_OUTPUT_PARENT_REQUIRED')
    private_tasks = _canonical_directory(
        PRIVATE_TASK_ROOT, 'EVIDENCE_PRIVATE_TASK_ROOT_REQUIRED')
    need(parent.is_relative_to(private_tasks),
         'PROJECT_PRIVATE_EVIDENCE_REQUIRED')
    need(_entry(target) is None, 'EVIDENCE_OUTPUT_DIRECTORY_EXISTS')
    try:
        os.mkdir(str(target), 0o700)
    except FileExistsError as exc:
        raise NotesEvidenceError('EVIDENCE_OUTPUT_DIRECTORY_EXISTS') from exc
    sync_dir(parent)
    target = _canonical_directory(target, 'NEW_EVIDENCE_DIRECTORY_CHANGED')
    for sha256, raw in raws.items():
        _write_new(target / sha256, raw)
    bundle_path = target / 'bundle.json'
    _write_new(bundle_path, bundle_raw)
    for ref in _bundle_refs(data):
        _verify_child_path(target, ref)
    reference = dict(path=str(bundle_path), bytes=len(bundle_raw),
                     sha256=digest(bundle_raw))
    return dict(bundle_path=str(bundle_path), reference=reference,
                schema=SCHEMA, context=data['context'])
