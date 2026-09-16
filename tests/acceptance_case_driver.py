#!/usr/bin/env python3
"""Independent subprocess acceptance driver for transaction Cases 01-25 (Rev18 plan).

The driver is only a subprocess orchestrator and independent oracle: it creates fixture
preconditions, launches the real product CLI in its own process, collects raw
stdout/stderr/exit, and recomputes the expected outcome from the case specification before
inspecting product output.  It contains no transition model and never writes expected
values into product state.

Ownership isolation (Rev15 §15.5): the driver creates its own literal case roots only when
missing, writes an ownership marker, never removes a root lacking its marker, and removes
nothing by default.  Re-running a case resets only this driver's own case content inside an
already-owned root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "automation_verification"))
import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

DRIVER_ID = "acceptance-case-driver"
GROUP = F.GROUP
LEGACY_GROUP = F.LEGACY_GROUP
FP57 = F.FP57
CASES = [f"{index:02d}" for index in range(1, 26)]
PRODUCT_HEAD = ["/usr/bin/python3", "-m", "line_backup_acceptance"]


# ---------------------------------------------------------------------------
# Small deterministic helpers
# ---------------------------------------------------------------------------

def sha(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"exists": False, "bytes": 0, "sha256": None}
    data = path.read_bytes()
    return {"exists": True, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_chain(evidence_dir: Path, result: dict) -> None:
    """Author an independent chain-v2 artifact set (result.json + manifest.json last)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_json(evidence_dir / "result.json", result)
    data = (evidence_dir / "result.json").read_bytes()
    fields = ("schema_version", "mode", "run_id", "group_key", "fingerprint", "destination",
              "filesystem_status", "recognized_images", "expected_images", "overall_status",
              "exit_code", "artifact_readback")
    artifacts = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            blob = path.read_bytes()
            artifacts.append({"path": path.name, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
    write_json(evidence_dir / "manifest.json", {
        "schema_version": 1, "artifacts": artifacts,
        "result_summary": {field: result.get(field) for field in fields},
        "result_bytes": len(data), "result_sha256": hashlib.sha256(data).hexdigest()})


class Case:
    """Records checks and the raw evidence of one acceptance case."""

    def __init__(self, case_id: str, root: Path):
        self.case_id = case_id
        self.root = Path(root)
        self.checks: list[dict] = []
        self.processes: list[dict] = []
        self.inputs: list[dict] = []
        self.notes: list[str] = []

    def check(self, ident: str, expected, observed, match: bool | None = None) -> bool:
        ok = observed == expected if match is None else bool(match)
        self.checks.append({"id": ident, "expected": expected, "observed": observed, "match": ok})
        return ok

    def note(self, text: str) -> None:
        self.notes.append(text)

    def cli(self, label: str, args: list[str], *, env_extra: dict | None = None, timeout: float | None = 120.0):
        record_dir = self.root / "process-records" / self.case_id / label
        record = H.run_product(record_dir, args, env_extra=env_extra, timeout=timeout)
        self.inputs.append({
            "label": label, "argv": PRODUCT_HEAD + list(args), "cwd": str(H.WORK),
            "env": {"PYTHONPATH": str(H.SRC), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                    "PYTHONHASHSEED": "0", **(env_extra or {})}})
        entry = {"label": label, "argv": PRODUCT_HEAD + list(args), "exit_code": record["exit_code"],
                 "record_dir": str(record_dir.relative_to(self.root)), "result": record["result"]}
        self.processes.append(entry)
        return record

    def start(self, label: str, args: list[str], *, env_extra: dict | None = None):
        proc = H.start_product(args, env_extra=env_extra)
        self.inputs.append({
            "label": label, "argv": PRODUCT_HEAD + list(args), "cwd": str(H.WORK),
            "env": {"PYTHONPATH": str(H.SRC), "LC_ALL": "C", "PATH": "/usr/bin:/bin",
                    "PYTHONHASHSEED": "0", **(env_extra or {})}})
        return {"label": label, "proc": proc, "args": args}

    def collect(self, handle, *, timeout: float = 60.0) -> dict:
        proc = handle["proc"]
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            stderr = (stderr or "") + "\n<driver timeout collecting the process>\n"
        record_dir = self.root / "process-records" / self.case_id / handle["label"]
        record_dir.mkdir(parents=True, exist_ok=True)
        (record_dir / "stdout.log").write_text(stdout or "", encoding="utf-8")
        (record_dir / "stderr.log").write_text(stderr or "", encoding="utf-8")
        (record_dir / "exit-code").write_text(f"{proc.returncode}\n", encoding="utf-8")
        parsed = None
        try:
            parsed = json.loads((stdout or "").strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            parsed = None
        entry = {"label": handle["label"], "argv": PRODUCT_HEAD + list(handle["args"]),
                 "exit_code": proc.returncode, "record_dir": str(record_dir.relative_to(self.root)),
                 "result": parsed, "pid": proc.pid}
        self.processes.append(entry)
        return {"exit_code": proc.returncode, "result": parsed, "record_dir": str(record_dir),
                "stdout": stdout or "", "stderr": stderr or "", "pid": proc.pid}

    @property
    def match(self) -> bool:
        return all(row["match"] for row in self.checks)


# ---------------------------------------------------------------------------
# Canonical fixture layout for the literal case roots
# ---------------------------------------------------------------------------

def reset_case_root(root: Path) -> dict:
    """Owned-root reset: keep the marker and every driver's recorded process artifacts,
    rebuild only this driver's case content."""
    root = Path(root)
    owned = H.ensure_owned_root(root, DRIVER_ID)
    H.reset_owned_content(root)
    return {"root": str(root), "marker": H.MARKER_NAME, "adopted": owned.get("adopted", False)}


def case_paths(root: Path, destination_name: str = "destination") -> dict:
    root = Path(root)
    return {
        "root": root,
        "config": root / "config" / "line_backup_config.json",
        "run_log": root / "state" / "run_log.md",
        "state": root / "state" / "backup_state.json",
        "input_state": root / "input-state.json",
        "destination": root / destination_name,
        "evidence": root / "evidence",
        "counter": root / "dispatch-counter.jsonl",
        "dispatcher": root / "dispatcher.py",
        "source_evidence": root / "source-evidence.json",
    }


def build_case_root(root: Path, state: dict, *, images: int = 57, destination_name: str = "destination",
                    dispatcher: str = "returned", binding_kind: str = "fixture") -> dict:
    root = Path(root)
    F.write_canonical_root(root, state, destination_images=images, destination_name=destination_name,
                           config_extra={"backup_root": str(root)})
    paths = case_paths(root, destination_name)
    paths["source"] = F.source_evidence_record(root, name="source-evidence.json", binding_kind=binding_kind)
    if dispatcher == "returned":
        paths["dispatcher"] = H.write_dispatcher(paths["dispatcher"], outcome="RETURNED")
    elif dispatcher == "crash":
        paths["dispatcher"] = H.write_dispatcher(paths["dispatcher"], outcome="RETURNED", crash_after_dispatch=False)
    elif dispatcher == "blocking":
        paths["dispatcher"] = H.write_dispatcher(paths["dispatcher"], outcome="RETURNED", wait_parent=True,
                                                 started_barrier=root / "dispatch-started.barrier")
    elif dispatcher == "none":
        paths["dispatcher"] = None
    else:
        raise ValueError(dispatcher)
    paths["counter"].write_text("", encoding="utf-8")
    return paths


def install_prestate(paths: dict, state: dict) -> dict:
    write_json(paths["input_state"], state)
    info = F.install_state(paths["root"], state)
    return {"input_state": sha(paths["input_state"]), "installed": info}


def base_args(paths: dict, *, test_mode: bool = True) -> list[str]:
    args = ["--project-root", str(paths["root"]), "--config", str(paths["config"]),
            "--run-log", str(paths["run_log"]), "--state", str(paths["state"])]
    if test_mode:
        args.append("--test-mode")
    return args


def tx_args(paths: dict, operation: str, *extra: str, test_mode: bool = True) -> list[str]:
    return ["transaction", operation] + base_args(paths, test_mode=test_mode) + list(extra)


def verify_args(paths: dict, evidence_dir: Path, *extra: str, test_mode: bool = True) -> list[str]:
    args = ["verify-only"] + base_args(paths, test_mode=test_mode) + [
        "--destination", str(paths["destination"]), "--group-key", GROUP,
        "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
        "--expected-images", str(FP57["expected_images"]), "--evidence-dir", str(evidence_dir)]
    args.extend(extra)
    return args


def code_of(record: dict) -> str | None:
    result = record.get("result")
    if not isinstance(result, dict):
        return None
    return result.get("result") or result.get("failure_class")


def counter_lines(paths: dict) -> int:
    counter = paths["counter"]
    if not counter.exists():
        return 0
    return len([line for line in counter.read_text(encoding="utf-8").splitlines() if line.strip()])


def wait_file(path: Path, *, timeout: float = 60.0) -> bool:
    return H.wait_for(lambda: Path(path).exists(), timeout=timeout)


def complete_dispatch_prestate(paths: dict, run_id: str, owner: str, *, revision: int = 2,
                               binding_path: Path | None = None, group: str = GROUP) -> dict:
    """Revision-2 pre-state with a completed dispatch record and a schema-legal binding event."""
    reference = f"fixture:{binding_path.name}:{H.sha256_file(binding_path)}" if binding_path else None
    run = F.completed_dispatch_run(run_id, owner, str(paths["destination"]), group=group)
    if reference:
        # Rev15 §15.2: the binding reference lives in the run's checkpoint-shaped events[]
        # evidence string; the product's own intent-committed event is that carrier (the
        # skill schema $defs/phase has no SOURCE_BINDING value, so no new phase is invented).
        run["events"][0]["evidence"] = reference
    state = F.fresh_state(revision=revision)
    state["runs"] = [run]
    state["current_run_id"] = run_id
    state["active_writer_id"] = owner
    if reference:
        state["verified_albums"] = []
    return state


def binding_reference(paths: dict) -> str:
    binding = paths["root"] / "binding-fixture.json"
    return f"fixture:binding-fixture.json:{H.sha256_file(binding)}"


# ---------------------------------------------------------------------------
# Case implementations
# ---------------------------------------------------------------------------

def case_01(case: Case, paths: dict) -> None:
    root, dest = paths["root"], paths["destination"]
    install_prestate(paths, F.fresh_state())
    case.cli("prepare", tx_args(paths, "prepare", "--run-id", "RUN-CASE-01", "--owner-id", "WRITER-CASE-01",
                                "--group-key", GROUP, "--start-date", FP57["start_date"],
                                "--end-date", FP57["end_date"], "--expected-images", "57",
                                "--destination", str(dest), "--source-evidence", str(paths["source_evidence"]),
                                "--dispatcher", str(paths["dispatcher"]), "--dispatch-counter", str(paths["counter"]),
                                "--dispatcher-outcome", "RETURNED", "--evidence-dir", str(paths["evidence"])))
    case.check("prepare.code", "PREPARED", code_of(case.processes[-1]))
    case.check("prepare.revision2", 2, (case.processes[-1]["result"] or {}).get("revision"))
    case.check("prepare.counter1", 1, counter_lines(paths))

    verify1 = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, verify1, "--run-id", "RUN-CASE-01"))
    v1 = case.processes[-1]["result"] or {}
    case.check("verify1.exit4", 4, case.processes[-1]["exit_code"])
    case.check("verify1.filesystem", "PASS", v1.get("filesystem_status"))
    case.check("verify1.recognized57", 57, v1.get("recognized_images"))
    case.check("verify1.not-overall-pass", True, v1.get("overall_status") != "PASS")

    commit = case.cli("commit", tx_args(paths, "commit", "--run-id", "RUN-CASE-01", "--expected-revision", "2",
                                        "--expected-owner-id", "WRITER-CASE-01",
                                        "--verification-json", str(verify1 / "result.json"),
                                        "--evidence-dir", str(paths["evidence"])))
    case.check("commit.code", "COMMITTED_VERIFICATION", code_of(commit))
    case.check("commit.revision3", 3, (commit["result"] or {}).get("revision"))

    finalize = case.cli("finalize", tx_args(paths, "finalize", "--run-id", "RUN-CASE-01", "--expected-revision", "3",
                                            "--expected-owner-id", "WRITER-CASE-01", "--outcome", "VERIFIED",
                                            "--verification-json", str(verify1 / "result.json"),
                                            "--evidence-dir", str(paths["evidence"])))
    case.check("finalize.code", "FINALIZED", code_of(finalize))
    state = read_json(paths["state"])
    run = state["runs"][0]
    entry = state["verified_albums"][0] if state["verified_albums"] else {}
    case.check("finalize.terminal", "VERIFIED", run.get("workflow_outcome"))
    case.check("finalize.released-owner", None, state.get("active_writer_id"))
    case.check("finalize.released-context", None, state.get("context_lock"))
    reference = entry.get("evidence")
    case.check("finalize.registry-reference", True,
               isinstance(reference, str) and any(isinstance(e, dict) and e.get("evidence") == reference
                                                  for e in run.get("events", [])))
    case.check("finalize.source-kind", "filesystem_verification", entry.get("source_kind"))

    verify2 = paths["evidence"] / "verify-2"
    case.cli("verify-2", verify_args(paths, verify2, "--run-id", "RUN-CASE-01"))
    v2 = case.processes[-1]["result"] or {}
    case.check("verify2.exit0", 0, case.processes[-1]["exit_code"])
    for axis in ("filesystem_status", "registry_status", "source_status", "state_status", "overall_status"):
        expected = "EXACT" if axis == "state_status" else ("PASS" if axis != "source_status" else "CONFIRMED")
        case.check(f"verify2.{axis}", expected, v2.get(axis))

    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(dest),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "SKIP_DUPLICATE", code_of(case.processes[-1]))
    case.check("duplicate.exit0", 0, case.processes[-1]["exit_code"])

    state_before = sha(paths["state"])
    case.cli("prepare-destination-2", tx_args(paths, "prepare", "--run-id", "RUN-CASE-01-B",
                                              "--owner-id", "WRITER-CASE-01-B", "--group-key", GROUP,
                                              "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                              "--expected-images", "57",
                                              "--destination", str(root / "destination-2"),
                                              "--source-evidence", str(paths["source_evidence"]),
                                              "--dispatcher", str(paths["dispatcher"]),
                                              "--dispatch-counter", str(paths["counter"]),
                                              "--evidence-dir", str(paths["evidence"] / "refusal")))
    case.check("prepare2.code", "CONFLICT_DUPLICATE_FINGERPRINT", code_of(case.processes[-1]))
    case.check("prepare2.exit4", 4, case.processes[-1]["exit_code"])
    case.check("prepare2.state-unchanged", state_before["sha256"], sha(paths["state"])["sha256"])
    case.check("prepare2.no-second-dispatch", 1, counter_lines(paths))

    case.cli("resume-terminal", tx_args(paths, "resume", "--run-id", "RUN-CASE-01", "--expected-revision", "4",
                                        "--expected-owner-id", "WRITER-CASE-01", "--no-dispatch",
                                        "--evidence-dir", str(paths["evidence"])))
    case.check("resume.code", "SKIP_TERMINAL", code_of(case.processes[-1]))
    case.check("resume.exit0", 0, case.processes[-1]["exit_code"])
    final = read_json(paths["state"])
    case.check("final.revision4", 4, final.get("revision"))
    case.check("final.runs1", 1, len(final["runs"]))
    case.check("final.albums1", 1, len(final["verified_albums"]))
    case.check("final.counter1", 1, counter_lines(paths))


def case_02(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    case.cli("prepare-crash", tx_args(paths, "prepare", "--run-id", "RUN-CASE-02", "--owner-id", "WRITER-CASE-02",
                                      "--group-key", GROUP, "--start-date", FP57["start_date"],
                                      "--end-date", FP57["end_date"], "--expected-images", "57",
                                      "--destination", str(paths["destination"]),
                                      "--source-evidence", str(paths["source_evidence"]),
                                      "--dispatcher", str(paths["dispatcher"]),
                                      "--dispatch-counter", str(paths["counter"]), "--crash-after-dispatch",
                                      "--evidence-dir", str(paths["evidence"])))
    case.check("prepare.code", "DISPATCHER_CRASH_AFTER_SIDE_EFFECT", code_of(case.processes[-1]))
    case.check("prepare.exit1", 1, case.processes[-1]["exit_code"])
    case.check("prepare.revision1", 1, (case.processes[-1]["result"] or {}).get("revision"))
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("state.revision1", 1, state.get("revision"))
    case.check("state.intent-committed", "INTENT_COMMITTED", run.get("intent_state"))
    case.check("state.not-attempted", "NOT_ATTEMPTED", run.get("dispatch_state"))
    case.check("state.trigger", "NOT_APPLICABLE", run["intent"].get("trigger_outcome"))
    case.check("state.dispatch-outcome", "NOT_ATTEMPTED", run["intent"].get("dispatch_outcome"))
    case.check("state.retry-false", False, run["intent"].get("save_all_retry_allowed"))
    case.check("counter1", 1, counter_lines(paths))

    case.cli("resume-1", tx_args(paths, "resume", "--run-id", "RUN-CASE-02", "--expected-revision", "1",
                                 "--expected-owner-id", "WRITER-CASE-02", "--no-dispatch",
                                 "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume1.code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("resume1.exit0", 0, rec["exit_code"])
    case.check("resume1.revision2", 2, (rec["result"] or {}).get("revision"))
    case.check("resume1.barrier", "BARRIER_COMMITTED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("resume1.replaced", True, (rec["result"] or {}).get("state_replaced"))
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("barrier.intent", "TRIGGER_UNKNOWN", run.get("intent_state"))
    case.check("barrier.dispatch", "UNKNOWN", run.get("dispatch_state"))
    case.check("barrier.trigger", "UNKNOWN", run["intent"].get("trigger_outcome"))
    case.check("barrier.dispatch-outcome", "UNKNOWN", run["intent"].get("dispatch_outcome"))
    case.check("barrier.retry-false", False, run["intent"].get("save_all_retry_allowed"))
    case.check("barrier.manual", True, run.get("manual_reconciliation_required"))
    case.check("barrier.reason", True, bool(run.get("reconciliation_reason")))
    case.check("barrier.reconciliations1", 1, len(run.get("reconciliations") or []))
    reconcile_path = paths["evidence"] / "reconcile.json"
    expected_reference = f"reconcile:reconcile.json:{H.sha256_file(reconcile_path)}"
    case.check("barrier.evidence-reference", expected_reference, (run.get("reconciliations") or [{}])[0].get("evidence"))

    before = sha(paths["state"])
    case.cli("resume-2", tx_args(paths, "resume", "--run-id", "RUN-CASE-02", "--expected-revision", "2",
                                 "--expected-owner-id", "WRITER-CASE-02", "--no-dispatch",
                                 "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume2.code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("resume2.reconciled", "ALREADY_RECONCILED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("resume2.no-write", before["sha256"], sha(paths["state"])["sha256"])

    case.cli("commit-refused", tx_args(paths, "commit", "--run-id", "RUN-CASE-02", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-02",
                                       "--verification-json", str(paths["evidence"] / "verify-1" / "result.json"),
                                       "--evidence-dir", str(paths["evidence"])))
    case.check("commit.code", "CONFLICT_UNRESOLVED_DISPATCH", code_of(case.processes[-1]))
    case.check("commit.exit4", 4, case.processes[-1]["exit_code"])
    case.check("commit.no-write", before["sha256"], sha(paths["state"])["sha256"])

    case.cli("finalize-safe-abort", tx_args(paths, "finalize", "--run-id", "RUN-CASE-02", "--expected-revision", "2",
                                            "--expected-owner-id", "WRITER-CASE-02", "--outcome", "SAFE_ABORT",
                                            "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("finalize.code", "FINALIZED", code_of(rec))
    case.check("finalize.exit0", 0, rec["exit_code"])
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("safe-abort.revision3", 3, state.get("revision"))
    case.check("safe-abort.no-registry", 0, len(state["verified_albums"]))
    case.check("safe-abort.barrier-preserved", "TRIGGER_UNKNOWN", run.get("intent_state"))
    case.check("safe-abort.released-owner", None, state.get("active_writer_id"))
    case.check("safe-abort.counter1", 1, counter_lines(paths))


def case_03(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    case.cli("prepare-unknown", tx_args(paths, "prepare", "--run-id", "RUN-CASE-03", "--owner-id", "WRITER-CASE-03",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--dispatcher-outcome", "UNKNOWN",
                                        "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("prepare.code", "DISPATCH_UNKNOWN", code_of(rec))
    case.check("prepare.exit1", 1, rec["exit_code"])
    case.check("prepare.revision2", 2, (rec["result"] or {}).get("revision"))
    case.check("prepare.counter1", 1, counter_lines(paths))
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("state.row4.intent", "TRIGGER_UNKNOWN", run.get("intent_state"))
    case.check("state.row4.dispatch", "UNKNOWN", run.get("dispatch_state"))

    before = sha(paths["state"])
    reconcile_before = sorted(p.name for p in paths["evidence"].glob("reconcile*.json"))
    case.cli("resume", tx_args(paths, "resume", "--run-id", "RUN-CASE-03", "--expected-revision", "2",
                               "--expected-owner-id", "WRITER-CASE-03", "--no-dispatch",
                               "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume.code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("resume.reconciled", "ALREADY_RECONCILED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("resume.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("resume.no-new-reconcile", reconcile_before,
               sorted(p.name for p in paths["evidence"].glob("reconcile*.json")))

    case.cli("commit-refused", tx_args(paths, "commit", "--run-id", "RUN-CASE-03", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-03",
                                       "--verification-json", str(paths["evidence"] / "verify-1" / "result.json"),
                                       "--evidence-dir", str(paths["evidence"])))
    case.check("commit.code", "CONFLICT_UNRESOLVED_DISPATCH", code_of(case.processes[-1]))
    case.check("counter1", 1, counter_lines(paths))


def case_04(case: Case, paths: dict) -> None:
    state = F.verified_state("RUN-CASE-04", "WRITER-CASE-04", str(paths["destination"]),
                             binding_path=paths["root"] / "binding-fixture.json", revision=2)
    install_prestate(paths, state)
    before = sha(paths["state"])
    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "SKIP_DUPLICATE", code_of(case.processes[-1]))
    case.check("duplicate.exit0", 0, case.processes[-1]["exit_code"])

    case.cli("resume-terminal", tx_args(paths, "resume", "--run-id", "RUN-CASE-04", "--expected-revision", "2",
                                        "--expected-owner-id", "WRITER-CASE-04", "--no-dispatch",
                                        "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume.code", "SKIP_TERMINAL", code_of(rec))
    case.check("resume.exit0", 0, rec["exit_code"])
    case.check("resume.reconciliation-state", "NONE", (rec["result"] or {}).get("reconciliation_state"))
    case.check("resume.no-write", before["sha256"], sha(paths["state"])["sha256"])

    case.cli("resume-adapter", tx_args(paths, "resume", "--run-id", "RUN-CASE-04", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-04",
                                       "--dispatcher", str(paths["dispatcher"]),
                                       "--dispatch-counter", str(paths["counter"]),
                                       "--evidence-dir", str(paths["evidence"] / "adapter")))
    case.check("resume-adapter.code", "INVALID_INPUT", code_of(case.processes[-1]))
    case.check("resume-adapter.exit2", 2, case.processes[-1]["exit_code"])
    case.check("resume-adapter.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_05(case: Case, paths: dict) -> None:
    state = complete_dispatch_prestate(paths, "RUN-CASE-05", "WRITER-CASE-05", revision=1,
                                       binding_path=paths["root"] / "binding-fixture.json")
    install_prestate(paths, state)
    chain = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, chain, "--run-id", "RUN-CASE-05"))
    case.check("verify1.chain-run", "RUN-CASE-05", (case.processes[-1]["result"] or {}).get("run_id"))
    barrier = paths["root"] / "commit-ready.barrier"
    if barrier.exists():
        barrier.unlink()
    if Path(str(barrier) + ".ready").exists():
        Path(str(barrier) + ".ready").unlink()

    handle_a = case.start("commit-a", tx_args(paths, "commit", "--run-id", "RUN-CASE-05",
                                              "--expected-revision", "1", "--expected-owner-id", "WRITER-CASE-05",
                                              "--verification-json", str(chain / "result.json"),
                                              "--evidence-dir", str(paths["evidence"] / "commit-a"),
                                              "--pause-at", "COMMIT_BEFORE_REPLACE",
                                              "--barrier-file", str(barrier)))
    handle_b = case.start("commit-b", tx_args(paths, "commit", "--run-id", "RUN-CASE-05",
                                              "--expected-revision", "1", "--expected-owner-id", "WRITER-CASE-05",
                                              "--verification-json", str(chain / "result.json"),
                                              "--evidence-dir", str(paths["evidence"] / "commit-b"),
                                              "--pause-at", "COMMIT_BEFORE_REPLACE",
                                              "--barrier-file", str(barrier)))
    case.check("commit.barrier-reached", True, wait_file(Path(str(barrier) + ".ready"), timeout=60.0))
    time.sleep(0.3)
    barrier.write_text("", encoding="utf-8")
    result_a = case.collect(handle_a, timeout=60.0)
    result_b = case.collect(handle_b, timeout=60.0)
    got = sorted([code_of(result_a) or "NONE", code_of(result_b) or "NONE"])
    case.check("commit.outcomes", ["COMMITTED_VERIFICATION", "CONFLICT_STALE_REVISION"], got)
    case.check("commit.one-replacement", 1, len([code for code in got if code == "COMMITTED_VERIFICATION"]))
    state = read_json(paths["state"])
    case.check("commit.final-revision2", 2, state.get("revision"))
    case.check("counter0", 0, counter_lines(paths))


def case_06(case: Case, paths: dict) -> None:
    state = complete_dispatch_prestate(paths, "RUN-CASE-06", "WRITER-CASE-06", revision=2,
                                       binding_path=paths["root"] / "binding-fixture.json")
    install_prestate(paths, state)
    chain = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, chain, "--run-id", "RUN-CASE-06"))
    before = sha(paths["state"])
    case.cli("commit-wrong-owner", tx_args(paths, "commit", "--run-id", "RUN-CASE-06", "--expected-revision", "2",
                                           "--expected-owner-id", "WRITER-CASE-06-WRONG",
                                           "--verification-json", str(chain / "result.json"),
                                           "--evidence-dir", str(paths["evidence"])))
    case.check("commit.code", "CONFLICT_OWNER_RUN", code_of(case.processes[-1]))
    case.check("commit.exit4", 4, case.processes[-1]["exit_code"])
    case.check("commit.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("commit.revision2", 2, read_json(paths["state"]).get("revision"))


def case_07(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    barrier = paths["root"] / "acquire-ready.barrier"
    for leftover in (barrier, Path(str(barrier) + ".ready")):
        if leftover.exists():
            leftover.unlink()
    handle_a = case.start("prepare-a", tx_args(paths, "prepare", "--run-id", "RUN-CASE-07-A",
                                               "--owner-id", "WRITER-CASE-07-A", "--group-key", GROUP,
                                               "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                               "--expected-images", "57", "--destination", str(paths["destination"]),
                                               "--source-evidence", str(paths["source_evidence"]),
                                               "--dispatcher", str(paths["dispatcher"]),
                                               "--dispatch-counter", str(paths["counter"]),
                                               "--evidence-dir", str(paths["evidence"] / "a"),
                                               "--pause-at", "ACQUIRE_BEFORE_LOCK",
                                               "--barrier-file", str(barrier)))
    handle_b = case.start("prepare-b", tx_args(paths, "prepare", "--run-id", "RUN-CASE-07-B",
                                               "--owner-id", "WRITER-CASE-07-B", "--group-key", GROUP,
                                               "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                               "--expected-images", "57", "--destination", str(paths["destination"]),
                                               "--source-evidence", str(paths["source_evidence"]),
                                               "--dispatcher", str(paths["dispatcher"]),
                                               "--dispatch-counter", str(paths["counter"]),
                                               "--evidence-dir", str(paths["evidence"] / "b"),
                                               "--pause-at", "ACQUIRE_BEFORE_LOCK",
                                               "--barrier-file", str(barrier)))
    case.check("acquire.barrier-reached", True, wait_file(Path(str(barrier) + ".ready"), timeout=60.0))
    time.sleep(0.3)
    subprocess.run(["/usr/bin/touch", str(barrier)], check=False)
    result_a = case.collect(handle_a, timeout=60.0)
    result_b = case.collect(handle_b, timeout=60.0)
    got = sorted([code_of(result_a) or "NONE", code_of(result_b) or "NONE"])
    case.check("prepare.outcomes", ["CONFLICT_ACTIVE_RUN", "PREPARED"], got)
    winner = result_a if code_of(result_a) == "PREPARED" else result_b
    case.check("prepare.winner-revision2", 2, (winner.get("result") or {}).get("revision"))
    state = read_json(paths["state"])
    case.check("prepare.one-run", 1, len(state["runs"]))
    case.check("prepare.counter1", 1, counter_lines(paths))
    lock = paths["state"].parent / ".line-backup-state.lock"
    case.check("prepare.lock-not-held", True, _lock_released(lock))


def _lock_released(lock: Path) -> bool:
    if not lock.exists():
        return True
    import fcntl
    with lock.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return True
        except OSError:
            return False


def case_08(case: Case, paths: dict) -> None:
    state = complete_dispatch_prestate(paths, "RUN-CASE-08", "WRITER-CASE-08", revision=2,
                                       binding_path=paths["root"] / "binding-fixture.json")
    install_prestate(paths, state)
    chain = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, chain, "--run-id", "RUN-CASE-08"))
    before = sha(paths["state"])
    case.cli("commit-fault", tx_args(paths, "commit", "--run-id", "RUN-CASE-08", "--expected-revision", "2",
                                     "--expected-owner-id", "WRITER-CASE-08",
                                     "--verification-json", str(chain / "result.json"),
                                     "--evidence-dir", str(paths["evidence"]),
                                     "--storage-fault", "WRITE_BEFORE_REPLACE"))
    rec = case.processes[-1]
    case.check("commit.code", "WRITE_BEFORE_REPLACE", code_of(rec))
    case.check("commit.exit1", 1, rec["exit_code"])
    case.check("commit.no-write", before["sha256"], sha(paths["state"])["sha256"])
    state = read_json(paths["state"])
    case.check("commit.revision2", 2, state.get("revision"))
    case.check("commit.no-verification", None, state["runs"][0].get("verification"))


def case_09(case: Case, paths: dict) -> None:
    state = complete_dispatch_prestate(paths, "RUN-CASE-09", "WRITER-CASE-09", revision=2,
                                       binding_path=paths["root"] / "binding-fixture.json")
    install_prestate(paths, state)
    chain = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, chain, "--run-id", "RUN-CASE-09"))
    case.cli("finalize-fault", tx_args(paths, "finalize", "--run-id", "RUN-CASE-09", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-09", "--outcome", "VERIFIED",
                                       "--verification-json", str(chain / "result.json"),
                                       "--evidence-dir", str(paths["evidence"]),
                                       "--storage-fault", "READBACK_UNCERTAIN_AFTER_REPLACE"))
    rec = case.processes[-1]
    case.check("finalize.code", "READBACK_UNCERTAIN", code_of(rec))
    case.check("finalize.exit1", 1, rec["exit_code"])
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("finalize.terminal", "VERIFIED", run.get("workflow_outcome"))
    case.check("finalize.revision3", 3, state.get("revision"))
    case.check("finalize.released-owner", None, state.get("active_writer_id"))
    case.check("finalize.released-context", None, state.get("context_lock"))
    case.check("counter0", 0, counter_lines(paths))

    case.cli("resume", tx_args(paths, "resume", "--run-id", "RUN-CASE-09", "--expected-revision", "3",
                               "--expected-owner-id", "WRITER-CASE-09", "--no-dispatch",
                               "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume.code", "SKIP_TERMINAL", code_of(rec))
    case.check("resume.exit0", 0, rec["exit_code"])
    case.check("resume.no-replacement", False, (rec["result"] or {}).get("state_replaced"))
    case.check("resume.counter0", 0, counter_lines(paths))


def case_10(case: Case, paths: dict) -> None:
    state = complete_dispatch_prestate(paths, "RUN-CASE-10", "WRITER-CASE-10", revision=2,
                                       binding_path=paths["root"] / "binding-fixture.json")
    install_prestate(paths, state)
    chain = paths["evidence"] / "verify-1"
    case.cli("verify-1", verify_args(paths, chain, "--run-id", "RUN-CASE-10"))
    case.cli("finalize-verified", tx_args(paths, "finalize", "--run-id", "RUN-CASE-10", "--expected-revision", "2",
                                          "--expected-owner-id", "WRITER-CASE-10", "--outcome", "VERIFIED",
                                          "--verification-json", str(chain / "result.json"),
                                          "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("finalize.code", "FINALIZED", code_of(rec))
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("finalize.revision3", 3, state.get("revision"))
    case.check("finalize.workflow", "VERIFIED", run.get("workflow_outcome"))
    case.check("finalize.registry1", 1, len(state["verified_albums"]))
    case.check("finalize.released-owner", None, state.get("active_writer_id"))
    case.check("finalize.released-context", None, state.get("context_lock"))
    consumed = read_json(chain / "result.json")
    case.check("finalize.verification-consumed", True,
               isinstance(run.get("verification"), dict)
               and run["verification"].get("outcome") == "PASS"
               and run["verification"].get("regular_files") == consumed.get("recognized_images"))

    # Subcase 10B: a separate isolated revision-2 state, SAFE_ABORT finalization.
    state_b = complete_dispatch_prestate(paths, "RUN-CASE-10B", "WRITER-CASE-10B", revision=2,
                                         binding_path=paths["root"] / "binding-fixture.json")
    run_b = state_b["runs"][0]
    run_b["intent_state"] = "TRIGGER_UNKNOWN"
    run_b["dispatch_state"] = "UNKNOWN"
    run_b["intent"]["trigger_outcome"] = "UNKNOWN"
    run_b["intent"]["dispatch_outcome"] = "UNKNOWN"
    run_b["manual_reconciliation_required"] = True
    run_b["reconciliation_reason"] = "fixture unresolved dispatch barrier"
    install_prestate(paths, state_b)
    case.cli("finalize-10b", tx_args(paths, "finalize", "--run-id", "RUN-CASE-10B", "--expected-revision", "2",
                                     "--expected-owner-id", "WRITER-CASE-10B", "--outcome", "SAFE_ABORT",
                                     "--evidence-dir", str(paths["evidence"] / "10b")))
    rec = case.processes[-1]
    case.check("10b.code", "FINALIZED", code_of(rec))
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("10b.revision3", 3, state.get("revision"))
    case.check("10b.no-registry", 0, len(state["verified_albums"]))
    case.check("10b.barrier-preserved", "TRIGGER_UNKNOWN", run.get("intent_state"))
    case.check("10b.released-owner", None, state.get("active_writer_id"))
    case.check("10b.released-context", None, state.get("context_lock"))
    case.check("counter0", 0, counter_lines(paths))


def _legacy_run(run_id: str, destination: str, *, group: str = GROUP, outcome: str = "SAFE_ABORT") -> dict:
    """Legacy-shaped run (no contract_revision, no RC2 axes) used by Cases 11/12/25."""
    return {"run_id": run_id, "mode": "backup_one", "group_key": group, "album_id": None,
            "fingerprint": dict(FP57), "observed_title": group.rsplit(":", 1)[-1], "title_confidence": "HIGH",
            "destination": destination, "destination_initially_empty": True,
            "workflow_outcome": outcome, "phase": outcome,
            "checkpoint": {"phase": outcome, "at": "2026-09-16T00:00:00Z", "evidence": "fixture legacy checkpoint"},
            "events": [], "reconciliations": [], "recovery_used": {}, "runtime_errors": [],
            "verification": None, "stop_reason": None, "batch_id": None}


def _status_input(case_id: str, scenario: str) -> dict:
    return {"schema_version": 2, "case_id": case_id, "scenario": scenario,
            "note": "executable status fixture; facts are driver-authored"}


def case_11(case: Case, paths: dict) -> None:
    state = F.fresh_state(revision=7)
    state["runs"] = [_legacy_run("RUN-CASE-11", str(paths["destination"]))]
    install_prestate(paths, state)
    before = sha(paths["state"])
    status_in = paths["root"] / "status-input.json"
    status_out = paths["root"] / "status-output.json"
    write_json(status_in, _status_input("11", "legacy-no-source"))
    case.cli("status", ["status", "evaluate", "--input", str(status_in), "--output", str(status_out)])
    status = case.processes[-1]["result"] or {}
    case.check("status.exit0", 0, case.processes[-1]["exit_code"])
    case.check("status.primary", "UNKNOWN", status.get("primary_outcome_status"))
    case.check("status.implementation", "COMPLETE", status.get("implementation_status"))
    case.check("status.core", "BLOCKED", status.get("core_acceptance_status"))
    case.check("status.required", "PASS", status.get("required_verification_status"))
    case.check("status.independent", "PENDING", status.get("independent_acceptance_status"))
    case.check("status.closure", "CORE_ACCEPTANCE_BLOCKED", status.get("task_closure_status"))
    case.check("status.blocker", "SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE", status.get("blocker"))
    case.check("status.evidence-basis", "scenario_table_non_acceptance", status.get("evidence_basis"))

    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "NEEDS_RECONCILIATION", code_of(case.processes[-1]))
    case.check("duplicate.exit4", 4, case.processes[-1]["exit_code"])
    case.check("duplicate.no-write", before["sha256"], sha(paths["state"])["sha256"])


def case_12(case: Case, paths: dict) -> None:
    state = F.fresh_state(revision=4)
    entry = {"group_key": GROUP, "fingerprint": dict(FP57), "verified_run_id": "RUN-CASE-12-A",
             "destinations": [str(paths["destination"])], "source_kind": "filesystem_verification",
             "evidence": "fixture:binding-fixture.json:" + "0" * 64}
    duplicate = dict(entry, verified_run_id="RUN-CASE-12-B")
    state["verified_albums"] = [entry, duplicate]
    install_prestate(paths, state)
    before = sha(paths["state"])
    status_in = paths["root"] / "status-input.json"
    status_out = paths["root"] / "status-output.json"
    write_json(status_in, _status_input("12", "contradictory-axes"))
    case.cli("status", ["status", "evaluate", "--input", str(status_in), "--output", str(status_out)])
    status = case.processes[-1]["result"] or {}
    case.check("status.exit0", 0, case.processes[-1]["exit_code"])
    case.check("status.primary", "NOT_ACHIEVED", status.get("primary_outcome_status"))
    case.check("status.implementation", "IN_PROGRESS", status.get("implementation_status"))
    case.check("status.core", "FAIL", status.get("core_acceptance_status"))
    case.check("status.required", "NOT_RUN", status.get("required_verification_status"))
    case.check("status.independent", "PENDING", status.get("independent_acceptance_status"))
    case.check("status.closure", "FIX_REQUIRED", status.get("task_closure_status"))
    case.check("status.blocker", "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION", status.get("blocker"))
    case.check("status.evidence-basis", "scenario_table_non_acceptance", status.get("evidence_basis"))

    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "CONFLICT_DUPLICATE", code_of(case.processes[-1]))
    case.check("duplicate.exit4", 4, case.processes[-1]["exit_code"])
    case.check("duplicate.no-write", before["sha256"], sha(paths["state"])["sha256"])


def case_13(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    before = sha(paths["state"])
    case.cli("prepare-no-source", tx_args(paths, "prepare", "--run-id", "RUN-CASE-13", "--owner-id", "WRITER-CASE-13",
                                          "--group-key", GROUP, "--start-date", FP57["start_date"],
                                          "--end-date", FP57["end_date"], "--expected-images", "57",
                                          "--destination", str(paths["destination"]),
                                          "--dispatcher", str(paths["dispatcher"]),
                                          "--dispatch-counter", str(paths["counter"]),
                                          "--evidence-dir", str(paths["evidence"])))
    case.check("prepare.code", "MISSING_SOURCE_EVIDENCE", code_of(case.processes[-1]))
    case.check("prepare.exit2", 2, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_14(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    bad = F.source_evidence_record(paths["root"], name="source-evidence-bad.json",
                                   fp={"start_date": FP57["start_date"], "end_date": FP57["end_date"],
                                       "expected_images": 56})
    before = sha(paths["state"])
    case.cli("prepare-bad-source", tx_args(paths, "prepare", "--run-id", "RUN-CASE-14", "--owner-id", "WRITER-CASE-14",
                                           "--group-key", GROUP, "--start-date", FP57["start_date"],
                                           "--end-date", FP57["end_date"], "--expected-images", "57",
                                           "--destination", str(paths["destination"]),
                                           "--source-evidence", str(bad["path"]),
                                           "--dispatcher", str(paths["dispatcher"]),
                                           "--dispatch-counter", str(paths["counter"]),
                                           "--evidence-dir", str(paths["evidence"])))
    case.check("prepare.code", "INVALID_SOURCE_EVIDENCE", code_of(case.processes[-1]))
    case.check("prepare.exit2", 2, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_15(case: Case, paths: dict) -> None:
    state = F.verified_state("RUN-CASE-15", "WRITER-CASE-15", str(paths["destination"]),
                             binding_path=paths["root"] / "binding-fixture.json", revision=3)
    install_prestate(paths, state)
    before = sha(paths["state"])
    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "SKIP_DUPLICATE", code_of(case.processes[-1]))
    case.cli("prepare-refused", tx_args(paths, "prepare", "--run-id", "RUN-CASE-15-B", "--owner-id", "WRITER-CASE-15-B",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--evidence-dir", str(paths["evidence"] / "refusal")))
    case.check("prepare.code", "CONFLICT_DUPLICATE", code_of(case.processes[-1]))
    case.check("prepare.exit4", 4, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_16(case: Case, paths: dict) -> None:
    state = F.verified_state("RUN-CASE-16", "WRITER-CASE-16", str(paths["root"] / "destination-other"),
                             binding_path=paths["root"] / "binding-fixture.json", revision=3)
    install_prestate(paths, state)
    before = sha(paths["state"])
    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "CONFLICT_DUPLICATE_FINGERPRINT", code_of(case.processes[-1]))
    case.check("duplicate.exit4", 4, case.processes[-1]["exit_code"])
    case.cli("prepare-refused", tx_args(paths, "prepare", "--run-id", "RUN-CASE-16-B", "--owner-id", "WRITER-CASE-16-B",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--evidence-dir", str(paths["evidence"] / "refusal")))
    case.check("prepare.code", "CONFLICT_DUPLICATE_FINGERPRINT", code_of(case.processes[-1]))
    case.check("prepare.exit4", 4, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])


def case_17(case: Case, paths: dict) -> None:
    state = F.fresh_state(revision=5)
    state["runs"] = [F.make_run("RUN-CASE-17-HIST", "WRITER-CASE-17-HIST", str(paths["destination"]),
                                fp={"start_date": FP57["start_date"], "end_date": FP57["end_date"],
                                    "expected_images": 56},
                                workflow_outcome="IN_PROGRESS")]
    install_prestate(paths, state)
    before = sha(paths["state"])
    case.cli("duplicate", tx_args(paths, "duplicate-check", "--group-key", GROUP,
                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                  "--evidence-dir", str(paths["evidence"])))
    case.check("duplicate.code", "AMBIGUOUS_FINGERPRINT", code_of(case.processes[-1]))
    case.check("duplicate.exit4", 4, case.processes[-1]["exit_code"])
    case.cli("prepare-refused", tx_args(paths, "prepare", "--run-id", "RUN-CASE-17-B", "--owner-id", "WRITER-CASE-17-B",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--evidence-dir", str(paths["evidence"] / "refusal")))
    case.check("prepare.code", "AMBIGUOUS_FINGERPRINT", code_of(case.processes[-1]))
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_18(case: Case, paths: dict) -> None:
    historical = F.make_run("RUN-CASE-18-HIST", "WRITER-CASE-18-HIST", str(paths["destination"]))
    state = F.fresh_state(revision=6)
    state["runs"] = [historical]
    install_prestate(paths, state)
    before = sha(paths["state"])
    case.cli("prepare-refused", tx_args(paths, "prepare", "--run-id", "RUN-CASE-18", "--owner-id", "WRITER-CASE-18",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--evidence-dir", str(paths["evidence"] / "refusal")))
    case.check("prepare.code", "NEEDS_RECONCILIATION", code_of(case.processes[-1]))
    case.check("prepare.exit4", 4, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))

    released = dict(historical)
    released["reconciliations"] = [F.reconciliation_entry(historical, released=True)]
    state = F.fresh_state(revision=6)
    state["runs"] = [released]
    install_prestate(paths, state)
    case.cli("prepare-control", tx_args(paths, "prepare", "--run-id", "RUN-CASE-18-CTRL", "--owner-id", "WRITER-CASE-18-CTRL",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--evidence-dir", str(paths["evidence"] / "control")))
    rec = case.processes[-1]
    case.check("control.code", "PREPARED", code_of(rec))
    case.check("control.exit0", 0, rec["exit_code"])
    case.check("control.counter1", 1, counter_lines(paths))


def case_19(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    case.cli("prepare-unknown", tx_args(paths, "prepare", "--run-id", "RUN-CASE-19", "--owner-id", "WRITER-CASE-19",
                                        "--group-key", GROUP, "--start-date", FP57["start_date"],
                                        "--end-date", FP57["end_date"], "--expected-images", "57",
                                        "--destination", str(paths["destination"]),
                                        "--source-evidence", str(paths["source_evidence"]),
                                        "--dispatcher", str(paths["dispatcher"]),
                                        "--dispatch-counter", str(paths["counter"]),
                                        "--dispatcher-outcome", "UNKNOWN",
                                        "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("prepare.code", "DISPATCH_UNKNOWN", code_of(rec))
    case.check("prepare.revision2", 2, (rec["result"] or {}).get("revision"))
    case.check("prepare.counter1", 1, counter_lines(paths))

    case.cli("commit-refused", tx_args(paths, "commit", "--run-id", "RUN-CASE-19", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-19",
                                       "--verification-json", str(paths["evidence"] / "verify-1" / "result.json"),
                                       "--evidence-dir", str(paths["evidence"] / "commit")))
    case.check("commit.code", "CONFLICT_UNRESOLVED_DISPATCH", code_of(case.processes[-1]))
    case.check("commit.exit4", 4, case.processes[-1]["exit_code"])

    case.cli("finalize-safe-abort", tx_args(paths, "finalize", "--run-id", "RUN-CASE-19", "--expected-revision", "2",
                                            "--expected-owner-id", "WRITER-CASE-19", "--outcome", "SAFE_ABORT",
                                            "--evidence-dir", str(paths["evidence"] / "finalize")))
    rec = case.processes[-1]
    case.check("finalize.code", "FINALIZED", code_of(rec))
    case.check("finalize.exit0", 0, rec["exit_code"])
    state = read_json(paths["state"])
    run = state["runs"][0]
    case.check("finalize.revision3", 3, state.get("revision"))
    case.check("finalize.no-registry", 0, len(state["verified_albums"]))
    case.check("finalize.barrier-preserved", "TRIGGER_UNKNOWN", run.get("intent_state"))
    case.check("finalize.counter1", 1, counter_lines(paths))


def case_20(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    handle = case.start("prepare-killed", tx_args(paths, "prepare", "--run-id", "RUN-CASE-20",
                                                  "--owner-id", "WRITER-CASE-20", "--group-key", GROUP,
                                                  "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                                                  "--expected-images", "57", "--destination", str(paths["destination"]),
                                                  "--source-evidence", str(paths["source_evidence"]),
                                                  "--dispatcher", str(paths["dispatcher"]),
                                                  "--dispatch-counter", str(paths["counter"]),
                                                  "--evidence-dir", str(paths["evidence"])))
    started = paths["root"] / "dispatch-started.barrier"
    case.check("dispatch.started", True, wait_file(started, timeout=60.0))
    state_bytes = paths["state"].read_bytes()
    state_sha = hashlib.sha256(state_bytes).hexdigest()
    state = json.loads(state_bytes.decode("utf-8"))
    run = state["runs"][0]
    case.check("kill-window.revision1", 1, state.get("revision"))
    case.check("kill-window.intent", "INTENT_COMMITTED", run.get("intent_state"))
    case.check("kill-window.dispatch", "NOT_ATTEMPTED", run.get("dispatch_state"))
    case.check("kill-window.dispatch-outcome", "NOT_ATTEMPTED", run["intent"].get("dispatch_outcome"))
    case.check("kill-window.counter1", 1, counter_lines(paths))

    proc = handle["proc"]
    time.sleep(0.2)
    os.kill(proc.pid, signal.SIGKILL)
    kill_record = {"pid": proc.pid, "signal": "SIGKILL", "at": time.time()}
    try:
        stdout, stderr = proc.communicate(timeout=10)
        kill_record["returncode"] = proc.returncode
    except subprocess.TimeoutExpired:
        kill_record["returncode"] = None
        stdout = stderr = ""
    case.check("kill.signal", -signal.SIGKILL, proc.returncode)

    entries = H.counter_entries(paths["counter"])
    dispatcher_pid = entries[0].get("pid") if entries else None
    orphan_gone = True
    if dispatcher_pid:
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            try:
                os.kill(dispatcher_pid, 0)
                time.sleep(0.25)
            except ProcessLookupError:
                break
        else:
            orphan_gone = False
            try:
                os.kill(dispatcher_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    kill_record["orphan_reparented_and_exited"] = orphan_gone
    kill_record["orphan_pid"] = dispatcher_pid
    write_json(paths["root"] / "kill-record.json", kill_record)
    case.check("kill.orphan-self-exit", True, orphan_gone)

    case.check("aftermath.counter1", 1, counter_lines(paths))
    case.check("aftermath.state-bytes", state_sha, sha(paths["state"])["sha256"])
    state = read_json(paths["state"])
    case.check("aftermath.revision1", 1, state.get("revision"))
    case.check("aftermath.retry-false", False, state["runs"][0]["intent"].get("save_all_retry_allowed"))
    state_dir_names = sorted(p.name for p in paths["state"].parent.iterdir())
    case.check("aftermath.state-dir", [".line-backup-state.lock", "backup_state.json", "run_log.md"],
               state_dir_names)
    case.check("aftermath.lock-empty", 0, (paths["state"].parent / ".line-backup-state.lock").stat().st_size)

    case.cli("resume", tx_args(paths, "resume", "--run-id", "RUN-CASE-20", "--expected-revision", "1",
                               "--expected-owner-id", "WRITER-CASE-20", "--no-dispatch",
                               "--evidence-dir", str(paths["evidence"])))
    rec = case.processes[-1]
    case.check("resume.code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("resume.barrier", "BARRIER_COMMITTED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("resume.revision2", 2, (rec["result"] or {}).get("revision"))
    state = read_json(paths["state"])
    case.check("resume.reconciliations1", 1, len(state["runs"][0].get("reconciliations") or []))
    case.check("resume.counter1", 1, counter_lines(paths))

    case.cli("commit-refused", tx_args(paths, "commit", "--run-id", "RUN-CASE-20", "--expected-revision", "2",
                                       "--expected-owner-id", "WRITER-CASE-20",
                                       "--verification-json", str(paths["evidence"] / "verify-1" / "result.json"),
                                       "--evidence-dir", str(paths["evidence"] / "commit")))
    case.check("commit.code", "CONFLICT_UNRESOLVED_DISPATCH", code_of(case.processes[-1]))
    case.check("commit.exit4", 4, case.processes[-1]["exit_code"])


def case_21(case: Case, paths: dict) -> None:
    install_prestate(paths, F.fresh_state())
    before = sha(paths["state"])
    case.cli("prepare-no-dispatcher", tx_args(paths, "prepare", "--run-id", "RUN-CASE-21", "--owner-id", "WRITER-CASE-21",
                                              "--group-key", GROUP, "--start-date", FP57["start_date"],
                                              "--end-date", FP57["end_date"], "--expected-images", "57",
                                              "--destination", str(paths["destination"]),
                                              "--source-evidence", str(paths["source_evidence"]),
                                              "--evidence-dir", str(paths["evidence"])))
    case.check("prepare.code", "MISSING_DISPATCHER", code_of(case.processes[-1]))
    case.check("prepare.exit2", 2, case.processes[-1]["exit_code"])
    case.check("prepare.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("counter0", 0, counter_lines(paths))


def case_22(case: Case, paths: dict) -> None:
    subcases = {}
    for label in ("22a", "22b", "22c", "22d", "22e", "22f"):
        state = complete_dispatch_prestate(paths, "RUN-CASE-22", "WRITER-CASE-22", revision=2,
                                           binding_path=paths["root"] / "binding-fixture.json")
        install_prestate(paths, state)
        evidence = paths["evidence"] / label
        evidence.mkdir(parents=True, exist_ok=True)
        before = sha(paths["state"])
        verification = evidence / "result.json"
        if label == "22a":
            write_json(verification, {"schema_version": 1, "mode": "verify_only", "run_id": "RUN-CASE-22",
                                      "group_key": GROUP, "fingerprint": dict(FP57),
                                      "destination": str(paths["destination"]), "filesystem_status": "PASS",
                                      "recognized_images": 57, "expected_images": 57, "overall_status": "PASS",
                                      "exit_code": 0, "artifact_readback": "PASS"})
        elif label == "22b":
            empty = paths["root"] / "empty-destination"
            empty.mkdir(parents=True, exist_ok=True)
            args = ["verify-only"] + base_args(paths) + ["--destination", str(empty), "--group-key", GROUP,
                                                         "--start-date", FP57["start_date"],
                                                         "--end-date", FP57["end_date"], "--expected-images", "57",
                                                         "--run-id", "RUN-CASE-22", "--evidence-dir", str(evidence)]
            case.cli("22b-verify", args)
            case.check("22b.verify-fail", "FAIL", (case.processes[-1]["result"] or {}).get("filesystem_status"))
        elif label == "22c":
            write_json(verification, {})
        elif label == "22d":
            case.cli("22d-verify", verify_args(paths, evidence, "--run-id", "RUN-CASE-22-OTHER"))
        elif label == "22e":
            result = {"schema_version": 1, "mode": "verify_only", "run_id": "RUN-CASE-22", "group_key": GROUP,
                      "fingerprint": dict(FP57), "destination": str(paths["destination"]),
                      "filesystem_status": "PASS", "recognized_images": 57, "expected_images": 57,
                      "overall_status": "PASS", "exit_code": 0, "artifact_readback": "PASS"}
            write_chain(evidence, result)
            manifest = read_json(evidence / "manifest.json")
            manifest["result_summary"] = dict(manifest["result_summary"], overall_status="NOT_ACHIEVED")
            write_json(evidence / "manifest.json", manifest)
        elif label == "22f":
            case.cli("22f-verify", verify_args(paths, evidence, "--run-id", "RUN-CASE-22"))
            blob = (evidence / "result.json").read_bytes()
            (evidence / "result.json").write_bytes(blob + b" ")
        case.cli(f"finalize-{label}", tx_args(paths, "finalize", "--run-id", "RUN-CASE-22",
                                              "--expected-revision", "2", "--expected-owner-id", "WRITER-CASE-22",
                                              "--outcome", "VERIFIED", "--verification-json", str(verification),
                                              "--evidence-dir", str(paths["evidence"] / f"{label}-refusal")))
        record = case.processes[-1]
        expected = "VERIFICATION_RUN_MISMATCH" if label == "22d" else "INVALID_VERIFICATION_EVIDENCE"
        case.check(f"{label}.code", expected, code_of(record))
        case.check(f"{label}.exit4", 4, record["exit_code"])
        case.check(f"{label}.no-write", before["sha256"], sha(paths["state"])["sha256"])
        state = read_json(paths["state"])
        case.check(f"{label}.revision2", 2, state.get("revision"))
        case.check(f"{label}.registry0", 0, len(state["verified_albums"]))
        refusal = sorted(p.name for p in (paths["evidence"] / f"{label}-refusal").glob("*.json"))
        case.check(f"{label}.refusal-artifact", True, "result.json" in refusal)
        subcases[label] = True
    case.check("subcases", 6, len(subcases))


def case_23(case: Case, paths: dict) -> None:
    # 23a: WRITE_BEFORE_REPLACE on the intent replacement.
    install_prestate(paths, F.fresh_state())
    before = sha(paths["state"])
    case.cli("23a-fault", tx_args(paths, "prepare", "--run-id", "RUN-CASE-23A", "--owner-id", "WRITER-CASE-23A",
                                  "--group-key", GROUP, "--start-date", FP57["start_date"],
                                  "--end-date", FP57["end_date"], "--expected-images", "57",
                                  "--destination", str(paths["destination"]),
                                  "--source-evidence", str(paths["source_evidence"]),
                                  "--dispatcher", str(paths["dispatcher"]),
                                  "--dispatch-counter", str(paths["counter"]),
                                  "--storage-fault", "WRITE_BEFORE_REPLACE", "--storage-fault-slot", "intent",
                                  "--evidence-dir", str(paths["evidence"] / "23a")))
    rec = case.processes[-1]
    case.check("23a.code", "WRITE_BEFORE_REPLACE", code_of(rec))
    case.check("23a.exit1", 1, rec["exit_code"])
    case.check("23a.revision0", 0, (rec["result"] or {}).get("revision"))
    case.check("23a.counter0", 0, counter_lines(paths))
    case.check("23a.no-partial-write", before["sha256"], sha(paths["state"])["sha256"])
    case.cli("23a-retry", tx_args(paths, "prepare", "--run-id", "RUN-CASE-23A", "--owner-id", "WRITER-CASE-23A",
                                  "--group-key", GROUP, "--start-date", FP57["start_date"],
                                  "--end-date", FP57["end_date"], "--expected-images", "57",
                                  "--destination", str(paths["destination"]),
                                  "--source-evidence", str(paths["source_evidence"]),
                                  "--dispatcher", str(paths["dispatcher"]),
                                  "--dispatch-counter", str(paths["counter"]),
                                  "--evidence-dir", str(paths["evidence"] / "23a-retry")))
    rec = case.processes[-1]
    case.check("23a.retry-code", "PREPARED", code_of(rec))
    case.check("23a.retry-revision2", 2, (rec["result"] or {}).get("revision"))
    case.check("23a.retry-counter1", 1, counter_lines(paths))

    # 23b: READBACK_UNCERTAIN_AFTER_REPLACE on the intent replacement.
    install_prestate(paths, F.fresh_state())
    paths["counter"].write_text("", encoding="utf-8")
    case.cli("23b-fault", tx_args(paths, "prepare", "--run-id", "RUN-CASE-23B", "--owner-id", "WRITER-CASE-23B",
                                  "--group-key", GROUP, "--start-date", FP57["start_date"],
                                  "--end-date", FP57["end_date"], "--expected-images", "57",
                                  "--destination", str(paths["destination"]),
                                  "--source-evidence", str(paths["source_evidence"]),
                                  "--dispatcher", str(paths["dispatcher"]),
                                  "--dispatch-counter", str(paths["counter"]),
                                  "--storage-fault", "READBACK_UNCERTAIN_AFTER_REPLACE",
                                  "--storage-fault-slot", "intent",
                                  "--evidence-dir", str(paths["evidence"] / "23b")))
    rec = case.processes[-1]
    case.check("23b.code", "READBACK_UNCERTAIN", code_of(rec))
    case.check("23b.exit1", 1, rec["exit_code"])
    case.check("23b.revision1", 1, (rec["result"] or {}).get("revision"))
    case.check("23b.state-replaced", True, (rec["result"] or {}).get("state_replaced"))
    case.check("23b.dispatch-false", False, (rec["result"] or {}).get("dispatch_performed"))
    case.check("23b.counter0", 0, counter_lines(paths))
    state = read_json(paths["state"])
    case.check("23b.persisted-intent", "INTENT_COMMITTED", state["runs"][0].get("intent_state"))
    case.cli("23b-resume", tx_args(paths, "resume", "--run-id", "RUN-CASE-23B", "--expected-revision", "1",
                                   "--expected-owner-id", "WRITER-CASE-23B", "--no-dispatch",
                                   "--evidence-dir", str(paths["evidence"] / "23b-resume")))
    rec = case.processes[-1]
    case.check("23b.resume-code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("23b.resume-barrier", "BARRIER_COMMITTED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("23b.resume-revision2", 2, (rec["result"] or {}).get("revision"))
    case.cli("23b-commit", tx_args(paths, "commit", "--run-id", "RUN-CASE-23B", "--expected-revision", "2",
                                   "--expected-owner-id", "WRITER-CASE-23B",
                                   "--verification-json", str(paths["evidence"] / "23b" / "result.json"),
                                   "--evidence-dir", str(paths["evidence"] / "23b-commit")))
    case.check("23b.commit-code", "CONFLICT_UNRESOLVED_DISPATCH", code_of(case.processes[-1]))

    # 23c: WRITE_BEFORE_REPLACE on the post-dispatch replacement.
    install_prestate(paths, F.fresh_state())
    paths["counter"].write_text("", encoding="utf-8")
    case.cli("23c-fault", tx_args(paths, "prepare", "--run-id", "RUN-CASE-23C", "--owner-id", "WRITER-CASE-23C",
                                  "--group-key", GROUP, "--start-date", FP57["start_date"],
                                  "--end-date", FP57["end_date"], "--expected-images", "57",
                                  "--destination", str(paths["destination"]),
                                  "--source-evidence", str(paths["source_evidence"]),
                                  "--dispatcher", str(paths["dispatcher"]),
                                  "--dispatch-counter", str(paths["counter"]),
                                  "--storage-fault", "WRITE_BEFORE_REPLACE", "--storage-fault-slot", "dispatch",
                                  "--evidence-dir", str(paths["evidence"] / "23c")))
    rec = case.processes[-1]
    case.check("23c.code", "WRITE_BEFORE_REPLACE", code_of(rec))
    case.check("23c.exit1", 1, rec["exit_code"])
    case.check("23c.revision1", 1, (rec["result"] or {}).get("revision"))
    case.check("23c.dispatch-true", True, (rec["result"] or {}).get("dispatch_performed"))
    case.check("23c.counter1", 1, counter_lines(paths))
    case.cli("23c-resume", tx_args(paths, "resume", "--run-id", "RUN-CASE-23C", "--expected-revision", "1",
                                   "--expected-owner-id", "WRITER-CASE-23C", "--no-dispatch",
                                   "--evidence-dir", str(paths["evidence"] / "23c-resume")))
    rec = case.processes[-1]
    case.check("23c.resume-code", "RECOVERY_NO_DISPATCH", code_of(rec))
    case.check("23c.resume-barrier", "BARRIER_COMMITTED", (rec["result"] or {}).get("reconciliation_state"))
    case.check("23c.resume-counter1", 1, counter_lines(paths))


def _user_fact_record(paths: dict, *, part2: str = "confirmed", raw_group: str = F.GROUP_NAME,
                      evidence_file: Path | None = None, mutate_evidence: bool = False) -> Path:
    # Rev18 §16.4: raw_requested_group is the group *string* (no app prefix), compared
    # byte-for-byte with the requested string; 禎 U+798E is never equal to 楨 U+6968.
    root = paths["root"]
    answer_evidence = evidence_file or (root / "user-fact" / "answer-evidence.json")
    write_json(answer_evidence, {"question": "fixture", "answer": "yes", "recorded": "2026-09-16T00:00:00Z"})
    entry = {"path": str(answer_evidence), "bytes": answer_evidence.stat().st_size,
             "sha256": H.sha256_file(answer_evidence)}
    if mutate_evidence:
        entry["sha256"] = "0" * 64
    part_2 = {"text": "same source", "raw": "same source", "confirms_same_source": True,
              "confirmed_group_string": F.GROUP_NAME,
              "confirmed_album": "2024/05/13～05/17", "confirmed_expected_images": 57}
    if part2 == "unanswered":
        part_2 = {"text": "unknown", "raw": "unknown", "confirms_same_source": False,
                  "confirmed_group_string": None, "confirmed_album": None, "confirmed_expected_images": None}
    record = {"record_version": "1.0", "kind": "source_identity_user_fact", "status": "CONFIRMED",
              "source_correspondence_result": "CONFIRMED", "merge_prohibited": True,
              "app_identifier": "jp.naver.line.mac", "raw_requested_group": raw_group,
              "raw_persisted_group": LEGACY_GROUP, "fingerprint": dict(FP57),
              "question": {"text": "is this the same source?", "asked_at_local": "2026-09-16 10:00"},
              "answer": {"raw": "yes", "part_1": {"text": "yes", "raw": "yes"}, "part_2": part_2},
              "supplied_by": "fixture", "recorded_at_local": "2026-09-16 10:01", "evidence": [entry]}
    path = root / "user-fact" / "source-identity-user-fact.confirmed.v1.json"
    write_json(path, record)
    return path


def case_24(case: Case, paths: dict) -> None:
    root = paths["root"]
    artifact = _user_fact_record(paths)
    reference = f"user_fact:{artifact.relative_to(root)}:{H.sha256_file(artifact)}"
    state = F.verified_state("RUN-CASE-24", "WRITER-CASE-24", str(paths["destination"]),
                             evidence_reference=reference, source_kind="user_attestation", revision=2)
    install_prestate(paths, state)
    case.cli("24a", verify_args(paths, paths["evidence"] / "24a", "--run-id", "RUN-CASE-24"))
    result = case.processes[-1]["result"] or {}
    case.check("24a.exit0", 0, case.processes[-1]["exit_code"])
    case.check("24a.source", "CONFIRMED", result.get("source_status"))
    case.check("24a.source-kind", "user_attestation", result.get("source_kind"))
    for axis, expected in (("filesystem_status", "PASS"), ("registry_status", "PASS"), ("state_status", "EXACT"),
                           ("overall_status", "PASS")):
        case.check(f"24a.{axis}", expected, result.get(axis))

    for label, kwargs, check in (
            ("24b", {"part2": "unanswered"}, "unanswered"),
            ("24c", {"raw_group": LEGACY_GROUP.rsplit(":", 1)[-1]}, "楨 merge guard"),
            ("24d", {"mutate_evidence": True}, "evidence byte mutation")):
        artifact = _user_fact_record(paths, **kwargs)
        reference = f"user_fact:{artifact.relative_to(root)}:{H.sha256_file(artifact)}"
        state = F.verified_state("RUN-CASE-24", "WRITER-CASE-24", str(paths["destination"]),
                                 evidence_reference=reference, source_kind="user_attestation", revision=2)
        install_prestate(paths, state)
        case.cli(label, verify_args(paths, paths["evidence"] / label, "--run-id", "RUN-CASE-24"))
        result = case.processes[-1]["result"] or {}
        case.check(f"{label}.exit4", 4, case.processes[-1]["exit_code"])
        case.check(f"{label}.source", "UNRESOLVED", result.get("source_status"))
        case.check(f"{label}.registry", "PASS", result.get("registry_status"))
        case.check(f"{label}.state", "EXACT", result.get("state_status"))
        case.check(f"{label}.overall", "NOT_ACHIEVED", result.get("overall_status"))
        case.check(f"{label}.failure", "INPUT_PROVENANCE_LIMITED", result.get("failure_class"))
        case.check(f"{label}.note", check, check)


def case_25(case: Case, paths: dict) -> None:
    root = paths["root"]
    extra = {"observed_at": "2026-09-16T00:00:00Z", "screenshot_width": 1512, "screenshot_height": 982,
             "ellipsis": [1400, 300], "dot_spacing": 24.0, "save_all_point": [1200, 210],
             "confidence": "HIGH", "evidence": "fixture calibration", "first_row_point": [1, 1], "row_step": 32}
    run_extra = _legacy_run("RUN-CASE-25-A", str(paths["destination"]), group=LEGACY_GROUP, outcome="VERIFIED")
    run_extra["intent"] = {"calibration": dict(extra)}
    run_missing = _legacy_run("RUN-CASE-25-B", str(paths["destination"]), group=LEGACY_GROUP, outcome="SAFE_ABORT")
    run_missing["intent"] = {"action_id": "ACTION-RUN-CASE-25-B"}
    run_pre_1 = _legacy_run("RUN-CASE-25-C", str(paths["destination"]), group=LEGACY_GROUP, outcome="VERIFIED")
    run_pre_1["intent"] = {"calibration": {key: value for key, value in F.CALIBRATION.items()}}
    run_pre_2 = _legacy_run("RUN-CASE-25-D", str(paths["destination"]), group=LEGACY_GROUP, outcome="SAFE_ABORT")
    run_pre_2["intent"] = {"calibration": {key: value for key, value in F.CALIBRATION.items()}}
    state = F.fresh_state(revision=39)
    state["runs"] = [run_extra, run_missing, run_pre_1, run_pre_2]
    install_prestate(paths, state)
    before = sha(paths["state"])
    expected_normalizations = [
        {"run_id": "RUN-CASE-25-A", "kind": "calibration.extra_keys",
         "detail": "intent.calibration carries extra keys ['first_row_point', 'row_step']"},
        {"run_id": "RUN-CASE-25-B", "kind": "calibration.missing",
         "detail": "intent.calibration is absent; calibration reports UNKNOWN"},
        {"run_id": "RUN-CASE-25-C", "kind": "contract_revision.missing",
         "detail": "pre-RC2 run without contract_revision"},
        {"run_id": "RUN-CASE-25-D", "kind": "contract_revision.missing",
         "detail": "pre-RC2 run without contract_revision"},
    ]
    case.cli("25a", verify_args(paths, paths["evidence"] / "25a"))
    result = case.processes[-1]["result"] or {}
    case.check("25a.exit4", 4, case.processes[-1]["exit_code"])
    case.check("25a.filesystem", "PASS", result.get("filesystem_status"))
    case.check("25a.registry", "FAIL", result.get("registry_status"))
    case.check("25a.source", "UNRESOLVED", result.get("source_status"))
    case.check("25a.state", "LEGACY_PROVENANCE_LIMITED", result.get("state_status"))
    case.check("25a.overall", "UNKNOWN", result.get("overall_status"))
    case.check("25a.failure", "INPUT_PROVENANCE_LIMITED", result.get("failure_class"))
    case.check("25a.legacy-normalizations", expected_normalizations, result.get("legacy_normalizations"))
    case.check("25a.state-unchanged", before["sha256"], sha(paths["state"])["sha256"])

    case.cli("25b", tx_args(paths, "prepare", "--run-id", "RUN-CASE-25-B", "--owner-id", "WRITER-CASE-25-B",
                            "--group-key", GROUP, "--start-date", FP57["start_date"], "--end-date", FP57["end_date"],
                            "--expected-images", "57", "--destination", str(paths["destination"]),
                            "--source-evidence", str(paths["source_evidence"]),
                            "--dispatcher", str(paths["dispatcher"]),
                            "--dispatch-counter", str(paths["counter"]),
                            "--evidence-dir", str(paths["evidence"] / "25b")))
    rec = case.processes[-1]
    case.check("25b.code", "INVALID_STATE_LEGACY", code_of(rec))
    case.check("25b.exit4", 4, rec["exit_code"])
    case.check("25b.no-write", before["sha256"], sha(paths["state"])["sha256"])
    case.check("25b.counter0", 0, counter_lines(paths))


CASE_FUNCTIONS = {
    "01": case_01, "02": case_02, "03": case_03, "04": case_04, "05": case_05, "06": case_06,
    "07": case_07, "08": case_08, "09": case_09, "10": case_10, "11": case_11, "12": case_12,
    "13": case_13, "14": case_14, "15": case_15, "16": case_16, "17": case_17, "18": case_18,
    "19": case_19, "20": case_20, "21": case_21, "22": case_22, "23": case_23, "24": case_24,
    "25": case_25,
}


def artifact_inventory(root: Path) -> list[dict]:
    root = Path(root)
    artifacts = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            info = sha(path)
            info["path"] = str(path.relative_to(root))
            artifacts.append(info)
    return artifacts


def run_case(case_id: str, root: Path) -> dict:
    case = Case(case_id, root)
    reset_case_root(root)
    paths = build_case_root(root, F.fresh_state(), images=57,
                            dispatcher="blocking" if case_id == "20" else "returned")
    case.note("fixture preconditions authored by the driver; oracle computed before product execution")
    CASE_FUNCTIONS[case_id](case, paths)
    manifest = {"schema_version": 1, "case_id": case_id, "root": str(root),
                "checks": case.checks, "processes": case.processes, "inputs": case.inputs,
                "notes": case.notes, "independent_oracle_match": case.match,
                "artifacts": artifact_inventory(root)}
    write_json(root / "manifest.json", manifest)
    summary = {"case_id": case_id, "independent_oracle_match": case.match,
               "failed_checks": [row["id"] for row in case.checks if not row["match"]],
               "manifest": sha(root / "manifest.json")}
    write_json(root / "result.json", summary)
    return summary


def copy_within(src: Path, dst: Path) -> None:
    """Copy src to dst; a no-op when the literal argv aliases the same file."""
    if Path(src).resolve() == Path(dst).resolve():
        return
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True, choices=CASES)
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
    root = Path(ns.case_root)
    summary = run_case(ns.case_id, root)
    Path(ns.pre_state).parent.mkdir(parents=True, exist_ok=True)
    copy_within(root / "input-state.json", Path(ns.pre_state))
    copy_within(Path(ns.state), Path(ns.post_state))
    copy_within(root / "manifest.json", Path(ns.manifest))
    copy_within(root / "dispatch-counter.jsonl", Path(ns.counter))
    write_json(Path(ns.result), summary)
    Path(ns.stdout).write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    Path(ns.stderr).write_text("", encoding="utf-8")
    code = 0 if summary["independent_oracle_match"] else 1
    Path(ns.exit_code).write_text(f"{code}\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
