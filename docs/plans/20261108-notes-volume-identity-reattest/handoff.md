# Planner 交接：list directory 重新見證（草案 v1）

## 任務與精確版本

- 角色：Owner 以 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/01_plan_prompt.md` 啟動的 Planner，只做規劃。
- Repo／分支：`/Users/hsiaojohnny/dev/Line_backup`／`feature/line-notes-media`。
- 初始 HEAD：`9027d8ea4df41480b785017a7c57a39813907e65`；初始工作樹乾淨。其他 worktree 不修改、不整理。
- 計畫：本目錄 `plan.md` 草案 v1；尚未核准。交付 commit 以本文件所在 commit 為準，私有 `delivery-receipt.md` 另記精確 HEAD、文件 hashes 與遠端核對，避免在文件內自我引用未生成的 commit。
- 原提報、根因診斷保留原樣；本輪只新增 plan、handoff、planner-report，追加 progress。未改程式／Skill／測試／帳本／照片影片。

## 本角色完成與可主張的結論

已以原始碼確認：list directory gate 使用 destination 的 device／inode，既有 restart 可在精確 scope 處理 LOCAL_CHANGED；本草案因而採 list-only 追加式轉接。完成可執行的 CLI／事件 schema、witness、確認／查回、OPEN_BATCH、fresh scan gates、相容限制、首切片與驗證 owner 設計。

結論為 `PLAN_DRAFT_COMPLETE`，不簽發 plan PASS 或產品 PASS。remount 成因、同物件連續性、舊 UNKNOWN 晚到與真實接續均未證明；前輪 28 events 等真實資料結果只作原證據引用，本輪未重新讀取真實帳本／媒體。

本輪實際來源、命令、exit、檢查與六狀態見 `planner-report.md`；最後交付核對放專案私有 `.local/line-backup/tasks/notes-volume-plan-20261108/`。Owner 指定 GPT-6 Luna helper 只在草案完成後整理 commit 訊息；不作獨立 review 或 acceptance。

## 人工需要決定的事項

1. 是否接受「witness 相符＋精確 Owner 同意的 binding 轉接」，並承認不能排除完美 clone／無法證明 remount。如果要求更強來源連續性，保留阻塞，不把此草案當成可行放行。
2. 是否接受首版限 OPEN_BATCH 尚無 v3、完整 v2 witness、空舊 staging 與簡單布局；其他情況明確拒絕。前輪尚未證明真實完整 list 子項集合符合這個布局。
3. 是否接受 CRITICAL 人工關卡、舊 binary 不可讀新增 event kind 的相容界線，以及真實測試須另授權。不藉計畫核准授權對真實帳本 confirm 或操作 LINE。

這些決策均待 Owner；本輪規劃與文件提交已獲授權，沒有把待審設計當成既有同意。

## 下一步與必須攜帶的資料

建議 Owner 先另開 **Simplicity Reviewer（plan）主 Session**，提供本目錄 `plan.md`、本 handoff、`issue-analysis.md`、`problem-report.md`、`planner-report.md`、精確交付 commit／diff 與 `AGENTS.md`。此關卡通過後，再由人啟動 CRITICAL 的獨立 Plan Reviewer。兩者都不是本 Planner 的子代理工作。

有權限的 reviewer 如需原始證據，參考診斷列出的私有 `notes-volume-review-20261108/` 及原任務；不將原始帳本 ID、群組／人名、媒體檔名、grant 或截圖搬入公開 Git。只審設計不需要執行真實 notes 命令。文件 SHA-256 保存在本輪私有 `artifact-hashes.txt`。

Owner 核准計畫與必要關卡後，才另啟動 Implementer 的 S1：read-only preview＋合成 witness／零副作用檢查；不得先加入 confirm 或有效 binding projection。首切片交付仍需人工啟動 implementation Simplicity Review，再決定 S2。完整產品 acceptance 與真實日常試用分開；日常試用仍用手冊的記事本正式 Prompt，不能要求使用者另讀這份開發計畫才能備份。

## 停止條件與授權

本輪只獲規劃與文件 add／commit／push 授權。不操作 LINE，不 bind／scan／intent／reattest 真實帳本，不改 restart scope，不解除 UNKNOWN，不合併 master、不 force-push。後續若實作需要 completion／candidate／staging reattestation、跨帳本協調框架、不同資料布局或證據 schema，先交具體 evidence 由人定路線，不沿用本計畫偷偷擴案。

審查拒絕、缺 source／authority、候選不符或必要檢查阻塞時，紀錄已知與未知後停止；不由本角色修復、重測或啟動下一角色。

## 交接時狀態快照

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_PLAN_REVIEW
```
