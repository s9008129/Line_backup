# LINE 記事本 Pre-Bind 歷史候選核對與 CUA 原件落地修復計畫

- 計畫日期：2026-11-25（Asia/Taipei）
- 版本：v1
- 專案：`/Users/hsiaojohnny/dev/Line_backup`
- 分支：`feature/line-notes-media`
- 基準 HEAD：`c9d315a22fc834d259ea0a6f957a22c3a35de7c3`
- 對應問題提報單：`docs/diagnostics/20261125-notes-daily-backup-handoff/問題提報單.md`
- 既有未追蹤檔保留：`2026.1122_問題提報單及意圖釐清點.md`（本計畫不讀取、不修改、不 stage）

## 1. 核心目標與問題定位

本專案的核心目標是以可重複使用的 Skill 驅動 AI Agent 搭配原生 Mac Computer Use 與 notes 輔助 CLI，**全程自適應地完成單一 LINE 記事本列表的照片與影片下載及中斷後接續（不依賴人工介入判斷恢復方式、不要求 Owner 手填 UUID／key／JSON）**。

依 `問題提報單.md` 與專案實碼查證，2026-11-25 日常備份於 `bind` 前停止的根因**並非 notes CLI 缺陷**（本輪零非零退出碼、零業務拒絕、零帳本寫入），而是兩個會讓不同模型／Session 反覆卡在 `bind` 前的 **Skill 指示與可執行範本缺口**，疊加 Agent 未依既有 helper 執行所致：

### 1.1 五項分析問題實證結論（對應提報單 §6）

1. **Q1（CUA Node runtime helper 能力與 H1／E4）**：
   - `evidence-template.md:64-345, 1070-1110` 的 `evidenceTools.captureAndPersist`／`persistObservation` 已於 CUA Node runtime 透過 `import('node:fs/promises')`、`util.types.isUint8Array`、`wx` 獨占寫入與逐 bytes SHA-256 讀回實作，並受 `tests/test_notes_input_helper.py` 覆蓋。
   - **真實缺口有二**：
     1. 缺少「**禁止未實際呼叫 `evidenceTools` 即宣稱環境不支援原件落地**」及「未執行（`NOT_RUN`）vs 真實失敗（附 `error`/`stages`/`blockers`）vs 工具 namespace 撤除（H3）」的明文歸因分流。
     2. `evidence-template.md:1114-1124` 的初始觀察呼叫範例透過 `captureAndPersist` 傳入 `emit: false`，呼叫後只 `nodeRepl.write(JSON.stringify(OBSERVATION))`，未像 Block 9 (`notes-intent-capture`, L1867–1870) 與 Block 12 (`notes-reveal-path`, L2020–2025) 示範**在 `ready_for_bind === true` 後讀回同一份落地截圖與 AX 呼叫 `nodeRepl.emitImage`／`nodeRepl.write`（零額外 capture）**。這容易誘發 Agent 為「先看見畫面」而改跑裸 `lineApp.getAXStateAndScreenshot()`，脫離持久化 helper 後誤認無法寫檔。
2. **Q2（10 份帳本、`lists` 截斷、空 AX 標題與多候選消歧 — E1／E2／E3／H2）**：
   - 實測目前本機 `notes lists` 單行輸出達 **376,989 bytes**，其中 `posts` 占 257,257 bytes（68.2%）、`media` 占 102,802 bytes（27.3%），其餘索引／識別欄位合計僅約 17 KB。`lists` 每列本就是完整的 `summary()` 投影（含每篇 `posts` 的 `source_order`、`date_summary`、`identity`、`media_count`、`state`）。
   - 當次 Agent 未先用既有 `notes_capture -- lists` 無損落盤至 `stdout.bin`，直接跑裸 `notes lists` 遭終端顯示截斷後，臨時 wrapper 又只抽取少數頂層欄位而丟棄 `posts` 與 `identity.signals`，看到多份名稱相近帳本及指向另一已註冊列表的 `active_hint`，即在未完成候選比對下提前停止。
   - 同時 macOS LINE Desktop 的 AX Window title 為空字串且列表節點泛用（2026-11-15 與 2026-11-25 兩次實機均同）。現行 Skill 雖禁止單憑中文名／OCR／日期／張數認領，但**缺少可執行的「完整 `lists` 展開 → `active_hint` 分流 → 多訊號逐一排除全部 N 份候選 → 三路決策（唯一既有帳本／證明新列表／真實歧義停止）」操作指引**。
3. **Q3（Pre-Bind 固定順序與失敗歸因紀律）**：
   - 須在 `SKILL.md` 與 `download-and-ledger.md` 固化「**完整 `lists` capture → CUA `captureAndPersist` 落地讀回與視覺呈現 → 入口確認＋多訊號全候選交叉核對與 `active_hint` 分流 → `evidence-pack`（新列表先 `list-key`→`evidence-pack`→`init`→讀回）→ `bind` → 舊交易收斂**」五步順序，並明文將未呼叫 helper／CLI（`NOT_RUN`）與真實失敗（具實際輸出／exit code／`error`／`stages`／`blockers`）嚴格分開。
4. **Q4（最小修改邊界：不改 Python CLI，只修 Skill／references 與離線 helper 回歸測試）**：
   - **不修改 `src/line_backup_batch/*.py`**（無任何 CLI 缺陷證據；`notes_capture -- lists` 已無損解決 377 KB 輸出截斷；`lists` 既有 JSON 契約受 `tests/test_notes_evidence.py:489-496` 黃金測試鎖定；新增 CLI flag 屬過度工程化）。
   - **不修改 `docs/LINE相簿備份_使用手冊.md` 與 `AGENTS.md`**（日常正式 Prompt 不得因實作細則膨脹，符合手冊 L628 與 `AGENTS.md` 邊界分工）。
   - 僅修改 Skill／references 與 `tests/test_notes_input_helper.py` 之最小必要區塊，直接消除上述兩個已證實可重複發生的結構性缺口。
5. **Q5（重跑前置事實保留）**：
   - 2026-11-25 本輪零帳本寫入、零 scan／attempt／下載，既有 10 份帳本與 `active-notes-task.json` 無需修復或遷移。後續具備原生 CUA 的新工作階段直接沿用同一日常正式 Prompt，以當次新原件從新訂 Pre-Bind 五步順序開始，不重用提報單文字描述作為視覺輸入。

## 2. 明確非目標與不採方案（Strict YAGNI / KISS）

- **不新增 `notes lists --brief` 或任何新 Python CLI 子命令／flag／schema**：既有 `notes_capture --output-root "$CAPTURE_PARENT" -- lists` 已完整保存 `stdout.bin` 且終端僅回約 180 bytes receipt，搭配文件提供之唯讀 Python 抽取命令即可一次展開全部 N 份候選的識別與首屏 `posts` 錨點，零程式複雜度與零介面破壞。
- **不改動 `evidenceTools.captureAndPersist`／`persistObservation` 的函式簽章與回傳形狀**：完全保持既有 383 項 `test_notes*.py` 與 `notes-intent-*` 區塊相容。
- **不放寬任何安全紅線**：仍禁止單憑中文標題／OCR／`active_hint`／單一日期／單一張數認領帳本；仍禁止未完成全候選核對即 `init`；真實歧義或未註冊 `active_hint`／索引異常仍須停在 `bind`/`init` 前；仍不要求 Owner 手填 UUID／key／JSON；不將離線測試宣稱為真實 LINE GUI／E2E PASS。
- **不觸碰**：`src/line_backup_batch/*.py`、`docs/LINE相簿備份_使用手冊.md`、`AGENTS.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/問題提報單.md`、`2026.1122_問題提報單及意圖釐清點.md`、任何真實 `notes-backup-records/`、`.local/line-backup/active-notes-task.json` 與 `backup/`。

## 3. 平行子任務切片設計（零檔案衝突）

計畫通過 Reviewer 審查後，將切割為兩個完全獨立、修改檔案零重疊的子任務，由 `Worker1` 與 `Worker2` 平行實作：

### Slice 1（分派給 Worker1 `w9:p8`）：CUA 初始觀察落地＋讀回顯示範本與離線自動化回歸

- **檔案白名單（僅 2 檔）**：
  1. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`
  2. `tests/test_notes_input_helper.py`
- **具體修改內容**：
  1. 在 `evidence-template.md`「CUA 觀察原件落地」（約 L53–62 與 L1114–1131）：
     - 補明**實作試跑與歸因紀律**：不得僅因 CUA 工具在對話介面呈現截圖／AX 就推斷「無法橋接至檔案系統」；必須先建好 canonical `TASK_PRIVATE_DIR` 與 `OBSERVATION_DIR`，並在同一個 CUA Node runtime（如 `mcp__cua_repl.js`）實際呼叫 `evidenceTools.captureAndPersist`（或對已取得的同次 `capture` 呼叫 `persistObservation`）。未執行屬 `NOT_RUN`，不得列為環境或工具不支援；只有實際執行拋錯（含 `import('node:fs/promises')` 被拒）或回傳 `ready_for_bind=false`，才保留真實 `error`（`name`/`code`/`message`）或 `OBSERVATION.stages`/`blockers` 作為環境／路徑阻塞。若 CUA 工具 namespace 於任務中途被撤除，只記工具可用性變動並停止，不可用對話摘要重建 AX／截圖原件。
     - 將 L1114–1124 的初始觀察呼叫範例加上明確標記 `<!-- cua-initial-observation:start -->` 與 `<!-- cua-initial-observation:end -->`（注意：**不可更動既有 `BLOCK_MARKERS` 的 7 個暫態工具列標記順序與內容**）。區塊內保留原本 `const OBSERVATION = await evidenceTools.captureAndPersist({...})`，先 `nodeRepl.write(JSON.stringify(OBSERVATION, null, 2))`，失敗則 `throw new Error('CUA_RAW_OBSERVATION_INCOMPLETE: ' + OBSERVATION.blockers.join(', '))`；成功（`OBSERVATION.ready_for_bind === true`）後於獨立區塊作用域 `{ ... }` 內以 `const fs = await import('node:fs/promises')`（避免與後續 Block 8 頂層 `const fs` 衝突）讀回 `OBSERVATION.assets.screenshot.path` 與 `OBSERVATION.assets.ax.path`，以既有 `evidenceTools.sha256` 與位元組長度核對與 `OBSERVATION.assets` 一致（不符即拋 `CUA_OBSERVATION_EMIT_READBACK_MISMATCH`），再呼叫 `await nodeRepl.emitImage(new Uint8Array(savedScreenshot))` 與 `nodeRepl.write(savedAx.toString('utf8'))` 供 Agent 視覺判讀（**零第二次 capture**）。
  2. 在 `tests/test_notes_input_helper.py`：
     - 新增 `documented_initial_observation_source()` 抽取 `<!-- cua-initial-observation:start -->` 至 `<!-- cua-initial-observation:end -->` 的唯一 `js` 區塊（並斷言標記內僅有 1 個 `js` 區塊且無多餘尾隨文字，不破壞既有 `BLOCK_MARKERS` 與 `test_a1_each_marker_encloses_one_js_block_in_document_order`）。
     - 新增聚焦離線回歸測試（於 Node.js 實際執行 `documented_tools_source()` ＋ `documented_initial_observation_source()`，所有暫存均位於 `TASKS` 內 `TemporaryDirectory`）：
       - **成功路徑**：模擬單次 `cua.getApp`／`getAXStateAndScreenshot`，驗證只呼叫 1 次 capture、AX／screenshot／diagnostic 落地且 `ready_for_bind === true`、`nodeRepl.emitImage` 收到與落地截圖檔案位元組完全一致的 `Uint8Array`、`nodeRepl.write` 含 `OBSERVATION` JSON 與完整落地 AX，且與後續 `const fs = await import('node:fs/promises')` 共存於同一頂層腳本無語法衝突。
       - **失敗路徑（不回放圖片）**：模擬 `PRIVATE_PATHS:FAILED`（observationDir 不存在）或 `CAPTURE:FAILED`（`getAXStateAndScreenshot` 拋錯），驗證拋出含具體 blocker 的 `CUA_RAW_OBSERVATION_INCOMPLETE`、`nodeRepl.write` 仍先輸出真實 `OBSERVATION`（含 `stages`/`blockers`），且 `nodeRepl.emitImage` 呼叫次數為 `0`。
       - **讀回漂移保護路徑**：模擬落地後檔案被篡改（或長度／SHA-256 不符），驗證拋出 `CUA_OBSERVATION_EMIT_READBACK_MISMATCH` 且不呼叫 `nodeRepl.emitImage`。

### Slice 2（分派給 Worker2 `w9:p9`）：Pre-Bind 固定順序、多候選帳本交叉核對、`active_hint` 分流與決策案例

- **檔案白名單（僅 4 檔）**：
  1. `.agents/skills/line-notes-agent-cua/SKILL.md`
  2. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`
  3. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`
  4. `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md`
- **具體修改內容**：
  1. `download-and-ledger.md`（〈啟動與帳本對帳〉，約 L265–275，作為唯一操作本文）：
     - 明確列出 **Pre-Bind 五步固定順序**：(1) 以 `notes_capture --output-root "$CAPTURE_PARENT" -- lists --collection "$ABS_COLLECTION"` 取得完整無截斷 `stdout.bin` 與 `COMPLETE` receipt；(2) 於 CUA Node runtime 實跑 `evidenceTools.captureAndPersist` 落地並讀回顯示同次截圖與 AX；(3) 入口確認＋展開全部 N 份帳本候選表並完成 `active_hint` 分流與多訊號交叉比對；(4) 依唯一結果封裝 v2 `evidence-pack`（新列表先 `list-key` → `evidence-pack` → `init` → 讀回 `list_key`）；(5) `bind` → 處理舊交易／open scan → 普通完整掃描。
     - 提供一段簡潔、純唯讀、相容 macOS `/usr/bin/python3`（Python 3.9+，無 f-string 反斜線、無 3.10+ 語法）的 `stdout.bin` 抽取命令：針對 `lists` 內**全部 N 份帳本**輸出精簡候選對照表（`local_list_id`、`records_root`、`list_key`、`display_name`、`context_id`、`identity`、`scan_coverage`、`post_count`、前 5 篇 `posts` 錨點之 `source_order`/`date_summary`/`media_count`/`state`/`identity`、`unresolved_attempts` 筆數、`dispatch_blockers`）以及 `active_hint` 是否命中已註冊清單；註明 `lists` 本身已含全部 `summary` 投影，不必為 N 份各跑 `summary`，且空帳本／空 `posts`／`active_hint=null`／`identity=null` 均可安全處理。
     - 明文分流 `active_hint`：
       - `active_hint` 精確對應 `lists` 內某筆已註冊帳本之 `records_root` 與 `local_list_id` 時，表示前次曾操作該帳本（切換至其他列表的日常常態）；核對確認非當次目標後即已完成核對，**不構成缺損歷史阻塞**。
       - 僅當 `active_hint` 指向未出現在 `lists` 的 root／ID，或 `lists`／索引讀取拒絕時，才視為潛在歷史缺損阻塞並停止 `init`／`bind`。
     - 明文定義**三路列表判定契約**（不要求 Owner 填 UUID／key／JSON）：
       - **既有列表唯一匹配**：恰有一份候選在當次入口與視窗脈絡、`identity`／`context_id`／`signals`、及首屏多張可見卡片錨點（順序／日期／摘要脈絡／媒體縮圖排列與數量；相近候選必要時唯讀核對其 `records_root/events/` 既有 `created`／`binding`／`page` 事件與已保存 `statement`）上交叉吻合，且其餘 N−1 份均有具體差異正面排除 → 直接封裝當次 observation／handoff 並 `bind`。
       - **證明新列表**：`lists` exit 0 且全部 N 份已註冊帳本均逐一核對並以具體差異正面排除（不重疊之頁首脈絡＋`posts`／`identity` 歷史）、`active_hint` 已核對且無未註冊／損壞歷史 → 以當次已落地多訊號建立 `visual_key`/`context_id`/`signals`（AX title 空白時明記 `ax_window_title=EMPTY`），走 `list-key` → `evidence-pack`（statement 明列全部 N 份已核對帳本排除依據，滿足 binding 與 history_scope）→ `init`（正式日常 Prompt 涵蓋恢復授權時加 `--recovery-authorized`）→ 讀回 `list_key` → `bind`。
       - **真實候選歧義或歷史缺口**：完成全部 N 份候選比對（含相近候選的 `posts`／`identity`／既有事件 `statement`）後，仍有 >= 2 份候選無法區分、或有空／過舊候選無法排除為當前列表、或有未註冊 `active_hint`／索引異常 → 停在 `init`／`bind` 前（零帳本寫入、零下載輸入），保留已落地原件與 `lists` capture receipt，向 Owner 回報去識別化衝突候選摘要與單一具體釐清動作。
     - 明文區分「未執行（`NOT_RUN`）」與「真實 CLI／helper 失敗（附實際 exit code／JSON／`error`／`stages`／`blockers`）」。
  2. `gui-inventory.md`（〈三層身分 → 列表〉，約 L16–20）：
     - 補充 macOS LINE Desktop 的 AX Window title 常為空字串且列表節點為泛用元素：這屬於可存取性資訊有限，**不是工具錯誤，也不阻止列表核對**。須以已落地讀回的同次截圖＋AX（視窗頁首視覺脈絡、記事本分頁狀態、首屏多張可見貼文卡片之順序／日期／文字脈絡／媒體縮圖排列）與全部候選帳本之 `identity`／`posts` 錨點（必要時既有事件 `statement`）交叉核對；新列表於 AX 標題空白時如實記錄 `ax_window_title=EMPTY`，仍不得單憑中文名稱、OCR、單一日期或單一張數認領。
  3. `SKILL.md`（〈日常入口與 Agent 責任〉第 1–2 點與〈工作流程〉第 1 點，約 L34–35、L86）：
     - 以精煉摘要串接上述 Pre-Bind 五步順序、禁止未執行 `evidenceTools` 即宣稱環境不支援落地、禁止因 `lists` 終端截斷或名稱相近而跳過 `posts`/`identity` 交叉比對提前停止，以及 `active_hint` 指向已註冊他帳本非缺損阻塞之原則；完整操作細則單一連結至 `download-and-ledger.md#啟動與帳本對帳`、`gui-inventory.md#列表` 與 `evidence-template.md#cua-觀察原件落地`，不重複堆砌長文。
  4. `evidence-decision-cases.md`（末尾順接新增 **D6** 與 **D7**，延續現有 D1–D5 結構）：
     - **D6：多候選帳本、已註冊他帳本 `active_hint` 與 AX 標題空白**：假設案例對照三路結果（唯一匹配、全部正面排除建新帳、完成全核對後仍消歧失敗而停止），明確禁止因終端截斷或名稱相近未查 `posts`/`identity` 就提前停在 `bind` 前，也禁止單憑中文標題認領或誤把已註冊他帳本 `active_hint` 當缺損阻塞。
     - **D7：CUA 原件落地未執行 helper vs 真實 helper 失敗／工具撤除**：明確區分僅看對話畫面即推斷不能落地（屬 Agent 未執行，非環境錯誤）、實跑 `captureAndPersist` 取得真實 `error`/`stages`/`blockers`（才屬實證阻塞）與中途 CUA 工具 namespace 撤除（停止且不以對話摘要補造原件）。

## 4. 驗收定義（Definition of Done）與驗證命令

所有實作完成後，必須於 `/Users/hsiaojohnny/dev/Line_backup` 依序通過以下檢查（嚴格零修改真實帳本／照片／未追蹤檔）：

1. **Diff 與範圍衛生**：
   - `git status --short --branch`（確認僅白名單內計畫／Skill／references／測試檔異動；`src/`、`docs/LINE相簿備份_使用手冊.md`、`AGENTS.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/問題提報單.md` 未改動；`2026.1122_問題提報單及意圖釐清點.md` 維持原狀未追蹤）
   - `git diff --check`（零空白／格式錯誤）
2. **文件與抽取腳本實測**：
   - 核對 `download-and-ledger.md` 中的唯讀 Python 候選展開片段在 `/usr/bin/python3 -B` 對合成 `lists` JSON（涵蓋多帳本、空 `posts`、`active_hint=null`、已註冊與未註冊 `active_hint`、`identity=null` 邊界）可正常執行並輸出完整對照表，不碰真實帳本。
   - 核對 `SKILL.md` 與各 `references/*.md` 交叉連結錨點存在且一致，無自相矛盾規則。
3. **既有與新增自動化回歸（全量離線檢查）**：
   - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help`（exit 0）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py`（exit 0，涵蓋新增 `cua-initial-observation` 成功／失敗／讀回漂移回歸案例）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`（exit 0，全量通過）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`（exit 0，相簿相容無回歸）
4. **獨立審查關卡**：
   - **Plan Review**：由下方 Reviewer pane（`w9:p7`）依 `AGENTS.md` Independent Review Constitution 審查本計畫並回傳 `APPROVE`，方得派工給 Worker1／Worker2。
   - **Code & Security Review**：Worker1／Worker2 完成並通過全量回歸後，將精確 `git diff` 與驗證證據交付 Reviewer（`w9:p7`）進行獨立 Code & Security Review，修復所有發現問題直到回傳 `APPROVE`。
5. **證據界限聲明**：
   - 本計畫的所有驗證屬離線自動化測試與靜態核對；真實 LINE 記事本 GUI、CUA 實機原件落地、10 份實機帳本匹配、`bind`、下載與跨 Session 恢復維持 `NOT_RUN`，不得以離線 PASS 冒稱實機 E2E 通過。
