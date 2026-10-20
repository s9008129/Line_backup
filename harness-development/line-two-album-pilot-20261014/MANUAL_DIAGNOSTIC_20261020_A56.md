# MANUAL_DIAGNOSTIC 2026-10-20：A 相簿 Save All、下載與內容驗證

日期：2026-10-20（Asia/Taipei）  
模式：`MANUAL_DIAGNOSTIC_NOT_FORMAL_E2E`  
相簿：`2024/05/27～05/31`（56 張）  
結論：A 的 Save All、56 檔下載與內容驗證 **PASS（manual diagnostic）**；formal state `VERIFIED` readback **NOT_RUN**；B **NOT_RUN**；正式產品 E2E **BLOCKED/NOT_RUN**。

## 0. 邊界

本輪證明的是：

- 在真實 macOS LINE 的相簿詳細頁，點擊右上 `⋯` 可看到含唯一 `儲存全部` 的選單。
- 一次 `儲存全部` 派送、一次 chooser 確認，可將 A 的 56 張照片下載到指定空資料夾。
- 56 個檔案可逐一計算 SHA-256，並完成全檔解碼。

本輪不證明：

- 正式產品入口 `openAlbum` 已完成本次交易；
- `state/backup_state.json` 或 ledger 已寫入 `VERIFIED`；
- B 相簿已完成 Save All、下載或驗證；
- 這是獨立 DeepSeek `deepseek-v4.1-flash:1017` 的正式 E2E。

> **後續：** B 相簿 `2024/05/20～05/24`、53 張也已以相同 manual diagnostic 模式完成 Save All、下載與內容驗證。見 [`MANUAL_DIAGNOSTIC_20261020_B53.md`](./MANUAL_DIAGNOSTIC_20261020_B53.md)。兩本手動流程 PASS 仍不代表正式產品 TWO_ALBUM_AUTO 或 state `VERIFIED`。

## 1. 為什麼先手動診斷

正式產品執行目前仍受 review／source-runtime binding 阻塞：authorizer 回報 `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`，ONE56 bundle 仍待外部 review，既有 one-scroll grant 已關閉，且安裝 source/runtime 與受審候選不同。這輪因此只做 owner 授權範圍內的真實 UI 診斷，不偽造 grant、不重置 ledger、不修改 protected state。

## 2. 實際操作順序

1. 在相簿列表上以 fresh screenshot／OCR 定位 A 的名稱欄，而不是封面中心。
2. 點擊名稱欄，開啟獨立的相簿 grid 詳細頁；畫面顯示 `2024/05/27～05/31`、`56張照片`、`2024.06.01`，沒有 `(1/56)` 檢視器標題。
3. 在詳細頁右上開啟 `⋯`，以同一張 fresh screenshot 的 OCR 結果定位選單。
4. 實見五個選項，順序為：
   - `選擇項目`
   - `修改相簿名稱`
   - `儲存全部`
   - `刪除相簿`
   - `分享相簿`
5. 確認 `儲存全部` 在當次選單中唯一存在，派送 **1 次**。
6. chooser 出現，預設位置為 `Downloads`；先建立空的目標資料夾，再使用 Go to Folder 進入。
7. 目標資料夾確認後按 `打開` **1 次**。
8. 等待下載完成，對檔案數量、bytes、檔名索引、JPEG 類型、SHA-256 與完整解碼做驗證。

## 3. 操作證據

### 3.1 選單

公開去識別化裁切：[`public/manual-diagnostic-20261020-a56/01-menu-crop.png`](./public/manual-diagnostic-20261020-a56/01-menu-crop.png)  
SHA-256：`609a0f9453d61d8776058304f73bbf8cde58b65a5d9584dec5db4e75630f84e3`

OCR 在原始 2294×1490 截圖中的 `儲存全部` 文字框為 `[1297, 417, 107, 30]`。裁切只保留選單面板，不含照片、人名、群組名或本機路徑。

### 3.2 Chooser

公開去識別化裁切：[`public/manual-diagnostic-20261020-a56/02-chooser-crop.png`](./public/manual-diagnostic-20261020-a56/02-chooser-crop.png)  
SHA-256：`ee11f9cf85c4cca372d47936cea585c0e08ac1a3bd97ff3e1890bd7a82ffe9c6`

OCR 觀察到：

- `Downloads` at `[210, 776, 140, 30]`
- 目的地資料夾名稱 at `[957, 407, 357, 30]`
- `取消` at `[1560, 1170, 53, 30]`
- `打開` at `[1731, 1170, 60, 30]`

裁切已排除群組名與帳號路徑。

### 3.3 原始私有截圖

四張原始全幅截圖保存在 `private/manual-diagnostic-20261020-a56/`，`private/` 已由版控排除：

| 檔案 | Bytes | SHA-256 | 用途 |
|---|---:|---|---|
| `pre-saveall.png` | 2546948 | `79c6409382cd7d0b6d26396e631ceb5cf28ab3ac3d45c8ce3d5fde135282099d` | A grid，選單開啟前 |
| `full-ellipsis2.png` | 2546942 | `38f09a8208acf65d11149b6ea464c37b3e3a488124c166cabbde7900105b5631` | 完整 `⋯` 選單 |
| `post-saveall-01.png` | 1493301 | `712ae2e5f76c0b8411e4d90367261bcf1ff9df17d7b3e9973b9b34819f967fda` | Save All 派送後畫面 |
| `chooser-in-dest.png` | 1312611 | `b5f37d921e0015cba2265056fe2d184797a8068533192583a0e00819fa28429c` | chooser 目的地確認前 |

## 4. 下載與內容驗證

目的地（公開時群組名遮罩）：

```text
backups/<REDACTED_GROUP>/2024-05-27_2024-05-31_56張
```

驗證結果：

| 檢查 | 結果 |
|---|---|
| 檔案數 | 56 / 56 |
| 預期張數 | 56 |
| 檔名索引 | 1..56，無重複 |
| 全部 JPEG | PASS |
| 總 bytes | 18,117,492 |
| SHA-256 清單 | 56 筆，[`a56-sha256.txt`](./public/manual-diagnostic-20261020-a56/a56-sha256.txt) |
| 完整解碼 | `ffmpeg` 解碼 56 檔，0 errors |
| 計數穩定取樣 | 2 次，檔案數／bytes 一致 |

結構化摘要：[`a56-verification.json`](./public/manual-diagnostic-20261020-a56/a56-verification.json)  
證據 manifest：[`03-evidence-manifest.json`](./public/manual-diagnostic-20261020-a56/03-evidence-manifest.json)

## 5. 根因分析

### 5.1 相簿名稱 vs 封面

第一性原理：LINE 相簿卡片不是單一 hit target。封面是 2×2 照片縮圖，具有照片檢視語意；名稱／metadata strip 才是相簿容器入口。點封面會開 `(1/N)` viewer，點名稱才會開 grid detail。

本次失敗不是 Computer Use 看不到名稱，而是 raw CUA 使用了卡片中心座標，沒有使用當次 OCR 的名稱文字框。產品的正確路徑本來是 `card_target → name_target_point → openAlbum`；診斷若繞過產品路徑，就必須手動重做同樣的 title-point 與 post-click grid guard。

### 5.2 多視窗綁定與座標漂移

LINE 同時存在主視窗、相簿列表與相簿詳細頁獨立視窗。只靠 `getApp("LINE")` 或歷史座標，無法保證點擊與截圖指向同一個 window surface。正確閉環是：

```text
enumerate windows
→ choose and raise target window
→ fresh screenshot of that window
→ OCR/title bounds in the same coordinate space
→ click inside title bounds
→ verify grid identity and window lineage
```

任何一步若重用舊 snapshot 或跨視窗，就會產生「看起來有座標、實際點錯 surface」的假精準。

### 5.3 413 Payload Too Large

原始錯誤：

```text
unexpected status 413 Payload Too Large: Request Entity Too Large
(ref: 7caddeb4-33b7-4f9f-9f9e-4cf0e6e6312f)
url: https://ollama.com/v1/responses
```

根因不是 LINE，而是模型請求 body 超限。長流程重複攜帶全幅截圖、完整 AX 樹與大量工具輸出，會讓上下文只增不減，最終超過 provider 限制。重送同一個過大請求沒有資訊增益，只會再次 413。

往後必須：

- 截圖落盤，模型只看小裁切／OCR／縮圖；
- 使用 `emit:false` 或等價方式避免影像重複進入上下文；
- 不輸出完整 AX 樹、base64 影像或數萬字日誌；
- 長流程設定 checkpoint，接近上限前換 fresh session；
- 若仍遇 413，先縮小 request 或分段，不得原樣重試。

## 6. 狀態表

| 項目 | 狀態 | 證據等級 |
|---|---|---|
| A 名稱／metadata 點擊 → grid detail | PASS | 真實 GUI screenshot／OCR |
| A 右上 `⋯` → 唯一 `儲存全部` | PASS | 真實 GUI screenshot／OCR |
| A Save All 派送 | PASS，1 次 | 真實 GUI；非正式 gate |
| A folder chooser → 目的地 | PASS，1 次確認 | 真實 GUI screenshot／OCR |
| A 下載 | PASS，56 檔 | 實際檔案系統 |
| A 內容驗證 | PASS | SHA-256＋完整解碼 |
| A formal state `VERIFIED` | NOT_RUN | 未寫入 state／ledger |
| B Save All | NOT_RUN | — |
| B 下載 | NOT_RUN | — |
| B 驗證 | NOT_RUN | — |
| 正式產品 E2E | BLOCKED/NOT_RUN | authorizer/source-runtime review 未完成 |

## 7. 副作用

- Save All 派送：1
- chooser 確認：1
- 下載：56 檔
- LINE 訊息送出：0
- formal intent／ledger／checkpoint／backup state mutation：0
- B 操作：0

## 8. 未知與限制

1. 本輪沒有 formal product invocation receipt、reservation 或 `detail_identity` JSON。
2. formal `VERIFIED` readback 未執行；不能把檔案驗證冒充 state PASS。
3. B 尚未完成；目前只是候選 `2024/05/20～05/24`、53 張，仍需 fresh screenshot／OCR 重新確認。
4. 65 張相簿已在既有人工備份範圍，不得重開或重下載。
5. 本輪不是 DeepSeek 1017 的 independent E2E。

## 9. 下一步

1. Owner 提供一次新的 LINE 前景交接。
2. 以 fresh window inventory／screenshot／OCR 定位不同的 B 名稱。
3. 驗證 B grid identity 後，開 `⋯` 並確認 `儲存全部` 唯一。
4. 建立空的目的地資料夾，單次 Save All，完成 chooser 與 53 檔驗證。
5. 若任何派送結果不明，停止並保存證據，不重送。
6. 由新的獨立 DeepSeek 1017 Session 執行正式 E2E；本報告只作為 manual diagnostic 證據。
