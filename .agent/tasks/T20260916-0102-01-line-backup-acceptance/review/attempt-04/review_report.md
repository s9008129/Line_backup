# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 04
- REVIEWED_PLAN_REVISION: 4
- REVIEWED_PLAN_SHA256: 2a0bd820d4d3953b16bca996a9b0b72c04d5be2dde70b6be5debc8b1e38bdc4d
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-04/plan_snapshot.md
- Repository anchor observed: WORK has no product `src/` or `tests/`; the formal project contains only config/state/run_log; the bridge/controller are separate read-only GUI-observation projects with no Backup Skill/state integration.
- Reviewer runtime/model: Codex desktop review context

## OWNER_VERDICT

The plan remains aligned with the goal: safely classify the existing 57-file destination for the exact requested LINE source, preserve formal state/photos, prove a real reusable offline transaction process, and stop before ambiguous GUI side effects. Rev4 correctly does not claim that an absent external producer already exists, and no implementation evidence is required at this gate.

It is not ready for Handoff. The remaining gaps are contract-level: several advertised commands/cases are not actually reproducible from the declared CLI, two verifier rows use an illegal state-axis value, the current formal config compatibility profile is undefined, the Status Contract fixture set is not exhaustive and contains an unreachable waiver scenario, and the new GUI ledger does not bound separately counted navigation/acquisition inputs. These can cause Stage 04/05 to implement or accept incompatible behavior.

Essentials are exact source correspondence, read-only filesystem/state evidence, real guarded resume/commit/finalize/duplicate behavior, and a bounded route decision. Bridge readiness remains supporting/non-gating; production Save-All remains a later plan. The largest risk is still provenance, with a second material risk that a nominally real CLI can diverge across unlisted race/status cases.

## GOAL_BASELINE

- PRIMARY_OUTCOME: safely establish whether the existing destination is a valid backup of `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17` / 57 images, otherwise stop without ambiguous or duplicate production side effects.
- SUCCESS_EVIDENCE: exact source correspondence; read-only filesystem and state/registry/intent/writer reconciliation; real subprocess restart/fault/race evidence through the operator process boundary; a separately classified current-runtime Save-All route; no prohibited GUI/formal-state mutation.
- MUST_NOT_BREAK: existing files and formal state remain read-only in this wave; `禎` and `楨` remain distinct; UNKNOWN dispatch remains a barrier; no self-authenticating fixture oracle; no unbounded GUI input or production download.
- CORE: source identity, filesystem/state integrity, reusable transaction safety, necessary route/stop decision, and independent acceptance.
- SUPPORTING: bridge/service diagnosis only when route-specific causal evidence proves necessity.
- BEST_EFFORT/NON_GOAL: production download in this wave, bridge repair without causal proof, migration/spelling merge, broad cleanup, and unrelated refactors.
- CRITICAL_PATH: offline verifier/transaction evidence first, identity reconciliation, then at most one explicitly authorized ellipsis observation if still necessary; production route only under a later reviewed plan.

## GOAL_ALIGNMENT

[VERIFIED] Rev4 preserves the primary goal and correctly treats valid-looking files, historical PASS labels, bridge readiness, and an absent producer as insufficient source or transaction proof.

[VERIFIED] The `CORE`/`SUPPORTING` split is proportionate. Exact identity, uncertain dispatch, destination safety, and persistent state integrity have explicit correctness rationales; bridge readiness is explicitly non-gating.

## NECESSITY_AND_TRACEABILITY

[VERIFIED] The new verifier/transaction package is justified as the task's operator-facing reusable product boundary, not as an alleged existing producer. The formal data project remains an input/state authority and is read-only.

[VERIFIED] The route ledger, independent oracles, status fixtures, and source tri-state each trace to a stated acceptance or must-not-break obligation.

## GATE_AND_VETO_AUDIT

[VERIFIED] The hard gates protect exact source identity, duplicate/dispatch safety, destination integrity, persistence integrity, or acceptance validity. The plan explicitly permits route observation to end in UNKNOWN/SAFE_ABORT and does not authorize Save All.

[MAJOR GAP] The new ledger says acquisition/navigation inputs are counted separately (plan lines 273-275) but gives no allowed classes, maximum counts, or exact pre-gate boundary for those inputs. The one-ellipsis limit is exact, but “no unlisted input” cannot be independently enforced if navigation/acquisition can be unbounded or ambiguously included. This is an authorization/accounting gap, not a preference.

## COUPLING_AND_FAILURE_CONTAINMENT

[VERIFIED] Formal state/photos/destination are isolated from product test state; the fake dispatcher is limited to the final side-effect boundary; and bridge readiness cannot veto offline verification.

[VERIFIED] Rev4 fixes the prior shared-serialization omission by specifying `dirname(P)/.line-backup-state.lock`, POSIX `flock(LOCK_EX)`, the lock hold interval, revision/owner/run/intent predicates, atomic replacement, fsync/read-back, and deterministic barrier/fault concepts.

[UNVERIFIED] The acquisition race case is not reachable through the declared CLI as written; see RV4-001. Until that is corrected, the stated common boundary is not reproducibly testable for every claimed operation.

## DESIGN_ECONOMY

[VERIFIED] The package is the smallest stated reusable boundary that can prove the requested real-process transaction behavior in a repository where no such product exists. No distributed exactly-once design, formal migration, bridge refactor, or production download is added.

[MINOR] Existing evidence manifests and the root handoff are historical/stale relative to Rev4, but the plan explicitly requires Stage 03 to create a fresh task-bound handoff and new evidence; this is not itself an approval blocker.

## CRITICAL_PATH_AND_PRIORITY

[VERIFIED] The order remains correct: reproduce the old false positive, create the approved product package, prove verifier and transaction core, run offline reconciliation, resolve identity, and only then consider the bounded observation gate.

[VERIFIED] The plan does not let bridge deployment, GUI observation, or production download displace the existing-destination verify-only path.

## REQUIREMENT_FIDELITY

[VERIFIED] Rev4 adds the requested explicit CLI grammar, state fixture field set, call graph, 12 case roots, independent oracle fields, exact target strings, hashed historical action/scope/budget artifacts, route-result schema, one-ellipsis gate, tri-state source result, and `E2E_REQUIRED: NO` rationale.

[MAJOR] The concrete command requirement is still not satisfied consistently. Plan line 90 advertises a transaction `resume` entry point without the grammar-required `--expected-revision` and `--expected-owner-id`; only Case 01 and Case 04 have mostly fully expanded argv (lines 243-246). Cases 02/03/05/07-12 are prose descriptions, not literal reproducible commands. Case 07 additionally refers to “acquisition” and `ACQUIRE_BEFORE_LOCK`, while no `acquire` CLI or `prepare` pause flag is declared. The barrier is named `acquire.barrier` at line 116 but `acquire-ready.barrier` at line 247.

## GROUNDING_AND_DRIFT

[VERIFIED] The current formal config is 372 bytes and contains only `schema_version`, `group_key`, `group_name`, and `backup_root`; the current state is schema 2, revision 39, 48,146 bytes, with four verified entries and five runs. The target persisted key is `楨`, while the requested key is `禎`; the target run is legacy/provenance-limited.

[VERIFIED] The old verifier accepted both 56 and 58-image fixtures with exit 0; the current standalone canonical audit reports 57 stable recognized JPEGs and 17,924,900 bytes but omits mtime, full suffix/hidden/path checks, registry/source axes, and an artifact manifest.

[VERIFIED] Historical ledger hashes and sizes in Rev4 match the named `actions.jsonl`, `environment.json`, and `scope.json`: 4219/4555/1026 bytes and SHA-256 `9d6a1590…5aee` / `a43d23d6…2c95` / `6bb8795e…5aaa`. The ledger records two ellipsis inputs and no Save-All/menu-item click or state write; the environment records a 2/2 historical budget.

[VERIFIED] Bridge README/source and controller source are read-only observation infrastructure with no backup-state integration or Save-All dispatch. Current live readiness/menu capability is not proven here, and this review performed no GUI or deployment action.

## ARCHITECTURE_AND_CONTRACTS

### RV4-001 — MAJOR — ARCHITECTURE / TEST / GROUNDING

**Affected:** plan lines 90-122, 226-249; product boundary/call graph and transaction acceptance matrix.

**Evidence:** The declared grammar requires expected revision/owner on resume (line 97), but the separate advertised transaction entry point omits them (line 90). The plan promises literal expanded argv for every case (lines 109 and 237), yet supplies full argv only for selected cases; the remaining cases name adapters/barriers without exact command lines. Case 07 invokes an undeclared acquisition operation/pause boundary, and its barrier path conflicts internally (`acquire.barrier` versus `acquire-ready.barrier`). The state fixture is a required field inventory, but not a complete typed/literal initial fixture contract for every operation.

**Failure/rework mechanism:** Stage 04 can implement a command set that passes the shown happy path while restart, acquisition contention, fault, or finalization cases require flags/operations that do not exist. Stage 05 cannot reproduce the claimed call graph or independently prove that every transition uses the same operator process. A barrier-name or missing-argument mismatch also makes the race result non-auditable.

**Smallest required correction:** Make the grammar internally identical everywhere; add the missing resume arguments to line 90; provide fully expanded literal argv/process-launch/release commands and expected input/output artifact paths for Cases 01-12; define whether acquisition is `prepare` or a separate command; declare all pause/fault flags on the operation that uses them; fix the barrier name; and specify required/optional types plus the literal initial/post fixture shape. Keep the external LINE producer explicitly absent/unproven.

### RV4-002 — MAJOR — SEMANTIC_CONTRACT / TEST

**Affected:** plan lines 188-218, especially verifier matrix rows “Destination outside backup_root” and “Special file”.

**Evidence:** Those rows set the `State` axis to `NOT_ACHIEVED`, but the plan's own state outcome contract lists only `EXACT`, `ABSENT`, `AMBIGUOUS`, `LEGACY_PROVENANCE_LIMITED`, and `STATE_CONTRADICTED` (lines 155-161). `NOT_ACHIEVED` is a primary/overall status, not a legal state-axis value.

**Failure/rework mechanism:** The verifier can emit an output that violates its declared five-axis contract, or Stage 05 may normalize the illegal value inconsistently. That defeats deterministic status/exit/oracle comparison precisely on path-safety failures.

**Smallest required correction:** Replace the illegal state value with one explicitly justified legal state result (`NOT_RUN`, `UNKNOWN`, or `STATE_CONTRADICTED` as appropriate to the exact validation order), and state the downstream-axis rule. Add a schema assertion that no axis accepts values from another subject's enum.

### RV4-003 — MAJOR — COMPATIBILITY / GROUNDING / SEMANTIC_CONTRACT

**Affected:** plan lines 83-105, 174-182, and the real verify-only command at line 88.

**Evidence:** The command is required to run against the current formal config/state, but “validate schema” is not defined as a compatibility profile. The applicable LINE state contract requires additional config fields for the full mutating workflow (`app_identifier`, `max_albums_per_run`, `recovery_limit`, polling/sample/wait settings), while the actual selected config contains none of them. The actual state also contains legacy runs with missing RC2 fields.

**Failure/rework mechanism:** An implementation that validates the full skill config schema will reject the mandated current verify-only command; an implementation that accepts everything without a declared legacy branch may silently treat incomplete current authority as valid. Either outcome can block or falsely pass the CORE reconciliation.

**Smallest required correction:** Define the product's verify-only compatibility profile separately from the mutating transaction-fixture profile: exact required current-config fields, allowed legacy omissions, state legacy normalization, and exact failure/status/exit for missing authority. State whether the real current config is expected to pass verify-only or be a deterministic blocked/invalid case, without mutating or initializing the formal project.

### RV4-004 — MAJOR — TEST / STATUS_CONTRACT / SEMANTIC_CONTRACT

**Affected:** plan lines 291-342, especially the routing fixture table at lines 318-335 and check metadata at lines 304-316.

**Evidence:** Rev4 includes many required rows, but it does not include explicit rows for the canonical incident, baseline-delta, hard-clean pre-existing debt, or valid CORE `NOT_REQUIRED` with its Plan rationale. The waiver row claims “all required items formally waived,” while every required table item has `WAIVER_ALLOWED: NO`; the only `YES` item (`BRIDGE_READINESS`) is `NON_GATING`, so the row is unreachable under the declared matrix. The waiver row also does not explicitly assert preservation of the original item-level `CHECK_RESULT` and the complete waiver fields.

**Failure/rework mechanism:** Stage 04/05 can appear v2-shaped while routing baseline absence versus delta, hard-clean debt versus regression, valid NOT_REQUIRED versus NOT_RUN, canonical incident, or waiver-versus-PASS incorrectly. An impossible waiver fixture cannot prove the required original-result-preservation rule.

**Smallest required correction:** Add exact fixture rows for each omitted branch, including all six orthogonal statuses, scoped blocker/class, baseline rule, `CHECK_RESULT`, `WAIVER_STATUS`, and closure. Either define a narrowly justified required check that is actually waivable by the named authority, or make the waiver fixture explicitly synthetic/contract-only with a waivable check and assert that its original result remains visible; never let it imply that a non-gating bridge waiver satisfies closure.

### RV4-005 — MAJOR — SCOPE / TEST / SECURITY

**Affected:** plan lines 271-289, particularly ledger accounting and Human Gate.

**Evidence:** Historical action/scope/budget provenance is now correctly named and hashed, and the exact raw target/one ellipsis input is correct. However, the new schema's `allowed_budget_before/after` fields do not have declared numeric budgets for app acquisition/navigation, and the plan does not state whether those inputs occur before the Human Gate, count against a separate finite allowance, or are forbidden once the exact album card is in view.

**Failure/rework mechanism:** A later run could remain at one ellipsis click while performing unbounded or unaccounted acquisition/navigation, making the ledger unable to prove the “no unlisted input” and exact-scope claims. Conversely, an implementer may reject necessary acquisition because the only explicit allowance is the ellipsis input. This risks either authorization drift or an unusable gate.

**Smallest required correction:** Declare the exact allowed action classes and finite counts for acquisition/navigation, their phase boundary relative to the Human Gate, and the invariant that only one current-target ellipsis input is permitted after target binding. Require the ledger/oracle to reject any unlisted or over-budget event before route status can be AFFIRMATIVE; preserve menu-item/Save-All/chooser/state-write counts at zero.

## DATA_SECURITY_RELIABILITY

[VERIFIED] The plan preserves formal state and existing photos, rejects unsafe destination/entry forms, requires content-based MIME and SHA-256/size/mtime evidence, separates storage from dispatcher faults, retains UNKNOWN dispatch barriers, and forbids AXPress/AX writes/OCR-only acceptance/guessed coordinates/retry after uncertainty.

[VERIFIED] The `禎`/`楨` rule is safe: raw strings and keys remain separate; exact correspondence requires an authoritative join or an explicitly recorded user fact; legacy provenance cannot authorize dispatch; unresolved/contradicted identity stops the exact-source outcome.

[MINOR] The plan should retain explicit evidence that the current real config is only a minimal legacy-compatible authority if that is the intended verify-only profile; this is included in RV4-003 as a required plan correction rather than assumed behavior.

## IMPLEMENTATION_SEQUENCE

[VERIFIED] The offline-first sequencing is correct and does not require product implementation, deployment, GUI, download, or formal-state evidence for this review.

[MAJOR] Handoff must not be compiled until the command/case protocol and status/config compatibility corrections are made, because those are prerequisites to a reproducible Stage 04/05 contract rather than implementation polish.

## TESTABILITY_AND_ACCEPTANCE

[VERIFIED] Rev4 correctly requires the real operator CLI/library path, subprocess boundaries, independent pre/post state/counter hashes, named barriers/faults, exact verifier axes/exits for most rows, artifact manifests, immutable Stage-04 snapshot fields, and independent Stage 05 acceptance.

[MAJOR] The gaps in RV4-001 through RV4-005 still permit a non-reproducible transaction case, illegal verifier output, incompatible current-state handling, incomplete v2 routing coverage, or unbounded GUI accounting. These are acceptance-invalidating plan defects, not absent implementation evidence.

## SCOPE_AND_COMPLEXITY

[VERIFIED] Scope is economical and within one album. The absent formal producer is explicitly not claimed; product code is intentionally deferred until approval, as requested.

## FINDINGS

- RV4-001 — MAJOR — declared CLI/call graph/state fixture is internally inconsistent and does not provide literal reproducible commands for all cases; Case 07 uses an undeclared acquisition/pause interface and conflicting barrier names.
- RV4-002 — MAJOR — verifier rows use illegal `State=NOT_ACHIEVED`, crossing the primary/overall enum into a five-axis subject.
- RV4-003 — MAJOR — verify-only compatibility with the actual minimal formal config and legacy state is undefined despite the mandated real command.
- RV4-004 — MAJOR — Status Contract fixture coverage is not exhaustive; baseline-delta, hard-clean debt, canonical incident, valid CORE NOT_REQUIRED, and reachable waiver/original-result preservation are missing or inconsistent.
- RV4-005 — MAJOR — new GUI ledger counts navigation/acquisition but does not define their finite allowance/phase boundary, so exact-scope accounting is not enforceable.
- Handoff freshness — MINOR — root `handoff.md` and older evidence manifests are historical; the plan already requires a fresh Stage 03 handoff bound to Rev4/hash.

No implementation, deployment, GUI observation, download, formal-state mutation, or acceptance was performed or inferred by this review.

## REQUIRED_PLAN_CHANGES

1. Correct RV4-001 by making grammar, call graph, state fixture, barrier names, and all Case 01-12 commands fully literal and mutually consistent.
2. Correct RV4-002 by using only legal subject-specific verifier axis values and asserting enum separation.
3. Correct RV4-003 by defining the current-formal-config/legacy-state compatibility profile and exact verify-only result for missing fields.
4. Correct RV4-004 with exhaustive v2 routing fixtures, a reachable waiver scenario or explicit synthetic waiver contract, and original-result preservation assertions.
5. Correct RV4-005 with explicit finite acquisition/navigation budgets and phase/accounting rules while retaining the exact one-ellipsis gate.
6. Increment the same TASK_ID from Revision 4 to Revision 5, preserve unaffected decisions, and submit the new revision to a fresh independent CRITICAL review. Do not create/update Stage 03 Handoff before approval.

## RESIDUAL_MINOR_NOTES

- [VERIFIED] Current filesystem evidence supports only present file completeness; it does not prove exact source history, uniqueness, original resolution, or full decode quality.
- [VERIFIED] Current source identity remains unresolved (`禎` versus persisted `楨`); this is correctly represented as a future CORE stop, not a reason to fabricate correspondence.
- [VERIFIED] The bridge/controller evidence supports read-only observation-contract claims only; it does not prove current live Save-All capability or a reusable backup transaction engine.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revise the same TASK_ID to Revision 5, addressing RV4-001 through RV4-005, then rerun Stage 02 independently.
