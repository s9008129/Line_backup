# 新對話用 /goal（macOS 內建 Vision 取代 tesseract ＋ AI Agent 自主自動化測試）

使用方法：在**新對話**貼上下面整段（含 `/goal` 那一行）。它就是啟動指令；真正的細節全部在
`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff-vision-agent-2026-09-17.md`（H3.0）。
本檔是 H3.0 的搭配指令；上一代的 `GOAL-next-conversation.md`＋`handoff.md`（H2.1）是歷史紀錄，不要拿來當本輪輸入。

---

```text
/goal

【必讀】先把這份檔案完整讀完，再開始任何動作：
/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff-vision-agent-2026-09-17.md
它是本輪唯一的啟動交接文件（H3.0，2026-09-17）。裡面有：兩個目標、現況 SHA 快照、Vision 實測證據、
helper 原始碼、凍結工具盤點、路線待決事項、AI Agent 測試規格（C1–C5）、硬邊界與禁令、建議流程。
不要憑記憶、舊對話或舊版 handoff 推測。

【任務】兩個目標（缺一不可）：
一、把正式驗證鏈的 OCR 讀取器，由 tesseract 換成 macOS 內建 Vision（VNRecognizeTextRequest）。
    「正式」＝ evidence/20260916-route/tools/ 下三個 v3 工具實際使用的讀取器。這是語意變更：
    必須走完整流程（Rev21 規劃 → fresh 雙複審 → 重編 task handoff → fresh 實作 → 獨立驗收），
    不得以「小修改」直接改工具、不得臨場放寬任何 fail-closed 規則。
二、建立一個「AI Agent 自主自動化測試」，用可重跑、append-only 的證據證明 Vision 讀取器有效、
    且能解決目前的卡點（attempt-05 的「57 被 tesseract 讀成 75」→ TARGET_MISMATCH）。
    測試準則以 handoff 的 C1–C5 為起點（全部離線、零 GUI 輸入）；正式接受語意由 Rev21 定義。
    自主迴圈有界：失敗累計 5 次即停、記證、通知我介入；禁止長時間重試。

【範圍】只做一個相簿：LINE app jp.naver.line.mac、群組「旻謙允禎成長日記」（禎＝U+798E）、
相簿「2024/05/13～05/17」、預期 57 張。目的地
/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57（已確認 57 檔）
為唯讀；57 張永不重下載、永不刪改。正式 config／state／run-log 一律唯讀。

【硬性禁令（違反即停止並通知）】
- 零對話圖片：影像只落 /tmp（或工作目錄）供程式讀；對話與證據只出現路徑與 SHA-256。
  （本流程曾在對話爆 60 張圖片上限，ref 05ffef68-274a-4707-9db7-62f0c4c47ff8。）
- 所有 GUI 輸入 at-most-once、零重試；非明確 AFFIRMATIVE 授權視同未授權。
- 永不點選任何選單項目（特別點名「Save All 儲存全部」）；不碰 chooser；不送鍵盤；不做 AX 寫入。
- 不得使用歷史座標當輸入依據；一律由現幀推導。
- 凍結 verdict 不因補充證據翻案；「補充證據」≠「語意變更」。
- 禎（U+798E）與楨（U+6968）永不合并/正規化。
- 不新增第三方依賴；不寫正式 state/config/run-log；不覆寫任何過往 evidence（append-only）。

【路線待決（不得自行動作）】handoff §7：attempt-05 停在 STOPPED_AT_S5_TARGET_MISMATCH，
run-ledger SHA 17b17203…、CLOSED_AFTER_INPUT_1、owner_decision_required=true。
相簿卡輸入已耗 1/1；⋮ 未送且前置未成立。選項：(A) 明示 ROUTE_NOT_NEEDED 結案；
(B) 新 revision＋新一次性 gate 授權「⋮ 只觀察一次」。我還沒選——先問我，不要自己做。

【流程（依 harness CRITICAL）】
Phase 0 唯讀基線：git status；重算 handoff §3 全部 SHA；重建 Vision helper（swiftc）並跑 C1/C3/C5
  離線 sanity（零輸入、零 UI）。
Stage 01 規劃：在同一 TASK_ID（T20260916-0102-01-line-backup-acceptance）建立 Rev21：
  Goal Contract（CORE＝Vision 替換＋agent 測試；SUPPORTING/BEST_EFFORT 明確標；gating/門檻/
  fail-closed/自測更新策略）；不得擴大範圍。
Stage 02 獨立複審：fresh context 雙複審（append-only review/attempt-NN/）直到 PLAN_APPROVED。
Stage 03 交接重編：依核准 Rev21 重編 task handoff（舊版先封存），記 revision/hash。
Stage 04 fresh 實作：改 reader、更新自測（現 13 cases @ selftest/v3/selftest-summary.json
  17840e91…）、跑 C1–C5、產出 append-only 證據（JSON＋SHA）。
Stage 05 獨立驗收：依計畫的 acceptance 設定執行；離線重跑屬 integration/contract 等級，
  不得冒充 live E2E。

【回報與流程慣例】對外回報最白話；三個結果分開（①本相簿資料 ②可重用能力 ③整體結案）；
每次階段完成→深度梳理＋繁體中文四段式 git commit（意圖／做了什麼／驗證／下一步建議）並實際
add＋commit。

【升級條件（遇到即停、記證、通知）】任何語意變更超出 Rev21 授權；自證/污染疑慮；
同根因連續 2 次失敗；需要新的 GUI 授權；任何會動到 57 張或正式資料的念頭；
失敗累計 5 次。
```
