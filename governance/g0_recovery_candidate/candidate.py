"""Pure, non-activating G0 recovery state-machine candidate.

This module has no filesystem, process, network, UI, or Controller integration.
It verifies signed envelopes and returns immutable candidate state values only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import hmac
import json
from types import MappingProxyType
from typing import Mapping
import unicodedata


class CandidateError(ValueError):
    """A recovery transition failed closed."""


TASK_ID = "TASK-4acb4326ea2a4c50ace6f333f2de8751"
ISSUE_ID = "a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5"
C6_RUN_ID = "c6c6b55d-865f-467b-94ba-3fd669df97ec"

CONTROLLER_SHA256 = "385bbd2abd57ed305c01c7437f449833ed09cfc7e9f07add87d6352d405a8af5"
ESCALATION_SHA256 = "7044aa55c6cc7721205fbd95ed2643ac0debcc67701c303c563a23dbc4768451"
POLICY_SHA256 = "7c2251913507a8cc09b4a697576963aaf6694ffd7fd7af55a6eb2e813a690912"
CONTRACT_SHA256 = "a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc"
TASK_STATE_FILE_SHA256 = "17e74f0b9f00fafa770273dd5a481e3aa8c98fb1ae9d508ff21bb248956ec822"
FROZEN_GATE_FREEZE_FILE_SHA256 = "f13f019adeb9afe5eb019f9abe579b9795834f5959e15bf404c7a51ce8c63fe0"
GATE_CATALOG_SHA256 = "697821120d0eaea35e9b7bcab5c8b7ca8a99002d9e1e9184494bbf844ebc0f49"
ISSUE_STATE_SHA256 = "fcd32c55924e52824184e25b6ebb70d7d346f3fe0d17fd96ec6c787654658dd6"
C6_CONSUMPTION_SHA256 = "2af57177374f393e4e965d6e96f386853362ef8595f2b990abee2fefc05f4ffe"
C6_RESULT_SHA256 = "0e9a4f7439209703bcf4b45742fde3344905c2feaf913d45d7704f9ba2787c07"
C6_RECEIPT_SHA256 = "9889e84de2ceaa0fa0154a0f172dafdc5260d8dbd2fb9da6af4bbfd4288f3144"
ISSUE_WAIT_EVENT_SHA256 = "b79292c76783259cc41f2f6b81907e312a8b5791137978ef92f0a1c68380b7dc"

# The original root issue criterion differs from c6's bounded continuation
# criterion. Only the former can authorize resolution of this original issue.
ORIGINAL_CRITERION_SHA256 = "9b5b171e37e828f325b004b6a8a91d7ceae6ef52b36b2a4270ce6c4f8d4db657"
C6_PERMISSION_CRITERION_SHA256 = "82b1892f80e4b1b00a0386644ea875148fa0c82cbfa7cb81228b786bae6b8861"
EXPECTED_GATE_COUNT = 28
TASK_ROOT_RELATIVE = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08"
TASK_ROOT_PATH_SHA256 = "5f2da693fdbd5c3b71faf62313663842dad8606e3eec5bd1089e8522c5bd749e"

DENIED_CAPABILITIES = (
    "GUI_INPUT",
    "SCREENSHOT_AX_CAPTURE",
    "LINE_DOWNLOAD",
    "SAVE_ALL",
    "CHOOSER_CONFIRMATION",
    "BACKUP_STATE_WRITE",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")


def _is_sha256(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


def _safe_relative_module_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if (unicodedata.normalize("NFC", value) != value
            or any(unicodedata.category(character) == "Cc" for character in value)):
        return False
    parts = value.split("/")
    return (not any(part in {"", ".", ".."} for part in parts)
            and value.startswith(TASK_ROOT_RELATIVE + "/"))


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


_HISTORY_ANCHOR = _sha256(_canonical({
    "issue_state": ISSUE_STATE_SHA256,
    "c6_consumption": C6_CONSUMPTION_SHA256,
    "c6_result": C6_RESULT_SHA256,
    "c6_receipt": C6_RECEIPT_SHA256,
    "issue_wait_event": ISSUE_WAIT_EVENT_SHA256,
}))

FROZEN_BINDING = {
    "task_id": TASK_ID,
    "issue_id": ISSUE_ID,
    "c6_run_id": C6_RUN_ID,
    "controller_sha256": CONTROLLER_SHA256,
    "escalation_sha256": ESCALATION_SHA256,
    "policy_sha256": POLICY_SHA256,
    "contract_sha256": CONTRACT_SHA256,
    "task_state_file_sha256": TASK_STATE_FILE_SHA256,
    "gate_freeze_file_sha256": FROZEN_GATE_FREEZE_FILE_SHA256,
    "gate_catalog_sha256": GATE_CATALOG_SHA256,
    "task_root_path_sha256": TASK_ROOT_PATH_SHA256,
    "original_criterion_sha256": ORIGINAL_CRITERION_SHA256,
    "c6_permission_criterion_sha256": C6_PERMISSION_CRITERION_SHA256,
    "history_anchor_sha256": _HISTORY_ANCHOR,
    "gate_count": EXPECTED_GATE_COUNT,
}
FROZEN_BINDING_SHA256 = _sha256(_canonical(FROZEN_BINDING))


@dataclass(frozen=True)
class Envelope:
    key_id: str
    payload: bytes
    signature_hex: str

    @classmethod
    def from_mapping(cls, key_id: str, payload: Mapping[str, object], signature_hex: str) -> "Envelope":
        return cls(key_id, _canonical(dict(payload)), signature_hex)

    def payload_dict(self) -> dict[str, object]:
        def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise CandidateError("signed envelope contains a duplicate JSON key")
                result[key] = value
            return result

        try:
            value = json.loads(self.payload.decode("utf-8"), object_pairs_hook=unique_pairs,
                               parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise CandidateError("signed envelope bytes are not valid canonical JSON") from exc
        if not isinstance(value, dict):
            raise CandidateError("signed envelope payload must be an object")
        if _canonical(value) != self.payload:
            raise CandidateError("signed envelope bytes are not canonical JSON")
        return value


@dataclass(frozen=True)
class TrustRoots:
    """Host-owned key maps; never load these from an approval/evidence payload."""

    governance_keys: Mapping[str, bytes]
    verifier_keys: Mapping[str, bytes]

    def __post_init__(self) -> None:
        object.__setattr__(self, "governance_keys", MappingProxyType(dict(self.governance_keys)))
        object.__setattr__(self, "verifier_keys", MappingProxyType(dict(self.verifier_keys)))

    def validate(self) -> None:
        if not self.governance_keys or not self.verifier_keys:
            raise CandidateError("both separately provisioned trust roles are required")
        if (set(self.governance_keys) & set(self.verifier_keys)
                or set(self.governance_keys.values()) & set(self.verifier_keys.values())):
            raise CandidateError("governance and evidence-verifier key IDs must be distinct")
        for key_map in (self.governance_keys, self.verifier_keys):
            for key_id, key in key_map.items():
                if not isinstance(key_id, str) or not key_id or not isinstance(key, bytes) or len(key) < 32:
                    raise CandidateError("invalid host trust key configuration")


@dataclass(frozen=True)
class CandidateEvent:
    sequence: int
    kind: str
    decision_id: str
    operation_id: str
    payload_sha256: str
    payload: bytes
    key_id: str
    signature_hex: str
    previous_candidate_sha256: str
    event_sha256: str
    evidence_bytes: bytes | None = None

    def payload_dict(self) -> dict[str, object]:
        return Envelope(self.key_id, self.payload, self.signature_hex).payload_dict()


@dataclass(frozen=True)
class Operation:
    operation_id: str
    begin_decision_id: str
    begin_payload_sha256: str
    state: str = "AUTHORIZED"
    finish_payload_sha256: str | None = None
    evidence_sha256: str | None = None
    module_path_sha256: str | None = None
    closure_manifest_sha256: str | None = None
    test_only_binding: bool = False
    reactivation_decision_id: str | None = None
    reactivation_payload_sha256: str | None = None


@dataclass(frozen=True)
class CaseState:
    task_id: str = TASK_ID
    issue_id: str = ISSUE_ID
    c6_run_id: str = C6_RUN_ID
    task_phase: str = "BLOCKED"
    next_stage: str | None = None
    issue_state: str = "WAIT_HUMAN"
    continuations_used: int = 1
    retries_remaining: int = 0
    gate_count: int = EXPECTED_GATE_COUNT
    gate_catalog_bytes: bytes = b""
    gate_catalog_sha256: str = GATE_CATALOG_SHA256
    contract_sha256: str = CONTRACT_SHA256
    task_state_file_sha256: str = TASK_STATE_FILE_SHA256
    original_history_anchor_sha256: str = _HISTORY_ANCHOR
    statuses: tuple[tuple[str, str], ...] = (
        ("PRIMARY_OUTCOME_STATUS", "UNKNOWN"),
        ("IMPLEMENTATION_STATUS", "ESCALATED"),
        ("CORE_ACCEPTANCE_STATUS", "NOT_RUN"),
        ("REQUIRED_VERIFICATION_STATUS", "NOT_RUN"),
        ("INDEPENDENT_ACCEPTANCE_STATUS", "PENDING"),
        ("TASK_CLOSURE_STATUS", "HIGH_REASONING_REVIEW_REQUIRED"),
    )
    accepted_gates: tuple[str, ...] = ()
    operation: Operation | None = None
    events: tuple[CandidateEvent, ...] = ()


@dataclass(frozen=True)
class OperationPermit:
    operation_id: str
    scope: str = "ORIGINAL_ISSUE_CRITERION_ONLY"
    denied_capabilities: tuple[str, ...] = DENIED_CAPABILITIES
    executable_command: None = None


@dataclass(frozen=True)
class HostContext:
    """Context supplied by an integration-owned trust adapter, never by a proof."""

    canonical_module_path_sha256: str | None = None
    test_only: bool = False
    live_binding_verified: bool = False

    def validate(self) -> None:
        if type(self.test_only) is not bool or type(self.live_binding_verified) is not bool:
            raise CandidateError("host context flags must be exact booleans")
        if (self.canonical_module_path_sha256 is not None
                and not _is_sha256(self.canonical_module_path_sha256)):
            raise CandidateError("host module-path anchor must be a lowercase SHA-256")


def state_fingerprint(state: CaseState) -> str:
    """Hash current candidate state; decision payloads cannot supply this hash."""
    return _sha256(_canonical({
        "frozen_binding_sha256": FROZEN_BINDING_SHA256,
        "task_id": state.task_id,
        "issue_id": state.issue_id,
        "c6_run_id": state.c6_run_id,
        "task_phase": state.task_phase,
        "next_stage": state.next_stage,
        "issue_state": state.issue_state,
        "continuations_used": state.continuations_used,
        "retries_remaining": state.retries_remaining,
        "gate_count": state.gate_count,
        "gate_catalog_sha256": state.gate_catalog_sha256,
        "gate_catalog_bytes_sha256": _sha256(state.gate_catalog_bytes),
        "contract_sha256": state.contract_sha256,
        "task_state_file_sha256": state.task_state_file_sha256,
        "original_history_anchor_sha256": state.original_history_anchor_sha256,
        "statuses": state.statuses,
        "accepted_gates": state.accepted_gates,
        "operation": None if state.operation is None else {
            "operation_id": state.operation.operation_id,
            "begin_decision_id": state.operation.begin_decision_id,
            "begin_payload_sha256": state.operation.begin_payload_sha256,
            "state": state.operation.state,
            "finish_payload_sha256": state.operation.finish_payload_sha256,
            "evidence_sha256": state.operation.evidence_sha256,
            "module_path_sha256": state.operation.module_path_sha256,
            "closure_manifest_sha256": state.operation.closure_manifest_sha256,
            "test_only_binding": state.operation.test_only_binding,
            "reactivation_decision_id": state.operation.reactivation_decision_id,
            "reactivation_payload_sha256": state.operation.reactivation_payload_sha256,
        },
        "events": [event.event_sha256 for event in state.events],
    }))


def _validate_state(state: CaseState, trust: TrustRoots | None = None,
                    host: HostContext | None = None, allow_test_only: bool = False) -> None:
    if not isinstance(state, CaseState):
        raise CandidateError("candidate state type is invalid")
    if (state.task_id, state.issue_id, state.c6_run_id) != (TASK_ID, ISSUE_ID, C6_RUN_ID):
        raise CandidateError("state is not the frozen original task/issue/c6 lineage")
    if (type(state.continuations_used) is not int or type(state.retries_remaining) is not int
            or state.continuations_used != 1 or state.retries_remaining != 0):
        raise CandidateError("consumed continuation and exhausted retry budget are immutable")
    if (type(state.gate_count) is not int or type(state.events) is not tuple
            or type(state.statuses) is not tuple or type(state.accepted_gates) is not tuple):
        raise CandidateError("state collections and gate count must use immutable exact types")
    if type(allow_test_only) is not bool:
        raise CandidateError("test-only opt-in must be an exact boolean")
    if host is not None:
        host.validate()
    if state.operation is None and not (state.task_phase == "BLOCKED" and state.next_stage is None
                                        and state.issue_state == "WAIT_HUMAN" and not state.events):
        raise CandidateError("only the frozen blocked WAIT_HUMAN baseline is valid before authorization")
    if state.gate_count != EXPECTED_GATE_COUNT or state.gate_catalog_sha256 != GATE_CATALOG_SHA256:
        raise CandidateError("original frozen 28-gate binding changed")
    if not isinstance(state.gate_catalog_bytes, bytes) or not state.gate_catalog_bytes:
        raise CandidateError("all frozen gate records are required")
    if not hmac.compare_digest(_sha256(state.gate_catalog_bytes), GATE_CATALOG_SHA256):
        raise CandidateError("gate record bytes or order differ from the frozen catalog")
    try:
        gates = json.loads(state.gate_catalog_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError("frozen gate catalog is not canonical UTF-8 JSON") from exc
    if not isinstance(gates, list) or len(gates) != EXPECTED_GATE_COUNT:
        raise CandidateError("frozen gate catalog must contain exactly 28 records")
    required_gate_fields = {"gate_id", "owner", "phase", "required", "reuse", "evidence_source",
                            "goal_criticality", "evidence_role", "closure_gate"}
    if any(not isinstance(gate, dict) or set(gate) != required_gate_fields for gate in gates):
        raise CandidateError("gate catalog fields differ from the nine-field frozen schema")
    canonical_gates = json.dumps(gates, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if canonical_gates != state.gate_catalog_bytes:
        raise CandidateError("gate catalog bytes are not canonical or ordered")
    if (state.contract_sha256 != CONTRACT_SHA256 or state.task_state_file_sha256 != TASK_STATE_FILE_SHA256
            or state.original_history_anchor_sha256 != _HISTORY_ANCHOR):
        raise CandidateError("original contract or history anchor changed")
    expected_statuses = (("PRIMARY_OUTCOME_STATUS", "UNKNOWN"),
                         ("IMPLEMENTATION_STATUS", "ESCALATED"),
                         ("CORE_ACCEPTANCE_STATUS", "NOT_RUN"),
                         ("REQUIRED_VERIFICATION_STATUS", "NOT_RUN"),
                         ("INDEPENDENT_ACCEPTANCE_STATUS", "PENDING"),
                         ("TASK_CLOSURE_STATUS", "HIGH_REASONING_REVIEW_REQUIRED"))
    if state.statuses != expected_statuses:
        raise CandidateError("known independent status projection changed or an unknown status was added")
    if state.accepted_gates != ():
        raise CandidateError("candidate recovery cannot accept, waive, or promote any original gate")
    previous = FROZEN_BINDING_SHA256
    authorized_operation_id: str | None = None
    expected_kinds = {1: "REMEDIATION_AUTHORIZED", 2: {"REMEDIATION_VERIFIED", "REMEDIATION_FAILED"},
                      3: "TASK_REACTIVATED_IMPLEMENT_ONLY"}
    for index, event in enumerate(state.events, 1):
        if not isinstance(event, CandidateEvent):
            raise CandidateError("candidate journal contains a mutable or invalid event")
        if (type(event.sequence) is not int or event.sequence != index
                or event.previous_candidate_sha256 != previous
                or not isinstance(event.payload, bytes)
                or (event.evidence_bytes is not None and not isinstance(event.evidence_bytes, bytes))):
            raise CandidateError("candidate event chain is discontinuous")
        allowed = expected_kinds.get(index)
        if allowed is None or event.kind not in (allowed if isinstance(allowed, set) else {allowed}):
            raise CandidateError("candidate event order or kind is invalid")
        expected = _event_digest(event.sequence, event.kind, event.decision_id, event.operation_id,
                                 event.payload_sha256, event.key_id, event.signature_hex,
                                 event.previous_candidate_sha256, event.evidence_bytes)
        if not hmac.compare_digest(event.event_sha256, expected):
            raise CandidateError("candidate event digest mismatch")
        if trust is None:
            raise CandidateError("signed candidate events require host trust roots")
        role_keys = trust.verifier_keys if event.sequence == 2 else trust.governance_keys
        required_fields = _evidence_fields() if event.sequence == 2 else (
            set(_base_payload("", "", "")) | {"operation_id", "scope"})
        verified, payload_sha = _verify(Envelope(event.key_id, event.payload, event.signature_hex),
                                        role_keys, required_fields)
        if (not hmac.compare_digest(payload_sha, event.payload_sha256)
                or verified.get("decision_id", verified.get("attestation_id")) != event.decision_id
                or verified.get("operation_id") != event.operation_id):
            raise CandidateError("candidate journal signature does not bind its event")
        if event.sequence == 1:
            authorized_operation_id = verified.get("operation_id")
        elif verified.get("operation_id") != authorized_operation_id or event.operation_id != authorized_operation_id:
            raise CandidateError("later event is not bound to the originally authorized operation")
        expected_action = {
            "REMEDIATION_AUTHORIZED": "AUTHORIZE_BOUNDED_REMEDIATION",
            "REMEDIATION_VERIFIED": "ATTEST_ORIGINAL_CRITERION_EVIDENCE",
            "REMEDIATION_FAILED": "ATTEST_ORIGINAL_CRITERION_EVIDENCE",
            "TASK_REACTIVATED_IMPLEMENT_ONLY": "REACTIVATE_ORIGINAL_TASK",
        }[event.kind]
        if verified.get("action") != expected_action:
            raise CandidateError("candidate journal signature action differs from event kind")
        if event.sequence == 1:
            _validate_payload_constants(verified, expected_action, state_fingerprint(_baseline_state(state)))
            if verified.get("scope") != "ORIGINAL_ISSUE_CRITERION_ONLY":
                raise CandidateError("authorization scope differs from the frozen original issue")
        elif event.sequence == 2:
            if state.operation is None:
                raise CandidateError("completion event lacks an operation")
            pre = _pre_completion_state(state)
            _validate_evidence_binding(verified, pre)
            if event.evidence_bytes is None:
                raise CandidateError("completion event must retain the attested raw proof bytes")
            raw_sha = _sha256(event.evidence_bytes)
            if verified.get("raw_evidence_sha256") != raw_sha or verified.get("raw_evidence_length") != len(event.evidence_bytes):
                raise CandidateError("journal evidence bytes do not match the signed verifier attestation")
            if event.kind == "REMEDIATION_VERIFIED":
                if host is None:
                    raise CandidateError("host context is required to validate a completion event")
                if verified.get("test_only_context") is not host.test_only:
                    raise CandidateError("attestation test-only context differs from host context")
                module_sha, closure_sha = _validate_runtime_binding_proof(
                    event.evidence_bytes, event.operation_id, host, allow_test_only=allow_test_only)
                if (verified.get("verification_result") != "VERIFIED"
                        or verified.get("module_path_sha256") != module_sha
                        or verified.get("closure_manifest_sha256") != closure_sha):
                    raise CandidateError("attestation does not bind the parsed proof")
            elif verified.get("verification_result") != "REJECTED":
                raise CandidateError("failed event requires an authenticated rejection")
        elif event.sequence == 3:
            pre = _pre_reactivation_state(state)
            _validate_payload_constants(verified, expected_action, state_fingerprint(pre))
            if verified.get("scope") != "IMPLEMENT_ONLY_AFTER_VERIFIED_RESOLUTION":
                raise CandidateError("reactivation scope differs from remaining IMPLEMENT eligibility")
        previous = event.event_sha256
    if state.operation is None and state.events:
        raise CandidateError("candidate events require their single bounded operation")
    if state.operation is not None:
        if not state.events or state.events[0].kind != "REMEDIATION_AUTHORIZED":
            raise CandidateError("operation has no append-only authorization event")
        first = state.events[0].payload_dict()
        if (first.get("operation_id") != state.operation.operation_id
                or first.get("decision_id") != state.operation.begin_decision_id
                or state.events[0].payload_sha256 != state.operation.begin_payload_sha256):
            raise CandidateError("operation does not match its authenticated authorization event")
    if state.operation is not None:
        count = len(state.events)
        operation = state.operation
        first_payload = state.events[0].payload_dict()
        expected_operation = Operation(
            operation_id=str(first_payload.get("operation_id")),
            begin_decision_id=str(first_payload.get("decision_id")),
            begin_payload_sha256=state.events[0].payload_sha256,
        )
        if count >= 2:
            second = state.events[1]
            second_payload = second.payload_dict()
            if second.kind == "REMEDIATION_VERIFIED":
                expected_operation = replace(
                    expected_operation, state="VERIFIED",
                    finish_payload_sha256=second.payload_sha256,
                    evidence_sha256=str(second_payload.get("raw_evidence_sha256")),
                    module_path_sha256=str(second_payload.get("module_path_sha256")),
                    closure_manifest_sha256=str(second_payload.get("closure_manifest_sha256")),
                    test_only_binding=bool(second_payload.get("test_only_context")),
                )
            else:
                expected_operation = replace(
                    expected_operation, state="FAILED",
                    finish_payload_sha256=second.payload_sha256,
                    evidence_sha256=str(second_payload.get("raw_evidence_sha256")),
                )
        if count == 3:
            third = state.events[2]
            expected_operation = replace(
                expected_operation,
                reactivation_decision_id=third.payload_dict().get("decision_id"),
                reactivation_payload_sha256=third.payload_sha256,
            )
        if operation != expected_operation:
            raise CandidateError("operation state is not reconstructed from authenticated journal transitions")
        if operation.state == "AUTHORIZED" and not (count == 1 and state.issue_state == "WAIT_HUMAN"
                                                       and state.task_phase == "BLOCKED" and state.next_stage is None):
            raise CandidateError("authorized operation must leave issue and task blocked")
        if operation.state == "VERIFIED" and not (count in {2, 3} and state.issue_state == "RESOLVED"
                                                      and operation.finish_payload_sha256 and operation.evidence_sha256
                                                      and operation.module_path_sha256 and operation.closure_manifest_sha256):
            raise CandidateError("issue resolution requires verified original-criterion evidence")
        if operation.state == "FAILED" and not (count == 2 and state.issue_state == "WAIT_HUMAN"
                                                   and state.task_phase == "BLOCKED" and state.next_stage is None):
            raise CandidateError("failed bounded operation must remain blocked and terminal")
        if count == 2 and operation.state in {"VERIFIED", "FAILED"}:
            if state.task_phase != "BLOCKED" or state.next_stage is not None:
                raise CandidateError("issue verification must not reactivate the task")
        if count == 3 and not (operation.state == "VERIFIED" and operation.reactivation_decision_id
                               and state.issue_state == "RESOLVED" and state.task_phase == "IN_PROGRESS"
                               and state.next_stage == "IMPLEMENT"):
            raise CandidateError("reactivation may only expose the remaining IMPLEMENT stage")
        if count >= 2:
            second = state.events[1]
            second_payload = second.payload_dict()
            if (operation.finish_payload_sha256 != second.payload_sha256
                    or operation.evidence_sha256 != second_payload.get("raw_evidence_sha256")):
                raise CandidateError("operation completion metadata differs from the authenticated event")
            if second.kind == "REMEDIATION_VERIFIED":
                if state.issue_state != "RESOLVED" or operation.state != "VERIFIED":
                    raise CandidateError("verified event must resolve only the original issue")
            elif state.issue_state != "WAIT_HUMAN" or operation.state != "FAILED":
                raise CandidateError("failed event must preserve WAIT_HUMAN")
        if count == 3:
            third_payload = state.events[2].payload_dict()
            if (operation.reactivation_decision_id != third_payload.get("decision_id")
                    or operation.reactivation_payload_sha256 != state.events[2].payload_sha256):
                raise CandidateError("reactivation metadata differs from its authenticated event")


def _event_digest(sequence: int, kind: str, decision_id: str, operation_id: str,
                  payload_sha256: str, key_id: str, signature_hex: str,
                  previous_sha256: str, evidence_bytes: bytes | None = None) -> str:
    return _sha256(_canonical({
        "sequence": sequence, "kind": kind, "decision_id": decision_id,
        "operation_id": operation_id, "payload_sha256": payload_sha256,
        "key_id": key_id, "signature_hex": signature_hex,
        "previous_candidate_sha256": previous_sha256,
        "evidence_sha256": None if evidence_bytes is None else _sha256(evidence_bytes),
    }))


def _append(state: CaseState, kind: str, decision_id: str, operation_id: str,
            envelope: Envelope, evidence_bytes: bytes | None = None) -> tuple[CandidateEvent, ...]:
    previous = state.events[-1].event_sha256 if state.events else FROZEN_BINDING_SHA256
    sequence = len(state.events) + 1
    payload = envelope.payload_dict()
    payload_sha256 = _sha256(_canonical(payload))
    digest = _event_digest(sequence, kind, decision_id, operation_id, payload_sha256,
                           envelope.key_id, envelope.signature_hex, previous, evidence_bytes)
    return state.events + (CandidateEvent(sequence, kind, decision_id, operation_id,
                                          payload_sha256, envelope.payload, envelope.key_id,
                                          envelope.signature_hex, previous, digest, evidence_bytes),)


def _verify(envelope: Envelope, keyring: Mapping[str, bytes], required: set[str]) -> tuple[dict[str, object], str]:
    payload = envelope.payload_dict()
    if set(payload) != required:
        raise CandidateError("signed envelope has missing or unexpected fields")
    key = keyring.get(envelope.key_id)
    if key is None:
        raise CandidateError("signer is not in the host-owned trust role")
    expected = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, envelope.signature_hex):
        raise CandidateError("signed envelope verification failed")
    return payload, _sha256(_canonical(payload))


def sign_for_test(key_id: str, payload: Mapping[str, object], key: bytes) -> Envelope:
    """Test helper; production integrations must use externally provisioned host keys."""
    signature = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
    return Envelope.from_mapping(key_id, payload, signature)


def _base_payload(action: str, decision_id: str, expected_state_sha256: str) -> dict[str, object]:
    return {
        "version": 1,
        "action": action,
        "decision_id": decision_id,
        "task_id": TASK_ID,
        "issue_id": ISSUE_ID,
        "c6_run_id": C6_RUN_ID,
        "frozen_binding_sha256": FROZEN_BINDING_SHA256,
        "expected_state_sha256": expected_state_sha256,
        "original_criterion_sha256": ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": C6_PERMISSION_CRITERION_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "task_state_file_sha256": TASK_STATE_FILE_SHA256,
        "gate_catalog_sha256": GATE_CATALOG_SHA256,
        "task_root_path_sha256": TASK_ROOT_PATH_SHA256,
        "original_history_anchor_sha256": _HISTORY_ANCHOR,
        "continuations_used": 1,
        "retries_remaining": 0,
        "denied_capabilities": DENIED_CAPABILITIES,
    }


def _validate_signed_binding(payload: Mapping[str, object], action: str, state: CaseState) -> None:
    expected = _base_payload(action, payload.get("decision_id", ""), state_fingerprint(state))
    _validate_payload_constants(payload, action, expected["expected_state_sha256"])
    if payload.get("expected_state_sha256") != state_fingerprint(state):
        raise CandidateError("signed decision does not bind to the current state")


def _validate_payload_constants(payload: Mapping[str, object], action: str, expected_state_sha256: str) -> None:
    expected = _base_payload(action, payload.get("decision_id", ""), expected_state_sha256)
    for key, value in expected.items():
        if _canonical(payload.get(key)) != _canonical(value):
            raise CandidateError("signed decision binding differs from frozen lineage/current state")
    if not isinstance(payload.get("decision_id"), str) or not payload["decision_id"]:
        raise CandidateError("decision ID is required")
    if action in {"AUTHORIZE_BOUNDED_REMEDIATION", "REACTIVATE_ORIGINAL_TASK"}:
        operation_id = payload.get("operation_id")
        if (not isinstance(operation_id, str) or not operation_id
                or operation_id in {TASK_ID, ISSUE_ID, C6_RUN_ID}):
            raise CandidateError("new bounded operation ID must be distinct from the original lineage IDs")


def _baseline_state(state: CaseState) -> CaseState:
    return replace(state, task_phase="BLOCKED", next_stage=None, issue_state="WAIT_HUMAN",
                   operation=None, events=())


def _pre_completion_state(state: CaseState) -> CaseState:
    first = state.events[0]
    payload = first.payload_dict()
    operation = Operation(str(payload["operation_id"]), str(payload["decision_id"]), first.payload_sha256)
    return replace(state, task_phase="BLOCKED", next_stage=None, issue_state="WAIT_HUMAN",
                   operation=operation, events=(first,))


def _pre_reactivation_state(state: CaseState) -> CaseState:
    first, second = state.events[:2]
    begin = first.payload_dict()
    finish = second.payload_dict()
    operation = Operation(
        operation_id=str(begin["operation_id"]),
        begin_decision_id=str(begin["decision_id"]),
        begin_payload_sha256=first.payload_sha256,
        state="VERIFIED",
        finish_payload_sha256=second.payload_sha256,
        evidence_sha256=str(finish["raw_evidence_sha256"]),
        module_path_sha256=str(finish["module_path_sha256"]),
        closure_manifest_sha256=str(finish["closure_manifest_sha256"]),
        test_only_binding=bool(finish["test_only_context"]),
    )
    return replace(state, task_phase="BLOCKED", next_stage=None, issue_state="RESOLVED",
                   operation=operation, events=(first, second))


def initial_state(gate_catalog_bytes: bytes) -> CaseState:
    """Construct the pinned blocked snapshot from exact canonical gate bytes."""
    state = CaseState(gate_catalog_bytes=gate_catalog_bytes)
    _validate_state(state)
    return state


def authorize_remediation(state: CaseState, decision: Envelope, trust: TrustRoots,
                          host: HostContext | None = None, *,
                          allow_test_only: bool = False) -> tuple[CaseState, OperationPermit | None]:
    """Append one bounded permit; issue and task remain blocked and unresolved."""
    trust.validate()
    _validate_state(state, trust, host, allow_test_only)
    if state.operation is not None:
        prior = state.operation
        payload, payload_sha = _verify(decision, trust.governance_keys, set(_base_payload("", "", "")) | {"operation_id", "scope"})
        if (payload["action"] == "AUTHORIZE_BOUNDED_REMEDIATION"
                and payload["decision_id"] == prior.begin_decision_id
                and payload_sha == prior.begin_payload_sha256):
            _validate_signed_binding(payload, "AUTHORIZE_BOUNDED_REMEDIATION", _baseline_state(state))
            if payload.get("operation_id") != prior.operation_id or payload.get("scope") != "ORIGINAL_ISSUE_CRITERION_ONLY":
                raise CandidateError("authorization replay differs from the original bounded decision")
            if prior.state == "AUTHORIZED" and state.issue_state == "WAIT_HUMAN" and state.task_phase == "BLOCKED":
                return state, OperationPermit(prior.operation_id)
            return state, None
        raise CandidateError("the exhausted root permits one operation; it cannot be reauthorized")
    if state.task_phase != "BLOCKED" or state.next_stage is not None or state.issue_state != "WAIT_HUMAN":
        raise CandidateError("only the frozen blocked WAIT_HUMAN state can begin remediation")
    expected_fields = set(_base_payload("", "", "")) | {"operation_id", "scope"}
    payload, payload_sha = _verify(decision, trust.governance_keys, expected_fields)
    if payload["action"] != "AUTHORIZE_BOUNDED_REMEDIATION" or payload["scope"] != "ORIGINAL_ISSUE_CRITERION_ONLY":
        raise CandidateError("authorization scope does not match the bounded original issue")
    _validate_signed_binding(payload, "AUTHORIZE_BOUNDED_REMEDIATION", state)
    operation_id = payload["operation_id"]
    if not isinstance(operation_id, str) or not operation_id:
        raise CandidateError("operation ID is required")
    decision_id = payload["decision_id"]
    if not isinstance(decision_id, str) or not decision_id:
        raise CandidateError("decision ID is required")
    events = _append(state, "REMEDIATION_AUTHORIZED", decision_id, operation_id, decision)
    authorized = replace(state, operation=Operation(operation_id, decision_id, payload_sha), events=events)
    _validate_state(authorized, trust)
    return authorized, OperationPermit(operation_id)


def _evidence_fields() -> set[str]:
    return {
        "version", "action", "attestation_id", "task_id", "issue_id", "c6_run_id",
        "frozen_binding_sha256", "expected_state_sha256", "contract_sha256",
        "task_state_file_sha256", "gate_catalog_sha256", "original_history_anchor_sha256",
        "task_root_path_sha256", "continuations_used", "retries_remaining", "denied_capabilities",
        "operation_id", "original_criterion_sha256", "c6_permission_criterion_sha256",
        "raw_evidence_sha256", "raw_evidence_length", "scope", "module_path_sha256",
        "closure_manifest_sha256", "producer_receipt_sha256",
        "test_only_context",
        "verification_result",
    }


def _validate_evidence_binding(payload: Mapping[str, object], state: CaseState) -> None:
    expected = {
        "version": 1,
        "action": "ATTEST_ORIGINAL_CRITERION_EVIDENCE",
        "task_id": TASK_ID,
        "issue_id": ISSUE_ID,
        "c6_run_id": C6_RUN_ID,
        "operation_id": state.operation.operation_id if state.operation is not None else None,
        "frozen_binding_sha256": FROZEN_BINDING_SHA256,
        "expected_state_sha256": state_fingerprint(state),
        "contract_sha256": CONTRACT_SHA256,
        "task_state_file_sha256": TASK_STATE_FILE_SHA256,
        "gate_catalog_sha256": GATE_CATALOG_SHA256,
        "original_history_anchor_sha256": _HISTORY_ANCHOR,
        "task_root_path_sha256": TASK_ROOT_PATH_SHA256,
        "continuations_used": 1,
        "retries_remaining": 0,
        "denied_capabilities": DENIED_CAPABILITIES,
        "original_criterion_sha256": ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": C6_PERMISSION_CRITERION_SHA256,
        "scope": "VERIFY_ORIGINAL_RUNTIME_BINDING_ONLY",
    }
    for key, value in expected.items():
        if _canonical(payload.get(key)) != _canonical(value):
            raise CandidateError("evidence attestation binding differs from frozen case or current state")
    if not isinstance(payload.get("attestation_id"), str) or not payload["attestation_id"]:
        raise CandidateError("attestation ID is required")
    for key in ("raw_evidence_sha256", "module_path_sha256", "closure_manifest_sha256", "producer_receipt_sha256"):
        if not _is_sha256(payload.get(key)):
            raise CandidateError("evidence attestation lacks a required digest")
    if type(payload.get("raw_evidence_length")) is not int or payload["raw_evidence_length"] <= 0:
        raise CandidateError("evidence attestation raw length is invalid")
    if not isinstance(payload.get("test_only_context"), bool):
        raise CandidateError("evidence attestation host-context flag is invalid")
    if payload.get("verification_result") not in {"VERIFIED", "REJECTED"}:
        raise CandidateError("evidence verifier result is unknown")


def _validate_runtime_binding_proof(raw: bytes, operation_id: str, host: HostContext,
                                    *, allow_test_only: bool = False) -> tuple[str, str]:
    if host.test_only and not allow_test_only:
        raise CandidateError("test-only host bindings cannot authorize a real transition")
    if not host.test_only and not host.live_binding_verified:
        raise CandidateError("real host binding has not been independently verified")
    if host.canonical_module_path_sha256 is None:
        raise CandidateError("canonical runtime module path is unbound; activation remains blocked")
    if not isinstance(host.canonical_module_path_sha256, str) or len(host.canonical_module_path_sha256) != 64:
        raise CandidateError("host runtime binding is unavailable")
    try:
        proof = json.loads(raw.decode("utf-8"), parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError("runtime binding proof must be UTF-8 JSON") from exc
    except ValueError as exc:
        raise CandidateError("runtime binding proof cannot contain NaN or Infinity") from exc
    expected_fields = {
        "schema", "task_id", "issue_id", "c6_run_id", "operation_id",
        "original_criterion_sha256", "c6_permission_criterion_sha256", "contract_sha256",
        "task_root_path_sha256", "module_paths", "module_path_sha256", "closure_files",
        "closure_manifest_sha256", "closure_complete", "language_checks",
    }
    if not isinstance(proof, dict) or set(proof) != expected_fields:
        raise CandidateError("runtime binding proof fields are incomplete or unexpected")
    fixed = {
        "schema": "g0-runtime-binding-proof-v1",
        "task_id": TASK_ID,
        "issue_id": ISSUE_ID,
        "c6_run_id": C6_RUN_ID,
        "operation_id": operation_id,
        "original_criterion_sha256": ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": C6_PERMISSION_CRITERION_SHA256,
        "contract_sha256": CONTRACT_SHA256,
        "task_root_path_sha256": TASK_ROOT_PATH_SHA256,
        "closure_complete": True,
    }
    for key, value in fixed.items():
        if proof.get(key) != value:
            raise CandidateError("runtime proof does not match the original bounded criterion")
    if proof.get("closure_complete") is not True:
        raise CandidateError("runtime task-module closure must be explicitly complete")
    if not _is_sha256(host.canonical_module_path_sha256):
        raise CandidateError("host runtime module-path anchor is malformed")
    if host.canonical_module_path_sha256 != proof.get("module_path_sha256"):
        raise CandidateError("module path does not match the host-anchored runtime binding")
    module_paths = proof["module_paths"]
    if not isinstance(module_paths, list) or not module_paths:
        raise CandidateError("full runtime module path list is required")
    normalized_paths = []
    for value in module_paths:
        if not _safe_relative_module_path(value):
            raise CandidateError("module path escapes the frozen task-root boundary")
        normalized_paths.append(value)
    if normalized_paths != sorted(set(normalized_paths)):
        raise CandidateError("module paths must be unique and canonically ordered")
    module_sha = _sha256(_canonical(normalized_paths))
    if module_sha != proof["module_path_sha256"]:
        raise CandidateError("module path binding digest mismatch")
    closure = proof["closure_files"]
    if not isinstance(closure, list) or not closure:
        raise CandidateError("full runtime closure manifest is required")
    closure_paths = []
    for item in closure:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "length"}:
            raise CandidateError("closure manifest record schema is invalid")
        path, digest, length = item["path"], item["sha256"], item["length"]
        if (not _safe_relative_module_path(path) or not _is_sha256(digest)
                or type(length) is not int or length <= 0):
            raise CandidateError("closure manifest contains an invalid path or file digest")
        closure_paths.append(path)
    if closure_paths != sorted(set(closure_paths)) or not set(module_paths).issubset(closure_paths):
        raise CandidateError("closure manifest omits or reorders task modules")
    closure_sha = _sha256(_canonical(closure))
    if closure_sha != proof["closure_manifest_sha256"]:
        raise CandidateError("full runtime closure manifest digest mismatch")
    language_checks = proof["language_checks"]
    if not isinstance(language_checks, list) or len(language_checks) != 3:
        raise CandidateError("exact JavaScript, Python, and Swift checks are required")
    expected_languages = ("javascript", "python", "swift")
    expected_check_fields = {"language", "contract_sha256", "task_root_path_sha256",
                             "module_path_sha256", "closure_manifest_sha256", "result"}
    for check, language in zip(language_checks, expected_languages):
        if not isinstance(check, dict) or set(check) != expected_check_fields:
            raise CandidateError("language check has missing or unexpected fields")
        if (check["language"] != language or check["contract_sha256"] != CONTRACT_SHA256
                or check["task_root_path_sha256"] != TASK_ROOT_PATH_SHA256
                or check["module_path_sha256"] != module_sha
                or check["closure_manifest_sha256"] != closure_sha or check["result"] != "AGREES"):
            raise CandidateError("JavaScript, Python, and Swift do not agree on the same current binding")
    if _canonical(proof) != raw:
        raise CandidateError("runtime proof JSON must use canonical encoding")
    return module_sha, closure_sha


def complete_remediation(state: CaseState, attestation: Envelope, raw_evidence: bytes,
                         trust: TrustRoots, host: HostContext, *,
                         allow_test_only: bool = False) -> CaseState:
    """Verify raw proof bytes and a role-separated attestation; never promotes Task status."""
    trust.validate()
    _validate_state(state, trust, host, allow_test_only)
    if not isinstance(raw_evidence, bytes) or not raw_evidence:
        raise CandidateError("raw remediation evidence bytes are required")
    payload, payload_sha = _verify(attestation, trust.verifier_keys, _evidence_fields())
    actual_sha = _sha256(raw_evidence)
    if payload["action"] != "ATTEST_ORIGINAL_CRITERION_EVIDENCE":
        raise CandidateError("verifier attestation action is invalid")
    if state.operation is None:
        raise CandidateError("evidence attestation has no bounded operation")
    _validate_evidence_binding(payload, _pre_completion_state(state))
    if (payload["task_id"], payload["issue_id"], payload["c6_run_id"]) != (TASK_ID, ISSUE_ID, C6_RUN_ID):
        raise CandidateError("evidence attestation is not bound to the original lineage")
    if state.operation is None or payload["operation_id"] != state.operation.operation_id:
        raise CandidateError("evidence attestation does not identify the authorized operation")
    if payload["original_criterion_sha256"] != ORIGINAL_CRITERION_SHA256:
        raise CandidateError("evidence does not address the original root issue criterion")
    if payload["c6_permission_criterion_sha256"] != C6_PERMISSION_CRITERION_SHA256:
        raise CandidateError("historical c6 permission criterion binding changed")
    if payload["raw_evidence_sha256"] != actual_sha or payload["raw_evidence_length"] != len(raw_evidence):
        raise CandidateError("supplied raw evidence bytes do not match the signed attestation")
    operation = state.operation
    if operation.state in {"VERIFIED", "FAILED"}:
        if payload_sha == operation.finish_payload_sha256 and actual_sha == operation.evidence_sha256:
            return state
        raise CandidateError("terminal remediation cannot be replayed with different evidence")
    if operation.state != "AUTHORIZED" or state.issue_state != "WAIT_HUMAN" or state.task_phase != "BLOCKED":
        raise CandidateError("remediation completion requires the authorized blocked state")
    if payload["verification_result"] == "REJECTED":
        event_id = payload["attestation_id"]
        events = _append(state, "REMEDIATION_FAILED", event_id, operation.operation_id, attestation, raw_evidence)
        failed = replace(operation, state="FAILED", finish_payload_sha256=payload_sha,
                         evidence_sha256=actual_sha)
        updated = replace(state, operation=failed, events=events)
        _validate_state(updated, trust, host, allow_test_only)
        return updated
    module_sha, closure_sha = _validate_runtime_binding_proof(
        raw_evidence, state.operation.operation_id, host, allow_test_only=allow_test_only)
    if payload["module_path_sha256"] != module_sha or payload["closure_manifest_sha256"] != closure_sha:
        raise CandidateError("verifier attestation does not bind the parsed runtime proof")
    event_kind = "REMEDIATION_VERIFIED"
    attestation_id = payload["attestation_id"]
    if not isinstance(attestation_id, str) or not attestation_id:
        raise CandidateError("attestation ID is required")
    events = _append(state, event_kind, attestation_id, operation.operation_id, attestation, raw_evidence)
    updated_operation = replace(operation, state="VERIFIED", finish_payload_sha256=payload_sha,
                                evidence_sha256=actual_sha, module_path_sha256=module_sha,
                                closure_manifest_sha256=closure_sha,
                                test_only_binding=host.test_only)
    updated = replace(state, issue_state="RESOLVED",
                      operation=updated_operation, events=events)
    _validate_state(updated, trust, host, allow_test_only)
    return updated
def reactivate_task(state: CaseState, decision: Envelope, trust: TrustRoots, host: HostContext,
                    *, allow_test_only: bool = False) -> CaseState:
    """Separately authorize eligibility for the remaining IMPLEMENT stage only."""
    trust.validate()
    _validate_state(state, trust, host, allow_test_only)
    fields = set(_base_payload("", "", "")) | {"operation_id", "scope"}
    payload, payload_sha = _verify(decision, trust.governance_keys, fields)
    if payload["action"] != "REACTIVATE_ORIGINAL_TASK" or payload["scope"] != "IMPLEMENT_ONLY_AFTER_VERIFIED_RESOLUTION":
        raise CandidateError("reactivation authority scope is invalid")
    if state.operation is None or payload["operation_id"] != state.operation.operation_id:
        raise CandidateError("reactivation must bind the verified remediation operation")
    if state.task_phase == "IN_PROGRESS" and state.next_stage == "IMPLEMENT":
        if (state.operation.reactivation_decision_id == payload["decision_id"]
                and state.operation.reactivation_payload_sha256 == payload_sha):
            _validate_signed_binding(payload, "REACTIVATE_ORIGINAL_TASK", _pre_reactivation_state(state))
            return state
        raise CandidateError("reactivation already occurred under a different decision")
    _validate_signed_binding(payload, "REACTIVATE_ORIGINAL_TASK", state)
    if payload["expected_state_sha256"] != state_fingerprint(state):
        raise CandidateError("reactivation is not bound to current resolved state")
    if state.issue_state != "RESOLVED" or state.operation.state != "VERIFIED":
        raise CandidateError("task cannot reactivate before original issue evidence is verified")
    if state.continuations_used != 1 or state.retries_remaining != 0:
        raise CandidateError("reactivation cannot reset or consume an additional budget")
    decision_id = payload["decision_id"]
    if not isinstance(decision_id, str) or not decision_id:
        raise CandidateError("reactivation decision ID is required")
    events = _append(state, "TASK_REACTIVATED_IMPLEMENT_ONLY", decision_id,
                     state.operation.operation_id, decision)
    operation = replace(state.operation, reactivation_decision_id=decision_id,
                        reactivation_payload_sha256=payload_sha)
    updated = replace(state, task_phase="IN_PROGRESS", next_stage="IMPLEMENT",
                      operation=operation, events=events)
    _validate_state(updated, trust, host, allow_test_only)
    return updated
