# v5 corrected ellipsis position rule (Rev24)

## Problem (verified against durable attempt-06 evidence)

- v4 rule (`../v4/locate_album_ellipsis.py` `b77e3d51…`): eligible only when the
  middle dot lay inside the album-title row band derived from the verified title
  bbox (`band.y0 = max(0, ty0-6)`, `band.y1 = ty1+10`).
- Real attempt-06 post frame (327×643, `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3`):
  title bbox `[15,83,204,111]` → v4 band x∈[206,326], y∈[77,121].
  The only non-text ⋮ candidate `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]`
  (middle y=49.5) sits 33.5 px above the strip top (ty0=83) and 27.5 px above
  the band top (77) → `above_album_title_band`, ineligible. The other triples
  are `inside_text` (`57張照片`, `2024.05.18` glyph runs). Verdict
  `NO_ELLIPSIS_FOUND` (`attempt-06/album-ellipsis-locate.json`). ⋮ never sent.
- v4 self-test blind spot: `selftest/v4/run_selftest.py album_frame()` drew its
  control dots inside the synthetic strip (cy≈47 vs title y≈32) → 16/16 PASS but
  blind to the real geometry. The blind spot was the fixture, not the reader
  (S5 already `ALBUM_OPEN_VERIFIED` with Vision reading `57張照片` conf 1.00).

## Corrected rule (v5, plan §24.3)

- Unchanged (byte-identical logic/constants): census, dot, triple,
  text-blocking; delta 45, flat-tol 25, flat-fraction 0.6, max-area 16,
  max-side 5, text-margin 6.
- Title strip (recorded, NOT eligible):
  `band = {x0: tx1+2, x1: width-1, y0: max(0, ty0-6), y1: min(height-1, ty1+10)}`.
- NEW header (eligible region):
  `header = {x0: tx1+2, x1: width-1, y1: max(0, ty0-7), y0: max(0, ty0-7-header_depth)}`,
  `--header-depth` default 60.
- Eligible iff middle dot is (a) not `inside_text`, (b) not in the group-title
  band, (c) inside `header` (`header_band`). Exactly one required for ELIGIBLE.
- Non-eligible classes: inside strip → `in_title_strip`; above header →
  `above_header_band`; below strip → `below_album_title_band`; header-vertical
  but left of title right edge → `header_left_of_title`.
- Exit codes unchanged: 0 ELIGIBLE, 2 TARGET_TITLE_NOT_FOUND,
  3 NO_ELLIPSIS_FOUND, 4 AMBIGUOUS_ELLIPSIS, 5 GROUP_LEVEL_ONLY, 6 BAD_FRAME.

## Why 60

Observed offset 33.5 px above the strip top; 60 px is a bounded containment
window (~27 px headroom). Deeper would sweep unrelated chrome and could turn a
benign frame into `AMBIGUOUS_ELLIPSIS`; farther above is fail-closed
(`NO_ELLIPSIS_FOUND`), never guessed.

## Rejected alternative

Union (strip ∪ header) as eligible. Rejected: the strip is text-only on the
real surface and every real-frame triple inside it is a glyph run; the union
would widen the eligible region without real-frame support and increase the
wrong-coordinate risk class (a click onto text if the text blocker ever misses).

## Tool set

- `vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8` (byte-identical to v4)
- `locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162` (byte-identical to v4)
- `verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
- `locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (v5 corrected)
- Self-test: `../selftest/v5/selftest-summary.json` `e207f5029940d90b7cfae379ef67bddd3c976abebb12d6772c111c93dea5d5bf` (21 cases, `cases_failed 0`, `result PASS`)
- Helper source (frozen): `../vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`

## Offline replay (zero GUI; durable §24.6 proof before gate-5)

- v5 over the committed post frame with the S5 title bbox must return exit 0
  `ELIGIBLE` with `ellipsis_dots [[304.5,44.0],[304.5,49.5],[304.5,55.0]]` and
  `click_point [304,50]`:

```
/opt/homebrew/bin/python3 -B evidence/20260916-route/tools/v5/locate_album_ellipsis.py evidence/20260917-vision-reader/frames/route5r_frame_post.jpg --expect-start 2024/05/13 --expect-end 2024/05/17 --title-bbox 15,83,204,111 --expect-group-title 「旻謙允禎成長日記」 --header-depth 60 --out evidence/20260916-route/attempt-07/album-ellipsis-locate.json
```

- Frozen v4 bytes over the same frame must still return `NO_ELLIPSIS_FOUND`
  (attempt-06 `album-ellipsis-locate.json` is the对照证据):

```
/opt/homebrew/bin/python3 -B evidence/20260916-route/tools/v4/locate_album_ellipsis.py evidence/20260917-vision-reader/frames/route5r_frame_post.jpg --expect-start 2024/05/13 --expect-end 2024/05/17 --title-bbox 15,83,204,111 --expect-group-title 「旻謙允禎成長日記」 --out /tmp/v4-baseline-replay.json
```

- Any other verdict or point is `TASK_REGRESSION`. Historical coordinates are
  never live input; the live S6 point comes only from the current frame.
