#!/usr/bin/env python3
"""Phase 2 / R5 — verifier source & read gaps through the real `verify-only --test-mode` entry.

CLAIM  verify-only confirms claims it never verified:
       (a) `source_authority="authoritative_exact_join"` inside a `verified_albums` entry alone
           upgrades source_status to CONFIRMED, although no original join artifact is read;
       (b) `verified_albums[].verified_run_id` is never resolved against `runs[]`, so an entry whose
           verified run does not exist (b1) or is a terminal SAFE_ABORT run (b2) still passes;
       (c) `read_error` in `inspect()` only inspects `samples[0]`, so a read error that first appears
           in inventory samples 2/3 never reaches the UNKNOWN/INTERNAL_READ_ERROR classification;
       (d) image recognition is `file --mime-type` + hash only, so a truncated PNG header counts as a
           recognized photo without any decode step.
ENTRY  Real CLI `python3 -m line_backup_acceptance verify-only --test-mode`, canonical
       `<case>/config/line_backup_config.json` + `<case>/state/backup_state.json` under
       /private/tmp/line-backup-acceptance-verifier/r5/.  (c) uses `--pause-at SAMPLE_2_READY
       --barrier-file ...` and chmod 000 one destination file after sample #1 (restored afterwards).
ORACLE The verifier's own result.json (filesystem/registry/source/state/overall status, failure_class,
       exit code), the three inventory samples it persists, and state before/after (verify_only must
       not write state).
DECIDE If a forged string / unrelated run id / late-sample read error / truncated file still yields
       overall PASS (or is misclassified), R5 stands: verify-only must not confirm on claims it never
       verified.  Expected per contract: source cannot be CONFIRMED by a bare string; a registry entry
       whose verified run is missing or SAFE_ABORT cannot be an exact association; a read error is
       UNKNOWN/INTERNAL_READ_ERROR (never PASS); a truncated image is not a recognized actual image.
"""
from __future__ import annotations

import argparse
import binascii
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (durable_copy_tree, hard_kill, product_argv, program_hashes, read_json, run_product,
                     sha256_bytes, start_product, wait_for, write_json, write_tree_manifest)

WORK = Path(__file__).resolve().parents[2]
ATTEMPT = WORK / "evidence/20260916-auto-verification/attempt-01"
DEFAULT_CASE_ROOT = Path("/private/tmp/line-backup-acceptance-verifier/r5")
DEFAULT_EVIDENCE_DIR = ATTEMPT / "phase2-r5"
WORKSPACE_PARENT = Path("/private/tmp/line-backup-acceptance-verifier")
GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
FP = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}
JPEG_STUB = b"\xff\xd8\xff\xe0" + bytes(64)
MAGIC = "authoritative_exact_join"
CHMOD_TARGET = "image-042.jpg"
RESULT_FIELDS = ("overall_status", "filesystem_status", "registry_status", "source_status", "state_status",
                 "failure_class", "exit_code", "inventory_samples", "mode")
CASE_ROOT_BASE = DEFAULT_CASE_ROOT  # rebound in main() after the guard


# ---------------------------------------------------------------- fixtures

def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)


def full_tiny_png() -> bytes:
    """Deterministic 1x1 grayscale PNG, built with zlib+struct only (no user photos)."""
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
            + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00"))
            + _png_chunk(b"IEND", b""))


def png_decode_check(data: bytes) -> dict:
    """Minimal full-image decode: chunk walk + CRC + IHDR/IDAT/IEND + zlib inflate."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"decodes": False, "reason": "missing PNG signature"}
    offset, chunks, idat = 8, [], b""
    try:
        while offset + 8 <= len(data):
            (length,) = struct.unpack(">I", data[offset:offset + 4])
            tag = data[offset + 4:offset + 8]
            body = data[offset + 8:offset + 8 + length]
            if len(body) != length:
                return {"decodes": False, "reason": f"chunk {tag!r} truncated at offset {offset} ({len(body)}/{length} bytes)",
                        "chunks": chunks}
            (crc,) = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])
            if crc != (binascii.crc32(tag + body) & 0xFFFFFFFF):
                return {"decodes": False, "reason": f"chunk {tag!r} CRC mismatch", "chunks": chunks}
            chunks.append(tag.decode("latin1"))
            if tag == b"IDAT":
                idat += body
            if tag == b"IEND":
                break
            offset += 12 + length
        else:
            return {"decodes": False, "reason": f"no IEND; chunks={chunks}"}
    except struct.error as exc:
        return {"decodes": False, "reason": f"struct error: {exc}", "chunks": chunks}
    try:
        inflated = zlib.decompress(idat)
    except zlib.error as exc:
        return {"decodes": False, "reason": f"IDAT inflate failed: {exc}", "chunks": chunks}
    return {"decodes": True, "chunks": chunks, "inflated_pixels_bytes": len(inflated)}


def rc2_run(run_id: str, destination: str, workflow_outcome: str) -> dict:
    """Fully-populated RC2 run record (contract_revision/observed_title/source_provenance present,
    so `_association()` may reach state_status EXACT)."""
    return {"run_id": run_id, "mode": "backup_one", "group_key": GROUP, "album_id": None,
            "fingerprint": dict(FP), "observed_title": GROUP.rsplit(":", 1)[-1],
            "source_provenance": "r5 fixture source", "title_confidence": "HIGH",
            "destination": destination, "destination_initially_empty": True,
            "workflow_outcome": workflow_outcome, "phase": workflow_outcome, "owner_id": None,
            "contract_revision": "1.0-rc2", "intent_state": "INTENT_COMMITTED",
            "dispatch_state": "SAVE_ALL_RETURNED",
            "intent": {"action_id": f"ACTION-{run_id}", "committed_at": "2026-09-16T00:00:00Z",
                       "owner_execution_id": f"WRITER-{run_id}", "group_key": GROUP, "fingerprint": dict(FP),
                       "destination": destination, "calibration": {"confidence": "HIGH", "evidence": "fixture"},
                       "intent_state": "INTENT_COMMITTED", "dispatch_state": "SAVE_ALL_RETURNED",
                       "trigger_outcome": "UNKNOWN", "dispatch_outcome": "RETURNED",
                       "save_all_retry_allowed": False},
            "dispatch_evidence": None, "verification": None, "runtime_errors": [], "events": [],
            "reconciliations": [], "checkpoint": {"phase": workflow_outcome, "at": "2026-09-16T00:00:00Z",
                                                  "evidence": "r5 fixture terminal record"}}


def album_entry(destination: str, *, verified_run_id: str, source_authority: str | None, evidence: str) -> dict:
    entry = {"group_key": GROUP, "fingerprint": dict(FP), "verified_run_id": verified_run_id,
             "destinations": [destination], "source_kind": "filesystem_verification", "evidence": evidence}
    if source_authority is not None:
        entry["source_authority"] = source_authority
    return entry


def fixture_destination(case_name: str) -> str:
    return str(CASE_ROOT_BASE / case_name / "backup_root" / "destination")


def build_case(case_root: Path, *, images: list[tuple[str, bytes]], runs: list[dict], albums: list[dict]) -> dict:
    if case_root.exists():
        shutil.rmtree(case_root)
    backup_root = case_root / "backup_root"
    destination = backup_root / "destination"
    destination.mkdir(parents=True)
    for filename, data in images:
        (destination / filename).write_bytes(data)
    (case_root / "config").mkdir()
    (case_root / "state").mkdir()
    write_json(case_root / "config" / "line_backup_config.json", {
        "schema_version": 2, "group_key": GROUP, "group_name": GROUP.rsplit(":", 1)[-1],
        "backup_root": str(backup_root), "app_identifier": "jp.naver.line.mac",
        "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
        "stable_samples": 3, "max_wait_seconds": 60})
    write_json(case_root / "state" / "backup_state.json", {
        "schema_version": 2, "revision": 1, "current_run_id": None, "active_writer_id": None,
        "context_lock": None, "runs": runs, "verified_albums": albums})
    (case_root / "state" / "run_log.md").write_text("# run log (r5 fixture; verify_only does not write it)\n",
                                                    encoding="utf-8")
    return {"case_root": str(case_root), "backup_root": str(backup_root), "destination": str(destination)}


def verify_args(case_root: Path, destination: str, *, extra: tuple[str, ...] = ()) -> list[str]:
    return ["verify-only", "--project-root", str(case_root),
            "--config", str(case_root / "config" / "line_backup_config.json"),
            "--state", str(case_root / "state" / "backup_state.json"),
            "--destination", destination, "--group-key", GROUP,
            "--start-date", FP["start_date"], "--end-date", FP["end_date"],
            "--expected-images", str(FP["expected_images"]),
            "--evidence-dir", str(case_root / "evidence"), "--test-mode", *extra]


# ---------------------------------------------------------------- recording helpers

def result_summary(result: dict | None) -> dict:
    if not isinstance(result, dict):
        return {"parsed": False}
    return {key: result.get(key) for key in RESULT_FIELDS if key in result}


def stash_case_evidence(record_dir: Path, case_root: Path, *, state_before: dict) -> dict:
    write_json(record_dir / "state-before.json", state_before)
    state_after = read_json(case_root / "state" / "backup_state.json")
    write_json(record_dir / "state-after.json", state_after)
    case_result = case_root / "evidence" / "result.json"
    if case_result.exists():
        shutil.copyfile(case_result, record_dir / "verifier-result.json")
    return {"state_unchanged": state_after == state_before,
            "state_revision_after": state_after.get("revision"),
            "verifier_result_present": case_result.exists()}


def inventory_samples(case_root: Path) -> list[dict]:
    samples = []
    for index in (1, 2, 3):
        path = case_root / "evidence" / f"inventory-{index}.json"
        samples.append(read_json(path) if path.exists() else {})
    return samples


def sample_target_entries(case_root: Path, target: str) -> list[dict]:
    rows = []
    for index, sample in enumerate(inventory_samples(case_root), start=1):
        entry = next((e for e in sample.get("entries", []) if e.get("relative_path") == target), None)
        rows.append({"sample": index,
                     "status": (entry or {}).get("status"),
                     "mime": (entry or {}).get("mime"),
                     "sha256": (entry or {}).get("sha256"),
                     "error_code": (entry or {}).get("error_code"),
                     "error": (entry or {}).get("error")})
    return rows


def _row_facts(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "sample"}


def run_simple_case(name: str, *, images: list[tuple[str, bytes]], runs: list[dict], albums: list[dict],
                    ev: Path, timeout: float = 120.0) -> dict:
    case_root = CASE_ROOT_BASE / name
    setup = build_case(case_root, images=images, runs=runs, albums=albums)
    state_before = read_json(case_root / "state" / "backup_state.json")
    record_dir = ev / "records" / name
    rec = run_product(record_dir, verify_args(case_root, setup["destination"]), timeout=timeout)
    stash = stash_case_evidence(record_dir, case_root, state_before=state_before)
    return {"case_root": case_root, "setup": setup, "record_dir": record_dir, "run": rec, "stash": stash}


def run_barrier_case(name: str, *, chmod: bool, ev: Path) -> dict:
    """(c) driver: real verify-only entry paused at SAMPLE_2_READY; optionally chmod 000 one file
    after sample #1, then release the barrier and restore permissions afterwards."""
    case_root = CASE_ROOT_BASE / name
    destination = case_root / "backup_root" / "destination"
    setup = build_case(
        case_root, images=[(f"image-{i:03d}.jpg", JPEG_STUB) for i in range(57)],
        runs=[rc2_run("RUN-A", str(destination), "VERIFIED")],
        albums=[album_entry(str(destination), verified_run_id="RUN-A", source_authority=MAGIC,
                            evidence="r5 fixture entry (string-only join claim)")])
    state_before = read_json(case_root / "state" / "backup_state.json")
    record_dir = ev / "records" / name
    record_dir.mkdir(parents=True, exist_ok=True)
    barrier = case_root / "barrier-file"
    args = verify_args(case_root, setup["destination"], extra=("--pause-at", "SAMPLE_2_READY",
                                                               "--barrier-file", str(barrier)))
    write_json(record_dir / "argv.json", {"argv": product_argv(*args), "cwd": str(WORK),
                                          "env_extra": {}, "secrets_removed": True,
                                          "stimulus": f"chmod 000 {CHMOD_TARGET} after sample #1" if chmod
                                          else "control: no chmod"})
    proc = start_product(args)
    ready = Path(str(barrier) + ".ready")
    saw_ready = wait_for(ready.exists, timeout=30.0)
    chmod_applied = None
    target = destination / CHMOD_TARGET
    if saw_ready:
        if chmod:
            os.chmod(target, 0o000)
            chmod_applied = oct(target.stat().st_mode & 0o777)
        barrier.touch()
        try:
            stdout, stderr = proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            killed = hard_kill(proc)
            stdout, stderr = killed["stdout"], killed["stderr"]
    else:
        killed = hard_kill(proc)
        stdout, stderr = killed["stdout"], killed["stderr"]
    restored = None
    if chmod and chmod_applied is not None:
        os.chmod(target, 0o644)
        restored = oct(target.stat().st_mode & 0o777)
    (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        parsed = None
    stash = stash_case_evidence(record_dir, case_root, state_before=state_before)
    write_json(record_dir / "barrier-report.json", {
        "pause_at": "SAMPLE_2_READY", "saw_ready": saw_ready, "chmod_target": CHMOD_TARGET,
        "chmod_applied_mode": chmod_applied, "chmod_restored_mode": restored,
        "target_per_sample": sample_target_entries(case_root, CHMOD_TARGET)})
    return {"case_root": case_root, "setup": setup, "record_dir": record_dir, "saw_ready": saw_ready,
            "chmod_applied": chmod_applied, "chmod_restored": restored, "exit_code": proc.returncode,
            "result": parsed, "stash": stash}


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2 R5 — verifier source & read gaps")
    ap.add_argument("--case-root", default=str(DEFAULT_CASE_ROOT))
    ap.add_argument("--evidence-dir", default=str(DEFAULT_EVIDENCE_DIR))
    ap.add_argument("--force", action="store_true",
                    help="re-run into an evidence dir that already contains observation.json")
    ns = ap.parse_args()

    case_base = Path(ns.case_root)
    ev = Path(ns.evidence_dir)
    if case_base.resolve() != DEFAULT_CASE_ROOT.resolve():
        raise SystemExit(f"refusing: --case-root must be exactly {DEFAULT_CASE_ROOT} (got {case_base})")
    if ev.resolve() != DEFAULT_EVIDENCE_DIR.resolve():
        raise SystemExit(f"refusing: --evidence-dir must be exactly {DEFAULT_EVIDENCE_DIR} (got {ev})")
    if (ev / "observation.json").exists() and not ns.force:
        raise SystemExit(f"refusing to overwrite existing evidence without --force: {ev}")
    if ev.exists():
        shutil.rmtree(ev)  # this script is the only writer of phase2-r5; rebuild it cleanly
    ev.mkdir(parents=True)
    if case_base.exists():
        shutil.rmtree(case_base)
    case_base.mkdir(parents=True)

    subcases: dict[str, dict] = {}

    # (a) forged source_authority magic string, no raw join evidence anywhere in state
    a_dest = fixture_destination("a-forged-source-authority")
    run = run_simple_case(
        "a-forged-source-authority",
        images=[(f"image-{i:03d}.jpg", JPEG_STUB) for i in range(57)],
        runs=[rc2_run("RUN-A", a_dest, "VERIFIED")],
        albums=[album_entry(a_dest, verified_run_id="RUN-A", source_authority=MAGIC,
                            evidence="forged: string-only authoritative_exact_join claim, no join artifact exists")],
        ev=ev)
    res = run["run"]["result"]
    subcases["a_forged_source_authority"] = {
        "claim": "source_authority=\"authoritative_exact_join\" alone upgrades source_status to CONFIRMED "
                 "(no original join evidence is read).",
        "fixture": {"case_root": str(run["case_root"]),
                    "registry_entry": album_entry(a_dest, verified_run_id="RUN-A", source_authority=MAGIC,
                                                  evidence="forged string-only"),
                    "raw_join_artifact_present": False,
                    "run_verification_field": None},
        "expected_under_contract": "source_status must not be CONFIRMED without reading the raw join evidence",
        "observed": {**result_summary(res), "state_unchanged": run["stash"]["state_unchanged"]},
        "verdict": "REPRODUCED_FALSE_SOURCE_CONFIRMATION"
        if (res or {}).get("source_status") == "CONFIRMED" and (res or {}).get("overall_status") == "PASS"
        else "NOT_REPRODUCED"}

    # (b1) verified_run_id points at a run that does not exist
    b1_dest = fixture_destination("b1-dangling-verified-run-id")
    run = run_simple_case(
        "b1-dangling-verified-run-id",
        images=[(f"image-{i:03d}.jpg", JPEG_STUB) for i in range(57)],
        runs=[rc2_run("RUN-A", b1_dest, "VERIFIED")],
        albums=[album_entry(b1_dest, verified_run_id="RUN-DOES-NOT-EXIST", source_authority=MAGIC,
                            evidence="forged: verified_run_id resolved by nobody")],
        ev=ev)
    res = run["run"]["result"]
    subcases["b1_dangling_verified_run_id"] = {
        "claim": "verified_albums[].verified_run_id is never resolved against runs[]; a dangling id still passes.",
        "fixture": {"case_root": str(run["case_root"]), "run_ids_in_state": ["RUN-A"],
                    "entry_verified_run_id": "RUN-DOES-NOT-EXIST"},
        "expected_under_contract": "entry must not associate when its verified run id cannot be matched in runs[]",
        "observed": {**result_summary(res), "state_unchanged": run["stash"]["state_unchanged"]},
        "verdict": "REPRODUCED_DANGLING_VERIFIED_RUN_ID_ACCEPTED"
        if (res or {}).get("overall_status") == "PASS" else "NOT_REPRODUCED"}

    # (b2) verified_run_id points at a terminal SAFE_ABORT run
    b2_dest = fixture_destination("b2-safe-abort-run-linked")
    run = run_simple_case(
        "b2-safe-abort-run-linked",
        images=[(f"image-{i:03d}.jpg", JPEG_STUB) for i in range(57)],
        runs=[rc2_run("RUN-B", b2_dest, "SAFE_ABORT")],
        albums=[album_entry(b2_dest, verified_run_id="RUN-B", source_authority=MAGIC,
                            evidence="forged: registered as verified though its run aborted")],
        ev=ev)
    res = run["run"]["result"]
    subcases["b2_safe_abort_run_linked"] = {
        "claim": "an entry whose verified run is terminal SAFE_ABORT is still accepted (cross-entry not verified).",
        "fixture": {"case_root": str(run["case_root"]),
                    "runs": [{"run_id": "RUN-B", "workflow_outcome": "SAFE_ABORT"}],
                    "entry_verified_run_id": "RUN-B"},
        "expected_under_contract": "a registered verified album must not link a SAFE_ABORT run",
        "observed": {**result_summary(res), "state_unchanged": run["stash"]["state_unchanged"]},
        "verdict": "REPRODUCED_SAFE_ABORT_RUN_LINKED_ACCEPTED"
        if (res or {}).get("overall_status") == "PASS" else "NOT_REPRODUCED"}

    # (c) read error that first appears in samples 2/3 (control: same fixture, no chmod)
    control = run_barrier_case("c0-control-no-chmod", chmod=False, ev=ev)
    chmod_run = run_barrier_case("c-read-error-after-sample-1", chmod=True, ev=ev)
    c_res = chmod_run["result"]
    control_res = control["result"]
    target_rows = sample_target_entries(chmod_run["case_root"], CHMOD_TARGET)
    late_read_error = (target_rows[0]["status"] == "OK"
                       and all(row["status"] == "READ_ERROR" for row in target_rows[1:3]))
    samples_2_3_identical = (_row_facts(target_rows[1]) == _row_facts(target_rows[2])) if len(target_rows) == 3 else False
    if (c_res or {}).get("overall_status") == "PASS":
        c_verdict = "REPRODUCED_LATE_SAMPLE_READ_ERROR_FALSE_PASS"
    elif not chmod_run["saw_ready"]:
        c_verdict = "INCONCLUSIVE_SETUP_FAILED"
    elif late_read_error and (c_res or {}).get("overall_status") in {"NOT_ACHIEVED", "UNKNOWN"}:
        c_verdict = "REPRODUCED_DIFFERENT_MANIFESTATION_MISCLASSIFIED_NOT_PASS"
    else:
        c_verdict = "NOT_REPRODUCED"
    subcases["c_late_sample_read_error"] = {
        "claim": "read_error only inspects samples[0]: a read error first appearing in samples 2/3 escapes "
                 "the UNKNOWN/INTERNAL_READ_ERROR classification (task claim expects a false overall PASS).",
        "fixture": {"case_root": str(chmod_run["case_root"]), "pause_at": "SAMPLE_2_READY",
                    "chmod_after_sample_1": CHMOD_TARGET, "expected_images": 57},
        "control_run": {"case_root": str(control["case_root"]), "saw_ready": control["saw_ready"],
                        "exit_code": control["exit_code"], "result": result_summary(control_res)},
        "stimulus_run": {"case_root": str(chmod_run["case_root"]), "saw_ready": chmod_run["saw_ready"],
                         "chmod_applied_mode": chmod_run["chmod_applied"],
                         "chmod_restored_mode": chmod_run["chmod_restored"],
                         "exit_code": chmod_run["exit_code"], "result": result_summary(c_res),
                         "target_per_sample": target_rows,
                         "inventory_error_codes": [s.get("error_codes") for s in inventory_samples(chmod_run["case_root"])]},
        "expected_under_contract": "read error must surface as UNKNOWN/INTERNAL_READ_ERROR (never PASS); "
                                   "filesystem PASS requires stable inventory over ALL samples and no read errors",
        "observed": {
            "claimed_current_behavior": "overall PASS (false positive)",
            "actual_current_behavior": {
                "overall_status": (c_res or {}).get("overall_status"),
                "filesystem_status": (c_res or {}).get("filesystem_status"),
                "failure_class": (c_res or {}).get("failure_class"),
                "exit_code": (c_res or {}).get("exit_code"),
            },
            "sample_1_clean": target_rows[0]["status"] == "OK",
            "samples_2_3_read_error_identical": samples_2_3_identical,
            "read_error_gate_input": "inspect(): read_error = any(status == READ_ERROR for e in samples[0]['entries'])",
            "note": "sample-level error_codes do contain INTERNAL_READ_ERROR, but the classification branch "
                    "requires the sample-1-only read_error flag, so the late read error is reported as "
                    "filesystem FAIL / INPUT_NEGATIVE instead of UNKNOWN / INTERNAL_READ_ERROR; the exact "
                    "claimed false PASS cannot occur with this classifier because the stability check compares "
                    "every sample against samples[0], but the read-error classification itself is unreachable "
                    "for samples 2/3 (the code path that would report UNKNOWN/INTERNAL_READ_ERROR never fires)",
        },
        "verdict": c_verdict}

    # (d) truncated-but-MIME-valid image counted as a recognized photo
    png_full = full_tiny_png()
    png_truncated = png_full[:40]
    d_dest = fixture_destination("d-truncated-png")
    run = run_simple_case(
        "d-truncated-png",
        images=[(f"image-{i:03d}.jpg", JPEG_STUB) for i in range(56)] + [("image-056.png", png_truncated)],
        runs=[rc2_run("RUN-A", d_dest, "VERIFIED")],
        albums=[album_entry(d_dest, verified_run_id="RUN-A", source_authority=MAGIC,
                            evidence="r5 fixture entry (string-only join claim)")],
        ev=ev)
    res = run["run"]["result"]
    sample1 = inventory_samples(run["case_root"])[0]
    png_entry = next((e for e in sample1.get("entries", []) if e.get("relative_path") == "image-056.png"), {})
    subcases["d_truncated_png"] = {
        "claim": "`file --mime-type` + hash is not a decode: a valid PNG truncated to its signature+IHDR is "
                 "counted in recognized_images and yields overall PASS.",
        "fixture": {"case_root": str(run["case_root"]), "files": 57, "truncated_file": "image-056.png",
                    "full_png_bytes": len(png_full), "full_png_sha256": sha256_bytes(png_full),
                    "truncated_bytes": len(png_truncated), "truncated_sha256": sha256_bytes(png_truncated),
                    "decode_check_full": png_decode_check(png_full),
                    "decode_check_truncated": png_decode_check(png_truncated)},
        "expected_under_contract": "a file that cannot be decoded as an image must not be counted as a recognized "
                                   "actual image (no decode step is executed today)",
        "observed": {**result_summary(res),
                     "recognized_images": sample1.get("recognized_images"),
                     "truncated_entry": {"mime": png_entry.get("mime"), "status": png_entry.get("status"),
                                         "size": png_entry.get("size")},
                     "state_unchanged": run["stash"]["state_unchanged"]},
        "verdict": "REPRODUCED_TRUNCATED_IMAGE_COUNTED_AS_PHOTO_PASS"
        if (res or {}).get("overall_status") == "PASS" and png_entry.get("mime") == "image/png"
        and sample1.get("recognized_images") == 57 else "NOT_REPRODUCED"}

    # ---------------- durable copies + observation + manifest
    durable_roots = {}
    for path in sorted(case_base.iterdir()):
        if path.is_dir():
            durable_roots[path.name] = durable_copy_tree(path, ev / "case-root-durable" / path.name)

    verdicts = {name: block["verdict"] for name, block in subcases.items()}
    reproduced = [name for name, value in verdicts.items() if value.startswith("REPRODUCED")]
    if all(value.startswith("REPRODUCED") and "DIFFERENT_MANIFESTATION" not in value for value in verdicts.values()):
        overall = "REPRODUCED"
    elif reproduced:
        overall = "REPRODUCED_WITH_VARIANCE"
    else:
        overall = "NOT_REPRODUCED"

    observation = {
        "schema_version": 1,
        "task": "Phase 2 R5 — verifier source & read gaps",
        "claim": "verify-only confirms registry source/association claims it never verified (forged "
                 "source_authority string, unresolved/aborted verified_run_id), misclassifies read errors "
                 "that appear after sample 1, and counts truncated-but-MIME-valid files as recognized photos.",
        "entry": "python3 -m line_backup_acceptance verify-only --test-mode (canonical config/state under "
                 f"{case_base}); (c) additionally --pause-at SAMPLE_2_READY --barrier-file",
        "oracle": "verifier result.json (overall/filesystem/registry/source/state/failure_class/exit), its three "
                  "persisted inventory samples, state before/after (unchanged), and per-file sample entries",
        "decision": "any overall PASS for (a)/(b1)/(b2)/(d) keeps R5 open; for (c) the UNKNOWN/INTERNAL_READ_ERROR "
                    "classification must be reachable regardless of which sample first observes the read error",
        "program_hashes": program_hashes(),
        "code_references": {
            "src/line_backup_acceptance/verifier.py:172":
                'source_proof = bool(exact and exact[0].get("source_authority") == "authoritative_exact_join") '
                "- the only source gate; no join artifact is read",
            "src/line_backup_acceptance/verifier.py:206":
                'read_error = any(e.get("status") == "READ_ERROR" for e in samples[0]["entries"]) '
                "- sample-1-only read-error gate",
            "src/line_backup_acceptance/verifier.py (grep verified_run_id)":
                "0 occurrences - verified_albums[].verified_run_id is never resolved against runs[]",
            "src/line_backup_acceptance/verifier.py:120":
                "recognized_images counts any regular file whose `file --mime-type` output is in IMAGE_MIMES; "
                "no decode/decodability check exists",
        },
        "case_root_base": str(case_base),
        "evidence_dir": str(ev),
        "subcases": subcases,
        "durable_roots": durable_roots,
        "verdict": overall,
        "residual_uncertainty": [
            "R5(c) as stated in the task ('late-sample read error -> overall PASS') was NOT observed; the "
            "observed defect is misclassification (INPUT_NEGATIVE instead of UNKNOWN/INTERNAL_READ_ERROR), "
            "so no false PASS exists for that exact stimulus with the current classifier.",
            "Evidence is fixture-based (68-byte JPEG stubs and a synthetic PNG); no real user photos were used.",
            "The forged registry entries were written directly into the fixture state; the product's own "
            "finalize path (R4) does not write source_authority today.",
        ],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_json(ev / "observation.json", observation)
    supplement = {"schema_version": 1,
                  "note": "The shared harness tree manifest excludes files named manifest.json; this supplement "
                          "records SHA-256+bytes for those verifier-owned manifests. manifest-supplement.json is "
                          "itself covered by manifest.json.",
                  "files": [{"path": str(path.relative_to(ev)), "bytes": path.stat().st_size,
                             "sha256": sha256_bytes(path.read_bytes())}
                            for path in sorted(ev.rglob("manifest.json"))]}
    write_json(ev / "manifest-supplement.json", supplement)
    manifest = write_tree_manifest(ev)
    print(json.dumps({"verdict": overall, "subcases": verdicts,
                      "manifest": {"files": manifest["files"], "total_bytes": manifest["total_bytes"],
                                   "manifest_sha256": manifest["manifest_sha256"]}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
