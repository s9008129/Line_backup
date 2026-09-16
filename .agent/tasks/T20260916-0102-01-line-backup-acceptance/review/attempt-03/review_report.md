# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 03
- REVIEWED_PLAN_REVISION: 3
- REVIEWED_PLAN_SHA256: b2e541d1edac85b6488d27e48bb9a5d3393651cf5dac7e789982325f8678f4d4
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-03/plan_snapshot.md
- Repository anchor observed: WORK has no `src/` or `tests/`; the formal project contains only config/state/run_log; the existing destination audit is read-only evidence; bridge/controller are separate GUI-observation projects with no backup-state integration.
- Reviewer runtime/model: Codex desktop review context

## OWNER_VERDICT
[DECIDED] The plan has the right goal: safely classify one exact 57-image existing destination, preserve files/formal state, refuse ambiguous dispatch, and prove a reusable process before any new GUI side effect. Revision 3 genuinely fixes the prior product-boundary assertion, absolute verify command, truthful `E2E_REQUIRED: NO`, controlled ellipsis gate, axis direction for registry-only failures, tri-state `禎`/`楨` handling, and the canonical Status Contract v2 field lists.

It is not ready for Handoff. The remaining gaps are material because Stage 04 could still implement a self-consistent but non-reproducible transaction CLI, or a verifier/status suite that passes ambiguous expectations. Essential work is the real product CLI contract, deterministic per-case process/oracle protocol, exhaustive v2 routing fixtures, and ledger/budget provenance. Supporting bridge readiness remains correctly non-gating; production Save-All remains a separate later gate.

## GOAL_BASELINE
- PRIMARY_OUTCOME: safely establish whether the existing destination is a valid backup of `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17` / 57 images; otherwise stop without ambiguous or duplicate production side effects.
- SUCCESS_EVIDENCE: exact source correspondence; read-only filesystem and state/registry/intent/writer reconciliation; real restart/fault/race evidence through the operator process boundary; a separately classified current-runtime Save-All route; no prohibited GUI/formal-state mutation.
- MUST_NOT_BREAK: existing files and formal state remain read-only in this wave; `禎` and `楨` are not merged silently; UNKNOWN dispatch remains a barrier; no self-authenticating fixture oracle; no unbounded GUI input or production download.
- CRITICAL_PATH: offline verifier and transaction evidence first, then identity reconciliation, then at most one explicitly authorized ellipsis observation if still necessary; production route only in a later reviewed plan.

## GOAL_ALIGNMENT
[VERIFIED] Revision 3 remains aligned with the primary outcome. It does not treat valid-looking files, historical PASS labels, bridge readiness, or an absent external producer as source proof. The existing 57-file observation is correctly treated as filesystem-only support.

[VERIFIED] The plan's CORE/SUPPORTING split and non-gating bridge decision are proportionate. The exact-source and uncertain-dispatch stops have a correctness rationale; no supporting bridge dependency is allowed to veto offline work.

## NECESSITY_AND_TRACEABILITY
[VERIFIED] The new verifier, source tri-state, guarded transaction, independent acceptance, and bounded route decision each trace to the requested acceptance or a stated data/safety invariant. The package is explicitly declared the task's reusable product boundary rather than an alleged existing producer.

[MINOR] The current root `handoff.md` is visibly a non-Stage-03 handoff for an older Rev34 task/plan, while this plan is Rev3. Plan § “Closure and sequencing” says Stage 03 will use the approved hash, which is the correct safeguard, but the next handoff should explicitly mark the current root handoff as non-authoritative and carry the Rev3 hash/task identity.

## GATE_AND_VETO_AUDIT
[VERIFIED] Filesystem/source/state/dispatch integrity gates are justified independently of schema completeness. Bridge readiness is `SUPPORTING / DIAGNOSTIC / NON_GATING`, with no unsupported global veto.

[VERIFIED] The GUI gate now names the exact app/bundle, raw target, album/count, surface, one ellipsis input, prohibited actions, immediate post-evidence, and separate later production authorization. `E2E_REQUIRED: NO` is truthful for this wave.

[MAJOR] The plan cites only the historical `actions.jsonl` as “ledger authority” but derives `ellipsis_clicks_used=2` and `ellipsis_click_budget=2` from the separate `environment.json` in the supplied evidence tree. The action ledger itself records the two clicks but not those budget fields. The plan also does not define how navigation/app-acquisition inputs are counted in a new run-specific ledger. A later gate could therefore report a budget from a non-authoritative artifact or permit unaccounted inputs.

## COUPLING_AND_FAILURE_CONTAINMENT
[SUPPORTED] The intended isolation is sound: formal data root and destination are read-only, tests use `/private/tmp`, the dispatcher is injected only at the side-effect seam, and bridge/service is outside the backup-state path.

[MAJOR] The plan says “same-directory exclusive guard” and “shared compare-and-commit” but does not identify the guard path/primitive or the exact admission/commit protocol shared by acquire, resume, commit/finalize, duplicate skip, and cleanup. The current state contract expressly says read/check/write or atomic rename alone is insufficient.

## DESIGN_ECONOMY
[SUPPORTED] The proposed scope is economical if the package is genuinely the reusable local product: no schema migration, distributed exactly-once protocol, bridge repair, or production download is added. No implementation evidence is required at this review stage, and none is claimed.

[MAJOR] Without a concrete CLI/state contract, the new package can still become a second acceptance-local model despite the stated product-boundary decision. The deletion test is only satisfied once every tested operation has an operator-invocable path and the injected fake is demonstrably limited to the final side-effect adapter.

## CRITICAL_PATH_AND_PRIORITY
[VERIFIED] The order is correct: baseline false-positive reproduction, package boundary, fail-closed verifier, transaction process, offline acceptance, identity reconciliation, then optional observation. Existing valid files are not redownloaded.

[VERIFIED] The plan separates this wave's offline/observation closure from any later production route. An unresolved source is correctly allowed to leave the primary outcome UNKNOWN rather than forcing a false DONE.

## REQUIREMENT_FIDELITY
[VERIFIED] The raw target is exact in the plan: `line:jp.naver.line.mac:旻謙允禎成長日記`, album `2024/05/13～05/17`, expected 57, with persisted `楨` kept distinct. The plan correctly preserves a user-fact evidence path without rewriting config/state.

[MAJOR] The verifier matrix is not fully deterministic despite its corrected axis orientation. § “Axis-correct verifier fixture matrix” still contains alternative expected results: “1 or 4” for special/unreadable/file-command cases, “EXACT or LEGACY” for wrong-group state, and “UNKNOWN/BLOCKED” for legacy overall status. It also does not give a per-row exact artifact/read-back result. These are contract choices, not implementation details.

## GROUNDING_AND_DRIFT
[VERIFIED] The formal state currently parses as schema 2, revision 39, with four verified entries and five runs; the target registry entry and destination use the persisted `楨` key. The target run has null observed title/title confidence UNKNOWN and no contract revision, while another run has legacy `TRIGGER_UNKNOWN`/`SAVE_ALL_RETURNED` fields. This supports the plan's legacy/provenance stop rule, not exact source proof.

[VERIFIED] The current destination audit reports 57 regular recognized JPEGs, 17,924,900 bytes, three stable samples, and no listed anomalies. The old 56/58 reproductions and self-authenticating recovery fixture remain historical evidence only.

[VERIFIED] The bridge README states it has no Backup Skill integration or backup-state path. The controller exposes read-only observation/navigation contracts and explicitly does not perform Save-All; source/static tests cannot prove current live menu capability. No current GUI observation or production action was performed.

## ARCHITECTURE_AND_CONTRACTS

### RV3-001 — MAJOR — ARCHITECTURE / TEST / GROUNDING
**Affected:** plan §§ “Authoritative roots and product boundary”, “Packaging/build contract”, and “Transaction product contract and executable acceptance matrix” (lines 69–91, 177–213).

**Evidence:** [VERIFIED] The planned package is not present yet, and the formal project has no verifier, transaction library, producer, or consumer. Revision 3 improves this by declaring the task package the operator product and giving an absolute `verify-only` command plus one absolute `transaction resume` command. It still does not specify the input JSON/state fixture schema, the CLI grammar for `commit`/finalization/duplicate handling, or concrete commands and adapter flags for the storage-fault, read-back, stale-writer, and competing-writer cases.

**Failure/rework mechanism:** Stage 04 can satisfy the one shown command with a self-consistent implementation while tests invoke helper-only paths or a different in-memory transition model. Independent acceptance then cannot establish that resume, commit, duplicate gating, and finalization are the same operator process.

**Smallest required correction:** Define the exact operator CLI grammar and state-fixture schema before Handoff. Provide one reproducible command per matrix case, including resume, commit/finalize, terminal duplicate, injected dispatcher, storage fault, read-back uncertainty, process pause/termination, and deterministic race barrier. State explicitly that tests may inject only the final dispatcher/storage adapters and that every transition under test is reached through the same CLI/library call graph. Keep any future LINE producer integration explicitly unproven and outside this revision.

### RV3-002 — MAJOR — TEST / SEMANTIC_CONTRACT / DATA
**Affected:** plan §§ “Product verifier oracle and failure containment” and “Axis-correct verifier fixture matrix” (lines 143–175).

**Evidence:** [VERIFIED] The table includes non-singleton outcomes: `1 or 4`, `EXACT or LEGACY`, and `UNKNOWN/BLOCKED`. The plan requires independent axis checks but does not make these row expectations exact for `filesystem`, `registry`, `source`, `state`, `overall`, exit, and manifest read-back.

**Failure/rework mechanism:** A verifier can choose whichever branch its implementation happens to produce and still be considered compliant. Internal I/O errors can be confused with safely rejected negative inputs; legacy state can be normalized inconsistently; and a broken artifact writer can be hidden behind a nominal status.

**Smallest required correction:** Split each alternative into a separate case or choose one deterministic classification. For every case specify exact axis values, exact exit code, whether downstream axes are `NOT_RUN` or independently evaluated, required artifact names, manifest/read-back result, and failure class. In particular separate malformed/unsafe input (safe rejection) from internal/read/command/artifact errors, and separate exact wrong-group state from legacy-provenance state.

### RV3-003 — MAJOR — RELIABILITY / TEST / SEMANTIC_CONTRACT
**Affected:** plan §§ “Transaction product contract” and “Concrete subprocess test protocol” (lines 181–213).

**Evidence:** [VERIFIED] The plan names the required invariants—revision/owner/run/terminal/intent checks, atomic replacement, fsync/read-back, stale-writer rejection, deterministic contention, separate storage injection—but gives no guard path/primitive, pause/resume barrier protocol, exact fault flags, or durable read-back recovery sequence. “Crash after side effect before persistence” and “read-back uncertainty” are described as cases, not executable boundaries.

**Failure/rework mechanism:** A timing-based two-process test can pass without proving serialization. A process killed after the dispatcher counter increments could be incorrectly treated as `NOT_ATTEMPTED` if the product/test fixture lacks a named action-boundary protocol. A replacement followed by failed read-back can leave the implementation unable to state whether the original barrier, new revision, or terminal claim is authoritative; retry behavior would then be guesswork.

**Smallest required correction:** Specify one shared guard path and supported serialization mechanism, the exact lock hold interval, atomic temp/replacement and read-back steps, and the conditional commit predicate. Add deterministic named barriers/events for B-wins/A-stale, dispatcher-side-effect-before-persist, storage-write failure, and post-replace read-back failure. Give exact subprocess commands and independent pre/post state/counter byte/revision/axis/owner/terminal oracles, including the reload/no-retry rule after read-back uncertainty.

### RV3-004 — MAJOR — SEMANTIC_CONTRACT / TEST
**Affected:** plan §§ “Canonical status and blocker contract” and “Closure and sequencing” (lines 242–297).

**Evidence:** [VERIFIED] Revision 3 now lists the canonical six Status Contract v2 enum sets, per-check metadata, scoped blockers, waiver authority, and DONE prerequisites. It does not provide an explicit fixture matrix for all review-required branches: canonical incident, true `IMPLEMENTATION_STATUS: BLOCKED`, `CORE_ACCEPTANCE_STATUS: NOT_REQUIRED` with rationale, CORE `BLOCKED` and `NOT_RUN`, `ESCALATED`/`REPLAN_REQUIRED`, baseline unavailable versus baseline-delta, hard-clean pre-existing debt, formal waiver preserving the original check result, and the Stage-05 immutable Stage-04 snapshot fields.

**Failure/rework mechanism:** Stage 04/05 can emit legal-looking fields yet leave routing ambiguity for implementation blockage versus acceptance blockage, baseline absence versus regression, waiver versus PASS, or a Stage-05 environment blocker. That can produce an illegal or premature DONE state and does not satisfy the active review gate's explicit-fixture requirement.

**Smallest required correction:** Add a status-routing fixture table with exact input state, six orthogonal outputs, scoped blocker, baseline/failure classification, waiver metadata, and expected closure for every named branch. Require Stage 05 to snapshot `STAGE_04_REPORTED_IMPLEMENTATION_STATUS`, `STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS`, `STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS`, and `STAGE_04_EXECUTION_ARTIFACT_SHA256` before computing current acceptance. Include contradictory-state rejection and legacy normalization as explicit cases.

### RV3-005 — MAJOR — GROUNDING / SCOPE / TEST
**Affected:** plan §§ “Runtime route, GUI gate, and truthful E2E decision” (lines 215–240).

**Evidence:** [VERIFIED] The referenced historical `actions.jsonl` exists and contains two ellipsis input events, no Save-All/menu-item click, and no backup-state write. The supplied evidence also contains the budget-bearing `environment.json` with `ellipsis_clicks_used: 2` and `ellipsis_click_budget: 2`; that authority is not named in Rev3. The plan has no explicit route-result artifact fields tying documented runtime capability, fresh target binding, post-observation, ownership/role/text/bounds, and action counters to the new run ledger.

**Failure/rework mechanism:** A later reviewer cannot verify the claimed 2/2 budget from the cited ledger alone, cannot tell whether navigation inputs were within scope, and could accept a fresh observation whose target or provider is not bound to the exact raw target. This risks either an unauthorized third ellipsis input or an unsupported route conclusion.

**Smallest required correction:** Name and hash the authoritative historical scope/budget artifact(s), including `environment.json` (and the referenced scope artifact if used), and record the exact 2/2 consumed budget as a precondition. Define the new run-specific ledger schema and accounting for all permitted navigation and exactly one target ellipsis input. Define the route result schema with documented-capability reference, runtime/provider identity, raw target/bundle/album/count, fresh pre/post evidence, exact menu candidate correlation, counters, and `ROUTE_STATUS`/`SAFE_ABORT` outcome. Preserve production Save-All as a separate Revision 4 gate.

## DATA_SECURITY_RELIABILITY
[VERIFIED] The plan retains read-only formal state and destination constraints, rejects symlinks/unsafe entries, requires content-based MIME and hash/read errors to fail closed, and disallows AXPress, AX writes, OCR-only acceptance, guessed coordinates, and retries after uncertainty.

[SUPPORTED] The `禎`/`楨` handling is safe: raw strings/keys remain separate, `CONFIRMED` requires an exact join or an explicitly recorded user fact, legacy provenance cannot authorize dispatch, and the default remains `UNRESOLVED`.

## IMPLEMENTATION_SEQUENCE
[SUPPORTED] The sequence is materially improved and should remain offline-first. After the corrections above, Stage 03 can compile only the approved Rev3/hash, then Stage 04 can implement the product package. The absent source package is not itself a review failure; it is correctly planned for creation after approval.

## TESTABILITY_AND_ACCEPTANCE
[MAJOR] The plan correctly rejects the old self-authenticating recovery fixture and requires subprocess tests, but “real subprocess” is not enough without exact command/fixture/barrier definitions (RV3-001 and RV3-003). The current bridge/controller fixture PASS evidence remains historical and cannot substitute for the future product or live route.

## SCOPE_AND_COMPLEXITY
[SUPPORTED] The design remains within the requested one-album acceptance scope. The additional package is justified only as the explicit reusable product boundary; the plan should not add a second external producer or bridge integration in this revision.

## FINDINGS
- RV3-001 — MAJOR — product boundary is declared but not executable as a complete operator/test CLI contract.
- RV3-002 — MAJOR — verifier cases still allow alternative statuses/exits and lack exact per-case artifact oracles.
- RV3-003 — MAJOR — compare-and-commit, crash, fault, race, and read-back processes are named but not concretely runnable.
- RV3-004 — MAJOR — canonical v2 fields are listed, but required exhaustive routing fixtures and Stage-04 snapshot requirements are not explicit.
- RV3-005 — MAJOR — ledger/budget authority and route evidence schema are incomplete; the cited actions ledger does not itself contain the claimed budget fields.
- Handoff freshness — MINOR — current root `handoff.md` is older/non-authoritative; next Stage 03 handoff must bind the approved Rev3 identity/hash.

## REQUIRED_PLAN_CHANGES
1. Add the exact product CLI grammar, state fixture schema, call graph, and one concrete command per verifier/transaction/status case; preserve the future external producer as unproven and out of scope.
2. Make every verifier case deterministic: exact five-axis statuses, exact exit, exact failure class, and exact artifact/read-back expectations; split all current alternatives.
3. Specify the shared guard path/serialization and deterministic barriers/fault injectors, with independent state/counter byte/revision/axis/owner/terminal oracles and a defined read-back uncertainty reload/no-retry path.
4. Add the exhaustive Status Contract v2 fixture/routing table, including canonical incident, implementation blocker, CORE not-required/blocked/not-run, replan/escalation, baseline cases, hard-clean debt, authorized waiver preservation, legacy/contradictory cases, and immutable Stage-04 snapshot fields for Stage 05.
5. Name the authoritative historical budget artifact (`environment.json` plus any scope artifact used), bind its 2/2 ledger precondition, define all new-run input accounting, and specify a route-result evidence schema separating documented capability from fresh observation.
6. Increment the same TASK_ID from Revision 3 to Revision 4 only after these dependent sections are corrected, then submit Revision 4 to a fresh independent review. Do not create/update Stage 03 Handoff before approval.

## RESIDUAL_MINOR_NOTES
- [VERIFIED] Existing destination evidence supports only current filesystem completeness: it does not prove exact LINE source identity, original capture provenance, uniqueness, or full image decode/quality.
- [VERIFIED] Current formal state is readable and internally populated, but the target persisted key is `楨`, the requested key is `禎`, and the target run lacks authoritative title/provenance. Exact source acceptance therefore remains unresolved by current evidence.
- [VERIFIED] The bridge/controller source and historical fixture artifacts support read-only observation-contract claims only; they do not prove a live current Save-All route or a reusable backup transaction engine.
- No implementation, deployment, GUI observation, production download, formal-state mutation, or acceptance was performed by this review.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revision mode on T20260916-0102-01-line-backup-acceptance; correct RV3-001 through RV3-005, preserve the tri-state source stop rule, increment to Revision 4, then rerun Stage 02 independently.
