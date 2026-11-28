# Notes 全問題重規劃：S1 Implementer 報告

## 本角色結論

- 角色／階段：Implementer，只執行 Owner 指定的第一個離線切片 S1（A1 evidence bundle／舊讀相容、A3 notes 專用單次 capture、E 精確 LOCK_BUSY）。
- 使用者目標／核定版本：依 [replan.md](replan.md)、[plan.md](plan.md) 與 [handoff.md](handoff.md) 的現行 S1 路由。Owner 已將兩項前置計畫審查記為 `WAIVED_BY_OWNER`；這不是審查 PASS，也沒有擴張 S2／S3、GUI、真實帳本或下載授權。
- 交接版本：`e89f856582a7a4101c1ecb15fc416faf5ed8ac36`；replan SHA-256 仍為 `da2af8f3fbcd54e5492f06a042e3c2b3d03d6c4b3c5c42b6b3942acf787b2113`。
- Repo／worktree：`Line_backup`；分支 `feature/line-notes-media`。起始本機與遠端 HEAD 均為 `e89f856582a7a4101c1ecb15fc416faf5ed8ac36`。
- 候選身分：本報告、產品程式、測試與 frozen fixture 位於同一交付 commit。該 commit 不能在自身內容中預填自己的 SHA；交付後以 `git rev-parse HEAD` 與 `git ls-remote` 讀回。
- 角色獨立性：本次由單一 Implementer 主 Session 完成；既有 helper 只提供同角色唯讀研究，不能簽發 Acceptance、Simplicity Review 或獨立 PASS。

## 起始狀態與保留工作

起始工作樹不是空白候選，而是同一 S1 的前輪未提交草稿。依交接要求全部保留並接續修正，沒有 `reset`、`clean`、覆寫無關變更或建立替代 worktree：

```text
 M src/line_backup_batch/notes.py
 M tests/test_notes_e2e_media.py
 M tests/test_notes_records.py
 M tests/test_notes_regressions.py
?? src/line_backup_batch/notes_capture.py
?? src/line_backup_batch/notes_evidence.py
?? tests/fixtures/
?? tests/test_notes_capture.py
?? tests/test_notes_evidence.py
?? tests/test_notes_locks.py
```

本次在同一 S1 範圍內補上 T2／T6 的直接測試，並將 capture 的新 receipt 再做一次不跟隨 symlink 的 canonical 驗證。未新增白名單以外產品路徑。

前輪測試曾留下合成的 `.local/line-backup/active-notes-task.json`。已確認其目標為已刪除的合成 `notes-locks-*` 目錄、內容不是真實業務資料後移除；原始證據保存於 `.local/line-backup/tasks/20261101-notes-s1-implementation/contamination-synthetic-active-notes-task.json`，SHA-256 為 `27216e4149afdbf8838c357dbc713dbe94aa00f31d41eca95525ebab17e222fb`。完測後再次核對 active notes hint 不存在；此私有證據不進 Git。

## 變更與 S1 需求映射

| 路徑 | 行為 | S1 對應 |
|---|---|---|
| `src/line_backup_batch/notes_evidence.py` | 新增一層 `line-notes-evidence/v2` bundle、固定五欄 context、exact asset refs、child blob hash／長度／路徑核對、legacy opaque 唯讀分類、import source 與 ledger 重開分離。 | A1、T1 的 A1 部分 |
| `src/line_backup_batch/notes.py` | created／binding／destination／scan／page／post／media／intent／outcome／reconcile／exclude／protect 接上 v2 context；init 先 preflight、鎖內比對來源漂移；新 scan-bound 寫入拒絕 `UNKNOWN` context；新增 `evidence-pack` CLI；精確 flock 分類。 | A1、E |
| `src/line_backup_batch/notes_capture.py` | 固定 notes module 與 argv 陣列、無 shell、單次 child；request 先保存讀回；result、stdout、stderr、程式身分、時間／時鐘與 complete 最後發布；保存或 child 啟動失敗維持 wrapper 70。 | A3、T2 |
| `tests/test_notes_evidence.py` | v2 正常／tamper／symlink／escape／missing／duplicate key／context 錯誤、preflight 前置拒絕、漂移無 event、中斷 blob 保留、v1 frozen fixture、legacy 不升格與新寫拒絕。 | A1、T1 的 A1 部分 |
| `tests/test_notes_capture.py` | 新 receipt、refusal→success、0／2／4／70／signal、request 先於 child、全量輸出、四階段保存失敗、launch failure、program drift、collision、symlink、固定 interpreter／cwd／PYTHONPATH／hash／clock。 | T2 |
| `tests/test_notes_locks.py` | in-process 精確 errno、mutation／resume 不標 retry、exit 70 契約；真正 CLI 子程序持 collection／records flock，唯讀命令 exit 4，釋放後 exit 0。 | T6 |
| `tests/test_notes_records.py`、`tests/test_notes_regressions.py`、`tests/test_notes_e2e_media.py` | 將既有合成 ledgers 轉用 v2 evidence；保留原 UNKNOWN、verification、naming、media 與 CLI 契約。 | A1 回歸 |
| `tests/fixtures/notes_v1/` | 以 `e89f856` 的舊 writer 生成 frozen synthetic v1 ledger，覆蓋 created→binding→scan/page→post/media→intent/outcome；保存 legacy opaque evidence 與舊 writer 投影。 | T1 的 A1 相容證據 |
| `docs/plans/20261101-notes-all-issues-replan/implementation.md` | 本報告。 | 交付 |

關鍵候選檔案 SHA-256：

```text
622a21734f7ce464aedf156ef06d5900a4c8c1266acd4e1581cdcef51f339389  src/line_backup_batch/notes.py
8d279a16711942852f5e2d4882fd8903f2341905b1259857b11c58d63fb0c905  src/line_backup_batch/notes_evidence.py
c7cfeec43797f56f8cc2bd27d49b9a67436c49449a58d96c1c37f87f9896b5e6  src/line_backup_batch/notes_capture.py
19fca3ebd24cd866ea0eb380c877a468bb9ad3f27a60111a6763caef48191c61  tests/test_notes_evidence.py
9f446be5e1f3e43a5e7184b0ec8b301784d560d10ccee480d4ad5b506690406c  tests/test_notes_capture.py
9507eb9e97c9e3775c300128f4f30d678f5ece7d99934be1e22f13bb8a8034bf  tests/test_notes_locks.py
b82dd3d1b27783d574e37393ed04db198c81c43cb2b283c4ec97bf15d199e180  tests/test_notes_records.py
ea11cfc0baf6d181949c1e2a3851b59522c311025bf66c9ce8daf12a07262899  tests/test_notes_regressions.py
f47179eaca6dff029c9bf621c06ff57903db4d6fdd0ab6b908b8c1f96a3be65b  tests/test_notes_e2e_media.py
```

受保護檔案 `src/line_backup_batch/media_verify.py` 未修改，SHA-256 仍為 `7c8051d1699449434dbaa41682a5a50f949858d593ee39cd2a1f38a1e1c6dd99`。起始 `notes.py` SHA-256 為 `9cdb1f75d19ae61939b98fbea3c0fbe95367e8caef6f69b1c3724946804c36f9`。daily、Swift decoder、OCR、相簿 Skill／測試、AGENTS、全域政策與舊任務均未修改。

## 實際檢查與結果

環境：macOS；工作目錄 `/Users/hsiaojohnny/dev/Line_backup`；`/usr/bin/python3` 為 Python 3.9.6；影片工具為 `/opt/homebrew/bin/ffmpeg` 與 `ffprobe` 7.1.1。以下 stdout／stderr 均保存於 `.local/line-backup/tasks/20261101-notes-s1-implementation/`。

| 檢查 | 命令 | Exit | 結果與證據 |
|---|---|---:|---|
| capture 針對性 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest -v tests.test_notes_capture` | 0 | 10 tests OK；`test-notes-capture-final.txt` |
| lock 第一輪 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest -v tests.test_notes_locks` | 1 | 6 OK、1 FAIL；只有測試對 `OSError` 字串的預期錯，產品分類正確；`test-notes-locks-final.txt` |
| lock 修正後 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest -v tests.test_notes_locks` | 0 | 7 tests OK；`test-notes-locks-final-r2.txt` |
| daily 回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 tests OK，319.212s；`final-daily-records.txt` |
| notes CLI | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 完整 usage；`final-notes-help.txt` |
| notes 全回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 113 tests OK，11.730s；`final-notes-tests.txt` |
| whitespace／patch | `git diff --check` | 0 | 無輸出；`final-git-diff-check.txt` |

事實：

- v2 reader 可從 ledger 自身 evidence 重開；來源 source path 移走後仍可驗證 saved bundle；legacy opaque 保持 `LEGACY_OPAQUE`，新寫入拒絕舊 opaque。
- 新 page／post／media 的 v2 evidence 若 context 的 `scan_id` 為 `UNKNOWN`，會以 `EVIDENCE_SCAN_CONTEXT_REQUIRED` 拒絕；v1 opaque 保持相容。
- capture 每次建立新 receipt；同一命令不覆寫前次 refusal／success；child 僅啟動一次；保存失敗時 wrapper 仍為 70 並保留已知 `child_exit`。
- 只有尚未取得 flock 時的 `EAGAIN`／`EWOULDBLOCK` 進入 `NOTES_LOCK_BUSY`；其他 flock `OSError`、非 flock EAGAIN、mutation、resume 不標 `retry_safe`。exit 70 仍為 `INTERNAL_ERROR`／`UNEXPECTED_EXCEPTION`。
- pre-S1 frozen fixture 的 event bytes 與 legacy opaque bytes 在讀取後不變；測試只重綁根路徑及既有 hash chain，不以新 writer 重造舊格式。

推論：

- 上述離線測試提高 S1 行為一致性信心，但不證明 LINE 真實畫面、GUI 控制定位、chooser／popup、跨 Session 恢復或服務端原始位元同一性。

未知／限制：

- 本輪沒有真實 input trace、原 UNKNOWN 晚到結果、原始媒體、正式 ledgers 或 Owner 實機資料可核對；不得以 synthetic fixture 回填。
- S1 的 T1 audit／page correction、S2 的種類更正／intent-v2／到期事件／coverage、S3 的操作文件均未執行。
- 本報告不是 implementation Simplicity Review，也不是獨立 Acceptance；helper 意見不能替代。

## 未執行項

以下全部維持 `NOT_RUN`，沒有以單元測試冒充：

- S2／S3 全部工作、T1 audit／page correction、B2 種類更正／intent-v2、C 到期事件、D coverage／scan 改動。
- GUI、LINE 操作、真實 notes `lists`／`summary`／`resume`、下載 attempt、chooser／popup、混合附件、影片真實下載、跨 Session 恢復。
- G0、D1、D2、G1／G2、真實帳本／媒體驗證與任何部署。
- implementation Simplicity Review、獨立相容驗證、Acceptance 與 Issue 關閉。

## 停止條件與人工交接

本切片依交接要求在 S1 後停止。建議 Owner 在另一個正式主 Session 讀取本次精確 commit、本報告與私有證據，啟動 implementation Simplicity Review；不得由本 Implementer 自行開始 S2／S3、Reviewer、Acceptance、merge master、force-push 或關閉 Issue。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: S1_IMPLEMENTATION_CANDIDATE_READY
IMPLEMENTATION_STATUS: S1_IMPLEMENTED_LOCAL_CHECKS_PASSED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: S1_LOCAL_CHECKS_PASSED_S2_S3_AND_REAL_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

這些狀態彼此分離；S1 離線候選完成不表示全問題 DONE，也不簽發 Acceptance。
