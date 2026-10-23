#!/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13
"""Recovery-02 host-side receipt writer (host-authored helper, tmp/).

Usage:
  python -B tmp/make_host_receipt.py '<json blob>'
blob = {"check_id": str, "exit_code": int, "argv": [str,...],
        "source_hashes": {rel: sha256}, "started_at_utc": str|null,
        "started_epoch": float|null, "ended_epoch": float|null}

Reads RUNROOT/evidence/<check_id>.stdout and .stderr (must already exist),
then writes RUNROOT/evidence/<check_id>.receipt.json and
<check_id>.invocation.json exclusively (O_EXCL; refuses if either exists).
Never rewrites. Readback verified. No child processes, no network.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
EVIDENCE = ROOT / RUNREL / "evidence"
TMPDIR = ROOT / RUNREL / "tmp"
FORMAT = "RECOVERY_02_HOST_RECEIPT_V1"


def sha256_file(path: pathlib.Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            h.update(chunk)
    return size, h.hexdigest()


def ref_of(path: pathlib.Path) -> dict:
    size, digest = sha256_file(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "absolute_path": str(path),
        "bytes": size,
        "sha256": digest,
    }


def write_exclusive(path: pathlib.Path, data: bytes) -> dict:
    dir_fd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        wfd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(wfd, view):]
            os.fsync(wfd)
        finally:
            os.close(wfd)
        rfd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        try:
            chunks = []
            while True:
                chunk = os.read(rfd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(rfd)
        readback = b"".join(chunks)
    finally:
        os.close(dir_fd)
    if readback != data:
        raise RuntimeError(f"WRITE_READBACK_MISMATCH:{path}")
    return {"path": path.relative_to(ROOT).as_posix(), "absolute_path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(json.dumps({"status": "REFUSED", "errors": ["usage: make_host_receipt.py '<json blob>'"]}))
        return 2
    blob = json.loads(argv[1])
    check_id = str(blob["check_id"])
    stem = EVIDENCE / check_id
    stdout_path = pathlib.Path(f"{stem}.stdout")
    stderr_path = pathlib.Path(f"{stem}.stderr")
    receipt_path = pathlib.Path(f"{stem}.receipt.json")
    invocation_path = pathlib.Path(f"{stem}.invocation.json")
    for path in (receipt_path, invocation_path):
        if os.path.lexists(path):
            print(json.dumps({"status": "REFUSED", "errors": [f"ID_COLLISION:{path}"]}))
            return 2
    for path in (stdout_path, stderr_path):
        if not path.exists():
            print(json.dumps({"status": "REFUSED", "errors": [f"MISSING_STREAM:{path}"]}))
            return 2
    stdout_ref = ref_of(stdout_path)
    stderr_ref = ref_of(stderr_path)
    exit_code = int(blob["exit_code"])
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    started_epoch = blob.get("started_epoch")
    ended_epoch = blob.get("ended_epoch")
    elapsed_ms = None
    if isinstance(started_epoch, (int, float)) and isinstance(ended_epoch, (int, float)):
        elapsed_ms = int((ended_epoch - started_epoch) * 1000)
    receipt = {
        "format": FORMAT,
        "kind": "RECOVERY_02_HOST_RECEIPT",
        "task_id": "TASK-20261011-line-baseline-recovery-02",
        "run_rel": RUNREL,
        "check_id": check_id,
        "status": "PASS" if exit_code == 0 else "FAIL",
        "exit_code": exit_code,
        "timeout": False,
        "argv": [str(item) for item in blob.get("argv") or []],
        "cwd": str(ROOT),
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(TMPDIR),
            "TMP": str(TMPDIR),
            "TEMP": str(TMPDIR),
        },
        "source_hashes": blob.get("source_hashes") or {},
        "started_at_utc": blob.get("started_at_utc"),
        "ended_at_utc": now_utc,
        "elapsed_ms": elapsed_ms,
        "stdout": stdout_ref,
        "stderr": stderr_ref,
        "readback_verified": True,
        "automatic_retry": False,
        "native_harness_validation": "NOT_RUN",
        "created_at_utc": now_utc,
        "created_monotonic_ns": time.monotonic_ns(),
    }
    invocation = {
        "format": "RECOVERY_02_HOST_INVOCATION_V1",
        "check_id": check_id,
        "argv": receipt["argv"],
        "cwd": str(ROOT),
        "environment": receipt["environment"],
        "host_command_line": " ".join(receipt["argv"]),
        "stdout_path": stdout_ref,
        "stderr_path": stderr_ref,
        "receipt_path": str(receipt_path),
        "started_at_utc": blob.get("started_at_utc"),
        "ended_at_utc": now_utc,
        "elapsed_ms": elapsed_ms,
    }
    receipt_ref = write_exclusive(receipt_path, (json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    invocation_ref = write_exclusive(invocation_path, (json.dumps(invocation, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": "OK", "check_id": check_id, "receipt": receipt_ref, "invocation": invocation_ref}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
