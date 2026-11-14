# Planner 交接：記事本檢查邊界 v3（待核准）

## 任務與精確版本

本輪依 Owner 指定的 `01_plan_prompt.md`，只修正舊計畫的環境附屬項邊界與防再發驗證。結論為 `PLAN_DRAFT_COMPLETE`，不是計畫核准、產品 PASS 或真實接續完成。

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`，目前主 worktree。
- 分支／起始 HEAD：`feature/line-notes-media`／`b635218da3ba4dbcfe563897e0d94515fe713414`；起始工作區乾淨，本輪查得遠端同 HEAD。
- 本版：同目錄 `plan.md` v3、此 handoff、`planner-boundary-revision-report.md`、追加的 progress。
- 精確交付 commit：以包含以上檔案的本輪提交及私有 `delivery-receipt.md` 為準，不在提交中自我引用尚未生成的 SHA。
- 接手執行 `git log -1 --format=%H -- docs/plans/20261108-notes-volume-identity-reattest/planner-boundary-revision-report.md` 找交付提交；若之後有產品／計畫實質漂移，先釐清，不自行換基準。
- 原 v2 計畫／handoff 在 `2b742b9ef670a6b618b794432e11d1af6c009f1b`。原審查、診斷、報告、歷史 S1 handoff 均保留，不把其 PASS 套到 v3。

## 本角色交付與未完成工作

已將「整個容器不得有帳本以外項目」改成保護受管理媒體、原交易及目標碰撞。草案只界定精確名稱 `.DS_Store` 的未引用 regular file、nlink=1，先檢查受管理名稱，不忽略全部 dotfile。同名 symlink／目錄／異常 hardlink、額外影片、未知 staging、證據損壞仍拒絕。

計畫涵蓋 reattest、completion／active 投影、新 intent staging、inventory、普通／restart 發布與收尾。發布後只剩合格環境項的 staging 應保留原檔、正常完成，不因 rmdir 失敗留下假 pending。未改產品或資料，尚未執行任何 V1–V9。

v2 的 Owner trust／clone 剩餘風險同意有效；每帳本一次、device-only、精確 replay、原 OPEN_BATCH 與 fresh recovery scan 不變。本次只核准邊界修正，不要求重新同意既有風險，也不把新計畫當成真實 reattest 同意。

私有證據：`.local/line-backup/tasks/notes-environment-boundary-plan-20261109/`。文件檢查、實際命令／exit／hashes 與保留核對見同目錄角色報告。產品測試、LINE、真實帳本、下載、解碼、實際跨 Session 及獨立接受均 `NOT_RUN`。

## 人工下一步與必傳資料

1. 由 Owner 決定 v3 與適用重審。因涉及拒絕邊界，建議人啟動計畫 Simplicity 與 CRITICAL 獨立 Plan Review；不讓同角色助手給正式接受。
2. 審查與核准完成後，由 Owner 在另一主 Session 啟動 Implementer（04），先做 v3 的 F1；不再重做舊 S1 的新增 preview 或 S2 的新增 confirm。
3. F1 交付候選與局部證據後停止，供人啟動 implementation Simplicity；若尚有 F2，再由人續交，否則不製造空實作。
4. 獨立接受須對映要求與證據。真實可用性另以手冊記事本正式日常 Prompt＋前景啟動，不改成 Acceptance／E2E 角色 Prompt，不增加 Owner 啟動步驟。

必傳：
- Owner 本輪交辦、`AGENTS.md`、01／04 相應角色 Prompt、4.9.0 workflow／subagent policies。
- 本版 plan／handoff／角色報告、精確 commit／diff、`docs/根因調查報告.md`。
- 原 v2 設計提交、`plan-review-v2.md`／`simplicity-plan-review-v2.md`、20261108 S1 handoff 中的 Owner 核准紀錄（作歷史來源，不套用其舊範圍）。
- 現有 `notes.py` 與 v3 列出的測試及操作文件；公開交接不附私人原始 receipt／圖片／帳本鍵。
- 若查原始事故證據確有必要，只在專案私有 `notes-preview-20261108/` 定位原 receipt；開發角色不藉此另讀寫真實媒體或帳本。

Implementer 前置必須是**已核准的 v3 plan／handoff**、Owner 決定的適用審查結果與精確候選。現在尚未核准，不能把本 handoff 的未來式當成執行授權。

## 實作邊界與檢查責任

完整可寫路徑及 V1–V9 以 plan 為準。產品僅 notes.py，測試限 reattest／records／restart／regressions／e2e_media 五檔；操作文件僅 notes Skill 兩份 references 與手冊記事本衝突文字。原事件、證據 schema、相簿、媒體驗證器、真實帳本與媒體不可動。

F1 指定三個局部 suite：`test_notes_reattest.py`、`test_notes_records.py`、`test_notes_restart.py`。F2 依變更選局部檢查，最終跑 plan 指定的三條最小完整回歸。證據須包含業務狀態、第一支完成／hash、attempt、manifest、pending、原始事件及新 Session 重讀，不能只測名稱分類函式。

V9 的實際派送、前景、兩支影片與跨 Session 由正式日常入口證明；合成測試不代替。若當時第二支仍 UNKNOWN，只能依原規則查證或精確批次，不能因環境項消失便重送。

## 事實、推論、未知與停止

事實：起始 Git 乾淨；現有程式多處比完整名稱集合；舊計畫明訂拒絕 `.DS_Store`；根因報告記原 preview exit 4。這次沒有再執行原 preview，刪檔是否仍缺席也未重查。

推論：只修第一個 gate 不能消除其餘同根因拒絕；因此需要同一條流程一致修正。靜態可達風險不是每處已實機重現。

未知：device 改變原因、第二支晚到／來源現況、原 OPEN_BATCH 當前適用性、外部 writer、真實修正後接續結果。均不得預填 PASS。

若必須擴路徑、分類、schema、公開介面、restart scope、刪附屬項、改歷史、取消防重送或操作真實資料，保留具體證據停交 Owner。拒絕或未解 blocker 不自動修復／重測／結案。同根因最多三次有證據嘗試、連續兩次無新資訊即停；exit 70 不是重送或改入口的理由。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NO_PRODUCT_CHANGES_THIS_ROLE; BOUNDARY_FIX_NOT_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: NOT_RUN; ORIGINAL_SECOND_VIDEO_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; V1_V9_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_V3_APPROVAL_AND_APPLICABLE_REVIEWS
```
