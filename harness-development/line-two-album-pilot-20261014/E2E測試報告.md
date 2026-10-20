# LINE 相簿導覽 E2E 測試報告：封面誤點與名稱點擊修正

日期：2026-10-20（Asia/Taipei）  
測試時段：第一輪約 19:23；第二輪約 19:29–19:34  
測試類型：真實 macOS LINE GUI（app-bound Computer Use）可逆導覽；不是正式交易 E2E  
受測目標：從已登入的 LINE 相簿列表，以名稱點擊開啟兩本不同 eligible 相簿的 grid 詳細頁  
本輪結論：**第一輪 FAIL（點封面開 `(1/N)` viewer）；第二輪導覽 PASS（點名稱開 grid）；Save All 與下載全部 NOT_RUN**

> **2026-10-20 後續更新：** 本報告保留當時的導覽診斷。後續已在同一真實 LINE 環境完成 A 相簿 56 檔與 B 相簿 53 檔的 manual Save All、下載與內容驗證；正式產品 state `VERIFIED` 與 Independent E2E 仍 NOT_RUN。A 證據見 [`MANUAL_DIAGNOSTIC_20261020_A56.md`](./MANUAL_DIAGNOSTIC_20261020_A56.md)，B 證據見 [`MANUAL_DIAGNOSTIC_20261020_B53.md`](./MANUAL_DIAGNOSTIC_20261020_B53.md)，CUA 多視窗與 413 根因見 [`ISSUE-20261020-cua-window-binding-and-provider-413.md`](./ISSUE-20261020-cua-window-binding-and-provider-413.md)。

> **LATEST STATUS（2026-10-20 21:xx）：** A56 56/56、B53 53/53 的實體檔案已重新逐檔 SHA-256 核對，兩本皆 **PASS**（18,117,492 + 17,095,114 bytes；正式 state 仍 revision 35，未寫入）。正式 `runTwoAlbumPilot()` 目前 **BLOCKED**：唯一 authority 是「單相簿 ONE56、`no_second_album=true`、quota 1、`PENDING_EXTERNAL_REVIEW`」，且其 target 正是已完成 manual 下載的 A56；同時 state 沒有 manual provenance，A56/B53 在正式去重邏輯中仍屬 eligible。現有產品沒有合法 import／adopt manual 檔案的路徑。詳見 [`FORMAL_ADMISSION_AUDIT_20261020.md`](./FORMAL_ADMISSION_AUDIT_20261020.md)。本輪 GUI 輸入 0、Save All 0。


## 0. 重要邊界

本報告只證明「可逆導覽」層面的事實：

- 相簿名稱點擊可以開啟相簿 grid 詳細頁。
- 卡片封面中心點擊會開啟單張檢視器。
- A/B 兩本不同相簿的詳細頁標題、張數與日期可被截圖辨識。

本報告**不**證明：

- 右上 `⋯` menu 在本次 LINE 版本仍可開啟。
- 「儲存全部」仍存在或可派送。
- 任何 Save All、folder chooser、下載、逐檔 SHA-256、ImageIO 解碼、state readback。
- 正式 T1／T2 或完整兩本備份 E2E。

本輪沒有啟動新的獨立 DeepSeek `deepseek-v4.1-flash:1017` Codex CLI Session；因此不能把本報告當成正式 Independent E2E。執行者是目前的 Codex root session，操作方式是直接 CUA，而不是產品 `two_album_entry` 入口。

## 1. 環境與前置狀態

| 項目 | 值 |
|---|---|
| OS | macOS（LINE macOS app） |
| LINE 狀態 | 已登入；相簿列表在前景；Owner 已口頭交還前景 |
| 操作通道 | Computer Use app-bound `getAXStateAndScreenshot`／`click`／`pressKey` |
| CUA frame 尺寸 | 654×1286（第二輪）；第一輪 viewer 為 1280×960 |
| 群組 | 已識別的真實群組；本公開報告以 Group G 表示，不揭露名稱 |
| 相簿 A | `2024/05/27～05/31`，56 張 |
| 相簿 B | `2024/05/20～05/24`，53 張；建立日 `2024.05.25` |
| 產品入口 | 未使用；本輪為手動 CUA 導覽 |
| Save All 授權 | 本輪未使用、未派送 |
| State revision | 未讀取、未變更 |

### 1.1 為什麼不用產品入口

本輪目的是先取得乾淨的 hit-target 事實，而不是跑交易。產品入口 `two_album_entry` 需要 grant、ledger、menu calibration 與 Save All 前置條件；在尚未確認「點名稱會開 grid」之前就進入產品入口，會把錯誤座標帶進不可逆交易。因此本輪刻意只做可逆導覽，並且在每次點擊後立即以截圖判定 surface。

這個選擇也暴露了本次根因：**手動導覽繞過了產品的 `card_target`／`openAlbum` guard。** 正式執行時不應再這樣做；應走產品入口，或至少复用其 grounded title target 與 post-click identity check。

## 2. 測試案例與結果

| ID | 操作 | 預期 | 實際 | 判定 |
|---|---|---|---|---|
| N1 | 第一輪：點 A 卡片幾何中心 `[320,700]` | 相簿 grid 詳細頁 | 單張檢視器 `2024/05/27～05/31(1/56)` | **FAIL** |
| N2 | 第一輪：點 B 卡片幾何中心（同一啟發式） | 相簿 grid 詳細頁 | 單張檢視器 `2024/05/20～05/24(1/53)` | **FAIL** |
| N3 | 第二輪：點 A 名稱 `[120,310]` | 相簿 grid 詳細頁 | 標題 `2024/05/27～05/31`，grid 可見，無 `(1/N)` | **PASS** |
| N4 | 第二輪：`Escape` 返回列表 | 回到相簿列表 | 列表可見，位置保持 | **PASS** |
| N5 | 第二輪：點 B 名稱 `[120,1044]` | 相簿 grid 詳細頁 | `2024/05/20～05/24`、`53張照片`、`2024.05.25` | **PASS** |
| N6 | 第二輪：`Escape` 返回列表 | 回到相簿列表 | 列表可見 | **PASS** |
| M1 | 右上 `⋯` menu | 開啟 detail menu | 未執行 | **NOT_RUN** |
| S1 | Save All | 不執行 | 未執行 | **NOT_RUN** |
| D1 | 下載／chooser | 不執行 | 未執行 | **NOT_RUN** |
| V1 | 逐檔驗證／state readback | 不執行 | 未執行 | **NOT_RUN** |

## 3. 第一輪：FAIL 的逐步事實

### 3.1 A：`[320,700]` → `(1/56)`

操作：

1. 在相簿列表中選定 A（`2024/05/27～05/31`，56 張）。
2. 以卡片幾何中心 `[320,700]` 送出 raw CUA click。
3. 等待畫面更新並截圖。

預期：相簿 grid 詳細頁，標題只有 `2024/05/27～05/31`，有張數與 grid。

實際：視窗標題為 `2024/05/27～05/31(1/56)`；中央是單張大圖，左右有上一張／下一張箭頭，底部是橫向縮圖列。這是單張檢視器，不是相簿詳細頁。

證據：

- 私有原圖：`harness-development/line-two-album-pilot-20261014/private/test-first-20261020-01/evidence-session/05-open-album-a-and-verify-its-detail-page.jpg`
- SHA-256：`f0489cb06e060b3feb23cfa5c66ef1ba4866da4804985c47cf139a9b2dd8885a`
- 公開裁切：`public/test-first-20261020-title-click-02/07-viewer-a-title-crop.png`

### 3.2 B：同一啟發式 → `(1/53)`

操作：

1. 返回列表。
2. 以同一「卡片中心」啟發式選定 B（`2024/05/20～05/24`，53 張）。
3. 點擊並截圖。

預期：B 的相簿 grid 詳細頁。

實際：視窗標題 `2024/05/20～05/24(1/53)`；同樣是單張檢視器。

證據：

- 私有原圖：`.../evidence-session/12-wait-for-album-b-detail-to-load.jpg`
- SHA-256：`75020535d74db521e3cfdb84ff27eb3959d7ac5550bd4e2b632a2612f37f10d9`
- 公開裁切：`public/test-first-20261020-title-click-02/08-viewer-b-title-crop.png`

### 3.3 第一輪的判讀錯誤

第一輪把「有標題、有照片」誤讀成「相簿詳細頁」。實際上：

- `(1/56)`／`(1/53)` 是單張檢視器的頁序，不是相簿張數的標註。
- 單張檢視器的標題列包含 `(1/N)`；相簿 grid 的標題列只有日期區間。
- 單張檢視器底部是縮圖列；相簿 grid 是可捲動的 2 欄照片牆。

這個誤讀不是 LINE 的 UI 問題，而是 surface 判定沒有把 `(1/N)` 當成負面特徵。

## 4. 第二輪：PASS 的逐步事實

### 4.1 A：點名稱 `[120,310]`

前置畫面：列表已回到 A 的 metadata strip 附近；A 名稱文字位於 `y≈295–325`，`[120,310]` 落在名稱左段。

操作：fresh CUA screenshot → 確認 A 名稱位置 → click `[120,310]` → 等待 → screenshot。

實際：

- 視窗標題只有 `2024/05/27～05/31`，沒有 `(1/N)`。
- 內容是 2 欄照片 grid，可向下捲動。
- 右上 `⋯` 可見。

判定：**PASS（相簿 grid 詳細頁）**。

證據：

- 點擊前：`.../evidence-title-click-20261020-02/pre-title-click.jpg`，SHA-256 `1fd4c171eeaa586b2fc77fcd4e066b4a7b1bb5b18d74989ae150dae04ce240c7`
- 點擊後：`.../evidence-title-click-20261020-02/post-title-click.jpg`，SHA-256 `f732bb30b2db5fbf12536ea0c7a25a9fef827e0098ceadde74bc5b01e5fee2cf`
- 公開裁切：`03-album-a-metadata-crop.png`、`05-album-a-detail-header-crop.png`

### 4.2 返回列表

操作：按 `Escape`。

實際：回到相簿列表；A 與 B 的名稱／張數仍可見。沒有關閉 LINE，沒有切換群組。

證據：`returned-to-list.jpg`，SHA-256 `828dd2df633598c40a3c544718c53269e61a092046a7a1cb7d50a0fd3dea9ce6`。

### 4.3 B：點名稱 `[120,1044]`

前置畫面：B 名稱文字位於 `y≈1030–1055`；`[120,1044]` 落在名稱文字內。公開裁切 `04-album-b-metadata-crop.png` 可直接核對名稱與 `53`。

操作：fresh screenshot → 確認 B 名稱位置 → click `[120,1044]` → 等待 → screenshot。

實際：

- 視窗標題 `2024/05/20～05/24`，沒有 `(1/N)`。
- 顯示 `53張照片` 與 `2024.05.25`。
- 內容是 2 欄照片 grid，右上 `⋯` 可見。

判定：**PASS（相簿 grid 詳細頁）**。

證據：

- 點擊後：`.../evidence-title-click-20261020-02/post-b-title-click.jpg`，SHA-256 `552f92657ee7dbe020f63654a2e91b9be5d5677ef986768d67506fd554f9156d`
- 公開裁切：`04-album-b-metadata-crop.png`、`06-album-b-detail-header-crop.png`

### 4.4 再返回列表

操作：按 `Escape`。

實際：回到相簿列表；沒有 menu、沒有 chooser、沒有下載。

證據：`final-returned-list.jpg`，SHA-256 `c46c4056812970a8b5c662eec7bf9a1415456685c931122dd2f4d578e6264e9d`。

## 5. 點擊座標與 hit-target 判讀

第二輪 CUA frame 為 654×1286。以公開裁切與原圖交叉核對：

| 目標 | 觀察到的文字帶 | 點擊點 | 結果 |
|---|---|---|---|
| A 名稱 | `y≈295–325` | `[120,310]` | grid 詳細頁 |
| B 名稱 | `y≈1030–1055` | `[120,1044]` | grid 詳細頁 |
| A 封面（第一輪） | 卡片封面約 `y≈630–940` | `[320,700]` | `(1/56)` viewer |

這個對照直接支持第一性原理：**封面與名稱是不同的 hit target；卡片中心落在封面，名稱落在 metadata strip。**

公開示意圖：`public/test-first-20261020-title-click-02/01-card-hit-target-schematic.svg`（合成，不是截圖）。

## 6. AX 觀察

第二輪 A/B 詳細頁的 AX 輸出非常精簡：

```text
Window: "", App: LINE.
0 標準視窗 Secondary Actions: Raise
  1 關閉按鈕
  2 縮到最小按鈕
3 menu bar
  ...
The focused UI element is 0 標準視窗 Secondary Actions: Raise
```

也就是說：

- AX 沒有把相簿名稱、日期、張數或 grid 照片暴露成可用的文字節點。
- 不能用 AX 文字直接判定「這是 A 還是 B」。
- 本輪的 identity 判定主要來自 screenshot／OCR 與視覺標題；AX 只用來確認 app／視窗／焦點沒有漂移。

證據：

- A 詳細頁 AX：`.../post-title-click.ax.txt`，SHA-256 `e17385e3559f2c2c56f513306ad6bab6b5b7a8f8480d4a2dc98057f7bcc43aaa`
- B 詳細頁 AX：`.../post-b-title-click.ax.txt`，同上 SHA-256
- 前後 AX 合併：`.../pre-and-post-title-click.ax.txt`，SHA-256 `dd5f742837df5ab86fd3339b9dc0a1e7acbbcefd5cd6e49686e7de53c10c001e`

這是為什麼正式產品路徑需要 `title_ocr.bounds`，而不能只依賴 AX。也是為什麼「Computer Use 看得到名稱」是正確的：**截圖看得到，AX 看不到。**

## 7. 根因摘要

### 7.1 直接原因

第一輪對相簿封面縮圖送 click，LINE 依語意開啟單張檢視器。

### 7.2 程式路徑原因

操作者沒有走 `card_target` → `name_target_point` → `openAlbum`。正式路徑在 pilot 分支已存在：

- `src/line_backup_batch/observations.py:707` `card_target`
- `:720–726` 要求 `title_ocr.bounds` 並回傳名稱中心
- `scripts/line_backup_cua_adapter.mjs:416` `openAlbum`
- `:425` 送出 `prepared.click`
- `:436–448` 要求 `ALBUM_DETAIL`＋`ALBUM_DETAIL_GRID`＋lineage／fingerprint

本次 raw click 完全跳過這些 guard。

### 7.3 測試原因

- `tests/test_cua_adapter.mjs:310`：第一次 click 無條件 `surface='ALBUM_DETAIL'`，不看點位。
- 沒有 `PHOTO_VIEWER`／`(1/N)` fixture。
- `tests/test_batch_observations.py:18–21` 走 `/fixtures/` bypass，測的是 `safe_metadata_bounds` 中心，不是 OCR 名稱中心。

完整分析與修正建議見 [`ISSUE-20261020-album-title-vs-cover-hit-target.md`](./ISSUE-20261020-album-title-vs-cover-hit-target.md)。

## 8. 狀態矩陣

| 狀態 | 值 | 說明 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `NOT_ACHIEVED` | 兩本 Save All／下載／驗證未完成 |
| `IMPLEMENTATION_STATUS` | `NOT_CHANGED` | 本輪只新增文件與公開證據 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN` | menu、交易、檔案、state 未驗 |
| `REQUIRED_VERIFICATION_STATUS` | `PARTIAL` | 導覽 A/B PASS；其餘 NOT_RUN |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | 無獨立 DeepSeek E2E |
| `TASK_CLOSURE_STATUS` | `OPEN` | 待回歸測試與正式 E2E |

### 8.1 子項狀態

| 子項 | 狀態 |
|---|---|
| 相簿列表辨識 | `PASS`（A/B 名稱與張數可見） |
| 名稱點擊 A | `PASS` |
| 名稱點擊 B | `PASS` |
| grid 詳細頁辨識 | `PASS` |
| `(1/N)` viewer 負面判別 | `PASS`（第一輪已實際觀察） |
| 返回列表 | `PASS`（A/B 各一次） |
| 右上 `⋯` menu | `NOT_RUN` |
| Save All | `NOT_RUN` |
| Folder chooser | `NOT_RUN` |
| 下載 | `NOT_RUN` |
| 逐檔 SHA-256／ImageIO | `NOT_RUN` |
| State readback／release | `NOT_RUN` |

## 9. 副作用與保護

本輪副作用：

- Save All 派送：**0**
- Folder chooser：**0**
- 下載檔案：**0**
- Intent／ledger／checkpoint：**0**
- Backup state mutation：**0**
- 目的地建立：**0**
- LINE 訊息送出：**0**

本輪只做了：

- CUA screenshot／AX 讀取。
- 四次點擊（第一輪 A/B 封面；第二輪 A/B 名稱）。
- 三次 `Escape` 返回。
- 本機檔案寫入（截圖、AX、公開裁切、報告）。

## 10. 嘗試歷史與資訊增益

| 嘗試 | 操作 | 結果 | 新資訊 |
|---|---|---|---|
| 1 | 卡片中心 `[320,700]` | FAIL：`(1/56)` | 證明封面中心是照片 viewer，不是相簿 |
| 2 | 卡片中心啟發式（B） | FAIL：`(1/53)` | 證明不是單一相簿的偶然 |
| 3 | 名稱 `[120,310]`（A） | PASS：grid A | 證明名稱點擊可行 |
| 4 | 名稱 `[120,1044]`（B） | PASS：grid B | 證明同一規則可套用到第二本不同相簿 |

資訊增益：

- 第一輪告訴我們「失敗是座標語意錯誤」，不是 LINE 沒登入、不是視窗不見、不是 Computer Use 看不到。
- 第二輪告訴我們「名稱點擊是穩定可行的」，而且 A/B 都能開啟 grid。
- 兩輪合併後，root cause 可以從「操作失误」提升為「entrypoint bypass＋測試缺口」。

## 11. 未知與限制

1. 本輪沒有重驗 menu；歷史 menu 證據不能自動轉移到本次 LINE 狀態。
2. 本輪沒有使用產品 `openAlbum`，所以沒有 `ALBUM_OPEN_INVOCATION` receipt、reservation 或 `detail_identity` 的正式 JSON。
3. 本輪的 identity 判定來自 screenshot／OCR；沒有獨立的 OCR JSON sidecar 或 hash-bound classifier artifact。
4. 第一輪 `[320,700]` 的精確 tool-call 參數來自互動 session；持久化證據是 viewer 截圖。若需逐位元重建，應查原始 session log。
5. B 的名稱點擊 x 座標 `120` 是手選，不是 OCR bounds 中心；正式執行應由 `name_target_point` 計算。
6. 本輪沒有啟動 DeepSeek 1017；不得把本報告當成 Independent E2E PASS。

## 12. 下一步建議

### 立即（文件與 review）

1. 把本報告與問題單交給外部 Plan／Code Reviewer。
2. 請 reviewer 先確認 P1 的 fixture 設計，再決定是否 backport `name_target_point` 到 integration base。

### 修正（需另開實作切片）

1. 在 pilot 分支補 `PHOTO_VIEWER` fixture 與 negative test。
2. 在 `card_target` 測試中補非 `/fixtures/` bypass 的 OCR 名稱案例。
3. 讓 `openAlbum` 在 observed viewer 時回傳可區分的錯誤碼，例如 `ALBUM_OPEN_PHOTO_VIEWER`。
4. 在 invocation receipt 記錄 click、title bounds、grounding hash。

### 重測（修正後）

1. 先跑 adapter unit／integration tests；negative test 必須在修正前 FAIL、修正後 PASS。
2. 再跑真實 LINE 名稱導覽：A/B 各一次，確認 grid，不出現 `(1/N)`。
3. 確認 0 次 Save All／下載／state mutation。
4. 由 Owner 啟動新的獨立 DeepSeek `deepseek-v4.1-flash:1017` Session 做正式 E2E；本報告不代替。

## 13. 證據清單

### 13.1 私有原始證據（本機，未上傳）

根目錄：`harness-development/line-two-album-pilot-20261014/private/test-first-20261020-01/`

| 檔案 | Bytes | SHA-256 |
|---|---:|---|
| `evidence-session/05-open-album-a-and-verify-its-detail-page.jpg` | 277898 | `f0489cb06e060b3feb23cfa5c66ef1ba4866da4804985c47cf139a9b2dd8885a` |
| `evidence-session/12-wait-for-album-b-detail-to-load.jpg` | 166161 | `75020535d74db521e3cfdb84ff27eb3959d7ac5550bd4e2b632a2612f37f10d9` |
| `evidence-title-click-20261020-02/pre-title-click.jpg` | 173919 | `1fd4c171eeaa586b2fc77fcd4e066b4a7b1bb5b18d74989ae150dae04ce240c7` |
| `evidence-title-click-20261020-02/post-title-click.jpg` | 237242 | `f732bb30b2db5fbf12536ea0c7a25a9fef827e0098ceadde74bc5b01e5fee2cf` |
| `evidence-title-click-20261020-02/returned-to-list.jpg` | 175304 | `828dd2df633598c40a3c544718c53269e61a092046a7a1cb7d50a0fd3dea9ce6` |
| `evidence-title-click-20261020-02/post-b-title-click.jpg` | 189502 | `552f92657ee7dbe020f63654a2e91b9be5d5677ef986768d67506fd554f9156d` |
| `evidence-title-click-20261020-02/final-returned-list.jpg` | 174637 | `c46c4056812970a8b5c662eec7bf9a1415456685c931122dd2f4d578e6264e9d` |

完整清單與 AX hash 見 `public/test-first-20261020-title-click-02/02-evidence-manifest.json`。

### 13.2 公開去識別化證據（本 PR）

根目錄：`harness-development/line-two-album-pilot-20261014/public/test-first-20261020-title-click-02/`

| 檔案 | 用途 |
|---|---|
| `01-card-hit-target-schematic.svg` | 合成 hit-target 示意圖 |
| `02-evidence-manifest.json` | 私有原圖 hash、公開裁切 hash、隱私說明 |
| `03-album-a-metadata-crop.png` | A 名稱／張數 |
| `04-album-b-metadata-crop.png` | B 名稱／張數 |
| `05-album-a-detail-header-crop.png` | A grid 標題 |
| `06-album-b-detail-header-crop.png` | B grid 標題／張數／日期 |
| `07-viewer-a-title-crop.png` | A viewer `(1/56)` 標題 |
| `08-viewer-b-title-crop.png` | B viewer `(1/53)` 標題 |

隱私：公開檔不含群組名稱、人名、照片內容、檔案清單、授權資料或本機絕對路徑。私有原圖保留本機，未上傳。

## 14. 2026-10-20 覆蓋率對帳（唯讀）— `NO_ELIGIBLE_TARGET` 在目前群組

完整證據：`COVERAGE_AUDIT_20261020.md`。**未開 LINE、未寫 state、未 Save All。**

- 本群組 5 本相簿全部已有歸屬：182 + 57 = 239 正式 `VERIFIED`；56 + 53 = 109 manual；65 張為 Owner 排除（目錄檔案數 0）。
- 因此「再用另外兩本相簿」在**目前群組內不存在**，屬真實限制回報，不是程式缺陷。
- 另一發現：A56 `verification.json` 在 PR 分支（已遮蔽）為 `a67e8207…`、Owner 本機 canonical 為 `9381d72a…`，差異僅 `destination_workspace_relative`。Plan 已補 9.1 修正（registry hash 必須即時計算）。
- state 仍為 `revision 35`、SHA-256 `4550501…8ee6`，與前一輪完全一致。

```text
COVERAGE_AUDIT=PASS_READ_ONLY
A56_FILES=56  B53_FILES=53  VERIFIED_239=UNCHANGED  EXCLUDED_65_FILES=0
ELIGIBLE_ALBUMS_IN_CURRENT_GROUP=0
TWO_ALBUM_AUTO=NOT_RUN_NO_ELIGIBLE_TARGET
STATE_WRITES=0  GUI=0  SAVE_ALL=0
```
