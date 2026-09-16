#!/usr/bin/env python3
"""Phase 2 / R1 — normal-path crash window between the dispatch side effect and the barrier commit.

CLAIM  In the normal (non-flag) resume path the dispatcher side effect runs before the
       dispatch barrier is committed. A hard interruption inside that window leaves the
       persisted state at INTENT_COMMITTED; a fresh `resume` then dispatches a second time.
ENTRY  Real CLI `transaction resume`; the fixture dispatcher only replaces the external
       Save-All I/O and maintains its own independent side-effect counter.
ORACLE Independent dispatcher-owned counter file (jsonl) + persisted state revision/fields.
       Safe behaviour: after the crash a fresh process must NOT dispatch again
       (counter stays 1) and the loaded intent must become an ambiguity barrier.
DECIDE Counter increases on the fresh resume -> at-most-once is violated; production
       dispatch stays blocked until the barrier/continuity contract is fixed.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (counter_entries, durable_copy_tree, hard_kill, program_hashes, read_json, run_product,
                     start_product, wait_for, write_dispatcher, write_json, write_tree_manifest)

GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
FP = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-root", required=True)
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root = Path(ns.case_root)
    ev = Path(ns.evidence_dir)
    ev.mkdir(parents=True, exist_ok=True)

    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    destination = case_root / "destination"
    destination.mkdir()
    counter = case_root / "counter.jsonl"
    counter.touch()
    dispatcher_blocking = write_dispatcher(case_root / "dispatcher-blocking.py", block_seconds=120.0)
    dispatcher_second = write_dispatcher(case_root / "dispatcher-second.py", block_seconds=0.0)

    state = {
        "schema_version": 2, "revision": 1, "current_run_id": "RUN-R1", "active_writer_id": "WRITER-R1",
        "context_lock": None,
        "runs": [{
            "run_id": "RUN-R1", "mode": "backup_one", "group_key": GROUP, "album_id": None, "fingerprint": FP,
            "observed_title": GROUP.rsplit(":", 1)[-1], "source_provenance": "fixture source",
            "title_confidence": "HIGH", "destination": str(destination), "destination_initially_empty": True,
            "workflow_outcome": None, "phase": "SAVE_ALL_INTENT_COMMITTED", "owner_id": "WRITER-R1",
            "contract_revision": "1.0-rc2", "intent_state": "INTENT_COMMITTED", "dispatch_state": "NOT_ATTEMPTED",
            "intent": {"action_id": "ACTION-RUN-R1", "committed_at": "2026-09-16T00:00:00Z",
                       "owner_execution_id": "WRITER-R1", "group_key": GROUP, "fingerprint": FP,
                       "destination": str(destination),
                       "calibration": {"observed_at": "2026-09-16T00:00:00Z", "screenshot_width": 1,
                                       "screenshot_height": 1, "ellipsis": [1, 1], "dot_spacing": 1.0,
                                       "save_all_point": [1, 1], "confidence": "HIGH",
                                       "evidence": "fixture calibration"},
                       "intent_state": "INTENT_COMMITTED", "dispatch_state": "NOT_ATTEMPTED",
                       "save_all_retry_allowed": False, "dispatch_outcome": "NOT_ATTEMPTED",
                       "trigger_outcome": "NOT_APPLICABLE"},
            "dispatch_evidence": None, "verification": None, "runtime_errors": [], "events": [], "reconciliations": [],
            "checkpoint": {"phase": "SAVE_ALL_INTENT_COMMITTED", "at": "2026-09-16T00:00:00Z", "evidence": "fixture"},
        }],
        "verified_albums": [],
    }
    state_path = case_root / "state.json"
    write_json(state_path, state)
    write_json(ev / "pre-state.json", state)

    common = ["transaction", "resume", "--project-root", str(case_root), "--state", str(state_path),
              "--run-id", "RUN-R1", "--expected-revision", "1", "--expected-owner-id", "WRITER-R1",
              "--test-mode"]

    record = {"claim": "normal-path crash window between dispatch side effect and barrier commit",
              "entry": "python -m line_backup_acceptance transaction resume (real CLI)",
              "oracle": "independent dispatcher counter jsonl + persisted revision/intent fields",
              "program_hashes": program_hashes(), "case_root": str(case_root)}

    # 1) first (interrupted) dispatch: blocking dispatcher, killed after its side effect
    proc = start_product(common + ["--dispatcher", str(dispatcher_blocking), "--dispatch-counter", str(counter),
                                   "--evidence-dir", str(case_root / "evidence" / "first")])
    saw_side_effect = wait_for(lambda: len(counter_entries(counter)) == 1, timeout=30.0)
    record["first_dispatch_side_effect_observed"] = saw_side_effect
    if not saw_side_effect:
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
        write_json(ev / "observation.json", record)
        write_tree_manifest(ev)
        return 1
    live_state = read_json(state_path)
    write_json(ev / "state-after-crash-before-kill.json", live_state)
    record["state_at_kill"] = {"revision": live_state.get("revision"),
                               "intent_state": live_state["runs"][0].get("intent_state"),
                               "dispatch_evidence": live_state["runs"][0].get("dispatch_evidence"),
                               "workflow_outcome": live_state["runs"][0].get("workflow_outcome")}
    kill_evidence = hard_kill(proc)
    record["kill"] = {"pid": kill_evidence["pid"], "returncode": kill_evidence["returncode"],
                      "signal": kill_evidence["signal"], "stderr_tail": kill_evidence["stderr"][-800:]}
    write_json(ev / "state-after-kill.json", read_json(state_path))
    write_json(ev / "counter-after-kill.json", counter_entries(counter))

    # 2) fresh process resume of the same loaded intent
    fresh = run_product(ev / "fresh-resume", common + ["--dispatcher", str(dispatcher_second),
                                                       "--dispatch-counter", str(counter),
                                                       "--evidence-dir", str(case_root / "evidence" / "second")],
                        timeout=60)
    after = counter_entries(counter)
    final_state = read_json(state_path)
    write_json(ev / "state-after-fresh-resume.json", final_state)
    write_json(ev / "counter-final.json", after)
    record["fresh_resume"] = {"exit_code": fresh["exit_code"], "result": fresh["result"]}
    record["dispatch_side_effect_count_after_fresh_resume"] = len(after)
    record["final_run_fields"] = {k: final_state["runs"][0].get(k) for k in
                                  ("intent_state", "dispatch_state", "workflow_outcome")}
    record["verdict"] = "REPRODUCED_DUPLICATE_DISPATCH" if len(after) >= 2 else "NO_DUPLICATE_DISPATCH"
    write_json(ev / "observation.json", record)

    durable_copy_tree(case_root, ev / "case-root-durable")
    write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "side_effects": len(after)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
