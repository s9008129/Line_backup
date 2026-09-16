#!/usr/bin/env python3
"""Phase 2 / R5 (post-fix) — verifier source & read gaps closed: safe verdicts through the real
`verify-only --test-mode` entry.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  verify-only confirmed claims it never verified:
       a forged `source_authority` string alone reached CONFIRMED, a dangling or SAFE_ABORT
       `verified_run_id` still passed, a read error first appearing in samples 2/3 was
       misclassified, and a truncated PNG counted as a recognized photo while overall PASSed.

ENTRY  Real CLI `python3 -m line_backup_acceptance verify-only --test-mode`, canonical
       `<case>/config/line_backup_config.json` + `<case>/state/backup_state.json` under the
       literal driver root /private/tmp/line-backup-acceptance-verifier/r5/.  The read-error row
       uses `--pause-at SAMPLE_2_READY --barrier-file ...` and chmod 000 on one destination file
       after sample #1 (restored afterwards; the driver never deletes foreign content).

ORACLE The verifier's own result.json chain (filesystem/registry/source/state/overall status,
       failure_class, exit code), the three persisted inventory samples, and state before/after
       (verify_only must not write state).

DECIDE Post-fix safe verdicts (Rev14 F4/F5, Rev15 §15.3/§15.4, Rev18 §18.1):
       - a bare forged string can no longer CONFIRM: Registry PASS / Source UNRESOLVED /
         NOT_ACHIEVED / exit 4 / INPUT_PROVENANCE_LIMITED; a genuine fixture binding still
         verifies (negative control: PASS / CONFIRMED / EXACT / exit 0).
       - dangling / SAFE_ABORT / non-terminal links: Registry FAIL / Source UNRESOLVED /
         NOT_ACHIEVED / exit 4 / INPUT_NEGATIVE.
       - any-sample read error: Filesystem FAIL / Registry-Source-State NOT_RUN / Overall UNKNOWN /
         exit 1 / INTERNAL_READ_ERROR (never PASS, never INPUT_NEGATIVE).
       - truncated PNG / JPEG missing EOI / unsupported image type: Filesystem FAIL /
         INPUT_NEGATIVE or UNSUPPORTED_IMAGE_TYPE / exit 4; never counted as recognized photos.
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
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r5-verifier-gaps"
WORK = H.WORK
DEFAULT_CASE_ROOT = Path("/private/tmp/line-backup-acceptance-verifier/r5")
GROUP = F.GROUP
FP = dict(F.FP57)
MAGIC = "authoritative_exact_join"
CHMOD_TARGET = "image-042.png"
RESULT_FIELDS = ("overall_status", "filesystem_status", "registry_status", "source_status", "state_status",
                 "failure_class", "exit_code", "inventory_samples", "mode", "source_kind")
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
    """Schema-valid RC2 run record (so `classify_legacy_run` stays clean and state can reach EXACT)."""
    owner = f"WRITER-{run_id}"
    phase = workflow_outcome if workflow_outcome in {"VERIFIED", "SAFE_ABORT"} else "SAVE_ALL_DISPATCH_ATTEMPTED"
    outcome = workflow_outcome if workflow_outcome in {"VERIFIED", "SAFE_ABORT"} else "IN_PROGRESS"
    return F.make_run(run_id, owner, destination, workflow_outcome=outcome, phase=phase,
                      intent_state="SAVE_ALL_DISPATCH_ATTEMPTED", dispatch_state="SAVE_ALL_RETURNED",
                      trigger_outcome="UNKNOWN", dispatch_outcome="RETURNED",
                      dispatch_evidence=F.dispatch_proof(run_id, owner), events=[])


def album_entry(destination: str, *, verified_run_id: str, source_authority: str | None, evidence: str) -> dict:
    entry = {"group_key": GROUP, "fingerprint": dict(FP), "verified_run_id": verified_run_id,
             "destinations": [destination], "source_kind": "filesystem_verification", "evidence": evidence}
    if source_authority is not None:
        entry["source_authority"] = source_authority
    return entry


def fixture_destination(case_name: str) -> str:
    return str(CASE_ROOT_BASE / case_name / "backup_root" / "destination")


def build_case(case_root: Path, *, images: list[tuple[str, bytes]], runs: list[dict], albums: list[dict]) -> dict:
    H.ensure_owned_root(case_root, DRIVER_ID)
    H.reset_owned_content(case_root)
    backup_root = case_root / "backup_root"
    destination = backup_root / "destination"
    destination.mkdir(parents=True)
    for filename, data in images:
        (destination / filename).write_bytes(data)
    (case_root / "config").mkdir()
    (case_root / "state").mkdir()
    H.write_json(case_root / "config" / "line_backup_config.json", {
        "schema_version": 2, "group_key": GROUP, "group_name": GROUP.rsplit(":", 1)[-1],
        "backup_root": str(backup_root), "app_identifier": "jp.naver.line.mac",
        "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
        "stable_samples": 3, "max_wait_seconds": 60})
    H.write_json(case_root / "state" / "backup_state.json", {
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
    H.write_json(record_dir / "state-before.json", state_before)
    state_after = H.read_json(case_root / "state" / "backup_state.json")
    H.write_json(record_dir / "state-after.json", state_after)
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
        samples.append(H.read_json(path) if path.exists() else {})
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


def axes_of(result: dict | None) -> dict:
    result = result or {}
    return {"filesystem_status": result.get("filesystem_status"), "registry_status": result.get("registry_status"),
            "source_status": result.get("source_status"), "state_status": result.get("state_status"),
            "overall_status": result.get("overall_status"), "failure_class": result.get("failure_class"),
            "exit_code": result.get("exit_code")}


def run_simple_case(name: str, *, images: list[tuple[str, bytes]], runs: list[dict], albums: list[dict],
                    ev: Path, timeout: float = 120.0) -> dict:
    case_root = CASE_ROOT_BASE / name
    setup = build_case(case_root, images=images, runs=runs, albums=albums)
    state_before = H.read_json(case_root / "state" / "backup_state.json")
    record_dir = ev / "records" / name
    rec = H.run_product(record_dir, verify_args(case_root, setup["destination"]), timeout=timeout)
    stash = stash_case_evidence(record_dir, case_root, state_before=state_before)
    return {"case_root": case_root, "setup": setup, "record_dir": record_dir, "run": rec, "stash": stash}


def run_barrier_case(name: str, *, chmod: bool, ev: Path, image_payload: bytes) -> dict:
    """Read-error row: real verify-only entry paused at SAMPLE_2_READY; optionally chmod 000 one file
    after sample #1, then release the barrier and restore permissions afterwards."""
    case_root = CASE_ROOT_BASE / name
    destination = case_root / "backup_root" / "destination"
    setup = build_case(
        case_root, images=[(f"image-{i:03d}.png", image_payload) for i in range(57)],
        runs=[rc2_run("RUN-A", str(destination), "VERIFIED")],
        albums=[album_entry(str(destination), verified_run_id="RUN-A", source_authority=MAGIC,
                            evidence="forged: string-only authoritative_exact_join claim, no join artifact exists")])
    state_before = H.read_json(case_root / "state" / "backup_state.json")
    record_dir = ev / "records" / name
    record_dir.mkdir(parents=True, exist_ok=True)
    barrier = case_root / "barrier-file"
    args = verify_args(case_root, setup["destination"], extra=("--pause-at", "SAMPLE_2_READY",
                                                               "--barrier-file", str(barrier)))
    H.write_json(record_dir / "argv.json", {"argv": H.product_argv(*args), "cwd": str(WORK),
                                            "env_extra": {}, "secrets_removed": True,
                                            "stimulus": f"chmod 000 {CHMOD_TARGET} after sample #1" if chmod
                                            else "control: no chmod"})
    proc = H.start_product(args)
    ready = Path(str(barrier) + ".ready")
    saw_ready = H.wait_for(ready.exists, timeout=30.0)
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
            killed = H.hard_kill(proc)
            stdout, stderr = killed["stdout"], killed["stderr"]
    else:
        killed = H.hard_kill(proc)
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
    H.write_json(record_dir / "barrier-report.json", {
        "pause_at": "SAMPLE_2_READY", "saw_ready": saw_ready, "chmod_target": CHMOD_TARGET,
        "chmod_applied_mode": chmod_applied, "chmod_restored_mode": restored,
        "target_per_sample": sample_target_entries(case_root, CHMOD_TARGET)})
    return {"case_root": case_root, "setup": setup, "record_dir": record_dir, "saw_ready": saw_ready,
            "chmod_applied": chmod_applied, "chmod_restored": restored, "exit_code": proc.returncode,
            "result": parsed, "stash": stash, "argv": args}


def evaluate_subcase(block: dict, expected: dict, *, verdict_ok: str, state_unchanged_required: bool = True) -> dict:
    block = {key: (str(value) if isinstance(value, Path) else value) for key, value in block.items()}
    result = (block.get("run") or block)["result"]
    observed = axes_of(result)
    matches = {key: observed.get(key) == value for key, value in expected.items()}
    if "state_unchanged" in expected:
        matches["state_unchanged"] = block["stash"]["state_unchanged"] == expected["state_unchanged"]
    block.update({"observed": observed, "expected": expected, "matches": matches,
                  "ok": all(matches.values()) and (not state_unchanged_required or block["stash"]["state_unchanged"]),
                  "verdict": verdict_ok})
    return block


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2 R5 (post-fix) — verifier source & read gaps")
    ap.add_argument("--case-root", default=str(DEFAULT_CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()

    case_base = Path(ns.case_root)
    ev = Path(ns.evidence_dir)
    if case_base.resolve() != DEFAULT_CASE_ROOT.resolve():
        raise SystemExit(f"refusing: --case-root must be exactly {DEFAULT_CASE_ROOT} (got {case_base})")
    if ev.exists() and any(ev.iterdir()):
        raise SystemExit(f"refusing: evidence dir {ev} is not empty (append-only evidence)")

    H.ensure_owned_root(case_base, DRIVER_ID)
    H.reset_owned_content(case_base)
    ev.mkdir(parents=True, exist_ok=True)
    probe_dir = ev / "probe-images"
    probe_dir.mkdir(parents=True, exist_ok=True)
    valid_png = F.make_png(probe_dir / "_valid-sample.png").read_bytes()

    subcases: dict[str, dict] = {}

    # (a) forged source_authority magic string, no raw join evidence anywhere in state
    a_dest = fixture_destination("a-forged-source-authority")
    forged_entry = album_entry(a_dest, verified_run_id="RUN-A", source_authority=MAGIC,
                               evidence="forged: string-only authoritative_exact_join claim, no join artifact exists")
    run = run_simple_case(
        "a-forged-source-authority",
        images=[(f"image-{i:03d}.png", valid_png) for i in range(57)],
        runs=[rc2_run("RUN-A", a_dest, "VERIFIED")], albums=[forged_entry], ev=ev)
    block = evaluate_subcase(run, {"filesystem_status": "PASS", "registry_status": "PASS",
                                   "source_status": "UNRESOLVED", "state_status": "EXACT",
                                   "overall_status": "NOT_ACHIEVED", "failure_class": "INPUT_PROVENANCE_LIMITED",
                                   "exit_code": 4},
                             verdict_ok="SAFE_FORGED_STRING_NOT_CONFIRMED")
    block["claim"] = "a bare source_authority magic string used to upgrade source_status to CONFIRMED"
    subcases["a_forged_source_authority"] = block

    # (a2) negative control: a genuine fixture binding, referenced by the run event and the entry,
    #      still verifies end-to-end (PASS / CONFIRMED / EXACT).
    a2_root = CASE_ROOT_BASE / "a2-valid-binding-control"
    H.ensure_owned_root(a2_root, DRIVER_ID)
    H.reset_owned_content(a2_root)
    paths = F.write_canonical_root(a2_root, F.verified_state(
        "RUN-A2", "WRITER-A2", str(a2_root / "backups" / "destination"), binding_path=None),
        destination_name="backups/destination", destination_images=57)
    binding = F.write_binding_fixture(a2_root, name="binding-valid.json")
    state = F.verified_state("RUN-A2", "WRITER-A2", paths["destination"], binding_path=binding)
    state_path_info = F.install_state(a2_root, state)
    state_before = H.read_json(a2_root / "state" / "backup_state.json")
    record_dir = ev / "records" / "a2-valid-binding-control"
    rec = H.run_product(record_dir, verify_args(a2_root, paths["destination"]), timeout=120)
    stash = stash_case_evidence(record_dir, a2_root, state_before=state_before)
    block = evaluate_subcase({"run": rec, "stash": stash, "case_root": a2_root},
                             {"filesystem_status": "PASS", "registry_status": "PASS",
                              "source_status": "CONFIRMED", "state_status": "EXACT",
                              "overall_status": "PASS", "failure_class": "NONE", "exit_code": 0},
                             verdict_ok="SAFE_VALID_BINDING_CONFIRMED")
    block["claim"] = "negative control: a valid external binding (re-hashed and re-read) still confirms"
    block["binding"] = {"path": str(binding), "artifact": F.artifact_entry(binding),
                        "reference_in_state": (state.get("verified_albums") or [{}])[0].get("evidence"),
                        "state_before_install": state_path_info}
    subcases["a2_valid_binding_control"] = block

    # (b1..b3) unresolved / non-terminal verified_run_id links
    rows_b = [
        ("b1-dangling-verified-run-id", "RUN-DOES-NOT-EXIST",
         [rc2_run("RUN-A", fixture_destination("b1-dangling-verified-run-id"), "VERIFIED")],
         "SAFE_DANGLING_VERIFIED_RUN_ID_REFUSED"),
        ("b2-safe-abort-run-linked", "RUN-B",
         [rc2_run("RUN-B", fixture_destination("b2-safe-abort-run-linked"), "SAFE_ABORT")],
         "SAFE_SAFE_ABORT_LINK_REFUSED"),
        ("b3-nonterminal-run-linked", "RUN-C",
         [rc2_run("RUN-C", fixture_destination("b3-nonterminal-run-linked"), "DISPATCH_ATTEMPTED")],
         "SAFE_NONTERMINAL_LINK_REFUSED"),
    ]
    for name, verified_run_id, runs, verdict in rows_b:
        dest = fixture_destination(name)
        run = run_simple_case(
            name, images=[(f"image-{i:03d}.png", valid_png) for i in range(57)], runs=runs,
            albums=[album_entry(dest, verified_run_id=verified_run_id, source_authority=MAGIC,
                                evidence="forged: entry links a run that is not terminal VERIFIED")], ev=ev)
        block = evaluate_subcase(run, {"filesystem_status": "PASS", "registry_status": "FAIL",
                                       "source_status": "UNRESOLVED", "state_status": "EXACT",
                                       "overall_status": "NOT_ACHIEVED", "failure_class": "INPUT_NEGATIVE",
                                       "exit_code": 4}, verdict_ok=verdict)
        block["claim"] = f"entry verified_run_id={verified_run_id} must not produce an exact association"
        subcases[name.replace("-", "_")] = block

    # (c) any-sample read error: control (no chmod) vs stimulus (chmod after sample #1)
    control = run_barrier_case("c0-control-no-chmod", chmod=False, ev=ev, image_payload=valid_png)
    control_block = evaluate_subcase(control, {"filesystem_status": "PASS", "registry_status": "PASS",
                                               "source_status": "UNRESOLVED", "state_status": "EXACT",
                                               "overall_status": "NOT_ACHIEVED",
                                               "failure_class": "INPUT_PROVENANCE_LIMITED", "exit_code": 4},
                                     verdict_ok="SAFE_CONTROL_FORGED_BINDING_ONLY")
    control_block["claim"] = "control: the same fixture without the read-error stimulus"
    subcases["c0_control_no_chmod"] = control_block

    chmod_run = run_barrier_case("c-read-error-after-sample-1", chmod=True, ev=ev, image_payload=valid_png)
    # The normative axis matrix (plan.md:1195/1211) and the accepted verifier fixture driver pin
    # State=UNKNOWN for the read-error branch (Rev15 line 736 still reads "State NOT_RUN"; recorded
    # as a textual variance in execution.md, not a behavioural change).
    c_block = evaluate_subcase(chmod_run, {"filesystem_status": "FAIL", "registry_status": "NOT_RUN",
                                           "source_status": "NOT_RUN", "state_status": "UNKNOWN",
                                           "overall_status": "UNKNOWN", "failure_class": "INTERNAL_READ_ERROR",
                                           "exit_code": 1}, verdict_ok="SAFE_ANY_SAMPLE_READ_ERROR_UNKNOWN")
    target_rows = sample_target_entries(chmod_run["case_root"], CHMOD_TARGET)
    c_block["claim"] = "a read error first visible in samples 2/3 must surface as UNKNOWN/INTERNAL_READ_ERROR"
    c_block["read_error_evidence"] = {
        "saw_ready": chmod_run["saw_ready"], "chmod_applied_mode": chmod_run["chmod_applied"],
        "chmod_restored_mode": chmod_run["chmod_restored"], "target_per_sample": target_rows,
        "sample_1_clean": target_rows[0]["status"] == "OK",
        "samples_2_3_read_error": all(row["status"] == "READ_ERROR" for row in target_rows[1:]),
        "inventory_error_codes": [s.get("error_codes") for s in inventory_samples(chmod_run["case_root"])]}
    c_block["matches"]["sample_1_clean"] = c_block["read_error_evidence"]["sample_1_clean"]
    c_block["matches"]["samples_2_3_read_error"] = c_block["read_error_evidence"]["samples_2_3_read_error"]
    c_block["ok"] = c_block["ok"] and all(c_block["matches"].values())
    subcases["c_read_error_sample_2"] = c_block

    # (d) structural image decode: truncated PNG / JPEG without EOI / unsupported type
    png_full = full_tiny_png()
    png_truncated = png_full[:40]
    jpeg_eoi_ok = F.make_jpeg(probe_dir / "_probe-ok.jpg", eoi=True).read_bytes()
    jpeg_no_eoi = F.make_jpeg(probe_dir / "_probe-bad.jpg", eoi=False).read_bytes()
    rows_d = [
        ("d1-truncated-png", [(f"image-{i:03d}.png", valid_png) for i in range(56)] + [("image-056.png", png_truncated)],
         "image-056.png", "DECODE_ERROR", "INPUT_NEGATIVE", "SAFE_TRUNCATED_PNG_REFUSED",
         {"full_png_sha256": H.sha256_bytes(png_full), "truncated_sha256": H.sha256_bytes(png_truncated),
          "truncated_bytes": len(png_truncated), "decode_check_truncated": png_decode_check(png_truncated)}),
        ("d2-jpeg-missing-eoi", [(f"image-{i:03d}.png", valid_png) for i in range(56)] + [("image-056.jpg", jpeg_no_eoi)],
         "image-056.jpg", "DECODE_ERROR", "INPUT_NEGATIVE", "SAFE_JPEG_MISSING_EOI_REFUSED",
         {"jpeg_probe_ok_bytes": len(jpeg_eoi_ok), "jpeg_no_eoi_bytes": len(jpeg_no_eoi)}),
        ("d3-unsupported-image-type", [(f"image-{i:03d}.png", valid_png) for i in range(56)]
         + [("image-056.gif", b"GIF89a" + bytes(32))],
         "image-056.gif", "UNSUPPORTED", "UNSUPPORTED_IMAGE_TYPE", "SAFE_UNSUPPORTED_TYPE_REFUSED", {}),
    ]
    for name, images, target, status, failure, verdict, extra in rows_d:
        dest = fixture_destination(name)
        run = run_simple_case(name, images=images,
                              runs=[rc2_run("RUN-A", dest, "VERIFIED")],
                              albums=[album_entry(dest, verified_run_id="RUN-A", source_authority=MAGIC,
                                                  evidence="r5 fixture entry (string-only join claim)")], ev=ev)
        block = evaluate_subcase(run, {"filesystem_status": "FAIL", "registry_status": "NOT_RUN",
                                       "source_status": "NOT_RUN", "state_status": "NOT_RUN",
                                       "overall_status": "NOT_ACHIEVED", "failure_class": failure, "exit_code": 4},
                                 verdict_ok=verdict)
        sample1 = inventory_samples(run["case_root"])[0]
        entry = next((e for e in sample1.get("entries", []) if e.get("relative_path") == target), {})
        block["claim"] = f"{target} must not count as a recognized image ({status})"
        block["image_evidence"] = {"target": target, "entry_status": entry.get("status"), "mime": entry.get("mime"),
                                   "recognized_images": sample1.get("recognized_images"),
                                   "expected_images": FP["expected_images"], **extra}
        block["matches"]["target_entry_status"] = entry.get("status") == status
        block["matches"]["recognized_below_expected"] = sample1.get("recognized_images") == FP["expected_images"] - 1
        block["ok"] = block["ok"] and all(block["matches"].values())
        subcases[name.replace("-", "_")] = block

    # ---------------- durable copies + observation + manifest
    durable = H.durable_copy_tree(case_base, ev / "case-root-durable")
    verdicts = {name: block["verdict"] if block["ok"] else "REGRESSION_OR_UNEXPECTED"
                for name, block in subcases.items()}
    failed = sorted(name for name, block in subcases.items() if not block["ok"])
    overall = "SAFE_R5_AXIS_AND_READ_ERROR_CONTRACT" if not failed else "REGRESSION_OR_UNEXPECTED"
    observation = {
        "schema_version": 1,
        "task": "Phase 2 R5 (post-fix) — verifier source & read gaps",
        "claim": "post-fix: forged strings cannot CONFIRM, unresolved/non-terminal links FAIL, any-sample read "
                 "errors are UNKNOWN/INTERNAL_READ_ERROR, and structurally invalid images are refused",
        "entry": "python3 -m line_backup_acceptance verify-only --test-mode (canonical config/state under "
                 f"{case_base}); the read-error row additionally uses --pause-at SAMPLE_2_READY --barrier-file",
        "oracle": "verifier result.json chain (axes/failure_class/exit), its three persisted inventory samples, "
                  "state before/after (unchanged), per-file sample entries and an independent PNG/JPEG structure check",
        "pre_fix": {"attempt": "evidence/20260916-auto-verification/attempt-01/phase2-r5",
                    "verdicts": ["REPRODUCED_FALSE_SOURCE_CONFIRMATION", "REPRODUCED_DANGLING_VERIFIED_RUN_ID_ACCEPTED",
                                 "REPRODUCED_SAFE_ABORT_RUN_LINKED_ACCEPTED",
                                 "REPRODUCED_DIFFERENT_MANIFESTATION_MISCLASSIFIED_NOT_PASS",
                                 "REPRODUCED_TRUNCATED_IMAGE_COUNTED_AS_PHOTO_PASS"]},
        "program_hashes": H.program_hashes(),
        "case_root_base": str(case_base), "evidence_dir": str(ev),
        "subcases": subcases, "durable_root": durable, "verdict": overall, "failed_subcases": failed,
        "residual_uncertainty": [
            "Evidence is fixture-based (68-byte JPEG stubs, synthetic PNGs/GIFs); no real user photos were used.",
            "The forged registry entries were written directly into the fixture state; the product's own finalize "
            "path refuses the same payloads (R4 refusal rows).",
        ],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    H.write_json(ev / "observation.json", observation)
    supplement = {"schema_version": 1,
                  "note": "The shared harness tree manifest excludes files named manifest.json; this supplement "
                          "records SHA-256+bytes for those verifier-owned chains. manifest-supplement.json is "
                          "itself covered by manifest.json.",
                  "files": [{"path": str(path.relative_to(ev)), "bytes": path.stat().st_size,
                             "sha256": H.sha256_bytes(path.read_bytes())}
                            for path in sorted(ev.rglob("manifest.json"))]}
    H.write_json(ev / "manifest-supplement.json", supplement)
    manifest = H.write_tree_manifest(ev)
    print(json.dumps({"verdict": overall, "failed": failed, "subcases": verdicts,
                      "manifest": {"files": manifest["files"], "total_bytes": manifest["total_bytes"],
                                   "manifest_sha256": manifest["manifest_sha256"]}}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
