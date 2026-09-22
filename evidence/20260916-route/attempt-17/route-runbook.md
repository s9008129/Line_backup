# Rev27d route attempt-17 — one-shot album reopen runbook (pre-declared before any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` — AUTHORIZATION_TYPE = ALBUM_REOPEN_ONLY, AUTHORIZATION_ID = REV27B-ALBUM-REOPEN-AFTER-ATTEMPT16. New album-card click budget 1; navigation 1; everything else 0. Frozen v5 ellipsis locator is explicitly FORBIDDEN; there is no menu-observation step and no Save All/chooser step in this runbook.
- Entry state per owner: LINE was left on the album-LIST surface at attempt-16 end (a zero-input round). This round's S1 success condition is "still album-list"; it then reopens the album-detail with exactly one album-card click. attempt-16's ellipsis authorization and unused budget are NOT transferred.
- Baseline: HEAD `e6ebf404…` and ahead 15 match the owner's stated expectation (no deviation expected); `origin/master` `a9e523e7…` unchanged; no fetch/pull/push/reset/rebase/amend/stash.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v6/locate_album_card.py` `d55a974fd61f3494d3ab7c26705a35bb6e91b39eefeb1bd95de5527a988d9142` (the ONLY locator this round)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - `tools/vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` — re-hashed for integrity ONLY; executing it is forbidden this round.
  - attempt-local read-only observation tools copied byte-identical from attempt-16: `tools/ax_window_bounds.swift` `5c615a90451919cc7fa0a2dbbe5875a1f4c8ea2c910d1fc070845ebae3e06ff6` (compiled binary `1c34c62c6183a4db8f809edc9fdfc7a9ade4db63837a9c24090cd7770156d6ae`, byte-identical to attempt-10/12/13/14/15/16), `tools/validate_live_geometry.py` `ea4230e4aa90a1662b7c7c7059810c087af70ff1f4a46f92ab75b89d7518da68`.
- No historical coordinate as live input ([39,923], [39,926], [39,932], [304,50], [305,50] are documentation only), no fallback, no threshold tuning, no retry.

## Pre-declared space, pairing and capture decisions (fixed BEFORE any run)
1. **Spaces:** full-screen frame (2× device pixels) for frame-space evidence; the read-only CU app-window screenshot (1 px = 1 pt of the focused window) for window space — the same space `lineApp.click` consumes.
2. **S5 formal frozen pair (window space):** pre = THIS round's fresh pre-click CU window screenshot (album-LIST window); post = THIS round's fresh post-click CU window screenshot. Rationale (as attempt-14): this round's click is the transition being verified and window space makes the frozen verifier's title identity rule discriminative.
3. **S5 supporting frozen pair (frame space):** pre = `frame-pre.png`; post = `frame-post.png`. This artifact is also the object for the guard's C7 machine binding because its `post_sha256` equals this round's `--frame` sha256.
4. **S6 v7 guard inputs (all this round):** `--window-inventory` = fresh post-click AX window-bounds JSON; `--window-ax-state` = CU AX state text of the focused window in **full-tree form** (`getAXState({disableDiffing:true})`; diff forms are refused by the guard — recorded as-is, no re-captures); `--window-screenshot` = fresh post-click CU window screenshot; `--frame` = `frame-post.png`; `--expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57`; `--reader-dir` default (frozen v5); `--frozen-album-open-json` = the frame-space frozen artifact from decision 3.
5. **Composite decision:** PASS only if (a) window-space frozen verdict == `ALBUM_OPEN_VERIFIED`, (b) frame-space frozen verdict == `ALBUM_OPEN_VERIFIED`, and (c) the guard exits 0 with lineage `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` and `composite == ALBUM_OPEN_VERIFIED_COMPOSITE_PASS`. Any other combination = `ALBUM_OPEN_COMPOSITE_REFUSED`, recorded with exact reasons, STOP, no retry, no manual override.
6. **S3 frozen v6 locator.** Exactly ONE invocation, on the SAME fresh frame (`frame-pre.png`) with `--window-geometry` = this round's frame-SHA-bound `live-window-geometry.json`; expected `2024/05/13`, `2024/05/17`, `57`; verdict must be `ELIGIBLE`; the candidate must be derived from THIS frame. Any other verdict -> STOP with album-card 0.
7. **S4 pre-click gates (all must hold, else stop with album-card 0).** (a) fresh CU window screenshot byte-identical to the S2 binding-time shot; (b) fresh read-only AX window list identical to S1/S2; (c) LINE still frontmost; (d) no overlay/permission prompt. Then exactly one left click at the fresh v6 `click_point`, converted to CU window-screenshot coordinates with this round's rect/scale (`window px = (frame px − rect origin px) / 2`), via `lineApp.click([x,y], {mouseButton:"left", clickCount:1})`; no retry, budget consumed forever.
8. **Post-click capture schedule (read-only).** `frame-post.png` immediately after the click returns (~0.5 s settle); fresh AX window-bounds (post); CU post-click window read (screenshot + AX state per rule 4). No additional captures; no dismissals; no Escape; no click-outside.
9. **STOP boundary.** After S6/composite the round stops unconditionally. frozen v5 is never invoked; ellipsis/menu/Save All/chooser remain unauthorized. If composite PASS: `ALBUM_OPEN_VERIFIED_COMPOSITE` + `READY_FOR_NEW_ELLIPSIS_AUTHORIZATION` (NOT READY_FOR_SAVE_ALL).

## Step sequence
- S1 read-only album-LIST identity: AX window read + CU window state/screenshot + window-space OCR + visual read; verify bundle/frontmost/target window unambiguous/target card `2024/05/13～05/17` with count 57 fully visible/no overlay/no permission prompt/no occlusion. If not album-list, or the target is uncertain, STOP with 0 GUI input.
- S2 fresh full-screen frame + AX post + frame-SHA-bound geometry + frame/window binding validation (dims exact AND gray MAD <= 12.0). Any ambiguity → STOP, no screenshot retry.
- S3 frozen v6 → require ELIGIBLE (else STOP, GUI input 0).
- S4 pre-click freshness gates → exactly one album-card left click (budget 1, consumed forever).
- S5 post frame + frozen verifier pairs (window formal / frame supporting) → require `ALBUM_OPEN_VERIFIED` (else COMPOSITE FAIL, STOP).
- S6 v7 guard → composite decision → STOP unconditionally.

## Decision rules (owner-specified)
- A: S1 not album-list → stop, album-card 0.
- B: v6 != ELIGIBLE → stop, album-card 0.
- C: click dispatched but frozen verifier != ALBUM_OPEN_VERIFIED → COMPOSITE FAIL, stop, no retry.
- D: frozen verifier verified but v7 REFUSED → ALBUM_OPEN_COMPOSITE_REFUSED (record exact reasons), stop, no retry.
- E: both verified → `ALBUM_OPEN_VERIFIED_COMPOSITE` + `READY_FOR_NEW_ELLIPSIS_AUTHORIZATION`; no ellipsis/menu/Save All input.
