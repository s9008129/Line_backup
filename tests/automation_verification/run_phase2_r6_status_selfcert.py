#!/usr/bin/env python3
"""Phase 2 / R6 (status half) — `status evaluate` scenario table as self-certification.

CLAIM  The real `status evaluate` entry routes the six Status-Contract-v2 axes from a hard-coded
       `scenario` -> status-tuple table instead of from facts: `{"scenario": "done"}` with zero
       facts (no checks, no evidence fields) returns the canned
       ACHIEVED/COMPLETE/PASS/PASS/PASS + DONE, and `{"scenario": "baseline-unchanged"}` pointing
       at a nonexistent baseline artifact still returns required-verification PASS +
       READY_FOR_INDEPENDENT_ACCEPTANCE. The generic (non-scenario) branch derives closure from
       the supplied fact fields, so the same payload without `scenario` does not claim DONE.
ENTRY  Real CLI `python3 -m line_backup_acceptance status evaluate --input X --output Y`, one
       fresh process per subcase; no test flags, no in-process import of the evaluator.
ORACLE The written output JSON: canned-tuple equality, identical routing axes across a minimal and
       a contradictory `done` payload, a nonexistent baseline artifact recorded as absent, a
       control group (`legacy-no-source` -> CORE_ACCEPTANCE_BLOCKED), and generic-branch controls
       with the same facts supplied as `primary_outcome_status`/... fields.
DECIDE A confirmed self-certified DONE/READY answer must not be accepted as status evidence; only
       evidence-grounded facts may drive closure, so the scenario table stays fixture-only until
       evaluated facts (never scenario names) determine the routing.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (durable_copy_tree, program_hashes, read_json, run_product, sha256_bytes, write_json,
                     write_tree_manifest)

WORK = Path(__file__).resolve().parents[2]
SRC = WORK / "src"
DEFAULT_CASE_ROOT = Path("/private/tmp/line-backup-acceptance-status-r6")
FIELDS = ("primary_outcome_status", "implementation_status", "core_acceptance_status",
          "required_verification_status", "independent_acceptance_status", "task_closure_status")
DONE_TUPLE = ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PASS", "DONE")
READY_TUPLE = ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE")
LEGACY_TUPLE = ("UNKNOWN", "COMPLETE", "BLOCKED", "PASS", "PENDING", "CORE_ACCEPTANCE_BLOCKED")
LEGACY_BLOCKER = "SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE"
GENERIC_DEFAULT_TUPLE = ("UNKNOWN", "NOT_STARTED", "NOT_RUN", "NOT_RUN", "PENDING", "PENDING_CORE_ACCEPTANCE")
FORBIDDEN_CASE_ROOTS = ({Path("/private/tmp/line-backup-acceptance-status"),
                         Path("/private/tmp/line-backup-acceptance-authority"),
                         Path("/private/tmp/line-backup-acceptance-verifier"),
                         Path("/private/tmp/line-backup-legacy-false-positive")}
                        | {Path(f"/private/tmp/line-backup-acceptance-case-{i:02d}") for i in range(1, 13)})


def default_check() -> dict:
    return {"CHECK_ID": "STATUS_CLOSURE_CONTRACT", "GOAL_CRITICALITY": "CORE", "EVIDENCE_ROLE": "MUST_NOT_BREAK",
            "CLOSURE_GATE": "HARD_CLEAN", "BASELINE_REQUIRED": "NO",
            "FAILURE_CLASSIFICATION_RULE": "illegal enum or routing is TASK_REGRESSION", "WAIVER_ALLOWED": "NO",
            "WAIVER_AUTHORITY": "NONE", "CHECK_RESULT": "PASS", "WAIVER_STATUS": "NOT_ALLOWED"}


def baseline_check() -> dict:
    return {"CHECK_ID": "BASELINE_REGRESSION_DELTA", "GOAL_CRITICALITY": "CORE", "EVIDENCE_ROLE": "MUST_NOT_BREAK",
            "CLOSURE_GATE": "HARD_CLEAN", "BASELINE_REQUIRED": "YES",
            "FAILURE_CLASSIFICATION_RULE": "new or worsened baseline signature is TASK_REGRESSION",
            "WAIVER_ALLOWED": "NO", "WAIVER_AUTHORITY": "NONE", "CHECK_RESULT": "PASS",
            "WAIVER_STATUS": "NOT_ALLOWED"}


def digest(path: Path) -> dict:
    data = path.read_bytes() if path.exists() else b"<missing>"
    return {"path": str(path), "exists": path.exists(), "bytes": len(data), "sha256": sha256_bytes(data)}


def guard(case_root: Path, ev: Path, allow_nonempty: bool) -> None:
    resolved = case_root.resolve()
    if not str(resolved).startswith("/private/tmp/"):
        raise SystemExit(f"refusing: case root {resolved} is not under /private/tmp")
    if resolved == WORK or WORK in resolved.parents:
        raise SystemExit(f"refusing: case root {resolved} is inside the repository")
    for forbidden in FORBIDDEN_CASE_ROOTS:
        if resolved == forbidden or forbidden in resolved.parents:
            raise SystemExit(f"refusing: case root {resolved} overlaps another driver's root {forbidden}")
    if ev.exists() and any(ev.iterdir()) and not allow_nonempty:
        raise SystemExit(f"refusing: evidence dir {ev} is not empty (append-only evidence; "
                         f"pass --allow-nonempty-evidence only for scratch reruns)")


def subcase_specs(case_root: Path) -> "dict[str, dict]":
    missing_ready = case_root / "artifacts" / "baseline-unchanged-missing.baseline.json"
    missing_done = case_root / "artifacts" / "done-contradiction-missing.baseline.json"
    a2_payload = {"checks": [], "baseline_delta": "UNAVAILABLE", "baseline_artifact": str(missing_done),
                  "failure_class": "PRODUCT_DEFECT"}
    return {
        "a1-scenario-done-minimal": {
            "note": "zero facts: only the scenario name; no checks, no evidence fields",
            "input": {"scenario": "done"},
            "expect": DONE_TUPLE, "expect_blocker_none": True,
        },
        "a2-scenario-done-contradictory-facts": {
            "note": "obviously contradictory facts (empty checks, missing baseline artifact, failure_class PRODUCT_DEFECT)",
            "input": {"scenario": "done", **a2_payload},
            "expect": DONE_TUPLE, "expect_blocker_none": True, "missing_artifact": missing_done,
        },
        "b-scenario-baseline-unchanged-missing-artifact": {
            "note": "required verification PASS + READY_FOR_INDEPENDENT_ACCEPTANCE while the baseline artifact does not exist and no verification evidence is referenced",
            "input": {"scenario": "baseline-unchanged", "checks": [baseline_check()],
                      "baseline_delta": "UNCHANGED", "baseline_artifact": str(missing_ready), "failure_class": None},
            "expect": READY_TUPLE, "expect_blocker_none": True, "missing_artifact": missing_ready,
        },
        "c-scenario-legacy-no-source": {
            "note": "control group: current semantics CORE_ACCEPTANCE_BLOCKED",
            "input": {"scenario": "legacy-no-source", "checks": [default_check()], "failure_class": "INPUT_UNAVAILABLE"},
            "expect": LEGACY_TUPLE, "expect_blocker": LEGACY_BLOCKER,
        },
        "c2a-generic-legacy-no-source-facts": {
            "note": "same facts via the generic branch: all axes supplied as primary_outcome_status/... fields",
            "input": {"checks": [default_check()], "failure_class": "INPUT_UNAVAILABLE",
                      "primary_outcome_status": "UNKNOWN", "implementation_status": "COMPLETE",
                      "core_acceptance_status": "BLOCKED", "required_verification_status": "PASS",
                      "independent_acceptance_status": "PENDING", "blocker": LEGACY_BLOCKER},
            "expect": LEGACY_TUPLE, "expect_blocker": LEGACY_BLOCKER,
        },
        "c2b-generic-done-payload-without-scenario": {
            "note": "exact (a2) payload minus the scenario key: generic branch must not turn it into DONE",
            "input": a2_payload,
            "expect": GENERIC_DEFAULT_TUPLE, "expect_blocker_none": True, "missing_artifact": missing_done,
        },
        "c2c-generic-claimed-all-pass-no-evidence": {
            "note": "extra control: generic branch is fact-driven but trusts unevidenced caller-asserted axes",
            "input": {"checks": [], "primary_outcome_status": "ACHIEVED", "implementation_status": "COMPLETE",
                      "core_acceptance_status": "PASS", "required_verification_status": "PASS",
                      "independent_acceptance_status": "PASS"},
            "expect": DONE_TUPLE, "expect_blocker_none": True,
        },
    }


def run_subcase(spec_id: str, spec: dict, case_root: Path, timeout: float = 60.0) -> dict:
    run_dir = case_root / spec_id
    input_path = run_dir / "input.json"
    output_path = run_dir / "output.json"
    write_json(input_path, spec["input"])
    run = run_product(run_dir, ["status", "evaluate", "--input", str(input_path), "--output", str(output_path)],
                      timeout=timeout)
    output = read_json(output_path) if output_path.exists() else None
    stdout = (run_dir / "stdout.log").read_text(encoding="utf-8")
    stdout_last = None
    try:
        stdout_last = json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        stdout_last = None
    statuses = tuple(output.get(field) for field in FIELDS) if isinstance(output, dict) else None
    record = {"id": spec_id, "note": spec.get("note"), "argv": run["argv"], "input": spec["input"],
              "input_digest": digest(input_path), "output": output, "output_digest": digest(output_path),
              "statuses": statuses, "blocker": output.get("blocker") if isinstance(output, dict) else None,
              "exit_code": run["exit_code"], "stdout_digest": digest(run_dir / "stdout.log"),
              "stderr_digest": digest(run_dir / "stderr.log"), "program_hashes": program_hashes(),
              "stdout_last_line_equals_output": isinstance(output, dict) and stdout_last == output}
    if spec.get("missing_artifact"):
        record["baseline_artifact"] = str(spec["missing_artifact"])
        record["baseline_artifact_exists_at_run"] = spec["missing_artifact"].exists()
    oracle = {"exit_zero": run["exit_code"] == 0, "output_written": isinstance(output, dict),
              "stdout_matches_output": record["stdout_last_line_equals_output"]}
    if spec.get("expect"):
        oracle["statuses_match_expected"] = statuses == spec["expect"]
    if spec.get("expect_blocker") is not None:
        oracle["blocker_match_expected"] = record["blocker"] == spec["expect_blocker"]
    if spec.get("expect_blocker_none"):
        oracle["blocker_is_none"] = record["blocker"] is None
    if spec.get("missing_artifact"):
        oracle["baseline_artifact_absent"] = not spec["missing_artifact"].exists()
    record["oracle"] = oracle
    record["match"] = all(oracle.values())
    return record


def compare(records: dict, missing_ready: Path) -> dict:
    a1, a2 = records["a1-scenario-done-minimal"], records["a2-scenario-done-contradictory-facts"]
    b = records["b-scenario-baseline-unchanged-missing-artifact"]
    c, c2a = records["c-scenario-legacy-no-source"], records["c2a-generic-legacy-no-source-facts"]
    c2b, c2c = records["c2b-generic-done-payload-without-scenario"], records["c2c-generic-claimed-all-pass-no-evidence"]
    out1, out2 = a1["output"] or {}, a2["output"] or {}
    differing = sorted(key for key in set(out1) | set(out2) if out1.get(key) != out2.get(key))
    c_sha, c2a_sha = c["output_digest"]["sha256"], c2a["output_digest"]["sha256"]
    return {
        "a1_vs_a2": {
            "status_axes_identical": a1["statuses"] == a2["statuses"] == DONE_TUPLE,
            "blocker_identical_and_none": a1["blocker"] is None and a2["blocker"] is None,
            "a1_statuses": list(a1["statuses"] or []), "a2_statuses": list(a2["statuses"] or []),
            "differing_output_keys": differing,
            "a1_checks": out1.get("checks"), "a2_checks": out2.get("checks"),
            "interpretation": "scenario 'done' returns the canned tuple regardless of facts; only passthrough echo fields (failure_class/baseline_delta) differ",
        },
        "scenario_vs_generic_legacy": {
            "output_byte_identical": c_sha == c2a_sha and c["output_digest"]["exists"] and c2a["output_digest"]["exists"],
            "shared_output_sha256": c_sha,
            "interpretation": "the generic branch reproduces the identical row when every axis is supplied as a fact -> the scenario table is a canned substitute for facts",
        },
        "scenario_vs_generic_done_payload": {
            "a2_statuses": list(a2["statuses"] or []), "c2b_statuses": list(c2b["statuses"] or []),
            "scenario_key_flips_closure_to_DONE": (a2["statuses"] or (None,))[-1] == "DONE" and (c2b["statuses"] or (None,))[-1] != "DONE",
            "input_key_difference": "only the 'scenario' key",
            "interpretation": "identical facts without the scenario key do not yield DONE -> DONE is keyed off the scenario name, not the facts",
        },
        "b_required_verification_without_evidence": {
            "baseline_artifact": str(missing_ready), "baseline_artifact_exists_at_run": b.get("baseline_artifact_exists_at_run"),
            "input_fields_referencing_verification_evidence": [],
            "required_verification_status": (b["statuses"] or (None,) * 4)[3],
            "interpretation": "required verification PASS + READY_FOR_INDEPENDENT_ACCEPTANCE with a nonexistent baseline artifact and no evidence reference",
        },
        "generic_branch_evidence_grounding": {
            "c2c_statuses": list(c2c["statuses"] or []),
            "c2c_output_byte_identical_to_scenario_done": c2c["output_digest"]["sha256"] == a1["output_digest"]["sha256"],
            "interpretation": "the generic branch is fact-driven but still accepts unevidenced caller-asserted PASS axes; evaluate() consults no evidence field on either path",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case-root", default=str(DEFAULT_CASE_ROOT))
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--allow-nonempty-evidence", action="store_true")
    ns = ap.parse_args()
    case_root, ev = Path(ns.case_root), Path(ns.evidence_dir)
    guard(case_root, ev, ns.allow_nonempty_evidence)

    if case_root.exists():
        shutil.rmtree(case_root)
    case_root.mkdir(parents=True)
    specs = subcase_specs(case_root)
    records = {spec_id: run_subcase(spec_id, spec, case_root) for spec_id, spec in specs.items()}
    missing_ready = case_root / "artifacts" / "baseline-unchanged-missing.baseline.json"
    comparisons = compare(records, missing_ready)
    hashes = program_hashes()

    decisive = {
        "a1_scenario_done_zero_facts_is_canned_DONE": records["a1-scenario-done-minimal"]["match"] and
            records["a1-scenario-done-minimal"]["statuses"] == DONE_TUPLE,
        "a2_scenario_done_contradictory_facts_still_canned_DONE": records["a2-scenario-done-contradictory-facts"]["match"] and
            records["a2-scenario-done-contradictory-facts"]["statuses"] == DONE_TUPLE and
            comparisons["a1_vs_a2"]["status_axes_identical"],
        "b_missing_baseline_artifact_still_READY_FOR_INDEPENDENT_ACCEPTANCE": records["b-scenario-baseline-unchanged-missing-artifact"]["match"] and
            records["b-scenario-baseline-unchanged-missing-artifact"]["statuses"] == READY_TUPLE and
            records["b-scenario-baseline-unchanged-missing-artifact"].get("baseline_artifact_exists_at_run") is False,
        "c_legacy_no_source_control_is_CORE_ACCEPTANCE_BLOCKED": records["c-scenario-legacy-no-source"]["match"] and
            records["c-scenario-legacy-no-source"]["statuses"] == LEGACY_TUPLE,
        "c2a_generic_branch_reproduces_legacy_row_from_facts_byte_identical": records["c2a-generic-legacy-no-source-facts"]["match"] and
            comparisons["scenario_vs_generic_legacy"]["output_byte_identical"],
        "c2b_generic_branch_same_facts_without_scenario_is_not_DONE": records["c2b-generic-done-payload-without-scenario"]["match"] and
            comparisons["scenario_vs_generic_done_payload"]["scenario_key_flips_closure_to_DONE"],
    }
    failed = sorted(key for key, value in decisive.items() if not value)
    verdict = "REPRODUCED_R6_STATUS_SELF_CERTIFICATION" if not failed else "NOT_REPRODUCED_R6_STATUS_SELF_CERTIFICATION"
    version = subprocess.run(["/usr/bin/python3", "--version"], capture_output=True, text=True, check=False)

    observation = {
        "schema_version": 1, "task": "phase2-r6-status-selfcert", "verdict": verdict, "failed_oracles": failed,
        "claim": "the real status-evaluate entry answers from a hard-coded scenario->tuple table, not from facts or evidence",
        "entry": "python3 -m line_backup_acceptance status evaluate --input X --output Y (real CLI, one fresh process per subcase)",
        "oracle": "written output JSON (six status axes + blocker) compared against canned tuples, missing baseline artifact asserted absent, and generic-branch controls with the same facts supplied as primary_outcome_status/... fields",
        "decision": "DONE / READY_FOR_INDEPENDENT_ACCEPTANCE answers produced by the scenario table must not be accepted as status evidence; routing must be grounded in evaluated facts (the generic branch is fact-driven but still trusts caller-asserted axes without evidence, so evidence grounding remains a separate gap)",
        "case_root": str(case_root), "workdir_is_private_tmp": str(case_root.resolve()).startswith("/private/tmp/"),
        "product_python": "/usr/bin/python3", "product_python_version": (version.stdout + version.stderr).strip(),
        "driver_python_version": sys.version.splitlines()[0],
        "product_env_fixed": {"PYTHONPATH": str(SRC), "LC_ALL": "C", "PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0"},
        "program_hashes": hashes, "oracle_evaluations": decisive, "comparisons": comparisons, "subcases": records,
    }
    write_json(ev / "observation.json", observation)
    durable_copy_tree(case_root, ev / "case-root-durable")
    manifest = write_tree_manifest(ev)
    summary = {"verdict": verdict, "failed_oracles": failed, "subcases": {k: v["match"] for k, v in records.items()},
               "evidence_dir": str(ev), "manifest_files": manifest["files"], "manifest_total_bytes": manifest["total_bytes"],
               "manifest_sha256": manifest["manifest_sha256"]}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if all(record["exit_code"] == 0 for record in records.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
