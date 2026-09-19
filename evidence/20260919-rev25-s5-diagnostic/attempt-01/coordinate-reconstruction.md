# Rev25 Phase 2 — S5 座標鏈重建（zero GUI）

**Status:** PASS as a reconstruction of the recorded event; hitbox/event-delivery conclusions remain explicitly bounded.

## Frozen observations

- S3 frame: `2294x1490` screen pixels; Retina scale `2`.
- System Events read-only window geometry at the historical run: WIN1 (album list) position `(0,27)` logical points, size `327x643` logical points. The corresponding screen-pixel origin was `(0,54)` and crop size `654x1286`.
- S3 target title bbox: `[30,883,257,907]` screen pixels.
- S3 derived click point: `[42,895]` screen pixels (`title left edge + 12 px`, vertical centre).
- S4 emitted command: `osascript ... tell application "System Events" to click at {21, 448}`; exit `0`; returned `window 1 of application process LINE`.

## Deterministic mapping

For this display and window:

```text
screen_px -> global logical pt: (x/2, y/2)
screen_px -> WIN1-local logical pt: (x/2 - 0, y/2 - 27)
```

Therefore:

```text
[42,895] px -> [21,447.5] global pt -> emitted [21,448] global pt
[42,895] px -> [21,420.5] WIN1-local pt -> emitted local y [21,421] pt
```

The title bbox maps to global logical points `x=[15,128.5]`, `y=[441.5,453.5]`; the emitted event point `[21,448]` is inside that title/text rectangle. In WIN1-local points the same rectangle is `y=[414.5,426.5]`, and the emitted local point is `[21,421]`.

## Interpretation boundary

- **SUPPORTED:** the px/Retina/origin arithmetic and the global-point conversion are internally consistent; the event is in the OCR title/text band.
- **UNKNOWN:** whether the title/text band is backed by LINE's album-card hitbox, whether a 0.5-point rounding choice changes hit testing, and whether the process-level event was consumed as the intended card action.
- The arithmetic does not prove that `[42,895]` was a valid card hitbox point; the historical evidence only proves that it was the current-frame-derived title point and that System Events dispatched it to the LINE window.
