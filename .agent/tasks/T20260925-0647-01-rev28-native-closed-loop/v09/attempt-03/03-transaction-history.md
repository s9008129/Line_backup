bindings_verified: PASS (all)

# V-09 attempt-03 independent review — 03-transaction-history (C4 transaction & history integrity)

- task: `T20260925-0647-01-rev28-native-closed-loop`; branch `v43-ab/codex-rev28`; worktree `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- bound product tree: `a758317b725370b008fe58c848e0d28463e86709`; observed HEAD: `16017b5e7068c9b9f6699dc784971ac41f228291` (later commits touch `.agent/` only)
- bound implementation digest: `e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf` (48 files = 36 Rev28Core swift + 9 rev28ctl swift + `rev28/Package.swift` + 2 `rev28/Tools` files)
- reviewer context: `03-transaction-history`, fresh and independent for attempt-03; the attempt-01/02 reports were read only as prior context, never as proof
- date: 2026-09-29 (Asia/Taipei); Phase B status: `FORBIDDEN_AB_EVALUATION`
- read-only statement: no build, no test execution, no product binary, no `rev28ctl`, no LINE.app interaction, no OS events, no git write. Only `rg`/`sed`/`awk`/`shasum`/read-only git (`show`/`log`/`diff`/`rev-parse`/`hash-object`) and read-only python hashing were used. Exactly one file was written: this report. `bindings.json` was not modified. Producer evidence logs' commands were not run.

## Bindings verification (recomputed this session)

| Item | Bound (bindings.json) | Observed | Result |
| --- | --- | --- | --- |
| rev28 tree vs bound head | `git diff --stat a758317 -- rev28` empty | empty (0 paths) | PASS |
| non-.agent commits since bound head | `git diff --name-only a758317 HEAD` only `.agent/` | 24 paths, all `.agent/` (0 non-agent) | PASS |
| `plan.md` SHA-256 | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | `05413807…f84c1b` | PASS |
| `handoff.md` SHA-256 | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | `67fc16a6…c227a33` | PASS |
| implementation digest (48 manifest paths) | `e748568d…c0cf` | `e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf`; split 36+9+1+2=48 | PASS |
| `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` | `c411011b1b44b1efb614e000f526b2118f45d120` | `c411011b…45d120` | PASS |
| a45 production digest record | `ZZDIGEST_SHA256=e748568d…c0cf`, `ZZDIGEST_PATHCOUNT=48` | present in `a45`; path lines match the manifest | PASS |
| manifest algorithm conformance | sha256 over sorted (path + NUL + bytes + NUL) for swift under the two source roots + Package.swift + every Tools file | my independent python recomputation matches exactly; `ReviewedImplementationDigest.manifestPaths` (`ReviewedImplementationDigest.swift:44–93`) implements the same rule | PASS |

Frozen rule artifacts (all 9 re-hashed by me; every value equals `frozen_rule_artifacts`):

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| `…/frozen/capture-geometry-rulebook-v1.json` | `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed` | PASS |
| `…/frozen/chooser-affirmation-predicate-v2.json` | `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` | PASS |
| `…/frozen/chooser-ax-calibration-v2.json` | `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569` | PASS |
| `…/frozen/capture-matrix-v1.json` | `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b` | PASS |
| `…/frozen/tripwire-attribution-ladder-v1.json` | `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` | PASS |
| `…/frozen/restart-observe-only-fixture-v1.json` | `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` | PASS |
| `…/frozen/postcondition-bounds-v3.json` | `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84` | PASS |
| `…/frozen/postcondition-latency-observations-v3.json` | `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155` | PASS |
| `…/ci-w2-item5-freeze-provenance-v3.json` | `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152` | PASS |

Repaired-tree evidence (all hashes and quoted summary lines re-derived from the files):

| Evidence | SHA-256 | Content observed | Result |
| --- | --- | --- | --- |
| `a37-build-attempt02-final…074109.log` | `2d6ff8835618ee49f928ff358ed8280425ae811b007103eb28630fae83e2e381` | `Build complete!`, `EXIT_PROD=0`, second `Build complete!`, `EXIT_TESTS=0` | PASS |
| `a38-focused-attempt02-final…074114.log` | `033e9be945fd6dad512e992e922c2e6891b5860a48e7526bd4fdcf5a3600f652` | `Executed 96 tests, with 0 failures (0 unexpected)`; 8 test suites started (96 = sum of per-suite executed counts) — see MINOR-1 | PASS (96/0) |
| `a39-full-suite-attempt02-final…074124.log` | `3113cad17b3207f7a87b2ea4ecf8d66d2a5a739c0ab2f7eb5951e8cc88a0933f` | `Executed 241 tests, with 0 failures (0 unexpected)`; no skipped-test lines (only the test name `…IsNamedNotSkipped`); 25 suites incl. `GoalSlotTests`, `LiveExecutionEngineTests`, `IntentLedgerTests`, `TripwirePostDispatchGateTests`, `ChooserPredicateProductionDerivationTests`, `AXWindowIdentitySelectorTests` | PASS |
| `a40-adversarial…run1…074153.log` | `de1d8f49e9ddb9aca2fae220f7aba43749830015fa1a774112bd445834427d28` | `Executed 27 tests, with 0 failures` | PASS |
| `a41-adversarial…run2…074153.log` | `09286e2d86bc288cf9cb770ccf4895b7d3512262c10c622cc7be95981955febc` | `Executed 27 tests, with 0 failures` | PASS |
| `a42-replay…run1…074157.json` | `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261` | `verdict=PASS`, `fixture_count=20`, `expected_fixture_count=20`, `failures=[]`, schema `rev28-historical-replay-v2`; `.stdout` empty (`e3b0c442…`) | PASS |
| `a43-replay…run2…074157.json` | `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261` | byte-identical to a42, same fields; `.stdout` empty | PASS |
| `a44-provenance…074210.log` | `3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a` | `status=PASS`, `generation=v3`, `implementationSourceGitBlobSHA=c411011b…45d120`, `sampleCount=20`, `maxLatencyMs=155.18903732299805`, `harnessRunID=HARNESS-20260925-105114` | PASS |
| `a45-digest…074221.log` | `d4188b0a0879c8c57c86765a52456414a3ebe7b582e7e3e7183b4ef5c95f86dd` | `ZZDIGEST_PATHCOUNT=48`, `ZZDIGEST_PATH=` lines = the 48 manifest paths, `ZZDIGEST_SHA256=e748568d…c0cf` | PASS |
| `cli-refusal-20260929T0742/cli-refusal-transcript-20260929T0742.log` | `20567f37179592b339cdc3320ff220f97f0c0edc89ae06b4ae0a06ce3e3a0a56` | `live-execute 77 / live-preflight 77 / CI guard 77 / missing config 64 / stale digest 77`; `evidence files: 0`, `staging files: 0`, `ledger present: no`, `anchor present: no`, `one-shot renamed: no` | PASS |

CLI-refusal fixture details (hashes computed by me): `config.json` `650948a4…f7e45e` carries `reviewedImplementationSHA256=e748568d…c0cf`; `config-stale-digest.json` `4e7a5ede…eeeda7` differs from `config.json` only at line 19 (`reviewedImplementationSHA256=e80e4f0f…a254e9`); `one-shot-authorization.json` `64c651be…9a2e03` binds `planSHA256=05413807…f84c1b` and the same implementation digest; fixture `chooser-predicate.json` `0472aa0a…ef7e569` and `chooser-calibration.json` `13aa01a2…f7e569` equal the frozen artifact bytes; `evidence/` and `staging/` exist but are empty (0 files each). The stale-config run refuses with `one-shot authorization or plan digest mismatch` before any entitlement touch.

## Scope / inputs / checks

- Scope (C4 transaction/history integrity): goal slot and entitlement; ledger/reservation gates and durable budget derivation; Phase B eligibility artifact canonical bindings (handoff/frozen/predicate bindings, evidence-root containment, ReviewedBuildState HEAD/diff/binary recomputation); digest manifest change; resume/continuation; chooser predicate-v2 derivation; trust-boundary dispositions (03-MINOR-C consume-before-append crash window; 03-MINOR-D goal-slot key includes staging root).
- Inputs: `bindings.json`, `plan.md`, `handoff.md`, `progress.md`; product tree at `a758317` (`rev28/Sources/Rev28Core/Transaction/*`, `Policy/ExecutionPolicy.swift`, `Chooser/ChooserAffirmationPredicate.swift`, `Composition/PostSaveComposition.swift`, `rev28ctl/main.swift`); tests read only (`GoalSlotTests`, `ChooserPredicateProductionDerivationTests`); evidence `a37`–`a45`, `cli-refusal-20260929T0742/`; attempt-01/02 reports only as context.
- Checks: independent recomputation of every bound hash; independent digest recomputation with python (not the product binary); read-only source inspection at the bound tree; no execution of producer commands.
- Limitation: I did not execute the production `ReviewedImplementationDigest.compute` (running the product binary is forbidden); conformance is established by (a) my independent recomputation matching the bound value and (b) code inspection showing `manifestPaths`/`compute` implement exactly the bound algorithm. Similarly the test logs were read, not re-run; this review establishes code correctness and evidence/hash correspondence, not fresh test execution.

## Per-claim verdicts

| Claim | Verdict | Evidence / citation |
| --- | --- | --- |
| `V09_A2_MAJOR_A_CANONICAL_ELIGIBILITY_BINDINGS` (owner/eligibility half) | VERIFIED | `CanonicalEvidenceBinding` `PhaseBEligibility.swift:86`; recomputation context `:120–152`; 18 required predicates `:160–182`; structural validate `:243–293`; recomputed validate (canonical handoff/frozen/predicate comparisons, exact name-set + predicate-set equality, allowed-root containment, plan/handoff/frozen/predicate re-hash, implementation digest compare, reviewed HEAD/diff/binary compare) `:300–398`; path containment `:413–426`; artifact must live under the run evidence dir `:401–409`; `ReviewedBuildState.observe` (git HEAD, ancestor check, reviewed-paths diff SHA-256, executable SHA-256) `ReviewedBuildState.swift:67–151`; CLI requires the canonical bindings + reviewed triple whenever `phaseBEligibilityPath` is set `main.swift:208–256` and validates before owner `:258–265`; owner re-validates with the slot state `PersistentTransactionOwner.swift:390`; composition re-validates immediately before the dispatch `PostSaveComposition.swift:196–201` |
| `V09_A2_MAJOR_3_BUDGET_ENFORCEMENT` (budget half) | VERIFIED | Static ceilings + `isExhausted` `ExecutionPolicy.swift:49–92`; durable per-blocker/consecutive counts derived from the ledger only `PersistentTransactionOwner.swift:296–324`; `recordReversibleDispatch` refuses at ceiling/abort threshold `:332–356`; `recordCandidateRevalidation` durably appends the failing outcome then throws `:357–374`; `reserveSaveAll` refuses exhausted **before** consuming the entitlement `:419–425` (`phaseBBudgetExhausted` `:118`/`:139`); 18th predicate `REVERSIBLE_AND_REVALIDATION_BUDGETS_NOT_EXHAUSTED` `PhaseBEligibility.swift:181` |
| `DIGEST_MANIFEST` | VERIFIED | `sourceRoots`/`configurationPaths`/`toolRoots`/`reviewedPaths` `ReviewedImplementationDigest.swift:24–42`; `manifestPaths` enumerates swift under both source roots, `rev28/Package.swift`, every regular file under `rev28/Tools` `:44–81`; `/private/var`-safe relative path from the root marker `:87–92`; `reviewedPaths` reused by the git diff check `ReviewedBuildState.swift:104–124`; independent recomputation = `e748568d…c0cf` (48 paths) |
| `V09_C4_BUDGET_NOT_DURABLE` (attempt-01 claim, in force) | VERIFIED | `liveDispatchBudget` is only a derived view of the verified ledger `PersistentTransactionOwner.swift:296–324`; per-identical-blocker ≤3 and 2-consecutive-failure abort enforced at the durable write paths `:332–374`; ceilings fixed, action grouping default key `:340–343` |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` (attempt-01 claim, in force) | VERIFIED | `mayEnterIrreversibleBoundary` `PersistentTransactionOwner.swift:237–238`; `preIntentContinuationAllowed` `:249–258`; `reserveSaveAll` requires `.saveAllLocated` + bound `eligibility.phaseB` + unexhausted budget, then consumes the slot and maps `entitlementAlreadyConsumed` → `irreversibleIntentAlreadyRecorded` `:403–433`; `reserveDestinationConfirmation` requires `.destinationPrepared` + `saveAll>=2` + one-shot chooser record + zero prior confirmation `:514–529` |
| `V09_ELIGIBILITY_LABEL_ONLY` (attempt-01 claim; attempt-02 verdict was PARTIAL due to self-declared bindings) | VERIFIED | All attempt-02 MAJOR-A gaps are closed on this tree: canonical reviewed values from config, exact frozen name-set and predicate-set equality, containment of declared and canonical paths, live reviewed HEAD/diff/binary recomputation and comparison, artifact must declare `PhaseBEligibilityReviewedBuild` and live under the run evidence root (citations as in the MAJOR_A row). No self-declared binding can arm the entitlement |
| `V09_GOALSLOT_NON_ATOMIC_WRITE` (attempt-01 claim, in force) | VERIFIED | `write` uses fsynced temp + `rename(2)` + parent-dir fsync `GoalSlot.swift:178–216`; key = NUL-joined goal/group/album/stagingRoot `:68–72`; `consumeOneShotEntitlement` one-way `:116–143`; concurrent-reader atomicity test `GoalSlotTests.swift:54–78` (read, not run) |
| `V09_ONESHOT_MARKER_INERT` (attempt-01 claim, in force) | VERIFIED | `OneShotAuthorization.swift` absent (`git ls-files rev28 | grep -i oneshot` empty; no source reference; deleted in `79004cf`); `live-preflight` observe-only refusal is goal-slot based `main.swift:141–150`; consumption only via `reserveSaveAll`; residual flag/file naming only — see INFO-3 |
| `V09_ENGINE_RESUME_CONTINUATION_NARROW` (attempt-01 claim, in force) | VERIFIED | `run()` observe-only unless `preIntentContinuationAllowed` `LiveExecutionEngine.swift:136–155`; continuation re-establishes remaining pre-save states from fresh live evidence, never reusing prior evidence `:229–258`; `runPreflight` refuses any ledger with irreversible records `LiveExecutionEngine.swift:264–267`; owner gate `PersistentTransactionOwner.swift:249–258` |
| `V09_CHOOSER_PREDICATE_V2_NOT_DERIVED` (attempt-01 claim, in force) | VERIFIED (code-level; test read, not executed) | Frozen predicate + calibration bytes re-read and hash-checked against the config bindings, then derived via `ChooserProductionPredicate.derive` with a process-stable version guard `main.swift:164–190`; derivation `ChooserAffirmationPredicate.swift:179–228`; production evaluator requires version 2 `:307`/`:320–329`; test `ChooserPredicateProductionDerivationTests.swift:80–108` |

No PARTIAL/NOT VERIFIED verdicts; no failing plan.md line to cite.

## Trust-boundary dispositions (reasoning checks; no code change expected)

- `03-MINOR-C` (consume-before-append crash window) — **DISPOSITION SUPPORTED**. In-process retry: `reserveSaveAll` consumes the slot before appending intent; a second reservation maps `GoalSlotError.entitlementAlreadyConsumed` → `irreversibleIntentAlreadyRecorded("saveAll")` (`PersistentTransactionOwner.swift:418–430`). Restart with empty ledger: owner init refuses consumed slot + empty ledger (`:184–190`). Restart with ledger but no irreversible record: `dispatchSaveAll` re-reads the slot and calls `validateWithRecomputedEvidence(entitlementConsumed: slot?.entitlementConsumed ?? false)` (`PostSaveComposition.swift:196–201`), which refuses `PhaseBEligibilityError.entitlementConsumed` (`PhaseBEligibility.swift:261`). All observed recovery paths fail closed; the residual slot-vs-ledger forensic ambiguity is a documentation note only, as recorded.
- `03-MINOR-D` (goal-slot key includes staging root) — **DISPOSITION SUPPORTED**. `plan.md:134` keys the slot to "this task/group/album/approved new-path authorization"; the key is exactly goal/group/album/stagingRoot (`GoalSlot.swift:68–72`) and the staging root/approved root are part of the reviewed authorization/config, so an approved new path legitimately forms a new identity. The in-product distinction between "re-approved new root" and "operator replacement" remains absent, exactly as documented; no code change is required for the current review scope.

## Findings

### MAJOR
- None.

### MINOR
- MINOR-1 — `focused_11_suites`: the repaired-tree evidence descriptor states 11 suites, but the bound a38 log contains exactly 8 test suites. `bindings.json` names the key `focused_11_suites`, and `progress.md:165` / `progress.md:289` describe a38 as "focused 11 suites 96/0". The a38 log (`a38-focused-attempt02-final-20260929T074114.log`, SHA-256 `033e9be9…0f652`) contains suite-start lines for exactly 8 classes (ActuationReadiness=10, AdversarialMatrix=27, ComposedAdapters=14, ExecutionPolicy=7, PersistentTransactionOwner=7, PhaseBEligibility=21, PostconditionMonitor=7, ReviewedBuildState=3; sum = 96) and the aggregate `Executed 96 tests, with 0 failures`. The earlier repair round (`a27`/`a30`) genuinely had 11 suites at 80/0, so the "11 suites" phrase appears carried over. The required bound summary line ("focused 96/0") verifies exactly, and the a39 full suite (25 suites, 241/0/0 skipped) independently covers the classes absent from the focused run; the label therefore misdescribes observed evidence without affecting any gating claim. Contract: AGENTS.md §1 prime directive ("never claim a test, verification, deployment, or outcome that was not actually observed") and `handoff.md:183` ("Update only from observed evidence"). Recommended correction on a future record update: "focused 8 suites 96/0".

### INFO
- INFO-1 — `03-MINOR-C` disposition is sound and fail-closed; the only residual is the documented forensic need to compare slot vs ledger for the consume→append window. No code change required (details above).
- INFO-2 — A pre-intent continuation cannot re-record Phase B eligibility: `recordPhaseBEligibility` refuses a second bound `eligibility.phaseB` (`PersistentTransactionOwner.swift:384–386`), and `dispatchSaveAll` records it on every attempt (`PostSaveComposition.swift:205`). A restart that otherwise satisfies `preIntentContinuationAllowed` but whose crashed predecessor recorded eligibility before failing pre-reserve can re-observe but cannot re-arm the dispatch. This is fail-closed (no dispatch-safety gap) but is narrower than `plan.md:142`'s continuation allowance ("allowed only after … zero irreversible records"); worth an explicit disposition if Phase B ever arms.
- INFO-3 — Residual `--one-shot-authorization` naming. The CLI still requires the flag (`main.swift:58–63`) and decodes runID/planSHA256/reviewedImplementationSHA256 from it (`:110–121`), but the durable authority is the goal slot, not the file (`:141–150`). This re-confirms attempt-02 INFO E; naming only, no correctness impact.

verdict: ISSUES_FOUND
