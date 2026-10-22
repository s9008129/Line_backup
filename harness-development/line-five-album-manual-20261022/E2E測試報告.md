# LINE 五本相簿實機測試報告（MANUAL_DIAGNOSTIC）

- 報告 ID：`MANUAL-DIAGNOSTIC-FIVE-20261022-01`
- 日期：2026-10-22（Asia/Taipei）
- 測試類型：`MANUAL_DIAGNOSTIC`，不是 `TWO_ALBUM_AUTO`，也不是正式 `LINE_TWO_ALBUM_PILOT/1` 交易
- 執行者：本次 Codex CLI 實機操作 Session；執行模型識別未由本 Session 獨立記錄，記為 `UNKNOWN`
- 最終狀態：**A45 單本 PASS；B78、C77、D42、E87 NOT_RUN；Owner 主動暫停批次**

## 0. 摘要

本輪只完成五本候選中的第一本：

| 候選 | 相簿 | 張數 | 狀態 |
|---|---|---:|---|
| A45 | `2024/04/22～04/26` | 45 | **PASS**：一次 Save All、45/45 下載、索引 1–45、SHA-256 manifest、45/45 ImageIO 完整解碼 |
| B78 | `2024/04/21` | 78 | **NOT_RUN** |
| C77 | `2024/04/08～04/12` | 77 | **NOT_RUN** |
| D42 | `2024/04/01～04/03` | 42 | **NOT_RUN** |
| E87 | `2024/03/25～03/29` | 87 | **NOT_RUN** |

本輪沒有修改產品原始碼、Harness、正式 Authorizer、grant、ledger 或 state。A45 的下載只存在本機 private evidence 目錄，沒有加入正式 `VERIFIED` 狀態。

## 1. Owner 授權、環境與邊界

Owner 在本次操作前明確回覆：

> 授權本次五本各一次 Save All；LINE 已交給你操作。

本輪遵守的邊界：

- 使用真實 macOS LINE GUI、Computer Use、截圖、Vision OCR 與 AX 觀察。
- 未呼叫正式 AUTO Authorizer，未偽造 grant，未變更 state／ledger。
- 每本最多派送一次 Save All；A45 實際派送數為 1。
- 未碰觸歷史正式 VERIFIED 的 239 張、Manual Diagnostic 的 109 張，或 Owner 排除的 65 張相簿。
- LINE 的 AX 在相簿列表只提供 generic rows；相簿身分判定依賴 fresh screenshot＋OCR＋進入後的詳細頁交叉核對，不依賴 AX 文字。

測試期間有一次 foreground 變化：在 A45 的 folder chooser 按下「打開」後，後續全螢幕截圖觀察到 Terminal 位於前景。此後沒有再送出任何 LINE 點擊或 Save All；下載已在背景完成。依專案規則，下一個 LINE 操作階段必須重新取得 Owner 當次前景交接。

## 2. 重複下載與目標資格核對

操作前的 state／policy baseline SHA-256：

| 檔案 | SHA-256 |
|---|---|
| `state/backup_state.json` | `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6` |
| `state/manual_archives.json` | `efe572afc9da1ae2123b3016430370f9ecd84ffb259f3bf73b0e5d26cd667bc5` |
| `policies/line-two-album-pilot-v1.json` | `59d94b72f4fd59d829b56d21a494c9d83c6b91eb2513c15795a58021194a39e9` |

操作後重新計算，三份檔案 SHA-256 全部相同，表示本輪沒有改動正式 state／manual registry／pilot policy。

核對到的已完成或排除指紋：

- 正式 `VERIFIED`：`2024/05/06～05/10` 182 張、`2024/05/13～05/17` 57 張，合計 239 張。
- Manual Diagnostic：`2024/05/27～05/31` 56 張、`2024/05/20～05/24` 53 張，合計 109 張。
- Owner 排除的 65 張：`2024/06/02～06/07`；本輪沒有下載它。
- 以上清單皆不含 A45、B78、C77、D42、E87 的日期／張數指紋。

因此 A45 在派送前符合「不同、未完成、可診斷」條件。B～E 尚未開始，不能被本報告宣稱為已核對完成或已下載。

### 2.1 白話判讀：為什麼點 A45、為什麼知道它尚未下載

- **為什麼點 A45：**不是靠記憶或沿用舊座標，而是先在當下截圖中看到同一張卡片的日期 `2024/04/22～04/26` 與張數 `45`，再點該卡片的日期 metadata strip；進入後又讀到相同日期、`45張照片` 與建立日 `2024.04.27`，並確認是 grid 而非單張 viewer。兩層身分一致才繼續。
- **為什麼知道尚未下載：**派送前比對正式 VERIFIED、Manual Archive、既有 backups 與本機已下載資料；這些指紋都不含 A45。A45 的目的地另確認為新空資料夾，下載後也實際數到 45 個檔案並逐檔驗證。這裡靠的是檔案與紀錄證據，不是只憑畫面或印象。
- **為何仍算 MANUAL_DIAGNOSTIC：**A45 沒有寫入正式 VERIFIED 狀態；後續 duplicate guard 必須同時把本次本機 A45 視為既有資料，不能因正式 state 未變而重下載。

## 3. A45：實際操作順序

1. 從 LINE 相簿列表的 fresh screenshot 開始，記錄目前相簿卡片、AX 與 scrollbar 值。
2. 實際向下捲動四次；每次都有前後截圖與 AX，scrollbar 值依序為 `0 → 536 → 1073 → 1610 → 2147`。
3. 在 `04-scroll-4` 看到候選 A45 的卡片 metadata strip：日期 `2024/04/22～04/26`、張數 `45`。
4. Vision OCR 定位日期框為 `[26.803, 956.463, 238.549, 24.112]`，張數框為 `[29.484, 991.292, 32.164, 24.112]`。
5. 點擊日期 metadata strip 內的 `[120,968]`，沒有點封面中心。結果進入 grid 詳細頁，不是 `(1/N)` viewer。
6. 詳細頁再次顯示 `2024/04/22～04/26`、`45張照片`、`2024.04.27`，內容為照片 grid；AX 沒有暴露這些文字，因此使用 fresh screenshot＋OCR 確認。
7. 點擊右上三點選單。選單實際開啟後，CUA `getScreenshot` 會收起這個 transient menu，因此 menu 證據另以原生全螢幕截圖保存；沒有因此重送或改變任何交易。
8. 全螢幕 OCR 定位「儲存全部」為 `[1296.932, 386.265, 106.921, 30.804]`，依視窗與全螢幕座標換算後，點擊 `[635,276]` 一次。
9. Folder chooser 開啟。以 Go to Folder 前往新的專用目錄：`harness-development/line-five-album-manual-20261022/private/downloads/01-2024-04-22_2024-04-26_45`；開啟前確認 `0` 個檔案，然後按「打開」。
10. 下載完成後停止 LINE 操作。Owner 隨後要求暫停，因此沒有返回列表、沒有捲動至 B、也沒有第二次 Save All。

## 4. A45：下載與檔案驗證

結果：

| 驗證項目 | 實際結果 |
|---|---|
| 下載檔案數 | `45` |
| 檔名索引 | `1..45` 連續，無缺號、無非 JPEG 檔 |
| 總 bytes | `14,433,233` |
| per-file SHA-256 manifest | `45` 行 |
| manifest SHA-256 | `3e3f8253ca20aff2f5e464a7ad403d5458a6940c96fb4f99ef21f10632c1338c` |
| ImageIO full RGB decode | `45/45 PASS`、`0` failed |
| decoder 結果 SHA-256 | `577d995610349c199113b82892935de0b0ec7bee8cf2207e2404a74a4ecbb0ce` |
| 去識別化 manifest SHA-256 | `ce125d76266d664f13a858195ac9bd183cc913ef915a9feeb0d82978c7baee6f` |

去識別化 `45` 行 manifest 已放在 `public/A45-manifest.sha256`；原始照片、完整檔名對照與原始截圖只留在本機 private 目錄。

## 5. 本輪已證明與未證明

### 已證明

- 真實 LINE 中，A45 可由日期＋張數＋詳細頁三重識別。
- 點擊 metadata strip 可進入正確 grid；不是封面 viewer。
- A45 的三點選單與「儲存全部」可操作一次。
- Folder chooser 能導向指定空白資料夾。
- 45 個檔案可在一次派送後完整出現，索引、SHA-256 與 ImageIO 完整解碼皆 PASS。

### 尚未證明

- 返回相簿列表後的真實 scroll、B 的 identification、B 的 Save All／下載／驗證。
- 五本連續操作沒有 UI／座標漂移、重複下載、部分下載或 UNKNOWN。
- 正式 AUTO 的 Authorizer、grant、ledger、state commit、release 或無人值守能力。
- 本輪不宣稱 `FORMAL_TWO_ALBUM_AUTO=PASS` 或完整五本 E2E 完成。

## 6. 精準下一步建議

### 6.1 下一個 Session 的前置條件

1. 先由 Owner 指定的獨立 reviewer 審查本報告、`public/evidence-index.json`、本次 commit 與公開 manifest；本 Session 不得自填 reviewer PASS。
2. reviewer 完成後，由 Owner 明確下達下一個測試指令，並重新把 LINE 相簿列表置於前景、完成當次交接。不要把本報告或上一輪的五本授權自動延伸成新的背景交易。
3. 下一個指令若要求繼續，只先做 **B78 一本**；C77、D42、E87 不與 B78 合併派送，須等 B78 完整驗證並經 reviewer／Owner 確認後再逐一進行。

Reviewer 應先核對：

- 本報告與 `public/evidence-index.json`。
- A45 確實只派送一次，且 45/45 驗證 PASS。
- A45 已存在本機 private 目錄，後續不得重下載；但它在正式 state 中仍是 `MANUAL_DIAGNOSTIC`，不可冒充 `VERIFIED`。
- B～E 的 `NOT_RUN` 狀態不得被改寫成 PASS。

### 6.2 B78 的最小可驗證步驟

1. 重新取得 fresh LINE screenshot 與 AX；記錄 app、window、scrollbar 與畫面位置。
2. 從 A45 詳細頁按 Escape 返回列表；若無法確認已返回正確群組，停止，不用舊座標盲點。
3. 在真實列表中向下捲動至少一次，保存操作前／後兩張截圖；確認 scrollbar 值或卡片位置有可觀察位移。
4. 以 fresh OCR 找到 `2024/04/21` 與 `78`，且日期框與張數框屬於同一張卡片；不得只憑封面縮圖或舊座標判定。
5. 點擊日期 metadata strip，不點封面中心；進入後必須看到 `78張照片`、正確日期與 grid，不得是 `(1/78)` viewer。
6. 派送前再次核對 `state/backup_state.json`、`state/manual_archives.json`、既有 backups 與本輪已下載資料；若 B78 已存在，立即停止並回報 `ALREADY_EXISTS`。
7. 建立新的空資料夾 `02-2024-04-21_78`，確認開啟前為 `0` 檔。點擊「儲存全部」最多一次，保存 chooser 與派送證據。
8. 若結果 UNKNOWN、張數不是 78、出現重複 chooser、或下載中斷，立即停止整個批次，不重送 Save All。
9. 完成後驗證 78 個 JPEG 的索引連續性、bytes、per-file SHA-256、manifest hash 與完整 ImageIO 解碼；再做一次狀態指紋比對，確認沒有改動正式 state／ledger／grant。
10. 將 B78 的 PASS／FAIL／BLOCKED／NOT_RUN、一次 Save All 證據、下載與解碼結果交付獨立 reviewer；未經下一步指令，不開始 C77。

### 6.3 C77、D42、E87：B78 經審查並另行指示後

B78 完整 PASS 後，才依同一組 gates 逐本進行：

- C77：`2024/04/08～04/12`，77 張，專用空資料夾 `03-2024-04-08_2024-04-12_77`。
- D42：`2024/04/01～04/03`，42 張，專用空資料夾 `04-2024-04-01_2024-04-03_42`。
- E87：`2024/03/25～03/29`，87 張，專用空資料夾 `05-2024-03-25_2024-03-29_87`。

每本都必須重新做 fresh screenshot／OCR／AX、真實捲動、相簿詳細頁身分核對、重複下載檢查、一次 Save All、下載完整驗證。不能把 A45 或 B78 的成功推論成其餘相簿的成功，也不能把本輪五本授權視為跨 Session 的長期授權。

### 6.4 何時才可開始自動化

五本 MANUAL_DIAGNOSTIC 全部 PASS 只是「人工流程可重現」的門檻，仍不足以宣稱正式 AUTO。之後至少要有以下獨立階段：

1. **Read-only recognition dry run：** 不派送 Save All，只驗證連續五本的名稱／日期／張數／詳細頁與 scroll 定位正確，且 duplicate guard 正確。
2. **Single-album automation gate：** 選一本新的 eligible 相簿，取得當次 Save All 授權，只派送一次，完整驗證下載與未知結果停止行為。
3. **Two-album continuous gate：** 只有在單本 automation 與獨立 review 都成立後，才測試 A→返回→scroll→B 的正式連續流程。
4. **不得重用已下載的五本來製造自動化 PASS。** A45 已完成本輪 MANUAL_DIAGNOSTIC；B～E 若在本輪完成，也不能再被當成下一次自動化的全新測試資料。

## 7. 狀態矩陣

| 狀態 | 值 | 說明 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `PARTIAL` | A45 PASS；五本與正式 AUTO 未完成 |
| `IMPLEMENTATION_STATUS` | `NOT_CHANGED` | 沒有修改產品原始碼 |
| `CORE_ACCEPTANCE_STATUS` | `PARTIAL` | A45 單本鏈路 PASS；B～E NOT_RUN |
| `REQUIRED_VERIFICATION_STATUS` | `PARTIAL` | A45 檔案驗證 PASS；其餘 NOT_RUN |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | 尚未有本次獨立 reviewer 的真實審查結果 |
| `TASK_CLOSURE_STATUS` | `OPEN` | 待 reviewer 與 Owner 下一個測試指令 |

## 8. 證據索引與隱私

完整私有證據位於本機：

`harness-development/line-five-album-manual-20261022/private/evidence/`

下載檔位於本機：

`harness-development/line-five-album-manual-20261022/private/downloads/01-2024-04-22_2024-04-26_45/`

為避免公開兒童照片、群組名稱與本機個人路徑，以下只提交去識別化報告、OCR 摘要、per-file hash manifest 與證據 hash 索引；不提交原始照片、原始截圖、AX 全檔或本機私密 grant。所有私有證據保留在本機，未刪除。
