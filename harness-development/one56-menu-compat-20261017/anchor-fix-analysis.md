# Anchor-dispersion failure: source audit and bounded Plan proposal

Date: 2026-10-18. This is a read-only analysis artifact for external Plan Review. No product source, tests, grant, ledger, or task acceptance criteria were changed by this analysis.

Plan revision: `ANCHOR-DETAIL-R1-20261018`. Status: `PROPOSED_PENDING_OWNER_TRANSFER_TO_EXTERNAL_PLAN_REVIEWER`; no `APPROVE_PLAN` has been received. Baseline is exact HEAD91c85617 with product source7debc2. The proposed registration method is not yet implemented or proven; the external reviewer may reject this proposal or require a more specific bounded method before any production source GO. `GOAL_CRITICALITY=CRITICAL`; `EVIDENCE_ROLE=REAL_FRAME_REPLAY_AND_READONLY_GUI_OBSERVATION`; `CLOSURE_GATE=EXTERNAL_PLAN_APPROVAL_THEN_EXACT_SOURCE_REVIEW_AND_REAL_TRANSACTION_ACCEPTANCE`.

## Finding

The first unmet gate is `ANCHOR_DISPERSION`. The native geometry already supplies the affine CUA-to-SCK mapping; OCR does not estimate that transform. `AutomaticOcrAnchorMapper.derive` uses exact-text OCR-center pairs as a cross-check, and currently uses their count, spread, and residual as the acceptance proof. Those OCR centers are a poor geometric witness for this detail-grid crop.

The real `71-vs-73` replay shows both the concrete false correspondence and why the first refusal is misleading. CUA has seven OCR items; the full SCK display has 35. Global exact-text matching accepts four anchors, including an `album-date` match from the background album list: CUA center `(221.127, 196.919)` is paired with SCK center `(185.054, 1243.219)`, a 1215.032 px residual. The crop and the detail header differ in the date separator, so the correct detail header is not an exact match. Despite this gross mismatch, the largest-triangle ratio is only 0.0127273, below the 0.02 gate, and Swift returns `anchorsNotDispersed` before it evaluates the residual. Thus this result is not merely “text is concentrated”: an exact global-text collision selects the wrong window content, while the correct detail text is omitted.

Restricting the comparison to the actual native detail-window ROI removes that background-list match. Exact matching then leaves three tightly clustered anchors (area ratio 0.00007364), with the short uncertain OCR item at 2.944 px residual. Normalizing the two date separators recovers the correct header and raises the area ratio only to 0.0127273; its measured center residual is 2.676 px, and the uncertain short item remains at 2.944 px. Both exceed the existing 2 px residual limit, and the distribution remains below 0.02. ROI filtering, separator normalization, dropping the noisy anchor, or lowering the dispersion threshold therefore cannot establish a valid pass from these frames.

The separate `66-vs-68` replay has the same relevant outcome: exact and ROI-exact sets each contain only the three clustered anchors; separator normalization yields four anchors, 0.0127273 area ratio, and maximum residual 2.944 px (the corrected header alone is 2.676 px). Production derivation refuses `anchorsNotDispersed`.

Historical geometry for these captures is CUA `654×1286`, SCK full display `2294×1490`, and the authenticated detail ROI at SCK `(716,92,654,1286)`; native geometry maps at scale `(1,1)`, offset `(716,92)`. These values describe the retained evidence only and are not runtime constants or click coordinates.

## Reusable source audit

The following existing code is relevant, but none is a reusable cross-image pixel-registration/landmark implementation:

| Existing symbol | Path | What it actually proves |
|---|---|---|
| `AutomaticOcrAnchorMapper.derive` | `rev28/Sources/Rev28Core/Perception/OcrEngine.swift` | Derives scale/offset from native window/display bounds, then validates using unique exact-text OCR centers, their triangle area, and residual. It is the current failing check, not an independent pixel witness. |
| `VisualDiagnosticCommand.analyze` | `rev28/Sources/rev28ctl/VisualDiagnostic.swift` | Calls the same OCR-anchor mapper; it does not independently register image content. |
| `AlbumSupportMapping`, `AlbumSupportEvaluation.measureCapture`, `AlbumSupportEvaluation.guardPoint` | `rev28/Sources/Rev28Core/Perception/OcrEngine.swift` | Maps an OCR row using native geometry and verifies the actual Save All point lies within the unique row with margin `uncertainty + 4`; preserves the 16 px minimum intersection. This is the target-row guard and must remain. It does not independently prove the CUA/SCK frame transform. |
| `NonMenuFrameSupportEvaluation.measure` | `rev28/Sources/Rev28Core/Perception/OcrEngine.swift` | Enforces the existing uncertainty and surface-margin rules, but does not measure pixel alignment. |
| `EllipsisPixelDetector` / `AlbumEllipsisLocator` | `rev28/Sources/Rev28Core/Perception/AlbumEllipsisLocator.swift` | Detects the three-dot visual feature in one frame. It has no paired-frame correspondence or transform validation. |
| `HarnessCalibration` pixel/screen round trip | `rev28/Sources/rev28ctl/HarnessCalibration.swift` | Checks conversion reversibility inside a calibration geometry; it does not compare a hosted CUA frame with an SCK crop. |
| `verifyScrollMovement`, `compareRetainedViewport`, `compareRetainedViewportProbe` | `scripts/line_backup_cua_adapter.mjs` | Establishes visual change/movement between observations, not coordinate registration or a measured point residual. |

Repository searches for image registration, feature matching, template matching, cross-correlation, or reusable paired-image landmarks found no existing implementation in `rev28/Sources` or `rev28/Tests`. The current supported proof is native geometry plus OCR-center parity. No existing pixel symbol can honestly be reused to certify the actual point transform.

The formal menu row guards are already appropriately point-specific: `AlbumSupportEvaluation.measureCapture` and `guardPoint` require one exact `儲存全部` OCR row and keep the candidate point at least `uncertainty + 4` inside it; the interactive intersection must remain at least `16×16`. They should not be weakened to compensate for uncertain frame alignment. The current flow is `rev28ctl frame-support` in `rev28/Sources/rev28ctl/main.swift`, then `_support` in `src/line_backup_batch/observations.py`; the Python authority independently recomputes native geometry and the global OCR anchor count, 0.02 area ratio, and 2 px residual.

## Minimum bounded Plan for external review

**Decision requested from the external Plan Reviewer:** authorize or reject a new, purpose- and surface-bound pixel-alignment proof for the actual `ALBUM_DETAIL` CUA crop against the crop of the same authenticated native detail window from the retained full-display SCK image. This changes the geometry-evidence contract and must not be treated as an already approved implementation detail.

If approved, the smallest honest production change is a narrow registration proof, not a relaxed OCR gate:

1. Keep native PID/window/display identity, fresh CUA/SCK pairing, native-bounds affine scale/offset, capture-size/bounds checks, and all existing menu row/click guards.
2. On `ALBUM_DETAIL` only, use the native window bounds to extract the corresponding SCK ROI and compare actual image content from that ROI with the CUA crop. Emit a typed, hash-bound proof of the measured alignment and its uncertainty. The proof must be computed from the retained images, bind both frame hashes plus PID/window/display and ROI geometry, and refuse on ambiguous/low-information matching, wrong ROI, or a measured residual above 2 px. It must not accept caller-supplied points or infer corners from native bounds.
3. Keep OCR for album date, photo count, unique Save All label, and other semantic checks. OCR bbox centers may remain diagnostic, but may not be silently selected or discarded to manufacture geometric PASS. For `ALBUM_DETAIL`, only the typed pixel proof can replace OCR-center dispersion/residual as the geometric witness. All other surfaces retain the current `AutomaticOcrAnchorMapper` behavior unchanged.
4. Feed the measured uncertainty into the existing `uncertainty >= 2`, safe-margin `>= uncertainty + 4`, and minimum `16×16` intersection checks. Preserve `AlbumSupportEvaluation.measureCapture` and `guardPoint` unchanged. A pixel match that cannot demonstrate the same target-point alignment within 2 px refuses; it does not cause a threshold reduction.
5. Keep the proof isolated to this `ALBUM_DETAIL` support observation. The proof itself is not an ordinary-intent `CLEAR` frame and cannot authorize a click on its own. A complete fresh detail observation still has to pass all existing semantic, native-lineage, occlusion, frame and authority checks before it can be CLEAR. Existing at-most-once Save All, chooser, owner, intent, hash, and transaction checks remain untouched.

The evidence does not yet identify a proven registration algorithm or show a positive real-frame match with ≤2 px error. Therefore the acceptance contract must explicitly require a reproducible positive test on a genuine retained CUA/SCK detail pair, plus a genuine or controlled negative pair with an intentionally displaced ROI that refuses. Replaying older real frames proves only the image-matching property; it cannot meet a current capture/authority/freshness gate. The formal trial must obtain its own genuine ≤5-second CUA/SCK pair through the supported producer after exact-source review and valid runtime authority. If a bounded image-registration method cannot produce the positive evidence without ambiguity, stop and report the detail surface unsupported; do not lower 2 px or 0.02 and do not proceed to Save All. The implementation plan should not claim a production fix until the independent real-frame positive is observed.

### Proposed literal source and test scope

Source paths, only after external Plan approval and a new explicit source GO:

- `rev28/Sources/Rev28Core/Perception/OcrEngine.swift` — add the narrow typed registration result/evaluator; retain native affine mapping, OCR semantics, and existing target-row guards.
- `rev28/Sources/rev28ctl/main.swift` — compute the proof from the exact retained CUA bytes and same-capture full-display SCK bytes/ROI, bind hashes and native lineage, and include it in the existing frame-support sidecar/manifest/receipt. Keep existing freshness and native capture guards.
- `src/line_backup_batch/observations.py` — validate the typed proof for `ALBUM_DETAIL`, including exact artifact hashes, frame/session/PID/window/display/ROI binding and residual/uncertainty bounds; keep the current OCR identity and menu-point safe-bound checks. Keep legacy OCR anchor checks for non-detail surfaces.
- `harness-development/line-two-album-pilot-20261014/mac/producer.mjs` — only if the receipt contract needs to surface an additional typed proof reference; otherwise leave this wrapper untouched because it currently forwards native-produced uncertainty and artifact references without interpreting anchor geometry.

Focused tests:

- `rev28/Tests/Rev28CoreTests/FrameSupportTests.swift` — test the registration evaluator's valid same-content mapping and refusals for displacement `>2 px`, ambiguous/low-information images, mismatched dimensions/ROI, and wrong native lineage. These tests validate the evaluator only and cannot substitute for the required real-frame positive.
- `tests/test_batch_observations.py` — test sidecar hash/lineage binding and refusal for missing, stale, altered, wrong-window, wrong-display, out-of-ROI, over-2 px, understated uncertainty, safe-margin below `u+4`, and intersection below `16×16`; prove ordinary non-detail validation still uses the existing OCR contract and menu OCR row remains mandatory.

No edits are proposed to `entry.mjs`, `classifier.mjs`, `service.py`, grant/ledger/store/CLI contracts, generic cache behavior, or Swift capture APIs unless implementation discovery proves one strictly necessary; such an expansion requires an updated literal path plan and external Plan Review. In particular, there is no approved Swift/native guard relaxation, no general image-registration framework, and no production change in this artifact.

### Acceptance criteria and adversarial cases

- **Positive:** a genuine, retained `ALBUM_DETAIL` CUA/SCK pair from the same fresh capture, matching native PID/window/display, yields an image-derived alignment residual at most 2 px; its proof verifies by hash in Python; actual Save All OCR row and existing point/safe-bound guards still pass on a fresh calibration. A single real pair is necessary evidence, not sufficient real LINE E2E acceptance.
- **Negative:** the historical `71-vs-73` global exact-text false pairing (1215.032 px) is shown to refuse or be excluded by the authenticated native-window ROI; normalized date OCR plus the uncertain short OCR anchor cannot pass by dropping anchors or lowering limits. The historical ROI replay itself remains a refusal (max OCR center residual 2.944 px; corrected date 2.676 px; area ratio 0.0127273).
- **Negative:** wrong native PID/window/display, changed CUA or SCK bytes, stale pairing, wrong ROI, unsupported image content, ambiguous match, measured residual above 2 px, `uncertainty < 2`, row margin `< uncertainty + 4`, or interactive overlap `<16×16` all fail closed.
- **Isolation:** an `ALBUM_DETAIL` proof cannot be consumed as ordinary intent `CLEAR` or for another frame/window; original Save All/chooser/owner/intent/hash and at-most-once gates remain byte-for-byte behaviorally unchanged.
- **Regression:** other surfaces continue the current OCR anchor contract and the current valid native-geometry tests remain passing.
- **Stop:** if genuine pixel registration cannot meet the positive criterion with a directly measured ≤2 px point-alignment error, report `BLOCKED/UNSUPPORTED` and do not dispatch Save All. No acceptance waiver is implied.

## Evidence and provenance

- Existing source HEAD reviewed: `91c85617c2e943037caa41188c26f1474a3e56d6`; tracked source diff for the three inspected files was empty.
- Source hashes: `OcrEngine.swift` `d0dcab179db7311853857eeaf065339eb4f74c64976dd2b5104ef9fa280cec00`; `rev28ctl/main.swift` `1f6724e6f1a1149074177251253517d72d3719550c9dd5725289cf4f930baddc`; `observations.py` `c519b3f962556e1655157e6df0c089fd1f496c06dfa19addfb593d13a42792a6`.
- Genuine-frame replay driver: `harness-development/one56-menu-compat-20261017/review/anchor-roi-replay-driver.swift`, SHA-256 `661e27f832a35fe6819efd353b5d9227f89bb0cc01d4e529e93b7c2079e60c4e`.
- Genuine-frame output `anchor-roi-71-vs-73.txt`, SHA-256 `a232aa0c0bfffe67e044c778f4624c493552b6c81e5bca45d34ac3c5fbe2697b`; `anchor-roi-66-vs-68.txt`, SHA-256 `ba6eb8ae49ea2761e8d1e9ddd51e7103777d7b1578fb83fe92f028d7dfc96ab8`.
- The append-only private ROI follow-up driver is `private/anchor-dispersion-20261018/roi-followup-driver.swift`, same SHA `661e27f832a35fe6819efd353b5d9227f89bb0cc01d4e529e93b7c2079e60c4e`; private outputs have the same content hashes above. The executable replay binary SHA-256 is `1d6f58923d5a3268e969674c9053b18c1f70517800c19d9bae243e0ab787d4d9`.
- Existing native build input used for replay: `OcrEngine.swift.o` SHA-256 `ab133ceff739ae9bf9fa3e392d6cab2729d5d79005403c9b404b17368c4399b3`; existing `rev28ctl` SHA-256 `d500156e5e39eaa867bff7689f8cc6b700323324ae59c0d922219b57f672d842`. These identify the local debug/build artifacts used by this diagnostic, not the installed production producer9ef75efe. Their hashes are not an external approval, new production build, current authorizer PASS, or evidence that the installed producer executed this replay.
- Root reports the independent read-only environment check at 2026-10-17T19:12:48Z (2026-10-18 Asia/Taipei): native LINE foreground PID 25266; hosted frame 19:14:28.821Z, 654×1286, list top showing the excluded 65-card while the 56-card was not visible; no input was sent, mapper NOT_RUN. Root separately reports the 245 protection-file hashes unchanged. These are independently reported observations, not actions performed by this analysis agent.
- This document and its source proposal are not external Plan approval. The next gate is Owner-transferred external review of the exact plan revision; until then source remains unchanged.

## Delivery and full-goal limits

This proposal preserves the Owner's full goal: eligible56 album A → at-most-one original Save All → empty independent destination → exactly56 stable files → per-file SHA-256 and full ImageIO decode → durable VERIFIED readback/release; then return to list, perform the required real downward scroll, select a different eligible B and use a separate transaction authority. This plan alone authorizes neither A nor B.

After actual external Plan approval, the existing Luna/high Implementer receives only the admitted literal scope, without helper writers. Root inspects the diff and appropriate focused checks, rebuilds native production after Swift changes, and binds exact source/runtime/producer/decoder/entry bytes. The same newly fixed HEAD and full report go to Owner for a genuine external Code Review; the local E2E agent cannot substitute for either external review. Independent post-implementation E2E uses a new context on the fixed commit and the current genuine runtime/foreground authorization. The next real input sequence should be the continuous formal A trial, not another standalone menu-opening campaign.

No old grant is reopened, no counters are reset, and no historical record/photo is edited. Canonical ledger and239 historical VERIFIED plus manual65 exclusion remain protected. Preserve all previous root-issue attempts; at most3 evidence-bearing attempts and stop after2 without information gain, or earlier at a material blocker. If the proposed proof would require another source path, new dependency/framework, weaker bounds, changed authority/data boundary or relaxed AC, stop and return the exact delta for external Plan Review. Do not amend or force-push existing review history. Publish this proposal and full redacted evidence with a checkpoint commit to Draft PR10; publication is not external submission or approval.
