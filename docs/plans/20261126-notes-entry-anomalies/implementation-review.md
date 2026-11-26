# LINE 記事本入口遺失、輸入通道與證據可重現性異常實作與安全審查紀錄

- 審查日期：2026-11-26（Asia/Taipei）
- 審查候選：分支 `feature/line-notes-media`（基準 HEAD `70c81279d8f9091a9570a7b92bb1a38584c8bb46`），候選工作樹 `git diff` SHA-256 `93869811b2b42467a3eed366fb0f92928b5052e65fc2ad984710641caf2823ba`
- 對應計畫：`docs/plans/20261126-notes-entry-anomalies/plan.md`（v1，SHA-256 `cdbf770f67da111d810d42f8d71cd5ab9f39fd5873c83176b63870d262ca1e19`）
- 審查角色：獨立 Reviewer（Herdr pane `wA:p2`，對 repo 嚴格唯讀審查）
- 審查依據：`code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution（Code Review ＋ Security Review）
- 總指揮官全量回歸實證（同一凍結工作樹）：
  - `git diff --check`：exit 0
  - 6 份 Skill／references `##`/`###` 標題與 `HEAD` 逐檔 `diff`：全數一致（零更動／零遺失）
  - `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help`：exit 0
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py`：69 tests OK（2.359s）
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py`：7 tests OK（0.684s）
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`：393 tests OK（55.112s）
  - `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`：73 tests OK（317.828s）

## Code & Security Review

### Review Verdict: APPROVE
- **Review Type**: Code & Security
- **Core Goal Alignment**: 實作完全服務以同一 Skill 無人值守完成單一記事本備份之核心目標，證據保存 fail-closed 且回報語意收斂，無偏離或新產品行為。
- **Diff / Scope Hygiene**: 僅白名單 7 檔異動共 375 行且 6 檔標題零變更，`src/`、手冊、`AGENTS.md`、問題提報單完全未動，無範圍蔓延或過度工程。

### Findings
None

### Verification Evidence
- `git --no-pager status --short --branch`：僅 7 個追蹤檔修改，與核准計畫白名單一致；未追蹤項僅既有 2 項加 `docs/plans/20261126-notes-entry-anomalies/`，符合 DoD。
- `git --no-pager diff --check` exit 0；`git diff --name-only` 確認 `src/`、`docs/LINE相簿備份_使用手冊.md`、`AGENTS.md`、`docs/diagnostics/20261126-notes-entry-anomalies/問題提報單.md` 零異動；新增行無真實群組名、人名或本機絕對路徑。
- 6 檔 `##`/`###` 標題與 `HEAD` 逐檔 `diff` 全數一致；`BLOCK_MARKERS` 7 項、`cua-initial-observation` 單一 `js` 區塊、`writes==1/2` 與單一 `emitImage` 契約維持。
- Slice 1 `references/evidence-template.md:185-200,249-300,1170-1185,1201-1235` 已讀：`isAxNoChangeStub` 僅前綴錨定加 512 字元與 3 行守衛，後續行禁數字節點，誤判路徑已有正反測試鎖定；`CAPTURE_BOUNDARY` 置於 `PRIVATE_PATHS:OK` 後，早期回傳缺 stage 時入口閘門視為 `MISSING` 而 fail-closed，低階 bare 呼叫維持 `ready/blockers` 相容；`AX:EMPTY` 改以 `trim().length===0` 判定，修補空白字串舊誤判。
- Slice 1 入口閘門僅新增 `nodeRepl.write` 後之唯讀檢查，不新增 `write`，`writes==1` 失敗契約不變；`CAPTURE_BOUNDARY:MISSING` 與 `AX:DIFF_NO_CHANGE` 皆為固定字串拼接，無注入、無 `eval`、無動態執行，正規式皆線性無回溯風險，路徑仍走 `validatePrivatePaths` canonical 子目錄校驗。
- `tests/test_notes_input_helper.py:1259-1480,3577-3600,3650-3700` 5 個新增測試已讀：no-change 保存原件且 `STOP/DOWNLOAD_OBSERVATION_INVALID`、短樹與 JSON 內文不誤判、空白判 `EMPTY`、`RECORDED/MISSING` 四路區分、入口雙閘門 `writes==1` 皆覆蓋正反路徑。
- Slice 2 五檔術語與 Slice 1 完全一致：`CAPTURE_BOUNDARY=RECORDED`、`AX:DIFF_NO_CHANGE(full_tree:false)`、`STALE_CAPTURE_SUSPECTED`、`PARTIAL_AX_ONLY`、`gui_blockers` 與 CLI `dispatch_blockers` 分欄、舊 staging 晚到保留，跨檔引用錨點有效，無規則衝突。
- Reviewer 唯讀實證：`QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py` 69 tests OK；`test_notes_locks.py` 7 tests OK；`git diff --check` exit 0。

## 證據界限
- 以上全部屬離線自動化回歸與靜態核對結果；真實 LINE 記事本 GUI、CUA 實機 `noWindowsAvailable` 重現、window handle reacquire、跨 Session 恢復與正式 LINE E2E 一律維持 `NOT_RUN`。
