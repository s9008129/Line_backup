# Implement Progress — T20260925-0647-01-rev28-native-closed-loop

STATE: RUNNING
UPDATED_AT: 2026-09-29T06:25+0800
PLAN_REVISION: 4
MODE: AB_IMPLEMENTATION_EVALUATION (Phase B forbidden; PHASE_B_STATUS=FORBIDDEN_AB_EVALUATION)

## 給使用者看的白話摘要

- **目前目標：** 依 R4 批准的 Execution Contract 完成 C2/C3/C5–C7 的原生生產組合，讓 `rev28ctl live-preflight`／`live-execute` 走同一條已審查的原生組合路徑，並在 Save All 之前 fail closed。Phase B 永久禁止。
- **目前卡點：** C2–C7 的原生組合已完成：`dispatchSaveAll`／chooser／destination／download／filesystem／content verification 全部由同一個 composed adapter 提供，唯一能 arm Save All 的來源是顯式的 Phase B eligibility artifact，缺席即 named refusal。下一個 blocker 是在這台 Mac 上（LINE 目標對話開著）跑真正的 Phase A `live-preflight`（零 irreversible、授權不消耗），取得真實的 pre-dispatch context digest。
- **主要嘗試：** compile／segmentation／stability／C4 goal-slot／C4 preflight／C4 typed evidence enforcement／native observation session／typed state evidence／pre-Save-All composition／ellipsis rows／rev28ctl production composition 各 1/3（皆已解決）；post-Save-All composition 1/3（已解決：C5–C7 全路徑完成且 Phase B 前置條件 fail closed）；real Phase A preflight 0/3（下一輪）。
- **上一輪在測試什麼：** (A12) 把 C5–C7 全部接進 composed adapter 與 CLI，並確認：沒有 Phase B eligibility artifact 時 `dispatchSaveAll` 以 named refusal 拒絕且 0 事件；有 artifact 時恰好一次 guarded click；pre-dispatch context 有 collection gap 時拒絕；download 無法定靜止時在 10 分鐘 cap 停止；baseline 變動時 content 成功宣告被拒。
- **結果：** 新增 `PhaseBEligibilityArtifact`／`FilesystemTripwireJournal`／`PostSaveEnvironment`／`PostSaveComposition` 並改寫 `ComposedNativeAdapter` 與 `rev28ctl`；27 個 focused tests 全數通過，full suite 181 tests / 0 failures；CLI refusal transcript 維持 77／77／64／77；baseline 57 檔／17,924,900 bytes／multiset `ee958e…cadaaf`／tripwire `b7debe…28fbd` 未變。
- **這輪多知道了什麼：** post-Save-All 的每個步驟都能在注入 OS boundary 下被證明（含 named refusal 與 cap 終止），且唯一能 arm Save All 的來源是顯式 eligibility artifact；production 路徑在缺 artifact 時仍 fail closed（0 dispatch、0 confirmation）。
- **距離驗收有沒有更近：** YES（primary outcome 仍 NOT_ACHIEVED；Phase B 未執行且禁止；累計 irreversible intent／attempt／dispatch = 0）
- **下一步：** 在這台 Mac 上開著已審查的 LINE 目標對話，執行 `rev28ctl live-preflight`（Phase A；零 irreversible、授權不消耗），取得真實 `preDispatchContextSHA256`；之後才是 V-09 topic reviews 與 Stage 05 independent acceptance。
- **停損點：** 任一 blocker 累積 3 次 material attempts 或 2 次連續無新資訊即寫 escalation packet 並停止 substantive implementation；需要改 load-bearing 架構/acceptance semantics 即 REPLAN_REQUIRED。Phase B 任何動作直接 fail closed。

## Current blocker (next up: real Phase A preflight on this Mac)

```text
BLOCKER_FINGERPRINT:
STAGE=04
CHECK=REAL_PHASE_A_PREFLIGHT_EVIDENCE_MISSING
SURFACE=rev28ctl live-preflight (Phase A, zero irreversible)
EXPECTED=a real live-preflight on this Mac with the reviewed LINE instance open, reaching SAVE_ALL_LOCATED and recording a >=10 s gap-free pre-dispatch context digest, with production counters 0/0
OBSERVED=no real live-preflight has been run; every CLI refusal this round is the PID-1 fixture (target process is not the reviewed LINE instance), so Phase A evidence exists only at unit level
```

Resolved fingerprints: `DETERMINISTIC_SWIFT_TEST_COMPILATION` (A1), short-end-date segmentation (A2), equal-tail stability span (A3), C4 goal slot (A4), C4 preflight consumption (A5), C4 typed eligibility/evidence enforcement (A6), `NATIVE_OBSERVATION_SESSION_MISSING` (A7), `UNTYPED_STATE_EVIDENCE` (A8), `PRE_SAVE_ALL_COMPOSITION_MISSING` (A9), `ELLIPSIS_ROW_CONVENTION_MIRRORED` (A10), `NATIVE_PRODUCTION_COMPOSITION_REACHABLE` (A11), `POST_SAVE_ALL_COMPOSITION_MISSING` (A12).

## Convergence counters

```text
MATERIAL_ATTEMPTS_USED: 1 (compile blocker, resolved) / 1 (segmentation blocker, resolved) / 1 (stability blocker, resolved) / 1 (C4 goal slot, resolved) / 1 (C4 preflight, resolved) / 1 (C4 typed evidence enforcement, resolved) / 1 (native observation session, resolved) / 1 (typed state evidence, resolved) / 1 (pre-Save-All composition, resolved) / 1 (ellipsis row convention, resolved) / 1 (native production composition reachable, resolved) / 1 (post-Save-All composition, resolved)
MAX_MATERIAL_ATTEMPTS: 3
CONSECUTIVE_NO_INFORMATION_GAIN: 0
SAME_BLOCKER_GOAL_TURNS_AT_IMPASSE: 0
OSCILLATION_DETECTED: NO
NEXT_BLOCKER_ATTEMPTS_USED: 0/3 (REAL_PHASE_A_PREFLIGHT_EVIDENCE_MISSING)
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
| A11 (rev28ctl production composition) | CLI 進不了已審查的 composition：`rev28ctl` 只有 stub 檢查，沒有 production `ObservationSource`／`ActuationEnvironment`／幾何設定，也沒有不可重啟的 epoch 來源 | 新增 `LiveCompositionFactory`（fail-closed 驗證 budget／frozen rule／locator geometry 後組裝 owner＋session＋adapter＋engine）與 `RunEpochAuthority`（floor 取自 run evidence 內的 `state-<STATE>-<epoch>` 檔名，衝突回 0 讓 bundle 驗證拒絕）；新增 `ProductionObservationSource`（SCK/CG/AX/process/signing）與 `ProductionActuationEnvironment`（GatedQuartzActuator reversible click）；改寫 `rev28ctl` live 區塊走同一 composition；加 7 個 composition＋4 個 epoch tests；刪除死碼 `XCTargetProcess` | 未校準幾何必須在第一次 capture 前被拒（captureCount 0）；組裝後 preflight 走到 `SAVE_ALL_LOCATED`（12 captures、2 reversible、0 irreversible、entitlement 未消耗）；`run()` 在 `dispatchSaveAll` 以 `capabilityNotBuilt` fail closed；CLI 四案例維持 77/77/64/77 | 7/7 composition tests＋4/4 epoch tests PASS；full suite 167 tests / 0 failures；CLI refusal transcript 重現 target-not-LINE 77／CI 77／missing config 64／stale digest 77 | CLI 與 common engine 進入同一 reviewed composition；pre-Save-All 路徑可由 production 程式碼抵達；epoch 不可跨重啟重用 | `execution-evidence/a12-full-suite-live-composition-20260929T054820.log`, `execution-evidence/cli-refusal-20260929T0550/cli-refusal-transcript-20260929T0551.log` | 排除「CLI 無法抵達 composition」與「新 session 可重置 epoch」；確認 Phase B 邊界在 capability 層 fail closed | YES |
| A12 (post-Save-All composition) | `dispatchSaveAll` 之後的 chooser／destination／download／filesystem／content 能力全部是 `capabilityNotBuilt`，Phase B 之前的路徑無法用同一 composition 走完，也無法在注入 boundary 下被證明 | 新增 `PhaseBEligibilityArtifact`（17 predicates、goal-identity digest、run-dir 邊界載入；缺席即拒絕）與唯讀 `FilesystemTripwireJournal`（startedAt 單調時戳、collection-gap 偵測）；新增 `PostSaveEnvironment` protocol 與 `ProductionPostSaveEnvironment`（10 s bounded pre-dispatch context gate、journal failure／gap named refusal、production click 走 `GatedQuartzActuator`）；在 `ComposedNativeAdapter` 實作 dispatch／chooser／destination／download／filesystem／content 全路徑（≥10 s gap-free context → fresh re-locate → baseline re-verify → census → readiness → permit → dispatch boundary → durable records）；`rev28ctl` 新增 chooser predicate／baseline reference／approvedRoot／tripwireRoots／optional eligibility 設定，`live-preflight` 記錄 `preDispatchContextSHA256` | 無 eligibility artifact → `dispatchSaveAll` named refusal 且 0 事件；有 artifact → 恰好一次 guarded click；context gap → 拒絕；download 無法定靜止 → 10 分鐘 cap 終止；baseline 變動 → content 成功宣告被拒 | 27 個 focused tests（PhaseBEligibility 8／ComposedAdapters 12／LiveComposition 7）全 PASS；full suite 181 tests / 0 failures；CLI refusal transcript 重現 77／77／64／77；新 implementation digest `f6ef94dc…a4f68` | C5–C7 全部由同一 composition 提供且經注入 boundary 測試；Phase B 仍 fail closed（無 artifact 即拒絕）；production counters 0/0 | `execution-evidence/a13-focused-postsave-20260929T060456.log`, `execution-evidence/a14-full-suite-phaseb-eligibility-postsave-20260929T060502.log`, `execution-evidence/cli-refusal-20260929T0607/cli-refusal-transcript-20260929T0607.log` | 排除「capability 無法走完」與「eligibility 可隱式 arm」；確認 gap／cap／baseline 變動都在測試中真的拒絕 | YES |

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
```

## Evidence pointers

- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/` — A1–A14 raw logs (build/focused/full suite)
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a12-full-suite-live-composition-20260929T054820.log` — 167 tests / 0 failures（含 live composition 與 epoch authority suites）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/cli-refusal-20260929T0550/` — 前一輪 CLI refusal fixture（c7eb3f9 樹，`b0a71b95…ba0070`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a13-focused-postsave-20260929T060456.log` — 27 focused tests / 0 failures（PhaseBEligibility 8／ComposedAdapters 12／LiveComposition 7）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a14-full-suite-phaseb-eligibility-postsave-20260929T060502.log` — 181 tests / 0 failures（含 post-Save-All composition 與 eligibility suites）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/cli-refusal-20260929T0607/` — CLI refusal fixture（config／rulebook／one-shot／stale-digest config／frozen chooser predicate 的 byte copy）與 transcript；`reviewedImplementationSHA256` 綁定 e407565 的 `rev28/Sources` 樹（`f6ef94dc…a4f68`）
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/a13-focused-postsave-FAILED-intermediate-20260929T060425.log` — 中間失敗的 focused run（test 內 fake clock 與 permit 不一致），修好後由 a13/a14 取代，保留為除錯紀錄
- `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` (SHA-256 `4cb8a6b4…c6560b3`) — reviewed v5 real frame used by the A10 regression test
- `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/analysis/r4-20260928/` — R4 read-only diagnostics (segmentation/stability compile probes, test.log, build.log)
- `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json` (SHA 3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2)
- `evidence/20260925-rev28-native-closed-loop/harness/build-test-log-20260925T1156+0800.txt` — historical 28/0 pass log (pre-regression)
