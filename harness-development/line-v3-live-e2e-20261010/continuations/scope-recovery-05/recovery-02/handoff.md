你是 Recovery 02 的 Implementer。Project root 固定為 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup；唯一可寫 RUNROOT 是該 root 下的 harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02。完整讀取同目錄 plan.md 與本 handoff.md，核對兩份 JSON 契約 block 逐 byte 相同，先只在記憶體擷取，不寫契約或工具。依本文輸入索引讀前輪報告、FAIL 收據、FIFO detail、事故原件及 attempt ledger，辨別文件發布後真實 HEAD/index 與既有 dirty/untracked/ignored 工作，再用 host 建立兩次一致的 namespace/metadata anchor；文件發布清單不是你的 G_BASELINE PASS，不能沿用旧 helper 的 f969c817 EXPECTED_HEAD。anchor 通過後，從 block exclusive materialize plan-contract.json，再逐 byte 複製為 handoff.json，不重排或變更契約；只在 RUNROOT 做有界 bootstrap、新 inventory 工具及 fixture 測試，FIFO 僅 lstat、永不開啟。完整且一致的 fresh baseline 與歷史/bootstrap 核對 PASS 後，才實作固定 root/output 的 runner；host 直接保留 preflight/selftest，G_RUNNER PASS 後只跑一次 unchanged adapter 的固定 Node syntax 與 existing+supplemental suite。全部 check/source/runtime/output 規格依 plan.md 凍結，產品與既有 tests/state/config/backups/ledger 唯讀，舊收據與 cache 原位保留；不操作 LINE、不下載、不換 writer、不修產品、不 commit/push。root 串行、helpers=0、writers=0，不安排獨立審查。兩次 baseline-helper 歷史與 parent LIVE_CLASSIFIER_CHOOSER 已用兩次不重置，本輪各只使用其剩餘一個凍結集合；首個必要失敗停止依賴步驟、保留 raw/partial evidence，不失敗重跑。baseline 已 PASS 時即使後續失敗，仍做独立 preservation/report；baseline 不完整則 G_PRESERVE BLOCKED。每個 gate 只能以自身新證據 PASS，產生完整 E2E測試報告.md、progress.md、format 3 result、manifest 與 attempt ledger 交回 Planner。native Harness 因固定 runtime 失效及無 stage packet 保持 NOT_RUN，不能用本地 JSON/hash/readback 冒充 schema/admission PASS，不能宣稱 parent 兩本交易、實際 scroll 或整體 E2E 完成。

# Recovery 02 精準實作交接

本文件依 `/Users/hsiaojohnny/.codex/prompts/v4.8.0/03_handoff_prompt.md` 保持契約、路徑、checks、owners 與授權一致。該提示是 optional reviewer；使用者明確指示本輪不需要獨立審查，且本契約 `handoff_review_required=false`，故本文件是 deterministic 本地交接，不是獨立審查結果或 native publication。

凍結 Plan：`plan.md` 為 21887 bytes，SHA-256 `6604529c8e9bf06aa59eeb4a0c92358a0b0e7218335d6cd568e8cd4d96bb71bc`。兩份文件的完整契約 block 均為 2811 bytes，SHA-256 `057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a`。接手時先核對這些 bytes/hash；Git 發布不改文件內容，HEAD 發生已授權變更也不能略過文件 hash。

本次使用者只要求 root 落檔兩份文件及發布；目前尚未建立 IMPLEMENT inventory/runner/tests，也未執行 Node 檢查。文件發布所用 GPT-6 luna 子代理只梳理上下文/提交訊息，不是 reviewer，且不授予後續 Implementer helper 或 Git mutation 權限。

## 1. 身分、優先序與實際授權

| 名稱 | 固定值 |
|---|---|
| ROOT | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup |
| CON | harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05 |
| RUNREL | harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02 |
| RUNROOT | ROOT / RUNREL |
| local task | TASK-20261011-line-baseline-recovery-02 |
| lineage | TASK-20261011-line-receipt-recovery → TASK-20261010-line-v3-live-e2e |
| branch（發布前觀察，接手需核對） | v43-ab/codex-rev28 |
| 文件發布前 HEAD | 7ee2f6813ed428eaf4513b7e22a9c91957fcd677 |
| IMPLEMENT 模式 | root 串行；helpers=0、writers=0；network=OFF、browser=false |

讀取 project AGENTS.md 與使用者上層 Harness 契約。使用者核定的新 plan.md/本文控制本輪接手；舊 CON plan/handoff 是唯讀歷史，不能恢復其 helper=3 或覆盖新 RUNROOT。若本文與新 Plan/嵌入 contract 真有矛盾，保存 discrepancy 並停在 Planner，不自行改選範圍或規則。日後必要 schema validation 只能用實際 stage packet 發出的固定命令；目前沒有此 packet。

文件發布允許 root add/commit/normal push 的精確內容只有本 RUNROOT 的 plan.md、handoff.md。其 `.local` 保全、message、publication receipts 不提交；已授權的 HEAD/index 改變需與 receipt/actual Git readback 相符。Implementer 必須新捕獲 Git identity/index，不能拿歷史 f969c817 或 7ee2f681 當發布後常數。沒有 local publication receipt 時，不推定 push/commit 成功；用實際 history 核對或記 UNKNOWN，必要身份不能確認即停止。

## 2. 必讀輸入與可信界線

所有 CON-relative 輸入的絕對路徑都由 ROOT / CON / 下列相對路徑取得；其他輸入從 ROOT 解析。下表 hash 是已讀回的規劃輸入識別資訊，不代表新 IMPLEMENT gates。

| 輸入 | 相對位置 | bytes / SHA-256 或用途 |
|---|---|---|
| 前輪 E2E 報告 | CON/E2E測試報告.md | 21815 / 168dc950512ab10872447840ca7fbe3ab267f34965e52bd5a6f2639794d0bb5d |
| 前輪 G_BASELINE FAIL | CON/evidence/g-baseline.json | 142531 / b8837c5dc8aadccf46e24c25d768ed57fa4dde7e7644e5938448b90e67ef464d |
| FIFO detail | CON/evidence/g-baseline-failure-detail.json | 1680 / c0ce0019b68df53f72e2b0e6ab2c0e0ac151df2c3dd8e6619c7289ed38a6a005 |
| 前輪 format 3 result | CON/evidence/implementation-result.json | 10490 / ce74d1deacb972ef835aa41e1e6b1db43bbfb4280af444261c956ee58731f7ef |
| 前輪報告索引 | CON/evidence/report-manifest.json | 本地 36 個 file refs；native schema NOT_RUN |
| 歷史內容清單 | CON/.local/preexisting-files.json | 98513 records；SHA-256 b115df6ea55e3a985e98651018e742769b02e6f7854989e68f8d7214680832f2 |
| 歷史 Git status | CON/.local/preexisting-status.z | SHA-256 67f7855774654f9f32f635fba5dbc80262b1e72fc950d32df00360a39fa40f04 |
| 事故原件索引 | CON/incident-reconciliation.json | 四份原件 exact paths/bytes/hash；全部原位唯讀 |
| 歷史 Plan/工具/規格 | CON/plan.md、plan-contract.json、handoff.md、check-specs.json、.local/implementer_baseline.py | 理解已有錯誤；不執行或改寫舊 helper |
| lineage/狀態 | CON/lineage.json、native-admission.json、progress.md | parent statuses、attempts、native 缺口 |
| parent 事故 | harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04/scope-incident-001.json | runner 錯位/cwd 与四份原始 receipt；產品 attempt=2 的依據 |
| parent attempt ledger | harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/attempt-ledger.json | 與後續事故合讀，不能只看較舊 attempt=1 就重置 |
| 文件發布本地資料 | RUNROOT/.local/document-publication-baseline.json、document-publication-status.z、document-publication-tracked.diff；後續 actual receipt | 文檔保全，非 G_BASELINE；未提交的大清單可能只存在本 workspace |

必要 local 大清單未帶入下一環境時，記 INPUT_MISSING，停在 bootstrap；不能初始化空歷史或改找其他 root。前輪空 `.local/implementer-preexisting-files.json` 不是 usable baseline。FIFO 的歷史存在／未變無法從 Git 清單證實；mtime、fixture 路徑或舊 census 都不能補造證據。

必須核對的產品/資料來源：

| ROOT-relative path | frozen SHA-256 |
|---|---|
| scripts/line_backup_cua_adapter.mjs | bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2 |
| tests/test_cua_adapter.mjs | 0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd |
| state/backup_state.json | 455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6 |
| config/line_backup_config.json | 5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362 |
| harness-development/line-v3-live-e2e-20261010/gui-ledger.json | 92bab0cf122871b42f3db62af956289b62fbf4e279219766a8850b61f20e135f |

239 個既有 backup regular files 逐檔 hash 與 type 需在 fresh inventory 核對，不僅核對張數。state/config/ledger 與四份 receipt hashes 只能證明那些檔案；不能取代全部 filesystem preservation。

## 3. 精確接手步驟

1. **LOAD／read-only freeze：**完整讀新 Plan/本文與上表；只在記憶體以 bytes 擷取各自唯一 JSON block，確認 equality/hash，不寫契約或工具，不認為 schema 已驗證。準備 Plan 凍結的 check-specs 絕對 argv/cwd/environment/timeout/output/source hashes，以及 bootstrap/new-file/fixture 清單。
2. **Bootstrap anchor → materialize：**任何新契約/工具寫入前 host 兩次 fresh namespace/metadata observation 一致；建立既有 CON hash、Git/index/runtime/source/incident anchor，將文件發布之後的現場納入。通過後才 exclusive materialize plan-contract.json、逐 byte 複製 handoff.json、建立 check-specs，記 exact hashes/readback。既存 RUNROOT plan/handoff/.local 收據保持唯讀。只允許 Plan 授權的 task-local bootstrap additions；原既有 path 不刪改或搬移。
3. **Inventory fixtures：**在 RUNROOT tools/inventory.py 與 checks/test_inventory.py 實作並用 host 固定 Python -B 自測；保留 host invocation/raw streams/receipt。FIFO 實體只在新 fixture 內建立或替換；真實已知 FIFO 永不 open/read/move/recreate。未完成 scan 的 delta 必須 BLOCKED，coverage 與 policy PASS 分開。
4. **G_BASELINE：**兩次完整 inventory/hash/type/entry passes 一致；驗 historical projections、bootstrap delta、source/runtime/incident/state/config/ledger/backup；發新 baseline ID 與 immutable receipt。完整性、receipt PASS、hash與 task/run/tool binding 均成立才能解鎖 runner。
5. **G_RUNNER：**只在 RUNROOT checks/run_command.py/test_run_command.py 建固定 root/guarded bounded runner。host exact-absolute launch --preflight/selftest；所有 fixtures 在新包內且有清單。錯位、symlink、越界、ID collision 副作用前拒絕；正常 invocation reservation 是 exclusive、不可重放，partial receipts 保留。
6. **G_ADAPTER_OFFLINE：**G_RUNNER PASS 後只發一次 node-adapter-syntax-02，PASS 才發一次 node-adapter-tests-01。Node path/hash、argv、cwd=ROOT、TMP roots、60 秒與各 stream 1 MiB 依 Plan，補充 capture test 只能 fake I/O。前後產品/hash不变，無 product repair。
7. **G_PRESERVE：**若 baseline PASS，不論後續測試成功或失敗，都做獨立兩次全量 post inventory。新包外零差異；新包內 exact additions、fixtures、metadata/report changes 有清單；原件/FIFO unchanged。失敗保留 delta 原文，不為通過而更新 baseline。
8. **G_REPORT／交回：**產生實際 E2E測試報告.md、progress.md、format 3 result、manifest、attempt ledger；尾段 publication 使用精確清單/原子 exclusive/readback，記錄驗證窗口與副作用，不形成 receipt 自引用。具備 actual Planner 通道才記交接完成，否則保留包並記尚未交接。

Python path/hash：/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13 / 34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804。

Node path/hash：/opt/homebrew/Cellar/node/26.7.0/bin/node / 1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040。

所有 child check timeout=60 秒、每 stream=1048576 bytes、automatic_retry=false；baseline inventory 總上限=1200 秒且定期回報，不因 timeout 重跑。契約 retry_policy=2/[10,30] 是 Harness 4.8 schema 固定的通用上限，本輪自動重試均禁用，不因此重跑。不得由不受限 subprocess.run 收齊巨量資料後才裁剪。TMPDIR/TMP/TEMP=RUNROOT/tmp；Python -B/PYTHONDONTWRITEBYTECODE=1；GIT_OPTIONAL_LOCKS=0 用於唯讀 Git。固定 exe 失效/hash不同即停止，不替换可用版本。

## 4. Gates、停止條件與報告要求

| Gate | Owner / phase / source | Criticality / role / closure / reuse | 独立新證據（RUNROOT 內） |
|---|---|---|---|
| G_BASELINE | ROLE / IMPLEMENT / ROLE_OBSERVATION | CORE / MUST_NOT_BREAK / HARD_CLEAN / NEVER | evidence/g-baseline-recovery-02.json + complete inventory + baseline-selftest-02 |
| G_RUNNER | ROLE / IMPLEMENT / ROLE_OBSERVATION | CORE / MUST_NOT_BREAK / HARD_CLEAN / NEVER | evidence/g-runner.json + host preflight/selftest receipts |
| G_ADAPTER_OFFLINE | ROLE / IMPLEMENT / ROLE_OBSERVATION | CORE / OUTCOME / HARD_CLEAN / NEVER | evidence/g-adapter-offline.json + two Node receipts |
| G_PRESERVE | ROLE / IMPLEMENT / ROLE_OBSERVATION | CORE / MUST_NOT_BREAK / BASELINE_DELTA / NEVER | evidence/preservation-recovery-02.json + post inventory/delta |
| G_REPORT | ROLE / IMPLEMENT / ROLE_OBSERVATION | SUPPORTING / OUTCOME / HARD_CLEAN / NEVER | E2E測試報告.md、progress.md、evidence/report-manifest.json、evidence/implementation-result.json |

全部 required=true；当前新 gates 未執行。任何前置條件 FAIL 就阻塞依賴 gates。保留 proven implementation/core facts，不以 blocker 抹掉它們；也不把前輪報告 PASS 複製成新報告 gate PASS。

同一 root issue 最多三次、有兩次無新資訊即升級，material blocker 提前停。baseline-helper 兩次歷史已用，本輪恢復集合僅剩一次；LIVE_CLASSIFIER_CHOOSER 兩次歷史已用，本輪產品集合僅剩一次，原 candidate validation=0 不等於 parent 次數為0。文件 QA、Git publication與消息 helper 不算產品嘗試，也不能重置工具或產品額度。未知 dispatch/check 結果保留 UNKNOWN，不重送以獲得乾淨結果。

每項主張需 evidence relative/absolute path、bytes/SHA-256、工具/command、actual step order、預期/實際、前後狀態、副作用、attempt learning/unknown/stop reason。空 streams 保留 bytes=0，不能造一 byte 來符合格式。人眼觀察是 OBSERVED；本地 parse/equality/readback 不是 native schema PASS。沒有 issue claim 回應時不能構造高階審查 analysis_path/validator，沒有 stage packet 不能構造 publication/contract/result驗證命令。

## 5. 六狀態與後續工作

新本地文件交付目前按這些字段記錄：

| 字段 | 文件交付／IMPLEMENT 未開始 | 未來五個本地 gates 真實全 PASS |
|---|---|---|
| PRIMARY_OUTCOME_STATUS | NOT_ACHIEVED | ACHIEVED（僅本地工具與離線目標） |
| IMPLEMENTATION_STATUS | NOT_STARTED | COMPLETE |
| CORE_ACCEPTANCE_STATUS | NOT_RUN | PASS |
| REQUIRED_VERIFICATION_STATUS | INCOMPLETE | INCOMPLETE（native未完成） |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_REQUIRED | NOT_REQUIRED |
| TASK_CLOSURE_STATUS | PENDING_REQUIRED_VERIFICATION | PENDING_REQUIRED_VERIFICATION |

發生 fail/blocker 時按實際 evidence 更新，不能照抄右欄。前輪 G_BASELINE FAIL 仍保留為 FAIL；parent 的 PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED、IMPLEMENTATION_STATUS=BLOCKED、CORE_ACCEPTANCE_STATUS=BLOCKED、REQUIRED_VERIFICATION_STATUS=INCOMPLETE、INDEPENDENT_ACCEPTANCE_STATUS=PENDING、TASK_CLOSURE_STATUS=REPLAN_REQUIRED。

本地結果交 Planner 後，下一輪才有權規劃 LINE 現場：UI/menu、單本交易、實際 0.25-view-height scroll/continuity/new eligible grounding、第二本交易、batch/state、parent independent Acceptance。本輪不需要使用者交还前景，不能跳過 SCROLL_TEST_NOT_RUN 或把重開已驗相簿算第二本。

## 附錄：逐 byte 複製的完整本地 format 3 契約

以下 block 與 plan.md 完全相同；只有 equality/materialization 證據，沒有 native schema/admission PASS。

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
