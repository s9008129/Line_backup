# 問題單：LINE 相簿卡片誤點封面縮圖，開啟單張檢視器而非相簿詳細頁

日期：2026-10-20（Asia/Taipei）  
狀態：根因已由真實 A/B 導覽證據確認；導覽層面的修正操作已重測 PASS；產品級回歸測試仍待補  
嚴重度：High（會讓後續 menu 校準與 Save All 建立在錯誤畫面上）  
影響範圍：LINE macOS 相簿列表 → 相簿詳細頁的可逆導覽；本輪未觸及 Save All、下載、chooser、intent、ledger 或 state  
證據等級：真實 macOS LINE GUI（app-bound CUA）＋截圖／AX／逐檔 SHA-256；不是合成測試，也不是正式 DeepSeek 1017 E2E

## 一句話

相簿卡片不是單一 hit target：**封面是 2×2 的單張縮圖，點縮圖會開 `(1/N)` 單張檢視器；只有點相簿名稱（metadata strip）才會開相簿 grid 詳細頁。** 本輪第一次用「卡片幾何中心」`[320,700]`，正好落在封面縮圖，因此開成 `(1/56)`；改用名稱文字上的 `[120,310]` 後，立即開到 `2024/05/27～05/31` 的相簿詳細頁。第二次 B 以同一規則點 `[120,1044]`，也開到 `2024/05/20～05/24`、`53張照片` 的詳細頁。

這不是「Computer Use 看不到相簿名稱」；**截圖看得到名稱，AX 不把它暴露成獨立文字節點**，所以正式程式用 OCR 取得名稱矩形，再點矩形中心。這次真正的問題是：**操作者繞過了產品的 grounded title target 與 post-click grid guard，直接對卡片中心送出 raw click。**

## 六狀態（不把導覽 PASS 冒充交易 PASS）

- `PRIMARY_OUTCOME_STATUS`: `NOT_ACHIEVED`（兩本不同 eligible 相簿的 Save All、逐檔驗證、state readback 尚未完成）
- `IMPLEMENTATION_STATUS`: `NOT_CHANGED`（本輪只新增問題單／報告／公開證據；沒有修改產品程式）
- `CORE_ACCEPTANCE_STATUS`: `NOT_RUN`（menu 校準、Save All、下載、檔案驗證、state 均未執行）
- `REQUIRED_VERIFICATION_STATUS`: `PARTIAL`（A/B 名稱點擊與 grid 導覽已真實驗證；其餘 NOT_RUN）
- `INDEPENDENT_ACCEPTANCE_STATUS`: `NOT_RUN`
- `TASK_CLOSURE_STATUS`: `OPEN`

## 1. 目標與判定

本輪目標不是 Save All，而是先取得一個乾淨、可重現的導覽事實：

1. 從目前前景的 LINE 相簿列表，選定一本 eligible 相簿 A。
2. 點擊 A 的**相簿名稱**，確認開啟的是相簿 grid 詳細頁，而不是 `(1/N)` 單張檢視器。
3. 返回列表，實際捲動或確認列表位置改變。
4. 選定不同的 eligible 相簿 B，重複同一判定。
5. 全程不開 menu、不按 Save All、不開 folder chooser、不寫 intent／ledger／state。

判定標準：

- 相簿詳細頁必須同時具備：日期標題、照片張數、可捲動的 grid、右上 `⋯`，且不是 `(1/N)` 檢視器。
- 單張檢視器的判別特徵：視窗標題含 `(1/56)`、`(1/53)` 這類序號，中央是單張大圖，底部是橫向縮圖列。
- 相簿 grid 的判別特徵：標題只有 `2024/05/27～05/31`（A）或 `2024/05/20～05/24`（B），B 另外顯示 `53張照片` 與 `2024.05.25`。

## 2. 實際發生什麼

### 2.1 第一輪：FAIL（誤點封面）

第一輪操作者直接對相簿卡片的幾何中心送出 raw CUA click。A 的點位是 `[320,700]`（654×1286 CUA frame）。結果：

- A 開啟的是 **單張檢視器**，視窗標題 `2024/05/27～05/31(1/56)`。
- B 以同一個「卡片中心」啟發式開啟，結果是 **單張檢視器**，視窗標題 `2024/05/20～05/24(1/53)`。
- 兩張 viewer 截圖都有中央大圖、左右箭頭、底部縮圖列；這不是相簿 grid。

第一輪證據（私有原圖保留本機；公開檔只放去識別化裁切）：

| 事實 | 私有證據（repo-relative） | SHA-256 |
|---|---|---|
| A viewer `(1/56)` | `harness-development/line-two-album-pilot-20261014/private/test-first-20261020-01/evidence-session/05-open-album-a-and-verify-its-detail-page.jpg` | `f0489cb06e060b3feb23cfa5c66ef1ba4866da4804985c47cf139a9b2dd8885a` |
| B viewer `(1/53)` | `harness-development/line-two-album-pilot-20261014/private/test-first-20261020-01/evidence-session/12-wait-for-album-b-detail-to-load.jpg` | `75020535d74db521e3cfdb84ff27eb3959d7ac5550bd4e2b632a2612f37f10d9` |
| A viewer AX | `.../evidence-session/05-open-album-a-and-verify-its-detail-page.ax.txt` | `e3ff2283bfa7c8815cd4afd0ad9c123c9b75c2844272adfbf53074e6d715cf81` |
| B viewer AX | `.../evidence-session/12-wait-for-album-b-detail-to-load.ax.txt` | `9be6c45f214a681e83098b5babe687259955f1cb1b042582464a33fe28c8091b` |

公開去識別化證據（只有視窗標題列，沒有人名、群組名或照片）：

- [A viewer 標題裁切](./public/test-first-20261020-title-click-02/07-viewer-a-title-crop.png)
- [B viewer 標題裁切](./public/test-first-20261020-title-click-02/08-viewer-b-title-crop.png)

### 2.2 第二輪：PASS（改點相簿名稱）

第二輪在同一個前景、同一個 LINE app、同一組相簿上，改成點名稱文字：

1. 點 A 名稱 `[120,310]`，開啟相簿詳細頁，標題 `2024/05/27～05/31`，不是 `(1/56)`。
2. 按 `Escape` 返回列表；列表位置與內容保持可見。
3. 點 B 名稱 `[120,1044]`，開啟相簿詳細頁，顯示 `2024/05/20～05/24`、`53張照片`、`2024.05.25`。
4. 再按 `Escape` 返回列表。

第二輪證據：

| 事實 | 私有證據（repo-relative） | SHA-256 |
|---|---|---|
| 點名稱前列表 | `.../evidence-title-click-20261020-02/pre-title-click.jpg` | `1fd4c171eeaa586b2fc77fcd4e066b4a7b1bb5b18d74989ae150dae04ce240c7` |
| A 詳細頁 | `.../evidence-title-click-20261020-02/post-title-click.jpg` | `f732bb30b2db5fbf12536ea0c7a25a9fef827e0098ceadde74bc5b01e5fee2cf` |
| 返回列表 | `.../evidence-title-click-20261020-02/returned-to-list.jpg` | `828dd2df633598c40a3c544718c53269e61a092046a7a1cb7d50a0fd3dea9ce6` |
| B 詳細頁 | `.../evidence-title-click-20261020-02/post-b-title-click.jpg` | `552f92657ee7dbe020f63654a2e91b9be5d5677ef986768d67506fd554f9156d` |
| 再返回列表 | `.../evidence-title-click-20261020-02/final-returned-list.jpg` | `c46c4056812970a8b5c662eec7bf9a1415456685c931122dd2f4d578e6264e9d` |
| A 詳細頁 AX | `.../evidence-title-click-20261020-02/post-title-click.ax.txt` | `e17385e3559f2c2c56f513306ad6bab6b5b7a8f8480d4a2dc98057f7bcc43aaa` |
| B 詳細頁 AX | `.../evidence-title-click-20261020-02/post-b-title-click.ax.txt` | `e17385e3559f2c2c56f513306ad6bab6b5b7a8f8480d4a2dc98057f7bcc43aaa` |
| 前後 AX 合併 | `.../evidence-title-click-20261020-02/pre-and-post-title-click.ax.txt` | `dd5f742837df5ab86fd3339b9dc0a1e7acbbcefd5cd6e49686e7de53c10c001e` |

公開去識別化證據：

- [A 名稱／張數裁切](./public/test-first-20261020-title-click-02/03-album-a-metadata-crop.png)
- [B 名稱／張數裁切](./public/test-first-20261020-title-click-02/04-album-b-metadata-crop.png)
- [A 詳細頁標題列](./public/test-first-20261020-title-click-02/05-album-a-detail-header-crop.png)
- [B 詳細頁標題／張數／日期](./public/test-first-20261020-title-click-02/06-album-b-detail-header-crop.png)
- [座標與 hit-target 示意圖（合成，不是截圖）](./public/test-first-20261020-title-click-02/01-card-hit-target-schematic.svg)

完整公開 manifest：[`public/test-first-20261020-title-click-02/02-evidence-manifest.json`](./public/test-first-20261020-title-click-02/02-evidence-manifest.json)。

## 3. 第一性原理分析

### 3.1 相簿卡片不是單一 hit target

LINE 的相簿卡片由至少三個語意不同的區域組成：

1. **封面 collage**：2×2 的單張照片縮圖。每一格是「照片」，不是「相簿」。點一格 → 單張檢視器 `(1/N)`。
2. **名稱／metadata strip**：日期區間、張數、右側 `⋯`。點名稱文字 → 相簿 grid 詳細頁；點 `⋯` → 卡片層級 menu（不是 Save All menu）。
3. **卡片空白／邊界**：命中語意取決於 LINE 的實作，不能拿來當穩定目標。

因此「卡片中心」不是「相簿」的同義詞。卡片中心通常是封面，母體是照片；點它當然開照片。

### 3.2 為什麼 `[320,700]` 會開 viewer

第一輪的 654×1286 frame 中，A（56 張）卡片封面大約佔 `y≈630–940`，`[320,700]` 落在封面左上或右上的縮圖格內。LINE 對縮圖格的語意是「打開這張照片」，所以結果是 `(1/56)` viewer。這是**正確的 UI 行為**，不是 LINE 故障。

### 3.3 為什麼 `[120,310]` 與 `[120,1044]` 會開 grid

第二輪 frame 中：

- A 名稱文字大約 `y≈295–325`，`[120,310]` 在名稱文字的左段。
- B 名稱文字大約 `y≈1030–1055`，`[120,1044]` 在名稱文字內。

名稱文字位於 metadata strip，不屬於任何單張縮圖，所以 LINE 的語意是「打開這本相簿」→ grid 詳細頁。公開裁切圖 `03`／`04` 可以直接看到名稱與張數；`05`／`06` 可以看到 grid 詳細頁的標題、張數與日期。

### 3.4 為什麼「程式看起來有 guard」卻沒擋住

在 pilot 實作分支 `implement/line-two-album-pilot-v1-20261014`（PR #10，HEAD `516932dfcee94b662082b909b7980fc2483ab9c0`）中，正式路徑已經是名稱導向：

- `src/line_backup_batch/observations.py:707` `card_target(...)`
- `:720–722` 要求 classifier 的 `title_ocr.bounds`，否則 `CARD_NAME_TARGET_UNPROVEN`
- `:724–726` 以 `name_target_point(...)` 回傳名稱矩形中心
- `:730–740` `name_target_point(...)` 只接受 OCR 名稱矩形，並檢查不與 button 重疊
- `scripts/line_backup_cua_adapter.mjs:416` `openAlbum(prepared)`
- `:425` 才送出 `app.click(prepared.click)`
- `:436–448` 要求 `after.surface==='ALBUM_DETAIL'`、frame／session／group／pid／window lineage 正確，且 `detail_identity.kind==='ALBUM_DETAIL_GRID'`

也就是說，**產品路徑本來就會點名稱，而且會在點擊後檢查 grid identity。** 這次的問題是操作者沒有走這條路：

- 直接呼叫 `app.click([320,700])`，
- 沒有先呼叫 `card_target` 取得 grounded title point，
- 沒有呼叫 `openAlbum` 的 reserve／consume／post-click guard，
- 因此 `(1/56)` viewer 不會被 `ALBUM_OPEN_NOT_VERIFIED` 或 `PROJECT_DETAIL_IDENTITY_MISMATCH` 擋下。

這是**入口繞過（entrypoint bypass）**，不是 title target 不存在。

補充：目前 integration base `v43-ab/codex-rev28` 的 committed HEAD `b7bb666` 還沒有 `name_target_point`；上述 guard 在 pilot 分支與目前 worktree 的未提交變更中。這一點必須在 review 時講清楚，不能把未提交的 worktree 說成已部署的正式防護。

### 3.5 為什麼測試沒抓到

這是本問題單最重要的測試缺口。pilot 分支的 adapter fixture 在 `tests/test_cua_adapter.mjs:303–310`：

```js
function fixture(options={}) {
  ...
  async click(p){calls.push(['click',p]);clicks++;
    if(clicks===1)surface='ALBUM_DETAIL';
    else if(clicks===2)surface='FOLDER_CHOOSER';
    else downloadStarted=true;}
```

**第一次點擊無條件把 surface 設成 `ALBUM_DETAIL`，完全不管 `p` 落在封面、名稱或空白。** 因此：

- 即使 `prepared.click` 是封面中心 `[320,700]`，fixture 仍回報 `ALBUM_DETAIL`，測試會 PASS。
- fixture 沒有 `PHOTO_VIEWER` surface，也沒有 `(1/N)` 的 detail identity。
- `openAlbum` 測試（`:742–753`、`:755–764`）只驗證 lineage／identity mismatch，沒有驗證「點封面必須被拒絕」。
- `tests/test_batch_observations.py:18–21` 的 `test_same_frame_full_card_safe_metadata` 使用 `fixture_support.Fixture`，其 root 位於 `.../fixtures/` 下；`card_target` 的 `if not (... and '/fixtures/' in reader.root)` 會走 bypass，回傳 `safe_metadata_bounds` 中心 `[40,36]`，**沒有走到 OCR 名稱分支**。
- 純函式 `test_name_target_uses_exact_ocr_text_center...`（`:22–30`）只測 `name_target_point` 幾何，不測 `card_target` 的 OCR grounding 與 post-click surface。

結論：現有測試能證明「名稱中心計算正確」，但不能證明「實際點擊點是名稱」或「點到封面會被拒絕」。這正好對應本次真實 FAIL。

## 4. 歷史對照

這不是新發明的要求。歷史證據 `evidence/20260916-route/attempt-09/album-card-locate.json:103` 已明確記錄：

```json
"click_point_derivation": "title left edge + 12 px, title vertical centre"
```

同一個 JSON 也記錄了 title OCR、count OCR、safe margins 與 `UNSAFE_MARGINS` 的判定。也就是說，**「點名稱左緣內縮、垂直中心」是專案早已驗證過的方法**；本輪第一輪的卡片中心啟發式是退化，不是新發現。

## 5. 根因判定

### 5.1 直接原因

操作者對相簿卡片封面縮圖送出 raw click，LINE 依語意開啟單張檢視器 `(1/56)`。

### 5.2 系統原因

操作者繞過了 `card_target → name_target_point → openAlbum` 的 grounded 名稱路徑與 post-click grid guard。

### 5.3 測試原因

adapter fixture 將第一次點擊無條件映射成 `ALBUM_DETAIL`；沒有 photo viewer fixture；Python `card_target` 測試走 `/fixtures/` bypass，沒有覆蓋 OCR 名稱分支。

### 5.4 5 Whys

1. 為什麼開到單張？因為點到封面縮圖。
2. 為什麼點到封面？因為用「卡片幾何中心」而不是名稱文字。
3. 為什麼用中心？因為操作者直接送 raw CUA click，沒有先取 grounded title bounds。
4. 為什麼會繞過？因為本次是手動導覽，沒有呼叫產品的 `openAlbum`／`card_target`。
5. 為什麼測試沒阻止？因為 fixture 的第一次點擊無條件變成 `ALBUM_DETAIL`，且沒有 `(1/N)` viewer 的負面案例。

## 6. 最小修正建議

### P0：操作程序（立即）

- 任何相簿開啟都必須走 `card_target` → `name_target_point` → `openAlbum`；禁止對卡片幾何中心送 raw click。
- 若因診斷必須手動點擊，點擊前必須先取得名稱 OCR 矩形，點擊點必須落在矩形內，且與 `⋯`／button 不重疊。
- 點擊後必須以 `ALBUM_DETAIL_GRID`、日期、張數、window lineage 驗證；看到 `(1/N)` 一律視為 FAIL，不得繼續 menu 或 Save All。

### P1：adapter 回歸測試（最高優先）

把 fixture 的 `click(p)` 改成依點位決定 surface：

- `p` 落在 thumbnail cell → `PHOTO_VIEWER`（或 `PHOTO_VIEWER_1_OF_N`）。
- `p` 落在 title bounds → `ALBUM_DETAIL`，並帶 `ALBUM_DETAIL_GRID` identity。
- 其他 → `ALBUMS` 或不變。

新增至少三個測試：

1. `openAlbum` 收到封面點位 → 必須拒絕（建議代碼 `ALBUM_OPEN_PHOTO_VIEWER` 或沿用 `ALBUM_OPEN_NOT_VERIFIED`）。
2. `openAlbum` 收到名稱點位 → 必須接受 grid detail。
3. `openAlbum` 收到 `(1/N)` viewer 的 detail identity → 必須拒絕，且不得消耗 menu calibration 配額。

### P2：Python `card_target` 測試

- 新增一個不位於 `/fixtures/` bypass 的 synthetic reader，讓 `card_target` 真正走 `title_ocr.bounds`。
- 斷言回傳點等於名稱矩形中心，而不是 `safe_metadata_bounds` 中心。
- 斷言名稱矩形與 button 重疊時回傳 `CARD_NAME_TARGET_CONTROL_OVERLAP`。

### P3：證據可追溯性

- 在 `ALBUM_OPEN_INVOCATION` 記錄 `click`、`title_ocr.bounds`、`grounding_frame_id`、`grounding_sha256`。
- 在 post-click 失敗時記錄 observed surface、viewer title（如有）、window lineage，讓 `(1/N)` 可以直接從 receipt 判定。

## 7. 驗收條件

修正後至少要有：

1. 新負面測試：封面點位 → viewer → `openAlbum` 拒絕；在修正前應 FAIL，修正後 PASS。
2. 新正面測試：名稱點位 → grid detail → `openAlbum` 接受。
3. 真實 LINE 導覽：點名稱開 grid，不是 `(1/N)`；A/B 各一次。
4. 全程 0 次 Save All、0 次下載、0 次 chooser、0 次 intent／ledger／state mutation。
5. 正式 E2E 仍須由獨立 DeepSeek `deepseek-v4.1-flash:1017` Session 重驗；本問題單不代替該關卡。

## 8. 未知與限制

- 第一輪 `[320,700]` 的精確 tool-call 參數來自互動 session 記錄；持久化的 viewer 截圖是更強的結果證據。若需要逐位元重建，應查該 session 的原始 tool log。
- 本輪沒有重新驗證右上 `⋯` menu。歷史證據曾驗證 detail menu 與「儲存全部」；本次只確認 grid 詳細頁與 `⋯` 可見，menu 內容為 `NOT_RUN`。
- AX 在相簿列表只暴露 generic rows，沒有把相簿名稱暴露成獨立文字節點；因此名稱定位必須依賴 screenshot＋OCR，不能只看 AX。
- 本輪不是正式 DeepSeek 1017 E2E；沒有獨立 E2E Session 的模型／receipt。
- B 的 `[120,1044]` 已由公開裁切 `04` 證明落在名稱文字內；但仍建議未來以 OCR bounds 中心（而非手選 x）作為正式點位。

## 9. 本輪明確沒有做的事

- 沒有按 Save All。
- 沒有開 folder chooser、沒有建立下載目的地。
- 沒有寫入 intent、ledger、checkpoint 或 backup state。
- 沒有重送任何結果不明的交易。
- 沒有修改產品程式、測試標準、grant 或歷史資料。
- 沒有把本輪導覽宣稱為正式 T1／T2 或完整 E2E PASS。

## 10. 給高階診斷模型的問題

請獨立判斷：

1. 上述「封面縮圖 vs 名稱 metadata strip」的 hit-target 分析是否完整？有沒有遺漏的 LINE 互動語意？
2. P1 的 fixture 設計是否足以捕捉本次 FAIL？是否需要直接把 `prepared.click` 與 `title_ocr.bounds` 的包含關係做成 assertion，而不是只改 surface？
3. `openAlbum` 的 post-click guard 是否應新增獨立的 `ALBUM_OPEN_PHOTO_VIEWER` 錯誤碼，讓 `(1/N)` 與一般 identity mismatch 可區分？
4. 在目前 integration base 尚未包含 `name_target_point` 的情況下，最小、可審查的 backport 路徑是什麼？
5. 是否同意本輪不把導覽 PASS 升格為正式 E2E，並要求新的獨立 DeepSeek Session 重驗？

## 11. 證據索引

私有原始證據根目錄：

`harness-development/line-two-album-pilot-20261014/private/test-first-20261020-01/`

- 第一輪：`evidence-session/`
- 第二輪：`evidence-title-click-20261020-02/`

公開去識別化證據：

`harness-development/line-two-album-pilot-20261014/public/test-first-20261020-title-click-02/`

- `01-card-hit-target-schematic.svg`（合成示意圖）
- `02-evidence-manifest.json`（私有原圖 hash、公開裁切 hash、隱私說明）
- `03-album-a-metadata-crop.png`（A 名稱／張數）
- `04-album-b-metadata-crop.png`（B 名稱／張數）
- `05-album-a-detail-header-crop.png`（A grid 詳細頁標題）
- `06-album-b-detail-header-crop.png`（B grid 詳細頁標題／張數／日期）
- `07-viewer-a-title-crop.png`（A viewer `(1/56)` 標題）
- `08-viewer-b-title-crop.png`（B viewer `(1/53)` 標題）

隱私處理：公開檔只保留日期、張數、視窗控制項與 synthetic 示意；不包含群組名稱、人名、照片內容、檔案清單、授權資料或本機絕對路徑。私有原圖保留在本機，未上傳。

---

## 2026-10-20 後續真實驗證（A 相簿 Save All）

本問題單先前把 menu／Save All 標為 NOT_RUN；後續已在 Owner 授權的人工診斷中補上 A 相簿實測，更新如下：

- A `2024/05/27～05/31`、56 張的名稱欄點擊成功開啟 grid detail，沒有出現 `(1/N)`。
- 右上 `⋯` 實見 `選擇項目`、`修改相簿名稱`、`儲存全部`、`刪除相簿`、`分享相簿`；`儲存全部` 唯一，僅派送 1 次。
- chooser 經 Go to Folder 進入預先建立的空資料夾，按 `打開` 1 次。
- 下載 56/56 檔、18,117,492 bytes；檔名索引 1..56、全部 JPEG、完整解碼 0 errors。
- 這是 `MANUAL_DIAGNOSTIC`，不是正式產品入口與 formal `VERIFIED` state；B 仍 NOT_RUN。

完整證據與新發現的 CUA 視窗綁定／413 根因：

- [`MANUAL_DIAGNOSTIC_20261020_A56.md`](./MANUAL_DIAGNOSTIC_20261020_A56.md)
- [`ISSUE-20261020-cua-window-binding-and-provider-413.md`](./ISSUE-20261020-cua-window-binding-and-provider-413.md)
