from __future__ import annotations

import json
import os
import stat
import subprocess
import time
from pathlib import Path
from typing import Any

from .authority import validate_destination, validate_verify
from .common import AcceptanceError, atomic_write_json, json_bytes, read_json, sha256_bytes, sha256_file, utc_now, within

REQUIRED_CONFIG = {"schema_version", "group_key", "group_name", "backup_root", "app_identifier",
                   "max_albums_per_run", "recovery_limit", "poll_interval_seconds", "stable_samples", "max_wait_seconds"}
PARTIAL_SUFFIXES = (".part", ".partial", ".tmp", ".temp", ".download", ".crdownload", ".incomplete", ".filepart")
IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/tiff", "image/bmp", "image/heic", "image/avif"}


def _write_manifest(evidence: Path) -> dict:
    artifacts = []
    for path in sorted(evidence.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            data = path.read_bytes()
            artifacts.append({"path": path.name, "bytes": len(data), "sha256": sha256_bytes(data)})
    manifest = {"schema_version": 1, "artifacts": artifacts}
    atomic_write_json(evidence / "manifest.json", manifest)
    if read_json(evidence / "manifest.json") != manifest:
        raise AcceptanceError("INTERNAL_ARTIFACT_ERROR", "manifest read-back mismatch", 1)
    return manifest


def _config(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptanceError("INVALID_CONFIGURATION", f"cannot read config: {exc}", 2) from exc
    if not isinstance(value, dict) or set(value) != REQUIRED_CONFIG:
        raise AcceptanceError("INVALID_CONFIGURATION", "config keys do not match schema v2", 2)
    if value.get("schema_version") != 2 or not isinstance(value.get("group_key"), str) or not value["group_key"]:
        raise AcceptanceError("INVALID_CONFIGURATION", "invalid schema/group key", 2)
    if not isinstance(value.get("group_name"), str) or not value["group_name"] or not isinstance(value.get("backup_root"), str) or not value["backup_root"].startswith("/"):
        raise AcceptanceError("INVALID_CONFIGURATION", "invalid group name or backup root", 2)
    if value.get("app_identifier") != "jp.naver.line.mac" or not isinstance(value.get("max_albums_per_run"), int) or value["max_albums_per_run"] < 1:
        raise AcceptanceError("INVALID_CONFIGURATION", "invalid app or album limit", 2)
    if value.get("recovery_limit") != 1 or value.get("poll_interval_seconds") != 5 or value.get("stable_samples") != 3 or not isinstance(value.get("max_wait_seconds"), int) or value["max_wait_seconds"] < 15:
        raise AcceptanceError("INVALID_CONFIGURATION", "invalid recovery/polling values", 2)
    return value


def _state(path: Path) -> dict:
    value = read_json(path)
    required = {"schema_version", "revision", "current_run_id", "active_writer_id", "context_lock", "runs", "verified_albums"}
    if not isinstance(value, dict) or value.get("schema_version") != 2 or not required.issubset(value) or not isinstance(value.get("runs"), list) or not isinstance(value.get("verified_albums"), list):
        raise AcceptanceError("STATE_READ_ERROR", "state is not a readable schema v2 registry", 1)
    return value


def _mime(path: Path, test_mode: bool) -> str:
    if test_mode and os.environ.get("LINE_BACKUP_FILE_COMMAND_ERROR") == "1":
        raise AcceptanceError("INTERNAL_COMMAND_ERROR", "injected file-command failure", 1)
    try:
        p = subprocess.run(["/usr/bin/file", "--mime-type", "-b", "--", str(path)], capture_output=True, text=True, check=False)
    except OSError as exc:
        raise AcceptanceError("INTERNAL_COMMAND_ERROR", f"file command failed to start: {exc}", 1) from exc
    if p.returncode != 0:
        raise AcceptanceError("INTERNAL_COMMAND_ERROR", f"file command returned {p.returncode}: {p.stderr.strip()}", 1)
    return p.stdout.strip()


def _inventory(destination: Path, test_mode: bool) -> dict:
    entries: list[dict[str, Any]] = []
    try:
        scanned = sorted(os.scandir(destination), key=lambda e: e.name)
    except OSError as exc:
        raise AcceptanceError("INTERNAL_READ_ERROR", f"cannot enumerate destination: {exc}", 1) from exc
    for entry in scanned:
        rel = entry.name
        try:
            st = entry.stat(follow_symlinks=False)
            mode = st.st_mode
            item: dict[str, Any] = {"relative_path": rel, "size": st.st_size, "mtime_ns": st.st_mtime_ns,
                                    "status": "OK", "type": "regular" if stat.S_ISREG(mode) else "other"}
            if stat.S_ISLNK(mode):
                item["type"] = "symlink"
            elif stat.S_ISDIR(mode):
                item["type"] = "directory"
            elif not stat.S_ISREG(mode):
                item["type"] = "special"
            if stat.S_ISREG(mode):
                if st.st_size == 0:
                    item["status"] = "ZERO_BYTE"
                if test_mode and os.environ.get("LINE_BACKUP_UNREADABLE_FILE") == "1" and rel == "image-000.jpg":
                    item["status"] = "READ_ERROR"
                    item["error"] = "injected unreadable regular file"
                    entries.append(item)
                    continue
                try:
                    item["mime"] = _mime(Path(entry.path), test_mode)
                    item["sha256"] = sha256_file(Path(entry.path))
                except AcceptanceError as exc:
                    item["status"] = "READ_ERROR"
                    item["error"] = exc.message
                    item["error_code"] = exc.code
                except PermissionError as exc:
                    item["status"] = "READ_ERROR"
                    item["error"] = str(exc)
                    item["error_code"] = "INTERNAL_READ_ERROR"
                except OSError as exc:
                    item["status"] = "READ_ERROR"
                    item["error"] = str(exc)
                    item["error_code"] = "INTERNAL_READ_ERROR"
                if item.get("status") == "OK" and item.get("mime") not in IMAGE_MIMES:
                    item["status"] = "UNRECOGNIZED"
            entries.append(item)
        except OSError as exc:
            entries.append({"relative_path": rel, "status": "READ_ERROR", "type": "unknown", "error": str(exc)})
    return {"observed_at": utc_now(), "root": str(destination), "entries": entries,
            "regular_files": sum(e.get("type") == "regular" for e in entries),
            "recognized_images": sum(e.get("type") == "regular" and e.get("status") == "OK" and e.get("mime") in IMAGE_MIMES for e in entries),
            "total_bytes": sum(e.get("size", 0) for e in entries),
            "error_codes": sorted({e.get("error_code") for e in entries if e.get("error_code")})}


def _inventory_key(inv: dict) -> list[tuple]:
    return [tuple((e.get(k) for k in ("relative_path", "type", "size", "mtime_ns", "mime", "sha256", "status"))) for e in inv["entries"]]


def _classify_filesystem(samples: list[dict], expected: int) -> tuple[str, str]:
    first = samples[0]
    bad = False
    for item in first["entries"]:
        name = item.get("relative_path", "")
        if item.get("type") != "regular" or name.startswith(".") or name == "__MACOSX" or name.startswith("__MACOSX/") or name.lower().endswith(PARTIAL_SUFFIXES) or item.get("status") != "OK":
            bad = True
    stable = all(_inventory_key(x) == _inventory_key(first) and x["total_bytes"] == first["total_bytes"] for x in samples)
    if not stable:
        return "FAIL", "INPUT_NEGATIVE"
    if first["recognized_images"] != expected or bad:
        return "FAIL", "INPUT_NEGATIVE"
    return "PASS", "NONE"


def _same_fp(a: Any, fp: dict) -> bool:
    return isinstance(a, dict) and all(a.get(k) == v for k, v in fp.items())


def _association(state: dict, group_key: str, fp: dict, destination: str) -> tuple[str, str, str]:
    entries = [x for x in state.get("verified_albums", []) if isinstance(x, dict) and x.get("group_key") == group_key and _same_fp(x.get("fingerprint"), fp)]
    exact = [x for x in entries if destination in (x.get("destinations") or [])]
    registry = "PASS" if len(exact) == 1 and len(entries) == 1 else "FAIL"
    candidates = [r for r in state.get("runs", []) if isinstance(r, dict) and r.get("group_key") == group_key and _same_fp(r.get("fingerprint"), fp) and r.get("destination") == destination]
    related_legacy_runs = [r for r in state.get("runs", []) if isinstance(r, dict) and r.get("group_key") != group_key
                           and _same_fp(r.get("fingerprint"), fp) and r.get("destination") == destination
                           and (not r.get("contract_revision") or not r.get("observed_title") or not r.get("source_provenance"))]
    related_legacy_entries = [x for x in state.get("verified_albums", []) if isinstance(x, dict) and x.get("group_key") != group_key
                              and _same_fp(x.get("fingerprint"), fp) and destination in (x.get("destinations") or [])]
    if len(exact) > 1 or len(candidates) > 1:
        state_status = "AMBIGUOUS"
    elif candidates and (not candidates[0].get("contract_revision") or not candidates[0].get("observed_title") or not candidates[0].get("source_provenance")):
        state_status = "LEGACY_PROVENANCE_LIMITED"
    elif candidates and entries and not exact:
        state_status = "STATE_CONTRADICTED"
    elif candidates:
        state_status = "EXACT"
    elif related_legacy_runs and related_legacy_entries:
        state_status = "LEGACY_PROVENANCE_LIMITED"
    elif entries or candidates:
        state_status = "STATE_CONTRADICTED"
    else:
        state_status = "UNKNOWN"
    source_proof = bool(exact and exact[0].get("source_authority") == "authoritative_exact_join")
    return registry, state_status, "CONFIRMED" if registry == "PASS" and state_status == "EXACT" and source_proof else "UNRESOLVED"


def inspect(ns) -> tuple[dict, int]:
    authority = validate_verify(ns)
    evidence = Path(authority["evidence_dir"])
    try:
        config = _config(Path(authority["config"]))
        state = _state(Path(authority["state"]))
        destination = Path(os.path.abspath(ns.destination))
        backup_root = Path(config["backup_root"])
        try:
            validate_destination(destination, backup_root)
        except AcceptanceError as exc:
            if exc.code != "INPUT_NEGATIVE":
                raise
            result = {"schema_version": 1, "mode": "verify_only", "filesystem_status": "FAIL", "registry_status": "NOT_RUN", "source_status": "NOT_RUN", "state_status": "NOT_RUN", "overall_status": "NOT_ACHIEVED", "failure_class": exc.code, "exit_code": 4, "artifact_readback": "PASS", "destination": str(destination)}
            atomic_write_json(evidence / "result.json", result)
            _write_manifest(evidence)
            return result, 4
        if not destination.is_dir():
            raise AcceptanceError("INVALID_INPUT", "destination is not an existing directory", 2)
        samples = []
        for index in range(3):
            if ns.test_mode and ns.pause_at == "SAMPLE_2_READY" and index == 1:
                from .common import wait_barrier
                wait_barrier(ns.pause_at, ns.barrier_file)
            samples.append(_inventory(destination, ns.test_mode))
            atomic_write_json(evidence / f"inventory-{index + 1}.json", samples[-1])
            if index < 2 and not ns.test_mode:
                time.sleep(config["poll_interval_seconds"])
        fs_status, failure = _classify_filesystem(samples, ns.expected_images)
        fp = {"start_date": ns.start_date, "end_date": ns.end_date, "expected_images": ns.expected_images}
        read_error = any(e.get("status") == "READ_ERROR" for e in samples[0]["entries"])
        error_codes = {code for sample in samples for code in sample.get("error_codes", [])}
        if read_error:
            registry, source, state_status = "NOT_RUN", "NOT_RUN", "UNKNOWN"
            failure = "INTERNAL_COMMAND_ERROR" if "INTERNAL_COMMAND_ERROR" in error_codes else "INTERNAL_READ_ERROR"
            overall, exit_code = "UNKNOWN", 1
        elif fs_status != "PASS":
            registry, source, state_status = "NOT_RUN", "NOT_RUN", "NOT_RUN"
            overall, exit_code = "NOT_ACHIEVED", 4
        else:
            registry, state_status, source = _association(state, ns.group_key, fp, str(destination))
            if config["group_key"] != ns.group_key and state_status == "EXACT":
                source = "CONTRADICTED"
            if failure == "NONE" and registry == "PASS" and source == "CONFIRMED" and state_status == "EXACT":
                overall, exit_code = "PASS", 0
            elif state_status == "LEGACY_PROVENANCE_LIMITED":
                overall, exit_code, failure = "UNKNOWN", 4, "INPUT_PROVENANCE_LIMITED"
            else:
                overall, exit_code = "NOT_ACHIEVED", 4
            if overall == "NOT_ACHIEVED" and failure == "NONE":
                failure = "INPUT_NEGATIVE"
        if ns.test_mode and os.environ.get("LINE_BACKUP_ARTIFACT_READBACK_FAILURE") == "1":
            raise AcceptanceError("INTERNAL_ARTIFACT_ERROR", "injected evidence manifest read-back failure", 1)
        result = {"schema_version": 1, "mode": "verify_only", "filesystem_status": fs_status,
                  "registry_status": registry, "source_status": source, "state_status": state_status,
                  "overall_status": overall, "failure_class": failure, "exit_code": exit_code,
                  "artifact_readback": "PASS", "fingerprint": fp, "group_key": ns.group_key,
                  "destination": str(destination), "inventory_samples": 3,
                  "filesystem": samples[-1], "state_revision": state.get("revision")}
        atomic_write_json(evidence / "result.json", result)
        _write_manifest(evidence)
        return result, exit_code
    except AcceptanceError:
        raise


def write_error(evidence_dir: Path, error: AcceptanceError, authority: dict | None = None) -> dict:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    fs_status = "FAIL" if error.code in {"INTERNAL_READ_ERROR", "INTERNAL_COMMAND_ERROR", "INPUT_NEGATIVE"} else "PASS" if error.code == "INTERNAL_ARTIFACT_ERROR" else "NOT_RUN"
    result = {"schema_version": 1, "overall_status": "UNKNOWN", "filesystem_status": "NOT_RUN",
              "registry_status": "NOT_RUN", "source_status": "NOT_RUN", "state_status": "UNKNOWN" if error.code == "INTERNAL_ARTIFACT_ERROR" else "NOT_RUN",
              "failure_class": error.code, "error": error.message, "exit_code": error.exit_code,
              "artifact_readback": "PASS_WITH_NO_STATE_WRITE" if error.code == "INVALID_AUTHORITY" else "FAIL_WITH_ERROR_ARTIFACT" if error.code == "INTERNAL_ARTIFACT_ERROR" else "UNKNOWN"}
    result["filesystem_status"] = fs_status
    atomic_write_json(evidence_dir / "result.json", result)
    if error.code != "INVALID_AUTHORITY":
        atomic_write_json(evidence_dir / "error.json", {"code": error.code, "message": error.message})
    if error.code == "INVALID_AUTHORITY":
        _write_manifest(evidence_dir)
        return result
    if error.code != "INTERNAL_ARTIFACT_ERROR":
        _write_manifest(evidence_dir)
        result["artifact_readback"] = "PASS"
        atomic_write_json(evidence_dir / "result.json", result)
        _write_manifest(evidence_dir)
    else:
        _write_manifest(evidence_dir)
    return result
