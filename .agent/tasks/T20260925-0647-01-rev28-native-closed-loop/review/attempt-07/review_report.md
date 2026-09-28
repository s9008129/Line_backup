# Stage 02 independent plan review — attempt 07

REVIEWED_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da  
REVIEWED_REMOTE_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da  
PLAN_REVISION: 4  
PLAN_SHA256: 05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b  
REVIEW_RESULT: PLAN_APPROVED  
NEXT_ROUTE: READY_FOR_HANDOFF

## FRESHNESS_RESULT

PASS. `git fetch origin --prune` succeeded. Local and remote HEAD equal the Plan's bound commit. The Plan SHA-256 equals the required value; every entry in `planning-artifacts.sha256` passed verification. `final-audit.json` records `headFresh=true`, `planHashMatches=true`, `protectedProductTestWorkflowStatus=UNCHANGED`, and `readyForPlanReview=true`. The initial worktree had the expected R4 Plan/analysis/decision files modified or untracked; this review preserved them. The snapshot in this attempt is a byte-for-byte copy of the reviewed Plan.

## GOAL BASELINE AND FALSIFICATION RESULT

The goal is one newly downloaded staging copy of the exact LINE group and album, with a one-shot irreversible path and authoritative filesystem proof of `DUPLICATE_CONTENT_CONFIRMED`. I tested whether R4 could misdirect implementation or authorize unsafe input. No blocking counterexample was found in the specified Stage 01 evidence or the targeted source reads below.

## BLOCKING_FINDINGS

NONE.

## LOAD-BEARING CHECKS

| Claim | Independent review result |
|---|---|
| A — current blocker | `StructuralLocatorsTests.swift` declares `binding` as a computed property and `item(...)` as its OCR helper; two new tests call `binding()` and `ocr(...)`. R4 correctly treats the test compile failure as the first blocker. Those helper fixes cannot make the real CLI reach the engine. |
| B/C — production root cause and CI distinction | `rev28ctl/main.swift` constructs an owner, then unconditionally refuses `live-execute` before any `LiveExecutionEngine.run()`. `rg` over `rev28/Sources` found the adapter protocol and engine definition but no concrete source adapter or engine invocation. `LiveExecutionEngineTests.swift` supplies a `FakeAdapter` with synthetic chooser and tripwire artifacts. R4 requires one common engine and policy, with injection below safety decisions. |
| D — transaction authority | The current owner derives counts from ledger entries, but `main.swift` omits a checkpoint, preflight consumes the one-shot file, `IntentLedger.append` is public, and the owner currently accepts SHA strings for state transitions. R4 explicitly requires a persistent goal slot, mandatory independent anchor, owner-enforced eligibility/state/evidence, and permanent budget consumption on intent. It forbids a new run ID or generic append from creating semantic authority. |
| E — observation authority | `FrameCaptureService.capture` makes a structured frame record; `ReadinessObservation.captureLive` independently recaptures with its own configuration and reuses the candidate epoch after a hash comparison. R4 requires one retained-image session with process/window/capture epoch/frame hash/geometry/OCR/AX/tripwire/deadline provenance and fresh re-localization after redraw. |
| F — deterministic defects | `StructuralLocators.isDateRangeTitle` requires three components on both sides, so the target's short end date cannot be segmented. `StagingVerifier.isStable` checks total history span while comparing only the final three signatures. R4 separately requires repairs and regression cases for both, with the stable span measured over the equal tail. |
| G — Phase A | The current `live-preflight` creates a ledger/owner and renames the one-shot authorization to `.consumed`; its name does not make it read-only. R4 requires zero Save All and confirmation intents/attempts, retention of the one-shot entitlement, real LINE observations and a Phase A evidence manifest. |
| H — Phase B gate | R4 makes eligibility a typed, persisted, rechecked conjunction. FAIL, UNKNOWN, NOT_RUN, stale or missing hash, and unbound evidence are ineligible; human authorization cannot promote them. Actual chooser/content facts are deferred runtime gates with fail-closed outcomes. |
| I/J — history and final acceptance | R4 preserves Rev27 `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` and limits historical coordinates to evidence. It requires 57 complete stable decodable regular images, 17,924,900 bytes, content multiset `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`, baseline unchanged, name-inclusive tripwire `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`, and independent Stage 05 recomputation. Click/menu/chooser/count alone cannot close the task. |
| K — critical path and convergence | The first action repairs the test helper interface so deterministic tests can execute; date and stability fixes precede native composition and Phase A. Phase B is conditional on all pre-B gates. The Plan specifies ceilings of three material attempts per blocker, two consecutive no-information attempts, immediate A→B→A escalation, and no reset on model/session/hypothesis changes. |

## NON_BLOCKING_NOTES

- Real LINE layout, permissions, chooser hosting, and eventual download content remain unobserved. R4 assigns these to Phase A and the single conditional Phase B, with explicit refusal when facts cannot be proved.
- Source inspection and the Stage 01 diagnostic record support this review. I did not rerun a build, test suite, live preflight, or GUI action; Stage 02 approval is approval of the execution Plan, not a claim of implementation or outcome success.
- Stage 03 must bind its handoff to this exact Plan SHA and review snapshot. The existing handoff remains historical/stale as recorded in `decision.md`.

## ROLE_ISOLATION

PRODUCT_CODE_MUTATED: NO  
TEST_CODE_MUTATED: NO  
WORKFLOW_MUTATED: NO  
PLAN_MUTATED: NO  
HANDOFF_MUTATED: NO  
EXECUTION_MUTATED: NO  
GIT_COMMIT_CREATED: NO  
GIT_PUSHED: NO

PLAN_APPROVED
