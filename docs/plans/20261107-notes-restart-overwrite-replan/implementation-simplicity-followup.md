# 記事本中斷恢復 S1：Simplicity 審查後續實作報告

## 授權、基線與範圍

本輪依 Owner 提交的 Implementer Prompt 與 [S1 實作簡潔性審查](simplicity-implementation-review.md) 處理兩項非阻塞建議。基線為 branch `feature/line-notes-media`、HEAD `4b2dc7ccf8589b8b928b96eb1c4061644c6d3c35`；開工時 index、tracked 與 untracked 均無待提交差異，遠端 HEAD 相同。

本次只實作 `SI-N01`、`SI-N02`，沒有修改計畫、schema、資料語意或正式入口。`SI-U01` 的同媒體第二次 generation 恢復仍 `NOT_RUN`；本輪不把它靜態推定為通過或失敗。整體接受、真實 LINE／CUA、跨 Session 實機恢復、S2 文件整合與獨立 Acceptance 均不在本輪範圍。

## 變更內容

### SI-N01：收斂 v3 關係檢查

`NotesRecords._validate_event_graph()` 不再重複核對 v3 intent 的 confirmation、scope 與 prior 關係。一般 attempt 的媒體與目的地檢查仍保留；v1／v2 的 recovery guards 仍保留。v3 關係改由既有 `_restart_projection()` 的單一 replay 路徑核對，避免兩份實作漂移。

新增 `test_restart_replay_rejects_v3_prior_attempt_drift`：建立一筆具有 prior attempt 的 v3 intent，將 ledger 內合成事件的 `prior_attempt` 改為 `null`，重開後仍須以 `RESTART_PRIOR_ATTEMPT_CHANGED` fail closed。

### SI-N02：共用保留檔名蒐集

`_target_names_for_directory()` 現在同時服務一般發布與 restart 版本目錄；刪除逐字重複的 `_restart_target_names_for_directory()`。普通與 restart 各自的目錄、inode、scope guards 沒有改變。

## 精確候選

| 檔案 | SHA-256 |
|---|---|
| `src/line_backup_batch/notes.py` | `d597fab57fcb0d305e26c0fadc630cb65ff74d9ec05c06c0d0817b9f8eaea0ab` |
| `tests/test_notes_restart.py` | `e65dd506b289648d91c363bea37a5b01d343b3142c735358849a9abe3e8faafa` |

產品／測試 diff 為 2 檔、36 insertions／51 deletions。Git commit SHA 由提交及推送後的 receipt 另記，不在本文件預填。

## 實際驗證

環境為 macOS 27.2（26B123、arm64）、`/usr/bin/python3` 3.9.6、Node v24.22.1；工作目錄為 repo 根目錄。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
# 18 tests, OK, 3.812s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
# 154 tests, OK, 16.803s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
# 73 tests, OK, 318.270s, exit 0

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
# exit 0; help includes restart

PYTHONPATH=src /usr/bin/python3 -B -m py_compile src/line_backup_batch/notes.py tests/test_notes_restart.py
# exit 0

git diff --check
# exit 0
```

記事本全套輸出中的 `INVALID_--SIGNALS` 與 evidence JSON 來自既有負向案例，最終 exit 0。以上沒有操作真實 LINE、GUI、chooser、真實帳本或私人照片／影片。

## 事實、推論與未知

- 事實：審查在 `4b2dc7c` 對首輪候選 `7f1d978` 判定 `PASS（僅 S1 簡潔性）`，並提出 `SI-N01`、`SI-N02` 與待查點 `SI-U01`。
- 事實：本輪產品／測試只修改 `notes.py` 與 `test_notes_restart.py`，另新增本報告並追加舊報告指向；規定離線回歸全部通過。
- 推論：移除重複 v3 關係檢查可降低同一不變量由兩處維護的漂移風險；共用檔名 helper 不改變普通與 restart 的發布邊界。
- 未知：`SI-U01` 的動態結果、真實 GUI 中斷、跨 Session 實機恢復、C08 完整故障矩陣、C10／C12、Owner 日常 Prompt 試用及最終產品接受。
- 界線：離線測試、簿記、檔案解碼與本實作者自評均不等於獨立接受或整體完成。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: SIMPLICITY_REVIEW_FOLLOWUP_IMPLEMENTED
IMPLEMENTATION_STATUS: S1_CANDIDATE_UPDATED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

## 下一步建議

由 Owner 決定是否另交 S2 或適用複查。第一個功能釐清點仍是 `SI-U01`：同一媒體已啟用後，再確認另一個 generation 的恢復；其後再按既有計畫補 C08／C10／C12、整合唯一日常記事本 Prompt／Skill／手冊並安排真實試用。本報告不授權自動啟動下一角色、操作真實資料、合併 master 或宣稱整體 DONE。
