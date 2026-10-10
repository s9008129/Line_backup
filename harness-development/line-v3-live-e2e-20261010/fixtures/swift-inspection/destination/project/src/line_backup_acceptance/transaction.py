from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .authority import validate_transaction
from .common import (AcceptanceError, atomic_write_json, _check_calibration, find_run, fingerprint, json_bytes,
                     locked_state, parse_binding_reference, read_json, resolve_binding_artifact,
                     sha256_bytes, sha256_and_bytes, terminal, utc_now, validate_result_chain,
                     validate_state_strict, wait_barrier, within, WORK_ROOT)

SOURCE_EVIDENCE_KEYS = {"record_version", "test_mode", "app_identifier", "group_key", "observed_title",
                        "title_confidence", "fingerprint", "observed_at", "calibration", "binding",
                        "evidence_artifacts"}
TITLE_CONFIDENCES = {"HIGH", "LOW", "UNKNOWN"}


def _utc() -> str:
    return utc_now()


# ---------------------------------------------------------------------------
# Result artifacts and guarded replacement
# ---------------------------------------------------------------------------

def _result(evidence: Path, code: str, message: str, exit_code: int, **extra) -> dict:
    value = {"schema_version": 1, "result": code, "message": message, "exit_code": exit_code, **extra}
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    atomic_write_json(evidence / "result.json", value)
    return value


def _replace(path: Path, state: dict, expected_revision: int, *, fault: str | None = None) -> dict:
    """Guarded compare-and-commit replacement: strict payload validation -> durable write -> read-back."""
    validate_state_strict(state)
    if state.get("revision") != expected_revision + 1:
        raise AcceptanceError("INTERNAL_ERROR", "replacement payload revision is not expected+1", 1)
    try:
        meta = atomic_write_json(path, state, fault=fault)
    except AcceptanceError as exc:
        if exc.code == "WRITE_BEFORE_REPLACE":
            raise
        raise
    if fault == "READBACK_UNCERTAIN_AFTER_REPLACE":
        raise AcceptanceError("READBACK_UNCERTAIN", "injected read-back uncertainty after replacement", 1)
    try:
        read_back = read_json(path)
    except Exception as exc:
        raise AcceptanceError("READBACK_UNCERTAIN", str(exc), 1) from exc
    try:
        validate_state_strict(read_back)
    except AcceptanceError as exc:
        raise AcceptanceError("READBACK_UNCERTAIN", f"replacement read-back invalid: {exc.message}", 1) from exc
    if read_back.get("revision") != expected_revision + 1:
        raise AcceptanceError("READBACK_UNCERTAIN", "replacement read-back revision mismatch", 1)
    return meta


# ---------------------------------------------------------------------------
# Source-evidence record (Rev15 §15.3)
# ---------------------------------------------------------------------------

def _load_source_evidence(ns, fp: dict) -> dict:
    raw_path = getattr(ns, "source_evidence", None)
    if not raw_path:
        raise AcceptanceError("MISSING_SOURCE_EVIDENCE", "--source-evidence is required for prepare", 2)
    path = Path(raw_path)
    if not path.is_file():
        raise AcceptanceError("MISSING_SOURCE_EVIDENCE", "source-evidence record is missing or unreadable", 2)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", f"source-evidence record is unparseable: {exc}", 2) from exc
    if not isinstance(record, dict) or set(record) != SOURCE_EVIDENCE_KEYS:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "source-evidence record keys do not match the schema", 2)
    if record.get("record_version") != 1:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "record_version must be 1", 2)
    if record.get("test_mode") is not bool(ns.test_mode):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "test_mode mismatch between record and invocation", 2)
    if record.get("app_identifier") != "jp.naver.line.mac":
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "app_identifier mismatch", 2)
    if record.get("group_key") != ns.group_key:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "record group_key does not equal the argv group key", 2)
    if record.get("fingerprint") != fp:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "record fingerprint does not equal the argv fingerprint", 2)
    if not isinstance(record.get("observed_title"), str) or not record["observed_title"]:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "observed_title is missing", 2)
    if record.get("title_confidence") not in TITLE_CONFIDENCES:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "title_confidence is invalid", 2)
    if not isinstance(record.get("observed_at"), str) or not record["observed_at"]:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "observed_at is missing", 2)
    try:
        _check_calibration(record.get("calibration"))
    except AcceptanceError as exc:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", f"calibration is not schema-shaped: {exc.message}", 2) from exc
    binding = record.get("binding")
    if not isinstance(binding, dict) or set(binding) != {"kind", "artifact"}:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding is not a kind+artifact object", 2)
    kind = binding.get("kind")
    artifact = binding.get("artifact")
    if kind not in {"join", "user_fact", "fixture"}:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding kind is not a source binding", 2)
    if ns.test_mode and kind == "join":
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "join binding is production-only", 2)
    if not ns.test_mode and kind == "fixture":
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "fixture binding is unverifiable in production", 2)
    if not isinstance(artifact, dict) or set(artifact) != {"path", "bytes", "sha256"}:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding.artifact shape is invalid", 2)
    artifacts = record.get("evidence_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "evidence_artifacts is empty", 2)
    if not any(isinstance(e, dict) and set(e) == {"path", "bytes", "sha256"} and e["path"] == artifact["path"]
               and e["bytes"] == artifact["bytes"] and e["sha256"] == artifact["sha256"] for e in artifacts):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding.artifact is not an evidence_artifacts entry", 2)
    base = Path(ns.project_root) if kind in {"fixture", "user_fact"} and ns.test_mode else WORK_ROOT
    relpath = _normalize_binding_relpath(artifact, base, kind=kind, ns=ns)
    resolved = resolve_binding_artifact(kind, relpath, project_root=Path(ns.project_root),
                                        test_mode=ns.test_mode, state_path=Path(ns.state),
                                        evidence_dir=Path(ns.evidence_dir))
    if not resolved.is_file():
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding artifact is missing or unreadable", 2)
    data = resolved.read_bytes()
    if len(data) != artifact["bytes"] or sha256_bytes(data) != artifact["sha256"]:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding artifact bytes/sha256 do not match the record", 2)
    return {"record": record, "kind": kind, "relpath": relpath, "sha256": artifact["sha256"],
            "reference": f"{kind}:{relpath}:{artifact['sha256']}"}


def _normalize_binding_relpath(artifact: dict, base: Path, *, kind: str, ns) -> str:
    value = artifact.get("path")
    if not isinstance(value, str) or not value:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding.artifact.path is missing", 2)
    base_real = Path(os.path.realpath(base))
    raw = Path(value)
    if raw.is_absolute():
        real = Path(os.path.realpath(raw))
        if not within(real, base_real):
            raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding artifact is outside its base", 2)
        relpath = str(real.relative_to(base_real))
    else:
        relpath = value
    if not relpath or relpath.startswith("/") or any(part in {"", ".", ".."} for part in relpath.split("/")):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding relpath is not a normal relative path", 2)
    current = base_real
    for part in relpath.split("/"):
        current = current / part
        if current.is_symlink():
            raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding path passes through a symlink", 2)
    if not within(Path(os.path.realpath(base_real / relpath)), base_real):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding path escapes its base", 2)
    return relpath


# ---------------------------------------------------------------------------
# Run record and shared precondition evaluator
# ---------------------------------------------------------------------------

def _base_run(run_id, owner_id, group_key, fp, destination, calibration, observed_title, title_confidence, reference):
    at = _utc()
    checkpoint = {"phase": "SAVE_ALL_INTENT_COMMITTED", "at": at, "evidence": "intent committed with retry=false"}
    intent = {"action_id": f"ACTION-{run_id}", "committed_at": at, "owner_execution_id": owner_id,
              "group_key": group_key, "fingerprint": fp, "destination": destination,
              "calibration": calibration, "save_all_retry_allowed": False,
              "dispatch_outcome": "NOT_ATTEMPTED", "trigger_outcome": "NOT_APPLICABLE"}
    events = [{"phase": "SAVE_ALL_INTENT_COMMITTED", "at": at, "evidence": reference}]
    return {"run_id": run_id, "mode": "backup_one", "group_key": group_key, "album_id": None,
            "fingerprint": fp, "observed_title": observed_title, "title_confidence": title_confidence,
            "destination": destination, "destination_initially_empty": True,
            "workflow_outcome": "IN_PROGRESS", "phase": "SAVE_ALL_INTENT_COMMITTED",
            "contract_revision": "1.0-rc2", "intent_state": "INTENT_COMMITTED",
            "dispatch_state": "NOT_ATTEMPTED", "intent": intent, "dispatch_evidence": None,
            "verification": None, "runtime_errors": [], "events": events, "reconciliations": [],
            "checkpoint": checkpoint, "manual_reconciliation_required": False,
            "reconciliation_reason": None, "recovery_used": {}, "stop_reason": None, "batch_id": None}


def _same_fp(candidate, fp: dict) -> bool:
    return isinstance(candidate, dict) and all(candidate.get(k) == v for k, v in fp.items())


def _fingerprint_released(runs: list[dict], group_key: str, fp: dict) -> bool:
    for run in runs:
        if run.get("group_key") != group_key or not _same_fp(run.get("fingerprint"), fp):
            continue
        for rec in run.get("reconciliations") or []:
            if (isinstance(rec, dict) and rec.get("outcome") == "ABORTED_BEFORE_SAVE_ALL_DISPATCH"
                    and rec.get("blocking_intent_released") is True and isinstance(rec.get("proof"), dict)):
                return True
    return False


def _evaluate_preconditions(state: dict, group_key: str, fp: dict, destination: str, *, duplicate_check: bool):
    """Shared evaluator for duplicate-check and prepare (F2).  Returns (code, exit) or None."""
    runs = [r for r in state.get("runs", []) if isinstance(r, dict)]
    entries = [e for e in state.get("verified_albums", []) if isinstance(e, dict)]
    if not duplicate_check:
        if state.get("current_run_id") is not None or state.get("active_writer_id") is not None or state.get("context_lock") is not None:
            return "CONFLICT_ACTIVE_RUN", 4
    exact_entries = [e for e in entries if e.get("group_key") == group_key and _same_fp(e.get("fingerprint"), fp)
                     and destination in (e.get("destinations") or [])]
    exact_runs = [r for r in runs if r.get("group_key") == group_key and _same_fp(r.get("fingerprint"), fp)
                  and r.get("destination") == destination and r.get("workflow_outcome") == "VERIFIED"]
    # One association, one unit: a VERIFIED run already linked by an exact registry entry is the
    # same association as that entry and must not be counted twice (case-01 closed-loop oracle).
    exact_linked = {e.get("verified_run_id") for e in exact_entries}
    exact = len(exact_entries) + len([r for r in exact_runs if r.get("run_id") not in exact_linked])
    if exact > 1:
        return "CONFLICT_DUPLICATE", 4
    if exact == 1:
        return ("SKIP_DUPLICATE", 0) if duplicate_check else ("CONFLICT_DUPLICATE", 4)
    released = _fingerprint_released(runs, group_key, fp)
    other_dest_entries = [e for e in entries if e.get("group_key") == group_key and _same_fp(e.get("fingerprint"), fp)
                          and destination not in (e.get("destinations") or [])]
    other_dest_runs = [r for r in runs if r.get("group_key") == group_key and _same_fp(r.get("fingerprint"), fp)
                       and r.get("destination") != destination and r.get("workflow_outcome") == "VERIFIED"]
    if (other_dest_entries or other_dest_runs) and not released:
        return "CONFLICT_DUPLICATE_FINGERPRINT", 4
    ambiguous = [r for r in runs if r.get("group_key") == group_key and isinstance(r.get("fingerprint"), dict)
                 and r["fingerprint"].get("start_date") == fp["start_date"]
                 and r["fingerprint"].get("end_date") == fp["end_date"]
                 and r["fingerprint"].get("expected_images") != fp["expected_images"]]
    ambiguous += [e for e in entries if e.get("group_key") == group_key and isinstance(e.get("fingerprint"), dict)
                  and e["fingerprint"].get("start_date") == fp["start_date"]
                  and e["fingerprint"].get("end_date") == fp["end_date"]
                  and e["fingerprint"].get("expected_images") != fp["expected_images"]]
    if ambiguous:
        return "AMBIGUOUS_FINGERPRINT", 4
    for run in runs:
        if run.get("group_key") != group_key or not _same_fp(run.get("fingerprint"), fp):
            continue
        outcome = run.get("workflow_outcome")
        if outcome not in {"VERIFIED", "SAFE_ABORT", "FAILED"}:
            if not released:
                return "NEEDS_RECONCILIATION", 4
        elif outcome == "SAFE_ABORT":
            intent_state = run.get("intent_state")
            dispatch_state = run.get("dispatch_state")
            # Legacy records never carry an affirmative non-dispatch proof, so a missing
            # dispatch axis is conservatively unresolved, never NOT_ATTEMPTED (Rev17 §17.3).
            unresolved = (intent_state in {"SAVE_ALL_DISPATCH_ATTEMPTED", "TRIGGER_UNKNOWN"}
                          or dispatch_state in {"UNKNOWN", "SAVE_ALL_ATTEMPTED"}
                          or intent_state is None or dispatch_state is None
                          or run.get("workflow_outcome") == "SAFE_ABORT" and run.get("manual_reconciliation_required") is True)
            if unresolved and not released:
                return "NEEDS_RECONCILIATION", 4
    return None


# ---------------------------------------------------------------------------
# Dispatch adapter (the single in-process dispatch window)
# ---------------------------------------------------------------------------

def _dispatch(ns) -> dict:
    argv = ["/usr/bin/python3", str(ns.dispatcher), "--counter", str(ns.dispatch_counter)]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=300)
        return {"argv": argv, "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}
    except subprocess.TimeoutExpired as exc:
        return {"argv": argv, "returncode": -1000,
                "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                "stderr": "adapter timeout", "timeout": True}


def _dispatch_evidence(run: dict, observed: dict, run_id: str, owner: str) -> dict:
    return {"run_id": run_id, "action_id": f"ACTION-{run_id}", "execution_id": owner, "observed_at": _utc(),
            "save_all_click_count": 1, "save_all_invocation_attempted": True, "failure_boundary": "NONE",
            "folder_chooser_appeared": False, "download_started": False,
            "provenance": f"external dispatcher adapter {Path(str(observed['argv'][1])).name} (test-mode side-effect fake)"}


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def prepare(ns):
    auth = validate_transaction(ns)
    root, path, evidence = Path(auth["project_root"]), Path(auth["state"]), Path(auth["evidence_dir"])
    fp = fingerprint(ns.start_date, ns.end_date, ns.expected_images)
    # Deterministic prepare refusal precedence (Rev16 §16.6): authority validation ->
    # MISSING_SOURCE_EVIDENCE -> MISSING_DISPATCHER -> INVALID_SOURCE_EVIDENCE ->
    # precondition refusals -> PREPARED.  Record load precedes adapter-flag evaluation only
    # for the presence check; the record's content is validated after the adapter pair.
    raw_source = getattr(ns, "source_evidence", None)
    if not raw_source or not Path(raw_source).is_file():
        return _result(evidence, "MISSING_SOURCE_EVIDENCE", "--source-evidence is required for prepare", 2), 2
    if not getattr(ns, "dispatcher", None) or not getattr(ns, "dispatch_counter", None):
        return _result(evidence, "MISSING_DISPATCHER", "prepare requires the --dispatcher/--dispatch-counter pair", 2), 2
    loaded = _load_source_evidence(ns, fp)
    if ns.pause_at == "ACQUIRE_BEFORE_LOCK":
        wait_barrier(ns.pause_at, ns.barrier_file)
    with locked_state(path):
        state = read_json(path)
        try:
            validate_state_strict(state)
        except AcceptanceError as exc:
            return _result(evidence, "INVALID_STATE_LEGACY", exc.message, 4, revision=state.get("revision"), state_replaced=False), 4
        refusal = _evaluate_preconditions(state, ns.group_key, fp, ns.destination, duplicate_check=False)
        if refusal:
            code, exit_code = refusal
            return _result(evidence, code, "prepare precondition refused", exit_code,
                           revision=state.get("revision"), state_replaced=False, dispatch_performed=False), exit_code
        run = _base_run(ns.run_id, ns.owner_id, ns.group_key, fp, ns.destination,
                        loaded["record"]["calibration"], loaded["record"]["observed_title"],
                        loaded["record"]["title_confidence"], loaded["reference"])
        state["runs"].append(run)
        state["current_run_id"] = ns.run_id
        state["active_writer_id"] = ns.owner_id
        state["revision"] = state["revision"] + 1
        expected_revision = state["revision"] - 1
        intent_fault = ns.storage_fault if getattr(ns, "storage_fault_slot", None) == "intent" else None
        try:
            _replace(path, state, expected_revision, fault=intent_fault)
        except AcceptanceError as exc:
            if exc.code == "READBACK_UNCERTAIN":
                # The intent replacement was committed; only this process's read-back is
                # uncertain, and the dispatch window is not entered (Rev16 §16.7 23b).
                return _result(evidence, "READBACK_UNCERTAIN", exc.message, 1, revision=state["revision"],
                               state_replaced=True, dispatch_performed=False), 1
            return _result(evidence, exc.code, exc.message, exc.exit_code, revision=expected_revision,
                           state_replaced=False, dispatch_performed=False), exc.exit_code
        if ns.dispatcher_outcome == "UNKNOWN":
            # Rev15 §15.1 row 4 / Rev16 §16.6: the ambiguity barrier is committed (revision
            # 1->2 with the row-4 fields) *before* the adapter is invoked, so a crash in the
            # dispatch window leaves exactly this barrier on disk.
            _commit_barrier(run, state, expected_revision + 1)
            _replace(path, state, expected_revision + 1)
            observed = _dispatch(ns)
            return _result(evidence, "DISPATCH_UNKNOWN", "pre-dispatch ambiguity barrier committed; adapter invoked once",
                           1, revision=state["revision"], dispatch_performed=True, state_replaced=True), 1
        observed = _dispatch(ns)
        if ns.crash_after_dispatch or observed["returncode"] != 0:
            return _result(evidence, "DISPATCHER_CRASH_AFTER_SIDE_EFFECT",
                           "dispatcher died after its side effect; state stays at the committed intent revision",
                           1, revision=state["revision"], dispatch_performed=True, state_replaced=True), 1
        run["intent_state"] = "SAVE_ALL_DISPATCH_ATTEMPTED"
        run["dispatch_state"] = "SAVE_ALL_RETURNED"
        run["phase"] = "SAVE_ALL_DISPATCH_ATTEMPTED"
        run["intent"]["dispatch_outcome"] = "RETURNED"
        run["intent"]["trigger_outcome"] = "UNKNOWN"
        run["dispatch_evidence"] = _dispatch_evidence(run, observed, ns.run_id, ns.owner_id)
        run["events"].append({"phase": "SAVE_ALL_DISPATCH_ATTEMPTED", "at": _utc(),
                              "evidence": "adapter returned; trigger independently unconfirmed"})
        run["checkpoint"] = {"phase": "SAVE_ALL_DISPATCH_ATTEMPTED", "at": _utc(),
                             "evidence": "post-dispatch record committed"}
        dispatch_fault = ns.storage_fault if getattr(ns, "storage_fault_slot", None) == "dispatch" else None
        state["revision"] = expected_revision + 2
        try:
            _replace(path, state, expected_revision + 1, fault=dispatch_fault)
        except AcceptanceError as exc:
            if exc.code == "WRITE_BEFORE_REPLACE":
                return _result(evidence, exc.code, exc.message, exc.exit_code, revision=state["revision"] - 1,
                               state_replaced=False, dispatch_performed=True), exc.exit_code
            return _result(evidence, exc.code, exc.message, exc.exit_code, revision=state["revision"],
                           state_replaced=True, dispatch_performed=True), exc.exit_code
        return _result(evidence, "PREPARED", "intent committed and exactly one dispatch performed",
                       0, revision=state["revision"], dispatch_performed=True, state_replaced=True), 0


def _commit_barrier(run: dict, state: dict, expected_revision: int) -> None:
    """Persist the ambiguity barrier (row-4 fields of the Rev15 §15.1 resume table)."""
    run["intent_state"] = "TRIGGER_UNKNOWN"
    run["dispatch_state"] = "UNKNOWN"
    run["intent"]["trigger_outcome"] = "UNKNOWN"
    run["intent"]["dispatch_outcome"] = "UNKNOWN"
    run["intent"]["save_all_retry_allowed"] = False
    run["manual_reconciliation_required"] = True
    run["reconciliation_reason"] = "dispatch outcome unresolved; reconciliation required"
    run["events"].append({"phase": "TRIGGER_UNKNOWN", "at": _utc(),
                          "evidence": "ambiguity barrier committed without a second dispatch"})
    run["checkpoint"] = {"phase": "TRIGGER_UNKNOWN", "at": _utc(), "evidence": "ambiguity barrier committed"}
    state["revision"] = expected_revision + 1


# ---------------------------------------------------------------------------
# resume (reconciliation-only; never dispatches)
# ---------------------------------------------------------------------------

def resume(ns):
    auth = validate_transaction(ns)
    evidence = Path(auth["evidence_dir"])
    if (getattr(ns, "dispatcher", None) or getattr(ns, "dispatch_counter", None)
            or getattr(ns, "crash_after_dispatch", False)
            or (getattr(ns, "dispatcher_outcome", "RETURNED") not in (None, "RETURNED"))):
        return _result(evidence, "INVALID_INPUT", "resume never dispatches; adapter options are not accepted", 2), 2
    path = Path(auth["state"])
    with locked_state(path):
        state = read_json(path)
        try:
            validate_state_strict(state)
        except AcceptanceError as exc:
            return _result(evidence, "INVALID_STATE_LEGACY", exc.message, 4, revision=state.get("revision"), state_replaced=False), 4
        run = find_run(state, ns.run_id)
        if run is None:
            return _result(evidence, "CONFLICT_OWNER_RUN", "run id is not present in state", 4,
                           state_replaced=False, dispatch_performed=False, reconciliation_state="NONE"), 4
        if terminal(run):
            if ns.expected_revision is not None and state.get("revision") != ns.expected_revision:
                return _result(evidence, "CONFLICT_STALE_REVISION", "terminal run at a different revision", 4,
                               state_replaced=False, dispatch_performed=False, reconciliation_state="NONE"), 4
            return _result(evidence, "SKIP_TERMINAL", "run is terminal; nothing to resume", 0,
                           state_replaced=False, dispatch_performed=False, reconciliation_state="NONE"), 0
        if ns.expected_revision is not None and state.get("revision") != ns.expected_revision:
            return _result(evidence, "CONFLICT_STALE_REVISION", "expected revision does not match authoritative state", 4,
                           state_replaced=False, dispatch_performed=False, reconciliation_state="NONE"), 4
        intent = run.get("intent") or {}
        never_dispatched = (run.get("intent_state") == "INTENT_COMMITTED" and run.get("dispatch_state") == "NOT_ATTEMPTED"
                            and intent.get("dispatch_outcome") == "NOT_ATTEMPTED")
        if never_dispatched and not run.get("manual_reconciliation_required"):
            expected_revision = state.get("revision")
            _commit_barrier(run, state, expected_revision)
            record = _reconcile_record(run, state, evidence)
            run["reconciliations"].append(record["entry"])
            run["events"].append({"phase": "TRIGGER_UNKNOWN", "at": _utc(),
                                  "evidence": record["entry"]["evidence"]})
            _replace(path, state, expected_revision)
            if state.get("_reconcile_reference"):
                pass
            return _result(evidence, "RECOVERY_NO_DISPATCH", "ambiguity barrier committed; no dispatch performed", 0,
                           revision=state["revision"], state_replaced=True, dispatch_performed=False,
                           reconciliation_state="BARRIER_COMMITTED"), 0
        return _result(evidence, "RECOVERY_NO_DISPATCH", "run already carries the barrier or a completed dispatch record", 0,
                       revision=state.get("revision"), state_replaced=False, dispatch_performed=False,
                       reconciliation_state="ALREADY_RECONCILED"), 0


def _reconcile_record(run: dict, state: dict, evidence: Path) -> dict:
    """Write the reconciliation artifact and the schema-valid reconciliations[] entry."""
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        name = "reconcile.json" if index == 1 else f"reconcile-{index}.json"
        if not (evidence / name).exists():
            break
        index += 1
    payload = {"schema_version": 1, "kind": "reconciliation_evidence",
               "run_id": run["run_id"], "action_id": run["intent"]["action_id"],
               "loaded_revision": state.get("revision"),
               "observation": "loaded intent never dispatched; ambiguity barrier committed without a second dispatch"}
    meta = atomic_write_json(evidence / name, payload)
    digest = meta["sha256"]
    entry = {"reconciliation_id": f"RECON-{run['run_id']}-{index}",
             "recorded_at": _utc(), "run_id": run["run_id"], "action_id": run["intent"]["action_id"],
             "execution_id": run["intent"]["owner_execution_id"], "outcome": "EVIDENCE_RECONCILED",
             "trigger_outcome": "UNKNOWN", "blocking_intent_released": False,
             "manual_reconciliation_required": True,
             "original_observation": {"reference": f"intent-checkpoint:{run['run_id']}:rev{state.get('revision')}",
                                      "trigger_outcome": "UNKNOWN"},
             "proof": None, "evidence": f"reconcile:{name}:{digest}"}
    return {"entry": entry, "name": name, "sha256": digest}


# ---------------------------------------------------------------------------
# commit / finalize / duplicate-check
# ---------------------------------------------------------------------------

def _verification_block(result: dict, verification_json: Path) -> dict:
    fs = result.get("filesystem") or {}
    entries = [e for e in fs.get("entries", []) if isinstance(e, dict)]
    regular = [e for e in entries if e.get("type") == "regular"]
    inventory = [{"relative_path": str(e.get("relative_path", "")), "size": int(e.get("size", 0)),
                  "mtime": str(e.get("mtime_ns", "")), "mime": str(e.get("mime") or "application/octet-stream")}
                 for e in regular]
    extensions: dict[str, int] = {}
    for entry in regular:
        name = Path(str(entry.get("relative_path", ""))).name
        suffix = name.rsplit(".", 1)[1].lower() if "." in name else ""
        extensions[suffix] = extensions.get(suffix, 0) + 1
    status = result.get("filesystem_status")
    outcome = "PASS" if status == "PASS" else ("FAIL" if status in {"FAIL"} else "INCOMPLETE_OR_STILL_DOWNLOADING")
    return {"observed_at": str(fs.get("observed_at") or _utc()), "outcome": outcome,
            "regular_files": len(regular),
            "image_files": int(result.get("recognized_images") or 0),
            "subdirectories": sum(e.get("type") == "directory" for e in entries),
            "total_bytes": int(fs.get("total_bytes") or 0),
            "extensions": extensions,
            "metadata_files": [str(e.get("relative_path")) for e in entries if e.get("status") == "HIDDEN"],
            "zero_byte_files": sum(e.get("status") == "ZERO_BYTE" for e in regular),
            "partial_temp_files": sum(e.get("status") == "SUFFIX" for e in regular),
            "unrecognized_files": sum(e.get("status") in {"UNRECOGNIZED", "DECODE_ERROR", "UNSUPPORTED"} for e in regular),
            "other_entries": [str(e.get("relative_path")) for e in entries if e.get("type") not in {"regular"}],
            "stable_samples": int(fs.get("stable_samples", 3) or 3), "inventory": inventory,
            "evidence": f"product verifier result consumed from {verification_json}"}


def _consume_verification(ns, run: dict) -> dict:
    """Recompute the §17.2 evidence chain and apply the F3 gates."""
    path = Path(ns.verification_json or "")
    if not ns.verification_json:
        raise AcceptanceError("INVALID_INPUT", "--verification-json is required", 2)
    result = validate_result_chain(path)
    if result.get("mode") != "verify_only" or result.get("filesystem_status") != "PASS":
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "verification result is not a passing verify_only result", 4)
    if result.get("run_id") != run.get("run_id"):
        raise AcceptanceError("VERIFICATION_RUN_MISMATCH", "verification run_id does not belong to this run", 4)
    if (result.get("group_key") != run.get("group_key") or result.get("fingerprint") != run.get("fingerprint")
            or result.get("destination") != run.get("destination")):
        raise AcceptanceError("VERIFICATION_RUN_MISMATCH", "verification identity does not match the run", 4)
    expected_count = (run.get("fingerprint") or {}).get("expected_images")
    if result.get("recognized_images") != expected_count:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "recognized_images does not equal the expected count", 4)
    return result


def _owner_gate(state: dict, run: dict | None, ns) -> str | None:
    if not run or state.get("current_run_id") != ns.run_id or state.get("active_writer_id") != ns.expected_owner_id:
        return "CONFLICT_OWNER_RUN"
    if ns.expected_revision is not None and state.get("revision") != ns.expected_revision:
        return "CONFLICT_STALE_REVISION"
    return None


def _dispatch_complete(run: dict) -> bool:
    """Return True only for the single schema-valid completed Save All dispatch shape."""
    intent = run.get("intent") or {}
    evidence_block = run.get("dispatch_evidence") or {}
    return (run.get("intent_state") == "SAVE_ALL_DISPATCH_ATTEMPTED"
            and run.get("dispatch_state") == "SAVE_ALL_RETURNED"
            and run.get("manual_reconciliation_required") is False
            and intent.get("dispatch_outcome") == "RETURNED"
            and evidence_block.get("save_all_click_count") == 1
            and evidence_block.get("save_all_invocation_attempted") is True
            and evidence_block.get("failure_boundary") == "NONE")


def commit(ns):
    auth = validate_transaction(ns)
    path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path)
        try:
            validate_state_strict(state)
        except AcceptanceError as exc:
            return _result(evidence, "INVALID_STATE_LEGACY", exc.message, 4, revision=state.get("revision"), state_replaced=False), 4
        run = find_run(state, ns.run_id)
        conflict = _owner_gate(state, run, ns)
        if conflict:
            return _result(evidence, conflict, "run/owner/revision is not authoritative", 4,
                           replacement=False, state_replaced=False), 4
        if not _dispatch_complete(run):
            return _result(evidence, "CONFLICT_UNRESOLVED_DISPATCH", "no completed successful dispatch record; commit is refused", 4,
                           replacement=False, state_replaced=False), 4
        try:
            verification = _consume_verification(ns, run)
        except AcceptanceError as exc:
            return _result(evidence, exc.code, exc.message, exc.exit_code, replacement=False, state_replaced=False), exc.exit_code
        expected_revision = state.get("revision")
        run["verification"] = _verification_block(verification, Path(ns.verification_json))
        run["phase"] = "VERIFYING"
        run["checkpoint"] = {"phase": "VERIFYING", "at": _utc(), "evidence": "verification committed"}
        run["events"].append({"phase": "VERIFYING", "at": _utc(), "evidence": f"verification committed from {ns.verification_json}"})
        state["revision"] = expected_revision + 1
        if ns.test_mode and ns.pause_at == "COMMIT_BEFORE_REPLACE":
            # Case 05: the deterministic race barrier sits inside the lock immediately before
            # the guarded replacement; a competing commit either wins the lock first or, after
            # the winner commits, observes the stale revision here (Rev16 case protocol).
            wait_barrier(ns.pause_at, ns.barrier_file)
            latest = read_json(path)
            if latest.get("revision") != expected_revision:
                return _result(evidence, "CONFLICT_STALE_REVISION",
                               "authoritative revision changed while paused before replacement", 4,
                               replacement=False, state_replaced=False), 4
        try:
            _replace(path, state, expected_revision, fault=ns.storage_fault)
        except AcceptanceError as exc:
            return _result(evidence, exc.code, exc.message, exc.exit_code, revision=state["revision"] - 1,
                           replacement=False, state_replaced=False), exc.exit_code
        return _result(evidence, "COMMITTED_VERIFICATION", "verification committed", 0,
                       revision=state["revision"], replacement=True, state_replaced=True), 0


def finalize(ns):
    auth = validate_transaction(ns)
    path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    if ns.outcome == "VERIFIED" and not ns.verification_json:
        return _result(evidence, "INVALID_INPUT", "--verification-json is required for --outcome VERIFIED", 2), 2
    if ns.outcome == "SAFE_ABORT" and ns.verification_json:
        try:
            value = json.loads(Path(ns.verification_json).read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("not a JSON object")
        except Exception as exc:
            return _result(evidence, "INVALID_INPUT", f"SAFE_ABORT verification JSON must be a readable object: {exc}", 2), 2
    with locked_state(path):
        state = read_json(path)
        try:
            validate_state_strict(state)
        except AcceptanceError as exc:
            return _result(evidence, "INVALID_STATE_LEGACY", exc.message, 4, revision=state.get("revision"), state_replaced=False), 4
        run = find_run(state, ns.run_id)
        conflict = _owner_gate(state, run, ns)
        if conflict:
            return _result(evidence, conflict, "run/owner/revision is not authoritative", 4,
                           replacement=False, state_replaced=False), 4
        if terminal(run):
            return _result(evidence, "CONFLICT_STALE_REVISION", "run is already terminal", 4,
                           replacement=False, state_replaced=False), 4
        if ns.outcome == "VERIFIED" and not _dispatch_complete(run):
            return _result(evidence, "CONFLICT_UNRESOLVED_DISPATCH",
                           "no completed successful dispatch record; VERIFIED finalization is refused", 4,
                           replacement=False, state_replaced=False), 4
        expected_revision = state.get("revision")
        if ns.outcome == "VERIFIED":
            try:
                verification = _consume_verification(ns, run)
            except AcceptanceError as exc:
                return _result(evidence, exc.code, exc.message, exc.exit_code, replacement=False, state_replaced=False), exc.exit_code
            reference = None
            for event in reversed(run.get("events", [])):
                if isinstance(event, dict):
                    parsed = parse_binding_reference(event.get("evidence"))
                    if parsed is not None and parsed[0] in {"join", "user_fact", "fixture"}:
                        reference = event["evidence"]
                        break
            from .common import binding_artifact_matches
            binding_ok = reference is not None and binding_artifact_matches(
                reference, app_identifier="jp.naver.line.mac", group_key=run["group_key"],
                fp=run["fingerprint"], project_root=Path(auth["project_root"]), test_mode=ns.test_mode,
                state_path=path, evidence_dir=evidence)
            if not binding_ok:
                return _result(evidence, "BINDING_UNVERIFIED", "the external binding artifact cannot be re-verified; VERIFIED finalization is refused", 4,
                               replacement=False, state_replaced=False), 4
            run["verification"] = _verification_block(verification, Path(ns.verification_json))
            run["workflow_outcome"] = "VERIFIED"
            run["phase"] = "VERIFIED"
            run["checkpoint"] = {"phase": "VERIFIED", "at": _utc(), "evidence": "terminal VERIFIED with binding reference"}
            run["events"].append({"phase": "VERIFIED", "at": _utc(), "evidence": reference})
            source_kind = "user_attestation" if parse_binding_reference(reference)[0] == "user_fact" else "filesystem_verification"
            state["verified_albums"].append({"group_key": run["group_key"], "fingerprint": run["fingerprint"],
                                             "verified_run_id": run["run_id"], "destinations": [run["destination"]],
                                             "source_kind": source_kind, "evidence": reference})
        else:
            run["workflow_outcome"] = "SAFE_ABORT"
            run["phase"] = "SAFE_ABORT"
            run["stop_reason"] = "SAFE_ABORT_UNRESOLVED_DISPATCH"
            run["checkpoint"] = {"phase": "SAFE_ABORT", "at": _utc(), "evidence": "terminal SAFE_ABORT: unresolved dispatch barrier preserved"}
            run["events"].append({"phase": "SAFE_ABORT", "at": _utc(),
                                  "evidence": "terminal SAFE_ABORT: unresolved dispatch barrier preserved"})
        state["current_run_id"] = None
        state["active_writer_id"] = None
        state["context_lock"] = None
        state["revision"] = expected_revision + 1
        try:
            _replace(path, state, expected_revision, fault=ns.storage_fault)
        except AcceptanceError as exc:
            if exc.code == "READBACK_UNCERTAIN":
                return _result(evidence, "READBACK_UNCERTAIN", exc.message, 1,
                               revision=state["revision"], terminal_committed=True, state_replaced=True), 1
            return _result(evidence, exc.code, exc.message, exc.exit_code, revision=state["revision"] - 1,
                           replacement=False, state_replaced=False), exc.exit_code
        return _result(evidence, "FINALIZED", "terminal outcome committed", 0,
                       revision=state["revision"], outcome=ns.outcome, replacement=True, state_replaced=True), 0


def duplicate_check(ns):
    auth = validate_transaction(ns)
    path, evidence = Path(auth["state"]), Path(auth["evidence_dir"])
    with locked_state(path):
        state = read_json(path)
        fp = fingerprint(ns.start_date, ns.end_date, ns.expected_images)
        refusal = _evaluate_preconditions(state, ns.group_key, fp, ns.destination, duplicate_check=True)
        if refusal:
            code, exit_code = refusal
            if code == "SKIP_DUPLICATE":
                return _result(evidence, "SKIP_DUPLICATE", "exact terminal association exists", 0,
                               replacement=False, state_replaced=False, dispatch_performed=False), 0
            return _result(evidence, code, "duplicate-check precondition refused", exit_code,
                           replacement=False, state_replaced=False, dispatch_performed=False), exit_code
    return _result(evidence, "NOT_DUPLICATE", "no same-group association and no same-fingerprint intent or run exists", 0,
                   replacement=False, state_replaced=False, dispatch_performed=False), 0
