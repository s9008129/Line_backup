#!/usr/bin/env python3
"""Shared harness for the automation-verification wave (H2.1 / Phase 2).

Every case records: full argv (secrets removed: none exist here), stdout,
stderr, exit code, subject program hashes, independent side-effect counters,
before/after state and a SHA-256+bytes manifest of the durable evidence tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
SRC = WORK / "src"
TASK_ID = "T20260916-0102-01-line-backup-acceptance"
DEFAULT_ATTEMPT = WORK / "evidence/20260916-auto-verification/attempt-02/order-driver-first"
ATTEMPT = Path(os.environ.get("LINE_BACKUP_ATTEMPT_ROOT", str(DEFAULT_ATTEMPT)))
PROGRAM_MODULES = ("transaction.py", "verifier.py", "status.py", "authority.py", "cli.py", "common.py")
MARKER_NAME = ".driver-ownership.json"


class RootOwnershipError(RuntimeError):
    """A literal root exists without this driver's ownership marker; refusing to touch it."""


KEEP_ON_RESET = (MARKER_NAME, "process-records", "driver-records")


def ensure_owned_root(root: Path, driver_id: str) -> dict:
    """Rev15 §15.5: every driver creates only its own literal roots and writes an ownership
    marker before any fixture content; a root that lacks a marker is never removed or
    overwritten (hard refusal, TASK_REGRESSION).

    The product's test-mode authority pins the transaction roots to the literal case-root
    namespace `-01`…`-25`, so several drivers of this wave legitimately share those roots.
    A root that already carries a task-managed marker of this TASK_ID is therefore adopted
    (the marker names the creating driver and is preserved); only `--clean-owned` removes a
    root, and only when the marker names the removing driver."""
    root = Path(root)
    marker = root / MARKER_NAME
    if root.exists():
        if not marker.is_file():
            raise RootOwnershipError(
                f"{root} exists without an ownership marker; refusing to overwrite foreign content")
        try:
            owned = json.loads(marker.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RootOwnershipError(f"{root} marker is unreadable: {exc}") from exc
        if owned.get("task_id") != TASK_ID or owned.get("root") != str(root):
            raise RootOwnershipError(
                f"{root} marker belongs to {owned.get('driver_id')!r}/{owned.get('task_id')!r}, not {driver_id!r}")
        return {**owned, "created": False, "adopted": owned.get("driver_id") != driver_id}
    root.mkdir(parents=True, exist_ok=True)
    owned = {"marker_version": 1, "driver_id": driver_id, "task_id": TASK_ID, "root": str(root),
             "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_json(marker, owned)
    return {**owned, "created": True, "adopted": False}


def reset_owned_content(root: Path) -> dict:
    """Rebuild this driver's own fixture content inside an already-owned root.

    Only paths this wave's drivers own are cleared; the ownership marker and every other
    driver's `process-records/` and `driver-records/` subtrees are preserved, so no driver
    ever deletes another driver's recorded artifacts."""
    root = Path(root)
    removed = []
    for child in sorted(root.iterdir()):
        if child.name in KEEP_ON_RESET:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed.append(child.name)
    return {"root": str(root), "removed": removed, "kept": list(KEEP_ON_RESET)}


def clean_owned_root(root: Path, driver_id: str) -> dict:
    """Explicit --clean-owned: remove only a root carrying this driver's own marker."""
    root = Path(root)
    marker = root / MARKER_NAME
    if not root.exists():
        return {"root": str(root), "removed": False, "reason": "absent"}
    if not marker.is_file():
        return {"root": str(root), "removed": False, "reason": "no marker; removal refused"}
    try:
        owned = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return {"root": str(root), "removed": False, "reason": "unreadable marker; removal refused"}
    if owned.get("driver_id") != driver_id or owned.get("task_id") != TASK_ID:
        return {"root": str(root), "removed": False, "reason": "marker belongs to another driver; removal refused"}
    shutil.rmtree(root)
    return {"root": str(root), "removed": True, "reason": "owned marker present"}


def root_inventory(root: Path) -> dict:
    """Hash-only inventory of a working-space root (nothing is copied)."""
    root = Path(root)
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            files.append({"path": str(path.relative_to(root)), "bytes": len(data), "sha256": sha256_bytes(data)})
    listing = json.dumps(files, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {"root": str(root), "files": len(files), "total_bytes": sum(f["bytes"] for f in files),
            "listing_sha256": sha256_bytes(listing), "artifacts": files}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return {"path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def program_hashes() -> dict:
    out = {}
    for name in PROGRAM_MODULES:
        p = SRC / "line_backup_acceptance" / name
        out[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    return out


def tree_manifest(root: Path, *, exclude=("manifest.json",)) -> dict:
    artifacts = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and path.name not in exclude:
            data = path.read_bytes()
            artifacts.append({"path": str(path.relative_to(root)), "bytes": len(data), "sha256": sha256_bytes(data)})
    return {"schema_version": 1, "root": str(root), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "files": len(artifacts), "total_bytes": sum(a["bytes"] for a in artifacts), "artifacts": artifacts}


def write_tree_manifest(root: Path, *, name="manifest.json", exclude_extra=()) -> dict:
    manifest = tree_manifest(root, exclude=(name, *exclude_extra))
    meta = write_json(root / name, manifest)
    manifest["manifest_sha256"] = meta["sha256"]
    manifest["manifest_bytes"] = meta["bytes"]
    return manifest


def product_env(extra: dict | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env["LC_ALL"] = "C"
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHASHSEED"] = "0"
    if extra:
        env.update(extra)
    return env


def product_argv(*args: str) -> list[str]:
    return ["/usr/bin/python3", "-m", "line_backup_acceptance", *args]


def run_product(record_dir: Path, args: list[str], *, env_extra: dict | None = None, timeout: float | None = None,
                cwd: Path | None = None) -> dict:
    """Run the product CLI in its own process group; record everything durably."""
    record_dir.mkdir(parents=True, exist_ok=True)
    argv = product_argv(*args) if args and args[0] not in {"--help"} else ["/usr/bin/python3", "-m", "line_backup_acceptance", *args]
    write_json(record_dir / "argv.json", {"argv": argv, "cwd": str(cwd or WORK), "env_extra": env_extra or {},
                                          "secrets_removed": True})
    try:
        proc = subprocess.run(argv, cwd=cwd or WORK, env=product_env(env_extra), capture_output=True, text=True,
                              check=False, timeout=timeout, start_new_session=True)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n<harness timeout after {timeout}s>\n"
        code = -1000
    (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(f"{code}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        parsed = None
    return {"argv": argv, "exit_code": code, "result": parsed, "record_dir": str(record_dir)}


def start_product(args: list[str], *, env_extra: dict | None = None) -> subprocess.Popen:
    """Start the product CLI in its own process group (for hard-interrupt windows)."""
    argv = product_argv(*args)
    return subprocess.Popen(argv, cwd=WORK, env=product_env(env_extra), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)


def hard_kill(proc: subprocess.Popen, *, grace: float = 0.0) -> dict:
    """SIGKILL the whole process group; collect the observed termination evidence."""
    import signal
    time.sleep(grace)
    pid = proc.pid
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
        killed_group = True
    except ProcessLookupError:
        killed_group = False
    try:
        stdout, stderr = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        stdout, stderr = "", "<no output; process already gone>"
    return {"pid": pid, "killed_process_group": killed_group, "returncode": proc.returncode,
            "signal": -proc.returncode if proc.returncode is not None and proc.returncode < 0 else None,
            "stdout": stdout, "stderr": stderr}


def counter_entries(counter: Path) -> list[dict]:
    if not counter.exists():
        return []
    entries = []
    for line in counter.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def wait_for(predicate, *, timeout: float = 20.0, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def write_dispatcher(path: Path, *, block_seconds: float = 0.0, outcome: str = "RETURNED",
                     crash_after_dispatch: bool = False, started_barrier: Path | None = None,
                     wait_parent: bool = False) -> Path:
    """Fixture dispatcher: appends one JSON line to the counter file (the only side effect)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#!/usr/bin/env python3",
        "import argparse, json, os, time",
        "p = argparse.ArgumentParser()",
        "p.add_argument('--counter')",
        "p.add_argument('--outcome')",
        "p.add_argument('--crash-after-dispatch', action='store_true')",
        "n = p.parse_args()",
        "with open(n.counter, 'a', encoding='utf-8') as fh:",
        "    fh.write(json.dumps({'outcome': n.outcome, 'pid': os.getpid(), 'ppid': os.getppid(),",
        "                         'at': time.time()}) + '\\n')",
    ]
    if started_barrier is not None:
        lines.append(f"open({str(started_barrier)!r}, 'w').close()")
    if wait_parent:
        lines += [
            "parent = os.getppid()",
            "deadline = time.time() + 300.0",
            "while time.time() < deadline:",
            "    if os.getppid() != parent:",
            "        raise SystemExit(3)",
            "    try:",
            "        os.kill(parent, 0)",
            "    except OSError:",
            "        raise SystemExit(3)",
            "    time.sleep(0.25)",
            "raise SystemExit(4)",
        ]
    else:
        lines.append(f"time.sleep({block_seconds!r})")
        lines.append("raise SystemExit(1 if n.crash_after_dispatch else 0)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def durable_copy_tree(src: Path, dest: Path) -> dict:
    """Copy a working tree into durable evidence storage; never delete the source.

    Append-only: an existing durable destination is refused instead of overwritten.
    """
    src, dest = Path(src), Path(dest)
    if dest.exists():
        raise RuntimeError(f"durable destination {dest} already exists; attempts are append-only")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    return write_tree_manifest(dest)


def ensure_attempt() -> Path:
    ATTEMPT.mkdir(parents=True, exist_ok=True)
    return ATTEMPT


def parse_args(description: str) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--case-root", required=True)
    ap.add_argument("--evidence-dir", required=True)
    return ap.parse_args()


def main_guard(fn):
    def wrapper() -> int:
        code = fn()
        return code if isinstance(code, int) else 0
    return wrapper
