# Route attempt-06 執行手冊 v4 — 修正後路線（v4 Vision 讀者）：先進目標相簿，再輸入「相簿內 ⋮」（凍結於任何輸入之前）

凍結時間：2026-09-17T23:10+0800（本檔、`gate-4-authorization.json`、v4 工具與其自測皆於任何輸入之前
凍結入庫；見本路徑的 git log）。
底稿：`evidence/20260916-route/attempt-05/route-runbook.md`（11,826 bytes，SHA-256
`b78f1c9133ae4b77f922b650800f93f030a8aec7014a0db36bf272f5a3010019`），依 Rev23 §22.3 置換：
S3／S5／S6 改用 v4 Vision 工具（其 JSON 必須帶 v4 `reader` block）、S10 維持凍結 tesseract detector（豁免）、
S11 增寫耐久執行紀錄 `execution-rev22.md`；其餘條文不變。
計畫綁定：`plan.md` Rev23，SHA-256 `4337e2b5c105901ce7c56956ecea5469894df2d2a29f099068c979584c71b6b2`
（2,093 行 / 284,897 B；雙批准＝review/attempt-34 report `21c4bbb551070dbdfc7c155536c4651abc9492970311b739cf506dd1d2b8a57c`
＋ review/attempt-35 report `975142c3ad79098141a74e4bd1cebf107d8e307fc65ec42ef4c781e3d8c8582c`，皆 `PLAN_APPROVED`）。
授權來源（gate-4）：`evidence/20260916-route/attempt-06/gate-4-authorization.json`；owner 決策逐字
2026-09-17T21:38:29.198+0800（transcript line 1063）「1 選 B；2 用更正版紀錄」；權威紀錄＝
`evidence/20260917-owner-decisions/owner-decisions-rev22.json`（SHA-256
`0664b5fba0fc73b3516a790b8b2e783819892ffea3cf078c087cd68c09374b32`，commit `c301e5e`）。
系列同名提醒：`evidence/20260916-route/attempt-06` 是「路線 run 系列」；`.agent/tasks/<TASK_ID>/e2e/attempt-06`
是已消耗的 Rev21 波驗收，本波驗收是 `e2e/attempt-07`——兩系列不得混稱（RV-33-4）。

## 授權與硬邊界（不可擴張、不可重試）

- 授權來源：第四次一次性授權（Rev20 §20.3 branch (b)，Rev23 §22.2/§22.3）；gate 檔（同上）；owner 決策逐字（同上）；
  option presentation L1025（2026-09-17T21:27:32.926+0800）與 L1048（21:30:01.805+0800）。
- 本授權與 gate-1／gate-2／gate-3 完全獨立：**不重置、不展延**先前已用完的額度；
  attempt-05 的 album-card 輸入維持 SPENT 1/1，其凍結裁決（`STOPPED_AT_S5_TARGET_MISMATCH`）原樣有效。
- 允許的輸入總量：**恰好 2 次**、順序固定——
  ①目標相簿卡的 metadata 左鍵 **1 次**（本 run 唯一一次導航輸入；開啟相簿）；
  ②v4 `verify_album_open.py` 對當幀回報 `ALBUM_OPEN_VERIFIED`（且 S6 回報 `ELIGIBLE`）之後，
  「相簿內 ⋮」左鍵 **1 次**；之後只觀察。兩者皆 `click_count=1`。
- 預算別名：**輸入 #1 同時計入 `navigation_inputs` 與 `album_card_inputs`**；不另授權任何額外導航輸入。
- 禁止：把 LINE 帶到前景、捲動、`performSecondaryAction`/AXPress/AXUIElementPerformAction/AX 寫入、
  鍵盤快捷鍵、點任何選單項、Save All、任何 chooser、任何 destination／formal state／run-log 寫入、
  重新下載、第二次嘗試任一控制項、`ROUTE_NOT_NEEDED` 結案（owner 選 B，非 A）。
- **零重試、零對話圖片**；兩個點擊點都必須由「當幀」推導並記錄推導證據，**禁止歷史座標**。
- 目標＝相簿「2024/05/13～05/17」（畫面顯示標題 `2024/05/13~05/17`）＋57 張
  （來源指紋 2024-05-13 / 2024-05-17 / 57）。可見非目標卡（例：2024/06/02~06/07、65張）
  與視窗頂端群組列的 ⋮（群組選單）皆非目標；群組列候選永不具資格。

## 前置（全部成立才可執行；任一不成立＝唯讀停止並立即通知使用者）

1. 使用者已把 LINE 置於相簿列表狀態、目標卡可見（標題 `2024/05/13~05/17`、57 張），且當前
   畫面沒有可見的選單／對話框／chooser／照片檢視器／系統權限提示。畫面已顯示這類覆蓋層、或
   無法顯示目標卡 → 記 `NO_TARGET_ON_FRAME`（如實記錄）、最多 **5 個唯讀觀察窗**、**立即**
   通知使用者（常駐指示：不得長時間重試／迴圈）、停止、零輸入。
2. 凍結項（pre-freeze 波，皆於任何輸入前入庫並由 orchestrator 提交）：本手冊、gate-4、v4 工具
   `evidence/20260916-route/tools/v4/` 與**已通過並留證的自測**，以及凍結 Vision helper 原始碼、
   凍結 detector 與其凍結自測。凍結 SHA-256（bytes）：
   `v4/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`（8,369）；
   `v4/locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162`（7,025）；
   `v4/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`（6,981）；
   `v4/locate_album_ellipsis.py` `b77e3d51d43e6cb4a0a1b7bf2e9e1179a2718d7867ac01b5344fbcd07cef96c4`（11,436）；
   `vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`（1,070）；
   `selftest/v4/selftest-summary.json` `5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d`（11,718；
   16 cases、`cases_failed 0`、`result PASS`、5× 逐位元組相同 stdout）；
   detector `detect_menu_popup.py`（6,339 B /
   `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`）與其凍結自測
   `selftest/selftest_menu_popup.py`（`db0917039f085b0d90196348de0d0038e8d6abcd18418c0e41c4037231fbbfdc`）
   原樣重用（tesseract 版；reader-block 豁免）。
   v3 工具組與其 13/13 自測（`17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324`）維持凍結，
   不用於本 run 的裁決；唯一例外是 S2 的 screen-scope 探針（唯讀、SUPPORTING、非阻擋）以凍結 v3
   `locate_album_card.py`（`500fcadbe8cb47f1cd22f0d247ad7d7d65c84baef4000f2239e1872e340e98e4`）判讀；
   其 JSON（screen-probe.json）屬 reader-block 豁免項。
3. 新建 `run-ledger.json`（本路徑），其 `parent_ledger_sha256` ＝ attempt-05 最終 ledger
   `17b172031a38ea6b5c66ebfedacf748aa1f08b12d572263d13eef02f54465218`；`initial_counts` 明列
   `album_card_input=1`、`navigation_input=1`、`ellipsis_input=1`、`app_acquisition_input=0`、其餘輸入類別 0；
   `state=FROZEN_BEFORE_INPUTS`。

## 步驟（逐步記證；任何偏離＝SAFE_ABORT）

S1. **Binding read（零輸入）**：`getApp("jp.naver.line.mac", {emit:false})` →
    `getScreenshot({emit:false})` 寫 `/tmp/route6_frame_pre.jpg`（記 bytes／尺寸／SHA-256／擷取時間）；
    `getAXState({emit:false, disableDiffing:true})`（記 SHA）。
S2. **Screen-scope 探針（恰一次；唯讀）**：`screencapture -x /tmp/route6_screen_probe.png`。
    接受條件：exit 0、可解碼、且**凍結 v3** `locate_album_card.py` 對「AX 視窗 bounds 裁切」在 scale 2
    或 scale 1 得到 `ELIGIBLE`；記錄所採 scale。否則 `screen_scope=UNAVAILABLE`（SUPPORTING、非致命，
    run 以 window-scoped 續行）。探針後若觀察到**新的系統權限對話框** → `PERMISSION_PROMPT_OBSERVED`、
    `SAFE_ABORT`、不送任何輸入。產出 `evidence/20260916-route/attempt-06/screen-probe.json`
    （v3 screen-probe JSON；reader-block 豁免）。
S3. **卡片定位（唯讀；v4；不得以歷史座標跳過）**：`/opt/homebrew/bin/python3
    evidence/20260916-route/tools/v4/locate_album_card.py /tmp/route6_frame_pre.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57
    --out evidence/20260916-route/attempt-06/album-card-locate.json`。僅接受
    `verdict=ELIGIBLE`（標題日期相符、click point 通過邊距規則、可讀張數為 57；張數單獨不可讀依凍結 v3
    同軌、不拒絕）；可讀但非 57、邊距不安全、找不到標題、或 v4 reader 失敗（`binary_missing`／
    `build_failed`／`nonzero_exit`／`unparsable`／`timeout`）→ 凍結拒絕路徑，`SAFE_ABORT`，不送輸入，
    記唯讀證據並立即通知使用者。**本 JSON 必須帶 v4 `reader` block**（`helper.resolved_from`、
    `helper.binary_sha256`、各 call 的 `outcome`、`exit_code`、`stdout_sha256`）。
S4. **輸入 #1**：於 S3 的 `click_point` 送**恰好 1 次**正常左鍵（相簿卡 metadata 點）；
    同時計入 `navigation_inputs` 與 `album_card_inputs`。
S5. **立即 post 觀察（零輸入）＋開啟驗證（v4）**：`getScreenshot` → `/tmp/route6_frame_post.jpg`；
    `/opt/homebrew/bin/python3 evidence/20260916-route/tools/v4/verify_album_open.py
    /tmp/route6_frame_pre.jpg /tmp/route6_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 --delta 12
    --out evidence/20260916-route/attempt-06/album-open-verify.json`。
    `ALBUM_OPEN_VERIFIED` 需「post 幀找得到目標日期標題」且「相對 pre 幀的變動像素比例 ≥5%（凍結
    `--delta 12`）」；可讀非目標日期／可讀且合理的非 57 張數 → `TARGET_MISMATCH`；無實質變動 → `NO_EFFECT`；
    標題不可讀 → `INCONCLUSIVE`。**任何非 `ALBUM_OPEN_VERIFIED` 的結果都不得送 ⋮ 輸入**：記證、
    立即通知使用者、停止。confidence 值僅為記錄證據、**永不是關卡**。**本 JSON 必須帶 v4 `reader` block**。
S6. **相簿內 ⋮ 定位（唯讀；v4）**：`/opt/homebrew/bin/python3
    evidence/20260916-route/tools/v4/locate_album_ellipsis.py /tmp/route6_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17
    --title-bbox <S5 的目標標題 bbox> --expect-group-title 「旻謙允禎成長日記」
    --out evidence/20260916-route/attempt-06/album-ellipsis-locate.json`。
    全幀三點普查如實記錄；`ELIGIBLE` 僅當**恰有一個**候選落在「目標標題同一列帶」內且位於標題右方；
    群組標題列帶內候選永不具資格。`NO_ELLIPSIS_FOUND`／`AMBIGUOUS_ELLIPSIS`／`GROUP_LEVEL_ONLY`／
    `TARGET_TITLE_NOT_FOUND`／`BAD_FRAME`／任何 v4 reader 失敗 → 不送 ⋮ 輸入：記證、立即通知使用者、
    停止。**本 JSON 必須帶 v4 `reader` block**。
S7. **Screen-scope pre-menu 擷取（唯讀；當 `screen_scope=AVAILABLE` 時）**：
    `screencapture -x /tmp/route6_screen_pre_menu.png`（detector 的 screen 空間 pre 幀）。
    若 S2 已判定 `screen_scope=UNAVAILABLE`，本步驟與 S9 的 screen captures 皆**不執行**，
    S10 的判定以 app pre（`/tmp/route6_frame_post.jpg` 之前的 album-open 幀）vs app post
    為基礎，並如實記錄。
S8. **輸入 #2**：於 S6 的 `click_point` 送**恰好 1 次**正常左鍵（相簿內 ⋮）。
S9. **立即 post 觀察（零輸入）**：app 幀 `/tmp/route6_frame_post_menu.jpg` 與 AX 狀態（AX re-read）；
    當 `screen_scope=AVAILABLE` 時於約 4 秒內做 ≤5 張 screen captures
    `/tmp/route6_screen_post_<n>.png`（只記 timestamp／bytes／尺寸／SHA-256）。
S10. **偵測與轉錄**：凍結 tesseract detector `detect_menu_popup.py` 對**每一組凍結 pre/post**——
     （screen pre-menu vs 各 post，僅 `screen_scope=AVAILABLE`）與（app pre vs app post，永遠執行）——
     並對 S9 的 AX 狀態**重讀**（AX re-read；新 AX menu 元素屬機器可觀測證據）；
     選單項目逐列轉錄。detector 與其輸出（menu-analysis.json）**豁免 v4 reader block**。
     `AFFIRMATIVE` 僅認機器可觀測證據（新 AX menu 元素，或 detector `MENU_DETECTED`＝新矩形區塊＋
     ≥2 轉錄字串）；OCR-only、人類目擊-only、不完整擷取 → `UNKNOWN`，永不 AFFIRMATIVE。
     觀察到的選單另與 capability reference 的項目順序（Select items / Rename album / Save All /
     Delete album / Share album）比對並記錄——只作核對，**永不用來計算或點擊任何一列**。若轉錄缺少
     capability reference 的項目（尤其 Save All）→ 記為 scope fact，路由到「owner 明示決定／另開新
     revision」分支，不得靜默完成路線判定。
S11. **停止並寫證**：`run-ledger.json`（FINAL，含 events／final counts／stop reason；達路線結果時另含
     `route_result_sha256`）與 `workflow-routing` §7.11 的耐久執行紀錄 `execution-rev22.md`（Rev23 §22.3）。
     達路線結果時另寫 `route-result.json`、`manifest.json`、`album-card-locate.json`、
     `album-open-verify.json`、`album-ellipsis-locate.json`、`screen-probe.json`、`menu-analysis.json`。
     **停止政策：凡在任何路線結果之前停止（前置失敗、S3／S5／S6 任一關卡、reader 失敗），
     不寫 `route-result.json`、不寫 `manifest.json`；由 FINAL ledger 如實記錄 events／final counts／
     stop reason。**
     幀不落庫（只記 bytes／尺寸／SHA-256，frames 留 /tmp）；既有 attempt 與凍結紀錄永不觸碰；
     選單保持開啟即停（全程不送鍵盤）。通知使用者時必須同時點名危害：**選單內含破壞性項目（Save All），
     請勿點擊任何項目**，並請其自行關閉選單（關閉動作本身即為輸入，所以由使用者執行）。

## 判定與結案路由（依 Rev23 §22.5／Rev20 §20.3 branch (b)）

- `AFFIRMATIVE` → 修正後路線在相簿層級成立；`CUA_ROUTE_DECISION` PASS；路線不再是 CORE 阻擋。
  **不**授權任何選單項啟動；production Save-All 仍在所有波次之外。
- 非 `AFFIRMATIVE`（`UNKNOWN`／`SAFE_ABORT`／`NO_EFFECT`／`TARGET_MISMATCH`／`INCONCLUSIVE`／
  `NO_ELLIPSIS_FOUND`／`AMBIGUOUS_ELLIPSIS`／`GROUP_LEVEL_ONLY`／`NO_TARGET_ON_FRAME`／reader 失敗）→
  如實記錄、零副作用、立即通知使用者；`ROUTE_NOT_NEEDED` **不得**自動執行（owner 選 B），
  結案路由由 owner 明示決定。

## 停止／通知／續行（fail-closed）

- 前置失敗（零輸入）：如實記錄、通知使用者、停止；**不花任何輸入、不變更任何狀態**。
- **續行規則（Rev23 §22.3）**：若停止時**零輸入**已花（例：前置畫面失敗），同一 ledger 可在 owner
  復原畫面後以同一未用授權續行（同 attempt-05 的 resume 模式）；**已花輸入 #1 後才停止者，
  絕不重新授權輸入 #2**。
- 任何 reader 失敗或任一關卡非通過 → 停止於下一個輸入之前；不得猜測、不得重試、不得改點其他座標。

## 證據政策

- 幀不落庫：只記 bytes／尺寸／SHA-256 與轉錄結果；frames 留 /tmp 供 Stage 05 重跑凍結工具。
- v4 三工具只做唯讀分析、永不送輸入；凍結 detector 只比對影像、永不送輸入；v3 工具本次僅供 S2 probe
  判讀（SUPPORTING、非阻擋，其 JSON 豁免 reader block）。
- **reader block 規則**：僅三個 v4 工具 JSON（S3／S5／S6 的 album-card-locate／album-open-verify／
  album-ellipsis-locate）必須帶 v4 `reader` block；detector 輸出與 v3 screen-probe JSON 豁免。
- **reader 失敗語意**：`binary_missing`／`build_failed`／`nonzero_exit`／`unparsable`／`timeout` →
  凍結拒絕路徑（非零退出、不猜值），在下一個輸入前停止；confidence 值僅記錄、**永不是關卡**。
- **空 stdout 註記（RV-33-5）**：空 stdout＝outcome `ok` ＋零詞＝如實記 `UNREADABLE`，**永不**算成功讀取；
  只有在規則要求可讀值（如標題區）時才觸發拒絕；**單獨的張數不可讀**依凍結 v3 同軌、**不**拒絕。
- 零對話圖片；環境陷阱：本環境 tesseract 讀不到 /tmp 下的圖檔（`Error in fopenReadStream`），
  所有工具以 stdin/stdout 模式執行 OCR（`tesseract - stdout … tsv`），不落暫存檔。
- 任何偏離本手冊的行為＝本次 run 無效；以 `SAFE_ABORT` 記錄並回報使用者。
