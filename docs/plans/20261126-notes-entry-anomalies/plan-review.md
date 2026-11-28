# LINE 記事本入口遺失、輸入通道與證據可重現性異常修復計畫審查紀錄

- 審查日期：2026-11-26（Asia/Taipei）
- 審查對象：`docs/plans/20261126-notes-entry-anomalies/plan.md`（v1，SHA-256 `cdbf770f67da111d810d42f8d71cd5ab9f39fd5873c83176b63870d262ca1e19`）
- 審查角色：獨立 Reviewer（Herdr pane `wA:p2`，對 repo 嚴格唯讀審查）
- 審查依據：`code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution（Plan Review）

### Review Verdict: APPROVE
- **Review Type**: Plan
- **Core Goal Alignment**: 本計畫緊扣以同一日常 Prompt 與 Skill 無人值守完成單一記事本列表備份之核心目標，所有修復收斂於證據保存與回報契約，未偏離日常產品入口。
- **Diff / Scope Hygiene**: 範圍極簡且明確凍結 `src/`、使用手冊、`AGENTS.md`、問題提報單、標題錨點、公開簽章與 `BLOCK_MARKERS` 順序，僅允許白名單 7 檔加計畫紀錄檔異動，無多餘重構。

### Findings
None

### Verification Evidence
- 計畫檔 `docs/plans/20261126-notes-entry-anomalies/plan.md:1-188` 全文已讀，SHA-256 與委託一致；基準 `70c8127` 與分支 `feature/line-notes-media` 經 `git --no-pager log --oneline -3` 核對。
- 問題提報單 `docs/diagnostics/20261126-notes-entry-anomalies/問題提報單.md:§A5,A7,A9,A13,§11 Q1-Q10,§12` 已讀；A5 106 bytes 樣本、A13 同 bytes 不同 inode 與 `NOT_RUN` 邊界、A7 同 mtime 鎖競爭均與計畫裁決一致。
- `src/line_backup_batch/notes.py:59,345,570,6063,7268,8468-8476,6118-6236` 已讀：`_file_lock` 為 `LOCK_EX|LOCK_NB`，`summary` 與 `resume` 皆經 `locked()`，`LOCK_SH` 仍與 `LOCK_EX` 互斥；`retry_safe` 區分唯讀與 `resume` 正確，凍結判斷有直接程式證據。
- `references/evidence-template.md:53-70,99-185,185-360,758-790,1070-1110,1116-1185,1280-1330,1492-1550,1665-1742` 已讀：`persistObservation` 現行對非空字串一律判 `AX:OK`，確認 A5 缺口存在；`normalizeHostCalls` 缺值回 `NOT_RUN`，`captureAndPersist` 與 reveal after 皆透傳 `hostCalls`，確認雙層相容設計之必要性；`persistSingleInput` 已具 `wx`、`RETURN/ERROR/NATIVE_RETURN_UNDEFINED` 與 `DOWNLOAD_CONTROL` 拒絕，A12 無需新 API 之主張屬實。
- `observationAssets:1665` 要求 `ready_for_bind===true`，故 `AX:DIFF_NO_CHANGE` 自動阻斷 `checkDownloadReadiness` 與 `persistReveal`，與計畫所述一致；`cua-initial-observation:1116-1153` 現行僅檢查 `ready_for_bind`，補上 `CAPTURE_BOUNDARY` 閘門後仍維持 `writes==1/2` 與單一 `emitImage` 契約。
- `tests/test_notes_input_helper.py:31-110,3428-3560` 已讀：`BLOCK_MARKERS` 7 項、`documented_initial_observation_source` 單一 `js` 區塊約束、`64` 個測試均存在；既有斷言僅比對 `stages.*.status`，新增 `full_tree/diff_only/stale_index_warning/CAPTURE_BOUNDARY` 不破壞既有契約。
- `tests/test_notes_locks.py:141,237`、`tests/test_notes_restart.py:622` 已讀：`NOTES_LOCK_BUSY` 與 `status_counts_scope` 鍵值已有精確斷言，凍結 `notes.py` 具回歸測試依據。
- `SKILL.md:30,119-124`、`references/gui-inventory.md:126-190`、`references/download-and-ledger.md:7-25,451-495`、`references/verification-and-recovery.md:147,200-213`、`references/evidence-decision-cases.md:C27,D2,D4,D5` 錨點均存在，計畫引用之行號與標題無虛構；Slice 1 與 Slice 2 白名單零重疊。
- 僅執行唯讀命令：`sha256sum`、`grep -n`、`sed -n`、`git --no-pager status --short --branch`；未修改 repo，未執行寫入型驗證，實機 E2E 維持 `NOT_RUN` 之界限聲明正確。
