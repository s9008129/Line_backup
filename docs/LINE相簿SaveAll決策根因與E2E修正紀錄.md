# LINE 相簿 Save All 決策根因與 E2E 修正紀錄

日期：2026-10-30（Asia/Taipei）

## 範圍

本文件整理一次 Owner 已授權的真實 LINE 相簿 E2E 中，Agent 為何沒有在初始決策直接使用相簿詳細頁的 `⋯ → 儲存全部`，以及後續如何補足觀察、找到 Save All 並完成多本備份。

本文件是 Planner handoff 與工程根因紀錄，不是新的產品實作、模型矩陣、GUI PASS 或硬性控制器設計。公開版已去識別化；私人畫面、照片、相簿名稱、原始檔名、Session 與本機路徑不進入版本庫。對應 GitHub Issue：[#44](https://github.com/s9008129/Line_backup/issues/44)。

## 結論

直接問題不是 Owner 沒有授權 Save All，也不是原生 CUA 完全缺少點擊能力。可證據支持的主要根因是：

> Agent 把「app-bound screenshot／AX 目前看不到獨立 popup」錯誤地轉成「沒有安全可執行的 Save All 目標／需要 Owner 再操作」，沒有把 popup 觀察與座標映射當成必須完成的中介目標。

LINE 的相簿詳細頁沒有常駐的 `儲存全部` 按鈕；它藏在右上未標示的 `⋯` 所開啟之獨立原生 popup。當 app-bound 畫面沒有 popup 時，正確做法是保存目前狀態、改用當次允許的唯讀桌面來源觀察 popup、建立可靠座標映射，再單次觸發 Save All；不是改走照片選取、逐張下載，或把觀察缺口誤報成授權缺口。

## 證據分層

### OBSERVED

- Owner 已授權當時交接列表的備份，並允許每個 attempt 最多一次 Save All。
- 有文件化的歷史事件中，Agent 已進正確相簿詳細頁並開過一次 `⋯`；app-bound screenshot／AX 沒顯示 popup，當時 Save All 為 0，chooser 未開。
- 同一次事件的唯讀桌面截圖顯示獨立 popup，且只有一個 `儲存全部`。
- 初始階段 Agent 停下並請 Owner 代操作；Owner 糾正並重新交接後，才以可靠身分與映射單次觸發 Save All。
- 2026-10-30 修正後的 E2E 中，多本相簿均由詳細頁 `⋯ → 儲存全部` 完成；每本重新觀察、重新映射，沒有以舊座標跨本操作。
- 每本皆保存 detail、intent、新空白目的地、outcome、verify 與 completion；chooser、檔案及 ImageIO 驗證分別提供不同層的結果證據。

### INFERENCE

- 照片網格是顯著 affordance，未標示 overflow menu 不是最直覺的下載入口；泛用 Computer Use 先驗可能優先聯想到單張、勾選或 `選擇項目`。
- 盤點／下載分階段與「先確認入口再前進」是必要安全設計，但若沒有在同一決策點明示 Save All 的唯一性，會提高狀態轉換成本。
- 「單本照片頁」若同時指相簿詳細頁與單張照片檢視器，會讓 Agent 對「先返回」或「先 Save All」產生 precedence 歧義。

### UNKNOWN

- 初始偏離時是否真的使用過 `選擇項目`、逐張下載或任何特定替代路徑；Owner 介入前的原始 CUA action trace 未保存，不能補造。
- 模型內部選擇機制、不同模型／effort 的遵循率，以及 provider 身分與 usage。
- 靜態截圖是否能像 OS 點擊審計一樣獨立證明每個 attempt 恰好一次；目前仍是否定的證據邊界。

## 第一性原理

一次可靠的 album-level 派送需要五個獨立 gate：

1. **授權**：Owner 已允許對指定列表寫入照片與派送 Save All。
2. **目標身分**：目前詳細頁確實對應已盤點清單中的正確相簿。
3. **畫面狀態**：知道 `⋯` 選單是否開啟，以及 popup 位於哪個 macOS window／capture surface。
4. **動作可達性**：能在最新證據中唯一辨識 Save All，建立安全點位，並確認前次未派送。
5. **結果證據**：點擊後看到 chooser、progress 或明確錯誤，再進 outcome、verify、completion。

正確狀態轉換：

```text
已核對相簿詳細頁
→ detail／intent 保存與讀回
→ 最新畫面開啟 ⋯ 一次
→ 觀察獨立 popup
→ 唯一「儲存全部」與安全點位
→ Save All 一次
→ chooser／progress／錯誤
→ outcome → verify → completion
```

此流程的下載 leaf 是 album-level 的 `儲存全部`，不是某張照片或 `選擇項目`。若看不到 Save All，缺失的是「使這個 leaf 可安全到達」的中介證據，而不是任務授權。

## 根因排序

### 1. Observation gap 被誤判成 action／authorization gap

主因。app-bound CUA 來源不含獨立 popup 時，Agent 沒有完成「popup 在另一 surface」的狀態判斷與座標映射，反而停下或要求 Owner 操作。這使一個可在授權內解決的觀察問題，錯誤地變成需要人代操作的授權／工具問題。

### 2. 正向規則存在，但替代路徑沒有在同一決策點封閉

Skill 已寫 Save All 是授權備份的下載動作，也有 popup／安全點位規範；但 top-level workflow 沒有直接寫明 `選擇項目`、逐張下載與單張下載都不是 fallback。選單同時存在 `選擇項目` 與 `儲存全部`，使替代路徑可能被局部合理化。

### 3. 入口詞義與 precedence 仍有張力

已授權目標的「相簿詳細頁」下一步可能是 Save All；「單張照片檢視器」則可能需要先安全返回。若兩者共用模糊的「單本照片頁」描述，Agent 可能先追求返回列表，尚未走到 Save All。

### 4. 缺少針對 popup 可達性的負向行為案例

既有 B08 覆蓋正向 Save All 與一次派送，但沒有明確區分：

- app-bound 來源看不到 popup，桌面來源可見；
- 所有允許來源都看不到 popup；
- popup 可見但 Save All 不唯一或映射不可靠；
- 點擊後沒有 chooser／progress／明確錯誤。

### 5. 泛用 CUA／模型先驗是促成因素，但不是已證模型缺陷

未標示 overflow menu 較不直覺，模型可能把「下載照片」聯想到單張或選取。此項可作為待測假說，不能由單次事件推論特定模型、provider 或後端。

## 本次修正與找到 Save All 的過程

1. Owner 糾正後，重新確認已授權任務與有效前景；重新交接不被當成新增下載授權。
2. 回到已確認相簿列表重新盤點，每本以日期、張數、封面、相鄰卡片與詳細頁核對身分。
3. 在詳細頁保存 detail，建立 intent 與新空白目的地並讀回，確保 Save All 前已有禁止重送的持久紀錄。
4. 在最新詳細頁畫面以新座標開啟 `⋯` 一次。
5. app-bound screenshot／AX 不含 popup，因此依 Skill 改用當次允許的唯讀完整桌面截圖與離線 OCR。
6. OCR 找到唯一 `儲存全部`，同時辨識危險鄰項 `刪除相簿`、`分享相簿`；沒有把第一個 `選擇項目` 當成下載動作。
7. 用同一相簿內共同可見的詳細頁標題框，建立 desktop pixel 到 CUA app-local 座標的 frame offset。
8. 將 Save All 文字框映射到 app-local 安全點，選在文字前緣並避開相鄰危險列。
9. 點擊前保存 mapping：唯一 menu label、危險鄰項、frame offset、安全點位、選單輸入次數。
10. 單次點擊 Save All，立即觀察到原生 folder chooser；chooser 是輸入已觸發的直接結果證據。
11. 以 Go to Folder 輸入完整目的地，讀回完整路徑與空白目錄，再單次確認。
12. 下載後核對檔數、非空、三次穩定清單、逐檔 SHA-256 與 ImageIO 完整解碼，保存 completion 並讀回。
13. 下一本重新從清單與詳細頁取得新畫面與新 mapping，不沿用上一本座標，也不對同一 attempt 重送。

## 能證明與不能證明

### 能證明

- 在本次 macOS CUA Session，`完整桌面截圖 → OCR → 共同錨點座標映射 → CUA app-local click` 確實可到達 Save All。
- 點擊後 chooser 立即出現，支持 Save All 已觸發。
- 多本相簿可在每本重新觀察與 mapping 後完成；檔案、manifest、ImageIO 與 completion 各有獨立證據層。

### 不能證明

- 初始偏離時實際走了哪一條替代路徑。
- 靜態檔案與 Agent 紀錄具備 OS 等級的「恰好一次」點擊審計。
- 特定模型的內部因果、跨模型遵循率，或 Markdown 規則能形成不可繞過的硬限制。

## 給 Planner 的最小處理

1. 將分散規則收斂成單一有序 Save All gate；細節維持一個來源，不重複多份。
2. 明確寫成：已確認的相簿詳細頁 → 唯一允許的 album-level 下載 leaf 是 `⋯ → 儲存全部`；`選擇項目`、逐張下載、單張下載都不是 fallback。
3. 將「授權已存在但 popup 不在 app-bound source」定義為 observation gap；先補當次允許的桌面／popup 觀察與映射。所有允許來源皆不可靠時才停止 Save All，且不得改走替代下載。
4. 分開命名「相簿詳細頁」與「單張照片檢視器」，建立入口 precedence。
5. 在既有 B08 增加負向子案例：
   - B08-P1：app-bound 看不到、桌面 popup 可見；只能使用新鮮 mapping，不得再開 `⋯`，Save All 一次。
   - B08-P2：所有允許來源都看不到 popup；停止 Save All，不得要求重新授權或改走替代下載。
   - B08-P3：Save All 不唯一、鄰項重疊或 mapping 不可證明；停止該輸入。
   - B08-P4：點擊後沒有 chooser／progress／明確錯誤；記 UNKNOWN 並查證，不得第二次點擊。
6. 證據欄位區分 `menu_open_inputs` 與 `save_all_dispatches`，不把選單開啟次數和 Save All 派送次數混為一談。
7. 不新增 controller／CLI／授權框架。若要硬性阻止任意替代路徑，需另立平台層 popup 觀察／輸入控制 capability 工作，不能靠 Markdown 假裝硬保證。

## 相關版本

- Product candidate under review：`a33fed16571aeb95daaa0a20af4672672198fd6e`
- Draft PR：[#43](https://github.com/s9008129/Line_backup/pull/43)
- Root-cause Issue：[#44](https://github.com/s9008129/Line_backup/issues/44)
- Existing CUA window-binding / popup geometry issue：[#22](https://github.com/s9008129/Line_backup/issues/22)

## 狀態

```text
PRIMARY_OUTCOME_STATUS: ROOT_CAUSE_DOCUMENTED
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: NOT_RUN_FOR_ROOT_CAUSE_REMEDIATION
REQUIRED_VERIFICATION_STATUS: PENDING_PLANNER_SCOPE
INDEPENDENT_ACCEPTANCE_STATUS: NOT_APPLICABLE_TO_ANALYSIS_DOC
TASK_CLOSURE_STATUS: PENDING_PLANNER_HANDOFF
```
