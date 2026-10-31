"""Independent offline verification for one note photo or video.

This module verifies local bytes only. It neither observes LINE nor grants a
download, Save All, publication, or completion. A PASS means the isolated file
decoded, not that the file is byte-identical to LINE's server-side original.

Photo verification reuses the existing macOS ImageIO decoder in a clean
single-file directory. Video verification uses one pinned pair of absolute
FFmpeg tools, probes every stream strictly, and decodes every audio/video stream
by exact index into the null muxer. Decode progress is consumed with a stall
watchdog rather than a fixed total-runtime timeout.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import stat
import subprocess
import tempfile
import time
from fractions import Fraction


FFMPEG_PATH = Path('/opt/homebrew/bin/ffmpeg')
FFPROBE_PATH = Path('/opt/homebrew/bin/ffprobe')
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_TOOL_VERSION = '7.1.1'
FFMPEG_SHA256 = '7697b094387e2918821fe7480c73f5d44543817096e9d5b5fafe58ecd6912569'
FFPROBE_SHA256 = 'fd670257233c93c88608a62ed8b5ddeeb812bd341dfb39bbe0e1c654b91672ad'

VIDEO_TOOL_PINS = {
    'ffmpeg': {
        'path': str(FFMPEG_PATH),
        'version': VIDEO_TOOL_VERSION,
        'sha256': FFMPEG_SHA256,
    },
    'ffprobe': {
        'path': str(FFPROBE_PATH),
        'version': VIDEO_TOOL_VERSION,
        'sha256': FFPROBE_SHA256,
    },
}

PHOTO_EXTENSIONS = ('.jpg', '.jpeg', '.png')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.m4v', '.avi', '.mkv')
PHOTO_FORMAT_BY_SUFFIX = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png'}
VIDEO_CONTAINER_ALIASES = {
    '.mp4': frozenset(('mov', 'mp4', 'm4a', '3gp', '3g2', 'mj2')),
    '.mov': frozenset(('mov', 'mp4', 'm4a', '3gp', '3g2', 'mj2')),
    '.m4v': frozenset(('mov', 'mp4', 'm4a', '3gp', '3g2', 'mj2')),
    '.avi': frozenset(('avi',)),
    '.mkv': frozenset(('matroska', 'webm')),
}
MAX_PHOTO_BYTES = 512 * 1024 * 1024
DEFAULT_STABLE_SAMPLES = 3
DEFAULT_STABLE_INTERVAL = 1.0
DEFAULT_DECODE_STALL_TIMEOUT = 30.0
DEFAULT_PROBE_TIMEOUT = 60.0
DEFAULT_VERSION_TIMEOUT = 15.0
PROGRESS_READ_SIZE = 64 * 1024


class MediaVerificationError(ValueError):
    """A fail-closed verification rejection with a stable code and evidence."""

    def __init__(self, code, evidence=None):
        super().__init__(code)
        self.code = code
        self.evidence = evidence or {}


VerificationError = MediaVerificationError


def _need(condition, code, evidence=None):
    if not condition:
        raise MediaVerificationError(code, evidence)


def _strict_json_int(value, code, evidence=None):
    if type(value) is not int:
        raise MediaVerificationError(code, evidence)
    return value


def _strict_int_like(value, code, *, minimum=None, evidence=None):
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r'[0-9]+', value) is not None:
        number = int(value)
    else:
        raise MediaVerificationError(code, evidence)
    if minimum is not None and number < minimum:
        raise MediaVerificationError(code, evidence)
    return number


def _canonical_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(',', ':')) + '\n').encode('utf-8')


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _bytes(value):
    if value is None:
        return b''
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode('utf-8')
    raise MediaVerificationError('INVALID_CAPTURE_TYPE')


def _strict_json(raw, code):
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, code)
            result[key] = value
        return result

    def invalid_constant(_value):
        raise MediaVerificationError(code)

    try:
        return json.loads(_bytes(raw).decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=invalid_constant)
    except MediaVerificationError:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise MediaVerificationError(code) from exc


def _path(value):
    path = Path(value).expanduser().absolute()
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MediaVerificationError('CANONICAL_FILE_REQUIRED') from exc
    _need(path == resolved, 'CANONICAL_FILE_REQUIRED')
    return path


def _directory(value):
    path = Path(value).expanduser().absolute()
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise MediaVerificationError('ISOLATION_PARENT_REQUIRED') from exc
    _need(path == resolved and path.is_dir(), 'ISOLATION_PARENT_REQUIRED')
    return path


def _regular_file_identity(path):
    info = os.lstat(path)
    _need(not stat.S_ISLNK(info.st_mode), 'SOURCE_SYMLINK_REFUSED')
    _need(stat.S_ISREG(info.st_mode), 'SOURCE_NOT_REGULAR')
    _need(info.st_nlink == 1, 'SOURCE_HARDLINK_REFUSED')
    return info


def _fingerprint_file(path):
    """Hash one regular file while binding its stat identity and content."""
    path = _path(path)
    before_path = _regular_file_identity(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
              'REGULAR_SINGLE_LINK_FILE_REQUIRED')
        _need((before.st_dev, before.st_ino) == (before_path.st_dev, before_path.st_ino),
              'FILE_REPLACED')
        hasher = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            size += len(chunk)
        after = os.fstat(fd)
        _need(size == before.st_size == after.st_size, 'FILE_CHANGED')
    finally:
        os.close(fd)
    after_path = os.lstat(path)
    _need(stat.S_ISREG(after_path.st_mode), 'FILE_REPLACED')
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')
    _need(tuple(getattr(before, key) for key in fields) ==
          tuple(getattr(after, key) for key in fields) ==
          tuple(getattr(after_path, key) for key in fields), 'FILE_CHANGED')
    return {
        'name': path.name,
        'size': size,
        'sha256': hasher.hexdigest(),
        'mtime_ns': after.st_mtime_ns,
        'ctime_ns': after.st_ctime_ns,
        'device': after.st_dev,
        'inode': after.st_ino,
        'mode': stat.S_IMODE(after.st_mode),
        'nlink': after.st_nlink,
    }


def _public_fingerprint(fingerprint):
    return {key: fingerprint[key]
            for key in ('name', 'size', 'sha256', 'mtime_ns', 'ctime_ns')}


def _stable_fingerprints(path, sample_count, interval):
    _need(type(sample_count) is int and sample_count >= 2,
          'STABLE_SAMPLE_COUNT_REQUIRED')
    _need(isinstance(interval, (int, float)) and not isinstance(interval, bool) and
          math.isfinite(interval) and interval >= 0, 'INVALID_STABLE_INTERVAL')
    samples = []
    fingerprints = []
    for index in range(sample_count):
        if index and interval:
            time.sleep(interval)
        fingerprint = _fingerprint_file(path)
        _need(not fingerprints or fingerprint == fingerprints[-1],
              'MEDIA_NOT_STABLE')
        fingerprints.append(fingerprint)
        samples.append(_public_fingerprint(fingerprint))
    _need(fingerprints[-1]['size'] > 0, 'EMPTY_MEDIA')
    return fingerprints[-1], samples


def _decoder_reference(decoder):
    path = _path(decoder)
    _regular_file_identity(path)
    fingerprint = _fingerprint_file(path)
    _need(fingerprint['size'] > 0, 'EMPTY_DECODER')
    _need(os.access(str(path), os.X_OK), 'DECODER_NOT_EXECUTABLE')
    return {
        'path': str(path),
        'bytes': fingerprint['size'],
        'sha256': fingerprint['sha256'],
    }


def _validate_sha256(value, code):
    _need(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
          code)


def _copy_exclusive(source, target, expected):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    source_fd = os.open(str(source), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    target_fd = None
    try:
        target_fd = os.open(str(target), flags, 0o600)
        before = os.fstat(source_fd)
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            offset = 0
            while offset < len(chunk):
                offset += os.write(target_fd, chunk[offset:])
        os.fsync(target_fd)
        after = os.fstat(source_fd)
        _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
               before.st_ctime_ns) ==
              (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
               after.st_ctime_ns), 'MEDIA_CHANGED_DURING_ISOLATION')
    finally:
        os.close(source_fd)
        if target_fd is not None:
            os.close(target_fd)
    source_after = _fingerprint_file(source)
    copied = _fingerprint_file(target)
    _need(source_after == expected, 'MEDIA_CHANGED_DURING_ISOLATION')
    _need(copied['size'] == expected['size'] and copied['sha256'] == expected['sha256'],
          'ISOLATED_COPY_MISMATCH')
    return copied


def _photo_format(path):
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
        try:
            prefix = os.read(fd, 8)
        finally:
            os.close(fd)
    except OSError as exc:
        raise MediaVerificationError('PHOTO_FORMAT_UNREADABLE') from exc
    if prefix.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if prefix.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    return None


def _capture_call(runner, command, *, timeout, code):
    try:
        result = runner(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise MediaVerificationError(code) from exc
    except OSError as exc:
        raise MediaVerificationError(code) from exc
    return result, _bytes(result.stdout), _bytes(result.stderr)


def verify_photo(path, decoder, decoder_sha256, *, stable_samples=DEFAULT_STABLE_SAMPLES,
                 stable_interval=DEFAULT_STABLE_INTERVAL, decoder_timeout=120,
                 runner=subprocess.run, isolation_parent=PROJECT_ROOT):
    """Fully decode one JPG/PNG through ImageIO in a single-file directory."""
    _validate_sha256(decoder_sha256, 'INVALID_DECODER_SHA256')
    source = _path(path)
    _need(source.suffix.lower() in PHOTO_EXTENSIONS, 'UNSUPPORTED_PHOTO_EXTENSION')
    source_fingerprint, samples = _stable_fingerprints(
        source, stable_samples, stable_interval)
    _need(source_fingerprint['size'] < MAX_PHOTO_BYTES, 'PHOTO_TOO_LARGE')

    decoder_before = _decoder_reference(decoder)
    _need(decoder_before['sha256'] == decoder_sha256, 'DECODER_DRIFT')

    isolation_parent = _directory(isolation_parent)
    with tempfile.TemporaryDirectory(
            prefix='.line-notes-photo-isolate-', dir=str(isolation_parent)) as temporary:
        isolated = Path(temporary).resolve(strict=True)
        _need(isolated.is_dir(), 'ISOLATION_DIRECTORY_REQUIRED')
        target = isolated / source.name
        copied = _copy_exclusive(source, target, source_fingerprint)
        names = sorted(entry.name for entry in isolated.iterdir())
        _need(names == [source.name], 'ISOLATION_ENTRY_MISMATCH')
        actual_format = _photo_format(target)
        expected_format = PHOTO_FORMAT_BY_SUFFIX[source.suffix.lower()]
        _need(actual_format == expected_format, 'PHOTO_FORMAT_MISMATCH', {
            'expected_format': expected_format,
            'actual_format': actual_format,
        })

        run, stdout, stderr = _capture_call(
            runner, [str(decoder_before['path']), str(isolated), '1'],
            timeout=decoder_timeout, code='IMAGEIO_DECODE_TIMEOUT')
        evidence = {
            'command': [str(decoder_before['path']), str(isolated), '1'],
            'exit_code': run.returncode,
            'stdout_sha256': _digest(stdout),
            'stderr_sha256': _digest(stderr),
            'stderr_empty': not stderr,
        }
        _need(run.returncode == 0, 'IMAGEIO_DECODE_FAILED', evidence)
        _need(not stderr, 'IMAGEIO_DECODE_STDERR', evidence)
        result = _strict_json(stdout, 'INVALID_IMAGEIO_RESULT')
        _need(isinstance(result, dict), 'INVALID_IMAGEIO_RESULT')
        _need(result.get('verdict') == 'PASS' and result.get('readOnly') is True,
              'IMAGEIO_BINDING_MISMATCH', evidence)
        expected_entries = _strict_json_int(
            result.get('expected'), 'IMAGEIO_BINDING_MISMATCH', evidence)
        actual_entries = _strict_json_int(
            result.get('actualEntries'), 'IMAGEIO_BINDING_MISMATCH', evidence)
        _need(result.get('destination') == str(isolated) and
              expected_entries == 1 and actual_entries == 1,
              'IMAGEIO_BINDING_MISMATCH', evidence)
        entries = result.get('entries')
        _need(isinstance(entries, list) and len(entries) == 1,
              'IMAGEIO_CONTENT_MISMATCH', evidence)
        entry = entries[0]
        _need(isinstance(entry, dict) and entry.get('name') == source.name and
              entry.get('decoded') is True and entry.get('sha256') == copied['sha256'] and
              type(entry.get('width')) is int and entry['width'] > 0 and
              type(entry.get('height')) is int and entry['height'] > 0,
              'IMAGEIO_CONTENT_MISMATCH', evidence)

        names_after = sorted(entry.name for entry in isolated.iterdir())
        _need(names_after == [source.name], 'ISOLATION_ENTRY_MISMATCH')
        copied_after = _fingerprint_file(target)
        _need(copied_after['size'] == copied['size'] and
              copied_after['sha256'] == copied['sha256'], 'ISOLATED_COPY_CHANGED')

    source_after = _fingerprint_file(source)
    decoder_after = _decoder_reference(decoder_before['path'])
    _need(source_after == source_fingerprint, 'CONTENT_CHANGED_AFTER_DECODE')
    _need(decoder_after == decoder_before, 'DECODER_CHANGED_AFTER_DECODE')
    manifest = [_public_fingerprint(source_after)]
    return {
        'verdict': 'PASS',
        'kind': 'PHOTO',
        'source': manifest[0],
        'manifest': manifest,
        'manifest_sha256': _digest(_canonical_json(manifest)),
        'stable_samples': samples,
        'stable_sample_count': len(samples),
        'decoder': decoder_after,
        'isolation': {
            'entry_count': 1,
            'entry_name': source.name,
            'read_only_decoder': True,
        },
        'imageio': result,
        'imageio_stdout_sha256': evidence['stdout_sha256'],
        'full_decode_evidence': evidence,
        'pass_scope': 'OFFLINE_PHOTO_FILE_INTEGRITY_ONLY',
        'dispatch_authorized': False,
        'sensor_verified': False,
        'real_line_e2e': 'NOT_TESTED',
    }


def _tool_binary(configured, expected_path, expected_sha256, expected_version,
                 runner, version_timeout):
    _need(str(configured) == expected_path, 'VIDEO_TOOL_PATH_MISMATCH')
    configured = Path(configured)
    try:
        configured_info = os.lstat(configured)
    except OSError as exc:
        raise MediaVerificationError('VIDEO_TOOL_TARGET_MISSING') from exc
    _need(stat.S_ISREG(configured_info.st_mode) or
          stat.S_ISLNK(configured_info.st_mode), 'VIDEO_TOOL_LINK_OR_FILE_REQUIRED')
    try:
        resolved = configured.resolve(strict=True)
    except OSError as exc:
        raise MediaVerificationError('VIDEO_TOOL_TARGET_MISSING') from exc
    _need(resolved == _path(resolved), 'VIDEO_TOOL_TARGET_NOT_CANONICAL')
    _need(stat.S_ISREG(os.stat(resolved, follow_symlinks=False).st_mode),
          'VIDEO_TOOL_TARGET_NOT_REGULAR')
    _need(os.access(str(resolved), os.X_OK), 'VIDEO_TOOL_NOT_EXECUTABLE')
    fingerprint = _fingerprint_file(resolved)
    _need(fingerprint['sha256'] == expected_sha256, 'VIDEO_TOOL_SHA256_MISMATCH')

    run, stdout, stderr = _capture_call(
        runner, [str(configured), '-version'], timeout=version_timeout,
        code='VIDEO_TOOL_VERSION_TIMEOUT')
    _need(run.returncode == 0, 'VIDEO_TOOL_VERSION_FAILED')
    _need(not stderr, 'VIDEO_TOOL_VERSION_STDERR')
    try:
        text = stdout.decode('utf-8')
    except UnicodeError as exc:
        raise MediaVerificationError('VIDEO_TOOL_VERSION_INVALID') from exc
    first_line = text.splitlines()[0] if text else ''
    match = re.match(r'^(?:ffmpeg|ffprobe) version ([^ ]+)', first_line)
    _need(match is not None, 'VIDEO_TOOL_VERSION_INVALID')
    version = match.group(1)
    _need(version == expected_version, 'VIDEO_TOOL_VERSION_MISMATCH')
    return {
        'configured_path': str(configured),
        'resolved_path': str(resolved),
        'configured_link': stat.S_ISLNK(configured_info.st_mode),
        'bytes': fingerprint['size'],
        'sha256': fingerprint['sha256'],
        'expected_sha256': expected_sha256,
        'version': version,
        'version_first_line': first_line,
        'version_stdout_sha256': _digest(stdout),
        'executable': True,
    }


def inspect_video_tools(*, runner=subprocess.run,
                        version_timeout=DEFAULT_VERSION_TIMEOUT):
    """Validate and record the exact pinned FFmpeg/ffprobe pair."""
    ffmpeg = _tool_binary(
        FFMPEG_PATH, VIDEO_TOOL_PINS['ffmpeg']['path'],
        VIDEO_TOOL_PINS['ffmpeg']['sha256'], VIDEO_TOOL_PINS['ffmpeg']['version'],
        runner, version_timeout)
    ffprobe = _tool_binary(
        FFPROBE_PATH, VIDEO_TOOL_PINS['ffprobe']['path'],
        VIDEO_TOOL_PINS['ffprobe']['sha256'], VIDEO_TOOL_PINS['ffprobe']['version'],
        runner, version_timeout)
    return {'ffmpeg': ffmpeg, 'ffprobe': ffprobe}


def _positive_duration(stream):
    value = stream.get('duration')
    if value not in (None, 'N/A'):
        try:
            duration = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MediaVerificationError('INVALID_STREAM_DURATION') from exc
        _need(math.isfinite(duration) and duration > 0, 'INVALID_STREAM_DURATION')
        return duration, 'stream.duration'
    duration_ts = stream.get('duration_ts')
    time_base = stream.get('time_base')
    if duration_ts not in (None, 'N/A') and time_base not in (None, 'N/A'):
        ticks = _strict_int_like(
            duration_ts, 'INVALID_STREAM_DURATION', minimum=1)
        try:
            base = Fraction(str(time_base))
            duration = float(ticks * base)
        except (TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
            raise MediaVerificationError('INVALID_STREAM_DURATION') from exc
        _need(math.isfinite(duration) and duration > 0,
              'INVALID_STREAM_DURATION')
        return duration, 'stream.duration_ts'
    return None, None


def _frame_count(stream):
    value = stream.get('nb_frames')
    if value in (None, 'N/A'):
        return None
    return _strict_int_like(
        value, 'INVALID_STREAM_FRAME_COUNT', minimum=1)


def _streams(probe):
    _need(isinstance(probe, dict) and isinstance(probe.get('format'), dict) and
          isinstance(probe.get('streams'), list), 'INVALID_PROBE_RESULT')
    rows = []
    indexes = set()
    for raw in probe['streams']:
        _need(isinstance(raw, dict), 'INVALID_STREAM_TABLE')
        index = raw.get('index')
        _need(type(index) is int and index >= 0 and index not in indexes,
              'INVALID_STREAM_INDEX')
        indexes.add(index)
        codec_type = raw.get('codec_type')
        if codec_type not in ('video', 'audio'):
            continue
        _need(isinstance(raw.get('codec_name'), str) and bool(raw['codec_name']),
              'INVALID_STREAM_CODEC')
        disposition = raw.get('disposition')
        _need(isinstance(disposition, dict), 'INVALID_STREAM_DISPOSITION')
        attached_pic = _strict_json_int(
            disposition.get('attached_pic'), 'INVALID_STREAM_DISPOSITION')
        _need(attached_pic in (0, 1), 'INVALID_STREAM_DISPOSITION')
        attached = attached_pic == 1
        if codec_type == 'video':
            _need(type(raw.get('width')) is int and raw['width'] > 0 and
                  type(raw.get('height')) is int and raw['height'] > 0,
                  'INVALID_VIDEO_DIMENSIONS')
        duration, duration_source = _positive_duration(raw)
        frames = _frame_count(raw) if codec_type == 'video' else None
        if attached and duration is None and frames is None:
            frames = 1
        rows.append({
            'index': index,
            'codec_type': codec_type,
            'codec_name': raw['codec_name'],
            'width': raw.get('width'),
            'height': raw.get('height'),
            'attached_pic': attached,
            'duration_seconds': duration,
            'duration_source': duration_source,
            'expected_frames': frames,
        })
    _need(any(row['codec_type'] == 'video' and not row['attached_pic']
              for row in rows), 'NO_VIDEO_STREAM')
    return rows


def _probe(path, *, runner, probe_timeout):
    command = [str(FFPROBE_PATH), '-v', 'error', '-print_format', 'json',
               '-show_format', '-show_streams', str(path)]
    run, stdout, stderr = _capture_call(
        runner, command, timeout=probe_timeout, code='PROBE_TIMEOUT')
    evidence = {
        'command': command,
        'exit_code': run.returncode,
        'stdout_sha256': _digest(stdout),
        'stderr_sha256': _digest(stderr),
        'stderr_empty': not stderr,
        'stderr_preview': stderr[:4000].decode('utf-8', 'replace'),
    }
    _need(run.returncode == 0, 'PROBE_FAILED', evidence)
    _need(not stderr, 'PROBE_STDERR', evidence)
    parsed = _strict_json(stdout, 'INVALID_PROBE_JSON')
    streams = _streams(parsed)
    container_format = _validate_container_format(path, parsed)
    evidence.update({
        'result': parsed,
        'streams': streams,
        'container_format': container_format,
    })
    return evidence


def _validate_container_format(path, probe):
    suffix = path.suffix.lower()
    _need(suffix in VIDEO_EXTENSIONS, 'UNSUPPORTED_VIDEO_EXTENSION')
    format_data = probe.get('format')
    _need(isinstance(format_data, dict), 'INVALID_PROBE_RESULT')
    raw_name = format_data.get('format_name')
    _need(isinstance(raw_name, str) and bool(raw_name.strip()),
          'INVALID_CONTAINER_FORMAT')
    names = frozenset(part.strip() for part in raw_name.split(',')
                      if part.strip())
    _need(bool(names), 'INVALID_CONTAINER_FORMAT')
    allowed = VIDEO_CONTAINER_ALIASES[suffix]
    _need(bool(names & allowed), 'CONTAINER_FORMAT_MISMATCH', {
        'suffix': suffix,
        'format_name': raw_name,
        'allowed_aliases': sorted(allowed),
    })
    return {
        'suffix': suffix,
        'format_name': raw_name,
        'aliases': sorted(names),
    }


def _decode_command(stream):
    command = [str(FFMPEG_PATH), '-nostdin', '-hide_banner', '-loglevel', 'error',
               '-err_detect', 'explode', '-xerror', '-i']
    command.extend(['{}'.format(stream['path'])])
    command.extend(['-map', '0:{}'.format(stream['index'])])
    command.extend(['-an', '-sn', '-dn'] if stream['codec_type'] == 'video'
                   else ['-vn', '-sn', '-dn'])
    command.extend(['-f', 'null', '-progress', 'pipe:1', '-nostats', '-'])
    return command


def _progress_number(block, key):
    value = block.get(key)
    if value in (None, 'N/A'):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MediaVerificationError('INVALID_PROGRESS') from exc
    _need(number >= 0, 'INVALID_PROGRESS')
    return number


def _progress_summary(records):
    if not records:
        return {
            'count': 0,
            'first': None,
            'last': None,
            'max_out_time_us': None,
            'max_frame': None,
            'final_out_time_us': None,
            'final_frame': None,
            'final_progress': None,
        }
    out_times = []
    frames = []
    previous_out_time = None
    previous_frame = None
    for row in records:
        out_time = _progress_number(row, 'out_time_us')
        if out_time is not None:
            _need(previous_out_time is None or out_time >= previous_out_time,
                  'INVALID_PROGRESS')
            previous_out_time = out_time
            out_times.append(out_time)
        frame = _progress_number(row, 'frame')
        if frame is not None:
            _need(previous_frame is None or frame >= previous_frame,
                  'INVALID_PROGRESS')
            previous_frame = frame
            frames.append(frame)
    final_out_time = _progress_number(records[-1], 'out_time_us')
    final_frame = _progress_number(records[-1], 'frame')
    return {
        'count': len(records),
        'first': dict(records[0]),
        'last': dict(records[-1]),
        'max_out_time_us': max(out_times) if out_times else None,
        'max_frame': max(frames) if frames else None,
        'final_out_time_us': final_out_time,
        'final_frame': final_frame,
        'final_progress': records[-1].get('progress'),
    }


def _read_temporary(stream):
    stream.flush()
    stream.seek(0)
    return stream.read()


def _stop_process(process):
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except OSError:
        return
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except OSError:
        return
    try:
        process.wait(timeout=2)
    except (subprocess.TimeoutExpired, OSError):
        return


def _decode_evidence(command, stream_index, exit_code, stdout_sha256,
                     stderr, records, stalled_seconds=None, stdout_bytes=0):
    summary = _progress_summary(records)
    evidence = {
        'stream_index': stream_index,
        'command': command,
        'exit_code': exit_code,
        'stdout_bytes': stdout_bytes,
        'stdout_sha256': stdout_sha256,
        'stderr_bytes': len(stderr),
        'stderr_sha256': _digest(stderr),
        'stderr_empty': not stderr,
        'stderr_preview': stderr[:4000].decode('utf-8', 'replace'),
        'progress': summary,
    }
    if stalled_seconds is not None:
        evidence['stalled_seconds'] = stalled_seconds
    return evidence


def run_decode_command(command, *, stream_index, stall_timeout=DEFAULT_DECODE_STALL_TIMEOUT,
                       popen_factory=subprocess.Popen, clock=time.monotonic,
                       progress_callback=None):
    """Run one already-built decode command with a progress-based watchdog.

    A timeout means no completed `-progress` record with a strictly increasing
    frame or out_time_us arrived for the configured stall interval. Repeated
    heartbeat blocks with unchanged/regressing metrics do not extend it. It is
    never converted to PASS. `progress=end` is required here but is only one
    part of the later duration/frame coverage checks.
    """
    _need(isinstance(command, list) and bool(command) and
          all(isinstance(value, str) for value in command) and
          Path(command[0]).is_absolute(), 'INVALID_DECODE_COMMAND')
    _need(isinstance(stall_timeout, (int, float)) and
          not isinstance(stall_timeout, bool) and math.isfinite(stall_timeout) and
          stall_timeout > 0, 'INVALID_STALL_TIMEOUT')

    records = []
    current = {}
    buffer = b''
    completed_progress_seen = False
    monotonic_metrics = {'frame': None, 'out_time_us': None}
    stdout_hasher = hashlib.sha256()
    stdout_bytes = 0
    last_progress = clock()
    stdout_eof = False
    process = None
    stderr_file = tempfile.TemporaryFile()
    try:
        try:
            process = popen_factory(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=stderr_file, bufsize=0, close_fds=True)
        except OSError as exc:
            raise MediaVerificationError('DECODE_START_FAILED') from exc
        descriptor = process.stdout.fileno()

        def consume_line(line):
            nonlocal current, completed_progress_seen, monotonic_metrics
            try:
                text = line.decode('utf-8')
            except UnicodeError as exc:
                raise MediaVerificationError('INVALID_PROGRESS') from exc
            if not text:
                return False
            _need(not completed_progress_seen, 'INVALID_PROGRESS')
            key, separator, value = text.partition('=')
            _need(bool(separator) and bool(key), 'INVALID_PROGRESS')
            _need(key not in current, 'INVALID_PROGRESS')
            current[key] = value
            if key != 'progress':
                return False
            _need(value in ('continue', 'end'), 'INVALID_PROGRESS')
            block = current
            current = {}
            advanced = False
            for metric in ('frame', 'out_time_us'):
                number = _progress_number(block, metric)
                if number is None:
                    continue
                previous = monotonic_metrics[metric]
                _need(previous is None or number >= previous, 'INVALID_PROGRESS')
                if previous is None or number > previous:
                    advanced = True
                monotonic_metrics[metric] = number
            records.append(block)
            if value == 'end':
                completed_progress_seen = True
            if progress_callback is not None:
                progress_callback(dict(block, sequence=len(records),
                                       stream_index=stream_index))
            return advanced

        def stalled_exception():
            _stop_process(process)
            stderr = _read_temporary(stderr_file)
            evidence = _decode_evidence(
                command, stream_index, process.poll(), stdout_hasher.hexdigest(),
                stderr, records, stalled_seconds=stall_timeout,
                stdout_bytes=stdout_bytes)
            evidence['stdout_eof'] = stdout_eof
            return MediaVerificationError('DECODE_STALLED', evidence)

        while True:
            remaining = stall_timeout - (clock() - last_progress)
            if remaining <= 0:
                raise stalled_exception()
            ready, _, _ = select.select([descriptor], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(descriptor, PROGRESS_READ_SIZE)
            if not chunk:
                stdout_eof = True
                break
            stdout_hasher.update(chunk)
            stdout_bytes += len(chunk)
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                if consume_line(line):
                    last_progress = clock()
        if buffer:
            if consume_line(buffer):
                last_progress = clock()

        exit_code = process.poll()
        if exit_code is None:
            remaining = stall_timeout - (clock() - last_progress)
            if remaining <= 0:
                raise stalled_exception()
            try:
                exit_code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                raise stalled_exception()
        stderr = _read_temporary(stderr_file)
        evidence = _decode_evidence(
            command, stream_index, exit_code, stdout_hasher.hexdigest(), stderr,
            records, stdout_bytes=stdout_bytes)
        evidence['stdout_eof'] = stdout_eof
        _need(exit_code == 0, 'DECODE_NONZERO_EXIT', evidence)
        _need(not stderr, 'DECODE_STDERR', evidence)
        _need(not current, 'INVALID_PROGRESS', evidence)
        _need(bool(records), 'EMPTY_DECODE_PROGRESS', evidence)
        _need(records[-1].get('progress') == 'end', 'DECODE_PROGRESS_NOT_EOF', evidence)
        _need(completed_progress_seen, 'DECODE_PROGRESS_NOT_EOF', evidence)
        _need(evidence['progress']['final_out_time_us'] is not None or
              evidence['progress']['final_frame'] is not None,
              'DECODE_PROGRESS_WITHOUT_METRICS', evidence)
        return evidence
    finally:
        if process is not None:
            if process.poll() is None:
                _stop_process(process)
            if process.stdout is not None:
                process.stdout.close()
        stderr_file.close()


def _coverage(stream, evidence):
    progress = evidence['progress']
    duration = stream['duration_seconds']
    frames = stream['expected_frames']
    final_out_time_us = progress.get('final_out_time_us')
    final_frame = progress.get('final_frame')
    _need(duration is not None or frames is not None, 'STREAM_COVERAGE_UNKNOWN')
    duration_covered = None
    if duration is not None:
        _need(final_out_time_us is not None, 'DURATION_COVERAGE_MISSING')
        duration_covered = _duration_coverage(duration, final_out_time_us)
        _need(duration_covered, 'DURATION_COVERAGE_SHORT')
    if frames is not None:
        _need(final_frame is not None, 'FRAME_COVERAGE_MISSING')
        _need(final_frame >= frames, 'FRAME_COVERAGE_SHORT')
    return {
        'duration_seconds': duration,
        'expected_frames': frames,
        'observed_out_time_us': final_out_time_us,
        'observed_frames': final_frame,
        'duration_covered': duration is None or duration_covered,
        'frames_covered': frames is None or final_frame >= frames,
    }


def _duration_coverage(duration, observed_out_time_us):
    try:
        expected = (Fraction(duration, 1)
                    if type(duration) is int else Fraction.from_float(duration))
        observed = Fraction(observed_out_time_us, 1_000_000)
        tolerance = max(
            Fraction(1, 20),
            min(Fraction(1, 1), expected * Fraction(1, 500)),
        )
        return observed + tolerance >= expected
    except (OverflowError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise MediaVerificationError('DURATION_COVERAGE_INVALID') from exc


def verify_video(path, *, stable_samples=DEFAULT_STABLE_SAMPLES,
                 stable_interval=DEFAULT_STABLE_INTERVAL,
                 stall_timeout=DEFAULT_DECODE_STALL_TIMEOUT,
                 probe_timeout=DEFAULT_PROBE_TIMEOUT,
                 version_timeout=DEFAULT_VERSION_TIMEOUT,
                 runner=subprocess.run, popen_factory=subprocess.Popen,
                 clock=time.monotonic, progress_callback=None):
    """Probe and fully decode every audio/video stream of one local video."""
    tools_before = inspect_video_tools(runner=runner, version_timeout=version_timeout)
    source = _path(path)
    source_fingerprint, samples = _stable_fingerprints(
        source, stable_samples, stable_interval)
    probe = _probe(source, runner=runner, probe_timeout=probe_timeout)
    streams = probe['streams']

    decoded = []
    for stream in streams:
        command = _decode_command(dict(stream, path=str(source)))
        callback = None
        if progress_callback is not None:
            def callback(event, source_stream=stream):
                progress_callback({'stream': dict(source_stream), 'progress': event})
        evidence = run_decode_command(
            command,
            stream_index=stream['index'],
            stall_timeout=stall_timeout,
            popen_factory=popen_factory,
            clock=clock,
            progress_callback=callback,
        )
        decoded.append({
            'stream': stream,
            'decode': evidence,
            'coverage': _coverage(stream, evidence),
        })

    source_after = _fingerprint_file(source)
    tools_after = inspect_video_tools(runner=runner, version_timeout=version_timeout)
    _need(source_after == source_fingerprint, 'CONTENT_CHANGED_AFTER_DECODE')
    _need(tools_after == tools_before, 'VIDEO_TOOL_CHANGED_DURING_DECODE')
    manifest = [_public_fingerprint(source_after)]
    return {
        'verdict': 'PASS',
        'kind': 'VIDEO',
        'source': manifest[0],
        'manifest': manifest,
        'manifest_sha256': _digest(_canonical_json(manifest)),
        'stable_samples': samples,
        'stable_sample_count': len(samples),
        'tools': tools_after,
        'probe': probe,
        'streams': decoded,
        'all_audio_video_streams_decoded': len(decoded),
        'pass_scope': 'OFFLINE_VIDEO_FILE_INTEGRITY_ONLY',
        'dispatch_authorized': False,
        'sensor_verified': False,
        'real_line_e2e': 'NOT_TESTED',
    }


def verify_media(path, kind, *, decoder=None, decoder_sha256=None, **options):
    """Dispatch a local file to photo or video verification without GUI work."""
    normalized = kind.upper() if isinstance(kind, str) else kind
    if normalized == 'PHOTO':
        _need(decoder is not None and decoder_sha256 is not None,
              'PHOTO_DECODER_REQUIRED')
        return verify_photo(path, decoder, decoder_sha256, **options)
    if normalized == 'VIDEO':
        return verify_video(path, **options)
    raise MediaVerificationError('UNSUPPORTED_MEDIA_KIND')


__all__ = [
    'DEFAULT_DECODE_STALL_TIMEOUT',
    'FFMPEG_PATH',
    'FFMPEG_SHA256',
    'FFPROBE_PATH',
    'FFPROBE_SHA256',
    'MediaVerificationError',
    'VIDEO_TOOL_PINS',
    'VIDEO_TOOL_VERSION',
    'VerificationError',
    'inspect_video_tools',
    'run_decode_command',
    'verify_media',
    'verify_photo',
    'verify_video',
]
