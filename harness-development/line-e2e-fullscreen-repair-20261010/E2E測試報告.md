# LINE 全螢幕定位與相簿備份 E2E 測試報告

日期：2026-10-10（Asia/Taipei）
專案根目錄：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
本報告及主要證據目錄：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-e2e-fullscreen-repair-20261010/`
規範計畫：[20261010_LINE全螢幕定位與相簿備份_E2E技術修復計畫.md](../../20261010_LINE全螢幕定位與相簿備份_E2E技術修復計畫.md)，SHA-256 `9ea60dc98f95efed57cb591481d01028e16053403b8f4270e857a7c8103784b5`。
實作交接文件：[handoff.md](handoff.md)，SHA-256 `7912d009fab88477144e465ea11dcc7e8e6b265cfa1e05422127930fbcd0321d`。獨立研究報告：[report.md](../catalog-diagnostic-continuity-replan-20261010/results/research-independent-vision-20261010/report.md)，SHA-256 `6a59d7dbcfd1d2e3a92f71e06ed9979409b8b1b3155450bdd8be6b44014af350`。
本輪高階 Planner 回饋：[planner-replan-next-iteration.md](planner-replan-next-iteration.md)，整理交易阻塞、架構選項、停止條件與 P0–P8 下一輪建議；它是建議，不是新的實作授權。

## 結論

本次實機驗證證明：在使用者交還 LINE 前景後，文件化 Computer Use 可以從已核對的群組／相簿詳細頁打開右上角「⋯」；全螢幕 ScreenCaptureKit 可取得 app-bound CUA 畫面漏掉的 LINE 原生 popup；同一張全螢幕影像可由 Vision 讀出五列選單，並由幾何程式把「儲存全部」映射到具有上下列安全距離的 CUA 點位。選單也以不觸發命令的方式安全關閉，且畫面仍是同一本相簿。這些成功結果直接支持原計畫 §5–§6 的全螢幕感測、同源 OCR 與定位設計。

**自動備份 E2E 尚未完成，也不能判定已能完整自動備份。** 本次只把一本文字與張數已確認的 65 張相簿走到詳細頁選單辨識／幾何校準；未點擊 Save All，未出現儲存對話框，未下載照片，未做檔案數量、解碼或 terminal state 驗收。取得交易 owner 時，task-local schema-2 writer 被產品共用寫入保護拒絕。沒有第二本相簿，也沒有滾輪到下一本的測試。

使用者已明確授權對目標相簿執行 Save All。此授權目前仍是**已授權、未派送**：授權不會替代 fresh state owner、持久 intent、正確 chooser 路徑或 at-most-once 證據；在 writer 閘門未解決前沒有進行 UI 派送。

## 原計畫對本次測試的幫助與落差

原計畫很有幫助：它要求全螢幕原始像素、同源畫面 hash、LINE／popup window inventory、日期與張數身份、三個分散錨點、相鄰選單列、安全距離、一次性交易 intent 以及落地驗收。這使測試能區分「列表卡片功能表」與「相簿詳細頁的儲存全部」，也能把成功截圖綁定到真正看到 popup 的時點，而非從一張漏掉 popup 的 app 截圖猜座標。上述獨立研究報告提出先解決全螢幕 popup 觀察的路線，已獲實機結果支持；換 OCR API 本身不是本次成功的原因。

計畫的 live state 假設則與本次實際 writer guard 不一致。計畫 §3、§4、§9、§11 凍結 schema 2／RC2，並明言本輪不把 schema-3 Store 當成 live schema-2 authority；實際呼叫 schema-2 candidate `acquire` 時，`src/line_backup_acceptance/common.py` 的 canonical writer guard 拒絕寫入，要求使用 v3 service。v3 production CLI 又要求先有獨立 Acceptance PASS，而計畫 §11 把正式獨立 Acceptance 放在 E2E／報告後。把交易改接 v3、遷移 state 或調整授權／Acceptance 順序，會改變已核准的交易架構及安全閘門，不是本次可自行繞過的機械修正。完整技術證據見 [state writer gate](evidence/e02-state-writer-gate.json)。

## 本次目標與前置狀態

- 群組：`旻謙允禎成長日記`，由 `config/line_backup_config.json` 讀取。
- 受測相簿：2024/06/02–06/07，65 張，建立日 2024.06.09。
- 按設定推導的目的地：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/backups/旻謙允禎成長日記/2024-06-02_2024-06-07_65張`。
- 唯讀 duplicate 檢查：state revision 34；已 VERIFIED 的 57 張及 182 張相簿仍須略過；65 張目標未在 registry 中。
- `max_albums_per_run=1`。兩本相簿若要測試，必須是兩筆不同 fingerprint 的交易，第一筆 VERIFIED 並讀回、釋放 owner 後才能開始第二筆。
- Save All 的使用者授權已存在，但這不是 Save All invocation 記錄。下方逐步列出本輪 0 次派送。

### Save All 需求與授權

本次 E2E 的操作需求是：對唯一匹配的 `旻謙允禎成長日記 / 2024-06-02–2024-06-07 / 65 張` 執行一次 LINE 原生 Save All，僅確認一次由程式推導的精確目的地 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/backups/旻謙允禎成長日記/2024-06-02_2024-06-07_65張`，並以真實檔案數、穩定 inventory、全圖解碼及 state registry 驗證完成。使用者已在本次對話明確授權 Save All；不需要再向使用者申請同一項操作授權。授權範圍不包括對未核對相簿點擊、重送不確定的 Save All 或改寫既有目的地。本輪尚未派送，原因是 state owner／intent 前置閘門沒有成功。

## 實作技術與可重現細節

### 1. Computer Use 導覽與前景處理

所有 LINE UI 輸入使用文件化 `mcp__cua_repl` Computer Use；沒有以 shell、AppleScript 或其他非 CUA 手段模擬滑鼠／鍵盤。全螢幕 helper 是唯讀感測器，不 activation、不送 UI input。使用者已提醒前景可能被取回，因此前景中斷後不把畫面缺 popup 當成點擊成功；先等使用者明確交還，再刷新畫面及重新執行。

開啟第一個可見 65 張候選時，CUA 先重新綁定 LINE 相簿列表，點相簿日期文字（不是縮圖或省略號）：列表截圖座標 `[164, 869]`，畫面 654×1286 px；動作回傳 `RETURNED`。隨後的 detail 與同組列表全螢幕圖顯示日期、65 張及建立日，並仍可看到父列表，確認這次導覽是同一群組、同一張卡片。證據：[開啟相簿動作紀錄](evidence/e01-open-album-01.json)、[detail 全螢幕 PNG](evidence/e01-album-detail-01.png)、[detail manifest](evidence/e01-album-detail-01.json)。

成功打開 detail menu 的重測中，前景被使用者取去打字時所取的 [`e02-menu-retest-01.png`](evidence/e02-menu-retest-01.png)，SHA-256 `3fbfdc8e9512f9cc4570f21b327e0ec2f957253710b52f3181610eadc986ae0b`，沒有 popup。使用者明確交還前景後，先重新讀 detail，再以文件化 CUA 單擊 detail 右上角省略號 `[610, 100]`。這才是成功定位截圖的直接前置動作。沒有對選單列點擊。

### 2. 全螢幕 ScreenCaptureKit 擷取

候選程式：[FullscreenCapture.swift](candidate/v2/FullscreenCapture.swift)，SHA-256 `6080c65adb93288042123dc69d7a8f70c8bc4cfc3d67c370189c0477b4673050`（build receipt 亦記錄同一來源 hash）。它以 LINE bundle ID `jp.naver.line.mac` 查詢 on-screen window，將目標窗口所在 display 作完整 display filter；若有 LINE window，要求它至少 98% 落在單一 display，否則 fail closed。只有「沒有可見 app window、且僅一個 display」時才允許明確 single-display fallback。

本次決定性程式片段（來源 `FullscreenCapture.swift`）：

```swift
let filter = SCContentFilter(display: display, excludingWindows: [])
let configuration = SCScreenshotConfiguration()
configuration.showsCursor = false
configuration.includeChildWindows = true
configuration.dynamicRange = .sdr
configuration.displayIntent = .local
configuration.contentType = UTType.png._bridgeToObjectiveC()
let output = try await SCScreenshotManager.captureScreenshot(
    contentFilter: filter, configuration: configuration)
```

沒有設定 `sourceRect` 或 `destinationRect`，所以 manifest 記錄完整 display surface；保存 PNG 及獨立 JSON manifest，記錄 nonce、時間、pixel dimensions、display ID、scale、bundle/PID/launch date、每個 LINE window 的 on-screen 狀態及 image SHA-256。build source 的完整 CLI 參數定義在同檔 `Arguments`：`--image PATH --manifest PATH --nonce VALUE --bundle-id jp.naver.line.mac`。本輪每張圖的實際輸出路徑及 nonce 以各自 manifest 為準。

**成功截圖一：前景相簿列表。** [`e00-display-04.png`](evidence/e00-display-04.png)，SHA-256 `cff72b134c0f53d54256dbe0322da2fb95341c7ad6dca41b0a45e72a64d65064`，2294×1490 px、display 1、2 px/point；LINE window 3365 `on_screen=true`，同源 Vision 讀到群組標題、相簿 tab、首張 2024/06/02–06/07、65 張。證據：[manifest](evidence/e00-display-04.json)、[observation](evidence/e00-display-04-observation.json)、[OCR](evidence/e00-display-04-ocr.json)。這驗證 LINE app-bound CUA surface 與實體 display 對得上；早期 [`e00-display-02.png`](evidence/e00-display-02.png)，SHA-256 `6382c463baf432abb05aba71d2bc2804db2ac81945761a016afab6d5cd3a5d9a`，及 [`e00-display-03.png`](evidence/e00-display-03.png)，SHA-256 `5b63264c3937e6648095b8478fd049b6b3fcef7dc1bd139f16bed393dbbf96ab`，因 SCK 畫面是 Codex、LINE windows `on_screen=false`，曾判為 `OBSERVED_MISMATCH`，不算成功。

**成功截圖二：前景交還後最新一次成功讀到 Save All 的重測畫面。** `e02-menu-retest-02` manifest 時間為 2026-10-10 04:56:58Z（台北 12:56:58），capture 約 37.86 ms；完整 2294×1490 px、coverage 1.0、2×。PNG：[e02-menu-retest-02.png](evidence/e02-menu-retest-02.png)，SHA-256 `254934128ade2f8c4ede672461d3d127d6bedbdf8c5158e1b70092d865b0a8df`；manifest：[e02-menu-retest-02.json](evidence/e02-menu-retest-02.json)，SHA-256 `d2c740b77804de12d0307ddfc2500d1952ffd8f31ebb593d38cc01b9f769632c`。SCK 同時記錄 detail window 6743、父列表 window 6723 和原生 popup window 6809（popup frame x=640,y=107、137×167 pt），三者均 `on_screen=true`。

這張圖成功的關鍵不是「把舊 CUA screenshot 放大」，而是：**前景交還 → fresh detail observation → CUA 點 detail ellipsis `[610,100]` → ScreenCaptureKit 立即截完整 display（含 child windows）**。LINE 的 app-bound CUA 截圖沒有 native popup；SCK 原圖有。較早的 [`e01-detail-menu-01.png`](evidence/e01-detail-menu-01.png)，SHA-256 `685a142c7cf0868a4215097651ca099b7741762c11f833ecbfa66dfcf6adf86c`，也拍到五列 native popup，v2 幾何結果 [`e01-detail-menu-01-v2-geometry.json`](evidence/e01-detail-menu-01-v2-geometry.json)，SHA-256 `0f5b27c068a93cae3ef606e3aba52091a0203e88021f23bda7aa6a0b69a78a84`，max anchor residual 0.8223 px、safe clearance 26.967 px、候選點 `[610,271]`。因此 E02 是前景中斷後的最新成功重測，不是唯一曾拍到 menu 的截圖。E02 這張同時收錄父列表與 detail；相簿詳細頁日期與列表群組標題位於不同 LINE window，該 frame 的這項限制由 target match artifact 明確記錄。

列表層的另一張 [`e00-display-05.png`](evidence/e00-display-05.png)，SHA-256 `9fce00c59dcc471848b49dc9c81af2aa9ef51ab416cce248c7e81915375e654b`，顯示的是**相簿卡片**選單，列為「上傳項目、修改相簿名稱、分享相簿、刪除相簿」，沒有 Save All。它證明流程不能把列表卡片 menu 誤認為 detail 的下載 menu；此時沒有選取任何功能。

### 3. Vision OCR、profile 與座標來源

候選程式：[VisionRegions.swift](candidate/v2/VisionRegions.swift)，SHA-256 `a43d3d5667d76a6a15f0238ff813fb48012d6a174f6ef09942e250f24b78cb02`。對 SCK PNG 取命名 ROI，最近鄰放大 2×，使用 Vision `RecognizeTextRequest(.revision3)`；profile 明確固定 accurate、zh-Hant + en-US、關閉自動語言偵測／語言校正、自訂詞空集合、minimum text height 0、最多三個候選。核心設定片段：

```swift
var request = RecognizeTextRequest(.revision3)
request.recognitionLevel = .accurate
request.recognitionLanguages = [
    Locale.Language(identifier: "zh-Hant"),
    Locale.Language(identifier: "en-US")
]
request.automaticallyDetectsLanguage = false
request.usesLanguageCorrection = false
request.customWords = []
request.minimumTextHeightFraction = 0
```

定位成功使用的 detail menu ROI 是原始桌面 `[x=1250,y=190,w=340,h=370]`，放大至 680×740；group header ROI `[180,150,500,100]`，detail ROI `[714,110,654,1286]`。三份 OCR JSON 的 `input_sha256` 均綁定同一 SCK PNG hash。五列辨識序列是「選擇項目、修改相簿名稱、儲存全部、刪除相簿、分享相簿」；group OCR 精確讀到 `旻謙允禎成長日記`，detail OCR 讀到 `2024/06/02~06/07`、`65張照片`、`2024.06.09`。證據：[menu OCR](evidence/e02-menu-retest-02-ocr.json)、[group OCR](evidence/e02-menu-retest-02-group-ocr.json)、[detail OCR](evidence/e02-menu-retest-02-detail-ocr.json)、[target match](evidence/e02-target-match.json)。

v1 曾把 Vision normalized bbox 還原到來源 crop 時多除一次 processing scale。v2 對放大圖的像素尺寸除以放大倍率一次，再加 ROI 原點；程式註解、失敗重現和 scale-regression test 都保留這個修正。實作片段：

```swift
let x = roi.x + b.minX * CGFloat(enlarged.width) / CGFloat(args.scale)
let y = roi.y + (1 - b.maxY) * CGFloat(enlarged.height) / CGFloat(args.scale)
```

只有這個 v2 coordinate-fix profile 用於本次新鮮幾何結果；v1 量測不作派送依據。

### 4. Same-frame 幾何驗證與候選 Save All 點

候選程式：[geometry.py](candidate/v2/geometry.py)，SHA-256 `fdc439c1ac7286468c7bcc0a2de03e76b7095a87153984b679e217512e6929a7`。它要求 capture、OCR、anchors 使用同一 image hash，detail 與 popup 都在 SCK inventory 中且 on-screen，CUA screenshot 尺寸要與 detail window × display scale 相符；至少三個分散 anchor，每點殘差不可超過 profile 上限。接著要求唯一且按畫面垂直順序出現的 Rename／Save All／Delete 文字框，安全邊距至少是 mapping uncertainty + 4 px；最後只取 CUA 可操作 detail window 與 popup 的實際交集內點位。

本次新鮮結果見 [e02-menu-retest-02-geometry.json](evidence/e02-menu-retest-02-geometry.json)，SHA-256 `e312f68b387c3795459281229d75022e2745b1309185fe02bf1dc08c059af484`：

- anchor residual：三點，最大 0.8223 source px，profile 上限 2 px。
- display 座標文字中心：Rename y=327.5、Save All y=381.5、Delete y=435.5 px。
- Save All safe row clearance 約 27 px，最低要求 6 px。
- detail/popup 可操作交集 88×334 px。
- 推導點：全螢幕 pixel `[1324,381.5]` → CUA detail screenshot pixel `[610,271.5]`；detail window 左上在全螢幕 `[714,110]` px。
- 幾何 JSON 的 `pre_dispatch_ready=true` **只表示幾何候選符合 profile**，不構成 owner、intent 或 Save All 授權。

同 hash 綁定由 validator 再查一次。可檢視 [校準驗證 smoke](evidence/operator-calibration-smoke.json)：正確 package PASS；geometry hash 被竄改時拒絕；把 dispatch point 移進上方「修改相簿名稱」列時拒絕；`state_mutated=false`。

### 5. 安全關閉與不觸發副作用

計算後不是按 Escape，也沒有點任何 menu row；CUA 在新鮮畫面確認的空白標題列 `[500,50]` 單擊一次。緊接的全螢幕 `e02-menu-retest-03.png` SHA-256 `b4bbb0d007d0b21fa105a3cab4f4569045ce1c5750508bb70be4bed436612d5a`，manifest `[e02-menu-retest-03.json](evidence/e02-menu-retest-03.json)` 證明 popup 不再 on-screen，原 detail 6743 及父列表 6723 仍 on-screen。其同一 hash 的 group/detail OCR 再次讀到群組、日期、65 張；[closure record](evidence/e02-calibration-closure.json) 將 safe close、post-close window 狀態、OCR hash 與 CUA ellipsis 觀察綁定。觀察記錄：[e02-menu-retest-observation.json](evidence/e02-menu-retest-observation.json)。

截至這次安全收合：Save All invocation 0、chooser confirmation 0、download 0、state mutation 0。這一批 menu 校準確實保持無下載副作用。

## Build 與離線測試

編譯使用 Xcode 26.6／Swift 6.3.3、明確指定 macOSX26.5 SDK；不依賴 macOS 27 OCRTool。`build/attempt-08.json` 保存每個 compiler command、source hash、exit code 與 binary hash，該 receipt SHA-256 為 `70bd64d7fff3ccc06a680193081b20a01624d1ed81b9c93a8b1bdd6ed0680dc0`。最後成功 binary：

| 元件 | build attempt 08 | Binary SHA-256 |
|---|---|---|
| ScreenCaptureKit 全螢幕擷取 | exit 0 | `f12954d671d1e016f5626d76bebaab7a03e6e1c5779ec60927471b88daa30a2c` |
| Vision 區域辨識 | exit 0 | `7a35228d7e565934b8857cdb0271c2705702fd79f73a61d2363b03a38c7d069f` |
| ImageIO 全圖解碼器 | exit 0 | `17a003351d00ef739aeb5a686800894501bcce2c5fb8b1a3b688b6ae2086b642` |

attempt-08 receipt 保存實際 compiler argv。ScreenCaptureKit 及 Vision 的共同命令形狀為：

```sh
/usr/bin/xcrun --sdk macosx26.5 swiftc \
  -sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk \
  -target arm64-apple-macosx26.0 -swift-version 6 -parse-as-library \
  <source.swift> -o <candidate/v2/bin/output>
```

ImageIO decoder 使用同 SDK／target，但不加 `-parse-as-library`，因它採 Swift top-level statements。每個實際 source path、argv、exit code、binary path 與 hash 請以 [`attempt-08.json`](build/attempt-08.json) 為準；上方是為可讀性縮短的命令樣式。

保留 build attempt 01–08 的全部結果：#3、#5、#6、#8 編譯通過；#1、#2、#4 記錄 capture/Vision API 或 Swift 語法錯誤；#7 的 capture/Vision 通過，但 decoder 因 `-parse-as-library` 不容許 top-level statements 而編譯失敗。#8 僅為 image decoder 移除該編譯旗標後，三個二進位皆 exit 0。這些錯誤都在離線 build 階段發現，沒有造成 LINE 輸入。

幾何測試在 `candidate/v2` 執行，完整輸出 [test-geometry-v2.log](evidence/test-geometry-v2.log)，SHA-256 `7aa0cdbf4d17753d2e9ccd208527aeb88f3188a8a6134024477c574ab4e1ab58`：**7/7 通過**。涵蓋 v1 scale bug regression、安全 interior 點、hash mismatch 拒絕、anchor 殘差超限拒絕、錯誤 screenshot 尺寸拒絕、popup 交集過小拒絕、menu 順序不確定拒絕。

ImageIO positive fixture 對一張 340×370 PNG 做完整 RGB bitmap draw，結果 PASS、read-only；expected count 2 而目錄只有一張的 negative case 產生預期不符合張數的拒絕（JSON `verdict=FAIL`，代表該驗證資料不符合 expected count，不是 image decode 成功）。請見 [decoder positive](evidence/image-decode-positive.stdout.json)、[decoder negative](evidence/image-decode-negative.stdout.json)。這只驗證 decoder／count gate 的測試 fixture，不是 LINE 相簿檔案。

## 交易前置實測與阻塞

完整 state 前置證據：[交易阻塞紀錄](evidence/e02-state-writer-gate.json)，SHA-256 `5e7d328ac3a738e56eaae1228bb1cb60b3ee50fa2e2639fa40f9b39e2156c19a`。操作流程如下：

1. Candidate v2 `operator.py snapshot` 對 canonical state 唯讀成功，revision 34、state SHA `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`；前後快照 [before](evidence/snapshot-e02-65-pre-acquire-r34.json) 與 [after refusal](evidence/snapshot-e02-65-after-acquire-refusal-r34.json) SHA 相同。
2. 唯讀 `line_backup_batch.cli inspect` 回報 schema 2、revision 34、`active_batch=null`、`active_writer_id=null`、verified_count 2、`dispatch_authorized=false`。這只證明可讀，不授權 dispatch。
3. 以本任務 absolute path authority + fresh snapshot receipt 呼叫 task-local `operator.py acquire`。canonical state write 被明確拒絕：`Canonical state requires the v3 service`。沒有 canonical state write、transaction owner 或已提交的 canonical intent；前後 state snapshot 相同。
4. acquire 的執行順序在呼叫共用 atomic writer 前先建立目的地；因此該 refusal 留下一個**空目標資料夾**。已唯讀確認裡面 0 entries；未刪除或改動。這是本次唯一新增的備份目的地副作用。state SHA／revision 不變。

另有 task evidence 下的本機檔案 [`intent-payload.json`](evidence/runs/RUN-20261010-e02-65-c6aba32e1f104d91b01aa0ffd372bf71/intent-payload.json)，SHA-256 `1a461ff8d7e3e912696d6134f149a1a70ca3b6d82ad0552a678de141d66edd5d`，內容引用本輪 calibration 證據與候選點位。它是 task-local 的 operation payload 檔，不是 canonical state 內已提交的 intent，也沒有使 `dispatch_authorized` 變為 true；state gate 明確記錄 `intent_committed=false`、`dispatch_authorized=false`。因此報告所稱「沒有 intent」均指沒有已提交的 canonical intent。

**重現資料缺口：** `e02-state-writer-gate.json` 保存 `operation=acquire`、錯誤原文和前後 state 證據，但沒有保存當次 shell argv、stdout/stderr 原始檔或 process exit code；這些值在本次封包中標記為 UNKNOWN，不從錯誤字串推算。先前未保全的嘗試不納入可稽核命令履歷。下一輪任何 writer invocation 都必須先保存實際 argv、exit code、stdout/stderr 與 pre/post snapshot，再執行。

V3 Service 不是本任務可以直接替換的本地細節：它要求 schema 3 migration／batch authority；production CLI 要求 Acceptance artifact，計畫卻把獨立 Acceptance 排在 E2E 後。原計畫還規定本輪 schema 2／RC2、`backup_one` 交易，並明確不把 schema-3 Store 混作本輪 live writer。因此在取得新的 architecture／authorization 決定前，不再嘗試另一種 writer，也不做 state migration。

此外，現行 v3 batch service 的 `Coordinator.run()` 在任何 album transaction 前先呼叫 `p.catalog()` 和 `svc.admit(...)`；結束時又要求 `p.final_catalog()` 與起始 manifest 的 identities 完全相同（見 `src/line_backup_batch/coordinator.py`、`service.py`）。`service.py` 對 catalog manifest、frame、mapping、boundary evidence 及最終 collection drift 均設有檢查。這與核准計畫 E02 的操作要求不同：E02 可在目前可見完整卡片中選第一個 eligible target，只有當前沒有 eligible 卡片時才逐次 0.25-page scroll；不要求完整 catalog coverage 作為第一筆備份前置。故改用 v3 會同時改變 state writer、Acceptance 順序及 catalog-admission 語義，需由高階 Planner 一併決定，不能只替換呼叫命令。

### 交給高階 Planner 的下一輪決策輸入

高階 Planner 已以本報告及上述原始證據完成唯讀重規劃，完整回饋記錄於 [Planner 下一輪建議](planner-replan-next-iteration.md)。下一份經審查計畫至少須回答：

1. **Canonical state writer 路線：** 保留 schema 2／RC2 並定義一條受既有安全 guard 接受的正式寫入路徑，或明確改版為 schema 3 batch authority。不能透過直接改 guard、旁路共用 writer 或使用另一份 state 來取得 owner。
2. **Execution authorization 與 Acceptance 順序：** 若採 v3，production CLI 要求 `authorization.json` 中 `config_cap=1` 及精確 `user_message`，並要求獨立 Acceptance artifact 的 `INDEPENDENT_ACCEPTANCE_STATUS=PASS` 與 I0–I4／A1 gates（`src/line_backup_batch/cli.py`）。Planner 必須核對現有授權能否合法滿足這些欄位，並解決原計畫把獨立 Acceptance 排在 E2E 後所形成的順序循環；不得為通過 CLI 補造或重寫使用者授權。
3. **Catalog admission 與 E02/E03 範圍：** 決定第一筆交易是否改為完整 catalog admission，或保留「第一個可見 eligible 相簿」的計畫語義並提供符合既有安全條件的服務路徑。若維持 v3 全 catalog admission，實際測試須納入起始／結束 catalog 一致性與完整 frame、mapping、boundary 證據；不能只測單卡片定位。
4. **交易數量與 run semantics：** 說明 v3 `backup_batch`、catalog admission 及 `authorized_limit` 如何保留原計畫兩筆獨立 `backup_one` 交易與每 run `max_albums_per_run=1` 的行為；兩個 run 的 duplicate、owner、intent、VERIFIED readback／release 不得合併或重置歷史額度。
5. **實際滾輪驗收：** 把至少一次 bounded 0.25-view-height scroll transition 列為獨立 E03 gate，即使第一張 eligible 卡片已完整可見也要實際驗證 scroll 到新內容。前後要有同 group／surface／session／PID／window／layout、至少一個完整唯一 fingerprint 的有序 overlap，且至少一張新而完整的 eligible 卡片出現。若目標不存在則 `NO_ELIGIBLE_TARGET`；若被 writer gate 擋住或未做滾輪則 `SCROLL_TEST_NOT_RUN`／PARTIAL，不能用觀察現成卡片取代 scroll 測試。
6. **全自動 evidence boundary：** 本輪 CUA supporting frame bytes 沒有另存，部分 anchor 對應依賴人工 cross-check。Planner 須決定 live E2E 是否必須保存 CUA support frame 並以可重現演算法自動完成三 anchor 對應；若仍需人工觀察，須明確列為 `OBSERVED`，不能宣稱完全自主定位。
7. **恢復 live E2E 的明確前置 gate：** 新計畫須列出可驗證的 fresh state／duplicate decision、owner、intent、dispatch 和 destination 條件，並說明本次 acquire 所建立的空資料夾如何在不刪除或覆寫的情況下被既定流程安全採用或處置。決策完成前，維持本輪不派送 Save All、不變更 state、不操作 LINE。
8. **歷史嘗試與 GUI 額度：** 先從可追溯 receipts 重建 material-attempt 與 GUI invocation 使用量。原計畫追加的 5 次 material attempts 不會重置歷史；build attempts 01–08 不可代替 material-attempt 計數。task package 尚無完整 append-only GUI／attempt ledger，未知值不能視為 0；若無法證明餘額，不得開始新的 LINE UI 操作。

這是需交由 Planner 審查的架構決策清單，不代表已選定 schema 2 或 schema 3 路線，也不構成對修改安全 guard 或進行 state migration 的授權。

## 單次測試／相簿結果矩陣

以下矩陣依核准計畫 §13 彙總實機相簿路徑。`NOT_RUN`、0 次派送與幾何測試 PASS 均不表示相簿備份完成。

| 測試／相簿 | 候選／人工介入 | menu 原圖／mapping 誤差與安全邊距 | 實際點擊與效果 | Save All／confirmation | 檔案 N／bytes／decode／穩定 | state／preservation | Verdict |
|---|---|---|---|---|---|---|---|
| E00 列表定位；65 張候選 | 指定群組；使用者提供前景。 | menu 不適用；mapping 不適用。 | full-display SCK 觀察 Albums 與完整候選卡；沒有交易 click。 | 0／0 | 0；bytes、decode、穩定 inventory NOT_RUN。 | 只讀觀察；無 state mutation。 | `OBSERVED`：列表／候選身份可讀；不是備份 PASS。 |
| E01 單本 detail 與首次 menu observation；2024/06/02–06/07，65 張 | 65 張相簿；使用者曾交還前景，CUA 點 metadata `[164,869]` 開啟 detail。 | [原圖](evidence/e01-detail-menu-01.png) SHA `685a142c7cf0868a4215097651ca099b7741762c11f833ecbfa66dfcf6adf86c`；v2 幾何 max residual 0.8223 px、margin 26.967 px、候選點 `[610,271]`。[Geometry](evidence/e01-detail-menu-01-v2-geometry.json)。 | 原始 trace 記錄 ellipsis 點位序列 `610,100 → 609,99 → 610,100 → 610,100 → 610,89`，中間曾遇 foreground-changed guard；最後 full-display SCK 拍到五列。之後 blank titlebar `[500,50]` 關閉。無 menu row click。 | 0／0 | 0；bytes、decode、穩定 inventory NOT_RUN。 | E01 action receipt 記 state mutation=false、destination_created=false。 | `MENU_OBSERVED_AND_CLOSED`；首張圖當時 mapping 尚待；v2 對同一張已保存原圖後處理通過候選幾何檢查，仍未派送。 |
| E02 前景中斷後 menu 重測及 transaction preflight；同一 65 張 | 使用者取回前景後再明確交還；重新讀 detail。 | [最新重測原圖](evidence/e02-menu-retest-02.png) SHA `254934128ade2f8c4ede672461d3d127d6bedbdf8c5158e1b70092d865b0a8df`；max residual 0.8223 px、margin 27 px、候選點 `[610,271.5]`。[Geometry](evidence/e02-menu-retest-02-geometry.json)。 | 單擊 ellipsis `[610,100]` 後 SCK 立即見 native popup；blank titlebar `[500,50]` 安全關閉。之後 acquire 被 canonical writer guard 拒絕。 | 0／0 | 0 files；bytes、decode、穩定 inventory NOT_RUN。 | revision 34／state SHA 前後相同；無 owner／已提交 intent；acquire 留下空目的地目錄。 | Menu mapping 候選 `PASS`；交易 `BLOCKED`。 |
| E03 滾輪至下一本與第二筆備份 | 第二個不同 eligible fingerprint 尚未選取；第一筆未 VERIFIED。 | NOT_RUN。 | 未回列表滾輪；scroll transition、overlap、第二本 detail 均 NOT_RUN。 | 0／0 | 0；NOT_RUN。 | 未建立第二個 run。 | `NOT_RUN`，不得由 E01/E02 的 menu PASS 推論。 |
| E04 duplicate／preservation／terminal 狀態驗收 | 目標交易沒有完成；無第二本。 | N/A。 | 沒有 terminal close 或後續 duplicate-run replay。 | 0／0 | 0；NOT_RUN。 | 只有 revision 34 唯讀前後比對；未做完成交易後 preservation acceptance。 | `NOT_RUN`。 |

## E2E 狀態與六項狀態分開記錄

| 狀態主體 | 本次結果 |
|---|---|
| `PRIMARY_OUTCOME_STATUS` | INCOMPLETE：尚未證明能自動完成 LINE 相簿備份。 |
| `IMPLEMENTATION_STATUS` | PARTIAL：task-local v2 全螢幕 capture、Vision、geometry、decoder 已 build；一本相簿的日期／張數確認與 detail menu 定位成功。 |
| `CORE_ACCEPTANCE_STATUS` | NOT PASS：沒有 Save All、正確 chooser、下載與交易終結證據。 |
| `REQUIRED_VERIFICATION_STATUS` | BLOCKED：owner acquire 在 canonical state writer guard 被拒絕；canonical state 中沒有已提交 intent。 |
| `INDEPENDENT_ACCEPTANCE_STATUS` | NOT RUN；原計畫要求 E2E／報告後再做。 |
| `TASK_CLOSURE_STATUS` | OPEN：等待 state-writer／authorization 架構解法，並需完成第二本相簿及其下載驗證。 |

## 尚未驗證與不能據此推論的事項

- Save All 實際 click、macOS 儲存 chooser、目的地路徑輸入／確認、下載開始及 at-most-once dispatch。
- 65 張相片真實落盤、5 秒間隔三次穩定 inventory、每個檔案完整 ImageIO 解碼、registry append 與 VERIFIED owner release 同 revision readback。
- 第二筆不同 eligible fingerprint 的 E2E；從 detail 返回相簿列表、滾輪到下一本、確認 scroll effect、辨識卡片、再次點入正確 detail 並下載。本次沒有測試滾輪。
- app-bound screenshot 省略 popup 的更深層作業系統原因；本次只證明 SCK 完整 display 能看到該 popup。
- CUA screenshot bytes 沒有被另存為 PNG；幾何 evidence 使用當時 CUA screenshot 尺寸及位置觀察，並以 SCK 同源畫面／window frame 綁定。這個限制已記在 closure record。

## 後續 Implement 規劃建議：明確加入「滾輪到下一本」測試

雖然原計畫 §11 要求兩本不同相簿，且 E02/E03 已描述卡片觀察與下一 eligible album 流程，本次實作測試只到第一本文字與 menu 校準。因此後續 implement 規劃應把「下一本相簿」明列為獨立 gate，而不把兩筆 transaction 數量當成已覆蓋滾輪行為：

1. 第一筆必須完成目的地確認、穩定檔案數、全檔解碼、VERIFIED registry/readback 與 owner release；先重新 snapshot，將這本加入已驗證 history。
2. 用 fresh CUA observation 回到相同 group 的 Albums 列表；記錄同一 session、PID、window、layout 和完整清單位置。確認 57、182 及剛完成的第一筆都由動態 duplicate gate 跳過。
3. 至少實際執行一次 bounded 0.25-page scroll transition，作為使用者特別要求補測的獨立 gate；即使 eligible 卡片原本完整可見，也不能因此跳過滾輪測試。一次 scroll 後重新做 CUA + SCK before/action/after observation；不可沿用上一張 frame 的 card 座標。保存 scroll 前後影像與 hash、工具 action/result、同 group／surface／session／PID／window／layout、相鄰完整 fingerprint 的有序 overlap，並確認至少一張新的完整 eligible 卡片出現。如果下一本因無 eligible target 或前置 writer gate 無法執行，分別標記 `NO_ELIGIBLE_TARGET` 或 `SCROLL_TEST_NOT_RUN`／PARTIAL，不得把它算成 scroll PASS。
4. 只在新畫面中選唯一、完整、metadata 可讀的 next eligible card；以 metadata 安全區而非縮圖點擊。若日期/count 模糊、卡片部分出界、相鄰 overlap 無法連續對上或 scroll 效果 UNKNOWN，停止導覽，不猜點、不連續重試。開啟後再核對 detail 的 exact date/count/group。
5. 對第二本重新計算目的地與 duplicate gate，取得該 run 的 owner/context、持久 intent；依 fresh menu capture/geometry，最多一次 Save All 和一次精確目的地 confirmation，之後重跑穩定 inventory／全解碼／terminal state 驗收。
6. 報告必須區分「單相簿 menu 校準」、「滾輪與 next-card grounding」、「第一筆備份完成」、「第二筆備份完成」。若沒有另一個 eligible album，明確回報 `NO_ELIGIBLE_TARGET`，不可重開 57、182 或已 VERIFIED 相簿製造第二筆測試。

## 核心證據索引

以下路徑相對於本 task package；絕對前綴均為：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-e2e-fullscreen-repair-20261010/`。

| 證據 | 相對路徑 | SHA-256／說明 |
|---|---|---|
| 前景 group/list 全螢幕成功圖 | [e00-display-04.png](evidence/e00-display-04.png) | `cff72b134c0f53d54256dbe0322da2fb95341c7ad6dca41b0a45e72a64d65064` |
| 65 張 detail 全螢幕圖 | [e01-album-detail-01.png](evidence/e01-album-detail-01.png) | `0f62ddd272b399b4a29a62a1a2244eda985de9655e063e8e58e37209f3090ebf` |
| 較早拍到 detail menu 的全螢幕圖 | [e01-detail-menu-01.png](evidence/e01-detail-menu-01.png) | `685a142c7cf0868a4215097651ca099b7741762c11f833ecbfa66dfcf6adf86c` |
| 較早 menu 圖的 v2 幾何 replay | [e01-detail-menu-01-v2-geometry.json](evidence/e01-detail-menu-01-v2-geometry.json) | `0f5b27c068a93cae3ef606e3aba52091a0203e88021f23bda7aa6a0b69a78a84` |
| 成功拍到 Save All popup 的完整桌面圖 | [e02-menu-retest-02.png](evidence/e02-menu-retest-02.png) | `254934128ade2f8c4ede672461d3d127d6bedbdf8c5158e1b70092d865b0a8df` |
| 同圖 SCK manifest | [e02-menu-retest-02.json](evidence/e02-menu-retest-02.json) | `d2c740b77804de12d0307ddfc2500d1952ffd8f31ebb593d38cc01b9f769632c` |
| 同圖 Save All OCR | [e02-menu-retest-02-ocr.json](evidence/e02-menu-retest-02-ocr.json) | `0abab471e2752be98fbea24e61e49465fc92c7122a2c9fbc568ee0f855889989` |
| 同圖幾何結果 | [e02-menu-retest-02-geometry.json](evidence/e02-menu-retest-02-geometry.json) | `e312f68b387c3795459281229d75022e2745b1309185fe02bf1dc08c059af484` |
| 安全關閉後完整桌面圖 | [e02-menu-retest-03.png](evidence/e02-menu-retest-03.png) | `b4bbb0d007d0b21fa105a3cab4f4569045ce1c5750508bb70be4bed436612d5a` |
| 七項幾何測試 | [test-geometry-v2.log](evidence/test-geometry-v2.log) | `7aa0cdbf4d17753d2e9ccd208527aeb88f3188a8a6134024477c574ab4e1ab58` |
| build attempt 08 | [attempt-08.json](build/attempt-08.json) | `70bd64d7fff3ccc06a680193081b20a01624d1ed81b9c93a8b1bdd6ed0680dc0` |
| transaction state gate | [e02-state-writer-gate.json](evidence/e02-state-writer-gate.json) | `5e7d328ac3a738e56eaae1228bb1cb60b3ee50fa2e2639fa40f9b39e2156c19a` |
| 尚未提交的 task-local intent payload | [intent-payload.json](evidence/runs/RUN-20261010-e02-65-c6aba32e1f104d91b01aa0ffd372bf71/intent-payload.json) | `1a461ff8d7e3e912696d6134f149a1a70ca3b6d82ad0552a678de141d66edd5d` |
| state 前後 snapshot | [before](evidence/snapshot-e02-65-pre-acquire-r34.json) / [after](evidence/snapshot-e02-65-after-acquire-refusal-r34.json) | 都是 revision 34、state SHA `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9` |

主要 source：[`FullscreenCapture.swift`](candidate/v2/FullscreenCapture.swift)、[`VisionRegions.swift`](candidate/v2/VisionRegions.swift)、[`geometry.py`](candidate/v2/geometry.py)、[`operator.py`](candidate/v2/operator.py)、[`profiles.json`](candidate/v2/profiles.json)。已完成的 SCK/Vision/geometry 成功鏈證明「原生 menu 可見並可定位」；state writer refusal 和缺少 Save All／下載／第二本相簿證據，仍使自動備份整體結果保持未完成。
