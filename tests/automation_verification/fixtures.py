#!/usr/bin/env python3
"""Fixture builders for the automation-verification wave (test-mode fixture roots)."""
from __future__ import annotations

import shutil
from pathlib import Path

from harness import write_json

GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
FP57 = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}


def fresh_state() -> dict:
    return {"schema_version": 2, "revision": 0, "current_run_id": None, "active_writer_id": None,
            "context_lock": None, "runs": [], "verified_albums": []}


def make_run(run_id: str, owner: str, destination: str, *, group: str = GROUP, fp: dict | None = None,
             intent_state: str = "INTENT_COMMITTED", dispatch_state: str = "NOT_ATTEMPTED",
             trigger_outcome: str = "NOT_APPLICABLE", dispatch_outcome: str = "NOT_ATTEMPTED",
             workflow_outcome: str | None = None, phase: str | None = None,
             legacy: bool = False, observed_title: str | None = None, source_provenance: str | None = None,
             retry_allowed: bool = False, calibration: dict | None = None) -> dict:
    fp = dict(fp or FP57)
    run = {"run_id": run_id, "mode": "backup_one", "group_key": group, "album_id": None, "fingerprint": fp,
           "destination": destination, "workflow_outcome": workflow_outcome,
           "phase": phase or workflow_outcome or "SAVE_ALL_INTENT_COMMITTED",
           "owner_id": None if workflow_outcome else owner, "runtime_errors": [], "events": [],
           "reconciliations": [], "verification": None, "dispatch_evidence": None}
    if not legacy:
        run.update({
            "contract_revision": "1.0-rc2",
            "observed_title": observed_title if observed_title is not None else group.rsplit(":", 1)[-1],
            "source_provenance": source_provenance if source_provenance is not None else "fixture source",
            "title_confidence": "HIGH",
            "destination_initially_empty": True,
            "intent_state": intent_state, "dispatch_state": dispatch_state,
            "intent": {"action_id": "ACTION-" + run_id, "committed_at": "2026-09-16T00:00:00Z",
                       "owner_execution_id": owner, "group_key": group, "fingerprint": fp,
                       "destination": destination, "calibration": calibration or {"confidence": "HIGH", "evidence": "fixture"},
                       "intent_state": intent_state, "dispatch_state": dispatch_state,
                       "trigger_outcome": trigger_outcome, "dispatch_outcome": dispatch_outcome,
                       "save_all_retry_allowed": retry_allowed},
            "checkpoint": {"phase": phase or "SAVE_ALL_INTENT_COMMITTED", "at": "2026-09-16T00:00:00Z",
                           "evidence": "fixture checkpoint"},
        })
    return run


def write_fixture_root(case_root: Path, state: dict, *, destination_files: int = 0, verification: dict | None = None,
                       clean: bool = True) -> dict:
    case_root = Path(case_root)
    if clean and case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True, exist_ok=True)
    destination = case_root / "destination"
    destination.mkdir(exist_ok=True)
    for index in range(destination_files):
        (destination / f"image-{index:03d}.jpg").write_bytes(b"\xff\xd8\xff\xe0" + bytes(64))
    state_path = case_root / "state.json"
    write_json(state_path, state)
    write_json(case_root / "input-state.json", state)
    write_json(case_root / "verification.json", verification or {
        "filesystem_status": "PASS", "regular_files": destination_files, "recognized_images": destination_files,
        "zero_byte_files": 0})
    return {"case_root": str(case_root), "state": str(state_path), "destination": str(destination)}


def make_png(path: Path, *, size: int = 8, color=(10, 20, 30)) -> Path:
    """Deterministic, decodable 8-bit RGB PNG (no external libraries)."""
    import struct
    import zlib
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes(color * size) for _ in range(size))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return path
