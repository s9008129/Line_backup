# Stage 04 progress — Rev28 native closed-loop (A/B offline evaluation)

AB_MODE: AB_IMPLEMENTATION_EVALUATION_OFFLINE_ONLY
REAL_LINE_INTERACTION: NONE (this entire run)
TASK_ID: T20260925-0647-01-rev28-native-closed-loop
BRANCH: v43-ab/deepseek-rev28
START_HEAD: 9cbaa1141595acb538d4672066072d2b8ffb7065
PLAN_SHA256: 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b
HANDOFF_SHA256: 67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33

## STATE

STATE: IN_PROGRESS

## CURRENT_GOAL (what we are solving now)

Finish the offline half of TEST_ORDER before any Phase A: rebuild the closed loop,
repair the independently reproduced defects, prove the composition through the real
state machine + typed evidence store + transaction authority with injected OS edges
(done), then (a) calibrate the current composer with real AppKit panels/SCK/Vision/AX
(step 5) and (b) complete the seven-topic V-09 exact-binding reviews (step 6).
Stop at AB_PHASE_A_READY; Phase B stays forbidden and LINE is never touched.

## CURRENT_BLOCKER

None open. All registered implementation blockers (compile, SEG-1, STAB-1, ELL-1, MAT-1)
and the new CAL-1 monitor SIGABRT are RESOLVED with evidence.

CAL-1 (resolved 2026-09-29): the current-composer driver aborted with SIGABRT
`freed pointer was not the last allocation` inside the strict monitor. Root cause is an
upstream Swift 6.3 -Onone defect with **default-argument async closures across module
boundaries** (swiftlang/swift#92017): the library copy of the default `sleep` closure
overflows its async context and corrupts the task allocator. Workaround: the driver now
passes `monotonicNow`/`sleep` explicitly. Evidence:
`analysis/ab-offline-20260929/composer-diagnostics/` (root-cause note, two crash reports,
probes, crash-free diagnostic run).

REMAINING GATE (registered, attempted under `--diagnose-only`; official run NOT_RUN):

    STAGE=04
    CHECK=CURRENT_COMPOSER_SYNTHETIC_APPKIT_CALIBRATION
    SURFACE=rev28/Tools + rev28harness bundle + SCK/Vision/AX/occluder/input sink (synthetic target only)
    EXPECTED=≥20 panel timings under the strict monitor with real NSOpenPanel, destination preparation + exactly one AXPress, refusal/crash branches, current-composer applicability reconfirmed (V-02); frozen HarnessCalibration blob untouched
    OBSERVED=DIAGNOSTIC_ONLY (driver path executes crash-free end-to-end; every item-03/04 refusal traced to the locked console session — CG/SCK see the panel, AX exposes only AXApplication placeholders while locked — so the official ≥20-timings run requires the Mac session to be UNLOCKED)

WAIT STATE (2026-09-29T10:45+08:00): the official run is ready to execute but the
console session is still locked (`CGSSessionScreenIsLocked=true`, frontmost
`loginwindow`) — verified by a live 25-minute poll (10:19–10:45). Pre-flight while
locked: frozen binding hashes re-verified (rulebook/predicate/ax-calibration/bounds/
latency/tripwire all match the v3 verdict record), `rev28ctl` + `rev28harness` +
`rev28occluder` + `rev28probe` binaries present in `rev28/.build/debug`, and the host
capability record shows axIsProcessTrusted / postEvent / screenCapture / SCK / Vision
all PASS (diag7 capability probe; host macOS 27.0 build 26A428 = same build as the
frozen calibration host). Official pass = verdict PASS with geometry + chooser +
timings + destination + refusals all true; exit code alone is not the signal (PARTIAL
also exits 0, blocked paths exit 75).

## PLAIN-LANGUAGE STATUS (required)

- What are we trying to solve now? — Land the official ≥20-timings native calibration
  of the current composer (needs the console session unlocked), then complete the
  independent V-09 code/rule reviews; the rest of the offline half is done.
- What is blocking us? — Nothing is blocked. The official calibration run needs the Mac
  session unlocked (while locked, AX exposes only placeholder elements, so the harness
  panel cannot be located); that is an environment precondition, not a defect.
- How many meaningful attempts have we spent? — 8 charged material attempts total
  across six fingerprints: compile blocker 1/3, SEG-1 1/3, STAB-1 1/3, ELL-1 1/3,
  MAT-1 2/3, CAL-1 2/3. All resolved; no fingerprint exhausted; no oscillation.
- What did the last attempt teach us? — The current-composer SIGABRT was an upstream
  Swift 6.3 -Onone defect, not a driver race: a library module's default-argument
  async closure is emitted in both the library and the client with disagreeing async
  context sizes (swiftlang/swift#92017), so the monitor's `sleep` closure overflows
  its context and corrupts the task allocator. Passing `monotonicNow`/`sleep`
  explicitly in the driver removes the crash: diag6 (fix build) and diag7 (clean
  build) complete end-to-end exit 0, 168/168 tests green, provenance PASS.
- Are we closer to success? — Yes, materially. The strict monitor now runs crash-free
  end-to-end against real synthetic AppKit panels; only the official ≥20-timings run
  (after unlock) and the V-09 reviews remain before AB_PHASE_A_READY.
- What happens if the next attempt fails? — Step 5 is calibration, not a repair loop:
  if the official run under an unlocked session still refuses to locate the panel, or
  the strict-predicate/monitor calibration does not reproduce on the current composer,
  that is a V-02 applicability finding; repair mechanically if the mismatch is bounded
  and mechanical, otherwise stop and route REPLAN_REQUIRED. A run that fails only
  because the session locked again is an environment artifact and is reported as such.
  No Phase A claim is made either way.

## COUNTERS (budget is TASK_ID + BLOCKER_FINGERPRINT)

| FINGERPRINT | MATERIAL_ATTEMPTS | OF MAX 3 | STATUS |
|---|---|---|---|
| STAGE=04 CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION | 1 | 3 | RESOLVED |
| STAGE=04 CHECK=SHORT_END_DATE_ALBUM_SEGMENTATION (SEG-1) | 1 | 3 | RESOLVED |
| STAGE=04 CHECK=EQUAL_TAIL_STABILITY_SPAN (STAB-1) | 1 | 3 | RESOLVED |
| STAGE=04 CHECK=ELLIPSIS_PIXEL_ROW_ORIENTATION (ELL-1) | 1 | 3 | RESOLVED |
| STAGE=04 CHECK=NATIVE_COMPOSITION_MATRIX_FAILURES (MAT-1) | 2 | 3 | RESOLVED |
| STAGE=04 CHECK=CURRENT_COMPOSER_MONITOR_SIGABRT_TASK_DEALLOC (CAL-1) | 2 | 3 | RESOLVED |

CONSECUTIVE_NO_INFORMATION_GAIN: 0 / MAX 2
OSCILLATION: none (no A→B→A).
Reconciliation: R3 fixture repairs (wrong expected union maxX, single-glyph fixture)
have a different fingerprint and are not charged here. No budget was reset; every
counter below is carried forward explicitly and no fingerprint has been re-opened.
CAL-1 charging: two charged material attempts (instrumented diagnosis; root-cause fix +
verification). Raw runs against the same failed acceptance condition: six diagnostic runs
(diag1, diag2 pre-session; diag3 malloc-instrumented, diag4/diag5 traced, diag6 fix build,
diag7 clean build) plus one non-crashing smoke run. The three pre-fix crash runs are
charged as attempt 1 (same hypothesis family: reproducibility/heap corruption) because
diag2 added no new cause hypothesis — only confirmation. Under the strictest reading
(each crash run charged separately) the fingerprint would be 3 of 3 with monotone
information gain, resolved by the immediately following fix attempt; nothing was silently
reset or re-opened either way. Disclosed for Stage 05 / high-reasoning review.

## ATTEMPT LOG

### ATTEMPT_ID: A1 (compile blocker, pre-registered)

BLOCKER_FINGERPRINT: STAGE=04 CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION
HYPOTHESIS: The compile failure is exactly the two helper-call forms introduced
by 0d373ae (`binding()` on a computed property; `ocr(...)` instead of `item(...)`);
replacing them with the existing interfaces restores compilation, and the
secondary type-inference diagnostics disappear with it.
EXPERIMENT_OR_CHANGE: Smallest edit in StructuralLocatorsTests.swift:
`binding()` → `binding` and `ocr(` → `item(` in the two added tests only.
No test deletion, no skip, no expected-refusal change.
EXPECTED_DISTINGUISHING_RESULT: `xcrun swift build --package-path rev28` succeeds
and `xcrun swift test --package-path rev28 --filter StructuralLocatorsTests`
executes test cases (instead of failing to compile). If instead the same compile
failure persists, the hypothesis is falsified and the budget must be counted.

#### A1 OBSERVED RESULT

OBSERVED_RESULT: `xcrun swift build --package-path rev28` → exit 0 ("Build complete!").
`xcrun swift test --package-path rev28 --filter StructuralLocatorsTests` → test target
COMPILED and executed: 12 tests, 3 failures (0 unexpected). The three failures are the
pre-existing segmentation defect, not the compile defect: the two short-end-date tests
fail because `segmentAlbumCards` returns 0 regions (unsafeGeometry / no candidate).
Logs: `analysis/ab-offline-20260929/A1-build.log`, `A1-structural-test.log`.
ACCEPTANCE_DELTA: DETERMINISTIC_SWIFT_TEST_COMPILATION now PASSES (was the reviewed-head FAIL).
NEW_EVIDENCE: Compile failure was exactly the two helper-call forms; secondary diagnostics
were type-inference fallout. Runtime failure mode of the segmentation defect is now observed
in the test harness: 0 regions for `2024/05/13~05/17` input.
UNCERTAINTY_REDUCED: Yes — the "additional hidden compile errors" hypothesis is falsified.
INFORMATION_GAIN: YES
NEXT_DECISION: Close A1; open the next blocker (short end-date album segmentation) as its own
fingerprint with its own 3-attempt budget. Compile blocker is resolved and stays resolved.

MATERIAL_ATTEMPTS_USED (compile fingerprint): 1 of 3 → RESOLVED (no further attempts charged).

### ATTEMPT_ID: A2 (SEG-1, pre-registered)

BLOCKER_FINGERPRINT (SEG-1):

    STAGE=04
    CHECK=SHORT_END_DATE_ALBUM_SEGMENTATION
    SURFACE=rev28/Sources/Rev28Core/Perception/StructuralLocators.swift
    EXPECTED=segmentation accepts the exact short end-date representation used by the target and by the new tests; cross-card test refuses with referenceStructureMismatch
    OBSERVED=short end-date titles yield zero card regions; cross-card test refuses with unsafeGeometry

HYPOTHESIS: `isDateRangeTitle` accepts only full `yyyy/mm/dd` start and end dates, so the
reviewed title form `2024/05/13～05/17` never becomes an anchor and no regions are
derived; accepting an end date without a year (inheriting the start year) restores the
regions and lets the cross-card case fail for the right reason.
EXPERIMENT_OR_CHANGE: Extend `isDateRangeTitle` to parse start `yyyy/mm/dd` and end
either `yyyy/mm/dd` or `mm/dd` (year inherited), validate real calendar days,
retain `～`→`~` mapping and everything else unchanged.
EXPECTED_DISTINGUISHING_RESULT: `StructuralLocatorsTests` = 12/12 pass, including
`testSegmentAlbumCardsKeepsTargetCountInsideItsDateBand` (2 regions + candidate)
and `testSegmentAlbumCardsRejectsCrossCardCount` (refusal reason exactly
`.referenceStructureMismatch`). If regions stay 0 or the cross-card reason differs,
the hypothesis is falsified.

#### A2 OBSERVED RESULT

OBSERVED_RESULT: `xcrun swift test --package-path rev28 --filter StructuralLocatorsTests`
→ exit 0, "Executed 12 tests, with 0 failures". Both previously failing tests pass,
including the exact `.referenceStructureMismatch` cross-card refusal.
Log: `analysis/ab-offline-20260929/A2-structural-test.log`.
ACCEPTANCE_DELTA: SEG-1 resolved; short end-date segmentation and cross-card refusal
regressions are green.
NEW_EVIDENCE: The zero-region failure was exactly the missing short end-date form;
after adding it, anchor/region derivation equals the full-date case (2 regions).
UNCERTAINTY_REDUCED: Yes — no hidden second parser defect surfaced.
INFORMATION_GAIN: YES
NEXT_DECISION: Add minimal exact-form regression coverage in StructuralLocatorsTests
(full-end and malformed forms) as part of this step's test strategy; then open STAB-1.

MATERIAL_ATTEMPTS_USED (SEG-1): 1 of 3 → RESOLVED.

### ATTEMPT_ID: A3 (STAB-1, pre-registered)

BLOCKER_FINGERPRINT (STAB-1):

    STAGE=04
    CHECK=EQUAL_TAIL_STABILITY_SPAN
    SURFACE=rev28/Sources/Rev28Core/Verification/StagingVerifier.swift
    EXPECTED=stability requires ≥3 equal contiguous snapshots spanning ≥4s and ≥5s without file/directory change
    OBSERVED=isStable true for an old different sample followed by a 0.2s equal tail (whole-history span used instead of equal-tail span)

HYPOTHESIS: `isStable` measures `last.observedAt - first.observedAt` over the whole
history while only comparing the last three signatures, so an old different sample
can lend its elapsed time to a fresh short equal tail. Measuring count and span on
the contiguous equal-signature run ending at the final snapshot (plus monotonic
observation order) makes the diagnostic false and keeps all existing positives true.
EXPERIMENT_OR_CHANGE: Rewrite the ordering/span guard in `isStable` to use the
contiguous equal tail; keep minimumSamples=3, minimumSpanSeconds=4,
quiescenceSeconds=5 and the existing signature definition unchanged. Add regression
tests: old-different-sample + short equal tail → false; earlier different sample +
≥4s equal tail with quiescence → true; reordered observation times → false.
EXPECTED_DISTINGUISHING_RESULT: StagingVerifierTests all pass; the diagnostic case
([t0 empty, t10 f, t10.1 f, t10.2 f]) yields isStable=false, while the existing
positive case (20/22/25, mtime 10) still yields true. If the diagnostic still yields
true or a valid case flips false, the hypothesis is falsified.

#### A3 OBSERVED RESULT

OBSERVED_RESULT: `--filter StagingVerifierTests` → 18/18 pass (14 existing + 4 new),
including the exact diagnostic shape (old-different-sample + 0.2s equal tail → false),
the contiguous-tail requirement, reordered-time rejection, and the positive control
(earlier different sample + ≥4s equal tail with quiescence → true). `--filter
StructuralLocatorsTests` → 13/13 pass including the new exact-form regression.
Logs: `analysis/ab-offline-20260929/A3-staging-test.log`, `A3-structural-test.log`.
ACCEPTANCE_DELTA: STAB-1 resolved; stability now measures count/span on the contiguous
equal tail ending at the final snapshot and rejects reordered observation times.
NEW_EVIDENCE: The diagnostic reproduction now yields false; valid cases remain true.
UNCERTAINTY_REDUCED: Yes — no other stability caller depends on the old whole-history span.
INFORMATION_GAIN: YES
NEXT_DECISION: Proceed to TEST_ORDER steps 2 (deterministic suite then full suite on
this real Mac) and 3 (25-case adversarial suite + 20 pinned replay fixtures, twice each).

MATERIAL_ATTEMPTS_USED (STAB-1): 1 of 3 → RESOLVED.

### ATTEMPT_ID: A4 (ELL-1 ellipsis pixel row orientation)

BLOCKER_FINGERPRINT (ELL-1):

    STAGE=04
    CHECK=ELLIPSIS_PIXEL_ROW_ORIENTATION
    SURFACE=rev28/Sources/Rev28Core/Perception/AlbumEllipsisLocator.swift (EllipsisPixelDetector)
    EXPECTED=on the pinned v5 frame the album-header ellipsis is reported at the reviewed top-left capture rows 44/49.5/55 and the matrix composition reaches ELLIPSIS_LOCATED
    OBSERVED=component rows are mirrored (587.0/592.5/598.0 on the 643-px frame); the reviewed header band finds no eligible triple and every composition case refuses ELLIPSIS_LOCATED missingIdentity

DISCOVERY: first red run of the new native composition matrix (A10 attempt 1) refused
ELLIPSIS_LOCATED `missingIdentity` in 12 of 24 failing cases while the same geometry
passed in pure-geometry unit tests. Reproducing the detector on the pinned v5 frame
`evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` (SHA
4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3) showed the dot
components at y ≈ 587/592.5/598 — the vertical mirror of the reviewed 44/49.5/55.

HYPOTHESIS: the grayscale bitmap context is flipped twice — the explicit
`translateBy(0,h)`/`scaleBy(1,-1)` plus CoreGraphics' own row handling — so the
detector reads a vertically mirrored image. Drawing with the default CTM stores rows
in capture order (row 0 = capture top) and makes component y equal top-left capture
pixels, consistent with `OcrGeometry.item`.
EXPERIMENT_OR_CHANGE: remove the CTM flip in `EllipsisPixelDetector` (perception only;
no threshold, spacing, band or eligibility rule changed). Add regression coverage:
synthetic dot rows must be reported as 44.5/50.5/56.5, and a new pinned-frame test
must read the archived jpg, verify its SHA-256 and assert rows 44.0/49.5/55.0.
No fixture (`MatrixFrame.image(withEllipsisDots:)`) change was required.
EXPECTED_DISTINGUISHING_RESULT: pinned-frame test reports exactly 44.0/49.5/55.0 and
7/7 AlbumEllipsisLocatorTests pass; the matrix's ellipsis refusals disappear while all
other refusals stay unchanged. If rows stayed mirrored, the hypothesis is falsified.

#### A4 OBSERVED RESULT

OBSERVED_RESULT: `--filter AlbumEllipsisLocatorTests` → 7/7 pass (6 pre-existing + the
new pinned-frame test). Matrix attempt 2 (09:20) has zero ellipsis refusals remaining.
Replay: `A12-replay-run-{1,2}.json` are byte-identical to the pre-fix baseline
`A8-replay-run-1.json` (sha256 d8a59cd7d8d6f07c…) with verdict PASS, failures [].
Full suite 168/168 twice (A11). Logs: `A11-full-suite.log`, `A11-full-suite-2.log`,
`A12-replay-run-1.json`, `A12-replay-run-2.json`.
ACCEPTANCE_DELTA: ELL-1 resolved; the reviewed v5 orientation is now the detector's
contract and is locked by a byte-pinned frame test.
NEW_EVIDENCE: the mirror was exactly the missing orientation; detection rows now equal
the v5 records; replay segmentation is unchanged by the fix (byte-identical output).
UNCERTAINTY_REDUCED: Yes — the alternative hypothesis "matrix fixture dots were placed
outside the band" is falsified (no fixture change was needed).
INFORMATION_GAIN: YES
NEXT_DECISION: keep the pinned-frame test as the permanent orientation lock; continue
with the remaining matrix failures (MAT-1) which are now the only red suite.

MATERIAL_ATTEMPTS_USED (ELL-1): 1 of 3 → RESOLVED.

### ATTEMPT_ID: A5 (MAT-1 native composition matrix failures)

BLOCKER_FINGERPRINT (MAT-1):

    STAGE=04
    CHECK=NATIVE_COMPOSITION_MATRIX_FAILURES
    SURFACE=rev28/Tests/Rev28CoreTests/NativeCompositionMatrixTests.swift (+ fixture)
    EXPECTED=29-case matrix over the real Rev28Core composition (injected OS edges only) reaches 0 failures with unchanged refusal semantics, ledger counts and evidence accounting
    OBSERVED=29 tests, 24 failures (6 unexpected) on the first full run

ATTEMPT 1 (09:14) — hypothesis: the new fixture's frames/ledger expectations describe the
composition incorrectly, and remaining refusals are fixture alignment. OBSERVED: 29 tests,
24 failures (6 unexpected) — including 12 `ELLIPSIS_LOCATED missingIdentity` refusals
(which routed to the ELL-1 production blocker above), plus capture-ledger counts,
pre-save refusal expectations, destination primitive ordering and intent-after-press
accounting. INFORMATION_GAIN: YES (found a real production defect; separated fixture-vs-
product failure classes).

ATTEMPT 2 (09:19–09:22) — hypothesis: with the ellipsis orientation fixed, the remaining
failures are fixture/expectation mismatches only (menu-row OCR shape, second-owner
continuation expectations, one capture-ledger count). OBSERVED: intermediate run (09:20)
29 tests, 10 failures (1 unexpected), zero ellipsis refusals; after completing the
fixture/matrix alignment the 09:22 run is 29 tests, 0 failures.
INFORMATION_GAIN: YES (each run's failure set strictly shrank; no oscillation).

#### A5 OBSERVED RESULT

OBSERVED_RESULT: `A10-matrix.log` → 29 tests, 0 failures (0 unexpected), 19.491 s.
Happy path: ledger (2,2), reversibleDispatchCount 5, state.transition 14, sink 3 moves /
6 buttons, chooser pressCalls 1, panelBoundCalls 6, sampleCalls 1, 15 capture states
ending FILESYSTEM_STABLE, 15 retained observations, 14 state artifacts. Pre-save refusal
ledger [appReady 1, groupReady 2, albumListReady 3, targetAlbumLocated 4,
albumDetailVerified 6, ellipsisLocated 7, menuVerified 8, saveAllLocated 9]; intent
accounting: pre-intent readiness loss → 0 intent, post-intent → 2 records with pressCalls 0
and no retry.
ACCEPTANCE_DELTA: MAT-1 resolved; the composed production pipeline now has an executable
offline contract covering happy path, refusals, restart, tampering and content verification.
NEW_EVIDENCE: the two red runs each produced a strictly smaller failure set (24 → 10 → 0)
with distinct causes; the first red run is what exposed ELL-1.
UNCERTAINTY_REDUCED: Yes — "the composition refuses legitimate work" is falsified for all
29 scenarios at the reviewed rules.
INFORMATION_GAIN: YES
NEXT_DECISION: freeze the matrix as regression evidence; then re-run the full suite twice
(A11) and the replay fixtures twice (A12) to prove nothing else moved.

MATERIAL_ATTEMPTS_USED (MAT-1): 2 of 3 → RESOLVED. Transparency note: the fingerprint saw
three runs (09:14, 09:20, 09:22) but two charged material attempts — the 09:20 and 09:22
runs belong to one change set (attempt 2), whose remaining fixture alignments were
completed between them. Under the strictest reading the fingerprint would be 3 of 3 ≤ 3
with monotone information gain and no oscillation; nothing was silently reset either way.

### ATTEMPT_ID: A6 (CAL-1 current-composer monitor SIGABRT)

BLOCKER_FINGERPRINT (CAL-1):

    STAGE=04
    CHECK=CURRENT_COMPOSER_MONITOR_SIGABRT_TASK_DEALLOC
    SURFACE=rev28/Sources/rev28ctl/ComposerCalibration.swift + Rev28Core PostconditionMonitor (monitor task)
    EXPECTED=the current-composer driver runs the strict-predicate monitor end-to-end (panelShown → panelClosed → fileGrew → deadline) with no crash and can produce the official ≥20-timings calibration
    OBSERVED=in-process SIGABRT `freed pointer was not the last allocation` at swift_task_dealloc while the monitor task was suspended in `await sleep(...)` (PostconditionMonitor.swift:155), driven from rev28ctl

ATTEMPT 1 (instrumented diagnosis; diag1–diag5): hypothesis family — the crash is a
driver misuse or a data race around the monitor task. OBSERVED: the crash reproduces
across runs and builds (diag3 with the malloc guard; diag4/diag5 traced builds); both
`.ips` reports symbolicate to `PostconditionMonitor.swift:155` reached from the driver's
monitor task, with allocator evidence at `swift_task_dealloc`; hypotheses about the
sampler/windowID/telemetry were falsified. INFORMATION_GAIN: YES (reproducibility,
exact crash site, allocator mechanism).

ATTEMPT 2 (root cause + fix; diag6 fix build, diag7 clean build): hypothesis — the crash
is upstream swiftlang/swift#92017: a library module's default-argument async closure is
emitted in both the library and each client module, the two copies disagree on the async
context size under `-Onone`, and the overflow corrupts the task allocator; passing the
closures explicitly leaves only one copy and removes the crash. OBSERVED: diag6/diag7
complete end-to-end, exit 0; verdict=DIAGNOSTIC_ONLY; blocker
`ACTIVATION_REFUSED_DIAGNOSTIC_BYPASS frontmost=com.apple.loginwindow` (locked session);
no SIGABRT in either run. INFORMATION_GAIN: YES.

#### A6 OBSERVED RESULT

OBSERVED_RESULT: new file-private `runCurrentComposerMonitor(bounds:sampler:)` in
ComposerCalibration.swift calls `PostconditionMonitor.run` with `monotonicNow:` and
`sleep:` passed explicitly; all seven driver call sites use it. Rev28Core (including the
monitor's defaults) and its tests are untouched; `HarnessCalibration.swift` still matches
the frozen v3 provenance blob `c411011b1b44b1efb614e000f526b2118f45d120`. Verification:
`xcrun swift test --package-path rev28` → 168/168 pass;
`python3 -B rev28/Tools/verify_pre_live_provenance.py` → PASS; diag7 preserved under
`composer-diagnostics/CAL1-diag7-COMPOSER-20260929-101022/` with its own
`sha256sums.txt`, verified with `shasum -a 256 -c`.
ACCEPTANCE_DELTA: CAL-1 resolved; the driver path is crash-free end-to-end under the
strict monitor. The toolchain landmine remains reachable only from the frozen
HarnessCalibration path, which is bound by the W2 freeze and out of scope here.
NEW_EVIDENCE: the failure was a toolchain defect with a bounded driver-side workaround,
not a monitor-semantics or driver-race defect; locked-session probes show every
remaining item-03/04 refusal comes from the locked console session (CG/SCK list the
harness chooser window; AX exposes no window with a frame), so the official run requires
an unlocked session.
UNCERTAINTY_REDUCED: Yes — "driver misuse/race" and "monitor semantics broken" are both
falsified.
INFORMATION_GAIN: YES
NEXT_DECISION: land the fix and evidence, then run the official ≥20-timings calibration
into a new append-only run directory once the Mac session is unlocked.

MATERIAL_ATTEMPTS_USED (CAL-1): 2 of 3 → RESOLVED. Charging disclosure: six diagnostic
runs hit the same failed acceptance condition (diag1/diag2 before this session; diag3
malloc-instrumented; diag4/diag5 traced; diag6 fix build; diag7 clean build) plus the
crash reports preserved in `composer-diagnostics/`. The pre-fix crash runs are charged as
one attempt (single hypothesis family with monotone information gain); under the
strictest per-run reading this would be 3 of 3, resolved by the immediately following
fix; nothing was silently reset or re-opened. Disclosed for Stage 05 / high-reasoning
review.

## STEP EVIDENCE INDEX (append-only, analysis/ab-offline-20260929/)

- A1-build.log, A1-structural-test.log — compile blocker fix + focused run.
- A2-structural-test.log — SEG-1 fix, 12/12.
- A3-staging-test.log, A3-structural-test.log — STAB-1 + 13/13 structural.
- A4-deterministic-suite.log (124), A4-full-suite.log (129) — step 2, macOS deterministic
  workflow + full suite (Vision/hosted limitations kept explicit).
- A5-adversarial-1.log, A5-adversarial-2.log — step 3 adversarial suite 27/27 twice.
- A6-replay-{1,2}.log + A6-replay-run-{1,2}.json — step 3 replay 20/20 twice, PASS.
- A7-segmentation-replay-test.log — replay now drives actual segmentation (2/2).
- A8-replay-{1,2}.log + A8-replay-run-{1,2}.json — replay with
  `segmentation_replay_verdict: PASS`; pre-ellipsis-fix baseline.
- A9-deterministic-suite.log (126), A9-full-suite.log (131) — step 2 re-run after step 3.
- A10-matrix-attempt1.log (24 failures), A10-matrix-attempt2.log (10 failures),
  A10-matrix.log (0 failures) — step 4 native composition matrix.
- A11-full-suite.log, A11-full-suite-2.log — 168/168 twice.
- A12-replay-{1,2}.log + A12-replay-run-{1,2}.json — replay twice post-fix, byte-identical
  to A8 (sha256 d8a59cd7d8d6f07c…).
- `python3 -B rev28/Tools/verify_pre_live_provenance.py` → PASS (v3 manifest;
  `rev28/Sources/rev28ctl/HarnessCalibration.swift` git blob frozen at 4a3fe1c4…).
- Correction (2026-09-29): the v3 provenance manifest binds `HarnessCalibration.swift`
  to git blob `c411011b1b44b1efb614e000f526b2118f45d120` (printed by the verify script,
  unchanged after the CAL-1 fix); `4a3fe1c4…` above was a stale draft value.
- composer-diagnostics/CAL1-root-cause-note.md — CAL-1 root cause (upstream
  swiftlang/swift#92017), the driver-side explicit-closure workaround, and the
  verification list.
- composer-diagnostics/CAL1-diag7-COMPOSER-20260929-101022/ — crash-free
  `--diagnose-only --timings 1` run end-to-end (items + logs + sha256sums.txt, verified
  with `shasum -a 256 -c`).
- composer-diagnostics/CAL1-crash-report-095613.ips, CAL1-crash-report-095920.ips —
  the two SIGABRT reports (`PostconditionMonitor.swift:155` ← driver monitor task).
- composer-diagnostics/CAL1-full-suite-post-fix.log — full 168/168 suite re-run after
  the CAL-1 fix (exit 0, 0 failures, 20.7 s).
- composer-diagnostics/CAL1-probe3-cg-sck-under-lock.log,
  CAL1-probe4-ax-under-lock.log — locked-session split: CG/SCK list the harness chooser
  window; AX exposes only AXApplication placeholders (`kAXErrorAttributeUnsupported`
  -25205) and no window with a frame.
- composer-diagnostics/CAL1-upstream-issue-92017.json — upstream issue record.

## REVERIFY_ON_START (executed 2026-09-29, offline only)

- git fetch origin --prune: OK. origin/rev28-prelive-finalization == 9cbaa11… == local HEAD. No drift.
- Plan SHA == 05413807…: PASS. Handoff SHA == 67fc16a6…: PASS.
- Review attempt-07: PLAN_APPROVED, REVIEWED_HEAD 67c4fad9…, plan SHA bound; snapshot byte-identical per review report.
- Baseline recompute (read-only, 2026-09-29): count=57, bytes=17,924,900,
  content multiset ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf,
  tripwire b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd,
  per-file name/size/sha256/mtime_ns all match baseline-readonly.json (0 mismatches).
- Old staging /Users/hsiaojohnny/LINE-Backup-PoC/staging/RUN-20260923-111908-01: empty (0 entries).
- No production LINE interaction, no GUI, no SCK/AX/Quartz against LINE in this run.
- Stray harness bundle process from the earlier calibration experiment (PID 82242,
  `/tmp/rev28cal-test.emtn0L`) was terminated before any repo mutation; no occluder or
  rev28ctl process remained.

## COMMITS (branch-local, atomic, no push)

- fc67dd0 test(rev28): restore StructuralLocators helper usage (A1, blocker resolved)
- dc699e2 fix(rev28): accept reviewed short end-date album title forms (A2, regression test included)
- 9323855 fix(rev28): require contiguous equal-tail stability span (A3, regressions included)
- 99f0ca9 test(rev28): replay pinned album observations through actual card segmentation
- 441ac9c feat(rev28): persistent goal slot, pre-intent continuation, post-move revalidation
- 9470520 feat(rev28): add native observation session, typed evidence store and common composition
- 4dbbb0a feat(rev28): add read-only tripwire journal and pre-dispatch context gate
- 391b3f1 feat(rev28ctl): production composition for the native live closed loop
- c6a670e fix(rev28): correct ellipsis pixel row orientation (A4/ELL-1, pinned-frame test included)
- 33b168c test(rev28): add native composition matrix fixture and failure matrix (A5/MAT-1)
- 306c08c chore(rev28): record offline closed-loop evidence and Stage 04 progress
- 936536f feat(rev28ctl): add current-composer synthetic calibration
- <this commit> chore(rev28): record composer-diagnostics evidence and CAL-1 resolution

## STOP_POINT

- Convergence guard (3 same-fingerprint attempts / 2 consecutive no-gain / A→B→A).
- Any need to change load-bearing Plan semantics → REPLAN_REQUIRED, stop.
- Offline readiness reached → STATE: AB_PHASE_A_READY (do not enter Phase A; Phase B forbidden).
- Absolute prohibition: no real LINE interaction at any point in this run.
