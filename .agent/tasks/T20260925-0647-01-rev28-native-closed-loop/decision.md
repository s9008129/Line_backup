# Stage 01 decision — R4 candidate

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
PLAN_REVISION: 4
PLAN_SHA256: 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b
ANALYSIS_BOUND_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da
PLAN_VALIDITY_DECISION: PLAN_REVISION_REQUIRED
PLAN_STATUS: CANDIDATE_UNAPPROVED
PLAN_REVIEW_REQUIRED: YES
NEXT_ROUTE: READY_FOR_PLAN_REVIEW (only if final-audit.json confirms unchanged remote HEAD)

## 現在要解決的事

建立通往真實 LINE 相簿備份結果的安全執行路線。第一個障礙是 test target 無法編譯；主要產品缺口是正式 CLI 尚未接上原生 observation/session、共用 engine 與完整 filesystem proof。兩者不能視為同一個問題。

本輪唯讀診斷確認 helper 名稱／呼叫方式錯置；另重現短日期分段拒絕與穩定時間窗誤判。R4 規定先修復診斷入口，再完成共用原生組合路徑與安全證據鏈。未執行修復，未進入 Stage 04。

## 歷史與 authority

- 原 plan.md R3 已完整保存在 plan-history/plan-r3-before-20260928-replan.md；SHA-256 63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828。
- review/attempt-01..06、所有 snapshot、handoff-history、execution.md 保留原始位元組。
- 現有 handoff.md 狀態：**STALE / SUPERSEDED_CANDIDATE**，不得作為 R4 的執行授權。原檔保留，SHA-256 88fc1932bbf93b3fa0d4328cfcf941da7890d94a69d2471a84becd15019b1bf6。
- 舊 execution.md 的 PRE_LIVE_READY 等文字是歷史敘述，不能推翻目前 compile failure 與 live-execute stub 的 source 證據。
- Stage 02 必須獨立審查這份 R4，特別是 ledger 單一 authority、完整 observation chain、Phase A／B 接續、pre-intent resume 的严格條件和永久禁止 irreversible retry。
- 只有審查 PASS 後，Stage 03 才能重新編譯 handoff。此 Planner 未自行審查批准，未建立新的 handoff 或 result.md。

## 收斂紀錄的範圍

本輪 Stage 04 material implementation attempts = 0；這不是將既有 task 的歷史嘗試或 irreversible budget 歸零。唯讀 diagnostic commands/results 均留存在 analysis/r4-20260928。啟動 Stage 04 前須從 execution/history 重建可觀察的既有嘗試；缺少 progress.md 不代表 budget 可重置。

未來首個 blocker fingerprint 見 plan.md。最多 3 次 material attempts、最多 2 次連續無新資訊；A → B → A 立即 escalation。下一步無可反駁假設／新資訊來源／可區別結果時，不應继续改碼。

## Current status subjects

PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: FAIL
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: REPLAN_REQUIRED

Build PASS 與 frozen provenance PASS 保留；test compilation FAIL 不抹除這些事實。沒有新 production outcome 或 Stage 05 acceptance 證據。

## Preservation and freshness

See analysis/r4-20260928/final-audit.json for final fetch/local/remote binding, baseline per-file preservation and protected source/test/workflow/history hashes. See planning-artifacts.sha256 for artifact hashes. Any remote drift not reassessed changes route to STALE_REMOTE_HEAD; neither freshness nor this decision is plan approval.

PRODUCT_CODE_MUTATED: NO
TEST_CODE_MUTATED: NO
WORKFLOW_MUTATED: NO
BASELINE_MUTATED: NO
PRODUCTION_SAVE_ALL_DISPATCHES_THIS_STAGE: 0
DESTINATION_CONFIRMATIONS_THIS_STAGE: 0
GIT_COMMIT_CREATED: NO
GIT_PUSHED: NO
