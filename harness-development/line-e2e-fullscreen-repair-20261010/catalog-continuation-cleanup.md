# 舊 continuation 清理與新讀到的歷史額度

使用者在研究／計畫 Git 交付期間明確指定舊 `catalog-diagnostic-continuity-replan-20261010/results/implement-continuation-handoff/handoff.md` 的相關實作需安全移除。其 `repair-01/` 與 `tmp/smoke-repair/` 已完整移至專案外封存；本目錄的候選與進度保留。

來源、逐檔核對、保護檔案比對與還原方式見：`harness-development/catalog-continuation-cleanup-20261010/report.md`。這是使用者授權的來源位置變動，不是無聲刪除歷史。若既有 `start-snapshot.json` 包含它們，保留 snapshot 原檔，另記此授權與 receipt；接續使用的 baseline 應反映實際來源，不改寫舊 snapshot，不忽略 preservation gate。

清理時新讀到舊 repair ledger 記錄完整 catalog 方法累計 **3+2=5**（原 catalog 3+1，再加這個已存在的 repair run）。最後一次既有結果為 exit 2、18 PASS、R17 FAIL、R20 NOT_RUN；不是本次 root 重跑／驗證的測試。兩份 ledger 位元組複本在清理目錄 `historical-ledger/`，完整原始證據在封存中。新 E2E 帳冊應保存這個已知歷史，不把移動當成 reset；新計畫的 +5 方法仍是另行授權的上限。

這則說明不修改 API、profile、requiredness、gate 或本次 E2E 成功條件，亦不宣稱修復或 E2E PASS。
