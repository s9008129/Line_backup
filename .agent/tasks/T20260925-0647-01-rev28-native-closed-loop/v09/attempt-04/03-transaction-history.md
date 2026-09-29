bindings_verified: PASS (all)

# V-09 attempt-04 independent review — 03-transaction-history (C4 transaction authority, ledger/budget durability, history integrity, record accuracy)

- task: `T20260925-0647-01-rev28-native-closed-loop`; branch `v43-ab/codex-rev28`; worktree `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- bound product tree: `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`; observed HEAD `5ed71064a9f93d4abc27eecc857e3584a1b2a2ae` (3 commits above the product tree — `3d74248b`, `c945f04`, `5ed71064` — each touching only `.agent/` paths)
- bound implementation digest: `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686` (48 manifest paths = 36 `Rev28Core` swift + 9 `rev28ctl` swift + `rev28/Package.swift` + 2 files under `rev28/Tools`)
- reviewer context: `03-transaction-history`, fresh for attempt-04. The attempt-01/02/03 reports were read only to recover claim IDs/disposition titles; nothing in them is reused as proof, and no attempt-01/02/03 verification is cited as evidence below — every verdict is re-derived from the bytes bound at `cf39fdcc`.
- date: 2026-09-29 (Asia/Taipei); Phase B status: `FORBIDDEN_AB_EVALUATION`
- read-only statement: no build, no test execution, no product binary, no `rev28ctl`, no LINE.app interaction, no OS events, no git write. Only `cat`/`sed`/`awk`/`grep`/`find`/`shasum`/read-only `python3` hashing and read-only git (`rev-parse`, `status`, `diff`, `log`, `show`, `ls-files`, `merge-base`, `hash-object`) were used. Exactly one file was written: this report. `bindings.json` and every other reviewed artifact were not modified.

## Bindings verification (independently recomputed this session)

| Item | Bound (attempt-04 `bindings.json`) | Recomputed here | Result |
| --- | --- | --- | --- |
| Product-tree commit | `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1` | `cf39fdcc63e2b9c0d94ff8f34fd34b7aaaf58ff1`; `cf39fdcc` is an ancestor of HEAD | PASS |
| `git diff --stat cf39fdcc -- rev28` | empty | empty (rev28 worktree == product tree) | PASS |
| `git diff --name-only cf39fdcc HEAD` | only `.agent/` paths | 21 paths, every one under `.agent/`; `git log --name-only cf39fdcc..HEAD` = 3 commits, all `.agent`-only | PASS |
| Worktree cleanliness for `rev28` | clean | `git status --porcelain -- rev28` empty; whole-worktree porcelain empty at observation time | PASS |
| `plan.md` SHA-256 | `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b` | `05413807…f84c1b`; identical to `plan.sha256` file | PASS |
| `handoff.md` SHA-256 | `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33` | `67fc16a6…c227a33`; identical to `handoff.sha256` file | PASS |
| `git hash-object rev28/Sources/rev28ctl/HarnessCalibration.swift` | `c411011b1b44b1efb614e000f526b2118f45d120` (v3-frozen blob) | `c411011b…45d120`; the same blob SHA appears in `harness/ci-w2-item5-freeze-provenance-v3.json`; the file is absent from `git diff a758317 cf39fdcc -- rev28` | PASS |
| Implementation digest | `6734dda5…a686`, 48 files, manifest "45 swift (36+9) + Package.swift + 2 Tools" | own Python replica of "sha256 over sorted (repo-relative path + NUL + bytes + NUL)" = `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686`, 48 paths (36+9+1+2); `ReviewedImplementationDigest.manifestPaths` (`ReviewedImplementationDigest.swift:44–83`) implements exactly that rule | PASS |
| Production digest record `a49` | `ZZDIGEST_SHA256=6734dda5…a686`, `ZZDIGEST_PATHCOUNT=48` | both present; the 48 `ZZDIGEST_PATH=` lines are identical, element-for-element and order-for-order, to my independently derived manifest list | PASS |
| Superseded digest record | attempt-03 bound to `e748568dbc…c0cf` | `v09/attempt-03/bindings.json` declares `e748568dbc7c23a642eeead559afc0df345c56e91ff694dc1b6012744615c0cf`; attempt-03 report/log files `a37–a45` and `cli-refusal-20260929T0742/` exist | PASS |

Frozen rule artifacts (all 9 files re-hashed; every value equals the `frozen_rule_artifacts` map):

| Artifact | Recomputed SHA-256 | Result |
| --- | --- | --- |
| `…/frozen/capture-geometry-rulebook-v1.json` | `09e1cf2ae181f519f9ed47979e0286212f0b051f197ced6909a9789f2f1a62ed` | PASS |
| `…/frozen/chooser-affirmation-predicate-v2.json` | `0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2` | PASS |
| `…/frozen/chooser-ax-calibration-v2.json` | `13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569` | PASS |
| `…/frozen/capture-matrix-v1.json` | `e008478201770f0496d6a252680ae2a737473c32a70db888ebd2bf4aafb7ba7b` | PASS |
| `…/frozen/tripwire-attribution-ladder-v1.json` | `d67abb17afbb77dc03fb3d70efc32d63ae4d3e616f7f259f6d803c8e88ef3216` | PASS |
| `…/frozen/restart-observe-only-fixture-v1.json` | `146b373a93c7a1ab02041e079c95eed645a7dd46d45ef518bc4a49bc8128a93f` | PASS |
| `…/frozen/postcondition-bounds-v3.json` | `c10dcb43e9da14feedaed4f9e1ef5fdbf9b6afdd96d6ee8e79b84ac45a055e84` | PASS |
| `…/frozen/postcondition-latency-observations-v3.json` | `ca4beabefc1f671162cec06345cf06755a62ad77a28458ac1b03a563f640b155` | PASS |
| `…/harness/ci-w2-item5-freeze-provenance-v3.json` | `4f6f5fdcea491503b51e279b688de123ae4e38883b9d54edd02ad794baa0b152` | PASS |

Repaired-tree evidence `a46–a54` and `cli-refusal-20260929T0807/` (hashes and quoted summary lines re-derived from the bytes):

| Evidence | Recomputed SHA-256 | Quoted summary lines observed | Result |
| --- | --- | --- | --- |
| `a46-build-attempt03-repair-20260929T080503.log` | `4e516ea0da01668a0ef131cfa7c286e8824be3d0b222c577fb60694f779002b9` | `Build complete! (0.11s)` | PASS |
| `a47-focused-m1-repair-20260929T0805.log` | `ef1f097427afc6bcb8e1c65f8b77c9f7eace627b3d61bc5a86300752027240ef` | 6 class suites (ActuationReadiness, AdversarialMatrix, ComposedAdapters, CoordinateTransform, LiveExecutionEngine, StructuralLocators); aggregate `Executed 88 tests, with 0 failures (0 unexpected)`; new regression `testDispatchMarginConvertsOnePointAtCaptureScaleNotOnePixel` started/passed (lines 669–670); zero `failed` lines | PASS (88/0) |
| `a48-full-suite-m1-repair-20260929T0806.log` | `7ac047be636f49086e30a27ca3e6ad85ffa51b89b5878f060becc09ea99a56a8` | aggregate `Executed 242 tests, with 0 failures (0 unexpected)` (lines 566/568); zero `failed` lines; no skipped-test lines anywhere (the only `skip` substring is the test name `…IsNamedNotSkipped` at lines 346–347), so "0 skipped" is consistent with the log | PASS (242/0, 0 skipped) |
| `a49-digest-m1-repair-20260929T0806.log` | `e3e62a2bd5459064e233eb711859a8e9c2bd21376097dd799b072c0104ebd3a3` | `ZZDIGEST_PATHCOUNT=48`, `ZZDIGEST_SHA256=6734dda5…a686`, 48 path lines identical to my manifest | PASS |
| `a50-adversarial-m1-repair-run1-20260929T0808.log` | `fc081145267ac41c9212c74675d89b3d34ad091e3f4c7c97160912f356788e00` | `Executed 27 tests, with 0 failures (0 unexpected)`; 27 `Test Case … passed`; zero `failed` lines | PASS (27/0) |
| `a51-adversarial-m1-repair-run2-20260929T0808.log` | `4c1a1722254623ab3349af16cc0c303a37720dc901d61e4f5eecaf8128e31574` | `Executed 27 tests, with 0 failures (0 unexpected)`; 27 passed | PASS (27/0) |
| `a52-replay-m1-repair-run1-20260929T0808.json` | `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261` | `verdict=PASS`, `fixture_count=20`, `expected_fixture_count=20`, `failures=[]`, schema `rev28-historical-replay-v2`; equals the bound `replay_output_sha256` | PASS |
| `a53-replay-m1-repair-run2-20260929T0808.json` | `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261` | byte-identical to `a52`, same fields | PASS |
| `a54-provenance-m1-repair-20260929T0808.log` | `3bf448fa3ed389581b852d95d3c950f3e1bb4ad1c6dd23bd483ca7ea0bbaeb1a` | `status=PASS`, `generation=v3`, `sampleCount=20`, `maxLatencyMs=155.18903732299805`, `implementationSourceGitBlobSHA=c411011b…45d120`, `harnessRunID=HARNESS-20260925-105114` | PASS |
| `cli-refusal-20260929T0807/cli-refusal-transcript-20260929T0807.log` | `184c72b469e7602277bed47b5766a8be50e425c8122206f43b3300fca7e259ab` | `live-execute EXIT=77 / live-preflight EXIT=77 / CI guard EXIT=77 / missing --config EXIT=64 / stale digest EXIT=77`; side effects `evidence files: 0`, `staging files: 0`, `ledger present: no`, `anchor present: no`, `one-shot renamed: no`; the fixture `evidence/` and `staging/` directories exist and contain 0 files | PASS |
| `cli-refusal-20260929T0807/config.json` | `94f172093e2d1aeb5e6655cc5b9a1bb28d365939afe6d1d5e35eb0e448d7d38c` | carries `reviewedImplementationSHA256=6734dda5…a686` (line 19); `targetPID=1`, bundle `jp.naver.line.mac` (refusal happens at the process-identity guard before any LINE interaction) | PASS |
| `cli-refusal-20260929T0807/config-stale-digest.json` | `80dda02733a61958583318eb6c57a62e3bf8b1ddf07d0bcb66806e093c946435` | differs from `config.json` only at line 19 (`reviewedImplementationSHA256=e80e4f0f…a254e9`) — verified by `diff` | PASS |
| `cli-refusal-20260929T0807/one-shot-authorization.json` | `f28ce3eb27e38f0ee391c9eba264e52f9d8e0188db77aee5371c06e85c7dab2f` | binds `planSHA256=05413807…f84c1b` and implementation digest `6734dda5…a686`; file present and un-renamed | PASS |
| `cli-refusal-20260929T0807/rulebook.json` | `00759abb1a71270b62eedec6ac24c7aa4456ab01df697e6c510809a62713fc8e` | present | PASS |
| fixture `chooser-predicate.json` / `chooser-calibration.json` | `0472aa0a…f3f2` / `13aa01a2…e569` | equal to the frozen artifact bytes | PASS |

Record-accuracy evidence:

| Evidence | Recomputed SHA-256 | Content observed | Result |
| --- | --- | --- | --- |
| `a38-focused-attempt02-final-20260929T074114.log` | `033e9be945fd6dad512e992e922c2e6891b5860a48e7526bd4fdcf5a3600f652` | exactly 8 class suite-start blocks (lines 7/30/87/118/135/152/197/214); per-suite executed counts 10+27+14+7+7+21+7+3 = 96, each `0 failures`; aggregate `Executed 96 tests, with 0 failures (0 unexpected)` (lines 224/226); zero `failed` lines | PASS (96/0, 8 suites) |
| `v09/attempt-03/bindings.json` | `737bdebb5aba7a40c05ccfc78c4e06b4e4deb1b5a7ed328d7d7a4f23619abeab` | equals the hash recorded at `progress.md:312`; `git diff 16017b5 HEAD -- …/attempt-03/bindings.json` is empty (bytes untouched since the binding commit); the key `focused_11_suites` is still present at line 45 (immutable by design) | PASS |
| `progress.md` / `execution.md` corrected records | n/a | both say "focused 8 suites 96/0" (`progress.md:22,175,307,322,329`; `execution.md:82,123`); the only remaining "11 suites" strings describe the earlier a27/a30 round (`progress.md:35,275`, `execution.md:63`) | PASS |

## Attempt-04 delta confinement (M-1 repair vs transaction semantics)

`git diff --stat a758317 cf39fdcc -- rev28` is exactly three files: `Rev28Core/Actuation/QuartzActuator.swift` (7 lines), `Rev28Core/Geometry/Coordinates.swift` (27 lines), `Tests/Rev28CoreTests/ActuationReadinessTests.swift` (51 lines). Exact changed hunks:

1. `QuartzActuator.swift:327-333` (inside `DispatchReadinessGate.mintPermit`) — the two raw boundary comparisons `point.x > minX + 1 && point.x < maxX - 1` / same for `y` are replaced by `CaptureGeometryRules.isDispatchableCapturePixels(point:safeRect:captureScale: observation.captureGeometry.scale)`, plus an explanatory comment. The enclosing `guard` (`:330-348`) still throws the same `dispatchRefusedByPrecondition("unsafe candidate geometry")` (`:347`); its other conjuncts (scale finite/positive `:335`, bbox/image bounds, frame-delta checks `:343-346`) are unchanged. No `±1` comparison remains anywhere in the file (`grep '+ 1' / '- 1'` returns nothing).
2. `Coordinates.swift:323-325` — new single constant `dispatchMinimumMarginPt: Double = 1.0`; `:331` — `isDispatchable`'s default parameter changes from the literal `1.0` to that constant (same value, so no behavior change for every caller, including the explicitly-passing frozen `HarnessCalibration.swift:1321,1341,1537-1538`); `:345-364` — new pure function `isDispatchableCapturePixels` requiring `margins.min() >= dispatchMinimumMarginPt * captureScale` (`:363`) and refusing non-finite/non-positive scales (`:353-354`).
3. `ActuationReadinessTests.swift:89-138` — new regression (test target, outside the 48-path manifest).

Confinement argument (re-derived, not inherited):

- `isDispatchableCapturePixels` is pure (no IO, no state) and its only production call site is the readiness guard at `QuartzActuator.swift:332-333`; the only other call sites are the new test assertions (`ActuationReadinessTests.swift:129-136`). Verified by grep across `rev28/Sources` and `rev28/Tests`.
- The guard's failure path is a pre-dispatch refusal. In `PostSaveComposition.dispatchSaveAll`, the permit is minted at `:241` *before* `markDispatchBoundary()` (`:274`), `journalBox.recordDispatchBoundary` (`:278`) and `postSave.dispatchSaveAllClick` (`:279`); the owner-side reservation/accounting (`owner.reserveSaveAll()`, `owner.markSaveAllAttempted()`) runs inside the gated actuator only after the live guards, at `QuartzActuator.swift:520-526`, and the first event (`sink(move)`) follows at `:527`. A mint failure therefore cannot consume the one-shot entitlement, append `intent.saveAll`/`attempt.saveAll`, or post any event.
- Same for the reversible path: `ComposedNativeAdapter.swift:305` mints before `environment.postReversibleClick` (`:322-328`), and `recordReversibleDispatch` (`QuartzActuator.swift:522`) is only reachable inside `postClick` after `permit.consume` (`:483`) and `liveGuards()` (`:514`). A mint refusal consumes no reversible budget and records nothing.
- Direction of the semantic change: at scale 1 the new predicate is point-for-point identical to the frozen `isDispatchable` (`>=` at exactly 1 pt, strict interior at `Coordinates.swift:340/361`); at scale > 1 it is strictly more conservative than the pre-repair gate (it refuses margins below 1 pt that the old raw-1-px check admitted); at scale < 1 it admits exactly what the frozen point-space rule admits and no more. Either way the changed code only selects between "mint" and the existing fail-closed refusal and cannot reach owner/ledger/eligibility/dispatch-accounting code.
- `revalidateAfterHover` deliberately has no second margin check; that reasoning is sound on this tree: the permit's `capturePoint`/`safeRectCapturePx`/`windowFrame` fields are `fileprivate let` (`QuartzActuator.swift:260-290`) set once at mint, and `consume` mutates only `consumed` (`:292-303`), so the margin facts cannot drift between mint and click; the post-hover path still re-checks window identity/geometry/frame deltas and the live guards (`:374-420`, `:500-513`).
- Production candidates still satisfy the guard at real capture scales: Save All uses the safe-rect midpoint (`StructuralLocators.swift:291`, margins = half of the row cell), and the ellipsis candidate uses the triple's middle-dot centre with a >= 4 px inset safe rect (`AlbumEllipsisLocator.swift:242-258`), which satisfies the required `1.0 pt x scale` margin for the reviewed 1x/2x scales (cross-checked here; the full production-candidate analysis belongs to the 01-perception-geometry context).

## Per-claim verdicts (re-derived on `cf39fdcc`, digest `6734dda5…a686`)

| Claim | Verdict | Evidence on this tree |
| --- | --- | --- |
| `V09_A3_M1_RETINA_MARGIN_SCALE` | VERIFIED | `Coordinates.swift:323-325` single constant; `:331` default shares it; `:345-364` scale-converted `>=` with fail-closed invalid scale (`:353-354`); `QuartzActuator.swift:330-348` guard now calls it (`:332-333`), raw ±1 px comparisons gone; invalid-scale double guard `:335`; production candidates `StructuralLocators.swift:291`, `AlbumEllipsisLocator.swift:242-258` |
| `V09_A3_M1_REGRESSION_TEST` | VERIFIED (code-level; not executed) | `ActuationReadinessTests.swift:89-138`: 2x 1 px refused `:112-114`, 2x 2 px accepted `:117-119`, 3x 2 px refused `:121-123`, 1x 1 px accepted `:125-127`, direct assertions incl. NaN `:129-137`; bound log `a47` shows this test started+passed (lines 669-670) |
| `V09_A3_M1_NO_BEHAVIOR_DRIFT` | VERIFIED | Semantics match `isDispatchable`: same `>=` and strict-interior rules (`Coordinates.swift:340/342` vs `:361/363`); existing fixtures use 50 px margins (`ActuationReadinessTests.swift:47-48`) and are unaffected; the permit-immutability argument for skipping a second margin check in `revalidateAfterHover` is sound (`QuartzActuator.swift:260-303`, `:374-420`); the only delta vs the pre-repair gate is the exact-boundary point now admitted in line with the frozen rule (see INFO-6) |
| `V09_A3_SUITE_COUNT_LABEL_DISPOSITION` | VERIFIED | `a38` SHA `033e9be9…0f652`; 8 class suites, 96/0 (see table above); corrected records "focused 8 suites 96/0" (`progress.md:22,175,307,322,329`, `execution.md:82,123`); attempt-03 `bindings.json` bytes `737bdebb…beab` unmodified since `16017b5` and still carrying `focused_11_suites` (line 45), matching the recorded hash at `progress.md:312` |
| `V09_C4_BUDGET_NOT_DURABLE` | VERIFIED | Ceilings `ExecutionPolicy.swift:54-56`; derived-view-only init `:66-80`; `isExhausted` `:88-92`; durable counts derived only from the verified ledger `PersistentTransactionOwner.swift:296-327`; enforcement at the write paths `:332-352` (refusals before append), `:357-368` (failing revalidation appended before the throw); `reserveSaveAll` refuses exhaustion before touching the entitlement `:423-425` |
| `V09_C4_OWNER_RESERVATION_ENFORCEMENT_MISSING` (reservation-time state/eligibility enforcement) | VERIFIED | Gate `PersistentTransactionOwner.swift:237-239`; `.saveAllLocated` required `:410-412`; bound durable `eligibility.phaseB` record required `:416-418`; unexhausted budget required `:423-425`; one-way consumption `:426-430`; intent append `:431`; destination reservation requires `.destinationPrepared` + saveAll>=2 + zero prior confirmations + bound chooser record `:514-529`; owner re-validation `:375-398` |
| `V09_A2_MAJOR_3_BUDGET_ENFORCEMENT` | VERIFIED | As above plus predicate `REVERSIBLE_AND_REVALIDATION_BUDGETS_NOT_EXHAUSTED` `PhaseBEligibility.swift:181` (plan.md:257); durable per-blocker/consecutive counts `PersistentTransactionOwner.swift:300-317`; composition re-validates before dispatch `PostSaveComposition.swift:196-205` |
| `V09_A2_MAJOR_A_CANONICAL_ELIGIBILITY_BINDINGS` | VERIFIED | Canonical values only from reviewed config: `main.swift:207-215` (required with any artifact), `:224-233` (canonical expectations + live `ReviewedBuildState.observe`), `:249-252` (allowed roots = repo root + run evidence dir), `:258-266` (artifact load within run dir + full recomputation); comparison/containment `PhaseBEligibility.swift:300-395` — canonical completeness `:308-316`, artifact-vs-canonical and observed-vs-canonical HEAD/diff/binary `:317-334`, path containment `:335-349`, plan bytes + implementation digest `:350-357`, handoff `:358-364`, frozen exact name-set + re-hash `:365-380`, predicate set + canonical binding + re-hash `:381-394`; artifact location `:399-405`; live git observations `ReviewedBuildState.swift:67-151` (diff computed over `ReviewedImplementationDigest.reviewedPaths`, `:104-121`) |
| `V09_ELIGIBILITY_LABEL_ONLY` | VERIFIED | Verdict must be `PASS` `PhaseBEligibility.swift:272-278`; evidence must be a well-formed path+hash `:279-281`; exact predicate set `:286-292`; every evidence byte re-read/re-hashed `:377,391,428-432`; plan/handoff/frozen re-hashed `:350-380`; implementation digest recomputed twice and compared `main.swift:117-124`, `PhaseBEligibility.swift:354-357`; owner-boundary re-validation `PersistentTransactionOwner.swift:388-398`. No self-declared value can arm the entitlement |
| `V09_GOALSLOT_NON_ATOMIC_WRITE` | VERIFIED | Key = NUL-joined goal/group/album/stagingRoot `GoalSlot.swift:68-72`; atomic install = fsynced temp + `rename(2)` + parent-dir fsync `:178-216`; one-way consume `:113-144`; single-writer lock `:218-229`; concurrent-reader atomicity test (read, not run) `GoalSlotTests.swift:54-78`; repeated-consume refusal test `:137-141` |
| `V09_ONESHOT_MARKER_INERT` | VERIFIED | `OneShotAuthorization.swift` absent (`git ls-files rev28` no match; no source reference); the only production entitlement consumption is `reserveSaveAll` → `GoalSlot.consumeOneShotEntitlement` (`PersistentTransactionOwner.swift:427`; grep shows no other production call site); `live-preflight` observe-only refusal is goal-slot based `main.swift:141-148`; residual `--one-shot-authorization` flag naming only (`main.swift:58-63,107-126`) — INFO-5 |
| `V09_ENGINE_RESUME_CONTINUATION_NARROW` | VERIFIED | `run()` observe-only unless continuation `LiveExecutionEngine.swift:136-153`; continuation re-establishes remaining states from fresh adapter evidence, never reusing old evidence `:229-258`; `runPreflight` refuses any ledger with irreversible records `:264-269`; owner gate `PersistentTransactionOwner.swift:237-258`; post-irreversible resume detection `:178-181` |
| `DIGEST_MANIFEST` | VERIFIED | `sourceRoots`/`configurationPaths`/`toolRoots`/`reviewedPaths` `ReviewedImplementationDigest.swift:24-40`; enumeration (swift under both roots, `rev28/Package.swift`, every regular file under `rev28/Tools`) `:44-83`; `/private/var`-safe relative path `:87-93`; material formula `:95-104`; my replica = `6734dda5…a686` (48 paths); `a49` path lines identical; `reviewedPaths` reused by the git diff check `ReviewedBuildState.swift:104-121` |

No PARTIAL or NOT VERIFIED verdicts in this context; no failing plan.md line.

## Trust-boundary dispositions (reasoning checks, no code change expected)

- `03-MINOR-C` (crash window between entitlement consumption and the durable `intent.saveAll` append) — **DISPOSITION SUPPORTED**. Consumption happens at `PersistentTransactionOwner.swift:427`, the append at `:431`; the failure matrix re-derived here is: (a) in-process retry — `GoalSlotError.entitlementAlreadyConsumed` is mapped to `irreversibleIntentAlreadyRecorded("saveAll")` (`:428-430`); (b) restart with consumed slot + empty ledger — the owner initializer refuses (`:187-190`); (c) restart with a ledger but no irreversible record — `dispatchSaveAll` re-reads the slot and calls `validateWithRecomputedEvidence(..., entitlementConsumed: slot?.entitlementConsumed ?? false, ...)` (`PostSaveComposition.swift:196-201`), which refuses with `PhaseBEligibilityError.entitlementConsumed` (`PhaseBEligibility.swift:260`). Every observed path fails closed; the residual slot-vs-ledger forensic ambiguity is a documentation note only (INFO-1).
- `03-MINOR-D` (goal-slot identity includes the staging root) — **DISPOSITION SUPPORTED**. `GoalSlot.fileURL` keys the slot to goal/group/album/stagingRoot (`GoalSlot.swift:68-72`), matching `plan.md:134` ("keyed to this task/group/album/approved new-path authorization"); `stagingRoot` is part of the reviewed `ImmutableRunAuthorization` (`PersistentTransactionOwner.swift:12`) and of the authorization fields bound into every ledger entry (`:56-72`, `:555-557`), so the approved root is itself part of the reviewed authorization config, and an approved new root legitimately forms a new goal identity. The absence of an in-product distinction between "re-approved new root" and "operator replacement" stands, exactly as documented (INFO-2).
- `01-MINOR-1` (locator menu/addressable bounds config-supplied but fail-closed) is listed in the attempt-04 bindings' dispositions but belongs to the 01-perception-geometry review context; not re-adjudicated here (noted for completeness only).

## Findings

### MAJOR
- None.

### MINOR
- None. (The attempt-03 MINOR-1 record-accuracy issue is dispositioned as corrected below; no new MINOR was found on the repaired tree.)

### INFO
- INFO-1 — `03-MINOR-C` residual: a crash between `GoalSlot.consumeOneShotEntitlement` and the `intent.saveAll` append leaves a consumed slot without a ledger intent; all re-derived recovery paths fail closed (see disposition above), and the only residual is the documented forensic need to compare slot vs ledger for that window. No code change required.
- INFO-2 — `03-MINOR-D` residual: the goal identity keyed by `stagingRoot` cannot distinguish "re-approved new root" from "operator replacement" in-product; documented as intended (the approved root is part of the reviewed authorization config). No code change required.
- INFO-3 — Pre-intent continuation is intentionally narrower than `plan.md:142` inside the consume-before-append window: even when `preIntentContinuationAllowed` is true (zero irreversible records), `dispatchSaveAll` refuses at `PostSaveComposition.swift:196-201` because the slot reports `entitlementConsumed`. This is fail-closed (no dispatch-safety gap); derive it independently as an explicit disposition if Phase B ever arms.
- INFO-4 — The immutable `v09/attempt-03/bindings.json` still contains the mislabel key `focused_11_suites` (line 45) by design; the corrected records now read "focused 8 suites 96/0" (`progress.md:22,175,307,322,329`; `execution.md:82,123`) and the reviewed artifact's bytes are unchanged (`737bdebb…beab`, matching the recorded hash at `progress.md:312`). Residual cosmetic inconsistency in an immutable artifact only.
- INFO-5 — Residual `--one-shot-authorization` flag naming: the CLI still requires the flag and decodes runID/planSHA256/reviewedImplementationSHA256 from it (`main.swift:58-63,107-126`), but the durable authority is the goal slot (`main.swift:134-148`, `GoalSlot.swift`, `reserveSaveAll`); naming only, no correctness impact.
- INFO-6 — Precision note on "no behavior drift": relative to the pre-repair gate, a candidate whose margin is *exactly* 1 pt (e.g. exactly 1 px at 1x, exactly 2 px at 2x) was previously refused by the strict `>` comparison and is now admitted by the `>=` comparison; this is precisely the frozen rule's semantics (`Coordinates.swift:342,363`; plan.md:130 "1-point safe-boundary refusal") that M-1 required the readiness gate to match, and it cannot alter transaction accounting (pre-dispatch only). Recorded for accuracy rather than as an issue.

## Read-only statement

This review performed no build, no test execution, no execution of `rev28ctl` or any product binary, no LINE.app interaction, no OS events, and no git writes. Only read-only commands were used (`cat`, `sed`, `awk`, `grep`, `find`, `shasum`, read-only `python3` hashing, and read-only git commands) plus `apply_patch` for the single output file. Exactly one file was written: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/v09/attempt-04/03-transaction-history.md`. `bindings.json` and every other reviewed artifact were left untouched.

## PHASE_B_STATUS

`FORBIDDEN_AB_EVALUATION`. Nothing in this review dispatches Save All, confirms a destination, arms eligibility, or in any way enables Phase B; all C4/entitlement statements above are code-and-evidence verification only.

verdict: PASS
