# V-09 attempt-02 · Reviewer context 01 — perception & geometry

- Task: `T20260925-0647-01-rev28-native-closed-loop` (Stage 04, A/B branch `v43-ab/codex-rev28`)
- Worktree: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Reviewer: context `01-perception-geometry` — independent, read-only. No build/test/binary/LINE/OS-event/git-write action was performed. Tests were **not** executed by this review; test evidence below is read from the bound logs.
- Bindings: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/v09/attempt-02/bindings.json` (recorded 2026-09-29T07:28+0800)
- Prior context only (not proof): `v09/attempt-01/01-perception-geometry.md` (bound to superseded digest `eb4415f9…`); used only to re-check the earlier `V09_MENU_BOUNDS_UNBOUND` concern against the repaired tree.
- Phase B: `FORBIDDEN_AB_EVALUATION` — no production Save All dispatch enabled, simulated or requested.

bindings_verified: PASS (all)

## 1. Binding recomputation — exact observed results

HEAD / tree:

- `git rev-parse HEAD` → `7cd444e152daede802e21430f1501e17ddfd3784`.
  The announced pre-check value `0ce9e0505328a5fd9169cf98f045b0b180641d8e` is an ancestor (`git merge-base --is-ancestor 0ce9e05 HEAD` exit 0). Two later commits exist (`96ef88c`, `7cd444e`); `git diff --name-only 42ae9a3 HEAD | grep -v '^\.agent/'` → none (all changes are `.agent` records only). The literal HEAD moved beyond the announced SHA, but the bound product state is unchanged (see INFO-1).
- `git diff --stat 42ae9a3 -- rev28` → empty. `git diff --name-only 42ae9a3 HEAD -- rev28 | wc -l` → 0. `git status --porcelain -- rev28` → empty (clean worktree under `rev28`).

Plan / handoff:

- `plan.md` SHA-256 = `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` — matches bindings.
- `handoff.md` SHA-256 = `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` — matches bindings.

Implementation digest (sha256 over sorted `repo-relative path + NUL + file bytes + NUL` for every `.swift` under `rev28/Sources/Rev28Core` + `rev28/Sources/rev28ctl`):

- observed `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9`, file count 44 — matches bindings (superseded `03ac90b4…` not used).
- `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` → `c411011b1b44b1efb614e000f526b2118f45d120`; `git ls-tree 42ae9a3 -- …HarnessCalibration.swift` → same blob. Matches `ci_freeze_provenance.frozen_source_blob_sha`.

Nine frozen artifacts (`shasum -a 256`, all match bindings):

| Artifact | SHA-256 |
|---|---|
| `harness/frozen/capture-geometry-rulebook-v1.json` | `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed` |
| `harness/frozen/chooser-affirmation-predicate-v2.json` | `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` |
| `harness/frozen/chooser-ax-calibration-v2.json` | `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569` |
| `harness/frozen/capture-matrix-v1.json` | `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b` |
| `harness/frozen/tripwire-attribution-ladder-v1.json` | `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` |
| `harness/frozen/restart-observe-only-fixture-v1.json` | `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` |
| `harness/frozen/postcondition-bounds-v3.json` | `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84` |
| `harness/frozen/postcondition-latency-observations-v3.json` | `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155` |
| `harness/ci-w2-item5-freeze-provenance-v3.json` | `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152` |

Evidence logs (`shasum -a 256` + observed `Executed … 0 failures` / build / provenance lines):

- `a27-focused-v09-repairs-20260929T0707.log` → `ecfcb8def948753e69e5d9a0a2f35e06ab123c4b86df2e3be7e885ce78f22a4e` (matches bindings); line 200/202: `Executed 80 tests, with 0 failures (0 unexpected) in 3.304 (3.308) seconds` / `… (3.309) seconds`.
- `a28-full-suite-v09-repairs-20260929T0708.log` → `e789e2b37b5794d81adcf877b4036971b5e9f8befb1d5353c30d52a9bbef15c9` (matches bindings); line 520/522: `Executed 222 tests, with 0 failures (0 unexpected) in 4.851 (4.861) seconds`.
- `a29-build-v09-repairs-provenance-restore-20260929T0722.log` → `8e4deaf4f02dea1e713d0cf2a08e2e323621d4e2ce10ef7e9d81b87a427aa50c`; line 10 `Build complete! (5.06s)`.
- `a30-focused-v09-repairs-provenance-restore-20260929T0722.log` → `f98fa449fa5ea8911fdc378b96d7f47a88fd75740eaa2f3dab6adae6cd1ee0ac`; line 201/203: `Executed 80 tests, with 0 failures (0 unexpected) in 3.284 (3.288) seconds`; includes `AXWindowIdentitySelectorTests` (5 cases passed), `NativeObservationSessionTests`, `ComposedAdaptersTests`.
- `a31-full-suite-v09-repairs-provenance-restore-20260929T0723.log` → `02742ae768f9ba4440a94ec14279d2e3ab021effe430a951b258cd147af54484`; line 520/522: `Executed 222 tests, with 0 failures (0 unexpected) in 4.840 (4.850) seconds`.
- `a32-provenance-v09-repairs-provenance-restore-20260929T0726.log` → `3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a`; JSON: `"status": "PASS"`, `"generation": "v3"`, `"implementationSourceGitBlobSHA": "c411011b1b44b1efb614e000f526b2118f45d120"`, `"sampleCount": 20`, `"maxLatencyMs": 155.18903732299805`.
- `a27`/`a28` are the superseded first repair revision but are requested by the review brief and their hashes match the bindings' quoted values; the current-tree evidence is `a29`–`a32`.

## 2. Topic / scope

Perception & geometry surfaces of the repaired tree: AX identity binding to the exact target window (`AXWindowIdentitySelector`, `ProductionObservationSource.readAXIdentity`, `AXIdentityRead.isBoundToWindow`, `WindowIdentityValidator`); retained-frame geometry containment for `.saveAllMenuRows`; `FrameCaptureSupport.backingScaleFactor` / `resolvedBackingScale` single-display fail-closed; coordinate transforms; epoch/freshness; retained-PNG hash binding; observation-session concurrency. Repair claims `V09_AX_IDENTITY_WINDOW_UNBOUND`, `V09_MENU_BOUNDS_UNBOUND` and the calibration-harness frozen-AX-read entry are in scope; the transaction/timing claims (C4/C5/C6/C7, eligibility, goal slot, resume) belong to reviewer contexts 02/03 and were not adjudicated here.

## 3. Inputs inspected

- `bindings.json` (attempt-02), `plan.md` (§C3 lines 119–131, §C6 156–170, Phase A 244–258, verification 205–222), `handoff.md` (grep hits), `progress.md` lines 190–240.
- Product sources: `Identity/AXWindowIdentitySelector.swift`, `Identity/WindowIdentity.swift`, `Observation/NativeObservationSession.swift`, `Composition/ProductionObservationSource.swift`, `Sensor/FrameCapture.swift`, `Sensor/RunEpochAuthority.swift`, `Composition/LiveComposition.swift`, `Composition/ComposedNativeAdapter.swift`, `Composition/PhaseAEvidence.swift`, `Perception/StructuralLocators.swift`, `Geometry/Coordinates.swift`, `Actuation/QuartzActuator.swift`, `Transaction/StateEvidence.swift`, `rev28ctl/main.swift`, `rev28ctl/HarnessCalibration.swift`.
- Tests: `AXWindowIdentitySelectorTests.swift`, `NativeObservationSessionTests.swift`, `AdversarialMatrixTests.swift`, `StructuralLocatorsTests.swift`, `ComposedAdaptersTests.swift`, `LiveCompositionTests.swift`, `CoordinateTransformTests.swift` (read only; not executed here).
- Bound evidence logs `a27`–`a32` (and the existence, not adjudication, of `a33`–`a36` V-08 re-runs referenced in `progress.md:232`).

## 4. Checks performed (read-only)

1. Recomputed HEAD/tree state, plan/handoff hashes, implementation digest (44 files), all nine frozen hashes, the frozen `HarnessCalibration.swift` blob, and the six evidence log hashes with their key lines (section 1).
2. Traced the AX binding path end-to-end: selector decision logic, production call site, bundle-validation guard, validator cross-check, and the absence of production `windows[0]`/`.first` AX reads (only `HarnessCalibration.swift:2479` remains, harness-only).
3. Traced `.saveAllMenuRows` geometry: config → composition → adapter → session containment guard → locator structure/overlap/safe-rect refusals; verified the retained-frame pixel space used for containment.
4. Verified scale resolution: `backingScaleFactor(forWindowFrame:)` / `resolvedBackingScale` exactly-one-display rule, throw site, and `pointPixelScale == backingScaleFactor` invariant; checked the positive-size config validation.
5. Verified epoch issuance/refusal, bundle epoch/hash cross-fields, post-inventory identity revalidation, and `StateEvidence` stale-epoch refusal.
6. Verified session concurrency (actor + pre-await busy flag + refusal test) and the retained-PNG/OCR byte binding (single encode, hash equality, decode re-checks).
7. Verified the coordinate transforms and 1 pt safe-boundary margin (canonical transform funcs, capture-geometry rule evaluation, dispatch re-check) and the Phase A inventory AX match path.
8. Cross-checked the three in-scope claims against code and the bound test/provenance evidence, and looked for false refusals / widened acceptance / ambiguous-match acceptance introduced by the repairs.

## 5. In-scope repair claims — verification

| Claim | Result | Evidence |
|---|---|---|
| `V09_AX_IDENTITY_WINDOW_UNBOUND` | **VERIFIED** | `AXWindowIdentitySelector.swift:43–97`: exact `windowNumber` match preferred (`:66–77`), >1 exact match refuses (`:66–69`), frame fallback only when exactly one descriptor is within `frameTolerancePt = 0.5` (`:58`, `:78–90`), missing CG bounds / no unique match refuses (`:78–90`). `AXIdentityRead.matchMethod` defaults nil and `isBoundToWindow` = `matchMethod != nil` (`WindowIdentity.swift:61–82`). Production path uses the selector, not `windows[0]` (`ProductionObservationSource.swift:106–126`; `rg` shows the only AX `.first` left is harness-only `HarnessCalibration.swift:2479`). Session refuses unbound AX evidence (`NativeObservationSession.swift:233–243`) and re-checks identity against the post inventory at 0.5 pt + epoch (`:205–232`, `WindowIdentityValidator.validate` `WindowIdentity.swift:179–217`). Tests: `AXWindowIdentitySelectorTests.swift:19–98` (5 cases) and `NativeObservationSessionTests.swift:237–254` pass in `a30`/`a31` with 0 failures. |
| `V09_MENU_BOUNDS_UNBOUND` | **VERIFIED (as scoped)** | Containment guard: `.saveAllMenuRows` refuses `.unsafeGeometry` unless both bounds are inside the retained image (`NativeObservationSession.swift:502–509`; `imageBounds` from the decoded retained PNG `:403–406`). Locator also requires exact ordered 5-row reference, per-row intersection with `menuBounds`, ≥8 px addressable overlap, and safe rect inside `menuBounds` (`StructuralLocators.swift:241–298`). Single-display scale fail-closed: `FrameCaptureSupport.resolvedBackingScale` requires `displayCount == 1` and a known positive scale (`FrameCapture.swift:152–164`); capture throws `backingScaleUnresolved` (`:273–275`) and records invalid on `pointPixelScale != backingScaleFactor` (`:278–283`, `Coordinates.swift:309–321`). Config positive-size validation: `LiveComposition.swift:178–185`. Hash-binding is explicitly deferred to Phase A (`progress.md:226`, claim text in `bindings.json`; Phase A assumption/retained-frame condition `PhaseAEvidence.swift:774–795` with frame-SHA verification `:522–537`; plan Phase A requires actual five-row localization `plan.md:246`). Residual gap recorded as MINOR-1. |
| Calibration harness keeps the frozen AX read | **VERIFIED** | `HarnessCalibration.swift` is the frozen blob `c411011b…` (`git hash-object`; `git ls-tree 42ae9a3`); its `windows(ofApp:).first` (`:2479`) and `matchingAXWindow` ≤6 pt best-match (`:461–472`) are harness/calibration-only and are not on the production observation path; `a32` provenance is `status=PASS`, generation v3, with the same blob SHA; the digest `e80e4f0f…` includes those frozen bytes. |
| C4/C5/C6/C7, eligibility, goal slot, resume, chooser provenance | OUT OF SCOPE (reviewer contexts 02/03) | Not adjudicated here. |

## 6. Findings

### MAJOR

None found in this topic. No plan-conformance violation observed on the perception/geometry surfaces: C3's requirements for a bound AX read, same-frame Vision/retained bytes, independent scale, epoch discipline, and 1 pt boundary behaviour (`plan.md:123–130`) are implemented fail-closed, and ambiguity is refused rather than promoted (`plan.md:272`).

### MINOR

- **MINOR-1 (residual, contract-deferred; not a current plan violation): locator bounds are still not machine-bound.** `menuBoundsCapture`/`addressableBoundsCapture` are read from operator config (`rev28ctl/main.swift:79–80`, passed at `:232–233`) and validated only for positive size (`LiveComposition.swift:178–185`); the runtime guard checks only that they are inside the retained image (`NativeObservationSession.swift:507–509`). A wrong-but-in-frame bounds pair could still yield a candidate if the exact five ordered OCR rows happen to intersect it — the acceptance is bounded, not fully closed, by the ordered 5-row identity + row/menu intersection + ≥8 px addressable overlap + safe-rect containment (`StructuralLocators.swift:249–263, 269–275, 288–290`). The frozen set contains no real LINE menu bounds, and the repair explicitly documents hash-binding of these values as a Phase A obligation (`progress.md:226`; `PhaseAEvidence.swift:774–795` checks only candidate/nonzero-bounds/retained-frame; plan `plan.md:246` requires Phase A to record the actual five-row localization, `plan.md:214` forbids silently changing frozen bounds). No new defect introduced by the repair; it converts the earlier unbounded acceptance into a bounded, fail-closed one and records the open obligation.

### INFO

- **INFO-1 — announced HEAD drifted by `.agent`-only commits.** Announced pre-check `HEAD == 0ce9e05…`; observed `7cd444e152daede802e21430f1501e17ddfd3784` (`0ce9e05` is an ancestor; `96ef88c`, `7cd444e` follow). `git diff --name-only 42ae9a3 HEAD` contains only `.agent/` paths and `git diff --stat 42ae9a3 -- rev28` is empty, so the bound product tree holds; all bound hashes match. Recorded for traceability, not a product finding.
- **INFO-2 — Phase A inventory AX match is weaker than production.** `main.swift:296–303` records `axFrameMatchesTarget` via `contains` with a 4 pt tolerance, whereas production requires a unique match at 0.5 pt (`AXWindowIdentitySelector.swift:58, 88–90`). This is an evidence-only pre-check; the fail-closed Phase A gate uses artifact-level `retainedFrameVerified` (`PhaseAEvidence.swift:785`) and runtime dispatch still uses the strict path.
- **INFO-3 — frame fallback does not exclude a descriptor whose non-nil `windowNumber` differs from the target.** `AXWindowIdentitySelector.swift:81–87` filters only by frame when no descriptor carries the target number; if exactly one other-numbered element frame-matched within 0.5 pt it would bind via `.frameGeometry`. Requires an unusual coincidence (two AX windows within 0.5 pt), and the unique-match rule already refuses the common ambiguous case; optional hardening would exclude descriptors with a present, different window number from the fallback set.
- **INFO-4 — CG inventory is read twice per capture.** `ProductionObservationSource.readAXIdentity` looks up the target CG entry internally (`:107`) and the session looks it up again for the identity record (`NativeObservationSession.swift:373–377`); both must name the target at the same epoch, so this is redundancy, not epoch mixing.
- **INFO-5 — no direct session-level test observed for the `.saveAllMenuRows` out-of-frame refusal branch.** `NativeObservationSession.swift:507` is exercised indirectly through the adapter path (`ComposedNativeAdapter.swift:188–192`, `ComposedAdaptersTests.swift:88–106`) and the locator-level refusals are tested (`AdversarialMatrixTests.swift:464–473`, `StructuralLocatorsTests.swift:117–155`); no test constructing `.saveAllMenuRows` with out-of-frame bounds through `session.capture` was found. Fail-closed code path, coverage observation only.
- **INFO-6 — retained-PNG hash binding relies on byte-deterministic encoding.** The record hash is produced by `FrameCaptureSupport.pngSHA256` (`FrameCapture.swift:315`) and the session re-encodes with `pngData` and requires equality (`NativeObservationSession.swift:341–347`); a nondeterministic encoder would refuse rather than silently diverge, and `validated()` re-checks bytes hash + decode dimensions (`:193–204`). Fail-closed as designed.

## 7. Verdict

All three in-scope repair claims are VERIFIED; the frozen-AX-read entry is intentional and provenance-clean; no new MAJOR or behaviour-widening defect was found in perception/geometry. One MINOR residual (MINOR-1) remains as an explicitly tracked Phase A obligation.

verdict: ISSUES_FOUND
