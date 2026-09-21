# Rev28 route attempt-13 — one-shot ellipsis runbook (pre-declared before any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` (ellipsis click budget 1; everything else 0; Save All 0).
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (== expected frozen binding)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - `tools/vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - attempt-local read-only observation tools copied byte-identical from attempt-12: `tools/ax_window_bounds.swift` `5c615a90…`, `tools/validate_live_geometry.py` `ea4230e4…`.
- No v4 fallback, no new locator fallback, no threshold tuning, no historical coordinate as live input, no retry.

## Pre-declared space and pairing decisions (fixed BEFORE any run)
1. **Live window space = the read-only CU app-window screenshot (1 px = 1 pt, 327×643)** — the same space `sky.click` consumes and the same space the frozen v5 family was tuned and self-tested in (327×643). The full-screen frame (2×) is used for occlusion evidence and frame/window binding only.
2. **S3 formal album-open revalidation pair:** pre = `attempt-12/cua-window-s1.jpg` `92ea79915f13c68bec6473ed224bb0e51662aaa846167df37fc25e54872e5a47` (the byte-authenticated pre-click album-LIST window frame of the very transition being revalidated — no fresh list state can exist in a zero-input round because the click that opened the album happened in attempt-12), post = THIS round's fresh live window frame. Both frames are window-space 327×643. Verdict must be `ALBUM_OPEN_VERIFIED` (exit 0).
   Supporting (not gating) pair: pre = `attempt-12/frame-pre.png` (full-screen list), post = this round's fresh full-screen frame; same frozen verifier, recorded for transparency.
   Rationale for window-space formal: in full-screen space the verifier's title rule can be satisfied by non-LINE text elsewhere on screen (attempt-12's own S5 title match lay at frame x≈704-1077, outside the LINE window), so only the window-space pair makes the identity rule discriminative.
3. **S4:** frozen v5 locator on the SAME fresh live window frame, `--title-bbox` taken from the S3 post title bbox, `--expect-group-title 「旻謙允禎成長日記」`, `--header-depth 60`, all thresholds at defaults. Verdict must be `ELIGIBLE`.
4. **S5 pre-click gates (all must hold, else stop with ellipsis 0):** (a) fresh CU window screenshot byte-identical to the S4 frame; (b) fresh read-only AX window list identical to S1; (c) fresh full-screen pre-click frame binds to the window (dims exact + gray MAD ≤ 12.0). Then exactly one left click at the fresh v5 `click_point` (window space) via `sky.click`; no retry.
5. **S6 menu observation pairs (frozen `detect_menu_popup.py`, defaults, declared now):**
   - Pair A (app window): pre = the S4 live window frame; post = post-click CU window frame.
   - Pair B (screen): pre = fresh pre-click full-screen frame; post = post-click full-screen frame #1 (and #2, if captured).
   - Affirmative menu evidence (attempt-07 rule): **new AX menu elements** or **`MENU_DETECTED`**. OCR-only / visual-only / incomplete → UNKNOWN, never affirmative.
   - Declared disqualifier for pair B: if every changed component lies entirely outside the LINE album window rect, the detection is recorded as unrelated screen noise (my own Codex UI can update between captures), NOT menu evidence.
6. **Capture schedule after the single click (read-only):** full-screen #1 at ≈0.4 s; CU window post frame at ≈1.2 s; full-screen #2 at ≈2.2 s. No additional captures, no dismissals (no Escape / click-outside), menu may be left open for the owner.

## Step sequence
- S1 read-only album-open observation: AX window read + CU window state/screenshot + visual album-open surface check (title, photo grid, no list, no permission prompt, no overlay).
- S2 fresh full-screen frame + AX post + frame/window binding + occlusion check of the toolbar/⋮ region.
- S3 formal pair -> require `ALBUM_OPEN_VERIFIED` (else stop, ellipsis 0).
- S4 frozen v5 -> require `ELIGIBLE` (else stop, ellipsis 0).
- S5 pre-click gates -> exactly one ellipsis left click (budget 1, consumed forever).
- S6 post captures -> menu pairs A/B -> record verdicts; **no further input of any kind**; stop.

## Decision rules (owner-specified)
- A: fresh album-open != ALBUM_OPEN_VERIFIED -> stop, ellipsis 0.
- B: verified but live v5 != ELIGIBLE -> stop, ellipsis 0.
- C: v5 ELIGIBLE, ⋮ dispatched, menu detector non-affirmative -> stop, ellipsis 1, retry 0.
- D: v5 ELIGIBLE, one ⋮ click, menu surface affirmatively observed -> route success `MENU_SURFACE_AFFIRMATIVELY_OBSERVED`; state `READY_FOR_SAVE_ALL_PLAN_AND_NEW_AUTHORIZATION`; still no Save All.
- Save All boundary: `save_all_budget = 0`, `save_all_dispatch_attempted = false`; reading `Save All`/`儲存全部` text is evidence only.
