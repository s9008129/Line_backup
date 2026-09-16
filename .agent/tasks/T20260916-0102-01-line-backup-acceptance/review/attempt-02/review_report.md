# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 02
- REVIEWED_PLAN_REVISION: 2
- REVIEWED_PLAN_SHA256: 6eb4a23631a567f2355316796f8d7800c4fa3eea1bf3f885bae41a5d6d483be1
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-02/plan_snapshot.md
- Repository anchor observed: WORK contains the candidate plan, handoffs, and evidence; `src/` and `tests/` are absent. The selected formal project contains only config/state/run_log. The bridge README explicitly says it has no Backup Skill integration or backup-state path.
- Reviewer runtime/model: Codex desktop review context

## OWNER_VERDICT
[DECIDED] The plan is correctly centered on safely accepting or stopping for one exact 57-image album, preserving existing files/formal state, and refusing ambiguous Save-All dispatch. The current evidence independently supports only a filesystem observation (57 regular files, 17,924,900 bytes); it does not resolve the requested `禎` identity against the persisted `楨` identity, prove a current Save-All route, or prove a real resumable transaction implementation.

Revision 2 materially improves the prior plan: `E2E_REQUIRED: NO` is truthful for a wave that neither authorizes nor needs a production download, the `禎`/`楨` result is tri-state with a stop rule, and the verifier/transaction cases are much more concrete. It is not ready for Handoff because the proposed product ownership/process boundary is asserted but not grounded, the named CLI commands are not yet fully executable, the verifier matrix confuses filesystem and registry outcomes, and the status/closure section is not the canonical Status Contract v2 and omits per-check waiver/baseline metadata.

Essential: exact source correspondence, read-only file/state evidence, and real shared resume/commit/duplicate behavior. Supporting: bridge/service readiness. Deferred: production Save-All/download, bridge repair, migration, and broad cleanup. Global stops are justified for unresolved source identity, uncertain/attempted dispatch, unsafe state/destination, and missing independent evidence. The largest risk remains that a future module and its tests could pass against an injected fake without proving the production resume/dispatch/commit path.

## GOAL_BASELINE
- PRIMARY_OUTCOME: safely establish whether the existing destination is a valid backup of the exact LINE bundle/group/album requested: `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17` / 57 images; otherwise stop without ambiguous or duplicate production side effects.
- SUCCESS_EVIDENCE: independent filesystem inventory and hashes; exact source/registry/state association; real restart/recovery/duplicate/commit evidence; a separately classified current runtime route decision; no unsafe GUI or formal-state mutation.
- MUST_NOT_BREAK: existing 57 files and formal state remain read-only in this wave; unknown dispatch remains a permanent barrier; no spelling merge or inferred root; no self-authenticating test oracle.
- CORE: source correspondence, filesystem/state integrity, real transaction safety, and the necessary route/stop decision.
- SUPPORTING: bridge/service diagnosis only when a selected route proves it necessary.
- BEST_EFFORT/NON_GOAL: bridge repair without causal proof, historical cleanup, OCR, migration, distributed exactly-once semantics, and unrequested production download.
- CRITICAL_PATH: offline verifier/transaction evidence first; exact identity reconciliation; only then a precisely bounded observation gate if still necessary; production route only under a later separately reviewed plan/gate.

## GOAL_ALIGNMENT
[VERIFIED] The plan preserves the primary outcome and correctly prioritizes verify-only before any new side effect. It correctly prevents file hashes, historical GUI evidence, bridge readiness, or old PASS labels from proving source identity or current Save-All capability.

[MAJOR GAP] The plan makes the future transaction module a CORE acceptance dependency but does not yet establish whether it is a product component consumed by any real backup process or merely a new implementation placed beside the evidence. This affects whether the planned acceptance evidence can prove the user's reusable transaction goal.

## NECESSITY_AND_TRACEABILITY
[VERIFIED] Verifier hardening, source tri-state, legacy normalization, compare-and-commit, and independent acceptance each trace to a concrete user outcome or must-not-break invariant. The non-gating bridge classification is economical.

[MAJOR GAP] The deletion test for the new implementation surface is incomplete: removing the proposed module would leave no existing product resume/dispatch/commit path to test, but the plan does not identify a product owner/consumer or an integration contract. Directory placement and use of a Python CLI are not, by themselves, product ownership.

## GATE_AND_VETO_AUDIT
[VERIFIED] Blocking unresolved/contradicted source identity, unsafe destination, unknown dispatch, state conflict, and failed read-back is proportionate to decision validity/data safety. Bridge readiness is explicitly non-gating.

[MAJOR GAP] The observation gate is described as a “fresh, read-only CUA session” while allowing an ellipsis click; that is reversible GUI input, not observation-only in the strict sense. The plan does not name the existing ledger artifact/allowance or give the exact bundle, raw group string, album, count, observation surface, and input budget in the gate itself. A future production gate is separated conceptually but not separated in the closure model.

## COUPLING_AND_FAILURE_CONTAINMENT
[SUPPORTED] The proposed fake dispatcher seam, isolated state, no production-state writes, and shared serialized compare-and-commit are the right containment direction. The bridge remains outside the formal backup-state path.

[MAJOR GAP] The plan names the compare-and-commit invariant but not the concrete shared lock/conditional-commit boundary, lock path, stale-payload check, or deterministic race schedule. Atomic replacement plus a post-write read-back cannot fence a delayed writer without the shared serialization rule actually used by acquisition, resume, finalize, and cleanup.

## DESIGN_ECONOMY
[SUPPORTED] No distributed exactly-once protocol, schema migration, bridge reinstall, or broad refactor is proposed. The verifier and transaction scope is plausibly minimal if it is genuinely product-owned and uses the existing state schema.

[MAJOR GAP] If the module is only an acceptance-local harness, it adds a second transaction implementation and can create false confidence. The plan must either make it the real reusable product boundary or narrow the claim and acceptance target accordingly.

## CRITICAL_PATH_AND_PRIORITY
[VERIFIED] Offline verification and identity reconciliation precede any GUI gate. Existing valid files are not redownloaded. The plan correctly treats bridge work as conditional.

[MINOR GAP] The plan's final DONE sentence requires no unresolved production-route blocker even though production dispatch is explicitly deferred to Revision 3 and E2E is intentionally NO. It needs an explicit distinction between “this wave reaches a valid stop/acceptance result” and “the later production route is ready.”

## REQUIREMENT_FIDELITY
[SUPPORTED] The plan captures the one-album/57-image scope, no-redownload rule, exact spelling distinction, state/registry separation, at-most-once barrier, and independent acceptance requirement.

[MAJOR GAP] The verifier fixture table does not preserve requirement-axis semantics: wrong-group and cross-entry registry cases are listed with an expected filesystem FAIL even though the filesystem can remain PASS and only registry/source/overall acceptance should fail.

## GROUNDING_AND_DRIFT
[VERIFIED] Current config uses `line:jp.naver.line.mac:旻謙允楨成長日記`; the user goal uses `禎`. Current state is revision 39 with null current run/writer/context lock. The target 57-image registry record points to the existing destination but has no `contract_revision`; its associated run has `observed_title: null`, `title_confidence: UNKNOWN`, and legacy formula-derived calibration. The real destination read-only summary is 57 regular files and 17,924,900 bytes. The old verifier accepted stable 56 and 58 fixtures with exit 0 and `FILESYSTEM_VERIFICATION=PASS`.

[VERIFIED] The current bridge README says it has no Backup Skill integration or backup-state path; the controller/package is a GUI observation/navigation surface. Installed daemon evidence is stale/failed-looking and cannot be treated as current Save-All proof.

[MAJOR GAP] The plan's `VERIFY_COMMAND` contains unresolved symbolic arguments (`DATA_DESTINATION`, `TARGET_GROUP_KEY`, `EVIDENCE_DIR`) and gives no explicit working directory/packaging contract. The TEST_COMMAND is likewise only executable from an assumed cwd. This is insufficiently grounded for a later independent verifier to demonstrate the named process boundary.

## ARCHITECTURE_AND_CONTRACTS
[VERIFIED] The source/legacy contract in the plan is substantially corrected: `CONFIRMED`, `UNRESOLVED`, and `CONTRADICTED` are distinct; `LEGACY_PROVENANCE_LIMITED` cannot satisfy exact source acceptance; no automatic `禎`/`楨` merge is allowed; and state axes remain separate.

[MAJOR GAP] No existing implementation currently owns the planned `resume`, `dispatch`, `commit), and duplicate-gate operations. The plan must define the production-facing adapter and prove the fake is injected only at the side-effect seam, not that the entire transaction path is fake-controlled.

## DATA_SECURITY_RELIABILITY
[SUPPORTED] The proposed verifier oracle covers real-path containment, symlink/non-regular/hidden/temp rejection, content-based MIME, read/hash errors, complete metadata-bearing stable inventories, arbitrary filenames, and evidence manifests. It preserves the current destination as read-only.

[MAJOR GAP] The verifier negative matrix lacks axis-correct expected outputs and an executable mechanism for between-sample mutation/race cases. It must assert filesystem, registry, source, state, overall, exit code, and artifact read-back independently; otherwise a broken verifier can satisfy an incorrectly labeled test.

## IMPLEMENTATION_SEQUENCE
[SUPPORTED] The intended sequence—new product verifier, transaction process, isolated cases, real-destination verify-only, identity reconciliation, then optional observation—is sound.

[MAJOR GAP] Stage 04 cannot start from the current plan without resolving the product-boundary decision. The plan should define the exact subprocess commands, input fixture schema, dispatcher/storage fault injection points, and process restart/crash mechanism before Handoff.

## TESTABILITY_AND_ACCEPTANCE
[VERIFIED] `E2E_REQUIRED: NO` is truthful for this wave: the existing destination is the primary object, production download is not authorized, and the C04 controller is observation-only. The plan explicitly says observation-only is not production E2E and Stage 05 still independently accepts the real CLI/evidence.

[MAJOR GAP] The transaction cases are named but not yet an executable acceptance matrix. There is no per-case command, precondition, injected failure boundary, expected durable bytes/revision, counter, owner/run result, or exact status routing. “transaction ...” cannot establish that restart calls the same resume/commit path.

[MAJOR GAP] The status section is not canonical Status Contract v2. It uses `PRIMARY_OUTCOME_STATUS: PASS/FAIL/BLOCKED` instead of `ACHIEVED/NOT_ACHIEVED/UNKNOWN`; `IMPLEMENTATION_STATUS: REPLAN_REQUIRED` instead of `ESCALATED`; omits `INCOMPLETE/WAIVED` required-verification states and the canonical closure states; and provides no per-check `BASELINE_REQUIRED`, `FAILURE_CLASSIFICATION_RULE`, `WAIVER_ALLOWED`, `WAIVER_AUTHORITY`, or `WAIVER_STATUS`. The sentence “No agent may self-waive” is not a substitute for plan-time waiver authority.

## SCOPE_AND_COMPLEXITY
[SUPPORTED] The plan avoids scope growth into bridge repair, schema migration, or production download. The complexity budget is acceptable only if the new module is the actual reusable product boundary and not a test-only replica.

## FINDINGS

### RV2-001 — MAJOR — ARCHITECTURE / GROUNDING / TEST
**Affected:** plan lines 54–64, 69–73, 144–168; “Authoritative roots and implementation surface” and “Transaction contract and actual process tests”.

**Evidence:** [VERIFIED] The selected formal project has only `config/line_backup_config.json`, `state/backup_state.json`, and `state/run_log.md`; WORK has no `src/` or `tests/`; bridge README states “no Backup Skill integration and no backup-state path”; the controller is a GUI observation/navigation executable. The plan therefore introduces a future Python module but does not identify a product owner, production consumer, package/build contract, or a real existing resume/dispatch/commit path. The fake dispatcher is the only explicitly executable side-effect boundary.

**Failure/rework mechanism:** A new module in the task workspace can implement a self-consistent model that subprocess tests call successfully while the real backup path, if later created, uses different state transitions or dispatch authority. Passing fake-dispatch counters would then not prove the requested reusable production transaction behavior.

**Smallest required correction:** Before Handoff, define either (a) the real product owner/consumer and the exact shared `resume`/`dispatch`/`commit` API/CLI used by both production and tests, with the fake injected only at the final side-effect seam, or (b) an explicit acceptance-only scope and remove the claim that it proves the production process. Resolve every symbolic CLI argument to a concrete invocation rooted at the implementation package. If production integration is deferred, mark it as a separate unproven contract and do not make it a passed CORE claim.

### RV2-002 — MAJOR — SEMANTIC_CONTRACT / TEST
**Affected:** plan lines 175–186, “Status and closure matrix” and all material checks.

**Evidence:** [VERIFIED] Canonical `workflow-routing.md` Status Contract v2 requires independent fields and verification-item metadata. Rev2 instead declares non-canonical values (`PASS/FAIL/BLOCKED` for primary outcome, `REPLAN_REQUIRED` for implementation, and a three-state closure field), omits `INCOMPLETE`/`WAIVED`, and has no per-check waiver authority or baseline policy.

**Failure/rework mechanism:** Stage 04/05 can emit a superficially orthogonal report that is illegal under the active contract, cannot distinguish implementation escalation from acceptance blockage, or silently treat a required check as waived/passed. This directly permits self-waiver or incorrect DONE routing.

**Smallest required correction:** Replace the status section with the canonical v2 enums/routing and add a material-check table for every closure-relevant check containing `CHECK_ID`, `GOAL_CRITICALITY`, `EVIDENCE_ROLE`, `CLOSURE_GATE`, `BASELINE_REQUIRED`, failure classification, waiver allowance/authority, and waiver status. Add scoped blocker fields and executable fixtures for baseline unavailable/delta, hard-clean debt, formal waiver preserving the original result, legacy normalization, contradictory state, independent acceptance pending/blocked/product defect, and every DONE prerequisite. Agents must never approve their own waiver.

### RV2-003 — MAJOR — TEST / DATA
**Affected:** plan lines 119–140, “Verifier negative fixture matrix”.

**Evidence:** [VERIFIED] The rows “Wrong group_key with same fingerprint/destination” and “Cross-entry group/fingerprint/destination mix” expect a filesystem FAIL, although the directory can be filesystem-valid and the registry/source/overall axis is what fails. The mtime/bytes-change case has no deterministic mutator or synchronization contract. The plan also leaves no per-case exit/status/artifact oracle.

**Failure/rework mechanism:** An implementation can conflate unrelated filesystem and registry failures, making a valid file inventory look corrupt or allowing a registry association defect to be reported as a filesystem result. A race case can be skipped or pass by timing accident.

**Smallest required correction:** For each fixture specify independent `filesystem_status`, `registry_status`, `source_status`, `state_status`, `overall_status`, exit code, and required evidence files. Expected registry-only defects should retain filesystem PASS while overall acceptance fails. Provide a deterministic fixture mutator/barrier for mtime/bytes changes and preserve both pre/post inventories.

### RV2-004 — MAJOR — RELIABILITY / TEST
**Affected:** plan lines 144–168, “Transaction contract and actual process tests”.

**Evidence:** [VERIFIED] The plan names compare-and-commit, atomic replacement, restart, fault, and race cases, but `TRANSACTION_COMMAND` is only `transaction ...`; it does not define the input state schema, process subcommands, restart/crash boundary, lock/guard path, or per-case durable oracle. The current state contract requires a shared serialized commit boundary for acquisition, mutation, finalization, and cleanup; atomic replacement/read-back alone is insufficient.

**Failure/rework mechanism:** Tests may construct a state file, invoke a helper, and assert a counter/state that the helper itself wrote, without proving the actual resume path preserves an unknown barrier or rejects a stale delayed writer. Competing-writer outcomes can also be nondeterministic.

**Smallest required correction:** Define a concrete CLI/library call graph and fixture protocol: fresh prepare → real subprocess resume/dispatch → injected crash/write/read-back fault → fresh subprocess resume/commit; identify the shared exclusive guard/conditional revision+owner check; add deterministic synchronization for competing writers. For every case assert independently observed dispatch count, exact pre/post state bytes/revision, intent/dispatch/trigger axes, registry, owner release, terminal outcome, and no retry permission. Include a separate storage fault injector; the fake dispatcher alone cannot inject all persistence failures.

### RV2-005 — MAJOR — SCOPE / SEMANTIC_CONTRACT / SEQUENCING
**Affected:** plan lines 84, 169–186 and “Runtime and E2E decision”.

**Evidence:** [SUPPORTED] `E2E_REQUIRED: NO` is correct for an existing-destination acceptance wave with no authorized production download. [VERIFIED] Rev2 nevertheless marks “Actual Save-All route” CORE/HARD_CLEAN, describes a future observation-only session with an ellipsis click, and makes DONE contingent on no unresolved production-route blocker, while the production route is explicitly deferred to Revision 3. No current ledger path or exact observation authorization is named.

**Failure/rework mechanism:** Stage 05 could either mislabeled observation evidence as production E2E or hold this wave open for an unauthorized future transaction. A “read-only” label could also obscure that an ellipsis click is GUI input, and an unscoped human gate could permit more interaction than intended.

**Smallest required correction:** Keep `E2E_REQUIRED: NO), but separate (1) independent acceptance of the real offline CLI, (2) a precisely bounded observation-only/diagnostic route decision, and (3) any later production Save-All gate. Define the current wave’s legal closure when route evidence is unavailable (for example, scoped `INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED` / `TASK_CLOSURE_STATUS: ACCEPTANCE_BLOCKED`, not DONE). The human gate must name the exact app/bundle, raw group string `禎`, album/date/count 57, surface, existing ledger artifact and remaining budget, exactly one permitted ellipsis click, no Save-All/menu-item/chooser/state write, and immediate post-evidence; production dispatch requires Revision 3 review and a separate gate.

### RV2-006 — MINOR — DATA / GROUNDING
**Affected:** plan lines 90–103, “Source and state outcome contract”.

**Evidence:** [VERIFIED] Current config/registry use `楨`; the user request uses `禎`; the target run has no `contract_revision`, null observed title, UNKNOWN title confidence, and legacy formula-derived calibration. Rev2 correctly says this is not exact source proof and defines `UNRESOLVED`/`LEGACY_PROVENANCE_LIMITED`.

**Residual risk:** The plan does not prescribe the immutable evidence form/authority for the exceptional “one precise user fact” path, so a later verifier could record the fact inconsistently or treat a user confirmation as a silent state migration.

**Smallest correction:** Define an evidence-only record containing both raw strings, who/when supplied the fact, exact question/answer, and the unchanged legacy key/run/registry fields. The default result on current evidence must remain `SOURCE_CORRESPONDENCE=UNRESOLVED` plus `LEGACY_PROVENANCE_LIMITED`, with overall acceptance stopped.

## REQUIRED_PLAN_CHANGES
1. Resolve RV2-001 before Handoff: establish genuine product ownership and the shared real process boundary, or explicitly narrow the claim to an acceptance-only implementation. Make VERIFY/TRANSACTION commands concrete and reproducible.
2. Replace Rev2’s status section with canonical Status Contract v2, including orthogonal enums, scoped blocker routing, per-check baseline/waiver metadata, non-self-waivable authority, and executable closure fixtures.
3. Correct RV2-003’s verifier matrix so filesystem, registry, source, state, and overall outcomes are independent; add deterministic mutation/race fixtures and exact exit/artifact oracles.
4. Turn RV2-004 into a runnable transaction acceptance matrix with concrete subprocess/restart/crash commands, shared compare-and-commit guard, deterministic contention, independent counter/state oracles, and read-back uncertainty containment.
5. Clarify RV2-005: retain truthful `E2E_REQUIRED: NO`, but define independent CLI acceptance, observation-only route status, and later production Save-All authorization/closure separately; specify the exact human gate and current legal blocked closure.
6. Preserve the corrected `禎`/`楨` tri-state/legacy stop rule and add immutable provenance for any exceptional user-fact confirmation.
7. Increment the same TASK_ID revision by exactly one, preserve unaffected decisions, and submit the new revision to a fresh independent Stage 02 review. Do not create/update Stage 03 Handoff before approval.

## RESIDUAL_MINOR_NOTES
- The current 57-file destination observation is [VERIFIED] as a filesystem snapshot only: three historical/current sample sets report 57 JPEG/image entries and 17,924,900 bytes; this does not prove original source, uniqueness, full decode, or resolution fidelity.
- The old 56/58 false-positive evidence is [VERIFIED] as a reproduction of the old script’s false acceptance, not evidence about the future product verifier.
- Historical target state/run evidence is [VERIFIED] as legacy provenance, not current Save-All authorization. The formula-derived Save-All calibration and historical title cannot be reused.
- The current bridge/controller evidence supports observation-only capability claims and explicitly lacks backup-state integration; it is not transaction acceptance evidence.
- No implementation, deployment, GUI observation, production download, formal-state mutation, or acceptance was performed by this review.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revision mode on T20260916-0102-01-line-backup-acceptance; address RV2-001 through RV2-005, preserve the source/legacy stop rule, increment PLAN_REVISION to 3, then rerun Stage 02 independently.

