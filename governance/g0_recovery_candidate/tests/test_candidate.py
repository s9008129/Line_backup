from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import unittest

from governance.g0_recovery_candidate import candidate as c


GOV_KEY = b"g" * 32
VER_KEY = b"v" * 32
TRUST = c.TrustRoots({"governance-1": GOV_KEY}, {"verifier-1": VER_KEY})
TEST_HOST = c.HostContext(canonical_module_path_sha256=None, test_only=True)
Q = c.TASK_ROOT_RELATIVE


def h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def gate_bytes() -> bytes:
    path = Path(__file__).parent / "fixtures" / "gate_catalog.json"
    return json.dumps(json.loads(path.read_text()), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def base(action: str, decision_id: str, state: c.CaseState, **extra: object) -> dict[str, object]:
    payload = c._base_payload(action, decision_id, c.state_fingerprint(state))
    payload.update(extra)
    return payload


def authorize(state: c.CaseState | None = None) -> tuple[c.CaseState, c.OperationPermit]:
    state = state or c.initial_state(gate_bytes())
    payload = base("AUTHORIZE_BOUNDED_REMEDIATION", "decision-1", state,
                   operation_id="operation-1", scope="ORIGINAL_ISSUE_CRITERION_ONLY")
    updated, permit = c.authorize_remediation(state, c.sign_for_test("governance-1", payload, GOV_KEY), TRUST)
    assert permit is not None
    return updated, permit


def make_proof(operation_id: str) -> tuple[bytes, str, str]:
    paths = [f"{Q}/runtime/module.js", f"{Q}/runtime/module.py", f"{Q}/runtime/module.swift"]
    module_sha = h(canonical(paths))
    closure = [{"path": path, "sha256": h(path.encode()), "length": len(path)} for path in paths]
    closure_sha = h(canonical(closure))
    proof = {
        "schema": "g0-runtime-binding-proof-v1",
        "task_id": c.TASK_ID,
        "issue_id": c.ISSUE_ID,
        "c6_run_id": c.C6_RUN_ID,
        "operation_id": operation_id,
        "original_criterion_sha256": c.ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": c.C6_PERMISSION_CRITERION_SHA256,
        "contract_sha256": c.CONTRACT_SHA256,
        "task_root_path_sha256": c.TASK_ROOT_PATH_SHA256,
        "module_paths": paths,
        "module_path_sha256": module_sha,
        "closure_files": closure,
        "closure_manifest_sha256": closure_sha,
        "closure_complete": True,
        "language_checks": [
            {"language": language, "contract_sha256": c.CONTRACT_SHA256,
             "task_root_path_sha256": c.TASK_ROOT_PATH_SHA256, "module_path_sha256": module_sha,
             "closure_manifest_sha256": closure_sha, "result": "AGREES"}
            for language in ("javascript", "python", "swift")
        ],
    }
    return canonical(proof), module_sha, closure_sha


def finish(state: c.CaseState, *, raw: bytes | None = None, host: c.HostContext = TEST_HOST,
           result: str = "VERIFIED") -> c.CaseState:
    raw, module_sha, closure_sha = (raw, None, None) if raw is not None else make_proof(state.operation.operation_id)
    if module_sha is None:
        try:
            proof = json.loads(raw)
            module_sha, closure_sha = proof["module_path_sha256"], proof["closure_manifest_sha256"]
        except (UnicodeDecodeError, json.JSONDecodeError):
            module_sha, closure_sha = h(b"rejected module binding"), h(b"rejected closure")
    if host.test_only and host.canonical_module_path_sha256 is None:
        host = c.HostContext(canonical_module_path_sha256=module_sha, test_only=True)
    payload = {
        "version": 1, "action": "ATTEST_ORIGINAL_CRITERION_EVIDENCE", "attestation_id": "attestation-1",
        "task_id": c.TASK_ID, "issue_id": c.ISSUE_ID, "c6_run_id": c.C6_RUN_ID,
        "frozen_binding_sha256": c.FROZEN_BINDING_SHA256,
        "expected_state_sha256": c.state_fingerprint(c._pre_completion_state(state)),
        "contract_sha256": c.CONTRACT_SHA256, "task_state_file_sha256": c.TASK_STATE_FILE_SHA256,
        "gate_catalog_sha256": c.GATE_CATALOG_SHA256,
        "original_history_anchor_sha256": c._HISTORY_ANCHOR,
        "task_root_path_sha256": c.TASK_ROOT_PATH_SHA256,
        "continuations_used": 1, "retries_remaining": 0,
        "denied_capabilities": c.DENIED_CAPABILITIES,
        "operation_id": state.operation.operation_id,
        "original_criterion_sha256": c.ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": c.C6_PERMISSION_CRITERION_SHA256,
        "raw_evidence_sha256": h(raw), "raw_evidence_length": len(raw),
        "scope": "VERIFY_ORIGINAL_RUNTIME_BINDING_ONLY",
        "module_path_sha256": module_sha, "closure_manifest_sha256": closure_sha,
        "producer_receipt_sha256": h(b"new-operation producer receipt"),
        "test_only_context": host.test_only,
        "verification_result": result,
    }
    signed = c.sign_for_test("verifier-1", payload, VER_KEY)
    return c.complete_remediation(state, signed, raw, TRUST, host, allow_test_only=True)


class CandidateTransitionsTest(unittest.TestCase):
  def test_no_governance_authority_keeps_original_issue_blocked(self):
    state = c.initial_state(gate_bytes())
    bad = c.sign_for_test("untrusted", base("AUTHORIZE_BOUNDED_REMEDIATION", "d", state,
        operation_id="operation-1", scope="ORIGINAL_ISSUE_CRITERION_ONLY"), b"x" * 32)
    with self.assertRaises(c.CandidateError):
        c.authorize_remediation(state, bad, TRUST)
    self.assertEqual((state.issue_state, state.task_phase), ("WAIT_HUMAN", "BLOCKED"))
    self.assertEqual((state.continuations_used, state.retries_remaining), (1, 0))


  def test_authority_only_creates_one_non_executable_permit_and_replay_is_idempotent(self):
    state = c.initial_state(gate_bytes())
    payload = base("AUTHORIZE_BOUNDED_REMEDIATION", "decision-1", state,
                   operation_id="operation-1", scope="ORIGINAL_ISSUE_CRITERION_ONLY")
    signed = c.sign_for_test("governance-1", payload, GOV_KEY)
    begun, permit = c.authorize_remediation(state, signed, TRUST)
    replay, same_permit = c.authorize_remediation(begun, signed, TRUST)
    self.assertEqual(replay, begun)
    self.assertEqual(same_permit, permit)
    self.assertIsNone(permit.executable_command)
    self.assertEqual((begun.issue_state, begun.task_phase), ("WAIT_HUMAN", "BLOCKED"))
    self.assertEqual((begun.continuations_used, begun.retries_remaining, len(begun.events)), (1, 0, 1))


  def test_wrong_lineage_or_scope_is_rejected_even_with_valid_governance_signature(self):
    state = c.initial_state(gate_bytes())
    for operation_id, issue_id in (("operation-1", "another-issue"), ("", c.ISSUE_ID),
                                   (c.C6_RUN_ID, c.ISSUE_ID), (c.TASK_ID, c.ISSUE_ID),
                                   (c.ISSUE_ID, c.ISSUE_ID)):
        payload = base("AUTHORIZE_BOUNDED_REMEDIATION", "d", state,
                       operation_id=operation_id, scope="ORIGINAL_ISSUE_CRITERION_ONLY")
        payload["issue_id"] = issue_id
        with self.subTest(operation_id=operation_id), self.assertRaises(c.CandidateError):
            c.authorize_remediation(state, c.sign_for_test("governance-1", payload, GOV_KEY), TRUST)


  def test_c6_criterion_alone_and_unbound_real_path_cannot_resolve(self):
    state, _ = authorize()
    raw, module_sha, closure_sha = make_proof(state.operation.operation_id)
    proof = json.loads(raw)
    proof["original_criterion_sha256"] = c.C6_PERMISSION_CRITERION_SHA256
    raw = canonical(proof)
    with self.assertRaises(c.CandidateError):
        finish(state, raw=raw, host=c.HostContext(canonical_module_path_sha256=module_sha,
                                                 live_binding_verified=True))
    raw, _, _ = make_proof(state.operation.operation_id)
    with self.assertRaises(c.CandidateError):
        finish(state, raw=raw, host=c.HostContext())
    self.assertEqual((state.issue_state, state.task_phase), ("WAIT_HUMAN", "BLOCKED"))


  def test_verified_test_fixture_resolves_issue_without_promoting_task_or_gates(self):
    state, _ = authorize()
    verified = finish(state)
    self.assertEqual(verified.issue_state, "RESOLVED")
    self.assertEqual((verified.task_phase, verified.next_stage), ("BLOCKED", None))
    self.assertEqual(verified.statuses, state.statuses)
    self.assertEqual(verified.accepted_gates, ())
    self.assertEqual((verified.continuations_used, verified.retries_remaining, len(verified.events)), (1, 0, 2))
    self.assertTrue(verified.operation.test_only_binding)
    malformed_attestation = verified.events[1].payload_dict()
    malformed_attestation["raw_evidence_length"] = True
    with self.assertRaises(c.CandidateError):
        c._validate_evidence_binding(malformed_attestation, c._pre_completion_state(verified))


  def test_reactivation_is_separate_signed_action_and_replay_does_not_promote_gates(self):
    state, _ = authorize()
    verified = finish(state)
    host = c.HostContext(canonical_module_path_sha256=verified.operation.module_path_sha256,
                         test_only=True)
    payload = base("REACTIVATE_ORIGINAL_TASK", "reactivation-1", verified,
                   operation_id=verified.operation.operation_id,
                   scope="IMPLEMENT_ONLY_AFTER_VERIFIED_RESOLUTION")
    signed = c.sign_for_test("governance-1", payload, GOV_KEY)
    active = c.reactivate_task(verified, signed, TRUST, host, allow_test_only=True)
    self.assertEqual((active.task_phase, active.next_stage), ("IN_PROGRESS", "IMPLEMENT"))
    self.assertEqual(active.issue_state, "RESOLVED")
    self.assertEqual(active.accepted_gates, ())
    self.assertEqual((active.continuations_used, active.retries_remaining), (1, 0))
    self.assertEqual(c.reactivate_task(active, signed, TRUST, host, allow_test_only=True), active)
    self.assertEqual(len(active.events), 3)


  def test_forged_state_journal_and_gate_drift_fail_closed(self):
    authorized, _ = authorize()
    forged_operation = replace(authorized.operation, state="VERIFIED")
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(authorized, operation=forged_operation), TRUST)
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(authorized, task_phase="IN_PROGRESS", next_stage="IMPLEMENT"), TRUST)
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(authorized, gate_catalog_bytes=authorized.gate_catalog_bytes[:-1]), TRUST)
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(authorized, accepted_gates=("fake-pass",)), TRUST)
    for index, (key, value) in enumerate(authorized.statuses):
        altered = list(authorized.statuses)
        altered[index] = (key, "PASS")
        with self.subTest(status=key), self.assertRaises(c.CandidateError):
            c._validate_state(replace(authorized, statuses=tuple(altered)), TRUST)


  def test_mutable_caller_key_maps_are_snapshotted_and_roles_must_differ(self):
    gov, verifier = {"g": GOV_KEY}, {"v": VER_KEY}
    trust = c.TrustRoots(gov, verifier)
    gov["later"] = b"z" * 32
    self.assertNotIn("later", trust.governance_keys)
    with self.assertRaises(c.CandidateError):
        c.TrustRoots({"same": GOV_KEY}, {"same": GOV_KEY}).validate()

  def test_signed_envelope_snapshots_mutable_nested_payload(self):
    state = c.initial_state(gate_bytes())
    payload = base("AUTHORIZE_BOUNDED_REMEDIATION", "decision-1", state,
                   operation_id="operation-1", scope="ORIGINAL_ISSUE_CRITERION_ONLY",
                   extra_list=["original"])
    envelope = c.sign_for_test("governance-1", payload, GOV_KEY)
    payload["extra_list"].append("mutated")
    self.assertEqual(envelope.payload_dict()["extra_list"], ["original"])
    with self.assertRaises(c.CandidateError):
        c.Envelope("governance-1", b'{"x":1,"x":1}', "00").payload_dict()
    with self.assertRaises(c.CandidateError):
        c.Envelope("governance-1", b'{ "x":1}', "00").payload_dict()


  def test_tampered_proof_bytes_cannot_match_signed_attestation(self):
    state, _ = authorize()
    raw, _, _ = make_proof(state.operation.operation_id)
    corrupted = raw + b" "
    with self.assertRaises(c.CandidateError):
        finish(state, raw=corrupted)

  def test_authenticated_rejection_is_terminal_and_never_issues_a_second_permit(self):
    state, permit = authorize()
    failed = finish(state, raw=b"evidence rejected by independent verifier", result="REJECTED")
    replay, no_permit = c.authorize_remediation(state=failed,
        decision=c.sign_for_test("governance-1", base("AUTHORIZE_BOUNDED_REMEDIATION", "decision-1",
            c.initial_state(gate_bytes()), operation_id="operation-1",
            scope="ORIGINAL_ISSUE_CRITERION_ONLY"), GOV_KEY), trust=TRUST)
    self.assertEqual(replay, failed)
    self.assertIsNone(no_permit)
    self.assertEqual((failed.issue_state, failed.task_phase, failed.operation.state),
                     ("WAIT_HUMAN", "BLOCKED", "FAILED"))
    self.assertEqual((failed.continuations_used, failed.retries_remaining), (1, 0))

  def test_proof_rejects_boolean_integer_and_non_normalized_paths(self):
    state, _ = authorize()
    for mutate in (
        lambda proof: proof.update(closure_complete=1),
        lambda proof: proof["closure_files"][0].update(length=True),
        lambda proof: proof["module_paths"].__setitem__(0, f"{Q}/runtime/../escape.js"),
        lambda proof: proof["closure_files"][0].update(path=f"{Q}/runtime\\escape.js"),
        lambda proof: proof["closure_files"][0].update(sha256="A" * 64),
    ):
        proof = json.loads(make_proof(state.operation.operation_id)[0])
        mutate(proof)
        raw = canonical(proof)
        with self.subTest(change=mutate), self.assertRaises(c.CandidateError):
            finish(state, raw=raw)

  def test_completion_event_must_reference_the_originally_authorized_operation(self):
    state, _ = authorize()
    other_operation = "different-operation"
    raw, module_sha, closure_sha = make_proof(other_operation)
    payload = {
        "version": 1, "action": "ATTEST_ORIGINAL_CRITERION_EVIDENCE", "attestation_id": "attestation-x",
        "task_id": c.TASK_ID, "issue_id": c.ISSUE_ID, "c6_run_id": c.C6_RUN_ID,
        "frozen_binding_sha256": c.FROZEN_BINDING_SHA256,
        "expected_state_sha256": c.state_fingerprint(c._pre_completion_state(state)),
        "contract_sha256": c.CONTRACT_SHA256, "task_state_file_sha256": c.TASK_STATE_FILE_SHA256,
        "gate_catalog_sha256": c.GATE_CATALOG_SHA256,
        "original_history_anchor_sha256": c._HISTORY_ANCHOR,
        "task_root_path_sha256": c.TASK_ROOT_PATH_SHA256,
        "continuations_used": 1, "retries_remaining": 0,
        "denied_capabilities": c.DENIED_CAPABILITIES,
        "operation_id": other_operation,
        "original_criterion_sha256": c.ORIGINAL_CRITERION_SHA256,
        "c6_permission_criterion_sha256": c.C6_PERMISSION_CRITERION_SHA256,
        "raw_evidence_sha256": h(raw), "raw_evidence_length": len(raw),
        "scope": "VERIFY_ORIGINAL_RUNTIME_BINDING_ONLY",
        "module_path_sha256": module_sha, "closure_manifest_sha256": closure_sha,
        "producer_receipt_sha256": h(b"test receipt"),
        "test_only_context": True, "verification_result": "VERIFIED",
    }
    envelope = c.sign_for_test("verifier-1", payload, VER_KEY)
    events = c._append(state, "REMEDIATION_VERIFIED", "attestation-x", other_operation, envelope, raw)
    forged_op = replace(state.operation, state="VERIFIED", finish_payload_sha256=h(canonical(payload)),
                        evidence_sha256=h(raw), module_path_sha256=module_sha,
                        closure_manifest_sha256=closure_sha, test_only_binding=True)
    forged = replace(state, issue_state="RESOLVED", operation=forged_op, events=events)
    host = c.HostContext(canonical_module_path_sha256=module_sha, test_only=True)
    with self.assertRaises(c.CandidateError):
        c._validate_state(forged, TRUST, host, allow_test_only=True)

  def test_exact_state_types_and_host_flags_fail_closed(self):
    state = c.initial_state(gate_bytes())
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(state, continuations_used=True))
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(state, gate_count=True))
    with self.assertRaises(c.CandidateError):
        c._validate_state(replace(state, events=[]))
    with self.assertRaises(c.CandidateError):
        c._validate_state(state, host=c.HostContext(test_only=1))


if __name__ == "__main__":
    unittest.main()
