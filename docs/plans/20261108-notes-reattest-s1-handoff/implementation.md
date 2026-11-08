# 記事本 list directory 重新見證 S1 實作報告

## 結果與版本

- Repo：`/Users/hsiaojohnny/dev/Line_backup`
- 分支：`feature/line-notes-media`
- 起始本地與遠端 HEAD：`52fef4ab95c5843db4793c9dd5ebab5552bfb60e`
- 起始工作樹：既有未追蹤 `codex-session-01a1bab6-c1b6-75b0-a7e0-bcf9dbf72d2c.md` 保持未讀、未修改、未 stage。實作只使用下列明列路徑。
- 核准設計：`../20261108-notes-volume-identity-reattest/plan.md` v2；Owner 已明示接受 witness 信任模型及 clone 剩餘風險。S1 不因此取得真實帳本、LINE、下載或 S2 授權。
- 核准來源 SHA-256：plan `937e86eb276ed025c41617d7a5fafc6c80259ea7bc0314e31fa5fc84eb3a858b`；原 handoff `a6bd06190ca677363ecb2e08847d9863d5daf99c24bb79135f3a8ae9752d71e8`；Plan Review v2 `aa97bfe28f113123331ed3a4eb05724db6ba876f487d71fb8cfebe81ba3eba21`；Simplicity Review v2 `3e09bc50544d535f1979e10086eef3092d24e53153e2fffeb85e15107a4d6f01`。本輪重核上述四份 bytes，均相符。起始 `notes.py` 與 handoff 紀錄一致，SHA-256 為 `80d0ab5b61b27eee4b5ee9727eef6176ba5a489365ae1651e27f0295fc1170b0`。

## 實作內容

只新增 `notes reattest preview --records-root R --session-id S` 與供後續切片共用的 bounded witness builder。程式會在現有 records lock 內驗證帳本與 session，要求唯一未 activation 的 OPEN_BATCH；拒絕已有 reattest／v3 intent／candidate／activation／未完成 publish 等不支援狀態。只接受 canonical 專案內 root/list path、list path 與 inode 不變且 device 不同的第一次預覽。device 相同回 `NO_CHANGE`，附固定空 witness。

device 改變時，builder 收集該 list 直接子目錄中的每份 v2-intent completion 與所有登錄 staging。它核對舊新 device 單一映射、completion 目錄 inode、完整檔名集合、regular file、無 symlink、`nlink=1`、檔案 inode／size／mtime／ctime／SHA-256，並在讀取前後重查檔案與目錄穩定性。已完成 attempt 的舊 staging 可不存在；未解 attempt 必須仍存在且空白。未知 list 項目、非空／缺少 unresolved staging、scope 外 `LOCAL_CHANGED`、不支援布局及 witness 缺失均拒絕。scope 內 UNKNOWN 僅被觀測，不會因此解除。

成功輸出固定 schema、穩定排序、witness SHA-256 及 preview digest，並固定 `dispatch_authorized=false`、`external_copy_verified=false`、`real_line_e2e=NOT_TESTED`。read-only lock busy 會標為可安全重試；已知 reattest 拒絕回傳分類與事件引用。未新增事件 kind、confirm、binding projection、freshness gate 或任何可寫轉接路徑。

| 路徑 | 變更 |
|---|---|
| `src/line_backup_batch/notes.py` | 新增 preview、bounded witness、CLI dispatch 及 read-only lock/refusal 分類 |
| `tests/test_notes_reattest.py` | 新增 13 個合成測試，覆蓋成功／NO_CHANGE、必填參數、witness 缺漏與名稱集合、completion/staging 異動、list／completion inode、符號連結（含祖先）、hardlink、device mapping、scope 外 LOCAL_CHANGED、純讀快照 |
| `tests/test_notes_locks.py` | 新增 reattest preview lock busy 的 retry-safe 分類案例 |
| 本報告與原任務 `progress.md` | 記錄實作、檢查與交接狀態 |

沒有修改原 plan、handoff、審查報告、Skill、手冊、daily／evidence 工具、事件 schema 或真實備份資料。後續 S2 的 confirm／事件 graph／有效 binding projection／replay／fresh scan gates，以及 T3–T11、實機 volume、LINE、跨 Session、獨立 acceptance 均未執行。

## 指定驗證

環境：`/usr/bin/python3` 版本 `3.9.6`；Darwin 27.2.0，`arm64`。三項命令均在 repo 根執行，測試只建立並使用 `.local/line-backup/tasks` 下的合成 fixture。

| 實際命令 | Exit | 結果 |
|---|---:|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py` | 0 | 13 tests，OK |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | CLI help 列出 `reattest`；stderr 空 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py` | 0 | 7 tests，OK |
| `git diff --check` | 0 | 無 whitespace error；此為補充差異核對，不冒充上述指定測試 |

各命令 stdout、stderr 與 exit 檔保存於 `.local/line-backup/tasks/notes-volume-reattest-s1-20261108-impl/logs/`。Unittest 的 dots／summary 寫在 stderr；兩個測試命令 stdout 為空。完整回歸、受控 volume、真實帳本、LINE GUI、下載／解碼、跨 Session 與獨立 acceptance：`NOT_RUN`。

合成樹純讀證據由測試的 `snapshot_tree` 對每個案例前後比較，條目包含相對路徑、mode、device、inode、size、mtime／ctime，以及 symlink target 或 regular file SHA-256；比較範圍包含 fixture records/events、evidence、active-hint fixture 與媒體樹。13 個案例通過；成功預覽、同 device `NO_CHANGE` 及拒絕 helper 的完整快照相等。合成媒體只含測試文字 bytes；完成樹有登錄的單一合成檔，另含空 unresolved staging 與已完成而缺席的 staging；拒絕案例覆蓋額外項目、缺檔、symlink／hardlink、metadata/device 漂移及 scope 外異常。fixture 由 unittest 暫存目錄建立並在 teardown 刪除；未讀寫真實帳本、照片、影片或 active hint。

## 狀態、未知與交接

仍未知的事包括實際 device 變化原因、真實 list 的完整允許名稱集合、matching clone 是否與原物件相同、舊 UNKNOWN 是否晚到，以及轉接後其他 gates 是否可通過。本信任模型不能識別完美 clone。這些未知不由合成測試或 commit/push 消除。

```text
PRIMARY_OUTCOME_STATUS: S1_READ_ONLY_PREVIEW_CANDIDATE
IMPLEMENTATION_STATUS: IMPLEMENTED; NO_WRITABLE_CONFIRM_OR_BINDING_CHANGE
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_THREE_S1_CHECKS; FULL_REGRESSION_AND_REAL_ENVIRONMENT_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_START_OF_IMPLEMENTATION_SIMPLICITY_REVIEW
```

交付候選由本報告、上列程式／測試差異及本次 delivery commit 共同識別；commit SHA、commit 本體核對與 push 後遠端精確 HEAD 留在本輪交付紀錄及最終回覆。下一步由 Owner 另啟 Simplicity Reviewer（Implementation），提供本報告、核准 plan、handoff、精確 commit／diff 與私有檢查紀錄。審查前不開始 S2、不操作真實資料、不宣稱獨立接受或結案。
