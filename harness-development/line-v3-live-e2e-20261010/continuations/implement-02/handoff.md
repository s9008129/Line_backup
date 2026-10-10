你是下一位接手的 IMPLEMENTER。請直接依本交接完成產品 Implement 與兩本 LINE 相簿實機 E2E_test，使用者已授權，不需要再次詢問同一範圍的許可，也不安排本次獨立 Plan Review。

Project root 固定為 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup。
Task ID 固定為 TASK-20261010-line-v3-live-e2e；本次 continuation 固定為 harness-development/line-v3-live-e2e-20261010/continuations/implement-02。

先讀本專案 AGENTS.md、/Users/hsiaojohnny/.codex/prompts/v4.8.0/04_implement_prompt.md、本目錄 plan.md、plan-contract.json、handoff.json、continuation-policy.json、plan-review-waiver.json、compile-handoff.receipt.json，再讀 ../../E2E測試報告.md、../../blocker-packet.md、../../attempt-ledger.json、../../evidence/planner-replan.md、../../results/implementer.result.json 及其原始收據。使用 /Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md；本專案已核准的 originalObservedDispatch 具體順序优先於 skill 通用 atomic pair。

核對 plan-contract.json 與 handoff.json 的 bytes/hash 完全一致，並 fresh 核對 HEAD、branch、index、dirty/untracked work、source、config、canonical state。文件基線 HEAD fad3641a3193e25b2ae5b6b3ce036e8d33843418；你接手時可能已有本交接的文件 commit，不能把歷史 HEAD/index 狀態當成當下事實。保全無關修改、旧 artifacts、既有照片與歷史 state；只改 frozen allowed_paths，root 串行，max_parallel_writers=0。唯讀 helpers 可平行但不寫產品或 nested spawn。

Swift 同 root issue 已有四次執行，四筆收據不得刪改、改名或清零。使用者在 request_user_input 明確選擇「核准單次例外 (Recommended)」；離線缺口全修好後只准一次額外 package 驗證。先持久 reserve，再啟動一次完整 macOS26.5 Swift test；任何 compile/fail/crash/timeout/不完整收據均消耗額度並停。不預跑 package build/filtered tests，不跑第六次。

依 plan.md 順序實作：完整 fixture config/state/report 資料鏈修復 → 巢狀 operation authority/retained dispatch receipts/GUI quota/filesystem intent/finalize drift fence → full-display SCK/Vision producer/正式 popup guard/live bridge → Python/Node/唯一 Swift 回歸。重點：六組 fixture 外層 config/state 的 root 與 bytes/hash 都不匹配，只改 nested destination 不足。負向 tests 要先證明原始正向 fixture 能 binding。

只有 G_OFFLINE/G_AUTH 明確 PASS、完整 source/config/native binary freeze/grants 成立，才可做 schema2 rev34 → schema3 rev35 exact migration。原 state hash ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9；config hash 5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362。先原件 snapshot，再唯一 writer/shared lock/CAS/readback，歷史及整數精度保全。

LINE 前景操作前必須告知 app/surface/下一個精確動作，等待使用者明確交接；舊交接不可當新鮮證據。所有 LINE 輸入只用 runtime documented CUA。runtime bridge/raw screenshots/持續 session 不具備時停止，不能以 fake provider 冒充實機。

完整 E2E 順序：fresh 完整 catalog（top/bottom/每一步 overlap）→ 第一 eligible card 同 frame 安全 metadata binding/post-open MATCH → 真實 menu 校準及無 activation 的安全關閉 → intent commit/readback/一次 token → ellipsis/native popup guard/唯一 Save All → 真實 chooser/精確 Go to Folder/一次確認 → download開始後停止 LINE 輸入 → 五秒取樣、三次相同 inventory、600秒上限、exact count、逐張 full ImageIO decode、decode後不變 → VERIFIED/readback/cap1 finish/release。

第一本 active_writer/context_lock/active_batch 全釋放後，fresh 回列表，必須實際做至少一次≤0.25 viewport scroll並保存 before/action/after；同群組/surface/session/PID/window/layout、有序完整唯一 overlap、新完整 eligible card 全證明後，才選不同 fingerprint 進第二個 cap1 lifecycle，重跑全部 transaction及內容/state驗收。無下一本 NO_ELIGIBLE_TARGET、未scroll SCROLL_TEST_NOT_RUN 均不能宣稱兩本成功。

整 task 上限為兩次 Save All、兩次 chooser confirmation、1000次額外可逆 GUI invocation；兩個 owner 共用持久 ledger。intent後不校準/換點/重送；UNKNOWN/crash保留barrier。前景中斷、identity/mapping/scroll不明、source/grant/state drift、目的地副作用、writer/readback不確定即停，保存 blocker。

本次 Plan Review已明確waiver，記WAIVED/NOT_RUN；既有事後獨立Acceptance仍是完整專案關閉gate。03_handoff_prompt.md是handoff_review_required=true才用的可選Reviewer；本contract為false，不啟動它。Harness4.8 immutable schema的CRITICAL flag仍為true，实际waiver另存；native admission/controller validation尚未提供收據，維持NOT_RUN，不杜撰命令、run identity或PASS。若實際收到stage packet，才使用其固定emitted validators。

每次實測更新本目錄 E2E測試報告.md、progress.md、attempt ledger；保留工具/命令/環境/順序/原始證據/bytes/hash/狀態差異/副作用/未知，分列所有gate及六項status。原先Python77/Node10僅歷史離線PASS，Swift317/320為FAIL；本交接只完成文件，沒有產品修正、migration或新live evidence。按task適用gates與事後Acceptance結案；產品提交/推送只納入核准差異，保全其餘dirty work。


# 執行交接封包

Plan SHA-256：`b81ca57103bb71b60dacc7848a104e8cb0efcd28347fba862ad8736997756a49`。Contract/Handoff SHA-256：`6505ad3817a899c223d42a8e814ec81cbb0f3317bb206d73a4a503671726d419`。

這是本次已確認計畫的 deterministic local Handoff；不是 03 prompt 的可選 Handoff Reviewer 結果。native stage packet/emitted validators 尚未提供，controller admission/validation 保持 NOT_RUN。直接 JSON Schema 檢查只證明文件結構，不認證產品或 E2E。

本次交接只完成文件；所有產品／實機 gates 的 PASS 仍需接手者產生原始證據。Plan Review waiver 是獨立 user decision，不是 reviewer PASS。

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

## 完整機器契約

下面的 JSON 與 plan-contract.json / handoff.json 內容一致；allowed_paths、required_evidence、gate_specs 及 writer limits 不得由接手者自行擴張。

```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "Integrate the canonical v3 transaction writer and documented LINE CUA/native observation path; preserve schema-2 history through exact migration; complete two distinct cap=1 live album lifecycles with actual scroll grounding; report, independently accept, and deliver the reviewed result.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "src/line_backup_batch",
    "src/line_backup_acceptance/common.py",
    "src/line_backup_acceptance/authority.py",
    "src/line_backup_acceptance/transaction.py",
    "src/line_backup_acceptance/project_binding.py",
    "src/line_backup_acceptance/cli.py",
    "scripts/line_backup_cua_adapter.mjs",
    "rev28/Sources/Rev28Core/Composition/LiveComposition.swift",
    "rev28/Sources/Rev28Core/Composition/ProductionObservationSource.swift",
    "rev28/Sources/Rev28Core/Composition/ProjectBackupBinding.swift",
    "rev28/Sources/Rev28Core/Observation/NativeObservationSession.swift",
    "rev28/Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift",
    "rev28/Sources/Rev28Core/Sensor/FrameCapture.swift",
    "rev28/Sources/Rev28Core/Sensor/RunEpochAuthority.swift",
    "rev28/Sources/Rev28Core/Perception/OcrEngine.swift",
    "rev28/Sources/rev28ctl/main.swift",
    "tests/test_batch_authority.py",
    "tests/test_batch_migration.py",
    "tests/test_batch_coordinator.py",
    "tests/test_batch_observations.py",
    "tests/test_batch_content.py",
    "tests/test_batch_scroll.py",
    "tests/test_batch_lifecycle.py",
    "tests/test_project_binding.py",
    "tests/test_cua_adapter.mjs",
    "rev28/Tests/Rev28CoreTests/ProjectBackupBindingTests.swift",
    "rev28/Tests/Rev28CoreTests/LiveCompositionTests.swift",
    "rev28/Tests/Rev28CoreTests/NativeObservationSessionTests.swift",
    "rev28/Tests/Rev28CoreTests/RunEpochAuthorityTests.swift",
    "rev28/Tests/Rev28CoreTests/ExplicitLineCaptureSelectionTests.swift",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-migration-v3.tmp",
    "state/.line-backup-v3.tmp",
    "backups/旻謙允禎成長日記",
    "harness-development/line-v3-live-e2e-20261010"
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
    "E_PLAN_REVIEW_WAIVER"
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
    "max_parallel_read_only_helpers": 3,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
