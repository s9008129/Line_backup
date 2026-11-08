# Planner 交接：list directory 重新見證（草案 v2）

## 任務與精確版本

- 角色：Owner 以 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/01_plan_prompt.md` 啟動 Planner，承接獨立 Plan Review 的 B1；本輪只修訂計畫。
- Repo／分支：`/Users/hsiaojohnny/dev/Line_backup`／`feature/line-notes-media`；本輪初始 HEAD `0edf5cff88bb605b5c4608990ea6924c0d424e75`，工作樹乾淨，其他 worktree 不整理。
- 目前候選：本目錄 `plan.md` 草案 v2 與本 handoff；交付 commit 以文件所在提交為準。精確 hashes、實際 commit／push／遠端核對保存在 `.local/line-backup/tasks/notes-volume-plan-20261108/planner-revision-b1/delivery-receipt.md`，不自我引用未生成的 commit。
- 前版：v1 計畫提交 `1ac98575d7296cfd943b871ff24c29ed467dc47a`；Simplicity Review 提交 `0e681e45a8a6812f9c9dc1061c1b20379a1b894b`；獨立 Plan Review 提交 `0edf5cff88bb605b5c4608990ea6924c0d424e75`。兩份報告只適用 v1，保留原樣。
- 本輪只改 plan／handoff，新增 `planner-revision-report.md`，追加 progress；原 planner-report、診斷、提報、兩份 review、產品、測試、Skill、手冊、帳本與媒體均保留。

## 本角色完成與限制

Owner 已用白話選擇：「先停下來回報，這版只處理第一次變號（建議；修改較少）」。v2 據此改成**每份帳本至多一筆 `list-directory-reattest`**，不是每個 binding／destination／batch／session 各一次。後續再次漂移一律停止，不補上連續 witness 鏈。

原 completion／v2 intent 的 before witness 不變；old_binding_ref 只可指當時有效的 created／destination。validator 用歷史 prefix 拒絕第二筆事件。新 preview／非精確 replay confirm 遇已有轉接回 `REATTEST_UNSUPPORTED_STATE`；原精確 replay 仍可在新 session 查回，但當前 guard 再漂移回 `REATTEST_CURRENT_BINDING_CHANGED`，不能宣稱現在可用。精確 replay 分支先於首次轉接限額與 stale-tip／無 v3 條件，不新增事件或授權。

新增 T11 覆蓋 D0→D1→D2（第二次在任何 v3 前）、未漂移查回、新 preview 拒絕、session／destination／batch 不重置、graph 拒絕第二筆及零副作用。T3 加上非法第二事件驗證，T10 納入 T11；fresh recovery scan 仍須 START 晚於唯一轉接。S1 仍只讀 preview，需合法新增事件的檢查在 S2。

本角色結論為 `PLAN_DRAFT_COMPLETE`，只代表修訂草案可交審。B1 尚未由獨立 Reviewer 接受；v1 的 REVISION_REQUIRED 未被本 Planner 改成 PASS。原備份仍阻塞，沒有實作或下載。

## Owner 下一步與傳遞資料

1. 決定 v2 是否需要重做計畫 Simplicity Review；前版 PASS 不自動涵蓋能力變更。
2. 另開 CRITICAL 獨立 Plan Reviewer 主 Session，攜帶精確交付 commit／diff、plan v2、本 handoff、`planner-revision-report.md`、原 `plan-review.md`（B1）、`simplicity-plan-review.md`、`issue-analysis.md`、`problem-report.md`、`AGENTS.md`。
3. 審查須確認一次限制、原 witness 比較、精確 replay、第二次漂移停止及 T11 是否一致。未接受前不得啟動 Implementer；本 Planner 不啟動下一正式角色。

仍待決定：是否接受 witness-based binding 轉接與無法排除完美 clone 的剩餘風險、其他首版布局限制、舊 binary 拒絕新 kind 的相容界線。Owner 此次只決定「一次轉接」能力，不代表上述 trust 或整份計畫核准。

核准與必要關卡完成後，才由 Owner 另啟動 Implementer 做 S1 read-only preview；首切片交付仍需人啟動 implementation Simplicity Review，再決定 S2。獨立 acceptance 與真實日常試用各自保留。日常試用使用手冊記事本正式 Prompt，不把本計畫增加成日常入口要求。

## 授權、證據與停止

本輪只授權規劃文件與 add／commit／普通 push。commit helper 只整理提交訊息，不代表正式審查。沒有對真實帳本 preview／confirm、bind／scan／intent、LINE、下載、合併 master 或 force-push 的授權。

事實與當次文件檢查見修訂報告；真實歷史只引用既有診斷，沒有重新讀取帳本或媒體。未知仍包含 device 改變原因、來源連續性、舊 UNKNOWN 晚到、完整 list 子項集合與後續 gate 能否通過。

若要支援第二次轉接、改 completion／candidate／staging guard、擴 restart scope／資料布局／證據 schema 或操作真實資料，停止交 Owner。若重審拒絕或必要檢查阻塞，保留成果與證據後停止，不自動修復／重測／結案。

## 交接時狀態快照

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_REVIEW_OF_V2
```
