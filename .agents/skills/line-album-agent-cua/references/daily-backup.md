# 本地紀錄工具與舊紀錄對帳

此參考用於完整列表／跨 Session 工作。GUI 仍由 Agent 在既有 CUA 中進行；此文件與輔助 CLI 都不授予 GUI 權限。

Owner 已選日常 AI Agent 流程。這裡是現有工具的輸入規則，不是使用者的啟動表單；不要要求使用者手填 JSON，也不要把記錄工具變成新授權系統。實際下載／恢復步驟見 [備份與恢復](backup-and-resume.md)。

## 本地紀錄入口

在 repo root 使用 `PYTHONPATH=src python3 -B -m line_backup_batch.daily --help`。
每個操作使用 `--root <Owner選定的既存目錄> --input <私有JSON>`；JSON 由 Agent 依實際證據產生，使用者不必手填。
輸入欄位就是 `DailyRecords` 同名 method 的 keyword arguments，來源：`src/line_backup_batch/daily.py`。

```text
BACKUP_ROOT/
  albums/<attempt UUID>/       每次嘗試各自的新空白目錄
  backup-records/
    group.json                本地群組 UUID、目的地與磁碟／目錄識別
    events/00000001.json ...   追加式 inventory／history／intent／outcome／completion
    .lock                     本地序列寫入鎖
```

不同類別共用一份有序事件紀錄，各自可投影讀出，沒有第二份容易不同步的可變 cursor。每筆有前筆 hash、sequence、群組 UUID；exclusive publish、fsync、readback。發現 pending write 或破損紀錄就停止，不刪紀錄來解鎖。這不是平台 sandbox、正式 writer admission 或實體 exactly-once 證明。

- `init`：需當次前景／目的地對應證據及歷史來源盤點範圍證據。可靠 `context_id` 可省略。新目錄不是「沒有舊備份」的證明；先讀歷史索引並查其原始 state／manual archives／私有 checkpoints／completion／最新 summary／排除項。
- `bind`：傳 `session_id`、既有 `local_group_id`、fresh `observation`、真實 `handoff` 證據檔；可靠 ID 存在時需一致。沒有穩定 LINE ID 時，由 Agent 以實機脈絡對應本地 UUID，歧義才請 Owner 確認。不能只因目錄 basename 或 OCR 相同就認定同群組。
- `history`：`scope_evidence` 加逐本 `entries`。每筆附本地 UUID、完整 `identity`、聲明狀態與原始 `source` 檔。只有 `line-backup-daily-history/v1` 正規來源會作為完成／排除狀態：來源必須逐欄匹配本地 UUID、完整 identity、`album_key` 與聲明狀態；COMPLETED 另需具預期張數、manifest hash、逐檔 SHA-256 與一致的完整 ImageIO 證據檔；EXCLUDED 需具同群組／同相簿的 `line-backup-exclusion/v1` 證據與 Owner source。這些只證明引用內容相互一致，不提升為正式 AUTO 驗證。
- 不支援、舊格式、欄位不符或證據不完整的來源保留原始 `source` 與 identity，狀態改為 `PROTECTED_HISTORY`：不重新下載，也不計入完成／排除，並阻止日常 summary PASS。不能猜測舊格式意義來補欄位；跨本地 UUID 的輸入仍拒絕，避免混入其他群組。

正規 `source` JSON 的固定欄位為 `schema`、`local_group_id`、完整 `identity`、`album_key`、`status`。COMPLETED 另含 `photo_verification.expected_images`、`manifest_sha256`、`manifest_evidence` 與 `imageio_evidence`；manifest JSON 形狀為 `{ "manifest": [{"name", "size", "sha256"}], "manifest_sha256": "..." }`，ImageIO JSON 必須含 `verdict=PASS`、`readOnly=true`、相符 expected／actualEntries 與逐檔 decoded/name/SHA。EXCLUDED 改含 `exclusion_evidence`，其 JSON 必須是 `line-backup-exclusion/v1`、同 UUID／identity／key、`decision=EXCLUDE_ALBUM` 及 `owner_source` reference。
- `scan`：新 Session／重新盤點都開新 scan，完成事實不清除，畫面 cursor 不跨 Session 重用。
- `page`：`cards`、fresh `screenshot`／`ax` 證據檔，第一頁需 `top_confirmed` 與頂端無位移證據；後頁需 `scroll_evidence`。前頁 suffix／後頁 prefix 必須有序重疊。`unresolved` 記未能定位卡片數，非零不能完成。無法辨識整頁時停下，不省略卡片。空列表目前拒絕 `NO_GROUNDED_CARDS`，不得當完整群組。
- `identity`：`start_date`、`end_date`、`expected_images`、持久 `visual_key`。後者是 Agent 依封面／列表鄰接／詳細頁可區分資訊建立的識別，不是中文 OCR 字串。日期／張數不能單獨 dedupe；歧義不亂配。
- 底端：以同一末頁再次向下捲動，傳 `bottom_stationary=true` 與 `boundary_evidence`；卡片集合／次序、scrollbar／視覺量測位移都須不變。

`boundary_evidence` 是實際觀察的私有 JSON：`edge=top|bottom`、`session_id`、`edge_key`、`before_offset`、`after_offset`、`before_screenshot`、`after_screenshot`、`input_receipt`。offset 使用當次可靠 scrollbar 或同一座標基準的視覺量測；頂端為 0，兩次必須相等。三個 reference 均含 `path/bytes/sha256`，由 `reference()` 建立，後圖需等於當頁 screenshot；底端前圖需等於上一頁 screenshot。這是 Agent 的 `OBSERVED` 證據，不是自動感測器或已退役的正式 G2 gate。

## 交易與恢復

`detail` 記錄當次詳細頁核對。`intent` 需最新相符 detail，會建立新空白 attempt 目錄並持久保留「可能派送／禁止重送」。回傳固定 `dispatch_authorized=false`：它只保留本地操作紀錄，不授予下載權限。日常 GUI 依 Owner 真實授權及前景交接；不得把這個回傳值改成 true，或把本地 reservation 當成程式 runtime grant。

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

`verify` 需已知下載完成、當次 decoder path／SHA-256。沿用 `src/line_backup_batch/image_decode.swift`，可用已確認來源相同的既有 binary；需編譯時先確認編譯器和 SDK 相符，不修改系統 toolchain。三次間隔樣本一致、數量相符、逐檔非空 SHA-256、ImageIO 完整 RGB 解碼、decoder hash 與目錄事後重核全部通過，才追加 completion。重啟對完成檔做 metadata 核對，異動就停止而不重下載。

`outcome` 的第一筆結果不可再追加另一筆，因此明確 UNKNOWN 也不能事後改寫為 DOWNLOAD_FINISHED。此時可依 [備份與恢復](backup-and-resume.md) 直接呼叫既有 decoder 唯讀核驗照片、保存獨立查證證據，但 `daily verify` 不能提交 completion。不要要求 Owner 重複授權、改寫事件或另建 attempt 解鎖；如實回報紀錄收斂所缺的工具能力。

`summary` 投影目前 scan 的逐本狀態；曾見但新 scan 消失的卡片也記 UNKNOWN。輸出明示 `evidence_role=AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED`、`pass_scope=AGENT_ATTESTED_ACCOUNTING_ONLY`。`ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS` 只表示呼叫者提供的逐本狀態簿記完整；不是工具對畫面／照片的獨立 PASS、不是實機 LINE E2E，也不是正式 AUTO。`PROTECTED_HISTORY` 必須為零，且 `INCOMPLETE=UNKNOWN=0`、到底證據存在，才可有此日常簿記 PASS。

## 舊紀錄對帳

先列來源、相簿識別、目的地、張數、實際完成／派送證據及原紀錄格式；保留來源不變。日期／張數相同不是同一本的證明，也不跨列表套用。

只有能用現有支援格式及完整證據安全對應的來源，才交工具讀入。缺本地識別、manifest、完整解碼或原始來源時，標成受保護歷史：先跳過下載，向 Owner 白話說明缺哪項。不可自己補造驗證結果、改寫舊檔或為了清零狀態重下照片。沒有可靠轉入方法時保留對照清單與具體阻塞，不臨時開發新的匯入框架。

歷史原件依 [封存來源](legacy-formal.md) 查找。`authorization-request`、舊 batch／acceptance CLI 及正式 AUTO 控制器已退役，不從封存目錄啟動，也不建立替代 issuer。既有紀錄格式與狀態語意不變。

## Skill 文件維護參考

維護 Skill 時可參考 [OpenAI Skill 文件](https://learn.chatgpt.com/docs/build-skills) 與 [Anthropic Skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：description 保持精簡，較長流程放在 references 並按需載入。這些參考連結不代表本 Skill 已受官方審核。
