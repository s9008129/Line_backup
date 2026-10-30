# 人工交接草稿 v1

## 任務與精確版本

目標：修補沒有導覽作用依據就把 Escape 當返回鍵的決策缺口；保留正常自主備份。

產品基準：`66ebd9d50378d3b1d533c83eaf48eaca9a72ef43`，原分支 `fix/backup-relocation-20261030`；它是未合併的既有候選，不代表獨立通過。

規劃分支：`plan/cua-navigation-20261030`。Repo 為目前 `Line_backup` 工作樹，原 clean。候選為本任務四份 Markdown 與 `source-manifest.json`；對外提供 Draft PR 與推送後精確 HEAD。`artifact-manifest.json` 固定各交付文件的 SHA-256；不把 manifest 自己當自我雜湊。

必須攜帶：

- `plan.md`：範圍、第一切片、責任人、驗證與停止條件。
- `analysis.md`：觀察、推論、未知與來源行號。
- `role-report.md`：本次實際執行與六狀態。
- `source-manifest.json`、`artifact-manifest.json`：來源及草稿的版本識別。
- 本次原對話事件；若下一角色無對話權限，使用本機 `.local/line-backup/planning-20261030-escape/evidence/incident-summary.md`。該檔是人工脫敏整理，不是平台原始 trace，也沒有原始像素截圖。

## 本角色完成與限制

本輪依 Owner 明確要求做規劃研究，沒有更改產品、LINE、備份任務入口或照片。當前 Session 含先前實作歷史；不聲稱這是一個隔離的新 Session，也不作任何獨立審查或驗收。兩名 helper 只做同一規劃範圍的唯讀來源研究，無正式接受權。

已完成：Git 基準核對、Skill／工具邊界分析、可見事件對照、官方 Skill 與指定模型文件查閱、修正計畫草稿、文件 diff 與來源 hashes。具體命令與退出碼見 report。

未執行：產品修復、unittest、模型行為矩陣、真實 GUI／備份重試、Plan Acceptance、Simplicity Review、獨立驗收。

事實：Escape 由 Agent 呼叫；呼叫後同一批程式取得 AX＋截圖並呈現聊天主畫面。Skill 沒寫此按鍵做返回。

推論：入口／返回的具體條件缺失，讓一般快捷鍵假設取代可核對的動作依據；現有 CUA 能力沒有由 daily 進行語義攔截。

未知：模型內部機制、provider 身分／effort／用量、跨次錯誤率、當前平台是否能用更細輸入權限、LINE 各版本 Escape 行為。這些未知不阻止有界文件修補，但不允許宣稱任意模型必然安全。

## 下一個人工決策

建議由 Owner **另開主 Session 啟動 Simplicity Review（計畫）**，先檢查本計畫是否以最少規則補上具體缺口；這份 handoff 不自動啟動下一角色。

請下一角色先核對產品基準、草稿 commit／artifact hashes，並保留未合併的既有搬移成果。若 master 或候選改變，不自行套用舊批准；交人決定重綁基準及重查範圍。

需人決定：是否核定本計畫的指令層修補，以及是否另加 Plan Review。若要求硬性保證所有模型不能派送錯鍵，需先決定是否允許新工具控制架構；目前計畫不含此授權。

模型行為矩陣由 Owner 指定模型／effort／重複次數後才執行。GUI驗收需另行提供指定列表及有效前景。不能拿舊前景交接在本規劃任務中重演錯誤或繼續下載。

拒絕、基準漂移或安全行為 FAIL 時，保存已知結果並停止，由人決定下一步；不自動進入修復、重測或結案。

## 狀態快照

PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: PENDING_HUMAN_HANDOFF
