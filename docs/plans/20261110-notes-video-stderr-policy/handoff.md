# Planner 交接草案 v1

## 任務與精確版本

- 任務：記事本影片 stderr 政策的一致化規劃。
- 計畫：[plan.md](plan.md) v1；來源：[issue-context.md](issue-context.md)；報告：[planner-report.md](planner-report.md)；進度：[progress.md](progress.md)。五份文件以本輪提交它們的 commit 為精確草案候選，接收者應用 Git 取得完整 SHA，不以檔名或日期代替版本。
- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`；產品基線 `2f53bebd0875239312dacb0cb2cf843792a6377d`。
- 起始 tracked／index 無差異；Owner 的 `issue提交單.md` 是既有 untracked 私人原件，保留且不提交。沒有產品檔變更。

## 本角色結果與授權

Planner 已完成可執行的有界草案：推薦 C，僅將 ffmpeg **逐 stream 解碼 stderr** 與完成判準分開。ffprobe、工具版本、照片、coverage、工具 pin、穩定性、身分及禁止重送條件保留。這不是產品批准；只授權本輪文件、來源核對、Git checkpoint／push，以及 Owner 指定的 Luna 提交訊息協助。

事實：Skill、runtime、持久化 loader 都要求空白 stderr；原 plan／AGENTS 沒有把它另列需求。相同 DTS 訊息在 FFmpeg n7.1.1 原始碼屬 AV_LOG_ERROR。推論：空白通道被用作較嚴格的代理，需由 Owner 決定產品語意。未知：完整診斷、事故 coverage 與目前真實狀態；不把 exit 0／progress end 當作已通過全部檢查。

提交單描述 Post1 已有 candidate、Post2 已下載但沒有 candidate／completion，批次未 activation。這是既有報告，本輪未重看 LINE、讀真實帳本／媒體或重跑。所有原件與 UNKNOWN 仍須保護。

## 下一個人工決定

請 Owner 決定是否採 C，且接受：**未知診斷若伴隨 exit 0 與全部硬性證據成立，不再僅因 stderr 非空而拒絕**。此選擇不代表已證明每筆診斷無害。probe 與版本探測仍嚴格，不加入 allowlist，也不增加日常核准步驟。

建議 Owner 先以精確草案 commit，另開主 Session 啟動計畫 Simplicity Review，隨後為此 CRITICAL 變更啟動獨立 Plan Review。兩者都是對草案的檢查；通過及 Owner 核准後，才開 Implementer。本輪停止於此，不自動派送正式角色，不進行實作／修復／重測。

若 Owner 選 A 或 B，須修訂計畫候選並決定哪些審查重做；不能讓 Implementer 在三案間自行切換。若因證據或語意不明而拒絕，保留所有已證事實並停止，不在同一輪跨角色修計畫或補實作。

## 交給下一主 Session 的資料

1. 使用者這次要求、專案 `AGENTS.md`、相應 v4.9.0 角色 Prompt 及手動政策。
2. 本輪精確草案 commit 與五份文件；產品基線 SHA。未遮蔽 `issue提交單.md` 只在本機受權範圍查看，不送外部審查。
3. 本機 `source-baseline.json`、唯讀命令退出碼與檢查 log；外部審查僅傳公開摘要與產品來源。
4. 兩個待明確認可的政策邊界：C 對未知診斷的處理，以及新 payload policy／legacy 嚴格預設。不改 probe、不回寫舊歷史。
5. 後續 S1 的可寫路徑、成功反例與必要命令以 plan 正文為準，handoff 不擴張它。

## 後續實作與驗證注意

- S1 必須同時對齊 runtime、normalizer、ordinary verification 與 restart candidate loader；不能只刪一行 gate。
- 新識別才啟用 C，無識別仍依舊嚴格政策；未知識別或 stderr 欄位矛盾拒絕。舊 clean candidate 與新診斷 candidate 的合成批次可重開。
- 合成正負例、真實合成影片解碼、既有最小回歸與 S1 Simplicity Review 不替代獨立驗收。必要工具缺失／skip 保持 NOT_RUN。
- 真實 verify 會寫 candidate，`restart resume` 可能自動 activation；本案沒有授權使用兩者操作真實資料。不能用 resume 包裝成「只重新驗證」。
- 未來若處理 Post2，先另定精確既有 attempt、檔案、相容版本、Session／scan 綁定、單次次數與候選可寫範圍；不建立新 intent、不重下、不順手 reattest 或 activation。條件不符停止，不套用歷史綁定。
- 真實列表完成與實際可用性確認仍由 Owner 用手冊的正式記事本備份 Prompt 與有效前景交接啟動；不得改成 Harness Acceptance／E2E Prompt。這份計畫不成為新的日常依賴。
- 不 merge master，不 force-push；不提交私人照片、ledger、原始畫面／檔名。新事件寫入後，不能以刪除或重寫事件回退相容性。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE; BACKUP_NOT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: PLANNER_SOURCE_AUDIT_ONLY; PRODUCT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_POLICY_AND_PLAN_REVIEW
```

Git 提交／推送結果以實際命令與最終回覆為準；Git 成功不構成獨立接受或列表完成。
