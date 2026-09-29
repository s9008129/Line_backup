# V-09 attempt-04 — Reviewer Report: 02-timing-automation

- **Task**: T20260925-0647-01-rev28-native-closed-loop (V-09 pre-Phase-A code/rules review, attempt-04: fresh verification of the attempt-03 M-1 repair)
- **Reviewer context**: `02-timing-automation` (C5/C6/C7 timing and automation: dispatch boundary and postcondition clock, intra-click revalidation, durable budgets and reservation enforcement, chooser/destination primitives and accounting, post-dispatch tripwire re-checks, the timing/actuation half of the readiness margin repair)
- **Branch**: `v43-ab/codex-rev28`
- **Bound product tree**: `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`; observed HEAD `5ed71064a9f93d4abc27eecc857e3584a1b2a2ae` (3 `.agent`-only commits above it)
- **Implementation digest (bound and observed)**: `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686` — 48 manifest paths
- **Worktree**: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- **Date**: 2026-09-29 (Asia/Taipei)
- **Read-only statement**: strictly read-only. No build, no test execution, no product binary, no `rev28ctl` invocation, no LINE.app interaction, no OS events, no git write. Producer evidence logs were read and hashed as artifacts only; none of their commands was re-executed. Every verdict below is re-derived from the bytes bound at `cf39fdcc`; nothing from attempt-01/02/03 is cited as proof. Only this report was written.
- **PHASE_B_STATUS**: `FORBIDDEN_AB_EVALUATION`. No Save All dispatch, no destination confirmation, no eligibility arming, no irreversible action.

bindings_verified: PASS (all)

## 1. Bindings verification (independently recomputed)

| Item | Bound | Recomputed | Result |
|---|---|---|---|
| Product tree `cf39fdcc`; `git diff --stat cf39fdcc -- rev28` | empty | empty; `git status --porcelain -- rev28` empty | PASS |
| `git diff --name-only cf39fdcc HEAD` | only `.agent/` | 21 paths, all under `.agent/` | PASS |
| `plan.md` / `handoff.md` SHA-256 | `05413807…f84c1b` / `67fc16a6…c227a33` | identical | PASS |
| Implementation digest | `6734dda5…a686`, 48 paths | own replica of the manifest formula → `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686` | PASS |
| Frozen artifacts (9) | bound map | all 9 re-hashed identical (rulebook `09e1cf2a…`, predicate `0472aa0a…`, calibration `13aa01a2…`, matrix `e0084782…`, tripwire ladder `d67abb17…`, restart fixture `146b373a…`, postcondition bounds `c10dcb43…`, latency observations `ca4beabe…`, freeze provenance `4f6f5fdc…`) | PASS |
| Gate battery on the repaired tree | `a46–a54` | `a46` build complete; `a47` 88/0 (includes the margin regression, lines 669-670); `a48` 242/0/0 skipped; `a50`/`a51` 27/27; `a52`/`a53` byte-identical `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261`; `a54` provenance `status=PASS` generation v3 | PASS |
| CLI refusal fixture `cli-refusal-20260929T0807/` | 77/77/77/64/77; zero side effects | transcript header binds `reviewedImplementationSHA256=6734dda5…a686 (attempt-03 M-1 repair tree)`; EXIT 77/77/77/64/77; `evidence files: 0`, `staging files: 0`, `ledger present: no`, `anchor present: no`, `one-shot renamed: no`; `evidence/` and `staging/` directories independently observed empty; `config-stale-digest.json` differs from `config.json` only at the `reviewedImplementationSHA256` line | PASS |

## 2. Per-claim verdicts (topic-overlapping, re-derived at `cf39fdcc`)

| Claim | Verdict |
|---|---|
| `V09_A2_MAJOR_1_DISPATCH_BOUNDARY_TIMER` | VERIFIED |
| `V09_A2_MAJOR_2_POST_HOVER_REVALIDATION` — timing/actuation half | VERIFIED |
| `V09_A2_MAJOR_3_BUDGET_ENFORCEMENT` | VERIFIED |
| `V09_A2_MINOR_1_AX_VALUE_PRIMITIVE` | VERIFIED |
| `V09_A2_MINOR_2_TRIPWIRE_RECHECK` | VERIFIED |
| `V09_C5_INTRA_CLICK_REVALIDATION_MISSING` (in force) | VERIFIED |
| `V09_C4_BUDGET_NOT_DURABLE` (in force) | VERIFIED |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` (in force; timing/enforcement half) | VERIFIED |
| `V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING` (in force) | VERIFIED |
| `V09_C7_POST_DISPATCH_GAP_UNCHECKED` (in force) | VERIFIED |
| M-1 repair — readiness-gate timing path and consumers | VERIFIED |

### 2.1 `V09_A2_MAJOR_1_DISPATCH_BOUNDARY_TIMER` — VERIFIED

- The boundary is durably recorded under lock before the click: `PostSaveJournalBox.dispatchBoundaryMonotonic` (`Composition/PostSaveComposition.swift:23`), `recordDispatchBoundary(_:)` (`:28-31`), `recordedDispatchBoundary` (`:33-35`); `postSave.markDispatchBoundary()` at `:274`, then `let dispatchBoundary = postSave.monotonicNow()` at `:277` and `journalBox.recordDispatchBoundary(dispatchBoundary)` at `:278`, and only then `postSave.dispatchSaveAllClick(...)` at `:279`.
- The chooser state refuses when no boundary is recorded: `:313-318` ("Save All dispatch boundary is not recorded; the chooser window cannot be deadline-bound").
- The monitor is armed from that boundary, not from a later adapter invocation: `StrictPostconditionMonitor.run(... dispatchBoundaryMonotonic: dispatchBoundary ...)` at `:323`/`:345`; `PostconditionMonitor.swift:239` accepts the boundary, `:252` clamps `start = min(dispatchBoundaryMonotonic ?? now, now)` (a future boundary cannot extend the window), and `:253` sets `deadline = start + bounds.hardCapSeconds` (frozen 15 s bound).

### 2.2 `V09_A2_MAJOR_2_POST_HOVER_REVALIDATION` (timing/actuation half) — VERIFIED

- One-shot consume before any event: `permit.consume(now:)` at `QuartzActuator.swift:483`; binding is re-asserted against the live `currentBinding` at `:484-486`; the intent/candidate identity coupling is enforced (Save All requires the `儲存全部` candidate; reversible refuses it) at `:487-497`.
- Pre-dispatch live guards: `func liveGuards()` (`:500-511`) checks foreground/window readiness, process instance + bundle, `CGPreflightPostEventAccess`, and the topmost addressed surface; invoked at `:514` before the hover.
- Durable accounting happens before the hover: `owner.recordReversibleDispatch(action:)` / `owner.reserveSaveAll()` + `owner.markSaveAllAttempted()` at `:521-525`; `sink(move, .cghidEventTap)` at `:527`.
- After the hover and before mouseDown: `try await postHoverRevalidation(); try liveGuards()` at `:532-535`; any failure durably records the failed revalidation (`recordRevalidationOutcome(intent:passed:)`, `:551-558`) and throws before `mouseDown` is posted (`:537-540`) — zero down/up events on refusal. Success is recorded at `:542`; then `down` (`:543`), 30 ms spacing (`:544`), `up` (`:545`).
- The Save All path supplies the fresh-observation closure from the live environment (`PostSaveComposition.swift:262-273`, call `:268`), so the timing half of this claim uses live facts.

### 2.3 `V09_A2_MAJOR_3_BUDGET_ENFORCEMENT` — VERIFIED

- Reviewed ceilings are single constants: `reversibleCeiling = 12`, `perIdenticalBlockerCeiling = 3`, `consecutiveRevalidationAbortThreshold = 2` (`Policy/ExecutionPolicy.swift:54-56`); the in-memory recorder and the derived exhaustion test share them (`:88-92`, `:95-110`).
- Durable enforcement lives at the owner's write paths: `recordReversibleDispatch` refuses above the global ceiling, the per-identical-blocker ceiling and an already-aborted revalidation history before appending (`Transaction/PersistentTransactionOwner.swift:332-352`); `recordCandidateRevalidation` appends the durable outcome and throws on the second consecutive failure (`:357-368`).
- The derived view is recomputed only from the verified ledger (`:296`, `:319`), and the Phase B entry conjunction consumes it before the one-shot entitlement: `reserveSaveAll` requires located state, a durable `eligibility.phaseB` record, and `!liveDispatchBudget.isExhausted` before `GoalSlot.consumeOneShotEntitlement` (`:403-430`).
- Eligibility predicate set includes `REVERSIBLE_AND_REVALIDATION_BUDGETS_NOT_EXHAUSTED` (`Transaction/PhaseBEligibility.swift:181`, within `requiredPredicates` `:160-182`), and the Save All state re-validates the eligibility artifact with `entitlementConsumed: slot?.entitlementConsumed ?? false` immediately before arming (`PostSaveComposition.swift:197-205`).

### 2.4 `V09_A2_MINOR_1_AX_VALUE_PRIMITIVE` — VERIFIED

`FolderChooserDriver`: the AX value write is re-acquired and durably accounted under its reviewed action name before the write (`:225` `reacquire`, `:226-231` field ownership + settability, `:236` `willPostPrimitive("chooser.navigate.setPathFieldValue")`, `:237` the write); a non-settable field writes nothing and is not recorded. The guard wiring (`:392-397`) re-checks chooser freshness and calls `owner.recordReversibleDispatch(action:)` for every primitive; key primitives go through `postKeyPrimitive` (`:305-315`, `willPostPrimitive` at `:312`, exactly one post, no concealed retry).

### 2.5 `V09_A2_MINOR_2_TRIPWIRE_RECHECK` — VERIFIED

Every download-poll iteration re-checks the post-dispatch gate (`PostSaveComposition.swift:617`); on failure it writes `download-progress-terminal.json` with `terminal: "TRIPWIRE_ABORTED"` and throws. Both completion gates re-check before claiming success: `observeFilesystemStable` (`:664`) and `verifyContent` (`:690`). The gate refuses on collector failure, collector not running, or a collection gap (`Composition/PostSaveEnvironment.swift:295-301`; detail derivation `Transaction/FilesystemTripwireJournal.swift:86-93`), and the post-confirmation facts path re-checks it too (`PostSaveEnvironment.swift:401-403`).

### 2.6 In-force attempt-01 claims — VERIFIED

- `V09_C5_INTRA_CLICK_REVALIDATION_MISSING`: hover (`:527`) → full revalidation + live guards (`:532-535`) → down/up (`:543-545`); refusals post zero events (`:537-539`).
- `V09_C4_BUDGET_NOT_DURABLE`: durable counts derived from the ledger (`PersistentTransactionOwner.swift:296`, `:319`), enforced at `:332-352` and `:357-368`.
- `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` (timing/enforcement half): `reserveSaveAll` requires `.saveAllLocated`, the durable eligibility record and an unexhausted derived budget before consuming the entitlement (`:403-430`).
- `V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING`: all five chooser primitives accounted under their names — `chooser.navigate.goToFolderChord` (`:207`), `setPathFieldValue` (`:236-237`), `clearField` (`:244`), `enterPathText` (`:252`), `returnKey` (`:280`) — each preceded by re-acquisition of the unique verified panel (`:386-397`).
- `V09_C7_POST_DISPATCH_GAP_UNCHECKED`: per-poll and completion-gate re-checks with terminal `TRIPWIRE_ABORTED` evidence (2.5).

### 2.7 M-1 repair — readiness-gate timing path and consumers — VERIFIED

`DispatchReadinessGate.mintPermit` now evaluates the interior margin through `CaptureGeometryRules.isDispatchableCapturePixels(point:safeRect:captureScale: observation.captureGeometry.scale)` (`QuartzActuator.swift:330-333`) while keeping its pre-existing freshness (≤1 s staleness), identity, frame-delta and image-size guards unchanged in order and meaning; the two production mint sites (`PostSaveComposition.swift:241`, `ComposedNativeAdapter.swift:305`) pass the same fresh `ReadinessObservation`. The regression test for the conversion is reviewed in context 01; from the timing perspective the repair changes only the accept/refuse threshold, not the sequence, the guards, or the accounting, and the repaired-tree gate battery (`a47`/`a48`/`a50`/`a51`) plus the byte-identical replay (`a52`/`a53`) show no timing-path drift.

## 3. Out of this context

The trust-boundary dispositions `03-MINOR-C` / `03-MINOR-D` and the eligibility canonical-binding/digest claims are transaction/history scope and are adjudicated by attempt-04 context `03-transaction-history`; this report does not re-adjudicate them.

## 4. Findings

### MAJOR
None.

### MINOR
None.

### INFO

**I-1: line shift after the repair.** M-1 shifted `QuartzActuator.swift` line numbers by +3 relative to attempt-03 citations; all references here are post-repair `cf39fdcc` lines.

**I-2: `recordRevalidationOutcome` uses `try?` on the durable append.** A failing append cannot abort the actuation path silently: the same owner methods are also called by `reserveSaveAll`'s pre-consumption gate and are re-derived from the verified ledger, and the owner's own methods throw before the refusal path where budget exhaustion applies (`PersistentTransactionOwner.swift:357-368`). Noted as an observation only; no fail-open path was found.

**I-3: residual `--one-shot-authorization` flag naming** — the flag name is legacy; the authoritative entitlement is the durable goal slot plus ledger (verified in attempt-04 context 03). No action.

**I-4: `a47` focused log binds the margin regression only by name** — the log shows the test started and passed (lines 669-670) but does not itself assert the numeric cases; the numeric cases are asserted in the source reviewed here (context 01, 3.2). No action.

verdict: PASS
