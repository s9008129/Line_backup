# v6 album-card S3 safety locator (offline evidence only)

Scope: the album-card S3 safety decision **only**. v6 does not locate an ellipsis, does
not verify an album-open (S5) and does not detect menus. It never dispatches input; every
verdict it emits is offline evidence. The frozen v4/v5 tools are never modified or called
as a fallback.

## Why v6 exists

Frozen v4 (`../v4/locate_album_card.py`, sha256 `bb52aff1…`) decides the candidate click
margin by the mean grayscale of the **entire screenshot row** (all x of the frame it is
given). On the attempt-08/09 full-screen frames the LINE window occupies only ~28.5 % of
the row width, so even fully bright photo rows inside the window cannot lift the row mean
to v4's `bright=100` threshold below the title; v4 returns `UNSAFE_MARGINS` with
`band_bottom_bright_row = null` / `margin_below_px = null` in three distinct window
arrangements. The recomputation, the exact formula and the observed/inferred split live in
`evidence/20260921-replan-v6/attempt-01/v4-failure-analysis.md` (+ `.json`).

v6 keeps the frozen v4 **identity semantics** (machine-read title must match the expected
date range; a readable count that differs refuses) and replaces the spatial domain: all
row statistics are measured inside a caller-supplied **LINE-window ROI** that is bound to
the analysed frame's SHA-256, using the frame's own local background colour.

## Files

| File | Role |
|---|---|
| `locate_album_card.py` | v6 S3 safety locator (this document's subject) |
| `extract_window_geometry.py` | deterministic offline producer of the `--window-geometry` artifact from a frame's own pixels (see "ROI provenance") |

## Safety architecture (what must be proven)

For the candidate point of THIS frame the tool must establish:

- **A. exact target identity** — title OCR `2024/05/13~05/17` from this frame only.
- **B. expected count not mismatched** — readable count must contain `57`; unreadable count
  is recorded and does not refuse (same semantics as frozen v4); mismatch refuses (5).
- **C. candidate from the immediate frame** — `click_point = [tx0 + 12, (ty0+ty1)//2]` from
  this frame's OCR title box. No historical coordinate, no v4 candidate fallback.
- **D. candidate inside the target card's safe interior** — the caption strip is delimited
  by a content band above and a content band below, measured within the ROI at the same
  x-range; the candidate must clear both bands by `sep_min_px = max(24, round(title_h))`
  (= 27 px on the frozen frames).
- **E. separation from neighbouring cards / destructive UI** — the caption strip must
  contain exactly ONE non-title/non-count content cluster inside the ROI (the album's ⋮
  control), with `gap_left_of_candidate ≥ 100 px` and `gap_right_of_title ≥ 100 px`, and
  bounded size (≤ 48×80 px).
- **F. no historical coordinate** — geometry must be bound to the frame SHA-256; the tool
  source contains no historical click point; the replay selftest asserts the click point
  is derived (varies with the frame's own OCR box).
- **G. fail closed** — every unresolved structure, missing ROI, unbound ROI, or ambiguous
  strip refuses; there is no "best effort" ELIGIBLE path.

## Refusal codes

`0 ELIGIBLE`, `2 TARGET_TITLE_NOT_FOUND`, `4 UNSAFE_MARGINS`, `5 TARGET_COUNT_MISMATCH`,
`6 BAD_FRAME`, `7 WINDOW_ROI_MISSING_OR_INVALID`, `8 IDENTITY_NOT_ROI_BOUND`,
`9 CARD_STRUCTURE_UNRESOLVED`, `10 STRIP_CONTENT_UNEXPECTED`, `11 CANDIDATE_OUT_OF_BOUNDS`.

The decision order is: frame → title (2) → geometry binding (7) → candidate bounds (11) →
identity-inside-ROI incl. right tail (8) → count (5) → local background (9) → bands (9) →
margins (4) → strip thickness (9) → strip control clusters (10) → ELIGIBLE (0).

## ROI provenance

The `--window-geometry` artifact must be a JSON object with integer `x0,y0,x1,y1`, a
non-empty `source`, and `frame_sha256` equal to the analysed frame's SHA-256 (mismatch
refuses, exit 7; rect outside the frame, inverted, or smaller than 200×200 px also
refuses).

- **Live route (future wave):** the artifact is expected to be produced from a read-only
  AX window-bounds observation of the LINE window at fresh-frame time. Coordinate
  transform: the full-screen frame is a 2× device-pixel capture
  (`2294×1490` px ≡ `1147×745` pt; attempt-07 `screen-probe.json` records "Retina 2x"), so
  `frame_px = 2 × window_pt`; the candidate is reported in the same frame-pixel space that
  the click would be dispatched in. No scale guess is made at decision time: the geometry
  artifact carries the already-transformed pixel rect, and v6 validates it against the
  frame (insets, tail, structure).
- **Offline replay (this wave):** no AX read exists for the frozen frames, so
  `extract_window_geometry.py` derives the rect deterministically from the frame's own
  pixels: vertical border-line columns (colour 56..92, ≥12 levels brighter than the pixel
  6 px to the right, ≥8 levels brighter than 6 px to the left) spanning ≥300 rows and
  ≥400 px vertically; each left column pairs with the nearest right column ≥200 px away
  with ≥300 px span overlap; exactly one resulting rect must contain the machine-read
  title with ≥8 px insets, otherwise the extractor refuses and writes nothing. The
  extractor output used in this wave is byte-deterministic and recorded under
  `evidence/20260921-replan-v6/replay/geometry/`.

The ROI is not blindly trusted at decision time: the checks are frame-derived. In
particular the candidate bound (≥16 px from the ROI edge), the title/right-tail rule
(≥120 px of ROI right of the title) and the single-strip-control rule (the ⋮ control at
the caption's right end must be inside the ROI) jointly force any accepted ROI to span
essentially the full card width, and any ROI that fails to do so refuses (7/8/9/10).

## Constants (and why they are not tuned to pass)

| Constant | Value | Rationale |
|---|---|---|
| `CONTENT_DIFF` | 60 | max-channel distance from the local background; photos/controls differ far more, anti-aliasing far less |
| `BAND_FRAC_THRESHOLD` | 0.45 | a photo-grid row covers far more than 45 % of the card width; the caption strip covers only the text + ⋮ |
| `BAND_MIN_ROWS` | 20 | real grids are hundreds of rows thick |
| `STRIP_FRAC_MAX` / `STRIP_MIN_ROWS` | 0.30 / 40 | the caption strip is a tall, low-content band |
| `BG_MAD_MAX` | 5.0 | the strip background is uniform; a non-flat sample means the "strip" is not a clean surface |
| `SEP_MIN` | `max(24, title_h)` px | **stricter than v4's 10 px floor**; one title height of clearance to both content bands |
| `ROI_RIGHT_TAIL_PX` | 120 | the ROI must extend past the title toward the card's right content |
| `CONTROL_MIN_GAP_PX` | 100 | candidate must stay a caption's width away from the ⋮ control |
| `CONTROL_MAX_W/H` | 48 / 80 | the observed three-dot control is 5×26 px |

No constant was relaxed to make attempt-09 pass: on all three frozen frames the observed
margins (45/102, 44/103, 46/101 px) clear the floor by >1.6×, and the floor itself is
higher than the frozen v4 rule's 10 px.

## Determinism

All v6 decisions are pure functions of (frame bytes, geometry file, expected values): no
timestamps, no randomness, no live state. Replays on the same inputs are byte-identical
except `reader.helper.binary_sha256`, which reflects the locally rebuilt macOS Vision
helper binary; the frozen frames' OCR stdout hashes are stable and are recorded per call.

## Running

```
/opt/homebrew/bin/python3 extract_window_geometry.py <frame> \
    --expect-start 2024/05/13 --expect-end 2024/05/17 --out geo.json
/opt/homebrew/bin/python3 locate_album_card.py <frame> \
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 \
    --window-geometry geo.json --out verdict.json
```

Interpreter: `/opt/homebrew/bin/python3` (Pillow + numpy). OCR uses the frozen v4
`vision_reader.py` (sha256 `22a4e9ef…`) loaded as a sibling module; title/count logic is
copied verbatim from the frozen v4 locator (sha256 `bb52aff1…`).

## Self-tests

`selftest/run_selftest.py` replays the frozen frames and runs the negative matrix (wrong
date, wrong count, erased title, missing/unbound/malformed geometry, target at the ROI
edge, insufficient upper/lower separation, ambiguous strip, malformed frame, candidate
outside bounds, no-historical-coordinate assertions). Results are written to
`evidence/20260921-replan-v6/replay/selftest/results.json`.

## What v6 is not

- Not a live authorization. An offline `ELIGIBLE` is evidence that a fresh zero-input live
  verification is worth running; it never authorizes a click.
- Not a replacement for frozen v4/v5 in any other stage, and not a gate.
