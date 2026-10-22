# Rev28 Native Closed-Loop Architecture

Status (2026-10-04): fresh identity repair under `harness-development/rev28-fresh-repair/TASK-d34338d2680f4814aabd6841ef094c14`. This document describes the current implementation; new check and independent-review results are recorded in that task. Existing work and historical evidence are preserved. The LINE production backup has not completed.

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

The observation session reads the target process instance, signing identity and
bound AX identity before capture and again after capture/OCR. A change or read
error refuses the bundle; its post-read fields are checked again by
`ObservationBundle.validated()`. Unavailable signing information remains unknown.
The first process-instance read precedes initial SCK enumeration; the final
read follows post-capture SCK, signing, AX and explicit CG acquisition. These
actual process values bracket all retained native facts, including replacement
inside an inventory or identity read.
`ProcessCodeIdentity` reads the requested PID's code only and never substitutes
the calling executable's signature for an unavailable target.

The session explicitly reads one post-capture CG inventory and shares it between
its `WindowIdentity` and retained bundle. SCK pre/post and CG target entries must
be unique, ownership-consistent and have finite positive frames agreeing within
the existing 0.5-point tolerance. Duplicate IDs and invalid or inconsistent
geometry refuse capture without incrementing the completed-capture count.
All post-identity reads and final validation remain inside the original deadline.
This is temporal cross-checking, not atomic acquisition of OS facts: the native
AX matching adapter also reads its own CG provider.

## 2. Coordinate model

Coordinates are typed as separate spaces. Transform code is centralized; callers do not hand-convert ad hoc coordinates.

Click candidates must be inside a validated safe interior. Scale is cross-checked independently. A missing validated capture rule fails closed.

Per-side size residuals are checked by absolute magnitude, so undersized frames
fail just like oversized frames. For a configured `sourceRect`, the capture
bbox records both the crop's nonzero offset and extent; transforms use that
recorded cropped bbox.

No historical screen coordinate is accepted as production input.

An invalid-frame refusal retains the original violations plus
`recordedFrameGeometry`: pixel width/height, expected width/height in points,
point-pixel scale and independent backing scale already present in the record.
These numbers are labeled as recorded fields because rejection precedes PNG
verification. They do not validate the image, locate clipping edges, explain
the renderer's behavior, or authorize another capture. No window positions,
identifiers, titles or pixels are added to the refusal.

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

`StructuralCandidate` is bound to a `SurfaceBinding(bundleID, ProcessInstanceID, windowID, captureEpoch, frameSHA256)`. Reuse after a process restart/PID reuse, window change, new epoch, or frame change is rejected.

### Album card/detail

Album selection requires the current exact group plus a unique exact date title and exact count contained in one explicitly segmented, uniquely identified card region; cross-card pairings and multiple matching regions are rejected. Album detail and subsequent ellipsis/menu/Save All surfaces require unique exact group title, `2024/05/13~05/17` and `57張照片` on their own frames.

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

The menu locator requires the complete five-row reference structure in order. Its safe click rectangle is the intersection of the target row and the current addressable menu region, additionally constrained by neighboring row geometry:

1. 選擇項目
2. 修改相簿名稱
3. 儲存全部
4. 刪除相簿
5. 分享相簿

The target must be unique. Click geometry comes from the structural target-row cell and its neighboring rows, not from OCR character boxes.

## 5. Final dispatch gate

Immediately before an event can be posted, `DispatchReadinessGate` requires all of:

- application active,
- target frontmost,
- window/process identity fresh,
- candidate frame/epoch fresh,
- geometry safe.

Failure of any clause refuses dispatch.

Production readiness projects the retained `NativeObservationSession` bundle,
including its original capture timestamp and frozen geometry. After hover the
same session captures and localizes again with a greater epoch; identical pixels
do not authorize reuse of the old candidate. A redraw can pass only when the
fresh target has the same identity and the original click point still meets the
one-point safe margin, with mapping/frame changes within 0.5 point. Readiness
frames are retained separately from state transitions. The original one-second
permit expires even if capture, OCR, durable writes or final guards take time.
Ledger or anchor write failure prevents mouseDown/mouseUp; its error propagates.
Each dispatch binds its revalidation records to the exact durable reservation
entry returned under the owner lock. Its final failure supersedes its own
provisional success, so a late refusal cannot clear an earlier failed attempt.
Distinct successful attempts still reset the consecutive-failure counter;
legacy standalone records keep their existing meaning.

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

### V-09 durable enforcement

`PersistentTransactionOwner` binds one verified ledger to immutable run, goal,
group, album, plan/source digests and staging paths. It derives action budgets
from durable intent/attempt entries. An intent itself consumes the operation;
a restarted owner cannot post after a saved-but-unresolved intent. Chooser
confirmation requires a bound affirmative postcondition record and persists the
selected action before it is attempted. `IntentLedger` serializes writers with
an OS advisory lock, reloads and verifies the complete chain under that lock,
rejects stale snapshots and fsyncs every append. Its separately stored
`LedgerHeadAnchor` detects subsequent truncation/rollback when retained
independently.

Verified pre-intent continuation re-observes the current state before advancing,
including when it already reached `SAVE_ALL_LOCATED`. It appends a reobservation
record without rewriting old transitions or resetting budgets. The stable goal
slot also binds its run and authorization: changing runID is not a recovery
mechanism. Source changes require new review and a separately reviewed authority
decision; this repair never rebinds the historical slot or ledger.

Production event posting is exposed only by `GatedQuartzActuator`; its permit
can be minted only from a fresh active/frontmost SC+CG window census and a
candidate bound to the live screenshot digest. Permits are single-use,
short-lived and recheck focus/window, bundle and process start instance
immediately before posting; the live binding supplied to the boundary must
still equal the permit's complete candidate binding. Synthetic raw
Quartz and chooser compatibility is target-local to `rev28ctl` for the
byte-frozen calibration harness; it is not exported by `Rev28Core`.

`StrictPostconditionMonitor` is the production monitor. It bounds every sample
by the unchanged plan-time deadline, schedules from sample start, treats sampler
errors and aborting tripwire outcomes as terminal, and carries tripwire
observations in every verdict. The old `PostconditionMonitor.run` remains for
synthetic harness compatibility only. Empirical `PRE_SIDE_EFFECT_OBSERVED`
requires an affirmative outcome and rehashed postcondition/tripwire artifacts
beneath the same run-ID directory; the legacy unbound-boolean helper can only
return indeterminate.

`LiveCompositionFactory` assembles the native session, common engine, adapter,
actuation and post-save observers used by both CLI commands. `live-preflight`
verifies immutable authorization/source bindings and fresh process/window/TCC
facts. It may perform guarded reversible album/menu navigation, but never Save
All or destination confirmation and never consumes the irreversible entitlement
or one-shot execute authorization. It publishes Phase A evidence and exits 77
with `preflight=blocked` if any required condition is FAIL or UNKNOWN.

Phase A report v2 uses the common exact state-evidence policy. Configured bounds
and retained pixels alone cannot prove current native calibration or popup
ownership/absence of occlusion; these remain UNKNOWN until independently bound
observations exist. The current builder deliberately cannot manufacture their
PASS from caller flags. `live-execute` requires independently recomputed Phase B
eligibility before irreversible authority can be consumed. Actual chooser
observation remains a separate runtime gate.

### Real-session-only residual evidence

CI cannot establish that the installed LINE build presents the reviewed
album/menu structure, that native chooser AX semantics match the append-only
predicate version, or that the real filesystem tripwire observes every
relevant write. Those facts require a live authorized macOS session with LINE,
Accessibility and Screen Recording permissions, calibrated capture rules, and
preserved evidence. Historical calibration and offline provider tests do not
prove these current-session obligations; production eligibility remains blocked.

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
- no hidden or visible extra files, subdirectories, symlinks or other directory entries,
- no partial suffixes,
- no zero-byte files,
- every file structurally decodable,
- exactly 17,924,900 total bytes,
- directory-entry set and file sizes/mtimes stable for >=3 samples spanning >=4 seconds,
- >=5 seconds quiescence after last modification,
- sorted filename-excluded content SHA-256 multiset digest exactly
  `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`.

A second, name-inclusive baseline tripwire must remain
`b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`.

## 10. Offline replay and adversarial hardening

`rev28/Tools/replay_rev28.py` binds the 20 plan-selected historical fixtures to full reviewed SHA-256 values, then invokes `rev28replay` to run current Save All and strict album-card locator logic on recorded OCR observations and reviewed geometry. It also runs the current pixel detector on the historical image fixture. Any production-locator disagreement fails replay. CI runs it twice and requires byte-identical output.

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

Historical hosted macOS 27 evidence returned Vision `unknownError` for **both** Swift `RecognizeTextRequest` and legacy `VNRecognizeTextRequest`. Both API generations failed while the real Mac's earlier executable-context Vision probe passed, so that recorded failure was classified as an environment limitation. This repair did not reprobe either live capability or weaken the production OCR rule.

Only the user's real Mac can establish actual LINE app/session state, current LINE UI geometry/labels, real chooser hosting, real download side effects, baseline/staging disk state and final content equality.

## 12. Production boundary

Synthetic/CI evidence can advance implementation and pre-live verification, but never the primary outcome.

The remaining production sequence is:

1. real-Mac preflight and baseline/staging/TCC re-verification,
2. Phase A observation plus guarded reversible navigation, with zero irreversible intent,
3. required exact-SHA pre-live review gates,
4. one bounded Phase B production transaction,
5. filesystem/content proof,
6. independent Stage-05 recomputation from disk.

Until those complete, `PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`.

## Passive native diagnostic packet

`rev28ctl capture-diagnostic --project-root <absolute-project-root> --output <existing-empty-project-root/harness-development/native-diagnostics/directory> --rulebook <regular-project-file> --bundle-id jp.naver.line.mac --pid <fresh-LINE-pid>` provides one passive native observation. The executable must reside inside the explicit project root so its actual bytes can be retained in provenance. The caller prepares the empty output directory. Absolute paths reject traversal and symlink components; an exclusive claim prevents reuse, and partial output remains on failure. Missing arguments exit 64; observation or publication refusal exits 77.

The command binds the fresh PID to LINE, checks existing AX/screen-capture permission without requesting it, measures window settling with two fresh SCK samples and activation with `NSRunningApplication.isActive`, then uses `ProductionObservationSource`, `NativeObservationSession`, and `VisionOcrEngine`. Capture defaults to `primaryWindow`; optional `--capture-profile childUnion` explicitly selects the existing child-window capture path. State is `appReady`, localization is `none`. It constructs no transaction owner, input actuator, goal slot, or backup-state writer and does not activate an application.

The packet retains `claim.json`, `observation.png`, the full raw bundle projection in `observation.json`, actual `rulebook.json` bytes, source/executable file hashes in `provenance.json`, and a manifest. Files use exclusive no-follow creation, sync, and readback. `PassiveNativeDiagnostic.load(directory:expectedManifestSHA256:)` requires an external manifest SHA256 from the original receipt or independent review; omission or mismatch refuses. It checks every retained file and reconstructs the existing bundle validator using the actual PNG, then independently recomputes configuration, included-window, geometry-rule and scale consistency. The manifest is not signed; provenance hashes do not establish OS code attestation.

Success means `OBSERVED_VALID_BUNDLE`. Calibration, occlusion, current composer, and Phase B permission remain `UNKNOWN`. CG inventory is one post-capture census and does not establish atomic acquisition, bracketing occlusion, popup ownership or topmost status. This diagnostic packet issues no production permit, resets no transaction budget, and does not satisfy the missing full native backup acceptance gates.

Passive observer construction uses the output's pinned directory descriptor and a separate existing-directory-only `RunEpochAuthority` mode. This mode owns its descriptor, derives epoch floors directly from retained directory entries, and never resolves a URL or creates a directory. Path identity is checked before and after construction; deletion or symlink/ancestor replacement refuses without recreating output or redirecting creation. Existing live callers retain their original URL initializer semantics. Diagnostic source construction and collection are each single use.

Primary-window packets retain format version 1. Child-union packets use version 2 in both record and manifest; loading rejects a disagreement or a version/profile mismatch. The child profile requires at least one affirmative on-screen child snapshot from the same LINE process, intersecting the unique main window. The complete selected main/child snapshots must agree between both settling samples and the session's pre/post inventories and included-window set. Duplicate IDs, missing or changed children, unsupported configurations, or geometry that cannot be recomputed from their union refuse before successful publication. Validation uses the retained PNG and the original bundle validator. No automatic profile fallback occurs.

These snapshot checks bound diagnostic collection; they do not prove AX parentage, popup ownership, topmost status, or lack of occlusion. All four certifications remain `UNKNOWN`. The live engine and its production permission gates are unchanged; accepting or collecting a child-union packet does not authorize backup execution.

The settling samples report a non-unique main-window count through `targetWindowNotUnique(found:)`, distinguishing zero candidates from multiple candidates in future refusals. Selection predicates and short-circuit order remain unchanged. A count does not choose a window, permit a retry, or reconstruct counts missing from historical records.
# Explicit LINE diagnostic packet v3

`explicitLineWindows` is an opt-in, diagnostic-only profile. Logical selection is
the exact fresh LINE main plus intersecting on-screen same-process candidate
children; it is independent of the SDK's `includeChildWindows=false` flag. The
source resolves every selected native handle and refuses set/owner/frame/layer
drift. One `SCContentFilter(display:including:)` contains those handles only;
menu bar, implicit children, shadows and cursor are disabled, clipping remains
enabled, and the effective source rectangle is the complete selected union.
The first implementation supports one containing display at origin `(0,0)`
with matching point dimensions and independently known NSScreen backing scale.
Crossing/mirrored/nonzero-origin/unknown-scale selections refuse before screenshot.

`ExplicitLineRequestBinding` retains the original crop-free request, geometry
state, settled selected snapshots and the existing frozen rulebook input.
`ExplicitLineSelectionWitness` retains selected IDs, display facts, actual crop,
filter bounds/scale and effective child/menu-bar flags. The same pure validator
checks original request versus retained effective facts, exact settling/pre/post
sets and numeric geometry inside `ObservationBundle.validated()` before return
and `completedCaptures` increment, and again at strict retained reconstruction.
The final session deadline includes this validation. Source downgrade cannot
discard the original request. The rulebook requires an `explicitLineWindows-v3-`
ID, affirmative settling, and the existing 1-point-or-stricter bounds; the prefix
is profile binding, not actual calibration certification.

Passive packet/manifest v3 retains this binding and requires an external manifest
anchor. V1/v2 keep their existing defaults, wire and flags, read absent optional
fields, and reject v3 witness/request fields. `LiveCompositionFactory.validate`
rejects the new kind before constructing any owner, session or adapter.
Synthetic session/packet tests and valid witnesses do not certify native pixels,
popup ownership, occlusion, current composer, Phase B or end-to-end backup.
Current work authorizes local implementation and offline checks only; any real
LINE image/full supporting inventories still require a separate explicit grant.

### Project authority inspection (read-only foundation)

`project-preflight` reads only an explicitly selected project's canonical config, accepted
RC2 state, bound registry evidence, producer source bytes and proposed directory entries.
It performs two stable reads with file identity checks. This is a snapshot, not a writer
lease or an atomic transaction across files. Terminal current run pointers do not imply
active ownership; verified fingerprints remain skip barriers across destinations. Unverified
historical intents remain blocked even when a record claims release.

`ProjectBackupBinding.inspect` accepts the original request, raw config/state, actual stdout
and its external SHA256, and the complete ordered producer source material. It validates
strict JSON, exact report keys, source byte aggregates and recomputed authority/history
facts. Its only output is `ProjectBackupInspectionBinding`, whose `canDispatch` is always
false. Destination inspection remains a reported observation, not a reservation. Source
binding is not OS code attestation. Every later runtime must read fresh authority again
at a shared writer boundary; config identity does not prove the current native LINE group.

Shared writer/native intent commit ordering, dynamic target continuity, content acceptance,
Phase A/B readiness and production authorization remain separate future work. No current
production guard, immutable authorization, owner, ledger or GoalSlot is changed here.
