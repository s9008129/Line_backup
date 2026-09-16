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
ATTEMPT = WORK / "evidence/20260916-auto-verification/attempt-01"
PROGRAM_MODULES = ("transaction.py", "verifier.py", "status.py", "authority.py", "cli.py", "common.py")


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


def write_tree_manifest(root: Path, *, name="manifest.json") -> dict:
    manifest = tree_manifest(root, exclude=(name,))
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


def write_dispatcher(path: Path, *, block_seconds: float = 0.0) -> Path:
    """Fixture dispatcher: appends one JSON line to the counter file (the only side effect)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, json, os, time\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--counter')\n"
        "p.add_argument('--outcome')\n"
        "p.add_argument('--crash-after-dispatch', action='store_true')\n"
        "n = p.parse_args()\n"
        "with open(n.counter, 'a', encoding='utf-8') as fh:\n"
        "    fh.write(json.dumps({'outcome': n.outcome, 'pid': os.getpid(), 'at': time.time()}) + '\\n')\n"
        f"time.sleep({block_seconds!r})\n"
        "raise SystemExit(1 if n.crash_after_dispatch else 0)\n",
        encoding="utf-8")
    path.chmod(0o755)
    return path


def durable_copy_tree(src: Path, dest: Path) -> dict:
    """Copy a working tree into durable evidence storage; never delete the source."""
    if dest.exists():
        shutil.rmtree(dest)
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
