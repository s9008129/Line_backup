#!/usr/bin/env python3
"""Read back formal check/inventory publication tail after child reap."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

from evidence_io import publish_exclusive
from output_policy import OutputPolicy, _read_anchored

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
EPOCH = pathlib.Path(os.path.realpath(__file__)).parent.parent
TASK = "TASK-20261010-line-v3-live-e2e"


def actual_ref(rel: str, cap: int) -> dict:
    raw, st = _read_anchored(ROOT, rel, cap)
    return {"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "dev": st.st_dev, "ino": st.st_ino, "created_at_ns": st.st_ctime_ns, "readback_verified": True}


def verify_one(policy: OutputPolicy, rel: str, *, phase: str, producer: str, receipt_ref: dict | None) -> tuple[dict, int]:
    rule = policy.rule_for(rel)
    if rule is None:
        raise RuntimeError("NO_RULE:" + rel)
    ref = actual_ref(rel, rule["max_bytes"])
    decision = policy.validate_observed(path=rel, phase=phase, producer=producer, entry_type="REGULAR", byte_count=ref["bytes"], operation="CREATE", receipt_ref=receipt_ref, readback_ref=ref)
    if not decision.allowed:
        raise RuntimeError(f"POLICY:{decision.code}:{rel}")
    return ref, ref["created_at_ns"]


def audit(mode: str) -> dict:
    policy = OutputPolicy.load(EPOCH / "output-policy.json", ROOT)
    ids = ["E01-evidence-policy", "E02-runner-selftest", "B01-baseline-pair"] if mode == "baseline" else ["B02-preservation-pair"]
    verified = []
    for check_id in ids:
        base = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/checks/{check_id}"
        receipt_path = base + ".receipt.json"
        receipt_ref = actual_ref(receipt_path, 1_000_000)
        receipt = json.loads(_read_anchored(ROOT, receipt_path, 1_000_000)[0])
        if receipt.get("verdict") != "PASS" or receipt.get("outcome", {}).get("reaped") is not True or receipt.get("outcome", {}).get("stop_reason") is not None:
            raise RuntimeError("CHECK_NOT_PASS:" + check_id)
        checks = []
        for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json"):
            ref, ctime = verify_one(policy, base + "." + suffix, phase="RUN_CHECK", producer="checks/run_command.py", receipt_ref=receipt_ref)
            checks.append({"suffix": suffix, "ref": ref, "ctime_ns": ctime})
        if not (checks[0]["ctime_ns"] <= checks[1]["ctime_ns"] <= checks[4]["ctime_ns"] and checks[2]["ctime_ns"] <= checks[4]["ctime_ns"] and checks[3]["ctime_ns"] <= checks[4]["ctime_ns"]):
            raise RuntimeError("CHECK_PUBLICATION_ORDER:" + check_id)
        verified.append({"check_id": check_id, "outputs": checks})
    base = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/inventory/{mode}"
    inventory_receipt_path = base + "-receipt.json"
    inventory_receipt = actual_ref(inventory_receipt_path, 1_000_000)
    inventory = json.loads(_read_anchored(ROOT, inventory_receipt_path, 1_000_000)[0])
    if inventory.get("verdict") != "PASS":
        raise RuntimeError("INVENTORY_NOT_PASS")
    outputs = []
    for suffix in ("scan-01.json", "scan-02.json", "compare.json", "receipt.json"):
        ref, ctime = verify_one(policy, base + "-" + suffix, phase="INVENTORY", producer="tools/inventory_pair.py", receipt_ref=inventory_receipt)
        outputs.append({"suffix": suffix, "ref": ref, "ctime_ns": ctime})
    if not all(outputs[i]["ctime_ns"] <= outputs[i+1]["ctime_ns"] for i in range(3)):
        raise RuntimeError("INVENTORY_PUBLICATION_ORDER")
    comparison = json.loads(_read_anchored(ROOT, base + "-compare.json", 1_000_000)[0])
    if comparison.get("verdict") != "PASS":
        raise RuntimeError("COMPARISON_NOT_PASS")
    return {"format": "ML07_TAIL_AUDIT_V1", "task_id": TASK, "epoch": str(EPOCH), "mode": mode, "verdict": "PASS", "verified_checks": verified, "inventory_outputs": outputs, "self_excluded_from_audit": True}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("baseline", "preservation") or pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != EPOCH / "tools/tail_audit.py" or EPOCH.parent != R / "epochs" or EPOCH.name not in ("e01", "e02", "e03"):
        print(json.dumps({"verdict": "REFUSED", "reason": "LOCATION_OR_ARGUMENTS"})); return 2
    try:
        document = audit(sys.argv[1])
        raw = (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        rel = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/inventory/{sys.argv[1]}-tail-audit.json"
        policy = OutputPolicy.load(EPOCH / "output-policy.json", ROOT)
        decision = policy.authorize_prewrite(path=rel, phase="TAIL_AUDIT", producer="tools/tail_audit.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE")
        if not decision.allowed: raise RuntimeError("TAIL_POLICY:" + decision.code)
        ref = publish_exclusive(ROOT, rel, raw, max_bytes=16 * 1024 * 1024)
        print(json.dumps({"verdict": "PASS", "ref": ref}, sort_keys=True)); return 0
    except BaseException as exc:
        print(json.dumps({"verdict": "BLOCKED", "reason": f"{type(exc).__name__}:{exc}"})); return 1


if __name__ == "__main__":
    raise SystemExit(main())
