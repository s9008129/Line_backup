# Rev27d route attempt-18 — one-shot ellipsis runbook (pre-declared BEFORE any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` — AUTHORIZATION_TYPE = ELLIPSIS_ONLY, AUTHORIZATION_ID = REV27B-ELLIPSIS-AFTER-ATTEMPT17. Ellipsis click budget 1; everything else 0; Save All NOT authorized; no album-card click; no navigation; no retry.
- Entry state per owner: LINE was left on the album-DETAIL surface at attempt-17 end (attempt-17 = one album-card reopening click; frozen verifier ALBUM_OPEN_VERIFIED both spaces; v7 = ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED; composite = ALBUM_OPEN_VERIFIED_COMPOSITE). This round re-verifies the live surface freshly and read-only; it never re-opens the album.
- Gate A baseline: HEAD `f314d74a7621b877bd5a797a63fddeec4e40814a` and ahead 16 match the owner's stated expectation exactly (no deviation); `origin/master` `a9e523e7d2b91ec1775bba573003a7a1671ef945` unchanged; no fetch/pull/push/reset/rebase/amend/stash; untracked `attempt-11/` and the four `__pycache__` dirs left untouched.
- Historical prerequisite re-hashed from disk this round: `attempt-17/99-scope-status.json` artifact manifest 43/43 entries byte-consistent; attempt-17 is immutable and was not modified.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (== expected frozen binding; the ONLY locator this round)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - `tools/v5/locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - `tools/vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
  - `tools/v6/locate_album_card.py` `d55a974fd61f3494d3ab7c26705a35bb6e91b39eefeb1bd95de5527a988d9142` — NOT used this round (no album-card click)
  - attempt-local read-only observation tools copied byte-identical from attempt-17: `tools/ax_window_bounds.swift` `5c615a90451919cc7fa0a2dbbe5875a1f4c8ea2c910d1fc070845ebae3e06ff6` (compiled binary `1c34c62c6183a4db8f809edc9fdfc7a9ade4db63837a9c24090cd7770156d6ae`, byte-identical to attempt-10/12/13/14/15/16/17), `tools/validate_live_geometry.py` `ea4230e4aa90a1662b7c7c7059810c087af70ff1f4a46f92ab75b89d7518da68`.
- No v4 locator fallback, no historical-coordinate fallback ([304,50] / [305,50] are evidence only), no threshold tuning, no retry.
- Known non-blocking disclosure: attempt-17 `live-window-geometry.json` prints the 16:51:23 read time for BOTH AX reads in its `source` string (labelling slip); authoritative timestamps are s1-ax-pre 16:50:00 and s2-ax-post 16:51:23. Recorded as `KNOWN_NON_BLOCKING_PROVENANCE_LABEL_TYPO`; attempt-17 and that v6-consumed artifact are NOT modified and attempt-17 is NOT re-run.

## Pre-declared space, pairing and capture decisions (fixed BEFORE any run)
1. **Spaces.** Full-screen frame (2× device pixels) for frame-space evidence; the read-only CU app-window screenshot (1 px = 1 pt of the focused window) for window space — the same space `lineApp.click` consumes and the same space the frozen v5 family was tuned and self-tested in (327×643).
2. **S3 formal frozen pair (window space).** pre = `attempt-17/cua-window-preclick.jpg` `eac18de8806c23d9bc320a14a84ceda1a7b8add8d1ac832785021411386aab2a` (the byte-authenticated pre-click album-LIST window frame of the very transition being revalidated — no fresh list state can exist in this round because this round is forbidden to navigate and the click that opened the album happened in attempt-17), post = THIS round's fresh live window frame (album-detail). Verdict must be `ALBUM_OPEN_VERIFIED` (exit 0).
   Supporting (recorded, not gating): same frozen verifier on `attempt-17/frame-pre.png` `6b37df75a8aa1ac48466c1167178916cdf6f432c30f4b08fa332329c2443caed` (full-screen album list) vs this round's fresh full-screen frame.
   Rationale for window-space formal: in full-screen space the verifier's title rule can be satisfied by non-LINE text elsewhere on screen (attempt-12/13/14/15/16/17 all recorded this), so only the window-space pair makes the identity rule discriminative.
3. **S3 lineage guard inputs (v7) — all this round.** `--window-inventory` = this round's fresh AX window-bounds JSON; `--window-ax-state` = this round's CU AX state text of the focused window in **full-tree form** (`getAXState({disableDiffing:true})`; diff/"no change" forms are refused by the guard, so no re-capture is attempted); `--window-screenshot` = this round's fresh CU window screenshot; `--frame` = this round's fresh full-screen frame; `--expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57`; `--reader-dir` default (frozen v5); `--frozen-album-open-json` = the frame-space frozen artifact from decision 2 (its `post_sha256` equals this round's frame sha256, which is exactly what the guard's C7 requires).
4. **Composite decision.** PASS only if (a) window-space frozen verdict == `ALBUM_OPEN_VERIFIED`, (b) frame-space frozen verdict == `ALBUM_OPEN_VERIFIED`, and (c) the guard exits 0 with lineage `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` and `composite == ALBUM_OPEN_VERIFIED_COMPOSITE_PASS`. Any other combination = `ALBUM_OPEN_COMPOSITE_REFUSED`, recorded with exact reasons, STOP, no retry, no manual override. The attempt-03/attempt-15 false-positive class (title + 57 + changed_fraction alone, or the frozen verifier alone) is never used as album-detail success.
5. **S4 frozen v5 locator.** Exactly ONE invocation, on the SAME fresh live window frame used by S3, with `--title-bbox` = the window-space frozen verifier's post title bbox, `--expect-group-title 「旻謙允禎成長日記」`, `--header-depth 60`, all other thresholds at defaults. Verdict must be `ELIGIBLE`; the candidate must be derived from THIS frame. Any other verdict -> STOP with ellipsis 0 (no fallback, no retry, no re-run on another frame). A fresh value that numerically coincides with a historical value ([304,50]/[305,50]) is acceptable only because it is independently re-derived from this round's frame and recorded with derivation evidence.
6. **S5 pre-click gates (all must hold, else stop with ellipsis 0).** (a) fresh CU window screenshot byte-identical to the S4 frame; (b) fresh read-only AX window list identical to S2's post-frame read; (c) LINE still frontmost; (d) fresh full-screen pre-click frame binds to the window (dims exact + gray MAD <= 12.0, pre-declared bound). Then exactly one left click at the fresh v5 `click_point` (window space, `lineApp.click([x,y], {mouseButton:"left", clickCount:1})`); no retry, no second click, whatever the outcome.
7. **S6 menu observation pairs (frozen `detect_menu_popup.py`, defaults, declared now).**
   - Pair A (app window): pre = the S4 live window frame; post = post-click CU window frame.
   - Pair B (screen): pre = the S5 fresh pre-click full-screen frame; post = post-click full-screen frame #1 (and #2, if captured).
   - Affirmative menu evidence (attempt-07 rule): frozen-detector `MENU_DETECTED` (geometry + >=2 OCR strings of >=2 chars inside the changed component) plus visual/OCR confirmation of the menu; OCR-only or visual-only or incomplete -> UNKNOWN, never affirmative.
   - Declared disqualifier for pair B: if every changed component lies entirely outside the LINE album window rect, the detection is recorded as unrelated screen noise (the agent's own Codex UI can update between captures), NOT menu evidence.
8. **Capture schedule after the single click (read-only).** full-screen #1 at ~0.4 s; CU window post frame at ~1.2 s; full-screen #2 at ~2.2 s. No additional captures; **no dismissals** (no Escape, no click-outside, no second click, no keyboard, no scroll). The menu, if present, is left open for the owner.
9. **STOP boundary.** After S6 the round stops unconditionally. Save All / menu-item / chooser / download remain unauthorized even when the menu is affirmatively observed.

## Step sequence
- S0 declarations: `authorization-record.json`, this runbook, `00-start-state.json`; frozen SHAs re-verified from disk; attempt-18 is a new unused slot; attempt-17 untouched.
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
