你是 `TASK-20261010-line-v3-live-e2e / live-grounding-03` 的 IMPLEMENTER。你的任務是依同目錄已落檔且凍結的 `plan.md`，修復 non-menu SCK producer、grounded classifier／geometry、chooser/download evidence、grant v2 與 runner/session 接線，實際完成兩本不同 eligible 相簿的 Save All、內容 decode、VERIFIED/readback、第一本釋放後的真实 downward bounded scroll，以及 required independent Acceptance。你收到的兩個主文件是 `plan.md` 與本 `handoff.md`；先讀 Plan，再核對本文件中的 hashes／machine contract／waiver。Project root 嚴格固定 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`，branch `v43-ab/codex-rev28`，source checkpoint `a26a8e99141d9d4141c08e85f22491d35847f81c`；保留既有未提交來源與其他工作。root 串行修改，最多三名唯讀 helpers 同步分析，writer=0。只改凍結 allowed_paths；不用舊 task runner 覆寫歷史證據。保留 schema 3、唯一 Store/CAS、完整 catalog admission/drift check、每格 SCK、五秒 freshness／permit deadline、16 MiB artifact cap、兩個 cap-one lifecycle、共用兩次 Save All／兩次 chooser／1000 GUI額度及 at-most-once barrier。先完成離線 regression、source/runtime/binary freeze與新版 grants，再以新鮮前景交接開始真機 grounding與交易；不要將 import成功、fake tests、shape validator、candidate geometry或human observation當live E2E PASS。完成 intent readback 的同一不中斷 execution才有原始一次 permission；消耗後 ellipsis→bounded SCK popup capture/guard→唯一Save All，guard只驗證原校準點。每次 chooser輸入使用fresh實際控件／path／leaf證據，一次confirmation；download evidence獨立於17-key frame，真實HIGH焦點不可改稱NONE。下載後原session永久停止；VERIFIED/readback後用新的navigation-only observer做fresh完整catalog、finish/release，之後第二owner fresh觀察並实际向下≤0.25view-height scroll，保留before/action/after与完整唯一有序overlap及新候選，再重跑第二本全部gates。第一本未 VERIFIED/readback/release，不得進第二 lifecycle；第二本原先可見也不能跳過scroll。Swift新issue最多三次，每次build/test啟動前durable reservation；保留舊四次及單次例外收據，不用改名重置。所有意外或不確定停依賴操作，保存證據及intent barrier，不重送、不刪資料、不換writer、不降gate；每輪更新本目錄E2E測試報告、progress、ledger與manifest，分開六狀態。使用者本輪Plan Review明確WAIVED/NOT_RUN，事後獨立Acceptance保留；native controller/stage validation NOT_RUN，不能捏造邀請或receipt。例行scope內編輯與列明本地測試已有授權，LINE前景按AGENTS明確交接；本次document add/commit/push授權不自動授予你產品Git發布權。若真正能力／來源／geometry／chooser／latency／owner／state無法通過，輸出最小可重現blocker與精確下一決策，保留部分成功。

# Implementer Handoff — 已落檔 Plan 的 deterministic local compilation

## 1. 交接性質與執行狀態

本文件只在 Plan/contract 落檔、schema結構核對及 `plan-freeze.json` 產生後編寫。它是deterministic Handoff，不是03 prompt可選Handoff Reviewer的模型結果。使用者免除本輪Plan Review；`handoff_review_required=false`。沒有任何本輪產品實作、Swift新issue attempt、LINE input、Save All、chooser confirmation、download或scroll因本文件而執行。

Runtime/compiler不能因本交接新增gates、改requiredness、paths、budget、writer、schema或scope。附錄contract是原Plan contract的原文copy；磁碟 `handoff.json` 必須逐byte相等。本輪documentation交付≠產品G_DELIVERY PASS。

## 2. 接手第一步

1. 載入指定root的AGENTS.md與已落檔plan.md；使用line-album-backup skill，讀state contract，GUI階段讀evidence/state-machine/UI procedure，驗收階段讀verification。專案核准的SCK popup guard順序優先於skill通用blind atomic pair。
2. 以本文件下方hash、`plan-freeze.json`、`input-manifest.json`核對完整文件與28個原输入；重新查看Git HEAD/branch/index、current source/state/config/ledger。只接受source checkpoint的後繼documentation commit，不能discard source工作區。stage/index如果出现未预期資料先停。
3. 閱讀原 `$TP/submission-packet.md`、`blocker-packet.md`、`E2E測試報告.md`、`results/implementer.result.json`與 `continuations/implement-02/user-decision-A.json`。blocker/progress中的「等待A/B/C」已由user decision A取代，不能再詢問同一決策。
4. 本輪state schema3/rev35是已完成migration結果；唯一writer与歷史保全繼續，不能再遷移或初始化state。舊G_AUTH/G_OFFLINE不認證新code/grants。
5. 先保存你的fresh實作基線與新issue ledger，再分配最多三個唯讀分析helpers：native/geometry、classifier/chooser、grant/orchestration。它們不能寫產品、變更契約、nested sessions或代替獨立Acceptance。root串行寫程式、負責全部merged evidence。

## 3. 固定實作順序與完成條件

| 順序 | 行動 | 結束條件 |
|---|---|---|
| 1 | Native frame-support、實際capture timing、SCK/native mapping／geometry；保留menu guard | 正負離線fixtures正确、fresh provider/identity/anchors拒絕路徑完整；不含GUI。 |
| 2 | `$CON/live_classifier.mjs`、`chooser_locators.mjs`、新版`live_runner.mjs`與adapter | Strict17frame與typed chooser/download分開、未知拒絕、own-session捕獲、async callbacks、永久ceased dispatch與新的navigation-only observer。 |
| 3 | Grant v2、來源閉包、binary/runtime sensors、menu_calibration/return_navigation ledger | 原decoder與producer分别綁、新contract/user waiver、完整runtime inventory、shared quotas和每次GUI記帳可驗證。 |
| 4 | 全部必要offline suites及一次預先reserved Swift full suite | 新候選實際PASS，保存commands/env/counts/stdout/stderr/exit/bytes/hash；失敗依3/2額度停止。 |
| 5 | 真正runtime bridge preflight→重新source/runtime/binary freeze→雙grant→前景交接→live grounding | Catalog/detail native+CUA資料可驗證、card geometry真實、pre-intent menu latency符合既有deadline。 |
| 6 | 第一完整catalog→fresh candidate→open MATCH→calibrate/close→fresh detail→original intent/dispatch→chooser→download→content verify | 第一本完整VERIFIED、state/inventory readback、navigation-only fresh final catalog、CAP_REACHED finish/release。 |
| 7 | first release後fresh Albums→至少一次真实downward bounded scroll→第二完整catalog/fresh candidate→第二完整交易 | 不同fingerprint，scroll有before/action/after/effect/ordered overlap/new complete candidate；第二本VERIFIED/readback/release。 |
| 8 | 分項報告、preservation、獨立Acceptance、正式交付 | menu/first/scroll/second/batch/state各自证據，全部適用gates满足；不得將CAP_REACHED稱為整群ALL_COMPLETE。 |

Interface以Plan §§3–6為准。新的classifier/locators/runner放本輪package，不把原25,510B runner的兩個fail-closed stubs當完成產品。`adapterModule`必要依賴明列；模組載入实际bytes核對。每個source改動讓舊freeze/grant失效；重驗再freeze，不能只改hash欄位迎合。

`runtime_binding`來源閉包固定為既有21個產品sources＋新runner/classifier/locators＋實際Python executable＋producer binary＋Package.swift／Rev28Core／rev28ctl全部Swift literal file inventory；每個entry有bytes/hash/membership。source inventory不是OS隔離證據。

Chooser必须使用实际LINE panel（owner/dispatch/parent context連續性），不能自建NSOpenPanel作真機PASS。Typed envelope允許已確認GoToFolder field的真實HIGH_EDITABLE，但generic album-frame拒絕政策保留。Path/index/confirm point不可跨capture重用。

## 4. 前景、atomic dispatch與下載

每個需要前景的有界操作先公告LINE app/surface與下一精確動作，等待明確交接。被取回立即停止，新的交接後重新capture/bind；没有回覆、等待時間、舊session交接都不是當下許可。

Intent前要求identity/duplicate/destination/owner/calibration/freshness全部成立，持久intent與readback成功才發原始opaque token。Save All point全鏈保持JSON整數同一性。消耗token後單次ellipsis、既有menu wait、SCK popup capture/guard/16MiB bytes-hash precheck，確認與原點完全相等及deadline未過後才唯一Save All。nativeguard過程無額外GUI、鍵盤、app switch或改點。任何失敗／不確定消耗權限，不補發。

Confirmation一次，下載開始後cease input。開始证据为实际下載UI或同bound空目的地的新增recognized image；closed chooser／常數boolean不算。UI不足時30秒×1秒readonly sampling，仍UNKNOWN則停依賴交易，不派第二Save All。完整content另以5秒×3相同inventory、600秒上限、全部entries與ImageIO full decode、commit/readback fence验收。不能用LINE畫面代替filesystem驗收。

## 5. Gate outputs、報告與停止

Machine GateSpecs／required evidence完整列於附錄，Plan §7逐項指出owner与輸出。使用者waiver單独保存，只表明免除Plan Review；underlyingreview仍NOT_RUN。Human observation的OBSERVED不當工具PASS；helper報告／fake I/O／schema shape／import能力不當livePASS。

成果輸出全部到本輪package（Plan、contract、waiver、freeze、Handoff原件保持不可覆寫）：`runtime-binding.json`、`authorization.json`、`live-grant-1.json`、`live-grant-2.json`、`attempt-ledger.json`、`evidence/*`、`E2E測試報告.md`、`progress.md`、必要blocker與真正role results。引用本轮与历史証据要relative/absolute paths、bytes、SHA256及可重現command。

前景／identity／geometry／focus／anchor／latency／scroll／source／grant／quota／dest／writer／state/readback／dispatch／confirmation有UNKNOWN或unexpected副作用：立刻停止依赖动作，保持原intent barrier与现有資料。NO_ELIGIBLE_TARGET或SCROLL_TEST_NOT_RUN都維持PARTIAL。两次无信息增益、三次同root issue或material blocker走既定升级，不重复碰运气。

每轮测试后将报告交指定Planner；沒有真實通道就明确「尚未完成Planner交接」。独立Acceptance必须由没有贡献当前candidate的人完成；此Handoff/helper不充任Acceptance。

六狀態保持分開：PRIMARY_OUTCOME_STATUS、IMPLEMENTATION_STATUS、CORE_ACCEPTANCE_STATUS、REQUIRED_VERIFICATION_STATUS、INDEPENDENT_ACCEPTANCE_STATUS、TASK_CLOSURE_STATUS。core已證成事实不得被阻塞抹掉，所有适用gate与Acceptance满足前不得DONE。

## 6. Native Harness 與 Git 授權

Immutable v4.8 schema/CLI/runtime固定如Plan §11。当前controller不支持實作前Critical review waiver，采用明确user授权的local deterministic route；native admission/publication/CONTRACT/RESULT stage validation均NOT_RUN。`document-run.json`UUID只是已記錄的local document invocation，不是native invitation/run allocation。本地官方schema API的VALID只是结构检查。若有genuine stagepacket，按其fixed emitted commands走，不能构造替代nativevalidator。

本轮文件完成后root按user另行授权仅stage本文件目录，使用GPT-6 luna建议的详细commit message add/commit/push。你作为下一轮Implementer不能借这项document授权commit/push产品或无关dirty工作；需要任何超contract行为先形成精确决策。也不修改Harness、config、canonical schema或替换writer。

## 7. 凍結 bindings 與 machine contract

Plan：`plan.md`，30678 bytes，SHA-256 `001b90861631fe27b0d21ec871be5fc19446bf3070e88bb116350a0f3690708c`。

Contract／handoff.json：各 6318 bytes，SHA-256 `d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219`，逐byte相等。

Plan freeze creation time：`2026-10-10T12:00:46.532403+00:00`；Handoff compilation time：`2026-10-10T12:04:13.597110+00:00`。前者已持久保存後才建立本交接。

完整凍結JSON如下；与同目录plan-contract.json／handoff.json原文相同。

```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "Repair non-menu SCK support, grounded visual/AX classification, chooser evidence, grant runtime binding and session orchestration; preserve the canonical schema-3 writer and history; complete two different cap-one album lifecycles with actual post-first downward scroll, full content verification, reporting and independent Acceptance.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "src/line_backup_batch/cli.py",
    "src/line_backup_batch/store.py",
    "src/line_backup_batch/observations.py",
    "src/line_backup_batch/service.py",
    "scripts/line_backup_cua_adapter.mjs",
    "rev28/Sources/Rev28Core/Perception/OcrEngine.swift",
    "rev28/Sources/Rev28Core/Sensor/FrameCapture.swift",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Tests/Rev28CoreTests/OcrEngineTests.swift",
    "rev28/Tests/Rev28CoreTests/FrameSupportTests.swift",
    "tests/test_batch_authority.py",
    "tests/test_batch_observations.py",
    "tests/test_batch_coordinator.py",
    "tests/test_batch_lifecycle.py",
    "tests/test_cua_adapter.mjs",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-v3.tmp",
    "backups/旻謙允禎成長日記",
    "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03"
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
    "E_FRAME_SUPPORT",
    "E_CLASSIFIER",
    "E_CHOOSER",
    "E_RUNTIME_BINDING",
    "E_LATENCY",
    "E_SESSION_LIFECYCLE"
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
