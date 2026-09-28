# Implement Progress — T20260925-0647-01-rev28-native-closed-loop

STATE: RUNNING
STATE_NOTE: prior AB_IMPLEMENTATION_COMPLETE claim SUPERSEDED by V-09 attempt-01 review evidence. All eight MAJOR plan-conformance fingerprints (C3 AX-window binding, C5 intra-click revalidation, C4 durable budget + owner reservation enforcement, C6 per-primitive accounting + chooser predicate-v2 derivation, C7 post-dispatch tripwire-gap gate, eligibility recomputation) and the actionable MINORs are repaired in-contract; the repair set first drifted the CI-frozen `HarnessCalibration.swift` blob (v3 provenance guard FAIL), which was corrected by restoring the frozen blob — guard PASS again. Current tree: build PASS, focused 80/0 (11 suites), full suite 222/0 at implementation digest e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9 (44 swift files). Next: V-09 attempt-02 re-review on that digest; real Phase A evidence still blocked by external prerequisite (LINE signed out on this Mac); Phase B forbidden; zero irreversible
UPDATED_AT: 2026-09-29T07:26+0800
PLAN_REVISION: 4
MODE: AB_IMPLEMENTATION_EVALUATION (Phase B forbidden; PHASE_B_STATUS=FORBIDDEN_AB_EVALUATION)

## 給使用者看的白話摘要

- **目前目標：** 完成 R4 批准的 Phase A 證據工具鏈（`phase-a.json`＋raw manifest），讓 `rev28ctl live-preflight` 的既審查原生路徑能在真實 Mac／真實 LINE 上發布逐條件證據；Phase B 永久禁止。
- **目前卡點：** Phase A 發布工具鏈已完成並全數通過（16 conditions、deferred chooser gate、append-only per run dir）。最後一哩「真實 Phase A preflight」目前在**外部前置**上受阻：這台 Mac 的 LINE（pid 54034）是**登出狀態**，只顯示登入／歡迎畫面（單一 242x169 pt 視窗），沒有任何目標對話或相簿畫面；現在跑只會（預期）在 GROUP_READY named refusal，無法產生 `phase-a.json`，故本輪未開火（fail closed、授權與 counters 未動）。此外兩個 Phase A 當場必須驗證的未定項已記錄：真實 menu-surface 幾何常數（rev27 候選 `[586,124,824,427]`，未驗證）與 popup 是否能在 frozen `primaryWindow` 擷取中被看見（W2 matrix 顯示 `includeChildWindows=false` 不含 popup child window）。
- **主要嘗試：** compile／segmentation／stability／C4 goal-slot／C4 preflight／C4 typed evidence enforcement／native observation session／typed state evidence／pre-Save-All composition／ellipsis rows／rev28ctl production composition／post-Save-All composition 各 1/3（皆已解決）；Phase A evidence publisher 1/3（已解決，A13）；real Phase A preflight 0/3（外部前置未滿足，未開火）；V-08 閘門於現行樹補驗 1 輪（adversarial 27/27 ×2、replay PASS ×2、v3 provenance PASS）。
- **上一輪在測試什麼：** (A13) Phase A 證據只能從真實 run artifacts 推導：`PhaseAEvidenceBuilder.inspect` 讀 state artifacts＋retained PNG hash＋pre-dispatch context（排除 `-refused-`、記錄 malformed 名稱），`build` 逐一評 16 條件（含 deferred `ACTUAL_LINE_CHOOSER_OBSERVED`=UNKNOWN、ledger-proven zero counters、`phaseBPreventedBy`），`publish` 寫 `phase-a.json`＋raw manifest 且同一 run dir 二次發布被拒；`live-preflight` 接線並在既有 run dir 有報告時 named refusal。
- **結果：** 新增 `PhaseAEvidence.swift`（1039 行）／21 個 tests／`tripwireReadiness()` 唯讀快照／`rev28ctl` 發布路徑；focused 21 tests / 0 failures、full suite 202 tests / 0 failures；CLI refusal fixture 更新（`cli-refusal-20260929T0617`）維持 77／77／77／64／77 且無 evidence/ledger/staging 副作用；新 implementation digest `eb4415f9…f6b1`（43 swift files）。唯讀環境偵察（`phase-a-env-20260929T0626`）：TCC/SCK/Vision 在這個 terminal 的 responsible-process context 全部 OK；LINE 已登出（外部前置）。
- **本輪補驗（A14）：** adversarial 27/27 ×2、20 個 pinned replay fixtures ×2（JSON 輸出 byte-identical，SHA `81f6da94…7261`）、v3 provenance `status=PASS`（`HarnessCalibration.swift` blob 未漂移、20 samples／max 155.19 ms）、final-HEAD full suite 202/0——V-08 與 handoff item-5 在現行樹重驗通過。
- **這輪多知道了什麼：** (1) Phase A 報告無法被合成——缺任何一項真實 artifact 即 FAIL/UNKNOWN 並擋下 Phase B；(2) 本機執行環境本身可用（ax/screenCapture/postEvent=true、SCK 21 windows、Vision OK）；(3) 真正的下一步是外部前置（LINE 登入＋目標相簿畫面），並已把幾何與擷取面的兩個未定項寫成下一次 Phase A 必須當場驗證的問題。
- **這輪最新（06:50）：** V-09 attempt-01 三個獨立審查報告全部落地，結果是 ISSUES_FOUND：共 8 個 MAJOR（AX 身分未綁視窗、click 過程未再驗證、per-primitive 記帳缺失、per-blocker 預算未持久化、owner reservation 未強制 state/eligibility、post-dispatch tripwire gap 未複查、chooser predicate v2 未從 frozen bytes 推導、eligibility 只做標籤檢查）＋5 個 MINOR。這些都是 plan 明文要求的行為，屬**合約內修復**（非 replan，除 eligibility 範圍問題待評估）。
- **V-09 修復（07:26）：** 8 個 MAJOR 全數在合約內修復完成（詳見 `## V-09 attempt-01 repairs`）：GoalSlot 改 `rename(2)` 原子寫入；AX 身分改由 `AXWindowIdentitySelector` 綁定目標 windowID；`postClick` 在 hover 與 `mouseDown` 之間再驗證（zero-event test）；chooser predicate 由 frozen bytes 推導並接進 `live-preflight`（不匹配即 named refusal）；per-blocker（≤3）與連續 revalidation（2）預算改由 ledger 重算並在 owner reservation 強制 eligibility/state；destination 準備每個 primitive 都 reacquire＋逐筆記帳；post-dispatch gap/failure 進 gate 並在 evidence 揭露；eligibility 改為 recomputed evidence（plan/handoff/frozen artifacts/predicate evidence/implementation digest 全部重驗）；menu/addressable bounds 加「必須落在 retained frame 內」guard；`OneShotAuthorization` marker 直接刪除，observe-only 改由 durable goal slot 判定；MINOR 兩項（provenance qualifier、menu-bounds freeze）判定不需 replan、以 Phase A 層級記錄。首版修復另把 `HarnessCalibration.swift`（v3 CI freeze 綁 blob 的檔案）一起改了，導致 `verify_pre_live_provenance.py` fail-closed FAIL；已還原 frozen blob（guard PASS），生產路徑的 C3 修復不受影響。build PASS、focused 80/0（11 suites）、full suite 222/0；最終 implementation digest `e80e4f0f…54e9`（44 swift files）。
- **距離驗收有沒有更近：** 中期 YES（V-09 attempt-01 的 8 MAJOR 已全數修復並在現行樹重驗：focused 80/0、full 222/0）；但 attempt-02 複審未跑、Phase A 真實證據仍缺（外部前置）、Phase B 未執行且禁止；primary outcome 仍 NOT_ACHIEVED；累計 irreversible intent／attempt／dispatch = 0
- **下一步：** (1) V-09 attempt-02：3 個 fresh independent reviewer contexts 針對新 digest `03ac90b4…e17d` 複審（同一批 report 名稱、append-only）；(2) 請使用者登入 LINE（QR 或電子郵件）並開好群組 旻謙允禎成長日記 的 `2024/05/13～05/17` 相簿列表（保持單一 on-screen layer-0 視窗），再用 fresh runID／fresh evidence dir 跑 `rev28ctl live-preflight`（零 irreversible、授權不消耗）以發布真實 `phase-a.json`；(3) Stage 05 independent acceptance。
- **停損點：** 任一 blocker 累積 3 次 material attempts 或 2 次連續無新資訊即寫 escalation packet 並停止 substantive implementation；需要改 load-bearing 架構/acceptance semantics（例如擷取面）即 REPLAN_REQUIRED。Phase B 任何動作直接 fail closed。

## Current blocker (next up: real Phase A preflight on this Mac)

```text
BLOCKER_FINGERPRINT (active, Stage 04 repairs):
STAGE=04
CHECK=V09_REPAIR_SET (V09_AX_IDENTITY_WINDOW_UNBOUND, V09_C5_INTRA_CLICK_REVALIDATION_MISSING, V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING, V09_C4_BUDGET_NOT_DURABLE, V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING, V09_C7_POST_DISPATCH_GAP_UNCHECKED, V09_CHOOSER_PREDICATE_V2_NOT_DERIVED; MINORs in the V-09 section)
SURFACE=rev28/Sources/Rev28Core (in-contract repairs; Phase B still forbidden)
EXPECTED=all V-09 attempt-01 MAJOR findings repaired within the approved plan contract, covered by focused tests, full suite green, then V-09 attempt-02 re-review on the new implementation digest
OBSERVED=repairs landed 2026-09-29T07:10 (1/3 each; see `## V-09 attempt-01 repairs`); the first repair revision drifted the CI-frozen `HarnessCalibration.swift` blob and was corrected by restoring the frozen blob (`a32` provenance guard PASS; fingerprint V09_REPAIR_PROVENANCE_BLOB_DRIFT 1/3 resolved); build `a29`, focused 80/0 (11 suites, `a30`) and full suite 222/0 (`a31`) at the corrected tree; implementation digest recomputed = e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9 (44 swift files); attempt-02 re-review NOT_RUN

BLOCKER_FINGERPRINT (active, next):
STAGE=04
CHECK=V09_ATTEMPT_02_REVIEW_PENDING
SURFACE=.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/v09/attempt-02 (fresh independent reviewers, read-only)
EXPECTED=three fresh independent reviewer contexts re-run the V-09 topics against bindings bound to implementation digest 03ac90b4…e17d (plus plan/handoff/frozen artifacts) and report PASS or remaining plan-conformance issues
OBSERVED=not yet started; attempt-01 binds to the superseded digest eb4415f9…f6b1

BLOCKER_FINGERPRINT (next after repairs):
STAGE=04
CHECK=REAL_PHASE_A_PREFLIGHT_EVIDENCE_MISSING
SURFACE=rev28ctl live-preflight (Phase A, zero irreversible)
EXPECTED=a real live-preflight on this Mac with the reviewed LINE instance open, reaching SAVE_ALL_LOCATED and recording a >=10 s gap-free pre-dispatch context digest, with production counters 0/0
OBSERVED=no real live-preflight has been run. Read-only reconnaissance (execution-evidence/phase-a-env-20260929T0626) shows the external prerequisite is absent: LINE.app (pid 54034, started 06:17:54) is running but shows its login/welcome screen (signed out) with one 242x169 pt layer-0 window and no target chat/album surface, so a preflight now could not pass GROUP_READY and would only capture private login material. Two Phase A-time unknowns are also recorded: the real frozen menu-surface bounds (candidate [586,124,824,427] derived from reviewed rev27 S11c evidence, unvalidated) and whether the LINE menu popup is observable inside the frozen primaryWindow capture (W2 capture matrix shows includeChildWindows=false excludes popup child windows).
```

Resolved fingerprints: `DETERMINISTIC_SWIFT_TEST_COMPILATION` (A1), short-end-date segmentation (A2), equal-tail stability span (A3), C4 goal slot (A4), C4 preflight consumption (A5), C4 typed eligibility/evidence enforcement (A6), `NATIVE_OBSERVATION_SESSION_MISSING` (A7), `UNTYPED_STATE_EVIDENCE` (A8), `PRE_SAVE_ALL_COMPOSITION_MISSING` (A9), `ELLIPSIS_ROW_CONVENTION_MIRRORED` (A10), `NATIVE_PRODUCTION_COMPOSITION_REACHABLE` (A11), `POST_SAVE_ALL_COMPOSITION_MISSING` (A12), `PHASE_A_EVIDENCE_PUBLISHER_MISSING` (A13).

## Convergence counters

```text
MATERIAL_ATTEMPTS_USED: 1 (compile blocker, resolved) / 1 (segmentation blocker, resolved) / 1 (stability blocker, resolved) / 1 (C4 goal slot, resolved) / 1 (C4 preflight, resolved) / 1 (C4 typed evidence enforcement, resolved) / 1 (native observation session, resolved) / 1 (typed state evidence, resolved) / 1 (pre-Save-All composition, resolved) / 1 (ellipsis row convention, resolved) / 1 (native production composition reachable, resolved) / 1 (post-Save-All composition, resolved) / 1 (Phase A evidence publisher, resolved)
MAX_MATERIAL_ATTEMPTS: 3
CONSECUTIVE_NO_INFORMATION_GAIN: 0
SAME_BLOCKER_GOAL_TURNS_AT_IMPASSE: 0
OSCILLATION_DETECTED: NO
NEXT_BLOCKER_ATTEMPTS_USED: 0/3 (REAL_PHASE_A_PREFLIGHT_EVIDENCE_MISSING; no preflight fired — external prerequisite LINE sign-in + target album surface is absent)
V09_REPAIR_ATTEMPTS: 1/3 each, all resolved 07:10 (V09_AX_IDENTITY_WINDOW_UNBOUND, V09_C5_INTRA_CLICK_REVALIDATION_MISSING, V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING, V09_C4_BUDGET_NOT_DURABLE, V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING, V09_C7_POST_DISPATCH_GAP_UNCHECKED, V09_CHOOSER_PREDICATE_V2_NOT_DERIVED, V09_ELIGIBILITY_LABEL_ONLY; MINOR resolved/documented: V09_GOALSLOT_NON_ATOMIC_WRITE, V09_ONESHOT_MARKER_INERT, V09_ENGINE_RESUME_CONTINUATION_NARROW, V09_MENU_BOUNDS_UNBOUND (geometry guard; freeze-binding documented as Phase A item), V09_CHOOSER_PROVENANCE_QUALIFIER (no replan — qualifier already carried at Phase A artifact level per plan.md:248))
V09_ATTEMPT_01: 3 reports landed 06:50; verdicts ISSUES_FOUND; AB_IMPLEMENTATION_COMPLETE superseded; no V-09 attempt consumed the REAL_PHASE_A_PREFLIGHT fingerprint
V09_REPAIR_PROVENANCE_BLOB_DRIFT: 1/3, resolved 07:26 (first repair revision touched the v3-frozen `HarnessCalibration.swift` blob → provenance guard FAIL; frozen blob restored, guard PASS `a32`)
V09_ATTEMPT_02: 0/3 (NOT_RUN; bound to digest e80e4f0f…54e9)
```

## Run terminal state (2026-09-29T06:35+0800)

STATE: SUPERSEDED by the V-09 attempt-01 section below (2026-09-29T06:50+0800) — recorded 2026-09-29T06:35+0800 as: AB_IMPLEMENTATION_COMPLETE — 本輪成功條件逐項：1 approved R4 implementation（pre-Phase-B）✅ 盡可能完成；2 deterministic/regression gates（V-08／V-12／provenance）✅ 達成 handoff 要求；3 Phase A 真實證據「若可安全執行」——不可安全執行（LINE 已登出、無目標相簿畫面；開火只會在 GROUP_READY named refusal 並可能擷取私人登入畫面），未取得；4 zero irreversible ✅（dispatch 0／confirmation 0／intent 0）；5 progress.md ✅；6 convergence guard ✅（未觸發，0/3）。仍未完成（皆屬獨立步驟）：V-09 independent reviews（NOT_RUN）、真實 Phase A preflight（需使用者先登入 LINE 並開好目標相簿）、Stage 05 independent acceptance。PHASE_B_STATUS 固定 FORBIDDEN_AB_EVALUATION。

## Seed reconciliation (R3/R4)

- R4 planning recorded 0 material *implementation* attempts; its diagnostics live in `analysis/r4-20260928/` and are diagnostics, not fixes.
- R3 execution history (`execution-history/execution-r3-before-r4-stage03-20260929T045938+0800.md`) records only passing `swift test` runs (28/0) before the two new tests landed; it contains no prior fix attempt for `CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION`.
- No prior `progress.md` existed; absence is not a reset. Counters above start at 0 for this fingerprint based on the evidence above.

## START_INTEGRITY / REVERIFY_ON_START (observed 2026-09-29 ~05:10+0800)

```text
git status --short: (clean)
git branch --show-current: rev28-prelive-finalization
git rev-parse HEAD: 9cbaa1141595acb538d4672066072d2b8ffb7065  (matches required start commit)
plan.md SHA-256: 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b (matches)
handoff.md SHA-256: 67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33 (matches)
origin/rev28-prelive-finalization == local HEAD (no remote drift after fetch --prune)
baseline dir 57 files / 17,924,900 bytes; multiset digest ee958e…cadaaf (matches); tripwire digest b7debe…28fbd (matches)
old staging RUN-20260923-111908-01: present and empty
historical Rev27 ledger files: evidence-archived only; no active goal slot / live ledger exists in source yet
A/B branch created for this run: v43-ab/codex-rev28 (rev28-prelive-finalization pointer untouched)
```

## Material attempts

| Attempt | Hypothesis | Experiment/change | Expected distinguishing result | Observed result | Acceptance delta | New evidence | Uncertainty reduced | Information gain |
|---|---|---|---|---|---|---|---|---|
| A1 (compile) | 編譯失敗只因兩處 helper 呼叫錯（`binding()`/`ocr` vs computed `binding`/`item`） | 最小修改兩測試呼叫點後 `swift build` + focused `StructuralLocatorsTests` | test target compiles 且 focused tests 執行（vs 相同 compile failure） | build PASS；focused target 執行 12 tests，其中 2 個 segmentation 測試失敗（0 regions / unsafeGeometry） | CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION 不再失敗；REQUIRED_VERIFICATION_STATUS 由 FAIL 轉為可重評 | `execution-evidence/a1-focused-20260929T0517.log` | 排除「還有其他編譯錯誤」 | YES |
| A2 (segmentation) | 0-region 只因 `isDateRangeTitle` 拒收 2-component 短結束日期 | 允許 canonical 短結束形式（同起始年、end>=start），加邊界 regression test，重跑 focused | 兩個 segmentation 測試通過（2 regions + candidate；cross-card 為 referenceStructureMismatch） | 12/12 focused tests PASS | segmentation defect resolved；card association refusal 保持 | `execution-evidence/a2-focused-20260929T0520.log` | 排除 segmentation 其他原因；明確化 unsupported 短形式仍拒絕 | YES |
| A4 (C4 goal slot) | 一次性 entitlement 可被新 runID／新 ledger path 重置 | 新增 GoalSlot（goal/group/album/stagingRoot 為鍵、flock + fsync、consume-once）；owner init 開啟 slot 並拒絕「consumed + 空 ledger」；reserveSaveAll 加上 SAVE_ALL_LOCATED state gate 並先消費 slot | 新 runID 同 goal → goalSlotConflict；已消費 slot + 空/搬移 ledger → goalSlotEntitlementConsumed；正常 walk 後 reserve 成功且 slot 標記 consumed | GoalSlotTests 6 tests PASS；full suite 133 tests / 0 failures | C4 goal-slot blocker resolved；entitlement 不可跨 runID/path 重置 | `execution-evidence/a5-full-suite-goalslot-20260929T0545.log` | 排除「換 ledger path 可重置」與「未到 SAVE_ALL_LOCATED 也能 reserve」 | YES |
| A3 (stability) | equal-tail 誤判只因 span 用了 sample[0] | span 改量 contiguous equal tail，加 old-different-sample / long-equal-tail tests，重跑 focused | R4 diagnostic 案例 (0.2s tail) 由 true 變 false；正常 4s+ tail 仍 true | 13+16 focused tests PASS；full suite 127 tests / 0 failures | stability defect resolved；V-06 前置 stable-window 語意符合 C7 | `execution-evidence/a3-focused-20260929T0525.log`, `a4-full-suite-20260929T0527.log` | 排除時間窗判斷的其他解釋 | YES |
| A5 (C4 preflight) | live-preflight 仍會把一次性授權改名為 `.consumed`，且 production resume 不強制 checkpoint | 新增 `OneShotAuthorizationGate`（唯讀 inspect）；preflight 不再 rename；CLI 要求 `checkpointPath` + `requireCheckpointOnResume: true`；加 regression tests | preflight 後授權保持 `available`；缺 checkpoint 的 resume 被拒；full suite 保持 green | 135 tests / 0 failures | C4 preflight 面向收斂；Phase A 可安全重複 preflight | `execution-evidence/a6-full-suite-preflight-20260929T0556.log` | 排除「preflight 會消耗一次性授權」 | YES |
| A6 (C4 typed evidence) | `recordChooserVerified` 只檢查 `attempt.saveAll` 存在，未綁 state，也未防重複 append（可偽造第二份 chooser 歷史） | 加 state gate（必須在 `SAVE_ALL_LOCATED`）與 one-shot record gate，加 regression test（pre-dispatch / duplicate / post-transition 三情境） | 三情境分別回傳 authorizationMismatch / chooserVerificationAlreadyRecorded / chooserVerificationNotPermitted；既有 5 個 owner tests 保持通過 | PersistentTransactionOwnerTests 5/5 PASS | C4 typed eligibility/evidence enforcement 收斂 | `execution-evidence/a7-focused-chooser-gate-20260929T052557.log` | 排除「chooser 驗證可繞過 state／可重放」 | YES |
| A7 (observation session) | 共同引擎沒有任何面向前端的觀察者：沒有 retained frame、沒有 provenance，狀態只能靠呼叫端自我宣稱 | 新增 `NativeObservationSession`（單一 actor 序列化、retained PNG + imageSHA、epoch/binding、絕對 deadline）與 8 個 session tests；`NativeObservationRequest` 改帶 `observationBudgetNanos` | 每個狀態都能由一個 fresh bundle 推導；identity/epoch/deadline 任一破口都回 `ObservationRefusal` | 144 tests / 0 failures | C2/C3 觀察層存在且可被引擎使用 | `execution-evidence/a8-full-suite-observation-session-20260929T052843.log` | 排除「狀態只能靠 adapter 自述」的架構假設 | YES |
| A8 (typed state evidence) | engine 原本信任 adapter 回傳的證據，未在每個 transition 前驗證「這份證據是否為該 run/state 的 durable artifact」 | 新增 typed run-bound 驗證（artifact policy + 檔案 bytes digest + 前後 epoch 單調）在每次 transition 前執行，失敗回 `typedStateEvidenceRejected` | 偽造/錯綁/舊 epoch 的證據必須在 transition 前被拒，合法 walk 不變 | 147 tests / 0 failures（新 test 覆蓋 typed 拒絕路徑） | C3 收斂：狀態前進必須綁 typed、run-bound、file-backed 證據 | `execution-evidence/a9-full-suite-typed-evidence-20260929T052957.log` | 排除「transition 可吃呼叫端自製證據」 | YES |
| A9 (pre-Save-All composition) | 沒有具體 adapter 把 observation session 接到 common engine，所以 live-execute 連 Save All 邊界都到不了（先前只有 stub） | 新增 `ComposedNativeAdapter`（8 狀態、單次 guarded reversible recovery、artifact 只投影 fresh bundle）＋`preSaveStates`/`establishPreSaveStates`/`runPreflight`；6 個 composed tests 以假場景替換 OCR/pixels/焦點事實 | happy path：8 狀態、12 captures、2 reversible dispatches、0 irreversible、entitlement 未消耗；缺幾何在 `SAVE_ALL_LOCATED` refuse；`run()` 在 `dispatchSaveAll` 以 `capabilityNotBuilt` 停止且 0 irreversible | 6/6 composed tests PASS；full suite 156 tests / 0 failures | pre-Save-All composition 可用且證據/授權不變量有測試 | `execution-evidence/a11-focused-observation-ellipsis-composed-20260929T054308.log`, `a10-full-suite-ellipsis-rows-20260929T054157.log` | 排除「引擎與感測器之間缺少可測組合」；同時證明 Phase B 邊界 fail closed | YES |
| A10 (ellipsis rows) | `ELLIPSIS_LOCATED` 在合成場景被拒，懷疑 `EllipsisPixelDetector` 回傳的 y 是 bottom-up（`translate/scale` 造成多餘的一次翻轉） | 以已知 raster rows 的合成圖 + reviewed v5 真實 frame 做前後對照，移除多餘翻轉，加 3 個 regression tests（含真實 frame digest/SHA 綁定） | 修前：raster rows 4.5/12.5/20.5 被回報成 38.5/46.5/54.5（60 高圖），locator refuse；修後：reviewed v5 frame 重現 dots 44/49.5/55 @ x 304.5 並 locate (304.5, 49.5) | 修前 4 個 composed tests 失敗於 `ELLIPSIS_LOCATED`；修後 focused 23 tests / 0 failures、full suite 156 tests / 0 failures | `ELLIPSIS_LOCATED` 可用；detector 與 reviewed v5 幾何一致 | `execution-evidence/a10-full-suite-ellipsis-rows-20260929T054157.log`, `a11-focused-observation-ellipsis-composed-20260929T054308.log`、`evidence/20260919-rev25-baseline/attempt-01/v5-offline-replay.json` | 排除「y 方向鏡射」；確認 rev28replay 只讀 component count 故不受影響 | YES |
| A11 (rev28ctl production composition) | CLI 進不了已審查的 composition：`rev28ctl` 只有 stub 檢查，沒有 production `ObservationSource`／`ActuationEnvironment`／幾何設定，也沒有不可重啟的 epoch 來源 | 新增 `LiveCompositionFactory`（fail-closed 驗證 budget／frozen rule／locator geometry 後組裝 owner＋session＋adapter＋engine）與 `RunEpochAuthority`（floor 取自 run evidence 內的 `state-<STATE>-<epoch>` 檔名，衝突回 0 讓 bundle 驗證拒絕）；新增 `ProductionObservationSource`（SCK/CG/AX/process/signing）與 `ProductionActuationEnvironment`（GatedQuartzActuator reversible click）；改寫 `rev28ctl` live 區塊走同一 composition；加 7 個 composition＋4 個 epoch tests；刪除死碼 `XCTargetProcess` | 未校準幾何必須在第一次 capture 前被拒（captureCount 0）；組裝後 preflight 走到 `SAVE_ALL_LOCATED`（12 captures、2 reversible、0 irreversible、entitlement 未消耗）；`run()` 在 `dispatchSaveAll` 以 `capabilityNotBuilt` fail closed；CLI 四案例維持 77/77/64/77 | 7/7 composition tests＋4/4 epoch tests PASS；full suite 167 tests / 0 failures；CLI refusal transcript 重現 target-not-LINE 77／CI 77／missing config 64／stale digest 77 | CLI 與 common engine 進入同一 reviewed composition；pre-Save-All 路徑可由 production 程式碼抵達；epoch 不可跨重啟重用 | `execution-evidence/a12-full-suite-live-composition-20260929T054820.log`, `execution-evidence/cli-refusal-20260929T0550/cli-refusal-transcript-20260929T0551.log` | 排除「CLI 無法抵達 composition」與「新 session 可重置 epoch」；確認 Phase B 邊界在 capability 層 fail closed | YES |
| A12 (post-Save-All composition) | `dispatchSaveAll` 之後的 chooser／destination／download／filesystem／content 能力全部是 `capabilityNotBuilt`，Phase B 之前的路徑無法用同一 composition 走完，也無法在注入 boundary 下被證明 | 新增 `PhaseBEligibilityArtifact`（17 predicates、goal-identity digest、run-dir 邊界載入；缺席即拒絕）與唯讀 `FilesystemTripwireJournal`（startedAt 單調時戳、collection-gap 偵測）；新增 `PostSaveEnvironment` protocol 與 `ProductionPostSaveEnvironment`（10 s bounded pre-dispatch context gate、journal failure／gap named refusal、production click 走 `GatedQuartzActuator`）；在 `ComposedNativeAdapter` 實作 dispatch／chooser／destination／download／filesystem／content 全路徑（≥10 s gap-free context → fresh re-locate → baseline re-verify → census → readiness → permit → dispatch boundary → durable records）；`rev28ctl` 新增 chooser predicate／baseline reference／approvedRoot／tripwireRoots／optional eligibility 設定，`live-preflight` 記錄 `preDispatchContextSHA256` | 無 eligibility artifact → `dispatchSaveAll` named refusal 且 0 事件；有 artifact → 恰好一次 guarded click；context gap → 拒絕；download 無法定靜止 → 10 分鐘 cap 終止；baseline 變動 → content 成功宣告被拒 | 27 個 focused tests（PhaseBEligibility 8／ComposedAdapters 12／LiveComposition 7）全 PASS；full suite 181 tests / 0 failures；CLI refusal transcript 重現 77／77／64／77；新 implementation digest `f6ef94dc…a4f68` | C5–C7 全部由同一 composition 提供且經注入 boundary 測試；Phase B 仍 fail closed（無 artifact 即拒絕）；production counters 0/0 | `execution-evidence/a13-focused-postsave-20260929T060456.log`, `execution-evidence/a14-full-suite-phaseb-eligibility-postsave-20260929T060502.log`, `execution-evidence/cli-refusal-20260929T0607/cli-refusal-transcript-20260929T0607.log` | 排除「capability 無法走完」與「eligibility 可隱式 arm」；確認 gap／cap／baseline 變動都在測試中真的拒絕 | YES |
| A13 (Phase A publisher) | Phase A 的 16 條件、deferred chooser gate 與 raw manifest 只能從真實 run artifacts 推導；缺任何一項必須 FAIL/UNKNOWN 並擋下 Phase B，同一 run dir 不得重複發布 | 新增 `PhaseAEvidence`（`inspect`：state artifacts＋retained PNG hash＋pre-dispatch context；`build`：16 條件逐一評分＋`phaseBPreventedBy`＋ledger-proven zero counters＋explicit chooser-assumption statement；`publish`：`phase-a.json`＋raw manifest，append-only per run dir）；`ProductionPostSaveEnvironment.tripwireReadiness()`（唯讀、不 drain journal）；`rev28ctl live-preflight` 發布接線與既有報告 named refusal；21 個新 tests | 完整 run → 16 條件全 PASS＋deferred gate=UNKNOWN；缺檔／frame hash 不符／baseline 不符／staging 非空／tripwire 未就緒／短或斷裂的 pre-dispatch context／ledger 非零 → 對應 FAIL 或拒絕；同一 run dir 二次發布被拒 | focused 21 tests / 0 failures；full suite 202 tests / 0 failures；CLI refusal fixture 更新（`cli-refusal-20260929T0617`）維持 77／77／77／64／77 且無 evidence／ledger／staging 副作用；implementation digest `eb4415f9…f6b1`（43 swift files） | Phase A 證據工具鏈完成；真實 Phase A preflight 因 LINE 登出（外部前置）未開火 | `execution-evidence/a19-focused-phasea-20260929T062509.log`, `execution-evidence/a20-full-suite-phasea-20260929T062509.log`, `execution-evidence/cli-refusal-20260929T0617/`, `execution-evidence/phase-a-env-20260929T0626/` | 排除「Phase A 證據可合成／可重複發布」；確認 TCC／SCK／Vision 在真實 launch context 可用，並定位到外部前置與兩個擷取面未定項 | YES |
| A14 (V-08 補驗＋provenance) | Phase A publisher 落地後，V-08（adversarial／replay）與 handoff item-5 的 provenance 綁定尚未在現行樹重驗 | 在最終樹重跑 `AdversarialMatrixTests` ×2、20 個 pinned replay fixtures ×2（`replay_rev28.py`）、`verify_pre_live_provenance.py`（v3 fail-closed guard）、final-HEAD full suite | adversarial 27/27 兩次；replay `verdict=PASS` 兩次且 JSON 輸出 byte-identical；provenance `status=PASS`（blob 未漂移）；full suite 202/0 | V-08 在現行樹重驗 PASS；provenance binding 維持 PASS；final-HEAD deterministic gates 與 handoff 要求一致 | `execution-evidence/a21-full-suite-final-head-20260929T0635.log`, `execution-evidence/a22-adversarial-run1-20260929T0640.log`, `execution-evidence/a23-adversarial-run2-20260929T0640.log`, `execution-evidence/a24-replay-run1-20260929T0640.json`, `execution-evidence/a25-replay-run2-20260929T0640.json`, `execution-evidence/a26-provenance-20260929T0631.log` | 排除「Phase A publisher 落地造成 V-08／provenance 漂移」；確認現行 sampler 就是 CI-frozen blob | YES |

## Commits (A/B branch v43-ab/codex-rev28)

```text
783dd37 fix(rev28): repair StructuralLocatorsTests helper calls so the focused target compiles
4b34c17 fix(rev28): accept canonical short end date in album card segmentation
3a42164 fix(rev28): measure staging stability span over the contiguous equal tail
a142322 chore(harness): record Stage 04 progress and evidence for the A/B round
cc7fe56 feat(rev28): bind the one-shot entitlement to a persistent goal slot
b46054c chore(harness): record the C4 goal-slot attempt in progress.md
bebc418 fix(rev28): keep live preflight observation-only and require the production checkpoint
57419bf fix(rev28): require dispatched Save All state before chooser verification record
e5b5dfa chore(harness): record the C4 preflight and chooser-gate attempts in progress.md
9c02979 feat(rev28): add one serialized native observation session with retained-image provenance
c441477 feat(rev28): require typed run-bound state evidence before every engine transition
f5e7a3e fix(rev28): report ellipsis dot rows in top-left capture coordinates
947db18 feat(rev28): compose the native adapter for every pre-Save-All state
0d8663d feat(rev28): derive capture epochs from evidence so reruns never reuse artifact names
c7eb3f9 feat(rev28): assemble the live composition and wire it into rev28ctl
8528ce5 feat(rev28): arm Phase B only from an explicit machine-checkable eligibility artifact
e407565 feat(rev28): compose the post-Save-All path and keep it fail closed
0d1cdb5 feat(rev28): publish real Phase A evidence from the live preflight path
51cd793 chore(harness): record the Phase A publisher evidence and the live-preflight environment prerequisite
e93e298 chore(harness): record the final-HEAD full-suite run for the Phase A publisher round
```

## Evidence pointers

- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a22-adversarial-run1-20260929T0640.log`, `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a23-adversarial-run2-20260929T0640.log` — `AdversarialMatrixTests` 27 tests / 0 failures ×2（exit 0；SHA-256 `de37dfbd…179f`／`d03ea5ab…07fb`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a24-replay-run1-20260929T0640.json`（＋`.stdout`）, `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a25-replay-run2-20260929T0640.json`（＋`.stdout`）— `replay_rev28.py`：20 fixtures、`verdict=PASS` ×2，JSON 輸出 byte-identical SHA-256 `81f6da94…7261`
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a26-provenance-20260929T0631.log` — `verify_pre_live_provenance.py` v3 fail-closed guard：`status=PASS`、`validatedImplementationCommit=2ecfeb9c…`、`implementationSourceGitBlobSHA=c411011b…`、20 samples／max 155.19 ms（SHA-256 `3bf448fa…eb1a`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a27-focused-v09-repairs-20260929T0707.log` — V-09 修復後的 focused 批次：11 個 suites（GoalSlot／AXWindowIdentitySelector／NativeObservationSession／ActuationReadiness／ExecutionPolicy／PersistentTransactionOwner／LiveExecutionEngine／TripwirePostDispatchGate／ChooserPredicateProductionDerivation／PhaseBEligibility／ComposedAdapters）共 80 tests / 0 failures
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a28-full-suite-v09-repairs-20260929T0708.log` — V-09 修復後 full suite：23 suites、222 tests / 0 failures / 0 skipped（exit 0）；同時是 digest `03ac90b4…e17d` 的驗證樹

- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/` — A1–A14 raw logs (build/focused/full suite)
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a12-full-suite-live-composition-20260929T054820.log` — 167 tests / 0 failures（含 live composition 與 epoch authority suites）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/cli-refusal-20260929T0550/` — 前一輪 CLI refusal fixture（c7eb3f9 樹，`b0a71b95…ba0070`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a13-focused-postsave-20260929T060456.log` — 27 focused tests / 0 failures（PhaseBEligibility 8／ComposedAdapters 12／LiveComposition 7）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a14-full-suite-phaseb-eligibility-postsave-20260929T060502.log` — 181 tests / 0 failures（含 post-Save-All composition 與 eligibility suites）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a15-full-suite-final-head-20260929T060833.log` — final HEAD `7cc2e99` 的 181 tests / 0 failures（與 a14 同一 source tree；implementation digest `f6ef94dc…a4f68`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/cli-refusal-20260929T0607/` — CLI refusal fixture（config／rulebook／one-shot／stale-digest config／frozen chooser predicate 的 byte copy）與 transcript；`reviewedImplementationSHA256` 綁定 e407565 的 `rev28/Sources` 樹（`f6ef94dc…a4f68`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a16-focused-phasea-20260929T061700.log`, `a17-full-suite-phasea-20260929T061704.log` — Phase A publisher 首輪（前一 implementer turn）：21 focused／202 full，皆 0 failures
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a18-build-phasea-20260929T062509.log`, `a19-focused-phasea-20260929T062509.log`, `a20-full-suite-phasea-20260929T062509.log` — 本輪最終樹的 build／focused 21／full 202（0 failures）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a21-full-suite-final-head-20260929T0635.log` — final HEAD `51cd793` 的 202 tests / 0 failures（SHA-256 `876da172…e22b`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/cli-refusal-20260929T0617/` — 現行 CLI refusal fixture（`reviewedImplementationSHA256=eb4415f9…f6b1`，43 swift files）與 transcript：live-execute／live-preflight／CI guard 皆 77、缺 config 64、stale digest 77；refusal 後無 evidence／ledger／staging 副作用
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/phase-a-env-20260929T0626/` — Phase A 環境偵察：capability probe record（ax/screenCapture/postEvent=true、SCK OK、Vision OK）、LINE 唯讀 window inventory、environment-observations.md（外部前置與兩個 Phase A 未定項）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a13-focused-postsave-FAILED-intermediate-20260929T060425.log` — 中間失敗的 focused run（test 內 fake clock 與 permit 不一致），修好後由 a13/a14 取代，保留為除錯紀錄
- `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` (SHA-256 `4cb8a6b4…c6560b3`) — reviewed v5 real frame used by the A10 regression test
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/analysis/r4-20260928/` — R4 read-only diagnostics (segmentation/stability compile probes, test.log, build.log)
- `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json` (SHA 3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2)
- `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` — historical 28/0 pass log (pre-regression)

## Handoff TEST_ORDER status (2026-09-29T06:35+0800)

| # | Item | Status | Evidence / note |
|---|---|---|---|
| 1 | Narrow diagnostics（build／StructuralLocatorsTests／StagingVerifierTests regressions） | PASS | A1–A3（`a1`–`a4` logs） |
| 2 | Deterministic Swift tests＋executable-context full suite | PASS | `a21` final-HEAD full suite 202/0；Vision limitation tests 保持明示 |
| 3 | Adversarial 套件 ×2＋20 pinned replay fixtures ×2（含 hash 驗證） | PASS | `a22`／`a23` 27/27 ×2；`a24`／`a25` `verdict=PASS` ×2 byte-identical（現行 suite 為 27 cases，為 handoff 所述 25-case 基線的超集） |
| 4 | Common-composition failure matrix＋owner/restart matrix | PASS（suite-level、injected boundaries） | `a21` full suite 內執行 AdversarialMatrixTests（G01–G22／X01–X03）＋PersistentTransactionOwnerTests／GoalSlotTests／IntentLedgerTests／RunEpochAuthorityTests；本輪無獨立於 suites 之外的 matrix 執行 |
| 5 | provenance py＋current-composer synthetic AppKit calibration | provenance PASS；calibration 以 frozen W2 證據＋provenance binding 覆蓋（本輪未重跑） | `a26`；`frozen/postcondition-latency-observations-v3.json`（20 timings、strict monitor、input-free）仍受 fail-closed guard 綁定 |
| 6 | V-09 exact-binding code/rule reviews（before Phase A） | ATTEMPT-01 DONE / ISSUES_FOUND | 3 fresh reviewer contexts landed 06:50（`v09/attempt-01/`）；8 MAJOR＋5 MINOR；見下節；修復後需 attempt-02 複審 |
| 7 | Phase A eligibility／evidence | BLOCKED（external prerequisite） | 工具鏈完成（A13）；真實 preflight 未開火：LINE 已登出、無目標相簿畫面（`phase-a-env-20260929T0626`）；0/3 attempts |
| 8 | Conditional Phase B runtime gates／finalization | FORBIDDEN | 本輪為 A/B evaluation，Phase B 絕對禁止；零 irreversible |

## V-09 pre-Phase-A reviews (attempt-01) — LANDED 2026-09-29T06:50+0800

- Handoff TEST_ORDER item 6 requires V-09 exact-binding code/rules reviews before Phase A. Three fresh independent reviewer contexts (read-only; no builds/tests/git writes) ran against the frozen bindings in `v09/attempt-01/bindings.json` (HEAD `8cdb8e53`, implementation digest `eb4415f9…f6b1` 43 swift files, plan/handoff SHA-256, all frozen rule/predicate/calibration/matrix/tripwire/restart/postcondition-v3 artifacts — every reviewer recomputed these read-only, all matched). All three reports landed; this section is the authoritative Stage 04 record of their verdicts.
- Reports (append-only; this file is the orchestrator record, reports stay immutable):
  - `v09/attempt-01/01-perception-geometry.md` SHA-256 `1b17be4e…fc829` — **ISSUES_FOUND** (3 MAJOR, 1 MINOR)
  - `v09/attempt-01/02-timing-automation.md` SHA-256 `ed29d011…3aeca` — **ISSUES_FOUND** (postcondition APPROVE; risk classes 4 MAJOR/1 MINOR/1 INFO; chooser 1 MAJOR/1 MINOR)
  - `v09/attempt-01/03-transaction-history.md` SHA-256 `59eeb8ea…eea08f` — **ISSUES_FOUND** (3 MINOR, no fail-open; adversarial 27/27×2 and Rev27 barrier supersession APPROVED)
- **Net: the earlier `AB_IMPLEMENTATION_COMPLETE` terminal claim is superseded.** V-09 attempt-01 found plan-conformance MAJORs in C3/C4/C5/C6/C7 and the chooser predicate-v2 derivation. These are behaviors `plan.md` explicitly requires, so they route to **in-contract repairs** (not replan) unless a repair exposes a genuine load-bearing conflict. Phase B remains FORBIDDEN_AB_EVALUATION; nothing in the reviews authorizes Phase B; zero irreversible counters remain 0/0/0.
- Confirmed first-hand by the implementer (cited code re-read 2026-09-29T06:48): `ProductionObservationSource.readAXIdentity` ignores `windowID` and returns `AXDriver.windows(ofApp: pid)[0]`; `QuartzActuator.postClick` validates once before posting `move→down→up` with no revalidation between `mouseMoved` and `mouseDown`; `FolderChooserDriver.navigateToDestination` posts ⇧⌘G/⌘A/text/Return through ungated primitives with one compound budget record; `LiveDispatchBudget` has no production call sites (tests only); `GoalSlot.write` fsyncs a temp then `removeItem`+`moveItem` (two-step, non-atomic).

## V-09 attempt-01 findings → Stage 04 blocker fingerprints (each starts 0/3)

| Fingerprint | Class | Plan basis | Summary |
|---|---|---|---|
| `V09_AX_IDENTITY_WINDOW_UNBOUND` | MAJOR | C3 (`plan.md:123-131`) | Production AX identity read is not tied to the target window; validation only requires non-empty AX role. |
| `V09_C5_INTRA_CLICK_REVALIDATION_MISSING` | MAJOR | C5 (`plan.md:152`) | No post-`mouseMoved` revalidation before `mouseDown`; focus theft between check and down still posts. No zero-event test for that window. |
| `V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING` | MAJOR | C6 (`plan.md:162-166`) | Destination preparation posts multiple primitives with a single reversible-budget record; per-primitive reacquisition/accounting absent. |
| `V09_C4_BUDGET_NOT_DURABLE` | MAJOR | C4 (`plan.md:136-140`) | Per-identical-blocker (≤3) and 2-consecutive-revalidation budgets not persisted/enforced in production; `LiveDispatchBudget` tests-only. |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` | MAJOR | C4 (`plan.md:144-146`) | Owner reservations do not enforce `PHASE_B_ELIGIBLE` / `DESTINATION_PREPARED` + approved tripwire; adapter-level gates only. |
| `V09_C7_POST_DISPATCH_GAP_UNCHECKED` | MAJOR | C7 (`plan.md:172-176`) | Post-dispatch FSEvents collection gaps/failures never re-checked; a clean-looking tripwire artifact can accompany dropped events. |
| `V09_CHOOSER_PREDICATE_V2_NOT_DERIVED` | MAJOR | C6 (`plan.md:162`) | Production decodes the frozen v1-shaped predicate directly (missing `predicateVersion` → 1) and refuses v1 → chooser path unreachable; `ChooserProductionPredicate.derive` has no production call site. |
| `V09_ELIGIBILITY_LABEL_ONLY` | MAJOR (open scope question) | handoff `:148` | Eligibility artifact validation checks verdict/labels/bindings but never recomputes evidence; no in-tree producer/recomputer exists. Repair-vs-replan assessment pending. |
| `V09_GOALSLOT_NON_ATOMIC_WRITE` | MINOR | C4 durability | `GoalSlot.write` temp-fsync then remove+move; crash window could lose the slot (contained by ledger+checkpoint today). |
| `V09_MENU_BOUNDS_UNBOUND` | MINOR | C3 (`plan.md:214`) | `menuBoundsCapture`/`addressableBoundsCapture` are config-supplied, not hash-bound to frozen calibration. |
| `V09_ONESHOT_MARKER_INERT` | MINOR | C4 | `OneShotAuthorizationGate` is inspect-only with no production writer; marker semantics unresolved. |
| `V09_ENGINE_RESUME_CONTINUATION_NARROW` | MINOR | C4 | Only `runPreflight` has the pre-intent continuation; fresh-ledger `run()` skips resume-time ledger/anchor checks. |
| `V09_CHOOSER_PROVENANCE_QUALIFIER` | MINOR (freeze boundary) | `plan.md:248` | Frozen chooser provenance lacks the "actual LINE chooser not yet observed" qualifier (exists only at Phase A report level). Adding it = append-only re-freeze (replan), not a local edit. |

- INFO-only reviewer notes (not blockers): postcondition APPROVE with 4 INFOs (harness-only 30 s late-delay exercise; guard bound-vs-recomputed max; ceil-nearest-rank median label; max latency 155.19 ms vs 150 ms fast cadence ratified in the freeze); journal always `attributableToThisRun=false` (strictly more aborting); ungated `pressDefaultButton`/`confirmWithReturnKey` helpers have no production callers today.

## V-09 attempt-01 repairs — LANDED 2026-09-29T07:10+0800

All eight MAJOR fingerprints plus the actionable MINORs were repaired in-contract (no plan/architecture change), re-verified on the repaired tree, then the implementation digest was recomputed with the same reviewed formula.

| Fingerprint | Repair (files) | Evidence |
|---|---|---|
| `V09_AX_IDENTITY_WINDOW_UNBOUND` | New `Identity/AXWindowIdentitySelector.swift`: binds the AX read to the target CGWindowID via the element's AX window number, else a unique same-frame match against the CG inventory entry; ambiguity/mismatch throws → `axIdentityUnavailable`. `AXIdentityRead` gained `matchMethod` + `isBoundToWindow`; `ProductionObservationSource.readAXIdentity(pid:windowID:)` uses it (never `windows[0]`). | `AXWindowIdentitySelectorTests`（a27／a28） |
| `V09_C5_INTRA_CLICK_REVALIDATION_MISSING` | `QuartzActuator.postClick` revalidates readiness + process identity + post-event access after the hover and immediately before `mouseDown`; refusal throws before any click is posted. | `ActuationReadinessTests` zero-event case（a27／a28） |
| `V09_C4_BUDGET_NOT_DURABLE` | `LiveDispatchBudget` gained a derived-view initializer; `PersistentTransactionOwner` rebuilds it from the verified ledger (`reversibleDispatchCount`、`budget.blocker` 的 per-action ≤3、trailing `budget.revalidation` 的連續失敗 ≤2)，並新增耐久寫入 `recordReversibleDispatch(action:blockerKey:)` 與 `recordCandidateRevalidation(blockerKey:passed:)`（第二次連續失敗先落帳再回錯）。 | `ExecutionPolicyTests`／`PersistentTransactionOwnerTests`／`LiveExecutionEngineTests`（a27／a28） |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` | `reserveSaveAll` 要求耐久 `eligibility.phaseB` 記錄（僅由 `recordPhaseBEligibility` 寫入，且會重驗證 artifact 證據）＋`currentState == .saveAllLocated`；`reserveDestinationConfirmation` 要求 `.destinationPrepared`（新錯誤 `destinationConfirmationRequiresPreparedState`）；`preIntentContinuationAllowed` 以 `isCheckpointVerified`＋零 irreversible＋未越界閘住 pre-intent resume。 | `PersistentTransactionOwnerTests`／`ComposedAdaptersTests`（a27／a28） |
| `V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING` | `FolderChooserDriver.navigateToDestination(pid:destination:primitiveGuard:)`：新 `DestinationPrimitiveGuard`（`verifiedPanel`／`reacquire`／`willPostPrimitive`）在每個 posted primitive 前重新取得唯一 verified panel 並逐筆記 `dispatch.reversible`（GoToFolder chord、set path value、clear、enter text、Return）；不再用單筆 compound 記錄；panel/field 非唯一即 fail closed。 | focused `ComposedAdaptersTests`＋full suite（a27／a28） |
| `V09_C7_POST_DISPATCH_GAP_UNCHECKED` | `FilesystemTripwireJournal.postDispatchRefusalDetail()`（collector failure／stopped／collection gap；僅 clean 時 nil）；`PostSaveEnvironment.postDispatchTripwireGate()` 在每個 post-dispatch 取樣前拒絕，且 `tripwireCollectionGapDisclosure()` 會寫入 tripwire evidence artifact。 | `TripwirePostDispatchGateTests` 3/3（a27／a28） |
| `V09_CHOOSER_PREDICATE_V2_NOT_DERIVED` | `live-preflight` 新增必填 `chooserCalibrationPath`／`chooserPredicateSHA256`／`chooserCalibrationSHA256`：重讀並 hash 驗證 frozen bytes、decode、`ChooserProductionPredicate.derive`，非 process-stable v2 即 named refusal。 | `ChooserPredicateProductionDerivationTests` 2/0（真實 frozen pair `0472aa0a…`／`13aa01a2…`；a27／a28） |
| `V09_ELIGIBILITY_LABEL_ONLY` | `PhaseBEligibilityArtifact` 綁定 handoff＋frozen artifacts＋predicate evidence；`validate` 維持純結構檢查，新增 `validateWithRecomputedEvidence(...)` 重讀 plan／handoff／frozen／predicate bytes 並比對 caller 重算的 implementation digest；共用 `ReviewedImplementationDigest`（自 `main.swift` 移出）；owner／adapter／factory 全部串接 recomputation。 | `PhaseBEligibilityTests` 15/0（a27／a28） |
| `V09_GOALSLOT_NON_ATOMIC_WRITE` | `GoalSlot.write` 以 `rename(2)` 一步安裝 fsynced temp（消除 remove+move 空窗）後 fsync parent directory。 | `GoalSlotTests`（含並發替換 loop；a27／a28） |
| `V09_ONESHOT_MARKER_INERT` | 刪除 `OneShotAuthorization.swift` 與其 tests；`live-preflight` 改用 durable goal slot（`entitlementConsumed`）判 observe-only，不再依賴 inert token marker。 | build＋full suite（a27／a28） |
| `V09_ENGINE_RESUME_CONTINUATION_NARROW` | `LiveExecutionEngine.run()` 改為先嘗試 verified pre-intent continuation（`owner.preIntentContinuationAllowed`），否則回 observe-only；不再只有 `runPreflight` 具備 continuation。 | `LiveExecutionEngineTests`（a27／a28） |
| `V09_MENU_BOUNDS_UNBOUND` | Fail-closed 幾何：`.saveAllMenuRows` 要求設定的 menu／addressable bounds 落在 retained frame 內，`resolvedBackingScale` 要求恰一 display。Hash-binding 需要新的 append-only freeze（frozen 集內沒有真實 LINE menu bounds），故列為 Phase A 當場義務。 | `NativeObservationSessionTests`＋`PhaseAEvidence` context（a27／a28） |
| `V09_CHOOSER_PROVENANCE_QUALIFIER` | 不需 replan：plan 要求的標註（"calibrated on real NSOpenPanel, actual LINE chooser not yet observed"）已存在於 Phase A evidence artifact（declared assumption＋deferred `ACTUAL_LINE_CHOOSER_OBSERVED`=UNKNOWN），frozen 檔保持 byte-identical（append-only）。 | `PhaseAEvidenceTests`（a28 內） |

- CI-freeze blob drift correction（in-flight, 07:26）：首版修復把 `rev28/Sources/rev28ctl/HarnessCalibration.swift` 的 AX-read 也改成 `AXWindowIdentitySelector`，但該檔 blob 受 `ci-w2-item5-freeze-provenance-v3.json` fail-closed 綁定（"pre-live review/live use must stop" until a new hosted freeze）。已以 apply_patch 還原該檔為 frozen blob `c411011b…`（`git hash-object` 相符、`python3 -B rev28/Tools/verify_pre_live_provenance.py` 回復 `status=PASS` = `a32`）；C3 的合約內修復只落在生產觀測路徑（`ProductionObservationSource`＋`AXWindowIdentitySelector`），calibration harness 的自身 AX read 維持 frozen bytes。
- Digest recompute（同一 reviewed formula；先以 `00f8634` 樹重現舊 digest `eb4415f9…f6b1`／43 files 作為公式交叉驗證）：最終 `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9`，44 files（−`OneShotAuthorization.swift`，＋`AXWindowIdentitySelector.swift`，＋`ReviewedImplementationDigest.swift`）。
- Focused 批次（11 suites）80/0 = `a27`（首版）／`a30`（還原後）；full suite 23 suites 222/0/0 skipped = `a28`（首版）／`a31`（還原後）；build = `a29`；provenance guard 還原後 `status=PASS` = `a32`。

## Next up (dependency order)

1. V-09 attempt-02：3 個 fresh independent reviewer contexts 針對 `v09/attempt-02/bindings.json`（新 digest `03ac90b4…e17d`＋plan/handoff/frozen artifacts）複審，報名沿用 `01-perception-geometry.md`／`02-timing-automation.md`／`03-transaction-history.md`，append-only；每 blocker 上限 3 次。
2. 視需要更新 CLI refusal fixture（`LiveConfig` 新增 3 個必填 chooser 欄位、observe-only 改由 goal slot 判定，舊 transcript 描述已不對應）；僅在需要新一輪 refusal 證據時重跑。
3. Real Phase A preflight 仍受外部前置阻擋（需登入 LINE＋目標相簿畫面）；零 irreversible。
4. Phase A 後進 Stage 05 independent acceptance。
