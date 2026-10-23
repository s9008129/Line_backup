# Plan Amendment 01 — helper ceiling and review

Recorded 2026-10-11 for `TASK-20261011-line-receipt-recovery`.

The published Plan and Handoff froze implementation at zero helpers and zero writers. The user then required maximum parallel subagents. After I described that conflict and proposed revising the plan to allow up to three read-only helpers while keeping writers at zero, the user replied “是”. This amendment records that decision before implementation work.

The change is limited to the workflow policy and the requested review step:

- `max_parallel_read_only_helpers`: 0 → 3.
- `max_parallel_writers`: remains 0.
- `plan_review_required`: false → true for the amended Plan before its handoff.
- All allowed paths, goals, five implementation gates, check commands/order, retry limits, product read-only boundary, and capability policy remain unchanged.

The host exposes four total collaboration slots including the root, so no more than three helpers can run at once. Helpers are advisory and read-only. The root remains the only plan, contract, code, evidence, and result author. No helper may run checks, edit files, operate LINE, approve gates, alter scope, commit/push, or start nested work.

The three concurrent planning helpers were `plan_contract_audit`, `workspace_evidence_audit`, and `harness_feasibility`. They made no file changes, ran no product checks, and used no LINE UI. Their findings are summarized in `plan-amendment-01-helper-notes.md`. The collaboration API records real subagent sessions, but the missing Harness controller stage packet means these are not controller-registered helper allocations or native admission evidence.

The prior plan/contract hashes were:

- Plan: `e3bdc89bfd4e627d82cc5d22fce3b66bcc83311fb928aac4652c7695e8aa4020`
- Contract and handoff JSON: `6b2076527f343e895f0a9798ffe4c8b85f4e855b2afcdd19d2de168ba1f0f7a0`

The amended contract requires independent review before the revised Handoff is compiled. The review result will be retained separately. Existing publication, freeze, compiler, and format-3 role results remain historical evidence for the earlier document stage; they are not overwritten or relabeled. This local amendment does not claim native schema validation or controller publication.

No LINE foreground handoff is needed: this continuation performs local tooling and offline adapter checks only.
