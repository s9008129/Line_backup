#!/usr/bin/env python3
"""Independent subprocess driver for the Status Contract v2 fixture matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


IDS = ["candidate", "implementation-blocked", "replan-required", "core-not-run", "core-blocked", "core-fail",
       "baseline-unchanged", "canonical-preexisting-debt", "baseline-unavailable", "all-required-waived",
       "retention-waived", "stage05-blocked", "acceptance-product-defect", "legacy-no-source", "contradictory-axes",
       "core-not-required-no-rationale", "core-not-required-rationalized", "done"]
STATUSES = {
    "candidate": ("UNKNOWN", "NOT_STARTED", "NOT_RUN", "NOT_RUN", "PENDING", "IN_PROGRESS"),
    "implementation-blocked": ("UNKNOWN", "BLOCKED", "NOT_RUN", "NOT_RUN", "PENDING", "IMPLEMENTATION_BLOCKED"),
    "replan-required": ("UNKNOWN", "ESCALATED", "NOT_RUN", "NOT_RUN", "PENDING", "REPLAN_REQUIRED"),
    "core-not-run": ("UNKNOWN", "COMPLETE", "NOT_RUN", "NOT_RUN", "PENDING", "PENDING_CORE_ACCEPTANCE"),
    "core-blocked": ("UNKNOWN", "COMPLETE", "BLOCKED", "NOT_RUN", "PENDING", "CORE_ACCEPTANCE_BLOCKED"),
    "core-fail": ("NOT_ACHIEVED", "IN_PROGRESS", "FAIL", "NOT_RUN", "PENDING", "FIX_REQUIRED"),
    "baseline-unchanged": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE"),
    "canonical-preexisting-debt": ("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING", "PENDING_REQUIRED_VERIFICATION"),
    "baseline-unavailable": ("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING", "PENDING_REQUIRED_VERIFICATION"),
    "all-required-waived": ("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE"),
    "retention-waived": ("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE"),
    "stage05-blocked": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "BLOCKED", "ACCEPTANCE_BLOCKED"),
    "acceptance-product-defect": ("UNKNOWN", "IN_PROGRESS", "PASS", "PASS", "FAIL", "FIX_REQUIRED"),
    "legacy-no-source": ("UNKNOWN", "COMPLETE", "BLOCKED", "PASS", "PENDING", "CORE_ACCEPTANCE_BLOCKED"),
    "contradictory-axes": ("NOT_ACHIEVED", "COMPLETE", "FAIL", "FAIL", "PENDING", "FIX_REQUIRED"),
    "core-not-required-no-rationale": ("UNKNOWN", "ESCALATED", "NOT_REQUIRED", "NOT_RUN", "PENDING", "REPLAN_REQUIRED"),
    "core-not-required-rationalized": ("ACHIEVED", "COMPLETE", "NOT_REQUIRED", "NOT_REQUIRED", "NOT_REQUIRED", "DONE"),
    "done": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PASS", "DONE"),
}
BLOCKERS = {
    "implementation-blocked": "IMPLEMENTATION/BLOCKED/ENVIRONMENT_FAILURE",
    "replan-required": "IMPLEMENTATION/BLOCKED/TASK_REGRESSION",
    "core-not-run": "CORE_ACCEPTANCE/NOT_RUN/INPUT_UNAVAILABLE",
    "core-blocked": "CORE_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED",
    "core-fail": "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION",
    "canonical-preexisting-debt": "DOCUMENTATION_RETENTION_HEALTH/FAIL/PRE_EXISTING_REPOSITORY_FAILURE",
    "baseline-unavailable": "REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE",
    "stage05-blocked": "INDEPENDENT_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED",
    "acceptance-product-defect": "INDEPENDENT_ACCEPTANCE/FAIL/PRODUCT_DEFECT",
    "legacy-no-source": "SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE",
    "contradictory-axes": "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION",
    "core-not-required-no-rationale": "IMPLEMENTATION/BLOCKED/TASK_REGRESSION",
    "retention-waived": "DOCUMENTATION_RETENTION_HEALTH/WAIVED/PRE_EXISTING_REPOSITORY_FAILURE",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> dict:
    data = path.read_bytes() if path.exists() else b"<missing>"
    return {"path": str(path), "exists": path.exists(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def check_fixture(ident: str) -> dict:
    result = {"CHECK_ID": "STATUS_CLOSURE_CONTRACT", "GOAL_CRITICALITY": "CORE", "EVIDENCE_ROLE": "MUST_NOT_BREAK",
              "CLOSURE_GATE": "HARD_CLEAN", "BASELINE_REQUIRED": "NO",
              "FAILURE_CLASSIFICATION_RULE": "illegal enum or routing is TASK_REGRESSION", "WAIVER_ALLOWED": "NO",
              "WAIVER_AUTHORITY": "NONE", "CHECK_RESULT": "PASS", "WAIVER_STATUS": "NOT_ALLOWED"}
    if ident == "canonical-preexisting-debt":
        result.update(CHECK_ID="DOCUMENTATION_RETENTION_HEALTH", GOAL_CRITICALITY="SUPPORTING", EVIDENCE_ROLE="REPOSITORY_HEALTH",
                      BASELINE_REQUIRED="NO", FAILURE_CLASSIFICATION_RULE="pre-existing missing retention evidence",
                      WAIVER_ALLOWED="YES", WAIVER_AUTHORITY="Project owner", CHECK_RESULT="FAIL", WAIVER_STATUS="NOT_REQUESTED")
    if ident == "retention-waived":
        result.update(CHECK_ID="DOCUMENTATION_RETENTION_HEALTH", GOAL_CRITICALITY="SUPPORTING", EVIDENCE_ROLE="REPOSITORY_HEALTH",
                      BASELINE_REQUIRED="NO", FAILURE_CLASSIFICATION_RULE="scoped retention debt",
                      WAIVER_ALLOWED="YES", WAIVER_AUTHORITY="Project owner", CHECK_RESULT="FAIL", WAIVER_STATUS="APPROVED")
    if ident in {"baseline-unchanged", "baseline-unavailable"}:
        result.update(CHECK_ID="BASELINE_REGRESSION_DELTA", EVIDENCE_ROLE="MUST_NOT_BREAK", BASELINE_REQUIRED="YES",
                      FAILURE_CLASSIFICATION_RULE="new or worsened baseline signature is TASK_REGRESSION")
    return result


def fixture_input(ident: str) -> dict:
    value = {"scenario": ident, "checks": [check_fixture(ident)]}
    if ident == "baseline-unchanged":
        value.update({"baseline_delta": "UNCHANGED", "baseline_artifact": "/private/tmp/line-backup-acceptance-status/baseline-unchanged.baseline.json",
                      "failure_class": None})
    elif ident == "baseline-unavailable":
        value.update({"baseline_delta": "UNAVAILABLE", "baseline_artifact": "/private/tmp/line-backup-acceptance-status/missing-baseline.json",
                      "failure_class": "INPUT_UNAVAILABLE"})
    elif ident == "canonical-preexisting-debt":
        value["failure_class"] = "PRE_EXISTING_REPOSITORY_FAILURE"
    elif ident == "acceptance-product-defect":
        value["failure_class"] = "PRODUCT_DEFECT"
    elif ident == "contradictory-axes":
        value["failure_class"] = "TASK_REGRESSION"
    elif ident == "core-not-required-no-rationale":
        value["failure_class"] = "TASK_REGRESSION"
    elif ident == "core-not-required-rationalized":
        value["plan_rationale"] = "This scoped artifact has no CORE acceptance obligation; Plan explicitly records why."
    elif ident == "all-required-waived":
        value["waiver"] = {"WAIVED_BY": "Project owner", "WAIVER_SCOPE": "REQUIRED_VERIFICATION",
                            "RATIONALE": "approved scoped waiver", "EVIDENCE": "owner approval", "RESIDUAL_RISK": "tracked",
                            "APPROVED_AT": "2026-09-16T00:00:00Z", "REVIEW_OR_EXPIRY_TRIGGER": "next acceptance"}
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--summary", required=True)
    ns = parser.parse_args()
    root = Path(ns.evidence_dir)
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["LC_ALL"] = "C"
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHASHSEED"] = "0"
    for ident in IDS:
        row_dir = root / ident
        input_path = Path("/private/tmp/line-backup-acceptance-status") / f"{ident}.input.json"
        output_path = Path("/private/tmp/line-backup-acceptance-status") / f"{ident}.output.json"
        write_json(input_path, fixture_input(ident))
        argv = ["/usr/bin/python3", "-m", "line_backup_acceptance", "status", "evaluate",
                "--input", str(input_path), "--output", str(output_path)]
        row_dir.mkdir(parents=True, exist_ok=True)
        (row_dir / "inputs.json").write_text(json.dumps({"argv": argv, "input": fixture_input(ident)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(argv, cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, check=False)
        (row_dir / "stdout.log").write_text(process.stdout, encoding="utf-8")
        (row_dir / "stderr.log").write_text(process.stderr, encoding="utf-8")
        (row_dir / "exit-code").write_text(str(process.returncode) + "\n", encoding="utf-8")
        actual = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else None
        expected_statuses = STATUSES[ident]
        fields = ("primary_outcome_status", "implementation_status", "core_acceptance_status",
                  "required_verification_status", "independent_acceptance_status", "task_closure_status")
        observed_statuses = tuple(actual.get(key) for key in fields) if isinstance(actual, dict) else None
        expected_blocker = BLOCKERS.get(ident)
        expected_checks = [check_fixture(ident)]
        expected_failure = fixture_input(ident).get("failure_class")
        if ident == "retention-waived":
            expected_waiver = {"WAIVED_BY": "Project owner", "WAIVER_SCOPE": "DOCUMENTATION_RETENTION_HEALTH",
                               "RATIONALE": "scoped retention debt", "EVIDENCE": "pre-existing evidence", "RESIDUAL_RISK": "reproducibility debt",
                               "APPROVED_AT": "2026-09-16T00:00:00Z", "REVIEW_OR_EXPIRY_TRIGGER": "next acceptance"}
        else:
            expected_waiver = fixture_input(ident).get("waiver")
        expected_delta = fixture_input(ident).get("baseline_delta")
        observed = {"statuses": observed_statuses, "blocker": actual.get("blocker") if isinstance(actual, dict) else None,
                    "checks": actual.get("checks") if isinstance(actual, dict) else None,
                    "baseline_delta": actual.get("baseline_delta") if isinstance(actual, dict) else None,
                    "failure_class": actual.get("failure_class") if isinstance(actual, dict) else None,
                    "waiver": actual.get("waiver") if isinstance(actual, dict) else None}
        oracle = {"statuses": observed_statuses == expected_statuses, "blocker": observed["blocker"] == expected_blocker,
                  "checks": observed["checks"] == expected_checks, "baseline_delta": observed["baseline_delta"] == expected_delta,
                  "failure_class": observed["failure_class"] == expected_failure, "waiver": observed["waiver"] == expected_waiver,
                  "output_matches_stdout": isinstance(actual, dict) and process.stdout.strip().splitlines()[-1] == json.dumps(actual, ensure_ascii=False, sort_keys=True),
                  "exit": process.returncode == 0}
        row = {"id": ident, "argv": argv, "exit": process.returncode, "result": actual, "observed": observed,
               "expected": {"statuses": expected_statuses, "blocker": expected_blocker, "checks": expected_checks,
                            "baseline_delta": expected_delta, "failure_class": expected_failure, "waiver": expected_waiver},
               "oracle": oracle, "match": all(oracle.values()),
               "artifacts": [digest(path) for path in (input_path, output_path, row_dir / "inputs.json", row_dir / "stdout.log", row_dir / "stderr.log", row_dir / "exit-code")]}
        rows.append(row)
    manifest = {"schema_version": 2, "rows": rows}
    write_json(Path(ns.manifest), manifest)
    summary = {"schema_version": 1, "total": len(rows), "passed": sum(row["match"] for row in rows), "rows": rows}
    write_json(Path(ns.summary), summary)
    print(json.dumps({"passed": summary["passed"], "total": summary["total"], "failed": [r["id"] for r in rows if not r["match"]]}, sort_keys=True))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
