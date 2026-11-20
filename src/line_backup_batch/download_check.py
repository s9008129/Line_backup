"""Lightweight signature checks for downloaded LINE Notes media.

This module asks the system ``file`` utility for a magic-based MIME type. It
does not decode images, play videos, or infer trust from a filename alone.
"""

import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess


SCHEMA = 'line-notes-file-signature/v1'
FILE_TOOL = '/usr/bin/file'
TIMEOUT_SECONDS = 30

_MIME_BY_SUFFIX = {
    '.jpg': ('PHOTO', frozenset(('image/jpeg',))),
    '.jpeg': ('PHOTO', frozenset(('image/jpeg',))),
    '.png': ('PHOTO', frozenset(('image/png',))),
    '.gif': ('PHOTO', frozenset(('image/gif',))),
    '.webp': ('PHOTO', frozenset(('image/webp',))),
    '.tif': ('PHOTO', frozenset(('image/tiff',))),
    '.tiff': ('PHOTO', frozenset(('image/tiff',))),
    '.heic': ('PHOTO', frozenset(('image/heic', 'image/heif',
                                  'image/heic-sequence',
                                  'image/heif-sequence'))),
    '.heif': ('PHOTO', frozenset(('image/heic', 'image/heif',
                                  'image/heic-sequence',
                                  'image/heif-sequence'))),
    '.mp4': ('VIDEO', frozenset(('video/mp4', 'application/mp4'))),
    '.mov': ('VIDEO', frozenset(('video/quicktime',))),
    '.m4v': ('VIDEO', frozenset(('video/mp4', 'video/x-m4v'))),
    '.avi': ('VIDEO', frozenset(('video/x-msvideo', 'video/vnd.avi'))),
    '.mkv': ('VIDEO', frozenset(('video/x-matroska',))),
}
_NON_MEDIA_MIMES = frozenset((
    'text/plain', 'text/html', 'application/pdf', 'application/zip'))
_MEDIA_KINDS = frozenset(('PHOTO', 'VIDEO'))
_HASH_RE = re.compile(r'[0-9a-f]{64}\Z')
_MIME_RE = re.compile(r'[a-z][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*\Z')


class DownloadCheckError(ValueError):
    """A file signature could not be safely classified or validated."""


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _stat_fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _regular_nonsymlink(path, code):
    try:
        info = os.lstat(os.fspath(path))
    except OSError as exc:
        raise DownloadCheckError(code) from exc
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise DownloadCheckError(code)
    return info


def _tool_snapshot():
    info = _regular_nonsymlink(FILE_TOOL, 'FILE_TOOL_INVALID')
    try:
        digest = _sha256_file(FILE_TOOL)
    except OSError as exc:
        raise DownloadCheckError('FILE_TOOL_INVALID') from exc
    after = _regular_nonsymlink(FILE_TOOL, 'FILE_TOOL_CHANGED')
    if _stat_fingerprint(info) != _stat_fingerprint(after):
        raise DownloadCheckError('FILE_TOOL_CHANGED')
    return _stat_fingerprint(after), digest


def _check_result_shape(result):
    if not isinstance(result, dict) or set(result) != {
            'schema', 'kind', 'mime_type', 'tool_sha256', 'stdout_sha256'}:
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if result.get('schema') != SCHEMA:
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    kind, mime_type = result.get('kind'), result.get('mime_type')
    tool_hash, stdout_hash = result.get('tool_sha256'), result.get('stdout_sha256')
    if kind not in ('PHOTO', 'VIDEO', 'NON_MEDIA'):
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if not isinstance(mime_type, str) or not _MIME_RE.fullmatch(mime_type):
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if not isinstance(tool_hash, str) or not _HASH_RE.fullmatch(tool_hash):
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if not isinstance(stdout_hash, str) or not _HASH_RE.fullmatch(stdout_hash):
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if stdout_hash != hashlib.sha256((mime_type + '\n').encode('ascii')).hexdigest():
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if kind == 'NON_MEDIA' and mime_type not in _NON_MEDIA_MIMES:
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    if kind in _MEDIA_KINDS and mime_type in _NON_MEDIA_MIMES:
        raise DownloadCheckError('INVALID_SIGNATURE_METADATA')
    return kind, mime_type


def validate(result, name):
    """Validate persisted classification structure against a filename suffix."""
    kind, mime_type = _check_result_shape(result)
    if kind == 'NON_MEDIA':
        return result
    suffix = Path(os.fspath(name)).suffix.lower()
    allowed = _MIME_BY_SUFFIX.get(suffix)
    if allowed is None:
        raise DownloadCheckError('UNSUPPORTED_MEDIA_SUFFIX')
    expected_kind, expected_mimes = allowed
    if kind != expected_kind or mime_type not in expected_mimes:
        raise DownloadCheckError('MEDIA_SIGNATURE_SUFFIX_MISMATCH')
    return result


def classify(path):
    """Classify a regular media file using ``/usr/bin/file`` magic MIME output."""
    path = Path(path)
    suffix = path.suffix.lower()

    before = _regular_nonsymlink(path, 'MEDIA_FILE_INVALID')
    if before.st_size <= 0:
        raise DownloadCheckError('MEDIA_FILE_EMPTY')
    try:
        media_hash_before = _sha256_file(path)
    except OSError as exc:
        raise DownloadCheckError('MEDIA_FILE_CHANGED') from exc
    tool_fingerprint, tool_hash = _tool_snapshot()

    try:
        completed = subprocess.run(
            [FILE_TOOL, '--brief', '--mime-type', '--', os.fspath(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired as exc:
        raise DownloadCheckError('FILE_TOOL_TIMEOUT') from exc
    except OSError as exc:
        raise DownloadCheckError('FILE_TOOL_FAILED') from exc

    try:
        after = _regular_nonsymlink(path, 'MEDIA_FILE_CHANGED')
        media_hash_after = _sha256_file(path)
    except OSError as exc:
        raise DownloadCheckError('MEDIA_FILE_CHANGED') from exc
    if (_stat_fingerprint(before) != _stat_fingerprint(after) or
            media_hash_before != media_hash_after):
        raise DownloadCheckError('MEDIA_FILE_CHANGED')
    tool_fingerprint_after, tool_hash_after = _tool_snapshot()
    if tool_fingerprint != tool_fingerprint_after or tool_hash != tool_hash_after:
        raise DownloadCheckError('FILE_TOOL_CHANGED')

    if completed.returncode != 0:
        raise DownloadCheckError('FILE_TOOL_FAILED')
    if completed.stderr != b'':
        raise DownloadCheckError('FILE_TOOL_STDERR_NOT_EMPTY')
    try:
        output = completed.stdout.decode('ascii')
    except UnicodeDecodeError as exc:
        raise DownloadCheckError('FILE_TOOL_INVALID_OUTPUT') from exc
    if not output.endswith('\n') or output.count('\n') != 1:
        raise DownloadCheckError('FILE_TOOL_INVALID_OUTPUT')
    mime_type = output[:-1]
    if not _MIME_RE.fullmatch(mime_type):
        raise DownloadCheckError('FILE_TOOL_INVALID_OUTPUT')

    if mime_type in _NON_MEDIA_MIMES:
        kind = 'NON_MEDIA'
    elif mime_type not in {value for _kind, values in _MIME_BY_SUFFIX.values()
                           for value in values}:
        raise DownloadCheckError('UNSUPPORTED_MEDIA_MIME')
    else:
        if suffix not in _MIME_BY_SUFFIX:
            raise DownloadCheckError('UNSUPPORTED_MEDIA_SUFFIX')
        kind, allowed_mimes = _MIME_BY_SUFFIX[suffix]
        if mime_type not in allowed_mimes:
            raise DownloadCheckError('MEDIA_SIGNATURE_SUFFIX_MISMATCH')
    result = {
        'schema': SCHEMA,
        'kind': kind,
        'mime_type': mime_type,
        'tool_sha256': tool_hash,
        'stdout_sha256': hashlib.sha256(completed.stdout).hexdigest(),
    }
    return validate(result, path.name)
