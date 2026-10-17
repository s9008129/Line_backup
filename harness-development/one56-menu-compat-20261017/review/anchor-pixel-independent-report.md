# Independent retained-image P1 report (redacted)

This is GPT-6-luna/xhigh independent retained-image validation, not external Code Review or live backup E2E. Source reports below are retained unchanged locally. Public copies replace the personal worktree/project-root prefix only; original photos, native/AX bytes and authority records are not published. Original source report hashes identify the private originals, not the redacted copies.

---

Original: `private/anchor-implementation-20261018-01/independent-p1/provenance-audit.md`; SHA-256 `9fbab2b94b1f60f8fb2f3e16dbf9345cc55546eb4ac902379cee266b5bd3d9be`.

# Independent P1 Retained-Image Provenance Audit

**Role/status:** independent evidence validation for retained-image P1 only. This is not post-implementation E2E, an external code review, or fresh live calibration. No GUI was used. No product source, tests, fixtures, Git state, grant, intent, or ledger was changed. Only this audit file was added under the authorized evidence directory.

**Binding:** worktree `<WORKTREE>`; fixed HEAD `a846df01fb056b34511dad1e2ad3abb7ac152e26`. External GitHub review `5560487952` was read in full and returns `APPROVE_PLAN` for `ANCHOR-DETAIL-R1-20261018` only, with mandatory P1 feasibility and P2 detail semantic-binding constraints. The immutable Plan file `harness-development/one56-menu-compat-20261017/anchor-fix-analysis.md` hashes to `f0518fc3fd0bc8103401168476d1e23b505d1e8d539751bf62cfdfa30a2f7094`. This grants no implementation approval, runtime authority, fresh-calibration pass, or Save All permission.

## Retained images and visual content

I inspected the original retained CUA/JPEG and full-display SCK/PNG bytes directly. The CUA frames `private/independent-live-01/22-probe3/66-dots-pre.jpg` and `71-dots-post.jpg` are each 654×1286 JPEG/JFIF. The SCK frames `68-dots-sck-pre/sck-frame.png` and `73-dots-sck-post/sck-frame.png` are each 2294×1490 PNG. All paths below are relative to `harness-development/one56-menu-compat-20261017/`.

| Artifact | Bytes | SHA-256 | Capture metadata / visible state |
|---|---:|---|---|
| `private/independent-live-01/22-probe3/66-dots-pre.jpg` | 200,746 | `3677b3cc976f1b0f0cc36e1138b172927a8d8c32e0dbd86b99f785d3b08f26b3` | CUA crop visibly shows the `2024/05/27～05/31` 56-photo detail, header and grid; ellipsis visible; menu closed. |
| `private/independent-live-01/22-probe3/68-dots-sck-pre/sck-frame.png` | 3,694,207 | `4ea25b3d268879a6860b2b8b6e37c10bd37e487f50ee115890933974fb5978c9` | Full desktop; same detail is the right LINE window, menu closed. SCK record started `2026-10-17T14:13:48.788Z`, ended `14:13:49.293Z`; OCR record SHA-256 `ed60d37271f95fac669bf14783b2f28fbb1399e994c00e4aae222a094aa6d969`. |
| `private/independent-live-01/22-probe3/71-dots-post.jpg` | 201,359 | `8d27e6b4222d71fe17916a023078cf5c7fbb6e48cebec68aabfe494923ca5ec7` | CUA crop still shows the same detail/grid and cursor at the ellipsis; popup is not visible in this crop. |
| `private/independent-live-01/22-probe3/73-dots-sck-post/sck-frame.png` | 3,661,221 | `2f6f359c82dc55ec401f4704e66c0d734b26d76ad533d28b6011998fe40ffde1` | Full desktop; same detail plus visible popup and `儲存全部`. SCK record started `2026-10-17T14:14:15.543Z`, ended `14:14:16.059Z`; OCR record SHA-256 `c31cd8f22b1a4f58f07703c564190678bea4ffa8101d5788366454d48d7fdedc`. |

The retained SCK metadata consistently binds display ID 1, display bounds `[0,0,1147,745]` points, point-pixel scale 2, and image dimensions 2294×1490. The intended detail window is PID 25266, window ID 7349, bounds `[358,46,327,643]` points, which maps by those recorded geometry fields to a 654×1286 pixel ROI at `[716,92,654,1286]`. The list window is ID 3766 at `[21,46,327,643]` points. Before the ellipsis input, both LINE windows are on-screen, with detail 7349 main/focused. After it, native inventory adds popup window 7359 at `[641,98,137,167]` points, layer 101; detail 7349 remains main/focused. Post-SCK OCR identifies title `2024/05/27〜05/31`, `56張照片`, and popup item `儲存全部`.

The CUA images and SCK crops have matching dimensions and visually recognizable album content. This is evidence that the retained material contains the real target detail and a later real popup. It does not by itself establish a sub-2px image-derived registration or target-point error bound.

## Provenance and timing limits

- Native pre/post snapshots `67-native-pre-dots.json` and `72-native-post-dots.json` are read-only. They both identify bundle `jp.naver.line.mac`, frontmost/target PID 25266, launch time `2026-10-16T17:43:32Z`, executable `/Applications/LINE.app/Contents/MacOS/LINE`, and one matching process. Snapshot times are `2026-10-17T14:13:49Z` and `2026-10-17T14:14:15Z`. File hashes are respectively `99dc0322bea3b6e52d0ae702e6f2c19aec551fb49bfe29f6950b7d2beb5bf21a` and `14e85909fb4b122b90693d4a6fa6fc505a642bab7ec5ee2479a3fe1a44139788`.
- The SCK tool is the retained observer `private/menu-sck-observer.swift`, SHA-256 `216e2ae6fb7d9b8189ac8f27ae97ef2244af1028be20bb31b957d09ce40463a8`; retained executable `private/native-observer-build-01/menu-sck-observer`, SHA-256 `484fdaedc0b90f23fd643ba4644dbea5a69265f08f4bcd2991a4c08f2eb9985f`. The build receipt binds them. Source uses ScreenCaptureKit and Vision; it records `evidence_only=true`, `formal_authority=false`, `gui_inputs=0`, exclusive file creation and readback. The PNG/record hashes in its stdout match the retained artifacts.
- The native observer source is `<PROJECT_ROOT>/harness-development/line-two-album-pilot-20261014/private/owner-list-menu-saveall-20261017-01/native-readonly.swift`, SHA-256 `a6d2c5b29c470fe79e032adbafbcc333cfefbd7b8a826f29807cd1716086ef01`; retained executable SHA-256 is `9ef7a852aa0d02ab211dadef306898d4f0a16ffd446401335ee019110c6f6401`, matching the build receipt. Its code uses AX attribute reads and `CGWindowListCopyWindowInfo`; it has no AX action or setter calls.
- The CUA AX text for pre and post is byte-identical (SHA-256 `e17385e3559f2c2c56f513306ad6bab6b5b7a8f8480d4a2dc98057f7bcc43aaa`), contains only a standard window/close/minimize/menu-bar controls, and does not name the album. CUA screenshot artifacts have no retained per-capture receipt binding timestamp, source PID, or native window ID. Their local file mtimes are `14:13:56Z` and `14:14:08Z`; these are artifact modification times, not proved capture timestamps.
- The ellipsis click receipt `70-dots-click.receipt.json` binds one resolved call, `CUA app.click([610,99])`, from `14:14:07.048Z` to `14:14:07.744Z`, with no retry. It is not a CUA image-capture receipt and contains no before/after screenshot hash. Its pending file `69-dots-click-pending.json` says `delivery: not yet invoked`; pending SHA-256 `6f34226412aa2827f3d6cff7b85f308bc81dade36569f93a76565ab8178abf26`; receipt SHA-256 `766b485f96a012b614ea815514723c86f047eb6f07924423729b69876b4a74a2`.
- The pre CUA file mtime follows the pre-SCK capture by about 7 seconds; post CUA file mtime precedes the post-SCK capture by about 7.5 seconds. These times are consistent with the surrounding sequence but cannot prove acquisition times or a <=5-second paired capture. More concretely, post CUA lacks the popup while later native/SCK show popup 7359. The post pair therefore has a known visible-state difference in the ROI. A P1 method may establish a limited image property using stable, unoccluded content, but must explicitly reject/mask changed, popup-occluded, cursor, repeating, or photo-sensitive pixels and must not claim these historical frames satisfy fresh-pair authority.
- No screenshot was synthesized or pixel-converted for this audit. No alignment algorithm was run. No positive/negative registration claim is made here.

## Current independent gate state

The retained history supports a **feasibility experiment candidate**, not a fresh live gate. Historical P1 can establish only whether a frozen method measures a reproducible image-content property on these exact bytes. It cannot satisfy a current synchronized-capture, formal authority, runtime-grant, or transaction gate. There is no accepted matching algorithm yet. The computed candidate point `[635,272]` is a proposed Save All point from prior M6 analysis; it was never dispatched as a menu-row click. No Save All was dispatched in this probe.

External P1 requirements still to validate after the root supplies the frozen driver and its exact hash: reproducible same-detail positive; deliberate displaced/wrong-window negative; unique match and adequate spatial spread; conservative bound on the actual target-point error `<=2px`; no OCR-center/native-geometry substitution; and explicit rejection of wrong ROI, ambiguity, low information, occlusion, repeated/photo-changing content, or bad provenance. Quantization or an integer peak alone must not be treated as a proof of continuous target error. If the method cannot establish a genuine positive on the retained bytes, report unsupported and do not integrate.

**At this point: P1 reproduction NOT_RUN; live/fresh calibration BLOCKED by absent fresh paired capture; implementation/source approval NO; Save All count 0.** Await the exact frozen experiment driver path/hash and declared error bound from root. Do not rerun or alter the experiment independently.

---

Original: `private/anchor-implementation-20261018-01/independent-p1/provenance-clarification-01.md`; SHA-256 `7facc6566873a7be768eed5039628a03567f11907de3f5abe23e6797f391aa28`.

# Provenance Clarification 01

This addendum refines the interpretation in `provenance-audit.md` without changing or replacing its raw facts. The hosted CUA JPEGs are app-window captures, not full-display captures. A separate floating popup can be omitted from the CUA app-window image even while it is open; the full-display SCK image includes it. Therefore the absence of the popup from `71-dots-post.jpg`, compared with its presence in `73-dots-sck-post/sck-frame.png` and native inventory `72`, proves a cross-provider content/occlusion difference, **not** that the popup opened between those captures. CUA acquisition time and popup capture behavior are not bound by a CUA receipt here.

The pre-SCK frame independently records no popup at its capture time, while the post native/SCK frame records popup window 7359. The relative timing of the CUA frames remains unknown; file mtimes are write times only. For any post-pair image-registration experiment, the region occluded by the separate popup in full-display SCK must be excluded or explicitly handled. Do not infer popup temporal state from the window-cropped CUA frame alone.

---

Original: `private/anchor-implementation-20261018-01/independent-p1/p1-results.md`; SHA-256 `6bf26a73053f8eca812bdd73f66f7d466ff47d63d036f03a404b19b76f781c76`.

# Independent P1 retained-image result

**Verdict: BLOCKED for the target-point alignment gate; do not integrate this method into production.** This independent run reproduces broad, zero-integer-shift image correspondence on retained detail-frame content and refuses the supplied wrong-ROI/wrong-window negatives. It does **not** establish a conservative `<=2 px` error bound at the proposed point `(635,272)`: the pre-frame target patch has zero variance, the post-frame target is in the SCK popup occlusion, and the point lies outside the accepted match hull in both real detail comparisons. The driver's own status is `REFUSE_TARGET_OUTSIDE_MATCH_HULL` for both. An integer shift of zero and zero residual among other patches do not bound the continuous target-point error.

This result is bound to the fixed base HEAD `a846df01fb056b34511dad1e2ad3abb7ac152e26` and frozen Plan revision `ANCHOR-DETAIL-R1-20261018` (SHA-256 `f0518fc3fd0bc8103401168476d1e23b505d1e8d539751bf62cfdfa30a2f7094`). External GitHub review `5560487952` approves that Plan slice only; it does not approve the implementation, runtime, or live calibration.

This is a retained-image feasibility result only. It is not fresh/current calibration, a formal runtime observation, a post-implementation E2E, external Code Review, GUI authorization, or Save All evidence. No GUI, product source, test, fixture, grant, intent, ledger, or Git state was changed by this validator. The historical CUA acquisition time is unknown; its file modification time is not a capture receipt. The SCK/CUA crop difference concerning the popup is described in `provenance-clarification-01.md` and is not treated as proof of a temporal state change.

## Acceptance criteria

| P1 criterion | Result | Evidence and interpretation |
|---|---|---|
| Reproduce a genuine retained detail-pair image property | **PASS, limited property only** | `pre-positive` measured 1,335 locally unique patches with integer shift `(0,0)` and max residual `0`; `post-popup-masked` measured 1,326 with the same values after the driver's popup/cursor exclusions. Both have broad accepted coverage `[17,17,625,1265]`. These are image-content correspondences away from the proposed target, not a target proof. Raw outputs are under `runs/`; identities and hashes are in `run-manifest.md`. |
| Required positive: prove the actual proposed target point aligns within `<=2 px` on a genuine retained pair | **FAIL for the tested method/input; required property remains unestablished** | Both positive-named cases return `REFUSE_TARGET_OUTSIDE_MATCH_HULL`. Pre target `(635,272)` has variance `0`, reason `LOW_TEXTURE`, and hull signed margin `-15.9253 px`. Post target is masked as `SCK_POPUP_OCCLUSION`, with hull margin `-120.2395 px`. No target error estimate is emitted. The case label `pre-positive` is only a matrix label, not a PASS. |
| Conservative continuous target-point error bound `<=2 px` | **BLOCKED / NOT ESTABLISHED** | Source method reports integer-pixel NCC shifts and explicitly says “no error bound asserted.” There is no subpixel fit, localization uncertainty, or independent target witness here. Other matched patches at shift zero cannot supply a bound outside their supported coverage. Actual target error is unknown; this report does not claim it exceeds 2 px. |
| Adequate uniqueness and spatial spread | **PARTIAL** | The pre comparison has 15/16 selected global representatives unique and one ambiguous; post has 14/15 unique and one ambiguous. Accepted patches are spread across much of the ROI, but terminate at x=625 and do not cover the proposed x=635 point. The target is outside both accepted hulls. Thus spread supports broad correspondence only and does not satisfy target-point support. |
| Wrong/displaced ROI and wrong-window negatives refuse | **PASS for the tested negatives** | `wrong-roi-plus8` rejected all 1,367 textured candidates at measured `(-8,0)`; `wrong-roi-diagonal-plus2` rejected all 1,335 at `(-2,-2)` (radial displacement `sqrt(8) ~= 2.828 px`, over the Euclidean 2 px bound); `wrong-window-list` accepted zero candidates and refused. All three driver exits are `0`; refusal status is `REFUSE_INSUFFICIENT_UNIQUE_MATCHES`. See raw JSON and command binding in `run-manifest.md`. |
| Fresh synchronized pair, current runtime lineage, and formal calibration | **NOT_RUN** | Only retained 2026-10-17 frames were replayed offline. The CUA capture receipt does not bind capture time/PID/native window; historical replay cannot satisfy the Plan's fresh `<=5s` pair or current formal gate. No GUI or formal lifecycle was used. |
| Production integration / full E2E / Save All | **NOT_RUN; not authorized by this P1 result** | The tested method fails to establish the required target bound. No product changes, Save All, download, file verification, state readback, or second-album E2E occurred. |

## Independent execution and evidence binding

I reviewed the frozen driver source independently and rebuilt it with `swiftc -O`. Frozen source SHA-256 is `f8a09bdba3f1b6043b447b3e9d0e45a2669426088e8f712503b5438506d5f671`; the independent rebuilt executable SHA-256 is `337df866b583cea271a314b049771c5da3abadeddb85f88940b8a14235f9423d`. It differs from the root-supplied candidate executable, so I used only my independently rebuilt executable. Build command, compiler identity, supplied binary identity, retained input identities, exact invocations, timestamps, per-case exit codes, raw-output sizes and SHA-256 values are recorded in [`run-manifest.md`](run-manifest.md).

The five offline cases are `pre-positive`, `post-popup-masked`, `wrong-roi-plus8`, `wrong-window-list`, and the permitted diagonal `wrong-roi-diagonal-plus2`. The first four JSON objects were independently cross-checked by root against a separate executor's results; root's append-only receipt says every JSON value except input-path spelling is identical and that root did not re-execute the algorithm: `../independent-output-crosscheck.json`. I independently inspected my own complete raw JSON and derived the verdict above from the values, rather than treating that cross-check or producer assertion as acceptance.

The source's matcher is 8-bit grayscale normalized cross-correlation over `17x17` patches, integer search `+/-8 px`, candidate stride `16 px`, variance floor `90`, peak floor `0.92`, non-adjacent peak gap `0.025`; it accepts local shifts only when Euclidean displacement is at most `2 px`. The target patch is checked separately, but the reported target outcome is zero-variance/occluded. The global representative check found one ambiguous representative in each positive pair. The source's status deliberately distinguishes `MEASURED_ALIGNMENT_NO_VALIDATED_ERROR_BOUND` from a refusal, and the two genuine pairs refuse before that status because the target is outside the hull.

## Evidence references

All paths are relative to `<WORKTREE>` unless otherwise stated.

- Frozen Plan and external Plan approval binding: `harness-development/one56-menu-compat-20261017/anchor-fix-analysis.md` and `harness-development/one56-menu-compat-20261017/chief-review.github.json`; Plan SHA-256 `f0518fc3fd0bc8103401168476d1e23b505d1e8d539751bf62cfdfa30a2f7094`.
- Frozen implementation under test: `harness-development/one56-menu-compat-20261017/private/anchor-implementation-20261018-01/feasibility/anchor-feasibility-v3.swift`.
- Independent provenance assessment, including actual image dimensions/hashes, native windows/PID, SCK/OCR lineage, and timing limits: `provenance-audit.md` and `provenance-clarification-01.md`.
- Raw per-case stdout JSON, stderr, start/end (where retained), and exit code: `runs/<case>/`. The `wrong-roi-plus8` driver completed with exit `0`; a wrapper typo prevented writing only its end-time file. The exact wrapper issue is preserved in `runs/wrong-roi-plus8/runner-note.md`; the unknown end time was not reconstructed and the case was not rerun.
- Source/build/input/output hash manifest: `run-manifest.md`.

**Next decision:** treat this P1 attempt as unable to support production integration. A subsequent plan, if pursued, needs a method that can produce a genuine positive at the actual target with a directly justified `<=2 px` bound while preserving wrong-ROI, ambiguity, occlusion, freshness, and lineage refusals. Do not lower the bound or infer it from zero integer shift. The current evidence does not prove actual target error; it proves only that this experiment refuses to certify it.

---

Original: `private/anchor-implementation-20261018-01/independent-p1/run-manifest.md`; SHA-256 `f56ed9522ca865d3fcacc2bed8b694090f5500ed67f2012fa0be2232cdca3176`.

# Independent P1 Replay Run Manifest

All paths below are relative to worktree `<WORKTREE>`. Runs were offline over retained files only; no GUI APIs were called.

## Source and build binding

- Frozen driver source: `harness-development/one56-menu-compat-20261017/private/anchor-implementation-20261018-01/feasibility/anchor-feasibility-v3.swift`, SHA-256 `f8a09bdba3f1b6043b447b3e9d0e45a2669426088e8f712503b5438506d5f671` (matches root-provided frozen hash).
- Root-supplied executable: `.../feasibility/anchor-feasibility-v3`, SHA-256 `a2acc1a04ddc93f1e4b69c65b96f8010d215670ab96e05fee3524ae884619398` (matches root-provided hash). I independently rebuilt from the verified source and used only my rebuilt binary for these runs.
- Independent command: `swiftc -O -module-cache-path harness-development/one56-menu-compat-20261017/private/anchor-implementation-20261018-01/independent-p1/module-cache harness-development/one56-menu-compat-20261017/private/anchor-implementation-20261018-01/feasibility/anchor-feasibility-v3.swift -o harness-development/one56-menu-compat-20261017/private/anchor-implementation-20261018-01/independent-p1/anchor-feasibility-v3-independent`.
- Compiler: Swift 6.3.3 / swift-driver 1.148.6, target `arm64-apple-macosx28.0`; `swiftc` version output SHA-256 `fccc73515642539c6245fc264ebd4a652bb68f6a5a375d4dc8b8d6f08b71cfef`.
- Independent binary: `.../independent-p1/anchor-feasibility-v3-independent`, SHA-256 `337df866b583cea271a314b049771c5da3abadeddb85f88940b8a14235f9423d`; Mach-O arm64. Build exit 0; stdout/stderr are both empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). The rebuilt binary differs from the root-supplied binary; I did not assume binary equivalence.

## Retained input identities

| Input | Bytes | SHA-256 |
|---|---:|---|
| `harness-development/one56-menu-compat-20261017/private/independent-live-01/22-probe3/66-dots-pre.jpg` | 200,746 | `3677b3cc976f1b0f0cc36e1138b172927a8d8c32e0dbd86b99f785d3b08f26b3` |
| `harness-development/one56-menu-compat-20261017/private/independent-live-01/22-probe3/68-dots-sck-pre/sck-frame.png` | 3,694,207 | `4ea25b3d268879a6860b2b8b6e37c10bd37e487f50ee115890933974fb5978c9` |
| `harness-development/one56-menu-compat-20261017/private/independent-live-01/22-probe3/71-dots-post.jpg` | 201,359 | `8d27e6b4222d71fe17916a023078cf5c7fbb6e48cebec68aabfe494923ca5ec7` |
| `harness-development/one56-menu-compat-20261017/private/independent-live-01/22-probe3/73-dots-sck-post/sck-frame.png` | 3,661,221 | `2f6f359c82dc55ec401f4704e66c0d734b26d76ad533d28b6011998fe40ffde1` |
| `harness-development/one56-menu-compat-20261017/private/independent-live-01/22-probe3/01-sck-before-open/sck-frame.png` | 3,476,740 | `972d2151a049176e711c1b19d7e0976797bad3237498b1f6db16a2ad0099603f` |

## Executed cases

Each command below is the rebuilt executable followed by the listed arguments, with stdout/stderr redirected to that case directory. Every driver process exited `0`; each case's retained `exit-code.txt` contains `0`, and each driver `stderr.txt` is empty (empty SHA above). The generated JSON is the unmodified driver stdout.

| Case | Exact driver arguments after binary | Start → end UTC | Output JSON bytes / SHA-256 | Output summary |
|---|---|---|---|---|
| `runs/pre-positive` | `66-dots-pre.jpg 68-dots-sck-pre/sck-frame.png 716 92 654 1286 635 272 pre` | `23:12:25Z → 23:12:26Z` | 536,752 / `4405535456a7c2874b201dd49e26fe9803ba4d6cb4400885bb4c6728b733bc9c` | 1,335 locally unique patches; each sampled shift `(0,0)`; median displacement 0; max residual 0; 15/16 representative global patches unique at native prediction, 1 ambiguous. Target is outside the matched hull (x-max 625; signed margin −15.925px), target-patch variance 0/`LOW_TEXTURE`; status `REFUSE_TARGET_OUTSIDE_MATCH_HULL`. |
| `runs/post-popup-masked` | `71-dots-post.jpg 73-dots-sck-post/sck-frame.png 716 92 654 1286 635 272 post` | `23:13:07Z → 23:13:08Z` | 538,171 / `8f1866a83b72ee0f5503cbd164517b580ab8ffb51f040a84b8815b29b4454a26` | 1,326 locally unique patches, all `(0,0)`; median displacement 0; max residual 0; 14/15 representative global patches unique, 1 ambiguous. Target outside matched hull (signed margin −120.239px) and masked as `SCK_POPUP_OCCLUSION`; status `REFUSE_TARGET_OUTSIDE_MATCH_HULL`. |
| `runs/wrong-roi-plus8` | `66-dots-pre.jpg 68-dots-sck-pre/sck-frame.png 724 92 654 1286 635 272 pre` | `23:13:25Z → unknown` | 546,689 / `4e47b3831f4e1b04626374d2c6c54c3b186f6b6d4ccd7730e5913da68f7904df` | 0 accepted; 1,367 candidate patches measured exactly `(-8,0)` and rejected as over-2px; 353 ambiguous; 1,361 low texture; status `REFUSE_INSUFFICIENT_UNIQUE_MATCHES`. The shell wrapper's end-time redirect had a path typo; exact note is in `runs/wrong-roi-plus8/runner-note.md`. Driver ran once, exited 0; it was not repeated. |
| `runs/wrong-window-list` | `66-dots-pre.jpg 01-sck-before-open/sck-frame.png 716 92 654 1286 635 272 pre` | `23:14:07Z → 23:14:07Z` | 540,954 / `8a20539cdfd24f6434d9240d51686bea1d409b0b089ca7a1bf7ad45164086256` | 0 accepted; 1,719 low-correlation, 1 ambiguous, 1,361 low texture; status `REFUSE_INSUFFICIENT_UNIQUE_MATCHES`. |
| `runs/wrong-roi-diagonal-plus2` | `66-dots-pre.jpg 68-dots-sck-pre/sck-frame.png 718 94 654 1286 635 272 pre` | `23:14:26Z → 23:14:26Z` | 548,175 / `86d2523c7589a5cd9fa076635c0da51ecd2592e7447894f78c263f924cc53983` | 0 accepted; all 1,335 textured candidates returned `(-2,-2)` (radial displacement √8≈2.828px) and were rejected as over-2px; 385 ambiguous; 1,361 low texture; status `REFUSE_INSUFFICIENT_UNIQUE_MATCHES`. |

Each case's full command/start/end/exit/raw stdout/raw stderr files are under its `runs/<case>/` directory. No synthetic image or pixel-converted derivative was created. The wrong-window comparison uses the retained list-only full-display frame whose SCK metadata binds window 3766; the positive pair's detail frame binds 7349. All invocation JSONs retain input filenames, ROI, target, parameters, all candidate peaks, and all global-match records; this manifest binds the exact source bytes and image bytes.

---

## Sol integration clarifications

- The independent result references legacy `chief-review.github.json` in one evidence list. The actual current Plan Review retained by root is `private/anchor-implementation-20261018-01/external-plan-review.github.json`, SHA-256 `9f3cc3318041dbf9686f9857899b040046e7613e059aa5524b9278c0cbb2204a`, with binding beside it. The official review is [5560487952](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560487952). The legacy filename is not the current approval evidence.
- Local patch uniqueness means within the bounded +/-8 search. Only selected representatives receive the whole-ROI check; not every accepted local match is globally unique, and ambiguous representatives do not filter the local-set hull. No formal target uncertainty is established.
- Exact invocation forms are recorded in the run manifest. Per-case directories retain stdout/stderr/start/exit and end where available, rather than a separate command file for each case. The x+8 wrapper error and unknown end timestamp remain visible; no repeat was performed.
- A source comment says half-pixel grid, but the implemented representative scan uses stride 2 pixels. The method string and manifest describe the actual 2px sampling; there is no subpixel measurement.
- This evidence supports the independent BLOCKED verdict for the tested method, not impossibility of every registration method or a positive backup E2E.
