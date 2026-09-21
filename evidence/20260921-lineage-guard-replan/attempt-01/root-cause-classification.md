# Root cause: why the frozen album-open verifier said ALBUM_OPEN_VERIFIED on a non-detail surface

Rev27b replan, zero GUI input. Sources: frozen tool source, attempt-12/13
evidence, Rev27 Gate A attempt-03 evidence and the offline replays (see
`replay/replay-record.json`). No historical verdict is modified.

## 1. What the frozen verifier actually checks

OBSERVED (from `evidence/20260916-route/tools/v4|v5/verify_album_open.py`):

- reads two same-size gray frames (pre/post),
- runs the frozen Vision OCR on the **post** frame only: looks for a
  title-sized token window containing the target start+end digits, date-like
  tokens and (best-effort, non-refusing when empty) the count digits below the
  title,
- computes the fraction of pixels whose gray level differs by > 12,
- verdict rules: `ALBUM_OPEN_VERIFIED = target title readable in post AND
  changed_fraction >= 0.05`; other outcomes are `TARGET_MISMATCH`, `NO_EFFECT`,
  `INCONCLUSIVE`.

It has **no window identity, no AX evidence, no geometry and no surface
classification**. Its own docstring contract says both frames must be the ones
captured for the run; attempt-03 ran it twice with attempt-12's frames as
`pre`.

## 2. The attempt-03 false positive, precisely

OBSERVED:

- window pair: pre = attempt-12 `cua-window-s1.jpg` (`92ea7991…`, the
  pre-click **list** window) vs post = attempt-03 `cua-window-s1.jpg`
  (`3d926e7d…`, the **list** window again, different scroll/time) ->
  `changed_fraction 0.530517`, title read at bbox `[15,449,129,462]`
  (y ≈ 70 % of window height), count read `57` -> `ALBUM_OPEN_VERIFIED`.
- screen pair: pre = attempt-12 `frame-pre.png` (`b88f7e09…`) vs post =
  attempt-03 `frame-s1.png` (`0979cb78…`) -> `changed_fraction 0.42594`,
  same verdict.
- In attempt-03 the AX inventory has **2 windows only**; the album-detail
  window (`[337,30]`, the menu owner of attempt-13) does not exist; the
  AX-focused/main window is the group window and its CU AX tree contains
  `文字欄位` + `列表 (101 rows)`; its screenshot is the album list.

Also OBSERVED (relevant to the replay): attempt-12's `s2-ax-post.json` was
written at 15:08:31, i.e. **before** its album-card click at 15:11:39 (the file
is a pre-click read; mtime 15:08, intent 15:11), so attempt-12 has **no
post-click AX window inventory**; its post-click CU state file is a diff form.
The bridged attempt-12-post replay therefore uses attempt-13's same-surface
inventory read, justified by the byte-identical window screenshot
(`4cb8a6b4…` in attempt-12 S5, attempt-13 preclick and attempt-13 S1).

## 3. Why title + count + changed_fraction are insufficient

OBSERVED (OCR of the actual window screenshots):

- the album-**list** surface shows the target date-range title as a section
  header and the number `57` right below it (attempt-03: title at y ≈ 449/643;
  attempt-12 pre: y ≈ 425/643; `57` on the next line; no `張照片`),
- the album-**detail** surface shows the same title but in the top header
  (y ≈ 83/643 = 13 %) followed by `57張照片`, and has no `相簿`/`記事本` tabs,
- `changed_fraction >= 0.05` is satisfied by any repaint: between two
  different rounds it measured 0.53 / 0.43 on pure list-to-list pairs.

So every signal the verifier uses is also produced by the list surface, and
the change test measures "the screen changed", not "a detail window opened".
INFERRED: `ALBUM_OPEN_VERIFIED` alone can never identify the detail surface.

## 4. Reliable detail-vs-list discriminators (from the lineage evidence)

OBSERVED:

| signal | list surface (a12 pre, a03) | detail surface (a12 post, a13) |
|---|---|---|
| focused window AX tree (CU) | standard window + `文字欄位` + `列表` + rows + scrollbar | standard window + close/minimize chrome only (custom-drawn) |
| focused UI element | the text field | the window itself |
| window screenshot OCR | group name header, `相簿`/`記事本` tabs, title at y≈66-70 %, `57` alone | title at y≈13 %, `57張照片`, no tabs |
| window topology | 2 windows (a03) / group focused | 3 windows; detail window focused & main (327x643) beside the group list window and the LINE main window |
| frame/window pixel binding at the detail rect | detail shot does not bind (MAD 65.8–79.7) | binds exactly (dims exact, MAD ≈ 2.2) |

## 5. Signals missing in attempt-03

OBSERVED: no detail window in the inventory (2/3 windows), focused window is
the list window (101-row AX tree), screenshot OCR is the list surface, and no
detail screenshot binds to attempt-03's frame (MAD 79.67). The frozen verifier
never inspected any of this.

## 6. Classification

OBSERVED: sections 1–5 above, plus all recorded hashes re-verified
(`evidence-rehash.json`: attempt-12 20/20, attempt-13 33/33, attempt-03 34/34).

INFERRED:

- the attempt-03 verdict is a **verifier false-positive exposure**: the
  instrument is correct by its own rules but its rules do not include surface
  identity; it must not be used alone as "the correct album detail is open",
- the detail window's identity is `{focused/main custom-drawn window (chrome-only
  AX tree) + pixel-bound window screenshot + album header context}`, not a
  position and not title text,
- `[337,30]` is evidence of where the detail window sat during attempt-12/13,
  **not** a property to hard-code: attempt-03 proves the window can be absent,
  and the guard therefore derives every rect from the current inventory.

UNKNOWN:

- whether a future LINE build could render the detail view with AX elements
  (the guard refuses unless it can positively classify the surface),
- whether the frozen AX tool's window `index` implies front-to-back z-order
  (undocumented; the guard does not rely on it — it uses the focused/main flags
  plus pixel binding),
- whether the CU window screenshot scale is always 1x points (observed 1x; the
  guard derives the scale from the inventory display block and refuses on
  mismatch).

## 7. Guard-level closure (Rev27b)

OBSERVED (selftest + replay, `tools/v7`): the new
`ALBUM_DETAIL_WINDOW_LINEAGE_GUARD` verifies the attempt-13 detail surface and
the (bridged) attempt-12 post-click surface, and refuses attempt-12 pre-click,
attempt-03 (regression, with its frozen verdict present) and every constructed
adversarial variant; no attempt-03-derived combination ever verifies and the
composite can never PASS for it.
