# 記事本 active 定位拒絕：高階根因分析

## 本角色結論與精確候選

- 角色：Owner 指定的 High-Reasoning Reviewer；診斷及建議，不執行修復。
- 結論：`ANALYSIS_COMPLETE`。已重現測試子程序的 active locator 污染機制；原事故歸因為高度吻合的推論，未冒稱歷史寫入事件已直接證實。
- 單一根因識別：`NOTES-ACTIVE-LOCATOR-CHILD-ISOLATION`。
- 故障：日常 Agent 從 `lists.active_hint` 取得 task-local root，`memory` 回覆 `CANONICAL_NOTES_RECORDS_REQUIRED`，停在列表綁定前。
- Repo：`Line_backup`；分支：`feature/line-notes-media`；分析候選：`1c6a4cae0bb140cd74894b7b9bf16f1682d3ae6e`。初始 tracked／untracked 工作樹乾淨。
- 輸入：`docs/問題提報單_記事本帳本定位拒絕_20261115.md`，由 Tester 經 Herdr 確認是本次高階分析用的故障提報。其引用的事發前程式 HEAD 是 `cdb6b1e42de23808f3b86e695b6049704d60d436`；本候選增加提報文件。
- 授權：唯讀來源分析、同角色研究、合成隔離診斷、分析文件及 commit／push。未取得修帳、搬移、刪 active、重新備份或 GUI 派送授權。

**精準建議：修正 `tests/test_notes_records.py` 的 CLI 子程序隔離。父程序的 `mock.patch` 不會跟進重新啟動的 Python。先保護測試執行邊界，不放寬產品的 canonical／註冊／禁止重送 gate。**

## 已證實的因果鏈

| 環節 | 直接證據 | 能證明的範圍 |
|---|---|---|
| 父程序 mock writer | `tests/test_notes_records.py:51`、`:67` | fixture 在父程序替換 `_write_active_hint` |
| 新 Python 不繼承 mock | `tests/test_notes_records.py:190` | `subprocess.run` 以新 Python 載入 `line_backup_batch.notes`，沒有注入該 mock 或隔離 locator |
| CLI 接受 bind | `tests/test_notes_records.py:283`、`:294` | context 測試有成功的 CLI bind；不只是拒絕路徑 |
| 真實 writer 寫專案 active | `src/line_backup_batch/notes.py:496`、`:517`、`:2686` | bind 追加事件後呼叫 writer；預設路徑與 fixture collection 分離 |
| 清除 fixture 留下 locator | `tests/test_notes_records.py:72` | teardown 移除合成帳本，不清除／隔離子程序寫的全域 active |
| 缺目錄被拒 | `src/line_backup_batch/notes.py:750` | 缺目錄時在讀帳本註冊前回該 canonical 拒絕碼 |

造成風險的 CLI context 測試由 commit `74aceac8529bbde9e53a10565e7ebee3c592a875` 加入；實際查核命令為 `git log -1 --format='%H %s' -L 254,300:tests/test_notes_records.py`。這是程式來源版本證據，並非該測試在事故前執行的證明。

本輪隔離診斷保留真正的子程序 writer，只把父、子程序的 `_active_task_path` 指向專案私有診斷目錄內的合成 locator。沿用既有 `test_bind_omitted_context_inherits_saved_context`；沒有執行未隔離的原測試或整套回歸。

| 合成步驟 | 實際結果 |
|---|---|
| 錯誤 context 的 CLI bind | child exit 4，`WRONG_NOTES_CONTEXT`，locator 尚不存在 |
| 正確 context 的 CLI bind | child exit 0，locator 已建立，目標合成帳本存在 |
| 原 fixture teardown | 合成帳本目錄移除，診斷 locator 仍指向舊路徑 |
| 同一合成 locator 的 memory | child exit 4，`CANONICAL_NOTES_RECORDS_REQUIRED` |
| 比對原事故 capture | hint session 精確等於測試 CLI bind session；路徑同有 `notes-records-` fixture 前綴 |

這證實「測試隔離缺口 → 子程序寫 locator → 清 fixture 後留下失效定位 → memory 拒絕」的機制。未碰真實 active 檔、真實帳本或照片；合成 locator 留在私有診斷目錄，供核對。

## 事實、推論與未知

### 直接事實

1. 原 `lists` stdout 與 receipt 讀回 SHA-256 均符合提報單。stdout 列出六份候選；hint 的 root、ID 都不符合其中任一列。
2. hint 路徑位於專案私有 tasks，具有現行 fixture 的 `notes-records-` 前綴。原 capture 的 session 與 `tests/test_notes_records.py:285` 的 CLI bind 字串常數完全相同；不是該 fixture 父程序最初的 session 常數。
3. `NotesCollection.lists()` 只回所選 collection 的摘要並附上獨立 active hint，沒有將 hint 與該 collection 索引交叉驗證，見 `notes.py:624`。因此「第七個 hint」不能直接等同第七份真實帳本。
4. `CANONICAL_NOTES_RECORDS_REQUIRED` 檢查目錄存在與路徑等於嚴格解析結果；`notes-backup-records/` 只是預設 collection。專案內自訂 collection 有正式支援，見 `notes.py:554`、`:750`。
5. 四個合成 canonical 探針中，缺目錄、regular file、symlink 都產生相同拒絕碼；現存且實體路徑一致的自訂 UUID 目錄通過第一 gate。後者刻意以 mock 截止在 collection 註冊前，**不是完整帳本通過**。
6. Tester 回覆：當時只對 hint root 呼叫 memory；曾比對部分畫面與候選摘要，但未唯一確認帳本。當次拒絕沒有 capture receipt／exit code；本輪合成 exit 4 不補填成原事故 exit code。

### 有根據的推論

- 最符合現有證據的來源是上述 CLI context 測試留下的 locator。session 精確匹配、路徑前綴、成功 writer 路徑及合成拒絕鏈相互支持；缺少事故當次 writer trace，仍標「高度吻合」，不標歷史歸因已證實。
- Agent 流程也有可核對的偏差：reference 已要求 hint 的 root＋ID 對應候選，不符時保留並核對全部候選。直接對不符的 hint root 查 memory 未遵循選帳步驟，見 `references/download-and-ledger.md:230`、`:232`、`:236`。這不能反推其餘候選必然有匹配，也不能稱繼續就一定能完成備份。
- AX-only 過早停止、capture wrapper 首次參數錯誤與保存目錄缺席是獨立的執行偏差；它們不會使既有 active locator 指向測試目錄，不混為本根因。

### 尚未證實／替代解釋

- 原 hint 目標在事故當時究竟缺席、變成非目錄、經 symlink 解析，或檢查間變動：`UNKNOWN`。未對真實目標執行 metadata／內容讀取。
- 原事故前哪一次測試或診斷實際寫了 active、是否有其他程序使用相同 session：`UNKNOWN`。既有 commit 的回歸成功紀錄不等於 writer trace。
- 真實目標列表對應六份候選的哪一份、是否存在索引外的真實歷史：`UNKNOWN`。未完成來源列表匹配，不能將 hint 判作可刪垃圾。
- 若有直接寫入紀錄指出另一合法流程，會推翻本事故的測試來源歸因；不會抹除已重現的測試隔離缺陷。
- 若事故當時有完整 metadata 證明目錄存在、實體解析一致且未變動，需重新檢查當時版本／原輸出；不能繼續以缺目錄解釋。

## 嘗試歷史與新增資訊

| 次序／性質 | 行為 | 新資訊／停止點 |
|---|---|---|
| 原日常流程 | capture 語法錯誤後修正，lists 成功；hint memory 一次拒絕 | 原拒絕 exit 未保存；未下載。非修復嘗試 |
| 本輪來源核對 | 同版本程式、reference、Tester 與原 capture 雜湊／去識別投影 | 釐清 canonical 非預設目錄限制；辨識 hint session 對應 CLI 測試 |
| 本輪合成診斷 1 | 四種路徑第一 gate 探針 | 相同錯誤碼不能單獨判斷缺席或 symlink；未重試真實 root |
| 本輪合成診斷 2 | 隔離 locator 後沿用一個 CLI bind 測試，再讀已清除的合成 root | 跨程序 mock 缺口及完整失效鏈重現；至此停止，不增加第三次試探 |

本輪沒有產品修復嘗試、沒有重派或修帳。未因換 Session 重設既有歷史。兩項合成診斷各帶來新資訊，沒有以重跑耗用嘗試額度。

## 唯一建議路線：`IMPLEMENTER_FIX`

這是交由 Owner 決定的下一步建議，未啟動 Implementer。

- **範圍：**僅修 `tests/test_notes_records.py` 的父、子程序 fixture 邊界與必要回歸斷言；可參考 `tests/test_notes_locks.py:29` 的 child bootstrap 模式，不改產品 CLI、ledger schema、正式 Prompt 或日常啟動步驟。
- **具體修法：**在父程序與 `run_cli` 的每個 Python 子程序載入 notes 後、任何 notes 動作前，把 active locator 定位到該 fixture 的專用合成檔。不可只靠父程序 `_write_active_hint` no-op；子程序須能真的寫合成 locator，才能驗證成功 bind 的副作用。
- **回歸：**成功 child bind 後，assert 合成 locator 的 root／ID／session 對應 fixture；拒絕 child bind 不變更它。用測試控制的外層 sentinel 證明 child 沒有寫出 fixture；讓失敗退出／cleanup 同樣保持隔離。不得為了測試先讀寫真實 active 檔，或以事後恢復全域檔案替代隔離，避免覆蓋並行使用者的合法更新。
- **成功檢查：**先隔離後執行該測試；三個 child 交易與預期退出碼成立；外層 sentinel bytes 不變；fixture 清除後不產生供日常流程使用的失效 locator。再由實作者執行專案相稱回歸。單元測試仍不是實機日常備份成功。
- **停止條件：**若需修改真實 active／index／events、搬移／恢復資料、放寬 canonical 或新增產品遷移功能，停止並交 Owner 決定資料範圍；不擴寫此修復。不先跑未隔離原測試，不自動清除本次真實 hint。
- **人工決定：**是否交辦上述單一測試隔離修復。真實定位與列表歷史仍保護不動；其清理或重新備份不包含在建議的執行授權內。

hint 不符時仍可在有效日常前景內核對全部候選，無需先讀失效 hint 目錄；若列表身分／歷史仍無法唯一確定，就停在 bind／init／scan 寫入前。這是既有 reference 的解讀，不是另開修復路線，也不授權本 Reviewer 操作 LINE。

## 實際命令、版本與證據

工作目錄為專案根目錄。Python 合成交易使用 `/usr/bin/python3 -B` 與 `PYTHONPATH=src`；Codex CLI 為 `0.169.0`。

| 本輪實際命令／輸出 | 結果 |
|---|---|
| `git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | exit 0；初始乾淨；候選與分支如上 |
| `test "${HERDR_ENV:-}" = 1` | exit 0 |
| `herdr pane current --current` | exit 1，`pane_not_found`；繼承 pane ID 已失效。依 live list、process-info、標題與 Owner 指認核對目前分析 pane；未換 dispatch 後端 |
| `herdr agent start ... -- -m gpt-6-luna -c 'model_reasoning_effort="high"' -a never -s read-only --no-alt-screen` | 兩個 sibling pane 啟動成功；實際 argv／終端顯示另存私有 evidence |
| `python3 -B .local/line-backup/tasks/notes-active-locator-review-20261115/capture_projection.py` | 原 capture bytes／hash 與去識別投影如上；與 canonical 探針同一組合命令 exit 0，未單獨保存該 child exit |
| `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/notes-active-locator-review-20261115/canonical_probe.py` | 四案例輸出保存；組合命令 exit 0，未單獨保存該 child exit |
| `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/notes-active-locator-review-20261115/subprocess_probe.py` | exit 0；既有測試斷言通過；其三次 child exits 分別保存為 4／0／4 |

文件交付前另執行 `git diff --cached --check`（exit 0）、逐檔 stage 白名單核對、完整私人 ID／root 不外洩檢查與產品來源 hash 比對，均通過。結果保存於私有 `delivery-preflight.json`。

私有診斷目錄：`.local/line-backup/tasks/notes-active-locator-review-20261115/`。含三支診斷腳本、結果、Tester 釐清、兩位助手回覆及 `source-manifest.json`。未納入 Git；沒有原始帳本／照片複製。

| 固定證據 | SHA-256 |
|---|---|
| 原 lists stdout | `4fbf93e2477d03b92fdee34eea049474a6bd0f746acaa2b909462eab95731b21` |
| 原 lists receipt | `6f54674bd729bacd7dd14f0b2875ff9b1b0b012699119c583ff733f7e6eebdf2` |
| `capture-projection.json` | `08a0b0f1ff1c99d16a4349095725611eb79ca7d3615527b14406029289983c17` |
| `canonical-probe.json` | `4006ff778be61770df26629b97cbe49a899141f6cb44f41be377ebb41156a625` |
| `subprocess-probe.json` | `6e16f807ca345ffa601305200f9d106ef73dd7dd410c5014e45c56bd7695700a` |
| 分析候選 `notes.py` | `fcd5bd4196e9963d93ca94b6025ea2c1065ff9202373afd3311b3a8a8dc4ea00` |
| 分析候選 `test_notes_records.py` | `7264f74f68ca9ca8c5e4c6df688ee3bb72abc7c13049e45da0bbda20b3a495e5` |

未新執行整套 daily／notes 回歸、真實 notes 命令、真實資料修復、GUI 下載、chooser 或實機 E2E；均 `NOT_RUN`。本輪無新增實機人眼 `OBSERVED`；Tester 對先前畫面的敘述保留為來源回報，不升格為本輪 sensor 證據。

## 同角色協助與模型證據

兩位 Herdr 助手分別讀取 canonical 分支及測試來源／既有指引；Tester 僅釐清已保存的執行事實。助手不具獨立驗收資格，最終推論由主代理整合，未採用助手對整體 DONE 的自評。

- configuration default：未查核，不用來證明實際模型。
- request parameters：兩次 `agent start` 回傳 argv 明示 `gpt-6-luna`、`high`。
- session/platform display：主代理 `herdr agent read --source visible` 及完成後 transcript 底列顯示兩位新助手為 `GPT-6-Luna high`。Tester 原 pane 顯示 `max`，只作既有事實釐清，未改其設定。
- provider usage：未取得模型路由、用量或計費證據，不聲稱後端身分、token 節省或成本。

## 六項狀態與人工交接

| 狀態 | 判定與邊界 |
|---|---|
| `PRIMARY_OUTCOME_STATUS` | `ANALYSIS_COMPLETE`：測試缺陷已合成重現，事故歸因仍有明列的未知 |
| `IMPLEMENTATION_STATUS` | `NOT_RUN`：未修改產品、測試或資料，只交付分析 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN`：未執行正式產品接受 |
| `REQUIRED_VERIFICATION_STATUS` | `PASS`，僅限本輪 capture 雜湊、隔離診斷及文件核對；產品回歸／修復驗證 `NOT_RUN` |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN`：助手與主代理診斷不是獨立驗收 |
| `TASK_CLOSURE_STATUS` | `BLOCKED`：原備份、真實 locator／歷史匹配與後續修復尚未解決 |

下一 owner 為人工決策者。交付本文件後停止診斷；僅依 Owner 已明示要求整理文件 commit／push，不開始下一正式角色、修復、重測或結案。
