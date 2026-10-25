# 進度

目標是完成前景列表驅動、完整盤點、相簿級恢復、正常授權準備及 Skill／手冊；Owner 追加 archive-first 整理與可攜性，實際搬移留待之後。

已讀最新本地來源、PR28、PR32 原始觀察及 10/24 私有 batch summary。已建立目的地 UUID／有序頁面重疊／底端無位移／持久 intent／新空目錄恢復／既有 ImageIO 驗證的離線候選。

首輪測試因 Swift compiler／預設 SDK 不匹配未能執行；改選既有 SDK26.5 後 14/15 通過。正例剩餘失敗追到 Foundation 將 `/private/var` 正規化為 `/var`，既有 decoder 因 canonical guard exit2；沒有放寬 decoder，fixture 改用 checkout 內隔離目錄後 15/15 PASS。每次都取得新資訊，沒有盲目重送 GUI。

Luna 技術檢查另發現歷史來源採信與 UNKNOWN 可改寫風險，已交原功能 Implementer 在隔離 worktree 修正並加負例。這不是正式獨立外部 Review。所有正式 GUI／Save All／取消／下載次數仍為零；新群組、完整列表與實機恢復為 NOT_TESTED。

已建立完整外部工作樹 clone 快照與 all-refs Git bundle，copy／bundle create／verify 均 exit0。Luna 正依精確 scope 核對 hashes 後移出過期文書／重建快取。原 1,275 份受保護 artifacts 保留基線。

功能修正、清理 receipts、乾淨候選整合與本地檢查已完成；本輪不重跑既有測試。正式新群組 issuer、外部 review、精確 runtime、磁碟掛載與當輪前景未成立，不能執行 Save All。Owner 已針對 PR #36 原候選 `af99c14459202cb148a3eceda8faa0b6871bb3f2` 明確核准 merge-only exception；正式下載仍停用，例外不構成外部批准或 E2E。

最新結果：Luna 完成19/19 daily負例及最終跨checkout可攜檢查，22/22 Node adapter測試、官方bundled Skill validator PASS。完整Swift測試揭露來源列表與manual-archive欄位漂移；已用既有測試修復non-manual報告相容，manual=true/數值0/缺欄仍拒絕。聚焦17/17、完整334/334 PASS。只改兩個Swift source/test，不啟用manual archive新能力。

實際清理63項/53,983節點/3,662,301,514 bytes，均移到外部封存；1,275項baseline零差異。Owner要求完成後提供永久刪除建議與信心，已產生63項精確CSV及決策文件，沒有永久刪除。

候選證據固定與本地 Git checkpoint／Draft PR 已完成。Owner merge-only 決策已逐字記錄，文件提交與 PR #36 正常合併仍待完成；PR31／PR32 的外審狀態不變，沒有新 external review。原任務 P0/P1/P2 離線候選及 P4 已完成；P3 正式跨群組 issuer 與實機 E2E 仍 BLOCKED/NOT_TESTED。正式下載停用，不能把本機測試和整理完成寫成兩本真實交易達標。
