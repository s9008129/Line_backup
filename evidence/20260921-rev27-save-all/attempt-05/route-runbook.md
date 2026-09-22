# Rev27 ELLIPSIS_THEN_SAVE_ALL_GATE_A — combined one-shot (attempt-05; Gate lineage continues attempt-04) — runbook, pre-declared BEFORE any live observation or input

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記`; album `2024/05/13～05/17`; expected count 57.
- Authorization (this round, new owner one-shot): `AUTHORIZATION_TYPE = ELLIPSIS_THEN_SAVE_ALL_GATE_A`, `AUTHORIZATION_ID = REV27-ELLIPSIS-TO-SAVE-ALL-GATE-A-AFTER-ATTEMPT04`.
- Budgets: `ellipsis_click <= 1`, `save_all_menu_item_click <= 1`, total GUI input <= 2, `staging mkdir <= 2`; everything else 0 (album-card, navigation, second ellipsis, second Save All, retry, other menu-item, chooser interaction, keyboard/Escape, scroll, AX write, bring-to-front, app acquisition, Go to Folder, path entry, Return, destination confirm, download-completion, cleanup/delete).
- Owner-prepared start state (owner statement): LINE frontmost; target album opened; `2024/05/13～05/17` with 57-photo context and photo grid visible; album-level ⋮ visible; menu NOT yet opened; no Terminal / media toolbox / Chrome occluding LINE. If live evidence does not match => fail closed. Codex performs NO bring-to-front, NO app acquisition.
- Predecessor lineage: route attempt-19 achieved (18:15–18:19) ALBUM_OPEN_VERIFIED_COMPOSITE -> frozen v5 ELIGIBLE -> exactly one ellipsis click -> MENU_SURFACE_AFFIRMATIVELY_OBSERVED with 儲存全部 identified, then STOPPED with the menu left open. Gate-A attempt-04 then fail-closed STOPPED (LINE had lost frontmost; menu gone; zero GUI input; blocker `MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`). This round re-does the whole chain in ONE uninterrupted attempt.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (the ONLY ellipsis locator; v4 fallback forbidden)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52` (selftest results affb3602…, 22/22 PASS)
  - `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`, `tools/v5/locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162` (v7 reader dir)
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - round-local byte-identical read-only helpers (attempt-04/tools -> attempt-05/tools): `ax_window_bounds.swift` `5c615a90…`, `validate_live_geometry.py` `ea4230e4…`, `locate_save_all_menu_item.py` `ea09c1ca…` (v7-class Save-All locator; re-frozen + re-selftested + re-reviewed THIS round before any click).
- No historical coordinate is ever used as input (`[304,50]`/`[305,50]`/`[39,923]`/`[39,926]` and all formula rows permanently barred). A fresh candidate that numerically coincides with a historical value must still be independently derived from this round's frame.

## Pre-declared spaces and mechanisms (fixed BEFORE the run)
1. **CU window space = window-local pt** (1 px = 1 pt): the ellipsis locator output and the click space (`lineApp.click([x, y], {mouseButton:"left", clickCount:1})` via `cua_repl`).
2. **Full-screen frame** = `/usr/sbin/screencapture -x`, device pixels at capture scale 2 (2294x1490 px = 1147x745 pt). Window rect in frame px = window_pt * 2 (re-read fresh this round).
3. **Dispatch forms**: exactly one ellipsis click and (conditionally) exactly one Save All click via `cua_repl` `lineApp.click`, each invoked exactly once, no other input.
4. **Order**: P0 (this file + authorization-scope-check.json + authorization-record.json + 00-start-state.json, before any live observation) -> S1 fresh album-detail observation -> S2 fresh frame/window binding -> S3 fresh composite (frozen verifier + v7) -> S4 frozen v5 ellipsis locator -> S5 exactly one ellipsis click -> S6 fresh menu observation + fresh Save All candidate (frozen-class locator selftest/freeze/review first) -> S7 baseline tripwire -> S8 staging preflight -> S9 durable Save-All intent -> S10 exactly one Save All click -> S11 resulting-surface observation only -> STOP.

## S1 — fresh album-detail observation (zero input)
- Read-only AX (`/tmp/attempt05/ax_window_bounds`) -> require `ax_frontmost=true`, `frontmost_application=jp.naver.line.mac`, exactly one focused/main standard LINE window, readable position/size; fresh full-screen frame; post AX identical.
- Fresh read-only CU capture (window screenshot + AX text).
- Visual/OCR check: photo grid + `2024/05/13～05/17` + `57張照片`; no album-list controls/rows in the active target; no permission prompt; no unknown overlay; no occlusion; the ⋮ visible and NOT yet activated (no menu on screen).
- Any mismatch -> STOP, GUI input 0, no reopen/navigate/bring-to-front.

## S2 — fresh frame/window binding (zero input)
- `live-window-geometry.json` bound to this round's frame SHA + `validate_live_geometry.py` (pre-declared rule: dims exact AND gray MAD <= 12.0) -> require `GEOMETRY_BINDING_PASS`. Failure -> STOP, GUI 0, no retry of the screenshot.

## S3 — fresh composite revalidation (zero input)
- Frozen `verify_album_open.py`: window pair pre = `attempt-19/a4-precheck-window-cu.jpg` `b9be8bfc…` (byte-authenticated album-LIST window), post = this round's fresh CU window shot -> require `ALBUM_OPEN_VERIFIED` (count MATCH); supporting screen pair pre = `attempt-19/frame-s1.png`, post = this round's frame.
- Approved v7 lineage guard on THIS round's evidence (fresh AX inventory + CU AX text + CU window shot + fresh frame + `--frozen-album-open-json` whose post_sha256 == fresh frame SHA) -> require `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` (exit 0, C0–C6 PASS).
- Composite = both. Otherwise STOP; v5 NOT executed; no ellipsis click. (attempt-03/15/16/18 precedent: title + 57 + changed_fraction alone is NOT enough; v7 must PASS.)

## S4 — frozen v5 ellipsis locator (zero input)
- Single invocation of `locate_album_ellipsis.py` on THIS round's fresh verified detail CU frame (title-bbox from this round's verify window result); require `ELIGIBLE` (exit 0) with exactly one header-band dot triple and a click_point derived from THIS frame. Any other verdict -> STOP, ellipsis 0, no v4, no tuning, no retry.

## S5 — exactly one ellipsis click (at-most-once)
- Final freshness gate (dispatch as the next action): require LINE still frontmost, CU shot unchanged-or-equivalent (fresh re-read), composite still holding. Then exactly one left click at the fresh v5 candidate (window-local pt). `ellipsis_used = 1`, GUI input count = 1. Never a second ellipsis click; never retry.

## S6 — fresh menu observation + fresh Save All candidate (zero input after the click)
- Immediately: fresh full-screen frame; frozen `detect_menu_popup.py` pair B (pre = this round's pre-click frame, post = post-click frame) -> affirmative only if `MENU_DETECTED` with a bbox overlapping the fresh LINE window rect; independent ROI cross-check against byte-authenticated menu-open/menu-absent references; read-only OCR of the menu bbox (3x LANCZOS, tesseract chi_tra+eng psm 6) must contain `儲存全部` among the item strings.
- Required verdicts: `MENU_SURFACE_AFFIRMATIVELY_OBSERVED` AND `SAVE_ALL_ITEM_AFFIRMATIVELY_IDENTIFIED`. Otherwise STOP (GUI total 1, Save All 0, never re-click the ellipsis).
- Fresh Save All candidate: this round re-proves the locator (determinism selftest positive x2 byte-identical ELIGIBLE on this round's menu frame; negative fixture -> NOT_FOUND; barred-literal grep; SHA record in `selftest-attempt05/` + `locator-freeze-attempt05.json` + `locator-review-attempt05.md`), then a single run of `locate_save_all_menu_item.py <fresh frame> --detector-json <fresh bound detector JSON> --geometry <fresh bound geometry>` -> require `ELIGIBLE`, exactly one candidate. Otherwise STOP.

## S7 — accepted baseline tripwire (read-only)
- Recompute the 57-file manifest: require 57 files / 17,924,900 bytes / digest `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` (label `READ_ONLY_ACCEPTED_BASELINE`). Mismatch -> STOP; Save All 0.

## S8 — fresh staging preflight (only after S6+S7 PASS; strictly before Save All)
- Fresh `run_id = RUN-YYYYMMDD-HHMMSS-01`; path `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<run_id>/`; mkdir <= 2 (parent only if machine-proven absent + leaf). Machine proofs (all required): authorized canonical root, no symlink escape, unique/new run_id, leaf absent-before/exists-after, 0 entries / 0 bytes, staging != baseline and no ancestor relation, writable, not reused from a failed run, baseline unchanged around the mkdir. Any failure -> STOP, Save All 0. Staging policy PRESERVE; cleanup/delete forbidden.

## S9 — durable Save-All intent (before dispatch)
- `save-all-click-intent.json` with: authorization type/id, run_id, staging path, accepted-baseline inventory SHA, staging-preflight SHA, fresh composite evidence SHA, fresh menu frame SHA, menu observation SHA, detector/tool SHA, fresh Save All candidate + derivation, `ellipsis_used = 1`, Save All budget = 1 / used = 0, `dispatch_state = NOT_ATTEMPTED`, `retry = 0`, chooser budget = 0. Write + read back + re-hash; failure -> STOP.

## S10 — exactly one Save All click (at-most-once; dispatch semantics)
- Final gate (dispatch as the very next action): LINE still frontmost, same album-detail lineage, menu still present (fresh frame + detector), fresh candidate still valid (<= ±3 px), baseline unchanged, staging PASS, intent PASS. Then exactly one left click at the fresh candidate. `save_all_used = 1`, total GUI input = 2, permanently consumed; never a second Save All click.
- Dispatch semantics: not sent -> `NOT_ATTEMPTED`; sent+returned -> `RETURNED`; possibly sent/ambiguous -> `UNKNOWN` (then `save_all_used = 1`, `retry = 0`, `manual_reconciliation_required = true`).

## S11 — resulting-surface observation only (GUI budget = 0)
- Capture post frames (~0.4 s, ~2.2 s) + read-only CU/AX. Answer: menu disappeared?, new window/panel/modal?, app/process identity, role, title, visible labels/fields/buttons, chooser affirmatively present?, chooser type, default/current destination safely readable?, staging files?, baseline unchanged?
- `CHOOSER_AFFIRMATIVELY_OBSERVED` only if this round's fresh evidence proves it; never upgrade from historical runs. Ambiguous -> record exact evidence and STOP.
- Filesystem tripwire (pre-Save-All, immediate post-Save-All, end): baseline digest must remain `b7debe92…`; staging inventory read-only; if staging gains any file before a chooser confirm -> `UNEXPECTED_PRE_CONFIRM_FILESYSTEM_WRITE` -> STOP (no delete, no cancel, no retry).
- **STOP.** No chooser interaction of any kind. Gate B requires a NEW owner authorization.

## Hard counters (this round)
album-card 0; navigation 0; ellipsis <= 1; Save All <= 1; total GUI <= 2; retry 0; second ellipsis 0; second Save All 0; other menu item 0; chooser interaction 0; keyboard 0 (Escape included); scroll 0; AX write 0; destination confirm 0; download-completion 0; cleanup/delete 0; staging mkdir <= 2; formal state/config write 0.
