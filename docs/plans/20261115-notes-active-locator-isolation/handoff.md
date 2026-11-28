# 記事本 locator 隔離修復交接

## 候選與交付

本輪依 Owner 最新協調授權，在目前 session 以兩個 Herdr Luna/high Workers 完成單檔修復與核對；沒有重啟本 pane，也沒有建立 Worker3。Git 最終交付結果由 [planner-report.md](planner-report.md) 與私有 delivery receipt 綁定，不將未執行提交宣稱已完成。

- Repo／分支：`Line_backup`／`feature/line-notes-media`。
- 輸入 HEAD：`42bc0e9ee55c2e2c281e4aea8ea65484a83caa75`。
- 分析 commit：`c105002ad8cfde194e48d22dc9635fd9c521dd20`。
- 唯一來源變更：`tests/test_notes_records.py`。
- 凍結候選 SHA-256：`10bda15e49433e1714f249b7a15a7b7e8f69a8beb14d0735e31257bc272b602e`。
- 文件：本目錄 plan、handoff、planner-report、progress；私有證據不入 Git。

## 修復與檢查

父程序及每個 CLI child 都先把 `_active_task_path` 指到內層合成 fixture；保留真實 reader／writer。成功 bind 讀回正確 root／ID／session，拒絕前後 bytes 不變。外層 sentinel 是受控 fallback；cleanup 使用真正 unittest 正常、測試失敗、setUp 失敗流程驗證清理及 mock 還原。

最終單檔 36 tests、相簿 daily 73 tests 與 notes help 均 exit 0。完整命令、結果與來源 hash 見報告。Worker2 已對上述凍結 hash 核對 S1–S6，結論無阻塞，另各跑一次 context／lifecycle 目標案例，均 exit 0；未沿用初版的手動 cleanup 測試證據。

Owner 已明確選擇保留單檔，完整 notes suite 標 NOT_RUN。locks child 的模組隔離疑慮列為後續事項；本次不修改或執行它，也不以其他入口繞過。所有正式獨立接受與實機備份結果仍未執行。

## 接續所需資料與邊界

攜帶本目錄四份文件、精確修復 commit／diff，以及私有 `.local/line-backup/tasks/notes-active-locator-plan-20261115/` 中的來源／文件 manifests、Worker1 補強報告、Worker2 peer 結果及 commander 檢查／交付 receipts。原 [分析](../../diagnostics/20261115-notes-active-locator/issue-analysis.md) 與 [啟動交接](../../diagnostics/20261115-notes-active-locator/planner-start.md) 保持原 binding。

真實 active／index／events／hint 目標帳本／照片沒有讀寫，沒有 LINE 操作。這項修復不清理真實 hint、不認領未知列表歷史、不重下載、不合併 master。事故歷史 writer trace 與真實列表匹配仍 UNKNOWN。

若 Owner 之後要求處理 locks 或恢復真實備份，須另定該範圍；實際備份仍使用手冊記事本正式日常 Prompt 及有效前景交接，不改用 Harness E2E 角色 Prompt。不能把本次離線測試當成原備份已恢復。

## 六項狀態

PRIMARY_OUTCOME_STATUS: FIX_COMPLETE（單檔修復）
IMPLEMENTATION_STATUS: PASS（單檔）
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PASS（Owner 選定範圍；完整 notes suite NOT_RUN）
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED（原備份／正式接受）
