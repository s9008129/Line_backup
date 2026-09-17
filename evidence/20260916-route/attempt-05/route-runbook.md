# Route attempt-05 執行手冊 v3 — 修正後路線：先進目標相簿，再輸入「相簿內 ⋮」（凍結於任何輸入之前）

凍結時間：2026-09-17T17:01+0800（本檔、`gate-3-authorization.json`、v3 工具與自測皆於任何輸入之前
凍結入庫；見本路徑的 git log）。
底稿：`evidence/20260916-route/attempt-04/route-runbook.md`（7,101 bytes，SHA-256
`302538920b108a6836059f27eff034cd7769b09b1dc47de843bfb8b78d5cdac8`），依 Rev20 §20.1/§20.2
把「唯一一次 ⋮」修正為「先開啟目標相簿（唯一一次導航輸入）→ 相簿內 ⋮（唯一一次 ⋮ 輸入）」，
並新增 `verify_album_open.py` 的開啟驗證與 `locate_album_ellipsis.py` 的相簿內定位。
計畫綁定：`plan.md` Rev20，SHA-256 `4919d87148c68ea3d70cbb9abd258edbd0bfa0b55be5123f7202251e557db17c`
（1,744 行 / 233,123 B；Stage 03 handoff `ab88e496e7ab24214247a1cc3c5fc65b751e439d3c46238433f65d02361484a4`，
38,196 B；雙批准＝review/attempt-28 `d9bf574f…` ＋ attempt-29 `540fda1a…`）。
Documented capability reference：`~/.codex/skills/line-album-backup/references/ui-procedure.md`
（27,769 bytes，SHA-256 `3a1bc29e7cc379ee41166387133125245f017c8f7a78799b27d920df09b75627`）。

## 授權與硬邊界（不可擴張、不可重試）

- 授權來源：第三次一次性授權（Rev20 §20.1）；gate 檔
  `evidence/20260916-route/attempt-05/gate-3-authorization.json`；使用者逐字指示
  2026-09-17T16:00:03.652+0800（transcript line 6206）與 16:01:49.779+0800（line 6224），
  脈絡為 14:59:40.847+0800（line 5091）逐字「2.要，授權給你」。
- 本授權與 attempt-03／attempt-04 額度完全獨立：**不重置、不展延**先前已用完的額度。
- 允許的輸入總量：**恰好 2 次**、且順序固定——
  ①目標相簿卡的 metadata 左鍵 **1 次**（本 run 唯一一次導航輸入；開啟相簿）；
  ②`verify_album_open.py` 對當幀回報 `ALBUM_OPEN_VERIFIED` 之後，「相簿內 ⋮」左鍵 **1 次**；
  之後只觀察。兩者皆 `click_count=1`。
- 禁止：把 LINE 帶到前景、捲動、`performSecondaryAction`/AXPress/AXUIElementPerformAction、
  鍵盤快捷鍵、點任何選單項、Save All、任何 chooser、任何 state/config/run-log 寫入、
  第二次嘗試任一控制項。
- **零重試、零對話圖片**；兩個點擊點都必須由「當幀」推導並記錄推導證據，**禁止歷史座標**。
- 目標＝相簿「2024/05/13～05/17」（畫面顯示標題 `2024/05/13~05/17`）＋57 張
  （來源指紋 2024-05-13 / 2024-05-17 / 57）。可見非目標卡（例：2024/06/02~06/07、65張）
  與視窗頂端群組列的 ⋮（群組選單）皆非目標；群組列候選永不具資格。

## 前置（全部成立才可執行；任一不成立＝唯讀停止並立即通知使用者）

1. 使用者已把 LINE 置於相簿列表狀態、目標卡可見（標題 `2024/05/13~05/17`、57 張），且當前
   畫面沒有可見的選單／對話框／chooser／照片檢視器／系統權限提示。畫面已顯示這類覆蓋層、或
   無法顯示目標卡 → 記 `NO_TARGET_ON_FRAME`（如實記錄）、最多 **5 個唯讀觀察窗**、**立即**
   通知使用者（常駐指示：不得長時間重試／迴圈）、停止。
2. 凍結項（pre-freeze 波，皆於任何輸入前入庫）：本手冊、`gate-3-authorization.json`、
   v3 工具與**已通過並留證的自測** `evidence/20260916-route/tools/`：`locate_album_card.py`、
   `verify_album_open.py`、`locate_album_ellipsis.py`（SHA 見下）；
   自測須先執行完畢且 `tools/selftest/v3/selftest-summary.json` 為 `result: PASS`，該摘要 SHA-256
   一併記錄（對應 Rev19 §19.2「frozen and self-tested before the click」）。凍結 SHA-256（bytes）：
   `locate_album_card.py` `500fcadbe8cb47f1cd22f0d247ad7d7d65c84baef4000f2239e1872e340e98e4`（7,389）；
   `verify_album_open.py` `80504262025cf10202c8938612b5be73f91809578f1317f36733f52b513fa74b`（6,818）；
   `locate_album_ellipsis.py` `60e3120abb312f189f785f12ee4047f4365028a8759ae88874eebb06046a7deb`（11,273）；
   `selftest/v3/run_selftest.py` `94a41092e2c72a95bf833fea64f7c607979512133034c43abeaa0aedf9f0bf13`（10,777）；
   `selftest/v3/selftest-summary.json` `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324`（4,250）；
   `tools/README.md` `174f01cd22f7032bb72aca9a8ebd0cd04021b595f706034f8d6de1f67bccb14c`（3,392）；
   attempt-04 的 `detect_menu_popup.py`（6,339 B /
   `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`）與 v2 定位器
   `locate_card_ellipsis.py`（8,943 B /
   `8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e`）原樣重用：
   v2 定位器在本 run 僅作旁證，永不阻擋、永不算出點擊點。
3. 新建 `run-ledger.json`，其 `parent_ledger_sha256` ＝ attempt-04 最終 ledger
   `df0e9c446acf127c59c5827e4d50bc37a8be5e4cbc56722e7b61734866f19dd6`；`initial_counts` 明列
   `album_card_input=1`、`ellipsis_input=1`、`app_acquisition_input=0`、其餘輸入類別 0。
4. 工具自測已於**任何輸入之前**通過並入庫：`evidence/20260916-route/tools/selftest/v3/selftest-summary.json`
   （`result: PASS`，13/13；SHA-256 `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324`）；
   自測涵蓋 v3 三工具全部拒絕路徑與一個合格案例的
   點擊點。

## 步驟（逐步記證；任何偏離＝SAFE_ABORT）

S1. **Binding read（零輸入）**：`getApp("jp.naver.line.mac", {emit:false})` →
    `getScreenshot({emit:false})` 寫 `/tmp/route5_frame_pre.jpg`（記 bytes／尺寸／SHA-256／擷取時間）；
    `getAXState({emit:false, disableDiffing:true})`（記 SHA）。
S2. **Screen-scope 探針（恰一次；唯讀）**：`screencapture -x /tmp/route5_screen_probe.png`。
    接受條件：exit 0、可解碼、且凍結 `locate_album_card.py` 對「AX 視窗 bounds 裁切」在 scale 2
    或 scale 1 得到 `ELIGIBLE`；記錄所採 scale。否則 `screen_scope=UNAVAILABLE`（非致命，run 以
    window-scoped 續行）。探針後若觀察到**新的系統權限對話框** → `PERMISSION_PROMPT_OBSERVED`、
    `SAFE_ABORT`、不送任何輸入。
S3. **卡片定位（唯讀；不得以歷史座標跳過）**：`locate_album_card.py /tmp/route5_frame_pre.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57
    --out evidence/20260916-route/attempt-05/album-card-locate.json`。僅接受
    `verdict=ELIGIBLE`（標題日期相符、click point 通過邊距規則、可讀張數為 57）；可讀但非 57、
    邊距不安全、找不到標題 → `SAFE_ABORT`，不送輸入，記唯讀證據並立即通知使用者。
S4. **輸入 #1**：於 S3 的 `click_point` 送**恰好 1 次**正常左鍵（相簿卡 metadata 點）。
S5. **立即 post 觀察（零輸入）＋開啟驗證**：`getScreenshot` → `/tmp/route5_frame_post.jpg`；
    `validate`：`verify_album_open.py /tmp/route5_frame_pre.jpg /tmp/route5_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57
    --out evidence/20260916-route/attempt-05/album-open-verify.json`。
    `ALBUM_OPEN_VERIFIED` 需「post 幀找得到目標日期標題」且「相對 pre 幀的變動像素比例 ≥5%」；
    可讀非目標日期／可讀且合理的非 57 張數 → `TARGET_MISMATCH`；無實質變動 → `NO_EFFECT`；
    標題不可讀 → `INCONCLUSIVE`。**任何非 `ALBUM_OPEN_VERIFIED` 的結果都不得送 ⋮ 輸入**：
    記證、立即通知使用者、停止。
S6. **相簿內 ⋮ 定位（唯讀）**：`locate_album_ellipsis.py /tmp/route5_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17
    --title-bbox <S5 的目標標題 bbox> --expect-group-title 「旻謙允禎成長日記」
    --out evidence/20260916-route/attempt-05/album-ellipsis-locate.json`。
    全幀三點普查如實記錄；`ELIGIBLE` 僅當**恰有一個**候選落在「目標標題同一列帶」內且位於標題
    右方；群組標題列帶內候選永不具資格。`NO_ELLIPSIS_FOUND`／`AMBIGUOUS_ELLIPSIS`／
    `GROUP_LEVEL_ONLY` → 不送 ⋮ 輸入：記證、立即通知使用者、停止。
S7. **Screen-scope pre-menu 擷取（唯讀；當 `screen_scope=AVAILABLE` 時）**：
    `screencapture -x /tmp/route5_screen_pre_menu.png`（detector 的 screen 空間 pre 幀）。
    若 S2 已判定 `screen_scope=UNAVAILABLE`，本步驟與 S9 的 screen captures 皆**不執行**，
    S10 的判定以 app pre（`/tmp/route5_frame_post.jpg` 之前的 album-open 幀）vs app post
    為基礎，並如實記錄。
S8. **輸入 #2**：於 S6 的 `click_point` 送**恰好 1 次**正常左鍵（相簿內 ⋮）。
S9. **立即 post 觀察（零輸入）**：app 幀 `/tmp/route5_frame_post_menu.jpg` 與 AX 狀態；當
    `screen_scope=AVAILABLE` 時於約 4 秒內做 ≤5 張 screen captures
    `/tmp/route5_screen_post_<n>.png`（只記 timestamp／bytes／尺寸／SHA-256）。
S10. **偵測與轉錄**：凍結 detector 對（screen pre-menu vs 各 post，僅 `screen_scope=AVAILABLE`）
     與（app pre vs app post，永遠執行）；
     選單項目逐列轉錄。`AFFIRMATIVE` 僅認機器可觀測證據（新 AX menu 元素，或 detector
     `MENU_DETECTED`＝新矩形區塊＋≥2 轉錄字串）；OCR-only、人類目擊-only、不完整擷取 →
     `UNKNOWN`，永不 AFFIRMATIVE。觀察到的選單另與 capability reference 的項目順序
     （Select items / Rename album / Save All / Delete album / Share album）比對並記錄——
     只作核對，**永不用來計算或點擊任何一列**。若轉錄缺少 capability reference 的項目
     （尤其 Save All）→ 記為 scope fact，路由到「owner 明示決定／另開新 revision」分支，
     不得靜默完成路線判定。
S11. **停止並寫證**：`route-result.json`、`run-ledger.json`（FINAL，含 counts 與
     `route_result_sha256`）、`manifest.json`、`album-card-locate.json`、`album-open-verify.json`、
     `album-ellipsis-locate.json`、`screen-probe.json`、`menu-analysis.json`，以及
     `workflow-routing` §7.11 的耐久執行紀錄 `execution-rev20.md`。幀不落庫（只記
     bytes／尺寸／SHA-256，frames 留 /tmp）；既有 attempt 與凍結紀錄永不觸碰；選單保持開啟即停
     （全程不送鍵盤）。通知使用者時必須同時點名危害：**選單內含破壞性項目（Save All），
     請勿點擊任何項目**，並請其自行關閉選單（關閉動作本身即為輸入，所以由使用者執行）。

## 判定與結案路由（依 Rev20 §20.3）

- `AFFIRMATIVE` → 修正後路線在相簿層級成立；`CUA_ROUTE_DECISION` PASS；路線不再是 CORE 阻擋。
  **不**授權任何選單項啟動；production Save-All 仍在所有波次之外。
- 非 `AFFIRMATIVE`（`UNKNOWN`／`SAFE_ABORT`／`NO_EFFECT`／`TARGET_MISMATCH`／`NO_ELLIPSIS_FOUND`／
  `AMBIGUOUS_ELLIPSIS`／`GROUP_LEVEL_ONLY`／`NO_TARGET_ON_FRAME`）→ 如實記錄、零副作用、立即通知
  使用者；是否以 `ROUTE_NOT_NEEDED` 結案**必須**由使用者明示決定，且不得自動執行。

## 證據政策

- 幀不落庫：只記 bytes／尺寸／SHA-256 與轉錄結果；frames 留 /tmp 供 Stage 05 重跑凍結工具。
- 三個 v3 工具只做唯讀分析、永不送輸入；detector 只比對影像、永不送輸入。
- **環境陷阱**：本環境 tesseract 讀不到 /tmp 下的圖檔（`Error in fopenReadStream`），所有工具
  以 stdin/stdout 模式執行 OCR（`tesseract - stdout … tsv`），不落暫存檔。
- 任何偏離本手冊的行為＝本次 run 無效；以 `SAFE_ABORT` 記錄並回報使用者。
