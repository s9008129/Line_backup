#!/usr/bin/env python3
"""One-time ML07 e01 materialization from finished literal draft bytes.

This is a local preparation tool, not a substitute Harness controller.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
EPOCHREL = RUNREL + "/epochs/e01"
EPOCH = ROOT / EPOCHREL
TASK = "TASK-20261010-line-v3-live-e2e"
PY = pathlib.Path("/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13")
SCANNER = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
SOURCES = ["tools/evidence_io.py", "tools/output_policy.py", "tools/transaction_chain.py", "tools/inventory_pair.py", "tools/tail_audit.py", "checks/run_command.py", "checks/test_evidence_policy.py", "checks/test_run_command.py"]
CHECKS = ["E01-evidence-policy", "E02-runner-selftest", "B01-baseline-pair", "B02-preservation-pair"]
PRODUCT = ["scripts/line_backup_cua_adapter.mjs", "src/line_backup_batch/cli.py", "src/line_backup_batch/observations.py", "src/line_backup_batch/store.py", "rev28/Sources/rev28ctl/main.swift", "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift", "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift", "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift", "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift"]
sys.path.insert(0, str(R / "tools"))
from evidence_io import publish_exclusive
from output_policy import OutputPolicy


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def git(*argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def static_rule(path: str, *, producer: str, phase: str, lifecycle="CREATE_ONCE", cap=16 * 1024 * 1024, entry_type="REGULAR", receipt="NONE", claim=None, readback="VERIFIED", extra=None) -> dict:
    result = {"rule_id": "r-" + sha(path.encode())[:16], "exact_path": path, "exact_parent": path.rsplit("/", 1)[0], "producer": producer, "allowed_phase": [phase], "entry_type": entry_type, "max_bytes": cap, "lifecycle": lifecycle, "required_receipt": receipt, "readback_requirement": readback}
    if claim: result["required_claim"] = claim
    if extra: result.update(extra)
    return result


def policy_document(source_sha: str) -> dict:
    rules = []
    def add(path, **kwargs): rules.append(static_rule(path, **kwargs))
    for path in ("plan.md", "handoff.md", "commit-message.txt", "plan-contract.json", "handoff.json"):
        add(f"{RUNREL}/{path}", producer="document-publication", phase="BOOTSTRAP")
    for path in ("replan-amendment-01.md", "replan-amendment-02.md"):
        add(f"{RUNREL}/{path}", producer="root_planner", phase="BOOTSTRAP")
    for path in ("E2E測試報告.md", "progress.md", "evidence/attempt-ledger-draft.json", "tools/evidence_io.py", "tools/output_policy.py", "tools/transaction_chain.py", "tools/inventory_pair.py", "tools/tail_audit.py", "tools/prepare_epoch.py", "tools/prepare_dependencies.py", "checks/run_command.py", "checks/test_evidence_policy.py", "checks/test_run_command.py", "host_io.mjs", "live_analyzer.mjs", "live_classifier.mjs", "live_runner.mjs", "live_entry.mjs", "chooser_locators.mjs", "checks/validate_real_frame.py"):
        add(f"{RUNREL}/{path}", producer="root_implementer", phase="BOOTSTRAP", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
    for path in ("evidence/bootstrap-anchors.json", "evidence/controller-readiness.json", "evidence/namespace-pair-prewrite.json", "evidence/bootstrap-publications.json", "evidence/canonical-preimage.json", "evidence/draft-e01-second-pass.json", "evidence/draft-e01-current-pass.json", "evidence/draft-e02-second-pass.json", "evidence/draft-e02-current-pass.json", "evidence/epoch-materialization-plan.json"):
        add(f"{RUNREL}/{path}", producer="bootstrap-capture", phase="BOOTSTRAP", cap=8 * 1024 * 1024)
    add(f"{RUNREL}/evidence/dependency-bootstrap-policy.json", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", cap=1024 * 1024)
    for path in ("evidence/attempt-ledger-07.json", "evidence/implementation-result.json", "evidence/report-manifest.json", "evidence/publication-tail-receipt.json", "evidence/acceptance.result.json"):
        add(f"{RUNREL}/{path}", producer="report-publisher", phase="REPORT", cap=8 * 1024 * 1024)
    for path in PRODUCT:
        add(path, producer="root_implementer", phase="PRODUCT_EDIT", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
    dependency_receipt = f"{EPOCHREL}/runtime/dependency-preparation-receipt.json"
    for path in ("runtime", "runtime/wheels", "runtime/site-packages", "tmp/pip-cache"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    for path in ("runtime/requirements.lock", "runtime/dependency-input-manifest.json", "runtime/dependency-install-observation.json"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", cap=8 * 1024 * 1024, receipt=dependency_receipt)
    for filename in ("jsonschema-4.26.0-py3-none-any.whl", "referencing-0.37.0-py3-none-any.whl", "jsonschema_specifications-2025.9.1-py3-none-any.whl", "attrs-26.1.0-py3-none-any.whl", "rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl", "rfc3339_validator-0.1.4-py2.py3-none-any.whl", "six-1.17.0-py2.py3-none-any.whl"):
        add(f"{EPOCHREL}/runtime/wheels/{filename}", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", cap=1024 * 1024, receipt=dependency_receipt)
    dependency_observation = json.loads((EPOCH / "runtime/dependency-install-observation.json").read_bytes())
    if dependency_observation.get("exit_code") != 0 or dependency_observation.get("stdout_truncated") or dependency_observation.get("stderr_truncated"):
        raise RuntimeError("DEPENDENCY_INSTALL_NOT_SUCCESSFUL")
    for item in dependency_observation["installed_tree"]:
        add(f"{EPOCHREL}/runtime/site-packages/{item['path']}", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", entry_type=item["type"], cap=max(item.get("bytes", 0), 1), receipt=dependency_receipt if item["type"] == "REGULAR" else "NONE", readback="VERIFIED" if item["type"] == "REGULAR" else "IDENTITY")
    add(dependency_receipt, producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", cap=1024 * 1024)
    material_receipt = f"{EPOCHREL}/evidence/materialization-receipt.json"
    for path in ("source-freeze.json", "output-policy.json", "check-specs.json", "check-specs-freeze.json"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024, receipt=material_receipt)
    for path in SOURCES:
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024, receipt=material_receipt)
    add(material_receipt, producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024)
    for path in ("tools", "checks", "evidence/artifacts", "evidence/transactions"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    for check_id in CHECKS:
        base = f"{EPOCHREL}/evidence/checks/{check_id}"
        claim = base + ".claim.json"
        receipt = base + ".receipt.json"
        for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json"):
            pending_self = check_id in ("B01-baseline-pair", "B02-preservation-pair") and suffix == "invocation.json"
            add(base + "." + suffix, producer="checks/run_command.py", phase="RUN_CHECK", cap=16 * 1024 * 1024 if suffix in ("stdout", "stderr") else 1_000_000, receipt=receipt if suffix in ("invocation.json", "stdout", "stderr") and not pending_self else "NONE", claim=claim if suffix in ("invocation.json", "stdout", "stderr") and not pending_self else None, extra={"check_id": check_id})
    for mode in ("baseline", "preservation"):
        base = f"{EPOCHREL}/evidence/inventory/{mode}"
        receipt = base + "-receipt.json"
        for suffix in ("scan-01.json", "scan-02.json", "compare.json", "receipt.json"):
            add(base + "-" + suffix, producer="tools/inventory_pair.py", phase="INVENTORY", cap=128 * 1024 * 1024 if suffix != "receipt.json" else 1_000_000, receipt=receipt if suffix != "receipt.json" else "NONE")
        add(base + "-tail-audit.json", producer="tools/tail_audit.py", phase="TAIL_AUDIT", cap=16 * 1024 * 1024)
    for path in ("evidence/transactions/chain.json", "evidence/transactions/destinations.json", "evidence/transactions/state-summary.json", "evidence/transactions/ledger-summary.json"):
        add(f"{EPOCHREL}/{path}", producer="transaction_auditor", phase="TRANSACTION_AUDIT", cap=4 * 1024 * 1024)
    for path, receipt in (("state/backup_state.json", "state-summary.json"), ("harness-development/line-v3-live-e2e-20261010/gui-ledger.json", "ledger-summary.json")):
        add(path, producer="line_backup_batch.Store", phase="CANONICAL", lifecycle="CANONICAL_TRANSACTION", cap=16 * 1024 * 1024, receipt=f"{EPOCHREL}/evidence/transactions/{receipt}", extra={"transaction_authority": "line_backup_batch.Store", "allowed_owners": ["minimal-live-07-g1", "minimal-live-07-g2"]})
    kinds = ["screenshot-png", "raw-ax", "native-context", "sck-capture", "ocr", "grounding", "classifier", "chooser", "action", "catalog", "download", "verification", "state-readback", "command", "gate"]
    extensions = {k: ("png" if k in ("screenshot-png", "sck-capture") else "json") for k in kinds}
    rules.append({"rule_id": "dynamic-registrations", "path_template": f"{EPOCHREL}/evidence/registrations/{{kind}}-{{sequence:04d}}.json", "exact_parent": f"{EPOCHREL}/evidence/registrations", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 1000000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 5000})
    rules.append({"rule_id": "dynamic-artifacts", "path_template": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}.{{extension}}", "exact_parent": f"{EPOCHREL}/evidence/artifacts", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 33554432, "lifecycle": "CREATE_ONCE", "required_receipt": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}-receipt.json", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 5000, "extensions": extensions, "registration_required": True, "registration_path": f"{EPOCHREL}/evidence/registrations/{{kind}}-{{sequence:04d}}.json"})
    rules.append({"rule_id": "dynamic-artifact-receipts", "path_template": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}-receipt.json", "exact_parent": f"{EPOCHREL}/evidence/artifacts", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 1000000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 5000})
    return {"format": "ML07_OUTPUT_POLICY_V1", "task_id": TASK, "epoch": str(EPOCH), "source_freeze_sha256": source_sha, "rules": rules}


def main() -> int:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != R / "tools/prepare_epoch.py":
        raise RuntimeError("WRONG_LOCATION")
    head, branch = git("rev-parse", "HEAD"), git("branch", "--show-current")
    index = pathlib.Path(git("rev-parse", "--git-path", "index"))
    if not index.is_absolute(): index = ROOT / index
    if git("diff", "--cached", "--name-only"):
        raise RuntimeError("STAGED_CHANGES")
    if any((EPOCH / name).exists() for name in ("source-freeze.json", "output-policy.json", "check-specs.json", "check-specs-freeze.json")):
        raise RuntimeError("EPOCH_ALREADY_MATERIALIZED")
    source_hashes = {f"{EPOCHREL}/{path}": sha((R / path).read_bytes()) for path in SOURCES}
    source_hashes[SCANNER] = sha((ROOT / SCANNER).read_bytes())
    source_hashes[f"{RUNREL}/tools/prepare_epoch.py"] = sha((R / "tools/prepare_epoch.py").read_bytes())
    source_hashes[f"{RUNREL}/tools/prepare_dependencies.py"] = sha((R / "tools/prepare_dependencies.py").read_bytes())
    source_hashes[f"{RUNREL}/plan-contract.json"] = sha((R / "plan-contract.json").read_bytes())
    for path in ("replan-amendment-01.md", "replan-amendment-02.md", "evidence/dependency-bootstrap-policy.json"):
        source_hashes[f"{RUNREL}/{path}"] = sha((R / path).read_bytes())
    runtime = EPOCH / "runtime"
    for path in sorted(runtime.rglob("*")):
        if path.is_file() and not path.is_symlink():
            source_hashes[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    executables = {str(PY): sha(PY.read_bytes())}
    source_freeze = {"format": "ML07_EVIDENCE_SOURCE_FREEZE_V1", "task_id": TASK, "epoch": str(EPOCH), "source_hashes": source_hashes, "executables": executables}
    source_bytes = encoded(source_freeze); source_sha = sha(source_bytes)
    policy_bytes = encoded(policy_document(source_sha))
    policy = OutputPolicy(json.loads(policy_bytes), ROOT)
    plan = {"task_id": TASK, "epoch": str(EPOCH), "head": head, "branch": branch, "index_sha256": sha(index.read_bytes()), "source_freeze_sha256": source_sha, "policy_sha256": sha(policy_bytes), "formal_sources": source_hashes, "publication_order": ["source-freeze", "output-policy", "formal-source-copies", "check-specs", "check-specs-freeze", "materialization-receipt"]}
    publish_exclusive(ROOT, f"{RUNREL}/evidence/epoch-materialization-plan.json", encoded(plan), max_bytes=4 * 1024 * 1024)
    refs = []
    for rel, raw in ((f"{EPOCHREL}/source-freeze.json", source_bytes), (f"{EPOCHREL}/output-policy.json", policy_bytes)):
        refs.append(publish_exclusive(ROOT, rel, raw, max_bytes=4 * 1024 * 1024))
    for directory in ("tools", "checks", "evidence/artifacts", "evidence/transactions"):
        (EPOCH / directory).mkdir(mode=0o700, parents=False)
    for path in SOURCES:
        rel = f"{EPOCHREL}/{path}"; raw = (R / path).read_bytes()
        decision = policy.authorize_prewrite(path=rel, phase="MATERIALIZE", producer="tools/prepare_epoch.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE")
        if not decision.allowed: raise RuntimeError("MATERIALIZE_POLICY:" + decision.code)
        refs.append(publish_exclusive(ROOT, rel, raw, max_bytes=4 * 1024 * 1024))
    checks = [
        {"check_id": "E01-evidence-policy", "argv": [str(PY), "-B", str(EPOCH / "checks/test_evidence_policy.py")], "timeout_seconds": 120, "stream_cap_bytes": 2 * 1024 * 1024},
        {"check_id": "E02-runner-selftest", "argv": [str(PY), "-B", str(EPOCH / "checks/test_run_command.py")], "timeout_seconds": 120, "stream_cap_bytes": 2 * 1024 * 1024},
        {"check_id": "B01-baseline-pair", "argv": [str(PY), "-B", str(EPOCH / "tools/inventory_pair.py"), "baseline"], "timeout_seconds": 2500, "stream_cap_bytes": 1024 * 1024},
        {"check_id": "B02-preservation-pair", "argv": [str(PY), "-B", str(EPOCH / "tools/inventory_pair.py"), "preservation"], "timeout_seconds": 2500, "stream_cap_bytes": 1024 * 1024},
    ]
    specs = {"format": "ML07_CHECK_SPECS_V1", "task_id": TASK, "epoch": str(EPOCH), "checks": checks, "automatic_retry": False}
    spec_raw = encoded(specs)
    spec_ref = publish_exclusive(ROOT, f"{EPOCHREL}/check-specs.json", spec_raw, max_bytes=4 * 1024 * 1024);refs.append(spec_ref)
    freeze = {"format": "ML07_CHECK_SPECS_FREEZE_V1", "task_id": TASK, "epoch": str(EPOCH), "head": head, "branch": branch, "index_sha256": sha(index.read_bytes()), "source_freeze_sha256": source_sha, "specs_sha256": sha(spec_raw), "policy_sha256": sha(policy_bytes), "source_hashes": source_hashes, "executables": executables}
    freeze_ref = publish_exclusive(ROOT, f"{EPOCHREL}/check-specs-freeze.json", encoded(freeze), max_bytes=4 * 1024 * 1024);refs.append(freeze_ref)
    receipt = {"format": "ML07_EPOCH_MATERIALIZATION_RECEIPT_V1", "task_id": TASK, "epoch": str(EPOCH), "phase": "MATERIALIZE", "producer": "tools/prepare_epoch.py", "source_freeze_sha256": source_sha, "artifacts": refs}
    receipt_ref = publish_exclusive(ROOT, f"{EPOCHREL}/evidence/materialization-receipt.json", encoded(receipt), max_bytes=4 * 1024 * 1024)
    print(json.dumps({"source_freeze_sha256": source_sha, "policy_sha256": sha(policy_bytes), "specs_sha256": sha(spec_raw), "receipt": receipt_ref}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
