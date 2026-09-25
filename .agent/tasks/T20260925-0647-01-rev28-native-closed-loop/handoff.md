# Handoff — Rev28 native closed-loop LINE album backup (continuation revision 2, post-W1 + W2-partial)

This is the CONTINUATION handoff for a fresh Stage-04 session. The pre-implementation handoff (revision 1, SHA-256 `d1a86814b2a2cc40431a31cadd08eb7d80e87a3969a6ace2d20b1ee3a7a35ed6`) is archived byte-identical at `handoff-history/handoff-plan-r3-20260925T0745+0800.md`. The approved plan did NOT change: `PLAN_REVISION 3`, SHA-256 `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`. Everything below either restates that contract or records verified implementation state as of 2026-09-25 08:2x +0800.

## TASK
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- STATUS: READY_FOR_IMPLEMENTATION (continuation; Stage 04 already in progress — do not restart W1, do not re-plan)
- PLAN_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`
- PLAN_REVISION: `3`
- PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- REVIEW_REQUIRED: YES
- REVIEW_REPORT: `review/attempt-05/review_report.md` (SHA-256 `bdc2069158916c40e435b14c2ab5f2f9f2094c1338070a198ff0c33f8f003310`) and `review/attempt-06/review_report.md` (SHA-256 `b716ccd06fee6711b1094206c29924ee7a54ccd3ab8d3ee28a7482b974fecefc`) — both `PLAN_APPROVED` on revision 3
- REVIEWED_PLAN_REVISION / SHA256: `3` / `63b25602…` (snapshots byte-identical, `review/attempt-05|06/plan_snapshot.md`)
- INDEPENDENT_ACCEPTANCE_REQUIRED: YES (Stage 05; CORE acceptance first, recompute from disk)
- E2E_REQUIRED: YES (true user-journey live run; strictly conditional on every gate; otherwise a scoped blocked/partial state — never "Done")
- ACCEPTANCE_MODE: Stage-02 reviews (done) → W1 (done) → W2 harness freeze (partial) → W3 replay → W4 policy → W5 adversarial → V-09 reviews (7 topics + adversarial + barrier) → Phase A read-only recon → Phase B single live run → filesystem/content verification → Stage 05
- Fresh Implementer required: YES for the continuation session (fresh context; do not import this session's chat)
- Planner/Reviewer transcript required: NO

## GOAL_ANCHOR
- PRIMARY_OUTCOME: a NEW macOS-27-native closed-loop engine (ScreenCaptureKit sense → Vision read → Quartz act → direct postcondition observation → filesystem verify) backs up the LINE group `旻謙允禎成長日記` album `2024/05/13～05/17` (57 photos) into a fresh unique staging run, proving `DUPLICATE_CONTENT_CONFIRMED` against the accepted baseline.
- SUCCESS_EVIDENCE: chooser directly observed in the bounded postcondition window; exactly 57 stable decodable files, no subdirs/partials/zero-byte, total bytes 17,924,900; name-excluded content multiset == `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`; baseline unchanged (manifest tripwire `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`).
- MUST_NOT_BREAK: never claim BACKUP_COMPLETE/duplicate-confirmed from a click, menu change, chooser appearance, or file count alone; exactly one Save All dispatch and exactly one confirmation action for the whole task; no historical coordinates; baseline byte-identical; do-not-touch list preserved; no `__pycache__`.
- Failure outcome is allowed and pre-declared: an honest scoped `INDETERMINATE_*`/`ABORTED_*` terminal with all evidence preserved.

## CONTINUATION_STATE (verified on disk as of the wrap-up commit)
Implementation commits (local; pushed to `origin/master` by the orchestrator in the wrap-up, see §PUSH_AND_GIT_POLICY):
- `ff04f2d` — W1 complete (SwiftPM package `rev28/`, Rev28Core geometry/identity/sensor/OCR, `rev28probe`, 28/28 tests, V-01 PASS in executable context).
- `80cbb5d` — W2 convergent PARTIAL (harness `rev28harness` + `rev28occluder` + `rev28ctl`, Rev28Core Actuation/Chooser/Postcondition/Transaction/Diagnostics), all sources compile, `swift test` 28/28, harness items 8/9 PASS and frozen; items 1/2/4/6 PARTIAL; 3/5/7 NOT_RUN. No W3+ work exists yet.

W2 item status (plan §SYNTHETIC_HARNESS_CALIBRATION_PLAN numbering) — full detail in `evidence/20260925-rev28-native-closed-loop/harness/PARTIAL-status-20260925T0817+0800.json` (SHA-256 `49bc7a2cfada259f104e7eb6d4711e32c54a400463b65d2a2920fc6ab090e7fa`):
- item 1 capture per-state matrix — PARTIAL: 1/16 cells; `noRuleFailClosed=true`, occlusion capture verified; **rule book NOT_FROZEN** (`capture-geometry-rulebook-v1.json` / `capture-matrix-v1.json` do not exist).
- item 2 Vision localization — PARTIAL: 儲存全部×1 in 5-row menu, `57張照片`, 禎/楨 discrimination, ambiguity refused — all proven; row-box/safe-interior rows empty because no frozen rule book.
- item 3 coordinate transforms — NOT_RUN (code-blocked on item 1 freeze, by design).
- item 4 Quartz routing — PARTIAL: failure mode recorded — the harness popup was NOT topmost while the separately-activated peer occluder was up. Must be resolved by evidence before it can pass (see NEXT_ACTIONS 4).
- item 5 postcondition latency/bounds freeze — NOT_RUN (owner STOP-AND-CONVERGE deferred the ≥20-run freeze; plan-time bounds remain 150 ms/8.0 s then 500 ms to 15.0 s cap, ~30 s late forensic sample).
- item 6 chooser AX observation + predicate freeze — PARTIAL: AX calibration PASS (panel AXWindow/AXStandardWindow, 145 nodes, `開啟` button, AXPress succeeded); predicate proof PARTIAL — the real `NSOpenPanel` presented as a **sheet** was refused by clause `notNewWindow`; fake same-process look-alike refused; empty-census widened refusal verified. Canonical `chooser-affirmation-predicate-v1.json` (`20399c4f…`) and `chooser-ax-calibration-v1.json` (`43e221f1…`) are **PROVISIONAL_NOT_VALIDATED** and flagged by `PROVISIONAL-NOT-VALIDATED-20260925T0817+0800.json` (`11ce3eef52b19d9d3c7421426340d19d9c32dfd38d9118be1770314e1976c3b5`).
- item 7 focus theft — NOT_RUN (code-blocked on item 1 freeze).
- item 8 tripwire attribution — **PASS, FROZEN_VALIDATED**: `harness/frozen/tripwire-attribution-ladder-v1.json` SHA-256 `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` (7/7 ladder classifications: L1 stagingExpectedEvidence; L2 attributable `attributedExternalWriteObserved` non-abort; L2 unattributable `abortedUnattributedFilesystemWrite` fail-closed; L3 attributable `abortedWriteOutsideApprovedRoot`; L3 unattributable `environmentalContext` non-aborting; baseline-modified `abortedBaselineModified`; pre-dispatch context).
- item 9 restart/observe-only fixture — **PASS, FROZEN_VALIDATED**: `harness/frozen/restart-observe-only-fixture-v1.json` SHA-256 `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` (4 SIGKILL points, hash chain 4/4, observe-only 4/4, zero new irreversible dispatches).

V-01 evidence (executable-context trust): `capability-probe-exec/probe-record-20260925T074610+0800.json` SHA-256 `499748933e2e089e05275c92147894a95705ab4c8cd8beb50af73ed9918d4b13`; build log `3a744171…`; probe stdout `5d37afeb…`. AXIsProcessTrusted=true, CGPreflightScreenCaptureAccess=true, CGPreflightPostEventAccess=true; SCK OK (7 windows/1 display); Vision read `儲存全部` + `57張照片`; Quartz event construction OK (no events posted). LINE was never launched.

Build/test evidence for the W2 commit: `harness/build-test-log-20260925T0817+0800.txt` SHA-256 `91ae29a28c6ae65b66e7024478e725790f35ed18e0987ede6ce95a6443f4943e`; 11 calibration runs under `harness/runs/HARNESS-*` (summary SHAs in the PARTIAL-status record). `swift build` = Build complete (one pre-existing warning, `rev28harness/HarnessApp.swift:531` unused `try?`); `swift test` = 28 tests, 0 failures.

`execution.md` (durable Stage-04 record): SHA-256 `eab33ae1264c042bd7627b30d8523caed87353601de3bf20f09e41b88ecba5cc`, Update 1 (W1) + Update 2 (W2 partial). Historical prior execution artifacts are append-only.

## CRITICAL_PATH (unchanged; ordered)
1. W1 capability + package — DONE.
2. W2 harness calibration + **frozen rules** (capture per-state rule, postcondition bounds, chooser predicate, tripwire ladder, restart fixture) — IN PROGRESS (only items 8/9 frozen).
3. W3 offline: structural locators + 20-fixture historical replay + registration/tracking + unit tests.
4. W4 policy: state machine, risk classes, ledger, staging verifier (exact RV-02 predicate + named mismatch classes), chooser driver, postcondition monitor.
5. W5 hardening: 25-scenario adversarial matrix G01–G22 + X01–X03, deterministic reruns.
6. V-09 reviews (7 topics + adversarial + barrier supersession) on frozen SHAs — hard pre-live gate.
7. Phase A read-only LINE reconnaissance (zero side-effecting dispatch) → gate (g).
8. Phase B: one ellipsis, one Save All, direct chooser observation, one confirmation into a unique staging run, download.
9. Filesystem + content verification → `DUPLICATE_CONTENT_CONFIRMED`; baseline unchanged.
10. Stage 05 independent acceptance → closeout (ledger, manifests, final report, local commits).

## SEMANTIC_INVARIANTS (do not change; any change = replan + fresh review, never a bounded fix)
- `S-01` exactly-once irreversibles: Save All dispatch = 1; destination confirmation = 1 and only the one pre-chosen action (`AXPress` **or** `Return`, never both); a non-effect consumes the budget; no blind retry; crash resume is observe-only.
- `S-02` success predicate: exactly 57 image files, no subdirs/partials/zero-byte, decodable, stable (≥3 samples ≥4 s + ≥5 s quiescence), total bytes 17,924,900, and `SHA-256(sort(values).joined("\n"))` (no trailing newline) == `ee958e64…`; filenames excluded by design.
- `S-03` identity/epochs: selection by bundle + pid-instance + layer + live geometry, never windowID alone; windowID valid only inside one capture epoch; stale ID invalidates; no historical coordinate may ever be reused.
- `S-04` transform invariants 1–5 (plan §COORDINATE_TRANSFORM_MODEL): validated-tolerance vs the W2-frozen rule (never exact equality); recorded bbox drives the transform; origin consistency incl. same-epoch re-read; `pointPixelScale` must equal `NSScreen.backingScaleFactor`; no implicit 2×; click point within 1 pt of a safe-interior boundary → refuse/re-locate.
- `S-05` postcondition: one bounded window, single evidence standard; cadence ≤150 ms first 8.0 s then ≤500 ms to hard cap 15.0 s (W2 re-freezes with ≥20 measured real-`NSOpenPanel` runs; review 4 binds); late affirmative (~30 s forensic sample) → `CHOOSER_OBSERVED_AFTER_WINDOW`; none → `NO_CHOOSER_OBSERVED`; logs/panel presence/click-return never sufficient.
- `S-06` chooser predicate: frozen 4-clause predicate (§11) incl. ownership via panel-process census + bundle/code-sign + process start time (pid reuse rejected); an empty/indeterminate pre-census **widens refusal**, never relaxes; ambiguity → `INDETERMINATE_CHOOSER_REFUSED` (cause enum incl. `frozen_predicate_mismatch`); never loosen ad hoc.
- `S-07` tripwire ladder (frozen, item 8): L1 staging evidence; L2 attributable → `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED` (non-fatal, disclosed); L2 unattributable → `ABORTED_UNATTRIBUTED_FILESYSTEM_WRITE`; baseline modified → immediate abort; L3 attributable-to-run → `ABORTED_WRITE_OUTSIDE_APPROVED_ROOT`; L3 unattributable → environmental context, non-aborting, disclosed.
- `S-08` baseline fail-closed: canonical path = `baseline-content-multiset.json.source_dir` (JSON SHA `3c932d8c…` checked first); realpath-resolve; 57 files / 17,924,900 B; recompute `b7debe92…` (trailing-newline method) and `ee958e64…` (no trailing newline); unresolvable/mismatch → `CHECK_RESULT: BLOCKED` (no degraded comparison, no Phase B).
- `S-09` Save All executes under `IRREVERSIBLE_SIDE_EFFECT` semantics this round; record `saveAllEmpiricalClassRecord`; `PRE_SIDE_EFFECT_ACTION` stays defined but unused.
- `S-10` recovery budget: ≤3 attempts per identical blocker with fresh preconditions; global reversible-dispatch ceiling 12 → `ABORTED_REVERSIBLE_BUDGET_EXHAUSTED`; two consecutive failed revalidations of the same candidate → abort (stricter cap wins).
- `S-11` status semantics v4.2: keep PRIMARY_OUTCOME / IMPLEMENTATION / CORE_ACCEPTANCE / REQUIRED_VERIFICATION / INDEPENDENT_ACCEPTANCE / TASK_CLOSURE orthogonal; `IMPLEMENTATION_BLOCKED` only for unfinished product implementation, always scope-named; no naked `BLOCKED`; `DONE` only on primary-outcome achievement.
- `S-12` frozen-rule freeze: after a W2 rule is reviewed, changing it = replan + fresh review.
- `S-13` scope/preservation: only `rev28/**`, `evidence/20260925-rev28-native-closed-loop/**`, the task dir, and the one `.gitignore` line (`rev28/.build/`) may change; DO_NOT_TOUCH stays byte-identical; no `__pycache__`.
- `S-14` Foundation Models diagnostics only; beta APIs never the sole production gate.

## BEST_EFFORT_DO_NOT_GATE
Foundation Models diagnostics; registration/rectangle-tracking evidence (R6/R7); `VNRecognizeTextRequest` parity wrapper — degrade to deterministic-only, never block the core path. `V-11` is `REPOSITORY_HEALTH`/`NON_GATING` for closure (violation is reported, never re-labelled product CORE).

## DEFERRED_NOT_THIS_TASK
No second accepted production copy; no copying staging into the baseline; no cleanup/deletion of staging or baseline; no attempt-07 reclassification; no Rev27e-WIP modification; no production Foundation Models use; no scope beyond the named album/group.

## REPO_ANCHOR
- Project root: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`; branch `master`; remote `origin` = `https://github.com/s9008129/Line_backup.git`
- Anchor at wrap-up: HEAD `80cbb5d9f79a84d19abbdec544bc7c51b53fb090`; the wrap-up commit for this handoff follows it; after the owner-authorized push, `git rev-list --left-right --count origin/master...HEAD` must be `0  0`.
- Dirty state: untracked-only pre-existing work (Rev27e WIP, `PLAN-2026-09-23-rev27e*.md`, prior evidence incl. three `__pycache__` dirs under `evidence/20260916-route/tools/**`) — preserved, never staged. No tracked modifications.
- Staging `…/staging/RUN-20260923-111908-01` = 0 entries (unchanged). LINE 26.0.2 installed, not running.

## PUSH_AND_GIT_POLICY
- The approved plan (R25/S-13) said "no push". On 2026-09-25 the OWNER explicitly instructed push, which supersedes the plan on this point: commit `ff04f2d` (W1), `80cbb5d` (W2 partial) and the wrap-up handoff commit are pushed to `origin/master`. This is a documented owner-authorized deviation for git policy only — it changes no engine semantic, gate, or evidence rule.
- Continuation policy: local commits at wave boundaries are allowed (explicit paths only); do NOT `git add -A`/`.`; never stage Rev27e WIP or `__pycache__`; keep pushing only if the owner asks in the new session, otherwise stay local (state it in the final report).

## REVERIFY_ON_START (only mutable facts; run before any edit)
1. `git log --oneline -3` shows `80cbb5d` and the wrap-up commit; `git status` untracked-only; ahead/behind vs `origin/master`.
2. `shasum -a 256 .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md` == `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`.
3. `shasum -a 256` of `handoff.sha256` must equal the SHA in that file (its own file lists the SHA of `handoff.md` as written at wrap-up).
4. `xcrun swift build --package-path rev28` + `xcrun swift test --package-path rev28` → build complete, 28/28 passing.
5. Integrity of the two frozen artifacts (`d67abb17…`, `146b373a…`) and the two PROVISIONAL predicate files (`20399c4f…`, `43e221f1…` + marker `11ce3eef…`) against `harness/frozen/sha256sums-HARNESS-20260925-081236.txt`.
6. staging `RUN-20260923-111908-01` still 0 entries; LINE installed and not running; baseline resolves with 57 files / 17,924,900 B and both digests.
7. TCC/AX preflight **in the built binary's context** (rerun `rev28probe`; a false result is a hard gate failure, not a workaround).

## MUST_READ_PLAN / MUST_READ_FIRST
Read, in this order: this handoff → `execution.md` (Update 1 + Update 2) → plan sections `META`, `GOAL_CONTRACT`, `REQUIREMENTS_AND_CRITICALITY` (R1–R25), `CRITICAL_PATH`, `ARCHITECTURE` §1–§13, `COORDINATE_TRANSFORM_MODEL`, `SYNTHETIC_HARNESS_CALIBRATION_PLAN`, `HISTORICAL_REPLAY_PLAN`, `ADVERSARIAL_TEST_MATRIX`, `REVIEW_PLAN`, `RECONCILIATION_BARRIER_SUPERSESSION`, `LIVE_RUN_ENVELOPE`, `IMPLEMENTATION_WAVES`, `VERIFICATION_AND_ACCEPTANCE` + §7.3 table, `DEGRADATION_AND_GATE_BEHAVIOR`, `RISKS`, `ACCEPTED_TERMINAL_STATES_AND_CLOSURE`, `STATUS_SEMANTICS_AND_CLOSURE_ROUTING`, `DELIVERABLES_MAP`. Then the harness evidence: `harness/PARTIAL-status-20260925T0817+0800.json` and the frozen artifacts.

## SETTLED_DO_NOT_REOPEN
- Architecture (SCK + Vision + Quartz/AX + one state machine + append-only ledger), module layout, plan revision 3 approvals, baseline values/methods, envelope counters, 25-scenario composition (G01–G22 + X01–X03), 20 replay fixtures, barrier-supersession argument.
- W1 implementation design (coordinate spaces, identity binding, capture records, OCR wrapper) — verified and committed.
- Carried MINOR review clarifications from revision-2 review attempts (already applied): envelope abort item resolves through the §10 ladder (L2 fail-closed, L3-unattributable non-aborting); `LIVE_RUN_INTERLOCK` = "part of the authorized run's gate chain"; W3 replay manifest must be anchored to the reviewed plan's 8-hex prefixes; `.gitignore` is an explicitly Modified tracked file; R22 "registry/evidence" maps to ledger + manifest + evidence dir.
- **Naming decision for the chooser predicate republish (resolved here, do not escalate):** append-only forbids overwriting the PROVISIONAL `chooser-*` v1 files. When the predicate proof becomes fully validated, publish **new v2 files** (`chooser-affirmation-predicate-v2.json`, `chooser-ax-calibration-v2.json`) in the canonical frozen dir, keep the v1 + PROVISIONAL marker as history, and record the supersession in the sha256sums file and `execution.md`. This is an evidence-naming convention, not a semantic change.
- **Item 4 (popup z-order) and item 6 (sheet-vs-standalone panel) are known failure modes to fix with evidence**, not design questions: fix the harness scenario (bring the popup above the peer occluder / present the panel as the shape the predicate calibrates against, or add the calibrated sheet clause to the predicate proof) and re-run; if a fix would change `S-06`'s predicate semantics or any `S-0x` invariant, that IS a replan.

## FIRST_ACTION
Reverify (`REVERIFY_ON_START` 1–7), then W2 item 1: run the FULL 16-cell capture matrix via `rev28ctl harness-calibrate --items 1` (no `--max-cells` cap) → publish the canonical `harness/frozen/capture-geometry-rulebook-v1.json` + `capture-matrix-v1.json` with a sha256sums file; only cells actually observed may be frozen. Then proceed per `NEXT_ACTIONS`.

## NEXT_ACTIONS (ordered; exit criteria in parentheses)
1. W2 item 1 full matrix → freeze rule book + matrix (**FROZEN_VALIDATED** with per-cell residuals; no-rule fail-closed preserved).
2. W2 items 3 (coordinate transforms: window moved ±, round-trips, wrong-scale injection detected) and 7 (focus theft) — re-run post-freeze (**PASS with evidence records**).
3. W2 item 4 fix popup-vs-peer-occluder z-order and re-prove Quartz routing (click lands on the topmost popup; hit-test recorded) (**PASS**).
4. W2 item 2 re-run post-freeze: row-box + safe-interior repeatability, ambiguity refusal (**PASS**).
5. W2 item 5: ≥20 real `NSOpenPanel` latency runs → freeze cadence/bounds (**review-4 input, FROZEN_VALIDATED**).
6. W2 item 6: repair panel presentation; complete the predicate proof; republish per the resolved naming decision (**FROZEN_VALIDATED; review-6 input**).
7. W3: structural locators + 20-fixture replay + `replay/fixture-manifest.json` anchored mechanically to the reviewed plan's 8-hex prefixes (fail closed on mismatch) + registration/`TrackRectangleRequest` + unit tests (**tests pass; replay divergences recorded, never threshold-tuned**).
8. W4: state machine, risk classes, ledger incl. `saveAllEmpiricalClassRecord`, staging verifier with the exact `S-02` predicate + named mismatch classes, chooser driver, postcondition monitor + tests (**tests pass**).
9. W5: adversarial matrix G01–G22 + X01–X03 end-to-end in the harness, deterministic across two runs (**PASS, semantic equality**).
10. V-09: seven pre-live topic reviews + adversarial review + reconciliation-barrier supersession review, each bound to frozen SHAs (fresh reviewer contexts). Production only if all approve (**all APPROVED on frozen SHAs**).
11. Phase A read-only LINE reconnaissance (frozen locators only; zero side-effecting dispatch) → gate (g) (**PASS or repair/replan**).
12. Phase B single live run under `LIVE_RUN_ENVELOPE` (Save All=1, confirmation=1, reversible ceiling 12) → filesystem/content verification → `DUPLICATE_CONTENT_CONFIRMED` (**exact `S-02` predicate + baseline unchanged**).
13. Stage 05 independent acceptance (recompute from disk; never trust Stage-04 claims) → closeout (final report, deliverable manifest, local commits) (**CORE acceptance first; then supporting**).

## IMPLEMENTATION_WAVES (status-annotated)
- `W1` (CORE, no GUI): **DONE** (`ff04f2d`; 28/28; V-01 PASS).
- `W2` (CORE, harness): **PARTIAL** — items 8, 9 FROZEN_VALIDATED; 1, 2, 4, 6 PARTIAL; 3, 5, 7 NOT_RUN. Open per NEXT_ACTIONS 1–6.
- `W3` (CORE, offline): NOT STARTED.
- `W4` (CORE, policy): NOT STARTED (some scaffolding already exists: `PostconditionMonitor`, `FolderChooserDriver`, `IntentLedger`, `TripwireAttribution`, `AXDriver`, `QuartzActuator`).
- `W5` (CORE, hardening): NOT STARTED.
- `W6` (SUPPORTING): NOT STARTED (handoff exists; architecture doc/capability matrix/replay report/deliverable manifest pending).
- `W7` (CORE, conditional): NOT STARTED; gated on 10–12 above; Phase A/B only after every pre-live gate.

## ACCEPTANCE_CONTRACT
CORE acceptance first (V-03…V-07, V-10). Every item: `BASELINE_RULE: none` (`BASELINE_REQUIRED: NO`), `WAIVER_ALLOWED: NO`, `WAIVER_AUTHORITY: NONE`, default `WAIVER_STATUS: NOT_ALLOWED`, default `CHECK_RESULT: NOT_RUN` (recorded in `execution.md` and the Stage-05 report).

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
| V-11 | preservation audit (do-not-touch, no pycache) | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | none | violation → stop + report (never product CORE) | NO | NONE |

Live-run interlock mapping (carried clarification): pre-live for V-01/V-02/V-08/V-09; live-time for V-03…V-06; pre-live + closeout for V-07; V-10 gates closure; V-11 is the closeout audit. Stage-05 must carry forward Stage-04 outcome evidence without erasing proven facts and must recompute from disk.

## STOP_AND_ESCALATE_IF
- `plan.md`/handoff revision-hash mismatch, stale approval after any plan edit.
- Any change to semantic validity/requiredness/gating/error/fallback/priority meaning, or to a frozen W2 rule (capture tolerance, postcondition bounds, chooser predicate, attribution, restart fixture) — replan + fresh review.
- Any new architecture/contract/migration/security/root-cause decision (`escalation.md` + replan loop).
- Baseline unresolvable/mismatched (`CHECK_RESULT: BLOCKED`) — no Phase B.
- Any abort condition fires (wrong album/identity, baseline delta, staging precondition, transform invariant, no chooser in window, unattributable write per `S-07`) — stop immediately, zero further input, no retry of irreversible ops.
- Three consecutive reviews on the same unresolved external dependency → `BLOCKED_WITH_ROOT_CAUSE` naming the dependency.
- LINE launch requires session/login or other external input → report `BLOCKED_WITH_ROOT_CAUSE` after the audit threshold.
- Any temptation to weaken an invariant to obtain approval or to proceed → refuse and escalate.

## HISTORICAL_TASK_DEPENDENCIES
- Issue `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md` (SHA-256 `0b3c9efab209bcb4c8c9b5dcaa5fa1ca6279234df0ee3cc0984da829ead67a2d`).
- `evidence/20260916-route/attempt-07/**` — `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` (preserved; read only the barrier rationale).
- `evidence/20260925-rev28-native-closed-loop/capability-probe/**` (round-1/2 probe evidence) — read-only capability inputs.
- 20 replay fixtures under `evidence/20260916-route/**` — exact paths/SHAs in plan §HISTORICAL_REPLAY_PLAN.
- Do not scan other `.agent/tasks/*`.

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
HANDOFF_PATH: .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/handoff.md
HANDOFF_REVISION: 2 (continuation; rev 1 archived at handoff-history/handoff-plan-r3-20260925T0745+0800.md, SHA-256 d1a86814b2a2cc40431a31cadd08eb7d80e87a3969a6ace2d20b1ee3a7a35ed6)
PLAN_REVISION: 3 (SHA-256 63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828)
STATUS: READY_FOR_IMPLEMENTATION
NEXT_STAGE: 04_IMPLEMENT (continuation)
