# ML07 Amendment 06：離線 implementation 與後續實機 E2E 分線

日期：2026-10-11。決策 owner：root Planner；依據為使用者在 2026-10-11 14:46:14 UTC 時鐘觀察後明確恢復並調整本輪範圍。實際作者：`context_history`。本 amendment 是原計畫的有界執行附錄，不改寫或取代 `plan.md`、`handoff.md`、`plan-contract.json`、`handoff.json`、e01/e02 immutable artifacts。原完整 LINE/D01/Save All/兩本相簿/scroll/Acceptance gates 保持 required；最新使用者授權把本輪 D01 實機前置操作及所有 CUA/LINE action/capture 延後到新對話，交 C 獨立審閱此分線並保留 live gate 未通過狀態。本輪不以延後改為 waiver/PASS。

## 本輪範圍

本輪完成已核准的 e03 最後有界 recovery 與早期 E01→E02→B01 evidence gates；在 early gates 和 tail readback 通過後，完成可由本機來源及文件化介面支持的產品 implementation 與離線驗證。不得在本輪操作 LINE/CUA、開啟或切換前景 app、擷取螢幕、派送輸入、建立 owner/destination/transaction intent、Save All 或下載。真實 D01 sample、LINE 前景交接、相簿 UI 驗證和兩本相簿完整交易改交新的實機 E2E 對話／執行者；這項分線不將相關 gate 改為 PASS，也不以 fixture、mock、推測畫面或假資料冒充實機證據。

e03 仍是原計畫最後允許的 recovery epoch。保留完整 namespace 與親目錄 no-follow/readback reconciliation、evidence/production 雙 family 凍結和各自 source SHA 綁定、E01/E02/B01 固定 IDs 各一次及 baseline tail readback。e02 已 frozen；其 preclaim `E01-evidence-policy` REFUSED 不得重跑或補目錄。不得建立 e04、reset attempt budget、改寫舊 receipts 或遷移 state。e03 任一 materializer、dependency finalization、formal check 或 tail readback 出現 material failure 時，保留現場並停止；依報告交 Planner，不以後續成功覆蓋失敗。

產品實作只依原計畫 literal paths：`scripts/line_backup_cua_adapter.mjs`、`src/line_backup_batch/cli.py`、`src/line_backup_batch/observations.py`、`src/line_backup_batch/store.py`，以及由 `implementation_feasibility` 在明確 serial handoff 後獨立處理的五個既保留 Swift paths。不得改其餘 dirty Composition/Sensor/NativeObservationSession、root tests、設定、套件、canonical state/schema、既有照片或已驗證資料。不得直接修 JSON。使用現有 store transaction lifecycle；UI/AX/raw-frame layout 任何未觀察欄位都維持 unknown 並 fail closed。沒有實機 sample 時只驗證程式安全拒絕、既有合法輸入處理及離線 store/CLI 行為，不能虛構 selector、座標、raw AX hierarchy 或 live witness。

在新對話實機執行者取得 D01 前，handoff 必須列明真實實機未執行、native Harness Python 3.14 unavailable、PlanReview 狀態 `USER_WAIVED_NOT_RUN`、independent Acceptance 尚待完成，以及當前六個 status subjects。下一位執行者仍須遵循原計畫：新鮮畫面確認候選、Save All at-most-once gates、每筆交易完整 readback；第一本 VERIFIED 並 release 後，實際 bounded scroll 和第二本不同相簿交易不可省略。

原 PlanReview `USER_WAIVED_NOT_RUN` 僅是原計畫的歷史 waiver record，不代表本附錄 review 已完成。C 必須對本輪新 overlay contract 作獨立 read-only review；未獲其結果前不得改產品。C review 不等於原 PlanReview PASS，也不是 independent Acceptance。報告和 result 按實際證據更新。完整協作紀錄由 recorder 在其獨立 publication window 以唯一 root-level literal path `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/代理協作開發紀錄.md` 輸出（producer `collaboration_recorder`、phase `REPORT`、type `REGULAR`、exact-path mutable `DRAFT` output、上限 8 MiB、verified readback）；原 R 內初始 recorder log 保持不變。該明確授權的單一 outside-R output 不是對 ROOT 或 R 的泛化豁免。`context_history` 不改 recorder 唯一作者的原始記錄。使用者已明確授權最後 add/commit/push；但實際 Git mutation 等 root 明確 serial handoff，並在提交前保持 HEAD、index 與原有 11 tracked dirty files/其他 untracked work 完整不變。
