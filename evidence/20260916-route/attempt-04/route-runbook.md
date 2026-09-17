# Route attempt-04 執行手冊 v2 — 第二次唯一一次 ⋮ 輸入（凍結於點擊之前）

凍結時間：2026-09-17T15:48+0800（本檔、`gate-2-authorization.json`、detector＋自測與
locator 皆於任何點擊之前凍結入庫；見本路徑的 git log）。
底稿：`evidence/20260916-route/attempt-03/route-runbook.md`（4,264 bytes，SHA-256
`4e5b865cb4f1d30623f9a0d7b619f7328bf1b721e9ba6fcf0963deaa0ada9cd1`），依 Rev19 §19.2
新增 screen-scope 探針、post 上限、AFFIRMATIVE 機器可觀測性與 NO_TARGET_ON_FRAME 即時通知。
Documented capability reference：`~/.codex/skills/line-album-backup/references/ui-procedure.md`
（27,769 bytes，SHA-256 `3a1bc29e7cc379ee41166387133125245f017c8f7a78799b27d920df09b75627`）。

## 授權與硬邊界（不可擴張、不可重試）

- 授權來源：第二次一次性授權（Rev19 §19.2）；gate 檔
  `evidence/20260916-route/attempt-04/gate-2-authorization.json`；使用者
  2026-09-17T06:59:40.847Z（session transcript line 5091）逐字「2.要，授權給你」。
- 本授權與 attempt-03 額度完全獨立：**不重置、不展延** attempt-03 已用完的 1 次。
- 允許的輸入總量：**恰好 1 次**「當前目標相簿卡」的 ⋮ 輸入（正常左鍵，click_count=1）
  → 立即 post 觀察 → 停止。
- 禁止（與 attempt-03 相同）：把 LINE 帶到前景、捲動/導航、
  `performSecondaryAction`/AXPress/AXUIElementPerformAction、鍵盤快捷鍵、點任何選單項、
  Save All、任何 chooser、任何 state/config/run-log 寫入。
- **零重試、零對話圖片**；點擊點必須由「當幀」推導並記錄推導證據，**禁止歷史座標**。
- 目標卡＝標題「2024/05/13～05/17」＋57 張（來源指紋 2024-05-13 / 2024-05-17 / 57）。
  可見非目標卡（例：2024/06/02~06/07、65張）的 ⋮ 嚴禁點擊；視窗頂端群組標題旁的 ⋮
  （群組選單）亦非目標。

## 前置（全部成立才可執行）

1. 使用者已把目標卡置於可見處；LINE 視窗保持標準視窗狀態。
2. 當幀可見目標卡標題與 ⋮；⋮ 輸入額度仍為 1（見 `run-ledger.json`：initial/final counts）。
3. `run-ledger.json` 已建立（`parent_ledger_sha256`＝attempt-03 run-ledger
   `77c4f86c21f61df08614d069d621816ede6a1465c794813b7977d2f784e5f2aa`）。
4. locator 與 detector 已凍結且自測通過：
   `locate_card_ellipsis.py` 8,943 B / `8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e`；
   `detect_menu_popup.py` 6,339 B / `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`
   （自測 ALL_OK：`evidence/20260916-route/tools/selftest/selftest-summary.json`
   `d8ffc1290347da13816f988adbe47656d42c60041ef701bf159b9d4c52a76557`）。

## 步驟

S1. **Binding read（零輸入）**
    - `getApp("jp.naver.line.mac", {emit:false})` → `getScreenshot({emit:false})` 將 bytes 寫到
      `/tmp/route_frame_pre.jpg`，記 bytes / 尺寸 / SHA-256；`getAXState({emit:false, disableDiffing:true})`
      記 SHA。全部寫入 `route-result.json` 的 target-binding / pre-observation 欄位（含擷取時間）。

S2. **Screen-scope 探針（恰一次；唯讀；不送輸入事件、無聲）**
    - `screencapture -x /tmp/route_screen_probe.png`（或等效唯讀螢幕擷取）。
    - 接受條件（全部成立）：exit 0、可解碼、且**凍結 locator 對「AX 視窗 bounds 裁切」在
      scale 2 或 scale 1 得到 ELIGIBLE**（證明影像含真實視窗內容）；記錄所採 scale 於
      `screen-probe.json`。
    - 否則 `screen_scope=UNAVAILABLE`（非致命），run 以 window-scoped 續行。
    - 若探針後觀察到**新的系統權限對話框** → 記 `PERMISSION_PROMPT_OBSERVED`、`SAFE_ABORT`、
      **不送 ⋮ 輸入**、停止。

S3. **定位（唯讀；不得以歷史座標跳過）**
    - `python3 evidence/20260916-route/tools/locate_card_ellipsis.py /tmp/route_frame_pre.jpg
      --expect-start 2024/05/13 --expect-end 2024/05/17
      --out evidence/20260916-route/attempt-04/ellipsis-locate.json`
    - 僅當 `verdict=ELIGIBLE`（exit 0）、`title.texts` 為目標日期、且 `click_point` 由當幀三點
      推導時才可續行；否則 SAFE_ABORT，不得點擊。
    - 人工複核：卡片張數應為 57（目視／OCR）；若明顯非 57 → 停止。

S4. **目標卡不在當幀**
    - 不送任何輸入：記 `NO_TARGET_ON_FRAME`；最多使用 **5 個唯讀觀察窗**；依使用者常駐指示
      **立即通知使用者**（不得長時間重試／迴圈）；停止。零重試。

S5. **唯一輸入**：`await line.click([x, y])`，`[x, y]`＝S3 的 `click_point`（正常左鍵）。除此之外
    不得有任何輸入。

S6. **立即 post 觀察（零輸入）**
    - `getScreenshot({emit:false})` → `/tmp/route_frame_post.jpg`（記 SHA/bytes）。
    - `getAXState({emit:false, disableDiffing:true})`（記 SHA；逐字轉錄選單文字/順序/bounds、新
      menu 元素 role/subrole/bounds）。
    - 當 `screen_scope=AVAILABLE`：於約 4 秒內做 **≤5 張** screen captures（`/tmp/route_screen_post_<n>.png`），
      每張記 timestamp / bytes / 尺寸 / SHA-256；**不加入人工延遲**；幀 bytes 不落庫，留 /tmp 供
      Stage 05 重跑凍結 detector。
    - 若出現非預期彈窗（開啟相簿、下載對話框等）→ 立即停止、不點任何東西、記錄現況。
    - 選單保持開啟即停（不按 Esc——按鍵也是輸入）；請使用者事後自行關閉。

S7. **判定（AFFIRMATIVE 僅認機器可觀測）**
    - AFFIRMATIVE ⇐ 新 AX menu 元素（role/subrole/bounds）**或**凍結 detector
      `evidence/20260916-route/tools/detect_menu_popup.py` 判定 `MENU_DETECTED`
      （新矩形區塊＋≥2 轉錄字串）；輸出存 `menu-analysis.json`。
    - OCR-only、人類目擊-only、或不完整擷取 → `UNKNOWN`，永不 AFFIRMATIVE。
    - owner/observer 目擊可逐字記於 `owner_action_requested`（supplementary），永不改變
      `route_status`。

S8. **停止並寫證**：`route-result.json`（attempt-03 schema；含 screen-probe 欄位）、
    `menu-analysis.json`、`screen-probe.json`（或明示 `screen_scope=UNAVAILABLE` 記錄）、
    `manifest.json`；更新 `run-ledger.json`（events / final_counts / route_result_sha256）；
    `route_status ∈ {AFFIRMATIVE, UNKNOWN, SAFE_ABORT}`；記 decision/reason/stop_reason；
    commit（四段式訊息）。

## 證據政策

- 幀不落庫（沿用 attempt-03 政策）：只記 bytes/尺寸/SHA-256 與轉錄結果；frames 留在 /tmp。
- locator 只定位、永不送輸入；detector 只比對影像、永不送輸入。
- **環境陷阱**：本環境 tesseract 讀不到 /tmp 下的圖檔（`Error in fopenReadStream`），detector
  以 stdin/stdout 模式執行 OCR（`tesseract - stdout … tsv`），不落暫存檔；詳見
  `evidence/20260916-route/tools/selftest/README.md`。
- 任何偏離本手冊的行為＝本次 run 無效；以 SAFE_ABORT 記錄並回報使用者。
