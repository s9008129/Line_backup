# 實作報告：記事本影片解碼 stderr 政策

## 結論與版本

本輪 Implementer 完成核准方案 C 的離線產品候選。只有帶有
`FFMPEG_DECODE_DIAGNOSTIC_V1` policy 的新 ffmpeg 逐 stream 解碼證據，
才允許非空 stderr 作為原樣保存的診斷，不再單獨否決；ffprobe、工具版本／
binary hash、嚴格 flags、exit code、stdout EOF、progress、逐 stream
coverage、watchdog、前後檔案與工具穩定、身分及持久化讀回仍維持嚴格。

- 日期：2026-11-10。
- Repo／worktree：`Line_backup` 專案根目錄，主工作目錄。
- 分支：`feature/line-notes-media`。
- 起始 HEAD：`db011e21ee4497d7e169703a7f23bae96422672c`；與當時遠端同分支
  HEAD 相同。
- 核准計畫：commit
  `423fd96f809307ad3f8d09c3faf1631ca74a2870` 的 `plan.md` v1；
  SHA-256 `5ed302615f4261cddeda83d47cb223029341688f8360c9e4bb02c6f80f26c040`。
- 交接：`handoff.md` 已由 Owner 更新並提交於本分支起始 HEAD；開頭 Prompt
  明確核准方案 C、allowlist、資料保護與停止條件。
- 產品內容基線：`2f53bebd0875239312dacb0cb2cf843792a6377d`。
- 本報告與六個產品／測試／Skill 檔案一起形成本輪候選；精確候選 commit
  SHA 由提交後的 Git 交付核對記錄，不在提交前預填。

## 核准範圍與變更

### `src/line_backup_batch/media_verify.py`

- 新增 `VIDEO_DECODE_STDERR_POLICY = 'FFMPEG_DECODE_DIAGNOSTIC_V1'`，
  並由 `verify_video()` 在既有 verification payload 寫入
  `decode_stderr_policy`。
- 移除 `run_decode_command()` 中「非空 decode stderr 立即拒絕」的獨立
  `DECODE_STDERR` gate。ffmpeg 仍使用既有固定 binary、版本／SHA-256 pin、
  `-xerror`、`-err_detect explode`、null muxer、真正 exit 0、stdout EOF、
  progress end、coverage、watchdog 與前後穩定檢查。
- `stderr_empty`、`stderr_bytes`、`stderr_sha256`、有限
  `stderr_preview` 仍由解碼證據保存；診斷不被清洗、改寫或截成無法辨識的摘要。
- ffprobe 的 stderr gate 與工具版本探測沒有放寬。

### `src/line_backup_batch/notes.py`

- 新增 policy 解析：缺少 `decode_stderr_policy` 時維持 legacy 嚴格語意；
  未知值、錯誤型別或其他 policy 一律拒絕。
- 新增 stderr 欄位一致性驗證：`stderr_empty` 必須是 bool；
  `stderr_bytes` 必須是非負整數而不是 bool；SHA-256 必須是合法 hex；
  bytes 與 emptiness 必須一致；空 stderr 的 hash 必須是空 bytes 的 hash；
  preview 必須是有限字串並與 emptiness 一致；新 policy 的非空診斷必須有
  preview。
- 普通 verification 與 restart candidate loader 共用同一份持久化驗證來源；
  `_verify_video_strict()` 在寫入事件前先驗證 payload，malformed 結果不會
  先落帳。`ffprobe` 仍要求空 stderr。
- legacy clean 證據可讀取；legacy 非空證據仍拒絕。新政策只改變診斷通道，
  沒有改變 completion、activation、派送、scope、generation 或歷史語意。

### 測試與 Skill reference

- `tests/test_notes_media_verify.py`：覆蓋 clean、DTS 與未知診斷在完整
  coverage 下通過、診斷 bytes／hash／preview 原樣保存、檔案與工具解碼期間
  漂移拒絕，以及壞檔不解碼仍不得 PASS。
- `tests/test_notes_regressions.py`：覆蓋 legacy clean／非空、未知或錯誤
  policy、bool／float 偽整數、矛盾 stderr、缺 EOF、短 coverage、漏／重複
  stream、偽造 coverage、ffprobe stderr 等拒絕；每個拒絕案例核對沒有新增
  verification／completion。
- `tests/test_notes_restart.py`：以隔離合成帳本驗證 legacy clean 與新政策
  非空診斷混合候選的重開、activation、completion 與讀回；既有 UNKNOWN 與
  既有完成檔保持不變。
- `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md`：
  同步記載新 policy、legacy 嚴格規則、ffprobe 維持嚴格，以及未知診斷不代表
  已證明無害；沒有新增日常啟動步驟。

## 資料保護與邊界

- 本輪只修改核准 allowlist 內的檔案，沒有修改相簿、`daily.py`、
  `record_store.py`、Swift、AGENTS、CLI 參數／退出碼或固定啟動 Prompt。
- 沒有執行 LINE GUI、下載、真實 verify／resume／activation／reattest／
  restart confirm；沒有讀寫真實照片、影片或帳本。
- 既有私人 untracked 提交單原樣保留，未讀取內容、未 stage、未提交。
- 私有證據保存在 `.local/line-backup/tasks/20261110-notes-video-stderr-policy-implementation/`；
  該目錄受 Git ignore，未 stage。舊的合成案例目錄保留，沒有刪除或改寫。
- 本輪沒有 merge master、force-push 或改寫既有歷史。

## 驗證與結果

環境：macOS 27.2（26B123）、zsh、Python 3.9.6、FFmpeg／ffprobe
7.1.1。工具實際 SHA-256 與程式 pin 相符：

```text
ffmpeg  7697b094387e2918821fe7480c73f5d44543817096e9d5b5fafe58ecd6912569
ffprobe fd670257233c93c88608a62ed8b5ddeeb812bd341dfb39bbe0e1c654b91672ad
```

每項命令的 stdout／stderr 與退出碼保存在私有 `logs/`；以下為實際結果：

| 命令 | 退出碼 | 結果 |
|---|---:|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_media_verify.py` | 0 | 30 tests，OK，約 5.5 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_regressions.py` | 0 | 56 tests，OK，約 7.0 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py` | 0 | 40 tests，OK，約 8.0 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 tests，OK，318.7 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 既有 CLI help 正常輸出 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 223 tests，OK，約 29.3 秒 |
| `git diff --check` | 0 | 無空白或 diff 錯誤 |

合成影片測試使用固定工具產生有聲、無聲、多 stream、截斷及損壞 fixture；
測試中的 diagnostic fixture 不是真實影片事故重現，不能推論真實 Post2 已通過。

### 精確基線 reader 相容性

使用 `2f53bebd0875239312dacb0cb2cf843792a6377d` 的 `git archive` 內容建立
隔離 baseline reader。先以新 reader 寫入一個帶有新 policy 非空診斷的合成
ledger，再以 baseline reader 讀取；baseline 的 `notes.py` 與
`media_verify.py` SHA-256 已與該 commit 的精確 blobs 核對相符。

結果：新 reader 成功完成合成影片；baseline reader 退出 0，回報
`{"status":"REJECTED","code":"INVALID_VIDEO_DECODE_EVIDENCE"}`。這證明舊
reader 不會把新非空診斷誤認為可接受的 legacy 完成，但不代表舊 reader 能
接受所有未來候選格式。

第一次重跑既有 helper 時，因前次合成 `baseline-reader-policy` 目錄已存在而
以 `FileExistsError` 退出 1；該次沒有修改產品或真實資料。改用全新的隨機
隔離案例名稱後得到上述退出 0 結果，舊案例保留。

## 事實、推論與未知

### 事實

- runtime、normalizer、普通 verification 與 restart candidate loader 已同步
  使用同一個 policy 邊界。
- 測試中的 clean、DTS、未知診斷在完整 coverage 下可通過；所有列出的
  malformed／漂移／偽造案例均被拒絕，且拒絕案例沒有新增 verification 或
  completion。
- 上述命令退出碼均為 0；這些是離線合成與 repo 回歸結果。

### 推論

- 以 policy 標記保留 legacy 嚴格語意，可避免把歷史非空 stderr 自動重新解釋
  為完成；這是一項由測試支撐的設計推論，不是真實事故的無害性證明。
- 保留 ffprobe 與工具 pin 可維持 probe 邊界；本輪沒有證明所有 ffmpeg 診斷
  都對播放無害。

### 未知／NOT_RUN

- 真實 LINE 列表、GUI 前景、即時 popup、混合附件 chooser、跨 Session 恢復、
  真實 Post2 及整份列表完成：`NOT_RUN`。
- 服務端原始位元一致性、外部副本驗證、OS 隔離、exactly-once：`NOT_RUN`；
  本產品只證明離線檔案解碼與本地證據一致性。
- Owner S1 Simplicity Review、核心條件獨立驗收、獨立 E2E：`NOT_RUN`。
- 真實資料現況是否與提交單描述相同：`UNKNOWN`；本輪沒有讀回或重測。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: APPROVED_IMPLEMENTATION_CANDIDATE_PREPARED; BACKUP_NOT_COMPLETE
IMPLEMENTATION_STATUS: DONE_CANDIDATE; OFFLINE_SYNTHETIC_CHECKS_PASSED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PASS_OFFLINE_SYNTHETIC; REAL_LINE_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_S1_SIMPLICITY_REVIEW
```

## 下一步建議

1. Owner 以本次提交的精確候選 SHA、六檔 diff、本報告與私有驗證紀錄，開啟
   新的主 Session 執行 S1 Simplicity Review。
2. S1 通過後，再由另行啟動的獨立驗收 Session 對精確候選重現合成正負例、
   policy 一致性與舊 reader 相容性；S1 或本報告都不能代替獨立驗收。
3. 真實備份另由 Owner 使用手冊的記事本正式日常 Prompt 與有效前景交接執行；
   不得以本輪離線結果宣稱真實列表完成。
4. 本輪停止，不自動啟動下一個角色、不執行真實 verify／resume／activation／
   restart confirm，也不 merge master 或 force-push。
