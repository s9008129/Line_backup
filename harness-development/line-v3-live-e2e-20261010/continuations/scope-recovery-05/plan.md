# scope-recovery-05：保留事故證據、修復收據工具並驗證 adapter

Task：TASK-20261011-line-receipt-recovery；parent task：TASK-20261010-line-v3-live-e2e。角色：PLANNER。
Project root 固定為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
CON 固定為 `harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05`。所有相對路徑從 project root 解析。

## 1. 目標、現況與授權

使用者選定本輪止於「工具修復與 adapter 驗證」：保留四份範圍外收據原件，修復本地檢查工具，完成目前候選 adapter 的離線驗證，產生報告交回 Planner。本輪分類 QUICK，因產品維持唯讀，修改限於可逆的本地檢查工具與證據包；不繼承 parent 真實下載流程的 CRITICAL 執行範圍。

本計画不需要獨立 Plan Review 或 Handoff Review。parent 的兩本 E2E 與獨立 Acceptance 要求完整保留，本輪局部恢復不要求獨立 Acceptance。Implementation workflow 的 helper/writer 上限均為 0，root 串行。

使用者另已明確授權本次「計畫與交接文件落檔 → 一名 GPT-6 luna 唯讀梳理上下文並撰寫詳細提交訊息 → add、commit、正常 push」。這是文件交付階段的獨立授權：helper 不審查、不改 Plan、不寫檔、不執行產品、GUI 或 Git mutation。此文件階段的一名 helper 不改變後續 IMPLEMENT 的 0-helper/0-writer 契約。

現況 HEAD 為 `3d8539a8447a3bfee08f493c4d2322772422c5d3`，branch 為 `v43-ab/codex-rev28`，index 空。該 HEAD 已提交候選 adapter 與事故文件；`tests/test_cua_adapter.mjs` 仍含既有未提交修改。四份事故原件、adapter、tests、state/config 與事故記錄的 hash 已唯讀核對一致；這不代表產品 syntax/test PASS。State revision 35、2 VERIFIED，state hash `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`，config hash `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`。Backup 目前列出 239 個 regular files；本文件階段的內容 hash 保全不是照片解碼／完整下載 E2E 驗收。

本次發布前遠端 `origin/v43-ab/codex-rev28` 為 `b06b47b717da1aa9ae63e70d6d86c24d34282bba`，正常 push 將一併送出既有事故 checkpoint `3d8539a` 和新的文件提交。新 commit 只包含本 CON 的明列文件；不得 stage 既有 dirty/untracked 工作、產品測試或四份範圍外原件。

## 2. 邊界、保全與工具介面

唯一可寫路徑是完整 CON 目錄。adapter、既有 tests、state/config、backups、GUI ledger、舊 continuations、global Harness/runtime/release 與外部 bridge 全部唯讀。不操作 LINE、不下載、不換 writer、不 migrate、不修改 gate 或產品 API。

四份事故收據依 `live-grounding-04/scope-incident-001.json` 的 `out_of_scope_artifacts` 原位保留，不能搬移、删除、覆寫或重新封裝成成功。CON 新增 `incident-reconciliation.json`，保存原始相對／絕對路徑、bytes、SHA-256 及唯讀 readback。舊 G_PRESERVE 保持 FAIL/BLOCKED；新的 preservation 只判定新 baseline 之後的 delta。

Implementer 在任何工具實作前建立自己的 fresh baseline，不能直接把文件階段 baseline 當 G_BASELINE PASS。保存 HEAD/branch/index、dirty/untracked/ignored 清單、regular file hashes、symlink targets、nested fixture directory 清單、歷史證據、state/config/ledger 與 backup 逐檔 hash。不能讀取、類型不明或盤點中漂移即停止。不得 reset、checkout、clean、整批 stage 或清理既有資料。

在 `CON/checks/run_command.py` 實作唯一新 runner。固定 REPO_ROOT、CON 與 evidence 絕對位置；禁止以 `parents[n]` 推算或接受任意輸出根。保持 `CHECK_ID -- COMMAND [ARG ...]` 介面，新增不寫檔、不啟動子程序的 `--preflight`。命令限定 `check-specs.json` 的本輪檢查 ID 與 argv。

任何 mkdir、receipt write 或 subprocess 之前，核對自身真實位置必為 `CON/checks/run_command.py`、project root、輸出 realpath/ancestor/symlink 與 receipt 檔名衝突。錯置、越界、symlink 或已存在的 ID 立即拒絕，不發生寫入或 child launch。使用 exclusive creation 保留原收據；產生不完整新收據時保留現場，不自行清理重跑。

固定 cwd 為 project root，使用 argv array、shell=False、60 秒 timeout、每條 stdout/stderr 流最多 1 MiB；超時／超限停止子程序並記錄 FAIL 與 incomplete streams，不能靠截斷資料標 PASS。記錄工具/source/runtime hash、argv、cwd、environment、開始／結束 UTC、exit/timeout、原始輸出 bytes/hash 與 readback。PASS 需要 exit 0、完整且一致的留存。TMPDIR/TMP/TEMP 全部在 CON/tmp，Python 使用 -B 與 PYTHONDONTWRITEBYTECODE=1；不得產生 src/__pycache__ 或舊 TP/evidence 副作用。

## 3. 凍結檢查、gates 與證據

`check-specs.json` 凍結實際 executable、argv、cwd、environment、證據輸出及依賴順序。Python 固定為 `/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13`，SHA-256 `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804`；Node 固定為 `/opt/homebrew/Cellar/node/26.7.0/bin/node`，SHA-256 `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`。執行前核對 realpath/hash，不以失效 Python3.14 launcher 啟動。

順序：fresh baseline → host 以明確絕對路徑留存 --preflight 及 runner 自測輸出 → G_RUNNER 通過 → Node adapter syntax → 既有全套 adapter tests 與 CON 補充 capture tests → preservation → 完整報告。host bootstrap 不用待驗 runner 認證自身；原始 tool invocation/output 由 root 直接保存於 CON/evidence。第一個必要檢查失敗即停止依賴步驟，不擴大或反覆跑 suites。

G_RUNNER 自測包含：呼叫 cwd 改變仍綁固定 root；工具錯置、越界、symlink、既存 ID 在副作用前拒絕；timeout、輸出上限、child exit、exclusive receipt、relative/absolute refs、hash/readback。錯置測試副本與測試資料限 CON/fixtures，不觸碰舊 runner 或 sibling evidence。

產品命令僅為 Node --check scripts/line_backup_cua_adapter.mjs，以及 Node --test tests/test_cua_adapter.mjs CON/checks/test_capture_regression.mjs。補充測試全部在 CON，使用 fake I/O；不載入真實 App/SDK、不觸發 bridge/UI、不呼叫 state writer。涵蓋跨 realm Uint8Array、Buffer subarray offset、copy/hash、DataView/其他 typed array/空值/>16 MiB 拒絕、兩條 capture 入口、UTC/monotonic interval、retain/classify 耗時不刷新五秒 freshness、無效 screenshot/AX refs、bytes/hash mismatch 與 retain failure 在 classify/動作之前拒絕。保留既有 suite 的一次性 dispatch、chooser、SCK、quota 等回歸。

原 Python/Swift/full-live suites 本輪不執行，也不因本輪 Node PASS 改寫原 G_OFFLINE、G_AUTH、G_MIGRATION 或 live gate 為 PASS。

| Gate | 必要输出／明確 PASS 條件 | Criticality / evidence role / closure | 失敗路由 |
|---|---|---|---|
| G_BASELINE | evidence/g-baseline.json；fresh 完整基線、原件與 runtime/source hash 一致 | CORE / MUST_NOT_BREAK / HARD_CLEAN | 停止並保存精確漂移 |
| G_RUNNER | evidence/g-runner.json；host bootstrap、自測與每份 raw receipt/readback | CORE / MUST_NOT_BREAK / HARD_CLEAN | 停止；不啟動產品檢查 |
| G_ADAPTER_OFFLINE | evidence/g-adapter-offline.json；syntax 與完整既有＋補充 suite 實際 PASS | CORE / OUTCOME / HARD_CLEAN | 保存 failure，交回 Planner；不改產品 |
| G_PRESERVE | evidence/preservation.json；新寫入只在 CON，所有其他基線資料保持 | CORE / MUST_NOT_BREAK / BASELINE_DELTA | 保留原件、立即停止 |
| G_REPORT | E2E測試報告.md＋evidence/report-manifest.json；完整實際步驟／結果／限制／refs | SUPPORTING / OUTCOME / HARD_CLEAN | 缺證據維持 PARTIAL |

全部 gates 為 required=true、ROLE/IMPLEMENT、ROLE_OBSERVATION、reuse=NEVER。每個 gate 有自身明確 PASS 和實際可重驗證據，才可記本地驗證通過。文件一致性或人眼 OBSERVED 不能代替產品 gate PASS。

## 4. 嘗試限制與交接

沿用原 ledger 及事故記錄，不因新 task/CON 重置 root issue。LIVE_CLASSIFIER_CHOOSER 已記 attempt 1 與本次停止的 attempt 2；本輪候選驗證最多使用剩餘第 3 次有證據嘗試，包含一個凍結檢查集合，不失敗重跑、不修補產品。receipt 工具根因與修復另行保存但不能重置產品額度。未知歷史保留 UNKNOWN；其他 root issue 的額度不挪用。同一 root issue 的 3/2 規則及 material blocker 提前停止保持。

Implementer 每輪保存 E2E測試報告.md、progress.md、format3 result 與 evidence manifest，列命令/程式片段、環境、步驟順序、前後狀態、副作用、失敗/未執行、attempt history、新資訊與停止原因。所有关键主張引用相對／絕對路徑、bytes/hash；raw stdout 即使空檔也如實保存 bytes=0，result manifest 可引用非空 receipt，不偽造空檔長度。

完成本地驗證或任何阻塞後，準備報告交回 Planner；沒有實際通道就記未交接。本輪沒有 LINE 相簿列表或前景交接需求。原 G_SCROLL=SCROLL_TEST_NOT_RUN、两本交易及整體批次驗收維持未完成，下一步需另行規劃。

## 5. 文件發布、native 限制與六狀態

本次只實際執行文件發布，不建立 IMPLEMENT runner/test、不執行候選產品檢查。文件順序：plan.md＋format3 plan-contract.json → 精確 hash freeze → deterministic handoff.json 逐 byte 複製契約 → handoff.md 開頭精準接手 prompt＋完整原契約 → JSON/readback/hash/preservation 檢查 → 一名指定 GPT-6 luna 唯讀上下文／提交訊息 → root 明列文件 add/commit/正常 push → 實際 Git 收據及遠端 readback。

03_handoff_prompt.md 是 optional Reviewer 規範；本輪 handoff_review_required=false，不啟動該角色、不添 gate、不改 contract、不把 commit-message helper 當 Reviewer。詳細提交訊息使用 CON/.local/commit-message.txt 及 git commit -F；不以 shell substitution 傳正文。

發布時只 stage document-files.json 所列本 CON 文件。原件、產品測試、保全大清單、local helper scratch 和未來 implementation artifacts 不提交。Git 操作是本次使用者另授權的文件交付行為；後續 Implementer 的契約不授權 commit/push。push 到 origin 的 v43-ab/codex-rev28，禁止 force、rewrite 或整批 stage。遠端若出現競爭或未預期拒絕，保留收據並停止，不自行 merge/rebase。

原固定 Harness4.8 runtime `/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3` 仍失效，沒有 native invitation/stage packet。本次不修 global runtime、不啟動替代 validator、不造 invitation。native admission/publication/CONTRACT/RESULT validation 都為 NOT_RUN。JSON parse、bytes/hash/equality/readback 只屬 document consistency，不是 JSON Schema PASS、native admission 或 OS/network enforcement。

六狀態按本地 continuation 與 parent 兩組分開呈現。本次文件交付的本地狀態：PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED、IMPLEMENTATION_STATUS=NOT_STARTED、CORE_ACCEPTANCE_STATUS=NOT_RUN、REQUIRED_VERIFICATION_STATUS=INCOMPLETE、INDEPENDENT_ACCEPTANCE_STATUS=NOT_REQUIRED、TASK_CLOSURE_STATUS=PENDING_REQUIRED_VERIFICATION。日後本地 gates 全 PASS 也需保留正式 native verification 未完成；parent goal 仍 NOT_ACHIEVED、獨立 Acceptance PENDING，不能宣稱整體 DONE。

baseline.json 及 input-manifest.json 公布來源識別資訊；約 98,513 筆既有檔案的完整保全 manifest 與 raw Git status 保留於 CON/.local，屬本 workspace 本地證據，不假裝已隨遠端文件包發布。Git 發布後產生的收據亦保留於 .local，以避免自引用 commit hash。
