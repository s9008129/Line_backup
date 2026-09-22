# Independent locator review — v7 Save All menu-item locator (attempt-05)

**Plan requirement:** `PLAN-2026-09-21-rev27-save-all.md` §5.3 — the locator must be
created, self-tested, frozen (SHA-256), and independently reviewed (separate pass recorded
in this round's evidence) **within the Gate A round before any click**.

**Frozen tool:** `tools/locate_save_all_menu_item.py`
SHA-256 `ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a`, 16538 bytes
(byte-identical to attempt-02/03/04 copies; re-verified from disk this round).
Freeze record: `locator-freeze-attempt05.json` `f6c4f2ef…`.

This review pass is read-only: nothing under `tools/`, `selftest-attempt05/` or the freeze
record was modified during it. It precedes any Save-All input (0 Save-All inputs this
round; 1 ellipsis input consumed earlier in this round).

## Property checks (§5.3 items 1–6)

1. **Input binding — PASS.** Detector JSON must be `MENU_DETECTED` and bind the frame by
   path and SHA (lines 216–222); geometry must bind the frame SHA and carry window rect +
   capture scale (lines 226–244); violations return `BAD_INPUT` (6). Exercised this round:
   `selftest-attempt05/result-binding-fail.json` → `BAD_INPUT` 6.
2. **Text-first identification — PASS.** Menu-bbox crop → 3× LANCZOS → `tesseract -l
   chi_tra+eng --psm 6 tsv` (stdin, lines 65–99); rows are vertical clusters; a row's text is
   the whitespace-stripped left-to-right concatenation, so multi-glyph OCR splits still match
   `儲存全部`. Exactly one matching row required; >1 → `AMBIGUOUS` (4); 0 → `NOT_FOUND` (2).
   Exercised: `result-ambiguous.json` → `AMBIGUOUS` 4; `result-negative.json` → `NOT_FOUND` 2.
3. **Cross-check, never computation — PASS.** The reference order is only checked *against*
   the observed CJK rows (containment + strictly increasing row order around the identified
   row, lines 283–307). No row-index arithmetic; a contradicting set → `MENU_CONTENT_UNEXPECTED`
   (5). Exercised: `result-unexpected.json` → 5; **and live:** on this round's frame the
   reference item `修改相簿名稱` read as `修改相簿名般` (single-glyph misread) → the tool
   fail-closed with `MENU_CONTENT_UNEXPECTED` rather than emitting a candidate. This is the
   designed conservative behaviour.
4. **Candidate rule — PASS.** `x` = midpoint of (observed text-box x-range ∩ addressable
   region x-range); `y` = vertical center of the observed text box; require overlap ≥ 20 px,
   candidate inside menu bbox, inside addressable region, within the identified row's extent
   (lines 320–353). Exercised: `result-not-addressable.json` → `NOT_ADDRESSABLE` 3.
5. **Output spaces — PASS.** `frame_px`, `screen_pt = px/scale`, `app_local_pt = screen_pt −
   window origin pt`, all from the round's own bound geometry (lines 333–347). Observable in
   `result-fixture-positive.json` (candidate present in all three spaces).
6. **Hard prohibitions — PASS.** Programmatic grep for barred literals (`\b(304|305|39|923|
   926|1313)\b`) in `tools/locate_save_all_menu_item.py` finds zero matches; the only text
   constants are the target item and the reference-order item names; no formula rows.

## Adversarial checks

- **No input capability — PASS.** Imports are `argparse, hashlib, io, json, re, subprocess`
  + `PIL.Image`; `subprocess` is used solely for tesseract (lines 72–73, 103–104); the only
  write site is `open(out_path, "w")` in `finish()` (line 158).
- **Fail-closed coverage — PASS.** Every non-ELIGIBLE path returns without a candidate;
  `ELIGIBLE` (0) requires all checks to pass. All six exit codes exercised this round:
  ELIGIBLE 0 / NOT_FOUND 2 / NOT_ADDRESSABLE 3 / AMBIGUOUS 4 / MENU_CONTENT_UNEXPECTED 5 /
  BAD_INPUT 6 (see `locator-freeze-attempt05.json` `self_test.runs`).
- **Determinism — PASS.** (a) fixture positive run is byte-identical to attempt-02's accepted
  `b97bd773…`; (b) the two live runs on this round's frame are byte-identical (`7e92e252…`).
- **Fixture coordinates carry no live authority — PASS.** Fixture candidates (e.g.
  `[1313.5, 332.333]` frame px) exist only in `selftest-attempt05/` artifacts; the live path
  requires a fresh frame + fresh detector JSON + fresh frame-bound geometry, and it produced
  **no** candidate this round.
- **Live inputs are this round's own — PASS.** Live inputs were `frame-menu-post1.png`
  (this round, sha `2f6bf83d…`), `s6-menu-pairB1.json` (this round's detector run, bound to
  that frame), and `live-window-geometry-post1.json` (this round's AX read, bound to that
  frame). No historical coordinate or geometry was used.

## Verdict

`LOCATOR_REVIEW_PASS` — the frozen v7 locator is fit for use on this round's fresh frame.
On this round's frame it returned `MENU_CONTENT_UNEXPECTED` (deterministic), which per plan
§5.1.4/§5.3.3 means: **no Save-All candidate exists → STOP**, Save All 0. The module is not
modified, not re-tuned, and not bypassed.
