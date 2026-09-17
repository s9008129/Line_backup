# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 33
- REVIEWED_PLAN_REVISION: 22
- REVIEWED_PLAN_SHA256: 426fe6a1c758e96667e970021a80e20b68396c5af6a4ccaf65672772c514734b (2,041 lines; 278,141 bytes; re-computed before reading, before writing this report, and after writing — all three identical; matches the mandated value)
- PLAN_SNAPSHOT_PATH: none — this review is write-limited to this report file; the mandated hash re-verification (before/writing/after) is the substitution
- Repository anchor: branch master, HEAD a68f890; plan.md frozen across the review
- Reviewer: independent Codex CLI agent, fresh context; no Planner transcript loaded except the mandated owner lines (1034, 1063) and the two surrounding presentation lines
- Review inputs (order): user mandate → session transcript L1034/L1025/L1048/L1063 → plan.md Rev22 (all sections) → repository re-derivation (freeze set, v4/v3/v2 tool sources, self-test summaries, both user-fact records, attempt-05 artifacts, e2e/attempt-06) → raw falsification replays (below)
- Freeze-set verification: `evidence/20260917-freeze-set/rev22-freeze-set.json` enumerates 71 artifacts; every one re-hashed from disk: 0 missing, 0 mismatched. This covers all `tools/*.py` (v1/v2/v3 family), `tools/v4/*.py`, `tools/vision/vision_ocr.swift`, both self-test summaries (v2 `d8ffc129…` 2,946 B; v3 `17840e91…` 4,250 B; v4 `5ad2be10…` 11,718 B), `attempt-03/04/05/**`, both user-fact records, `e2e/attempt-06/e2e_report.md` (`14b44c94…`), and review attempts 30/31 (`92d5be16…`, `c80a14da…`). No artifact differs from what Rev22/§22 claims; all §22-cited hashes and byte counts that I spot-checked (v4 tool set `22a4e9ef/bb52aff1/ffa82aed/b77e3d51`, helper source `4fc9fa2b`, v3 set `500fcadb/60e3120a/80504262`, v2 locator `8c8b6fc7`, detector `6ae9c250`, v4 self-test `5ad2be10`, attempt-05 ledger `17b17203`, album-open-verify `ffa5d963`, v1 record 1,746 B `2cd7eccd…`, v1.1 record 1,741 B `a8c10551…`, human-gate answer 1,438 B `03ffff57…`) reproduce exactly. The 21-anchor `frozen-recheck.json` (e2e/attempt-06) is UNCHANGED.
- Disclosure (read-only replays): transient outputs were written only under /tmp (`/tmp/rev33_v4_*`, `/tmp/rev33_v3_*`, `/tmp/rev33_ellipsis_*`; disclosed, left in place outside the repo). The replays transiently created `__pycache__/` under `evidence/20260916-route/tools/`, `evidence/20260916-route/tools/v4/` and `src/line_backup_acceptance/`; all three were removed, restoring the pre-review tree. `git status` before and after this review shows the same pre-existing, not-author-of-this-review state: `M evidence/20260917-owner-decisions/owner-decisions-rev22.json` (worktree `0664b5fb…` vs committed HEAD `9d6b72e0…`; the diff is the documented CORR-01 `correction_history` entry at 22:18 responding to review/attempt-32 RV-32-1, self-declared plan-hash-neutral) and untracked `review/attempt-32/`, `evidence/20260917-freeze-set/`, `evidence/20260917-owner-briefing/`. No attempt-32 content was read.
- One plan edit would invalidate this review; this report reviews Rev22 at the hash above and nothing else.

## OWNER_VERDICT
- 這版要做什麼：照您已選的「B」再走一次受控路線（新修訂、新的一次性關卡；「開相簿 → 看一眼相簿裡的 ⋮」，全程只觀察、不點任何選單項目），但這次「看畫面讀字」的引擎換成已自我測試 16/16、並在同一張冷凍畫面上把 57 讀對（舊引擎讀成 75）的 macOS Vision v4 讀取器；同時採用「更正版紀錄」v1.1 作為來源證明。
- 真正必要的（CORE）：v1.1 通過「一字不差」契約檢核（我重跑：舊版 False、更正版 True）；attempt-06 只送兩個各一次的左鍵（相簿卡、⋮），S5 驗證必須用 v4 讀取器且失敗即停、不重試；所有 v1/v2/v3 工具、舊證據、57 張照片、正式資料一字不動。
- 支撐性、不擋結案：螢幕探測、v4 說明文件、建置紀錄；失敗只記 UNAVAILABLE，不卡整體。
- 什麼會卡住整套：只有 CORE 失敗才會；另外執行時您的畫面必須停在「相簿列表且看得到目標卡片」，否則這次一個輸入都不送、只記錄並請您復原。
- 設計是否過度：沒有。v4 工具鏈在 Rev21 已完成並凍結，這版只加「跑一次 + 驗一次」，沒有新依賴、沒有新產品程式碼。
- 最大風險（我這次發現的）：驗收表裡有一條 CORE 規則（V22_S5_BOUND_TO_V4_READER）寫成「attempt-06 過程中任何 tesseract 判斷都是失敗」，但流程本身（S10）依規定必須重用「tesseract 版」的選單偵測器——兩句互相打架。照字面走，一次完全正確的 attempt-06 也會被判成失敗。這不是方向錯，是規則文字要修一句（見 RV-33-1）；另有 3 個小的行號／版號殘留要一起修。修完再複審即可，不必重做架構。

## GOAL_BASELINE
Reconstructed from the owner's own words only (session `01a0af3c-6693-72b2-abf2-095a3317e9a4`; real user messages verified at lines 1034 and 1063):
- L1034 (2026-09-17T13:29:07.582Z), verbatim: `請深度梳理上下文後，用白話、一般人或非技術人員可以理解的方式告訴我，為什麼這一次做的測試失敗了，以及它的瓶頸是什麼。`
- The option presentation quoted by §22.1 sits at **L1025** (2026-09-17T13:27:32.926Z, assistant), verbatim markers confirmed: 「路線：**A** 記成「這條路不需要」關閉卡點 ／ **B** 開新修訂＋再授權一次「⋮ 只觀察」（不點任何選單項目；新修訂會把驗證改用新 Vision 讀取器）。建議 **B**。」 and 「來源紀錄：**(i)** 用您先前已同意的「更正版紀錄」… ／ **(ii)** 您重新給一次精確答案。建議 **(i)**。」. L1048 (13:30:01.805Z) contains only the closing `回覆範例：「1 選 B；2 用更正版紀錄」` line, not the quoted excerpt.
- L1063 (2026-09-17T13:38:29.198Z), verbatim: `1 選 B；2 用更正版紀錄`. This is the **only** real user-message carrier: L1064 is the harness echo (`event_msg item_completed`), L1164/L1220 are `<subagent_notification>` messages, and L1025/L1048 are assistant messages. `evidence/20260917-owner-decisions/owner-decisions-rev22.json` records both presentation lines (1025 and 1048) correctly.
- PRIMARY_OUTCOME (this wave): (G1) run the corrected route attempt-06 once, with S3/S5/S6 bound to the frozen v4 Vision reader, and machine-observable AFFIRMATIVE at the album level → route no longer a scoped CORE blocker; (G2) adopt the corrected v1.1 record so §16.4 re-derives `SOURCE_CORRESPONDENCE=CONFIRMED`.
- MUST_NOT_BREAK: at-most-once inputs (retry 0, click 1 per input, menu-item 0, keyboard 0, images 0); a stop after input #1 never re-authorizes input #2; prior v1/v2/v3 bytes, both ledgers, gates 1-3, attempt-01..05, destination and formal state read-only; 禎 U+798E / 楨 U+6968 never merged.
- CRITICAL_PATH: approve this revision → Stage 03 handoff (bind v4 as official + gate-4 + budgets) → Stage 04 freeze gate-4/runbook/v4 set before any input → attempt-06 run → Stage 05 `e2e/attempt-07` re-derives both closure facts from fresh evidence. E2E_REQUIRED stays NO (INTEGRATION acceptance; the live run is the subject under test, not a repeated E2E).

## GOAL_ALIGNMENT
- PASS. The CORE set traces 1:1 to the owner's two decisions; the wave's primary value is closing the two remaining result-① gaps (route evidence and source correspondence), and both are exactly what the owner authorized. No gold-plating: no new product code, no new dependency, no scope beyond the one album.
- The route subject and the source-record subject are kept separate; a failure of either is recorded honestly and does not rewrite the other. No hidden expansion of the owner's B decision beyond the two directed inputs, disclosed in §22.2/§22.7 (see residual note on the narrow alternative reading).

## NECESSITY_AND_TRACEABILITY
- `REQ-V22-1` ↔ v1.1 adoption ↔ owner decision 2; `REQ-V22-2` ↔ attempt-06 ↔ owner decision 1; `NFR-V22-1..3` ↔ the frozen-set/one-shot/read-only invariants; `NFR-V22-4` is correctly SUPPORTING/non-gating. Every material check row in §22.6 maps to a requirement or invariant.
- Traceability defect (RV-33-1): `V22_S5_BOUND_TO_V4_READER` as written ("a tesseract-based verdict anywhere in the attempt-06 chain is TASK_REGRESSION") also fires on the mandated S10 detector, which the same revision pins as reused byte-identically — the check contradicts the requirement it implements.

## GATE_AND_VETO_AUDIT
- Six §22.6 rows: five CORE (HARD_CLEAN, NOT_ALLOWED waivers) and one SUPPORTING (NON_GATING). CORE rows are outcome/must-not-break checks tied to owner decisions; no supporting item can block; no veto is hidden in prose.
- One defect: a CORE row whose literal failure rule fires on the plan's own mandated correct behavior (RV-33-1) — that is an unsatisfiable gate as written, not a proportionality question.
- Owner-reserved items: A/B is decided (B); `ROUTE_NOT_NEEDED` remains not-taken per §22.5/OOS-V22-3 — correct.

## COUPLING_AND_FAILURE_CONTAINMENT
- Attempt-06's stop gates are properly sequenced: S5 must return `ALBUM_OPEN_VERIFIED` before input #2 exists; S3/S6 refusals stop with zero further input; a zero-input stop is resume-eligible, an input-#1 stop is not re-authorized (§22.3).
- Failure paths of the v4 reader degrade locally to empty words → frozen refusal verdicts (empirically re-verified: broken helper → `TARGET_TITLE_NOT_FOUND(2)` / `NO_ELLIPSIS_FOUND(3)`, no `click_point`); no path turns a reader failure into a pass (see FALSIFICATION F3/F4).
- The route subject cannot contaminate the source-record subject or the frozen attempt-05 verdict; prior evidence is bound immutable.

## DESIGN_ECONOMY
- Minimal delta: reuse the already-frozen v4 tool set + v4 self-test + detector; add only the run (attempt-06 evidence) and the re-derivation. The deletion test fails for nothing in the CORE set.
- A simpler plan was considered: skipping attempt-06 and closing as `ROUTE_NOT_NEEDED` was option A — the owner explicitly chose B, so the two-input run is the required, not the simpler-but-wrong, path. No cheaper design satisfies the owner's chosen outcome.

## CRITICAL_PATH_AND_PRIORITY
- Correct order (freeze ⇒ run ⇒ verify), CORE before supporting. No priority inversion: the screen probe/readme/build record cannot delay the run; the run does not wait on the deferred live-capture layer.
- Two stale literals could mis-prioritize execution: the closure section still says review "Revision 21"/"(21 at this writing)" (RV-33-3) and earlier sections still bind Stage-05 re-derivation to the consumed `e2e/attempt-06` (RV-33-4). Both are textual; the header's attempt-07 binding is the operative one.

## REQUIREMENT_FIDELITY
- Independently re-derived (raw results in FALSIFICATION): v1.1 differs from v1 by exactly one leaf (`answer.part_2.confirmed_album`, U+FF5E preserved in both) and only v1.1 passes `user_fact_v1_matches` (v1 False, v1.1 True); on the still-present attempt-05 frames the frozen v4 `verify_album_open.py` returns `ALBUM_OPEN_VERIFIED`/0 with count 57 where the frozen v3 tool returns `TARGET_MISMATCH`/4 with count 75; the v4 helper record carries `resolved_from "env"`, `binary_sha256 f54628e8…`, source `4fc9fa2b…`.
- Budgets in §22.3 (`album_card 1`, `ellipsis 1`, `navigation 1`, menu/keyboard/retry 0, captures ≤5) equal §20.2's corrected sequence and NFR-V22-2; the two inputs are a new one-shot authorization (gate-4), not a reuse of attempt-05's spent budget — §22.2 states this; the worktree-corrected decisions artifact (CORR-01) now says the same.
- Defect: RV-33-1 (check-row wording) — fidelity of the acceptance rule, not of the requirement itself.

## GROUNDING_AND_DRIFT
- All load-bearing hashes/bytes I cite are re-derived from disk, not re-read from the plan: plan SHA 3× identical; 71/71 freeze artifacts; v4/v3/v2 tool SHAs; self-test summaries (v4 `cases_failed 0`, 16 cases, expectations pinned to v3 `17840e91…`); the two records; the detector's tesseract call (source line 47) and its `verdict` emission (line 168).
- Drift found (all textual, none architectural): §22.1's line-1048 attribution (RV-33-2), the closure "Revision 21" literals (RV-33-3), the consumed-attempt-06 acceptance references in §19.1/§19.3/§20.3 (RV-33-4).

## ARCHITECTURE_AND_CONTRACTS
- Reader contract unchanged from Rev21 (Vision observation-line token unit, v3-shaped records, scales/geometry frozen); v4 files stay byte-frozen and are bound by hash; the v3 set is explicitly not used by this run's verdicts (§22.3 precondition 2).
- Fail-closed contract verified in source: every helper failure returns empty words with a recorded outcome (`vision_reader.py:151`, `:156-160`, `:190-196`, `:216-219`), and the tool verdict chain refuses on unreadable input (`verify_album_open.py:166-180`). No confidence value gates any verdict in `locate_album_ellipsis.py` (`conf` appears only at line 145 as recorded evidence). The one taxonomy nuance (empty stdout records `outcome "ok"` yet yields zero words) is RV-33-5; it cannot produce a pass.

## DATA_SECURITY_RELIABILITY
- Frozen set: 71/71 byte-identical; destination/formal state read-only; no re-download; no state/config/run-log write; no conversation image; no secret handling. The v1 record is never rewritten; v1.1 is a new versioned file authorized under §16.4's own "corrected re-authoring" clause (read at plan L927-929) and §19.1's single-leaf rule.
- Live-execution safety enumeration (FALSIFICATION F5): the plan can cause exactly two GUI input events (one album-card left click, one album-⋮ left click), read-only `screencapture -x` (S2 once, S7 once, S9 ≤5 within ~4 s), read-only AX/screenshot observation, and a temp-dir `swiftc -O` helper build. No menu-item activation, chooser, keyboard event, AX write, extra click, retry or bring-to-front path exists in the plan or in the frozen tools; the alternative narrow reading of decision 1 would send zero inputs.

## IMPLEMENTATION_SEQUENCE
- Preconditions before any input are correct and ordered: gate-4 + v4 runbook + v4 tool set + helper source + v4 self-test frozen and committed; ledger parented to `17b17203…`; then S1→S11 with the S3/S5/S6 substitutions and the S5 stop gate.
- RV-33-4 aside: the route attempt series (`evidence/20260916-route/attempt-06/`, does not exist yet) and the acceptance series (`.agent/.../e2e/attempt-06/`, consumed by Rev21; attempt-07 is next) share the number 06 with different meanings; earlier sections' "Stage 05 attempt-06" literals are what collide.

## TESTABILITY_AND_ACCEPTANCE
- The wave's acceptance is machine-checkable: two named records + the frozen matcher (raw outputs below), one run whose every verdict is a frozen-tool JSON with a reader block, and a Stage-05 re-derivation bound to `e2e/attempt-07` that runs no GUI input of its own.
- RV-33-1 makes one CORE acceptance row untestable-as-written (a correct chain triggers its TASK_REGRESSION clause); this must be fixed for the acceptance to be coherent. RV-33-5 is a taxonomy note for the handoff, no acceptance impact.

## SCOPE_AND_COMPLEXITY
- No new dependency, module, or state machine; the only new artifacts are run evidence and this wave's records. Complexity verdict: minimal and repository-consistent. Out-of-scope items (menu items, Save All, chooser, downloads, formal writes, any third input) are explicitly fenced.

## FALSIFICATION_RAW_RESULTS
### F0 — Owner transcript (raw)
- Real user messages carrying the answer: exactly one — L1063 `response_item`/`message`/`role=user`, ts `2026-09-17T13:38:29.198Z`, bytes of the text `1 選 B；2 用更正版紀錄`. L1064 is `event_msg item_completed` (echo). L1164/L1220 are `<subagent_notification>` (role=user carrier, not owner turns). L1025/L1048 are assistant messages. All four option markers (`路線：**A**`, `建議 **B**`, `來源紀錄：**(i)**`, `建議 **(i)**`) are present in L1025 and absent from L1048; L1048 contains only `回覆範例`. Result: §22.1's attribution of the quoted excerpt to line 1048 is wrong; the answer-carrier claim (line 1063) is correct.
### F1 — `user_fact_v1_matches` (`src/line_backup_acceptance/common.py:533`)
- Command shape: `user_fact_v1_matches(record, app_identifier='jp.naver.line.mac', group_key='line:jp.naver.line.mac:旻謙允禎成長日記', fp={"start_date":"2024-05-13","end_date":"2024-05-17","expected_images":57})`.
- Raw output: `v1 -> False | file_sha256 2cd7eccdb99da5dc… | bytes 1746`; `v1.1 -> True | file_sha256 a8c1055137d14026… | bytes 1741`.
- Structural leaf diff (27 leaves each): exactly one differing leaf — `/answer/part_2/confirmed_album`: v1 `'2024/05/13～2024/05/17'` → v1.1 `'2024/05/13～05/17'`; both strings use U+FF5E (0xFF5E) for ～, no ASCII tilde in either file. All other leaves (including the single `evidence[]` entry `human-gate-answer-20260917.json`, 1,438 B, `03ffff57…`, re-hashed by the matcher for v1.1) are identical.
- Conclusion: plan §22.4's claim is reproducible; v1 must be False, v1.1 must be True. ANOM-01 (the frozen gate artifact records a stale v1 back-reference `603ab720…`/1,585 B while the real v1 is 1,746 B `2cd7eccd…`) confirmed at `human-gate-answer-20260917.json:19` — consistent with §19.1's disclosure.
### F2 — Frozen v4 vs frozen v3 on the still-present attempt-05 frames
- Inputs present and hashed: `/tmp/route5r_frame_pre.jpg` `3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531`, `/tmp/route5r_frame_post.jpg` `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3`, `/tmp/vision_ocr` `f54628e8f42fb65200bf98bf5cc6463937d28781c673c22e5ca8b9418ae3f6c9`.
- v4 invocation (raw): `VISION_OCR_BIN=/tmp/vision_ocr python3 evidence/20260916-route/tools/v4/verify_album_open.py <pre> <post> --expect-start 2024-05-13 --expect-end 2024-05-17 --expect-count 57` → `exit=0`; `verdict ALBUM_OPEN_VERIFIED`; `count_digits_read 57`; `count_text MATCH`; `reader.helper = {"resolved_from":"env","binary_path":"/tmp/vision_ocr","binary_sha256":"f54628e8…","binary_bytes":67192,"source_sha256":"4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32"}`. Two consecutive runs: exits 0/0, stdout byte-identical, SHA-256 `91e2bfd4274704840e4fdc4652cf4278174472e8617779946ce6e8047e6c16b6`.
- v3 invocation (raw): same args with `evidence/20260916-route/tools/verify_album_open.py` → `exit=4`; `verdict TARGET_MISMATCH`; `count_digits_read 75`; no `reader` block. Conclusion: the reader substitution is real and the v4 verdict is reproducible at the claimed hash binding; no input file was missing.
### F3 — Fail-closed / confidence audit (sources quoted)
- `vision_reader.py:151`: "Any failure returns an empty list; the call outcome is recorded either way." `:156-160`: `if not _STATE["usable"]: call["outcome"] = ("binary_missing" if …"env" else "build_failed"); … return []`. `:190-193`: `if proc.returncode != 0: call["outcome"] = "nonzero_exit"; … return []`. `:194-196`: `if not out: call["outcome"] = "ok"; return []` (empty stdout → zero words; recorded outcome is "ok" — taxonomy nuance, RV-33-5). `:216-219`: `if not words: call["outcome"] = "unparsable"; … return []`.
- `verify_album_open.py:166-180`: `if count_text == "MISMATCH" or (title is None and date_like): … TARGET_MISMATCH; return 4` → `if stats["changed_fraction"] < args.min_diff_fraction: … NO_EFFECT; return 3` → `if title: … ALBUM_OPEN_VERIFIED; return 0` → else `INCONCLUSIVE; return 5`. `title` requires parsed words, so a Vision failure cannot reach exit 0.
- `locate_album_ellipsis.py:145`: `return {"text": text, "conf": round(w["conf"], 1)}` — `conf` occurs nowhere else in the file; no confidence value gates any verdict.
- Empirical refusal replay: `VISION_OCR_BIN=/tmp/does-not-exist-vision python3 …/v4/locate_album_ellipsis.py <post> --expect-start … --expect-end …` → `exit=2`, `verdict TARGET_TITLE_NOT_FOUND`, `call0.outcome binary_missing`, no `click_point`, helper `resolved_from "env"`. No silent-pass path found.
### F4 — Cross-revision contradiction audit
- Contradiction found (RV-33-1), quoted verbatim: §22.6 row `V22_S5_BOUND_TO_V4_READER` — "attempt-06's stop-or-continue decision must come from the frozen v4 verifier and its JSON must carry the v4 reader block; a tesseract-based verdict anywhere in the attempt-06 chain is TASK_REGRESSION" — versus §22.3 precondition 2 — "The unchanged detector `detect_menu_popup.py` `6ae9c250…` and its frozen self-test `d8ffc129…` are reused byte-identically" — and §20.2 S10 — "`AFFIRMATIVE` requires machine-observable evidence (a new AX menu element or the detector's `MENU_DETECTED`: a new rectangular region plus ≥2 transcribed menu strings)". The detector runs `tesseract` (`detect_menu_popup.py:47`) and emits `result["verdict"] = "MENU_DETECTED"` (`:168`); the corroborating v2 locator is also tesseract-based (`locate_card_ellipsis.py:41`, verdicts at `:240/:244/:253`). A correct attempt-06 chain therefore contains tesseract-based verdicts — the CORE row as literally written is unsatisfiable.
- Stale literals (RV-33-3/4), quoted verbatim: plan L2027 "the current PLAN_REVISION at handoff time (21 at this writing)"; L2029 "Stage 02 must independently review this Revision 21 and its exact hash"; §19.1 "subject to independent re-verification at Stage 05 attempt-06"; §19.3 title "(Plan-authored; applied at Stage 05 attempt-06)" and "re-verified by Stage 05 attempt-06" (L553) / "re-derived by Stage 05 attempt-06" (L567); §20.3 L421 "(re-derived by Stage 05 attempt-06 from fresh evidence, never assumed here)". These collide with the header L11 binding ("its independent acceptance is `e2e/attempt-07`") and with `e2e/attempt-06/` already existing (`e2e_report.md 14b44c94…`). §21.6's "a later route-closure acceptance takes the number after it" (L288) is consistent and needs no change.
- No contradiction found in: §16.4 (its own text authorizes the §19.1 single-leaf corrected re-authoring — read at L927-929; the matcher re-derived True on v1.1), §16.8 (revision semantics), §19.1's substantive rules, §21.6's branch-B binding ("the new revision must bind its S5 verification to the v4 reader and carry a new one-shot gate"), the base check matrix rows `SOURCE_CORRESPONDENCE`/`CUA_ROUTE_DECISION`/`VISION_READER_*`/`V3_FROZEN_EVIDENCE_UNCHANGED`, and the base closure rules (including the `ROUTE_NOT_NEEDED` proviso, correctly not taken).
### F5 — Safety attack: every input the plan can cause
- Tooling grep across `tools/v4/*.py`, `tools/detect_menu_popup.py`, `tools/vision/`: `cliclick|osascript|CGEvent|AXUIElement|AXPress|performSecondaryAction|screencapture|pyautogui|Quartz|NSEvent|keyDown|mouseDown` → zero matches. The only subprocess uses are the temp-dir `swiftc -O` build (`vision_reader.py:109`) and the helper exec on a temp PNG (`:168`); the detector execs `tesseract`.
- Enumerated plan-caused inputs on the owner's machine: (1) one normal left click at the S3 album-card point (S4), (2) one normal left click at the S6 album-⋮ point (S8), plus read-only `screencapture -x` (S2 once; S7 once; S9 ≤5 within ~4 s) and read-only AX/screenshot observation (S1/S9). Budgets: `retry_budget=0`, `click_count_per_input=1`, `menu_item_budget=0`, `keyboard_input_budget=0` (NFR-V22-2); input #2 exists only if S5 verifies; input #1 stops the run on any S3 refusal; a zero-input stop is the only resume (S1-S11 + §22.3).
- Extra-input paths attempted and found closed: no menu-item or chooser step exists anywhere in S1-S11; no keyboard step; no AX write (only AX state read); no bring-to-front/navigation/scroll step; no retry logic in any tool (verdict chains are single-pass); no historical/guessed coordinate (click points come from current-frame `click_point` only). The narrow reading of decision 1 (⋮ input only) is recorded in §22.2 and would send zero inputs, i.e., it fails safe. No way found for the plan to send a menu-item click, a chooser interaction, a keyboard event, an AX write, an extra click or a retry.

## FINDINGS
- ID: RV-33-1 | Severity: MAJOR | Category: SEMANTIC_CONTRACT
  - Affected: §22.6 `V22_S5_BOUND_TO_V4_READER` vs §22.3 precondition 2 + §22.3 steps (S10 applies unchanged) + §20.2 S10.
  - Evidence: [VERIFIED] by source and text (quotes in F4): the CORE/HARD_CLEAN failure class says "a tesseract-based verdict anywhere in the attempt-06 chain is TASK_REGRESSION" while the same revision mandates reusing the frozen tesseract-based detector `detect_menu_popup.py` (`6ae9c250…`) whose S10 `MENU_DETECTED`/`NOT_DETECTED` verdicts are tesseract-derived; the corroborating v2 card-⋮ locator is tesseract-based too.
  - Failure mechanism: Stage 05 applying the row literally must classify a correct attempt-06 as TASK_REGRESSION (or quietly reinterpret a CORE gate row) — the check can never pass on a correct run, so the wave's CORE acceptance is not machine-coherent.
  - Smallest correction: scope the failure class to the S3/S5/S6 reader-substituted stop-or-continue verdicts and explicitly exempt/cite the frozen v2/v3-era detector reused by S10 (one clause). If the intent is a total Vision-only chain, re-bind S10/§22.3 precondition 2 to a Vision reader and re-derive the detector's role — a larger change.
- ID: RV-33-2 | Severity: MINOR | Category: GROUNDING
  - Affected: §22.1 L45 ("line 1048 … (the option presentation immediately before the answer), verbatim (excerpt)").
  - Evidence: [VERIFIED] raw transcript: all four quoted markers are in L1025; L1048 carries only the `回覆範例` line. The decisions artifact lists both lines (1025 and 1048), so the artifact is more accurate than the plan.
  - Failure mechanism: a Stage-03/05 reader re-deriving the excerpt from line 1048 finds different bytes and may distrust the record.
  - Smallest correction: 1048 → 1025 for the quoted excerpt (or cite both lines with L1025 as the excerpt source).
- ID: RV-33-3 | Severity: MINOR | Category: PRECISION
  - Affected: closure section L2027 "(21 at this writing)" and L2029 "Stage 02 must independently review this Revision 21 and its exact hash"; §22.8's corrected-literals list omits this section.
  - Evidence: [VERIFIED] by text; the header is PLAN_REVISION 22 and §22.8 lists no closure-section fix.
  - Failure mechanism: Stage 03 could bind a handoff to the stale "21" literal; Stage 02's mandate becomes literally unsatisfiable for Rev22.
  - Smallest correction: update both literals to 22 (and add one supersession sentence to §22.8).
- ID: RV-33-4 | Severity: MINOR | Category: PRECISION
  - Affected: §19.1 "subject to independent re-verification at Stage 05 attempt-06"; §19.3 title "(applied at Stage 05 attempt-06)" + L553/L567; §20.3 L421 "(re-derived by Stage 05 attempt-06 …)".
  - Evidence: [VERIFIED] by text; header L11 binds Rev22's independent acceptance to `e2e/attempt-07`; `.agent/.../e2e/attempt-06/` is already consumed (`14b44c94…`); `evidence/20260916-route/attempt-06/` (route series) does not exist yet — the same number 06 means two different runs in two series.
  - Failure mechanism: Stage 05 could try to reuse the consumed e2e attempt-06 number (append-only violation) or mis-scope the re-derivation; the two series' homonyms invite evidence mis-citation.
  - Smallest correction: replace these three acceptance-number references with attempt-07 (or "the next unused e2e attempt") and add one clarifying sentence distinguishing the route attempt series from the e2e acceptance series.
- ID: RV-33-5 | Severity: MINOR | Category: TEST
  - Affected: §21.3's reader failure-class taxonomy vs `vision_reader.py:194-196`.
  - Evidence: [VERIFIED] empty helper stdout records `outcome "ok"` but returns zero words (→ unreadable → tool refusal); the recorded taxonomy therefore differs slightly from the listed classes. No silent pass is possible (F3).
  - Failure mechanism: none for acceptance; a Stage-04 debugger could misread an "ok" outcome with `lines_parsed 0` as a successful empty read.
  - Smallest correction: optional one-line handoff note ("empty stdout = `ok` + zero words = refusal path"); no plan revision needed for this item alone.

No BLOCKER findings.

## REQUIRED_PLAN_CHANGES
A further plan revision (Rev23) is required before Stage 03 handoff. RV-33-1 must be fixed (CORE check-row wording contradicts the plan's own mandated S10 procedure; a correct attempt-06 would be classified as TASK_REGRESSION). RV-33-2/3/4 are one-line literal corrections and should be folded into the same revision to avoid a second review cycle. RV-33-5 is an optional handoff note. After the edit: re-verify the new plan hash, re-run a fresh independent review of that exact revision, and only then compile the handoff. No architectural, safety, or goal-alignment rework is required; the wave's direction, budgets, and freeze set stand.

## RESIDUAL_MINOR_NOTES
- Observed worktree state (not authored by this review): `evidence/20260917-owner-decisions/owner-decisions-rev22.json` is modified (worktree `0664b5fb…` vs HEAD `9d6b72e0…`) with the documented CORR-01 correction (RV-32-1 response; plan-hash-neutral). Stage 03/04 must commit it and pin its hash before gate-4 freeze so the gate's citation is byte-stable.
- §22.2's alternative reading of decision 1 (⋮ only) is examined: the operative two-input reading is disclosed in §22.2 and in the owner-facing §22.7 ("開相簿 → 看一眼相簿裡的 ⋮"), gate-4 is frozen before any input, and the narrow reading sends zero inputs. No hidden or excess input was found; no change required, but Stage 03 may restate the two-input reading in the handoff's GOAL_ANCHOR so the owner sees it at gate-4 freeze.
- Pre-existing (v3-inherited) crash edge, out of Rev22 scope: a corrupt/unreadable frame file can raise a Python traceback (exit 1) rather than `BAD_FRAME(6)`; v4 preserves v3 behavior by design, and this remains a future-revision candidate.
- Stage 05's `e2e/attempt-07` must run no GUI input of its own (header L11); the re-derivation is over attempt-06's frozen artifacts, so the run's evidence must be complete at S11 (execution-rev22.md + all tool JSONs with reader blocks).
NEXT_ACTION: Revise plan.md to PLAN_REVISION 23 fixing RV-33-1 (CORE check-row scope) and the RV-33-2/3/4 literals; re-verify the new hash; then run a fresh independent review of that exact revision before Stage 03.
PLAN_REVISION_REQUIRED
