#!/usr/bin/env python3
"""Phase 2 / R3 — prepare preconditions and the duplicate gate must refuse at the real entry.

CLAIM (Rev14, reproduced pre-fix in attempt-01)
  (a) duplicate-check additionally required the requested destination to equal the registry
      destination, so the same group+fingerprint aimed at a NEW destination was NOT_DUPLICATE;
  (b) prepare only checked current_run_id/active_writer_id/context_lock, so a historical
      non-terminal run (INTENT_COMMITTED or dispatch UNKNOWN, cleared ownership) did not block
      a new run;
  (c) the same dates with a changed expected count were a different fingerprint and bypassed
      the 57-image registry entry;
  (d) control: two ambiguous entries were rejected (CONFLICT_DUPLICATE, exit 4);
  (e) the production entry (no --test-mode) accepted an isolated fabricated root and persisted
      a fixture calibration ([1,1]/HIGH) plus source_provenance='test fixture' with no source
      observation.
ENTRY  Real product CLI subprocesses (`transaction prepare|duplicate-check`).  Test-mode fixture
       roots replace external I/O paths only; no dispatcher side effect occurs on any refusal.
ORACLE Persisted state JSON (registry/intent/calibration), CLI result JSON, exit codes, pre/post
       state SHA-256, and the independent dispatch counter.
DECIDE Post-fix (this run) every reproduced bypass must be refused before any side effect:
       (a) destination change -> CONFLICT_DUPLICATE_FINGERPRINT, (b) historical unresolved intent
       -> NEEDS_RECONCILIATION, (c) count change -> AMBIGUOUS_FINGERPRINT, (d) stays
       CONFLICT_DUPLICATE, (e) the production entry refuses fixture-derived content
       (MISSING_SOURCE_EVIDENCE / INVALID_SOURCE_EVIDENCE) with zero writes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r3-preconditions"
GROUP = F.GROUP
FP57 = F.FP57
CASE03 = Path("/private/tmp/line-backup-acceptance-case-03")
CASE04 = Path("/private/tmp/line-backup-acceptance-case-04")
ATTEMPT_01 = H.WORK / "evidence/20260916-auto-verification/attempt-01/phase2-r3"
PRE_FIX = {
    "verdict": "REPRODUCED_PRECONDITION_GAPS",
    "observation": ("destination change bypassed duplicate-check (NOT_DUPLICATE); a historical unresolved intent did "
                    "not block prepare; count change 57->56 bypassed; an isolated production-shaped root accepted "
                    "prepare without --test-mode and persisted calibration [1,1], confidence=HIGH, "
                    "source_provenance='test fixture'; the two-entry ambiguity control already returned "
                    "CONFLICT_DUPLICATE"),
    "evidence": str(ATTEMPT_01 / "observation.json"),
}


def sha(path: Path) -> str:
    return H.sha256_file(Path(path))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def registry_entry(destination: Path, verified_run_id: str) -> dict:
    return {"group_key": GROUP, "fingerprint": dict(FP57), "verified_run_id": verified_run_id,
            "destinations": [str(destination)], "source_kind": "filesystem_verification",
            "evidence": "fixture terminal registry entry"}


def terminal_run(run_id: str, owner: str, destination: Path) -> dict:
    run = F.completed_dispatch_run(run_id, owner, str(destination))
    run["workflow_outcome"] = "VERIFIED"
    run["phase"] = "VERIFIED"
    return run


def base_state(*, runs: list[dict] | None = None, entries: list[dict] | None = None, revision: int = 0) -> dict:
    state = F.fresh_state(revision=revision)
    state["runs"] = runs or []
    state["verified_albums"] = entries or []
    return state


def canonical_case_root(root: Path, state: dict, *, extra_dirs: tuple[str, ...] = ()) -> dict:
    paths = F.write_canonical_root(root, state, destination_images=0)
    for name in extra_dirs:
        (root / name).mkdir(parents=True, exist_ok=True)
    paths["source_evidence"] = F.source_evidence_record(root, name="source-evidence.json")["path"]
    paths["counter"] = root / "dispatch-counter.jsonl"
    paths["counter"].touch()
    paths["dispatcher"] = H.write_dispatcher(root / "dispatcher.py", block_seconds=0.0)
    return paths


def check_args(paths: dict, *, destination: Path, expected_images: int) -> list[str]:
    return ["transaction", "duplicate-check", "--project-root", str(paths["case_root"]),
            "--config", str(paths["config"]), "--run-log", str(paths["run_log"]), "--state", str(paths["state"]),
            "--test-mode", "--group-key", GROUP, "--start-date", FP57["start_date"],
            "--end-date", FP57["end_date"], "--expected-images", str(expected_images),
            "--destination", str(destination), "--evidence-dir", str(Path(paths["case_root"]) / "evidence" / "duplicate")]


def prepare_args(paths: dict, *, run_id: str, owner: str, destination: Path) -> list[str]:
    return ["transaction", "prepare", "--project-root", str(paths["case_root"]),
            "--config", str(paths["config"]), "--run-log", str(paths["run_log"]), "--state", str(paths["state"]),
            "--test-mode", "--run-id", run_id, "--owner-id", owner, "--group-key", GROUP,
            "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
            "--expected-images", str(FP57["expected_images"]), "--destination", str(destination),
            "--source-evidence", str(paths["source_evidence"]), "--dispatcher", str(paths["dispatcher"]),
            "--dispatch-counter", str(paths["counter"]),
            "--evidence-dir", str(Path(paths["case_root"]) / "evidence" / "prepare")]


def counter_lines(paths: dict) -> int:
    return len(H.counter_entries(paths["counter"]))


def run_case(ev: Path, name: str, args: list[str], *, timeout: float = 60.0) -> dict:
    rec = H.run_product(ev / name, args, timeout=timeout)
    return {"name": name, "argv": rec["argv"], "exit_code": rec["exit_code"], "result": rec["result"]}


def subcase_a(root: Path, ev: Path) -> dict:
    dest_a, dest_b = root / "destination", root / "destination-B"
    state = base_state(runs=[terminal_run("RUN-A-HIST", "WRITER-A", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-A-HIST")], revision=5)
    paths = canonical_case_root(root, state, extra_dirs=("destination-B",))
    pre = sha(paths["state"])
    control = run_case(ev, "a-control-same-destination", check_args(paths, destination=dest_a, expected_images=57))
    probe = run_case(ev, "a-changed-destination", check_args(paths, destination=dest_b, expected_images=57))
    post = sha(paths["state"])
    checks = {
        "control.skip-duplicate": (control["exit_code"], (control["result"] or {}).get("result")) == (0, "SKIP_DUPLICATE"),
        "probe.conflict-fingerprint": (probe["exit_code"], (probe["result"] or {}).get("result")) ==
                                      (4, "CONFLICT_DUPLICATE_FINGERPRINT"),
        "no-state-mutation": pre == post,
    }
    return {"subcase": "a", "claim": "a destination change must not bypass the fingerprint gate",
            "entry": "real CLI transaction duplicate-check (test-mode fixture root)",
            "oracle": "registry entry + CLI result JSON + exit codes + pre/post state SHA-256",
            "expected_safe_behavior": ("changed destination -> CONFLICT_DUPLICATE_FINGERPRINT exit 4; same-destination "
                                       "control -> SKIP_DUPLICATE exit 0; no state mutation"),
            "control": control, "probe": probe, "pre_state_sha256": pre, "post_state_sha256": post,
            "checks": checks, "verdict": "SAFE_DESTINATION_CHANGE_REFUSED" if all(checks.values()) else
                                          "REGRESSION_OR_UNEXPECTED"}


def subcase_b(root: Path, ev: Path) -> dict:
    dest_old = root / "destination-old"
    state = base_state(runs=[F.make_run("RUN-B-HIST-INTENT", "WRITER-B0", str(dest_old))], revision=7)
    paths = canonical_case_root(root, state, extra_dirs=("destination-old", "destination-new"))
    pre1 = sha(paths["state"])
    probe1 = run_case(ev, "b-probe1-intent-committed", prepare_args(paths, run_id="RUN-B01", owner="WRITER-B01",
                                                                     destination=root / "destination-new"))
    post1 = sha(paths["state"])
    checks = {
        "intent-committed.needs-reconciliation": (probe1["exit_code"], (probe1["result"] or {}).get("result")) ==
                                                 (4, "NEEDS_RECONCILIATION"),
        "intent-committed.no-state-write": pre1 == post1,
        "intent-committed.no-dispatch": counter_lines(paths) == 0,
    }

    state2 = base_state(runs=[F.make_run("RUN-B-HIST-UNKNOWN", "WRITER-B0B", str(root / "destination-old"),
                                         workflow_outcome="SAFE_ABORT", phase="SAFE_ABORT",
                                         intent_state="SAVE_ALL_DISPATCH_ATTEMPTED", dispatch_state="UNKNOWN",
                                         dispatch_outcome="UNKNOWN", trigger_outcome="UNKNOWN",
                                         manual_reconciliation_required=True,
                                         reconciliation_reason="dispatch outcome unresolved")], revision=8)
    paths2 = canonical_case_root(root, state2, extra_dirs=("destination-old", "destination-new"))
    pre2 = sha(paths2["state"])
    probe2 = run_case(ev, "b-probe2-dispatch-unknown", prepare_args(paths2, run_id="RUN-B02", owner="WRITER-B02",
                                                                    destination=root / "destination-new"))
    post2 = sha(paths2["state"])
    checks.update({
        "dispatch-unknown.needs-reconciliation": (probe2["exit_code"], (probe2["result"] or {}).get("result")) ==
                                                 (4, "NEEDS_RECONCILIATION"),
        "dispatch-unknown.no-state-write": pre2 == post2,
        "dispatch-unknown.no-dispatch": counter_lines(paths2) == 0,
    })

    state3 = base_state(runs=[F.make_run("RUN-B-HIST-ACTIVE", "WRITER-B0C", str(root / "destination-old"))], revision=9)
    state3["current_run_id"] = "RUN-B-HIST-ACTIVE"
    state3["active_writer_id"] = "WRITER-B0C"
    paths3 = canonical_case_root(root, state3, extra_dirs=("destination-old", "destination-new"))
    control = run_case(ev, "b-control-active-run", prepare_args(paths3, run_id="RUN-B03", owner="WRITER-B03",
                                                                destination=root / "destination-new"))
    checks["active-run.control"] = (control["exit_code"], (control["result"] or {}).get("result")) == \
                                   (4, "CONFLICT_ACTIVE_RUN")
    return {"subcase": "b", "claim": "a historical unresolved intent must block a new prepare until reconciled",
            "entry": "real CLI transaction prepare (test-mode fixture root)",
            "oracle": "persisted state SHA-256 pre/post + CLI result JSON + exit codes + counter",
            "expected_safe_behavior": ("historical INTENT_COMMITTED and unresolved SAFE_ABORT both -> "
                                       "NEEDS_RECONCILIATION exit 4 with no write and no dispatch; active-run control "
                                       "-> CONFLICT_ACTIVE_RUN exit 4"),
            "probe1": probe1, "probe2": probe2, "control": control, "checks": checks,
            "verdict": "SAFE_UNRESOLVED_INTENT_BLOCKS_PREPARE" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"}


def subcase_c(root: Path, ev: Path) -> dict:
    dest_a = root / "destination"
    state = base_state(runs=[terminal_run("RUN-C-HIST", "WRITER-C", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-C-HIST")], revision=6)
    paths = canonical_case_root(root, state)
    pre = sha(paths["state"])
    control = run_case(ev, "c-control-expected-57", check_args(paths, destination=dest_a, expected_images=57))
    probe = run_case(ev, "c-probe-expected-56", check_args(paths, destination=dest_a, expected_images=56))
    post = sha(paths["state"])
    checks = {
        "control.skip-duplicate": (control["exit_code"], (control["result"] or {}).get("result")) == (0, "SKIP_DUPLICATE"),
        "probe.ambiguous-fingerprint": (probe["exit_code"], (probe["result"] or {}).get("result")) ==
                                       (4, "AMBIGUOUS_FINGERPRINT"),
        "no-state-mutation": pre == post,
    }
    return {"subcase": "c", "claim": "a same-date count change must be a reconciliation conflict, not a silent new album",
            "entry": "real CLI transaction duplicate-check (test-mode fixture root)",
            "oracle": "registry entry + CLI result JSON + exit codes + pre/post state SHA-256",
            "expected_safe_behavior": ("expected-images 56 -> AMBIGUOUS_FINGERPRINT exit 4; expected-images 57 "
                                       "control -> SKIP_DUPLICATE exit 0; no state mutation"),
            "control": control, "probe": probe, "checks": checks,
            "verdict": "SAFE_COUNT_CHANGE_REFUSED" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"}


def subcase_d(root: Path, ev: Path) -> dict:
    dest_a = root / "destination"
    state = base_state(runs=[terminal_run("RUN-D-HIST-1", "WRITER-D", dest_a)],
                       entries=[registry_entry(dest_a, "RUN-D-HIST-1"), registry_entry(dest_a, "RUN-D-HIST-2")],
                       revision=6)
    paths = canonical_case_root(root, state)
    pre = sha(paths["state"])
    probe = run_case(ev, "d-ambiguous-registry", check_args(paths, destination=dest_a, expected_images=57))
    post = sha(paths["state"])
    checks = {
        "control.conflict-duplicate": (probe["exit_code"], (probe["result"] or {}).get("result")) ==
                                      (4, "CONFLICT_DUPLICATE"),
        "no-state-mutation": pre == post,
    }
    return {"subcase": "d", "claim": "the two-entry ambiguity control keeps failing closed",
            "entry": "real CLI transaction duplicate-check (test-mode fixture root)",
            "oracle": "ambiguous registry + CLI result JSON + exit codes + pre/post state SHA-256",
            "expected_safe_behavior": "ambiguous entries -> CONFLICT_DUPLICATE exit 4, no write",
            "probe": probe, "checks": checks,
            "verdict": "SAFE_AMBIGUITY_FAILS_CLOSED" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"}


def subcase_e(root: Path, ev: Path) -> dict:
    prod_root = root / "prod-root"
    H.ensure_owned_root(root, DRIVER_ID)
    H.reset_owned_content(root)
    destination = prod_root / "backups" / "album-2024-05-13_to_2024-05-17_57"
    destination.mkdir(parents=True)
    (prod_root / "state").mkdir(parents=True)
    config = {"schema_version": 2, "group_key": GROUP, "group_name": F.GROUP_NAME,
              "backup_root": str(prod_root / "backups"), "app_identifier": "jp.naver.line.mac",
              "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
              "stable_samples": 3, "max_wait_seconds": 120}
    H.write_json(prod_root / "config" / "line_backup_config.json", config)
    H.write_json(prod_root / "state" / "backup_state.json", base_state(revision=0))
    (prod_root / "state" / "run_log.md").write_text("# run_log (isolated fake production root)\n", encoding="utf-8")
    state_path = prod_root / "state" / "backup_state.json"
    dispatcher = H.write_dispatcher(prod_root / "dispatcher.py", block_seconds=0.0)
    counter = prod_root / "dispatch-counter.jsonl"
    counter.touch()
    state_before = state_path.read_bytes()

    base = ["transaction", "prepare", "--project-root", str(prod_root),
            "--config", str(prod_root / "config" / "line_backup_config.json"),
            "--run-log", str(prod_root / "state" / "run_log.md"), "--state", str(state_path),
            "--run-id", "RUN-PROD-R3", "--owner-id", "WRITER-PROD-R3", "--group-key", GROUP,
            "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
            "--expected-images", str(FP57["expected_images"]), "--destination", str(destination),
            "--dispatcher", str(dispatcher), "--dispatch-counter", str(counter),
            "--evidence-dir", str(prod_root / "evidence" / "prod-prepare")]
    e1 = run_case(ev, "e1-production-prepare-no-source-evidence", base)
    state_after_e1 = state_path.read_bytes()
    fixture_record = F.source_evidence_record(prod_root, name="fixture-source-evidence.json", test_mode=True,
                                              binding_kind="fixture")
    e2 = run_case(ev, "e2-production-prepare-fixture-record",
                  base + ["--source-evidence", str(fixture_record["path"])])
    state_after_e2 = state_path.read_bytes()
    state_data = read_json(state_path)
    checks = {
        "e1.missing-source-evidence": (e1["exit_code"], (e1["result"] or {}).get("result")) ==
                                      (2, "MISSING_SOURCE_EVIDENCE"),
        "e1.no-state-write": state_after_e1 == state_before,
        "e2.invalid-source-evidence": (e2["exit_code"], (e2["result"] or {}).get("failure_class")) ==
                                      (2, "INVALID_SOURCE_EVIDENCE"),
        "e2.no-state-write": state_after_e2 == state_before,
        "no-run-persisted": state_data.get("runs") == [],
        "no-fabricated-calibration": "calibration" not in json.dumps(state_data),
        "zero-dispatch": len(H.counter_entries(counter)) == 0,
        "revision-unchanged": state_data.get("revision") == 0,
    }
    return {"subcase": "e", "claim": "the production entry (no --test-mode) must refuse fixture-derived content",
            "entry": "real CLI transaction prepare (NO --test-mode, isolated fake production root)",
            "oracle": "persisted production state bytes + CLI result JSON + exit code + counter",
            "expected_safe_behavior": ("missing --source-evidence -> MISSING_SOURCE_EVIDENCE exit 2; a test-mode "
                                       "fixture record -> INVALID_SOURCE_EVIDENCE exit 2; zero writes, zero dispatch"),
            "production_root": str(prod_root),
            "e1": e1, "e2": e2, "checks": checks,
            "verdict": "SAFE_PRODUCTION_REFUSES_FIXTURE_CONTENT" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(CASE03))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    if case_root.resolve() != CASE03.resolve():
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"R3 is bound to its literal case root {CASE03}"}, ensure_ascii=False))
        return 1
    ev.mkdir(parents=True, exist_ok=True)
    H.ensure_owned_root(case_root, DRIVER_ID)
    H.reset_owned_content(case_root)

    observation = {
        "driver": DRIVER_ID,
        "claim": ("pre-fix: the duplicate gate was bypassable by destination change and same-date count change, a "
                  "historical unresolved intent did not block prepare, and the production entry accepted "
                  "fixture-derived content; post-fix: every bypass is refused before any side effect"),
        "entry": "real product CLI subprocesses (`transaction prepare|duplicate-check`)",
        "oracle": "persisted state JSON + CLI result JSON + exit codes + pre/post state SHA-256 + counter",
        "pre_fix": PRE_FIX,
        "program_hashes": H.program_hashes(),
        "case_roots": {"test_mode": str(case_root), "production_fake_root": str(CASE04 / "prod-root")},
    }
    subcases = [subcase_a(case_root, ev), subcase_b(case_root, ev), subcase_c(case_root, ev), subcase_d(case_root, ev),
                subcase_e(CASE04, ev)]
    observation["subcases"] = subcases
    observation["checks"] = {f"{s['subcase']}.{k}": v for s in subcases for k, v in s["checks"].items()}
    all_safe = all(v for v in observation["checks"].values())
    observation["verdict"] = "SAFE_R3_PRECONDITION_REFUSALS" if all_safe else "REGRESSION_OR_UNEXPECTED"
    observation["subcase_verdicts"] = {s["subcase"]: s["verdict"] for s in subcases}
    H.write_json(ev / "observation.json", observation)
    for root in (case_root, CASE04):
        durable = ev / "case-root-durable" / root.name
        H.durable_copy_tree(root, durable)
    H.write_tree_manifest(ev)
    print(json.dumps({"verdict": observation["verdict"],
                      "failed": [k for k, v in observation["checks"].items() if not v],
                      "subcases": observation["subcase_verdicts"]}, ensure_ascii=False))
    return 0 if all_safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
