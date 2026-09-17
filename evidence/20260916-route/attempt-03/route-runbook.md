# Route attempt-03 執行手冊 — 唯一一次 ⋮ 輸入（凍結於點擊之前）

凍結時間：2026-09-17T11:58+0800（本檔與 locator 於任何點擊之前 commit；見本路徑的 git log）。
Documented capability reference：`~/.codex/skills/line-album-backup/references/ui-procedure.md`
（27,769 bytes，SHA-256 `3a1bc29e7cc379ee41166387133125245f017c8f7a78799b27d920df09b75627`）。

## 授權與硬邊界（不可擴張、不可重試）

- 授權來源：單一 human gate（Rev18 §Human gate；使用者 2026-09-17T09:09:49+0800 答「2.授權」）。
- 允許的輸入總量：**恰好 1 次**「當前目標相簿卡」的 ⋮ 輸入（正常左鍵點擊，click_count=1）→ 立即 post 觀察 → 停止。
- 禁止：把 LINE 帶到前景、捲動/導航、`performSecondaryAction`/AXPress/AXUIElementPerformAction、鍵盤快捷鍵、點選任何選單項、Save All、開啟 chooser、寫任何 state/config/run-log。
- 若該次輸入未達預期（例如選單未開、或開成別的畫面）：**不得重試**；本次 run 就以實際結果記錄（UNKNOWN/SAFE_ABORT），後續需新 gate／新 PLAN_REVISION。
- 目標卡＝標題「2024/05/13～05/17」＋57 張（來源指紋 2024-05-13 / 2024-05-17 / 57）。**禁止使用歷史座標**；點擊點必須由「當幀」推導並記錄推導證據。
- 可見非目標卡（例：2024/06/02~06/07、65張）的 ⋮ 嚴禁點擊；視窗頂端群組標題旁的 ⋮（群組選單）亦非目標。

## 前置（全部成立才可執行）

1. 使用者已把目標卡捲到可見並回報（或等效）；LINE 保持最前。
2. 當幀可見目標卡標題與 ⋮；⋮ 輸入額度仍為 1（見 `run-ledger.json`：initial/final counts）。

## 步驟

S1. **Binding read（零輸入）**
    - `getApp("jp.naver.line.mac", {emit:false})` → `getScreenshot({emit:false})` 將 bytes 寫到 `/tmp/route_frame_pre.jpg`，記 bytes / 尺寸 / SHA-256；`getAXState({emit:false, disableDiffing:true})` 記 SHA。
    - 全部寫入 `route-result.json` 的 target-binding / pre-observation 欄位（含擷取時間）。

S2. **定位（唯讀；不得以歷史座標跳過）**
    - `python3 evidence/20260916-route/tools/locate_card_ellipsis.py /tmp/route_frame_pre.jpg --expect-start 2024/05/13 --expect-end 2024/05/17 --out evidence/20260916-route/attempt-03/ellipsis-locate.json`
    - 僅當 `verdict=ELIGIBLE`（exit 0）、`title.texts` 為目標日期、且 `click_point` 由當幀三點推導時才可續行；否則 SAFE_ABORT，不得點擊。
    - 人工複核：卡片張數應為 57（目視/OCR）；若明顯非 57 → 停止。

S3. **唯一輸入**：`await line.click([x, y])`，`[x, y]`＝S2 的 `click_point`（正常左鍵）。除此之外不得有任何輸入。

S4. **立即 post 觀察（零輸入）**：`getScreenshot({emit:false})` → `/tmp/route_frame_post.jpg`（記 SHA/bytes）；`getAXState({emit:false, disableDiffing:true})`（記 SHA）。逐字轉錄選單文字/順序/bounds（AX 可行時）；若出現非預期彈窗（開啟相簿、下載對話框等）→ 立即停止、不點任何東西、記錄現況。
    備註：選單保持開啟即停（不按 Esc——按鍵也是輸入）；請使用者事後自行關閉。

S5. **停止並寫證**：`route-result.json`（schema 依 plan §New run ledger and route-result schema：documented_capability_ref、target-binding/pre/post SHAs、candidate text/role/subrole/bounds/owner、same-item correlation、`save_all_click_count=0`、`menu_item_click_count=0`、`chooser_state`、`backup_state_write_count=0`、`route_status=AFFIRMATIVE|UNKNOWN|SAFE_ABORT`、decision/reason）＋更新 `run-ledger.json`（events/final_counts/route_result_sha256）＋manifest；commit（四段式訊息）。

## 證據政策

- 幀不落庫（沿用 attempt-03 政策）：只記 bytes/尺寸/SHA-256 與轉錄結果；OCR 僅輔助，AFFIRMATIVE 必須來自當幀可重述的具體觀察。
- locator 只定位、永不送輸入；自測證據見 `evidence/20260916-route/tools/selftest/`（凍結版 SHA-256 `8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e`）。
- 任何偏離本手冊的行為＝本次 run 無效；以 SAFE_ABORT 記錄並回報使用者。
