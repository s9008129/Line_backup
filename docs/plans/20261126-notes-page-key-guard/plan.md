# LINE 記事本 page 10 貼文身分漂移與寫入前鍵值預檢修復計畫

- 計畫日期：2026-11-26（Asia/Taipei）
- 版本：v3（已全數修正 Plan Review Round 1 之 6 項與 Round 2 之 4 項 Findings）
- 專案：`<PROJECT_ROOT>`
- 分支：`feature/line-notes-media`
- 基準 HEAD：`296be838da26092db2ef1587542209b7157eceb6`
- 問題提報單：`docs/diagnostics/20261126-notes-daily-page10-key-mismatch/問題提報單.md`
- 隱私邊界：本計畫、審查紀錄與後續所有 Git 追蹤變更均不含真實群組／列表名稱、作者、貼文正文、原始檔名、使用者本機家目錄絕對路徑或本機帳本內容；路徑一律以 repo 相對路徑或 `<PROJECT_ROOT>` 表示。
- 受保護與既有未追蹤資料：本機 `notes-backup-records/`、`backup/`、`.local/line-backup/`、`docs/diagnostics/20261126-notes-daily-page10-key-mismatch/問題提報單.md` 及既有未追蹤項目（`2026.1122_問題提報單及意圖釐清點.md`、`docs/diagnostics/20261125-notes-daily-backup-handoff/`、`docs/diagnostics/20261126-notes-daily-stop-after-post13/`）不修改、不覆寫、不 stage；凡宣稱內容未異動者，須留存前後私有內容雜湊查核證據（見 §4）。

## 1. 核心目標與實證根因分析

本專案核心目標是讓不同模型、Agent 與 Session 皆能透過同一日常正式 Prompt 與 `line-notes-agent-cua` Skill，搭配原生 macOS Computer Use 與 notes 輔助 CLI，**全程無人值守、可靠且可重複地完成單一指定 LINE 記事本列表照片與影片的備份、驗證及跨 Session 接續**，同時堅守永久帳本不可變性、三層嚴格身分契約與最小必要變更原則。

經核對問題提報單、`src/line_backup_batch/notes.py`、Skill／references、既有去識別化帳本結構及 Tester（`wA:pN`）現場釐清，本次事故之實證根因與分項裁決如下：

| 問題項 | 實證事實 | 根因歸類 | 最小修復策略 | 歸屬切片 |
|---|---|---|---|---|
| **P1（主因）：page 10 第 14 列 `identity` 漂移於寫入永久 event 後才被發現** | page 00–09（`source_order=0..13`）與 page 10 row 13 的輸入 `{identity, date_summary}` 與歷史完成 scan 投影逐位元組相同、全數命中歷史 `post_key`；唯獨 page 10 row 14 的 `statement`／`source-ledger` 預期歷史 key `7b21…576b`，實際 `page-10-posts.json` 卻送出縮短／重寫的 `identity`（`visual_key` 63 vs 95；`text_anchor` 99 為歷史 191 前綴）。`notes page` 於 `notes.py:3806` 計算出新 key `7a51…dfd6` 並直接追加不可變 event 100；Agent 讀回後才發現 `source_order=14` 雙列投影並觸發 `page_gate` 停止。 | **雙重缺口**：(1) CLI `page` 缺少寫入前預期 `post_key` 斷言（無法在 `_preserve_evidence`／`append` 前 fail-closed 攔截）；(2) Skill／references 雖對媒體明訂「既有媒體沿用原 key／identity」，但對**貼文**未明訂從權威歷史來源（獨立核對過的完成掃描／既有歷史事件；overlap 以前頁成功讀回 row 為準，排除失敗頁 row）原樣沿用穩定 `identity`、跨輪僅文字編輯時維持穩定 `post_key` 以避免完成媒體轉成 `PENDING`，以及寫入前預期鍵預檢與拒絕後統一證據重試流程。 | (1) 在 `notes.py` 的 `page` 新增**可選** `--assert-post-keys` 寫入前斷言（`--a` 前綴不與既有 `--e`／`--evidence` 等任何縮寫衝突；零 event schema 變更、完全向後相容），不符即在保存 evidence 與 append event 前以 exit 4 `PAGE_POST_KEY_MISMATCH` 零寫入拒絕；(2) 在 `gui-inventory.md`、`download-and-ledger.md`、`evidence-template.md` 與 `SKILL.md` 補齊權威取值、原樣沿用穩定貼文 `identity`（含跨輪可唯一核對之文字編輯）、`page --assert-post-keys` 預檢、提交前 `expected_tip` 基準與拒絕後統一新 bundle 重試契約。 | Slice 1（CLI＋測試）＋ Slice 2（Skill／references） |
| **P2（獨立證據紀律缺口）：`observation-inv-18` 的 `.diagnostic.json` 遭本地原地手動修改** | 提報單 §8 第 4 點與 Tester 核對記載 `observation-inv-18-20261126-1627.diagnostic.json` 曾在本地衍生檔上手動修正 `full_tree` 與 `ready_for_bind`（AX／screenshot mtime `16:27:18`，diagnostic mtime `16:27:33`）。現行 `evidence-template.md:59` 禁止以手寫 curated diagnostic 取代 helper，但未明禁「對 helper 已落地之 `.diagnostic.json` 原地編輯修補」。 | **文件規則缺口**（非 helper 程式缺陷；`cua-evidence-tools` 原本即採 `wx` 獨占寫入，無 edit API）。 | 於 `evidence-template.md`（單一本文）與 `SKILL.md`（摘要連結）明禁對 helper 已落地之 `.diagnostic.json` 進行原地編輯／修補（例如把 `full_tree`、`ready_for_bind` 改為 `true` 或清空 `blockers`）；遇異常應保留原檔不動、記為證據異常，以新 `observationId` 重跑 `captureAndPersist` 或停止。 | Slice 2 |
| **N1（刻意不改）：`notes.py` 的 `post_key()` 嚴格雜湊與 `_post_rows()` `IN_PROGRESS` 投影** | `post_key()` 對 `(list_key, identity)` 做嚴格 canonical SHA-256；`_post_rows()` 在 `current_complete=False` 時並陳歷史 scan 與進行中 scan 的 `page` rows。 | **刻意設計（Chesterton's Fence）**，非缺陷。 | **完全凍結**：不放寬 `post_key()` 做模糊／前綴認領（違反 `AGENTS.md` 嚴格身分紅線）；不修改 `_post_rows()`（進行中 scan 若頂端新增貼文，新舊 scan 在同 `source_order` 並陳不同 `post_key` 屬合法中間態，直到 `scan finish` 收斂）。 | 無需修改 |
| **N2（刻意不改）：`evidence-pack` 不解析 `statement` 語意** | `evidence-pack` 僅核對 bundle 結構、context 與子資產 bytes／SHA-256。 | **刻意職責邊界**，非缺陷。 | **完全凍結**：不在 `evidence-pack` 新增自由文字解析器；改由 `page --assert-post-keys` 在機器層對 `--posts` 強制驗證。 | 無需修改 |

## 2. 明確非目標與最小修改邊界（Strict YAGNI / KISS）

- **不新增獨立 `post-key` 子命令或 `page --dry-run` 模式**：獨立子命令無法在寫入點強制約束，易產生「查完仍送錯檔」之 TOCTOU 落差；`--dry-run` 則在寫入命令中混入旁路分支。可選 `--assert-post-keys` 直接於 `NotesRecords.page()` 寫入邊界原子攔截，最小化表面積且零繞過縫隙。
- **嚴格保持 CLI 旗標與縮寫向後相容**：既有 `page` 參數前綴為 `--r`/`--se`/`--sc`/`--pa`/`--po`/`--o`/`--t`/`--b`/`--e`；選用 `--assert-post-keys`（`--a` 前綴）確保既有的 `--e`（解析為 `--evidence`）與全部 89 個既有可唯一解析前綴維持不變，零歧義、零回歸。
- **完全凍結事件與帳本格式**：`line-notes-page/v1` 事件 schema、事件載入驗證、`_post_rows()`、`summary()`、`evidence-audit`、`list-key` 及所有既有 `notes` 子命令均**零變更**；`--assert-post-keys` 僅為寫入前輸入斷言，不寫入 event payload，100% 向後相容全部既有帳本與既有呼叫端。
- **不新增 `NotesError` 子類別或變更 `retry_safe` 契約**：沿用既有 `NotesError` 輸出格式 `{"status":"REFUSED","reason":"<CODE>","dispatch_authorized":false}`（exit 4，**不含** `retry_safe` 欄位；保留 `retry_safe` 專屬於 `NOTES_LOCK_BUSY` 之既有測試契約 `tests/test_notes_locks.py:230-271`）。
- **完全凍結 `cua-evidence-tools` 與 `cua-initial-observation` JS 區塊**：P2 屬人工原地編輯違規，不新增 helper API、不變動 `tests/test_notes_input_helper.py` 或 `BLOCK_MARKERS`。
- **完全凍結 `AGENTS.md`、`docs/LINE相簿備份_使用手冊.md`、`verification-and-recovery.md`、`evidence-decision-cases.md` 與既有 Markdown 標題／錨點**：日常正式 Prompt 與專案常駐指令無需膨脹；所有既有 `##`/`###` 標題與錨點原樣保留。
- **不自動修改真實帳本或宣稱本次修復已解除真實備份阻塞**：真實帳本（含 event 100 與 open scan `aa628f2a...`）完全不觸碰；真實 LINE 實機測試維持 `NOT_RUN`。

## 3. 平行子任務切片設計（零檔案重疊）

本計畫經下方 Reviewer pane（`wA:pM`）依 `code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution 審查獲 `APPROVE` 後，平行分派予右方兩個 Worker pane：

### Slice 1（分派給 Worker1 `wA:pP`）：`notes.py` `page --assert-post-keys` 寫入前預檢與回歸測試

- **檔案白名單（僅 2 檔）**：
  1. `src/line_backup_batch/notes.py`
  2. `tests/test_notes_regressions.py`
- **具體修改規格**：
  1. `src/line_backup_batch/notes.py`：
     - **`NotesRecords.page(...)`（L3772–3849）**：
       - 新增可選關鍵字參數 `assert_post_keys=None`（維持完全向後相容）。
       - 於鎖外基本參數檢查區（緊接 `overlap_keys` 檢查 L3777–3779 之後，在 `need(isinstance(posts, list), 'INVALID_PAGE_POSTS')` 之後）：
         ```python
         if assert_post_keys is not None:
             need(isinstance(assert_post_keys, list) and
                  len(assert_post_keys) == len(posts),
                  'INVALID_ASSERT_POST_KEYS')
             seen_expected = set()
             for expected in assert_post_keys:
                 if expected is not None:
                     _hex(expected, 'INVALID_ASSERT_POST_KEYS')
                     need(expected not in seen_expected,
                          'INVALID_ASSERT_POST_KEYS')
                     seen_expected.add(expected)
         ```
         契約說明：
         - 省略或 `None`：維持原行為，不檢核預期鍵。
         - 非 `list`、長度與 `posts` 不等、任一元素既非 `None` 亦非合法 64 位小寫十六進位字串（含空字串、大寫 hex、數字、布林、物件／陣列）、或存在重複非 `None` hex 鍵：以 `INVALID_ASSERT_POST_KEYS` 拒絕（鎖前即拒，零事件、零證據寫入）。
         - 允許陣列內出現多個 `None`（代表同一頁多張確實新發現之貼文）。
       - 於 `with self.locked():` 的 `for index, row in enumerate(posts):` 迴圈內（L3800–3819），緊接 `key = post_key(...)` 與 `need(key not in page_keys, 'DUPLICATE_POST_IN_PAGE')` 之後（仍在 `_preserve_evidence()` L3843 與 `self.append('page', data)` L3848 之前）：
         ```python
         if assert_post_keys is not None:
             expected_key = assert_post_keys[index]
             if expected_key is not None:
                 need(key == expected_key, 'PAGE_POST_KEY_MISMATCH')
         ```
         契約說明：
         - 任一非 `None` 位置計算出之 `post_key` 與預期值不符，立即拋 `NotesError('PAGE_POST_KEY_MISMATCH')`；此時尚未呼叫 `_preserve_evidence()` 亦未呼叫 `self.append()`，保證 `events/` 與 `evidence/` 雙重零異動。
         - `expected_key is None` 代表該位不對預期歷史鍵作斷言（供確實新發現貼文使用）；所有既有 overlap、top/bottom、duplicate、session、sequence 檢核完全保留不減弱。
         - `data`（`line-notes-page/v1`）欄位完全不變。
     - **`_build_notes_parser()`（L8028–8041）**：
       - 在 `page` subparser 新增可選參數（`--a` 前綴，絕不與 `--e`/`--evidence` 等既有縮寫衝突）：
         ```python
         page.add_argument(
             '--assert-post-keys',
             help='Optional JSON array or @JSON-file of expected 64-hex post keys (or null for new posts) aligned with --posts')
         ```
     - **`main()`（L8294–8304）**：
       - 處理 `--assert-post-keys`：
         ```python
         assert_post_keys = None
         if args.assert_post_keys is not None:
             assert_post_keys = _json_cli_argument(
                 parser, args.assert_post_keys, '--assert-post-keys')
             if assert_post_keys is None:
                 raise NotesError('INVALID_ASSERT_POST_KEYS')
         ```
         並傳遞 `assert_post_keys=assert_post_keys` 給 `records.page(...)`。
         契約說明：
         - 未提供旗標：`args.assert_post_keys is None` → `assert_post_keys=None`（沿用原行為）。
         - 明確傳入 JSON `null`（inline 或 `@file`）：不靜默降級，fail-closed 回 exit 4 `INVALID_ASSERT_POST_KEYS`。
         - 非法 JSON 語法或不存在 `@file`：由 `_json_cli_argument` 觸發 `parser.error`（exit 2，與 `--posts`／`--overlap-keys` 一致）。
  2. `tests/test_notes_regressions.py`（新增聚焦回歸測試，不弱化或更動既有測試）：
     - **`test_page_assert_post_keys_accepts_exact_and_new_post_slots`**：
       - 涵蓋：(a) page 0 全 64-hex 預期鍵匹配；(b) 後續 overlap 頁同時含既有貼文（64-hex）與新貼文（`None`／`null`）匹配；(c) 省略 `assert_post_keys` 維持相容；(d) 驗證持久化 `line-notes-page/v1` 事件 `data` 鍵集合完全不變，不含額外欄位，且 `reopen().summary()`／`evidence_audit()` 均通過。
     - **`test_page_assert_post_keys_mismatch_refuses_before_append_and_allows_fixed_retry`**：
       - 精確重現 page 10 事故模型：先完成首次 scan 取得歷史貼文（長 `visual_key` 與 `text_anchor`）並完成一項媒體的 `completion`（記錄其原 `completion` event）；開新 scan 後，在第二頁對第 2 列送出縮短 `visual_key`／前綴 `text_anchor` 但傳入歷史 `assert_post_keys`，且**該次拒絕呼叫必須使用一個含全新、未曾入帳位元組內容的 v2 evidence bundle**（避免 SHA-256 去重掩蓋提前呼叫 `_preserve_evidence()`）。
       - 同時以 Python API 與 CLI（含 `@JSON-file`）驗證：
         1. CLI 回 exit 4、`status == 'REFUSED'`、`reason == 'PAGE_POST_KEY_MISMATCH'`、`dispatch_authorized is False`，且**不含 `retry_safe` 鍵**。
         2. 拒絕前後 `events/` 檔案集合與 bytes、**以及 `evidence/` 目錄檔案集合與 bytes** 皆**完全未異動**（雙重零寫入，且新 bundle 的子 blob 與外層 SHA-256 均未進入 `evidence/`）。
         3. 保留被拒絕的 payload 與 bundle 不覆寫，另建含原樣歷史 `identity` 的新 payload 與**新的對應 v2 evidence bundle**，保留同一 `--assert-post-keys` 重跑 `page` 成功。
         4. 直接核對新寫入之 `page` 事件 `posts`：精確包含預期歷史 `post_key`，且錯誤的縮短 `post_key` **從未出現在任何事件中**；核對原 `completion` 事件原樣保留；完成 `scan finish` 並依既有流程重做該貼文的新掃描 `post`/`media` 細盤後，核對 `reopen().summary()` 中該歷史媒體仍投影為 `COMPLETED`，無重複 `source_order` 且 `evidence_audit()` 通過。
     - **`test_page_assert_post_keys_cross_run_text_edit_preserves_completed_media`**：
       - 合成驗證跨輪僅文字編輯場景（對應 Round 2 Finding 1）：首輪 scan 完成一篇貼文與一項媒體 `completion`（記錄原 `text_sha256`、`post_key`、`media_key`）。第二輪開新 scan 時，貼文正文已編輯但確認為同一篇，故 `page` 沿用穩定歷史 `identity` 並以 `assert_post_keys=[original_post_key]` 通過，接著 `scan finish` 後於 `record_post` 寫入新的 `text_sha256`（與新觀察證據）並以原媒體 `identity` 執行 `record_media`；驗證 `reopen().summary()` 中 `post_key` 與 `media_key` 不變、原媒體維持 `COMPLETED`（絕不轉為 `PENDING`）且 `posts[0]['text_sha256']` 已更新為新雜湊。另附反例對照：若錯誤把新文字塞進 `identity` 並帶 `assert_post_keys=[original_post_key]`，會於寫入前遭 `PAGE_POST_KEY_MISMATCH` 攔截，避免產生新 `post_key`／`PENDING` 媒體。
     - **`test_page_assert_post_keys_rejects_invalid_shapes_and_preserves_evidence_abbrev`**：
       - 以 `subTest` 覆蓋非 list（dict／str／int）、長度不符（過短／過長）、非法元素（空字串、大寫 hex、非 64 字元、int、bool、dict）、重複非 `None` hex 鍵，驗證皆以全新未入帳 bundle 拋 `INVALID_ASSERT_POST_KEYS` 且 `events/` 與 `evidence/` 雙重零異動；
       - 以 CLI 驗證 `--assert-post-keys null`（inline 與 `@file`）回 exit 4 `INVALID_ASSERT_POST_KEYS`、無效 JSON 語法回 exit 2；
       - **Parser 縮寫回歸**：直接驗證 `_build_notes_parser().parse_args([... '--e', '/tmp/e' ...])` 仍精確解析為 `args.evidence == '/tmp/e'`（零歧義），不因新增 `--assert-post-keys` 破壞既有的 `--e` 縮寫相容性。

### Slice 2（分派給 Worker2 `wA:pQ`）：Skill 與 3 份參考文件契約補強（權威來源取值、穩定貼文 `identity`、寫入前預檢與 diagnostic 不可變性）

- **檔案白名單（僅 4 檔，與 Slice 1 零重疊）**：
  1. `.agents/skills/line-notes-agent-cua/SKILL.md`
  2. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`
  3. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`
  4. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`
- **具體修改規格（嚴守單一本文＋短連結原則，不跨檔重複或矛盾；嚴禁更動既有 Markdown 標題與錨點）**：
  1. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`（貼文 `identity` 權威取值、跨輪文字編輯與 `page` 前對帳唯一本文）：
     - `### 貼文`（L24–28）：補上與媒體對稱之規則——
       - 當次多訊號觀察正面確認某張來源卡對應既有帳本中未變動之歷史貼文時，**必須以程式從獨立核對過的最新完成掃描（`scan COMPLETE` 事件）或既有歷史事件原樣抽取該篇穩定 `identity` 物件與預期 `post_key`**（禁止人工轉錄、摘要、截斷或重寫 `visual_key`／`signals.text_anchor`），並於 `page` 提交時以 `--assert-post-keys` 宣告預期 `post_key`。進行中或曾中斷掃描的混合 `summary` 僅用於定位候選，**對帳失敗頁或未收尾中斷頁的 row 不得直接作為既有歷史 `identity` 或預期鍵來源**。
       - **跨輪文字編輯 vs 無法唯一核對 vs 本輪覆蓋漂移**：
         1. 若為新一輪掃描開始前即已發生之文字編輯，且當次多訊號觀察能**唯一確認**為同一篇歷史貼文（而非另一篇貼文）：本輪 `page` 首次出現時仍**原樣沿用該篇既有穩定 `identity` 並以 `--assert-post-keys` 斷言原 `post_key`**（避免改變 `post_key` 連帶導致同篇未變媒體產生新 `media_key` 而轉成 `PENDING` 重下），同時將實際觀察到的文字變更記於當次新觀察證據與既有 `post` 細盤欄位（`--text-sha256`／`--date-summary`／statement），不掩蓋文字已改之事實。
         2. 若無法唯一確認為同一篇歷史貼文，或新增／刪除與既有媒體對應有歧義：不得硬套舊 `identity` 或自動認領舊完成，依既有[變動與隔離](#變動與隔離)保護該篇並停止該篇新派送（列表級覆蓋仍成立時其他已核對篇可繼續）。
         3. 若為**本輪掃描進行中**相對本輪已提交頁發生的覆蓋漂移／變動：依[finish 前原件重核與來源變動](#finish-前原件重核與來源變動)保留前後證據並停止 finish／新派送。
     - `### page 前雙向對帳`（L67–73）：補明在產生 `--posts` 後、呼叫 `notes page` 前：
       - 先留存本次提交前的 `expected_tip` 基準（取自前次序列讀回 `summary`）。
       - overlap 列須以前一頁成功讀回的本輪 `page` row 原樣取值；既知歷史貼文列（未變或已唯一確認為同一篇之跨輪文字編輯）須從獨立核對過的完成掃描／既有歷史事件原樣取值（排除失敗頁／未收尾頁 row）；僅確實新發現貼文建立新 `identity` 並於對應槽位填 `null`。
       - 呼叫 `notes page` 時搭配 `--assert-post-keys` 依序傳入每列預期 `post_key`（或 `null`），由 CLI 在寫入永久事件前 fail-closed 攔截漂移。
       - 若遇 `PAGE_POST_KEY_MISMATCH` 或 `INVALID_ASSERT_POST_KEYS` 拒絕，一律依 [下載與 notes CLI](download-and-ledger.md#cli-共同契約) 的統一拒絕與重試證據契約處理（本節不再重複展開細節，避免跨檔分歧）。
       - `page` 成功後仍須依原規則完成實際 key 與事件讀回核對，讀回有異即停且不得以 `evidence-correct` 改寫 page 成員。
  2. `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`（`page --assert-post-keys` CLI 契約、拒絕分流與重試證據唯一本文）：
     - `## CLI 共同契約`（L17）：維持 `retry_safe` 專屬於 `NOTES_LOCK_BUSY` 之鎖競爭契約（唯讀 `true`、寫入 `false`），並明確增列 `page` 的兩個寫入前預檢 exit-4 命令專屬分支（皆不含 `retry_safe` 欄位；於 `_preserve_evidence` 與 `append` 前中止，零事件與零證據寫入）及**統一重試證據規則**：
       - **重試前置核對（兩分支共用）**：須以本頁提交前已讀回之 `expected_tip` 為基準；拒絕後先序列讀回 `summary` 確認 `expected_tip` 與基準完全一致，再唯讀核對既有 `scan`／`page` 事件確認原 `scan_id` 仍處於開放狀態（既無 `COMPLETE` 亦無 `INTERRUPTED`，因 `summary` 在開放與中斷時皆回 `scan_coverage=IN_PROGRESS` 且不列 `scan_id`）、綁定 `session_id` 與下一 `page_index` 均相符，最後由 `page` 既有的 records lock 內部檢核（`CURRENT_SCAN_REQUIRED`／`SCAN_ALREADY_COMPLETE`／`PAGE_SESSION_CHANGED`／`PAGE_SEQUENCE_CHANGED`）決定是否接受重試。
       - **統一重試證據規則（兩分支共用）**：無論是 `PAGE_POST_KEY_MISMATCH` 或 `INVALID_ASSERT_POST_KEYS`，**一律保留被拒絕的原 `--posts`、原 `--assert-post-keys`（若有存檔）與原 v2 bundle 不覆寫**；將修正後的 `--posts` 及／或修正後的 `--assert-post-keys` 另存新私有檔案，撰寫反映實際重試輸入（修正後 rows 與斷言陣列）的新 statement，以既有 `evidence-pack` 封裝至新 `--output-dir` 產生新 v2 bundle（當次觀察仍有效時可沿用原始 AX 與截圖檔）並傳入重試 `--evidence`。嚴禁覆寫原 asset、嚴禁沿用引用舊輸入的 bundle、嚴禁省略 `--assert-post-keys` 繞過拒絕。重試仍受「同一根因最多三次有證據嘗試、連續兩次無新資訊即停」上限約束。
       - **兩條拒絕分支分流**：
         1. **`PAGE_POST_KEY_MISMATCH`**：核對待提交 `--posts`、獨立核對過的完成掃描／歷史事件／前頁成功讀回 row 與當次觀察；若確認來源卡為未變歷史貼文（或跨輪可唯一確認同一篇之文字編輯）且差異源自 payload 轉錄／組裝漂移，**保留原已核對之 `--assert-post-keys`**，依上述統一規則從權威來源原樣重建新 `--posts` 與新 bundle 後重試；若無法唯一確認為同一篇或屬本輪覆蓋漂移，依 `gui-inventory.md` 保護／停止，不得硬套舊 `identity`。
         2. **`INVALID_ASSERT_POST_KEYS`**：從獨立核對過的來源對帳（完成掃描／既有歷史事件／前頁成功讀回 row，排除失敗頁 row）重建合法的 `--assert-post-keys` 陣列，依上述統一規則另存新陣列檔並封裝與實際重試輸入一致的新 bundle 後重試。
     - `## 目前子命令`（`page` 列 L38）：補記可選 `--assert-post-keys` 寫入前預期 key 預檢。
     - `### 必填參數矩陣`（`page` 區塊 L79–80 與下方說明段 L127–130）：於 `page` 補列 `[--assert-post-keys JSON_OR_@FILE]`，說明其為與 `--posts` 等長對齊之 JSON 陣列（既有歷史貼文／前頁 overlap 填 64-hex 預期 `post_key`，確實新貼文填 `null`；明確傳入 JSON `null`、非陣列、長度不符、非法元素或重複非空鍵拒絕 `INVALID_ASSERT_POST_KEYS`；僅作寫入前斷言，不變更 `line-notes-page/v1` 事件欄位，且 `--a` 前綴不與既有 `--e`／`--evidence` 縮寫衝突）。
  3. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`：
     - `## CUA 觀察原件落地`（L59 與 L1210）：明禁對 helper 以 `wx` 落地之 `.diagnostic.json` 進行**原地手動編輯或修補**（例如將 `full_tree`、`ready_for_bind` 改為 `true` 或清空 `blockers`）；該檔屬不可變診斷原件。若 diagnostic 出現 blocker 或疑義，只可原樣保留、記為證據異常，並以新 `observationId` 重新呼叫 `captureAndPersist` 取得新觀察或依規則停止。
     - `## page／finish 覆蓋紀錄`（L2408）：精煉同步 `page_gate` 條文——提交前除 `source_to_rows`、`rows_to_source` 與待解為零外，須留存提交前 `expected_tip` 基準，由權威來源（獨立核對過的完成掃描／歷史事件或前頁成功讀回 row，排除失敗頁 row）原樣沿用穩定 `identity`，並以 `--assert-post-keys` 經 CLI 寫入前預檢；遇 `PAGE_POST_KEY_MISMATCH`／`INVALID_ASSERT_POST_KEYS` 拒絕時一律依 [下載與 notes CLI](download-and-ledger.md#cli-共同契約) 之統一重試證據規則處置（本節不重複細節）；`page` 成功後仍須核對讀回 key 與來源對應，有異即停且不得以 `evidence-correct` 改寫 page 成員。
  4. `.agents/skills/line-notes-agent-cua/SKILL.md`：
     - `## 工作流程` 步驟 3（L88）：精煉補一句——既知歷史貼文（含跨輪可唯一確認同一篇之文字編輯）須由獨立核對過的完成掃描／歷史事件原樣沿用穩定 `identity`（overlap 以前頁成功讀回 row 為準），並於 `page` 提交時以 `--assert-post-keys` 執行寫入前 key 預檢；helper 已落地之 observation `.diagnostic.json` 不可原地改寫（詳見 `gui-inventory.md`、`download-and-ledger.md`、`evidence-template.md`）。

## 4. 驗收定義（Definition of Done）與驗證命令

所有實作完成後，於 `<PROJECT_ROOT>` 依序通過以下檢查：

1. **實作前後保護與 Diff 範圍衛生**：
   - **已追蹤與新增檔案檢查**：以 `git diff HEAD --name-status`（同時涵蓋 staged 與 unstaged 已追蹤變更）核對已追蹤異動僅限白名單 6 檔（Slice 1 的 2 檔＋Slice 2 的 4 檔）；以 `git status --short --branch --untracked-files=all` 核對新增未追蹤檔僅限 `docs/plans/20261126-notes-page-key-guard/`；`AGENTS.md`、`docs/LINE相簿備份_使用手冊.md`、`verification-and-recovery.md`、`evidence-decision-cases.md`、`daily.py`、`tests/test_notes_input_helper.py` 均零異動。
   - **受保護／未追蹤／忽略資料之前後唯讀雜湊查核**：於派工前與實作完成後，分別以唯讀腳本對所有受保護路徑（`docs/diagnostics/20261126-notes-daily-page10-key-mismatch/問題提報單.md`、3 個既有未追蹤路徑、`notes-backup-records/`、`backup/`、`.local/line-backup/`）逐檔計算 `(relative_path, sha256)` 並聚合成每路徑單一去識別化總雜湊與檔數（原始路徑清單位於私有查核輸出，絕不寫入公開報告或 commit），比對前後總雜湊完全一致作為「內容零異動」之實證；若任一目錄因故僅做路徑清單與計數核對，則回報結論嚴格限於清單與計數，不超額宣稱內容未變。
   - `git diff HEAD --check`（exit 0）。
   - **隱私檢查**：掃描全部新增／修改之 Git 追蹤檔（含 `docs/plans/20261126-notes-page-key-guard/*.md`），確認不含本機家目錄絕對路徑、真實群組／清單名稱、作者或貼文正文。
2. **文件錨點與規則一致性檢查**：
   - 核對 4 份異動 Skill／references 檔案的所有既有 `##`/`###` 標題與錨點完整保留、交叉連結有效、跨檔無矛盾重試規定，且與 `notes.py` 參數與錯誤碼名稱（`--assert-post-keys`、`INVALID_ASSERT_POST_KEYS`、`PAGE_POST_KEY_MISMATCH`）完全一致。
3. **自動化離線回歸**：
   - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` 與 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes page --help`（exit 0，確認 `--assert-post-keys` 顯示於 `page --help`）。
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_regressions.py`（exit 0，新增 4 組測試含全新未入帳 bundle 零寫入、直接事件／completion 核對、跨輪文字編輯保留 `COMPLETED` 與 `--e` 縮寫回歸全數通過）。
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py`（exit 0，確認 `retry_safe` 契約無回歸）。
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py`（exit 0，確認 `evidence-template.md` 標記與 helper 無回歸）。
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`（exit 0，全量通過）。
   - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`（exit 0，相簿日常紀錄 73 項無回歸）。
4. **獨立審查關卡**：
   - **Plan Review**：由下方 Reviewer pane（`wA:pM`）依 `code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution 審查本計畫，修正所有提出的問題直至取得 `APPROVE`。
   - **Code & Security Review**：Worker1／Worker2 平行實作完成並通過全量離線測試後，將精確 `git diff HEAD` 與驗證輸出提交 Reviewer（`wA:pM`）執行獨立 Code & Security Review，視建議評估是否 replan 並修正直至取得 `APPROVE`。
5. **證據界限聲明**：
   - 本計畫全部驗證屬離線單元／CLI 測試與靜態文件核對；真實 LINE 記事本 GUI、page 10 實機恢復掃描、chooser、`download-check`、跨 Session 恢復與正式 LINE E2E 一律維持 `NOT_RUN`。
