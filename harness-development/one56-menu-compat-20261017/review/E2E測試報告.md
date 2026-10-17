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
