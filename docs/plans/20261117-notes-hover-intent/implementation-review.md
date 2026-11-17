# 指定 Reviewer 實作符合計畫審查

來源：Owner 指定 Herdr Reviewer pane `w5:pB`；以下為其完整回覆。審查未執行測試或真實 GUI，不代表 E2E 接受。Leader 在審查前後另核對七個來源檔 SHA-256 未變，原始 manifest 留私有 task。

實作符合計畫唯讀審查（不改檔、不跑測試、不含 dirty 提報單/`.playwright-mcp`）：

範圍：`SKILL.md`、`gui-inventory.md`、`evidence-decision-cases.md`、`verification-and-recovery.md`、`evidence-template.md`、`download-and-ledger.md`、`tests/test_notes_input_helper.py`。分支 `feature/line-notes-media`。

verdict：**ACCEPT** —— 無 blocking findings，可按此版交 Leader 整合回歸。

Findings（皆非 blocking）：

1. [Pass] B1 窄例外完整：`gui-inventory.md:109-114` 同 scope 原 `candidate_ordinal=2`、不增第三候選；當次新 intent 讀回、同 Session/連續前景/同 viewer/三層身分、`budget_before=1`、intent 前 `TOOLBAR_VISIBLE`、intent 後可見轉隱藏為新 gate；`111` 以完整連續原件+持久 intent 讀回正面核對尚無下載呼叫/無 outcome/無 chooser/活動下載/pending naming/未解 attempt/輸入，零計數/空 staging/缺檔不單獨證明；舊 `UNKNOWN`/crash window/中斷/新 Session/額度不明禁入。`114` 其餘封鎖：下載呼叫一旦開始或不明即永久關窗，不重置額度。
2. [Pass] 既有 exclusive slot：`download-and-ledger.md:289` 同 attempt 原 `taskDir/inputDir`+`attempt_id` 導出固定 `operationId`，`wx`+逐 bytes 讀回才進 callback；`intent_event_ref` 非 CLI 原生，由唯讀 `sequence/event_sha256` 建立，已見 HEAD `evidence-template.md:1281` 既有 Attempt 表，非新 ledger 狀態；`evidence-template.md:1266-1270` 只用既有 Reveal 欄位、不建新持久狀態，`selected_state_after=UNKNOWN` 待派送，`1268` 換 ID/目錄/Session 另開 slot 禁止，已存在/讀回非 MATCH 零 input。
3. [Pass] 文件一致、無矛盾：`SKILL.md:18-20` 唯一決策本文仍歸 B1，延後一次不增總額；`evidence-decision-cases.md:C18` 停止反例含已用兩次/額度不明/UNKNOWN/crash/中斷/已有下載呼叫/無安全區/漂移，保存缺口耗額停、`NOT_SENT` 禁止；`verification-and-recovery.md` 矩陣只依 B1，不另授權；`evidence-template.md:1317` `fail_closed=false`+`ready_for_bind=true`+Agent 同份 after 正面核對才交 grounded helper，helper 不視覺判斷，下載 slot 唯一。
4. [Pass] 無過度工程、無因果承諾：無新 controller/event/schema/CLI；沿用 `persistRevealWithDirectAfter`+`persistGroundedDownloadClick`；`C18` 證據界線明示不保證 click 叫回 toolbar、不保證維持到下載，舊事故/新例外皆 `NOT_RUN`；當次僅 click 時只用已選 filmstrip 非播放安全邊緣，無區域即停，不假造 hover API。
5. [Pass] 測試可落實：`tests/test_notes_input_helper.py:+535` 三合成測試——slot 不可重入（第二次 `REQUEST_PERSIST_FAILED`，click/capture 各 1）、capture error 無 after 下載源（`fail_closed=true`）、同份 after 交接一次下載（第二次下載同 slot 拒絕）。只斷言合成呼叫/保護邊界，未把 mock boolean 說成真實核准。

無需另問 Owner：本輪仍無真實 GUI/下載/restart/帳本/照片變更，與 ACCEPT 計畫邊界一致。
