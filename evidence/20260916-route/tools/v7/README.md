# tools/v7 — ALBUM_DETAIL_WINDOW_LINEAGE_GUARD

Append-only new tool version (Rev27b replan). **v4 / v5 / v6 are untouched and
remain frozen; the frozen album-open verifier is not modified.**

## Why this exists

Rev27 Save All Gate A attempt-03 produced a false-positive exposure:
the frozen album-open verifier (`verify_album_open.py`, v4/v5) returned
`ALBUM_OPEN_VERIFIED`, but the actual surface was the **album-list window** and
no album-detail window existed. The verifier's whole rule set is
`target title readable in post` + `changed_fraction >= 0.05`; the album-list
surface itself shows the target date-range title and the photo count `57`, and
any inter-round repaint satisfies the change test. Title + count + change is
therefore **not** detail-exclusive.

`album_detail_lineage_guard.py` closes that gap: it verifies, from
current-round evidence only, that the **focused LINE window right now** is an
album-detail window of the attempt-12/13 lineage.

## Composite success rule (future rounds)

```
ALBUM_OPEN_VERIFIED_COMPOSITE =
    frozen album-open verifier == ALBUM_OPEN_VERIFIED
    AND album_detail_lineage_guard == ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED
```

Only the composite may admit a run to the ellipsis stage. The guard also
machine-checks the composite when `--frozen-album-open-json` is supplied and,
in that case, additionally requires the frozen artifact's `post_sha256` to
equal this round's `--frame` sha256 (same-round binding of the frozen verdict).

## Inputs (all captured in the SAME round; sha256 of each is recorded)

| flag | content |
|---|---|
| `--window-inventory` | frozen read-only AX window-bounds JSON (v2 schema: bundle/frontmost/windows/display) |
| `--window-ax-state` | CU read-only AX state text of the **focused** window; a **full-tree** form is required (CU diff / "no change" forms are refused) |
| `--window-screenshot` | CU read-only window screenshot of that focused window |
| `--frame` | full-screen capture of the same moment |
| `--expect-start/--expect-end/--expect-count` | target album identity (e.g. `2024/05/13` `05/17` `57`) |
| `--reader-dir` | directory with the frozen `locate_album_card.py` + `vision_reader.py` (default: v5) |
| `--frozen-album-open-json` | optional frozen verifier verdict JSON for the composite check |

## Checks (all must PASS; any FAIL/UNKNOWN -> REFUSED, fail-closed)

| id | rule |
|---|---|
| C0 | evidence present, inventory parses, schema complete, frame size == display bounds x backing scale == CG display mode pixels |
| C1 | `bundle_id`/`frontmost_application` == `jp.naver.line.mac`, `ax_frontmost` and `ax_api_trusted` true, running |
| C2 | exactly ONE `is_ax_focused_window` window AND exactly ONE `main` window and they are the same window; not minimized; `AXWindow`/`AXStandardWindow` |
| C3 | no other window shares the target's exact rect (no duplicate-geometry ambiguity); target rect inside the frame |
| C4 | AX surface class of the focused window (from the same-round CU text): standard window + close/minimize chrome; NO `列表`/`文字欄位`, no `row` entries; the focused UI element is the window itself (custom-drawn content) |
| C5 | frame/window pixel binding: crop `--frame` at the target rect x scale, LANCZOS-downscale by scale, require exact dims vs the window screenshot and gray MAD <= 12.0 (frozen validator precedent). Proves the window is visible/unoccluded at that rect and that the binding uses only this round's inventory (no historical coordinate) |
| C6 | detail header context on the BOUND window screenshot via the frozen Vision reader: target title found with `title bbox bottom <= 30%` of window height; a `張照片` token whose digits == `--expect-count`; NO `相簿`/`記事本` tab tokens |
| C7 | composite (only when requested): frozen verdict == `ALBUM_OPEN_VERIFIED` AND frozen `post_sha256` == this round's frame sha256 |

## Refusal reason codes

`EVIDENCE_MISSING`, `EVIDENCE_MALFORMED` (+`frame_scale`), `NOT_FRONTMOST`,
`TARGET_AMBIGUOUS` (+ counters), `GEOMETRY_DOUBT`,
`SURFACE_AX_NOT_FULL_TREE:<FORM>`, `SURFACE_HAS_LIST_CONTROLS`,
`SURFACE_HAS_LIST_ROWS`, `FOCUSED_ELEMENT_NOT_WINDOW`,
`SURFACE_NOT_CUSTOM_DRAWN_WINDOW`, `BINDING_FAILED`, `READER_UNAVAILABLE`,
`HEADER_TITLE_NOT_FOUND`, `TITLE_NOT_IN_HEADER_BAND`,
`PHOTO_COUNT_CONTEXT_MISSING_OR_MISMATCH`, `LIST_TAB_MARKERS_PRESENT`,
`FROZEN_ARTIFACT_MISSING/MALFORMED`, `FROZEN_VERDICT_NOT_ALBUM_OPEN_VERIFIED`,
`FROZEN_POST_FRAME_NOT_BOUND_TO_THIS_FRAME`, `FROZEN_PRE_FRAME_HASH_MISSING`.

Deliberate non-signal: the photo-grid pixel structure itself is NOT used as a
hard check. It does not separate list vs detail surfaces reliably across
rounds/scrolls (both surfaces contain photo mosaics), and a tile-layout metric
would overfit the current screenshots. The custom-drawn detail content is
established by the chrome-only AX tree (C4) plus the bound header context (C6).

Exit codes: `0` verified (and composite PASS when requested), `2` lineage
refused, `3` lineage verified but composite FAIL, `6` bad input.

## Determinism / safety properties

- read-only, zero GUI input, no network; identical inputs => byte-identical JSON
  (no timestamps, no process-unique values)
- no historical coordinate fallback: every rect is derived from the supplied
  current-round inventory; failure to bind refuses instead of retrying elsewhere
- ambiguity, missing evidence, wrong/multiple windows, occluded or stale
  frames, list surfaces, wrong album, wrong count all refuse
- it never clicks, never selects, never opens a chooser; the future route still
  stops after the album-card gate even when the composite passes

## Evidence-capture requirements for future rounds (learned from replay)

1. The guard needs a **full-tree** CU AX state read of the focused window in the
   same round. CU returns a full tree on the first `get_app_state` of a session
   and diff forms afterwards, so the post-click read must be the session's
   first read (attempt-12's post-click evidence only saved a diff form and can
   therefore not be strictly verified).
2. The frozen album-open verifier must run on the SAME round's frame pair
   (`frame-pre`/`frame-post`), never on historical frames; attempt-03 violated
   that contract and produced its false positive.

## Selftest / offline replay

`python3 selftest/run_selftest.py` -> 22 deterministic cases + a determinism
repeat + a 5-combo attempt-03 sweep (no combo may verify). Results:
`selftest/results.json`; per-case outputs in `selftest/out/`.

Key replays: attempt-13 detail => VERIFIED (MAD 2.259, header y-frac 0.17,
`57張照片`); attempt-12 post-click via the byte-identical-screenshot bridge =>
VERIFIED + composite PASS; attempt-12 pre-click => REFUSED; attempt-03 (even
with its frozen `ALBUM_OPEN_VERIFIED` artifact) => REFUSED, composite never
PASSes.
