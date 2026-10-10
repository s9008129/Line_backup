from __future__ import annotations

import json
import os
import stat
import struct
import subprocess
import time
import zlib
from pathlib import Path
from typing import Any

from .authority import validate_destination, validate_verify
from .common import (AcceptanceError, atomic_write_json, binding_artifact_matches, classify_legacy_run,
                     json_bytes, parse_binding_reference, read_json, sha256_bytes, sha256_file, utc_now,
                     within, write_result_chain)

REQUIRED_CONFIG = {"schema_version", "group_key", "group_name", "backup_root", "app_identifier",
                   "max_albums_per_run", "recovery_limit", "poll_interval_seconds", "stable_samples", "max_wait_seconds"}
PARTIAL_SUFFIXES = (".part", ".partial", ".tmp", ".temp", ".download", ".crdownload", ".incomplete", ".filepart")
JPEG_MIMES = {"image/jpeg", "image/jpg"}
PNG_MIMES = {"image/png"}
OTHER_IMAGE_MIMES = {"image/gif", "image/webp", "image/tiff", "image/bmp", "image/heic", "image/heif",
                     "image/avif", "image/jxl", "image/svg+xml", "image/x-icon", "image/vnd.microsoft.icon"}


# ---------------------------------------------------------------------------
# Structural image decode (F4 / R5): a recognized JPEG/PNG must also pass a
# deterministic structural decode; anything else fails closed.
# ---------------------------------------------------------------------------

def _png_structurally_ok(data: bytes) -> bool:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    pos = 8
    saw_ihdr = saw_iend = False
    idat = bytearray()
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            return False
        payload = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[end - 4:end])
        if zlib.crc32(ctype + payload) & 0xFFFFFFFF != crc:
            return False
        if not saw_ihdr:
            if ctype != b"IHDR" or length != 13:
                return False
            width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if width < 1 or height < 1 or depth not in (1, 2, 4, 8, 16) or color not in (0, 2, 3, 4, 6):
                return False
            saw_ihdr = True
        elif ctype == b"IHDR":
            return False
        if ctype == b"IDAT":
            idat += payload
        if ctype == b"IEND":
            if length != 0:
                return False
            saw_iend = True
            break
        pos = end
    if not (saw_ihdr and saw_iend and idat):
        return False
    try:
        zlib.decompress(bytes(idat))
    except zlib.error:
        return False
    return True


def _jpeg_structurally_ok(data: bytes) -> bool:
    if not data.startswith(b"\xff\xd8"):
        return False
    pos = 2
    saw_sof = saw_sos = False
    while pos + 1 < len(data):
        if data[pos] != 0xFF:
            return False
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker == 0xD8 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            pos += 2
            continue
        if marker == 0xD9:
            return saw_sof and saw_sos
        if pos + 4 > len(data):
            return False
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if length < 2 or pos + 2 + length > len(data):
            return False
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            saw_sof = True
        if marker == 0xDA:
            saw_sos = True
            return saw_sof and data.rfind(b"\xff\xd9") != -1
        pos += 2 + length
    return saw_sof and saw_sos and data.rfind(b"\xff\xd9") != -1


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


def _image_entry_status(path: Path, mime: str, test_mode: bool) -> tuple[str, str | None]:
    """Return (status, failure_class) for a recognized regular file."""
    if mime in JPEG_MIMES:
        try:
            ok = _jpeg_structurally_ok(path.read_bytes())
        except OSError as exc:
            raise AcceptanceError("INTERNAL_READ_ERROR", f"cannot read {path}: {exc}", 1) from exc
        return ("OK", None) if ok else ("DECODE_ERROR", "INPUT_NEGATIVE")
    if mime in PNG_MIMES:
        try:
            ok = _png_structurally_ok(path.read_bytes())
        except OSError as exc:
            raise AcceptanceError("INTERNAL_READ_ERROR", f"cannot read {path}: {exc}", 1) from exc
        return ("OK", None) if ok else ("DECODE_ERROR", "INPUT_NEGATIVE")
    if mime in OTHER_IMAGE_MIMES:
        return "UNSUPPORTED", "UNSUPPORTED_IMAGE_TYPE"
    return "UNRECOGNIZED", "INPUT_NEGATIVE"


def _inventory(destination: Path, test_mode: bool) -> dict:
    entries: list[dict[str, Any]] = []
    scan_error = None
    try:
        scanned = sorted(os.scandir(destination), key=lambda e: e.name)
    except OSError as exc:
        scanned = []
        scan_error = f"cannot enumerate destination: {exc}"
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
            if item["type"] != "regular":
                entries.append(item)
                continue
            name = Path(rel).name
            if rel.startswith(".") or rel == "__MACOSX" or rel.startswith("__MACOSX/"):
                item["status"] = "HIDDEN"
                entries.append(item)
                continue
            if name.lower().endswith(PARTIAL_SUFFIXES):
                item["status"] = "SUFFIX"
                entries.append(item)
                continue
            if st.st_size == 0:
                item["status"] = "ZERO_BYTE"
                entries.append(item)
                continue
            if test_mode and os.environ.get("LINE_BACKUP_UNREADABLE_FILE") == "1":
                item["status"] = "READ_ERROR"
                item["error_code"] = "INTERNAL_READ_ERROR"
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
            except (PermissionError, OSError) as exc:
                item["status"] = "READ_ERROR"
                item["error"] = str(exc)
                item["error_code"] = "INTERNAL_READ_ERROR"
            if item.get("status") == "OK":
                item["status"], item["failure_class"] = _image_entry_status(Path(entry.path), item["mime"], test_mode)
            entries.append(item)
        except OSError as exc:
            entries.append({"relative_path": rel, "status": "READ_ERROR", "type": "unknown",
                            "error": str(exc), "error_code": "INTERNAL_READ_ERROR"})
    recognized = sum(e.get("status") == "OK" and e.get("type") == "regular" for e in entries)
    return {"observed_at": utc_now(), "root": str(destination), "entries": entries,
            "scan_error": scan_error,
            "regular_files": sum(e.get("type") == "regular" for e in entries),
            "recognized_images": recognized,
            "total_bytes": sum(e.get("size", 0) for e in entries),
            "error_codes": sorted({e.get("error_code") for e in entries if e.get("error_code")})}


def _inventory_key(inv: dict) -> list[tuple]:
    return [tuple((e.get(k) for k in ("relative_path", "type", "size", "mtime_ns", "mime", "sha256", "status")))
            for e in inv["entries"]]


def _classify_filesystem(samples: list[dict], expected: int) -> tuple[str, str]:
    first = samples[0]
    for sample in samples:
        if sample.get("scan_error"):
            return "FAIL", "INTERNAL_READ_ERROR"
    if not all(_inventory_key(x) == _inventory_key(first) and x["total_bytes"] == first["total_bytes"] for x in samples):
        return "FAIL", "INPUT_NEGATIVE"
    unsupported = False
    for item in first["entries"]:
        if item.get("type") != "regular" or item.get("status") != "OK":
            if item.get("status") == "UNSUPPORTED":
                unsupported = True
            else:
                return "FAIL", item.get("failure_class") or "INPUT_NEGATIVE"
    if unsupported:
        return "FAIL", "UNSUPPORTED_IMAGE_TYPE"
    if first["recognized_images"] != expected:
        return "FAIL", "INPUT_NEGATIVE"
    return "PASS", "NONE"


# ---------------------------------------------------------------------------
# Read-only association axes (F2/F4, Rev15 §15.4, Rev16 §16.8, Rev18 §18.1)
# ---------------------------------------------------------------------------

def _same_fp(candidate: Any, fp: dict) -> bool:
    return isinstance(candidate, dict) and all(candidate.get(k) == v for k, v in fp.items())


def _link_kind(state: dict, entry: dict, destination: str) -> str:
    run_id = entry.get("verified_run_id")
    if run_id is None:
        return "null"
    run = next((r for r in state.get("runs", []) if isinstance(r, dict) and r.get("run_id") == run_id), None)
    if run is None:
        return "dangling"
    if (run.get("group_key") == entry.get("group_key") and _same_fp(run.get("fingerprint"), entry.get("fingerprint") or {})
            and destination in (entry.get("destinations") or [])):
        return "verified" if run.get("workflow_outcome") == "VERIFIED" else "unverified"
    return "mismatched"


def _axes(state: dict, *, request_group: str, fp: dict, destination: str, app_identifier: str,
          project_root: Path, state_path: Path, evidence_dir: Path, test_mode: bool) -> dict:
    runs = [r for r in state.get("runs", []) if isinstance(r, dict)]
    entries = [e for e in state.get("verified_albums", []) if isinstance(e, dict)]
    legacy_normalizations = []
    for run in runs:
        kind, detail = classify_legacy_run(run)
        if kind is not None:
            legacy_normalizations.append({"run_id": run.get("run_id"), "kind": kind, "detail": detail})
    legacy_present = bool(legacy_normalizations) or any(not isinstance(r, dict) for r in state.get("runs", []))

    candidates = [e for e in entries if e.get("group_key") == request_group and _same_fp(e.get("fingerprint"), fp)
                  and destination in (e.get("destinations") or [])]
    matching_runs = [r for r in runs if r.get("group_key") == request_group and _same_fp(r.get("fingerprint"), fp)
                     and r.get("destination") == destination]
    links = {id(e): _link_kind(state, e, destination) for e in candidates}

    unique_candidate = candidates[0] if len(candidates) == 1 else None
    registry = "PASS" if (unique_candidate is not None and links[id(unique_candidate)] in {"null", "verified"}) else "FAIL"

    contradicted_link = any(links[id(e)] == "mismatched" for e in candidates)
    near_miss_contradiction = any(
        e.get("group_key") == request_group and _same_fp(e.get("fingerprint"), fp)
        and destination not in (e.get("destinations") or []) and _link_kind(state, e, destination) == "dangling"
        for e in entries)
    cross_pair_contradiction = False
    for e in entries:
        run_id = e.get("verified_run_id")
        if run_id is None:
            continue
        run = next((r for r in runs if r.get("run_id") == run_id), None)
        if run is None:
            continue
        if (e.get("group_key") != run.get("group_key") and _same_fp(e.get("fingerprint"), fp)
                and _same_fp(run.get("fingerprint"), fp)
                and request_group in {e.get("group_key"), run.get("group_key")}):
            cross_pair_contradiction = True

    if len(candidates) > 1 or len(matching_runs) > 1:
        state_status = "AMBIGUOUS"
    elif contradicted_link or near_miss_contradiction:
        state_status = "STATE_CONTRADICTED"
    elif legacy_present:
        state_status = "LEGACY_PROVENANCE_LIMITED"
    elif len(matching_runs) == 1:
        state_status = "EXACT"
    else:
        state_status = "UNKNOWN"

    binding_defect = False
    source = "UNRESOLVED"
    if cross_pair_contradiction or contradicted_link:
        source = "CONTRADICTED"
    elif unique_candidate is not None and links[id(unique_candidate)] == "verified":
        run = next(r for r in runs if r.get("run_id") == unique_candidate.get("verified_run_id"))
        reference = unique_candidate.get("evidence")
        same_reference = any(isinstance(ev, dict) and ev.get("evidence") == reference for ev in run.get("events", []))
        if not same_reference:
            binding_defect = True
        elif binding_artifact_matches(str(reference), app_identifier=app_identifier, group_key=request_group, fp=fp,
                                      project_root=project_root, test_mode=test_mode,
                                      state_path=state_path, evidence_dir=evidence_dir):
            source = "CONFIRMED"
        else:
            binding_defect = True
    elif unique_candidate is not None and links[id(unique_candidate)] == "null":
        binding_defect = True
    # A missing/unverified/dangling link is an association defect (Registry FAIL) and leaves
    # Source UNRESOLVED without a provenance-limited classification.

    if state_status == "LEGACY_PROVENANCE_LIMITED":
        overall, exit_code, failure = "UNKNOWN", 4, "INPUT_PROVENANCE_LIMITED"
    elif registry == "PASS" and source == "CONFIRMED" and state_status == "EXACT":
        overall, exit_code, failure = "PASS", 0, "NONE"
    else:
        overall, exit_code = "NOT_ACHIEVED", 4
        failure = "INPUT_PROVENANCE_LIMITED" if (binding_defect and source == "UNRESOLVED" and not contradicted_link) else "INPUT_NEGATIVE"
    source_kind = None
    if source == "CONFIRMED":
        parsed = parse_binding_reference(unique_candidate.get("evidence") if unique_candidate else None)
        source_kind = "user_attestation" if (parsed is not None and parsed[0] == "user_fact") else "filesystem_verification"
    return {"registry_status": registry, "source_status": source, "state_status": state_status,
            "overall_status": overall, "exit_code": exit_code, "failure_class": failure,
            "source_kind": source_kind,
            "legacy_normalizations": legacy_normalizations, "binding_defect": binding_defect}


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


def inspect(ns) -> tuple[dict, int]:
    authority = validate_verify(ns)
    evidence = Path(authority["evidence_dir"])
    evidence.mkdir(parents=True, exist_ok=True)
    destination = Path(ns.destination or "")
    try:
        config = _config(Path(authority["config"]))
        validate_destination(destination, Path(config["backup_root"]))
        if not destination.is_dir():
            raise AcceptanceError("INPUT_NEGATIVE", "destination is not an existing directory", 4)
    except AcceptanceError as exc:
        result = {"schema_version": 1, "mode": "verify_only", "run_id": getattr(ns, "run_id", None),
                  "group_key": ns.group_key, "fingerprint": _request_fp(ns),
                  "destination": str(destination),
                  "filesystem_status": "NOT_RUN" if exc.code == "INVALID_CONFIGURATION" else "FAIL",
                  "recognized_images": None, "expected_images": ns.expected_images,
                  "registry_status": "NOT_RUN", "source_status": "NOT_RUN", "state_status": "NOT_RUN",
                  "overall_status": "NOT_ACHIEVED" if exc.exit_code == 4 else "UNKNOWN",
                  "failure_class": exc.code, "exit_code": exc.exit_code, "artifact_readback": "PASS"}
        _write_chain(evidence, result)
        return result, exc.exit_code
    try:
        state = _state(Path(authority["state"]))
    except AcceptanceError as exc:
        result = {"schema_version": 1, "mode": "verify_only", "run_id": getattr(ns, "run_id", None),
                  "group_key": ns.group_key, "fingerprint": _request_fp(ns),
                  "destination": str(destination), "filesystem_status": "NOT_RUN",
                  "recognized_images": None, "expected_images": ns.expected_images,
                  "registry_status": "NOT_RUN", "source_status": "NOT_RUN", "state_status": "NOT_RUN",
                  "overall_status": "UNKNOWN", "failure_class": exc.code, "exit_code": exc.exit_code,
                  "artifact_readback": "PASS"}
        _write_chain(evidence, result)
        return result, exc.exit_code

    samples = []
    for index in range(3):
        if ns.test_mode and ns.pause_at == "SAMPLE_2_READY" and index == 1:
            from .common import wait_barrier
            wait_barrier(ns.pause_at, ns.barrier_file)
        samples.append(_inventory(destination, ns.test_mode))
        atomic_write_json(evidence / f"inventory-{index + 1}.json", samples[-1])
        if index < 2 and not ns.test_mode:
            time.sleep(config["poll_interval_seconds"])

    fp = _request_fp(ns)
    read_error = any(e.get("status") == "READ_ERROR" for sample in samples for e in sample["entries"]) \
        or any(sample.get("scan_error") for sample in samples)
    error_codes = {code for sample in samples for code in sample.get("error_codes", [])}
    if read_error:
        failure = "INTERNAL_COMMAND_ERROR" if "INTERNAL_COMMAND_ERROR" in error_codes else "INTERNAL_READ_ERROR"
        result = {"schema_version": 1, "mode": "verify_only", "run_id": getattr(ns, "run_id", None),
                  "group_key": ns.group_key, "fingerprint": fp, "destination": str(destination),
                  "filesystem_status": "FAIL", "recognized_images": samples[-1]["recognized_images"],
                  "expected_images": ns.expected_images, "registry_status": "NOT_RUN",
                  "source_status": "NOT_RUN", "state_status": "UNKNOWN", "overall_status": "UNKNOWN",
                  "failure_class": failure, "exit_code": 1, "artifact_readback": "PASS",
                  "inventory_samples": 3, "filesystem": samples[-1], "state_revision": state.get("revision")}
        _write_chain(evidence, result)
        return result, 1

    fs_status, fs_failure = _classify_filesystem(samples, ns.expected_images)
    if fs_status != "PASS":
        result = {"schema_version": 1, "mode": "verify_only", "run_id": getattr(ns, "run_id", None),
                  "group_key": ns.group_key, "fingerprint": fp, "destination": str(destination),
                  "filesystem_status": "FAIL", "recognized_images": samples[-1]["recognized_images"],
                  "expected_images": ns.expected_images, "registry_status": "NOT_RUN",
                  "source_status": "NOT_RUN", "state_status": "NOT_RUN", "overall_status": "NOT_ACHIEVED",
                  "failure_class": fs_failure, "exit_code": 4, "artifact_readback": "PASS",
                  "inventory_samples": 3, "filesystem": samples[-1], "state_revision": state.get("revision")}
        _write_chain(evidence, result)
        return result, 4

    axes = _axes(state, request_group=ns.group_key, fp=fp, destination=str(destination),
                 app_identifier=config["app_identifier"], project_root=Path(authority["project_root"]),
                 state_path=Path(authority["state"]), evidence_dir=evidence, test_mode=ns.test_mode)
    result = {"schema_version": 1, "mode": "verify_only", "run_id": getattr(ns, "run_id", None),
              "group_key": ns.group_key, "fingerprint": fp, "destination": str(destination),
              "filesystem_status": "PASS", "recognized_images": samples[-1]["recognized_images"],
              "expected_images": ns.expected_images, "registry_status": axes["registry_status"],
              "source_status": axes["source_status"], "state_status": axes["state_status"],
              "overall_status": axes["overall_status"], "failure_class": axes["failure_class"],
              "source_kind": axes["source_kind"],
              "exit_code": axes["exit_code"], "artifact_readback": "PASS",
              "inventory_samples": 3, "filesystem": samples[-1], "state_revision": state.get("revision"),
              "legacy_normalizations": axes["legacy_normalizations"]}
    if ns.test_mode and os.environ.get("LINE_BACKUP_ARTIFACT_READBACK_FAILURE") == "1":
        _write_chain(evidence, result, inject_readback_failure=True)
        raise AcceptanceError("INTERNAL_ARTIFACT_ERROR", "injected evidence manifest read-back failure", 1)
    _write_chain(evidence, result)
    return result, axes["exit_code"]


def _request_fp(ns) -> dict:
    return {"start_date": ns.start_date, "end_date": ns.end_date, "expected_images": ns.expected_images}


def _write_chain(evidence: Path, result: dict, *, inject_readback_failure: bool = False) -> dict:
    return write_result_chain(evidence, result, inject_readback_failure=inject_readback_failure)


def write_error(evidence_dir: Path, error: AcceptanceError, authority: dict | None = None) -> dict:
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if error.code == "INVALID_AUTHORITY":
        fs_status = "NOT_RUN"
    elif error.code == "INTERNAL_ARTIFACT_ERROR":
        fs_status = "PASS"
    elif error.code in {"INTERNAL_READ_ERROR", "INTERNAL_COMMAND_ERROR", "INPUT_NEGATIVE", "UNSUPPORTED_IMAGE_TYPE"}:
        fs_status = "FAIL"
    else:
        fs_status = "NOT_RUN"
    result = {"schema_version": 1, "mode": "verify_only",
              "filesystem_status": fs_status, "recognized_images": None, "expected_images": None,
              "registry_status": "NOT_RUN", "source_status": "NOT_RUN",
              "state_status": "UNKNOWN" if error.code == "INTERNAL_ARTIFACT_ERROR" else "NOT_RUN",
              "overall_status": "UNKNOWN", "failure_class": error.code, "error": error.message,
              "exit_code": error.exit_code, "artifact_readback":
              "PASS_WITH_NO_STATE_WRITE" if error.code == "INVALID_AUTHORITY"
              else "FAIL_WITH_ERROR_ARTIFACT" if error.code == "INTERNAL_ARTIFACT_ERROR" else "PASS"}
    if error.code != "INVALID_AUTHORITY":
        atomic_write_json(evidence_dir / "error.json", {"code": error.code, "message": error.message})
    try:
        write_result_chain(evidence_dir, result)
    except AcceptanceError:
        pass
    return result
