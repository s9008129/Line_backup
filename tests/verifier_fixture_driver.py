#!/usr/bin/env python3
"""Subprocess acceptance driver for the real verify-only CLI.

The fixture builder supplies inputs only.  Expected axes are read from the
literal manifest supplied by the caller, while the product process performs
inventory, association, and artifact work.  The driver never treats a
product PASS line as its oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path("/private/tmp/line-backup-acceptance-verifier")
GROUP = "line:jp.naver.line.mac:旻謙允禎成長日記"
OTHER_GROUP = "line:jp.naver.line.mac:other-group"
START, END, COUNT = "2024-05-13", "2024-05-17", 57
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cfc000000301010018dd8db40000000049454e44ae426082"
)
SUFFIXES = ("part", "partial", "tmp", "temp", "download", "crdownload", "incomplete", "filepart")


def digest(path: Path) -> dict:
    if path.is_dir():
        entries = []
        for child in sorted(path.rglob("*")):
            if child.is_file():
                data = child.read_bytes()
                entries.append({"path": str(child.relative_to(path)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        data = json.dumps(entries, ensure_ascii=False, sort_keys=True).encode()
        return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "entries": entries}
    data = path.read_bytes() if path.exists() else b"<missing>"
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def config(backup_root: Path, group: str = GROUP) -> dict:
    return {
        "schema_version": 2, "group_key": group, "group_name": "fixture",
        "backup_root": str(backup_root), "app_identifier": "jp.naver.line.mac",
        "max_albums_per_run": 1, "recovery_limit": 1, "poll_interval_seconds": 5,
        "stable_samples": 3, "max_wait_seconds": 15,
    }


def run_record(group: str, destination: Path, *, legacy: bool = False) -> dict:
    fp = {"start_date": START, "end_date": END, "expected_images": COUNT}
    base = {
        "run_id": "RUN-FIXTURE", "group_key": group, "destination": str(destination),
        "fingerprint": fp, "workflow_outcome": "VERIFIED", "phase": "VERIFIED",
        "owner_id": None, "verification": {"filesystem_status": "PASS"},
        "events": [], "reconciliations": [],
    }
    if not legacy:
        base.update({"contract_revision": "1.0-rc2", "observed_title": "旻謙允禎成長日記",
                     "source_provenance": "fixture exact source", "intent_state": "INTENT_COMMITTED",
                     "dispatch_state": "SAVE_ALL_DISPATCH_ATTEMPTED",
                     "intent": {"intent_state": "SAVE_ALL_DISPATCH_ATTEMPTED", "dispatch_state": "SAVE_ALL_RETURNED",
                                "trigger_outcome": "UNKNOWN", "dispatch_outcome": "RETURNED",
                                "save_all_retry_allowed": False}})
    return base


def state_for(destination: Path, kind: str) -> dict:
    fp = {"start_date": START, "end_date": END, "expected_images": COUNT}
    run_group = GROUP
    entry_group = GROUP
    runs = []
    entries = []
    legacy = kind == "legacy"
    if kind == "wrong-group":
        # The exact run is present, but the registry entry belongs to a
        # different group.  The product must keep registry/source separate.
        entry_group = OTHER_GROUP
    if kind == "cross":
        runs = [run_record(GROUP, destination)]
    else:
        runs = [run_record(run_group, destination, legacy=legacy)]
    if kind != "cross":
        entry = {"group_key": entry_group, "fingerprint": fp, "verified_run_id": "RUN-FIXTURE",
                 "destinations": [str(destination)], "source_kind": "filesystem_verification"}
        if not legacy:
            entry["source_authority"] = "authoritative_exact_join"
        entries.append(entry)
        if kind == "duplicate":
            entries.append(dict(entry))
    if kind == "cross":
        entries = [{"group_key": GROUP, "fingerprint": fp, "verified_run_id": "RUN-OTHER",
                    "destinations": [str(destination.parent / "different-destination")]}]
    return {"schema_version": 2, "revision": 7, "current_run_id": None,
            "active_writer_id": None, "context_lock": None, "runs": runs,
            "verified_albums": entries}


def make_fixture(case: str, manifest_row: dict | None = None) -> tuple[Path, Path, Path, dict]:
    root = Path(manifest_row["project_root"]) if manifest_row else ROOT / case
    if case == "authority":
        base = root.parent
        if base.exists():
            shutil.rmtree(base)
        root = base / "root-a"
        alternate = base / "root-b"
        backup = root / "backup"
        destination = backup / "destination"
        destination.mkdir(parents=True)
        (root / "config").mkdir(parents=True)
        (root / "state").mkdir(parents=True)
        (alternate / "config").mkdir(parents=True)
        (alternate / "state").mkdir(parents=True)
        for index in range(COUNT):
            (destination / f"image-{index:03d}.jpg").write_bytes(PNG)
        cfg = config(backup)
        write_json(root / "config" / "line_backup_config.json", cfg)
        write_json(alternate / "config" / "line_backup_config.json", cfg)
        write_json(root / "state" / "backup_state.json", state_for(destination, "authority"))
        write_json(alternate / "state" / "backup_state.json", state_for(destination, "authority"))
        (root / "state" / "run_log.md").write_text("fixture run log\n", encoding="utf-8")
        (alternate / "state" / "run_log.md").write_text("alternate run log\n", encoding="utf-8")
        expected = {"filesystem_status": "NOT_RUN", "registry_status": "NOT_RUN", "source_status": "NOT_RUN",
                    "state_status": "NOT_RUN", "overall_status": "UNKNOWN", "failure_class": "INVALID_AUTHORITY",
                    "exit_code": 2, "artifact_readback": "PASS_WITH_NO_STATE_WRITE"}
        return root, destination, alternate / "config" / "line_backup_config.json", expected
    if root.exists():
        shutil.rmtree(root)
    backup = root / "backup"
    destination = backup / "destination"
    destination.mkdir(parents=True)
    (root / "config").mkdir()
    (root / "state").mkdir()
    file_count = int(case) if case in {"56", "58"} else COUNT
    for index in range(file_count):
        (destination / f"image-{index:03d}.jpg").write_bytes(PNG)
    kind = case
    if case in SUFFIXES:
        old = destination / "image-000.jpg"
        old.rename(destination / f"image-000.jpg.{case}")
    elif case == "hidden":
        (destination / ".DS_Store").write_bytes(b"metadata")
        (destination / "._hidden").write_bytes(b"metadata")
        (destination / "__MACOSX").mkdir()
    elif case == "symlink-entry":
        (destination / "linked.jpg").symlink_to(destination / "image-000.jpg")
    elif case == "special":
        os.mkfifo(destination / "special.fifo")
    elif case == "safe":
        (destination / "image-000.jpg").rename(destination / "空 格|pipe\nname.jpg")
    elif case == "text":
        (destination / "image-000.jpg").write_bytes(b"not an image")
    elif case == "mtime":
        pass
    elif case == "bytes":
        pass
    elif case == "dest-symlink":
        real = backup / "real-destination"
        destination.rename(real)
        destination.symlink_to(real, target_is_directory=True)
    if case == "outside":
        outside = ROOT / "outside" / case
        outside.mkdir(parents=True)
        destination = outside
    group = OTHER_GROUP if case == "wrong-group" else GROUP
    if case == "invalid-config":
        cfg = config(backup)
        del cfg["stable_samples"]
    else:
        cfg = config(backup, group=group)
    write_json(root / "config" / "line_backup_config.json", cfg)
    write_json(root / "state" / "backup_state.json", state_for(destination, case))
    (root / "state" / "run_log.md").write_text("fixture run log\n", encoding="utf-8")
    expected = {
        "filesystem_status": "PASS", "registry_status": "PASS", "source_status": "CONFIRMED",
        "state_status": "EXACT", "overall_status": "PASS", "failure_class": "NONE", "exit_code": 0,
        "artifact_readback": "PASS",
    }
    if case in {"56", "58"} or case in SUFFIXES or case in {"hidden", "symlink-entry", "special", "outside", "dest-symlink", "text", "mtime", "bytes"}:
        expected.update(filesystem_status="FAIL", registry_status="NOT_RUN", source_status="NOT_RUN",
                        state_status="NOT_RUN", overall_status="NOT_ACHIEVED", failure_class="INPUT_NEGATIVE", exit_code=4)
    elif case in {"unreadable", "file-command"}:
        expected.update(filesystem_status="FAIL", registry_status="NOT_RUN", source_status="NOT_RUN",
                        state_status="UNKNOWN", overall_status="UNKNOWN",
                        failure_class="INTERNAL_READ_ERROR" if case == "unreadable" else "INTERNAL_COMMAND_ERROR", exit_code=1)
    elif case == "wrong-group":
        expected.update(registry_status="FAIL", source_status="CONTRADICTED", overall_status="NOT_ACHIEVED",
                        failure_class="INPUT_NEGATIVE", exit_code=4)
    elif case == "cross":
        expected.update(registry_status="FAIL", source_status="UNRESOLVED", state_status="STATE_CONTRADICTED",
                        overall_status="NOT_ACHIEVED", failure_class="INPUT_NEGATIVE", exit_code=4)
    elif case == "legacy":
        expected.update(source_status="UNRESOLVED", state_status="LEGACY_PROVENANCE_LIMITED",
                        overall_status="UNKNOWN", failure_class="INPUT_PROVENANCE_LIMITED", exit_code=4)
    elif case == "duplicate":
        expected.update(registry_status="FAIL", source_status="UNRESOLVED", state_status="AMBIGUOUS",
                        overall_status="NOT_ACHIEVED", failure_class="INPUT_NEGATIVE", exit_code=4)
    elif case == "invalid-config":
        expected.update(filesystem_status="NOT_RUN", registry_status="NOT_RUN", source_status="NOT_RUN",
                        state_status="NOT_RUN", overall_status="UNKNOWN", failure_class="INVALID_CONFIGURATION", exit_code=2)
    elif case == "artifact":
        expected.update(filesystem_status="PASS", registry_status="NOT_RUN", source_status="NOT_RUN",
                        state_status="UNKNOWN", overall_status="UNKNOWN", failure_class="INTERNAL_ARTIFACT_ERROR",
                        exit_code=1, artifact_readback="FAIL_WITH_ERROR_ARTIFACT")
    if case in {"mtime", "bytes"}:
        expected["mutation"] = case
    return root, destination, root / "config" / "line_backup_config.json", expected


def command(root: Path, destination: Path, config_path: Path, evidence: Path, case: str,
            manifest_row: dict) -> list[str]:
    state_path = Path(manifest_row["state"])
    return ["/usr/bin/python3", "-m", "line_backup_acceptance", "verify-only",
            "--project-root", str(root), "--config", str(config_path),
            "--state", str(state_path), "--destination", str(destination),
            "--group-key", GROUP, "--start-date", START, "--end-date", END,
            "--expected-images", str(COUNT), "--evidence-dir", str(evidence), "--test-mode"]


def manifest_ok(evidence: Path) -> bool:
    path = evidence / "manifest.json"
    if not path.is_file():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        for item in value["artifacts"]:
            data = (evidence / item["path"]).read_bytes()
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                return False
        return True
    except (KeyError, OSError, ValueError, TypeError):
        return False


def run_case(case: str, manifest_row: dict) -> dict:
    root, destination, config_path, generated_expected = make_fixture(case, manifest_row)
    evidence = Path(manifest_row["evidence_dir"])
    record_dir = root / "records"
    record_dir.mkdir()
    before = {"root": digest(root / "state" / "backup_state.json"), "config": digest(config_path)}
    argv = command(root, destination, config_path, evidence, case, manifest_row)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    if case == "unreadable":
        env["LINE_BACKUP_UNREADABLE_FILE"] = "1"
    if case == "file-command":
        env["LINE_BACKUP_FILE_COMMAND_ERROR"] = "1"
    if case == "artifact":
        env["LINE_BACKUP_ARTIFACT_READBACK_FAILURE"] = "1"
    if case in {"mtime", "bytes"}:
        argv += ["--pause-at", "SAMPLE_2_READY", "--barrier-file", str(root / "sample-2.barrier")]
    process = None
    if case in {"mtime", "bytes"}:
        process = subprocess.Popen(argv, cwd=Path(__file__).resolve().parents[1], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ready = root / "sample-2.barrier.ready"
        deadline = time.time() + 10
        while not ready.exists() and time.time() < deadline:
            time.sleep(0.01)
        target = destination / "image-001.jpg"
        if case == "mtime":
            os.utime(target, ns=(time.time_ns(), time.time_ns() + 1000))
        else:
            target.write_bytes(PNG + b"changed")
        (root / "sample-2.barrier").touch()
        stdout, stderr = process.communicate(timeout=30)
        exit_code = process.returncode
    else:
        process = subprocess.run(argv, cwd=Path(__file__).resolve().parents[1], env=env,
                                 capture_output=True, text=True, check=False)
        stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    (record_dir / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (record_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (record_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (record_dir / "exit-code").write_text(str(exit_code) + "\n", encoding="utf-8")
    after = {"root": digest(root / "state" / "backup_state.json"), "config": digest(config_path)}
    try:
        product = json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, ValueError, json.JSONDecodeError):
        product = {"parse_error": True}
    expected = manifest_row["expected"]
    expected_axes = {key: value for key, value in expected.items() if key != "mutation"}
    observed_axes = {key: product.get(key) for key in expected_axes}
    match = (exit_code == expected["exit_code"] and observed_axes == expected_axes
             and expected == generated_expected and manifest_ok(evidence))
    if case in {"invalid-config", "artifact"}:
        # These errors are not allowed to replace formal fixture authority.
        match = match and before == after
    write_json(record_dir / "independent-oracle.json", {"manifest_expected": expected_axes,
             "fixture_builder_expected": generated_expected, "observed": observed_axes,
             "manifest_ok": manifest_ok(evidence), "before": before, "after": after, "match": match})
    for name, value in (("stdout", stdout), ("stderr", stderr), ("exit_code", str(exit_code) + "\n")):
        Path(manifest_row[name]).parent.mkdir(parents=True, exist_ok=True)
        Path(manifest_row[name]).write_text(value, encoding="utf-8")
    return {"case": case, "id": manifest_row["id"], "argv": argv, "exit_code": exit_code,
            "expected": expected_axes,
            "observed": observed_axes, "manifest_ok": manifest_ok(evidence), "match": match,
            "records": str(record_dir), "literal_manifest_row": manifest_row}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--summary", default=str(ROOT / "summary.json"))
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest["cases"]
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise SystemExit("manifest must contain a non-empty cases array")
    expected_ids = {
        "valid-57", "count-56", "count-58", "part-suffix", "partial-suffix", "tmp-suffix",
        "temp-suffix", "download-suffix", "crdownload-suffix", "incomplete-suffix", "filepart-suffix",
        "hidden-metadata", "symlink-entry", "outside-backup-root", "special-file", "unreadable-file",
        "file-command-error", "mime-mismatch", "safe-filenames", "mtime-at-sample-2", "bytes-at-sample-2",
        "wrong-group", "cross-entry", "legacy-record", "duplicate-registry", "invalid-config",
        "authority-mismatch", "artifact-readback-failure",
    }
    if {row.get("id") for row in rows} != expected_ids:
        raise SystemExit("manifest IDs do not match the approved 28-row matrix")
    if any(not isinstance(row.get("expected"), dict) for row in rows):
        raise SystemExit("every manifest row must contain an independent expected oracle")
    results = [run_case(row["case"], row) for row in rows]
    summary = {"schema_version": 2, "manifest": str(manifest_path), "cases": results,
               "all_match": all(row["match"] for row in results)}
    write_json(Path(args.summary), summary)
    print(json.dumps({"summary": args.summary, "all_match": summary["all_match"],
                      "failed_cases": [r["case"] for r in results if not r["match"]]}, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
