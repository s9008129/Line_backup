# V-09 attempt-04 — Reviewer Report: 01-perception-geometry

- **Task**: T20260925-0647-01-rev28-native-closed-loop (V-09 pre-Phase-A code/rules review, attempt-04: fresh verification of the attempt-03 M-1 repair)
- **Reviewer context**: `01-perception-geometry` (C2/C3 perception and geometry: retained-frame capture and epochs, AX window identity binding, Vision/OCR and locator surfaces, menu/addressable-bounds containment, single-display scale, the perception/geometry half of the readiness margin repair)
- **Branch**: `v43-ab/codex-rev28`
- **Bound product tree**: `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`; observed HEAD `5ed71064a9f93d4abc27eecc857e3584a1b2a2ae` (3 commits above the product tree — `3d74248b`, `c945f04`, `5ed7106` — each touching only `.agent/` paths)
- **Implementation digest (bound and observed)**: `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686` — 48 manifest paths (36 `Rev28Core` swift + 9 `rev28ctl` swift + `rev28/Package.swift` + 2 files under `rev28/Tools`)
- **Worktree**: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- **Date**: 2026-09-29 (Asia/Taipei)
- **Read-only statement**: strictly read-only. Observed worktree state; read source/plan/handoff/progress/logs; recomputed hashes with `rg`/`sed`/`awk`/`shasum`, read-only git (`rev-parse`, `merge-base`, `diff`, `log`, `show`, `ls-files`, `hash-object`, `status`) and read-only python hashing. No build, no test execution, no product binary, no `rev28ctl`, no LINE.app interaction, no OS events, no git write. The exact bytes bound at `cf39fdcc` were re-read; nothing in attempt-01/02/03 is cited as proof for any verdict below.
- **PHASE_B_STATUS**: `FORBIDDEN_AB_EVALUATION`. No Save All dispatch, no destination confirmation, no irreversible action.

bindings_verified: PASS (all)

## 1. Bindings verification (independently recomputed)

| Item | Bound | Recomputed | Result |
|---|---|---|---|
| Product tree is `cf39fdcc` | required | `cf39fdcc` is an ancestor of HEAD; `git diff --stat cf39fdcc -- rev28` empty; `git status --porcelain -- rev28` empty | PASS |
| `git diff --name-only cf39fdcc HEAD` | only `.agent/` paths | 21 paths, every one under `.agent/`; 3 commits, all `.agent`-only | PASS |
| `plan.md` SHA-256 | `05413807…f84c1b` | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | PASS |
| `handoff.md` SHA-256 | `67fc16a6…c227a33` | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | PASS |
| Implementation digest | `6734dda5…a686`, 48 paths | own Python replica of `ReviewedImplementationDigest.manifestPaths` (sorted path + NUL + bytes + NUL; 36+9+1+2) → `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`, 48 paths | PASS |
| Frozen artifacts (9) | bound map | all 9 re-hashed: rulebook `09e1cf2a…`, predicate `0472aa0a…`, calibration `13aa01a2…`, matrix `e0084782…`, tripwire ladder `d67abb17…`, restart fixture `146b373a…`, postcondition bounds `c10dcb43…`, latency observations `ca4beabe…`, freeze provenance `4f6f5fdc…` | PASS |
| Repaired-tree evidence | `a46–a54`, `cli-refusal-20260929T0807` | all files present; `a47` = 88/0 focused (regression test started+passed at lines 669-670), `a48` = 242/0, `a50`/`a51` = 27/27, `a52`/`a53` byte-identical `81f6da94…7261`, `a54` provenance PASS, transcript EXIT 77/77/77/64/77 with evidence files 0 / staging files 0 / ledger no / anchor no / one-shot not renamed; fixture `chooser-predicate.json`/`chooser-calibration.json` re-hash to the bound frozen values | PASS |

## 2. Scope and inputs

Inputs read (read-only): `v09/attempt-04/bindings.json`; `plan.md`, `handoff.md`, `progress.md`; bound source at `cf39fdcc`: `Geometry/Coordinates.swift`, `Actuation/QuartzActuator.swift`, `Perception/StructuralLocators.swift`, `Perception/AlbumEllipsisLocator.swift`, `Perception/OcrEngine.swift`, `Sensor/FrameCapture.swift`, `Sensor/WindowSensor.swift`, `Identity/AXWindowIdentitySelector.swift`, `Identity/WindowIdentity.swift`, `Observation/NativeObservationSession.swift`, `Composition/ProductionObservationSource.swift`, `Composition/ComposedNativeAdapter.swift`, `Composition/LiveComposition.swift`, `Composition/PostSaveComposition.swift`, `Transaction/ReviewedImplementationDigest.swift`; `rev28ctl/main.swift`; tests `ActuationReadinessTests.swift`, `StructuralLocatorsTests.swift`, `NativeObservationSessionTests.swift`, `AdversarialMatrixTests.swift`; frozen JSON artifacts; execution-evidence logs. Producer commands were not re-executed; test results are cited as bound artifacts.

## 3. Per-claim verdicts (re-derived at `cf39fdcc`)

| Claim | Verdict |
|---|---|
| `V09_A3_M1_RETINA_MARGIN_SCALE` — margin converted at the observed capture scale | VERIFIED |
| `V09_A3_M1_REGRESSION_TEST` — code-level coverage | VERIFIED |
| `V09_A3_M1_NO_BEHAVIOR_DRIFT` — semantics match `isDispatchable`; production candidates keep behaviour at real scales | VERIFIED |
| `V09_A2_MAJOR_2_POST_HOVER_REVALIDATION` — perception/geometry half | VERIFIED |
| `V09_AX_IDENTITY_WINDOW_UNBOUND` (in force) | VERIFIED |
| `V09_MENU_BOUNDS_UNBOUND` + `01-MINOR-1` disposition (in force) | VERIFIED |
| `DIGEST_MANIFEST` | VERIFIED |

### 3.1 `V09_A3_M1_RETINA_MARGIN_SCALE` — VERIFIED

- `CaptureGeometryRules.dispatchMinimumMarginPt: Double = 1.0` is a single constant (`Geometry/Coordinates.swift:325`, doc cites `plan.md:130` "1 point — **not 1 pixel**").
- `isDispatchable(point:safeRect:minimumMarginPt:)` now defaults to that constant (`Coordinates.swift:328-343`); its strict-interior + `margins.min()! >= minimumMarginPt` semantics are unchanged.
- New `isDispatchableCapturePixels(point:safeRect:captureScale:)` (`Coordinates.swift:348-365`): fail-closed on non-positive rect and on non-finite/non-positive scale (`:353-354`), strict interior (`:361`), and the invariant is `margins.min()! >= dispatchMinimumMarginPt * captureScale` (`:363`) — exactly the scale conversion the plan requires.
- Production call site: `DispatchReadinessGate.mintPermit` (`Actuation/QuartzActuator.swift:307`) now evaluates `CaptureGeometryRules.isDispatchableCapturePixels(point:safeRect:captureScale: observation.captureGeometry.scale)` at `:332-333`; the previous raw `±1` capture-pixel comparisons are gone (grep shows no other margin comparison in `mintPermit`). The guard keeps its independent scale validity checks (`:335`), so an invalid scale refuses twice over (fail-closed at both layers).
- Production mint call sites: `Composition/PostSaveComposition.swift:241` and `Composition/ComposedNativeAdapter.swift:305` — both pass the fresh `ReadinessObservation` whose `captureGeometry.scale` is the measured backing scale, so the conversion uses the real display scale rather than a caller constant.

### 3.2 `V09_A3_M1_REGRESSION_TEST` — VERIFIED (code-level; not executed)

`ActuationReadinessTests.testDispatchMarginConvertsOnePointAtCaptureScaleNotOnePixel` (`rev28/Tests/Rev28CoreTests/ActuationReadinessTests.swift:89-138`) asserts: 2× with 1 px margin throws (`:112-114`), 2× with exactly 2 px (= 1 pt) mints (`:117-119`), 3× with 2 px throws (`:121-123`), 1× with 1 px mints (`:125-127`), plus direct `isDispatchableCapturePixels` assertions including `captureScale: .nan` refusing (`:129-137`). The bound log `a47` shows this test started and passed (lines 669-670), and the focused run executed 88 tests with 0 failures.

### 3.3 `V09_A3_M1_NO_BEHAVIOR_DRIFT` — VERIFIED

- Both functions share `dispatchMinimumMarginPt`, use identical strict-interior (`>` min, `<` max) and `>=` interior rules (`Coordinates.swift:340/342` vs `:361/363`); at 1× the conversion is the identity, so the guard admits exactly the points `isDispatchable` admits.
- Production candidate points retain real margins: Save All places the point at the safe-cell midpoint (`StructuralLocators.swift:291`) with intrinsic insets (`targetOverlap.minX + 2`, width `−4`, at `:282-287`; vertical `edgeInset = max(2, min(6, …))` at `:281`); the ellipsis candidate places the point at the middle-dot centre inside a `+4 px` box intersected with the image bounds (`AlbumEllipsisLocator.swift:246-258`). At 2× both keep ≥1 pt margins; at 3× the geometry would have to produce sub-3 px margins to refuse, which the construction insets do not.
- `revalidateAfterHover` deliberately does not re-check the interior margin (`QuartzActuator.swift:374-424`): the point and safe rect are immutable permit fields (`:269-272`, initializer `:277`) and were validated at mint. The reasoning is sound — the only facts that can change post-hover (frame identity/geometry, binding, staleness, screen-point mapping) are re-checked (`:380-424`).
- Existing fixtures use a 100×100 safe rect centered at (50, 50) with `scale: 1` (`ActuationReadinessTests.swift:46-51`) — 50 px margins, far above 1 pt, and unaffected.

### 3.4 `V09_A2_MAJOR_2_POST_HOVER_REVALIDATION` (perception/geometry half) — VERIFIED

`revalidateAfterHover` re-checks applicationActive/targetFrontmost, exact windowID/pid/process/bundle/layer/onScreen identity, `currentBinding`, positive finite scale + positive capture image size, staleness ≤1 s, frame deltas ≤0.5 pt, safe-rect containment and image-size bounds, and the mapped screen-point delta ≤0.5 pt (`QuartzActuator.swift:374-424`); `topmostSurfaceMatchesTarget` walks the front-to-back CG list and requires the target windowID/pid at layer 0 (`:439-457`). The Save All path supplies a fresh-observation closure to the actuator (`PostSaveComposition.swift:262-273`, revalidation call at `:268`), so the revalidation runs on live facts, not stored ones.

### 3.5 `V09_AX_IDENTITY_WINDOW_UNBOUND` — VERIFIED

`AXWindowIdentitySelector.select` binds to the target CGWindowID: exact `windowNumber` preferred and ambiguity refused (`Identity/AXWindowIdentitySelector.swift:66-68`), else a unique frame match within 0.5 pt, else `targetWindowNotAddressable` (`:79`, `:89`) — selector `:60-96`; `isBoundToWindow` requires a recorded `matchMethod` (`Identity/WindowIdentity.swift:81`). `ProductionObservationSource.readAXIdentity` resolves the exact CG inventory entry and builds descriptors from the target PID's AX windows, never `windows[0]` (`Composition/ProductionObservationSource.swift:104-126`); the session refuses an unbound read (`Observation/NativeObservationSession.swift:235-243`). The only remaining `.first` AX read is the v3-frozen calibration harness blob (`c411011b…`), which is provenance-bound by the frozen artifact.

### 3.6 `V09_MENU_BOUNDS_UNBOUND` / `01-MINOR-1` disposition — VERIFIED

Config-supplied bounds (`rev28ctl/main.swift:88-89`, passed at `:297-298`, `:393-394`) are validated positive-size at composition time (`Composition/LiveComposition.swift:178-184`) and fail-closed against the retained frame for `.saveAllMenuRows` (`Observation/NativeObservationSession.swift:502-509`). The locator requires exact five-row reference-text equality (`StructuralLocators.swift:251`), every row band intersecting the menu (`:261`), a ≥8 px addressable ∩ menu (`:267-270`), a ≥8 px target overlap (`:272-274`), and a >2×>2 safe cell contained in the menu (`:282-288`). Single-display scale resolution stays fail-closed (`Sensor/FrameCapture.swift:154-163`). Hash-binding remains the explicitly tracked Phase A obligation (the frozen set contains no real LINE menu bounds), exactly as the disposition states.

### 3.7 `DIGEST_MANIFEST` — VERIFIED

Manifest definition (`Transaction/ReviewedImplementationDigest.swift:26-104`) enumerates both source roots' `.swift`, `rev28/Package.swift` and every regular file under `rev28/Tools`, sorts, derives repo-relative paths via the reviewed root marker, and hashes sorted (path + NUL + bytes + NUL). My independent replica produced the bound digest over the same 48 paths, matching `a49` (`ZZDIGEST_PATHCOUNT=48`).

## 4. Findings

### MAJOR
None.

### MINOR
None.

### INFO

**I-1: line shift after the repair.** The M-1 repair shifted `QuartzActuator.swift` lines by +3 relative to attempt-03 report citations; all citations in this report are the post-repair line numbers at `cf39fdcc`.

**I-2: `isDispatchable`'s default parameter is now the shared constant.** The calibration harness (`rev28ctl/HarnessCalibration.swift`) is byte-frozen and still evaluates invariant 5 through `isDispatchable`'s default; because the default now references `dispatchMinimumMarginPt`, the harness and the readiness gate provably share one threshold source. No action.

**I-3 (carried, unchanged): Phase A inventory AX pre-check is a 4 pt `contains` frame match** (`rev28ctl/main.swift` Phase A facts path), looser than the production identity gate; it is evidence-only and must not be read as production-equivalent AX binding.

**I-4 (carried, unchanged): `.saveAllMenuRows` out-of-frame bounds have no dedicated session-level test**; the containment guard is exercised indirectly and is simple enough that reading suffices.

verdict: PASS
