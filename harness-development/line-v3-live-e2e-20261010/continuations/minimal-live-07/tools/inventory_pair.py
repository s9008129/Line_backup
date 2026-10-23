#!/usr/bin/env python3
"""ML07 complete paired inventory with prewrite-anchor reconciliation."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import sys
import time
import zlib

from evidence_io import open_anchored_directory, publish_exclusive
from output_policy import OutputPolicy
from transaction_chain import validate_ledger_chain, validate_state_chain

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
EPOCH = pathlib.Path(os.path.realpath(__file__)).parent.parent
SCANNER = ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/tools/inventory.py"
FIFO_REL = "evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo"
TASK_ID = "TASK-20261010-line-v3-live-e2e"
CAP = 128 * 1024 * 1024
PRODUCT_PATHS = {
    "scripts/line_backup_cua_adapter.mjs", "src/line_backup_batch/cli.py",
    "src/line_backup_batch/observations.py", "src/line_backup_batch/store.py",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift",
    "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift",
    "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift",
    "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift",
}
STATE = "state/backup_state.json"
LEDGER = "harness-development/line-v3-live-e2e-20261010/gui-ledger.json"
BACKUP = "backups/旻謙允禎成長日記"
BASELINE_E03 = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07/epochs/e03"
E01 = ROOT / RUNREL / "epochs/e01"
E01_REL = f"{RUNREL}/epochs/e01"
E02 = ROOT / RUNREL / "epochs/e02"
E02_REL = f"{RUNREL}/epochs/e02"
READ_ONLY_USER_INPUT = "codex-session-01a12976-2554-7ed0-8d4c-356688f674ee.md"
ROOT_COLLABORATION_LOG = "代理協作開發紀錄.md"


def _in_scratch(path: str) -> bool:
    epochrel = EPOCH.relative_to(ROOT).as_posix()
    roots = (RUNREL + "/tmp", RUNREL + "/swift-build", RUNREL + "/module-cache", RUNREL + "/fixtures",
             epochrel + "/tmp", epochrel + "/module-cache", epochrel + "/swift-build", epochrel + "/fixtures")
    return any(path == root or path.startswith(root + "/") for root in roots)


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def command(*argv: str) -> bytes:
    if argv and argv[0] == "git":
        argv = ("git", "--no-optional-locks", *argv[1:])
    return subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def scanner_module():
    spec = importlib.util.spec_from_file_location("ml07_frozen_readonly_scanner", SCANNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("SCANNER_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_only_user_input_observation() -> dict:
    annex_path = R / "evidence/read-only-user-input-01.json"
    receipt_path = R / "evidence/read-only-user-input-01.receipt.json"
    annex_raw = annex_path.read_bytes()
    receipt_raw = receipt_path.read_bytes()
    annex = json.loads(annex_raw)
    receipt = json.loads(receipt_raw)
    source_fstat = annex.get("source_fstat", {})
    annex_ref = receipt.get("annex", {})
    if (annex.get("authority") != "READ_ONLY_USER_INPUT" or annex.get("user_reference") != READ_ONLY_USER_INPUT
            or annex.get("source_absolute_path") != str(ROOT / READ_ONLY_USER_INPUT)
            or annex.get("source_producer") is not None or annex.get("source_write_authority") is not None
            or receipt.get("source_fstat") != source_fstat or receipt.get("decision_owner") != "root_planner"
            or receipt.get("publisher") != "context_history" or annex_ref.get("path") != f"{RUNREL}/evidence/read-only-user-input-01.json"
            or annex_ref.get("bytes") != len(annex_raw) or annex_ref.get("sha256") != sha(annex_raw)):
        raise RuntimeError("READ_ONLY_USER_INPUT_ANNEX_RECEIPT")
    source = base64.b64decode(annex.get("source_base64", ""), validate=True)
    if len(source) != source_fstat.get("size") or sha(source) != source_fstat.get("sha256"):
        raise RuntimeError("READ_ONLY_USER_INPUT_ANNEX_CONTENT")
    parent_fd = open_anchored_directory(ROOT)
    try:
        fd = os.open(READ_ONLY_USER_INPUT, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise RuntimeError("READ_ONLY_USER_INPUT_TYPE")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk: break
                chunks.append(chunk)
            raw = b"".join(chunks)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        current = os.stat(READ_ONLY_USER_INPUT, dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)
    values = lambda s: {"dev": s.st_dev, "ino": s.st_ino, "mode": s.st_mode, "uid": s.st_uid, "gid": s.st_gid,
                        "size": s.st_size, "mtime_ns": s.st_mtime_ns, "ctime_ns": s.st_ctime_ns,
                        "birthtime": getattr(s, "st_birthtime", None)}
    observed = values(after)
    observed["sha256"] = sha(raw)
    if values(before) != values(after) or values(after) != values(current) or observed != source_fstat or raw != source:
        raise RuntimeError("READ_ONLY_USER_INPUT_CURRENT_IDENTITY_OR_HASH_DRIFT")
    return {"path": READ_ONLY_USER_INPUT, "fstat": observed, "sha256": observed["sha256"],
            "annex_path": f"{RUNREL}/evidence/read-only-user-input-01.json", "annex_sha256": sha(annex_raw),
            "receipt_path": f"{RUNREL}/evidence/read-only-user-input-01.receipt.json", "receipt_sha256": sha(receipt_raw)}


def scan_once(scanner, slot: int) -> dict:
    start = time.monotonic()
    input_before = _read_only_user_input_observation()
    pipcache_before = _e01_pipcache_observation()
    state = scanner.scan_tree(ROOT, fifo_abs=ROOT / FIFO_REL, allowlist_fifo=True, exclude_top_git=True, deadline_seconds=1200)
    input_after = _read_only_user_input_observation()
    pipcache_after = _e01_pipcache_observation()
    if input_before != input_after or pipcache_before != pipcache_after:
        raise RuntimeError("BOOTSTRAP_INPUT_CHANGED_DURING_SCAN")
    by_path = {x["path"]: x for x in state.records}
    if not _input_record_matches_annex(by_path.get(READ_ONLY_USER_INPUT, {})) or not _pipcache_record_matches(by_path.get(PIPCACHE, {}), pipcache_after):
        raise RuntimeError("BOOTSTRAP_INPUT_SCANNER_READBACK_MISMATCH")
    return {"format": "ML07_INVENTORY_SCAN_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "slot": slot,
            "captured_at_utc": utc(), "elapsed_seconds": time.monotonic()-start,
            "complete": state.complete, "timeout": state.timeout, "errors": state.errors,
            "policy": state.policy, "records": state.records,
            "read_only_user_input_observation": input_after,
            "e01_pipcache_observation": pipcache_after,
            "counts": {"total": len(state.records), "regular": sum(r.get("kind") == "REGULAR" for r in state.records)}}


def pair_compare(a: dict, b: dict) -> dict:
    if not a["complete"] or not b["complete"] or not a["policy"]["ok"] or not b["policy"]["ok"]:
        return {"verdict": "BLOCKED", "reason": "PARTIAL_TIMEOUT_OR_SPECIAL_POLICY", "added": [], "removed": [], "changed": []}
    first = {x["path"]: x for x in a["records"]}
    second = {x["path"]: x for x in b["records"]}
    added = sorted(second.keys()-first.keys()); removed = sorted(first.keys()-second.keys())
    changed = sorted(p for p in first.keys() & second.keys() if first[p] != second[p])
    return {"verdict": "PASS" if not (added or removed or changed) else "BLOCKED", "reason": "IDENTICAL_COMPLETE_PAIR" if not (added or removed or changed) else "WORKSPACE_CHANGED_DURING_PAIR", "added": added, "removed": removed, "changed": changed}


def _input_observation_matches_scan(scan: dict) -> bool:
    try:
        return scan.get("read_only_user_input_observation") == _read_only_user_input_observation()
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def _input_record_matches_annex(record: dict, observation: dict | None = None) -> bool:
    try:
        observed = observation or _read_only_user_input_observation()
        st = observed["fstat"]
        return (record.get("path") == READ_ONLY_USER_INPUT and record.get("kind") == "REGULAR"
                and record.get("mode") == stat.S_IMODE(st["mode"])
                and all(record.get(k) == st[v] for k, v in (("dev", "dev"), ("ino", "ino"),
                    ("uid", "uid"), ("gid", "gid"), ("bytes", "size"), ("mtime_ns", "mtime_ns"),
                    ("ctime_ns", "ctime_ns"), ("sha256", "sha256")))
                and record.get("read_verified") is True)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


PIPCACHE = f"{E01_REL}/tmp/pip-cache"


def _e01_pipcache_observation() -> dict:
    manifest_rel = f"{RUNREL}/evidence/e01-pip-cache-current-readback-01.json"
    receipt_rel = f"{RUNREL}/evidence/e01-pip-cache-current-readback-01.receipt.json"
    manifest_raw = (ROOT / manifest_rel).read_bytes()
    receipt_raw = (ROOT / receipt_rel).read_bytes()
    manifest = json.loads(manifest_raw); receipt = json.loads(receipt_raw)
    manifest_ref = receipt.get("artifact", {})
    if (manifest_ref.get("path") != manifest_rel or manifest_ref.get("bytes") != len(manifest_raw)
            or manifest_ref.get("sha256") != sha(manifest_raw) or receipt.get("producer") != "tools/prepare_e01_pipcache_readback.py"
            or receipt.get("phase") != "BOOTSTRAP" or receipt.get("readback_verified") is not True):
        raise RuntimeError("E01_PIPCACHE_CURRENT_RECEIPT")
    frozen = manifest.get("observation", {})
    if (manifest.get("format") != "ML07_E01_PIPCACHE_CURRENT_READBACK_V1" or frozen.get("path") != PIPCACHE
            or frozen.get("historical_inode_or_readback") != "UNKNOWN" or frozen.get("children") != []):
        raise RuntimeError("E01_PIPCACHE_CURRENT_MANIFEST")
    st = os.lstat(ROOT / PIPCACHE)
    children = sorted(os.listdir(ROOT / PIPCACHE))
    actual = {"path": PIPCACHE, "dev": st.st_dev, "ino": st.st_ino, "actual_type": "DIRECTORY",
              "mode": st.st_mode, "uid": st.st_uid, "gid": st.st_gid, "size": st.st_size,
              "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns, "children": children,
              "observed_at_utc": frozen.get("observed_at_utc"), "historical_inode_or_readback": "UNKNOWN"}
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or actual != frozen:
        raise RuntimeError("E01_PIPCACHE_CURRENT_DRIFT")
    policy = _e01_policy()
    rule = policy.rule_for(PIPCACHE)
    if (not rule or rule.get("exact_path") != PIPCACHE or rule.get("producer") != "tools/prepare_dependencies.py"
            or rule.get("allowed_phase") != ["RUNTIME_PREPARE"] or rule.get("entry_type") != "DIRECTORY"
            or rule.get("lifecycle") != "CREATE_ONCE" or rule.get("required_receipt") != "NONE"):
        raise RuntimeError("E01_PIPCACHE_POLICY_BINDING")
    bootstrap_policy_raw = (R / "evidence/dependency-bootstrap-policy.json").read_bytes()
    bootstrap_policy = json.loads(bootstrap_policy_raw)
    dep_receipt_raw = (E01 / "runtime/dependency-preparation-receipt.json").read_bytes()
    dep_receipt = json.loads(dep_receipt_raw)
    obs_rel = f"{E01_REL}/runtime/dependency-install-observation.json"
    manifest_dep_rel = f"{E01_REL}/runtime/dependency-input-manifest.json"
    obs_raw = (ROOT / obs_rel).read_bytes(); dep_manifest_raw = (ROOT / manifest_dep_rel).read_bytes()
    dep_manifest = json.loads(dep_manifest_raw); observation = json.loads(obs_raw)
    if (dep_receipt.get("task_id") != TASK_ID or dep_receipt.get("epoch") != str(E01)
            or dep_receipt.get("producer") != "tools/prepare_dependencies.py" or dep_receipt.get("phase") != "RUNTIME_PREPARE"
            or dep_receipt.get("source_freeze_sha256") != sha((E01 / "source-freeze.json").read_bytes())
            or dep_receipt.get("bootstrap_policy_sha256") != sha(bootstrap_policy_raw)
            or bootstrap_policy.get("task_id") != TASK_ID or bootstrap_policy.get("epoch") != str(E01)):
        raise RuntimeError("E01_PIPCACHE_DEPENDENCY_RECEIPT")
    artifact_map = {x.get("path"): x for x in dep_receipt.get("artifacts", [])}
    for rel, raw in ((obs_rel, obs_raw), (manifest_dep_rel, dep_manifest_raw)):
        ref = artifact_map.get(rel)
        if not ref or ref.get("bytes") != len(raw) or ref.get("sha256") != sha(raw) or ref.get("readback_verified") is not True:
            raise RuntimeError("E01_PIPCACHE_DEPENDENCY_ARTIFACT:" + rel)
    if (dep_manifest.get("policy_ref", {}).get("path") != f"{RUNREL}/evidence/dependency-bootstrap-policy.json"
            or dep_manifest.get("policy_ref", {}).get("sha256") != sha(bootstrap_policy_raw)
            or dep_manifest.get("policy_ref", {}).get("bytes") != len(bootstrap_policy_raw)
            or observation.get("exit_code") != 0 or observation.get("env_overrides", {}).get("TMPDIR") != str(ROOT / PIPCACHE)):
        raise RuntimeError("E01_PIPCACHE_DEPENDENCY_OBSERVATION")
    return {"path": PIPCACHE, "dev": st.st_dev, "ino": st.st_ino, "mode": st.st_mode,
            "uid": st.st_uid, "gid": st.st_gid, "size": st.st_size, "mtime_ns": st.st_mtime_ns,
            "ctime_ns": st.st_ctime_ns, "children": children, "readback_manifest_path": manifest_rel,
            "readback_manifest_sha256": sha(manifest_raw), "readback_receipt_path": receipt_rel,
            "readback_receipt_sha256": sha(receipt_raw), "dependency_receipt_sha256": sha(dep_receipt_raw),
            "dependency_observation_sha256": sha(obs_raw), "dependency_policy_sha256": sha(bootstrap_policy_raw),
            "historical_inode_or_readback": "UNKNOWN"}


def _pipcache_record_matches(record: dict, observation: dict) -> bool:
    return (record.get("path") == PIPCACHE and record.get("kind") == "DIRECTORY"
            and record.get("dev") == observation["dev"] and record.get("ino") == observation["ino"]
            and record.get("mode") == stat.S_IMODE(observation["mode"]) and record.get("uid") == observation["uid"]
            and record.get("gid") == observation["gid"] and record.get("size") == observation["size"]
            and record.get("mtime_ns") == observation["mtime_ns"] and record.get("ctime_ns") == observation["ctime_ns"]
            and record.get("entries") == [])


_E01_POLICY = None
_E01_SOURCE_LIMITATIONS = []
_E02_POLICY = None
_E02_SOURCE_LIMITATIONS = []


def _verified_historical_sources(source_hashes: dict) -> dict[str, bytes]:
    archive = R / "evidence/historical-source-recovery-01"
    manifest_path, receipt_path = archive / "recovery-manifest.json", archive / "recovery-receipt.json"
    if any(path.is_symlink() or not path.is_file() for path in (manifest_path, receipt_path)):
        raise RuntimeError("E01_HISTORICAL_RECOVERY_MISSING")
    manifest_raw, receipt_raw = manifest_path.read_bytes(), receipt_path.read_bytes()
    manifest, receipt = json.loads(manifest_raw), json.loads(receipt_raw)
    manifest_ref = receipt.get("manifest", {})
    if (manifest.get("format") != "ML07_HISTORICAL_SOURCE_RECOVERY_MANIFEST_V1"
            or receipt.get("format") != "ML07_HISTORICAL_SOURCE_RECOVERY_RECEIPT_V1"
            or manifest.get("publisher") != "context_history" or receipt.get("publisher") != "context_history"
            or manifest.get("decision_owner") != "root_planner" or receipt.get("decision_owner") != "root_planner"
            or manifest.get("source_authority") != "READ_ONLY_USER_INPUT"
            or manifest.get("source_producer") is not None or manifest.get("source_write_authority") is not None
            or manifest.get("old_e01_artifacts_modified") is not False
            or receipt.get("historical_metadata_restored") is not False or receipt.get("historical_tools_executed") is not False
            or manifest_ref.get("path") != f"{RUNREL}/evidence/historical-source-recovery-01/recovery-manifest.json"
            or manifest_ref.get("bytes") != len(manifest_raw) or manifest_ref.get("sha256") != sha(manifest_raw)
            or manifest_ref.get("readback_verified") is not True):
        raise RuntimeError("E01_HISTORICAL_RECOVERY_BINDING")
    annex_path = R / "evidence/read-only-user-input-01.json"
    annex_receipt_path = R / "evidence/read-only-user-input-01.receipt.json"
    annex_raw, annex_receipt_raw = annex_path.read_bytes(), annex_receipt_path.read_bytes()
    annex, annex_receipt = json.loads(annex_raw), json.loads(annex_receipt_raw)
    t = manifest.get("transcript", {})
    if (t.get("annex_path") != f"{RUNREL}/evidence/read-only-user-input-01.json"
            or t.get("annex_sha256") != sha(annex_raw)
            or t.get("annex_receipt_path") != f"{RUNREL}/evidence/read-only-user-input-01.receipt.json"
            or t.get("annex_receipt_sha256") != sha(annex_receipt_raw)
            or annex.get("authority") != "READ_ONLY_USER_INPUT"
            or annex.get("source_fstat", {}).get("sha256") != t.get("source_sha256")
            or annex_receipt.get("annex", {}).get("sha256") != sha(annex_raw)
            or annex_receipt.get("readback_verified") is not True):
        raise RuntimeError("E01_HISTORICAL_TRANSCRIPT_ANNEX_BINDING")
    recovered = {}
    expected = {
        "tools/prepare_dependencies.py": "prepare_dependencies.py",
        "tools/prepare_epoch.py": "prepare_epoch.py",
    }
    receipt_refs = {x.get("source_path"): x.get("archive", {}) for x in receipt.get("sources", [])}
    listed = {x.get("source_path"): x for x in manifest.get("recovered_sources", [])}
    for source_rel, archive_name in expected.items():
        source_path = f"{RUNREL}/{source_rel}"
        archived_path = archive / archive_name
        ref = receipt_refs.get(source_path, {})
        record = listed.get(source_path, {})
        if archived_path.is_symlink() or not archived_path.is_file():
            raise RuntimeError("E01_HISTORICAL_SOURCE_ARCHIVE_MISSING:" + source_path)
        raw = archived_path.read_bytes()
        frozen = source_hashes.get(source_path)
        if (record.get("e01_frozen_sha256") != frozen or record.get("recovered_sha256") != sha(raw)
                or record.get("recovered_bytes") != len(raw) or ref.get("path") != f"{RUNREL}/evidence/historical-source-recovery-01/{archive_name}"
                or ref.get("sha256") != sha(raw) or ref.get("bytes") != len(raw) or ref.get("readback_verified") is not True
                or frozen != sha(raw)):
            raise RuntimeError("E01_HISTORICAL_SOURCE_HASH_OR_RECEIPT:" + source_path)
        recovered[source_path] = raw
    return recovered


def _e01_policy():
    global _E01_POLICY, _E01_SOURCE_LIMITATIONS
    if _E01_POLICY is not None:
        return _E01_POLICY
    source_raw = (E01 / "source-freeze.json").read_bytes()
    specs_raw = (E01 / "check-specs.json").read_bytes()
    freeze_raw = (E01 / "check-specs-freeze.json").read_bytes()
    policy_raw = (E01 / "output-policy.json").read_bytes()
    source = json.loads(source_raw); specs = json.loads(specs_raw); freeze = json.loads(freeze_raw)
    policy_doc = json.loads(policy_raw)
    if (source.get("format") != "ML07_EVIDENCE_SOURCE_FREEZE_V1"
            or freeze.get("source_freeze_sha256") != sha(source_raw) or freeze.get("specs_sha256") != sha(specs_raw)
            or freeze.get("policy_sha256") != sha(policy_raw) or policy_doc.get("source_freeze_sha256") != sha(source_raw)
            or freeze.get("source_hashes") != source.get("source_hashes")
            or specs.get("task_id") != TASK_ID or specs.get("epoch") != str(E01)
            or freeze.get("task_id") != TASK_ID or freeze.get("epoch") != str(E01)
            or policy_doc.get("task_id") != TASK_ID or policy_doc.get("epoch") != str(E01)):
        raise RuntimeError("E01_FROZEN_FAMILY_BINDING")
    recovered_sources = _verified_historical_sources(source["source_hashes"])
    for rel, digest in source["source_hashes"].items():
        path = ROOT / rel
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("E01_FROZEN_SOURCE_DRIFT:" + rel)
        actual_digest = sha(path.read_bytes())
        if actual_digest != digest:
            if rel not in recovered_sources or sha(recovered_sources[rel]) != digest:
                raise RuntimeError("E01_FROZEN_SOURCE_DRIFT:" + rel)
            _E01_SOURCE_LIMITATIONS.append({"path": rel, "frozen_sha256": digest, "current_draft_sha256": actual_digest,
                                           "historical_bytes": "RECOVERED_EXACT_CONTENT_FROM_USER_TRANSCRIPT",
                                           "archive_path": f"{RUNREL}/evidence/historical-source-recovery-01/{pathlib.Path(rel).name}",
                                           "historical_metadata": "UNKNOWN_WHEN_NOT_RECORDED"})
    for absolute, digest in source.get("executables", {}).items():
        path = pathlib.Path(absolute)
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != digest:
            raise RuntimeError("E01_FROZEN_EXECUTABLE_DRIFT:" + absolute)
    material = json.loads((E01 / "evidence/materialization-receipt.json").read_bytes())
    material_refs = {x.get("path"): x for x in material.get("artifacts", [])}
    for rel, raw in ((f"{E01_REL}/source-freeze.json", source_raw), (f"{E01_REL}/output-policy.json", policy_raw),
                     (f"{E01_REL}/check-specs.json", specs_raw), (f"{E01_REL}/check-specs-freeze.json", freeze_raw)):
        ref = material_refs.get(rel)
        if not ref or ref.get("bytes") != len(raw) or ref.get("sha256") != sha(raw) or ref.get("readback_verified") is not True:
            raise RuntimeError("E01_MATERIALIZATION_REF:" + rel)
    # Preserve the consumed E01 results, including the historical B01 failure.
    spec_ids = {x.get("check_id") for x in specs.get("checks", [])}
    if not {"E01-evidence-policy", "E02-runner-selftest", "B01-baseline-pair"} <= spec_ids:
        raise RuntimeError("E01_FIXED_CHECK_SPECS")
    for check_id, verdict in (("E01-evidence-policy", "PASS"), ("E02-runner-selftest", "PASS"), ("B01-baseline-pair", "FAIL")):
        receipt_path = E01 / f"evidence/checks/{check_id}.receipt.json"
        receipt = json.loads(receipt_path.read_bytes())
        if (receipt.get("task_id") != TASK_ID or receipt.get("epoch") != str(E01)
                or receipt.get("check_id") != check_id
                or receipt.get("verdict") != verdict or receipt.get("source_freeze_sha256") != sha(source_raw)):
            raise RuntimeError("E01_FORMAL_RECEIPT_BINDING:" + check_id)
        expected_exit = 0 if verdict == "PASS" else 1
        if receipt.get("outcome", {}).get("exit_code") != expected_exit or receipt.get("outcome", {}).get("reaped") is not True:
            raise RuntimeError("E01_FORMAL_OUTCOME_BINDING:" + check_id)
    from output_policy import OutputPolicy
    _E01_POLICY = OutputPolicy(policy_doc, ROOT)
    return _E01_POLICY


def _e02_policy():
    """Load the immutable E02 evidence family and verify its pinned inputs."""
    global _E02_POLICY, _E02_SOURCE_LIMITATIONS
    if _E02_POLICY is not None:
        return _E02_POLICY
    source_raw = (E02 / "source-freeze.json").read_bytes()
    specs_raw = (E02 / "check-specs.json").read_bytes()
    freeze_raw = (E02 / "check-specs-freeze.json").read_bytes()
    policy_raw = (E02 / "output-policy.json").read_bytes()
    source = json.loads(source_raw)
    specs = json.loads(specs_raw)
    freeze = json.loads(freeze_raw)
    policy_doc = json.loads(policy_raw)
    if (source.get("format") != "ML07_EVIDENCE_SOURCE_FREEZE_V2"
            or source.get("task_id") != TASK_ID or source.get("epoch") != str(E02)
            or source.get("family") != "evidence"
            or specs.get("task_id") != TASK_ID or specs.get("epoch") != str(E02)
            or specs.get("family") != "evidence"
            or freeze.get("task_id") != TASK_ID or freeze.get("epoch") != str(E02)
            or freeze.get("family") != "evidence"
            or policy_doc.get("task_id") != TASK_ID or policy_doc.get("epoch") != str(E02)
            or policy_doc.get("family") != "evidence"
            or freeze.get("source_freeze_sha256") != sha(source_raw)
            or freeze.get("specs_sha256") != sha(specs_raw)
            or freeze.get("policy_sha256") != sha(policy_raw)
            or policy_doc.get("source_freeze_sha256") != sha(source_raw)
            or freeze.get("source_hashes") != source.get("source_hashes")
            or freeze.get("executables") != source.get("executables")):
        raise RuntimeError("E02_FROZEN_FAMILY_BINDING")
    for rel, digest in source.get("source_hashes", {}).items():
        live = ROOT / rel
        if not live.is_symlink() and live.is_file() and sha(live.read_bytes()) == digest:
            continue
        if not rel.startswith(RUNREL + "/"):
            raise RuntimeError("E02_FROZEN_SOURCE_DRIFT:" + rel)
        archived = E02 / rel[len(RUNREL) + 1:]
        if archived.is_symlink() or not archived.is_file() or sha(archived.read_bytes()) != digest:
            raise RuntimeError("E02_FROZEN_SOURCE_DRIFT:" + rel)
        _E02_SOURCE_LIMITATIONS.append({"path": rel, "frozen_sha256": digest,
                                        "current_draft_sha256": sha(live.read_bytes()) if live.is_file() and not live.is_symlink() else None,
                                        "archive_path": f"{E02_REL}/{rel[len(RUNREL) + 1:]}",
                                        "archive_sha256": digest})
    for absolute, digest in source.get("executables", {}).items():
        path = pathlib.Path(absolute)
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != digest:
            raise RuntimeError("E02_FROZEN_EXECUTABLE_DRIFT:" + absolute)
    material_path = E02 / "evidence/materialization-receipt.json"
    if material_path.is_symlink() or not material_path.is_file():
        raise RuntimeError("E02_MATERIALIZATION_RECEIPT_MISSING")
    material = json.loads(material_path.read_bytes())
    if (material.get("format") != "ML07_EPOCH_MATERIALIZATION_RECEIPT_V1"
            or material.get("task_id") != TASK_ID or material.get("epoch") != str(E02)
            or material.get("producer") != "tools/prepare_epoch.py"
            or material.get("phase") != "MATERIALIZE"
            or material.get("source_freeze_sha256") != sha(source_raw)):
        raise RuntimeError("E02_MATERIALIZATION_RECEIPT_BINDING")
    material_refs = {x.get("path"): x for x in material.get("artifacts", [])}
    if not material_refs:
        raise RuntimeError("E02_MATERIALIZATION_ARTIFACTS_MISSING")
    for rel, ref in material_refs.items():
        path = ROOT / rel
        if path.is_symlink() or not os.path.lexists(path):
            raise RuntimeError("E02_MATERIALIZATION_ARTIFACT_MISSING:" + str(rel))
        st = os.lstat(path)
        if stat.S_ISREG(st.st_mode):
            raw = path.read_bytes()
            if (ref.get("bytes") != len(raw) or ref.get("sha256") != sha(raw)
                    or ref.get("readback_verified") is not True):
                raise RuntimeError("E02_MATERIALIZATION_ARTIFACT_READBACK:" + str(rel))
        elif stat.S_ISDIR(st.st_mode):
            if (ref.get("dev") != st.st_dev or ref.get("ino") != st.st_ino
                    or ref.get("readback_verified") is not True):
                raise RuntimeError("E02_MATERIALIZATION_DIRECTORY_IDENTITY:" + str(rel))
        else:
            raise RuntimeError("E02_MATERIALIZATION_ARTIFACT_TYPE:" + str(rel))
    for rel, raw in ((f"{E02_REL}/source-freeze.json", source_raw),
                     (f"{E02_REL}/output-policy.json", policy_raw),
                     (f"{E02_REL}/check-specs.json", specs_raw),
                     (f"{E02_REL}/check-specs-freeze.json", freeze_raw)):
        ref = material_refs.get(rel)
        if (not ref or ref.get("bytes") != len(raw) or ref.get("sha256") != sha(raw)
                or ref.get("readback_verified") is not True):
            raise RuntimeError("E02_MATERIALIZATION_REF:" + rel)
    expected_ids = {"E01-evidence-policy", "E02-runner-selftest", "B01-baseline-pair", "B02-preservation-pair"}
    if not expected_ids <= {item.get("check_id") for item in specs.get("checks", [])}:
        raise RuntimeError("E02_FIXED_CHECK_SPECS")
    _E02_POLICY = OutputPolicy(policy_doc, ROOT)
    return _E02_POLICY


def _read_ref(path: str, *, directory: bool = False) -> dict:
    absolute = ROOT / path
    st = os.lstat(absolute)
    if directory:
        if not stat.S_ISDIR(st.st_mode):
            raise RuntimeError("HISTORICAL_DIRECTORY_TYPE:" + path)
        return {"path": path, "dev": st.st_dev, "ino": st.st_ino}
    if not stat.S_ISREG(st.st_mode):
        raise RuntimeError("HISTORICAL_FILE_TYPE:" + path)
    raw = absolute.read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": sha(raw), "dev": st.st_dev, "ino": st.st_ino,
            "readback_verified": True}


def _historical_e01_authorized(path: str, record: dict) -> tuple[bool, str]:
    try:
        policy = _e01_policy()
        rule = policy.rule_for(path)
        if not rule:
            return False, "NOT_IN_FROZEN_E01_POLICY"
        if rule.get("exact_path") != path:
            return False, "E01_DYNAMIC_PATH_REQUIRES_EXACT_REGISTRATION"
        if len(rule.get("allowed_phase", [])) != 1:
            return False, "E01_PHASE_AMBIGUOUS"
        phase = rule["allowed_phase"][0]
        kind = record.get("kind")
        if kind not in ("REGULAR", "DIRECTORY", "SYMLINK") or kind != rule["entry_type"]:
            return False, "E01_TYPE_MISMATCH"
        operation = "CREATE"
        if kind == "DIRECTORY":
            if path == PIPCACHE:
                observation = _e01_pipcache_observation()
                if not _pipcache_record_matches(record, observation):
                    return False, "E01_PIPCACHE_SCAN_MISMATCH"
            readback = _read_ref(path, directory=True)
            byte_count = 0
        elif kind == "REGULAR":
            readback = _read_ref(path)
            byte_count = readback["bytes"]
            if (record.get("bytes") != byte_count or record.get("sha256") != readback["sha256"]
                    or record.get("dev") != readback["dev"] or record.get("ino") != readback["ino"]):
                return False, "E01_FILE_INVENTORY_MISMATCH"
        else:
            return False, "E01_SYMLINK_REQUIRES_EXPLICIT_RECEIPT"
        receipt = _read_ref(rule["required_receipt"]) if rule["required_receipt"] != "NONE" else None
        registration = _read_ref(rule["registration_path"].replace("{kind}", record.get("kind", "")).replace("{sequence:04d}", "0001")) if rule.get("registration_required") else None
        result = policy.validate_observed(path=path, phase=phase, producer=rule["producer"], entry_type=kind,
                                          byte_count=byte_count, operation=operation, preexisting=False,
                                          registration_ref=registration, receipt_ref=receipt, readback_ref=readback)
        return result.allowed, result.code
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return False, f"E01_EVIDENCE:{type(exc).__name__}:{exc}"


def _historical_family_authorized(policy: OutputPolicy, epoch_rel: str, path: str,
                                  record: dict) -> tuple[bool, str]:
    """Verify one historical output against its exact frozen family rule/receipt."""
    try:
        if path != epoch_rel and not path.startswith(epoch_rel + "/"):
            return False, "OUTSIDE_HISTORICAL_EPOCH"
        rule = policy.rule_for(path)
        if not rule or rule.get("exact_path") != path:
            return False, "NOT_IN_FROZEN_EXACT_POLICY"
        phases = rule.get("allowed_phase", [])
        if len(phases) != 1:
            return False, "HISTORICAL_PHASE_AMBIGUOUS"
        phase = phases[0]
        kind = record.get("kind")
        if kind not in ("REGULAR", "DIRECTORY") or kind != rule.get("entry_type"):
            return False, "HISTORICAL_TYPE_MISMATCH"
        if kind == "REGULAR":
            readback = _read_ref(path)
            byte_count = readback["bytes"]
            if (record.get("bytes") != byte_count or record.get("sha256") != readback["sha256"]
                    or record.get("dev") != readback["dev"] or record.get("ino") != readback["ino"]
                    or record.get("read_verified") is not True):
                return False, "HISTORICAL_FILE_INVENTORY_MISMATCH"
        else:
            readback = _read_ref(path, directory=True)
            byte_count = 0
            if record.get("dev") != readback["dev"] or record.get("ino") != readback["ino"]:
                return False, "HISTORICAL_DIRECTORY_IDENTITY_MISMATCH"
        receipt_path = rule.get("required_receipt", "NONE")
        if receipt_path == "NONE":
            receipt = None
        elif "{" in receipt_path:
            return False, "HISTORICAL_RECEIPT_TEMPLATE_UNSUPPORTED"
        else:
            receipt = _read_ref(receipt_path)
        registration_path = rule.get("registration_path")
        if rule.get("registration_required"):
            if not registration_path or "{" in registration_path:
                return False, "HISTORICAL_REGISTRATION_TEMPLATE_UNSUPPORTED"
            registration = _read_ref(registration_path)
        else:
            registration = None
        result = policy.validate_observed(path=path, phase=phase, producer=rule["producer"],
                                          entry_type=kind, byte_count=byte_count,
                                          operation="CREATE", preexisting=False,
                                          registration_ref=registration, receipt_ref=receipt,
                                          readback_ref=readback)
        return result.allowed, result.code
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return False, f"HISTORICAL_EVIDENCE:{type(exc).__name__}:{exc}"


def _historical_e02_authorized(path: str, record: dict) -> tuple[bool, str]:
    try:
        return _historical_family_authorized(_e02_policy(), E02_REL, path, record)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return False, f"E02_FROZEN_EVIDENCE:{type(exc).__name__}:{exc}"


def _pending_artifacts_for_readiness(policy: OutputPolicy, epoch_rel: str,
                                     witness: dict) -> tuple[dict[str, dict], str | None]:
    """Accept only the predeclared exact 172 outputs awaiting dependency receipt."""
    receipt_rel = f"{epoch_rel}/runtime/dependency-preparation-receipt.json"
    items = witness.get("pending_artifacts") if isinstance(witness, dict) else None
    if (not isinstance(witness, dict)
            or witness.get("verdict") != "PREFLIGHT_READY_PENDING_PUBLICATION"
            or witness.get("formal_gate_pass") is not False
            or witness.get("task_id") != TASK_ID
            or witness.get("epoch") != str(EPOCH)
            or witness.get("pending_required_publication") != receipt_rel
            or witness.get("pending_artifact_count") != 172
            or not isinstance(items, list) or len(items) != 172):
        return {}, "PENDING_DEPENDENCY_WITNESS_INVALID"
    artifacts = {}
    for item in items:
        path = item.get("path") if isinstance(item, dict) else None
        digest = item.get("sha256") if isinstance(item, dict) else None
        try:
            valid_digest = isinstance(digest, str) and len(digest) == 64 and int(digest, 16) >= 0
        except ValueError:
            valid_digest = False
        if (not isinstance(path, str) or path in artifacts
                or not path.startswith(epoch_rel + "/runtime/")
                or item.get("entry_type") != "REGULAR"
                or type(item.get("bytes")) is not int or item["bytes"] < 0
                or not valid_digest):
            return {}, "PENDING_DEPENDENCY_ARTIFACT_INVALID"
        artifacts[path] = item
    declared = {rule.get("exact_path") for rule in policy.rules
                if rule.get("required_receipt") == receipt_rel}
    if set(artifacts) != declared:
        return {}, "PENDING_DEPENDENCY_POLICY_SET_MISMATCH"
    return artifacts, None


def _canon_kind(kind: str) -> str:
    return kind if kind in ("REGULAR", "DIRECTORY", "SYMLINK") else "SPECIAL"


def _kind(rec: dict) -> str:
    return _canon_kind({"D": "DIRECTORY", "F": "REGULAR", "L": "SYMLINK", "S": "SPECIAL"}.get(rec[1], "SPECIAL"))


def _anchor_identity_matches(path: str, old: list, new: dict) -> bool:
    """Compare stable identity; let lifecycle reconciliation handle mutable metadata."""
    old_kind = _kind(old)
    new_kind = _canon_kind(new.get("kind", "SPECIAL"))
    if new.get("kind") == "FIFO" and path != FIFO_REL:
        return False
    if path == FIFO_REL:
        if (old[1] != "S" or not stat.S_ISFIFO(old[4]) or new.get("kind") != "FIFO"
                or new.get("content_read") is not False or new.get("content_hash") is not None):
            return False
    elif old_kind != new_kind:
        return False
    return (
        old[2] == new.get("dev")
        and old[3] == new.get("ino")
        and stat.S_IMODE(old[4]) == new.get("mode")
        and old[5] == new.get("uid")
        and old[6] == new.get("gid")
        and (path != FIFO_REL or (old[7] == new.get("size")
             and old[8] == new.get("mtime_ns") and old[9] == new.get("ctime_ns")))
    )


def _children(paths: set[str], directory: str) -> set[str]:
    prefix = directory + "/" if directory else ""
    return {p[len(prefix):].split("/", 1)[0] for p in paths if p.startswith(prefix) and p != directory}


def _symlink_target_matches(anchor_target: str, record: dict) -> bool:
    return anchor_target == record.get("target") and record.get("sha256") == sha(os.fsencode(anchor_target))


def _authorized_bootstrap_delta(policy: OutputPolicy, before: dict, after: dict, path: str, operation: str, *, product: bool = False) -> tuple[bool, str]:
    rule = policy.rule_for(path)
    if not rule:
        return False, "UNKNOWN_BOOTSTRAP_PATH"
    if not path.startswith(RUNREL + "/") and path != ROOT_COLLABORATION_LOG and not (product and path in PRODUCT_PATHS):
        return False, "BOOTSTRAP_OUTSIDE_R"
    if rule["lifecycle"] not in ("CREATE_ONCE", "DRAFT_BEFORE_FREEZE", "PRODUCER_SCRATCH"):
        return False, "BOOTSTRAP_LIFECYCLE"
    expected = after or before
    kind = _kind(expected) if isinstance(expected, list) else _canon_kind(expected.get("kind"))
    if kind != rule["entry_type"]:
        return False, "BOOTSTRAP_TYPE"
    if operation == "MODIFY" and rule["lifecycle"] != "DRAFT_BEFORE_FREEZE":
        return False, "BOOTSTRAP_MODIFY_NON_DRAFT"
    allowed_phases = rule["allowed_phase"]
    if len(allowed_phases) == 1:
        phase = allowed_phases[0]
    elif (path in {f"{RUNREL}/E2E測試報告.md", f"{RUNREL}/progress.md",
                   f"{RUNREL}/evidence/attempt-ledger-draft.json", f"{RUNREL}/代理協作開發紀錄.md", ROOT_COLLABORATION_LOG}
          and set(allowed_phases) == {"BOOTSTRAP", "REPORT"}):
        frozen = EPOCH / "source-freeze.json"
        phase = "REPORT" if frozen.exists() else "BOOTSTRAP"
    else:
        return False, "AMBIGUOUS_POLICY_PHASE"
    if phase not in allowed_phases:
        return False, "POLICY_PHASE_NOT_ALLOWED"
    def disk_ref(rel: str | None) -> dict | None:
        if not rel:
            return None
        p = ROOT / rel
        if not p.is_file() or p.is_symlink():
            return None
        raw = p.read_bytes()
        return {"path": rel, "bytes": len(raw), "sha256": sha(raw)}
    registration = disk_ref(rule.get("registration_path"))
    receipt = disk_ref(rule["required_receipt"] if rule["required_receipt"] != "NONE" else None)
    readback = None
    if kind == "REGULAR":
        readback = {"path": path, "bytes": expected["size"], "sha256": expected["sha256"],
                    "dev": expected["dev"], "ino": expected["ino"],
                    "created_at_ns": expected["ctime_ns"], "readback_verified": True}
    elif kind == "DIRECTORY":
        readback = {"path": path, "dev": expected["dev"], "ino": expected["ino"]}
    decision = policy.validate_observed(path=path, phase=phase, producer=rule["producer"],
                                        entry_type=kind, byte_count=expected["size"] if kind == "REGULAR" else 0,
                                        operation=operation, preexisting=(operation != "CREATE"),
                                        registration_ref=registration, receipt_ref=receipt,
                                        readback_ref=readback)
    return decision.allowed, decision.code


def _fresh_git(anchor: dict) -> list[str]:
    problems = []
    if command("git", "rev-parse", "HEAD").decode().strip() != anchor["head"]:
        problems.append("HEAD_CHANGED")
    if command("git", "branch", "--show-current").decode().strip() != anchor["branch"]:
        problems.append("BRANCH_CHANGED")
    idx = pathlib.Path(anchor["index"]["path"])
    if sha(idx.read_bytes()) != anchor["index"]["sha256"]:
        problems.append("INDEX_CHANGED")
    if sha(command("git", "diff", "--binary", "--no-ext-diff")) != anchor["tracked_diff"]["sha256"]:
        problems.append("TRACKED_DIFF_CHANGED")
    if sha(command("git", "diff", "--cached", "--binary", "--no-ext-diff")) != anchor["cached_diff"]["sha256"]:
        problems.append("CACHED_DIFF_CHANGED")
    return problems


def _protected(anchor: dict) -> list[str]:
    problems = []
    for item in anchor["protected"]:
        p = ROOT / item["path"]
        if p.exists() != item["exists"]:
            problems.append("PROTECTED_EXISTENCE:" + item["path"])
            continue
        if item["exists"] and item.get("sha256") and (not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != item["sha256"]):
            problems.append("PROTECTED_CONTENT:" + item["path"])
    return problems


def baseline_compare(first: dict, second: dict, policy: OutputPolicy, *,
                     pending_dependency: dict | None = None) -> dict:
    pair = pair_compare(first, second)
    if pair["verdict"] != "PASS":
        return {**pair, "anchor_reconciliation": "BLOCKED"}
    anchor = json.loads((R / "evidence/bootstrap-anchors.json").read_bytes())
    namespace = json.loads((R / "evidence/namespace-pair-prewrite.json").read_bytes())
    if not namespace["equal"] or namespace["scan_1_errors"] or namespace["scan_2_errors"]:
        return {"verdict": "BLOCKED", "reason": "NAMESPACE_ANCHOR_INCOMPLETE"}
    raw = zlib.decompress(base64.b64decode(namespace["records_zlib_base64"]))
    if sha(raw) != namespace["records_sha256"] or len(raw) != namespace["records_bytes"]:
        return {"verdict": "BLOCKED", "reason": "NAMESPACE_ANCHOR_HASH"}
    old = {r[0]: r for r in json.loads(raw)}
    now = {r["path"]: r for r in second["records"]}
    problems = _fresh_git(anchor) + _protected(anchor)
    if not _input_observation_matches_scan(first) or not _input_observation_matches_scan(second):
        problems.append("READ_ONLY_USER_INPUT_SCAN_BINDING")
    try:
        pipcache_now = _e01_pipcache_observation()
        if first.get("e01_pipcache_observation") != pipcache_now or second.get("e01_pipcache_observation") != pipcache_now:
            problems.append("E01_PIPCACHE_SCAN_BINDING")
    except Exception as exc:
        pipcache_now = None
        problems.append(f"E01_PIPCACHE_READBACK:{type(exc).__name__}:{exc}")
    previous = json.loads((ROOT / "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/prewrite-anchors.json").read_bytes())
    for item in previous["anchor_1"]["protected_files"]:
        if item.get("sha256") and sha((ROOT / item["path"]).read_bytes()) != item["sha256"]:
            problems.append("HISTORICAL_PROTECTED:" + item["path"])
    added = sorted(now.keys()-old.keys()); removed = sorted(old.keys()-now.keys())
    changed = []
    pending_artifacts = {}
    pending_verified = []
    if pending_dependency is not None:
        pending_artifacts, pending_error = _pending_artifacts_for_readiness(
            policy, EPOCH.relative_to(ROOT).as_posix(), pending_dependency)
        if pending_error:
            problems.append(pending_error)
    if [p for p in removed if not _in_scratch(p)]:
        problems.append("REMOVED_PATHS")
    for p in added:
        if p == READ_ONLY_USER_INPUT:
            if not _input_record_matches_annex(now[p]):
                problems.append("READ_ONLY_USER_INPUT_ADDITION_MISMATCH")
            continue
        if p in pending_artifacts:
            item = pending_artifacts[p]
            record = now[p]
            if (record.get("kind") != item["entry_type"] or record.get("bytes") != item["bytes"]
                    or record.get("sha256") != item["sha256"] or record.get("read_verified") is not True):
                problems.append("PENDING_DEPENDENCY_INVENTORY_MISMATCH:" + p)
            else:
                pending_verified.append(p)
            continue
        if p == E01_REL or p.startswith(E01_REL + "/"):
            ok, reason = _historical_e01_authorized(p, now[p])
            if not ok: problems.append(f"HISTORICAL_E01_ADDITION:{p}:{reason}")
            continue
        if p == E02_REL or p.startswith(E02_REL + "/"):
            ok, reason = _historical_e02_authorized(p, now[p])
            if not ok: problems.append(f"HISTORICAL_E02_ADDITION:{p}:{reason}")
            continue
        if _in_scratch(p):
            continue
        ok, reason = _authorized_bootstrap_delta(policy, {}, now[p], p, "CREATE")
        if not ok: problems.append(f"ADDED:{p}:{reason}")
    for p in sorted(old.keys() & now.keys()):
        if _in_scratch(p):
            continue
        o, n = old[p], now[p]
        kind = _kind(o)
        if not _anchor_identity_matches(p, o, n):
            problems.append("IDENTITY_OR_MODE:" + p); continue
        if kind == "DIRECTORY":
            if o[7:10] != [n["size"], n["mtime_ns"], n["ctime_ns"]]:
                if _children(set(old), p) == _children(set(now), p):
                    problems.append("DIRECTORY_METADATA_WITHOUT_CHILD_DELTA:" + p)
                else:
                    changed.append(p)
        elif kind == "SYMLINK":
            if not _symlink_target_matches(o[10], n):
                problems.append("SYMLINK_TARGET_CHANGED:" + p)
            elif o[7:10] != [n["size"], n["mtime_ns"], n["ctime_ns"]]:
                problems.append("SYMLINK_METADATA_CHANGED:" + p)
        elif o[7:10] != [n["size"], n["mtime_ns"], n["ctime_ns"]]:
            ok, reason = _authorized_bootstrap_delta(policy, o, n, p, "MODIFY")
            if not ok: problems.append(f"CHANGED:{p}:{reason}")
            else: changed.append(p)
    if pending_artifacts:
        missing_pending = sorted(set(pending_artifacts) - set(pending_verified))
        if missing_pending:
            problems.extend("PENDING_DEPENDENCY_PATH_NOT_NEW:" + p for p in missing_pending)
    # Exact known early bootstrap publications have readback fingerprints.
    bootstrap = json.loads((R / "evidence/bootstrap-publications.json").read_bytes())
    for item in bootstrap["entries"]:
        if item["lifecycle"] == "DRAFT_BEFORE_FREEZE":
            continue
        p = ROOT / item["path"]
        if not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != item["sha256"]:
            problems.append("BOOTSTRAP_PUBLICATION_DRIFT:" + item["path"])
    categories = {}
    for problem in problems:
        parts = problem.split(":")
        category = f"ADDED:{parts[2]}" if parts[0] == "ADDED" and len(parts) > 2 else parts[0]
        categories[category] = categories.get(category, 0) + 1
    ready_pending = bool(pending_artifacts) and not problems and len(pending_verified) == len(pending_artifacts)
    return {"verdict": "BLOCKED" if problems or ready_pending else "PASS",
            "reason": "ANCHOR_OR_BOOTSTRAP_MISMATCH" if problems else "PENDING_REQUIRED_PUBLICATION" if ready_pending else "ANCHOR_BOOTSTRAP_GIT_PROTECTED_RECONCILED",
            "readiness": "READY_PENDING_PUBLICATION" if ready_pending else "BLOCKED" if problems else "READY",
            "formal_gate_pass": not problems and not ready_pending,
            "pending_required_publication": pending_dependency.get("pending_required_publication") if ready_pending else None,
            "pending_artifact_count": len(pending_verified),
            "pending_artifacts": pending_dependency.get("pending_artifacts", []) if ready_pending else [],
            "added": added, "removed": removed, "changed": changed, "problems": problems,
            "problem_count": len(problems), "problem_categories": categories,
            "namespace_record_count": len(old), "pair_record_count": len(now),
            "historical_e01_source_limitations": _E01_SOURCE_LIMITATIONS,
            "historical_e02_source_limitations": _E02_SOURCE_LIMITATIONS}


def _canonical_preimage() -> dict[str, bytes]:
    data = json.loads((R / "evidence/canonical-preimage.json").read_bytes())
    result = {}
    for entry in data["entries"]:
        raw = base64.b64decode(entry["base64"], validate=True)
        if len(raw) != entry["bytes"] or sha(raw) != entry["sha256"]:
            raise ValueError("CANONICAL_PREIMAGE_HASH")
        result[entry["path"]] = raw
    return result


def _transaction_chain() -> dict:
    path = EPOCH / "evidence/transactions/chain.json"
    if not path.exists():
        return {"state": [], "ledger": []}
    data = json.loads(path.read_bytes())
    if data.get("task_id") != TASK_ID or data.get("epoch") != str(EPOCH) or set(data) != {"task_id", "epoch", "state", "ledger"}:
        raise ValueError("TRANSACTION_CHAIN_IDENTITY")
    return data


def _registered_destinations(baseline_paths: set[str]) -> tuple[list[str], list[str]]:
    registry = EPOCH / "evidence/transactions/destinations.json"
    if not registry.exists():
        return [], []
    data = json.loads(registry.read_bytes())
    problems = []
    if data.get("task_id") != TASK_ID or data.get("epoch") != str(EPOCH):
        problems.append("DESTINATION_REGISTRY_IDENTITY")
    dests = data.get("destinations")
    if not isinstance(dests, list) or len(dests) > 2:
        return [], problems + ["DESTINATION_COUNT"]
    paths = []
    for item in dests:
        path = item.get("path")
        if not isinstance(path, str) or not path.startswith(BACKUP + "/") or path in baseline_paths or item.get("owner") not in ("minimal-live-07-g1", "minimal-live-07-g2") or item.get("registered_empty") is not True or not item.get("registration_ref"):
            problems.append("DESTINATION_REGISTRATION")
        else:
            paths.append(path)
    if len(paths) != len(set(paths)):
        problems.append("DESTINATION_DUPLICATE")
    return paths, problems


def preservation_compare(first: dict, second: dict, policy: OutputPolicy) -> dict:
    pair = pair_compare(first, second)
    if pair["verdict"] != "PASS":
        return {**pair, "baseline_comparison": "BLOCKED"}
    baseline, baseline_problem = _verified_e03_baseline()
    if baseline_problem:
        return {"verdict": "BLOCKED", "reason": baseline_problem}
    if not baseline.get("complete") or not baseline.get("policy", {}).get("ok"):
        return {"verdict": "BLOCKED", "reason": "BASELINE_SCAN_INCOMPLETE"}
    old = {r["path"]: r for r in baseline["records"]}
    now = {r["path"]: r for r in second["records"]}
    added = sorted(now.keys()-old.keys()); removed = sorted(old.keys()-now.keys())
    changed = sorted(p for p in old.keys() & now.keys() if old[p] != now[p])
    problems = []
    if not _input_observation_matches_scan(first) or not _input_observation_matches_scan(second):
        problems.append("READ_ONLY_USER_INPUT_SCAN_BINDING")
    baseline_scan_ref = baseline.get("read_only_user_input_observation")
    if baseline_scan_ref != first.get("read_only_user_input_observation") or baseline_scan_ref != second.get("read_only_user_input_observation"):
        problems.append("READ_ONLY_USER_INPUT_BASELINE_DRIFT")
    removed_scratch = [p for p in removed if _in_scratch(p)]
    if len(removed_scratch) != len(removed):
        problems.append("REMOVED_PATHS")
    destinations, destination_problems = _registered_destinations(set(old))
    problems.extend(destination_problems)
    for p in added:
        if _in_scratch(p):
            continue
        if p.startswith(RUNREL + "/"):
            ok, reason = _authorized_bootstrap_delta(policy, {}, now[p], p, "CREATE")
            if not ok: problems.append(f"ARTIFACT:{p}:{reason}")
        elif p in PRODUCT_PATHS:
            ok, reason = _authorized_bootstrap_delta(policy, {}, now[p], p, "CREATE", product=True)
            if not ok: problems.append(f"PRODUCT_ADD:{p}:{reason}")
        elif any(p == dest or p.startswith(dest + "/") for dest in destinations):
            if now[p]["kind"] not in ("DIRECTORY", "REGULAR") or (now[p]["kind"] == "REGULAR" and now[p]["size"] == 0):
                problems.append("NATIVE_DESTINATION_TYPE_OR_ZERO:" + p)
        else:
            problems.append("UNAUTHORIZED_ADDITION:" + p)
    for p in changed:
        if _in_scratch(p):
            continue
        a,b=old[p],now[p]
        if a["kind"] != b["kind"] or (a["dev"],a["ino"],a["mode"],a["uid"],a["gid"]) != (b["dev"],b["ino"],b["mode"],b["uid"],b["gid"]) and b["kind"] == "DIRECTORY":
            problems.append("IDENTITY_OR_MODE:" + p);continue
        if b["kind"] == "DIRECTORY":
            if _children(set(old),p) == _children(set(now),p):
                problems.append("DIRECTORY_METADATA_WITHOUT_CHILD_DELTA:" + p)
        elif p in (STATE, LEDGER):
            pass
        elif p in PRODUCT_PATHS or p.startswith(RUNREL + "/"):
            ok, reason = _authorized_bootstrap_delta(policy, a, b, p, "MODIFY", product=(p in PRODUCT_PATHS))
            if not ok: problems.append(f"CHANGED:{p}:{reason}")
        else:
            problems.append("UNAUTHORIZED_CHANGE:" + p)
    for p in old:
        if p.startswith(BACKUP + "/") and p in now and old[p]["kind"] != "DIRECTORY" and old[p] != now[p]:
            problems.append("ORIGINAL_BACKUP_CHANGED:" + p)
    try:
        pre = _canonical_preimage()
        chain = _transaction_chain()
        for p, validator, key in ((STATE, validate_state_chain, "state"), (LEDGER, validate_ledger_chain, "ledger")):
            if old[p]["sha256"] != sha(pre[p]):
                problems.append("BASELINE_CANONICAL_PREIMAGE:" + p)
            final = (ROOT / p).read_bytes()
            if sha(final) != now[p]["sha256"]:
                problems.append("POST_CANONICAL_HASH:" + p)
            problems.extend(validator(pre[p], final, chain[key], root=ROOT))
    except Exception as exc:
        problems.append(f"TRANSACTION_CHAIN_READ:{type(exc).__name__}:{exc}")
    return {"verdict": "PASS" if not problems else "BLOCKED", "reason": "AUTHORIZED_DELTA_AND_CANONICAL_CHAIN" if not problems else "PRESERVATION_DELTA_REQUIRES_REVIEW", "added": added, "removed": removed, "removed_scratch": removed_scratch, "changed": changed, "problems": problems[:200], "problem_count": len(problems)}


def _verified_e03_baseline() -> tuple[dict, str | None]:
    base = ROOT / BASELINE_E03 / "evidence/inventory"
    scan_rel = BASELINE_E03 + "/evidence/inventory/baseline-scan-01.json"
    receipt_rel = BASELINE_E03 + "/evidence/inventory/baseline-receipt.json"
    compare_rel = BASELINE_E03 + "/evidence/inventory/baseline-compare.json"
    check_base_rel = BASELINE_E03 + "/evidence/checks/B01-baseline-pair"
    stdout_rel = check_base_rel + ".stdout"
    check_receipt_rel = check_base_rel + ".receipt.json"
    tail_rel = BASELINE_E03 + "/evidence/inventory/baseline-tail-audit.json"
    try:
        check_receipt_raw = (ROOT / check_receipt_rel).read_bytes()
        check_receipt = json.loads(check_receipt_raw)
        receipt = json.loads((base / "baseline-receipt.json").read_bytes())
        compare = json.loads((base / "baseline-compare.json").read_bytes())
        tail = json.loads((ROOT / tail_rel).read_bytes())
        refs = {item.get("path"): item for item in receipt.get("artifacts", [])}
        ref = refs.get(scan_rel)
        compare_ref = refs.get(compare_rel)
        scan_raw = (base / "baseline-scan-01.json").read_bytes()
        compare_raw = (base / "baseline-compare.json").read_bytes()
        receipt_raw = (base / "baseline-receipt.json").read_bytes()
        stdout_raw = (ROOT / stdout_rel).read_bytes()
        source_sha = sha((ROOT / BASELINE_E03 / "source-freeze.json").read_bytes())
        check_artifacts = {item.get("path"): item for item in check_receipt.get("artifacts", [])}
        stdout_ref = check_artifacts.get(stdout_rel)
        child_stdout = json.loads(stdout_raw)
        inventory_receipt_ref = child_stdout.get("receipt", {})
        tail_checks = {item.get("check_id"): item for item in tail.get("verified_checks", [])}
        tail_b01 = tail_checks.get("B01-baseline-pair")
        tail_outputs = {item.get("suffix"): item.get("ref", {}) for item in (tail_b01 or {}).get("outputs", [])}
        check_receipt_ref = tail_outputs.get("receipt", {})
        tail_stdout_ref = tail_outputs.get("stdout", {})
        tail_inventory = {item.get("suffix"): item.get("ref", {}) for item in tail.get("inventory_outputs", [])}
        tail_scan = tail_inventory.get("scan-01.json", {})
        tail_receipt = tail_inventory.get("receipt.json", {})
        if (check_receipt.get("task_id") != TASK_ID or check_receipt.get("epoch") != str(ROOT / BASELINE_E03)
                or check_receipt.get("check_id") != "B01-baseline-pair" or check_receipt.get("family") != "evidence"
                or check_receipt.get("verdict") != "PASS" or check_receipt.get("outcome", {}).get("exit_code") != 0
                or check_receipt.get("outcome", {}).get("reaped") is not True or check_receipt.get("outcome", {}).get("stop_reason") is not None):
            return {}, "BASELINE_E03_CHECK_NOT_PASS"
        if (receipt.get("task_id") != TASK_ID or receipt.get("epoch") != str(ROOT / BASELINE_E03)
                or receipt.get("producer") != "tools/inventory_pair.py" or receipt.get("phase") != "INVENTORY"
                or receipt.get("source_freeze_sha256") != source_sha or receipt.get("mode") != "baseline" or receipt.get("verdict") != "PASS"):
            return {}, "BASELINE_E03_RECEIPT_NOT_PASS"
        if (tail.get("task_id") != TASK_ID or tail.get("epoch") != str(ROOT / BASELINE_E03)
                or tail.get("mode") != "baseline" or tail.get("verdict") != "PASS"
                or not tail_b01 or check_receipt_ref.get("path") != check_receipt_rel
                or check_receipt_ref.get("bytes") != len(check_receipt_raw) or check_receipt_ref.get("sha256") != sha(check_receipt_raw)):
            return {}, "BASELINE_E03_TAIL_CHECK_REF"
        if (not stdout_ref or stdout_ref.get("path") != stdout_rel or stdout_ref.get("bytes") != len(stdout_raw)
                or stdout_ref.get("sha256") != sha(stdout_raw) or child_stdout.get("verdict") != "PASS"
                or inventory_receipt_ref.get("path") != receipt_rel or inventory_receipt_ref.get("bytes") != len(receipt_raw)
                or inventory_receipt_ref.get("sha256") != sha(receipt_raw) or tail_stdout_ref.get("path") != stdout_rel
                or tail_stdout_ref.get("bytes") != len(stdout_raw) or tail_stdout_ref.get("sha256") != sha(stdout_raw)):
            return {}, "BASELINE_E03_RUNNER_STDOUT_REF"
        if not ref or ref.get("path") != scan_rel or ref.get("bytes") != len(scan_raw) or ref.get("sha256") != sha(scan_raw):
            return {}, "BASELINE_E03_SCAN_REF_MISMATCH"
        if not compare_ref or compare_ref.get("path") != compare_rel or compare_ref.get("bytes") != len(compare_raw) or compare_ref.get("sha256") != sha(compare_raw):
            return {}, "BASELINE_E03_COMPARE_REF_MISMATCH"
        if compare.get("verdict") != "PASS":
            return {}, "BASELINE_E03_COMPARE_NOT_PASS"
        if (tail_scan.get("path") != scan_rel or tail_scan.get("bytes") != len(scan_raw) or tail_scan.get("sha256") != sha(scan_raw)
                or tail_receipt.get("path") != receipt_rel or tail_receipt.get("bytes") != len(receipt_raw)
                or tail_receipt.get("sha256") != sha(receipt_raw)):
            return {}, "BASELINE_E03_TAIL_INVENTORY_REF"
        scan = json.loads(scan_raw)
        if scan.get("task_id") != TASK_ID or scan.get("epoch") != str(ROOT / BASELINE_E03):
            return {}, "BASELINE_E03_SCAN_IDENTITY"
        if not isinstance(receipt_raw, bytes):
            return {}, "BASELINE_E03_READBACK"
        return scan, None
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {}, "BASELINE_E03_MISSING_OR_INVALID"


def publish(mode: str, first: dict, second: dict, comparison: dict, policy: OutputPolicy) -> dict:
    base = f"{EPOCH.relative_to(ROOT).as_posix()}/evidence/inventory/{mode}"
    refs = []
    for suffix, doc in (("scan-01.json", first), ("scan-02.json", second), ("compare.json", comparison)):
        rel = f"{base}-{suffix}"; raw = encoded(doc)
        decision = policy.authorize_prewrite(path=rel, phase="INVENTORY", producer="tools/inventory_pair.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=(ROOT / rel).exists())
        if not decision.allowed: raise RuntimeError(f"POLICY:{decision.code}:{rel}")
        refs.append(publish_exclusive(ROOT, rel, raw, max_bytes=CAP))
    receipt = {"format": "ML07_INVENTORY_PAIR_RECEIPT_V1", "task_id": TASK_ID, "epoch": str(EPOCH), "phase": "INVENTORY", "producer": "tools/inventory_pair.py", "source_freeze_sha256": policy.source_freeze_sha256, "mode": mode, "verdict": comparison["verdict"], "artifacts": refs, "published_at_utc": utc(), "scanner": {"path": str(SCANNER), "sha256": sha(SCANNER.read_bytes())}, "fifo": {"path": FIFO_REL, "content_opened": False}}
    rel = f"{base}-receipt.json"; raw = encoded(receipt)
    decision = policy.authorize_prewrite(path=rel, phase="INVENTORY", producer="tools/inventory_pair.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=(ROOT / rel).exists())
    if not decision.allowed: raise RuntimeError(f"POLICY:{decision.code}:{rel}")
    receipt_ref = publish_exclusive(ROOT, rel, raw, max_bytes=1_000_000)
    return {"verdict": comparison["verdict"], "receipt": receipt_ref, "counts": second["counts"]}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("baseline", "preservation") or pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != EPOCH / "tools/inventory_pair.py" or EPOCH.parent != R / "epochs" or EPOCH.name not in ("e01", "e02", "e03"):
        print(json.dumps({"verdict": "REFUSED", "reason": "LOCATION_OR_ARGUMENTS"})); return 2
    mode = sys.argv[1]
    policy = OutputPolicy.load(EPOCH / "output-policy.json", ROOT)
    scanner = scanner_module()
    first = scan_once(scanner, 1)
    second = scan_once(scanner, 2)
    comparison = baseline_compare(first, second, policy) if mode == "baseline" else preservation_compare(first, second, policy)
    result = publish(mode, first, second, comparison, policy)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
