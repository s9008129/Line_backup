# NATIVE_AUTO_CLICK/1 — macOS Native Click Feasibility Plan

Status: `PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`

Verdict: `SUPPORTED_NATIVE_AUTO_ROUTE_CANDIDATE`

This plan is a bounded implementation proposal, not an approval, not an
implementation, and not a LINE E2E result. It does not claim that a `<=2px`
proof has been demonstrated or that the LINE popup has been clicked. Every
unmeasured condition below remains fail-closed.

## 1. Frozen inputs and authority

- Repository: `s9008129/Line_backup`
- Planning worktree: `/Users/hsiaojohnny/.codex/worktrees/3c27/Line_backup`
- Planning branch: `plan/two-album-auto-20261019`
- AUTO base: `516932dfcee94b662082b909b7980fc2483ab9c0`
- Prior AUTO Plan HEAD: `c563cba5a353a85b3cd0da34cc0e9dc12e3cbd40`
- Prior AUTO Plan SHA-256: `31986a0cbe00e2267704073b9d4ddfa24dd3c7743c62b7a11649d9131d7d91a9`
- Prior AUTO Plan PR: <https://github.com/s9008129/Line_backup/pull/15>
- External Chief Review: <https://github.com/s9008129/Line_backup/pull/15#pullrequestreview-5569680474>
- Prior verdict: `BLOCKED_FOR_AUTO_IMPLEMENTATION`
- Effective `AGENTS.md` SHA-256: `8ea0cf8a75a239d1a849ac471756027970645821d73b0068c4da3103557fb3d2`
- Host: macOS 27.0.1 build 26A434; Xcode 26.6; SDK `MacOSX26.5.sdk`
- `GOAL_CRITICALITY=CRITICAL`
- `EVIDENCE_ROLE=PLANNER_PROPOSAL_ONLY`
- `CLOSURE_GATE=EXTERNAL_PLAN_REVIEW + EXACT_CODE_REVIEW + INDEPENDENT_E2E`

The exact bytes of this committed file are the reviewed Plan bytes. Their
SHA-256 is recorded outside the file in the commit/PR handoff so that the hash
is not self-referential. No product source, grant, ledger, protected state,
LINE GUI, or Save All is changed by this planning round.

## 2. Decision and evidence levels

The native route is technically supportable as a candidate because the
installed macOS SDK exposes a real event-posting API, the repository already
contains a partial native actuator, and a conservative receipt design can be
added without replacing `runTwoAlbumPilot`, its transaction authority, or its
ledger. It is not yet supported as a production route because the popup surface
contract, actual delivery receipt, and every `<=2px` error component have not
been demonstrated for LINE.

The following levels are intentionally separate:

| Level | Current fact |
| --- | --- |
| 1. Official API exists | Proven by installed SDK declarations listed in section 4. |
| 2. Existing code implements it | Partly proven in `QuartzActuator.swift`; no AUTO integration and no EventTap receipt. |
| 3. Local permission exists | Not verified in this planning round. Runtime must use nonprompting preflight. |
| 4. Actual event/recipient identity is observable | Not proven for LINE. It is a required approved probe result. |
| 5. Conservative `<=2px` upper bound exists | Not proven. It is a required approved probe result; otherwise dispatch is refused. |

No lower level implies a higher level. In particular, a declared CGEvent field,
a reported event location, a successful hover, or a screenshot/OCR match is not
by itself proof that LINE's intended popup row received the click.

## 3. Existing native capability and gaps

### 3.1 What already exists

`rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift` already has:

- real `CGPreflightPostEventAccess()` and `CGEvent(...).post(tap: .cghidEventTap)`;
- typed `ScreenPoint`, `WindowLocalPoint`, and `CapturePixelPoint` contracts in
  `rev28/Sources/Rev28Core/Geometry/Coordinates.swift`;
- process-start/bundle/PID/window readiness checks;
- fresh-frame, window-frame, safe-rect and point-drift checks after a hover;
- a single-use `ReadinessPermit` consumed before posting;
- durable pre-input hooks through `PersistentTransactionOwner`;
- `reserveSaveAll()` and `markSaveAllAttemptedWithRevalidationID()` before the
  mouse-down/up pair;
- a test-injectable sink that can prove refusal posts zero events.

This is a strong starting point, but it is not the AUTO route. The legacy
`rev28ctl live-execute` entry remains disabled at
`rev28/Sources/rev28ctl/main.swift:124-130`; it must not be revived or treated
as an available shortcut.

### 3.2 Blocking gaps

1. The production AUTO adapter still uses hosted `app.click(...)` at
   `scripts/line_backup_cua_adapter.mjs:425,479,609,630`. The documented call
   returns no actual event point, recipient PID/window, event token, or receipt.
2. `topmostSurfaceMatchesTarget` requires `layer == 0` at
   `QuartzActuator.swift:460-477`.
3. `revalidateAfterHover` requires `freshWindow.layer == 0` at
   `QuartzActuator.swift:408-414`.
4. `WindowIdentityValidator` rejects every non-zero layer at
   `rev28/Sources/Rev28Core/Identity/WindowIdentity.swift:200-202`.
5. No passive per-PID event receipt exists. `CGEventGetLocation` at creation is
   not a delivery receipt.
6. No AUTO source currently translates a fresh frame-bound target into this
   actuator, and no accepted dispatch receipt can carry native receipt evidence.

Therefore the correct conclusion is a candidate route with explicit gaps, not
`AUTO_CLICK_PROOF_SUPPORTED` and not a claim that the existing Quartz code is
already usable for Save All.

## 4. Official API contract inventory

The following are declarations in the installed macOS 26.5 SDK. They prove that
the APIs exist and compile; they do not prove LINE recipient semantics.

| Installed header | SHA-256 | Relevant declarations |
| --- | --- | --- |
| `CoreGraphics.framework/Headers/CGEvent.h` | `82c0ad9eb7c2f1ccfe8483fe96f5d71493ee1f5b4a6a68458ba9c07dd728f8bb` | `CGEventCreateMouseEvent`, `CGEventGetLocation`, `CGEventSetLocation`, `CGEventGetTimestamp`, `CGEventGetIntegerValueField`, `CGEventSetIntegerValueField`, `CGEventTapCreateForPid`, `CGEventPost`, `CGEventPostToPid`, `CGPreflightPostEventAccess`, `CGPreflightListenEventAccess` |
| `CoreGraphics.framework/Headers/CGEventTypes.h` | `0eb5b0aca9a77730d7c1b0449113b18419765771ae02a596708281f56f6c45b4` | `kCGEventSourceUserData`, `kCGEventTargetUnixProcessID`, `kCGMouseEventWindowUnderMousePointer`, `kCGMouseEventWindowUnderMousePointerThatCanHandleThisEvent`, `kCGTailAppendEventTap`, `kCGEventTapOptionListenOnly` |
| `CoreGraphics.framework/Headers/CGWindow.h` | `4c81fe292a23634fe7fe67f9eb0c36d178bd1b0aea04ba5ed80fa354ba237295` | `CGWindowListCopyWindowInfo`, window number, owner PID, layer, bounds, alpha |
| `ApplicationServices.framework/Frameworks/HIServices.framework/Headers/AXUIElement.h` | `e4c7b5521a48ace58127ef8e696370b265a26fe935f0bf63b8fa6876d072fddd` | `AXUIElementCreateApplication`, `AXUIElementCopyElementAtPosition`, `AXUIElementCopyAttributeValue`, `AXUIElementGetPid` |
| `ScreenCaptureKit.framework/Headers/SCShareableContent.h` | `01ecd6997892d404773d724a3936feffb2ca6f03cdbb8df31950d004e1992a33` | `windowID`, `frame`, `windowLayer`, `owningApplication`, `isOnScreen` |
| `ScreenCaptureKit.framework/Headers/SCStream.h` | `025ce72289d842191571495dfc98ba1f5fec0c00b77ed598ab7cc765a649e9aa` | `SCStreamFrameInfoContentRect`, `SCStreamFrameInfoBoundingRect`, `SCStreamFrameInfoScaleFactor`, `SCStreamFrameInfoContentScale` |

The installed SDK root is:

`/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk`

Official declarations do not establish the runtime value or presence of
`kCGMouseEventWindowUnderMousePointer*` for synthetic events, nor whether a PID
tap observes the exact posted event. Those are measured contracts, not assumed
facts.

## 5. Why the current layer-0 policy is incompatible with Save All

The repository's own LINE model treats the menu as a separate raised LINE-owned
window, not as part of the ordinary detail window:

- `mac/analyzer.mjs:160-180` requires exactly one raised LINE overlay above the
  fresh detail window, with a distinct `windowNumber`, `ownerPID`, and layer.
- `mac/analyzer.mjs:313-316` records `layer > 0` and
  `above_window_id == detail.window_id`.
- `mac/classifier.mjs:684-688` rejects a popup unless it is a different,
  positive-layer LINE window above the exact detail window.
- `mac_runtime.mjs:86-90` repeats the same popup identity requirement, and
  `mac_runtime.mjs:122-125` preserves `uncertainty + 4` erosion and a
  `16x16` minimum.

Consequently, ordinary `layer == 0` is correct for the album list/detail
surfaces but incorrect for the Save All popup. The required source change is to
parameterize the expected surface, not to delete or weaken the layer/topmost or
recipient checks.

### 5.1 Required `SurfaceExpectation`

Each dispatch must carry one explicit expectation:

- `ordinaryWindow`: exact window ID, owner PID, process instance, bundle,
  display ID, on-screen state, and layer `0`.
- `saveAllPopup`: exact popup ID, owner PID, process instance, bundle, display
  ID, on-screen state, positive layer, popup ID different from the detail ID,
  and popup below-window relationship to the exact detail ID.

Before both the hover and the down event, the topmost alpha-positive window
containing the point must be the exact expected surface. For the popup, no
other alpha-positive intersecting window may sit above it. An opaque or
ambiguous window above the target refuses dispatch. A popup animation or window
replacement between capture, permit, hover, and down refuses dispatch.

The expectation must be re-evaluated from a fresh `CGWindowListCopyWindowInfo`
sample and a fresh LINE window/AX/SCK frame. Cached layer values or historical
popup IDs are inadmissible.

## 6. Candidate native click bridge

The bridge is an actuator adapter, not another orchestrator or ledger.

`runTwoAlbumPilot` remains the entry point. Existing A -> C1 -> bounded scroll
-> distinct B sequencing, Python admission/intent/dispatch/finalize authority,
GUI reservations, and at-most-once Save All behavior remain authoritative.

The bridge accepts only a structured request, never a caller-supplied raw
screen point:

- `target_kind`: `album_card`, `menu_trigger`, or `save_all`.
- fresh `frame_id`, `session_id`, PID, process-start identity, bundle, display ID.
- exact `SurfaceExpectation` including popup/detail relationship.
- `CaptureGeometry` (`windowFrame`, recorded capture bbox, point-pixel scale).
- capture-space safe rectangle and derived center.
- `uncertainty_px`, declared safe margin, and a measured component bound vector.
- existing permit/receipt token, run/action identity, and reversible versus
  Save All intent.
- source hashes for the frame, AX evidence, OCR/popup evidence, and transaction
  references.

The bridge refuses if the point is not the center of a safe rectangle that was
derived from the exact target witness and is at least `16x16` pixels after
erosion. It refuses if the requested target is not unique. It does not accept a
point merely because OCR once reported the expected text.

### 6.1 Album-card target

Reuse `observations.py:707-740`: unique card fingerprint, fully visible card,
unique OCR title witness, uncertainty `<=2`, no enabled-button overlap, and the
center of the verified title rectangle.

The implementation must additionally bind that rectangle to the fresh window
and require a `16x16` safe intersection after erosion. If the live title
rectangle cannot satisfy that hard requirement, `album_card` refuses; it does
not fall back to a guessed card center.

### 6.2 Three-dot/menu trigger

Reuse the existing fresh `PIXEL_STRUCTURE` menu trigger and its uncertainty.
The native bridge must validate the target rectangle against the same detail
window identity and require the eroded safe rectangle to be at least `16x16`.
The menu popup that appears is then observed as a new raised surface; the menu
trigger click itself remains an ordinary detail-window click.

### 6.3 Save All target

Reuse `mac_runtime.mjs:75-134`: unique OCR `儲存全部`/`Save All`, exact popup
ownership and layer/above-detail relation, popup/crop/label intersection,
`uncertainty + 4` erosion, and `16x16` minimum.

The native bridge may accept the Save All point only when all of these are from
the same fresh pair: popup window, detail window, capture frame, process
instance, AX state, OCR row, safe rectangle, and transaction permit. It posts
nothing if the popup is absent, duplicated, moved, replaced, occluded, or not
the window that would receive the event at that point.

## 7. Per-PID receipt and actual-point proof

Before posting, install a passive `CGEventTapCreateForPid` for the authenticated
LINE PID using `kCGTailAppendEventTap`, `kCGEventTapOptionListenOnly`, and only
the mouse-move/down/up event mask. Require `CGPreflightListenEventAccess()` to
be already true; do not request permission during a transaction.

Each posted event carries a unique `kCGEventSourceUserData` token. The receipt
must record, for each expected event:

- event type and order;
- `CGEventGetTimestamp`;
- `CGEventGetLocation` from the delivered event;
- source user-data token;
- `kCGEventSourceUnixProcessID` and `kCGEventTargetUnixProcessID`;
- `kCGMouseEventWindowUnderMousePointer`;
- `kCGMouseEventWindowUnderMousePointerThatCanHandleThisEvent`;
- tap placement and listener identity;
- the expected point, expected PID/window/layer, and fresh surface facts.

An independent `AXUIElementCopyElementAtPosition` hit test is performed at the
same point using `AXUIElementCreateApplication(pid)` and the fresh AX state. It
must return the expected album/title/menu/control node for the album-card,
menu-trigger, and Save All row checks. If LINE does not expose the exact expected
node, the result is `AX_UNAVAILABLE` and the bridge refuses. This condition may
not be waived by the planner or by the local adapter; no AX action API is used
as a substitute for the actual mouse event.

The bridge computes:

`P_req_global = capture_origin_pt + P_req_capture / scale`

`P_event_capture = (P_event_global - capture_origin_pt) * scale`

and records `dx`, `dy`, Euclidean error, and Chebyshev error. The inverse
mapping must use the same frozen `CaptureGeometry` that produced the request.

The event is accepted as routed only when all of the following hold:

1. the tap observed the move, down, and up in the expected order;
2. the source-user-data token and target PID match;
3. `kCGMouseEventWindowUnderMousePointerThatCanHandleThisEvent` equals the exact
   expected surface; a missing field is `UNKNOWN`, not a fallback;
4. the actual event point is within the measured `<=2px` upper bound;
5. the actual point remains inside the eroded target safe rectangle;
6. the fresh Window Server and AX hit tests agree with the expected surface;
7. no competing physical or synthetic event is observed between hover and down.

If these facts are incomplete after a mouse-down has been posted, the outcome is
`UNKNOWN`, never a retry. Save All is at-most-once. If the facts fail before the
down event, only the permitted hover may have been posted and the outcome is
`REFUSED_ZERO_CLICK`.

The receipt is retained as an immutable artifact and referenced by the existing
dispatch receipt path. A new reviewed receipt version may add a
`native_click_receipts` reference, but it must not modify ledger counts,
historical records, or the meaning of an existing `UNKNOWN` intent.

## 8. Conservative `<=2px` bound method

All component bounds below are measured in capture pixels or conservatively
converted to them. A missing or non-finite term is a refusal, not zero.

`U_total_px = U_ocr + U_transform + U_motion + U_event_round + U_hit_test`

Minimum rule:

`U_total_px <= 2`

`safe_margin_px >= max(2, U_total_px) + 4`

`eroded_target.width >= 16 and eroded_target.height >= 16`

`max(|actual_x - requested_x|, |actual_y - requested_y|) <= U_total_px`

`euclidean(actual, requested) <= U_total_px`

The implementation must not recycle the existing constant `2` as if it were
already a proof of every component. If `2` is a composite uncertainty, it must
be decomposed and re-measured. Component methods:

- `U_ocr`: maximum declared label-bound uncertainty plus OCR anchor residual on
  the live frame, independently bounded from the label geometry.
- `U_transform`: maximum residual of the SCK/CUA/window/display inverse
  transform over at least three distributed anchors, with scale and origin
  checks; the current code's `<=2` transform residual is not a substitute for a
  total bound.
- `U_motion`: conservative upper bound from the last fresh capture to the
  post-hover check, including the configured frame/point tolerance and the
  measured display scale. A moved or animated popup refuses rather than
  consuming an allowance if the movement cannot be bounded.
- `U_event_round`: measured difference between the requested CGEvent location
  and the tap's actual location, including coordinate rounding/scale.
- `U_hit_test`: measured difference between the intended target boundary and
  the Window Server/AX hit-tested surface at the point. Ambiguity at a boundary
  refuses.

The safe rectangle is computed in the same capture space as the OCR/target
witnesses, then independently mapped for the native request and back-mapped for
the event receipt. No screen-space point derived from a different frame may be
used as the request.

## 9. Unbounded or not-yet-proven error terms

The following are deliberately unresolved in this plan and must fail closed
until measured under the approved probe/implementation round:

- real LINE OCR label-bound precision and row uniqueness under the actual
  language, font, scale, and popup animation;
- SCK content-rectangle, CUA crop, window frame, display origin, and backing
  scale mapping residual, including negative/multi-display origins;
- popup/window movement between capture, reservation, hover, and down;
- CGEvent coordinate rounding and any implicit Window Server transform;
- Window Server hit-test behavior at the popup/card boundary;
- whether synthetic events populate the two mouse window fields;
- whether `CGEventTapCreateForPid` reliably observes events posted with
  `CGEventPost(.cghidEventTap)`;
- whether LINE exposes the popup row or its controls through
  `AXUIElementCopyElementAtPosition`;
- physical user-input interleaving and popup animation timing;
- the effect of different display arrangements, Retina scale, and menu-bar
  coordinates.

Any of these that cannot be bounded or consistently observed is a hard stop.
It must not be replaced by a historical coordinate, a center-of-screen guess,
a shadow click, or a previous single success.

## 10. Minimal integration path

No new orchestrator, ledger, transaction framework, or second Save All path is
proposed. The smallest reviewed source delta is:

1. `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift`
   - add the explicit `SurfaceExpectation` and surface-aware topmost checks;
   - keep permit, intent, PID, process-start, post-hover, and at-most-once hooks;
   - add the passive receipt and request-bound posting facade;
   - retain the injectable sink for zero-event refusal tests.
2. `rev28/Sources/Rev28Core/Identity/WindowIdentity.swift`
   - replace unconditional `layer == 0` validation with expectation-driven
     ordinary/popup validation; never accept an arbitrary non-zero layer.
3. `rev28/Sources/Rev28Core/Geometry/Coordinates.swift`
   - only if required, add an explicit frozen capture-origin/scale context for
     the popup and event back-mapping; do not create a second coordinate space.
4. `rev28/Sources/rev28ctl/main.swift`
   - add a reviewed bounded native click/actuation command or a pure request
     endpoint; leave `live-execute` disabled; no arbitrary click CLI.
5. `scripts/line_backup_cua_adapter.mjs`
   - route only `album_open`, menu trigger, and Save All through the native
     bridge; preserve the existing chooser/download/verification path and
     preserve all existing fallback/refusal behavior.
6. `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs`
   - pass the native bridge and its exact evidence/permission callbacks into
     the runtime; do not change the A -> C1 -> B sequence.
7. `src/line_backup_batch/service.py`
   - accept and validate the reviewed native receipt reference in a new
     receipt version only if the existing strict receipt key set cannot carry
     it; no ledger/state semantic or quota change.

Expected source hashes in this planning base are recorded in section 12. Any
drift before implementation stops the work and starts a new source audit.

`two_album_entry.mjs` is intentionally expected to remain unchanged. If the
integration requires changing its A -> C1 -> B semantics, this Plan must be
revised and re-reviewed.

## 11. Positive and negative tests

### 11.1 Offline/synthetic positive tests

- A synthetic raised popup above a main test window receives the event at the
  expected point while the main window does not.
- A synthetic occluder above the popup prevents delivery and the bridge returns
  `REFUSED_ZERO_EVENT` before mouse-down.
- A unique token/event order produces a complete immutable receipt with
  `P_event` and target-window fields.
- An ordinary layer-0 app receives only its own event; a positive-layer popup is
  accepted only when its exact expected relationship is supplied.
- Multi-display, negative-origin, Retina-scale, and scale-mismatch fixtures
  either produce a bounded inverse transform or refuse.

### 11.2 Offline/synthetic negative tests

- Point outside the eroded safe rectangle -> zero event.
- Wrong PID, window ID, bundle, process instance, display, or layer -> zero event.
- Popup window duplicated, absent, moved, replaced, covered, or not immediately
  above detail -> zero event.
- Stale frame, stale permit, expired permit, consumed permit, or changed target
  binding -> zero event.
- Missing post or listen permission -> zero event, `BLOCKED_PERMISSION`.
- EventTap unavailable or does not observe the token -> no mouse-down; if it
  occurs after mouse-down, `UNKNOWN` and no replay.
- Event point outside `U_total_px` or target boundary -> `UNKNOWN`, no replay.
- AX hit test returns another element or is unavailable when required -> refuse.
- A physical competing event between hover and down -> refuse before down.
- `CGEventPostToPid` or an active/modifying tap is used -> hard refusal in the
  implementation contract.

### 11.3 Approved reversible LINE probe (not run in this round)

Only after this Plan and exact source/runtime are approved, and only under the
Owner's foreground handoff, run a bounded real probe with no Save All:

1. native click the unique album-name target and verify a fresh detail window;
2. native click the unique three-dot target and verify the exact raised LINE
   popup/window relationship;
3. hover the unique Save All row without mouse-down, record the event/tap/AX/
   window fields, then dismiss via a separate title-surface click;
4. verify popup closure, detail identity, and zero Save All dispatch count.

This probe is `NOT_RUN` in the planning round. A pass is reversible-input
evidence only; it is not a Save All PASS.

### 11.4 Formal A/B validation (not run in this round)

After External Plan approval, exact source review, a valid grant, independent
E2E setup, and fresh Owner handoff, the existing runtime may execute A's one
cap-1 lifecycle. Only after A's complete original-file SHA-256, ImageIO decode,
VERIFIED/readback/release may it perform the real C1 scroll and open a distinct
eligible B. B uses a separate cap-1 lifecycle and a separate valid intent.

No historical VERIFIED album, PR #14 HUMAN_A_ONLY path, A56 grant, or used 2/2
quota may be reused. If no distinct eligible B exists, the result is
`NO_ELIGIBLE_TARGET`, never a fabricated two-album success.

## 12. Source and evidence index

Workspace root for every relative path below:

`/Users/hsiaojohnny/.codex/worktrees/3c27/Line_backup`

| Evidence | Relative path | SHA-256 |
| --- | --- | --- |
| Effective governance | `AGENTS.md` | `8ea0cf8a75a239d1a849ac471756027970645821d73b0068c4da3103557fb3d2` |
| Native actuator | `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift` | `bf7bfb4d9dc3db108e962649a110dd40c999286c1398745480d1a6ff44e3b9f8` |
| Coordinate contract | `rev28/Sources/Rev28Core/Geometry/Coordinates.swift` | `f9b77879cfc7abf596de4f0ab562ba8e7506bde2673844a94d37d96b4b0d564c` |
| Disabled legacy entry | `rev28/Sources/rev28ctl/main.swift` | `1f6724e6f1a1149074177251253517d72d3719550c9dd5725289cf4f930baddc` |
| AUTO CUA adapter | `scripts/line_backup_cua_adapter.mjs` | `1b41f7c87b65692a69c229bce7e4db3f5c0a82f0f1349d776cf8bcb3254bde5d` |
| Runtime/AUTO wiring | `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs` | `a1d2c16528b5584a02780045384afb535715287925cabccdaab2111d03ffe27d` |
| A/C1/B sequence | `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs` | `f5981c071709203adc2c1cbbc8d5779a77eb1bc37cf0eb8e0444aa5ee21ab277` |
| Popup analyzer | `harness-development/line-two-album-pilot-20261014/mac/analyzer.mjs` | `2c22180971843ed1e379bc69f23ad4990bf8d162de355277c4e6f624a4ef1ba7` |
| Popup classifier | `harness-development/line-two-album-pilot-20261014/mac/classifier.mjs` | `ab4f6ed1bff0cd75f14de594703d7083d5ce571243dd3c5043e0d818725423d6` |
| Window identity | `rev28/Sources/Rev28Core/Identity/WindowIdentity.swift` | `e9a6a82672dc0d1d2eb2b5dbff47b878bd7eb625a7d6c6fee915e23f985b7edf` |
| Card target | `src/line_backup_batch/observations.py` | `c519b3f962556e1655157e6df0c089fd1f496c06dfa19addfb593d13a42792a6` |
| Receipt/authority validation | `src/line_backup_batch/service.py` | `9b3978052717a9a06a072cc367c224233c5f90f49625058a5938c736a42c98f0` |
| Synthetic routing test | `evidence/20260925-rev28-native-closed-loop/harness/runs/HARNESS-20260925-104146/items/04-quartz-routing.json` | `1b79cee5fe1fb179886d8e08465bb89df8eeb227c8e72b4f9fe66ddbf6906acc` |

The synthetic routing evidence proves only that a synthetic raised popup can
receive a posted input while an occluder does not. It does not prove LINE
identity, LINE popup ownership, a real LINE event, Save All, or `<=2px`.

Test paths for the reviewed implementation are:

- `rev28/Tests/Rev28CoreTests/ActuationReadinessTests.swift`
- `rev28/Tests/Rev28CoreTests/WindowIdentityTests.swift`
- `rev28/Tests/Rev28CoreTests/CoordinateTransformTests.swift`
- `rev28/Tests/Rev28CoreTests/AdversarialMatrixTests.swift`
- `tests/test_cua_adapter.mjs`
- `tests/test_batch_lifecycle.py`

## 13. Rejection conditions before any irreversible event

The bridge and adapter must refuse, or mark `UNKNOWN` without replay after an
already-posted down event, on any of:

- source, runtime, grant, Plan, or review hash drift;
- missing post/listen/AX/SCK permission, or nil EventTap;
- non-unique or stale album card/title/menu trigger/row;
- target uncertainty above `2`, safe margin below `uncertainty + 4`, or safe
  intersection below `16x16`;
- PID, process-start, bundle, window ID, display ID, layer, popup-above-detail,
  topmost, alpha, or on-screen mismatch;
- popup animation/movement/replacement or another intersecting window above it;
- event/tap field missing, token/order mismatch, point outside the measured
  `<=2px` bound, or AX hit test disagreement;
- permit absent, expired, already consumed, or bound to another candidate;
- existing intent absent, already dispatched, or `UNKNOWN`;
- Save All attempted after any replay ambiguity;
- destination non-empty, duplicate/historical album selected, protected
  VERIFIED/65-album overlap, or no distinct eligible B;
- any attempt to use `CGEventPostToPid`, an active event filter, a raw click CLI,
  or the disabled legacy `live-execute` route.

## 14. What this Plan claims and does not claim

Proven now:

- the relevant macOS APIs are declared by the installed SDK;
- real CGEvent posting and much of the safety scaffold already exist;
- LINE's current repository model requires a distinct positive-layer popup;
- the current AUTO adapter has no auditable native receipt;
- the existing layer-0 checks reject the modeled Save All popup.

Not proven now:

- that LINE will expose the required event/window/AX fields for synthetic input;
- that the popup is bound strongly enough in a real live frame;
- that the actual event lands within `<=2px` for every required term;
- that all permissions are present on the target Mac;
- that A and B can be completed through the existing runtime;
- that any Save All has occurred in this round.

`REAL_LINE_INPUT=0`, `REAL_SAVE_ALL_DISPATCH=0_AS_LAST_RECORDED`, and
`PRODUCT_CODE_CHANGED=NO` for this planning round.

## 15. Handoff

This file is the independent `NATIVE_AUTO_CLICK/1` review candidate. The Owner
must transfer the exact Plan HEAD, committed file SHA-256, this evidence index,
and the prior AUTO review link to the External Chief Plan Reviewer. No
implementation, grant, LINE GUI operation, intent, or Save All may start until
the external reviewer returns `APPROVE_PLAN` for these exact bytes. A later
`CHANGES_REQUIRED`, `BLOCKED`, or source hash drift invalidates the handoff and
requires a new frozen revision.
