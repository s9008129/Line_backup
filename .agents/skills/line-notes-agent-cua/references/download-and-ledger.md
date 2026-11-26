# 下載、notes CLI 與恢復

本文件是記事本備份單項交易與操作順序的唯一來源，也定義本工作樹應有的 `notes` CLI 契約介面。GUI 的定位與觀察依 [GUI 導覽與盤點](gui-inventory.md)，結果、驗證與恢復依 [驗證與恢復](verification-and-recovery.md)，證據欄位依 [證據範本](evidence-template.md)。CLI 只做持久紀錄、交易與驗證，不授予 GUI 權限。

> 實際命令與 flags 一律以 `feature/line-notes-media` 當次工作樹的 `--help` 為準；尚未合併 `master`，也尚未經真實 GUI E2E 驗證。使用前先在 repo root 執行 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` 核對當次 commands 與 flags；退出碼契約見下節。若本文件所用的命令不存在、help 失敗或接口不符，停止並回報 `IMPLEMENTATION_NOT_AVAILABLE`，不得手寫 JSON、建空帳或改用相簿命令冒充。

## CLI 共同契約

- Agent 從 `page`／`post`／`media` 結果取得 `post_key`、`media_key`；Owner 不填 UUID、key 或內部 JSON。`lists` 的 `--collection` 只定位 collection，`init` 用 collection 建新帳，`evidence-pack` 只建立 bundle，`list-key` 只做 identity 純計算；`memory`、`summary` 及其他持久帳本命令使用 `--records-root`，其中 `destination` 另要求 `--photo-root`。`init` 也要求 `--photo-root`。`backup/記事本/` 是 Agent 層預設，不是 CLI 全域預設。
- `memory`／`summary` 只回摘要投影：列表身分、`recovery_authorized`、`scan_coverage`、貼文／媒體列、`status_counts`、`status_counts_scope`、`all_known_media_status_counts`、`local_counts`、`unresolved_attempts`、`open_restart`、`evidence_corrections`、`dispatch_blockers` 與 `all_known_media_complete`；`memory()` 與 `summary()` 是同一投影。`unresolved_attempts` 只列尚未完成／排除／受保護的最新 attempt，不提供完整 attempt 歷史或 completion manifest，且不保證包含剩餘額度數值。`summary`／`resume` 另以 attempt phase 區分 `OUTCOME_REQUIRED`、`RECONCILE_REQUIRED`、`RECOVERY_SCAN_REQUIRED`、`REDOWNLOAD_REQUIRED`、`RECOVERY_EXHAUSTED` 與既有驗證／命名狀態；`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 是未完成報告，不計完成，也不當其他合格項的全域 blocker。`attempt_id`／`destination` 以該次 `intent` JSON 及追加事件為準，日常 completion 以 `download-check` JSON 及 `completion` 事件為準；目前沒有完整的 attempts／completions 查詢子命令。跨 Session 可先以 `memory` 定位 `records_root` 與 blockers，再唯讀核對該帳本 `events/*.json`，不得從 `photo_root` 或目錄名猜交易。貼文列以 `posts[].state` 表示，媒體列以 `status` 表示；`current_incomplete` 的 scoped 定義見[結束對帳](#結束對帳)。
- observation、handoff、下載、chooser、更正與恢復等證據參數（`--binding-evidence`、`--history-scope-evidence`、`--observation`、`--handoff`、`--evidence`、`--recovery-evidence`、`--replacement`）必須是先以 `evidence-pack` 封裝、再由 CLI 回傳的 `line-notes-evidence/v2` bundle 路徑；不可用手寫 JSON、自由文字、目錄或範例內容冒充。bundle 的 statement 可依 [證據範本](evidence-template.md) 撰寫；畫面／AX／input receipt 等原件以 `--asset ROLE PATH` 加入。`source_path` 只記錄匯入來源，重開時核對帳本內保存的子 blob，不要求原件仍在。
- `evidence-pack` 的 statement、每個 asset 與 `--output-dir` 必須使用確認 repo 根目錄後取得的絕對路徑。statement／asset 是專案內 canonical regular file，不是 symlink，且只允許單一 hard link；output 是私有 tasks 下尚不存在的子目錄，其 canonical 父目錄要先存在。Agent 只準備父目錄，不預建輸出子目錄、不自動 resolve 穿過 symlink、不覆寫。固定五欄 context 由 Agent 從 CLI 輸出帶入，適用 ID 不得填 `UNKNOWN` 或另一個主體。成功後把回傳的絕對 `bundle_path` 傳給事件參數。Owner 不需填 JSON、UUID、key 或 hash；bundle 只核對 bytes／context，不證明畫面真實、控制命中或下載結果。
- 若要以 wrapper 保存一次 child 的 request、stdout／stderr、exit／signal 與程式身分，使用既有 `notes_capture --output-root ABS_PRIVATE_TASK_DIR -- <notes argv>`；`--output-root` 必須是已存在、專案私有的絕對路徑。capture receipt 不是 CUA／GUI 原始回傳，也不證明輸入。wrapper 保存失敗就停止，不為補輸出重跑 child；拒絕與成功各自保存新 receipt。
- 同一 `--records-root`（`records` lock）或同一 `--collection`（`collection` lock）的所有 notes CLI 命令一律嚴格序列執行；不得以平行 shell 工作、背景程序或同回合並行工具呼叫同時執行 `summary`／`memory`／`evidence-audit` 與 `resume` 或其他帳本命令。`summary` 雖是唯讀業務命令，仍持 exclusive non-blocking `flock`，read-only 不代表可並行。
- 成功的 JSON 與業務拒絕 JSON 固定含 `dispatch_authorized=false`；參數／必填欄位錯誤以 exit 2 結束，只在 stderr 顯示 argparse 錯誤，不輸出 JSON；已列業務拒絕以 exit 4 回傳 JSON；未預期內部錯誤以 exit 70 回傳 `status=INTERNAL_ERROR`、`reason=UNEXPECTED_EXCEPTION`、`dispatch_authorized=false`。`dispatch_authorized=false` 是簿記聲明，不是 GUI grant、已派送證明或 E2E PASS；不得把它改成 true 或當成 Owner 同意。
- exit 70 不是可重試業務拒絕，不得據此重送、改寫 ledger、建立新 attempt、換目的地或換入口繞過；先停止並保留現場、原始 JSON、命令與證據，回報實作者／維護者。
- 成功以 exit 0 回傳 JSON；實際使用時記錄命令、exit code 與原始輸出摘要。看到 70 時必須原樣記錄並停止，不能降格成 exit 4 或其他業務狀態。exit 2 僅表示參數／必填欄位錯誤；在尚無派送或不明寫入、可由現有輸出確定正確值時，可修正命令前置條件後重跑相同的唯讀／綁定操作。exit 4 只有在明確業務原因、`retry_safe` 與可證明無資料變更均成立時，才可依輸出修正前置條件。`NOTES_LOCK_BUSY` 時，唯讀命令（`lists`／`memory`／`summary`／`evidence-audit`／`restart preview`／`reattest preview`）回 `retry_safe=true`，可於鎖釋放後序列重試一次；寫入／交易命令（含 `resume`）回 `retry_safe=false`，須先停止並序列查帳本狀態，不得盲目重試。同一根因最多三次有證據嘗試，連續兩次無新資訊就停止。不得重播 intent／GUI、改帳本／目的地、手改 events，或把 exit 70 當可重試拒絕。
- 業務拒絕後不得改寫事件、另開空帳、重設 ledger、換目的地或改走相簿流程繞過。先讀拒絕原因及既有事件，仍不能安全處理就保留阻塞。

## 合格環境附屬項

「合格環境附屬項」僅指位於 canonical 且非 symlink 的 notes 媒體容器內、名稱精確為 `.DS_Store`、以不跟隨連結 metadata 確認為 regular file 且 `nlink=1`，且未被帳本、manifest、證據或交易引用或保留的檔案。受管理名稱、manifest 目標或發布目標與其碰撞時，碰撞規則優先；其他 dotfile、未知檔／staging、額外影片、特殊檔及異常連結仍拒絕；本定義只針對完成貼文媒體容器，列表目錄下的 `.line-notes-incoming-*` 屬交易 staging，不是本定義所述的非預期額外檔。此類環境項存在、bytes 改變或消失，均不列入 witness、manifest 或媒體計數，也不改變 completion 或 `LOCAL_VERIFIED`；此定義不新增日常步驟。

## 目前子命令

以下是目前實作的命令面。實際 flags 與 JSON 欄位以當次 `--help` 及執行結果為準；離線測試通過不表示真實 GUI 或 LINE E2E 已驗證。

| 子命令 | 用途 | 不可省略的界線 |
|---|---|---|
| `lists` | 列出全部記事本帳本位置與可讀狀態 | `index.json` 只定位；不以 active-task 或最近修改時間代替全歷史 |
| `memory` | 讀單一帳本的摘要投影：貼文／媒體狀態、blockers 與本機可用性 | 不含完整 attempt、staging 目的地或 completion manifest；照片 root 消失仍可讀摘要，缺帳本不能當空帳 |
| `evidence-pack` | 將 statement、截圖／AX／input 等原件封裝成不可覆寫的 v2 evidence bundle | 只做位元引用與 context 核對；不是 GUI sensor、下載結果或 acceptance |
| `list-key` | 在建帳前以同一組 identity 輸入計算 `list_key` | 純計算，只可讀明示的 `--signals @FILE`；不讀寫帳本、照片、active 檔、鎖或事件，也不代表列表身分或下載資格 |
| `evidence-audit` | 唯讀逐引用稽核保存的 evidence、legacy 分類與 correction 鏈 | 不投影業務狀態；`integrity_ok=false` 或結構鏈異常時不得使用一般 summary 的局部結果 |
| `init` | 建立新的記事本帳本 | 只用於已證明的新列表；歷史缺損、索引毀損或候選歧義時拒絕 |
| `bind` | 將當次列表與既有帳本綁定 | 須有真實前景／觀察 evidence；不靠名稱、日期或張數猜配 |
| `scan` | 建立本次 Session 的新盤點 | 每個新 Session 開新 scan；不重用舊 cursor、舊座標或舊畫面 |
| `page` | 保存有頂底／重疊證據的列表頁 | 前後頁要有序重疊；未解卡片不得省略或假裝完成 |
| `post` | 保存貼文身分、順序、媒體候選及 `NO_MEDIA` | 文字／日期／總數不能單獨認領；貼文層與媒體層分開 |
| `media` | 保存逐媒體觀察與來源順序 | 同外觀／同 hash 仍各自保存；新媒體取目前最大編號加一 |
| `intent` | 在派送前保存 attempt、新空白暫存目錄及禁止重送 | 必須先持久保存並讀回；寫入後按「可能已派送」對待。`--restart-id` 只限已確認批次；安全隔離後由 CLI 建立 `line-notes-intent/v5`，只有這次 append 消耗跨 Session 一次額度 |
| `isolate` | 為一個持久 `UNKNOWN` 的最新 attempt 追加隔離處置 | `line-notes-attempt-isolation/v1`；零消耗、不建立 scan／attempt、不派送。只接受精確 attempt／證據／鏈頭，衝突即拒絕 |
| `outcome` | 記第一個實際下載結果 | `UNKNOWN` 不可任意改成 `NOT_SENT`／`STOPPED`；逾時不等於未派送 |
| `reconcile` | 以新觀察、原事件與目的地調和未知結果 | 只追加證據，不改寫原 UNKNOWN；未收斂且未安全隔離時不得 verify、新 intent 或新派送 |
| `download-check` | 檢查本次下載檔案的 magic MIME 與副檔名分類、非空／穩定、SHA-256，並完成防覆寫與身分核對 | 日常命令；不做 ImageIO／ffmpeg 解碼，不證明來源原件或內容完整 |
| `line-notes-download-exclusion/v1` | `download-check` 對明確非媒體的完成下載 attempt 追加 exclusion | 僅限明確 MIME `text/plain`、`text/html`、`application/pdf`、`application/zip`；保留 staging、不寫 completion、不宣稱來源原件不是媒體 |
| `verify` | 舊流程的嚴格檔案解碼、發布及 completion | 僅 legacy 相容；不作日常命令 |
| `resume` | 接續中斷的命名／發布交易 | 只用唯一可核對的同一交易；不重送下載、不手動改名 |
| `restart` | `preview`／`confirm`／`resume` 一個確認取代批次 | preview 唯讀；confirm 需精確 scope、證據與 Owner 同意；日常 `resume --download-only` 做 candidate 基本檢查與 activation，不按 GUI、不下載；舊嚴格預設相容保留 |
| `reattest` | `preview`／`confirm` 一次已轉接 list binding 的 device-only 重新見證 | 僅限既有 OPEN_BATCH 與完整 witness；confirm 需本次精確 Owner 同意；不解除 UNKNOWN／LOCAL_CHANGED，也不授權 GUI。普通 `created`／`destination` 列表只有歷史 device 差異時直接沿日常流程；不新增 reattest |
| `summary` | 投影本次盤點、六類狀態、attempt phase、缺項及完成數 | `all_known_media_complete=true` 只代表摘要投影一致；`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 仍列未完成，不是畫面／檔案獨立驗收或真實 LINE E2E |
| `evidence-correct` | 針對已精確核對的 page 追加 replacement evidence 更正 | 只修 page 引用；不改 page 成員／順序／頂底／scan 覆蓋，也不把更正當成原證據或完成證明 |
| `media-kind-correct`／`media-kind-reconcile` | 舊帳本種類修正的相容入口 | legacy only；日常流程不要求種類更正或來源種類證據 |
| `source-unavailable` | 記錄單一媒體來源已明確到期 | 只限最新 attempt 為 `STOPPED`；不是完成、排除、重試授權或服務端已回收證明 |
| `destination` | 為新批次追加目的地綁定 | 保留舊完成路徑；不得解鎖 UNKNOWN／pending／LOCAL_CHANGED |
| `exclude` | 以觀察證據把已盤點媒體標為排除 | 只能處理已觀察項；不得覆蓋 UNKNOWN／活動 attempt，也不得成為跳過未盤點項的藉口 |
| `protect` | 以證據把媒體列為受保護歷史 | 不升格完成、不默認排除、不重下；不得覆蓋 UNKNOWN／活動 attempt |

### 必填參數矩陣

以下只列必要參數；其他可選 flags 以當次 `--help` 為準。`--records-root` 指向一個已註冊的記事本帳本，不是相簿帳本。

```text
lists        [--collection COLLECTION]
memory       --records-root RECORDS_ROOT
evidence-pack --statement FILE [--asset ROLE PATH ...] --output-dir NEW_DIR
             [--list-key KEY] [--post-key KEY] [--media-key KEY]
             [--attempt-id ID] [--scan-id SCAN_ID]
list-key     --visual-key TEXT [--context-id TEXT] [--signals JSON_OR_@FILE]
init         --photo-root PHOTO_ROOT --name NAME --visual-key VISUAL_KEY
             --binding-evidence FILE --history-scope-evidence FILE
             [--collection COLLECTION] [--context-id ID] [--signals JSON_OR_@FILE]
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
             --media-key KEY [--restart-id RESTART_ID | --recovery-evidence FILE]
isolate      --records-root RECORDS_ROOT --session-id SESSION_ID
             --attempt-id ID --evidence BUNDLE
             --expected-tip JSON_OR_@FILE
outcome      --records-root RECORDS_ROOT --session-id SESSION_ID
             --attempt-id ID --outcome {STOPPED,NOT_SENT,DOWNLOAD_FINISHED,UNKNOWN}
             --evidence FILE
reconcile    --records-root RECORDS_ROOT --session-id SESSION_ID
             --attempt-id ID --result {STOPPED,NOT_SENT,DOWNLOAD_FINISHED,UNKNOWN}
             --evidence FILE
download-check --records-root RECORDS_ROOT --session-id SESSION_ID --attempt-id ID
verify       --records-root RECORDS_ROOT --session-id SESSION_ID --attempt-id ID
             [photo: --decoder FILE --decoder-sha256 SHA256]
             [--stall-seconds SECONDS]  # legacy compatibility only
resume       --records-root RECORDS_ROOT
restart preview --records-root RECORDS_ROOT
restart confirm --records-root RECORDS_ROOT --session-id SESSION_ID
             --preview @PREVIEW_JSON --evidence BUNDLE
restart resume --records-root RECORDS_ROOT --session-id SESSION_ID --download-only
             # daily basic-check path; legacy strict default remains compatible
reattest preview --records-root RECORDS_ROOT --session-id SESSION_ID
reattest confirm --records-root RECORDS_ROOT --session-id SESSION_ID
             --preview @PREVIEW_JSON --evidence BUNDLE
summary      --records-root RECORDS_ROOT
evidence-audit --records-root RECORDS_ROOT
evidence-correct --records-root RECORDS_ROOT --session-id SESSION_ID
             --page-sequence N --page-sha256 SHA256
             --original-evidence-sha256 SHA256 --replacement BUNDLE
             --reason TEXT [--previous-correction-ref JSON]
media-kind-correct / media-kind-reconcile # legacy compatibility only
source-unavailable --records-root RECORDS_ROOT --session-id SESSION_ID
             --media-key KEY --attempt-id ID --evidence BUNDLE
destination  --records-root RECORDS_ROOT --photo-root PHOTO_ROOT
             --session-id SESSION_ID --evidence FILE
exclude      --records-root RECORDS_ROOT --media-key KEY --session-id SESSION_ID
             --reason TEXT --evidence FILE
protect      --records-root RECORDS_ROOT --media-key KEY
             --reason TEXT --evidence FILE
```

`--items` 是當次可下載、仍存在的媒體，依相對來源順序排列；`--missing` 只接受先前已存在的 media key，格式為 `{media_key, source_order, reason}`。`source_order` 是當次整體 slot 的 0-based 位置，writer 會讓 present items 填入其餘 slot；不得用猜測的序號建立新身分。

`scan start` 禁止 `--scan-id`；`scan finish` 必須有 `--scan-id`。日常 `download-check` 不需 decoder；舊 `verify` 的照片 decoder 參數仍按舊介面成對提供、影片不傳照片參數。`download-check` 只有在 magic MIME 明確為 `text/plain`、`text/html`、`application/pdf` 或 `application/zip` 時才追加 `line-notes-download-exclusion/v1` 並保留 staging；不寫 completion，也不推論來源原件的類別。未知 MIME、`application/octet-stream` 或 MIME／suffix 不相符時維持 pending 並拒絕完成。`post` 的 `--no-media` 與非零 `--media-count` 衝突。未知種類使用 `identity.kind=UNCLASSIFIED`；既有媒體沿用原 key／identity，不為取得種類或避開歷史另建 key。`isolate --expected-tip` 只接受 strict JSON 字串或 `@JSON-file`，物件為目前鏈頭的精確 `{"sequence":N,"sha256":"…"}`；caller 不填 media key、scan id、destination、disposition、額度或 event refs，均由 CLI 從 exact `--attempt-id` 與帳本導出。

`summary`／`resume` 保留的 legacy `VERIFY_REQUIRED` 標記在日常表示尚待 `download-check`；不得因此啟動舊 `verify` 或來源種類取證。

`list-key` 成功 JSON 只增加 `identity`、`list_key` 與既有 `dispatch_authorized=false`，不建立或查詢帳本。`visual_key`／`context_id` 僅以 strip 後非空作檢查，實值的前後空白與 Unicode 原樣保留；context 未提供才是省略，空字串／全空白拒絕。signals 未提供與 JSON `null` 都視為省略，`{}` 是實際值；JSON 物件 key 次序／排版不改 key，字串內容與陣列次序保留。沿用 4096 字元字串、256 KiB identity、strict JSON（拒絕 duplicate key／NaN）限制。缺參數或 JSON 語法錯 exit 2、identity 業務拒絕 exit 4、未預期例外 exit 70；沒有 `--collection`／`--records-root`／照片／evidence 參數，也不參與帳本 lock／retry。

`evidence-audit` 是不可寫入的一般唯讀命令；event chain／結構性引用無法可靠解析時停止，不輸出可誤用的 audit row。引用或子 blob 漂移時仍輸出 audit JSON，但 `integrity_ok=false`、exit 4、`business_projection_omitted=true`，不得從它推論完成數或下一步。legacy opaque 可保持 `LEGACY_OPAQUE`／`REFERENCE_CHECK_NOT_AVAILABLE`，這不是損壞，也不是已核對的原始位元。

### 舊 UNKNOWN 的安全隔離與一次補下載

本節是普通 `UNKNOWN` 的獨立單項路徑，不是 `STOPPED`／`NOT_SENT` 恢復，也不是 restart generation。尚無 outcome 時仍先用 `outcome` 保存第一筆真實結果；已有持久 `outcome=UNKNOWN` 才可用新證據 `reconcile`。若可靠證據已能證明原下載完成，接續原 attempt；不要為可收斂的結果另建補下載。v5 補下載額度以單一 `media_key` 為 scope，不由同貼文、列表或 Session 的其他媒體共用；另一個媒體的 B1／readiness `READY` 也不解除本項未隔離 `UNKNOWN`／no-outcome 的全域停止。

重新交接後，新 Session 先以當次 CUA 工具文件支援的唯讀 app／window 列舉與 handle reacquire 核對同一已授權列表及有效前景（`osascript`／System Events 非 CUA reacquire，只能作非 CUA OS 唯讀診斷）；證據不足即停止輸入並記錄具體阻塞。前景有效後完成 `bind`；未 `bind` 前不寫 outcome／reconcile／isolate。先讀 `summary` 的 `unresolved_attempts`，以 `has_outcome`、`last_result`、`attempt_phase` 與原事件區分 `OUTCOME_REQUIRED`、`RECONCILE_REQUIRED`、`RECOVERY_SCAN_REQUIRED`、`REDOWNLOAD_REQUIRED` 與 `RECOVERY_EXHAUSTED`。尚無 outcome 不等於 `UNKNOWN`，不得直接隔離。普通 intent 以同一 `media_key` 的完整歷史計算，跨 Session 最多三筆，包含最多一筆 v5；精確 restart 的 v3 不計入。合法 `STOPPED`／`NOT_SENT` 恢復可使用普通第三筆，只要總額未超過三筆，並符合原授權、來源與前景證據 gate。摘要若沒有額度欄位，只回讀同一 `media_key` 的全部普通 intent（含 v5）及 attempt-isolation 事件判定，不從列表總覽、其他媒體或 Session 推測。隔離仍要求帳本已持久 `recovery_authorized=true`；`false` 或未持久化時停止該恢復，不手改紀錄或以新帳、換目的地繞過。

1. **有限前景核對。** 隔離前以當次最新 AX／截圖核對有效前景、目標列表／viewer、舊 chooser／modal、可歸屬活動下載、來源歧義與舊 staging 身分。舊 staging 必須是空目錄，或只有至多一個非隱藏、非零、單連結、支援照片／影片副檔名且穩定的普通檔，另可有既有合格環境附屬物；此空目錄／單一穩定普通媒體檔條件僅適用 UNKNOWN v5 隔離路徑，`STOPPED`／`NOT_SENT` 恢復不要求舊 staging 為空。這是對舊目標的 bounded witness，不是新完整 scan，也不能拿它宣稱列表覆蓋。證據仍用 `line-notes-evidence/v2`，context 精確綁舊 intent 的 `list_key + post_key + media_key + attempt_id + scan_id`；舊 scan id 不得填 `UNKNOWN`。statement 引用舊 UNKNOWN 結果事件與當次原目標和前景觀察。CLI 驗證 bundle 結構、bytes／hash 與引用，GUI 觀察由 Agent 核對。

2. **第一次追加隔離，零消耗。** 只有目標仍是同媒體最新 attempt、已有第一筆 `UNKNOWN` 且未終止、尚無 completion／exclusion／protection／source-unavailable／pending naming／開放的手動 restart，且同一 attempt 尚無隔離事件時，才可執行一次：

   ```sh
   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes isolate \
     --records-root "$RECORDS_ROOT" --session-id "$SESSION_ID" \
     --attempt-id "$ATTEMPT_ID" --evidence "$ISOLATION_BUNDLE" \
     --expected-tip '{"sequence":N,"sha256":"…"}'
   ```

   `--expected-tip` 必須等於呼叫前讀到的目前鏈頭；接受 strict JSON 或 `@JSON-file`。成功事件 kind 為 `attempt-isolation`、schema `line-notes-attempt-isolation/v1`，由 exact intent 導出舊路徑與身分。隔離本身**零消耗**：不派送、不建立 scan／新 attempt、不建立 restart、不消耗跨 Session 補下載額度。從隔離回覆讀取 `next_action` 與 `redownload_remaining`，後續以摘要的 `attempt_phase` 追蹤。普通總額有餘且 v5 尚未使用時，先進 `RECOVERY_SCAN_REQUIRED`，完成新掃描後成為 `REDOWNLOAD_REQUIRED`。用完普通總額或 v5 時，首次隔離也會回 `RECOVERY_EXHAUSTED`、`redownload_remaining=0`。v1 `disposition` 保留其既有 v5 子額度語意，不能單獨推論普通總額仍有餘額。精確重放回覆也包含有效額度與 `next_action`。

3. **fencing 與重放。** 目標不是同媒體最新 attempt、鏈頭／binding／intent／result／destination ref 不符、舊 staging 或身分變動、重複隔離、分支或亂序都應 exit 4 拒絕並保留原帳本。同一 attempt 的隔離已是鏈頭時，只可用完全相同 session、refs、evidence、disposition 與原 `expected_tip` 作精確重放，成功才回 `replayed=true`；鏈頭、payload 或引用不同即拒絕，不新增第二條分支。若 CLI 寫入結果不明，只可唯讀重查同一 ref；不得重送 GUI、改路徑或另建 attempt。

4. **隔離後新掃描。** 隔離讀回後，舊 attempt 不再是普通 `scan start` 的全域派送 blocker，`destination` 仍須通過原有檢查。若該媒體仍待補下載，由目前綁定 Session 重新完成普通完整卡片掃描，再完成目標貼文／媒體細盤；新 scan 的 start sequence 必須大於 isolation sequence、屬於目前綁定 Session 且是目前最新完整 scan，目標貼文／媒體細盤也必須對應這次最新 scan。隔離前的舊 scan、cursor 或有限前景核對都不能當成這次完整盤點。

5. **只在額度允許時建立 v5。** 完成上述條件後，先核對同一 media key 的普通 intent 總額少於三筆、v5 尚未使用，再依 B1 取得當次 `checkDownloadReadiness=READY`，才以既有 `intent` 建立補下載；helper `STOP` 時保留本項，不能為跳過 blocker 直接呼叫 CLI。B1 可見時分別核對 DIRECT 與備選 REVEAL，備選 REVEAL 不合格不使合格的 DIRECT 失效；只有 intent 前已保留的 READY 與 intent 後最新原件重核成立，才可在同一 intent 後單次 reveal。CLI 自動使用 `line-notes-intent/v5`、連結 `isolation_ref` 與 `recovery_of`，不接受 caller 自填隔離欄位或以 `recovery_evidence` 替代。只有這次 v5 intent 的單一 append 原子消耗這個 `media_key` 的額度；A 的 v5 不消耗 B 的首次額度，B 仍須有自己的隔離、隔離後完整 scan 與 readiness。成功回應可保留 `status=UNKNOWN`，並應有 `phase=OUTCOME_REQUIRED`、`isolation_ref`、`redownload_budget=CONSUMED`、`dispatch_authorized=false`。新 attempt 仍使用新空白 staging、重新通過 B1、當次下載控制與 chooser 各最多一次；不能重用舊 viewer／chooser／路徑。

6. **再次不明與用盡。** 若最新 attempt 已記持久 `UNKNOWN` 且安全前提仍成立，可隔離並保留原結果。普通 intent 以同一 media key 跨 Session 最多三筆為限（含首次），其中 v5 最多一筆。用完任一適用額度時，隔離回 `redownload_remaining=0`、`next_action=RECOVERY_EXHAUSTED`。v1 事件的 `disposition` 描述 v5 子額度，因此先用完普通總額時可能仍是 `REDOWNLOAD_AVAILABLE`。採用 `next_action`／`attempt_phase` 判斷下一步。普通總額已用完時，CLI 拒絕新 intent，回 `AUTO_RECOVERY_ATTEMPT_LIMIT`。用盡只列該項欠件，其他合格項可繼續；原有全域阻塞及安全前提仍需核對。

7. **晚到與舊史。** 舊 attempt、outcome／reconcile、隔離、證據、路徑與可能晚到的 staging 檔全部保留。晚到檔只屬舊 attempt，不得轉成最新 completion、發布、清理、合併或覆寫新 staging；接受背景晚到仍可能發生的殘留風險。此保留不因舊 staging 目前為空而解除（一般規則見[恢復與不可解鎖狀態](#恢復與不可解鎖狀態)）。舊 attempt 的 outcome／reconcile／download-check／verify／naming 與晚到檔都不能繞過隔離歷史轉正。

8. **報告與界線。** `REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 必須列在未完成報告；前者表示合格新 scan 後尚待 v5，後者表示額度用盡，兩者都不是全域完成或全域阻擋。未隔離／無法安全處理的 `UNKNOWN`／no-outcome 仍是全域 blocker。精確 restart／reattest、`STOPPED`／`NOT_SENT` 恢復、`LOCAL_CHANGED`、批次 scope、換目的地與相簿流程各自保留原 gate，不能被本路徑替代。

**v5 後 `STOPPED`／`NOT_SENT`。** v5 intent 一經有效 append 即消耗唯一 v5 額度且不退還。若之後有充分證據記為 `STOPPED`／`NOT_SENT`，不得再建立第二筆 v5、以再隔離重置額度或改寫舊 outcome；但若普通 intent 總額尚未達三筆，可依合法恢復路徑建立下一筆普通 intent（最多第三筆）。只有在全域 blocker 為零、原檔與舊史保留、帳本已有持久 `recovery_authorized=true`、正式 Prompt 的原任務授權涵蓋恢復、前景有效且停止證據充分時，才可依既有 `intent --recovery-evidence` 精確恢復。`--recovery-evidence` bundle context 綁定舊 prior 的 `list_key`、`post_key`、`media_key`、`attempt_id` 與 `scan_id`；statement 同時引用原停止事件及本次新完整 scan、目標細盤與有效前景，新 intent 本身綁目前完整 scan。新 attempt 仍走新空白 staging；舊 v5 intent、outcome、隔離與 staging 不得刪除、覆寫或合併。`recovery_authorized=true` 不能代替正式 Prompt 原授權；未持久化／`false`、證據不足或有其他未決 attempt 時停止。

### 確認取代恢復（restart）

排除前述「舊 UNKNOWN 的安全隔離與一次補下載」後，正常流程沒有 `RESTART_REQUIRED`／`OPEN_BATCH` 時，未隔離的 `UNKNOWN`、pending 與 `LOCAL_CHANGED` 仍依原禁止重送規則停止。只有完整盤點已成立，才能用此批次處理無法直接接續的舊交易；它不是普通新下載，也不是無限重試授權。

1. **預覽。** 在任何新恢復 intent 前執行 `restart preview --records-root RECORDS_ROOT`，保存完整 JSON。`RESTART_REQUIRED` 是新的待確認批次；`OPEN_BATCH` 是既有未完成批次，回傳 `open_batch` progress；`NO_RESTART_REQUIRED` 不建立批次。preview 唯讀，不建立目錄、intent、確認或 activation。
2. **精確確認。** Agent 以白話列出列表、受影響貼文／媒體、已完成 sibling、舊版位置、新 `versions/gNNNNNNNN/` 目錄、額外空間估算、來源缺項與 `EXCLUDED`／`PROTECTED_HISTORY` 保留項。Owner 明示同意後，以同一次 session 執行 `restart confirm`；preview 建議存成私有 JSON，使用 `--preview @PREVIEW_JSON` 傳入。confirmation evidence 必須是 v2 bundle，context 為 `list_key` 加 preview 的 `scope.scan_id`。CLI 在鎖內重算 expected tip 與 scope digest；preview 後的任何漂移以 `RESTART_EXPECTED_TIP_CHANGED`／`RESTART_PREVIEW_CHANGED` 拒絕，不建立確認。
3. **確認後重新盤點。** confirm 成功後必須以 `scan start --recovery` 完成一次新的完整 recovery scan；若目前仍有尚未結束的 scan，先以新 Session 明確 `scan interrupt`，不能假設 `bind` 或 `restart confirm` 會替舊 scan 收尾。不可拿 confirm 前的 page rows、cursor 或舊 scan 直接建立新 attempt。未做此 scan 時 `intent --restart-id` 回 `POST_CONFIRMATION_RECOVERY_SCAN_REQUIRED`。新 scan 只證明目前 scope／來源身分，不改寫舊 attempt 的 scan binding。
4. **逐項新 attempt。** 對 scope 內每個合格媒體執行 `intent --records-root ... --session-id ... --media-key ... --restart-id RESTART_ID`。每次仍建立新的空白 staging，當次下載控制與 chooser 最終確認各最多一次；不得使用舊 raw 路徑、舊 chooser、舊座標或舊 attempt 再按一次。沒有 outcome 時先記第一筆結果；結果未知記 `UNKNOWN`，不可偽造 `STOPPED`。
5. **候選與 activation。** 日常以 `restart resume --download-only` 對 restart candidates 執行與 `download-check` 相同的基本檔案檢查及不可覆寫發布，不做完整解碼；舊嚴格預設保留供相容舊批次。已驗證 candidate 讀回時核對 regular file、`nlink=1`、非 symlink、canonical parent、size／SHA-256、預期檔集與媒體身分；歷史 device／inode／mtime／ctime 不單獨否決內容與布局，讀取期間的變動仍拒絕。整篇版本目錄缺席為 `LOCAL_MISSING`，目錄仍在卻缺 candidate 為 `LOCAL_CHANGED`；非預期額外檔仍拒絕。scope 內若 candidate 明確是上述非媒體 MIME，回報 `RESTART_SCOPE_NON_MEDIA` 並停止，不自動改寫已確認 scope。所有 scope candidate 成立後才完成該次 `restart resume --download-only` activation。`restart resume` 只做檔案／candidate／activation，不按 GUI、不下載、不重送。
6. **再次中斷。** 同一個已確認 scope 在完成前再次中斷時，可用 `RESTART_REQUIRED`／`OPEN_BATCH` 找回原批次；已驗證 candidate 與原歷史保留，只對未完成或結果不確定的項目建立新的 v3 attempt。scope、媒體身分、舊版本、目的地或版本策略改變，必須重新 preview 與取得新的 Owner 明示同意。確認不涵蓋另一個列表、其他貼文或無限次重送。

scope 內舊 `UNKNOWN`、無 outcome 或 pending 可被新 attempt 取代，但這不證明舊操作已停止；舊事件、舊 raw、舊 completion 與 UNKNOWN 全部保留。`LOCAL_CHANGED` 只在精確 scope 內以新版本目錄重建，舊目錄不搬動、不覆寫、不自動清理。`LOCAL_MISSING` 不觸發重下；scope 外 `LOCAL_CHANGED`、`EXCLUDED`、`PROTECTED_HISTORY` 與來源 missing／expired 仍保留欠件，不得宣稱整份列表完成。`dispatch_authorized=false` 不是 GUI grant；preview／confirm／resume 的成功都只證明簿記與指定狀態，不證明真實 LINE 派送或 E2E。

### List directory device 轉接（reattest）

此協議只處理既有 OPEN_BATCH 中，canonical list path 與 inode 不變而 device 改變、且有效 binding 尚非 reattest 的情況。普通 `created`／`destination` 列表歷史 device 差異由共用容器檢查容忍，不呼叫本命令。轉接事件建立後，該有效 binding 對後續 device／inode 漂移維持嚴格；再次漂移時停止。協議保留原 restart confirmation 與 scope；不證明 remount、相同實體 volume 或排除 matching clone。每個帳本最多新增一筆轉接。

confirm 會追加 `list-directory-reattest` 事件。新版本可讀舊帳本；舊版本遇到此事件會以 `UNKNOWN_NOTES_EVENT_KIND` 拒絕。首次真實 confirm 前須確認後續 session 使用相容版本；事件寫入後不得刪除事件或回退成空帳。

1. 在已核對的 session 執行 `reattest preview --records-root RECORDS_ROOT --session-id SESSION_ID`，保存完整 JSON。preview 必須核對所有 completion 與已登錄 staging 的完整 witness；已知拒絕、不支援布局、缺 witness 或任何身分歧義都停止。
2. 只有 `CONFIRMATION_REQUIRED` 才可向 Owner 展示列表、舊／新 binding、restart scope／generation、witness 摘要、未解項與信任模型剩餘風險。Owner 必須明示同意這個精確 preview；既有 restart 同意、一般備份 Prompt、沉默或「繼續」都不是同意。
3. 以同一 preview 與 v2 evidence bundle 執行 `reattest confirm --records-root RECORDS_ROOT --session-id SESSION_ID --preview @PREVIEW_JSON --evidence BUNDLE`。statement 記錄 Owner 實際同意與 preview digest；以 `command_stdout` asset 封存完整 preview，context 使用該 list_key。
4. 成功後先以 `scan start --recovery` 完成新的全量盤點，才按原 OPEN_BATCH 建立合格 v3 intent。confirm 前的舊 scan 不可沿用；轉接不解除 UNKNOWN／LOCAL_CHANGED、不改 completion 或批次 scope，也不授權 GUI。
5. 精確 replay 只查回同一事件，不新增 evidence 或 event，也不構成新同意。若目前 binding 再漂移，回報 `REATTEST_CURRENT_BINDING_CHANGED` 並停止；不建立第二筆轉接、不換目的地或入口繞過。

## 證據路徑與唯讀查詢

路徑範例以 Agent 確認後的專案實體根目錄為基底；下列變數只供 Agent 在當次私有任務區展開，不是要求 Owner 填寫：

```sh
TASK_PROJECT_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
TASK_PRIVATE_DIR="$TASK_PROJECT_ROOT/.local/line-backup/tasks/CURRENT_TASK"
STATEMENT_FILE="$TASK_PRIVATE_DIR/statement.txt"
SCREENSHOT_FILE="$TASK_PRIVATE_DIR/screenshot.png"
EVIDENCE_PARENT="$TASK_PRIVATE_DIR/evidence"
EVIDENCE_OUTPUT="$EVIDENCE_PARENT/NEW_UNIQUE_EVIDENCE_ID"
mkdir -p "$EVIDENCE_PARENT"

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
  --statement "$STATEMENT_FILE" \
  --asset screenshot "$SCREENSHOT_FILE" \
  --output-dir "$EVIDENCE_OUTPUT" \
  --list-key "$ABS_LIST_KEY"
```

`$STATEMENT_FILE`／`$SCREENSHOT_FILE` 必須已存在，且是不可經 symlink 或第二個 hard link 指到的專案內 regular file；Agent 只建立 `$EVIDENCE_PARENT`，不建立 `$EVIDENCE_OUTPUT`。`$ABS_LIST_KEY` 是新列表的 `list-key` 結果，不是顯示名稱或路徑。三種不同路徑拒絕不可混寫：

- statement／asset 傳相對路徑：`PROJECT_LOCAL_EVIDENCE_REQUIRED`。
- `--output-dir` 傳相對路徑：`NEW_EVIDENCE_DIRECTORY_REQUIRED`。
- output 的父目錄不存在：`EVIDENCE_OUTPUT_PARENT_REQUIRED`。

其他安全拒絕仍保留：輸入 symlink 為 `EVIDENCE_SYMLINK_REFUSED`，多於一個 hard link 為 `EVIDENCE_SOURCE_CHANGED`，輸出已存在為 `EVIDENCE_OUTPUT_DIRECTORY_EXISTS`，輸出逸出私有 tasks 為 `PROJECT_PRIVATE_EVIDENCE_REQUIRED`。不能用目前觀察反推第一筆歷史 argv 是輸入或 output 錯；舊 argv 未知就保留 `UNKNOWN`，不重跑同一失敗以補歸因。

若要保存單次 child 執行，改用 capture wrapper；它不是 GUI input：

```sh
CAPTURE_PARENT="$TASK_PRIVATE_DIR/captures"
mkdir -p "$CAPTURE_PARENT"
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes_capture \
  --output-root "$CAPTURE_PARENT" -- \
  summary --records-root "$ABS_LEDGER"
```

**本段只說明「欲刷新單一既有帳本摘要」時的 `summary --records-root` 查詢，不是 Pre-Bind 的前置或日常備份的停止條件。** `lists` 已包含全部帳本的摘要列；需要刷新已選帳本的摘要時，先用它唯一定位與當次入口、列表身分及歷史相符的帳本（通常不必再查），再將該列的 `records_root` 原值傳給 `summary`：

```sh
TASK_PROJECT_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
ABS_COLLECTION="$TASK_PROJECT_ROOT/notes-backup-records"
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes \
  lists --collection "$ABS_COLLECTION"

ABS_LEDGER="/ABS/PROJECT/Line_backup/notes-backup-records/UNIQUE_LOCAL_LIST_ID"
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes \
  summary --records-root "$ABS_LEDGER"
```

`ABS_LEDGER` 必須換成上一步結果中唯一相符列的完整 `records_root`；不得拿猜測路徑呼叫 `summary`，不要靠顯示名稱猜目錄，也不要把 collection 傳給 `summary` 或增加 `--local-list-id`。查無相符既有帳本（含零同名候選）不是日常備份的停止條件：應依下方[啟動與帳本對帳](#啟動與帳本對帳)完成全部 N 份候選核對，再走既有帳本 `bind`（Route A）或新列表自動 `init`（Route B）；只有真實多候選歧義、索引／歷史損壞或無法唯一定位（Route C）才停止。

`evidence-correct` 只用於已確認的 page 證據錯引。Agent 從目前帳本事件取得 page 的 sequence／SHA-256、原 evidence SHA-256 及替換 bundle；替換 bundle 的 scan context 必須對應 target page 當時的 scan，不是現在最新 scan。若 page 以外仍有 evidence 損壞，拒絕 `EVIDENCE_REPAIR_SCOPE_MISMATCH`；重複更正須帶前一筆 correction 的 sequence／SHA-256，不得分叉。成功只追加 correction，不修改 page 成員、順序、top/bottom、scan 覆蓋、media key 或已完成事實；真實帳本仍須 D2 的精確資料預覽與授權。

`media-kind-correct` 只處理最新完整 scan 中、尚無任何 intent／verification／completion／exclusion／protection 的已盤點媒體。來源 inventory 必須是最新且 context 相符；更正只新增 `media-kind-correction`，原 media key、貼文、數量、次序與 inventory 保留。`summary` 會同時顯示原始 `kind`、`effective_kind` 與 correction ref；新 `intent` 使用 `line-notes-intent/v2` 凍結 effective kind，後續 `verify` 選擇對應照片／影片驗證器。合法舊 v1 intent 保持可讀，但任何更正後才偽造的 v1 intent 會 fail closed；不手改 schema 或 events。

`media-kind-reconcile` 是下載後、驗證前的精確 attempt 補救路徑，不是新的下載或 restart。只有在 outcome 已為 `DOWNLOAD_FINISHED`、尚未有 verification／completion／publish plan／restart candidate、沒有 pending naming／open restart／本機變更，且 staging 恰有一個穩定 regular file 時才可追加 `media-kind-reconcile`。`from_kind` 必須等於該 intent 凍結的 effective kind；`to_kind` 必須與目前檔案 suffix 相容，而舊種類的 suffix 不相容；事件保存 intent／outcome ref 與檔案 inventory。它只新增觀察，不修改 intent、outcome、media key、post key、來源順序或舊事件。`verify` 對該 attempt 使用 reconciliation 的 `to_kind`，但 summary 保留 `effective_kind`，另列 `verification_kind` 與 reconciliation ref；因此不能把手改 JSON、改名或重下說成已完成。真實帳本必須先有能證明原分類其實錯誤的來源證據；單憑下載後看到 JPEG、縮圖或檔名不得自動改種類，影片只存到預覽影格時仍可能不是真正的 PHOTO。

`source-unavailable` 只在單一來源已明確到期、最新 attempt 為 `STOPPED`，且沒有完成／排除／保護／待命名交易時可用。成功只代表該項來源不可用：摘要顯示 `source_availability=EXPIRED`，`resume` 對該項列 `SOURCE_UNAVAILABLE`，不得再 `intent`；六類狀態與 scoped 的 `current_incomplete` 不改（定義見[結束對帳](#結束對帳)），也不能批次推論同列表其他項到期或自動排除。

## 掃描覆蓋與綁定 gate

`summary` 的 `scan_coverage`、`dispatch_blockers`、`unresolved_attempts` 與 `scan_binding_match` 是唯讀事實投影，不是下載許可。新 Session 先以 `summary` 找舊 attempt，核對當次入口／前景並成功 `bind` 後，才使用要求 Session 的交易命令；不能因為尚無綁定就沿用舊 Session ID。`has_outcome=false` 時依原 attempt 的真實證據先用 `outcome` 保存第一筆結果，證據不足可記 `UNKNOWN`，不得先 `reconcile`；已有 `outcome=UNKNOWN` 才以新證據 `reconcile`；`DOWNLOAD_FINISHED` 先 `download-check`，pending naming 先 `resume`。無新證據就保留原狀，不補造結果或重送。未隔離且無法安全處理的 attempt 仍阻止普通新 scan；安全隔離事件讀回後，才可由目前綁定 Session 開始普通完整 scan。只有完成精確 `restart confirm` 後，才可用 `scan start --recovery` 建立新的完整 recovery scan，再逐項 `intent --restart-id`；這不是用新 scan 掩蓋舊問題，也不改寫舊 attempt 的 scan binding。`bind` 若因未完成 scan、身分或證據等條件拒絕，停止並保留原狀，不重建空帳或以新 scan 掩蓋。

普通 `scan start` 會拒絕待命名交易、仍 open 的 scan，以及未隔離且無法安全處理的未解 attempt；已安全隔離的舊 attempt 從此派送護欄移除。隔離後的新 scan 仍須完成頂底／重疊與完整卡片覆蓋，且其 start sequence 必須晚於 isolation；v5 intent 也要求這份 scan 目前仍是最新完整 scan。`scan start --recovery` 只在 STOPPED／NOT_SENT 恢復或已確認 restart 批次的路徑使用，仍受 bind、Session、完整掃描與各自 gate 限制，不是通用解鎖。已完成項與正面 `STOPPED`／`NOT_SENT` 不會被重下；後者仍需原恢復授權與充分證據才可另建 attempt。普通 `intent` 要求最新完整 scan 的卡片覆蓋，以及目標貼文 detail、媒體數量／順序與目標 media 身分完整；安全隔離後同一媒體的 `intent` 會自動走 v5 並在這次 append 消耗一次額度。`dispatch_blockers` 中 `POST_DETAIL_PENDING`、`STALE_POST_DETAIL` 等局部貼文資訊不會自動阻止其他合格目標；`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 列未完成報告，但不是其他合格項的全域 blocker。列表覆蓋／身分不明、未隔離且無法安全處理的 attempt／UNKNOWN／no-outcome、活動下載、pending naming 或 `LOCAL_CHANGED` 等全局阻塞仍須停止新派送。摘要仍如實列出待盤貼文，`all_known_media_complete` 在全列表媒體細盤未完成或仍有待補下載／用盡項時保持 false。純文字貼文以 `NO_MEDIA` 表示，不可當成缺少媒體。

`scan_binding_match` 只表示是否符合最新 scan，不等於原下載無效。已 `DOWNLOAD_FINISHED` 的舊 attempt 先讀 `resume`：`VERIFY_REQUIRED` 以原 attempt 執行 `download-check`；已有 BASIC 命名交易則由 `resume` 接續。歷史來源可核對的 STOPPED／NOT_SENT 回 `RECOVERY_REVIEW_REQUIRED`，有額度時由 Agent 核對停止證據與當次盤點後恢復。CLI 核對 intent 當時的歷史 scan／post／media，不要求改綁最新 scan；原證據無法核對或已被 restart 取代時仍拒絕。`SCAN_BINDING_REVIEW_REQUIRED` 表示原始來源無法核對，保留資料並依影響範圍報告。不得改綁定、重寫舊 intent、開新 scan 覆蓋或另建 attempt 解鎖。

`--decoder`／`--decoder-sha256` 由呼叫端提供；CLI 只核對呼叫端提供的 SHA-256，並確認執行前後是同一個 binary、沒有內容漂移，不能證明該 binary 來自 repo 的 `src/line_backup_batch/image_decode.swift`。實作者仍須自行核對建置來源、路徑與版本；來源無法確認時停止，不得以 caller 提供的 hash 相符代替 provenance。

## 啟動與帳本對帳

`bind` 前（Pre-Bind）固定五步，不得跳步、調換或提前停止：

1. **完整 `lists` capture。** 以 `notes_capture --output-root "$CAPTURE_PARENT" -- lists --collection "$ABS_COLLECTION"` 取得完整無截斷的 `stdout.bin` 與 `status=COMPLETE` receipt；非零 exit、`incomplete.json` 或不可解析輸出保留原狀，不進入下一步。
2. **CUA 原件落地並讀回。** 須先於同一 CUA Node runtime 載入 `evidence-template.md` 的 `cua-evidence-tools` 定義區塊，再實跑 `evidenceTools.captureAndPersist`，把同次截圖與完整 AX 落地，再讀回顯示同一份 bytes；只看到對話介面圖片不算落地。未載入（`typeof evidenceTools === "undefined"` 或 `CUA_EVIDENCE_TOOLS_NOT_LOADED`）或未實跑 helper 屬 `NOT_RUN`，不得宣稱環境不支援。實作與讀回契約見 [CUA 觀察原件落地](evidence-template.md#cua-觀察原件落地)。
3. **入口確認與全部候選核對。** 以同次已落地讀回的截圖＋AX 確認列表角色與入口，展開全部 N 份候選，完成 `active_hint` 分流與多訊號交叉比對，依[三路列表判定契約](#候選帳本展開唯讀)得出三路之一的結果。
4. **封裝 v2 `evidence-pack`。** 新列表固定同一組 identity，先 `list-key` → `evidence-pack`（statement 明列全部 N 份排除依據，滿足 binding 與 history_scope）→ `init`（正式日常 Prompt 涵蓋恢復授權時加 `--recovery-authorized`）→ 讀回 `list_key`；既有列表沿用原 `list_key`，仍以同次落地原件封裝當次 observation／handoff bundle。
5. **`bind` → 舊交易 → 普通完整掃描。** `bind` 後先處理舊 attempt／命名交易與仍 open 的 scan，再 `scan start` 完成普通完整掃描；沒有未決項才直接進新 scan。

### 候選帳本展開（唯讀）

`lists` 每一列已是 `summary()` 的完整投影，含 `identity`、`scan_coverage`、`unresolved_attempts`、`dispatch_blockers` 與每篇 `posts` 的 `source_order`／`date_summary`／`media_count`／`state`／`identity`；不需對 N 份各跑一次 `summary`，也不得用只留少數頂層欄位的 wrapper 丟掉 `posts`／`identity` 再比對，亦不得撰寫只保留 `display_name == 畫面標題` 的過濾器（例如得到 `matches: []` 後即停止）。名稱只是線索；仍須展開全部 N 份候選的 `identity` 與 `posts` 錨點交叉核對。以 receipt 回傳的 `receipt_dir` 讀取 `stdout.bin`，不自行猜路徑；`status=COMPLETE` 才可展開。以下腳本只讀 JSON、不寫入，空 `lists`、空 `posts`、`active_hint=null`、`identity=null` 均照實輸出：

```sh
CAPTURE_PARENT="$TASK_PRIVATE_DIR/captures"
# 步驟 1 的 capture 已完成；UNIQUE_CAPTURE_ID 取自 receipt 的 receipt_dir 目錄名。
/usr/bin/python3 -B - "$CAPTURE_PARENT/UNIQUE_CAPTURE_ID/stdout.bin" <<'PY'
import json
import sys


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'))


def field(value):
    if value is None:
        return 'null'
    if isinstance(value, str):
        return value if value else 'EMPTY'
    return compact(value)


if len(sys.argv) != 2:
    print('usage: /usr/bin/python3 -B - CAPTURE/stdout.bin')
    raise SystemExit(2)

with open(sys.argv[1], 'rb') as handle:
    payload = json.load(handle)

rows = payload.get('lists') or []
if isinstance(rows, dict):
    rows = [rows[key] for key in sorted(rows)]

hint = payload.get('active_hint')
registered = None
if isinstance(hint, dict):
    hint_root = hint.get('records_root')
    hint_id = hint.get('local_list_id')
    if (isinstance(hint_root, str) and hint_root and
            isinstance(hint_id, str) and hint_id):
        for row in rows:
            if (isinstance(row, dict) and
                    row.get('records_root') == hint_root and
                    row.get('local_list_id') == hint_id):
                registered = hint_id
                break

if hint is None:
    print('active_hint: none')
elif registered is not None:
    print('active_hint: registered local_list_id=%s' % registered)
elif isinstance(hint, dict):
    print('active_hint: unregistered records_root=%s local_list_id=%s' % (
        field(hint.get('records_root')), field(hint.get('local_list_id'))))
else:
    print('active_hint: unregistered raw=%s' % compact(hint))

print('candidate_count=%d' % len(rows))
for index, row in enumerate(rows, 1):
    posts = row.get('posts') or []
    attempts = row.get('unresolved_attempts') or []
    blockers = row.get('dispatch_blockers') or []
    print('')
    print('[%d] local_list_id=%s' % (index, field(row.get('local_list_id'))))
    print('  records_root=%s' % field(row.get('records_root')))
    print('  list_key=%s' % field(row.get('list_key')))
    print('  display_name=%s' % field(row.get('display_name')))
    print('  context_id=%s' % field(row.get('context_id')))
    print('  identity=%s' % compact(row.get('identity')))
    print('  scan_coverage=%s post_count=%d unresolved_attempts=%d' % (
        field(row.get('scan_coverage')), len(posts), len(attempts)))
    print('  dispatch_blockers=%s' % compact(blockers))
    if not posts:
        print('  posts=EMPTY')
        continue
    for order, post in enumerate(posts[:5], 1):
        print('  post[%d] source_order=%s date_summary=%s media_count=%s '
              'state=%s identity=%s' % (
                  order, field(post.get('source_order')),
                  field(post.get('date_summary')),
                  field(post.get('media_count')), field(post.get('state')),
                  compact(post.get('identity'))))
    if len(posts) > 5:
        print('  posts_shown=5 post_count=%d' % len(posts))
PY
```

**`active_hint` 分流。** 腳本以 `active_hint: registered`／`unregistered`／`none` 表示命中狀態。`active_hint` 的 `records_root` 與 `local_list_id` 同時精確命中 `lists` 內某筆已註冊帳本時，只表示前次曾操作該帳本（切換至其他列表的日常常態）；核對確認它不是當次目標後即完成分流，**不構成缺損歷史阻塞**，也不得因此改綁他帳本。只有 `active_hint` 指向未出現在 `lists` 的 `records_root`／`local_list_id`，或 `lists`／索引／帳本讀取被拒絕時，才視為潛在歷史缺損阻塞，停止 `init`／`bind` 並回報。

**前景目標與 `display_name` 對稱規則。** Owner 交接的有效 LINE 記事本前景即為本次目標，不需先在 `lists` 找到同名帳本才可備份；`display_name`／中文標題只作線索，**同名或不同名皆不能單獨決定 `bind`、`init` 或停止**。「**零同名候選**」（`display_name` 完全相符為 0，例如過濾後得到 `matches: []`）只是尚未完成核對的中間觀察，不等於身分不符、候選歧義或停止理由，也不等於自動認定新列表，仍須完成全部 N 份 `identity`／`posts` 交叉核對；只有完成全核對後仍有真實身分衝突，才是 **Route C** 阻塞。

**三路列表判定契約**（不要求 Owner 填 UUID／key／JSON）：

- **A 唯一既有帳本匹配：** 恰有一份候選在當次入口與視窗脈絡、`identity`／`context_id`／signals、首屏多張可見卡片錨點（卡片順序／日期／摘要脈絡／媒體縮圖排列與數量）上交叉吻合，其餘 N−1 份均有具體差異可正面排除 → 封裝當次 observation／handoff 後 `bind`；既有帳本沿用原 `list_key`，不重新 `init`。即使該帳本 `display_name` 與目前畫面標題不同，只要上述多訊號唯一交叉吻合且其餘 N−1 份可正面排除，仍綁定原帳本。
- **B 證明新列表：** `lists` exit 0、全部 N 份已註冊帳本均逐一核對並以具體差異正面排除（不重疊的頁首脈絡＋`posts`／`identity` 歷史），且 `active_hint` 已核對、無未註冊／損壞歷史 → 以當次已落地多訊號建立 `visual_key`／`context_id`／`signals`（AX 標題空白時明記 `ax_window_title=EMPTY`），依序 `list-key` → `evidence-pack`（statement 明列全部 N 份已核對帳本的排除依據，滿足 binding 與 history_scope）→ `init`（正式日常 Prompt 涵蓋恢復授權時加 `--recovery-authorized`）→ 讀回 `list_key` → `bind`。
- **C 真實候選歧義或歷史缺口：** 完成全部 N 份交叉比對（含相近候選的 `posts`／`identity`／既有事件 `statement`）後，仍有 `>= 2` 份無法區分、有空／過舊候選無法排除為目前列表，或有未註冊 `active_hint`／索引異常 → 停在 `init`／`bind` 前，零帳本寫入、零下載輸入，保留已落地原件與 `lists` capture receipt，向 Owner 回報去識別化衝突摘要與單一具體釐清動作。**Blocker 證據契約：** 停止回報必須指出具體未成立的身分證據、衝突候選之去識別化 ID 與 `identity`／`posts` 差異，或實跑 CLI／helper 之 exit code／`error`／`stages`／`blockers`；不得以抽象的「找不到同名帳本」「名稱不符」或「`typeof evidenceTools === "undefined"`」要求 Owner 重新交接。

**未執行與真實失敗。** `NOT_RUN` 只表示該步沒有實際執行，不證明 CLI、helper 或環境不支援；不得把未執行寫成失敗，也不得改走替代入口後宣稱原路徑不可用。僅測得 `typeof evidenceTools === "undefined"`（尚未載入 `cua-evidence-tools` 定義區塊）不是 helper 失敗，須先載入再實跑。真實 CLI／helper 失敗必須附實際 exit code、JSON、`error`（`name`／`code`／`message`）、`stages` 或 `blockers`，才可列為環境／路徑阻塞。Pre-Bind 阻塞回報同受上述 Blocker 證據契約約束，不得以「找不到同名帳本」「名稱不符」或未載入 helper 要求 Owner 重新交接。CUA 工具 namespace 中途撤除只記工具可用性變動並停止，不以對話摘要重建原件。

以下各點為上述步驟的判準與例外：

**完整 capture。** 以本節前述既有 `notes_capture` 用法執行並保存一次 `lists` 的完整 request、stdout、stderr、exit code 與 capture receipt；先確認 exit 0 且輸出完整可解析，不能以截斷畫面、`head` 或不完整摘要當成全部結果。

為每一個候選列出內部短表，保留可用的 `local_list_id`、`records_root`、`list_key`、identity／context、覆蓋、六類計數、未決交易及 blockers 等辨識資訊，再讀 `.local/line-backup/active-notes-task.json` 作定位提示。hint 的 root＋ID 必須分別精確對應候選列的 `records_root` 與 `local_list_id`，仍須以本次連續入口及當次畫面核對列表身分與 context；hint 缺席或不符時保留並核對全部候選，不能因此推論新列表或建立空帳。

沒有相符既有帳本本身不代表帳本為空；只有完整查閱並核對全部歷史候選、未見缺損或歧義，且具備步驟 3 與步驟 4 所述完整、無歧義的新列表證據時，才走既有新列表 `init` 流程。當次來源無法唯一對應歷史候選且也不符合新列表條件，或發現輸出不完整／不可解析、索引／歷史異常時，停止相關寫入與新派送並回報具體缺口。

只有確需刷新已選帳本摘要時，才以其原值 `records_root` 序列 capture 一次 `summary`；不為同一 lock domain 平行查 `memory`，也不沿用 hint 中的舊 Session ID 作當次 `bind`。

**摘要核對。** 使用已取得的摘要核對列表、貼文／媒體狀態、缺項、`unresolved_attempts`、`dispatch_blockers`、scan binding 與本機可用性；需要 staging 目的地或 completion 細節時，依上節回到 `intent`／`download-check` 結果及追加事件。索引缺失、帳本損壞、證據鏈異常，或仍有多個可能對應當次列表的歷史候選而無法消除歧義時，停止相關動作，不建立新空帳。

**新列表鏈。** 新列表只有在入口、列表身分與歷史均確認，且沒有缺損／歧義時才建立。Agent 固定同一組 `visual_key`、適用 `context_id` 與 signals 輸入，以 `list-key` 取得 key；若同一完整觀察涵蓋 init 所需的 binding 與 history 命題，且 context 相同，可共用一份 v2 bundle；命題或 context 不同才分開建立。再以完全相同的 identity 參數執行 `init`，最後讀回相同 `list_key`。鏈如下；`CONTEXT_ID` 不適用時整項省略，不是空字串或 `UNKNOWN`，SIGNALS 未使用時同樣省略：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes list-key \
  --visual-key "$VISUAL_KEY" --context-id "$CONTEXT_ID" --signals "$SIGNALS_INPUT"

# 同一完整觀察可同時支持 binding 與 history 時，只封裝一次。
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
  --statement "$INIT_STATEMENT" --asset screenshot "$INIT_SCREENSHOT" \
  --output-dir "$INIT_EVIDENCE_NEW_DIR" --list-key "$LIST_KEY"
BINDING_BUNDLE="$INIT_BUNDLE"
HISTORY_BUNDLE="$INIT_BUNDLE"
# 若兩項命題需要不同原件或 context，才分別建立 bundle 並設定以上兩個變數。

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes init \
  --collection "$ABS_COLLECTION" --photo-root "$ABS_PHOTO_ROOT" \
  --name "$DISPLAY_NAME" --visual-key "$VISUAL_KEY" \
  --context-id "$CONTEXT_ID" --signals "$SIGNALS_INPUT" \
  --binding-evidence "$BINDING_BUNDLE" \
  --history-scope-evidence "$HISTORY_BUNDLE"

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes summary \
  --records-root "$ABS_LEDGER"
```

`SIGNALS_INPUT` 是明示的 strict JSON 文字或 `@` 加指定 JSON 檔的絕對路徑；未使用 signals 時連同整個 flag 省略。當次任務已授權確認停止後的恢復時，在真正新建帳本的 `init` 命令加上 `--recovery-authorized`，並從回傳／摘要讀回 `recovery_authorized=true`；未獲授權不得加此 flag。既有帳本不重新 init，也不手改 false 的授權值。先核對所用 bundle 的 context 等於 list-key 結果，再執行 `init`；若 identity 輸入、觀察命題或明示 signals 檔在期間改變，舊 bundle 不可沿用。`init` 後只使用其回傳的 `records_root` 讀回 key，不一致或有未預期副作用就停止；不得先建空帳取得 key、手填 key／JSON，或讓適用 ID 留 `UNKNOWN`。新列表讀回成功、或既有列表從 `lists`／`memory` 找到相符帳本後，先核對當次入口與有效前景，再依序 **`bind` → 處理舊 attempt／命名交易 → `scan start`**；沒有未決項才直接進新 scan。每一命令仍須滿足自己的 scan binding／資料完整性 gate，不能因已 bind 就視為舊 attempt 已獲重送或恢復許可。不因新 Session、照片 root 改變或使用者重交前景而重新初始化。

**完整掃描。** `scan start` → `page`… → `scan finish` → `post`／`media` 保存本輪完整盤點。`scan finish` 前必須已看到頂端、底端與有序重疊；`post`／`media` 需要最新完成的 scan。新 Session 必須重新看頂底與重疊，不沿用上一個 Session 的畫面 cursor。純文字貼文由 `post` 記 `NO_MEDIA`，不建立媒體下載項。

**目的地。** 重新更換照片 root 時用 `destination` 追加綁定；舊 completion 路徑不改，UNKNOWN、活動下載、pending 命名或 `LOCAL_CHANGED` 不因換位置解鎖。

## 一次一項的派送交易

每次只處理一個已核對的貼文／媒體 attempt，不得平行下載多項。固定順序如下：

1. **intent 前預檢。** 從 `memory`／本次 scan 確認該項不是 `COMPLETED`、`EXCLUDED` 或不可跳過的 `PROTECTED_HISTORY`；`PREVIOUSLY_INCOMPLETE` 先走恢復判斷，已有 outcome 的 `UNKNOWN` 先 `reconcile`。未安全隔離的舊 `UNKNOWN`、舊無 outcome／crash window、活動下載、未解輸入與 pending naming 不得由普通流程重進；只有安全隔離讀回且完成其後新完整 scan／細盤的同媒體項目，才可交給自動 v5 intent。建立 attempt 前依 [B1](gui-inventory.md#目標與下載控制就緒b1) 核對同一列表、貼文、媒體、viewer、有效前景與三層身分：最新控制正面可定位時，可通過直接路徑的 intent 前 gate，實際定位仍須在 intent 後重取；工具列隱藏時，只有同一 viewer／選中項的當次安全 reveal 方法、ordinal／前次引用／新證據條件及完整可核對的 `0`／`1` 額度均成立，才可建立 intent。無方法、無可用候選、額度不明或未決時停在 intent 前，不得先 hover／click，也不得預建未派送的候選或 input request。另解析帳本、照片 root、CLI、私有 task／證據父目錄、statement、fixed reveal／download slot 的命名推導與精確 `intent` argv／讀回欄位；不要預建 intent staging、猜 key 或先寫事件。
2. **建立並讀回 intent。** B1 gate 成立後，用已備妥 argv 執行一次 `intent`；intent 前不送 reveal，也不插入固定等待或為了預測穩定而先做額外 GUI 輸入。CLI 會保存 attempt、新空白暫存目錄與「可能已派送、禁止重送」紀錄；讀回 JSON 中的 `attempt_id`、`destination`、`save_all_limit` 與 `save_all_count`，並在私有任務區保存這次預檢、B1 方法／額度分支與讀回證據。成功 intent 會帶 `status=UNKNOWN`，那是**派送前初始狀態**，不表示已點擊或下載。`save_all_limit=1`／`save_all_count=0` 只是 intent 建立時的 ledger 約束與初始值，不是 GUI 點擊或 reveal 計數。CLI／讀回失敗、衝突或前景中斷時零 GUI 輸入；intent 讀回後不得再回到 intent 前 discovery、另建 attempt 或換 Session，只能依 B1 走本 attempt 的直接或單次 reveal 路徑。
3. **intent 後最新觀察與單一路徑。** 在任何 GUI 輸入前取得一次最新的同一 app AX／截圖原件，重新核對有效前景、同一列表／貼文／媒體／viewer、返回控制、Agent 播放輸入 `NONE`、來源播放狀態已依 [B1](gui-inventory.md#目標與下載控制就緒b1) 正面記錄且無漂移、無 chooser／活動下載／未解輸入，以及 intent 讀回的 `post_key`、`media_key`、原目的地與 staging。控制可見且歸屬、啟用、映射成立時，走直接路徑，以這份原件準備下載，不再 reveal。控制未見時，只有 intent 前已稽核的當次安全方法仍成立、ordinal／prior refs／新證據條件與 `budget_before` 為 `0`／`1` 仍成立、本 attempt 尚無下載控制呼叫或 outcome，且方法安全區／選取可重新歸屬時，才可在同一 attempt 使用一次 reveal：固定 slot 為 `notes-reveal-c2-<attempt_id>`，`c2` 字面固定，真實 `candidate_ordinal` 寫在 request；由 `persistRevealWithDirectAfter` 內的 `persistSingleInput` 以 `wx` 建立 request、逐 bytes 讀回，再送一次當次工具支持的 hover 或 selected-filmstrip `NAVIGATION`，同一次 callback 取得並保存 after。方法、額度、歸屬、前景或連續性任一不足就停在輸入前；不得返回、reopen、換 viewer、再 capture 找 control 或用舊點位。
4. **同次正面 after 與下載控制至多一次。** 直接路徑只使用 intent 後最新的當次原件；reveal 路徑只使用同一次 invocation 剛保存的 after，不得重取、補拍或混用舊 after。Agent 在該份原件正面確認控制可見、歸屬、啟用、映射、viewer、三層身分、前景、Agent 播放輸入 `NONE`、來源播放狀態已依 [B1](gui-inventory.md#目標與下載控制就緒b1) 正面記錄及無漂移；全部成立才組出 request，連同該份原件與 live handle 交既有 `persistGroundedDownloadClick` 一次；由 helper 以 `wx` 獨占建立並逐 bytes 讀回本 attempt 唯一固定 slot `notes-download-<attempt_id>`，讀回成功後才依 target 呼叫。slot 已存在、並行競爭、欄位缺失、讀回不符或任一 gate 不足時零下載輸入；Agent 不得先手動建立或寫入該固定檔。helper 只驗證 request、保存 request／raw 與 diagnostic，並依持久讀回的 `candidate_point`（與 `prepared_target` 相同）呼叫一次 `app.click([x, y])`；`control_region` 只是送出前篩選，不是 native hit-test，也不提供 native receipt。從選定來源至 download call 之間不再 capture、執行 CLI、插入固定等待或旁支工作；下載呼叫後仍照本節步驟 5 觀察 chooser／結果。Agent 判讀需要模型時間，不能承諾時效。每個 attempt 的實際下載控制呼叫上限是一；失敗、逾時、`undefined`、結果不明或 chooser 出現都算已開始，且立即關閉本 attempt 的 reveal 與後續控制，不得重開 viewer 或改入口再點。
5. **chooser 觀察與至多一次確認。** 下載控制呼叫與 chooser 最終確認是兩個獨立計數。chooser 可能延遲出現；只有視窗／process、來源 viewer 與 attempt 能唯一歸屬時，才輸入此 attempt 的新空白暫存絕對路徑並讀回。Go to Folder 的預填值只證明 PathTextField 內容，不是 panel current directory，也不是 intent staging；三者要分開觀察。只有 PathTextField、where／current directory 與本 attempt 的 intent destination 能一致指向該 intent 已建立、讀回且仍空白的原目的地，且來源貼文可歸屬時，才可確認至多一次。出處不明、三者任一 `UNKNOWN`／不符或確認結果未知時不得確認，也不得用第二次確認、猜 Return 或重派恢復。出現 chooser 只證明 App 有階段性回應，不是下載完成；chooser 之後不得再進 reveal。
6. **記錄第一筆 outcome。** 先確認該 attempt 是否已有 outcome 事件，不從 `memory` 顯示的 `UNKNOWN` 猜測。沒有 outcome 時只執行一次 `outcome`，依第一筆真實結果記錄；若只有逾時、畫面未變、進度未終止、chooser／檔案的歸屬不足或其他不確定訊號，就記 `UNKNOWN`，不得改寫成 `NOT_SENT`／`STOPPED`，也不得先呼叫 `reconcile`。已有 `outcome=UNKNOWN` 時，才可以在取得新證據後使用 `reconcile`；不得再做第二次 `outcome`。
7. **未收斂的安全隔離。** 結果未達可進入基本檢查的正面終結前，不得 `download-check`、legacy `verify`、建立新 intent、重下或派送下一項。先以有限 AX／截圖核對舊目標；只有本文件的安全前提成立時，才可追加 `attempt-isolation`。隔離零消耗、不建立 scan／新 attempt；依 `next_action`／`attempt_phase`，只有普通 intent 總額未滿三筆且 v5 未使用時才進 `RECOVERY_SCAN_REQUIRED` 並允許新普通完整 scan、細盤及一次 v5 intent。普通總額已滿或 v5 已用時隔離仍可保留原結果，但回報 `RECOVERY_EXHAUSTED`，不得建立新 v5。補下載再 `UNKNOWN` 且安全時，可再隔離成 `RECOVERY_EXHAUSTED`，該項留欠件，其他合格項可繼續；不安全就停止依賴該前提的全域派送。晚到結果只能先歸回原 attempt 並調和，不能算成下一項或轉正成新 completion。每個媒體普通 intent 跨 Session 總額最多三筆（首次加最多兩次恢復），UNKNOWN v5 最多一筆；使用永久 attempt 歷史計數，重開、重掃、結果轉換不退額。每次重試須有支持下一步的新證據；同一根因最多三次有證據查證，連續兩次沒有新資訊即停止相同方法，不換入口繞過。只有可歸屬且足以排除原操作稍後繼續的明確停止／未派送證據，才可能進 `STOPPED`／`NOT_SENT`；隔離不提供此證明。若安全前提不成立且構成全域阻塞，保留具體原因與進度並停止依賴該前提的派送，不引導 Owner 診斷或核准 restart；僅單項欠件時繼續其他合格項。
8. **日常基本檢查與完成。** 只有具備可歸屬的下載終結結果及穩定結果檔，才可記 `DOWNLOAD_FINISHED` 並執行 `download-check`。明確的 `text/plain`、`text/html`、`application/pdf`、`application/zip` MIME 追加 `line-notes-download-exclusion/v1` 並保留 staging，不寫 completion，也不宣稱來源原件不是媒體；未知 MIME、`application/octet-stream` 或 MIME／suffix 不相符時保持 pending 並拒絕。其他檔案只有通過 MIME／suffix 分類、非空穩定、SHA-256、防覆寫與身分核對後，才追加 `DOWNLOAD_ONLY` completion 並讀回。任何檢查或紀錄失敗時保留原檔，不重新下載補帳。完整解碼僅屬 legacy `verify` 相容流程。
9. **命名中斷。** 只要來源、暫名、目標及 journal 可唯一核對，執行 `resume` 接續同一交易；`resume` 不得觸發下載。歷史 device-only 差異不單獨阻擋原發布，但仍核對交易 inode、時間、size／hash、當下 same-device 與 link count。既有 target 必須能證明屬於該交易；未歸屬目標、非預期額外檔、symlink、內容／交易身分不符或來源與目標歧義時，保護原檔並停止，不用手動改名解鎖。

每個 GUI 控制／chooser 操作當下保存定位觀察與工具原始回傳；原件不可事後重建。intent 仍須先保存並讀回。需要寫入有 evidence 參數的事件前，才依 [證據範本](evidence-template.md) 整理 statement，將同一 attempt、同一 context 適用的原件一併封裝並傳入 CLI 回傳的 `bundle_path`；若新事件需要新的事實或 context，另建 bundle。`intent` 沒有一般 evidence 參數，其預檢與讀回證據留在私有任務區，不能冒充 CLI 欄位。同一 attempt 可多次 reconcile；每次完成後都要追加該次 sequence／event SHA-256 與結果引用，保留全部歷史，不以最後一筆覆寫。bundle 只證明指定 bytes 與 context 一致，不解析 statement 的語意真假；缺少必要值時寫 `UNKNOWN`，不可由檔名、猜測或另一個來源補值。

### Reveal 前置、固定 slot 與永久證據

Reveal 的當次方法、安全區、intent 前隱藏分支、ordinal／前次引用／新證據／budget、intent 後直接或單次 reveal、同次 after 與停止只依 [B1](gui-inventory.md#目標與下載控制就緒b1)；本節只記交易與永久證據。每個 `list_key + post_key + media_key` 最多兩次已派送 reveal 候選，跨 viewer、reopen、Session 與 restart 累計；每個 attempt 最多一次 intent 後 reveal。click 只可用已選 filmstrip 的非播放安全邊緣 `NAVIGATION`，文件支持的 hover 則用它自身的可歸屬安全區與映射，不要求 filmstrip。工具列隱藏時必須在 intent 前先完成安全方法、ordinal／前次引用／新證據與額度稽核，不得先送 reveal；控制直接可見則走直接路徑，不需 reveal。無方法、無可用候選、額度已用盡／不明或未決時停在該 gate 前。

每個 attempt 的 canonical slots 固定為 reveal 的 `notes-reveal-c2-<attempt_id>` 與下載的 `notes-download-<attempt_id>`。reveal 的 `c2` 是固定檔名字面，真實 `candidate_ordinal` 只能寫在 request，不能用 ordinal 改名或另建 slot；兩者都使用同一 attempt 的 `taskDir`／`inputDir` 與既有介面。request 由對應 helper 以 `wx` 建立並逐 bytes 讀回，包含 `input_phase=NAVIGATION`、`attempt_id`、原 event 的 sequence／SHA 引用、scope／candidate／prior refs、ordinal／budget、before、選取、安全區／映射及既有 `fail_closed`／`afterObservation` 回傳。slot 已存在、並行競爭、讀回失敗或不符時零 input；不得換 operationId、taskDir、Session、目錄或 ordinal 重開。`intent_event_ref` 不是 CLI 原生欄位，須由該 attempt 的唯讀事件 `sequence`／`event_sha256` 建立並與 request 一同讀回。

Intent 後先取最新的同一 viewer 原件：控制正面可見就走直接路徑；控制未見且 B1 隱藏分支仍成立，才以固定 reveal slot 送一次 input，並在同一 `persistRevealWithDirectAfter` callback 取得 after。before 截圖／AX、input receipt、after 截圖／AX 各自保存 bytes／hash；相同 AX 可以重複引用，但不同畫面各自保留。slot 已存在或 request 寫入／讀回失敗時，helper 不會送出本次輸入，保留原紀錄並停止。已開始送出的輸入即耗額；input error／timeout、after error／缺證、crash 或 `fail_closed=true` 一律停止，不重拍、重送或交給下載 helper。

`TOOLBAR_VISIBLE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT` 是控制可見性的 statement 結論，不是業務狀態或 outcome；舊 `UNKNOWN`、舊無 outcome crash window、新 Session、reopen 與 restart 都不重置本 scope 額度。`TOOLBAR_VISIBLE` 支持當次直接定位；`TOOLBAR_NOT_SHOWN` 只表示 bounded observation 未見；`REVEAL_TRANSIENT` 只描述曾見後又消失。隱藏分支只有在 B1 的方法與額度完整成立時才可進 intent；控制缺席本身不是 `NOT_SENT`、失敗或完成證明。既有 `STOPPED`／`NOT_SENT` 精確恢復與 restart 規則不變。

這些原件仍只用既有 v2 roles；本方案無需新增 `navigation_receipt`、schema、CLI 或 GUI sensor。`evidence-pack` 只寫私有 bundle，必須經既有 event 的 evidence 參數保存並讀回才算進永久帳本。合法順序只有：

- 新 scan 的 `post`／`media` 細盤只以該事件當時的盤點原件建立 v2 bundle，傳入該次 `--evidence`。事件 context 是 `list_key + post_key + scan_id`，`media_key` 僅記在 statement。先保存細盤才建立 intent。不要為補證據另用 `page`、`scan`、`bind` 或 `protect`；`intent` 沒有一般 evidence 參數。
- 同 scan 的 `post`／`media` 各只能寫一次。B1 前置阻塞的原件留私有 task 區，明列「永久帳本未保存」。同一個實際 attempt 有合法 outcome 時，才能把它的直接定位或 reveal／after 原件依該 attempt 的精確 context 封裝。不能把沒有 attempt context 的舊 bundle 當成新 attempt 或另一畫面的證據。若沒有既有事件可以附掛，保留私有原件與 hash，不另開 scan 或寫入事件。

## 恢復與不可解鎖狀態

| 既有狀態／證據 | 下一步 |
|---|---|
| `COMPLETED` 且本地完整，或整篇目錄已 `LOCAL_MISSING` | 保留完成並跳過；`LOCAL_MISSING` 回報本機不可用，不重下、不證明外部副本 |
| 完成目錄仍存在但缺檔、非屬合格環境附屬項的額外檔、hash／身分漂移或 symlink | `LOCAL_CHANGED`：保護原件。scope 外停止新派送；只有 `restart preview` 精確列出且 Owner 確認該 scope 時，才可在新 generation 重建，不重下補帳或覆寫舊目錄 |
| 已 `DOWNLOAD_FINISHED`、尚未 completion | 日常執行 `download-check`；若命名交易 pending 則 `resume`，不重下 |
| 命名／發布交易中斷 | `resume` 同一交易；不得重送下載 |
| intent 尚無 outcome | 先以原事件、目的地與當次畫面／檔案查證，再用 `outcome` 保存第一筆真實結果；證據不足可記 `UNKNOWN`，不得先 `reconcile`。未寫第一筆結果前不得 `download-check`、legacy `verify`、建立新 intent、重下或派下一項 |
| 已有持久 `outcome=UNKNOWN`，且同一媒體的安全隔離、有效前景、原目的地、符合隔離條件的舊 staging、無 chooser／活動下載／pending naming／檔案異常／手動 restart 均成立 | 先做一次有限查證。有新結果證據時才用 `reconcile`。結果仍不明時，以當次有限 AX／截圖核對舊目標，追加 `attempt-isolation`。隔離零消耗、不建立 scan／新 attempt、不宣稱停止；只有普通 intent 總額未滿三筆且 v5 未用時，才投影 `RECOVERY_SCAN_REQUIRED` 並由目前綁定 Session 完成隔離後才開始的普通完整 scan 與細盤，再建立一次 v5 intent。普通總額已滿或 v5 已用時投影 `RECOVERY_EXHAUSTED`，保留欠件，不建立新 v5 |
| `REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` | 兩者都列未完成，不計完成，也不當其他合格項的全域阻擋。前者先完成合格新 scan，再以 v5 intent 消耗一次額度；後者表示適用額度已用盡，保留欠件；同一 media key 普通 intent 不得超過三筆，UNKNOWN v5 不得超過一筆。舊 staging 可為空或含符合本工具隔離檢查的單一穩定普通媒體檔；晚到檔不發布、不清理、不合併 |
| 未隔離或無法安全處理的 `UNKNOWN`／no-outcome | 保留原結果，停止相同查證、重送、新 intent 與下一項；這是全域 blocker。只有另外取得 fresh `restart preview` 精確 scope、Owner 明示確認該批並完成 confirm 後 recovery scan，才可走 `intent --restart-id`；舊史保留，不偽造 STOPPED。confirm 後同一批次任何新增 v3 attempt 尚無 outcome 或結果 `UNKNOWN`（包括後來被 supersede 的舊版），不得再建立新 intent 或 activation；若 latest-only `reconcile` 無法處理已被 supersede 的舊版，保留證據、回報具體資料阻塞，不擴寫更正入口 |
| `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH` | Agent 出示精確 scope 並取得 Owner 明示同意後 `restart confirm`；confirm 後必做新的完整 recovery scan，才可逐項 `intent --restart-id`。每項下載仍最多一次；日常用 `restart resume --download-only` 檢查 candidate。`open_restart.scope_unresolved_attempts` 非空時停止新 restart intent／activation，先查原 attempt；scope 內有明確非媒體就回報 `RESTART_SCOPE_NON_MEDIA` 並停止，不自動改 scope。scope／身分／目的地改變要重新確認 |
| `source_availability=EXPIRED` | 該項保留原欠件並停止 recovery／intent；`resume` 只列 `SOURCE_UNAVAILABLE`，不自動排除、不計完成、不宣稱服務端已回收 |
| `scan_binding_match=false` | 先讀 `resume`：已下載且原始證據有效者回 `VERIFY_REQUIRED`，用原 attempt 執行 `download-check`；BASIC 命名交易接續原發布。若回 `SCAN_BINDING_REVIEW_REQUIRED`，保留資料並報告無法核對的原始來源；STOPPED／NOT_SENT 只在原來源可核對時走有界恢復 |
| 明確 `STOPPED` 或 `NOT_SENT`、原檔保留、帳本已有持久化 `recovery_authorized=true`、當次正式 Prompt 明示涵蓋此次恢復、前景有效，且有充分停止證據 | 保存並讀回證據，以 `intent --recovery-evidence` 綁定前次 attempt，由 CLI 建立另一個新空白恢復目錄；evidence bundle 的 context 沿用舊 prior 的 `list_key`、`post_key`、`media_key`、`attempt_id`、`scan_id`，statement 引用原停止事件及本次新完整掃描、目標細盤與有效前景；新 intent 本身綁目前完整 scan。已完成項跳過。`true` 不能代替當次正式 Prompt 授權；授權未持久化／`false`、證據不足或前項不是終止狀態時停止，不手動建目錄、不改寫或繞過 ledger。舊 staging（即使為空目錄）原樣保留；此路徑不要求舊 staging 為空（空目錄／單檔隔離條件只屬 UNKNOWN v5） |
| `PREVIOUSLY_INCOMPLETE` | 依原授權走上述恢復判斷，不當普通待下載直接派送 |
| `PROTECTED_HISTORY` | 保留來源與缺項；只有完整盤點、無列表級歧義且不是活動／UNKNOWN／pending 時才可跳過該項，不計完成或排除 |

恢復只重做原授權範圍內未完成的項目，不重跑已完成清單。原本的暫存、部分下載、證據與日誌全部保留；新 attempt 不可覆寫舊目錄或舊事件。舊 `STOPPED` staging（即使為空目錄）一律原樣保留，不清理、不刪除、不合併、不發布；目前為空不代表未來不會晚到，回報須保留殘留晚到檔風險註記。成功發布後新 recovery staging 不存在屬正常行為，不是 `LOCAL_CHANGED`，也不證明完成檔異常。`STOPPED`／`NOT_SENT` 的 v2 recovery 與精確 restart 批次是兩條不同路徑：前者需要已持久化 `recovery_authorized=true`、正式 Prompt 的原任務授權涵蓋恢復及充分停止證據；同媒體普通 intent 總額最多三筆，含最多一筆 v5，因此符合原 gate 的 `STOPPED`／`NOT_SENT` 恢復可使用第三筆普通 intent；後者需要 fresh preview、Owner 對精確 scope 的明示確認及 confirm 後新 scan，不需要也不得把 `recovery_authorized` 當成批次同意。若UNKNOWN 無法安全隔離或工具缺少安全調和能力時，保留具體全域阻塞與進度並停止依賴該前提的派送；不要求 Owner 診斷或核准 restart；只有安全隔離後仍有 v5 額度的項目待補下載；用盡額度的單項列欠件並允許其他合格項繼續。舊 `recovery_authorized=true` 不能代替當次正式 Prompt，`false` 保留，不由單次 UNKNOWN 路徑改寫或繞過。

`expected_tip` 是 restart preview／confirm 與 `isolate` 的 ledger chain baseline 核對值，物件為 `sequence + sha256`；不是新的 event／evidence schema，也不是同意或 GUI 授權。`summary` 的 `expected_tip` 代表讀取當下最新事件鏈頭；舊 `summary` 快照（較低 `sequence`，如 bind 後快照）只供歷史對照，不得充當現行 blockers、現行 `unresolved_attempts` 或 fencing 基準。

現行 CLI 只在 `init --recovery-authorized` 時把 v2 `STOPPED`／`NOT_SENT` 恢復授權持久化到列表帳本；沒有事後修改該授權的子命令。`recovery_authorized=true` 只是舊恢復路徑的持久資格，不能代替當次正式 Prompt 的明示允許、有效前景或 GUI grant；`false` 保留，不得改寫，也不得把它當成可由一次 UNKNOWN 隔離或 v5 補下載解除。既有列表若 `memory` 顯示未授權，停止舊 `STOPPED`／`NOT_SENT` 恢復路徑並列明阻塞，不直接編輯 `list.json`、事件或另造空帳。`restart` 批次另有 confirmation evidence 與 scope gate，不能以缺少此 flag 為理由繞過，也不能把 flag 當成 Owner 同意。

## 新媒體、重排與跨列表

- 再次執行時先 `bind`，一般情境再以新 `scan start` 對帳，不重用上輪 cursor；若走已確認 restart 批次，則 confirm 後先明確中斷尚未結束的 scan，再以 `scan start --recovery` 重新盤點。貼文重排只更新 `source_order`，舊完成檔名不動；新媒體只補唯一可辨識者，編號取該貼文目前最大值加一。
- 貼文文字被編輯不重下舊媒體；只保存新的索引差異。若新舊媒體對應無法唯一證明，保護該篇，其他已核對篇可繼續。
- 相同日期、標題、總數、媒體 hash 或外觀不能跨列表合併；每個 `local_list_id` 分開，跨帳本寫入一律拒絕。
- `init` 建立空帳只適用真正新列表；`destination`、重掃、刪除照片、清空暫存或改索引都不能把 UNKNOWN／pending 解鎖。

## 結束對帳

每完成一項立即保存並讀回，不把整批成功留到最後才寫。最終執行 `summary`，再以當次列表／貼文畫面核對：

- 貼文總數、`NO_MEDIA` 篇數、六類媒體狀態及未解缺項。
- `COMPLETED` 的檔案驗證與 completion 讀回；`LOCAL_MISSING`／`LOCAL_CHANGED` 分開列示。
- 是否有活動下載、未隔離或無法安全處理的 UNKNOWN／no-outcome、`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED`、未完成命名交易、先前未完成或不可跳過的受保護歷史；後兩類 recovery phase 須明列未完成，不能省略或算完成。

`summary` 的 `all_known_media_complete=true` 只表示呼叫者提供的已知貼文／媒體簿記與覆蓋資料一致，不代表 GUI、個別檔案或真實 LINE E2E PASS。只有 `scan_coverage=COMPLETE`、貼文細節覆蓋完整、六類狀態沒有未解阻塞、沒有 `REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 等未完成 phase 且 `dispatch_blockers=[]`，才會有此值；個別 `PROTECTED_HISTORY` 或 `LOCAL_MISSING` 仍須明列，不能稱整份列表在本機全部可用或全部備份成功。`status_counts` 的範圍以 `status_counts_scope` 為準（含 `scan_id`；沒有 current scan 時 kind 為 `ALL_KNOWN`）；`all_known_media_status_counts` 另列全部已知媒體。兩者都不是本批次 attempt 成功的證據，成功仍只看對應 attempt 的 outcome／基本檢查／completion。`current_incomplete` 僅計 `status_counts_scope` 範圍內媒體的 `PENDING`／`PREVIOUSLY_INCOMPLETE`／`UNKNOWN`／`PROTECTED_HISTORY`，不含貼文層 `.state=DETAIL_PENDING`；`current_incomplete=0` 在仍有 `DETAIL_PENDING` 貼文或 `all_known_media_complete=false` 時，絕不代表全列表完成（未細盤貼文的媒體總數為 `UNKNOWN`）。貼文列欄位是 `.state`（`NO_MEDIA`／`MEDIA`／`DETAIL_PENDING`，導出 `POST_DETAIL_PENDING`），媒體列欄位才是六類 `status`。`open_restart.scope_unresolved_attempts` 非空時先查原 attempt；安全隔離待補／用盡不是 restart，也不得混入 restart scope 統計。

本機可用性另以 `local_counts` 四類回報：`VERIFIED_PRESENT`、`LOCAL_MISSING`、`LOCAL_CHANGED`、`NOT_APPLICABLE`；不得只列前兩類，也不得把它們混成六類業務狀態。

### 已確認 restart 的 scope 外舊下載

`restart preview` 的 `open_batch.blocking_attempts` 列出 scope 外未決交易，須先按原 outcome 收斂；`DOWNLOAD_FINISHED` 不等於 completion。原交易可用 `download-check` 完成，或依明確非媒體 MIME 追加 exclusion 並保留 staging。scope 內既有交易不沿用這條路徑，仍走已確認 restart；不擴 scope 或改 digest。scope 內已確認的 `LOCAL_CHANGED` 保留原件，不妨礙 scope 外獨立交易收斂；scope 外異常仍停止。新的 restart intent 要求 confirm 後完整卡片覆蓋與 scope 細盤一致，不要求 scope 外所有貼文細盤；全列表待盤狀態仍如實回報。
