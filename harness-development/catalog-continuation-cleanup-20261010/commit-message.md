封存舊 catalog continuation 實作並保留清理證據

意圖
依使用者追加的清理要求，將舊 catalog continuation handoff 所授權範圍內的實作移出工作目錄，保留可核對的封存副本與歷史失敗紀錄。本提交記錄這次封存，不代表執行新修復或 E2E。

已完成
- 依使用者指定的舊 handoff 核對實作範圍，封存未追蹤的 repair-01/ 與相關 tmp/smoke-repair/。以同磁碟原子 rename 移至 repository 外的本機封存目錄：
  /Users/hsiaojohnny/Documents/ChatGPT/Line_backup_local_archives/catalog-continuation-20261010T035451Z
- 封存保留 1,021 個檔案、共 555,287,414 bytes；receipt 記錄所有檔案的 SHA-256、大小與權限相符，且兩個原始實作路徑已不存在。
- 保護清單中的 266 個檔案內容維持不變，包含 config、state、已備份照片、原 candidate 與既有 dirty tracked 檔案。未使用 rm、git clean 或還原未提交程式。
- 新增 cleanup.py、restore.py、archive-manifest.json、cleanup-receipt.json，以及兩份歷史 repair ledger 的逐位元組副本。restore.py 預設只檢查封存與目的路徑衝突；唯讀檢查實際 exit 0，本次未執行還原。
- 新增清理報告、進度、舊 handoff 旁的封存說明與新 E2E 接手說明。原始 handoff、candidate、replay、offline-validation、review 與歷史報告留在原位置；新的 line-e2e-fullscreen-repair candidate 保留。外部封存中的實作、二進位及照片不納入 Git。
- 沿用使用者指定的唯一 GPT-6-luna（xhigh）唯讀子代理撰寫追加提交訊息，由 root 核對與執行 Git。

驗證與限制
- 清理 receipt 記錄 ARCHIVED、逐檔 hash／權限相符、原路徑不存在及 266 個保護檔案未變。
- archive-manifest 保留移動前的 PREPARED 紀錄；cleanup-receipt.json 記錄完成後的 ARCHIVED 結果。判讀最終清理結果以 receipt 為準。
- 封存保留的既有 run-01 紀錄為 exit 2、18 PASS、R17 FAIL、R20 NOT_RUN；清理過程沒有重跑測試。R17 的舊紀錄指向 check-builder 的 evidence key lookup 缺陷，不能當作本次清理的測試結果。
- 保留的 ledger 記錄歷史方法 3 加實際 extension 2，合計 5。這比先前研究／E2E 計畫列出的已知 3+1 多一次；新接手說明保留此新讀到的歷史事實，不能因封存或新目錄而重設額度。
- 本次沒有影像 OCR、LINE UI 操作、下載或 E2E，亦未消耗或重置方法額度。
- 同磁碟封存移出專案工作區，不會減少整個磁碟的總占用。還原工具未經實際還原演練，且會拒絕覆蓋既有來源路徑。

下一步建議
後續 Implementer 使用新的 line-e2e-fullscreen-repair candidate 繼續工作，保留並引用既有 3+2 ledger 歷史。若其 baseline 涵蓋封存路徑，保留原 snapshot，另記本次使用者授權與清理 receipt，再建立後續有效基準，不默默忽略 preservation gate。若需查考舊實作，從本機封存副本唯讀取證，勿將封存內容當作新候選或重跑舊 helper。正式 E2E 結果仍以新候選的實測報告為準。
