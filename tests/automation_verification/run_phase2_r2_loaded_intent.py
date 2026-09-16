#!/usr/bin/env python3
"""Phase 2 / R2 — a fresh process can dispatch from a loaded intent.

CLAIM  `prepare` commits INTENT_COMMITTED and exits. A *different*, fresh process can then
       call `resume` and perform the Save-All dispatch, because continuity is assumed from
       persisted fields (run/owner/revision + INTENT_COMMITTED). The state contract allows
       the original single dispatch only from the same uninterrupted caller that just
       completed the intent write/read-back; a loaded intent is reconciliation only.
       Safety currently depends on the caller passing --no-dispatch.
ENTRY  Real CLI `transaction prepare` then `transaction resume` (separate processes).
ORACLE Independent dispatcher counter jsonl + persisted intent fields + exit codes.
DECIDE A fresh (non-originating) process dispatches -> at-most-once/continuity contract
       is unmet; loaded intent must become an ambiguity barrier with no dispatch.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (counter_entries, durable_copy_tree, program_hashes, read_json, run_product, write_dispatcher,
                     write_json, write_tree_manifest)

CASE = "RUN-R2"


def setup(case_root: Path):
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    (case_root / "destination").mkdir()
    counter = case_root / "counter.jsonl"
    counter.touch()
    dispatcher = write_dispatcher(case_root / "dispatcher.py", block_seconds=0.0)
    write_json(case_root / "state.json", {"schema_version": 2, "revision": 0, "current_run_id": None,
                                          "active_writer_id": None, "context_lock": None, "runs": [],
                                          "verified_albums": []})
    return counter, dispatcher


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-root", required=True)
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    ev.mkdir(parents=True, exist_ok=True)
    counter, dispatcher = setup(case_root)
    state_path = case_root / "state.json"
    record = {"claim": "fresh process can dispatch a loaded intent",
              "entry": "transaction prepare (process A) then transaction resume (process B)",
              "oracle": "independent dispatcher counter jsonl; persisted intent fields",
              "program_hashes": program_hashes(), "case_root": str(case_root)}

    common = ["--project-root", str(case_root), "--state", str(state_path), "--test-mode"]
    prepare = run_product(ev / "prepare", ["transaction", "prepare", *common,
                                           "--run-id", CASE, "--owner-id", "WRITER-R2",
                                           "--group-key", "line:jp.naver.line.mac:旻謙允禎成長日記",
                                           "--start-date", "2024-05-13", "--end-date", "2024-05-17",
                                           "--expected-images", "57", "--destination",
                                           str(case_root / "destination"),
                                           "--evidence-dir", str(case_root / "evidence" / "prepare")],
                          timeout=60)
    record["prepare"] = {"exit_code": prepare["exit_code"], "result": prepare["result"]}
    pre_state = read_json(state_path)
    record["state_after_prepare"] = {"revision": pre_state.get("revision"),
                                     "runs": [r.get("run_id") for r in pre_state.get("runs", [])],
                                     "intent_state": (pre_state.get("runs") or [{}])[0].get("intent_state")}

    resume_argv = ["transaction", "resume", *common, "--run-id", CASE, "--expected-revision", "1",
                   "--expected-owner-id", "WRITER-R2", "--dispatcher", str(dispatcher),
                   "--dispatch-counter", str(counter)]
    fresh = run_product(ev / "fresh-resume", resume_argv + ["--evidence-dir", str(case_root / "evidence" / "resume")],
                        timeout=60)
    after = counter_entries(counter)
    record["fresh_resume"] = {"exit_code": fresh["exit_code"], "result": fresh["result"]}
    record["side_effects_after_fresh_resume"] = len(after)
    post_state = read_json(state_path)
    record["state_after_fresh_resume"] = {"revision": post_state.get("revision"),
                                          "intent_state": (post_state.get("runs") or [{}])[0].get("intent_state"),
                                          "dispatch_state": (post_state.get("runs") or [{}])[0].get("dispatch_state")}
    write_json(ev / "state-after-fresh-resume.json", read_json(state_path))
    write_json(ev / "counter-final.json", after)

    # flag-dependence probe: identical fresh fixture, but caller passes --no-dispatch
    counter2, dispatcher2 = setup(case_root)
    prepare2 = run_product(ev / "prepare-b", ["transaction", "prepare", *common,
                                              "--run-id", CASE, "--owner-id", "WRITER-R2",
                                              "--group-key", "line:jp.naver.line.mac:旻謙允禎成長日記",
                                              "--start-date", "2024-05-13", "--end-date", "2024-05-17",
                                              "--expected-images", "57", "--destination",
                                              str(case_root / "destination"),
                                              "--evidence-dir", str(case_root / "evidence" / "prepare-b")],
                            timeout=60)
    no_dispatch = run_product(ev / "fresh-resume-no-dispatch",
                              ["transaction", "resume", *common, "--run-id", CASE, "--expected-revision", "1",
                               "--expected-owner-id", "WRITER-R2", "--dispatcher", str(dispatcher2),
                               "--dispatch-counter", str(counter2), "--no-dispatch",
                               "--evidence-dir", str(case_root / "evidence" / "resume-b")], timeout=60)
    record["probe_no_dispatch_flag"] = {"prepare_exit": prepare2["exit_code"], "exit_code": no_dispatch["exit_code"],
                                        "result": no_dispatch["result"],
                                        "side_effects": len(counter_entries(counter2))}
    record["verdict"] = ("REPRODUCED_FRESH_PROCESS_DISPATCH" if len(after) >= 1 and
                         (fresh["result"] or {}).get("dispatch_performed") is True
                         else "NO_FRESH_PROCESS_DISPATCH")
    write_json(ev / "observation.json", record)
    durable_copy_tree(case_root, ev / "case-root-durable")
    write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "side_effects": len(after),
                      "no_dispatch_probe": record["probe_no_dispatch_flag"]["result"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
