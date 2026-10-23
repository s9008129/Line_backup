# live/ — NOT_RUN

No live observation exists in this directory. The single authorized live session
(≤6 documented single App.scroll 0.25-page calls) has NOT been started; the budget
is unused (`results/attempt-ledger.json`: `scroll_calls_used = 0`,
`remaining_budget = 6`).

Why not started (in order):
1. G_OFFLINE is satisfied locally (`offline-validation/results.json`:
   19 PASS / 0 FAIL / R20 NOT_RUN).
2. The independent same-candidate pre-live program/evidence review is **pending**:
   native delegation was attempted twice and both dispatches were rejected at the
   platform layer with the same error (`results/pre-live-review.dispatch.json`);
   no reviewer artifact exists; a root self-review would violate independence.
   The ready-to-forward packet is `results/pre-live-review.packet.json`
   (sha256 `cd6edf3edbf44d68ac318d0f508914f83ab771aab989d4b0f1e4fe20a5d315c4`).
3. Fresh user-coordinated LINE foreground readiness: not yet performed.

Capability facts (verified 2026-10-10, read-only):
- The host exposes the documented CUA surface (runtime documentation read on first
  use): `cua.getApp`, `App.getAXStateAndScreenshot`, `App.scroll` (native app scroll
  accepts a page count on macOS).
- App inventory shows LINE (`jp.naver.line.mac`) running; no app was opened,
  focused, or interacted with.
- Correction: an earlier version of this file claimed the host "exposes no
  documented CUA live surface". That claim is corrected here: the surface exists;
  it was simply not exercised, and the live preconditions were not met.

Live allowlist (handoff §10): getApp / getAXStateAndScreenshot / App.scroll only;
no click, key, Page Down, setValue, album open, menu, Save All, chooser, download,
or canonical-state write.

Zero inputs sent from this task: 0 click, 0 key, 0 Page Down, 0 setValue,
0 album open, 0 menu, 0 Save All, 0 chooser, 0 download, 0 canonical state write.
