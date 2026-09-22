# Rev27d route attempt-19 — one-shot ALBUM_REOPEN_THEN_ELLIPSIS runbook (pre-declared BEFORE any input)

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` — AUTHORIZATION_TYPE = ALBUM_REOPEN_THEN_ELLIPSIS, AUTHORIZATION_ID = REV27B-ROUTE-TO-MENU-AFTER-ATTEMPT18. Max GUI budget: album-card click <= 1 AND ellipsis click <= 1 (total <= 2), each conditional; everything else 0; Save All NOT authorized.
- Conditional structure (owner text): S1 classifies the live surface as A (album-list), B (detail composite candidate) or C (ambiguous/other). Only A can spend the album-card click; only a fresh `ALBUM_OPEN_VERIFIED_COMPOSITE` can unlock the ellipsis click; the two halves run inside ONE uninterrupted attempt (no extra owner round between them).
- Gate A baseline: HEAD `2d93e88148fb878fad69149919f320eeda99117a` (owner-known HEAD, matched) and ahead 17 (matched); `origin/master` read from disk = `a9e523e7d2b91ec1775bba573003a7a1671ef945` (full value recorded; the owner's note about a one-character suffix discrepancy is resolved by this disk read). No fetch/pull/push/reset/rebase/amend/stash; untracked `attempt-11/` and the four `__pycache__` dirs untouched.
- Historical immutability: attempt-17 and attempt-18 are NOT modified and NOT re-run; attempt-18's unspent ellipsis budget is NOT transferred (owner-stated). attempt-18's fresh frames (`frame-s1.png`, `s1-window-cu.jpg`) are reused ONLY as the authenticated **pre-click album-list** state for this round's Branch-B pairing decision — never as click coordinates.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v6/locate_album_card.py` `d55a974fd61f3494d3ab7c26705a35bb6e91b39eefeb1bd95de5527a988d9142` (Branch A locator only)
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (== expected; COMMON ELLIPSIS GATE only)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` (byte-identical to v4)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`; `tools/v5/locate_album_card.py` `bb52aff1…`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`; `tools/v7/selftest/results.json` `affb3602…`
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`; `tools/vision/vision_ocr.swift` `4fc9fa2b…`
  - Rev27b plan/review/replay artifacts under `evidence/20260921-lineage-guard-replan/**` present and unmodified (hashes re-recorded).
  - attempt-local read-only observation tools copied byte-identical from attempt-18: `tools/ax_window_bounds.swift` `5c615a90…` (compiled binary `1c34c62c…`), `tools/validate_live_geometry.py` `ea4230e4…`.
- No historical coordinate as live input ([39,923]/[39,926]/[39,932]/[304,50]/[305,50] are documentation only), no v4 locator fallback, no threshold tuning, no retry, no double click.

## Pre-declared decisions (fixed BEFORE any run)
1. **Spaces.** Full-screen frame (2× device pixels) for frame-space evidence; the read-only CU app-window screenshot (1 px = 1 pt of the focused window) for window space — the space `lineApp.click` consumes and the space frozen v5/v6 were tuned in.
2. **S1 classification rule.** A = AX tree carries list controls (列表/文字欄位) with rows and the window screenshot/OCR show the group's album-list (tabs 相簿/記事本, album card caption 2024/05/13～05/17 + 57, card ⋮). B = the focused window's AX tree carries only window chrome (no list controls/rows), OCR reads the date-range title in the header band with a `57張照片` context token and no list tab tokens. C = LINE not frontmost, unknown overlay/permission dialog, occlusion, ambiguous target identity, or unresolved competing LINE windows. C => STOP with 0 GUI input; never bring-to-front.
3. **Branch A2 / Branch B binding.** read-only AX pre -> fresh full-screen frame -> read-only AX post; require identical window list, stable geometry, still frontmost, no overlay transition; frame-SHA-bound `live-window-geometry.json` + `validate_live_geometry.py` (dims exact AND gray MAD <= 12.0). Failure => STOP, 0 further GUI, no screenshot retry.
4. **Branch A3 frozen v6.** Exactly ONE invocation on THIS round's fresh frame with THIS round's frame-bound geometry (`--window-geometry`), expected `2024/05/13`, `2024/05/17`, count 57; must be `ELIGIBLE`; candidate derived only from this frame. Any other verdict => STOP.
5. **Branch A4 album-card click.** Only if A2 PASS + A3 ELIGIBLE + fresh pre-click CU window frame byte-identical to the binding-time shot + AX window list unchanged + LINE frontmost + no overlay: exactly one left click at this round's fresh v6 `click_point` converted with this round's rect/scale (`window px = (frame px − rect origin px)/2`). Budget consumed forever; no second click, no retry.
6. **A5 / B composite pairs (pre-declared).**
   - Branch A: window-space formal pair pre = THIS round's fresh **pre-click** CU window frame (album-list), post = THIS round's fresh **post-click** CU window frame (detail). Frame-space supporting pair pre = THIS round's `frame-pre.png`, post = THIS round's `frame-post.png`.
   - Branch B: the album was opened by an interaction this round did not perform, so the pre-state frames are the last authenticated album-list frames: window-space pre = `attempt-18/s1-window-cu.jpg` `bc833dd10c6a0e8ee5d4347fba4b438319b225f2fb27065920eaf2e9e405a9ed`, frame-space pre = `attempt-18/frame-s1.png` `8d260f4e122d900c20ff48a038091b9e8c6d9f0fa5c262df299ae78dceffb8b9`; post = this round's fresh frames.
   - Composite rule (both branches): PASS only if the window-space frozen verdict == `ALBUM_OPEN_VERIFIED` AND the frame-space frozen verdict == `ALBUM_OPEN_VERIFIED` AND the v7 guard exits 0 with `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` and `composite == ALBUM_OPEN_VERIFIED_COMPOSITE_PASS`. Any other combination = `ALBUM_OPEN_COMPOSITE_REFUSED` with exact reasons; STOP; no manual override; the attempt-03/15/16/18 false-positive class (frozen verifier alone) is never sufficient for the ellipsis gate.
7. **A5 / B v7 guard inputs — all THIS round.** `--window-inventory` = fresh AX window-bounds JSON of the post/current detail state; `--window-ax-state` = CU AX state text of the focused window in **full-tree form** (`getAXState({disableDiffing:true})`); `--window-screenshot` = fresh CU window screenshot of that window; `--frame` = the branch's post frame; `--expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57`; `--reader-dir` default (frozen v5); `--frozen-album-open-json` = the frame-space frozen artifact whose `post_sha256` equals that `--frame` sha256.
8. **E1 pre-ellipsis stability.** Read-only: fresh CU window frame byte-identical to the composite-time window frame, fresh AX window list still the verified detail window, LINE still frontmost, no overlay. Any change => STOP (no second album-card click as "repair").
9. **E2 frozen v5.** Exactly ONE invocation on THAT verified fresh detail window frame with `--title-bbox` = the window-space frozen verifier's post title bbox, `--expect-group-title 「旻謙允禎成長日記」`, `--header-depth 60`, otherwise defaults. Must be `ELIGIBLE`; the candidate must be derived from this round's frame (a numerically identical fresh value is admissible only with this round's independent derivation evidence). Any other verdict => STOP, ellipsis 0, no v4 fallback, no threshold change, no retry.
10. **E3 ellipsis click.** Only if composite PASS + v5 ELIGIBLE + E1 unchanged: exactly one left click at the fresh v5 `click_point` in CU window coordinates; budget consumed forever; no second ellipsis click, no retry.
11. **MENU OBSERVATION (read-only).** Immediately after the ellipsis click: fresh full-screen #1 (~0.4 s), CU window post frame (~1.2 s), full-screen #2 (~2.2 s); frozen `detect_menu_popup.py` pair A (app window pre/post) + pair B (screen pre/post) + OCR + visual read. Affirmative menu evidence = frozen-detector `MENU_DETECTED` (geometry + >=2 OCR strings of >=2 chars inside the changed component) PLUS visual/OCR confirmation. OCR-only or visual-only = UNKNOWN, never affirmative. Pair-B disqualifier: changed components entirely outside the LINE window rect are unrelated screen noise, not menu evidence. **No dismissals** (no Escape, no click-outside, no menu-item, no keyboard, no scroll). If the menu is not affirmative => STOP (C-type outcome), no second ellipsis click.
12. **Failure matrix (owner).** album-list + v6 unsafe -> STOP, 0 GUI; album click dispatched then composite FAIL -> STOP, GUI 1, no retry; detail-start composite FAIL -> STOP, GUI 0; composite PASS but v5 unsafe -> STOP, no ellipsis; ellipsis dispatched but menu missing/ambiguous -> STOP, no retry; any surface change -> STOP; unknown competing window -> STOP. No failure path extends to Save All.
13. **STOP boundary.** After the menu observation the round stops unconditionally; Save All / menu-item / chooser / keyboard / download remain unauthorized even when 「儲存全部」is clearly readable.

## Step sequence
- S0 declarations (this runbook, authorization record, scope check, start state) + frozen re-hash + attempt-19 creation.
- S1 read-only classification (A/B/C).
- Branch A: A2 binding -> A3 frozen v6 -> A4 exactly one album-card click -> A5 fresh post-click evidence + composite (frozen verifier pairs + v7 guard).
- Branch B: binding + composite with album_card_used = 0.
- COMMON ELLIPSIS GATE: E1 stability -> E2 frozen v5 -> E3 exactly one ellipsis click -> menu observation -> STOP.

## Decision rules
- C at S1: STOP, GUI 0.
- Branch A v6 not ELIGIBLE: STOP, GUI 0.
- Composite FAIL (either branch): STOP; ellipsis 0; no reopen/repair click.
- Composite PASS but v5 not ELIGIBLE: STOP; ellipsis 0.
- Ellipsis dispatched but menu not affirmative: STOP; retry 0.
- Menu affirmative with 「儲存全部」identified: scoped status `READY_FOR_SAVE_ALL_GATE_A_AUTHORIZATION` with Save All used = 0, then STOP.
