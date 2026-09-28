# Implement Progress — T20260925-0647-01-rev28-native-closed-loop

STATE: RUNNING
UPDATED_AT: 2026-09-29T05:26+0800
PLAN_REVISION: 4
MODE: AB_IMPLEMENTATION_EVALUATION (Phase B forbidden; PHASE_B_STATUS=FORBIDDEN_AB_EVALUATION)

## 給使用者看的白話摘要

- **目前目標：** 依 R4 批准的 Execution Contract，完成 C1 的三個 deterministic 修復後，往 C2–C7 原生生產組合（native observation session、durable transaction authority、guarded actuation、actual chooser/destination、filesystem finalization）前進。Phase B 永久禁止。
- **目前卡點：** deterministic foundation、C4 goal slot/entitlement、C4 preflight 一次性授權、C4 typed chooser-verification gate 均已完成；下一個 blocker 仍是 primary architecture gap：`rev28ctl live-execute` 仍是 stub，沒有把 native observation/session、common engine、durable transaction、chooser、staging proof 串起來的原生組合。
- **主要嘗試：** compile blocker 1/3（已解決）；segmentation blocker 1/3（已解決）；stability blocker 1/3（已解決）；C4 goal-slot blocker 1/3（已解決）；C4 typed eligibility/evidence enforcement 1/3（chooser verification gate，已解決）；native composition blocker 0/3。
- **上一輪在測試什麼：** (A5) live-preflight 是否仍會消耗/改名一次性授權，以及缺少 checkpoint 時能否通過 resume 檢查；(A6) `recordChooserVerified` 是否可在未dispatch Save All 或重複呼叫時偽造 chooser 歷史。
- **結果：** 兩個嘗試都達成 predeclared distinguishing result；A6 focused 5 tests / 0 failures（含新 regression test）。
- **這輪多知道了什麼：** C4 的 reservation 面已完整（slot + state gate + preflight 唯讀 + chooser one-shot），剩下的是 native composition 本身。
- **距離驗收有沒有更近：** YES（C4 全面收斂；primary outcome 仍 NOT_ACHIEVED，Phase B 未執行且禁止）
- **下一步：** C2/C3 native composition 第一個 material attempt：以既有 LiveExecutionEngine/PersistentTransactionOwner 為核心，加入 NativeObservationSession（retained-image provenance + typed observation bundle）與 composition 入口，讓 preflight/execute 共用同一組合與 phase controller。
- **停損點：** 任一 blocker 累積 3 次 material attempts 或 2 次連續無新資訊即寫 escalation packet 並停止 substantive implementation；需要改 load-bearing 架構/acceptance semantics 即 REPLAN_REQUIRED。Phase B 任何動作直接 fail closed。

## Current blocker (next up: native composition)

```text
BLOCKER_FINGERPRINT:
STAGE=04
CHECK=NATIVE_PRODUCTION_COMPOSITION_REACHABLE
SURFACE=rev28/Sources/rev28ctl/main.swift
EXPECTED=live-preflight and live-execute enter one reviewed native composition that binds fresh retained-image observations, durable transaction authority, chooser/staging evidence
OBSERVED=live-execute refuses; no native observation session or concrete adapter connects the common engine to real sensors
```

Resolved fingerprints: `DETERMINISTIC_SWIFT_TEST_COMPILATION` (A1), short-end-date segmentation (A2), equal-tail stability span (A3), C4 goal slot (A4), C4 preflight consumption (A5), C4 typed eligibility/evidence enforcement (A6).

## Convergence counters

```text
MATERIAL_ATTEMPTS_USED: 1 (compile blocker, resolved) / 1 (segmentation blocker, resolved) / 1 (stability blocker, resolved) / 1 (C4 goal slot, resolved) / 1 (C4 preflight, resolved) / 1 (C4 typed evidence enforcement, resolved)
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

## Commits (A/B branch v43-ab/codex-rev28)

```text
783dd37 fix(rev28): repair StructuralLocatorsTests helper calls so the focused target compiles
4b34c17 fix(rev28): accept canonical short end date in album card segmentation
3a42164 fix(rev28): measure staging stability span over the contiguous equal tail
cc7fe56 feat(rev28): bind the one-shot entitlement to a persistent goal slot
bebc418 fix(rev28): keep live preflight observation-only and require the production checkpoint
57419bf fix(rev28): require dispatched Save All state before chooser verification record
```

## Evidence pointers

- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/` — A1–A4 raw logs (build/focused/full suite)
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/analysis/r4-20260928/` — R4 read-only diagnostics (segmentation/stability compile probes, test.log, build.log)
- `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json` (SHA 3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2)
- `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` — historical 28/0 pass log (pre-regression)
