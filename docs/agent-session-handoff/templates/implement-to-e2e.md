# 給新獨立 E2E Session 的啟動 Prompt（IMPLEMENT → E2E 模板）

> **正式使用時先填完整下面的審查及真實權限欄位，再把本段給 Owner 選定模型的新 Session。** 本模板不能創建 grant。

你是 `[OWNER_SELECTED_E2E_MODEL_AND_PROVIDER]`，使用**新的、與 Implementer 不共用推理歷史**的 Session，獨立驗收 `[BUSINESS_GOAL]`。驗收對象只能是外部 ChatGPT **真正核准的** `[IMPLEMENTATION_COMMIT_40_SHA]` 與 `[CODE_REVIEW_URL]`，搭配已確認相同的 installed source closure、producer、decoder、runtime binding、config 與合法 grant。先唯讀核對 `[APPROVED_AC_AND_PLAN_SHA]`、原始資料保護、`[REAL_EVIDENCE_INDEX]`；不得把 Implementer 自述或離線 fixture 當 E2E PASS。

若 `[RUNTIME_GRANT]`、Code Review、實機工具、權限、當次 LINE 前景或本輪模型真實 Session ID 缺失，立即回報 BLOCKED，不能為了測試而消耗唯一 lifecycle／GUI 配額。Owner 才能進行任何明確指定的人工操作；**若本輪 HUMAN_ASSISTED，嚴禁 Agent 假冒人工輸入紀錄或自行點擊人工階段**。如果是核准全自動模式，只有一個合法 E2E GUI 執行者，不能與開發 Session 同時操作；嚴守原點擊幾何／身份／交易限制。

在合法前置條件成立後，用真正來源／裝置／檔案驗證逐項 AC，記錄畫面、AX／SCK、實際操作、持久 intent、at-most-once 記錄、Chooser、下載檔案、逐檔 hash、完整 ImageIO 解碼、VERIFIED/readback／release。Save All **最多一次**，結果不明不得重送，也不得補造成功。先完成 A 並 VERIFIED，B 需要新的身分核對與自己的 grant。

**角色邊界：你執行有副作用的正式 GUI／交易期間是經授權的 E2E Executor；Harness v4.8.0 原生 `ACCEPTANCE_REVIEWER` 是唯讀角色，不能把 Executor 操作憑空寫成該角色的 admission 或 receipt。真正原生 Acceptance 若被 workflow 要求，仍需由符合條件的獨立唯讀 Session／控制器完成。**

你只能讀受審產品與正式狀態、執行核准的業務流程及在隔離 evidence 目錄寫驗收資料；不能修改產品程式／原始 AC／測試 fixture／授權或原 ledger。任何 FAIL/BLOCKED 保留原證據並回報。完成後以 `docs/agent-session-handoff/templates/e2e-to-close.md` 產出**實例交接**、E2E Evidence Manifest 和獨立裁決，Commit／Push 到 E2E 階段 Draft PR（若無新差異則不製造 empty commit）；由 Owner 把 PR、HEAD 轉交外部 ChatGPT 審核；**本 Session 不自行宣布整體交付完成。**

---

## A. 待驗收的固定身分與真正批准
| 欄位 | 必填 |
|---|---|
| Task / frozen AC／Plan／Contract SHA | [TASK_ID / URL / HASHES] |
| Owner 指定實際 E2E 模型／Provider | [MODEL_ID + PROVIDER] |
| Implementer PR、受審 Commit、ChatGPT Code Review | [URL / EXACT_40_SHA / URL + VERDICT] |
| 實際 Source closure／Installed source closure | [64_SHA / 64_SHA / MATCH?] |
| Producer／Decoder／Runtime-binding | [SHA / SHA / SHA] |
| Authority mode／grant／ledger／可執行 entry | [AUTO_OR_HUMAN / VALID / refs] |
| LINE 前景交接／唯一 GUI operator | [當次授權及時間；缺失填 NOT_READY] |
| 證據專用 private 路徑／公開報告 | [本機相對路徑；禁止 GitHub 推原圖] |

## B. 本輪真實 AC（由已核准 Plan 複製，不得自行增刪）
[逐項 AC0...、所需實際證據／不得以模擬替代的 gate；對 HUMAN 模式明列 Owner 與 E2E Agent 的角色界線。]

## C. 必讀最小索引
- 專案憲法：`AGENTS.md`
- 已核准 Plan/Handoff： [URLs + HASHES]
- Implementation exact Code Review： [URL + VERDICT]
- 真實入口： [路徑＋命令或經授權交互方式]
- 安裝與 authority 收據： [Refs；不存在填 UNKNOWN]
- 保護 baseline 與上次真正失敗： [Refs＋SHA；不要全量載入歷史聊天]

## D. 核對與真實流程
1. **AC0 Readiness：**凍結版本、工具、唯一 GUI、前景、授權、目標相簿 eligibility、保護基線及已有 intent/ledger。缺一不可啟動真交易。
2. **UI／行為：**新鮮身份 → 正確目標 → 相簿網格 → 功能表／儲存全部（依核准模式完成真實證據）→ 原持久 intent → 至多一次真派送。
3. **檔案：**核對 exact chooser destination／空資料夾、檔案穩定、正確張數、每檔 SHA-256、完整影像解碼，不能只看 GUI 成功。
4. **狀態：**VERIFIED durable commit／readback／release，檢查原 ledger／239 VERIFIED／人工65排除不變；B 只在 A 完成且獨立授權有效時操作。
5. **不明／錯誤：**保留 raw 與 hash、意圖和配額，停；不知道是否派送就不重發；不改產品做實驗。

## E. 真實驗收回報格式
```text
E2E_ACTUAL_SESSION_MODEL_PROVIDER=
REVIEWED_IMPLEMENTATION_HEAD=
REVIEW_AND_AUTHORITY_BINDING=
AC0=NOT_RUN; AC1=NOT_RUN; AC2=NOT_RUN; AC3=NOT_RUN; AC4=NOT_RUN; AC5=NOT_RUN; AC6=NOT_RUN
A_SAVE_ALL_DISPATCH=UNKNOWN_OR_0_OR_1
A_FILE_COUNT=NOT_RUN
A_HASH_AND_FULL_DECODE=NOT_RUN
A_VERIFIED_READBACK=NOT_RUN
B_IDENTITY_AND_GRANT=NOT_RUN
B_SAVE_ALL_AND_VERIFIED=NOT_RUN
HISTORY_AND_LEDGER_INTEGRITY=NOT_RUN
INDEPENDENT_E2E_VERDICT=NOT_RUN
FIRST_REAL_BLOCKER=
EVIDENCE_MANIFEST_AND_SHA=
NEXT_ACTION=
```
填實際結果，不要沿用模板的預設狀態作偽裝；每項有 raw refs。報告與 `e2e-to-close` 實例送 GitHub Draft PR，**請 Owner 轉交 ChatGPT 獨立驗收 Review**。
