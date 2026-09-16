#!/usr/bin/env python3
"""Phase 2 / R3 — prepare preconditions and the duplicate gate are bypassable.

CLAIM  (a) `duplicate_check()` additionally requires the requested destination to equal a
       registry destination, so the same group+fingerprint aimed at a NEW destination is
       NOT_DUPLICATE; (b) `prepare()` only checks current_run_id/active_writer_id/context_lock,
       so a historical non-terminal run (INTENT_COMMITTED or dispatch_state UNKNOWN,
       workflow_outcome null) with cleared ownership does not block a new run at a new
       destination; (c) the same dates with a changed expected count are a different
       fingerprint and bypass the 57-image registry entry; (d) control: two ambiguous
       registry entries for the same group/fingerprint/destination are rejected
       (CONFLICT_DUPLICATE, exit 4); (e) the production entry (no --test-mode) accepts an
       isolated fabricated project root and persists calibration [1,1]/HIGH and
       source_provenance='test fixture' without any source observation.
ENTRY  Real product CLI subprocesses (`python3 -m line_backup_acceptance transaction ...`).
       Test-mode fixture roots only replace external I/O paths; no dispatcher is involved.
ORACLE Persisted state JSON (registry / intent / calibration / provenance), CLI result JSON,
       exit codes, pre/post state SHA-256. The side-effect surface here is persisted state.
DECIDE (a)(b)(c)(e) reproduced -> the production entry must reject these before any side
       effect; (d) must stay fail-closed after the fix.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (WORK, durable_copy_tree, program_hashes, read_json, run_product, sha256_file, write_json,
                     write_tree_manifest)

from fixtures import FP57, GROUP, make_run

CASE03 = Path("/private/tmp/line-backup-acceptance-case-03")
CASE04 = Path("/private/tmp/line-backup-acceptance-case-04")
CONFIG_KEYS = ["app_identifier", "backup_root", "group_key", "group_name", "max_albums_per_run", "max_wait_seconds",
               "poll_interval_seconds", "recovery_limit", "schema_version", "stable_samples"]


def tx_common(case_root: Path, state_path: Path) -> list[str]:
    return ["--project-root", str(case_root), "--state", str(state_path), "--test-mode"]


def duplicate_check_args(common: list[str], *, destination: Path, expected_images: int, evidence_dir: Path) -> list[str]:
    return ["transaction", "duplicate-check", *common, "--group-key", GROUP,
            "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
            "--expected-images", str(expected_images), "--destination", str(destination),
            "--evidence-dir", str(evidence_dir)]


def prepare_args(common: list[str], *, run_id: str, owner_id: str, destination: Path, evidence_dir: Path) -> list[str]:
    return ["transaction", "prepare", *common, "--run-id", run_id, "--owner-id", owner_id,
            "--group-key", GROUP, "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
            "--expected-images", str(FP57["expected_images"]), "--destination", str(destination),
            "--evidence-dir", str(evidence_dir)]


def make_case_root(case_root: Path, state: dict, *, extra_dirs: tuple[Path, ...] = ()) -> Path:
    """Rebuild a literal test-mode case root (state.json + destination dirs)."""
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    (case_root / "destination").mkdir()
    for directory in extra_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    state_path = case_root / "state.json"
    write_json(state_path, state)
    return state_path


def base_state(*, runs: list[dict] | None = None, entries: list[dict] | None = None, revision: int = 0) -> dict:
    return {"schema_version": 2, "revision": revision, "current_run_id": None, "active_writer_id": None,
            "context_lock": None, "runs": runs or [], "verified_albums": entries or []}


def registry_entry(destination: Path, verified_run_id: str) -> dict:
    return {"group_key": GROUP, "fingerprint": dict(FP57), "verified_run_id": verified_run_id,
            "destinations": [str(destination)], "source_kind": "filesystem_verification",
            "evidence": "fixture terminal registry entry"}


def terminal_run(run_id: str, owner: str, destination: Path) -> dict:
    return make_run(run_id, owner, str(destination), workflow_outcome="VERIFIED", phase="VERIFIED",
                    intent_state="SAVE_ALL_DISPATCH_ATTEMPTED", dispatch_state="SAVE_ALL_RETURNED",
                    dispatch_outcome="RETURNED", trigger_outcome="UNKNOWN")


def snapshot_state(state_path: Path, ev: Path, tag: str) -> dict:
    data = read_json(state_path)
    meta = write_json(ev / f"{tag}.json", data)
    return {"sha256": sha256_file(state_path), "bytes": state_path.stat().st_size, "durable": meta,
            "excerpt": state_excerpt(data)}


def state_excerpt(state: dict) -> dict:
    return {"revision": state.get("revision"), "current_run_id": state.get("current_run_id"),
            "active_writer_id": state.get("active_writer_id"), "run_count": len(state.get("runs") or []),
            "verified_album_count": len(state.get("verified_albums") or []),
            "runs": [{"run_id": run.get("run_id"), "workflow_outcome": run.get("workflow_outcome"),
                      "intent_state": run.get("intent_state"), "dispatch_state": run.get("dispatch_state"),
                      "owner_id": run.get("owner_id"), "destination": run.get("destination")}
                     for run in state.get("runs") or []]}


def do_run(ev: Path, name: str, args: list[str], *, timeout: float = 60) -> dict:
    result = run_product(ev / name, args, timeout=timeout)
    return {"name": name, "argv": result["argv"], "exit_code": result["exit_code"], "result": result["result"],
            "record_dir_relative_to_evidence": name}


def outcome(run: dict) -> tuple[int | None, str | None]:
    return run.get("exit_code"), (run.get("result") or {}).get("result")


def base_record(subcase: str, claim: str, entry: str, oracle: str, expected_current: str, expected_safe: str) -> dict:
    return {"subcase": subcase, "claim": claim, "entry": entry, "oracle": oracle,
            "expected_current_behavior": expected_current, "expected_safe_behavior": expected_safe,
            "program_hashes": program_hashes(), "dispatch": "none (prepare/duplicate-check never dispatch; no dispatcher passed)",
            "runs": {}}


def subcase_a(case_root: Path, ev: Path) -> dict:
    dest_a = case_root / "destination"
    dest_b = case_root / "destination-B"
    state = base_state(runs=[terminal_run("RUN-A-HIST", "WRITER-A", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-A-HIST")], revision=5)
    state_path = make_case_root(case_root, state, extra_dirs=(dest_b,))
    record = base_record(
        "a",
        "duplicate-check is bypassable by changing the destination: the registry gate requires an exact destination match, so the same group+fingerprint aimed at a new destination is NOT_DUPLICATE",
        "python3 -m line_backup_acceptance transaction duplicate-check (real CLI, test-mode fixture root)",
        "persisted registry entry (group+fp+destA) + CLI result JSON + exit codes; pre/post state SHA-256",
        "changed destination -> NOT_DUPLICATE exit 0 (bypass); same-destination control -> SKIP_DUPLICATE exit 0",
        "a terminal VERIFIED fingerprint in the group must gate regardless of destination; destination is part of the attempted run, not album identity",
    )
    record["pre_state"] = snapshot_state(state_path, ev, "a-pre-state")
    common = tx_common(case_root, state_path)
    record["runs"]["control_same_destination"] = do_run(
        ev, "a-control-same-destination",
        duplicate_check_args(common, destination=dest_a, expected_images=FP57["expected_images"],
                             evidence_dir=case_root / "evidence" / "a-control"))
    record["runs"]["changed_destination"] = do_run(
        ev, "a-changed-destination",
        duplicate_check_args(common, destination=dest_b, expected_images=FP57["expected_images"],
                             evidence_dir=case_root / "evidence" / "a-changed"))
    record["post_state"] = snapshot_state(state_path, ev, "a-post-state")
    record["state_mutated_by_duplicate_check"] = record["post_state"]["sha256"] != record["pre_state"]["sha256"]
    control = outcome(record["runs"]["control_same_destination"])
    probe = outcome(record["runs"]["changed_destination"])
    record["control_outcome"] = {"observed": list(control), "expected": [0, "SKIP_DUPLICATE"],
                                 "matches": control == (0, "SKIP_DUPLICATE")}
    if probe == (0, "NOT_DUPLICATE"):
        record["verdict"] = "REPRODUCED_DUPLICATE_CHECK_DESTINATION_BYPASS"
    elif probe[0] == 4:
        record["verdict"] = "NOT_REPRODUCED"
    elif probe[0] in (1, 2):
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
    else:
        record["verdict"] = "CONTRADICTED"
    record["durable_manifests"] = {"case_root": durable_copy_tree(case_root, ev / "a" / "case-root-durable")}
    return record


def subcase_b(case_root: Path, ev: Path) -> dict:
    record = base_record(
        "b",
        "prepare does not scan historical non-terminal runs: an unresolved intent (INTENT_COMMITTED or dispatch_state UNKNOWN, workflow_outcome null) with current_run_id/active_writer_id/context_lock null does not block a new run at a new destination",
        "python3 -m line_backup_acceptance transaction prepare (real CLI, test-mode fixture root)",
        "persisted state (new run/owner/revision vs untouched historical run) + CLI result JSON + exit codes",
        "both historical fixtures -> PREPARED exit 0 (bypass); active-run control -> CONFLICT_ACTIVE_RUN exit 4",
        "a new run must search all prior intents for the same group/fingerprint and treat unresolved ones as a blocking barrier until proven non-dispatch release",
    )
    dest_old_1 = case_root / "destination-old-1"
    state_path = make_case_root(
        case_root,
        base_state(runs=[make_run("RUN-B-HIST-INTENT", "WRITER-B0", str(dest_old_1), intent_state="INTENT_COMMITTED",
                                  dispatch_state="NOT_ATTEMPTED", phase="SAVE_ALL_INTENT_COMMITTED")], revision=7),
        extra_dirs=(dest_old_1,))
    record["probe1_pre_state"] = snapshot_state(state_path, ev, "b-probe1-pre-state")
    common = tx_common(case_root, state_path)
    record["runs"]["probe1_prepare_intent_committed"] = do_run(
        ev, "b-probe1-prepare",
        prepare_args(common, run_id="RUN-B01", owner_id="WRITER-B01", destination=case_root / "destination-new-1",
                     evidence_dir=case_root / "evidence" / "b-probe1"))
    post1 = snapshot_state(state_path, ev, "b-probe1-post-state")
    record["probe1_post_state_excerpt"] = post1["excerpt"]
    record["durable_manifests"] = {"probe1_case_root": durable_copy_tree(case_root, ev / "b" / "probe1-case-root-durable")}

    dest_old_2 = case_root / "destination-old-2"
    state_path = make_case_root(
        case_root,
        base_state(runs=[make_run("RUN-B-HIST-UNKNOWN", "WRITER-B0B", str(dest_old_2), intent_state="TRIGGER_UNKNOWN",
                                  dispatch_state="UNKNOWN", dispatch_outcome="UNKNOWN", trigger_outcome="UNKNOWN",
                                  phase="TRIGGER_UNKNOWN")], revision=7),
        extra_dirs=(dest_old_2,))
    record["probe2_pre_state"] = snapshot_state(state_path, ev, "b-probe2-pre-state")
    common = tx_common(case_root, state_path)
    record["runs"]["probe2_prepare_dispatch_unknown"] = do_run(
        ev, "b-probe2-prepare",
        prepare_args(common, run_id="RUN-B02", owner_id="WRITER-B02", destination=case_root / "destination-new-2",
                     evidence_dir=case_root / "evidence" / "b-probe2"))
    post2 = snapshot_state(state_path, ev, "b-probe2-post-state")
    record["probe2_post_state_excerpt"] = post2["excerpt"]
    record["runs"]["control_active_run_prepare"] = do_run(
        ev, "b-control-active-run",
        prepare_args(common, run_id="RUN-B03", owner_id="WRITER-B03", destination=case_root / "destination-new-3",
                     evidence_dir=case_root / "evidence" / "b-control"))
    control_post = snapshot_state(state_path, ev, "b-control-post-state")
    record["control_post_state_excerpt"] = control_post["excerpt"]
    record["control_state_unchanged"] = control_post["sha256"] == post2["sha256"]
    record["durable_manifests"]["probe2_case_root"] = durable_copy_tree(case_root, ev / "b" / "probe2-case-root-durable")

    probe1 = outcome(record["runs"]["probe1_prepare_intent_committed"])
    probe2 = outcome(record["runs"]["probe2_prepare_dispatch_unknown"])
    control = outcome(record["runs"]["control_active_run_prepare"])
    record["probe1_result_revision_field"] = (record["runs"]["probe1_prepare_intent_committed"]["result"] or {}).get("revision")
    record["probe1_persisted_revision"] = record["probe1_post_state_excerpt"]["revision"]
    record["control_outcome"] = {"observed": list(control), "expected": [4, "CONFLICT_ACTIVE_RUN"],
                                 "matches": control == (4, "CONFLICT_ACTIVE_RUN")}
    if probe1 == (0, "PREPARED") and probe2 == (0, "PREPARED"):
        record["verdict"] = "REPRODUCED_UNRESOLVED_INTENT_DOES_NOT_BLOCK_NEW_PREPARE"
    elif probe1[0] == 4 or probe2[0] == 4:
        record["verdict"] = "NOT_REPRODUCED"
    elif probe1[0] in (1, 2) or probe2[0] in (1, 2):
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
    else:
        record["verdict"] = "CONTRADICTED"
    return record


def subcase_c(case_root: Path, ev: Path) -> dict:
    dest_a = case_root / "destination"
    state = base_state(runs=[terminal_run("RUN-C-HIST", "WRITER-C", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-C-HIST")], revision=6)
    state_path = make_case_root(case_root, state)
    record = base_record(
        "c",
        "the fingerprint includes expected_images, so the same dates with a changed count (56 vs the registry 57) are NOT_DUPLICATE instead of a same-album reconciliation conflict",
        "python3 -m line_backup_acceptance transaction duplicate-check (real CLI, test-mode fixture root)",
        "persisted registry entry (2024-05-13..17, 57) + CLI result JSON + exit codes; pre/post state SHA-256",
        "expected-images 56 -> NOT_DUPLICATE exit 0 (bypass); expected-images 57 control -> SKIP_DUPLICATE exit 0",
        "a changed count for the same dates must trigger reconciliation against the historical fingerprint, not a silent new album",
    )
    record["pre_state"] = snapshot_state(state_path, ev, "c-pre-state")
    common = tx_common(case_root, state_path)
    record["runs"]["control_expected_57"] = do_run(
        ev, "c-control-expected-57",
        duplicate_check_args(common, destination=dest_a, expected_images=57, evidence_dir=case_root / "evidence" / "c-control"))
    record["runs"]["probe_expected_56"] = do_run(
        ev, "c-probe-expected-56",
        duplicate_check_args(common, destination=dest_a, expected_images=56, evidence_dir=case_root / "evidence" / "c-probe"))
    record["post_state"] = snapshot_state(state_path, ev, "c-post-state")
    record["state_mutated_by_duplicate_check"] = record["post_state"]["sha256"] != record["pre_state"]["sha256"]
    control = outcome(record["runs"]["control_expected_57"])
    probe = outcome(record["runs"]["probe_expected_56"])
    record["control_outcome"] = {"observed": list(control), "expected": [0, "SKIP_DUPLICATE"],
                                 "matches": control == (0, "SKIP_DUPLICATE")}
    if probe == (0, "NOT_DUPLICATE"):
        record["verdict"] = "REPRODUCED_SAME_DATE_COUNT_CHANGE_BYPASS"
    elif probe[0] == 4:
        record["verdict"] = "NOT_REPRODUCED"
    elif probe[0] in (1, 2):
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
    else:
        record["verdict"] = "CONTRADICTED"
    record["durable_manifests"] = {"case_root": durable_copy_tree(case_root, ev / "c" / "case-root-durable")}
    return record


def subcase_d(case_root: Path, ev: Path) -> dict:
    dest_a = case_root / "destination"
    state = base_state(runs=[terminal_run("RUN-D-HIST-1", "WRITER-D", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-D-HIST-1"), registry_entry(dest_a, "RUN-D-HIST-2")],
                       revision=6)
    state_path = make_case_root(case_root, state)
    record = base_record(
        "d",
        "control: two ambiguous registry entries for the same group/fingerprint/destination must fail closed (CONFLICT_DUPLICATE exit 4); current behaviour is already correct",
        "python3 -m line_backup_acceptance transaction duplicate-check (real CLI, test-mode fixture root)",
        "persisted ambiguous registry + CLI result JSON + exit code; pre/post state SHA-256",
        "ambiguous entries -> CONFLICT_DUPLICATE exit 4",
        "unchanged after the fix: ambiguous terminal associations keep failing closed",
    )
    record["pre_state"] = snapshot_state(state_path, ev, "d-pre-state")
    common = tx_common(case_root, state_path)
    record["runs"]["ambiguous_registry"] = do_run(
        ev, "d-ambiguous-registry",
        duplicate_check_args(common, destination=dest_a, expected_images=57, evidence_dir=case_root / "evidence" / "d-ambiguous"))
    record["post_state"] = snapshot_state(state_path, ev, "d-post-state")
    record["state_mutated_by_duplicate_check"] = record["post_state"]["sha256"] != record["pre_state"]["sha256"]
    probe = outcome(record["runs"]["ambiguous_registry"])
    record["control_outcome"] = {"observed": list(probe), "expected": [4, "CONFLICT_DUPLICATE"],
                                 "matches": probe == (4, "CONFLICT_DUPLICATE")}
    if probe == (4, "CONFLICT_DUPLICATE"):
        record["verdict"] = "NOT_REPRODUCED"
        record["verdict_note"] = "control only: no bypass; duplicate-check fails closed exactly as required"
    elif probe[0] in (1, 2):
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
    else:
        record["verdict"] = "CONTRADICTED"
    record["durable_manifests"] = {"case_root": durable_copy_tree(case_root, ev / "d" / "case-root-durable")}
    return record


def subcase_e(prod_case_root: Path, ev: Path) -> dict:
    prod_root = prod_case_root / "prod-root"
    if prod_case_root.exists():
        shutil.rmtree(prod_case_root)
    destination = prod_root / "backups" / "album-2024-05-13_to_2024-05-17_57"
    destination.mkdir(parents=True)
    (prod_root / "state").mkdir()
    config = {"schema_version": 2, "group_key": GROUP, "group_name": "旻謙允禎成長日記",
              "backup_root": str(prod_root / "backups"), "app_identifier": "jp.naver.line.mac",
              "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
              "stable_samples": 3, "max_wait_seconds": 120}
    write_json(prod_root / "config" / "line_backup_config.json", config)
    write_json(prod_root / "state" / "backup_state.json", base_state(revision=0))
    (prod_root / "state" / "run_log.md").write_text(
        "# run_log (isolated fake production root; human-readable projection only)\n", encoding="utf-8")
    record = base_record(
        "e",
        "the production entry (no --test-mode) accepts an isolated fabricated project root and persists a fixture calibration ([1,1], HIGH) plus source_provenance='test fixture' with no source observation",
        "python3 -m line_backup_acceptance transaction prepare (real CLI, NO --test-mode, isolated fake production root)",
        "persisted production state JSON (intent.calibration / source_provenance / observed_title) + CLI result JSON + exit code",
        "prepare -> PREPARED exit 0 with fabricated calibration/provenance persisted",
        "the production entry must reject fixture-derived content without a real source observation (or prove provenance); the real authority under /Users/hsiaojohnny/Documents/Codex is never touched",
    )
    record["production_root"] = str(prod_root)
    record["config_keys"] = sorted(config)
    record["config_keys_exact"] = sorted(config) == CONFIG_KEYS
    record["config_durable"] = write_json(ev / "e-prod-config.json", config)
    record["test_mode_flag_present"] = False
    state_path = prod_root / "state" / "backup_state.json"
    record["pre_state"] = snapshot_state(state_path, ev, "e-prod-pre-state")
    argv = ["transaction", "prepare",
            "--project-root", str(prod_root),
            "--config", str(prod_root / "config" / "line_backup_config.json"),
            "--run-log", str(prod_root / "state" / "run_log.md"),
            "--state", str(state_path),
            "--evidence-dir", str(prod_root / "evidence" / "prod-prepare"),
            "--run-id", "RUN-PROD-R3", "--owner-id", "WRITER-PROD-R3", "--group-key", GROUP,
            "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
            "--expected-images", str(FP57["expected_images"]), "--destination", str(destination)]
    record["runs"]["production_prepare_no_test_mode"] = do_run(ev, "e-production-prepare", argv)
    post = snapshot_state(state_path, ev, "e-prod-post-state")
    record["post_state"] = post
    record["post_state_excerpt"] = post["excerpt"]
    record["result_revision_field"] = (record["runs"]["production_prepare_no_test_mode"]["result"] or {}).get("revision")
    post_state_data = read_json(state_path)
    run0 = (post_state_data.get("runs") or [{}])[0]
    calibration = (run0.get("intent") or {}).get("calibration") or {}
    record["persisted_run_fields"] = {key: run0.get(key) for key in
                                      ("run_id", "group_key", "fingerprint", "observed_title", "title_confidence",
                                       "source_provenance", "destination", "destination_initially_empty",
                                       "intent_state", "dispatch_state", "workflow_outcome")}
    record["persisted_calibration"] = calibration
    record["fixture_fabrication_checks"] = {
        "calibration_ellipsis_equals_1_1": calibration.get("ellipsis") == [1, 1],
        "calibration_save_all_point_equals_1_1": calibration.get("save_all_point") == [1, 1],
        "calibration_confidence": calibration.get("confidence"),
        "source_provenance": run0.get("source_provenance"),
        "source_observation_note": "no GUI/source adapter ran; the persisted content comes from _base_run() constants",
    }
    probe = outcome(record["runs"]["production_prepare_no_test_mode"])
    if (probe == (0, "PREPARED") and calibration.get("ellipsis") == [1, 1]
            and calibration.get("confidence") == "HIGH" and run0.get("source_provenance") == "test fixture"):
        record["verdict"] = "REPRODUCED_PRODUCTION_ACCEPTS_FIXTURE_INTENT"
    elif probe[0] in (4,):
        record["verdict"] = "NOT_REPRODUCED"
    elif probe[0] in (1, 2):
        record["verdict"] = "NOT_REPRODUCED"
        record["verdict_note"] = "production entry rejected the fabricated root (fail-closed); claim not reproduced"
    else:
        record["verdict"] = "CONTRADICTED"
    record["durable_manifests"] = {"case_root": durable_copy_tree(prod_case_root, ev / "e" / "case-root-durable")}
    return record


def overall_verdict(subcases: list[dict]) -> str:
    by_letter = {subcase["subcase"]: subcase["verdict"] for subcase in subcases}
    expected = {"a": "REPRODUCED_DUPLICATE_CHECK_DESTINATION_BYPASS",
                "b": "REPRODUCED_UNRESOLVED_INTENT_DOES_NOT_BLOCK_NEW_PREPARE",
                "c": "REPRODUCED_SAME_DATE_COUNT_CHANGE_BYPASS",
                "e": "REPRODUCED_PRODUCTION_ACCEPTS_FIXTURE_INTENT"}
    hits = [letter for letter, verdict in expected.items() if by_letter.get(letter) == verdict]
    control_ok = by_letter.get("d") == "NOT_REPRODUCED"
    if len(hits) == len(expected) and control_ok:
        return "REPRODUCED_R3_PRECONDITION_GAPS"
    if not hits:
        return "NOT_REPRODUCED"
    return "REPRODUCED_R3_PARTIAL"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    ns = parser.parse_args()
    case_root = Path(ns.case_root)
    if case_root not in {CASE03, CASE04}:
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"case root must be one of the literal roots {CASE03}, {CASE04}"}, ensure_ascii=False))
        return 1
    ev = Path(ns.evidence_dir)
    if not ev.is_absolute():
        ev = WORK / ev
    if "phase2-r3" not in ev.parts:
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": "evidence dir must be the dedicated phase2-r3 attempt directory"}, ensure_ascii=False))
        return 1
    prod_case_root = CASE04
    if ev.exists():
        shutil.rmtree(ev)
    ev.mkdir(parents=True)

    observation = {
        "claim": ("R3: transaction prepare lacks precondition checks and the duplicate gate is bypassable by "
                  "destination change, by historical unresolved intent, and by same-date count change; the "
                  "production entry (no --test-mode) accepts a fabricated root and persists fixture calibration "
                  "with no source observation"),
        "entry": ("real product CLI subprocesses (`python3 -m line_backup_acceptance transaction prepare|duplicate-check`); "
                  "test-mode fixture roots replace external I/O paths only"),
        "oracle": ("persisted state JSON (registry / intent / calibration / source_provenance), CLI result JSON and "
                   "exit codes, pre/post state SHA-256; no dispatcher is involved, so persisted state is the "
                   "side-effect surface"),
        "decision": ("(a)(b)(c)(e) reproduced -> keep GUI/production dispatch blocked; Phase 4 must add pre-side-effect "
                     "checks (history-wide unresolved-intent scan, destination-independent duplicate/fingerprint "
                     "barrier, same-date count change as reconciliation, production rejection of fixture-derived "
                     "calibration/provenance). (d) must stay fail-closed (CONFLICT_DUPLICATE/exit 4) after the fix."),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "work": str(WORK),
        "case_roots": {"test_mode": str(case_root), "production_fake_root": str(CASE04 / "prod-root")},
        "program_hashes": program_hashes(),
        "independent_side_effect_surface": ("no dispatcher is invoked by prepare/duplicate-check; the independent "
                                            "oracle is the persisted state file plus CLI exit codes"),
    }
    subcases = [subcase_a(case_root, ev), subcase_b(case_root, ev), subcase_c(case_root, ev), subcase_d(case_root, ev),
                subcase_e(prod_case_root, ev)]
    observation["subcases"] = subcases
    observation["verdict"] = overall_verdict(subcases)
    write_json(ev / "observation.json", observation)
    write_tree_manifest(ev)
    summary = {"verdict": observation["verdict"],
               "subcases": {subcase["subcase"]: subcase["verdict"] for subcase in subcases},
               "evidence_dir": str(ev)}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
