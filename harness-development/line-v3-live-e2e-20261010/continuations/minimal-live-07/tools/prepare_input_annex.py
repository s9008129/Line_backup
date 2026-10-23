#!/usr/bin/env python3
"""Publish immutable snapshots for explicitly authorized read-only inputs."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import pathlib
import stat
import sys

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
R = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
sys.path.insert(0, str(R / "tools"))
from evidence_io import open_anchored_directory, publish_exclusive

SOURCE = "codex-session-01a12976-2554-7ed0-8d4c-356688f674ee.md"
RECORDER = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/代理協作開發紀錄.md"
EXPECTED = {"dev": 16777229, "ino": 134658566, "mode": 33152, "uid": 501, "gid": 20,
            "size": 2381481, "mtime_ns": 1791717244792215415, "ctime_ns": 1791717244792301332,
            "sha256": "5cd0f697d6b6eac0bd7c6ffa284397980b08113aab2cd480435735f2e2028210"}


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture_root_file(name: str) -> tuple[bytes, dict]:
    rel = pathlib.PurePosixPath(name)
    parent_path = ROOT.joinpath(*rel.parts[:-1])
    root_fd = open_anchored_directory(parent_path)
    try:
        fd = os.open(rel.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root_fd)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise RuntimeError("READ_ONLY_INPUT_NOT_REGULAR")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        current = os.stat(rel.parts[-1], dir_fd=root_fd, follow_symlinks=False)
        values = lambda s: {"dev": s.st_dev, "ino": s.st_ino, "mode": s.st_mode, "uid": s.st_uid,
                            "gid": s.st_gid, "size": s.st_size, "mtime_ns": s.st_mtime_ns,
                            "ctime_ns": s.st_ctime_ns, "birthtime": getattr(s, "st_birthtime", None)}
        if values(before) != values(after) or values(after) != values(current) or len(raw) != after.st_size:
            raise RuntimeError("READ_ONLY_INPUT_IDENTITY_DRIFT")
        result = values(after)
        result["sha256"] = sha(raw)
        return raw, result
    finally:
        os.close(root_fd)


def publish(path: str, data: bytes, producer: str) -> dict:
    return {"path": path, "producer": producer, **publish_exclusive(ROOT, path, data, max_bytes=8 * 1024 * 1024)}


def main() -> int:
    if (len(sys.argv) != 1 or pathlib.Path.cwd() != ROOT
            or pathlib.Path(os.path.realpath(__file__)) != R / "tools/prepare_input_annex.py"):
        raise RuntimeError("LOCATION_OR_ARGUMENTS")
    source, source_stat = capture_root_file(SOURCE)
    if any(source_stat.get(k) != v for k, v in EXPECTED.items()):
        raise RuntimeError("USER_INPUT_PREIMAGE_MISMATCH")
    observed = dt.datetime.now(dt.timezone.utc).isoformat()
    annex = {"format": "ML07_READ_ONLY_USER_INPUT_ANNEX_V1", "task_id": "TASK-20261010-line-v3-live-e2e",
             "authority": "READ_ONLY_USER_INPUT", "user_reference": SOURCE, "source_absolute_path": str(ROOT / SOURCE),
             "source_fstat": source_stat, "source_base64": base64.b64encode(source).decode("ascii"),
             "source_producer": None, "source_write_authority": None,
             "decision_owner": "root_planner", "publisher": "context_history", "observed_at_utc": observed,
             "historical": {"old_namespace_absence_observed_at_utc": "2026-10-11T06:09:58.275012Z",
                            "old_namespace_records_sha256": "6fef9dbcc4d6dfcccdfcb3e72bf5073fa5049277e1c81665c4b16fbd1b6041bd",
                            "pre_11_14_bytes_and_creator": "UNKNOWN"}}
    annex_raw = encoded(annex)
    annex_ref = publish(f"{R.relative_to(ROOT).as_posix()}/evidence/read-only-user-input-01.json", annex_raw, "context_history")
    annex_receipt = {"format": "ML07_READ_ONLY_INPUT_ANNEX_RECEIPT_V1", "task_id": annex["task_id"],
                     "authority": annex["authority"], "publisher": "context_history", "decision_owner": "root_planner",
                     "source_producer": None, "source_write_authority": None, "source_fstat": source_stat,
                     "annex": annex_ref, "readback_verified": True, "observed_at_utc": observed}
    annex_receipt_ref = publish(f"{R.relative_to(ROOT).as_posix()}/evidence/read-only-user-input-01.receipt.json", encoded(annex_receipt), "context_history")

    recorder, recorder_stat = capture_root_file(RECORDER)
    snap_rel = f"{R.relative_to(ROOT).as_posix()}/evidence/recorder-log-initial-01.md"
    snapshot_ref = publish(snap_rel, recorder, "context_history")
    snapshot_receipt = {"format": "ML07_RECORDER_INITIAL_SNAPSHOT_RECEIPT_V1", "task_id": annex["task_id"],
                        "source_path": RECORDER, "source_producer": "collaboration_recorder",
                        "publisher": "context_history", "source_fstat": recorder_stat,
                        "snapshot": snapshot_ref, "readback_verified": True, "observed_at_utc": observed}
    snapshot_receipt_ref = publish(f"{R.relative_to(ROOT).as_posix()}/evidence/recorder-log-initial-01.receipt.json", encoded(snapshot_receipt), "context_history")
    print(json.dumps({"annex": annex_ref, "annex_receipt": annex_receipt_ref,
                      "recorder_snapshot": snapshot_ref, "recorder_receipt": snapshot_receipt_ref,
                      "source_sha256": source_stat["sha256"], "recorder_sha256": recorder_stat["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
