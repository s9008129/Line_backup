# Rev25 Phase 2 — Runtime / focus / z-order read-only checks

## Historical runtime

The frozen execution record says the shell runtime had no CUA executor. It used:

- `screencapture -x` for a screen capture;
- `osascript` + System Events process-level `click at` for the input;
- no `getApp`, `getScreenshot`, or `getAXState` implementation in that runtime;
- no activate/bring-to-front before the click.

The read-only `System Events.sdef` definition states that the `at` parameter for a process click is “the { x, y } location at which to click, in global coordinates.” This supports global logical-point semantics, not a window-local argument.

Historical focus/window facts recorded before S4:

- LINE was recorded frontmost.
- WIN1 was the `327x643` album-list window at `(0,27)` points.
- The command returned `window 1 of application process LINE`, but exit `0` is dispatch evidence, not proof that LINE changed its model state.

## Current read-only query (2026-09-19)

No input or activation was sent. The observed current state was:

- `System Events` could not obtain application process `LINE` (`-1728`).
- `pgrep -x LINE` returned exit `1`.
- The frontmost application query returned `Safari` (unix id `986`).
- Current LINE window geometry/focus therefore has no observation in this attempt; it must not be substituted for the historical geometry.

## Difference from the planned CUA path

The plan's CUA-shaped runbook expected app/screenshot/AX primitives. The actual historical route used whole-screen capture plus System Events global-coordinate dispatch and did not produce an AX event-target trace. That runtime difference is evidence for an **UNKNOWN** delivery/semantics hypothesis, not proof of the root cause.

## Frozen inputs rehashed

- `run-ledger.json`: `7c8ea39a391617f3276b4e3e40043086317c73719baf3b51bdf3d356ea2f032f`
- `screen-probe.json`: `38130a6a540c099b3ca88e979a72684a467e158b4a78ce64bf4334ccdba6f77c`
- `album-card-locate.json`: `94694c921171f98c53b7fc79a350d0f7faf635c234ed17cf894b87f9fb0fd624`
- `album-open-verify.json`: `aa0a2161d844b5cf7583514d2269c4db61f210c3cc85b57afa0f9d8b471a83ff`
- `route-runbook.md`: `a9669a99ea9a488c0df96a454ea5da8a60441da35cc2e77f8e23db014f6b5107`
- `execution-rev24.md`: `8f8d2b3de1372709b34b9fc9d3fa4d7168e1739acf799131b1fe01e80493a104`
