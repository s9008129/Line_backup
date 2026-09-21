# Independent locator review — v7 Save All menu-item locator (attempt-02)

**Plan requirement:** `PLAN-2026-09-21-rev27-save-all.md` §5.3 — the locator must be created,
self-tested, frozen (SHA-256), and independently reviewed (separate pass recorded in this
round's evidence) **within the Gate A round before any click**.

**Frozen tool:** `tools/locate_save_all_menu_item.py`
SHA-256 `ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a`, 16538 bytes.
Freeze record: `locator-freeze.json` `2621cce5…`.

This review pass is read-only: nothing under `tools/`, `selftest/` or the freeze record was
modified during it. It precedes any GUI input (0 inputs so far this round).

## Property checks (§5.3 items 1–6)

1. **Input binding — PASS.** Detector JSON must be `MENU_DETECTED` and bind the frame by path
   and SHA; geometry must bind the frame SHA and carry window rect + capture scale; violations
   return `BAD_INPUT` (6). The report carries all three bindings.
2. **Text-first identification — PASS.** Menu-bbox crop → 3× LANCZOS → `tesseract -l chi_tra+eng
   --psm 6 tsv` (stdin). Rows are vertical clusters; row text is the whitespace-stripped
   left-to-right concatenation, so multi-glyph OCR splits still match `儲存全部`. Exactly one
   matching row required; >1 → `AMBIGUOUS` (4); 0 → `NOT_FOUND` (2). OCR run failure → `BAD_INPUT`
   (fail-closed).
3. **Cross-check, never computation — PASS.** The reference order
   (`選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿`) is only checked *against* the observed
   CJK rows (containment + strictly increasing row order around the observed target row). The row
   used for the candidate is the observed OCR row. No row-index arithmetic; a contradicting set →
   `MENU_CONTENT_UNEXPECTED` (5).
4. **Candidate rule — PASS.** `x` = midpoint of the observed text-box x-range ∩ addressable-region
   x-range (addressable = window rect ∩ menu bbox ∩ frame bounds); `y` = observed text-box vertical
   center. Overlap must be ≥ 20 px (default), candidate must lie inside the menu bbox, the
   addressable region, and the identified row's vertical extent — else `NOT_ADDRESSABLE` (3).
5. **Output spaces — PASS.** `frame_px`, `screen_pt = px/scale`, `app_local_pt = screen_pt −
   window origin pt` (the dispatch form), all computed from this round's own bound geometry.
6. **Hard prohibitions — PASS.** Programmatic grep for barred literals (`304`, `305`, `39`, `923`,
   `926`, `1313`) finds zero matches; the only text constants are the target item and the
   reference-order item names; no formula rows.

## Adversarial checks

- **No input capability — PASS.** Only imports are stdlib + PIL; `subprocess` is used solely for
  tesseract; the only write is the `--out` evidence JSON.
- **Fail-closed coverage — PASS.** Every error path returns a non-ELIGIBLE verdict and never emits
  a candidate; `ELIGIBLE` (0) requires all checks to pass.
- **Determinism — PASS.** Positive fixture run twice → byte-identical result JSON
  (`b97bd773…`).
- **Failure-fixture coverage — PASS.** `NOT_FOUND` 2 / `BAD_INPUT` 6 / `NOT_ADDRESSABLE` 3 /
  `AMBIGUOUS` 4 / `MENU_CONTENT_UNEXPECTED` 5 all exercised; stderr empty.
- **Fixture coordinates carry no live authority — PASS.** Self-test candidates (e.g.
  `[1313.5, 332.333]` frame px) exist only in `selftest/` artifacts and cannot be reached from the
  live path, which requires a fresh frame + fresh detector JSON + fresh frame-bound geometry.

## Verdict

`LOCATOR_REVIEW_PASS` — the v7 locator may be used on this round's fresh frame once the frozen
menu detector produces a `MENU_DETECTED` bbox. Any locator verdict other than `ELIGIBLE` stops the
round with zero GUI input.
