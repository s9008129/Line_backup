# Plan Review Report

## REVIEW_METADATA

- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 07
- REVIEWED_PLAN_REVISION: 6
- REVIEWED_PLAN_SHA256: 4b52c985174a61396c2fd36aacc45349131214de6ed7323d30a35fda380eb1c6
- REVIEWED_PLAN_BYTES: 76904
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-07/plan_snapshot.md
- PLAN_SNAPSHOT_SHA256: 4b52c985174a61396c2fd36aacc45349131214de6ed7323d30a35fda380eb1c6
- PLAN_SNAPSHOT_BYTES: 76904
- PLAN_SNAPSHOT_VERIFICATION: [VERIFIED] byte-for-byte `cmp` equal to canonical plan.md before judgment
- Repository anchor observed: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup; no repository-local AGENTS.md; no product package, src/, tests/, or pyproject.toml exists yet; pre-existing untracked .agent/, evidence/, handoff.md, and LINE-BACKUP-GOAL-HANDOFF-2026-09-15.md preserved
- Reviewer runtime/model: Codex desktop review context; model identity not recorded by runtime
- Review mode: read-only for product code and plan.md; only attempt-07 snapshot/report were created

## OWNER_VERDICT

The plan is aimed at the correct outcome: determine whether the existing 57-image directory can be attributed to the exact requested LINE source, preserve the existing data and formal state, and build a real operator-facing CLI whose recovery and duplicate behavior is independently testable. The essential path is offline fail-closed verification, exact source/state reconciliation, real subprocess transaction tests, and independent acceptance. Bridge readiness and the one possible GUI observation remain supporting/scoped work; production Save-All is correctly deferred.

The plan is not yet ready for Handoff. The core design is directionally sound, but several acceptance contracts still permit two incompatible implementations or two incompatible oracle interpretations. The largest risks are (1) treating a post-replace finalization uncertainty as non-terminal, (2) allowing a baseline-delta result without a named reproducible baseline subject and artifact, and (3) accepting status/recovery fixtures whose exact durable transitions are not fully specified. These can make a test suite appear complete while failing to prove the safety contract.

## GOAL_BASELINE

- PRIMARY_OUTCOME: Safely establish whether the existing destination `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` is a valid backup of the exact requested LINE app/group/album `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17` with 57 images; otherwise stop without modifying existing photos/formal state or creating an ambiguous or duplicate production transaction.
- SUCCESS_EVIDENCE: independently observed filesystem/inventory evidence; exact source correspondence or an explicit unresolved/contradicted result; non-mixing state/registry/intent/writer reconciliation; a real operator CLI boundary for verify-only and transaction recovery/duplicate/commit/finalization behavior; and independent acceptance evidence.
- MUST_NOT_BREAK: preserve existing files and formal state; keep `禎` and `楨` distinct; never retry an uncertain Save-All; keep intent, dispatch, trigger, filesystem, source, registry, and terminal ownership as separate axes; never rely on a self-written fixture field or product PASS line as its own oracle.
- NON_GOALS: production download in this wave, spelling merge/migration, bridge reinstall/TCC work, broad historical cleanup, distributed exactly-once, and unrelated refactoring.
- CRITICAL_PATH: old false-positive and self-certifying-fixture evidence -> real fail-closed verifier -> real subprocess transaction process -> independent state/status oracles -> current destination/source reconciliation -> scoped route decision.

## GOAL_ALIGNMENT

[VERIFIED] Rev6 preserves the goal baseline. It does not treat the valid-looking 57 files, old GUI evidence, bridge health, or a historical approval string as proof of exact source correspondence. It keeps the current `禎` versus persisted/configured `楨` distinction unresolved and correctly makes production routing conditional on later evidence.

[VERIFIED] The planned local CLI is a justified product boundary for this wave because the authoritative data project has no verifier or transaction producer. The plan explicitly prevents the acceptance driver from becoming a second transition model.

## NECESSITY_AND_TRACEABILITY

[VERIFIED] The filesystem, source, state, transaction, route, and independent-acceptance requirements each trace to the primary outcome or a stated safety/provenance invariant. The bridge is explicitly SUPPORTING/DIAGNOSTIC and NON_GATING unless route-specific causal evidence proves necessity.

[VERIFIED] The new `DOCUMENTATION_RETENTION_HEALTH` requirement has a concrete, narrow rationale: missing raw command/output/exit or manifest/hash read-back can make independent acceptance non-reproducible and provenance-invalid. Unrelated repository documentation is excluded. The reachable waiver row preserves the original item failure and requires named authority, scope, rationale, evidence, residual risk, approval time, and expiry/review trigger. This is an adequate proportionality rationale, subject to the fixture corrections below.

## GATE_AND_VETO_AUDIT

[VERIFIED] The supporting hard-clean veto is not justified by schema completeness alone; it is tied to reproducibility/provenance validity and scoped to task evidence. The project-owner exact-scope waiver is permitted without allowing an agent to self-waive. Core source/data-integrity and fabricated/missing provenance remain non-waivable.

[VERIFIED] The core source and route gates are separated. `ROUTE_NOT_NEEDED` is explicitly available only after exact existing provenance is proven and no side effect is needed; otherwise route evidence remains a scoped core blocker. This is consistent with the goal and the skill.

## COUPLING_AND_FAILURE_CONTAINMENT

[VERIFIED] Filesystem PASS is not allowed to imply registry/source/state PASS. Internal read/command/artifact failures remain UNKNOWN/nonzero rather than being converted to a negative or successful outcome. Formal-state verification is read-only, and fake dispatch counters are isolated from the authoritative project.

[VERIFIED] Case 07 uses only the declared `transaction prepare` interface and one literal barrier, with distinct run/owner IDs and one shared state. The invariant of one ownership replacement and one acquisition conflict is the right narrow concurrency contract. The wording inconsistency is recorded as RV7-001.

## DESIGN_ECONOMY

[VERIFIED] The plan avoids introducing a second persistence schema, distributed exactly-once machinery, or bridge integration without causal proof. The lock, atomic replacement/read-back, evidence manifest, independent oracle, and subprocess cases each pay rent in data-integrity or repeat-dispatch risk reduction.

[INFERRED] A separate status evaluator is necessary for the Status Contract v2 fixtures, but it is not listed among the planned source files. This is a minor implementation-scope inconsistency unless the evaluator is intentionally housed in an already listed module.

## CRITICAL_PATH_AND_PRIORITY

[VERIFIED] The plan sequences false-positive reproduction and real verifier/transaction implementation before any optional GUI observation or bridge work. The current unresolved source identity correctly stops exact primary acceptance while still permitting filesystem findings.

[MAJOR RISK] The exact recovery and status oracle definitions must be resolved before implementation; otherwise later fixture debugging can consume effort without proving the primary safety outcome. See RV7-002 through RV7-006.

## REQUIREMENT_FIDELITY

[VERIFIED] Rev6 addresses the prior attempt-06 requirements: Case 07 no longer asks for an undeclared acquisition/finalization operation; the canonical hard-clean incident now preserves `PRIMARY_OUTCOME_STATUS=ACHIEVED`; contradictory-state routing now uses `IMPLEMENTATION_STATUS=IN_PROGRESS`; a named baseline-delta check exists; the supporting hard-clean rationale and waiver are present; and literal driver commands are present for Cases 01–12.

[UNVERIFIED] The plan does not yet prove that the new implementation will be able to realize all of those contracts; this is expected before Stage 04, but the acceptance protocol must be exact enough to make the later proof decision-valid.

## GROUNDING_AND_DRIFT

[VERIFIED] Current data evidence matches the material plan anchors: the selected data root contains only config/state/run_log; config is 372 bytes with SHA-256 `390cbdcf36a88c9f134c0ecb29d39018ebadf42babfb7a264a741337499d3b3b`; state is 48,146 bytes with SHA-256 `e9313a563bf298d4b1e9ae243c5d3d404ad1333f69cb71b156e68589a8ec2f59`; and run_log is 15,950 bytes.

[VERIFIED] Current state is schema 2/revision 39 with four verified-album entries, five runs, and null current run/active writer/context lock. The 57-image target run is legacy (`contract_revision=null`, `observed_title=null`) and uses persisted group key `line:jp.naver.line.mac:旻謙允楨成長日記`, not the requested `line:jp.naver.line.mac:旻謙允禎成長日記`. The target registry entry and destination are present, but exact source provenance is not established.

[VERIFIED] The destination currently reports 57 immediate `image/jpeg` files. The three historical raw inventories are each 7,971 bytes and share SHA-256 `96b00082f3999710bbb46630c8e8d87b8f7d046c3bbf157340f739ef79c5e0a8`; corrected audit evidence reports 17,924,900 total bytes and no observed anomalies. This is filesystem provenance only, not source proof.

## ARCHITECTURE_AND_CONTRACTS

[VERIFIED] The old verifier’s lines 115–129 compare only inventory stability and a destination registry match; they never compare observed image count with `EXPECTED=57`. Isolated 56-file and 58-file reproductions therefore emit `ACTUAL_IMAGES=56/58`, `FILESYSTEM_VERIFICATION=PASS`, and exit 0. The plan correctly treats this as a false-positive baseline rather than acceptance.

[VERIFIED] The historical recovery fixture writes `UNKNOWN` and `save_all_retry_allowed=false` into a temporary state at lines 90–113 and then validates those same values. It does not invoke an operator CLI, restart a process, or independently derive expected state. The plan correctly rejects it as CORE recovery evidence.

[VERIFIED] The historical GUI ledger is preserved as provenance: `actions.jsonl` is 4,219 bytes, SHA-256 `9d6a159024f822003052fd7d538598d3a161f226c49ce14ea5c11d5c95c95aee`, with 2 ellipsis inputs, 0 menu-item/Save-All clicks, and 0 state writes. Its budget authority is 4,555 bytes, SHA-256 `a43d23d6166a3d2156c5e3a1ccd08cc394b8b283f9c3a2d007929db986922c95`, and records an exhausted 2/2 ellipsis budget. Current direct menu capability remains UNKNOWN/UNAVAILABLE for affirmative Save-All proof; the current bridge status file has stale `pid=794` provenance and does not establish a ready route.

## DATA_SECURITY_RELIABILITY

[VERIFIED] The plan preserves project-root authority, backup-root containment, no formal-state mutation, no GUI bypasses, no OCR-only acceptance, and no retry after dispatch uncertainty. It keeps historical evidence separate from operational authority and requires literal absolute paths for isolated fixtures.

[MAJOR] The post-replace uncertainty branch and recovery restart revisions are not yet semantically closed. This is a data-integrity/repeat-side-effect risk, not a style preference.

## IMPLEMENTATION_SEQUENCE

[VERIFIED] The intended order—baseline reproduction, real package, verifier, transaction, fixtures, current reconciliation, then optional route observation—is appropriate. Stage 03 must remain blocked until the revised plan is reviewed; no handoff or product implementation is authorized by this report.

## TESTABILITY_AND_ACCEPTANCE

[VERIFIED] Literal driver command coverage exists for all twelve case IDs: each has one line with absolute `/private/tmp/line-backup-acceptance-case-N/...` paths, and the plan contains no unresolved `${...}`/placeholder command variables. Cases 05 and 07 also name literal barrier paths and release actions. The path protocol is materially improved over Rev5.

[MAJOR] Literal paths alone do not make Cases 02, 03, 09, or the Status Contract fixture set reproducible when their expected durable transitions or command outcomes are absent/contradictory. See the findings.

## SCOPE_AND_COMPLEXITY

[VERIFIED] The scope remains one album, one data authority, isolated test roots, and no production download. The absent formal data-directory producer is not silently invented. The only minor scope note is the unlisted placement of the status evaluator noted above.

## FINDINGS

### RV7-001

- Severity: MAJOR
- Category: SEMANTIC_CONTRACT
- Affected plan: `plan.md:237,258-259,289`
- Evidence: The plan says the Case 07 winner identity is “intentionally scheduling-independent,” while also saying either A or B may win and there is no fixed scheduler-selected winner. A single barrier before the shared lock can serialize the race invariant, but it cannot make the process identity of the winner independent of scheduling.
- Failure/rework mechanism: An implementer or driver can incorrectly assert a fixed process winner, or treat a scheduling-dependent identity as part of the deterministic contract. That would make the acceptance result depend on launch timing or require an undeclared scheduler control.
- Smallest required correction: Replace the contradictory wording with: winner selection may be A or B and is not an acceptance precondition; the deterministic, winner-independent assertion is exactly one `PREPARED`/state replacement and exactly one `CONFLICT_ACTIVE_RUN` exit 4/no replacement. Define winner identity as whichever literal process is independently proven to own the post-state, and record both identities after the post-state read.

### RV7-002

- Severity: MAJOR
- Category: SEMANTIC_CONTRACT
- Affected plan: `plan.md:240,242,291,299`
- Evidence: `READBACK_UNCERTAIN_AFTER_REPLACE` is defined as replacing state and then returning uncertainty; finalization is defined as one guarded replacement that commits `workflow_outcome`, terminal evidence, registry/verification as applicable, and null ownership; Case 09 nevertheless requires that after the fault the state remain explicitly uncertain/non-terminal while the reload uses expected revision 3.
- Failure/rework mechanism: If the replacement payload is final VERIFIED, authoritative reload should see a terminal run with ownership released, not a non-terminal state. If the state is non-terminal, the case did not exercise read-back uncertainty after a terminal replacement. The first process and the reload can therefore disagree about terminality and routing while both satisfy the prose.
- Smallest required correction: Choose one exact fault model. Recommended: the first finalize process returns exit 1 because its post-replace read-back is uncertain, while the independently read state is the committed revision-3 terminal payload; specify the exact fresh `resume --no-dispatch` result/status and preserve the first-process uncertainty separately. If non-terminal preservation is required instead, move the injected fault before replacement and rename the case/expected result accordingly.

### RV7-003

- Severity: MAJOR
- Category: TEST
- Affected plan: `plan.md:361,365,377,295,297-300`
- Evidence: `BASELINE_REGRESSION_DELTA` now has the required metadata names, but the plan does not name the baseline subject, exact artifact path/filename, literal pre-change command, exact working directory/interpreter/environment fingerprint schema or values, captured output/signature files, or the literal post-change invocation. Existing historical logs are not automatically the same command/environment as the future product check.
- Failure/rework mechanism: Stage 05 cannot reproduce the baseline or determine whether a changed result is a new/worsened signature versus a missing/renamed artifact. A future implementation could satisfy the field list with a different command and still report `UNCHANGED`.
- Smallest required correction: Bind the check to one named broad check, identify the exact pre-change artifact(s) and byte/hash manifest, record one literal argv plus cwd, `/usr/bin/python3` identity and a normalized environment fingerprint, and specify the exact captured exit/stdout/stderr/result/signature inputs. Require the post-change run to use that same literal command/environment and compare the named signatures; define absent/unreadable/mismatched baseline artifact handling as `INCOMPLETE` with a scoped next action.

### RV7-004

- Severity: MAJOR
- Category: SEMANTIC_CONTRACT
- Affected plan: `plan.md:367-379`, especially the canonical incident row at line 378
- Evidence: The canonical incident correctly changes primary status to `ACHIEVED` and aggregate required verification to `INCOMPLETE`, but its exact blocker is `REQUIRED_VERIFICATION/BLOCKED/PRE_EXISTING_REPOSITORY_FAILURE`. Status Contract v2 §7.7 rule 9 permits aggregate `INCOMPLETE` for pre-existing hard-clean debt and reserves aggregate `BLOCKED` for a verification phase that cannot obtain a valid conclusion; a hard-clean failure is a conclusive check result, not an unavailable phase.
- Failure/rework mechanism: A status evaluator can route a conclusive pre-existing failure as a blocked verification phase, conflating `FAIL` with `BLOCKED` and making the fixture disagree with the canonical routing semantics. This undermines the distinction between pre-existing debt and an environment/input inability to conclude.
- Smallest required correction: Make the underlying hard-clean check/blocker result `FAIL` with class `PRE_EXISTING_REPOSITORY_FAILURE`, retain aggregate `REQUIRED_VERIFICATION_STATUS=INCOMPLETE`, `PRIMARY_OUTCOME_STATUS=ACHIEVED`, and `TASK_CLOSURE_STATUS=PENDING_REQUIRED_VERIFICATION`; reserve `BLOCKED` for the unavailable-baseline/environment fixture. If the slash shorthand is retained, change the canonical row to `REQUIRED_VERIFICATION/FAIL/PRE_EXISTING_REPOSITORY_FAILURE` and explicitly document why aggregate status is `INCOMPLETE`.

### RV7-005

- Severity: MAJOR
- Category: TEST
- Affected plan: `plan.md:284-285,298-299`
- Evidence: Cases 02 and 03 invoke a first process at expected revision 1, then require a fresh process at expected revision 2, but do not specify the first process exit code, the exact durable state mutation that creates revision 2, or the precise crash/unknown boundary relative to that mutation. `--crash-after-dispatch` can mean after the counter side effect but before state commit unless the injection point is explicitly defined.
- Failure/rework mechanism: A real dispatcher can write the counter once and crash before the state advances, leaving revision 1 while the prescribed restart command requires revision 2. A different implementation can commit revision 2 before simulating the crash. Both follow the current prose but produce different restart inputs and routing.
- Smallest required correction: For each case, specify the first-process exit/result, the exact pre/post revision and all changed intent/dispatch/trigger fields, and the injection point. For Case 02 state whether the product commits the dispatch barrier/state before the simulated process crash; for Case 03 state the durable UNKNOWN transition and exit. Specify the exact reload exit/status and the independent counter/state oracle before the product output is read.

### RV7-006

- Severity: MAJOR
- Category: TEST
- Affected plan: `plan.md:252,261,367-384`
- Evidence: The Status Contract table declares many required executable fixtures, including baseline unavailable, hard-clean debt, formal waiver, Stage 05 acceptance block, CORE NOT_REQUIRED rationale, and all closure prerequisites. Only the legacy and contradictory cases have explicit `status evaluate` commands in Cases 11–12; the plan does not map the other fixture rows to literal input/output paths, command invocations, expected exits, or an explicit fixture manifest.
- Failure/rework mechanism: Independent acceptance can report the transaction Cases 01–12 complete while never executing or independently checking the waiver, baseline, routing, and closure rows that the plan calls required. A declarative table alone cannot prove the v2 contract or its next-step decisions.
- Smallest required correction: Enumerate every status fixture ID with a literal isolated input JSON, output/result path, exact `status evaluate` command (or one literal driver command whose fixture manifest and argv arrays are fixed), expected exit and all six statuses, blocker fields, check metadata, waiver fields, and next-step decision. Include explicit independent oracle rules for original `CHECK_RESULT` preservation and waiver reachability.

### RV7-007

- Severity: MAJOR
- Category: TEST
- Affected plan: `plan.md:242,250,283-292`
- Evidence: The product contract makes `transaction finalize --outcome SAFE_ABORT` a core terminal transition that preserves unresolved intent barriers and releases ownership safely, but the literal transaction cases exercise only VERIFIED finalization (Cases 01 and 10) and a faulty VERIFIED finalization (Case 09). No transaction subprocess case independently proves terminal SAFE_ABORT preservation/release.
- Failure/rework mechanism: An implementation may pass every listed transaction case while incorrectly clearing an unresolved intent, registering a verification on SAFE_ABORT, or leaving an owner/context lock behind. The generic status rows cannot prove the persisted transaction mutation and read-back invariants.
- Smallest required correction: Add a literal isolated SAFE_ABORT transaction subcase within the approved case set (or an explicitly enumerated additional case) with pre-state containing an unresolved intent, exact finalize argv, expected revision/state fields, preserved barrier and original observations, null ownership fields, no registry addition, exit/result, and independent post-state/read-back oracle. Keep it separate from the post-replace uncertainty case.

## REQUIRED_PLAN_CHANGES

1. Revise the same TASK_ID to the next monotonic plan revision and correct RV7-001 through RV7-007 without changing the unresolved `禎`/`楨` conclusion, formal-state read-only rule, historical ledger interpretation, or current GUI authorization scope.
2. Make Case 07 explicitly winner-independent: the identity may vary with scheduling; only the one-winner/one-`CONFLICT_ACTIVE_RUN` invariant is deterministic, and the literal driver derives winner/loser from independently read post-state evidence.
3. Close the Case 09 storage-fault contract by choosing terminal-after-replace uncertainty or pre-replace failure and specifying exact fresh-resume statuses, exit, revision, ownership, and next action.
4. Bind `BASELINE_REGRESSION_DELTA` to a named subject and concrete artifact/command/environment contract, including exact hashes/byte lengths and unavailable-baseline routing. Do not silently substitute a historical artifact with a different command/environment.
5. Correct the canonical hard-clean fixture’s scoped result to `FAIL`/pre-existing while retaining aggregate `INCOMPLETE`, and make the formal waiver and all status rows literal, executable, independently oracled fixtures with original results preserved.
6. Specify the missing first-process outcomes and durable transitions for Cases 02–03 and add an independently oracled SAFE_ABORT transaction finalization subcase.
7. Re-run Stage 02 against the new plan snapshot/hash. Do not compile Stage 03 or implement product code from this Rev6 candidate.

## RESIDUAL_MINOR_NOTES

- [VERIFIED] The exact Rev6 snapshot is preserved at the metadata path and is byte-identical to plan.md. No product code or plan.md was modified.
- [VERIFIED] The existing 57-file audit is useful filesystem evidence, but the old delimiter-based inventory and old verifier output remain historical/provenance evidence only; the plan correctly requires structured JSON and independent artifact read-back for the product.
- [VERIFIED] The supporting bridge hard-clean/waiver policy is materially improved and does not need to become a global blocker. The current installed bridge status and historical runtime ledger remain insufficient for affirmative Save-All proof, and the plan correctly keeps production download behind a later reviewed plan and gate.
- [MINOR] The planned file list does not name the module that implements `status evaluate`; either list it or explicitly place the evaluator in an already listed module without expanding scope.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revision mode on the same TASK_ID; increment PLAN_REVISION from 6 to 7, correct RV7-001 through RV7-007, then request a fresh Stage 02 review against the new exact snapshot/hash.
