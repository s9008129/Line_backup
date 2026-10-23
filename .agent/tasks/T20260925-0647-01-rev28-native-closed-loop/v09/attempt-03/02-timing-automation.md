bindings_verified: PASS (all)

# V-09 attempt-03 review — 02-timing-automation (C5/C6/C7 timing and automation)

- **Task**: T20260925-0647-01-rev28-native-closed-loop
- **Branch**: v43-ab/codex-rev28
- **Bound head (product tree under review)**: a758317b725370b008fe58c848e0d28463e86709
- **Bound implementation digest**: e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf (48 files)
- **Reviewer context**: 02-timing-automation — C5/C6/C7 timing and automation: hover→revalidate→mouseDown and its zero-down/up refusal path; chooser postcondition window bound to the recorded Save All dispatch boundary; durable reversible/revalidation budget enforcement; chooser per-primitive accounting including the AX value write; post-dispatch tripwire gate re-checks during download polling and completion.
- **Date**: 2026-09-29 (Asia/Taipei)
- **Read-only statement**: This review ran no build, no tests, no rev28ctl or other product binary, no LINE.app interaction, no OS events, and no git writes. Only `rg`, `sed`, `shasum`, read-only `git show/log/diff/rev-parse/hash-object/merge-base/status`, and read-only Python hashing were used. Producer evidence logs were read but their commands were not executed. Exactly one file was created: this report. `bindings.json` was not modified.
- **Phase B status**: FORBIDDEN_AB_EVALUATION — nothing in this review dispatches Save All, confirms a destination, arms any eligibility artifact, or enables Phase B.

## 1. Bindings verification (observed vs bound)

### 1.1 Tree state

| check | observed | result |
|---|---|---|
| HEAD | 16017b5e7068c9b9f6699dc784971ac41f228291 | info |
| commits after a758317 | 16017b5 (`chore(harness): bind the V-09 attempt-03 review to the repaired tree`), 0d3149b (`chore(harness): record the V-09 attempt-02 findings and repair set`) — both `.agent`-only | PASS |
| `git merge-base --is-ancestor a758317 HEAD` | true | PASS |
| `git diff --stat a758317 -- rev28` | empty | PASS |
| `git diff --name-only a758317 HEAD` | only `.agent/` paths | PASS |
| `git status --porcelain` | clean worktree | PASS |

### 1.2 Plan, handoff, calibration blob, implementation digest

| binding | bound | observed | result |
|---|---|---|---|
| plan.md SHA-256 | 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b | same | PASS |
| handoff.md SHA-256 | 67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33 | same | PASS |
| `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` | c411011b1b44b1efb614e000f526b2118f45d120 | same | PASS |
| implementation digest | e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf | same | PASS |
| digest manifest | 48 files = 36 `rev28/Sources/Rev28Core/**/*.swift` + 9 `rev28/Sources/rev28ctl/**/*.swift` + `rev28/Package.swift` + 2 under `rev28/Tools` | 36+9+1+2 = 48; algorithm sha256 over sorted (repo-relative path + NUL + bytes + NUL) re-implemented independently in Python | PASS |

### 1.3 Frozen rule artifacts (9)

| artifact | bound = observed SHA-256 | result |
|---|---|---|
| `evidence/20260925-rev28-native-closed-loop/harness/frozen/capture-geometry-rulebook-v1.json` | 09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed | PASS |
| `.../frozen/chooser-affirmation-predicate-v2.json` | 0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2 | PASS |
| `.../frozen/chooser-ax-calibration-v2.json` | 13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569 | PASS |
| `.../frozen/capture-matrix-v1.json` | e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b | PASS |
| `.../frozen/tripwire-attribution-ladder-v1.json` | d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216 | PASS |
| `.../frozen/restart-observe-only-fixture-v1.json` | 146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f | PASS |
| `.../frozen/postcondition-bounds-v3.json` | c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84 | PASS |
| `.../frozen/postcondition-latency-observations-v3.json` | ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155 | PASS |
| `evidence/20260925-rev28-native-closed-loop/harness/ci-w2-item5-freeze-provenance-v3.json` | 4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152 | PASS |

`postcondition-bounds-v3.json` observed contents: `hardCapSeconds: 15`, `fastPhaseSeconds: 8`, `fastCadenceMs: 150`, `slowCadenceMs: 500`, `lateForensicSampleDelaySeconds: 30`, `maxObservedMs: 155.18903732299805`, `measuredRuns: 20` — consistent with the bound latency-evidence hash `ca4beabe…`.

### 1.4 Repaired-tree evidence a37–a45 (paths under `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/execution-evidence/`, as referenced by bindings.json)

| file | observed SHA-256 | quoted summary line(s) observed | result |
|---|---|---|---|
| a37-build-attempt02-final-20260929T074109.log | 2d6ff8835618ee49f928ff358ed8280425ae811b007103eb28630fae83e2e381 | `Build complete! (0.15s)` (line 5), `Build complete! (0.10s)` (line 10) | PASS |
| a38-focused-attempt02-final-20260929T074114.log | 033e9be945fd6dad512e992e922c2e6891b5860a48e7526bd4fdcf5a3600f652 | `Executed 96 tests, with 0 failures (0 unexpected) in 7.275 (7.281) seconds` (line 226) | PASS |
| a39-full-suite-attempt02-final-20260929T074124.log | 3113cad17b3207f7a87b2ea4ecf8d66d2a5a739c0ab2f7eb5951e8cc88a0933f | `Executed 241 tests, with 0 failures (0 unexpected) in 9.492 (9.505) seconds` (line 566); no skip-count line exists; the only match for "Skipped" is the test name `…testMalformedArtifactIsNamedNotSkipped` (lines 344–345), so 0 skipped is supported by absence of any skip event | PASS |
| a40-adversarial-attempt02-final-run1-20260929T074153.log | de1d8f49e9ddb9aca2fae220f7aba43749830015fa1a774112bd445834427d28 | `Executed 27 tests, with 0 failures (0 unexpected) in 0.012 (0.013) seconds` (line 66) | PASS |
| a41-adversarial-attempt02-final-run2-20260929T074153.log | 09286e2d86bc288cf9cb770ccf4895b7d3512262c10c622cc7be95981955febc | `Executed 27 tests, with 0 failures (0 unexpected) in 0.010 (0.012) seconds` (line 66) | PASS |
| a42-replay-attempt02-final-run1-20260929T074157.json | 81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261 | `fixture_count: 20`, `expected_fixture_count: 20`, `verdict: "PASS"`, `failures: []` | PASS |
| a43-replay-attempt02-final-run2-20260929T074157.json | 81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261 | same as a42; the two outputs are byte-identical (same SHA-256) | PASS |
| a44-provenance-attempt02-final-20260929T074210.log | 3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a | `"status": "PASS"`, `"generation": "v3"`, `"implementationSourceGitBlobSHA": "c411011b1b44b1efb614e000f526b2118f45d120"`, `"sampleCount": 20`, `"maxLatencyMs": 155.18903732299805` | PASS |
| a45-digest-attempt02-final-20260929T074221.log | d4188b0a0879c8c57c86765a52456414a3ebe7b582e7e3e7183b4ef5c95f86dd | `ZZDIGEST_SHA256=e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf`, `ZZDIGEST_PATHCOUNT=48` | PASS |

Note (not a discrepancy): a44 also carries `"validatedImplementationCommit": "2ecfeb9c1803d9ab184e69381b0a340e69bd46ea"`, which is the commit the hosted CI freeze was validated against when the v3 provenance was generated; the attempt-03 bindings claim only `status=PASS`, `generation v3` and blob `c411011b…`, all of which re-verified.

### 1.5 CLI refusal fixture `execution-evidence/cli-refusal-20260929T0742/`

| item | observed | result |
|---|---|---|
| transcript SHA-256 | 20567f37179592b339cdc3320ff220f97f0c0edc89ae06b4ae0a06ce3e3a0a56 | info |
| dispatch-refusal exits | `live-execute` EXIT=77 (`target process is not the reviewed LINE instance`); `live-preflight` EXIT=77 (same); CI guard EXIT=77 (`live execution is disabled in CI`); missing `--config` EXIT=64; stale digest EXIT=77 (`one-shot authorization or plan digest mismatch`) — 77/77/77/64/77 | PASS |
| fixture digest binding | transcript header `reviewedImplementationSHA256=e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf (attempt-02 repair tree)` | PASS |
| side effects | transcript `evidence files: 0`, `staging files: 0`, `ledger present: no`, `anchor present: no`, `one-shot renamed: no`; independently re-checked: `evidence/` and `staging/` subdirectories are empty and no ledger/anchor/consumed-named file exists | PASS |
| frozen fixtures in the dir | `chooser-predicate.json` SHA-256 `0472aa0a…`, `chooser-calibration.json` SHA-256 `13aa01a2…` (match the bound frozen artifacts) | PASS |

Attempt-01/02 reports were read only as prior context and were not used as proof. The superseded-digest evidence (a29–a36, cli-refusal-20260929T0713) was not relied upon, per the bindings.

## 2. Scope, inputs, checks

- Inputs: `v09/attempt-03/bindings.json` (binding contract), `plan.md`, `handoff.md`, `progress.md`, this context's topic claims, and the prior attempt-02 claim identifiers still listed as in force.
- Code re-read at bound tree a758317 (verified unchanged per 1.1): `PostSaveComposition.swift`, `PostconditionMonitor.swift`, `QuartzActuator.swift`, `ExecutionPolicy.swift`, `PersistentTransactionOwner.swift`, `FolderChooserDriver.swift`, `PhaseBEligibility.swift`, `GoalSlot.swift`, `FilesystemTripwireJournal.swift`, `PostSaveEnvironment.swift`, `ActuationReadinessTests.swift`, `PostconditionMonitorTests.swift`.
- Every binding in section 1 was recomputed by me on the current worktree; no hash was copied from attempt-01/02 artifacts or from producer claims alone.
- Claims out of this context (perception-geometry, transaction-history eligibility/digest items such as `V09_A2_MAJOR_A_CANONICAL_ELIGIBILITY_BINDINGS`, `DIGEST_MANIFEST`, `V09_AX_IDENTITY_WINDOW_UNBOUND`, `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING`, predicate derivation, goal-slot atomicity, one-shot marker, resume-continuation, menu bounds, provenance qualifier) were not adjudicated here; only their timing/automation-overlapping parts (budget enforcement, reservation exhaustion guard) are covered below.

## 3. Per-claim verdicts (topic-overlapping, re-derived at a758317)

### V09_A2_MAJOR_1_DISPATCH_BOUNDARY_TIMER — VERIFIED
- `rev28/Sources/Rev28Core/Composition/PostSaveComposition.swift:13` (`PostSaveJournalBox`), `:23`/`:28-35` (`recordDispatchBoundary`/`recordedDispatchBoundary` with lock), `:274` (`markDispatchBoundary`), `:277-278` (`let dispatchBoundary = postSave.monotonicNow(); journalBox.recordDispatchBoundary(dispatchBoundary)`), `:279-284` (`dispatchSaveAllClick` invoked only after the boundary is recorded), `:295` (`SaveAllDispatchRecord.dispatchBoundaryMonotonicNanos`), `:315-318` (refuse `CHOOSER_VERIFIED` when `recordedDispatchBoundary == nil` with detail “Save All dispatch boundary is not recorded; the chooser window cannot be deadline-bound”), `:345` (`dispatchBoundaryMonotonic: dispatchBoundary` passed into `StrictPostconditionMonitor.run`).
- `rev28/Sources/Rev28Core/Postcondition/PostconditionMonitor.swift:239` (`dispatchBoundaryMonotonic: Double? = nil`), `:252` (`let start = min(dispatchBoundaryMonotonic ?? now, now)` — a future boundary cannot extend the window), `:253` (`deadline = start + bounds.hardCapSeconds`; frozen bound 15 s).
- `plan.md:257` (“Pre-dispatch chooser/process inventories saved; strict observer armed with the reviewed clock/deadline”) — satisfied; the timer origin is the recorded dispatch boundary, not a later adapter invocation.

### V09_A2_MAJOR_2_POST_HOVER_REVALIDATION (timing half) — VERIFIED
- `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift:482` (`permit.consume(now:)` — one-shot permit consumed before any event), `:524` (`sink(move)` hover), `:531-532` (`try await postHoverRevalidation(); try liveGuards()` after the hover and before down), `:534` (`recordRevalidationOutcome(passed: false)`), `:540` (`sink(down)`), `:541` (`usleep(30_000)`), `:542` (`sink(up)`) — any revalidation/guard failure throws before `:540`, so zero down/up events are posted.
- `:371-421` `revalidateAfterHover`: applicationActive, targetFrontmost, windowID/pid/process/bundleID/layer==0/onScreen identity, `currentBinding`, scale/capture-image validity, staleness `now - observedAtUptime <= 1.0`, frame deltas ≤ 0.5 pt, safe-rect containment/in-bounds, addressed screen-point delta ≤ 0.5 pt.
- `:436-454` `topmostSurfaceMatchesTarget`: front-to-back `CGWindowListCopyWindowInfo`; the first alpha > 0 window whose bounds contain the point must be the target windowID + pid at layer 0, else false.
- `:497-510` `liveGuards`: readiness, process-instance identity, `CGPreflightPostEventAccess`, addressed/topmost surface; `:456-478` `postClick` defaults `addressedSurfaceCheck` to `topmostSurfaceMatchesTarget`.
- Save All path wires the fresh-observation closure at `rev28/Sources/Rev28Core/Composition/PostSaveComposition.swift:262-271` and passes it through `rev28/Sources/Rev28Core/Composition/PostSaveEnvironment.swift:350-361`.
- Tests: `rev28/Tests/Rev28CoreTests/ActuationReadinessTests.swift:240-274` asserts the failure path posts only `.mouseMoved` (`no down/up`) and records the durable failure.

### V09_A2_MAJOR_3_BUDGET_ENFORCEMENT — VERIFIED
- `rev28/Sources/Rev28Core/Policy/ExecutionPolicy.swift:48-124`: `LiveDispatchBudget` with `isExhausted` (`:88`), `consumeReversible` (`:94`), `recordCandidateRevalidation` (`:104`), `consumeSaveAll` (`:115`), `consumeDestinationConfirmation` (`:120`); ceilings 12/3/2 match `plan.md:138`.
- `rev28/Sources/Rev28Core/Transaction/PersistentTransactionOwner.swift:291-316` (all counters derived from ledger entries: `dispatch.reversible`, `budget.blocker`, `budget.revalidation`, `intent/attempt.saveAll`), `:319-327` (`liveDispatchBudget` derived view), `:332-352` (`recordReversibleDispatch` durable appends `dispatch.reversible` + `budget.blocker` and refuses at ceilings), `:357-368` (`recordCandidateRevalidation` appends `budget.revalidation` before throwing at 2 consecutive failures), `:423` (`guard !liveDispatchBudget.isExhausted` → `phaseBBudgetExhausted`) executed before `:425-430` consumes the one-shot entitlement.
- Production writer: `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift:548-554` (`recordRevalidationOutcome`) called at `:534`/`:539`.
- `rev28/Sources/Rev28Core/Transaction/PhaseBEligibility.swift:160-182`: 18 required predicates, including `REVERSIBLE_AND_REVALIDATION_BUDGETS_NOT_EXHAUSTED` at `:181` (count is 18; the 19th regex hit was comment text at `:178-180`).
- `plan.md:138` (persist all reversible counts, per-blocker counts and consecutive revalidation failures in the owner; derived views only) — satisfied.

### V09_A2_MINOR_1_AX_VALUE_PRIMITIVE — VERIFIED
- `rev28/Sources/Rev28Core/Chooser/FolderChooserDriver.swift:225-238`: `primitiveGuard.reacquire("chooser.navigate.setPathFieldValue")` (`:225`), `fieldIsOwned` (`:226`), settable check (`:230-231`), `try primitiveGuard.willPostPrimitive("chooser.navigate.setPathFieldValue")` (`:236`) immediately before `AXUIElementSetAttributeValue` (`:237`); non-settable fields write nothing and are not recorded.
- Guard wiring: `:392-396` — `willPostPrimitive` re-checks chooser freshness and calls `owner.recordReversibleDispatch(action:)` (`:396`).

### V09_A2_MINOR_2_TRIPWIRE_RECHECK — VERIFIED
- Download polling: `rev28/Sources/Rev28Core/Composition/PostSaveComposition.swift:589-638` — every `while` iteration re-checks the gate at `:616-637`; on failure it writes `download-progress-terminal.json` with `terminal: "TRIPWIRE_ABORTED"` and throws instead of silently completing.
- Completion gates: `observeFilesystemStable` re-check at `:662-664`; `verifyContent` re-check at `:688-690`.
- Gate implementation: `rev28/Sources/Rev28Core/Composition/PostSaveEnvironment.swift:295-301` (`postDispatchTripwireGate`), plus the post-confirmation gate at `:401-403` and disclosure at `:176`/`:419-420`; `rev28/Sources/Rev28Core/Transaction/FilesystemTripwireJournal.swift:86-93` (`postDispatchRefusalDetail`: startup failure / collector not running / collection gap).

### V09_C5_INTRA_CLICK_REVALIDATION_MISSING (attempt-01, still in force) — VERIFIED
- `QuartzActuator.swift:524` hover → `:531-532` readiness/process/postEvent/addressed revalidation → `:540-542` down/up; `:533-538` refusal records the failure and posts no down/up.

### V09_C4_BUDGET_NOT_DURABLE (attempt-01, still in force) — VERIFIED
- `PersistentTransactionOwner.swift:291-316` (ledger-recomputed views), `:332-352` (`recordReversibleDispatch` per-action ≤ 3 durable), `:357-368` (2-consecutive durable revalidation abort, written before the error surfaces).

### V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING (attempt-01, still in force) — VERIFIED
- All five primitives recorded: `FolderChooserDriver.swift:207` (`chooser.navigate.goToFolderChord`), `:236` (`chooser.navigate.setPathFieldValue`), `:244` (`chooser.navigate.clearField`), `:252` (`chooser.navigate.enterPathText`), `:279` (`chooser.navigate.returnKey`, via `postKeyPrimitive` `:305-315` with `willPostPrimitive` at `:312`); the guard re-acquires/verifies the unique panel per primitive (`:386-397`).

### V09_C7_POST_DISPATCH_GAP_UNCHECKED (attempt-01, still in force) — VERIFIED
- As `V09_A2_MINOR_2`: per-poll and completion-gate re-checks with terminal `TRIPWIRE_ABORTED` evidence; `tripwireCollectionGapDisclosure` surfaces the gap in the tripwire artifact.

## 4. Trust boundary dispositions (reasoning; no code change expected)

- **03-MINOR-C — crash window between entitlement consumption and the durable `intent.saveAll` append — VERIFIED (reasoning).** Retry of `reserveSaveAll` reaches `GoalSlot.consumeOneShotEntitlement`, maps `entitlementAlreadyConsumed` to `PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll")` (`PersistentTransactionOwner.swift:425-430`). Restart with retained slot and empty ledger refuses at owner init (`:188-190`, `goalSlotEntitlementConsumed`), and `dispatchSaveAll` re-validation passes `slot?.entitlementConsumed ?? false` into `PhaseBEligibility.validate` (`PostSaveComposition.swift:195-201`), which refuses with `.entitlementConsumed` at `PhaseBEligibility.swift:260`. Every observed recovery path fails closed.
- **03-MINOR-D — goal-slot identity includes the staging root — VERIFIED (reasoning).** `GoalSlot.canonicalDirectory` is derived from `authorization.stagingRoot` (`GoalSlot.swift:62-66`) and the slot file key is `[goal, group, album, stagingRoot]` NUL-joined (`:69-70`); consistent with `plan.md:134` (“persistent goal slot, keyed to this task/group/album/approved new-path authorization”), the approved root being part of the reviewed authorization.
- **01-MINOR-1 — locator menu/addressable bounds** is perception-geometry scope; not adjudicated by this context.

## 5. Findings

### MAJOR
None.

### MINOR
None.

### INFO
1. **Boundary recorded before the true mouseDown instant (conservative).** `PostSaveComposition.swift:274-284` records the boundary before `dispatchSaveAllClick` performs the durable intent writes, hover, revalidation and down/up, so the effective window start is ≤ the true dispatch instant; `PostconditionMonitor.swift:252` additionally clamps a future boundary. The window can never extend beyond the actual dispatch.
2. **`recordRevalidationOutcome` swallows durable-append errors with `try?`** (`QuartzActuator.swift:548-554`). The refusal itself still surfaces (the throw happens after the `try?`), and subsequent dispatches pass through `recordReversibleDispatch`, whose own durable append fails closed; but the “durably recorded failure” is best-effort for an I/O error at that single append. No unsafe path observed; relates to `plan.md:138` durability intent.
3. **No unit test passes a non-nil `dispatchBoundaryMonotonic` to `StrictPostconditionMonitor.run`** (rg over `rev28/Tests` finds zero occurrences; `PostconditionMonitorTests.swift:172/196/206/218` call `run` without it). The boundary-bound behavior was verified by source read only.
4. **Hardcoded inter-event delay remains** — `usleep(30_000)` between down and up (`QuartzActuator.swift:541`); no frozen artifact binds this constant (same item flagged in attempt-02 as INFO-1).
5. **Download observation clock starts after the AX press returns** — `PostSaveComposition.swift:514` calls `confirmDefaultButton` (AXPress at `FolderChooserDriver.swift:469`) and `:523` records the confirmation clock afterwards; the 10-minute observation cap (`:589-607`) therefore measures from after the press returns rather than from the press instant (same item flagged in attempt-02 as INFO-3).

verdict: PASS
