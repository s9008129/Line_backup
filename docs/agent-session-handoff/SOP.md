# LINE_backup：外部 ChatGPT 管控 × Harness 4.8.0 × GitHub Handoff SOP

> 文件性質：**可重用的治理 SOP**，不是 Plan、Implementation Approval、runtime grant 或 E2E PASS。
> 憲法：專案根目錄 `AGENTS.md`。本 SOP 優先保護該憲法與現行已核准交易契約；Universal Harness 4.8.0 原封不動。

## 目標與成本原理
減少 Plus 高階推理額度耗在長期監督與重複上下文。高階 Planner **一次性**產出最小 Plan/機器契約/Handoff，便退出 Session；Owner 將固定 GitHub PR 給外部 ChatGPT Reviewer；通過後由 Owner **選擇模型、開新 Session** 交給 Implementer；再經 Code Review 進入**另一個**獨立 E2E Session。真正跨 Session 的事實儲存在 Git 固定版本、Controller receipts、保留的測試證據與 canonical ledger，而非舊聊天。

## 文件到底何時使用？
| 文件 | 使用時機與負責產出者 | 真正用途 |
|---|---|---|
| `AGENTS.md` | 所有角色每次開始 | 不可擅改的專案治理／安全邊界；不是單次任務 Plan |
| `SOP.md`（本檔） | Owner／外部 ChatGPT 排定階段時 | 決定何時發 Prompt、何時停、何時送審及模型分工 |
| `templates/plan-to-implement.md` | Planner 完成 Plan，**送 Plan Review 前** | **模板**：產出任務特定 `handoff.md`，連同 Plan、v3 contract、SHA 放 GitHub；尚未核准不可交給 Implementer |
| `templates/implement-to-e2e.md` | Implementer 完成實作後，**送 Code Review 前** | **模板**：實作變更、真測試、修正範圍、source/runtime、下一 Session Boot Prompt |
| `templates/e2e-to-close.md` | 獨立 E2E 完成／BLOCKED 後 | **模板**：真機／檔案／ledger 證據、AC 判定、下一輪缺陷 Handoff／結案 |
| 真正的 `plan.md`、`plan-contract.json`、`handoff.md` | 每項實際工作由當階段 Agent 產製並 Commit | 有精確 hash 的**實例**；模板絕不可假充具體任務 Handoff |
| Controller 編譯的 `handoff.json` | Harness v4.8.0 stage packet 實際支援時，由 Controller 確定性產生 | 綁定已審 Contract 的**機器交接**；外部 Markdown 不能代替其 receipt |

**交接實例推薦位置：**`harness-development/session-handoffs/<TASK_ID>/<STAGE>/handoff.md`，同層依階段保留 `plan.md`、契約、`result`、簡明去識別化證據 Manifest。已有 task/continuation 特定位置的專案，**優先沿用現有位置**，不可為了 SOP 遷移歷史。

## 工作流：由外部 Controller 放行下一個角色
1. **Owner → ChatGPT：**提交原始需求、repo、當前 PR/HEAD、保護條件，指定本輪 Planner 模型（ChatGPT 可以建議）；ChatGPT 給 Planner **一次性** Boot Prompt。
2. **PLAN（新 Session）：**最小讀檔 → 業務 AC／風險分類（依 v4.8.0）→ `plan.md`＋v3 `plan-contract.json` → 對應模板形成新 `handoff.md`（開頭必須有接手 Prompt）→ 必要的真實 schema/stage receipts → Git commit/push、Draft Plan PR，報精確 HEAD／Plan SHA／證據。**不用等待／監控 Implementer。**
3. **PLAN REVIEW（本對話 ChatGPT）：**Owner 送 PR URL+HEAD → Reviewer 核對實際 Plan、Contract、Handoff 與 scope／安全／證據，輸出 `APPROVE_PLAN`、`CHANGES_REQUIRED` 或 `BLOCKED`。退回時輸出「問題、影響、最小改動、驗收」；Planner 修正同 Plan PR → 新 HEAD 重審。**只有通過**，Reviewer 才給下一階段實際 Boot Prompt 與需讀的精確 URL。
4. **IMPLEMENT（Owner 指定低成本模型，新 Session）：**先核對 PR/plan SHA、已核准 AC、未提交 dirty、真正權限與受審 source，按 `handoff.md` 接手；只修改 frozen paths，focused tests、保存 hash／真實 FAIL、Commit Push→Implementation Draft PR，形成 `implement-to-e2e` 實例。不擅自新增門檻、重設 ledgers、自己核准自己。嚴重阻塞只交**一項**可執行的決策，停止盲目修復。
5. **CODE REVIEW（ChatGPT）：**Owner 送精確 Implementation PR URL／HEAD／diff／結果／Handoff → Reviewer 檢查程式碼、保護條件、source/runtime、錯誤及測試證據。未通過則原 Implementer 修必要項並提交新 SHA；通過才交新 E2E Boot Prompt。
6. **E2E（Owner 指定模型，另一個新 Session）：**固定 reviewed source、真實 installed runtime/grant/owner foreground 與隔離的驗收路徑；唯一 GUI 操作者（若 HUMAN mode，Owner 是實際人工輸入者）。不得修改產品／AC；獨立驗證 UI、檔案、checksum、ImageIO、VERIFIED／ledger，產出 E2E Handoff／evidence，提交階段 PR／報告。
7. **E2E REVIEW / CLOSE（ChatGPT）：**只基於實際證據裁決 PASS／FIX_REQUIRED／BLOCKED；FAIL 回 Implementer 的**精確修復包**，新 source 經必要 Code Review 後另開 E2E Session。重大業務／安全契約改變才回 Planner 重審；不能只為同一機械修正新開 Plan。

## Git / PR 階段規則
- 每段有實質差異就建立對應 Draft PR；同一階段、同一範圍沿用該 PR 更新；下一階段需要獨立審查 diff 時開新的階段 PR。若前段未合併，建立**有明確 base 指向前一階段 branch 的 stacked PR**，不得偷偷合併或 force-push。若其後要移到 main，先對帳 base 和來源，Owner 決定 Merge。
- 每次審查需固定 40 碼 HEAD、URL、涉及 source 的閉包 SHA 或具體檔案，以及真正的 evidence ref。文件修改後若 HEAD 變更，Reviewer 須聲明有效範圍；更動受審產品內容則重審。
- Commit body 必須有「意圖」「做了什麼」「驗證與結果」「下一步的建議」。私人截圖、照片、群組名、秘密、原始 grant、機器私人路徑不能推公開 Repo。
- ChatGPT 的 COMMENT/文字審查是外部人工可核對的裁決，不自動創建 v4.8.0 Controller/native role receipts，也不自行將 `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED` 改為 PASS。若規格要求 provider-verified approval，要等合法精確機器綁定。
- **Acceptance 身分不得混用：**Harness v4.8.0 的原生 `ACCEPTANCE_REVIEWER` **唯讀**；若 E2E Session 透過核准入口操作 LINE、產生真實交易副作用，它在那一段是「獲授權的 E2E 執行者」，**不能冒充原生唯讀 Acceptance role 或自行製造 receipt**。外部 ChatGPT 可獨立審查其真實結果；若要登錄 v4.8 Controller Acceptance，必須由真正符合 role 的唯讀 Session 及有效 stage packet/receipts 完成。這不是另建一套 Harness，不能因成本而省略 CRITICAL 必要驗收。
- **沒有背景承諾：**外部 ChatGPT 只在 Owner 送出新 PR／要求審查時工作；下一階段的 Prompt 由 ChatGPT 在審查當下提供，Owner 自行轉交新 Session。模型在任何階段均由 Owner 按額度選擇，不寫死。

## 工作量控制及收斂
- **一階段／一主要 Agent／一個可檢查產物**；預設 helper、writer 均為 0。只讀需要的文件，避免貼入全對話 `/export`、整份舊 E2E 日誌或重複引用大量已知問題。
- Handoff 第一屏約 1–2 KB 最重要（角色、目標、HEAD、授權、下一個動作）；正文只保存不可重建的核心決策與差異，冗長證據只用 hash＋GitHub ref／私人索引。**完整 ≠ 把全部歷史重貼**。
- 根因相同最多 3 次有證據的新嘗試；連續 2 次無新增資訊就停、保留 blocker fingerprint，請外部 Reviewer 做一次有界判定，不能跨 Session 重新計數。
- **六個狀態分開回報：**`PRIMARY_OUTCOME_STATUS`／`IMPLEMENTATION_STATUS`／`CORE_ACCEPTANCE_STATUS`／`REQUIRED_VERIFICATION_STATUS`／`INDEPENDENT_ACCEPTANCE_STATUS`／`TASK_CLOSURE_STATUS`。不因 Plan 被核准而把 Implementation／E2E 標 PASS。

## 本案立即適用狀態（閱 GitHub 最新事實為準）
- LINE 相簿目標是兩本不同且合格的原圖 Save All、逐檔 SHA256／完整解碼、正式 VERIFIED；A56 2024/05/27–05/31 共 56 張，人工備份 65 張與歷史 239 VERIFIED 均排除。
- 目前已有 Owner 選擇 HUMAN_ASSISTED 的模式提案（`human-assisted-one56-contract-delta.md`），**仍是 PENDING_EXTERNAL_PLAN_REVIEW**，尚未實作、未執行 Save All、尚無有效 runtime/grant。下一件事是外部 ChatGPT 審核**已存在**的提案，而不是浪費 Sol 額度重新起草。
- 該 Plan 獲核准後，Owner 選擇當輪 Implementer 模型，新 Session 讀**經核准的實例 Handoff**；執行時保持人工／自動輸入分界、原始 ledger 與未知不可重送。B 需 A 成功後單獨 grant。

## v4.8.0 原始來源（只讀，無須另造框架）
- `s9008129/coding-agent-harness/prompts/v4.8.0/01_plan_prompt.md`
- `02_plan_review_prompt.md`、`03_handoff_prompt.md`（optional Handoff reviewer）
- `04_implement_prompt.md`、`05_acceptance_prompt.md`
- `policies/v4.8.0/workflow-routing.md`、`convergence-escalation.md`
- `schemas/v3/task.schema.json`、`schemas/v3/result.schema.json`
- controller 提供的 stage packet/receipts 為準；外部 BYOK session 的運作若沒有真實 Controller invitation/admission，照實標 `CONTROLLER_ADMISSION=NOT_VERIFIED`，**不能以模板冒充機器 PASS**。
