# 舊 continuation 實作安全移除報告

## 授權與範圍

使用者先要求安全移除本次修復不需要的檔案，隨後明確指定：`harness-development/catalog-diagnostic-continuity-replan-20261010/results/implement-continuation-handoff/handoff.md`，並要求「跟這個有關的實作檔案都安全移除」。本次以此較精確的範圍執行，不擴大成整個專案清空。

該 handoff 將新增實作限定於舊 task 的 `repair-01/`。實際檢視找到相關 runner、Swift helper、parser、guard、checks、tests、profiles、writer 暫存、建置快取及 run 結果，另有相關 `tmp/smoke-repair/`。Git 確認兩處均沒有已追蹤檔案；在 `src`、`scripts`、`rev28/Sources`、`rev28/Tests` 與新 E2E `candidate` 搜尋 `repair-01`，沒有找到程式引用。

## 已執行

兩處已從工作區以同磁碟原子 rename 移至：

`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup_local_archives/catalog-continuation-20261010T035451Z`

封存內保留原本的專案相對路徑。共 **1,021 個檔案、555,287,414 bytes（約 530 MiB）**，所有檔案 SHA-256、大小與權限均與移動前逐項相符；原實作路徑已不存在。這是從工作區移除並完整封存，不是永久刪除，亦不會降低同一磁碟的總占用。

移動前後比對 **266 個保護檔案**，包括目前設定、state、既有備份檔案、研究所需來源，以及既有已修改追蹤檔案；內容雜湊均不變。未執行 `git clean`、reset、還原既有 dirty code、影像 OCR、LINE 操作、下載或 E2E。本次新的全螢幕 E2E 候選、建置及進度保留。

## 歷史事實保留

原候選 `candidate/`、`replay/`、`offline-validation/`、diagnostic-spec、原 ledger、review、handoff、修復失敗報告仍在原位置，供本次研究與計畫核對。舊 handoff 旁新增封存說明，原 handoff 位元組未變。

本次讀到舊 `repair-01/results/repair-ledger*.json` 已記錄累計 **3+2=5 次**方法；最後一次原始紀錄為 exit 2、18 PASS、R17 FAIL、R20 NOT_RUN。這是既有紀錄，本次沒有重跑或重新認證那些測試。兩份 ledger 的逐位元組複本放在 `historical-ledger/`；完整原始碼、run、OCR 與失敗證據仍留在專案外封存中。清理不重置額度，不把舊失敗改成 PASS。

## 取證與還原

- `archive-manifest.json`：移動前清單、逐檔雜湊／權限、來源與目的地，以及保護檔案的基準。其 PREPARED 狀態代表移動前紀錄，與完成 receipt 分開保存。
- `cleanup-receipt.json`：實際移動與移動後核對結果。
- `cleanup.py`：本次固定兩處的操作；已有 manifest 時拒絕重跑。
- `restore.py`：預設只核對封存及路徑碰撞；加 `--apply` 才還原，拒絕覆蓋已存在的來源目錄。

先核對：

```sh
python3 -B harness-development/catalog-continuation-cleanup-20261010/restore.py
```

需要復原時：

```sh
python3 -B harness-development/catalog-continuation-cleanup-20261010/restore.py --apply
```

目前沒有執行實際還原。若未來來源位置已有新內容，不可強制覆蓋，應先處理碰撞。

## 接續本次修復

Implementer 使用新的全螢幕 E2E 計畫與 handoff，保留本次新找到的歷史第 5 次方法紀錄。若其先前 fresh baseline 包含已封存的舊路徑，保存該 baseline 原檔，以本次使用者授權與清理 receipt 記錄變動，另建立後續有效來源的基準；不要改寫原 snapshot 或默默忽略 preservation gate。原始封存必要時仍可按 manifest 核對。

本清理完成只代表指定舊實作已安全移出工作區，不代表 LINE 自動備份修復或 E2E 已完成。
