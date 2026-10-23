# LINE 視窗辨識與自動相簿備份：獨立技術研究

日期：2026-10-10。研究目標是找出能改善辨識與點擊的技術路徑，並評估 Apple Vision OCR 的選擇。範圍已依使用者補充擴展到 Computer Use、macOS 擷取、相簿定位、派送及備份驗證。

這是研究建議，不是 IMPLEMENT、pre-live PASS、Acceptance 或 controller receipt。本輪沒有執行任何 OCR perform、螢幕擷取、LINE 操作、下載或備份／registry 寫入。只新增研究文件、公開來源快照及不含影像輸入的 SDK／設定探針。沒有修改既有研究報告、candidate、profiles、repair、契約或 ledger，也沒有 commit／push。設定探針的實際命令、stdout、stderr 與退出碼見 [sdk-probe-record.json](sdk-probe-record.json)；來源身份見 [local-source-manifest.json](local-source-manifest.json)。使用 context7-mcp 與 line-album-backup 技能協助核對文件與既有程序，沒有派出子代理。

## A. 白話結論與目前最大瓶頸

**最優先的突破是讓系統自行取得「含 popup 的完整桌面畫面」，取代使用者手動提供選單截圖，再將同張畫面的目標轉成 Computer Use 可以操作的座標。現有工具已有成功派送及下載的證據；目前尚未穩定自動完成的是選單的完整觀察、正確身份與座標綁定。** Apple Vision 仍適合作為日期／張數及文字位置的主要辨識來源；OCRTool 值得有限旁路比較，但沒有證據顯示換成它就能解決 popup 不在輸入影像、跨卡配對或失效 binding。

182 張成功案例提供了比一般推測更直接的證據。其 [report.md](../../../rev28-download182/TASK-20261009-download182/report.md) 明載：CUA app 畫面缺少 popup，使用者完整桌面 PNG 補上實際「儲存全部」文字及列範圍；之後確認目前視窗、版本及影像對應，再完成一次 Save All、一次目的地確認及 182 張落地驗證。這是有人協助校準的成功案例。它支持「自動補上同等畫面可消除一項人工依賴」，尚未證明所有相簿的無人介入批次可靠性。

相對座標不是憑感覺估計。保存的 [menu-geometry-correspondence.json](../../../rev28-download182/TASK-20261009-download182/evidence/menu-geometry-correspondence.json) 記錄：桌面影像 2294×1490，LINE 對應區域原點 (750,110)，app 影像 654×1286，兩影像比例 1:1；實際 Save All 列由桌面座標轉成 app 相對矩形 (588,244,230,54)。列中心 (700,271) 超出 app 截圖寬度，因此 [menu-safe-point.json](../../../rev28-download182/TASK-20261009-download182/evidence/menu-safe-point.json) 選取同時落在列內與 app 範圍內的 (635,271)，保留上下列安全間距。這些數字只解釋歷史成功，不能作為現在點擊座標。

**建議維持現行主 API，另立一個「自動完整桌面選單觀察與定位」的有限計畫，優先級高於直接更換 OCR。** 同時有一項具體 OCR 研究價值：本機設定探針讀到 modern 最小文字高度比例 0.03125、legacy 0.0，而候選及產品 wrapper 都未顯式指定。這使現有兩 API 比較包含未對齊的預設值；它可能影響小字，尚未證明是「相溥」誤讀根因。

## B. 現行方案與 macOS 27 OCRTool 比較

| 項目 | RecognizeTextRequest／VNRecognizeTextRequest | macOS 27 OCRTool | 本案判斷 |
|---|---|---|---|
| 定位與最低版本 | modern 自 macOS 15；legacy 自 10.15。是直接影像 request。 | 自 macOS 27；Vision 與 Foundation Models 的 Tool。 | 新舊主要包含介面／整合差異，不能推導品質排名。[S1][S2][S3] |
| 小字／密集文字 | 有 accurate、最小文字高度及 ROI 等可控參數。 | WWDC26 說可協助模型讀取細小／密集文字。 | WWDC 的比較語境是幫助 LLM；沒有聲稱比直接 request 更準。[S4][S5] |
| 繁體中文 | 官方指南明列 zh-Hant，中文只能與英文搭配；本機兩 request 的支援語言查詢均包含 zh-Hant。 | WWDC 稱超過 30 種語言；已查公開介面未提供 OCR 語言清單或 zh-Hant 選擇器。 | 不能把 Foundation Models 語言清單或文件翻譯語言當成 OCRTool 繁中保證。[S4][S6][S7] |
| 幾何 | observation 可提供位置；候選輸出 quad 的軸對齊矩形或 legacy boundingBox，再轉成原圖座標。 | 文件描述輸出整張影像辨識文字；已查介面沒有結構化逐筆 bbox 控制。 | 可比較文字；不能直接取代現有幾何／配對／位移證據。[S1][S3][S6] |
| 候選與分數 | topCandidates 的參數是最多數量，非保證數量；modern 上限 10。文字候選有 normalized confidence。 | 已查介面沒有 top candidates 或逐筆 confidence。 | 不得用模型自行產生的分數、bbox 或猜測補成 API 證據。[S8][S9][S3] |
| Revision | modern 公開 enum 與本機 SDK 都列 revision3，可於 init 選擇；legacy 公開 1／2／3，1／2 已 deprecated。本案輸出為 modern revision3、legacy 3，但程式用預設 constructor。 | 已查公開初始化器只有名稱與描述，未公開 OCR revision 選擇。 | 記 revision 與鎖 revision 是不同事；沒有跨 OS 位元相同保證。[S10][S2][S3] |
| 中文 correction／customWords | Vision 官方明載中文不支援；correction=false 時 customWords 被忽略。 | 未公開相同設定項。 | 開啟 correction 不能當成中文固定標籤加強機制。[S6][S11] |
| 執行條件 | 可直接對既有 CGImage／Data 等執行，不需 LanguageModelSession。 | 官方流程加入 session；Simulator 不支援。system model 需檢查裝置／地區、Apple Intelligence 與模型準備狀態。 | OCRTool 旁路增加模型與 session 的可用性條件；本機尚未驗證。[S3][S12] |
| 可重現性 | 原圖／crop／decoder／profile／revision／OS／binary 可留下清楚紀錄；本案尚缺若干有效預設值與 SDK binding。 | 需增加模型版本、prompt、附件標籤、session transcript、工具實際呼叫及原始 tool output。 | greedy 官方承諾固定輸入的相同輸出，但不等於跨模型更新、任意工具、OS 的全流程相同。[S13][S14][S15] |
| 本機驗證 | 以 Xcode 的 26.5 SDK 建置設定探針成功，在 macOS 27.0.1 讀出預設值及語言；沒有執行 OCR。 | 27.0 SDK 有符號，但符號 typecheck exit 1：Swift 6.3.3 與 SDK Swift 6.4 不匹配。 | 無 OCRTool 編譯／辨識成功或品質改善證據。見探針紀錄。 |

兩個直接 request 仍屬同一 Vision 框架。WWDC24 將新 API 描述為 Swift concurrency、async/await 與 request／observation 的直接對應，舊 API 仍保留。現有輸出確實存在差異：scan-003 同一 derivative hash、同為 revision 3，一邊「相溥」、另一邊「相簿」。這能提供有意義的 API 路徑差異偵測；不能把一致當成兩個獨立引擎的正確性證明，也不能憑差異推論完全不同的底層模型。Apple 沒有在已查資料公開兩條路徑／OCRTool 的底層模型對應。[S16]

## C. 本案已知問題的成因分類

下表區分「直接讀到的來源／保存紀錄」與「物理根因仍未知」。沒有重新執行審查中的測例，也沒有重跑歷史 OCR。

| 已知問題／證據 | 分類 | 技術處置及 OCR 的限度 |
|---|---|---|
| 182 成功流程中 app capture 不含 popup，桌面 PNG 含 Save All。選單相對 x 範圍 588..818，超出 app 寬 654。 | 擷取／前處理及座標來源 | 自動完整桌面擷取最有直接依據。影像中缺少的選單無法靠 OCR 換 API 重建。當次缺圖的底層原因仍未完整隔離。 |
| 另一原生 182 觀察 PNG 有正確群組、日期及 182，沒有 popup；無同步桌面／開關選單 bracket。 | 擷取時間／視窗範圍，物理根因 UNKNOWN | 保存材料只能證明 packet 沒有 menu，不能宣稱 SDK bug、menu 仍開或 observer 導致關閉。需要同步／有時間綁定的觀察。[本機 assessment](../../../rev28-target-observation/TASK-91a404524b134364bef6b57f330c1125/assessment.md) |
| 列表卡片四項 menu 沒有 Save All，與詳細頁五項 menu 混淆；曾提供上方 57 卡片的 menu。 | UI 身份／操作情境 | 先打開 intended album，再確認詳細頁日期與張數；更準文字辨識無法使錯誤 menu 出現正確命令。 |
| 歷史 intended 57 卻開到 182 的照片 viewer；沒有完整當時 bounds／click trace。 | 解析／目標配對及控制流程；物理原因 UNKNOWN | 應保存同幀卡片、非縮圖安全區、相鄰卡片及實際 click，並核對開啟後身份。不能斷言是 stale、點縮圖或 scale 錯。skill evidence ledger 保存此限制。 |
| scan-003「相溥」／「相簿」與低 confidence；原 .95 門檻排除正確可讀欄位。 | OCR 能力，加上未校準分數的決策政策 | 局部 crop、明確小字參數或另一 OCR 路徑可能改善。confidence 不是已校準的成功率，不能以 .95 當安全證明。 |
| 四幀固定標籤 correction on/off 保存 items 完全相同，每 observation 實際只有一候選。 | OCR 設定效果／證據語義 | 此資料支持「未觀察到改善」；不證明所有混合中英文輸入都一樣。請求前三個不代表實際有三個。 |
| offline Swift 可 crop，但 runner 的 16 個新 OCR 全用 [0,0,654,1286]。 | 前處理／方法落實 | 尚未實證局部 crop 效果及非零原點轉換。新 repair 提案的每幀六 run／四幀二十四 run，與旧全圖 run 是不同證據。 |
| 新 legacy OCR 已生成，但 stage_evaluate 的 --legacy 實際接歷史 replay 的單候選檔。 | 證據接線／綁定 | 新 legacy 結果不是該 evaluator 實際比較來源，不能把其結論說成新兩 API 全候選交叉檢查。見 runner 347..414 行。 |
| legacy 只解析首候選、日期框可在 viewport 外仍配成 agreement；ambiguous count 不阻止 scroll。 | 候選解析／相簿身份配對 | 兩 API 用同 parser 檢查全部實際候選、完整框、同 block 的唯一配對與阻擋歧義。即使 OCR 每字正確也可能跨卡配錯。 |
| candidate/profile/decoder/binding hash 只是回傳欄位，漂移仍可能 VALID。 | 證據綁定 | 必須重算、讀取可信 manifest 並逐欄核對實際 bytes。OCR 品質與此無關。 |
| indicator UNKNOWN 或 safety UNKNOWN 仍延伸 chain；停止原因不完整。 | 控制流程／失敗傳播 | 集中阻擋條件，terminal 後只補證據，不延伸 coverage 或 dispatch。不能以可讀文字取代現在的 menu/viewer/focus 判斷。 |
| R06 未隔離 safety；R08 未驗保存時間；R18 以常數作 PASS；R19 只看 hash 不同；frame manifest 被覆寫。 | 驗證設計／append-only 證據 | 需要實際行為及保存證據。舊 19 PASS 不能消除後續獨立 FAIL。 |
| CUA 的 user-change guard、noWindowsAvailable、paste RETURNED 但欄位仍舊值。 | Computer Use transport／狀態同步／postcondition | 新觀察後重建當前目標；以欄位實際值或畫面效果判斷。不能只改 OCR 或把 returned 當完成。 |
| 產品 wrapper 與診斷不同：Rev28 topCandidates(2) 只保留 best 和 candidateCount；診斷保留最多三個的文字／分數。 | 觀測資料設計 | 若要把診斷候選衝突政策用於產品，必須另行設計／審查資料與 parser，不能聲稱已具備同等資訊。 |
| 方法額度已記 3+1；同候選 pre-live FAIL；controller admission BLOCKED。 | 計畫／執行條件 | 技術可行性與執行許可分开。新研究沒有新 OCR 方法額度，也沒有解除任何 gate。repair 檔案存在不代表新來源已凍結或驗證完成。 |

直接程式依據：[offline_vision.swift](../../candidate/offline_vision.swift)、[profiles.json](../../candidate/profiles.json)、[run_offline_once.py](../../candidate/run_offline_once.py)、[catalog_diagnostic.py](../../candidate/catalog_diagnostic.py)、[OcrEngine.swift](../../../../rev28/Sources/Rev28Core/Perception/OcrEngine.swift)、[FrameCapture.swift](../../../../rev28/Sources/Rev28Core/Sensor/FrameCapture.swift)、[CUA adapter](../../../../scripts/line_backup_cua_adapter.mjs)。審查依據：[獨立 FAIL](../high-reasoning-review-01.md) 及 [bounded replan](../pre-live-replan-01.md)。逐步程序與預算以 [handoff.md](../../handoff.md)、[diagnostic-spec.json](../../diagnostic-spec.json)、[plan-contract.json](../../plan-contract.json)、[attempt ledger](../attempt-ledger.json) 為準。

## D. 已查證事實、推論與未知

### 已查證事實

1. **凍結規格與程式一致的部分。** 主／診斷 API 非獨立，accurate、zh-Hant/en-US、auto detect=false；標籤 live correction=true、自訂「相簿」「記事本」，offline 標籤比較及 identity correction=false。Swift 實際向兩 request 指派上述值，取 topCandidates(3)，保存原字、score、source／derivative bbox、revision、OS 及 hash。幾何先將 Vision 左下原點轉成左上，再除放大比例、加 crop 原點。程式有此能力，舊 runner 全圖實驗未驗非零原點。confidence calibration 為 UNKNOWN。spec 與 contract hash 仍對應歷史紀錄，plan-contract 與 handoff.json 逐 bytes 相同。
2. **中文修正的官方限制。** Apple 的 Recognizing Text in Images／Optimize Language Settings 明載「Vision doesn’t support language correction ... for Chinese」，同段也包含 related customWords array。modern customWords 文件另外明載 correction=false 時忽略。因此「相簿」「記事本」不能作為有官方支援的中文辭典修正。官方沒有在已查資料指定這種混合 zh-Hant/en-US request 是整個 flag no-op、讀回自動變 false、一定報錯，或所有輸出位元相同。英文部分可能受支援的 correction 影響是推論，不能宣稱已發生。本案四幀 on/off items 相同是保存結果的實際事實，不是新 OCR 測試。[S6][S11]
3. **小字預設的證據有矛盾，必須忠實保存。** modern 網頁寫 1/32；legacy 網頁現在也寫 1/32，然而本機 27 SDK header 寫 legacy default=0.0。設定探針在 macOS 27.0.1 實際讀到 modern=0.03125、legacy=0.0；兩個 revision 都是 3。這證明此次執行的預設不同，不能把 legacy 0 當成所有版本的官方一致保證。[S5][S17] 本案 source 沒有顯式指定或輸出最小文字高度；現有 OCR JSON 無法完整還原該項有效設定。
4. **OS 與工具鏈限制。** sw_vers=27.0.1／26A434；Xcode=26.6／17F113；Swift=6.3.3。默认 xcrun SDKVersion 查詢失敗，但 27.0 SDK 目錄及 SDKSettings.json 實際存在。其 Vision 及 _Vision_FoundationModels 介面包含所查 API；OCRTool 標記 macOS 27、output 為 opaque PromptRepresentable，沒有公開 bbox／候選／revision 參數。指定 27 SDK 的 typecheck exit1，明確報 compiler 6.3.3 與 SDK 6.4 不匹配。指定 Xcode 26.5 SDK 的無影像設定探針 build/run exit0；其成功不能外推 OCRTool 編譯成功。probe 沒有 OCR、畫面或 UI。
5. **原報告需要兩項補正。** 不能由 xcrun 查詢失敗寫成「本機沒有 macOS27 SDK」；存在 SDK 但 compiler 不相容是更精確的結論。當次下載的 OCRTool 官方 DocC JSON 各平台 beta=false，因此原報告「目前官方標 Beta」不能原樣沿用；已保存 source snapshot。JSON 的 availableLanguages 是文件可用翻譯語言，不是 OCR 辨識語言。
6. **成功與失敗範圍。** 保存的 182 report 與 acceptance 支持有人協助 CUA 單次備份成功；10/10 verify182 report 支持既有 182 檔仍完整且 state 一致。本輪未重新核對照片。保存的另一次 native packet 支持原生擷取／日期張數讀取成功，但不包含 menu calibration；catalog 的 pre-live review 明確 FAIL。這些事實可以同時成立，沒有矛盾。
7. **全畫面取得在 API 上有可行入口。** ScreenCaptureKit 可按 display 篩選，SCScreenshotConfiguration 提供像素尺寸、格式、sourceRect 等；pointPixelScale 是 points→pixels 比例。它可成為自動取代手動整屏圖的原生感測來源。includeChildWindows 官方預設包含 alerts/popovers/sheets，但文件未保證 LINE 某個 menu 的視窗分類或 lifecycle。[S18][S19][S20] 不得混用 SCStreamConfiguration 與 SCScreenshotConfiguration 的屬性語義。

### 根據資料的推論

- **最大產品瓶頸是把「人提供的完整觀察與判斷」自動化。** 182 成功的輸入與下載已被接受，而 menu 原始來源仍是人工桌面圖。最短技術路徑是在已成功的 CUA 開選單步驟後，用不切換前景的原生 display 擷取補上 popup。比更換 OCR 有更直接的本案證據。
- **局部 crop 與明確小字設定值得研究。** 它們可以縮小背景／搜尋範圍、改變字高占輸入高度的比例。nearest 2× 只複製既有像素；整圖一起放大不改變字高比例。其改善可能來自處理尺度／上下文，而非恢復失去的筆畫。只有圖片 654×1286 不能判定已被降採樣：另一原生 PNG 也是 654×1286，記錄 scale=2、geometry delta=0。更高品質原始擷取需以實際 points、pixels、scale 及來源證據判斷。
- **現有兩 API 差異可能部分來自有效預設未對齊。** revision 相同、source hash 相同仍不等於全部配置相同，也不代表必須輸出完全相同。未知底層實作不能從結果倒推。
- **Computer Use 的視覺語義判斷加原生 pixels／幾何，是合理組合。** 模型可協助區分列表、詳細頁、選單與 chooser；deterministic parser 核對日期/count；結構列／卡片框提供安全目標；工具只執行已綁定動作。ScreenSpot-Pro 的原始研究發現縮小搜尋區域能改善小目標 grounding，支持先整體認情境、再看局部的研究方向，不能直接當作本案精準率。[S21]
- **安全停止與完成備份必須各自有證據。** UI 點擊後要驗 correct detail／chooser／path；落地後才由 filesystem inventory、解碼與 registry 完成。OCRTool 的文字較漂亮或一次 click returned，均不足以完成這條鏈。

### 目前未知

- 自動 display 擷取是否能在目前 LINE 版本、主機與 provider 中穩定保留 popup，且不引發選單消失；歷史未隔離的缺圖原因。
- 新計畫下 LINE menu 能否公開提供 grounded AX role／label／bounds／action。Apple AX API 提供查詢及 action，app 是否支援需實測；角色或 index 本身不是 target authority。[S22]
- OCRTool 在相同繁中 crop 的 raw text 是否較好；底層是否與直接 Vision request 共用模型；實際 OCR 語言與內部 revision、resizing、排序。
- Foundation Models availability、本機 image model 狀態、原始 OCRTool tool output 可否完整保留與攔截呼叫次數；未下載模型、未執行 session。
- 最小文字高度改為明確 0 是否改善本案。既有短字與日期 bbox 仍可小於按預設比例計算的高度而被回傳，故不能用比例直接推導必定漏讀或完整解釋「相溥」。
- 手動 screenshot 對成功的貢獻可從執行紀錄定位，但沒有一個「只有 screenshot 不同」的控制實驗，不能量化它單獨的因果效果。
- repair-01 source 已存在，但未在本輪查到足以簽發同候選新版 pre-live PASS 的完整綁定結果；本輪不裁決其後續授權或方法消耗。

## E. 建議下一步、最小實驗與停止条件

### 1. 優先：自動完整桌面選單觀察

建議新計畫先解決一個具體結果：**已確認的 album detail → CUA 開選單 → 自動取得含 Save All 的 display 原始像素 → 同張圖導出可操作安全點 → 校準關閉後保持正確相簿。**

先在下載意圖之前的 nondestructive calibration 步驟驗證。**這個設計可以替代人工 desktop screenshot；不是直接在最後 atomic ellipsis→Save All 二點擊之間塞入截圖。** 現行 skill、CUA adapter 與已凍結流程禁止最後二點擊間的觀察；若要改成觀察後再第二點擊，需新的 action／證據／失敗傳播計畫及独立審查。

固定設計：

- 使用 reviewed 的 documented CUA 取得 fresh detail，確認 group、日期/count、toolbar anchor，再開 menu 一次。使用同一段已成功的操作鏈，不從錯誤列表卡片 menu 校準。
- ScreenCaptureKit 使用已選 display 的完整畫面；擷取程式不 activation、不模擬鍵鼠、不呼叫會重置 CUA target 的 UI 操作。必要時先以固定短暫 stream 記錄開選單前後，判斷 screenshot 時 menu 是否仍存在。選單生命週期的問題先取得證據，再決定是否需要 stream。
- 確認畫面中當前 LINE 及 popup 的所有權／位置，再將同一原始 frame 的 LINE、toolbar、menu crop 送給辨識器。保留原圖 dimensions、display origin、points/pixels、crop origin、timestamp、image hash、tool session 與實際 target。
- 用當張實際文字辨識 Save All，按上下列邊界導出 safe interior；校對 view→screen→CUA 的 documented mapping。若目標只部分落在 app 可操作範圍，使用已觀察且足夠大的交集；交集不足即不點。若採 display-coordinate actuator，須先另驗 mapping，不能套用 app-coordinate 常數。
- 校準關閉需要 fresh no-command evidence；後續意圖、一次派送、chooser 路徑、檔案驗證仍分別驗證。這輪 menu 診斷不下載。

預先指標：實際 menu 是否完整出現在原圖；正確詳細頁／menu 身份；Save All 及相鄰 Rename/Delete 列的 bbox；座標轉換在至少三個分散 anchor 的誤差；safe 點在人工 ground-truth 列／可操作交集的距離；capture→判斷→操作 latency；有無 unexpected UI action、menu close 或 focus change。數值容忍与時間限制在看實驗結果之前審查凍結，沿用目前政策者不事後放寬。

停止：正確 detail 不明、menu 不在原圖、popup 所有權不明、mapping／anchor 不一致、safe 交集不足、選單可能關閉、TCC 不足、transport error 或超過期限，立即保存原圖及 event／時間序列並停止。不得切換 capture profile、猜第三列、點鄰近命令或重試 Save All。新設計若需 bounded read-only 多幀觀察，事前寫明數量；不能到失敗時臨時加額度。

### 2. OCR 首選研究：固定 crop／小字配置，先找到改善機制

建議預先定義一個有限離線診斷，而非連續調參：四張既有 scan，全圖與固定局部 ROI、minimum-height 現行讀值與明確 0 作 2×2 對照；其他 API revision、zh-Hant/en-US、accurate、correction、scale、orientation、decoder 全固定。如果需要 legacy 配對比較，兩邊有效最小文字高度必須事先對齊，保存所有設定，不把同框架 agreement 當獨立真值。

此 2×2 是待審查的固定實驗，**不是本輪授權，也不是既有 repair 的 profile 可以自行改動**。完整 derivative/crop/source hash 与 raw candidates 要保留；評分不挑候選補正。最少呼叫數、重現次數及 ledger 方法消耗在新計畫中固定。四張已被看過，只可測目前 failure 的改善機制，不能估計一般化可靠性；後續需要事先留出且未用來调參的資料。

### 3. 現行 API 與 OCRTool 的最小公平旁路比較

適用 27 SDK／compiler 配對及模型 availability 先成立，才進資料實驗。不能為了啟動實驗而在本輪安裝 Xcode、模型或改全域 SDK 設定。

- **固定輸入：** 原四張 image bytes/hash；事先凍結每幀 header 和 list 兩個 ROI、canonical sRGB RGBA、orientation 與 nearest 2× derivative，共八份完全相同影像。兩分支使用同一份 derivative，不讓 OCRTool 拿更大的 crop，或讓主 API 拿不同壓縮格式。若要另測 card-specific crop，先凍結一套獨立輸入，不依輸出臨時裁切。
- **固定真值：** 看 source pixels 建立逐字與欄位 ground truth，記錄看不清、截斷、完整可讀的區域。標註可由人獨立核對，不能拿任一 OCR 結果或歷史預期 D 當真值。日期正規化白名單先定義，只處理契約容許的空白／分隔符，不把「溥」改成「簿」或合併姓名字形。
- **直接 request：** 用預先指定的一個 profile、revision 與有效 minimum height，保存最多前三候選；文字主評分只取第一候選。另報候選有效身份衝突，不作 oracle-best selection。
- **OCRTool：** 每張新 session，固定 attachment label、模型、prompt 與 greedy。prompt 只要求逐字轉錄／不可補字；主評分使用 transcript 中原始 tool output，不使用模型潤飾後的 final answer。Tool 呼叫由模型決定，須證明實際工具與影像參照；未呼叫不能冒稱 OCRTool 結果。若無法保留／限制或辨明呼叫次數，不啟動正式比較。零次、多次與錯附件都另記失敗，不能改 prompt 重跑取得滿意結果。[S15][S23]
- **指標：** CER=(替換+刪除+插入)/truth 字元數；完整標籤／群組 exact match；日期、count 各自 exact accuracy 與缺讀率；正規化後完整 metadata identity；插入幻覺字／數字；固定重複下輸出差異；elapsed time、tool 次數、runtime errors。八份分別及按四個原始 frame 分組報告，避免相鄰畫面重複文字變成假獨立樣本。
- **幾何合規另報：** bbox coverage、同卡配對、candidate conflict、confidence、revision binding 與 source provenance。OCRTool 不提供的欄位記 NOT_AVAILABLE，不能以 prompt 產生 JSON bbox 補足。沒有 geometry 的 tool 可以贏文字分數，仍不滿足目前替換門檻。
- **重現資料：** OS build、hardware、compiler／SDK build/path、source/binary/profile hashes、request revisions、所有有效參數、input/crop/transform/decoder、timestamps；Tool 另外保存模型版本可觀察欄位、availability、prompt bytes/hash、attachment／image reference、完整 calls/raw outputs、generation options。無法查到的 model／OCR revision 明列 UNKNOWN，不填假固定值。
- **預先規模與停止：** 可選八 inputs×兩分支×兩次事先固定重複，共 32 個分支執行，用於記錄一致性，不把多次結果投票／挑選。實際 tool 次數另受凍結上限。原候選的 required check 失敗按既有規則立即停；旁路單筆辨識錯字忠實計分，不能提前只留下有利 prefix；執行前提、binding、runtime／call budget 失敗則停止、報未完成。全部結束即不再調 crop、詞典、prompt 或門檻。資料不足或兩者互有勝負就報 inconclusive。

比較方法學依據是 Baek 等人的 ICCV 2019 原始研究：不同資料／評估選擇會誤導 OCR 比較，因此應統一條件與預先指標。[S24] 它不是 Apple API 行為證據。

### 4. 連回自動備份的完成條件

小範圍感測／定位驗證成立後，才由新計畫把其結果接到現有 transaction。最小產品里程碑是：一個未 VERIFIED 相簿，系統自行發現並辨識、正確開啟、校準 menu、一次 Save All、正確 chooser path、落地檔案穩定且完整解碼、原子寫入 VERIFIED 與 duplicate registry。先確認一個完整閉環，再研究多相簿與中斷恢復。

182 成功已證明一條可行的有人協助操作路線，現有 content verifier／transaction 有可復用部分。Rev28 native pipeline 與 hosted CUA adapter 是不同操作路線；不同的 1／2／5 秒 freshness、座標域、popup 證據及權限不可拼成一份虛假的同源證據。正式整合應選定每個 action 的一個 actuator，其他感測源提供綁定證據；一次失敗不能在未知是否已執行時換另一 actuator 重送。

原 task ledger 已消耗歷史 3+1；原 live 保持 0/6，controller admission BLOCKED，四道 required gates 與独立 Acceptance 都保留。本研究建議更改 API/profile、來源／證據政策、校準／派送流程或 gate 的部分，一律需要新計畫、獨立審查與適用執行授權／額度；研究文件及不含 OCR 的設定探針沒有消耗或重設方法額度。

## 直接來源索引與支持內容

[S1] [Apple — RecognizeTextRequest](https://developer.apple.com/documentation/vision/recognizetextrequest)：影像 request、typed observations、設定項與 macOS15 availability。
[S2] [Apple — VNRecognizeTextRequest](https://developer.apple.com/documentation/vision/vnrecognizetextrequest)：legacy request、結果與 revision 1／2／3。
[S3] [Apple — OCRTool](https://developer.apple.com/documentation/vision/ocrtool)：macOS27、文字輸出、session 整合、Simulator 限制；另保留 DocC metadata snapshot。
[S4] [WWDC26 — What’s new in image understanding，7:57 image-based tool calling 章節](https://developer.apple.com/videos/play/wwdc2026/237/)：工具用傳統影像 API 協助模型；OCR fine/dense text 及超過30語言。沒有直接 OCR A/B 品質聲明。
[S5] [Apple — minimumTextHeightFraction](https://developer.apple.com/documentation/vision/recognizetextrequest/minimumtextheightfraction)：modern 預設1/32，提高值可能忽略較小文字。
[S6] [Apple — Recognizing Text in Images](https://developer.apple.com/documentation/vision/recognizing-text-in-images)：accurate 路徑、中文／英文配置、中文 correction/customWords 不支援；中文 bbox 可能是 line／fragment。
[S7] [Apple — SystemLanguageModel.supportedLanguages](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/supportedlanguages)：此清單是 foundation model 的語言，不是 OCRTool 的識別清單。
[S8] [Apple — RecognizedTextObservation.topCandidates](https://developer.apple.com/documentation/vision/recognizedtextobservation/topcandidates(_:))：最多回傳數，上限10。
[S9] [Apple — RecognizedText.confidence](https://developer.apple.com/documentation/vision/recognizedtext/confidence)：normalized score；沒有本案 .95 校準資料。
[S10] [Apple — RecognizeTextRequest.Revision](https://developer.apple.com/documentation/vision/recognizetextrequest/revision-swift.enum) 與 [init](https://developer.apple.com/documentation/vision/recognizetextrequest/init(_:))：公開 revision3，initializer 可指定 revision。
[S11] [Apple — modern customWords](https://developer.apple.com/documentation/vision/recognizetextrequest/customwords)：correction=false 時忽略。
[S12] [Apple — SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel) 與 [Generating content and performing tasks](https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models)：系統模型 availability、裝置／地區與模型下載。
[S13] [Apple — greedy sampling](https://developer.apple.com/documentation/foundationmodels/generationoptions/samplingmode-swift.struct/greedy)：每次選最大可能 token，固定輸入相同輸出。
[S14] [Apple — Updating prompts for new model versions](https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions)：保留先前輸出、因模型更新檢查差異；不保證跨版本相同。
[S15] [Apple — Tool](https://developer.apple.com/documentation/foundationmodels/tool)：name/description/schema 進入 prompt，model 決定何時及多少次呼叫，結果交回 model。
[S16] [WWDC24 — Discover Swift enhancements in the Vision framework，11:05 migration 章節](https://developer.apple.com/videos/play/wwdc2024/10163/)：Swift API redesign／async／observations、VN 直接對應及舊 API 保留；Vision 左下 normalized 座標。
[S17] [Apple — legacy minimumTextHeight](https://developer.apple.com/documentation/vision/vnrecognizetextrequest/minimumtextheight)：目前網頁預設1/32；與本機 SDK header／runtime0矛盾，來源皆保留。
[S18] [Apple — SCScreenshotConfiguration](https://developer.apple.com/documentation/screencapturekit/scscreenshotconfiguration)：尺寸、PNG/JPEG、crop、child windows 等 screenshot 設定。
[S19] [Apple — includeChildWindows](https://developer.apple.com/documentation/screencapturekit/scscreenshotconfiguration/includechildwindows)：預設包含 subwindows、alerts、popovers、sheets；沒有特定 LINE 保證。
[S20] [Apple — pointPixelScale](https://developer.apple.com/documentation/screencapturekit/sccontentfilter/pointpixelscale) 與 [display content filter](https://developer.apple.com/documentation/screencapturekit/sccontentfilter/init(display:excludingwindows:))：顯示器篩選與 points→pixels 比例。
[S21] [Li 等 — ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use，2025](https://arxiv.org/abs/2504.07981)：高解析度／小目標困難、縮小搜尋範圍改善 grounding。不是目前模型的 LINE 評估。
[S22] [Apple — AXUIElementCopyActionNames](https://developer.apple.com/documentation/applicationservices/1462053-axuielementcopyactionnames) 與 [AXUIElementPerformAction](https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction)：查詢支援 action／執行 action；元素無效、unsupported 或 cannotComplete 仍可能發生。
[S23] [Apple — Transcript.ToolOutput](https://developer.apple.com/documentation/foundationmodels/transcript/tooloutput) 及 [ImageReference](https://developer.apple.com/documentation/foundationmodels/imagereference)：原始工具結果可從 transcript 區分；image reference 與 session 的影像綁定。
[S24] [Baek 等 — What Is Wrong With Scene Text Recognition Model Comparisons? Dataset and Model Analysis，ICCV2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Baek_What_Is_Wrong_With_Scene_Text_Recognition_Model_Comparisons_Dataset_ICCV_2019_paper.html)：統一資料、指標與比較條件的重要性。

本輪沒有宣稱 OCR、新 locator、LINE menu 自動擷取或自動批次測試通過。來源快照見 [sources/manifest.json](sources/manifest.json)；舊成功、舊 FAIL 與未完成事項分別保存。
