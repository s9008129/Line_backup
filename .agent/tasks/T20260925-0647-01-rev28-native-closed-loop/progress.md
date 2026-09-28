# Implement Progress — T20260925-0647-01-rev28-native-closed-loop

STATE: RUNNING
UPDATED_AT: 2026-09-29T05:45+0800
PLAN_REVISION: 4
MODE: AB_IMPLEMENTATION_EVALUATION (Phase B forbidden; PHASE_B_STATUS=FORBIDDEN_AB_EVALUATION)

## 給使用者看的白話摘要

- **目前目標：** 依 R4 批准的 Execution Contract 完成 C2/C3/C5 的原生生產組合，讓 `rev28ctl live-preflight`／`live-execute` 走同一條已審查的原生組合路徑，並在 Save All 之前 fail closed。Phase B 永久禁止。
- **目前卡點：** C2/C3（native observation session、typed run-bound evidence）與 pre-Save-All 的 composed adapter（含 8 個狀態、guarded reversible recovery、zero irreversible intent）已完成並通過 composed tests；下一個 blocker 仍是 primary architecture gap：`rev28ctl` 尚未接上 production `ObservationSource`／`ActuationEnvironment` 與幾何設定，因此 CLI 仍進不了這個 composition。
- **主要嘗試：** compile blocker 1/3（已解決）；segmentation blocker 1/3（已解決）；stability blocker 1/3（已解決）；C4 goal-slot blocker 1/3（已解決）；C4 typed eligibility/evidence enforcement 1/3（已解決）；native observation session 1/3（已解決）；typed state evidence 1/3（已解決）；pre-Save-All composition 1/3（已解決，含新發現的 ellipsis row convention 1/3 已解決）；rev28ctl production composition 0/3。
- **上一輪在測試什麼：** (A9) composed adapter 是否能從 fresh observation 逐一建立 8 個 pre-Save-All 狀態、只發 reversible navigation、且在 Save All 邊界以 `capabilityNotBuilt` fail closed；(A10) 為何 `ELLIPSIS_LOCATED` 在合成場景被拒（懷疑 pixel detector 的 y 方向）。
- **結果：** A9 的 6 個 composed tests 全數通過（12 captures、2 reversible dispatches、0 irreversible、entitlement 未消耗）；A10 證實並修好 detector 的 y 鏡射（真實 reviewed v5 frame 現在重現 reviewed dots 44/49.5/55 @ x 304.5）。
- **這輪多知道了什麼：** pre-Save-All composition 已可用且證據綁定正確；剩下的只是把它接到 CLI 的 production source/environment（含不可重啟的 epoch seed）。
- **距離驗收有沒有更近：** YES（C2/C3/C5 pre-Save-All 組合完成；primary outcome 仍 NOT_ACHIEVED，Phase B 未執行且禁止）
- **下一步：** 把 composed adapter 接進 `rev28ctl`：production `ObservationSource`（SCK + CG/AX/process + monotonic clock + 不可重啟的 epoch seed）、production `ActuationEnvironment`（GatedQuartzActuator reversible click）、以及 fail-closed 的 menu/addressable 幾何設定。
- **停損點：** 任一 blocker 累積 3 次 material attempts 或 2 次連續無新資訊即寫 escalation packet 並停止 substantive implementation；需要改 load-bearing 架構/acceptance semantics 即 REPLAN_REQUIRED。Phase B 任何動作直接 fail closed。

## Current blocker (next up: native composition)

```text
BLOCKER_FINGERPRINT:
STAGE=04
CHECK=NATIVE_PRODUCTION_COMPOSITION_REACHABLE
SURFACE=rev28/Sources/rev28ctl/main.swift
EXPECTED=live-preflight and live-execute enter one reviewed native composition that binds fresh retained-image observations, durable transaction authority, chooser/staging evidence
OBSERVED=the pre-Save-All composition now exists and is test-covered (ComposedNativeAdapter + establishPreSaveStates + runPreflight), but rev28ctl still builds no production ObservationSource/ActuationEnvironment/geometry, so live-preflight and live-execute cannot enter it yet
```

Resolved fingerprints: `DETERMINISTIC_SWIFT_TEST_COMPILATION` (A1), short-end-date segmentation (A2), equal-tail stability span (A3), C4 goal slot (A4), C4 preflight consumption (A5), C4 typed eligibility/evidence enforcement (A6), `NATIVE_OBSERVATION_SESSION_MISSING` (A7), `UNTYPED_STATE_EVIDENCE` (A8), `PRE_SAVE_ALL_COMPOSITION_MISSING` (A9), `ELLIPSIS_ROW_CONVENTION_MIRRORED` (A10).

## Convergence counters

```text
MATERIAL_ATTEMPTS_USED: 1 (compile blocker, resolved) / 1 (segmentation blocker, resolved) / 1 (stability blocker, resolved) / 1 (C4 goal slot, resolved) / 1 (C4 preflight, resolved) / 1 (C4 typed evidence enforcement, resolved) / 1 (native observation session, resolved) / 1 (typed state evidence, resolved) / 1 (pre-Save-All composition, resolved) / 1 (ellipsis row convention, resolved)
MAX_MATERIAL_ATTEMPTS: 3
CONSECUTIVE_NO_INFORMATION_GAIN: 0
SAME_BLOCKER_GOAL_TURNS_AT_IMPASSE: 0
OSCILLATION_DETECTED: NO
NEXT_BLOCKER_ATTEMPTS_USED: 0/3 (NATIVE_PRODUCTION_COMPOSITION_REACHABLE)
```

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
```

## Evidence pointers

- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/` — A1–A10 raw logs (build/focused/full suite)
- `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` (SHA-256 `4cb8a6b4…c6560b3`) — reviewed v5 real frame used by the A10 regression test
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/analysis/r4-20260928/` — R4 read-only diagnostics (segmentation/stability compile probes, test.log, build.log)
- `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json` (SHA 3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2)
- `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` — historical 28/0 pass log (pre-regression)
