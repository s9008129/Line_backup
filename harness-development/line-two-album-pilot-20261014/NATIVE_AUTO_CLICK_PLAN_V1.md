# NATIVE_AUTO_CLICK/1 — macOS Native Click Feasibility Plan

Status: `AMENDED_PENDING_BOUNDED_EXTERNAL_REREVIEW`

Verdict: `SUPPORTED_NATIVE_AUTO_ROUTE_CANDIDATE_FEASIBILITY_FIRST`

This plan is a bounded implementation proposal, not an approval, not an
implementation, and not a LINE E2E result. It does not claim that a `<=2px`
proof has been demonstrated or that the LINE popup has been clicked. Every
unmeasured condition below remains fail-closed.

This revision resolves only External Chief review items C1-C4. It deliberately
changes the rollout order to F0/F1 feasibility first, conditional F2 product
wiring second, and F3 formal real-LINE E2E last. No product source is changed
by this planning amendment.

## 1. Frozen inputs and authority

- Repository: `s9008129/Line_backup`
- Planning worktree: `/Users/hsiaojohnny/.codex/worktrees/3c27/Line_backup`
- Planning branch: `plan/native-auto-click-20261019`
- AUTO base: `516932dfcee94b662082b909b7980fc2483ab9c0`
- Prior AUTO Plan HEAD: `c563cba5a353a85b3cd0da34cc0e9dc12e3cbd40`
- Prior AUTO Plan SHA-256: `31986a0cbe00e2267704073b9d4ddfa24dd3c7743c62b7a11649d9131d7d91a9`
- Prior AUTO Plan PR: <https://github.com/s9008129/Line_backup/pull/15>
- Native Plan PR: <https://github.com/s9008129/Line_backup/pull/16>
- Prior native review: <https://github.com/s9008129/Line_backup/pull/16#pullrequestreview-5571003472>
- Prior native reviewed HEAD: `4d40d6c62e99bb749507dec4de257b9a1282e777`
- Prior native Plan SHA-256: `3bef9f2f0fab4e4f530e08f19cf529e8bbcd92060e340aee50e5defd89258c1f`
- Prior native verdict: `CHANGES_REQUIRED` for C1-C4 only
- Effective `AGENTS.md` SHA-256: `8ea0cf8a75a239d1a849ac471756027970645821d73b0068c4da3103557fb3d2`
- Host: macOS 27.0.1 build 26A434; Xcode 26.6; SDK `MacOSX26.5.sdk`
- `GOAL_CRITICALITY=CRITICAL`
- `EVIDENCE_ROLE=PLANNER_PROPOSAL_ONLY`
- `CLOSURE_GATE=EXTERNAL_PLAN_REVIEW + EXACT_CODE_REVIEW + INDEPENDENT_E2E`
- Model-routing policy: `ollama_cloud/deepseek-v4.1-flash:1017`; no unverified
  subagent, Codex-native model, or other-provider fallback.

The exact bytes of this committed file are the reviewed Plan bytes. Their
SHA-256 is recorded outside the file in the commit/PR handoff so that the hash
is not self-referential. No product source, grant, ledger, protected state,
LINE GUI, or Save All is changed by this planning round.

### 1.1 C1-C4 amendment resolution

| Item | Resolution in this revision |
| --- | --- |
| C1 | `PRE_DOWN_ADMISSION` and `POST_DOWN_AUDIT` are separate contracts. The former must prove the target-specific coordinate bound, constructed event location, fresh surface identity, authorization and refusal conditions before any mouse-down. The latter is independent evidence only and can never retroactively authorize a click. |
| C2 | F1 is a reversible, non-LINE, nontransactional native feasibility gate. It must prove per-PID tap callbacks, event fields, source token, chronology, coordinates, recipient delivery and activated-control semantics on controlled ordinary/raised/occluded test surfaces. Missing required capability is `UNSUPPORTED`. A later separately approved LINE identity/AX observation gate is still required for the popup row. |
| C3 | Each target kind retains its own existing geometry contract. No generic post-erosion `16x16` rule is imposed on album-card titles. The menu trigger and Save All retain their existing `u+4`, `16x16`, safety-intersection and popup-ownership rules; the global `<=2px` condition remains. |
| C4 | The existing Python project lifecycle/ledger/intent is the only transaction authority. The native layer may consume one already-durable, uniquely bound, single-use input authorization derived from that intent and its existing `dispatch_inputs` reservation. It may not create another Save All reservation, rearm permission, write the project ledger, or replay `UNKNOWN`. |

### 1.2 Stage order

1. `F0`: exact source/config/SDK readback plus offline contract and negative
   tests. No runtime input and no product wiring.
2. `F1`: the smallest isolated native feasibility executable against controlled,
   non-LINE, nontransactional test surfaces. Any missing mandatory capability
   stops the route as `UNSUPPORTED`.
3. `F2`: conditional product wiring only after F1 positive evidence and a
   separately reviewed scope. A later reversible LINE identity/AX probe remains
   a separate approved gate.
4. `F3`: formal A/B real-LINE E2E only after exact code review, runtime/controller
   admission, valid grants, and Owner foreground handoff.

No F2 source path may be changed merely because it is listed later in this Plan.
F1 must pass first.

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
- durable pre-input hooks through `PersistentTransactionOwner` in the legacy
  `rev28ctl` path;
- `reserveSaveAll()` and `markSaveAllAttemptedWithRevalidationID()` in that
  legacy path;
- a test-injectable sink that can prove refusal posts zero events.

This is a strong starting point, but it is not the AUTO route. The legacy
`rev28ctl live-execute` entry remains disabled at
`rev28/Sources/rev28ctl/main.swift:124-130`; it must not be revived or treated
as an available shortcut. The embedded `PersistentTransactionOwner` Save All
reservation hooks are not an acceptable second authority for AUTO; F2 must keep
them out of the AUTO path rather than calling both Python and Swift ownership
mechanisms.

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
5. No passive per-PID event receipt exists. `CGEventGetLocation` at creation
   proves the constructed event location, not delivery, recipient handling, or
   row activation.
6. No AUTO source currently translates a fresh frame-bound target into this
   actuator, and no accepted dispatch receipt can carry native receipt evidence.
7. The current actuator's post-hover/receipt facts are not yet a pre-mouse-down
   proof contract, and the runtime presence of the EventTap/window fields has
   not been measured.

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
  and the fresh front-to-back relationship that places the popup immediately
  above the exact detail window.

Before both the hover and the down event, the topmost alpha-positive window
containing the point must be the exact expected surface. For the popup, no
other alpha-positive intersecting window may sit above it. An opaque or
ambiguous window above the target refuses dispatch. A popup animation or window
replacement between capture, permit, hover, and down refuses dispatch.

The expectation must be re-evaluated from a fresh `CGWindowListCopyWindowInfo`
sample and a fresh LINE window/AX/SCK frame. Cached layer values, a historical
popup ID, or a bare `layer > 0` match without the exact above-detail relation are
inadmissible. F1 must first prove that the controlled raised test surface can be
modeled and observed without relying on the current unconditional layer-0 code.

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
- target-kind-specific bounds and the existing verified target point.
- `U_pre_px`, its measured component vector, and the target-specific safe-margin
  rule defined below.
- immutable reference to the existing intent and persisted single-use native
  authorization described in section 10.3; never a caller-created permission.
- source hashes for the frame, AX evidence, OCR/popup evidence, and transaction
  references.

The bridge refuses if the target is not unique, the target-specific geometry is
not satisfied, any uncertainty term is missing or non-finite, `U_pre_px > 2`, or
the constructed event location is not inside the target-specific admissible
region. A universal `16x16` post-erosion rule must not be applied to every target
kind. It refuses a point merely because OCR once reported the expected text.

### 6.1 Album-card target

Reuse `observations.py:707-740`: unique card fingerprint, fully visible card,
unique OCR title witness, uncertainty exactly `2`, no enabled-button overlap, and
the center of the verified title rectangle. The existing contract accepts a
title rectangle with width `>= 16` and height `>= 2u + 1` (therefore height
`>= 5` at `u = 2`). That contract is preserved.

No new generic `16x16` post-erosion rule and no new `u + 4` erosion rule are
imposed on `album_card`. The selected center and the global `<=2px` pre-down
bound must still be proven. If the fresh title witness or event-construction
proof cannot support that bound, `album_card` refuses; it does not fall back to
a guessed card center or silently enlarge the title rectangle.

### 6.2 Three-dot/menu trigger

Preserve the existing fresh `PIXEL_STRUCTURE` contract in
`mac_runtime.mjs:24-72`: unique actual pixel-dot triple, structural component
limits, safe interior, uncertainty `u = 2`, erosion by `u + 4`, and an eroded
interior of at least `16x16`. The native bridge must bind that exact target
rectangle to the same fresh detail-window identity and must not strengthen or
weaken those checks without new representative evidence and re-review.

The menu popup that appears after the trigger click is a new raised surface. It
must satisfy `SurfaceExpectation.saveAllPopup` before any Save All mouse-down;
the trigger click itself remains an ordinary detail-window click.

### 6.3 Save All target

Reuse `mac_runtime.mjs:75-134`: unique OCR `儲存全部`/`Save All`, exact popup
ownership and layer/above-detail relation, popup/crop/label intersection,
`uncertainty + 4` erosion, and `16x16` minimum.

The native bridge may accept the Save All point only when all of these are from
the same fresh pair: popup window, detail window, capture frame, process
instance, AX state, OCR row, safe rectangle, and transaction permit. It posts
nothing if the popup is absent, duplicated, moved, replaced, occluded, or not
the window that would receive the event at that point.

The popup's positive layer is necessary but not sufficient. The target must be
the exact popup immediately above the exact detail window, topmost among
alpha-positive windows intersecting the point, and the OCR row must be unique
inside that exact popup. A post-down Window Server field cannot repair a missing
pre-down popup identity.

### 6.4 Target-kind invariant summary

| Target kind | Existing geometry preserved | New generic rule |
| --- | --- | --- |
| `album_card` | Unique fully visible card, unique OCR title, `u=2`, title width `>=16`, title height `>=2u+1`, no enabled-control overlap, center point | None; `16x16`/`u+4` must not be added without fresh evidence and re-review |
| `menu_trigger` | Fresh `PIXEL_STRUCTURE`, unique dot triple, existing safe interior, `u+4` erosion and `16x16` minimum | None |
| `save_all` | Unique OCR row, exact positive-layer popup above exact detail, popup/crop/label intersection, `u+4` erosion and `16x16` minimum | None |

The global hard condition remains `U_pre_px <= 2` for every irreversible
mouse-down. Target-specific checks are cumulative; this table never authorizes
skipping one of them.

## 7. F0 and F1 feasibility-first gate

### 7.1 F0: frozen readback and offline contracts

F0 performs no runtime input and no product wiring. It must:

1. Read back the exact worktree, branch, HEAD, effective `AGENTS.md`, installed
   SDK declarations, and source hashes in section 12. Any drift stops the gate.
2. Encode separate `PRE_DOWN_ADMISSION` and `POST_DOWN_AUDIT` records so a
   post-event field cannot satisfy a missing pre-event condition.
3. Unit-test the three target-specific geometry contracts in section 6.4,
   including the album-card `width >= 16` / `height >= 2u+1` rule and the existing
   menu-trigger and Save All `u+4` / `16x16` rules.
4. Unit-test refusal ordering: a failure before any event yields
   `REFUSED_ZERO_EVENT`; a failure after a hover but before mouse-down yields
   `REFUSED_ZERO_CLICK`; a failure after mouse-down yields
   `UNKNOWN_LATCHED_NO_REPLAY`.
5. Prove with the injectable sink that every pre-down refusal posts zero
   mouse-down and mouse-up events. No post-down receipt may override that fact.

F0 can prove only local contract behavior. It cannot prove EventTap delivery,
Window Server field population, application reception, or LINE AX visibility.
Those are F1 or later gates.

### 7.2 F1: minimal non-LINE native feasibility test

F1 is the first executable feasibility stage. It is isolated, reversible,
nontransactional, and zero-product-wiring:

- no LINE process, LINE window, LINE GUI, album, menu, Save All, grant, intent,
  ledger, chooser, download, or protected state;
- no call to `runTwoAlbumPilot`, `PersistentTransactionOwner`, Python lifecycle,
  or any Save All reservation;
- test events target only controlled test windows owned by `rev28harness` and
  `rev28occluder` processes;
- the only native event route under test is
  `CGEventPost(.cghidEventTap)`; `CGEventPostToPid` and active/modifying taps are
  forbidden.

The feasibility executable must install a `CGEventTapCreateForPid` tap for the
controlled target PID with `kCGTailAppendEventTap`, `kCGEventTapOptionListenOnly`,
and only the mouse-move/down/up event mask. It must use nonprompting
`CGPreflightPostEventAccess()` and `CGPreflightListenEventAccess()` and must not
request permission during the test. A missing permission or nil tap is
`F1_UNSUPPORTED`, not a prompt or fallback.

The first executable F1 gate (`F1-G0`) requires all of the following on the
controlled ordinary surface before any later F1 case may run:

1. the tap is created for the exact test PID at tail/listen-only placement;
2. synthetic mouse-move/down/up events are observed in the expected order;
3. each observed event has a timestamp and location;
4. the unique `kCGEventSourceUserData` token is preserved and matches the
   constructed event;
5. `kCGEventSourceUnixProcessID` and `kCGEventTargetUnixProcessID` are available
   and match the controlled source/target;
6. `kCGMouseEventWindowUnderMousePointer` and
   `kCGMouseEventWindowUnderMousePointerThatCanHandleThisEvent` are available
   and identify the expected controlled window;
7. `CGEventGetLocation` after construction/serialization matches the selected
   point within its declared pre-down component bound;
8. the test application records the delivered event at the same control, and
   the handler reports the activated control only for the intended surface;
9. the tap chronology and source token distinguish the posted move/down/up from
   unrelated input.

The first unavailable or mismatched mandatory field/API stops the entire stage
with `F1_UNSUPPORTED` and records the literal field name in
`first_missing_capability`. Later partial passes cannot override this stop.

### 7.3 F1 proof classes and surfaces

F1 must record three separate evidence classes and must not substitute one for
another:

1. `OBSERVED_AT_TAP`: field population, token, point, PIDs, window fields, order
   and timestamps.
2. `DELIVERED_TO_APP`: the controlled application's independent event log
   showing which window/control received each event.
3. `ACTIVATED_CONTROL`: the controlled application's handler proves the intended
   control or row ran and the underlying/occluded control did not.

The test matrix uses a controlled ordinary layer-0 surface, a controlled raised
surface above a normal surface, and an occluder above the raised surface. It
must prove that the raised target can be addressed only with the exact expected
identity and that an occluder causes zero mouse-down under the pre-down
admission gate. These results validate the measurement method, not LINE popup
ownership.

The geometry test must compare `P_req_global`, the constructed event's
`CGEventGetLocation`, and the post-down tap location using one frozen
`CaptureGeometry`. The pre-down check is valid only when
`U_pre_px <= 2`. A post-down tap observation may confirm or contradict that
bound, but may never create the missing bound or retroactively authorize the
click.

Required F1 evidence includes a machine-readable JSON summary and raw logs under
`evidence/20261019-native-auto-click-f1/`. The summary must state each required
field as `PRESENT`, `ABSENT`, or `MISMATCH`, and each proof class separately.

Allowed F1 conclusions are only:

- `F1_SUPPORTED_CANDIDATE`: every mandatory controlled-surface capability exists
  and the pre-down contract is testable, with no LINE claim; or
- `F1_UNSUPPORTED`: the first missing/mismatched capability is named and all
  later stages stop.

An F1 pass is not a LINE approval, not a real `<=2px` result, and not authority
to begin F2.

## 8. `PRE_DOWN_ADMISSION` and `POST_DOWN_AUDIT`

### 8.1 `PRE_DOWN_ADMISSION`: authorization before irreversible input

`PRE_DOWN_ADMISSION` is a pure, fail-closed contract evaluated before the first
mouse-down. It must use only current facts available at or before that moment.
The record is immutable and contains:

1. exact Plan/source/runtime hashes and the F2/F3 review binding;
2. fresh frame/session/PID/process-instance/bundle/display/window identity;
3. the target-specific unique witness and geometry from section 6.4;
4. the frozen `CaptureGeometry` and forward/inverse coordinate derivation for
   the selected point;
5. `U_pre_px` and each measured component from section 9;
6. the constructed move/down/up event identities and their
   `CGEventGetLocation` values after `CGEventSetLocation`/serialization;
7. the unique `kCGEventSourceUserData` value used only to correlate events;
8. fresh topmost/alpha/layer/above-detail and addressability facts for the exact
   expected surface;
9. target-specific hit-test identity at the selected point and at conservative
   probes around the `U_pre_px` neighborhood;
10. the existing Python intent reference, the canonical authorization-binding
    fields, and the pre-down time bound. The opaque authorization hash is added
    after the one-shot Python claim and before mouse-down.

For `C1`, the selected point is the point encoded into the actual mouse-down
event. `CGEventGetLocation` on that constructed event is read back before
posting and must agree with the requested point within the declared serialization
term. This proves the selected event coordinate; it does not prove delivery or
application acknowledgement.

The pre-authorization admission succeeds only when all target-specific checks
pass, every error term is finite and measured, `U_pre_px <= 2`, the constructed
point is inside the target-specific admissible region, and the pre-down surface
identity is exact. Any missing term, ambiguity, stale evidence, unsupported
permission, or expired time bound refuses the click. The authorization claim is
then mandatory and is revalidated with the volatile binding before mouse-down.

The hover may be posted only after a pre-hover admission. After the hover and
before mouse-down, the full fresh admission is repeated. Only then may Python
consume the single-use input authorization. Immediately after that claim and
before mouse-down, Swift must revalidate the volatile binding against the
immutable admission record under a short fixed deadline: authorization hash,
target-binding hash, current frame/identity, topmost popup/card surface,
constructed event location and the absence of a competing event. Any mismatch
posts no down/up and burns the authorization. A local `ReadinessPermit`-style
guard may be retained as an additional one-shot guard, but it is not the
transaction authority and cannot replace the Python authorization.

The per-PID audit tap must be created and confirmed ready before the first hover;
if it is absent, no event is posted. Tap readiness is only a precondition for
collecting independent post-down evidence and never substitutes for any
pre-down admission field.

### 8.2 `POST_DOWN_AUDIT`: evidence only after dispatch

`POST_DOWN_AUDIT` begins only after a mouse-down has been posted. It records, as
independent evidence:

- the per-PID EventTap observation of move/down/up and their order;
- tap placement, listener identity, timestamps, delivered-event locations and
  source token;
- source/target PID and both mouse window-under-pointer fields;
- the controlled or LINE application-level event/chooser/download readback;
- Window Server/AX observations made after the event.

Those facts may confirm, contradict, or leave the dispatch unresolved. They may
**never** retroactively authorize a missing pre-down bound, replace a missing
pre-down authorization, or cause a second click. `CGEventPost` inserts the event
into the stream before subsequent taps; observing it in a tap is not proof that
the intended control or popup row handled it. Apple's public contracts are
[`CGEventPost`](https://developer.apple.com/documentation/coregraphics/cgevent/post%28tap%3A%29)
and
[`CGEventTapCreateForPid`](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreateforpid%28pid%3Aplace%3Aoptions%3Aeventsofinterest%3Acallback%3Auserinfo%3A%29).

### 8.3 Terminal semantics

| Point reached | Condition | Terminal outcome |
| --- | --- | --- |
| Before any posted event | Any admission, identity, permission, geometry, or authorization failure | `REFUSED_ZERO_EVENT` |
| After hover, before mouse-down | A fresh final admission fails | `REFUSED_ZERO_CLICK`; no down/up; no replay of a burned authorization |
| Mouse-down posted | Audit is absent, incomplete, mismatched, or chooser/download readback is unresolved | `UNKNOWN_LATCHED_NO_REPLAY` |
| Mouse-down not posted but authorization already consumed | Crash or indeterminate local sequence | `UNKNOWN_LATCHED_NO_REPLAY` on recovery; never rearm |
| Mouse-down posted and all independent facts confirm handling | Existing transaction evidence confirms the next phase | Existing dispatch/finalize path may continue; this is not a new authority |

The bridge never posts a second mouse-down after any row other than a confirmed
pre-down refusal. For Save All, at-most-once is enforced by the project ledger,
not by retry logic in Swift or JavaScript.

## 9. Conservative `<=2px` pre-down bound and unresolved terms

### 9.1 Bound method

All bounds are measured in capture pixels or in screen points with an explicit
conservative conversion. A missing, non-finite, or unmeasured term is a refusal,
not zero.

`P_req_global = capture_origin_pt + P_req_capture / scale`

`P_constructed = CGEventGetLocation(constructed_mouse_down)`

`P_constructed_capture = (P_constructed - capture_origin_pt) * scale`

The pre-down upper bound is:

`U_pre_px = U_localize + U_transform + U_motion + U_serialize`

Hard conditions for every target kind:

`U_pre_px <= 2`

`max(|P_constructed_capture.x - P_req_capture.x|,
       |P_constructed_capture.y - P_req_capture.y|) <= U_pre_px`

`Euclidean(P_constructed_capture, P_req_capture) <= U_pre_px`

Component definitions:

- `U_localize`: declared uncertainty of the exact target witness plus measured
  residual of the fresh OCR or pixel-structure localization. It is not assumed
  to be the existing literal `2` unless that literal is independently decomposed.
- `U_transform`: maximum residual of the same-frozen-frame SCK/CUA/window/display
  transform over at least three distributed anchors, including origin, scale,
  negative-origin and display checks. The existing `<=2` transform residual is
  not automatically the total bound.
- `U_motion`: conservative target/window movement bound from the latest fresh
  observation through the final pre-down check. A moving or animated target must
  be re-observed and bounded, or it refuses. Historical coordinates and
  unbounded waiting are forbidden.
- `U_serialize`: difference between the requested selected point and the
  constructed `CGEvent` location after setting location and reading
  `CGEventGetLocation`, including coordinate rounding and scale effects.

`U_hit_test` is not added as an unmeasured fudge term. Instead, the exact target
identity predicate must hold at the selected point and at conservative probes
whose offsets cover `U_pre_px`. If the target surface, popup relationship, or
control row is ambiguous anywhere in that neighborhood, the target refuses.
For a popup, this includes the exact above-detail relation and topmost
alpha-positive surface at every probe.

`P_tap` observed after mouse-down is an audit measurement. It may be compared
with `P_req` and `P_constructed` to confirm or contradict `U_pre_px`, but it
cannot supply or replace the pre-down bound.

### 9.2 Target-specific application

- `album_card` preserves the existing title geometry and center selection. The
  `<=2px` pre-down bound must hold, but no generic post-erosion `16x16` or
  `u+4` rule is added.
- `menu_trigger` preserves its existing safe interior, `u+4` erosion and
  `16x16` checks, in addition to `U_pre_px <= 2`.
- `save_all` preserves its unique popup row, exact popup identity and
  intersection, `u+4` erosion and `16x16` checks, in addition to
  `U_pre_px <= 2`.

The existing `u` used by a target's established contract is not silently
replaced by `U_pre_px`. Both the target-specific invariant and the global
pre-down bound must pass.

### 9.3 Unbounded or not-yet-proven terms

These remain hard stops until measured at the named gate:

- F1: whether `CGEventTapCreateForPid` observes events posted through
  `CGEventPost(.cghidEventTap)` for the controlled target PID;
- F1: whether synthetic events preserve `kCGEventSourceUserData`, timestamp,
  location, source/target PID, and both mouse window-under-pointer fields;
- F1: whether tap chronology and controlled application/control delivery can be
  distinguished reliably from unrelated input;
- F1/F2: coordinate rounding, display scale, multi-display origins and any
  Window Server transform not already bounded by the same-frame model;
- F2: real LINE OCR/title/row precision and uniqueness;
- F2: SCK content-rectangle, CUA crop, window frame, display and backing-scale
  residuals on the actual LINE instance;
- F2: popup/window movement between capture, hover and down;
- F2: Window Server hit-test behavior at the card/popup boundary and the exact
  positive-layer/above-detail relationship in live LINE;
- F2: whether LINE exposes the required Save All row through
  `AXUIElementCopyElementAtPosition`; if it does not and no independently
  reviewed substitute satisfies the mandatory row identity, the route is
  `UNSUPPORTED`;
- F2/F3: physical user-input interleaving, popup animation timing, and
  foreground changes.

Any unresolved term is a hard stop. It must not be replaced by a historical
coordinate, a center-of-screen guess, a shadow click, an application-level
readback used backwards, or a previous single success.

## 10. Conditional F2 product wiring and single transaction authority

### 10.1 Entry gate

F2 is not authorized by this Plan alone and must not begin as a seven-file
product refactor. It may begin only after:

1. this amended Plan receives external approval;
2. F1 returns `F1_SUPPORTED_CANDIDATE` with its exact evidence bundle;
3. the Owner/External Chief approves the bounded F2 source scope; and
4. no source, SDK or runtime hash has drifted.

An F1 failure stops at F1. A post-down EventTap field cannot revive a failed
pre-down contract.

### 10.2 Conditional source paths

The maximum F2 source set is:

1. `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift`
   - add `SurfaceExpectation` and surface-aware topmost checks;
   - add the pre-down admission facade, construction-time location readback,
     EventTap audit and one-shot sink;
   - keep the injectable sink for zero-event refusal tests;
   - isolate legacy `PersistentTransactionOwner` hooks so AUTO never calls them.
2. `rev28/Sources/Rev28Core/Identity/WindowIdentity.swift`
   - make layer validation expectation-driven for ordinary versus exact
     positive-layer popup; never accept an arbitrary non-zero layer.
3. `rev28/Sources/Rev28Core/Geometry/Coordinates.swift`
   - only if needed, add a frozen capture-origin/scale context for the same
     target/event inverse mapping; do not create a second coordinate space.
4. `rev28/Sources/rev28ctl/main.swift`
   - add a reviewed structured native-input endpoint or bounded command;
   - leave `live-execute` disabled and expose no arbitrary click CLI.
5. `scripts/line_backup_cua_adapter.mjs`
   - route only `album_open`, menu trigger and Save All through the structured
     bridge;
   - preserve chooser, download and verification behavior;
   - never retry after a post-down unknown.
6. `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs`
   - pass exact target/permission/evidence callbacks into the runtime;
   - do not change the A -> C1 -> bounded-scroll -> distinct-B sequence.
7. `src/line_backup_batch/service.py`
   - validate the single-use authorization and native receipt version;
   - preserve the existing intent, reservation, dispatch and ledger semantics.

`src/line_backup_batch/store.py` is not in the F2 change set. If the existing
durable intent and `dispatch_inputs` reservation cannot represent the single-use
binding without changing store semantics, F2 stops and returns for a new Plan
amendment. `src/line_backup_batch/observations.py`, `two_album_entry.mjs`,
popup analyzer/classifier and the chooser path are expected to remain unchanged.

Expected source hashes in this planning base are recorded in section 12. Any
drift before implementation stops the work and starts a new source audit.

### 10.3 Python is the only transaction authority

The existing Python project lifecycle/intent/ledger remains authoritative. The
native layer is an input executor only. It must not call
`PersistentTransactionOwner.reserveSaveAll()`,
`PersistentTransactionOwner.markSaveAllAttemptedWithRevalidationID()`, create a
Save All reservation, rearm a permission, mutate quota, or replay `UNKNOWN`.
Those old owner hooks remain legacy/non-AUTO unless F2 explicitly separates
them behind a testable compatibility boundary that cannot execute in AUTO.

The exact crossings are:

1. **Identity/evidence -> Python intent.** The existing JS/runner path presents
   the fresh frame identity, target-specific witness, pre-down uncertainty
   vector and a canonical target-binding hash to the existing Python lifecycle.
   `ProjectTransactionService.intent()` persists the normal single Save All
   intent and consumes no new reservation because the existing
   `dispatch_inputs`/`SAVE_ALL` reservation is already the sole slot.
2. **Python -> JS native authorization.** After the fresh post-hover admission
   and immediately before mouse-down, JS asks Python for a single-use
   native-input authorization bound to the current `action_id`, intent
   revision/hash, run/session, target-binding hash and the existing
   dispatch-inputs reservation. Python atomically verifies
   `INTENT_COMMITTED`, `dispatch_outcome=NOT_ATTEMPTED`, unconsumed reservation
   and matching target. On success it durably marks `INPUT_AUTHORIZED` (or the
   exact reviewed equivalent), emits the immutable authorization record and
   returns its opaque ID/hash. It does not reserve again.
3. **JS -> Swift pre-down execution.** Swift receives the authorization ID/hash
   plus the canonical target binding and pre-down contract hash. It revalidates
   the volatile facts against the already-passed admission, posts at most one
   move/down/up sequence, and emits immutable `pre_down` and `post_down`
   receipts. It never writes the project ledger and cannot mint another
   authorization.
4. **Swift/JS -> Python outcome.** The existing `dispatch` path receives the
   native receipt and ordinary chooser/download evidence. Python verifies the
   binding and records `RETURNED` only when the existing downstream evidence is
   confirmed. Any post-down missing/mismatch is `TRIGGER_UNKNOWN` /
   `UNKNOWN_LATCHED_NO_REPLAY`; the intent cannot be rearmed or replayed.

If authorization exists but no down was posted, the receipt may record
`REFUSED_ZERO_CLICK`; the consumed authorization remains burned and is not
reopened. If restart occurs after `INPUT_AUTHORIZED` without a complete
receipt, Python latches `UNKNOWN` in recovery and never dispatches a second
Save All.

### 10.4 F2 reversible LINE identity gate

After exact F1-positive source/runtime review, a separately approved diagnostic
permission and an Owner foreground handoff, run one reversible LINE probe with
zero Save All mouse-down:

1. native-click the unique album-name target and verify a fresh detail window;
2. native-click the unique three-dot target and verify the exact raised LINE
   popup/window relationship;
3. hover the unique Save All row without mouse-down, record EventTap, Window
   Server and AX/window facts, then dismiss from a separate title surface;
4. verify popup closure, unchanged detail identity, and zero Save All dispatch.

This is still not production Save All authority. If the required Save All row
cannot be identified through AX or an independently reviewed equivalent, stop
with `UNSUPPORTED`; do not hardcode `true`, invent an AX role, guess a point, or
start a follow-on research loop.

### 10.5 F3 formal two-album E2E remains unchanged

F3 starts only after F2 reversible evidence, exact code review, valid runtime
admission/grants and fresh Owner transaction handoff. It preserves:

- the existing `runTwoAlbumPilot` entry point and A -> C1 -> bounded scroll ->
  distinct B sequence;
- two sequential cap-1 lifecycles; `max_albums_per_run=1` is never changed;
- one A Save All at most once, full original-file SHA-256, complete ImageIO
  decode, VERIFIED/readback/release before any B intent;
- one different eligible B Save All under its own valid intent/grant;
- 239 historic VERIFIED records and the 65 manually backed-up album exclusion;
- at-most-once Save All, `UNKNOWN` no-replay, independent empty destination.

If no distinct eligible B exists, F3 returns `NO_ELIGIBLE_TARGET`; it never
fabricates a two-album success or reuses a closed grant.

## 11. Positive and negative tests

### 11.1 F0 offline and contract tests

Positive:

- a valid target-specific request produces a complete `PRE_DOWN_ADMISSION`
  record and exactly one constructed down/up pair in the injected sink;
- an album-card title with width `16` and height `2u+1` is accepted by the
  preserved card rule without requiring post-erosion `16x16`;
- the existing menu-trigger and Save All `u+4`/`16x16` fixtures remain accepted;
- a complete controlled post-down record is retained separately from the
  pre-down admission record.

Negative:

- missing or non-finite `U_pre` component -> `REFUSED_ZERO_EVENT`;
- constructed `CGEventGetLocation` outside `U_pre` or target-specific region ->
  `REFUSED_ZERO_EVENT`;
- missing/stale/wrong intent authorization -> zero event;
- any post-down field cannot change a pre-down refusal into acceptance;
- after hover, a final admission failure -> `REFUSED_ZERO_CLICK` and zero
  mouse-down/up;
- after mouse-down, any missing or contradictory audit ->
  `UNKNOWN_LATCHED_NO_REPLAY`;
- a second Save All reservation/rearm attempt is rejected by Python authority;
- stale, consumed or foreign authorization is rejected without replay.

### 11.2 F1 controlled native feasibility tests

Positive:

- the per-PID tail/listen-only tap receives move/down/up in order for the
  controlled target;
- source token, timestamp, location, source/target PID and both
  window-under-pointer fields are present and match the expected controlled
  surface;
- the controlled application independently logs the event and activates the
  intended control;
- a raised controlled surface is addressed only with its exact identity and
  the ordinary/underlying surface is not activated;
- multi-display, negative-origin, Retina-scale and scale-mismatch fixtures either
  produce a bounded construction/serialization residual or refuse.

Negative:

- permission preflight false, nil tap or missing mandatory field ->
  `F1_UNSUPPORTED` at the first unavailable item;
- tap callback absent, wrong order, wrong token, wrong PID or nondeterministic
  chronology -> `F1_UNSUPPORTED`;
- event observed at the tap but not delivered to the application -> separate
  failure, never treated as field-population success;
- delivered event does not activate the intended control -> separate failure,
  never treated as delivery success;
- occluder above the raised surface -> zero mouse-down under the pre-down gate;
- `CGEventPostToPid` or an active/modifying tap -> immediate unsupported.

### 11.3 F2 single-authority and integration tests

- exactly one existing Python intent exists for the action and the native input
  authorization binds to it;
- no Swift `reserveSaveAll`/`markSaveAllAttempted` call occurs on the AUTO path;
- the existing `dispatch_inputs` reservation is consumed once, with no second
  reservation or quota change;
- duplicate authorization claim, intent-state drift, stale target binding, or
  a consumed reservation refuses before mouse-down;
- a receipt with `mouse_down_posted=false` cannot produce a Save All;
- a post-down missing field latches `UNKNOWN` and a recovery attempt cannot
  replay;
- `runTwoAlbumPilot`, the A/C1/B order, chooser/download and verification paths
  remain unchanged.

### 11.4 Approved reversible LINE identity probe (not run in this round)

Only after F1 positive evidence, this Plan's approval, exact F2 source/runtime
review, a valid diagnostic permission and Owner foreground handoff, run the
bounded reversible probe in section 10.4. It has zero Save All mouse-down. A
pass is reversible identity evidence only, never a Save All PASS.

### 11.5 Formal A/B validation (not run in this round)

After F2 reversible evidence, exact code review, valid runtime admission and a
fresh Owner transaction handoff, the existing runtime may execute A's one cap-1
lifecycle. Only after A's complete original-file SHA-256, ImageIO decode,
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

Current review evidence is PR #16 review `5571003472`, bounded to the four items
in section 1.1. It is a review input, not a Controller receipt or execution
authorization.

### 12.1 Literal minimum F1 paths

These paths do not exist yet and may be created only after this amended Plan is
approved. F1 must not modify any product/AUTO source path.

New or changed:

- `rev28/Package.swift` — add only the isolated feasibility library, executable
  and test targets; do not add product dependencies.
- `rev28/Sources/Rev28NativeFeasibility/NativePreDownContract.swift` — pure
  pre-down/post-down records, target-kind invariants and refusal semantics.
- `rev28/Sources/rev28nativefeasibility/main.swift` — controlled non-LINE EventTap
  and coordinate feasibility probe.
- `rev28/Tests/Rev28NativeFeasibilityTests/NativePreDownContractTests.swift` —
  offline positive/negative contract tests.

Reused unchanged:

- `rev28/Sources/rev28harness/HarnessApp.swift`
- `rev28/Sources/rev28harness/main.swift`
- `rev28/Sources/rev28occluder/main.swift`

Evidence output directory:

- `evidence/20261019-native-auto-click-f1/`

F1 must not modify `rev28/Sources/Rev28Core`, `rev28/Sources/rev28ctl`,
`scripts/`, `src/`, `harness-development/line-two-album-pilot-20261014/*.mjs`,
or any LINE/protected-state path.

### 12.2 Conditional F2 test paths

After F1 positive and separately approved F2 scope, extend or add:

- `rev28/Tests/Rev28CoreTests/ActuationReadinessTests.swift`
- `rev28/Tests/Rev28CoreTests/WindowIdentityTests.swift`
- `rev28/Tests/Rev28CoreTests/CoordinateTransformTests.swift`
- `rev28/Tests/Rev28CoreTests/AdversarialMatrixTests.swift`
- `tests/test_cua_adapter.mjs`
- `tests/test_batch_lifecycle.py`

F2 must also record the reversible LINE identity/AX evidence from section 10.4
outside product source and without a Save All mouse-down.

## 13. Rejection conditions before any irreversible event

The bridge and adapter must refuse, or mark `UNKNOWN` without replay after an
already-posted down event, on any of:

- source, runtime, grant, Plan, or review hash drift;
- F0 not passed, F1 not `F1_SUPPORTED_CANDIDATE`, or any F2/F3 prerequisite
  absent;
- missing post/listen/AX/SCK permission or nil EventTap; any first missing F1
  capability is `UNSUPPORTED`, not a reason to continue;
- non-unique or stale album card/title/menu trigger/row;
- `U_pre_px` missing/non-finite or above `2`; target-specific card dimensions
  not satisfied; or, where the existing menu/Save All contract applies,
  safe margin below `u + 4` or eroded intersection below `16x16`;
- PID, process-start, bundle, window ID, display ID, layer, popup-above-detail,
  topmost, alpha, or on-screen mismatch;
- popup animation/movement/replacement or another intersecting window above it;
- constructed `CGEventGetLocation` outside the declared bound, or pre-down
  Window Server/AX hit-test disagreement over the uncertainty neighborhood;
- EventTap unavailable or unable to observe the hover in the expected token/order
  before mouse-down;
- any post-down event/tap field used as a substitute for a missing pre-down
  condition;
- permit absent, expired, already consumed, or bound to another candidate;
- existing Python intent/authorization absent, foreign, expired, already
  consumed, already dispatched, or `UNKNOWN`;
- any attempt by Swift/JS to create a second Save All reservation, rearm a
  permission, write project quota/ledger state, or continue from `UNKNOWN`;
- Save All attempted after any replay ambiguity, or any second mouse-down after
  an indeterminate post-down sequence;
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

- that `CGEventTapCreateForPid` observes the controlled or LINE events as needed;
- that synthetic events preserve the required token/PID/window fields;
- that the controlled application receives and activates the intended control;
- that the pre-down bound method is realized by the future F1 executable;
- that the popup is bound strongly enough in a real live frame;
- that LINE exposes the required Save All AX identity;
- that the actual event lands within `<=2px` for every required term;
- that all permissions are present on the target Mac;
- that A and B can be completed through the existing runtime;
- that any Save All has occurred in this round.

The only plan-level claim resolved here is that C1-C4 have explicit,
target-specific, feasibility-first contracts. F0/F1 have not been run, F2 is not
authorized, and no LINE input or Save All occurred.

`REAL_LINE_INPUT=0`, `REAL_SAVE_ALL_DISPATCH=0_AS_LAST_RECORDED`, and
`PRODUCT_CODE_CHANGED=NO` for this planning round.

## 15. Handoff

This file is the amended `NATIVE_AUTO_CLICK/1` review candidate for a bounded
re-review of C1-C4 only. The Owner must transfer the exact new Plan HEAD,
committed file SHA-256 and PR #16 link to the External Chief Plan Reviewer.

Approval of these bytes permits only the scoped F0/F1 feasibility work described
here. It does not authorize F2 product wiring, a LINE GUI probe, a grant, an
intent, a Controller receipt, a Save All, or an E2E claim. F2 and F3 remain
separate gates. A later `CHANGES_REQUIRED`, `BLOCKED`, `UNSUPPORTED`, or source
hash drift invalidates this handoff and requires a new frozen revision.
