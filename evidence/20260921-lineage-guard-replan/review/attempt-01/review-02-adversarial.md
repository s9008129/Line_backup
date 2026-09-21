# Review 2 — adversarial false-positive review

- Reviewed artifact: `PLAN-2026-09-21-rev27b-lineage-guard.md`
- Reviewed SHA-256: `7a179d15f61033611dec333d246b6d8c590901c06c182628533e442feae10a7c`
  (recomputed from disk by the reviewer)
- Guard observed: `evidence/20260916-route/tools/v7/album_detail_lineage_guard.py`,
  sha256 `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
- Lens: adversarial — actively try to compose a false-positive PASS from wrong surfaces / wrong
  windows / historical coordinates / unbound frozen verdicts.
- Date: 2026-09-21 (read-only; synthetic batteries written to `/tmp` only; no repo writes)

## Adversarial attempts (all real evidence; synthetic JSON only in /tmp)

1. **a13 inventory+state + a03 shot/frame** → exit 2 REFUSED `BINDING_FAILED`, MAD 74.53. Deeper
   variant (a03 inventory + a13 detail state + a03 shot/frame + a03 frozen artifacts): C4 PASS, **C5
   PASS (MAD 2.15)**, then C6 REFUSED ×3 — `TITLE_NOT_IN_HEADER_BAND` (y-frac 0.7185),
   `PHOTO_COUNT_CONTEXT_MISSING_OR_MISMATCH` (no `張照片` token), `LIST_TAB_MARKERS_PRESENT`
   (`相簿`,`記事本`); composite never evaluated. a03 window-screenshot passed as `--frame` → exit 6
   `EVIDENCE_MALFORMED:frame_scale`.
2. **a13 inventory/state/shot + a03 frame** → exit 2 REFUSED `BINDING_FAILED`, MAD 79.67.
3. **Historical-coordinate injection** — a03 inventory with focused rect hard-set to `[337,30]`:
   with a03 list state → exit 2 REFUSED C4 (`SURFACE_HAS_LIST_CONTROLS/ROWS`,
   `FOCUSED_ELEMENT_NOT_WINDOW`); with a13 detail state → REFUSED `BINDING_FAILED` 74.53.
4. **Window-set ambiguity** — duplicate geometry → `GEOMETRY_DOUBT`; two focused →
   `TARGET_AMBIGUOUS focused_windows=2`; two-focused+main → both; oversized LINE offscreen →
   `GEOMETRY_DOUBT`; wrong LINE window (group `[0,30]` focused + detail shot) → `BINDING_FAILED`
   65.82.
5. **Composite-binding attacks** — a13 verified + a03 window frozen → exit 3
   `ALBUM_OPEN_VERIFIED_COMPOSITE_FAIL` (`FROZEN_POST_FRAME_NOT_BOUND`); a13 + a13 same-round
   screen-supporting frozen → exit 0 composite PASS (legitimate); a12-bridged (a13 AX + a12
   frame-post + a12 frozen) → exit 0 composite PASS (documented bridge; those pixels are a genuine
   detail window).
6. **Sweep re-runs** — selftest sweep combos 0–4 independently re-run: none verified. Extra list
   sample (a12-pre list pixels + a13 state) → C6 refused (y 0.6827, tabs). Missing file/frame →
   exit 6.

## Hole classes examined (no surviving false positive)

- `C4` (guard L285–288) is satisfiable by a mismatched/doctored chrome-only state text (it parses
  text only; diff forms are refused at L76–78). Real a03 list pixels + a13 state text passed C4 —
  but **C6 was the backstop** and refused every real list-pixel set. C4 alone is not surface proof;
  the design correctly relies on the C5 pixel binding + C6 header context for surface identity.
- `C5` cannot pass with a wrong window: it requires `shot.size == rect` (L323–324) and MAD ≤ 12
  (L329); wrong-rect attempts measured 65.8–79.7.
- `C6` cannot pass with either real list screenshot (both show `相簿`/`記事本`, no `張照片` token,
  title y-frac 0.68–0.72 > 0.30).
- `C7` refuses an unbound frozen artifact (L407–408 requires `post_sha256 == this frame sha256`).

## Required confirmations

- **Frozen verifier unmodified: CONFIRMED.** `tools/v4/verify_album_open.py` and
  `tools/v5/verify_album_open.py` both = `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`.
- **No historical coordinate / window-position hard-code: CONFIRMED.** `rect_pt` derives from
  `target["position_points"]/size_points` (L258–259) of the current inventory, scaled by the
  inventory's `nsscreen_backing_scale_factor` (L204, L311–313); grep for `337/674/1328/1346` finds
  nothing in the guard; constants only `MAD_MAX=12.0` (L49) and `HEADER_Y_FRAC_MAX=0.30` (L50).
- **Ambiguity / missing evidence refuses: CONFIRMED** (exit 6 missing/frame-scale; DIFF_FORM/EMPTY,
  two-focused/two-main, duplicate geometry refuse).
- **Album-card click not merged with ellipsis: CONFIRMED** — the guard contains no click/input code
  (no `click/osascript/subprocess/ellipsis/Save/chooser/download` matches); plan §4 mandates an
  unconditional STOP after the composite with the ellipsis budget 0.
- **Save All / chooser / download excluded: CONFIRMED** textually (§1, §4 budgets, §7 `NOT READY…`);
  no code paths exist.

## Residual (non-falsifying)

- Cross-round byte-identical surfaces can compose via the documented bridge (pixels there are a
  genuine detail window).
- C7 binds only `post_sha256` (as the plan states); `pre_sha256` is only checked for presence.
- `--reader-dir` imports code from a caller-supplied directory (tool-trust boundary; default is the
  frozen v5).
- `selftest/results.json` reports `SELFTEST_PASS` (22/22, determinism, sweep); reviewer did not
  re-execute `run_selftest.py` (it writes into the repo) and independently replayed the sweep and
  key negatives instead. `replay-record.json` (`REPLAY_PASS`) exists and matches.

## Verdict

**PLAN_APPROVED** for plan SHA-256
`7a179d15f61033611dec333d246b6d8c590901c06c182628533e442feae10a7c`.
