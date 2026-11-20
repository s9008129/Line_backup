# 指定 Reviewer 實作符合計畫審查

來源：Owner 指定 Herdr Reviewer pane `w5:pM`。以下為完整原文；只接受文件符合性，沒有執行 GUI 或測試。四檔在審查前後的 SHA-256 另由 Leader 核對，manifest 留私有 task。

# 記事本延後候選實作符合已ACCEPT計畫 — Reviewer 審查紀錄

- 審查對象：已ACCEPT計畫 `docs/plans/20261118-notes-deferred-preparation/plan.md`（SHA-256 `691a141f59e3a6aeebb3d387ae37ed6de5739fd848795fde1dcdb829837b7f97`）之最終實作
- Verdict：**ACCEPT — 文件符合性通過，不簽實機E2E**
- 審查範圍：僅四個凍結 Skill 文件 diff；未讀既有 dirty `問題提報單.md`／untracked `.playwright-mcp/`；未改檔、未跑測試、未 GUI、未產 HTML
- 四檔：`.agents/skills/line-notes-agent-cua/SKILL.md`、`references/gui-inventory.md`、`references/evidence-template.md`、`references/evidence-decision-cases.md`
- 前提：Leader 與單 Worker 已互斥平行完成；`src/tests/helper/composition` 執行碼無變更（`git diff --name-only -- src tests` 為空）；Worker focused 31 tests PASS 由實作方回報、Leader 三條回歸執行中，Reviewer 未另跑測試
- 只簽文件符合性，不簽實機 E2E、日常備份、音訊、chooser、跨 Session 或核心可重複使用能力

## Findings（按檔與行號）

- `SKILL.md:80（一次一項下載）`：新增「依 B1 的客觀條件保存、讀回延後候選骨架，或記錄不能準備的具體原因，不以預測工具列會消失作為準備條件」。入口只連結 B1 預備分流，未新增下載入口、控制器、啟動步驟或相簿入口混用；與計畫 L24 一致。
- `references/gui-inventory.md:99（先備妥非 GUI 前置）`：延後第二候選可預先取得的方法、作用區與非派送骨架也在此備妥，候選 1 引用及未分配 ID 依真實取得時序補齊；`intent` 與空白 staging 仍只能在 `TOOLBAR_VISIBLE` 後由 CLI 建立，不預建 staging、猜 key 或先寫事件。與計畫 L25 一致，無 stability capture／固定等待／額外 GUI。
- `references/gui-inventory.md:110-111（依客觀條件在 intent 前準備／骨架與不可用原因）`：
  - 客觀條件成立（候選 1 request／raw／after 完整保存讀回、同 scope／viewer／有效前景、仍有原第二額度、安全作用區與映射有具體證據）則 intent 前必須保存並讀回骨架，不得等待或要求預測工具列消失；候選 1 真實引用補齊並讀回。
  - 符合條件卻保存／讀回失敗時停在 intent 前，不把寫入失敗當成準備不可用來繼續；區分 I/O 失敗與不可用，符合計畫 L24-25 與「I/O 失敗停 intent 前」。
  - 無安全方法、額度不足／不明或候選 1 原件不足時記未準備與具體原因，不猜值、不擴額、不為補骨架新增輸入；未準備不額外禁止本來符合全部既有 gate 的直接下載；控制消失後維持原停止、不臨時補造；符合計畫 L26 與「未備妥不額外阻合法直接下載」。
  - 骨架是非派送準備，未分配 attempt ID／intent event ref 待 CLI 成功與唯讀事件核對後填入，不預建 staging 或真正輸入 request；骨架候選 2 與 budget 1→2 是計畫值，不是已派送或已耗額；實際計數與保護仍依原固定額度／保存缺口規則（含 timeout、error、未知、crash）；缺 receipt 不證明未呼叫；無原 task 前置準備 intent 後不得臨時補造。符合計畫 L27 與「骨架非真正 request、未知 ID 待 CLI 真實取得、計畫 quota 不算派送」。
  - 先核對連續性／方法與單次保存／after 與一次下載各節未放寬：仍須當次新 intent、同一 Session／連續前景、同一 viewer／三層身分、候選 1 完整、尚無下載呼叫／outcome／chooser／活動下載／未解輸入；舊 UNKNOWN、舊 crash window、額度不明、已用兩次一律停止；零計數／空 staging／缺檔／缺 receipt 不證未呼叫；只送一次 input→直接 after，禁重播舊點／舊 mapping、禁第三候選。符合計畫 L28 與「intent 後 fresh 重核與所有原 gate／舊 UNKNOWN 保護不變」。
- `references/evidence-template.md:1267（intent 前準備）`：依 B1 先核對客觀條件；成立時不等待或預測即保存並讀回既有 Reveal 導覽欄位骨架，不建新持久狀態；此骨架不是 `persistSingleInput` 真正 input request，尚無 attempt ID／intent event ref 待 intent CLI 成功與唯讀事件核對後補入；不預建 staging、不建 event、不派送、不耗額度；只有真正執行延後候選 input 才計數，timeout／error／UNKNOWN／crash 仍耗額，缺 receipt 不視為 0；符合條件而保存／讀回失敗停 intent 前，不冒充安全方法不足；條件不成立記未備妥原因、不增 GUI、不阻止原本符合 B1 gate 的直接下載。與計畫 L24-27 一致。
- `references/evidence-template.md:1269（canonical slot）`：沿用原 taskDir／inputDir／既有 request 路徑，operationId 由 intent 讀回 attempt_id 導出；intent CLI 成功建 staging 後才補入 attempt_id 與唯讀事件 intent_event_ref；真正 request 只能在 B1 原 gate 再次成立後依當次 fresh before／AX 重核方法、安全區、viewer／三層身分與 mapping，才 wx 寫入並同 bytes 讀回，不得沿用骨架舊座標；request 本身非 LINE event／未派送證明／額度外授權。符合計畫 L28。
- `references/evidence-decision-cases.md:162-186（C19／C20／C21）`：
  - C19 客觀條件成立時的 intent 前骨架：無預測即準備，骨架非 receipt／派送／已耗額；成功後才建 intent，CLI 後補引用再 fresh 重核；保存／讀回失敗停 intent 前；禁把計畫 budget_after=2 當已耗額、骨架當 receipt、先建 staging／猜 ID、沿用舊點、未見 transient 就不必準備。
  - C20 未具準備條件時的直接下載：僅表延後例外未準備，不否決合法直接下載，不補未授權 GUI 探索；禁無方法嘗試取得、禁以未準備阻止直接下載、禁 I/O 失敗冒充安全不足。
  - C21 intent 後才發現未準備或額度不符：intent 後禁臨時補造，骨架非派送／額度／解鎖證明；保留原 intent 走 outcome／reconcile，不足記 UNKNOWN；禁補 statement／request、重播舊點、第三候選、空 staging／缺 receipt／零計數當額度 0、舊 UNKNOWN 解鎖。
  - 三例均註明真實 GUI／成效仍 `NOT_RUN`，文件案例非實機 `OBSERVED`；符合計畫 L29「案例不作真人 OBSERVED 或 GUI PASS」。
- 範圍與邊界：diff 未提 AUDIO、未加 suffix／enum／event；總額仍兩次，無第三候選；未新增 schema／CLI／controller／登錄／狀態機；骨架沿既有 Reveal 欄位；`git diff --name-only -- src tests` 為空，無執行碼變更；`git diff --name-only` 除四檔外僅既有 dirty 提報單（依指示未讀），docs/plans 與 .playwright-mcp 為 untracked（未讀）。

## 限制

- 本 ACCEPT 僅為四檔文件對已 ACCEPT 精確計畫 hash 版本的符合性；不簽 Worker 31 tests、Leader 三條回歸、實機 GUI、日常備份、音訊、chooser、跨 Session 或核心可重複使用能力，相關均維持 `NOT_RUN`／待獨立驗收。
- 若計畫或四檔任一變更，須重新審查；未接受不派後續工作。
