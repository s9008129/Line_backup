# HANDOFF H4.0 — Rev24 修正版路線複驗：Agent 全自主測試自動化啟動交接

- 版本：H4.0（2026-09-18，Asia/Taipei）
- 用途：**下一個新對話（Codex `/goal` 全自主測試）的唯一啟動交接文件**。新對話的 agent 必須先讀 `GOAL-rev24-next-conversation.md`，再完整讀完本檔，然後讀 `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24），才開始任何動作。
- 搭配指令：`GOAL-rev24-next-conversation.md`（同 repo 根目錄；是要貼進新對話的 `/goal` 指令；其中內嵌本檔定稿 SHA-256（已填入）。引用方向：GOAL → 本檔，單向）。
- 上位依據：`.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md` **Rev24**（`PLAN_REVISION: 24`、`PLAN_STATUS: CANDIDATE`；取代 Rev23）。語意權威為計畫之 §24.1–§24.9；本檔為啟動交接的可讀版，遇疑義以計畫為準。
- 前一代交接：`handoff-vision-agent-2026-09-17.md`（H3.0）＝歷史紀錄，不再是本輪輸入；task 內 `handoff.md`（Rev23 綁定、`19c9c6d3…`）將於 Stage 03 先封存為 `handoff-history/handoff-plan-r23-<YYYYMMDD>-<HHMMSS>.md`，再重編為 Rev24 版。
- 撰寫時 repo 狀態：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`，branch `master`，HEAD `29bdf53`（素材基準時點；本輪交付物由主流程統一 commit）。
- 語言：繁體中文（技術名詞保留英文）。寫給兩種讀者：接手 agent（全檔）與非技術主持人（每節「白話」框）。

---

## 0. 白話總結（給非技術主持人）

上一輪的測試不是功能壞了：相簿有成功打開、57 張備份和所有紀錄都沒被動到；失敗點只是「程式找 ⋮（三點按鈕）的位置規則」跟 LINE 真實畫面差了一格——程式只在標題列裡找，LINE 卻把 ⋮ 畫在標題列上方，所以程式找不到就安全停住、沒有亂點。修正版規則已經用「上一次那張真實畫面」離線證明：新規則找得到、舊規則找不到，問題與修法都明確。新對話會做一輪「修正版」正式測試：先讓兩份獨立審查通過新計畫、再把一次性授權凍結起來，才做那一次真機驗證（點開相簿、再點一次 ⋮ 只為看選單有沒有出現；全程不點任何選單項目）。您之前問的「多輪＋容錯」對一半：可以多輪、可以反覆驗證的是「測試與證據」那一層；真正會點畫面的那一層刻意只准一次、不准重試，因為點錯收不回來；產品本身的下載重試/續傳則是另一層的容錯。您唯一要做的：開跑前把 LINE 停在相簿列表、目標相簿（57 張）可見；執行時不要動滑鼠鍵盤；不論結果好壞，都會留下完整紀錄並誠實回報。

---

## 1. 任務總覽與本輪三份交付物

### 1.1 任務（一句話）

以修正版 ⋮ 定位規則（v5）完成一次受控、一次性授權的真機路線複驗（route attempt-07），為「打開目標相簿（`2024/05/13～05/17`）→ 相簿層 ⋮ 可達性」補上機器可觀察證據；無論正／負結果，都依既有 closure 語意誠實收尾。

### 1.2 三份交付物與引用方向

| # | 交付物 | 角色 |
|---|---|---|
| ① | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24，CANDIDATE） | 新的測試計畫：取代 Rev23；定義 v5 規則、gate-5、route attempt-07 與驗收矩陣；須通過 `review/attempt-36`、`review/attempt-37` |
| ② | `GOAL-rev24-next-conversation.md`（repo 根目錄） | 要貼進新對話的 `/goal` 指令；內嵌本檔定稿 SHA-256（單向；已填入） |
| ③ | `handoff-rev24-agent-autonomous-2026-09-18.md`（本檔，repo 根目錄） | 啟動交接：現況快照、三層邏輯、owner 決策、Rev24 變更、管線、禁令與升級條件 |

引用方向：GOAL → 本檔（GOAL 內嵌本檔 SHA-256）；本檔 → Rev24 計畫與 owner 決策紀錄（本檔於 §2.3 放定稿值）；本檔**不內嵌** GOAL 的 hash。

### 1.3 新對話啟動順序

1. 讀 `GOAL-rev24-next-conversation.md`（啟動指令）。
2. 讀本檔（H4.0）全檔。
3. 讀 `plan.md`（Rev24）與本檔點名的凍結證據（§11 全表即 Phase 0 核對清單）。
4. 依 §7 管線執行；Stage 01（規劃）已在上一對話完成，本輪不需重做。

### 1.4 白話

> 三份東西分工：①新計畫（規格書）②可直接貼的啟動指令③本交接（為什麼、怎麼做、不准做什麼）。新對話先讀②、再讀③、再照①的規格執行；一切以檔案內容為準，不靠記憶或舊對話。

---

## 2. 現況快照（權威路徑與 SHA-256）

### 2.1 基準與狀態

- repo：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；branch `master`；HEAD `29bdf53`（素材基準時點）。
- Task：`T20260916-0102-01-line-backup-acceptance`；task 目錄：`.agent/tasks/T20260916-0102-01-line-backup-acceptance/`（harness CRITICAL class）。
- 現行計畫：`plan.md` 已更新為 **Rev24**（`PLAN_REVISION: 24`、`PLAN_STATUS: CANDIDATE`），取代 Rev23；**Rev24 尚無任何複審**，下一號為 `review/attempt-36`、`review/attempt-37`。
- Rev23（已被複審核准的歷史版本）：`4337e2b5c105901ce7c56956ecea5469894df2d2a29f099068c979584c71b6b2`（2,093 行 / 284,897 bytes）；由 `review/attempt-34`（`21c4bbb5…`）與 `review/attempt-35`（`975142c3…`）雙雙 `PLAN_APPROVED`。
- 目前驗收狀態（未變）：`CORE_ACCEPTANCE_BLOCKED`（`result.md` `bd00d9c9…`）；唯一 scoped blocker＝`CUA_ROUTE_DECISION`（owner 保留；owner 已回覆 B，本輪即為修正版一次性複驗）。
- owner 決策紀錄（本輪建立）：`evidence/20260918-owner-decisions/owner-decisions-rev24.json`；其 SHA-256 見 §2.3 定稿值。
- 流水號：route attempt-01..06 已存在，本輪＝`evidence/20260916-route/attempt-07/`；e2e attempt-02..07 已存在，本輪 Stage 05＝`.agent/tasks/T20260916-0102-01-line-backup-acceptance/e2e/attempt-08/`。

### 2.2 關鍵凍結錨點（節錄；全表見 §11）

| 項目 | 路徑 | SHA-256 |
|---|---|---|
| attempt-06 FINAL ledger（attempt-07 ledger 的 parent） | `evidence/20260916-route/attempt-06/run-ledger.json` | `906c1433…` |
| gate-4 授權書（gate-5 的鏡射範本） | `evidence/20260916-route/attempt-06/gate-4-authorization.json` | `e32ccd88…` |
| attempt-06 post 幀（離線重播錨點） | `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` | `4cb8a6b4…` |
| v4 自測 summary（16 cases / 0 failed） | `evidence/20260916-route/tools/selftest/v4/selftest-summary.json` | `5ad2be10…` |
| v4 定位工具（本輪修正對象） | `evidence/20260916-route/tools/v4/locate_album_ellipsis.py` | `b77e3d51…` |
| 冷凍偵測器（S10） | `evidence/20260916-route/tools/detect_menu_popup.py` | `6ae9c250…` |
| baseline（57 檔 / 17,924,900 bytes） | `evidence/20260916-baseline/attempt-01/baseline-pre.json` | `ab6747f2…` |
| 現行 task handoff（Stage 03 先封存） | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/handoff.md` | `19c9c6d3…` |

（表內 `…` 為縮寫索引；§11 附錄提供完整值。）

### 2.3 本輪產物的 SHA-256（已定稿）

下列兩值已於 2026-09-18 由主流程在對應產物定稿後填入，即 gate-5 綁定用的定稿 SHA-256；不得把任何其他舊值或中間值當作真值使用。

- Rev24 計畫（`plan.md`）定稿值：
40eb01980c7e11f96b4b12c2db8f53728852f1ab6ca452dfb5e865fd5435a003
- owner 決策紀錄（`evidence/20260918-owner-decisions/owner-decisions-rev24.json`）定稿值：
be1f5173de9219bfba2a547223542dde17c6e6a23f653274122f0d8dcbe2360d

### 2.4 白話

> 舊計畫、舊紀錄、上一輪的失敗畫面都完整保留。本節兩個空位，是等「新計畫」與「您的決策紀錄」完全定稿後填入數位指紋，讓新對話能確認它拿到的是同一份、沒被偷改過。

---

## 3. 三層關鍵邏輯（owner 特別要求）

### 3.1 owner 的提問（逐字）

> 「所以我們現在的新計畫可以說是比較有彈性，而且不是只有測一次。然後還有什麼不一樣嗎？我的理解這樣對嗎？是不是可以做多輪的測試，然後有做一些容錯機制在裡頭，是這樣嗎？」（transcript line 2291 / ordinal 2290；243 bytes；SHA-256 `3fc89cbc9388a176fd92f47a00e0cae7bde24d51286a084584fa73da16d0ae8e`）
> 「所以我現在還要決策什麼？你用白話跟我說。」（transcript line 2365 / ordinal 2364；60 bytes；SHA-256 `2e729d0339bc1574d9869b7054da586259f7dde584fb6ef85c28135796850364`）

### 3.2 ① GUI 執行層（真機操作）＝刻意「零容錯」

- 規則：一次到位（at-most-once）、零重試、零替代座標、零選單項目點擊、fail-closed（找不到就停）。
- 為什麼：真機點擊**不可逆**。點了 ⋮ 可能彈出選單；若誤觸任何選單項目（尤其 Save All），副作用在外部應用上、**無法回收**。所以這層不是「不夠聰明」，是安全設計：寧可停，不可猜。
- 每個真機輸入都要：新修訂＋新 gate（事前凍結的一次性授權）＋單次單擊指定座標；輸入送出後該輪即封閉，不得重送。
- resume 規則：**零輸入**停止（還沒送過任何輸入）可視為可重排的 resume；一旦送出任何輸入，該輪結束，只能以「全新修訂＋全新 gate」開新嘗試（本輪 attempt-07 正是依此從 attempt-06 的 `CLOSED_AFTER_INPUT_1` 之後開啟）。
- 本輪真機授權（恰兩個輸入）：輸入#1＝點目標卡片一次（S4）；輸入#2＝點 ⋮ 一次（S8，只為讓選單出現並唯讀觀察 S9–S10）。menu_item=0、keyboard=0、retry=0。

### 3.3 ② 測試／證據層＝真正的「多輪＋容錯」在這裡

- 多輪：route attempt-01..06 每一輪都有完整 ledger／幀／JSON／雜湊；失敗**不被覆寫**，而是成為下一輪的輸入（append-only）。
- 離線可重跑：同一張已入庫畫面＋同一支工具＝零 GUI 重複驗證規則。規劃期已用 `/tmp` prototype（零 GUI、未入庫）證明：v5 規則對已入庫 post 幀 `4cb8a6b4…` 得 `ELIGIBLE`（dots `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]`、`click_point [304,50]`）；v4 位元同幀仍為 `NO_ELLIPSIS_FOUND`。
- 所以在這層，「重跑／重試」是允許且鼓勵的：它零副作用、可重複、可審計——這才是您所說「容錯」真正的落點。
- 但每輪結果不可變：新證據＝新一輪目錄，不修改舊檔。

### 3.4 ③ 產品層（交付的 CLI）＝下載容錯，與①②不同層

- 產品（line_backup CLI）在下載層有容錯設計：重試、續傳、冪等、拒絕重複下載等。
- 這是**產品行為**，與真機操作層（①）、測試證據層（②）完全不同層；不可把「產品有重試」誤解成「agent 可以重試點擊」，也不可把「agent 零容錯」誤解成「產品很脆弱」。
- 本輪不修改、不重驗產品的下載容錯（範圍見 §6／§8）；本輪只做路線複驗。

### 3.5 白話

> 用「手、實驗紀錄、產品」三分法：**① 手**——只准點一次、不准亂動，因為點錯收不回來；**② 實驗紀錄**——可以一直重做分析、重跑驗證，而且每輪紀錄不能改，這是「多輪＋容錯」真正的地方；**③ 產品**——本身有下載重試/續傳等容錯。您原本的理解「多輪＋容錯」對了一半：對在②；①是刻意沒有、③是產品自己的。

---

## 4. 上一輪（route attempt-06）為什麼失敗

### 4.1 一句話

位置規則與真實 UI 幾何不符：v4 只在「標題列內」找 ⋮，但 LINE 真實畫面把相簿層 ⋮ 放在標題列**上方** → 找不到 → fail-closed 停止；⋮ 未送出、零副作用。

### 4.2 技術細節

- v4 規則（`evidence/20260916-route/tools/v4/locate_album_ellipsis.py`，`b77e3d51…`）：合格區＝由 S5 標題 bbox 導出的標題列帶 `band = {x0: tx1+2, x1: width-1, y0: max(0, ty0-6), y1: min(height-1, ty1+10)}`；形狀檢查：三點縱列、間距 3–10 px、同欄 ±3、span ≤24；常數：delta 45、flat-tol 25、flat-fraction 0.6、max-area 16、max-side 5、text-margin 6。Exit codes：0 `ELIGIBLE`、2 `TARGET_TITLE_NOT_FOUND`、3 `NO_ELLIPSIS_FOUND`、4 `AMBIGUOUS_ELLIPSIS`、5 `GROUP_LEVEL_ONLY`、6 `BAD_FRAME`。
- 真實幀（327×643；attempt-06 post 幀）：標題 bbox `[15,83,204,111]` → v4 band x∈[206,326]、y∈[77,121]。畫面唯一的非文字 ⋮ 候選：三點 `(304.5,44.0)/(304.5,49.5)/(304.5,55.0)`（幾何完美）；middle y=49.5 < 77 → 分類 `above_album_title_band` → 不合格。其餘 5 組三點候選都在文字區（`57張照片`、`2024.05.18` 的 glyph 列）→ `inside_text`。
- 結果：exit 3 `NO_ELLIPSIS_FOUND`（`evidence/20260916-route/attempt-06/album-ellipsis-locate.json`）；S6 fail-closed 停止；⋮ **未送出**、零副作用；attempt-06 FINAL ledger `906c1433…`、state `CLOSED_AFTER_INPUT_1`（輸入#1＝卡片點擊已用；輸入#2 未用）。
- 自測為什麼沒抓到：v4 自測（`evidence/20260916-route/tools/selftest/v4/`，16 cases / 0 failed，`5ad2be10…`）的 album fixture 把控制點 ⋮ 畫在合成標題列**內**（`album_frame()`；dots cy≈47、標題 y≈32）→ 合成 band 包含 dots → 16/16 全過；真實 UI 在標題列**上方** → 規則失準。**盲點在 fixture，不在 reader**。
- 邊界事實：reader（Vision）本身正常——S5 已通過（≥5% 像素差＋標題＋張數 57）；失敗發生在 S6 的**位置規則**。

### 4.3 白話

> 程式以為 ⋮ 在「標題那一行裡面」，但 LINE 真實畫面把它畫在標題的「上一行」。測試用的假畫面把 ⋮ 畫在標題行內，所以 16 題全對；真實畫面上，程式找不到 ⋮、就停下來——沒有亂點、沒有任何多餘動作，這是它該有的行為，只是規則要修。

---

## 5. owner 決策與授權（逐字、locators、SHA-256）

### 5.1 來源與方法

- transcript 檔：`/Users/hsiaojohnny/.codex/sessions/2026/09/17/rollout-2026-09-17T19-59-26-01a0af3c-6693-72b2-abf2-095a3317e9a4.jsonl`
- session id：`01a0af3c-6693-72b2-abf2-095a3317e9a4`；owner 訊息＝`response_item.payload.role == "user"`、文字在 `payload.content[0].text`；下表 SHA-256 以該欄位 UTF-8 bytes 計算（`shasum -a 256`）。
- 行號為 JSONL 檔案行號；ordinal 為 thread 內序號（observed `ordinal = line − 1`）。

| 角色 | line / ordinal | 時間 UTC / local（+0800） | bytes | SHA-256 |
|---|---|---|---|---|
| assistant：A/B 選項呈現 | 2405 / 2404 | 2026-09-18T00:02:44.793Z / 08:02:44.793 | 1,931 | `14905585890cb158957b0e20e34abe6ec8bac26439c8b18187d3f58076ff8752` |
| user：草稿 #1（後被中斷） | 2412 / 2411 | 2026-09-18T00:06:14.768Z / 08:06:14.768 | 304 | `caf2f7d789c3429fa9bc4e956ea1da6782c50afd4f6983ce952e565160ca4038` |
| user：草稿 #2（後被中斷） | 2420 / 2419 | 2026-09-18T00:06:20.436Z / 08:06:20.436 | 430 | `a8caf86dc8e92338777157dae54904a689525a8fe653f1f7b08f3311ca7383b9` |
| user：**最終決策** | 2427 / 2426 | 2026-09-18T00:06:40.115Z / 08:06:40.115 | 882 | `a600ac4c9af8e3e44327f4566f5388985a79658b43a6eeb435915edec6f9e9ec` |

### 5.2 A/B 選項呈現（line 2405；1,931 bytes；逐字）

```text
**你現在只剩「一件事」要決定：「相簿內的 ⋮」這條驗證要怎麼收尾（A 或 B）。**

先講清楚現況：你的照片、備份（57 檔）沒被動過；工具（新版 Vision 眼睛）已完成並通過獨立驗收；紀錄都在。唯一還擋著「正式結案」的，就是「要不要拿到『機器親自確認 ⋮ 找得到』這項證據」——因為這輪它被自己的位置規則擋下，沒點成功。

**選項 A — 收掉（記成「這條路不需要」）**
- 用你的正式決定關掉這個卡點，就能走結案；相簿資料那項結果也能通過（來源已經用更正版紀錄確認）。
- 不做任何新動作：不再打開相簿、不需新授權、不碰畫面、不碰任何檔案。
- 紀錄會誠實保留「⋮ 沒有被機器驗證過」這點不確定，不會假裝做過。
- 未來若真要走到「儲存全部」流程，那時本來就得重新建立這條路線＋重新拿授權——所以 A 不是丟掉功能，只是現在不為「多一份證據」再跑一輪。

**選項 B — 再驗一次**
- 會先做一份新修訂計畫＋重新規劃＋全新獨立審查，然後你再給一次新的「只觀察」授權，才會再打開相簿看一眼 ⋮（全程不點任何選單項目）。
- 代價：多花一輪時間、會再打開一次相簿；同一套畫面設定下很可能停在同一條位置規則，不保證有進展；新授權一樣一次性、不重試。
- 若這次看到機器肯定的結果 → 一樣能結案。

**你只需要問自己一句**：「『機器親自確認 ⋮』這項證據，現在值得再花一輪去拿嗎？」
- 值得 → 回 **B**
- 不值得／現在不需要 → 回 **A**

在我收到你的回覆前，不會有任何動作；除了這一件事，沒有其他事在等你決定。

附註：目前沒有「已存在的新計畫」在跑——只有你選 B，才會去做那份新修訂。
```

### 5.3 最終決策（line 2427；882 bytes；逐字，含換行與縮排）

```text
B我要用一個新的計畫來取代原本的計畫。在新的計畫裡，我要你詳細且精準地撰寫。我等一下會重啟一個新的對話，來進行接下來的 Agent 自主測試自動化作業。一樣我會用
  Codex 的 goal 的方式，這個功能來進行 Agent 全自主的測試。
所以你等一下必須給我三樣東西：
  第一，你必須重新擬定這一個新的測試計畫。
  第二，你必須給我重新在新對話中 Agent 自主自動化測試的 goal 指令，以及要帶到新對話的相關交接 handoff 文件。
  總共是三件事情：
  第一，一個新的測試計畫。
  第二，一個 goal 的精準指令，讓後續有新對話接手的 Agent 可以自主完成相關的測試。


第三，梳理我們現在討論的關鍵重點邏輯，以及在新對話中要交接的相關意圖與邏輯的 handoff 文件。
```

### 5.4 兩則被中斷草稿（非授權來源）

**草稿 #1（line 2412；304 bytes；其後 line 2415 有 `turn_aborted`，turn `01a0b1d5-cfbb…`、duration 5,671 ms）：**

```text
B我要用一個新的計畫來取代原本的計畫。在新的計畫裡，我要你詳細且精準地撰寫。我等一下會重啟一個新的對話，來進行接下來的 Agent 自主測試自動化作業。一樣我會用 Codex 的 goal 的方式，這個功能來進行 Agent 全自主的測試。
```

**草稿 #2（line 2420；430 bytes；其後 line 2422 有 `turn_aborted`，turn `01a0b1d5-e5f3…`、duration 1,361 ms）：**

```text
所以你等一下必須給我三樣東西：
第一，你必須重新擬定這一個新的測試計畫。
第二，你必須給我重新在新對話中 Agent 自主自動化測試的 goal 指令，以及要帶到新對話的相關交接 handoff 文件。
總共是三件事情：
第一，一個新的測試計畫。
第二，一個 goal 的精準指令，讓後續有新對話接手的 Agent 可以自主完成相關的測試。
```

說明：兩則草稿都被 owner 主動中斷（`<turn_aborted>`），**不是授權來源**；正式依據是 line 2427 的最終完整版（turn `01a0b1d6-32c3-7c50-8466-11685c5a7830`；其 UserMessage echo 在 line 2428，client_id `143b072f-23ad-41e3-92fb-07111b1c983a`）。

### 5.5 解讀與授權邊界（本輪 gate-5 的權威依據）

- 決策：**B**（branch (b)）。＝以新修訂 **Rev24** 取代 Rev23＋全新獨立複審（`review/attempt-36`、`review/attempt-37`）＋新的一次性 **gate-5**＋route **attempt-07** 恰好兩個 at-most-once 真機輸入：S4 目標卡片左鍵 ×1、S8 相簿層 ⋮ 左鍵 ×1（僅為讓選單出現並唯讀觀察 S9–S10；不重試、不點任何選單項目）。
- **A 未被選**：不採「記成這條路不需要／`ROUTE_NOT_NEEDED`」；「⋮ 沒有被機器驗證過」的不確定性由本輪解除，或由本輪誠實保留。
- 不授權（依決策紀錄與計畫 §24.4）：任何選單項目（尤其 Save All）／任何 chooser／任何鍵盤／任何 AX 寫入／任何第三個或重試的輸入（含第二次卡片或第二次 ⋮ 點擊）／任何下載、目的地寫入、正式 config/state/run-log 寫入／任何非由當輪畫面推導的座標（含把 `(304,50)`、`(305,50)` 當成 live 輸入）。
- live 點擊座標一律由「當輪新幀」＋冷凍 v5 定位器輸出推導；歷史座標（含實測 `(304,50)`）只准用於離線重播比對。
- gate-5 綁定要求：在任何輸入**之前**凍結並 commit；逐字綁定 line 2427（`context_authorization`）與 line 2405（`option_presentation_transcript`）；並綁定 Rev24 計畫與本決策紀錄的**定稿 SHA-256**（即 §2.3 的兩個定稿值）及 `review/attempt-36`／`review/attempt-37`。
- 決策紀錄檔：`evidence/20260918-owner-decisions/owner-decisions-rev24.json`（本輪已建立；SHA-256 見 §2.3 定稿值）。

### 5.6 白話

> 您在一道 A/B 選擇題裡選了 B：不做「記成不需要」，而是「開一份新計畫、重新獨立審查，然後再給一次、只有一次的新授權，把相簿打開、把 ⋮ 看一眼」。這個授權只允許「點開相簿一次、點 ⋮ 一次、看有沒有選單」，**不准點任何選單裡的按鈕、不准重試**。您前後打了三次，前兩次自己中斷，最後一次（完整版）才是正式依據。

---

## 6. Rev24 改了什麼（精準）

### 6.1 一句話

只改「⋮ 合格區域」的位置規則（v5）＋相應自測、gate 與 runbook 綁定；closure 語意、預算種類、append-only、唯讀邊界**全部不變**（計畫 §24.9）。

### 6.2 v5 修正規則（計畫 §24.3 的權威值）

- 不變：census／dot／triple／text-blocking 邏輯與所有偵測常數與 v4 **byte-identical**。
- 標題列（title strip）仍以 v4 公式導出：`band = {x0: tx1+2, x1: width-1, y0: max(0, ty0-6), y1: min(height-1, ty1+10)}`。
- 新增 header 區域：`header = {x0: tx1+2, x1: width-1, y1: max(0, ty0-7), y0: max(0, ty0-7-header_depth)}`；`--header-depth` 預設 **60**。
- eligible 條件（middle dot）：(a) 不在 `inside_text`（不變）；(b) 不在 group-title band（不變）；(c) 落在 `header` 內。`ELIGIBLE` 需**恰好一個**候選。
- 標題列內的 triple → 記為 `in_title_strip`，**不合格**（標題列承載日期與張數文字；放行它會重新引入「文字被誤讀成點」的風險區）。高於 header 上界 → `above_header_band`；低於標題列 → `below_album_title_band`。
- Exit codes 與 verdict 詞彙不變：0 `ELIGIBLE`、2 `TARGET_TITLE_NOT_FOUND`、3 `NO_ELLIPSIS_FOUND`、4 `AMBIGUOUS_ELLIPSIS`、5 `GROUP_LEVEL_ONLY`、6 `BAD_FRAME`；僅群組層候選仍為 `GROUP_LEVEL_ONLY`。
- 為什麼是 60：實測偏移為標題條上緣上方 33.5 px；60 px 為刻意有界的容納視窗（≈27 px 餘裕）；更深會掃入無關 chrome、可能把良性畫面變成 `AMBIGUOUS_ELLIPSIS`；再往上即 fail-closed（`NO_ELLIPSIS_FOUND`），絕不猜。
- 被拒的替代方案（已記錄給複審）：把標題列與 header 聯集（union）為合格區。拒絕理由：標題列在真實畫面是純文字、每個真實 triple 都是 glyph run；union 會無真實幀依據地放寬區域、提高誤點風險。
- 規劃期離線驗證（`/tmp` prototype；零 GUI、未入庫；Stage 04 必須以耐久證據重現）：對已入庫 post 幀 `4cb8a6b4…`、以 `--title-bbox 15,83,204,111` 執行修正規則 → 恰一個 eligible：`ellipsis_dots [[304.5,44.0],[304.5,49.5],[304.5,55.0]]`、`click_point [304,50]`；v4 位元同幀仍 `NO_ELLIPSIS_FOUND`。

### 6.3 v5 產物、自測與離線重播

- v5 目錄：`evidence/20260916-route/tools/v5/`（新目錄；v1–v4 全部凍結、不得改）：
  - `vision_reader.py`、`locate_album_card.py`、`verify_album_open.py`＝v4 位元相同副本；
  - `locate_album_ellipsis.py`＝修正版（v5）；
  - `README.md`：記錄修正幾何（含實幀數字）、被拒替代方案、`header_depth` 選值理由、離線重播指令。
- v5 自測：`evidence/20260916-route/tools/selftest/v5/selftest-summary.json`：
  - v4 的 16 cases 以修正版真實幾何重新表達（正例＝標題列上方、觀測偏移處；OCR 標題；header 內兩候選 → `AMBIGUOUS_ELLIPSIS`；僅群組 → `GROUP_LEVEL_ONLY`；皆無 → `NO_ELLIPSIS_FOUND`；card/verify/reader/helper/determinism 重綁 v5 工具組）；
  - 至少 4 個 v5 專屬案例：標題列內 dots → `NO_ELLIPSIS_FOUND`；超出 `header_depth` → `NO_ELLIPSIS_FOUND`；在 header 內但位於標題右緣左側 → `NO_ELLIPSIS_FOUND`；真實幾何正例的 5× determinism 重播；
  - 目標 ≥20 cases、`cases_failed 0`；summary 需同時登錄 v5 工具 SHA。
- 離線重播（驗收級，零 GUI；必須在 gate-5 凍結前完成）：v5＋已入庫 post 幀 `4cb8a6b4…` → `ELIGIBLE`、dots `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]`、`click_point [304,50]`；v4 位元＋同幀 → `NO_ELLIPSIS_FOUND`（attempt-06 之 `album-ellipsis-locate.json` 為對照證據）。任何其他 verdict 或座標＝TASK_REGRESSION。

### 6.4 gate-5 與 route attempt-07

- gate-5＝鏡射 gate-4 的 **17 鍵** schema：`artifact_type, gate, session_id, session_transcript, prior_gate, authority_artifact, plan_binding, context_authorization, option_presentation_transcript, decided_interpretation, alternative_reading, scope, budgets, not_authorized, recorded_in, recorded_at_local, notes`。
- 綁定：`prior_gate`＝gate-4（`e32ccd88…`，記為已被 attempt-06 用掉、不得延展或重發）；`authority_artifact`＝owner 決策紀錄（§2.3 定稿值）＋ Rev24 計畫其精確 hash（§2.3 定稿值）；`plan_binding.review_attempts`＝`review/attempt-36`、`review/attempt-37`（對同一修訂/hash 雙 `PLAN_APPROVED`）。
- `context_authorization`＝transcript line 2427（ordinal 2426）逐字＋SHA-256；`option_presentation_transcript`＝line 2405（ordinal 2404）之節錄（計畫 §24.4 記錄 470-byte excerpt）＋SHA-256。
- `decided_interpretation`＝目標：於 `jp.naver.line.mac` 內已開啟之目標相簿 `2024/05/13～05/17` 的相簿層 ⋮；授權輸入依序＝[S3 卡片左鍵 ×1、S6（v5）⋮ 左鍵 ×1]；`nothing_else: true`；worst case＝⋮ 打開的選單被唯讀觀察、由冷凍偵測器轉錄、留給 owner 關閉；**永不選取任何項目**。
- `budgets`（fresh、UNSPENT；鏡射 gate-4）：album_card 1、navigation 1、ellipsis 1、retry 0、menu_item 0、keyboard 0、app_acquisition 0、conversation_images 0、click_count_per_input 1、observation windows ≤5、screen captures ≤5、輸入 #2 後約 4 秒觀察窗。
- `not_authorized`：任何選單項目（明列 Save All）、任何 chooser、任何鍵盤、任何 AX 寫入、任何第三個或重試輸入、任何下載、任何目的地或正式 state 寫入、任何非由當輪畫面推導的座標。
- gate-5（與 Rev24 runbook、ledger skeleton）必須在任何輸入之前凍結並 commit；run 開始後才寫的 gate、缺 gate、或 ledger 少了 `906c1433…` parent 綁定＝TASK_REGRESSION。
- route attempt-07：`evidence/20260916-route/attempt-07/`；§20.2 的 S1–S11 沿用，僅以下替換／加註：S6 改呼叫 v5 定位器（同一張 post 幀、`--expect-start 2024/05/13 --expect-end 2024/05/17`）；S8 依 v5 `click_point` 送恰好一次左鍵；S9–S10 同 attempt-06 之觀察與冷凍偵測器轉錄；S11 寫 durable ledger＋execution 記錄。S3／S5 維持凍結 v4 工具；S10 冷凍偵測器 `detect_menu_popup.py`（`6ae9c250…`）沿用（reader-block exempt）；**S6 不得 fallback 回 v4 規則**。
- ledger parent＝attempt-06 FINAL `906c1433…`（其 parent＝attempt-05 `17b17203…`）。
- closure 語意不變（計畫 §24.5）：若 attempt-07 得機器可觀察 `AFFIRMATIVE` **且** §16.4 對採用之 v1.1 紀錄仍 re-derive `CONFIRMED`（兩者由 Stage 05 `e2e/attempt-08` 以新證據重新推導）→ 依 §20.3 closure tuple 前進；任何非 `AFFIRMATIVE` → 誠實記錄、零副作用、路線維持 scoped CORE blocker、立即通知 owner；**不得**自動採 `ROUTE_NOT_NEEDED`、不得自動分支；再試一次需**新修訂**（OOS-V24-5）。
- 不可變清單：v1–v4 工具與 v3／v4 自測、route attempt-01..06 證據、`e2e/attempt-02..07`、gate-1..4、各 ledger、已封存 handoff、`result.md` 既有歷史——一律 append-only。

### 6.5 白話

> 這次只改一件事：找 ⋮ 的「合格範圍」從「標題行裡面」改成「標題行的上方」（預設往上看 60 像素的帶狀區）。其他規矩（找到剛好一個才過、找不到就停、不准重試、不准點選單、最後還是同一個結案語意）完全沒變。修改版會先補上更真實的測試題，再用「上次那張真實畫面」離線證明：新版找得到、舊版找不到——證明完成後，才准凍結授權、才准碰真機。

---

## 7. 本輪管線（Pipeline）與 Exit gate

### 7.1 六步管線（新對話依序執行）

1. **Phase 0：唯讀基線（零 GUI）**。`git status`（工作區須乾淨）；逐項核對本檔 §11 的 SHA／bytes／檔數；任何不符 → 停、記證、通知 owner。
2. **Stage 02：獨立雙複審**。對 Rev24 精確 hash 跑 `review/attempt-36`、`review/attempt-37`（append-only、fresh context）。兩份皆 `PLAN_APPROVED` 才前進；否則修訂（→ `PLAN_REVISION 25`）並重跑複審，不得自我核准。
3. **Stage 03：交接重編**。先把現行 task `handoff.md`（`19c9c6d3…`）封存為 `handoff-history/handoff-plan-r23-<YYYYMMDD>-<HHMMSS>.md`，再依 Rev24 重編 `handoff.md`。
4. **Stage 04：fresh 實作（零 GUI）**。建立 `tools/v5/`＋`selftest/v5/`；完成離線重播（§6.3）並以耐久證據重現；**在任何輸入之前**凍結並 commit：gate-5、Rev24 runbook、ledger skeleton。
5. **Route attempt-07：一次性複驗**（本波唯一 GUI）。依 §6.4 執行；恰兩個輸入、fail-closed。
6. **Stage 05：獨立驗收 `e2e/attempt-08/`**（append-only；不得執行任何 GUI 輸入、不得改產品碼），以新證據重新推導「修正路線」與 §16.4 closure 事實；最後寫 `result.md`。

### 7.2 Runbook 摘要（S1–S11；權威細節在 Rev24 計畫／runbook）

S1：`getApp`／`getScreenshot({emit:false})`／`getAXState` → 落檔。S2：`screencapture -x` 探測（非 gating）。S3：卡片定位（凍結 v4 `locate_album_card.py`）。S4：輸入#1＝卡片左鍵 ×1。S5：開啟驗證（凍結 v4 `verify_album_open.py`；≥5% 像素差＋標題＋張數 57）。**S6：⋮ 定位（v5）**——決定停止或續行與 click point 的唯一來源。S7：pre 幀擷取。S8：輸入#2＝⋮ 左鍵 ×1（依 v5 click_point）。S9：post 觀察。S10：冷凍偵測器 `detect_menu_popup.py` 轉錄選單是否彈出。S11：FINAL ledger＋execution 記錄。

停止時的政策：未達結果的停止**不得**產出 `route-result.json`／`manifest.json`；停止狀態需在 ledger 明載。

### 7.3 Exit gate（什麼叫「這輪完成」）

- attempt-07 在 gate-5 下恰好執行一次；結果（正或負）為機器可觀察並已記錄。
- 三個結果分開回報：①本相簿資料 ②可重用能力（v5 定位與自測、可重跑證據）③整體結案。
- Stage 05 完成且未執行任何 GUI 輸入、未改產品碼。
- `result.md` 依 §24.5 語意誠實更新：正面（＋§16.4 `CONFIRMED`）→ 對應 closure tuple 前進；非正面 → 路線維持 scoped CORE blocker＋立即通知 owner。
- 全程零未授權動作、零對話內圖片、append-only 未破。

### 7.4 白話

> 新對話的順序：先重驗現況（零動作）→ 兩份獨立審查新計畫 → 重編交接文件 → 寫好新工具並用舊畫面離線證明修正有效 → **把一次性授權事先凍結** → 才准點那一次真機（卡片一次、⋮ 一次）→ 最後獨立驗收、誠實收尾。任何一步沒過，就不能往下走。

---

## 8. 硬邊界與禁令（逐條；與 GOAL 同步）

1. **零對話圖片**：影像只落 `/tmp` 或 repo evidence 供程式讀；對話與書面回報只出現路徑與 SHA-256。
2. **at-most-once**：所有 GUI 輸入恰好一次、每次恰 1 click；零重試、零替代座標；非明確授權視同未授權。
3. **零選單項目點擊**：任何選單項目（特別點名 **Save All 儲存全部**）永不點；⋮ 只為讓選單出現並被觀察。
4. 零 chooser、零鍵盤輸入、零 AX 寫入、零 app 取得（app_acquisition=0）。
5. **未凍結不得輸入**：gate-5／runbook／ledger skeleton 未凍結並 commit 前，不得有任何真機輸入。
6. **歷史座標不得作 live 輸入**：`(304,50)`、`(305,50)` 僅供離線重播比對；live 座標一律由當輪畫面推導。
7. **S6 不得 fallback 回 v4**；S3／S5 不得改用 v5 之外的工具。
8. **目的地唯讀**：`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`（57 檔 / 17,924,900 bytes）永不寫入、永不重下載。
9. **正式狀態唯讀**：`/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json`、`.../state/backup_state.json`、`.../state/run_log.md` 唯讀。
10. **字元不變**：`禎`（U+798E）與 `楨`（U+6968）不得合併或正規化。
11. **append-only**：v1–v4 工具、v3／v4 自測、route attempt-01..06 證據、`e2e/attempt-02..07`、gate-1..4、各 ledger、已封存 handoff、`result.md` 既有歷史——不得改寫或刪除。
12. **不新增第三方依賴**；不寫正式 state／config／run-log；不提交 `__pycache__`（python 一律 `-B`）。
13. **不得自我豁免 gate、不得自行擴權**；不確定時停下來問，不要猜。
14. **commit 慣例**：`<type>(<scope>): 繁中摘要`＋繁體中文四段式 body（意圖／做了什麼／驗證／下一步建議），並實際 add＋commit。
15. **回報三結果分離**：①本相簿資料 ②可重用能力 ③整體結案。

### 白話

> 規矩濃縮成三句：**不准在對話裡貼圖**；**真機只准點兩下（一次卡片、一次 ⋮）而且不准重試、不准點選單**；**所有既有紀錄、您的正式檔案、還有 57 張備份都唯讀，不准動**。任何需要破例的狀況，一律停下來問您。

---

## 9. 給 owner 的開跑前後指示

### 9.1 開跑前（必須）

- 把 LINE 停在**相簿列表**檢視，目標相簿卡片可見（`2024.05.13~2024.05.17`、57 張）。
- 若任何選單／彈窗是開著的：**由您自己關閉**（agent 不得點任何 UI 去關它）；關好後再讓 agent 開始。
- 維持與上次一致的視窗狀態（同一 app `jp.naver.line.mac`、同一列表檢視；不要改視窗大小／縮放／解析度）。

### 9.2 執行中（必須）

- 不要移動滑鼠、不要打字、不要切換視窗或 App；輸入 #2（⋮）後約 4 秒的觀察窗內尤其不要干擾。
- 不要鎖屏、不要讓螢幕睡眠。
- 若出現系統權限提示（螢幕錄製／輔助使用等）：agent 會停；請您人工處理後，再由主流程決定是否重開新一輪。

### 9.3 執行後

- 等 agent 回報；設計上失敗＝零殘留副作用，您不需要做任何復原動作。
- 若 ⋮ 成功彈出選單：agent **只觀察、不點任何項目**；結束後若選單仍開著，由**您自行關閉**。

### 9.4 白話

> 開跑前：把 LINE 開在相簿列表、看得到目標那本相簿；有選單開著請自己先關掉。開跑後：手離開滑鼠鍵盤、不要切視窗，讓它跑完。跑完若選單還開著，請您關掉（agent 不會點）。

---

## 10. 升級條件與「什麼時候一定要停」

1. **失敗上限**：路線複驗失敗累計 5 次 → 停，回報 owner 重新規劃；禁止長時間重試、禁止自動跑第 6 次。
2. **語意變更**：任何超出 Rev24 授權的語意變更（含放寬 fail-closed、改 closure 語意、改 gate 效力）→ 停，回 Planner（escalation／replan）。
3. **權限與系統提示**：出現任何系統權限提示／授權視窗 → 停，等 owner 處理。
4. **surface 不符**：LINE 不在相簿列表、目標卡不可見、或畫面狀態與 runbook 指定不符 → **零輸入停止**（resume-eligible；不是 route 結果、不改任何狀態）。
5. **未授權動作**：任何需要第三個輸入、重試、點選單、鍵盤、AX、或以歷史座標輸入的情境 → 停。
6. **根因或規則不可靠**：同一根因連續失敗，或證據顯示 v5 規則本身不可靠 → 停，回報 owner 決策。
7. **輸入 #1 已耗而輸入 #2 未獲成立條件** → 不得再重新授權；該輪誠實關閉。
8. **append-only／唯讀邊界被要求打破** → 停。

### 白話

> 會停下來的時候：試了 5 次還是不行、需要改規則的意義、系統跳權限視窗、LINE 畫面不是預期的樣子、需要任何「破例」動作、或證據顯示新規則本身有問題。停下來不是失敗，是設計：把狀況講清楚，再由您決定下一步。

---

## 11. 附錄：SHA-256 全表

說明：下表為 Phase 0 的核對清單。「完整」值為撰寫本檔時以 `shasum -a 256` 實測核對（與素材前綴一致）。本輪新產物（Rev24 計畫、決策紀錄）的 hash 見 §2.3 定稿值。

| 項目 | 路徑 | SHA-256 | 備註 |
|---|---|---|---|
| 現行計畫（Rev24，CANDIDATE） | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md` | 見 §2.3 定稿值 | 已由 Rev23 更新；等待 reviews 36/37 |
| Rev23（歷史核准版） | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（當時版本） | `4337e2b5c105901ce7c56956ecea5469894df2d2a29f099068c979584c71b6b2` | 2,093 行 / 284,897 bytes；34/35 核准 |
| 計畫複審 34 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-34/review_report.md` | `21c4bbb551070dbdfc7c155536c4651abc9492970311b739cf506dd1d2b8a57c` | `PLAN_APPROVED`（Rev23） |
| 計畫複審 35 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-35/review_report.md` | `975142c3ad79098141a74e4bd1cebf107d8e307fc65ec42ef4c781e3d8c8582c` | `PLAN_APPROVED`（Rev23） |
| v4 `vision_reader.py` | `evidence/20260916-route/tools/v4/vision_reader.py` | `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8` | 凍結 |
| v4 `locate_album_card.py` | `evidence/20260916-route/tools/v4/locate_album_card.py` | `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162` | 凍結（S3） |
| v4 `verify_album_open.py` | `evidence/20260916-route/tools/v4/verify_album_open.py` | `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58` | 凍結（S5） |
| v4 `locate_album_ellipsis.py` | `evidence/20260916-route/tools/v4/locate_album_ellipsis.py` | `b77e3d51d43e6cb4a0a1b7bf2e9e1179a2718d7867ac01b5344fbcd07cef96c4` | 凍結；v5 修正對象 |
| v4 `README.md` | `evidence/20260916-route/tools/v4/README.md` | `ed3ebf0aad53024f3e4fe7d4886faa9b37c048e2fdf95513ab3bc7bafe677f23` | 凍結 |
| v4 自測 summary | `evidence/20260916-route/tools/selftest/v4/selftest-summary.json` | `5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d` | 16 cases / 0 failed |
| v3 自測 summary | `evidence/20260916-route/tools/selftest/v3/selftest-summary.json` | `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324` | 13/13；凍結、不用於本輪 verdict |
| Vision helper | `evidence/20260916-route/tools/vision/vision_ocr.swift` | `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32` | 凍結 |
| 偵測器（S10） | `evidence/20260916-route/tools/detect_menu_popup.py` | `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc` | 凍結；reader-block exempt |
| 偵測器自測 | `evidence/20260916-route/tools/selftest/selftest_menu_popup.py` | `db0917039f085b0d90196348de0d0038e8d6abcd18418c0e41c4037231fbbfdc` | 4,018 bytes；凍結 |
| gate-4 | `evidence/20260916-route/attempt-06/gate-4-authorization.json` | `e32ccd882b93b784e1faf3f3ea1df9732ab093e26f74a89622ac857159876272` | 已由 attempt-06 用掉 |
| attempt-06 FINAL ledger | `evidence/20260916-route/attempt-06/run-ledger.json` | `906c14330605122e9b600359892d4400171d62564707d50af26ef8d8bb32fa2c` | attempt-07 的 parent |
| attempt-05 ledger | `evidence/20260916-route/attempt-05/run-ledger.json` | `17b172031a38ea6b5c66ebfedacf748aa1f08b12d572263d13eef02f54465218` | attempt-06 的 parent |
| post 幀 | `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` | `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3` | 離線重播錨點 |
| pre 幀 | `evidence/20260917-vision-reader/frames/route5r_frame_pre.jpg` | `3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531` | 已入庫 |
| baseline | `evidence/20260916-baseline/attempt-01/baseline-pre.json` | `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5` | 57 檔 / 17,924,900 bytes |
| v1.1 更正版紀錄 | `evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.1.json` | `a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263` | 1,741 bytes |
| result.md | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/result.md` | `bd00d9c9377a01530093e35a158280fb975f66fe493198b6ff315b21223207c0` | `CORE_ACCEPTANCE_BLOCKED` |
| execution-rev22 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev22.md` | `c9b590802c7b27f34796c8623005ad106343bcf0c43b23b799cdb94fcfade131` | — |
| task handoff（Rev23 綁定） | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/handoff.md` | `19c9c6d33c9fc2ea5aff2cd35948c6c5d81cb788285d6432b590520412b6883a` | 175 行 / 37,582 bytes；Stage 03 先封存 |
| owner 決策紀錄（Rev24） | `evidence/20260918-owner-decisions/owner-decisions-rev24.json` | 見 §2.3 定稿值 | 本輪建立 |
| transcript 決策行 2427 | 見 §5.1 | `a600ac4c9af8e3e44327f4566f5388985a79658b43a6eeb435915edec6f9e9ec` | 882 bytes |
| transcript 選項行 2405 | 見 §5.1 | `14905585890cb158957b0e20e34abe6ec8bac26439c8b18187d3f58076ff8752` | 1,931 bytes |
| transcript 草稿 2412 | 見 §5.1 | `caf2f7d789c3429fa9bc4e956ea1da6782c50afd4f6983ce952e565160ca4038` | 304 bytes（中斷） |
| transcript 草稿 2420 | 見 §5.1 | `a8caf86dc8e92338777157dae54904a689525a8fe653f1f7b08f3311ca7383b9` | 430 bytes（中斷） |
| transcript 提問 2291 | 見 §5.1 | `3fc89cbc9388a176fd92f47a00e0cae7bde24d51286a084584fa73da16d0ae8e` | 243 bytes |
| transcript 提問 2365 | 見 §5.1 | `2e729d0339bc1574d9869b7054da586259f7dde584fb6ef85c28135796850364` | 60 bytes |

命名更正註（依 Rev24 §24.8）：歷史文件曾以 `d8ffc129…` 標示「偵測器自測」；正確為——偵測器自測本體＝`evidence/20260916-route/tools/selftest/selftest_menu_popup.py` `db091703…`（4,018 B）；`d8ffc129…` 實為凍結的 `evidence/20260916-route/tools/selftest/selftest-summary.json`（2,946 B），已以該檔身分登錄。此為文件用字更正，非語意變更。

方向註：GOAL 內嵌本檔定稿 SHA-256（GOAL → 本檔）；本檔以 §2.3 定稿值指向 Rev24 計畫與 owner 決策紀錄；本檔**刻意不內嵌** GOAL 的 hash。
