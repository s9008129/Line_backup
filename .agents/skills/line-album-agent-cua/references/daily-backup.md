# 本地紀錄工具與舊紀錄對帳

此參考用於完整列表／跨 Session 工作。GUI 仍由 Agent 在既有 CUA 中進行；此文件與輔助 CLI 都不授予 GUI 權限。

Owner 已選日常 AI Agent 流程。這裡是現有工具的輸入規則，不是使用者的啟動表單；不要要求使用者手填 JSON，也不要把記錄工具變成新授權系統。實際下載／恢復步驟見 [備份與恢復](backup-and-resume.md)。

## 本地紀錄入口

在 repo root 使用 `PYTHONPATH=src python3 -B -m line_backup_batch.daily --help`。以下 `daily ...` 都是 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily ...` 的簡寫。

名稱取得、`intent`／`outcome`／`verify`、使用者校正與 `resume-naming` 使用 direct CLI 參數；`scan`、`page`、`detail`、`init`、`bind`、`history` 等仍使用 Agent 依實際觀察建立的私有 JSON 證據，絕不由 Owner 手填。直接參數不可和 `--input` 同時使用。`--source` 必須是真實私有證據檔，不可用手寫字串冒充。業務層的成功與拒絕結果都包含 `dispatch_authorized=false`；那只是簿記結果，不是 GUI grant，也不得改寫為 true。參數語法／必填欄位錯誤會在執行前以 exit 2 與純 stderr 拒絕，不會產生 JSON 或任何紀錄變更。

未另指定時預設為目前專案根目錄的 `backups/`，本工作區是 `/Users/hsiaojohnny/dev/Line_backup/backups`。目的地、證據與編譯後工具均放在本專案內，外部 root／證據引用會被拒絕；不要將外層舊目錄加回輸入。預設路徑不會自動修復搬移後的舊綁定，必須依 [備份與恢復](backup-and-resume.md) 保護原紀錄並停止查明。

新備份使用 `BACKUP_ROOT/<群組實際目錄名>/<相簿實際目錄名>/<相簿實際目錄名>_001.<原副檔名>`。名稱只供顯示及路徑使用；群組／相簿身分仍由 `local_group_id`、`album_key` 與視覺證據決定。新流程固定順序為 `bind → scan/page → capture-group-name（同組一次）→ capture-album-name（每本）→ detail → intent → Save All → outcome → verify`。新 `intent` 必須先取得群組與相簿名稱及最新 detail，完全讀不到名稱時詢問 Owner，不再以舊 `albums/<UUID>` 默默建立新備份。既有、沒有 `naming` 欄位的舊 intent 仍可完成，既有 `albums/<UUID>` 與照片不遷移。

```text
BACKUP_ROOT/
  <group-path>/<album-path>/   新格式；相簿目錄內為 <album-path>_001.<ext> ...
  albums/<attempt UUID>/       僅舊／未命名備份相容，不用於新 intent
  backup-records/
    group.json                本地群組 UUID、目的地與磁碟／目錄識別
    events/00000001.json ...   追加式 inventory／history／memory／intent／outcome／completion
    memory-anchors/*.json      匯入記憶事件的獨立 SHA-256 校驗紀錄
    .lock                     本地序列寫入鎖
```

同名或 Unicode／大小寫正規化後同名的不同實體使用 ` (2)`、` (3)`；恢復使用 ` (恢復 N)` 的新空白相簿目錄並保留前次。名稱清理、路徑元件上限、原子不覆寫改名與每次改名 progress 均由工具處理。不可在 Finder 手動改名來代替校正工具。

不同類別共用一份有序事件紀錄，各自可投影讀出，沒有第二份容易不同步的可變 cursor。每筆有前筆 hash、sequence、群組 UUID；exclusive publish、fsync、readback。發現 pending write 或破損紀錄就停止，不刪紀錄來解鎖。這不是平台 sandbox、正式 writer admission 或實體 exactly-once 證明。

記憶事件另有不可覆寫的 `memory-anchors` 校驗紀錄，讀取時核對事件內容與集合，防止末筆記憶被單獨改寫／移除後繼續。寫入中斷而缺少校驗紀錄也會停止；保留原件查明原因。這是本機一致性保護，不是對具有整個目錄寫入權限者的簽章或防竄改保證。

- `memory`：唯讀投影 `line-backup-memory/v1`，包含完整相簿身分、目前狀態、名稱、目前目的地、attempt、completion 與 `legacy_albums`。校正時先用它取得 `album_key`。這是日常讀取入口，不寫第二份容易不同步的狀態檔。
- `capture-group-name`：在有效前景 binding 內保存 Agent 看到的群組顯示名與安全目錄名。範例：`daily capture-group-name --root "$BACKUP_ROOT" --session-id "$SESSION" --name "$GROUP_NAME" --source "$PRIVATE_SOURCE_FILE"`。名稱不是群組搜尋或身分依據。
- `capture-album-name`：用最新盤點畫面中的 `album_key` 保存相簿顯示名；工具從 `memory` 解析完整 identity，不要求手填 identity JSON。範例：`daily capture-album-name --root "$BACKUP_ROOT" --session-id "$SESSION" --album-key "$ALBUM_KEY" --name "$ALBUM_NAME" --source "$PRIVATE_SOURCE_FILE"`。
- `intent`／`outcome`／`verify`：以 `--album-key` 或 `--attempt-id` 直接操作，不需要 JSON；三者都回傳 `dispatch_authorized=false`。先用 `capture-group-name` 與 `capture-album-name` 保存名稱，`intent` 才能建立新格式空白目的地。
- `init`：需當次前景／目的地對應證據及本專案結構化記憶／實際照片盤點範圍證據。可靠 `context_id` 可省略。新目錄不是「沒有舊備份」的證明；先讀本專案現有 backup-records 與已保存排除／操作紀錄。
- `bind`：傳 `session_id`、既有 `local_group_id`、fresh `observation`、真實 `handoff` 證據檔；可靠 ID 存在時需一致。沒有穩定 LINE ID 時，由 Agent 以實機脈絡對應本地 UUID，歧義才請 Owner 確認。不能只因目錄 basename 或 OCR 相同就認定同群組。
- `history`：`scope_evidence` 加逐本 `entries`。每筆附本地 UUID、完整 `identity`、聲明狀態與本專案 `source` 檔；只在匯入時查核。只有 `line-backup-daily-history/v1` 正規來源會作為完成／排除狀態：來源必須逐欄匹配本地 UUID、完整 identity、`album_key` 與聲明狀態；COMPLETED 另需具預期張數、manifest hash、逐檔 SHA-256 與一致的完整 ImageIO 證據；EXCLUDED 需具同群組／同相簿的 `line-backup-exclusion/v1` 決定與 Owner source。工具把評估結果、必要結構化證據及來源 digest 內嵌進事件，之後讀記憶不再開啟來源。這不提升為正式 AUTO 驗證。
- 不支援、舊格式、欄位不符或證據不完整者保留來源 digest、identity 與原聲明，轉為 `PROTECTED_HISTORY`；可直接匯入 `UNKNOWN`／`PROTECTED_HISTORY` 保護事實。兩者不重新下載，也不計入完成／排除。跨本地 UUID 的輸入仍拒絕。

正規 `source` JSON 的固定欄位為 `schema`、`local_group_id`、完整 `identity`、`album_key`、`status`。COMPLETED 另含 `photo_verification.expected_images`、`manifest_sha256`、`manifest_evidence` 與 `imageio_evidence`；manifest JSON 形狀為 `{ "manifest": [{"name", "size", "sha256"}], "manifest_sha256": "..." }`，ImageIO JSON 必須含 `verdict=PASS`、`readOnly=true`、相符 expected／actualEntries 與逐檔 decoded/name/SHA。EXCLUDED 改含 `exclusion_evidence`，其 JSON 必須是 `line-backup-exclusion/v1`、同 UUID／identity／key、`decision=EXCLUDE_ALBUM` 及 `owner_source` reference。
- `scan`：新 Session／重新盤點都開新 scan，完成事實不清除，畫面 cursor 不跨 Session 重用。
- `page`：`cards`、fresh `screenshot`／`ax` 證據檔，第一頁需 `top_confirmed` 與頂端無位移證據；後頁需 `scroll_evidence`。前頁 suffix／後頁 prefix 必須有序重疊。`unresolved` 記未能定位卡片數，非零不能完成。無法辨識整頁時停下，不省略卡片。空列表目前拒絕 `NO_GROUNDED_CARDS`，不得當完整群組。
- `identity`：`start_date`、`end_date`、`expected_images`、持久 `visual_key`。後者是 Agent 依封面／列表鄰接／詳細頁可區分資訊建立的識別，不是中文 OCR 字串。日期／張數不能單獨 dedupe；歧義不亂配。
- 底端：以同一末頁再次向下捲動，傳 `bottom_stationary=true` 與 `boundary_evidence`；卡片集合／次序、scrollbar／視覺量測位移都須不變。

`boundary_evidence` 是實際觀察的私有 JSON：`edge=top|bottom`、`session_id`、`edge_key`、`before_offset`、`after_offset`、`before_screenshot`、`after_screenshot`、`input_receipt`。offset 使用當次可靠 scrollbar 或同一座標基準的視覺量測；頂端為 0，兩次必須相等。三個 reference 均含 `path/bytes/sha256`，由 `reference()` 建立，後圖需等於當頁 screenshot；底端前圖需等於上一頁 screenshot。這是 Agent 的 `OBSERVED` 證據，不是自動感測器或已退役的正式 G2 gate。

## 交易與恢復

`detail` 記錄當次詳細頁核對。`intent` 需最新相符 detail 及已保存的群組／相簿名稱，會建立具名的新空白目的地並持久保留「可能派送／禁止重送」；新流程缺少名稱時回 `GROUP_AND_ALBUM_NAMES_REQUIRED`。回傳固定 `dispatch_authorized=false`：它只保留本地操作紀錄，不授予下載權限。日常 GUI 依 Owner 真實授權及前景交接；不得把這個回傳值改成 true，或把本地 reservation 當成程式 runtime grant。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily intent \
  --root "$BACKUP_ROOT" --session-id "$SESSION" --album-key "$ALBUM_KEY"

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily outcome \
  --root "$BACKUP_ROOT" --session-id "$SESSION" --attempt-id "$ATTEMPT_ID" \
  --outcome DOWNLOAD_FINISHED --evidence "$PRIVATE_DOWNLOAD_EVIDENCE"

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily verify \
  --root "$BACKUP_ROOT" --session-id "$SESSION" --attempt-id "$ATTEMPT_ID" \
  --decoder "$DECODER" --decoder-sha256 "$DECODER_SHA256"
```

`outcome` 記 `UNKNOWN|NOT_SENT|STOPPED|DOWNLOAD_FINISHED`。預留 intent 後可記錄第一個實際已知結果；一旦寫入明確 `UNKNOWN`，該 outcome 不可由普通 outcome 改成 STOPPED／NOT_SENT，也不能因此自動恢復或重送。`DOWNLOAD_FINISHED` 只能進驗證。前次明確 STOPPED／NOT_SENT 且原任務授權涵蓋自動相簿級恢復時，Agent 依真實初始授權整理該列表／相簿／attempt 的恢復資料，再建立保留原檔的新空目錄；不用使用者逐本重下指令，既有工具的拒絕仍有效。

恢復僅允許前次 `STOPPED|NOT_SENT` 且提供專屬 `recovery_authorization` 檔，內容：

```json
{
  "decision": "AUTHORIZE_ALBUM_RECOVERY",
  "local_group_id": "實際本地UUID",
  "album_key": "實際相簿key",
  "previous_attempt_id": "實際前次attempt",
  "preserve_existing": true,
  "owner_source": {"path": "真實Owner授權檔", "bytes": 1, "sha256": "由實際檔案計算"}
}
```

此為輸入格式示意，不是有效同意。必須引用 Owner 實際提交且涵蓋該任務自動恢復的初始授權；Agent 可整理條件符合與逐本綁定資料，不可捏造 Owner 曾另給一次批准。恢復會新增 attempt／新空白資料夾並引用前次；原檔全留。UNKNOWN 不受此檔覆蓋。日常 helper 只核對資料格式及所引來源仍存在，不驗證簽章，也不簽發 runtime grant。

`verify` 需已知下載完成、當次 decoder path／SHA-256。新格式會先保存原名／暫名／目標名／大小／SHA-256／mtime／ctime 交易，逐檔以不覆寫 rename 改成 `<相簿目錄名>_001.<ext>`，再執行三次間隔樣本、數量、逐檔非空 SHA-256、ImageIO 完整 RGB 解碼、decoder hash 與目錄事後重核；全部通過才追加 completion。沿用 `src/line_backup_batch/image_decode.swift` 或已確認來源相同的既有 binary，不修改系統 toolchain。重啟對完成檔做逐檔 SHA-256 與 metadata 核對，異動就停止而不重下載。

命名或改名中斷用 `resume-naming --root "$BACKUP_ROOT" --decoder "$DECODER" --decoder-sha256 "$DECODER_SHA256"` 接續；它可接續已記錄 `DOWNLOAD_FINISHED` 但尚未建立 name-transaction 的邊界，也會重驗 outcome evidence。不得重送 Save All、重下或手動改資料夾。重跑相同校正時必須使用同一 pending 目標／名稱；不同名稱會被 `PENDING_NAMING_TRANSACTION` 拒絕。`intent`、`outcome`、`verify` 在 pending 校正期間也都停止。

| 中斷／狀態 | 處置 |
|---|---|
| 初始命名交易中斷，來源／暫名／目標可唯一核對 | `resume-naming`，接續同一 transaction，不重送 |
| 群組或相簿校正計畫已保存 | 受影響相簿先顯示 `PROTECTED_HISTORY`；以相同名稱重跑校正或 `resume-naming` |
| 檔案、manifest、mtime／ctime 或目錄內容漂移 | fail closed，不改名、不重下、不自動修補；保留原檔與證據 |
| 無 outcome、`UNKNOWN` 或 `STOPPED` | 不當成可完成；`UNKNOWN` 不重送，`STOPPED` 依原授權走恢復 |

`correct-group-name` 以 `--name` 校正整組已完成的新格式相簿；`correct-album-name` 以 `--album-key`、`--name`、`--source`、`--decoder`、`--decoder-sha256` 校正單本資料夾及照片前綴。兩者都要求群組的實際子目錄集合精確等於已知完成相簿、相簿內檔案集合精確等於 manifest，且沒有活動、未知、未完成、舊格式／外來 sibling、相簿內額外檔案、symlink、device／inode 漂移或 hash 不一致；任何一項成立就停止，不對部分集合宣稱成功。兩者都先保存計畫、再經暫名改名、重驗，並追加可追溯 correction event；原 completion 不改寫。先執行 `memory` 取得相簿 key，範例：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily correct-album-name \
  --root "$BACKUP_ROOT" --album-key "$ALBUM_KEY" --name "$NEW_NAME" \
  --source "$PRIVATE_OWNER_SOURCE" --decoder "$DECODER" --decoder-sha256 "$DECODER_SHA256"
```

計畫一旦寫入，任何來源／目標／符號連結／目錄 device、inode、逐檔大小、SHA-256、mtime、ctime、completion manifest 或 outcome evidence 漂移都 fail closed；目標已存在、foreign 內容、pending correction 的重複 completion 也不會被覆寫或以新空目錄解鎖。即使 SHA-256 相同，只要大小、mtime／ctime 或精確檔名集合改變也不自動接受。已完成但沒有 pending 的檔案變動回報 `COMPLETED_FILES_CHANGED_NO_REDOWNLOAD`；pending 校正期間則顯示 `PROTECTED_HISTORY`。保留原檔與 pending 證據，依具體錯誤查明後再安全 resume。

`outcome` 的第一筆結果不可再追加另一筆，因此明確 UNKNOWN 也不能事後改寫為 DOWNLOAD_FINISHED。此時可依 [備份與恢復](backup-and-resume.md) 直接呼叫既有 decoder 唯讀核驗照片、保存獨立查證證據，但 `daily verify` 不能提交 completion。不要要求 Owner 重複授權、改寫事件或另建 attempt 解鎖；如實回報紀錄收斂所缺的工具能力。

`summary` 投影目前 scan 的逐本狀態；曾見但新 scan 消失的卡片也記 UNKNOWN。輸出明示 `evidence_role=AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED`、`pass_scope=AGENT_ATTESTED_ACCOUNTING_ONLY`。`ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS` 只表示呼叫者提供的逐本狀態簿記完整；不是工具對畫面／照片的獨立 PASS、不是實機 LINE E2E，也不是正式 AUTO。`PROTECTED_HISTORY` 必須為零，且 `INCOMPLETE=UNKNOWN=0`、到底證據存在，才可有此日常簿記 PASS。

## 一次性記憶轉入與身分未明項

`memory-import` 是一次性的離線資料整理，不要求也不建立前景交接。輸入 `local_group_id`、`legacy_albums`、`coverage` 與 `provenance`；既有事件不改寫。舊格式 history 的決定在此轉為內嵌記憶，缺證據就降為受保護，既有 UNKNOWN／受保護事實不升格。未轉入且仍有舊格式 history entries 時，讀取回報 `MEMORY_MIGRATION_REQUIRED`，不自行找外部來源。

每個 `legacy_albums` 項有唯一 `id`、`local_group_id`（未可靠對應為 null）、`identity_hint`（start_date／end_date／expected_images）、`status=UNKNOWN|PROTECTED_HISTORY`、`reason`，可附原聲明、現存照片的相對位置及 SHA-256 清單。不能將開發 fixture、總數或日期／張數轉成逐本完成事實。日常工具只把同日期範圍的候選標成受保護，從不據此跨列表合併或認定完成／排除；實際操作事件的狀態優先。非本列表的提示不應要求還原開發資料，需釐清時只問具體列表／相簿關係。

`authorization-request`、舊 batch／acceptance CLI 及正式 AUTO 控制器已退役。日常流程使用本專案工具與結構化記憶。

## Skill 文件維護參考

維護 Skill 時可參考 [OpenAI Skill 文件](https://learn.chatgpt.com/docs/build-skills) 與 [Anthropic Skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：description 保持精簡，較長流程放在 references 並按需載入。這些參考連結不代表本 Skill 已受官方審核。
