你是 scope-recovery-05 的 Implementer。Project root 固定為 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup；唯一可寫 CON 是 harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05。先讀 CON 的 plan.md、plan-contract.json、plan-amendment-01.md、plan-amendment-01-review.md、plan-amendment-01-helper-notes.md、handoff.json、check-specs.json、incident-reconciliation.json、lineage.json、baseline.json、input-manifest.json、native-admission.json、E2E測試報告.md 與 progress.md，再讀 parent live-grounding-04 的事故／報告和 live-grounding-03 attempt-ledger。確認 amended contract 與 handoff.json 逐 byte 相同、核對現在 HEAD/branch/index、所有既有 dirty/untracked/ignored 工作及原件 hash，建立你自己的 fresh baseline；文件階段 baseline 不是你的 gate PASS。四份 sibling evidence 原件及舊 runner 保持原位唯讀，原 G_PRESERVE 失敗不改寫。只在 CON/checks/run_command.py 實作固定 root/output、寫入前 scope/realpath/symlink/覆寫 guard、--preflight、bounded process 與完整收據工具；先用 host 明確絕對路徑留存 preflight/selftest，G_RUNNER PASS 後才依 check-specs.json 跑 unchanged adapter 的 Node syntax 和既有全套＋CON 補充 capture tests。adapter、既有 tests、state/config/backups/GUI ledger 與所有其他路徑保持唯讀；不操作 LINE、不下載、不換 writer、不修產品、不 commit/push。最多 3 名唯讀 helpers、writer=0；helpers 僅提供諮詢，不寫檔、不執行檢查、不審核 gates、不擴大範圍、不啟動巢狀代理。root 是唯一實作者和決策者。Plan Amendment 01 的本地獨立檢視 PASS 見 plan-amendment-01-review.md；它不是 native Harness stage。沿用 LIVE_CLASSIFIER_CHOOSER 已有兩次紀錄，本輪最多一個剩餘第3次驗證集合；任何必要檢查失敗、範圍副作用或 baseline 漂移即保留 raw evidence、停止依賴步驟，交回 Planner，不失敗重跑。每個 gate 需自身實際證據與明確 PASS；記錄 relative/absolute/bytes/hash/readback、實際命令／順序／環境／副作用／未知及 E2E測試報告.md、progress.md、format3 result。無 Planner 通道則準備交接包並如實記未交接。native Harness4.8 因固定 runtime 失效保持 NOT_RUN，不造 invitation、不換 validator、不修 global runtime；局部離線結果不能替代正式驗證、parent 兩本 E2E／實際 scroll／獨立 Acceptance，也不能宣稱整體 DONE。本次文件發布由前一角色另行處理，不授予你 Git 發布或 parent 全流程實作權限。

# scope-recovery-05 精準實作交接

Plan SHA-256：43ebe2d8b940703ff5aa67ccc6f430de5789d976ef6e6776259fe2d85041bea4。Contract／handoff.json SHA-256：18ea97bc6d41171a2460c3979ce9d3f7ca5e7441aaf104aa922ebd8969d297c7。Plan Amendment 01 獨立檢視結果見 `plan-amendment-01-review.md`。

本文件是 root 依凍結契約產生的本地 deterministic Handoff；沒有 native controller publication，也沒有 model-backed Handoff Review。文件一致性與格式3形狀不能冒充 native schema PASS。文件發布及其 Git 收據以 document-delivery-policy.json 和 CON/.local 實際記錄為準，正文不預寫未來 commit/push 為成功。

## 接手順序與授權

fresh baseline → incident/runtime/source closure → host preflight/selftest → verified runner → unchanged adapter syntax／full existing＋supplemental tests → preservation → detailed report／format3 result → Planner。精確命令、環境、輸出見 check-specs.json；實作及驗收規則見 plan.md。

唯一 allowed path：`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05`。產品及既有 tests 唯讀。原四份收據依 incident-reconciliation.json 原位保留，舊失敗不改寫。任何第一個必要失敗都停止依賴檢查；候選驗證最多使用剩餘第三次，沒有產品修補或失敗重跑授權。

## 凍結 gates

全部 required=true、ROLE_OBSERVATION。下表與原契約一致，現在全為 NOT_RUN。

| Gate | Owner / Phase | Criticality / Evidence role / Closure | Reuse |
|---|---|---|---|
| G_BASELINE | ROLE / IMPLEMENT | CORE / MUST_NOT_BREAK / HARD_CLEAN | NEVER |
| G_RUNNER | ROLE / IMPLEMENT | CORE / MUST_NOT_BREAK / HARD_CLEAN | NEVER |
| G_ADAPTER_OFFLINE | ROLE / IMPLEMENT | CORE / OUTCOME / HARD_CLEAN | NEVER |
| G_PRESERVE | ROLE / IMPLEMENT | CORE / MUST_NOT_BREAK / BASELINE_DELTA | NEVER |
| G_REPORT | ROLE / IMPLEMENT | SUPPORTING / OUTCOME / HARD_CLEAN | NEVER |

## 尚未完成的要求

native admission、stage publication、CONTRACT/RESULT validators 均 NOT_RUN。parent 的 G_AUTH/G_MIGRATION/full G_OFFLINE/live catalog/menu/兩本交易/實際 scroll/獨立 Acceptance 未因本交接通過。新局部恢復不要求獨立 Acceptance，parent 必須保留。不得把發布文件當成產品、照片內容或批次 E2E 完成。

## Amendment 01 完整機器契約

```json
{
  "format_version": "3",
  "task_id": "TASK-20261011-line-receipt-recovery",
  "goal": "Preserve the four original out-of-scope receipts in place; repair a CON-bound local check runner and verify the unchanged candidate CUA adapter offline; preserve all unrelated work and report back to Planner without LINE input, downloads, product/state/config/ledger edits or parent E2E closure.",
  "task_class": "QUICK",
  "allowed_paths": [
    "harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05"
  ],
  "required_evidence": [
    "E_BASELINE",
    "E_INCIDENT_RECONCILIATION",
    "E_RUNNER",
    "E_ADAPTER_OFFLINE",
    "E_PRESERVATION",
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
    "plan_review_required": true,
    "independent_acceptance_required": false,
    "max_parallel_read_only_helpers": 3,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
