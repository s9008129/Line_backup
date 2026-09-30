# HANDOFF — LINE Backup Rev28（2026-09-30，新對話／接手專用）

> 本文件是下一個新對話與後續 Agent 的唯一接手入口（navigation + status snapshot）。
> 它**不是** canonical 契約，也不取代任何 Stage 03 文件；canonical 執行契約仍為
> `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/handoff.md`（SHA-256 `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33`），
> 設計契約仍為同目錄 `plan.md`（R4）。**不要覆寫它們。**
> 核心原則：**不要從頭探索；不要重跑已證明事項；不要重置 blocker budget；不要在應該停止的位置繼續燒 token。**
> Updated: 2026-09-30（Asia/Taipei）。撰寫依據：repo 實測＋task durable artifacts＋commit `815e9f1`。

---

## 0. 一句話現況

產品樹已凍結於 `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`（implementation digest `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`，48 paths）。V-09 attempt-04 三份 fresh 複審全部 **0 MAJOR**，並已入 commit `815e9f1`（已推送 origin）。`PRIMARY_NATIVE_COMPOSITION` 以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉（3/3 exhausted，永不重開）。離線可完成的實作與驗證已全部收束；**唯一剩下的真實世界 gate 是外部 Phase A 前置**：使用者登入 LINE 並把「旻謙允禎成長日記」的 `2024/05/13～05/17` 相簿 surface 準備到可觀察狀態，之後才以 fresh runID 跑 `rev28ctl live-preflight`（Phase A、read-only、零不可逆）。在該條件成立前：不操作 GUI、不跑 `live-preflight`／`live-execute`、不開任何新 implementation attempt——**正確的 STOP 就是成功**。

---

## 1. 專案與 Task 身分（先核對，再行動）

| 項目 | 值 |
|---|---|
| TASK_ID | `T20260925-0647-01-rev28-native-closed-loop` |
| Task class | `CRITICAL` |
| Harness | V4.3.1（STATUS_CONTRACT v2、CONVERGENCE_CONTRACT v1） |
| 主要 repo | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` |
| 目前 branch / HEAD | `v43-ab/codex-rev28` @ `815e9f1b02ac3f74539fae3814e52bf914547850`（clean、已推 origin） |
| canonical Plan | `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`｜SHA-256 `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b`（R4；review attempt-07 `PLAN_APPROVED`） |
| canonical Stage 03 Handoff | 同目錄 `handoff.md`｜SHA-256 `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` |
| approved starting checkpoint | `9cbaa1141595acb538d4672066072d2b8ffb7065`（branch `rev28-prelive-finalization`；**禁止前移**） |
| 產品凍結樹 | `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`；`cf39fdcc..815e9f1` 的差異全部只在 `.agent/`（實測 `git diff cf39fdcc 815e9f1 -- rev28` 為空） |
| implementation digest | `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`（48 paths = 45 Swift + `Package.swift` + 2 tools；由生產用 `ReviewedImplementationDigest` 計算，Python replica 一致） |

### 1.1 Worktree 現場（2026-09-30 實測）

| 路徑 | branch | HEAD | 狀態 |
|---|---|---|---|
| `Documents/ChatGPT/Line_backup` | `v43-ab/codex-rev28` | `815e9f1`（已推） | clean＝authority tree |
| `Documents/ChatGPT/Line_backup-ab-deepseek` | `v43-ab/deepseek-rev28` | `472c283`（已推） | clean；`EXTERNAL_BLOCKER` 歷史（locked session） |
| `Documents/ChatGPT/Line_backup-ab-luna` | `v43-ab/luna-rev28` | `9cbaa11` | **11 個 dirty/untracked（唯一副本，禁止破壞）** |

- luna 現場 11 檔＝6 modified（`execution.md`、`StructuralLocators.swift`、`FrameCapture.swift`、`StagingVerifier.swift`、`StagingVerifierTests.swift`、`StructuralLocatorsTests.swift`）＋5 untracked（`escalations/`、`evidence/`、`progress.md`、`SameFramePerception.swift`、`SameFramePerceptionTests.swift`）。這些內容**不存在於任何 commit**；如需 snapshot 或清理，先取得使用者明確同意。
- 身分不一致（worktree / branch / HEAD / Plan SHA / Handoff SHA 與本表不符）＝`STATE_RECONCILIATION_REQUIRED`：停止並回報，**不得自行修 Git**。

### 1.2 origin refs（2026-09-30 實測）

| ref | SHA |
|---|---|
| `refs/heads/master` | `9db32f68d271272fd8ac5a6337522534e88d9ab2` |
| `refs/heads/rev28-prelive-finalization` | `9cbaa1141595acb538d4672066072d2b8ffb7065` |
| `refs/heads/v43-ab/codex-rev28` | `815e9f1b02ac3f74539fae3814e52bf914547850` |
| `refs/heads/v43-ab/deepseek-rev28` | `472c283cdda283628ca42e59390c44d921275f4c` |
| `refs/heads/rev28-ci-prelive-hardening` | `a572ec58f506100ae895c21891db8595aaadd5d6` |
| `refs/heads/harness-v4.3-validation` | `7f2a3104e03ade4f32c45647cbb58d291ab74576` |

---

## 2. 使用者真正要解決的問題（產品目標）

最終目標不是「讓測試變綠」，而是：從 macOS LINE App（`jp.naver.line.mac`）精確定位群組：

`旻謙允禎成長日記`

> 注意：`禎 = U+798E`。不得與 `楨 = U+6968` 混淆、正規化、合併或猜測為同一群組。

目標相簿：`2024/05/13～05/17`。最終需建立一份新的 staging backup；真正成功只能由 filesystem 與獨立 Stage 05 evidence 證明。

### 2.1 Primary Outcome＝唯一成功狀態 `DUPLICATE_CONTENT_CONFIRMED`

必須同時證明：

- exactly 57 complete、stable、decodable regular image files
- total bytes = `17,924,900`
- 無 symlink、無 hidden / extra / non-image entry、無 nested directory、無 partial / zero-byte file
- staging 內沒有 duplicate content
- filename-excluded content multiset SHA-256 = `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`
- 既有 baseline 完全不變（filenames / bytes / hashes / mtimes）
- baseline name-inclusive tripwire SHA-256 = `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`
- baseline reference：`Line_backup/evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json`｜SHA-256 `3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2`（2026-09-30 實測存在且相符）

Authoritative existing source（baseline）目錄：

`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`

2026-09-30 唯讀核對：57 files / 17,924,900 bytes / 0 symlinks（與基準一致）。

禁止把 baseline 檔案複製到 staging 來假裝下載成功。

---

## 3. Production 不可逆動作契約（ceiling）

- 真正成功的 production run 最多：`Save All dispatch = 1`、`destination confirmation = 1`。這是天花板，不是必須消耗的 quota。
- 任何 irreversible intent 一旦建立即視為消耗，即使 effect 是 `UNKNOWN`。
- 不得因為沒看到效果、session 重開、換模型、換 run、換 TASK wording、換 worktree 而取得第二次機會。
- `UNKNOWN` irreversible effect：**永遠不能 blind retry**（只能 observe-only）。
- Human authorization 不能把 mechanical `FAIL` 變成 `PASS`。

---

## 4. 目前狀態（2026-09-30；routing truth＝最新 valid Stage result）

```text
STATE: IMPLEMENTATION_COMPLETE_AS_FAR_AS_ALLOWED_PRE_PHASE_A
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: IN_PROGRESS（離線已無 falsifiable target；V-09 attempt-04 已收束）
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: IN_PROGRESS（V-09 attempt-04 完成、0 MAJOR；真實 Phase A NOT FIRED）
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS
PHASE_A_STATUS: EVIDENCE TOOLCHAIN COMPLETE; real preflight NOT FIRED — external prerequisite missing; 0/3 attempts
PHASE_B_STATUS: FORBIDDEN_AB_EVALUATION
irreversible counters: Save All dispatches 0 / destination confirmations 0 / irreversible intents 0
```

為什麼不是 `DONE`：Primary Outcome 尚未達成（尚未有任何真實 backup run）；Phase A 從未 fired；Stage 05 從未執行。目前**不是** `READY_FOR_PHASE_B`；Phase A 工具鏈已 COMPLETE，只缺外部前置。

---

## 5. 架構與關鍵邏輯（接手必讀）

產品程式碼在 `Line_backup/rev28/`：`Sources/Rev28Core/`、`Sources/rev28ctl/`、`Tests/`。

### 5.1 模組與職責（實際檔案）

| 模組 | 代表檔案 | 職責 |
|---|---|---|
| Observation | `Observation/NativeObservationSession.swift` | 同幀 observation／identity／geometry 證據鏈；menu/addressable bounds 必須落在 retained frame 內 |
| Composition | `Composition/LiveComposition.swift`、`ProductionObservationSource.swift`、`ComposedNativeAdapter.swift`、`PostSaveComposition.swift`、`PhaseAEvidence.swift` | 組裝 CLI→engine 的 native path（typed evidence＋adapters）；Phase A 報告 builder |
| Transaction | `Transaction/LiveExecutionEngine.swift`、`PersistentTransactionOwner.swift`、`IntentLedger.swift`、`StateEvidence.swift`、`PhaseBEligibility.swift`、`ReviewedImplementationDigest.swift`、`GoalSlot.swift`、`FilesystemTripwireJournal.swift`、`TripwireAttribution.swift`、`ReviewedBuildState.swift` | 單一 durable owner/ledger；phase entrypoint；budget 記帳；implementation digest |
| Policy | `Policy/ExecutionPolicy.swift`（`LiveDispatchBudget` 等） | budget 與 policy 規則 |
| Actuation | `Actuation/QuartzActuator.swift`（含 `GatedQuartzActuator`）、`AXDriver.swift` | guarded dispatch、per-primitive accounting、click 前重新驗證 |
| Perception | `Perception/StructuralLocators.swift`、`AlbumEllipsisLocator.swift`、`OcrEngine.swift` | 短日期 `yyyy/mm/dd～mm/dd` 分段、card-local count、cross-card refusal |
| Identity | `Identity/AXWindowIdentitySelector.swift`、`WindowIdentity.swift` | AX 讀取綁定 CGWindowID（絕不用 `windows[0]`） |
| Sensor | `Sensor/FrameCapture.swift`、`WindowSensor.swift`、`RunEpochAuthority.swift` | 擷取、視窗盤點、epoch authority |
| Chooser | `Chooser/FolderChooserDriver.swift`、`ChooserAffirmationPredicate.swift` | Go to Folder 逐 primitive 記帳、panel 唯一性 |
| Verification | `Verification/StagingVerifier.swift`、`BaselineVerifier.swift` | staging 完整性／穩定性；baseline 驗證 |
| Postcondition | `Postcondition/PostconditionMonitor.swift` | postcondition 監測 |
| CLI | `rev28ctl/main.swift`（factory `:282-317`；usage `:496`）、`HarnessCalibration.swift`、`FolderChooserDriver.swift`、`EvidenceRun.swift`、`QuartzActuator.swift`、`RestartFixture.swift` 等 | `live-preflight`／`live-execute`／`harness-calibrate`／`restart-child` |

### 5.2 Phase A 執行路徑（現行 CLI 真實行為）

1. `rev28ctl live-preflight --config <json> --one-shot-authorization <json>`
2. `LiveCompositionFactory.make(...)`（`main.swift:282`）組裝：`ProductionObservationSource` + `ComposedNativeAdapter` + `NativeObservationSession` + `PersistentTransactionOwner` + `GatedQuartzActuator`
3. `composition.engine.runPreflight()`（`LiveExecutionEngine.swift:264`，零不可逆）→ `observePreDispatchContext`（≥10s 環境取樣、tripwire 無 gap）
4. 寫 `preflight-outcome-<stamp>.json`；`PhaseAEvidenceBuilder.inspect` 產出 per-condition `PASS/FAIL/UNKNOWN` 報告＋raw evidence manifest
5. 真實 LINE chooser 在 Phase A 一律標記 deferred，**永不記為 PASS**（Phase B runtime gate）

`live-preflight` 的 config 需含 chooser calibration binding（`chooserCalibrationPath`／`chooserPredicateSHA256`／`chooserCalibrationSHA256`）；CLI 會重讀、hash 驗證 frozen bytes、decode、`ChooserProductionPredicate.derive`，非 process-stable v2 即 named refusal。

### 5.3 關鍵語意（不得在 implementation 內私自變更）

- 單一 durable authority：owner + ledger（`PersistentTransactionOwner`＋`IntentLedger`）。`reserveSaveAll` 要求耐久 `eligibility.phaseB` 記錄＋`currentState == .saveAllLocated`；`reserveDestinationConfirmation` 要求 `.destinationPrepared`。
- Phase separation：Phase A 零不可逆；Phase B eligibility 全 predicate PASS 才 arm。
- Irreversible dispatch boundary＋per-primitive accounting（每個 posted primitive 逐筆記帳；panel/field 非唯一即 fail closed）。
- 下載觀察上限 10 分鐘；stability 需 ≥3 個 equal snapshots 且跨度 ≥4 秒（以同一 final contiguous equal suffix 計算）。細節以 canonical `handoff.md` 為準。
- Fail-closed：任何不確定（timeout／ambiguous／stale／identity mismatch／baseline change／chooser ownership mismatch／crash after intent）→ 拒絕或 observe-only，絕不猜測或 retry。
- Stage 05 必須從 disk / raw evidence 獨立重算；不得引用 Stage 04 自寫的 PASS 字串。
- `exit 0 ≠ semantic PASS`。`progress.md` 不得凌駕 Stage result；`result.md` 不得自己創造 PASS。

### 5.4 C1–C7 核心工作契約（`plan.md`，行號為 plan 內位置）

- C1（`:105`）：恢復 diagnostic execution、保留 identity rules
- C2（`:111`）：單一 safety-critical orchestration
- C3（`:119`）：observation authority（同幀＋geometry provenance）
- C4（`:132`）：單一 durable transaction authority（ledger／budget／reservation）
- C5（`:148`）：guarded actuation（dispatch readiness、click 前重驗）
- C6（`:156`）：actual chooser 與 destination（逐 primitive 記帳）
- C7（`:170`）：filesystem authority 與 finalization（tripwire、post-dispatch gap、staging 證明）

---

## 6. 流程：Phase A／Phase B eligibility／Phase B／Stage 05

### 6.1 Phase A（read-only；目前 NOT FIRED，0/3 attempts）

- 可做：fresh read-only LINE identity observation、geometry、same-frame evidence、process/window inventory、baseline revalidation、pre-panel inventory、exact album/card association、LINE-specific V-09 證據。
- 不可做：任何未經 canonical 契約與當前授權明確允許的 reversible GUI navigation；`Save All intent/attempt = 0`；`destination confirmation intent/attempt = 0`。

### 6.2 Phase B eligibility（全部 predicate PASS 才 arm）

須同時滿足：approved source/binary/rule binding、所有 pre-B gates PASS、valid persistent authority、clean one-shot entitlement、baseline unchanged、fresh LINE identity、current geometry、actual fresh target、chooser/tripwire 準備有效、**當前 run 的 explicit one-shot human authorization**。任一 `FAIL / UNKNOWN / NOT_RUN / STALE / MISSING` → `PHASE_B_INELIGIBLE`。

### 6.3 Phase B（不可逆；`FORBIDDEN_AB_EVALUATION`）

`Save All` ≤1 persisted intent/attempt；`destination confirmation` ≤1；任何 timeout／ambiguous／crash → observe-only，不 retry。

### 6.4 Stage 05（fresh independent acceptance）

真正執行完成後，Stage 05 必須從 disk/raw evidence 自己重算：staging file count、bytes、decodability、content hashes、content multiset、stability、baseline names/hashes/mtimes、ledger、intent/attempt counts、emitted GUI actions、evidence chain/anchors、LINE observation 與 backup run 的 binding。Stage 04 不得自我宣稱成功。

---

## 7. Blocker 史與根因分析（避免重複走冤枉路）

### 7.1 已 RESOLVED（有 mechanical evidence；勿重探）

| Blocker | 收束方式 |
|---|---|
| Deterministic Swift test compilation | `StructuralLocatorsTests.swift` 修正 computed `binding`／不存在的 `ocr` helper；build＋focused tests 可跑 |
| Short end-date album segmentation | `yyyy/mm/dd～mm/dd` 正確接受；保留 exact OCR text／title matching／card-local count／cross-card refusal；focused tests PASS |
| Staging stability false positive | stability duration 改以同一 final contiguous equal suffix 計算；focused regression PASS |
| V-09 attempt-01 | 8 MAJOR → in-contract 修復 |
| V-09 attempt-02 | 4 MAJOR + 2 MINOR → 修復 |
| V-09 attempt-03 | 0 MAJOR；M-1 修復於 `cf39fdc`（dispatch margin 改以 capture scale 換算）＋ record 修正 `3d74248` |
| Native composition reachability（曾為 PRIMARY_NATIVE_COMPOSITION blocker） | codex lineage：`c441477`（typed `EstablishedStateEvidence`）→ `947db18`（`establishPreSaveStates()`／`runPreflight()`）→ `c7eb3f99`（`LiveCompositionFactory`＋`ProductionObservationSource` 接入 CLI）→ `8528ce5`（Phase B eligibility arming）→ `e407565`（post-Save-All composition）→ `0d1cdb5`（Phase A publisher）；全程 R4 C2–C7 契約未變 |
| V-09 attempt-04（fresh 複審收束） | 3/3 reports PASS、0 MAJOR；已入 `815e9f1` |

### 7.2 兩層根因（Stage 06 decision 的核心結論）

- **契約層（已封閉）**：舊 escalation 是 **stale slice**（luna worktree @ `9cbaa11`）。同一 `TASK_ID`、同一 plan/handoff 的 codex lineage 早已解掉其 cited root causes；`PLANNER_REPLAN` 被 FALSIFIED（無需改 C2–C7 語意）。
- **流程層（真病根）**：同一 `TASK_ID` 散在 3 個 worktree、沒有單一 controller；已解問題被重複升級（identity discipline defect，非架構缺陷）。V4.3.1 的對策＝identity preflight、blocker fingerprint、單一 authority tree、convergence budget。

### 7.3 Budget 記帳（硬性；不得重置）

- `PRIMARY_NATIVE_COMPOSITION`：**3/3 exhausted**，以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉。**不得重置、不得第 4 次 composition attempt**（換 model／session／branch／prompt 都不算重置）。
- `BUDGET_EXTENSION +2` 僅限 **distinct** fingerprint `V09_A4_FRESH_VERIFICATION_INCOMPLETE`（different surface／different acceptance）；其 `STOP_AFTER` 已於 `815e9f1` 達成，extension 已收束。
- 未來任何新 blocker 執行前必須先回答：falsifiable hypothesis？new information source？distinguishing result（A 結果怎麼走？B 結果怎麼走？）。答不出就不應執行。

### 7.4 Escalation packet（durable）

`escalations/attempt-01/`：

| 檔案 | SHA-256 |
|---|---|
| `escalation.md` | `5bcbd72c718384d96fab9d69a4d272bf4c6bb210ba56a3e5ba7513063060a367` |
| `context.json` | `ae2081adb327c90fb421c1855cc65468c23f22848ad5bf979f03d2f40a69b8b1` |
| `decision.md`（`ESCALATION_DECISION: IMPLEMENTER_FIX`；G1–G6 PASS） | `e2fc4a288aa6ef60848729f3a05f98ee624855808a0efdac1a66cf022fcf54d9` |
| `stage-result-06.json` | `e92e4c62d1ca3eaf9aba9b5c99c93b09d8ad66e4351b7dcd5a762c84376b3061` |
| `PROVENANCE.md` | `9abf3ab90f7604b77fa792d085af3ddec4f3cf0295910bf44bbe33ce163806ec` |

---

## 8. V-09 驗證證據（現行有效）

### 8.1 attempt-04（fresh 複審；bindings head `cf39fdcc…ff1`、digest `6734dda5…a686`；全部 `bindings_verified: PASS`）

| 報告 | SHA-256 | 結果 |
|---|---|---|
| `v09/attempt-04/01-perception-geometry.md` | `d49a8212ee53db766bc3cddfbb7bdbf262e53df375900a57ec7edbc680ac6e3e` | PASS；0 MAJOR / 0 MINOR / 4 INFO；7 claims VERIFIED |
| `v09/attempt-04/02-timing-automation.md` | `c8c52adede4ffeb0b5ea3a08649b2ddea3491548b4892c6e8dd69332c1ed5a6d` | PASS；0 / 0 / 4；11 claims VERIFIED |
| `v09/attempt-04/03-transaction-history.md` | `063330fa39eeb168b3815f1009a5fada7d78012f90b33e15a67baeb74f4450ba` | PASS；0 / 0 / 6 |
| `v09/attempt-04/bindings.json` | `81d9ea21f567d28cfd89aec773202a92c61a4974dd4f059db103bc7a705eb7a7` | 48 paths、bindings 全 PASS |

attempt-01/02/03 的證據未作為 attempt-04 的 proof。

### 8.2 離線／deterministic 證據（cf39fdcc / digest `6734dda5…a686`，已入 commit）

- build `a46`；focused `a47` 88/0；full suite `a48` 242/0（0 skipped）
- adversarial `a50`/`a51`：27 tests × 2 runs PASS
- replay `a52`/`a53`：20/20 fixtures × 2，byte-identical，SHA-256 `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261`
- provenance `a54` PASS；frozen artifacts 9/9 re-hash PASS
- CLI refusal fixture `cli-refusal-20260929T0807`：77/77/77/64/77 且 zero side effects

**注意**：以上全部是 offline/deterministic evidence；不是 real LINE evidence、不是 GUI acceptance、不是 Phase A/B、不是 full backup success。不得冒充 production completion。

---

## 9. Git／遠端／PR／現場狀態

- 已落地：`815e9f1`（HEAD；「land the V-09 attempt-04 verification (0 MAJOR) and the Stage 06 decision (IMPLEMENTER_FIX)」；10 files +764/−3；訊息含 INTENT / WHAT WAS DONE / ROOT CAUSE / BUDGET / NEXT STEPS / NOT DONE）。前後關鍵 commit：`5ed7106`（bind attempt-04 to M-1 tree）、`c945f04`、`3d74248`、`cf39fdc`（M-1 repair）、`0d3149b`。
- 事實核對：`git diff cf39fdcc 815e9f1 -- rev28` 為空 → 產品樹自 `cf39fdcc` 起 byte-identical。
- PR #1（draft）head 固定於 `rev28-prelive-finalization @9cbaa11`，無法承載後續 commits。待決選項（**尚未執行，由使用者決定**）：
  - C：從 `v43-ab/codex-rev28` 開新 draft PR → `master`，標註 supersedes #1。
  - D：關閉 PR #1（draft、head 固定，關閉不刪分支）。
- luna worktree 11 檔唯一副本（見 §1.1）：禁止破壞；snapshot 需使用者同意。
- Harness orchestrator：`~/.codex/tools/task-orchestrator.py` 對本 task 尚無 controller `state.json`，實測回應 `STATE_RECONCILIATION_REQUIRED`。在完成 reconciliation 前，不得自動 `start` 產生第二套 state；routing truth 以 task 目錄內最新 machine-readable Stage result 為準（現為 `v09/attempt-04`＋`escalations/attempt-01/stage-result-06.json`）。

---

## 10. 尚待解決事項與下一步（依序）

**P0（唯一真實外部 gate）：Phase A 前置**

1. 使用者完成 §11 的唯一動作，並通知 Agent「準備好了」。
2. Agent 先取得使用者對「本次 read-only Phase A run」的明示一次性授權（`HUMAN_AUTHORIZATION_REQUIRED` 為此用途），再以 fresh runID 執行 `rev28ctl live-preflight --config <json> --one-shot-authorization <json>`：零不可逆，產出 Phase A per-condition `PASS/FAIL/UNKNOWN`＋raw manifest。Phase A 期間 `Save All intent/attempt = 0`、`destination confirmation intent/attempt = 0`。
3. Phase A PASS → 依 canonical 契約進入後續合法 routing。若 FAIL/UNKNOWN：不得 retry/猜測；回報並依契約裁決（必要時以**新 fingerprint**再走 Stage 06）。
4. Phase B 需要**當前 run 的 one-shot human authorization**；Phase B 完成後由 fresh **Stage 05** 從 disk 獨立重算，才可能達成 `DUPLICATE_CONTENT_CONFIRMED` 並在 `result.md` closure。

**P1（可並行、需使用者決定）**：PR 方案 C/D；luna 11 檔 snapshot；orchestrator reconciliation。

---

## 11. 人類唯一必要動作（現在）

> 解鎖 Mac（如需要）→ 登入 LINE（`jp.naver.line.mac`）→ 進入群組「旻謙允禎成長日記」（禎 U+798E）→ 把相簿「2024/05/13～05/17」所在的相簿 surface 帶到可被觀察的狀態 → 告訴 Agent「準備好了」；當 Agent 請你確認進行本次 read-only preflight 時，給予一次性同意。

不要點 `Save All`、不要打開存檔 chooser、不要預先開 ellipsis 選單；其餘 reversible 導航由 Agent 依契約與授權處理。LINE 已開著可保持，不需特地關，也不要在未授權時繼續操作。

若後續 Agent 需要新的一次性 GUI 授權、Phase A 授權或 Phase B authorization：必須 STOP，輸出 `HUMAN_AUTHORIZATION_REQUIRED` 或 `EXTERNAL_BLOCKER`，且一次只要求一個動作；不得 polling、不得沿用舊授權、不得把 `/goal` 當 GUI authorization。

---

## 12. 禁止事項（合併清單）

- Git：`reset --hard`、`clean`、automatic stash、`rebase`、force push、覆寫任何 dirty/untracked、動 `rev28-prelive-finalization`、merge/cherry-pick A/B branches 拼版本。
- Execution：第 4 次 `PRIMARY_NATIVE_COMPOSITION` attempt；重開 A/B competition；未經授權的 `live-preflight`／`live-execute`；任何 LINE GUI 操作或 album-list prepositioning（在 §11 完成前）；`Save All`；destination confirmation；polling／retry／舊授權。
- Budget／流程：換 model／session／branch／prompt 不重置；`exit 0 ≠ semantic PASS`；worktree dirty 或 branch 不一致不得自動破壞現場（→ `STATE_RECONCILIATION_REQUIRED`）。

---

## 13. 檔案索引與閱讀順序（新 Agent 開場 10 分鐘）

1. 本文件（navigation）
2. `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`（R4 契約；SHA-256 `05413807…4c1b`）
3. 同目錄 `handoff.md`（canonical Stage 03 執行契約；SHA-256 `67fc16a6…7a33`）
4. 同目錄 `progress.md`（讀最後三段：attempt-03 reviews／attempt-04＋Stage 06／最新 status）
5. 同目錄 `execution.md`（讀末段 attempt-04 記錄）
6. `escalations/attempt-01/`（§7.4 五檔＋hashes）
7. `v09/attempt-04/`（§8.1 四檔＋hashes）
8. `Line_backup/evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json`（SHA-256 `3c932d8c…1bc2`）
9. `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`（baseline source）
10. Harness：`~/.codex/AGENTS.md`、`~/.codex/policies/convergence-escalation.md`、`~/.codex/schemas/stage-result.schema.json`

---

## 14. 常用指令（read-only 驗身分用）

```bash
# 身分
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup status --short --branch
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup log --oneline -8
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup worktree list
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup ls-remote --heads origin

# 契約 hash
cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260925-0647-01-rev28-native-closed-loop
shasum -a 256 plan.md handoff.md

# baseline 完整性（唯讀）
find /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 -type f | wc -l          # 57
find /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 -type f -print0 | xargs -0 stat -f %z | awk '{s+=$1} END {print s}'  # 17924900

# orchestrator（只查，不 start）
python3 ~/.codex/tools/task-orchestrator.py status --task T20260925-0647-01-rev28-native-closed-loop
```

---

## 15. 與 2026-09-29 版 rev28 交接的差異（避免被舊指示誤導）

| 舊版（2026-09-29 版） | 現況（2026-09-30） |
|---|---|
| `STATE: ESCALATED`；下一步＝ Stage 06 | Stage 06 已完成（`IMPLEMENTER_FIX`）；`STOP_AFTER` 達成於 `815e9f1`；無 open escalation |
| §16 核心問題（IMPLEMENTER_FIX vs PLANNER_REPLAN） | 已回答：`IMPLEMENTER_FIX`；C2–C7 無需 replan（H2 FALSIFIED） |
| §7 budget：3/3、不得第 4 次 | 仍 3/3，以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉；禁止第 4 次不變 |
| §18/§19「不要主動操作 LINE」 | 仍有效；直到 §11 唯一人類動作完成 |
| §23 Stage 05 定義 | 仍有效 |
| §25 開場順序 | 以本文件 §13 取代（原則相同） |

---

## 16. 交接結論（一句話）

> 不要重新解這個專案。產品樹凍結於 `cf39fdcc` / digest `6734dda5…a686`；V-09 attempt-04 0 MAJOR 已收束入 `815e9f1`（已推）；`PRIMARY_NATIVE_COMPOSITION` 3/3 以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉。離線工作已到極限；唯一剩下的是外部 Phase A 前置（使用者登入 LINE＋目標相簿 surface），之後以 fresh runID 跑 `live-preflight`。在該條件成立前：**正確的 STOP 就是成功。**
