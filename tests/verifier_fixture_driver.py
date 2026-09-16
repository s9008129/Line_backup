#!/usr/bin/env python3
"""Subprocess acceptance driver for the real verify-only CLI (Rev15 §15.4 40-row matrix).

The fixture builder supplies inputs only.  Expected axes are read from the literal
manifest supplied by the caller, while the product process performs inventory,
association and artifact work.  The driver derives its own static expectation per row,
hashes every pre-state input before launch, runs the row's literal argv, and never
treats a product PASS line as its oracle.  It owns only its literal roots (Rev15 §15.5:
ownership marker before any fixture content, no default removal, explicit --clean-owned).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR / "automation_verification"))

import fixtures as F  # noqa: E402
import harness as H  # noqa: E402

ROOT = Path("/private/tmp/line-backup-acceptance-verifier")
PRODUCTION_ROOT = Path("/private/tmp/line-backup-acceptance-verifier-production")
DRIVER_ID = "verifier-fixture-driver"
GROUP = F.GROUP
OTHER_GROUP = "line:jp.naver.line.mac:other-group"
START_DATE = F.FP57["start_date"]
END_DATE = F.FP57["end_date"]
EXPECTED_IMAGES = F.FP57["expected_images"]
BASE_ARGV = ["/usr/bin/python3", "-m", "line_backup_acceptance", "verify-only"]

ORDERED_IDS = [
    "valid-57", "count-56", "count-58", "part-suffix", "partial-suffix", "tmp-suffix", "temp-suffix",
    "download-suffix", "crdownload-suffix", "incomplete-suffix", "filepart-suffix", "hidden-metadata",
    "symlink-entry", "outside-backup-root", "special-file", "unreadable-file", "file-command-error",
    "mime-mismatch", "safe-filenames", "mtime-at-sample-2", "bytes-at-sample-2", "wrong-group",
    "cross-entry", "legacy-record", "duplicate-registry", "invalid-config", "authority-mismatch",
    "artifact-readback-failure", "truncated-png", "jpeg-missing-eoi", "unsupported-image-type",
    "read-error-sample-2", "dangling-verified-run-id", "safe-abort-linked", "nonterminal-linked",
    "wrong-group-link", "forged-binding", "binding-artifact-deleted", "binding-artifact-mutated",
    "fixture-binding-in-production",
]

CASE_BY_ID = {
    "valid-57": "valid", "count-56": "56", "count-58": "58",
    "part-suffix": "part", "partial-suffix": "partial", "tmp-suffix": "tmp", "temp-suffix": "temp",
    "download-suffix": "download", "crdownload-suffix": "crdownload", "incomplete-suffix": "incomplete",
    "filepart-suffix": "filepart", "hidden-metadata": "hidden", "symlink-entry": "symlink-entry",
    "outside-backup-root": "outside", "special-file": "special", "unreadable-file": "unreadable",
    "file-command-error": "file-command", "mime-mismatch": "text", "safe-filenames": "safe",
    "mtime-at-sample-2": "mtime", "bytes-at-sample-2": "bytes", "wrong-group": "wrong-group",
    "cross-entry": "cross", "legacy-record": "legacy", "duplicate-registry": "duplicate",
    "invalid-config": "invalid-config", "authority-mismatch": "authority",
    "artifact-readback-failure": "artifact", "truncated-png": "truncated-png",
    "jpeg-missing-eoi": "jpeg-missing-eoi", "unsupported-image-type": "unsupported-image-type",
    "read-error-sample-2": "read-error-2", "dangling-verified-run-id": "dangling",
    "safe-abort-linked": "safe-abort", "nonterminal-linked": "nonterminal",
    "wrong-group-link": "wrong-group-link", "forged-binding": "forged-binding",
    "binding-artifact-deleted": "binding-deleted", "binding-artifact-mutated": "binding-mutated",
    "fixture-binding-in-production": "fixture-in-production",
}

SUFFIX_KINDS = {"part", "partial", "tmp", "temp", "download", "crdownload", "incomplete", "filepart"}
BARRIER_KINDS = {"mtime", "bytes", "read-error-2"}
NO_SAMPLING_KINDS = {"invalid-config", "authority", "outside"}
FAIL4 = ("FAIL", "NOT_RUN", "NOT_RUN", "NOT_RUN", "NOT_ACHIEVED", 4, "INPUT_NEGATIVE")
LINK_FAIL4 = ("PASS", "FAIL", "UNRESOLVED", "EXACT", "NOT_ACHIEVED", 4, "INPUT_NEGATIVE")
PROVENANCE4 = ("PASS", "PASS", "UNRESOLVED", "EXACT", "NOT_ACHIEVED", 4, "INPUT_PROVENANCE_LIMITED")
GIF_BYTES = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
             b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


def _ax(filesystem, registry, source, state, overall, exit_code, failure, readback="PASS"):
    return {"filesystem_status": filesystem, "registry_status": registry, "source_status": source,
            "state_status": state, "overall_status": overall, "exit_code": exit_code,
            "failure_class": failure, "artifact_readback": readback}


EXPECTED_BY_KIND = {
    "valid": _ax("PASS", "PASS", "CONFIRMED", "EXACT", "PASS", 0, "NONE"),
    "safe": _ax("PASS", "PASS", "CONFIRMED", "EXACT", "PASS", 0, "NONE"),
    "56": _ax(*FAIL4), "58": _ax(*FAIL4),
    **{kind: _ax(*FAIL4) for kind in SUFFIX_KINDS},
    "hidden": _ax(*FAIL4), "symlink-entry": _ax(*FAIL4), "outside": _ax(*FAIL4),
    "special": _ax(*FAIL4), "text": _ax(*FAIL4),
    "unreadable": _ax("FAIL", "NOT_RUN", "NOT_RUN", "UNKNOWN", "UNKNOWN", 1, "INTERNAL_READ_ERROR"),
    "file-command": _ax("FAIL", "NOT_RUN", "NOT_RUN", "UNKNOWN", "UNKNOWN", 1, "INTERNAL_COMMAND_ERROR"),
    "mtime": _ax(*FAIL4), "bytes": _ax(*FAIL4),
    "wrong-group": _ax("PASS", "FAIL", "CONTRADICTED", "EXACT", "NOT_ACHIEVED", 4, "INPUT_NEGATIVE"),
    "cross": _ax("PASS", "FAIL", "UNRESOLVED", "STATE_CONTRADICTED", "NOT_ACHIEVED", 4, "INPUT_NEGATIVE"),
    "legacy": _ax("PASS", "PASS", "UNRESOLVED", "LEGACY_PROVENANCE_LIMITED", "UNKNOWN", 4,
                  "INPUT_PROVENANCE_LIMITED"),
    "duplicate": _ax("PASS", "FAIL", "UNRESOLVED", "AMBIGUOUS", "NOT_ACHIEVED", 4, "INPUT_NEGATIVE"),
    "invalid-config": _ax("NOT_RUN", "NOT_RUN", "NOT_RUN", "NOT_RUN", "UNKNOWN", 2, "INVALID_CONFIGURATION"),
    "authority": _ax("NOT_RUN", "NOT_RUN", "NOT_RUN", "NOT_RUN", "UNKNOWN", 2, "INVALID_AUTHORITY",
                     readback="PASS_WITH_NO_STATE_WRITE"),
    "artifact": _ax("PASS", "NOT_RUN", "NOT_RUN", "UNKNOWN", "UNKNOWN", 1, "INTERNAL_ARTIFACT_ERROR",
                    readback="FAIL_WITH_ERROR_ARTIFACT"),
    "truncated-png": _ax(*FAIL4), "jpeg-missing-eoi": _ax(*FAIL4),
    "unsupported-image-type": _ax("FAIL", "NOT_RUN", "NOT_RUN", "NOT_RUN", "NOT_ACHIEVED", 4,
                                  "UNSUPPORTED_IMAGE_TYPE"),
    "read-error-2": _ax("FAIL", "NOT_RUN", "NOT_RUN", "UNKNOWN", "UNKNOWN", 1, "INTERNAL_READ_ERROR"),
    "dangling": _ax(*LINK_FAIL4), "safe-abort": _ax(*LINK_FAIL4), "nonterminal": _ax(*LINK_FAIL4),
    "wrong-group-link": _ax("PASS", "FAIL", "CONTRADICTED", "STATE_CONTRADICTED", "NOT_ACHIEVED", 4,
                            "INPUT_NEGATIVE"),
    "forged-binding": _ax(*PROVENANCE4), "binding-deleted": _ax(*PROVENANCE4),
    "binding-mutated": _ax(*PROVENANCE4), "fixture-in-production": _ax(*PROVENANCE4),
}


# ---------------------------------------------------------------------------
# Literal row paths and argv (the manifest is generated from these functions)
# ---------------------------------------------------------------------------

def row_paths(case_id: str) -> dict:
    kind = CASE_BY_ID[case_id]
    if kind == "authority":
        base = ROOT / "authority"
        return {"owner_root": base, "project_root": base / "root-a",
                "config": base / "root-b" / "config" / "line_backup_config.json",
                "state": base / "root-b" / "state" / "backup_state.json",
                "run_log": base / "root-b" / "state" / "run_log.md",
                "destination": base / "root-a" / "backup" / "destination",
                "evidence_dir": base / "root-a" / "evidence",
                "records": base / "root-a" / "records"}
    if kind == "fixture-in-production":
        root = PRODUCTION_ROOT / "fixture-binding"
    else:
        root = ROOT / (case_id if case_id in {
            "truncated-png", "jpeg-missing-eoi", "unsupported-image-type", "read-error-sample-2",
            "dangling-verified-run-id", "safe-abort-linked", "nonterminal-linked", "wrong-group-link",
            "forged-binding", "binding-artifact-deleted", "binding-artifact-mutated"} else {
            "valid-57": "valid", "count-56": "56", "count-58": "58", "part-suffix": "part",
            "partial-suffix": "partial", "tmp-suffix": "tmp", "temp-suffix": "temp",
            "download-suffix": "download", "crdownload-suffix": "crdownload",
            "incomplete-suffix": "incomplete", "filepart-suffix": "filepart",
            "hidden-metadata": "hidden", "symlink-entry": "symlink-entry",
            "outside-backup-root": "outside", "special-file": "special", "unreadable-file": "unreadable",
            "file-command-error": "file-command", "mime-mismatch": "text", "safe-filenames": "safe",
            "mtime-at-sample-2": "mtime", "bytes-at-sample-2": "bytes", "wrong-group": "wrong-group",
            "cross-entry": "cross", "legacy-record": "legacy", "duplicate-registry": "duplicate",
            "invalid-config": "invalid-config", "artifact-readback-failure": "artifact"}[case_id])
    destination = root / ("outside-destination" if kind == "outside" else "backup/destination")
    return {"owner_root": root, "project_root": root,
            "config": root / "config" / "line_backup_config.json",
            "state": root / "state" / "backup_state.json",
            "run_log": root / "state" / "run_log.md",
            "destination": destination,
            "evidence_dir": root / "evidence",
            "records": root / "records"}


def build_argv(case_id: str, p: dict) -> list:
    kind = CASE_BY_ID[case_id]
    argv = list(BASE_ARGV) + [
        "--project-root", str(p["project_root"]), "--config", str(p["config"]),
        "--state", str(p["state"]), "--destination", str(p["destination"]),
        "--group-key", GROUP, "--start-date", START_DATE, "--end-date", END_DATE,
        "--expected-images", str(EXPECTED_IMAGES), "--evidence-dir", str(p["evidence_dir"]),
    ]
    if kind in BARRIER_KINDS:
        argv += ["--test-mode", "--pause-at", "SAMPLE_2_READY", "--barrier-file",
                 str(ROOT / f"{case_id}.barrier")]
    elif kind not in {"authority", "fixture-in-production"}:
        argv += ["--test-mode"]
    return argv


def manifest_row(case_id: str) -> dict:
    p = row_paths(case_id)
    evidence = p["evidence_dir"]
    return {
        "id": case_id, "case": CASE_BY_ID[case_id],
        "project_root": str(p["project_root"]), "config": str(p["config"]), "state": str(p["state"]),
        "run_log": str(p["run_log"]), "destination": str(p["destination"]),
        "evidence_dir": str(evidence),
        "fixture-precondition": str(p["records"] / "fixture-precondition.json"),
        "stdout": str(p["records"] / "stdout.log"), "stderr": str(p["records"] / "stderr.log"),
        "exit_code": str(p["records"] / "exit-code"),
        "result": str(evidence / "result.json"), "manifest": str(evidence / "manifest.json"),
        "inventory-1": str(evidence / "inventory-1.json"),
        "inventory-2": str(evidence / "inventory-2.json"),
        "inventory-3": str(evidence / "inventory-3.json"),
        "argv": build_argv(case_id, p),
        "expected": expected_for(CASE_BY_ID[case_id]),
    }


def expected_for(kind: str) -> dict:
    return dict(EXPECTED_BY_KIND[kind])


def emit_manifest(path: Path) -> None:
    manifest = {"schema_version": 1, "root": str(ROOT),
                "cases": [manifest_row(case_id) for case_id in ORDERED_IDS]}
    write_json(Path(path), manifest)


# ---------------------------------------------------------------------------
# Small independent helpers (never import product code)
# ---------------------------------------------------------------------------

def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha_meta(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    data = path.read_bytes()
    return {"path": str(path), "exists": True, "bytes": len(data), "sha256": H.sha256_bytes(data)}


def tree_digest(root: Path) -> dict:
    root = Path(root)
    entries = []
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                entries.append({"path": str(path.relative_to(root)), "bytes": len(data),
                                "sha256": H.sha256_bytes(data)})
    listing = json.dumps(entries, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {"root": str(root), "files": len(entries), "listing_sha256": H.sha256_bytes(listing),
            "entries": entries}


def chain_ok(evidence: Path) -> tuple:
    """Independent read-back of the product's chain-v2 evidence directory."""
    evidence = Path(evidence)
    result_path = evidence / "result.json"
    manifest_path = evidence / "manifest.json"
    detail = {"result_exists": result_path.is_file(), "manifest_exists": manifest_path.is_file()}
    if not (result_path.is_file() and manifest_path.is_file()):
        return False, detail
    result_data = result_path.read_bytes()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result = json.loads(result_data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False, detail
    ok = isinstance(manifest, dict) and isinstance(result, dict)
    fields = ("schema_version", "mode", "run_id", "group_key", "fingerprint", "destination",
              "filesystem_status", "recognized_images", "expected_images", "overall_status",
              "exit_code", "artifact_readback")
    if ok:
        ok = (len(result_data) == manifest.get("result_bytes")
              and H.sha256_bytes(result_data) == manifest.get("result_sha256")
              and manifest.get("result_summary") == {field: result.get(field) for field in fields})
    names = set()
    for item in manifest.get("artifacts") or []:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            ok = False
            continue
        name = item["path"]
        if "/" in name or name in names:
            ok = False
            continue
        names.add(name)
        target = evidence / name
        if not target.is_file():
            ok = False
            continue
        data = target.read_bytes()
        if len(data) != item["bytes"] or H.sha256_bytes(data) != item["sha256"]:
            ok = False
    ok = bool(ok and "result.json" in names and "manifest.json" not in names)
    for path in sorted(evidence.iterdir()):
        if path.is_file() and path.name not in names and path.name != "manifest.json":
            ok = False
    detail.update({"artifacts": sorted(names), "ok": bool(ok)})
    return bool(ok), detail


def artifact_hashes(evidence: Path, names) -> dict:
    out = {}
    for name in names:
        path = Path(evidence) / name
        out[name] = sha_meta(path)
    return out


def read_inventory(evidence: Path, index: int):
    path = Path(evidence) / f"inventory-{index}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def entry_for(inventory: dict, relative_path: str):
    if not isinstance(inventory, dict):
        return None
    for entry in inventory.get("entries") or []:
        if entry.get("relative_path") == relative_path:
            return entry
    return None


# ---------------------------------------------------------------------------
# Fixture preconditions (inputs only; never product outputs)
# ---------------------------------------------------------------------------

def reset_case_root(root: Path) -> dict:
    root = Path(root)
    owned = H.ensure_owned_root(root, DRIVER_ID)
    H.reset_owned_content(root)
    return owned


def config_for(backup_root: Path) -> dict:
    return {"schema_version": 2, "group_key": GROUP, "group_name": F.GROUP_NAME,
            "backup_root": str(backup_root), "app_identifier": "jp.naver.line.mac",
            "max_albums_per_run": 50, "recovery_limit": 1, "poll_interval_seconds": 5,
            "stable_samples": 3, "max_wait_seconds": 60}


def plain_state(destination: Path) -> dict:
    return F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination))


def safe_abort_run(destination: Path) -> dict:
    run = F.make_run("RUN-ABORT", "WRITER-FIXTURE", str(destination),
                     intent_state="ABORTED_BEFORE_SAVE_ALL_DISPATCH", workflow_outcome="SAFE_ABORT",
                     phase="SAFE_ABORT", trigger_outcome="NOT_TRIGGERED", dispatch_outcome="NOT_ATTEMPTED",
                     dispatch_state="NOT_ATTEMPTED", dispatch_evidence=None)
    run["reconciliations"] = [F.reconciliation_entry(run, released=True)]
    return run


def build_fixture(case_id: str, row: dict) -> dict:
    kind = row["case"]
    p = row_paths(case_id)
    for key in ("project_root", "config", "state", "run_log", "destination", "evidence_dir"):
        if str(p[key]) != row[key]:
            raise RuntimeError(f"{case_id}: literal {key} drifted from the driver's own path table")
    owner_root = p["owner_root"]
    reset_case_root(owner_root)
    records = p["records"]
    records.mkdir(parents=True, exist_ok=True)
    evidence = p["evidence_dir"]
    destination = p["destination"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    config_path, state_path, run_log = p["config"], p["state"], p["run_log"]
    precondition = ""
    binding = {"path": None, "reference": None, "mutated": False, "deleted": False}

    if kind == "outside":
        (owner_root / "backups").mkdir(parents=True, exist_ok=True)
        backup_root = owner_root / "backups"
    else:
        backup_root = destination.parent

    if kind == "authority":
        alternate = owner_root / "root-b"
        (owner_root / "config").mkdir(parents=True, exist_ok=True)
        (owner_root / "state").mkdir(parents=True, exist_ok=True)
        (alternate / "config").mkdir(parents=True, exist_ok=True)
        (alternate / "state").mkdir(parents=True, exist_ok=True)
        for index in range(EXPECTED_IMAGES):
            F.make_png(destination / f"image-{index:03d}.png")
        write_json(owner_root / "config" / "line_backup_config.json", config_for(backup_root))
        write_json(owner_root / "state" / "backup_state.json", plain_state(destination))
        (owner_root / "state" / "run_log.md").write_text("fixture run log\n", encoding="utf-8")
        write_json(alternate / "config" / "line_backup_config.json", config_for(backup_root))
        write_json(alternate / "state" / "backup_state.json", plain_state(destination))
        (alternate / "state" / "run_log.md").write_text("alternate run log\n", encoding="utf-8")
        precondition = ("root-a is the authoritative --project-root while --config/--state point at root-b; "
                        "the command must fail INVALID_AUTHORITY before any authority read/write")
        return {"case_id": case_id, "kind": kind, "paths": p, "destination": destination, "records": records,
                "evidence": evidence, "precondition": precondition, "binding": binding,
                "authority_paths": [config_path, state_path, run_log,
                                    owner_root / "config" / "line_backup_config.json",
                                    owner_root / "state" / "backup_state.json",
                                    owner_root / "state" / "run_log.md"],
                "authority_tree": owner_root / "root-b",
                "mutation_target": None}

    count = 56 if kind == "56" else 58 if kind == "58" else EXPECTED_IMAGES
    for index in range(count):
        F.make_png(destination / f"image-{index:03d}.png")

    if kind in SUFFIX_KINDS:
        (destination / "image-000.png").rename(destination / f"image-000.png.{kind}")
    elif kind == "hidden":
        (destination / ".DS_Store").write_bytes(b"metadata")
        (destination / "._hidden").write_bytes(b"metadata")
        (destination / "__MACOSX").mkdir()
    elif kind == "symlink-entry":
        (destination / "linked.png").symlink_to(destination / "image-000.png")
    elif kind == "special":
        os.mkfifo(destination / "special.fifo")
    elif kind == "safe":
        (destination / "image-000.png").rename(destination / "空 格|pipe\nname.jpg")
    elif kind == "text":
        (destination / "image-000.png").write_bytes(b"not an image")
    elif kind == "truncated-png":
        F.make_png(destination / "image-000.png", iend=False)
    elif kind == "jpeg-missing-eoi":
        (destination / "image-000.png").unlink()
        F.make_jpeg(destination / "image-000.jpg", eoi=False)
    elif kind == "unsupported-image-type":
        (destination / "image-000.png").unlink()
        (destination / "image-000.gif").write_bytes(GIF_BYTES)

    state = None
    if kind in {"valid", "safe", "duplicate", "dangling", "artifact"}:
        binding["path"] = str(F.write_binding_fixture(owner_root))
        state = F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                                 binding_path=binding["path"])
        binding["reference"] = state["verified_albums"][0]["evidence"]
        if kind == "duplicate":
            state["verified_albums"].append(dict(state["verified_albums"][0]))
        if kind == "dangling":
            state["verified_albums"][0]["verified_run_id"] = "RUN-DANGLING-MISSING"
    elif kind == "fixture-in-production":
        binding["path"] = str(F.write_binding_fixture(owner_root))
        state = F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                                 binding_path=binding["path"])
        binding["reference"] = state["verified_albums"][0]["evidence"]
        precondition = "a valid fixture: binding presented to production verify-only (no --test-mode)"
    elif kind == "forged-binding":
        (owner_root / "evidence").mkdir(parents=True, exist_ok=True)
        forged = F.write_binding_fixture(owner_root / "evidence", name="forged-binding.json")
        reference = f"fixture:evidence/forged-binding.json:{H.sha256_file(forged)}"
        state = F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                                 evidence_reference=reference)
        binding["path"] = str(forged)
        binding["reference"] = reference
        precondition = "the binding artifact sits inside the operation's own --evidence-dir (product-authored)"
    elif kind in {"binding-deleted", "binding-mutated"}:
        artifact = F.write_binding_fixture(owner_root)
        reference = f"fixture:binding-fixture.json:{H.sha256_file(artifact)}"
        state = F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                                 evidence_reference=reference)
        binding["path"] = str(artifact)
        binding["reference"] = reference
        if kind == "binding-deleted":
            artifact.unlink()
            binding["deleted"] = True
            precondition = "the external binding artifact was deleted after a valid finalize shape"
        else:
            data = artifact.read_bytes()
            artifact.write_bytes(data[:-1] + bytes([data[-1] ^ 0x01]))
            binding["mutated"] = True
            precondition = "the external binding artifact was mutated by one byte after a valid finalize shape"
    elif kind == "wrong-group":
        binding["path"] = str(F.write_binding_fixture(owner_root))
        state = F.verified_state("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                                 binding_path=binding["path"])
        state["verified_albums"][0]["group_key"] = OTHER_GROUP
        binding["reference"] = state["verified_albums"][0]["evidence"]
        precondition = "the exact run exists but the registry entry belongs to a different group key"
    elif kind == "cross":
        run = F.make_run("RUN-FIXTURE", "WRITER-FIXTURE", str(destination),
                         intent_state="SAVE_ALL_DISPATCH_ATTEMPTED", dispatch_state="SAVE_ALL_RETURNED",
                         trigger_outcome="UNKNOWN", dispatch_outcome="RETURNED", workflow_outcome="VERIFIED",
                         phase="VERIFIED", dispatch_evidence=F.dispatch_proof("RUN-FIXTURE", "WRITER-FIXTURE"))
        state = F.fresh_state(revision=7)
        state["runs"] = [run]
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": dict(F.FP57),
                                     "verified_run_id": "RUN-OTHER",
                                     "destinations": [str(destination.parent / "different-destination")],
                                     "source_kind": "filesystem_verification"}]
        precondition = "the registry entry mixes a different run id and a different destination"
    elif kind == "legacy":
        run = F.make_run("RUN-LEGACY", "WRITER-FIXTURE", str(destination), contract_revision=None,
                         intent_state="COMMITTED_NOT_DISPATCHED", workflow_outcome="VERIFIED", phase="VERIFIED")
        state = F.fresh_state(revision=3)
        state["runs"] = [run]
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": dict(F.FP57),
                                     "verified_run_id": None, "destinations": [str(destination)],
                                     "source_kind": "filesystem_verification"}]
        precondition = "a pre-RC2 run without contract_revision and a null verified_run_id entry"
    elif kind == "safe-abort":
        run = safe_abort_run(destination)
        state = F.fresh_state(revision=2)
        state["runs"] = [run]
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": dict(F.FP57),
                                     "verified_run_id": "RUN-ABORT", "destinations": [str(destination)],
                                     "source_kind": "filesystem_verification"}]
        precondition = "the entry links to a terminal SAFE_ABORT run"
    elif kind == "nonterminal":
        run = F.completed_dispatch_run("RUN-INT", "WRITER-FIXTURE", str(destination))
        state = F.fresh_state(revision=2)
        state["runs"] = [run]
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": dict(F.FP57),
                                     "verified_run_id": "RUN-INT", "destinations": [str(destination)],
                                     "source_kind": "filesystem_verification"}]
        precondition = "the entry links to a non-terminal (IN_PROGRESS) run"
    elif kind == "wrong-group-link":
        run = F.make_run("RUN-OTHER-GROUP", "WRITER-FIXTURE", str(destination), group=OTHER_GROUP,
                         intent_state="SAVE_ALL_DISPATCH_ATTEMPTED", dispatch_state="SAVE_ALL_RETURNED",
                         trigger_outcome="UNKNOWN", dispatch_outcome="RETURNED", workflow_outcome="VERIFIED",
                         phase="VERIFIED",
                         dispatch_evidence=F.dispatch_proof("RUN-OTHER-GROUP", "WRITER-FIXTURE"))
        state = F.fresh_state(revision=2)
        state["runs"] = [run]
        state["verified_albums"] = [{"group_key": GROUP, "fingerprint": dict(F.FP57),
                                     "verified_run_id": "RUN-OTHER-GROUP",
                                     "destinations": [str(destination)], "source_kind": "filesystem_verification"}]
        precondition = "the linked run's group_key differs from the entry/request group"
    else:  # plain-state kinds (including invalid-config)
        state = plain_state(destination)

    if state is None:
        state = plain_state(destination)

    cfg = config_for(backup_root)
    if kind == "invalid-config":
        del cfg["stable_samples"]
    write_json(config_path, cfg)
    write_json(state_path, state)
    run_log.write_text("fixture run log\n", encoding="utf-8")
    if kind in BARRIER_KINDS:
        barrier = ROOT / f"{case_id}.barrier"
        for suffix in ("", ".ready"):
            try:
                Path(str(barrier) + suffix).unlink()
            except FileNotFoundError:
                pass
    precondition = precondition or f"canonical fixture precondition for {kind}"
    mutation = None
    if kind in BARRIER_KINDS:
        mutation = {"kind": "mtime" if kind == "mtime" else "bytes" if kind == "bytes" else "read-error",
                    "target": str(destination / "image-001.png")}
    return {"case_id": case_id, "kind": kind, "paths": p, "destination": destination, "records": records,
            "evidence": evidence, "precondition": precondition, "binding": binding,
            "authority_paths": [config_path, state_path, run_log],
            "authority_tree": None, "mutation_target": mutation}


def product_env(kind: str) -> dict:
    env = {"LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0",
           "PYTHONPATH": str(REPO / "src")}
    if kind == "unreadable":
        env["LINE_BACKUP_UNREADABLE_FILE"] = "1"
    if kind == "file-command":
        env["LINE_BACKUP_FILE_COMMAND_ERROR"] = "1"
    if kind == "artifact":
        env["LINE_BACKUP_ARTIFACT_READBACK_FAILURE"] = "1"
    return env


def run_product(ctx: dict, row: dict) -> dict:
    kind = ctx["kind"]
    argv = list(row["argv"])
    if argv != build_argv(ctx["case_id"], ctx["paths"]):
        raise RuntimeError(f"{ctx['case_id']}: manifest argv is not the literal driver argv")
    env = product_env(kind)
    barrier_info = {"saw_ready": None}
    if kind in BARRIER_KINDS:
        barrier = Path(argv[argv.index("--barrier-file") + 1])
        ready = Path(str(barrier) + ".ready")
        process = subprocess.Popen(argv, cwd=REPO, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 10
        while not ready.exists() and time.time() < deadline:
            time.sleep(0.01)
        barrier_info["saw_ready"] = ready.exists()
        target = Path(ctx["mutation_target"]["target"])
        try:
            if kind == "mtime":
                os.utime(target, ns=(time.time_ns(), time.time_ns() + 1_000_000_000))
            elif kind == "bytes":
                target.write_bytes(target.read_bytes() + b"changed")
            else:
                os.chmod(target, 0o000)
            barrier.touch()
            stdout, stderr = process.communicate(timeout=60)
            exit_code = process.returncode
        finally:
            if kind == "read-error-2":
                os.chmod(target, 0o644)
        process_result = subprocess.CompletedProcess(argv, exit_code, stdout, stderr)
    else:
        process_result = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, check=False)
    record_dir = ctx["records"]
    write_json(record_dir / "argv.json", argv)
    (record_dir / "stdout.log").write_text(process_result.stdout or "", encoding="utf-8")
    (record_dir / "stderr.log").write_text(process_result.stderr or "", encoding="utf-8")
    (record_dir / "exit-code").write_text(str(process_result.returncode) + "\n", encoding="utf-8")
    return {"stdout": process_result.stdout or "", "stderr": process_result.stderr or "",
            "exit_code": process_result.returncode, "barrier": barrier_info}


# ---------------------------------------------------------------------------
# Independent oracle
# ---------------------------------------------------------------------------

def oracle_checks(ctx: dict, run: dict, product: dict, pre: dict, post: dict, chain: dict) -> dict:
    kind = ctx["kind"]
    evidence = ctx["evidence"]
    destination = ctx["destination"]
    checks = {}

    def add(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}

    add("chain_manifest_readback", chain.get("ok"), chain)
    add("state_unchanged", pre["state"] == post["state"], {"before": pre["state"], "after": post["state"]})
    add("config_unchanged", pre["config"] == post["config"], None)
    add("run_log_unchanged", pre["run_log"] == post["run_log"], None)
    add("product_result_parsed", isinstance(product, dict) and "overall_status" in product, None)

    inv1, inv2, inv3 = (read_inventory(evidence, i) for i in (1, 2, 3))
    sampling = kind not in NO_SAMPLING_KINDS
    add("sampling_expectation", (inv1 is not None) == sampling, {"expect_sampling": sampling})

    if kind in {"valid", "safe"}:
        add("count_57_recognized", (inv3 or {}).get("recognized_images") == 57, None)
        add("all_entries_ok", bool(inv3) and all(e.get("status") == "OK" for e in inv3["entries"]), None)
    if kind in {"56", "58"}:
        add("regular_file_count", (inv1 or {}).get("regular_files") == (56 if kind == "56" else 58), None)
    if kind in SUFFIX_KINDS:
        add("suffix_entry", (entry_for(inv1, f"image-000.png.{kind}") or {}).get("status") == "SUFFIX", None)
    if kind == "hidden":
        add("hidden_entries", all((entry_for(inv1, name) or {}).get("status") == "HIDDEN"
                                  for name in (".DS_Store", "._hidden")), None)
    if kind == "symlink-entry":
        add("symlink_entry", (entry_for(inv1, "linked.png") or {}).get("type") == "symlink", None)
    if kind == "special":
        add("special_entry", (entry_for(inv1, "special.fifo") or {}).get("type") == "special", None)
    if kind == "text":
        add("unrecognized_entry", (entry_for(inv1, "image-000.png") or {}).get("status") == "UNRECOGNIZED", None)
    if kind == "truncated-png":
        entry = entry_for(inv3, "image-000.png") or {}
        add("decode_error_png", entry.get("status") == "DECODE_ERROR" and entry.get("mime") == "image/png", None)
    if kind == "jpeg-missing-eoi":
        entry = entry_for(inv3, "image-000.jpg") or {}
        add("decode_error_jpeg", entry.get("status") == "DECODE_ERROR" and entry.get("mime") == "image/jpeg", None)
    if kind == "unsupported-image-type":
        add("unsupported_entry", (entry_for(inv3, "image-000.gif") or {}).get("status") == "UNSUPPORTED", None)
    if kind == "mtime":
        rows = [entry_for(inv, "image-001.png") or {} for inv in (inv1, inv2, inv3)]
        add("barrier_seen", run["barrier"].get("saw_ready") is True, None)
        add("mtime_changed_after_barrier",
            all(row.get("mtime_ns") for row in rows) and rows[0].get("mtime_ns") != rows[1].get("mtime_ns")
            and rows[1].get("mtime_ns") == rows[2].get("mtime_ns"), None)
        add("content_unchanged", len({(row.get("sha256"), row.get("size")) for row in rows}) == 1, None)
    if kind == "bytes":
        rows = [entry_for(inv, "image-001.png") or {} for inv in (inv1, inv2, inv3)]
        add("barrier_seen", run["barrier"].get("saw_ready") is True, None)
        add("bytes_changed_after_barrier",
            all(row.get("sha256") for row in rows) and rows[0].get("sha256") != rows[1].get("sha256")
            and rows[1].get("sha256") == rows[2].get("sha256"), None)
    if kind == "read-error-2":
        rows = [entry_for(inv, "image-001.png") or {} for inv in (inv1, inv2, inv3)]
        add("barrier_seen", run["barrier"].get("saw_ready") is True, None)
        add("sample0_clean", rows[0].get("status") == "OK", None)
        add("samples12_read_error",
            all(row.get("status") == "READ_ERROR"
                and row.get("error_code") == "INTERNAL_READ_ERROR" for row in rows[1:]), None)
    if kind == "unreadable":
        add("read_error_entries", bool(inv1) and all(e.get("status") == "READ_ERROR" for e in inv1["entries"]), None)
    if kind == "file-command":
        add("command_error_entries",
            bool(inv1) and all(e.get("error_code") == "INTERNAL_COMMAND_ERROR" for e in inv1["entries"]), None)
    if kind in {"wrong-group", "cross", "legacy", "duplicate", "dangling", "safe-abort", "nonterminal",
                "wrong-group-link", "forged-binding", "binding-deleted", "binding-mutated",
                "fixture-in-production", "artifact"}:
        add("count_57_recognized", (inv3 or {}).get("recognized_images") == 57, None)
    if kind == "artifact":
        add("error_artifact_present", (evidence / "error.json").is_file(), None)
    if kind == "authority":
        add("authority_tree_unchanged", pre.get("authority_tree") == post.get("authority_tree"), None)
        add("authority_files_unchanged", pre.get("authority_files") == post.get("authority_files"), None)
        add("no_inventory", inv1 is None, None)
    destination_now = post["destination"]
    if kind == "bytes":
        add("destination_changed_only_by_mutation", destination_now != pre["destination"], None)
    else:
        add("destination_unchanged", destination_now == pre["destination"], None)
    if ctx["binding"]["path"] is not None:
        add("binding_state_recorded", pre["binding"] is not None, None)
    if ctx["binding"]["deleted"]:
        reference_sha = str(ctx["binding"]["reference"] or "").rsplit(":", 1)[-1]
        add("binding_deleted_with_recorded_reference",
            not Path(ctx["binding"]["path"]).exists() and len(reference_sha) == 64,
            {"reference_sha256": reference_sha})
    if ctx["binding"]["mutated"]:
        reference_sha = str(ctx["binding"]["reference"] or "").rsplit(":", 1)[-1]
        target = Path(ctx["binding"]["path"])
        current = H.sha256_file(target) if target.is_file() else None
        add("binding_hash_differs_from_recorded_reference",
            current is not None and current != reference_sha,
            {"current_sha256": current, "reference_sha256": reference_sha})
    return checks


# ---------------------------------------------------------------------------
# Case runner
# ---------------------------------------------------------------------------

def run_case(case_id: str, row: dict) -> dict:
    ctx = build_fixture(case_id, row)
    evidence = ctx["evidence"]
    p = ctx["paths"]
    pre = {"state": sha_meta(p["state"]), "config": sha_meta(p["config"]), "run_log": sha_meta(p["run_log"]),
           "destination": tree_digest(ctx["destination"]),
           "binding": sha_meta(ctx["binding"]["path"]) if ctx["binding"]["path"] else None,
           "binding_sha256": H.sha256_file(Path(ctx["binding"]["path"]))
           if ctx["binding"]["path"] and Path(ctx["binding"]["path"]).is_file() else None,
           "authority_tree": tree_digest(ctx["authority_tree"]) if ctx.get("authority_tree") else None,
           "authority_files": [sha_meta(path) for path in ctx.get("authority_paths") or []]}
    precondition_file = Path(row["fixture-precondition"])
    write_json(precondition_file, {"case_id": case_id, "case": ctx["kind"],
                                   "precondition": ctx["precondition"], "argv": row["argv"],
                                   "pre_state": pre, "binding": ctx["binding"],
                                   "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    run = run_product(ctx, row)
    post = {"state": sha_meta(p["state"]), "config": sha_meta(p["config"]), "run_log": sha_meta(p["run_log"]),
            "destination": tree_digest(ctx["destination"]),
            "binding": sha_meta(ctx["binding"]["path"]) if ctx["binding"]["path"] else None,
            "binding_sha256": H.sha256_file(Path(ctx["binding"]["path"]))
            if ctx["binding"]["path"] and Path(ctx["binding"]["path"]).is_file() else None,
            "authority_tree": tree_digest(ctx["authority_tree"]) if ctx.get("authority_tree") else None,
            "authority_files": [sha_meta(path) for path in ctx.get("authority_paths") or []]}
    chain, chain_detail = chain_ok(evidence)
    try:
        product = json.loads((run["stdout"] or "").strip().splitlines()[-1])
    except (IndexError, ValueError, json.JSONDecodeError):
        product = {"parse_error": True}
    expected = expected_for(ctx["kind"])
    if row["expected"] != expected:
        raise RuntimeError(f"{case_id}: manifest expectation is not the approved row expectation")
    observed = {key: product.get(key) for key in expected}
    checks = oracle_checks(ctx, run, product, pre, post, chain_detail)
    ok = (run["exit_code"] == expected["exit_code"] and observed == expected and chain
          and all(item["ok"] for item in checks.values()))
    record = {"id": case_id, "case": ctx["kind"], "argv": row["argv"], "exit_code": run["exit_code"],
              "expected": expected, "observed": observed, "match": bool(ok), "checks": checks,
              "chain": chain_detail, "pre_state": pre, "post_state": post,
              "artifacts": artifact_hashes(evidence, ("result.json", "manifest.json", "inventory-1.json",
                                                      "inventory-2.json", "inventory-3.json", "error.json")),
              "records_dir": str(ctx["records"]), "evidence_dir": str(evidence),
              "literal_manifest_row": row}
    write_json(ctx["records"] / "independent-oracle.json", record)
    (ctx["records"] / "stdout.log").write_text(run["stdout"], encoding="utf-8")
    (ctx["records"] / "stderr.log").write_text(run["stderr"], encoding="utf-8")
    (ctx["records"] / "exit-code").write_text(str(run["exit_code"]) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--evidence-dir")
    parser.add_argument("--summary")
    parser.add_argument("--emit-manifest")
    parser.add_argument("--clean-owned", action="store_true")
    args = parser.parse_args()

    if args.emit_manifest:
        emit_manifest(Path(args.emit_manifest))
        print(json.dumps({"emitted": args.emit_manifest, "rows": len(ORDERED_IDS)}, sort_keys=True))
        return 0
    if not args.manifest or not args.evidence_dir or not args.summary:
        parser.error("--manifest, --evidence-dir and --summary are required unless --emit-manifest is used")
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("cases")
    if not isinstance(rows, list) or [row.get("id") for row in rows] != ORDERED_IDS:
        raise SystemExit("manifest IDs do not match the approved 40-row matrix (order included)")
    if any(not isinstance(row.get("expected"), dict) or not isinstance(row.get("argv"), list)
           or not row.get("argv") for row in rows):
        raise SystemExit("every manifest row must carry its literal argv and an independent expected oracle")

    driver_evidence = Path(args.evidence_dir)
    driver_evidence.mkdir(parents=True, exist_ok=True)
    results = []
    for index, row in enumerate(rows, 1):
        case_id = row["id"]
        try:
            record = run_case(case_id, row)
        except Exception as exc:  # keep the wave moving; the row is a hard failure
            record = {"id": case_id, "case": row.get("case"), "match": False, "error": f"{type(exc).__name__}: {exc}"}
        results.append(record)
        write_json(driver_evidence / "rows" / f"{case_id}.json", record)
        print(f"# [{index}/{len(rows)}] {case_id}: match={record.get('match')}"
              + ("" if record.get("match") else f" error={record.get('error', '')}"))

    cleanup = None
    if args.clean_owned:
        cleanup = {}
        for case_id in ORDERED_IDS:
            owner_root = row_paths(case_id)["owner_root"]
            cleanup[case_id] = H.clean_owned_root(owner_root, DRIVER_ID)

    summary = {"schema_version": 1, "driver_id": DRIVER_ID, "task_id": H.TASK_ID,
               "manifest": str(manifest_path), "manifest_sha256": H.sha256_file(manifest_path),
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "program_hashes": H.program_hashes(), "cases": results,
               "all_match": all(record.get("match") for record in results), "cleanup": cleanup}
    write_json(Path(args.summary), summary)
    print(json.dumps({"summary": args.summary, "all_match": summary["all_match"],
                      "failed_cases": [r["id"] for r in results if not r.get("match")]},
                     ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
