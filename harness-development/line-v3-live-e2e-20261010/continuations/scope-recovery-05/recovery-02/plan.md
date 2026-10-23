# Recovery 02：修復完整基線、runner 與 adapter 離線驗證

角色：PLANNER。Local task ID：`TASK-20261011-line-baseline-recovery-02`；parent local task：`TASK-20261011-line-receipt-recovery`；parent project task：`TASK-20261010-line-v3-live-e2e`。建立日期：2026-10-11。

Project root（ROOT）：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。

既有 continuation（CON）：`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05`。

唯一新增寫入範圍（RUNREL）：`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02`；RUNROOT 是 ROOT / RUNREL。以下相對路徑除非明示「RUNROOT 內」，皆從 ROOT 解析。

## 1. 根因、授權與完成目標

本輪路由為 `PLANNER_REPLAN`，完成範圍依使用者選擇：**本地工具修復與 unchanged adapter 離線驗證**。採 QUICK：修改限於可逆的 task-local 工具與證據，產品、資料與 LINE 操作保持唯讀。root 串行執行；Plan Review、Handoff Review、獨立 Acceptance 均不要求，IMPLEMENT helpers／writers 設為 0。使用者本輪明確指示「本次不需要獨立審查」。舊 Amendment 01 的 review PASS 與 helper=3 是歷史，不能替代本計畫的新 gates。

根因已由程式與唯讀觀察確認：

- **物件模型不完整。** FIFO 是具名管道，不能當成一般檔案讀取或計算內容 hash；其 size=0 也不表示空檔案。現有 `CON/.local/implementer_baseline.py` 只支援 regular file、directory、symlink。
- **觀察失敗被誤當成不存在。** `inventory()` 中斷後留下空清單，仍進入歷史差異比較，產生 98,513 筆缺失訊息。完整掃描未成立，就沒有判定缺失的依據。
- **歷史清單覆蓋不足。** Git 衍生歷史清單有 170 個目錄；本輪唯讀型別盤點找到 30,131 個目錄及唯一 FIFO。歷史未收錄物件應標記覆蓋缺口，不能直接稱為新增或消失。
- **續行與保全規則不相容。** 現有工具要求 evidence 目錄為空、固定 ID 已被 FAIL 收據占用；保全清單也未涵蓋 runner selftest 的 fixtures。舊 runner 另以目錄層數推算 root，曾造成錯誤 cwd 與四份範圍外寫入。

規劃階段的路徑集合、型別、權限、大小比較，未發現 CON 外歷史檔案差異；這不是完整內容 hash 的 IMPLEMENT 保全 PASS。新鮮工具驗證與產品驗證均未執行。FIFO 內容沒有開啟或讀取。

本次文件交付另獲使用者授權：寫入 `plan.md` 與 `handoff.md` → 一名 GPT-6 luna 唯讀梳理上下文並撰寫含意圖、完成事項、下一步的 commit message → root 明列兩份文件 add、commit、正常 push。此 helper 是文件發布用途，不是 reviewer 或 IMPLEMENT helper。其授權不傳遞成後續 Implementer 的 Git 發布權限。

## 2. 固定範圍、歷史保全與原生限制

所有新 Plan、format 3 contract/check specs、工具、fixtures、raw receipts、報告與結果，都限 RUNROOT。既有 CON 文件、失敗收據、空 manifest、`__pycache__`、四份 sibling 事故收據，以及其他 dirty/untracked/ignored 工作保留原位。產品、既有 tests、state、config、backups、GUI ledger 唯讀；本輪無 LINE UI、下載、writer 替換、狀態遷移或產品修補。

文件發布只提交本 RUNROOT 的 `plan.md`、`handoff.md`。為精確交付這兩個檔案，完整 format 3 機器契約嵌入本文件，並逐 byte 複製到 Handoff 的 JSON block；此階段不另提交 JSON 契約檔。Implementer 接手後只能從 block 提取原 bytes，exclusive 建立 `plan-contract.json`，再逐 byte 複製為 `handoff.json`，不得重新排版或自行變更契約。SHA/readback 只是本地一致性證據，不能冒充 native schema validation。

使用者指定的 `/Users/hsiaojohnny/.codex/prompts/v4.8.0/03_handoff_prompt.md` 是 Optional Handoff Reviewer 規範。依其要求保持 paths、checks、owners、authorization 與契約一致；本契約 `handoff_review_required=false`，故不啟動該角色、不增 gates、不安排獨立審查。

本輪規劃開始時 HEAD 曾為 `f969c817975396bea28e7315dec1a2aec5c6a312`；文件發布前已觀察最新 HEAD 為 `7ee2f6813ed428eaf4513b7e22a9c91957fcd677`，branch 為 `v43-ab/codex-rev28`，staged paths 為空，有 11 個既有 tracked 修改。本次文件 commit 將再改變 HEAD/index；Implementer 必須建立自己的 fresh baseline，核對本次文件發布收據與實際 Git 狀態，不能沿用舊 helper 的 hard-coded EXPECTED_HEAD/index。不能用新基線吸收未經授權的其他漂移。

文件發布的保全清單和 raw Git 資料保存在 RUNROOT `.local/`，只屬文件交付證據，不是 `G_BASELINE`；此階段建立 RUNROOT 與 `.local` 的 namespace 變化是明確授權的文件副作用。Implementer bootstrap 的起點是文件交付後的現場，既有 `plan.md`、`handoff.md` 和 `.local` 收據納入 fresh inventory 並保持唯讀。此後新增子項必須逐項列在 bootstrap/output 清單。

Harness 4.8 固定 runtime `/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3` 是指向不存在 Python 3.14 target 的 symlink。没有有效 issue/stage packet、invitation 或 emitted validation command。native admission、stage publication、CONTRACT／RESULT validation 維持 `NOT_RUN`；不修 global runtime、不改 launcher、不構造替代 validator。OS sandbox 與 network denial enforcement 為 UNKNOWN；本輪工具行為遵守 network=OFF。

## 3. 實作順序、介面與證據

### A. 有界 bootstrap 與盤點器

在新增工具前，host 唯讀取得兩次一致的 filesystem namespace／metadata anchor、既有 CON 檔案 hashes、Git identity／index、固定 executable、產品及事故收據識別資訊。anchor 包含 hidden/ignored/untracked、所有 directory entries、symlink targets 與已知 FIFO metadata，不能只靠 Git 列路徑。先讀文件發布資料並識別授權的兩份文件與 local 收據；保留未可證實的歷史為 UNKNOWN。

Bootstrap 僅允許在 RUNROOT 新增契約、check specs、基線工具、自測與必要資料，逐項記錄前後差異。兩次 anchor 不一致、必要輸入缺失或未核准範圍漂移即停止。這解開「必須先用失效掃描器建立基線，才能修掃描器」的循環；不能擴成任意 pre-baseline 寫入。語法檢查使用 AST parse，Python 一律 `-B`／`PYTHONDONTWRITEBYTECODE=1`，不使用會寫 cache 的 py_compile。

新工具放 RUNROOT `tools/inventory.py`，保留 `baseline|preservation` CLI，ROOT/RUNROOT 固定，不接受任意根或輸出路徑。盤點格式使用自身 version 欄位，不更動產品 state schema：

- filesystem 全量遞迴；包含 hidden、ignored、untracked、空目錄、nested fixture repositories。只排除 ROOT `.git` 內容，Git identity/index 另行保全。
- 不跟隨 symlink；記錄 target。目錄記錄排序後 entries；regular file 記錄 bytes/SHA-256。正規化相對路徑，拒絕 duplicate、越界或不明 identity。
- 唯一 allowlisted FIFO 是 `evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo`。只 `lstat`，記錄 path/type/dev/ino/mode/uid/gid/nlink/mtime_ns/ctime_ns；`content_read=false`、`content_hash=null`。已知路徑型別改變立即 FAIL，永不開啟該路徑。
- 未核准特殊物件只保留 metadata 並阻塞，不能開啟內容。完整枚舉與 policy PASS 分開表示；能記錄某物件不代表准許通過。
- fd-relative、不跟隨 symlink；regular file 使用非阻塞開啟，`fstat` 確認仍為相同 regular object 後才讀取；前後 metadata、bytes 不一致即 FAIL。一般物件 metadata 保留在 record；atime 不參與一致性，讀取可改變它。
- 回傳 records、complete、errors、coverage、start/end；未完成或不穩定掃描保留 partial inventory，不能作 usable baseline。下游 delta 判定 BLOCKED，不產生缺失結論，也不補掃洗成 PASS。

歷史比較僅投影到舊紀錄確實具備的欄位，regular hash、symlink target/hash、mode 與已記錄 directory entries 仍需一致。舊 manifest 未涵蓋的目錄和 FIFO 記為 `HISTORICAL_COVERAGE_GAP`；其歷史存在／不變不能追認，從新完整快照起建立後續保全。Git porcelain v1 -z 要正確處理 rename/copy 的雙路徑，不能用單純 NUL split/filter 丟失關聯。

Bootstrap anchor 必須在 contract/check-spec/tool 的新增寫入之前取得；可以先讀取與在記憶體擷取契約。anchor 通過後才 materialize 契約及工具。先用 host 固定 Python 留存 RUNROOT `checks/test_inventory.py` 的 fixture 自測；通過才進行兩次一致的完整 hash/type/entry inventory、歷史內容核對與 bootstrap delta 核對。以新的 `E_BASELINE_RECOVERY_02`／`evidence/g-baseline-recovery-02.json` 發布；不覆寫舊 FAIL。consumer 必須核對 receipt PASS、complete、inventory bytes/hash、task/run/contract/tool binding 後才能使用。新增輸出 exclusive creation、flush/fsync、readback；ID 碰撞立即拒絕。

### B. 固定 root 的 runner

新 runner 放 RUNROOT `checks/run_command.py`，CLI 為 `CHECK_ID -- COMMAND [ARG ...]` 和 `--preflight`。不得用 `parents[n]` 推算 root；固定 ROOT、RUNROOT、`evidence`、`tmp` 絕對路徑。自身位置、contract/check-spec hashes、ancestor/symlink、輸出 scope 與 ID 衝突必須在 mkdir/write/launch 前確認。使用 anchored directory FD 發布，避免父路徑替換造成逃逸。`--preflight` 不寫檔、不啟動 child，只回傳觀察；host 直接留存輸出，pending runner 不認證自身。

固定 Python 為 `/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13`，SHA-256 `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804`。固定 Node 為 `/opt/homebrew/Cellar/node/26.7.0/bin/node`，SHA-256 `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`。執行前核對 realpath/hash；維持普通 environment，不能 repurpose HOME/CODEX_HOME。

檢查命令與順序凍結為：

| Check | Launcher / argv（SCRIPT 是 RUNROOT 對應檔案的絕對路徑） | 證據 stem（RUNROOT 內） |
|---|---|---|
| baseline-selftest-02 | host：固定 Python `-B SCRIPT(checks/test_inventory.py)` | evidence/baseline-selftest-02 |
| runner-preflight-01 | host：固定 Python `-B SCRIPT(checks/run_command.py) --preflight` | evidence/runner-preflight-01 |
| runner-selftest-01 | host：固定 Python `-B SCRIPT(checks/test_run_command.py)` | evidence/runner-selftest-01 |
| node-adapter-syntax-02 | verified runner：固定 Node `--check scripts/line_backup_cua_adapter.mjs` | evidence/node-adapter-syntax-02 |
| node-adapter-tests-01 | verified runner：固定 Node `--test tests/test_cua_adapter.mjs RUNREL/checks/test_capture_regression.mjs`（RUNREL 展開為本文件固定字串） | evidence/node-adapter-tests-01 |

baseline selftest 通過 → G_BASELINE PASS → host preflight/selftest → G_RUNNER PASS → Node syntax → Node existing+supplemental suite → preservation → 報告/結果。每個 check 固定 child cwd=ROOT、shell=False、60 秒 timeout、每條 stdout/stderr 1 MiB，automatic_retry=false。host 執行使用確切 executable/argv，並自行保留 invocation/raw output/receipt；Node checks 只可由已驗 runner 執行。全量 workspace inventory 是單獨讀取步驟，凍結 1200 秒總上限，不套用 child-check 的 60 秒；poll/使用者更新間隔不超過 60 秒，timeout 保留 partial 並停止，不重跑。

機器契約的 retry_policy 保留 Harness 4.8 task schema 固定值 2／[10,30]，作為通用上限；本輪 check-specs 與 inventory 行為一律 automatic_retry=false，且第一個必要失敗即停。此固定欄位不是使用重試額度的要求，也不授權重跑本輪集合。

超時/超限須終止並回收 child process group，保存已收到的 bytes、limit/timeout reason、incomplete streams，判定 FAIL；不能把截斷輸出標為完整或 PASS。receipt 包含 exact argv、cwd、environment、source/runtime/tool hash、UTC/monotonic start/end、exit/timeout、raw output bytes/hash/readback；exit 0 且完整證據一致才 PASS。TMPDIR/TMP/TEMP 固定 RUNROOT/tmp。

runner selftest 資料與純測試 context 限 RUNROOT/fixtures；production CLI 不能接受 test override 或任意新增 check ID。先凍結 test fixture/output 清單；失敗資料保留，不自動清理重跑。任何 fixture 清理只可針對本次建立、identity 核對一致且明列的物件，並記錄刪除；不可清理既有資料。

### C. Unchanged adapter 與 post-run 保全

產品 adapter 固定 SHA-256 `bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2`；既有 dirty test 固定 `0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd`。`G_RUNNER=PASS` 後只執行上述一次 syntax 與一次完整 existing+supplemental Node suite。補充測試只用 fake I/O，不載入真實 App/SDK、bridge/UI/state writer。

最後用兩次一致的新完整 inventory 比較 fresh baseline：RUNROOT 外零差異；RUNROOT 內只接受事前凍結的新增檔案、fixtures、output 清單及當輪報告/progress 明列變更。既有文檔/收據/source 保持 hash 不變，directory entry delta 逐項檢查，不能用整個 evidence/fixtures 目錄豁免。FIFO stable metadata、Git identity/index、四份原件、產品/state/config/ledger/backups 均需一致；read-induced atime 不作差異。

報告、結果與索引結尾發布採精確清單和逐檔 exclusive/readback；保全收據記錄 scan 區間與此尾段寫入，避免自引用與未記錄發布。若保全後仍有需要驗證的來源改動，前一 receipt 失效，保存原因交 Planner，不能默認放行。

## 4. 回歸測試與 gates

必要測試：

- FIFO metadata 掃描不呼叫 open/read；fixture FIFO 移除、替換、chmod 時 preservation FAIL。st_size=0 不走 zero-byte regular 邏輯。
- 中途 exception、不可讀物件、metadata 漂移、兩次 scan 不同：保留 partial，delta BLOCKED，下游不執行；不出現連帶歷史缺失判定。
- hidden/ignored/空目錄/nested directories、symlink 不跟隨、歷史 coverage gap、path normalization/duplicate；未知 special object 阻塞。
- regular→FIFO 競態不阻塞；fstat 未證實 regular identity 前無內容 read。
- runner 錯置、ancestor symlink、越界、既存 ID：副作用前拒絕；不同 caller cwd 仍固定 child cwd；timeout/stream limit/nonzero exit/process-group cleanup/exclusive output/relative+absolute refs/hash/readback。
- 兩條 capture 入口：foreign-realm Uint8Array、Buffer subarray offset、copy/hash、DataView/其他 typed array/空值/>16 MiB 拒絕、UTC/monotonic interval；retain/classify 耗時不刷新五秒 freshness；無效 screenshot/AX refs、bytes/hash mismatch、retain failure 在 classify/動作前拒絕。保留 existing suite 的 dispatch/chooser/SCK/quota 回歸。

| Gate | 明確 PASS 所需證據（RUNROOT 內） | Criticality / evidence role / closure |
|---|---|---|
| G_BASELINE | evidence/g-baseline-recovery-02.json：tool fixture PASS、兩次完整快照一致、historical/bootstrap 核對、FIFO 未開啟 | CORE / MUST_NOT_BREAK / HARD_CLEAN |
| G_RUNNER | evidence/g-runner.json：host preflight/selftest、raw receipts、guards/process bounds/readback | CORE / MUST_NOT_BREAK / HARD_CLEAN |
| G_ADAPTER_OFFLINE | evidence/g-adapter-offline.json：unchanged hashes、syntax 與完整 suite 實際 PASS | CORE / OUTCOME / HARD_CLEAN |
| G_PRESERVE | evidence/preservation-recovery-02.json：新包外零差異、新包內核准變更、FIFO 與原件一致 | CORE / MUST_NOT_BREAK / BASELINE_DELTA |
| G_REPORT | E2E測試報告.md、progress.md、evidence/report-manifest.json、evidence/implementation-result.json：完整實際記錄與 readback | SUPPORTING / OUTCOME / HARD_CLEAN |

五項 gate 均 required=true、owner=ROLE、phase=IMPLEMENT、evidence_source=ROLE_OBSERVATION、reuse=NEVER；保留原 metadata 政策。文檔一致性、型別 census 或人眼 OBSERVED 不代替 gate PASS。

## 5. 嘗試限制、停止、報告與六狀態

兩次 baseline-helper 嘗試完整繼承：01 是 NameError；02 發現 FIFO 並保留 FAIL。本輪只允許一個凍結的恢復驗證集合，保守沿用第三次剩餘額度；不因新 task/run/root 重置。產品 candidate attempt=0；parent LIVE_CLASSIFIER_CHOOSER 已用兩次，本輪最多一個剩餘第三次集合，在首次 Node candidate launch 時記錄 consumed。工具 fixture/盤點與產品集合分開記，不挪用其他 root issue 額度。未知舊 ledger 保留 UNKNOWN。

第一個必要 failure、scope side effect、identity ambiguity 或 baseline drift：保存 raw error/partial/前後狀態，停止依賴步驟，不改產品、不失敗重跑、不另換 writer或降低 gate。若 G_BASELINE 已 PASS，後續 check FAIL 仍做獨立 preservation/report；若 baseline 不完整，G_PRESERVE BLOCKED，僅記局部可證事實。兩次連續無新資訊或 material blocker 按 Harness 規則升級/提前停止。

交付 E2E測試報告.md、progress.md、format 3 implementation result、attempt ledger、evidence manifest，記 exact 命令/順序/環境/程式片段、前後差異、副作用、失敗與未執行、資訊增益/未知/停止原因；關鍵主張需相對及絕對路徑、bytes/hash/readback。空 stdout/stderr 如實 bytes=0。報告交回 Planner；無實際通道就記未交接。

本次文件交付不是 IMPLEMENT。新五 gates 尚未執行；前輪 G_BASELINE=FAIL、G_RUNNER/G_ADAPTER_OFFLINE=NOT_RUN、G_PRESERVE=BLOCKED、G_REPORT=本地 PASS 保持歷史。新本地六狀態目前為 NOT_ACHIEVED / NOT_STARTED / NOT_RUN / INCOMPLETE / NOT_REQUIRED / PENDING_REQUIRED_VERIFICATION（依下列字段順序）。

本地五 gates 全 PASS 後可記：PRIMARY_OUTCOME_STATUS=ACHIEVED（只指本地目標）、IMPLEMENTATION_STATUS=COMPLETE、CORE_ACCEPTANCE_STATUS=PASS、REQUIRED_VERIFICATION_STATUS=INCOMPLETE、INDEPENDENT_ACCEPTANCE_STATUS=NOT_REQUIRED、TASK_CLOSURE_STATUS=PENDING_REQUIRED_VERIFICATION。native NOT_RUN 不消失。

parent 狀態保持 NOT_ACHIEVED / BLOCKED / BLOCKED / INCOMPLETE / PENDING / REPLAN_REQUIRED。兩本交易、實際 bounded scroll（SCROLL_TEST_NOT_RUN）、grounding、整體 batch/state 與 parent 獨立 Acceptance 未因本地成功完成；另交下一輪 Planner。

## 附錄：完整 format 3 本地機器契約

此 block 是交接與日後 materialization 的唯一契約來源。沒有 native stage publication/schema PASS。Handoff 複製包括縮排、key order 和末尾換行的完整 bytes。Block 長度為 2811 bytes，SHA-256 為 `057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a`。

```json
{
  "format_version": "3",
  "task_id": "TASK-20261011-line-baseline-recovery-02",
  "goal": "Repair the task-local complete filesystem baseline and fixed-root check runner, preserve all historical evidence and unrelated work, verify the unchanged CUA adapter once offline, and report to Planner without LINE input, downloads, product/state/config/ledger edits or parent E2E closure.",
  "task_class": "QUICK",
  "allowed_paths": [
    "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02"
  ],
  "required_evidence": [
    "E_BOOTSTRAP",
    "E_BASELINE_RECOVERY_02",
    "E_INCIDENT_RECONCILIATION",
    "E_RUNNER",
    "E_ADAPTER_OFFLINE",
    "E_PRESERVATION_RECOVERY_02",
    "E_REPORT"
  ],
  "gate_specs": [
    {
      "gate_id": "G_BASELINE",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_RUNNER",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_ADAPTER_OFFLINE",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_PRESERVE",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "BASELINE_DELTA",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_REPORT",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    }
  ],
  "capability_policy": {
    "network": "OFF",
    "browser": false,
    "destinations": []
  },
  "retry_policy": {
    "transient_read_only_retries": 2,
    "delays_seconds": [
      10,
      30
    ]
  },
  "resource_policy": {
    "prompt_bytes": 65536,
    "state_bytes": 524288,
    "inspect_bytes": 16384,
    "log_bytes": 134217728
  },
  "workflow_policy": {
    "plan_review_required": false,
    "independent_acceptance_required": false,
    "max_parallel_read_only_helpers": 0,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
