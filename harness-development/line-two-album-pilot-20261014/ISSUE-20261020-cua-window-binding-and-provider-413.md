# 問題單：CUA 視窗綁定／座標語意漂移與模型請求 413

日期：2026-10-20（Asia/Taipei）  
狀態：根因已收斂；A 相簿已用人工診斷流程完成 Save All 與 56 檔內容驗證，但正式產品 E2E 仍 BLOCKED  
嚴重度：High（會造成錯窗點擊、錯誤畫面判定，以及長流程中斷）  
影響範圍：LINE macOS 多視窗 CUA 操作；Codex／Ollama Cloud 請求上下文管理  
證據等級：真實 macOS LINE GUI、真實下載檔、SHA-256、完整解碼；另有 provider 原始錯誤字串

## 一句話

這輪不是「Computer Use 看不到相簿名稱」。真正可重現的兩個問題是：**(1) CUA 的 app/window binding 與座標系沒有在同一個 fresh surface 上閉環，導致 raw click 可能落到另一個 LINE 視窗或卡片封面；(2) 長流程把重複全幅截圖、完整 AX 樹與大量工具輸出累積進同一個模型請求，最後超過 `https://ollama.com/v1/responses` 的 body limit，回傳 413。**

## 六狀態

- `PRIMARY_OUTCOME_STATUS`: `NOT_ACHIEVED`（B 尚未 Save All／下載／驗證；正式兩本 E2E 未完成）
- `IMPLEMENTATION_STATUS`: `NOT_CHANGED`（本輪沒有修改產品程式、grant、ledger、checkpoint 或 state）
- `CORE_ACCEPTANCE_STATUS`: `PARTIAL_MANUAL_DIAGNOSTIC`（A 的 Save All、56 檔下載、內容驗證 PASS；formal VERIFIED readback NOT_RUN）
- `REQUIRED_VERIFICATION_STATUS`: `PARTIAL`（A PASS；B NOT_RUN；正式產品入口 BLOCKED）
- `INDEPENDENT_ACCEPTANCE_STATUS`: `NOT_RUN`
- `TASK_CLOSURE_STATUS`: `OPEN`

## 根因一：CUA 視窗與座標沒有同 surface 閉環

### 觀察事實

1. LINE 同時存在主聊天視窗、相簿列表視窗與相簿詳細頁獨立視窗。`getApp("LINE")` 取得的 app surface 不保證每次都是操作者當下看到的那一個視窗。
2. 舊的固定座標與「卡片中心」啟發式不是當次 grounding 結果。卡片中心落在 2×2 封面縮圖時，LINE 會開啟 `(1/N)` 單張檢視器；名稱／metadata strip 才會開啟相簿 grid 詳細頁。
3. 選單可能超出被綁定視窗的截圖邊界；若只在舊截圖上找座標，會把點擊送到另一個 surface。
4. 本輪 A 的成功路徑是：先確認 detail window，對同一個 fresh screenshot 做 OCR，取得 `儲存全部` 的文字框，再送出唯一一次 menu click。不是重用歷史座標。

### 根因

**缺少「視窗 inventory → raise target → fresh screenshot → OCR/target derivation → click → post-click identity」的單一閉環。** 只要其中一歩跨到另一個 snapshot／window，點擊語意就會漂移；產品層的 `name_target_point` 與 post-click `ALBUM_DETAIL_GRID` guard 可以阻擋錯誤，但 raw CUA 診斷若繞過產品路徑，就沒有這層保護。

### 最小修正

- 每次操作前列出 LINE 視窗，選定唯一 target window，必要時先 raise。
- 只使用該 window 的 fresh screenshot 與 OCR box 推導 click point；不得重用歷史座標，不得以卡片幾何中心代替名稱。
- 點擊後必須驗證 grid identity：日期、張數、可捲動 grid、右上 `⋯`，且不得出現 `(1/N)`。
- 若 menu 或 chooser 不在被綁定截圖內，重新綁定或改用全螢幕 capture；不要對猜測座標送出點擊。

## 根因二：模型請求 413 Payload Too Large

### 原始錯誤

```text
unexpected status 413 Payload Too Large: Request Entity Too Large
(ref: 7caddeb4-33b7-4f9f-9f9e-4cf0e6e6312f)
url: https://ollama.com/v1/responses
request id: 7caddeb4-33b7-4f9f-9f9e-4cf0e6e6312f
```

### 第一性原理

413 是 HTTP request body 超過 provider 限制，不是 LINE、CUA、macOS TCC 或下載流程的錯誤。長流程中若每一輪都把下列內容重新放進同一個上下文，body 會單調累積：

- 重複的全解析度截圖（或 base64 影像）；
- 完整、未裁切的 AX 樹；
- 數萬字的工具輸出、日誌與舊報告；
- 同一畫面的多張近似截圖。

只要上下文只增不減，最終必然跨過 provider 上限；重試同一個過大請求只會再次 413。

### 已採取的 containment

- 截圖先落盤，模型只接收縮圖、裁切或 OCR 摘要；必要時使用 `emit:false`。
- 不再輸出完整 AX 樹；只輸出 filtered window/element identity。
- 工具輸出限制在數百行內；長清單以檔案／manifest 保存，不貼回模型。
- 每輪只保留目前 blocker 所需的摘要；接近上下文上限前建立 checkpoint，換新 session 繼續。
- 禁止在 prompt、commit message 或報告中貼 base64 影像與完整私有日誌。

### 回歸條件

- 下一次長流程不得再出現同一個 413。
- 若 provider 仍回 413，必須先縮小 request、分段讀取或換新 session，不得原請求盲重試。

## A 相簿實測結果

- 相簿：`2024/05/27～05/31`，`56張照片`，日期文字 `2024.06.01`。
- 名稱／metadata strip 點擊後開啟 grid 詳細頁，未出現 `(1/N)`。
- `⋯` 選單實見：`選擇項目`、`修改相簿名稱`、`儲存全部`、`刪除相簿`、`分享相簿`。
- `儲存全部` 僅派送一次。
- chooser 顯示 `Downloads`；先建立空目的地資料夾，再以 Go to Folder 進入並按一次 `打開`。
- 下載：56 檔、18,117,492 bytes；檔名索引 1..56 無重複；全部 JPEG。
- `ffmpeg` 完整解碼：0 errors。
- 目的地（公開發布時群組名已遮罩）：`backups/<REDACTED_GROUP>/2024-05-27_2024-05-31_56張`。
- 正式 state／ledger：未寫入；因此不能宣稱 formal product `VERIFIED`。

## 邊界

- 本輪是 `MANUAL_DIAGNOSTIC`，不是獨立 DeepSeek `deepseek-v4.1-flash:1017` 的正式 E2E。
- A 的檔案內容 PASS 與正式產品 `VERIFIED` 狀態是兩個不同層級；本問題單只主張前者。
- B 尚未 Save All／下載／驗證，不得用歷史相簿或 65 張已人工備份相簿湊數。
- 不重送 Save All；若下一次結果不明，停在该操作並保存證據。

## 下一步

1. 由 Owner 重新提供一次有效的 LINE 前景交接。
2. 在 fresh surface 上找到不同的 B（目前候選：`2024/05/20～05/24`、53 張，未在 state verified 清單）。
3. 以名稱文字 OCR 框開啟 grid，驗證 identity 後才開 `⋯`。
4. 建立空目的地，單次 Save All，完成 chooser、53 檔 SHA-256、ImageIO/ffmpeg 解碼。
5. 再由獨立 DeepSeek 1017 Session 做正式產品 E2E；本問題單不代替該驗收。
