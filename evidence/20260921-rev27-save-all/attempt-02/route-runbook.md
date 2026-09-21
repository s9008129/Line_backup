# Rev27 Gate A — Save All dispatch observation (attempt-02; route lineage continues attempt-13) — runbook, pre-declared BEFORE any live observation or input

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記` (禎 U+798E); album `2024/05/13～05/17`; expected count 57.
- Authorization: `authorization-record.json` (Save All menu-item click budget 1, staging mkdir <= 2, everything else 0; OD-1 no formal state writes; OD-3 staging PRESERVE).
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`, `tools/v5/locate_album_card.py` `bb52aff1…`
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (reference only; not used for input this round)
  - attempt-local copies byte-identical from attempt-13: `tools/ax_window_bounds.swift` `5c615a90…`, `tools/validate_live_geometry.py` `ea4230e4…` (read-only observation helpers)
- New tool this round: v7-class menu-item locator `tools/locate_save_all_menu_item.py` — created, self-tested on frozen fixtures, SHA-256 frozen, and reviewed before any click (plan §5.3).
- No historical coordinate is ever used as input (`[304,50]`/`[305,50]`/`[39,923]`/`[39,926]` and all formula rows are barred). No v4/v5 fallback in the locator path. No threshold tuning. No retry of any consumed input.

## Pre-declared spaces and mechanisms (fixed BEFORE the run)
1. **CU window space = window-local pt** (1 px = 1 pt; LINE window 327x643 at position (337,30) pt as of attempt-13; re-verified fresh this round). This is the space `sky.click({app, x, y})` consumes (proven live in attempts 12–13: a click at the window-local point landed exactly on the ⋮ control, whose hover delta then appeared at that same window-local pixel).
2. **Full-screen frame** = `screencapture -x`, device pixels at capture scale 2 (2294x1490 px = 1147x745 pt display). The window rect in frame px = window_pt * 2 (provenance re-read fresh from the AX tool this round).
3. **Dispatch form**: `sky.click({app: "jp.naver.line.mac", x: <candidate x in window-local pt>, y: <candidate y>, mouse_button: "left", click_count: 1})` via `node_repl` + `@oai/sky` (the historically proven path). Exactly one call. No other input.
4. **Execution order note**: the read-only surface verification (S1/S2 below) precedes the staging mkdir so that a menu-absent STOP performs zero filesystem writes; the staging preflight still precedes any GUI input (plan §5.1 items 3→5). S0 numbering in the owner brief is preserved as a section label.

## S1 — fresh read-only surface revalidation (zero input)
- Read-only AX window list via `tools/ax_window_bounds.swift` (compiled to /tmp; read-only queries only) -> require `ax_frontmost=true`, `frontmost_application=jp.naver.line.mac`, exactly one standard LINE window, position/size readable.
- Fresh CU app state via `sky.get_app_state({app})` (read-only) -> save screenshot + AX text.
- Fresh full-screen `screencapture -x` frame.
- Post-frame AX read -> require window list identical (position/size/pid/frontmost).
- **Formal album-open revalidation pair** (frozen `verify_album_open.py`): pre = `attempt-12/cua-window-s1.jpg` `92ea79915f13c68bec6473ed224bb0e51662aaa846167df37fc25e54872e5a47` (the byte-authenticated album-LIST window frame of the very transition being revalidated; no fresh list state can exist because the album was opened by attempt-12 and no authorized input has occurred since), post = THIS round's fresh CU window screenshot. Both frames window-space 327x643. Require `ALBUM_OPEN_VERIFIED` (exit 0) with `count_text` MATCH.
  - Supporting (non-gating) pair: pre = `attempt-12/frame-pre.png` `b88f7e09…`, post = fresh full-screen frame; recorded for transparency.
- Geometry binding: `live-window-geometry.json` bound to the fresh frame SHA (from the fresh AX read; window point rect and capture scale recorded) + `validate_live_geometry.py` (dims exact + gray MAD <= 12.0) -> require `GEOMETRY_BINDING_PASS`.
- Visual surface check (recorded as read-only observation): target album title + count visible, photo grid, no album list, no permission prompt, no unknown overlay.

## S2 — fresh menu detection + fresh candidate (zero input)
- **Menu presence pair** (frozen `detect_menu_popup.py`, defaults): pre = `attempt-13/frame-menu-pre.png` `0118b12fb758aa86fdd5b181c56005a94eef1be4b7cd60b005b547d9a47f0fb6` (byte-authenticated menu-absent full-screen reference of this same frozen album surface), post = THIS round's fresh full-screen frame.
  - Affirmative rule: `MENU_DETECTED` (exit 0) AND the freshly chosen bbox overlaps the fresh LINE window rect (the menu straddles the window's right edge; a bbox entirely outside the window rect would be recorded as unrelated screen noise, never upgraded).
  - A `NOT_DETECTED`/`BAD_INPUT`/disqualified result => STOP with zero input; report `MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`. No manual upgrade from eye/OCR alone; no historical menu coordinate.
- **Fresh Save All candidate** via the new frozen v7 locator on THIS round's fresh frame with the fresh bbox and the fresh frame-bound window geometry. Verdicts: `ELIGIBLE` (exactly one 儲存全部 row, row-order cross-check against the reference order `選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿`, candidate addressable) or fail-closed `NOT_FOUND` / `AMBIGUOUS` / `MENU_CONTENT_UNEXPECTED` / `NOT_ADDRESSABLE` / `BAD_INPUT`. Only `ELIGIBLE` advances; anything else => STOP, zero input.
- Candidate form: frame px, screen pt, app-local pt (= screen pt − window origin pt; the dispatch form). Candidate must lie inside the menu bbox, inside the addressable region (window interior ∩ menu bbox ∩ frame bounds), with the text-box ∩ addressable x-overlap >= 20 px, and inside the identified row's vertical extent.

## S0 — fresh staging preflight (only after S1/S2 pass; before any GUI input)
- Run id `RUN-YYYYMMDD-HHMMSS-01` generated fresh now; path `…/LINE-Backup-PoC/staging/<run_id>/`; frozen into everything below.
- Exactly one `mkdir` of the leaf; plus exactly one `mkdir` of `staging/` ONLY if `staging/` is machine-proven absent (its parent must already exist and be proven). No other filesystem writes outside evidence.
- Machine proofs (each recorded in `staging-preflight.json`): lexical equality realpath==abspath; no symlink component; parent `staging/` real and within `realpath(backup_root)`; leaf absent before mkdir; after mkdir 0 entries / 0 regular files / 0 bytes / not symlink / not mount point; staging != baseline and no ancestor/descendant relation; run_id never used before (ledger scan); writable proof (mkdir by this user + stat mode of parent and leaf); accepted baseline digest unchanged across the preflight (read-only recomputation before and after).
- Any failure => STOP, Save All input 0.

## S3 — Save All intent + at-most-once barrier
- Write `save-all-click-intent.json` (run_id, staging path, preflight SHA, fresh frame SHA, detector/locator tool SHAs, candidate in all three spaces, derivation, budget 1, used 0, `dispatch_state=NOT_ATTEMPTED`, `retry_budget=0`, `formal_state_write=false`), read back, re-hash.
- Immediately before the click call (inside the same dispatcher block, as the very next operation): write `SAVE_ALL_DISPATCH_ATTEMPTED` marker atomically, read back, then dispatch.

## S4 — final freshness gate + exactly one click
- Within <= 15 s before the click: fresh CU window screenshot + fresh full-screen frame + fresh AX read; re-run (all read-only):
  - `validate_live_geometry` on the fresh frame/CU shot/AX -> GEOMETRY_BINDING_PASS;
  - `verify_album_open` formal pair with post = fresh CU window screenshot -> ALBUM_OPEN_VERIFIED;
  - `detect_menu_popup` with pre = attempt-13 menu-absent reference, post = fresh frame -> MENU_DETECTED; chosen bbox B2 must equal the S2 bbox B1 exactly;
  - v7 locator on the fresh frame + B2 + fresh geometry -> ELIGIBLE; candidate C2 must equal the S2 candidate C1 exactly; identified row text must be the same 儲存全部 row.
- Any deviation => `ABORTED_BEFORE_SAVE_ALL_DISPATCH`, click budget used 0, STOP.
- Dispatch: exactly one `sky.click` call at C2. The call's invocation is the boundary: returned => `dispatch_state=RETURNED`, Save All used=1; throws/ambiguous => `dispatch_state=UNKNOWN`, Save All used=1, permanent no-retry barrier, manual reconciliation. Never a second call under any circumstance.

## S5 — post-dispatch observation only (read-only; no input of any kind)
- Capture schedule: full-screen #1 ~0.4 s; CU window state+screenshot ~1.2 s; full-screen #2 ~2.2 s; AX window read ~2.5 s.
- Frozen detector on the fresh pairs [pre-click frame vs post #1] and [pre-click frame vs post #2]; record components, OCR strings, verdicts.
- Surface classification (fail-closed): chooser affirmatively observed only by machine-readable evidence (e.g., a newly appeared AX window/element with panel semantics in LINE's app window list, and/or an unmistakable new surface in the frozen detector's output); else `TRIGGER_NOT_OBSERVED` (no new surface provable) or `TRIGGER_UNKNOWN` (anything else). No manual upgrade from historical expectation.
- Filesystem tripwire (read-only): accepted baseline manifest digest recomputed -> must equal `b7debe92…`; fresh staging inventory -> must remain 0 entries/0 bytes during Gate A observation. If staging gains any entry => `UNEXPECTED_PRE_CONFIRM_FILESYSTEM_WRITE`, stop, touch nothing.
- STOP unconditionally: the menu (if still open) is left as-is; no chooser interaction, no keyboard/Escape, no click-outside, no second ellipsis, no cleanup.

## Owner decision rules (verbatim intent preserved)
- A: fresh album-open != ALBUM_OPEN_VERIFIED -> stop, Save All 0. B: not verified menu -> stop, Save All 0. C: v7 not ELIGIBLE -> stop, Save All 0. D: all gates pass -> exactly one Save All click -> observation; success state `READY_FOR_CHOOSER_GATE_B_PLAN_OR_AUTHORIZATION` (never `READY_TO_DOWNLOAD`/`BACKUP_COMPLETE`); Save All itself is never bundled with chooser operations.
