# F01 有界重規劃人工交接

## 任務與精確版本

本次角色為 Planner，依 Owner 指定的 `01_plan_prompt.md` 交付 [plan.md](plan.md) 草案；未接受計畫、實作、操作 LINE、重測或啟動下一正式角色。Owner 另指定完成後使用 GPT-6 Luna 子代理梳理上下文、撰寫提交訊息，再由主 Session add／commit／普通 push。該 helper 只協助 Git 文案，不簽正式審查或獨立驗收。

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- 起始 HEAD `f64ba8dc5875fdb88f2e4ac5b9107896ed90cf87`，前輪兩份診斷文件 dirty／untracked。唯讀核對時它們由外部工作提交為 `7c71a3f1f3fc23eb0a745f09545f6b0a2d121b32`，本機／遠端一致；未由本 Planner 修改或 stage。確認此版本為規劃基準後才建立本輪文件。
- 產品候選 `23e35798fe08f39eddd4b93372688ee2ed4e6edf`；前輪測試 HEAD `5ae930d18a946ab448d4108a15b050d19c07e992`。產品至規劃基準的 `src tests .agents AGENTS.md` 無差異。
- 待審版本為本目錄四份文件的共同提交。Owner 應攜主 Session 最終回覆的完整 SHA，以 `git show <SHA>:docs/plans/20261103-notes-f01-field-validation-replan/plan.md` 讀取；文件不預填自身未來 commit SHA。來源 manifest、命令、檢查、helper 及 Git 回傳留 `.local/line-backup/tasks/20261103-notes-f01-field-validation-replan/`。

## 結論與尚未解除的條件

既有最新 AX／輸入後觀察／page 雙向對帳／finish 原件重核與停止規則已足以定義驗證方法。本版不提出改程式或 Skill，亦不把 `8` 固定為下次捲軸索引。歷史 `10`→`8` 換位是已證實的目標錯用；正確索引能 184→0→184，仍不足以證明底端或程式缺陷。

下一個必要來源決定是：下一次指定列表是前次同一來源、其他既有來源，還是確實獨立的新測試來源？Owner 可自然語言說明，不須填 ledger ID／JSON；接手 Agent 再以連續入口與全部 notes 歷史交叉核對。舊來源有 UNKNOWN／LOCAL_CHANGED 等 blocker 時，隔離帳本或新目的地不能解鎖。目的地可沿用產品預設，不是新阻塞。

計畫已區分有效列表位移、可靠邊界、載入未定及工具拒絕。底端須有當次有效輸入、可辨識外層終止線索、連續末卡／位置與順序穩定、無未解載入；單一 AX 值、hash、兩次不動或只有空白區均不足。沒有可取得的邊界線索時，保留 UNKNOWN 並停止，不重播原迴圈。

本輪重算補充清單 86 項、舊原件清單 14／50 項均相符；清單有重疊，不宣稱 150 個獨立檔案。hash 只支持保存內容完整，不證明畫面語意。實際命令、錯誤及退出碼見 [角色報告](role-report.md) 與私有檢查。沒有新的 GUI OBSERVED；舊報告的人工觀察不升格為本輪工具 PASS。

## Owner 的下一步與資料包

建議 Owner 先決定是否在另一正式主 Session 啟動本版計畫 Simplicity Review，檢查「沿用現有規則即可驗證」與底端／停止判準是否充分；不再安排重複的 High-Reasoning Reviewer。STANDARD 預設檢查點保留，原產品 CRITICAL／獨立驗收 gates 也保留。

必須一併攜帶：本版 plan／handoff／role-report／progress 精確提交、[補充診斷](../20261103-notes-f01-download-review/issue-analysis-addendum.md)、[原診斷](../20261103-notes-f01-download-review/issue-analysis.md)、[前輪驗收報告](../../../验收报告.md)、原 F01 plan／handoff／implementation／SIM-F01-01 重審，以及兩個完整私有 packet：

1. `.local/line-backup/tasks/20261103-notes-acceptance-f01-download/`。
2. `.local/line-backup/tasks/20261103-notes-f01-input-evidence/`，先讀 `evidence-handoff.md` 與 `raw/cua-call-index.tsv`；必要原始 calls／outputs 與當時文件均在其中，不需另泛搜 server log。

Owner 再根據計畫審查結果及來源關係，決定後續：

- 現有方法足夠、來源與權限可核對：另開獨立 Acceptance，先做 F01-V0／V1，再於同一核定範圍內完成 V2。明示是否允許 scan／page／finish 等盤點寫入，重新提供有效前景。僅 F01 盤點不包含下載、chooser 或跨 Session 恢復。
- 發現具體產品／Skill 缺口：先核定差異、白名單、首個實作切片及適用 Plan Review，再由人啟動 Implementer 與 implementation Simplicity Review；本草案沒有預先批准任何產品修改。
- 若只有原來源且 blockers 未解：維持 BLOCKED，另定歷史恢復／資料處置範圍。本計畫不處理那些資料，不建立替代帳本。

上述是 Owner 的條件決策，不是本 Planner 自動派送的多條工作線。先前嘗試歷史不重置；新 Session、正確索引或新目錄不提供新額度。工具拒絕、前景中斷、身份／映射不明、來源變動、讀回差異、已提交漏卡或兩次無新資訊時，按 plan 停止並回報，不跨角色修復。

## 交接時六狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_APPLICABLE_THIS_ROLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PLAN_SOURCE_AND_DOCUMENT_CHECKS_ONLY; NEW_GUI_DOWNLOAD_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED; NO_NEW_ACCEPTANCE
TASK_CLOSURE_STATUS: BLOCKED
```

Git 交付成功不等於計畫接受或產品通過。本角色完成規劃及本次明示 Git 交付後停止，後續由 Owner 決定。
