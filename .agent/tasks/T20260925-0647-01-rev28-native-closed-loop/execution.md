# execution.md — Stage 04 Implementer outcome record

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
PLAN_PATH: .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md
PLAN_REVISION: 3
PLAN_SHA256: 63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828
HANDOFF_PATH: .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/handoff.md
HANDOFF_SHA256: d1a86814b2a2cc40431a31cadd08eb7d80e87a3969a6ace2d20b1ee3a7a35ed6
HANDOFF_STATUS_AT_START: READY_FOR_IMPLEMENTATION
REVIEW: attempt-05 + attempt-06 both PLAN_APPROVED on PLAN_REVISION 3 (verified via handoff; not re-read)
Freshness check at start: PASS (both digests recomputed on disk before any product edit).

## Update 1 — session start + W1 (CORE, no GUI) complete

session_started: 2026-09-25T07:33+08:00
session_started_branch: master
session_started_HEAD: 766b22c4f8bf29b9d0a46049c75309c70593d66d (= origin/master, ahead 0)
working_tree_at_start: untracked-only (Rev27e WIP + prior evidence dirs incl. three __pycache__ dirs; no tracked modifications; preserved untouched)

REVERIFY_ON_START probes (all run before any product edit):
- HEAD/branch: PASS (766b22c4… / master; origin identical)
- plan.md SHA-256 == 63b25602…: PASS (recomputed on disk)
- handoff.md SHA-256 == d1a86814…: PASS (recomputed on disk)
- staging /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260923-111908-01: PASS (0 entries, 0 bytes)
- LINE installed 26.0.2 / not running: PASS (Info.plist 26.0.2; pgrep found no process)
- accepted baseline resolves: PASS (57 files, 0 subdirs, 17,924,900 bytes)
- baseline manifest digest (trailing-newline method) == b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd: PASS (negative control without trailing newline = 287d95c2… differs)
- baseline content multiset (no trailing newline) == ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf: PASS (negative control with trailing newline = af389c83… differs; 57 unique hashes)
- baseline-content-multiset.json SHA-256 == 3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2: PASS
- SDK: xcrun --sdk macosx --show-sdk-path = /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk (expected Xcode MacOSX26.5.sdk): PASS; swift 6.3.3; macOS 27.0 (26A428)

W1 deliverables (new SwiftPM package rev28/):
- rev28/Package.swift — library Rev28Core + executable rev28probe + Tests/Rev28CoreTests; platform macOS 26.0; Swift language mode 5
- rev28/Sources/Rev28Core/Geometry/Coordinates.swift — 3 distinct coordinate spaces (window-local pt / screen-global pt / capture px), canonical transform carrying W/B/S, validated-tolerance per-state capture rule (no tolerance without a recorded rule; fail closed), independent scale check, 1-pt safe-interior refusal rule
- rev28/Sources/Rev28Core/Identity/WindowIdentity.swift — identity binding {bundle, pid+start time, windowID, frame, AX read, CG entry, epoch, capture SHA} + fresh-enumeration validation (stale ID / pid reuse / bundle / layer / offscreen / frame tolerance / stale epoch)
- rev28/Sources/Rev28Core/Sensor/WindowSensor.swift — SCShareableContent enumeration snapshots, candidate selection by bundle+pid+layer, child-window discovery
- rev28/Sources/Rev28Core/Sensor/FrameCapture.swift — explicit CaptureConfiguration (kind/includeChildWindows/ignoreShadows/ignoreClipping/showsCursor/sourceRect), CapturedFrameRecord with all plan-required fields, FrameCaptureService (epoch counter, union bbox, PNG SHA-256, INVALID record on invariant failure)
- rev28/Sources/Rev28Core/Perception/OcrEngine.swift — Vision RecognizeTextRequest wrapper (accurate, zh-Hant+en-US, no language correction), capture-px quads, exact-identity comparison (no normalization/merge)
- rev28/Sources/rev28probe/ — capability probe CLI (atomic temp+rename record write, append-only timestamped filename)
- rev28/Tests/Rev28CoreTests/ — CoordinateTransformTests (12), WindowIdentityTests (12), OcrEngineTests (4)

Commands actually run and observed results:
- DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift build --package-path rev28 → "Build complete!"
- DEVELOPER_DIR=… xcrun swift test --package-path rev28 → exit 0; "Executed 28 tests, with 0 failures"; two first-run mechanical test failures (wrong expected union maxX; single-glyph 楨 below Vision text-detection granularity) were repaired in the test fixture (album-title context fixture 旻謙允禎成長日記 vs 旻謙允楨成長日記) and the suite then passed; the diagnostic finding (single rare glyph 楨 not recognized; in-context it is) is a fixture-level observation, not a product semantic change.
- V-01: REV28_SDK_PATH=MacOSX26.5.sdk rev28/.build/debug/rev28probe evidence/…/capability-probe-exec → exit 0, overallStatus=PASS
  - trust in the executable context: AXIsProcessTrusted=true, CGPreflightScreenCaptureAccess=true, CGPreflightPostEventAccess=true
  - SCK: status OK, windows=7, displays=1, applications=3
  - Vision: status OK, exact strings found: ["儲存全部", "57張照片"]
  - Quartz: mouse/keyboard CGEvent construction OK (no events posted); CGWindowList on-screen count 7
  - record: evidence/20260925-rev28-native-closed-loop/capability-probe-exec/probe-record-20260925T074610+0800.json (SHA-256 499748933e2e089e05275c92147894a95705ab4c8cd8beb50af73ed9918d4b13)
  - build/evidence logs: capability-probe-exec/build-log.txt (SHA-256 3a74417139bb2c09e571fae5b15d77dd811a1578e12802051365e6f06ff7e782), probe-stdout.txt (5d37afeb895c3afe3dda8aed12f4f254dcf00a5e341679d2f38a5c756aadd796), sha256sums-v2.txt (authoritative; supersedes the v1 self-line)
- .gitignore: exactly one line added under Modified: `rev28/.build/`

Verification matrix (v4.2 §7.3) at this update:
| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_REQUIRED | WAIVER_ALLOWED | WAIVER_STATUS | CHECK_RESULT |
|---|---|---|---|---|---|---|---|
| V-01 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | PASS (this session, executable context; LINE untouched) |
| V-02 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | NOT_RUN (W2 in progress) |
| V-03…V-07, V-10 | CORE | OUTCOME / MUST_NOT_BREAK | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (pre-live / live-time) |
| V-08 | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | NOT_RUN (W3/W5) |
| V-09 | CORE | DIAGNOSTIC | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (pre-live reviews) |
| V-11 | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | NO | NO | NOT_ALLOWED | PASS so far (no pycache/push; do-not-touch preserved; re-audited at closeout) |

Orthogonal status at this update:
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS
NEXT_ACTION: W2 — build rev28harness + rev28occluder + rev28ctl driver; prove capture per-state matrix and freeze the rule/tolerance; then transforms, Vision localization, Quartz routing, panel-latency/bounds freeze, chooser predicate freeze, focus theft, tripwire attribution, restart fixture.

Residual risk: W2 harness is the largest remaining pre-live uncertainty (per-state capture rule, panel hosting shape on macOS 27, chooser predicate calibration). No LINE interaction has occurred in this session (GUI input: 0).

## Update 2 — W2 harness (CORE, own-window GUI only) CONVERGENT PARTIAL + owner STOP-AND-CONVERGE close

session_resumed_at: 2026-09-25T08:05+08:00
session_start_branch: master
session_start_HEAD: ff04f2da9e1afea9b2ca73a64fe9323a4e495803 (= W1 commit ff04f2d; no origin comparison performed this session — no push/fetch)
working_tree_at_resume: modified rev28/Package.swift, rev28/Sources/Rev28Core/Sensor/WindowSensor.swift; untracked rev28/Sources/Rev28Core/{Actuation,Chooser,Diagnostics,Postcondition,Transaction}/, rev28/Sources/{rev28ctl,rev28harness,rev28occluder}/ (all from the interrupted W2 session); pre-existing Rev27e untracked WIP + __pycache__ dirs preserved untouched.
Note: Update 1 said "Executed 28 tests"; the W1-committed test sources declare 28 `func test` methods but only 27 were collected, because `testDiscriminatesZhenGlyphsInAlbumTitleContext` was accidentally nested inside `testQuadIsInCapturePixelSpace` (never collected). Repaired this session (sibling methods) → the suite now genuinely runs 28/28. The W1 product code is unchanged by this repair.

W2 files on disk (all compile; no new features added after the STOP-AND-CONVERGE order):
- rev28/Package.swift — executable targets rev28harness, rev28occluder, rev28ctl (Rev28Core dependency)
- Rev28Core/Actuation/{AXDriver,QuartzActuator}.swift (AX reads/tree dump/press; Quartz click/keys/unicode; postKeyChord, postReturnKey, postGoToFolderChord)
- Rev28Core/Chooser/{ChooserAffirmationPredicate,FolderChooserDriver}.swift (clause sets incl. empty-pre-census refusal widening, pid-reuse, not-new-window; real-panel navigation + AXPress confirmation; destination reflection)
- Rev28Core/Postcondition/PostconditionMonitor.swift (plan-time 150 ms fast / 8 s window; 500 ms cadence to 15 s hard cap; 30 s late forensic sample; §10 outcome routing incl. chooserObservedAfterWindow vs noChooserObserved)
- Rev28Core/Transaction/{IntentLedger,TripwireAttribution}.swift (hash-chained append-only ledger + observe-only resume; L1/L2/L3 ladder: L1 stagingExpectedEvidence, L2 attributable attributedExternalWriteObserved (non-abort), L2 unattributable abortedUnattributedFilesystemWrite (fail-closed), L3 attributable abortedWriteOutsideApprovedRoot, L3 unattributable environmentalContext (non-aborting), baseline-modified abortedBaselineModified, pre-dispatch preDispatchContext)
- Rev28Core/Diagnostics/DiagnosticHooks.swift (EvidenceIO atomic temp+rename + SHA-256; LineReader; LineProtocol)
- Rev28Core/Sensor/WindowSensor.swift (added CGWindowSnapshot + CGWindowInventory.onScreenWindows)
- Sources/rev28harness/ (AppKit harness: 800x600 main window, red origin marker at content (4,4), title 旻謙允禎成長日記, 57張照片, 5-row menu at local (40,200) r=40 w=320 with row 2 = 儲存全部, floating borderless popup child window, real NSOpenPanel directory sheet, same-process look-alike, focus theft, moveBy/setFrame/setShadows/showPopup/hidePopup, writeFiles normal/zeroByte/partialSuffix/slowGrowth, hitReport)
- Sources/rev28occluder/ (separate-process cover + look-alike windows, hit counters, writeFile, state, hitReport, cover/hide/activate/lookalike/hideLookalike/quit)
- Sources/rev28ctl/ (ProcessPeer JSON-lines stdio peer; EvidenceRun run dirs + canonical frozen dir; RawCapture + PixelProbe; ProcessIdentity (bundleID + signing identity); RestartFixture SIGKILL at 4 points; HarnessCalibration driver with items 1-9 and --max-cells partial guard)

Commands actually run and observed results (this session):
- export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer; xcrun --sdk macosx --show-sdk-path → /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk (expected); swift 6.3.3
- xcrun swift build --package-path rev28 → "Build complete!" (0 errors; one pre-existing warning: unused `try?` result at rev28/Sources/rev28harness/HarnessApp.swift:531)
- xcrun swift test --package-path rev28 → exit 0; "Executed 28 tests, with 0 failures (0 unexpected)"
- ./rev28/.build/debug/rev28ctl harness-calibrate --evidence evidence/20260925-rev28-native-closed-loop/harness --items 8 → exit 0, item 8 PASS, canonical frozen tripwire ladder
- … --items 1 --max-cells 1 → exit 1 (PARTIAL as designed), 1/16 cell; noRuleFailClosed=true; occlusionCapture=true; canonical rule book correctly NOT published
- … --items 2 → exit 1 (PARTIAL); OCR/Vision localization proven (menuRowMatches=1, countMatch=true, titleMatch=true, 楨 discrimination true, ambiguity refusal true); row-box/safe-interior rows empty because item 1 never froze a rule book
- … --items 3,4 → item 3 NOT_RUN (needs frozen rule book); then driverError (occluder unknownCommand:hitReport) which is fixed
- … --items 6 → item 6 chooser-ax-calibration PASS (panel AXWindow/AXStandardWindow, 145 nodes, buttons include 開啟); predicate proof PARTIAL (realPanel=refused: notNewWindow; fake same-process refused; empty-census refused; occluder look-alike refused; AXPress of 開啟 succeeded: pressedButtonDescription=role=AXButton title=開啟; marker file written; navigationReflected=false)
- … --items 4 → PARTIAL: popupHits=0 at the popup point, coverHits=1 at the same point → with the peer occluder active/raised the harness popup was NOT topmost (routing not proven); main-window clicks do deliver (mainHits=1)
- … --items 9 → exit 0, item 9 PASS (points=4 sigkill=4 chainVerified=4 observeOnly=4 zeroNewIrreversible=true controlAllowed=1), canonical frozen restart fixture
- pgrep -fl 'rev28harness|rev28occluder|rev28ctl' after the runs → none (peers stopped); LINE never launched/poked: GUI input to LINE = 0

Defects found and fixed this session (mechanical only; no semantic/priority/fallback change):
1. Rev28Core/Diagnostics/DiagnosticHooks.swift — LineReader was created inline and not retained while its readability handler held it weakly, so all three JSON-lines peers silently received nothing (root cause of every "timeout waiting for reply", incl. the pre-abort HARNESS-20260925-080909 smoke run). Fixed with a deliberate strong self-capture whose cycle is broken on EOF.
2. rev28ctl/EvidenceRun.swift — writeFrozen did not create the canonical frozen/ parent directory (missingParent driverError after a PASS item 8 record).
3. rev28ctl/HarnessCalibration.swift item 1 — a --max-cells partial matrix could publish a canonical frozen rule book; now only a complete 16-cell matrix freezes, otherwise a NOT_FROZEN note is recorded.
4. rev28ctl/HarnessCalibration.swift item 6 — a PARTIAL chooser proof could publish canonical frozen predicate artifacts; now only a PASS proof freezes.
5. rev28occluder/main.swift — added the missing hitReport command (driver already called it; previously unknownCommand).
6. Rev28Core/Chooser/FolderChooserDriver.swift — defaultButtonElement search depth 7 → 12: a native NSOpenPanel presented as a sheet nests its prompt button ~8–10 levels below the host window, so depth 7 silently reported defaultButtonMissing.
7. Tests/Rev28CoreTests/OcrEngineTests.swift — de-nested the 楨 discrimination test (see note above).

Frozen artifacts (canonical evidence/20260925-rev28-native-closed-loop/harness/frozen/, SHA-256):
- tripwire-attribution-ladder-v1.json — d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216 — FROZEN_VALIDATED (item 8 PASS, run HARNESS-20260925-081236)
- restart-observe-only-fixture-v1.json — 146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f — FROZEN_VALIDATED (item 9 PASS, run HARNESS-20260925-081625)
- chooser-affirmation-predicate-v1.json — 20399c4f27b6f9f3828b55a972f686ab6dcf495252d4032977aa83322f334f3b — PROVISIONAL_NOT_VALIDATED (published by run HARNESS-20260925-081519 while the item 6 proof was PARTIAL: realPanel refused with notNewWindow because the harness presents the panel as a sheet)
- chooser-ax-calibration-v1.json — 43e221f1d6803b67c930bab5bce974a60323f29d277a80d2c0bd29283bfa0443 — PROVISIONAL_NOT_VALIDATED (same run/reason)
- PROVISIONAL-NOT-VALIDATED-20260925T0817+0800.json — 11ce3eef52b19d9d3c7421426340d19d9c32dfd38d9118be1770314e1976c3b5 — explicit marker so the two files above cannot be mistaken for validated freezes
NOT_FROZEN (must not be treated as frozen): capture-geometry-rulebook-v1.json, capture-matrix-v1.json (partial matrix), postcondition-bounds-v1.json, postcondition-latency-observations-v1.json (item 5 not run).
Append-only caveat: the two PROVISIONAL chooser files already exist, so a corrected re-freeze cannot reuse those names; the next session needs an explicit naming/republish decision (Plan-level question, not a Stage-04 choice).

W2 item status vs the plan's 9 harness items:
1 capture matrix + rule freeze — PARTIAL (code complete incl. occlusion capture + no-rule fail-closed proof + partial guard; only 1/16 cells executed; NOT_FROZEN)
2 Vision localization — PARTIAL (OCR proofs PASS: 儲存全部 x1 in the 5-row menu, 57張照片, 旻謙允禎/旻謙允楨 discrimination, ambiguity (2 identical rows) refused; row-box/safe-interior repeatability NOT measured this run — the record's 0.0 pt deviation fields are defaults because no boxes were recorded without a frozen rule book)
3 coordinate transforms — NOT_RUN (needs item 1 frozen rule book)
4 Quartz routing — PARTIAL (failure mode identified: popup not topmost over the active peer occluder; not proven)
5 postcondition latency/bounds freeze — NOT_RUN (owner STOP-AND-CONVERGE explicitly deferred the >=20-run freeze)
6 chooser AX observation + predicate freeze — PARTIAL (AX calibration PASS + real panel observed and its 開啟 button AXPressed successfully; predicate proof refused the real panel with notNewWindow; freeze PROVISIONAL)
7 focus theft — NOT_RUN (code guards on the frozen rule book)
8 tripwire attribution — PASS (L1/L2/L3 ladder incl. L3 unattributable = non-aborting environmental context and L2 unattributable = fail-closed)
9 restart/observe-only fixture — PASS (4 SIGKILL points, hash chain verified, zero new irreversible dispatches, freshReviewed control allowed=1)

Evidence (append-only; structured records with SHA-256):
- harness/PARTIAL-status-20260925T0817+0800.json — 49bc7a2cfada259f104e7eb6d4711e32c54a400463b65d2a2920fc6ab090e7fa (full per-item status, run IDs, per-record SHAs)
- harness/build-test-log-20260925T0817+0800.txt — 91ae29a28c6ae65b66e7024478e725790f35ed18e0987ede6ce95a6443f4943e
- runs (00-calibration-summary.json SHA-256): HARNESS-20260925-080909 6e861884…, 081032 438eb263…, 081214 f485dae1…, 081236 e36e7b1b…, 081309 6d73d04b…, 081321 d0ae5cd1…, 081401 5ab83926…, 081431 2be9cf3d…, 081519 7ee7e7d4…, 081620 b5d52632…, 081625 512e6ee6… (full text in the status record)
- item records: 01 a37ae4a6…, 02 (5ab83926 summary; record in status file), 03 b615dc23…, 04 c6af2e49…, 06 calibration 43e221f1… / proof 948b5cb3…, 08 d67abb17…, 09 146b373a…
- pre-W2 (W1, already committed): capability-probe-exec/probe-record-20260925T074610+0800.json 499748933e2e089e05275c92147894a95705ab4c8cd8beb50af73ed9918d4b13

Verification matrix (v4.2 §7.3) at this update:
| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_REQUIRED | WAIVER_ALLOWED | WAIVER_STATUS | CHECK_RESULT |
|---|---|---|---|---|---|---|---|
| V-01 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | PASS (Update 1; unchanged) |
| V-02 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | PARTIAL (items 2/4/6 partial; items 3/5/7 not run; item 1 rule book NOT_FROZEN; item 8/9 PASS) |
| V-03…V-07, V-10 | CORE | OUTCOME / MUST_NOT_BREAK | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (pre-live / live-time) |
| V-08 | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | NOT_RUN (W3/W5) |
| V-09 | CORE | DIAGNOSTIC | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (pre-live reviews) |
| V-11 | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | NO | NO | NOT_ALLOWED | PASS so far (no pycache created, no push, no git add -A, plan/handoff/baseline/staging/DO_NOT_TOUCH untouched; re-audited at closeout) |

Orthogonal status at this update:
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS (W2 harness implementation substantially complete but unverified end to end)
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PARTIAL (V-02 partial; no frozen rules except items 8/9; nothing waived)
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS
NEXT_ACTION: (1) full 16-cell capture matrix to freeze capture-geometry-rulebook-v1.json + capture-matrix-v1.json; (2) then items 3 and 7; (3) fix the item 4 popup-vs-peer-occluder z-order failure and re-prove routing; (4) item 5 >=20 NSOpenPanel latency samples + bounds freeze; (5) repair the item 6 panel presentation (standalone window vs sheet) and republish the chooser predicate freeze under an explicit naming decision (existing provisional v1 files are append-only); (6) then start W3 only after W1/W2 are complete and verified.

Blockers (scoped, not task-blocking):
- items 3 and 7 are code-blocked on the item 1 frozen rule book (by design).
- item 5 deferred by the owner's STOP-AND-CONVERGE order.
- item 6 republish needs a Plan-level naming decision (semantic/contract, not a bounded Stage-04 fix) — the provisional v1 files cannot be rewritten in place.
- Escalation not required: no semantic validity/requiredness/gating/error/fallback/priority meaning was changed this session; the mechanical guards added only prevent an incomplete run from publishing a canonical freeze.

Residual risk: the harness popup was observed below an activated peer occluder window (item 4), and a real NSOpenPanel presented as a sheet is refused by the chooser predicate (item 6, notNewWindow). Both are fail-closed behaviours, but if either shape matches production routing/hosting, later live phases would stall rather than misfire; both must be resolved by evidence before live use.
LINE interaction this session: 0 (no launch, no clicks, no AX writes; GUI events posted only to own harness/occluder windows).

## Update 3 — closeout checkpoint and fresh-session handoff

checkpoint_time: 2026-09-25T12:00+08:00
branch: master
pre_closeout_HEAD: 9c29648 (origin/master matched before this closeout; no fetch/rebase performed)
owner_request: finish a coherent checkpoint, write a detailed commit message with intent/work/next steps, `git add`, commit, push, and leave a precise handoff for a new conversation before shutdown.

Stage-03 freshness and handoff:
- Recomputed plan SHA-256 `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`; review attempts 05 and 06 both remain `PLAN_APPROVED` for revision 3 and that exact hash. No plan edit or semantic replan was made.
- Archived the prior handoff byte-identically as `handoff-history/handoff-plan-r3-20260925T1200+0800.md` (SHA-256 `10a46357ae0ef81ebf1baa8d4e6b14d89235857ec6dc10c8f42a89b54e7969dd`).
- Compiled current continuation handoff at `handoff.md`; its bound SHA-256 is `af250fdb398749216d396a55df0ae8814de3ab294fc6b4b3783965990fe73cde` (`handoff.sha256` updated). It records all nine W2 item states, provisional-vs-validated artifacts, the current code delta, six orthogonal statuses, acceptance matrix, stop conditions and exact first action for a fresh Stage-04 session.
- Archived the actual current `swift test` output as `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` (SHA-256 `4d7dc802ee87b40599a9e8e58fd41c63b35417f223c7ac9fab18cf9f2fd12bc2`); only trailing whitespace was removed from the copied log.

Closeout verification actually observed:
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift test --package-path rev28` → exit 0; build complete; 28 tests, 0 failures.
- `git diff --check` → PASS after source changes and again after the handoff was written.
- Last process census → no `rev28harness`, `rev28occluder`, `rev28ctl`, or LINE process. The extra orphan harness/occluder pairs requested closed earlier were terminated; LINE was not opened.
- No GUI rerun was done for item 5 after the latest sampler/event/boundary changes. Its 20-sample run `HARNESS-20260925-114515` is PARTIAL: within scenario became `chooserObservedAfterWindow` at 5.19 s, timeout was `noChooserObserved`, late scenario had no eligible chooser; zero further input. Existing `postcondition-bounds-v1.json` and `postcondition-latency-observations-v1.json` remain provisional (hashes `da5795423ddc3a2a80dac4aef632ea6e7b0fd80f2f016d054d784453d5155f90` and `7ee9a9e5dc07333c06c56a56a4fcac241ccba89d7abdc80aac22359d06b3b647`).
- W2 item 6 PASS is bound to run `HARNESS-20260925-112927`: real chooser affirmed, lookalikes and invalid ownership cases refused, exact destination reflected, one AXPress action, marker verified. v2 predicate/calibration SHAs: `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` / `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569`.

Verification matrix (current evidence; no waiver):
| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_REQUIRED | WAIVER_ALLOWED | WAIVER_STATUS | CHECK_RESULT |
|---|---|---|---|---|---|---|---|
| V-01 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | PASS (earlier executable-context probe; not rerun in closeout) |
| V-02 | CORE | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | PARTIAL (W2 items 1–4, 6–9 pass; item 5 incomplete) |
| V-03 | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (live phase gated) |
| V-04 | CORE | OUTCOME | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (no live Save All) |
| V-05 | CORE | OUTCOME | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (no live chooser) |
| V-06 | CORE | OUTCOME | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (no production staging run) |
| V-07 | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN for closeout; baseline was previously verified, reverify before live work |
| V-08 | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | NO | NOT_ALLOWED | NOT_RUN (W3/W5 outstanding) |
| V-09 | CORE | DIAGNOSTIC | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (pre-live reviews not started) |
| V-10 | CORE | OUTCOME | HARD_CLEAN | NO | NO | NOT_ALLOWED | NOT_RUN (Stage 05 pending) |
| V-11 | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | NO | NO | NOT_ALLOWED | PARTIAL at this checkpoint; final staged-scope audit and push verification remain to record in the commit/push result |

Orthogonal status at closeout:
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: INCOMPLETE (V-02 partial and later required gates pending; no waiver)
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS
NEXT_ACTION: Fresh Stage 04 session re-verifies plan/review/handoff hashes, git/upstream, baseline/staging and environment; reruns item 5 on latest source in the synthetic harness; audits W2 items 1–9; only then starts W3. No LINE until all plan pre-live gates pass.

Commit/push scope and authority:
- Stage only the three modified Rev28 source files, this task's `execution.md`, `handoff.md`, `handoff.sha256`, the new archived handoff, and `evidence/20260925-rev28-native-closed-loop/**`. Preserve unrelated Rev27e plans/task/evidence and pre-existing `__pycache__` directories; never use `git add -A`.
- Plan R25 says no push. The owner has now explicitly authorized `add`, `commit`, and `push` for this closeout checkpoint; this current instruction overrides the plan only for this push. Use ordinary `git push origin master`, no force/rebase. Verify exact commit message, pushed HEAD/upstream and final tree, then report any push rejection without rewriting history.
- This is a checkpoint, not task completion. Do not create `result.md`; independent Stage 05 has not run.
