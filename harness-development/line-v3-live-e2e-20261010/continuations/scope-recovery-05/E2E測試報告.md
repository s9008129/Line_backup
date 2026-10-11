# E2E測試報告 — scope-recovery-05／文件發布階段

本輪終點為收據工具修復與 unchanged adapter 離線驗證；實際本階段只完成事故閱讀、基線保全與 Plan／deterministic Handoff 文件。沒有建立 IMPLEMENT runner 或補充 tests，沒有執行產品 syntax/test、LINE input、Save All、chooser confirmation、下載、state/config/ledger mutation。

## 實際工具與順序

1. root 使用 exec_command 唯讀讀取 AGENTS、01/03 prompts、immutable4.8 routing/defaults/schema shape、parent plan/report/incident/ledger、adapter/tests diff 與四份原始收據。
2. 唯讀重算四份原件及 source/state/config hashes；均符合事故紀錄。git log/HEAD/index 查核目前已有事故 checkpoint，index 空；git ls-remote 查到遠端 parent document commit。這是觀察，不是產品 gate。
3. 用固定 Python3.13 -B 盤點既有 tracked/untracked/ignored regular file hashes、symlink targets、nested fixture directory entries；第一次掃描遇到巢狀既有 fixture directory，未寫檔即停止。唯讀確認為目錄後，第二次完整遞迴盤點；這是文件保全機械修正，沒有 product attempt。記錄於 .local/preparation-observations.json。
4. root 只寫 CON 的 baseline、plan、contract、freeze、user decisions、incident reconciliation、check specs、lineage、native blocker、input manifest、deterministic Handoff 及結果。handoff.json 直接複製 plan-contract.json；handoff.md 第一段為接手 prompt，內含完全相同契約。
5. 文件一致性／preservation 的實際結果保存於 .local/document-verification.json。之後由一名指定 GPT-6 luna 唯讀梳理落檔文件與 parent 上下文，返回詳細 commit message；實際 helper actor／結果與 Git 發布另保存於 .local，不在本報告預寫成功。

## 判定與未知

G_BASELINE/G_RUNNER/G_ADAPTER_OFFLINE/G_PRESERVE/G_REPORT 是後續 IMPLEMENT gates，目前 NOT_RUN；文件 hash 保全不當 IMPLEMENT PASS。Parent G_PRESERVE 的四份範圍外寫入仍 FAIL/BLOCKED，原件不搬移／删除／覆寫；Node MODULE_NOT_FOUND 仍不是 adapter syntax 結果。原 scroll 保持 SCROLL_TEST_NOT_RUN；兩本交易與獨立 Acceptance 未執行。

native admission/publication/CONTRACT/RESULT validators NOT_RUN；固定runtime缺失、無stage packet，沒有代替schema validator或invitation。不可將JSON parse/equality/readback稱native schema PASS。OS sandbox/network denial UNKNOWN。

## 证据索引及状態

input-manifest.json 列 parent 原件、prompts、product/runtime 的相對（外部為絕對）／絕對路徑、bytes/hash。incident-reconciliation.json 每筆原件與readback對照。document-manifest.json 列本文件包hash；自身不自引用。baseline.json 指向 CON/.local/preexisting-files.json 與 preexisting-status.z：完整保全大清單保持本 workspace 本地，不假裝遠端已發布。Git收據和publication後保全亦留.local，避免自引用commit hash。

本輪產品/GUI attempt=0；LIVE_CLASSIFIER_CHOOSER 已知原attempt=2，剩餘驗證最多1次，沒有重置。來源與四份收據的新確認讓事故處置和安全續行邊界明確；產品能力尚無新驗證結論。

六狀態見 planner.result.json/handoff.result.json；局部與parent分开記。下一步由Implementer先fresh baseline與runner自測；第一個必要失敗即保留原始證據並交回Planner，不修產品。無可用Planner通道時只準備報告，記錄未交接。

## 文件一致性檢查補記

第一次文件保全比較因 git ls-files 對六個既有 nested fixture repository 目錄保留尾端斜線，而 baseline pathlib 已正規化路徑，產生表示法不同的假 delta。98,513 筆既有內容／類型／mode 核對沒有變更；未新增範圍外資料。root 只在 CON/.local 正規化比較路徑，保留原 script 與錯誤記錄於 .local/document-verification-attempts.json，再重驗文件。此為文件檢查，不消耗產品候選驗證額度，也不能標產品 PASS。

## 2026-10-11 Plan Amendment 01 與 Implementer 開始前盤點

本節是文件階段報告的後續紀錄。此時只完成 Plan／契約修訂和獨立唯讀檢視；runner 尚未編寫、產品檢查尚未執行。G_BASELINE、G_RUNNER、G_ADAPTER_OFFLINE、G_PRESERVE、G_REPORT 仍 NOT_RUN／未完成；plan review 的 PASS 不替代任何實作 gate。

### 實際步驟與順序

1. `exec_command` 唯讀讀取指定 `/Users/hsiaojohnny/.codex/prompts/v4.8.0/04_implement_prompt.md`、專案 `AGENTS.md`、scope-recovery-05 Plan／Handoff／contract／check-specs／incident／lineage／baseline／input manifest／native admission／progress／E2E 報告，以及 parent live-grounding-04 incident/report 和 live-grounding-03 attempt ledger。使用 `rg --files` 找到安裝於 `/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source` 的 immutable routing policy、result schema 和 runtime defaults；沒有啟動舊 controller 或修復 runtime。
2. `git status --short --branch`、`git rev-parse HEAD`、`git symbolic-ref --short HEAD` 和 `git diff --cached --name-status` 顯示 branch `v43-ab/codex-rev28`、index 空、HEAD `f969c817975396bea28e7315dec1a2aec5c6a312`。三名唯讀 collaboration helpers 另外盤點出 11 個既有 tracked 修改、68,483 個 untracked 路徑和 3,753 個 ignored 路徑。這是實作前觀察，不是 G_BASELINE PASS。
3. 原 contract 與 `handoff.json` 的 SHA-256 都是 `6b2076527f343e895f0a9798ffe4c8b85f4e855b2afcdd19d2de168ba1f0f7a0`，原 `max_parallel_read_only_helpers=0`，與使用者新指示衝突。使用者同意先修訂並審查，允許最多 3 名唯讀 helpers，writers 維持 0。
4. 三個平行 read-only subagents `plan_contract_audit`、`workspace_evidence_audit`、`harness_feasibility` 提交了建議；內容摘要保存於 [相對路徑](harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-helper-notes.md)／`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-helper-notes.md`，2,431 bytes，SHA-256 `aa9ae6d0803e9e1cda6d0096fb5ed9fd4faf9340b8ab722d48820ca859f89463`。這些是真實 collaboration 輸出，但沒有 Harness controller actor/session receipt；不當作 native admission、Plan reviewer 或 gate evidence。
5. root 用 `apply_patch` 更新本 CON 的 `plan.md`／`plan-contract.json`／`check-specs.json`，僅改 helper ceiling 與要求的 plan review workflow flag；其他 gates、argv、依賴順序和產品邊界維持不變。更新後 Plan 是 13,567 bytes、SHA-256 `43ebe2d8b940703ff5aa67ccc6f430de5789d976ef6e6776259fe2d85041bea4`；contract 是 2,757 bytes、SHA-256 `18ea97bc6d41171a2460c3979ce9d3f7ca5e7441aaf104aa922ebd8969d297c7`；check specs 是 6,581 bytes、SHA-256 `258a30213850153024b4fc97afe38f28b7ad4382103e2f5c78b1e8859bb30ffb`，其 `contract_sha256` 指向新 contract。
6. 新的獨立唯讀 reviewer `plan_amendment_review` 對修訂版回 PASS，確認 allowed path、五項 IMPLEMENT gates、writers=0、frozen checks 順序及產品／資料邊界均保持；證據見 [相對路徑](harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-review.md)／`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-review.md`，1,490 bytes，SHA-256 `d1d7469a4ba56ae8f62716cabbb7945c3f57c6d6f7e0553cd6d079309ee72bcf`。這是使用者要求的本地 role review，不是 native Harness stage validation。
7. reviewer PASS 後，root 以 `cp plan-contract.json handoff.json` 編譯新 Handoff，使用 read-only Python bytes/hash comparison 確認 `plan-contract.json == handoff.json`，Markdown JSON block 與 contract byte-identical，且 check-spec hash 一致。新 Handoff JSON 2,757 bytes、SHA-256 同 contract；Markdown 7,784 bytes、SHA-256 `5cbd6be4b27688b5d20efe49e793cc5d264cf6011a43733ec0413d52e53924e6`。本地 freeze／copy receipt 分別保存於 `plan-amendment-01-freeze.json`、`compile-handoff-amendment-01.receipt.json`；舊 freeze、handoff receipt、結果和 document manifest 保持原樣。

### 結果、狀態前後與副作用

Plan／契約 helper 衝突已解決，並新增獨立檢視 PASS；這讓下一個有界步驟能按明確 3-helper／0-writer 政策開始。產品能力結論沒有改變。這一階段的預期是只寫現有 CON 內的 plan／handoff／review／helper notes／progress／報告／一致性收據；尚未重算實作 fresh baseline，也沒有寫 runner 或產品檔案。`state/backup_state.json`、config、GUI ledger、239 張既有備份與四份 sibling incident receipts 未由此階段操作；其新鮮 bytes/hash 須由下一步 fresh baseline 再確認。

沒有執行 preflight、runner self-test、Node syntax、Node test suite、Python/Swift suite、LINE UI、Save All、chooser、download 或狀態寫入。沒有新增 product attempt；parent `LIVE_CLASSIFIER_CHOOSER` 仍是 2 次，最多剩第 3 次候選驗證集合。

### 現存未知與下一步

固定 Harness 4.8 Python runtime 不存在，且 `native-admission.json` 沒有 admitted stage packet、invitation、validator command 或 result path；native admission、CONTRACT／RESULT schema validation 仍 NOT_RUN。不得以本地 hash/equality 或下方之後的 Node PASS 宣稱正式 Harness 驗證。collaboration subagents 的實際結果只能作 advisory 輸入；controller-bound helper lifecycle receipts unavailable。

下一步在任何 runner 工具編寫之前，由 Implementer 重做完整 fresh baseline：HEAD/branch/index、tracked/untracked/ignored 清單、regular-file hashes、symlink targets、nested directory entries、四份原件、source/runtime、state/config/ledger 和 backups；若任何既有範圍外內容漂移、不能讀取或類型不明，保留證據並停止。baseline PASS 後才建立 CON runner/self-test；G_RUNNER 任何必要檢查 FAIL 即停止，不跑產品 suite，也不修 adapter。這個 local-only 範圍不需要 LINE 前景交接。

## 2026-10-11 Implementer 執行記錄：G_BASELINE FAIL，後續檢查停止

### 實際結果

本輪在任何 runner、Node 產品檢查或 LINE 操作之前停止。`G_BASELINE=FAIL`；`G_RUNNER=NOT_RUN`、`G_ADAPTER_OFFLINE=NOT_RUN`、`G_PRESERVE=BLOCKED_BY_G_BASELINE_FAIL`。本節是本輪失敗證據，不覆寫前面的文件發布／Plan Amendment 歷史。產品 candidate 驗證 attempt 仍為 0；parent `LIVE_CLASSIFIER_CHOOSER` 仍為 2，本輪最後一次候選驗證額度未使用。

第二次 fresh baseline 掃描遇到 workspace 外部的特殊檔案：`evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo`。唯讀 `lstat` 顯示 mode `0o10644`、`stat.S_ISFIFO=True`、regular file=false、symlink=false、size 欄位 0；沒有開啟或讀取 FIFO。此路徑不在文件階段 `.local/preexisting-files.json`，root Git `ls-files` 無紀錄、path-scoped porcelain 也無項目；因此舊 manifest 並未覆蓋它，不能把舊 manifest 當成完整保全基線。

目前 `implementer_baseline.py` 對所有非 regular／directory／symlink 類型採 fail-closed：

```text
INVENTORY_FAILED: RuntimeError: SPECIAL_FILE: evidence/.../special.fifo: mode=0o10644
```

這是本輪目前可重現的阻塞。`g-baseline.json` 另列出歷史 manifest 路徑缺失 98,513 筆；這是 inventory 在 FIFO 處立即停止、回傳空清單後的連帶比較錯誤，不代表已逐一觀察到那些路徑消失。收據明確記 `inventory_complete=false`、`inventory_count=0`，不能用作成功快照。

### 基線嘗試、修正與命令順序

1. 三名唯讀 helper 平行檢視 amended Plan/check-spec、工作區快照限制與 Harness 可行性；沒有寫檔、執行測試、操作 LINE 或審核 gates。其結果只屬 advisory，無 controller registration。彙整見 `plan-amendment-01-helper-notes.md`（2,431 bytes，SHA-256 `aa9ae6d0803e9e1cda6d0096fb5ed9fd4faf9340b8ab722d48820ca859f89463`）。另一名獨立 reviewer 對 Plan Amendment 01 回 PASS，見 `plan-amendment-01-review.md`（1,490 bytes，SHA-256 `d1d7469a4ba56ae8f62716cabbb7945c3f57c6d6f7e0553cd6d079309ee72bcf`）；這不是 native Harness review。
2. 唯讀確認 amended Plan SHA-256 `43ebe2d8b940703ff5aa67ccc6f430de5789d976ef6e6776259fe2d85041bea4`、contract/handoff.json 相同 SHA `18ea97bc6d41171a2460c3979ce9d3f7ca5e7441aaf104aa922ebd8969d297c7`、check-spec SHA `258a30213850153024b4fc97afe38f28b7ad4382103e2f5c78b1e8859bb30ffb`。三個 IMPLEMENT helper 均核對兩個 Node check IDs、argv、60 秒 timeout、各 stream 1 MiB 限制與 Python/Node executable hashes；無規格 mismatch。
3. root 讀取歷史 manifest/status，並以唯讀 Git 查詢確認當時 branch `v43-ab/codex-rev28`、HEAD `f969c817975396bea28e7315dec1a2aec5c6a312`、index SHA-256 `0fff924ae62f4b209d921464bedf6d0b8f661b1c069c7255584373883a7e261c`、staged paths 空。outside-CON raw Git status 過濾比較與舊 status 相同；這只是一項 Git-status 比較，並不證明完整 filesystem preservation。既有 dirty `tests/test_cua_adapter.mjs` hash 為 `0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd`，沒有修改。
4. root 建立 CON 內的 workspace inventory helper `.local/implementer_baseline.py`。為檢查其語法，執行過固定 Python 3.13 的 `-m py_compile`；它在 CON `.local/__pycache__` 留下編譯檔，沒有寫入 `src/__pycache__` 或 CON 外。後續語法檢視使用 `-B` 的 AST parse。
5. 第一次 baseline 命令：`PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -B /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/implementer_baseline.py baseline`，cwd 為 project root。helper 因 `current_paths` 未定義，在產生 manifest／receipt 前以 exit 1 停止；沒有啟動 child/product command。完整 traceback 文字留在 `.local/implementer-baseline-attempt-01.stderr`（1,049 bytes，SHA-256 `327d40c8511455adcbb6dcd376cfd8e0d08404f96916c7e76c24f5846db1a8ec`）；對應 invocation 為 1,595 bytes，SHA-256 `2bba45fe6ca80c1fcacbcde911e71081d90e3ae1b27321fe9da927799706c032`，stdout 0 bytes，空值 SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。首次失敗只建立了空的 `evidence/` 目錄。
6. root 修正未定義變數並保留第一次錯誤，確認 `evidence/` 仍為真實空目錄、baseline 輸出 ID 不存在後，再執行相同固定命令一次。這次 inventory 在上述 FIFO 停止；helper 以 exit 1 寫出 `evidence/g-baseline.json` FAIL 收據，並保留當時 raw Git status 和不完整的空 manifest。沒有再重跑、沒有刪除或覆寫任何失敗證據，也沒有啟動下一個 gate。
7. root 首次組裝本地 report manifest 時，臨時組檔腳本把 CON 相對的 `plan.md` 錯接到 project root，得到 `FileNotFoundError`；它在任何寫入前停止，沒有建立 manifest。修正路徑基準後再組裝，這不是產品／baseline 重跑，也沒有改變 G_BASELINE FAIL。
8. root 僅對阻塞路徑做唯讀 `lstat`、`git ls-files --error-unmatch`、path-scoped `git status`／`git check-ignore` 與舊 manifest membership 查詢。細節見 `evidence/g-baseline-failure-detail.json`；未讀取 FIFO 內容，未改動該外部 fixture。

### 證據與狀態差異

本地 task package 絕對根目錄為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05`。下表列出本輪關鍵收據的相對／絕對路徑與識別資訊；失敗 evidence 保持唯讀。

| 證據 | 相對路徑 | 絕對路徑 | bytes / SHA-256 |
|---|---|---|---|
| G_BASELINE FAIL 收據 | `evidence/g-baseline.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/evidence/g-baseline.json` | 142531 / `b8837c5dc8aadccf46e24c25d768ed57fa4dde7e7644e5938448b90e67ef464d` |
| FIFO 阻塞詳情 | `evidence/g-baseline-failure-detail.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/evidence/g-baseline-failure-detail.json` | 1680 / `c0ce0019b68df53f72e2b0e6ab2c0e0ac151df2c3dd8e6619c7289ed38a6a005` |
| 不完整清單（空 list） | `.local/implementer-preexisting-files.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/implementer-preexisting-files.json` | 3 / `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| 當時 raw Git status | `.local/implementer-preexisting-status.z` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/implementer-preexisting-status.z` | 11951956 / `9476ae506c9dbf0193544cf76d67ddc891341c2671d5fa3b477c984c47d8fd6d` |
| 第一次 baseline traceback | `.local/implementer-baseline-attempt-01.stderr` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/implementer-baseline-attempt-01.stderr` | 1049 / `327d40c8511455adcbb6dcd376cfd8e0d08404f96916c7e76c24f5846db1a8ec` |
| 第一次 baseline invocation | `.local/implementer-baseline-attempt-01.invocation.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/.local/implementer-baseline-attempt-01.invocation.json` | 1595 / `2bba45fe6ca80c1fcacbcde911e71081d90e3ae1b27321fe9da927799706c032` |
| helpers 彙整 | `plan-amendment-01-helper-notes.md` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-helper-notes.md` | 2431 / `aa9ae6d0803e9e1cda6d0096fb5ed9fd4faf9340b8ab722d48820ca859f89463` |
| Amendment 獨立 review | `plan-amendment-01-review.md` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/plan-amendment-01-review.md` | 1490 / `d1d7469a4ba56ae8f62716cabbb7945c3f57c6d6f7e0553cd6d079309ee72bcf` |

- `evidence/g-baseline.json`：142,531 bytes，SHA-256 `b8837c5dc8aadccf46e24c25d768ed57fa4dde7e7644e5938448b90e67ef464d`；status FAIL，inventory incomplete，0 records。receipt 仍記錄 HEAD/branch/index、固定 Python／Node 真實路徑與 SHA、state/config/GUI ledger、四份事故收據 readback，並盤點 backups 239 個 regular files；這些局部事實不能替代完整基線。
- `evidence/g-baseline-failure-detail.json`：1,680 bytes，SHA-256 `c0ce0019b68df53f72e2b0e6ab2c0e0ac151df2c3dd8e6619c7289ed38a6a005`；包含 FIFO 的 lstat 結果與「不開啟、不移動、不重建」處置。
- `.local/implementer-preexisting-files.json`：3 bytes，SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`，內容只是空 JSON list；它不是完整 manifest。`.local/implementer-preexisting-status.z`：11,951,956 bytes，SHA-256 `9476ae506c9dbf0193544cf76d67ddc891341c2671d5fa3b477c984c47d8fd6d`，是當時 raw Git status，不代表檔案 hash inventory。
- `incident-reconciliation.json` 記錄的四份原始事故 receipts 均由失敗基線 helper readback 並符合原 hash；沒有移動、覆寫或刪除。state、config、GUI ledger 未寫入；backup 內容未寫入。
- 固定 Python 3.13 為 52,640 bytes、SHA-256 `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804`；Node 為 50,320 bytes、SHA-256 `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`。候選 adapter hash `bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2`；既有 test hash仍為上列 dirty hash。這些是基線收據中的讀取值，沒有 syntax/test 結果。

### 沒有執行的項目與後續路由

`runner-preflight-01`、`runner-selftest-01`、`node-adapter-syntax-02`、`node-adapter-tests-01` 全部未執行；沒有 runner/test source 在 `checks/` 寫入。G_RUNNER、G_ADAPTER_OFFLINE 未通過；G_PRESERVE 因沒有完整 fresh baseline 而 BLOCKED，不能宣稱全 workspace 未變。沒有 LINE 前景操作、Save All、chooser、下載、writer／state mutation、commit 或 push。root 沒有可用 native Planner stage channel，因此本報告尚未正式提交 Planner；下一個階段必須先有 reviewed Plan 決定如何只以 lstat metadata 表示並比較這個已知 FIFO，如何處理歷史 manifest 未涵蓋的 filesystem object，並使用不覆寫目前 FAIL receipt 的新 baseline evidence ID。不得自行修改現有 gate 或把本次 G_BASELINE 改寫為 PASS。

文件 Plan §5 保留「當時只實際執行文件發布」的歷史文字；我依 amended Handoff 中「文件發布由前一角色處理」及其明確 Implementer 接手序列，將該段解讀為前一階段紀錄。本輪在任何 runner/adapter 檢查前即停止，因此沒有依賴此解讀執行產品工作。

本地交付索引為 `evidence/report-manifest.json`，本輪格式 3 role result 為 `evidence/implementation-result.json`；兩者只記錄本地觀察與 readback，不能代替 Harness native schema validation。`G_REPORT` 的最終本地判定記於 role result；manifest 不自我引用，避免自引用 hash。
