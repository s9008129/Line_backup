# HANDOFF H3.0 — macOS 內建 Vision 取代 tesseract ＋ AI Agent 自主自動化測試

- 版本：H3.0（2026-09-17，Asia/Taipei）
- 用途：**新討論串（新對話）的啟動輸入**。新對話的 agent 必須先完整讀完本檔，再開始動作。
- 搭配指令：`GOAL-vision-agent-next-conversation.md`（同 repo 根目錄；內容是要貼進新對話的 `/goal` 指令）
- 前一代交接：`handoff.md`（H2.1，2026-09-16）＝上一個階段的歷史紀錄，**本檔不動它、也不取代它**；新對話請認本檔。
- 撰寫時 repo 狀態：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`，branch `master`，HEAD `4d6c307`，工作區乾淨。
- 語言：繁體中文（技術名詞保留英文）。寫給兩種讀者：接手 agent（全檔）與非技術主持人（每節「白話」框）。

---

## 0. 白話總結（給非技術主持人）

一句話：我們已用「macOS 內建 Vision」在**同兩張畫面上實測**，它把卡住我們的「照片張數」讀對了（原工具 tesseract 讀成 75、Vision 讀成「57張照片」信心 1.00）；新對話要把這個內建辨識**正式接進工具鏈**，並讓一個 AI Agent **自動、可重複地測它真的有效**。

新對話開始前，要知道三件事：

1. **正式判定還沒換**：現在正式流程用的還是舊的 tesseract；要換掉它，依照我們的安全規則，必須走一輪完整流程（修計畫 → 兩位獨立複審 → 重編交接 → 新的實作者執行 → 獨立驗收）。這一輪就是新對話要做的。
2. **有一個舊決策還等你**（見 §11）：上一輪「點開相簿、觀察 ⋮」的實驗，停在張數判讀失敗（就是上面那個 75≠57）。你要選：(A) 把它標記為「這條路線不需要了」結案；或 (B) 之後再開一次「一次性授權」，讓你現場看 agent 把**相簿內部**的 ⋮ 點開——**只觀察，不點任何選單項目**。你還沒回答，新對話不會擅自動作。
3. **AI Agent 的自主是有界的**：失敗最多 5 次就停下來通知你（不再 try 兩小時）；所有畫面擷取只存在 /tmp 給程式讀，**永遠不會在對話裡貼圖**；任何真的要「點畫面」的動作，都要你再給一次明確授權，agent 不得自我授權。

---

## 1. 任務總覽（兩個目標）

主持人原話（2026-09-17）：

> 「1.我要你改成 macOS 內建 Vision。2.完成後我要你撰寫一個詳細精準的 GOAL 指令。……我要在新的討論串去實作這個 macOS 的 Vision，然後再搭配整個 GOAL 功能來去做一個 AI Agent 的自動化測試作業。」
> 「第一，我們要先把 macOS 內建的 Vision 這個功能來取代目前的 OCR。第二，你要做一個 AI Agent 的自主自動化測試，來測試我們所做的這一個視覺化辨識有沒有效，有沒有辦法來解決目前的問題。」

任務解讀（本檔為權威版本）：

- **目標一（Vision 替換）**：把正式驗證鏈中的 tesseract OCR 讀取角色，改為 **macOS Vision framework（`VNRecognizeTextRequest`）**。「正式」＝三個凍結 v3 工具（`locate_album_card.py`／`verify_album_open.py`／`locate_album_ellipsis.py`）實際使用的讀取器。這是**語意變更**：必須走 harness CRITICAL 流程（見 §10），不得以「小修改」直接改工具。
- **目標二（AI Agent 自主測試）**：建立一個**有界**的 AI Agent 自主測試作業，用可重跑、append-only 的證據證明：(a) Vision 讀取器在關鍵欄位（日期標題、照片張數、群組名）上比 tesseract 可靠；(b) 以 Vision 為讀取器重跑凍結的驗證邏輯時，「75≠57」這個卡點會消失（先在**凍結幀**上做離線重跑示範；正式的接受語意由 Rev21 計畫定義）。測試設計起點見 §8（C1–C5）。

---

## 2. 背景：卡點在哪裡、為什麼是 Vision

### 2.1 目前卡住的點

上一輪（route attempt-05）依主持人授權，在 LINE 相簿列表點了一次目標相簿卡（一次、不重試）。畫面**有成功進入相簿視圖**（日期標題 `2024/05/13~05/17` 可讀、64.7% 像素變動），但凍結的 `verify_album_open.py` 判定 `TARGET_MISMATCH (exit 4)` 而停止——原因：**標題下方的張數區，tesseract 讀成「75」，正確答案是 57**（fail-closed，不送下一個輸入 ⋮）。

### 2.2 唯讀交叉比對的發現（已入庫）

同一批畫面用 macOS 內建 Vision 重讀（唯讀、零輸入、零 UI 動作；證據見 §4）：

- post 幀（點擊後）：Vision 讀出 **「57張照片」conf 1.00**；tesseract 讀「75」。
- s1（1x 裁切）：Vision 讀「57」conf 1.00；tesseract 讀「27」。
- s2（2x 裁切）：Vision 讀「57」conf 1.00；tesseract 讀「5」。
- 日期標題：Vision 在全部四個輸入都讀對、conf 1.00。
- 結論：**卡點的根因是 tesseract 對極小字元的讀值不穩**；同圖 Vision 全對。「57 張」這個事實本身沒有問題，問題在讀取引擎。

### 2.3 白話

> 就像同一個招牌，舊工具近視又老花，一下看成 75、一下 27、一下 5；系統規定「看不到正確數字就停」，所以整個流程卡住。換成 macOS 內建的辨識（Vision），同一張圖直接讀對「57張照片」。新對話就是把這個「好眼睛」正式裝上去，並用自動測試證明它一直看得對。

---

## 3. 現況快照（權威路徑與 SHA-256）

以下全部在撰寫本檔時 **重新實測核對過**（`shasum -a 256`），可直接當驗證錨點。

| 項目 | 路徑 | SHA-256 | 備註 |
|---|---|---|---|
| Task ID | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/` | — | 現行任務目錄（CRITICAL class） |
| 現行計畫 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md` | `4919d87148c68ea3d70cbb9abd258edbd0bfa0b55be5123f7202251e557db17c` | **Rev20**，1,744 行／233,123 bytes；狀態 CANDIDATE，已由兩份獨立複審核准 |
| 計畫複審① | `review/attempt-28/review_report.md`（相對 task 目錄） | `d9bf574facc636c97bfbe080769cce9ed30e5b05c31f7ef0847b0552b99ea09d` | `FINAL_STATUS: PLAN_APPROVED`（Rev20） |
| 計畫複審② | `review/attempt-29/review_report.md` | `540fda1a35590fc4047a49723a204879395c2258ec1597c4d036093f69872683` | `FINAL_STATUS: PLAN_APPROVED`（Rev20） |
| Stage-03 交接（現行） | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/handoff.md` | `ab88e496e7ab24214247a1cc3c5fc65b751e439d3c46238433f65d02361484a4` | 38,196 bytes；**與根目錄 `handoff.md`（H2.1）不同檔** |
| 路線 run-ledger | `evidence/20260916-route/attempt-05/run-ledger.json` | `17b172031a38ea6b5c66ebfedacf748aa1f08b12d572263d13eef02f54465218` | `run_status: STOPPED_AT_S5_TARGET_MISMATCH`；`ledger_state: CLOSED_AFTER_INPUT_1`；`owner_decision_required: true` |
| Vision 交叉比對證據 | `evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json` | `d3ebbaed3db446cfbecd01d74d132764b6a675232b9db9edd2d1af3071dd6d5b` | classification `SUPPLEMENTARY_NON_AUTHORITATIVE`（凍結 verdict 不因它翻案） |
| Vision helper（本檔新增已入庫） | `evidence/20260916-route/tools/vision/vision_ocr.swift` | `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32` | 1,070 bytes；與當初 /tmp 版逐 byte 相同 |
| Vision helper 說明 | `evidence/20260916-route/tools/vision/README.md` | `9fa083d551da6d89fd9e385d228e3041802e1595457169af28b324013318767d` | 建置、輸出格式、讀值表 |
| 目的地（57 張，唯讀） | `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` | — | 實測 57 個檔案（撰寫本檔時再確認）；**永不重下載** |
| 三 v3 工具（凍結） | `evidence/20260916-route/tools/` | 見 §6 | tesseract 呼叫點在 §6 表 |
| v3 自測（13/13） | `evidence/20260916-route/tools/selftest/v3/selftest-summary.json` | `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324` | 13 cases；改工具後必須重跑此自測（新語意由 Rev21 定義） |

撰寫時 HEAD 鏈：`4d6c307` ← `e53f67b` ← `5d3db62` ← `5f3da67` ← `d490354` ← `e242ff4`。

---

## 4. 已完成的唯讀證據：Vision 交叉比對（attempt-05 補充）

證據檔：`evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json`（SHA `d3ebbaed…`）。
性質：**補充、非權威**（`SUPPLEMENTARY_NON_AUTHORITATIVE`）：全程唯讀、零 GUI 輸入、零 UI 動作，只用已存在的 4 個凍結影像檔重讀；凍結的 verdict（attempt-05 的 TARGET_MISMATCH）**不因它翻案**。它證明的是「有更可靠的讀取器存在」，採用與否＝新語意＝要走 Rev21 流程。

四個輸入與讀值（Vision helper，設定：`.accurate`、`zh-Hant`+`en-US`、`usesLanguageCorrection=false`）：

| 輸入 | 尺寸 | SHA-256 | Vision 關鍵讀值 | 凍結 tesseract 讀值 |
|---|---|---|---|---|
| post 幀（點擊後） | 327x643 | `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3` | 標題 `2024/05/13~05/17` conf **1.00** @[14,88,201,110]；**「57張照片」conf 1.00** @[12,120,66,136]；`2024.05.18` 0.50 | 標題可讀；**張數讀「75」→ TARGET_MISMATCH (exit 4)** |
| pre 幀（點擊前） | 327x643 | `3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531` | 標題 conf 1.00；`57` conf 0.50；群組名 `旻議允禎…` 0.50（1x 誤字） | `57` 可讀 |
| s1 探針裁切（1x） | 327x643 | `aea53a0df8c4ef20488446dbccc42fa84ecd72c36aad71d42199f20b9e30f5c3` | 標題 conf 1.00；`57` conf **1.00** @[12,467,32,481]；群組名 0.50 | 張數讀「27」→ locate exit 5 |
| s2 探針裁切（2x） | 654x1286 | `7b9d0a19323e0f7341d2ee9722415251195531dc067b773f231676729c63721b` | 標題 conf 1.00 @[30,900,256,926]；`57` conf **1.00** @[30,934,62,958]；群組名 `旻謙允禎…` **1.00**（2x 修正） | 張數讀「5」→ locate exit 5 |

原始 stdout 逐行轉錄已嵌在 crosscheck JSON 內；當次 stdout 檔（/tmp，易失、未入庫）SHA：post `5c86dda8ab2b80fa0ce8177891bb312dae0d4693e4fc8e4d1ad813947f5a3a32`、pre `07e3e15605e27631e504898419eb51f1425f6715d4f318d5c827f60cae83e4fb`、s1 `561bb131a8a58a3360bb134dfa2ee1fc9ab3ae2554b29e567c89900dd4c36bfe`、s2 `abf9d75eeab903cfafeb3ca20875461b34d4014ef1719d8e6db58bee2150e39e`。

### 白話

> 同一張相簿畫面：舊引擎把「57張照片」看成「75」；新引擎（Vision）一次就讀對，信心 1.00（滿分）。連群組名裡比較難的字，放大兩倍後 Vision 也修回正確的「謙」。這代表「75≠57」不是資料問題，是引擎問題，換引擎就能解。

---

## 5. Vision helper：原始碼、建置、輸出格式（已凍結入庫）

**已入庫位置**：`evidence/20260916-route/tools/vision/vision_ocr.swift`（SHA `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`，1,070 bytes；與當初實測用的 /tmp 版逐 byte 相同）。說明與讀值表：同目錄 `README.md`。**二進位不進 repo**（重建即可）。

### 5.1 完整原始碼（全文）

```swift
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 2 else { print("usage: vision_ocr <image>"); exit(2) }
let url = URL(fileURLWithPath: args[1])
guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("LOAD_FAIL \(args[1])"); exit(3)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hant", "en-US"]
req.usesLanguageCorrection = false
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do { try handler.perform([req]) } catch { print("OCR_FAIL \(error)"); exit(4) }
let W = Double(cg.width), H = Double(cg.height)
for obs in (req.results ?? []) {
    guard let c = obs.topCandidates(1).first else { continue }
    let bb = obs.boundingBox
    let x0 = bb.origin.x * W, w = bb.size.width * W
    let y1 = (1 - bb.origin.y) * H, h = bb.size.height * H
    let y0 = y1 - h
    print(String(format: "px[%.0f,%.0f,%.0f,%.0f]\tconf=%.2f\t%@", x0, y0, x0+w, y0+h, c.confidence, c.string))
}
```

### 5.2 建置與呼叫

```
swiftc -O evidence/20260916-route/tools/vision/vision_ocr.swift -o /tmp/vision_ocr
/tmp/vision_ocr <image>
```

- 建置環境：Apple Swift 6.3.3（swiftlang-6.3.3.1.3 clang-2100.1.1.101）、arm64、macOS 26.0；只用 Foundation＋Vision＋AppKit，**無第三方依賴**。
- 當次實測用的 binary：`/tmp/vision_ocr`（67,192 bytes，SHA `f54628e8f42fb65200bf98bf5cc6463937d28781c673c22e5ca8b9418ae3f6c9`；易失，可重建）。
- 輸出（stdout，一行一個觀察）：`px[x0,y0,x1,y1]\tconf=NN\tTEXT`。座標為左上原點像素（y 已從 Vision 的 bottom-left 翻轉）。exit codes：`2` usage、`3` 影像載入失敗、`4` 辨識失敗、`0` 成功（含「無文字」）。
- 與舊鏈差異：tesseract 在此環境**無法開 /tmp 檔案**（`Error in fopenReadStream`），所以舊工具只能 stdin/stdout 管線；Vision helper 直接吃檔案路徑。若 Rev21 決議替換，需定義統一的 frame→讀值介面（檔案或記憶體）與輸出契約。

### 5.3 已知限制

- 讀值≠判定：`conf` 是 top-1 候選信心，**不是**通過門檻；任何 Vision-based reader 的接受規則（例如 conf 門檻、欄位定位規則）必須由 Rev21 計畫明確定義，**不得**臨場放寬 fail-closed 規則。
- 1x 下群組名 `謙` 會讀成 `議`（conf 0.50）；2x 修正為 `謙`（conf 1.00）。張數「57」在 1x/2x 都是 1.00。
- 任何情況下**不得**把主持人的 `禎`（U+798E）與 `楨`（U+6968）合併或正規化。

---

## 6. 凍結工具盤點：tesseract 呼叫點（新串第一步要 grep 的對象）

工具目錄：`evidence/20260916-route/tools/`（全部凍結、唯讀、fail-closed、不送任何輸入）。

| 工具 | SHA-256 | 角色 | tesseract 呼叫點（行） |
|---|---|---|---|
| `locate_album_card.py`（v3） | `500fcadbe8cb47f1cd22f0d247ad7d7d65c84baef4000f2239e1872e340e98e4` | 正式鏈：S3 定位相簿卡可點點 | 第 44 行：`["tesseract", "-", "stdout", "-l", "chi_tra+eng", "--psm", str(psm), "tsv"]`（stdin/stdout，3x upscale） |
| `verify_album_open.py`（v3） | `80504262025cf10202c8938612b5be73f91809578f1317f36733f52b513fa74b` | 正式鏈：S5 判定相簿是否開啟（**卡點本人**） | 共用 `locate_album_card.py` 的讀取器（v3 工具同目錄互相載入，見 README） |
| `locate_album_ellipsis.py`（v3） | `60e3120abb312f189f785f12ee4047f4365028a8759ae88874eebb06046a7deb` | 正式鏈：S6 定位相簿內部 ⋮ | 共用 `locate_album_card.py` 的讀取器 |
| `detect_menu_popup.py`（v2 旁證） | `6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc` | 選單彈出前後差異判定 | 第 47 行：`["tesseract", "-", "stdout", "-l", "chi_tra+eng", "--psm", "6", "tsv"]` |
| `locate_card_ellipsis.py`（v2 旁證） | `8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e` | 卡片層 ⋮（attempt-04 用） | 第 41 行：`["tesseract", img3x_path, base, "-l", "chi_tra+eng", "--psm", "6", "tsv"]`（注意：這是唯一用檔案路徑的呼叫點） |
| 自測（13 cases） | `selftest/v3/selftest-summary.json` = `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324` | 三 v3 工具的 refusal path 全覆蓋 | 改 reader 後必須重跑；預期有些 case 的 OCR 行為需重新定義（Rev21） |

**新對話第一步（唯讀、零風險）**：`grep -n "tesseract" evidence/20260916-route/tools/*.py` 確認以上呼叫點與介面邊界，然後在 Rev21 計畫裡定義「Vision reader」替換契約（輸入、輸出、門檻、fail-closed 語意、自測更新方式）。**不要在沒有 Rev21 核准下直接改任何工具檔**。

---

## 7. 路線（attempt-05）現況與待決事項

- `run_status: STOPPED_AT_S5_TARGET_MISMATCH`；`ledger_state: CLOSED_AFTER_INPUT_1`；`owner_decision_required: true`（run-ledger SHA `17b17203…`）。
- 輸入盤點：**相簿卡點擊 SPENT（1/1）**；**⋮（輸入②）UNSPENT（0/1）但前置條件 `ALBUM_OPEN_VERIFIED` 未成立**——依凍結 runbook 不得送出；重試預算 0。
- 停止原因（原文摘要）：post 幀日期標題可讀、64.7% 像素變動（相簿視圖確實開了），但張數框讀成 75≠57，fail-closed 停止；未開任何選單、未動其他東西，立即通知主持人。
- 現行畫面狀態（停止時）：相簿樣式的視圖開著（日期標題＋照片格）；**沒有**我們打開的選單/對話框。
- 未寫入 `route-result.json`（未執行任何 ⋮ 觀察）。
- **待主持人決策（二選一，agent 不得自行選）**：
  - **(A) 結案**：明示 `ROUTE_NOT_NEEDED`，把路線卡點關閉（依 Rev20 §20.3 需主持人明示）。
  - **(B) 新一次性授權**：開新的 plan revision／新 one-shot gate，授權在「目前這個已開著的視圖」對**相簿內部** ⋮ 送一次觀察（只觀察、不點任何選單項目）。注意：這條要搭配新 revision，因為現行授權的輸入②以前置成立為條件。

### 白話

> 上輪實驗「點開相簿」成功了、但舊引擎把 57 看成 75 而自動煞車；⋮ 那一步還沒做（授權也還沒用到）。你可以選：這件事先記「不需要」結案；或之後再授權一次，讓我點開相簿裡的 ⋮ 只觀察（不點任何功能）。

---

## 8. AI Agent 自主自動化測試：規格建議（給 Rev21 規劃的起點）

**目的**：證明「Vision 讀取器有效，且能解決卡住我們的 75≠57 問題」。**自主但嚴格有界**。

### 8.1 建議驗收準則（C1–C5；最終以 Rev21 複審版為準）

| 代號 | 內容 | 判法（建議） | 風險層 |
|---|---|---|---|
| C1 | post 幀（`4cb8a6b4…`）用 Vision reader 讀出張數＝57 | 讀值正規化後含 `57` 且欄位落於標題下方張數區 | 離線（零輸入） |
| C2 | 同輸入重跑 N≥5 次讀值逐次一致（決定性） | 每次 stdout 逐行相同（或允許 conf 抖動？→ Rev21 定義） | 離線 |
| C3 | 日期標題 `2024/05/13~05/17` 在 pre/post 兩幀皆讀對 | 逐字比對（全形/半形、`~` 變體規則由 Rev21 定義） | 離線 |
| C4 | 以 Vision reader 取代 tesseract 重跑凍結 `verify_album_open.py` 於 attempt-05 的 pre/post 幀 → 應達 `ALBUM_OPEN_VERIFIED`（示範性；正式語意需 Rev21 定義） | 在**凍結幀**上離線重跑，輸出對照表；標記 `DEMONSTRATION_ONLY` | 離線 |
| C5 | 1x/2x 裁切（`aea53a0d…`／`7b9d0a19…`）皆讀出 57 | 同 C1 判法 | 離線 |

以上全部**不需要任何 GUI 輸入**，可在隔離環境重跑。若要加「活體層」（read-only 螢幕擷取後重讀），屬 read-only 可做；只要碰到「點擊」＝**新的 owner gate**（見 §9）。

### 8.2 自主迴圈邊界（主持人明示）

- 失敗（含 verdict 非預期、工具非零退出、讀值不符）**累計 5 次即停**，寫下停止原因＋證據，通知主持人介入。**禁止**長時間無限重試（主持人原話：「不要 try 兩小時」）。
- 每個步驟 append-only 證據：JSON＋SHA-256；不覆寫歷史檔。
- **零對話圖片**：影像只落 /tmp（或工作目錄）供程式讀；對話/證據只出現路徑與 SHA。背景：本流程曾在對話爆過 60 張圖片上限（ref `05ffef68-274a-4707-9db7-62f0c4c47ff8`），之後嚴禁。
- Agent 不得自我授權 GUI 輸入；不得因為「差一步」就自行多點一下。

### 8.3 測試產出建議位置

- `evidence/20260916-route/agent-e2e/attempt-NN/`（新目錄；append-only；每 attempt 一組 `summary.json`＋原始讀值檔＋SHA 表）。具體命名待 Rev21 定。

---

## 9. 硬邊界與禁令（新對話不可違反）

1. **零對話圖片**（60 張上限曾爆；ref `05ffef68…`）。影像只給程式讀，報告只用路徑/SHA。
2. **所有 GUI 輸入 at-most-once、零重試**；非明確 AFFIRMATIVE 的授權一律當作未授權而停止。
3. **永不點選任何選單項目**；**特別點名「Save All（儲存全部）」不可點**。目前畫面上沒有我們打開的選單。
4. 不碰 chooser（檔案選擇器）；不送鍵盤輸入；不做 AX 寫入。
5. **正式 config／state／run-log 唯讀**；`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` 的 57 張**永不重下載、永不刪改**。
6. `禎`（U+798E）與 `楨`（U+6968）**永不合并/正規化**。
7. **換 OCR 引擎＝語意變更**：必走 Rev21＋獨立複審＋（如涉 GUI）owner gate；「補充證據」不得翻案任何凍結 verdict。
8. 不得使用歷史座標當輸入依據（一律現幀推導）。
9. 不新增第三方依賴；Vision 用系統內建 framework。
10. 每次階段完成→深度梳理＋**繁中四段式 commit**（意圖／做了什麼／驗證／下一步建議）——主持人常駐指令。

---

## 10. 新對話的建議工作流程（Harness CRITICAL，逐步）

| 階段 | 內容 | 產出 |
|---|---|---|
| Phase 0 唯讀基線 | 讀本檔＋GOAL；`git status`；重算 §3 SHA；重跑 §5 建置與 C1/C3/C5 離線讀值做 sanity（零輸入） | 基線快照（SHA 對照表） |
| Stage 01 規劃 | 建立 **Rev21** plan（Goal Contract、CORE＝Vision 替換＋agent 測試；SUPPORTING／BEST_EFFORT 明確標記；gating 語意、門檻、fail-closed 規則、自測更新策略） | `plan.md` Rev21（同一 TASK_ID） |
| Stage 02 獨立複審 | fresh context 雙複審（append-only `review/attempt-NN/`），直到 `PLAN_APPROVED` | 兩份 review reports |
| Stage 03 交接重編 | 依核准的 Rev21 重編 task `handoff.md`（舊版先封存） | 新 task handoff（記 revision/hash） |
| Stage 04 實作 | fresh implementer：改 reader、跑自測（13 cases 對應更新）、跑 C1–C5、產出證據 | 程式變更＋evidence |
| Stage 05 驗收 | 依 `INDEPENDENT_ACCEPTANCE_REQUIRED` 執行獨立驗收（E2E_REQUIRED 由 Rev21 定；離線重跑屬 integration/contract 等級，不得冒充 live E2E） | `e2e/attempt-NN/`＋`result.md` |

**升級條件（遇到即停、記證、通知主持人）**：語意變更需求超出 Rev21 授權；自證/污染疑慮；同根因連續 2 次失敗；需要新 GUI 授權；任何會動到 57 張/正式資料的念頭。

---

## 11. 待決事項（給主持人的決策清單）

1. **路線 attempt-05 收尾（二選一）**：(A) 明示 `ROUTE_NOT_NEEDED` 結案；或 (B) 之後開新一次「⋮ 只觀察」gate＋新 revision。**未決前，新對話不得對路線做任何動作。**
2. **Vision reader 接受規則**：conf 門檻、欄位定位容差、讀值正規化（例如 `57張照片`→`57`）、重跑決定性判定——留給 Rev21 規劃＋複審決定；主持人只需在 Rev21 的 owner view 確認白話摘要。
3. （已決策，僅記錄）2026-09-17：主持人拍板「改成 macOS 內建 Vision 取代目前 OCR」。

---

## 12. Owner 偏好與常駐指令（新對話要遵守）

- 主持人為非技術者：對外回報一律**最白話**；先講「結果、卡在哪、要決策什麼」。
- **三個結果分開報告**：①本相簿資料結果 ②可重用能力結果 ③整體任務結案。only ①與②皆成立才算 complete。
- 每階段完成→**深度梳理上下文**＋**繁中四段式 git commit**（意圖／做了什麼／驗證（含實測證據）／下一步建議）並實際 `add`＋`commit`。直到任務結束或主持人終止。
- 失敗 5 次即停並通知（不再長跑）。
- 回報格式偏好：簡短、可直接掃描；決策點要列選項與建議。

---

## 13. 證據索引（本檔引用）

- 本檔：`handoff-vision-agent-2026-09-17.md`（repo 根目錄）
- 指令檔：`GOAL-vision-agent-next-conversation.md`（repo 根目錄）
- Vision 證據：`evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json`（`d3ebbaed…`）
- Vision helper：`evidence/20260916-route/tools/vision/vision_ocr.swift`（`4fc9fa2b…`）＋`README.md`（`9fa083d5…`）
- Run-ledger：`evidence/20260916-route/attempt-05/run-ledger.json`（`17b17203…`）
- 工具：§6 表（全部 SHA 已列）
- 現行計畫/交接/複審：§3 表（全部 SHA 已列）
- 舊世代紀錄（不動）：根目錄 `handoff.md`（H2.1）、`GOAL-next-conversation.md`、`LINE-BACKUP-GOAL-HANDOFF-2026-09-15.md`

— 本檔結束（H3.0）。
