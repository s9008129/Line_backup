# Handoff — Rev28 native closed-loop LINE album backup (PLAN_REVISION 3, approved)

## TASK
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- STATUS: READY_FOR_IMPLEMENTATION
- PLAN_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`
- PLAN_REVISION: `3`
- PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- REVIEW_REQUIRED: YES
- REVIEW_REPORT: `review/attempt-05/review_report.md` (SHA-256 `bdc2069158916c40e435b14c2ab5f2f9f2094c1338070a198ff0c33f8f003310`) and `review/attempt-06/review_report.md` (SHA-256 `b716ccd06fee6711b1094206c29924ee7a54ccd3ab8d3ee28a7482b974fecefc`) — both `PLAN_APPROVED`
- REVIEWED_PLAN_REVISION: `3` (snapshots `review/attempt-05/plan_snapshot.md`, `review/attempt-06/plan_snapshot.md`, byte-identical to `plan.md`)
- REVIEWED_PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- INDEPENDENT_ACCEPTANCE_REQUIRED: YES (Stage 05; CORE acceptance first, recompute from disk)
- E2E_REQUIRED: YES (true user-journey live run; strictly conditional — if any pre-live gate fails, the task ends in a scoped blocked/partial state and Phase B does not execute)
- ACCEPTANCE_MODE: Stage-02 reviews (done) → W2 synthetic AppKit calibration with frozen rules → offline replay → adversarial suite → seven pre-live reviews + adversarial + barrier supersession → read-only LINE reconnaissance (Phase A) → single bounded production run (Phase B) → filesystem/content verification → independent Stage-05 acceptance
- Fresh Implementer required: YES
- Planner/Reviewer transcript required: NO

## GOAL_ANCHOR
- PRIMARY_OUTCOME: a NEW macOS-27-native closed-loop engine (ScreenCaptureKit sense → Vision read → Quartz act → direct postcondition observation → filesystem verify) backs up the LINE group `旻謙允禎成長日記` album `2024/05/13～05/17` (57 photos) into a fresh unique staging run, proving `DUPLICATE_CONTENT_CONFIRMED` against the accepted baseline.
- SUCCESS_EVIDENCE: chooser directly observed in the bounded postcondition window; exactly 57 stable decodable files, no subdirs/partials/zero-byte, total bytes 17,924,900; name-excluded content multiset == `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`; baseline unchanged.
- MUST_NOT_BREAK: never claim BACKUP_COMPLETE/duplicate-confirmed from a click, menu change, chooser appearance, or file count alone; exactly one Save All dispatch and exactly one confirmation action for the whole task; no historical coordinates; baseline byte-identical; no push; no `__pycache__`; do-not-touch list preserved.
- Failure outcome is allowed and pre-declared: an honest scoped `INDETERMINATE_*`/`ABORTED_*` terminal state with all evidence preserved; it is never "Done".

## CRITICAL_PATH
Ordered (plan §CRITICAL_PATH; only steps 1–5 hard-gate the irreversible step):
1. Capability + harness first: prove SCK capture semantics, Vision localization, the canonical transform, Quartz routing in the synthetic AppKit harness (W1→W2).
2. Engine core: deterministic pure cores + thin OS edges (W1/W3/W4).
3. Offline validation: unit/integration + 20-fixture historical replay (W3).
4. Adversarial hardening: 25 scenarios G01–G22 + X01–X03, deterministic reruns (W5).
5. Seven pre-live topic reviews + adversarial review + barrier supersession, bound to frozen W2 artifacts and implementation SHAs (V-09).
6. Phase A read-only LINE reconnaissance (no side-effecting dispatch) → gate (g).
7. Phase B: one ellipsis, one Save All, direct chooser observation, one confirmation, download into unique staging run.
8. Filesystem + content verification → `DUPLICATE_CONTENT_CONFIRMED`; baseline unchanged.
9. Closeout: ledger, manifests, final report, local commits (no push).

## SEMANTIC_INVARIANTS
Executor must not change these; any change is a replan + fresh review, never a bounded fix.
- `S-01` exactly-once irreversibles: Save All dispatch = 1; destination confirmation = 1 and only the one pre-chosen action (`AXPress` **or** `Return`, never both); a non-effect consumes the budget; no blind retry of an irreversible action; crash resume is observe-only.
- `S-02` success predicate: `DUPLICATE_CONTENT_CONFIRMED` = exactly 57 image files, no subdirs/partials/zero-byte, decodable, stable (≥3 samples ≥4 s + ≥5 s quiescence), total bytes 17,924,900, and `SHA-256(sort(values).joined("\n"))` (no trailing newline) == `ee958e64…`. Filenames excluded by design (fresh downloads carry a new date token).
- `S-03` identity/epochs: window selected by bundle+pid-instance+layer+live geometry, never windowID alone; windowID valid only inside one capture epoch; stale ID invalidates; no historical coordinate may ever be reused.
- `S-04` transform invariants 1–5 (plan §COORDINATE_TRANSFORM_MODEL): validated-tolerance geometry vs W2-frozen rule (not exact equality); recorded bbox drives the transform; origin consistency incl. same-epoch re-read; `pointPixelScale` must equal `NSScreen.backingScaleFactor`; no implicit 2×; click point within 1 pt of a safe-interior boundary → refuse/re-locate.
- `S-05` postcondition: one bounded window, single evidence standard, cadence ≤150 ms first 8.0 s then ≤500 ms to hard cap 15.0 s (W2 re-freezes with ≥20 measured real-`NSOpenPanel` runs; review 4 binds); late affirmative (~30 s forensic sample) → `CHOOSER_OBSERVED_AFTER_WINDOW`; none → `NO_CHOOSER_OBSERVED`; logs/panel presence/click-return are never sufficient.
- `S-06` chooser predicate: frozen 4-clause predicate (§11) incl. ownership via panel-process census + bundle/code-sign + start time (pid reuse rejected); an empty/indeterminate pre-census **widens refusal**, never relaxes the predicate; ambiguity → `INDETERMINATE_CHOOSER_REFUSED` with cause enum incl. `frozen_predicate_mismatch`; never loosen the predicate ad hoc.
- `S-07` tripwire attribution ladder (plan §10 / reviewer-06 RV-01 clarification): `L1` = unique staging run dir (writes are expected evidence); `L2` = approved root `…/LINE-Backup-PoC/` (attributable-but-unexpected → `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED`, non-fatal, disclosed; unattributable → `ABORTED_UNATTRIBUTED_FILESYSTEM_WRITE`; any accepted-baseline modification → immediate abort regardless); `L3` = outside approved root (attributable-to-run → `ABORTED_WRITE_OUTSIDE_APPROVED_ROOT`; unattributable → environmental context, non-aborting, disclosed). The envelope abort-item resolves through this ladder (L2 fail-closed; L3 unattributable does not abort).
- `S-08` baseline is fail-closed: canonical path = `baseline-content-multiset.json.source_dir` (SHA `3c932d8c…` checked first); realpath-resolve, assert 57 files / 17,924,900 B, recompute manifest digest `b7debe92…` (trailing-newline method) and multiset `ee958e64…` (no trailing newline); unresolvable/mismatch → `CHECK_RESULT: BLOCKED` (no degraded comparison, no skipped tripwire, no Phase B).
- `S-09` Save All runs under `IRREVERSIBLE_SIDE_EFFECT` semantics this round (classification is NOT proven); record `saveAllEmpiricalClassRecord`; `PRE_SIDE_EFFECT_ACTION` stays defined but unused.
- `S-10` recovery budget: `REVERSIBLE_NAVIGATION` ≤3 attempts per identical blocker with fresh preconditions; global reversible-dispatch ceiling 12 → `ABORTED_REVERSIBLE_BUDGET_EXHAUSTED`; two consecutive failed revalidations of the same candidate → abort (the stricter cap wins).
- `S-11` status semantics v4.2: keep PRIMARY_OUTCOME / IMPLEMENTATION / CORE_ACCEPTANCE / REQUIRED_VERIFICATION / INDEPENDENT_ACCEPTANCE / TASK_CLOSURE orthogonal; `IMPLEMENTATION_BLOCKED` only for unfinished product implementation, always scope-named; no naked `BLOCKED`; `DONE` only on primary-outcome achievement; a passed synthetic suite never implies a live result.
- `S-12` frozen-rule freeze: once a W2 rule (capture tolerance, postcondition bounds, chooser predicate, attribution, restart fixture) is reviewed, changing it = replan + fresh review, never an implementer edit.
- `S-13` scope/preservation: only `rev28/**`, `evidence/20260925-rev28-native-closed-loop/**`, the task dir, and one `.gitignore` line (`rev28/.build/`) may change; everything in DO_NOT_TOUCH stays byte-identical; no push; no `__pycache__`.
- `S-14` Foundation Models is diagnostics only (never click authority, never predicate relaxation); beta APIs are never the sole production gate.

## BEST_EFFORT_DO_NOT_GATE
- Foundation Models diagnostics; registration/rectangle-tracking evidence (`R6`/`R7`); `VNRecognizeTextRequest` parity wrapper — degrade to deterministic-only behavior, never block the core path.
- `V-11` preservation audit: `REPOSITORY_HEALTH`, `NON_GATING` for closure — but a violation is reported and stops closeout claims; it must not be re-labelled as product CORE.

## DEFERRED_NOT_THIS_TASK
- No second accepted production copy; no copying staging into the accepted baseline; no cleanup/deletion of staging or baseline; no reclassification of attempt-07; no modification of Rev27e WIP or other agents' work; no push; no push-worthy packaging; no production Foundation Models use.

## REPO_ANCHOR
- Project root: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Branch: `master`
- Anchor HEAD: `766b22c4f8bf29b9d0a46049c75309c70593d66d` (= `origin/master`, ahead 0)
- Relevant dirty state: untracked-only — Rev27e WIP (`.agent/tasks/T20260924-1113-03-rev27e3-hardening/`, `PLAN-2026-09-23-rev27e*.md`), prior evidence dirs incl. three `__pycache__` dirs (pre-existing, untracked, never staged), plus this task dir and `evidence/20260925-rev28-native-closed-loop/`. No tracked modifications.
- Drift since plan/review: none observed at handoff compile time (plan SHA unchanged, HEAD unchanged, staging empty, LINE not running).

## CURRENT_STATE_DELTA
- Stage-02 complete: two independent approvals on Rev3 (`attempt-05`, `attempt-06`); prior revision history preserved (`attempt-01` APPROVED on rev1; `attempt-02/03/04` REVISION_REQUIRED).
- `rev28/` does not exist yet; `evidence/20260925-rev28-native-closed-loop/` currently holds only `baseline-content-multiset.json` + `capability-probe/**`.
- Carried MINOR review findings (non-blocking; reviewer-recommended clarifications of approved-plan wording — apply as interpretation, never as new design):
  1. attempt-06 RV-01: envelope abort item = L2 fail-closed per `S-07`; L3 unattributable stays non-aborting environmental context (also update harness item 8 / RISKS #9 wording in-code, not in plan).
  2. attempt-06 RV-02: `LIVE_RUN_INTERLOCK` = "part of the authorized run's gate chain": pre-live for V-01/V-02/V-08/V-09, live-time for V-03…V-06, pre-live + closeout for V-07; V-10 gates closure; V-11 is the closeout audit.
  3. attempt-06 RV-03: at W3, write full SHA-256s into `replay/fixture-manifest.json` **and** mechanically assert each against the 8-hex prefixes in the reviewed plan snapshot (fail closed on any discrepancy) — the manifest must be anchored to the reviewed plan, not self-generated.
  4. attempt-06 RV-04: `.gitignore` is an explicitly planned **Modified** tracked file (one line `rev28/.build/`).
  5. attempt-05 RV-01: R22's "registry/evidence updated consistently" maps to the Rev28 append-only ledger + filesystem manifest + evidence dir (no separate registration/registry artifact exists in Rev28).
  6. attempt-05 RV-02: the rev1→rev3 history contains exactly two reviewed narrowings (capture exact-equality → W2-frozen validated tolerance; any-unexpected-write abort → attributable/unattributable ladder). No CORE→SUPPORTING or blocking→non-blocking downgrades.

## MUST_READ_PLAN
Read the full plan once; before FIRST_ACTION read at minimum: `META`, `GOAL_CONTRACT`, `REQUIREMENTS_AND_CRITICALITY` (R1–R25), `CRITICAL_PATH`, `VERIFIED_REPOSITORY_FACTS`, `ENVIRONMENT_AND_CAPABILITY_MATRIX`, `ARCHITECTURE` §1–§13, `COORDINATE_TRANSFORM_MODEL`, `SYNTHETIC_HARNESS_CALIBRATION_PLAN`, `HISTORICAL_REPLAY_PLAN`, `ADVERSARIAL_TEST_MATRIX`, `REVIEW_PLAN`, `RECONCILIATION_BARRIER_SUPERSESSION`, `LIVE_RUN_ENVELOPE`, `IMPLEMENTATION_WAVES`, `CHANGE_MAP`, `VERIFICATION_AND_ACCEPTANCE` incl. the §7.3 table, `DEGRADATION_AND_GATE_BEHAVIOR`, `RISKS`, `ACCEPTED_TERMINAL_STATES_AND_CLOSURE`, `STATUS_SEMANTICS_AND_CLOSURE_ROUTING`, `DELIVERABLES_MAP`.

## SETTLED_DO_NOT_REOPEN
- Architecture: SCK sensor + Vision perception + Quartz actuator + AX plane + one state machine + append-only ledger (plan §ARCHITECTURE). Do not re-derive alternatives.
- Rev3 is approved by two independent Stage-02 reviews; do not re-litigate plan wording (MINORs are carried above as interpretation).
- Baseline values/methods are frozen: path `album-2024-05-13_to-2024-05-17_57`, 57/17,924,900 B, `b7debe92…` (trailing newline), `ee958e64…` (no trailing newline), JSON `3c932d8c…`.
- Envelope counters: Save All = 1; confirmation = 1; reversible ceiling 12; ≤3 per blocker.
- 25-scenario composition (G01–G22 + X01–X03); 20 replay fixtures; module layout `rev28/`; evidence dir naming; barrier-supersession argument (plan §RECONCILIATION_BARRIER_SUPERSESSION).
- Save All classified `IRREVERSIBLE_SIDE_EFFECT` for this run (conservative; `S-09`).

## REVERIFY_ON_START
Only mutable facts: HEAD/branch/`origin` position; `plan.md` SHA == `63b25602…`; `handoff.md` plan-hash consistency; staging `RUN-20260923-111908-01` still 0 entries; LINE 26.0.2 still installed and not running; accepted baseline still resolves with 57/17,924,900 B and both digests; TCC (ScreenCapture/PostEvent/AX) preflight **in the built binary's context** (V-01 — a false result is a hard gate failure, not a workaround); exact SDK path used per build recorded; concurrent-machine-activity context.

## TRIGGERED_POLICIES
`goal-alignment-design-economy.md`, `workflow-routing.md` (§7 status semantics), `testing-verification.md`, `debugging-recovery.md`, `security-privacy.md`, `high-risk-change.md` (one-shot irreversible run), `performance-concurrency.md`, `context-budget.md`, `git-change-hygiene.md`; `ui-accessibility.md` where AX semantics are touched; `dependencies-contracts.md` only if a stable contract changes; `data-migration.md` only if persistent data is touched.

## FIRST_ACTION
W1 start (CORE, no GUI): create the `rev28/` SwiftPM package skeleton exactly as `§SYSTEM_BOUNDARY_AND_MODULE_MAP`, then implement and run `rev28probe` to record the **executable-context** trust result (TCC/AX preflight inside the built binary) plus SC/Vision/Quartz API availability into `evidence/20260925-rev28-native-closed-loop/capability-probe-exec/` (V-01: `NOT_RUN` → no Phase B; `FAIL` → replan/blocked). Record the exact SDK path used in the build log. Do not touch LINE.

## IMPLEMENTATION_WAVES
- `W1` (CORE, no GUI): package skeleton · capability probe CLI · coordinate transform + tests (validated-tolerance rule, never exact equality) · OCR wrapper + fixtures · capture layer + bbox/config records · identity binding + tests.
- `W2` (CORE, harness): synthetic harness app + separate-process occluder + driver; prove capture per-state matrix and **freeze rule/tolerance** · transforms · Vision localization · Quartz routing · postcondition latency/bounds freeze (≥20 real `NSOpenPanel` runs) · AX chooser observation + affirmation-predicate freeze · focus theft · tripwire attribution · restart/observe-only fixture. Frozen artifacts are mandatory review inputs.
- `W3` (CORE, offline): structural locators + historical replay (20 SHA-bound fixtures; manifest anchored to plan prefixes per carried note 3) + registration/tracking incl. `TrackRectangleRequest` + unit tests.
- `W4` (CORE, policy): state machine · risk classes · ledger incl. `saveAllEmpiricalClassRecord` · staging verifier with the exact predicate + named mismatch classes · chooser driver · postcondition monitor + tests.
- `W5` (CORE, hardening): adversarial matrix G01–G22 + X01–X03 end-to-end in harness + deterministic reruns + defect repair.
- `W6` (SUPPORTING): architecture doc · capability matrix · replay report · deliverable manifest · handoff (already compiled; update only if plan changes).
- `W7` (CORE, conditional): Phase A reconnaissance gate → Phase B single live run under the envelope → filesystem/content verification → final report → local commits (no push).

## ACCEPTANCE_CONTRACT
CORE acceptance first (V-03…V-07, V-10). Every item: `BASELINE_RULE: none` (`BASELINE_REQUIRED: NO`; no item is a `BASELINE_DELTA` gate; the baseline comparison is the success predicate and its own subject), `WAIVER_ALLOWED: NO`, `WAIVER_AUTHORITY: NONE`, default `WAIVER_STATUS: NOT_ALLOWED`, default `CHECK_RESULT: NOT_RUN` (recorded in Stage-04 `execution.md` and the Stage-05 report).

| CHECK_ID | COMMAND/SCENARIO | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY |
|---|---|---|---|---|---|---|---|---|
| V-01 | build & run `rev28probe` in binary context (TCC/AX + SC/Vision/Quartz) | CORE | DIAGNOSTIC | NON_GATING | none | `NOT_RUN` → pending, no Phase B; `FAIL` → replan/blocked | NO | NONE |
| V-02 | W2 harness calibration incl. frozen per-state capture rule | CORE | DIAGNOSTIC | NON_GATING | none | `FAIL` → repair/replan (semantic change) | NO | NONE |
| V-03 | live frames honor capture-geometry invariants | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | unexplained INVALID frame → abort | NO | NONE |
| V-04 | postcondition direct observation (frozen predicate, bounded window) | CORE | OUTCOME | HARD_CLEAN | none | `SAVE_ALL_POSTCONDITION_CONFIRMED` / `NO_CHOOSER_OBSERVED` / `CHOOSER_OBSERVED_AFTER_WINDOW` (§10) | NO | NONE |
| V-05 | chooser identity + exactly-once confirmation | CORE | OUTCOME | HARD_CLEAN | none | refusal → `INDETERMINATE_CHOOSER_REFUSED` (cause enum incl. `frozen_predicate_mismatch`) | NO | NONE |
| V-06 | staging predicate 57/stable/decodable/17,924,900 B/multiset | CORE | OUTCOME | HARD_CLEAN | none | named mismatch classes (§12) | NO | NONE |
| V-07 | baseline unchanged: resolution + both digests + mtimes | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | unresolvable/mismatch → `CHECK_RESULT: BLOCKED`; delta → abort + report | NO | NONE |
| V-08 | replay + adversarial suites (G01–G22, X01–X03) | SUPPORTING | DIAGNOSTIC | NON_GATING | none | failure → repair before Phase B | NO | NONE |
| V-09 | reviews: 7 topics + adversarial + barrier supersession | CORE | DIAGNOSTIC | HARD_CLEAN | none | `REVISION_REQUIRED` → repair + re-review | NO | NONE |
| V-10 | Stage-05 independent acceptance, recomputed from disk | CORE | OUTCOME | HARD_CLEAN | none | compute-from-disk mismatch → fail/replan | NO | NONE |
| V-11 | preservation audit (do-not-touch, no pycache, no push) | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | none | violation → stop + report (never product CORE) | NO | NONE |

Stage-04 durable evidence: append-only `execution.md` (+ `escalation.md` when triggered) in the task dir, carrying orthogonal status subjects and per-item `CHECK_RESULT`. Stage-05 must carry forward Stage-04 outcome evidence without erasing proven facts; required checks may remain pending without deleting already-proven implementation/CORE facts; every repair after a failed attempt starts a new append-only `e2e/attempt-<NN>/`.

## STOP_AND_ESCALATE_IF
- `plan.md`/`handoff.md` revision-hash mismatch, or any stale approval after a plan edit.
- Any change to semantic validity/requiredness/gating/error/fallback/priority meaning, or to any frozen W2 rule (capture tolerance, postcondition bounds, chooser predicate, attribution, restart fixture) — replan + fresh review, never an implementer edit.
- Any new architecture/contract/migration/security/root-cause decision (escalation.md + replan loop).
- Baseline unresolvable/mismatched (`CHECK_RESULT: BLOCKED`) — do not proceed to Phase B.
- An abort condition fires (identity/wrong album, baseline delta, staging precondition, transform invariant, no chooser in window, unattributable write per `S-07`) — stop immediately with zero further input, no retry of irreversible ops.
- Three consecutive reviews on the same unresolved external dependency → `BLOCKED_WITH_ROOT_CAUSE` naming the dependency.
- LINE launch requires session/login or other genuinely external input → report `BLOCKED_WITH_ROOT_CAUSE` after the audit threshold; never ask casually.
- Any temptation to weaken an invariant to obtain approval or to proceed — refuse and escalate.

## HISTORICAL_TASK_DEPENDENCIES
- Issue `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md` (SHA-256 `0b3c9efab209bcb4c8c9b5dcaa5fa1ca6279234df0ee3cc0984da829ead67a2d`) — read §reconciliation barrier.
- `evidence/20260916-route/attempt-07/**` — `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` (preserved, never reinterpreted); read only §barrier rationale.
- `evidence/20260925-rev28-native-closed-loop/capability-probe/**` (round-1/round-2 probe evidence + metadata) — read-only capability inputs.
- 20 replay fixtures under `evidence/20260916-route/**` — exact paths/SHAs in plan §HISTORICAL_REPLAY_PLAN (read that section only).
- Do not scan other `.agent/tasks/*`.

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
HANDOFF_PATH: .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/handoff.md
PLAN_REVISION: 3 (SHA-256 63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828)
STATUS: READY_FOR_IMPLEMENTATION
NEXT_STAGE: 04_IMPLEMENT
