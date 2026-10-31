# LINE 記事本照片與影片備份：實作報告

## 角色、授權與邊界

本 Session 的主 Agent 只擔任 Implementer。Curie、Archimedes、James、Dewey、Arendt 都在同一個 Implementer 角色內提供實作、測試或唯讀靜態稽核；helper 的結果不是 Independent Reviewer、Independent Acceptance 或真實 LINE E2E。

Owner 已免除本任務的獨立計畫審查、Simplicity Review 與 Independent Acceptance，但沒有免除必要本機驗證。Owner 要求本功能先留在 `feature/line-notes-media`，待 Owner 實機測試通過並明示合併後，才可合併 `master`。本輪沒有操作 LINE GUI、Save All、真實記事本下載控制、真實帳本或私人照片／影片。

規格來源為 [plan.md](plan.md) 與 [handoff.md](handoff.md)。兩者是交付時的歷史快照，本次沒有修改；本報告以目前 branch、候選 commit、工作樹與實際命令結果為準。

## 基線與候選

| 項目 | 實際值 |
|---|---|
| Repo | `Line_backup`（本機 repository root） |
| Branch | `feature/line-notes-media` |
| 起始 HEAD／產品基線 | `94630d38de83bd8e44b273906521feb4a9eb9040` |
| `master`／`origin/master` | 同為 `94630d38de83bd8e44b273906521feb4a9eb9040`；本次未合併 |
| 功能候選 | `81d9db40a702a145cd2e2e9004cc01ce6df912e3` |
| 最終報告 HEAD | commit／push 後由 Git 遠端 HEAD 與交付回報確認 |
| 合併狀態 | `NOT_MERGED`；等待 Owner 實機測試與明示同意 |

起始工作樹沒有與本任務無關的 modified 或 untracked 內容；「起始」指 handoff 前的基線；候選實作完成時工作樹仍有本任務的未提交變更。本次只新增／修改下列受權路徑；`plan.md`、`handoff.md`、私人任務目錄、照片區與永久帳本均未納入 commit。

## 變更範圍

- 文件與入口：`.gitignore`、`AGENTS.md`、`README.md`、`docs/LINE相簿備份_使用手冊.md`。
- Skill：`.agents/skills/line-notes-agent-cua/` 主文與 `gui-inventory.md`、`download-and-ledger.md`、`verification-and-recovery.md`。
- 程式：`src/line_backup_batch/notes.py`、`src/line_backup_batch/media_verify.py`。
- 測試：`tests/test_notes_e2e_media.py`、`tests/test_notes_media_verify.py`、`tests/test_notes_records.py`、`tests/test_notes_regressions.py`。
- 報告：本文件。

## 已實作行為

- 新增獨立 `notes-backup-records/` 帳本；列表、貼文與媒體三層身分和相簿帳本分離。索引只登錄位置，追加式事件才是事實來源。
- 新增 notes CLI 的列表初始化／綁定、完整掃描、貼文／媒體盤點、intent、outcome、reconcile、verify、resume、summary、目的地追加、排除與保護入口。
- 相鄰頁要求非空、依序的頁尾到頁首重疊；空頁、集合式假重疊、重排缺口與 session 漂移 fail closed。
- 相簿與記事本 Skill、工具、狀態、帳本與 active 定位檔不得互換；GUI authority 不由 CLI 或簿記授予。

### F1／F5：summary 只認最新完整掃描

- completion scope 改以最新完整 scan 的 posts、同 scan 的 post detail 與 media inventory 計算。
- summary 的 `status_counts`／`local_counts` 只計最新完整 scan；歷史 `media` 列仍可能保留供追溯，不能與當次 counts 直接相加解讀。
- 舊 scan detail／inventory 不得讓同一貼文在新 scan 解鎖 intent，也不得讓 summary 回報 `all_known_media_complete=true`。
- 最新 scan 之外的未解 `UNKNOWN` 或 `DOWNLOAD_FINISHED` attempt 仍會形成 completion blocker，不因舊媒體不在新 scan 而解鎖。
- 舊格式或無 `scan_id` 的 post／media 保持可讀，但不計入最新 completion；summary 會列出 `STALE_POST_DETAIL`、`STALE_MEDIA_INVENTORY` 並 fail closed。
- 零貼文列表沒有被補成假 completion。

### F2：同 scan 不可重寫明細

- writer 對同一 `(post_key, scan_id)` 的重複 post detail／media inventory 分別回 `POST_DETAIL_ALREADY_RECORDED`、`MEDIA_INVENTORY_ALREADY_RECORDED`。
- loader 重啟時也拒絕同樣的 duplicate graph，並核對 media inventory 的 `items + missing` 數、`source_order` 與 current post detail 的 `media_count`。
- 舊 inventory 不會解鎖同 scan 的新 detail；現有 `STALE_POST_DETAIL`／`STALE_MEDIA_INVENTORY` 防線保留。

### F3：attempt 綁定掃描與跨 scan 發布

- 新 intent 保存 `scan_id`；舊 unbound intent 仍可載入。
- verify、pending publish resume 與集中 `_execute_publish` 都要求 attempt 綁定仍等於最新完整 scan。
- 舊 unbound intent 回 `INTENT_SCAN_BINDING_REQUIRED`；新 scan 出現後，舊 attempt 的 verify／resume／publish 回 `ATTEMPT_SCAN_BINDING_CHANGED`，不發布也不新增事件。

### F4：open scan 與 session 寫入防線

- scan 尚未 finish 時，`bind` 回 `SCAN_ALREADY_OPEN`。
- `page` 在 append 前比對 scan START session，錯配回 `PAGE_SESSION_CHANGED`。
- `finish_scan` 在 append 前比對 scan START session，錯配回 `SCAN_SESSION_CHANGED`。
- 上述拒絕都確認 event bytes 未變，不先寫入再由 loader 事後失敗。

### F6／legacy 政策

- Owner 尚未另行定義「完全零貼文列表」的產品語義。現行 `page(posts=[])` 回 `EMPTY_PAGE_NOT_ALLOWED`；沒有 page 的 finish 回 `SCAN_REQUIRES_PAGE`，因此零貼文維持 fail closed，不建立完成事實。
- legacy unbound post／media 可讀，但永遠不能作為最新 complete scan 的完成依據；目前會形成全域 `STALE_POST_DETAIL`／`STALE_MEDIA_INVENTORY` blocker，沒有自動補寫、猜測或清除入口。
- legacy unbound intent 沒有自動遷移；verify／resume 固定拒絕。此安全行為可能讓舊帳本無法自動達到 complete，需 Owner 後續決定是否提供正式遷移語義。

### 媒體驗證

- 照片使用 ImageIO 完整像素解碼；嚴格驗證只接受 JPG／JPEG／PNG，檔案須小於 512 MiB，magic format 與副檔名一致。
- 影片使用固定成對的 `/opt/homebrew/bin/ffmpeg`／`/opt/homebrew/bin/ffprobe`，檢查 container／stream、逐 stream null decode、進度覆蓋、watchdog、工具 hash 與版本。
- watchdog 只接受嚴格成長的 frame／out-time；重複或回退 heartbeat 不續命。duration、time-base、溢位與 container 邊界錯誤轉為結構化拒絕。
- `actualEntries`、`expected`、`nb_frames`、`duration_ts`、`attached_pic` 等整數 evidence 明確拒絕 bool／float，避免寬鬆 JSON 型別造成 false PASS。
- persisted loader 會用 `decode.progress.final_*` 重算 duration／frame coverage，並核對 `coverage.observed_*`；只寫 `duration_covered=true` 不再足以通過。

### 明確缺項與 slot coverage

- `media_count` 是當次貼文的 observed total（present + explicitly missing），不是只算可下載的 present item。
- 既有媒體轉為 missing 時，inventory 必須明確保存該項的 `source_order`；省略或重複會拒絕，present items 會填入剩餘 slot，loader 要求完整且不重複的 `0..media_count-1` 覆蓋。
- missing row 仍只接受先前已存在的 media key；首次出現且沒有可唯一對應 key／identity 的 missing 繼續 fail closed，待 Owner 定義 schema，不以序號或猜測建立身分。
- 個別 missing 會反映在該 media 的未完成狀態；其他已核對且可下載的媒體仍可繼續，但不能把整篇或整份列表宣稱為全部完成。

## 實際驗證

環境：macOS／zsh；cwd 為本機 `Line_backup` repository root；Python `/usr/bin/python3`；`PYTHONPATH=src`。

| 命令 | Exit | 結果 | 私有證據 |
|---|---:|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | `Ran 82 tests in 7.779s`；`OK` | `test-notes.candidate.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_permanent_records.py` | 0 | `Ran 18 tests in 32.272s`；`OK` | `test-permanent.candidate.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | `Ran 73 tests in 322.456s`；`OK` | `test-daily.candidate.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m py_compile src/line_backup_batch/notes.py src/line_backup_batch/media_verify.py tests/test_notes_e2e_media.py tests/test_notes_media_verify.py tests/test_notes_records.py tests/test_notes_regressions.py` | 0 | 六個檔案通過 | `py-compile.candidate.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | usage／命令清單可用；含 exit 70、`INTERNAL_ERROR` 契約 | `notes-help.candidate.log` |
| `ruby .local/line-backup/tasks/20261031-notes-media/validate_notes_skill.rb .agents/skills/line-notes-agent-cua`；再執行 `check_notes_skill_links.rb` | 0／0 | frontmatter 契約通過；8 個本地 Markdown 連結均可解析 | `skill-format.candidate.log` |
| `git diff --check`；`git diff --cached --check` | 0／0 | working tree 與最終 index 均無 whitespace error | 終端輸出 |
| `rg -n '[[:blank:]]+$' .gitignore AGENTS.md README.md 'docs/LINE相簿備份_使用手冊.md' docs/plans/20261031-notes-media/implementation.md src/line_backup_batch/notes.py src/line_backup_batch/media_verify.py tests/test_notes_e2e_media.py tests/test_notes_media_verify.py tests/test_notes_records.py tests/test_notes_regressions.py .agents/skills/line-notes-agent-cua` | 1 | exit 1 表示沒有 trailing whitespace match | 終端輸出 |

最終 notes 套件包含：合成 lifecycle 的兩照片一影片（非真實 LINE E2E）、照片／影片完整解碼、watchdog、CLI 0／2／4／70、跨列表隔離、summary stale／legacy blocker、舊 scan UNKNOWN blocker、duplicate writer／loader、跨 scan attempt、open-scan session、missing slot coverage 與零貼文 fail closed。

上表測試／工具 log、`notes-help.candidate.log`、`skill-format.candidate.log` 與兩支 Ruby 檢查腳本均保存在私有任務目錄 `.local/line-backup/tasks/20261031-notes-media/`，不納入 commit。六份最終候選 log 的 SHA-256 如下；每份都由 wrapper 明確寫入實際 exit 行。

| Log | SHA-256 |
|---|---|
| `test-notes.candidate.log` | `f648b153aea7c958874c2d665720547e816e691add9bf99bd89a48942c28c791` |
| `test-permanent.candidate.log` | `56a04ae6091b39c2520bc66627a1805a22751c3fe3cead0287f387123a0ccd50` |
| `test-daily.candidate.log` | `2b4b8da8c536dbd283c0084dfe465cdcad3494a282fdaab0bad136eb8cf887cf` |
| `py-compile.candidate.log` | `418a5c17f33c70e99b0cc0a07fce69191489cfedc94164bfa903785777c5bd4b` |
| `notes-help.candidate.log` | `57227fbf5ee1d222cea2e51f37d3f7fd87a5db88d6c2c67a416c78f3644a6f42` |
| `skill-format.candidate.log` | `b75f661824f5a80e272f272071e7ac0fb37e89034d959bf4198bfcdccb8eda47` |

## 已知限制與未知

- `--decoder`／`--decoder-sha256` 由 caller 提供；工具只證明呼叫端提供的 hash 與執行前後 binary 未漂移，不能證明 binary 來自 repo 的 `image_decode.swift`。實作者必須自行核對 provenance。
- ffmpeg／ffprobe 在 hash 檢查與執行之間仍有本機 binary TOCTOU 邊界；SHA pin 不涵蓋 Homebrew 動態 library。
- `.mp4`／`.mov`／`.m4v`／`.avi`／`.mkv` 允許的 container alias 較寬；目前沒有以真實 LINE 媒體逐一證明所有 alias 的語義。
- 沒有 `nb_frames` 時，影片覆蓋主要依 duration；不能逐幀證明沒有缺幀。
- `save_all_limit=1`／`save_all_count=0` 是 ledger 約束與初始值，不證明 GUI 實際點擊次數，也不是 Save All 控制器的實作。
- `_allow_injected_verification` 是測試建構子的私有開關；production loader／CLI 預設拒絕 injected event 與 verifier，但內部 caller 若刻意開啟，驗證 payload 的檢查較合成測試薄。不得把它當 production 路徑或 acceptance 證據。
- 嚴格照片只支援 JPG／JPEG／PNG；HEIC／HEIF、WebP、TIFF、GIF 與超限檔保留原檔但不降格完成。
- 零貼文 completion、legacy blocker 清除／遷移與舊 incomplete intent 的產品政策仍待 Owner 決定。
- 目的地追加綁定、active-notes-task 真正寫入／損壞／symlink、attached-pic-only 無有效影像、長影片實際等待、貼文文字編輯／附件刪除、結構性 symlink、多檔 locality、相同 bytes 的不同來源項與負向影片案例逐一保存 exit code，尚未全部有專門合成測試；列為 `EVIDENCE_GAP`，不以相鄰測試替代。
- 未執行真實 LINE GUI／列表身分、混合照片／影片附件、下載控制、chooser、popup、Save All、前景中斷、跨 Session 恢復或人眼驗收；不能以合成測試或簿記 PASS 推廣為真實 E2E。

## 未執行與待 Owner 驗證

| 項目 | 狀態 |
|---|---|
| 真實 LINE 記事本列表與貼文盤點 | `NOT_RUN` |
| 真實照片／影片及混合附件下載 | `NOT_RUN` |
| 下載控制、Save All 與 chooser | `NOT_RUN` |
| 真實 popup、前景中斷與恢復 | `NOT_RUN` |
| 跨 Session 接續與多篇列表 | `NOT_RUN` |
| 人眼驗收 | `NOT_RUN` |
| Independent Acceptance | `NOT_RUN`；Owner 免除不等於 PASS |
| destination／active hint／結構性 symlink／多檔 locality 等缺口 | `EVIDENCE_GAP`；見已知限制 |

## 六狀態

```text
PRIMARY_OUTCOME_STATUS: IMPLEMENTED_PENDING_OWNER_REAL_DEVICE_TEST
IMPLEMENTATION_STATUS: DONE_WITH_EVIDENCE_GAPS
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: IN_PROGRESS
```

本報告不是 Independent Acceptance；整體任務仍待 Owner 實機測試、驗收與決定是否合併 `master`。

`IMPLEMENTATION_STATUS: DONE_WITH_EVIDENCE_GAPS` 只表示 feature branch 候選程式與本輪實際完成的合成驗證已落檔；仍保留明確 evidence gaps。它不代表已合併、已通過 Owner 實機測試或已取得 Independent Acceptance。
