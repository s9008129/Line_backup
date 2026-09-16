#!/usr/bin/env python3
"""Fixture builders for the automation-verification wave (test-mode fixture roots).

Rev16 §16.1 canonical layout: every literal case root carries
config/line_backup_config.json, state/backup_state.json, state/run_log.md,
input-state.json (fixture source of the pre-state) and evidence/.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

from harness import sha256_bytes, sha256_file, write_json

GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"          # requested, 禎 U+798E
LEGACY_GROUP = "line:jp.naver.line.mac:旻謙允楨成長日記"    # persisted, 楨 U+6968 (never merged)
GROUP_NAME = "旻謙允禎成長日記"
FP57 = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}
CALIBRATION = {"observed_at": "2026-09-16T00:00:00Z", "screenshot_width": 1512, "screenshot_height": 982,
               "ellipsis": [1400, 300], "dot_spacing": 24.0, "save_all_point": [1200, 210],
               "confidence": "HIGH", "evidence": "fixture calibration (test-mode, driver-authored)"}
EVIDENCE_ARTIFACT_KEYS = {"path", "bytes", "sha256"}


def fresh_state(revision: int = 0) -> dict:
    return {"schema_version": 2, "revision": revision, "current_run_id": None, "active_writer_id": None,
            "context_lock": None, "runs": [], "verified_albums": []}


def base_config(root: Path, *, group_key: str = GROUP) -> dict:
    root = Path(root)
    return {"schema_version": 2, "group_key": group_key, "group_name": GROUP_NAME,
            "backup_root": str(root / "backups"), "app_identifier": "jp.naver.line.mac",
            "max_albums_per_run": 50, "recovery_limit": 1, "poll_interval_seconds": 5,
            "stable_samples": 3, "max_wait_seconds": 60}


def write_canonical_root(root: Path, state: dict | None = None, *, group_key: str = GROUP,
                         destination_images: int = 0, destination_name: str = "destination",
                         config_extra: dict | None = None) -> dict:
    """Create the Rev16 §16.1 canonical children (fixture content only, never state writes)."""
    root = Path(root)
    state = state if state is not None else fresh_state()
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(parents=True, exist_ok=True)
    (root / "backups").mkdir(parents=True, exist_ok=True)
    config = base_config(root, group_key=group_key)
    if config_extra:
        config.update(config_extra)
    config_path = root / "config" / "line_backup_config.json"
    state_path = root / "state" / "backup_state.json"
    run_log_path = root / "state" / "run_log.md"
    input_state_path = root / "input-state.json"
    write_json(config_path, config)
    write_json(state_path, state)
    write_json(input_state_path, state)
    run_log_path.write_text("# fixture run log (the product never writes this file)\n", encoding="utf-8")
    destination = root / destination_name
    destination.mkdir(parents=True, exist_ok=True)
    for index in range(destination_images):
        make_png(destination / f"image-{index:03d}.png")
    return {"case_root": str(root), "config": str(config_path), "state": str(state_path),
            "run_log": str(run_log_path), "input_state": str(input_state_path),
            "destination": str(destination), "evidence": str(root / "evidence"),
            "backup_root": config["backup_root"]}


def install_state(root: Path, state: dict) -> dict:
    """Install a fixture pre-state into the single authoritative state file."""
    root = Path(root)
    path = root / "state" / "backup_state.json"
    write_json(path, state)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


# ---------------------------------------------------------------------------
# Deterministic, structurally decodable images (no external libraries)
# ---------------------------------------------------------------------------

def make_png(path: Path, *, size: int = 8, color=(10, 20, 30), iend: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes(color * size) for _ in range(size))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw))
    if iend:
        out += chunk(b"IEND", b"")
    path.write_bytes(out)
    return path


def make_jpeg(path: Path, *, size: int = 8, eoi: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x01\x01" + b"\x00" + struct.pack(">HH", 1, 1) + b"\x00\x00"
    sof = (b"\xff\xc0" + struct.pack(">H", 11) + bytes([8]) + struct.pack(">HH", size, size) + bytes([3])
           + b"\x01\x11\x00\x02\x11\x00\x03\x11\x00")
    sos = b"\xff\xda" + struct.pack(">H", 12) + bytes([3]) + b"\x01\x00\x02\x00\x03\x00" + b"\x00\x3f\x00"
    out = b"\xff\xd8" + app0 + sof + sos + (b"\xff\xd9" if eoi else b"")
    path.write_bytes(out)
    return path


# ---------------------------------------------------------------------------
# Source-evidence record (Rev15 §15.3) and the external binding artifact
# ---------------------------------------------------------------------------

def artifact_entry(path: Path) -> dict:
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def write_binding_fixture(root: Path, *, name: str = "binding-fixture.json", group_key: str = GROUP,
                          fp: dict | None = None, kind: str = "fixture", extra: dict | None = None) -> Path:
    root = Path(root)
    payload = {"app_identifier": "jp.naver.line.mac", "group_key": group_key, "fingerprint": dict(fp or FP57),
               "note": f"test-mode {kind} binding fixture"}
    if extra:
        payload.update(extra)
    path = root / name
    write_json(path, payload)
    return path


def source_evidence_record(root: Path, *, group_key: str = GROUP, fp: dict | None = None, test_mode: bool = True,
                           name: str = "source-evidence.json", binding_name: str = "binding-fixture.json",
                           calibration: dict | None = None, binding_kind: str = "fixture",
                           binding_path: Path | None = None, overrides: dict | None = None) -> dict:
    root = Path(root)
    fp = dict(fp or FP57)
    if binding_path is None:
        binding_path = write_binding_fixture(root, name=binding_name, group_key=group_key, fp=fp, kind=binding_kind)
    record = {"record_version": 1, "test_mode": test_mode, "app_identifier": "jp.naver.line.mac",
              "group_key": group_key, "observed_title": group_key.rsplit(":", 1)[-1],
              "title_confidence": "HIGH", "fingerprint": fp, "observed_at": "2026-09-16T00:00:00Z",
              "calibration": dict(calibration or CALIBRATION), "binding": {"kind": binding_kind, "artifact": artifact_entry(binding_path)},
              "evidence_artifacts": [artifact_entry(binding_path)]}
    if overrides:
        record.update(overrides)
    path = root / name
    write_json(path, record)
    return {"path": str(path), "record": record, "binding_path": str(binding_path)}


# ---------------------------------------------------------------------------
# Schema-valid run records
# ---------------------------------------------------------------------------

def _intent(run_id: str, owner: str, destination: str, *, group: str, fp: dict,
            dispatch_outcome: str = "NOT_ATTEMPTED", trigger_outcome: str = "NOT_APPLICABLE",
            calibration: dict | None = None, retry: bool = False) -> dict:
    return {"action_id": f"ACTION-{run_id}", "committed_at": "2026-09-16T00:00:00Z",
            "owner_execution_id": owner, "group_key": group, "fingerprint": dict(fp),
            "destination": destination, "calibration": dict(calibration or CALIBRATION),
            "save_all_retry_allowed": retry, "dispatch_outcome": dispatch_outcome,
            "trigger_outcome": trigger_outcome}


def make_run(run_id: str, owner: str | None, destination: str, *, group: str = GROUP, fp: dict | None = None,
             intent_state: str = "INTENT_COMMITTED", dispatch_state: str = "NOT_ATTEMPTED",
             trigger_outcome: str = "NOT_APPLICABLE", dispatch_outcome: str = "NOT_ATTEMPTED",
             workflow_outcome: str = "IN_PROGRESS", phase: str = "SAVE_ALL_INTENT_COMMITTED",
             dispatch_evidence: dict | None = None, verification: dict | None = None,
             reconciliations: list | None = None, manual_reconciliation_required: bool = False,
             reconciliation_reason: str | None = None, events: list | None = None,
             calibration: dict | None = None, contract_revision: str | None = "1.0-rc2",
             observed_title: str | None = None, title_confidence: str = "HIGH",
             destination_initially_empty: bool = True, checkpoint_phase: str | None = None) -> dict:
    fp = dict(fp or FP57)
    run = {"run_id": run_id, "mode": "backup_one", "group_key": group, "album_id": None, "fingerprint": fp,
           "observed_title": observed_title if observed_title is not None else group.rsplit(":", 1)[-1],
           "title_confidence": title_confidence, "destination": destination,
           "destination_initially_empty": destination_initially_empty,
           "workflow_outcome": workflow_outcome, "phase": phase,
           "checkpoint": {"phase": checkpoint_phase or phase, "at": "2026-09-16T00:00:00Z", "evidence": "fixture checkpoint"},
           "events": list(events or []), "intent": _intent(run_id, owner or "WRITER-FIXTURE", destination,
                                                           group=group, fp=fp, dispatch_outcome=dispatch_outcome,
                                                           trigger_outcome=trigger_outcome, calibration=calibration),
           "recovery_used": {}, "runtime_errors": [], "verification": verification,
           "stop_reason": None, "batch_id": None, "intent_state": intent_state,
           "manual_reconciliation_required": manual_reconciliation_required,
           "reconciliation_reason": reconciliation_reason}
    if contract_revision is not None:
        run["contract_revision"] = contract_revision
        run["dispatch_state"] = dispatch_state
        run["dispatch_evidence"] = dispatch_evidence
        run["reconciliations"] = list(reconciliations if reconciliations is not None else [])
    return run


def dispatch_proof(run_id: str, owner: str, *, click_count: int = 1, attempted: bool = True,
                   boundary: str = "NONE", chooser: bool = False, started: bool = False) -> dict:
    return {"run_id": run_id, "action_id": f"ACTION-{run_id}", "execution_id": owner,
            "observed_at": "2026-09-16T00:00:00Z", "save_all_click_count": click_count,
            "save_all_invocation_attempted": attempted, "failure_boundary": boundary,
            "folder_chooser_appeared": chooser, "download_started": started,
            "provenance": "fixture dispatcher adapter (test-mode side-effect fake)"}


def completed_dispatch_run(run_id: str, owner: str, destination: str, *, group: str = GROUP,
                           fp: dict | None = None) -> dict:
    return make_run(run_id, owner, destination, group=group, fp=fp, intent_state="SAVE_ALL_DISPATCH_ATTEMPTED",
                    dispatch_state="SAVE_ALL_RETURNED", trigger_outcome="UNKNOWN", dispatch_outcome="RETURNED",
                    phase="SAVE_ALL_DISPATCH_ATTEMPTED",
                    dispatch_evidence=dispatch_proof(run_id, owner),
                    events=[{"phase": "SAVE_ALL_INTENT_COMMITTED", "at": "2026-09-16T00:00:00Z",
                             "evidence": "fixture checkpoint"},
                            {"phase": "SAVE_ALL_DISPATCH_ATTEMPTED", "at": "2026-09-16T00:00:00Z",
                             "evidence": "fixture dispatch record"}])


def verified_state(run_id: str, owner: str, destination: str, *, group: str = GROUP, fp: dict | None = None,
                   evidence_reference: str = "fixture:binding-fixture.json:" + "0" * 64,
                   source_kind: str = "filesystem_verification", verified_run_id: str | None = None,
                   revision: int = 2, binding_path: Path | None = None) -> dict:
    """Terminal VERIFIED state used by verifier/legacy rows; the binding reference is written
    both into the registry entry and into the run events (the verifier's same-reference gate)."""
    fp = dict(fp or FP57)
    if binding_path is not None:
        reference = f"fixture:{Path(binding_path).name}:{sha256_file(Path(binding_path))}"
        evidence_reference = reference
    run = completed_dispatch_run(run_id, owner, destination, group=group, fp=fp)
    run["workflow_outcome"] = "VERIFIED"
    run["phase"] = "VERIFIED"
    run["checkpoint"] = {"phase": "VERIFIED", "at": "2026-09-16T00:00:00Z", "evidence": "fixture terminal VERIFIED"}
    run["events"].append({"phase": "VERIFIED", "at": "2026-09-16T00:00:00Z", "evidence": evidence_reference})
    state = fresh_state(revision=revision)
    state["runs"] = [run]
    state["verified_albums"] = [{"group_key": group, "fingerprint": fp,
                                 "verified_run_id": verified_run_id if verified_run_id is not None else run_id,
                                 "destinations": [destination], "source_kind": source_kind,
                                 "evidence": evidence_reference}]
    return state


def reconciliation_entry(run: dict, *, released: bool, index: int = 1, proof: dict | None = None) -> dict:
    return {"reconciliation_id": f"RECON-{run['run_id']}-{index}", "recorded_at": "2026-09-16T00:00:00Z",
            "run_id": run["run_id"], "action_id": run["intent"]["action_id"],
            "execution_id": run["intent"]["owner_execution_id"], "outcome": "ABORTED_BEFORE_SAVE_ALL_DISPATCH",
            "trigger_outcome": "NOT_TRIGGERED", "blocking_intent_released": released,
            "manual_reconciliation_required": False,
            "original_observation": {"reference": f"intent-checkpoint:{run['run_id']}:rev0",
                                     "trigger_outcome": "NOT_TRIGGERED"},
            "proof": proof or dispatch_proof(run["run_id"], run["intent"]["owner_execution_id"], click_count=0,
                                             attempted=False, boundary="BEFORE_SAVE_ALL_INVOCATION"),
            "evidence": "fixture non-dispatch reconciliation"}


def write_json_file(path: Path, value) -> dict:
    write_json(path, value)
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
