# Plan Review 紀錄：`docs/plans/20261126-notes-page-key-guard/plan.md`

## Round 1（v1，SHA-256 `3b06f0e4897febd062abc3283dcf9977b86286623cd296a7aee080e60ece7c96`）

- 審查者：Reviewer pane（`wA:pM`，Read-Only 獨立審查，使用 `$code-reviewer` 與 `AGENTS.md` Independent Review Constitution）
- Verdict：`REQUEST_CHANGES`
- Findings（1 `[BLOCKER]` + 5 `[MAJOR]`）：
  1. `[BLOCKER]` `plan.md:122`：重試規格要求重建 `--posts`，未要求保留舊檔／舊 bundle 並另存修正 payload 與重封裝新 `evidence-pack` bundle。
  2. `[MAJOR]` `plan.md:122`：`PAGE_POST_KEY_MISMATCH` 與 `INVALID_EXPECTED_POST_KEYS` 共用重試指示，且未於 `download-and-ledger.md:17` 明確區分其與 `retry_safe`（鎖競爭專屬）的契約關係。
  3. `[MAJOR]` `plan.md:119`：未區分獨立核對過的完成掃描／歷史事件／前頁成功讀回 row 與混合 `summary`（可能含失敗頁 row），且對已編輯貼文的停止規則過寬、涵蓋了跨輪可安全處理之編輯。
  4. `[MAJOR]` `plan.md:76`：`--expected-post-keys` 使既有 `page --e` 縮寫（原解析為 `--evidence`）產生歧義，違反 CLI 向後相容。
  5. `[MAJOR]` `plan.md:101`：拒絕零寫入驗收未要求使用全新未入帳內容之 v2 bundle（避免 SHA-256 去重掩蓋提前保存），且不應僅以 `scan finish` 後無重複 `source_order` 作為修復證據。
  6. `[MAJOR]` `plan.md:135`：範圍驗收僅靠最終 `git status` 無法證明既有未追蹤及忽略資料未變，且 `plan.md:5` 含本機家目錄絕對路徑。
- 修訂處置：全部 6 項已於 v2 完整修正（改用 `--assert-post-keys`／`INVALID_ASSERT_POST_KEYS` 保留 `--e` 縮寫、補齊保留舊檔與另建新 bundle 重試、拆分兩拒絕分支與 `retry_safe` 契約、明訂歷史權威取值與跨輪編輯分流、強化全新未入帳 bundle 與直接事件／completion 測試、改用 `<PROJECT_ROOT>` 並補前後唯讀保護快照）。

## Round 2（v2，SHA-256 `9e5432a7178e3b2a920cd795bc3349ef7688c1dc9c1b63f05dc38c69ab098122`）

- 審查者：Reviewer pane（`wA:pM`，Read-Only 獨立審查）
- Verdict：`REQUEST_CHANGES`
- Findings（1 `[BLOCKER]` + 3 `[MAJOR]`）：
  1. `[BLOCKER]` `plan.md:126`：跨輪文字編輯且唯一確認為同一篇時，未定義首次出現於本輪 `page` 的 `identity` 與斷言欄位取值；若改動 `identity` 會連帶改變 `media_key` 使原 `COMPLETED` 媒體轉成 `PENDING`。
  2. `[MAJOR]` `plan.md:134`：未指定提交前何時保存 `expected_tip` 基準，也未指出因 `summary` 在 open／interrupted 皆回 `IN_PROGRESS` 且不含 `scan_id`，拒絕後須以 `scan`／`page` 事件核對原 `scan_id`／Session／下一頁序號。
  3. `[MAJOR]` `plan.md:135`：`INVALID_ASSERT_POST_KEYS` 在 `download-and-ledger.md` 與 `gui-inventory.md`／`evidence-template.md` 關於何時需重封裝新 bundle 的表述不一致。
  4. `[MAJOR]` `plan.md:149`：保護快照僅以檔名與事件數不足以宣稱內容未變，未涵蓋 `backup/` 與 `.local/line-backup/`，且 `git diff --name-only` 未覆蓋 staged 異動。
- 修訂處置：全部 4 項已於 v3 完整修正（明訂跨輪可唯一確認之文字編輯沿用穩定歷史 `identity`＋斷言原 `post_key` 並於新觀察與 `post` 細盤記錄文字變更，另增第 4 組回歸測試驗證不轉 `PENDING`；補齊提交前 `expected_tip` 基準與拒絕後事件核對；於 `download-and-ledger.md` 統一兩分支重試證據規則並令其餘兩檔純引用；改用 `git diff HEAD --name-status`＋`--untracked-files=all`＋全受保護路徑前後去識別化總雜湊查核）。

## Round 3（v3，SHA-256 `8ea6370bc36af3f4b518f21a19386f80f81c89a2f03cfc4984fc01d705217046`）

- 審查者：Reviewer pane（`wA:pM`，Read-Only 獨立審查，使用 `$code-reviewer` 與 `AGENTS.md` Independent Review Constitution）
- Verdict：`APPROVE`
- Findings：`None`
- 核對要點：
  - `shasum -a 256` 確認 v3 雜湊為 `8ea6370bc36af3f4b518f21a19386f80f81c89a2f03cfc4984fc01d705217046`。
  - 記憶體模擬確認兩種拒絕（`PAGE_POST_KEY_MISMATCH`／`INVALID_ASSERT_POST_KEYS`）均於保存證據與追加事件前中止，沿用原 `post_key` 時可另寫新文字雜湊，且 `--e` 等 89 個既有唯一前綴維持原解析。
  - 白名單兩切片共 6 檔零重疊，無本機家目錄路徑外洩。
