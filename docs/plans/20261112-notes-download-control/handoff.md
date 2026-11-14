# handoff：記事本下載控制規劃交接（草稿 v1）

## 任務與精確版本

- 目前角色：Planner；未開始 Simplicity Reviewer、Plan Reviewer、Implementer 或 Acceptance。
- 任務目錄：`docs/plans/20261112-notes-download-control/`。
- Repo／分支／輸入 HEAD：`/Users/hsiaojohnny/dev/Line_backup`／`feature/line-notes-media`／`40a7b09e9900eddab2df9bfd81aad9ec25b89c1f`。
- 事發產品 HEAD：`02db924fd89ff79067cd4958729a3ac6b8157437`；到輸入 HEAD 只新增問題提報單，產品版本沒有變。
- 候選：本次六份新增規劃文件；由承載這些文件的 Git commit 精確識別，推送收據與遠端 HEAD 核對留本機私有任務目錄及最終回覆。不是程式修復候選，沒有已核定 plan 或 acceptance。
- 工作樹初始狀態：僅一份既有無關 untracked Markdown；保留原件，不 stage；規劃證據包含其初始與收尾 hash。

固定內容版本：

| 文件 | SHA-256 |
|---|---|
| plan.md v1 | `fba0ca1fa9b4618b29ce424cde251405220eba0e4f092a8ad81421098d6fd437` |
| analysis.md | `be2b0cc595e577f88089f826d9ddb0861052ed31da18607876fe6c91c822eda9` |
| source-manifest.json | `1e8beeae9e38d6bd4645d293dc69596394392f8c82717d2f88c3b96c4dc77f77` |

## 本角色交接

**PLAN_DRAFT_COMPLETE。** 已完成公開來源的有界分析與可執行查證計畫；這不代表底層根因已確定，也不簽發產品 PASS。

已知的立即停止點是「控制出處／可見性／定位沒有證據，停在 intent 前」。公開提報單記錄 5 個 PHOTO 仍 PENDING、另 1 篇 NO_MEDIA、無 attempt／chooser／下載／completion；本輪未重讀私人原件或帳本，沒有把提報單敘述升為本輪實機證據。

目前沒有支持修改 notes CLI 的具體違約。`dispatch_blockers=[]` 是帳本投影；固定的 `dispatch_authorized=false` 不判斷 Owner 授權；`source_availability=UNKNOWN` 不等於 UNKNOWN attempt。程式核對位置與根因候選排序見 [analysis.md](analysis.md)。

### 已完成與未完成的檢查

- 已完成：Git root／worktree／branch／HEAD／status、遠端輸入 SHA、事發版差異、公開來源及 hash、文件範圍與連結／隱私核對。實際命令、exit 與最終文件檢查見 [planner-report.md](planner-report.md)；不能把來源閱讀記為測試 PASS。
- 未執行：真實 LINE／hover／popup／chooser／下載、照片解碼、影片解碼、completion 讀回、跨 Session 恢復、程式回歸、正式獨立審查與接受，均為 NOT_RUN。
- 助手只支援同一 Planner：一名繼承派送的唯讀來源助手分析 CLI；使用者指定 GPT-6-luna 助手在文件完成後撰寫提交訊息。兩者不能簽獨立接受。模型參數、平台回覆與未取得的 provider usage 分層留證，不主張 backend identity 或費用。

### 已授權與未授權

本輪授權規劃文件及同範圍 add／commit／push。沒有 GUI 前景交接、私人媒體／真實帳本讀寫或產品修改授權。原日常備份 Prompt 的歷史授權與本輪規劃不是同一份新前景；交接文件本身不開啟 GUI 權限。

S1 觀察與 S2 reference 修改是待 Owner 決定的計畫步驟，不是助手可自行展開的工作。S1 必須先有明確資料／觀察範圍與必要前景；不得建 intent 或開下載驗證控制。S2 必須先有具體方法及 Owner 核准。計畫未授予 notes.py、資料模型、相簿或正式 Prompt 的寫入權。

## 傳遞資料與下一步

建議 Owner 下一步：**另開主 Session 啟動計畫 Simplicity Review**，提供本次推送 commit 與以下文件；這是可直接審閱的具體草稿，不需要先交接 LINE。

1. [原始問題提報單](問題提報單.md)、[證據分析](analysis.md)、[plan.md](plan.md)、本 handoff。
2. [planner-report.md](planner-report.md)、[progress.md](progress.md)、[source-manifest.json](source-manifest.json)。
3. 對應版本的記事本 Skill／references、使用手冊 B 區及 AGENTS；審查只需公開來源，不要求打開私人帳本或影像。

需由 Owner 決定的事項：

- 是否接受「先 S1 觀察、無具體缺口不改程式」的 STANDARD 範圍；必要獨立 Plan Review 由人依風險安排，不由 Planner 自行啟動。
- S1 用 Owner 提供的遮蔽現存原件，還是另行授權有界診斷與有效前景。這是診斷來源決策，不是日常新增的模式或內部 JSON。
- S1 有結果後，是否需要核准 S2 的最小 reference 修正。若不需要，保存證據即可，不造空實作。若需要，實作首片後由人啟動第二次 Simplicity Review。

實際備份能力仍由 Owner 使用手冊 B 區正式日常 Prompt 確認；不使用 Harness Acceptance／E2E Prompt 取代、不要求 Owner 帶本開發計畫才能備份。若新方法必須靠臨時教學才能成功，應先記尚未整合缺口，不能宣稱入口已可重用。

## 未解風險與停止條件

底層 UI 原因、事發精確版本、hover 與來源範圍差異、其他 Notes 上下文是否有控制仍 UNKNOWN。沒有原件作用證據不能把照片中的按鈕當 LINE，也不能移植相簿入口。

工具拒絕、缺必要授權或來源、版本／候選不符、身分歧義、寫入衝突、不明派送、exit 70 或需越過計畫邊界時，保留證據並停止依賴該前提的動作；同根因最多三次有證據嘗試，兩次連續無新資訊即停止相同方法。不得自動轉角色修復、重測、接受或結案。

## 交接時六項狀態

- PRIMARY_OUTCOME_STATUS: BLOCKED（五張待下載；本輪沒有新增下載證據）
- IMPLEMENTATION_STATUS: NOT_RUN
- CORE_ACCEPTANCE_STATUS: NOT_RUN
- REQUIRED_VERIFICATION_STATUS: PARTIAL（來源與規劃核對完成；產品檢查 NOT_RUN）
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
- TASK_CLOSURE_STATUS: BLOCKED

Planner 草稿已可交接；整體備份目標尚未達成，不能標 DONE。
