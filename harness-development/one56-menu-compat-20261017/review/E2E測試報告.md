# ONE56 真實選單相容性 E2E 測試報告

本報告是進行中的證據交接。尚未完成的步驟明列 NOT_RUN；離線測試與診斷觀察不代表正式備份成功。公開版本移除個人群組名稱、本機帳號、家庭照片與私有授權內容；原始畫面、AX、OCR、原生收據及雜湊保留在本輪 private 證據目錄，由獨立驗收者直接檢查。

## 意圖與範圍

修復真實 LINE 相簿網格右上角選單與現有程式的相容性：找到實際三點控制、辨識浮動選單的「儲存全部」，並安全關閉或恢復同一本網格。原先假設存在 AXButton / AXMenuItem，以及 Escape 後一定留在同一網格，都必須以真機證據核對。

外部 Chief 已閱讀的 PR HEAD 為 `d27c80b7d9ebecc9c170353110263971adc83f99`；產品實作為 `8bebd236d57bb80e39bfca163c67b9cecba1d36f`。[完整 Chief 審查](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5557707124)僅接受 B1/B2 來源切片，結論為 `CHANGES_REQUIRED_FOR_LIVE_SAVE_ALL`。本輪不把此審查改寫為新版實作核准。

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
- `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs`：唯一 1 行接線（把 classifier 的 `collectMenuEnvelope` 傳入 hosted session）。此檔不在原凍結五路徑內，屬本輪 scope amendment，須由雲端審查確認。
- `.../mac/analyzer.mjs`：修正三個真機診斷得到的缺陷：(a) 浮動選單候選改為「LINE 所有且實際被抬升的 CG layer（cgLayer>0）」恰一個、允許與 detail 相交，其餘上層視窗才套用原本 occlusion 規則；(b) `MENU_ENVELOPE_WINDOW_MISMATCH` 改與 detail 自身 window 比對；(c) 座標轉換修正：新增 `cua_scale`／`cua_offset_px`，popup 與 save-all 列同時輸出 `cua_bounds_px`／`cua_label_bounds_px`，`safe = crop ∩ popup_cua ∩ label_cua`（erode u+4）。這三項先前在真機上分別造成 popup 找不到、identity 誤判與點位換算錯誤。
- `.../mac/classifier.mjs`：envelope record 增加 `captured_at`；驗證改用 `cua_*` 邊界與 `cua_offset_px`／`cua_scale`，transform drift ≤1 px，`safe ⊂ popup_cua ∩ label_cua ∩ crop`。
- `.../mac_runtime.mjs`：`locateSaveAllRow` 改用 popup／save-all 的 `cua_*` 邊界；修 closure context key（原以 `detail.frame_id` 寫入、卻以 menu frame 讀取）。
- `src/line_backup_batch/service.py`：把同一契約移植到正式 Python 驗證器（`menu_envelope`、`menu_envelope_support`）：envelope 19 鍵與 native/popup/layer/row/mapping/OCR 綁定、trigger 9 鍵＋`PIXEL_STRUCTURE`＋`component_count>=3`、closure proof 驗 native popup 消失＋新鮮 OCR。移植過程中由測試抓到自身兩個缺陷並已修正：缺少 `inside` 匯入（會以 NameError 而非 typed `AcceptanceError` 失敗，違反 fail-closed）與 `menu_support` 與既有區域變數同名（`UnboundLocalError`）。
- `tests/test_cua_adapter.mjs`：ROW locator mock 補 `popup_window_id`／`popup_layer`。
- `tests/test_batch_authority.py`：兩個 calibrate 呼叫點改用 adapter 等價 fixture（envelope record、trigger、closure proof）；`safe` 改為交集結果 `[40,26,28,28]`、save-all 點改為 `[54,40]`。

### 驗證結果（可重跑）

- `node --test tests/test_cua_adapter.mjs` → 42/42 pass（多次重跑）。另有既有不穩定案例 `SCROLL_CAPTURE_TIME_ORDER`：本分支 1/10、基線 d27c80b 1/20，與本輪差異無關。
- `node --test tests/test_detail_grid_name_target.mjs` → 5/5；`test_single_album_entry.mjs` → 2/2；`test_visual_diagnostic.mjs` → 6/6；`test_visual_diagnostic_clock.mjs` → 1 skipped。
- `PYTHONPATH=src LINE_BACKUP_BATCH_TASK=<task> python -m unittest discover -s tests -p 'test_batch_authority.py'` → 37 tests、1 failure、1 skip。同一 worktree 修正前為 1 failure＋1 error（該 error 即本輪新增的 adapter 等價測試），現已修復。
- 其餘 8 個 Python 模組（排除 `test_project_binding.py`）→ 103 tests、1 failure、1 skip。
- 唯一 failure 是既有紅燈 `test_project_receipt3_download_and_pinned_decode_finalize_positive`（`GROUNDING_AX_SCROLL_RANGE`），已在基線 d27c80b 重現。根因更正：不是 Python 3.11/3.13 差異，而是測試本地合成 fixture `project_native_shaped_observation` 落後正式 `observations.py` 契約（AX scroll bar 元素缺 `minimum_value`／`maximum_value`／`native_node_id`，classifier evidence 缺 `detail_identity`）。此問題既有且與本輪無關，本輪不修改；該測試中的 calibrate 呼叫點已同步更新，但在 fixture 修好前屬未執行（UNVERIFIED）。
- `tests/test_project_binding.py` 需要 `LINE_BACKUP_INSPECTION_TEST_ROOT` 指向已備妥的 `project_binding_seed` 目錄；一般 discovery 下出現 31 個 setup error，基線相同，屬環境設定而非回歸。

### 尚未取得真機證據的部分

`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`：analyzer／classifier／mac_runtime 三個修正目前只有離線回歸與既有真機畫面的重播驗證，尚無新的 hosted capture 證明 envelope 能在真機產生並通過 Python 驗證器。`REAL_SAVE_ALL_DISPATCH_COUNT=0`、`CHOOSER=NOT_RUN`、`FORMAL_MENU_CALIBRATION=NOT_RUN` 全部不變。

下一步（須 Owner 重新授權）：在新鮮前景交接下，對既有 popup 做一次唯讀 hosted envelope 擷取＋同一標題關閉恢復的 bounded 診斷；envelope 通過後才依既有 gate 進入正式 calibration／Save All 交易。

## 正式交易狀態

`FORMAL_MENU_CALIBRATION=NOT_RUN`
`REAL_SAVE_ALL_DISPATCH_COUNT=0`
`CHOOSER=NOT_RUN`
`ALBUM_A_FILES_VERIFIED=NOT_RUN`
`ALBUM_A_VERIFIED=NOT_RUN`
`ALBUM_B_VERIFIED=NOT_RUN`

任何正式 Save All 均須先有新版 exact-source positive review 與有效 runtime grant，再通過原本 duplicate、空目的地、owner、原始持久 intent、menu identity / geometry 及 at-most-once gate。結果不明不得重送。下載後須實體盤點正好 56 個穩定原圖、每張 SHA-256 與完整 ImageIO 解碼，接著 VERIFIED 提交、讀回及 release。第二本必須獨立授權及記錄，不重用 ONE56 grant。

## 未完成事項與交接

真機選單結果與安全關閉已填入上節。本輪最小來源差異（六路徑，含 1 個 scope amendment）、針對性離線回歸與本報告已提交並推送至 Draft PR #10，待由使用者選定的雲端模型做獨立精確來源審查。待完成：真機 envelope 擷取（`MENU_ENVELOPE_DEVICE_VERIFIED=NOT_RUN`）、既有紅燈 fixture 修復（與本輪無關）、獨立 bounded-plan 接受、新 HEAD／closure／native／runtime SHA、唯讀 authorizer smoke、保護資料比對及獨立驗收。Draft PR #10 保持不合併。未取得實際外部審查結果前，不宣稱正式 Save All 已解除阻塞。
