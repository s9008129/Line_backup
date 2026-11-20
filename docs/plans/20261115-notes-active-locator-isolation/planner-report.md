# 記事本 locator 隔離：規劃與修復協調報告

## 結果與範圍

本輪只修復 `tests/test_notes_records.py` 的父子程序 active locator 隔離，沒有修改產品程式、其他測試、Skill 或真實備份資料。最終來源 SHA-256：`10bda15e49433e1714f249b7a15a7b7e8f69a8beb14d0735e31257bc272b602e`。單檔 36 tests 與相簿 daily 73 tests 通過；Worker2 對凍結候選的 S1–S6 peer 核對無阻塞，兩個目標案例也分別 exit 0。

Owner 已明示本 session 從 Planner 擴為修復總指揮，授權以 Herdr 管理 Luna/high Workers，完成修復後由 Luna 子代理撰寫詳細提交訊息並 add／commit／push；之後明示不必重啟。本次採兩個 Worker panes，沒有新增 Worker3 或重新啟動本 pane。完整 notes suite 因額外隔離疑慮，經 Owner 明確選擇列為 NOT_RUN；不擴檔修 locks。

真實備份仍 BLOCKED；本輪不修真實 active、不認領真實列表歷史、不下載，也不把離線測試當實機備份成功。

## 基準與變更

- Repo：`Line_backup`；分支：`feature/line-notes-media`。
- 基準 HEAD：`42bc0e9ee55c2e2c281e4aea8ea65484a83caa75`；分析 commit：`c105002ad8cfde194e48d22dc9635fd9c521dd20`，祖先關係 exit 0。
- Planner 初始 tracked／untracked 乾淨。修復協調開始時，只有本 session 產生的四份未提交規劃文件；未吸收他人變更。
- 修復開始前 `git ls-remote origin refs/heads/feature/line-notes-media` exit 0，遠端 HEAD 與本地基準一致。
- 來源只改一檔；另交付本目錄四份去識別文件。私有證據、測試合成檔及頁面不入 Git。

| 保護要求 | 最終行為與證據 |
|---|---|
| S1 父子先隔離 | setUp 在任何 Notes 動作前設 fixture `_active_task_path`；child 使用 `-B -c`，檢查實際 locator 回傳值等於預期且位於內層，再在同一 notes 模組呼叫 main |
| S2 成功可觀察 | 保留真實 reader／writer，child bind 成功後核對 hint schema、root、list ID、session |
| S3 拒絕不寫 | child bind 依序 4／0／4；兩次錯誤 context 前後比較 locator 與 events bytes，外層 sentinel 不變 |
| S4 清理邊界 | sentinel 是測試控制 fallback；真實 TestCase.run(TestResult) 覆蓋正常、測試失敗、setUp 注入失敗，檢查清理 callback、fixture 缺席與 mock 還原 |
| S5 CLI 相容 | 既有 help、argparse、業務拒絕與預期內部錯誤分類斷言保留，整檔 36 tests 通過 |
| S6 範圍與回歸 | 來源差異僅白名單；daily 73 tests、notes help 通過；完整 notes suite 依 Owner 決定 NOT_RUN |

`notes.py` SHA-256 仍為 `fcd5bd4196e9963d93ca94b6025ea2c1065ff9202373afd3311b3a8a8dc4ea00`；唯讀參考 `test_notes_locks.py` 仍為 `1494a9a3c2f839900d7a5fcb99b78d11c4c5c92f590da85304849c1ae457c151`。沒有新增產品 flags、控制器、遷移或公共介面。

## 協調與驗證

Worker1 單獨持有測試檔，Worker2 先唯讀核對計畫／suite 安全，之後核對凍結候選。計畫核對採納一項簡化：不重測刪 fixture 後 memory 的產品 canonical gate。首切片整合時，主代理發現手動 rmtree 案例不能證明 setUp 失敗後的 unittest cleanup；Worker1 以真實 TestCase 生命週期取代，並把 child 邊界收緊為實際內層路徑。這兩步都帶來新證據；未發生連續無新資訊重試，未重跑原分析腳本。

| 實際命令 | owner／結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py -k test_bind_omitted_context_inherits_saved_context` | Worker1 初切片：1 test，exit 0；最終候選亦包含於整檔及後續 peer 目標核對 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py -k test_active_locator_fixture_cleanup_boundary` | Worker1 最終候選：1 test，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py` | Worker1 最終候選：36 tests，3.777 秒，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 主代理：73 tests，322.719 秒，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 主代理：exit 0，只顯示 help |
| `git diff --check`、來源 hash 與 diff 白名單 | 主代理／Worker1：exit 0，產品及 locks hash 未變 |

整檔輸出中的 argparse usage 為既有負向案例，unittest 整體為 OK。Worker1 的執行工具輸出合併 stdout／stderr，報告如實標示未分流；主代理 daily／help 證據則分流保存。未以預期分類測試的 70 冒充日常可重試錯誤，未出現非預期 child 70。

Worker2 的 suite 安全盤點發現 locks 的 sitecustomize patch 匯入模組後再用 `-m` 執行，無充分證據證明實際 CLI 模組實例受到隔離。這是靜態風險判讀，未透過讀真實 active 或執行 locks 取證。Owner 明確決定保留單檔，完整 notes suite NOT_RUN；該未執行項不是測試 FAIL，也不計為已通過。

## 證據與限制

私有執行證據根目錄：`.local/line-backup/tasks/notes-active-locator-plan-20261115/`。包含 preflight／來源 manifest、Worker 啟動參數與可見顯示、計畫及安全核對 transcript、Worker1 初切片與補強報告、Worker2 peer 證據、主代理 daily／help JSON，以及最終文件／交付 receipts。既有分析任務的已列合成結果只讀，沒有重跑或沿其路徑讀原件。

舊環境曾拒絕 Herdr socket 及 `.git/index.lock`；Owner 開放權限後 Herdr live 操作已成功，舊拒絕僅保留歷史。另有一次本機 Python heredoc 解碼失敗，未送出 Herdr prompt，改用同一 Herdr CLI 正確傳遞文字後成功；沒有換派工後端或重派不明任務。Herdr 短時 wait 的 timeout 只表示 Worker 尚未完成，未重送已送出的工作。

模型證據分開記錄：主 session 原啟動 argv 為 `gpt-6.1-sol/high`；兩個 Worker 的 start 回傳 argv 與 process-info 均明示 `gpt-6-luna`、`model_reasoning_effort="high"`，可見介面也顯示 `GPT-6-Luna high`。configuration default 未查核，provider usage／路由／成本 UNKNOWN；不宣稱後端身分、token 節省或 OS 隔離。

直接事實是測試隔離缺陷與本輪修復證據。事故 hint 與測試常數／路徑高度吻合，仍屬有根據推論；歷史 writer trace、事故時 metadata、真實列表與帳本唯一匹配均 UNKNOWN。本輪沒有新增實機人眼 OBSERVED。

Workers 的候選核對屬同任務 peer 檢查，不是正式獨立接受。真實 GUI、chooser、下載、跨 Session 恢復、原備份完成及正式接受均 NOT_RUN。

## 交付結果與六狀態

單檔修復及已授權安全檢查完成。Worker2 對最終 hash 完成 S1–S6 peer 核對，未發現具體阻塞；另各跑一次 context 與 lifecycle 案例，均為 1 test、exit 0。原始 stdout 為空，測試結果在 stderr；主代理已讀原始結果確認，不沿用報告初稿相反的 stream 說明。

依 Owner 要求，修復完成後再由 Luna/high Worker2 完整梳理上下文撰寫提交訊息，主代理核對後只 stage 五份白名單檔案。實際 commit message 本體、push 與遠端精確 HEAD 結果另存私有 delivery receipt，並在 Owner 交付訊息回報；本文件不預填尚未執行的 Git 成功，也不發出整體 DONE。

PRIMARY_OUTCOME_STATUS: FIX_COMPLETE（單檔修復）
IMPLEMENTATION_STATUS: PASS（限單檔隔離修復）
CORE_ACCEPTANCE_STATUS: NOT_RUN（未開正式接受）
REQUIRED_VERIFICATION_STATUS: PASS（限 Owner 選定的安全檢查；完整 notes suite NOT_RUN）
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED（原備份及正式接受未完成）
