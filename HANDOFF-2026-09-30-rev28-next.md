# HANDOFF — LINE Backup Rev28（2026-09-30 rev3｜prompt-first＋Harness V4.3.1 整合）

> 給新對話的接手 Agent：**先讀 §0 的 Prompt，並依它執行**；本文件其餘章節是它引用的完整上下文。
> 本文件是 navigation + status snapshot，**不是** canonical 契約，不取代
> `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md` 與同目錄 `handoff.md`。**不要覆寫它們。**
> 核心原則：**不要從頭探索；不要重跑已證明事項；不要重置 blocker budget；不要在應該停止的位置繼續燒 token。**
> Updated: 2026-09-30 14:05（Asia/Taipei）rev3：
> (a) 交辦 Prompt 置頂；(b) 併入 **Phase A attempt-01 已 fired 並 REFUSED** 的最新狀態；
> (c) 更新本地 HEAD 與交付時工作樹現況；(d) append 本檔 rev2 與 `phase-a/` evidence（docs/records-only commits）；
> (e) **整併 Harness V4.3.1 全域運作邏輯（新增 §7；其後章節全部重編號）**；(f) 六個正交狀態正規化為 harness canonical 值（§5／§7.5）。

---

## 0. 交辦 Prompt（把下面整段貼給接手 Agent；或整份文件一起貼）

```text
你是 T20260925-0647-01-rev28-native-closed-loop（CRITICAL）的接手 Agent。這個任務已做完離線實作
與全部複審，只剩「真實 Phase A（read-only 觀察）」的外部前置與 attempt-02。不要重新解這個專案。

【第 0 步｜讀與核對（不符＝STATE_RECONCILIATION_REQUIRED，停止並回報）】
1. 讀 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/HANDOFF-2026-09-30-rev28-next.md 全文（§0＝本 Prompt；
   §7＝Harness V4.3.1 運作邏輯；§17＝指令）。
2. 讀 harness process authority：`~/.codex/AGENTS.md`、`~/.codex/policies/workflow-routing.md`、
   `~/.codex/policies/convergence-escalation.md`；本 task 適用摘要見 §7（controller／status／收斂規則）。
3. 機械核對（指令見 §17）：
   - repo /Users/hsiaojohnny/Documents/ChatGPT/Line_backup；branch `v43-ab/codex-rev28`；
     本地 HEAD 應為 `ce52103` 或之後的 docs/records-only commit（本 HANDOFF rev2／rev3 與 phase-a evidence
     可能已 commit／push；origin 同步或落後皆屬正常，一律以實測為準）。
   - 產品樹必須仍是 `cf39fdcc…`（digest `6734dda5…a686`；`git diff cf39fdcc HEAD -- rev28` 必須為空）。
   - plan.md SHA-256 = `05413807…4c1b`；canonical handoff.md SHA-256 = `67fc16a6…7a33`。
   - working tree 為 clean、或顯示本 HANDOFF 檔 modified／`phase-a/` untracked（未及入庫），皆屬正常
     （見 §2.3／§12）；不要 reset。
   - 若只有這些差異、其餘不符：停止，輸出 STATE_RECONCILIATION_REQUIRED，不得自行修 Git。

【第 1 步｜已知事實（不要再論證）】
- PRIMARY_NATIVE_COMPOSITION 3/3 → RESOLVED_BY_SUPERSEDING_LINEAGE：禁止第 4 次 attempt、
  禁止重開 A/B competition、禁止任何新 implementation attempt；換 model/session/branch/prompt 不重置。
- 離線實作與驗證已收束（V-09 attempt-04：0 MAJOR；產品樹凍結 cf39fdcc）。
- Phase A attempt-01 已於 2026-09-30 10:30 fired 並被 fail-closed REFUSED（exit 77，
  `targetWindowNotUnique(found=2)`）；未進入觀察、未產出 per-condition report、零不可逆（0/0/0）。
  證據：`.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/phase-a/attempt-01/RUN-20260930-103002-01/`（§10）。
- 目前 blocker fingerprint：`PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)`（環境前置，非 code defect）。
- orchestrator 無 state.json（STATE_RECONCILIATION_REQUIRED）；只准 `status`，不准 `start`（§7.4）。

【第 2 步｜先做環境確認，再決定走哪條路】
向使用者確認：「LINE 是否已登入、目標相簿 surface 是否就緒、且只有一個 LINE 視窗？」
然後自己做**唯讀** probe（§17 視窗盤點；不觸碰 GUI）：數 layer-0 on-screen 的 LINE 視窗數。
- 若 probe ≠ 1（0 或 ≥2）：
  - 不執行 live-preflight、不請求授權、不 polling、不 retry。
  - 只告訴使用者需要的那一個動作：
    * 0 個視窗：啟動／登入 LINE，進入群組「旻謙允禎成長日記」（禎 U+798E），把相簿
      2024/05/13～05/17 的卡片帶到看得到的位置（捲到出現即可；不要點開、不要開 ellipsis 選單），
      視窗擺前景、單一螢幕、不被遮住。
    * ≥2 個視窗：關閉多餘的 LINE 視窗，只留一個主視窗（內容維持在上述 surface）。
  - 然後停止；使用者回報完成後重新 probe，通過才進第 3 步。
- 若 probe == 1 且使用者確認就緒：進第 3 步。

【第 3 步｜Phase A attempt-02（只有 probe == 1 才允許）】
1. 先請使用者對「本次 read-only Phase A run」給**新的**明確一次性授權（舊授權已用於 attempt-01；
   不得沿用、不得推定）。提醒：開始後 1～2 分鐘不要動滑鼠／鍵盤、不要切換 App、Mac 不休眠／鎖屏。
2. 準備新的 fresh runID 與 run 目錄（`phase-a/attempt-02/RUN-<timestamp>-01/`），重新產生 config
   （可抄 attempt-01 的 config.json 結構，但 runID／路徑／targetPID 必須重新觀測；chooser binding
   三欄與 frozen files 維持；不得重用 attempt-01 的 ledger／授權檔，也不得手動編輯它們）。
3. 以凍結產品樹建置的 binary 執行一次：
   `rev28ctl live-preflight --config <new config> --one-shot-authorization <new one-shot-authorization.json>`
4. 零不可逆：Save All intent/attempt = 0、destination confirmation intent/attempt = 0；
   不點 Save All、不開 chooser；timeout／ambiguous／stale／identity mismatch → observe-only 停止。
5. 結果處置：
   - PASS：依 canonical 契約進入後續合法 routing（真實 chooser 仍留 Phase B；不得自行推進 Phase B）。
   - REFUSED／FAIL／UNKNOWN：不 retry、不猜測；寫下 outcome 與 counters；依收斂契約決定下一步
     （同 fingerprint 的重複失敗會消耗 budget；不得換 model/session/branch/prompt 重置）。
6. 把記錄 append 到 progress.md／execution.md；`phase-a/` 證據目錄 append-only，不改寫既有檔案。
   attempt-01 截至 rev2 撰寫時尚未回填 progress.md／execution.md，請一併補記。

【硬禁止】
- git reset --hard／clean／stash／rebase／force push；動 `rev28-prelive-finalization`；覆寫任何
  dirty/untracked（含 `phase-a/`）；merge 或 cherry-pick A/B branches。
- 第 4 次 PRIMARY_NATIVE_COMPOSITION attempt；Phase B；Save All；destination confirmation；
  未取得明示授權就執行 live-preflight；由 Agent 自行操作 GUI（授權的 Phase A run 內、契約允許的
  reversible 步驟除外）；album-list prepositioning。
- 使用 `~/Library/Application Support/LineNativeAXGUIBridge`（舊世代殘留 LaunchAgent）或任何
  非 rev28 契約的 AX bridge／替代 authority；手動編輯 ledger／goal slot／授權檔。
- luna／deepseek worktree 僅可唯讀作歷史 evidence。`exit 0 ≠ semantic PASS`。

【回報格式】
- 一句話：現況＋你做了什麼＋下一步；附：probe 數量、runID、run 目錄、counters（0/0/0 或實際值）、
  下一步唯一動作（若 STOP）。不得宣稱未實際觀察到的 PASS。
```

---

## 1. 一句話現況

離線工作全部收束（產品樹凍結 `cf39fdcc` / digest `6734dda5…a686`；V-09 attempt-04 複審 0 MAJOR 已 commit）。
**Phase A attempt-01 已 fired（2026-09-30 10:30）：fail-closed REFUSED（exit 77，`targetWindowNotUnique(found=2)`）**，
原因是當時 LINE 同時存在 2 個 on-screen layer-0 視窗；未進入觀察、未產生任何 Phase A per-condition 證據，且**零不可逆（0/0/0）**。
截至 2026-09-30 13:42 唯讀盤點：**LINE 目前已不在執行中（0 個視窗）**。
下一步＝使用者把 LINE 帶回「已登入＋目標相簿 surface 可見＋恰好一個視窗」的狀態；Agent 以唯讀 probe 確認 =1 後，
取得**新的一次性授權**並以 **fresh runID** 跑 attempt-02。在此之前不碰 GUI、不重跑、不重置任何 budget——**正確的 STOP 就是成功**。

---

## 2. 專案與 Task 身分（先核對，再行動）

| 項目 | 值 |
|---|---|
| TASK_ID | `T20260925-0647-01-rev28-native-closed-loop` |
| Task class | `CRITICAL` |
| Harness | V4.3.1（STATUS_CONTRACT v2、CONVERGENCE_CONTRACT v1） |
| 主要 repo | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` |
| 本地 branch / HEAD | `v43-ab/codex-rev28` @ `ce5210389eb983c200f4360cae443d58e9233ab5` 或之後的 docs/records-only commit（本檔 rev2 與 `phase-a/` evidence 已於交付時 commit；是否 push 以實測為準） |
| origin 對應 ref | `refs/heads/v43-ab/codex-rev28` = `815e9f1b02ac3f74539fae3814e52bf914547850`（本地領先 1） |
| canonical Plan | `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`｜SHA-256 `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b`（R4；review attempt-07 `PLAN_APPROVED`） |
| canonical Stage 03 Handoff | 同目錄 `handoff.md`｜SHA-256 `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` |
| approved starting checkpoint | `9cbaa1141595acb538d4672066072d2b8ffb7065`（branch `rev28-prelive-finalization`；**禁止前移**） |
| 產品凍結樹 | `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`；`rev28/` 自該 commit 起未變（`git diff cf39fdcc HEAD -- rev28` 必須為空）；`cf39fdcc..HEAD` 另有 `.agent/` 記錄與根目錄 HANDOFF 文件（docs-only） |
| implementation digest | `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`（48 paths = 45 Swift + `Package.swift` + 2 tools；`ReviewedImplementationDigest` 計算，Python replica 一致） |

### 2.1 Worktree 現場（2026-09-30 實測）

| 路徑 | branch | HEAD | 狀態 |
|---|---|---|---|
| `Documents/ChatGPT/Line_backup` | `v43-ab/codex-rev28` | `ce52103` 或之後 | authority tree；見 §2.3 工作樹現況 |
| `Documents/ChatGPT/Line_backup-ab-deepseek` | `v43-ab/deepseek-rev28` | `472c283`（已推） | clean；`EXTERNAL_BLOCKER` 歷史（locked session） |
| `Documents/ChatGPT/Line_backup-ab-luna` | `v43-ab/luna-rev28` | `9cbaa11` | **11 個 dirty/untracked（唯一副本，禁止破壞）** |

- luna 現場 11 檔＝6 modified（`execution.md`、`StructuralLocators.swift`、`FrameCapture.swift`、`StagingVerifier.swift`、`StagingVerifierTests.swift`、`StructuralLocatorsTests.swift`）＋5 untracked（`escalations/`、`evidence/`、`progress.md`、`SameFramePerception.swift`、`SameFramePerceptionTests.swift`）。這些內容不存在於任何 commit；如需 snapshot 或清理，先取得使用者明確同意。
- 身分不一致（worktree / branch / HEAD / Plan SHA / Handoff SHA 與本表不符）＝`STATE_RECONCILIATION_REQUIRED`：停止並回報，**不得自行修 Git**。

### 2.2 origin refs（2026-09-30 實測）

| ref | SHA |
|---|---|
| `refs/heads/master` | `9db32f68d271272fd8ac5a6337522534e88d9ab2` |
| `refs/heads/rev28-prelive-finalization` | `9cbaa1141595acb538d4672066072d2b8ffb7065` |
| `refs/heads/v43-ab/codex-rev28` | `815e9f1b02ac3f74539fae3814e52bf914547850` |
| `refs/heads/v43-ab/deepseek-rev28` | `472c283cdda283628ca42e59390c44d921275f4c` |
| `refs/heads/rev28-ci-prelive-hardening` | `a572ec58f506100ae895c21891db8595aaadd5d6` |
| `refs/heads/harness-v4.3-validation` | `7f2a3104e03ade4f32c45647cbb58d291ab74576` |

### 2.3 工作樹現況（clean／modified 皆屬正常，不要 reset）

| 路徑 | 狀態 | 說明 |
|---|---|---|
| `HANDOFF-2026-09-30-rev28-next.md` | clean 或 modified | 本檔（rev3：prompt-first＋Harness 整合）。clean＝已 commit；modified＝相對最後一次 commit 有差異（若內容仍是 rev3，屬正常，不要 reset） |
| `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/phase-a/` | 已 commit 或 untracked | Phase A attempt-01 證據（§10）；**append-only，禁止改寫／刪除** |
| 其餘（含 `rev28/`） | clean | 產品樹凍結；`git diff cf39fdcc HEAD -- rev28` 必須為空 |

---

## 3. 使用者真正要解決的問題（產品目標）

最終目標不是「讓測試變綠」，而是：從 macOS LINE App（`jp.naver.line.mac`）精確定位群組：

`旻謙允禎成長日記`

> 注意：`禎 = U+798E`。不得與 `楨 = U+6968` 混淆、正規化、合併或猜測為同一群組。

目標相簿：`2024/05/13～05/17`。最終需建立一份新的 staging backup；真正成功只能由 filesystem 與獨立 Stage 05 evidence 證明。

### 3.1 Primary Outcome＝唯一成功狀態 `DUPLICATE_CONTENT_CONFIRMED`

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

## 4. Production 不可逆動作契約（ceiling）

- 真正成功的 production run 最多：`Save All dispatch = 1`、`destination confirmation = 1`。這是天花板，不是必須消耗的 quota。
- 任何 irreversible intent 一旦建立即視為消耗，即使 effect 是 `UNKNOWN`。
- 不得因為沒看到效果、session 重開、換模型、換 run、換 TASK wording、換 worktree 而取得第二次機會。
- `UNKNOWN` irreversible effect：**永遠不能 blind retry**（只能 observe-only）。
- Human authorization 不能把 mechanical `FAIL` 變成 `PASS`。
- Phase A attempt-01 已在「進入觀察前」被拒絕，未建立任何 irreversible intent；0/0/0 仍成立。

---

## 5. 目前狀態（2026-09-30 14:05；routing truth＝最新 valid Stage result／run artifact；欄位語意見 §7.5）

```text
STATE: PHASE_A_ATTEMPT_01_REFUSED_PRECONDITION（implementation frozen cf39fdcc；無 pending code work）
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: COMPLETE
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: INCOMPLETE
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS
PHASE_A_STATUS: attempt-01 FIRED 2026-09-30 10:30 → REFUSED (targetWindowNotUnique(found=2)); attempts used = 1; next = probe==1 → attempt-02（fresh runID + fresh one-shot authorization）
PHASE_B_STATUS: FORBIDDEN_AB_EVALUATION
irreversible counters: Save All 0 / destination confirmation 0 / irreversible intents 0
scope: ENVIRONMENT（使用者動作可解；見 §9.2／§14；blocker 形狀見 §7.5）
```

欄位判讀（皆為 harness canonical 值，不得改寫成其他字樣，§7.5）：
`IMPLEMENTATION_STATUS: COMPLETE`＝pre-Phase-A scope 的實作面已完成（V-09 attempt-04 0 MAJOR；無 pending code work）；
`REQUIRED_VERIFICATION_STATUS: INCOMPLETE`＝已有有效離線證據、但要求的真實證據（Phase A per-condition）尚未產生。
attempts used = 1 表示 Phase A 真實世界執行已用掉 1 次；**先修環境前置再跑**，不得在無新資訊下盲目重耗（§7.6）。

為什麼不是 `DONE`：Primary Outcome 尚未達成（尚未有任何真實 backup run）；CORE 未 run；Phase A per-condition 證據未產生；Stage 05 從未執行（DONE 契約見 §7.5）。

---

## 6. 架構與關鍵邏輯（接手必讀）

產品程式碼在 `Line_backup/rev28/`：`Sources/Rev28Core/`、`Sources/rev28ctl/`、`Tests/`。

### 6.1 模組與職責（實際檔案）

| 模組 | 代表檔案 | 職責 |
|---|---|---|
| Observation | `Observation/NativeObservationSession.swift` | 同幀 observation／identity／geometry 證據鏈；menu/addressable bounds 必須落在 retained frame 內 |
| Composition | `Composition/LiveComposition.swift`、`ProductionObservationSource.swift`、`ComposedNativeAdapter.swift`、`PostSaveComposition.swift`、`PhaseAEvidence.swift` | 組裝 CLI→engine 的 native path（typed evidence＋adapters）；Phase A 報告 builder |
| Transaction | `Transaction/LiveExecutionEngine.swift`、`PersistentTransactionOwner.swift`、`IntentLedger.swift`、`StateEvidence.swift`、`PhaseBEligibility.swift`、`ReviewedImplementationDigest.swift`、`GoalSlot.swift`、`FilesystemTripwireJournal.swift`、`TripwireAttribution.swift`、`ReviewedBuildState.swift` | 單一 durable owner/ledger；phase entrypoint；budget 記帳；implementation digest |
| Policy | `Policy/ExecutionPolicy.swift`（`LiveDispatchBudget` 等） | budget 與 policy 規則 |
| Actuation | `Actuation/QuartzActuator.swift`（含 `GatedQuartzActuator`）、`AXDriver.swift` | guarded dispatch、per-primitive accounting、click 前重新驗證 |
| Perception | `Perception/StructuralLocators.swift`、`AlbumEllipsisLocator.swift`、`OcrEngine.swift` | 短日期 `yyyy/mm/dd～mm/dd` 分段、card-local count、cross-card refusal |
| Identity | `Identity/AXWindowIdentitySelector.swift`、`WindowIdentity.swift` | AX 讀取綁定 CGWindowID（絕不用 `windows[0]`）；**目標視窗必須唯一** |
| Sensor | `Sensor/FrameCapture.swift`、`WindowSensor.swift`、`RunEpochAuthority.swift` | 擷取、視窗盤點、epoch authority |
| Chooser | `Chooser/FolderChooserDriver.swift`、`ChooserAffirmationPredicate.swift` | Go to Folder 逐 primitive 記帳、panel 唯一性 |
| Verification | `Verification/StagingVerifier.swift`、`BaselineVerifier.swift` | staging 完整性／穩定性；baseline 驗證 |
| Postcondition | `Postcondition/PostconditionMonitor.swift` | postcondition 監測 |
| CLI | `rev28ctl/main.swift`（factory `:282-317`；usage `:496`）、`HarnessCalibration.swift`、`FolderChooserDriver.swift`、`EvidenceRun.swift`、`QuartzActuator.swift`、`RestartFixture.swift` 等 | `live-preflight`／`live-execute`／`harness-calibrate`／`restart-child` |

### 6.2 Phase A 執行路徑（現行 CLI 真實行為）

1. `rev28ctl live-preflight --config <json> --one-shot-authorization <json>`
2. `LiveCompositionFactory.make(...)`（`main.swift:282`）組裝：`ProductionObservationSource` + `ComposedNativeAdapter` + `NativeObservationSession` + `PersistentTransactionOwner` + `GatedQuartzActuator`
3. 目標視窗 identity 必須唯一（否則 `targetWindowNotUnique(found=N)` → exit 77、fail-closed，attempt-01 即此情形）
4. `composition.engine.runPreflight()`（`LiveExecutionEngine.swift:264`，零不可逆）→ `observePreDispatchContext`（≥10s 環境取樣、tripwire 無 gap）
5. 寫 `preflight-outcome-<stamp>.json`；`PhaseAEvidenceBuilder.inspect` 產出 per-condition `PASS/FAIL/UNKNOWN` 報告＋raw evidence manifest
6. 真實 LINE chooser 在 Phase A 一律標記 deferred，**永不記為 PASS**（Phase B runtime gate）

`live-preflight` 的 config 需含 chooser calibration binding（`chooserCalibrationPath`／`chooserPredicateSHA256`／`chooserCalibrationSHA256`）；CLI 會重讀、hash 驗證 frozen bytes、decode、`ChooserProductionPredicate.derive`，非 process-stable v2 即 named refusal。

### 6.3 關鍵語意（不得在 implementation 內私自變更）

- 單一 durable authority：owner + ledger（`PersistentTransactionOwner`＋`IntentLedger`）。`reserveSaveAll` 要求耐久 `eligibility.phaseB` 記錄＋`currentState == .saveAllLocated`；`reserveDestinationConfirmation` 要求 `.destinationPrepared`。
- Phase separation：Phase A 零不可逆；Phase B eligibility 全 predicate PASS 才 arm。
- Irreversible dispatch boundary＋per-primitive accounting（每個 posted primitive 逐筆記帳；panel/field 非唯一即 fail closed）。
- 下載觀察上限 10 分鐘；stability 需 ≥3 個 equal snapshots 且跨度 ≥4 秒（以同一 final contiguous equal suffix 計算）。細節以 canonical `handoff.md` 為準。
- Fail-closed：任何不確定（timeout／ambiguous／stale／identity mismatch／baseline change／chooser ownership mismatch／crash after intent）→ 拒絕或 observe-only，絕不猜測或 retry。
- Stage 05 必須從 disk / raw evidence 獨立重算；不得引用 Stage 04 自寫的 PASS 字串。
- `exit 0 ≠ semantic PASS`。`progress.md` 不得凌駕 Stage result；`result.md` 不得自己創造 PASS。

### 6.4 C1–C7 核心工作契約（`plan.md`，行號為 plan 內位置）

- C1（`:105`）：恢復 diagnostic execution、保留 identity rules
- C2（`:111`）：單一 safety-critical orchestration
- C3（`:119`）：observation authority（同幀＋geometry provenance）
- C4（`:132`）：單一 durable transaction authority（ledger／budget／reservation）
- C5（`:148`）：guarded actuation（dispatch readiness、click 前重驗）
- C6（`:156`）：actual chooser 與 destination（逐 primitive 記帳）
- C7（`:170`）：filesystem authority 與 finalization（tripwire、post-dispatch gap、staging 證明）

---

## 7. Harness V4.3.1 全域運作邏輯（整合自 `~/.codex`；2026-09-30）

> 本節把 Codex 全域 harness 的運作邏輯整理成本 Task 適用的 process authority。它是**規範**：與本文件其他章節
> 衝突時，canonical 契約（`.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`、`handoff.md`）
> 與本節所列的 harness 政策優先。依 progressive disclosure（`policies/context-budget.md`）：接手 Agent 先讀
> §7.1 列出的核心檔案即可，其餘政策按觸發載入，不要把全部歷史／transcript 預載進 context。

### 7.1 版本與檔案地圖（`~/.codex/`；存在性與 hash 已於 2026-09-30 實測）

| 檔案 | 角色 | SHA-256 |
|---|---|---|
| `AGENTS.md` | 全域契約：`HARNESS_VERSION 4.3.1`／`STATUS_CONTRACT_VERSION 2`／`CONVERGENCE_CONTRACT_VERSION 1` | `142e803b9a81cd0ad92bc5d5499e4490fc94634ed1b19d15700daeea11e41a43` |
| `policies/workflow-routing.md` | **canonical**：task class、status 語意、blocker、Stage 04/05/06 routing、closure、baseline、waiver | `ee9c9faf6d5fb0f3cd3dd52270ad9c021e930c3a9daf141ca5c48f8e79bcfadc` |
| `policies/convergence-escalation.md` | Stage 04 收斂：material attempt、blocker fingerprint、budget、escalation packet、Goal lifecycle | `6f459912bfc3d1ce367b01ea20f3099572c5aeac4f876e63a34c05dfdda5a81d` |
| `schemas/stage-result.schema.json` | 所有 role 的唯一輸出 schema（§7.4） | `4414816825c94cfbab4ca9755853bf81338e587a4e96884609522b9eb775a6d7` |
| `tools/task-orchestrator.py` | deterministic controller：`start`／`status`／`resume`；state 在 `~/.codex/task-orchestrator/tasks/<TASK_ID>/state.json` | `a6897ae29aa2c8da97243541f17ef8bc6c87c7a7bd2df36fc329f6ba033521b0` |
| `tools/harness-verify.sh` | harness 結構自驗；成功輸出 `HARNESS_VERIFY=PASS`＋`TASK_ACCEPTANCE=NOT_EVALUATED`（**只證 harness 結構，不證 task PASS**） | `9db14fd18721e0f3e5886ef8bb4270212be599f76338cf80e53f1b2f39eab3ba` |
| `tools/harness-status.sh` | `status` 包裝：`harness-status.sh <TASK_ID> [REPO]` | `67b179cec85ac33ba5091bce2342e140e6e4016f9ecab30ab34ee6f848d5a808` |
| `prompts/01a、01b、02、03、04、05、06` | Stage 01–06 role prompts（能力角色定義，與 model 名稱無關） | 見檔 |
| `policies/` 其餘 13 份 | context-budget、data-migration、debugging-recovery、dependencies-contracts、git-change-hygiene、goal-alignment-design-economy、high-risk-change、model-routing、performance-concurrency、plan-review-gate、security-privacy、testing-verification、ui-accessibility | 按需載入 |

若 hash 不同＝harness 已更新：以**現行版本**為準；這是外部工具，不得為了對齊本文件而改動它。

### 7.2 Task routing（QUICK／STANDARD／CRITICAL）

- `QUICK`：小、低風險；可略過 Plan Review，但仍保留 required gates 與 Acceptance。
- `STANDARD`：多檔／整合／重構／debug；Plan＋Handoff＋獨立 Plan Review＋獨立 Acceptance。
- `CRITICAL`（**本 task**）：架構／不可逆操作／外部契約／高風險／反覆未解；獨立 Plan Review 與 Independent Acceptance **必須**。
- 本 task 的 harness 歷程（已完成、不要重跑）：Stage 01 R4 Plan → Stage 02 review attempt-07 `PLAN_APPROVED` → Stage 03 Handoff → Stage 04（多 lineage 實作）→ Stage 06 `IMPLEMENTER_FIX` → V-09 驗證 attempt-01～04（0 MAJOR）。剩下的是同一契約下的真實世界執行（Phase A/B）與 Stage 05；**不得改契約、不得重開已關閉的 blocker**。

### 7.3 Stage 與角色（固定轉換；model-agnostic）

```text
PLAN → PLAN_REVIEW（STANDARD／CRITICAL 必需）→ HANDOFF → IMPLEMENT → ACCEPTANCE → DONE
```

- 角色＝能力角色：`PLANNER｜PLAN_REVIEWER｜HANDOFF_COMPILER｜IMPLEMENTER｜HIGH_REASONING_REVIEWER｜ACCEPTANCE_REVIEWER`；換 model／provider／session 不得改契約、**不得重置 convergence budget**（`policies/model-routing.md`）。
- Stage 06 `HIGH_REASONING_REVIEWER` 只由 Stage 04/05 escalation 進入，不是必經 stage；只能裁決一條路線：`IMPLEMENTER_FIX`／`TARGETED_DIAGNOSTIC`／`PLANNER_REPLAN`／`EXTERNAL_BLOCKER`。本 task 已裁決 `IMPLEMENTER_FIX`（§9.5）。
- Stage 05 是 fresh 獨立驗收：唯讀、不得修產品碼；`FIX_REQUIRED` 會路由回 **fresh** Stage 04 run。
- persistent `/goal` 是 Stage 04 的執行機制（`AGENTS.md §5`）；本 task 先前設計的 Stage 04 `/goal` 未執行，未來是否採用由使用者決定。

### 7.4 Controller 與 machine-readable Stage result

- `tools/task-orchestrator.py` 擁有 routing；role 輸出只是 advisory，直到全部通過：schema、task/stage/role/run identity、process exit、required gates／evidence、Plan/Handoff SHA-256、實測 git identity（repository／worktree／branch／HEAD before-after／dirty files）。一個 task-scoped atomic lock 防止並行 controller。
- 每個 role 必須回傳 `stage-result.schema.json` 的**一個** JSON，required 欄位：
  `schema_version, task_id, run_id(uuid), stage, role, verdict, blocker_fingerprint, information_gain, task_class, repository, worktree, branch, head_before, head_after, plan_sha256, handoff_sha256, required_gates, required_evidence, allowed_paths, evidence, next_route, artifact_content`。
  允許的 `next_route` 含 `STATE_RECONCILIATION_REQUIRED`；`exit 0 ≠ semantic PASS`；required gate 需 `verdict: PASS`＋非空 evidence；`WAIVED ≠ PASS`；`progress.md` 只供顯示，不得凌駕 controller state／最新 valid Stage result。
- **本 task 現況（2026-09-30 實測）**：controller 沒有 `~/.codex/task-orchestrator/tasks/T20260925-0647-01-rev28-native-closed-loop/state.json`；`status`／`resume` 一律回 `STATE_RECONCILIATION_REQUIRED`。因此：
  - **不得 `start`**（會生成新 TASK_ID＝第二套 authority）、不得補造或手改 state.json；
  - routing truth＝task 目錄內最新 machine-readable Stage result／run artifact（現行：`escalations/attempt-01/stage-result-06.json`、`phase-a/attempt-01/RUN-20260930-103002-01/`、`v09/attempt-04/`）；
  - 同一 state 目錄下可能出現**其他專案／其他 task** 的 state（實測有 `TASK-20260930-140106-…`，屬使用者其他專案）：只讀本 TASK_ID，不得觸碰他人 state；
  - 若使用者之後正式讓 controller 接管本 task，才由 controller 決定 routing（先 `status`、需要時 `resume`）。

### 7.5 Status 語意（六個正交欄位）＋ 本 task 現值

永不把六欄壓成一個 `BLOCKED`／`DONE`；`DONE` 只在 Primary Outcome 達成＋實作完成＋CORE pass＋required verification pass（或 NOT_REQUIRED）＋independent acceptance pass（或 NOT_REQUIRED）＋無 hard blocker 時使用，**不得**用於 implementation-only completion。

```text
PRIMARY_OUTCOME_STATUS:       ACHIEVED | NOT_ACHIEVED | UNKNOWN
IMPLEMENTATION_STATUS:        NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | ESCALATED
CORE_ACCEPTANCE_STATUS:       NOT_RUN | PASS | FAIL | BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED | INCOMPLETE
INDEPENDENT_ACCEPTANCE_STATUS:NOT_REQUIRED | PENDING | PASS | FAIL | BLOCKED
TASK_CLOSURE_STATUS:          IN_PROGRESS | HIGH_REASONING_REVIEW_REQUIRED | READY_FOR_INDEPENDENT_ACCEPTANCE |
                              PENDING_REQUIRED_VERIFICATION | ACCEPTANCE_BLOCKED | FIX_REQUIRED |
                              REPLAN_REQUIRED | IMPLEMENTATION_BLOCKED | DONE
```

本 task 現值＝§5；scoped blocker（blocker contract 形狀，`workflow-routing.md §6`）：

```yaml
BLOCKERS:
  - id: BLK-PHASE-A-WINDOW
    scope: ENVIRONMENT
    subject: PHASE_A_TARGET_WINDOW_NOT_UNIQUE
    result: BLOCKED
    class: ENVIRONMENT_FAILURE
    task_regression_evidence: NONE
    evidence: |
      .agent/tasks/T20260925-0647-01-rev28-native-closed-loop/phase-a/attempt-01/RUN-20260930-103002-01/phase-a-outcome.md
      （exit 77；targetWindowNotUnique(found=2)；未進入觀察；counters 0/0/0）
    next_action: 使用者把 LINE 帶回「已登入＋目標相簿 surface 可見＋恰好一個視窗」（§14）
    owner: USER
    waiver_allowed: NO
```

### 7.6 Stage 04 收斂契約（mandatory；`policies/convergence-escalation.md`）

- Material attempt＝一個能改變知識或驗收的因果實驗，不是每個命令。事前記錄 `ATTEMPT_ID／BLOCKER_FINGERPRINT／HYPOTHESIS／EXPERIMENT_OR_CHANGE／EXPECTED_DISTINGUISHING_RESULT`；事後記錄 `OBSERVED_RESULT／ACCEPTANCE_DELTA／NEW_EVIDENCE／UNCERTAINTY_REDUCED／INFORMATION_GAIN`。
- Blocker fingerprint＝失敗的**驗收條件**，不是假設說詞；canonical 形狀 `STAGE／CHECK／SURFACE／EXPECTED／OBSERVED`（排除時間戳、隨機 ID、位移行號）。預算屬 `TASK_ID + BLOCKER_FINGERPRINT`，**換 model／session／worktree／prompt 都不重置**。
- 預設上限：`MAX_MATERIAL_ATTEMPTS_PER_BLOCKER = 3`；`MAX_CONSECUTIVE_NO_INFORMATION_GAIN = 2`；`A → B → A`（修復造成的震盪）立即 escalation。3 是天花板不是 quota；第 1 次就證明該升級，不必做滿 3 次。
- 只有下列才算 progress（需有證據）：`ACCEPTANCE_DELTA`／`NEW_EVIDENCE`／`UNCERTAINTY_REDUCED`／`BLOCKER_RESOLVED`。程式碼變多、重跑同結果、log 變長、換句話說的假設、A→B→A——都不算。
- Escalation 觸發（任一即停止 local implementation）：3 次未解／連續 2 次無資訊增益／A→B→A／下一步說不出 falsifiable 結果／需要改 load-bearing 契約／重複舊實驗而無新證據源。
- Escalation 產物：下一個 append-only `escalations/attempt-<NN>/`（`escalation.md`＋`context.json`）；`progress.md` 記 `STATE: ESCALATED`；正式狀態 `IMPLEMENTATION_STATUS: ESCALATED`＋`TASK_CLOSURE_STATUS: HIGH_REASONING_REVIEW_REQUIRED`；未經 Stage 06 或使用者明示，不得第 4 次 local attempt。
- Stage 06 若加預算：必須 `BUDGET_EXTENSION: +N`／`EXTENSION_SCOPE`／`NEW_INFORMATION_SOURCE`／`STOP_AFTER`（預設自動上限 +2；更大需使用者授權）。
- Goal lifecycle：`complete` 僅限真正達標；`paused` 只有**使用者**能要求（Agent 不得自我暫停）；`blocked` 需符合 runtime 的連續 blocked audit；若 runtime 沒有 blocked 控制，寫 escalation packet 並明確說明「需要 runtime／使用者停止」。

### 7.7 本 Task 的套用（硬性結論）

1. `PRIMARY_NATIVE_COMPOSITION` 3/3 已以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉 → 禁止第 4 次、禁止重開 A/B competition、不得以新 worktree／branch／model 重新計數。
2. Phase A attempt-01 已 fired：fingerprint `PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)`、class `ENVIRONMENT_FAILURE`、attempts used = 1。這不是 code defect；解方是環境（使用者動作），不是重試。
3. attempt-02 只在**新資訊源**成立時執行：唯讀 probe 顯示 layer-0 on-screen LINE 視窗 == 1（環境狀態已改變）＋**新的一次性授權**＋fresh runID。同 fingerprint 無新資訊的重跑＝無資訊增益，連續 2 次即觸發 escalation（§7.6）。
4. attempt-02 執行後：把 material-attempt 前後欄位與 counters append 到 `progress.md`／`execution.md`（append-only、不改寫既有內容）；`phase-a/` 證據目錄 append-only。
5. Phase B（不可逆）gates 依 §8 與 canonical handoff；Stage 05 必須 fresh、唯讀、自行從 disk／raw evidence 重算——不得引用 Stage 04 自寫的 PASS 字串。
6. `exit 0 ≠ PASS`；`HARNESS_VERIFY=PASS` 只證 harness 結構（`TASK_ACCEPTANCE=NOT_EVALUATED`），不證任何 task outcome。

### 7.8 常用 harness 指令（唯讀）

```bash
bash ~/.codex/tools/harness-verify.sh   # 期待：HARNESS_VERIFY=PASS／TASK_ACCEPTANCE=NOT_EVALUATED

bash ~/.codex/tools/harness-status.sh T20260925-0647-01-rev28-native-closed-loop \
  /Users/hsiaojohnny/Documents/ChatGPT/Line_backup   # 目前預期：STATE_RECONCILIATION_REQUIRED（無 state.json）

python3 ~/.codex/tools/task-orchestrator.py status \
  --task T20260925-0647-01-rev28-native-closed-loop \
  --repo /Users/hsiaojohnny/Documents/ChatGPT/Line_backup   # 只查；不得 start
```

---

## 8. 流程：Phase A／Phase B eligibility／Phase B／Stage 05

### 8.1 Phase A（read-only；attempt-01 已 fired 並遭前置拒絕）

- 可做：fresh read-only LINE identity observation、geometry、same-frame evidence、process/window inventory、baseline revalidation、pre-panel inventory、exact album/card association、LINE-specific V-09 證據。
- 不可做：任何未經 canonical 契約與當前授權明確允許的 reversible GUI navigation；`Save All intent/attempt = 0`；`destination confirmation intent/attempt = 0`。
- 前置（attempt-01 學到的教訓）：**目標 LINE 視窗必須恰好一個**（layer-0、on-screen）；執行前先做唯讀視窗盤點，≠1 就不要執行（避免浪費授權與 attempt）。

### 8.2 Phase B eligibility（全部 predicate PASS 才 arm）

須同時滿足：approved source/binary/rule binding、所有 pre-B gates PASS、valid persistent authority、clean one-shot entitlement、baseline unchanged、fresh LINE identity、current geometry、actual fresh target、chooser/tripwire 準備有效、**當前 run 的 explicit one-shot human authorization**。任一 `FAIL / UNKNOWN / NOT_RUN / STALE / MISSING` → `PHASE_B_INELIGIBLE`。

### 8.3 Phase B（不可逆；`FORBIDDEN_AB_EVALUATION`）

`Save All` ≤1 persisted intent/attempt；`destination confirmation` ≤1；任何 timeout／ambiguous／crash → observe-only，不 retry。

### 8.4 Stage 05（fresh independent acceptance）

真正執行完成後，Stage 05 必須從 disk/raw evidence 自己重算：staging file count、bytes、decodability、content hashes、content multiset、stability、baseline names/hashes/mtimes、ledger、intent/attempt counts、emitted GUI actions、evidence chain/anchors、LINE observation 與 backup run 的 binding。Stage 04 不得自我宣稱成功。

---

## 9. Blocker 史與根因分析（避免重複走冤枉路）

### 9.1 已 RESOLVED（有 mechanical evidence；勿重探）

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

### 9.2 現行 blocker（Phase A 前置；非 code defect）

```text
BLOCKER_FINGERPRINT: PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)
STAGE: Phase A（read-only preflight）
SURFACE: rev28ctl live-preflight → AXWindowIdentitySelector / CGWindow inventory
EXPECTED: 恰好一個 layer-0 on-screen 的目標 LINE 視窗（jp.naver.line.mac）
OBSERVED: found=2（id=191 主視窗 + id=996 無標題第二視窗）→ refusal，exit 77
```

### 9.3 兩層根因（Stage 06 decision 的核心結論，仍有效）

- **契約層（已封閉）**：舊 escalation 是 stale slice（luna worktree @ `9cbaa11`）。同一 `TASK_ID`、同一 plan/handoff 的 codex lineage 早已解掉其 cited root causes；`PLANNER_REPLAN` 被 FALSIFIED。
- **流程層（真病根）**：同一 `TASK_ID` 散在 3 個 worktree、沒有單一 controller；已解問題被重複升級（identity discipline defect）。V4.3.1 的對策＝identity preflight、blocker fingerprint、單一 authority tree、convergence budget。

### 9.4 Budget 記帳（硬性；不得重置）

- `PRIMARY_NATIVE_COMPOSITION`：**3/3 exhausted**，以 `RESOLVED_BY_SUPERSEDING_LINEAGE` 關閉。**不得重置、不得第 4 次 composition attempt**。
- `BUDGET_EXTENSION +2` 僅限 distinct fingerprint `V09_A4_FRESH_VERIFICATION_INCOMPLETE`；其 `STOP_AFTER` 已於 `815e9f1` 達成，收束。
- Phase A：attempt-01 已使用 1 次；現行 fingerprint `PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)` 屬**環境前置**。先修環境（probe == 1）再執行 attempt-02，**不得盲目重跑**。
- 未來任何新 blocker 執行前必須先回答：falsifiable hypothesis？new information source？distinguishing result？答不出就不應執行。

### 9.5 Escalation packet（durable）

`escalations/attempt-01/`：

| 檔案 | SHA-256 |
|---|---|
| `escalation.md` | `5bcbd72c718384d96fab9d69a4d272bf4c6bb210ba56a3e5ba7513063060a367` |
| `context.json` | `ae2081adb327c90fb421c1855cc65468c23f22848ad5bf979f03d2f40a69b8b1` |
| `decision.md`（`ESCALATION_DECISION: IMPLEMENTER_FIX`；G1–G6 PASS） | `e2fc4a288aa6ef60848729f3a05f98ee624855808a0efdac1a66cf022fcf54d9` |
| `stage-result-06.json` | `e92e4c62d1ca3eaf9aba9b5c99c93b09d8ad66e4351b7dcd5a762c84376b3061` |
| `PROVENANCE.md` | `9abf3ab90f7604b77fa792d085af3ddec4f3cf0295910bf44bbe33ce163806ec` |

---

## 10. Phase A attempt-01 記錄（2026-09-30；append-only evidence）

- **Run 目錄**：`.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/phase-a/attempt-01/RUN-20260930-103002-01/`（untracked，**禁止改寫**）
- **授權**：使用者於對話中明示同意，範圍＝本次 read-only Phase A run 恰好一次（一次性，已用於本 run；下次需新的授權）
- **凍結綁定**：產品樹 `cf39fdcc…`；digest `6734dda5…a686`（runtime 已重算比對）；binary `rev28/.build/debug/rev28ctl`（`swift build --product rev28ctl` no-op＝與凍結樹一致）
- **指令（僅執行一次）**：`rev28ctl live-preflight --config config.json --one-shot-authorization one-shot-authorization.json`
- **結果**：`REFUSED (PRECONDITION)`；`EXIT=77`；stderr 逐字：`live-preflight refused: targetWindowNotUnique(found=2)`
- **未產生**：Phase A per-condition 報告（`phase-a.json`）與 raw evidence manifest（evidence dir 空）。**不得以任何形式記為 PASS。**
- **Counters（ledger 實測）**：Save All intent/attempt = 0/0；destination confirmation intent/attempt = 0/0；irreversible = 0/0/0；ledger 唯一 entry＝`transaction.authorization`（seq 1）
- **Goal slot**：`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/goal-slots/5f7e18ba…f017a.goal-slot.json`（bound；`consumedAtISO8601` 不存在＝entitlement 未消耗）
- **Baseline**：未被觸碰（run 未到達 baseline 驗證階段即拒絕）；attempt-01 的 staging run dir 為空
- **Artifacts（SHA-256）**：

| 檔案 | SHA-256 |
|---|---|
| `phase-a-outcome.md` | `a83383ab76f62b399d903116da46e24a6402f4c1d28ffcb175f949c7bee9496c` |
| `config.json` | `ea93b9f5c5e897ba3c8f554d52f719da5b8dcd7a7f199c442cf182b596cebcca` |
| `one-shot-authorization.json` | `e537d6efef545ac10fea7e036eb9662b194b5fcbfdf1cf784b22eda2804ac72c` |
| `live-preflight-20260930T103016.log` | `656566da050eff76da4708ed47d3242df2e042fc16161f1301dee9cf2bab23fc` |
| `ledger.jsonl` | `02c4097bc5705070b99e42aa3b56d15c268fd9c59b1b38db9fc7faca34fa1e45` |
| `ledger-head.anchor` | `373a45d11c006c68782cba06c18a00e4415af0cdbb4d30534544f25f27d29102` |

- **Post-refusal 唯讀視窗盤點（diagnostic only；非 Phase A evidence）**：當時（10:30 後）on-screen layer-0 LINE 視窗 = **2**：
  - `id=191` layer=0 onscreen=true name=`LINE` frame=(-1,35,1147,699)（主視窗）
  - `id=996` layer=0 onscreen=true name=（無） frame=(30,45,327,643)（第二個視窗；須由使用者處置）
- **rev2 撰寫時再次唯讀盤點（13:42）**：LINE 未執行（0 個 on-screen layer-0 視窗；`ps` 未見 `jp.naver.line.mac`）。
- **Next（依 phase-a-outcome.md 判讀）**：不 retry；先讓視窗唯一；再以 fresh runID＋新的一次性授權跑 attempt-02。

---

## 11. V-09 驗證證據（現行有效）

### 11.1 attempt-04（fresh 複審；bindings head `cf39fdcc…ff1`、digest `6734dda5…a686`；全部 `bindings_verified: PASS`）

| 報告 | SHA-256 | 結果 |
|---|---|---|
| `v09/attempt-04/01-perception-geometry.md` | `d49a8212ee53db766bc3cddfbb7bdbf262e53df375900a57ec7edbc680ac6e3e` | PASS；0 MAJOR / 0 MINOR / 4 INFO；7 claims VERIFIED |
| `v09/attempt-04/02-timing-automation.md` | `c8c52adede4ffeb0b5ea3a08649b2ddea3491548b4892c6e8dd69332c1ed5a6d` | PASS；0 / 0 / 4；11 claims VERIFIED |
| `v09/attempt-04/03-transaction-history.md` | `063330fa39eeb168b3815f1009a5fada7d78012f90b33e15a67baeb74f4450ba` | PASS；0 / 0 / 6 |
| `v09/attempt-04/bindings.json` | `81d9ea21f567d28cfd89aec773202a92c61a4974dd4f059db103bc7a705eb7a7` | 48 paths、bindings 全 PASS |

attempt-01/02/03 的證據未作為 attempt-04 的 proof。

### 11.2 離線／deterministic 證據（cf39fdcc / digest `6734dda5…a686`，已入 commit）

- build `a46`；focused `a47` 88/0；full suite `a48` 242/0（0 skipped）
- adversarial `a50`/`a51`：27 tests × 2 runs PASS
- replay `a52`/`a53`：20/20 fixtures × 2，byte-identical，SHA-256 `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261`
- provenance `a54` PASS；frozen artifacts 9/9 re-hash PASS
- CLI refusal fixture `cli-refusal-20260929T0807`：77/77/77/64/77 且 zero side effects

**注意**：以上全部是 offline/deterministic evidence；不是 real LINE evidence、不是 GUI acceptance、不是 Phase A/B、不是 full backup success。不得冒充 production completion。

---

## 12. Git／遠端／PR／環境狀態

- 已落地 commits：`ce52103`（本 HANDOFF 初版）、`815e9f1`（V-09 attempt-04 收束＋Stage 06 decision；已推）、`5ed7106`、`c945f04`、`3d74248`、`cf39fdc`（M-1 repair）、`0d3149b`……；其後 append（docs/records-only）：本檔 rev2、`phase-a/` evidence、本檔 rev3（Harness 整合）。
- 事實核對：`git diff cf39fdcc HEAD -- rev28` 為空 → 產品／測試碼自 `cf39fdcc` 起 byte-identical；其後變更只在 `.agent/` 與根目錄文件。
- **本地 vs origin**：本地相對 origin 的落差（0～3）視交付時是否已 push 而定，以 `git status -sb`／`git ls-remote --heads origin` 實測為準；push 非執行前置條件。
- PR #1（draft）head 固定於 `rev28-prelive-finalization @9cbaa11`，無法承載後續 commits。待決選項（**尚未執行，由使用者決定**）：
  - C：從 `v43-ab/codex-rev28` 開新 draft PR → `master`，標註 supersedes #1。
  - D：關閉 PR #1（關閉不刪分支）。
- luna worktree 11 檔唯一副本（見 §2.1）：禁止破壞；snapshot 需使用者同意。
- **舊世代殘留（非本 Task authority，禁止使用）**：`~/Library/Application Support/LineNativeAXGUIBridge/`（2026-09-14/15 建置；LaunchAgent label `com.openai.line-native-ax-gui-session-bridge`；daemon 目前執行中，heartbeat 正常；repo 內僅 2026-09-15/16 舊 evidence 引用）。rev28 契約的合法路徑只有凍結產品樹的 `rev28ctl`；**不得使用此 bridge 或任何外部 AX 工具做觀測／操作，也不得自行卸載**。
- Harness orchestrator：`~/.codex/tools/task-orchestrator.py` 對本 task 尚無 controller `state.json`，實測回應 `STATE_RECONCILIATION_REQUIRED`。在完成 reconciliation 前，不得自動 `start` 產生第二套 state；routing truth 以 task 目錄內最新 machine-readable Stage result／run artifact 為準（現為 `phase-a/attempt-01`＋`v09/attempt-04`＋`escalations/attempt-01/stage-result-06.json`）。完整 controller／status／收斂規則見 §7.4／§7.6。

---

## 13. 尚待解決事項與下一步（依序）

**P0（唯一真實外部 gate）：把環境帶到「Phase A 可執行」狀態**

1. 使用者完成 §14 的唯一動作（LINE 重新回到可觀察狀態、恰好一個視窗）。
2. Agent 以唯讀 probe 確認 layer-0 on-screen LINE 視窗 == 1；≠1 → 只回報「需要的那一個動作」並停止（不請求授權、不執行）。
3. 使用者對 attempt-02 給**新的**明示一次性授權。
4. Agent 以 fresh runID 產生新 run 目錄與 config → 執行 `live-preflight`（零不可逆）→ 記錄 outcome（PASS/FAIL/UNKNOWN）與 counters。
5. 將 attempt-01（與 attempt-02）記錄 append 到 `progress.md`／`execution.md`（依 §7.6 material-attempt 格式：fingerprint／hypothesis／expected → observed／information gain）；`phase-a/` 證據維持 append-only（如需入庫，僅以原樣 commit，由使用者決定）。

**P1（可並行、需使用者決定）**：PR 方案 C/D；luna 11 檔 snapshot；orchestrator reconciliation；本地 commits 與 origin 的落差（若尚未 push）。

**若 attempt-02 仍被拒**：同一 fingerprint（視窗不唯一）重複失敗會消耗收斂 budget；不得換 model/session/branch/prompt 重置；改以新資訊（例如更精確的視窗歸屬診斷）決定是否需要 Stage 06。

---

## 14. 人類唯一必要動作（現在）

> 1. 啟動／登入 LINE（`jp.naver.line.mac`）→ 進入群組「旻謙允禎成長日記」（禎 U+798E）。
> 2. 把相簿 `2024/05/13～05/17` 的卡片帶到看得到的位置（捲到出現即可；**不要點開、不要開 ellipsis 選單、不要點任何按鈕**）。
> 3. 讓 LINE **只留下一個視窗**（若出現第二個／多餘視窗，關掉它）；視窗擺到前景、完整落在同一螢幕、不被其他視窗蓋住。
> 4. Mac 不要休眠／鎖屏；跟 Agent 說「準備好了」。
> 5. 當 Agent 請求「本次 read-only Phase A 一次性授權」時，明確同意；Agent 說「開始跑」之後的 1～2 分鐘不要動滑鼠／鍵盤、不要切換 App。

其他視窗不用關；只要不蓋住 LINE 即可。若後續 Agent 需要新的一次性 GUI 授權或 Phase B authorization：它必須 STOP 並輸出 `HUMAN_AUTHORIZATION_REQUIRED`／`EXTERNAL_BLOCKER`，一次只要求一個動作；不得 polling、不得沿用舊授權、不得把 `/goal` 當 GUI authorization。

---

## 15. 禁止事項（合併清單）

- Git：`reset --hard`、`clean`、automatic stash、`rebase`、force push、覆寫任何 dirty/untracked（含 `phase-a/` 與 luna 11 檔）、動 `rev28-prelive-finalization`、merge/cherry-pick A/B branches。
- Execution：第 4 次 `PRIMARY_NATIVE_COMPOSITION` attempt；重開 A/B competition；未經（當次、明示）授權的 `live-preflight`／`live-execute`；由 Agent 自行操作 GUI（授權 run 內契約允許者除外）；album-list prepositioning；`Save All`；destination confirmation；polling／retry／沿用舊授權。
- 工具：使用 `LineNativeAXGUIBridge` 或任何非 rev28 契約的 AX bridge／替代 authority；手動編輯 ledger／goal slot／授權檔。
- Budget／流程：換 model／session／branch／prompt 不重置；`exit 0 ≠ semantic PASS`；worktree 不一致不得自動破壞現場（→ `STATE_RECONCILIATION_REQUIRED`）。

---

## 16. 檔案索引與閱讀順序（新 Agent 開場 10 分鐘）

1. 本文件 §0（Prompt）＋全文件（§7＝Harness 邏輯；§17＝指令）
2. 本文件 §7（Harness V4.3.1 運作邏輯）＋ `~/.codex/AGENTS.md`、`~/.codex/policies/workflow-routing.md`、`~/.codex/policies/convergence-escalation.md`
3. `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`（R4 契約；SHA-256 `05413807…4c1b`）
4. 同目錄 `handoff.md`（canonical Stage 03 執行契約；SHA-256 `67fc16a6…7a33`）
5. `phase-a/attempt-01/RUN-20260930-103002-01/phase-a-outcome.md`（嘗試結果；SHA-256 `a83383ab…9496c`）
6. 同目錄 `progress.md`（最後三段：attempt-03 reviews／attempt-04＋Stage 06／最新 status；**attempt-01 尚待回填**）
7. 同目錄 `execution.md`（末段 attempt-04 記錄；**attempt-01 尚待回填**）
8. `escalations/attempt-01/`（§9.5 五檔＋hashes）
9. `v09/attempt-04/`（§11.1 四檔＋hashes）
10. `Line_backup/evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json`（SHA-256 `3c932d8c…1bc2`）
11. Harness schema／工具：`~/.codex/schemas/stage-result.schema.json`、`~/.codex/tools/task-orchestrator.py`、`~/.codex/tools/harness-verify.sh`

---

## 17. 常用指令（read-only 驗身分／盤點用）

```bash
# 身分
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup status --short --branch
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup log --oneline -8
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup worktree list
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup ls-remote --heads origin
git -C /Users/hsiaojohnny/Documents/ChatGPT/Line_backup diff --stat cf39fdcc HEAD -- rev28   # 必須為空

# 契約 hash
cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260925-0647-01-rev28-native-closed-loop
shasum -a 256 plan.md handoff.md

# baseline 完整性（唯讀）
find /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 -type f | wc -l          # 57
find /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 -type f -print0 | xargs -0 stat -f %z | awk '{s+=$1} END {print s}'  # 17924900

# LINE 視窗盤點（唯讀；不觸碰 GUI；layer-0 on-screen 數必須 == 1 才能跑 Phase A）
ps aux | grep -i "jp.naver.line.mac" | grep -v grep
swift -e '
import CoreGraphics
let opts: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] ?? []
var count = 0
for w in list {
  guard let owner = w[kCGWindowOwnerName as String] as? String, owner == "LINE" else { continue }
  let layer = w[kCGWindowLayer as String] as? Int ?? -1
  let num = w[kCGWindowNumber as String] ?? "?"
  let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
  print("id=\(num) layer=\(layer) frame=\(b)")
  if layer == 0 { count += 1 }
}
print("layer0_on_screen_LINE_windows=\(count)")
'

# harness 結構驗證（只證 harness 本身，不證 task）
bash ~/.codex/tools/harness-verify.sh   # 期待：HARNESS_VERIFY=PASS／TASK_ACCEPTANCE=NOT_EVALUATED

# orchestrator（只查，不 start；目前預期回 STATE_RECONCILIATION_REQUIRED＝無 state.json，屬已知狀況）
python3 ~/.codex/tools/task-orchestrator.py status \
  --task T20260925-0647-01-rev28-native-closed-loop \
  --repo /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
```

---

## 18. 與舊版交接的差異（避免被舊指示誤導）

| 舊版 | 現況（rev3，2026-09-30） |
|---|---|
| rev2（13:45）：無 Harness 章節 | **rev3 新增 §7（Harness V4.3.1 運作邏輯）**；其後章節全部重編號；§5 六狀態正規化為 canonical 值（§7.5） |
| 2026-09-29 版：`STATE: ESCALATED`；下一步＝ Stage 06 | Stage 06 已完成（`IMPLEMENTER_FIX`）；`815e9f1` 收束；無 open escalation |
| rev1（本檔初版）：Phase A「NOT FIRED；等使用者登入」 | **已 fired（attempt-01）→ REFUSED（視窗不唯一）**；下一步＝修視窗唯一性 → attempt-02 |
| rev1：`0/3 attempts` | Phase A attempts used = 1；fingerprint `PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)` |
| 舊版「不用關其他視窗」 | 仍成立；**但 LINE 自身必須恰好一個視窗**（本次 refusal 的原因） |
| 舊版 §「不要操作 LINE」 | 仍成立；直到 §14 的人類動作完成、Agent 取得新授權為止 |

---

## 19. 交接結論（一句話）

> 不要重新解這個專案。離線全部收束（cf39fdcc / digest `6734dda5…a686`、V-09 0 MAJOR）；Phase A attempt-01 已 fired 並因 **LINE 視窗不唯一（found=2）** 被 fail-closed 拒絕（零不可逆）。下一步：把 LINE 帶回「已登入＋目標相簿可見＋恰好一個視窗」，唯讀 probe 確認 =1，取得新的一次性授權，再以 fresh runID 跑 attempt-02。Harness 層：本 task 無 controller state（`STATE_RECONCILIATION_REQUIRED`；不得 `start`；規則見 §7）、`exit 0 ≠ semantic PASS`。在環境就緒前：**正確的 STOP 就是成功。**
