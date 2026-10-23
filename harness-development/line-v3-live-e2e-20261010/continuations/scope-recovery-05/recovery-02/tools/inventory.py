#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Recovery-02 complete filesystem inventory (baseline|preservation).

Fixed ROOT/RUNROOT. Writes exactly one exclusive JSON output per invocation:
  RUNROOT/evidence/inventory-<mode>-<slot>.json

Safety properties (frozen in recovery-02 plan.md):
- full recursion, hidden/ignored/untracked/empty dirs/nested repos included
- only ROOT/.git contents are excluded
- symlinks are recorded, never followed
- the single allowlisted FIFO is lstat-only; it is never opened
- any other special object is recorded metadata-only and blocks policy
- regular files: fd-relative non-blocking open, fstat identity check before
  read, before/after metadata + byte count consistency check
- a scan that is incomplete (IO error, drift, timeout, duplicate) keeps its
  partial records and is never usable as a baseline
- total deadline 1200 s: on timeout keep the partial inventory and stop

This module is also imported by checks/test_inventory.py for fixture tests
(scan_tree supports explicit roots/allowlists for tests only; the CLI does not).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import stat
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
RUNROOT = ROOT / RUNREL
EVIDENCE = RUNROOT / "evidence"
TMPDIR = RUNROOT / "tmp"
TOOL_PATH = RUNROOT / "tools" / "inventory.py"

FORMAT = "RECOVERY_02_INVENTORY_V1"
TASK_ID = "TASK-20261011-line-baseline-recovery-02"
FIFO_REL = (
    "evidence/20260916-auto-verification/attempt-01/archive-phase1/"
    "private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo"
)
FIFO_ABS = ROOT / FIFO_REL
DEADLINE_SECONDS = 1200.0
CHUNK_BYTES = 1024 * 1024
MODES = ("baseline", "preservation")
SLOTS = ("01", "02")

_O_RDONLY = getattr(os, "O_RDONLY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_O_WRONLY = os.O_WRONLY
_O_CREAT = os.O_CREAT
_O_EXCL = os.O_EXCL


class ScanStop(Exception):
    """Raised internally to unwind the walk after a timeout."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> tuple[int, str]:
    h = hashlib.sha256()
    count = 0
    fd = _open(str(path), _O_RDONLY | _O_NOFOLLOW | _O_NONBLOCK | _O_CLOEXEC)
    try:
        while True:
            chunk = os.read(fd, CHUNK_BYTES)
            if not chunk:
                break
            count += len(chunk)
            h.update(chunk)
    finally:
        os.close(fd)
    return count, h.hexdigest()


# --------------------------------------------------------------------------
# seam functions (fixture tests monkeypatch these)
# --------------------------------------------------------------------------

def _lstat(name, dir_fd=None):
    return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)


def _open(name, flags, dir_fd=None, mode=0o777):
    if dir_fd is None:
        return os.open(name, flags, mode)
    return os.open(name, flags, mode, dir_fd=dir_fd)


def _fstat(fd):
    return os.fstat(fd)


def _listdir(fd):
    return os.listdir(fd)


def _readlink(name, dir_fd=None):
    if dir_fd is None:
        return os.readlink(name)
    return os.readlink(name, dir_fd=dir_fd)


def _read_fd_bytes(fd):
    """Read all bytes from an fd; returns (count, sha256hex)."""
    h = hashlib.sha256()
    count = 0
    while True:
        chunk = os.read(fd, CHUNK_BYTES)
        if not chunk:
            break
        count += len(chunk)
        h.update(chunk)
    return count, h.hexdigest()


def _monotonic():
    return time.monotonic()


def _sig(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def _identity(st):
    return (st.st_dev, st.st_ino)


def _mode_of(st):
    return stat.S_IMODE(st.st_mode)


def _type_char(st):
    return stat.filemode(st.st_mode)[0]


def _base_record(rel: str, st) -> dict:
    return {
        "path": rel,
        "mode": _mode_of(st),
        "dev": st.st_dev,
        "ino": st.st_ino,
        "nlink": st.st_nlink,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "ctime_ns": st.st_ctime_ns,
    }


def _norm_rel(rel: str) -> str:
    if not rel or rel.startswith("/") or rel.endswith("/"):
        raise ValueError(f"INVALID_REL_PATH:{rel!r}")
    parts = rel.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise ValueError(f"INVALID_REL_COMPONENT:{rel!r}")
    return "/".join(parts)


def _sane_name(name: str) -> bool:
    return bool(name) and name not in (".", "..") and "/" not in name and "\x00" not in name


def _dir_entries_sha(entries: list[str]) -> str:
    encoded = json.dumps(entries, ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------

class ScanState:
    def __init__(self, deadline_seconds: float, progress_cb=None):
        self.deadline_seconds = deadline_seconds
        self.start = _monotonic()
        self.timeout = False
        self.records: list[dict] = []
        self.errors: list[dict] = []
        self.policy_violations: list[dict] = []
        self.seen: set[str] = set()
        self.dirs_seen = 0
        self.fifo_observation = None
        self.fifo_found = False
        self.progress_cb = progress_cb
        self._last_progress = self.start

    def error(self, code: str, rel: str, detail: str = "") -> None:
        self.errors.append({"code": code, "path": rel, "detail": detail})

    def violation(self, code: str, rel: str, detail: str = "") -> None:
        self.policy_violations.append({"code": code, "path": rel, "detail": detail})

    def add(self, record: dict) -> None:
        rel = record["path"]
        if rel in self.seen:
            self.error("DUPLICATE_PATH", rel)
            return
        self.seen.add(rel)
        self.records.append(record)

    def check_deadline(self) -> None:
        now = _monotonic()
        if now - self.start > self.deadline_seconds:
            self.timeout = True
            raise ScanStop()
        if self.progress_cb and now - self._last_progress >= 30.0:
            self._last_progress = now
            self.progress_cb(self)

    def summary_progress(self) -> None:
        if self.progress_cb:
            self.progress_cb(self)

    @property
    def complete(self) -> bool:
        return not self.errors and not self.timeout

    @property
    def policy(self) -> dict:
        return {
            "ok": (not self.policy_violations) and self.fifo_found and self.fifo_observation is not None,
            "violations": list(self.policy_violations),
            "fifo_found": self.fifo_found,
            "fifo_observation": self.fifo_observation,
        }


def _finish_dir_record(state: ScanState, rel: str, st_before, st_after, entries: list[str]) -> None:
    if _sig(st_before) != _sig(st_after):
        state.error("DIRECTORY_CHANGED_DURING_SCAN", rel, "lstat signature changed while listing")
        return
    record = _base_record(rel, st_before)
    record.update({"kind": "DIRECTORY", "entries": entries, "sha256": _dir_entries_sha(entries)})
    state.add(record)


def _record_regular(state: ScanState, parent_fd: int, name: str, rel: str, st_before) -> None:
    flags = _O_RDONLY | _O_NOFOLLOW | _O_NONBLOCK | _O_CLOEXEC
    try:
        fd = _open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        state.error("UNREADABLE_PATH", rel, f"open failed: {exc.__class__.__name__}:{exc}")
        return
    try:
        st_open = _fstat(fd)
        if not stat.S_ISREG(st_open.st_mode):
            state.error("SPECIAL_RACE_DETECTED", rel, f"opened object is not regular: {stat.filemode(st_open.st_mode)}")
            state.violation("UNEXPECTED_SPECIAL_OBJECT", rel, "regular->special race; no content read")
            rec = _base_record(rel, st_open)
            rec.update({"kind": "OTHER_SPECIAL", "type_char": _type_char(st_open), "content_read": False})
            state.add(rec)
            return
        if _identity(st_open) != _identity(st_before):
            state.error("FILE_CHANGED_BEFORE_READ", rel, "fstat identity differs from lstat")
            return
        count, digest = _read_fd_bytes(fd)
        st_after = _fstat(fd)
    finally:
        os.close(fd)
    if _sig(st_before) != _sig(st_after) or count != st_before.st_size:
        state.error(
            "FILE_CHANGED_DURING_READ",
            rel,
            f"before/after signature differ or bytes={count} size={st_before.st_size}",
        )
        return
    record = _base_record(rel, st_before)
    record.update({"kind": "REGULAR", "bytes": count, "sha256": digest, "read_verified": True})
    state.add(record)


def _record_symlink(state: ScanState, parent_fd: int, name: str, rel: str, st_before) -> None:
    try:
        target = _readlink(name, dir_fd=parent_fd)
    except OSError as exc:
        state.error("UNREADABLE_PATH", rel, f"readlink failed: {exc.__class__.__name__}:{exc}")
        return
    try:
        st_after = _lstat(name, dir_fd=parent_fd)
    except OSError as exc:
        state.error("UNREADABLE_PATH", rel, f"re-lstat failed: {exc.__class__.__name__}:{exc}")
        return
    if _sig(st_before) != _sig(st_after):
        state.error("SYMLINK_CHANGED_DURING_SCAN", rel, "lstat signature changed while reading target")
        return
    record = _base_record(rel, st_before)
    record.update({"kind": "SYMLINK", "target": target, "sha256": sha256_bytes(os.fsencode(target))})
    state.add(record)


def _record_fifo(state: ScanState, rel: str, st) -> None:
    state.fifo_found = True
    if not stat.S_ISFIFO(st.st_mode):
        state.error("FIFO_TYPE_CHANGED", rel, f"allowlisted FIFO path is now {stat.filemode(st.st_mode)}")
        state.violation("FIFO_TYPE_CHANGED", rel, "known FIFO path changed type; never opened")
        record = _base_record(rel, st)
        record.update({"kind": "OTHER_SPECIAL", "type_char": _type_char(st), "content_read": False})
        state.add(record)
        return
    record = _base_record(rel, st)
    record.update({"kind": "FIFO", "content_read": False, "content_hash": None})
    state.add(record)
    state.fifo_observation = {k: record[k] for k in ("path", "mode", "dev", "ino", "nlink", "size", "mtime_ns", "ctime_ns")}


def _record_other_special(state: ScanState, rel: str, st) -> None:
    state.error("UNEXPECTED_SPECIAL_OBJECT", rel, f"type={stat.filemode(st.st_mode)}; metadata only, not opened")
    state.violation("UNEXPECTED_SPECIAL_OBJECT", rel, f"type={stat.filemode(st.st_mode)}")
    record = _base_record(rel, st)
    record.update({"kind": "OTHER_SPECIAL", "type_char": _type_char(st), "content_read": False})
    state.add(record)


def _scan_dir_fd(state: ScanState, fd: int, rel_prefix: str, root_abs: pathlib.Path, fifo_abs: pathlib.Path, exclude_top_git: bool, allowlist_fifo: bool) -> None:
    try:
        names = _listdir(fd)
    except OSError as exc:
        state.error("UNREADABLE_PATH", rel_prefix or ".", f"listdir failed: {exc.__class__.__name__}:{exc}")
        return
    for name in sorted(names):
        if not _sane_name(name):
            state.error("INVALID_NAME", f"{rel_prefix}/{name}", "unsanitary directory entry name")
            continue
        rel = f"{rel_prefix}/{name}" if rel_prefix else name
        _norm_rel(rel)
        state.check_deadline()
        try:
            st = _lstat(name, dir_fd=fd)
        except OSError as exc:
            state.error("UNREADABLE_PATH", rel, f"lstat failed: {exc.__class__.__name__}:{exc}")
            continue
        if allowlist_fifo and _is_allowlisted_fifo(rel, root_abs, fifo_abs):
            _record_fifo(state, rel, st)
            continue
        if stat.S_ISDIR(st.st_mode):
            if exclude_top_git and rel_prefix == "" and name == ".git":
                continue
            state.dirs_seen += 1
            try:
                child_fd = _open(name, _O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW | _O_CLOEXEC, dir_fd=fd)
            except OSError as exc:
                state.error("UNREADABLE_PATH", rel, f"directory open failed: {exc.__class__.__name__}:{exc}")
                continue
            try:
                st_open = _fstat(child_fd)
                if not stat.S_ISDIR(st_open.st_mode) or _identity(st_open) != _identity(st):
                    state.error("DIRECTORY_CHANGED_DURING_SCAN", rel, "fstat identity differs from lstat")
                    continue
                try:
                    entries = sorted(_listdir(child_fd))
                except OSError as exc:
                    state.error("UNREADABLE_PATH", rel, f"listdir failed: {exc.__class__.__name__}:{exc}")
                    continue
                try:
                    st_after = _lstat(name, dir_fd=fd)
                except OSError as exc:
                    state.error("UNREADABLE_PATH", rel, f"re-lstat failed: {exc.__class__.__name__}:{exc}")
                    continue
                _finish_dir_record(state, rel, st, st_after, entries)
                _scan_dir_fd(state, child_fd, rel, root_abs, fifo_abs, exclude_top_git, allowlist_fifo)
            finally:
                os.close(child_fd)
            continue
        if stat.S_ISLNK(st.st_mode):
            _record_symlink(state, fd, name, rel, st)
            continue
        if stat.S_ISREG(st.st_mode):
            _record_regular(state, fd, name, rel, st)
            continue
        _record_other_special(state, rel, st)


def _is_allowlisted_fifo(rel: str, root_abs: pathlib.Path, fifo_abs: pathlib.Path) -> bool:
    return os.path.abspath(os.path.join(str(root_abs), rel)) == str(fifo_abs)


def scan_tree(root_abs: pathlib.Path, *, fifo_abs: pathlib.Path, allowlist_fifo: bool, exclude_top_git: bool = True, deadline_seconds: float = DEADLINE_SECONDS, progress_cb=None) -> ScanState:
    """Scan root_abs (tests use fixture roots); production CLI passes ROOT + allowlist."""
    state = ScanState(deadline_seconds=deadline_seconds, progress_cb=progress_cb)
    root_fd = None
    try:
        st_root = _lstat(str(root_abs))
        if not stat.S_ISDIR(st_root.st_mode) or stat.S_ISLNK(st_root.st_mode):
            state.error("ROOT_NOT_DIRECTORY", ".", f"root lstat mode={stat.filemode(st_root.st_mode)}")
            return state
        root_fd = _open(str(root_abs), _O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW | _O_CLOEXEC)
        st_open = _fstat(root_fd)
        if not stat.S_ISDIR(st_open.st_mode) or _identity(st_open) != _identity(st_root):
            state.error("ROOT_CHANGED_DURING_SCAN", ".", "root fstat identity differs from lstat")
            return state
        try:
            _scan_dir_fd(state, root_fd, "", root_abs, fifo_abs, exclude_top_git, allowlist_fifo)
        except ScanStop:
            state.error("INVENTORY_TIMEOUT", ".", f"deadline {deadline_seconds}s exceeded; partial kept, stop, no rerun")
    finally:
        if root_fd is not None:
            os.close(root_fd)
    if allowlist_fifo and not state.fifo_found:
        state.violation("FIFO_NOT_FOUND", FIFO_REL, "allowlisted FIFO did not appear in the scan")
    state.records.sort(key=lambda item: item["path"])
    state.summary_progress()
    return state


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def _write_exclusive(path: pathlib.Path, data: bytes) -> dict:
    dir_fd = _open(str(path.parent), _O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW | _O_CLOEXEC)
    try:
        fd = _open(path.name, _O_WRONLY | _O_CREAT | _O_EXCL | _O_NOFOLLOW | _O_CLOEXEC, dir_fd=dir_fd, mode=0o600)
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        rb_fd = _open(path.name, _O_RDONLY | _O_NOFOLLOW | _O_CLOEXEC, dir_fd=dir_fd)
        try:
            chunks = []
            while True:
                chunk = os.read(rb_fd, CHUNK_BYTES)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(rb_fd)
        readback = b"".join(chunks)
    finally:
        os.close(dir_fd)
    if readback != data:
        raise RuntimeError(f"WRITE_READBACK_MISMATCH:{path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "absolute_path": str(path),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def _ref(path: pathlib.Path) -> dict:
    size, digest = sha256_file(path)
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": size, "sha256": digest}


def _validate_location() -> list[str]:
    errors = []
    if pathlib.Path.cwd() != ROOT:
        errors.append(f"WRONG_CWD:{pathlib.Path.cwd()}")
    try:
        script_real = pathlib.Path(os.path.realpath(sys.argv[0]))
        if script_real != TOOL_PATH:
            errors.append(f"WRONG_SCRIPT:{script_real}")
    except OSError as exc:
        errors.append(f"SCRIPT_UNRESOLVABLE:{exc}")
    try:
        if pathlib.Path(os.path.realpath(ROOT)) != ROOT:
            errors.append("ROOT_RESOLUTION_MISMATCH")
    except OSError as exc:
        errors.append(f"ROOT_UNRESOLVABLE:{exc}")
    for path in (ROOT, RUNROOT, EVIDENCE, TMPDIR):
        current = pathlib.Path(path.anchor)
        for part in path.parts[1:]:
            current = current / part
            try:
                info = current.lstat()
            except OSError as exc:
                errors.append(f"PATH_UNREADABLE:{current}:{exc}")
                break
            if stat.S_ISLNK(info.st_mode):
                errors.append(f"SYMLINK_ANCESTOR:{current}")
    if not EVIDENCE.is_dir():
        errors.append(f"EVIDENCE_MISSING:{EVIDENCE}")
    if not TMPDIR.is_dir():
        errors.append(f"TMPDIR_MISSING:{TMPDIR}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in MODES or argv[2] not in SLOTS:
        print(json.dumps({"status": "REFUSED", "errors": ["usage: inventory.py baseline|preservation 01|02"]}))
        return 2
    mode, slot = argv[1], argv[2]
    guard_errors = _validate_location()
    if guard_errors:
        print(json.dumps({"status": "REFUSED", "errors": guard_errors}, ensure_ascii=False))
        return 2
    out_path = EVIDENCE / f"inventory-{mode}-{slot}.json"
    if os.path.lexists(out_path):
        print(json.dumps({"status": "REFUSED", "errors": [f"ID_COLLISION:{out_path}"]}, ensure_ascii=False))
        return 2
    started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    started_mono = _monotonic()

    def progress(state: ScanState) -> None:
        print(
            json.dumps(
                {
                    "progress": {
                        "records": len(state.records),
                        "dirs": state.dirs_seen,
                        "elapsed_s": round(_monotonic() - state.start, 3),
                    }
                }
            ),
            flush=True,
        )

    state = scan_tree(
        ROOT,
        fifo_abs=FIFO_ABS,
        allowlist_fifo=True,
        deadline_seconds=DEADLINE_SECONDS,
        progress_cb=progress,
    )
    ended_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    elapsed_ms = int((_monotonic() - started_mono) * 1000)
    self_bytes, self_sha = sha256_file(TOOL_PATH)
    counts: dict[str, int] = {}
    for record in state.records:
        counts[record["kind"]] = counts.get(record["kind"], 0) + 1
    complete = not state.errors and not state.timeout
    policy_ok = not state.policy_violations and state.fifo_found and state.fifo_observation is not None
    doc = {
        "format": FORMAT,
        "task_id": TASK_ID,
        "run_rel": RUNREL,
        "mode": mode,
        "slot": slot,
        "root": str(ROOT),
        "runroot": str(RUNROOT),
        "tool": {"path": TOOL_PATH.relative_to(ROOT).as_posix(), "absolute_path": str(TOOL_PATH), "bytes": self_bytes, "sha256": self_sha},
        "started_at_utc": started_utc,
        "ended_at_utc": ended_utc,
        "elapsed_ms": elapsed_ms,
        "monotonic_start_ns": time.monotonic_ns(),
        "deadline_seconds": DEADLINE_SECONDS,
        "timeout": state.timeout,
        "complete": complete,
        "errors": state.errors,
        "policy": {
            "ok": policy_ok,
            "violations": state.policy_violations,
            "fifo_path": FIFO_REL,
            "fifo_found": state.fifo_found,
            "fifo_observation": state.fifo_observation,
            "unexpected_special_count": sum(1 for v in state.policy_violations if v["code"] == "UNEXPECTED_SPECIAL_OBJECT"),
        },
        "coverage": {
            "recursive": True,
            "hidden_ignored_untracked_included": True,
            "symlinks_followed": False,
            "root_git_contents_excluded": True,
            "excluded_paths": [".git"],
            "fifo_allowlist": [FIFO_REL],
            "records_are_partial_on_incomplete": True,
        },
        "counts": {"total": len(state.records), **counts},
        "records": state.records,
    }
    data = (json.dumps(doc, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    ref = _write_exclusive(out_path, data)
    summary = {
        "status": "COMPLETE" if complete else "PARTIAL",
        "mode": mode,
        "slot": slot,
        "timeout": state.timeout,
        "records": len(state.records),
        "counts": counts,
        "errors": len(state.errors),
        "policy_ok": policy_ok,
        "output": ref,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True), flush=True)
    return 0 if (complete and policy_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
