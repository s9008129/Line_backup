# Rev27c route attempt-15 — one-shot ellipsis runbook (pre-declared BEFORE any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` (ellipsis click budget 1; everything else 0; Save All 0; no album-card click / no navigation / no retry).
- Entry state claimed by the owner: LINE left on the album-detail window at the end of attempt-14 (composite = ALBUM_OPEN_VERIFIED_COMPOSITE). This round re-verifies that claim freshly and read-only; it never re-opens the album.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (== expected frozen binding)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - `tools/v5/locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162`
  - `tools/vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - attempt-local read-only observation tools copied byte-identical from attempt-14: `tools/ax_window_bounds.swift` `5c615a90…`, `tools/validate_live_geometry.py` `ea4230e4…`.
- No v4 locator fallback, no historical-coordinate fallback ([304,50] / [305,50] are evidence only), no threshold tuning, no retry.

## Pre-declared space, pairing and capture decisions (fixed BEFORE any run)
1. **Spaces.** Full-screen frame (2× device pixels) for frame-space evidence; the read-only CU app-window screenshot (1 px = 1 pt of the focused window) for window space — the same space `sky.click` consumes and the same space the frozen v5 family was tuned and self-tested in (327×643).
2. **S3 formal frozen pair (window space).** pre = `attempt-14/cua-window-preclick.jpg` `8b27c1e0a8bcd284e06a47521c47f7ee2c2b21a342764739c8e7620b3474ced4` (the byte-authenticated pre-click album-LIST window frame of the very transition being revalidated — no fresh list state can exist in this round because this round is forbidden to navigate and the click that opened the album happened in attempt-14), post = THIS round's fresh live window frame (album-detail window). Verdict must be `ALBUM_OPEN_VERIFIED` (exit 0).
   Supporting (recorded, not gating): same frozen verifier on `attempt-14/frame-pre.png` `7e16ddff…` (full-screen album list) vs this round's fresh full-screen frame.
   Rationale for window-space formal: in full-screen space the verifier's title rule can be satisfied by non-LINE text elsewhere on screen (attempt-12/13/14 all recorded this), so only the window-space pair makes the identity rule discriminative.
3. **S6 (v7 guard) inputs — all this round.** `--window-inventory` = fresh AX window-bounds JSON; `--window-ax-state` = CU AX state text of the focused window in **full-tree form** (`getAXState({disableDiffing:true})`; diff/"no change" forms are refused by the guard, so no re-capture is attempted); `--window-screenshot` = fresh CU window screenshot; `--frame` = this round's fresh full-screen frame; `--expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57`; `--reader-dir` default (frozen v5); `--frozen-album-open-json` = the frame-space frozen artifact from decision 2 (its `post_sha256` equals this round's `--frame` sha256, which is exactly what the guard's C7 requires).
4. **Composite decision.** PASS only if (a) window-space frozen verdict == `ALBUM_OPEN_VERIFIED`, (b) frame-space frozen verdict == `ALBUM_OPEN_VERIFIED`, and (c) the guard exits 0 with lineage `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` and `composite == ALBUM_OPEN_VERIFIED_COMPOSITE_PASS`. Any other combination = `ALBUM_OPEN_COMPOSITE_REFUSED`, recorded with exact reasons, STOP, no retry, no manual override. The attempt-03 false-positive class (title + 57 + changed_fraction alone) is never used as album-detail success.
5. **S4 frozen v5 locator.** Exactly ONE invocation, on the SAME fresh live window frame used by S3, with `--title-bbox` = the window-space frozen verifier's post title bbox, `--expect-group-title 「旻謙允禎成長日記」`, `--header-depth 60`, all other thresholds at defaults. Verdict must be `ELIGIBLE`; the candidate must be derived from THIS frame. Any other verdict -> STOP with ellipsis 0 (no fallback, no retry, no re-run on another frame).
6. **S5 pre-click gates (all must hold, else stop with ellipsis 0).** (a) fresh CU window screenshot byte-identical to the S4 frame; (b) fresh read-only AX window list identical to S2's post-frame read; (c) LINE still frontmost; (d) fresh full-screen pre-click frame binds to the window (dims exact + gray MAD ≤ 12.0, pre-declared bound). Then exactly one left click at the fresh v5 `click_point` (window space) via the CU tool; no retry, no second click, whatever the outcome.
7. **S6 menu observation pairs (frozen `detect_menu_popup.py`, defaults, declared now).**
   - Pair A (app window): pre = the S4 live window frame; post = post-click CU window frame.
   - Pair B (screen): pre = the S5 fresh pre-click full-screen frame; post = post-click full-screen frame #1 (and #2, if captured).
   - Affirmative menu evidence (attempt-07 rule): frozen-detector `MENU_DETECTED` (geometry + ≥2 OCR strings of ≥2 chars inside the changed component) plus visual/OCR confirmation of the menu; OCR-only or visual-only or incomplete -> UNKNOWN, never affirmative.
   - Declared disqualifier for pair B: if every changed component lies entirely outside the LINE album window rect, the detection is recorded as unrelated screen noise (the agent's own Codex UI can update between captures), NOT menu evidence.
8. **Capture schedule after the single click (read-only).** full-screen #1 at ≈0.4 s; CU window post frame at ≈1.2 s; full-screen #2 at ≈2.2 s. No additional captures; **no dismissals** (no Escape, no click-outside, no second click, no keyboard, no scroll). The menu, if present, is left open for the owner.
9. **STOP boundary.** After S6 the round stops unconditionally. Save All / menu-item / chooser / download remain unauthorized even when the menu is affirmatively observed.

## Step sequence
- S0 declarations: `authorization-record.json`, this runbook, `00-start-state.json`; frozen SHAs re-verified from disk; attempt-15 is a new unused slot.
- S1 fresh read-only album-detail observation: read-only AX window inventory + CU AX state/screenshot + fresh full-screen frame; verify bundle, LINE frontmost, unambiguous target window, target album identity, 57-photo context, album-detail surface still present, no album-list active surface, no unknown overlay, no permission prompt, no occluding window. **If the surface is no longer album-detail -> STOP** (no reopen, no album-card click, no navigation, no bring-to-front).
- S2 fresh frame / geometry binding: AX pre -> fresh full-screen frame -> AX post; require same target window, stable geometry, still frontmost, stable surface, no overlay transition; frame/window binding must PASS. Any ambiguity -> STOP (no screenshot retry).
- S3 fresh composite: frozen album-open verifier (window formal + frame supporting) -> must be `ALBUM_OPEN_VERIFIED`; then approved v7 lineage guard -> must be `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED`; composite must be `ALBUM_OPEN_VERIFIED_COMPOSITE`. No manual override.
- S4 frozen v5 fresh locator -> must be `ELIGIBLE`.
- S5 pre-click gates -> exactly one album-level ellipsis left click (budget 1, consumed forever).
- S6 post captures -> frozen menu detector pairs A/B -> record verdicts -> STOP unconditionally.

## Decision rules (owner-specified)
- A: fresh composite FAIL -> ellipsis 0, STOP.
- B: composite PASS but v5 != ELIGIBLE -> ellipsis 0, STOP.
- C: v5 ELIGIBLE, ellipsis dispatched, menu not affirmative -> ellipsis 1, retry 0, STOP.
- D: v5 ELIGIBLE, ellipsis dispatched, menu affirmatively observed with 儲存全部 -> scoped status `READY_FOR_SAVE_ALL_GATE_A_AUTHORIZATION`, Save All used 0, STOP.
