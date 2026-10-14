# 一次性 LINE 相簿點擊診斷：外部審查入口

請一併審查 [plan.md](plan.md) 與 [plan-contract.json](plan-contract.json)。本 PR 僅交付待審計畫，不授權或執行 LINE 擷取、點擊，也不代表正式准入或 ML08 驗收。

負責人於 2026-10-14 批准最多一個獨立診斷 Task 的建立與准入準備，之後指定由另一個模型審查，禁止使用 Luna Reviewer。GPT-6.1-sol／xhigh Planner 已發佈計畫並完成原生 role result；未啟動 Reviewer 或 Implementer。固定 CONTRACT／RESULT receipts、Planner result 正式匯入及 deterministic Handoff 均尚未完成。外部審查結果仍須依原有 Harness 程序處理，不能自動視為正式准入。

本 Task 為 `TASK-55518bd9640d4ea59ab3a6414a171795`。後續唯一診斷目標是在正式准入與新的明確前景／擷取／點擊同意後，取得 fresh screenshot／AX、綁定完整相簿卡片、最多點擊一次、核對詳細頁後立即停止。禁止重試、捲動、第二次點擊、Save All、下載、備份狀態變更、新 Issue／continuation、Harness 修改及無關工具／CI 修復。

審查請集中確認：

- 新診斷的目標與範圍是否確實獨立，沒有重置 ML08／c6 的舊根因額度或降低原 28 gates。
- fresh capture、身分／點位綁定、一次性 dispatch 與 post-click 身分核對是否能以現有 `cua_repl` 合法取得；未知能力不能當成已驗證。
- 禁止新 Issue 時，遇到 non-PASS 保存真實結果、停止在 importer 前並保留未完成 closure，是否符合上層治理。
- 非 Luna 外部審查如何滿足既有正式准入要求；目前沒有變更 runtime mapping 或宣稱外部審查已被 Controller 接受。

舊任務背景可參閱既已發布的 [c6 治理交接](../../../line-v3-live-e2e-20261010/continuations/minimal-live-08/replanner-handoff/evidence/c6/planner-handoff-native-admitted.md) 與 [Controller protocol blocker](../../../line-v3-live-e2e-20261010/continuations/minimal-live-08/replanner-handoff/evidence/c6/controller-protocol-blocker.md)。本地 `intake.json` 保存 predecessor Task／Issue／c6 關聯與保護檔案雜湊，未納入本 PR。

兩份計畫檔案保留原始發佈 bytes：

| 檔案 | SHA256 |
| --- | --- |
| plan.md | `469b093b33e8e89bd69506ab2fe7a91109800df034dba2924dd43192ac7f1dcf` |
| plan-contract.json | `127d4ac65a4dc19604c476ad162e6f50bc4ea397fedf25020bd376caaf4267ad` |

本次 LINE 擷取與點擊數均為 0。原始 screenshot／AX、session 紀錄、config、backup state 及其他本地證據均不在本 PR；任何之後取得的原始 screenshot／AX 只留在 Mac 私有位置。
