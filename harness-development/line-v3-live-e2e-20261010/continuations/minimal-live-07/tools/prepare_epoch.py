#!/usr/bin/env python3
"""One-time ML07 epoch materialization from finished literal draft bytes.

This is a local preparation tool, not a substitute Harness controller.
"""
from __future__ import annotations

import hashlib
import base64
import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import sys
import zlib

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
PRIOR_RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06"
R = ROOT / RUNREL
if len(sys.argv) not in (2, 3) or sys.argv[1] != "e03" or (len(sys.argv) == 3 and sys.argv[2] != "preflight"):
    raise SystemExit("ONLY_EXPLICIT_E03_PREFLIGHT_OR_MATERIALIZATION")
SUFFIX = "e03"
ACTION = "preflight" if len(sys.argv) == 3 else "materialize"
EPOCHREL = RUNREL + f"/epochs/{SUFFIX}"
EPOCH = ROOT / EPOCHREL
TASK = "TASK-20261010-line-v3-live-e2e"
PY = pathlib.Path("/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13")
NODE = pathlib.Path("/opt/homebrew/Cellar/node/26.7.0/bin/node")
SWIFT = pathlib.Path("/usr/bin/swift")
SDK = pathlib.Path("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk")
PY_SHA256 = "34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804"
NODE_SHA256 = "1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040"
SWIFT_SHA256 = "34129c71a01a74f7f3b2443521519b2e5447553fa187f5fcafaaf8c42cc192e2"
SCANNER = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
EVIDENCE_SOURCES = ["tools/evidence_io.py", "tools/output_policy.py", "tools/transaction_chain.py", "tools/inventory_pair.py", "tools/tail_audit.py", "tools/run_draft_checks.py", "tools/prepare_input_annex.py", "tools/prepare_e01_pipcache_readback.py", "tools/prepare_historical_source_recovery.py", "tools/prepare_epoch.py", "tools/prepare_dependencies.py", "checks/run_command.py", "checks/test_evidence_policy.py", "checks/test_run_command.py"]
PRODUCT = ["scripts/line_backup_cua_adapter.mjs", "src/line_backup_batch/cli.py", "src/line_backup_batch/observations.py", "src/line_backup_batch/store.py", "rev28/Sources/rev28ctl/main.swift", "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift", "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift", "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift", "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/tools/prepare_production_family.py", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/tools/prepare_d01.py", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/tools/run_d01.py", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/tools/publish_rev28ctl.py", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/checks/validate_real_frame.py", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/host_io.mjs", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/live_analyzer.mjs", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/live_classifier.mjs", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/live_runner.mjs", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/live_entry.mjs", "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/chooser_locators.mjs"]
sys.path.insert(0, str(R / "tools"))
from evidence_io import mkdir_exclusive, publish_exclusive
from output_policy import OutputPolicy


def dependency_policy_rel() -> str:
    return "evidence/dependency-bootstrap-policy.json" if SUFFIX == "e01" else f"evidence/dependency-bootstrap-policy-{SUFFIX}.json"


def plan_rel() -> str:
    return f"evidence/epoch-materialization-plan-{SUFFIX}.json"


def check_specs() -> list[dict]:
    return [
        {"check_id": "E01-evidence-policy", "argv": [str(PY), "-B", str(EPOCH / "checks/test_evidence_policy.py")], "timeout_seconds": 120, "stream_cap_bytes": 2 * 1024 * 1024},
        {"check_id": "E02-runner-selftest", "argv": [str(PY), "-B", str(EPOCH / "checks/test_run_command.py")], "timeout_seconds": 120, "stream_cap_bytes": 2 * 1024 * 1024},
        {"check_id": "B01-baseline-pair", "argv": [str(PY), "-B", str(EPOCH / "tools/inventory_pair.py"), "baseline"], "timeout_seconds": 2500, "stream_cap_bytes": 1024 * 1024},
        {"check_id": "B02-preservation-pair", "argv": [str(PY), "-B", str(EPOCH / "tools/inventory_pair.py"), "preservation"], "timeout_seconds": 2500, "stream_cap_bytes": 1024 * 1024},
    ]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def readback_ref(relative: str) -> dict:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("BOOTSTRAP_READBACK_MISSING:" + relative)
    raw = path.read_bytes()
    return {"path": relative, "bytes": len(raw), "sha256": sha(raw)}


def same_ref(actual: dict, expected: dict) -> bool:
    return all(actual.get(key) == value for key, value in expected.items())


def verify_bootstrap_snapshots() -> None:
    annex_rel = f"{RUNREL}/evidence/read-only-user-input-01.json"
    annex_receipt_rel = f"{RUNREL}/evidence/read-only-user-input-01.receipt.json"
    annex_ref, annex_receipt_ref = readback_ref(annex_rel), readback_ref(annex_receipt_rel)
    annex = json.loads((ROOT / annex_rel).read_bytes())
    receipt = json.loads((ROOT / annex_receipt_rel).read_bytes())
    if (annex.get("authority") != "READ_ONLY_USER_INPUT" or annex.get("source_producer") is not None
            or annex.get("source_write_authority") is not None or not same_ref(receipt.get("annex", {}), annex_ref)
            or receipt.get("source_fstat") != annex.get("source_fstat")
            or receipt.get("publisher") != "context_history" or receipt.get("decision_owner") != "root_planner"):
        raise RuntimeError("READ_ONLY_USER_INPUT_ANNEX_BINDING")
    for source_path, snap_path, receipt_path, producer in (
        ("代理協作開發紀錄.md", "evidence/recorder-log-initial-01.md", "evidence/recorder-log-initial-01.receipt.json", "collaboration_recorder"),
    ):
        snap_rel = f"{RUNREL}/{snap_path}"
        snap_ref = readback_ref(snap_rel)
        snap_raw = (ROOT / snap_rel).read_bytes()
        snap_receipt_rel = f"{RUNREL}/{receipt_path}"
        snap_receipt = json.loads((ROOT / snap_receipt_rel).read_bytes())
        if (snap_receipt.get("source_path") != f"{RUNREL}/{source_path}"
                or snap_receipt.get("source_producer") != producer or not same_ref(snap_receipt.get("snapshot", {}), snap_ref)
                or snap_receipt.get("source_fstat", {}).get("sha256") != sha(snap_raw)
                or snap_receipt.get("source_fstat", {}).get("size") != len(snap_raw)):
            raise RuntimeError("RECORDER_SNAPSHOT_BINDING")
    for original_name, copied_name in (("handoff.json", "handoff.json"), ("plan-contract.json", "original-plan-contract.json")):
        original_bytes = (R / original_name).read_bytes()
        copied_path = R / "implementation-only-handoff" / copied_name
        if copied_path.is_symlink() or not copied_path.is_file() or copied_path.read_bytes() != original_bytes:
            raise RuntimeError("IMPLEMENTATION_EXACT_COPY_DRIFT:" + copied_name)
    reviewed_contract = (R / "implementation-only-handoff/plan-contract.json").read_bytes()
    compiled_handoff = R / "implementation-only-handoff/compiled-handoff.json"
    if compiled_handoff.is_symlink() or not compiled_handoff.is_file() or compiled_handoff.read_bytes() != reviewed_contract:
        raise RuntimeError("COMPILED_HANDOFF_NOT_EXACT_REVIEWED_CONTRACT")


def historical_e02_inputs() -> list[pathlib.Path]:
    """Return only E02's frozen materialization copies and real runtime receipt."""
    spec = importlib.util.spec_from_file_location("ml07_e02_closure", R / "tools/inventory_pair.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("E02_CLOSURE_SOURCE_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EPOCH = EPOCH
    module._e02_policy()
    material_path = R / "epochs/e02/evidence/materialization-receipt.json"
    material = json.loads(material_path.read_bytes())
    rels = [item.get("path") for item in material.get("artifacts", [])]
    rels.extend([
        f"{RUNREL}/epochs/e02/evidence/materialization-receipt.json",
        f"{RUNREL}/epochs/e02/runtime/dependency-preparation-receipt.json",
    ])
    paths = []
    for rel in sorted(set(rels)):
        if not isinstance(rel, str) or not rel.startswith(f"{RUNREL}/epochs/e02/"):
            raise RuntimeError("E02_CLOSURE_PATH_INVALID")
        path = ROOT / rel
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("E02_CLOSURE_INPUT_MISSING:" + rel)
        paths.append(path)
    return paths


def verify_pending_dependency_finalization() -> dict:
    """Validate the pre-existing, planned E02 install without claiming its receipt."""
    policy_rel = f"{RUNREL}/evidence/dependency-bootstrap-policy-e03.json"
    policy_path = ROOT / policy_rel
    manifest_path = EPOCH / "runtime/dependency-input-manifest.json"
    observation_path = EPOCH / "runtime/dependency-install-observation.json"
    lock_path = EPOCH / "runtime/requirements.lock"
    receipt_path = EPOCH / "runtime/dependency-preparation-receipt.json"
    files = (policy_path, manifest_path, observation_path, lock_path)
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("DEPENDENCY_PREFLIGHT_INPUT_MISSING:" + str(path.relative_to(ROOT)))

    old_argv, old_write_bytecode = sys.argv[:], sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sys.argv = [str(R / "tools/prepare_dependencies.py"), "e03"]
        spec = importlib.util.spec_from_file_location("ml07_dependency_preflight", R / "tools/prepare_dependencies.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("DEPENDENCY_PREFLIGHT_SOURCE_IMPORT")
        dep = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dep)
    finally:
        sys.argv = old_argv
        sys.dont_write_bytecode = old_write_bytecode

    frozen = json.loads(policy_path.read_bytes())
    expected_epoch = str(EPOCH)
    expected_directories = [EPOCHREL, f"{EPOCHREL}/runtime", f"{EPOCHREL}/runtime/wheels",
                            f"{EPOCHREL}/runtime/site-packages", f"{EPOCHREL}/tmp", f"{EPOCHREL}/tmp/pip-cache"]
    expected_outputs = [f"{EPOCHREL}/runtime/requirements.lock", f"{EPOCHREL}/runtime/dependency-input-manifest.json",
                        f"{EPOCHREL}/runtime/dependency-install-observation.json"]
    expected_wheels = [{"path": f"{EPOCHREL}/runtime/wheels/{pin[2]}", "bytes": pin[3], "sha256": pin[4],
                        "source": f"{RUNREL}/epochs/e01/runtime/wheels/{pin[2]}"} for pin in dep.PINS]
    if (frozen.get("format") != "ML07_DEPENDENCY_BOOTSTRAP_POLICY_V1" or frozen.get("task_id") != TASK
            or frozen.get("epoch") != expected_epoch or frozen.get("producer") != "tools/prepare_dependencies.py"
            or frozen.get("directories") != expected_directories or frozen.get("outputs") != expected_outputs
            or frozen.get("install_root") != f"{EPOCHREL}/runtime/site-packages" or frozen.get("install_cap_bytes") != 64 * 1024 * 1024
            or frozen.get("scratch_root") != f"{EPOCHREL}/tmp/pip-cache" or frozen.get("wheels") != expected_wheels):
        raise RuntimeError("DEPENDENCY_PREFLIGHT_POLICY_MISMATCH")
    for name, expected in frozen.get("planning", {}).items():
        path = R / name
        if path.is_symlink() or not path.is_file() or len(path.read_bytes()) != expected.get("bytes") or sha(path.read_bytes()) != expected.get("sha256"):
            raise RuntimeError("DEPENDENCY_PREFLIGHT_PLANNING_INPUT:" + name)
    manifest_raw, observation_raw, lock_raw = manifest_path.read_bytes(), observation_path.read_bytes(), lock_path.read_bytes()
    manifest, observation = json.loads(manifest_raw), json.loads(observation_raw)
    if (manifest.get("format") != "ML07_DEPENDENCY_INPUT_V1" or manifest.get("task_id") != TASK
            or manifest.get("epoch") != expected_epoch or manifest.get("policy_ref", {}).get("path") != policy_rel
            or manifest.get("policy_ref", {}).get("bytes") != len(policy_path.read_bytes())
            or manifest.get("policy_ref", {}).get("sha256") != sha(policy_path.read_bytes())):
        raise RuntimeError("DEPENDENCY_PREFLIGHT_MANIFEST_POLICY_REF")
    lock_ref = manifest.get("lock", {})
    if (lock_ref.get("path") != f"{EPOCHREL}/runtime/requirements.lock" or lock_ref.get("bytes") != len(lock_raw)
            or lock_ref.get("sha256") != sha(lock_raw) or lock_ref.get("readback_verified") is not True
            or lock_raw != "".join(f"{p[0]}=={p[1]} --hash=sha256:{p[4]}\n" for p in dep.PINS).encode()):
        raise RuntimeError("DEPENDENCY_PREFLIGHT_LOCK")
    expected_manifest_wheels = []
    for pin in dep.PINS:
        rel = f"{EPOCHREL}/runtime/wheels/{pin[2]}"
        path = ROOT / rel
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("DEPENDENCY_PREFLIGHT_WHEEL_MISSING:" + rel)
        raw = path.read_bytes()
        if len(raw) != pin[3] or sha(raw) != pin[4]:
            raise RuntimeError("DEPENDENCY_PREFLIGHT_WHEEL_HASH:" + rel)
        ref = next((x for x in manifest.get("wheels", []) if x.get("path") == rel), None)
        if not ref or ref.get("bytes") != len(raw) or ref.get("sha256") != sha(raw) or ref.get("readback_verified") is not True:
            raise RuntimeError("DEPENDENCY_PREFLIGHT_WHEEL_REF:" + rel)
        source = ROOT / f"{RUNREL}/epochs/e01/runtime/wheels/{pin[2]}"
        if source.is_symlink() or not source.is_file() or sha(source.read_bytes()) != pin[4]:
            raise RuntimeError("DEPENDENCY_PREFLIGHT_PIN_SOURCE:" + str(source.relative_to(ROOT)))
        expected_manifest_wheels.append(rel)
    if len(manifest.get("wheels", [])) != len(expected_manifest_wheels):
        raise RuntimeError("DEPENDENCY_PREFLIGHT_WHEEL_SET")
    expected_argv = [str(PY), "-B", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps",
                     "--only-binary=:all:", "--require-hashes", "--no-compile", "--disable-pip-version-check",
                     "--no-cache-dir", "--target", str(EPOCH / "runtime/site-packages"), "--find-links",
                     str(EPOCH / "runtime/wheels"), "-r", str(lock_path)]
    if (observation.get("argv") != expected_argv or observation.get("cwd") != str(ROOT)
            or observation.get("exit_code") != 0 or observation.get("stdout_truncated") is not False
            or observation.get("stderr_truncated") is not False
            or observation.get("env_overrides") != {"TMPDIR": str(EPOCH / "tmp/pip-cache"), "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INPUT": "1"}
            or observation.get("installed_tree") != dep.tree_manifest(EPOCH / "runtime/site-packages")):
        raise RuntimeError("DEPENDENCY_PREFLIGHT_INSTALL_OBSERVATION_OR_TREE")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise RuntimeError("DEPENDENCY_FINALIZATION_RECEIPT_ALREADY_EXISTS")
    prospective = policy_document("0" * 64)
    receipt_rule = next((x for x in prospective["rules"] if x.get("exact_path") == f"{EPOCHREL}/runtime/dependency-preparation-receipt.json"), None)
    if (not receipt_rule or receipt_rule.get("producer") != "tools/prepare_dependencies.py"
            or receipt_rule.get("allowed_phase") != ["RUNTIME_PREPARE"] or receipt_rule.get("lifecycle") != "CREATE_ONCE"):
        raise RuntimeError("DEPENDENCY_FINALIZATION_POLICY_NOT_PREDECLARED")
    pending_artifacts = []
    for rel in expected_outputs + [x["path"] for x in expected_wheels]:
        raw = (ROOT / rel).read_bytes()
        pending_artifacts.append({"path": rel, "entry_type": "REGULAR", "bytes": len(raw), "sha256": sha(raw)})
    for item in observation["installed_tree"]:
        if item.get("type") == "REGULAR":
            pending_artifacts.append({"path": f"{EPOCHREL}/runtime/site-packages/{item['path']}",
                                      "entry_type": "REGULAR", "bytes": item["bytes"], "sha256": item["sha256"]})
    pending_artifacts.sort(key=lambda item: item["path"])
    declared_pending = {rule.get("exact_path") for rule in prospective["rules"]
                        if rule.get("required_receipt") == str(receipt_path.relative_to(ROOT))}
    actual_pending = {item["path"] for item in pending_artifacts}
    if len(pending_artifacts) != 172 or actual_pending != declared_pending:
        raise RuntimeError("DEPENDENCY_PENDING_ARTIFACT_SET_MISMATCH")
    return {"verdict": "PREFLIGHT_READY_PENDING_PUBLICATION", "task_id": TASK, "epoch": expected_epoch,
            "policy_path": policy_rel, "policy_sha256": sha(policy_path.read_bytes()),
            "input_manifest_path": str(manifest_path.relative_to(ROOT)), "input_manifest_sha256": sha(manifest_raw),
            "observation_path": str(observation_path.relative_to(ROOT)), "observation_sha256": sha(observation_raw),
            "lock_path": str(lock_path.relative_to(ROOT)), "lock_sha256": sha(lock_raw),
            "pinned_wheel_count": len(dep.PINS), "installed_tree_entries": len(observation["installed_tree"]),
            "installed_tree_sha256": sha(encoded(observation["installed_tree"])),
            "pending_required_publication": str(receipt_path.relative_to(ROOT)),
            "pending_artifact_count": len(pending_artifacts), "pending_artifacts": pending_artifacts,
            "formal_gate_pass": False}


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def git(*argv: str) -> str:
    return subprocess.run(["git", "--no-optional-locks", *argv], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def git_bytes(*argv: str) -> bytes:
    return subprocess.run(["git", "--no-optional-locks", *argv], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def static_rule(path: str, *, producer: str, phase: str, lifecycle="CREATE_ONCE", cap=16 * 1024 * 1024, entry_type="REGULAR", receipt="NONE", claim=None, readback="VERIFIED", extra=None) -> dict:
    result = {"rule_id": "r-" + sha(path.encode())[:16], "exact_path": path, "exact_parent": path.rsplit("/", 1)[0], "producer": producer, "allowed_phase": [phase], "entry_type": entry_type, "max_bytes": cap, "lifecycle": lifecycle, "required_receipt": receipt, "readback_requirement": readback}
    if claim: result["required_claim"] = claim
    if extra: result.update(extra)
    return result


def preflight_materialization() -> tuple[str, str, pathlib.Path, str, dict]:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != R / "tools/prepare_epoch.py" or SUFFIX != "e03":
        raise RuntimeError("WRONG_LOCATION_OR_EPOCH")
    head, branch = git("rev-parse", "HEAD"), git("branch", "--show-current")
    verify_bootstrap_snapshots()
    index = pathlib.Path(git("rev-parse", "--git-path", "index"))
    if not index.is_absolute():
        index = ROOT / index
    if git("diff", "--cached", "--name-only"):
        raise RuntimeError("STAGED_CHANGES")
    anchors = json.loads((R / "evidence/bootstrap-anchors.json").read_bytes())
    if head != anchors.get("head") or branch != anchors.get("branch") or sha(index.read_bytes()) != anchors.get("index", {}).get("sha256"):
        raise RuntimeError("BOOTSTRAP_GIT_IDENTITY_DRIFT")
    if sha(git_bytes("diff", "--binary", "--no-ext-diff")) != anchors.get("tracked_diff", {}).get("sha256") or sha(git_bytes("diff", "--cached", "--binary", "--no-ext-diff")) != anchors.get("cached_diff", {}).get("sha256"):
        raise RuntimeError("BOOTSTRAP_GIT_DIFF_DRIFT")
    for item in anchors.get("protected", []):
        protected = ROOT / item["path"]
        if protected.exists() != item.get("exists") or protected.is_symlink():
            raise RuntimeError("PROTECTED_PREIMAGE_IDENTITY:" + item["path"])
        if item.get("exists") and item.get("sha256") and (not protected.is_file() or sha(protected.read_bytes()) != item["sha256"]):
            raise RuntimeError("PROTECTED_PREIMAGE_HASH:" + item["path"])
    expected_dirs = {"runtime", "tmp"}
    if not EPOCH.is_dir() or EPOCH.is_symlink():
        raise RuntimeError("EPOCH_ROOT_MISSING_OR_LINK")
    present = {p.name for p in EPOCH.iterdir()}
    if not present <= expected_dirs or not expected_dirs <= present:
        raise RuntimeError("EPOCH_PREPARATION_NAMESPACE:" + ",".join(sorted(present)))
    e02_inputs = historical_e02_inputs()
    all_inputs = [R / path for path in EVIDENCE_SOURCES]
    all_inputs.extend(e02_inputs)
    if ACTION == "materialize":
        all_inputs.append(R / "evidence/draft-e03-readiness-03.json")
    all_inputs.extend([R / "tools/prepare_epoch.py", R / "tools/prepare_dependencies.py", R / "plan-contract.json", R / "replan-amendment-01.md", R / "replan-amendment-02.md", R / "replan-amendment-03.md", R / "replan-amendment-04.md", R / "replan-amendment-05.md", R / "replan-amendment-06.md", R / "implementation-only-handoff/implementation-plan.md", R / "implementation-only-handoff/plan-contract.json", R / "implementation-only-handoff/handoff.json", R / "implementation-only-handoff/original-plan-contract.json", R / "implementation-only-handoff/compiled-handoff.json", R / "evidence/overlay-plan-review-06.json", R / "evidence/draft-e03-rootlog-01.json", R / dependency_policy_rel(), R / "evidence/bootstrap-anchors.json", R / "evidence/namespace-pair-prewrite.json", R / "evidence/bootstrap-publications.json", R / "evidence/canonical-preimage.json", R / "evidence/read-only-user-input-01.json", R / "evidence/read-only-user-input-01.receipt.json", R / "evidence/recorder-log-initial-01.md", R / "evidence/recorder-log-initial-01.receipt.json", R / "evidence/e01-pip-cache-current-readback-01.json", R / "evidence/e01-pip-cache-current-readback-01.receipt.json", R / "evidence/draft-e03-readiness-01.json", R / "evidence/draft-e03-family-binding-01.json", R / "evidence/draft-e03-family-binding-02.json", ROOT / PRIOR_RUNREL / "prewrite-anchors.json", ROOT / SCANNER])
    all_inputs.extend(R / "evidence/historical-source-recovery-01" / name for name in ("prepare_dependencies.py", "prepare_epoch.py", "recovery-manifest.json", "recovery-receipt.json"))
    for path in all_inputs:
        st = path.lstat()
        if not stat.S_ISREG(st.st_mode):
            raise RuntimeError("INPUT_NOT_REGULAR:" + str(path))
    outputs = [f"{RUNREL}/{plan_rel()}", f"{EPOCHREL}/source-freeze.json", f"{EPOCHREL}/output-policy.json", f"{EPOCHREL}/check-specs.json", f"{EPOCHREL}/check-specs-freeze.json", f"{EPOCHREL}/evidence/materialization-receipt.json", f"{EPOCHREL}/tools", f"{EPOCHREL}/checks", f"{EPOCHREL}/evidence", f"{EPOCHREL}/evidence/artifacts", f"{EPOCHREL}/evidence/transactions", f"{EPOCHREL}/evidence/checks", f"{EPOCHREL}/evidence/inventory", f"{EPOCHREL}/evidence/registrations"]
    outputs.extend(f"{EPOCHREL}/{path}" for path in EVIDENCE_SOURCES)
    for rel in outputs:
        if os.path.lexists(ROOT / rel):
            raise RuntimeError("MATERIALIZATION_OUTPUT_COLLISION:" + rel)
    if not (EPOCH / "runtime/dependency-install-observation.json").is_file() or (EPOCH / "runtime/dependency-install-observation.json").is_symlink():
        raise RuntimeError("DEPENDENCY_INSTALL_OBSERVATION_MISSING")
    dependency_preflight = verify_pending_dependency_finalization()
    source_inventory = git("status", "--porcelain=v1", "--untracked-files=all")
    return head, branch, index, sha(source_inventory.encode()), dependency_preflight


def namespace_preflight(dependency_preflight: dict) -> dict:
    """Run the supported non-consuming complete namespace reconciliation."""
    spec = importlib.util.spec_from_file_location("ml07_e03_namespace_pair", R / "tools/inventory_pair.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("NAMESPACE_PREFLIGHT_SOURCE_IMPORT")
    pair = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pair)
    pair.EPOCH = EPOCH
    scanner = pair.scanner_module()
    first = pair.scan_once(scanner, 1)
    second = pair.scan_once(scanner, 2)
    policy = OutputPolicy(policy_document("0" * 64), ROOT)
    comparison = pair.baseline_compare(first, second, policy, pending_dependency=dependency_preflight)
    scan_summary = lambda scan: {
        "slot": scan["slot"], "complete": scan["complete"], "timeout": scan["timeout"],
        "errors": scan["errors"], "counts": scan["counts"],
        "records_sha256": sha(pair.encoded(scan["records"])),
        "user_input_sha256": scan["read_only_user_input_observation"]["sha256"],
        "e01_pipcache_observation": scan["e01_pipcache_observation"],
    }
    return {
        "format": "ML07_E03_NAMESPACE_PREFLIGHT_V1", "task_id": TASK, "epoch": str(EPOCH),
        "verdict": "PREFLIGHT_READY_PENDING_PUBLICATION" if comparison.get("readiness") == "READY_PENDING_PUBLICATION" else "BLOCKED",
        "formal_gate_pass": False, "formal_claim_created": False,
        "argv": [str(PY), "-B", str(R / "tools/prepare_epoch.py"), "e03", "preflight"],
        "scanner_path": SCANNER, "scanner_sha256": sha((ROOT / SCANNER).read_bytes()),
        "inventory_pair_sha256": sha((R / "tools/inventory_pair.py").read_bytes()),
        "prepare_epoch_sha256": sha((R / "tools/prepare_epoch.py").read_bytes()),
        "policy_sha256": sha(encoded(policy.document)),
        "dependency_preflight": dependency_preflight,
        "scan_1": scan_summary(first), "scan_2": scan_summary(second),
        "comparison": comparison,
    }


def policy_document(source_sha: str) -> dict:
    rules = []
    def add(path, **kwargs): rules.append(static_rule(path, **kwargs))
    for path in ("E2E測試報告.md", "progress.md", "evidence/attempt-ledger-draft.json"):
        rules.append(static_rule(f"{RUNREL}/{path}", producer="context_history", phase="BOOTSTRAP", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024, extra={"allowed_phase": ["BOOTSTRAP", "REPORT"]}))
    for path in ("plan.md", "handoff.md", "commit-message.txt", "plan-contract.json", "handoff.json"):
        add(f"{RUNREL}/{path}", producer="document-publication", phase="BOOTSTRAP")
    for path in ("replan-amendment-01.md", "replan-amendment-02.md", "replan-amendment-03.md", "replan-amendment-04.md"):
        add(f"{RUNREL}/{path}", producer="root_planner", phase="BOOTSTRAP")
    rules.append(static_rule(f"{RUNREL}/replan-amendment-05.md", producer="context_history", phase="BOOTSTRAP", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024))
    rules.append(static_rule(f"{RUNREL}/replan-amendment-06.md", producer="context_history", phase="BOOTSTRAP", lifecycle="CREATE_ONCE", cap=4 * 1024 * 1024))
    add(f"{RUNREL}/implementation-only-handoff", producer="context_history", phase="BOOTSTRAP", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    add(f"{RUNREL}/implementation-only-handoff/implementation-plan.md", producer="context_history", phase="BOOTSTRAP", cap=2 * 1024 * 1024, readback="VERIFIED")
    for path in ("plan-contract.json", "handoff.json", "original-plan-contract.json", "compiled-handoff.json"):
        add(f"{RUNREL}/implementation-only-handoff/{path}", producer="context_history", phase="BOOTSTRAP", cap=4 * 1024 * 1024, readback="VERIFIED")
    add(f"{RUNREL}/evidence/overlay-plan-review-06.json", producer="context_history", phase="BOOTSTRAP", cap=1 * 1024 * 1024, readback="VERIFIED")
    add(f"{RUNREL}/implementation-only-handoff/handoff.md", producer="context_history", phase="REPORT", lifecycle="CREATE_ONCE", cap=2 * 1024 * 1024, readback="VERIFIED")
    add(f"{RUNREL}/implementation-only-handoff/result.json", producer="context_history", phase="REPORT", lifecycle="CREATE_ONCE", cap=4 * 1024 * 1024, readback="VERIFIED")
    add(f"{RUNREL}/implementation-only-handoff/commit-message.txt", producer="context_history", phase="REPORT", lifecycle="CREATE_ONCE", cap=32 * 1024, readback="VERIFIED")
    root_log_rule = static_rule("代理協作開發紀錄.md", producer="collaboration_recorder", phase="REPORT", lifecycle="DRAFT_BEFORE_FREEZE", cap=8 * 1024 * 1024, readback="VERIFIED", extra={"exact_parent": "", "allowed_phase": ["BOOTSTRAP", "REPORT"]})
    rules.append(root_log_rule)
    for path in ("tools/evidence_io.py", "tools/output_policy.py", "tools/transaction_chain.py", "tools/inventory_pair.py", "tools/tail_audit.py", "tools/run_draft_checks.py", "tools/prepare_input_annex.py", "tools/prepare_e01_pipcache_readback.py", "tools/prepare_historical_source_recovery.py", "tools/prepare_epoch.py", "tools/prepare_dependencies.py", "checks/run_command.py", "checks/test_evidence_policy.py", "checks/test_run_command.py"):
        add(f"{RUNREL}/{path}", producer="context_history", phase="BOOTSTRAP", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
    add(f"{RUNREL}/tools/prepare_production_family.py", producer="context_history", phase="PRODUCT_EDIT", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
    rules.append(static_rule(f"{RUNREL}/代理協作開發紀錄.md", producer="collaboration_recorder", phase="REPORT", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024, extra={"allowed_phase": ["BOOTSTRAP", "REPORT"]}))
    for path in ("evidence/read-only-user-input-01.json", "evidence/read-only-user-input-01.receipt.json", "evidence/recorder-log-initial-01.md", "evidence/recorder-log-initial-01.receipt.json", "evidence/e01-pip-cache-current-readback-01.json", "evidence/e01-pip-cache-current-readback-01.receipt.json"):
        add(f"{RUNREL}/{path}", producer="tools/prepare_input_annex.py", phase="BOOTSTRAP", cap=8 * 1024 * 1024)
    rules[-2]["producer"] = "tools/prepare_e01_pipcache_readback.py"
    rules[-2]["rule_id"] = "r-" + sha((f"{RUNREL}/evidence/e01-pip-cache-current-readback-01.json").encode())[:16]
    rules[-1]["producer"] = "tools/prepare_e01_pipcache_readback.py"
    rules[-1]["rule_id"] = "r-" + sha((f"{RUNREL}/evidence/e01-pip-cache-current-readback-01.receipt.json").encode())[:16]
    add(f"{RUNREL}/evidence/historical-source-recovery-01", producer="tools/prepare_historical_source_recovery.py", phase="BOOTSTRAP", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    for name, cap in (("prepare_dependencies.py", 128 * 1024), ("prepare_epoch.py", 192 * 1024),
                      ("recovery-manifest.json", 1 * 1024 * 1024), ("recovery-receipt.json", 1 * 1024 * 1024)):
        add(f"{RUNREL}/evidence/historical-source-recovery-01/{name}", producer="tools/prepare_historical_source_recovery.py", phase="BOOTSTRAP", cap=cap)
    add(f"{RUNREL}/evidence/d01/cua-host-spec.json", producer="tools/prepare_d01.py", phase="D01_SPEC", cap=1 * 1024 * 1024)
    add(f"{RUNREL}/evidence/d01", producer="tools/prepare_d01.py", phase="D01_SPEC", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    add(f"{RUNREL}/evidence/d01/artifacts", producer="tools/prepare_d01.py", phase="D01_SPEC", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    add(f"{RUNREL}/evidence/d01/directory-setup-receipt.json", producer="tools/prepare_d01.py", phase="D01_SPEC", cap=1 * 1024 * 1024)
    for path in ("evidence/d01/source-freeze.json", "evidence/d01/spec-freeze.json", "evidence/d01/freeze-claim.json", "evidence/d01/freeze-receipt.json"):
        add(f"{RUNREL}/{path}", producer="tools/prepare_d01.py", phase="D01_SPEC_FREEZE", cap=1 * 1024 * 1024)
    add(f"{RUNREL}/evidence/d01/check-claim.json", producer="tools/run_d01.py", phase="D01_CLAIM", cap=1 * 1024 * 1024)
    add(f"{RUNREL}/evidence/d01/capture-registration.json", producer="cua_host", phase="D01_CAPTURE", cap=1 * 1024 * 1024)
    add(f"{RUNREL}/evidence/d01/capture-receipt.json", producer="cua_host", phase="D01_CAPTURE", cap=1 * 1024 * 1024)
    for kind, extension, cap in (("raw-ax", "json", 4 * 1024 * 1024), ("screenshot-png", "png", 8 * 1024 * 1024), ("native-context", "json", 2 * 1024 * 1024)):
        add(f"{RUNREL}/evidence/d01/artifacts/{kind}-0001.{extension}", producer="cua_host", phase="D01_CAPTURE", cap=cap, receipt=f"{RUNREL}/evidence/d01/capture-receipt.json", extra={"registration_required": True, "registration_path": f"{RUNREL}/evidence/d01/capture-registration.json"})
    for path in ("evidence/bootstrap-anchors.json", "evidence/controller-readiness.json", "evidence/namespace-pair-prewrite.json", "evidence/bootstrap-publications.json", "evidence/canonical-preimage.json", "evidence/draft-e01-second-pass.json", "evidence/draft-e01-current-pass.json", "evidence/draft-e02-second-pass.json", "evidence/draft-e02-current-pass.json", "evidence/draft-family-source-01.json", "evidence/draft-family-source-02.json", "evidence/epoch-materialization-plan.json"):
        add(f"{RUNREL}/{path}", producer="bootstrap-capture", phase="BOOTSTRAP", cap=8 * 1024 * 1024)
    for path in ("evidence/draft-e03-readiness-01.json", "evidence/draft-e03-family-binding-01.json", "evidence/draft-e03-family-binding-02.json"):
        add(f"{RUNREL}/{path}", producer="context_history", phase="BOOTSTRAP", lifecycle="CREATE_ONCE", cap=1 * 1024 * 1024, readback="VERIFIED")
    for path in ("evidence/draft-e03-readiness-03.json", "evidence/draft-e03-rootlog-01.json"):
        add(f"{RUNREL}/{path}", producer="context_history", phase="BOOTSTRAP", lifecycle="CREATE_ONCE", cap=4 * 1024 * 1024, readback="VERIFIED")
    add(f"{PRIOR_RUNREL}/prewrite-anchors.json", producer="bootstrap-capture", phase="BOOTSTRAP", cap=8 * 1024 * 1024)
    add(f"{RUNREL}/{plan_rel()}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024)
    for path in ("evidence/dependency-bootstrap-policy.json", dependency_policy_rel()):
        add(f"{RUNREL}/{path}", producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", cap=1024 * 1024)
    for path in ("evidence/attempt-ledger-07.json", "evidence/implementation-result.json", "evidence/report-manifest.json", "evidence/publication-tail-receipt.json", "evidence/acceptance.result.json"):
        add(f"{RUNREL}/{path}", producer="report-publisher", phase="REPORT", cap=8 * 1024 * 1024)
    for path in ("production-source-freeze.json", "production-check-specs.json", "production-check-specs-freeze.json", "production-output-policy.json", "runtime-binding.json", "authorization.json", "live-grant-1.json", "live-grant-2.json", "plan-review-waiver.json", "attempt-extension.json"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_production_family.py", phase="PRODUCTION_FREEZE", cap=4 * 1024 * 1024)
    for path in ("production-freeze-claim.json", "production-freeze-receipt.json"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_production_family.py", phase="PRODUCTION_FREEZE", cap=1 * 1024 * 1024)
    production_ids = ("N01-syntax-01", "N01-syntax-02", "N01-syntax-03", "N01-syntax-04", "N01-syntax-05", "N01-syntax-06", "N01-syntax-07", "N02-tests", "P01-batch", "P02-binding", "P03-transaction", "P04-v2", "S01-build", "S02-tests")
    for check_id in production_ids:
        base = f"{EPOCHREL}/evidence/checks/{check_id}"
        receipt = base + ".receipt.json"
        for suffix in ("claim.json", "invocation.json", "stdout", "stderr", "receipt.json"):
            add(base + "." + suffix, producer="checks/run_command.py", phase="RUN_CHECK", cap=16 * 1024 * 1024 if suffix in ("stdout", "stderr") else 1_000_000, receipt=receipt if suffix in ("invocation.json", "stdout", "stderr") else "NONE", claim=base + ".claim.json" if suffix in ("invocation.json", "stdout", "stderr") else None, extra={"check_id": check_id, "family": "production"})
    for path in ("module-cache", "module-cache/clang", "module-cache/swift", "fixtures", "fixtures/swift-inspection"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_production_family.py", phase="PRODUCTION_FREEZE", entry_type="DIRECTORY", cap=0, readback="IDENTITY", receipt=f"{EPOCHREL}/production-freeze-receipt.json")
    for path in PRODUCT:
        if path.endswith("/tools/prepare_production_family.py"):
            continue
        if path.endswith(("/tools/prepare_d01.py", "/tools/run_d01.py")):
            add(path, producer="context_history", phase="D01_TOOL_EDIT", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
        else:
            swift_path = path.startswith("rev28/")
            add(path, producer="implementation_feasibility" if swift_path else "context_history", phase="PRODUCT_EDIT", lifecycle="DRAFT_BEFORE_FREEZE", cap=4 * 1024 * 1024)
    add(f"{RUNREL}/bin", producer="tools/publish_rev28ctl.py", phase="BUILD_PUBLISH", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    add(f"{RUNREL}/bin/rev28ctl", producer="tools/publish_rev28ctl.py", phase="BUILD_PUBLISH", cap=64 * 1024 * 1024, receipt=f"{RUNREL}/evidence/build-publication-receipt.json")
    add(f"{RUNREL}/evidence/build-publication-receipt.json", producer="tools/publish_rev28ctl.py", phase="BUILD_PUBLISH", cap=1 * 1024 * 1024)
    dependency_receipt = f"{EPOCHREL}/runtime/dependency-preparation-receipt.json"
    for path in ("", "runtime", "runtime/wheels", "runtime/site-packages", "tmp", "tmp/pip-cache"):
        rel = EPOCHREL if not path else f"{EPOCHREL}/{path}"
        add(rel, producer="tools/prepare_dependencies.py", phase="RUNTIME_PREPARE", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
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
    for path in EVIDENCE_SOURCES:
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024, receipt=material_receipt)
    add(material_receipt, producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024)
    for path in ("tools", "checks", "evidence", "evidence/artifacts", "evidence/transactions", "evidence/checks", "evidence/inventory", "evidence/registrations"):
        add(f"{EPOCHREL}/{path}", producer="tools/prepare_epoch.py", phase="MATERIALIZE", entry_type="DIRECTORY", cap=0, readback="IDENTITY")
    for check_id in [spec["check_id"] for spec in check_specs()]:
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
    rules.append({"rule_id": "dynamic-registrations", "path_template": f"{EPOCHREL}/evidence/registrations/{{kind}}-{{sequence:04d}}.json", "exact_parent": f"{EPOCHREL}/evidence/registrations", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 1000000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 64})
    rules.append({"rule_id": "dynamic-artifacts", "path_template": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}.{{extension}}", "exact_parent": f"{EPOCHREL}/evidence/artifacts", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 33554432, "lifecycle": "CREATE_ONCE", "required_receipt": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}-receipt.json", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 64, "extensions": extensions, "registration_required": True, "registration_path": f"{EPOCHREL}/evidence/registrations/{{kind}}-{{sequence:04d}}.json"})
    rules.append({"rule_id": "dynamic-artifact-receipts", "path_template": f"{EPOCHREL}/evidence/artifacts/{{kind}}-{{sequence:04d}}-receipt.json", "exact_parent": f"{EPOCHREL}/evidence/artifacts", "producer": "live_entry", "allowed_phase": ["LIVE_EVIDENCE"], "entry_type": "REGULAR", "max_bytes": 1000000, "lifecycle": "CREATE_ONCE", "required_receipt": "NONE", "readback_requirement": "VERIFIED", "allowed_kinds": kinds, "sequence_min": 1, "sequence_max": 64})
    return {"format": "ML07_OUTPUT_POLICY_V2", "family": "evidence", "task_id": TASK, "epoch": str(EPOCH), "source_freeze_sha256": source_sha, "rules": rules}


def publish_checked(policy: OutputPolicy, rel: str, raw: bytes, *, producer: str, phase: str, cap: int) -> dict:
    decision = policy.authorize_prewrite(path=rel, phase=phase, producer=producer, entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=os.path.lexists(ROOT / rel))
    if not decision.allowed:
        raise RuntimeError(f"PUBLISH_POLICY:{decision.code}:{rel}")
    return publish_exclusive(ROOT, rel, raw, max_bytes=cap)


def main() -> int:
    head, branch, index, status_sha256, dependency_preflight = preflight_materialization()
    if ACTION == "preflight":
        namespace = namespace_preflight(dependency_preflight)
        print(json.dumps({"format": "ML07_E02_PURE_PREFLIGHT_V1", "task_id": TASK, "epoch": str(EPOCH),
                          "verdict": namespace["verdict"], "dependency": dependency_preflight,
                          "namespace": namespace,
                          "git_head": head, "branch": branch, "index_sha256": sha(index.read_bytes()),
                          "status_porcelain_sha256": status_sha256, "formal_claim_created": False},
                         ensure_ascii=False, sort_keys=True))
        return 0
    source_hashes = {f"{EPOCHREL}/{path}": sha((R / path).read_bytes()) for path in EVIDENCE_SOURCES}
    source_hashes[SCANNER] = sha((ROOT / SCANNER).read_bytes())
    source_hashes[f"{RUNREL}/tools/prepare_epoch.py"] = sha((R / "tools/prepare_epoch.py").read_bytes())
    source_hashes[f"{RUNREL}/tools/prepare_dependencies.py"] = sha((R / "tools/prepare_dependencies.py").read_bytes())
    for path in e02_inputs:
        source_hashes[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    source_hashes[f"{RUNREL}/plan-contract.json"] = sha((R / "plan-contract.json").read_bytes())
    for path in ("replan-amendment-01.md", "replan-amendment-02.md", "replan-amendment-03.md", "replan-amendment-04.md", "replan-amendment-05.md", "replan-amendment-06.md", "implementation-only-handoff/implementation-plan.md", "implementation-only-handoff/plan-contract.json", "implementation-only-handoff/handoff.json", "implementation-only-handoff/original-plan-contract.json", "implementation-only-handoff/compiled-handoff.json", "evidence/overlay-plan-review-06.json", "evidence/draft-e03-readiness-03.json", "evidence/draft-e03-rootlog-01.json", dependency_policy_rel(), "evidence/read-only-user-input-01.json", "evidence/read-only-user-input-01.receipt.json", "evidence/recorder-log-initial-01.md", "evidence/recorder-log-initial-01.receipt.json", "evidence/e01-pip-cache-current-readback-01.json", "evidence/e01-pip-cache-current-readback-01.receipt.json", "evidence/draft-e03-readiness-01.json", "evidence/draft-e03-family-binding-01.json", "evidence/draft-e03-family-binding-02.json"):
        source_hashes[f"{RUNREL}/{path}"] = sha((R / path).read_bytes())
    for name in ("prepare_dependencies.py", "prepare_epoch.py", "recovery-manifest.json", "recovery-receipt.json"):
        rel = f"evidence/historical-source-recovery-01/{name}"
        source_hashes[f"{RUNREL}/{rel}"] = sha((R / rel).read_bytes())
    for path in ("evidence/bootstrap-anchors.json", "evidence/namespace-pair-prewrite.json", "evidence/bootstrap-publications.json", "evidence/canonical-preimage.json"):
        source_hashes[f"{RUNREL}/{path}"] = sha((R / path).read_bytes())
    source_hashes[f"{PRIOR_RUNREL}/prewrite-anchors.json"] = sha((ROOT / PRIOR_RUNREL / "prewrite-anchors.json").read_bytes())
    runtime = EPOCH / "runtime"
    for path in sorted(runtime.rglob("*")):
        if path.is_file() and not path.is_symlink():
            source_hashes[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    executables = {str(PY): sha(PY.read_bytes())}
    source_freeze = {"format": "ML07_EVIDENCE_SOURCE_FREEZE_V2", "family": "evidence", "task_id": TASK, "epoch": str(EPOCH), "source_hashes": source_hashes, "executables": executables}
    source_bytes = encoded(source_freeze); source_sha = sha(source_bytes)
    policy_bytes = encoded(policy_document(source_sha))
    policy = OutputPolicy(json.loads(policy_bytes), ROOT)
    plan = {"task_id": TASK, "epoch": str(EPOCH), "head": head, "branch": branch, "index_sha256": sha(index.read_bytes()), "status_porcelain_sha256": status_sha256, "source_freeze_sha256": source_sha, "policy_sha256": sha(policy_bytes), "formal_sources": source_hashes, "dependency_preflight": dependency_preflight, "publication_order": ["source-freeze", "output-policy", "formal-source-copies", "check-specs", "check-specs-freeze", "materialization-receipt", "dependency-finalization-receipt", "formal-checks"]}
    publish_checked(policy, f"{RUNREL}/{plan_rel()}", encoded(plan), producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024)
    refs = []
    for rel, raw in ((f"{EPOCHREL}/source-freeze.json", source_bytes), (f"{EPOCHREL}/output-policy.json", policy_bytes)):
        refs.append(publish_checked(policy, rel, raw, producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024))
    for directory in ("tools", "checks", "evidence", "evidence/artifacts", "evidence/transactions", "evidence/checks", "evidence/inventory", "evidence/registrations"):
        rel = f"{EPOCHREL}/{directory}"
        decision = policy.authorize_prewrite(path=rel, phase="MATERIALIZE", producer="tools/prepare_epoch.py", entry_type="DIRECTORY", byte_count=0, operation="CREATE", preexisting=os.path.lexists(ROOT / rel))
        if not decision.allowed:
            raise RuntimeError("DIRECTORY_POLICY:" + decision.code + ":" + rel)
        refs.append(mkdir_exclusive(ROOT, rel))
    for path in EVIDENCE_SOURCES:
        rel = f"{EPOCHREL}/{path}"; raw = (R / path).read_bytes()
        decision = policy.authorize_prewrite(path=rel, phase="MATERIALIZE", producer="tools/prepare_epoch.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE")
        if not decision.allowed: raise RuntimeError("MATERIALIZE_POLICY:" + decision.code)
        refs.append(publish_checked(policy, rel, raw, producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024))
    checks = check_specs()
    for check in checks:
        check["family"] = "evidence"
    specs = {"format": "ML07_CHECK_SPECS_V2", "family": "evidence", "task_id": TASK, "epoch": str(EPOCH), "checks": checks, "automatic_retry": False}
    spec_raw = encoded(specs)
    spec_ref = publish_checked(policy, f"{EPOCHREL}/check-specs.json", spec_raw, producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024);refs.append(spec_ref)
    freeze = {"format": "ML07_CHECK_SPECS_FREEZE_V2", "family": "evidence", "task_id": TASK, "epoch": str(EPOCH), "head": head, "branch": branch, "index_sha256": sha(index.read_bytes()), "source_freeze_sha256": source_sha, "specs_sha256": sha(spec_raw), "policy_sha256": sha(policy_bytes), "source_hashes": source_hashes, "executables": executables}
    freeze_ref = publish_checked(policy, f"{EPOCHREL}/check-specs-freeze.json", encoded(freeze), producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024);refs.append(freeze_ref)
    receipt = {"format": "ML07_EPOCH_MATERIALIZATION_RECEIPT_V1", "task_id": TASK, "epoch": str(EPOCH), "phase": "MATERIALIZE", "producer": "tools/prepare_epoch.py", "source_freeze_sha256": source_sha, "artifacts": refs}
    receipt_ref = publish_checked(policy, f"{EPOCHREL}/evidence/materialization-receipt.json", encoded(receipt), producer="tools/prepare_epoch.py", phase="MATERIALIZE", cap=4 * 1024 * 1024)
    print(json.dumps({"source_freeze_sha256": source_sha, "policy_sha256": sha(policy_bytes), "specs_sha256": sha(spec_raw), "receipt": receipt_ref}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
