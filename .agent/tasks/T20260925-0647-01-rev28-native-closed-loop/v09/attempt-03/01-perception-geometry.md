# V-09 attempt-03 — Reviewer Report: 01-perception-geometry

- **Task**: T20260925-0647-01-rev28-native-closed-loop (V-09 pre-Phase-A code/rules review, attempt-03)
- **Reviewer context**: 01-perception-geometry (C2/C3 perception and geometry: retained-frame capture and epochs, AX window identity binding, Vision/OCR and locator surfaces, menu/addressable-bounds containment and single-display scale, perception/geometry half of the post-hover revalidation repair)
- **Branch**: v43-ab/codex-rev28
- **Bound head**: a758317b725370b008fe58c848e0d28463e86709 (`product_tree` commit under review)
- **Implementation digest (bound and observed)**: e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf — 48 files (36 `rev28/Sources/Rev28Core` swift + 9 `rev28/Sources/rev28ctl` swift + `rev28/Package.swift` + `rev28/Tools/replay_rev28.py` + `rev28/Tools/verify_pre_live_provenance.py`)
- **Worktree**: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- **Date**: 2026-09-29 (Asia/Taipei)
- **Read-only statement**: this review was strictly read-only. Observed worktree state, read source/plan/handoff/progress/logs, and recomputed hashes with `rg`/`sed`/`awk`/`shasum`, read-only git (`rev-parse`, `merge-base`, `diff`, `ls-tree`, `hash-object`, `status`), and read-only python hashing/inspection. No build, no test execution, no rev28ctl or other product binary, no LINE.app interaction, no OS events, no git writes (no add/commit/checkout/stash/reset). Producer evidence logs were read and hashed as artifacts only; none of their commands were re-executed. The only file written is this report. `bindings.json` was not modified.
- **PHASE_B_STATUS**: FORBIDDEN_AB_EVALUATION. No Save All dispatch, no destination confirmation, no irreversible action, no arming of any eligibility artifact, and nothing in this review enables Phase B.

bindings_verified: PASS (all)

## 1. Bindings verification (recomputed on this worktree)

### 1.1 Product tree / head / digest

| Item | Bound | Observed | Result |
|---|---|---|---|
| HEAD (for read-only checks) | — (reviewer may be ahead via `.agent`-only commits) | `16017b5e7068c9b9f6699dc784971ac41f228291` | INFO |
| a758317 is ancestor of HEAD | required | `git merge-base --is-ancestor a758317 HEAD` → yes | PASS |
| `git diff --stat a758317 -- rev28` | empty | 0 lines | PASS |
| `git diff --name-only a758317 HEAD` | only `.agent/` | only `.agent` (unique top-level prefix) | PASS |
| `git status --porcelain -- rev28` | clean | 0 lines | PASS |
| plan.md SHA-256 | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | PASS |
| handoff.md SHA-256 | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | PASS |
| `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` | `c411011b1b44b1efb614e000f526b2118f45d120` | `c411011b1b44b1efb614e000f526b2118f45d120`; also `git ls-tree a758317` blob `c411011b…` | PASS |
| Implementation digest | `e748568d…c0cf`, 48 paths | recomputed independently as sha256 over sorted (repo-relative path + NUL + bytes + NUL) for 36+9+1+2 paths → `e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf` | PASS |

The recomputation used the same manifest definition as `ReviewedImplementationDigest.manifestPaths` (`rev28/Sources/Rev28Core/Transaction/ReviewedImplementationDigest.swift:30-77`) and matched the a45 evidence log (`ZZDIGEST_PATHCOUNT=48`, `ZZDIGEST_SHA256=e748568d…c0cf`).

### 1.2 Frozen rule artifacts (9)

| Frozen artifact | Bound SHA-256 | Observed | Result |
|---|---|---|---|
| capture-geometry-rulebook-v1.json | `09e1cf2a…62ed` | `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed` | PASS |
| chooser-affirmation-predicate-v2.json | `0472aa0a…f3f2` | `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` | PASS |
| chooser-ax-calibration-v2.json | `13aa01a2…e569` | `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569` | PASS |
| capture-matrix-v1.json | `e0084782…ba7b` | `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b` | PASS |
| tripwire-attribution-ladder-v1.json | `d67abb17…3216` | `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` | PASS |
| restart-observe-only-fixture-v1.json | `146b373a…a93f` | `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` | PASS |
| postcondition-bounds-v3.json | `c10dcb43…5e84` | `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84` | PASS |
| postcondition-latency-observations-v3.json | `ca4beabe…b155` | `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155` | PASS |
| ci-w2-item5-freeze-provenance-v3.json | `4f6f5fdc…b152` | `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152` | PASS |

### 1.3 Repaired-tree evidence (a37–a45, cli-refusal-20260929T0742)

All files present under `.agent/tasks/…/execution-evidence/`. SHA-256 recomputed; quoted lines re-read from the artifacts (producer commands not re-run).

| Evidence | Observed SHA-256 | Quoted/observed summary line | Result |
|---|---|---|---|
| a37-build-attempt02-final-20260929T074109.log | `2d6ff883…e381` | `Build complete! (0.15s)` and `Build complete! (0.10s)`, with `EXIT_PROD=0` / `EXIT_TESTS=0` | PASS |
| a38-focused-attempt02-final-20260929T074114.log | `033e9be9…f652` | `Executed 96 tests, with 0 failures (0 unexpected)` (also the re-printed total line) | PASS |
| a39-full-suite-attempt02-final-20260929T074124.log | `3113cad1…933f` | `Executed 241 tests, with 0 failures (0 unexpected)`; no skipped-test summary (the only occurrence of "skip" is the test name `testMalformedArtifactIsNamedNotSkipped`) | PASS |
| a40-adversarial-attempt02-final-run1-20260929T074153.log | `de1d8f49…7d28` | `Executed 27 tests, with 0 failures (0 unexpected)` | PASS |
| a41-adversarial-attempt02-final-run2-20260929T074153.log | `09286e2d…febc` | `Executed 27 tests, with 0 failures (0 unexpected)` | PASS |
| a42-replay-attempt02-final-run1-20260929T074157.json | `81f6da94…7261` | `verdict=PASS`, `fixture_count=20`, `expected_fixture_count=20`, `failures=[]` | PASS |
| a43-replay-attempt02-final-run2-20260929T074157.json | `81f6da94…7261` | byte-identical to a42; `verdict=PASS`, 20/20, `failures=[]` | PASS |
| a44-provenance-attempt02-final-20260929T074210.log | `3bf448fa…eb1a` | `"status": "PASS"`, `"generation": "v3"`, `"implementationSourceGitBlobSHA": "c411011b1b44b1efb614e000f526b2118f45d120"`, `sampleCount 20` | PASS |
| a45-digest-attempt02-final-20260929T074221.log | `d4188b0a…86dd` | `ZZDIGEST_PATHCOUNT=48`, `ZZDIGEST_SHA256=e748568d…c0cf` | PASS |
| cli-refusal-20260929T0742/cli-refusal-transcript-20260929T0742.log | `20567f37…0a56` | `live-execute EXIT=77` / `live-preflight EXIT=77` / `CI guard EXIT=77` / `missing --config EXIT=64` / `stale reviewed-implementation digest EXIT=77`; `evidence files: 0`, `staging files: 0`, `ledger present: no`, `anchor present: no`, `one-shot renamed: no` | PASS |

Replay "output SHA-256" bound value `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261` equals the recomputed SHA-256 of both a42 and a43. The CLI fixture directory contains empty `evidence/` and `staging/`, no ledger/anchor file, and `one-shot-authorization.json` un-renamed; its transcript quotes `reviewedImplementationSHA256=e748568d…c0cf` (attempt-03 bound digest) for the live refusal runs and uses the superseded `e80e4f0f…54e9` only in `config-stale-digest.json` for the stale-digest refusal. These are refusal-only paths (no dispatch, no entitlement consumption).

## 2. Scope, inputs, checks

**Inputs read** (all read-only): `v09/attempt-03/bindings.json`; task `plan.md`, `handoff.md`, `progress.md`; attempt-02 `bindings.json` (only to recover the attempt-01 claims still in force); bound source at a758317: `Actuation/QuartzActuator.swift`, `Actuation/AXDriver.swift`, `Composition/ProductionActuationEnvironment.swift`, `Composition/ProductionObservationSource.swift`, `Composition/PostSaveComposition.swift`, `Composition/ComposedNativeAdapter.swift`, `Composition/LiveComposition.swift`, `Identity/AXWindowIdentitySelector.swift`, `Identity/WindowIdentity.swift`, `Observation/NativeObservationSession.swift`, `Perception/StructuralLocators.swift`, `Perception/AlbumEllipsisLocator.swift`, `Perception/OcrEngine.swift`, `Sensor/FrameCapture.swift`, `Sensor/WindowSensor.swift`, `Geometry/Coordinates.swift`, `Transaction/ReviewedImplementationDigest.swift`; `rev28ctl/main.swift`; tests `ActuationReadinessTests.swift`, `StructuralLocatorsTests.swift`, `NativeObservationSessionTests.swift`, `AdversarialMatrixTests.swift`, `CoordinateTransformTests.swift`; frozen JSON artifacts; execution-evidence logs a37–a45 and the CLI refusal fixture.

**Checks performed**: (a) worktree/head/diff/cleanliness checks; (b) independent digest recomputation of the 48-path manifest; (c) SHA-256 of plan/handoff/9 frozen artifacts/10 evidence files; (d) `git hash-object` + `ls-tree` for the frozen calibration source; (e) re-read of all in-scope claim code paths with `rg`/`sed` and line-numbered inspection; (f) cross-check of the in-scope production `windows[0]`/`.first` patterns. Producer commands were not re-executed; test-run results are cited as bound artifacts, not reproduced.

## 3. Per-claim verdicts (in-scope)

| Claim | Verdict |
|---|---|
| V09_A2_MAJOR_2_POST_HOVER_REVALIDATION — perception/geometry half (frame, capture point, safe rect, image size, addressed/topmost surface) | VERIFIED |
| DIGEST_MANIFEST — manifest includes `Package.swift` + every `rev28/Tools` file; relative paths derived from the reviewed root marker; reused for HEAD/diff checks | VERIFIED |
| V09_AX_IDENTITY_WINDOW_UNBOUND (prior attempt-01 claim still in force) | VERIFIED |
| V09_MENU_BOUNDS_UNBOUND (prior attempt-01 claim still in force; overlaps 01-MINOR-1) | VERIFIED |
| Calibration-harness AX read intentionally left as v3-frozen bytes (`windows(ofApp:).first`), provenance-clean | VERIFIED |
| 01-MINOR-1 trust-boundary disposition (reasoning only; no code change expected) | VERIFIED |

### 3.1 V09_A2_MAJOR_2_POST_HOVER_REVALIDATION (geometry/perception half) — VERIFIED

- `ReadinessPermit` retains the exact mint-time geometry facts: `windowFrame`, `capturePoint`, `safeRectCapturePx`, `captureImageSize` (`rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift:269-272`, initializer `:277-288`), plus a one-shot consume with ≤1 s mint expiry (`:293-303`).
- `DispatchReadinessGate.mintPermit` verifies positive safe rect, `safe.contains(point)`, interior margins, CG frame size, scale validity, capture bbox/image size, safe-rect and point containment in the capture image, and window-frame vs fresh-window-frame ≤0.5 pt (`QuartzActuator.swift:327-344`), then staleness ≤1 s (`:347-349`).
- `revalidateAfterHover` re-checks, against a freshly derived live observation: application active/target frontmost (`:378-382`), live window identity/process/layer/on-screen (`:384-390`), candidate binding equality (`:392`), fresh scale/image size (`:395-397`), fresh-observation staleness ≤1 s (`:399-401`), window frame 0.5 pt per side (`:403-407`), retained safe-rect containment + image-size bounds (`:410-413`), and re-derived screen point movement ≤0.5 pt (`:416-418`).
- The fresh observation is a genuinely live re-derivation: `ProductionActuationEnvironment.readinessObservation` → `ReadinessObservation.captureLive` re-checks bundle/process instance, re-reads SCK + CG inventories, re-captures a live screenshot, and requires the live PNG SHA-256 to equal the candidate binding frame hash and the identity capture hash (`QuartzActuator.swift:190-248`); any mismatch refuses before mouseDown.
- `topmostSurfaceMatchesTarget` uses front-to-back `CGWindowListCopyWindowInfo` (`onScreenOnly`, `excludeDesktopElements`) and requires the first alpha>0 window containing the screen point to be the target window with `layer == 0` (`QuartzActuator.swift:436-452`); it is the default `addressedSurfaceCheck` (`:474-478`) and is run inside `liveGuards` before the hover and again after revalidation (def `:497-510`; calls at `:511` and `:532`).
- `postClick` order is: consume permit → binding/intent guard → `liveGuards()` → record reversible/saveAll intent → post `mouseMoved` → `await postHoverRevalidation()` + `liveGuards()` → on failure `recordRevalidationOutcome(passed:false)` and throw before down/up; on success record `passed:true`, then post down + up (`QuartzActuator.swift:456-543`, failure branch `:530-538`, success `:539-542`).
- Callers wire the revalidation to the live environment: `PostSaveComposition.swift:266-272` (closure re-calls `environment.readinessObservation` + `revalidateAfterHover`) and `:279-284` (dispatch through `postSave.dispatchSaveAllClick`); reversible path `ComposedNativeAdapter.swift:314-320` and `:322-327`.
- Test evidence at the bound tree: `ActuationReadinessTests.swift:174` (focus theft between hover and mouseDown → zero click events), `:240` (failed post-hover revalidation → zero click events + recorded failure), `:279` (successful revalidation runs after hover and resets failures), `:313` (occlusion between hover and mouseDown → zero click events); `AdversarialMatrixTests` G05 (separate-process occluder) and G07 (popup movement invalidates candidate) pass in a40/a41. a38 `ActuationReadinessTests` is part of the 96/0 focused run.

Noted deviation (not part of this claim's text): the interior-margin threshold itself is a separate MINOR finding below.

### 3.2 DIGEST_MANIFEST — VERIFIED

`ReviewedImplementationDigest` unifies the manifest and the reviewed-path set: `sourceRoots` = the two source roots, `configurationPaths` = `rev28/Package.swift`, `toolRoots` = `rev28/Tools`, `reviewedPaths = sourceRoots + configurationPaths + toolRoots` (`ReviewedImplementationDigest.swift:26-44`); `manifestPaths` collects every `.swift` under the two roots plus the configuration path plus every regular file under `rev28/Tools`, sorts, and returns repo-relative paths (`:46-77`); `relativePath(of:under:)` derives the path from the reviewed root marker so `/private/var` does not break it (`:79-89`); `compute` hashes sorted (path + NUL + bytes + NUL) (`:91-104`). My independent recomputation of that exact algorithm over 36+9+1+2 paths produced the bound digest, and a45 records `ZZDIGEST_PATHCOUNT=48` with the same SHA-256.

### 3.3 V09_AX_IDENTITY_WINDOW_UNBOUND (prior attempt-01 claim still in force) — VERIFIED

- `AXWindowIdentitySelector.select` binds the AX read to the target CGWindowID: exact AX windowNumber preferred; more than one number match throws `ambiguousAXWindowMatch`; if no number match, requires `cgBounds`, then a unique frame match within 0.5 pt per side, else throws `targetWindowNotAddressable` (`Identity/AXWindowIdentitySelector.swift:66-96`); `matchMethod` records `.windowNumber` / `.frameGeometry`.
- `AXIdentityRead.isBoundToWindow` is true only when `matchMethod != nil` (`Identity/WindowIdentity.swift:63-82`).
- Production read path: `ProductionObservationSource.readAXIdentity(pid:windowID:)` looks up the exact CG inventory entry for the window, builds descriptors from the target PID's AX windows, and calls the selector; failure throws `axIdentityUnavailable` (`Composition/ProductionObservationSource.swift:104-126`).
- The session refuses an unbound AX read: `guard axIdentity.isBoundToWindow else { throw .identityMismatch(...) }` (`Observation/NativeObservationSession.swift:235-243`), and the AX read is bound to the same `main.windowID` (`:318`), with post-inventory identity revalidation (`:205-232`).
- No production `windows[0]`/`windows(ofApp:).first` AX identity read remains in `Rev28Core`; the only `.first` AX-window read is the calibration harness (`rev28ctl/HarnessCalibration.swift:2479`), which is byte-identical to the v3-frozen blob `c411011b…` (verified by `git hash-object`), so that intentional frozen read is provenance-clean (claim note verified).

### 3.4 V09_MENU_BOUNDS_UNBOUND (prior attempt-01 claim still in force) — VERIFIED

- Config-supplied bounds are declared as `menuBoundsCapture`/`addressableBoundsCapture` (`rev28ctl/main.swift:88-89`) and passed into the live environment (`:297-298`).
- Positive-size validation fails closed (`Composition/LiveComposition.swift:178-185`).
- Retained-frame containment fails closed for `.saveAllMenuRows`: `imageBounds.contains(menuBounds) && imageBounds.contains(addressableBounds)`, else `.unsafeGeometry` (`Observation/NativeObservationSession.swift:502-509`).
- Locator is fail-closed and ordered: exact five-row reference-text equality (with duplicate-target ambiguity refusal), row bands must intersect the menu bounds, addressable = menu ∩ addressable must be ≥8 px wide, target row must have ≥8 px addressable horizontal overlap, and the derived safe cell must be >2×>2 and contained in the menu (`Perception/StructuralLocators.swift:243-296`).
- Single-display scale: `FrameCapture.resolvedBackingScale` returns nil unless `displayCount == 1` with one known positive scale (`Sensor/FrameCapture.swift:154-163`).
- Hash-binding status: the frozen set contains no real LINE menu/addressable bounds (grep over the 9 frozen artifacts finds no menu-bounds geometry; only `AXMenuButton` role strings in the chooser calibration), and the obligation is recorded in `progress.md:228` and `progress.md:252` (Phase A on-the-spot obligation), consistent with the plan's Phase A evidence duty (`plan.md:246`) and frozen-rules requirement (`plan.md:130`).

### 3.5 Calibration-harness AX read / 01-MINOR-1 disposition — VERIFIED

- Harness frozen-read note: verified in 3.3 (blob equality).
- 01-MINOR-1 disposition reasoning verified: bounds are config-supplied but bounded fail-closed exactly as described (positive size + retained-frame containment + ordered five-row identity + per-row menu intersection + ≥8 px addressable overlap + safe-rect containment), and hash-binding remains an explicitly tracked Phase A obligation because the frozen set has no real LINE menu bounds; the disposition claims no more than that, so no code change is expected at this stage.

## 4. Findings

### MAJOR

None. The in-scope repair claims re-verify as claimed on the bound tree.

### MINOR

**M-1 (new, in scope): The production readiness permit enforces a 1-capture-pixel safe-boundary margin, not the plan's scale-converted 1-point refusal.**

- Contract: `plan.md:130` requires "1-point safe-boundary refusal (convert correctly at Retina scale; **not 1 pixel**)" and "Use frozen geometry configuration for capture and readiness alike"; `plan.md:152` requires the exact safe candidate to be revalidated before mouseDown.
- Code: `DispatchReadinessGate.mintPermit` compares the capture-pixel point against the capture-pixel safe rect with a raw `+1` / `-1` (`rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift:325-330`): `point.x > safe.minX + 1, point.x < safe.maxX - 1, point.y > safe.minY + 1, point.y < safe.maxY - 1`. `safeRectCapturePx`/`pointCapturePx` are capture pixels (`Perception/StructuralLocators.swift:25-33`), so the threshold is 1 pixel — 0.5 pt on a 2× Retina display — never multiplied by `observation.captureGeometry.scale`.
- The rules-level 1-pt invariant exists but has no production call site: `CaptureGeometryRules.isDispatchable(point:safeRect:minimumMarginPt: 1.0)` (`Geometry/Coordinates.swift:322-339`, doc "Invariant 5: a point within 1 pt (default)…") is used only by the calibration harness (`rev28ctl/HarnessCalibration.swift:1321, 1341, 1537-1538`) and unit tests (`CoordinateTransformTests.swift:285-293`, `AdversarialMatrixTests.swift:237`). The harness therefore evaluates invariant 5 with point semantics, while readiness uses pixel semantics — the divergence the plan line forbids.
- `revalidateAfterHover` re-checks only containment and image-size bounds, not the interior margin (`QuartzActuator.swift:410-413`); because the point is immutable after mint this is a consequence of the same threshold choice, not a second gap.
- Impact (why MINOR, not MAJOR): the two production candidate sources place the point at a midpoint with intrinsic construction insets — Save All: `targetOverlap.minX + 2` with width `-4` and vertical `edgeInset ≥ 2 px` around a midpoint (`StructuralLocators.swift:277-291`); ellipsis: `+4 px` box around the middle dot centre (`AlbumEllipsisLocator.swift:247-258`) — so real dispatch points retain ≥1 pt margins at 2× and identity/containment/stale-frame guards remain fail-closed. The defect is the guard's threshold semantics and its divergence from the frozen-rule evaluation; a hypothetical candidate 1 px (0.5 pt at 2×) inside the safe boundary would be accepted by readiness even though the plan requires refusal. Suggested repair direction (for a future attempt): convert the margin using the observation scale (or route the mint check through `CaptureGeometryRules.isDispatchable` with a scale-converted point/safe rect) and, for completeness, re-check the margin during `revalidateAfterHover`.
- Context only (not evidence): attempt-02's report asserted "1 pt safe-boundary margin … dispatch re-check" verified; this review re-derived that the production gate is 1 capture pixel. The attempt-02 verification is superseded and was not reused as proof.

### INFO

**I-1: Phase A inventory AX pre-check uses a 4 pt `contains` frame match, not the production selector.** `rev28ctl/main.swift:356-363` checks whether any AX window frame is within 4 pt of the target window frame for `PhaseAInventoryFacts`. This is evidence-only preflight (no dispatch path), but it is looser than the production identity gate (exact windowNumber, else unique 0.5 pt match); a Phase A PASS on `axWindowFrameMatch` should not be read as equivalent to production AX binding.

**I-2: Frame-fallback AX match does not exclude descriptors with a different non-nil windowNumber.** `AXWindowIdentitySelector.swift:81-87` filters by frame only; a descriptor whose own AX window number is present but different from the target could in principle be accepted by the unique-frame fallback. The common case (number equals target) is handled earlier, so this is a hardening note for unusual AX surfaces, not a demonstrated misbinding.

**I-3: CG inventory is read twice per capture.** The session reads `cgEntry` from `source.cgInventory()` (`NativeObservationSession.swift:372-377`), and `readAXIdentity` separately reads `cgInventoryProvider()` for the AX frame fallback (`ProductionObservationSource.swift:107`). Both occur inside the same session capture and before the post-inventory revalidation (`NativeObservationSession.swift:205-232`), so this is redundancy rather than epoch mixing; the two reads could disagree only on sub-0.5 pt frame details already tolerated by the selector.

**I-4: No dedicated session-level test for out-of-frame `.saveAllMenuRows` bounds.** The containment guard (`NativeObservationSession.swift:502-509`) is exercised indirectly; locator-level menu/addressable bound behavior is covered by `StructuralLocatorsTests.swift:114-150` (candidate, wrong neighbor, duplicate target). Coverage note only; the guard itself is simple and verified by reading.

verdict: ISSUES_FOUND
