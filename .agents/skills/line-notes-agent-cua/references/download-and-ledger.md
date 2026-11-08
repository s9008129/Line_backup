# 下載、notes CLI 與恢復

本文件是記事本備份單項交易與操作順序的唯一來源，也定義目前 branch 的 `notes` CLI 介面。GUI 的定位與觀察依 [GUI 導覽與盤點](gui-inventory.md)，結果、驗證與恢復依 [驗證與恢復](verification-and-recovery.md)，證據欄位依 [證據範本](evidence-template.md)。CLI 只做持久紀錄、交易與驗證，不授予 GUI 權限。

> 這些命令已在 `feature/line-notes-media` 工作樹提供，但尚未合併 `master`，也尚未經真實 GUI E2E 驗證。使用前先在 repo root 執行 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` 核對當次 commands 與 flags；退出碼契約見下節。若不存在或 help 失敗，停止並回報 `IMPLEMENTATION_NOT_AVAILABLE`，不得手寫 JSON、建空帳或改用相簿命令冒充。

## CLI 共同契約

- Agent 從 `page`／`post`／`media` 結果取得 `post_key`、`media_key`；Owner 不填 UUID、key 或內部 JSON。`lists` 的 `--collection` 只定位 collection，`init` 用 collection 建新帳，`evidence-pack` 只建立 bundle，`list-key` 只做 identity 純計算；`memory`、`summary` 及其他持久帳本命令使用 `--records-root`，其中 `destination` 另要求 `--photo-root`。`init` 也要求 `--photo-root`。`backup/記事本/` 是 Agent 層預設，不是 CLI 全域預設。
- `memory`／`summary` 只回摘要投影：列表身分、`scan_coverage`、貼文／媒體列、`status_counts`、`local_counts`、`unresolved_attempts`、`evidence_corrections`、`dispatch_blockers` 與 `all_known_media_complete`；`memory()` 與 `summary()` 是同一投影。`unresolved_attempts` 只列尚未完成／排除／受保護的最新 attempt，不提供完整 attempt 歷史、staging 目的地或 completion manifest。`attempt_id`／`destination` 以該次 `intent` JSON 及追加事件為準，completion 以 `verify` JSON 及 `completion` 事件為準；目前沒有完整的 attempts／completions 查詢子命令。跨 Session 可先以 `memory` 定位 `records_root` 與 blockers，再唯讀核對該帳本 `events/*.json`，不得從 `photo_root` 或目錄名猜交易。
- observation、handoff、下載、chooser、更正與恢復等證據參數（`--binding-evidence`、`--history-scope-evidence`、`--observation`、`--handoff`、`--evidence`、`--recovery-evidence`、`--replacement`）必須是先以 `evidence-pack` 封裝、再由 CLI 回傳的 `line-notes-evidence/v2` bundle 路徑；不可用手寫 JSON、自由文字、目錄或範例內容冒充。bundle 的 statement 可依 [證據範本](evidence-template.md) 撰寫；畫面／AX／input receipt 等原件以 `--asset ROLE PATH` 加入。`source_path` 只記錄匯入來源，重開時核對帳本內保存的子 blob，不要求原件仍在。
- `evidence-pack` 的 statement、每個 asset 與 `--output-dir` 必須使用確認 repo 根目錄後取得的絕對路徑。statement／asset 是專案內 canonical regular file，不是 symlink，且只允許單一 hard link；output 是私有 tasks 下尚不存在的子目錄，其 canonical 父目錄要先存在。Agent 只準備父目錄，不預建輸出子目錄、不自動 resolve 穿過 symlink、不覆寫。固定五欄 context 由 Agent 從 CLI 輸出帶入，適用 ID 不得填 `UNKNOWN` 或另一個主體。成功後把回傳的絕對 `bundle_path` 傳給事件參數。Owner 不需填 JSON、UUID、key 或 hash；bundle 只核對 bytes／context，不證明畫面真實、控制命中或下載結果。
- 若要以 wrapper 保存一次 child 的 request、stdout／stderr、exit／signal 與程式身分，使用既有 `notes_capture --output-root ABS_PRIVATE_TASK_DIR -- <notes argv>`；`--output-root` 必須是已存在、專案私有的絕對路徑。capture receipt 不是 CUA／GUI 原始回傳，也不證明輸入。wrapper 保存失敗就停止，不為補輸出重跑 child；拒絕與成功各自保存新 receipt。
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
| `evidence-pack` | 將 statement、截圖／AX／input 等原件封裝成不可覆寫的 v2 evidence bundle | 只做位元引用與 context 核對；不是 GUI sensor、下載結果或 acceptance |
| `list-key` | 在建帳前以同一組 identity 輸入計算 `list_key` | 純計算，只可讀明示的 `--signals @FILE`；不讀寫帳本、照片、active 檔、鎖或事件，也不代表列表身分或下載資格 |
| `evidence-audit` | 唯讀逐引用稽核保存的 evidence、legacy 分類與 correction 鏈 | 不投影業務狀態；`integrity_ok=false` 或結構鏈異常時不得使用一般 summary 的局部結果 |
| `init` | 建立新的記事本帳本 | 只用於已證明的新列表；歷史缺損、索引毀損或候選歧義時拒絕 |
| `bind` | 將當次列表與既有帳本綁定 | 須有真實前景／觀察 evidence；不靠名稱、日期或張數猜配 |
| `scan` | 建立本次 Session 的新盤點 | 每個新 Session 開新 scan；不重用舊 cursor、舊座標或舊畫面 |
| `page` | 保存有頂底／重疊證據的列表頁 | 前後頁要有序重疊；未解卡片不得省略或假裝完成 |
| `post` | 保存貼文身分、順序、媒體候選及 `NO_MEDIA` | 文字／日期／總數不能單獨認領；貼文層與媒體層分開 |
| `media` | 保存逐媒體觀察與來源順序 | 同外觀／同 hash 仍各自保存；新媒體取目前最大編號加一 |
| `intent` | 在派送前保存 attempt、新空白暫存目錄及禁止重送 | 必須先持久保存並讀回；寫入後按「可能已派送」對待。`--restart-id` 只限已確認批次 |
| `outcome` | 記第一個實際下載結果 | `UNKNOWN` 不可任意改成 `NOT_SENT`／`STOPPED`；逾時不等於未派送 |
| `reconcile` | 以新觀察、原事件與目的地調和未知結果 | 只追加證據，不改寫原 UNKNOWN；未收斂不得 verify 或新派送 |
| `verify` | 穩定檔案、hash、解碼、發布及保存 completion | 只接受已證明 `DOWNLOAD_FINISHED` 的 attempt；不重下補帳 |
| `resume` | 接續中斷的命名／發布交易 | 只用唯一可核對的同一交易；不重送下載、不手動改名 |
| `restart` | `preview`／`confirm`／`resume` 一個確認取代批次 | preview 唯讀；confirm 需精確 scope、證據與 Owner 同意；resume 只驗證 candidate／activation，不按 GUI、不下載 |
| `summary` | 投影本次盤點與六類狀態、缺項及完成數 | `all_known_media_complete=true` 只代表摘要投影一致，不是畫面／檔案獨立驗收，也不是真實 LINE E2E |
| `evidence-correct` | 針對已精確核對的 page 追加 replacement evidence 更正 | 只修 page 引用；不改 page 成員／順序／頂底／scan 覆蓋，也不把更正當成原證據或完成證明 |
| `media-kind-correct` | 在任何 attempt 前更正已盤點媒體的種類 | 只限最新完整 scan、尚無 intent／verification／completion／排除／保護的項目；不改 media key、貼文、數量或來源順序 |
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
restart preview --records-root RECORDS_ROOT
restart confirm --records-root RECORDS_ROOT --session-id SESSION_ID
             --preview @PREVIEW_JSON --evidence BUNDLE
restart resume --records-root RECORDS_ROOT --session-id SESSION_ID
             [--decoder FILE --decoder-sha256 SHA256] [--stall-seconds SECONDS]
summary      --records-root RECORDS_ROOT
evidence-audit --records-root RECORDS_ROOT
evidence-correct --records-root RECORDS_ROOT --session-id SESSION_ID
             --page-sequence N --page-sha256 SHA256
             --original-evidence-sha256 SHA256 --replacement BUNDLE
             --reason TEXT [--previous-correction-ref JSON]
media-kind-correct --records-root RECORDS_ROOT --session-id SESSION_ID
             --media-key KEY --inventory-sequence N [--inventory-sha256 SHA256]
             --to-kind {PHOTO,VIDEO} --evidence BUNDLE
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

`scan start` 禁止 `--scan-id`；`scan finish` 必須有 `--scan-id`。照片 `verify` 必須成對提供 `--decoder` 與 `--decoder-sha256`；影片 `verify` 不傳這兩個照片參數。`post` 的 `--no-media` 與非零 `--media-count` 衝突。

`list-key` 成功 JSON 只增加 `identity`、`list_key` 與既有 `dispatch_authorized=false`，不建立或查詢帳本。`visual_key`／`context_id` 僅以 strip 後非空作檢查，實值的前後空白與 Unicode 原樣保留；context 未提供才是省略，空字串／全空白拒絕。signals 未提供與 JSON `null` 都視為省略，`{}` 是實際值；JSON 物件 key 次序／排版不改 key，字串內容與陣列次序保留。沿用 4096 字元字串、256 KiB identity、strict JSON（拒絕 duplicate key／NaN）限制。缺參數或 JSON 語法錯 exit 2、identity 業務拒絕 exit 4、未預期例外 exit 70；沒有 `--collection`／`--records-root`／照片／evidence 參數，也不參與帳本 lock／retry。

`evidence-audit` 是不可寫入的一般唯讀命令；event chain／結構性引用無法可靠解析時停止，不輸出可誤用的 audit row。引用或子 blob 漂移時仍輸出 audit JSON，但 `integrity_ok=false`、exit 4、`business_projection_omitted=true`，不得從它推論完成數或下一步。legacy opaque 可保持 `LEGACY_OPAQUE`／`REFERENCE_CHECK_NOT_AVAILABLE`，這不是損壞，也不是已核對的原始位元。

### 確認取代恢復（restart）

正常流程沒有 `RESTART_REQUIRED`／`OPEN_BATCH` 時，`UNKNOWN`、pending 與 `LOCAL_CHANGED` 仍依原禁止重送規則停止。只有完整盤點已成立，才能用此批次處理無法直接接續的舊交易；它不是普通新下載，也不是無限重試授權。

1. **預覽。** 在任何新恢復 intent 前執行 `restart preview --records-root RECORDS_ROOT`，保存完整 JSON。`RESTART_REQUIRED` 是新的待確認批次；`OPEN_BATCH` 是既有未完成批次，回傳 `open_batch` progress；`NO_RESTART_REQUIRED` 不建立批次。preview 唯讀，不建立目錄、intent、確認或 activation。
2. **精確確認。** Agent 以白話列出列表、受影響貼文／媒體、已完成 sibling、舊版位置、新 `versions/gNNNNNNNN/` 目錄、額外空間估算、來源缺項與 `EXCLUDED`／`PROTECTED_HISTORY` 保留項。Owner 明示同意後，以同一次 session 執行 `restart confirm`；preview 建議存成私有 JSON，使用 `--preview @PREVIEW_JSON` 傳入。confirmation evidence 必須是 v2 bundle，context 為 `list_key` 加 preview 的 `scope.scan_id`。CLI 在鎖內重算 expected tip 與 scope digest；preview 後的任何漂移以 `RESTART_EXPECTED_TIP_CHANGED`／`RESTART_PREVIEW_CHANGED` 拒絕，不建立確認。
3. **確認後重新盤點。** confirm 成功後必須以 `scan start --recovery` 完成一次新的完整 recovery scan；若目前仍有尚未結束的 scan，先以新 Session 明確 `scan interrupt`，不能假設 `bind` 或 `restart confirm` 會替舊 scan 收尾。不可拿 confirm 前的 page rows、cursor 或舊 scan 直接建立新 attempt。未做此 scan 時 `intent --restart-id` 回 `POST_CONFIRMATION_RECOVERY_SCAN_REQUIRED`。新 scan 只證明目前 scope／來源身分，不改寫舊 attempt 的 scan binding。
4. **逐項新 attempt。** 對 scope 內每個合格媒體執行 `intent --records-root ... --session-id ... --media-key ... --restart-id RESTART_ID`。每次仍建立新的空白 staging，當次下載控制與 chooser 最終確認各最多一次；不得使用舊 raw 路徑、舊 chooser、舊座標或舊 attempt 再按一次。沒有 outcome 時先記第一筆結果；結果未知記 `UNKNOWN`，不可偽造 `STOPPED`。
5. **候選與 activation。** `verify` 只在同一 attempt 為 `DOWNLOAD_FINISHED` 後，將 staging 檔案獨立 copy 到新 generation 目錄，形成不同 inode 的 candidate；不是 rename 或 hard link 成目前結果。candidate 需通過 regular file、nlink、symlink、parent、inode／size／mtime／ctime／SHA-256、額外檔及解碼檢查。全部 scope candidate 成立後，才執行一次 `restart resume` 追加單筆 activation。`restart resume` 只做檔案／candidate／activation，不按 GUI、不下載、不重送。
6. **再次中斷。** 同一個已確認 scope 在完成前再次中斷時，可用 `RESTART_REQUIRED`／`OPEN_BATCH` 找回原批次；已驗證 candidate 與原歷史保留，只對未完成或結果不確定的項目建立新的 v3 attempt。scope、媒體身分、舊版本、目的地或版本策略改變，必須重新 preview 與取得新的 Owner 明示同意。確認不涵蓋另一個列表、其他貼文或無限次重送。

scope 內舊 `UNKNOWN`、無 outcome 或 pending 可被新 attempt 取代，但這不證明舊操作已停止；舊事件、舊 raw、舊 completion 與 UNKNOWN 全部保留。`LOCAL_CHANGED` 只在精確 scope 內以新版本目錄重建，舊目錄不搬動、不覆寫、不自動清理。`LOCAL_MISSING` 不觸發重下；scope 外 `LOCAL_CHANGED`、`EXCLUDED`、`PROTECTED_HISTORY` 與來源 missing／expired 仍保留欠件，不得宣稱整份列表完成。`dispatch_authorized=false` 不是 GUI grant；preview／confirm／resume 的成功都只證明簿記與指定狀態，不證明真實 LINE 派送或 E2E。

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

查詢既有帳本時，先用 collection 取得全部摘要列，只選出與當次入口、列表身分及歷史唯一相符的那一列，再把該列的 `records_root` 原值傳給 `summary`：

```sh
TASK_PROJECT_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
ABS_COLLECTION="$TASK_PROJECT_ROOT/notes-backup-records"
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes \
  lists --collection "$ABS_COLLECTION"

ABS_LEDGER="/ABS/PROJECT/Line_backup/notes-backup-records/UNIQUE_LOCAL_LIST_ID"
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes \
  summary --records-root "$ABS_LEDGER"
```

`ABS_LEDGER` 必須換成上一步結果中唯一相符列的完整 `records_root`。無相符帳本、多候選、索引／歷史損壞或無法唯一定位時停止；不要靠顯示名稱猜目錄，也不要把 collection 傳給 `summary` 或增加 `--local-list-id`。

`evidence-correct` 只用於已確認的 page 證據錯引。Agent 從目前帳本事件取得 page 的 sequence／SHA-256、原 evidence SHA-256 及替換 bundle；替換 bundle 的 scan context 必須對應 target page 當時的 scan，不是現在最新 scan。若 page 以外仍有 evidence 損壞，拒絕 `EVIDENCE_REPAIR_SCOPE_MISMATCH`；重複更正須帶前一筆 correction 的 sequence／SHA-256，不得分叉。成功只追加 correction，不修改 page 成員、順序、top/bottom、scan 覆蓋、media key 或已完成事實；真實帳本仍須 D2 的精確資料預覽與授權。

`media-kind-correct` 只處理最新完整 scan 中、尚無任何 intent／verification／completion／exclusion／protection 的已盤點媒體。來源 inventory 必須是最新且 context 相符；更正只新增 `media-kind-correction`，原 media key、貼文、數量、次序與 inventory 保留。`summary` 會同時顯示原始 `kind`、`effective_kind` 與 correction ref；新 `intent` 使用 `line-notes-intent/v2` 凍結 effective kind，後續 `verify` 選擇對應照片／影片驗證器。合法舊 v1 intent 保持可讀，但任何更正後才偽造的 v1 intent 會 fail closed；不手改 schema 或 events。

`source-unavailable` 只在單一來源已明確到期、最新 attempt 為 `STOPPED`，且沒有完成／排除／保護／待命名交易時可用。成功只代表該項來源不可用：摘要顯示 `source_availability=EXPIRED`，`resume` 對該項列 `SOURCE_UNAVAILABLE`，不得再 `intent`；六類狀態與 `current_incomplete` 不改，也不能批次推論同列表其他項到期或自動排除。

## 掃描覆蓋與綁定 gate

`summary` 的 `scan_coverage`、`dispatch_blockers`、`unresolved_attempts` 與 `scan_binding_match` 是唯讀事實投影，不是下載許可。新 Session 先以 `summary` 找舊 attempt，核對當次入口／前景並成功 `bind` 後，才使用要求 Session 的交易命令；不能因為尚無綁定就沿用舊 Session ID。`has_outcome=false` 時依原 attempt 的真實證據先用 `outcome` 保存第一筆結果，證據不足可記 `UNKNOWN`，不得先 `reconcile`；已有 `outcome=UNKNOWN` 才以新證據 `reconcile`；`DOWNLOAD_FINISHED` 先 `verify`，pending naming 先 `resume`。無新證據就保留原狀，不補造結果或重送；在這些狀態未處理前不得開始普通新 scan。只有完成精確 `restart confirm` 後，才可用 `scan start --recovery` 建立新的完整 recovery scan，再逐項 `intent --restart-id`；這不是用新 scan 掩蓋舊問題，也不改寫舊 attempt 的 scan binding。`bind` 若因未完成 scan、身分或證據等條件拒絕，停止並保留原狀，不重建空帳或以新 scan 掩蓋。

普通 `scan start` 會拒絕待命名交易、尚有未解 attempt，或上一個 scan 的貼文／媒體 coverage 不完整；`scan start --recovery` 只在 STOPPED／NOT_SENT 恢復或已確認 restart 批次的路徑使用，仍受 bind、Session、完整掃描與各自 gate 限制，不是通用解鎖。已完成項與正面 `STOPPED`／`NOT_SENT` 不會被重下；後者仍需原恢復授權與充分證據才可另建 attempt。`summary` 與 `intent` 共用細盤 coverage gate：頂底／重疊、所有現存貼文 detail、media 數量與本 scan inventory 必須一致；純文字貼文以 `NO_MEDIA` 表示，不可當成缺少媒體。

若舊 attempt 的 `scan_binding_match=false` 或 `resume` 回 `SCAN_BINDING_REVIEW_REQUIRED`，不得改綁定、重寫舊 intent、開新 scan 覆蓋、隱藏該項或自動另建 attempt；只保留原資料、收集最小證據並交人工審查。

`--decoder`／`--decoder-sha256` 由呼叫端提供；CLI 只核對呼叫端提供的 SHA-256，並確認執行前後是同一個 binary、沒有內容漂移，不能證明該 binary 來自 repo 的 `src/line_backup_batch/image_decode.swift`。實作者仍須自行核對建置來源、路徑與版本；來源無法確認時停止，不得以 caller 提供的 hash 相符代替 provenance。

## 啟動與帳本對帳

1. 先執行 `lists`，再讀 `.local/line-backup/active-notes-task.json`；以本次連續入口與當次畫面核對相符的 `local_list_id`，不要只讀最近一個帳本。需要單帳本摘要時，從唯一相符列的 `records_root` 執行 `summary`，不從名稱猜路徑。
2. 以 `memory` 讀摘要中的列表、貼文／媒體狀態、缺項、`unresolved_attempts`、`dispatch_blockers`、scan binding 與本機可用性；需要 staging 目的地或 completion 細節時，依上節回到 `intent`／`verify` 結果及追加事件。索引缺失、帳本損壞、證據鏈異常或出現兩個可能列表時停止相關動作，不建立新空帳。
3. 新列表只有在入口、列表身分與歷史均確認，且沒有缺損／歧義時才建立。Agent 先固定同一組 `visual_key`、適用 `context_id` 與 signals 輸入，以 `list-key` 取得 key；用同一 `list_key` context 分別建立 binding／history 兩份 v2 evidence；再以完全相同的 identity 參數與兩份 bundle 執行 `init`，最後以回傳的 `records_root` 執行 `summary` 讀回相同 `list_key`。鏈如下；`CONTEXT_ID` 不適用時整項省略，不是空字串或 `UNKNOWN`，SIGNALS 未使用時同樣省略：

   ```sh
   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes list-key \
     --visual-key "$VISUAL_KEY" --context-id "$CONTEXT_ID" --signals "$SIGNALS_INPUT"

   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
     --statement "$BINDING_STATEMENT" --asset screenshot "$BINDING_SCREENSHOT" \
     --output-dir "$BINDING_EVIDENCE_NEW_DIR" --list-key "$LIST_KEY"
   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
     --statement "$HISTORY_STATEMENT" --asset screenshot "$HISTORY_SCREENSHOT" \
     --output-dir "$HISTORY_EVIDENCE_NEW_DIR" --list-key "$LIST_KEY"

   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes init \
     --collection "$ABS_COLLECTION" --photo-root "$ABS_PHOTO_ROOT" \
     --name "$DISPLAY_NAME" --visual-key "$VISUAL_KEY" \
     --context-id "$CONTEXT_ID" --signals "$SIGNALS_INPUT" \
     --binding-evidence "$BINDING_BUNDLE" \
     --history-scope-evidence "$HISTORY_BUNDLE"

   PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes summary \
     --records-root "$ABS_LEDGER"
   ```

   `SIGNALS_INPUT` 是明示的 strict JSON 文字或 `@` 加指定 JSON 檔的絕對路徑；未使用 signals 時連同整個 flag 省略。當次任務已授權確認停止後的恢復時，在真正新建帳本的 `init` 命令加上 `--recovery-authorized`，並從回傳／摘要讀回 `recovery_authorized=true`；未獲授權不得加此 flag。既有帳本不重新 init，也不手改 false 的授權值。先核對兩份 bundle 的 context 都等於 list-key 結果，再執行 `init`；若 identity 輸入或明示 signals 檔在期間改變，舊 bundle 不可沿用。`init` 後只使用其回傳的 `records_root` 讀回 key，不一致或有未預期副作用就停止；不得先建空帳取得 key、手填 key／JSON，或讓適用 ID 留 `UNKNOWN`。新列表讀回成功、或既有列表從 `lists`／`memory` 找到相符帳本後，先核對當次入口與有效前景，再依序 **`bind` → 處理舊 attempt／命名交易 → `scan start`**；沒有未決項才直接進新 scan。每一命令仍須滿足自己的 scan binding／資料完整性 gate，不能因已 bind 就視為舊 attempt 已獲重送或恢復許可。不因新 Session、照片 root 改變或使用者重交前景而重新初始化。
4. `scan start` → `page`… → `scan finish` → `post`／`media` 保存本輪完整盤點。`scan finish` 前必須已看到頂端、底端與有序重疊；`post`／`media` 需要最新完成的 scan。新 Session 必須重新看頂底與重疊，不沿用上一個 Session 的畫面 cursor。純文字貼文由 `post` 記 `NO_MEDIA`，不建立媒體下載項。
5. 重新更換照片 root 時用 `destination` 追加綁定；舊 completion 路徑不改，UNKNOWN、活動下載、pending 命名或 `LOCAL_CHANGED` 不因換位置解鎖。

## 一次一項的派送交易

每次只處理一個已核對的貼文／媒體 attempt，不得平行下載多項。固定順序如下：

1. **intent 前預檢。** 從 `memory`／本次 scan 確認該項不是 `COMPLETED`、`EXCLUDED` 或不可跳過的 `PROTECTED_HISTORY`；`PREVIOUSLY_INCOMPLETE` 先走恢復判斷，已有 outcome 的 `UNKNOWN` 先 `reconcile`。在建立 attempt 前，再次核對同一列表、貼文、媒體、viewer 與記事本下載控制；只有資格、來源身分、控制出處／可見性與當次映射都能成立時才可繼續。任一項是 `UNKNOWN`，或控制可能屬於相簿／另一畫面，就停止在 intent 前，不為取得證據而先按下載控制。
2. **建立並讀回 intent。** 在任何下載派送前執行 `intent`，讓 CLI 保存 attempt、新空白暫存目錄與「可能已派送、禁止重送」紀錄；讀回 JSON 中的 `attempt_id`、`destination`、`save_all_limit` 與 `save_all_count`，並在私有任務區保存這次預檢與讀回的證據。成功 intent 會帶 `status=UNKNOWN`，那是**派送前初始狀態**，不表示已點擊或下載。`save_all_limit=1`／`save_all_count=0` 只是 intent 建立時的 ledger 約束與初始值，不是 GUI 點擊計數，也不證明記事本下載控制實際被按下幾次。
3. **讀回後再次定位。** 在任何輸入前，重新取得當次畫面／AX，核對同一列表、貼文、媒體、viewer、控制與 intent 讀回的 `post_key`、`media_key`、原目的地；視窗移動、縮放、換頁、popup 重開或來源改變都會使舊映射失效。重新定位失敗時停止所有 GUI 輸入，保留本次 intent 為可能已派送；不得建立替代 attempt，也不得以 marker／chooser 缺席解鎖。
4. **下載控制至多一次。** 只使用記事本當次畫面與工具文件提供的控制，不沿用相簿的 `⋯ → 儲存全部`、錄影座標或舊 Session 位置。每個 attempt 的實際下載控制呼叫上限是一；失敗、逾時、呼叫成功但結果不明也都算一次，必須分別保存工具原始回傳與獨立觀察。選單開啟、滑鼠移動或 chooser 路徑輸入不得重置這個計數；已派送但結果不明時，不得重開或再點下載控制查證。每次 attempt 仍使用自己的新空白暫存目錄；來源檔名、相同 basename、隱藏副檔名或檔案出現順序都不能證明同一媒體，也不因此建立全域改名器或跨 attempt 去重。
5. **chooser 觀察與至多一次確認。** 下載控制呼叫與 chooser 最終確認是兩個獨立計數。chooser 可能延遲出現；只有視窗／process、來源 viewer 與 attempt 能唯一歸屬時，才輸入此 attempt 的新空白暫存絕對路徑並讀回。Go to Folder 的預填值只證明 PathTextField 內容，不是 panel current directory，也不是 intent staging；三者要分開觀察。只有 PathTextField、where／current directory 與本 attempt 的 intent destination 能一致指向該 intent 已建立、讀回且仍空白的原目的地，且來源貼文可歸屬時，才可確認至多一次。出處不明、三者任一 `UNKNOWN`／不符或確認結果未知時不得確認，也不得用第二次確認、猜 Return 或重派恢復。出現 chooser 只證明 App 有階段性回應，不是下載完成。
6. **記錄第一筆 outcome。** 先確認該 attempt 是否已有 outcome 事件，不從 `memory` 顯示的 `UNKNOWN` 猜測。沒有 outcome 時只執行一次 `outcome`，依第一筆真實結果記錄；若只有逾時、畫面未變、進度未終止、chooser／檔案的歸屬不足或其他不確定訊號，就記 `UNKNOWN`，不得改寫成 `NOT_SENT`／`STOPPED`，也不得先呼叫 `reconcile`。已有 `outcome=UNKNOWN` 時，才可以在取得新證據後使用 `reconcile`；不得再做第二次 `outcome`。
7. **未收斂即停止。** 結果未達可進入驗證的正面終結前，不得 `verify`、建立新 intent、重下或派送下一項；晚到結果只能先歸回原 attempt 並調和，不能算成下一項。相同查證連續兩次沒有新資訊就停止，不重置次數或換入口繞過。只有可歸屬且足以排除原操作稍後繼續的明確停止／未派送證據，才可能進 `STOPPED`／`NOT_SENT`；目前是否能取得此證據仍 `UNKNOWN`。
8. **驗證與完成。** 只有具備可歸屬的下載終結結果及穩定結果檔，才可記 `DOWNLOAD_FINISHED` 並執行 `verify`。`verify` 先保存命名／發布交易，再核對穩定檔集、預期數、非空、SHA-256、逐檔內容解碼及前後身分；成功才追加不可覆寫 completion 並讀回。驗證或紀錄寫入失敗時保留原檔，不重新下載補帳。
9. **命名中斷。** 只要來源、暫名、目標及 journal 可唯一核對，執行 `resume` 接續同一交易；`resume` 不得觸發下載。目標已存在、額外檔、symlink、hash／mtime／ctime 漂移或來源與目標歧義時，保護原檔並停止，不用手動改名解鎖。

每次下載控制、chooser 確認、outcome、reconcile、更正與恢復前，先依 [證據範本](evidence-template.md) 寫當次私有 statement，再把 statement 與必要截圖／AX／input receipt／stdout／stderr 等原件用 `evidence-pack` 封裝；有 `--evidence` 或其他證據參數的子命令傳回傳的 `bundle_path`。`intent` 沒有一般 evidence 參數，其預檢與讀回證據留在私有任務區，不能冒充 CLI 欄位。同一 attempt 可多次 reconcile；每次完成後都要追加該次 sequence／event SHA-256 與結果引用，保留全部歷史，不以最後一筆覆寫。bundle 只證明指定 bytes 與 context 一致，不解析 statement 的語意真假；缺少必要值時寫 `UNKNOWN`，不可由檔名、猜測或另一個來源補值。

## 恢復與不可解鎖狀態

| 既有狀態／證據 | 下一步 |
|---|---|
| `COMPLETED` 且本地完整，或整篇目錄已 `LOCAL_MISSING` | 保留完成並跳過；`LOCAL_MISSING` 回報本機不可用，不重下、不證明外部副本 |
| 完成目錄仍存在但缺檔、額外檔、hash／身分漂移或 symlink | `LOCAL_CHANGED`：保護原件。scope 外停止新派送；只有 `restart preview` 精確列出且 Owner 確認該 scope 時，才可在新 generation 重建，不重下補帳或覆寫舊目錄 |
| 已 `DOWNLOAD_FINISHED`、尚未 completion | 驗證現有暫存／目標並完成或 `resume`，不重下 |
| 命名／發布交易中斷 | `resume` 同一交易；不得重送下載 |
| 已有 `outcome=UNKNOWN` | 先 `reconcile`；沒有新資訊就停止相同查證。未收斂前不得一般 verify、建新 attempt、重下或派下一項；只有精確 restart preview 與 Owner 明示確認該 scope 後，才可用 `intent --restart-id` 建立新 generation attempt。舊 UNKNOWN 保留，不宣稱已停止 |
| `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH` | Agent 出示精確 scope 並取得 Owner 明示同意後 `restart confirm`；confirm 後必做新的完整 recovery scan，才可逐項 `intent --restart-id`。每項下載仍最多一次；全部 candidate 通過後才 `restart resume` activation。scope／身分／目的地改變要重新確認 |
| `source_availability=EXPIRED` | 該項保留原欠件並停止 recovery／intent；`resume` 只列 `SOURCE_UNAVAILABLE`，不自動排除、不計完成、不宣稱服務端已回收 |
| `scan_binding_match=false` 或 `SCAN_BINDING_REVIEW_REQUIRED` | 不改舊 intent.scan_id、不隱藏、不自動新 scan／新 attempt；保留原事件與目的地，交人工審查 |
| 明確 `STOPPED` 或 `NOT_SENT`、原檔保留、帳本已有持久化 `recovery_authorized=true`，且有充分停止證據 | 保存並讀回證據，以 `intent --recovery-evidence` 綁定前次 attempt，由 CLI 建立另一個新空白恢復目錄；已完成項跳過。授權未持久化、證據不足或前項不是終止狀態時停止，不手動建目錄或改 ledger |
| `PREVIOUSLY_INCOMPLETE` | 依原授權走上述恢復判斷，不當普通待下載直接派送 |
| `PROTECTED_HISTORY` | 保留來源與缺項；只有完整盤點、無列表級歧義且不是活動／UNKNOWN／pending 時才可跳過該項，不計完成或排除 |

恢復只重做原授權範圍內未完成的項目，不重跑已完成清單。原本的暫存、部分下載、證據與日誌全部保留；新 attempt 不可覆寫舊目錄或舊事件。`STOPPED`／`NOT_SENT` 的 v2 recovery 與精確 restart 批次是兩條不同路徑：前者需要已持久化 `recovery_authorized=true` 與停止證據；後者需要 fresh preview、Owner 對精確 scope 的明示確認及 confirm 後新 scan，不需要也不得把 `recovery_authorized` 當成批次同意。若原 Prompt 未涵蓋恢復、UNKNOWN 無法收斂，或工具缺少安全調和能力，停止並提出最小具體問題；未收斂的同一列表不得派送下一項。

現行 CLI 只在 `init --recovery-authorized` 時把 v2 `STOPPED`／`NOT_SENT` 恢復授權持久化到列表帳本；沒有事後修改該授權的子命令。既有列表若 `memory` 顯示未授權，停止該路徑並交人決定，不直接編輯 `list.json`、事件或另造空帳。`restart` 批次另有 confirmation evidence 與 scope gate，不能以缺少此 flag 為理由繞過，也不能把 flag 當成 Owner 同意。

## 新媒體、重排與跨列表

- 再次執行時先 `bind`，一般情境再以新 `scan start` 對帳，不重用上輪 cursor；若走已確認 restart 批次，則 confirm 後先明確中斷尚未結束的 scan，再以 `scan start --recovery` 重新盤點。貼文重排只更新 `source_order`，舊完成檔名不動；新媒體只補唯一可辨識者，編號取該貼文目前最大值加一。
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
