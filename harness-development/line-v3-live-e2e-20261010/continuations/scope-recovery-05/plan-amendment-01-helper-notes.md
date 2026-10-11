# Read-only helper findings for Plan Amendment 01

These are concise notes from the three actual collaboration subagent sessions used concurrently during the amendment stage. They are advisory observations, not controller receipts, gate approvals, or native Harness admission.

## `plan_contract_audit`

- Confirmed the published plan, contract, and handoff all freeze implementation helpers and writers at zero.
- Recommended changing only the helper ceiling to three, retaining writers at zero, all five implementation gates, allowed paths, capability policy, and acceptance rules.
- Identified plan freeze, handoff, check-spec hash, result, and document manifest records as historical evidence that must not be silently rewritten.

## `workspace_evidence_audit`

- Observed HEAD `f969c817975396bea28e7315dec1a2aec5c6a312`, branch `v43-ab/codex-rev28`, and an empty index.
- Counted 11 modified tracked paths, 68,483 untracked paths, and 3,753 ignored paths. It identified `tests/test_cua_adapter.mjs` as pre-existing modified work.
- Confirmed the existing CON `.local` baselines and Git publication receipts must be preserved; no `checks/` or `evidence/` directory existed at the time of inspection.
- Confirmed the old classifier/chooser issue has two known attempts and one remaining candidate verification attempt.

## `harness_feasibility`

- Confirmed four total collaboration slots including the root, so the practical maximum is three simultaneous helpers.
- Confirmed the collaboration helpers can return read-only model findings, but the available interface does not create Harness controller-bound helper lifecycle receipts.
- Confirmed the pinned Harness runtime is missing, and there is no admitted stage packet, invitation, emitted validator command, or packet `result_path`; native admission, contract validation, and result validation remain `NOT_RUN`.
- Advised keeping helper output advisory and reporting the native Harness limitation accurately. It made no file edits, ran no product checks, and did not use LINE UI.

The source observations and current task files are under `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/`; the installed read-only routing policy is `/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source/policies/v4.8.0/workflow-routing.md`.
