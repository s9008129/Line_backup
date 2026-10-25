# 歷史正式 AUTO 研究流程

只有 Owner 明確要求舊 formal AUTO／交易驗收、grant 或來源綁定診斷時才讀本文件。Owner 於 2026-10-25 選擇「日常 Skill 依 Agent 流程精簡」，並明確拒絕 P3。這是產品方向決策，不是外部 review 通過、正式 E2E PASS 或可執行 grant。

日常主流程是 Owner 人工開列表、明確授權與交接前景，Agent 依 Skill 盤點、下載、驗證及保存紀錄；不以另建一般授權簽發系統為前提。

以下舊路徑仍按原本實際程式限制執行，本輪沒有修改它們：

- `policies/line-two-album-pilot-v1.json` 的 `gui_authorized_by_this_profile=false` 不授予 GUI 權限。
- `line_backup_batch.cli:native_authorize` 只檢查既存 project grant；`dispatch_authorized=false` 不是 issuer。
- `daily authorization-request` 只輸出待核對資料。它可能回 `BLOCKED_NEW_GROUP_ISSUER_REQUIRES_REVIEW`；保留此真實拒絕，不改值或偽造審查。
- 舊 project／ONE56 綁定固定 task、config、root、source/runtime、Owner 決策及外部 review。不能挪用到另一列表或用 P3 代替。
- 舊正式 Save All 路徑仍須原 duplicate、目的地、owner、intent、menu 與 at-most-once 檢查；不可重開 CLOSED grant、重置 ledger、刪除未知派送 barrier 或改寫 VERIFIED。
- 舊正式獨立 E2E 角色、兩本交易順序、正式 G2 證據及外部審查限制保留。日常完成紀錄不升格正式 AUTO。

若目前選用的工具遇到以上拒絕，停止該動作並回報。不能以「主流程已精簡」為由換入口偷渡原本被擋的同一操作。是否停用或修改舊可執行路徑是另一項明確範圍的任務，不由修改 Skill 偷渡。
