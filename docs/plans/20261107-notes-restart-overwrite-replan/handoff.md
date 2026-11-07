# 記事本重下與確認取代：Planner 人工交接

## 任務、版本與本輪權限

Owner 依 `01_plan_prompt.md` 指定本 Session 為 Planner，要求重規劃 `NOTES-INTERRUPTION-RECOVERY-GAP`。本輪交付 [plan.md](plan.md)、[進度](progress.md)、[角色報告](role-report.md)；未實作、未接受計畫、未開始其他正式角色。

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；branch `feature/line-notes-media`。
- 起始及當次查得遠端 HEAD：`7df6830728cb448052de0a2c065d4d039158e204`。初始工作樹／index 乾淨，其他 worktree 與所有私有資料保留。
- 待審候選是**本目錄四份 Markdown 的共同提交**；最終完整 SHA 由本輪回覆與私有交付 receipt 提供，不以起始 SHA 當新版版本。接手可執行 `git log -1 --format=%H -- docs/plans/20261107-notes-restart-overwrite-replan/plan.md` 定位，再用 `git show <SHA>:<path>` 取得共同提交內容。
- 原計畫／handoff 仍保留在 `20261107-notes-interruption-replan/`，舊共同提交 `414e61db1cd42e85c27d1edeef3cbb06d77bc2c2`；舊 Simplicity PASS 不涵蓋新版，舊 PR-B01 不被假稱已解。
- 本輪僅可新增規劃文件及專案私有任務證據，並依 Owner 授權 add／commit／push。沒有 GUI、取消、真實帳本追加、下載或真實資料取代授權。

## 交接結論與最小改動方向

**PLAN_DRAFT_COMPLETE。** 新版不再受文件限定；規劃記事本 CLI／event replay／版本／scan gates 的必要修改與測試，再整合回既有 Skill 與單一日常 Prompt。

候選流程：自動找回 → 完整核對受影響貼文 → 白話一次確認整批所有可備份媒體 → 新 raw 逐項下載 → 獨立 bytes copy 與完整驗證 → 單筆事件啟用整批新版本。再次中斷保留已驗證 candidate，依同批有效確認只重下不確定／未驗項；不在同 attempt 再送。

「覆蓋」的建議預設是新版本成為目前備份，實體路徑使用新版本目錄，舊路徑及舊 UNKNOWN／completion 原樣保留。這必須在預覽與確認內說清楚，不能把 Owner 的「所有」偷偷縮成單檔或擴到整庫。若 Owner 要求相同實體路徑原地覆寫，此候選不能直接實作，先由 Owner 決定重規劃。

本輪新確認的程式事實：現 `notes.py:3492` 以 hard link 發布 raw，晚到舊 fd 仍可能改正式 inode；新候選須持久獨立複製，不能只換目錄。`media_verify.py:252` 可重用 exclusive copy，但目前照片副本是驗證暫存，影片未用此方式持久發布。現完成模型一 media 一 completion、UNKNOWN／LOCAL_CHANGED／pending／scan gates 也需同步 writer 與 replay 調整，不能只改 intent gate。

## 下一個人類決定與角色順序

建議 Owner 另開主 Session，啟動**計畫 Simplicity Reviewer**，第一步核對本版共同提交與來源，再判斷「批次確認＋獨立副本＋單一 activation」是否最小充分。其後由 Owner 決定獨立 Plan Reviewer；CRITICAL 的獨立計畫審查不能跳過。

實作前要核定的三項預設：

1. 恢復批次包含本列表需要重新開始與 LOCAL_CHANGED 的受影響貼文；每篇全部可備份照片／影片包含已完成 sibling，其他正常完成／純 LOCAL_MISSING 不重下，排除／受保護不解除。
2. 以新實體路徑啟用目前版本；舊原件留原路徑，無自動清理與資料遷移；接受重複傳輸，不宣稱舊 UNKNOWN 已停止。
3. 真實批次一次確認涵蓋同範圍完成前再次中斷；範圍／身分／目的地策略變動再確認，歷史重試限制不重設。

P3 另須檢查 LOCAL_CHANGED 在 scope 內外的 gate、舊 pending publish 退休關聯、scan 中斷／新綁定、版本相容性、候選 copy／manifest／activation crash 矩陣，以及 CUA 當次輸入可靠性。這些決策不能交 Implementer 臨時放寬。

S1 是離線可驗證的垂直切片，非六檔文件小修：用一篇 LOCAL_CHANGED＋一篇 UNKNOWN 的合成資料驗未確認拒絕、確認後新 attempt、獨立檔案與整批啟用、重開讀回。產品／測試白名單及 C01–C12 詳見 plan。S1 完成交 Owner 啟動首切片 Simplicity Review；有剩餘工作才由 Owner 另交 S2 整合 Skill／手冊與完整回歸，不自動跨角色修復。

最終實機確認仍用手冊第 5 節正式日常 Prompt，不把 Acceptance／E2E 角色 Prompt 當備份入口。先在 Owner 另行指定、允許重下的測試列表做照片／影片與跨 Session；原私人列表套用時仍需精確預覽／批次確認。驗收者可獨立映射證據，任何真實 GUI／資料操作另須當次日常授權與前景。Planner 的新方向不是任何一批真實覆蓋的同意。

## 必須攜帶的輸入與證據界線

- 本目錄四份 Markdown 與最終共同提交 SHA。
- [Owner 意圖及重規劃要求](../20261107-notes-interruption-replan/plan-review-owner-intent.md)。
- [根因分析](../20261107-notes-interruption-review/issue-analysis.md)、[舊計畫](../20261107-notes-interruption-replan/plan.md)、[舊 handoff](../20261107-notes-interruption-replan/handoff.md)、[舊 Plan Review](../20261107-notes-interruption-replan/plan-review.md)。
- 精確候選的 `notes.py`、`media_verify.py`、notes Skill／references 與測試；本輪來源版本／hashes 存 `.local/line-backup/tasks/20261107-notes-restart-overwrite-replan/sources-before.json`。
- 私有任務區內命令／exit、文件檢查、同角色 helper 摘要與 Git receipt；跨機器沒有該區時，公開角色報告已列來源與檢查範圍，不要求交出私人原始畫面或帳本。本次未重讀那些真實資料。

事實：起始 Git 狀態與唯讀源碼映射支持上述缺口；Owner 已接受設計上重下並要求覆蓋前詢問。推論：獨立版本與單一啟用比原路徑覆蓋更容易保存唯一資料及恢復。未知：原 chooser、平台晚到輸入、LINE 實際落點、新機制實機可用性；沒有產品 PASS、GUI OBSERVED 或獨立接受。

同角色繼承設定的 native helper 只唯讀映射源碼；Owner 指定 GPT-6-luna helper 在草案完成後梳理上下文、擬詳細提交訊息。兩者都不是後續正式角色，不給接受。模型請求參數、平台顯示與 provider usage 各自留證，沒有證據的層次標 UNKNOWN。

未解風險不以無限重查解決：來源／path／scope／授權不明、chain 損壞、前景失效、工具拒絕、exit 70、寫入衝突或範圍外需求時停並交 Owner。不能為了恢復而修改現行產品、真實帳本或重設歷史嘗試次數。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

文件與來源檢查是本輪 Planner 交付驗證；產品、真實 GUI、再次中斷恢復與獨立接受皆未執行。草案交付不代表整體修復 DONE。完成本輪授權 Git 交付後停止，由人決定下一正式角色。
