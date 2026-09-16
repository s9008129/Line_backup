#!/usr/bin/env python3
"""Phase 2 / R2 — a fresh process must never dispatch a loaded intent.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  `prepare` committed INTENT_COMMITTED and exited;
       a *different*, fresh process could then call `resume` and perform the Save-All dispatch
       because continuity was assumed from persisted fields; safety depended on the caller
       passing --no-dispatch.
ENTRY  Real CLI `transaction prepare` (process A, the single in-process dispatch window) then
       fresh-process `transaction resume` variants (process B).
ORACLE Independent dispatcher counter jsonl + persisted intent/dispatch fields + exit codes +
       state bytes before/after each step.
DECIDE Post-fix (this run) continuity must not depend on a caller flag: prepare owns exactly one
       dispatch, every fresh resume is reconciliation-only, adapter options are refused with
       INVALID_INPUT before any state read, and a completed dispatch record is a no-op resume.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r2-loaded-intent"
GROUP = F.GROUP
FP = F.FP57
CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-02")
ATTEMPT_01 = H.WORK / "evidence/20260916-auto-verification/attempt-01/phase2-r2"
PRE_FIX = {
    "verdict": "REPRODUCED_FRESH_PROCESS_DISPATCH",
    "observation": ("prepare (process A) then fresh-process resume (process B) dispatched once; the same fixture "
                    "with --no-dispatch performed no dispatch: safety depended on the caller's flag"),
    "evidence": str(ATTEMPT_01 / "observation.json"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def counter_lines(counter: Path) -> int:
    return len(H.counter_entries(counter))


def build_fixture(root: Path, *, destination_name: str) -> dict:
    paths = F.write_canonical_root(root, F.fresh_state(), destination_name=destination_name)
    paths["source_evidence"] = F.source_evidence_record(root, name="source-evidence.json")["path"]
    paths["counter"] = root / "dispatch-counter.jsonl"
    paths["counter"].touch()
    paths["dispatcher"] = H.write_dispatcher(root / "dispatcher.py", block_seconds=0.0)
    return paths


def prepare_args(paths: dict, run_id: str, owner: str) -> list[str]:
    root = Path(paths["case_root"])
    return ["transaction", "prepare", "--project-root", str(root), "--config", str(paths["config"]),
            "--run-log", str(paths["run_log"]), "--state", str(paths["state"]), "--test-mode",
            "--run-id", run_id, "--owner-id", owner, "--group-key", GROUP,
            "--start-date", FP["start_date"], "--end-date", FP["end_date"],
            "--expected-images", str(FP["expected_images"]), "--destination", str(paths["destination"]),
            "--source-evidence", str(paths["source_evidence"]), "--dispatcher", str(paths["dispatcher"]),
            "--dispatch-counter", str(paths["counter"]), "--evidence-dir", str(root / "evidence" / "prepare")]


def resume_args(paths: dict, run_id: str, owner: str, revision: int, *extra: str) -> list[str]:
    root = Path(paths["case_root"])
    return ["transaction", "resume", "--project-root", str(root), "--config", str(paths["config"]),
            "--run-log", str(paths["run_log"]), "--state", str(paths["state"]), "--test-mode",
            "--run-id", run_id, "--expected-revision", str(revision), "--expected-owner-id", owner,
            "--evidence-dir", str(root / "evidence" / "resume"), *extra]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    if case_root.resolve() != CASE_ROOT.resolve():
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"R2 is bound to its literal case root {CASE_ROOT}"}, ensure_ascii=False))
        return 1
    ev.mkdir(parents=True, exist_ok=True)
    H.ensure_owned_root(case_root, DRIVER_ID)
    H.reset_owned_content(case_root)

    record = {"driver": DRIVER_ID,
              "claim": ("pre-fix: a fresh process could dispatch a loaded intent (flag-dependent safety); "
                        "post-fix: prepare owns the single dispatch and every fresh resume is reconciliation-only"),
              "entry": "real CLI transaction prepare then transaction resume (separate processes)",
              "oracle": "independent dispatcher counter jsonl + persisted intent/dispatch fields + exit codes "
                        "+ state bytes before/after",
              "pre_fix": PRE_FIX, "case_root": str(case_root), "program_hashes": H.program_hashes()}
    checks: dict[str, bool] = {}

    # --- probe A: prepare (process A) performs exactly one dispatch -------------------------
    paths = build_fixture(case_root, destination_name="destination")
    prepare = H.run_product(ev / "prepare", prepare_args(paths, "RUN-R2", "WRITER-R2"), timeout=60)
    prepare_result = prepare["result"] or {}
    state_after_prepare = read_json(paths["state"])
    run0 = state_after_prepare["runs"][0]
    record["probe_a_prepare"] = {"exit_code": prepare["exit_code"], "result": prepare_result,
                                 "revision": state_after_prepare.get("revision"),
                                 "intent_state": run0.get("intent_state"),
                                 "dispatch_state": run0.get("dispatch_state"),
                                 "counter_lines": counter_lines(paths["counter"]),
                                 "argv": prepare["argv"]}
    checks["prepare.prepared"] = prepare_result.get("result") == "PREPARED" and prepare["exit_code"] == 0
    checks["prepare.dispatch-performed"] = prepare_result.get("dispatch_performed") is True
    checks["prepare.revision2"] = state_after_prepare.get("revision") == 2
    checks["prepare.record-complete"] = (run0.get("intent_state") == "SAVE_ALL_DISPATCH_ATTEMPTED"
                                         and run0.get("dispatch_state") == "SAVE_ALL_RETURNED")
    checks["prepare.counter-1"] = counter_lines(paths["counter"]) == 1

    # --- probe B: fresh-process resume WITH adapter flags must refuse before any state read --
    state_before_b = Path(paths["state"]).read_bytes()
    resume_b = H.run_product(ev / "fresh-resume-with-adapter", resume_args(paths, "RUN-R2", "WRITER-R2", 2,
                                                                           "--dispatcher", str(paths["dispatcher"]),
                                                                           "--dispatch-counter", str(paths["counter"])),
                             timeout=60)
    result_b = resume_b["result"] or {}
    record["probe_b_resume_with_adapter"] = {"exit_code": resume_b["exit_code"], "result": result_b,
                                             "argv": resume_b["argv"],
                                             "state_unchanged": Path(paths["state"]).read_bytes() == state_before_b,
                                             "counter_lines": counter_lines(paths["counter"])}
    checks["resume-with-adapter.invalid-input"] = (result_b.get("result") == "INVALID_INPUT"
                                                   and resume_b["exit_code"] == 2)
    checks["resume-with-adapter.no-dispatch"] = counter_lines(paths["counter"]) == 1
    checks["resume-with-adapter.no-state-read"] = Path(paths["state"]).read_bytes() == state_before_b

    # --- probe C: fresh resume --no-dispatch over the completed dispatch record is a no-op ----
    resume_c = H.run_product(ev / "fresh-resume-no-dispatch",
                             resume_args(paths, "RUN-R2", "WRITER-R2", 2, "--no-dispatch"), timeout=60)
    result_c = resume_c["result"] or {}
    record["probe_c_resume_no_dispatch"] = {"exit_code": resume_c["exit_code"], "result": result_c,
                                            "counter_lines": counter_lines(paths["counter"])}
    checks["resume-no-dispatch.exit0"] = resume_c["exit_code"] == 0
    checks["resume-no-dispatch.code"] = result_c.get("result") == "RECOVERY_NO_DISPATCH"
    checks["resume-no-dispatch.no-dispatch"] = result_c.get("dispatch_performed") is False
    checks["resume-no-dispatch.no-write"] = result_c.get("state_replaced") is False
    checks["resume-no-dispatch.counter-1"] = counter_lines(paths["counter"]) == 1

    # --- probe D: a loaded never-dispatched intent is barrier-only, never dispatch ------------
    H.reset_owned_content(case_root)
    paths_d = build_fixture(case_root, destination_name="destination-d")
    loaded = F.make_run("RUN-R2-D", "WRITER-R2-D", str(paths_d["destination"]))
    F.install_state(Path(paths_d["case_root"]), {"schema_version": 2, "revision": 1, "current_run_id": "RUN-R2-D",
                                                 "active_writer_id": "WRITER-R2-D", "context_lock": None,
                                                 "runs": [loaded], "verified_albums": []})
    resume_d = H.run_product(ev / "fresh-resume-loaded-intent",
                             resume_args(paths_d, "RUN-R2-D", "WRITER-R2-D", 1), timeout=60)
    result_d = resume_d["result"] or {}
    state_after_d = read_json(paths_d["state"])
    run_d = state_after_d["runs"][0]
    record["probe_d_loaded_intent"] = {"exit_code": resume_d["exit_code"], "result": result_d,
                                       "revision": state_after_d.get("revision"),
                                       "intent_state": run_d.get("intent_state"),
                                       "dispatch_state": run_d.get("dispatch_state"),
                                       "manual_reconciliation_required": run_d.get("manual_reconciliation_required"),
                                       "counter_lines": counter_lines(paths_d["counter"])}
    checks["loaded-intent.recovery-code"] = result_d.get("result") == "RECOVERY_NO_DISPATCH"
    checks["loaded-intent.exit0"] = resume_d["exit_code"] == 0
    checks["loaded-intent.barrier"] = result_d.get("reconciliation_state") == "BARRIER_COMMITTED"
    checks["loaded-intent.no-dispatch"] = result_d.get("dispatch_performed") is False
    checks["loaded-intent.unknown-barrier"] = (run_d.get("intent_state") == "TRIGGER_UNKNOWN"
                                               and run_d.get("dispatch_state") == "UNKNOWN"
                                               and run_d.get("manual_reconciliation_required") is True)
    checks["loaded-intent.revision2"] = state_after_d.get("revision") == 2
    checks["loaded-intent.counter-0"] = counter_lines(paths_d["counter"]) == 0
    checks["loaded-intent.reconciliations"] = len(run_d.get("reconciliations") or []) == 1

    record["checks"] = checks
    record["verdict"] = "SAFE_FRESH_PROCESS_NEVER_DISPATCHES" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"
    H.write_json(ev / "observation.json", record)
    H.durable_copy_tree(case_root, ev / "case-root-durable")
    H.write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "failed": [k for k, v in checks.items() if not v]},
                     ensure_ascii=False))
    return 0 if record["verdict"] == "SAFE_FRESH_PROCESS_NEVER_DISPATCHES" else 1


if __name__ == "__main__":
    raise SystemExit(main())
