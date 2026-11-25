# LINE 記事本 Pre-Bind「零同名候選」誤判與 `evidenceTools` 未載入歸因修復計畫

- 計畫日期：2026-11-25（Asia/Taipei）
- 版本：v2（整合 Worker1／Worker2 唯讀預檢回饋，檔案白名單維持不變）
- 專案：`/Users/hsiaojohnny/dev/Line_backup`
- 分支：`feature/line-notes-media`
- 基準 HEAD：`ab525d3284f801df3508e328619c3df245f77261`
- 對應私有問題提報單：`.local/line-backup/tasks/notes-daily-20261125-misread/問題提報單.md`（本計畫不夾帶真實群組名稱、人名或帳本 UUID）
- 既有未追蹤檔保留：`2026.1122_問題提報單及意圖釐清點.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/`（本計畫不修改、不覆寫、不 stage）

## 1. 核心目標與問題根因定位

本專案核心目標是讓不同模型、Agent 與 Session 皆能透過同一日常正式 Prompt 與 `line-notes-agent-cua` Skill，搭配原生 macOS Computer Use 與 notes 輔助 CLI，**全程無人值守完成 Owner 交接的單一 LINE 記事本列表照片與影片備份及跨 Session 接續**（不要求 Owner 手填 UUID／key／JSON，也不要求先在既有帳本清單中找到同名項目才能備份）。

在 `ab525d3` 修正「`lists` 截斷與名稱相近候選」後，2026-11-25 新一輪實機日常嘗試仍於 `bind` 前提前停止。依據私有問題提報單與現行文件實碼逐行比對，**本次零 CLI 錯誤、零帳本寫入、零下載派送**，真正可重複發生的結構性缺口有四點：

1. **主要根因一：`display_name` 對稱規則缺口與「零同名候選」狀態未分離**
   - 現行 `SKILL.md` 與 `evidence-decision-cases.md`（D6）雖禁止單憑中文標題認領帳本，並防止因「名稱相近」而提前停止，卻**未明文禁止以 `display_name == 畫面標題` 過濾候選**，也未明確區分「**零同名候選（`matches: []`）**」與「**完成全部 N 份候選 `identity`／`posts` 交叉比對後仍有真實身分歧義（Route C）**」。
   - 結果 Agent 自行加上「畫面顯示標題必須與某份帳本 `display_name` 完全同名」的隱含門檻：在 `lists` 中查得 0 筆同名後即誤判身分無法核對並停止，要求 Owner 重新交接前景。
2. **促成因素二：多處殘留語句把「相符既有帳本」寫成必要條件或停止門檻**
   - `download-and-ledger.md:232,245`（緊鄰「啟動與帳本對帳」上方）原寫「先用它唯一定位…相符的帳本」及「`無相符帳本、多候選、索引／歷史損壞或無法唯一定位時停止`」，極易被誤讀為「無相符既有帳本就停止日常備份」，而非走 Route B 新列表自動 `init`。
   - `SKILL.md:78`（「列表身分須由本次連續入口、當次畫面／AX 脈絡及相符帳本共同支持」）與 `gui-inventory.md:18`（「可靠依據：…以及相符的本地帳本／觀察 evidence」）將「相符帳本」並列為必要共同依據，未明言新列表（Route B）係以「當次觀察證據＋全部 N 份已註冊候選之正面排除」成立，容易強化「必須先有相符既有帳本」的誤解。
3. **次要根因三：`evidenceTools` 非 CUA runtime 內建全域變數的預載說明與執行防護不足**
   - `SKILL.md`、`download-and-ledger.md` 與 `evidence-template.md` 直接要求在 CUA Node runtime 實跑 `evidenceTools.captureAndPersist`，卻未在前置處明寫 **`evidenceTools` 並非 CUA runtime 預先注入的全域物件，必須先於同一 Node runtime 執行 `evidence-template.md` 的 `cua-evidence-tools` 定義區塊建立 `evidenceTools`**。
   - 導致 Agent 只檢查 `typeof evidenceTools === "undefined"` 就過早宣稱 runtime 沒有 `captureAndPersist`、無法保存原件（後續實測 `await import('node:fs/promises')` 回傳 OK）。且 `cua-initial-observation` 區塊未對未載入 `evidenceTools` 拋出明確自癒錯誤，若誤跑只會得到易被誤解為環境缺件的裸 `ReferenceError`。
4. **回報缺口四：Pre-Bind 阻塞缺少具體證據契約**
   - 現行 Route C 尚未明文禁止以抽象的「找不到同名帳本」「名稱不符」或「`typeof evidenceTools === "undefined"`」作為 blocker 要求 Owner 重交前景，須明確要求指出未成立的具體身分證據、衝突候選之 `identity`／`posts` 差異或實際 CLI／helper `error`／`stages`／`blockers`。

補充排除：報告提及工作目錄不存在 `policies/v4.9.0/workflow-routing.md`（exit 1），經查專案現行 `.agents/skills/`、`src/`、`tests/` 與使用手冊均不依賴該退役 Harness 路徑，依 `AGENTS.md` 維持不恢復、不新增。

## 2. 明確非目標與最小修改邊界（Strict YAGNI / KISS）

- **不修改 `src/line_backup_batch/*.py`**：本輪零 CLI 缺陷證據，無需新增任何 CLI flag、子命令或 schema。
- **不修改 `docs/LINE相簿備份_使用手冊.md` 與 `AGENTS.md`**：日常正式 Prompt 已明載「新列表在無缺損歷史或候選歧義時自動初始化，既有列表綁定原帳本」，且依手冊 L628 與 `AGENTS.md` 邊界分工，操作規則與範本細則維護在 Skill／references，不膨脹 Prompt。
- **不修改 `download-and-ledger.md` 已通過實測的唯讀 Python 候選展開腳本**：該腳本原本即全量展開全部 N 份候選的 `identity` 與 `posts` 錨點、不含任何名稱過濾；只需於腳本前說明禁止改寫成 `display_name` 過濾器即可。
- **不改動既有 Markdown 標題與錨點**（`#啟動與帳本對帳`、`#候選帳本展開唯讀`、`#列表`、`#目標與下載控制就緒b1`、`#cua-觀察原件落地`），新增原則一律以粗體段落呈現，確保既有交叉連結零破壞。
- **不更動 `evidenceTools` 既有函式簽章、`BLOCK_MARKERS` 7 項順序，亦不新增多餘 D8／D9 案例或 try/catch TDZ wrapper**：直接於既有 D6／D7 精煉補齊，且維持 `evidence-template.md` 為 `evidenceTools` 預載規範唯一本文（其餘文件僅以一句＋連結引用，避免文案漂移）。
- **不放寬任何資料保護紅線**：仍禁止單憑中文標題／OCR／`active_hint`／單一日期／單一張數認領帳本；仍禁止未完成全部 N 份候選核對即因「零同名」直接 `init`；真實歧義或未註冊 `active_hint`／索引異常仍須零帳本寫入停在 `init`／`bind` 前；未實測之真實 LINE GUI／CUA 實機／E2E 維持 `NOT_RUN`。
- **不觸碰**：`notes-backup-records/`、`backup/`、`.local/line-backup/active-notes-task.json`、`.local/line-backup/tasks/notes-daily-20261125-misread/問題提報單.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/`、`2026.1122_問題提報單及意圖釐清點.md`。

## 3. 平行子任務切片設計（零檔案重疊）

計畫經下方 Reviewer pane（`w9:pD`）依 `code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution 審查通過（`APPROVE`）後，分派給右方兩個 Worker pane 平行執行：

### Slice 1（分派給 Worker1 `w9:pF`）：`evidenceTools` 預載歸因紀律、`cua-initial-observation` 未載入防護與離線回歸

- **檔案白名單（僅 2 檔）**：
  1. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`
  2. `tests/test_notes_input_helper.py`
- **具體修改內容**：
  1. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`（作為 `evidenceTools` 預載規範唯一本文）：
     - 於〈CUA 觀察原件落地〉之「實作試跑與歸因紀律」段補明：
       - `evidenceTools` 並非 CUA runtime 預先注入的全域物件，而是由本節下方 `cua-evidence-tools` 定義區塊建立；首次使用前必須先於同一 CUA Node runtime（例如 `mcp__cua_repl.js`）按「先定義、後呼叫」順序執行該定義區塊，再執行 `evidenceTools.captureAndPersist`（或對既有 capture 執行 `persistObservation`）。
       - 僅檢查 `typeof evidenceTools === "undefined"` 只代表尚未載入定義區塊，屬 `NOT_RUN`，不得宣稱環境不支援落地或缺少 helper；只有載入後實跑拋出真實 `error`（如 `import('node:fs/promises')` 被拒）或回傳 `ready_for_bind=false`（附 `stages`／`blockers`），才屬實證保存阻塞。
     - 於 `<!-- cua-initial-observation:start -->` 至 `<!-- cua-initial-observation:end -->` 的唯一 `js` 區塊最前方加入最小防衛檢查（保留單一 `js` 區塊、區塊作用域讀回顯示與零改動 `BLOCK_MARKERS`）：
       ```js
       if (typeof evidenceTools === 'undefined' || !evidenceTools ||
           typeof evidenceTools.captureAndPersist !== 'function') {
         throw new Error(
           'CUA_EVIDENCE_TOOLS_NOT_LOADED: evaluate the cua-evidence-tools ' +
           'block from evidence-template.md in this CUA Node runtime first; ' +
           'typeof evidenceTools === "undefined" is NOT_RUN, not an environment blocker'
         );
       }
       ```
     - 於 `<!-- cua-initial-observation:end -->` 下方說明段補註一句：本初始觀察範例要求先於同一 Node runtime 執行 `cua-evidence-tools` 定義區塊；若未先載入（或物件缺少 `captureAndPersist`）即直接執行此範例，會先拋出 `CUA_EVIDENCE_TOOLS_NOT_LOADED`（屬 `NOT_RUN`，非環境不支援），不觸發任何 capture 或 emit（若在同一個 module 內誤把 `const evidenceTools` 定義排於本段之後則屬拼接順序錯誤）。
  2. `tests/test_notes_input_helper.py`（在 `NotesInitialObservationBlockTests` 內）：
     - 將既有 `run_initial_observation` 參數化，新增可選參數 `tools_mode='tools'`（支援 `'tools'` 預設載入 `self.tools_source`、`'none'` 不載入工具區塊、`'empty'` 前置 `const evidenceTools = {};`），避免重複撰寫測試 runner；既有 4 個測試維持預設 `'tools'` 零行為改變。
     - 於 `test_initial_observation_marker_encloses_one_js_block` 新增斷言：`CUA_EVIDENCE_TOOLS_NOT_LOADED` 存在於 `documented_initial_observation_source()`。
     - 新增 1 個聚焦離線回歸測試 `test_initial_observation_unloaded_tools_fails_closed_without_capture_or_emit`，以 `subTest` 涵蓋 `tools_mode='none'` 與 `tools_mode='empty'` 兩情境，驗證兩者皆回傳非零 exit code、`stderr` 包含 `CUA_EVIDENCE_TOOLS_NOT_LOADED` 且不含 `ReferenceError`、`captureCalls == 0`、`emits == []`、`writes == []`，且 `observation_dir` 內無任何檔案寫入。

### Slice 2（分派給 Worker2 `w9:pE`）：Pre-Bind 消除同名門檻、分離「零同名候選」與真實歧義、Blocker 證據契約與 D6／D7 補強

- **檔案白名單（僅 4 檔）**：
  1. `.agents/skills/line-notes-agent-cua/SKILL.md`
  2. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`
  3. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`
  4. `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md`
- **具體修改內容**：
  1. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`（Pre-Bind 與三路判定唯一操作本文）：
     - **原子修正「證據路徑與唯讀查詢」查詢既有帳本段落（原 L232 與 L245 兩處同步對齊）**：明確限定該段僅說明「欲刷新單一既有帳本摘要時」的 `summary --records-root` 查詢，不得拿猜測路徑呼叫 `summary`；**查無相符既有帳本（或零同名候選）不是日常備份的停止條件**，應依下方[啟動與帳本對帳](#啟動與帳本對帳)完成全部 N 份候選核對後走既有帳本 `bind`（Route A）或新列表自動 `init`（Route B），僅真實多候選歧義、索引／歷史損壞或無法唯一定位（Route C）才停止。
     - **更新〈啟動與帳本對帳〉步驟 2**：精煉補一句「須先於同一 CUA Node runtime 載入 `evidence-template.md` 的 `cua-evidence-tools` 定義區塊再實跑 `evidenceTools.captureAndPersist`；未載入（`typeof evidenceTools === "undefined"` 或 `CUA_EVIDENCE_TOOLS_NOT_LOADED`）屬 `NOT_RUN`，不得宣稱環境不支援」，並維持連結至 `evidence-template.md#cua-觀察原件落地`。
     - **更新〈候選帳本展開（唯讀）〉程式碼圍籬前說明段**：在保留既有「不得只留少數頂層欄位 wrapper」句的基礎上，明確補列「亦不得撰寫只保留 `display_name == 畫面標題` 的過濾器（例如得到 `matches: []` 後即停止）」；下方 Python 腳本維持零改動。
     - **更新三路列表判定契約與「未執行與真實失敗」**：
       - 在三路契約前以精煉粗體段落定義**前景目標與 `display_name` 對稱規則**：Owner 交接的有效 LINE 記事本前景即為本次目標，不需先在 `lists` 找到同名帳本才可備份；`display_name`／中文標題只作線索，**同名或不同名都不能單獨決定 `bind`、`init` 或停止**。明確分離兩個狀態：「**零同名候選**」僅屬尚未完成核對之中間觀察（不等於身分不符／候選歧義／停止理由，亦不等於自動認定新列表），必須完成全部 N 份 `identity`／`posts` 核對；「**完成全核對後仍有真實歧義**」才是 Route C 阻塞。
       - **Route A** 補明：即使帳本 `display_name` 與目前畫面標題不同，只要入口、視窗脈絡、`identity`／`signals` 與首屏多卡錨點唯一交叉吻合且其餘 N−1 份可正面排除，仍綁定原帳本（不重 `init`）。
       - **Route C** 與「未執行與真實失敗」補明 **Blocker 證據契約**（與「`NOT_RUN` 不是失敗」一致）：停止並回報 blocker 時，必須指出具體未成立的身分證據、衝突候選之去識別化 ID 與 `identity`／`posts` 差異，或實跑 CLI／helper 之 exit code／`error`／`stages`／`blockers`；禁止以抽象的「找不到同名帳本」「名稱不符」或「`typeof evidenceTools === "undefined"`」要求 Owner 重新交接。
  2. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`（〈三層身分 → 列表〉）：
     - 釐清「可靠依據」中的本地帳本角色：既有列表由當次連續入口、畫面／AX 脈絡與相符本地帳本共同支持；新列表不以既有相符帳本為前置，而由當次連續入口、已落地觀察證據與全部 N 份已註冊候選之正面排除成立。
     - 補明顯示名稱／中文標題對稱限制：**既不得單獨認領既有帳本，也不得作為必要匹配門檻或過濾鍵**；查無同名帳本（「零同名候選」）不等於身分不符或候選歧義，不得據此停止或要求重新交接，仍須完成全候選 `identity`／`posts` 核對後依三路契約處理。
  3. `.agents/skills/line-notes-agent-cua/SKILL.md`（〈日常入口與 Agent 責任〉第 2 點、〈三層身分與不可重下原則〉列表條款、〈工作流程〉第 1 點）：
     - 〈三層身分與不可重下原則〉列表條款：由「及相符帳本共同支持」修正為「及相符既有帳本（或對全部 N 份已註冊候選之正面排除證據，用於新列表）共同支持」，消除把相符既有帳本誤讀為必要前置的殘留風險。
     - 〈日常入口與 Agent 責任〉第 2 點與〈工作流程〉第 1 點（維持精煉摘要＋單一連結，不堆砌長文）：
       1. 補明 `evidenceTools` 須先載入定義區塊（見 `evidence-template.md#cua-觀察原件落地`），未載入（含 `typeof evidenceTools === "undefined"`）屬 `NOT_RUN`，不得宣稱環境不支援；
       2. 擴充為禁止因 `lists` 終端截斷、名稱相近或**查無同名帳本（零同名候選）**跳過全部 N 份 `posts`／`identity` 交叉比對提前停止；明寫 `display_name`／中文標題同名或不同名皆不可單獨決定 `bind`、`init` 或停止；
       3. 回報 Pre-Bind 阻塞必須指出具體未成立的身分證據、候選衝突或 helper 階段錯誤，不得以「名稱不符」要求重新交接。
  4. `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md`（精煉擴充既有 **D6** 與 **D7**）：
     - **D6**：將前提調整為涵蓋「多份名稱相近或畫面顯示標題在 `lists` 中零同名候選（`display_name` 完全相符為 0）」，補列禁止以 `display_name == 畫面標題` 過濾候選、禁止將「零同名候選」自動升格為身分不符／候選歧義或直接認定新列表，且 Route C 回報須附具體候選比對證據而非「名稱不符」。
     - **D7**：於情境 (a) 納入「未先載入 `cua-evidence-tools` 定義區塊而僅測得 `typeof evidenceTools === "undefined"`（或直接觸發 `CUA_EVIDENCE_TOOLS_NOT_LOADED`）即宣稱 runtime 缺少 `captureAndPersist`」，歸為 `NOT_RUN`／未載入 helper（非環境阻塞），允許動作明寫先於同一 Node runtime 載入定義區塊再實跑 `captureAndPersist`。

## 4. 驗收定義（Definition of Done）與驗證命令

所有實作完成後，於 `/Users/hsiaojohnny/dev/Line_backup` 依序通過以下檢查（以內容、marker 與錨點核對，不綁死會位移之行號）：

1. **Diff 與範圍衛生**：
   - `git status --short --branch`（僅白名單內計畫／審查紀錄／Skill／references／測試檔異動；`src/`、`docs/LINE相簿備份_使用手冊.md`、`AGENTS.md`、既有未追蹤檔完全未動）
   - `git diff --check`（exit 0）
   - 隱私檢查：確認所有新增／修改之 Git 追蹤檔不含真實群組名稱、個人姓名或真實 `local_list_id` UUID。
2. **文件錨點與規則一致性檢查**：
   - 核對 `SKILL.md`、`download-and-ledger.md`、`gui-inventory.md`、`evidence-template.md`、`evidence-decision-cases.md` 所有既有錨點完整保留、無規則衝突（含確認 `download-and-ledger.md` 查詢既有帳本段、`SKILL.md` 三層身分列表條款與 `gui-inventory.md` 列表條款皆與 Pre-Bind Route B 一致）。
3. **自動化離線回歸**：
   - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help`（exit 0）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py`（exit 0，含新增 `test_initial_observation_unloaded_tools_fails_closed_without_capture_or_emit` 之 `'none'` 與 `'empty'` 子案例）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`（exit 0，全量通過）
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`（exit 0，相簿相容無回歸）
4. **獨立審查關卡**：
   - **Plan Review**：由下方 Reviewer pane（`w9:pD`）使用 `code-reviewer` Skill 並遵守 `AGENTS.md` Independent Review Constitution 審查本計畫 v2，修復所有意見直至回傳 `APPROVE`。
   - **Code & Security Review**：Worker1／Worker2 完成後，將精確 `git diff` 與驗證輸出交付 Reviewer（`w9:pD`）執行獨立 Code & Security Review，視建議評估是否 replan 並修復至 `APPROVE`。
5. **證據界限聲明**：
   - 本計畫全部驗證屬離線自動化測試與靜態文件核對；真實 LINE 記事本 GUI、CUA 實機 `captureAndPersist`、10 份實機帳本全候選交叉核對、`bind`／`init`、下載與跨 Session 恢復維持 `NOT_RUN`。
