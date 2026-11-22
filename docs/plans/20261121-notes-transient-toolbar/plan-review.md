# LINE 記事本短暫工具列與中斷接續修復計畫 v2 複審紀錄

- 審查日期：2026-11-22（Asia/Taipei）
- 審查對象：`docs/plans/20261121-notes-transient-toolbar/plan.md`（修訂版 v2，SHA-256 `89990d483de0ee333e72caacb751bb87ef10649b307f37f28f75f75b25af7ce5`）
- 對應前次審查：`docs/plans/20261121-notes-transient-toolbar/implementation-review.md`（對 Draft PR #52 `bb88c92395d7aad125089176045752079ccf1dde`／本機 `3e2b1dbbd5d5444e8c100ddb6d276a10804e9023` 之 `REQUEST_CHANGES`）
- 審查範圍：僅核對計畫 v2 內容、與既有程式碼／helper 介面的一致性、最小化變更邊界及可驗證通過條件；未修改產品程式碼、Skill 或測試；未執行真實 LINE GUI 或產品驗收（均維持 `NOT_RUN`）

### Review Verdict: APPROVE
- **Review Type**: Plan
- **Core Goal Alignment**: 修訂版計畫 v2（A1–A5）逐項精準對應 Round 1 Code & Security Review 的 3 項 `[BLOCKER]` 與 2 項 `[MAJOR]`，並保留已通過的切片 B 與既有安全／資料保護邊界，明確推進本案核心目標。
- **Diff / Scope Hygiene**: 核准後的實作範圍嚴格限定為 `.agents/skills/line-notes-agent-cua/references/evidence-template.md` 與 `tests/test_notes_input_helper.py` 兩檔；不改動切片 B、`tests/test_notes_unknown_recovery.py`、Python CLI、帳本 schema、相簿段落或既有 `AGENTS.md`／`.playwright-mcp/`，無過度設計或範圍膨脹。

### Findings
None

### 逐項核對摘要（A1–A5 對照 Findings 1–5）
1. **A1（對照 Finding 1 `[BLOCKER]`）**：要求依啟用分支延遲建立 `directDecision`／`revealDecision`（未用分支識別字保持未宣告）、將直接派送變數改名為 `directDispatchDecision` 消除頂層 `const` 衝突，並規定從 Markdown 實際抽取可複製區塊於同一個頂層作用域執行六種選路與候選 2 案例。
2. **A2（對照 Finding 2 `[BLOCKER]`）**：要求 `checkRevealBefore` 只要 `observation_id` 或截圖／AX 任一原件路徑或 file ref 重複即回 `REVEAL_BEFORE_OBSERVATION_NOT_FRESH`，同時保留不同新路徑允許相同內容 SHA-256（符合 LINE AX 實測特性），並明列對應正反測試案例。
3. **A3（對照 Finding 3 `[BLOCKER]`）**：沿用 `evidence-template.md:438-456` 既有 `snapshotJsonValue` 並由 `evidenceTools` 匯出，要求 `persistReveal` 於第一個 `await` 前建立不可變 JSON 請求快照與定稿 metadata 欄位，並補齊確定的非同步巢狀突變回歸測試。
4. **A4（對照 Finding 4 `[MAJOR]`）**：於 intent 後唯一 capture（`persistObservation`）與既有 `persistGroundedDownloadClick`／`syncGroundedDispatch`／`persistInputDiagnostic` 加入 `HOST_JS_DATE`／`CALL_BOUNDARY_ONLY`／`os_event_time='UNKNOWN'` 的 host 呼叫邊界時間（呼叫前拒絕維持 `NOT_RUN`，拋錯亦記結束時間），只寫本機診斷檔、不新增 CLI／schema，也不承諾工具列壽命或 OS hit-test。
5. **A5（對照 Finding 5 `[MAJOR]`）**：將 Block 9 改為中性「intent 後唯一 capture」並讓 Block 12 直接承接 `intentObservation`、移除 `FRESH_INTENT_OBSERVATION`；補齊「事前 `DIRECT READY`＋`REVEAL STOP` 後轉隱藏」與 `preIntentReveal`（缺值／`STOP`／`DIRECT`）、`candidate_ordinal`／`budget_*`／`prior_candidate_refs` 漂移測試，且正確區分 `checkReveal` 先行拒絕與 `checkRevealBefore` 漂移拒絕。

### Verification Evidence
- 唯讀核對 `docs/plans/20261121-notes-transient-toolbar/plan.md` 全文（83 行，SHA-256 `89990d483de0ee333e72caacb751bb87ef10649b307f37f28f75f75b25af7ce5`）與 `git diff docs/plans/20261121-notes-transient-toolbar/plan.md`，確認切片 B（L58–63）與原版逐字一致。
- 核對 `.agents/skills/line-notes-agent-cua/references/evidence-template.md` 既有實作介面：`persistObservation`（L171–329）、`snapshotJsonValue`（L438–456）、`syncGroundedDispatch`（L460–479）、`persistGroundedDownloadClick`（L864–978）、`persistInputDiagnostic`（L980–1036）、`notesIntentDispatch`（L1254–1645），確認計畫未虛構不存在的 API 或破壞既有介面。
- 審查界限：本 `APPROVE` 僅核准計畫 v2 進入兩檔實作；原 Draft PR #52（`bb88c92`／`3e2b1db`）之 Code & Security Review `REQUEST_CHANGES` 仍有效，實作完成後須以精確候選重新進行獨立 Code & Security Review。真實 LINE E1–E3、chooser、檔案落地、跨 Session 恢復與獨立產品驗收均維持 `NOT_RUN`。
