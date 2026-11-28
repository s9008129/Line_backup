# LINE 記事本短暫工具列與中斷接續實作審查紀錄（Round 1）

- 審查日期：2026-11-22（Asia/Taipei）
- 審查對象：Draft PR #52（`review/notes-transient-toolbar-20261121` HEAD `bb88c92395d7aad125089176045752079ccf1dde`）與本機 `feature/line-notes-media` 提交 `3e2b1dbbd5d5444e8c100ddb6d276a10804e9023`（兩者 7 份修復檔經 `git diff` 逐字一致）
- 對照基準：`docs/plans/20261121-notes-transient-toolbar/plan.md`（基準版）、`docs/plans/20261121-notes-transient-toolbar/continuation-acceptance.md`、`src/line_backup_batch/notes.py`
- 審查範圍：7 份交付檔唯讀檢視與離線測試／Node 實證重現；未修改產品程式碼、Skill、測試或帳本；未執行真實 LINE GUI、chooser 或跨 Session 實機操作（相關項目仍為 `NOT_RUN`）
- 審查交付：已透過 Herdr 送交 Planner pane（`w6:p3`）要求修訂計畫並重新提審

### Review Verdict: REQUEST_CHANGES
- **Review Type**: Code & Security
- **Core Goal Alignment**: 切片 B（`SKILL.md`、`download-and-ledger.md`、`docs/LINE相簿備份_使用手冊.md` 與 `tests/test_notes_unknown_recovery.py`）已對齊 `src/line_backup_batch/notes.py` 契約與補件目標，未發現缺陷；但切片 A 在可複製範本與 `notesIntentDispatch` 存在 3 項可實證重現的 `[BLOCKER]`（含執行期崩潰、過期截圖繞過、非同步突變繞過安全區）與 2 項 `[MAJOR]`（原計畫項目未落實、雙階段單次擷取交接與回歸覆蓋缺口），尚未達成核心目標。
- **Diff / Scope Hygiene**: 公開 PR #52 修改範圍嚴格落在原計畫的 7 個檔案、未改動 Python 產品碼或相簿段落、亦無私人資料外洩；問題集中在 `evidence-template.md` 實作缺陷與 `test_notes_input_helper.py` 測試覆蓋不足。

### Findings
1. `[BLOCKER]` `.agents/skills/line-notes-agent-cua/references/evidence-template.md:1679,1687,1703-1714,1833,1892`
   - **Issue**: 可複製範本在同一 CUA Node REPL 作用域內存在兩項執行期錯誤：(a) Block 7（L1679，intent 前 gate）與 Block 11（L1833，直接 dispatch）重複宣告頂層 `const directDecision`，而 Block 12（L1892）明確依賴 Block 7（L1714）的 `retainedReveal` 留在同一 REPL 作用域；(b) Block 7 在 `controlVisible === true`（L1703）與 `revealMethodIndependentlyAuditable === true`（L1708）判斷之前，即無條件求值 `directDecision`（L1679–1686）與 `revealDecision`（L1687–1701），單分支情境會直接求值不存在的 `CURRENT_*` 識別字。
   - **Impact**: (a) 走「可見 → 直接下載」主路徑時，Node 立即拋出 `SyntaxError: Identifier 'directDecision' has already been declared` 中斷；(b) 走「工具列已隱藏（`controlVisible=false`）」或「可見但無安全 reveal 方法（`revealMethodIndependentlyAuditable=false`）」時，直接拋出 `ReferenceError: CURRENT_CONTROL_REGION is not defined` 等錯誤，迫使 Agent 現場修改範本或填入假值（違反同節規則）；(c) `tests/test_notes_input_helper.py:12-41` 僅抽取 Blocks 1／5／6，未執行 Blocks 7–14，導致兩項錯誤漏網。
   - **Minimal Fix**: 將 Block 11 的變數改名（如 `directDispatchDecision`）避免重複宣告；在 Block 7 將 `directDecision` 與 `revealDecision` 改為依條件延遲建立（未啟用分支不求值對應佔位符）；於 `tests/test_notes_input_helper.py` 新增抽取並在同一 Node 作用域執行可複製範本六條選路與雙階段接續的回歸測試。

2. `[BLOCKER]` `.agents/skills/line-notes-agent-cua/references/evidence-template.md:1490-1495`
   - **Issue**: `notesIntentDispatch.checkRevealBefore()` 檢查新鮮度時使用邏輯 `&&` 而非 `||`：`sameFileRef(beforeAssets.screenshot, preIntentReveal.before_observation.screenshot) && sameFileRef(beforeAssets.ax, preIntentReveal.before_observation.ax)`。
   - **Impact**: `persistObservation()` 以 `wx` 建立獨立的 `<observationId>.screenshot.bin` 與 `<observationId>.ax.txt`，真正新鮮的 intent 後觀察兩檔路徑必然都與事前不同（即使兩次 AX 內容 SHA-256 相同，其 `.path` 仍不同）。使用 `&&` 會讓「新 `observation_id` 搭配過期 pre-intent `screenshot` ref 與新 `ax` ref（或反之）」繞過 `REVEAL_BEFORE_OBSERVATION_NOT_FRESH` 並實際呼叫 `app.click()`（實測重現：`status="INVOKED"`、`clicked=[[70,80]]`、`sameShot=true`）。
   - **Minimal Fix**: 將 L1490–1495 改為只要 `observation_id` 相同，或 `screenshot`／`ax` 任一方的 `path` 或 file ref 與 `preIntentReveal.before_observation` 相同即拒絕 `REVEAL_BEFORE_OBSERVATION_NOT_FRESH`；於 `tests/test_notes_input_helper.py` 補上僅截圖過期與僅 AX 過期的零輸入回歸測試。

3. `[BLOCKER]` `.agents/skills/line-notes-agent-cua/references/evidence-template.md:1528-1557`
   - **Issue**: `notesIntentDispatch.persistReveal()` 在同步執行 `checkReveal()` 與 `checkRevealBefore()` 後，未先對 `options.request` 建立不可變 JSON 快照即傳入非同步的 `persistRevealWithDirectAfter()` → `persistSingleInput()`（在 L544 `await validatePrivatePaths()` 之後才於 L566 序列化 `options.request`）；且 `await` 後的 L1552–1554 仍直接讀取可變的 `options.request.candidate_ordinal`、`options.preIntentReveal.observation_id` 與 `options.beforeObservation.observation_id`。
   - **Impact**: 與同檔 `persistGroundedDownloadClick()`（L878–880，並有 `test_grounded_request_snapshot_survives_nested_caller_mutation` 防護）相比，`persistReveal()` 存在非同步突變繞過漏洞：呼叫後、第一個 `await` 解析前修改 `request.prepared_target` 或 `candidate_ordinal`，可繞過 `checkRevealBefore()` 與 `safe_zone` 嚴格內點檢查，將 `app.click()` 派送至安全區外任意座標（實測重現：`safe_zone=[40,50,100,110]`，突變 `prepared_target=[9999,9999]`、`candidate_ordinal=99` → `status="INVOKED"`、`clicked=[[9999,9999]]`、`reportedOrdinal=99`）。
   - **Minimal Fix**: 由 `evidenceTools` 匯出 `snapshotJsonValue`（或於 `persistReveal()` 入口同步快照 `options.request`），以不可變快照進行 `checkReveal()`／`checkRevealBefore()` 與 `persistRevealWithDirectAfter()` 派送，並在 `await` 前保存不可變的 `candidate_ordinal`／`observation_id`；於 `tests/test_notes_input_helper.py` 補上對等的巢狀突變防護測試。

4. `[MAJOR]` `docs/plans/20261121-notes-transient-toolbar/plan.md:19` & `.agents/skills/line-notes-agent-cua/references/evidence-template.md:1608-1641,1752-1848`
   - **Issue**: 原計畫切片 A 第 4 點明訂「範本說明以 host 時間記錄可測的 capture 與 dispatch 邊界，未實測的壽命和點擊命中不作保證」，但 `9e0d9c3..bb88c92` 對 `evidence-template.md` 新增內容中完全沒有 capture 與 dispatch 邊界的 host 時間記錄（僅既有 `persistRevealWithDirectAfter` 記 reveal input／after capture；Block 9 `directCapture`、Block 10 `dispatchDownload`、`persistDownload` 及範本說明皆未記錄或說明 `capture_call_*`／`dispatch_call_*` host 時間邊界）。
   - **Impact**: 未完整落實原計畫交付物；後續在真實 LINE 進行 E1–E3 實機查核（`plan.md:49`）時，仍缺少可量測 `after／direct capture → download dispatch` 延遲的 host 邊界時間原件。
   - **Minimal Fix**: 在 Block 9（intent 後唯一 capture）與 `persistDownload`（或 `dispatchDownload`）加入最小 `hostCalls` 時間邊界欄位（`clock_source='HOST_JS_DATE'`、`precision='CALL_BOUNDARY_ONLY'`、`os_event_time='UNKNOWN'`），在 `evidence-template.md` 簡要說明不承諾工具列壽命與 OS hit-test，並於 `tests/test_notes_input_helper.py` 驗證欄位輸出。

5. `[MAJOR]` `.agents/skills/line-notes-agent-cua/references/evidence-template.md:1752-1772,1850-1896` & `tests/test_notes_input_helper.py:1579-1639`
   - **Issue**: (a) Block 9（L1752–1772）標題為「直接 capture（步驟一）」且變數名為 `directObservation`，而 Block 12（L1853）寫 `const beforeObservation = FRESH_INTENT_OBSERVATION;`，未明示在「可見轉隱藏」時必須直接沿用 Block 9 的那唯一一次 intent 後觀察；(b) `test_reveal_preflight_errors_and_slot_collision_make_zero_input`（L1579–1639）漏測原計畫 A.1／A.3 的關鍵拒絕與不抹除條件：`preIntentReveal` 為 `STOP` 或 `branch='DIRECT'`、`candidate_ordinal`／`budget_before`／`budget_after`／`prior_candidate_refs` 漂移，以及「可見 `DIRECT READY`＋備選 `REVEAL STOP` 不抹除 `DIRECT` 但阻擋 intent 後 reveal」。
   - **Impact**: (a) Agent 走「可見轉隱藏」主路徑時，容易在 Block 9 後再重拍一次形成兩次 post-intent capture，違反計畫 A.2「讀回 intent 後只取一次目前畫面」契約；(b) 關鍵 gate 拒絕分支缺乏回歸保護。
   - **Minimal Fix**: 將 Block 9 改為中性的「intent 後唯一 capture」並讓 Block 12 明確承接該變數，嚴禁第二次 capture；補齊上述關鍵負面與「`DIRECT READY` + `REVEAL STOP`」回歸測試。

### Verification Evidence
- 唯讀核對 `git show 9e0d9c3..bb88c92`、`git diff 3e2b1db bb88c92`（7 檔無差異）、`docs/plans/20261121-notes-transient-toolbar/plan.md`、`continuation-acceptance.md`、`.local/line-backup/tasks/notes-transient-toolbar-20261121/progress.md` 與 `src/line_backup_batch/notes.py`（`isolate`／`_attempt_phase`／`intent`／`summary`／`_unresolved_attempts`）；掃描 PR diff 無本機家目錄路徑、帳本 ID 或私人資料外洩。
- 離線驗證命令全部執行通過（exit 0）：
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_input_helper.py'`：Ran 40 tests, OK
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_unknown_recovery.py'`：Ran 17 tests, OK
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`：Ran 356 tests, OK
  - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help`：exit 0
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`：Ran 73 tests, OK
  - `git diff 9e0d9c3..bb88c92 --check`：exit 0
- 以 Node 實證重現 Findings 1–3（使用暫存目錄並於執行後清理，未改動專案程式碼）：
  - Repro 1（Block 7 + Block 11 同作用域）：exit 1，`SyntaxError`（重複宣告 `const directDecision`）
  - Repro 2（Block 7 `controlVisible=false` 單分支）：exit 1，`ReferenceError: CURRENT_CONTROL_REGION is not defined`
  - Repro 3（`checkRevealBefore` 僅 screenshot 過期）：exit 0，`{"status":"INVOKED","reason":null,"clicked":[[70,80]],"sameShot":true}`
  - Repro 4（`persistReveal` 呼叫後突變 `prepared_target=[9999,9999]`、`candidate_ordinal=99`）：exit 0，`{"status":"INVOKED","clicked":[[9999,9999]],"reportedOrdinal":99}`
- 證據界限：本審查僅涵蓋程式碼、範本、文件一致性與離線合成驗證；真實 LINE E1–E3、chooser、檔案落地、跨 Session 恢復與獨立產品驗收均維持 `NOT_RUN`。
