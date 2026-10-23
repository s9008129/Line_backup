"""Anchored, exclusive publication for ML07 evidence.

The caller supplies policy authorization separately. This module only supplies
the filesystem primitive and never creates a missing ancestor implicitly.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import stat


READ_CHUNK = 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def normalized_relative(relative: str) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or relative.startswith("/"):
        raise ValueError("INVALID_RELATIVE_PATH")
    parts = relative.split("/")
    if any(p in ("", ".", "..") or "\x00" in p for p in parts):
        raise ValueError("INVALID_RELATIVE_COMPONENT")
    return tuple(parts)


def open_anchored_directory(path: pathlib.Path) -> int:
    """Open every absolute path component without following a symlink."""
    if not path.is_absolute():
        raise ValueError("ROOT_NOT_ABSOLUTE")
    fd = os.open("/", DIR_FLAGS)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise RuntimeError("ROOT_NOT_DIRECTORY")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_parent(root: pathlib.Path, parts: tuple[str, ...]) -> int:
    fd = open_anchored_directory(root)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _write_all(fd: int, data: bytes) -> None:
    remaining = memoryview(data)
    while remaining:
        try:
            n = os.write(fd, remaining)
        except InterruptedError:
            continue
        if n <= 0:
            raise OSError("SHORT_WRITE")
        remaining = remaining[n:]


def _read_all(fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        try:
            chunk = os.read(fd, READ_CHUNK)
        except InterruptedError:
            continue
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > limit:
            raise RuntimeError("READBACK_CAP_EXCEEDED")
        chunks.append(chunk)


def mkdir_exclusive(root: pathlib.Path, relative: str, *, mode: int = 0o700) -> dict:
    """Create one directory through an anchored parent and fsync its entry."""
    parts = normalized_relative(relative)
    parent_fd = _open_parent(root, parts)
    try:
        os.mkdir(parts[-1], mode, dir_fd=parent_fd)
        os.fsync(parent_fd)
        child_fd = os.open(parts[-1], DIR_FLAGS, dir_fd=parent_fd)
        try:
            observed = os.fstat(child_fd)
            if not stat.S_ISDIR(observed.st_mode):
                raise RuntimeError("CREATED_ENTRY_NOT_DIRECTORY")
        finally:
            os.close(child_fd)
        return {"path": relative, "absolute_path": str(root.joinpath(*parts)), "dev": observed.st_dev,
                "ino": observed.st_ino, "mode": stat.S_IMODE(observed.st_mode), "uid": observed.st_uid,
                "gid": observed.st_gid, "created_at_ns": observed.st_ctime_ns, "identity_readback": True,
                "exclusive_create": True,
                "parent_fsync": True, "identity_readback": True}
    finally:
        os.close(parent_fd)


def publish_exclusive(root: pathlib.Path, relative: str, data: bytes, *, max_bytes: int) -> dict:
    """CREATE_ONCE with no-follow, file/dir fsync, same-dirfd readback.

    A failure leaves the newly created leaf in place. It is never unlinked or
    retried under the same identity; the caller must use a fresh epoch.
    """
    parts = normalized_relative(relative)
    if not isinstance(data, bytes) or len(data) > max_bytes:
        raise ValueError("INVALID_PAYLOAD_OR_CAP")
    parent_fd = _open_parent(root, parts)
    try:
        write_fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent_fd)
        try:
            _write_all(write_fd, data)
            os.fsync(write_fd)
            written = os.fstat(write_fd)
            if not stat.S_ISREG(written.st_mode) or written.st_size != len(data):
                raise RuntimeError("WRITTEN_FILE_IDENTITY_OR_SIZE")
        finally:
            os.close(write_fd)
        os.fsync(parent_fd)
        read_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            observed = os.fstat(read_fd)
            if not stat.S_ISREG(observed.st_mode):
                raise RuntimeError("READBACK_NOT_REGULAR")
            readback = _read_all(read_fd, max_bytes)
            after = os.fstat(read_fd)
        finally:
            os.close(read_fd)
        if (written.st_dev, written.st_ino) != (observed.st_dev, observed.st_ino) or (observed.st_dev, observed.st_ino) != (after.st_dev, after.st_ino):
            raise RuntimeError("READBACK_IDENTITY_CHANGED")
        if readback != data or len(readback) != after.st_size:
            raise RuntimeError("READBACK_BYTES_CHANGED")
        return {
            "path": relative,
            "absolute_path": str(root.joinpath(*parts)),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "dev": after.st_dev,
            "ino": after.st_ino,
            "created_at_ns": written.st_ctime_ns,
            "exclusive_create": True,
            "file_fsync": True,
            "parent_fsync": True,
            "readback_verified": True,
        }
    finally:
        os.close(parent_fd)
