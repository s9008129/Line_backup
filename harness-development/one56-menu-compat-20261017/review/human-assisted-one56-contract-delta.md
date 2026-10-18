# HUMAN_ASSISTED_ONE56/1：最小交易契約修訂

狀態：**PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW；未實作、未建立新 grant、不可執行。** Owner 已在本次對話明確回覆「我接受人機協作模式」。這項選擇授權提出本修訂；不冒充 Code Review、runtime grant 或當次前景交接。本檔 SHA-256 由同次 PR／報告固定，核准後才由 Luna/high 實作。

基底：`5261bc280a5a546781a2b14b2f54fd5ed4f94420`；產品來源仍為 M5/M6 `7debc2ef4593f4ae4430cd3a4a8c0cb24cec0875`，21-file closure `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d`。Chief [5561111099](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561111099) 僅接受 M5/M6 來源，整筆交易仍 CHANGES_REQUIRED；[5561127794](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561127794) 僅接受 DeepSeek 角色／交接文件。二者均不是完整 APPROVE_IMPLEMENTATION。

## 1. 唯一變更與保留條件

只新增明示 `execution_mode=HUMAN_ASSISTED` 的 A56 單本分支：Owner 是人工 GUI 輸入者，DeepSeek 1017 的全新獨立 Codex CLI Session 負責原始觀察、交易服務呼叫及獨立檔案／狀態驗收；Sol／Luna 不操作正式 GUI、不代寫判定。本切片不自動啟動 B；A VERIFIED/readback/release 後才另行交付不同 eligible B 的獨立交易授權，不挪用 ONE56。

自動分支、既有2px／u+4／16×16、M5/M6、decoder與原圖驗證算法不變。HUMAN 分支不呼叫自動 card/menu/chooser 點擊；必要的相簿名稱、選單及 chooser 輸入均由 Owner 依綁定請求完成，DeepSeek只讀觀察。人工證據標為 OBSERVED／OPERATOR_REPORTED，備份結果標 HUMAN_ASSISTED，永不稱 FULL_AUTOMATIC_PASS 或 native precision PASS。

保留原 task／Owner 身份、config 群組及目的地命名、canonical state、原 `private/gui-ledger.json`、初始化收據、已用 counters／slots、239歷史及65人工排除。**不另建或替代 canonical ledger，不退還 quota，不重開舊 grant。** 機器仍強制 duplicate／writer／空目的地／CAS／readback／original intent／不重送／逐檔驗證；不是先手動下載再補帳。

## 2. 需核准的精確資料與授權差異

| 現況 | HUMAN 分支的最小差異 |
| --- | --- |
| ONE56 grant／contract／review 綁定自動入口及 CUA receipt | 新 immutable ONE56-A authority bundle，新增 `execution_mode=HUMAN_ASSISTED`；contract 明列 input_actor=OWNER_HUMAN、observer=Owner啟動的 `deepseek-v4.1-flash:1017` Session、A56 fingerprint、cap1、一次 Save All／一次 chooser confirm。原 grant 不改。owner decision／consent／外部 review scope／runtime 同時綁定 mode、actor、來源／entry／producer／decoder／config及原ledger；跨 mode／bundle 混用拒絕。外部 ChatGPT 仍是 Code Reviewer，DeepSeek 不替代它。 |
| `manifest()` v1/2 的每個 frame 都要求自動 `frame()`／`_support` | 新 typed HUMAN manifest／observation 分支，只在新 mode 接受；驗 raw CUA/SCK/AX bytes refs／hash、完整 native process/window lineage、時間／session、原群組別名確認及人工＋DeepSeek辨識的日期／張數／唯一目標。資料標 OBSERVED，不構造假的 sck_support、映射或 CLASSIFIER PASS；不明、錯窗／viewer／歧義即拒絕。既有 AUTO frame validator 不放寬。 |
| intent.calibration 必須含 `ellipsis/dot_spacing/save_all_point/confidence=HIGH` | 僅在 v3 的 `intent.calibration` 增加 strict tagged HUMAN oneOf：`kind=human-menu-attestation-1, execution_mode, input_actor, observer_session_id, observed_at, detail_ref, menu_ref, closure_ref, attestation_ref`；不接受自動座標或 HIGH 欄位。原 AUTO shape 不變；schema pin 與 common.py 的 v3→legacy 語義驗證鏈同步處理，v2／AUTO不能藉此接受HUMAN物件。無 state version bump、無歷史改寫。 |
| CUA dispatch receipt、RETURNED 與四步 chooser input | 新 typed `human-input-request-1`（輸入前）及 `human-input-result-1`（輸入後）原始 artifact；共用 task／grant／mode／actor／DeepSeek Session／source／run／action／request_stage／fingerprint／destination／reservation IDs／raw evidence refs／時間。stage限定CARD／CALIBRATION／SAVE_ALL／CHOOSER_PATH／CHOOSER_CONFIRM；action僅CARD及CALIBRATION可為null，其他必須是已持久化原intent。Owner 原始回覆保留；reported與機器observed事實分開，未觀察的實際點擊數／時間／結果為null／UNKNOWN，不能補成CUA RETURNED或物理exactly-once。 |
| ledger outcome 非 RETURNED 就 latch failure | 僅 HUMAN grant 分支接受帶 artifact ref 的 HUMAN_REPORTED_RETURNED；錯 actor／mode 或未核對原始回覆拒絕，AUTO仍只認原 outcome。UNKNOWN、crash或未閉合 reservation 保留／latch，不refund／重送。沿用原 CARD、CAL pair、ATOMIC pair、CHOOSER quartet及原順序；實際未做的步驟不可虛構消耗為已完成。 |

capture 只重用現有 `captureVisualDiagnostic` 的原始 CUA/SCK/native／clock 保存能力，不走 `visual-diagnostic-analyze`、OCR mapper 或新配準算法；raw pair仍是原料，不能直接冒充正式自動 observation。Swift `VisualDiagnostic.swift` 目前把 surface 寫死 ALBUMS，須在 HUMAN mode 才接受受 grant 限定的實際 requested surface（ALBUMS／ALBUM_DETAIL／FOLDER_CHOOSER）；requested surface 不冒充 native 自動分類。原始 capture 的既有 freshness／process／window／display 檢查保留；popup／身份由新 typed OBSERVED 證據核對。producer bytes/source 變動須真實 rebuild 並重新綁定。舊歷史無需遷移；新增HUMAN run之後不承諾可由舊binary讀取，禁止回滾舊版續跑或為相容性填假AUTO座標。

## 3. A56 唯一執行順序與不可重送邊界

1. **無 lifecycle 的只讀 readiness：**精確外部 Code Review、合法安裝／實際 source/runtime/grant、native/CUA讀取能力、無未解 intent/writer、正確群組及A56完整卡片可見。需要 Owner 前景交接時一次指定該畫面；未 ready 不呼叫 begin。Owner交接前的自行定位不得冒稱正式 CARD/scroll invocation。只讀證據保留 append-only；沿用原觀察額度，不改 exhausted counters、不改名 checkpoint 偷渡。
2. **begin→admit→prepare：**cap1；新的 HUMAN manifest 明確接入既有 eligibility／同日期改張數阻塞與 writer／lease／獨立空目的地。prepare 回 HUMAN action，沒有可供自動輸入的 click point。每次人工 GUI 請求前先預留對應原slot並readback；Owner點名稱，DeepSeek保存實際新 detail 與list lineage，核對2024/05/27～05/31、56張，不把 viewer 當 grid。
3. **人工視覺校準：**先預留 CAL_OPEN＋CAL_DISMISS；Owner開菜單，保存真正 full-display popup／唯一儲存全部及Owner確認，Owner安全關閉回同grid，保存closure。`calibrate` 在 HUMAN mode 寫模式明確的 OBSERVED calibration refs；沿用既有 phase，但不得標為自動幾何PASS。任何不明即停止，不拿單一 lifecycle 試錯或重置。
4. **原 intent→一次請求：**核對新鮮相簿／同窗／目的地仍空，`intent` CAS提交原 action、fingerprint、destination、HUMAN calibration、retry=false，扣原單本額度並durable readback。預留 ATOMIC_ELLIPSIS＋SAVE_ALL；再以CAS把唯一 request 的ref／nonce與stage=SAVE_ALL寫入既有run.events（evidence.kind=HUMAN_INPUT_REQUEST_ISSUED），readback後才把請求交Owner。同一run／action／stage已有request或對應slot已使用就不得再次發放，`resume`不產生新許可；不需新增root state／通用狀態機。擬沿用CLI `dispatch` 的HUMAN專用stage payload分別處理發放request及記錄result，AUTO payload完全保留；不把發出人工請求寫成機器已click成功。
5. **Owner唯一輸入：**Owner開功能表、核對並點一次儲存全部；DeepSeek不送任何替代click／按鍵。原始Owner回覆與前後觀察形成 HUMAN result，綁定同一 request／intent／reservation／window；人工回報及可觀察副作用分開記錄。失聯、逾時或來源不明時 request保持已發放、intent／quota保留，不重發、不把未見chooser當未點擊。人工物理動作依Owner回報，平台物理exactly-once仍不聲稱。
6. **Chooser：**保存LINE-owned chooser來源；任何chooser輸入前先預留原CHOOSER quartet並readback，發放stage=CHOOSER_PATH的唯一請求，Owner完成Go-to-folder／精確path／Return。DeepSeek以原始AX值或實際完整路徑證據及同窗連續性核對exact destination，僅leaf名稱或Owner『成功』一句不夠。再次讀回目標directory identity及空inventory，確認同一quartet不混別本後，才發放stage=CHOOSER_CONFIRM的一次確認請求。Owner確認；若無法驗證完整路徑／空目標就不允許確認。無法證實是否已確認時不重送。所有chooser操作如實標人工，不能借用原CUA receipt或假定自動precision已支持。
7. **dispatch→finalize→stop/release：**新 HUMAN receipt 驗全部 request/result／chooser／download-start 真實來源與actor後，才寫既有 DOWNLOAD_STARTED／TRIGGER_CONFIRMED；GUI成功不等於檔案通過。DeepSeek另做實體56張穩定inventory、逐檔SHA-256、完整ImageIO解碼，再由原finalize機制commit／readback VERIFIED、stop/release。mode與human證據refs須能從intent／dispatch／events持久讀回；原內容驗證及歷史registry規則不放寬。無可核對結果則保留未知與intent barrier，不finalize、不重送。

## 4. 僅允許的來源／測試範圍

| 必要路徑 | 直接原因 |
| --- | --- |
| `src/line_backup_batch/cli.py` | strict HUMAN grant／review scope／entry及逐mode payload admission；保留原 authority 路徑 |
| `src/line_backup_batch/service.py`、`observations.py` | HUMAN manifest／觀察／calibration／原intent／一次request與result／chooser證據驗證；舊AUTO分支不放寬 |
| `src/line_backup_batch/store.py` | 原ledger追加actor-bound outcome、原slot／CAS／no-refund；不改初始收據、既有entries/counts或cap |
| `src/line_backup_batch/state_v3.schema.json`、`schema.py`、`src/line_backup_acceptance/common.py` | strict HUMAN calibration union、schema SHA pin與v3/legacy相容語義；不把人工校準塞成假AUTO資料 |
| `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs`、`mac_runtime.mjs`、`mac/producer.mjs` | 提議新增 `runHumanAssistedSingleAlbumPilot`、唯讀raw捕捉與人工作業request/result調度；不使用自動hosted input adapter，不新增框架 |
| `rev28/Sources/rev28ctl/VisualDiagnostic.swift` | 原capture的HUMAN mode-gated requested surface；原capture輸出不冒充frame-support PASS，需重建producer |

以上11個來源路徑是明示待審範圍，非已改碼；`mac/analyzer.mjs`、`mac/classifier.mjs`、`OcrEngine.swift`、自動 CUA adapter、content／decoder及全域Harness不改。若實作發現不可避免的新源碼邊界，先回報精確差異，不能自行擴寫。

只在既有 `tests/test_single_album_authority.py`、`tests/test_batch_authority.py`、`tests/test_batch_observations.py`、`tests/test_batch_lifecycle.py`、`tests/test_single_album_entry.mjs`、`tests/test_visual_diagnostic.mjs` 與 `rev28/Tests/Rev28CoreTests/VisualDiagnosticContractTests.swift` 加必要focused案例：舊AUTO歷史相容／HUMAN標籤不可混入AUTO或v2、錯owner/source/bundle/identity拒絕、request只可在intent與預留readback後發放、重複request／跨session重放／未知拒絕、chooser完整path及空目標、A cap1與原ledger不可重建。所有案例目前 NOT_RUN；合成只能回歸，不當成真正下載。Swift變更後必須build，提供實際source／producer／decoder／runtime hashes及只讀authorizer smoke；不修無關CI。

## 5. 核准及交付邊界

這是 Owner 已選模式之後唯一的有界契約差異，不是R3/R4研究。外部ChatGPT先針對本檔固定SHA、AC變更（人工身份／校準／dispatch／chooser來源，內容驗證不變）與上述literal scope給出真正Plan裁決；本地不預填批准。核准後Luna/high最小實作、focused測試／build、Sol整合固定新HEAD，再交真正exact-source Code Review（包括新mode、actor、operations及實際runtime bytes）。只有批准的來源才合法安裝並核對實際closure／producer／bindings，取得新的有效immutable grant及當次前景後，由Owner啟動獨立DeepSeek正式驗收；不因Plan批准直接下載、不修改舊pending bundle、不讓Sol先下載一次再讓DeepSeek重下載。
