# Phase A environment observations — 2026-09-29 06:22–06:27 +0800

Scope: read-only reconnaissance before any real `live-preflight`. No LINE GUI input, no menu
clicks, no authorization consumption, no Phase B intent. Production Save All / destination
counters stay 0 / 0 and the one-shot entitlement is untouched.

## Capability context (this Mac, this terminal's launch context)

- `capability-probe-record.json` (SHA-256 `87ee88c76b7c0a45b3567bd3dd9f07511789a7b0d3b1be612cf179d246b38127`)
  — `rev28probe` run at 2026-09-29T06:22:44+0800:
  `trust ax=true screenCapture=true postEvent=true`; ScreenCaptureKit `status=OK` (21 windows /
  1 display); Vision `status=OK` (synthetic-image exact match); Quartz event construction OK;
  no mouse/keyboard events posted.
- The probe ran from the same terminal/launch context as `rev28ctl`, and macOS evaluates TCC for
  the launched binary's responsible process, so `rev28ctl live-preflight` inherits these grants.

## LINE instance (read-only inventory, 2026-09-29T06:26:48+0800)

- `line-window-inventory.txt`:
  - LINE.app running, pid 54034, started 2026-09-29T06:17:54+0800. (The previous implementer
    turn launched it while investigating Phase A config readiness; recorded as an
    observation-adjacent reversible action — app activation only, no AX events posted.)
  - Exactly one on-screen layer-0 window: window 6179, bounds `17,516 242x169` pt, AX title empty.
  - Frontmost application: LINE.
- A read-only `screencapture` at 06:22 and a crop of that window (not archived: it contains the
  account e-mail and a login QR code) show LINE's **login / welcome screen**: e-mail and password
  fields, disabled 登入, 使用行動條碼登入 QR, 使用智慧手機登入. The LINE session is signed out on
  this Mac; there is no target chat or album surface on screen.

## Consequence for Phase A (fail closed, no attempt fired)

A real `live-preflight` today cannot produce Phase A evidence: with LINE signed out the composed
pre-save sequence cannot reach TARGET_ALBUM_LOCATED or beyond (expected named refusal at
GROUP_READY). Running it now would only capture private login material without advancing the
blocker, so it was deliberately not executed. Nothing irreversible was armed or consumed.

## Prerequisites for the next real Phase A attempt (dependency-correct)

1. Owner signs LINE in (QR or e-mail) and opens group 旻謙允禎成長日記 with the
   `2024/05/13～05/17` album list visible.
2. Exactly one on-screen layer-0 LINE window. The reviewed rev27 AX dump
   (`evidence/20260921-rev27-save-all/attempt-07/s11c-preclick-ax.json`) shows LINE can have
   several layer-0 windows at once; the observation session refuses a non-unique main window
   (`targetWindowNotUnique`).
3. A fresh runID plus fresh evidence / staging / ledger / checkpoint / goal-slot directories:
   Phase A publication is append-only per run directory, and `live-preflight` refuses a run
   directory that already carries `phase-a.json`.
4. Real frozen menu-surface geometry (`menuBoundsCapture` / `addressableBoundsCapture`, capture
   px) must be supplied and then proven by the run itself. Candidate derivation from the reviewed
   rev27 S11c evidence (`s11c-menu-detect.json`, `s11c-menu-frame-geometry.json`,
   `geometry-binding.json`): full-frame 2x px `[1008,182,1246,485]` minus window origin px
   `[422,58]` = **candidate `[586,124,824,427]`** in the window-crop capture space, explicitly
   unvalidated. Note it extends 170 px beyond the 654-px-wide window crop, i.e. it is clipped in
   a window-only capture.
5. Open capture-surface question Phase A must resolve (then repair/replan if confirmed): the frozen
   composition captures every state with `.primaryWindow` (`includeChildWindows=false`). The W2
   calibration matrix
   (`evidence/20260925-rev28-native-closed-loop/harness/frozen/capture-matrix-v1.json`) shows the
   harness popup child window is included only when `includeChildWindows=true`, and the reviewed
   rev27 geometry shows LINE's "…" menu opens as a separate surface extending past the main
   window's right edge. If the real menu cannot be observed inside the primary-window capture,
   MENU_VERIFIED / SAVE_ALL_LOCATED cannot be established as frozen and the typed refusal routes
   to repair/replan (capture-surface decision) per plan §PHASE_A.

## Provenance

Written by the Stage 04 implementer at 2026-09-29T06:27+0800, from read-only observations only
(probe record, CG/AX window inventory, process table, read-only screencapture; the temporary
screenshots were deleted and never added to the repository).
