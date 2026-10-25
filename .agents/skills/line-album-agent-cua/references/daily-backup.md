# 前景盤點、持久紀錄及相簿級恢復

此參考用於完整列表／跨 Session 工作。GUI 仍由 Agent 在既有 CUA 中進行；此文件與輔助 CLI 都不授予 GUI 權限。

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

- `init`：需當次前景／目的地對應證據及歷史來源盤點範圍證據。可靠 `context_id` 可省略。新目錄不是「沒有舊備份」的證明；先查 state／manual archives／私有 checkpoints／completion／最新 summary／排除項。
- `bind`：傳 `session_id`、既有 `local_group_id`、fresh `observation`、真實 `handoff` 證據檔；可靠 ID 存在時需一致。沒有穩定 LINE ID 時，由 Agent 以實機脈絡對應本地 UUID，歧義才請 Owner 確認。不能只因目錄 basename 或 OCR 相同就認定同群組。
- `history`：`scope_evidence` 加逐本 `entries`。每筆附本地 UUID、完整 `identity`、聲明狀態與原始 `source` 檔。只有 `line-backup-daily-history/v1` 正規來源會作為完成／排除狀態：來源必須逐欄匹配本地 UUID、完整 identity、`album_key` 與聲明狀態；COMPLETED 另需具預期張數、manifest hash、逐檔 SHA-256 與一致的完整 ImageIO 證據檔；EXCLUDED 需具同群組／同相簿的 `line-backup-exclusion/v1` 證據與 Owner source。這些只證明引用內容相互一致，不提升為正式 AUTO 驗證。
- 不支援、舊格式、欄位不符或證據不完整的來源保留原始 `source` 與 identity，狀態改為 `PROTECTED_HISTORY`：不重新下載，也不計入完成／排除，並阻止日常 summary PASS。不能猜測舊格式意義來補欄位；跨本地 UUID 的輸入仍拒絕，避免混入其他群組。

正規 `source` JSON 的固定欄位為 `schema`、`local_group_id`、完整 `identity`、`album_key`、`status`。COMPLETED 另含 `photo_verification.expected_images`、`manifest_sha256`、`manifest_evidence` 與 `imageio_evidence`；manifest JSON 形狀為 `{ "manifest": [{"name", "size", "sha256"}], "manifest_sha256": "..." }`，ImageIO JSON 必須含 `verdict=PASS`、`readOnly=true`、相符 expected／actualEntries 與逐檔 decoded/name/SHA。EXCLUDED 改含 `exclusion_evidence`，其 JSON 必須是 `line-backup-exclusion/v1`、同 UUID／identity／key、`decision=EXCLUDE_ALBUM` 及 `owner_source` reference。
- `scan`：新 Session／重新盤點都開新 scan，完成事實不清除，畫面 cursor 不跨 Session 重用。
- `page`：`cards`、fresh `screenshot`／`ax` 證據檔，第一頁需 `top_confirmed` 與頂端無位移證據；後頁需 `scroll_evidence`。前頁 suffix／後頁 prefix 必須有序重疊。`unresolved` 記未能定位卡片數，非零不能完成。無法辨識整頁時停下，不省略卡片。空列表目前拒絕 `NO_GROUNDED_CARDS`，不得當完整群組。
- `identity`：`start_date`、`end_date`、`expected_images`、持久 `visual_key`。後者是 Agent 依封面／列表鄰接／詳細頁可區分資訊建立的識別，不是中文 OCR 字串。日期／張數不能單獨 dedupe；歧義不亂配。
- 底端：以同一末頁再次向下捲動，傳 `bottom_stationary=true` 與 `boundary_evidence`；卡片集合／次序、scrollbar／視覺量測位移都須不變。

`boundary_evidence` 是實際觀察的私有 JSON：`edge=top|bottom`、`session_id`、`edge_key`、`before_offset`、`after_offset`、`before_screenshot`、`after_screenshot`、`input_receipt`。offset 使用當次可靠 scrollbar 或同一座標基準的視覺量測；頂端為 0，兩次必須相等。三個 reference 均含 `path/bytes/sha256`，由 `reference()` 建立，後圖需等於當頁 screenshot；底端前圖需等於上一頁 screenshot。這是 Agent 的 `OBSERVED` 證據，不是自動感測器或正式 G2 gate。一般列表導覽不冒充 G2；正式 G2 仍須其原有全部證據與 0.25 viewport 契約。

## 交易與恢復

`detail` 記錄當次詳細頁核對。`intent` 需最新相符 detail，會建立新空白 attempt 目錄並持久保留「可能派送／禁止重送」。回傳固定 `dispatch_authorized=false`：呼叫端還要通過真正 L2 與既有交易入口，不能拿本地 reservation 直接當 Save All permit。

`outcome` 記 `UNKNOWN|NOT_SENT|STOPPED|DOWNLOAD_FINISHED`。預留 intent 後可記錄第一個實際已知結果；一旦寫入明確 `UNKNOWN`，該 outcome 不可由普通 outcome 改成 STOPPED／NOT_SENT，也不能因此自動恢復或重送。`DOWNLOAD_FINISHED` 只能進驗證。前次明確 STOPPED／NOT_SENT 後，另有該群組、該相簿、該 attempt 的 Owner 恢復授權，才可建立保留原檔的新空目錄；這個日常紀錄格式不是執行時授權，正式 L2／交易 gate 仍須獨立成立。

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

此為輸入格式示意，不是有效同意。必須有真實 Owner 來源，不可由 Agent 自行預填批准。恢復會新增 attempt／新空白資料夾並引用前次；原檔全留。UNKNOWN 不受此檔覆蓋。日常 helper 只核對授權檔格式及所引來源仍存在；不驗證簽章、不簽發 runtime grant，不能替代正式 gate。

`verify` 需已知下載完成、當次 decoder path／SHA-256。沿用 `src/line_backup_batch/image_decode.swift`，可用已確認來源相同的既有 binary；需編譯時先確認編譯器和 SDK 相符，不修改系統 toolchain。三次間隔樣本一致、數量相符、逐檔非空 SHA-256、ImageIO 完整 RGB 解碼、decoder hash 與目錄事後重核全部通過，才追加 completion。重啟對完成檔做 metadata 核對，異動就停止而不重下載。

`summary` 投影目前 scan 的逐本狀態；曾見但新 scan 消失的卡片也記 UNKNOWN。輸出明示 `evidence_role=AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED`、`pass_scope=AGENT_ATTESTED_ACCOUNTING_ONLY`。`ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS` 只表示呼叫者提供的逐本狀態簿記完整；不是工具對畫面／照片的獨立 PASS、不是實機 LINE E2E，也不是正式 AUTO。`PROTECTED_HISTORY` 必須為零，且 `INCOMPLETE=UNKNOWN=0`、到底證據存在，才可有此日常簿記 PASS。

## 跨群組正式核准資料

`authorization-request` 輸入 `session_id`、候選 `identity`、真實 `owner_request`。唯讀輸出群組 UUID、目的地 stat、候選、來源 hashes、event head 及缺件；不建立 grant、ledger、consent 或 review。

已追溯：`policies/line-two-album-pilot-v1.json` 的 `gui_authorized_by_this_profile=false` 是來源實作政策與 GUI 執行權限分離；`src/line_backup_batch/cli.py:native_authorize` 只驗既存 project grant，明確 `dispatch_authorized=false`，不是 issuer。正式 project/ONE56 檢查又綁定固定舊 task、config、root、source/runtime、Owner 決策及真實外部 review；不能挪用給新群組。

本輪缺的是**通過獨立審查的一般跨群組 issuer 與對應交易入口**，不是把 false 改 true。request 會如實回 `BLOCKED_NEW_GROUP_ISSUER_REQUIRES_REVIEW`，審查／runtime grant 保持 null。精確審查需涵蓋新群組 UUID／目的地／source-runtime 閉包、專屬新 ledger、既有 duplicate／intent／at-most-once、Owner L1/L2 與各自的真實 review；未完成前停在 Save All 之前。

## Skill 文件維護參考

維護 Skill 時可參考 [OpenAI Skill 文件](https://learn.chatgpt.com/docs/build-skills) 與 [Anthropic Skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：description 保持精簡，較長流程放在 references 並按需載入。這些參考連結不代表本 Skill 已受官方審核。
