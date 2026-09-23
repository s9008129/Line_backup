# Rev27c ELLIPSIS_THEN_SAVE_ALL_GATE_A — combined one-shot (attempt-06; Gate lineage continues attempt-05) — runbook, pre-declared BEFORE any live observation or input

## Binding
- App `jp.naver.line.mac`; group `旻謙允禎成長日記`; album `2024/05/13～05/17`; expected count 57.
- Authorization (this round, new owner one-shot): `AUTHORIZATION_TYPE = REV27C_ELLIPSIS_THEN_SAVE_ALL_GATE_A`, `AUTHORIZATION_ID = REV27C-LIVE-GATE-A-AFTER-LOCATOR-V8`.
- Budgets: `ellipsis_click <= 1`, `save_all_menu_item_click <= 1`, total GUI input <= 2, `staging mkdir <= 2`; everything else 0 (album-card, navigation, second ellipsis, second Save All, retry, other menu-item, chooser interaction, keyboard/Escape, scroll, AX write, bring-to-front, app acquisition, Go to Folder, path entry, Return, destination confirm, download-completion, cleanup/delete).
- Owner-prepared start state (owner statement): LINE frontmost; target album opened; `2024/05/13～05/17` with 57-photo context and photo grid visible; album-level ⋮ visible; ⋮ popup menu NOT open; no occluding app. If live evidence does not match => fail closed. Codex performs NO bring-to-front, NO app acquisition, NO album reopening, NO album-card click.
- Predecessor lineage: attempt-05 achieved ALBUM_OPEN_VERIFIED_COMPOSITE -> frozen v5 ELIGIBLE -> exactly one ellipsis click -> MENU_SURFACE_AFFIRMATIVELY_OBSERVED with 儲存全部 affirmatively identified, then STOPPED fail-closed at the frozen v7 locator (`MENU_CONTENT_UNEXPECTED`; non-target 修改相簿名稱 misread 修改相簿名般) with the menu left open, Save All 0/1. The attempt-05 menu must NOT be reused this round; the owner states the menu is closed and this round re-establishes everything fresh in ONE uninterrupted attempt.
- Rev27c replan (offline, completed, committed f3ab3ee): plan rev27c-2 `906e949b…` (two fresh reviews both PLAN_APPROVED), new append-only v8 Save All locator `c5ad46861706a9a2c1c4d477caeda2a809c87c5488844f14a4d3efb34c668a86`, selftests 43/43 (results `943f2939…`), attempt-05 offline replay ELIGIBLE (unique candidate), historical-coordinate injection zero effect; target fuzzy matching and historical-coordinate fallback remain FORBIDDEN.
- Frozen tools (SHAs re-verified from disk this round):
  - `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418` (the ONLY ellipsis locator; v4 fallback forbidden)
  - `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`
  - `tools/v7/album_detail_lineage_guard.py` `cdff187e0b4f2fab2ba537e99aaacc810279c14f28a995d034fc76c73b6dde52`
  - `tools/detect_menu_popup.py` `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
  - v8 Save All locator `c5ad4686…` (the ONLY Save-All candidate authority; frozen v7 locator `ea09c1ca…` unmodified and NOT executed this round)
  - round-local read-only helpers carried forward byte-identical from attempt-05: `tools/ax_window_bounds.swift` `5c615a90…`, `tools/validate_live_geometry.py` `ea4230e4…`
- No historical coordinate is ever used as input (`[304,50]`/`[305,50]`/`[39,923]` and all formula rows permanently barred). A fresh candidate that numerically coincides with a historical value must still be independently derived from this round's frame.

## Pre-declared spaces and mechanisms (fixed BEFORE the run)
1. **CU window space = window-local pt** (1 px = 1 pt): the ellipsis locator output and both click spaces (`app.click([x, y], {mouseButton:"left", clickCount:1})` via the CU harness).
2. **Full-screen frame** = `/usr/sbin/screencapture -x`, device pixels at capture scale 2 (2294x1490 px = 1147x745 pt). Window rect in frame px = window_pt * 2 (re-read fresh this round).
3. **Dispatch forms**: exactly one ellipsis click and, later, exactly one Save All click; each dispatch is preceded by a freshness gate and followed by read-only observation; no retry under any outcome.
4. **Verdict vocabulary and STOP discipline**: any non-ELIGIBLE locator verdict, missing/ambiguous menu, missing target, baseline change, staging failure, or intent failure => STOP with the affected budgets unspent and all counters recorded truthfully.

## S1 — fresh album-detail observation (zero input)
- Read-only AX inventory (`ax_window_bounds.swift jp.naver.line.mac`) pre + fresh full-screen frame + read-only CU window state/shot.
- Required: LINE frontmost (`ax_frontmost = true`), focused+main detail window unambiguous, album `2024/05/13～05/17` with 57-photo context and photo grid visible, album-list NOT the active target, ⋮ menu NOT open, no overlay/permission prompt/occlusion.
- Any mismatch -> **STOP**, GUI input 0, no reopen/navigate/bring-to-front.

## S2 — fresh frame/window binding (zero input)
- AX post identical-or-equivalent to AX pre; `live-window-geometry.json` bound to this round's frame SHA + `validate_live_geometry.py` (pre-declared rule: dims exact AND gray MAD <= 12.0) -> require `GEOMETRY_BINDING_PASS`. Failure -> STOP, GUI 0, no screenshot retry.

## S3 — fresh composite revalidation (zero input)
- Frozen `verify_album_open.py`: window pair pre = a byte-authenticated album-LIST window shot from the lineage (attempt-19 `b9be8bfc…`), post = this round's fresh CU window shot -> require `ALBUM_OPEN_VERIFIED` (count MATCH); supporting screen pair pre = a byte-authenticated album-detail frame, post = this round's frame.
- Approved v7 lineage guard on THIS round's evidence (fresh AX inventory + CU AX text + CU window shot + fresh frame + `--frozen-album-open-json` whose post_sha256 == fresh frame SHA) -> require `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED` (exit 0, C0–C6 PASS).
- Composite = both. Otherwise STOP; v5 NOT executed; no ellipsis click. (attempt-03/15/16/18 precedent: title + 57 + changed_fraction alone is NOT enough.)

## S4 — frozen v5 ellipsis locator (zero input)
- Single invocation of `locate_album_ellipsis.py` on THIS round's fresh verified detail CU frame (title-bbox from this round's verify window result); require `ELIGIBLE` (exit 0) with exactly one header-band dot triple and a click_point derived from THIS frame. Any other verdict -> STOP, ellipsis 0, no v4, no tuning, no retry.

## S5 — exactly one ellipsis click (at-most-once)
- Final freshness gate (dispatch as the next action): require LINE still frontmost, fresh CU state equivalent, composite still holding. Then exactly one left click at the fresh v5 candidate (window-local pt). `ellipsis_used = 1`, GUI total = 1. Never a second ellipsis click; never retry.

## S6 — fresh menu observation (zero input after the click)
- Immediately: fresh full-screen frames; frozen `detect_menu_popup.py` pair B (pre = this round's pre-click frame, post = post-click frame) -> affirmative only if `MENU_DETECTED` with a popup-shaped bbox overlapping the fresh LINE window rect; independent ROI cross-check against byte-authenticated menu-open/menu-absent references; read-only OCR of the menu bbox (3x LANCZOS, tesseract chi_tra+eng) must contain `儲存全部` among the item strings.
- Required verdicts: `MENU_SURFACE_AFFIRMATIVELY_OBSERVED` AND target `儲存全部` affirmatively identified on THIS round's frame. Otherwise STOP (GUI total 1, Save All 0, never re-click the ellipsis). Non-target neighbor OCR noise is judged only by the reviewed v8 rules.

## S7 — approved v8 Save All locator (zero input)
- Inputs only: this round's fresh menu frame, this round's fresh frame-SHA-bound detector JSON, this round's frame-bound geometry JSON. Single run of `tools/v8/locate_save_all_menu_item.py` -> require `ELIGIBLE` with exactly one candidate; re-proves every HARD gate (frame/detector binding, popup shape, exact target tolerance 0 unique row, five-row structure with the reviewed ≤1-substitution non-target tolerance, row/neighbor geometry, safe-interior x/y). Any other verdict -> STOP; Save All 0; no tolerance expansion; no hot-fix.

## S8 — baseline tripwire recheck (zero input)
- Recompute the accepted-baseline manifest: require 57 files / 17,924,900 bytes / digest `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` AND identical to the pre-round inventory. Mismatch -> STOP; Save All 0.

## S9 — fresh staging preflight (only after S6+S8 PASS; strictly before Save All)
- Fresh `run_id = RUN-YYYYMMDD-HHMMSS-01`; path `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<run_id>/`; mkdir <= 2 (parent only if machine-proven absent + leaf). Machine proofs (all required): authorized canonical root, no symlink escape, run_id unique, leaf absent-before/exists-after, 0 entries / 0 bytes, staging != baseline and no ancestor/descendant relation, writable, not reused. Any failure -> STOP, Save All 0. Staging policy PRESERVE; cleanup/delete forbidden.

## S10 — durable Save-All intent (before dispatch)
- `save-all-click-intent.json` with: authorization type/id, run_id, staging path, baseline inventory SHA, staging-preflight SHA, fresh composite SHA, fresh menu frame SHA, menu detector SHA, menu observation SHA, v8 source SHA, v8 result SHA, fresh Save All candidate + derivation, `ellipsis_used = 1`, Save All budget = 1 / used = 0, `dispatch_state = NOT_ATTEMPTED`, `retry = 0`, chooser interaction = 0. Write + read back + re-hash; failure -> STOP.

## S11 — exactly one Save All click (at-most-once; dispatch semantics)
- Final gate (dispatch as the very next action): LINE still frontmost, same detail lineage, menu still present (fresh frame + detector), fresh candidate still valid, baseline unchanged, staging PASS, intent PASS. Then exactly one left click at the fresh v8 candidate. `save_all_used = 1`, total GUI input = 2, permanently consumed; never a second Save All click.
- Dispatch semantics: not sent -> `NOT_ATTEMPTED`; sent+returned -> `RETURNED`; possibly sent/ambiguous -> `UNKNOWN` (then `save_all_used = 1`, `retry = 0`, `manual_reconciliation_required = true`; never click again without a reconciliation revision).

## S12 — resulting-surface observation only (GUI budget = 0)
- Capture post frames (~0.4 s, ~2.2 s) + read-only CU/AX. Answer the 13 questions: menu disappeared? new panel/modal/window? process/app identity? window/panel role? title? visible controls? visible fields? visible buttons? chooser affirmatively observed? chooser type? current/default destination safely readable? staging still empty? accepted baseline unchanged?
- `CHOOSER_AFFIRMATIVELY_OBSERVED` only if THIS round's fresh evidence proves it; never upgrade from historical runs. Ambiguous -> record exact evidence and STOP.
- Filesystem tripwire (pre-Save-All, immediate post-Save-All, end): baseline digest must remain `b7debe92…`; staging inventory read-only; if staging gains any file before a chooser confirm -> `UNEXPECTED_PRE_CONFIRM_FILESYSTEM_WRITE` -> STOP (no delete, no cancel, no retry).
- **STOP.** No chooser interaction of any kind (no click, keyboard, Escape, Cmd+Shift+G, Go to Folder, path entry, Return, confirm, cancel, click outside, scroll, AX write). Gate B requires a NEW owner authorization.

## Known non-blocking items (disclosed, no action)
- Rev27c reviews recorded that some malformed/type-invalid geometry inputs may exit 1 instead of a specified refusal exit code; fail-closed still holds. If legitimate live evidence triggers this, STOP; no hot-fix.
- The committed `f3ab3ee` message cites the pre-append run-ledger bytes; the committed 99-scope-status manifest carries the current correct ledger hash. Historical commit not modified.

## Hard counters (this round)
album-card 0; navigation 0; ellipsis <= 1; Save All <= 1; total GUI <= 2; retry 0; second ellipsis 0; second Save All 0; other menu item 0; chooser interaction 0; keyboard 0 (Escape included); scroll 0; AX write 0; bring-to-front 0; app acquisition 0; destination confirm 0; download-completion 0; cleanup/delete 0; staging mkdir <= 2; formal state/config write 0.

## Success state
ALBUM_OPEN_VERIFIED_COMPOSITE + v5 ELIGIBLE + ellipsis = 1 + MENU_SURFACE_AFFIRMATIVELY_OBSERVED + target 儲存全部 affirmative + v8 ELIGIBLE + baseline PASS + staging PASS + Save All = 1 + dispatch_state = RETURNED + CHOOSER_AFFIRMATIVELY_OBSERVED + staging still empty + baseline unchanged => `READY_FOR_CHOOSER_GATE_B_AUTHORIZATION`. Never READY_TO_DOWNLOAD / BACKUP_COMPLETE.
