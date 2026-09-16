#!/usr/bin/env python3
"""Independent subprocess acceptance driver for transaction Cases 01-12."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
ROOT = Path("/private/tmp")
FP = {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57}


def sha(path: Path) -> dict:
    data = path.read_bytes() if path.exists() else b"<missing>"
    return {"exists": path.exists(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def artifact_inventory(root: Path) -> list[dict]:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            item = sha(path)
            item["path"] = str(path.relative_to(root))
            artifacts.append(item)
    return artifacts


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def copy_if_distinct(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copyfile(source, destination)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fresh_state(run_id: str, owner: str, revision: int, *, outcome=None, unknown=False, legacy=False) -> dict:
    destination = str(ROOT / "placeholder")
    intent_state = "TRIGGER_UNKNOWN" if unknown else "INTENT_COMMITTED"
    dispatch_state = "UNKNOWN" if unknown else "NOT_ATTEMPTED"
    trigger = "UNKNOWN" if unknown else "NOT_APPLICABLE"
    dispatch = "UNKNOWN" if unknown else "NOT_ATTEMPTED"
    run = {"run_id": run_id, "group_key": GROUP, "fingerprint": FP, "destination": destination,
           "workflow_outcome": outcome, "phase": outcome or ("TRIGGER_UNKNOWN" if unknown else "SAVE_ALL_INTENT_COMMITTED"),
           "owner_id": None if outcome else owner, "events": [], "reconciliations": [], "runtime_errors": []}
    if not legacy:
        run.update({"contract_revision": "1.0-rc2", "observed_title": "旻謙允禎成長日記",
                    "source_provenance": "fixture source", "intent_state": intent_state,
                    "dispatch_state": dispatch_state,
                    "intent": {"action_id": "ACTION-" + run_id, "owner_execution_id": owner,
                               "group_key": GROUP, "fingerprint": FP, "destination": destination,
                               "calibration": {"confidence": "HIGH", "evidence": "fixture"},
                               "intent_state": intent_state, "dispatch_state": dispatch_state,
                               "trigger_outcome": trigger, "dispatch_outcome": dispatch,
                               "save_all_retry_allowed": False}})
    state = {"schema_version": 2, "revision": revision,
             "current_run_id": None if outcome else run_id,
             "active_writer_id": None if outcome else owner, "context_lock": None,
             "runs": [run], "verified_albums": []}
    if outcome == "VERIFIED":
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": FP,
                                     "verified_run_id": run_id, "destinations": [destination],
                                     "source_authority": "authoritative_exact_join"}]
    return state


def setup(case_root: Path, case: str) -> tuple[Path, dict]:
    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    run_id, owner = "RUN-CASE-" + case, "WRITER-CASE-" + case
    if case in {"01", "07"}:
        state = {"schema_version": 2, "revision": 0, "current_run_id": None,
                 "active_writer_id": None, "context_lock": None, "runs": [], "verified_albums": []}
    elif case == "04":
        state = fresh_state(run_id, owner, 7, outcome="VERIFIED")
    elif case in {"09", "10A", "10B"}:
        state = fresh_state(run_id, owner, 2, unknown=case == "10B")
    elif case == "11":
        state = fresh_state(run_id, owner, 7, outcome="SAFE_ABORT", legacy=True)
    elif case == "12":
        state = fresh_state(run_id, owner, 7, outcome="VERIFIED")
        state["verified_albums"].append(dict(state["verified_albums"][0]))
    else:
        state = fresh_state(run_id, owner, 1)
    destination = case_root / "destination"
    destination.mkdir()
    for run in state["runs"]:
        run["destination"] = str(destination)
        if isinstance(run.get("intent"), dict):
            run["intent"]["destination"] = str(destination)
    for entry in state["verified_albums"]:
        entry["destinations"] = [str(destination)]
    state_path = case_root / "state.json"
    write_json(state_path, state)
    write_json(case_root / "input-state.json", state)
    write_json(case_root / "verification.json", {"filesystem_status": "PASS", "regular_files": 57,
                                                   "recognized_images": 57, "zero_byte_files": 0})
    dispatcher = case_root / "dispatcher.py"
    dispatcher.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, json\n"
        "p=argparse.ArgumentParser(); p.add_argument('--counter'); p.add_argument('--outcome'); p.add_argument('--crash-after-dispatch', action='store_true'); n=p.parse_args()\n"
        "with open(n.counter, 'a', encoding='utf-8') as f: f.write(json.dumps({'outcome': n.outcome})+'\\n')\n"
        "raise SystemExit(1 if n.crash_after_dispatch else 0)\n", encoding="utf-8")
    dispatcher.chmod(0o755)
    (case_root / "counter.jsonl").touch()
    return state_path, state


def env_for() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["LC_ALL"] = "C"
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHASHSEED"] = "0"
    return env


def record_process(argv: list[str], record_dir: Path, *, env=None, wait=True):
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not wait:
        return subprocess.Popen(argv, cwd=Path(__file__).resolve().parents[1], env={**env_for(), **(env or {})},
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p = subprocess.run(argv, cwd=Path(__file__).resolve().parents[1], env={**env_for(), **(env or {})},
                       capture_output=True, text=True, check=False)
    (record_dir / "stdout.log").write_text(p.stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(p.stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(str(p.returncode) + "\n", encoding="utf-8")
    try:
        result = json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        result = None
    return {"argv": argv, "exit_code": p.returncode, "result": result,
            "stdout": str(record_dir / "stdout.log"), "stderr": str(record_dir / "stderr.log")}


def tx_argv(root: Path, operation: str, evidence: Path, **kwargs) -> list[str]:
    argv = ["/usr/bin/python3", "-m", "line_backup_acceptance", "transaction", operation,
            "--project-root", str(root), "--state", str(root / "state.json"),
            "--evidence-dir", str(evidence), "--test-mode"]
    for key, value in kwargs.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        elif value is not None:
            argv.extend([flag, str(value)])
    return argv


def status_argv(root: Path) -> list[str]:
    return ["/usr/bin/python3", "-m", "line_backup_acceptance", "status", "evaluate",
            "--input", str(root / "status-input.json"), "--output", str(root / "status-output.json")]


def parse_result(record: dict) -> dict:
    return record.get("result") or {}


def intent_axes(run: dict) -> dict:
    intent = run.get("intent") if isinstance(run.get("intent"), dict) else {}
    return {"intent_state": run.get("intent_state"), "dispatch_state": run.get("dispatch_state"),
            "trigger_outcome": intent.get("trigger_outcome"), "dispatch_outcome": intent.get("dispatch_outcome"),
            "save_all_retry_allowed": intent.get("save_all_retry_allowed")}


def state_observation(path: Path, counter: Path) -> dict:
    state = read_json(path)
    runs = state.get("runs") or []
    run = runs[0] if runs else {}
    return {"bytes": sha(path), "revision": state.get("revision"), "run": run,
            "intent_axes": intent_axes(run), "verified_albums": state.get("verified_albums"),
            "current_run_id": state.get("current_run_id"), "active_writer_id": state.get("active_writer_id"),
            "context_lock": state.get("context_lock"),
            "counter_lines": len(counter.read_text(encoding="utf-8").splitlines()) if counter.exists() else 0}


def compare_status(root: Path, scenario: str, record_dir: Path) -> dict:
    write_json(root / "status-input.json", {"scenario": scenario})
    record = record_process(status_argv(root), record_dir)
    result = parse_result(record)
    expected = {
        "legacy-no-source": {"primary_outcome_status": "UNKNOWN", "implementation_status": "COMPLETE",
                             "core_acceptance_status": "BLOCKED", "required_verification_status": "PASS",
                             "independent_acceptance_status": "PENDING", "task_closure_status": "CORE_ACCEPTANCE_BLOCKED"},
        "contradictory-axes": {"primary_outcome_status": "NOT_ACHIEVED", "implementation_status": "COMPLETE",
                               "core_acceptance_status": "FAIL", "required_verification_status": "FAIL",
                               "independent_acceptance_status": "PENDING", "task_closure_status": "FIX_REQUIRED"},
    }[scenario]
    observed = {key: result.get(key) for key in expected}
    record["independent_match"] = record["exit_code"] == 0 and observed == expected
    record["expected"] = expected
    return record


def concurrent_processes(root: Path, operation: str, specs: list[dict], barrier_name: str, records: Path) -> list[dict]:
    barrier = root / barrier_name
    children = []
    for spec in specs:
        evidence = records / spec["label"]
        argv = tx_argv(root, operation, evidence, **spec["kwargs"])
        child = record_process(argv, records / (spec["label"] + "-process"), wait=False)
        children.append((spec["label"], evidence, child, argv))
    ready = Path(str(barrier) + ".ready")
    deadline = time.time() + 15
    while not ready.exists() and time.time() < deadline:
        time.sleep(0.01)
    barrier.touch()
    results = []
    for label, evidence, child, argv in children:
        stdout, stderr = child.communicate(timeout=30)
        record_dir = records / label
        record_dir.mkdir(parents=True, exist_ok=True)
        (record_dir / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        (record_dir / "exit-code").write_text(str(child.returncode) + "\n", encoding="utf-8")
        try:
            result = json.loads(stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            result = None
        results.append({"label": label, "argv": argv, "exit_code": child.returncode, "result": result})
    return results


def run_case(case: str, requested_root: Path | None = None) -> tuple[dict, int]:
    root = requested_root or (ROOT / ("line-backup-acceptance-case-" + case))
    state_path, _ = setup(root, case)
    counter = root / "counter.jsonl"
    records = root / "process-records"
    pre = state_observation(state_path, counter)
    records_list = []
    expected = True
    if case == "01":
        e = root / "evidence"
        records_list.extend([
            record_process(tx_argv(root, "prepare", e, run_id="RUN-CASE-01", owner_id="WRITER-CASE-01", group_key=GROUP,
                                  start_date=FP["start_date"], end_date=FP["end_date"], expected_images=57, destination=root / "destination"), records / "prepare"),
            record_process(tx_argv(root, "resume", e, run_id="RUN-CASE-01", expected_revision=1, expected_owner_id="WRITER-CASE-01",
                                  dispatcher=root / "dispatcher.py", dispatch_counter=counter), records / "resume"),
            record_process(tx_argv(root, "commit", e, run_id="RUN-CASE-01", expected_revision=2, expected_owner_id="WRITER-CASE-01",
                                  verification_json=root / "verification.json"), records / "commit"),
            record_process(tx_argv(root, "finalize", e, run_id="RUN-CASE-01", expected_revision=3, expected_owner_id="WRITER-CASE-01",
                                  verification_json=root / "verification.json", outcome="VERIFIED"), records / "finalize"),
        ])
        post = state_observation(state_path, counter)
        run = post["run"]
        expected = ([r["exit_code"] for r in records_list] == [0, 0, 0, 0] and post["revision"] == 4
                     and run.get("workflow_outcome") == "VERIFIED" and post["active_writer_id"] is None
                     and post["context_lock"] is None and post["counter_lines"] == 1
                     and len(post["verified_albums"]) == 1
                     and run.get("verification") == read_json(root / "verification.json"))
    elif case in {"02", "03"}:
        outcome = "RETURNED" if case == "02" else "UNKNOWN"
        first = tx_argv(root, "resume", root / "evidence" / "first", run_id="RUN-CASE-" + case, expected_revision=1,
                        expected_owner_id="WRITER-CASE-" + case, dispatcher=root / "dispatcher.py", dispatch_counter=counter,
                        dispatcher_outcome=outcome, crash_after_dispatch=case == "02")
        second = tx_argv(root, "resume", root / "evidence" / "second", run_id="RUN-CASE-" + case, expected_revision=2,
                         expected_owner_id="WRITER-CASE-" + case, dispatcher=root / "dispatcher.py", dispatch_counter=counter,
                         no_dispatch=True)
        records_list = [record_process(first, records / "first"), record_process(second, records / "second")]
        post = state_observation(state_path, counter)
        expected = (records_list[0]["exit_code"] == 1 and records_list[1]["exit_code"] == 0
                    and parse_result(records_list[1]).get("result") == "RECOVERY_NO_DISPATCH"
                    and post["revision"] == 2 and post["intent_axes"] == {
                        "intent_state": "TRIGGER_UNKNOWN", "dispatch_state": "UNKNOWN",
                        "trigger_outcome": "UNKNOWN", "dispatch_outcome": "UNKNOWN", "save_all_retry_allowed": False}
                    and post["counter_lines"] == 1)
    elif case == "04":
        e = root / "evidence"
        records_list = [record_process(tx_argv(root, "duplicate-check", e / "duplicate", group_key=GROUP,
                                               start_date=FP["start_date"], end_date=FP["end_date"], expected_images=57,
                                               destination=root / "destination"), records / "duplicate"),
                        record_process(tx_argv(root, "resume", e / "resume", run_id="RUN-CASE-04", expected_revision=7,
                                               expected_owner_id="WRITER-CASE-04", dispatcher=root / "dispatcher.py",
                                               dispatch_counter=counter), records / "resume")]
        post = state_observation(state_path, counter)
        expected = (parse_result(records_list[0]).get("result") == "SKIP_DUPLICATE"
                    and parse_result(records_list[1]).get("result") == "SKIP_TERMINAL"
                    and all(r["exit_code"] == 0 for r in records_list) and post == pre)
    elif case == "05":
        records_list = concurrent_processes(root, "commit", [
            {"label": "a", "kwargs": {"run_id": "RUN-CASE-05", "expected_revision": 1, "expected_owner_id": "WRITER-CASE-05",
                                         "verification_json": root / "verification.json", "pause_at": "COMMIT_BEFORE_REPLACE",
                                         "barrier_file": root / "commit-ready.barrier"}},
            {"label": "b", "kwargs": {"run_id": "RUN-CASE-05", "expected_revision": 1, "expected_owner_id": "WRITER-CASE-05",
                                         "verification_json": root / "verification.json", "pause_at": "COMMIT_BEFORE_REPLACE",
                                         "barrier_file": root / "commit-ready.barrier"}},
        ], "commit-ready.barrier", records)
        post = state_observation(state_path, counter)
        results = [parse_result(r) for r in records_list]
        expected = (sorted(r["exit_code"] for r in records_list) == [0, 4]
                    and sum(r.get("result") == "COMMITTED_VERIFICATION" for r in results) == 1
                    and sum(r.get("result") == "CONFLICT_STALE_REVISION" for r in results) == 1
                    and post["revision"] == 2 and post["counter_lines"] == 0)
    elif case == "06":
        r = record_process(tx_argv(root, "commit", root / "evidence", run_id="RUN-CASE-06", expected_revision=1,
                                   expected_owner_id="WRITER-CASE-06-WRONG", verification_json=root / "verification.json"), records / "commit")
        records_list = [r]
        post = state_observation(state_path, counter)
        expected = (r["exit_code"] == 4 and parse_result(r).get("result") == "CONFLICT_OWNER_RUN" and post == pre)
    elif case == "07":
        records_list = concurrent_processes(root, "prepare", [
            {"label": "a", "kwargs": {"run_id": "RUN-CASE-07-A", "owner_id": "WRITER-CASE-07-A", "group_key": GROUP,
                                         "start_date": FP["start_date"], "end_date": FP["end_date"], "expected_images": 57,
                                         "destination": root / "destination", "pause_at": "ACQUIRE_BEFORE_LOCK",
                                         "barrier_file": root / "acquire-ready.barrier"}},
            {"label": "b", "kwargs": {"run_id": "RUN-CASE-07-B", "owner_id": "WRITER-CASE-07-B", "group_key": GROUP,
                                         "start_date": FP["start_date"], "end_date": FP["end_date"], "expected_images": 57,
                                         "destination": root / "destination", "pause_at": "ACQUIRE_BEFORE_LOCK",
                                         "barrier_file": root / "acquire-ready.barrier"}},
        ], "acquire-ready.barrier", records)
        post = state_observation(state_path, counter)
        results = [parse_result(r) for r in records_list]
        expected = (sorted(r["exit_code"] for r in records_list) == [0, 4]
                    and sum(r.get("result") == "PREPARED" for r in results) == 1
                    and sum(r.get("result") == "CONFLICT_ACTIVE_RUN" for r in results) == 1
                    and post["revision"] == 1 and len(post["run"].get("run_id", "")) > 0)
    elif case == "08":
        r = record_process(tx_argv(root, "commit", root / "evidence", run_id="RUN-CASE-08", expected_revision=1,
                                   expected_owner_id="WRITER-CASE-08", verification_json=root / "verification.json",
                                   storage_fault="WRITE_BEFORE_REPLACE"), records / "commit")
        records_list = [r]
        post = state_observation(state_path, counter)
        expected = (r["exit_code"] == 1 and parse_result(r).get("failure_class") == "WRITE_BEFORE_REPLACE"
                    and post == pre)
    elif case == "09":
        first = record_process(tx_argv(root, "finalize", root / "evidence" / "finalize", run_id="RUN-CASE-09",
                                       expected_revision=2, expected_owner_id="WRITER-CASE-09", outcome="VERIFIED",
                                       verification_json=root / "verification.json",
                                       storage_fault="READBACK_UNCERTAIN_AFTER_REPLACE"), records / "finalize")
        second = record_process(tx_argv(root, "resume", root / "evidence" / "resume", run_id="RUN-CASE-09",
                                        expected_revision=3, expected_owner_id="WRITER-CASE-09", no_dispatch=True,
                                        dispatcher=root / "dispatcher.py", dispatch_counter=counter), records / "resume")
        records_list = [first, second]
        post = state_observation(state_path, counter)
        expected = (first["exit_code"] == 1 and parse_result(first).get("result") == "READBACK_UNCERTAIN"
                    and second["exit_code"] == 0 and parse_result(second).get("result") == "SKIP_TERMINAL"
                    and post["revision"] == 3 and post["run"].get("workflow_outcome") == "VERIFIED"
                    and post["active_writer_id"] is None and post["context_lock"] is None
                    and len(post["verified_albums"]) == 1 and post["counter_lines"] == 0)
    elif case == "10":
        subcases = []
        for label, subcase, outcome in (("verified", "10A", "VERIFIED"), ("safe-abort", "10B", "SAFE_ABORT")):
            subroot = root / label
            state_sub, _ = setup(subroot, subcase)
            e = subroot / "evidence"
            record = record_process(tx_argv(subroot, "finalize", e, run_id="RUN-CASE-" + subcase,
                                            expected_revision=2, expected_owner_id="WRITER-CASE-" + subcase,
                                            outcome=outcome, verification_json=subroot / "verification.json"),
                                    records / label)
            observation = state_observation(state_sub, subroot / "counter.jsonl")
            sub_expected = (record["exit_code"] == 0 and observation["revision"] == 3
                            and observation["active_writer_id"] is None and observation["context_lock"] is None
                            and observation["run"].get("workflow_outcome") == outcome
                            and observation["run"].get("verification") == read_json(subroot / "verification.json"))
            if outcome == "VERIFIED":
                sub_expected = sub_expected and len(observation["verified_albums"]) == 1
            else:
                sub_expected = sub_expected and len(observation["verified_albums"]) == 0 and observation["intent_axes"] == {
                    "intent_state": "TRIGGER_UNKNOWN", "dispatch_state": "UNKNOWN",
                    "trigger_outcome": "UNKNOWN", "dispatch_outcome": "UNKNOWN", "save_all_retry_allowed": False}
            subcases.append({"label": label, "process": record, "observation": observation, "match": sub_expected})
        expected = all(row["match"] for row in subcases)
        post = state_observation(root / "state.json", counter)
        records_list = subcases
    elif case in {"11", "12"}:
        scenario = "legacy-no-source" if case == "11" else "contradictory-axes"
        status_record = compare_status(root, scenario, records / "status")
        duplicate = record_process(tx_argv(root, "duplicate-check", root / "evidence", group_key=GROUP,
                                            start_date=FP["start_date"], end_date=FP["end_date"], expected_images=57,
                                            destination=root / "destination"), records / "duplicate")
        records_list = [status_record, duplicate]
        post = state_observation(state_path, counter)
        expected_duplicate = (duplicate["exit_code"] == 0 and parse_result(duplicate).get("result") == "NOT_DUPLICATE") if case == "11" else (
            duplicate["exit_code"] == 4 and parse_result(duplicate).get("result") == "CONFLICT_DUPLICATE")
        expected = status_record["independent_match"] and expected_duplicate and post == pre
    else:
        raise ValueError(case)
    if case != "10":
        post = state_observation(state_path, counter)
    manifest = {"schema_version": 1, "case_id": case, "initial": pre, "final": post,
                "processes": records_list, "artifacts": artifact_inventory(root),
                "independent_oracle_match": expected}
    write_json(root / "manifest.json", manifest)
    write_json(root / "result.json", {"case_id": case, "independent_oracle_match": expected,
                                       "manifest": sha(root / "manifest.json")})
    return {"case_id": case, "match": expected, "root": str(root), "manifest": sha(root / "manifest.json")}, 0 if expected else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--pre-state", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--post-state", required=True)
    parser.add_argument("--counter", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--stdout", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--exit-code", required=True)
    parser.add_argument("--evidence-dir", required=True)
    ns = parser.parse_args()
    result, code = run_case(ns.case_id, Path(ns.case_root))
    Path(ns.pre_state).parent.mkdir(parents=True, exist_ok=True)
    copy_if_distinct(Path(ns.case_root) / "input-state.json", Path(ns.pre_state))
    copy_if_distinct(Path(ns.case_root) / "state.json", Path(ns.post_state))
    copy_if_distinct(Path(ns.case_root) / "manifest.json", Path(ns.manifest))
    write_json(Path(ns.result), result)
    Path(ns.stdout).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    Path(ns.stderr).write_text("", encoding="utf-8")
    Path(ns.exit_code).write_text(str(code) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
