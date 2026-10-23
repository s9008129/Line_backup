# 已證實的 LINE 實機操作經驗與限制

以下是可重用的**方法與判斷**，不是允許複製座標或重新下載既有相簿的授權。

## 2026-10-22／PR28 五本實機紀錄

來源：repo `harness-development/line-five-album-manual-20261022/E2E測試報告.md`（PR #28）。

- A45：前一輪已完成 45/45，這一輪唯讀確認，**沒有重派 Save All**。
- B78、C77、D42、E87：在 Mac 真實 LINE 介面，透過 AI Agent + Computer Use、fresh screenshot、AX、macOS Vision OCR 交叉核對，再各執行一次 Save All；新增 78+77+42+87 = **284/284** 張；加上 A45 共 **329/329** 張。實際 JPEG 檔數、連續索引、非零 bytes、SHA-256 manifest、ImageIO 完整解碼均通過。
- 成功操作序列：在列表中由日期和張數辨識同一張卡片 → 點卡片文字 metadata strip → 詳細頁重新核對日期與總張數 → 新鮮畫面辨識右上 `⋯` → 確認開啟功能表 → OCR 找到唯一 `儲存全部` → 單次 Save All → 使用全新空白隔離資料夾 → 觀察檔數穩定 → hash 與完整解碼驗證。
- E87 成功紀錄中 `⋯` 使用 `[610,88]`、`儲存全部` 使用 `[635,273]`，但這兩個數值只說明**當次**視窗與截圖座標轉換曾成功，**不可當作新的 session 的固定座標**。
- E87 下載後真實返回列表，scrollbar `3757 → 4294`，新畫面出現後續候選。這證明當時的列表捲動及 Agent 視覺 grounding 成功。
- D42 曾因 fresh 畫面顯示的是 E87 而**先停止、不點擊**，重新取得正確 D42 才繼續。這是應保留的保護行為，不是無限重試的理由。
- 這五本的記錄分類為 `MANUAL_DIAGNOSTIC`，**不是** `TWO_ALBUM_AUTO`、正式 authorizer／ledger transaction 或完整自動接續驗收。正式 239 張 VERIFIED、既有手動封存與 Owner 排除清單也屬受保護資料，不能誤作新候選。

## 2026-10-23／H69 菜單阻塞

來源：Owner 提供的 H69 嘗試紀錄，SHA-256 `be4f2ad22bd052e964a1b94af38355e50394dd9a5bfe060ea054ed306c168fd0`；另見 PR28 adapter。

- H69 身分（日期、69 張）已核對；初次三次菜單點擊 `[610,70]`、`[610,100]`、`[610,88]` 未開啟選單。**實際失敗的物理原因仍不明**，不能擅自歸因於縮放或 LINE 版本。
- 後續受限的一輪：`MENU_CLICK_COUNT=0`，並非再次物理點擊失敗。PR28 `scripts/line_backup_cua_adapter.mjs` 要求外部提供 `locateMenu` callback，但 repo 沒有可直接呼叫的通用實作；此契約缺口**不等於 AI Agent 無法以當次視覺觀察辨識右上選單**。
- 當時 `SAVE_ALL_COUNT=0`、`CANCEL_COUNT=0`，隔離目錄 0 files / 0 bytes；原生中斷接續 `NOT_TESTED`。沒有證據支持宣稱下載或取消 PASS。
- 改進要點：先在新授權下使用 Agent 的即時語意視覺定位，確認 CUA 坐標契約後做**一個**當次允許的點擊與後驗證；不要把尋找不存在的 locator 設為先決條件。

## 2026-10-23／PR32 其他真實 GUI 成功範圍

來源：repo `harness-development/agent-resume-20261022/evidence/line-cancel-resume-observation-20261023.txt`（PR #32）。

- CUA 在真實 LINE 已能擷取 AX、看到 101 個相簿列表 row；單次 0.25-view-height scroll 將 scrollbar `3991 → 4531`，並能點擊兩本候選的 metadata/title，從詳細頁核對身份；過期 AX ID 被拒絕後可以重新擷取。
- 上述測試**沒有** Save All、下載、取消或接續；因此不能用來宣稱 `CANCEL_RESUME=PASS`。
- PR28 手動診斷流程與 PR32 Agent-resume 控制器尚不能推定為同一個已整合且完整驗收的 runtime。不要將「不同 branch 下各自成功」升級為整體產品 PASS。

## 審查者的快速裁決

1. **GO**：本次授權明確、候選未備份、畫面 fresh、座標映射可信、動作與結果可觀察；以最小真實步驟前進。
2. **CORRECT**：要求重建已成功功能、把 absent callback 誤認為必須先開發的大工程、重跑相同離線 mock、輸出新文件卻沒有增加真實行為證據。
3. **STOP**：授權或前景不明、身份錯誤、點位映射不可信、可能覆寫舊資料、Save All 派送結果未知、動作超出當輪次數。

保護安全 gate 與避免過度工程化可以並存；真正不安全或未知時停下，架構潔癖不應成為新的前置 blocker。
