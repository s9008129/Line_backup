# 新對話用 /goal（自動化驗證階段）

使用方法：在**新對話**貼上下面整段（含 `/goal` 那一行）。它就是啟動指令；真正的細節全部在
`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md`（H2.1）。

---

```text
/goal

【必讀】先把這份檔案完整讀完，再開始動作：
/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md
它是本任務唯一的啟動輸入（H2.1，2026-09-16）。裡面有：目標、權威路徑表、現況 hash 快照、兩個 blocker、
R1–R7 缺口清單、Phase 0→7 的自動化測試流程、禁令與升級條件。不要憑記憶或舊對話推測。

【任務】把 LINE 相簿備份流程做「自動化驗證」：用真正入口重現並修好 handoff §7 的 R1–R7 缺口，
產出可重跑、可獨立複驗的測試與證據。使用者要的最終目標是「全自動備份、不需人工介入」，本輪就是
把驗證做實，而不是增加 PASS 數字或文件。

【範圍】
- 只做一個相簿：LINE app `jp.naver.line.mac`、群組「旻謙允禎成長日記」、相簿「2024/05/13～05/17」、預期 57 張。
- 既有 57 張若有效 → 走 verify-only；**永不為測試重下載**。
- 正式 config、state、run-log 與 57 張照片：目前全部唯讀，除非使用者另外給出精確 gate。

【三個結果分開報告】1 本相簿資料結果／2 可重用自動化能力／3 整體任務結案。
只有 1 與 2 都成立才算 complete；offline 或 fixture PASS 不得冒充 GUI 端到端成功。

【怎麼做】依 handoff §8 的順序：
Phase 0 唯讀基線（git status、CLI --help、authority_baseline 前後快照）→
Phase 1 隔離與封存舊證據（不刪不搬）→
Phase 2 用真正入口重現 R1–R7（每個測試先寫「主張／受測入口／外部 oracle／結果如何改變下一步」；
不得用預告故障旗標製造安全行為）→
Phase 3 若需改安全／持久化／成功語意，走 CRITICAL：更新同一任務 plan.md（PLAN_REVISION 遞增）→
真正獨立的 fresh plan review → 封存舊 handoff 並重新編譯 → fresh implementer 執行 →
Phase 4 最小完整修復（不得為通過測試而改期望或放寬 authority）→
Phase 5 風險適當回歸＋真正整合（fake adapter 只能替換外部 I/O，不得製造 VERIFIED）→
Phase 6 需要時提出一次精確 GUI 觀察 gate → Phase 7 獨立驗收與 result。
舊批准（含 plan Rev13 與 review/attempt-16）不得沿用於新修復。

【兩個 blocker，只有兩個合法解法】
1) 來源身分：使用者要的是「旻謙允禎成長日記」（禎 U+798E），正式 config/state 是「旻謙允楨成長日記」
   （楨 U+6968）。**禁止合併、正規化、改寫 canonical key，也不可用相同日期／數量／hash 推斷同群**。
   解法：authoritative exact source join，或一筆精確保留的使用者事實（原問題、原答、供應者與時間、
   證據 SHA-256）。**第 1 問已取得並保存：使用者答「正確是「禎」」（見 `evidence/20260916-user-fact/`
   與 handoff §5 B1）；第 2 問（既有 57 張是否即該群組該相簿備份）未答前不得推定（可再問一次，允許答不知道）。**
2) GUI 觀察 gate：先完成所有無 GUI 前置工作，再**一次**提出精確 gate：在 LINE 已顯示精確目標時，
   允許恰好一次 current-target ellipsis 觀察，取得即時 post 證據後停止。該 gate 不授權選單項、Save All、
   chooser、鍵盤快捷鍵、任何 state 寫入或任何下載；歷史 ellipsis 額度已用盡，不得沿用。

【硬性禁令】
- 不得執行會觸發管理員／授權密碼視窗的命令（例如 sfltool、sudo、TCC 相關工具）。
- 不得使用 AXPress、AXUIElementPerformAction、AX write、猜座標、OCR-only 通過、sandbox workaround。
- 不得覆寫既有 evidence／attempt／result.md；所有 attempt append-only，失敗輸出也要保存。
- dispatch 結果不明時不得重送 Save All；錯相簿立即終止；`/private/tmp` 不得當長期保存。

【證據規則】每個 attempt 保存：完整輸入、argv/env（去秘密）、stdout/stderr/exit、受測程式 hash、
獨立副作用計數、前後 state、artifact manifest（SHA-256＋bytes），且全部要能獨立讀回。

【執行環境】本機可用的 Computer Use 已實測可用（含 BYOK 模型；圖片路徑 IMAGE_PATH_WORKS，見
handoff §6 與 evidence/20260916-cua-cli-proof/）。若換模型或 provider，先重跑一次 CUA 小實驗
（getState → Raise → getScreenshot）確認，再繼續。

【升級條件】遇到「同一不中斷 dispatch／crash recovery／CLI-GUI transport 無法同時滿足」「來源或歷史
intent 證據矛盾」「同根因兩次修復失敗」「獨立審查再發現自證或跨測試污染」「bridge 必要性無法判斷」時，
指名交由高階模型（GPT-6 Astra；不可用就明報並要求），附最小重現、原命令輸出、受測版本 hash、
失敗 attempt、假設與反證，以及要求裁決的單一問題。

【現在就開始】先回報：你讀到的目標、本輪 CORE 清單、你打算依序執行的前三個 Phase，然後直接動手。
```
