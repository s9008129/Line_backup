# 前景相簿修復：有界本機候選版本

task_id: FOREGROUND-ALBUM-20261025；revision: 1；base: 5919de77373af834d96a0842cce07a310c2bfc13。

Owner 已指定 RECOVERY_STRATEGY=ALBUM_LEVEL、PHOTO_LEVEL_RESUME=FUTURE_RESEARCH。
本輪直接完成離線可審查修復；不將本地測試、Owner 實作指示或此計畫冒充外部 Plan／Code Review。

## 範圍與驗收

- P0：以前景相簿列表及目的地建立本地 UUID；名稱只供顯示。重新交接須以實際畫面確認同一個本地識別，禁止由目的地名稱或 OCR 字串自動認定群組。
- P1：Agent 提交從頂端開始的卡片觀察，頁間保留有序重疊；底端必須有同一末頁向下捲動無位移的證據。相同日期／張數不足以去重，需視覺識別。所有卡片逐本對帳，未完成／未知為零才可報日常完整。
- P2：持久 intent 在 GUI 之前寫入。已完成不可再建立 intent；UNKNOWN 不自動重送。前次明確終止、該本 Owner 恢復證據及新空白目錄才可新增恢復嘗試。保留所有原目錄。
- P3：追溯舊 profile、native_authorize、grant／ledger。新增唯讀核准資料準備入口，列出精確來源、目的地、群組 UUID、候選與欠缺項；不簽發 grant、不填入同意或審查、不啟用新 GUI 權限。一般跨群組正式 issuer 屬受保護邊界，若未有真實外部批准，維持 BLOCKED 並交付明確差異。
- P4：精簡主要 Skill，依情境讀 references；白話手冊與啟動 Prompt 不要求輸入群組名稱，正式採相簿級恢復。

實作只新增日常紀錄輔助模組與聚焦測試，更新 Skill、references、README、使用手冊及本任務報告。不改既有正式授權器、Harness、config、state、grant、ledger、歷史紀錄或照片。新輔助模組不操作 GUI、不授予派送權限；Agent 使用既有原生 CUA，正式交易仍經既有受審入口。

## 驗證與停止

本地案例涵蓋：不同群組／目的地隔離、錯誤交接、重疊及漏頁、假底端、重複身分、未對帳、完成不可重送、UNKNOWN、明確停止後的新目錄恢復、symlink／資料異動拒絕、真實 ImageIO 小型 fixture 解碼與破損圖。
實機獨立驗收以 51 張候選為目前 Owner 案例，仍需有效前景、掛載目的地、真實審查與 L1／L2 授權。未成立就不派送 GUI 或 Save All；實機項記 NOT_TESTED。

風險：資料保護／授權為 CRITICAL；候選版本不啟用該路徑。外部審查與獨立 E2E 仍為必需關卡。root 的 routing/runtime resources 不存在，未啟動舊 lineage Controller、未宣稱 Controller admission 或平台隔離。使用序列本機修改，無 delegated writer allocation；最後另請指定 Luna 唯讀整理提交訊息。

Git：保留原有三個 tracked dirty 檔與所有 untracked 工作。逐檔 stage 本輪成果；依 Owner 最後指示 commit／push，使用 CI skip 並確認分支不符合現有 push workflows；不 merge、不手動啟動 CI。是否更新 Draft PR以不觸發 CI 為前提。

## Owner 追加範圍：整理、可攜性與分工（revision 2）

Owner 隨後要求 GPT-6-luna 多代理分析與實際執行整理，root 僅監督／分析／判斷；原 P0～P4 持續。Owner 已選「先外部封存再清理工作目錄」與「先修正路徑，之後由 Owner 搬移」。這個決策不允許改寫歷史 grant、state 或偽造外審，也不代表從未核對的唯一資料可以直接刪除。

原始範圍的本機草稿完成後，兩個互不交疊的 code 工作包由 Luna 接手：daily 功能／文件／單一 driver 路徑修正，在 `Line_backup_daily_writer_20261025`；113 個既存產品 paths 的乾淨整併候選，在 `Line_backup_consolidation_20261025`。兩者皆為 root 事先建立的 detached external worktree，allocation 與 seed hashes 記於 private。max_parallel_writers=2；沒有 Controller registration／原生安全 sandbox 證明，不宣稱正式 Harness IMPLEMENT PASS。另一路 Luna 執行精確允許的 live-filesystem archive-first 清理，不更動產品程式。

清理僅對已和完整外部快照逐檔核對的 scope 使用同磁碟 rename，原資料另存 `removed-from-active`，不永久刪除。照片、正式 state／grant／ledger／contract、最終 runtime、原始實機 evidence、三個原有 dirty 檔均排除。根目錄歷史文書與重建快取的精確清單及前後 hashes 由 executor 寫 receipt。

主分支整併：Owner 已要求 merge 到主分支。實際發現 PR31 外審 B03/B04 與 PR32 `DO_NOT_MERGE_DRAFT_YET`，不能將一般整理指示誤寫為既有外審通過。先準備並驗證乾淨候選；若仍需越過明確 merge-only blocker，交 Owner 決定是否明確豁免「候選入主分支」限制，且保留 runtime／L2／正式 E2E 禁止啟用。不得直接合併 PR31 的 1,900 個歷史檔案。
