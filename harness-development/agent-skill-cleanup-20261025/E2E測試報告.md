# 清理與分支整合：實際進度

日期：2026-10-25；task_id：AGENT-SKILL-CLEANUP-20261025；plan revision：1。

## 目標與目前結果

Owner 要求安全清除不必要檔案並整合全部分支，之後明確拒絕 P3，指定 AI Agent＋Skill＋原生 Computer Use 為核心。本輪沒有產品架構擴充、LINE GUI、Save All、下載或照片驗證操作。

清理切片完成；分支合併尚未完成。P3 不在本候選產品樹；不能把未合併、未審查或未實測項目寫成 PASS。

## 來源與保存

- 起始活躍 HEAD：`5919de77373af834d96a0842cce07a310c2bfc13`。
- 遠端主分支：`838a3650f9028fa2356c4b20ee8be931f03f2441`。
- 清理切片 commit：`990f841bd6af89042536d8d369aedcdff33af051`。
- 全 refs bundle 經 `git bundle verify` 成功；原始工作樹 snapshot 98,426 節點逐項比較 SHA-256／大小／型別／symlink target，差異 0。binary dirty diff 與未追蹤內容均保存在本機外部快照。
- 公開文件省略個人路徑、私人照片／群組與原始授權；外部保存點代號為 `Line_backup-safety-20261025-211501`，位於原工作目錄同層。`snapshot-manifest.json`、`refs-before.txt`、`status-before.z`、`dirty-before.patch`、bundle 與刪除 receipts 均保留本機。快照不是聲稱有 OS sandbox 或 network isolation。

## 實際步驟及副作用

1. 唯讀核對最近兩筆 commit：`4733f749` 只新增兩份操作知識文件 90 行；`5919de7` 新增使用手冊／檢查報告與 README 入口 217 行。兩筆共新增 307 行，刪除 0 行，不是清理 commit。
2. 核對 Git refs、worktrees、GitHub PR #31／#32／#37 與歷史清理收據。舊封存建議文件已落後實際刪除收據，不能當成目前仍存在副本的證明。
3. 建立上述完整保存點。在最新 origin/master 的獨立 worktree 建立清理候選，保護原工作樹未提交程式與資料。
4. 原工作目錄刪除 307 個可重建 bytecode，共 4,967,614 bytes；每檔與保存點核對。候選主分支刪除其中 260 個已追蹤 bytecode，共 3,512,130 bytes。
5. 原工作目錄另刪除 2,075 個舊 build/module-cache 中的 `.o/.pcm/.swiftmodule/.swiftdoc/.swiftsourceinfo/.swiftdeps/.dia`，共 812,987,658 bytes。只在歷史 task 的明確 cache/build 目錄篩選，不刪 runtime/bin 或現用 rev28/.build。每個檔案先核對保存點 SHA-256，精確清單在 `historical-compiler-cache-removal.json`。
6. 以上原目錄清理共 2,382 檔／817,955,272 logical bytes；完整歷史內容仍在保存點可恢復。舊 task 若需精確原地重播，須先從保存點恢復對應中間檔。APFS clone 不保證實體釋出相同空間。

沒有刪除照片、原始 screenshot、grant、ledger、state、完成／排除紀錄或現用執行檔。未明用途的原創資料未當作垃圾刪除；不宣稱所有非必要檔案已清乾淨。

## 本機驗證

| 方法 | 結果 |
|---|---|
| snapshot 逐節點比對 | PASS：98,426 項，差異 0 |
| bundle verify | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS：19 tests |
| `node --test tests/test_cua_adapter.mjs` | PASS：22 tests |
| `python3 -B rev28/Tools/replay_rev28.py` | 首次退出 2：缺必填 --output，不是產品失敗 |
| 上述 replay 補齊 --output 至外部保存點 | exit 0；輸出為 `replay-after-generated-cleanup.json`，尚不提升為正式實機 gate PASS |
| `python3 -B rev28/Tools/verify_pre_live_provenance.py` | FAIL：missing v3 provenance manifest。該缺件存在於清理前主分支，不在刪除名單 |
| `git diff --cached --check` | PASS，清理切片提交前 |
| Swift 完整 suite、LINE GUI／Save All、正式獨立 E2E | NOT_RUN |

本輪只有 1 次清理執行，沒有重複修復相同根因。replay 一次參數更正，不掩蓋第一次退出碼。沒有實際 GUI 派送、交易或照片驗證，因此不適用 Skill 實機經驗回報；唯一 Luna/high 子代理依 Owner 明確要求唯讀分析 4733f749，沒有實作或獨立 E2E 身分。

## 分支整合尚缺事項

- #31／#32 有既存未完成外部 review／do-not-merge 狀態。已向 Owner 確認本次是否授權僅合併來源且正式下載停用；尚未收到針對此項的明確答覆，不以 P3 拒絕指示代替這項決策。
- Owner 已明確排除 #37 P3。最終樹不納入其專用來源、測試或 CLI／使用手冊入口；保留歷史不等於啟用或核准。
- 舊分支直接合併會帶入大量歷史 task，並與新 Skill／手冊／portable binding 衝突；須保留較新主分支行為及必要證據，不能無差別覆蓋或使用 ours 假裝整合。

```text
PRIMARY_OUTCOME_STATUS=PARTIAL_CLEANUP
IMPLEMENTATION_STATUS=CLEANUP_SLICE_COMMITTED
CORE_ACCEPTANCE_STATUS=LOCAL_CHECKS_PASS_EXCEPT_EXISTING_PROVENANCE_GAP
REQUIRED_VERIFICATION_STATUS=PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN_NOT_CLAIMED
TASK_CLOSURE_STATUS=OPEN_PENDING_MERGE_DECISION_AND_INTEGRATION
```

下一步是在 Owner 合併決策範圍內完成序列來源整合、必要回歸、精確 ancestry 與 GitHub master 讀回。不得把這份清理報告當成 LINE 兩本相簿 E2E。
