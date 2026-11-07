# 記事本中斷恢復 S1 實作報告

## 文件目的與授權

本文件記錄 `NOTES-INTERRUPTION-RECOVERY-GAP` 的首個離線垂直切片（S1）。實作授權來自 Owner 在 `docs/plans/20261107-notes-restart-overwrite-s1-handoff/handoff.md` 開頭提交的 Implementer Prompt，以及其中明示的三項設計預設：受影響貼文的全媒體批次、獨立新版本路徑取代目前結果但保留舊原件，以及同範圍完成前再次中斷仍可在既存確認下接續。這是開發授權，不是真實批次下載、GUI、相簿、帳本或媒體處置授權。

本切片只處理記事本；沒有修改相簿程式、正式 Skill、使用手冊、AGENTS 或真實 `backup-records/`、`notes-backup-records/`、照片區。

## 基準、範圍與候選身分

- Repository：本專案工作區 `Line_backup`
- Branch：`feature/line-notes-media`
- Base commit：`9f9748cbbc00caa516d541e4c8a808a9e0cc8156`
- 開工前 remote HEAD：同一 SHA
- 本次產品／測試候選：
  - `src/line_backup_batch/notes.py`
  - `src/line_backup_batch/media_verify.py`
  - `tests/test_notes_regressions.py`
  - `tests/test_notes_restart.py`（新檔）
- 本次公開報告：本文件
- 私有原始證據：`.local/line-backup/tasks/20261107-notes-restart-overwrite-s1-handoff/s1-evidence/`

候選檔 SHA-256（在本文件與 Git commit 建立前量測）：

| 檔案 | SHA-256 |
|---|---|
| `src/line_backup_batch/notes.py` | `40198bad214f8e75767f7d90fbecc3651312887f68f5d013c51d5a476711b5f2` |
| `src/line_backup_batch/media_verify.py` | `3138819303ddbc854920d3ad2b02c80097187904359c7af4ae85c164f9fb89a0` |
| `tests/test_notes_regressions.py` | `3ece50b4a75687fdb152110331419e9132b90506764d36e9f365948a375dc789` |
| `tests/test_notes_restart.py` | `140505fe4c73abfaf5feee118cb6cfcea7a9799b18f8067f6626a71ba88b67e1` |

基底版本的三個既有檔案 hash 另存在 `s1-evidence/environment-and-hashes.txt`；`git diff --check` exit 0。tracked diff 為 1,941 insertions、95 deletions，另有 1,181 行的新測試檔。最終 commit SHA 會由 Git receipt 記錄，不在本文件預填。

## 實作內容

### 操作面與持久事件

在 `notes.py` 加入 `restart preview`、`restart confirm`、`restart resume`，並維持既有 `intent`、`verify`、`resume`、`summary` 的相容入口。恢復批次使用版本化的持久事件：

- `restart-confirm`：保存 frozen scope、scan 引用、舊 chain tip、scope digest、證據與 confirmation generation。
- `restart-copy-plan`：在任何 copy 前固定來源、attempt、目標目錄、新檔名與 generation。
- `restart-candidate`：保存持久 candidate 的檔案身分、hash 與驗證結果。
- `restart-activation`：整批候選都通過檢查後，以單一事件提交目前 active version。
- `line-notes-intent/v3`：在既有 intent 上加入 `restart_id`、`confirmation_ref`、`prior_attempt` 與版本資訊；原有 v1／v2 仍可讀取。

`preview` 只讀，從最新完整 scan 建立受影響貼文範圍；確認需要新鮮 session、證據與精確 scope。確認回覆遺失時會讀回既有 confirmation，重複呼叫不會新增第二個 confirmation。確認後要求新的完整盤點，舊 attempt 不會被改寫成新 scan 的 attempt，新 attempt 會保存自己的 scan binding。

### 獨立副本與版本 activation

新 candidate 位於同一允許 photo root 內的 `versions/gNNNNNNNN/<post>/`，不把 raw rename 或 hard-link 成目前結果。`media_verify.copy_exclusive` 使用 exclusive create、no-follow、串流 bytes copy，核對來源 fingerprint、前後來源 hash、副本 hash 與 inode，並對目標目錄做 fsync。copy plan 先持久化，未提交 manifest 的完整副本不會直接採用；candidate drift 會建立新的唯一副本。

候選在 activation 前仍是 candidate，不計為目前結果。全部 scope 候選與當下來源／舊版本核對成立後，`restart-activation` 才一次提交；舊 completion、舊 UNKNOWN、舊 raw、舊版本與原事件 bytes 保留。重開時由 `restart` 投影選出最新 active version，摘要每 media 只計一次，且開放批次未完成時不會因舊 completion 而回報本批次完成。activation 後同篇一般新增媒體會續接 active version 的命名，不重新產生舊版本。

### 邊界與拒絕條件

實作保留既有 fail-closed 行為：未確認、偽造或跨 scope 的 confirmation 不寫入；舊 attempt 在新確認建立後不能再由一般 `verify`／pending `resume` 發布；UNKNOWN 或無 outcome 只能建立有明確 prior 關聯的新 attempt，不偽造 STOPPED 或舊終態；scan／bind 中斷不會自動認領舊交易；候選或 activation 回覆遺失只讀回既有事件，不重複追加；不安全路徑、hash drift、copy 失敗、fsync 失敗或 manifest 未提交都不會 activation。

## 測試對照

以下均為合成離線資料。`PASS` 只描述所列測試案例，不代表整體 C01–C12、真實 LINE、GUI 或 Owner 日常試用已完成。

### V1 垂直路徑與 PR-N01–N04

| 項目 | 測試或證據 | 結果 |
|---|---|---|
| V1 兩篇 fixture、照片＋影片、LOCAL_CHANGED＋UNKNOWN、未確認拒絕、確認、candidate、activation、重開 | `test_restart_vertical_path_isolated_candidate_and_reopen` | PASS（合成路徑） |
| PR-N01 舊 verification／completion 經 activation 後仍可重放，舊 UNKNOWN 仍為 UNKNOWN | 同一垂直測試的舊 attempt／completion／UNKNOWN 斷言 | PASS（合成路徑） |
| PR-N02 跨 Session 新綁定、新 scan 引用與 writer 邊界 | `test_interrupted_recovery_scan_and_new_session_are_bound_to_new_attempt`；`test_new_session_bind_interrupts_open_scan_and_recovery_resumes` | PASS（直接路徑） |
| PR-N03 activation 後同篇新增媒體使用 active version 與續接編號 | `test_new_media_after_activation_publishes_into_active_version` | PASS（合成路徑） |
| PR-N04 skip 不可冒充真實解碼；照片與影片實際解碼 | restart suite 執行結果 `skipped=0`；`test_real_synthetic_photo_candidate_decodes_and_activates`；`test_real_synthetic_video_candidate_decodes_and_activates` | PASS（本機合成 fixture；未證明真實 LINE） |

### 指定的 C 項直接路徑

| 項目 | 本次覆蓋 | 結果 |
|---|---|---|
| C01 未確認／偽造／錯 scope | `test_unconfirmed_forged_and_wrong_confirmations_append_nothing`、`test_confirm_rejects_scan_drift_and_cross_list_preview`；確認前後事件 bytes 不變 | PASS（直接路徑） |
| C02 UNKNOWN／無 outcome 新 attempt | `test_restart_unknown_and_no_outcome_attempts_can_be_superseded`、`test_no_outcome_pre_restart_attempt_is_superseded_without_fake_stop` | PASS（直接路徑） |
| C06 scan／bind 中斷與 pending publish | `test_interrupted_recovery_scan_and_new_session_are_bound_to_new_attempt`、`test_confirmed_pending_publish_is_suppressed_not_republished`、`test_new_session_bind_interrupts_open_scan_and_recovery_resumes` | PASS（直接路徑） |
| C07 回覆遺失與再次 UNKNOWN | 垂直測試的 confirmation replay、`test_activation_reply_loss_is_read_back_without_duplicate`、`test_candidate_reply_loss_is_read_back_without_duplicate`、`test_restart_unknown_and_no_outcome_attempts_can_be_superseded` | PASS（直接路徑） |
| C08 copy／manifest／activation 邊界 | `test_copy_failure_does_not_publish_a_candidate_or_activate`、`test_complete_copy_without_manifest_is_not_adopted`、`test_candidate_drift_is_replaced_by_new_unique_copy`、`test_activation_reply_loss_is_read_back_without_duplicate` | PARTIAL（指定的直接故障路徑；完整邊界矩陣 NOT_RUN） |
| C09 晚到 raw fd、舊路徑重建、copy 中變動 | 垂直測試的晚到 file descriptor 寫入、`test_old_raw_path_recreated_after_candidate_does_not_change_candidate`、`test_candidate_drift_is_replaced_by_new_unique_copy` | PASS（直接路徑；未覆蓋全部硬體／檔案系統故障） |
| C11 舊 bytes／歷史保留與一 media 一 active | 垂直測試逐 bytes 比對舊事件與舊媒體 hash；重開摘要 active row 與舊 completion／UNKNOWN 重放 | PASS（合成 fixture 的直接路徑） |

## 實際驗證

執行環境：macOS 27.2（26B123, arm64）、Python 3.9.6、Apple Swift 6.3.3、選用 Xcode MacOSX26.5 SDK；固定 Homebrew `ffmpeg`／`ffprobe` 7.1.1，兩者 SHA-256 已記入私有證據。照片 fixture 以 `xcrun --sdk macosx swiftc` 建置既有 `image_decode.swift`，未修改產品 decoder 或系統工具鏈。

實際命令與結果：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
# 17 tests, OK, 3.452s; skipped=0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
# 153 tests, OK, 15.781s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py
# 22 tests, OK, 1.983s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_regressions.py
# 53 tests, OK, 4.887s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_media_verify.py
# 27 tests, OK, 4.076s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
# 73 tests, OK, 321.188s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
# exit 0; help includes restart

PYTHONPATH=src /usr/bin/python3 -B -m py_compile src/line_backup_batch/notes.py
# exit 0
```

原始 logs、環境與 hash 對照保存在私有 `s1-evidence/`；`git diff --check` exit 0。上述測試沒有操作真實 LINE、GUI、chooser、真實帳本或真實照片／影片。

## 已知界線、事實、推論與未知

### 事實

- 本次只修改上述四個產品／測試檔並新增本報告；舊 base 事件與檔案未被遷移。
- 合成 fixture 的直接 V1、C01、C02、C06–C09、C11 路徑及 PR-N01–N04 有執行結果。
- restart suite 實際包含一張合成 PNG 的 ImageIO 完整解碼，以及一支合成 MP4 的固定 ffmpeg／ffprobe 全解碼與 activation。
- 目前沒有真實 LINE／CUA、真實 records、照片區或 Owner 日常任務的結果。

### 推論

- 依實作與直接測試，獨立 candidate、單筆 activation、舊歷史保留及跨 Session 新掃描的核心狀態機已具備可審查的離線垂直路徑。
- 這不推論完整 C08、C10、C12 或其他故障矩陣已通過，也不推論所有模型、所有列表或真實中斷都能成功。

### 未知

- copy／fsync／manifest／activation 每個邊界的前後完整故障矩陣，以及磁碟滿、權限、nlink／symlink／inode drift 的全組合。
- 真實 LINE 的前景交接、晚到 GUI 輸入、chooser、下載中斷、跨 Session 實際恢復、真實帳本與媒體。
- 真實來源身分漂移、既有 LOCAL_CHANGED 成因、空間需求及 Owner 日常試用的可用性。

## 尚未執行（NOT_RUN）

- C08 完整邊界矩陣；C10、C12 完整矩陣；C03–C05 在本次未列入直接路徑的完整範圍。
- 整體 V2、V4、G1、G2、A1；Owner 日常正式記事本試用；獨立接受。
- 真實 LINE／CUA、真實 chooser、晚到 GUI 輸入、真實帳本、真實媒體、真實中斷恢復。
- 相簿產品與相簿資料的實機回歸；本次沒有相簿操作。
- 首切片 Simplicity Review、獨立 Plan／Acceptance Review、S2 或合併 master。

## 六種狀態

```text
PRIMARY_OUTCOME_STATUS: IMPLEMENTATION_CANDIDATE_READY
IMPLEMENTATION_STATUS: S1_CANDIDATE_COMPLETE
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

`IMPLEMENTATION_CANDIDATE_READY` 只表示 S1 離線候選已形成並有上述直接測試；不代表正式接受、日常可用、真實 E2E PASS 或整體 DONE。

## 下一步建議

Owner 可使用本報告所列精確候選（以及實際 Git commit SHA）啟動首切片 Simplicity Review，核對 S1 是否維持最小狀態模型與既有資料邊界。審查通過後再由 Owner 決定是否另開 S2 補完 C 項矩陣、整合唯一日常 Prompt／Skill／手冊與安排真實試用；實作者不自行啟動下一個正式角色、不自行 merge，也不把本切片標成整體完成。
