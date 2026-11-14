# F01 Planner 人工交接

## 任務與精確版本

本輪依 Owner 指定的 `01_plan_prompt.md` 完成 [plan.md](plan.md) 草案，只處理 F01 原畫面卡片漏登卻完成掃描。不實作、不接受計畫、不啟動下一正式角色。Owner 另授權草案完成後以一個 `gpt-6-luna` helper 梳理上下文、撰寫詳細 commit 訊息，主 Session add／commit／push；helper 無審查或接受權。

- Repo：`/Users/hsiaojohnny/dev/Line_backup`；worktree 為核心目錄；branch：`feature/line-notes-media`。
- 起始及核對到的遠端 HEAD：`f427472335e611ca0efdd8b99011d87d7f7beaa9`；起始工作樹／index 乾淨，保留其他 worktree／忽略檔。
- 原受測產品：`260a49612cb3f7570a57f135921b4101e2c8ee99`；至起始 HEAD 的 `src tests .agents AGENTS.md` 差異 exit 0。
- **待審版本是本目錄 plan／handoff／progress 的共同提交**，由 Owner 攜最終完整 SHA；接手用 `git log -1 --format=%H -- docs/plans/20261102-notes-f01-replan/plan.md` 與該 SHA 核對，再以 `git show <SHA>:<path>` 讀精確內容。起始 HEAD 不是本次規劃提交，文件不預填自己的未來 SHA。
- 本輪只新增三份去識別規劃文件；來源 hashes、實際命令／exit、helper 訊息與 Git 交付結果在 `.local/line-backup/tasks/20261102-notes-f01-replan/`，不入 Git。

## 已完成工作、證據與責任界線

已將 F01 分成來源逐卡列記、page 前雙向對帳、finish 前原件重核、來源變動停止四個步驟。選定三份 Skill／reference 的最小文件候選，列明不新增 CLI／schema 的原因與限制；對帳表本身不證明視覺真實，CLI 仍可能接受自洽但不完整的輸入。

事實：前輪診斷記錄舊原件含 P06、page 2 漏登；本輪讀取診斷、現行產品方法／函式與 overlap 測試，確認既有 CLI 沒有從圖片導出完整卡片集合。本輪未直接重驗原件、未跑真實帳本命令、未操作 LINE；前輪 OBSERVED 不升格本輪觀察。

推論：來源先行、逐卡雙向核對比單純重掃／總數一致更貼近已定位缺口，且不必先引入事件相容風險。能否穩定改善 Agent 行為仍待 C1–C7 與 G-F01，不能由 Planner 宣稱修好。

未知：完整歷史修復嘗試帳、未觀察的來源變動、下次實機可取得情境、provider 實際後端與用量。未知不以設定檔、預期或合成案例補齊。

本輪文件／來源／Git 檢查及命令詳見 [progress.md](progress.md) 與私有任務區。產品最小回歸、C1–C7 實作演練、真實 GUI、獨立 Acceptance 均 NOT_RUN。本輪只是定義這些檢查，沒有執行結果。

## 下一個人工決定與必需輸入

**建議 Owner 另開主 Session 啟動計畫 Simplicity Reviewer**，攜帶本版精確 commit／plan／handoff、[F01 診斷](../20261102-notes-f01-scan-review/issue-analysis.md)、[測試報告](../../../測試報告.md) F01、plan 列出的原 replan／S3 與 Skill 來源。先核對 Git 身分、版本、hash 與允許差異，保留無關 dirty／untracked；不使用 reset／clean 來符合基線。

請審查這三項決策：

1. 只針對原觀察→rows 缺口採流程候選是否充分，對帳是否真的回到原件，而非新一份自我聲明。
2. 三份產品文件、單一首切片與 C1–C7 是否足以驗證，不擴成 parser／sensor／controller；同時保留高卡片、小步補接、非下載附件與來源變動情境。
3. Agent gate 與 CLI 能力界線是否清楚，離線／實機／獨立驗證是否各自保留；本版 STANDARD 不免除原任務 CRITICAL gates。

Owner 決定採納後，另啟動 Implementer，只執行 plan 白名單與 F01-S1；交付精確候選及 V1/V2 後停止。首切片的 implementation Simplicity Review 仍由 Owner 啟動，之後才交獨立 Acceptance；如無剩餘實作不重開無必要 Implementer。此交接不是 Implementer 啟動授權，不沿用舊 S1 的特定免審作本版批准。

真實原件重放、GUI 盤點或任何帳本追加須另具適用資料／任務／前景授權。只下載照片／影片；F02–F18 與其他真實任務仍保留，F01 成功也不能稱整體所有問題完成。不得重下完成項、改歷史、建立 intent／attempt、合併 master、force-push、操作 Issue／PR 訊息或擴其他列表。

版本不符、審查拒絕、需改 CLI／事件／資料／白名單、已提交頁發現缺口或實機不足以完成證明時，保存具體證據與已知結果交 Owner；不跨角色修復／重測／結案。嘗試限制與未知歷史依 plan，不能重置。

## 交接狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: FIX_REQUIRED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

本輪規劃與 Git 交付不等於產品 PASS；最終提交與遠端精確 HEAD 隨本次角色回覆提供。
