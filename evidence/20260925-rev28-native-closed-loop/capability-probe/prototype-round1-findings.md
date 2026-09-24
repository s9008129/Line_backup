# Rev28 capability prototype round 1 — empirical findings (2026-09-25)

All probes are self-contained synthetic AppKit/ScreenCaptureKit programs run from `/tmp` (copies preserved here). No LINE interaction, no events posted, no repository or user data modified. Raw output: `prototype-round1-outputs.txt` (SHA-256 `55d7a56e32148c870caba69e3826b03fb3e473be0d44a1b4763de056eac78b04`).

## P1. Tool-process prerequisites (probe.swift, capture2.swift)

- `CGPreflightScreenCaptureAccess`, `CGPreflightPostEventAccess`, `AXIsProcessTrusted` are all `true` for the agent shell process tree.
- `SCScreenshotManager` in a plain CLI process **crashes** (`CGS_REQUIRE_INIT` assertion) unless a GUI context exists. Fix: initialize `NSApplication.shared` and pump a run loop. Confirmed twice.
- `SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)` works and matches `CGWindowListCopyWindowInfo` (windowID / frame / layer) for every observed window.

## P2. Capture of another app's window (capture3.swift, Terminal 1147×683 pt)

- `SCContentFilter(desktopIndependentWindow:)` → `contentRect` equals `SCWindow.frame`; `pointPixelScale` = 2.0 on this display.
- `SCScreenshotConfiguration` (macOS 26 API) `includeChildWindows=false` → 2294×1366 px = frame × 2.0 exactly.
- `includeChildWindows=true` → 2294×1438 px = **union of the window frame with its child titlebar window frame** (y 26..745 = 719 pt), NOT the window frame. Child windows must therefore be treated as a bounding-box union, never as "frame × scale".
- Legacy `captureImage` + `SCStreamConfiguration` works but defaults to 1920×1080 px; explicit pixel dimensions are required for deterministic sizes.

## P3. Child-window union rule + SC frame vs AppKit frame (childunion.swift)

AppKit main window frame (top-left) `(240,93,400,332)`; SCWindow.frame reported `(243,96,394,326)` at that moment (3 pt inset on every side). Borderless child at AppKit `(560,26,200,150)`; SCWindow.frame identical. `includeChildWindows=true` capture = 1038×796 px = 519×398 pt ≈ union(SC frames) (517×396 pt) + 1 pt per side. `includeChildWindows=false` = 792×660 px = 396×330 pt ≈ SC frame (394×326) + 1 pt horizontally / 2 pt vertically.

**Consequence:** the capture bounding box is *not* guaranteed to equal `SCWindow.frame`; a per-capture size self-check and an explicit bbox record are mandatory.

## P4. Default capture space = window-local (markers.swift / markers2.swift)

Settled titled window, AppKit frame (top-left) `(300,121,400,364)`; `SCWindow.frame` = `(300,121,400,364)` (equal in this settled state). Four 10×10 pt markers at view-local corners:

| marker | window-local (top-left pt) | predicted px (×2) | observed px |
|---|---|---|---|
| magenta TL | (20, 52) | (40, 104) | (39.5, 103.5) |
| yellow BL | (20, 344) | (40, 688) | (39.5, 687.5) |
| cyan TR | (380, 52) | (760, 104) | visible in `markers-default.png` |
| green BR | (380, 344) | (760, 688) | visible in `markers-default.png` |

Default capture (no `sourceRect`) = 800×728 px = window frame × 2.0, origin at window-local (0,0) = frame top-left; the image includes the title bar. **This is the primary transform for the Rev28 engine.**

## P5. `sourceRect` semantics (sourcerect2.swift, markers3.swift)

- `sourceRect` size is honored exactly: image px = sourceRect.size × scale (880×808 px for 440×404 pt).
- A `sourceRect` whose origin lies outside the window entirely (e.g. `(660,153,80,80)` for a 400×364 pt window) **fails** with `SCStreamErrorDomain -3811` (stream start failure). A `sourceRect` that starts inside the window but extends beyond its bounds succeeds and returns the in-bounds region with the rest black/transparent — consistent with `sourceRect` being interpreted in the **window's local coordinate space**, not display-global coordinates. (Labeled `[INFERRED]` from two observations; the harness will prove it with an in-bounds/out-of-bounds matrix.)
- Because `sourceRect` cannot extend beyond the window surface, popups or sheets that are separate windows must be captured as their own windows (own filter) with their own transforms.

## P6. SC frame vs AppKit frame instability

Three probes observed `SCWindow.frame == NSWindow.frame` (settled window) and two observed a uniform 3 pt inset (window shortly after creation / not activated). The engine must therefore **never** assume equality; it must read `SCWindow.frame` freshly for every capture epoch and re-validate before dispatch (`[VERIFIED]` instability; cause `[UNKNOWN]`).

## Open items for the harness (W2)

1. Exact capture-vs-frame border rule for `includeChildWindows=false/true` as a function of window style and activation state; formalize as a validated invariant (`image ≥ frame×scale`, delta ≤ 4 pt, recorded per capture).
2. Prove that a posted Quartz click at the computed screen point of a popup row is delivered to the topmost popup window (hit-test), not the main window beneath.
3. Prove capture independence from occlusion (full cover by another window must not blank the LINE/window surface) — the synthetic harness must *verify*, not assume, this, including the black-region behavior seen in P5.
4. Prove the AX surface and identity checks of an AppKit `NSOpenPanel` on macOS 27 and the Go-to-folder path.
