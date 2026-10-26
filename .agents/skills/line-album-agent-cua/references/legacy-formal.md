# 封存歷史與去重來源

2026-10-26，Owner 選擇保留日常 Agent 備份，封存後移出舊研究、控制器、正式交易程式與測試。退役不代表舊驗收完成，也不會重新開啟任何 grant、ledger 或 UNKNOWN 派送。

## 每次啟動查找

讀專案 `.local/line-backup/history-index.json`，核對它的 `archive_manifest`：一般檔案、bytes、SHA-256 及實際位置都須相符。該 manifest 的 `entries` 逐項列出 `original`、`archive`、節點型別及檔案 hash；用完整 `original` 精確查找，再唯讀開啟 `archive` 所指原件。不要把 `original` 的舊專案路徑當成仍存在。

依 `history_source_roots` 查原始正式 state、人工 archives、逐本 completion、checkpoint、批次 summary、排除與未知操作。manifest 同時包含合成 fixture；不可把 fixture 的完成狀態當成真實 LINE 歷史。

原件內若引用相對路徑，先按其原本的邏輯 task 位置解析成原專案相對路徑，再用 manifest 查該原位置；`join:` 的 project-relative 路徑也按此查找。舊絕對路徑僅在確認屬 manifest 的原專案根目錄後轉成 `original`。核對被引用內容 hash，不改寫原件內的路徑或狀態，也不為了舊 validator 而建立 symlink。

## 保留原來的判定界線

- 索引是位置對照，不是新帳本、完成證明、GUI 授權或 runtime grant。
- 原始 VERIFIED、人工 COMPLETED、EXCLUDED、UNKNOWN、STOPPED 與實際派送事件分開閱讀；不補造欄位、不升格驗收、不只按日期／張數跨列表合併。
- 能可靠對應本地列表、完整相簿身分與現有支援證據時，沿用日常工具的既有 history 規則；舊格式或證據不足者仍為 `PROTECTED_HISTORY`，不重下，也不算完成。
- 封存缺失、hash 不符或身分不明時，保留既有資料並回報具體缺件。不能因原資料夾已移出、索引不存在或目的地是空的，就當成沒有舊備份。

現行 `.local/line-backup/active-task.json` 與照片目的地的 backup-records 仍是日常進度來源，整理沒有重寫其事件。

## 歷史研究

舊程式、原 AGENTS、Plan、grant、ledger、凍結 runtime 與證據均由 manifest 定位。一般日常任務不載入或啟動它們。未來若 Owner 明確要求恢復研究，另定版本、資料／操作範圍與適用審查，先在隔離位置恢復必要原件；封存不保證舊 runtime 能原地重播，也不重新授權任何下載。
