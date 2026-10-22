#!/usr/bin/env python3
"""Minimal durable-session controller for the agent-resume P0 path.

This is the M0 slice: it proves the fixed-root single-writer session, real
process/boot identity checks, permanent EOF stop, and macOS full-sync
capabilities. It does not discover LINE, capture a screen, or dispatch GUI
input.
"""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = 1
MAX_LINE_BYTES = 1024 * 1024
MAX_LOCK_RECORD_BYTES = 64 * 1024
DEFAULT_ROOT = Path.home() / "Library" / "Application Support" / "LineBackup" / "agent-resume"
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_SAFETY_BLOCK = 3
EXIT_WRITER_BUSY = 4
EXIT_STORAGE_RUNTIME = 5


class ResumeError(Exception):
    def __init__(self, code: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


class InputError(ResumeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, EXIT_INPUT)


class SafetyBlock(ResumeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, EXIT_SAFETY_BLOCK)


class WriterBusy(ResumeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, EXIT_WRITER_BUSY)


class StorageRuntimeError(ResumeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, EXIT_STORAGE_RUNTIME)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _duplicate_safe_object(pairs: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY", "duplicate JSON key is not accepted")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise InputError("NON_FINITE_JSON", "NaN and Infinity are not accepted")


def strict_json_loads(raw: bytes) -> Any:
    if not raw or len(raw) > MAX_LINE_BYTES:
        raise InputError("JSON_SIZE_INVALID", "JSON payload is empty or too large")
    if b"\x00" in raw:
        raise InputError("JSON_NUL", "NUL bytes are not accepted")
    try:
        text = raw.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_duplicate_safe_object,
            parse_constant=_reject_json_constant,
        )
    except InputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("JSON_INVALID", "invalid UTF-8 JSON: %s" % exc) from exc


def _process_env() -> Dict[str, str]:
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["TZ"] = "UTC"
    return env


def process_identity(pid: int) -> Optional[Dict[str, Any]]:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        completed = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
            env=_process_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    started_at = " ".join(completed.stdout.split())
    if completed.returncode != 0 or not started_at:
        return None
    return {"pid": pid, "started_at": started_at}


def current_process_identity() -> Dict[str, Any]:
    identity = process_identity(os.getpid())
    if identity is None:
        raise StorageRuntimeError("CONTROLLER_IDENTITY_UNAVAILABLE", "controller process identity is unavailable")
    return identity


def boot_identity() -> str:
    try:
        completed = subprocess.run(
            ["sysctl", "-n", "kern.bootsessionuuid"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
            env=_process_env(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise StorageRuntimeError("BOOT_IDENTITY_UNAVAILABLE", "boot identity is unavailable") from exc
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        raise StorageRuntimeError("BOOT_IDENTITY_UNAVAILABLE", "boot identity is unavailable")
    return value


def _write_all(fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(fd, payload[offset:])
        if written <= 0:
            raise OSError(errno.EIO, "short write")
        offset += written


def _full_sync(fd: int) -> bool:
    os.fsync(fd)
    if not hasattr(fcntl, "F_FULLFSYNC"):
        raise StorageRuntimeError("FULLFSYNC_UNAVAILABLE", "F_FULLFSYNC is unavailable")
    result = fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)
    if result != 0:
        raise StorageRuntimeError("FULLFSYNC_FAILED", "F_FULLFSYNC did not report success")
    return True


def _ensure_private_root(root: Path) -> None:
    try:
        if not root.exists():
            root.mkdir(mode=0o700, parents=True)
        root_stat = root.lstat()
    except OSError as exc:
        raise StorageRuntimeError("ROOT_UNAVAILABLE", "fixed runtime root is unavailable") from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise SafetyBlock("ROOT_NOT_DIRECTORY", "runtime root must be a real directory")
    if root_stat.st_uid != os.getuid():
        raise SafetyBlock("ROOT_OWNER_MISMATCH", "runtime root is not owned by the current user")
    try:
        os.chmod(root, 0o700)
        dir_fd = os.open(
            root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise StorageRuntimeError("ROOT_OPEN_FAILED", "runtime root cannot be opened safely") from exc
    try:
        opened = os.fstat(dir_fd)
        if not stat.S_ISDIR(opened.st_mode) or opened.st_dev != root_stat.st_dev or opened.st_ino != root_stat.st_ino:
            raise SafetyBlock("ROOT_IDENTITY_DRIFT", "runtime root changed while opening")
    finally:
        os.close(dir_fd)


def sync_probe(root: Path) -> Dict[str, Any]:
    """Exercise the actual file/full-sync/readback primitives under the fixed root."""

    _ensure_private_root(root)
    probe = root / (".sync-probe-%d-%s" % (os.getpid(), secrets.token_hex(8)))
    payload = secrets.token_bytes(32)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    fd: Optional[int] = None
    directory_fd: Optional[int] = None
    try:
        fd = os.open(probe, flags, 0o600)
        _write_all(fd, payload)
        _full_sync(fd)
        os.close(fd)
        fd = None

        read_fd = os.open(probe, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
        try:
            readback = b""
            while len(readback) <= len(payload):
                chunk = os.read(read_fd, 4096)
                if not chunk:
                    break
                readback += chunk
            opened = os.fstat(read_fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != len(payload):
                raise StorageRuntimeError("SYNC_READBACK_INVALID", "sync probe readback is not a stable regular file")
        finally:
            os.close(read_fd)
        if readback != payload:
            raise StorageRuntimeError("SYNC_READBACK_MISMATCH", "sync probe bytes did not read back identically")

        os.unlink(probe)
        directory_fd = os.open(
            root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        os.fsync(directory_fd)
        return {
            "file_fsync": True,
            "fullfsync": True,
            "directory_fsync": True,
            "readback": True,
            "probe_sha256": hashlib.sha256(payload).hexdigest(),
        }
    except ResumeError:
        raise
    except OSError as exc:
        raise StorageRuntimeError("SYNC_PROBE_FAILED", "sync probe failed: %s" % exc) from exc
    finally:
        if fd is not None:
            os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)
        try:
            if probe.exists() or probe.is_symlink():
                probe.unlink()
                cleanup_fd = os.open(
                    root,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                )
                try:
                    os.fsync(cleanup_fd)
                finally:
                    os.close(cleanup_fd)
        except OSError:
            pass


class SessionRoot:
    """The single global writer lock and its durable owner record."""

    def __init__(self, root: Path = DEFAULT_ROOT) -> None:
        self.root = root
        self.lock_path = root / ".session.lock"
        self._fd: Optional[int] = None
        self.record: Optional[Dict[str, Any]] = None

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self) -> None:
        _ensure_private_root(self.root)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(self.lock_path, flags, 0o600)
        except OSError as exc:
            raise StorageRuntimeError("SESSION_LOCK_OPEN_FAILED", "session lock cannot be opened safely") from exc
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_uid != os.getuid():
                raise SafetyBlock("SESSION_LOCK_INVALID", "session lock is not a current-user regular file")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN):
                    raise WriterBusy("WRITER_BUSY", "another resume controller holds the global writer lock") from exc
                raise StorageRuntimeError("SESSION_LOCK_FAILED", "global writer lock failed") from exc
            self._fd = fd
            previous = self._read_record(fd)
            self._reject_unsafe_previous(previous)
        except Exception:
            if self._fd is not None:
                self._release_fd()
            else:
                os.close(fd)
            raise

    def _read_record(self, fd: int) -> Optional[Dict[str, Any]]:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            chunks = []
            total = 0
            while True:
                chunk = os.read(fd, 8192)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_LOCK_RECORD_BYTES:
                    raise SafetyBlock("SESSION_OWNER_RECORD_TOO_LARGE", "session owner record exceeds the limit")
                chunks.append(chunk)
        except OSError as exc:
            raise StorageRuntimeError("SESSION_OWNER_READ_FAILED", "session owner record cannot be read") from exc
        raw = b"".join(chunks).strip()
        if not raw:
            return None
        try:
            value = strict_json_loads(raw)
        except InputError as exc:
            raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "session owner record is not strict JSON") from exc
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
            raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "session owner record schema is invalid")
        return value

    def _reject_unsafe_previous(self, previous: Optional[Dict[str, Any]]) -> None:
        if previous is None or previous.get("state") == "closed":
            return
        current_boot = boot_identity()
        if previous.get("boot_id") == current_boot:
            host = previous.get("host")
            if isinstance(host, dict):
                observed = process_identity(host.get("pid"))
                if observed is not None and observed.get("started_at") == host.get("started_at"):
                    raise SafetyBlock(
                        "OLD_HOST_ALIVE",
                        "the previous GUI host process is still alive; close it before takeover",
                    )
            controller = previous.get("controller")
            if isinstance(controller, dict):
                observed_controller = process_identity(controller.get("pid"))
                if observed_controller is not None and observed_controller.get("started_at") == controller.get("started_at"):
                    raise WriterBusy("PREVIOUS_CONTROLLER_ALIVE", "the previous controller identity is still alive")
        if previous.get("pending_input") is True:
            raise SafetyBlock(
                "PENDING_INPUT_UNRESOLVED",
                "the previous session has an unresolved GUI input; do not take over",
            )

    def activate(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.held:
            raise StorageRuntimeError("SESSION_LOCK_NOT_HELD", "cannot activate an owner without the global lock")
        value = dict(record)
        value["schema_version"] = SCHEMA_VERSION
        value["state"] = "active"
        raw = canonical_json(value) + b"\n"
        self._replace_record(raw)
        self.record = value
        return value

    def close_clean(self) -> None:
        if not self.held:
            return
        if self.record is not None:
            value = dict(self.record)
            value["state"] = "closed"
            value["closed_at_utc"] = utc_now()
            self._replace_record(canonical_json(value) + b"\n")
            self.record = value
        self._release_fd()

    def release_without_close(self) -> None:
        self._release_fd()

    def _replace_record(self, raw: bytes) -> None:
        assert self._fd is not None
        try:
            os.lseek(self._fd, 0, os.SEEK_SET)
            os.ftruncate(self._fd, 0)
            _write_all(self._fd, raw)
            _full_sync(self._fd)
            os.lseek(self._fd, 0, os.SEEK_SET)
            readback = os.read(self._fd, len(raw) + 1)
        except ResumeError:
            raise
        except OSError as exc:
            raise StorageRuntimeError("SESSION_OWNER_WRITE_FAILED", "session owner record could not be persisted") from exc
        if readback != raw:
            raise StorageRuntimeError("SESSION_OWNER_READBACK_MISMATCH", "session owner record did not read back identically")

    def _release_fd(self) -> None:
        fd = self._fd
        self._fd = None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def __enter__(self) -> "SessionRoot":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.close_clean()
        else:
            self.release_without_close()


def _require_exact_keys(value: Mapping[str, Any], expected: Tuple[str, ...], code: str) -> None:
    if set(value.keys()) != set(expected):
        raise InputError(code, "request fields do not match the protocol")


def _validate_request(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("REQUEST_INVALID", "request must be a JSON object")
    _require_exact_keys(
        value,
        ("version", "request_id", "session_id", "task_id", "expected_generation", "operation", "data"),
        "REQUEST_INVALID",
    )
    if value["version"] != SCHEMA_VERSION:
        raise InputError("VERSION_UNSUPPORTED", "request version is unsupported")
    for key in ("request_id", "session_id", "task_id"):
        if not isinstance(value[key], str) or not value[key]:
            raise InputError("REQUEST_INVALID", "%s must be a non-empty string" % key)
    if not TASK_ID_RE.fullmatch(value["task_id"]):
        raise InputError("TASK_ID_INVALID", "task_id is invalid")
    if not isinstance(value["expected_generation"], int) or isinstance(value["expected_generation"], bool) or value["expected_generation"] < 0:
        raise InputError("GENERATION_INVALID", "expected_generation must be a non-negative integer")
    if not isinstance(value["operation"], str) or not value["operation"]:
        raise InputError("OPERATION_INVALID", "operation must be a non-empty string")
    if not isinstance(value["data"], dict):
        raise InputError("DATA_INVALID", "data must be a JSON object")
    return value


def _response(request: Mapping[str, Any], result: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "request_id": request["request_id"],
        "session_id": request["session_id"],
        "operation": request["operation"],
        "ok": True,
        "result": dict(result),
    }


def _error_response(request_id: Any, session_id: Any, error: ResumeError) -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "request_id": request_id,
        "session_id": session_id,
        "ok": False,
        "error": {"code": error.code, "message": error.message},
    }


def _write_json_line(value: Mapping[str, Any]) -> None:
    payload = canonical_json(value) + b"\n"
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


class SessionServer:
    def __init__(self, task_id: str, root: Path = DEFAULT_ROOT) -> None:
        if not TASK_ID_RE.fullmatch(task_id):
            raise InputError("TASK_ID_INVALID", "task_id is invalid")
        self.task_id = task_id
        self.root = root
        self.controller = current_process_identity()
        self.boot_id = boot_identity()
        self.session_id: Optional[str] = None
        self.hello_seen = False
        self.stopped = False
        self.writer = SessionRoot(root)

    def run(self) -> int:
        self.writer.acquire()
        exit_code = EXIT_SAFETY_BLOCK
        clean_close = False
        try:
            for raw_line in sys.stdin.buffer:
                if self.stopped:
                    break
                request_id: Any = None
                session_id: Any = self.session_id
                try:
                    if len(raw_line) > MAX_LINE_BYTES:
                        raise InputError("REQUEST_TOO_LARGE", "request line exceeds the size limit")
                    request = _validate_request(strict_json_loads(raw_line))
                    request_id = request["request_id"]
                    session_id = request["session_id"]
                    if request["task_id"] != self.task_id:
                        raise SafetyBlock("TASK_SCOPE_MISMATCH", "request task does not match the session task")
                    if request["expected_generation"] != 0:
                        raise SafetyBlock("GENERATION_STALE", "M0 only accepts the initial generation")
                    if not self.hello_seen:
                        if request["operation"] != "hello":
                            raise SafetyBlock("HELLO_REQUIRED", "hello must be the first request")
                        result = self._hello(request)
                        self.hello_seen = True
                        self.session_id = request["session_id"]
                        _write_json_line(_response(request, result))
                        continue
                    if session_id != self.session_id:
                        raise SafetyBlock("SESSION_ID_MISMATCH", "session identity changed")
                    if request["operation"] == "ping":
                        _require_exact_keys(request["data"], (), "PING_DATA_INVALID")
                        _write_json_line(_response(request, {"pong": True, "stopped": False}))
                    elif request["operation"] == "close":
                        _require_exact_keys(request["data"], (), "CLOSE_DATA_INVALID")
                        _write_json_line(_response(request, {"closed": True}))
                        clean_close = True
                        exit_code = EXIT_OK
                        break
                    else:
                        raise SafetyBlock("OPERATION_NOT_AVAILABLE", "operation is not available in the M0 capability slice")
                except ResumeError as exc:
                    _write_json_line(_error_response(request_id, session_id, exc))
                    if not self.hello_seen or exc.exit_code in (EXIT_SAFETY_BLOCK, EXIT_STORAGE_RUNTIME):
                        exit_code = exc.exit_code
                        break
                    exit_code = exc.exit_code
            else:
                exit_code = EXIT_SAFETY_BLOCK
        finally:
            self.stopped = True
            if clean_close:
                self.writer.close_clean()
            else:
                self.writer.release_without_close()
        return exit_code

    def _hello(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        data = request["data"]
        _require_exact_keys(data, ("host", "boot_id"), "HELLO_DATA_INVALID")
        if data["boot_id"] != self.boot_id:
            raise SafetyBlock("BOOT_IDENTITY_MISMATCH", "host boot identity does not match the controller")
        host = data["host"]
        if not isinstance(host, dict):
            raise InputError("HOST_IDENTITY_INVALID", "host identity must be an object")
        _require_exact_keys(host, ("pid", "started_at"), "HOST_IDENTITY_INVALID")
        if not isinstance(host["pid"], int) or isinstance(host["pid"], bool) or host["pid"] <= 0:
            raise InputError("HOST_IDENTITY_INVALID", "host pid is invalid")
        if not isinstance(host["started_at"], str) or not host["started_at"]:
            raise InputError("HOST_IDENTITY_INVALID", "host start identity is invalid")
        if host["pid"] == self.controller["pid"]:
            raise SafetyBlock("HOST_CONTROLLER_CONFUSED", "GUI host and controller must be distinct processes")
        observed_host = process_identity(host["pid"])
        if observed_host is None or observed_host.get("started_at") != host["started_at"]:
            raise SafetyBlock("HOST_IDENTITY_STALE", "GUI host process identity is stale or unknown")
        sync = sync_probe(self.root)
        record = self.writer.activate(
            {
                "session_id": request["session_id"],
                "task_id": self.task_id,
                "boot_id": self.boot_id,
                "controller": self.controller,
                "host": observed_host,
                "pending_input": False,
                "started_at_utc": utc_now(),
            }
        )
        return {
            "generation": 0,
            "root_sha256": hashlib.sha256(str(self.root).encode("utf-8")).hexdigest(),
            "controller": self.controller,
            "host": observed_host,
            "boot_id": self.boot_id,
            "session_id": request["session_id"],
            "writer_lock": "held",
            "record_state": record["state"],
            "sync": sync,
            "gui_observations": 0,
            "gui_dispatches": 0,
        }


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LINE agent-resume durable session controller")
    subparsers = parser.add_subparsers(dest="command", required=True)
    session = subparsers.add_parser("session", help="run the single-writer JSON-lines session")
    session.add_argument("--task", required=True)
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    try:
        args = _parse_args(argv)
        if args.command == "session":
            return SessionServer(task_id=args.task).run()
        raise InputError("COMMAND_INVALID", "unsupported command")
    except ResumeError as exc:
        _write_json_line(_error_response(None, None, exc))
        return exc.exit_code
    except (BrokenPipeError, KeyboardInterrupt):
        return EXIT_SAFETY_BLOCK
    except Exception as exc:
        error = StorageRuntimeError("UNEXPECTED_RUNTIME_ERROR", "unexpected runtime failure: %s" % type(exc).__name__)
        try:
            _write_json_line(_error_response(None, None, error))
        except Exception:
            pass
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
