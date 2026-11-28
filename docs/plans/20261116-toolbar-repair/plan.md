# 記事本短暫工具列：有界修復計畫

日期：2026-11-16；基準：`dfaf99bb009dadd5c3f463535af6e6aa4b72a78f`。

## 授權與保護邊界

Owner 本次末段要求統籌 Worker 1／2 修復、整理上下文及 commit／push；續訊要求自行向 Tester 釐清、不需人工介入。據此執行開發工作，不執行前段 Planner prompt 所禁止的 LINE／下載／真實帳本寫入。本計畫不是新的 GUI 授權。不 merge、不 force-push、不改 master。

使用者原有 dirty `問題提報單.md` 保持原件、不 stage。原始證據與協調紀錄放 `.local/line-backup/tasks/20261116-toolbar-repair/`。未找到根目錄合約引用的 `policies/v4.9.0/`；不補造已退役框架，直接遵守現行 AGENTS.md 的邊界。兩個 Worker 是本任務 helper，不啟動正式 Reviewer／Acceptance 角色、不簽發獨立通過。

## 初步根因判斷

直接失敗點是控制就緒 gate，五項沒有 intent。C 有正面可見畫面，後來消失；D 四項只證明 after 觀察未見，不能證明兩次觀察之間從未出現。兩者不是下載失敗。

`dfaf99b` 是新增硬停的回歸候選，不能認定為首次阻塞的唯一根因：其 parent `d655025` 已記錄同類控制發現阻塞，parent 操作規格也已禁止 media body／右鍵探索。主要修正是把正面可操作窗口接到交易，並給 intent 前短暫／未顯示狀態一個有證據且不能洗額度的有限接續；不以重寫 ledger 解鎖。

## P0 修改範圍與分工

1. Worker 1：Skill 與 `gui-inventory.md`、`download-and-ledger.md`、`verification-and-recovery.md`、`evidence-decision-cases.md` 的操作契約。
   - 先完成歷史／身分／盤點／返回錨點及 CLI 呼叫準備，再 reveal。
   - `TOOLBAR_VISIBLE` 正面證據充分就保存並接續 intent，不加固定 stability 等待；intent 讀回後仍須當次重新定位，消失就保留原 intent 並停止，不新增 attempt 或 re-arm。
   - intent 前初次候選加至多一次 re-arm（總計最多二次），每次須新的充分觀察與相關新證據、同一三層身分／有效前景／無 chooser、無 intent、無未解輸入。依 list/post/media 持久累計；不靠 reopen、新 Session 或新目錄重置；兩次無新資訊停止。不得從舊事故剩餘額度推論可直接再點。
   - 只用當次文件支持的 hover 或已證明安全的現有候選，不恢復 body／secondary click；無安全區即停止。D 無可用方法時保留阻塞，不承諾純文件修復能完成五項。
   - 由實際進入來源建立 `expected_return_role`，一層返回後判讀；同頁未變與入口真的遺失分開，不再固定把 viewer return 填 LIST。
2. Worker 2：`evidence-template.md` 與必要的 helper 測試。
   - 持久保存 viewer/post/media 核對矩陣、來源引用與 MATCH／拒絕；label 不充當身分。矛盾原件保留在 quarantine／未採信狀態，不歸屬新事件；舊錯名只追加說明，不改舊 bytes。
   - 同步 reveal／re-arm 欄位與次數；保存 screenshot／AX 各自來源與時間，未知不補值，不宣稱 atomic。
   - 普通 NAVIGATION 的頂層 native undefined，沿用下載 wrapper 已有 typed 回傳表示法；這只修保存，不能變成命中／成功／NOT_SENT。巢狀 undefined、循環、不完整 raw 仍拒絕完整性宣稱。無證據不擴寫 CUA 能力。
3. 統籌：與 Tester 釐清原始時序，整合證據推理、責任分層、真實 GUI 驗證計畫、最終報告及 Git 交付。

### 同範圍補充：落地 diagnostic 一致性

Tester 在原始 artifacts 發現 `ready_for_bind` 的回傳值與落地檔矛盾；原模板 `persistObservation` 初始化 metadata=false，成功時只更新回傳 output，沒有同步落地 metadata。這是本次證據保存層可直接檢驗的缺陷，不能推成 C／D GUI 原因。Worker 2 另核對並最小修正同一 helper 的落地欄位，使落地與回傳的 readiness／blockers 一致；加合成成功及失敗讀回測試，不改 CLI／ledger 語意。此項在修改前記入計畫；未擴張 LINE 或真實資料授權。

不改 `src/line_backup_batch/notes.py`、帳本事件／completion 語意、六類狀態、既有正式啟動 Prompt 或相簿流程。不新增 controller、GUI sensor、schema、下載替代入口。

## P1 與後續

hover 能力確認、來源捕捉順序／延遲及 LINE auto-hide 因果須在獨立、正式日常授權及有效前景內實測。只有真實證據支持現有 API 不足時才另提 wrapper 擴充，不先造 hover API。無需本次做完整 GUI 自動測試框架或新 telemetry 系統。

## 驗證與停止

- helper 只用合成 input／fake app，核對頂層 undefined 保存、巢狀資料缺口、一次呼叫及既有錯誤拒絕。
- 必要現有回歸：daily records、notes `--help`、`test_notes*.py`，另 `git diff --check`。回歸前後比對永久紀錄及 active locators 的檔案清單／hash；不含媒體區，不宣稱 OS 隔離。
- 真實 GUI C 一項及 D 1/5、2/5、3/5、5/5：本次 `NOT_RUN`。未來沿手冊正式日常 Prompt，保留既有完成項，逐項保存 reveal→intent→單次下載→chooser 一次確認→outcome→download-check→completion，核對返回與跨 Session 不洗額度。
- 不靠離線 PASS 宣稱五項修好，不把 helper 自評當獨立接受。超出邊界或出現未解拒絕即停止依賴工作並報告。
