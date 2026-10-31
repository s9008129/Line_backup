# 修正後獨立驗收交接

先讓新 Session 執行下方離線驗收；準備好至少兩本合格未備份項的指定列表後，再實際提交 [使用手冊的唯一正式 Prompt](../../LINE相簿備份_使用手冊.md)。那則訊息即同時授權備份與交接前景，不需逐本確認或第二道開始命令。本文件本身只授權驗收，不授權 LINE 操作。

```text
請在 /Users/hsiaojohnny/dev/Line_backup 擔任獨立 Acceptance / E2E Reviewer。
你及助手不得是本修正候選的實作者或實質貢獻者。
讀取 /Users/hsiaojohnny/.codex/prompts/v4.9.0/05_acceptance_prompt.md、
專案 AGENTS.md，以及 docs/plans/20261031-skill-precision/ 下的
plan.md、原 acceptance.md、fix-01.md 與原 implementation.md。

候選是 fix/save-all-gate-20261030 上首次加入 fix-01.md 的修正 commit；
以 git log -1 --diff-filter=A --format=%H -- docs/plans/20261031-skill-precision/fix-01.md
解析並記錄完整 SHA，
核對 HEAD 等於該 commit，
且產品 tracked/staged diff 無其他變動；不符合就停止。
修正基線為 5873db760fcbe561707c77f2b9049e447bfaf5fe。
Owner 已明示跳過另一次實作獨立審查，直接進 independent acceptance；
記錄這個決定，不補造審查 PASS。

保留兩份既有 acceptance.md（20261030-save-all-gate 與本任務）及
所有無關 dirty/untracked，不修改產品、不修補發現、不自動重測。
目前只授權唯讀及離線驗收、私有隔離 fixture 與新報告。
不得 commit、push、merge 或 CI。

將 F-01 至 F-06 逐一映射新候選的實際證據。
特別驗證：人工來源不是第七狀態；完整證據的人工備份只計一次
COMPLETED，僅聲明／證據不足保護，不覆蓋 UNKNOWN／pending、
不默認 EXCLUDED；只有舊證據不足的歷史保護可跳過，
pending 命名、活動下載、未知派送不得跳過另送。
並核對 README root、歷史範本註記、截圖／OCR 的當次同意、
必要範圍、本機私有保存及不上傳外部服務。

獨立核對 Skill quick_validate、Markdown 引用與 anchors、diff check，
及既定 test_daily_records.py 最小回歸；保留真實命令與退出碼。
可使用既有專案私有驗收 venv，不改全域工具或產品依賴。
過去離線 PASS 只保留原候選範圍，不直接移作新版 PASS。

只有收到我實際提交的使用手冊正式備份 Prompt 及有效前景，
才依 Skill 核對單一列表、目的地、排除與原任務對應後，
驗收至少兩本合格未備份相簿的真實端到端流程。
BACKUP_ROOT 留空與 EXCLUSIONS=[] 是有效預設，無須另外索取
非預設位置；只有前景或「請驗收」不等於授權下載。
名稱異同不能單獨判定列表，對應不明不得改 active-task 或開空帳。
真實流程應無追加開始／逐本授權，逐本驗證數量、非空、穩定性、
SHA-256、ImageIO 與 completion readback，最後對帳。
跨 Session 要真正新 Session；恢復須可靠 STOPPED／NOT_SENT，
不刻意製造中斷、破壞資料或重送來測負向案例。
無法安全執行的項目保持 BLOCKED／NOT_RUN，不以離線測試代替。

新報告寫 docs/plans/20261031-skill-precision/acceptance-fix01.md，
私人證據留 .local/line-backup/tasks/20261031-skill-precision-fix01-acceptance/。
報告列精確候選與穩定性、獨立性、F-01～F-06結果、需求證據矩陣、
命令／環境／退出碼／hashes、未驗項、finding及六項狀態。
最終判定 PASS / FIX_REQUIRED / REPLAN_REQUIRED / BLOCKED；
所有適用條件有有效證據才可整體 PASS。發現需修補就保存並交回
Owner，不修改產品或自動啟動修復角色。
```
