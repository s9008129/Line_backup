# Code & Security Review 紀錄：`docs/plans/20261126-notes-page-key-guard/plan.md`（v3）

## Round 1

- 審查者：Reviewer pane（`wA:pM`，Read-Only 獨立審查，使用 `$code-reviewer` 與 `AGENTS.md` Independent Review Constitution）
- Verdict：`REQUEST_CHANGES`
- Replan 評估：無需 replan；`src/line_backup_batch/notes.py` 實作與核心架構已通過審查，僅需 2 項最小精確修正對齊 Plan v3。
- Findings（2 `[MAJOR]`）：
  1. `[MAJOR]` `.agents/skills/line-notes-agent-cua/references/evidence-template.md:2408`：原句把沿用歷史事件／前頁讀回 `identity` 寫成所有 `page` 的提交前提，可能阻擋首次備份第一頁之全新貼文。最小修正：將沿用規則限定於已核對歷史貼文與 overlap，全新貼文取值與 `null` 槽位直接引用 `gui-inventory.md#page-前雙向對帳`。
  2. `[MAJOR]` `tests/test_notes_regressions.py:3803`：成功重試測試使用通用 `fresh_evidence()`，未於 statement 記錄實際修正後 rows 與斷言陣列，亦未核對新追加 `page` 事件之 `evidence.sha256` 等於新 bundle 雜湊（變異測試換回舊拒絕 bundle 仍可通過）。最小修正：以實際修正後 rows 與斷言陣列建立重試 statement／bundle，並斷言新 `page` 事件 `evidence.sha256` 精確等於新 bundle 雜湊且不等於舊拒絕 bundle（舊拒絕 bundle 雜湊仍完全未入 `evidence/`）。

## Round 2

- 審查者：Reviewer pane（`wA:pM`，Read-Only 獨立審查，使用 `$code-reviewer` 與 `AGENTS.md` Independent Review Constitution）
- Verdict：`APPROVE`
- Findings：`None`
- 核對要點：
  - 核對兩個修正檔 SHA-256：`evidence-template.md`（`734a848a3e7d5b8e65e9fc6575d5d585af7f6d33b65d3b5ec718bdd9d8ca6738`）、`tests/test_notes_regressions.py`（`d37a96884c8ea92c1baccf80c13ed257034c22aac1697475645eb363fd2880ec`）；`src/line_backup_batch/notes.py`（`b10ad336bcedaa04cddfea63aa3a940cea8153432ff781482ed16abd2b7613e5`）與其餘 3 份文件維持 Round 1 原件。
  - 在工作樹外暫存副本重跑 `test_notes*.py` 397 項通過、`notes --help` 與 `page --help` exit 0，並以變異測試確認刻意將重試證據換回舊包時，於新 `page` 事件之 `evidence.sha256` 斷言失敗；`test_daily_records.py` 73 項沿用 Round 1 通過結果（`daily.py` 與相簿測試零差異）。
  - `git diff HEAD --check` exit 0，4 份文件既有 `##`/`###` 標題一致，9 個候選檔 `/Users/` 字面掃描 0 命中。
  - 證據界限：真實 LINE GUI、事故帳本恢復掃描、chooser、實機 `download-check`、跨 Session 恢復與正式 E2E 維持 `NOT_RUN`。
