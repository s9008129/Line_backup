# 新對話用 /goal（Rev25 預備：唯讀診斷＋擬新修訂；GUI 需 owner 另行授權）

使用方法：在**新對話**貼上下面整段（含 `/goal` 那一行）。它是啟動指令；細節以同目錄
`HANDOFF-2026-09-19-rev25-next.md`（H5.0，本輪交接）為準；舊版 `GOAL-rev24-next-conversation.md`
＋`handoff-rev24-agent-autonomous-2026-09-18.md`（H4.0）是歷史，不要當本輪輸入。

```text
/goal

【必讀】先把這份檔案完整讀完，再開始任何動作：
/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/HANDOFF-2026-09-19-rev25-next.md
它是本輪唯一的啟動交接文件（H5.0，2026-09-19）。再讀本輪計畫
`.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24，
SHA-256 40eb01980c7e11f96b4b12c2db8f53728852f1ab6ca452dfb5e865fd5435a003）
作為現行契約；不要憑記憶或舊對話推測。

背景（一句話）：Rev24 已結案——route attempt-07 在 S5 止步（STOPPED_AT_S5_NO_EFFECT：
相簿卡點 1 次但無開啟反應，⋮ 依規未送、零副作用），v5 修正規則未取得 live 測試；
Stage 05（e2e/attempt-08）獨立重算全 PASS；六欄為
UNKNOWN | COMPLETE | BLOCKED | PASS | PASS | CORE_ACCEPTANCE_BLOCKED，
唯一 scoped blocker＝CUA_ROUTE_DECISION（owner 保留）。依 OOS-V24-5，
Rev24 內不得再開新 attempt；再觀察必須是 NEW revision（Rev25）＋新 gate＋新複審。

【任務】單一波次、全自主，但分兩段，中間必須停下來等 owner：
第一段（本 goal 授權範圍：零 GUI）：① Phase 0 唯讀基線（git status 乾淨；重算 H5.0
§6 指紋：計畫 40eb0198…／handoff 體 fee98581…／result 0fe26fb6…／attempt-07 FINAL
7c8ea39a…／attempt-08 報告 f7bf7b20…／基線 ab6747f2… 57 檔；i任何不符→停、記證、
通知）；② 唯讀診斷 S5 NO_EFFECT（重讀三幀＋ledger，不送任何輸入；假說標註為假說，
不驗證、不重試）；③ 擬出 Rev25 草案（沿用 v5 工具；若動工具則重跑自測＋離線雙列；
gate-6 鏡射 gate-5 的 17-key schema，parent 綁 7c8ea39a…；runbook 維持 at-most-once、
S6 綁 v5、禁 fallback）；④ 把「診斷結論＋Rev25 草案＋A/B 代價」交給 owner，
然後停止。第二段（不在本 goal 授權內）：只有 owner 明確選 B 並給出新一次性授權後，
才可開新對話／新 goal 執行任何 GUI；owner 選 A 則寫結案備忘，不碰凍結證據。

【硬性禁令】零對話圖片（只報路徑＋SHA-256）；本 goal 下零 GUI 輸入（連一次都不行）；
永不點選單項目（尤其 Save All）；不碰 chooser；不送鍵盤；不做 AX 寫入；
不用歷史座標當 live 依據；禎(U+798E)/楨(U+6968)永不合併；append-only
（v1–v5 工具、自測、attempt-01..07、e2e/attempt-02..08、gates 1–5、各 ledger、
已封存 handoff、result.md 歷史一律不改）；不新增第三方依賴；不寫正式
state／config／run-log；python 一律 -B；不得自我豁免 gate；不確定就停下來問。

【回報】白話＋三結果分開（①本相簿資料 ②可重用能力 ③整體結案）；每階段完成→
繁中四段式 commit；證據只出現路徑與 SHA-256。
```

根目錄搭配檔案：`HANDOFF-2026-09-19-rev25-next.md`（H5.0，本輪交接）。
