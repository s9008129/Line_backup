# 新對話用 /goal（Rev24：修正 ⋮ 定位規則 ＋ AI Agent 自主自動化複驗）

使用方法：在**新對話**貼上下面整段（含 `/goal` 那一行）。它就是啟動指令；真正的細節全部在
`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff-rev24-agent-autonomous-2026-09-18.md`（H4.0）。
本檔是 H4.0 的搭配指令；上一代 `GOAL-vision-agent-next-conversation.md`＋`handoff-vision-agent-2026-09-17.md`（H3.0）是歷史紀錄，不要拿來當本輪輸入。

本檔搭配檔案（指紋）：
- 啟動交接文件：`handoff-rev24-agent-autonomous-2026-09-18.md`，SHA-256 `ba870b4bdc574aec5406d9820adf906ffc13962e3e999100628eb965e91b7046`
- 本輪計畫：`.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24），SHA-256 `40eb01980c7e11f96b4b12c2db8f53728852f1ab6ca452dfb5e865fd5435a003`

---

```text
/goal

【必讀】先把這份檔案完整讀完，再開始任何動作：
/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff-rev24-agent-autonomous-2026-09-18.md
它是本輪唯一的啟動交接文件（H4.0，2026-09-18）。裡面有：背景與三層邏輯、現況 SHA 快照、
attempt-06 失敗的根因（⋮ 定位規則的位置假設錯，連帶自測 fixture 有盲點）、Rev24 的變更範圍、
gate-5 一次性授權、S1–S11 runbook 與停止規則、硬邊界與禁令、升級條件。
再讀本輪計畫 `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24，狀態 CANDIDATE）
作為工作契約；不要憑記憶、舊對話或舊版 handoff 推測。

背景（一句話）：上一輪 route attempt-06 在真實畫面成功開啟相簿後，⋮ 定位工具 v4 回報
NO_ELLIPSIS_FOUND——v4 的位置規則假設「⋮ 落在驗證標題同一列帶」內，但真實 LINE UI 把相簿內 ⋮
放在標題列「上方」（實測 middle dot (304.5, 49.5)；標題 bbox [15,83,204,111]、band y0=77 →
分類為 above_album_title_band，不具資格）；⋮ 未送出、零副作用。owner 其後選 B：用新計畫（Rev24）
＋新的一次性授權，把同一條「⋮ 只觀察」路線再驗一次（改用修正版定位規則）。

【任務】單一波次、全自主，依序完成六件事（缺一不可）：
① Phase 0 唯讀基線（零 GUI）：`git status`（工作區須乾淨）；核對 H4.0 的 SHA 清單——
   v4 四工具 `vision_reader.py` 22a4e9ef…／`locate_album_card.py` bb52aff1…／
   `verify_album_open.py` ffa82aed…／`locate_album_ellipsis.py` b77e3d51…（完整雜湊以 H4.0 為準）、
   v4 自測 summary 5ad2be10…（16 cases／0 failed）、v3 自測 17840e91…（13/13）、
   detector 6ae9c250…、detector 自測 db091703…、gate-4 e32ccd88…、
   attempt-06 FINAL ledger 906c1433… 及其 parent 17b17203…、
   已入庫 frames `route5r_frame_post.jpg` 4cb8a6b4…／`route5r_frame_pre.jpg` 3d926e7d…、
   baseline ab6747f2…（57 檔／17,924,900 B）、v1.1 record a8c10551…、`result.md` bd00d9c9…、
   `execution-rev22.md` c9b59080…、task `handoff.md` 19c9c6d3…；目的地 57 檔；
   正式 config／state／run-log 唯讀。任何雜湊或檔數不符 → 停、記證、通知 owner。
② Stage 02 獨立雙複審：對 Rev24 的精確 hash 跑 `review/attempt-36/`、`review/attempt-37/`
   （append-only、fresh context）。兩份都必須 `PLAN_APPROVED`；否則修訂 → `PLAN_REVISION 25`
   → 新的 attempts，重新複審到通過為止（不得自我核准、不得跳過）。
③ Stage 03 交接重編：先把現行 task `handoff.md`（19c9c6d3…）封存為
   `handoff-history/handoff-plan-r23-<YYYYMMDD>-<HHMMSS>.md`，再依 Rev24 重編 `handoff.md`。
④ Stage 04 fresh 實作（零 GUI）：建立 `evidence/20260916-route/tools/v5/`
   （`vision_reader.py`／`locate_album_card.py`／`verify_album_open.py` 為 v4 位元相同副本；
   `locate_album_ellipsis.py` 為修正版；README 記錄修正點與實幀證據）
   ＋ `evidence/20260916-route/tools/selftest/v5/`（自測 runner＋summary，約 20 cases、0 failed）。
   離線重播必須證明兩件事：
   (a) v5 對已入庫 post frame（4cb8a6b4…）必須 `ELIGIBLE`、`ellipsis_dots` 為
       [[304.5,44.0],[304.5,49.5],[304.5,55.0]]、`click_point` 為 [304,50]；
   (b) v4 位元對同一幀仍必須 `NO_ELLIPSIS_FOUND`（凍結基線不得翻案）。
   然後在**任何 GUI 輸入之前**凍結並 commit：gate-5（鏡射 gate-4 的 17-key 授權 schema，
   綁 owner 決策＋Rev24 hash＋reviews 36/37）、`evidence/20260916-route/attempt-07/route-runbook.md`、
   `attempt-07/run-ledger.json`（parent 為 906c1433…）。gate-5 未凍結前，一律不得有任何輸入。
⑤ 路線複驗（本波唯一 GUI）：**route attempt-07**，依 runbook S1–S11 執行一次；
   S3／S5 沿用 v4、S6 改用 v5；最多兩個輸入（相簿卡恰 1 次左鍵、⋮ 恰 1 次左鍵），
   零重試、零選單點擊。任何非 `ELIGIBLE`／非 `AFFIRMATIVE` 一律 fail-closed：停、記證、通知 owner，
   不自動分支、不換座標、不換路徑。點完輸入 #2 後於約 4 秒窗口內完成觀察。
⑥ Stage 05 獨立驗收：`e2e/attempt-08/`（append-only）重算 attempt-07 證據、重跑 v5 離線重播、
   核 §24.5 closure tuple 與不可變性；最後依閉幕角色寫 `result.md`。

【範圍】LINE `jp.naver.line.mac`、群組「旻謙允禎成長日記」（禎＝U+798E）、相簿「2024/05/13～05/17」、
預期 57 張。目的地 `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`
唯讀；57 張永不重下載、永不刪改。正式 config
`/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json`
與 state／run-log 一律唯讀。不得擴大範圍。

【硬性禁令（違反即停止並通知）】
- 零對話圖片：影像只落 `/tmp` 或 repo evidence 供程式讀；對話與書面回報只出現路徑與 SHA-256。
- 所有 GUI 輸入 at-most-once、零重試、每次輸入恰 1 click；非明確 AFFIRMATIVE 授權視同未授權。
- 永不點選任何選單項目（特別點名「Save All 儲存全部」）；不碰 chooser；不送鍵盤；不做 AX 寫入。
- 不得用歷史座標當 live 輸入依據；`(304,50)` 僅供離線重播比對，live 一律由現幀推導。
- 禎（U+798E）與楨（U+6968）永不合并／正規化。
- append-only：v1–v4 工具、v3／v4 自測、route attempt-01..06 證據、`e2e/attempt-02..07`、
  gate 1–4、各 ledger、已封存 handoff、`result.md` 既有歷史，一律不得改寫或刪除。
- 不新增第三方依賴；不寫正式 state／config／run-log；不提交 `__pycache__`（python 一律加 `-B`）。
- 不得自我豁免任何 gate；不得自行擴權；不確定時停下來問，不要猜。

【授權與預算（已由 owner 給定，不需再問）】
一次性 GUI 授權來源＝ owner 逐字決策（transcript 綁定：session
`01a0af3c-6693-72b2-abf2-095a3317e9a4`，line 2427 / ordinal 2426，2026-09-18T00:06:40.115Z
（local 08:06:40），SHA-256 a600ac4c9af8e3e44327f4566f5388985a79658b43a6eeb435915edec6f9e9ec；
前置選項呈現為 line 2405 / ordinal 2404，SHA-256
14905585890cb158957b0e20e34abe6ec8bac26439c8b18187d3f58076ff8752）：
「B我要用一個新的計畫來取代原本的計畫。在新的計畫裡，我要你詳細且精準地撰寫。我等一下會重啟一個新的對話，
來進行接下來的 Agent 自主測試自動化作業。一樣我會用 Codex 的 goal 的方式，這個功能來進行 Agent 全自主的測試。
所以你等一下必須給我三樣東西：第一，你必須重新擬定這一個新的測試計畫。第二，你必須給我重新在新對話中
Agent 自主自動化測試的 goal 指令，以及要帶到新對話的相關交接 handoff 文件。總共是三件事情：第一，一個新的
測試計畫。第二，一個 goal 的精準指令，讓後續有新對話接手的 Agent 可以自主完成相關的測試。
第三，梳理我們現在討論的關鍵重點邏輯，以及在新對話中要交接的相關意圖與邏輯的 handoff 文件。」
（原文含換行；此處僅依版面折行，位元精確錨點為上方 SHA-256。）
一次性預算（鏡射 gate-4，fresh、UNSPENT）：album_card 1、navigation 1、ellipsis 1、retry 0、
menu_item 0、keyboard 0、app_acquisition 0、conversation_images 0、click_count_per_input 1、
observation windows ≤5、screen captures ≤5（輸入 #2 後約 4 秒內）。
若執行時畫面非指定狀態（LINE 不在相簿列表、目標卡不可見）→ 零輸入停止（可 resume），通知 owner；
若輸入 #1 已耗而輸入 #2 未獲成立條件，不得再重新授權。

【流程（依 harness CRITICAL）】
Phase 0 唯讀基線（見任務①）→ Stage 01 規劃＝Rev24（本輪已由前一個對話完成，無需重做；若審查
要求修訂則照②處理）→ Stage 02 獨立雙複審（attempts 36／37）→ Stage 03 交接重編（舊版先封存）
→ Stage 04 fresh 實作＋離線重播證明＋gate-5 凍結 → route attempt-07 一次性複驗（本波唯一 GUI）
→ Stage 05 獨立驗收 `e2e/attempt-08/` → 寫 `result.md`。
複審未過不得進 Stage 03；gate-5 未凍結不得有任何輸入；S6 不得 fallback 回 v4 規則。

【回報與流程慣例】對外回報一律最白話、給非技術主持人看得懂；三個結果分開講：
①本相簿資料 ②可重用能力（v5 定位與自測、可重跑證據）③整體結案。每次階段完成 →
深度梳理＋繁體中文四段式 git commit（意圖／做了什麼／驗證／下一步建議）並實際 add＋commit；
證據只出現路徑與 SHA-256，不出現圖片。

【升級條件（遇到即停、記證、通知）】
- 失敗累計 5 次即停；禁止長時間重試。
- 任何語意變更超出 Rev24 授權（含放寬 fail-closed、改閉幕語意、改 gate 效力）。
- 出現系統權限提示／授權視窗；或需要任何未授權動作（含任何未列預算的輸入）。
- 執行時 surface（LINE 畫面狀態）與 runbook 指定不符。
- 同一根因連續失敗、或證據顯示 v5 規則本身不可靠 → 停，回報 owner 決策。
```

---

備註（給 owner，開跑前）：開始前請把 LINE 停在相簿列表、目標卡可見；跑的時候請不要動滑鼠鍵盤；
跑完若選單還開著，請您自行關閉（agent 不會點任何選單項目）。
