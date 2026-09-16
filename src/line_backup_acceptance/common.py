from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator


class AcceptanceError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 1):
        super().__init__(message)
        self.code, self.message, self.exit_code = code, message, exit_code


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def atomic_write_json(path: Path, value: Any, *, fault: str | None = None) -> dict:
    data = json_bytes(value)
    if fault == "WRITE_BEFORE_REPLACE":
        raise AcceptanceError("WRITE_BEFORE_REPLACE", "injected storage fault before replacement", 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            dfd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
            durability = "file-and-directory-fsync"
        except OSError:
            durability = "file-fsync-and-atomic-replace"
        return {"bytes": len(data), "sha256": sha256_bytes(data), "durability": durability}
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AcceptanceError("STATE_READ_ERROR", f"cannot read JSON {path}: {exc}", 1) from exc


@contextlib.contextmanager
def locked_state(state_path: Path) -> Iterator[None]:
    import fcntl
    lock = state_path.parent / ".line-backup-state.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def wait_barrier(pause_at: str | None, barrier_file: str | None) -> None:
    if not pause_at:
        return
    if not barrier_file:
        raise AcceptanceError("INVALID_INPUT", "--barrier-file is required with --pause-at", 2)
    ready = Path(barrier_file + ".ready")
    ready.parent.mkdir(parents=True, exist_ok=True)
    ready.touch()
    barrier = Path(barrier_file)
    while not barrier.exists():
        time.sleep(0.01)


def within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def exact_real_path(path: Path) -> bool:
    return os.path.realpath(path) == os.path.abspath(path)


def fingerprint(start: str, end: str, count: int) -> dict:
    return {"start_date": start, "end_date": end, "expected_images": count}


def find_run(state: dict, run_id: str) -> dict | None:
    for run in state.get("runs", []):
        if isinstance(run, dict) and run.get("run_id") == run_id:
            return run
    return None


def terminal(run: dict | None) -> bool:
    return bool(run and run.get("workflow_outcome") in {"VERIFIED", "SAFE_ABORT"})


def result_file(evidence_dir: Path, result: dict) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(evidence_dir / "result.json", result)


def emit(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


# ---------------------------------------------------------------------------
# Versioned schema contracts (line-album-backup schemas/schemas.json 1.0-rc2)
# ---------------------------------------------------------------------------

STATE_KEYS = {"schema_version", "revision", "current_run_id", "verified_albums", "runs",
              "active_writer_id", "context_lock"}
RUN_REQUIRED = {"run_id", "mode", "group_key", "album_id", "fingerprint", "observed_title",
                "title_confidence", "destination", "destination_initially_empty", "phase",
                "checkpoint", "events", "intent", "recovery_used", "runtime_errors",
                "verification", "workflow_outcome", "stop_reason", "batch_id", "intent_state",
                "manual_reconciliation_required", "reconciliation_reason"}
RUN_OPTIONAL_RC2 = {"contract_revision", "dispatch_state", "dispatch_evidence", "reconciliations"}
PHASES = {"LOAD_STATE", "CUA_RUNTIME_GATE", "TARGET_CONTEXT", "TARGET_CONTEXT_LOCKED",
          "ALBUM_DISCOVERY", "DUPLICATE_GATE", "PREPARE_DESTINATION", "OPEN_ALBUM",
          "SAVE_ALL_CALIBRATION", "SAVE_ALL_INTENT_COMMITTED", "SAVE_ALL_TRIGGERED", "CHOOSER",
          "DOWNLOAD_STARTED", "VERIFYING", "VERIFIED", "SAFE_ABORT",
          "ABORTED_BEFORE_SAVE_ALL_DISPATCH", "SAVE_ALL_DISPATCH_ATTEMPTED",
          "TRIGGER_CONFIRMED", "TRIGGER_UNKNOWN", "NONDESTRUCTIVE_CALIBRATION_MODE"}
WORKFLOW_OUTCOMES = {"IN_PROGRESS", "VERIFIED", "FAILED", "SAFE_ABORT"}
RC2_INTENT_STATES = {"INTENT_NONE", "INTENT_COMMITTED", "ABORTED_BEFORE_SAVE_ALL_DISPATCH",
                     "SAVE_ALL_DISPATCH_ATTEMPTED", "TRIGGER_CONFIRMED", "TRIGGER_UNKNOWN"}
LEGACY_INTENT_STATES = {"NONE", "COMMITTED_NOT_DISPATCHED", "DISPATCHED", "TRIGGER_CONFIRMED", "UNKNOWN"}
DISPATCH_STATES = {"NOT_ATTEMPTED", "ELLIPSIS_FAILED", "SAVE_ALL_ATTEMPTED", "SAVE_ALL_RETURNED", "UNKNOWN"}
INTENT_TRIGGER_OUTCOMES = {"NOT_OBSERVED", "CHOOSER_CONFIRMED", "UNKNOWN", "UNEXPECTED_UI",
                           "NOT_APPLICABLE", "NOT_TRIGGERED", "TRIGGER_CONFIRMED"}
INTENT_DISPATCH_OUTCOMES = {"NOT_ATTEMPTED", "RETURNED", "ERROR", "UNKNOWN"}
CALIBRATION_KEYS = {"observed_at", "screenshot_width", "screenshot_height", "ellipsis", "dot_spacing",
                    "save_all_point", "confidence", "evidence"}
DISPATCH_EVIDENCE_KEYS = {"run_id", "action_id", "execution_id", "observed_at", "save_all_click_count",
                          "save_all_invocation_attempted", "failure_boundary", "folder_chooser_appeared",
                          "download_started", "provenance"}
FAILURE_BOUNDARIES = {"ELLIPSIS_CLICK", "BEFORE_SAVE_ALL_INVOCATION", "SAVE_ALL_INVOCATION",
                      "AFTER_SAVE_ALL_INVOCATION", "NONE", "UNKNOWN"}
RECONCILIATION_KEYS = {"reconciliation_id", "recorded_at", "run_id", "action_id", "execution_id",
                       "outcome", "trigger_outcome", "blocking_intent_released",
                       "manual_reconciliation_required", "original_observation", "proof", "evidence"}
ENTRY_KEYS = {"group_key", "fingerprint", "verified_run_id", "destinations", "source_kind", "evidence"}


def _strict_fail(reason: str):
    raise AcceptanceError("INVALID_STATE_LEGACY", f"strict schema deviation: {reason}", 4)


def _int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_fingerprint(fp) -> None:
    if not isinstance(fp, dict) or set(fp) != {"start_date", "end_date", "expected_images"}:
        _strict_fail("fingerprint shape")
    if not isinstance(fp["start_date"], str) or not isinstance(fp["end_date"], str):
        _strict_fail("fingerprint dates")
    if not _int(fp["expected_images"]) or fp["expected_images"] < 1:
        _strict_fail("fingerprint count")


def _check_calibration(cal) -> None:
    if not isinstance(cal, dict) or set(cal) != CALIBRATION_KEYS:
        _strict_fail("calibration shape")
    for key in ("screenshot_width", "screenshot_height"):
        if not _int(cal[key]) or cal[key] < 1:
            _strict_fail("calibration dimension")
    if not isinstance(cal["confidence"], str) or cal["confidence"] != "HIGH":
        _strict_fail("calibration confidence")
    if not isinstance(cal["evidence"], str) or not cal["evidence"]:
        _strict_fail("calibration evidence")


def _check_intent(intent) -> None:
    if not isinstance(intent, dict):
        _strict_fail("intent is not an object")
    expected = {"action_id", "committed_at", "owner_execution_id", "group_key", "fingerprint",
                "destination", "calibration", "save_all_retry_allowed", "dispatch_outcome",
                "trigger_outcome"}
    if set(intent) != expected:
        _strict_fail("intent keys")
    for key in ("action_id", "committed_at", "owner_execution_id", "group_key", "destination"):
        if not isinstance(intent[key], str) or not intent[key]:
            _strict_fail(f"intent.{key}")
    if not intent["destination"].startswith("/"):
        _strict_fail("intent.destination")
    _check_fingerprint(intent["fingerprint"])
    _check_calibration(intent["calibration"])
    if intent["save_all_retry_allowed"] is not False:
        _strict_fail("intent.save_all_retry_allowed")
    if intent["dispatch_outcome"] not in INTENT_DISPATCH_OUTCOMES:
        _strict_fail("intent.dispatch_outcome")
    if intent["trigger_outcome"] not in INTENT_TRIGGER_OUTCOMES:
        _strict_fail("intent.trigger_outcome")


def _check_checkpoint(value) -> None:
    if not isinstance(value, dict) or set(value) != {"phase", "at", "evidence"}:
        _strict_fail("checkpoint shape")
    if value["phase"] not in PHASES or not isinstance(value["at"], str) or not isinstance(value["evidence"], str):
        _strict_fail("checkpoint values")


def _check_dispatch_evidence(value) -> None:
    if not isinstance(value, dict) or set(value) != DISPATCH_EVIDENCE_KEYS:
        _strict_fail("dispatch_evidence shape")
    for key in ("run_id", "action_id", "execution_id", "observed_at", "provenance"):
        if not isinstance(value[key], str) or not value[key]:
            _strict_fail(f"dispatch_evidence.{key}")
    if value["save_all_click_count"] is not None and not (_int(value["save_all_click_count"]) and 0 <= value["save_all_click_count"] <= 1):
        _strict_fail("dispatch_evidence.save_all_click_count")
    for key in ("save_all_invocation_attempted", "folder_chooser_appeared", "download_started"):
        if value[key] is not None and not isinstance(value[key], bool):
            _strict_fail(f"dispatch_evidence.{key}")
    if value["failure_boundary"] not in FAILURE_BOUNDARIES:
        _strict_fail("dispatch_evidence.failure_boundary")


def _check_reconciliation(value) -> None:
    if not isinstance(value, dict) or set(value) != RECONCILIATION_KEYS:
        _strict_fail("reconciliation shape")
    for key in ("reconciliation_id", "recorded_at", "run_id", "action_id", "execution_id", "evidence"):
        if not isinstance(value[key], str) or not value[key]:
            _strict_fail(f"reconciliation.{key}")
    if value["outcome"] not in {"ABORTED_BEFORE_SAVE_ALL_DISPATCH", "EVIDENCE_RECONCILED"}:
        _strict_fail("reconciliation.outcome")
    if value["trigger_outcome"] not in {"NOT_TRIGGERED", "TRIGGER_CONFIRMED", "UNKNOWN"}:
        _strict_fail("reconciliation.trigger_outcome")
    if not isinstance(value["blocking_intent_released"], bool) or not isinstance(value["manual_reconciliation_required"], bool):
        _strict_fail("reconciliation flags")
    obs = value["original_observation"]
    if not isinstance(obs, dict) or set(obs) != {"reference", "trigger_outcome"}:
        _strict_fail("reconciliation.original_observation")
    if not isinstance(obs["reference"], str) or not obs["reference"]:
        _strict_fail("reconciliation reference")
    if obs["trigger_outcome"] not in INTENT_TRIGGER_OUTCOMES:
        _strict_fail("reconciliation original trigger")
    if value["proof"] is not None:
        _check_dispatch_evidence(value["proof"])
        proof = value["proof"]
        if value["outcome"] == "ABORTED_BEFORE_SAVE_ALL_DISPATCH":
            if not (proof["save_all_click_count"] == 0 and proof["save_all_invocation_attempted"] is False
                    and proof["failure_boundary"] in {"ELLIPSIS_CLICK", "BEFORE_SAVE_ALL_INVOCATION"}
                    and proof["folder_chooser_appeared"] is False and proof["download_started"] is False):
                _strict_fail("non_dispatch_proof values")
    if value["outcome"] == "ABORTED_BEFORE_SAVE_ALL_DISPATCH":
        if value["trigger_outcome"] != "NOT_TRIGGERED" or value["blocking_intent_released"] is not True \
                or value["manual_reconciliation_required"] is not False or value["proof"] is None:
            _strict_fail("aborted reconciliation routing")


def _check_run(run) -> None:
    if not isinstance(run, dict):
        _strict_fail("run is not an object")
    keys = set(run)
    if not RUN_REQUIRED.issubset(keys):
        _strict_fail("run required keys")
    if "contract_revision" in keys:
        if keys - RUN_REQUIRED - RUN_OPTIONAL_RC2:
            _strict_fail("run extra keys (rc2)")
        if run["contract_revision"] != "1.0-rc2":
            _strict_fail("contract_revision value")
        if run["intent_state"] not in RC2_INTENT_STATES:
            _strict_fail("rc2 intent_state enum")
        if run["dispatch_state"] not in DISPATCH_STATES:
            _strict_fail("dispatch_state enum")
        if run["dispatch_evidence"] is not None:
            _check_dispatch_evidence(run["dispatch_evidence"])
        if not isinstance(run["reconciliations"], list):
            _strict_fail("reconciliations list")
        for item in run["reconciliations"]:
            _check_reconciliation(item)
    else:
        # Legacy (pre-RC2) records: the schema forbids dispatch_state/dispatch_evidence
        # and keeps the legacy intent_state enum; an appended reconciliations[] list is
        # tolerated by $defs/run ("optional appended reconciliation does not relabel history").
        if keys - RUN_REQUIRED - {"reconciliations"}:
            _strict_fail("run extra keys (legacy)")
        if run["intent_state"] not in LEGACY_INTENT_STATES:
            _strict_fail("legacy intent_state enum")
        if "reconciliations" in keys:
            if not isinstance(run["reconciliations"], list):
                _strict_fail("legacy reconciliations list")
            for item in run["reconciliations"]:
                _check_reconciliation(item)
    if run["mode"] not in {"backup_one", "backup_batch", "resume"}:
        _strict_fail("run.mode")
    if run["workflow_outcome"] not in WORKFLOW_OUTCOMES:
        _strict_fail("run.workflow_outcome")
    if run["phase"] not in PHASES:
        _strict_fail("run.phase")
    if run["title_confidence"] not in {"HIGH", "LOW", "UNKNOWN"}:
        _strict_fail("run.title_confidence")
    if run["destination"] is not None and (not isinstance(run["destination"], str) or not run["destination"].startswith("/")):
        _strict_fail("run.destination")
    if run["fingerprint"] is not None:
        _check_fingerprint(run["fingerprint"])
    if run["intent"] is not None:
        _check_intent(run["intent"])
    _check_checkpoint(run["checkpoint"])
    if not isinstance(run["events"], list):
        _strict_fail("run.events")
    for event in run["events"]:
        _check_checkpoint(event)
    if not isinstance(run["recovery_used"], dict):
        _strict_fail("run.recovery_used")
    if not isinstance(run["runtime_errors"], list):
        _strict_fail("run.runtime_errors")
    if run["verification"] is not None:
        value = run["verification"]
        required = {"observed_at", "outcome", "regular_files", "image_files", "subdirectories",
                    "total_bytes", "extensions", "metadata_files", "zero_byte_files",
                    "partial_temp_files", "unrecognized_files", "other_entries", "stable_samples",
                    "inventory", "evidence"}
        if not isinstance(value, dict) or set(value) != required:
            _strict_fail("run.verification shape")
        if value["outcome"] not in {"PASS", "FAIL", "INCOMPLETE_OR_STILL_DOWNLOADING"}:
            _strict_fail("run.verification.outcome")
        if not isinstance(value["inventory"], list):
            _strict_fail("run.verification.inventory")
    if run["manual_reconciliation_required"] is True and not (isinstance(run["reconciliation_reason"], str) and run["reconciliation_reason"]):
        _strict_fail("manual reconciliation reason")
    if "contract_revision" in keys and run["intent_state"] == "ABORTED_BEFORE_SAVE_ALL_DISPATCH":
        if run["workflow_outcome"] != "SAFE_ABORT":
            _strict_fail("aborted workflow outcome")
        if not any(isinstance(item, dict) and item.get("outcome") == "ABORTED_BEFORE_SAVE_ALL_DISPATCH"
                   for item in run.get("reconciliations", [])):
            _strict_fail("aborted reconciliation missing")


def validate_state_strict(state) -> None:
    """Validate a payload about to be replaced against $defs/state + $defs/run."""
    if not isinstance(state, dict) or set(state) != STATE_KEYS:
        _strict_fail("state keys")
    if state["schema_version"] != 2 or not _int(state["revision"]) or state["revision"] < 0:
        _strict_fail("state schema/revision")
    if state["current_run_id"] is not None and not isinstance(state["current_run_id"], str):
        _strict_fail("current_run_id")
    if state["active_writer_id"] is not None and not isinstance(state["active_writer_id"], str):
        _strict_fail("active_writer_id")
    lock = state["context_lock"]
    if lock is not None:
        if not isinstance(lock, dict) or set(lock) != {"group_key", "source", "confirmed_at", "execution_id", "continuity_evidence"}:
            _strict_fail("context_lock shape")
        if lock["source"] not in {"USER_CONFIRMATION", "RELIABLE_VISUAL_NAVIGATION"}:
            _strict_fail("context_lock source")
    if not isinstance(state["runs"], list) or not isinstance(state["verified_albums"], list):
        _strict_fail("state lists")
    for run in state["runs"]:
        _check_run(run)
    for entry in state["verified_albums"]:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            _strict_fail("verified_albums shape")
        if not isinstance(entry["group_key"], str) or not entry["group_key"]:
            _strict_fail("verified_albums group")
        _check_fingerprint(entry["fingerprint"])
        if entry["verified_run_id"] is not None and not isinstance(entry["verified_run_id"], str):
            _strict_fail("verified_run_id")
        if not isinstance(entry["destinations"], list) or any(not isinstance(d, str) or not d.startswith("/") for d in entry["destinations"]):
            _strict_fail("destinations")
        if entry["source_kind"] not in {"filesystem_verification", "user_attestation"}:
            _strict_fail("source_kind")
        if not isinstance(entry["evidence"], str) or not entry["evidence"]:
            _strict_fail("entry evidence")


def classify_legacy_run(run) -> tuple[str | None, str]:
    """Read-only legacy classification for one run.

    Returns (kind, detail): kind None when the run is strictly valid; otherwise one of the
    pinned kinds {calibration.extra_keys, calibration.missing, contract_revision.missing,
    UNREADABLE_LEGACY}; the real formal state is always readable under this contract.
    """
    if not isinstance(run, dict):
        return "UNREADABLE_LEGACY", "run record is not an object"
    if "contract_revision" in run:
        try:
            _check_run(dict(run))
        except AcceptanceError as exc:
            return "UNREADABLE_LEGACY", exc.message
        return None, ""
    intent = run.get("intent")
    if isinstance(intent, dict) and "calibration" in intent:
        calibration = intent.get("calibration")
        if isinstance(calibration, dict):
            extra = set(calibration) - CALIBRATION_KEYS
            if extra:
                return "calibration.extra_keys", f"intent.calibration carries extra keys {sorted(extra)}"
            if not CALIBRATION_KEYS.issubset(calibration):
                return "UNREADABLE_LEGACY", "legacy intent.calibration is missing required keys"
            return "contract_revision.missing", "pre-RC2 run without contract_revision"
        return "UNREADABLE_LEGACY", "legacy intent.calibration is not an object"
    if intent is None or (isinstance(intent, dict) and "calibration" not in intent):
        return "calibration.missing", "intent.calibration is absent; calibration reports UNKNOWN"
    return "UNREADABLE_LEGACY", "legacy run has an unrecognized intent shape"


# ---------------------------------------------------------------------------
# Binding-reference grammar and external-artifact resolution (Rev15 §15.2,
# Rev16 §16.6, Rev17 §17.4).  The reference grammar is exactly
#   join:<relpath>:<sha256> | user_fact:<relpath>:<sha256> | fixture:<relpath>:<sha256>
# and reconcile:<relpath>:<sha256> exists only for reconciliation evidence.
# ---------------------------------------------------------------------------

import re as _re

WORK_ROOT = Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
BINDING_KINDS = ("join", "user_fact", "fixture")
RECONCILE_KIND = "reconcile"
_SHA256_RE = _re.compile(r"^[0-9a-f]{64}$")


def parse_binding_reference(text: Any):
    """Return (kind, relpath, sha256) for a grammar-valid reference, else None."""
    if not isinstance(text, str):
        return None
    head, sep, rest = text.partition(":")
    if not sep or head not in (*BINDING_KINDS, RECONCILE_KIND):
        return None
    relpath, sep2, sha = rest.rpartition(":")
    if not sep2 or not relpath or not _SHA256_RE.match(sha):
        return None
    return head, relpath, sha


def _normal_relative(relpath: str) -> bool:
    if not relpath or relpath.startswith("/") or relpath.endswith("/"):
        return False
    parts = relpath.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return True


def _no_symlink_components(base: Path, relpath: str) -> bool:
    current = base
    for part in relpath.split("/"):
        current = current / part
        try:
            if current.is_symlink():
                return False
        except OSError:
            return False
    return True


def resolve_binding_artifact(kind: str, relpath: str, *, project_root: Path, test_mode: bool,
                             state_path: Path | None = None, evidence_dir: Path | None = None,
                             workspace_root: Path = WORK_ROOT) -> Path:
    """Resolve a binding reference to its external artifact or raise INVALID_SOURCE_EVIDENCE.

    Base rules (Rev18 §16.4): user_fact: resolves against the WORK root in production and
    against the case --project-root in test mode; join: resolves against the WORK root
    (production only); fixture: resolves against the case --project-root (test mode only).
    A path that escapes its base, contains `..`, passes through a symlink, or is not
    expressible as a normal relative path is refused.  The binding artifact must sit
    outside the operation's own state path and evidence directory.
    """
    if kind not in BINDING_KINDS:
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", f"unsupported binding kind {kind!r}", 2)
    if not _normal_relative(relpath):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding relpath is not a normal relative path", 2)
    if kind == "fixture":
        if not test_mode:
            raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "fixture binding is unverifiable in production", 2)
        base = Path(project_root)
    elif kind == "join":
        if test_mode:
            raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "join binding base is the workspace root", 2)
        base = Path(workspace_root)
    else:  # user_fact: WORK root in production, case project root in test mode (Rev18 §16.4)
        base = Path(project_root) if test_mode else Path(workspace_root)
    if not _no_symlink_components(base, relpath):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding path passes through a symlink component", 2)
    candidate = base / relpath
    real_base, real_candidate = Path(os.path.realpath(base)), Path(os.path.realpath(candidate))
    if not within(real_candidate, real_base):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding path escapes its base", 2)
    if state_path is not None and within(real_candidate, Path(os.path.realpath(state_path.parent))):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding artifact resolves inside the state path", 2)
    if evidence_dir is not None and within(real_candidate, Path(os.path.realpath(evidence_dir))):
        raise AcceptanceError("INVALID_SOURCE_EVIDENCE", "binding artifact resolves inside the evidence directory", 2)
    return real_candidate


def _rehash_evidence_entries(entries: Any) -> bool:
    if not isinstance(entries, list) or not entries:
        return False
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            return False
        if not isinstance(entry["path"], str) or not isinstance(entry["bytes"], int) or not isinstance(entry["sha256"], str):
            return False
        path = Path(entry["path"])
        if not path.is_absolute() or not path.is_file():
            return False
        data = path.read_bytes()
        if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
            return False
    return True


def user_fact_v1_matches(record: Any, *, app_identifier: str, group_key: str, fp: dict) -> bool:
    """Exact Rev16 §16.4 v1 CONFIRMED-record matching.  No normalization, no similarity."""
    if not isinstance(record, dict):
        return False
    if record.get("record_version") != "1.0" or record.get("kind") != "source_identity_user_fact":
        return False
    if record.get("status") != "CONFIRMED" or record.get("source_correspondence_result") != "CONFIRMED":
        return False
    if record.get("merge_prohibited") is not True:
        return False
    if record.get("app_identifier") != app_identifier:
        return False
    raw = record.get("raw_requested_group")
    if not isinstance(raw, str) or "line:" + str(app_identifier) + ":" + raw != group_key:
        return False
    if record.get("fingerprint") != fp:
        return False
    question = record.get("question")
    answer = record.get("answer")
    if not isinstance(question, dict) or not str(question.get("text", "")).strip():
        return False
    if not isinstance(answer, dict) or not str(answer.get("raw", "")).strip():
        return False
    part2 = answer.get("part_2")
    if not isinstance(part2, dict) or part2.get("confirms_same_source") is not True:
        return False
    album_label = fp["start_date"].replace("-", "/") + "～" + fp["end_date"][5:].replace("-", "/")
    if part2.get("confirmed_group_string") != group_key.rsplit(":", 1)[-1]:
        return False
    if part2.get("confirmed_album") != album_label:
        return False
    if part2.get("confirmed_expected_images") != fp["expected_images"]:
        return False
    if not _rehash_evidence_entries(record.get("evidence")):
        return False
    return True


def binding_artifact_matches(reference: str, *, app_identifier: str, group_key: str, fp: dict,
                             project_root: Path, test_mode: bool, state_path: Path | None = None,
                             evidence_dir: Path | None = None) -> bool:
    """Re-read and re-hash the external binding artifact and check its content anchors."""
    parsed = parse_binding_reference(reference)
    if parsed is None or parsed[0] not in BINDING_KINDS:
        return False
    kind, relpath, sha = parsed
    try:
        path = resolve_binding_artifact(kind, relpath, project_root=project_root, test_mode=test_mode,
                                        state_path=state_path, evidence_dir=evidence_dir)
    except AcceptanceError:
        return False
    if not path.is_file():
        return False
    data = path.read_bytes()
    if sha256_bytes(data) != sha:
        return False
    try:
        record = json.loads(data.decode("utf-8"))
    except Exception:
        return False
    if kind == "user_fact":
        return user_fact_v1_matches(record, app_identifier=app_identifier, group_key=group_key, fp=fp)
    if not isinstance(record, dict):
        return False
    if kind == "join" and record.get("join_authority") != "authoritative_exact_join":
        return False
    if record.get("app_identifier") != app_identifier:
        return False
    if record.get("group_key") != group_key:
        return False
    if record.get("fingerprint") != fp:
        return False
    return True


# ---------------------------------------------------------------------------
# Verification-evidence chain v2 (Rev17 §17.2)
# ---------------------------------------------------------------------------

RESULT_VERDICT_FIELDS = ("schema_version", "mode", "run_id", "group_key", "fingerprint", "destination",
                         "filesystem_status", "recognized_images", "expected_images", "overall_status",
                         "exit_code", "artifact_readback")


def result_summary_of(result: dict) -> dict:
    return {field: result.get(field) for field in RESULT_VERDICT_FIELDS}


def sha256_and_bytes(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), sha256_bytes(data)


def write_result_chain(evidence_dir: Path, result: dict, *, inject_readback_failure: bool = False) -> dict:
    """Write result.json, then manifest.json last, and validate the chain by read-back.

    Write order is one-directional (Rev17 §17.2): every other artifact -> result.json ->
    manifest.json; the manifest lists every artifact including result.json and excludes
    only itself, with result_summary/result_bytes/result_sha256 of the result it recorded.
    """
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(evidence_dir / "result.json", result)
    result_bytes, result_sha = sha256_and_bytes(evidence_dir / "result.json")
    artifacts = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            size, digest = sha256_and_bytes(path)
            artifacts.append({"path": path.name, "bytes": size, "sha256": digest})
    manifest = {"schema_version": 1, "artifacts": artifacts,
                "result_summary": result_summary_of(result),
                "result_bytes": result_bytes, "result_sha256": result_sha}
    if inject_readback_failure:
        raise AcceptanceError("INTERNAL_ARTIFACT_ERROR", "injected evidence manifest write/read-back failure", 1)
    atomic_write_json(evidence_dir / "manifest.json", manifest)
    validate_result_chain(evidence_dir / "result.json")
    return manifest


def validate_result_chain(result_path: Path) -> dict:
    """Recompute the whole evidence chain from disk; raise INVALID_VERIFICATION_EVIDENCE on any gap."""
    result_path = Path(result_path)
    try:
        result_data = result_path.read_bytes()
        result = json.loads(result_data.decode("utf-8"))
    except Exception as exc:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", f"verification JSON is unreadable: {exc}", 4) from exc
    if not isinstance(result, dict):
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "verification JSON is not an object", 4)
    manifest_path = result_path.parent / "manifest.json"
    if not manifest_path.is_file():
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "no evidence chain (manifest.json) beside the result", 4)
    try:
        manifest = json.loads(manifest_path.read_bytes().decode("utf-8"))
    except Exception as exc:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", f"manifest is unreadable: {exc}", 4) from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "manifest shape is not chain v2", 4)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "manifest artifacts list is missing", 4)
    if len(result_data) != manifest.get("result_bytes") or sha256_bytes(result_data) != manifest.get("result_sha256"):
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "manifest result bytes/sha256 disagree with result.json", 4)
    if manifest.get("result_summary") != result_summary_of(result):
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "manifest result_summary disagrees with result.json", 4)
    seen_names = set()
    for entry in artifacts:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "artifact entry shape is invalid", 4)
        name = entry["path"]
        if not isinstance(name, str) or "/" in name or name in seen_names:
            raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "artifact path is not a plain file name", 4)
        seen_names.add(name)
        target = result_path.parent / name
        if not target.is_file():
            raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", f"manifest artifact {name} is missing", 4)
        data = target.read_bytes()
        if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
            raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", f"manifest artifact {name} does not re-hash", 4)
    if "result.json" not in seen_names or "manifest.json" in seen_names:
        raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", "manifest artifact set is not the chain-v2 set", 4)
    for path in result_path.parent.iterdir():
        if path.is_file() and path.name not in seen_names and path.name != "manifest.json":
            raise AcceptanceError("INVALID_VERIFICATION_EVIDENCE", f"artifact {path.name} is not covered by the manifest", 4)
    return result
