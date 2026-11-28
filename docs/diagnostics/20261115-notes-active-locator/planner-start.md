# Owner 指定的 Planner 交接

## 任務與人工授權

Owner 在高階分析完成後明示要求：另開 Herdr pane，以 Codex CLI `gpt-6.1-sol`、`high` 執行 Planner，取得精準根因上下文並產出修復計畫；完成交接與本輪 add／commit／push 後，關閉 Tester、Worker1、Worker2，最後關閉分析 pane。這是本次人工指定的下一角色啟動，取代先前「本角色不啟動下一角色」在此次交接上的限制；不授權 Planner 實作、修帳、備份、驗收或再派下一正式角色。

來源分析已提交為 `c105002ad8cfde194e48d22dc9635fd9c521dd20`，並核對遠端 HEAD 一致。Planner 須以本交接文件所屬 commit 為啟動基準，記錄實際完整 HEAD，核對 `c105002` 為祖先且產品／測試來源 hash 仍符合分析報告；若有並行工作或版本差異，明列保留，不吸收無關變更。

## 唯一修復問題與證據

先完整閱讀同目錄 [issue-analysis.md](issue-analysis.md)，不要只依摘要寫計畫。

已證實缺陷：`tests/test_notes_records.py` 的 `setUp` 只在父程序 mock `_write_active_hint`；`run_cli` 重新啟動 Python，成功的 CLI bind 使用真實 writer。fixture cleanup 移除帳本後，寫出的 locator 會指向失效路徑。以合成 locator 安全重現：錯誤 context bind exit 4，正確 context bind exit 0，cleanup 後 memory exit 4／`CANONICAL_NOTES_RECORDS_REQUIRED`。

事故 capture 的 hint session 精確匹配該 CLI 測試常數，路徑有相同 fixture 前綴；這使事故來源高度吻合，但缺歷史 writer trace，不能宣稱歷史歸因直接證實。`canonical` 檢查實體目錄／解析路徑，並非只允許預設 collection。原列表對哪份永久帳本仍 `UNKNOWN`。

私有診斷目錄為 `.local/line-backup/tasks/notes-active-locator-review-20261115/`，可唯讀核對其中三支診斷腳本及去識別結果、`source-manifest.json`、`delivery-preflight.json`、`delivery-receipt.json`。不要重跑腳本或原測試，不讀真實 active、hint 目標帳本、index／events、照片或其他任務原件。

## 給 Planner 的精確指示

1. 讀 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/01_plan_prompt.md`、專案 `AGENTS.md` 與本交接；同版 policies 在 `/Users/hsiaojohnny/.codex/policies/v4.9.0/`，不要恢復 repo 已退役的 Harness controller。
2. 依 plan／handoff 範本，只在 `docs/plans/20261115-notes-active-locator-isolation/` 建立 `plan.md`、`handoff.md`、角色報告與必要進度。私有規劃證據另放專案 `.local/line-backup/tasks/notes-active-locator-plan-20261115/`；保留其他既有檔案。
3. 規劃中的實作白名單以 `tests/test_notes_records.py` 為限，優先在父程序及每個 CLI child 初始化時把 `_active_task_path` 定向該 fixture 的合成 locator。可唯讀參考 `tests/test_notes_locks.py` 的 child bootstrap；不要為此新增產品 flags、控制器、遷移功能或修改公共介面。
4. 保留 child 真實 writer 對合成 locator 的可觀察效果。不能只 no-op writer 後宣稱隔離完整；也不能先讀真實 active、跑測試污染後再恢復它。提出測試控制的外層 sentinel／等效可驗證證據，證明成功與拒絕 child bind 的寫入邊界、清理及失敗退出。
5. 計畫應列出最小切片、風險分級、成功條件、逐項驗證 owner／命令、必要人工檢查點、未測範圍及六項狀態。先完成隔離才執行可能寫 active 的測試；Planner 本輪不執行測試。原日常任務／真實 locator 修復與實機 E2E 保持未完成。
6. 根據已證實缺陷寫可執行的最小方案，不為未知事故歸因擴張功能。若需改產品、真實資料、授權／schema／日常入口或擴大實作路徑，明列超界並交 Owner 決定。
7. 不再詢問既有的「是否需要產出計畫」授權。完成草案後，以繁體中文交付 Owner，依專案規則處理規劃文件 checkpoint；不得把草案當接受、不得開始 Implementer／Reviewer／E2E，不再派正式角色。

Planner 的模型請求為 `gpt-6.1-sol`／`high`；記錄 request 與介面顯示，不宣稱 provider 後端或成本。用 Herdr 獨立主 session 執行，先前助手不是獨立接受。

## 交接狀態

- `PRIMARY_OUTCOME_STATUS=ANALYSIS_COMPLETE`：本分析交付；Planner 草案尚待其執行。
- `IMPLEMENTATION_STATUS=NOT_RUN`。
- `CORE_ACCEPTANCE_STATUS=NOT_RUN`。
- `REQUIRED_VERIFICATION_STATUS=PASS`：只限分析隔離診斷與文件交付；修復／計畫驗證尚未執行。
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`。
- `TASK_CLOSURE_STATUS=BLOCKED`：原備份及修復未完成；不因成功 dispatch 而結案。
