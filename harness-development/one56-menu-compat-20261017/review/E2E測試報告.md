# ONE56 真實選單相容性 E2E 測試報告

本報告是進行中的證據交接。尚未完成的步驟明列 NOT_RUN；離線測試與診斷觀察不代表正式備份成功。公開版本移除個人群組名稱、本機帳號、家庭照片與私有授權內容；原始畫面、AX、OCR、原生收據及雜湊保留在本輪 private 證據目錄，由獨立驗收者直接檢查。

## 意圖與範圍

修復真實 LINE 相簿網格右上角選單與現有程式的相容性：找到實際三點控制、辨識浮動選單的「儲存全部」，並安全關閉或恢復同一本網格。原先假設存在 AXButton / AXMenuItem，以及 Escape 後一定留在同一網格，都必須以真機證據核對。

外部 Chief 已閱讀的 PR HEAD 為 `d27c80b7d9ebecc9c170353110263971adc83f99`；產品實作為 `8bebd236d57bb80e39bfca163c67b9cecba1d36f`。[完整 Chief 審查](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5557707124)僅接受 B1/B2 來源切片，結論為 `CHANGES_REQUIRED_FOR_LIVE_SAVE_ALL`。本輪不把此審查改寫為新版實作核准。

後續外部 Chief 對精確 HEAD `4bbec71fee690f9b88fb91837924b7f75db5301f` 再次給出 `CHANGES_REQUIRED`（[review 5558490383](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5558490383)），兩個 deterministic blocker 為 `MENU_ROW_ORDINARY_CACHE_MISMATCH`（M5）與 popup／label 超出 hosted CUA crop（M6）。本報告後段＜M5／M6 最小修正＞即為針對這兩點的處理與驗證。

本次可逆診斷有獨立且不可變的 `MENU56-REVERSIBLE-20261017-01` 證據資料包。它只記錄 Owner 已授權的診斷範圍，不是正式交易 grant，不會 begin lifecycle、取得 writer、提交 intent、按 Save All、操作 chooser 或更動 canonical ledger。Owner 本輪已明確交還 LINE 前景。

## 角色與獨立性

根代理負責規劃、範圍、整合及最終判定。實際啟動 `gpt-6-luna / high` 進行最小源碼修正，並啟動另一個 `gpt-6-luna / xhigh` 進行獨立計畫檢查與真機驗收。獨立驗收者沒有產品源碼寫入權，並獨佔本輪 CUA GUI 操作；根代理與實作者不並行操作 LINE。外部新版精確來源審查仍須由使用者選定的雲端模型實際完成。

## 保護基線

正式狀態 revision 35，active batch / writer / context lock 皆為 null。歷史兩本 VERIFIED 合計 239 張。人工備份的 65 張相簿排除；本輪目標為 2024-05-27 至 2024-05-31、56 張。原 canonical task / Owner / ledger / initialization / grant 及舊觀察額度保持原狀。

- 狀態 SHA-256：`455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`
- canonical ledger SHA-256：`08aa18e42bfee7a8e4d0529bac5b793d830efc1127794dac4baa8f4bdb9864e2`
- 舊來源 closure SHA-256：`ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`
- 操作前已逐一記錄 245 個保護檔案雜湊；原始 dirty worktree 另外留存 diff，所有產品修正在既有隔離 worktree 進行。

## 真機證據鏈與目前結果

採用真正 hosted CUA 取得原始 JPEG / AX，並使用只讀 AX/CG 與 ScreenCaptureKit/Vision 工具保留實際 LINE PID、視窗、完整顯示器畫面及 OCR。工具不包含輸入、交易或授權繞過功能；來源、編譯退出碼、執行檔與實際輸出 SHA-256 另見 runtime 證據。

初始真實 CUA 擷取時間為 2026-10-17T12:14:29.796Z；畫面 SHA-256 為 `da605c7d71557e1cade2c15d74e8c697f4d8970b0940508c154c23bea2c36c42`。上方人工備份 65 張卡片可見，56 張名稱仍部分位於畫面外，因此沒有猜點或點進 65 張。獨立驗收者只執行到達指定相簿所必需的有界導覽，不重新研究已驗證的 scroll 可行性。

第三次（最後）關閉探針已於 2026-10-17 14:11–14:15Z 完成；所有輸入皆先經新鮮 native／CUA 綁定，逐項留存收據：

- 外部狀態變化（非本輪輸入）：14:03Z 仍存在的 detail 6916 最遲於 14:06:19Z 消失、列表回到頂端（scrollbar 225→0）。本輪在送出任何輸入前依專案憲法主動 STOP，收據 `22-probe3/STOP-receipt-abort-before-input.json`（sha256 `0603e83ac1aea732c215a98c5cc6dfec87269b421d8607d925160ba5d7ab2792`）。Owner 以選項 A 授權有界恢復＋探針並再次交還前景。
- 有界恢復：hosted CUA `app.scroll(2,'down',0.25)` 兩次；native scrollbar 0→112→225（與前輪一致）。每次皆有新鮮前後畫面；65 卡日期／張數列全程保留為唯一有序 overlap；56 卡於 225 完整呈現 `2024/05/27〜05/31`、`56`。
- 點擊 1（名稱文字 [143,1152]，非縮圖、非 ⋮、非 + 按鈕）：開啟全新 detail 7349 [358,46,327,643]；畫面與前輪已驗證 detail 畫面逐位元相同（sha256 `3677b3cc976f1b0f0cc36e1138b172927a8d8c32e0dbd86b99f785d3b08f26b3`），`56張照片`、`2024.06.01` 與網格一致。
- 點擊 2（⋮ [610,99]，4× 裁切確認點心）：開啟唯一 LINE 所有 layer-101 popup 7359 [641,98,137,167]；SCK/OCR 讀出五行（選擇項目／修改相簿名稱／**儲存全部**／刪除相簿／分享相簿），幾何與前輪 popup 相同；未啟動任何列。
- 點擊 3（標題靜態文字 [218,195]＝新鮮 SCK OCR 內縮中心）：popup 7359 消失、detail 7349 保留，標題與網格不變；未出現對話框／chooser。`POPUP_DISMISSED_BY_TITLE_CLICK=YES`（native 14:15:07Z＋SCK＋CUA 三重確認）。
- 對照結論：同一 ⋮ 再點一次（前輪）不能關閉；Escape（前輪已證）會同時關閉 popup 與 detail 並回到列表。本輪未使用 Escape。
- 狀態不變：`REAL_SAVE_ALL_DISPATCH_COUNT=0`；無 chooser／下載／intent／ledger／grant 寫入。本輪 GUI 輸入共 5 次（2 scroll＋3 click），全部正常返回、零重送。

原始收據位於 `private/independent-live-01/22-probe3/`：30／31／32／33（新鮮前置與 SCK）、40–42（scroll1）、50–54（scroll2）、60–65（名稱點擊與 detail 開啟）、66–73（⋮ 與 popup）、74／74b／75–79（標題關閉探針）。公開版僅去識別；完整雜湊與畫面留在原始目錄供獨立審查核對。

## 本輪最小來源修正與離線驗證（2026-10-17 後段）

Owner 追加授權只涵蓋「最小來源修正＋針對性回歸」。probe3 之後本輪未再對 LINE 送出任何 GUI 輸入（輸入次數為 0），所以下列結果全部屬 ENABLER 等級的離線證據，不得當成真機 PASS。

### 修正內容

- `scripts/line_backup_cua_adapter.mjs`：hosted session 新增 `collectMenuEnvelope` 注入；`observe(checkpoint,{menuEnvelope:true})` 直接呼叫 envelope collector，不再經一般 classify 包裝；缺 collector 時以 `MENU_ENVELOPE_COLLECTOR_REQUIRED` fail-closed。
- `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs`：唯一 1 行接線（把 classifier 的 `collectMenuEnvelope` 傳入 hosted session）。此檔不在原凍結五路徑內，屬前一輪申報之 scope amendment；外部審查 5558490383 已將此接線列為 in-scope 接受。
- `.../mac/analyzer.mjs`：修正三個真機診斷得到的缺陷：(a) 浮動選單候選改為「LINE 所有且實際被抬升的 CG layer（cgLayer>0）」恰一個、允許與 detail 相交，其餘上層視窗才套用原本 occlusion 規則；(b) `MENU_ENVELOPE_WINDOW_MISMATCH` 改與 detail 自身 window 比對；(c) 座標轉換修正：新增 `cua_scale`／`cua_offset_px`，popup 與 save-all 列同時輸出 `cua_bounds_px`／`cua_label_bounds_px`，`safe = crop ∩ popup_cua ∩ label_cua`（erode u+4）。這三項先前在真機上分別造成 popup 找不到、identity 誤判與點位換算錯誤。
- `.../mac/classifier.mjs`：envelope record 增加 `captured_at`；驗證改用 `cua_*` 邊界與 `cua_offset_px`／`cua_scale`，transform drift ≤1 px，`safe ⊂ popup_cua ∩ label_cua ∩ crop`。
- `.../mac_runtime.mjs`：`locateSaveAllRow` 改用 popup／save-all 的 `cua_*` 邊界；修 closure context key（原以 `detail.frame_id` 寫入、卻以 menu frame 讀取）。
- `src/line_backup_batch/service.py`：把同一契約移植到正式 Python 驗證器（`menu_envelope`、`menu_envelope_support`）：envelope 19 鍵與 native/popup/layer/row/mapping/OCR 綁定、trigger 9 鍵＋`PIXEL_STRUCTURE`＋`component_count>=3`、closure proof 驗 native popup 消失＋新鮮 OCR。移植過程中由測試抓到自身兩個缺陷並已修正：缺少 `inside` 匯入（會以 NameError 而非 typed `AcceptanceError` 失敗，違反 fail-closed）與 `menu_support` 與既有區域變數同名（`UnboundLocalError`）。
- `tests/test_cua_adapter.mjs`：ROW locator mock 補 `popup_window_id`／`popup_layer`。
- `tests/test_batch_authority.py`：兩個 calibrate 呼叫點改用 adapter 等價 fixture（envelope record、trigger、closure proof）；`safe` 改為交集結果 `[40,26,28,28]`、save-all 點改為 `[54,40]`。

### 驗證結果（可重跑）

- `node --test tests/test_cua_adapter.mjs` → 42/42 pass（多次重跑）。另有既有不穩定案例 `SCROLL_CAPTURE_TIME_ORDER`（本分支與基線 d27c80b 皆曾於重跑出現；2026-10-18 新鮮重跑：合跑綠，單檔首跑觸發、立即重跑即恢復），與本輪差異無關。
- `node --test tests/test_detail_grid_name_target.mjs` → 5/5；`test_single_album_entry.mjs` → 2/2；`test_visual_diagnostic.mjs` → 6/6；`test_visual_diagnostic_clock.mjs` → 1 skipped。
- `PYTHONPATH=src LINE_BACKUP_BATCH_TASK=<task> python -m unittest discover -s tests -p 'test_batch_authority.py'` → 37 tests、1 failure、1 skip。同一 worktree 修正前為 1 failure＋1 error（該 error 即本輪新增的 adapter 等價測試），現已修復。
- 其餘 8 個 Python 模組（排除 `test_project_binding.py`）→ 103 tests、1 failure、1 skip。
- 唯一 failure 是既有紅燈 `test_project_receipt3_download_and_pinned_decode_finalize_positive`（`GROUNDING_AX_SCROLL_RANGE`），已在基線 d27c80b 重現。根因更正：不是 Python 3.11/3.13 差異，而是測試本地合成 fixture `project_native_shaped_observation` 落後正式 `observations.py` 契約（AX scroll bar 元素缺 `minimum_value`／`maximum_value`／`native_node_id`，classifier evidence 缺 `detail_identity`）。此問題既有且與本輪無關，本輪不修改；該測試中的 calibrate 呼叫點已同步更新，但在 fixture 修好前屬未執行（UNVERIFIED）。
- `tests/test_project_binding.py` 需要 `LINE_BACKUP_INSPECTION_TEST_ROOT` 指向已備妥的 `project_binding_seed` 目錄；一般 discovery 下出現 31 個 setup error，基線相同，屬環境設定而非回歸。

### 尚未取得真機證據的部分

`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`：analyzer／classifier／mac_runtime 三個修正目前只有離線回歸與既有真機畫面的重播驗證，尚無新的 hosted capture 證明 envelope 能在真機產生並通過 Python 驗證器。`REAL_SAVE_ALL_DISPATCH_COUNT=0`、`CHOOSER=NOT_RUN`、`FORMAL_MENU_CALIBRATION=NOT_RUN` 全部不變。

下一步（須 Owner 重新授權）：在新鮮前景交接下，對既有 popup 做一次唯讀 hosted envelope 擷取＋同一標題關閉恢復的 bounded 診斷；envelope 通過後才依既有 gate 進入正式 calibration／Save All 交易。

## M5／M6 最小修正（2026-10-18，離線；零 GUI 輸入）

外部審查 `5558490383` 綁定精確 HEAD `4bbec71fee690f9b88fb91837924b7f75db5301f`，兩個 deterministic blocker：

- M5 `MENU_ROW_ORDINARY_CACHE_MISMATCH`：`menuEnvelopes` 與 ordinary cache 不相容，ROW locator 仍呼叫 `cached(frame)`；截圖同 hash 時誤用 stale detail、不同 hash 時直接 `FRESH_CLASSIFIER_FRAME_REQUIRED`。
- M6 `POPUP_LABEL_OUTSIDE_HOSTED_CUA_CROP`：真機 popup／標籤本來就超出 654×1286 的 detail CUA crop；要求全框 containment 會讓座標永遠無法成立。

### 修正內容（相對 4bbec71）

- `.../mac/analyzer.mjs`：新增 `analyzeMenuFrame`（只產生 evidence-only `MENU_FRAME_FACTS`）與 `buildMenuEnvelope`。`safe = crop ∩ popup_cua ∩ label_cua`，erode u+4；popup／label 各自與 crop 的交集需 ≥16×16；SCK 與 CUA 兩空間同時出現該列時必須一致（≤2 px）；重複列、離屏、空間衝突一律 fail-closed。
- `.../mac/classifier.mjs`：`collectMenuEnvelope` 改用新介面；菜單框以自身 `capturedAt` 與 layout signature 建立 geometry 並走既有 `frameSupport`；envelope 只存 `menuEnvelopes`（`evidence_only=true`、`admissible_to_ordinary_classifier=false`），任何路徑都不寫入 ordinary cache。
- `.../mac_runtime.mjs`：ROW 分支移除 `cached(frame)`（M5 根因），改讀 `classifier.menuEnvelopes` ＋新鮮 `detail`（`surface==='ALBUM_DETAIL'`、`window_id`、`layout_key`）；寬高取 envelope 自身 `mapping.crop_px`；`row.layoutKey = detail.layout_key`；關閉點改為獨立 `locateDismissRow`（標題 OCR 列內縮、與 popup 交集不相交、永不點 Save All 列關閉）。
- `scripts/line_backup_cua_adapter.mjs`：ROW 校驗改比 `detail.layout_key`。
- `src/line_backup_batch/service.py`／`observations.py`：正式驗證器改交集語意（popup_cua／label 僅需正尺寸；`safe` 必須等於 crop∩popup∩label，容差 1e-6；測試註解記有二進位浮點殘差 7.1e-15（`tests/test_menu_envelope_intersection.mjs`），非真機量測值）；新增 `PROJECT_CALIBRATION_CLICK_POINT`：`save_all_point` 必須等於 validated `eroded` 中心（±1 px，容許 JS 端 `Math.trunc`）。
- 新測試 `tests/test_menu_envelope_intersection.mjs`（6/6 pass）：以 probe3 真機實測數字（popup／label／safe／eroded／click `[635,272]`）驅動真實 `buildMenuEnvelope` 與真實 `locateSaveAllRow`；含 popup 離屏、label 離屏、重複列、空間衝突、facts 種類錯誤等負例。
- 既有測試更新：`tests/test_cua_adapter.mjs`（ROW stub 收 `detail`、envelope stub 補 `mapping`／`captured_at`）；`tests/test_batch_authority.py`（+3 測試：真實形狀正例、safe 非交集負例、raw rect 壞值負例）。

### 獨立稽核（read-only subagents；稽核後僅文件更新，產品源碼未再修改）

- 欄位 parity PASS：`buildMenuEnvelope` 回傳 ↔ `collectMenuEnvelope` 存取／回傳 ↔ Python `MENU_ENVELOPE_INNER_KEYS`／`MENU_ENVELOPE_RECORD_KEYS` 一致；adapter ROW 期望與 `locateSaveAllRow` 回傳一致；並以正式 Python validator 對真實 JS envelope 實際執行交叉驗證通過。
- M5 證明 PASS：ROW 路徑無任何 `cached(`／`classifier.cache`；只有 `classify()` 寫 ordinary cache；menu 框從不進入。
- M6 證明 PASS：menu 路徑無全框 containment；`save_all` 只能是 validated `eroded` 的中心，Python 再以 1 px 綁定，off-crop 點位結構上不可能。
- Swift↔JS 欄位：rev28 sidecar 的 `candidate_count`／`bounds` 與 JS 讀取完全一致；`analyzeMenuEnvelope` 舊名在工作樹與主 repo 皆已不存在。
- 已知覆蓋率殘留（未修）：真實 `collectMenuEnvelope` → 真實 `menuLocator` ROW 全鏈仍由 stub 取代，無端到端單元測試；review 要求的 identical／different CUA hash 情境在新設計已互不相依（moot），目前以靜態稽核與純函式測試佐證。
- 其他殘留（非本輪阻塞）：Python 未交叉比對 record 與 inner 的 `uncertainty_px`（實際 collector 同源，latent）；`mac_runtime.mjs` `intersectionRect` 為未使用死碼；`test_cua_adapter.mjs` 內另有一個不再執行的 mock envelope 分支。

### 驗證結果（可重跑）

- JS 逐檔：`test_cua_adapter.mjs` 42/42、`test_detail_grid_name_target.mjs` 5/5、`test_single_album_entry.mjs` 2/2、`test_visual_diagnostic.mjs` 6/6、`test_visual_diagnostic_clock.mjs` 1 skipped、`test_menu_envelope_intersection.mjs` 6/6；`node --check` 六個改動檔全數 OK。六檔合跑（2026-10-18 新鮮重跑，exit 0）62 tests／61 pass／0 fail／1 skip；單檔 `test_cua_adapter.mjs` 首跑曾觸發既有 flake `SCROLL_CAPTURE_TIME_ORDER`、立即重跑 42/42 pass（基線已存在，與本輪無關）。
- Python（`test_batch_authority.py`，`unittest discover -s tests -p 'test_batch_authority.py'`）：`Ran 40 tests`、1 failure、1 skip；3 個新測試全 ok。唯一 failure 為既有 `GROUNDING_AX_SCROLL_RANGE`，已於 pristine 基線重現。
- 全部屬 ENABLER（離線）；真機狀態不變：`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`、`REAL_SAVE_ALL_DISPATCH_COUNT=0`、`CHOOSER=NOT_RUN`、`FORMAL_MENU_CALIBRATION=NOT_RUN`。

## 新發現阻塞：frame-support 錨點離散門檻對 654×1286 detail crop 全數拒絕（2026-10-18，offline CONFIRMED；未修）

M5／M6 修正完成後、獨立稽核期間新增一項與 M5／M6 diff 無關的獨立發現，列為本輪已知限制與下一個決策點；本輪不修改。

- 機制（production 原始碼）：`frame-support` 的 `AutomaticOcrAnchorMapper.derive`（`rev28/Sources/Rev28Core/Perception/OcrEngine.swift:217` `minimumTriangleAreaFraction = 0.02`；`:259` `guard anchors.count >= 3`；`:270-272` 最大三角形面積 ÷ crop 面積 `< 0.02` 即 `throw .anchorsNotDispersed`；呼叫端 `rev28/Sources/rev28ctl/main.swift:1335-1337`）。對 654×1286 detail crop，門檻為 16,820.88 px²。
- 真機保留幀重播（真碼、真幀；以已編譯 `Rev28Core` 產物驅動 production `VisionOcrEngine` 與同一 `derive`）：71（menu-open detail crop）對 73（SCK 幀）shared anchors 4、最大三角形 10,704.245 px²（ratio 0.0127）→ `DERIVE_REFUSE anchorsNotDispersed`；74 對 73 同值（deterministic）；66 對 68（menu 開啟前 detail）3 anchors、61.94 px²，亦拒。
- 影響：`mac/classifier.mjs` 的 `collectMenuEnvelope` 與一般 `classify()` 走同一 `frameSupport` 路徑；此拒絕非 menu 專屬，屬一般 ALBUM_DETAIL crop 風險，live 會以 `NON_MENU_SCK_SUPPORT_REFUSED` 呈現，直接擋住 menu envelope 與正式 Save All 前置。
- 證據界線：offline 已證實（production 常數＋已編譯核心＋真機保留幀）；尚未 live 重驗（`frame-support` CLI 需 live 授權鏈與 ≤5 s 新鮮擷取，線上驗證本身屬正式前置流程的一部分）。修復須動 rev28 Swift 門檻／策略，超出本輪凍結路徑，需另行 bounded plan 與獨立審查。
- 收據（未納入版控、不在 PR #10 內；留存於本機供獨立核對）：driver `harness-development/one56-menu-compat-20261017/private/anchor-dispersion-20261018/driver.swift`（sha256 `2c520fc05e224bea09ccab8da1464edc8a14f775e8931b5969a25c1a613ab695`）；輸出 `out-71-vs-73.txt`（`52067000b8761226d76523009217351661bd17b36b2893a272a24b87908b1852`）、`out-74-vs-73.txt`（`640b9e7d12c327f88f5dd0dd82a8875939742d0c99347581452c7a518061fc83`）、`out-66-vs-68.txt`（`4e6cc97d4271146271e0e578fa7a5d49555ff1498eecf732c20bf36524d11475`）。編譯產物在本機暫存區（不隨 commit）。

待決策：外部審查裁決處理順序（修 rev28 門檻／策略，或先做一次 live envelope 前置驗證）；在裁決、有效 grant 與 Owner 前景交接前，不派送任何 GUI 輸入或 Save All。

## 正式交易狀態

`FORMAL_MENU_CALIBRATION=NOT_RUN`
`REAL_SAVE_ALL_DISPATCH_COUNT=0`
`CHOOSER=NOT_RUN`
`ALBUM_A_FILES_VERIFIED=NOT_RUN`
`ALBUM_A_VERIFIED=NOT_RUN`
`ALBUM_B_VERIFIED=NOT_RUN`

任何正式 Save All 均須先有新版 exact-source positive review 與有效 runtime grant，再通過原本 duplicate、空目的地、owner、原始持久 intent、menu identity / geometry 及 at-most-once gate。結果不明不得重送。下載後須實體盤點正好 56 個穩定原圖、每張 SHA-256 與完整 ImageIO 解碼，接著 VERIFIED 提交、讀回及 release。第二本必須獨立授權及記錄，不重用 ONE56 grant。

## 未完成事項與交接

真機選單結果與安全關閉已填入上節。前一輪最小來源差異（六路徑，含 1 個 scope amendment）、針對性離線回歸與本報告已隨來源提交 `4bbec71fee690f9b88fb91837924b7f75db5301f` 推送至 Draft PR #10；本輪（M5／M6）差異見末段更新。待由使用者選定的雲端模型做獨立精確來源審查。待完成：真機 envelope 擷取（`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`）、既有紅燈 fixture 修復（與本輪無關）、獨立 bounded-plan 接受、新 HEAD／closure／native／runtime SHA、唯讀 authorizer smoke、保護資料比對及獨立驗收。Draft PR #10 保持不合併。未取得實際外部審查結果前，不宣稱正式 Save All 已解除阻塞。 前述 anchor-dispersion 發現（offline CONFIRMED、未修）同列未完成事項，處理順序待外部審查與 Owner 決策。

2026-10-18 更新：M5／M6 最小修正、針對性離線回歸與本報告更新已提交；來源修正提交為 `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`（9 檔，已推送至 Draft PR #10），其後之 doc-only 提交更新本報告與 `progress.md`；精確審查 HEAD 即 PR #10 之最新 HEAD。舊審查 `5558490383` 僅綁 `4bbec71`，不構成新 HEAD 的核准；待由使用者選定的雲端模型對新 HEAD 做精確來源審查。本輪另發現 frame-support 錨點離散門檻對 654×1286 detail crop 全數拒絕（見上節，offline CONFIRMED、未修），同列未完成事項與下一個決策點。真機狀態不變：`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`、`REAL_SAVE_ALL_DISPATCH_COUNT=0`、`CHOOSER=NOT_RUN`、`FORMAL_MENU_CALIBRATION=NOT_RUN`。Draft PR #10 保持不合併；未取得新 HEAD 正式核准與有效 ONE56 grant、且 Owner 未再次交還 LINE 前景前，不派送任何 GUI 輸入或 Save All。

## 2026-10-18 續測：新鮮唯讀現況與錨點根因細分

本節為 Owner「繼續或重新進行測試」後的新結果。對帳基線為 `91c85617c2e943037caa41188c26f1474a3e56d6`；既有產品來源修正為 `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`，本節沒有再修改產品源碼或測試。時間以 UTC 標示（本地日期為 2026-10-18，Asia/Taipei）。本輪實際執行的 Luna/high 只做唯讀根因分析；Luna/xhigh 獨立取得新鮮真機唯讀證據，不把既有提交的作者／模型來源歸到本輪代理身上。

### 新鮮 Mac 現況（有工具執行；零輸入）

- 2026-10-17T19:12:48Z 原生快照：LINE `jp.naver.line.mac` 在前景，PID 25266；唯一 on-screen 視窗 3766 `[21,46,327,643]pt`。沒有前輪的 56 張獨立 detail 視窗。
- 19:14:28.821Z hosted CUA `getAXStateAndScreenshot`：目前是同群組的相簿列表頂端；可見 2024/06/02–06/07、65 張人工備份排除相簿，下張卡片部分可見，56 張的名稱／數量未出現在視窗內。原始 JPEG 654×1286，SHA-256 `da605c7d71557e1cade2c15d74e8c697f4d8970b0940508c154c23bea2c36c42`。與早先頂端畫面同 hash，不等於同一次 capture；本輪時間與原始 AX 另行保留。
- 全量 hosted AX 為 `showing 0-100 of 101 items`，SHA-256 `7aacccb12001d6676e37597e7c2495b058e3aee44fce8ef2a7fbd1cdd0be0028`。獨立驗收者初看截短 native 輸出曾估為 21 列，已在 append-only addendum 更正，未覆寫原始紀錄。
- `STOP_INPUT`：沒有 activate、scroll、click、按鍵、menu、Save All 或 mapper 派送。本輪未取得 fresh 56 detail，故 `FRESH_DETAIL_MAPPING_RETEST=NOT_RUN`。兩個被動讀取不是 ≤5 秒的正式 SCK/CUA pair，沒有把它們標為正式 calibration 或 E2E PASS。
- 原始相對路徑：`private/independent-live-01/26-current-20261018-readonly/`。完整本機路徑與逐檔 SHA 保留於私有收據；公開 [runtime／證據清單](resume-runtime-evidence-20261018.json) 只保留去識別化的相對路徑及 hash。

### 真正 production OCR／mapper 對保留真幀的唯讀重播

本輪沒有重跑完整 synthetic matrix。新增的 [唯讀重播 driver](anchor-roi-replay-driver.swift) 使用既有 `VisionOcrEngine` 與 `AutomaticOcrAnchorMapper.derive`；固定 native bounds 是該組歷史幀的實測資料，僅供離線重播，絕不可當作新的 GUI 點位或有效 runtime grant。[71/73 輸出](anchor-roi-71-vs-73.txt)與 [66/68 輸出](anchor-roi-66-vs-68.txt)均與私有原檔逐位元一致；輸出只列文字類別與幾何，不含人名／群組／照片。

| 實際策略（診斷比較，非 policy 變更） | 71/73 結果 |
| --- | --- |
| 原 production 全螢幕、exact-text 配對 | 4 anchors；相簿日期誤配背景列表，residual **1215.032 px**；derive 先以 `anchorsNotDispersed` 拒絕 |
| 只保留已知 detail 的 SCK ROI | 排除背景錯配；3 anchors；最大 residual **2.944 px**；三角形比例 0.00007364 |
| detail ROI ＋日期分隔符診斷正規化 | 4 anchors；正確標題 residual **2.676 px**；最大 residual **2.944 px**；比例仍 0.012727 < 0.02 |

66/68 重播得到同樣的限制。這修正了「只是 2% 面積門檻太嚴」的單一根因說法：全畫面字串配對可能選錯背景實體，OCR 框中心本身也未滿足現行 2px 約束。單純降低面積門檻、只加 ROI 或只把 `〜` 換成 `~` 都不能解鎖既有 gate。本輪沒有修改 2px、0.02、sidecar、grant 或任何正式 validator，也沒有將上述替代策略標為 PASS。

### 來源、runtime、資料完整性及下一步

- 21 檔候選來源 closure：`be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`。canonical 已安裝 closure 仍為 `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`；兩者明確區分，未偷換成同一套 runtime。
- 實際已安裝 producer SHA-256 仍為 `9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20`，decoder 為 `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`。本輪沒有 native production build、runtime 重綁、新 grant 或 authorizer smoke；不將舊 SHA 當作新實作的執行核准。
- 19:07:43Z 逐檔核對 245 個保護檔，差異 0；revision 35，active batch／writer／context lock 皆 null。canonical ledger、初始化收據、原 grant、設定、歷史 239 張 VERIFIED 圖檔及原有 dirty 工作均未由本輪改動。
- 舊外部 review 5558490383 是 `CHANGES_REQUIRED`，僅綁 4bbec71；7debc2 及後續 docs HEAD 沒有正面外部實作核准。Luna 的本機安全／分析檢查也不等於外部 `APPROVE_PLAN`。新的影像對位證據策略若改變驗收契約，依最新 AGENTS.md 須先由 Owner 轉交外部 ChatGPT 做 Plan Review，實作後再做 exact-source Code Review。
- 本輪只提交新證據、根因分析與可審查的下一步；保持 Draft、不 merge。正式試跑仍應在有效審查／runtime 授權／當次前景交接後，直接完成 A 的連續交易，再另建 B 的獨立交易，不新增無資訊增益的 menu 研究。

本輪的 [bounded Plan proposal／完整根因分析](../anchor-fix-analysis.md) revision 為 `ANCHOR-DETAIL-R1-20261018`，SHA-256 為 `f0518fc3fd0bc8103401168476d1e23b505d1e8d539751bf62cfdfa30a2f7094`。程式查核未找到可直接重用的跨影像像素配準能力；現有 VisualDiagnostic 也呼叫相同的 OCR mapper。因此提案明列「演算法未經實證」與停止條件，請外部 Reviewer 判定是否接受僅限 ALBUM_DETAIL 的 hash／native-lineage 綁定像素對位證據契約。這不是本機已核准的實作 Plan，也沒有新 production build 或新 guard 行為。真實重播使用既有本機 debug/core 產物，與已安裝 producer9ef75efe 的身份分開記錄；不冒稱已安裝 producer 執行過該重播。

`PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`
`IMPLEMENTATION_STATUS=M5_M6_PREVIOUSLY_PUSHED; ANCHOR_FIX_NOT_IMPLEMENTED`
`CORE_ACCEPTANCE_STATUS=PRIOR_REAL_MENU_AND_TITLE_CLOSE_OBSERVED; CURRENT_READONLY_SCREEN_CAPTURED`
`REQUIRED_VERIFICATION_STATUS=FORMAL_CALIBRATION_DOWNLOAD_DECODE_VERIFIED_NOT_RUN`
`INDEPENDENT_ACCEPTANCE_STATUS=READONLY_DIAGNOSTIC_ONLY`
`TASK_CLOSURE_STATUS=OPEN_PENDING_EXTERNAL_REVIEW_AND_MAPPING_FIX`
`REAL_SAVE_ALL_DISPATCH_COUNT=0`

## 2026-10-18：外部 Plan 核准後的 P1 真幀像素配準實驗

本節追加新結果，不改寫前面的失敗、未知或原始計畫。工作基線為 `a846df01fb056b34511dad1e2ad3abb7ac152e26`（既有隔離 worktree，detached HEAD）；產品來源仍為 `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`。本輪沒有正式 GUI 輸入、產品源碼／測試變更、download 或 state mutation。實際角色：原有 GPT-6-luna/high Implementer、原有 GPT-6-luna/xhigh 獨立保留影像驗收者，均向 Sol 回報；沒有新增本機審查代理，也沒有代替外部雲端審查。此驗收不是固定新實作後的正式交易 E2E。

### 授權與審查綁定

Sol 已透過 GitHub API 完整讀取 [正式 Plan Review 5560487952](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560487952)，實際 review commit 為 `a846df01fb056b34511dad1e2ad3abb7ac152e26`，submitted_at `2026-10-17T22:51:52Z`。GitHub state 是 `COMMENTED`；Owner 提供之外部審查正文明確為 `APPROVE_PLAN`，不升格成 GitHub APPROVED 或 Code Review。

- Plan revision：`ANCHOR-DETAIL-R1-20261018`；原檔 SHA-256：`f0518fc3fd0bc8103401168476d1e23b505d1e8d539751bf62cfdfa30a2f7094`，維持不變。
- 完整 review API raw SHA-256：`9f3cc3318041dbf9686f9857899b040046e7613e059aa5524b9278c0cbb2204a`；本機相對路徑 `private/anchor-implementation-20261018-01/external-plan-review.github.json`，綁定收據 SHA-256 `b96043868fe1fef88052d02ff0086b498ad03221affe6b7647557edf6aacfea8`。
- 核准要求 P1 真實 image-content 正例及負例先行，P2 分開 Python 語義 OCR 與幾何驗證，P3 typed/provenance 與跨語言驗證，P4 literal path 最小變更，P5 新 exact-HEAD Code Review、runtime grant 與當次前景後才進入正式 A。
- Plan approval 未核准 M5/M6 產品來源，也沒有建立 grant、豁免 2px、或讓本輪取得 live Save All 權限。上節舊的「等待 Plan Review」狀態已由這份實際審查更新；原 Plan bytes 保留，不回填歷史。

### 實驗資料、程式與執行順序

讀取的是真正保留 CUA/JPEG 與 SCK/PNG，沒有重畫或合成截圖。以下路徑均相對 task root `harness-development/one56-menu-compat-20261017/`；本機完整路徑在私有報告／路徑索引，公開報告遮蔽個人根目錄、群組／人名、照片、原始授權與逐張歷史檔案清單。

| 原始資料（`private/independent-live-01/22-probe3/` 下） | 尺寸／bytes | SHA-256 |
| --- | --- | --- |
| `66-dots-pre.jpg` | 654×1286／200746 | `3677b3cc976f1b0f0cc36e1138b172927a8d8c32e0dbd86b99f785d3b08f26b3` |
| `68-dots-sck-pre/sck-frame.png` | 2294×1490／3694207 | `4ea25b3d268879a6860b2b8b6e37c10bd37e487f50ee115890933974fb5978c9` |
| `71-dots-post.jpg` | 654×1286／201359 | `8d27e6b4222d71fe17916a023078cf5c7fbb6e48cebec68aabfe494923ca5ec7` |
| `73-dots-sck-post/sck-frame.png` | 2294×1490／3661221 | `2f6f359c82dc55ec401f4704e66c0d734b26d76ad533d28b6011998fe40ffde1` |

1. 先固定 Plan／review／HEAD，對帳 canonical 與隔離 worktree、保留既有 untracked 工作；讀前置 245 個保護檔。
2. Luna/high 在獨立 task evidence 內寫入與實跑有限 NCC 診斷，讀取 ImageIO 解碼後的實際像素，沒有呼叫 native 輸入 API。native ROI 是待驗證預測，不是比對結果。
3. 初版把 row corner `[617.6859,257.8712]` 當作測試點，並以 bbox containment 冒名 hull、以整數峰值加 0.7071 作未成立的誤差界限。Sol 查核後不接受該正例；原輸出 `out-66-vs-68-pre.json` SHA-256 `525d96621916e6603da9ece2b53b293fd940286fd85bbd0346a50c3322e623f5` 保留。初版 driver 曾原地編輯，故不聲稱保留了初版 output 對應的精確 source/build hash；目前 source hash 不回填給舊輸出。原型結果不是 gate PASS。
4. 同一有界方法修正版 v2/v3 改查真實 probe3 幾何所算出的歷史候選 `[635,272]`，修正凸包／徑向絕對位移與狀態報告，加入整個 ROI 的選定 patch 重複性檢查。這是從未派送的 Save All 候選點，不是曾點過 Save All 的證據。
5. 最終固定 v3 用 pre、post、錯 ROI x+8、錯視窗四組資料執行；正向兩組由 Implementer 再播 `cmp` 一致。這是同一作者的重現性檢查，獨立重播另列，不混報。

固定 [診斷 driver](anchor-pixel-feasibility-driver.swift) 與私有 `feasibility/anchor-feasibility-v3.swift` 逐位元一致（15541 bytes；SHA-256 `f8a09bdba3f1b6043b447b3e9d0e45a2669426088e8f712503b5438506d5f671`）。實際 diagnostic binary SHA-256 `a2acc1a04ddc93f1e4b69c65b96f8010d215670ab96e05fee3524ae884619398`；它是單獨編譯的證據工具，並非正式 native producer。

實際 build 命令為 `swiftc -O <feasibility/anchor-feasibility-v3.swift> -o <feasibility/anchor-feasibility-v3>`。CLI 依序接受 `CUA SCK ROI_X ROI_Y ROI_W ROI_H TARGET_X TARGET_Y MASK_MODE`；pre 使用 `66/68 716 92 654 1286 635 272 pre`，post 使用 `71/73` 與相同 ROI/point、`post`，錯 ROI 把 x 改724，錯視窗換成 `01-sck-before-open/sck-frame.png`。完整執行資料、每組原始 output ref/hash、候選分類數與 runtime 清單見 [公開數值證據](anchor-pixel-feasibility-evidence.json)。原始 JSON 留在 `private/anchor-implementation-20261018-01/feasibility/final-*.json`。

方法為 17×17 grayscale NCC、candidate stride16、local search±8、variance≥90、peak≥0.92、非相鄰 peak gap≥0.025、徑向位移超2拒絕；另於4×4空間格選至多16個 strongest patches，在整個 ROI 做2px格的稀疏取樣比對。門檻僅是診斷候選篩選，不是經外部接受的 localization/noise model，也不是獨立連續點位誤差證明。不是每個局部 match 都有完整 ROI 唯一性證明；不把診斷程式當成 typed production proof。

### 實際結果與停止原因

| 真實資料／負例 | 局部觀察 | 最終判定 |
| --- | --- | --- |
| 66/68 pre，相同 detail ROI | 1335 個局部候選通過；median shift `[0,0]`，consensus residual0；選定16個 global checks 中15個唯一、1個重複歧義 | `REFUSE_TARGET_OUTSIDE_MATCH_HULL`；候選點 x635 超出局部 match max-x625，signed hull margin約−15.9253；該點 patch variance0，未證明 ≤2px |
| 71/73 post，排除 popup／cursor 區域 | 1326 個局部候選通過；median `[0,0]`、consensus residual0；選定15個 global checks 中14個唯一、1個歧義 | `REFUSE_TARGET_OUTSIDE_MATCH_HULL`；signed margin約−120.2395；目標位置在 SCK popup 遮擋區，未證明 ≤2px |
| pre 的 ROI x716 改724（8px位移） | accepted0；1367個 candidate 被 `DISPLACEMENT_OVER_2PX` 拒絕 | `REFUSE_INSUFFICIENT_UNIQUE_MATCHES` |
| detail CUA 對較早 list-only SCK01 的相同位置 | accepted0；1719個 low-correlation candidate | `REFUSE_INSUFFICIENT_UNIQUE_MATCHES`；這是缺少目標 detail 的真實錯畫面負例，並非完整 native lineage contract 測試 |

**P1=BLOCKED。** 零整數位移是區域內容對應的觀察；沒有成立的 subpixel/noise／target uncertainty upper bound。不是「已證明 LINE 無法配準」或所有可能方法都不成立，只是本輪有界方法無法達到核准 AC。診斷 process 正常回傳 JSON 不等於 P1 PASS。未以 native 座標、OCR 中心、丟棄失敗 anchor、降低2px／0.02或更改點位製造成功。依外部審查 P1 停止，沒有再換演算法、沒有正式 observation budget／Save All lifecycle 消耗。

### 獨立驗收與資料來源限制

Luna/xhigh 已直接讀原始影像、native／SCK／AX 與 observer source/build 收據：LINE PID25266、process launch `2026-10-16T17:43:32Z`，detail window7349 `[358,46,327,643]pt`、display1 `[0,0,1147,745]pt`／2x；native 指示的 SCK ROI 為 `[716,92,654,1286]`。post 另有 LINE popup7359 layer101 `[641,98,137,167]pt`。這些是歷史來源證據，不是 pixel proof 本身。

CUA/JPEG 沒有保留逐次 acquisition timestamp／PID／window receipt。檔案 mtime 不替代 capture time；pre SCK request14:13:48.788–49.293Z、post14:14:15.543–16.059Z，不能由約7秒差的寫檔時間宣稱 ≤5秒同步。CUA app-window crop 會漏掉獨立 floating popup，即使 popup 已開；CUA 無 popup、SCK 有 popup 是跨 provider 遮擋差異，本身不證明兩幀間曾改變選單狀態。歷史實驗可以量測像素性質，仍無法通過現在的 freshness／authority gate。

獨立固定 v3 重播已完成，[完整遮蔽後獨立報告／run manifest](anchor-pixel-independent-report.md) 可在 GitHub 閱讀。Luna/xhigh 檢查固定 f8a09b… source 後，以 `swiftc -O -module-cache-path <independent-p1/module-cache> <fixed-source> -o <independent-binary>` 自行編譯並執行五組。其 binary SHA-256 是 `337df866b583cea271a314b049771c5da3abadeddb85f88940b8a14235f9423d`，不同於 Implementer a2acc1…；不假定兩個binary相同。

- 真實 pre／post：與 Implementer 重現同樣的1335／1326個局部 matches、zero integer shift與目標凸包外／低紋理／popup遮擋拒絕；沒有validated target bound。獨立判定 required positive **FAIL for tested method**、bound **BLOCKED/NOT_ESTABLISHED**，不是宣稱實際誤差已量到超2。
- +8px ROI及wrong-window拒絕；新增同一方法的對角ROI(+2,+2)負例，1335個候選量得(-2,-2)，徑向√8≈2.828px，accepted0，拒絕。此負例驗證不再以各軸≤2誤判徑向≤2。五個driver正常exit0仍不是P1 PASS。
- Sol以JSON值交叉核對四組共同矩陣（只移除input路徑拼寫欄位），所有其他值完全一致；只做輸出核對，沒有代跑獨立演算法或覆蓋其結論。
- 獨立原始report SHA-256 `6bf26a73053f8eca812bdd73f66f7d466ff47d63d036f03a404b19b76f781c76`；manifest `f56ed9522ca865d3fcacc2bed8b694090f5500ed67f2012fa0be2232cdca3176`。私有路徑在 `private/anchor-implementation-20261018-01/independent-p1/`。五組完整stdout／stderr／exit與時間記錄保留；其中+8 wrapper寫end timestamp時拼錯目錄，driver已一次exit0且未重跑，end timestamp維持unknown並保留runner-note。
- 獨立報告有一處引用legacy `chief-review.github.json`；整合附註明列正確當次審查是 phase內 `external-plan-review.github.json`／review5560487952，未把legacy檔案當新核准。來源註解half-pixel實為2px格，公開附註以實作為準，沒有subpixel量測。以上不修改原始報告或門檻。

獨立結論同為 **BLOCKED**，不是新實作後formal E2E或外部Code Review。獨立negative的PASS只代表該負例拒絕，不會升格成整體PASS。

### 產品、runtime、canonical 完整性與尚未執行項目

- 本輪正式產品與 focused tests diff 為空，Python `_support` 與 downstream `DETAIL_OCR_BINDING` 尚未修正。P2/P3 production contract、focused Swift/Python tests、native producer rebuild／install、新 runtime binding／grant 與 authorizer smoke 均 `NOT_RUN_P1_BLOCKED`。不以離線實驗宣稱這些 AC 完成，也沒有修 unrelated CI／fixture。
- 當次重新讀取 candidate21檔 closure仍為 `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`；canonical安裝closure仍 `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`。Swift source hashes與前輪相同，詳公開證據。
- 已安裝 production producer仍 `9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20`；decoder仍 `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`；installed entry仍 `726db9a876619aee66df57f0600f3ef07e40910c3f8285b266397800e12895f1`。
- 舊8beb pending runtime-binding重新讀取SHA為 `cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076`，不覆蓋candidate來源、未獲新版CodeReview，不能用於live。不是本輪新授權包，沒有重開舊grant。
- 前後245個保護檔皆相同，canonical Git HEAD、tracked status/diff相同。前收據SHA `760115995fec3fe075ffba90345ae0f4703d68b8aade16089b3b33ef2f0abd55`；後收據SHA `f94deb094bce4bf2548dca8e38883cf8e0669e60d611e47e62e1b2125ce13897`。Canonical ledger SHA仍 `08aa18e42bfee7a8e4d0529bac5b793d830efc1127794dac4baa8f4bdb9864e2`，state仍revision35／SHA `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`，batch／writer／context皆null。保留原ledger、歷史239、manual65排除、舊2/2計數與其他dirty/untracked。
- `REAL_SAVE_ALL_DISPATCH_COUNT=0`；menu calibration、chooser、下載56檔、逐檔SHA／完整ImageIOdecode、A/B VERIFIED、release全 `NOT_RUN`。沒有把GUI成功訊息當成檔案驗證，沒有不明派送或重送。
- 本輪是同一有界方法的初版缺陷更正與固定重播，保留原型錯誤及全部輸出，不重置歷史修復次數。Implementer保留13份量測JSON（初版1、v2四組及兩份重播、v3四組及兩份重播）；獨立重播5組。沒有每次重播都另開計畫、代理或交易。起始22:55Z，獨立執行23:12:25–23:14:26Z；+8那組end timestamp未知。模型使用額度未知；沒有要求Owner人工GUI操作，本輪沒有觀察或推論其他操作者期間的Mac活動。

`PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`
`IMPLEMENTATION_STATUS=P1_DIAGNOSTIC_ONLY; PRODUCTION_ANCHOR_AND_DETAIL_OCR_FIX_NOT_IMPLEMENTED`
`CORE_ACCEPTANCE_STATUS=REAL_RETAINED_PIXEL_DISPLACEMENTS_MEASURED; TARGET_BOUND_BLOCKED`
`REQUIRED_VERIFICATION_STATUS=PRODUCTION_TESTS_BUILD_RUNTIME_AND_LIVE_TRANSACTION_NOT_RUN`
`INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED_TARGET_BOUND; FORMAL_BACKUP_E2E_NOT_RUN`
`TASK_CLOSURE_STATUS=BLOCKED_NO_PROVEN_2PX_TARGET_BOUND`

下一步交付本輪完整報告、固定driver、數值輸出與runtime hashes到原Draft PR10，供Owner轉交外部Chief查核本輪方法限制。此checkpoint不是完成的production修正或新的exact-source Code Review請求。P1未成立前不整合P2/P3、不進行Save All；若後續有可證明的有界解法，仍須維持核准scope、真正2px與所有既有交易保護，再走精確HEAD外部CodeReview及A正式交易。A取得VERIFIED後才可另建B的獨立交易。不merge PR、不修改Harness／歷史紀錄。

交付前最終完整性核對於 `2026-10-17T23:23:34.939010Z`：245個保護檔差異0，canonical HEAD／tracked status／diff與phase開始相同，state revision35且batch／writer／context皆null。最終私有收據 `private/anchor-implementation-20261018-01/preservation-final.json` SHA-256 `d009c1c4a42b6b36a27c9c77f45c9f7866b399d8552cd8bdc477a01ab85aae47`；公開數值證據收錄其摘要與ref。這不是新的VERIFIED state receipt，只是讀取既有檔案的完整性檢查。Git checkpoint／push／Draft PR 的精確 HEAD 與實際成功狀態由後續遠端讀回及PR body提供，不在此檔內預填未發生的Git結果。

`CHIEF_REVIEW_STATUS=APPROVE_PLAN_ONLY; IMPLEMENTATION_NOT_APPROVED`
`FORMAL_MENU_CALIBRATION=NOT_RUN`
`INDEPENDENT_E2E=P1_REPLAY_BLOCKED; LIVE_TRANSACTION_NOT_RUN`
`REAL_SAVE_ALL_DISPATCH_COUNT=0`
`ALBUM_A_VERIFIED=NOT_RUN`
`ALBUM_B_VERIFIED=NOT_RUN`
`CANONICAL_LEDGER_INTEGRITY=UNCHANGED`
`HISTORICAL_239_PRESERVED=YES`
`FIRST_REMAINING_BLOCKER=P1_NO_INDEPENDENT_CONSERVATIVE_2PX_TARGET_BOUND`
`NEXT_ACTION=DELIVER_BLOCKED_EVIDENCE_TO_OWNER_FOR_EXTERNAL_CHIEF; NO_PRODUCTION_INTEGRATION_OR_SAVE_ALL`

## 2026-10-18：P1 證據裁決接受，提交唯一 R2 Plan（沒有新的 E2E）

Sol完整讀取外部 [review5560750050](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5560750050)，綁定HEAD `7b16c60aa325f36c17a7da24d255c57dce73ce89`，正文裁決 `ACCEPT_P1_BLOCKED_AS_CORRECT_FAIL_CLOSED`，GitHub狀態COMMENTED。原始API回覆保留 `private/anchor-detail-r2-20261018-01/chief-evidence-review.github.json`，SHA-256 `e2a491e97e6f39c378043bc787407ab957d4d8dee2494dd8dae6ad5ebe6852b9`。接受R1停止，不重啟NCC、不把局部zero shift當2px證明；原證據／Plan不回寫。此裁決不是R2 Plan approval、CodeReview、runtime grant或E2E PASS。

本輪只形成 [ANCHOR-DETAIL-R2-20261018 Plan amendment](../anchor-detail-r2-plan.md)，SHA-256 `be4de7516177fecff2f15dcd2c32c2eafdb817e6ac9552514c8930314cecb669`，20194 bytes。一次read-only `cua.getApp("LINE")`取得本機實際受支援API文件與自動AX：文件有座標click且回傳void，但未提供Mac座標原點／單位／crop／binding契約或原生派送位置收據。沒有要求截圖或輸入，不藉AX多重focus重開研究，也未聲稱目前56detail或Owner當次前景成立。查核既有adapter直接傳point給click、SCK full-display capture、geometry types與Apple SDK的native mouse/event listener/hit-test介面；來源／SDK hashes與查核限制完整列於 [R2 audit](anchor-detail-r2-coordinate-audit.json)。Apple官方文件只支持API能力，不支持本機已獲permission或已有2px精度保證。

唯一提出、尚未執行的實驗是exact-row shadow-point witness：從真正可見儲存全部列選點，先以安全title-label click關閉popup；確認同一點位在同視窗的無功能header，才以一次CUA click與PID-scoped listenOnly native事件比較。最多一項實驗、最多2次click、0 Save All。任何座標契約缺漏、listener不可用、位置可能碰不可逆控制、popup未關閉、事件歧義、未知誤差項或不能證明對後續實際派送的適用性，均STOP/UNSUPPORTED。原生helper只被動觀察，不post／改寫輸入，不要求新TCC權限。不把一次測試的小residual升格成future Save All保証。

R2明列保守上界、逐項誤差來源、預期原始證據、offline拒絕案例、停止條件及literal source scope。當前差異只有Plan／audit／現有報告與進度；診斷檔與條件式production影響只作提案，未實作。R2沒有改正式grant、ledger、2px／u+4／16×16、Save All保護或歷史資料。沒有另派agent或製作新Harness。本輪NCC重播0、GUI輸入0、SCK capture0、event tap0、permission prompt0、正式lifecycle0、Save All0；沒有新的實機／合成測試PASS。R2實驗及focused code tests、build、authorizer smoke全NOT_RUN。

本輪before receipt查核245個保護檔相同，SHA-256 `63821bca593d580075afddbb3adae4aee1c828a4356411bebbdc31fb422a4adc`；原始本機路徑在 `private/anchor-detail-r2-20261018-01/`，公開檔遮蔽個人根目錄、照片、AX原文及原始授權。後置保全與Git遠端讀回由本輪獨立收據保留；不預填未發生的Git結果。與前輪相同，canonical原有dirty/untracked工作不得夾帶或覆蓋。

`CHIEF_EVIDENCE_VERDICT=ACCEPT_P1_BLOCKED_AS_CORRECT_FAIL_CLOSED`
`P1_EXPERIMENT=CLOSED_BLOCKED`
`R2_PLAN_STATUS=PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`
`R2_COORDINATE_CORRESPONDENCE=NOT_ESTABLISHED`
`R2_EXPERIMENT=NOT_RUN`
`PRODUCTION_IMPLEMENTATION=NOT_RUN_THIS_PHASE`
`REAL_SAVE_ALL_DISPATCH_COUNT=0`
`ALBUM_A_VERIFIED=NOT_RUN; ALBUM_B_VERIFIED=NOT_RUN`
`NEXT_ACTION=OWNER_TRANSFER_FIXED_R2_PLAN_SHA_AND_EXACT_PR_HEAD_TO_EXTERNAL_CHATGPT_PLAN_REVIEW`

這次交付不是R2核准或Implementation完成。待真實外部Plan Review之後才依核准範圍推進；A必須真正完成56檔SHA／完整ImageIOdecode／VERIFIED讀回及release，才進入不同eligible B的獨立交易。

## 2026-10-18 Owner execution directive：真實正式入口唯讀 preflight（未執行交易）

本輪直接服務於 A56 Save All。完整讀取外部 [Chief Review 5561025091](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561025091)；其裁決為 `CHANGES_REQUIRED_GOAL_ALIGNMENT`，不是 R2 Plan 或 Implementation 核准。R2 shadow-click／EventTap 提案停止，未建立或執行探針、未重跑 NCC、OCR 調參、捲動或選單探索。

### 實際順序、第一拒絕與環境

1. 核對 candidate `5b9608355ccb247b251423833632fc21fd1b1178`、GitHub Draft PR #10 同一 HEAD、canonical 主目錄 `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`。保留主目錄 18 項既有 tracked dirty 與其他 untracked 工作；不安裝或混用候選來源。AGENTS.md 內容先前已核對相同。
2. 一次邏輯唯讀 preflight 中，證據初始化先因舊 manifest 鍵名 `files`（實際為 `protected`）停止，未呼叫 authorizer；保留錯誤後修正讀取。第一個 Python process 使用系統預設 Python，因缺少既有專案 dependency 路徑回 `INVALID_REQUEST: No module named 'jsonschema'`。改回已安裝的專案 Python 3.13 與既有 site-packages，沒有安裝套件或改源碼。兩個 process 均只有 `native_authorize`，零 GUI／交易呼叫。
3. 正確環境下實際執行：`<EXISTING_PYTHON_3_13> -B -m line_backup_batch.cli native_authorize --project-root <CANONICAL_ROOT> --authorization harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-20261017-8bebd23-PENDING-c6147d8f/project-grant.json`。`PYTHONPATH` 僅為 canonical `src` 加既有專案 dependencies，停用 bytecode 與 user site。開始 `2026-10-18T02:17:11.300104Z`，結束 `02:17:11.512480Z`，exit **4**：

   ```json
   {"status":"REFUSED","code":"PROJECT_IMPLEMENTATION_REVIEW_REQUIRED","message":"PROJECT_IMPLEMENTATION_REVIEW_REQUIRED","dispatch_authorized":false}
   ```

   **FIRST_FORMAL_REFUSAL=PROJECT_IMPLEMENTATION_REVIEW_REQUIRED**。literal guard 在 [cli.py](../../../src/line_backup_batch/cli.py) 的 `validate_one56_review()`（313–343）及 `validate_one56_provider_review()`（353–388）：要求真實外部 `APPROVE_IMPLEMENTATION` 與相同 source、HEAD、runtime、operations、fingerprint。pending bundle 中 review 仍是 `PENDING_EXTERNAL_REVIEW`。這個拒絕不是 GUI／2px 幾何證明，不代表後續 gate 已通過。
4. hosted CUA 僅 `getApp`、`getAXStateAndScreenshot`。當前真實截圖為相簿列表頂端，完整可見的是 **2024/06/02～06/07、65 張排除相簿**；A56 的日期／張數尚未可見。未點擊、未捲動、未開選單。101 AX list rows、scrollbar 0 僅是目前唯讀畫面資訊；沒有以 focus flags 推導身份。當次前景交接尚未重新建立，沒有宣稱可立即執行。
5. root 只啟動一個實際 `gpt-6-luna`／`high` 子代理，獨立上下文、有界唯讀檢查正式入口；沒有假稱使用其他模型或獨立 E2E。root 模型名稱未由 runtime 提供，記為 `NOT_EXPOSED_BY_RUNTIME`。Luna 沒有改檔、測試或 GUI 輸入。

### 來源／原生執行檔／runtime 的真實對帳

| 項目 | SHA-256／結果 |
| --- | --- |
| candidate 21-file source closure（含尚待外部 Code Review 的 M5/M6；產品提交 `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`） | `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d` |
| canonical installed source closure | `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54` |
| 實際 installed native producer | `9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20` |
| 原 pending ONE56 runtime-binding | `cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076` |
| 原 ImageIO decoder | `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf` |
| 實際 Python 3.13 executable | `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804` |
| native build record 的來源對 candidate | 全部相符；本輪沒有 Swift 變更或重建 |

原 runtime-binding 綁定 installed 8beb 來源，**不是 candidate M5/M6 的有效 runtime authority**。七個 callback／產品檔的 candidate 與 installed bytes 不同，完整逐檔 hash 見 [唯讀證據 JSON](formal-route-preflight-20261018.json)。`mac_runtime.mjs:264` 的 `REVIEWED_SOURCE_INSTALLATION_REQUIRED` 也拒絕 source root 與 projectRoot 混用。不覆寫原本 dirty state、不以舊 native binary/hash 冒充新執行核准。沒有新 runtime grant、bundle、review 或 readiness receipt。

### Luna/high 的有界結論與唯一替代決策

**沒有不改安全／授權契約就能解除第一拒絕的機械源碼修正；不應改碼偽造 review 或 geometry。** 不為取得綠燈而產生無關 patch 或測試。

- `two_album_entry.mjs:164` 的 `begin` 確實早於 229–235 的 open/calibrate。`service.py:390–459` 的 prepare 建立 transaction、lease、目的地；476–487 的 calibrate 要求 active run／manifest／身份，612–618 寫校準 checkpoint，620–643 的 intent 要求該 checkpoint。因此不能只移動 `begin` 便宣稱前置校準安全；另設 pre-transaction GUI 校準會改變 grant／ledger／證據契約，未實作。
- Python `observations.py:433–450` 的 `DETAIL_OCR_BINDING` 混用 OCR 語義和 transform 中心距離 ≤2px。即使修改此處，較早的 `_support`／native `frame-support` 仍是必要前置；只改 OCR 不足以建立可執行的正式路徑。本輪沒有重測或放寬它。
- hosted Mac `App.click(number|Vec2)` 回傳 void；已取得的支援文件沒有建立 macOS 原生輸入誤差界限。歷史真實選單存在與成功開啟證據仍保留，但不是已證明的 ≤2px actual click bound。沒有宣稱實際誤差必然大於2px，也沒有把 NCC 局部零位移重解釋為 PASS。

**唯一提交供 Owner／外部 Chief 決策的替代路徑：另立明確標示來源的人機協作交易模式。這不是現有可執行入口，也不是已核准源碼。** 精確契約差異限於：

1. 新 mode 的 Owner consent／獨立審查明確允許人工 GUI 身份確認與選單校準證據；automatic mode 的2px、u+4、16×16、原 grant 與歷史資料全部保留。人工 `OBSERVED` 不可寫成 automatic calibration PASS。
2. Owner 負責無法證明輸入精度的完整選單 trigger → 核對唯一「儲存全部」→ 一次 Save All 輸入。僅由 Owner 手點最後一列，不能解決前面的 CUA trigger／正式 geometry 依賴；不能偽造 CUA receipt。
3. 新模式仍在派送前固定群組／相簿日期／張數／process／window 與 duplicate 排除、獨立空目的地、writer lease、持久 original intent 和不可重送預留。派送前寫入「即將嘗試」，結果不明即保留鎖定與未知，不重送、不補造確定收據。原 `SAVE_ALL_CALIBRATION` 前置不能偷偷略過，必須以新 mode 的明示證據契約處理。
4. 需審查的接口為入口／runtime 的輸入者分流、`observations.py` 的明示人工來源、`service.py` intent/dispatch receipt 與 phase admission、`cli.py` 的新 mode grant／operations／review scope，以及必要的 ledger actor accounting。原 ledger 不重建、原 entries／counts 不改寫。現有 `resume`／`dispatch` 無法直接表達此流程；此處是待決的語義差異，不是假裝已有最小 code diff 或已完成實作。
5. 新模式下 chooser 的安全輸入方式也須經同一審查；僅已證明符合既有契約的機器輸入才可使用，否則人工操作也須明示來源。原有目的地核對、檔案穩定性、實際張數、逐檔 SHA-256／完整 ImageIO 解碼、durable VERIFIED readback 和 release 保留。A VERIFIED 後才獨立授權 B；ONE56 不挪用給 B。

這項替代會改變人工／自動證據與正式交易契約，必須先由 Owner 決定並交外部 Chief 審查其精確差異，才可實作、建立新 scope/grant 或操作；本機不自行把它當作 Plan approval／Code Review。若必須保持全自動輸入，現有已驗工具與證據尚不能證明符合既有2px契約，本輪保持 BLOCKED，沒有再開研究循環。

### 驗證、副作用、證據與交接

本輪 **產品 source diff=0、focused tests=NOT_RUN（無產品變更）、native build=NOT_RUN（無 Swift 變更）、獨立實機 E2E=NOT_RUN**。不以唯讀 audit 冒充任何正式成功。原239張歷史照片及6個保護控制檔，245個 hash 對前階段 baseline、對本輪前後均零差異。canonical revision35，active_batch／active_writer_id／context_lock 皆 null；ledger lifecycle0、entries0、failure_latched=false。65張排除相簿只有畫面核對及零輸入，未另外 inventory 人工65檔，不能宣稱本輪逐檔驗證該65張。

完整去識別化 runtime／來源／原始證據 hash 在 [formal-route-preflight-20261018.json](formal-route-preflight-20261018.json)（本次產出時 SHA-256 `65cd1d51c4308c6090f2143bd3fe3d228c71d76f61b43e519d840268eb10af56`）。原始截圖、AX、review、process stdout/stderr 與 before/after manifest 留在 `private/formal-route-preflight-20261018-01/`；本機絕對路徑為 `<CANDIDATE_ROOT>/harness-development/one56-menu-compat-20261017/private/formal-route-preflight-20261018-01/`，私有完整版列出實際絕對路徑。GitHub 不上傳照片、人名／群組名、原始授權、完整檔案清單或個人絕對路徑。JSON 中私有 refs 是本機取證索引，**不是可在 GitHub 開啟的原圖附件**；不宣稱雲端已看到私有原圖。

```text
PRIMARY_OUTCOME_STATUS=BLOCKED_NO_REAL_BACKUP
IMPLEMENTATION_STATUS=NO_PRODUCT_CHANGE_REQUIRED_FOR_REVIEW_REFUSAL
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=READONLY_PREFLIGHT_RECORDED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=NOT_DONE
FIRST_FORMAL_REFUSAL=PROJECT_IMPLEMENTATION_REVIEW_REQUIRED
RUNTIME_AUTHORITY=PENDING_NOT_VALID_FOR_CANDIDATE
LINE_FOREGROUND_HANDOFF=NOT_RENEWED_THIS_SESSION
FORMAL_MENU_CALIBRATION=NOT_RUN
REAL_SAVE_ALL_DISPATCH_COUNT=0
CHOOSER_RESULT=NOT_RUN
ALBUM_A_DOWNLOADED_FILES=NOT_RUN
ALBUM_A_VERIFIED=NOT_RUN
ALBUM_B_VERIFIED=NOT_RUN
CANONICAL_LEDGER_INTEGRITY=UNCHANGED
HISTORICAL_239_PRESERVED=HASHES_UNCHANGED
MANUAL_65_EXCLUDED=YES_NO_INPUT
NEXT_ACTION=OWNER_TRANSFER_EXACT_PR_SOURCE_AND_THIS_SINGLE_CONTRACT_DECISION_TO_EXTERNAL_CHIEF
```

本階段依持續授權 checkpoint commit/push 到既有 Draft PR #10；Commit 不等於審查或實機核准。請外部 Reviewer 查核精確 HEAD 的既有 M5/M6 實作與本節第一正式拒絕，並裁決上述唯一契約差異；在沒有真實核准、對齊 runtime 與有效前景前，不啟動 A 的唯一 lifecycle。

## 2026-10-18 Owner 角色修訂：DeepSeek 1017 獨立 E2E（尚未啟動）

本節僅記錄 Owner 的角色與交接修訂，並非實機驗收。正式 Independent E2E 改由 Ollama Cloud BYOK `deepseek-v4.1-flash:1017` 在 Owner 啟動的全新、獨立 Codex CLI Session 執行；它不是 Sol 本機 Subagent，Sol 不代操作或代寫判定，Luna/high 僅負責 Implementation／最小修復／Unit及Integration Tests。外部 ChatGPT 的兩道審查保持原職責。

已最小修正專案 [AGENTS.md](../../../AGENTS.md) 所有現行 Luna Independent E2E 角色描述，另明定正式 E2E 的唯一 GUI owner、只讀受審來源／標準／grant與ledger、隔離證據寫入、獨立否決權及修復後新 Commit／必要 Code Review／新 DeepSeek Session 重驗。對本機 canonical AGENTS 的修改僅套用相同內容基底上的本輪角色差異，不覆蓋其餘原有 dirty 工作。歷史報告中的 Luna 模型、測試或判定維持原樣，不追改為 DeepSeek 成果。

[DeepSeek E2E Handoff](deepseek1017-e2e-handoff.md) 固定 Owner 業務AC：A56一次 Save All、56實體原圖 SHA／完整ImageIO、VERIFIED讀回與release後才獨立B；239歷史與65人工排除、目的地分離、未知不重送不變。文件明列實際候選13b547a／既有closure與producer／舊pending bundle等身份，**尚未發放已核准正式 execution Commit／有效runtime/grant／當次前景**。本次文件交付的精確HEAD由同次PR和Owner訊息綁定，不能被當成正式執行批准。B入口／grant尚未交付，ONE56不可挪用。

交接不提供 Sol 完整推理、自評或預設PASS。原始必要環境索引僅留本機 `private/deepseek-e2e-role-20261018-01/environment.json`，記錄 canonical root／config派生backup root／獨立證據目錄／精確待綁定欄位，不含BYOK key。所有正式來源／grant／ledger／state保護不因換模型而放寬；前節實際authorizer拒絕保留，本輪不為同一已知拒絕重跑preflight。

本輪 `DEEPSEEK_SESSION=NOT_STARTED`、`ACTUAL_DEEPSEEK_MODEL=NOT_OBSERVED`、`INDEPENDENT_E2E=NOT_RUN`；GUI輸入、Save All派送及正式lifecycle新增均0。未改產品源碼或測試，未執行產品測試、build或GUI。只做文件一致性、無舊現行角色、交接未含預設PASS／私人內容、closure／控制檔完整性與Git差異檢查；不能把這些當E2E PASS。下一步仍是外部精確來源審查及正式runtime/authority準備，完成後由Owner啟動獨立DeepSeek Session，Sol/Luna讓出正式GUI。

## 2026-10-18 接受 Chief 限定來源裁決；自動路徑有界判定完成

完整審查為 [Chief5561111099](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561111099)，精確reviewed HEAD `13b547aecf9204762b53c984ca3c6c09064cb569`。其 M5/M6 source slice=`ACCEPT_SCOPED_SOURCE`；whole transaction=`CHANGES_REQUIRED`、`APPROVE_IMPLEMENTATION=NOT_GRANTED`。來源接受不改寫成整筆批准；現行candidate產品closure與受審來源相同，後續55396e8僅文件／角色變更，M5/M6不重寫。既有實際第一拒絕仍為 `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`，本輪不重跑已知的authorizer拒絕、不動pending grant。

本次Sol僅一次有界查核：讀既有真實證據、保留的frame-support／AX結果，以及目前hosted CUA `cua.rewriteDocumentation()`返回的支援介面。`App.click(number|Vec2)`仍回`Promise<void>`，未提供已成立的實際派送點位誤差證據；SCK／OCR／native window lineage可識別畫面、相簿與候選交集，但不能單獨證明實際輸入≤2px。既有popup沒有可用SaveAll AX action；不猜secondary action、不另試鍵盤或原生輸入。歷史成功開選單或局部零位移不能補足該證明。**AUTO_CLICK_2PX_PROOF=AUTOMATIC_CLICK_PROOF_UNSUPPORTED**，限定於本次已支援API與既有證據，不是宣稱誤差必定>2px或未來工具均不可行。

**SELECTED_PATH=OWNER_DECISION_REQUIRED。** 唯一待決方案為有界HUMAN_ASSISTED：Owner人工執行無法安全自動派送的選單操作，AI保留身份／duplicate／獨立目的地／writer／durable intent／不可重送等交易控制與後續檔案驗證，由獨立DeepSeek Session驗收。這會改變actor provenance、正式menu calibration／intent／dispatch receipt／chooser／ledger／驗收模式，**尚無Owner單獨核准、沒有可執行契約，不先實作或使用舊grant**。Owner若接受，下一步只提出上述直接相關的最小安全差異交外部ChatGPT審查，核准後才實作與固定精確版本；人工部分如實標HUMAN_ASSISTED，不標FULL_AUTOMATIC_PASS。若Owner不接受，保留全自動模式及目前BLOCKED，不再開R3/R4或新研究。

AGENTS.md已於55396e8改為Owner啟動`deepseek-v4.1-flash:1017`全新獨立Codex CLI Session，無須再次改寫；[handoff](deepseek1017-e2e-handoff.md)僅補本次限定來源審查身份。DeepSeek未啟動、正式E2E仍NOT_RUN。沒有product diff、focused tests、native build、GUI觀察／輸入、新intent或SaveAll；唯一CUA呼叫是文件讀取。沒有把本文當成實機PASS。

本輪直接讀檔核對：candidate source SHA=`be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`；installed=`ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`，不一致。舊pending runtime-binding仍`cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076`，非candidate有效authority。245保護hash相同，canonical state35，無active batch/writer/context；原ledger lifecycle0/entries0，A/B VERIFIED均NOT_RUN，SaveAll總派送0。

原始review與本輪hash／決策紀錄留本機 `private/chief-source-disposition-20261018-01/`：`chief-review.github.json` SHA-256 `532157f65307623716da715d263b747383fc0b45fdb942be3a5e13b55b15e4dc`；本機絕對根路徑由同任務private environment.json提供，公開版本遮蔽個人路徑，不上傳照片、群組名或原始grant。保留原始來源證據引用，不新增影像實驗、Plan或測試框架。本次checkpoint僅固定裁決與唯一待答決策，不代表正式Backup完成。

## 2026-10-18 Owner 接受 HUMAN_ASSISTED；契約差異交接（尚未實作）

Owner在同一對話明確表示「我接受人機協作模式」，因此不再把Owner模式選擇列為未答問題。該決定只允許準備最小安全契約差異供外部ChatGPT審查；不冒充Code Review、runtime grant或當次前景。已固定 [HUMAN_ASSISTED_ONE56/1](human-assisted-one56-contract-delta.md)（12,731 bytes；SHA-256 `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66`），基底5261bc2，狀態PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW。

實際GPT-6-luna/high只讀梳理確認：v3 intent.calibration與common.py目前強制自動座標及HIGH，不能把人工資料偽裝進去；manifest也會先走自動frame-support。修訂限定typed HUMAN證據／manifest分流、strict calibration oneOf及schema pin、原intent/CAS/一次請求、人工result／chooser與原ledger actor outcome。`visual-diagnostic-capture`可提供raw CUA/SCK/native原料，但完整observer仍走OCR分析且Swift surface寫死ALBUMS；提案只重用capture並加mode-gated正確requested surface，沒有新映射算法。Sol不採用另建ledger建議，明定原task／Owner／canonical ledger與收據／已用quota不變，只可在核准後追加真實新事件。十一條待審源碼邊界及既有focused測試清單已明列，並非已修改或已通過測試。

人工CARD／CAL／SAVE_ALL／CHOOSER依原slot先預留，原intent在SaveAll request前durable readback，request以run/action/stage唯一且不重發；未知保留intent與reservation。Owner是人工輸入者，DeepSeek是唯一AI觀察／正式E2E主體，Sol不派送或代判；人工資訊如實標OBSERVED／OPERATOR_REPORTED/HUMAN_ASSISTED。chooser需完整path及空目的地機器核對，最後仍實體56張SHA／完整ImageIO／VERIFIED/readback/release。自動2px/u+4/16×16及M5/M6不放寬、不重寫。A-only，B待A真正完成後獨立grant，不用第一本授權重送或湊第二本。

本輪沒有產品diff、Unit/Integration Tests、native build或authorizer重跑；沒有GUI輸入、formal lifecycle、intent、SaveAll或DeepSeek Session。candidate closure仍`be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`，installed仍`ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`，245保護hash零差異；A/B VERIFIED及獨立E2E仍NOT_RUN。真正下一關是固定SHA之契約差異的外部Plan裁決；取得後才最小實作、build、exact-source Code Review及合法runtime/grant準備。沒有把本次文件交付當成真正備份成果。

原始Owner模式文字與源碼／保護hash紀錄留本機 `private/human-assisted-contract-20261018-01/`；`owner-mode-selection.txt` SHA-256 `e29df429030a135e7fa23c9fe7c39b1f571e2034def5b9be4028dbac04c87770`。文字是對話決定的逐字保存，不是簽署receipt；對話message ID未公開，保持NOT_EXPOSED。個人絕對路徑／照片／原始grant不公開。

### 本輪附帶版本核對（唯讀，非LINE E2E）

Owner的VS Code截圖顯示舊工作樹 `Line_backup_capture_first_recovery_20261016`／`implement/one-scroll-slice-20261016`，實際HEAD `22cee2bc7686d18dfda839baa49ea885d90a0ade`。指定的單一GPT-6-luna子代理直接查GitHub refs／PR head及精確Git blobs：該同名遠端branch不存在；本機該工作樹tracked clean，AGENTS工作檔=舊HEAD，SHA-256 `0b1dbb0fcff342417950a205f42da96a0acb94786609b0c29b5b42cc78cd9fe8`，不是未提交改動造成。PR10在查核時為5261bc2；one56_authority候選工作樹同版。其AGENTS與canonical主目錄及GitHub PR bytes相同，SHA-256 `faa2524cd04a971cfe0a6cbca663107d005e148aeebce3a02b42d7430310d404`；canonical主目錄HEAD仍b7bb666，18項既有tracked dirty保留。

建議只在VS Code開正確one56_authority資料夾（detached HEAD是目前隔離工作樹的實際狀態），不對舊樹pull/reset。子代理沒有fetch、checkout、同步、改檔或GUI；本輪後續契約文件提交不改AGENTS，推送後由Sol另核對最新PR HEAD／AGENTS。這個版本核對不是DeepSeek或LINE驗收。

## 2026-10-18 階段性結束與下一Session交接

Owner要求因角色與交接流程調整，將手上工作收在明確階段、Commit/Push後交外部ChatGPT審查。本輪停在**Owner已選HUMAN_ASSISTED，最小契約差異已固定、待外部Plan Review**；不繼續產品實作或實機輸入。本節是正式交接紀錄，不是另一份Plan、授權或E2E判定。

| 交接項 | 狀態／固定識別 |
| --- | --- |
| 已交付來源基底 | `d6de2a1d280d382af7f018ec35623d7d26530b67`；本次收尾只追加既有progress與本報告 |
| 協作契約 | [HUMAN_ASSISTED_ONE56/1](human-assisted-one56-contract-delta.md)，SHA `1c00d80ff3dc50b167f5fe9e40b25736a13677b7011c40d6f8e1ba7c6ff00c66`；11條待審來源邊界，未實作 |
| Owner模式選擇 | 已接受，不再待答；不等於可執行grant或Code Review |
| 外部已接受項 | M5/M6 scoped source（5561111099）與DeepSeek角色/handoff docs only（5561127794）；未給完整APPROVE_IMPLEMENTATION |
| 下一個待決關卡 | 外部ChatGPT對固定契約SHA與本次精確PR HEAD作真正Plan Review；本機未代審 |
| 實際source/runtime | candidate `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`，installed `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`；舊pending runtime-binding `cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076` 不是候選有效authority |
| 正式交易 | 既有首拒絕PROJECT_IMPLEMENTATION_REVIEW_REQUIRED；state35／無active batch、writer、context；ledger lifecycle0、entries0，SaveAll0 |
| 真實業務結果 | chooser、下載、逐檔驗證、A56/B VERIFIED/readback/release及獨立DeepSeek E2E均NOT_RUN；未把文件或離線結果當成功 |
| 保全 | 原239歷史與6控制檔共245hash保持相同；canonical原有18項tracked dirty保留、未夾帶提交；人工65相簿排除，未因本輪重下載 |

依Owner要求，實際啟動一個`gpt-6-luna`／high子代理，只讀深讀progress、完整報告及固定契約，撰寫包含「意圖／做了什麼／驗證與結果／下一步的建議」的詳細commit message；Sol使用該文字逐檔stage本輪兩個交接檔並commit/push，提交後再核對遠端HEAD／實際commit body／公開報告bytes。子代理沒有改源碼或操作GUI，不是獨立E2E。這些讀回結果記錄在同階段private publication receipt，不能預寫為LINE測試PASS。

下一Session僅取得必要版本／契約／原始證據與已知NOT_RUN；先核對 repo、source worktree與canonical root、GitHub最新HEAD、commit body及本節。保留同一task/Owner、原ledger/初始化收據/counters、所有intent barrier，不重開舊grant、不重送未知SaveAll。外部Plan核准後才Luna最小實作／focused tests／build，固定新HEAD再外部Code Review；合法安裝與有效runtime/grant／當次前景完成後由Owner啟動全新獨立DeepSeek1017驗收A，A完成後才獨立B授權。Sol不承諾在Session停止後仍會背景執行。

```text
PRIMARY_OUTCOME_STATUS=NOT_DONE_TWO_REAL_BACKUPS_NOT_RUN
IMPLEMENTATION_STATUS=HUMAN_CONTRACT_PROPOSED_NO_PRODUCT_CHANGE
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=DOCUMENT_AND_DELIVERY_CHECKS_ONLY
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=STAGE_DELIVERED_PENDING_EXTERNAL_PLAN_REVIEW
```
