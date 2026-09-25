# Rev28 Native Closed-Loop Architecture

Status: pre-live implementation/hardening branch. This document describes the reviewed Rev28 architecture; it does **not** claim the LINE production backup has completed.

## Goal

Back up the LINE album `旻謙允禎成長日記 / 2024/05/13～05/17 / 57` using a macOS-native feedback loop and prove the resulting files are content-identical to the accepted baseline.

Success is not a click, a menu change, a chooser, or a file count. Success requires:

1. fresh identity and geometry for the intended LINE surface,
2. reviewed structural localization,
3. exactly-once irreversible dispatches,
4. direct chooser/postcondition observation,
5. exactly one destination confirmation,
6. stable, decodable staging content,
7. exact content-multiset equality with the accepted baseline,
8. unchanged baseline evidence.

## Trust model

Rev28 does not infer success from opaque LINE internals. The control loop is:

```
ScreenCaptureKit sense
  -> process/window identity binding
  -> Apple Vision text identity
  -> structural geometry
  -> fresh candidate + epoch/frame binding
  -> final dispatch-readiness gate
  -> Quartz actuation
  -> direct ScreenCaptureKit/AX/CG postcondition observation
  -> chooser AX confirmation
  -> filesystem stability/content verification
  -> durable ledger state
```

Every irreversible action is fail-closed. Unknown outcome means observe/reconcile, never blind retry.

## 1. Sensor and identity boundary

`WindowSensor` captures the intended surface with explicit ScreenCaptureKit configuration. A geometry-bearing frame records its window identity, capture epoch, capture image SHA-256 and scale information.

`WindowIdentity` binds:

- bundle identifier,
- process instance, not PID alone,
- window ID,
- window frame,
- capture epoch,
- capture image SHA-256.

A changed process instance, stale window ID, stale epoch, unexpected layer/offscreen state or unexplained frame delta invalidates the observation.

## 2. Coordinate model

Coordinates are typed as separate spaces. Transform code is centralized; callers do not hand-convert ad hoc coordinates.

Click candidates must be inside a validated safe interior. Scale is cross-checked independently. A missing validated capture rule fails closed.

No historical screen coordinate is accepted as production input.

## 3. OCR is identity, not click geometry

The production OCR path is Swift Vision `RecognizeTextRequest` with:

- `.accurate`,
- `zh-Hant` + `en-US`,
- language correction disabled.

Exact text identifies surfaces such as:

- `旻謙允禎成長日記`,
- `2024/05/13~05/17`,
- `57張照片`,
- `儲存全部`.

Distinct glyphs such as `禎` and `楨` are never fuzzy-merged.

`LegacyVisionOcrParityEngine` exists only as a diagnostic parity backend. It is never production click authority.

## 4. Structural locators

`StructuralCandidate` is bound to a `SurfaceBinding(windowID, captureEpoch, frameSHA256)`. Reuse after a new epoch/frame is rejected.

### Album card/detail

Album selection requires a unique exact date title and associated count in the same card. Album detail requires unique exact group title + `57張照片`.

### Album ellipsis

`AlbumEllipsisLocator` ports the reviewed v5 invariant into Swift:

- compact connected components from flat image rows,
- exactly one vertical three-dot pattern,
- consecutive dot spacing 3...10 capture pixels,
- x alignment within 3 pixels,
- total span <=24 pixels,
- text-overlapping triples refused,
- group-title and album-title-strip triples refused,
- candidate must be in the bounded album header region derived from the current title bbox.

The historical proven shape `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]` is a replay expectation, never a live coordinate input.

### Save All

The menu locator requires the complete five-row reference structure in order:

1. 選擇項目
2. 修改相簿名稱
3. 儲存全部
4. 刪除相簿
5. 分享相簿

The target must be unique. Click geometry comes from the structural target-row cell and its neighboring rows, not from OCR character boxes.

## 5. Final dispatch gate

Immediately before an event can be posted, `DispatchReadinessEvaluator` requires all of:

- application active,
- target frontmost,
- window/process identity fresh,
- candidate frame/epoch fresh,
- geometry safe.

Failure of any clause refuses dispatch.

Quartz actuation remains separated from sensing. A posted event never serves as its own success acknowledgement.

## 6. Save All postcondition

The postcondition monitor uses a monotonic deadline.

A critical hardening fix in this branch closes a subtle race: a ScreenCaptureKit/AX sample may start before the hard cap but return after it. The monitor now evaluates elapsed time **after** the sample returns; an affirmation that arrives after the hard cap is named `CHOOSER_OBSERVED_AFTER_WINDOW`, never `CHOOSER_VERIFIED`.

Reviewed result classes:

- inside bounded window -> `CHOOSER_VERIFIED`,
- first affirmative after hard cap -> `CHOOSER_OBSERVED_AFTER_WINDOW`,
- no affirmative -> `NO_CHOOSER_OBSERVED`.

No result authorizes a second Save All dispatch.

## 7. Chooser identity and confirmation

A chooser must satisfy the frozen native-panel predicate across ScreenCaptureKit, CG inventory and AX evidence. Ownership is process-instance aware and PID reuse is refused.

Destination navigation verifies the reflected path. Exactly one confirmation mechanism is selected:

- AXPress on the unambiguous default button, or
- reviewed Return-key fallback.

The two are never both attempted for one confirmation.

## 8. Persistent transaction policy

`ExecutionStateMachine` only permits the reviewed next-state transition.

`LiveDispatchBudget` enforces:

- <=12 reversible dispatches globally,
- <=3 recoveries per identical blocker,
- abort after two consecutive revalidation failures,
- exactly one Save All dispatch,
- exactly one destination confirmation.

`IntentLedger` is append-only and hash chained. After a crash following an irreversible dispatch, restart is observe-only unless a fresh reviewed decision explicitly arms a new future action.

`SaveAllEmpiricalClassRecord` records whether evidence from this run could support a future `PRE_SIDE_EFFECT_ACTION` classification. This does not relax the current run: current Save All remains irreversible/exactly-once.

## 9. Filesystem acceptance

`StagingVerifier` names failure states rather than collapsing them:

- `STAGING_INCOMPLETE`,
- `STAGING_EXTRA_FILES`,
- `STAGING_DUPLICATE_CONTENT`,
- `STAGING_UNSTABLE`,
- `CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE`,
- `DUPLICATE_CONTENT_CONFIRMED`.

The production predicate is:

- exactly 57 files,
- no subdirectories,
- no partial suffixes,
- no zero-byte files,
- every file structurally decodable,
- exactly 17,924,900 total bytes,
- sizes/mtimes stable for >=3 samples spanning >=4 seconds,
- >=5 seconds quiescence after last modification,
- sorted filename-excluded content SHA-256 multiset digest exactly
  `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`.

A second, name-inclusive baseline tripwire must remain
`b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`.

## 10. Offline replay and adversarial hardening

`rev28/Tools/replay_rev28.py` binds the 20 plan-selected historical fixtures to reviewed SHA-256 prefixes and replays semantic invariants. CI runs it twice and requires byte-identical output.

The named G01-G22 + X01-X03 suite covers stale identity, wrong app/window, scale mismatch, occlusion/focus theft, stale candidate, wrong/duplicate OCR, popup/menu ambiguity, timeout, fake chooser, filesystem anomalies, extra/partial/zero files, crash-resume and inactive dispatch. CI executes the full matrix twice.

## 11. CI versus real-Mac authority

GitHub-hosted `xcode-27` is a pre-live proving environment, not production authority.

It can verify:

- Swift 6.4 build and deterministic contracts,
- ScreenCaptureKit availability,
- Accessibility and post-event permissions,
- native NSOpenPanel/AX postcondition timing,
- replay,
- state machine/ledger/verifier,
- adversarial behavior.

The hosted macOS 27 environment currently returns Vision `unknownError` for **both** Swift `RecognizeTextRequest` and legacy `VNRecognizeTextRequest`. Because both API generations fail while the real Mac's earlier executable-context Vision probe passed, hosted Vision is classified as an environment limitation; no production OCR rule is weakened.

Only the user's real Mac can establish actual LINE app/session state, current LINE UI geometry/labels, real chooser hosting, real download side effects, baseline/staging disk state and final content equality.

## 12. Production boundary

Synthetic/CI evidence can advance implementation and pre-live verification, but never the primary outcome.

The remaining production sequence is:

1. real-Mac preflight and baseline/staging/TCC re-verification,
2. Phase A read-only LINE reconnaissance,
3. required exact-SHA pre-live review gates,
4. one bounded Phase B production transaction,
5. filesystem/content proof,
6. independent Stage-05 recomputation from disk.

Until those complete, `PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`.
