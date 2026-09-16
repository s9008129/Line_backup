from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator


class AcceptanceError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 1):
        super().__init__(message)
        self.code, self.message, self.exit_code = code, message, exit_code


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def atomic_write_json(path: Path, value: Any, *, fault: str | None = None) -> dict:
    data = json_bytes(value)
    if fault == "WRITE_BEFORE_REPLACE":
        raise AcceptanceError("WRITE_BEFORE_REPLACE", "injected storage fault before replacement", 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            dfd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
            durability = "file-and-directory-fsync"
        except OSError:
            durability = "file-fsync-and-atomic-replace"
        return {"bytes": len(data), "sha256": sha256_bytes(data), "durability": durability}
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptanceError("STATE_READ_ERROR", f"cannot read JSON {path}: {exc}", 1) from exc


@contextlib.contextmanager
def locked_state(state_path: Path) -> Iterator[None]:
    import fcntl
    lock = state_path.parent / ".line-backup-state.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def wait_barrier(pause_at: str | None, barrier_file: str | None) -> None:
    if not pause_at:
        return
    if not barrier_file:
        raise AcceptanceError("INVALID_INPUT", "--barrier-file is required with --pause-at", 2)
    ready = Path(barrier_file + ".ready")
    ready.parent.mkdir(parents=True, exist_ok=True)
    ready.touch()
    barrier = Path(barrier_file)
    while not barrier.exists():
        time.sleep(0.01)


def within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def exact_real_path(path: Path) -> bool:
    return os.path.realpath(path) == os.path.abspath(path)


def fingerprint(start: str, end: str, count: int) -> dict:
    return {"start_date": start, "end_date": end, "expected_images": count}


def find_run(state: dict, run_id: str) -> dict | None:
    for run in state.get("runs", []):
        if isinstance(run, dict) and run.get("run_id") == run_id:
            return run
    return None


def terminal(run: dict | None) -> bool:
    return bool(run and run.get("workflow_outcome") in {"VERIFIED", "SAFE_ABORT"})


def result_file(evidence_dir: Path, result: dict) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(evidence_dir / "result.json", result)


def emit(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
