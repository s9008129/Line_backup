# 下載、notes CLI 與恢復

本文件定義記事本備份的單項交易與目前 branch 的 `notes` CLI 介面。GUI 的實際點擊仍依 [GUI 導覽與盤點](gui-inventory.md) 與當次 Computer Use 畫面；CLI 只做持久紀錄、交易與驗證，不授予 GUI 權限。

> 這些命令已在 `feature/line-notes-media` 工作樹提供，但尚未合併 `master`，也尚未經真實 GUI E2E 驗證。使用前先在 repo root 執行 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` 核對當次 commands 與 flags；退出碼契約見下節。若不存在或 help 失敗，停止並回報 `IMPLEMENTATION_NOT_AVAILABLE`，不得手寫 JSON、建空帳或改用相簿命令冒充。

## CLI 共同契約

- Agent 從 `page`／`post`／`media` 結果取得 `post_key`、`media_key`；Owner 不填 UUID、key 或內部 JSON。`lists`／`init` 使用 collection；除 `lists`、`init` 外，所有帳本命令都要 `--records-root`。`init`／`destination` 另要求 `--photo-root`；`backup/記事本/` 是 Agent 層預設，不是 CLI 全域預設。
- `memory`／`summary` 只回摘要投影：列表身分、`scan_coverage`、貼文／媒體列、`status_counts`、`local_counts`、`dispatch_blockers` 與 `all_known_media_complete`；`memory()` 與 `summary()` 是同一投影。它們不提供完整 attempt、staging 目的地或 completion manifest。`attempt_id`／`destination` 以該次 `intent` JSON 及追加事件為準，completion 以 `verify` JSON 及 `completion` 事件為準；目前沒有獨立的 attempts／completions 查詢子命令。跨 Session 可先以 `memory` 定位 `records_root` 與 blockers，再唯讀核對該帳本 `events/*.json`，不得從 `photo_root` 或目錄名猜交易。
- observation、handoff、下載與 chooser 等 evidence 參數（`--binding-evidence`、`--history-scope-evidence`、`--observation`、`--handoff`、`--evidence`、`--recovery-evidence`）必須指向專案內非空、非 symlink 的 regular file；不可用手寫字串、目錄或範例內容冒充。
- 成功的 JSON 與業務拒絕 JSON 固定含 `dispatch_authorized=false`；參數／必填欄位錯誤以 exit 2 結束，只在 stderr 顯示 argparse 錯誤，不輸出 JSON；已列業務拒絕以 exit 4 回傳 JSON；未預期內部錯誤以 exit 70 回傳 `status=INTERNAL_ERROR`、`reason=UNEXPECTED_EXCEPTION`、`dispatch_authorized=false`。`dispatch_authorized=false` 是簿記聲明，不是 GUI grant、已派送證明或 E2E PASS；不得把它改成 true 或當成 Owner 同意。
- exit 70 不是可重試業務拒絕，不得據此重送、改寫 ledger、建立新 attempt、換目的地或換入口繞過；先停止並保留現場、原始 JSON、命令與證據，回報實作者／維護者。
- 成功以 exit 0 回傳 JSON；實際使用時記錄命令、exit code 與原始輸出摘要。看到 70 時必須原樣記錄並停止，不能降格成 exit 4 或其他業務狀態。
- 業務拒絕後不得改寫事件、另開空帳、重設 ledger、換目的地或改走相簿流程繞過。先讀拒絕原因及既有事件，仍不能安全處理就保留阻塞。

## 目前子命令

以下是目前實作的命令面。實際 flags 與 JSON 欄位以當次 `--help` 及執行結果為準；離線測試通過不表示真實 GUI 或 LINE E2E 已驗證。

| 子命令 | 用途 | 不可省略的界線 |
|---|---|---|
| `lists` | 列出全部記事本帳本位置與可讀狀態 | `index.json` 只定位；不以 active-task 或最近修改時間代替全歷史 |
| `memory` | 讀單一帳本的摘要投影：貼文／媒體狀態、blockers 與本機可用性 | 不含完整 attempt、staging 目的地或 completion manifest；照片 root 消失仍可讀摘要，缺帳本不能當空帳 |
| `init` | 建立新的記事本帳本 | 只用於已證明的新列表；歷史缺損、索引毀損或候選歧義時拒絕 |
| `bind` | 將當次列表與既有帳本綁定 | 須有真實前景／觀察 evidence；不靠名稱、日期或張數猜配 |
| `scan` | 建立本次 Session 的新盤點 | 每個新 Session 開新 scan；不重用舊 cursor、舊座標或舊畫面 |
| `page` | 保存有頂底／重疊證據的列表頁 | 前後頁要有序重疊；未解卡片不得省略或假裝完成 |
| `post` | 保存貼文身分、順序、媒體候選及 `NO_MEDIA` | 文字／日期／總數不能單獨認領；貼文層與媒體層分開 |
| `media` | 保存逐媒體觀察與來源順序 | 同外觀／同 hash 仍各自保存；新媒體取目前最大編號加一 |
| `intent` | 在派送前保存 attempt、新空白暫存目錄及禁止重送 | 必須先持久保存並讀回；寫入後按「可能已派送」對待 |
| `outcome` | 記第一個實際下載結果 | `UNKNOWN` 不可任意改成 `NOT_SENT`／`STOPPED`；逾時不等於未派送 |
| `reconcile` | 以新觀察、原事件與目的地調和未知結果 | 只追加證據，不改寫原 UNKNOWN；未收斂不得 verify 或新派送 |
| `verify` | 穩定檔案、hash、解碼、發布及保存 completion | 只接受已證明 `DOWNLOAD_FINISHED` 的 attempt；不重下補帳 |
| `resume` | 接續中斷的命名／發布交易 | 只用唯一可核對的同一交易；不重送下載、不手動改名 |
| `summary` | 投影本次盤點與六類狀態、缺項及完成數 | `all_known_media_complete=true` 只代表摘要投影一致，不是畫面／檔案獨立驗收，也不是真實 LINE E2E |
| `destination` | 為新批次追加目的地綁定 | 保留舊完成路徑；不得解鎖 UNKNOWN／pending／LOCAL_CHANGED |
| `exclude` | 以觀察證據把已盤點媒體標為排除 | 只能處理已觀察項；不得覆蓋 UNKNOWN／活動 attempt，也不得成為跳過未盤點項的藉口 |
| `protect` | 以證據把媒體列為受保護歷史 | 不升格完成、不默認排除、不重下；不得覆蓋 UNKNOWN／活動 attempt |

### 必填參數矩陣

以下只列必要參數；其他可選 flags 以當次 `--help` 為準。`--records-root` 指向一個已註冊的記事本帳本，不是相簿帳本。

```text
lists        [--collection COLLECTION]
memory       --records-root RECORDS_ROOT
init         --photo-root PHOTO_ROOT --name NAME --visual-key VISUAL_KEY
             --binding-evidence FILE --history-scope-evidence FILE
             [--collection COLLECTION] [--context-id ID] [--signals JSON]
             [--recovery-authorized]
bind         --records-root RECORDS_ROOT --session-id SESSION_ID
             --observation FILE --handoff FILE [--context-id ID]
scan start   --records-root RECORDS_ROOT --session-id SESSION_ID --evidence FILE
scan finish  --records-root RECORDS_ROOT --session-id SESSION_ID
             --scan-id SCAN_ID --evidence FILE
page         --records-root RECORDS_ROOT --session-id SESSION_ID
             --scan-id SCAN_ID --page-index N --posts JSON --evidence FILE
post         --records-root RECORDS_ROOT --session-id SESSION_ID
             --post-key KEY --date-summary TEXT
             (--media-count N | --no-media) --evidence FILE
media        --records-root RECORDS_ROOT --session-id SESSION_ID
             --post-key KEY --items JSON [--missing JSON] --evidence FILE
intent       --records-root RECORDS_ROOT --session-id SESSION_ID
             --media-key KEY [--recovery-evidence FILE]
outcome      --records-root RECORDS_ROOT --session-id SESSION_ID
             --attempt-id ID --outcome {STOPPED,NOT_SENT,DOWNLOAD_FINISHED,UNKNOWN}
             --evidence FILE
reconcile    --records-root RECORDS_ROOT --session-id SESSION_ID
             --attempt-id ID --result {STOPPED,NOT_SENT,DOWNLOAD_FINISHED,UNKNOWN}
             --evidence FILE
verify       --records-root RECORDS_ROOT --session-id SESSION_ID --attempt-id ID
             [photo: --decoder FILE --decoder-sha256 SHA256]
             [--stall-seconds SECONDS]
resume       --records-root RECORDS_ROOT
summary      --records-root RECORDS_ROOT
destination  --records-root RECORDS_ROOT --photo-root PHOTO_ROOT
             --session-id SESSION_ID --evidence FILE
exclude      --records-root RECORDS_ROOT --media-key KEY --session-id SESSION_ID
             --reason TEXT --evidence FILE
protect      --records-root RECORDS_ROOT --media-key KEY
             --reason TEXT --evidence FILE
```

`--items` 是當次可下載、仍存在的媒體，依相對來源順序排列；`--missing` 只接受先前已存在的 media key，格式為 `{media_key, source_order, reason}`。`source_order` 是當次整體 slot 的 0-based 位置，writer 會讓 present items 填入其餘 slot；不得用猜測的序號建立新身分。

`scan start` 禁止 `--scan-id`；`scan finish` 必須有 `--scan-id`。照片 `verify` 必須成對提供 `--decoder` 與 `--decoder-sha256`；影片 `verify` 不傳這兩個照片參數。`post` 的 `--no-media` 與非零 `--media-count` 衝突。

`--decoder`／`--decoder-sha256` 由呼叫端提供；CLI 只核對呼叫端提供的 SHA-256，並確認執行前後是同一個 binary、沒有內容漂移，不能證明該 binary 來自 repo 的 `src/line_backup_batch/image_decode.swift`。實作者仍須自行核對建置來源、路徑與版本；來源無法確認時停止，不得以 caller 提供的 hash 相符代替 provenance。

## 啟動與帳本對帳

1. 先執行 `lists`，再讀 `.local/line-backup/active-notes-task.json`；以本次連續入口與當次畫面核對相符的 `local_list_id`，不要只讀最近一個帳本。
2. 以 `memory` 讀摘要中的列表、貼文／媒體狀態、缺項、blockers 與本機可用性；需要 attempt、staging 目的地或 completion 細節時，依上節回到 `intent`／`verify` 結果及追加事件。索引缺失、帳本損壞、證據鏈異常或出現兩個可能列表時停止相關動作，不建立新空帳。
3. 新列表只有在入口、列表身分與歷史均確認，且沒有缺損／歧義時才 `init`；從結果取得 `records_root` 後依序執行 **`init` → `bind` → `scan start`**。既有列表從 `lists`／`memory` 取得帳本後執行 **`bind` → `scan start`**；不因新 Session、照片 root 改變或使用者重交前景而重新初始化。
4. `scan start` → `page`… → `scan finish` → `post`／`media` 保存本輪完整盤點。`scan finish` 前必須已看到頂端、底端與有序重疊；`post`／`media` 需要最新完成的 scan。新 Session 必須重新看頂底與重疊，不沿用上一個 Session 的畫面 cursor。純文字貼文由 `post` 記 `NO_MEDIA`，不建立媒體下載項。
5. 重新更換照片 root 時用 `destination` 追加綁定；舊 completion 路徑不改，UNKNOWN、活動下載、pending 命名或 `LOCAL_CHANGED` 不因換位置解鎖。

## 一次一項的派送交易

每次只處理一個已核對的貼文／媒體 attempt，不得平行下載多項。固定順序如下：

1. **資格核對。** 從 `memory`／本次 scan 確認該項不是 `COMPLETED`、`EXCLUDED` 或不可跳過的 `PROTECTED_HISTORY`；`PREVIOUSLY_INCOMPLETE` 先走恢復判斷，`UNKNOWN` 先 `reconcile`。重新觀察貼文、媒體及下載控制，保存真實 evidence。
2. **建立 intent。** 在任何下載派送前執行 `intent`，讓 CLI 保存 attempt、新空白暫存目錄與「可能已派送、禁止重送」紀錄；讀回 JSON 中的 `attempt_id`、`destination`、`save_all_limit` 與 `save_all_count`。成功 intent 會帶 `status=UNKNOWN`，那是**派送前初始狀態**，不表示已點擊或下載；寫入後仍按可能已派送處理，在取得正面 `outcome` 前不得再送。`save_all_limit=1`／`save_all_count=0` 只是 intent 建立時的 ledger 約束與初始值，不是 GUI 點擊計數，也不證明記事本 Save All（或任何下載控制）實際被按下幾次；不得據此宣稱 GUI 只按一次、已派送或已下載。
3. **確認下載控制。** 只使用記事本當次畫面與工具文件提供的控制；不要沿用相簿的 `⋯ → 儲存全部`、錄影座標或舊 Session 位置。若記事本 UI 顯示批次下載控制（包括 Save All 字樣），仍要重新證明其出處、作用及目標貼文／媒體；它是記事本自己的流程，不是相簿 Save All 的替代入口。
4. **單次派送。** 每個 attempt 的記事本當次下載控制最多派送一次；若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不得沿用相簿入口。選單或 popup 的開啟輸入與下載派送分開計數；已派送但結果不明時不得重開或再點。若畫面沒有清楚出現 chooser／進度，先記錄不確定，不要用第二次點擊查證。
5. **chooser 精確讀回。** 若出現儲存位置 chooser，只輸入此 attempt 的新空白暫存絕對路徑；讀回欄位真正值，確認末層目錄、空白狀態與來源貼文一致後確認一次。不能依賴上次位置、猜資料列或盲目按 Return。欄位不符、出處不明或確認結果未知時停止，不重派。
6. **第一個 outcome。** 觀察下載完成、明確錯誤、停止或未派送的正面證據後執行 `outcome`。工具逾時、呼叫成功但畫面沒變、進度尚在跑或檔案尚未穩定，都不能自行寫 `NOT_SENT`；至少記 `UNKNOWN`。第一筆結果不可用第二筆普通 outcome 覆蓋。
7. **未知先 reconcile。** 若結果是 `UNKNOWN`，先讀原事件、原視窗、chooser／進度、實際暫存與目的地，再用 `reconcile` 追加新證據。只有調和後能正面證明已下載完成，才可進入驗證；仍不能證明就保留 UNKNOWN，不得直接 `verify`、建立新 intent、換目錄或重下。
8. **驗證與完成。** `outcome=DOWNLOAD_FINISHED` 後執行 `verify`：先保存命名／發布交易，再核對穩定檔集、預期數、非空、SHA-256、逐檔內容解碼及前後身分。成功才追加不可覆寫 completion 並讀回。驗證或紀錄寫入失敗時保留原檔，不重新下載補帳。
9. **命名中斷。** 只要來源、暫名、目標及 journal 可唯一核對，執行 `resume` 接續同一交易；`resume` 不得觸發下載。目標已存在、額外檔、symlink、hash／mtime／ctime 漂移或來源與目標歧義時，保護原檔並停止，不用手動改名解鎖。

## 恢復與不可解鎖狀態

| 既有狀態／證據 | 下一步 |
|---|---|
| `COMPLETED` 且本地完整，或整篇目錄已 `LOCAL_MISSING` | 保留完成並跳過；`LOCAL_MISSING` 回報本機不可用，不重下、不證明外部副本 |
| 完成目錄仍存在但缺檔、額外檔、hash／身分漂移或 symlink | `LOCAL_CHANGED`：保護原件，停止新派送，不重下補帳 |
| 已 `DOWNLOAD_FINISHED`、尚未 completion | 驗證現有暫存／目標並完成或 `resume`，不重下 |
| 命名／發布交易中斷 | `resume` 同一交易；不得重送下載 |
| `UNKNOWN` | 先 `reconcile`；未收斂前不 verify、不建新 attempt、不重下 |
| 明確 `STOPPED` 或 `NOT_SENT`、原檔保留且原任務授權涵蓋自動恢復 | 綁定前次 attempt，建立另一個新空白恢復目錄；已完成項跳過 |
| `PREVIOUSLY_INCOMPLETE` | 依原授權走上述恢復判斷，不當普通待下載直接派送 |
| `PROTECTED_HISTORY` | 保留來源與缺項；只有完整盤點、無列表級歧義且不是活動／UNKNOWN／pending 時才可跳過該項，不計完成或排除 |

恢復只重做原授權範圍內未完成的項目，不重跑已完成清單。原本的暫存、部分下載、證據與日誌全部保留；新 attempt 不可覆寫舊目錄或舊事件。若原 Prompt 未涵蓋恢復、UNKNOWN 無法收斂，或工具缺少安全調和能力，停止並提出最小具體問題。

## 新媒體、重排與跨列表

- 再次執行時先 `bind`，再以新 `scan start` 對帳，不重用上輪 cursor。貼文重排只更新 `source_order`，舊完成檔名不動；新媒體只補唯一可辨識者，編號取該貼文目前最大值加一。
- 貼文文字被編輯不重下舊媒體；只保存新的索引差異。若新舊媒體對應無法唯一證明，保護該篇，其他已核對篇可繼續。
- 相同日期、標題、總數、媒體 hash 或外觀不能跨列表合併；每個 `local_list_id` 分開，跨帳本寫入一律拒絕。
- `init` 建立空帳只適用真正新列表；`destination`、重掃、刪除照片、清空暫存或改索引都不能把 UNKNOWN／pending 解鎖。

## 結束對帳

每完成一項立即保存並讀回，不把整批成功留到最後才寫。最終執行 `summary`，再以當次列表／貼文畫面核對：

- 貼文總數、`NO_MEDIA` 篇數、六類媒體狀態及未解缺項。
- `COMPLETED` 的檔案驗證與 completion 讀回；`LOCAL_MISSING`／`LOCAL_CHANGED` 分開列示。
- 是否有活動下載、UNKNOWN、未完成命名交易、先前未完成或不可跳過的受保護歷史。

`summary` 的 `all_known_media_complete=true` 只表示呼叫者提供的已知貼文／媒體簿記與覆蓋資料一致，不代表 GUI、個別檔案或真實 LINE E2E PASS。只有 `scan_coverage=COMPLETE`、貼文細節覆蓋完整、六類狀態沒有未解阻塞且 `dispatch_blockers=[]`，才會有此值；個別 `PROTECTED_HISTORY` 或 `LOCAL_MISSING` 仍須明列，不能稱整份列表在本機全部可用或全部備份成功。

本機可用性另以 `local_counts` 四類回報：`VERIFIED_PRESENT`、`LOCAL_MISSING`、`LOCAL_CHANGED`、`NOT_APPLICABLE`；不得只列前兩類，也不得把它們混成六類業務狀態。
