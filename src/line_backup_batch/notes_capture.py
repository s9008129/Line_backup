"""Single-run capture wrapper for the Notes CLI.

The wrapper records one fixed ``line_backup_batch.notes`` child invocation. It
does not operate a GUI, dispatch a download, choose a destination, or retry a
child. A missing complete receipt means INCOMPLETE.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import uuid

from . import notes
from .daily import digest, encoded, sync_dir


CORE_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_TASK_ROOT = CORE_ROOT / '.local' / 'line-backup' / 'tasks'
SCHEMA = 'line-notes-capture/v1'


class CaptureError(ValueError):
    def __init__(self, code, *, receipt_dir=None, child_exit=None,
                 signal_number=None, outer_exit=None):
        super().__init__(code)
        self.code = code
        self.receipt_dir = receipt_dir
        self.child_exit = child_exit
        self.signal_number = signal_number
        self.outer_exit = outer_exit


def need(condition, code):
    if not condition:
        raise CaptureError(code)


def _entry(path):
    try:
        return os.lstat(str(path))
    except FileNotFoundError:
        return None


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _canonical_directory(path, code):
    path = Path(path).expanduser()
    need(path.is_absolute(), code)
    info = _entry(path)
    need(info is not None and stat.S_ISDIR(info.st_mode) and
         not stat.S_ISLNK(info.st_mode), code)
    resolved = path.resolve(strict=True)
    need(resolved == path, code)
    return resolved


def _read_regular(path, code):
    path = Path(path)
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise CaptureError(code) from exc
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
        need(os.stat(str(path), follow_symlinks=False).st_ino == after.st_ino,
             code)
        return raw
    except CaptureError:
        raise
    except OSError as exc:
        raise CaptureError(code) from exc
    finally:
        os.close(fd)


def _write_new(path, raw):
    path = Path(path)
    need(_entry(path) is None, 'CAPTURE_FILE_COLLISION')
    temporary = path.parent / ('.pending-' + uuid.uuid4().hex)
    fd = os.open(str(temporary),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    temporary_info = None
    published = False
    try:
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        need(_read_regular(temporary, 'CAPTURE_READBACK_FAILED') == raw,
             'CAPTURE_READBACK_FAILED')
        temporary_info = os.stat(str(temporary), follow_symlinks=False)
        try:
            os.link(str(temporary), str(path), follow_symlinks=False)
        except FileExistsError as exc:
            raise CaptureError('CAPTURE_FILE_COLLISION') from exc
        published = True
        os.unlink(str(temporary))
        sync_dir(path.parent)
        need(_read_regular(path, 'CAPTURE_READBACK_FAILED') == raw,
             'CAPTURE_READBACK_FAILED')
    except Exception as exc:
        if published:
            try:
                current = os.stat(str(path), follow_symlinks=False)
                if (current.st_dev, current.st_ino) == (
                        temporary_info.st_dev, temporary_info.st_ino):
                    os.unlink(str(path))
                    sync_dir(path.parent)
            except OSError:
                pass
        if isinstance(exc, CaptureError):
            raise
        raise CaptureError('CAPTURE_WRITE_FAILED') from exc
    finally:
        os.close(fd)
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
    return dict(path=str(path), bytes=len(raw), sha256=digest(raw))


def _new_receipt(parent):
    target = parent / ('notes-capture-' + uuid.uuid4().hex)
    try:
        os.mkdir(str(target), 0o700)
    except FileExistsError as exc:
        raise CaptureError('CAPTURE_RECEIPT_COLLISION') from exc
    sync_dir(parent)
    return _canonical_directory(target, 'CAPTURE_RECEIPT_CHANGED')


def _program_identity():
    module_path = Path(notes.__file__).resolve(strict=True)
    module_raw = _read_regular(module_path, 'CAPTURE_PROGRAM_CHANGED')
    executable = Path(sys.executable).resolve(strict=True)
    executable_raw = _read_regular(executable, 'CAPTURE_PROGRAM_CHANGED')
    return dict(
        python_executable=str(executable),
        python_executable_sha256=digest(executable_raw),
        notes_module_path=str(module_path),
        notes_module_sha256=digest(module_raw),
        python_version=sys.version,
    )


def _ensure_program_unchanged(expected):
    try:
        current = _program_identity()
    except (CaptureError, OSError, ValueError) as exc:
        raise CaptureError('CAPTURE_PROGRAM_CHANGED') from exc
    need(current == expected, 'CAPTURE_PROGRAM_CHANGED')


def _run_child(command, cwd, env):
    return subprocess.run(command, cwd=str(cwd), env=env, shell=False,
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


def _exit_fields(returncode):
    if returncode is None:
        return None, None, None
    if returncode < 0:
        signal_number = -returncode
        return None, signal_number, 128 + signal_number
    return returncode, None, returncode


def _write_incomplete(receipt, *, phase, child_exit, signal_number):
    try:
        _write_new(receipt / 'incomplete.json', encoded(dict(
            schema=SCHEMA,
            status='INCOMPLETE',
            phase=phase,
            child_exit=child_exit,
            signal=signal_number,
            recorded_at=_utc_now(),
            clock_source='python:datetime.datetime.now(datetime.timezone.utc)',
            dispatch_authorized=False,
        )))
    except (CaptureError, OSError, ValueError):
        pass


def _persist(receipt, name, raw, *, phase, child_exit=None,
             signal_number=None):
    try:
        return _write_new(receipt / name, raw)
    except (CaptureError, OSError, ValueError) as exc:
        _write_incomplete(receipt, phase=phase, child_exit=child_exit,
                          signal_number=signal_number)
        raise CaptureError('CAPTURE_PERSISTENCE_FAILED',
                           receipt_dir=str(receipt), child_exit=child_exit,
                           signal_number=signal_number) from exc


def capture(output_root, child_args):
    parent = _canonical_directory(output_root, 'CAPTURE_OUTPUT_ROOT_REQUIRED')
    core = CORE_ROOT.resolve(strict=True)
    private_tasks = _canonical_directory(
        PRIVATE_TASK_ROOT, 'CAPTURE_PRIVATE_TASK_ROOT_REQUIRED')
    need(parent.is_relative_to(private_tasks),
         'PROJECT_PRIVATE_CAPTURE_REQUIRED')
    receipt = _canonical_directory(
        _new_receipt(parent), 'CAPTURE_RECEIPT_CHANGED')
    try:
        program = _program_identity()
    except (CaptureError, OSError, ValueError) as exc:
        raise CaptureError('CAPTURE_PROGRAM_CHANGED',
                           receipt_dir=str(receipt)) from exc
    request_raw = encoded(dict(
        schema=SCHEMA,
        receipt_id=receipt.name,
        child_args=list(child_args),
        child_command=[program['python_executable'], '-B', '-m',
                       'line_backup_batch.notes',
                       *child_args],
        cwd=str(core),
        pythonpath=str(core / 'src'),
        program=program,
        recorded_at=_utc_now(),
        clock_source='python:datetime.datetime.now(datetime.timezone.utc)',
        dispatch_authorized=False,
    ))
    request_ref = _persist(receipt, 'request.json', request_raw,
                           phase='REQUEST')

    command = [program['python_executable'], '-B', '-m',
               'line_backup_batch.notes',
               *child_args]
    env = dict(os.environ)
    env['PYTHONPATH'] = str(core / 'src')
    started_at = _utc_now()
    child_exit = None
    signal_number = None
    outer_exit = None
    try:
        completed = _run_child(command, core, env)
        finished_at = _utc_now()
        child_exit, signal_number, outer_exit = _exit_fields(
            completed.returncode)
    except OSError:
        finished_at = _utc_now()
        result_raw = encoded(dict(
            schema=SCHEMA,
            status='CHILD_LAUNCH_FAILED',
            child_exit=None,
            signal=None,
            outer_exit=None,
            started_at=started_at,
            finished_at=finished_at,
            clock_source='python:datetime.datetime.now(datetime.timezone.utc)',
            dispatch_authorized=False,
        ))
        _persist(receipt, 'result.json', result_raw, phase='CHILD_LAUNCH')
        _write_incomplete(receipt, phase='CHILD_LAUNCH', child_exit=None,
                          signal_number=None)
        raise CaptureError('CAPTURE_CHILD_LAUNCH_FAILED',
                           receipt_dir=str(receipt))

    stdout_raw = completed.stdout if completed.stdout is not None else b''
    stderr_raw = completed.stderr if completed.stderr is not None else b''
    result_raw = encoded(dict(
        schema=SCHEMA,
        status='CHILD_FINISHED',
        child_exit=child_exit,
        signal=signal_number,
        outer_exit=outer_exit,
        started_at=started_at,
        finished_at=finished_at,
        clock_source='python:datetime.datetime.now(datetime.timezone.utc)',
        dispatch_authorized=False,
    ))
    result_ref = _persist(
        receipt, 'result.json', result_raw, phase='RESULT',
        child_exit=child_exit, signal_number=signal_number)
    stdout_ref = _persist(
        receipt, 'stdout.bin', stdout_raw, phase='STDOUT',
        child_exit=child_exit, signal_number=signal_number)
    stderr_ref = _persist(
        receipt, 'stderr.bin', stderr_raw, phase='STDERR',
        child_exit=child_exit, signal_number=signal_number)
    try:
        _ensure_program_unchanged(program)
    except CaptureError as exc:
        _write_incomplete(receipt, phase='PROGRAM_CHANGED',
                          child_exit=child_exit,
                          signal_number=signal_number)
        raise CaptureError('CAPTURE_PROGRAM_CHANGED',
                           receipt_dir=str(receipt), child_exit=child_exit,
                           signal_number=signal_number) from exc
    complete_raw = encoded(dict(
        schema=SCHEMA,
        status='COMPLETE',
        child_exit=child_exit,
        signal=signal_number,
        outer_exit=outer_exit,
        started_at=started_at,
        finished_at=finished_at,
        clock_source='python:datetime.datetime.now(datetime.timezone.utc)',
        request=request_ref,
        stdout=stdout_ref,
        stderr=stderr_ref,
        result=result_ref,
        program=program,
        dispatch_authorized=False,
    ))
    _persist(receipt, 'complete.json', complete_raw, phase='COMPLETE',
             child_exit=child_exit, signal_number=signal_number)
    return dict(status='COMPLETE', receipt_dir=str(receipt),
                child_exit=child_exit, signal=signal_number,
                outer_exit=outer_exit, dispatch_authorized=False)


def _parser():
    parser = argparse.ArgumentParser(
        prog='python -B -m line_backup_batch.notes_capture',
        description='Capture one fixed Notes CLI child invocation without retry.')
    parser.add_argument('--output-root', required=True,
                        help='Existing project-private capture parent directory')
    parser.add_argument('child', nargs=argparse.REMAINDER,
                        help='Notes child arguments after --')
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    child = list(args.child)
    if child and child[0] == '--':
        child = child[1:]
    if not child:
        parser.error('a Notes child command is required after --')
    try:
        result = capture(args.output_root, child)
    except (CaptureError, OSError, ValueError) as exc:
        payload = dict(status='INTERNAL_ERROR', reason='CAPTURE_INCOMPLETE',
                       dispatch_authorized=False)
        if isinstance(exc, CaptureError):
            payload['capture_code'] = exc.code
            if exc.receipt_dir is not None:
                payload['receipt_dir'] = exc.receipt_dir
            if exc.child_exit is not None:
                payload['child_exit'] = exc.child_exit
            if exc.signal_number is not None:
                payload['signal'] = exc.signal_number
            if exc.outer_exit is not None:
                payload['outer_exit'] = exc.outer_exit
        print(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
        return 70
    except Exception:
        print(json.dumps(dict(status='INTERNAL_ERROR',
                              reason='UNEXPECTED_EXCEPTION',
                              dispatch_authorized=False),
                         ensure_ascii=False, separators=(',', ':')))
        return 70
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return result['outer_exit']


if __name__ == '__main__':
    raise SystemExit(main())
