# Blocker packet：Swift gate attempt-policy overrun

**Decision needed:** 是否啟動新的 Critical Planner 計畫，要求它提出符合既有 Harness attempt policy 的 G_OFFLINE 完成路徑；該計畫不得假設能重置目前四次同 root issue 執行。若替代路徑需要修改 attempts、G_OFFLINE 的必要性/證據門檻或架構，必須將它們列為新決策並先取得使用者明確授權及適用的獨立 Plan Review/waiver。

## 最小重現與證據

固定命令以 `/usr/bin/swift test --package-path /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/rev28 --sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk --scratch-path /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/swift-build-26.5` 執行。Task-local env 綁定 `LINE_BACKUP_INSPECTION_FIXTURES` 與 module cache，收據記錄實際 argv/env/stdout/stderr。

- 最早 Swift mapper run `668ea46f205c42f1b5d5ba5aa3f966e4`：兩個 Swift initializer 缺 x/y label，compile 未進 tests。
- 第二個 `5b37804c7b314bdeb80238d415d2fc1f`：fixture env 缺漏，16 個 ProjectBackupBinding setup errors。
- 第三個 `85355bab929e445c8719cd6056e3c591`：320 tests/3 failures；巢狀 fixture state destination/intent.destination 仍引用舊 task root。
- 第四個 `24fbfc8ff57743af97e60a9edc25ba23`：同樣 320 tests/3 failures，原因未解。

目前已將四筆順序寫入 `attempt-ledger.json`。同 root issue 的三次上限已被超過；不得再以同一 root issue 執行 Swift package tests，也不得重設或拆分其名稱掩蓋歷史。原始 receipts/stdout/stderr 全部保留在 `evidence/swift-26.5-*`。

## 其他硬 gate 與現況

- G_AUTH=BLOCKED；G_OFFLINE=FAIL；G_MIGRATION=NOT_RUN；G_MENU=BLOCKED。
- G_CATALOG、G_FIRST、G_SCROLL、G_SECOND 均 NOT_RUN；G_PRESERVE、G_REPORT 為 PARTIAL；G_ACCEPTANCE=BLOCKED；G_DELIVERY=NOT_RUN。
- Python 77 項及 Node 10 項有 PASS 收據，但 Node 使用 fake I/O，且它們不能覆蓋 Swift suite 失敗或 live sensor integration。
- 沒有 formal execution grant/source freeze；沒有 production full-display SCK/paired sidecar/callback；transaction audit 的巢狀權限、dispatch receipt、GUI quota、prepare 副作用和 final inventory 漂移項目仍未解。
- State 仍 schema 2/revision 34/hash `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`，config hash 仍 `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`。沒有 state、destination 或 LINE 副作用。
- 使用者已交出 LINE 群組相簿列表前景；本輪未擷取/輸入。需等前置 gates 解除並重新確認當下畫面後，才可開始 live preflight。

## 停止條件與精確下一步

在新 Planner 決策之前，停止這個 Swift root issue 的所有測試與修正循環；停止 migration、任何 LINE foreground input、Save All、chooser 和下載。下一步只需 Planner 明確判定：既有 gate/attempt policy 下是否存在可合法完成 G_OFFLINE 的獨立證據路徑；如不存在，提出確切需使用者決定的 policy/gate 選項，不能默認放寬。
