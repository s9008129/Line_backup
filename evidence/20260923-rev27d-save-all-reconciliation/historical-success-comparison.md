# Historical successful Save All vs attempt-07 — comparison from retained evidence only

Round: Rev27d `ZERO_GUI_SAVE_ALL_DISPATCH_RECONCILIATION`. Only evidence that actually exists in the repository / archived state was used. Fields with no retained evidence are marked UNKNOWN, per the authorization.

## 1. The successful run (retained evidence)

`RUN-20260907-154331-01` — the run that produced the accepted baseline (album 2024/05/13–05/17, 57 files).

- State file `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json` (`intent.calibration`): screenshot 327×643; ellipsis ≈ (305,50); dot spacing d≈6; formula row step 32.4; **save_all_point (350,148.4)**; confidence HIGH.
- `run_log.md`: “Save-All dispatch returned with exactly one ellipsis click and one Save All click, with no dispatch error. The expected macOS folder chooser appeared.” — “Atomic dispatch action EAD45337-…” — then Go to Folder with the exact destination (keyboard chord + path field, one clipboard timeout recovered via `setValue`), one confirmation, download “正在下載... 0/57”; destination first showed stable zero-byte placeholders, later completed.
- `intent.trigger_outcome = CHOOSER_CONFIRMED`.

**Observed anomaly in the historical record:** the successful point's x = 350 exceeds the recorded screenshot width (327). The retained evidence does not document how the old dispatch consumed this coordinate, so the historical coordinate space/mechanism **cannot be reconstructed** → UNKNOWN (not “different”, not “same”).

## 2. Failure / wrong-effect precedents in the same era

- `RUN-20260907-101314-01`: dispatch then SAFE_ABORT; owner attestation recorded: “Save All was not triggered”, “**popup click missed Save All**”, “folder chooser never appeared” → an affirmative miss precedent for formula coordinates.
- `RUN-20260908-124357-01`: one ellipsis + one Save All invocation returned without error; **no chooser**; `trigger_outcome UNKNOWN`; `failure_boundary AFTER_SAVE_ALL_INVOCATION`; `save_all_click_count 1` → the same “returned but no chooser” shape as attempt-07, one year earlier.
- `RUN-20260907-132845-01`: calibration first-row click entered selection mode “已選擇0個項目” (cancelled) → a wrong-effect precedent.
- `evidence/20260915-capability-matrix.md`: “one prior coordinate activated Rename” → a wrong-row **activation** precedent for coordinate-driven menu dispatch.

## 3. Field-by-field comparison (attempt-07 vs historical success)

| field | historical success (2025-09-07) | attempt-07 (2026-09-23) | comparison |
|---|---|---|---|
| LINE / macOS version recorded | not recorded → UNKNOWN (current LINE 26.0.2 installed 2026-03-05; current macOS 26.6.2/25G83 installed 2026-09-01; success predates both) | LINE 26.0.2, macOS 26.6.2 (25G83) | UNKNOWN |
| menu geometry (popup bbox) | not recorded | popup bbox px [1008,182,1246,485]; AXDialog pt [494,81,137×167] | UNKNOWN historically |
| Save All row geometry | not recorded (only a single formula point) | text band px [1047,316.33,1148.33,340.67]; x_safe/y_safe | UNKNOWN historically |
| candidate derivation | formula/row-order calibration (ellipsis (305,50), first-row (350,83.6), step 32.4 → (350,148.4)) | fresh machine-derived: OCR + geometry from the fresh frame, midpoint of x_safe/y_safe → (319.75,135.25) → args (320,135) | different derivation method; historical coordinate not machine-verified against row geometry (no retained hit-test) |
| click API / dispatch mechanism | “Atomic dispatch action EAD45337-…” (internal mechanism not documented in retained evidence) | CU IPC click, `lineApp.click([320,135])` → `ComputerUseIPCAppPerformActionRequest{click:{at:{coordinate:[320,135]}}}` | UNKNOWN whether the mapping/mechanism differs |
| coordinate-space convention | not documented → UNKNOWN | documented window-local + empirically anchored (overlay/glyph/semantic) | UNKNOWN historically |
| click call arguments | not retained in machine form (point (350,148.4)) | [320,135] window-local pt → screen (531,164) pt / px (1062,328) | not comparable |
| popup position | not recorded | AXDialog [494,81,137×167] pt | UNKNOWN historically |
| chooser appearance timing | appeared after the dispatch; then Go to Folder etc. | never observed (4 frames 11:29:34→11:37:23, 3 AX reads, CG list, process state) | outcome differs; mechanism unexplained |
| AX/window transition | chooser panel appeared | popup AXDialog gone; window set back to pre-popup 3 windows; no new window | differs |
| filesystem behavior | download started only after confirmation; zero-byte placeholders then completion | staging 0/0; no writes anywhere checked; baseline unchanged | differs (consistent with no confirmation) |

## 4. Bottom line

- The historical success used a **formula/calibration-based coordinate** that was **never machine-verified to lie inside the row**, and the same scheme produced documented misses and one wrong-row activation. It is not a template that can be copied.
- Whether the historical dispatch used a different coordinate mapping or a different activation mechanism than attempt-07 is **UNKNOWN** from retained evidence; the recorded “atomic dispatch action” is not the same documented path as the current CU `lineApp.click`, but the old mechanism's internals are not retained.
- The only machine-verified physical point in the entire Save All history is attempt-07's (this round), and it is inside the row (see `hit-test-reconstruction.json`).
- Historical and current menu/row geometry cannot be compared numerically (historical geometry not retained). No historical coordinate may be used for any future dispatch.
