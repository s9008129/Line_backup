# 交接草稿 v1：記事本啟動接續修正

## 任務與精確版本

- 本輪角色：Owner 指定的 Planner；結論 `PLAN_DRAFT_COMPLETE`。未開始正式計畫審查、實作或接受。
- 任務目錄：`docs/plans/20261112-notes-download-control/startup-resumption-plan/`。
- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- 規劃輸入 HEAD：`3b12e41cd12e458118e94f62feab8da3c6054db9`，起始遠端相同。這是來源基準，不是要求下一角色仍處於發布前 HEAD。
- 交付候選：承載本目錄五份文件的精確 commit，由本輪最終回覆及私有 Git postflight 記錄。Owner 將該實際 commit 交給下一角色；不能自行以 latest 取代已核對候選，也不要因這次規劃文件發布而要求回到輸入 HEAD。
- [source-manifest.json](source-manifest.json) 保存輸入來源與 plan SHA-256；候選未核定，沒有繼承的計畫 PASS。
- 初始既存 untracked Markdown 保留且不 stage；其他 worktree、舊 plan／handoff／報告／提報不修改。

## 已完成、事實與未知

已將[補充分析](../startup-resumption-review/issue-analysis.md)的啟動接續問題，以及[舊控制分析](../issue-analysis.md)的 viewer 控制未知納入同一可驗證目標，分開成功條件。沒有以文件完成關閉控制問題。

直接核對：lists 已回全部帳本摘要；舊診斷 Prompt 固定舊 HEAD、禁止下載；產品路徑自原事發版到規劃基準無變更。另發現舊報告「手冊 B 區」錯引；記事本實際入口是[附錄 C](../../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt)。舊文件只作歷史依據，不再作本輪現行步驟。

推論：補足明示授權更新、剩餘條件重核、帳本候選整理與畫面角色分流，可以消除已有證據的啟動負擔。它不證明 hover 是根因或控制已可用。

未知：事發授權原對話、補充提報該次原始 CUA、當時完整 stdout 是否截斷、目前來源及真實帳本狀態、該 viewer 控制的實際機制。上述未知不妨礙提出有界指示修正，但禁止預先宣稱五張可下載或已完成。

同角色唯讀助手只查覆蓋與來源，不作正式審查。主代理曾參與前輪分析，本次不是獨立接受；沒有模型覆寫或 provider usage／成本主張。

## 範圍、檢查與授權

目前授權只包含規劃與同範圍文件 checkpoint。沒有 LINE 前景、私人帳本／照片讀寫或 GUI 派送授權。

待核准的 S1 只有四份既有文件：

1. Skill 主文件的接續分支與 reference 連結。
2. download-and-ledger 的完整 lists 保存、全部候選摘要及必要刷新。
3. gui-inventory 的列表／viewer 分流與有限控制觀察方法。
4. next-agent-prompt 的歷史用途標示與正確記事本入口；原診斷授權保持歷史原文，不轉為下載 Prompt。

完整精確路徑、十種決策情境、保護條件與停止見 [plan.md](plan.md)。不改程式、測試、正式日常 Prompt、相簿、帳本、照片、資料／派送／restart 語意，不加新的 Owner 啟動欄位。超出範圍交 Owner 決定。

實作者交付文件 diff／位置引用、連結與隱私核對，以及專案既有最小三命令的真實結果；不是在本輪執行。文件情境可人工核對，不另寫仿實作測試。回歸失敗不在此範圍改程式或重複無新資訊的修法。

功能確認仍要以日常正式入口完成目標、控制、派送、檔案驗證與 completion，不能用三命令成功替代。來源變動、其他媒體或舊交易必須按當次有效授權與永久歷史處理，不能以歷史五張數字猜身分或擴範圍。

## 下一個人工步驟

**請 Owner 另開主 Session，使用既有 `07_simplicity_review_prompt.md`，審查這份計畫草稿。** 不需要先開 LINE。

需提供：

- 本輪交付的精確 commit，以及本目錄 [plan.md](plan.md)、本 handoff、[planner-report.md](planner-report.md)、[source-manifest.json](source-manifest.json)。
- [補充提報](../問題提報單-啟動阻塞與流程負擔.md)、[補充分析](../startup-resumption-review/issue-analysis.md)，以及原控制分析；其歷史版本已由 source manifest 綁定。
- 同候選版本 AGENTS、四個擬修改文件與使用手冊附錄 C；計畫審查只需公開來源，不需要真實帳本或私人影像。

下一角色先判定這四檔是否為最小充分範圍，確認 U1 未被假定已解、保護條件未放寬、沒有額外日常入口。它可提出必要的減法，不授予下載權、不代做實作或接受。

由 Owner 決定是否採用計畫及何時啟動後續角色。計畫檢查後再由 Owner 啟動 Implementer；S1 後由 Owner 啟動第二次 Simplicity Review。若已是最終文件切片，不重複造實作。

實際可用性由 Owner 以同一日常附錄 C Prompt 授權並交接當次前景，保持本案範圍；不以 `05_acceptance_prompt.md` 或本開發 handoff 取代。若試用仍卡 U1，交回具體證據並停止，不自動修復、再測或換角色。

## 六項狀態

- PRIMARY_OUTCOME_STATUS: BLOCKED（尚無五張完成證據）
- IMPLEMENTATION_STATUS: NOT_RUN
- CORE_ACCEPTANCE_STATUS: BLOCKED
- REQUIRED_VERIFICATION_STATUS: PARTIAL（僅來源／規劃核對）
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
- TASK_CLOSURE_STATUS: BLOCKED

未實作、未進行 GUI／chooser／下載／解碼／completion／跨 Session／獨立接受，不稱 DONE。詳細實際命令與文件驗證結果見 planner-report 及專案私有收據。
