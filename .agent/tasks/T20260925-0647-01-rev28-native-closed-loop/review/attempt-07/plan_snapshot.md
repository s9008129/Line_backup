# Rev28 native closed-loop backup — Plan revision 4

## META

TASK_ID: T20260925-0647-01-rev28-native-closed-loop  
PLAN_REVISION: 4  
PLAN_STATUS: CANDIDATE_UNAPPROVED  
ROLE: STAGE_01_HIGH_REASONING_PLANNER  
TASK_CLASS: CRITICAL  
ANALYSIS_BOUND_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da  
TARGET_BRANCH: rev28-prelive-finalization  
REPOSITORY: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup  
PLAN_VALIDITY_DECISION: PLAN_REVISION_REQUIRED  
PLAN_REVIEW_REQUIRED: YES  
INDEPENDENT_ACCEPTANCE_REQUIRED: YES  
NEXT_ROUTE: READY_FOR_PLAN_REVIEW, subject to final remote freshness record

This is a Stage 01 proposal, not implementation authorization or a new handoff. The immediate next route is Fresh Independent Stage 02 Plan Review. Stage 03 may compile a new execution contract only after approval of these exact plan bytes. Stage 04 must then use a fresh implementer. No new final handoff is created here.

Harness authority: installed V4.3 ~/.codex/AGENTS.md, prompts/01b_debug_plan_prompt.md, policies/workflow-routing.md and the triggered convergence, review, testing, debugging, git, high-risk and model-routing policies. Capability roles are model-agnostic. Persistent /goal, if later explicitly requested, is a Stage 04 execution facility only.

## PRIMARY_OUTCOME / GOAL_ANCHOR

Produce one newly downloaded staging copy from real LINE (`jp.naver.line.mac`), group **旻謙允禎成長日記**, album **2024/05/13～05/17**, through the reviewed native macOS path. Authoritative filesystem evidence must prove `DUPLICATE_CONTENT_CONFIRMED`:

- Exactly **57 complete stable decodable regular image files**; no symlink, directory, hidden extra entry, other non-image entry, partial suffix, zero-byte file or duplicate content within staging.
- Exactly **17,924,900 bytes**.
- Filename-excluded content multiset SHA-256: **ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf**.
- Baseline unchanged, including per-file names, bytes and mtimes. Name-inclusive tripwire SHA-256: **b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd**.
- Achieved production run: exactly **one Save All dispatch** and exactly **one destination confirmation**. Under refusal/failure these are ceilings, not actions to complete regardless of risk. An irreversible intent permanently consumes its operation budget even if the effect is unknown.
- Full fresh identity/geometry/chooser/transaction chain and independent Stage 05 recomputation. Build, test, click-return, menu disappearance, chooser appearance and file count alone cannot prove the primary outcome.

Frozen baseline reference: `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json`, SHA-256 **3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2**. Its `source_dir` is authoritative: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` (underscore in `_to_`; never substitute the historical typo).

Digest algorithms: multiset = SHA256 of lexicographically sorted per-file lowercase SHA-256 strings joined by newline, **no trailing newline**. Baseline tripwire = SHA256 of sorted `relative-name\tsize\tsha256` lines, newline-separated **with one trailing newline**. The notation describes actual tab/newline characters. Compare full digests and per-file metadata, not abbreviated prefixes.

## OBSERVED_FAILURE / CURRENT_BLOCKER / ROOT CAUSES / OUTCOME GAP

SYMPTOM: `StructuralLocatorsTests.swift` compilation reports non-callable `SurfaceBinding`, undefined `ocr`, and contextual `Equatable.referenceStructureMismatch` errors.

CURRENT_BLOCKER: deterministic test target does not compile, so tests cannot execute at the analysis HEAD. Local Swift product build PASS; focused test command fails before test execution. Exact-head CI run **36411316643** likewise has build PASS and deterministic tests FAIL; dependent adversarial/replay/headed checks skipped.

COMPILE_ROOT_CAUSE: new tests in commit 0d373ae call the existing computed `binding` property as `binding()` and use missing `ocr` helper calls rather than the existing `item` interface. The refusal enum member exists; its diagnostic is secondary type-inference fallout. This conclusion is source/history/compiler grounded, not a guess based on the reported symptoms.

PRIMARY_ROOT_CAUSE: missing production composition and its explicit observation/transaction binding contract. Current `rev28ctl live-execute` unconditionally refuses after inventory checks; no real NativeObservationSession/LiveExecutionAdapter calls the common engine. High-level fake adapter tests supply successful chooser, destination and content evidence instead of exercising the native composed path. Current helper APIs also do not jointly enforce a single fresh observation chain or all irreversible eligibility conditions.

PRIMARY_OUTCOME_GAP: no reachable, validated real-Mac path currently connects exact album observation to guarded one-shot dispatch, actual chooser, stable staging proof and unchanged baseline. The compile regression is the first blocker to diagnosing that path; fixing it alone cannot close the gap.

Additional independently reproduced defects: (1) album segmentation accepts full end dates but returns zero regions for the target's short end date; (2) stability accepts equal last samples spanning 0.2 seconds by borrowing elapsed time from an older different sample. See `analysis/r4-20260928/source-analysis.md` and diagnostic logs. No product/test code was changed during planning.

## ROOT_CAUSE_HYPOTHESES / DIAGNOSTIC_SEQUENCE

| Competing explanation | Smallest distinguishing evidence | Current disposition |
|---|---|---|
| Compiler/SDK incompatibility causes all reported errors | Build product targets; inspect test declarations and offending commit; link the existing refusal enum from the built module | Product build passes and enum resolves. No toolchain change is justified by these diagnostics. |
| New tests violate the local helper interface | Compare property/function declarations with calls introduced by 0d373ae; focused Swift test compilation | Confirmed compile root cause; repair remains future Stage 04 work. |
| Correcting helper calls is sufficient for target-card tests | Run current segmenter against short and full end-date inputs without changing product/test source | Falsified: short target date produces zero regions; full-date control produces two and a candidate. |
| Existing stability check enforces four seconds of equal samples | Feed one older different snapshot followed by three equal snapshots spanning 0.2 seconds | Falsified: current function returns true; regression case and bounded repair required. |
| Complete native production orchestration already exists and tests are the sole blocker | Trace both live CLI commands, engine callers and adapter conformances; inspect integration oracle | Falsified: unconditional live-execute refusal and no native adapter; test supplies high-level successful verdicts. |
| Real LINE permissions, layout, chooser or album contents ultimately prevent success | Current-binary capability and real Phase A, then only the conditional single Phase B for deferred chooser/content facts | Unresolved. Source analysis cannot prove these live facts; no speculative fix or irreversible diagnostic is authorized here. |

Completed diagnostic sequence: remote/worktree binding -> historical/current-source comparison -> product build -> focused test compile -> independent segmenter probe -> stable-interval/enum probe -> frozen provenance check -> read-only baseline comparison. Exact commands, output and times are under analysis/r4-20260928. No exact-head successful full suite is claimed. Future sequence is FIRST_ACTION followed by C1–C7 and the phase gates; repeating the same failed compile without a new distinguishing change adds no information.

## PLAN VALIDITY AND HISTORY

R3's outcome, historical truth and safety goals survive. R3 is not a valid current execution contract: it describes state.json persistence, while implementation now uses ledger-derived state; its Phase A and resume expectations conflict with preflight consuming the one-shot file and creating an observe-only-on-resume owner; a native session and real adapter remain absent; current readiness recaptures and high-level test seams do not establish the required chain.

R3 exact bytes are archived as `plan-history/plan-r3-before-20260928-replan.md`, SHA-256 **63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828**. Reviews 01–06, their snapshots, handoff-history, current handoff and execution remain historical evidence. Prior approvals are not R4 approvals. `decision.md` marks the old handoff STALE / SUPERSEDED_CANDIDATE without rewriting it.

Explicit R4 architecture decisions requiring Stage 02 review:

1. One ledger-derived owner replaces state.json as transaction authority; a checkpoint is an integrity witness, not a second state authority.
2. One native observation session supplies immutable, coherent evidence to the common safety logic. CI injects below that logic.
3. Phase A never consumes irreversible intent/token budgets. Verified **pre-intent** continuation may re-observe and continue; any irreversible intent, uncertain history, corrupt/missing anchor, or process result of unknown status forces observe-only. This narrowly changes the current blanket nonempty-ledger resume behavior; it does not permit an irreversible retry.
4. Production confirmation is **one AXPress on a unique bound default button**. No production Return fallback. Return used for proven Go-to-folder navigation must be separately bound to that navigation sheet.
5. Current owner refusal of an attributable pre-chooser staging write is retained as a stricter confirmation gate. Such a write is still L1 evidence, not silently relabeled as an L2/L3 scope violation.
6. The current frozen late-delay field means 30 seconds after the monitor's normal 15-second window (~45 seconds total on that path). Preserve it as forensic-only; it never enlarges the 15-second success window. Document the difference from R3's approximate “~30 s” prose.

Only the archived R3 **20-fixture list/hash anchors**, **G01–G22/X01–X03 definitions**, and **do-not-touch inventory** are incorporated as technical annexes. R4 states current architecture, gates, sequencing and status rules; old readiness/approval/first-action/closure claims are not inherited.

## ASSUMPTIONS AND UNKNOWNS

- Baseline read-only recomputation this turn matched 57 / 17,924,900 / both full digests; final preservation audit compares per-file mtimes too. Old staging `RUN-20260923-111908-01` was empty. Recheck both at every execution start and closeout.
- Real LINE remains capable of exposing exact group/album/count and the reviewed menu structure. This is **unverified on current live surfaces**; Phase A must resolve it. No OCR spelling correction may merge 禎 and 楨.
- Real LINE chooser hosting shape cannot be fully observed before the single Save All. Phase A proves available assumptions and real NSOpenPanel calibration, not a fictitious observation of LINE's future chooser. Post-dispatch frozen-predicate mismatch is an accepted fail-closed risk.
- TCC, executable identity, display arrangement, SDK, LINE version/session and window topology are mutable. A prior/hosted grant does not establish the production binary's current permission.
- FSEvents supplies path/timing, not authenticated writer PID. Native collector must record attribution evidence and uncertainty honestly; unknown attribution follows the frozen ladder.
- No currently proven new production result is assumed. Rev27 `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` remains exactly that; it is neither success nor failure. Coordinates from history remain replay evidence only.

## CRITICAL_PATH

1. Reverify remote HEAD, R4 review/handoff bindings and preservation state; initialize durable convergence telemetry from history.
2. Repair only the test helper regression; compile/run focused tests. Resolve the separately evidenced date-format and stability defects without weakening identity or acceptance.
3. Implement one common native composition with coherent observations, owner/ledger/anchor authority, native tripwire collection and typed evidence. Close the actuation and chooser binding gaps before connecting irreversible dispatch.
4. Exercise that exact common composition through injected OS boundaries, real synthetic AppKit panels, frozen provenance, replay and adversarial checks. Complete independent V-09 code/rule review.
5. Phase A on real Mac/LINE, Save All=0 and confirmation=0; publish evidence. Complete V-09 supplements for LINE-specific sensor/menu/chooser assumptions.
6. Recompute machine eligibility on exact reviewed plan/source/binary/rules plus fresh observations. Only if every pre-B condition passes may the separately authorized Phase B consume the one-shot budget.
7. Single Save All -> strict actual chooser observation -> guarded reversible destination preparation -> single AX confirmation -> bounded read-only download observation -> stable/content/baseline proof.
8. Append finalized evidence and empirical classification, then Fresh Independent Stage 05 recomputation. Close only after all outcome and closure gates pass.

No documentation cleanup, framework rewrite, broad workflow repair, second backup, or unrelated repository-health work precedes the shortest core route above.

## CORE WORK AND ARCHITECTURE CONTRACT

### C1 — Restore diagnostic execution, preserve identity rules

Use the existing XCTest helper interfaces in the two new tests. Do not delete tests, skip them, replace expected refusals, or add fake acceptance data. Then address date segmentation as a separately measured attempt: accept only explicitly supported exact date representations of the authorized interval, including the short end date already used by the target. Canonical separators may be mapped explicitly; no fuzzy identity, guessed year from unrelated cards, count borrowing or group glyph substitutions.

Card segmentation and association must operate on the **same captured image**. Prove actual non-overlapping card containers for the calibrated layout, one exact date anchor and its own count. Missing/truncated anchors, multiple columns without a validated layout, ambiguous card boundary, duplicate target or cross-card count -> refusal. A full-width midpoint band is not proof for an unknown layout. Album detail must preserve and re-confirm exact album date as well as group and 57-count continuity. Ellipsis is localized on that album header, never a card/thumbnail menu.

### C2 — One safety-critical orchestration

Extend existing LiveExecutionEngine and PersistentTransactionOwner; do not build an unrelated “production engine.” `live-preflight` and `live-execute` enter the same composition and phase controller. They differ by permitted phase/capability. Production CLI rejects CI execution; deterministic tests use injected sensors, clock, filesystem and event sink without changing state machine, gate evaluator, evidence validator or transaction authority.

Implement a real adapter using WindowSensor, FrameCaptureService, OcrEngine, StructuralLocators, AlbumEllipsisLocator, guarded Quartz, StrictPostconditionMonitor, FolderChooserDriver, BaselineVerifier and StagingVerifier. High-level adapter output cannot declare a state valid merely by returning a hex digest or constructed successful enum. Common code validates typed, run-bound evidence and underlying files before transitions. Keep fast unit fakes, and add composed tests whose substitutions are below perception/predicate/state/intent decisions.

State authority remains monotonic through APP_READY, GROUP_READY, ALBUM_LIST_READY, TARGET_ALBUM_LOCATED, ALBUM_DETAIL_VERIFIED, ELLIPSIS_LOCATED, MENU_VERIFIED, SAVE_ALL_LOCATED, CHOOSER_VERIFIED, DESTINATION_PREPARED, DOWNLOAD_CONFIRMED, DOWNLOAD_IN_PROGRESS, FILESYSTEM_STABLE, CONTENT_VERIFIED, FINALIZED. Refusal/indeterminate/abort are explicit terminal records. Re-observation is recorded without inventing a backward state transition or resetting any counter.

### C3 — Observation authority

Add one serialized NativeObservationSession (name may vary mechanically) whose immutable ObservationBundle contains:

- Session ID, monotonic capture start/end, deadline, epoch, actual process PID/start time, bundle/signing identity, window identity and fresh pre/post SCK/CG/AX inventory references.
- Exact retained screenshot bytes/CGImage, PNG SHA, capture configuration, included windows, sourceRect, bbox, image dimensions, independent backing scale, frozen rule ID/hash, per-side residual and validity.
- Vision results from that exact retained image, explicit identity decisions, structural regions/candidate and SurfaceBinding; AX evidence tied to that window/process interval.
- Tripwire journal cursor/range, baseline reference, evidence paths/hashes and observation failure states. No observer exception becomes an empty successful observation.

Independent sensor acquisition is permissible inside this session with pre/post consistency checks and bounded timestamps. Mixing unrelated epochs, recapturing one image for hash and another for OCR, reusing an old candidate while relabeling its epoch/time, or using caller flags as proof of freshness is forbidden. Every new capture has new provenance; equal pixels do not make an old observation fresh. Redraw/hash changes require re-localization, not a requirement to force pixels to remain identical.

Use frozen geometry configuration for capture and readiness alike. A state without a matching frozen rule or independently known scale is invalid. Preserve window/capture/screen coordinate transform, sourceRect offset, bbox union semantics and 1-point safe-boundary refusal (convert correctly at Retina scale; not 1 pixel). Multiple displays remain fail-closed unless separately replanned/calibrated.

### C4 — Single durable transaction authority

Owner + IntentLedger alone govern phase, state, goal identity, all dispatch budgets, authorization and bound evidence. Use a **persistent goal slot**, keyed to this task/group/album/approved new-path authorization, so choosing a new UUID, destination, ledger path, token filename or session cannot reset the one-shot entitlement. Lock it for a single writer. Refuse a second owner/race. Preserve stale-writer detection and hash-chain checks.

Require an independently stored head anchor/checkpoint in production from initialization onward, including parent-directory durability for new critical files. Before reconstructing state, verify ledger sequence/hash chain, full bytes, anchor and goal slot. Empty/truncated ledger with retained goal/anchor state is not a new transaction. Missing/corrupt/uncertain state is refusal; never regenerate an anchor from untrusted history or silently initialize a replacement ledger. Any ledger/anchor update error prevents dispatch.

Persist all reversible counts, per-identical-blocker counts and consecutive candidate revalidation failures in this owner. LiveDispatchBudget or in-memory counters may be derived views only. Maximum reversible semantic dispatches 12 across Phase A/B; maximum 3 per identical blocker; 2 consecutive failed revalidations abort. A compound destination preparation logs/checks every input primitive and cannot conceal retries inside one budget record. Reviewed semantic action grouping (e.g. one key chord) is fixed, not renamed to bypass a ceiling.

Phase A may append authorization/observation/reversible records but must leave **intent.saveAll=0, attempt.saveAll=0, intent.destinationConfirmation=0, attempt.destinationConfirmation=0** and the one-shot execution entitlement unconsumed. Preflight must not rename it to .consumed. Only the durable Save All reservation arms/consumes it; a convenience token marker is not authority.

**Pre-intent continuation:** allowed only after verifying the complete goal slot + ledger + anchor, exact unchanged authorization/review bindings, no terminal refusal requiring replan, and zero irreversible records. Reacquire all live facts, restart observation deadlines and preserve every state/budget record. Phase A evidence with stale process/window/epoch cannot supply a permit. This is not a reset or a claim that no effects occurred after an intent.

**After any irreversible intent/attempt:** every restart is permanently observe-only, including a crash between Save All and destination confirmation. No new confirmation, Save All, navigation, fallback or replacement run may be posted. Unknown durable history also forces observe-only. Read-only filesystem/forensic reconciliation may continue but never rearms an operation. Existing Rev27 historical budget remains consumed for its path; the reviewed Rev28 supersession is a separate, explicitly bound one-shot path, not a reinterpretation.

Owner must enforce state and eligibility at reservation: Save All only at freshly proved SAVE_ALL_LOCATED + PHASE_B_ELIGIBLE; confirmation only after in-window actual chooser + approved tripwire + exact destination prepared. Generic append/adapters cannot forge semantic authority. Critical records bind goal/run/plan/implementation/rule hashes and raw evidence, not an arbitrary 64-character string.

### C5 — Guarded actuation

A single-use readiness permit is minted by common validated logic from a current session observation, expires within the current one-second maximum, and binds the exact candidate/action/process/window/geometry. Production callers cannot fabricate successful readiness observations or bypass the frozen capture rule. Retain injection at OS boundaries for tests.

Before Save All: verify active/frontmost target, current process instance and signature, window geometry, topmost addressed surface at the screen point, permissions and exact safe candidate. Post mouseMoved, then revalidate these facts and candidate **before mouseDown**. Focus theft/occlusion/geometry change must yield zero down/up if down has not been posted. Once down is posted, only the paired up needed to release that same click may follow; no second click/retry. Record event ordering and direct result uncertainty.

Persist irreversible intent and attempt before effectful dispatch, with errors fail-closed. At most one click consists of one down/up pair (mouse move is not a second click); owner currently counts intent+attempt as 2 records, which is not a dispatch count of 2. Evidence must distinguish reservation, attempted dispatch, emitted events and observed effect.

### C6 — Actual chooser and destination

Use StrictPostconditionMonitor and hash-verified frozen/derived production predicate. Preserve 150 ms cadence during first 8 seconds, 500 ms thereafter and **15-second hard success cap**. Bind the timer to the actual Save All dispatch boundary, not a later adapter invocation. Native sampling is input-free, has real deadlines, preserves failures/cancellation and consumes cumulative tripwire observations. Delayed sampler completion cannot promote a terminal result.

The one late forensic sample follows the frozen delay, bounded separately (current slow cadence implies at most 2 seconds for that sample); no late affirmative authorizes input. Observer failure, tripwire abort, no in-window chooser or deadline -> zero further GUI input, durable named terminal, no blind retry.

Chooser affirmation requires actual new surface relative to pre-dispatch inventory, SCK+CG presence, calibrated AX roles/path/default/cancel, unambiguous hosting process with PID/start/bundle/signature continuity, and completion inside the cap. Bind raw census and AX evidence, not just `predicateID`. Derive runtime v2 from exact frozen predicate/calibration bytes; do not edit old frozen artifacts. An unreadable signature cannot fall back to this driver's identity. Empty/unknown pre-census widens refusal; no synthetic “pre” census created after dispatch. Unsupported LINE hosting shape -> `INDETERMINATE_CHOOSER_REFUSED(frozen_predicate_mismatch)`.

Destination must exactly equal the authorization's canonical staging run path. Reject symlink components, traversal, overlap with baseline, nonempty/reused staging, and evidence inside staging. For every AX/key primitive reacquire chooser/Go-to-folder identity, focused field ownership, process continuity and active/topmost surface. The target path field, resulting path and default button must all belong to the same unique verified panel. Never search all app windows and choose the first matching button/path.

Go-to-folder Return is allowed only while a freshly proved navigation sheet owns the verified field and the action has navigation semantics. Otherwise refuse before posting. Verify exact field value and reflected destination after navigation. A stale field, wrong path, duplicate panel/button or focus theft cannot fall through to confirmation.

After destination proof, reserve durable confirmation intent/attempt, freshly revalidate again, and perform exactly one AXPress on the bound default button. No Return fallback or second AXPress on non-effect. Directly observe chooser close/download start; the observation is not filesystem success.

### C7 — Filesystem authority and finalization

Collect real read-only FSEvents plus directory/baseline snapshots with cumulative journal, timestamps, watcher start/gap/error evidence and explicit attribution facts. Observe ≥10 seconds of pre-dispatch environmental context at SAVE_ALL_LOCATED. Dropped events/collector failure cannot become an empty clean tripwire. Maintain monitoring across dispatch, chooser, navigation, confirmation and completion.

Retain frozen ladder: L1 unique staging writes are evidence; L2 approved root attributable unexpected writes are disclosed nonfatal observations, unattributable writes abort; L3 ~/Downloads outside root attributable-to-run writes abort, unattributable activity is disclosed environmental context. Baseline modification always aborts. Pre-dispatch environmental activity alone does not abort. The stricter existing pre-chooser attributable-write refusal blocks confirmation without changing the ladder's category. Declare engine's own evidence/control writes in advance; path/timing alone cannot fabricate process attribution.

Baseline verifier runs at Phase A, immediately before Save All, through tripwire checks and at closeout. Compare reference SHA, all names/bytes/hashes/mtimes and both digests. Baseline failure -> no Phase B, or immediate zero-input abort if already in B.

Staging snapshot must read a stable regular file without following symlinks and bind metadata, hash and decode to the **same bytes** (pre/post file identity/metadata consistency). Detect replacement/rename, hidden extras, nested dirs, partials and errors. Poll at one-second intervals for download observation; plan maximum automatic download observation is **10 minutes from confirmation**, then preserve `STAGING_INCOMPLETE` or `STAGING_UNSTABLE` and stop automatic work. No additional download is authorized by timeout. A later separately recorded read-only recomputation may establish disk facts without rewriting the original terminal record.

Stability requires a contiguous run of ≥3 equal snapshots spanning ≥4 seconds, and ≥5 seconds without a directory/file change; elapsed time from an earlier different sample cannot satisfy it. Use monotonic observation durations, retain wall time/mtime evidence, reject reordered times and file replacement. Hash/decode must still agree at the final snapshot. Production must use `verifyStableSnapshots`, not a single-snapshot success shortcut.

After valid filesystem proof and baseline unchanged, append content evidence, Save All empirical-class record (derived from actual postcondition/tripwire), manifest and FINALIZED ledger transition. “Registry/evidence consistency” means this ledger + manifest + run evidence, not a new independent database. Finalization is not overall task closure: Stage 05 remains mandatory. Evidence stays outside staging, append-only with relative paths/full hashes, executable/plan/source/rules/clock provenance. Errors and indeterminate results receive equally durable records.

## SUPPORTING WORK / CHANGE MAP / NON-GOALS

Future Stage 04 may change `rev28/Sources/Rev28Core/**`, necessary production composition in `rev28/Sources/rev28ctl/**`, relevant `rev28/Tests/**`, `rev28/Tools/**`, and architecture/capability docs; append task/evidence artifacts. Small module additions within those directories are allowed for the explicit native/session/gate contracts. Reuse existing components. Preserve cadence-critical HarnessCalibration bytes and frozen history; a needed freeze change is replan, not an incidental refactor.

No GitHub Actions change is currently necessary to fix the first blocker. Existing CI already exposes it. Any later CI wiring change needs an evidenced need within the reviewed test contract, not model-loop/self-approval machinery. No dependency update, broad repository cleanup, new product feature, baseline migration, second accepted copy or packaging exercise. Diagnostics/registration/Foundation Models remain BEST_EFFORT, non-authoritative and non-gating; do not block the core route to implement optional features.

## FIRST_ACTION / FIRST_IMPLEMENTATION_BLOCKER_FINGERPRINT

After Stage 02 PASS and Stage 03 handoff, first reverify exact branch/remote/review/plan hashes and worktree preservation. Then repair the two tests' helper usage with the smallest change and run the focused compile/test diagnostic. The predeclared distinguishing result is test execution versus the same compile failure; once compilation succeeds, classify the already known segmentation failure independently. Do not collapse a later runtime assertion into the old compile blocker or declare product completion.

```text
STAGE=04
CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION
SURFACE=rev28/Tests/Rev28CoreTests/StructuralLocatorsTests.swift
EXPECTED=Swift test target compiles and StructuralLocatorsTests executes
OBSERVED=Swift test target compilation fails before test execution
```

Fingerprint is failed acceptance identity. Changing helper hypothesis, model, session or wording while expected/observed stay the same is the same blocker.

## TEST_STRATEGY

Tests below are explicitly required for the future implementation. This planner ran only bounded diagnostics already recorded.

1. `xcrun swift build --package-path rev28`; `xcrun swift test --package-path rev28 --filter StructuralLocatorsTests`; then focused StagingVerifierTests. Preserve current positive/negative assertions and add minimal regression cases for short end date/cross-card and old different sample + short equal suffix.
2. Run deterministic Swift tests as the current macOS27 workflow specifies (Vision tests separately), then the full suite on this real Mac in executable context. Report hosted Vision limitations separately; no blanket “all green” from a skipped class. No production input in CI.
3. Existing 25-case adversarial suite and full 20-fixture replay, twice each, semantic results equal. Verify full fixture hashes against archived R3 anchors/current pinned manifest; never derive new expected hashes from mutated fixtures. Replay must include actual segmentation, not only pre-supplied card regions. Negative mutations must preserve identity/geometry refusal.
4. Common composition matrix, with real state/gates/owner and low-level injected OS interfaces: full success using temporary real image files; every pre-Save-All state failure; stale/mixed epoch/hash/process/window/scale/config; occlusion after move; single-use/expired permits; missing observation; sampler stall/error/late result; empty/wrong census; same-process look-alike; two panels/default buttons; wrong destination/focus loss at each primitive; pre-chooser writes; all tripwire levels; baseline change; unstable/partial/extra/duplicate/undecodable content; evidence swap/tamper; out-of-order state; unbound SHA-only success.
5. Authority/restart matrix: second owner and new-runID attempts; ledger truncation including empty, deletion, valid-prefix rollback, stale/missing anchor, fsync/anchor error; one-shot preflight remains unconsumed; verified pre-intent continuation preserves counters and reobserves; crash after intent/before down/after click/in chooser/after confirmation/mid-download always resumes observe-only. Counts are checked both from ledger and independent counting sink, never inferred from one alone.
6. Real synthetic AppKit calibration of the **same native composer**, actual NSOpenPanel, SCK, Vision, AX, separate-process occluder and real input sink. Reconfirm frozen rule applicability, ≥20 panel timings with strict monitor, destination preparation/AXPress and crash/refusal behavior. Historical HarnessCalibration provenance PASS is retained but cannot substitute for this current-composer evidence. Never test synthetic dispatch against LINE.
7. `python3 -B rev28/Tools/verify_pre_live_provenance.py` retains exact v3 historical binding. New composed evidence is append-only and separately bound; do not overwrite freeze/proof files or silently change frozen bounds.
8. Stage 05 independently opens actual baseline/staging/ledger/evidence and recomputes; no adapter-created expected verdict is an oracle.

## MECHANICAL_ACCEPTANCE / REGRESSION_AND_ACCEPTANCE / GATE POLICY

For every check record CHECK_RESULT = PASS / FAIL / BLOCKED / NOT_RUN, command/scenario, exact inputs/source/binary hashes, actual outputs, evidence SHA, and status scope. All checks have BASELINE_RULE=none, BASELINE_REQUIRED=NO, WAIVER_ALLOWED=NO, WAIVER_AUTHORITY=NONE, WAIVER_STATUS=NOT_ALLOWED. Baseline comparison below is an outcome predicate, not a BASELINE_DELTA waiver. NON_GATING describes closure classification; an explicit pre-B interlock remains mandatory.

| ID | Observable check | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | When / FAILURE_ROUTING |
|---|---|---|---|---|---|
| V-01 | Actual binary SCK/Vision/AX/Quartz capability | CORE | DIAGNOSTIC | NON_GATING | Before A/B; failure or unknown blocks that phase, no permission assumption |
| V-02 | Frozen geometry/chooser/monitor calibration applies to current native composer | CORE | DIAGNOSTIC | NON_GATING | Before B; mechanical repair or semantic replan |
| V-03 | Every live frame/permit obeys identity/geometry/freshness | CORE | MUST_NOT_BREAK | HARD_CLEAN | A/B; invalidate candidate; abort at budget/irreversible boundary |
| V-04 | Actual chooser affirmed inside 15 seconds by strict predicate | CORE | OUTCOME | HARD_CLEAN | After Save All; no/late/error -> scoped terminal, zero further input |
| V-05 | Bound chooser/path plus exactly one confirmation, no unknown retry | CORE | OUTCOME | HARD_CLEAN | B; refusal -> indeterminate/abort; preserve spent budgets |
| V-06 | 57 stable decodable regular files / exact bytes / multiset | CORE | OUTCOME | HARD_CLEAN | After confirmation; named staging/content failure, no re-download |
| V-07 | Reference + baseline both hashes + per-file mtimes unchanged | CORE | MUST_NOT_BREAK | HARD_CLEAN | Before B and throughout/after B; unavailable blocks; delta aborts |
| V-08 | Replay/adversarial twice, pinned fixtures and refusal parity | SUPPORTING | DIAGNOSTIC | NON_GATING | Mandatory before B; repair or replan, never skip |
| V-09 | Seven topic reviews + adversarial + barrier supersession approve exact current bindings | CORE | DIAGNOSTIC | HARD_CLEAN | Code/rules review before A; LINE-specific supplement after A, all before B; issues -> fresh review |
| V-10 | Independent Stage 05 filesystem and transaction recomputation | CORE | OUTCOME | HARD_CLEAN | Closure only; mismatch fails acceptance/replan, preserve known facts |
| V-11 | Do-not-touch / unrelated work / no commit-push outside authorization | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | Start/closeout; violation stops closeout claims and is reported |
| V-12 | Build and required deterministic/native Swift tests actually execute and pass | SUPPORTING | DIAGNOSTIC | HARD_CLEAN | Before B; current compile regression requires repair |
| V-13 | Same composed engine/authority/gates in real and injected paths, full failure matrix | CORE | MUST_NOT_BREAK | HARD_CLEAN | Before B; divergence/forged success requires repair/replan |
| V-14 | Phase A complete real-Mac evidence + zero irreversible intent/dispatch | CORE | MUST_NOT_BREAK | HARD_CLEAN | Before B; insufficient observation fails closed |
| V-15 | Owner/goal slot/anchor/intent ordering/restart and no reset bypass | CORE | MUST_NOT_BREAK | HARD_CLEAN | Before and throughout B; uncertainty observe-only |
| V-16 | Append-only finalized manifest/empirical record/ledger bind raw evidence | CORE | OUTCOME | HARD_CLEAN | Post-run/closure; missing evidence stays incomplete, no success inflation |

V-09 topics: sensor/perception; coordinate transforms; Quartz; postcondition; risk classes; chooser automation; transaction/recovery; adversarial results; Rev27 barrier supersession. Use fresh independent reviewer contexts on exact inputs. Stage 02 R4 approval is separate from V-09 implementation approval. Final handoff is Stage 03's responsibility, not the planner's self approval.

## PHASE_A — OBSERVATION / PREFLIGHT

Purpose: obtain real-Mac/real-LINE evidence while Save All count=0 and destination confirmation count=0. No irreversible intent/token consumption. Stage 04, after the approved handoff and pre-A safety checks, may launch/activate and navigate with guarded reversible actions to the exact album; optionally open/dismiss ellipsis without selecting any row. All such actions consume the same persistent reversible budget, with fresh before/after evidence. No production menu row activation for “testing.”

Record real process/signature/start, executable-context TCC, SCK/CG/AX inventories, display/scale, frozen capture geometry, same-frame Vision, exact group/date/count association, actual card segmentation, ellipsis and five-row Save All localization, popup surface/occlusion assumptions, pre-panel process census, baseline integrity, empty unique staging/evidence separation and native tripwire readiness. Reverify album identity after navigation. If the current layout cannot support an invariant, return a typed refusal and route repair/replan; never synthesize the missing evidence.

Publish `phase-a.json` plus raw evidence manifest with per-condition PASS/FAIL/UNKNOWN and zero irreversible counters from owner ledger. Native chooser assumptions must be marked **calibrated on real NSOpenPanel, actual LINE chooser not yet observed**. An unsupported assumption blocks B; the expressly deferred actual chooser observation is a B runtime gate, not a fictitious pre-B PASS. Complete V-09 LINE-specific supplements against these findings.

## PHASE_B_ELIGIBILITY — MACHINE-CHECKABLE, ALL PASS

Eligibility is a typed common evaluator result, persisted and rechecked at reservation; a boolean supplied by an adapter or CLI flag is insufficient. Required conjunction:

- Approved R4 exact SHA, Stage 03 contract consistent, exact reviewed implementation source manifest + HEAD/diff state + binary hash + rule/predicate/fixture/provenance hashes, and all required independent review bindings current. Include Package.swift, production Swift, invoked tools and relevant build configuration; the current source-only Swift digest alone is insufficient.
- V-01/02/08/09/12/13/14/15 prerequisites PASS, no pending review issue, no stale remote/source drift, and explicit one-shot Phase B authorization for this goal. This Stage 01 request itself authorizes no production operation.
- Fresh Phase A chain and immediate pre-dispatch re-observation on actual LINE match exact group/date/count/menu/process/window/geometry. Permits meet current deadline. Re-observation cannot silently reuse old pixels/candidates.
- Goal slot/ledger/anchor valid, exclusive owner, no previous irreversible intent or attempt, no terminal/unknown history, reversible/revalidation budgets not exhausted, exact authorized operation/action/destination.
- Baseline reference/count/bytes/digests/mtimes match; new canonical staging empty and disjoint from baseline/evidence, symlink-free. Native tripwire active with ≥10-second pre-dispatch context and no collection gaps/unresolved gate failure.
- Pre-dispatch chooser/process inventories saved; strict observer armed with the reviewed clock/deadline; all post-dispatch refusal branches demonstrated. Actual chooser and final files are deferred runtime gates, not pre-B facts.

Any FAIL, UNKNOWN, NOT_RUN, missing/stale hash or unbound evidence => PHASE_B_INELIGIBLE, zero irreversible dispatch. Human authorization cannot turn a failed predicate into PASS.

## PHASE_B — IRREVERSIBLE EXECUTION

One eligible durable Save All reservation/attempt -> one guarded Quartz click -> strict actual chooser observation. On successful in-window affirmative plus tripwire gate, prepare exact destination reversibly, then one durable confirmation reservation/attempt -> one bound AXPress. Observe download without further input, verify stability/content/baseline, finalize evidence. There is no retry branch for unknown effects. Stop consuming GUI input on any post-intent refusal, timeout or uncertainty. Only read-only forensic/verification work remains possible.

## FAIL_CLOSED / MUST_NOT_BREAK

- Historical Rev27 effect classification and old coordinates never change authority.
- Baseline, old staging, evidence/reviews/frozen rules and unrelated work remain byte-identical; baseline mtimes unchanged. Never copy baseline files into staging to pass acceptance.
- No new runID/token/ledger/session/model can recreate spent budgets. Intent with no visible effect is consumed; no blind retry or fallback confirmation.
- Identity mismatch, mixed observations, invalid geometry, unknown scale/ownership, unverified signing, stale AX, ambiguous card/menu/button/path, unbound SHA, missing watcher or unreadable evidence never become success.
- Never weaken acceptance constants, geometry tolerance, chooser predicate, attribution semantics, timer bounds or test expected refusals to make the run pass.
- Runtime success facts do not erase pending independent acceptance; test failure does not erase product build PASS or other already-proven facts.

## REVERIFY_ON_START

Fetch origin --prune; record local/remote HEAD and branch; inspect dirty/untracked state before mutation. Remote is authority. Fast-forward only when clean and possible; never reset/clean/stash/rebase/restore/force-push. Check new commits against root cause, assumptions, critical path and acceptance. Confirm R4 reviewed snapshot/hash and Stage 03 binding; no stale handoff use.

Recompute baseline reference and both manifests/mtimes, inspect old staging and all task-owned goal/ledger/anchor histories. Unknown old transaction state blocks execution; missing V4.3 telemetry does not prove unused budgets. Verify exact binary/source/rules/frozen sampler/fixtures and current CI step results. Recheck TCC/LINE/session/display/SDK facts in the native context. Preserve unrelated dirt and record it separately.

## CONVERGENCE_CONTRACT / STOP_CONDITIONS / REPLAN_CONDITIONS / ESCALATION_CONDITIONS

STOP: any failed eligibility; preservation violation; missing required authority/data; duplicate owner; spent/uncertain irreversible budget; runtime identity/geometry/chooser/tripwire error; deadline; baseline change; exhausted reversible/revalidation limits. Preserve evidence and return a scoped non-success state. Do not force completion of the two action counts.

REPLAN: source/remote drift invalidates a load-bearing premise; architecture/session/owner boundary change; different chooser shape or capture rule; changed identity aliases, validity/requiredness/gate policy; new fallback semantics; migration or security boundary change; acceptance/time-bound changes; attribution cannot support reviewed semantics. Stage 04 may resolve mechanical details only, not make these decisions silently.

ESCALATION: apply V4.3 guard before each material debugging attempt, not after code churn. Limits:

- MAX_MATERIAL_ATTEMPTS_PER_BLOCKER = **3**.
- MAX_CONSECUTIVE_NO_INFORMATION_GAIN = **2**.
- A -> B -> A oscillation = immediate escalation.
- Model/session/hypothesis-wording changes never reset counts. Budget is a ceiling, not a quota.
- Before attempting, record a new falsifiable hypothesis, new information source and distinguishing result. Without one, stop substantive local implementation and escalate now.

Maintain progress.md after each material result: objective now, blocker fingerprint, attempts used, last evidence/information gain, whether closer, next distinguishing step and what happens if it fails. Also record hypothesis IDs, files/commands/evidence, attempted direction, no-information count and cumulative budget across handoffs. Planning diagnostics are recorded here as diagnostics, not secretly labeled implementation fixes; reconcile earlier execution history before seeding Stage 04 counters. Absence of old counters is not a reset instruction.

At guard trigger write next append-only `escalations/attempt-N/` packet with minimal reproducer, failed condition, hypotheses/evidence/deltas, counters and semantic question; set IMPLEMENTATION_STATUS=ESCALATED and TASK_CLOSURE_STATUS=HIGH_REASONING_REVIEW_REQUIRED. If a plan premise is disproved, route REPLAN_REQUIRED instead. In a compatible persistent Goal runtime load convergence-escalation.md; use blocked only when the three-consecutive-turn blocked audit is eligible, never self-pause. Stage 06 is this escalation route, not a mandatory extra stage.

## EXPECTED_ARTIFACTS AND STATUS CONTRACT

This Stage 01: revised plan.md; byte-identical R3 archive; decision.md; source-analysis.md; bounded diagnostic logs/results; preservation/freshness/hash manifests. No new handoff.md, execution update, result.md, product/test/workflow edit, commit or push.

Stage 02: next unused `review/attempt-N/` with exact R4 snapshot, SHA, independent findings and verdict. Stage 03 after PASS: archived old handoff plus new compiled execution contract and hashes. Stage 04: progress.md, append-only execution evidence, escalations when triggered; native composition/calibration/test reports; V-09 reviews; phase-a.json and raw evidence; eligibility.json; owner ledger/checkpoints; dispatch/postcondition/chooser/tripwire evidence; stable snapshots/manifest/baseline-before-after; empirical class; finalization. Stage 05: next `e2e/attempt-N/` with independent recomputation scripts/commands, raw result and acceptance report. result.md only at actual task closure.

Stage 05 must independently decode/hash all staging files, check exact count/bytes/multiset and stable/quiescent snapshots, reread baseline names/hashes/mtimes, verify raw evidence hashes/chain/anchors, count intents/attempts/emitted actions, and bind the real LINE observation to the downloaded run. It must not use Stage 04 verdict strings as proof. Prefer a read-only independently implemented verifier over simply calling the engine's same verifier twice.

Current assessment, not task closure:

```text
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: FAIL
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: REPLAN_REQUIRED
```

Required verification FAIL is the observed test compile regression. Native implementation is unfinished; primary live acceptance was not performed this turn. Keep these independent subjects in all later artifacts. Overall DONE is permissible only after actual primary outcome, all HARD_CLEAN gates and independent acceptance pass. Otherwise use canonical scoped FIX_REQUIRED / REPLAN_REQUIRED / HIGH_REASONING_REVIEW_REQUIRED / pending or blocked routing without erasing already-proven facts.

## FINAL FRESHNESS

After writing planning artifacts, fetch origin --prune again and compare remote branch HEAD with ANALYSIS_BOUND_HEAD. Record commands/time/SHAs and protected-file audit in `analysis/r4-20260928/final-audit.json`. A changed remote requires analysis of each new commit's root-cause/blocker/assumption/path/acceptance impact before the plan can be READY_FOR_PLAN_REVIEW. Without that reassessment, route STALE_REMOTE_HEAD. R4 remains unapproved even when fresh.
