# E2E測試報告 — scope-recovery-05／文件發布階段

本輪終點為收據工具修復與 unchanged adapter 離線驗證；實際本階段只完成事故閱讀、基線保全與 Plan／deterministic Handoff 文件。沒有建立 IMPLEMENT runner 或補充 tests，沒有執行產品 syntax/test、LINE input、Save All、chooser confirmation、下載、state/config/ledger mutation。

## 實際工具與順序

1. root 使用 exec_command 唯讀讀取 AGENTS、01/03 prompts、immutable4.8 routing/defaults/schema shape、parent plan/report/incident/ledger、adapter/tests diff 與四份原始收據。
2. 唯讀重算四份原件及 source/state/config hashes；均符合事故紀錄。git log/HEAD/index 查核目前已有事故 checkpoint，index 空；git ls-remote 查到遠端 parent document commit。這是觀察，不是產品 gate。
3. 用固定 Python3.13 -B 盤點既有 tracked/untracked/ignored regular file hashes、symlink targets、nested fixture directory entries；第一次掃描遇到巢狀既有 fixture directory，未寫檔即停止。唯讀確認為目錄後，第二次完整遞迴盤點；這是文件保全機械修正，沒有 product attempt。記錄於 .local/preparation-observations.json。
4. root 只寫 CON 的 baseline、plan、contract、freeze、user decisions、incident reconciliation、check specs、lineage、native blocker、input manifest、deterministic Handoff 及結果。handoff.json 直接複製 plan-contract.json；handoff.md 第一段為接手 prompt，內含完全相同契約。
5. 文件一致性／preservation 的實際結果保存於 .local/document-verification.json。之後由一名指定 GPT-6 luna 唯讀梳理落檔文件與 parent 上下文，返回詳細 commit message；實際 helper actor／結果與 Git 發布另保存於 .local，不在本報告預寫成功。

## 判定與未知

G_BASELINE/G_RUNNER/G_ADAPTER_OFFLINE/G_PRESERVE/G_REPORT 是後續 IMPLEMENT gates，目前 NOT_RUN；文件 hash 保全不當 IMPLEMENT PASS。Parent G_PRESERVE 的四份範圍外寫入仍 FAIL/BLOCKED，原件不搬移／删除／覆寫；Node MODULE_NOT_FOUND 仍不是 adapter syntax 結果。原 scroll 保持 SCROLL_TEST_NOT_RUN；兩本交易與獨立 Acceptance 未執行。

native admission/publication/CONTRACT/RESULT validators NOT_RUN；固定runtime缺失、無stage packet，沒有代替schema validator或invitation。不可將JSON parse/equality/readback稱native schema PASS。OS sandbox/network denial UNKNOWN。

## 证据索引及状態

input-manifest.json 列 parent 原件、prompts、product/runtime 的相對（外部為絕對）／絕對路徑、bytes/hash。incident-reconciliation.json 每筆原件與readback對照。document-manifest.json 列本文件包hash；自身不自引用。baseline.json 指向 CON/.local/preexisting-files.json 與 preexisting-status.z：完整保全大清單保持本 workspace 本地，不假裝遠端已發布。Git收據和publication後保全亦留.local，避免自引用commit hash。

本輪產品/GUI attempt=0；LIVE_CLASSIFIER_CHOOSER 已知原attempt=2，剩餘驗證最多1次，沒有重置。來源與四份收據的新確認讓事故處置和安全續行邊界明確；產品能力尚無新驗證結論。

六狀態見 planner.result.json/handoff.result.json；局部與parent分开記。下一步由Implementer先fresh baseline與runner自測；第一個必要失敗即保留原始證據並交回Planner，不修產品。無可用Planner通道時只準備報告，記錄未交接。

## 文件一致性檢查補記

第一次文件保全比較因 git ls-files 對六個既有 nested fixture repository 目錄保留尾端斜線，而 baseline pathlib 已正規化路徑，產生表示法不同的假 delta。98,513 筆既有內容／類型／mode 核對沒有變更；未新增範圍外資料。root 只在 CON/.local 正規化比較路徑，保留原 script 與錯誤記錄於 .local/document-verification-attempts.json，再重驗文件。此為文件檢查，不消耗產品候選驗證額度，也不能標產品 PASS。
