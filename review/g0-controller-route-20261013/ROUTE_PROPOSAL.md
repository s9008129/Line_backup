# G0–G3 route evaluation — evidence review copy (2026-10-13)

**Outcome: BLOCKED.** This document summarizes a bounded, read-only route evaluation authorized by `APPROVE_PLANNER_PREPARATION_ONLY`. It does not claim Controller admission, implementation, GUI authority, or a product gate PASS. The escalation to SOL implementation was not approved.

## Frozen lineage and current state

- Task: `TASK-4acb4326ea2a4c50ace6f333f2de8751`
- Issue: `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5`
- c6 run: `c6c6b55d-865f-467b-94ba-3fd669df97ec`
- Frozen plan SHA-256: `210641620db94ee5de8ee271b979015442d3f2934d9281890a02c19f8719c279`
- Frozen contract SHA-256: `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc`
- Current task: `BLOCKED`, `active_run_id=null`, `next_stage=null`, `accepted_gates={}`.
- Current issue: `WAIT_HUMAN`, one continuation consumed, zero retries remaining.

These values are reproduced in the redacted, reviewer-readable [route status record](evidence/route-status.redacted.json), which includes the original 28-gate requirement metadata and keeps the c6 candidate statuses separate from the Controller projection. The record is a derived review copy, not a native Controller receipt.

The original c6 role result was selected as gpt-6-luna/high; provider backend attestation is `UNKNOWN`. A Sol principal reread the cited Controller sources and checked the route reasoning. This was a source cross-check, not a formal independent Plan Review or Acceptance. The route review also recorded the repository as private and preserved the original main worktree, its 18 tracked dirty paths, and PR #3 (still Draft/Open/unmerged).

## Route A — recover the existing task

The selected task-local `resources-luna` copy of immutable v4.8.0 does not support the proposed recovery in the observed state. The four named source files used for this analysis have hashes matching their corresponding files in the installed immutable 4.8.0 copy; this check does not establish the integrity of the full resource tree or platform enforcement. CLI `resume` reports persisted state and does not clear STOP or allocate a stage. `reconcile(REPLAN)` rejects unresolved or exhausted issues; it also requires a completed candidate outcome of `FAIL` or `REVISION_REQUIRED`, while c6 is `BLOCKED`. A new task label would create another task record and would not restore the consumed issue budget.

## Route B — create a linked bounded G0–G3 route

Lineage linking exists through `IssueLedger.open(lineage_issue_id=...)`, but linking preserves the existing issue state and budget. `authorize()` does not accept the current `WAIT_HUMAN` issue with a consumed continuation; `guard_task()` requires an eligible `CONTINUATION_AUTHORIZED` issue before IMPLEMENT allocation. The reviewed source exposes no non-reset admission path for this state.

A separate issue root would create a separate budget for the same underlying blocker. That would not preserve the original issue's consumed budget. Renaming a task, issue, report, or hypothesis also does not supply admission.

## Scope and gates retained

All 28 original required gates remain in force: `G_BASELINE_08`, `G_EVIDENCE_POLICY`, `G_AUTH_RUNTIME`, `G_REAL_LINK`, `G_OFFLINE`, `G_CATALOG_1`, `G_CATALOG_2`, `G_MENU_1`, `G_MENU_2`, `G_FIRST`, `G_SCROLL`, `G_SECOND`, `G_PRESERVE_08`, `G_REPORT`, `G_ACCEPTANCE`, `G_EVIDENCE_READINESS_08`, `G_EARLY_CHECKS_08`, `G_PRODUCTION_FAMILY_OFFLINE_08`, `G_B02_PRESERVATION_08`, `G_OFFLINE_IMPLEMENTATION_08`, `G_FINAL_HANDOFF_08`, `G_PARENT_TRACE_08`, `G_PLAN_ADMISSION_08`, `G_D01_LIVE_08`, `G_ALBUM_ONE_LIVE_08`, `G_POST_RELEASE_SCROLL_LIVE_08`, `G_ALBUM_TWO_LIVE_08`, and `G_INDEPENDENT_ACCEPTANCE_08`. G0–G3 would provide only genuine list-observation, one bounded scroll, and a fresh second-album identity check. They do not satisfy the complete backup or Acceptance objective. No requiredness, owner, phase, evidence role, or closure rule was changed; independent Plan Review and Acceptance remain required.

G0 is `BLOCKED`; G1–G3 are `NOT_RUN`. There was no fresh LINE screenshot/AX capture, scroll, click, Save All, chooser confirmation, download, or backup-state mutation. The route evaluation itself did not invoke the Controller or allocate a role.

## Execution prerequisites still absent

The local draft's default `live-grant-1.json`, `runtime-binding.json`, and `bin/rev28ctl` paths under the ML08 task root were absent. `live_entry.mjs` and `live_runner.mjs` remain local drafts without a proven production caller; GitHub PR #3's head returned 404 for those paths. A running-app inventory does not prove login, unlocked state, permissions, foreground handoff, or a genuine retained screenshot/AX observation. Therefore this route review grants no automatic G1 action even if its A/B analysis is accepted.

## Decision requested from independent reviewer

Confirm or reject the finding that neither Route A nor Route B admits the linked work under unchanged v4.8.0 while retaining the original issue budget and all 28 gates. If confirmed, the governance owner must choose whether to keep execution stopped or separately authorize preparation of a non-reset, non-fabricated resolution/admission proposal bound to this task and consumed issue.

That decision would authorize proposal preparation only. It would not change the Controller, allocate a run, authorize GUI input, or authorize LINE operations. Any revised Plan remains subject to independent Plan Review and the original independent Acceptance gate.

## Source provenance

The local evidence review examined four files from the selected task-local `resources-luna` v4.8.0 copy: `controller.py`, `escalation.py`, `cli.py`, and `workflow-routing.md`. Their original SHA-256 values are listed in [evidence manifest](EVIDENCE_MANIFEST.md) and match the corresponding installed immutable 4.8.0 files. This comparison covers only these named files; it does not attest to the full resource tree or OS/network enforcement. Source locations and the relevant branch outcomes are summarized in [controller route findings](evidence/controller-route-findings.redacted.md). Private session context, user paths, invitation material, raw event payloads, controller source copies, screenshots, AX, group names, and backup contents are withheld from this review copy.
