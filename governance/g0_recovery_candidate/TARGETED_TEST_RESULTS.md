# Targeted Test Results

These deterministic tests exercise only candidate code and synthetic test-only state/proof values. They are not LINE evidence, Controller execution, product acceptance, original-task recovery, or runtime closure verification.

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v governance.g0_recovery_candidate.tests.test_candidate
```

Observed result: exit code 0; 14 tests passed.

Captured test output:

```text
test_authenticated_rejection_is_terminal_and_never_issues_a_second_permit ... ok
test_authority_only_creates_one_non_executable_permit_and_replay_is_idempotent ... ok
test_c6_criterion_alone_and_unbound_real_path_cannot_resolve ... ok
test_completion_event_must_reference_the_originally_authorized_operation ... ok
test_exact_state_types_and_host_flags_fail_closed ... ok
test_forged_state_journal_and_gate_drift_fail_closed ... ok
test_mutable_caller_key_maps_are_snapshotted_and_roles_must_differ ... ok
test_no_governance_authority_keeps_original_issue_blocked ... ok
test_proof_rejects_boolean_integer_and_non_normalized_paths ... ok
test_reactivation_is_separate_signed_action_and_replay_does_not_promote_gates ... ok
test_signed_envelope_snapshots_mutable_nested_payload ... ok
test_tampered_proof_bytes_cannot_match_signed_attestation ... ok
test_verified_test_fixture_resolves_issue_without_promoting_task_or_gates ... ok
test_wrong_lineage_or_scope_is_rejected_even_with_valid_governance_signature ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.017s

OK
```

The cases cover absent/untrusted authority; exact signed lineage binding; one non-executable permit and idempotent replay; distinct criterion hashes and unbound real path rejection; issue resolution with Task/gates/statuses still unchanged; separate reactivation limited to IMPLEMENT; forged state/event, gate, and six-status rejection; role-separated immutable trust maps; immutable envelope payload snapshots and canonical/duplicate-key JSON rejection; authenticated terminal rejection without a second permit; malformed proof booleans, lengths, paths and hashes; wrong-operation event replay; exact state-type/host-flag rejection; and raw evidence tampering.

The positive proof fixture uses a test-only host path anchor and synthetic module/closure digests. The test producer receipt is synthetic and is not evidence of actual files or producer provenance. No production trust key is provisioned, and no runtime bytes are read by this suite.

The local environment did not have pytest installed (`python3 -m pytest ...` exited 1 with `No module named pytest`); tests therefore use Python's standard-library `unittest`. This is recorded as an environment fact, not as a code failure.

Sol independently crosschecked code SHA-256 `d3afdbf91854f4f6e9471991c6e500fd3348dbbf4c035938b81bd77803e08f2e` and test SHA-256 `b2cc30170c7c0787e6e69c73a83817ee3a713846434550357daa1cf2563deac4`, and reran this exact command with bytecode generation disabled: exit 0, 14/14 passed. The review found the isolated candidate boundary acceptable after fixes for six-status freezing, immutable signed payloads, authenticated operation-origin binding and replay reconstruction, and strict type/path validation. This is an internal code/test crosscheck only, not formal independent Acceptance, product PASS, or the external Chief Reviewer decision. Protected main-worktree and selected-tree preservation equality was also independently confirmed before publication.
