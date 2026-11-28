# 20261128 記事本 Pre-Bind continuation 離線驗證

## 範圍與結論

- Tester worktree：`$TESTER_WORKTREE`（下列相對路徑與命令均以此 worktree 為工作目錄）。
- 綁定版本：detached HEAD `85e81009ad16c3b7659cca2ca249d79915226ee0`。
- 只讀該 worktree 的 Skill、references、手冊與 mock 測試；沒有呼叫 CUA、查看／切換 LINE、讀寫真實帳本、執行 `bind` 或下載。
- Pre-Bind 規則定義明確順序：完整 `lists` capture → CUA 同次原件落地及讀回 → 入口與全部候選核對 → evidence bundle／必要時建帳 → bind、舊交易處理、普通完整掃描。尚未完成的前置步驟是 `NOT_RUN`，不是自動成立的環境 blocker。
- 離線合成 `notes_capture ... lists --collection <絕對合成路徑>` 得到 `status=COMPLETE`、child／outer exit 0、可解析的空列表 JSON；receipt 對 request/stdout/stderr/result 的 bytes 與 SHA-256 全部相符。
- 指定 initial-observation mock 測試 7 項與 notes-capture 測試 10 項皆成功。它們驗證文件化 helper／wrapper 程式在 mock／合成輸入下的分支，不驗證真實 CUA、LINE 前景或日常備份完成。

## 候選依據

依 repo 根目錄 `AGENTS.md`：日常記事本入口是 Owner 開啟單一記事本列表後提交正式 Prompt；本任務雖採獨立 Tester 角色，但測試範圍另受使用者明示的離線、合成與不得操作真實資料限制。

正式入口為 `docs/LINE相簿備份_使用手冊.md` 附錄 C「記事本正式 Prompt」。它要求 Owner 交接前景後，Agent 自主查全部帳本、完成盤點、下載和恢復；不要求 Owner 另下開始指令。

`.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` 的「啟動與帳本對帳」第 276–282 行規定 Pre-Bind 五步：

1. 以 `notes_capture --output-root ... -- lists --collection ABS_COLLECTION` 取得完整 stdout 與 COMPLETE receipt；非零、不完整或不可解析時保留原狀，不進下一步。
2. 同一 CUA Node runtime 載入 `cua-evidence-tools` 後呼叫 `captureAndPersist`，持久保存並讀回同次 AX／截圖。未載入（含 `CUA_EVIDENCE_TOOLS_NOT_LOADED`）或未呼叫屬 `NOT_RUN`，不可宣稱環境不支援。
3. 用已落地讀回的 observation 核對入口並比較全部 N 個候選及 active hint。
4. 既有帳本用既有 list key 建立 observation／handoff evidence bundle；只有有證據的新列表才走 list-key／init。
5. bind 後處理舊交易及 open scan，再開始普通完整掃描。

`.agents/skills/line-notes-agent-cua/references/evidence-template.md`「CUA 觀察原件落地」提供 helper 實作及 readback 契約；`tests/test_notes_input_helper.py` 中的 `NotesInitialObservationBlockTests` 對應初始 observation 分支；`tests/test_notes_capture.py` 對應 capture receipt／失敗處理。

## A–F 情境判定

下列「下一工具」是依候選文件與已執行 mock 的行為推演，不是任何真實 CUA／GUI 工具紀錄。所有情境均不授權真實列表 bind 或下載。

| 情境 | 下一個工具／判斷 | 是否繼續 Pre-Bind | 根據與邊界 |
|---|---|---|---|
| A. 只有直接 `notes lists` 重導完整 JSON，未呼叫 wrapper | 對明示的合成絕對 collection 執行 `notes_capture --output-root ABS_PRIVATE_TASK_DIR -- lists --collection ABS_SYNTHETIC_COLLECTION`；讀 receipt 所指向的 stdout，核對 child exit、COMPLETE、JSON 與 hash | 只有 receipt 完整、child exit 0、stdout 可解析後才到 B | 本次已實跑合成 A；見下方「A 的實測」。直接重導檔不能代替 wrapper receipt。該命令只查指定合成 collection，不讀預設 collection。 |
| B. receipt 合格、看到 screenshot 但未保存；狀態為 `CUA_EVIDENCE_TOOLS_NOT_LOADED` | 在同一 CUA Node runtime 載入文件定義，再實跑 `captureAndPersist` 取得同次 AX／截圖並讀回 | 繼續；`NOT_LOADED` 是未執行，不是環境失敗 | 文件明文將未載入／未呼叫定為 `NOT_RUN`。若之後實際 helper 回傳錯誤或明確 blocker，才按該結果停在 bind 前。未呼叫 CUA 驗證這個實機分支。 |
| C. wrapper 為非零或 incomplete | 保留該 receipt／原始檔；查明 `child_exit`、signal、wrapper `status` 及缺失資產，不重播可能有副作用的 child | 不進第二步，保持 Pre-Bind；是否可修正取決於具體失敗證據 | 文件明定非零／incomplete／不可解析不進下一步。Capture wrapper 本身標示不重試 child。不能以另一份直接重導輸出補成 COMPLETE。 |
| D. `ready_for_bind=true`，但 `CAPTURE_BOUNDARY=MISSING` | 先保留原 observation／診斷證據，不 emit／不 bind；只有取得新證據或已證實可修正原因，且原等待／重試上限仍允許時，才用新 observation ID 重新取證並驗證 | 目前 observation 不可繼續；缺少 `RECORDED` 本身不觸發自動重抓。原因未查明或無新證據時保留阻塞 | mock 有實測：`CAPTURE_BOUNDARY:MISSING` 會失敗閉鎖且不 emit；沒有實機 capture 紀錄。不可把 ready 欄位單獨當成 RECORDED，也不可僅因缺 RECORDED 自動重跑。 |
| E. receipt、readback、RECORDED 都有效，但候選無法區分 | 唯讀展開所有候選的 identity／post anchors，再檢查是否有可新增的當次區別證據 | 可繼續唯讀消歧；身分未唯一前不得封裝為該列表、bind、scan 或派送 | Skill 要求全候選、多訊號交叉核對。無法消除的歧義是具體身分 blocker，依影響範圍保留／回報；不得只依名稱選帳或新建空帳。未用真實候選實測。 |
| F. receipt、readback、RECORDED 都有效，但尚未比對全部候選 | 從 COMPLETE receipt 的 `stdout.bin` 列出全部 N 份候選與 active hint，逐一比對 identity／posts | 必須繼續 Pre-Bind 第三步；不得提早停止或 bind | 文件明定 COMPLETE capture 後須展開全部 N 個候選；空同名結果、active hint 或名稱本身皆不足以跳過交叉核對。此分支為文件推演，未讀任何真實帳本。 |

## A 的合成實測

以下命令以 Tester worktree 根目錄為目前工作目錄；`TASK_PRIVATE_DIR` 位於此 worktree 的 `.local/line-backup/tasks` 下。

```sh
TESTER_WORKTREE="$(git rev-parse --show-toplevel)"
TASK_PRIVATE_DIR="$TESTER_WORKTREE/.local/line-backup/tasks/notes-prebind-continuation"
PYTHON=/usr/bin/python3
```

合成輸出根：

`$TASK_PRIVATE_DIR/`

唯一指定 collection 為執行前不存在的 `$TASK_PRIVATE_DIR/synthetic-collection-0001`。實際命令：

```sh
PYTHONPATH=src "$PYTHON" -B -m line_backup_batch.notes_capture \
  --output-root "$TASK_PRIVATE_DIR/captures" \
  -- lists --collection "$TASK_PRIVATE_DIR/synthetic-collection-0001"
```

結果：wrapper outer exit 0；`status=COMPLETE`；child exit 0；signal null；`dispatch_authorized=false`。receipt 位於 `$TASK_PRIVATE_DIR/captures/notes-capture-052d592924e34864bf6ff6d27112aedd/`。receipt `complete.json` 與 `result.json` 均記 child exit 0。`stdout.bin` 282 bytes，JSON 可解析，內容為 `line-notes-index/v1`、`lists=[]`、`active_hint=null`，collection 欄位正是上述 synthetic path。stderr 為 0 bytes。

Receipt readback 核對：

| 資產 | bytes | SHA-256 | 完整性 |
|---|---:|---|---|
| `request.json` | 1617 | `5304e492f8b0487c6b713aa798e8c66321cf44ecca1ec44f240fc6f4b0f98d1e` | bytes／hash 相符 |
| `stdout.bin` | 282 | `24a0795bcd822f424288a34d1ed3256ddda68508075af91b6762a9fb94ef7e91` | bytes／hash 相符 |
| `stderr.bin` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | bytes／hash 相符 |
| `result.json` | 299 | `0d1ed4179a4efaff02a948092ff162bd8ff8ab2e60e337828a1124f5a18875c8` | bytes／hash 相符 |

原始合成輸出保存在 Tester worktree 私有 task 目錄；沒有複製至 Git 報告或讀取主要 repo 預設帳本。

## 離線命令與退出碼

| 命令 | 結果 |
|---|---|
| `PYTHONPATH=src $PYTHON -B -m line_backup_batch.notes_capture --help` | exit 0；確認 wrapper flags |
| `PYTHONPATH=src $PYTHON -B -m line_backup_batch.notes lists --help` | exit 0；確認 `--collection` |
| 合成 collection 的 `notes_capture ... lists --collection ABS_SYNTHETIC_COLLECTION` | outer 0、child 0、COMPLETE；完整性見上節 |
| `PYTHONPATH=src $PYTHON -B -m unittest discover -s tests -p test_notes_input_helper.py -k NotesInitialObservationBlockTests` | exit 0；7 tests，OK |
| `PYTHONPATH=src $PYTHON -B -m unittest discover -s tests -p test_notes_capture.py` | exit 0；10 tests，OK |
| `git diff --check` | exit 0 |

另有一次測試命令的工具呼叫因 workdir 拼字錯誤（`notes-daily-2028`）在建立 process 前遭拒，沒有 child 執行且沒有 exit code；以正確 worktree 路徑重跑後取得上述 exit 0。這不是測試失敗或產品錯誤。

## 實測、推演與未測範圍

**實測：** detached HEAD 與 worktree 狀態；該版 Skill／references／手冊文字；合成 collection 的 notes_capture；wrapper receipt bytes／hash／child result；兩個指定 unittest 命令。

**Mock 行為實測：** `NotesInitialObservationBlockTests` 的 7 項涵蓋 helper 未載入時不 capture／不 emit、成功捕捉並 emit 落地 bytes、路徑／capture blocker 不 emit、AX no-change、CAPTURE_BOUNDARY missing 不 emit、readback drift 不 emit。測試的 CUA 與畫面內容均為 stub／合成資料。

**文件推演：** A–F 表格中工具選擇、何時繼續 Pre-Bind、何時停在 bind 前的規則應用。F/E 的候選歧義判定不是由測試自動替 Agent 做；必須由 Agent 依完整候選及原件作語意核對。

**未測：** 原生 Mac CUA 可用性、runtime helper 真實載入、LINE 畫面／前景、capture/readback 在真實工具上的結果、真實帳本候選、bind、全列表盤點、下載、chooser、download-check、completion、跨 Session 恢復及任何真實 E2E。上述皆 `NOT_RUN`；本離線結果不授予實機 PASS，也不證明不同 Agent／模型均能完成正式備份。

## 狀態

- `PRIMARY_OUTCOME_STATUS`: `PASS (offline scope only)` — 合成候選驗證與情境判定完成；不代表實機備份。
- `IMPLEMENTATION_STATUS`: `PASS (offline scope only)` — 合成 `notes_capture` receipt 與指定 mock／wrapper tests 成功。
- `CORE_ACCEPTANCE_STATUS`: `NOT_RUN` — 未執行正式入口或實際備份。
- `REQUIRED_VERIFICATION_STATUS`: `PASS (offline commands only)` — 指定離線命令已執行；實機驗證 `NOT_RUN`。
- `INDEPENDENT_ACCEPTANCE_STATUS`: `NOT_RUN` — 離線 Tester 結果不等於 Owner／獨立實機驗收。
- `TASK_CLOSURE_STATUS`: `DONE (offline task only)` — 本次離線候選驗證與報告已完成；正式備份任務仍未測。

## 下一步建議

候選已明定：helper 未載入或未呼叫屬 `NOT_RUN`，下一步是載入定義並實際執行 `captureAndPersist`；只有實際錯誤／blocker 才停。後續以正式實機驗證核對 Agent 是否能自主接續並完成任務；本離線報告不代替當次前景與正式任務授權，也不預判實機結果。
