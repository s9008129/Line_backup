# ANCHOR-DETAIL-R2 — action-space correspondence amendment

Revision: `ANCHOR-DETAIL-R2-20261018`.
Status: `PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`. No R2 implementation, experiment, production approval or runtime grant exists.
Base HEAD: `7b16c60aa325f36c17a7da24d255c57dce73ce89` in the existing isolated worktree. Product source remains `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`; installed production runtime remains different from that candidate.
Risk: CRITICAL for the proposed input-evidence contract; this delivery changes documentation only. The closure gate remains independent external Plan Review, applicable exact-source Code Review, valid runtime authority and genuine transaction acceptance.

## Decision requested and preserved goal

Approve or reject exactly one conditional, reversible point-correspondence feasibility experiment described below. This is not approval to download, change canonical authority, or replace the production geometry gate with a boolean. If its prerequisites cannot be established through supported interfaces, the experiment is NOT_RUN/UNSUPPORTED, with no alternate probe.

The Owner's outcome remains A (`2024-05-27` through `2024-05-31`, 56 original images) → one original Save All → separate empty destination → 56 stable physical images → per-file SHA-256 and full ImageIO decode → durable VERIFIED/readback/release. Only then may a different eligible B use separate authority. Historical239 and the manually saved65 remain excluded/preserved. No B under ONE56, no PR merge.

The [external evidence review 5560750050](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560750050) accepts R1 P1 BLOCKED as correct fail-closed. Its actual GitHub state is COMMENTED, not an APPROVE event; its text is an evidence verdict, not R2 approval. Raw review SHA-256: `e2a491e97e6f39c378043bc787407ab957d4d8dee2494dd8dae6ad5ebe6852b9`.

R1 P1 is closed as BLOCKED, with evidence intact. No NCC parameter search, new matching algorithm, ROI guessing, threshold reduction, or new local reviewer agents. Zero integer displacement established neither a ≤2px bound nor actual error >2px. The popup need not have shared scene pixels in the app-window CUA crop; a future proof must address the actual selected row's input coordinate.

## Current read-only audit: facts versus unestablished capabilities

The [audit receipt](review/anchor-detail-r2-coordinate-audit.json) records exact inspected source/SDK hashes, actual review binding and the protection baseline. This round used only `cua.getApp("LINE")` to obtain the actual hosted API documentation and automatically returned AX state. It did not request a screenshot, native event listener, SCK capture, click, scroll or keyboard input. It establishes neither current56 identity nor a foreground handoff.

| Space / interface | Established now | Not established now |
| --- | --- | --- |
| Hosted CUA `App.click(target: number \| Vec2, options?): Promise<void>` | Coordinate calls and app-window observations are exposed. Existing adapter serializes its calculated points directly to `app.click`. | The returned documentation does not define macOS origin, units, crop/client/shadow inclusion, display selection, rounding, or how observation/rebinding affects mapping. No dispatched-event location/ID receipt or Mac full-display input target is exposed. Linux/Windows notes are not a Mac contract. |
| Full-display SCK | Existing `captureFullDisplayRetained` retains display image/witness, display bounds/ID, contentRect, pointPixelScale, independent backing scale, image dimensions and timing, with no sourceRect. It sees the floating popup. | A full-display observation is not a supported full-display CUA input endpoint. Native geometry does not certify the actual CUA dispatch. |
| Native window/event spaces | Existing `Coordinates.swift` distinguishes image pixels, window-local points and top-left global points. Apple documents native event location in global display coordinates; installed SDK declares per-process passive taps. | Local type comments are not proof of provider mapping or measurement precision. Listener permission, successful creation, event attribution, recipient window and cross-space error bounds have not been tested. |
| Historical actual menu | Real name→grid→menu→儲存全部 and title-label dismissal already observed. | Historical `[635,272]`, window7349, scale2 or any other old coordinate is not an input constant, current calibration or valid transaction receipt. |

Apple primary references support the API capabilities, not an already-proven accuracy claim:

- [CGEvent location](https://developer.apple.com/documentation/coregraphics/cgevent/location?language=objc): an event's global display location can be read.
- [Per-process event tap](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreateforpid(pid:place:options:eventsofinterest:callback:userinfo:)) and [passive-listener semantics](https://developer.apple.com/documentation/coregraphics/cgeventtapoptions): a listener can observe routed events without modifying them. Installed `CGEvent.h` declares `CGEventTapCreateForPid`, `CGEventGetLocation` and nonprompting `CGPreflightListenEventAccess`.
- [SCK content information](https://developer.apple.com/documentation/ScreenCaptureKit/SCShareableContentInfo/contentRect) and [frame metadata](https://developer.apple.com/documentation/screencapturekit/scstreamframeinfo): capture scaling/content metadata must be retained and checked, rather than assuming 2x or a whole-display pixel size.
- [AX read-only point hit-test](https://developer.apple.com/documentation/applicationservices/1462077-axuielementcopyelementatposition?changes=_6): native top-left screen-position/z-order corroboration is possible where LINE exposes it; it is not an input operation or a substitute for missing event evidence.

Finding now: **direct actual-point correspondence and a conservative ≤2px bound are NOT_ESTABLISHED**. A provider-supported Mac coordinate contract or authenticated documented mapping receipt is a hard prerequisite. It must include window selection/binding, origin/units, crop coverage, rounding and behavior across popup/observation changes. Use only actually exposed provider documentation/metadata or reviewable official adapter source; do not introspect hidden CUA methods, reverse-engineer a private endpoint, or infer the contract from native bounds or a coarse successful click. If these facts remain unavailable, stop before input with `UNSUPPORTED_CUA_POINT_CONTRACT`; do not run the probe merely to guess units.

## Only proposed feasibility experiment: exact-row shadow-point witness

Purpose: measure where one supported CUA coordinate invocation is actually routed, at the **same serialized coordinate selected for the real visible Save All row**, while the popup has first been safely removed. The test is not allowed to activate that row. A harmless point elsewhere cannot be substituted and extrapolated to it. No owned overlay/helper window, native input synthesis, cursor-move-only check, screenshot round-trip arithmetic, or alternate full-display input route is proposed.

The native observation candidate is a PID-scoped `CGEventTapCreateForPid`, tail placement, `listenOnly`, mouse-down/up only, with a maximum20-second armed interval. It must return each input event unmodified. No global keyboard capture, active event filter, HID/root tap, event modification or posting. Existing listener permission must already be present: use nonprompting preflight; denial, nil tap, disabled/lost listener or unsupported recipient annotations stops the experiment. Do not call permission-request APIs, change TCC, or prompt Owner as part of this probe. These are proposed capabilities, not claims of a working installed observer.

### Preconditions before any of the two possible clicks

1. Actual external R2 approval, fixed diagnostic source/binary hashes, independently checked diagnostic execution contract, and a separate auditable reversible-diagnostic permit are required. None exists from this document alone. The permit is outside the formal backup transaction and observation ledger; it cannot reopen an old grant, alter counters, or produce an ordinary CLEAR frame.
2. Owner hands over the actual56 detail grid with its menu already open through the previously proven route. This avoids adding a navigation/menu-discovery campaign. If the starting surface is wrong, report NOT_READY rather than adding setup scrolls/clicks under this experiment. Same uninterrupted handoff suffices; a focus/context change stops input.
3. Verify exact group context/retained list→detail lineage, PID/process-start/window/display, date/count and unique 儲存全部 row on fresh actual SCK. Reject the photo viewer, another album, foreign/ambiguous popup and the manual65. Capture genuine CUA/SCK/native/AX with bound request intervals; each required pair must meet the existing ≤5s gate. Provider contract and current crop/bounds/scale must agree; all metadata/hash mismatches stop.
4. Derive `s_row` from the freshly visible SCK row's safe rectangle, and `c_row` from the supported input mapping, preserving existing `u+4` and ≥16×16 intersection. Require the actual serialized `c_row` inside the supported CUA-addressable intersection, without requiring the whole popup/label to fit the crop. Freeze it for this single test. No historical points or row-number formula.
5. Identify a fresh, unique nonactivating static album-title close target, safely outside every popup row/control. Existing evidence supports this closure mechanism; current safety still needs verification. If coordinate ambiguity could reach an irreversible control, do not click. The observer must be ready and evidence read back before input.

### One continuous trial, no resend

1. **At most one title-label click**, via the actual hosted `app.click(c_title)`, to close the popup. Record its invocation/result and native events separately. No Escape, ellipsis toggle or guessed cancel action. If delivery is uncertain or closure fails, stop; no fallback/retry.
2. Fresh native inventory and SCK must prove the popup absent and the original56 detail still present. Retain new CUA geometry and verify unchanged provider binding, PID/process/window/display, layout, size, origin and scale. At the frozen `c_row`/corresponding `s_row`, verify a genuinely inert, non-photo, non-input, non-button header region with adequate clearance. Use visual evidence plus available AX hit-test/z-order corroboration. Missing AX semantics is not itself a positive inert-target proof; unresolved safety stops. A tooltip, floating＋, photo, title-bar control, chooser, new popup or foreign window invalidates the target. **Never send the test click while the Save All popup remains.**
3. **At most one measured `app.click(c_row)`**, now on that verified inert region. Retain the exact serialized argument, supported provider binding and call interval. The PID-scoped listener must yield one attributable left-down/up pair, the same recipient detail/window evidence, native event positions and timestamps. Extra/unmatched events, another GUI owner, missing window attribution or incompatible clock domains mean UNKNOWN/UNSUPPORTED, never an assumed match.
4. Verify the same56 grid remains, no popup/chooser/download appears, then end the observer and release only the diagnostic resources. Do not reopen the menu, retry a point, try another target or run a second trial. Record any partial execution and actual dispatch counts. No formal begin/admit/intent/dispatch/finalize/release services are called.

The total cap is **one experiment, no more than two hosted clicks**, zero Save All, zero chooser confirmations and zero native synthesized inputs. Even if only the title click occurs, this trial is used and its failure is retained. Offline validation of its recorded values does not permit another physical trial.

## Measurement and acceptance: no guessed precision or future guarantee

For an authenticated SCK display frame, let `D` be its recorded global display origin and `K` the verified native-global-to-SCK-pixel scale/axis convention. Let `g_down` and `g_up` be actual recipient event locations. Compute `p_event = K(g_event - D)` under the confirmed coordinate contract, and `e = max(norm(p_down - s_row), norm(p_up - s_row))` in SCK pixels. Include actual input serialization/rounding in the comparison; do not merely invert native bounds and call that a measurement.

The conservative total upper bound is `U = e + b_native_to_sck + b_binding_drift + b_unobserved_transfer`, using worst-case radial bounds. Every term needs a stated, independently justified finite bound and its source. Unknown is unbounded, not zero. Do not add the R1 prototype's arbitrary0.7071, equate numeric precision with accuracy, use average/RMS instead of worst-case, or manufacture a bound from zero integer shift. AppKit lower-left coordinates, negative display origins, mixed scale, pixel-center convention and intermediate event transformations must be resolved explicitly or refused. For this bounded trial, restrict to one unchanged display and refuse ambiguous/multi-display crossings.

Separate result subjects:

| Gate | Required evidence / outcome |
| --- | --- |
| Capability/preflight | Supported Mac input contract and passive recipient witness available without new privileges; otherwise NOT_RUN/UNSUPPORTED before clicks. |
| Safe exact-point trial | Fresh real row selection, safe title closure, popup absent at measured click, inert shadow point and unchanged native/host binding. Any unknown stops. |
| Actual measured point | Genuine uniquely attributed recipient down/up positions and verifiable SCK conversion; report the measured `e` even if it refuses. |
| Conservative target bound | All finite independently supported terms, `U≤2px`; retain uncertainty floor2, `u+4` and ≥16×16. An event-location log alone is not PASS. |
| Applicability to a later visible popup | A supported stable mapping/transport contract must bound unobserved differences between the shadow click and the actual selected popup-row invocation. Same numeric argument or one good sample does not prove future jitter is bounded. A popup switch, new detail window, provider rebinding, different coordinate, stale pair or layout/scale drift invalidates the witness. Without this transfer proof, report `MEASURED_POINT_ONLY; PRODUCTION_POINT_PROOF=UNSUPPORTED`, even if `e` is small. |
| Isolation | Canonical authority/ledger/counters, original state/history and239 hashes unchanged; no formal lifecycle consumed and Save All0. |

**R2 is unsupported unless every required point-proof gate passes.** Success of the listener or a reversible click alone is only a limited observation. Do not infer an actual Save All event's accuracy from an unrelated title hit. A later production entry that creates a new detail window cannot reuse this window-bound diagnostic witness. Do not add an unreviewed formal calibration input or quota to work around that limitation.

Focused negative validation may replay the same actual trace with explicitly labelled altered contract data: expected-point offset+8, diagonal(+2,+2), wrong PID/process/window/display/scale/ROI, stale/swapped frame/hash, wrong popup lineage, changed serialized point, unknown/understated bound, an extra/missing event, popup still present, insufficient safe margin/intersection and invalid reuse. These are offline negative **validator** cases, not genuine new GUI actions. No extra physical wrong-point tests or synthetic screenshot success claims.

## Expected evidence and literal change scope

The one trial must retain an append-only manifest with source/build/runtime identities; actual Owner handoff and diagnostic authority; supported provider-contract artifact/version; CUA/SCK image and AX/native hashes; request/monotonic timing; window/process/display/layout lineage; current row OCR/safe rectangle; exact chosen coordinates/serialization; title-close and shadow-click invocation/return or uncertainty; passive recipient event fields; all measured/bound terms; pre/post screenshots; no-popup/no-chooser/no-download result; protection hashes; refusal reason and next action. No action-retry or ordinary CLEAR claim can be encoded by this manifest. Write only the isolated task evidence tree; publish the complete redacted report and numerical/runtime evidence to Draft PR10, preserving private originals.

| Stage | Literal allowed paths / status |
| --- | --- |
| This delivery | This Plan, `review/anchor-detail-r2-coordinate-audit.json`, existing `progress.md` and `review/E2E測試報告.md`; private review/protection/publication receipts. Documentation/evidence only. |
| After actual R2 approval: bounded diagnostic | Only `harness-development/one56-menu-compat-20261017/anchor-detail-r2/point-witness-observer.swift`, `harness-development/one56-menu-compat-20261017/anchor-detail-r2/point-witness-probe.mjs`, and `harness-development/one56-menu-compat-20261017/anchor-detail-r2/point-witness-probe.test.mjs`. Native helper is passive; all GUI input remains documented CUA. Reuse existing SCK/native observation code/tools with verified hashes; no framework or native-input fallback. These files do not exist as an implementation in this delivery. |
| Conditional later production impact, not source GO from a small measured residual | If the actual proof and its applicability are independently accepted, the minimum expected integration remains `rev28/Sources/Rev28Core/Perception/OcrEngine.swift`, `rev28/Sources/rev28ctl/main.swift`, `src/line_backup_batch/observations.py`; `harness-development/line-two-album-pilot-20261014/mac/producer.mjs` only if a typed witness reference must be surfaced. Tests limited to `rev28/Tests/Rev28CoreTests/FrameSupportTests.swift` and `tests/test_batch_observations.py`. |

The conditional integration must replace geometric authority only for actual ALBUM_DETAIL, retain legacy behavior on other surfaces, and independently check the native event/point witness rather than accept a producer PASS. Python must also separate the existing DETAIL_OCR_BINDING semantic date/count/ROI identity check from geometric OCR-center residual, preserving duplicate/foreign-window/wrong-count refusals. Exact artifact refs/hashes, process/frame/time/display/target binding and all safe-point bounds remain mandatory. The production manifest field contract is not implemented here. If proof transfer, entry behavior or validation requires another product path, schema/authority boundary, formal GUI operation or quota, stop and return only that precise delta for external review. No store/ledger/grant/entry/service/global-Harness edit is authorized by this amendment.

Sol owns the Plan/integration decision. After actual approval, Luna/high owns only the admitted minimum implementation; Luna/xhigh independently validates the fixed evidence/source in a separate context. Do not start either role now or add local cloud-review substitutes. One experiment; no new attempts by swapping model/session. Independent external ChatGPT reviews this exact Plan first. If a reusable proof is genuinely established, present its actual evidence before conditional production integration; then rebuild/bind exact producer/source/runtime/decoder bytes and obtain positive exact-HEAD external Code Review covering both the new source and earlier M5/M6. Existing ONE56 intent/owner/duplicate/empty-destination/atomic-dispatch/at-most-once guards remain. Only valid fresh formal authority and Owner foreground can enable A, and only A VERIFIED enables separately authorized B.

## Present disposition

`P1=BLOCKED_CLOSED; CHIEF_EVIDENCE_VERDICT=ACCEPT_P1_BLOCKED_AS_CORRECT_FAIL_CLOSED`
`R2_PLAN_STATUS=PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`
`R2_CUA_POINT_CONTRACT=NOT_ESTABLISHED`
`R2_EXPERIMENT=NOT_RUN; MAX_EXPERIMENTS=1; MAX_DIAGNOSTIC_CLICKS=2`
`PRODUCTION_IMPLEMENTATION=NOT_RUN; REAL_SAVE_ALL_DISPATCH_COUNT=0`
`CANONICAL_AUTHORITY_LEDGER_HISTORY=UNCHANGED`
`NEXT_ACTION=OWNER_TRANSFER_FIXED_PLAN_SHA_AND_PR_HEAD_TO_EXTERNAL_CHATGPT_PLAN_REVIEW`
