# Route attempt-07 執行手冊 v5 — 修正版位置規則（v5 header）：先進目標相簿，再輸入「相簿內 ⋮」（凍結於任何輸入之前）

凍結時間：2026-09-18T11:20+0800（本檔、`gate-5-authorization.json`、v5 工具與其自測、離線重播雙列、ledger skeleton 皆於任何輸入之前凍結入庫；見本路徑的 git log）。
底稿：`evidence/20260916-route/attempt-06/route-runbook.md`，依 Rev24 §24.3 置換：
S3／S5 維持凍結 v4 工具（其 JSON 必須帶 v4 `reader` block）、S6 改用 v5 定位器（其 JSON 必須帶 v4 `reader` block；S6 不得 fallback 回 v4）、S10 維持凍結 tesseract detector（豁免）、S11 增寫耐久執行紀錄 `execution-rev24.md`；其餘條文不變。
計畫綁定：`plan.md` Rev24，SHA-256 `40eb01980c7e11f96b4b12c2db8f53728852f1ab6ca452dfb5e865fd5435a003`
（2,330 行 / 313,461 B；雙批准＝review/attempt-36 report `f7a9d3ebaae5c56f7a93c1d98edebb127a331f784bf19b60aa2984598519aec5`
＋ review/attempt-37 report `941580825840a3b14bc1da8cb3abf5cec748179481714d445c80ebc3140f1506`，皆 `PLAN_APPROVED`）。
授權來源（gate-5）：`evidence/20260916-route/attempt-07/gate-5-authorization.json`（17 鍵，鏡射 gate-4；`prior_gate e32ccd88…` 已耗；`authority_artifact be1f5173…`；`plan_binding` Rev24＋reviews 36/37）；owner B 決策逐字
2026-09-18T08:06:40.115+0800（transcript line 2427，882 B `a600ac4c…`）；權威紀錄＝
`evidence/20260918-owner-decisions/owner-decisions-rev24.json`（SHA-256
`be1f5173de9219bfba2a547223542dde17c6e6a23f653274122f0d8dcbe2360d`，commit `92a167e`）；
option presentation line 2405（1,931 B `14905585…`，B 節錄 470 B `5674299e…`）。
系列同名提醒：`evidence/20260916-route/attempt-07` 是「路線 run 系列」；`.agent/tasks/<TASK_ID>/e2e/attempt-07`
是已消耗的 Rev22 波驗收（report `6416a5f4…`），本波驗收是 `e2e/attempt-08`——兩系列不得混稱（§23.1 RV-33-4＋§24）。

## 授權與硬邊界（不可擴張、不可重試）

- 授權來源：第五次一次性授權（§20.3 branch (b)，Rev24 §24.2/§24.3）；gate 檔（同上）；owner B 決策逐字（同上）；
  option presentation L2405（2026-09-18T08:02:44.793+0800）。
- 本授權與 gate-1..4 完全獨立：**不重置、不展延**先前已用完的額度；
  attempt-05 的 album-card 輸入維持 SPENT 1/1（`17b17203…`，`TARGET_MISMATCH`），
  attempt-06 的 album-card 輸入維持 SPENT 1/1（`906c1433…`，`CLOSED_AFTER_INPUT_1`，S6 `NO_ELLIPSIS_FOUND`），其凍結裁決原樣有效。
- 允許的輸入總量：**恰好 2 次**、順序固定——
  ①目標相簿卡的 metadata 左鍵 **1 次**（本 run 唯一一次導航輸入；開啟相簿）；
  ②v4 `verify_album_open.py` 對當幀回報 `ALBUM_OPEN_VERIFIED`（且 v5 S6 回報 `ELIGIBLE`）之後，
  「相簿內 ⋮」左鍵 **1 次**（於 v5 `click_point`）；之後只觀察。兩者皆 `click_count=1`。
- 預算別名：**輸入 #1 同時計入 `navigation_inputs` 與 `album_card_inputs`**；不另授權任何額外導航輸入。
- 禁止：把 LINE 帶到前景、捲動、`performSecondaryAction`/AXPress/AXUIElementPerformAction/AX 寫入、
  任何選單項目（明列 Save All 儲存全部）、任何 chooser、任何鍵盤、任何第三個或重試輸入、
  任何下載、任何目的地或正式 config/state/run-log 寫入、任何非由當輪畫面推導的座標
 （含把 `(304,50)`、`(305,50)` 當 live 輸入）、S6 fallback 回 v4。`retry_budget=0`，`menu_item_budget=0`，
  `keyboard_input_budget=0`，`conversation_images=0`。
- 前置條件（全須成立，否則零輸入）：LINE（`jp.naver.line.mac`）在相簿列表、目標卡可見
 （`2024/05/13～05/17`、57 張）、無選單／對話框／chooser／viewer／權限提示；gate-5＋本 runbook＋ledger skeleton 已凍結並 commit；
  v5 工具集＋自測＋離線重播雙列已凍結（見下）；ledger parent＝attempt-06 FINAL `906c1433…`。
- 開跑前：LINE 停在相簿列表、目標卡可見；跑時不動滑鼠鍵盤；選單彈出後由 owner 自行關閉（agent 不點任何選單項目）。

## 凍結工具集（輸入前已凍結；任何位元組變動＝TASK_REGRESSION）

- `tools/v5/vision_reader.py` `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8`（v4 位元相同）；
  `tools/v5/locate_album_card.py` `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162`（v4 位元相同）；
  `tools/v5/verify_album_open.py` `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`（v4 位元相同）；
  `tools/v5/locate_album_ellipsis.py` `6a015ea65058fe6c43a66fa07714e8f887e05507258d3a949f6f6807556b6418`（v5 修正版）；
  `tools/v5/README.md`（修正幾何、被拒聯集、depth-60 理由、重播指令）；
  `vision/vision_ocr.swift` `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`；
  `selftest/v5/selftest-summary.json` `e207f5029940d90b7cfae379ef67bddd3c976abebb12d6772c111c93dea5d5bf`（21 cases、`cases_failed 0`、`result PASS`，含修正正例＋四 v5 專屬負例＋5× determinism＋v5 工具 SHAs）；
  v4 工具集＋v4 自測 `5ad2be10…`（16/16）維持凍結；v3 自測 `17840e91…`（13/13）維持凍結，不用於本 run 裁決；
  detector `detect_menu_popup.py`（`6ae9c250…`）與其凍結自測腳本 `selftest/selftest_menu_popup.py`（`db091703…`，4,018 B）原樣重用（tesseract 版；reader-block 豁免）；
  凍結自測 summary `selftest/selftest-summary.json`（`d8ffc129…`，2,946 B）以該身分登錄（§24.8 文字更正）。
- 離線重播（耐久，零 GUI；gate-5 凍結前完成）：v5＋已入庫 post 幀 `4cb8a6b4…`（`--title-bbox 15,83,204,111`）→ `ELIGIBLE`、`ellipsis_dots [[304.5,44.0],[304.5,49.5],[304.5,55.0]]`、`click_point [304,50]`（`attempt-07/v5-offline-replay.json`）；v4 位元＋同幀 → `NO_ELLIPSIS_FOUND`（`attempt-07/v4-baseline-replay.json`；attempt-06 `album-ellipsis-locate.json` 為對照）。任何其他 verdict 或座標＝TASK_REGRESSION。
- v5 位置規則：census／dot／triple／text-blocking 與常數（delta 45、flat-tol 25、flat-fraction 0.6、max-area 16、max-side 5、text-margin 6）與 v4 相同；標題列 `band = {x0: tx1+2, x1: width-1, y0: max(0, ty0-6), y1: min(height-1, ty1+10)}`（記為 `album_title_band`，其內 triple 記 `in_title_strip`，不合格）；header `header = {x0: tx1+2, x1: width-1, y1: max(0, ty0-7), y0: max(0, ty0-7-header_depth)}`（`--header-depth` 預設 60；記為 `album_header_band`）；eligible 須 middle 同時非 `inside_text`、非 group-band、落在 header 內，且恰好一個；高於 header→`above_header_band`；低於 strip→`below_album_title_band`；header 內但左緣以左→`header_left_of_title`。Exit codes 0/2/3/4/5/6 不變；僅群組→`GROUP_LEVEL_ONLY`。被拒聯集（strip ∪ header）理由見 README。
- ledger parent：attempt-06 FINAL `906c14330605122e9b600359892d4400171d62564707d50af26ef8d8bb32fa2c`（其 parent `17b17203…`）；預算鏡射 gate-4（album_card 1／navigation 1／ellipsis 1／retry 0／menu_item 0／keyboard 0／app_acquisition 0／conversation_images 0；`click_count_per_input 1`；唯讀觀察窗 ≤5；擷圖 ≤5，輸入#2 後約 4 秒）。

## 步驟（逐步記證；任何偏離＝SAFE_ABORT）

S1. **Binding read（零輸入）**：`getApp("jp.naver.line.mac", {emit:false})` →
    `getScreenshot({emit:false})` 寫 `/tmp/route7_frame_pre.jpg`（記 bytes／尺寸／SHA-256／擷取時間）；
    `getAXState({emit:false, disableDiffing:true})`（記 SHA）。
S2. **Screen-scope 探針（恰一次；唯讀）**：`screencapture -x /tmp/route7_screen_probe.png`。
    接受條件：exit 0、可解碼、且凍結 v3 `locate_album_card.py` 對「AX 視窗 bounds 裁切」在 scale 2
    或 scale 1 得到 `ELIGIBLE`；記錄所採 scale。否則 `screen_scope=UNAVAILABLE`（SUPPORTING、非致命，
    run 以 window-scoped 續行）。探針後若觀察到新的系統權限對話框 → `PERMISSION_PROMPT_OBSERVED`、
    `SAFE_ABORT`、不送任何輸入。產出 `evidence/20260916-route/attempt-07/screen-probe.json`
    （v3 screen-probe JSON；reader-block 豁免）。
S3. **卡片定位（唯讀；凍結 v4；不得以歷史座標跳過）**：`/opt/homebrew/bin/python3
    evidence/20260916-route/tools/v4/locate_album_card.py /tmp/route7_frame_pre.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57
    --out evidence/20260916-route/attempt-07/album-card-locate.json`。僅接受
    `verdict=ELIGIBLE`；否則 `SAFE_ABORT`，不送輸入。**本 JSON 必須帶 v4 `reader` block**。
S4. **輸入 #1**：於 S3 的 `click_point` 送恰好 1 次正常左鍵（相簿卡 metadata 點）；
    同時計入 `navigation_inputs` 與 `album_card_inputs`。
S5. **立即 post 觀察（零輸入）＋開啟驗證（凍結 v4）**：`getScreenshot` → `/tmp/route7_frame_post.jpg`；
    `/opt/homebrew/bin/python3 evidence/20260916-route/tools/v4/verify_album_open.py
    /tmp/route7_frame_pre.jpg /tmp/route7_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 --delta 12
    --out evidence/20260916-route/attempt-07/album-open-verify.json`。
    僅 `ALBUM_OPEN_VERIFIED` 續行；否則記證、通知、停止（不得送 ⋮ 輸入）。**本 JSON 必須帶 v4 `reader` block**。
S6. **相簿內 ⋮ 定位（唯讀；v5；唯一座標來源；不得 fallback v4）**：`/opt/homebrew/bin/python3
    evidence/20260916-route/tools/v5/locate_album_ellipsis.py /tmp/route7_frame_post.jpg
    --expect-start 2024/05/13 --expect-end 2024/05/17
    --title-bbox <S5 的 target title bbox> --expect-group-title 「旻謙允禎成長日記」 --header-depth 60
    --out evidence/20260916-route/attempt-07/album-ellipsis-locate.json`。
    僅 `ELIGIBLE`（header 內恰好一個）准許 ⋮ 輸入，其 `click_point` 為唯一座標來源；
    歷史座標（含 `(304,50)`、`(305,50)`）永不作 live 輸入；
    `NO_ELLIPSIS_FOUND`／`AMBIGUOUS_ELLIPSIS`／`GROUP_LEVEL_ONLY`／`TARGET_TITLE_NOT_FOUND`／`BAD_FRAME`／reader 失敗 → 無 ⋮ 輸入：記證、通知、停止。
    **本 JSON 必須帶 v4 `reader` block**（v5 目錄的 v4-reader 副本；detector 豁免）。
S7. **Pre 幀擷取（零輸入）**：`getScreenshot` → `/tmp/route7_frame_pre_menu.jpg`（記 SHA）。
S8. **輸入 #2**：於 v5 S6 的 `click_point` 送恰好 1 次正常左鍵（相簿層 ⋮；只為讓選單出現）。
S9. **Post 觀察（零輸入）**：輸入#2 後約 4 秒內至多 5 次 `screencapture -x`（記每幀 SHA）＋ `getAXState` 重讀。
S10. **選單轉錄（唯讀；凍結 detector）**：凍結 `detect_menu_popup.py`（`6ae9c250…`）對每組凍結 pre/post（screen pre-menu vs 各 post；app pre vs app post）＋ AX 重讀。
    僅新的 AX 選單元素或 `MENU_DETECTED` 為 `AFFIRMATIVE`；OCR-only／human-only／不完整 → `UNKNOWN`，永不 AFFIRMATIVE。
    產出 `menu-analysis.json`（detector JSON；reader-block 豁免）。選單只觀察、不點任何項目（明列 Save All）；可留開，由 owner 關閉。
S11. **收尾（耐久）**：寫 `route-result.json`／FINAL `run-ledger.json`／`manifest.json`／耐久執行紀錄
    `.agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev24.md`
   （另含 `album-card-locate.json`、`album-open-verify.json`、`album-ellipsis-locate.json`、`screen-probe.json`、`menu-analysis.json`）；commit；通知 owner。
    未達結果的停止不寫 `route-result.json`／`manifest.json`；ledger、工具 JSONs 與幀雜湊即紀錄。
    attempt-05／06 凍結 verdict 永不重評。

## Resume 與停止

- 零輸入停止（preflight surface 失敗、能力不可用）可以同一份未耗授權重排（resume-eligible），不是路線結果、不改狀態。
- 輸入#1 已耗而後停止 → 不再授權輸入#2；該輪誠實關閉（`CLOSED_AFTER_INPUT_1` 或對應 ledger state）。
- 累計失敗 5 次 → 停，不再開新 attempt；任何語意變更、權限提示、surface 不符、未授權動作需求、同一根因連敗或 v5 不可靠證據 → 停、記證、通知。
