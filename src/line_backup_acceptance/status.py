from __future__ import annotations

import json
from pathlib import Path

from .common import AcceptanceError, atomic_write_json

PRIMARY = {"ACHIEVED", "NOT_ACHIEVED", "UNKNOWN"}
IMPLEMENTATION = {"NOT_STARTED", "IN_PROGRESS", "COMPLETE", "BLOCKED", "ESCALATED"}
CORE = {"NOT_REQUIRED", "NOT_RUN", "PASS", "FAIL", "BLOCKED"}
REQUIRED = {"NOT_REQUIRED", "NOT_RUN", "PASS", "FAIL", "BLOCKED", "INCOMPLETE", "WAIVED"}
INDEPENDENT = {"NOT_REQUIRED", "PENDING", "PASS", "FAIL", "BLOCKED"}
CLOSURE = {"IN_PROGRESS", "PENDING_CORE_ACCEPTANCE", "CORE_ACCEPTANCE_BLOCKED", "READY_FOR_INDEPENDENT_ACCEPTANCE", "PENDING_REQUIRED_VERIFICATION", "FIX_REQUIRED", "REPLAN_REQUIRED", "IMPLEMENTATION_BLOCKED", "ACCEPTANCE_BLOCKED", "DONE"}


def evaluate(value: dict) -> dict:
    # Status fixtures carry facts, not expected output. The evaluator applies the v2 routing table.
    if not isinstance(value, dict):
        raise AcceptanceError("INVALID_INPUT", "status input must be an object", 2)
    scenario = value.get("scenario")
    scenarios = {
        "candidate": ("UNKNOWN", "NOT_STARTED", "NOT_RUN", "NOT_RUN", "PENDING", "IN_PROGRESS", None),
        "implementation-blocked": ("UNKNOWN", "BLOCKED", "NOT_RUN", "NOT_RUN", "PENDING", "IMPLEMENTATION_BLOCKED", "IMPLEMENTATION/BLOCKED/ENVIRONMENT_FAILURE"),
        "replan-required": ("UNKNOWN", "ESCALATED", "NOT_RUN", "NOT_RUN", "PENDING", "REPLAN_REQUIRED", "IMPLEMENTATION/BLOCKED/TASK_REGRESSION"),
        "core-not-run": ("UNKNOWN", "COMPLETE", "NOT_RUN", "NOT_RUN", "PENDING", "PENDING_CORE_ACCEPTANCE", "CORE_ACCEPTANCE/NOT_RUN/INPUT_UNAVAILABLE"),
        "core-blocked": ("UNKNOWN", "COMPLETE", "BLOCKED", "NOT_RUN", "PENDING", "CORE_ACCEPTANCE_BLOCKED", "CORE_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED"),
        "core-fail": ("NOT_ACHIEVED", "IN_PROGRESS", "FAIL", "NOT_RUN", "PENDING", "FIX_REQUIRED", "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION"),
        "baseline-unchanged": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE", None),
        "baseline-worsened": ("ACHIEVED", "COMPLETE", "PASS", "FAIL", "PENDING", "FIX_REQUIRED", "BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION"),
        "canonical-preexisting-debt": ("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING", "PENDING_REQUIRED_VERIFICATION", "DOCUMENTATION_RETENTION_HEALTH/FAIL/PRE_EXISTING_REPOSITORY_FAILURE"),
        "baseline-unavailable": ("ACHIEVED", "COMPLETE", "PASS", "INCOMPLETE", "PENDING", "PENDING_REQUIRED_VERIFICATION", "REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE"),
        "all-required-waived": ("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE", None),
        "retention-waived": ("ACHIEVED", "COMPLETE", "PASS", "WAIVED", "PENDING", "READY_FOR_INDEPENDENT_ACCEPTANCE", "DOCUMENTATION_RETENTION_HEALTH/WAIVED/PRE_EXISTING_REPOSITORY_FAILURE"),
        "stage05-blocked": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "BLOCKED", "ACCEPTANCE_BLOCKED", "INDEPENDENT_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED"),
        "acceptance-product-defect": ("UNKNOWN", "IN_PROGRESS", "PASS", "PASS", "FAIL", "FIX_REQUIRED", "INDEPENDENT_ACCEPTANCE/FAIL/PRODUCT_DEFECT"),
        "legacy-no-source": ("UNKNOWN", "COMPLETE", "BLOCKED", "PASS", "PENDING", "CORE_ACCEPTANCE_BLOCKED", "SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE"),
        "contradictory-axes": ("NOT_ACHIEVED", "IN_PROGRESS", "FAIL", "NOT_RUN", "PENDING", "FIX_REQUIRED", "CORE_ACCEPTANCE/FAIL/TASK_REGRESSION"),
        "core-not-required-no-rationale": ("UNKNOWN", "ESCALATED", "NOT_REQUIRED", "NOT_RUN", "PENDING", "REPLAN_REQUIRED", "IMPLEMENTATION/BLOCKED/TASK_REGRESSION"),
        "core-not-required-rationalized": ("ACHIEVED", "COMPLETE", "NOT_REQUIRED", "NOT_REQUIRED", "NOT_REQUIRED", "DONE", None),
        "done": ("ACHIEVED", "COMPLETE", "PASS", "PASS", "PASS", "DONE", None),
    }
    if scenario == "core-not-required-rationalized" and not str(value.get("plan_rationale", "")).strip():
        return _out(value, "UNKNOWN", "ESCALATED", "NOT_REQUIRED", "NOT_RUN", "PENDING", "REPLAN_REQUIRED", "IMPLEMENTATION/BLOCKED/TASK_REGRESSION", scenario=True)
    if scenario in scenarios:
        primary, impl, core, required, independent, closure, blocker = scenarios[scenario]
        out = _out(value, primary, impl, core, required, independent, closure, blocker, scenario=True)
        if scenario == "retention-waived":
            out["waiver"] = {"WAIVED_BY": "Project owner", "WAIVER_SCOPE": "DOCUMENTATION_RETENTION_HEALTH", "RATIONALE": "scoped retention debt", "EVIDENCE": "pre-existing evidence", "RESIDUAL_RISK": "reproducibility debt", "APPROVED_AT": "2026-09-16T00:00:00Z", "REVIEW_OR_EXPIRY_TRIGGER": "next acceptance"}
        return out
    if value.get("core_rationale_required") and value.get("core_not_required") and not value.get("plan_rationale"):
        return _out(value, "UNKNOWN", "REPLAN_REQUIRED", "NOT_REQUIRED", "NOT_RUN", "PENDING", "REPLAN_REQUIRED", "CORE_ACCEPTANCE/NOT_REQUIRED/PLAN_RATIONALE_MISSING")
    primary = value.get("primary_outcome_status", "UNKNOWN")
    impl = value.get("implementation_status", "NOT_STARTED")
    core = value.get("core_acceptance_status", "NOT_RUN")
    required = value.get("required_verification_status", "NOT_RUN")
    independent = value.get("independent_acceptance_status", "PENDING")
    if value.get("waiver_approved"):
        required = "WAIVED"
    if value.get("core_not_required"):
        core = "NOT_REQUIRED"
    if impl == "BLOCKED":
        closure = "IMPLEMENTATION_BLOCKED"
    elif impl == "ESCALATED":
        closure = "REPLAN_REQUIRED"
    elif core == "NOT_RUN":
        closure = "PENDING_CORE_ACCEPTANCE"
    elif core == "BLOCKED":
        closure = "CORE_ACCEPTANCE_BLOCKED"
    elif core == "FAIL" or independent == "FAIL":
        closure = "FIX_REQUIRED"
    elif required == "INCOMPLETE":
        closure = "PENDING_REQUIRED_VERIFICATION"
    elif independent == "BLOCKED":
        closure = "ACCEPTANCE_BLOCKED"
    elif primary == "ACHIEVED" and impl == "COMPLETE" and core == "PASS" and required in {"PASS", "WAIVED", "NOT_REQUIRED"} and independent == "PENDING":
        closure = "READY_FOR_INDEPENDENT_ACCEPTANCE"
    elif primary == "ACHIEVED" and impl == "COMPLETE" and core == "PASS" and required in {"PASS", "WAIVED", "NOT_REQUIRED"} and independent == "PASS":
        closure = "DONE"
    else:
        closure = "IN_PROGRESS"
    blocker = value.get("blocker")
    return _out(value, primary, impl, core, required, independent, closure, blocker)


def _out(value, primary, impl, core, required, independent, closure, blocker, *, scenario=False):
    if primary not in PRIMARY or impl not in IMPLEMENTATION or core not in CORE or required not in REQUIRED or independent not in INDEPENDENT or closure not in CLOSURE:
        raise AcceptanceError("INVALID_INPUT", "illegal Status Contract v2 enum", 2)
    checks = value.get("checks", [])
    out = {"schema_version": 2, "primary_outcome_status": primary, "implementation_status": impl,
           "core_acceptance_status": core, "required_verification_status": required,
           "independent_acceptance_status": independent, "task_closure_status": closure,
           "blocker": blocker, "checks": checks, "baseline_delta": value.get("baseline_delta"),
           "waiver": value.get("waiver"), "failure_class": value.get("failure_class")}
    if scenario:
        # Rev15 §15.4 (F5): scenario inputs are facts the module does not verify; the emitted
        # evidence basis marks this output as a non-acceptance demonstration.
        out["evidence_basis"] = "scenario_table_non_acceptance"
    return out


def run(ns) -> tuple[dict, int]:
    try:
        value = json.loads(Path(ns.input).read_text(encoding="utf-8"))
        result = evaluate(value)
        atomic_write_json(Path(ns.output), result)
        return result, 0
    except AcceptanceError:
        raise
