# 程式修剪 Planner 交接 v1

## 任務與精確版本

Owner 指定本輪為 Planner，明示必須完成「修剪不必要程式碼片段 Plan」。目標是 Skill 驅動的記事本備份能持續完成與跨 Session 接續，減少內部軟體限制與 Owner 操作負擔。

- 基準：主 worktree `Line_backup`，`feature/line-notes-media`，產品 HEAD `94700e92ac11c6bbc6140f45a1ac680bc08b875a`。
- 待審產物：[plan.md](plan.md)、本 handoff、[planner-report.md](planner-report.md) v1；精確檔案 hashes 見 [artifact-hashes.sha256](artifact-hashes.sha256)。
- 既有未追蹤 `issue提交單.md` 保留，不納入提交；未處理其他 worktree。
- 私有證據：`.local/line-backup/tasks/notes-agent-simplification-plan-20261111/`；其中 source-before 保存產品與既有未追蹤檔案 hash。

## 本角色已完成工作

已核對更正後的 01 Planner Prompt、AGENTS、全域 4.9 routing／subagent policy、程式／測試與記事本操作文件。專案內沒有 policies 目錄；此次只讀 Owner 已安裝的全域政策，沒有重建 Harness。

已確認實際拒絕的呼叫根因為省略 optional context，程式卻要求精確重傳歷史值；沒有證據顯示該拒絕代表真實列表錯誤。兩位同角色唯讀 helper 分別研究恢復 gate 與 Skill 操作負擔，結論由 Planner 整合，不是獨立審查。

選定完整切片為 C1 省略 context 自動承接與死分支刪除、C2 新 scan 不依賴上一輪 detail 完整、C3 普通 intent 僅要求完整列表卡片及完整目標貼文；D1–D4 同步減少重複摘要／封裝與日常可修正錯誤造成的終止。精確位置、保留條件、V1–V7 owners 與停止條件以 plan 為準。

本輪沒有產品變更、產品測試、真實帳本呼叫或 LINE 輸入。先前日常任務的錯誤輸出作為既有證據引用；沒有重跑 bind 來製造重現。

## 授權與下一個人工步驟

Owner 已授權以簡化為方向移除不必要程式；本輪因明確 Planner 角色，只交付計畫，尚未執行產品刪減。後續產品實作須依本版範圍由 Owner 啟動；既有授權不擴至真實帳本改寫或不明派送。

建議 Owner 把本版三份文件、hashes 與精確基準交給計畫 Simplicity Reviewer。第一個具體問題：三項刪減是否剛好消除已證明的負擔，並保留當篇資格與全列表交易互斥。需決定的行為是 C3：全列表卡片覆蓋完成後，可逐篇盤媒體與下載，而無需先盤完所有篇媒體。

核定後由 Implementer 一次完成 C1–C3、D1–D4 與 V1–V6；首切片即完整候選，仍保留 implementation Simplicity Review。若已完整，不再開空切片。Owner 後續以手冊日常正式 Prompt 確認實際備份，不使用本 handoff 作為下載前置文件。

事實：根因與兩個 coverage gate 均可由精確原始碼核對。推論：此切片可減少已確認的自我阻擋。未知：修剪後的回歸、真實 LINE 整份完成、跨 Session 與混合附件結果；均不得提前標 PASS。來源變動、晚到 GUI 副作用與外部 writer 仍不可由 ledger lock 排除。

## 狀態快照

PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE（規劃）

IMPLEMENTATION_STATUS: NOT_RUN

CORE_ACCEPTANCE_STATUS: NOT_RUN

REQUIRED_VERIFICATION_STATUS: NOT_RUN（產品）

INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN

TASK_CLOSURE_STATUS: NOT_DONE
