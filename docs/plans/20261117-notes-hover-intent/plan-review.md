# 指定 Reviewer 計畫審查

來源：Owner 指定 Herdr Reviewer pane `w5:pB`；以下為其完整審查回覆。這是計畫接受，不是實作或實機驗收。

正式計畫 review：只審計畫，不實作、不 GUI、不改真實帳本。

審查 plan SHA-256：
`85eadf61afe0339f014f5d647455d6e33a143039701e08442421ace6a6a3d20d`
基準 `cbcbb81fb41a17e300eb91975b62466c83311b20` 與 HEAD 一致；dirty `問題提報單.md`、untracked `.playwright-mcp/` 保留不提交，已核對。

verdict：**ACCEPT**

可操作 findings：

1. [Info] 新例外可執行性 Pass：只延後原第二候選至新 intent 後，非第三候選；限本輪新建連續可稽核、無 outcome/下載呼叫/chooser/未解輸入、同 Session；舊 UNKNOWN 明確禁用；無 hover API 時只用既有 selected-filmstrip 非播放安全邊緣 click，不假造 API，不承諾因果/E2E。
2. [Info] 持久額度 Pass：`candidate_ordinal=2`、`budget 1→2`、prior refs、未解/crash 亦耗額、不換 Session/ID/路徑重置；總量仍兩次，與既有 B1 一致。Worker 落實時僅重用 `evidence-template.md` 既有欄位，不得新增持久狀態系統，否則按計畫停止交回 Leader。
3. [Info] 視覺 Agent 責任 Pass：helper 不作視覺辨識；Agent 讀同次 after 判可見/歸屬/啟用/映射，通過才走原 grounded helper 最多一次下載；再消失/證據不全/input error/timeout/漂移即停。
4. [Info] 白名單並行 Pass：Worker1/Worker2 檔案互斥，共享目錄不 commit/push、不增子代理、不改帳本/照片；其他檔只引用 B1。Leader 整合前須跑 diff/連結/白名單檢查。
5. [Minor] 測試可落實 Pass，可加強：最小回歸三命令與 Skill validator 目標均存在，`notes --help` 可用；落實時隔離合成 fixture、保護 active locator、回歸前後比對真實帳本/locator/提報單檔案清單與 SHA-256；mock boolean 不得說成真實核准，實機日常/hover-only/新例外真實成功/chooser/跨 Session 保持 `NOT_RUN`。
6. [Info] Owner 邊界：本輪無需另問。本計畫無真實 GUI/下載/restart/帳本/照片變更授權，不 merge、不 force-push；若需新持久系統或改 CLI 交易語意，停止並縮小方案，不得自行擴張。

Worker 可按此精確版本同步開工。
