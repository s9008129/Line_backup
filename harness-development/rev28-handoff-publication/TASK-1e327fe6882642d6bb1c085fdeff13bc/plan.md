# 2026-10-09 交接與 Git 發布方案

本單元只整理與發布 Markdown 交接、使用者決策及選定文字證據，不改產品、不操作 LINE、不改 config/state/photos。使用者已要求 git add/commit/push；最新又明確授權下一個 agent 點擊指定的 182 張相簿進行實機測試。此授權必須完整記錄，不能再沿用舊文件「無實機許可」結論。

風險 QUICK：Planner → byte-identical machine Handoff → root serial Implementer。獨立 Plan Review / Acceptance NOT_REQUIRED；這不影響先前產品 Critical 單元的真正獨立 A1，也不豁免下一個受保護持久化架構單元的必要 review。helpers=0、writers=0。

允許寫入：20261009_handoff.md、本 task 目錄。Git publication 允許 index/commit/目前 branch 一般 push，只限 publication-files.json 列出的 literal text paths；既有選定 evidence bytes 不可修改。禁止 git add .、force push、amend、切換分支、產品修改、重新下載57、改歷史結果。起點 HEAD e3b5af056733133a6eea37d3f21fee33588b5a4b，branch v43-ab/codex-rev28。Origin https://github.com/s9008129/Line_backup.git。

必要檢查：

1. 使用者三項新增要求完整收入：182目標、Best Practices、自動化工具核心及已授權實機點擊測試。leading prompt能獨立帶到新對話。
2. 最終 product/source/tests 117項及受保護 config/state/photos、Oct6 handoff、既有 correction evidence原始 bytes核對；原先53項Core manifest已當場吻合，再補117項完整核對。
3. Markdown local links、歷史/目前/下一步區分、明示 local-only source 和遠端發布範圍；引用最終 PASS不能覆寫 prior FAIL；避免把 inspection eligibility 當 dispatch permission。
4. pinned Harness4.8 v3 schemas用完整離線Registry驗證新task與role results；unknown refs直接拒絕，無 schema 網路查詢。plan-contract.json和handoff.json逐bytes相等。
5. staged literal paths/blob bytes、commit paths/content、normal push 和遠端branch commit readback相等，最後 index空、branch不變、protected bytes不變。

本機 controller admission 未建立；以上是 role-observed checks，不能聲稱 controller receipt、OS sandbox 或 network denial。能力政策只宣告允許origin Git聯繫，沒有強制egress控制證據。

產品測試沿用已完成的可核對證據，不為Markdown變更重跑Swift或下載。若內容/推送失敗，保留實際錯誤及已完成步驟，最多三次有證據的同根因嘗試，兩次無新資訊即升級；不虛稱推送成功。
