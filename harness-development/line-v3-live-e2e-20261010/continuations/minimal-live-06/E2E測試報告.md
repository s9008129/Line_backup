# E2E 測試報告：minimal-live-06 前置保全工具阻塞

本報告記錄本輪實際完成的 bootstrap、唯讀檢查和停止原因。**本輪沒有進行 LINE E2E；沒有任何正式 check ID launch。** 不把程式碼審查、歷史測試或 schema/JSON 讀取寫成 live PASS。

## 目標與計畫版本

目標是依 `plan.md` 完成兩本不同 eligible 相簿的受控備份、實際 release 後 scroll、全檔內容驗證、canonical state/ledger readback 和獨立 Acceptance。本輪預定先完成 `E01 → E02 → B01`，通過 `G_EVIDENCE_POLICY` 與 `G_BASELINE_06` 後才做 D01 真實 CUA raw capture，再進行產品修改與後續測試。

`plan.md` SHA-256：`57090d3af4ea0075b23d40c6733e7e094a757ed3b8f0969e91b48a0f8da94cb8`。
`handoff.md` SHA-256：`22803c91fcbcbfd6943bd46bcfab8e8364a08e6e492fa71e2cbb88fd274ed3eb`。
Appendix A byte-copy（`plan-contract.json` 與 `handoff.json`）：各 6,968 bytes，SHA-256 `e3cbf77f28a093e88188e9a4c9ec22dabbe3e03ca7b12f86f936ffec960811a1`。

## 環境與資料

- Repository root：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
- Prewrite anchor 記錄 branch `v43-ab/codex-rev28`、HEAD `7c191d1e8cccdf13f3043f0da9a367da87b9382b`，當時沒有 staged changes；prewrite metadata anchors 兩份相等。anchor 檔本身 SHA-256 `a3c4160b6eeb8f653f45313bf470fd8db72ffd4a323e9d477395c154a7930e69`。
- `input-manifest.json` 記錄 83 筆既有輸入重新讀取與 hash；`input-reconciliation.json` 記錄 83/83 相符、0 mismatch（該項只證明輸入檔對帳，不證明 G_BASELINE_06）。manifest SHA-256 `4f287f4055ad6891c801eecc5d49551c925ccd3073c1449e16eb6be60ed7fde5`；reconciliation SHA-256 `f9c1dc4299dfc382276a39a7a5ab99101a1a2b34ee54b40645520c14491ba605`。
- 已記錄計畫釘選 Python/Node/Swift/SDK/decoder 的既有 hash 對帳。這些不是本輪 build 或 runtime check。
- 不讀相簿、不建立下載目的地、不寫 state/ledger；沒有呼叫 CUA，也沒有在 LINE 前景輸入。

## 實際步驟與順序

1. 閱讀 `AGENTS.md`、實施 prompt、`plan.md`、`handoff.md`、Appendix A byte-copy、release 的 v3 result schema 和 LINE album skill；核對既有 Git/資料 anchors 和輸入 manifest。沒有清理或 stage 既有 dirty/untracked 工作。
2. 建立 task package 中的 bootstrap/output policy 和前置工具。`checks/run_command.py` 是從 recovery-02 複製到本輪 R 的；目標當時不存在，未觀察到覆寫，但這次沒有 O_EXCL 證據。`tools/inventory_pair.py` 使用 recovery-02 唯讀 scan core，並在 R 寫成新 wrapper。
3. 以 `sed`/`rg`/`nl -ba` 唯讀檢查工具實際常數、比較邏輯和 E01 assertions；用 Python `json.loads` 查看政策／anchor／schema 欄位。對三個存在的 Python 原始碼使用 `compile(source, path, 'exec')` 在記憶體做語法解析；這不是 formal check，也沒有啟動子程序測試。
4. 三個只讀 subagents 平行審閱 Plan 對照、runner/E01 和結果/報告需求。無 agent 寫入、執行 check 或操作 LINE。
5. 發現 runner 仍指向 recovery-02，B01/B02 comparator 不能支持計畫 gate，E01 缺少多個必要 assertions。未 launch E01/E02/B01；依 material blocker 停止產品修改與 D01。
6. 寫入問題提報和唯讀證據。`command-0001.json` 記錄靜態 audit；`command-0002.json` 記錄保護路徑目前讀回與允許產品路徑 diff。兩項各有在 artifact 建立前寫入的 registration。

## 重要原始程式觀察

`checks/run_command.py` 的 task constants 仍是 recovery-02：

```python
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
TASK_ID = "TASK-20261011-line-baseline-recovery-02"
```

`tools/inventory_pair.py` 的 preservation allow-set 僅包含：

```python
allowed_rel = set(policy.get("fixed_files", []))
allowed.update(policy.get("dynamic_registered_paths", []))
```

凍結政策沒有 `dynamic_registered_paths`，而且比較器不解析 policy 的 check/inventory/gate/dynamic/transaction rules。B01 模式只做本次兩次 scan 的 pair equality；它沒有對照 prewrite anchors 或檢查 protected preimages/Git identity。

`checks/test_evidence_policy.py` 的 scan-order fixture 使用同步 stub 和 `published=[]` 記憶體 marker，並沒有實際跑 inventory scan 或延遲 stdout child；unknown-special fixture 未 spy open/read/hash；也沒有測 tail publication、source drift、錯誤 cwd 或未註冊動態輸出拒絕。

完整問題、計畫行號、讀取證據雜湊和要求決策見 `問題提報單.md`。主要工具 hash：`inventory_pair.py` 10,015 bytes／`83d465a64a430f531e11dbc4422fcdbf63c268f222e6dcad226eea5a82510ca3`；`run_command.py` 19,829／`7a99176f828aeb098f0f68a16f470e6685782677386d2a9237b6908a10521cf3`；`test_evidence_policy.py` 8,147／`f684ad61c439b978b35a8a504f2c66f8475a231905ed336d6b20abdcd3d68a89`。

## 計畫檢查與 E2E 結果

| Gate / check | 狀態 | 實際結果 |
|---|---|---|
| E01-evidence-policy / G_EVIDENCE_POLICY | `NOT_RUN` / `BLOCKED` | 正式 ID 未 launch；靜態檢查已發現 E01 fixture 不覆蓋 Plan §7.3 多個必要條件。 |
| E02-runner-selftest | `NOT_RUN` / `BLOCKED` | `checks/test_run_command.py` 不存在；runner 綁錯 R/task。 |
| B01-baseline-pair / G_BASELINE_06 | `NOT_RUN` / `BLOCKED` | pair tool 沒有 anchor reconciliation／protected preimage／Git identity check。 |
| D01-raw-cua / G_REAL_LINK | `NOT_RUN` / `BLOCKED` | 前置 evidence/baseline gate 未過；沒有 CUA capture 或 LINE 操作。 |
| S01-build、R01、N01/N02、P01–P04、S02 / G_OFFLINE | `NOT_RUN` / `BLOCKED` | 前置 D01/G_REAL_LINK 未完成；沒有 build 或產品測試。 |
| G_CATALOG_1、G_MENU_1、G_FIRST | `NOT_RUN` | 沒有操作 LINE、選取相簿或下載。 |
| G_SCROLL、G_CATALOG_2、G_MENU_2、G_SECOND | `NOT_RUN` | 第一本交易未完成，因此未開始 scroll 或第二本交易。 |
| B02-preservation-pair / G_PRESERVE_06 | `NOT_RUN` | 沒有 B01 baseline，且現 comparator 不支援精確 preservation gate。 |
| G_REPORT | `PARTIAL` | 目前 report package 只記錄 material blocker；格式 3 native validation 尚未可用。 |
| G_ACCEPTANCE | `NOT_RUN` | 無 merged product candidate，也無獨立 acceptance review。 |

無 formal check exit code、stdout/stderr、build 結果、CUA capture、相簿指紋或下載結果可報告。任何舊 continuation 的 PASS/FAIL 都未轉成此輪 gate 結果。

## 前後狀態、副作用與保全

目前 `config/line_backup_config.json`、`state/backup_state.json`、`state/.line-backup-state.lock`、共享 `gui-ledger.json` 以及 state/ledger 固定 temp 的目前 lstat identity、bytes、SHA 與兩份 prewrite anchors 相同；核對細節在 `evidence/artifacts/command-0002.json`。9 個核准產品檔案相對 HEAD 的 staged 和 unstaged `git diff --name-only` 都是空集合。沒有刪除、搬移或覆寫既有檔案；本輪新 evidence 僅寫在 R 預定 evidence 路徑。

這項 protected-file readback 不等同完整 workspace inventory，也不能證明 bootstrap delta 完整；不可用來宣稱 G_BASELINE_06 或 G_PRESERVE_06 PASS。

## 嘗試歷史、未知與停止原因

- 產品 root issue `LIVE_CLASSIFIER_CHOOSER` 歷史 3 次已消耗。核准額外 1 個 collection 尚未開始；D01 attempt-start 未寫，所以額外 collection 未消耗。
- 本輪有 1 次具資訊增益的 bootstrap readiness 靜態 audit；沒有對失敗 ID 重試，因為沒有 formal ID launch。
- 仍未知：修正後精確逐檔 policy/runner 是否能通過 E01/E02；完整 B01 是否完成且與 prewrite 對帳；LINE 當下是否有可用非空 ALBUMS 畫面；真實 native/CUA/OCR/geometry 是否能關聯；有無兩本 eligible album；交易和 scroll 是否成功。
- 停止原因：工具缺陷使保全與檢查 gate 不可信；依 Plan 必須先解決政策/runner，再開始 D01。詳情與高階模型的精確裁決問題記錄於 `問題提報單.md`。
- Planner 交接：目前沒有可呼叫的高階 Planner 通道；只將完整報告留在 task package，沒有聲稱已提交。
- Commit/push：未執行。兩本 E2E、必要 gates 和獨立 Acceptance 未完成，使用者要求的「所有任務完成後」條件尚未成立。

## 報告證據定位

本輪 issue、attempt、result、gate receipts 與 report manifest 的 path/bytes/hash 以 `evidence/report-manifest.json` 為準。主要原始證據：

- `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/evidence/artifacts/command-0001.json`，絕對路徑 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/evidence/artifacts/command-0001.json`，6,514 bytes，SHA-256 `e7529fecc6e46fec45b5066824969eebcff1df67336ea133b33619b9ab41aa3f`。
- `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/evidence/artifacts/command-0002.json`，絕對路徑 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/evidence/artifacts/command-0002.json`，3,597 bytes，SHA-256 `cdbe22149586efa3eabd88d6551203cb4fe6ca55082babd5eb80356c7768de18`。
