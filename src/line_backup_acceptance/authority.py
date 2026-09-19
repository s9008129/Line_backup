from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .common import AcceptanceError, exact_real_path, read_json, within


CASE_ROOTS = {Path(f"/private/tmp/line-backup-acceptance-case-{i:02d}") for i in range(1, 26)}
VERIFIER_ROOT = Path("/private/tmp/line-backup-acceptance-verifier")
CONFIG_KEYS = {
    "schema_version", "group_key", "group_name", "backup_root", "app_identifier",
    "max_albums_per_run", "recovery_limit", "poll_interval_seconds", "stable_samples",
    "max_wait_seconds",
}


def _absolute(path: str | None) -> Path | None:
    return Path(os.path.abspath(path)) if path else None


def _within_fixture_root(path: Path, root: Path) -> bool:
    """Require both lexical and symlink-resolved containment under a canonical fixture root."""
    absolute = Path(os.path.abspath(path))
    real = Path(os.path.realpath(absolute))
    real_root = Path(os.path.realpath(root))
    return within(absolute, root) and within(real, real_root)


def _require_file(path: Path, label: str) -> None:
    if not exact_real_path(path) or not path.is_file():
        raise AcceptanceError("INVALID_AUTHORITY", f"{label} is not the canonical readable authority file", 2)


def _load_production_config(path: Path) -> dict[str, Any]:
    _require_file(path, "config")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptanceError("INVALID_AUTHORITY", f"canonical config cannot be read: {exc}", 2) from exc
    if not isinstance(value, dict) or set(value) != CONFIG_KEYS:
        raise AcceptanceError("INVALID_AUTHORITY", "canonical config does not match schema v2", 2)
    if value.get("schema_version") != 2 or not isinstance(value.get("group_key"), str):
        raise AcceptanceError("INVALID_AUTHORITY", "canonical config has invalid schema/group", 2)
    backup_root = value.get("backup_root")
    if not isinstance(backup_root, str) or not backup_root.startswith("/"):
        raise AcceptanceError("INVALID_AUTHORITY", "canonical backup root is not absolute", 2)
    if value.get("app_identifier") != "jp.naver.line.mac":
        raise AcceptanceError("INVALID_AUTHORITY", "canonical config has invalid app identifier", 2)
    return value


def _validate_required_transaction_args(ns) -> None:
    required_by_operation = {
        "prepare": ("run_id", "owner_id", "group_key", "start_date", "end_date", "expected_images", "destination"),
        "resume": ("run_id", "expected_revision", "expected_owner_id"),
        "commit": ("run_id", "expected_revision", "expected_owner_id"),
        "finalize": ("run_id", "expected_revision", "expected_owner_id", "outcome"),
        "duplicate-check": ("group_key", "start_date", "end_date", "expected_images", "destination"),
    }
    for name in required_by_operation.get(getattr(ns, "operation", ""), ()):
        if getattr(ns, name, None) is None:
            raise AcceptanceError("INVALID_INPUT", f"--{name.replace('_', '-')} is required", 2)


def validate_verify(ns) -> dict[str, str]:
    root = _absolute(ns.project_root)
    evidence = _absolute(ns.evidence_dir)
    if root is None or evidence is None:
        raise AcceptanceError("INVALID_AUTHORITY", "explicit project-root and evidence-dir are required", 2)
    if not exact_real_path(root) or not root.is_dir():
        raise AcceptanceError("INVALID_AUTHORITY", "project root is symlinked, missing, or not a directory", 2)
    expected_config = root / "config" / "line_backup_config.json"
    expected_state = root / "state" / "backup_state.json"
    if _absolute(ns.config) != expected_config or _absolute(ns.state) != expected_state:
        raise AcceptanceError("INVALID_AUTHORITY", "config/state are not canonical children of project root", 2)
    _require_file(expected_config, "config")
    _require_file(expected_state, "state")
    if ns.test_mode:
        allowed = root in CASE_ROOTS or root == VERIFIER_ROOT or within(root, VERIFIER_ROOT)
        if not allowed:
            raise AcceptanceError("INVALID_AUTHORITY", "verify test mode is outside the literal fixture roots", 2)
    else:
        if root == VERIFIER_ROOT or within(root, VERIFIER_ROOT):
            raise AcceptanceError("INVALID_AUTHORITY", "fixture root requires test mode", 2)
    return {"project_root": str(root), "config": str(expected_config), "state": str(expected_state),
            "run_log": str(root / "state" / "run_log.md"), "evidence_dir": str(evidence)}


def _validate_fixture_paths(ns, root: Path) -> None:
    for name in ("destination", "dispatcher", "dispatch_counter", "verification_json", "barrier_file",
                 "source_evidence"):
        value = getattr(ns, name, None)
        if value and not _within_fixture_root(_absolute(value), root):
            raise AcceptanceError("INVALID_AUTHORITY", f"--{name.replace('_', '-')} is outside test root", 2)


def validate_transaction(ns) -> dict[str, Any]:
    root = _absolute(ns.project_root)
    state = _absolute(ns.state)
    evidence = _absolute(ns.evidence_dir)
    if root is None or state is None or evidence is None:
        raise AcceptanceError("INVALID_AUTHORITY", "explicit project-root, state and evidence-dir are required", 2)
    if not exact_real_path(root) or not root.is_dir():
        raise AcceptanceError("INVALID_AUTHORITY", "project root is symlinked, missing, or not a directory", 2)
    if ns.test_mode:
        if root not in CASE_ROOTS:
            raise AcceptanceError("INVALID_AUTHORITY", "test mode requires one literal case root", 2)
        expected_config = root / "config" / "line_backup_config.json"
        expected_run_log = root / "state" / "run_log.md"
        expected_state = root / "state" / "backup_state.json"
        if (_absolute(getattr(ns, "config", None)) != expected_config
                or _absolute(getattr(ns, "run_log", None)) != expected_run_log
                or state != expected_state):
            raise AcceptanceError("INVALID_AUTHORITY", "test mode requires the canonical case-root children", 2)
        _require_file(expected_config, "config")
        _require_file(expected_state, "state")
        _require_file(expected_run_log, "run-log")
        if not _within_fixture_root(evidence, root):
            raise AcceptanceError("INVALID_AUTHORITY", "test evidence must remain under case root", 2)
        _validate_fixture_paths(ns, root)
        _validate_required_transaction_args(ns)
        return {"project_root": str(root), "config": str(expected_config), "run_log": str(expected_run_log),
                "state": str(state), "evidence_dir": str(evidence), "test_mode": True}

    config = _absolute(getattr(ns, "config", None))
    run_log = _absolute(getattr(ns, "run_log", None))
    expected_config = root / "config" / "line_backup_config.json"
    expected_run_log = root / "state" / "run_log.md"
    expected_state = root / "state" / "backup_state.json"
    if config != expected_config or run_log != expected_run_log or state != expected_state:
        raise AcceptanceError("INVALID_AUTHORITY", "production authority paths are not canonical", 2)
    cfg = _load_production_config(expected_config)
    _require_file(expected_state, "state")
    _require_file(expected_run_log, "run-log")

    # Preflight before locked_state() can create the control file. This is a
    # read-only authority check; every mutation path re-reads state under lock.
    try:
        raw_state = read_json(expected_state)
    except AcceptanceError as exc:
        raise AcceptanceError("INVALID_AUTHORITY", f"canonical state cannot be preflighted: {exc.message}", 2) from exc
    backup_root = Path(cfg["backup_root"])
    if not exact_real_path(backup_root) or not backup_root.is_dir():
        raise AcceptanceError("INVALID_AUTHORITY", "configured backup root is not a canonical directory", 2)
    destinations = []
    if getattr(ns, "destination", None):
        destinations.append(_absolute(ns.destination))
    for run in raw_state.get("runs", []) if isinstance(raw_state, dict) else []:
        if isinstance(run, dict) and isinstance(run.get("destination"), str):
            destinations.append(Path(run["destination"]))
    for destination in destinations:
        if destination is not None:
            try:
                validate_destination(destination, backup_root)
            except AcceptanceError as exc:
                raise AcceptanceError("INVALID_AUTHORITY", f"production destination authority rejected: {exc.message}", 2) from exc
    _validate_required_transaction_args(ns)
    return {"project_root": str(root), "config": str(expected_config), "run_log": str(expected_run_log),
            "state": str(expected_state), "evidence_dir": str(evidence), "test_mode": False,
            "config_value": cfg, "backup_root": str(backup_root)}


def validate_destination(destination: Path, backup_root: Path) -> None:
    if not exact_real_path(backup_root) or not exact_real_path(destination):
        raise AcceptanceError("INPUT_NEGATIVE", "backup root or destination is symlinked", 4)
    real_backup, real_dest = Path(os.path.realpath(backup_root)), Path(os.path.realpath(destination))
    if not within(real_dest, real_backup):
        raise AcceptanceError("INPUT_NEGATIVE", "destination is outside configured backup root", 4)
