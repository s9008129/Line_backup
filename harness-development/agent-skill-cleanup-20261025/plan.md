# Agent／Skill 專案清理與分支整合

task_id: AGENT-SKILL-CLEANUP-20261025；revision: 1。

Owner 目標：安全清除不必要檔案，將全部分支整合至 master。追加決策：P3 不需要；核心為 AI Agent 驅動 Skill 與原生 Computer Use，不新增授權框架。

本輪不操作 LINE、不下載、不修改照片、state、grant、ledger 或既有完成／排除事實。不把歷史來源合併當成外部審查批准或啟用下載。

## 實作與保存邊界

1. 先記錄 refs、工作樹與 binary diff，建立全 refs bundle 與外部完整快照，逐節點驗證來源與快照。私人內容僅留本機。
2. 在 origin/master 的獨立 worktree 序列整合。現有主分支產品已整合來源不可被舊分支回退；逐項記錄衝突取捨，保留歷史事實。P3 的專用來源、CLI 路由與使用入口不納入最終樹。
3. 清除已保存且可重建的 bytecode／Finder metadata；重複副本必須逐檔核對。歷史證據、照片、未明用途的原創檔、正式 runtime 與 state 不當作垃圾。補充忽略規則避免重新混入。
4. 清理後執行適用 Python／Node／Swift 本機檢查及 replay/provenance。失敗保留，不能冒稱 E2E 或正式外審 PASS。
5. 逐檔提交可公開成果，commit body 含意圖／做了什麼／下一步的建議。核對 CI 事件後交付 GitHub；master 合併仍遵守已知審查阻擋，Owner 的精確 merge-only 決策另記，不推定啟用。

## 驗收與停止

- 保存點可驗證；原有 dirty/untracked 內容不丟失。
- P3 不在最終可執行來源與日常入口。
- 每個分支 tip 的 ancestry 或未合併原因均明列；不以 ours 假裝完成內容整合。
- 私有資料不新增上傳；必要證據與工具依賴不被無差別刪除。
- 出現內容不符、未預期並行修改、無法確認的衝突或 protected data 風險時停止相關動作。

此為 STANDARD repository maintenance；不修改 protected runtime 授權架構。routing/runtime/schema 資源在 repo 根目錄缺失，不借用舊任務資源冒充 controller admission。無寫入子代理；唯一 GPT-6-luna/high 子代理依 Owner 指示唯讀分析 4733f749。
