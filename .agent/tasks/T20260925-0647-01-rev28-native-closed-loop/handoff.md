# Stage 03 Execution Contract — Rev28 native closed-loop backup

## TASK

TASK_ID: T20260925-0647-01-rev28-native-closed-loop  
PLAN_REVISION: 4  
PLAN_SHA256: 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b  
PLAN_REVIEW_ATTEMPT: 07  
PLAN_REVIEW_RESULT: PLAN_APPROVED  
REVIEW_REFERENCE: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/review/attempt-07/review_report.md`  
REVIEWED_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da  
TARGET_BRANCH: `rev28-prelive-finalization`  
HANDOFF_STATUS: READY_FOR_IMPLEMENTATION  
INDEPENDENT_ACCEPTANCE_REQUIRED: YES  
TASK_CLASS: CRITICAL  
NEXT_STAGE: STAGE_04_IMPLEMENT

## GOAL_ANCHOR / PRIMARY_OUTCOME

Create one new staging copy from real LINE (`jp.naver.line.mac`), group `旻謙允禎成長日記`, album `2024/05/13～05/17`. The only successful primary outcome is `DUPLICATE_CONTENT_CONFIRMED`, proven by authoritative filesystem evidence and later independent Stage 05 recomputation:

- Exactly 57 complete, stable, decodable regular image files; no symlink, hidden/extra/non-image entry, nested directory, partial, zero-byte file, or duplicate content within staging.
- Exactly 17,924,900 total bytes.
- Filename-excluded content multiset SHA-256: `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`.
- Baseline unchanged, including per-file names, bytes, hashes and mtimes. Name-inclusive tripwire SHA-256: `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`.
- On a successful production run: exactly one Save All dispatch and exactly one destination confirmation. These are ceilings under refusal/failure; an irreversible intent consumes its budget even if effect is unknown.
- Preserve and bind the full fresh LINE identity, geometry, chooser, transaction and filesystem evidence chain. Click return, menu/chooser visibility, file count, or Stage 04's verdict alone never establishes completion.

Baseline reference: `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json`, SHA-256 `3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2`; authoritative source directory is `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`. Recompute at execution start and closeout. Preserve the old staging, evidence, review, frozen-rule and unrelated files.

## CURRENT_BLOCKER / PRIMARY_OUTCOME_GAP

`StructuralLocatorsTests.swift` does not compile: two new tests call the computed `binding` property as `binding()` and use nonexistent `ocr` helpers instead of the existing `item` helper. Secondary compiler diagnostics are not a separate blocker. The focused target therefore cannot execute at the reviewed HEAD.

The primary outcome gap remains the missing reachable native production composition: the CLI refuses `live-execute`, and no native observation session/real adapter connects the common engine to fresh observations, one-shot transaction authority, actual chooser and final filesystem proof. Repairing the test helper calls only restores diagnostic execution; it does not resolve this gap. R4 also separately records the short end-date segmentation defect and stability-span defect. Handle each in the approved dependency order without loosening identity or acceptance.

## FIRST_IMPLEMENTATION_BLOCKER_FINGERPRINT

```text
STAGE=04
CHECK=DETERMINISTIC_SWIFT_TEST_COMPILATION
SURFACE=rev28/Tests/Rev28CoreTests/StructuralLocatorsTests.swift
EXPECTED=Swift test target compiles and StructuralLocatorsTests executes
OBSERVED=Swift test target compilation fails before test execution
```

This identity is fixed by the failed acceptance condition. Do not rename it when changing hypothesis, model, session or wording. Do not substitute the primary architecture gap as the first material attempt.

## CRITICAL_PATH / IMPLEMENTATION_WAVES

1. Reverify source/remote/review/Plan/hash and preserve the current dirty worktree. Reconcile the archived R3 execution history and seed V4.3 blocker counters; R4 planning diagnostics are not implementation attempts, and missing telemetry is not proof of unused budget.
2. Restore test execution with the smallest helper-call correction. Then fix and test exact short-date segmentation and the independently reproduced equal-tail stability-span defect.
3. Extend the existing `LiveExecutionEngine` and `PersistentTransactionOwner` into one native composition. Add coherent retained-image observation/session evidence, durable goal-slot/ledger/anchor authority, typed eligibility/evidence checks, native tripwire and actual adapter. Do not create a parallel production engine.
4. Validate the same composition through low-level injected OS interfaces, real synthetic AppKit panels, full refusal/restart matrix, replay/adversarial tests and current V-09 independent exact-binding reviews.
5. Only after pre-A safety checks, run Phase A on a real Mac/real LINE with zero Save All and zero destination-confirmation intents/attempts. Capture the required real observations and V-09 LINE-specific supplement.
6. Recompute the complete machine-checkable Phase B conjunction on the exact reviewed source/binary/rules and fresh evidence. B requires every predicate PASS, explicit one-shot Phase B authorization and a valid exact canonical staging path. Any non-PASS means ineligible.
7. If eligible, perform the one guarded Save All, observe the actual chooser within the hard window, prepare the authorized destination reversibly, then the one bound AXPress. Observe download read-only; verify stable contents and baseline; finalize append-only evidence.
8. Fresh Independent Stage 05 independently recomputes filesystem and transaction evidence. Close only if every outcome and closure gate passes.

### CORE

C1–C7 in Plan R4 are binding: repair existing test helper usage; exact date/card segmentation and association on one image; one common native composition; one immutable fresh observation bundle; one durable transaction authority and no budget-reset route; guarded single-use actuation; actual chooser/destination binding; real tripwire and stable filesystem proof/finalization. Preserve all refusal behavior and identity/geometry/freshness rules. See approved `plan.md` sections C1–C7 for the complete semantic contract.

### SUPPORTING

Build/test determinism, pinned fixture integrity, replay/adversarial parity, current-composer synthetic calibration, capability/evidence manifests, append-only execution artifacts and preservation audit are required at their specified gates. V-08 is classified SUPPORTING / NON_GATING for closure, but its explicit pre-B interlock remains mandatory.

### BEST_EFFORT_DO_NOT_GATE

Diagnostics/registration/Foundation Models are non-authoritative and non-gating. Do not delay the core route for optional features.

## MUST_NOT_BREAK / SEMANTIC_INVARIANTS

- Owner plus IntentLedger is the sole transaction authority. Persistent goal slot, independently stored anchor, hash chain, exclusive writer, state and budgets must survive run/session/path/token changes. Missing/corrupt/uncertain state fails closed; never reconstruct authority from untrusted history.
- Phase A leaves `intent.saveAll=0`, `attempt.saveAll=0`, `intent.destinationConfirmation=0`, `attempt.destinationConfirmation=0`, and leaves the one-shot entitlement unconsumed. Do not rename the entitlement to `.consumed` in preflight.
- Any irreversible intent/attempt makes every restart permanently observe-only. Unknown effects never permit retry, fallback, replacement run, or another confirmation.
- One retained screenshot/image is the source for its OCR/structure/frame evidence; every observation carries fresh process/window/epoch/geometry/provenance. No stale candidate relabeling, caller-asserted freshness, or observer exception converted to success.
- Save All requires fresh `SAVE_ALL_LOCATED` plus persisted `PHASE_B_ELIGIBLE`; confirmation requires the actual in-window chooser, approved tripwire and exact prepared destination. Adapters/generic append/SHA strings cannot manufacture semantic authority.
- Preserve reviewed 150 ms/8 s then 500 ms/15 s chooser monitor bounds, one late forensic sample (never affirmative authority), and no input after post-intent refusal/timeout/uncertainty. Destination confirmation is one AXPress on the unique bound default button; no production Return fallback or retry.
- Baseline modification always aborts. Preserve Rev27 `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` and historical coordinates as evidence only.
- Never weaken counts/digests, identity, geometry, chooser, tripwire, time bounds, acceptance, requiredness or gates. Never copy baseline images into staging to pass.
- Final filesystem stability: at least 3 equal contiguous snapshots spanning at least 4 seconds and at least 5 seconds without file/directory change; hash/decode same bytes; maximum automatic observation 10 minutes from confirmation. Timeout stays incomplete/unstable; no new download.

## ALLOWED_MUTATION_SURFACES

During Stage 04 only, the Plan permits `rev28/Sources/Rev28Core/**`, necessary production composition under `rev28/Sources/rev28ctl/**`, relevant `rev28/Tests/**`, `rev28/Tools/**`, and necessary architecture/capability documentation. Small additions within these areas may implement the explicit native/session/gate contracts. Append task/evidence artifacts. Reuse existing components. Any CI wiring change requires an evidenced need inside the reviewed test contract.

## FORBIDDEN_MUTATION_SURFACES

Do not mutate baseline or staging content, protected files under `rev28/` outside the allowed source/tests/tools scope, frozen calibration/provenance history, `.github/` workflows absent the narrowly evidenced Plan exception, unrelated repository files, or prior append-only task artifacts. No dependency update, broad cleanup/framework rewrite, second backup, packaging, or unrelated feature. Any semantic boundary listed in REPLAN_CONDITIONS requires replan, not local contract drift.

## REVERIFY_ON_START

Fetch `origin --prune`; record branch, local HEAD and `origin/rev28-prelive-finalization`; inspect dirty/untracked state before mutation and preserve it. Recheck Plan SHA, review attempt 07/result/snapshot, handoff SHA, source freshness, and new commits against the R4 assumptions and acceptance. Recompute baseline reference plus names/bytes/hashes/mtimes and both digests; inspect old staging and every goal/ledger/anchor history. Unknown transaction state blocks execution. Verify exact source/build configuration/binary/rules/frozen sampler/fixtures/current CI evidence, then recheck executable-context TCC, LINE/session/display/SDK and sensor capabilities in the native context. No Stage 04 work may overwrite unrelated dirt.

## FIRST_ACTION

After the above rechecks, make the smallest change in `rev28/Tests/Rev28CoreTests/StructuralLocatorsTests.swift`: use the existing computed `binding` property and existing `item(...)` OCR helper at the two erroneous test call sites. Do not delete/skip tests or alter expected refusals. Then run the targeted sequence beginning with `xcrun swift build --package-path rev28` and `xcrun swift test --package-path rev28 --filter StructuralLocatorsTests`.

Expected mechanical result: test target compiles and the focused test cases execute. If the same compile failure remains, the distinguishing outcome was not achieved; record evidence and count convergence accurately. If tests execute and reveal segmentation behavior, classify that under its own later approved blocker/step. This first action does not connect the production CLI to the engine or prove any real LINE behavior.

## TEST_ORDER

Do not start with expensive live E2E. Preserve dependency order and do not skip a later gate after an earlier PASS:

1. Narrow diagnostic: `xcrun swift build --package-path rev28`; focused `StructuralLocatorsTests`; focused `StagingVerifierTests`, adding minimal short-end-date/cross-card and old-different-sample/short-equal-tail regressions.
2. Run deterministic Swift tests per current macOS 27 workflow, keeping Vision tests and any hosted Vision limitation explicit; then the full suite on this real Mac in executable context. No production LINE input in CI.
3. Run the existing 25-case adversarial suite and all 20 pinned replay fixtures twice each with semantic parity; verify hashes against archived anchors/current pinned manifest. Replay actual segmentation, not only supplied card regions.
4. Run the common-composition failure matrix (freshness/identity/geometry, permits, sampling, chooser ownership, destination/focus, tripwire, baseline, content, evidence tampering and invalid state) and owner/restart matrix (second owner, ledger/anchor damage, continuation, crashes at each irreversible boundary, independent dispatch counts).
5. Run `python3 -B rev28/Tools/verify_pre_live_provenance.py` and preserve exact v3 historical binding. Run current-composer synthetic AppKit calibration with actual NSOpenPanel/SCK/Vision/AX, separate-process occluder and real input sink; include at least 20 panel timings, strict monitor, destination/AXPress and refusal/crash behavior. Never synthetic-dispatch into LINE.
6. Complete V-09 exact-binding code/rule reviews before Phase A. After Phase A, complete LINE-specific V-09 supplements. These reviews are independent of Plan Review attempt 07.
7. Phase A eligibility/evidence only after all preceding dependencies. Recompute every Phase B predicate; Phase B is forbidden unless all are PASS and explicit one-shot authorization exists.
8. Conditional Phase B runtime gates, stable/content/baseline proof and append-only finalization. Stage 05 performs independent recomputation last.

## MECHANICAL_ACCEPTANCE / ACCEPTANCE_CONTRACT

For every check retain result (`PASS|FAIL|BLOCKED|NOT_RUN`), command/scenario, exact source/binary/rule inputs, raw output/evidence path and SHA, and scoped status. No self-waiver; all checks use `BASELINE_RULE=none`, `BASELINE_REQUIRED=NO`, `WAIVER_ALLOWED=NO`, `WAIVER_AUTHORITY=NONE`, `WAIVER_STATUS=NOT_ALLOWED`. Closure gate classification does not remove explicit pre-B interlocks.

| CHECK_ID | COMMAND/SCENARIO / observable criterion | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING |
|---|---|---|---|---|---|---|
| V-01 | Actual binary SCK/Vision/AX/Quartz capability | CORE | DIAGNOSTIC | NON_GATING | none | Unknown/fail blocks phase |
| V-02 | Frozen geometry/chooser/monitor calibration applies to current composer | CORE | DIAGNOSTIC | NON_GATING | none | Repair mechanically or replan; mandatory before B |
| V-03 | Every frame/permit meets identity, geometry and freshness rules | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | Invalidate candidate; stop at budget/irreversible boundary |
| V-04 | Actual chooser affirmed by strict predicate within 15 seconds | CORE | OUTCOME | HARD_CLEAN | none | Named terminal; zero further input |
| V-05 | Bound chooser and exact path; exactly one confirmation; no unknown retry | CORE | OUTCOME | HARD_CLEAN | none | Refusal/indeterminate; preserve spent budget |
| V-06 | 57 stable decodable regular files, exact bytes and multiset | CORE | OUTCOME | HARD_CLEAN | none | Named staging/content failure; no redownload |
| V-07 | Reference/baseline digests and per-file mtimes unchanged | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | Block before B or abort with zero input |
| V-08 | Pinned replay/adversarial suite twice with refusal parity | SUPPORTING | DIAGNOSTIC | NON_GATING | none | Repair/replan; mandatory pre-B interlock |
| V-09 | Seven topic reviews + adversarial + Rev27 barrier supersession on exact bindings | CORE | DIAGNOSTIC | HARD_CLEAN | none | Resolve and fresh-review before applicable phase |
| V-10 | Independent Stage 05 filesystem/transaction recomputation | CORE | OUTCOME | HARD_CLEAN | none | Acceptance failure/replan; preserve proven facts |
| V-11 | Do-not-touch/unrelated-work preservation; no unauthorized commit/push | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | none | Stop closeout claim and report |
| V-12 | Build and required deterministic/native Swift tests execute and pass | SUPPORTING | DIAGNOSTIC | HARD_CLEAN | none | Repair current compile regression before B |
| V-13 | Same composed engine/authority/gates in real and injected paths; full failure matrix | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | Repair or replan divergence/forged success |
| V-14 | Complete real-Mac Phase A evidence and zero irreversible intent/dispatch | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | Fail closed; no B |
| V-15 | Goal slot/anchor/intent ordering/restart/no-reset authority | CORE | MUST_NOT_BREAK | HARD_CLEAN | none | Uncertainty is observe-only; no B |
| V-16 | Append-only final manifest/empirical record/ledger bind raw evidence | CORE | OUTCOME | HARD_CLEAN | none | Missing evidence stays incomplete |

True final acceptance is `DUPLICATE_CONTENT_CONFIRMED` only with all exact filesystem and baseline facts in GOAL_ANCHOR, exactly one authorized Save All and one confirmation, complete bound evidence, and Stage 05 independent recomputation. No UI state is sufficient.

## PHASE_A_REQUIREMENTS

Real Mac and real LINE observation/preflight only. Keep production Save All dispatch count and destination confirmation count at zero; both irreversible intents and attempts remain zero; do not consume/rename the one-shot entitlement. Guarded reversible navigation to the exact album and optional open/dismiss of ellipsis are allowed under the persistent reversible budget; never activate a production menu row to test it.

Record real process/signature/start, executable-context TCC, SCK/CG/AX inventory, display/backing scale, frozen capture geometry, same-frame Vision, exact group/date/count and card association, album re-verification, ellipsis and five-row menu localization, popup/occlusion assumptions, pre-panel census, baseline integrity, empty unique staging/evidence separation and native tripwire readiness. Capture ≥10 seconds pre-dispatch environmental context whenever at `SAVE_ALL_LOCATED`. Publish `phase-a.json` and raw evidence manifest with per-condition PASS/FAIL/UNKNOWN and ledger-proven zero irreversible counters. State explicitly that chooser assumptions are calibrated on real NSOpenPanel and actual LINE chooser is not yet observed. Any missing, failed, unknown, not-run, stale, unbound or ambiguous condition prevents B.

## PHASE_B_ELIGIBILITY

All machine-checkable predicates must be PASS and persisted/rechecked at reservation: exact approved Plan and Stage 03 binding; exact reviewed implementation source/config/tool manifest, HEAD/diff and binary hash; current rules/predicate/fixture/provenance hashes; all required independent reviews current and issue-free; V-01/02/08/09/12/13/14/15 prerequisites PASS; fresh Phase A plus immediate fresh LINE re-observation; valid exclusive goal slot/ledger/anchor and unused irreversible budget; baseline and empty canonical staging verified; tripwire has ≥10-second context and no gaps; strict observer/deadline armed; all refusal branches demonstrated; explicit one-shot Phase B authorization. Any FAIL, UNKNOWN, NOT_RUN, stale/missing hash or unbound evidence means `PHASE_B_INELIGIBLE` and zero irreversible dispatch. Human authorization cannot convert a failed machine predicate to PASS. Actual LINE chooser and final content are runtime gates, not pre-B facts.

## PHASE_B_EXECUTION_CONTRACT

Only after eligibility PASS and explicit authorization: reserve/consume one durable Save All intent/attempt, then one guarded Quartz click. Observe the actual new chooser with strict SCK+CG+AX/process/signature/ownership predicate inside the 15-second cap. Any refusal, observer/tripwire error, no/late chooser or uncertainty ends GUI input permanently. On affirmative chooser plus tripwire gate, prepare only the exact authorized canonical staging path with freshly bound panel/navigation field and verified reflected destination. Reserve/consume one confirmation and perform exactly one AXPress on the bound unique default button. No production Return fallback, second AXPress, blind retry, replacement run or new authorization after uncertain effect. Observe download read-only for at most 10 minutes; prove stable snapshots/content/baseline, then append evidence and finalize. Any restart after irreversible intent/attempt is observe-only.

## ATTEMPT_BUDGET / INFORMATION_GAIN_RULE

Budget is scoped to `TASK_ID + BLOCKER_FINGERPRINT`, never model/session/hypothesis wording:

- `MAX_MATERIAL_ATTEMPTS_PER_BLOCKER = 3`
- `MAX_CONSECUTIVE_NO_INFORMATION_GAIN = 2`
- `A -> B -> A` caused by attempted fixes: immediate escalation.
- Ceiling, not quota. Before each attempt require a falsifiable hypothesis, genuinely new information source and distinguishing result. If the next action has none, stop and escalate without spending another attempt.

For each material attempt record `ATTEMPT_ID`, fingerprint, `HYPOTHESIS`, `EXPERIMENT_OR_CHANGE`, `EXPECTED_DISTINGUISHING_RESULT`, `OBSERVED_RESULT`, `ACCEPTANCE_DELTA`, `NEW_EVIDENCE`, `UNCERTAINTY_REDUCED`, `INFORMATION_GAIN: YES|NO`, and `NEXT_DECISION`. Commands/re-runs with materially identical evidence, log rereads, cosmetic changes or renamed hypotheses do not create progress or reset budgets. Reconcile R3 execution history and R4 analysis before initializing counters; R4 decision records zero R4 analysis material implementation attempts, while earlier same-fingerprint material work must still be accounted for if evidenced.

Maintain `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/progress.md` after every material result and each Stage 04 boundary. At convergence trigger create next unused append-only `escalations/attempt-N/` with installed-template `escalation.md` and `context.json`; set `IMPLEMENTATION_STATUS=ESCALATED`, `TASK_CLOSURE_STATUS=HIGH_REASONING_REVIEW_REQUIRED`. If a load-bearing Plan premise is disproved, route `REPLAN_REQUIRED`. High-reasoning review is Stage 06 escalation, not an automatic Stage 04 implementation wave.

## STOP_CONDITIONS

Stop GUI input and preserve evidence on any failed Phase B eligibility; preservation/baseline violation; missing authority/data; duplicate owner; spent/uncertain irreversible budget; identity/geometry/chooser/tripwire failure; deadline; or exhausted reversible/revalidation limits. No blind retry after unknown effect. Stop automatic download observation at 10 minutes and retain the incomplete/unstable result. Stop substantive local implementation at the convergence guard.

## ESCALATION_CONDITIONS

Immediately escalate on 3 material attempts for the same unresolved blocker, 2 consecutive no-information attempts, fix-caused A→B→A oscillation, an unfalsifiable next action, repeated experiment without a new evidence source, or a need to change a load-bearing semantic/architecture/security/data/public contract. Use the append-only escalation packet and V4.3 status routing; do not self-pause any Goal runtime.

## REPLAN_CONDITIONS

Replan if source/remote drift invalidates a load-bearing premise; architecture/session/owner boundary, chooser shape, capture rule, identity alias, validity/requiredness/gate policy, fallback semantics, migration/security boundary, acceptance/time bound or required attribution semantics must change. Stage 04 may settle mechanical details only. Preserve the existing Rev27 effect classification and do not disguise semantic drift as a bounded fix.

## EXPECTED_ARTIFACTS / STATUS_UPDATE_RULES

Stage 04: `progress.md`; append-only execution evidence and status updates; exact source/binary/rules/provenance manifests; V-09 review artifacts; native composition/calibration/test and authority/restart evidence; `phase-a.json` plus raw manifest; typed `eligibility.json`; transaction ledger/anchors; dispatch/chooser/tripwire/stable snapshot/content/baseline evidence; append-only final manifest/empirical class/FINALIZED transition; escalation packets when triggered. Stage 05 creates next unused `e2e/attempt-N/` and independently recomputes files, baseline mtimes, evidence chain, ledger and action counts. `result.md` only at actual closure.

Keep canonical statuses orthogonal. Initial Stage 04 facts: `PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED`; `IMPLEMENTATION_STATUS=NOT_STARTED`; `CORE_ACCEPTANCE_STATUS=NOT_RUN`; `REQUIRED_VERIFICATION_STATUS=FAIL` (reviewed-head focused test target compile failure); `INDEPENDENT_ACCEPTANCE_STATUS=PENDING`; `TASK_CLOSURE_STATUS=FIX_REQUIRED`. Update only from observed evidence; a build or synthetic run does not imply primary outcome or independent acceptance. Overall `DONE` requires outcome, implementation, CORE acceptance, all required verification, independent acceptance and no hard blocker.

NEXT_STAGE: STAGE_04_IMPLEMENT
