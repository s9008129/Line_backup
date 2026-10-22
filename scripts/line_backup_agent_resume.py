#!/usr/bin/env python3
"""Single-writer store and session controller for resumable LINE album backup.

The module owns the fixed runtime store, the read-only history barrier, the
ordered task manifest, durable dispatch intents, file verification, and the
small JSON-lines controller used by the existing CUA Node wrapper. It never
locates or operates the LINE application itself.
"""

from __future__ import annotations

import argparse
import copy
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
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


STORE_SCHEMA_VERSION = 1
OWNER_RECORD_SCHEMA_VERSION = 1
SESSION_OWNER_KEYS = {
    "schema_version",
    "state",
    "session_id",
    "task_id",
    "boot_id",
    "controller",
    "host",
    "pending_input",
    "started_at_utc",
    "updated_at_utc",
    "checkpoint_generation",
}
LEGACY_SESSION_OWNER_KEYS = {
    "schema_version",
    "state",
    "session_id",
    "task_id",
    "boot_id",
    "controller",
    "host",
    "pending_input",
    "started_at_utc",
}
MAX_LINE_BYTES = 1024 * 1024
MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024
MAX_DECODER_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_LOCK_RECORD_BYTES = 64 * 1024
MAX_EXPECTED_IMAGES = 10_000
DEFAULT_ROOT = Path.home() / "Library" / "Application Support" / "LineBackup" / "agent-resume"
MODULE_ROOT = Path(__file__).resolve().parents[1]
IMAGE_DECODER_SOURCE = MODULE_ROOT / "scripts" / "agent_resume" / "image_decode.swift"
IMAGE_DECODER_SOURCE_SHA256 = "238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b"
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PARTIAL_SUFFIXES = (
    ".part",
    ".partial",
    ".tmp",
    ".temp",
    ".download",
    ".crdownload",
    ".incomplete",
    ".filepart",
)
HISTORY_EXPECTED_TOTALS = {
    "official_photos": 239,
    "manual_photos": 109,
    "pr28_photos": 329,
    "excluded_photos": 65,
}
HISTORY_KEYS = {"references", "barriers"}
HISTORY_REFERENCE_KEYS = {"source_kind", "path", "sha256", "bytes", "imported_at_utc"}
HISTORY_BARRIER_KEYS = {
    "barrier_id",
    "source_kind",
    "source_sha256",
    "group_key",
    "identity",
    "destinations",
    "verified_file_count",
    "deny_reason",
}
STORE_KEYS = {
    "schema_version",
    "generation",
    "last_event_seq",
    "payload_sha256",
    "events",
    "history",
    "tasks",
    "session_owner",
}
ALBUM_STATES = {
    "NOT_STARTED",
    "VERIFIED",
    "SKIPPED_EXISTING",
    "BLOCKED_PARTIAL",
    "BLOCKED_AMBIGUOUS",
    "UNKNOWN",
    "VERIFYING",
}
INTENT_OUTCOMES = {"RETURNED", "EXCEPTION", "TIMEOUT", "UNKNOWN"}
SAVE_ALL_INTENT_KEYS = {
    "action_id",
    "prepared_at_utc",
    "session_id",
    "album_key",
    "scope_sha256",
    "destination",
    "grounding",
    "result",
}
CHOOSER_INTENT_KEYS = {
    "action_id",
    "prepared_at_utc",
    "session_id",
    "album_key",
    "scope_sha256",
    "destination",
    "save_all_action_id",
    "grounding",
    "result",
}
SAVE_ALL_GROUNDING_KEYS = {
    "app_identifier",
    "group_key",
    "album_key",
    "window_id",
    "foreground_authorization_reference",
    "detail_identity",
    "menu_identity",
    "click_point",
    "destination_empty",
    "evidence_sha256",
}
CHOOSER_GROUNDING_KEYS = {
    "app_identifier",
    "group_key",
    "album_key",
    "window_id",
    "foreground_authorization_reference",
    "chooser_identity",
    "click_point",
    "evidence_sha256",
}
INTENT_RESULT_KEYS = {"at_utc", "outcome", "evidence_sha256"}
VERIFICATION_KEYS = {
    "verified_at_utc",
    "expected_images",
    "actual_entries",
    "inventory_sha256",
    "inventory",
    "decoder_source_sha256",
    "decoder_binary_sha256",
    "pre_inventory_sha256",
    "post_inventory_sha256",
    "stability_samples",
    "save_all_action_id",
    "chooser_action_id",
}
VERIFICATION_ENTRY_KEYS = {
    "name",
    "bytes",
    "sha256",
    "mtime_ns",
    "ctime_ns",
    "decoded",
    "width",
    "height",
    "content_type",
}

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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _inventory_digest(inventory: Sequence[Mapping[str, Any]]) -> str:
    normalized = [
        {key: entry[key] for key in sorted(VERIFICATION_ENTRY_KEYS)}
        for entry in inventory
    ]
    return sha256_bytes(canonical_json(normalized))


def _duplicate_safe_object(pairs: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY", "duplicate JSON key is not accepted")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise InputError("NON_FINITE_JSON", "NaN and Infinity are not accepted")


def strict_json_loads(raw: bytes, max_bytes: int = MAX_LINE_BYTES) -> Any:
    if not raw or len(raw) > max_bytes:
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


def _full_sync(fd: int) -> None:
    os.fsync(fd)
    if hasattr(fcntl, "F_FULLFSYNC"):
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)


def _directory_sync(path: Path) -> None:
    fd = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(fd)
        if hasattr(fcntl, "F_FULLFSYNC"):
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)
    finally:
        os.close(fd)


def _ensure_private_root(root: Path) -> None:
    root = Path(root)
    if root.is_symlink():
        raise SafetyBlock("RUNTIME_ROOT_SYMLINK", "runtime root must not be a symlink")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise SafetyBlock("RUNTIME_ROOT_INVALID", "runtime root must be a current-user directory")
    if stat.S_IMODE(info.st_mode) != 0o700:
        os.chmod(root, 0o700)


def _ensure_private_directory(path: Path) -> None:
    path = Path(path)
    if path.is_symlink():
        raise SafetyBlock("PRIVATE_DIRECTORY_SYMLINK", "private directory must not be a symlink")
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise SafetyBlock("PRIVATE_DIRECTORY_INVALID", "private directory must be a current-user directory")
    if stat.S_IMODE(info.st_mode) != 0o700:
        os.chmod(path, 0o700)


def _read_regular_bytes(path: Path, max_bytes: int, missing_code: str, invalid_code: str) -> bytes:
    path = Path(path)
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise InputError(missing_code, "%s is missing" % path.name) from exc
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise SafetyBlock(invalid_code, "%s must be a regular non-symlink file" % path.name)
    if info.st_size <= 0 or info.st_size > max_bytes:
        raise SafetyBlock(invalid_code, "%s size is invalid" % path.name)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise SafetyBlock(invalid_code, "%s cannot be opened safely" % path.name) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
            raise SafetyBlock(invalid_code, "%s is not a current-user regular file" % path.name)
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise SafetyBlock(invalid_code, "%s exceeds the size limit" % path.name)
            chunks.append(chunk)
        after = os.fstat(fd)
        if (
            before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise SafetyBlock(invalid_code, "%s changed while it was read" % path.name)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _atomic_json_write(
    path: Path,
    value: Mapping[str, Any],
    hooks: Optional[Mapping[str, Callable[[], None]]] = None,
    mode: int = 0o600,
) -> None:
    path = Path(path)
    _ensure_private_directory(path.parent)
    hooks = hooks or {}

    def hook(name: str) -> None:
        callback = hooks.get(name)
        if callback is not None:
            callback()

    raw = canonical_json(value) + b"\n"
    temp = path.parent / (".%s.tmp.%d.%s" % (path.name, os.getpid(), secrets.token_hex(8)))
    fd: Optional[int] = None
    try:
        fd = os.open(
            temp,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            mode,
        )
        hook("before_write")
        _write_all(fd, raw)
        hook("after_write")
        _full_sync(fd)
        hook("after_file_sync")
        os.close(fd)
        fd = None
        hook("before_replace")
        os.replace(temp, path)
        hook("after_replace")
        _directory_sync(path.parent)
        hook("after_directory_sync")
        readback = _read_regular_bytes(path, MAX_CHECKPOINT_BYTES, "ATOMIC_TARGET_MISSING", "ATOMIC_TARGET_INVALID")
        if readback != raw:
            raise StorageRuntimeError("ATOMIC_READBACK_MISMATCH", "atomic JSON readback differs from the written bytes")
        hook("after_readback")
    except ResumeError:
        raise
    except OSError as exc:
        raise StorageRuntimeError("ATOMIC_WRITE_FAILED", "atomic JSON write failed: %s" % exc) from exc
    finally:
        if fd is not None:
            os.close(fd)


def sync_probe(root: Path) -> Dict[str, Any]:
    root = Path(root)
    _ensure_private_root(root)
    probe = root / (".sync-probe-%s" % secrets.token_hex(8))
    payload = secrets.token_bytes(4096)
    fd: Optional[int] = None
    directory_fd: Optional[int] = None
    result: Dict[str, Any] = {
        "file_fsync": False,
        "fullfsync": False,
        "directory_fsync": False,
        "readback": False,
        "probe_sha256": sha256_bytes(payload),
    }
    try:
        fd = os.open(
            probe,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        _write_all(fd, payload)
        os.fsync(fd)
        result["file_fsync"] = True
        if hasattr(fcntl, "F_FULLFSYNC"):
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC, 0)
            result["fullfsync"] = True
        os.close(fd)
        fd = None
        directory_fd = os.open(
            root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        os.fsync(directory_fd)
        result["directory_fsync"] = True
        result["readback"] = probe.read_bytes() == payload
        return result
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
                _directory_sync(root)
        except OSError:
            pass


class SessionRoot:
    """The global cooperative writer lock and durable live-session record."""

    def __init__(self, root: Path = DEFAULT_ROOT) -> None:
        self.root = Path(root)
        self.lock_path = self.root / ".session.lock"
        self._fd: Optional[int] = None
        self.record: Optional[Dict[str, Any]] = None
        self.previous_pending_input = False

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
            if stat.S_IMODE(opened.st_mode) != 0o600:
                os.fchmod(fd, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN):
                    raise WriterBusy("WRITER_BUSY", "another resume controller holds the global writer lock") from exc
                raise StorageRuntimeError("SESSION_LOCK_FAILED", "global writer lock failed") from exc
            self._fd = fd
            previous = self._read_record(fd)
            self.record = previous
            self._reject_unsafe_previous(previous)
            self._reject_unsafe_checkpoint_owner()
        except Exception:
            if self._fd is not None:
                self._release_fd()
            else:
                os.close(fd)
            raise

    def _read_record(self, fd: int) -> Optional[Dict[str, Any]]:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            chunks: List[bytes] = []
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
            value = strict_json_loads(raw, MAX_LOCK_RECORD_BYTES)
        except InputError as exc:
            raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "session owner record is not strict JSON") from exc
        if not isinstance(value, dict) or value.get("schema_version") != OWNER_RECORD_SCHEMA_VERSION:
            raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "session owner record schema is invalid")
        normalized = copy.deepcopy(value)
        state = normalized.get("state")
        if isinstance(state, str):
            normalized["state"] = state.upper()
        if set(normalized) == SESSION_OWNER_KEYS:
            try:
                _validate_session_owner(normalized)
            except SafetyBlock as exc:
                raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", exc.message) from exc
            return normalized
        legacy_keys = set(normalized)
        if legacy_keys == LEGACY_SESSION_OWNER_KEYS or legacy_keys == LEGACY_SESSION_OWNER_KEYS | {"closed_at_utc"}:
            if normalized.get("state") != "CLOSED":
                raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "legacy active owner records are not accepted")
            normalized["updated_at_utc"] = str(normalized.get("closed_at_utc") or normalized.get("started_at_utc") or utc_now())
            normalized["checkpoint_generation"] = 0
            normalized.pop("closed_at_utc", None)
            try:
                _validate_session_owner(normalized)
            except SafetyBlock as exc:
                raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", exc.message) from exc
            return normalized
        raise SafetyBlock("SESSION_OWNER_RECORD_INVALID", "session owner record shape is invalid")

    def _reject_unsafe_previous(self, previous: Optional[Dict[str, Any]]) -> None:
        if previous is None:
            return
        if previous.get("pending_input") is True:
            self.previous_pending_input = True
            raise SafetyBlock(
                "PENDING_INPUT_UNRESOLVED",
                "the previous session has an unresolved GUI input; do not take over",
            )
        if previous.get("state") == "CLOSED":
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
    def _reject_unsafe_checkpoint_owner(self) -> None:
        checkpoint = self.root / "checkpoint.json"
        if not checkpoint.exists() and not checkpoint.is_symlink():
            return
        store = read_store(self.root)
        owner = store.get("session_owner")
        if owner is None:
            return
        if owner.get("pending_input") is True:
            self.previous_pending_input = True
            raise SafetyBlock(
                "PENDING_INPUT_UNRESOLVED",
                "the checkpoint has an unresolved GUI input; do not take over",
            )
        if owner.get("state") != "ACTIVE":
            return
        current_boot = boot_identity()
        if owner.get("boot_id") != current_boot:
            return
        host = owner.get("host")
        if isinstance(host, dict):
            observed = process_identity(host.get("pid"))
            if observed is not None and observed.get("started_at") == host.get("started_at"):
                raise SafetyBlock(
                    "OLD_HOST_ALIVE",
                    "the checkpoint's previous GUI host is still alive; close it before takeover",
                )
        controller = owner.get("controller")
        if isinstance(controller, dict):
            observed_controller = process_identity(controller.get("pid"))
            if (
                observed_controller is not None
                and observed_controller.get("started_at") == controller.get("started_at")
            ):
                raise WriterBusy(
                    "PREVIOUS_CONTROLLER_ALIVE",
                    "the checkpoint's previous controller identity is still alive",
                )

    def activate(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.held:
            raise StorageRuntimeError("SESSION_LOCK_NOT_HELD", "cannot activate an owner without the global lock")
        value = copy.deepcopy(dict(record))
        value["schema_version"] = OWNER_RECORD_SCHEMA_VERSION
        value["state"] = "ACTIVE"
        value["updated_at_utc"] = value.get("updated_at_utc") or value.get("started_at_utc") or utc_now()
        value["checkpoint_generation"] = int(value.get("checkpoint_generation") or 0)
        try:
            _validate_session_owner(value)
        except SafetyBlock as exc:
            raise StorageRuntimeError("SESSION_OWNER_INVALID", exc.message) from exc
        self._replace_record(canonical_json(value) + b"\n")
        self.record = value
        return value

    def set_pending_input(self, pending: bool, generation: int) -> None:
        if not self.held or self.record is None:
            raise StorageRuntimeError("SESSION_OWNER_MISSING", "cannot update pending input without an active owner")
        value = copy.deepcopy(self.record)
        value["pending_input"] = bool(pending)
        value["checkpoint_generation"] = generation
        value["updated_at_utc"] = utc_now()
        self._replace_record(canonical_json(value) + b"\n")
        self.record = value

    def close_clean(self) -> None:
        if not self.held:
            return
        if self.record is not None:
            value = copy.deepcopy(self.record)
            value["state"] = "CLOSED"
            value["pending_input"] = False
            value["updated_at_utc"] = utc_now()
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


def _payload_digest(value: Mapping[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "payload_sha256"}
    return sha256_bytes(canonical_json(payload))


def _append_events(store: Dict[str, Any], events: Sequence[Mapping[str, Any]]) -> None:
    seq = int(store["last_event_seq"])
    for source in events:
        seq += 1
        event = copy.deepcopy(dict(source))
        event["seq"] = seq
        store["events"].append(event)
    store["last_event_seq"] = seq


def _set_session_pending_in_store(store: Dict[str, Any], session_id: str, pending: bool) -> None:
    owner = store.get("session_owner")
    if isinstance(owner, dict) and owner.get("session_id") == session_id and owner.get("state") == "ACTIVE":
        owner["pending_input"] = bool(pending)
        owner["updated_at_utc"] = utc_now()
        owner["checkpoint_generation"] = int(store["generation"]) + 1


def _event(
    action: str,
    *,
    session_id: Optional[str],
    task_id: Optional[str],
    album_key: Optional[str] = None,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
    evidence_reference: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "at_utc": utc_now(),
        "session_id": session_id,
        "task_id": task_id,
        "album_key": album_key,
        "action": action,
        "from_state": from_state,
        "to_state": to_state,
        "evidence_reference": evidence_reference,
    }


def _validate_event_log(store: Mapping[str, Any]) -> None:
    events = store.get("events")
    if not isinstance(events, list):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "events must be a list")
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict) or event.get("seq") != index:
            raise SafetyBlock("STORE_EVENT_SEQUENCE_INVALID", "event sequence is not contiguous")
        if not isinstance(event.get("action"), str) or not event["action"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "event action is invalid")
        if not isinstance(event.get("at_utc"), str) or not event["at_utc"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "event time is invalid")
    if store.get("last_event_seq") != len(events):
        raise SafetyBlock("STORE_EVENT_SEQUENCE_INVALID", "last_event_seq does not match the event list")


def _validate_identity(identity: Any) -> None:
    required = {"group_key", "start_date", "end_date", "expected_images", "observed_title", "disambiguator"}
    if not isinstance(identity, dict) or set(identity) != required:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album identity shape is invalid")
    if not isinstance(identity["group_key"], str) or not identity["group_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "group_key is invalid")
    if not DATE_RE.fullmatch(str(identity["start_date"])) or not DATE_RE.fullmatch(str(identity["end_date"])):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album date is invalid")
    if str(identity["start_date"]) > str(identity["end_date"]):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album date range is reversed")
    count = identity["expected_images"]
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0 or count > MAX_EXPECTED_IMAGES:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "expected image count is invalid")
    if not isinstance(identity["observed_title"], str) or not isinstance(identity["disambiguator"], str):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album text identity is invalid")


def _validate_process_binding(value: Any, field: str) -> None:
    if not isinstance(value, dict) or set(value) != {"pid", "started_at"}:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "%s shape is invalid" % field)
    if not isinstance(value["pid"], int) or isinstance(value["pid"], bool) or value["pid"] <= 0:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "%s pid is invalid" % field)
    _validate_nonempty_text(value["started_at"], "%s.started_at" % field)


def _validate_session_owner(owner: Any) -> None:
    if not isinstance(owner, dict) or set(owner) != SESSION_OWNER_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "session_owner shape is invalid")
    if owner["schema_version"] != OWNER_RECORD_SCHEMA_VERSION or owner["state"] not in ("ACTIVE", "CLOSED"):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "session_owner schema or state is invalid")
    for field in ("session_id", "task_id", "boot_id", "started_at_utc", "updated_at_utc"):
        _validate_nonempty_text(owner[field], "session_owner.%s" % field)
    _validate_process_binding(owner["controller"], "session_owner.controller")
    _validate_process_binding(owner["host"], "session_owner.host")
    if not isinstance(owner["pending_input"], bool):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "session_owner.pending_input is invalid")
    if owner["state"] == "CLOSED" and owner["pending_input"] is not False:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "closed session_owner cannot leave pending input")
    if (
        not isinstance(owner["checkpoint_generation"], int)
        or isinstance(owner["checkpoint_generation"], bool)
        or owner["checkpoint_generation"] < 0
    ):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "session_owner checkpoint generation is invalid")


def _validate_history(history: Any) -> None:
    if not isinstance(history, dict) or set(history) != HISTORY_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "history shape is invalid")
    if not isinstance(history["references"], list) or not isinstance(history["barriers"], list):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "history collections must be lists")
    reference_hashes: set[Tuple[str, str]] = set()
    for reference in history["references"]:
        if not isinstance(reference, dict) or set(reference) != HISTORY_REFERENCE_KEYS:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history reference shape is invalid")
        for field in ("source_kind", "path", "imported_at_utc"):
            _validate_nonempty_text(reference[field], "history.reference.%s" % field)
        if not Path(reference["path"]).is_absolute():
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history reference path must be absolute")
        if not SHA256_RE.fullmatch(str(reference["sha256"])):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history reference digest is invalid")
        if not isinstance(reference["bytes"], int) or isinstance(reference["bytes"], bool) or reference["bytes"] <= 0:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history reference byte count is invalid")
        binding = (reference["source_kind"], reference["sha256"])
        if binding in reference_hashes:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history reference is duplicated")
        reference_hashes.add(binding)
    barrier_ids: set[str] = set()
    for barrier in history["barriers"]:
        if not isinstance(barrier, dict) or set(barrier) != HISTORY_BARRIER_KEYS:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier shape is invalid")
        if not SHA256_RE.fullmatch(str(barrier["barrier_id"])):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier id is invalid")
        if barrier["barrier_id"] in barrier_ids:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier is duplicated")
        barrier_ids.add(barrier["barrier_id"])
        for field in ("source_kind", "source_sha256", "group_key", "deny_reason"):
            _validate_nonempty_text(barrier[field], "history.barrier.%s" % field)
        if not SHA256_RE.fullmatch(barrier["source_sha256"]):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier source digest is invalid")
        if (barrier["source_kind"], barrier["source_sha256"]) not in reference_hashes:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier source is not referenced")
        _validate_identity(barrier["identity"])
        if barrier["identity"]["group_key"] != barrier["group_key"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier group binding is invalid")
        if (
            not isinstance(barrier["destinations"], list)
            or not barrier["destinations"]
            or not all(isinstance(item, str) and Path(item).is_absolute() for item in barrier["destinations"])
            or barrier["destinations"] != sorted(set(barrier["destinations"]))
        ):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier destinations are invalid")
        verified_file_count = barrier["verified_file_count"]
        if (
            not isinstance(verified_file_count, int)
            or isinstance(verified_file_count, bool)
            or verified_file_count < 0
            or verified_file_count > MAX_EXPECTED_IMAGES
        ):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier verified file count is invalid")
        payload = {
            "source_kind": barrier["source_kind"],
            "source_sha256": barrier["source_sha256"],
            "group_key": barrier["group_key"],
            "identity": barrier["identity"],
            "destinations": barrier["destinations"],
        }
        if barrier["barrier_id"] != sha256_bytes(canonical_json(payload)):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "history barrier id does not re-derive")


def _normalize_relative_destination(destination: str) -> str:
    if not isinstance(destination, str) or not destination or "\\" in destination or "\x00" in destination:
        raise InputError("DESTINATION_INVALID", "album destination must be a POSIX relative path")
    path = PurePosixPath(destination)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise InputError("DESTINATION_INVALID", "album destination traversal is not accepted")
    if len(path.parts) < 2 or path.parts[0] != "downloads":
        raise InputError("DESTINATION_INVALID", "album destination must be under downloads/")
    return path.as_posix()


def _validate_relative_destination(destination: Any) -> None:
    try:
        normalized = _normalize_relative_destination(destination)
    except InputError as exc:
        raise SafetyBlock("STORE_SCHEMA_INVALID", exc.message) from exc
    if normalized != destination:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "stored destination is not normalized")


def _scope_digest(scope: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(scope))


def _album_key(scope_id: str, identity: Mapping[str, Any]) -> str:
    value = {
        "scope_id": scope_id,
        "group_key": identity["group_key"],
        "start_date": identity["start_date"],
        "end_date": identity["end_date"],
        "expected_images": identity["expected_images"],
        "observed_title": identity["observed_title"],
        "disambiguator": identity["disambiguator"],
    }
    return sha256_bytes(canonical_json(value))


def _manifest_binding(task: Mapping[str, Any]) -> str:
    albums = task["albums"]
    order = task["album_order"]
    value = {
        "task_id": task["task_id"],
        "scope_sha256": _scope_digest(task["scope"]),
        "manifest_sha256": task["manifest_sha256"],
        "owner_authorization_reference": task["owner_authorization_reference"],
        "exclusions": task["exclusions"],
        "album_order": order,
        "identities": [albums[key]["identity"] for key in order],
        "destinations": [albums[key]["destination"] for key in order],
    }
    return sha256_bytes(canonical_json(value))


def _validate_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "%s must be a lowercase SHA-256" % field)


def _validate_uuid(value: Any, field: str) -> None:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "%s must be a UUID" % field)


def _validate_nonempty_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "%s must be a non-empty string" % field)


def _validate_click_point(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"x", "y"}:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "click_point shape is invalid")
    for axis in ("x", "y"):
        coordinate = value[axis]
        if (
            not isinstance(coordinate, (int, float))
            or isinstance(coordinate, bool)
            or coordinate != coordinate
            or coordinate in (float("inf"), float("-inf"))
            or coordinate < 0
            or coordinate > 100_000
        ):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "click_point coordinate is invalid")


def _validate_save_all_grounding(
    grounding: Any,
    *,
    scope: Mapping[str, Any],
    album: Mapping[str, Any],
) -> None:
    if not isinstance(grounding, dict) or set(grounding) != SAVE_ALL_GROUNDING_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all grounding shape is invalid")
    for field in (
        "app_identifier",
        "group_key",
        "album_key",
        "window_id",
        "foreground_authorization_reference",
        "detail_identity",
        "menu_identity",
    ):
        _validate_nonempty_text(grounding[field], "grounding.%s" % field)
    if grounding["app_identifier"] != scope["app_identifier"] or grounding["group_key"] != scope["group_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all grounding scope does not match the task")
    if grounding["album_key"] != album["album_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all grounding album does not match the task item")
    if grounding["destination_empty"] is not True:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all grounding must attest an empty destination")
    _validate_click_point(grounding["click_point"])
    _validate_sha256(grounding["evidence_sha256"], "grounding.evidence_sha256")


def _validate_chooser_grounding(
    grounding: Any,
    *,
    scope: Mapping[str, Any],
    album: Mapping[str, Any],
) -> None:
    if not isinstance(grounding, dict) or set(grounding) != CHOOSER_GROUNDING_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser grounding shape is invalid")
    for field in (
        "app_identifier",
        "group_key",
        "album_key",
        "window_id",
        "foreground_authorization_reference",
        "chooser_identity",
    ):
        _validate_nonempty_text(grounding[field], "grounding.%s" % field)
    if grounding["app_identifier"] != scope["app_identifier"] or grounding["group_key"] != scope["group_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser grounding scope does not match the task")
    if grounding["album_key"] != album["album_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser grounding album does not match the task item")
    _validate_click_point(grounding["click_point"])
    _validate_sha256(grounding["evidence_sha256"], "grounding.evidence_sha256")


def _validate_intent_result(result: Any) -> None:
    if not isinstance(result, dict) or set(result) != INTENT_RESULT_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "intent result shape is invalid")
    _validate_nonempty_text(result["at_utc"], "intent.result.at_utc")
    if result["outcome"] not in INTENT_OUTCOMES:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "intent result outcome is invalid")
    _validate_sha256(result["evidence_sha256"], "intent.result.evidence_sha256")


def _validate_save_all_intent(
    intent: Any,
    *,
    scope: Mapping[str, Any],
    album: Mapping[str, Any],
) -> None:
    if not isinstance(intent, dict) or set(intent) != SAVE_ALL_INTENT_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all intent shape is invalid")
    for field in ("prepared_at_utc", "session_id"):
        _validate_nonempty_text(intent[field], "save_all_intent.%s" % field)
    if not isinstance(intent["action_id"], str) or not UUID_RE.fullmatch(intent["action_id"]):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all intent action_id is invalid")
    if intent["album_key"] != album["album_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all intent album binding is invalid")
    if intent["scope_sha256"] != _scope_digest(scope):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all intent scope binding is invalid")
    if intent["destination"] != album["destination"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "save-all intent destination binding is invalid")
    _validate_save_all_grounding(intent["grounding"], scope=scope, album=album)
    if intent["result"] is not None:
        _validate_intent_result(intent["result"])


def _validate_chooser_intent(
    intent: Any,
    *,
    scope: Mapping[str, Any],
    album: Mapping[str, Any],
) -> None:
    if not isinstance(intent, dict) or set(intent) != CHOOSER_INTENT_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent shape is invalid")
    for field in ("prepared_at_utc", "session_id"):
        _validate_nonempty_text(intent[field], "chooser_confirm_intent.%s" % field)
    if not isinstance(intent["action_id"], str) or not UUID_RE.fullmatch(intent["action_id"]):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent action_id is invalid")
    if not isinstance(intent["save_all_action_id"], str) or not UUID_RE.fullmatch(intent["save_all_action_id"]):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent save-all action binding is invalid")
    if intent["album_key"] != album["album_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent album binding is invalid")
    if intent["scope_sha256"] != _scope_digest(scope):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent scope binding is invalid")
    if intent["destination"] != album["destination"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent destination binding is invalid")
    _validate_chooser_grounding(intent["grounding"], scope=scope, album=album)
    if intent["result"] is not None:
        _validate_intent_result(intent["result"])


def _validate_verification(verification: Any) -> None:
    if not isinstance(verification, dict) or set(verification) != VERIFICATION_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification shape is invalid")
    for field in (
        "inventory_sha256",
        "decoder_source_sha256",
        "decoder_binary_sha256",
        "pre_inventory_sha256",
        "post_inventory_sha256",
    ):
        _validate_sha256(verification[field], "verification.%s" % field)
    _validate_uuid(verification["save_all_action_id"], "verification.save_all_action_id")
    _validate_uuid(verification["chooser_action_id"], "verification.chooser_action_id")
    _validate_nonempty_text(verification["verified_at_utc"], "verification.verified_at_utc")
    for field in ("expected_images", "actual_entries", "stability_samples"):
        value = verification[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification.%s is invalid" % field)
    if verification["actual_entries"] != verification["expected_images"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry count is incomplete")
    if verification["decoder_source_sha256"] != IMAGE_DECODER_SOURCE_SHA256:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification is not bound to the pinned decoder source")
    if verification["pre_inventory_sha256"] != verification["post_inventory_sha256"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification inventory changed during decode or flush")
    if verification["stability_samples"] < 3:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification did not collect three stable samples")
    if verification["expected_images"] > MAX_EXPECTED_IMAGES:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification expected count exceeds the limit")
    inventory = verification["inventory"]
    if not isinstance(inventory, list) or len(inventory) != verification["actual_entries"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification inventory shape is invalid")
    names = []
    for entry in inventory:
        if not isinstance(entry, dict) or set(entry) != VERIFICATION_ENTRY_KEYS:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry shape is invalid")
        _validate_nonempty_text(entry["name"], "verification.entry.name")
        if "/" in entry["name"] or "\\" in entry["name"] or entry["name"] in (".", ".."):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry name is not a basename")
        if not isinstance(entry["bytes"], int) or isinstance(entry["bytes"], bool) or entry["bytes"] <= 0:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry bytes is invalid")
        if not isinstance(entry["mtime_ns"], int) or not isinstance(entry["ctime_ns"], int):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry time binding is invalid")
        _validate_sha256(entry["sha256"], "verification.entry.sha256")
        if entry["decoded"] is not True:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry is not decoded")
        if not isinstance(entry["width"], int) or not isinstance(entry["height"], int) or entry["width"] <= 0 or entry["height"] <= 0:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification entry dimensions are invalid")
        _validate_nonempty_text(entry["content_type"], "verification.entry.content_type")
        names.append(entry["name"])
    if names != sorted(names) or len(set(names)) != len(names):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification inventory order is invalid")
    if verification["inventory_sha256"] != _inventory_digest(inventory):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "verification inventory digest does not re-derive")


def _validate_task_album(album: Any, scope: Mapping[str, Any]) -> None:
    required = {
        "ordinal",
        "album_key",
        "identity",
        "destination",
        "save_all_intent",
        "chooser_confirm_intent",
        "verification",
    }
    if not isinstance(album, dict) or set(album) != required:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album shape is invalid")
    if not isinstance(album["ordinal"], int) or isinstance(album["ordinal"], bool) or album["ordinal"] < 1:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album ordinal is invalid")
    if not SHA256_RE.fullmatch(str(album["album_key"])):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album_key is invalid")
    _validate_identity(album["identity"])
    if album["identity"]["group_key"] != scope["group_key"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album group does not match the task scope")
    if album["album_key"] != _album_key(scope["scope_id"], album["identity"]):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album_key does not bind its scope and identity")
    _validate_relative_destination(album["destination"])
    for field in ("save_all_intent", "chooser_confirm_intent", "verification"):
        if album[field] is not None and not isinstance(album[field], dict):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "%s must be null or an object" % field)
    if album["save_all_intent"] is not None:
        _validate_save_all_intent(album["save_all_intent"], scope=scope, album=album)
    if album["chooser_confirm_intent"] is not None:
        if album["save_all_intent"] is None:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent without a save-all intent is invalid")
        _validate_chooser_intent(album["chooser_confirm_intent"], scope=scope, album=album)
    if album["verification"] is not None:
        _validate_verification(album["verification"])
        save_intent = album["save_all_intent"]
        chooser_intent = album["chooser_confirm_intent"]
        if save_intent is None or chooser_intent is None:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification requires both dispatch intents")
        if not _intent_returned(save_intent) or not _intent_returned(chooser_intent):
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification requires returned dispatch results")
        if chooser_intent["save_all_action_id"] != save_intent["action_id"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "chooser intent does not bind its save-all action")
        if album["verification"]["save_all_action_id"] != save_intent["action_id"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification does not bind its save-all action")
        if album["verification"]["chooser_action_id"] != chooser_intent["action_id"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification does not bind its chooser action")
        if album["verification"]["expected_images"] != album["identity"]["expected_images"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "verification count disagrees with the album identity")


def _validate_task(task: Any) -> None:
    required = {
        "task_id",
        "created_at_utc",
        "scope",
        "owner_authorization_reference",
        "exclusions",
        "manifest_sha256",
        "manifest_binding_sha256",
        "album_order",
        "albums",
    }
    if not isinstance(task, dict) or set(task) != required:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "task shape is invalid")
    if not TASK_ID_RE.fullmatch(str(task["task_id"])):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "task id is invalid")
    scope = task["scope"]
    if not isinstance(scope, dict) or set(scope) != {"group_key", "app_identifier", "owner_id", "scope_id"}:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "task scope is invalid")
    if not all(isinstance(scope[key], str) and scope[key] for key in scope):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "task scope values are invalid")
    if not isinstance(task["owner_authorization_reference"], str) or not task["owner_authorization_reference"]:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "owner authorization reference is invalid")
    if not isinstance(task["exclusions"], list):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "exclusions must be a list")
    if not SHA256_RE.fullmatch(str(task["manifest_sha256"])):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "manifest digest is invalid")
    if not SHA256_RE.fullmatch(str(task["manifest_binding_sha256"])):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "manifest binding digest is invalid")
    order = task["album_order"]
    albums = task["albums"]
    if not isinstance(order, list) or not isinstance(albums, dict) or len(order) < 100:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "ordered manifest must contain at least 100 albums")
    if len(order) != len(albums) or len(set(order)) != len(order) or set(order) != set(albums):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album order and album map disagree")
    if [albums[album_key]["ordinal"] for album_key in order] != list(range(1, len(order) + 1)):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "album ordinal order is not contiguous")
    destinations: List[str] = []
    for ordinal, album_key in enumerate(order, start=1):
        if not isinstance(album_key, str) or album_key not in albums:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "album order contains an unknown key")
        album = albums[album_key]
        _validate_task_album(album, scope)
        if album["album_key"] != album_key or album["ordinal"] != ordinal:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "album ordinal/key binding is invalid")
        if album["identity"]["group_key"] != scope["group_key"]:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "album group does not match task scope")
        destinations.append(album["destination"])
    if len(set(destinations)) != len(destinations):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "task destinations are not unique")
    if task["manifest_binding_sha256"] != _manifest_binding(task):
        raise SafetyBlock("STORE_MANIFEST_BINDING_INVALID", "ordered manifest binding does not re-derive")


def _validate_store(store: Any) -> Dict[str, Any]:
    if not isinstance(store, dict) or set(store) != STORE_KEYS:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "checkpoint top-level shape is invalid")
    if store.get("schema_version") != STORE_SCHEMA_VERSION:
        raise SafetyBlock("STORE_SCHEMA_UNKNOWN", "checkpoint schema version is not supported")
    generation = store.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise SafetyBlock("STORE_SCHEMA_INVALID", "checkpoint generation is invalid")
    if store.get("payload_sha256") != _payload_digest(store):
        raise SafetyBlock("STORE_CHECKSUM_INVALID", "checkpoint payload digest does not match")
    _validate_event_log(store)
    _validate_history(store.get("history"))
    tasks = store.get("tasks")
    if not isinstance(tasks, dict):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "tasks must be an object")
    for task_id, task in tasks.items():
        _validate_task(task)
        if task["task_id"] != task_id:
            raise SafetyBlock("STORE_SCHEMA_INVALID", "task key does not match task_id")
    owner = store.get("session_owner")
    if owner is not None and not isinstance(owner, dict):
        raise SafetyBlock("STORE_SCHEMA_INVALID", "session_owner must be null or an object")
    if owner is not None:
        _validate_session_owner(owner)
    return store


def read_store(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    root = Path(root)
    checkpoint = root / "checkpoint.json"
    if not root.exists():
        raise InputError("STORE_NOT_FOUND", "runtime store has not been initialized")
    if root.is_symlink() or not root.is_dir():
        raise SafetyBlock("RUNTIME_ROOT_INVALID", "runtime root is not a directory")
    info = root.lstat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise SafetyBlock("RUNTIME_ROOT_INVALID", "runtime root permissions or owner changed")
    if not checkpoint.exists() and not checkpoint.is_symlink():
        candidates = [entry.name for entry in root.iterdir() if ".tmp." in entry.name]
        if candidates:
            raise SafetyBlock("STORE_MISSING_WITH_TEMP", "canonical checkpoint is missing while temp files exist")
        raise InputError("STORE_NOT_FOUND", "runtime store has not been initialized")
    if checkpoint.is_symlink():
        raise SafetyBlock("CHECKPOINT_SYMLINK", "checkpoint must not be a symlink")
    raw = _read_regular_bytes(
        checkpoint,
        MAX_CHECKPOINT_BYTES,
        "CHECKPOINT_MISSING",
        "CHECKPOINT_INVALID",
    )
    try:
        value = strict_json_loads(raw, MAX_CHECKPOINT_BYTES)
    except InputError as exc:
        raise SafetyBlock("CHECKPOINT_JSON_INVALID", "checkpoint is not strict JSON") from exc
    return _validate_store(value)


def _mutate_store(
    root: Path,
    expected_generation: int,
    mutator: Callable[[Dict[str, Any]], Any],
    events: Sequence[Mapping[str, Any]],
    hooks: Optional[Mapping[str, Callable[[], None]]] = None,
) -> Tuple[Dict[str, Any], Any]:
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before the write")
    updated = copy.deepcopy(current)
    result = mutator(updated)
    _append_events(updated, events)
    updated["generation"] = current["generation"] + 1
    updated["payload_sha256"] = _payload_digest(updated)
    _atomic_json_write(Path(root) / "checkpoint.json", updated, hooks=hooks)
    readback = read_store(root)
    if readback["generation"] != updated["generation"] or readback["payload_sha256"] != updated["payload_sha256"]:
        raise StorageRuntimeError("STORE_READBACK_MISMATCH", "checkpoint did not read back at the committed generation")
    return readback, result


def _initial_store() -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema_version": STORE_SCHEMA_VERSION,
        "generation": 0,
        "last_event_seq": 0,
        "events": [],
        "history": {"references": [], "barriers": []},
        "tasks": {},
        "session_owner": None,
    }
    value["payload_sha256"] = _payload_digest(value)
    return value


def init_store(root: Path = DEFAULT_ROOT, hooks: Optional[Mapping[str, Callable[[], None]]] = None) -> Dict[str, Any]:
    root = Path(root)
    _ensure_private_root(root)
    lease = SessionRoot(root)
    lease.acquire()
    try:
        checkpoint = root / "checkpoint.json"
        if checkpoint.exists() or checkpoint.is_symlink():
            existing = read_store(root)
            return {"result": "ALREADY_INITIALIZED", "generation": existing["generation"]}
        if lease.record is not None and lease.record.get("state") != "CLOSED":
            raise SafetyBlock("UNRESOLVED_OWNER_RECORD", "cannot initialize over an unresolved session owner")
        value = _initial_store()
        _atomic_json_write(checkpoint, value, hooks=hooks)
        return {"result": "INITIALIZED", "generation": 0}
    finally:
        lease.release_without_close()


def _source_reference(source_kind: str, path: Path, extra: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    path = Path(path)
    raw = _read_regular_bytes(path, MAX_CHECKPOINT_BYTES, "HISTORY_SOURCE_MISSING", "HISTORY_SOURCE_INVALID")
    reference: Dict[str, Any] = {
        "source_kind": source_kind,
        "path": str(path.resolve()),
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
        "imported_at_utc": utc_now(),
    }
    if extra:
        reference.update(copy.deepcopy(dict(extra)))
    return reference


def _load_json_source(path: Path) -> Tuple[bytes, Any, str]:
    raw = _read_regular_bytes(Path(path), MAX_CHECKPOINT_BYTES, "HISTORY_SOURCE_MISSING", "HISTORY_SOURCE_INVALID")
    try:
        value = strict_json_loads(raw, MAX_CHECKPOINT_BYTES)
    except InputError as exc:
        raise SafetyBlock("HISTORY_SOURCE_JSON_INVALID", "%s is not strict JSON" % Path(path).name) from exc
    return raw, value, sha256_bytes(raw)


def _barrier(
    source_kind: str,
    source_sha256: str,
    group_key: str,
    fingerprint: Mapping[str, Any],
    destinations: Sequence[str],
    verified_file_count: int,
    deny_reason: str,
    observed_title: str = "",
) -> Dict[str, Any]:
    identity = {
        "group_key": group_key,
        "start_date": fingerprint["start_date"],
        "end_date": fingerprint["end_date"],
        "expected_images": fingerprint["expected_images"],
        "observed_title": observed_title,
        "disambiguator": "history:%s" % source_kind,
    }
    _validate_identity(identity)
    payload = {
        "source_kind": source_kind,
        "source_sha256": source_sha256,
        "group_key": group_key,
        "identity": identity,
        "destinations": sorted(set(destinations)),
    }
    return {
        "barrier_id": sha256_bytes(canonical_json(payload)),
        "source_kind": source_kind,
        "source_sha256": source_sha256,
        "group_key": group_key,
        "identity": identity,
        "destinations": sorted(set(destinations)),
        "verified_file_count": verified_file_count,
        "deny_reason": deny_reason,
    }


def _strict_fingerprint(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SafetyBlock("HISTORY_FINGERPRINT_INVALID", "history fingerprint must be an object")
    required = {"start_date", "end_date", "expected_images"}
    if not required.issubset(value):
        raise SafetyBlock("HISTORY_FINGERPRINT_INVALID", "history fingerprint is incomplete")
    fingerprint = {
        "start_date": value["start_date"],
        "end_date": value["end_date"],
        "expected_images": value["expected_images"],
    }
    if not DATE_RE.fullmatch(str(fingerprint["start_date"])) or not DATE_RE.fullmatch(str(fingerprint["end_date"])):
        raise SafetyBlock("HISTORY_FINGERPRINT_INVALID", "history dates are invalid")
    if str(fingerprint["start_date"]) > str(fingerprint["end_date"]):
        raise SafetyBlock("HISTORY_FINGERPRINT_INVALID", "history date range is reversed")
    count = fingerprint["expected_images"]
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0 or count > MAX_EXPECTED_IMAGES:
        raise SafetyBlock("HISTORY_FINGERPRINT_INVALID", "history image count is invalid")
    return fingerprint


def _count_regular_directory(path: Path) -> int:
    path = Path(path)
    if not path.exists() or path.is_symlink() or not path.is_dir():
        raise SafetyBlock("HISTORY_DESTINATION_MISSING", "history destination is missing or invalid")
    count = 0
    for entry in path.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise SafetyBlock("HISTORY_DESTINATION_INVALID", "history destination contains a non-regular entry")
        count += 1
    return count


def _parse_pr28_identity(destination: str, expected_images: int) -> Dict[str, Any]:
    match = re.match(r"^(?:\d+-)?(\d{4}-\d{2}-\d{2})(?:_(\d{4}-\d{2}-\d{2}))?_(\d+)$", Path(destination).name)
    if not match:
        raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 destination name cannot supply a strict album identity")
    start_date = match.group(1)
    end_date = match.group(2) or start_date
    parsed_count = int(match.group(3))
    if parsed_count != expected_images:
        raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 destination count disagrees with the checkpoint")
    return {"start_date": start_date, "end_date": end_date, "expected_images": parsed_count}


def build_history_bundle(
    official_state: Path,
    manual_archives: Path,
    pr28_checkpoints: Path,
    exclusion_gate: Path,
    project_root: Path,
    pr28_root: Path,
    group_key: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    project_root = Path(project_root).resolve()
    pr28_root = Path(pr28_root).resolve()
    if not group_key:
        raise InputError("GROUP_KEY_REQUIRED", "group_key is required")
    references: List[Dict[str, Any]] = []
    barriers: List[Dict[str, Any]] = []
    totals = {"official_photos": 0, "manual_photos": 0, "pr28_photos": 0, "excluded_photos": 0}

    official_raw, official, official_sha = _load_json_source(official_state)
    references.append(
        _source_reference("official_state", official_state, {"bytes": len(official_raw), "sha256": official_sha})
    )
    if not isinstance(official, dict) or not isinstance(official.get("runs"), list):
        raise SafetyBlock("OFFICIAL_STATE_INVALID", "official state runs are missing")
    verified_runs = [run for run in official["runs"] if isinstance(run, dict) and run.get("workflow_outcome") == "VERIFIED"]
    if len(verified_runs) != 2:
        raise SafetyBlock("OFFICIAL_STATE_INVALID", "official state must contain two verified runs")
    seen_official = set()
    for run in verified_runs:
        fingerprint = _strict_fingerprint(run.get("fingerprint"))
        run_group = run.get("group_key")
        destination = run.get("destination")
        if not isinstance(run_group, str) or not run_group or not isinstance(destination, str) or not destination:
            raise SafetyBlock("OFFICIAL_STATE_INVALID", "verified run identity is incomplete")
        destination_path = Path(destination)
        if not destination_path.is_absolute():
            raise SafetyBlock("OFFICIAL_STATE_INVALID", "official destination must be absolute")
        count = _count_regular_directory(destination_path)
        if count != fingerprint["expected_images"]:
            raise SafetyBlock("OFFICIAL_STATE_SOURCE_INCOMPLETE", "official destination file count is incomplete")
        totals["official_photos"] += count
        identity_binding = canonical_json({"run_id": run.get("run_id"), "group": run_group, "fp": fingerprint})
        if identity_binding in seen_official:
            continue
        seen_official.add(identity_binding)
        barriers.append(
            _barrier(
                "official_state",
                official_sha,
                run_group,
                fingerprint,
                [str(destination_path)],
                count,
                "HISTORICAL_OFFICIAL_VERIFIED",
                str(run.get("observed_title") or ""),
            )
        )

    manual_raw, manual, manual_sha = _load_json_source(manual_archives)
    references.append(
        _source_reference("manual_archives", manual_archives, {"bytes": len(manual_raw), "sha256": manual_sha})
    )
    if not isinstance(manual, dict) or not isinstance(manual.get("entries"), list):
        raise SafetyBlock("MANUAL_ARCHIVES_INVALID", "manual archive entries are missing")
    manual_group = manual.get("group_key")
    if manual_group != group_key:
        raise SafetyBlock("MANUAL_GROUP_MISMATCH", "manual archive group does not match the requested group")
    for entry in manual["entries"]:
        if not isinstance(entry, dict):
            raise SafetyBlock("MANUAL_ARCHIVES_INVALID", "manual archive entry must be an object")
        fingerprint = _strict_fingerprint(entry.get("fingerprint"))
        file_count = entry.get("file_count")
        if file_count != fingerprint["expected_images"]:
            raise SafetyBlock("MANUAL_ARCHIVES_INVALID", "manual file count disagrees with its fingerprint")
        totals["manual_photos"] += int(file_count)
        manifest_path = project_root / str(entry.get("manifest_path") or "")
        verification_path = project_root / str(entry.get("verification_path") or "")
        manifest_raw = _read_regular_bytes(manifest_path, MAX_CHECKPOINT_BYTES, "MANUAL_MANIFEST_MISSING", "MANUAL_MANIFEST_INVALID")
        verification_raw = _read_regular_bytes(
            verification_path, MAX_CHECKPOINT_BYTES, "MANUAL_VERIFICATION_MISSING", "MANUAL_VERIFICATION_INVALID"
        )
        if sha256_bytes(manifest_raw) != entry.get("manifest_sha256"):
            raise SafetyBlock("MANUAL_MANIFEST_DIGEST_MISMATCH", "manual manifest digest does not match the registry")
        if sha256_bytes(verification_raw) != entry.get("verification_sha256"):
            raise SafetyBlock("MANUAL_VERIFICATION_DIGEST_MISMATCH", "manual verification digest does not match the registry")
        verification = strict_json_loads(verification_raw, MAX_CHECKPOINT_BYTES)
        if not isinstance(verification, dict) or verification.get("album", {}).get("expected_images") != file_count:
            raise SafetyBlock("MANUAL_VERIFICATION_INVALID", "manual verification does not bind the expected count")
        relative_destination = verification.get("destination_workspace_relative")
        if not isinstance(relative_destination, str):
            raise SafetyBlock("MANUAL_VERIFICATION_INVALID", "manual verification destination is missing")
        destination_path = (project_root / relative_destination).resolve()
        try:
            destination_path.relative_to(project_root)
        except ValueError as exc:
            raise SafetyBlock("MANUAL_VERIFICATION_INVALID", "manual destination escapes the project root") from exc
        count = _count_regular_directory(destination_path)
        if count != fingerprint["expected_images"]:
            raise SafetyBlock("MANUAL_SOURCE_INCOMPLETE", "manual destination file count is incomplete")
        barriers.append(
            _barrier(
                "manual_archives",
                manual_sha,
                group_key,
                fingerprint,
                [str(destination_path)],
                count,
                "HISTORICAL_MANUAL_VERIFIED",
            )
        )

    pr28_raw, pr28, pr28_sha = _load_json_source(pr28_checkpoints)
    references.append(
        _source_reference("pr28_checkpoints", pr28_checkpoints, {"bytes": len(pr28_raw), "sha256": pr28_sha})
    )
    if not isinstance(pr28, dict) or not isinstance(pr28.get("albums"), dict) or len(pr28["albums"]) != 5:
        raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 checkpoint must contain five albums")
    for label, checkpoint in pr28["albums"].items():
        if not isinstance(checkpoint, dict):
            raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 album checkpoint must be an object")
        expected = checkpoint.get("expected_images")
        verified = checkpoint.get("verified_images")
        status = checkpoint.get("status")
        destination = checkpoint.get("destination")
        if (
            not isinstance(expected, int)
            or isinstance(expected, bool)
            or expected <= 0
            or verified != expected
            or status != "FILES_VERIFIED"
            or checkpoint.get("unknown_outcome") is not False
        ):
            raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 checkpoint is not a complete verified album")
        if not isinstance(destination, str) or not destination:
            raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 destination is missing")
        destination_path = (pr28_root / destination).resolve()
        try:
            destination_path.relative_to(pr28_root)
        except ValueError as exc:
            raise SafetyBlock("PR2_CHECKPOINT_INVALID", "PR28 destination escapes the test package") from exc
        count = _count_regular_directory(destination_path)
        if count != expected:
            raise SafetyBlock("PR2_SOURCE_INCOMPLETE", "PR28 destination file count is incomplete")
        totals["pr28_photos"] += count
        fingerprint = _parse_pr28_identity(destination, int(expected))
        barriers.append(
            _barrier(
                "pr28_checkpoints",
                pr28_sha,
                group_key,
                fingerprint,
                [str(destination_path)],
                count,
                "HISTORICAL_PR2_MANUAL_VERIFIED",
            )
        )

    gate_raw, gate, gate_sha = _load_json_source(exclusion_gate)
    references.append(_source_reference("exclusion_gate", exclusion_gate, {"bytes": len(gate_raw), "sha256": gate_sha}))
    if not isinstance(gate, dict) or gate.get("acquire_attempt", {}).get("state_write_committed") is not False:
        raise SafetyBlock("EXCLUSION_GATE_INVALID", "exclusion gate does not prove a non-dispatching refusal")
    target = _strict_fingerprint(gate.get("target_fingerprint"))
    totals["excluded_photos"] = int(target["expected_images"])
    destination = gate.get("destination", {}).get("path") if isinstance(gate.get("destination"), dict) else None
    if not isinstance(destination, str) or not destination:
        raise SafetyBlock("EXCLUSION_GATE_INVALID", "exclusion destination is missing")
    destination_path = (project_root / destination).resolve()
    try:
        destination_path.relative_to(project_root)
    except ValueError as exc:
        raise SafetyBlock("EXCLUSION_GATE_INVALID", "exclusion destination escapes the project root") from exc
    barriers.append(
        _barrier(
            "exclusion_gate",
            gate_sha,
            group_key,
            target,
            [str(destination_path)],
            0,
            "HISTORICAL_OWNER_EXCLUSION",
        )
    )

    if totals != HISTORY_EXPECTED_TOTALS:
        raise SafetyBlock(
            "HISTORY_TOTALS_MISMATCH",
            "history totals do not match the frozen 239/109/329/65 barrier",
        )
    history = {"references": references, "barriers": barriers}
    _validate_history(history)
    binding = sha256_bytes(canonical_json(history))
    return history, {"totals": totals, "history_binding_sha256": binding, "barrier_count": len(barriers)}


def import_history(
    root: Path,
    official_state: Path,
    manual_archives: Path,
    pr28_checkpoints: Path,
    exclusion_gate: Path,
    project_root: Path,
    pr28_root: Path,
    group_key: str,
) -> Dict[str, Any]:
    history, summary = build_history_bundle(
        official_state,
        manual_archives,
        pr28_checkpoints,
        exclusion_gate,
        project_root,
        pr28_root,
        group_key,
    )
    root = Path(root)
    lease = SessionRoot(root)
    lease.acquire()
    try:
        current = read_store(root)
        if current["history"]["references"] or current["history"]["barriers"]:
            existing_binding = sha256_bytes(canonical_json(current["history"]))
            if existing_binding == summary["history_binding_sha256"]:
                return {"result": "ALREADY_IMPORTED", "generation": current["generation"], **summary}
            raise SafetyBlock("HISTORY_IMMUTABLE", "history is already imported with a different binding")

        def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
            store["history"] = copy.deepcopy(history)
            return summary

        updated, result = _mutate_store(
            root,
            current["generation"],
            mutate,
            [
                _event(
                    "HISTORY_IMPORTED",
                    session_id=None,
                    task_id=None,
                    evidence_reference=summary["history_binding_sha256"],
                )
            ],
        )
        return {"result": "IMPORTED", "generation": updated["generation"], **result}
    finally:
        lease.release_without_close()


def _fingerprints_overlap_family(
    identity: Mapping[str, Any], barrier_identity: Mapping[str, Any]
) -> str:
    if identity["group_key"] != barrier_identity["group_key"]:
        return "NONE"
    if (
        identity["start_date"] == barrier_identity["start_date"]
        and identity["end_date"] == barrier_identity["end_date"]
        and identity["expected_images"] == barrier_identity["expected_images"]
    ):
        return "EXACT"
    if identity["start_date"] == barrier_identity["start_date"] and identity["end_date"] == barrier_identity["end_date"]:
        return "AMBIGUOUS"
    return "NONE"


def _history_match(store: Mapping[str, Any], identity: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    matches = _history_matches(store, identity)
    return matches[0] if matches else None


def _history_matches(store: Mapping[str, Any], identity: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        barrier
        for barrier in store["history"]["barriers"]
        if _fingerprints_overlap_family(identity, barrier["identity"]) == "EXACT"
    ]


def _validate_live_history_barrier(store: Mapping[str, Any], barrier: Mapping[str, Any]) -> Dict[str, Any]:
    reference = next(
        (
            item
            for item in store["history"]["references"]
            if item["source_kind"] == barrier["source_kind"] and item["sha256"] == barrier["source_sha256"]
        ),
        None,
    )
    if reference is None:
        raise SafetyBlock("HISTORY_SOURCE_UNBOUND", "history barrier source reference is missing")
    source = Path(reference["path"])
    raw = _read_regular_bytes(source, MAX_CHECKPOINT_BYTES, "HISTORY_SOURCE_MISSING", "HISTORY_SOURCE_INVALID")
    if len(raw) != reference["bytes"] or sha256_bytes(raw) != reference["sha256"]:
        raise SafetyBlock("HISTORY_SOURCE_CHANGED", "history source bytes no longer match the imported reference")
    if barrier["verified_file_count"] > 0:
        if barrier["verified_file_count"] != barrier["identity"]["expected_images"]:
            raise SafetyBlock("HISTORY_BARRIER_COUNT_INVALID", "history barrier count is not the full album count")
        for destination in barrier["destinations"]:
            count = _count_regular_directory(Path(destination))
            if count != barrier["verified_file_count"]:
                raise SafetyBlock("HISTORY_DESTINATION_CHANGED", "history destination file count changed")
    return {"source_bytes": len(raw), "verified_file_count": int(barrier["verified_file_count"])}


def _history_conflict(
    store: Mapping[str, Any], identity: Mapping[str, Any], destination_absolute: Path
) -> Optional[Dict[str, Any]]:
    exact = []
    for barrier in store["history"]["barriers"]:
        relation = _fingerprints_overlap_family(identity, barrier["identity"])
        if relation == "EXACT":
            exact.append(barrier)
            continue
        if relation == "AMBIGUOUS":
            return {"code": "HISTORICAL_DATE_AMBIGUOUS", "barrier_id": barrier["barrier_id"], "relation": relation}
        if str(destination_absolute) in set(barrier["destinations"]):
            return {"code": "HISTORICAL_DESTINATION_PRESENT", "barrier_id": barrier["barrier_id"], "relation": "DESTINATION"}
    if exact:
        return None
    return None


def _exclusion_match(identity: Mapping[str, Any], exclusions: Sequence[Any]) -> Optional[str]:
    for item in exclusions:
        if isinstance(item, str):
            if item == identity["disambiguator"] or item == identity["observed_title"]:
                return "EXACT_STRING"
            continue
        if isinstance(item, dict):
            try:
                candidate = {
                    "group_key": item["group_key"],
                    "start_date": item["start_date"],
                    "end_date": item["end_date"],
                    "expected_images": item["expected_images"],
                    "observed_title": item.get("observed_title", ""),
                    "disambiguator": item.get("disambiguator", ""),
                }
                _validate_identity(candidate)
            except (KeyError, SafetyBlock) as exc:
                raise SafetyBlock("TASK_EXCLUSION_INVALID", "task exclusion identity is invalid") from exc
            relation = _fingerprints_overlap_family(identity, candidate)
            if relation != "NONE":
                return "EXACT_IDENTITY" if relation == "EXACT" else "EXCLUDED_DATE_AMBIGUOUS"
    return None


def _exclusion_conflict(identity: Mapping[str, Any], exclusions: Sequence[Any]) -> Optional[str]:
    match = _exclusion_match(identity, exclusions)
    if match == "EXCLUDED_DATE_AMBIGUOUS":
        return match
    return None


def _task_absolute_path(root: Path, task_id: str, relative: str) -> Path:
    normalized = _normalize_relative_destination(relative)
    task_root = (Path(root) / "tasks" / task_id).resolve()
    result = (task_root / normalized).resolve()
    try:
        result.relative_to(task_root)
    except ValueError as exc:
        raise SafetyBlock("DESTINATION_ESCAPE", "task destination escapes its task root") from exc
    return result


def create_task(root: Path, manifest_path: Path) -> Dict[str, Any]:
    root = Path(root)
    manifest_raw = _read_regular_bytes(Path(manifest_path), MAX_CHECKPOINT_BYTES, "TASK_MANIFEST_MISSING", "TASK_MANIFEST_INVALID")
    try:
        manifest = strict_json_loads(manifest_raw, MAX_CHECKPOINT_BYTES)
    except InputError as exc:
        raise SafetyBlock("TASK_MANIFEST_JSON_INVALID", "task manifest is not strict JSON") from exc
    required = {"schema_version", "task_id", "scope", "owner_authorization_reference", "exclusions", "albums"}
    if not isinstance(manifest, dict) or set(manifest) != required or manifest.get("schema_version") != 1:
        raise InputError("TASK_MANIFEST_INVALID", "task manifest shape or schema is invalid")
    task_id = manifest.get("task_id")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise InputError("TASK_ID_INVALID", "task_id is invalid")
    scope = manifest.get("scope")
    if not isinstance(scope, dict) or set(scope) != {"group_key", "app_identifier", "owner_id", "scope_id"}:
        raise InputError("TASK_SCOPE_INVALID", "task scope is invalid")
    if not all(isinstance(scope[key], str) and scope[key] for key in scope):
        raise InputError("TASK_SCOPE_INVALID", "task scope values are invalid")
    authorization = manifest.get("owner_authorization_reference")
    if not isinstance(authorization, str) or not authorization:
        raise InputError("OWNER_AUTHORIZATION_REQUIRED", "owner authorization reference is required")
    exclusions = manifest.get("exclusions")
    if not isinstance(exclusions, list):
        raise InputError("TASK_EXCLUSIONS_INVALID", "task exclusions must be a list")
    source_albums = manifest.get("albums")
    if not isinstance(source_albums, list) or len(source_albums) < 100:
        raise InputError("TASK_MANIFEST_TOO_SMALL", "task manifest must contain at least 100 albums")

    lease = SessionRoot(root)
    lease.acquire()
    try:
        current = read_store(root)
        if task_id in current["tasks"]:
            raise SafetyBlock("TASK_ALREADY_EXISTS", "task already exists and is immutable")
        if not current["history"]["references"] or not current["history"]["barriers"]:
            raise SafetyBlock("HISTORY_REQUIRED", "import the read-only history barrier before creating a task")
        albums: Dict[str, Dict[str, Any]] = {}
        order: List[str] = []
        skip_reasons: Dict[str, str] = {}
        seen_ranges: Dict[Tuple[str, str], int] = {}
        seen_destinations = set()
        for ordinal, source in enumerate(source_albums, start=1):
            if not isinstance(source, dict) or set(source) != {"identity", "destination"}:
                raise InputError("TASK_ALBUM_INVALID", "album entry shape is invalid")
            identity = copy.deepcopy(source["identity"])
            try:
                _validate_identity(identity)
            except SafetyBlock as exc:
                raise InputError(exc.code, exc.message) from exc
            if identity["group_key"] != scope["group_key"]:
                raise InputError("TASK_ALBUM_GROUP_MISMATCH", "album group does not match task scope")
            key = _album_key(scope["scope_id"], identity)
            if key in albums:
                raise SafetyBlock("TASK_ALBUM_DUPLICATE", "album identity is duplicated in the manifest")
            date_range = (identity["start_date"], identity["end_date"])
            if date_range in seen_ranges:
                raise SafetyBlock("TASK_DATE_AMBIGUOUS", "two manifest albums share a date range")
            seen_ranges[date_range] = identity["expected_images"]
            destination = _normalize_relative_destination(source["destination"])
            if destination in seen_destinations:
                raise SafetyBlock("TASK_DESTINATION_DUPLICATE", "two manifest albums share a destination")
            seen_destinations.add(destination)
            destination_absolute = _task_absolute_path(root, task_id, destination)
            conflict = _history_conflict(current, identity, destination_absolute)
            if conflict is not None:
                raise SafetyBlock(conflict["code"], "manifest album conflicts with immutable history")
            exclusion = _exclusion_conflict(identity, exclusions)
            if exclusion is not None:
                raise SafetyBlock(exclusion, "manifest album is excluded by the Owner manifest")
            history_match = _history_match(current, identity)
            exclusion_match = _exclusion_match(identity, exclusions)
            cross_task = None
            if history_match is None and exclusion_match is None:
                cross_task = _cross_task_fact(
                    root,
                    current,
                    task_id,
                    {"identity": identity},
                    deep=False,
                )
                if cross_task is not None and cross_task.get("blocked") is True:
                    raise SafetyBlock(
                        str(cross_task["reason"]),
                        "the album conflicts with immutable evidence in another task",
                    )
            if history_match is not None:
                skip_reasons[key] = "HISTORY_EXACT:%s" % history_match["barrier_id"]
            elif cross_task is not None:
                skip_reasons[key] = "CROSS_TASK_VERIFIED:%s:%s" % (
                    cross_task["other_task_id"],
                    cross_task["other_album_key"],
                )
            elif exclusion_match is not None:
                skip_reasons[key] = "OWNER_EXCLUSION_EXACT"
            albums[key] = {
                "ordinal": ordinal,
                "album_key": key,
                "identity": identity,
                "destination": destination,
                "save_all_intent": None,
                "chooser_confirm_intent": None,
                "verification": None,
            }
            order.append(key)

        task_root = root / "tasks" / task_id
        if task_root.exists() or task_root.is_symlink():
            raise SafetyBlock("TASK_DIRECTORY_EXISTS", "task directory already exists")
        _ensure_private_directory(root / "tasks")
        active_destinations = [key for key in order if key not in skip_reasons]
        for key in active_destinations:
            destination = _task_absolute_path(root, task_id, albums[key]["destination"])
            if destination.exists() or destination.is_symlink():
                raise SafetyBlock("TASK_DESTINATION_EXISTS", "task destination already exists")
        created_destinations: List[Path] = []
        try:
            _ensure_private_directory(task_root)
            _ensure_private_directory(task_root / "evidence")
            for key in active_destinations:
                destination = _task_absolute_path(root, task_id, albums[key]["destination"])
                _ensure_private_directory(destination.parent)
                destination.mkdir(mode=0o700, exist_ok=False)
                created_destinations.append(destination)
        except Exception:
            for destination in reversed(created_destinations):
                try:
                    destination.rmdir()
                except OSError:
                    pass
            try:
                (task_root / "evidence").rmdir()
            except OSError:
                pass
            try:
                task_root.rmdir()
            except OSError:
                pass
            raise

        task = {
            "task_id": task_id,
            "created_at_utc": utc_now(),
            "scope": copy.deepcopy(scope),
            "owner_authorization_reference": authorization,
            "exclusions": copy.deepcopy(exclusions),
            "manifest_sha256": sha256_bytes(manifest_raw),
            "manifest_binding_sha256": "",
            "album_order": order,
            "albums": albums,
        }
        task["manifest_binding_sha256"] = _manifest_binding(task)
        _validate_task(task)

        def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
            store["tasks"][task_id] = copy.deepcopy(task)
            return {
                "task_id": task_id,
                "album_count": len(order),
                "manifest_sha256": task["manifest_sha256"],
                "skipped_existing_count": len(skip_reasons),
            }

        updated, result = _mutate_store(
            root,
            current["generation"],
            mutate,
            [
                _event(
                    "TASK_CREATED",
                    session_id=None,
                    task_id=task_id,
                    evidence_reference=task["manifest_binding_sha256"],
                )
            ],
        )
        return {"result": "TASK_CREATED", "generation": updated["generation"], **result}
    finally:
        lease.release_without_close()


def _destination_is_empty(path: Path) -> bool:
    path = Path(path)
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise SafetyBlock("DESTINATION_MISSING", "album destination is missing") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise SafetyBlock("DESTINATION_INVALID", "destination must be a current-user real directory")
    try:
        next(path.iterdir())
    except StopIteration:
        return True
    return False


def _inventory_directory(path: Path, max_entries: int = MAX_EXPECTED_IMAGES) -> Dict[str, Any]:
    path = Path(path)
    try:
        root_info = path.lstat()
    except FileNotFoundError as exc:
        raise SafetyBlock("DESTINATION_MISSING", "album destination is missing") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode) or root_info.st_uid != os.getuid():
        raise SafetyBlock("DESTINATION_INVALID", "destination must be a current-user real directory")
    try:
        names = sorted(entry.name for entry in path.iterdir())
    except OSError as exc:
        raise StorageRuntimeError("DESTINATION_READ_FAILED", "destination inventory cannot be read") from exc
    if len(names) > max_entries:
        raise SafetyBlock("DESTINATION_TOO_LARGE", "destination has more entries than the expected-image limit")
    entries: List[Dict[str, Any]] = []
    for name in names:
        if not name or "/" in name or "\\" in name or name in (".", "..") or "\x00" in name:
            raise SafetyBlock("DESTINATION_INVALID", "destination contains an invalid entry name")
        if name.lower().endswith(PARTIAL_SUFFIXES):
            raise SafetyBlock("PARTIAL_FILE_PRESENT", "destination contains a partial or temporary file")
        entry_path = path / name
        try:
            before_path = entry_path.lstat()
        except OSError as exc:
            raise SafetyBlock("DESTINATION_CHANGED", "destination changed while it was inventoried") from exc
        if not stat.S_ISREG(before_path.st_mode) or stat.S_ISLNK(before_path.st_mode) or before_path.st_uid != os.getuid():
            raise SafetyBlock("DESTINATION_INVALID", "destination contains a non-regular file")
        if before_path.st_size <= 0:
            raise SafetyBlock("ZERO_BYTE_FILE", "destination contains a zero-byte file")
        try:
            fd = os.open(
                entry_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0),
            )
        except OSError as exc:
            raise SafetyBlock("DESTINATION_READ_FAILED", "destination entry cannot be opened safely") from exc
        digest = hashlib.sha256()
        total = 0
        try:
            before = os.fstat(fd)
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 512 * 1024 * 1024:
                    raise SafetyBlock("DESTINATION_FILE_TOO_LARGE", "destination image exceeds the supported size")
                digest.update(chunk)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        if (
            before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
            or total != before.st_size
        ):
            raise SafetyBlock("DESTINATION_CHANGED", "destination entry changed while it was hashed")
        entries.append(
            {
                "name": name,
                "bytes": total,
                "sha256": digest.hexdigest(),
                "mtime_ns": before.st_mtime_ns,
                "ctime_ns": before.st_ctime_ns,
                "decoded": False,
                "width": 0,
                "height": 0,
                "content_type": "UNKNOWN",
            }
        )
    return {
        "entries": entries,
        "count": len(entries),
        "sha256": _inventory_digest(entries),
    }


def _sample_stable_inventory(
    path: Path,
    *,
    required_samples: int = 3,
    interval_seconds: float = 3.0,
    timeout_seconds: float = 600.0,
    require_nonempty: bool = True,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    if not isinstance(required_samples, int) or isinstance(required_samples, bool) or required_samples < 1:
        raise InputError("STABILITY_SAMPLE_COUNT_INVALID", "stability sample count is invalid")
    if interval_seconds < 0 or timeout_seconds < 0:
        raise InputError("STABILITY_TIMING_INVALID", "stability timing is invalid")
    started = time.monotonic()
    stable_count = 0
    previous_digest: Optional[str] = None
    latest: Optional[Dict[str, Any]] = None
    while stable_count < required_samples:
        if previous_digest is not None and interval_seconds:
            remaining = timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise SafetyBlock("DESTINATION_STABILITY_TIMEOUT", "destination inventory did not stabilize in time")
            sleep_fn(min(interval_seconds, remaining))
        latest = _inventory_directory(path)
        if require_nonempty and latest["count"] == 0:
            remaining = timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise SafetyBlock("DESTINATION_EMPTY", "destination inventory remained empty")
            if interval_seconds:
                sleep_fn(min(interval_seconds, remaining))
            continue
        if latest["sha256"] == previous_digest:
            stable_count += 1
        else:
            stable_count = 1
            previous_digest = latest["sha256"]
        if time.monotonic() - started > timeout_seconds:
            raise SafetyBlock("DESTINATION_STABILITY_TIMEOUT", "destination inventory did not stabilize in time")
    assert latest is not None
    return {**latest, "stability_samples": stable_count}


def _validate_decoder_source() -> None:
    if not IMAGE_DECODER_SOURCE.exists() or IMAGE_DECODER_SOURCE.is_symlink():
        raise SafetyBlock("IMAGE_DECODER_MISSING", "pinned ImageIO decoder source is missing")
    digest = sha256_file(IMAGE_DECODER_SOURCE)
    if digest != IMAGE_DECODER_SOURCE_SHA256:
        raise SafetyBlock("IMAGE_DECODER_SOURCE_CHANGED", "pinned ImageIO decoder source digest changed")


def _compile_decoder(directory: Path) -> Path:
    _validate_decoder_source()
    binary = Path(directory) / "image_decode"
    try:
        sdk_result = subprocess.run(
            ["xcrun", "--sdk", "macosx", "--show-sdk-path"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=_process_env(),
        )
        sdk_path = sdk_result.stdout.strip()
        if sdk_result.returncode != 0 or not sdk_path:
            raise StorageRuntimeError("MACOS_SDK_UNAVAILABLE", "the active macOS SDK path is unavailable")
        compile_result = subprocess.run(
            ["xcrun", "--sdk", "macosx", "swiftc", "-sdk", sdk_path, "-O", str(IMAGE_DECODER_SOURCE), "-o", str(binary)],
            check=False,
            capture_output=True,
            timeout=180,
            env=_process_env(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise StorageRuntimeError("IMAGE_DECODER_COMPILE_FAILED", "pinned ImageIO decoder did not compile") from exc
    if compile_result.returncode != 0 or not binary.exists() or binary.is_symlink() or not stat.S_ISREG(binary.stat().st_mode):
        raise StorageRuntimeError("IMAGE_DECODER_COMPILE_FAILED", "pinned ImageIO decoder did not compile")
    return binary


_ORIGINAL_COMPILE_DECODER = _compile_decoder
_DECODER_CACHE_CONTEXT: Optional[tempfile.TemporaryDirectory[str]] = None
_DECODER_CACHE: Dict[str, Path] = {}


def _compile_decoder_once() -> Path:
    global _DECODER_CACHE_CONTEXT

    compile_decoder = _compile_decoder
    cacheable = compile_decoder is _ORIGINAL_COMPILE_DECODER
    if cacheable:
        cached = _DECODER_CACHE.get(IMAGE_DECODER_SOURCE_SHA256)
        if cached is not None and cached.exists() and not cached.is_symlink() and stat.S_ISREG(cached.stat().st_mode):
            return cached
    if _DECODER_CACHE_CONTEXT is None:
        _DECODER_CACHE_CONTEXT = tempfile.TemporaryDirectory(prefix="line-backup-agent-resume-decoder-")
    binary = compile_decoder(Path(_DECODER_CACHE_CONTEXT.name))
    if cacheable:
        _DECODER_CACHE[IMAGE_DECODER_SOURCE_SHA256] = Path(binary)
    return Path(binary)


def _decode_inventory(
    path: Path,
    expected_images: int,
    *,
    decoder_binary: Optional[Path] = None,
) -> Tuple[Dict[str, Dict[str, Any]], str]:
    _validate_decoder_source()
    path = Path(path)
    try:
        if decoder_binary is None:
            decoder_binary = _compile_decoder_once()
        binary = Path(decoder_binary)
        if binary.is_symlink() or not binary.exists() or not stat.S_ISREG(binary.stat().st_mode):
            raise StorageRuntimeError("IMAGE_DECODER_MISSING", "compiled ImageIO decoder is unavailable")
        binary_sha256 = sha256_file(binary)
        decode_result = subprocess.run(
            [str(binary), str(path), str(expected_images)],
            check=False,
            capture_output=True,
            timeout=max(60, min(600, expected_images * 5)),
            env=_process_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise StorageRuntimeError("IMAGE_DECODER_TIMEOUT", "pinned ImageIO decoder timed out") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise StorageRuntimeError("IMAGE_DECODER_EXECUTION_FAILED", "pinned ImageIO decoder failed to execute") from exc
    if decode_result.returncode != 0 or not decode_result.stdout:
        stderr = decode_result.stderr.decode("utf-8", errors="replace").strip()[:512]
        detail = "exit %d" % decode_result.returncode
        if stderr:
            detail += "; %s" % stderr
        raise SafetyBlock("IMAGE_DECODE_REJECTED", "pinned ImageIO decoder rejected the destination: %s" % detail)
    try:
        decoded = strict_json_loads(decode_result.stdout, MAX_DECODER_OUTPUT_BYTES)
    except InputError as exc:
        raise SafetyBlock("IMAGE_DECODER_OUTPUT_INVALID", "pinned ImageIO decoder output is not strict JSON") from exc
    if not isinstance(decoded, dict) or decoded.get("verdict") != "PASS":
        actual = decoded.get("actualEntries") if isinstance(decoded, dict) else None
        raise SafetyBlock(
            "IMAGE_DECODE_REJECTED",
            "pinned ImageIO decoder did not pass every image (actual entries: %s)" % actual,
        )
    if decoded.get("expected") != expected_images or decoded.get("actualEntries") != expected_images:
        raise SafetyBlock("IMAGE_DECODE_COUNT_MISMATCH", "pinned ImageIO decoder count disagrees with the expected count")
    if decoded.get("destination") != str(path):
        raise SafetyBlock("IMAGE_DECODE_DESTINATION_MISMATCH", "pinned ImageIO decoder did not read the fixed destination")
    raw_entries = decoded.get("entries")
    if not isinstance(raw_entries, list) or len(raw_entries) != expected_images:
        raise SafetyBlock("IMAGE_DECODER_OUTPUT_INVALID", "pinned ImageIO decoder entries are incomplete")
    result: Dict[str, Dict[str, Any]] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict) or raw_entry.get("decoded") is not True:
            raise SafetyBlock("IMAGE_DECODE_REJECTED", "pinned ImageIO decoder did not fully decode every image")
        name = raw_entry.get("name")
        width = raw_entry.get("width")
        height = raw_entry.get("height")
        content_type = raw_entry.get("contentType")
        digest = raw_entry.get("sha256")
        if (
            not isinstance(name, str)
            or not name
            or name in result
            or not isinstance(width, int)
            or isinstance(width, bool)
            or width <= 0
            or not isinstance(height, int)
            or isinstance(height, bool)
            or height <= 0
            or not isinstance(content_type, str)
            or not content_type
            or not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
        ):
            raise SafetyBlock("IMAGE_DECODER_OUTPUT_INVALID", "pinned ImageIO decoder returned an invalid entry")
        result[name] = {
            "decoded": True,
            "width": width,
            "height": height,
            "content_type": content_type,
            "sha256": digest,
        }
    return result, binary_sha256


def _apply_decode_result(inventory: Mapping[str, Any], decoded: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    entries = copy.deepcopy(list(inventory["entries"]))
    if len(entries) != len(decoded):
        raise SafetyBlock("IMAGE_DECODE_COUNT_MISMATCH", "decoder result does not match the inventory")
    for entry in entries:
        decoded_entry = decoded.get(entry["name"])
        if decoded_entry is None or decoded_entry.get("sha256") != entry["sha256"]:
            raise SafetyBlock("IMAGE_DECODE_HASH_MISMATCH", "decoder result does not bind the same file bytes")
        entry["decoded"] = True
        entry["width"] = decoded_entry["width"]
        entry["height"] = decoded_entry["height"]
        entry["content_type"] = decoded_entry["content_type"]
    return entries


def _content_entry_binding(entries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    keys = ("name", "bytes", "sha256", "mtime_ns", "ctime_ns")
    return [{key: entry[key] for key in keys} for entry in entries]


def _verification_entry_binding(entries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {key: entry[key] for key in sorted(VERIFICATION_ENTRY_KEYS)}
        for entry in entries
    ]


def _flush_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    for entry in inventory["entries"]:
        entry_path = Path(path) / entry["name"]
        try:
            fd = os.open(
                entry_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            )
        except OSError as exc:
            raise StorageRuntimeError("PHOTO_FLUSH_FAILED", "downloaded photo could not be flushed") from exc
        try:
            _full_sync(fd)
        except OSError as exc:
            raise StorageRuntimeError("PHOTO_FLUSH_FAILED", "downloaded photo flush failed") from exc
        finally:
            os.close(fd)
    try:
        _directory_sync(Path(path))
    except OSError as exc:
        raise StorageRuntimeError("DESTINATION_FLUSH_FAILED", "downloaded destination directory flush failed") from exc


def _verification_matches_current(
    path: Path,
    verification: Mapping[str, Any],
    *,
    decoder_binary: Optional[Path] = None,
) -> Dict[str, Any]:
    if verification["decoder_source_sha256"] != IMAGE_DECODER_SOURCE_SHA256:
        raise SafetyBlock("VERIFIED_DECODER_SOURCE_CHANGED", "verification was not bound to the pinned decoder source")
    if verification["expected_images"] != verification["actual_entries"]:
        raise SafetyBlock("VERIFIED_COUNT_INVALID", "verification entry count is incomplete")
    if verification["pre_inventory_sha256"] != verification["post_inventory_sha256"]:
        raise SafetyBlock("VERIFIED_INVENTORY_UNSTABLE", "verified inventory digest changed around decode and flush")
    before = _inventory_directory(path, max_entries=max(MAX_EXPECTED_IMAGES, int(verification["expected_images"]) + 1))
    if before["count"] != verification["expected_images"]:
        raise SafetyBlock("VERIFIED_CONTENT_CHANGED", "previously verified album content changed")
    if _content_entry_binding(before["entries"]) != _content_entry_binding(verification["inventory"]):
        raise SafetyBlock("VERIFIED_CONTENT_CHANGED", "previously verified album content changed")
    decoded, binary_sha256 = _decode_inventory(
        path,
        int(verification["expected_images"]),
        decoder_binary=decoder_binary,
    )
    decoded_entries = _apply_decode_result(before, decoded)
    after = _inventory_directory(path, max_entries=max(MAX_EXPECTED_IMAGES, int(verification["expected_images"]) + 1))
    if after["sha256"] != before["sha256"] or after["entries"] != before["entries"]:
        raise SafetyBlock("DESTINATION_CHANGED", "destination changed during post-decode verification")
    if _verification_entry_binding(decoded_entries) != _verification_entry_binding(verification["inventory"]):
        raise SafetyBlock("VERIFIED_CONTENT_CHANGED", "previously verified decoder facts changed")
    if _inventory_digest(decoded_entries) != verification["inventory_sha256"]:
        raise SafetyBlock("VERIFIED_CONTENT_CHANGED", "verified inventory digest does not match current content")
    if binary_sha256 == "":
        raise StorageRuntimeError("IMAGE_DECODER_IDENTITY_MISSING", "decoder binary identity is missing")
    return {"verified": True, "inventory_sha256": before["sha256"], "decoder_binary_sha256": binary_sha256}


def _cross_task_fact(
    root: Path,
    store: Mapping[str, Any],
    task_id: str,
    album: Mapping[str, Any],
    *,
    deep: bool,
    decoder_binary: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    verified: List[Tuple[str, str, Mapping[str, Any]]] = []
    unresolved: List[Tuple[str, str, str]] = []
    for other_task_id, other_task in store["tasks"].items():
        if other_task_id == task_id:
            continue
        for other_key in other_task["album_order"]:
            other_album = other_task["albums"][other_key]
            relation = _fingerprints_overlap_family(album["identity"], other_album["identity"])
            if relation == "AMBIGUOUS":
                return {
                    "reason": "CROSS_TASK_DATE_AMBIGUOUS",
                    "blocked": True,
                    "other_task_id": other_task_id,
                    "other_album_key": other_key,
                    "verified_file_count": 0,
                }
            if relation != "EXACT":
                continue
            if other_album["verification"] is not None:
                verified.append((other_task_id, other_key, other_album))
                continue
            if other_album["save_all_intent"] is not None or other_album["chooser_confirm_intent"] is not None:
                unresolved.append((other_task_id, other_key, "CROSS_TASK_INTENT_UNRESOLVED"))
    if unresolved:
        other_task_id, other_key, reason = unresolved[0]
        return {
            "reason": reason,
            "blocked": True,
            "other_task_id": other_task_id,
            "other_album_key": other_key,
            "verified_file_count": 0,
        }
    if not verified:
        return None
    for other_task_id, other_key, other_album in verified:
        if deep:
            other_destination = _task_absolute_path(root, other_task_id, other_album["destination"])
            _verification_matches_current(
                other_destination,
                other_album["verification"],
                decoder_binary=decoder_binary,
            )
    first_task_id, first_key, first_album = verified[0]
    return {
        "reason": "CROSS_TASK_VERIFIED",
        "blocked": False,
        "other_task_id": first_task_id,
        "other_album_key": first_key,
        "verified_file_count": int(first_album["verification"]["actual_entries"]),
    }


def _album_history_skip(
    store: Mapping[str, Any],
    task: Mapping[str, Any],
    album: Mapping[str, Any],
    *,
    root: Optional[Path] = None,
    deep: bool = False,
    decoder_binary: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    matches = _history_matches(store, album["identity"])
    if matches:
        bindings = set()
        for barrier in matches:
            _validate_live_history_barrier(store, barrier)
            bindings.add((barrier["verified_file_count"], tuple(barrier["destinations"])))
        if len(bindings) != 1:
            raise SafetyBlock("HISTORY_MATCH_AMBIGUOUS", "multiple exact history barriers disagree")
        barrier = matches[0]
        return {
            "reason": "HISTORY_EXACT",
            "barrier_id": barrier["barrier_id"],
            "source_kind": barrier["source_kind"],
            "verified_file_count": barrier["verified_file_count"],
        }
    if root is not None:
        cross_task = _cross_task_fact(
            Path(root),
            store,
            task["task_id"],
            album,
            deep=deep,
            decoder_binary=decoder_binary,
        )
        if cross_task is not None:
            return cross_task
    exclusion = _exclusion_match(album["identity"], task["exclusions"])
    if exclusion is not None:
        return {"reason": "OWNER_EXCLUSION_EXACT", "barrier_id": None, "source_kind": "owner_manifest"}
    return None


def _intent_returned(intent: Optional[Mapping[str, Any]]) -> bool:
    return bool(
        isinstance(intent, dict)
        and isinstance(intent.get("result"), dict)
        and intent["result"].get("outcome") == "RETURNED"
    )


def _derive_album_state(
    root: Path,
    store: Mapping[str, Any],
    task: Mapping[str, Any],
    album: Mapping[str, Any],
    *,
    deep: bool,
    decoder_binary: Optional[Path] = None,
) -> Dict[str, Any]:
    album_key = album["album_key"]
    try:
        skip = _album_history_skip(
            store,
            task,
            album,
            root=root,
            deep=deep,
            decoder_binary=decoder_binary,
        )
    except ResumeError as exc:
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "BLOCKED_AMBIGUOUS",
            "dispatchable": False,
            "reason": exc.code,
            "inventory_count": 0,
        }
    if skip is not None:
        if skip.get("blocked") is True:
            return {
                "album_key": album_key,
                "ordinal": album["ordinal"],
                "state": "BLOCKED_AMBIGUOUS",
                "dispatchable": False,
                "reason": skip["reason"],
                "history": skip,
                "inventory_count": 0,
            }
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "SKIPPED_EXISTING",
            "dispatchable": False,
            "reason": skip["reason"],
            "history": skip,
            "inventory_count": int(album["identity"]["expected_images"]),
        }
    destination = _task_absolute_path(root, task["task_id"], album["destination"])
    if album["verification"] is not None:
        if deep:
            try:
                _verification_matches_current(
                    destination,
                    album["verification"],
                    decoder_binary=decoder_binary,
                )
            except ResumeError as exc:
                return {
                    "album_key": album_key,
                    "ordinal": album["ordinal"],
                    "state": "BLOCKED_AMBIGUOUS",
                    "dispatchable": False,
                    "reason": exc.code,
                    "inventory_count": album["verification"]["actual_entries"],
                }
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "VERIFIED",
            "dispatchable": False,
            "reason": None,
            "inventory_count": album["verification"]["actual_entries"],
        }

    save_intent = album["save_all_intent"]
    if save_intent is None:
        try:
            empty = _destination_is_empty(destination)
        except ResumeError as exc:
            return {
                "album_key": album_key,
                "ordinal": album["ordinal"],
                "state": "BLOCKED_AMBIGUOUS",
                "dispatchable": False,
                "reason": exc.code,
                "inventory_count": 0,
            }
        if empty:
            return {
                "album_key": album_key,
                "ordinal": album["ordinal"],
                "state": "NOT_STARTED",
                "dispatchable": True,
                "reason": None,
                "inventory_count": 0,
            }
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "BLOCKED_AMBIGUOUS",
            "dispatchable": False,
            "reason": "DESTINATION_NOT_EMPTY_WITHOUT_INTENT",
            "inventory_count": 0,
        }

    if not _intent_returned(save_intent):
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "UNKNOWN",
            "dispatchable": False,
            "reason": "SAVE_ALL_OUTCOME_UNKNOWN",
            "inventory_count": 0,
        }
    chooser_intent = album["chooser_confirm_intent"]
    if chooser_intent is None:
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "UNKNOWN",
            "dispatchable": False,
            "reason": "CHOOSER_OUTCOME_UNKNOWN",
            "inventory_count": 0,
        }
    if not _intent_returned(chooser_intent):
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": "UNKNOWN",
            "dispatchable": False,
            "reason": "CHOOSER_OUTCOME_UNKNOWN",
            "inventory_count": 0,
        }
    try:
        inventory = _inventory_directory(destination, max_entries=max(MAX_EXPECTED_IMAGES, album["identity"]["expected_images"] + 1))
    except ResumeError as exc:
        state = "UNKNOWN" if exc.code == "DESTINATION_MISSING" else "BLOCKED_AMBIGUOUS"
        return {
            "album_key": album_key,
            "ordinal": album["ordinal"],
            "state": state,
            "dispatchable": False,
            "reason": exc.code,
            "inventory_count": 0,
        }
    count = inventory["count"]
    expected = album["identity"]["expected_images"]
    if count == 0:
        state = "UNKNOWN"
        reason = "DOWNLOAD_NOT_OBSERVED"
    elif count < expected:
        state = "BLOCKED_PARTIAL"
        reason = "INCOMPLETE_DOWNLOAD"
    elif count > expected:
        state = "BLOCKED_AMBIGUOUS"
        reason = "UNEXPECTED_EXTRA_FILES"
    else:
        state = "VERIFYING"
        reason = "FULL_INVENTORY_NEEDS_VERIFICATION"
    return {
        "album_key": album_key,
        "ordinal": album["ordinal"],
        "state": state,
        "dispatchable": False,
        "reason": reason,
        "inventory_count": count,
    }


def derive_task_state(
    root: Path,
    store: Mapping[str, Any],
    task_id: str,
    *,
    deep: bool = False,
) -> Dict[str, Any]:
    if task_id not in store["tasks"]:
        raise InputError("TASK_NOT_FOUND", "task does not exist")
    task = store["tasks"][task_id]
    albums = []
    for album_key in task["album_order"]:
        albums.append(
            _derive_album_state(
                root,
                store,
                task,
                task["albums"][album_key],
                deep=deep,
                decoder_binary=None,
            )
        )
    blockers = [
        item
        for item in albums
        if item["state"] in ("BLOCKED_PARTIAL", "BLOCKED_AMBIGUOUS", "UNKNOWN")
    ]
    verifying = next((item for item in albums if item["state"] == "VERIFYING"), None)
    next_dispatch = None
    if not blockers and verifying is None:
        next_dispatch = next((item for item in albums if item["state"] == "NOT_STARTED"), None)
    counts: Dict[str, int] = {state: 0 for state in ALBUM_STATES}
    for item in albums:
        counts[item["state"]] += 1
    photo_count = sum(
        int(item["inventory_count"])
        for item in albums
        if item["state"] in ("VERIFIED", "SKIPPED_EXISTING")
    )
    if blockers:
        phase = "BLOCKED_AND_PRESERVE_WHOLE_TASK"
        next_action = "STOP_AND_RECONCILE_ONLY"
    elif verifying is not None:
        phase = "READY_TO_VERIFY"
        next_action = "VERIFY_ALBUM:%s" % verifying["album_key"]
    elif next_dispatch is not None:
        phase = "READY_TO_DISPATCH"
        next_action = "PREPARE_SAVE_ALL:%s" % next_dispatch["album_key"]
    else:
        phase = "COMPLETE"
        next_action = "NONE"
    first_blocker = blockers[0] if blockers else None
    return {
        "task_id": task_id,
        "generation": store["generation"],
        "checkpoint_sha256": store["payload_sha256"],
        "manifest_sha256": task["manifest_sha256"],
        "manifest_binding_sha256": task["manifest_binding_sha256"],
        "task_phase": phase,
        "album_count": len(albums),
        "albums": albums,
        "counts": counts,
        "photo_count": photo_count,
        "first_blocker": first_blocker,
        "next_safe_album_key": next_dispatch["album_key"] if next_dispatch is not None else None,
        "next_safe_ordinal": next_dispatch["ordinal"] if next_dispatch is not None else None,
        "next_safe_action": next_action,
        "gui_dispatches": 0,
    }


def inspect_task(root: Path, task_id: str) -> Dict[str, Any]:
    first = read_store(root)
    result = derive_task_state(root, first, task_id, deep=False)
    second = read_store(root)
    if first["generation"] != second["generation"] or first["payload_sha256"] != second["payload_sha256"]:
        raise SafetyBlock("GENERATION_UNSTABLE", "checkpoint changed during the read-only inspection")
    return result


def reconcile_task(root: Path, task_id: str) -> Dict[str, Any]:
    first = read_store(root)
    result = derive_task_state(root, first, task_id, deep=True)
    second = read_store(root)
    if first["generation"] != second["generation"] or first["payload_sha256"] != second["payload_sha256"]:
        raise SafetyBlock("GENERATION_UNSTABLE", "checkpoint changed during read-only reconciliation")
    return result


def _task_album(store: Mapping[str, Any], task_id: str, album_key: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if task_id not in store["tasks"]:
        raise InputError("TASK_NOT_FOUND", "task does not exist")
    task = store["tasks"][task_id]
    if album_key not in task["albums"]:
        raise InputError("ALBUM_NOT_FOUND", "album does not exist in the task manifest")
    return task, task["albums"][album_key]


def _intent_ack(result: Mapping[str, Any], action_id: str, generation: int, checkpoint_sha256: str) -> Dict[str, Any]:
    return {
        **dict(result),
        "action_id": action_id,
        "generation": generation,
        "checkpoint_sha256": checkpoint_sha256,
        "click_eligible": True,
    }


def prepare_save_all(
    root: Path,
    task_id: str,
    session_id: str,
    expected_generation: int,
    album_key: str,
    grounding: Mapping[str, Any],
) -> Dict[str, Any]:
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before save-all preparation")
    task, album = _task_album(current, task_id, album_key)
    if album["save_all_intent"] is not None:
        raise SafetyBlock("SAVE_ALL_INTENT_EXISTS", "save-all was already prepared for this album")
    if album["verification"] is not None or _album_history_skip(current, task, album, root=root, deep=False) is not None:
        raise SafetyBlock("ALBUM_NOT_DISPATCHABLE", "album is already verified or historical")
    derived = derive_task_state(root, current, task_id, deep=True)
    if derived["first_blocker"] is not None:
        raise SafetyBlock("TASK_BLOCKED", "an unresolved task blocker prevents any new dispatch")
    if derived["next_safe_album_key"] != album_key:
        raise SafetyBlock("ALBUM_NOT_NEXT_SAFE", "album is not the next safe manifest item")
    try:
        _validate_save_all_grounding(grounding, scope=task["scope"], album=album)
    except SafetyBlock as exc:
        raise InputError("SAVE_ALL_GROUNDING_INVALID", exc.message) from exc
    destination = _task_absolute_path(root, task_id, album["destination"])
    task_root = (Path(root) / "tasks" / task_id).resolve()
    try:
        destination.relative_to(task_root)
    except ValueError as exc:
        raise SafetyBlock("DESTINATION_ESCAPE", "album destination escapes the task root") from exc
    if not _destination_is_empty(destination):
        raise SafetyBlock("DESTINATION_NOT_EMPTY", "save-all destination is not empty")
    action_id = str(uuid.uuid4())
    intent = {
        "action_id": action_id,
        "prepared_at_utc": utc_now(),
        "session_id": session_id,
        "album_key": album_key,
        "scope_sha256": _scope_digest(task["scope"]),
        "destination": album["destination"],
        "grounding": copy.deepcopy(dict(grounding)),
        "result": None,
    }

    def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
        store["tasks"][task_id]["albums"][album_key]["save_all_intent"] = copy.deepcopy(intent)
        _set_session_pending_in_store(store, session_id, True)
        return {"album_key": album_key, "prepare": "SAVE_ALL", "destination": album["destination"]}

    updated, result = _mutate_store(
        root,
        expected_generation,
        mutate,
        [
            _event(
                "PREPARE_SAVE_ALL",
                session_id=session_id,
                task_id=task_id,
                album_key=album_key,
                from_state="NOT_STARTED",
                to_state="UNKNOWN",
                evidence_reference=action_id,
            )
        ],
    )
    return _intent_ack(result, action_id, updated["generation"], updated["payload_sha256"])


def record_save_all_result(
    root: Path,
    task_id: str,
    session_id: str,
    expected_generation: int,
    album_key: str,
    action_id: str,
    outcome: str,
    evidence_sha256: str,
) -> Dict[str, Any]:
    if outcome not in INTENT_OUTCOMES:
        raise InputError("INTENT_OUTCOME_INVALID", "save-all outcome is invalid")
    _validate_sha256(evidence_sha256, "save_all_result.evidence_sha256")
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before save-all result")
    _, album = _task_album(current, task_id, album_key)
    intent = album["save_all_intent"]
    if not isinstance(intent, dict) or intent["action_id"] != action_id or intent["session_id"] != session_id:
        raise SafetyBlock("SAVE_ALL_ACTION_MISMATCH", "save-all action is not owned by this session")
    if intent["result"] is not None:
        raise SafetyBlock("SAVE_ALL_RESULT_ALREADY_RECORDED", "save-all result was already recorded")
    recorded = {"at_utc": utc_now(), "outcome": outcome, "evidence_sha256": evidence_sha256}

    def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
        store["tasks"][task_id]["albums"][album_key]["save_all_intent"]["result"] = copy.deepcopy(recorded)
        _set_session_pending_in_store(store, session_id, False)
        return {"album_key": album_key, "action_id": action_id, "outcome": outcome}

    updated, result = _mutate_store(
        root,
        expected_generation,
        mutate,
        [
            _event(
                "RECORD_SAVE_ALL_RESULT",
                session_id=session_id,
                task_id=task_id,
                album_key=album_key,
                from_state="UNKNOWN",
                to_state="UNKNOWN" if outcome != "RETURNED" else "CHOOSER_PENDING",
                evidence_reference=evidence_sha256,
            )
        ],
    )
    return {**result, "generation": updated["generation"], "checkpoint_sha256": updated["payload_sha256"]}


def prepare_chooser_confirm(
    root: Path,
    task_id: str,
    session_id: str,
    expected_generation: int,
    album_key: str,
    grounding: Mapping[str, Any],
) -> Dict[str, Any]:
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before chooser preparation")
    task, album = _task_album(current, task_id, album_key)
    save_intent = album["save_all_intent"]
    if not _intent_returned(save_intent):
        raise SafetyBlock("SAVE_ALL_NOT_RETURNED", "chooser cannot be prepared before a returned save-all action")
    if album["chooser_confirm_intent"] is not None:
        raise SafetyBlock("CHOOSER_INTENT_EXISTS", "chooser confirmation was already prepared")
    if album["verification"] is not None:
        raise SafetyBlock("ALBUM_NOT_DISPATCHABLE", "album is already verified")
    try:
        _validate_chooser_grounding(grounding, scope=task["scope"], album=album)
    except SafetyBlock as exc:
        raise InputError("CHOOSER_GROUNDING_INVALID", exc.message) from exc
    derived = derive_task_state(root, current, task_id, deep=True)
    blocker = derived["first_blocker"]
    if blocker is not None and not (
        blocker["album_key"] == album_key and blocker["reason"] in ("CHOOSER_OUTCOME_UNKNOWN", "SAVE_ALL_OUTCOME_UNKNOWN")
    ):
        raise SafetyBlock("TASK_BLOCKED", "an unresolved task blocker prevents chooser input")
    if save_intent["session_id"] != session_id:
        raise SafetyBlock("CHOOSER_SESSION_MISMATCH", "a new session cannot continue an old chooser operation")
    destination = _task_absolute_path(root, task_id, album["destination"])
    if not _destination_is_empty(destination):
        raise SafetyBlock("CHOOSER_DESTINATION_NOT_EMPTY", "chooser destination is not empty before confirmation")
    action_id = str(uuid.uuid4())
    intent = {
        "action_id": action_id,
        "prepared_at_utc": utc_now(),
        "session_id": session_id,
        "album_key": album_key,
        "scope_sha256": _scope_digest(task["scope"]),
        "destination": album["destination"],
        "save_all_action_id": save_intent["action_id"],
        "grounding": copy.deepcopy(dict(grounding)),
        "result": None,
    }

    def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
        store["tasks"][task_id]["albums"][album_key]["chooser_confirm_intent"] = copy.deepcopy(intent)
        _set_session_pending_in_store(store, session_id, True)
        return {"album_key": album_key, "prepare": "CHOOSER_CONFIRM", "destination": album["destination"]}

    updated, result = _mutate_store(
        root,
        expected_generation,
        mutate,
        [
            _event(
                "PREPARE_CHOOSER_CONFIRM",
                session_id=session_id,
                task_id=task_id,
                album_key=album_key,
                from_state="CHOOSER_PENDING",
                to_state="UNKNOWN",
                evidence_reference=action_id,
            )
        ],
    )
    return _intent_ack(result, action_id, updated["generation"], updated["payload_sha256"])


def record_chooser_result(
    root: Path,
    task_id: str,
    session_id: str,
    expected_generation: int,
    album_key: str,
    action_id: str,
    outcome: str,
    evidence_sha256: str,
) -> Dict[str, Any]:
    if outcome not in INTENT_OUTCOMES:
        raise InputError("INTENT_OUTCOME_INVALID", "chooser outcome is invalid")
    _validate_sha256(evidence_sha256, "chooser_result.evidence_sha256")
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before chooser result")
    _, album = _task_album(current, task_id, album_key)
    intent = album["chooser_confirm_intent"]
    if not isinstance(intent, dict) or intent["action_id"] != action_id or intent["session_id"] != session_id:
        raise SafetyBlock("CHOOSER_ACTION_MISMATCH", "chooser action is not owned by this session")
    if intent["result"] is not None:
        raise SafetyBlock("CHOOSER_RESULT_ALREADY_RECORDED", "chooser result was already recorded")
    recorded = {"at_utc": utc_now(), "outcome": outcome, "evidence_sha256": evidence_sha256}

    def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
        store["tasks"][task_id]["albums"][album_key]["chooser_confirm_intent"]["result"] = copy.deepcopy(recorded)
        _set_session_pending_in_store(store, session_id, False)
        return {"album_key": album_key, "action_id": action_id, "outcome": outcome}

    updated, result = _mutate_store(
        root,
        expected_generation,
        mutate,
        [
            _event(
                "RECORD_CHOOSER_RESULT",
                session_id=session_id,
                task_id=task_id,
                album_key=album_key,
                from_state="UNKNOWN",
                to_state="VERIFYING" if outcome == "RETURNED" else "UNKNOWN",
                evidence_reference=evidence_sha256,
            )
        ],
    )
    return {**result, "generation": updated["generation"], "checkpoint_sha256": updated["payload_sha256"]}


def verify_album(
    root: Path,
    task_id: str,
    session_id: str,
    expected_generation: int,
    album_key: str,
    *,
    interval_seconds: float = 3.0,
    timeout_seconds: float = 600.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    current = read_store(root)
    if current["generation"] != expected_generation:
        raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before verification")
    task, album = _task_album(current, task_id, album_key)
    if _album_history_skip(current, task, album, root=root, deep=False) is not None:
        raise SafetyBlock("ALBUM_NOT_VERIFIABLE", "historical albums are never reverified as new downloads")
    if album["verification"] is not None:
        _verification_matches_current(
            _task_absolute_path(root, task_id, album["destination"]),
            album["verification"],
        )
        return {
            "album_key": album_key,
            "state": "VERIFIED",
            "generation": current["generation"],
            "checkpoint_sha256": current["payload_sha256"],
            "already_verified": True,
        }
    save_intent = album["save_all_intent"]
    chooser_intent = album["chooser_confirm_intent"]
    if not _intent_returned(save_intent) or not _intent_returned(chooser_intent):
        raise SafetyBlock("DISPATCH_EVIDENCE_INCOMPLETE", "save-all and chooser returned evidence are required")
    derived = derive_task_state(root, current, task_id, deep=True)
    if derived["first_blocker"] is not None:
        raise SafetyBlock("TASK_BLOCKED", "an unresolved blocker prevents verification promotion")
    if derived["task_phase"] != "READY_TO_VERIFY" or derived["next_safe_action"] != "VERIFY_ALBUM:%s" % album_key:
        raise SafetyBlock("ALBUM_NOT_NEXT_VERIFIABLE", "album is not the next safe verification item")
    destination = _task_absolute_path(root, task_id, album["destination"])
    expected = int(album["identity"]["expected_images"])
    stable = _sample_stable_inventory(
        destination,
        required_samples=3,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        require_nonempty=True,
        sleep_fn=sleep_fn,
    )
    if stable["count"] != expected:
        if stable["count"] < expected:
            raise SafetyBlock("INCOMPLETE_DOWNLOAD", "verified album inventory is incomplete")
        raise SafetyBlock("UNEXPECTED_EXTRA_FILES", "verified album inventory contains extra files")
    decoded, decoder_binary_sha256 = _decode_inventory(destination, expected)
    decoded_entries = _apply_decode_result(stable, decoded)
    post_decode = _inventory_directory(destination, max_entries=max(MAX_EXPECTED_IMAGES, expected + 1))
    if (
        post_decode["sha256"] != stable["sha256"]
        or _content_entry_binding(post_decode["entries"]) != _content_entry_binding(stable["entries"])
    ):
        raise SafetyBlock("DESTINATION_CHANGED", "destination changed during post-decode inventory")
    _flush_inventory(destination, stable)
    post_flush = _inventory_directory(destination, max_entries=max(MAX_EXPECTED_IMAGES, expected + 1))
    if (
        post_flush["sha256"] != stable["sha256"]
        or _content_entry_binding(post_flush["entries"]) != _content_entry_binding(stable["entries"])
    ):
        raise SafetyBlock("DESTINATION_CHANGED", "destination changed during post-flush readback")
    verification = {
        "verified_at_utc": utc_now(),
        "expected_images": expected,
        "actual_entries": len(decoded_entries),
        "inventory_sha256": _inventory_digest(decoded_entries),
        "inventory": decoded_entries,
        "decoder_source_sha256": IMAGE_DECODER_SOURCE_SHA256,
        "decoder_binary_sha256": decoder_binary_sha256,
        "pre_inventory_sha256": stable["sha256"],
        "post_inventory_sha256": post_flush["sha256"],
        "stability_samples": int(stable["stability_samples"]),
        "save_all_action_id": save_intent["action_id"],
        "chooser_action_id": chooser_intent["action_id"],
    }
    _validate_verification(verification)

    def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
        store["tasks"][task_id]["albums"][album_key]["verification"] = copy.deepcopy(verification)
        _set_session_pending_in_store(store, session_id, False)
        return {
            "album_key": album_key,
            "state": "VERIFIED",
            "inventory_sha256": verification["inventory_sha256"],
            "photo_count": expected,
        }

    updated, result = _mutate_store(
        root,
        expected_generation,
        mutate,
        [
            _event(
                "VERIFY_ALBUM",
                session_id=session_id,
                task_id=task_id,
                album_key=album_key,
                from_state="VERIFYING",
                to_state="VERIFIED",
                evidence_reference=verification["inventory_sha256"],
            )
        ],
    )
    return {
        **result,
        "generation": updated["generation"],
        "checkpoint_sha256": updated["payload_sha256"],
        "already_verified": False,
    }


def _require_exact_keys(value: Mapping[str, Any], expected: Sequence[str], code: str) -> None:
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
    if value["version"] != 1:
        raise InputError("VERSION_UNSUPPORTED", "request version is unsupported")
    for key in ("request_id", "session_id", "task_id"):
        if not isinstance(value[key], str) or not value[key]:
            raise InputError("REQUEST_INVALID", "%s must be a non-empty string" % key)
    if not TASK_ID_RE.fullmatch(value["task_id"]):
        raise InputError("TASK_ID_INVALID", "task_id is invalid")
    generation = value["expected_generation"]
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise InputError("GENERATION_INVALID", "expected_generation must be a non-negative integer")
    if not isinstance(value["operation"], str) or not value["operation"]:
        raise InputError("OPERATION_INVALID", "operation must be a non-empty string")
    if not isinstance(value["data"], dict):
        raise InputError("DATA_INVALID", "data must be a JSON object")
    return value


def _response(request: Mapping[str, Any], result: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "version": 1,
        "request_id": request["request_id"],
        "session_id": request["session_id"],
        "operation": request["operation"],
        "ok": True,
        "result": dict(result),
    }


def _error_response(request_id: Any, session_id: Any, error: ResumeError) -> Dict[str, Any]:
    return {
        "version": 1,
        "request_id": request_id,
        "session_id": session_id,
        "ok": False,
        "error": {"code": error.code, "message": error.message},
    }


def _write_json_line(value: Mapping[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json(value) + b"\n")
    sys.stdout.buffer.flush()


class SessionServer:
    def __init__(
        self,
        task_id: str,
        root: Path = DEFAULT_ROOT,
        *,
        verification_interval_seconds: float = 3.0,
        verification_timeout_seconds: float = 600.0,
    ) -> None:
        if not TASK_ID_RE.fullmatch(task_id):
            raise InputError("TASK_ID_INVALID", "task_id is invalid")
        self.task_id = task_id
        self.root = Path(root)
        self.controller = current_process_identity()
        self.boot_id = boot_identity()
        self.session_id: Optional[str] = None
        self.generation: Optional[int] = None
        self.hello_seen = False
        self.stopped = False
        self.deep_reconciled = False
        self.writer = SessionRoot(self.root)
        self.seen_request_ids: set[str] = set()
        self.verification_interval_seconds = verification_interval_seconds
        self.verification_timeout_seconds = verification_timeout_seconds

    def run(self) -> int:
        try:
            initial = read_store(self.root)
        except InputError:
            return EXIT_INPUT
        self.writer.acquire()
        exit_code = EXIT_SAFETY_BLOCK
        clean_close = False
        try:
            self.generation = initial["generation"]
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
                    if request["request_id"] in self.seen_request_ids:
                        raise SafetyBlock("REQUEST_REPLAYED", "request_id was already consumed")
                    self.seen_request_ids.add(request["request_id"])
                    if request["task_id"] != self.task_id:
                        raise SafetyBlock("TASK_SCOPE_MISMATCH", "request task does not match the session task")
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
                    if request["expected_generation"] != self.generation:
                        raise SafetyBlock("GENERATION_STALE", "request generation does not match the checkpoint")
                    if request["operation"] == "close":
                        _require_exact_keys(request["data"], (), "CLOSE_DATA_INVALID")
                        result = self._close_session()
                        _write_json_line(_response(request, result))
                        clean_close = True
                        exit_code = EXIT_OK
                        break
                    result = self._dispatch(request)
                    _write_json_line(_response(request, result))
                except ResumeError as exc:
                    try:
                        _write_json_line(_error_response(request_id, session_id, exc))
                    except BrokenPipeError:
                        pass
                    exit_code = exc.exit_code
                    self.stopped = True
                    break
            else:
                exit_code = EXIT_SAFETY_BLOCK
                self.stopped = True
        finally:
            self.stopped = True
            if clean_close and self.writer.held:
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
        current = read_store(self.root)
        if request["expected_generation"] != current["generation"]:
            raise SafetyBlock("GENERATION_STALE", "hello generation does not match the checkpoint")
        if self.task_id not in current["tasks"]:
            raise SafetyBlock("TASK_NOT_FOUND", "session task does not exist in the checkpoint")
        sync = sync_probe(self.root)
        planned_generation = current["generation"] + 1
        owner = {
            "schema_version": OWNER_RECORD_SCHEMA_VERSION,
            "state": "ACTIVE",
            "session_id": request["session_id"],
            "task_id": self.task_id,
            "boot_id": self.boot_id,
            "controller": copy.deepcopy(self.controller),
            "host": observed_host,
            "pending_input": False,
            "started_at_utc": utc_now(),
            "updated_at_utc": utc_now(),
            "checkpoint_generation": planned_generation,
        }

        def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
            store["session_owner"] = copy.deepcopy(owner)
            return {"owner": owner}

        updated, result = _mutate_store(
            self.root,
            current["generation"],
            mutate,
            [
                _event(
                    "SESSION_OPENED",
                    session_id=request["session_id"],
                    task_id=self.task_id,
                    evidence_reference=sha256_bytes(canonical_json(owner)),
                )
            ],
        )
        self.generation = updated["generation"]
        lock_record = {
            **owner,
            "schema_version": OWNER_RECORD_SCHEMA_VERSION,
            "state": "ACTIVE",
            "checkpoint_generation": updated["generation"],
        }
        self.writer.activate(lock_record)
        return {
            "generation": updated["generation"],
            "checkpoint_sha256": updated["payload_sha256"],
            "root_sha256": sha256_bytes(str(self.root).encode("utf-8")),
            "controller": self.controller,
            "host": observed_host,
            "boot_id": self.boot_id,
            "session_id": request["session_id"],
            "writer_lock": "held",
            "record_state": "ACTIVE",
            "sync": sync,
            "gui_observations": 0,
            "gui_dispatches": 0,
        }

    def _dispatch(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        assert self.session_id is not None and self.generation is not None
        operation = request["operation"]
        data = request["data"]
        if operation == "reconcile":
            _require_exact_keys(data, (), "RECONCILE_DATA_INVALID")
            result = reconcile_task(self.root, self.task_id)
            if result["generation"] != self.generation:
                raise SafetyBlock("GENERATION_UNSTABLE", "reconciliation observed a different generation")
            self.deep_reconciled = True
            return result
        if operation == "prepare_save_all":
            self._require_deep_reconcile()
            _require_exact_keys(data, ("album_key", "grounding"), "PREPARE_SAVE_ALL_DATA_INVALID")
            result = prepare_save_all(
                self.root,
                self.task_id,
                self.session_id,
                self.generation,
                data["album_key"],
                data["grounding"],
            )
            self.generation = result["generation"]
            self.writer.set_pending_input(True, self.generation)
            return result
        if operation == "record_save_all_result":
            _require_exact_keys(
                data,
                ("album_key", "action_id", "outcome", "evidence_sha256"),
                "RECORD_SAVE_ALL_DATA_INVALID",
            )
            result = record_save_all_result(
                self.root,
                self.task_id,
                self.session_id,
                self.generation,
                data["album_key"],
                data["action_id"],
                data["outcome"],
                data["evidence_sha256"],
            )
            self.generation = result["generation"]
            self.writer.set_pending_input(False, self.generation)
            return result
        if operation == "prepare_chooser_confirm":
            self._require_deep_reconcile()
            _require_exact_keys(data, ("album_key", "grounding"), "PREPARE_CHOOSER_DATA_INVALID")
            result = prepare_chooser_confirm(
                self.root,
                self.task_id,
                self.session_id,
                self.generation,
                data["album_key"],
                data["grounding"],
            )
            self.generation = result["generation"]
            self.writer.set_pending_input(True, self.generation)
            return result
        if operation == "record_chooser_result":
            _require_exact_keys(
                data,
                ("album_key", "action_id", "outcome", "evidence_sha256"),
                "RECORD_CHOOSER_DATA_INVALID",
            )
            result = record_chooser_result(
                self.root,
                self.task_id,
                self.session_id,
                self.generation,
                data["album_key"],
                data["action_id"],
                data["outcome"],
                data["evidence_sha256"],
            )
            self.generation = result["generation"]
            self.writer.set_pending_input(False, self.generation)
            return result
        if operation == "verify_album":
            self._require_deep_reconcile()
            _require_exact_keys(data, ("album_key",), "VERIFY_ALBUM_DATA_INVALID")
            result = verify_album(
                self.root,
                self.task_id,
                self.session_id,
                self.generation,
                data["album_key"],
                interval_seconds=self.verification_interval_seconds,
                timeout_seconds=self.verification_timeout_seconds,
            )
            if result["generation"] != self.generation:
                self.generation = result["generation"]
            return result
        raise SafetyBlock("OPERATION_NOT_AVAILABLE", "operation is not available in the session")

    def _require_deep_reconcile(self) -> None:
        if not self.deep_reconciled:
            raise SafetyBlock("DEEP_RECONCILE_REQUIRED", "a successful deep reconciliation is required first")

    def _close_session(self) -> Dict[str, Any]:
        current = read_store(self.root)
        assert self.session_id is not None and self.generation is not None
        if current["generation"] != self.generation:
            raise SafetyBlock("GENERATION_STALE", "checkpoint generation changed before close")
        owner = current.get("session_owner")
        if not isinstance(owner, dict) or owner.get("session_id") != self.session_id or owner.get("state") != "ACTIVE":
            raise SafetyBlock("SESSION_OWNER_MISMATCH", "active session owner record is missing")
        closed_owner = copy.deepcopy(owner)
        closed_owner["state"] = "CLOSED"
        closed_owner["pending_input"] = False
        closed_owner["updated_at_utc"] = utc_now()
        closed_owner["checkpoint_generation"] = current["generation"] + 1

        def mutate(store: Dict[str, Any]) -> Dict[str, Any]:
            store["session_owner"] = copy.deepcopy(closed_owner)
            return {"closed": True}

        updated, _ = _mutate_store(
            self.root,
            self.generation,
            mutate,
            [
                _event(
                    "SESSION_CLOSED",
                    session_id=self.session_id,
                    task_id=self.task_id,
                    evidence_reference=sha256_bytes(canonical_json(closed_owner)),
                )
            ],
        )
        self.generation = updated["generation"]
        self.writer.set_pending_input(False, self.generation)
        return {
            "closed": True,
            "generation": updated["generation"],
            "checkpoint_sha256": updated["payload_sha256"],
        }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LINE agent-resume durable controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_root(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=argparse.SUPPRESS)

    init_parser = subparsers.add_parser("init")
    add_root(init_parser)

    history_parser = subparsers.add_parser("import-history")
    add_root(history_parser)
    history_parser.add_argument("--official-state", type=Path, required=True)
    history_parser.add_argument("--manual-archives", type=Path, required=True)
    history_parser.add_argument("--pr28-checkpoints", type=Path, required=True)
    history_parser.add_argument("--exclusion-gate", type=Path, required=True)
    history_parser.add_argument("--project-root", type=Path, required=True)
    history_parser.add_argument("--pr28-root", type=Path, required=True)
    history_parser.add_argument("--group-key", required=True)

    create_parser = subparsers.add_parser("create-task")
    add_root(create_parser)
    create_parser.add_argument("--manifest", type=Path, required=True)

    inspect_parser = subparsers.add_parser("inspect")
    add_root(inspect_parser)
    inspect_parser.add_argument("--task", required=True)

    reconcile_parser = subparsers.add_parser("reconcile")
    add_root(reconcile_parser)
    reconcile_parser.add_argument("--task", required=True)

    session_parser = subparsers.add_parser("session")
    add_root(session_parser)
    session_parser.add_argument("--task", required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _parse_args(argv)
        if args.command == "init":
            result = init_store(args.root)
            _write_json_line({"ok": True, **result})
            return EXIT_OK
        if args.command == "import-history":
            result = import_history(
                args.root,
                args.official_state,
                args.manual_archives,
                args.pr28_checkpoints,
                args.exclusion_gate,
                args.project_root,
                args.pr28_root,
                args.group_key,
            )
            _write_json_line({"ok": True, **result})
            return EXIT_OK
        if args.command == "create-task":
            result = create_task(args.root, args.manifest)
            _write_json_line({"ok": True, **result})
            return EXIT_OK
        if args.command == "inspect":
            result = inspect_task(args.root, args.task)
            _write_json_line({"ok": True, **result})
            return EXIT_OK
        if args.command == "reconcile":
            result = reconcile_task(args.root, args.task)
            _write_json_line({"ok": True, **result})
            return EXIT_OK
        if args.command == "session":
            return SessionServer(task_id=args.task, root=args.root).run()
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
