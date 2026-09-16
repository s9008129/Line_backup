# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 01
- REVIEWED_PLAN_REVISION: 1
- REVIEWED_PLAN_SHA256: 6ba2760abf026010131e244da59859a268ff1f948704d52d7bc6d2511f5f7db3
- PLAN_SNAPSHOT_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-01/plan_snapshot.md
- Repository anchor observed: WORK contains only the candidate task/evidence; formal project contains config/state/run_log; bridge/controller are separate repositories and explicitly have no Backup Skill/state integration.
- Reviewer runtime/model: Codex desktop review context

## OWNER_VERDICT
The goal is correctly centered on safe verification of the existing 57 files, exact source identity, and non-repeatable side effects. The plan is not ready for Handoff because it does not identify an actual product transaction implementation or a true Stage-05 E2E path, and it leaves the `禎`/`楨` acceptance result under-specified. The current evidence supports filesystem verification only; historical PASS labels do not prove source correspondence or current Save-All capability.

## GOAL_BASELINE
- PRIMARY_OUTCOME: safely accept or stop on the exact LINE group/album and existing 57-file destination, with no duplicate or ambiguous Save-All action.
- CORE: source correspondence, read-only file/inventory integrity, state/registry/intent consistency, real resume/commit/duplicate behavior, and the necessary current runtime route decision.
- SUPPORTING: bridge/service diagnosis only if the selected route proves it necessary.
- BEST_EFFORT/NON_GOAL: spelling merge, broad cleanup, reinstall/TCC work, unrelated bridge refactor, and exactly-once redesign.
- MUST_NOT_BREAK: no production photo/state mutation in this acceptance wave; unknown dispatch remains blocked; formal state and existing photos stay unchanged.

## GOAL_ALIGNMENT
The primary outcome and critical-path ordering are aligned. The plan appropriately prioritizes verify-only and refuses to treat bridge readiness or historical PASS as acceptance evidence.

## NECESSITY_AND_TRACEABILITY
The verifier, identity, transaction-core, and runtime-route requirements trace to the goal. The plan needs explicit deletion/necessity treatment for any new product module because no such module is present in the reviewed WORK/formal-state/bridge/controller surfaces.

## GATE_AND_VETO_AUDIT
The hard gates are proportionate when they protect source identity, destination safety, dispatch ambiguity, or state durability. `BRIDGE_READINESS` is correctly non-gating. The plan must state the exact human-gate subject and permitted inputs for the observation-only route versus the separate production Save-All route.

## COUPLING_AND_FAILURE_CONTAINMENT
The proposed fake dispatcher boundary is a good containment point. It must be paired with a real shared compare-and-commit boundary; atomic replacement plus read-back alone does not satisfy the state contract for contending writers.

## DESIGN_ECONOMY
The proposed scope is minimal in intent. A new transaction core is justified only if it is product-owned and reused by the real resume/dispatch/commit path; a test-only model would add complexity without proving the goal.

## CRITICAL_PATH_AND_PRIORITY
Offline verification and identity reconciliation should precede any GUI gate. No production transaction should use the existing non-empty destination. The plan should make the stop-at-identity-gate outcome explicit.

## REQUIREMENT_FIDELITY
The plan captures the user's no-redownload and at-most-once requirements. It does not yet define whether `E2E_REQUIRED: YES` means a real Save-All/chooser/download journey, or whether an observation-only menu session is being mislabeled as E2E.

## GROUNDING_AND_DRIFT
Verified evidence: the old verifier accepted both stable 56-image and 58-image fixtures with exit 0 and `FILESYSTEM_VERIFICATION=PASS`. The corrected current audit passed the real destination (57 images, 17,924,900 bytes, three stable samples) but is a standalone evidence script, not a registry-aware product verifier. The bridge README states it has no Backup Skill integration or backup-state path. The formal state is revision 39 and legacy for the 57 run (`contract_revision` absent); its legacy calibration is formula-derived and cannot authorize current dispatch. The requested group uses `禎`, while config/state use `楨`; the historical run title is UNKNOWN.

## ARCHITECTURE_AND_CONTRACTS
The formal RC2 contract requires legacy-aware reads, immutable intent axes, a shared serialized compare-and-commit boundary, atomic replacement/read-back, and terminal verification/registry/owner release in one commit. The plan names these concepts but does not name the implementation surface, interfaces, legacy normalization rules, or concurrency/fault-injection mechanism that will enforce them.

## DATA_SECURITY_RELIABILITY
The read-only boundary is correctly stated. The verifier acceptance oracle must explicitly cover real-path containment under configured `backup_root`, root/destination symlink rejection, all required temporary suffixes, hidden metadata, mtime/inventory provenance, unreadable-entry failures, and arbitrary filenames. The current `canonical-audit.py` omits several of these checks, so its PASS is not sufficient.

## IMPLEMENTATION_SEQUENCE
The intended order is sound, but Stage 04 cannot safely start until the product-owned verifier/core path and its executable commands are identified. Stage 05 must run the real path, not only the evidence scripts or controller contracts.

## TESTABILITY_AND_ACCEPTANCE
The existing recovery fixture writes `UNKNOWN` and `retry=false` itself, then checks those same values; it never calls resume, dispatch, commit, restart, or a real writer. The plan correctly recognizes this defect but does not enumerate the required executable cases and oracles. The CRITICAL status contract also requires explicit coverage for contradictory legacy state, implementation blocker, CORE fail/blocked/not-run, replan, baseline unavailable/delta, waiver preservation, independent acceptance pending/blocked, and DONE prerequisites.

## SCOPE_AND_COMPLEXITY
No bridge deployment or formal-state mutation is justified by current evidence. Keep them deferred unless a route-specific experiment proves necessity and a later approved plan authorizes it.

## FINDINGS

### RV-001 — MAJOR — GROUNDING / ARCHITECTURE / TEST
**Affected:** CRITICAL_PATH items 2–3; Minimal design and semantic invariants; TRANSACTION_RESUME_CORE and TRANSACTION_COMMIT_CORE.

The reviewed roots contain no identified Backup Skill verifier or transaction-core implementation. The old recovery fixture is self-authenticating, and the bridge/controller explicitly have no backup-state integration. Without a named product-owned entry point, API, build/test command, and Stage-05 invocation, implementation can become a new test-only model whose passing fake-dispatch tests do not prove real resume/dispatch/commit behavior.

**Required correction:** Name the actual product module/repository and executable entry points, or explicitly add the smallest product-owned implementation as the planned deliverable. Specify the injected dispatcher seam, isolated state format, restart/fault-injection method, and how acceptance invokes the same code used by resume/commit/duplicate paths.

### RV-002 — MAJOR — SEMANTIC_CONTRACT / DATA
**Affected:** Requirement row “State/registry/intent/writer consistency”; Minimal design and semantic invariants; FORMAL_STATE_READONLY_RECONCILIATION.

The formal target run is legacy (`contract_revision` absent), uses `旻謙允楨成長日記`, has `observed_title=null`/`title_confidence=UNKNOWN`, and retains historical formula-derived calibration. The plan says “report legacy provenance limits” but does not define whether this is a hard acceptance failure, a provenance-limited result, or sufficient registry evidence. A verifier could otherwise pass on a fingerprint/destination match while leaving exact source attribution unresolved.

**Required correction:** Define explicit outcomes for legacy/provenance-limited and contradictory records. Overall source/state acceptance must remain blocked unless exact correspondence is proved; preserve all original legacy fields and never make historical calibration dispatch-authoritative. Add legacy-normalization and contradictory-state fixtures.

### RV-003 — MAJOR — TEST / DATA / SECURITY
**Affected:** VERIFY_REAL_DESTINATION; VERIFY_NEGATIVE_FIXTURES; Minimal design and semantic invariants.

The old verifier false-positive is confirmed by stable 56- and 58-image runs both exiting 0 with `FILESYSTEM_VERIFICATION=PASS`. The replacement audit passed the real destination, but its code does not enforce the full stated oracle: it lacks mtime in entries, detects only four temporary suffixes, has no explicit hidden-metadata classification, and does not validate real-path containment under configured `backup_root` or reject a symlinked destination root. A broad “negative fixtures” row is not an observable coverage plan.

**Required correction:** Enumerate fixtures and expected exit/status for wrong counts, every required temp/metadata/hidden-entry class, symlink/root/containment violations, unreadable entries, arbitrary names, MIME/content mismatch, and inventory/byte changes. Require per-file relative path, size, mtime, MIME, SHA-256, errors, and read-back artifact manifest; keep filesystem PASS separate from state/identity PASS.

### RV-004 — MAJOR — TEST / SEQUENCING / HANDOFF
**Affected:** `E2E_REQUIRED: YES`; CRITICAL_PATH item 6; GUI_SAVE_ALL_OBSERVATION; Stage 05 routing.

The plan declares true E2E required but defines only a future “observation gate” plus a separate production gate. The documented C04 controller session is observation-only and the bridge has no backup-state integration; it cannot by itself prove a real Save-All/chooser/transaction journey. No exact input budget or criterion distinguishes observation-only menu identification from a production Save-All attempt. This leaves Stage 05 able to mislabel a contract/integration check as E2E or to authorize an unclear side effect.

**Required correction:** Define the exact Stage-05 journey and gate. If a real transaction is meaningful, specify one atomic Save-All attempt, exact group/album/count, a newly created empty destination under configured `backup_root`, permitted input count, chooser confirmation, and stop/retry rules. If existing files make production E2E intentionally not meaningful, set `E2E_REQUIRED: NO` with rationale and retain independent read-only route acceptance; do not call C04 E2E.

### RV-005 — MAJOR — SEMANTIC_CONTRACT / GOAL_MISALIGNMENT
**Affected:** Goal contract item 2; Exact source correspondence; owner view.

The `禎` versus `楨` rule says to remain distinct until confirmation but does not define the resulting acceptance/status or how the read-only registry association is interpreted after a user fact confirmation. This can either silently accept the legacy `楨` registry entry as the requested `禎` source or leave the workflow without a precise stop condition.

**Required correction:** Define `SOURCE_CORRESPONDENCE` outcomes (`CONFIRMED`, `UNRESOLVED`, `CONTRADICTED`), preserve both original strings and provenance, specify the one exact user question if needed, and state that `UNRESOLVED`/`CONTRADICTED` stops overall acceptance and any production route while still reporting independent file findings.

### RV-006 — MAJOR — SEMANTIC_CONTRACT / RELIABILITY
**Affected:** Minimal design and semantic invariants; TRANSACTION_COMMIT_CORE.

“Atomic same-directory state replacement plus read-back” is weaker than the contract's required serialized compare-and-commit boundary. The plan does not say how expected revision, owner/run binding, current-run pointer, terminality, and stale prepared payloads are checked under contention, nor how a failed/uncertain read-back is represented without reopening dispatch authority.

**Required correction:** Add the shared guard/conditional-commit protocol and tests for stale revision, owner/run mismatch, concurrent acquisition/finalization, write failure, read-back uncertainty, terminal owner release, and preserved unknown-dispatch barrier. State explicitly that no test result or new run ID can reset the barrier.

### RV-007 — MAJOR — TEST / STATUS_CONTRACT
**Affected:** Material checks; Stage 05 and task-closure routing.

The plan has orthogonal header statuses but no explicit status-contract fixture matrix. The required CRITICAL review/acceptance semantics need executable coverage for canonical incident, true implementation blocker, CORE fail/blocked/not-run, replan, baseline unavailable and delta, hard-clean debt, formal waiver with original result preserved, independent acceptance pending/environment block/product defect, contradictory legacy state, legacy normalization, and every DONE prerequisite.

**Required correction:** Add a status/closure matrix tied to actual outputs and Stage-05 routing. Preserve primary-outcome, implementation, CORE, required-verification, independent-acceptance, and closure subjects separately; forbid self-waiver or converting pending/blocked evidence into DONE.

## REQUIRED_PLAN_CHANGES
1. Resolve RV-001 by naming the real implementation surface and executable test path; no handoff until the real process boundary is testable.
2. Resolve RV-002 and RV-005 with explicit legacy/source-correlation outcomes and a precise stop-at-human-gate rule.
3. Expand RV-003 into an enumerated verifier oracle/fixture matrix covering containment, hidden/temp entries, read errors, inventory/hash/mtime, and separate state/identity outcomes.
4. Resolve RV-004 with a truthful E2E decision and exact observation/production action budgets and gates.
5. Resolve RV-006 with shared compare-and-commit and fault/race tests, then add RV-007 status-contract fixtures and acceptance routing.
6. Increment `PLAN_REVISION` exactly once, preserve unaffected decisions, and submit the revised plan for a new independent review attempt. Do not create Stage 03 Handoff yet.

## RESIDUAL_MINOR_NOTES
- Existing handoff copies contain historical revision/approval language; they are not approval evidence for this Revision 1 plan.
- Current destination filesystem evidence is useful but does not prove image decode quality, uniqueness, original resolution, or source history.
- No implementation, deployment, GUI observation, or acceptance was performed by this review.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revise the same TASK_ID to Revision 2, addressing RV-001 through RV-007, then rerun Stage 02 independently.
