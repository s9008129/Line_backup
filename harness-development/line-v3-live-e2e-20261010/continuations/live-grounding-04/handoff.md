你是本輪 Implementer。Project root 固定為 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup；CON 固定為 harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04。先讀本目錄 plan.md、plan-contract.json、handoff.json、research.md、research-facts.json、input-manifest.json、baseline.json、native-admission.json，以及原 live-grounding-03 的 E2E測試報告.md與attempt-ledger.json。核對HEAD後繼、dirty bytes、state/config/runtime與既有嘗試額度；不要reset既有工作。依凍結契約修復cross-realm CUA bytes、repo自有passive native context、v2視覺／AX證據、production callbacks、boundary keys、intersectionPx與phase-specific chooser。唯一GUI輸入是documented CUA API；唯一交易writer是現有schema3 batch service。先完成必要隔離離線驗證與新source/runtime/producer/grants凍結，再取得有效前景交接、確認可行版面，依序完成第一本VERIFIED/readback/release、實際≤0.25-view-height scroll的fresh完整overlap與新完整候選、不同第二本完整交易及獨立Acceptance。任何身份、焦點、native權限、freshness、目的地、writer或派送結果不明就停止依賴工作；保存intent barrier與最小重現，禁止重送Save All／confirmation、另換writer或降低gate。舊contract/證據保持原件，舊PASS不能認證新candidate。每輪保存raw artifacts、bytes/hash/readback、相對與絕對路徑、E2E測試報告.md及progress.md，交給高階Planner。Plan Review為USER_WAIVED_NOT_RUN；post-implementation Acceptance仍必需。這是本地deterministic Handoff，native Harness4.8因原Python3.14 runtime失效仍NOT_RUN；不要用其他validator或假invitation宣稱native PASS。僅文件落檔與Git發布已在本次完成，產品IMPLEMENT尚未執行。

# live-grounding-04 實作交接

Plan SHA-256：c8ed33dfa1040c9c7843fda7008167eb14b7c0b9f45e94f6cee1c40419e65aaf。Contract／handoff.json SHA-256：a83bec99428ad66ae32e1795dfb17545e8dbd7df4df802cfb54b9f4e8b345883。

本交接在Plan與contract freeze後deterministic編譯。03 prompt的可選Reviewer未啟動。原生stage/publication/schema validators未執行，不能把下方契約當成native admission receipt。文件已獲落檔與Git授權；產品尚未實作。

## 先讀與執行順序

plan.md、research.md、input-manifest.json、baseline.json、native-admission.json → 原報告與attempt ledger → 核對head/dirty/state/runtime → production wiring與隔離回歸 → final source/binary/grants freeze → 有效前景與版面 → catalog/menu/第一本 → release/actual scroll → 不同第二本 → 報告與獨立Acceptance。

code/state/GUI授權、failure routes、檢查命令與界面見plan.md。config cap固定1，兩owner共享quota／ledger；不得自行增加額度。human observation及waiver分開記，不是工具PASS。

## 凍結 gates

| Gate | Phase | Owner | Criticality | Evidence role | Closure |
|---|---|---|---|---|---|
| G_PLAN_REVIEW_WAIVER | PLAN | HUMAN | SUPPORTING | DIAGNOSTIC | HARD_CLEAN |
| G_AUTH | IMPLEMENT | ROLE | CORE | MUST_NOT_BREAK | HARD_CLEAN |
| G_OFFLINE | IMPLEMENT | ROLE | CORE | MUST_NOT_BREAK | HARD_CLEAN |
| G_MIGRATION | IMPLEMENT | ROLE | CORE | MUST_NOT_BREAK | HARD_CLEAN |
| G_CATALOG | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_MENU | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_FIRST | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_SCROLL | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_SECOND | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_PRESERVE | IMPLEMENT | ROLE | CORE | MUST_NOT_BREAK | BASELINE_DELTA |
| G_REPORT | IMPLEMENT | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_ACCEPTANCE | ACCEPTANCE | ROLE | CORE | OUTCOME | HARD_CLEAN |
| G_DELIVERY | IMPLEMENT | ROLE | SUPPORTING | OUTCOME | HARD_CLEAN |

## 精確 allowed paths

- scripts/line_backup_cua_adapter.mjs
- src/line_backup_batch/cli.py
- src/line_backup_batch/observations.py
- src/line_backup_batch/service.py
- rev28/Sources/rev28ctl/main.swift
- rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift
- rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift
- rev28/Tests/Rev28CoreTests/FrameSupportTests.swift
- tests/test_cua_adapter.mjs
- tests/test_batch_authority.py
- tests/test_batch_observations.py
- tests/test_batch_lifecycle.py
- state/backup_state.json
- state/.line-backup-state.lock
- state/.line-backup-v3.tmp
- backups/旻謙允禎成長日記
- harness-development/line-v3-live-e2e-20261010/gui-ledger.json
- harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04

## 完整機器契約

```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "Repair cross-realm CUA byte retention, repo-owned passive native context, strict v2 visual/AX grounding, production callbacks, chooser phases and runtime bindings; preserve the canonical schema-3 writer and complete two different cap-one album lifecycles with actual post-first-release bounded scroll, content/state verification, reporting and independent Acceptance.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "scripts/line_backup_cua_adapter.mjs",
    "src/line_backup_batch/cli.py",
    "src/line_backup_batch/observations.py",
    "src/line_backup_batch/service.py",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift",
    "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift",
    "rev28/Tests/Rev28CoreTests/FrameSupportTests.swift",
    "tests/test_cua_adapter.mjs",
    "tests/test_batch_authority.py",
    "tests/test_batch_observations.py",
    "tests/test_batch_lifecycle.py",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-v3.tmp",
    "backups/旻謙允禎成長日記",
    "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04"
  ],
  "required_evidence": [
    "E_BASELINE",
    "E_AUTH",
    "E_OFFLINE",
    "E_MIGRATION",
    "E_LIVE_CATALOG",
    "E_MENU",
    "E_FIRST",
    "E_SCROLL",
    "E_SECOND",
    "E_PRESERVATION",
    "E_REPORT",
    "E_ACCEPTANCE",
    "E_DELIVERY",
    "E_PLAN_REVIEW_WAIVER",
    "E_NATIVE_CONTEXT",
    "E_BYTE_RETENTION",
    "E_FRAME_SUPPORT",
    "E_V2_CLASSIFIER",
    "E_CHOOSER",
    "E_RUNTIME_BINDING",
    "E_LATENCY",
    "E_SESSION_LIFECYCLE",
    "E_PRODUCTION_WIRING",
    "E_LAYOUT_FEASIBILITY"
  ],
  "gate_specs": [
    {
      "gate_id": "G_PLAN_REVIEW_WAIVER",
      "required": true,
      "owner": "HUMAN",
      "phase": "PLAN",
      "evidence_source": "HUMAN_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "DIAGNOSTIC",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_AUTH",
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
      "gate_id": "G_OFFLINE",
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
      "gate_id": "G_MIGRATION",
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
      "gate_id": "G_CATALOG",
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
      "gate_id": "G_MENU",
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
      "gate_id": "G_FIRST",
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
      "gate_id": "G_SCROLL",
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
      "gate_id": "G_SECOND",
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
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_ACCEPTANCE",
      "required": true,
      "owner": "ROLE",
      "phase": "ACCEPTANCE",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_DELIVERY",
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
    "network": "PROXY_ALLOWLIST",
    "browser": false,
    "destinations": [
      "https://developer.apple.com",
      "https://support.apple.com",
      "https://nodejs.org",
      "https://github.com/s9008129/Line_backup.git"
    ]
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
    "plan_review_required": true,
    "independent_acceptance_required": true,
    "max_parallel_read_only_helpers": 1,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
