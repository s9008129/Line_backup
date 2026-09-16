#!/usr/bin/env python3
"""Independent subprocess driver for the Status Contract v2 fixture matrix (Rev18 §16.7/§17.6).

Nineteen literal rows, one literal input/output pair per row under
/private/tmp/line-backup-acceptance-status.  The driver authors the fixtures (facts,
not outputs), pins the expected tuple/blocker/metadata independently of the product,
invokes the real status CLI in a subprocess, and compares every field.  Per Rev15
§15.4 (F5) every row additionally asserts the emitted
`evidence_basis == "scenario_table_non_acceptance"`; a row whose output omits or
changes that field fails.

Ownership (Rev15 §15.5): creates only its own literal root (marker before any
fixture content), never removes a root lacking its marker, removes nothing by
default; `--clean-owned` removes only its own marked root.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR / "automation_verification"))

import harness as H  # noqa: E402

ROOT = Path("/private/tmp/line-backup-acceptance-status")
DRIVER_ID = "status-fixture-driver"
PY = "/usr/bin/python3"
FIELDS = ("primary_outcome_status", "implementation_status", "core_acceptance_status",
          "required_verification_status", "independent_acceptance_status", "task_closure_status")
EVIDENCE_BASIS = "scenario_table_non_acceptance"
STATUS_CHECK = {"CHECK_ID": "STATUS_CLOSURE_CONTRACT", "GOAL_CRITICALITY": "CORE",
                "EVIDENCE_ROLE": "MUST_NOT_BREAK", "CLOSURE_GATE": "HARD_CLEAN",
                "BASELINE_RULE": "NONE", "FAILURE_ROUTING": "illegal enum or routing is TASK_REGRESSION",
                "WAIVER_ALLOWED": "NO", "WAIVER_AUTHORITY": "NONE", "CHECK_RESULT": "PASS",
                "WAIVER_STATUS": "NOT_ALLOWED"}
RETENTION_CHECK = {"CHECK_ID": "DOCUMENTATION_RETENTION_HEALTH", "GOAL_CRITICALITY": "SUPPORTING",
                   "EVIDENCE_ROLE": "REPOSITORY_HEALTH", "CLOSURE_GATE": "HARD_CLEAN",
                   "BASELINE_RULE": "NONE", "FAILURE_ROUTING": "pre-existing missing retention evidence",
                   "WAIVER_ALLOWED": "YES", "WAIVER_AUTHORITY": "Project owner", "CHECK_RESULT": "FAIL",
                   "WAIVER_STATUS": "NOT_REQUESTED"}
RETENTION_WAIVER = {"WAIVED_BY": "Project owner", "WAIVER_SCOPE": "DOCUMENTATION_RETENTION_HEALTH",
                    "RATIONALE": "scoped retention debt", "EVIDENCE": "pre-existing evidence",
                    "RESIDUAL_RISK": "reproducibility debt", "APPROVED_AT": "2026-09-16T00:00:00Z",
                    "REVIEW_OR_EXPIRY_TRIGGER": "next acceptance"}
BASELINE_EXECUTION = {"COMMAND": "tests/authority_baseline.py", "CWD": str(REPO), "INTERPRETER": "/usr/bin/python3",
                      "ENV_FINGERPRINT": "LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0"}
STAGE04_SNAPSHOT = {"CHECK_ID": "STAGE_04_SNAPSHOT", "STAGE_04_REPORTED_IMPLEMENTATION_STATUS": "COMPLETE",
                    "STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS": "FAIL",
                    "STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS": "NOT_RUN",
                    "STAGE_04_EXECUTION_ARTIFACT_SHA256": "0" * 64, "IMMUTABLE": "YES"}

# (primary, implementation, core, required, independent, closure), blocker
EXPECTED = {
    "candidate": (("UNKNOWN", "NOT_STARTED", "NOT_RUN", "NOT_RUN", "PENDING", "IN_PROGRESS"), None),
    "implementation-blocked": (("UNKNOWN", "BLOCKED", "NOT_RUN", "NOT_RUN", "PENDING", "IMPLEMENTATION_BLOCKED"),
                               "IMPLEMENTATION/BLOCKED/ENVIRONMENT_FAILURE"),
    "replan-required": (("UNKNOWN", "ESCALATED", "NOT_RUN", "NOT_RUN", "PENDING", "REPLAN_REQUIRED"),
                        "IMPLEMENTATION/BLOCKED/TASK_REGRESSION"),
    "core-not-run": (("UNKNOWN", "COMPLETE", "NOT_RUN", "NOT_RUN", "PENDING", "PENDING_CORE_ACCEPTANCE"),
                     "CORE_ACCEPTANCE/NOT_RUN/INPUT_UNAVAILABLE"),
    "core-blocked": (("UNKNOWN", "COMPLETE", "BLOCKED", "NOT_RUN", "PENDING", "CORE_ACCEPTANCE_BLOCKED"),
                     "CORE_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED"),
    "core-fail": (("NOT_ACHIEVED", "IN_PROGRESS", "FAIL", "NOT_RUN", "PENDING", "FIX_REQUIRED"),
                  "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION"),
    "baseline-unchanged": (("ACHIEVED", "COMPLETE", "PASS", "PASS", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE"), None),
    "baseline-worsened": (("ACHIEVED", "COMPLETE", "PASS", "FAIL", "PENDING", "FIX_REQUIRED"),
                          "BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION"),
    "canonical-preexisting-debt": (("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING",
                                    "PENDING_REQUIRED_VERIFICATION"),
                                   "DOCUMENTATION_RETENTION_HEALTH/FAIL/PRE_EXISTING_REPOSITORY_FAILURE"),
    "baseline-unavailable": (("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING",
                              "PENDING_REQUIRED_VERIFICATION"),
                             "REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE"),
    "all-required-waived": (("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING",
                             "READY_FOR_INDEPENDENT_ACCEPTANCE"), None),
    "retention-waived": (("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING",
                          "READY_FOR_INDEPENDENT_ACCEPTANCE"),
                         "DOCUMENTATION_RETENTION_HEALTH/WAIVED/PRE_EXISTING_REPOSITORY_FAILURE"),
    "stage05-blocked": (("ACHIEVED", "COMPLETE", "PASS", "PASS", "BLOCKED", "ACCEPTANCE_BLOCKED"),
                        "INDEPENDENT_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED"),
    "acceptance-product-defect": (("UNKNOWN", "IN_PROGRESS", "PASS", "PASS", "FAIL", "FIX_REQUIRED"),
                                  "INDEPENDENT_ACCEPTANCE/FAIL/PRODUCT_DEFECT"),
    "legacy-no-source": (("UNKNOWN", "COMPLETE", "BLOCKED", "PASS", "PENDING", "CORE_ACCEPTANCE_BLOCKED"),
                         "SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE"),
    "contradictory-axes": (("NOT_ACHIEVED", "IN_PROGRESS", "FAIL", "NOT_RUN", "PENDING", "FIX_REQUIRED"),
                           "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION"),
    "core-not-required-no-rationale": (("UNKNOWN", "ESCALATED", "NOT_REQUIRED", "NOT_RUN", "PENDING",
                                        "REPLAN_REQUIRED"), "IMPLEMENTATION/BLOCKED/TASK_REGRESSION"),
    "core-not-required-rationalized": (("ACHIEVED", "COMPLETE", "NOT_REQUIRED", "NOT_REQUIRED", "NOT_REQUIRED",
                                        "DONE"), None),
    "done": (("ACHIEVED", "COMPLETE", "PASS", "PASS", "PASS", "DONE"), None),
}
ORDERED_IDS = list(EXPECTED)


def row_checks(case_id: str) -> list:
    if case_id == "canonical-preexisting-debt":
        return [dict(STATUS_CHECK), dict(RETENTION_CHECK)]
    if case_id == "retention-waived":
        check = dict(RETENTION_CHECK)
        check["WAIVER_STATUS"] = "APPROVED"
        return [dict(STATUS_CHECK), check]
    if case_id in {"baseline-unchanged", "baseline-worsened"}:
        baseline = dict(STATUS_CHECK)
        baseline.update(CHECK_ID="BASELINE_REGRESSION_DELTA", EVIDENCE_ROLE="MUST_NOT_BREAK", BASELINE_RULE="BASELINE_DELTA")
        return [baseline]
    if case_id == "baseline-unavailable":
        baseline = dict(STATUS_CHECK)
        baseline.update(CHECK_ID="BASELINE_REGRESSION_DELTA", EVIDENCE_ROLE="MUST_NOT_BREAK", BASELINE_RULE="BASELINE_DELTA",
                        CHECK_RESULT="BLOCKED", WAIVER_STATUS="NOT_ALLOWED")
        return [baseline]
    if case_id == "contradictory-axes":
        return [dict(STATUS_CHECK), dict(STAGE04_SNAPSHOT)]
    return [dict(STATUS_CHECK)]


def baseline_artifact(case_id: str) -> dict | None:
    if case_id == "baseline-unchanged":
        path = ROOT / "baseline-unchanged.baseline.json"
        meta = H.write_json(path, {"signature": "pre-existing: clean", "bytes": 0})
        return {"path": str(path), "bytes": meta["bytes"], "sha256": meta["sha256"],
                "execution": dict(BASELINE_EXECUTION), "signature": {"UNCHANGED": ["pre-existing: clean"]},
                "baseline_delta": "UNCHANGED"}
    if case_id == "baseline-worsened":
        path = ROOT / "baseline-worsened.baseline.json"
        meta = H.write_json(path, {"signature": "pre-existing: clean", "bytes": 0})
        return {"path": str(path), "bytes": meta["bytes"], "sha256": meta["sha256"],
                "execution": dict(BASELINE_EXECUTION),
                "signature": {"NEW_OR_WORSENED": ["tests/verifier_fixture_driver.py:INPUT_NEGATIVE x1"]},
                "baseline_delta": "WORSENED"}
    return None


def fixture_input(case_id: str) -> dict:
    value = {"scenario": case_id, "checks": row_checks(case_id), "baseline_delta": EXPECTED_DELTA(case_id)}
    artifact = baseline_artifact(case_id)
    if case_id == "baseline-unchanged":
        value["baseline_artifact"] = str(ROOT / "baseline-unchanged.baseline.json")
        value["baseline_evidence"] = artifact
        value["failure_class"] = None
    elif case_id == "baseline-worsened":
        value["baseline_artifact"] = str(ROOT / "baseline-worsened.baseline.json")
        value["baseline_evidence"] = artifact
        value["failure_class"] = "TASK_REGRESSION"
    elif case_id == "baseline-unavailable":
        value["baseline_artifact"] = str(ROOT / "missing-baseline.json")
        value["failure_class"] = "INPUT_UNAVAILABLE"
    elif case_id == "canonical-preexisting-debt":
        value["failure_class"] = "PRE_EXISTING_REPOSITORY_FAILURE"
    elif case_id == "acceptance-product-defect":
        value["failure_class"] = "PRODUCT_DEFECT"
    elif case_id in {"contradictory-axes", "core-not-required-no-rationale"}:
        value["failure_class"] = "TASK_REGRESSION"
    elif case_id == "core-not-required-rationalized":
        value["plan_rationale"] = "This scoped artifact has no CORE acceptance obligation; the Plan records why."
        value["failure_class"] = None
    elif case_id == "all-required-waived":
        value["waiver"] = {"WAIVED_BY": "Project owner", "WAIVER_SCOPE": "REQUIRED_VERIFICATION",
                           "RATIONALE": "approved scoped waiver", "EVIDENCE": "owner approval",
                           "RESIDUAL_RISK": "tracked", "APPROVED_AT": "2026-09-16T00:00:00Z",
                           "REVIEW_OR_EXPIRY_TRIGGER": "next acceptance"}
        value["waiver_approved"] = True
    elif case_id == "retention-waived":
        value["waiver"] = dict(RETENTION_WAIVER)
        value["waiver_approved"] = True
    return value


def EXPECTED_DELTA(case_id: str) -> str | None:  # noqa: N802 - driver-side constant accessor
    return {"baseline-unchanged": "UNCHANGED", "baseline-worsened": "WORSENED",
            "baseline-unavailable": "UNAVAILABLE"}.get(case_id)


def expected_waiver(case_id: str):
    if case_id == "retention-waived":
        return dict(RETENTION_WAIVER)
    if case_id == "all-required-waived":
        return fixture_input("all-required-waived")["waiver"]
    return None


def manifest_rows() -> list:
    rows = []
    for case_id in ORDERED_IDS:
        statuses, blocker = EXPECTED[case_id]
        rows.append({"id": case_id,
                     "input": str(ROOT / f"{case_id}.input.json"),
                     "output": str(ROOT / f"{case_id}.output.json"),
                     "evidence_dir": str(ROOT / "evidence" / case_id),
                     "argv": [PY, "-m", "line_backup_acceptance", "status", "evaluate",
                              "--input", str(ROOT / f"{case_id}.input.json"),
                              "--output", str(ROOT / f"{case_id}.output.json")],
                     "expected_exit": 0,
                     "expected": {"statuses": dict(zip(FIELDS, statuses)), "blocker": blocker,
                                  "checks": row_checks(case_id), "baseline_delta": EXPECTED_DELTA(case_id),
                                  "failure_class": fixture_input(case_id).get("failure_class"),
                                  "waiver": expected_waiver(case_id),
                                  "evidence_basis": EVIDENCE_BASIS},
                     "oracle_rule": "exit 0; schema_version=2; every field equals this row's independent expectation; "
                                    "checks preserved byte-for-byte; evidence_basis pinned; output==stdout"})
    return rows


def ensure_root() -> None:
    H.ensure_owned_root(ROOT, DRIVER_ID)
    H.reset_owned_content(ROOT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--clean-owned", action="store_true")
    ns = parser.parse_args()

    ensure_root()
    rows = manifest_rows()
    H.write_json(Path(ns.manifest), {"schema_version": 2, "root": str(ROOT), "rows": rows})

    env = {"LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0",
           "PYTHONPATH": str(REPO / "src")}
    evidence_root = Path(ns.evidence_dir)
    results = []
    for row in rows:
        case_id = row["id"]
        input_path, output_path = Path(row["input"]), Path(row["output"])
        H.write_json(input_path, fixture_input(case_id))
        input_meta = {"path": str(input_path), "bytes": input_path.stat().st_size,
                      "sha256": H.sha256_file(input_path)}
        process = subprocess.run(row["argv"], cwd=REPO, env=env, capture_output=True, text=True, check=False)
        row_dir = Path(row["evidence_dir"])
        row_dir.mkdir(parents=True, exist_ok=True)
        (row_dir / "inputs.json").write_text(
            json.dumps({"argv": row["argv"], "input": fixture_input(case_id)}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        (row_dir / "stdout.log").write_text(process.stdout, encoding="utf-8")
        (row_dir / "stderr.log").write_text(process.stderr, encoding="utf-8")
        (row_dir / "exit-code").write_text(str(process.returncode) + "\n", encoding="utf-8")
        actual = None
        if output_path.is_file():
            try:
                actual = json.loads(output_path.read_text(encoding="utf-8"))
                (row_dir / "result.json").write_text(
                    json.dumps(actual, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            except ValueError:
                actual = None
        expected = row["expected"]
        observed_statuses = {key: (actual or {}).get(key) for key in FIELDS}
        oracle = {
            "exit_0": process.returncode == 0,
            "output_parsed": isinstance(actual, dict),
            "schema_version_2": isinstance(actual, dict) and actual.get("schema_version") == 2,
            "statuses": observed_statuses == expected["statuses"],
            "blocker": (actual or {}).get("blocker") == expected["blocker"],
            "checks_preserved": isinstance(actual, dict) and actual.get("checks") == expected["checks"],
            "baseline_delta": (actual or {}).get("baseline_delta") == expected["baseline_delta"],
            "failure_class": (actual or {}).get("failure_class") == expected["failure_class"],
            "waiver": (actual or {}).get("waiver") == expected["waiver"],
            "evidence_basis": (actual or {}).get("evidence_basis") == EVIDENCE_BASIS,
            "output_matches_stdout": isinstance(actual, dict)
            and process.stdout.strip().splitlines()[-1:] == [json.dumps(actual, ensure_ascii=False, sort_keys=True)],
        }
        if case_id == "canonical-preexisting-debt":
            oracle["original_fail_preserved"] = any(
                check.get("CHECK_ID") == "DOCUMENTATION_RETENTION_HEALTH" and check.get("CHECK_RESULT") == "FAIL"
                for check in (actual or {}).get("checks") or [])
        if case_id == "retention-waived":
            oracle["original_fail_preserved"] = any(
                check.get("CHECK_ID") == "DOCUMENTATION_RETENTION_HEALTH" and check.get("CHECK_RESULT") == "FAIL"
                for check in (actual or {}).get("checks") or [])
            waiver = (actual or {}).get("waiver") or {}
            oracle["waiver_fields"] = set(RETENTION_WAIVER).issubset(waiver)
            oracle["waiver_scope"] = waiver.get("WAIVER_SCOPE") == "DOCUMENTATION_RETENTION_HEALTH"
        if case_id == "baseline-worsened":
            artifact = fixture_input(case_id)["baseline_evidence"]
            oracle["worsened_signature_disclosed"] = (
                artifact["sha256"] and artifact["bytes"] > 0
                and artifact["signature"].get("NEW_OR_WORSENED")
                and artifact["baseline_delta"] == "WORSENED"
                and not (ROOT / "missing-baseline.json").exists())
        if case_id == "baseline-unchanged":
            evidence = fixture_input(case_id)["baseline_evidence"]
            oracle["baseline_evidence_echoed"] = (
                (actual or {}).get("checks") == row_checks(case_id)
                and evidence["sha256"] and evidence["execution"] == BASELINE_EXECUTION
                and evidence["signature"].get("UNCHANGED"))
        if case_id == "baseline-unavailable":
            oracle["missing_baseline_absent"] = not (ROOT / "missing-baseline.json").exists()
        if case_id == "core-not-required-no-rationale":
            oracle["no_rationale_in_input"] = "plan_rationale" not in fixture_input(case_id)
        if case_id == "core-not-required-rationalized":
            oracle["rationale_in_input"] = bool(str(fixture_input(case_id).get("plan_rationale", "")).strip())
        if case_id == "contradictory-axes":
            oracle["stage_04_snapshot_immutable"] = any(
                check.get("CHECK_ID") == "STAGE_04_SNAPSHOT" for check in (actual or {}).get("checks") or [])
        result = {"id": case_id, "argv": row["argv"], "exit_code": process.returncode,
                  "expected": expected, "observed": {"statuses": observed_statuses,
                                                     "blocker": (actual or {}).get("blocker"),
                                                     "checks": (actual or {}).get("checks"),
                                                     "baseline_delta": (actual or {}).get("baseline_delta"),
                                                     "failure_class": (actual or {}).get("failure_class"),
                                                     "waiver": (actual or {}).get("waiver"),
                                                     "evidence_basis": (actual or {}).get("evidence_basis")},
                  "oracle": oracle, "match": all(oracle.values()),
                  "input": input_meta,
                  "output": {"path": str(output_path), "exists": output_path.is_file(),
                             "bytes": output_path.stat().st_size if output_path.is_file() else None,
                             "sha256": H.sha256_file(output_path) if output_path.is_file() else None}}
        results.append(result)
        H.write_json(row_dir / "oracle.json", result)

    manifest_path = Path(ns.manifest)
    summary = {"schema_version": 1, "driver_id": DRIVER_ID, "task_id": H.TASK_ID,
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "manifest": {"path": str(manifest_path), "bytes": manifest_path.stat().st_size,
                            "sha256": H.sha256_file(manifest_path)},
               "program_hashes": H.program_hashes(), "rows": results,
               "passed": sum(record["match"] for record in results), "total": len(results),
               "all_match": all(record["match"] for record in results)}
    H.write_tree_manifest(evidence_root)
    cleanup = None
    if ns.clean_owned:
        cleanup = H.clean_owned_root(ROOT, DRIVER_ID)
        summary["cleanup"] = cleanup
    H.write_json(Path(ns.summary), summary)
    print(json.dumps({"passed": summary["passed"], "total": summary["total"],
                      "failed": [r["id"] for r in results if not r["match"]], "cleanup": cleanup},
                     ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
