# V-09 attempt-02 — timing & automation review (context 02)

- task_id: `T20260925-0647-01-rev28-native-closed-loop`
- stage: 04 (pre-Phase-A V-09 code/rules review, attempt-02)
- branch / worktree: `v43-ab/codex-rev28` @ `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- reviewer context: 02-timing-automation
- phase_b_status: `FORBIDDEN_AB_EVALUATION` — nothing in this review enabled, simulated or requested a production Save All dispatch
- reviewed binding: `v09/attempt-02/bindings.json` (head `42ae9a3fe026e1d3888001efeede88fde5dbb7cc`, digest `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9`)
- recorded_at: 2026-09-29 (Asia/Taipei)

## bindings_verified: PASS (all)

Recomputed read-only before code reading. Every value observed equals the frozen binding.

### Repository / provenance

| item | observed | result |
|---|---|---|
| `git rev-parse HEAD` | `7cd444e152daede802e21430f1501e17ddfd3784` | see note |
| `git diff --stat 42ae9a3 -- rev28` | empty (0 files) | PASS |
| `git diff --name-only 42ae9a3 HEAD` | 20 files, all under `.agent/` | PASS |
| `plan.md` sha256 | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | PASS |
| `handoff.md` sha256 | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | PASS |
| implementation digest (44 `.swift`; sha256 over sorted repo-relative path + NUL + bytes + NUL) | `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9` | PASS |
| `HarnessCalibration.swift` git blob | `c411011b1b44b1efb614e000f526b2118f45d120` (worktree `git hash-object` == `git ls-tree 42ae9a3`) | PASS |

Note on HEAD: the orchestrator's expected head `0ce9e05…` is present in history but two further commits landed after it, `96ef88c` and `7cd444e`, both `.agent`-records-only. The rev28 product tree is byte-identical to the bound head `42ae9a3` (`diff --stat` empty, 0 files), so the reviewed tree is the bound tree. Formula cross-checked against `rev28/Sources/Rev28Core/Transaction/ReviewedImplementationDigest.swift:30-50` (sorts paths, appends relative path + `0` + bytes + `0`).

### Frozen artifacts (all 9 match bindings)

- `capture-geometry-rulebook-v1.json` = `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed`
- `chooser-affirmation-predicate-v2.json` = `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2`
- `chooser-ax-calibration-v2.json` = `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569`
- `capture-matrix-v1.json` = `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b`
- `tripwire-attribution-ladder-v1.json` = `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216`
- `restart-observe-only-fixture-v1.json` = `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f`
- `postcondition-bounds-v3.json` = `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84`
- `postcondition-latency-observations-v3.json` = `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155`
- `ci-w2-item5-freeze-provenance-v3.json` = `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152`

### Evidence logs (`.agent/tasks/.../execution-evidence/`)

- a29 `a29-build-v09-repairs-provenance-restore-20260929T0722.log` sha256 `8e4deaf4f02dea1e713d0cf2a08e2e323621d4e2ce10ef7e9d81b87a427aa50c`; line 10 `Build complete! (5.06s)`.
- a30 `a30-focused-v09-repairs-provenance-restore-20260929T0722.log` sha256 `f98fa449fa5ea8911fdc378b96d7f47a88fd75740eaa2f3dab6adae6cd1ee0ac`; lines 201/203 `Executed 80 tests, with 0 failures (0 unexpected) in 3.284 (3.288) seconds`.
- a31 `a31-full-suite-v09-repairs-provenance-restore-20260929T0723.log` sha256 `02742ae768f9ba4440a94ec14279d2e3ab021effe430a951b258cd147af54484`; lines 520/522 `Executed 222 tests, with 0 failures (0 unexpected) in 4.840 (4.849) seconds`.
- a32 `a32-provenance-v09-repairs-provenance-restore-20260929T0726.log` sha256 `3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a`; line 1 JSON `"generation": "v3"`, `"status": "PASS"`, `"implementationSourceGitBlobSHA": "c411011b1b44b1efb614e000f526b2118f45d120"`.
- Superseded first repair revision (recorded in bindings only): a27 sha256 `ecfcb8def948753e69e5d9a0a2f35e06ab123c4b86df2e3be7e885ce78f22a4e` (lines 200/202: 80/0); a28 sha256 `e789e2b37b5794d81adcf877b4036971b5e9f8befb1d5353c30d52a9bbef15c9` (lines 520/522: 222/0) — hashes match the bindings' superseded note; not accepted as current proof.
- Prior context: `v09/attempt-01/02-timing-automation.md` is bound to superseded digest `eb4415f9…` (43 files) and was used only to compare against previously reported issues.

## Topic / scope

Timing and automation surfaces of the repaired tree: `GatedQuartzActuator.postClick` intra-click revalidation (permit consumption, post-hover refusal); permits and deadlines; durable reversible / per-blocker / consecutive-revalidation budgets (`PersistentTransactionOwner.liveDispatchBudget`, `recordReversibleDispatch`, `recordCandidateRevalidation`, `ExecutionPolicy`); `FolderChooserDriver` destination navigation per-primitive reacquisition/accounting (`DestinationPrimitiveGuard`, `verifyDestination`/`prepareDestination`); chooser predicate production wiring (`rev28ctl/main.swift` frozen-bytes → `ChooserProductionPredicate.derive` → v2 `evaluateProduction`) and `ChooserAffirmationEvaluator` semantics; the postcondition monitor; and Phase B prevention paths. Phase B itself is out of scope and forbidden.

## Inputs inspected

- Binding/contract: `v09/attempt-02/bindings.json`, `plan.md`, `handoff.md`, `v09/attempt-01/02-timing-automation.md` (context only), the 9 frozen artifacts, execution-evidence a27–a32.
- Sources: `Rev28Core/Actuation/QuartzActuator.swift`, `Rev28Core/Policy/ExecutionPolicy.swift`, `Rev28Core/Transaction/PersistentTransactionOwner.swift`, `Rev28Core/Transaction/LiveExecutionEngine.swift`, `Rev28Core/Transaction/GoalSlot.swift`, `Rev28Core/Transaction/PhaseBEligibility.swift`, `Rev28Core/Transaction/ReviewedImplementationDigest.swift`, `Rev28Core/Transaction/FilesystemTripwireJournal.swift`, `Rev28Core/Chooser/FolderChooserDriver.swift`, `Rev28Core/Chooser/ChooserAffirmationPredicate.swift`, `Rev28Core/Postcondition/PostconditionMonitor.swift`, `Rev28Core/Composition/PostSaveComposition.swift`, `Rev28Core/Composition/PostSaveEnvironment.swift`, `Rev28Core/Composition/ComposedNativeAdapter.swift`, `Rev28Core/Composition/ProductionActuationEnvironment.swift`, `Rev28Core/Composition/ProductionObservationSource.swift`, `Rev28Core/Composition/PhaseAEvidence.swift`, `Rev28Core/Observation/NativeObservationSession.swift`, `Rev28Core/Sensor/FrameCapture.swift`, `Rev28Core/Identity/AXWindowIdentitySelector.swift`, `Rev28Core/Identity/WindowIdentity.swift`, `rev28ctl/main.swift`, `rev28ctl/HarnessCalibration.swift`, `rev28ctl/FolderChooserDriver.swift` (legacy, harness-only).
- Tests (read-only): `ActuationReadinessTests.swift`, `ChooserPredicateProductionDerivationTests.swift`, `ExecutionPolicyTests.swift`, `GoalSlotTests.swift`.

## Checks performed

1. Recomputed every hash in `bindings.json` (HEAD/branch state, plan/handoff, 44-file implementation digest, 9 frozen artifacts, HarnessCalibration blob, a27–a32 evidence) and compared against the frozen values (all PASS; see above).
2. Traced the permit path: minting checks (`QuartzActuator.swift:296-346`), single-use consumption and 1.0 s expiry (`:278-291`), pre-hover guards (`:378-398`), durable owner record before dispatch (`:404-409`), hover, post-hover revalidation, down/up (`:411-424`); call sites `PostSaveEnvironment.swift:354` and `ProductionActuationEnvironment.swift:39-43` (neither supplies a custom `readinessCheck`, so the defaults at `QuartzActuator.swift:361-375` are the production closures).
3. Traced the durable budgets: ledger-derived counts (`PersistentTransactionOwner.swift:289-325`), `recordReversibleDispatch` (`:330-340`), `recordCandidateRevalidation` (`:345-356`), reservation enforcement (`reserveSaveAll :391-414`, `reserveDestinationConfirmation :495-510`, `preIntentContinuationAllowed :247-256`, `isPostIrreversibleResume :176-179`) and their production call sites via grep across `rev28`.
4. Traced destination navigation primitives and accounting (`FolderChooserDriver.swift:198-295`, `300-311`, `351-407`, `428-470`; `GatedDestinationConfirmation :76-91`) and checked the primitive names/ceiling keys against `plan.md:138`.
5. Traced the postcondition monitor (`PostconditionMonitor.swift:26-44`, `234-308`), its invocation site (`PostSaveComposition.swift:274-290`), the dispatch boundary (`:249-250`) and the engine call order (`LiveExecutionEngine.swift:155-204`).
6. Traced the chooser predicate production wiring (`main.swift:158-184`, `ChooserProductionPredicate.swift:179-228`, `ChooserAffirmationEvaluator.swift:307-390`) and the tripwire gate/disclosure (`FilesystemTripwireJournal.swift:80-125`, `PostSaveEnvironment.swift:294-300/401/416-418`, `PostSaveComposition.swift:318-325/503-640`).
7. Traced Phase B prevention: eligibility artifact load/validate (`main.swift:186-207`), adapter gate (`PostSaveComposition.swift:163-191`), owner gate (`PersistentTransactionOwner.swift:358-389`, `:391-414`) and the default command branch (`main.swift:424-430`).
8. Grepped for un-gated primitive reachability: `QuartzActuator.postClick(at:)` (ungated click) is reachable only from `rev28ctl/HarnessCalibration.swift:1607-1670`; the legacy `rev28ctl/FolderChooserDriver.swift` union-window/Return-key driver is referenced only by `HarnessCalibration.swift:1925-1967`; the live composition uses `Rev28Core`'s driver (`PostSaveEnvironment.swift:369/388`).

## Repair-claim verdicts (topic-overlapping)

| claim | verdict | evidence |
|---|---|---|
| `V09_C5_INTRA_CLICK_REVALIDATION_MISSING` | VERIFIED (as scoped) | `QuartzActuator.swift:415-421` re-runs readiness/process/postEvent between hover (`:411`) and down (`:422`); permit consumed at `:378`; failed revalidation yields no down/up; `ActuationReadinessTests.swift:154-180` asserts 2 readiness calls and `posted == [.mouseMoved]`. See MAJOR-2 for the residual C5 geometry/occlusion gap. |
| `V09_C4_BUDGET_NOT_DURABLE` | PARTIAL | Durability/derivation verified (`PersistentTransactionOwner.swift:289-356`; per-blocker ceiling wired through `:391`/`:406` and `FolderChooserDriver.swift:391`); the consecutive-revalidation counter has no production writer (see MAJOR-3). |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` | VERIFIED | `reserveSaveAll :391-414` requires `.saveAllLocated` + durable `eligibility.phaseB` record; `reserveDestinationConfirmation :495-510` requires `.destinationPrepared` + `saveAll>=2` + `postcondition.chooserVerified` + action whitelist; `preIntentContinuationAllowed :247-256`; `recordPhaseBEligibility :358-389` re-validates the artifact at the owner. |
| `V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING` | PARTIAL | Chords/key/text/Return primitives are recorded per action (`FolderChooserDriver.swift:207`, `300-311`, `387-393`); the AX value write is only reacquired (`:225-233`) and not recorded (see MINOR-1). |
| `V09_C7_POST_DISPATCH_GAP_UNCHECKED` | PARTIAL | Gate invoked per chooser sample (`PostSaveEnvironment.swift:305`) and once at post-confirmation (`:401`); not re-invoked during download polling/completion (see MINOR-2). |
| `V09_CHOOSER_PREDICATE_V2_NOT_DERIVED` | VERIFIED | `main.swift:158-184` hash-verifies frozen predicate+calibration bytes, derives v2, refuses non-process-stable; `evaluateProduction` (`ChooserAffirmationPredicate.swift:379-390`) requires v2; `ChooserPredicateProductionDerivationTests.swift:80-114`. |
| `V09_ELIGIBILITY_LABEL_ONLY` | VERIFIED | `PhaseBEligibility.swift:213-246` re-reads plan/handoff/frozen/predicate bytes and compares the recomputed implementation digest; invoked at `PersistentTransactionOwner.swift:358-389` and `main.swift:200-207`. |
| `V09_GOALSLOT_NON_ATOMIC_WRITE` | VERIFIED | `GoalSlot.swift:178-216` temp write + fsync + `rename(2)` + parent-directory fsync; `GoalSlotTests.swift`. |
| `V09_ONESHOT_MARKER_INERT` | VERIFIED | `Transaction/OneShotAuthorization.swift` absent; `main.swift:128-135` refuses live-preflight on a consumed goal-slot entitlement. |
| `V09_ENGINE_RESUME_CONTINUATION_NARROW` | VERIFIED | `LiveExecutionEngine.swift:139-153`: non-continuation resumes return `.observeOnlyResume`; continuation re-establishes pre-save states from fresh facts (`:155-156`). |
| `V09_MENU_BOUNDS_UNBOUND` | VERIFIED | `NativeObservationSession.swift:502-507` requires menu+addressable bounds inside the retained image; `ComposedNativeAdapter.swift:187-194`/`245-252` refuse when unconfigured; `FrameCapture.swift:154-164` requires exactly one display with a known scale; Phase A records the five-row menu localization obligation (`handoff.md:144`); no frozen LINE menu-bounds artifact exists. |
| `V09_CHOOSER_PROVENANCE_QUALIFIER` | VERIFIED | Qualifier text and deferred runtime gate at `PhaseAEvidence.swift:505-507`, `947-952`, `963`; frozen predicate file unchanged (`0472aa0a…`). |
| calibration-harness AX read intentionally frozen | VERIFIED | Claimed frozen read is `HarnessCalibration.swift:2479` (`AXDriver.windows(ofApp: harnessPID()).first`); blob `c411011b…` matches a32 provenance and the `42ae9a3` tree; production observation path uses the bound selector (`ProductionObservationSource.swift:106-127`). |
| `V09_AX_IDENTITY_WINDOW_UNBOUND` (context 01 primary; inspected read-only) | VERIFIED | `ProductionObservationSource.readAXIdentity :106-127` binds via `AXWindowIdentitySelector`; `AXIdentityRead.isBoundToWindow` (`WindowIdentity.swift:81`) enforced at `NativeObservationSession.swift:239`; no `windows[0]` in the production AX path. |

## Findings

### MAJOR-1 — The chooser postcondition timer is not bound to the actual Save All dispatch boundary

- Plan: `plan.md:158` — “Bind the timer to the actual Save All dispatch boundary, not a later adapter invocation.”
- Observed: the engine dispatches Save All and observes the chooser as two separate adapter calls (`LiveExecutionEngine.swift:157` then `:164`). `PostSaveComposition.swift:249` calls `markDispatchBoundary()` (which only switches the FSEvents journal phase) and `:250` posts the click; the observation window is started later inside `observeChooser` (`PostSaveComposition.swift:274` → `StrictPostconditionMonitor.run` `:283`), whose clock starts at `PostconditionMonitor.swift:246` (`let start = monotonicNow()`, deadline `:247`). `run` has no dispatch-time parameter (`PostconditionMonitor.swift:234-243`), and no dispatch timestamp is threaded into the monitor. The cadence phase (8 s) and the 15 s hard cap are therefore measured from a later adapter invocation; an affirmation that completes after `dispatch + 15 s` can still be classified `chooserVerified` when it completes within 15 s of monitor start (the effective cap since dispatch is `gap + 15 s`).
- Impact: C6’s deadline origin is wrong; the hard success cap can be effectively exceeded after a slow dispatch→observe gap (e.g. evidence writes at `PostSaveComposition.swift:252-269`).

### MAJOR-2 — Post-hover intra-click revalidation is a subset of C5’s facts (no geometry/frame, topmost-surface or candidate re-derivation)

- Plan: `plan.md:152` — “Post mouseMoved, then revalidate these facts and candidate **before mouseDown**. Focus theft/occlusion/geometry change must yield zero down/up if down has not been posted.”
- Observed: the post-hover guard (`QuartzActuator.swift:415-421`) re-runs only `readinessCheck` (default production closure `:361-369`: app active + frontmost + CG window inventory membership by windowNumber/ownerPID/layer==0), `processIdentityCheck` (`:370-375`: bundleID + `ProcessInstanceID`) and `postEventAccessCheck` (`:376`). It does not repeat the mint-time freshness/geometry checks (`:296-346`: `WindowIdentityValidator.isFresh` with 0.5 pt tolerance, `captureGeometry` vs `freshWindow` 0.5 pt comparison `:325-331`, candidate binding/frame-hash binding `:307-312`, 1 s observation staleness `:337`) and never re-derives the addressed/topmost surface at the permit’s screen point. A frame move or same-process occlusion occurring between the hover and the mouseDown therefore does not refuse; the down is posted at the point computed at mint time.
- Positives verified: the permit is consumed before any post (`:378`), a failed post-hover guard throws before `sink(down)` (asserted by `ActuationReadinessTests.swift:154-180`), the permit is single-use, and no second click/retry can follow (`:422-424`).

### MAJOR-3 — The durable consecutive-revalidation abort has no production writer; the derived budget is never consulted

- Plan: `plan.md:138` — “Persist all reversible counts, per-identical-blocker counts and consecutive candidate revalidation failures in this owner… maximum 3 per identical blocker; 2 consecutive failed revalidations abort.” Also `plan.md:257` includes “reversible/revalidation budgets not exhausted” in the Phase B eligibility conjunction.
- Observed: `PersistentTransactionOwner.recordCandidateRevalidation` (`:345-356`) is the only writer of `budget.revalidation` (`:349`) and has no production call site — a repo-wide grep finds it only at its definition and in `ExecutionPolicyTests.swift:36-46` (derived view). `liveDispatchBudget` (`:317-325`) has no production consumer (grep: definition only); `consecutiveCandidateRevalidationFailures` (`:308-314`) is read only at `:323`/`:348`. `reserveSaveAll` (`:391-414`) does not consult the reversible/revalidation budget, and `PhaseBEligibility.requiredPredicates` (`PhaseBEligibility.swift:95-107`) has no budget/revalidation predicate, so the Phase B entry condition at `plan.md:257` is not machine-checked.
- Mitigation observed: every production revalidation failure currently throws on the first failure (`QuartzActuator.swift:415-421`; `GatedDestinationConfirmation.perform` `FolderChooserDriver.swift:76-91`; `chooserIsFresh` refusal `:376-382`), so no unsafe retry after a failed revalidation exists today. The defect is that the plan’s durable abort rule and budget-derived Phase B condition are inert in production, not that a retry escaped a ceiling.
- What is genuinely wired: `recordReversibleDispatch` (`:330-340`) persists both the global count and the per-blocker key, and is called from `QuartzActuator.swift:406` and `FolderChooserDriver.swift:391`.

### MINOR-1 — The AX value write is re-acquired but not durably accounted as an input primitive

- Plan: `plan.md:138` (“A compound destination preparation logs/checks every input primitive…”) and `plan.md:164` (“For every AX/key primitive reacquire chooser/Go-to-folder identity…”) .
- Observed: `FolderChooserDriver.swift:225-233` performs `primitiveGuard.reacquire("chooser.navigate.setPathFieldValue")` plus an ownership check before `AXUIElementSetAttributeValue`, but `reacquire` is explicitly non-recording (`:104-105`) and only `willPostPrimitive` calls `recordReversibleDispatch` (`:387-393`, used at `:207` and via `postKeyPrimitive :300-311`). So four of five navigation primitives (⇧⌘G, ⌘A, text entry, Return) are recorded separately; the AX attribute write is checked but absent from the durable budget ledger.

### MINOR-2 — Post-dispatch tripwire gaps are not re-checked during download polling or completion

- Plan: `plan.md:172` — “Dropped events/collector failure cannot become an empty clean tripwire. Maintain monitoring across dispatch, chooser, navigation, confirmation and completion.”
- Observed: the gate (`PostSaveEnvironment.swift:294-300`, backed by `FilesystemTripwireJournal.postDispatchRefusalDetail :86-93`) is invoked per chooser sample (`:305`) and once in `postConfirmationFacts` (`:401`). The download loop (`PostSaveComposition.swift:544-592`) polls `stagingSnapshot` (`:571`) directly; `observeFilesystemStable` (`:594-615`) and `verifyContent` (`:617-640`) never consult the gate, and `tripwireCollectionGapDisclosure` is only written into the chooser artifact (`PostSaveComposition.swift:324`). A collection gap arising after the download-start observation (window up to 10 minutes, `plan.md:178`) is never surfaced or disclosed.

### INFO-1 — Hardcoded inter-event delay at the gated layer

`QuartzActuator.swift:423` uses `usleep(30_000)` between down and up with no injectable seam at the gated boundary (the legacy un-gated `postClick` has `usleep(interEventDelayMicroseconds)` at `:116`). Test-timing note only; no behavioural defect observed.

### INFO-2 — `ReturnKey` whitelist / `confirmWithReturnKey` remain but are unreachable in production

`PersistentTransactionOwner.swift:504` still admits `"ReturnKey"` as a confirmation action, and `FolderChooserDriver.confirmWithReturnKey` exists (`:421-423`), but there is no production call site; the only production confirmation is the single `AXPressDefaultButton` through `GatedDestinationConfirmation` (`FolderChooserDriver.swift:428-470`), matching `plan.md:168` (“No Return fallback or second AXPress on non-effect”).

### INFO-3 — Download observation clock starts after the AXPress returns

`PostSaveComposition.swift:471-482` calls `confirmDefaultButton` first and then `journalBox.recordConfirmation(at: postSave.monotonicNow())`; the 10-minute cap (`plan.md:178`, `downloadObservationCapSeconds = 600` at `PostSaveComposition.swift:82`) is measured from after the press returns rather than the dispatch instant. Bounded by the AXPress duration; not a safety issue observed.

### INFO-4 — Legacy rev28ctl driver paths are harness-only; frozen calibration AX read is intentional

The union-window/Return-key legacy driver (`rev28ctl/FolderChooserDriver.swift`) and the un-gated `QuartzActuator.postClick(at:)` are reachable only from `HarnessCalibration.swift` (`:1607-1670`, `:1925-1967`); the live path uses `Rev28Core` via `PostSaveEnvironment.swift:369/388`. The calibration harness’s frozen AX read (`HarnessCalibration.swift:2479`) is the intentional v3-frozen bytes documented in the bindings; provenance a32 PASS with source blob `c411011b…`.

## Verdict

verdict: ISSUES_FOUND

Three MAJOR (timer origin not bound to the dispatch boundary; incomplete post-hover revalidation of C5’s geometry/occlusion facts; durable consecutive-revalidation abort unwired and derived budget unconsumed), two MINOR (AX value write unrecorded; tripwire gate not re-checked at completion), four INFO. All frozen bindings, digests, artifact hashes and evidence logs recomputed clean. Phase B remains `FORBIDDEN_AB_EVALUATION`; no production Save All dispatch was enabled, simulated or requested.
