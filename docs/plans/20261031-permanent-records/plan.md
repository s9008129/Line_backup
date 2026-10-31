# 已核准計畫：永久帳本與可刪照片分離

## 使用者決策與授權

Owner 於本對話選擇：保留 Line_backup 專案，允許刪除單一群組或整個 backup；永久紀錄放專案根 backup-records；照片搬走後直接依完成紀錄跳過，不要求外接硬碟在線或另做歸檔登記。Owner 隨後明示「Implement the plan.」，並補充必須同步檢視 Skill 與工具。

**Owner 最新明示本次 plan 不需要獨立審查、不需要過度工程化的審查，也不需要 independent acceptance。此任務不安排獨立計畫審查、複雜度審查或 independent acceptance，不在第一切片停下等待審查；保留必要本機測試、真實遷移對帳與誠實回報。** 這是本次的明示例外，不改寫其他任務或歷史驗收。

## 基線與範圍

- repo：/Users/hsiaojohnny/dev/Line_backup
- branch：fix/save-all-gate-20261030
- baseline HEAD：e573e0522dd11d10d7d5f43eb03bfc4d4c399843
- 原風險分級 CRITICAL，依據為帳本遷移與防重下判斷；Owner 明示上述審查例外。
- 保留既有未追蹤 docs/plans/20261030-save-all-gate/acceptance.md 與 docs/plans/20261031-skill-precision/acceptance.md，不讀取內容、不修改、不提交。
- 可修改：daily 與紀錄儲存/搬移工具、對應測試、.gitignore、AGENTS、README、專案 Skill/references、使用手冊、記憶說明及本任務文件。
- 真實資料操作限：本專案三份既有帳本安全複製與必要證據保全、遷移入口更新與唯讀對帳。保留原帳本及照片；不刪除或搬動照片，不重寫完成事實，不操作 LINE/GUI，不 merge。

## 交付行為

- backup/ 僅為照片；永久 backup-records/index.json 登錄各列表 UUID/帳本位置，不保存第二份完成計數。逐列表帳本在 backup-records/<local_group_id>/，事件仍為唯一進度來源。
- 新 init 預設建永久帳本；groups 查全部帳本；memory/summary --records-root GROUP_RECORDS 不要求照片root存在。--root 為照片路徑；init/groups/migrate-records 的 --records-root 指collection，其餘指單一UUID帳本。
- 完成事實與本機可用性分離：整本目錄缺席仍 COMPLETED/LOCAL_MISSING；目錄存在但缺檔、hash或身分異動為 LOCAL_CHANGED，保留完成且阻止新派送。不推論外接副本已驗證。
- destination 需fresh bind、真實目的地source、無未解attempt或命名交易，追加新一批照片目的地，原completion路徑不改；UNKNOWN與pending不因刪照或新root解鎖。
- migrate-records 先驗來源事件與保護狀態、複製原始位元及依賴證據、核對hash，保留原副本，最後登錄永久帳本。中斷依收據接續；舊入口拒絕寫入，衝突不開空帳。
- 保留舊 relocation 原始收據、anchors、baseline及prefix投影，不用舊工具搬已命名帳本。
- Skill/啟動Prompt/references/手冊/README/記憶說明同步，Owner不多填UUID或JSON。ImageIO、離線OCR與GUI定位方法保留。

## 檢查、停止與限制

- 修改前基線：daily 73項、relocation 2項通過；不是新版驗收。
- 實作者執行 daily 與 relocation 必要回歸、新永久帳本合成測試、CLI整合、文件引用與範例核對、git diff --check。
- 合成情境涵蓋刪單本/整個root、完成不重送、只下載新增、跨群組隔離、UNKNOWN/pending、partial/hash/symlink、索引/帳本毀損、遷移重跑與發布中斷。
- 真實遷移前後逐份核對UUID、原始事件/anchors hashes、completion狀態與數量；保存私人證據、保留原件，最後更新並讀回active-task。
- 發現來源/寫入衝突、身分歧義、工具拒絕或不明派送時停止依賴該前提的操作；同根因最多三次有證據嘗試，連續兩次無新資訊即停。
- 不保證限制外部writer或舊版程序，遷移需無活動下載的維護時段；不宣稱OS隔離、正式AUTO、GUI或獨立E2E PASS。
- 任務私人證據位於 .local/line-backup/tasks/20261031-permanent-records/。授權同範圍commit/push/Draft PR，逐檔stage並保留既有工作；不含私人帳本/照片/證據。
