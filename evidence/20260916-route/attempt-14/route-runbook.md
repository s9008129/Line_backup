# Rev27b route attempt-14 — one-shot album reopen runbook (pre-declared before any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` (new album-card click budget 1; everything else 0; no ellipsis/menu/Save All/chooser/keyboard/download).
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v6/locate_album_card.py` `d55a974fd61f3494d3ab7c26705a35bb6e91b39eefeb1bd95de5527a988d9142`
  - `tools/v6/extract_window_geometry.py` `b396d6a85c9b068a1b9d6e584acbd4f9e6b1b14ccad8a11ef32b11797627b7d8`
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - `tools/vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
  - attempt-local read-only observation tools copied byte-identical from attempt-13: `tools/ax_window_bounds.swift` `5c615a90…`, `tools/validate_live_geometry.py` `ea4230e4…`; compiled binary `1c34c62c…` (byte-identical to attempt-10/12/13).
- No historical coordinate as live input (attempt-10/11/12/13 candidates are evidence only), no fallback, no threshold tuning, no retry.

## Pre-declared space, pairing and capture decisions (fixed BEFORE any run)
1. **Spaces:** full-screen frame (2x device pixels) for frame-space evidence; the read-only CU app-window screenshot (1 px = 1 pt of the focused window) for window space.
2. **S5 formal frozen pair (window space):** pre = THIS round's fresh pre-click CU window screenshot (album-LIST window); post = THIS round's fresh post-click CU window screenshot. Rationale: this round's click is the transition being verified and window space makes the frozen verifier's title identity rule discriminative (in full-screen space the rule can be satisfied by non-LINE text elsewhere, as recorded in attempt-12). The frozen verifier runs on frames captured for this run (its own contract).
3. **S5 supporting frozen pair (frame space):** pre = `frame-pre.png`; post = `frame-post.png`. Recorded for transparency. **This artifact is also the object for the guard's C7 machine binding** because its `post_sha256` equals this round's `--frame` sha256 (the guard's C7 requires exactly that).
4. **S6 v7 guard inputs (all this round):** `--window-inventory` = fresh post-click AX window-bounds JSON; `--window-ax-state` = CU AX state text of the focused window in **full-tree form** (see capture rule 6); `--window-screenshot` = fresh post-click CU window screenshot; `--frame` = `frame-post.png`; `--expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57`; `--reader-dir` default (frozen v5); `--frozen-album-open-json` = the frame-space frozen artifact (decision 3).
5. **Composite decision:** PASS only if (a) window-space frozen verdict == `ALBUM_OPEN_VERIFIED`, (b) frame-space frozen verdict == `ALBUM_OPEN_VERIFIED`, and (c) the guard exits 0 with lineage `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` and `composite == ALBUM_OPEN_VERIFIED_COMPOSITE_PASS`. Any other combination = `ALBUM_OPEN_COMPOSITE_REFUSED`, recorded with exact reasons, STOP, no retry, no manual override.
6. **Post-click AX state capture procedure (pre-declared; amended before any input after reading this runtime's documented API):** the plan requires a full-tree CU AX read of the focused window (diff/"no change" forms are refused by the guard). This runtime documents `getAXState({disableDiffing: true})` as the way to request "a fresh full accessibility tree". The post-click focused-window AX read therefore uses `getAXState({disableDiffing: true})` (and the same for the S1 pre read), saved verbatim as evidence. If the returned text is still not a full tree, it is recorded as-is; no further capture attempts are made and the guard refuses (fail-closed). No re-captures beyond this one.
7. **S3:** frozen v6 locator on the SAME fresh frame with `--window-geometry` = this round's frame-SHA-bound `live-window-geometry.json`; expected `2024/05/13`,`2024/05/17`,`57`; verdict must be `ELIGIBLE`; the candidate must be derived from THIS frame.
8. **S4 pre-click gates (all must hold, else stop with album-card 0):** (a) fresh CU window screenshot byte-identical to the S2 binding-time shot; (b) fresh read-only AX window list identical to S1/S2; (c) LINE still frontmost; (d) no overlay/permission prompt; then exactly one left click at the fresh v6 `click_point`, converted to window-screenshot coordinates with this round's rect/scale, via the CU tool; no retry.
9. **Post-click capture schedule (read-only):** `frame-post.png` immediately after the click returns (~0.5 s settle); fresh AX window-bounds (post); CU post-click window read (screenshot + AX state per rule 6). No additional captures; no dismissals; no Escape; no click-outside.
10. **STOP boundary:** after S6/composite the round stops unconditionally. Ellipsis/menu/Save All remain unauthorized. If composite PASS: `ALBUM_OPEN_VERIFIED_COMPOSITE` + `READY_FOR_NEW_ELLIPSIS_AUTHORIZATION` (NOT READY_FOR_SAVE_ALL).

## Step sequence
- S1 read-only album-LIST surface: AX window read + CU window state/screenshot; verify bundle/frontmost/group/tabs 相簿(selected)/記事本/first card 2024/05/13～05/17 with 57/fully visible card/no overlay/no permission prompt.
- S2 fresh full-screen frame + AX post + frame-SHA-bound geometry + frame/window binding validation (dims exact AND gray MAD <= 12.0).
- S3 frozen v6 -> require ELIGIBLE.
- S4 pre-click freshness gates -> exactly one album-card left click (budget 1, consumed forever).
- S5 post frame + frozen verifier pairs (window formal / frame supporting) -> require `ALBUM_OPEN_VERIFIED` (else COMPOSITE FAIL, STOP).
- S6 v7 guard -> composite decision -> STOP unconditionally.

## Decision rules (owner-specified)
- A: fresh album-list identity not PASS -> stop, album-card 0.
- B: v6 != ELIGIBLE -> stop, album-card 0.
- C: click dispatched but frozen verifier != ALBUM_OPEN_VERIFIED -> COMPOSITE FAIL, stop, no retry.
- D: frozen verifier verified but v7 REFUSED -> ALBUM_OPEN_COMPOSITE_REFUSED (record exact reasons), stop, no retry.
- E: both verified and composite PASS -> `ALBUM_OPEN_VERIFIED_COMPOSITE` + `READY_FOR_NEW_ELLIPSIS_AUTHORIZATION`; still no ellipsis/menu/Save All input.
