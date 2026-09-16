from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .authority import validate_transaction
from .common import AcceptanceError, atomic_write_json, emit, find_run, fingerprint, json_bytes, locked_state, read_json, terminal, utc_now, wait_barrier


def _base_run(run_id, owner_id, group_key, fp, destination):
    calibration = {"observed_at": utc_now(), "screenshot_width": 1, "screenshot_height": 1, "ellipsis": [1, 1], "dot_spacing": 1.0, "save_all_point": [1, 1], "confidence": "HIGH", "evidence": "test-mode adapter calibration fixture; no GUI authorization"}
    intent = {"action_id": f"ACTION-{run_id}", "committed_at": utc_now(), "owner_execution_id": owner_id, "group_key": group_key, "fingerprint": fp, "destination": destination, "calibration": calibration, "intent_state": "INTENT_COMMITTED", "dispatch_state": "NOT_ATTEMPTED", "save_all_retry_allowed": False, "dispatch_outcome": "NOT_ATTEMPTED", "trigger_outcome": "NOT_APPLICABLE"}
    return {"run_id": run_id, "mode": "backup_one", "group_key": group_key, "album_id": None, "fingerprint": fp, "observed_title": group_key.rsplit(":", 1)[-1], "source_provenance": "test fixture", "title_confidence": "HIGH", "destination": destination, "destination_initially_empty": True, "workflow_outcome": None, "phase": "SAVE_ALL_INTENT_COMMITTED", "owner_id": owner_id, "contract_revision": "1.0-rc2", "intent_state": "INTENT_COMMITTED", "dispatch_state": "NOT_ATTEMPTED", "intent": intent, "dispatch_evidence": None, "verification": None, "runtime_errors": [], "events": [], "reconciliations": [], "checkpoint": {"phase": "SAVE_ALL_INTENT_COMMITTED", "at": utc_now(), "evidence": "intent committed with retry=false"}}


def _new_state():
    return {"schema_version": 2, "revision": 0, "current_run_id": None, "active_writer_id": None, "context_lock": None, "runs": [], "verified_albums": []}


def _validate_state(state):
    if not isinstance(state, dict) or state.get("schema_version") != 2 or not isinstance(state.get("revision"), int) or not isinstance(state.get("runs"), list) or not isinstance(state.get("verified_albums"), list):
        raise AcceptanceError("STATE_READ_ERROR", "state fixture is not schema v2", 1)


def _commit_payload(path: Path, state: dict, expected_revision: int, expected_run: str | None, expected_owner: str | None, *, fault=None, pause_at=None, barrier_file=None, terminal_release=False):
    _validate_state(state)
    if state.get("revision") != expected_revision:
        raise AcceptanceError("CONFLICT_STALE_REVISION", "expected revision does not match authoritative state", 4)
    if expected_run is not None and not terminal_release and state.get("current_run_id") != expected_run:
        raise AcceptanceError("CONFLICT_OWNER_RUN", "current run does not match", 4)
    if expected_owner is not None and not terminal_release and state.get("active_writer_id") != expected_owner:
        raise AcceptanceError("CONFLICT_OWNER_RUN", "active writer does not match", 4)
    if pause_at:
        wait_barrier(pause_at, barrier_file)
        # Re-read under the same lock immediately before replacement; a delayed payload cannot win.
        latest = read_json(path)
        if latest.get("revision") != expected_revision:
            raise AcceptanceError("CONFLICT_STALE_REVISION", "stale revision after barrier", 4)
    state["revision"] = expected_revision + 1
    meta = atomic_write_json(path, state, fault=fault)
    if fault == "READBACK_UNCERTAIN_AFTER_REPLACE":
        # The replacement is durable; the adapter deliberately reports that
        # its first read-back observation is uncertain. A fresh process must
        # reload rather than replay the prepared payload.
        read_json(path)
        raise AcceptanceError("READBACK_UNCERTAIN", "injected read-back uncertainty after replacement", 1)
    try:
        read_back = read_json(path)
    except Exception as exc:
        raise AcceptanceError("READBACK_UNCERTAIN", str(exc), 1) from exc
    if read_back.get("revision") != expected_revision + 1:
        raise AcceptanceError("READBACK_UNCERTAIN", "replacement read-back revision mismatch", 1)
    return meta


def _result(evidence: Path, code: str, message: str, exit_code: int, **extra):
    value = {"schema_version": 1, "result": code, "message": message, "exit_code": exit_code, **extra}
    evidence.mkdir(parents=True, exist_ok=True)
    atomic_write_json(evidence / "result.json", value)
    return value


def prepare(ns):
    auth = validate_transaction(ns)
    root, path, evidence = Path(auth["project_root"]), Path(auth["state"]), Path(auth["evidence_dir"])
    fp = fingerprint(ns.start_date, ns.end_date, ns.expected_images)
    if ns.pause_at == "ACQUIRE_BEFORE_LOCK":
        wait_barrier(ns.pause_at, ns.barrier_file)
    with locked_state(path):
        state = read_json(path)
        _validate_state(state)
        if state.get("current_run_id") is not None or state.get("active_writer_id") is not None or state.get("context_lock") is not None:
            return _result(evidence, "CONFLICT_ACTIVE_RUN", "an active run already owns the state", 4), 4
        run = _base_run(ns.run_id, ns.owner_id, ns.group_key, fp, str(Path(os.path.abspath(ns.destination))))
        state["runs"].append(run)
        state["current_run_id"] = ns.run_id
        state["active_writer_id"] = ns.owner_id
        _commit_payload(path, state, state["revision"], None, None, pause_at=ns.pause_at, barrier_file=ns.barrier_file)
    return _result(evidence, "PREPARED", "intent prepared", 0, revision=1, run_id=ns.run_id), 0


def _dispatch(ns):
    if not ns.dispatcher or not ns.dispatch_counter:
        raise AcceptanceError("INVALID_INPUT", "dispatcher and dispatch-counter are required", 2)
    cmd = [ns.dispatcher, "--counter", ns.dispatch_counter, "--outcome", ns.dispatcher_outcome]
    if ns.crash_after_dispatch:
        cmd.append("--crash-after-dispatch")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise AcceptanceError("DISPATCH_UNKNOWN", f"dispatcher could not start: {exc}", 1) from exc
    if p.returncode != 0:
        raise AcceptanceError("DISPATCHER_CRASH_AFTER_SIDE_EFFECT" if ns.crash_after_dispatch else "DISPATCH_UNKNOWN", p.stderr.strip() or "dispatcher failed", 1)
    if ns.dispatcher_outcome == "UNKNOWN":
        raise AcceptanceError("DISPATCH_UNKNOWN", "dispatcher returned unknown outcome", 1)
    return "RETURNED"


def resume(ns):
    auth = validate_transaction(ns)
    path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path); _validate_state(state)
        run = find_run(state, ns.run_id)
        if not run:
            return _result(evidence, "CONFLICT_OWNER_RUN", "run/owner is not authoritative", 4), 4
        if state.get("revision") != ns.expected_revision:
            return _result(evidence, "CONFLICT_STALE_REVISION", "revision is not authoritative", 4), 4
        if terminal(run):
            return _result(evidence, "SKIP_TERMINAL", "matching run is terminal", 0, revision=state["revision"], dispatch_performed=False), 0
        if state.get("current_run_id") != ns.run_id or state.get("active_writer_id") != ns.expected_owner_id:
            return _result(evidence, "CONFLICT_OWNER_RUN", "run/owner is not authoritative", 4), 4
        if ns.no_dispatch:
            return _result(evidence, "RECOVERY_NO_DISPATCH", "loaded intent is reconciled without dispatch", 0, revision=state["revision"], dispatch_performed=False), 0
        if run.get("intent_state") != "INTENT_COMMITTED":
            return _result(evidence, "RECOVERY_NO_DISPATCH", "dispatch barrier already committed", 0, revision=state["revision"], dispatch_performed=False), 0
        if not isinstance(run.get("intent"), dict) or run["intent"].get("save_all_retry_allowed") is not False:
            raise AcceptanceError("STATE_CONTRACT_ERROR", "committed intent must disable Save-All retry before dispatch", 1)
        if ns.crash_after_dispatch or ns.dispatcher_outcome == "UNKNOWN":
            run["intent_state"] = "TRIGGER_UNKNOWN"; run["dispatch_state"] = "UNKNOWN"
            run["intent"]["intent_state"] = "TRIGGER_UNKNOWN"; run["intent"]["dispatch_state"] = "UNKNOWN"
            run["intent"]["trigger_outcome"] = "UNKNOWN"; run["intent"]["dispatch_outcome"] = "UNKNOWN"
            run["dispatch_evidence"] = {"coordinate_invocation_attempted": None, "save_all_click_count": None, "outcome": "UNKNOWN"}
            _commit_payload(path, state, ns.expected_revision, ns.run_id, ns.expected_owner_id)
            try:
                _dispatch(ns)
            except AcceptanceError as exc:
                return _result(evidence, exc.code, exc.message, exc.exit_code, revision=ns.expected_revision + 1, dispatch_performed=True), exc.exit_code
        else:
            try:
                _dispatch(ns)
            except AcceptanceError as exc:
                return _result(evidence, exc.code, exc.message, exc.exit_code, revision=state["revision"], dispatch_performed=True), exc.exit_code
            run["intent_state"] = "SAVE_ALL_DISPATCH_ATTEMPTED"; run["dispatch_state"] = "SAVE_ALL_RETURNED"
            run["intent"]["intent_state"] = "SAVE_ALL_DISPATCH_ATTEMPTED"; run["intent"]["dispatch_state"] = "SAVE_ALL_RETURNED"
            run["intent"]["dispatch_outcome"] = "RETURNED"; run["intent"]["trigger_outcome"] = "UNKNOWN"
            run["dispatch_evidence"] = {"coordinate_invocation_attempted": True, "save_all_click_count": 1, "outcome": "RETURNED"}
            _commit_payload(path, state, ns.expected_revision, ns.run_id, ns.expected_owner_id)
    return _result(evidence, "DISPATCH_RETURNED", "dispatcher returned; trigger remains independently unconfirmed", 0, revision=ns.expected_revision + 1, dispatch_performed=True), 0


def commit(ns):
    auth = validate_transaction(ns); path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path); _validate_state(state)
        run = find_run(state, ns.run_id)
        if not run or state.get("current_run_id") != ns.run_id or state.get("active_writer_id") != ns.expected_owner_id:
            return _result(evidence, "CONFLICT_OWNER_RUN", "run/owner is not authoritative", 4), 4
        if state.get("revision") != ns.expected_revision:
            return _result(evidence, "CONFLICT_STALE_REVISION", "revision is not authoritative", 4), 4
        verification = read_json(Path(ns.verification_json))
        run["verification"] = verification; run["phase"] = "VERIFYING"; run["checkpoint"] = {"phase": "VERIFYING", "at": utc_now(), "evidence": "verification committed"}
        _commit_payload(path, state, ns.expected_revision, ns.run_id, ns.expected_owner_id, pause_at=ns.pause_at, barrier_file=ns.barrier_file, fault=ns.storage_fault)
    return _result(evidence, "COMMITTED_VERIFICATION", "verification committed", 0, revision=ns.expected_revision + 1), 0


def finalize(ns):
    auth = validate_transaction(ns); path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path); _validate_state(state)
        run = find_run(state, ns.run_id)
        if not run or state.get("current_run_id") != ns.run_id or state.get("active_writer_id") != ns.expected_owner_id:
            return _result(evidence, "CONFLICT_OWNER_RUN", "run/owner is not authoritative", 4), 4
        if state.get("revision") != ns.expected_revision:
            return _result(evidence, "CONFLICT_STALE_REVISION", "revision is not authoritative", 4), 4
        verification = read_json(Path(ns.verification_json))
        run["verification"] = verification
        run["workflow_outcome"] = ns.outcome; run["phase"] = ns.outcome; run["checkpoint"] = {"phase": ns.outcome, "at": utc_now(), "evidence": "terminal finalization"}
        if ns.outcome == "VERIFIED":
            state["verified_albums"].append({"group_key": run["group_key"], "fingerprint": run["fingerprint"], "verified_run_id": ns.run_id, "destinations": [run["destination"]], "source_kind": "filesystem_verification", "evidence": "terminal finalization"})
        state["current_run_id"] = None; state["active_writer_id"] = None; state["context_lock"] = None
        try:
            _commit_payload(path, state, ns.expected_revision, ns.run_id, ns.expected_owner_id, fault=ns.storage_fault, terminal_release=True)
        except AcceptanceError as exc:
            if exc.code == "READBACK_UNCERTAIN":
                return _result(evidence, "READBACK_UNCERTAIN", exc.message, 1, revision=ns.expected_revision + 1, terminal_committed=True), 1
            raise
    return _result(evidence, "FINALIZED", "terminal outcome committed", 0, revision=ns.expected_revision + 1, outcome=ns.outcome), 0


def duplicate_check(ns):
    auth = validate_transaction(ns); path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path); _validate_state(state)
        fp = fingerprint(ns.start_date, ns.end_date, ns.expected_images)
        found = [x for x in state.get("verified_albums", []) if x.get("group_key") == ns.group_key and x.get("fingerprint") == fp and str(Path(ns.destination)) in (x.get("destinations") or [])]
        if len(found) == 1:
            return _result(evidence, "SKIP_DUPLICATE", "exact terminal registry association exists", 0, replacement=False, dispatch_performed=False), 0
        if len(found) > 1:
            return _result(evidence, "CONFLICT_DUPLICATE", "ambiguous terminal registry association", 4), 4
    return _result(evidence, "NOT_DUPLICATE", "no exact terminal registry association", 0, replacement=False, dispatch_performed=False), 0
