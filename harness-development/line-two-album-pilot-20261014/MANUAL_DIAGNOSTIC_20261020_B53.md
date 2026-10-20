# MANUAL_DIAGNOSTIC 2026-10-20：B 相簿 Save All、下載與內容驗證

日期：2026-10-20（Asia/Taipei）  
模式：`MANUAL_DIAGNOSTIC_NOT_FORMAL_E2E`  
相簿：`2024/05/20～05/24`（53 張）  
結論：B 的名稱導覽、`⋯` 選單、單次 Save All、chooser、53 檔下載與內容驗證 **PASS（manual diagnostic）**；formal state `VERIFIED` readback **NOT_RUN**；正式產品 TWO_ALBUM_AUTO **BLOCKED/NOT_RUN**。

## 0. 邊界

本輪證明的是：

- 在相簿列表向下捲動後，B 的名稱／metadata strip 可以開啟 `53張照片` 的 grid 詳細頁。
- 詳細頁 `⋯` 選單含唯一 `儲存全部`。
- 一次正確的選單選取可開啟 chooser；一次 chooser 確認可下載 53 張照片。
- 53 個檔案可逐一計算 SHA-256，並完成全檔解碼。

本輪不證明：

- 正式產品入口已完成 B 交易或 state readback；
- ledger／checkpoint／backup state 已寫入 B；
- 這是獨立 DeepSeek `deepseek-v4.1-flash:1017` 的正式 E2E。

## 1. 導覽與候選確認

一開始的相簿列表只看到 A 與已人工備份的 65 張相簿；B 不在初始 viewport。執行兩次有界的 0.25 viewport 向下捲動後：

- A 從 `y≈1031` 移到 `y≈764`，再移到 `y≈496`，可觀察到列表位移。
- B 的 `2024/05/20～05/24` 出現在 `y≈1227`，其下方 OCR 為 `53`。
- 以 fresh OCR 名稱框計算點擊點 `[147, 1241]`，不是卡片封面中心，也不是歷史座標。

點擊後詳情頁顯示：

- `2024/05/20～05/24`
- `53張照片`
- `2024.05.25`

沒有 `(1/53)` viewer 標題；因此本次是 `ALBUM_DETAIL_GRID`。

## 2. 選單與正確點擊

詳情頁右上 `⋯` 的 app-window 座標約為 `[608,96]`。用該點開啟選單後，full-screen screenshot 的 OCR 實見五個選項：

```text
選擇項目       [1294, 310, 107, 31]
修改相簿名稱   [1294, 363, 160, 31]
儲存全部       [1297, 417, 107, 30]
刪除相簿       [1297, 470, 107, 30]
分享相簿       [1294, 523, 110, 31]
```

第一次以錯算的 app-local 點 `[356,216]` 點選時，選單只被關閉；實測結果是：

- 沒有 chooser；
- 目標資料夾 0 檔；
- `~/Downloads` 沒有新的 B 檔案；
- 因此判定 **未派送 Save All**，不是 UNKNOWN dispatch。

重新開啟選單後，依 full-screen menu 與 app-window origin 的對應，使用 `[626,243]` 精確點中 `儲存全部`，立即出現 chooser。這是本輪唯一一次 Save All 派送。

## 3. Chooser 與目的地

chooser 預設為 `Downloads`。使用 `super+shift+g` 開啟 Go to Folder，將路徑欄位精確設為預先建立的空資料夾：

```text
backups/<REDACTED_GROUP>/2024-05-20_2024-05-24_53張
```

AX 在確認前顯示：

- `PathTextField` value 精確等於目的地；
- `where popup` value 為 `2024-05-20_2024-05-24_53張`；
- `打開` 為 `OKButton`。

以 AX element index `53` 點擊一次 `打開`。此舉避免再次用全螢幕座標猜按鈕。

## 4. 下載與內容驗證

下載完成後：

| 檢查 | 結果 |
|---|---|
| 檔案數 | 53 / 53 |
| 預期張數 | 53 |
| 檔名索引 | 1..53，無重複 |
| 全部 JPEG | PASS |
| 總 bytes | 17,095,114 |
| SHA-256 清單 | 53 筆，[`b53-sha256.txt`](./public/manual-diagnostic-20261020-b53/b53-sha256.txt) |
| 完整解碼 | `ffmpeg` 解碼 53 檔，0 errors |
| 計數穩定取樣 | 2 次，檔名／bytes／hash 一致 |

結構化摘要：[`b53-verification.json`](./public/manual-diagnostic-20261020-b53/b53-verification.json)  
證據 manifest：[`03-evidence-manifest.json`](./public/manual-diagnostic-20261020-b53/03-evidence-manifest.json)

## 5. 公開證據

| 檔案 | 用途 | SHA-256 |
|---|---|---|
| [`00-detail-header-crop.png`](./public/manual-diagnostic-20261020-b53/00-detail-header-crop.png) | B 名稱、53 張、日期 | `2a4c0cf3fdede1d58a89f446914e22d401f76d057715a656d9bea9ccea1d99bd` |
| [`01-menu-crop.png`](./public/manual-diagnostic-20261020-b53/01-menu-crop.png) | 唯一 `儲存全部` 選單 | `290da77c3f3cc2fd334ecff99b82395c8ec19f864890945b03fc0ad2f682cec6` |
| [`02-chooser-crop.png`](./public/manual-diagnostic-20261020-b53/02-chooser-crop.png) | chooser 目的地與 `打開` | `4b8332d8aa0990bafc85fa4724454483cfbed3c7fe5fffa21c19c930c3881bfd` |

私有全幅截圖與下載照片保留在本機 `private/manual-diagnostic-20261020-b53/` 與 `backups/<REDACTED_GROUP>/...`，未上傳。

## 6. 根因補充：選單 overlay 不在 app window 截圖內

本輪再次確認：`app.getScreenshot()` 只包含 app window content，沒有包含從視窗邊界延伸出去的 menu popover。因此：

- 選單文字只能在 full-screen capture 中 OCR；
- 不能把 full-screen menu 座標直接當成 app-local 座標；
- 必須先用同一個 title/元素求 window origin，再換算 local point；
- 若能用 AX 定位按鈕，應優先以 element index 操作，例如 chooser 的 `OKButton`。

這個差異正是第一次點 `[356,216]` 只關閉選單、第二次 `[626,243]` 才真正選取 `儲存全部` 的原因。

## 7. 狀態表

| 項目 | 狀態 | 證據等級 |
|---|---|---|
| B fresh scroll 與名稱 grounding | PASS | 真實 GUI screenshot／OCR |
| B 名稱 → grid detail | PASS | `53張照片`、無 `(1/N)` |
| B 右上 `⋯` → 唯一 `儲存全部` | PASS | full-screen screenshot／OCR |
| B Save All 派送 | PASS，1 次 | 真實 GUI；非正式 gate |
| B chooser → 空目的地 | PASS，1 次確認 | AX path popup＋`OKButton` |
| B 下載 | PASS，53 檔 | 實際檔案系統 |
| B 內容驗證 | PASS | SHA-256＋完整解碼 |
| B formal state `VERIFIED` | NOT_RUN | 未寫入 state／ledger |
| 兩本手動診斷流程 | PASS | A56 + B53 |
| 正式產品 TWO_ALBUM_AUTO | BLOCKED/NOT_RUN | authorizer/source-runtime review 未完成 |

## 8. 副作用

- Save All 派送：1
- chooser 確認：1
- 下載：53 檔
- LINE 訊息送出：0
- formal intent／ledger／checkpoint／backup state mutation：0
- 65 張已人工備份相簿：未重開、未重下載

## 9. 下一步

1. 保留 `backups/<REDACTED_GROUP>/2024-05-20_2024-05-24_53張` 與 B53 證據。
2. 更新 PR #21／Issue #22，明確標記 A56、B53 manual diagnostic PASS，但 formal state／Independent E2E NOT_RUN。
3. 由外部 Code Reviewer 檢查 source/runtime binding；修復後再由新的獨立 DeepSeek 1017 Session 執行正式 TWO_ALBUM_AUTO。
4. 正式 E2E 才可寫入 ledger／state 與宣告 `VERIFIED`；本報告不可代替。
