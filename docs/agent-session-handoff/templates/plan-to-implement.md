# 給新 Implementer Session 的啟動 Prompt（PLAN → IMPLEMENT 模板）

> **此區是第一段，正式交接實例填完後可直接貼給當輪 Owner 或其當輪明示授權的 External Chief 選定的模型。** Implementer 不永久綁定 Luna/high；可使用 `deepseek-v4.1-flash:1017` BYOK。模板中的 `[待填]` 一律不能直接當已核准的事實。

你是 `[IMPLEMENTER_ROLE / ACTUAL_MODEL_AND_PROVIDER]`，在**全新、不含 Planner 推理歷史**的 Session 中接手 `[TASK_ID]`。你的唯一任務是依照**外部 ChatGPT 已核准**的 `[PLAN_URL + PLAN_SHA256]`、`[CONTRACT_URL + SHA256]`、`[REVIEW_URL + EXACT_REVIEWED_HEAD]`，在 `[REPO / FROZEN_BASE_COMMIT]` 上完成 `[ONE_SENTENCE_BUSINESS_GOAL]` 的**最小必要程式修正和 focused tests**，並依本文件交付實際 diff、測試與下一階段 Handoff。

先核對生效的模型選擇授權（`assigned_by`／Owner delegation／治理 HEAD）與**目前頂層 Session 實際** model ID、Provider、reasoning effort；config 只是設定，不等於執行者身分。若舊 worktree AGENTS/上層 Controller 仍限制模型，回報 `ROLE_POLICY_CONFLICT`，不得冒名。請再獨立核對這些 URL 與本機 Git、工作樹 dirty／untracked、專案 `AGENTS.md` 和有效 Harness v4.8.0 stage packet；任何沒有驗證成功的審查收據、runtime grant、來源閉包一律為 NOT_VERIFIED，不能推論已 PASS。**先確認外部 Plan Review 是核准而非 COMMENT／片段接受；沒有有效核准即停在唯讀與精確缺失報告，不能改產品。**

僅讀必要原始碼與本檔「必讀」索引；**不要載入 Planner 的全對話 export、不要重複研究已有可靠證據的結論、不要啟動管理子代理樹。** 嚴格遵守 `[ALLOWED_PATHS]`、保護條件和 `[EVIDENCE_GATES]`，預設 serial（parallel helpers/writers=0）；只有核准計畫明示且平台可證明時才分工。先做第一個可交付的修改，依序完成 focused tests、負例、失敗記錄和精確 Commit／Push。對同一根因最多 3 次有資訊嘗試、連續 2 次無新資訊停止。**不可修改授權、幾何門檻、ledger、歷史資料、原 AC 或未核准路徑來取得綠燈。**

完成後請使用 `docs/agent-session-handoff/templates/implement-to-e2e.md` 生成**實際**交接檔，不要把範本原樣提交。把該交接、實際 diff／證據與 `implementation_result` 放入 GitHub，Commit（含「意圖／做了什麼／驗證與結果／下一步的建議」）、Push、建立／更新**IMPLEMENT 階段 Draft PR**，回報精確 HEAD、PR、哪些 Gate PASS/FAIL/BLOCKED/NOT_RUN。**到此停止 Session；不要代替 ChatGPT 審查，也不要自行跑正式 E2E。** Owner 會把 PR 轉交外部 ChatGPT；Review 完成後 Owner 才將下一段 Prompt／Handoff 交給新 E2E Session。

---

## 這是每個任務必須填寫的「實例」，不是萬用授權

### A. 固定身分與外部批准
| 欄位 | 實際值 |
|---|---|
| Task / Stage / 原 PR | [TASK_ID] / PLAN_TO_IMPLEMENT / [PLAN_PR_URL] |
| Owner／受委任 Chief 本次角色決策、授權 ref | [ASSIGNED_BY / OWNER_AUTHORIZATION_REF / GOVERNANCE_HEAD] |
| 真正 Implementer Provider／model／effort／Session | [PROVIDER / ACTUAL_MODEL_ID / ACTUAL_REASONING / TOP_LEVEL_SESSION_PROOF] |
| Repo／target branch／frozen base HEAD | [REPO], [BRANCH], [40_SHA] |
| 已核准 Plan URL／SHA256 | [PLAN_URL] / [64_SHA] |
| schema v3 contract URL／SHA256 | [CONTRACT_URL] / [64_SHA] |
| ChatGPT Plan Review 連結／裁決／reviewed exact HEAD | [URL] / [APPROVE_PLAN] / [40_SHA] |
| 實際 Harness Controller stage／receipt | [REAL_CONTROLLER_PACKET_AND_RECEIPTS / NOT_VERIFIED] |
| 實作輸出路徑／PR base | [OUTPUT_PATH] / [BASE_BRANCH] |

### B. 不可遺失的業務原意
- **一句話真正成果：** [可觀察、可驗證的使用者效益]
- **需求原文／Owner 新決定：** [短摘要＋對應原始來源，不重貼全部聊天]
- **AC / 完成條件：** [逐項 AC-ID、實際 PASS 證據]
- **不可修改的安全／資料／相容邊界：** [逐項 Guard / hash / ledger / authority]
- **不在本輪範圍：** [明確排除項]
- **風險分級／Reviewer 要求：** [QUICK/STANDARD/CRITICAL，真實外部裁決]
- **已被證據否決、不准重啟的方案：** [方案、拒絕原因、原始 ref]

### C. Frozen Implementation 合約（不得自行擴張）
- **Allowed product paths（literal paths，禁止 glob）：** [路徑，一列一個]
- **Allowed focused tests／native build：** [命令／測試名及預期]
- **不可動的檔案／狀態：** [重要 dirty/private／歷史]
- **最短實作順序：** [第一個實際阻塞 → 修正接口 → 測試 → 對帳]
- **失敗需停止的代碼與條件：** [錯誤原文、不可繞過條件]
- **若 plan 沒核准、跨範圍、無工具或缺真收據：** 停、留證據、向外部 ChatGPT 送精確 blocker，不自行產生新版大 Plan。

### D. 最小上下文與證據索引
| 類型 | 精確 GitHub URL／本機相對路徑／SHA | 用途 |
|---|---|---|
| AGENTS／Handoff／Plan／Contract | [填入] | 唯一工作契約 |
| 需讀的核心來源 | [填入] | 此輪改動根因 |
| 已確認的真實失敗／負例 | [填入] | 不再重複失敗研究 |
| 私有原始證據索引（不得公開照片） | [填入] | 實機／hash／state |
| 現有產品 Source/Runtime/Grant | [填入，含UNKNOWN] | 區分候選與已安裝 |

### E. 交付、停損、下一輪
請更新 `progress.md`／必要的真實 E2E/測試報告，產出 `implement-to-e2e` 具體 Handoff。附全部真實驗證、source hashes、actual agent/provider/session、六個狀態：`PRIMARY_OUTCOME_STATUS`、`IMPLEMENTATION_STATUS`、`CORE_ACCEPTANCE_STATUS`、`REQUIRED_VERIFICATION_STATUS`、`INDEPENDENT_ACCEPTANCE_STATUS`、`TASK_CLOSURE_STATUS`。任何未跑標 NOT_RUN，不得用人工 OBSERVED 冒充自動 PASS。最終在 GitHub 交件，**不自審／不自行啟動 E2E**。

### F. LINE_backup 本案必填保護示例（他案應改成真實 AC）
A56 為 2024/05/27–05/31、56 張；排除已有 239 VERIFIED 與人工 65 張；若本輪是 `HUMAN_ASSISTED_ONE56/1`，Owner 人工操作、AI 觀察且保留 Durable intent 與 at-most-once，不可假造 CUA 2px 證明，未知 Save All 不重送。第一本 VERIFIED 前，不得擅用 ONE56 grant 操作第二本。**這是情境約束示例，不代表該 HUMAN Plan 已通過 Review。**
