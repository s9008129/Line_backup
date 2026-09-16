#!/usr/bin/env python3
"""Phase 2 / R1 — crash window between the dispatch side effect and the barrier commit.

CLAIM (Rev14, reproduced pre-fix in attempt-01)  In the normal resume path the dispatcher side
       effect ran before the barrier commit; a hard interruption inside that window left the
       persisted state at INTENT_COMMITTED and a fresh `resume` dispatched a second time.
ENTRY  Real CLI `transaction prepare` (the single in-process dispatch window, Rev15 §15.1) with a
       fixture dispatcher that replaces only the external Save-All I/O and owns its counter;
       the prepare process is SIGKILLed while the dispatcher is alive; then a fresh process
       `transaction resume` (reconciliation-only).
ORACLE Independent dispatcher-owned counter file (jsonl) + persisted state revision/fields +
       state bytes before/after the kill, and the post-kill directory content of `state/`.
       Safe behaviour: counter never exceeds one line, the fresh process performs no dispatch,
       the loaded intent becomes the ambiguity barrier, and commit refuses.
DECIDE Post-fix (this run) the gap must flip to its safe verdict.  A second counter line, a
       state mutation by the kill, or a commit that accepts the unresolved intent re-opens R1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "phase2-r1-crash-window"
GROUP = F.GROUP
FP = F.FP57
CASE_ROOT = Path("/private/tmp/line-backup-acceptance-case-01")
ATTEMPT_01 = H.WORK / "evidence/20260916-auto-verification/attempt-01/phase2-r1"

PRE_FIX = {
    "verdict": "REPRODUCED_DUPLICATE_DISPATCH",
    "observation": ("normal-path resume is SIGKILLed after the dispatcher side effect (state revision 1, "
                    "INTENT_COMMITTED, no dispatch_evidence); fresh resume dispatched again; counter 1->2"),
    "evidence": str(ATTEMPT_01 / "observation.json"),
}


def sha(path: Path) -> dict:
    data = Path(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def counter_lines(counter: Path) -> list[dict]:
    return H.counter_entries(counter)


def build_case_root(root: Path) -> dict:
    """Owned, canonical case-root fixture (Rev16 §16.1 children) built by this driver only."""
    H.ensure_owned_root(root, DRIVER_ID)
    H.reset_owned_content(root)
    paths = F.write_canonical_root(root, F.fresh_state(), destination_name="destination")
    paths["source_evidence"] = F.source_evidence_record(root, name="source-evidence.json")["path"]
    paths["counter"] = root / "dispatch-counter.jsonl"
    paths["counter"].touch()
    paths["input_state"] = root / "input-state.json"
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    if case_root.resolve() != CASE_ROOT.resolve():
        print(json.dumps({"verdict": "INCONCLUSIVE_SETUP_FAILED",
                          "reason": f"R1 is bound to its literal case root {CASE_ROOT}"}, ensure_ascii=False))
        return 1
    ev.mkdir(parents=True, exist_ok=True)

    paths = build_case_root(case_root)
    state_path = Path(paths["state"])
    dispatcher = H.write_dispatcher(case_root / "dispatcher-blocking.py", wait_parent=True,
                                    started_barrier=case_root / "dispatch-started.barrier")
    pre_state = read_json(state_path)
    pre_state_sha = sha(state_path)

    record = {
        "driver": DRIVER_ID,
        "claim": ("pre-fix: a SIGKILL inside the dispatch window left the intent committed and a fresh resume "
                  "dispatched again; post-fix: the loaded intent is reconciliation-only and at-most-once holds"),
        "entry": "real CLI transaction prepare (killed mid-dispatch) then transaction resume (fresh process)",
        "oracle": ("independent dispatcher counter jsonl + persisted revision/intent/dispatch fields + state bytes "
                   "before/after the kill + post-kill `state/` directory content"),
        "pre_fix": PRE_FIX,
        "case_root": str(case_root),
        "program_hashes": H.program_hashes(),
        "pre_state": pre_state_sha,
        "pre_state_excerpt": {"revision": pre_state["revision"], "runs": len(pre_state["runs"])},
    }
    record["fixture"] = {"source_evidence": str(paths["source_evidence"]), "destination": str(paths["destination"]),
                         "config": str(paths["config"]), "run_log": str(paths["run_log"])}

    prepare_args = ["transaction", "prepare", "--project-root", str(case_root), "--config", str(paths["config"]),
                    "--run-log", str(paths["run_log"]), "--state", str(state_path), "--test-mode",
                    "--run-id", "RUN-R1", "--owner-id", "WRITER-R1", "--group-key", GROUP,
                    "--start-date", FP["start_date"], "--end-date", FP["end_date"],
                    "--expected-images", str(FP["expected_images"]), "--destination", str(paths["destination"]),
                    "--source-evidence", str(paths["source_evidence"]), "--dispatcher", str(dispatcher),
                    "--dispatch-counter", str(paths["counter"]),
                    "--evidence-dir", str(case_root / "evidence" / "prepare")]
    H.write_json(ev / "prepare-argv.json", {"argv": H.product_argv(*prepare_args), "cwd": str(H.WORK),
                                            "env": {"PYTHONPATH": str(H.SRC), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                                                    "PYTHONHASHSEED": "0"}})
    proc = H.start_product(prepare_args)
    barrier = case_root / "dispatch-started.barrier"
    started = H.wait_for(barrier.exists, timeout=60.0)
    record["dispatch_started_barrier"] = started
    if not started:
        H.hard_kill(proc)
        record["verdict"] = "INCONCLUSIVE_SETUP_FAILED"
        H.write_json(ev / "observation.json", record)
        H.write_tree_manifest(ev)
        print(json.dumps({"verdict": record["verdict"]}, ensure_ascii=False))
        return 1

    window_bytes = state_path.read_bytes()
    window_sha = hashlib.sha256(window_bytes).hexdigest()
    window_state = json.loads(window_bytes.decode("utf-8"))
    window_run = window_state["runs"][0]
    record["kill_window"] = {
        "revision": window_state.get("revision"),
        "intent_state": window_run.get("intent_state"),
        "dispatch_state": window_run.get("dispatch_state"),
        "intent_dispatch_outcome": window_run["intent"].get("dispatch_outcome"),
        "save_all_retry_allowed": window_run["intent"].get("save_all_retry_allowed"),
        "counter_lines": len(counter_lines(paths["counter"])),
        "state_sha256": window_sha,
    }
    counter_first = counter_lines(paths["counter"])
    dispatcher_pid = counter_first[0].get("pid") if counter_first else None

    time.sleep(0.2)
    os.kill(proc.pid, signal.SIGKILL)
    try:
        stdout, stderr = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        stdout = stderr = ""
    kill_record = {"pid": proc.pid, "signal": "SIGKILL", "returncode": proc.returncode,
                   "stdout_tail": (stdout or "")[-400:], "stderr_tail": (stderr or "")[-400:],
                   "dispatcher_pid": dispatcher_pid}
    record["kill"] = kill_record
    (ev / "prepare-stdout.log").write_text(stdout or "", encoding="utf-8")
    (ev / "prepare-stderr.log").write_text(stderr or "", encoding="utf-8")
    (ev / "prepare-exit-code").write_text(f"{proc.returncode}\n", encoding="utf-8")

    orphan_gone, orphan_forced = False, False
    if dispatcher_pid:
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            try:
                os.kill(dispatcher_pid, 0)
                time.sleep(0.25)
            except ProcessLookupError:
                orphan_gone = True
                break
        if not orphan_gone:
            orphan_forced = True
            try:
                os.kill(dispatcher_pid, signal.SIGKILL)
            except ProcessLookupError:
                orphan_gone = True
    record["orphan"] = {"pid": dispatcher_pid, "reparented_and_self_exited": orphan_gone,
                        "orphan_forced_kill": orphan_forced}

    after_kill_bytes = state_path.read_bytes()
    after_state = json.loads(after_kill_bytes.decode("utf-8"))
    record["after_kill"] = {
        "state_sha256": hashlib.sha256(after_kill_bytes).hexdigest(),
        "state_bytes_identical_to_kill_window": after_kill_bytes == window_bytes,
        "revision": after_state.get("revision"),
        "has_revision2_record": any(r.get("phase") == "SAVE_ALL_DISPATCH_ATTEMPTED" for r in after_state["runs"]),
        "retry_allowed": after_state["runs"][0]["intent"].get("save_all_retry_allowed"),
        "state_dir_names": sorted(p.name for p in state_path.parent.iterdir()),
        "counter_lines": len(counter_lines(paths["counter"])),
    }
    H.write_json(ev / "state-at-kill-window.json", window_state)
    H.write_json(ev / "state-after-kill.json", after_state)

    resume_args = ["transaction", "resume", "--project-root", str(case_root), "--config", str(paths["config"]),
                   "--run-log", str(paths["run_log"]), "--state", str(state_path), "--test-mode",
                   "--run-id", "RUN-R1", "--expected-revision", "1", "--expected-owner-id", "WRITER-R1",
                   "--no-dispatch", "--evidence-dir", str(case_root / "evidence" / "resume")]
    resume = H.run_product(ev / "fresh-resume", resume_args, timeout=60)
    resume_result = resume["result"] or {}
    record["fresh_resume"] = {"exit_code": resume["exit_code"], "result": resume_result,
                              "argv": resume["argv"]}
    final_state = read_json(state_path)
    final_run = final_state["runs"][0]
    record["after_fresh_resume"] = {
        "revision": final_state.get("revision"),
        "intent_state": final_run.get("intent_state"),
        "dispatch_state": final_run.get("dispatch_state"),
        "manual_reconciliation_required": final_run.get("manual_reconciliation_required"),
        "reconciliations": len(final_run.get("reconciliations") or []),
        "counter_lines": len(counter_lines(paths["counter"])),
    }
    H.write_json(ev / "state-after-fresh-resume.json", final_state)
    H.write_json(ev / "counter-final.json", counter_lines(paths["counter"]))

    commit_args = ["transaction", "commit", "--project-root", str(case_root), "--config", str(paths["config"]),
                   "--run-log", str(paths["run_log"]), "--state", str(state_path), "--test-mode",
                   "--run-id", "RUN-R1", "--expected-revision", str(final_state.get("revision")),
                   "--expected-owner-id", "WRITER-R1",
                   "--verification-json", str(case_root / "verification-not-used.json"),
                   "--evidence-dir", str(case_root / "evidence" / "commit")]
    commit = H.run_product(ev / "commit-attempt", commit_args, timeout=60)
    commit_result = commit["result"] or {}
    record["commit_after_barrier"] = {"exit_code": commit["exit_code"], "result": commit_result,
                                      "argv": commit["argv"],
                                      "state_replaced": commit_result.get("state_replaced")}

    checks = {
        "kill-window.revision1": record["kill_window"]["revision"] == 1,
        "kill-window.intent-committed": record["kill_window"]["intent_state"] == "INTENT_COMMITTED",
        "kill-window.not-attempted": record["kill_window"]["dispatch_state"] == "NOT_ATTEMPTED",
        "kill-window.counter-1": record["kill_window"]["counter_lines"] == 1,
        "kill-window.retry-false": record["kill_window"]["save_all_retry_allowed"] is False,
        "aftermath.state-bytes-identical": record["after_kill"]["state_bytes_identical_to_kill_window"],
        "aftermath.no-revision2": record["after_kill"]["has_revision2_record"] is False,
        "aftermath.counter-still-1": record["after_kill"]["counter_lines"] == 1,
        "aftermath.state-dir": record["after_kill"]["state_dir_names"] == [".line-backup-state.lock",
                                                                           "backup_state.json", "run_log.md"],
        "resume.code": resume_result.get("result") == "RECOVERY_NO_DISPATCH",
        "resume.exit0": resume["exit_code"] == 0,
        "resume.no-dispatch": resume_result.get("dispatch_performed") is False,
        "resume.barrier": resume_result.get("reconciliation_state") == "BARRIER_COMMITTED",
        "resume.revision2": final_state.get("revision") == 2,
        "resume.counter-still-1": record["after_fresh_resume"]["counter_lines"] == 1,
        "commit.refused": commit_result.get("result") == "CONFLICT_UNRESOLVED_DISPATCH",
        "commit.exit4": commit["exit_code"] == 4,
        "commit.no-replacement": commit_result.get("replacement") is False,
    }
    record["checks"] = checks
    record["verdict"] = "SAFE_NO_SECOND_DISPATCH_AFTER_CRASH_WINDOW" if all(checks.values()) else "REGRESSION_OR_UNEXPECTED"
    if orphan_forced:
        record["verdict"] = "TASK_REGRESSION_FIXTURE_ORPHAN_FORCED_KILL"
    H.write_json(ev / "observation.json", record)
    H.durable_copy_tree(case_root, ev / "case-root-durable")
    H.write_tree_manifest(ev)
    print(json.dumps({"verdict": record["verdict"], "checks": checks,
                      "counter_lines": record["after_fresh_resume"]["counter_lines"]}, ensure_ascii=False))
    return 0 if record["verdict"] == "SAFE_NO_SECOND_DISPATCH_AFTER_CRASH_WINDOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
