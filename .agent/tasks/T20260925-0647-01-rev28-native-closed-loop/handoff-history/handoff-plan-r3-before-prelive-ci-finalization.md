# Handoff — Rev28 native closed-loop LINE album backup

## TASK
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- STATUS: READY_FOR_IMPLEMENTATION (Stage 04 continuation; task remains open)
- PLAN_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`
- PLAN_REVISION: `3`
- PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- REVIEW_REQUIRED: YES
- REVIEW_REPORT: `review/attempt-05/review_report.md` (`bdc2069158916c40e435b14c2ab5f2f9f2094c1338070a198ff0c33f8f003310`) and `review/attempt-06/review_report.md` (`b716ccd06fee6711b1094206c29924ee7a54ccd0ab8d3ee28a7482b974fecefc`)
- REVIEWED_PLAN_REVISION: `3`
- REVIEWED_PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- INDEPENDENT_ACCEPTANCE_REQUIRED: YES (Stage 05)
- E2E_REQUIRED: YES (true user-journey run, only after every prior gate)
- ACCEPTANCE_MODE: approved Stage-02 reviews → W1 → complete W2 → W3 offline replay → W4 policy → W5 adversarial → V-09 reviews → Phase A read-only LINE reconnaissance → one bounded Phase B run → filesystem/content verification → Stage 05 independent acceptance.
- Fresh Implementer required: YES
- Planner/Reviewer transcript required: NO

## GOAL_ANCHOR
Primary outcome: use a new macOS-native closed-loop engine to back up group `旻謙允禎成長日記`, album `2024/05/13～05/17` (57 photos), into a fresh unique staging folder and prove `DUPLICATE_CONTENT_CONFIRMED` against the accepted baseline.
Success requires direct bounded observation of the real chooser, exactly 57 complete/stable/decodable images totaling 17,924,900 bytes, matching the baseline content multiset `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`, with the baseline unchanged.
No LINE interaction has occurred in this session. Do not open LINE or ask the owner to open the album during synthetic W2 work. Do not claim success from a click, chooser, or file count alone.
Exactly one Save All dispatch and one destination confirmation are permitted for the eventual live run; an unknown irreversible result is never retried.

## CRITICAL_PATH
1. Finish W2 item 5 against the synthetic harness using the current source, then verify all nine W2 items and frozen artifacts.
2. Complete W3 offline structural locators, all 20 SHA-bound historical replay fixtures, registration/tracking, and tests.
3. Complete W4 state machine, risk classes, ledger, staging verifier, chooser and postcondition behavior; then W5 G01–G22 + X01–X03 deterministic adversarial suite.
4. Complete all V-09 independent reviews on exact frozen SHAs. Only then may Phase A read-only LINE reconnaissance begin; Phase B remains gated on every pre-live gate.
5. If every gate passes, perform at most one authorized live run, verify files and baseline, then Stage 05 recomputes acceptance from disk.

## SEMANTIC_INVARIANTS
- Plan R1–R25 are authoritative; CORE stays CORE, SUPPORTING stays local/non-gating, and no missing supporting evidence may become a new global veto.
- Preserve plan §10–13 and the approved closed-loop contract: fresh identity/geometry per capture epoch; Vision text identity separated from click geometry; Quartz action followed by direct postcondition observation; filesystem proof is required for success.
- Exactly-once irreversibles, durable intent, no blind retry, observe-only crash recovery, fresh unique empty staging inside the approved root, one confirmation method only, and fail-closed ambiguity remain mandatory (R15–R22; see plan §§10–13 and LIVE_RUN_ENVELOPE).
- Do not change capture tolerances, chooser predicate, postcondition bounds, attribution, restart behavior, requiredness, failure routing, or terminal-state meaning without Stage 01 replan and fresh Stage 02 review. Current incomplete item-5 evidence is not a validated freeze.
- Never modify the accepted baseline or plan-listed historical artifacts; do not create `__pycache__` in task scope.

## BEST_EFFORT_DO_NOT_GATE
- R6 visual registration/tracking, R7 Foundation Models diagnostics, R23 supporting documentation/deliverable completeness, and V-08 replay/adversarial reporting are supporting per plan. V-08 remains a Phase-B interlock as explicitly stated in the plan, but its failure does not by itself redefine the primary outcome or global status.
- W6 is SUPPORTING. It must not displace unfinished CORE critical-path work.

## DEFERRED_NOT_THIS_TASK
- No LINE/album interaction during W2 or before all pre-live gates.
- No second production run, accepted-copy creation, historical-coordinate reuse, or broad repo cleanup.
- No general push authorization is implied by the owner’s explicit request to push this closeout checkpoint.

## REPO_ANCHOR
- Project root: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Branch: `master`
- Anchor HEAD: `9c29648` (pre-closeout; the closeout commit is intended as its direct descendant)
- Relevant dirty state at handoff compilation: three modified Rev28 source files; this task’s `execution.md`, regenerated `handoff.md`, archived prior handoff, and Rev28 harness evidence/log. Unrelated Rev27e plans, task files, route evidence and existing `__pycache__` directories were present and must remain untouched/unstaged.
- Drift since plan/review: implementation and W2 evidence have advanced from the approved plan anchor; plan itself remains byte-identical and attempt-05/06 approvals still match. Owner explicitly authorized add/commit/push for this checkpoint although plan R25 says “no push”; that instruction applies to this requested checkpoint only.

## CURRENT_STATE_DELTA
Handoff revision 3. Latest plan SHA and both review statuses were recomputed; attempts 05 and 06 are `PLAN_APPROVED` for exact revision 3. Previous handoff archived at `handoff-history/handoff-plan-r3-20260925T1200+0800.md` (SHA-256 `10a46357ae0ef81ebf1baa8d4e6b14d89235857ec6dc10c8f42a89b54e7969dd`).

W1 is complete. Current `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift test --package-path rev28` completed successfully: build complete, 28 tests, 0 failures. Durable log: `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` (SHA-256 `4d7dc802ee87b40599a9e8e58fd41c63b35417f223c7ac9fab18cf9f2fd12bc2`). Trailing whitespace was removed from the copied log; command output and test results are unchanged. `git diff --check` passed before handoff edits; rerun before commit.

W2 item status (evidence under `evidence/20260925-rev28-native-closed-loop/harness/`):
- 1 capture matrix/rule: PASS, frozen; complete 16-state matrix, no-rule fail-closed and occlusion capture. Rule SHA `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed`; matrix SHA `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b`.
- 2 Vision localization: PASS; exact menu/count/title, repeated row/safe-point agreement, ambiguity refused (`HARNESS-20260925-090259`).
- 3 transforms: PASS; round trips/moves 0 pt error, wrong scale detected, boundary refusal demonstrated (`085509`). Recorded-bbox differential itself was not distinguishable in that capture; unit test covers it.
- 4 Quartz routing: PASS; popup received event and was topmost over peer occluder (`104146`).
- 5 postcondition latency/bounds: PARTIAL, not validated/frozen. Run `114515` collected 20 real-panel samples (median 27.57 ms, p95/max 275.38 ms; delayed panel visible at 1060.67 ms), but behavior proof was incomplete: within case yielded `chooserObservedAfterWindow` at 5.19 s, timeout `noChooserObserved`, late case `noChooserObserved` / `noEligibleChooserCandidate`; no extra monitor input. The existing v1 bounds (`da579542…`) and latency file (`7ee9a9e5…`) are provisional artifacts from incomplete runs and must not be treated as validated. Latest source changes to sampler isolation, event draining and 8 s/15 s case bounds have not had a GUI rerun. Finish this item on the synthetic harness before W3; do not silently widen plan bounds.
- 6 chooser: PASS in `HARNESS-20260925-112927`; real panel affirmed, fake/empty-census/unbound/pid-reuse/lookalike cases refused, exact destination reflected, one AXPress confirmation, run-local marker verified. Canonical v2 predicate SHA `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2`; AX calibration SHA `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569`. Earlier v1 files remain provisional history.
- 7 focus theft: PASS (`085035`); lost focus/frame change detected, recovered after reactivation, zero dispatches during fixture.
- 8 tripwire attribution: PASS/FROZEN_VALIDATED, SHA `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216`.
- 9 restart/observe-only: PASS/FROZEN_VALIDATED, SHA `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f`.

Recent source work is limited to `FolderChooserDriver.swift`, `HarnessCalibration.swift`, and `HarnessApp.swift`: chooser focus/path reflection and run-local marker safety; item-5 monitor made independent of MainActor driver, per-scenario identity/event handling and freeze-only-on-PASS guard; harness panel activation/focus reporting. Item 5 still needs GUI verification on this final source. No W3/W4/W5 implementation completion, V-09 reviews, Phase A/B, or Stage 05 has occurred. At last process check no `rev28harness`, `rev28occluder`, `rev28ctl`, or LINE process was running.

Orthogonal status at this checkpoint:
- PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
- IMPLEMENTATION_STATUS: IN_PROGRESS
- CORE_ACCEPTANCE_STATUS: NOT_RUN
- REQUIRED_VERIFICATION_STATUS: INCOMPLETE (V-02 partial; subsequent required gates pending; no waiver)
- INDEPENDENT_ACCEPTANCE_STATUS: PENDING
- TASK_CLOSURE_STATUS: IN_PROGRESS

## MUST_READ_PLAN
Before action read plan §§GOAL_CONTRACT, REQUIREMENTS_AND_CRITICALITY (R1–R25), CRITICAL_PATH, CONSTRAINTS_NON_GOALS_AND_DO_NOT_TOUCH, ARCHITECTURE §§1–13, COORDINATE_TRANSFORM_MODEL, SYNTHETIC_HARNESS_CALIBRATION_PLAN items 1–9, HISTORICAL_REPLAY_PLAN, ADVERSARIAL_TEST_MATRIX, REVIEW_PLAN, RECONCILIATION_BARRIER_SUPERSESSION, LIVE_RUN_ENVELOPE, IMPLEMENTATION_WAVES W1–W7, VERIFICATION_AND_ACCEPTANCE V-01–V-11, DEGRADATION_AND_GATE_BEHAVIOR, ACCEPTED_TERMINAL_STATES_AND_CLOSURE, and STATUS_SEMANTICS_AND_CLOSURE_ROUTING.

## SETTLED_DO_NOT_REOPEN
- Plan revision 3 and approved SHA are unchanged; any plan edit invalidates reviews and requires a fresh review.
- W2 item 5 is the sole unfinished calibration item; the existing v1 bounds/latency artifacts are provisional. Do not start W3 until item 5 is validated and W2 re-audited.
- Chooser v2 filenames are the resolved append-only republish; preserve provisional v1 files.
- Owner’s push authorization covers this closeout checkpoint only; plan R25 remains the default for later pushes.

## REVERIFY_ON_START
1. `git status`, branch/HEAD/upstream and remote state; preserve all unrelated files. Confirm closeout commit/push and clean status for task-owned paths.
2. Recompute plan, attempt-05/06 and current handoff hashes; require exact revision-3 match before implementation.
3. Check canonical W2 artifact hashes and that item-5 v1 artifacts remain marked provisional; inspect latest item-5 source diff before running it.
4. Recheck build/test on current HEAD, macOS/Swift/Xcode environment, harness permissions and that no harness process is stale.
5. Reverify approved staging `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260923-111908-01` is empty, accepted baseline resolves to 57 files/17,924,900 bytes and both plan digests match; do not open or mutate the album.
6. Confirm do-not-touch/history inputs and unrelated pre-existing work remain unchanged.

## TRIGGERED_POLICIES
`workflow-routing.md` §7 status semantics; `goal-alignment-design-economy.md`; `testing-verification.md`; `dependencies-contracts.md` (frozen W2 contracts); `security-privacy.md` (user album/baseline); `git-change-hygiene.md`.

## FIRST_ACTION
After REVERIFY_ON_START, complete only W2 item 5 in the synthetic harness using the current source: `./rev28/.build/debug/rev28ctl harness-calibrate --evidence evidence/20260925-rev28-native-closed-loop/harness --items 5`. Require valid within-window affirmation, timeout `NO_CHOOSER_OBSERVED`, late affirmative `CHOOSER_OBSERVED_AFTER_WINDOW`, zero further input, and ≥20 latency samples before freezing. If final-code evidence still fails, repair only within plan semantics; if bounds/predicate semantics need change, stop for replan/review. Then re-audit W2 items 1–9 and proceed to W3.

## IMPLEMENTATION_WAVES
- W1 CORE: DONE.
- W2 CORE: PARTIAL; items 1–4 and 6–9 pass, item 5 partial and is the next action.
- W3 CORE: NOT STARTED; offline locators, 20-fixture SHA-bound replay, registration/tracking and tests.
- W4 CORE: NOT STARTED; state/risk/ledger/verifier/chooser/postcondition policy and tests (some scaffolding exists).
- W5 CORE: NOT STARTED; G01–G22 + X01–X03 deterministic harness suite.
- W6 SUPPORTING: incomplete; do not gate core work on it.
- W7 CORE/CONDITIONAL: not started; only after W1–W5 and V-09 gates.

## ACCEPTANCE_CONTRACT
All checks have `BASELINE_RULE: none`, `WAIVER_ALLOWED: NO`, `WAIVER_AUTHORITY: NONE`; no agent may self-waive. V-01/V-02/V-08 are diagnostics but Phase-B interlocks per plan. V-03–V-07 and V-09 are hard-clean Phase-B gates; V-10 gates closure; V-11 is supporting repository health.

| CHECK_ID | COMMAND/SCENARIO | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY |
|---|---|---|---|---|---|---|---|---|
| V-01 | Executable-context capability probe | CORE | DIAGNOSTIC | NON_GATING | none | NOT_RUN blocks Phase B; FAIL replan/block | NO | NONE |
| V-02 | W2 calibration + frozen capture rule | CORE | DIAGNOSTIC | NON_GATING | none | repair; semantic change replans | NO | NONE |
| V-03 | Live capture geometry | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | unexplained INVALID → abort | NO | NONE |
| V-04 | Bounded direct chooser postcondition | CORE | OUTCOME | HARD_CLEAN | none | named chooser outcome; no retry | NO | NONE |
| V-05 | Chooser identity + exactly-once confirmation | CORE | OUTCOME | HARD_CLEAN | none | refusal → INDETERMINATE_CHOOSER_REFUSED | NO | NONE |
| V-06 | 57 stable/decodable files, bytes and content multiset | CORE | OUTCOME | HARD_CLEAN | none | named staging/content mismatch | NO | NONE |
| V-07 | Baseline path/digests/mtimes unchanged | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | unresolved → BLOCKED; delta → abort | NO | NONE |
| V-08 | Replay + G01–G22/X01–X03 | SUPPORTING | DIAGNOSTIC | NON_GATING | none | failure repaired before Phase B | NO | NONE |
| V-09 | Seven reviews + adversarial + barrier review | CORE | DIAGNOSTIC | HARD_CLEAN | none | REVISION_REQUIRED → repair/re-review | NO | NONE |
| V-10 | Stage-05 recomputation from disk | CORE | OUTCOME | HARD_CLEAN | none | mismatch → fail/replan | NO | NONE |
| V-11 | Preservation/no-new-pycache audit | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | none | violation → stop/report | NO | NONE |

## STOP_AND_ESCALATE_IF
Plan/review/handoff hash mismatch; any semantic validity, requiredness, gating, failure/fallback, priority, or frozen W2 change; new architecture/root-cause/security decision; baseline/staging precondition failure or baseline delta; wrong album/window/identity; invalid geometry; chooser absent/refused; unknown irreversible dispatch; or any abort condition. Record escalation and replan; never weaken an invariant to proceed.

## HISTORICAL_TASK_DEPENDENCIES
Use only the exact read-only inputs named in plan §§SOURCE_OF_TRUTH, HISTORICAL_REPLAY_PLAN and HISTORICAL_TASK_DEPENDENCIES, including `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md`, the named `evidence/20260916-route/attempt-07/**` barrier rationale, and the 20 explicitly listed replay fixtures. Do not scan sibling `.agent/tasks/*`.

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
HANDOFF_PATH: .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/handoff.md
PLAN_REVISION: 3
STATUS: READY_FOR_IMPLEMENTATION
NEXT_STAGE: 04_IMPLEMENT
