# 給外部 ChatGPT／下一輪 Agent 的啟動 Prompt（E2E → REVIEW／FIX／CLOSE 模板）

> **此段在 E2E 結束時由該獨立 E2E Agent 填寫，並連同 GitHub PR 提交；不自動授權下一輪操作。**

你是本項任務的 **外部流程管控／獨立審查者（目前 Owner 指定 ChatGPT）**。請核對 `[E2E_PR_URL]`、`[EXACT_40_SHA]`、`[APPROVED_PLAN_SHA]`、`[REVIEWED_IMPLEMENTATION_SHA]` 和獨立的 `[EVIDENCE_MANIFEST_URL_OR_LOCAL_REF]`，對照 Owner 原始 AC、真正 Save All／文件／ledger 副作用、歷史資料保護及本輪實際模型來源，逐項給出 **PASS／FAIL／BLOCKED／NOT_RUN**，不可僅憑 Implementer 或 E2E 自述宣布成功。

如有缺陷，僅輸出「單一優先 blocker＋可重現原證據＋最小允許修改路徑＋必要 focused tests＋停止條件」，並為 Owner 準備下一個**全新 Session** 的精準修復 Prompt；若屬重大架構／授權／安全／AC 變動，才交新的 Planner。修完程式需真實 Code Review，且已使用、未知狀態的 Save All 不可再次派送。若所有必要 AC 真實通過且合法結案條件成立，才建議 Owner Merge／Close；你本身不因文字 review 自動合併或操作 Mac。

---

## 1. 階段結果與受審來源
| 欄位 | 真實資料（不得猜） |
|---|---|
| Task / 原始 Owner 目標 | [TASK_ID + ORIGINAL_GOAL] |
| PLAN PR／Plan SHA／ChatGPT verdict | [URLs + exact hashes] |
| IMPLEMENT PR／exact Code Review／Commit | [URLs + HEAD] |
| E2E PR／exact HEAD | [URL + 40_SHA] |
| E2E Model／Provider／Session | [ACTUAL, NOT ASSUMED] |
| E2E accepted source/producer/runtime/grant | [hashes and receipts] |
| Evidence Manifest／Private raw index | [ref, bytes, sha; GitHub 去識別化] |
| 真正 Owner 前景交接及輸入模式 | [AUTO/HUMAN_ASSISTED + evidence] |

## 2. 每項 AC 與真實證據
| AC / 門檻 | 預期 | 實際 | Verdict | 精確證據與 SHA |
|---|---|---|---|---|
| AC0 執行身份及授權 | [填] | [填] | [填] | [填] |
| AC1 目標／排重 | [填] | [填] | [填] | [填] |
| AC2 正式交易／一次派送 | [填] | [填] | [填] | [填] |
| AC3 實體原圖／hash／解碼 | [填] | [填] | [填] | [填] |
| AC4 Durable VERIFIED/readback/release | [填] | [填] | [填] | [填] |
| AC5 第二本／scroll／獨立 grant | [填] | [填] | [填] | [填] |
| AC6 歷史／ledger 完整性 | [填] | [填] | [填] | [填] |

## 3. 實際 E2E 記錄及保護
- 所有 GUI 操作者與輸入來源： [具名 actor / session，不記敏感身份]
- 操作前後保存的真實截圖／AX／SCK／stdout／檔案來源 hash： [最小必要 refs]
- 真正 Save All invocation 次數、未知狀態、chooser 完整 path、目的地空白核對： [填]
- 現存歷史 VERIFIED、原有 ledger 以及不能重送的 intent／reservation： [填]
- 人工輸入只能寫 OBSERVED／OPERATOR_REPORTED，不能當 automatic click PASS。
- 已完成與未完成不得互相抵銷；實際 E2E FAIL 應留在歷史，不因換 Session 抹除。

## 4. 獨立判定／下一輪交接
```text
PRIMARY_OUTCOME_STATUS=
IMPLEMENTATION_STATUS=
CORE_ACCEPTANCE_STATUS=
REQUIRED_VERIFICATION_STATUS=
INDEPENDENT_ACCEPTANCE_STATUS=
TASK_CLOSURE_STATUS=
E2E_VERDICT=PASS|FAIL|BLOCKED|NOT_RUN
FIRST_BLOCKER=
REPRODUCIBLE_EVIDENCE=
BLOCKER_ATTEMPTS_USED=
SMALLEST_APPROVED_NEXT_ACTION=
NEEDS_NEW_PLAN_OR_CODE_REVIEW=
NEXT_STAGE=FIX|PLAN|CLOSE|OWNER_DECISION
NEXT_REVIEW_OWNER=CHATGPT_EXTERNAL
```

**若修復：**下一個 Implementer 的交接必須帶此真實失敗與舊嘗試次數，並沿用已核准的 Frozen Plan／scope；不能新增相同 OCR/NCC 研究或重設交易計數。**若結案：**核對整個 Owner 業務目標而非單一相簿 GUI 成功，只有所有必要 gate 獨立有證據 PASS 才建議 DONE。

## 5. 交件
Commit／Push 本輪真實 evidence manifest、精簡報告及本 Handoff **實例**，開／更新 E2E 階段 Draft PR；不得推私人照片、私人群組名、API key、原始 grant。向 Owner 回報 exact SHA／PR；Owner 轉外部 ChatGPT，**E2E Agent 不得先寫 Reviewer verdict、假造 Controller receipt 或自行宣布通過**。
