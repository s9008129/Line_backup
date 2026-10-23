# V-09 attempt-02 — reviewer context 03: transaction & history

- Task: `T20260925-0647-01-rev28-native-closed-loop`, Stage 04, A/B branch `v43-ab/codex-rev28`
- Worktree: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Reviewer context: `03-transaction-history`; this is V-09 attempt-02, bound to the corrected (CI-freeze-restored) tree
- Date of review: 2026-09-29 (+0800); read-only review: no build, no test execution, no `rev28ctl`, no product binary, no LINE.app interaction, no OS events, no git writes
- Phase B status during this review: `FORBIDDEN_AB_EVALUATION`; nothing in this report arms, simulates or requests a production Save All dispatch

## bindings_verified: PASS (all)

All values below were recomputed by this reviewer in this worktree with read-only commands. Producer logs were read, never executed.

### Git state

| Item | Bound value | Observed | Result |
|---|---|---|---|
| Binding head | `42ae9a3fe026e1d3888001efeede88fde5dbb7cc` | `42ae9a3` is the bound product-tree commit; current `git rev-parse HEAD` = `7cd444e152daede802e21430f1501e17ddfd3784` | PASS with recorded nuance |
| Orchestrator pre-check (`0ce9e05…`) | — | HEAD had advanced from `0ce9e05` to `7cd444e` via two `.agent`-record-only commits (`96ef88c`, `7cd444e`); `git diff --name-only 42ae9a3 HEAD` contains zero non-`.agent/` paths | PASS |
| `git diff --stat 42ae9a3 -- rev28` | empty | empty (no output) | PASS |

The two post-`0ce9e05` commits only append execution-evidence/binding records (`git log --oneline 42ae9a3..HEAD`: `7cd444e`, `96ef88c`, `0ce9e05`), so the reviewed product tree is byte-identical to the bound `42ae9a3`.

### Contract artifacts

| Item | Bound SHA-256 | Observed SHA-256 | Result |
|---|---|---|---|
| `plan.md` | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | PASS |
| `handoff.md` | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | PASS |

### Implementation digest

| Item | Bound value | Observed | Result |
|---|---|---|---|
| Digest | `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9` | `e80e4f0fb5483ec9a7e1c795e62662235dcfcdd884276d2fd25c9d22a5a254e9` | PASS |
| File count | 44 | 44 | PASS |
| Formula | sha256 over sorted (repo-relative path + NUL + file bytes + NUL) for every `.swift` under `rev28/Sources/Rev28Core` + `rev28/Sources/rev28ctl` | reproduced with `find … -name '*.swift' \| LC_ALL=C sort` + NUL-joined material piped to `shasum -a 256` | PASS |

### Frozen artifacts (9/9)

(Paths in the two tables below are worktree-relative; the six evidence logs live under `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/`.)

| Artifact | Bound SHA-256 | Observed | Result |
|---|---|---|---|
| `harness/frozen/capture-geometry-rulebook-v1.json` | `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed` | identical | PASS |
| `harness/frozen/chooser-affirmation-predicate-v2.json` | `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` | identical | PASS |
| `harness/frozen/chooser-ax-calibration-v2.json` | `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569` | identical | PASS |
| `harness/frozen/capture-matrix-v1.json` | `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b` | identical | PASS |
| `harness/frozen/tripwire-attribution-ladder-v1.json` | `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` | identical | PASS |
| `harness/frozen/restart-observe-only-fixture-v1.json` | `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` | identical | PASS |
| `harness/frozen/postcondition-bounds-v3.json` | `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84` | identical | PASS |
| `harness/frozen/postcondition-latency-observations-v3.json` | `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155` | identical | PASS |
| `harness/ci-w2-item5-freeze-provenance-v3.json` | `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152` | identical | PASS |

### CI-freeze provenance (the reason for the superseding revision)

- `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` = `c411011b1b44b1efb614e000f526b2118f45d120` — equals `ci_freeze_provenance.frozen_source_blob_sha` in `bindings.json`. PASS.
- The frozen bytes are visible at `rev28/Sources/rev28ctl/HarnessCalibration.swift:2479` (`AXDriver.windows(ofApp: harnessPID()).first`), i.e. the calibration driver intentionally keeps the pre-repair AX read; the C3 binding repair lives in the production observation path (`ProductionObservationSource.readAXIdentity(pid:windowID:)`, `rev28/Sources/Rev28Core/Composition/ProductionObservationSource.swift:106`). PASS (documented entry).

### Execution evidence (read-only inspection of producer logs)

| Log | Observed SHA-256 | Summary lines observed |
|---|---|---|
| `execution-evidence/a29-build-v09-repairs-provenance-restore-20260929T0722.log` | `8e4deaf4f02dea1e713d0cf2a08e2e323621d4e2ce10ef7e9d81b87a427aa50c` | `Build complete! (5.06s)` (line 10) |
| `execution-evidence/a30-focused-v09-repairs-provenance-restore-20260929T0722.log` | `f98fa449fa5ea8911fdc378b96d7f47a88fd75740eaa2f3dab6adae6cd1ee0ac` | `Executed 80 tests, with 0 failures (0 unexpected)` (lines 201/203) |
| `execution-evidence/a31-full-suite-v09-repairs-provenance-restore-20260929T0723.log` | `02742ae768f9ba4440a94ec14279d2e3ab021effe430a951b258cd147af54484` | `Executed 222 tests, with 0 failures (0 unexpected)` (lines 520/522); no test-skipped lines (only a test *named* `…IsNamedNotSkipped`, line 328–329) |
| `execution-evidence/a32-provenance-v09-repairs-provenance-restore-20260929T0726.log` | `3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a` | `{"generation": "v3", "status": "PASS", "implementationSourceGitBlobSHA": "c411011b1b44b1efb614e000f526b2118f45d120", "validatedImplementationCommit": "2ecfeb9c1803d9ab184e69381b0a340e69bd46ea", "harnessRunID": "HARNESS-20260925-105114", …}` |
| `execution-evidence/a27-focused-v09-repairs-20260929T0707.log` (superseded) | `ecfcb8def948753e69e5d9a0a2f35e06ab123c4b86df2e3be7e885ce78f22a4e` | `Executed 80 tests, with 0 failures` (lines 200/202) |
| `execution-evidence/a28-full-suite-v09-repairs-20260929T0708.log` (superseded) | `e789e2b37b5794d81adcf877b4036971b5e9f8befb1d5353c30d52a9bbef15c9` | `Executed 222 tests, with 0 failures` (lines 520/522) |

`bindings_verified: PASS (all)`. No binding mismatch was observed. Evidence logs are producer evidence; this reviewer executed none of the commands they record.

## Topic / scope

Transaction & history surfaces: `GoalSlot` (identity, atomic install, flock, one-shot entitlement), `IntentLedger` (append/chain/anchor, resume decisions), `PersistentTransactionOwner` (irreversible-boundary flags, durable eligibility record, owner-level reservation enforcement, durable budgets, destination-prepared state), `PhaseBEligibilityArtifact.validateWithRecomputedEvidence` + `PhaseBEligibilityRecomputation` + `ReviewedImplementationDigest`, the post-dispatch tripwire refusal gate (`FilesystemTripwireJournal.postDispatchRefusalDetail`, `PostSaveEnvironment.postDispatchTripwireGate`) and chooser-evidence recording, `LiveExecutionEngine` resume/observe-only paths, `main.swift` live-preflight/live-execute refusal paths (incl. the deleted `OneShotAuthorization`), and the restart/adversarial semantics in the relevant test files (read, never run).

## Inputs inspected

- `.agent/tasks/…/v09/attempt-02/bindings.json`; `plan.md`; `handoff.md`; attempt-01 `03-transaction-history.md` (prior context only)
- Product sources (read): `rev28/Sources/Rev28Core/Transaction/{GoalSlot,IntentLedger,PersistentTransactionOwner,PhaseBEligibility,ReviewedImplementationDigest,LiveExecutionEngine,FilesystemTripwireJournal,StateEvidence,TripwireAttribution}.swift`; `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift`; `rev28/Sources/Rev28Core/Chooser/FolderChooserDriver.swift`; `rev28/Sources/Rev28Core/Composition/{PostSaveComposition,PostSaveEnvironment,ProductionObservationSource,ProductionActuationEnvironment,PhaseAEvidence}.swift`; `rev28/Sources/Rev28Core/Identity/{AXWindowIdentitySelector,WindowIdentity}.swift`; `rev28/Sources/Rev28Core/Composition/LiveComposition.swift`; `rev28/Sources/rev28ctl/main.swift`; `rev28/Sources/rev28ctl/HarnessCalibration.swift` (frozen region only)
- Tests (read, never executed): `GoalSlotTests`, `IntentLedgerTests`, `PersistentTransactionOwnerTests`, `PhaseBEligibilityTests`, `EligibilityTestSupport`, `LiveExecutionEngineTests`, `AdversarialMatrixTests`, `ComposedAdaptersTests`, `TripwirePostDispatchGateTests`, `ChooserPredicateProductionDerivationTests`
- Frozen artifacts and the six execution-evidence logs listed above

## Checks performed

1. Recomputed head/diff state, plan/handoff hashes, 44-file implementation digest, 9 frozen artifact hashes, `HarnessCalibration.swift` blob hash, and the SHA-256 + result lines of a27–a32. All as tabulated above.
2. Traced every transaction/recovery path named in the scope, including ordering of fsyncs, locks, ledger appends, checkpoint writes, entitlement consumption, reservations and refusals; cross-read the call sites in `PostSaveComposition`/`PostSaveEnvironment`/`FolderChooserDriver`/`QuartzActuator`/`main.swift`.
3. Read each `repair_claims_to_verify` entry overlapping this topic and classified it against the code (table below).
4. Read the adversarial/restart tests to check what semantics are actually exercised (not what their names suggest), and looked for new issues introduced by the repairs (resettable entitlement, replayable eligibility, unverified resume, budget persistence bypass, tripwire-disclosure gaps).
5. Verified nothing was armed: `phase_b_status = FORBIDDEN_AB_EVALUATION`; the observed code paths refuse without an explicitly validated eligibility artifact, and this round supplies none. No dispatch was simulated or requested.

## Findings

### MAJOR A — the eligibility artifact's handoff / frozen-artifact / predicate bindings are self-declared and their paths are uncontained

Plan requirement — `plan.md:254`: "exact reviewed implementation source manifest + HEAD/diff state + binary hash + rule/predicate/fixture/provenance hashes, and all required independent review bindings current"; `plan.md:261`: "Any FAIL, UNKNOWN, NOT_RUN, missing/stale hash or unbound evidence => PHASE_B_INELIGIBLE, zero irreversible dispatch."

Observed implementation:
- `PhaseBEligibilityArtifact` stores `handoffPath`/`handoffSHA256`, `frozenArtifactPaths`/`frozenArtifactSHA256` and per-predicate `evidencePath`/`evidenceSHA256` — all supplied by the artifact itself (`rev28/Sources/Rev28Core/Transaction/PhaseBEligibility.swift:65`, `:122`, `:126`).
- Structural validation only enforces hex shape and that the path/hash key sets match each other; there is no required artifact-name set (`PhaseBEligibility.swift:186`–`:191`, `:202`).
- `validateWithRecomputedEvidence` re-reads and re-hashes exactly those self-declared paths and compares them to the artifact's own declared hashes: handoff at `PhaseBEligibility.swift:227`–`:229`, frozen artifacts at `:230`–`:237`, predicate evidence at `:238`–`:243`. Nothing compares them with the canonical reviewed values (bindings `handoff_sha256 = 67fc16a6…c227a33`, the 9 frozen hashes, or the config-bound `chooserPredicateSHA256`/`chooserCalibrationSHA256` that `main.swift:83`–`:84`/`:158`–`:163` verifies separately).
- Path containment covers only the artifact file itself (`PhaseBEligibility.swift:248`–`:256`); `handoffPath`, `frozenArtifactPaths[*]` and `predicates[*].evidencePath` may point anywhere readable.
- The genuinely recomputed bindings are plan bytes (`PhaseBEligibility.swift:220`–`:222` against `authorization.planSHA256`), implementation digest (`:223`–`:225` against `authorization.reviewedImplementationSHA256`; recomputed from the tree at `main.swift:110`–`:117`) and run/goal identity (`:171`–`:183`, `:134`–`:137`). The plan bullet's "binary hash" and "HEAD/diff state" have no representation in the artifact or the live config at all (only bundle-ID/signing-identity/process-interval checks exist, e.g. `main.swift:119`–`:121`, `ChooserAffirmationPredicate.swift:327`).
- Impact: with a locally crafted artifact (self-declared handoff/frozen/predicate paths + hashes) the machine-checkable eligibility conjunction can be satisfied without the actual Stage 03 contract or review evidence being bound. The plan explicitly calls for a machine-checkable conjunction with "exact reviewed … rule/predicate/fixture/provenance hashes" and treats unbound evidence as `PHASE_B_INELIGIBLE`, so this is a plan-conformance gap, not merely a hardening wish. Mitigation observed: this AB round arms no artifact, and dispatch re-validates at the owner boundary (`PostSaveComposition.swift:180`–`:188`, `PersistentTransactionOwner.swift:363`–`:387`), so the gap is a forgery-resistance gap rather than a currently-open dispatch path.

### MAJOR B — post-hover revalidation omits the candidate, geometry and topmost-surface facts the plan requires before `mouseDown`

Plan requirement — `plan.md:152`: "Post mouseMoved, then revalidate these facts and candidate **before mouseDown**. Focus theft/occlusion/geometry change must yield zero down/up if down has not been posted."

Observed implementation (`rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift`):
- `postClick` (`:358`–`:423`) consumes the permit (`:378`), compares `permit.binding == currentBinding` (`:379`–`:381` — `currentBinding` is the same observation bundle the permit was minted from; see `PostSaveComposition.swift:250`–`:254` and `PostSaveEnvironment.swift:349`–`:359`), checks readiness/process/postEvent access once (`:392`–`:398`), posts the hover (`:411`), then re-checks only readiness/process/postEvent access (`:415`–`:418`) before `mouseDown` (`:422`).
- The production `readinessCheck` closure (`:362`–`:375`) verifies only that the app is active/frontmost and that the target window is still on-screen with matching owner/layer; it does not re-verify window geometry, the addressed/topmost surface at the click point, or that the structural candidate still exists and matches its frame/geometry.
- The mint-time permit does bind candidate + geometry + window-identity freshness and a ≤1 s observation age (`DispatchReadinessGate.mintPermit`, `QuartzActuator.swift:295`–`:346`), but none of those facts is re-derived after the hover; `ReadinessPermit.consume` re-checks only one-shot/expiry (`:280`–`:293`).
- Therefore a geometry change or occlusion that arrives after the hover while the process stays frontmost and the window stays on-screen still posts `mouseDown`/`up` at the stale point, contrary to the plan's "focus theft/occlusion/geometry change must yield zero down/up". The repair claim is literally true (readiness/process/postEvent access *are* re-checked), but the plan's full "these facts and candidate" set is not.
- Test note: `AdversarialMatrixTests.testG07PopupMovementInvalidatesCandidateAtGuardedBoundary` (`rev28/Tests/Rev28CoreTests/AdversarialMatrixTests.swift:167`–`:186`) and `testG14FocusTheftPostsZeroEventsAtGuardedBoundary` (`:238`–`:253`) pass a changed binding / a failing readiness check at entry, i.e. they exercise the pre-hover checks; no test drives a change occurring between the hover and the re-check. `ExecutionPolicyTests`/`ActuationReadinessTests` cover the mint-time evaluator (`AdversarialMatrixTests.swift:476`–`:481`).

### MINOR C — crash window between entitlement consumption and durable `intent.saveAll` append

`PersistentTransactionOwner.reserveSaveAll` (`rev28/Sources/Rev28Core/Transaction/PersistentTransactionOwner.swift:391`–`:413`) requires the durable eligibility record (`:405`–`:407`), consumes the goal-slot entitlement (`:408`–`:411`) and only then appends `intent.saveAll` (`:412`). A failure of the append leaves a consumed entitlement with no durable intent. All observed recovery paths still fail closed: retry maps `entitlementAlreadyConsumed` to `irreversibleIntentAlreadyRecorded` (`:409`–`:411`), and a restart that tries to continue reaches `dispatchSaveAll`'s eligibility re-validation with `entitlementConsumed = true` (`PostSaveComposition.swift:182`–`:188`) and refuses. The forensic record, however, cannot distinguish "entitlement consumed, intent lost" from "reservation never started" except by comparing the slot against the ledger. MINOR (ordering/forensics), not a dispatch-safety gap.

### MINOR D — the goal-slot identity includes the staging root, so a re-pointed approved root yields a fresh entitlement

`GoalSlot.fileURL` keys the slot on `goal`/`group`/`album`/`stagingRoot` (`rev28/Sources/Rev28Core/Transaction/GoalSlot.swift:68`–`:70`) and `canonicalDirectory` derives the slot directory from `stagingRoot` (`:61`–`:65`). Within one approved root, churn of run ID/destination/ledger is refused because the record verification binds the run identity and run directory (`GoalSlot.load` `:102`–`:110`, `verify` `:148`–`:171`; `GoalSlotTests.swift:108`–`:130`, `:172`–`:197`). Re-pointing `stagingRoot` itself, however, both changes the key and relocates the `goal-slots` directory, so a fresh unconsumed slot is created. Plan `plan.md:134` keys the slot to "task/group/album/approved new-path authorization", so a genuinely re-approved new path arguably starts a new identity; what is missing is any in-product distinction between "re-approved new root" and "operator-supplied replacement". Recorded as a MINOR/trust-boundary note (the approved-root value is part of the reviewed authorization config), not asserted as a violation.

### INFO E — `live-execute` would dispatch before its unconditional exit 78 if an artifact were armed

`rev28/Sources/rev28ctl/main.swift:424`–`:430` runs `composition.engine.run()` and only afterwards writes the "no irreversible dispatch is authorized in this round" message and `exit(78)`; `LiveExecutionEngine.run()` itself calls `adapter.dispatchSaveAll(owner:)` (`rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift:151`) once the pre-Save states are established. AB-round prevention therefore rests on (a) no eligibility artifact being supplied (`dispatchSaveAll` refuses "not armed", `PostSaveComposition.swift:168`–`:172`), and (b) the owner-level eligibility record + reservation gates (`PersistentTransactionOwner.swift:363`–`:387`, `:391`–`:413`) — not on a code constant. Combined with MAJOR A, a crafted artifact is the theoretical arming path; it still has to survive plan/implementation recomputation and the owner gates. Related residue: the CLI still requires a `--one-shot-authorization` JSON file (`main.swift:56`–`:59`, usage line `:436`) whose runID/plan/implementation triple is checked (`:108`–`:117`) but which consumes nothing — the `OneShotAuthorization` module is gone, the marker is inert as claimed, but the flag name now overstates what it is.

### INFO F — post-dispatch gate sampling points and remaining coverage holes

`FilesystemTripwireJournal.postDispatchRefusalDetail` (`rev28/Sources/Rev28Core/Transaction/FilesystemTripwireJournal.swift:86`–`:93`) reports collector failure/stopped collector/gap, and `PostSaveEnvironment.postDispatchTripwireGate` refuses on them (`rev28/Sources/Rev28Core/Composition/PostSaveEnvironment.swift:294`–`:301`). The gate is called inside `sampleChooserFacts` (`:305`) and `postConfirmationFacts` (`:401`); `recordChooserVerified` additionally requires a gap-free, non-aborting, digest-revalidated tripwire artifact (`PersistentTransactionOwner.swift:444`–`:455`, `:459`–`:473`). A gap that opens after the chooser artifact is written but before the confirmation AXPress is not re-checked ahead of that press (`prepareDestination`/`confirmDefaultButton` do not call the gate; grep shows callers only at those two points); it is disclosed and refused at the post-confirmation gate after the press. No plan line was found that requires a mid-navigation gap to block input (the pre-chooser attributable-write refusal is enforced at chooser verification), so this is recorded as INFO. Also remaining from attempt-01: `AdversarialMatrixTests.testG21RestartAfterSaveAllCannotRedispatch` (`:443`–`:448`) is still ledger-only; destination/baseline/tamper coverage lives in `ComposedAdaptersTests`, `PersistentTransactionOwnerTests` and `TripwirePostDispatchGateTests`.

## `repair_claims_to_verify` — verdicts (topic-overlapping)

| Claim | Verdict | Evidence |
|---|---|---|
| V09_AX_IDENTITY_WINDOW_UNBOUND | VERIFIED | `AXWindowIdentitySelector.select` prefers exact AX window number, else a unique ≤0.5 pt frame match, else refuses (`rev28/Sources/Rev28Core/Identity/AXWindowIdentitySelector.swift:60`–`:97`); `AXIdentityRead.isBoundToWindow` (`WindowIdentity.swift:81`); `NativeObservationSession.swift:239` refuses unbound reads; production `readAXIdentity(pid:windowID:)` binds to the target window (`ProductionObservationSource.swift:106`–`:126`). Frozen calibration driver intentionally keeps `windows(ofApp:).first` (`HarnessCalibration.swift:2479`, blob `c411011b…`, a32 PASS) |
| V09_C5_INTRA_CLICK_REVALIDATION_MISSING | VERIFIED (literal) | `QuartzActuator.swift:415`–`:418` re-runs readiness/process/postEvent after the hover; see MAJOR B for the remaining plan gap |
| V09_C4_BUDGET_NOT_DURABLE | VERIFIED | `liveDispatchBudget` derived from the verified ledger (`PersistentTransactionOwner.swift:317`–`:324`); `recordReversibleDispatch` global 12 / per-blocker 3 durability (`:330`–`:335`); `recordCandidateRevalidation` 2-consecutive durable (`:345`–`:353`); `IntentLedgerTests` read-only: `:22`–`:39`, `:117`–`:142` |
| V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING | VERIFIED | `mayEnterIrreversibleBoundary` (`:235`–`:237`), `preIntentContinuationAllowed` (`:247`–`:256`), durable eligibility record (`:363`–`:387`), `reserveSaveAll` requires `.saveAllLocated` + eligibility + slot consume (`:391`–`:413`), `reserveDestinationConfirmation` requires `.destinationPrepared` + `saveAll` attempt + one-shot chooser record (`:495`–`:509`) |
| V09_C6_PER_PRIMITIVE_ACCOUNTING_MISSING | VERIFIED | `DestinationPrimitiveGuard` re-acquires chooser identity and durably records each primitive before posting (`rev28/Sources/Rev28Core/Chooser/FolderChooserDriver.swift:98`–`:118`, `:380`–`:394`); confirmation intent/attempt fsynced before the single AXPress and consumed on post-intent readiness loss (`GatedDestinationConfirmation.perform`, `:72`–`:92`) |
| V09_C7_POST_DISPATCH_GAP_UNCHECKED | VERIFIED | `FilesystemTripwireJournal.swift:86`–`:93`; gate at `PostSaveEnvironment.swift:294`–`:301`, invoked at `:305` and `:401`; disclosure at `:416`–`:418`; owner record requires `collectionGap == nil` (`PersistentTransactionOwner.swift:444`–`:445`). See INFO F for the sampling-point note |
| V09_CHOOSER_PREDICATE_V2_NOT_DERIVED | VERIFIED (code-level) | `main.swift:151`–`:182` hash-verifies the frozen predicate + calibration bytes, derives via `ChooserProductionPredicate.derive` and refuses non-process-stable versions; test `ChooserPredicateProductionDerivationTests.swift:80`, `:104` (read, not run) |
| V09_ELIGIBILITY_LABEL_ONLY | PARTIAL | Bytes are genuinely re-read/re-hashed (`PhaseBEligibility.swift:213`–`:243`) and the implementation digest is recomputed and shared (`ReviewedImplementationDigest.swift:27`–`:52`), but handoff/frozen/predicate bindings remain self-declared and their paths uncontained — see MAJOR A |
| V09_GOALSLOT_NON_ATOMIC_WRITE | VERIFIED | temp write + fsync (`GoalSlot.swift:188`–`:192`), `rename(2)` install (`:195`–`:207`), parent-directory fsync (`:208`–`:216`); `GoalSlotTests.swift:54`–`:106` (read, not run) |
| V09_ONESHOT_MARKER_INERT | VERIFIED | `OneShotAuthorization.swift` absent from the tree (bindings delta; `rg` finds no symbol); preflight observe-only refusal is goal-slot based (`main.swift:128`–`:135`); residual `--one-shot-authorization` file name only, see INFO E |
| V09_ENGINE_RESUME_CONTINUATION_NARROW | VERIFIED | observe-only unless `preIntentContinuationAllowed` (`LiveExecutionEngine.swift:136`–`:155`); continuation re-establishes remaining states from fresh live evidence (`:227`–`:258`); `runPreflight` requires zero irreversible records (`:264`–`:270`); tests `LiveExecutionEngineTests.swift:299`–`:395` (read, not run) |
| V09_MENU_BOUNDS_UNBOUND | not verified in this context | perception/geometry topic (01); left to that context |
| V09_CHOOSER_PROVENANCE_QUALIFIER | not verified in this context | postcondition/chooser-automation topic (02/06); left to that context |
| calibration-harness frozen AX read | VERIFIED | blob `c411011b1b44b1efb614e000f526b2118f45d120` = frozen source blob; a32 `status=PASS`, `generation v3` |

Restart/adversarial semantics read (not run): irreversibility resume is permanently observe-only and zero events are posted (`LiveExecutionEngineTests.swift:299`, `AdversarialMatrixTests.swift:443`); pre-intent resume continues only remaining states with fresh evidence and stays observe-only without a verified anchor (`LiveExecutionEngineTests.swift:335`, `:370`); `LedgerResume.decide` always returns observe-only with 0 allowed new irreversible dispatches (`IntentLedger.swift:284`–`:293`); anchor rollback/stale-writer rejection and single-writer serialization (`IntentLedgerTests.swift:101`–`:142`); consumed slot with empty/moved ledger cannot reset the entitlement (`GoalSlotTests.swift:172`–`:197`); reservation refuses a second Save All or a second destination confirmation (`PersistentTransactionOwnerTests.swift:140`–`:175`, `:177`–`:236`).

## Reviewer statement

This review was performed read-only. No build/test/binary was executed, no LINE process was touched, no OS event was posted, no git write command was run, and no file other than this report was created. Phase B remained `FORBIDDEN_AB_EVALUATION` throughout; MAJOR A and INFO E identify forgery-resistance gaps in the eligibility gate, not an armed dispatch path in this round.

## verdict: ISSUES_FOUND

- MAJOR: 2 (A: eligibility self-declared evidence bindings / uncontained paths; B: post-hover revalidation omits candidate/geometry/topmost surface before `mouseDown`)
- MINOR: 2 (C: consume-before-append crash window; D: staging-root-keyed slot identity / approved-root trust boundary)
- INFO: 2 (E: live-execute ordering + residual CLI flag naming; F: tripwire gate sampling points / G21 coverage)
