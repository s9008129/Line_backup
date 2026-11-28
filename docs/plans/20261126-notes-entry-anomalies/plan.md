# LINE 記事本入口遺失、輸入通道與證據可重現性異常修復計畫

- 計畫日期：2026-11-26（Asia/Taipei）
- 版本：v1（已整合 Reviewer `wA:p2`、Worker1 `wA:p3` 與 Worker2 `wA:p4` 之唯讀對齊與預檢回饋）
- 專案：`/Users/hsiaojohnny/dev/Line_backup`
- 分支：`feature/line-notes-media`
- 基準 HEAD：`70c81279d8f9091a9570a7b92bb1a38584c8bb46`
- 問題提報單：`docs/diagnostics/20261126-notes-entry-anomalies/問題提報單.md`
- 隱私邊界：本計畫與後續所有追蹤異動不夾帶真實群組／清單名稱、人名、實際目錄名或本機使用者帳本內容。
- 既有未追蹤檔保留：`2026.1122_問題提報單及意圖釐清點.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/`（本計畫不修改、不覆寫、不 stage）。

## 1. 核心目標與問題定位（A1–A13 與 §11 Q1–Q10 判定總表）

本專案核心目標是讓不同模型、Agent 與 Session 皆能透過同一日常正式 Prompt 與 `line-notes-agent-cua` Skill，搭配原生 macOS Computer Use 與 notes 輔助 CLI，**全程無人值守完成單一指定 LINE 記事本列表照片與影片的備份、驗證及跨 Session 接續**，同時維持嚴格的資料保護紅線、CLI／GUI 職責分離，並禁止過度工程化或偏離日常產品入口。

依據 `問題提報單.md` 實證紀錄、現行 Skill／references、`src/line_backup_batch/notes.py` 與離線測試逐項核對，本輪 13 項異常（A1–A13）與 10 項待判定問題（Q1–Q10）的精準裁決如下：

| 異常／問題 | 根因歸類 | 裁決與最小修復方向 | 歸屬切片 |
|---|---|---|---|
| **A1 / A4**（`ENTRY_LOST`、`foreground=VALID`、AX 未暴露工具列控制） | 實機環境狀態＋文件細則不足 | `ENTRY_LOST` 根因維持 `UNKNOWN`；在 `gui-inventory.md` 明確界定 `foreground=VALID` 不等於入口可用／控制可達，並於 `input_capability` 加入 `PARTIAL_AX_ONLY`（AX 可點、pointer 不可用時不得當 `AVAILABLE` 操作僅視覺可見控制，須轉 `HANDOFF_REQUIRED`）。不新增 ad-hoc schema 欄位。 | Slice 2 |
| **A2 / Q2**（三次座標點擊均回 `-10005 noWindowsAvailable`） | 底層原因 `UNKNOWN`＋Agent 違規輪換座標空間重試且未留 raw receipt | 不得將 `noWindowsAvailable` 歸責為 LINE／CUA 缺陷；於 `gui-inventory.md` 與 `D4` 明禁在連續 `noWindowsAvailable` 下輪換截圖像素／螢幕點／視窗相對座標作為「新方法」，兩次無新資訊即停並進 `HANDOFF_REQUIRED`。合法重現僅限授權前景內經 `persistSingleInput` 落地原始 receipt。 | Slice 2（規則）＋ Slice 1（`persistSingleInput` 紀律） |
| **A3 / Q1**（macOS CUA window handle reacquire 形狀未證實、誤猜 `getApp({windowId})`） | 工具文件邊界未明＋Agent 猜 API | 離線不得臆造或硬編碼未驗證的 macOS CUA window handle API 形狀。於 `gui-inventory.md` 與 `D4` 明訂只可呼叫當次 CUA 工具文件明載之唯讀 app／window 列舉或 reacquire；未記載者不得猜參數試探，工具無文件支援或重取後仍無法恢復必要通道時，保存原始錯誤並立即進 `HANDOFF_REQUIRED`。 | Slice 2 |
| **A5 / Q3**（`getAXState()` no-change 單行輸出被 `persistObservation` 判 `AX:OK`／`ready_for_bind=true`） | **實證 helper 缺口**（`evidence-template.md`） | 於 `persistObservation` 加入前綴錨定＋非樹形守衛之 `isAxNoChangeStub` 偵測：仍以 `wx`＋讀回保存原始 `.ax.txt` 供唯讀診斷，但將 `stages.AX` 標為 `status: 'DIFF_NO_CHANGE', full_tree: false, diff_only: true, stale_index_warning: true`，並寫入 `blockers: ['AX:DIFF_NO_CHANGE']` 使 `ready_for_bind=false`（自動 fail-closed 阻擋 `cua-initial-observation` emit、`bind`、`checkDownloadReadiness` 與 `persistReveal`）。同時誠實註明 `disableDiffing: true` 非絕對保證且有變更 diff 仍須由 Agent 核對完整樹結構。 | Slice 1（helper＋測試＋本文）＋ Slice 2（D2／`gui-inventory.md` 引用） |
| **A6**（選單開關後 AX 索引漂移） | 正常 UI 行為，非缺陷 | 現行 `gui-inventory.md:129` 已要求「AX 索引失效時重取完整 AX」；不作無謂修改。 | 無需修改 |
| **A7 / Q4**（`summary` 與 `resume` 並行觸發 `NOTES_LOCK_BUSY`） | Agent 並行編排錯誤；**非 CLI 缺陷** | **維持凍結 `src/line_backup_batch/notes.py`**：`_file_lock` 採 `LOCK_EX \| LOCK_NB` 且 `summary`（read-only）回 `retry_safe=true`、`resume`（寫入）回 `retry_safe=false`；即使改 `summary` 為 `LOCK_SH` 仍與 `resume(LOCK_EX)` 互斥無法解並行。改於 `download-and-ledger.md`（單一本文）與 `SKILL.md` 明禁同一 lock domain（`--records-root`／`--collection`）任何 CLI 命令並行執行，並修正 `download-and-ledger.md:16` 明確區分唯讀（可序列重試）與寫入（`resume` `retry_safe=false`，停止並序列重查）。 | Slice 2 |
| **A8**（舊 `summary-after-bind` 快照與最新 summary 時間差） | 快照時序誤讀風險 | 於 `download-and-ledger.md`（`expected_tip` 定義）與 `verification-and-recovery.md` 回報模板明訂：所有回報與 fencing 一律以最新序列讀回 `summary` 的 `expected_tip`（`sequence`＋`sha256`）為基準，禁止混用較低 `sequence` 舊快照的 `unresolved_attempts`／blockers。 | Slice 2 |
| **A9 / Q5**（`status_counts_scope=CURRENT_SCAN`、`current_incomplete=0`、16 篇 `DETAIL_PENDING`） | 回報語意誤讀風險；**非 CLI 缺陷** | **維持凍結 `src/line_backup_batch/notes.py`**（`test_notes_restart.py:622` 精確鎖定 `status_counts_scope` 鍵值，且既有 `posts[].state`、`POST_DETAIL_PENDING` 與 `all_known_media_complete=false` 已自洽）。改於 `download-and-ledger.md`、`SKILL.md`、`verification-and-recovery.md` 與 `D2` 修正「舊 `status_counts`」措辭，精確定義 `current_incomplete`（僅計 scoped media，不含貼文 `.state=DETAIL_PENDING`，`0` 不等於全列表完成），並強制回報貼文層 `.state` 計數（總篇數／`MEDIA`／`NO_MEDIA`／`DETAIL_PENDING`）。 | Slice 2 |
| **A10 / Q10**（使用 `osascript System Events` 唯讀查視窗） | 流程邊界模糊 | 於 `SKILL.md`、`download-and-ledger.md`、`gui-inventory.md` 統一限定「當次 CUA 工具文件支援之唯讀 app／window 列舉與 handle reacquire」；於 `gui-inventory.md` 與 `D4` 明訂 `osascript`／System Events／CGWindow 查詢**不是** CUA reacquire，無法產生有效 handle 或恢復輸入通道，若作排錯參考須標為非 CUA OS 唯讀診斷，絕不可冒充 CUA reacquire。 | Slice 2 |
| **A11 / Q7**（舊 `STOPPED` 空 staging 保留與晚到檔風險；新 staging 發布後不存在） | 正確 fail-closed 行為＋文件細微歧義 | 不新增 helper、不清理、不標記改動舊目錄。於 `download-and-ledger.md`（`:21,142,163,466,470`）、`verification-and-recovery.md`（`:147,200+`）與 `SKILL.md`（`:122`）釐清：舊 `STOPPED` 空 staging 照常保留並於回報註記殘留晚到風險；`LOCAL_MISSING`/`LOCAL_CHANGED` 僅核對完成貼文目錄，不看交易 staging（成功發布後新 staging 不存在非 `LOCAL_CHANGED`）；列表層 `.line-notes-incoming-*` 屬交易 staging，不屬完成容器內額外檔；`STOPPED` 恢復不要求舊 staging 為空（空／單檔隔離條件僅屬 UNKNOWN v5）。 | Slice 2 |
| **A12 / Q8**（pointer 失敗與 `getApp({windowId})` 錯誤缺乏原始 request／response receipt） | 文件操作紀律缺口（**無需新 helper API**） | 經核對 `evidenceTools.persistSingleInput` 已具備 `wx` request 寫入讀回、`inputErrorSnapshot`（含 cross-realm／純字串／數值 `code`）與三檔不覆寫落地。於 `evidence-template.md` 補齊強制規則與三個操作邊界（1. 錯誤若以回傳值而非 throw 回傳時 `raw.kind=RETURN`，不得判成功；2. handle reacquire 回傳非 plain object 時須於 `invoke` 回傳可序列化投影並以 closure 帶出 live handle；3. 禁止使用 `input_phase=DOWNLOAD_CONTROL`，應用 `ENTRY_RECOVERY`／`HANDLE_REACQUIRE` 並每次換唯一 `operationId`，需要時間軸時另記 `HOST_JS_DATE` 且 `os_event_time=UNKNOWN`），並禁止以手寫 curated JSON 取代 raw receipt。於 `gui-inventory.md` 與 `D4` 引用。 | Slice 1（本文）＋ Slice 2（引用） |
| **A13 / Q9**（reacquire 與初次 observation bytes 完全相同、inode 不同、`hostCalls.capture_call_*=NOT_RUN` 卻 `ready_for_bind=true`） | **實證 helper＋gate 缺口**（`evidence-template.md`） | 1. 於 `persistObservation` 新增 `stages.CAPTURE_BOUNDARY`（`RECORDED`／`MISSING`，依 `hostCalls.capture_call_started_at` 與 `capture_call_returned_at` 是否為非空且非 `NOT_RUN`/`UNKNOWN` 字串判定）；為相容 17+ 既有低階 bare `persistObservation` 單元測試，`CAPTURE_BOUNDARY=MISSING` 不在低階 `persistObservation` 塞入 `blockers`。2. 於 `cua-initial-observation` 入口區塊強制 **fail-closed gate**：除 `!OBSERVATION.ready_for_bind` 外，若 `OBSERVATION.stages?.CAPTURE_BOUNDARY?.status !== 'RECORDED'` 一律拒絕 emit 並拋 `CUA_RAW_OBSERVATION_INCOMPLETE: ... CAPTURE_BOUNDARY:MISSING`（維持 `writes` 筆數契約不變）。3. 文件明訂 bind／reacquire 必須經 `captureAndPersist`（或具實時 `hostCalls` 且 `CAPTURE_BOUNDARY=RECORDED`）取得，呼叫端／稽核必查該 stage；靜止畫面在 `CAPTURE_BOUNDARY=RECORDED` 下 bytes 相同僅記新鮮度註記而非自動阻擋，但 `CAPTURE_BOUNDARY=MISSING` 不可採信為新鮮 bind／reacquire 證據（合併相同 bytes 時標 `STALE_CAPTURE_SUSPECTED` 並停止消費）。 | Slice 1（helper＋入口 gate＋測試＋本文）＋ Slice 2（`gui-inventory.md`／`D5` 引用） |
| **Q6**（GUI `ENTRY_LOST`／pointer 不可用／AX 控制缺失不進 notes CLI `dispatch_blockers`） | 刻意之 CLI／GUI 架構邊界＋回報欄位補強 | 維持 `notes` CLI 永不觀察 LINE GUI 之架構邊界；於 `SKILL.md`（回報契約單一本文）與 `verification-and-recovery.md`（回報模板）新增標準 `GUI／入口與通道狀態` 欄位（含 `gui_blockers`），與 `notes CLI dispatch_blockers` 明確分欄並列，並同步 `C27` 引用。 | Slice 2 |

## 2. 明確非目標與最小修改邊界（Strict YAGNI / KISS）

- **完全凍結 `src/line_backup_batch/*.py`**：本輪零 CLI 程式缺陷證據；不改 `_file_lock`、不改 `MEMORY_SCHEMA`（`summary()` 輸出鍵）、不新增子命令／flag／schema。
- **完全凍結 `docs/LINE相簿備份_使用手冊.md` 與 `AGENTS.md`**：日常正式 Prompt 與常駐邊界規範已涵蓋本輪原則，所有操作細則集中於 Skill／references，不膨脹啟動 Prompt。
- **完全凍結既有 Markdown 標題與錨點**：所有 6 份 Skill／references 檔案不更名、不刪除既有 `##`/`###` 標題，不新增冗餘 D8／D9 案例；維持單一本文＋短連結引用，避免跨檔文案漂移。
- **完全凍結 `evidenceTools` 公開函式簽章與 `BLOCK_MARKERS` 7 項順序**：不新增任何新的 helper 公開 API（沿用既有 `captureAndPersist`、`persistObservation`、`persistSingleInput`）；`cua-initial-observation` 仍維持恰好 1 個 `js` 區塊、尾端無額外文字、成功 `writes==2`／失敗 `writes==1` 與單次 `nodeRepl.emitImage`。
- **不破壞既有離線回歸契約**：低階 bare `persistObservation` 不因缺 `hostCalls` 改變 `ready_for_bind` 或既有 `blockers` 陣列斷言；fail-closed 捕捉邊界防護落於 `cua-initial-observation` 入口 gate 與 bind／reacquire 規範。
- **不放寬任何資料保護與實機驗證界限**：不觸碰 `notes-backup-records/`、`backup/`、`.local/`、`docs/diagnostics/20261126-notes-entry-anomalies/問題提報單.md` 及兩項既有無關未追蹤檔；真實 LINE GUI、CUA 實機 `noWindowsAvailable` 重現、window handle reacquire 與 E2E 維持 `NOT_RUN`。

## 3. 平行子任務切片設計（零檔案重疊）

本計畫經下方 Reviewer pane（`wA:p2`）依 `code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution 審查獲 `APPROVE` 後，立即平行分派給右方兩個 Worker pane：

### Slice 1（分派給 Worker1 `wA:p3`）：`evidence-template.md` helper 補強（A5／A12／A13）與離線單元測試

- **檔案白名單（僅 2 檔）**：
  1. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`
  2. `tests/test_notes_input_helper.py`
- **具體修改內容**：
  1. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`（`cua-evidence-tools` 區塊、`cua-initial-observation` 區塊與對應說明段）：
     - **A5（no-change AX 偵測，於 `cua-evidence-tools` 內）**：
       - 新增內部輔助函式 `isAxNoChangeStub(stateText)`：
         ```js
         function isAxNoChangeStub(stateText) {
           if (typeof stateText !== 'string') return false;
           const trimmed = stateText.trim();
           if (!trimmed || trimmed.length > 512) return false;
           const lines = trimmed.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
           if (lines.length === 0 || lines.length > 3) return false;
           if (!/^There has been no change in the accessibility tree\b/i.test(lines[0])) {
             return false;
           }
           return lines.slice(1).every(line => !/^\d+\s+/.test(line));
         }
         ```
       - 於 `persistObservation` 的 `AX` 階段：
         - `capture.state` 為非字串時維持 `INVALID_TYPE`；為空字串或僅空白（`capture.state.trim().length === 0`）時記 `setStage('AX', 'EMPTY')` 與 `blockers.push('AX:EMPTY')`。
         - 命中 `isAxNoChangeStub(capture.state)` 時：仍設定 `axBytes = Buffer.from(capture.state, 'utf8')`（使 `AX_PERSISTENCE` 照常寫入 `.ax.txt` 並讀回 `MATCH`，保留唯讀診斷原件），但設 `setStage('AX', 'DIFF_NO_CHANGE', { utf8_bytes: axBytes.length, full_tree: false, diff_only: true, stale_index_warning: true })` 並推入 `blockers.push('AX:DIFF_NO_CHANGE')`（使 `ready_for_bind = false`）。
         - 一般非空 AX 時設 `setStage('AX', 'OK', { utf8_bytes: axBytes.length, full_tree: true, diff_only: false })`。
     - **A13（捕捉邊界 `CAPTURE_BOUNDARY` 階段與入口 fail-closed gate）**：
       - 於 `persistObservation`（`hostCalls` 正規化完成且路徑檢查通過進入 capture 處理處，確保診斷 JSON 均含此 stage）記錄：
         ```js
         const hasCaptureBoundary = key => {
           const value = metadata.hostCalls[key];
           return typeof value === 'string' && value.trim().length > 0 &&
             value !== 'NOT_RUN' && value !== 'UNKNOWN';
         };
         setStage(
           'CAPTURE_BOUNDARY',
           hasCaptureBoundary('capture_call_started_at') &&
             hasCaptureBoundary('capture_call_returned_at')
             ? 'RECORDED' : 'MISSING',
         );
         ```
         **注意**：此處不將 `CAPTURE_BOUNDARY:MISSING` 推入低階 `persistObservation` 的 `blockers`，以保持既有低階 bare 呼叫與單元測試契約相容。
       - 於 `cua-initial-observation` 唯一 `js` 區塊（`nodeRepl.write(JSON.stringify(OBSERVATION, null, 2));` 之後）強化 fail-closed 檢查（不新增 `nodeRepl.write`）：
         ```js
         const captureBoundaryMissing =
           !OBSERVATION.stages ||
           !OBSERVATION.stages.CAPTURE_BOUNDARY ||
           OBSERVATION.stages.CAPTURE_BOUNDARY.status !== 'RECORDED';
         if (!OBSERVATION.ready_for_bind || captureBoundaryMissing) {
           const reasons = [...(OBSERVATION.blockers || [])];
           if (captureBoundaryMissing) reasons.push('CAPTURE_BOUNDARY:MISSING');
           throw new Error('CUA_RAW_OBSERVATION_INCOMPLETE: ' + reasons.join(', '));
         }
         ```
     - **A5／A12／A13 文件說明段補強（`evidence-template.md:59,1155-1180`，不改既有標題錨點）**：
       - 於 L59 修正 `(或對既有 capture 執行 evidenceTools.persistObservation)` 語意：明確限定 `bind` 與 `reacquire` 新觀察一律使用 `evidenceTools.captureAndPersist`（或具備同次實時 `hostCalls` 使 `stages.CAPTURE_BOUNDARY.status === 'RECORDED'`）；低階 `persistObservation` 僅用於同次 callback 內已有真實捕捉與 `hostCalls` 的保存（如 `persistRevealWithDirectAfter`），嚴禁對舊 capture 變數呼叫 bare `persistObservation` 充當新觀察，亦不得以手寫 curated diagnostic JSON 取代 helper 落地。
       - 於 L1155–1161 說明段補列：
         - `stages` 新增 `CAPTURE_BOUNDARY`（`RECORDED`／`MISSING`）及 `AX` 的 `DIFF_NO_CHANGE`（`full_tree: false, diff_only: true, stale_index_warning: true`，阻擋 `ready_for_bind`、`cua-initial-observation` emit 與 `checkDownloadReadiness`，同時仍保存原始 `.ax.txt` 供診斷）；誠實註記 `disableDiffing: true` 非平台絕對保證，若 CUA 回傳「有變更之局部 diff」仍須由 Agent 核對完整樹結構，不可將 `AX:OK` 視為完整樹之絕對證明。
         - 呼叫端／稽核在採信任何落地 observation 作為 `bind` 或 `reacquire` 前，**必須**核對 `ready_for_bind === true` 且 `stages.CAPTURE_BOUNDARY.status === 'RECORDED'`；靜止畫面於 `CAPTURE_BOUNDARY=RECORDED` 下相同 bytes 與不同 inode 僅記新鮮度註記、非自動阻擋，但 `CAPTURE_BOUNDARY=MISSING` 一律不得作為新鮮 `bind`／`reacquire` 證據（若同時出現相同 bytes 須標 `STALE_CAPTURE_SUSPECTED` 並停止消費）。
       - 於 L1163–1180（`### 單次 CUA 輸入保存 helper`）補明 **A12 強制落地紀律**：
         - 所有入口恢復（entry-recovery）之 CUA pointer／導覽點擊及所有 CUA handle reacquire 呼叫，皆須透過既有 `evidenceTools.persistSingleInput` 落地 `.input.request.json`／`.input.raw.json`／`.input.diagnostic.json`，禁止以手寫 curated blocker JSON 取代 raw receipt。
         - 補列三項操作邊界：(1) 工具若以回傳值而非 throw 回報錯誤，`raw.json` 為 `kind=RETURN`，Agent 仍須依實際內容歸類錯誤，不得宣稱成功；(2) handle reacquire 若回傳不可序列化之 live handle，須於 `invoke` closure 內暫存 live handle 並回傳純 JSON 投影（如 `{ ok, bundle_id, window_id, title }`）以利完整保存 raw；(3) 入口恢復／reacquire 不可用 `input_phase: 'DOWNLOAD_CONTROL'`（應標如 `ENTRY_RECOVERY`／`HANDLE_REACQUIRE`），每次重試須使用新唯一 `operationId`（遵守 `wx` 不覆寫），需要時間邊界時由 Agent 另以 `HOST_JS_DATE` 記錄並標 `os_event_time=UNKNOWN`。
  2. `tests/test_notes_input_helper.py`（聚焦離線回歸測試，涵蓋 A5 與 A13 正反路徑）：
     - 更新 `test_initial_observation_marker_encloses_one_js_block`：額外斷言 `CAPTURE_BOUNDARY` 守衛存在於 `documented_initial_observation_source()`。
     - 於 `NotesInputHelperTests`（或對應測試類別）新增測試：
       1. `test_observation_ax_no_change_stub_persists_raw_and_fails_closed`：以 `subTest` 覆蓋實際 CUA 兩行樣本（`Window: "LINE"`＋`The focused UI element is ...`）與單行空標題樣本（`Window: ""`），驗證 `.ax.txt` 與 `.screenshot.bin` 與 `.diagnostic.json` 均成功寫入且 `AX_PERSISTENCE === 'MATCH'`，但 `stages.AX` 為 `{ status: 'DIFF_NO_CHANGE', full_tree: false, diff_only: true, stale_index_warning: true }`、`blockers` 含 `'AX:DIFF_NO_CHANGE'`、`ready_for_bind === false`，且 `notesIntentDispatch.checkDownloadReadiness` 拒絕回 `STOP`（`DOWNLOAD_OBSERVATION_INVALID`）。
       2. `test_observation_ax_no_change_guard_avoids_false_positives_and_rejects_whitespace`：以 `subTest` 覆蓋 (a) 內文含 `"There has been no change in the accessibility tree"` 字串的完整 AX 樹／JSON、(b) 合法短樹（約 194 bytes 浮動視窗＋menu bar），驗證兩者皆維持 `stages.AX.status === 'OK'`、`full_tree: true`、`diff_only: false`、`ready_for_bind === true`；另覆蓋 (c) 純空白字串（`' \n\t '`）記為 `AX:EMPTY`、`ready_for_bind === false`。
       3. `test_observation_capture_boundary_stage_distinguishes_recorded_and_missing`：驗證 `captureAndPersist` 成功與 capture throw 皆為 `stages.CAPTURE_BOUNDARY.status === 'RECORDED'`，而 `getApp` pre-call 失敗與 bare `persistObservation`（未傳 `hostCalls`）皆為 `stages.CAPTURE_BOUNDARY.status === 'MISSING'`（且 bare `persistObservation` 仍保持 `ready_for_bind === true`、`blockers === []` 相容既有呼叫端）。
     - 於 `NotesInitialObservationBlockTests` 新增測試：
       4. `test_initial_observation_no_change_ax_persists_but_never_emits`：以 no-change AX 執行 `cua-initial-observation`，驗證拋 `CUA_RAW_OBSERVATION_INCOMPLETE`＋`AX:DIFF_NO_CHANGE`、`emits == []`、`len(writes) == 1`，且 `.ax.txt`／`.screenshot.bin`／`.diagnostic.json` 仍落地保存供唯讀診斷。
       5. `test_initial_observation_missing_capture_boundary_fails_closed_without_emit`：以 stub 令 `captureAndPersist` 回傳 `ready_for_bind: true` 但 `stages.CAPTURE_BOUNDARY.status === 'MISSING'`，驗證 `cua-initial-observation` 仍 fail-closed 拋 `CUA_RAW_OBSERVATION_INCOMPLETE`＋`CAPTURE_BOUNDARY:MISSING`、`emits == []`、`len(writes) == 1`。

### Slice 2（分派給 Worker2 `wA:p4`）：Skill 與 4 份參考文件契約收斂（A1–A4、A7–A11、Q6 與跨檔引用）

- **檔案白名單（僅 5 檔，與 Slice 1 零重疊）**：
  1. `.agents/skills/line-notes-agent-cua/SKILL.md`
  2. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`
  3. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`
  4. `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md`
  5. `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md`
- **具體修改內容（採單一本文＋精煉連結原則，嚴禁更動既有 Markdown 標題／錨點與新增 D8／D9）**：
  1. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`（入口狀態、通道能力與有界恢復階梯唯一本文）：
     - `## 導覽與輸入紀律`（L129, L137）：補明 (a) no-change AX（`AX:DIFF_NO_CHANGE`、`full_tree=false`）不得作為完整 AX 或沿用舊索引，詳見 `evidence-template.md#cua-觀察原件落地`；(b) 在同一 `-10005 noWindowsAvailable` 錯誤下輪換截圖像素／螢幕點／視窗相對座標空間不是新方法或有效映射修正，兩次無新資訊即停。
     - `### 分開記錄頁面、前景與能力`（L165–172）：
       - `foreground` 列補明：`VALID` 僅覆蓋 app／window 綁定與交接，不代表頁面角色為 `LIST`、入口仍可用或控制可達（可與 `ENTRY_LOST` 同時成立）。
       - `input_capability` 列加入 `PARTIAL_AX_ONLY`：表示 AX 元素／選單輸入可用但 pointer 座標通道不可用；對僅視覺可見且須座標點擊的控制不得當作 `AVAILABLE`，該路徑須按 `INPUT_UNAVAILABLE` 處理。不新增額外 ad-hoc schema 欄位。
     - `### 有界恢復階梯`（L174–181）：
       - 步驟 3 與步驟 6 統一限定「當次 CUA 工具文件支援的唯讀 app／window 列舉與 handle reacquire」；明禁猜測未記載於當次工具文件的 API 參數形狀（如未記載時不得試探 `getApp({windowId})`），並明訂 `osascript`／System Events／外部 CGWindow 查詢**非** CUA handle reacquire，不得作為前景／handle 恢復或座標輸入依據（僅能標為非 CUA OS 唯讀診斷）。
       - 明訂所有入口恢復之 pointer／導覽嘗試與 CUA handle reacquire 呼叫均須透過 `evidenceTools.persistSingleInput` 保存原始 request／raw／diagnostic（見 `evidence-template.md#單次-cua-輸入保存-helper`），不得僅留手寫 curated 摘要。
       - 步驟 5 補明：重複 `noWindowsAvailable` 時輪換座標空間不計新證據，連續兩次無新資訊即停並依步驟 6 進 `HANDOFF_REQUIRED`。
     - `### 重新交接與帳本 Session`（L185）：補明同一有效前景內重取 handle 沿用 notes Session 只影響帳本綁定，仍須經 `captureAndPersist` 取得 `CAPTURE_BOUNDARY=RECORDED` 之新觀察（禁止 bare `persistObservation` 充當新觀察，缺邊界合併相同 bytes 標 `STALE_CAPTURE_SUSPECTED`）並重新核對頁面角色與入口連續性，`ENTRY_LOST` 仍須停止派送。
  2. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`（CLI 鎖、快照基準、scope 統計與 staging 界線唯一本文）：
     - `## CLI 共同契約`（L10, L16）：
       - 新增明確序列執行規則：**同一 `--records-root`（`records` lock）或同一 `--collection`（`collection` lock）的所有 notes CLI 命令一律嚴格序列執行**，禁止以並行 shell 工作或同回合並行工具呼叫同時執行 `summary`/`memory`/`evidence-audit` 與 `resume` 或其他帳本命令（因 `summary` 亦持 exclusive non-blocking `flock`）。
       - 修正 L16 與 `notes.py:8467-8476` 對齊：明確區分唯讀命令（`lists`/`memory`/`summary`/`evidence-audit`/`restart preview`/`reattest preview`）遇 `NOTES_LOCK_BUSY` 回 `retry_safe=true` 可於鎖釋放後序列重試一次；寫入／交易命令（含 `resume`）回 `retry_safe=false`，須先停止並序列查帳本狀態，不得盲目重試。
     - `## 合格環境附屬項`（L21）：釐清列表目錄下的 `.line-notes-incoming-*` 屬交易 staging 目錄，非本定義所述完成貼文媒體容器內之非預期額外檔。
     - `### 舊 UNKNOWN 的安全隔離與一次補下載`（L140, L142, L163）：L140 統一改為「當次 CUA 工具文件支援的唯讀 app／window 列舉與 handle reacquire」；L142／L163 註明空目錄或單一穩定媒體檔之舊 staging 隔離條件僅適用 UNKNOWN v5 隔離路徑。
     - `## 恢復與不可解鎖狀態`（L466, L470, L472）：
       - L466（`STOPPED` 恢復列）：註明不要求舊 staging 為空。
       - L470：補明舊 `STOPPED` staging（即使為空目錄）一律原樣保留，不清理、不刪除、不合併、不發布，亦不新增 helper 或修改目錄，僅於回報保留殘留晚到檔風險註記；成功發布後新 recovery staging 不存在屬正常行為，非 `LOCAL_CHANGED`。
       - L472（`expected_tip`）：補明 `summary` 的 `expected_tip` 代表讀取當下最新事件鏈頭；舊 `summary` 快照（較低 `sequence`，如 bind 後快照）僅供歷史對照，不得充當現行 blockers、現行 `unresolved_attempts` 或 fencing 基準。
     - `## 結束對帳`（L491，並同步 L10／L253 用語）：
       - 精確定義 `current_incomplete`：僅計 `status_counts_scope` 範圍內媒體之 `PENDING`/`PREVIOUSLY_INCOMPLETE`/`UNKNOWN`/`PROTECTED_HISTORY`，**不含**貼文層 `.state=DETAIL_PENDING`；因此 `current_incomplete=0` 在仍有 `DETAIL_PENDING` 貼文或 `all_known_media_complete=false` 時絕不代表全列表完成（未細盤貼文之媒體總數為 `UNKNOWN`）。
       - 明確區分貼文列欄位 `.state`（`NO_MEDIA`/`MEDIA`/`DETAIL_PENDING`，導出 `POST_DETAIL_PENDING`）與媒體列欄位 `status`（六類業務狀態）；所有計數回報須錨定最新序列 `summary` 的 `expected_tip`。
  3. `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md`：
     - `## 本機可用性：LOCAL_MISSING 與 LOCAL_CHANGED`（L147）：補一句 `LOCAL_MISSING`/`LOCAL_CHANGED` 僅核對已完成貼文目錄及其保存內容，不以交易 staging 目錄存否判定（成功發布後原 staging 不存在非 `LOCAL_CHANGED`；舊 `STOPPED` 空 staging 照常保留並註記晚到風險）。
     - `## 回報模板`（L204–213）：
       - 明確加入 `最新帳本基準：expected_tip.sequence / sha256`、`貼文層（.state）：總數=... / MEDIA=... / NO_MEDIA=... / DETAIL_PENDING=...`、`業務狀態（scope=...；current_incomplete=... 僅計 scoped media，不等於全列表完成）`。
       - 新增獨立行：`GUI／入口與通道狀態：page_role=... / entry_status=... / foreground=... / observe_capability=... / input_capability=... / gui_blockers=...（與 notes CLI dispatch_blockers 分開；CLI 不觀察 GUI）`。
       - 保留舊 staging 晚到風險註記位置。
  4. `.agents/skills/line-notes-agent-cua/SKILL.md`（精煉摘要＋連結，不堆砌長文）：
     - L30：將「可用的唯讀 app/window 列舉與 handle reacquire」統一為「當次 CUA 工具文件支援的唯讀 app/window 列舉與 handle reacquire」。
     - L34：補一句同一 `--records-root`／`--collection` 的 notes CLI 命令一律嚴格序列執行，禁止並行 `summary` 與 `resume`（見 `download-and-ledger.md#cli-共同契約`）。
     - L61：補明同前景重取 handle 沿用 Session 只影響帳本綁定，仍須經 `captureAndPersist`（`CAPTURE_BOUNDARY=RECORDED`）重核頁面角色與入口，`foreground=VALID` 不等於入口可用，`ENTRY_LOST` 仍停止派送。
     - L119–124（回報契約）：修正「舊 `status_counts`」措辭為「`status_counts` 僅代表 `status_counts_scope` 範圍」，要求一併列示最新 `expected_tip`、貼文層 `.state` 計數（總數／`MEDIA`／`NO_MEDIA`／`DETAIL_PENDING`）、`current_incomplete` 之 scoped 定義、舊 `STOPPED` 空 staging 保留與晚到風險，以及獨立之 **GUI／入口與通道阻塞欄位**（明示與 CLI `dispatch_blockers` 分開，`dispatch_blockers` 僅反映帳本簿記，不代表 GUI 入口可用）。
  5. `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md`（只精煉既有案例，不新增 D8／D9）：
     - **C27**（L236）：於全域 blocker 清單補明或連結 GUI 級全域阻塞（`ENTRY_LOST`、`INPUT_UNAVAILABLE`／`PARTIAL_AX_ONLY` 缺所需通道）與 CLI `dispatch_blockers` 分開且同樣停止依賴該前提的新派送。
     - **D2**（L255–259 與 L269 摘要待盤列）：補明 no-change AX（`AX:DIFF_NO_CHANGE`）只可支撐 `RETURN_NOT_OBSERVED`／`UNKNOWN`，不可判 `RETURNED` 或沿用舊索引；L269 補明貼文欄位為 `.state` 且 `current_incomplete=0` 仍不代表全列表完成。
     - **D4**（L280–287）：納入 `PARTIAL_AX_ONLY`（AX 可點但 pointer 回 `-10005 noWindowsAvailable`）、禁止輪換座標空間重試（兩次無新資訊即停進 `HANDOFF_REQUIRED`）、禁止猜測未載明之 handle API（如 `getApp({windowId})`）、明訂 `osascript`／System Events 非 CUA reacquire，並要求所有恢復嘗試經 `persistSingleInput` 留存 raw receipt（連結 `gui-inventory.md` 與 `evidence-template.md`）。
     - **D5**（L289–296）：補明同前景 reacquire 須以 `captureAndPersist` 取得 `CAPTURE_BOUNDARY=RECORDED` 之新觀察並重核入口（`foreground=VALID` 不覆蓋 `ENTRY_LOST`；`CAPTURE_BOUNDARY=MISSING` 不可採信為新鮮觀察，合併相同 bytes 標 `STALE_CAPTURE_SUSPECTED`）。

## 4. 驗收定義（Definition of Done）與驗證命令

所有實作完成後，於 `/Users/hsiaojohnny/dev/Line_backup` 依序通過以下檢查：

1. **Diff 與範圍衛生**：
   - `git status --short --branch`：僅白名單 7 檔（Slice 1 的 2 檔＋Slice 2 的 5 檔）與 `docs/plans/20261126-notes-entry-anomalies/` 計畫／審查紀錄檔異動；`src/`、`docs/LINE相簿備份_使用手冊.md`、`AGENTS.md`、`docs/diagnostics/20261126-notes-entry-anomalies/問題提報單.md` 及兩項既有未追蹤檔完全未動。
   - `git diff --check`（exit 0）。
   - 隱私檢查：確認所有新增／修改之 Git 追蹤檔不含真實群組／清單名稱、人名或實際使用者本機路徑。
2. **文件錨點與規則一致性檢查**：
   - 核對 6 份 Skill／references 檔案的所有既有 `##`/`###` 標題與錨點完整保留、交叉連結有效、無跨檔規則衝突。
3. **自動化離線回歸**：
   - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help`（exit 0）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py`（exit 0，原有 64 項＋新增 A5／A13 正反案例全量通過）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py`（exit 0）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`（exit 0，全量通過）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`（exit 0，相簿相容無回歸）
4. **獨立審查關卡**：
   - **Plan Review**：由下方 Reviewer pane（`wA:p2`）使用 `code-reviewer` Skill 並遵守 `AGENTS.md` Independent Review Constitution 審查本計畫，修正所有提出的問題直至取得 `APPROVE`。
   - **Code & Security Review**：Worker1／Worker2 平行實作完成並通過全量離線測試後，將精確 `git diff` 與驗證輸出提交 Reviewer（`wA:p2`）執行獨立 Code & Security Review，視建議評估是否 replan 並修正直至取得 `APPROVE`。
5. **證據界限聲明**：
   - 本計畫全部驗證屬離線單元測試與靜態文件核對；真實 LINE 記事本 GUI、CUA 實機 `noWindowsAvailable` 重現、window handle reacquire、跨 Session 恢復與正式 LINE E2E 一律維持 `NOT_RUN`。
