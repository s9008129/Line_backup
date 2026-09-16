# Plan Review Report

## REVIEW_METADATA

- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 06
- REVIEWED_PLAN_REVISION: 5
- REVIEWED_PLAN_SHA256: 54cf44628bf60c71b636a3bae16ba94303e2c17f4b425708ea924c21da09c006
- REVIEWED_PLAN_BYTES: 53740
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-06/plan_snapshot.md
- PLAN_SNAPSHOT_SHA256: 54cf44628bf60c71b636a3bae16ba94303e2c17f4b425708ea924c21da09c006
- REVIEW_MODE: read-only for product code and plan.md
- PRIOR_ATTEMPT_NOTE: attempt-05 snapshot was preserved at 53737 bytes, SHA-256 7cbd7e83789e1798a6e7408c193b831f32e17073e054974dd589789132bb3626; it was explicitly aborted and is not approval evidence.

## GOAL_BASELINE

The primary outcome is to safely determine whether the existing 57-image destination belongs to the exact requested LINE source group `旻謙允禎成長日記`, album `2024/05/13～05/17`, and count 57. If exact correspondence or transaction safety cannot be proved, the process must stop without changing the existing files/formal state or creating an ambiguous/duplicate production transaction.

CORE evidence is exact source correspondence, read-only filesystem/state/registry/intent/writer reconciliation, a real operator-facing reusable transaction boundary with restart/duplicate/commit safety, and independent acceptance. Supporting bridge readiness may not veto unless route-specific causal evidence proves necessity. Production download, spelling merge, migration, bridge repair, and broad cleanup are deferred/non-goals.

## EVIDENCE REVIEWED

- [VERIFIED] No repository-local `AGENTS.md` was found. Global instructions, the `line-album-backup` skill, and the review/workflow/goal/testing/debugging/dependency/UI policies were read before judgment.
- [VERIFIED] The exact Rev5 plan is 53,740 bytes and hashes to the requested SHA-256. The new snapshot compares byte-for-byte equal to `plan.md`.
- [VERIFIED] The formal data root contains only the declared config, state, and run-log files. Config is 372 bytes, schema 2, has all ten declared keys/types, `backup_root=/Users/hsiaojohnny/Downloads/LINE-Backup-PoC`, and `max_albums_per_run=1`, `recovery_limit=1`, `poll_interval_seconds=5`, `stable_samples=3`, `max_wait_seconds=600`.
- [VERIFIED] Current state is schema 2, revision 39, four verified-album entries, five runs, `current_run_id=null`, `active_writer_id=null`, and `context_lock=null`. The requested `禎` key differs from persisted/configured `楨`; the 57-image target run has `contract_revision=null`, `observed_title=null`, legacy fields, and no full provenance. The plan correctly treats this as provenance-limited/unresolved rather than exact correspondence.
- [VERIFIED] The current destination is a real directory with 57 immediate regular files and no non-file immediate entries. Historical corrected audit evidence records 57 recognized JPEGs, 17,924,900 bytes, three stable samples, and no zero-byte/partial/unrecognized/subdirectory/other entries. This evidence does not prove source identity or a future product verifier.
- [VERIFIED] The old verifier accepted both isolated 56-file and 58-file fixtures with `Expected images: 57`, `FILESYSTEM_VERIFICATION=PASS`, and exit 0. The old script never compared the observed count with `EXPECTED`, establishing the false-positive mechanism.
- [VERIFIED] The self-certifying recovery fixture's corrected run exited 0, but its script writes `UNKNOWN`/`retry=false` and then checks those same values with `jq`; it does not invoke a product transaction, restart a process, or independently oracle durable state. The plan correctly identifies this as insufficient and requires a real CLI boundary.
- [VERIFIED] The documented CUA runtime exposes app acquisition, fresh AX/screenshot observation, and documented click/key/scroll primitives. The historical GUI ledger is 4,219 bytes (SHA-256 `9d6a159024f822003052fd7d538598d3a161f226c49ce14ea5c11d5c95c95aee`); its action records contain exactly two ellipsis inputs, zero menu-item/Save-All clicks, and zero formal-state writes. Its separate 4,555-byte budget authority (SHA-256 `a43d23d6166a3d2156c5e3a1ccd08cc394b8b283f9c3a2d007929db986922c95`) records 2/2 ellipsis budget used. The plan's new post-gate budgets of acquisition 0, navigation 0, ellipsis 1 are finite and exact.

## PLAN STRENGTHS

The Goal Contract, offline-first critical path, explicit product boundary, read-only formal-state rule, legacy compatibility profile, axis-separated verifier outcomes, content/MIME/hash/mtime requirements, at-most-once barrier, guarded compare-and-commit, atomic replacement/read-back, isolated subprocess cases, no-retry recovery, truthful `E2E_REQUIRED: NO` rationale, and GUI-ledger separation are aligned with the goal and the skill. Case 07 now uses the declared `transaction prepare` interface, a single literal barrier path, and no undeclared acquire/finalize command. Bridge readiness remains non-gating.

## FINDINGS

### RV6-001 — MAJOR — Case 07 is not yet deterministic enough to be an exact acceptance case

**Affected:** plan lines 114–116 and 234–258.

Both `transaction prepare` processes pause before the shared lock on the same barrier. Releasing that one barrier can let either process acquire the lock first; the plan also says “one fixed acquisition winner” without defining a scheduling/order mechanism. The expected loser is written as `CONFLICT_OWNER_RUN` **or** `CONFLICT_STALE_REVISION`, although `prepare` has no expected-revision/owner arguments and the plan does not define which stable conflict result applies to acquisition.

**Failure/rework mechanism:** Stage 05 cannot independently reproduce or assert one exact Case-07 result. A test may pass with a different error code or incorrectly claim a fixed winner even though the single barrier does not select one.

**Required correction:** Keep only the declared `transaction prepare` interface and one barrier, but define the oracle precisely: either A or B may be the winner; exactly one process may commit the ownership/run record; the other must return one explicitly named acquisition-conflict code with exact exit and no state replacement/second owner. Remove “fixed winner” unless a deterministic mechanism is added without introducing an undeclared interface. Record the final winner/loser identities and state revision from independent precomputed expectations.

### RV6-002 — MAJOR — Canonical incident status is inconsistent with Status Contract v2

**Affected:** plan line 340.

The fixture labeled “Canonical incident with pre-existing hard-clean debt” sets `PRIMARY=UNKNOWN` while `IMPLEMENTATION=COMPLETE`, `CORE=PASS`, and only required verification is `INCOMPLETE` because of pre-existing repository debt. Status Contract v2 explicitly allows `PRIMARY_OUTCOME_STATUS=ACHIEVED` to coexist with pending required verification, and its canonical incident example reports the CORE repair as successful while closure remains pending.

**Required correction:** Set this fixture's primary status to `ACHIEVED` (or change the fixture name and provide a concrete reason the primary outcome itself is unknown). Preserve `REQUIRED_VERIFICATION_STATUS=INCOMPLETE`, the scoped pre-existing blocker, and `TASK_CLOSURE_STATUS=PENDING_REQUIRED_VERIFICATION`; do not turn repository debt into a task regression.

### RV6-003 — MAJOR — Contradictory-state fixture violates routing precedence

**Affected:** plan line 347.

The row sets `CORE=FAIL` and `TASK_CLOSURE_STATUS=FIX_REQUIRED` but leaves `IMPLEMENTATION=COMPLETE`. Under the plan's own line 338 and workflow-routing §7.7 rule 4, completed implementation plus CORE failure must transition the current implementation subject to `IN_PROGRESS` while preserving the failure evidence.

**Required correction:** Change the contradictory-state fixture's current `IMPLEMENTATION_STATUS` to `IN_PROGRESS`, keep `CORE_ACCEPTANCE_STATUS=FAIL`, `PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`, and `FIX_REQUIRED`, and assert that the original completed Stage-04 snapshot (if present) is not silently rewritten.

### RV6-004 — MAJOR — Baseline-delta fixture has no declared baseline-delta check

**Affected:** plan lines 314–327 and 339.

The status row claims `baseline_delta=UNCHANGED`, but every listed closure gate is `HARD_CLEAN` or `NON_GATING`; no named `CHECK_ID` has `CLOSURE_GATE=BASELINE_DELTA`, `BASELINE_REQUIRED=YES`, a pre-change command/environment, and a precise no-new-or-worsened-signature rule. A free-form row label cannot prove the v2 baseline contract.

**Required correction:** Add a named check or explicit contract fixture with all v2 metadata, including `CLOSURE_GATE=BASELINE_DELTA`, baseline artifact/hash, identical command/environment (or approved equivalent), post-result, and exact classification of unchanged versus worsened signatures. Make the fixture assert the original debt remains disclosed and is not called clean.

### RV6-005 — MAJOR — Supporting hard-clean debt lacks the required global-gate rationale

**Affected:** plan lines 326–327 and 340–343.

`DOCUMENTATION_RETENTION_HEALTH` is classified `SUPPORTING` but uses `CLOSURE_GATE=HARD_CLEAN`, which can block overall closure. “Non-core evidence-retention debt remains a scoped required-verification issue” identifies the effect but does not explain the safety/correctness reason that local degradation is insufficient. The goal policy requires that rationale before a supporting check may be a hard-clean closure gate.

**Required correction:** State the concrete decision-validity obligation (for example, which missing retained artifact would make independent acceptance non-reproducible or provenance-invalid), why non-gating disclosure is insufficient, and the exact scope of the veto. Otherwise make the check `NON_GATING`. Retain the reachable formal-waiver fixture only if the hard-clean gate and its authority remain explicitly justified; preserve the original item-level FAIL when waived.

### RV6-006 — MAJOR — Most transaction cases still lack literal reproducible process commands

**Affected:** plan lines 243–258 and 260–265.

Rev5 supplies literal argv examples for Cases 01, 04, and 07, but Cases 02, 03, 05, 06, 08, 09, 10, 11, and 12 remain prose descriptions. The requirement that future `inputs.json` contain expanded argv is an implementation instruction, not a reviewable plan-time command protocol. Barrier release order, restart argv, fault flags, status inputs/outputs, and expected artifact paths are therefore still under-specified for most acceptance cases.

**Required correction:** Add literal absolute argv/process-launch and barrier-release commands (or one fully specified deterministic driver with its literal argv arrays) for every Case 01–12, including exact pre-state, evidence, counter, result, manifest, exit-code, and post-state paths. Keep Case 07 limited to the declared `transaction prepare` command and its one barrier.

## REQUIRED_PLAN_CHANGES

1. Revise the same task to the next monotonic plan revision and correct RV6-001 through RV6-006 without changing the unresolved `禎`/`楨` conclusion or GUI authorization scope.
2. Re-run independent review against the new plan hash. Do not compile a new handoff or implement product code from this Rev5 candidate.
3. Preserve the prior attempt-05 snapshot and this attempt-06 report as append-only evidence; neither is an approval for Rev5.

## RESIDUAL_VERIFIED_NOTES

- The formal config/legacy-state compatibility claims are grounded in the current files and are suitable for implementation planning.
- The false-positive and self-certifying-fixture corrections are correctly framed as baseline evidence, not acceptance evidence.
- The CUA route is correctly separated from offline acceptance; historical coordinates and exhausted historical budget are not reused, and the new finite ledger permits no unlisted input.
- No product code or `plan.md` was edited by this review.

GATE: PLAN_REVISION_REQUIRED
