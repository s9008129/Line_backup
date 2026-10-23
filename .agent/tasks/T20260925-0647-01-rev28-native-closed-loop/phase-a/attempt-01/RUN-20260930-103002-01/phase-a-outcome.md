# Phase A attempt-01 — RUN-20260930-103002-01（2026-09-30）

## Scope
- One-shot human authorization: 使用者明示同意（2026-09-30，對話中），範圍＝本次 read-only Phase A run 恰好一次。
- Frozen product tree: `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`；ReviewedImplementationDigest = `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`（48 paths，runtime precondition 已重算比對）。
- Binary: `rev28/.build/debug/rev28ctl`（`swift build --product rev28ctl` no-op＝與凍結樹一致）。
- Config: `config.json`（結構比照 cli-refusal fixture；chooser binding = canonical frozen v2 predicate `0472aa0a…f3f2` / calibration `13aa01a2…e569`；rulebook = `capture-geometry-rulebook-v1.json`）。
- Staging run dir: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260930-103002-01`（空）。

## Command (executed exactly once)
`rev28ctl live-preflight --config config.json --one-shot-authorization one-shot-authorization.json`

## Result: REFUSED (PRECONDITION)
- EXIT=77
- stderr（逐字）：`live-preflight refused: targetWindowNotUnique(found=2)`
- 判讀：目標 LINE 視窗不唯一（identity selector 實測 found=2）→ fail-closed 拒絕；未進入 observation／state establishment。
- Phase A per-condition report（phase-a.json）與 raw evidence manifest：**未產生**（evidence dir 為空）。不得以任何形式記為 PASS。

## Irreversible / side-effect counters（從 ledger 實測）
- `intent.saveAll` = 0；`attempt.saveAll` = 0
- `intent.destinationConfirmation` = 0；`attempt.destinationConfirmation` = 0
- irreversible counters = **0/0/0**；無 chooser、無 Save All、無 reversible dispatch 證據（evidence dir 空）。
- ledger 唯一 entry：`transaction.authorization`（1 筆）。
- Goal slot：`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/goal-slots/5f7e18ba…f017a.goal-slot.json`（bound，`consumedAtISO8601` 不存在＝entitlement 未消耗）。
- Baseline：未被觸碰（run 未到達 baseline 驗證階段即拒絕）。

## Artifacts & SHA-256
- `live-preflight-20260930T103016.log` — `656566da050eff76da4708ed47d3242df2e042fc16161f1301dee9cf2bab23fc`
- `ledger.jsonl` — `02c4097bc5705070b99e42aa3b56d15c268fd9c59b1b38db9fc7faca34fa1e45`
- `ledger-head.anchor` — `373a45d11c006c68782cba06c18a00e4415af0cdbb4d30534544f25f27d29102`

## Next
- 不 retry（本次授權為一次性，已用罄；contract：FAIL → 不猜測、不重試）。
- Blocker fingerprint（new）：`PHASE_A_TARGET_WINDOW_NOT_UNIQUE(found=2)` — 為環境性前置，非 code defect（尚無 evidence 指向實作缺陷）。
- 人類唯一動作：讓 LINE 只剩一個符合的目標視窗（關閉多餘 LINE 視窗），保持目標相簿 surface 可見。
- 之後若要再跑：需新的 fresh runID＋使用者新的明示一次性授權（Phase A attempt 2；budget 未重置）。

## Addendum — post-refusal read-only window probe（2026-09-30，diagnostic only；非 Phase A per-condition evidence）
CGWindowList（pid 1212、layer 0、on-screen）實測 = **2**，與 run 的 `targetWindowNotUnique(found=2)` 一致：
- `id=191` layer=0 onscreen=true name=`LINE` frame=(-1,35,1147,699) ← 主要大視窗
- `id=996` layer=0 onscreen=true name=（無） frame=(30,45,327,643) ← 第二個 on-screen 視窗（須由使用者處置）

判讀：attempt-02 在「on-screen layer-0 LINE 視窗數 ≠ 1」之前不得執行，否則必再 refusal（不燒授權、不燒 attempt）。使用者處置後，agent 需再以唯讀 probe 複查＝1 才執行 attempt-02。
