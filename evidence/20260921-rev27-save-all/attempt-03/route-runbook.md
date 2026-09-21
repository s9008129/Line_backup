# Rev27 Gate A — Save All dispatch observation (attempt-03; route lineage continues attempt-13/attempt-02) — runbook, pre-declared BEFORE any live observation or input

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` (Save All menu-item click budget 1, staging mkdir <= 2, everything else 0; OD-1 no formal state writes; OD-3 staging PRESERVE).
- Predecessor: attempt-02 (same Gate A authorization lineage) stopped fail-closed at S2 because the attempt-13 menu was NOT present; zero GUI input, zero filesystem writes, no staging mkdir.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`
  - round-local byte-identical copies (attempt-02/tools -> attempt-03/tools; read-only observation + locator): `ax_window_bounds.swift` `5c615a90…`, `validate_live_geometry.py` `ea4230e4…`, `locate_save_all_menu_item.py` `ea09c1ca…` (the frozen v7-class locator, re-frozen this round in `locator-freeze-attempt03.json`, re-selftested and re-reviewed this round before any click).
- No historical coordinate is ever used as input (`[304,50]`/`[305,50]`/`[39,923]`/`[39,926]` and all formula rows are permanently barred). No threshold tuning. No retry of any consumed input.

## Pre-declared spaces and mechanisms (fixed BEFORE the run)
1. **CU window space = window-local pt** (1 px = 1 pt). This is the space `sky.click({app, x, y})` consumes (proven live in attempts 12–13: a click at the window-local point landed exactly on the ⋮ control).
2. **Full-screen frame** = `screencapture -x`, device pixels at capture scale 2 (2294x1490 px = 1147x745 pt display). Window rect in frame px = window_pt * 2 (re-read fresh from the AX tool this round).
3. **Dispatch form**: `sky.click({app: "jp.naver.line.mac", x: <candidate app-local x>, y: <candidate app-local y>, mouse_button: "left", click_count: 1})` via `node_repl` + `@oai/sky`. Exactly one call. No other input.
4. **Pre-declared order**: P0 (this file + 00-start-state.json + authorization-record.json) -> S1 read-only surface revalidation -> S2 menu determination -> **if menu absent: STOP with zero GUI input and zero staging mkdir** -> S0 staging preflight (conditional; still strictly before any GUI input, plan §5.1 items 3->5) -> S2b fresh candidate -> S3 intent -> S4 exactly one click -> S5 observe + STOP. Rationale: a menu-absent STOP performs zero filesystem writes (attempt-02 precedent, owner decision tree).

## S1 — fresh read-only surface revalidation (zero input)
- Read-only AX window list via `tools/ax_window_bounds.swift` (compiled to /tmp; read-only queries only) -> require `ax_frontmost=true`, `frontmost_application=jp.naver.line.mac`, exactly one focused/main standard LINE window, position/size readable; fresh full-screen `screencapture -x` frame; post-frame AX read -> require window list identical (position/size/pid/frontmost).
- Fresh CU app state via `sky.get_app_state({app})` (read-only) -> save screenshot + AX text.
- **Formal album-open revalidation pair** (frozen `verify_album_open.py`): pre = `attempt-12/cua-window-s1.jpg` `92ea79915f13c68bec6473ed224bb0e51662aaa846167df37fc25e54872e5a47` (byte-authenticated album-LIST window frame of the very transition being revalidated), post = THIS round's fresh CU window screenshot. Require `ALBUM_OPEN_VERIFIED` (exit 0) with `count_text` MATCH; supporting (non-gating) screen pair pre = `attempt-12/frame-pre.png` `b88f7e09…`, post = fresh full-screen frame.
- Geometry binding (pre-declared rule: dims exact AND gray MAD <= 12.0): `live-window-geometry-attempt03.json` bound to the fresh frame SHA + `validate_live_geometry.py` -> require `GEOMETRY_BINDING_PASS`.
- Visual surface check (read-only): target album title + count, photo grid, no album list, no permission prompt, no unknown overlay, no occluding window over the album toolbar/ellipsis region.

## S2 — fresh menu determination (zero input; fail-closed)
- **Primary (affirmative rule, pre-declared)**: frozen `detect_menu_popup.py` (defaults: delta 12 / min-w 40 / min-h 20 / min-pixels 200 / min-strings 2 / min-strlen 2) with pre = `attempt-13/frame-menu-pre.png` `0118b12f…` (byte-authenticated menu-absent reference), post = THIS round's fresh frame. Menu is PRESENT only if `MENU_DETECTED` AND the freshly chosen bbox overlaps the fresh LINE window rect.
- **Independent ROI cross-check (pre-declared, read-only, never a click input)**: gray MAD over menu ROI px `[1247,127,1494,478]` against both byte-authenticated attempt-13 references (`frame-menu-pre.png` = menu-absent, `frame-menu-post1.png` `7ccb6f9e…` = menu-open). Pre-declared rule: ABSENT if MAD(fresh,absent) <= 12.0 AND MAD(fresh,absent) < MAD(fresh,open); PRESENT only if MAD(fresh,open) <= 12.0 AND MAD(fresh,open) < MAD(fresh,absent); anything else = INDETERMINATE -> STOP.
- Menu PRESENT requires BOTH the affirmative rule and the ROI cross-check to say PRESENT; any disagreement or INDETERMINATE -> treated as MENU_NOT_PRESENT -> STOP.
- **If MENU_NOT_PRESENT -> STOP**: final scoped blocker `MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`; Save All 0/1; staging mkdir 0/2 (no staging directory created); never reopen the ellipsis; never use a historical menu coordinate; record all evidence and stop.

## S0 — staging preflight (conditional: only if the menu chain holds; strictly before any GUI input)
- Fresh `run_id = RUN-YYYYMMDD-HHMMSS-01` generated at preflight; frozen into `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<run_id>/`. Exactly one `mkdir` of the leaf plus, only if `staging/` is machine-proven absent, exactly one `mkdir` of `staging/` (max 2 total; both empty). No other filesystem writes.
- Machine proofs (all required): canonical path equality / no symlink component; parent under authorized backup root and owner-writable; leaf absent before mkdir; after mkdir 0 entries / 0 files / 0 bytes / not symlink / not mount; staging != baseline and no ancestor/descendant relation; run_id pattern + not reused in any prior ledger; writable; accepted baseline unchanged before/after (tripwire digest).

## S2b — fresh candidate (frozen v7 locator; zero input)
- This round re-proves the frozen locator: determinism selftest (positive fixture `attempt-13/frame-menu-post1.png` twice -> byte-identical ELIGIBLE results; negative fixture `attempt-13/frame-menu-pre.png` -> NOT_FOUND), barred-literal grep, SHA verification; results recorded in `selftest-attempt03/` + `locator-freeze-attempt03.json` + `locator-review-attempt03.md`.
- Fresh run: `locate_save_all_menu_item.py <fresh frame> --detector-json <fresh detector JSON bound to that frame> --geometry <fresh frame-bound geometry>` -> must be `ELIGIBLE` with exactly one candidate and all three bindings recorded. Any other verdict -> STOP (zero input).

## S3 — intent record before dispatch
- `save-all-click-intent.json` written and read back (atomic) containing at least: run_id, gate, group, fingerprint `{2024-05-13, 2024-05-17, 57}`, staging path, staging-preflight evidence SHA, fresh menu frame SHA, detector/tool SHA, locator SHA, fresh candidate in all three spaces, candidate derivation, click budget = 1, click used = 0, `dispatch_state = NOT_ATTEMPTED`, `save_all_retry_allowed = false`, retry_budget = 0, formal state write = false, timestamp. Read-back + re-hash before any click; failure -> STOP.

## S4 — exactly one Save All click (at-most-once barrier)
- Final freshness gate (<= 15 s before dispatch, dispatch call as the very next action): re-capture frame F2 + fresh AX read; require LINE still frontmost, album-open still binding (geometry binding F2 PASS), menu still detected (affirmative rule), locator on F2 `ELIGIBLE`, and candidate2 within +/-3 frame px (x and y) of the S2b candidate. Any deviation -> `ABORTED_BEFORE_DISPATCH`, zero input, STOP.
- Boundary: `SAVE_ALL_DISPATCH_ATTEMPTED` recorded immediately before the click call (atomic write + read-back). The call is invoked exactly once; a returned call proves only that the call returned. Call throws/ambiguous -> `dispatch_state = UNKNOWN`; the click is never re-invoked.
- Budgets: `save_all_menu_item_click = 1`; `retry = 0` forever; everything else 0 (no double click, no second click, no keyboard, no Escape, no scroll, no AX write, no chooser interaction).

## S5 — post-dispatch observation only
- Immediately capture post frames (~0.4 s and ~2.2 s) + read-only CU/AX state; classify the resulting surface fail-closed: `SAVE_ALL_TRIGGER_CONFIRMED` (unmistakable macOS folder chooser affirmatively observed), `SAVE_ALL_TRIGGER_NOT_OBSERVED` (proven no new surface), `SAVE_ALL_TRIGGER_UNKNOWN` (anything else). Never upgrade the chooser verdict from historical evidence.
- Record: new modal/panel/window?, app/process identity, window role/title, AX structure, buttons/fields/labels, chooser affirmatively observed?, folder-chooser?, default destination readable?, staging still empty?, baseline unchanged?, filesystem side effects?. If a chooser is affirmatively observed -> record `CHOOSER_AFFIRMATIVELY_OBSERVED` and STOP (no Gate B). If not -> record the exact observed state and STOP.
- Filesystem tripwire (read-only, both at preflight and post-dispatch): baseline manifest digest must equal `b7debe92…`; staging inventory read-only. If staging unexpectedly gains files: record `UNEXPECTED_PRE_CONFIRM_FILESYSTEM_WRITE` and STOP. Never delete; never re-dispatch; never confirm the chooser.
- **STOP.** No input of any kind afterwards. Owner hand-off note: keep hands off the keyboard/pointer until the next authorized round.

## Budgets (this round)
Save All menu-item click 1; staging mkdir <= 2; ellipsis 0; album-card 0; navigation 0; retry 0; double click 0; other menu-item 0; chooser interaction 0; keyboard 0 (Escape included); scroll 0; AX write 0; app acquisition 0; bring-to-front 0; destination confirm 0; download 0; cleanup/delete 0; formal state/config write 0.
