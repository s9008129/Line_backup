# Independent Plan Review Report

## REVIEW_METADATA

- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 10
- REVIEWED_PLAN_REVISION: 10
- REVIEWED_PLAN_SHA256: aad1f80d68a194048c8fac12c9465fc8431b89454d0c5a474e87c859b2b742f1
- REVIEWED_PLAN_BYTES: 96763
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-10/plan_snapshot.md
- PLAN_SNAPSHOT_SHA256: aad1f80d68a194048c8fac12c9465fc8431b89454d0c5a474e87c859b2b742f1
- PLAN_SNAPSHOT_BYTES: 96763
- PLAN_SNAPSHOT_VERIFICATION: [VERIFIED] `cmp` exited 0; the snapshot and canonical plan were byte-identical before judgment.
- Repository anchor: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Repository instructions: [VERIFIED] no repository-local `AGENTS.md`; /Users/hsiaojohnny/.codex/AGENTS.md applies.
- Review mode: read-only for product code and `plan.md`; only the required attempt-10 snapshot and report were created.
- Inputs read: global instructions, `line-album-backup` skill, its state/evidence/state-machine/UI/verification references, and the goal-alignment, plan-review, workflow-routing, testing-verification, debugging-recovery, UI, and dependencies/contracts policies.

## GOAL_BASELINE

- PRIMARY_OUTCOME: Safely establish whether the existing 57-image destination is a valid backup of the exact requested LINE app/group/album `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17`, and otherwise stop without modifying existing photos or formal state or creating an ambiguous or duplicate production transaction.
- SUCCESS_EVIDENCE: independent filesystem and artifact evidence; exact source correspondence or an explicit unresolved/contradicted result; non-mixing state/registry/intent/writer reconciliation; a real operator CLI for verification and transaction recovery/duplicate/commit/finalization; and independent acceptance.
- MUST_NOT_BREAK: preserve the existing destination and formal state; keep requested `禎` distinct from persisted `楨`; never retry uncertain Save-All; keep filesystem/source/registry/intent/dispatch/trigger/terminal axes separate; and never use self-written fixture fields or a product result line as the oracle.
- NON_GOALS: production download in this wave, spelling merge/migration, bridge repair/TCC work, broad historical cleanup, distributed exactly-once, and unrelated refactoring.
- CRITICAL_PATH: historical false-positive evidence → real fail-closed verifier → real subprocess transaction process → independent state/status oracles → current destination/source reconciliation → scoped route decision.

## SNAPSHOT_AND_REPOSITORY_EVIDENCE

[VERIFIED] Revision 10 and the user-supplied SHA-256 match exactly. The plan was read in full from the recorded snapshot and canonical file.

[VERIFIED] The selected data project currently contains only the canonical config, backup state, and run log named by the plan. No product package, transaction library, verifier driver, or status driver exists yet. Existing untracked evidence, handoff material, and task artifacts were not changed.

## TOP_DOWN_REVIEW

[VERIFIED] The plan remains aligned with the goal. It preserves the `禎`/`楨` distinction, makes source correspondence tri-state, keeps filesystem health separate from source proof, treats the formal project as read-only, and defers production Save-All/download and future producer integration.

[VERIFIED] The product boundary is explicit: the operator-facing CLI and library are the real process boundary, while fixtures are isolated test inputs and the absent external producer is not assumed. The critical path prioritizes the false-positive, real transaction, and independent-oracle work before supporting bridge diagnosis.

[VERIFIED] The planned verifier driver/manifest now enumerates all 28 verifier matrix IDs (`valid-57` through `artifact-readback-failure),` requires literal absolute per-row paths and argv, computes independent pre-product expectations, and retains raw stdout/stderr/exit/result/manifest/inventory artifacts. It explicitly includes the authority-negative row and SAMPLE_2 mutation barriers.

[VERIFIED] The plan adds transaction authority negatives for `prepare`, `resume`, `commit`, `finalize`, and `duplicate-check`, plus an omitted-`--project-root` parser case. It requires pre/post state hashes, zero replacement/dispatch/registry-owner changes, exit 2, isolated error evidence, and raw result/manifest retention.

## EARLIER_CONTRACT_REGRESSION_CHECK

[VERIFIED] The source-spelling contract remains coherent: similarity, matching fingerprint, destination matching, legacy provenance, and historical GUI evidence do not establish exact correspondence; the current default remains `SOURCE_CORRESPONDENCE=UNRESOLVED`, with no automatic merge or rewrite.

[VERIFIED] The GUI contract remains coherent at the scope level: the exhausted historical 2/2 ledger is preserved; a fresh run requires a separate explicit gate; the controlled observation permits one current-target ellipsis input and no menu-item, Save-All, chooser, state write, or production download; production Save-All is deferred to Revision 11 plus fresh review.

[VERIFIED] The baseline contract remains explicit and reproducible: exact command, cwd, interpreter, environment, pre-artifact path/hash/length, post comparison, unchanged-versus-worsened classification, and unavailable-baseline routing to required-verification incompleteness.

[VERIFIED] The Status Contract v2 section preserves six orthogonal statuses, scoped blockers, per-check criticality/evidence/closure metadata, non-self-waiver rules, 18 literal status fixtures, and the distinction between required-verification incompleteness and product failure.

[VERIFIED] The earlier recovery shape is retained: Cases 02/03 model a durable pre-dispatch barrier, one independently counted adapter side effect, retry disabled, and fresh `--no-dispatch` recovery; Case 09 models terminal replacement followed by first-process uncertainty and no-dispatch reload; Case 10B preserves unresolved intent and releases ownership without registry addition. The persisted field values in Cases 02/03 have the contract defect identified below.

## FINDINGS

### RV10-001

- Severity: BLOCKER
- Category: SEMANTIC_CONTRACT / RECOVERY / STATE_COMPATIBILITY
- Affected plan: `plan.md:261,302-303`; transaction product contract and Cases 02/03.
- Evidence: The skill state contract's `Separate state axes` section permits `dispatch_state` values `NOT_ATTEMPTED`, `ELLIPSIS_FAILED`, `SAVE_ALL_ATTEMPTED`, `SAVE_ALL_RETURNED`, and `UNKNOWN`. Revision 10 instead requires the Case 02/03 pre-state to use `dispatch_state=NOT_DISPATCHED` and requires the durable revision-2 barrier to use `dispatch_state=DISPATCH_REQUESTED`. The plan simultaneously claims new runs use `contract_revision=1.0-rc2`, preserves the RC2 state axes, and introduces no new schema/enums. The phrase `intent is READY` is also not defined as an RC2 persisted `intent_state` value.
- Failure/rework mechanism: An implementation that follows the cases writes values outside the skill's RC2 contract; an implementation that follows the skill rejects the literal fixture expectations. A later reader, resume path, or independent oracle can classify the same persisted state differently, invalidating the intended no-retry/crash-recovery proof and potentially forcing an unsafe semantic patch during implementation.
- Smallest required correction: Choose and document an allowed RC2 representation for the pre-adapter barrier, update the Case 02/03 pre-state and post-state expectations, and define any shorthand such as `READY` in terms of an existing persisted field or evidence string. Keep `retry=false`, the independent counter, first-process uncertainty, and fresh `--no-dispatch` behavior unchanged. Update the fixture manifest/driver/oracles and README together. Retaining either new value requires an explicit schema/contract revision and a new reviewed plan; it cannot remain an undocumented RC2 value.

### RV10-002

- Severity: MAJOR
- Category: SEMANTIC_CONTRACT / DUPLICATE_GATING / STABLE_RESULT
- Affected plan: `plan.md:255,260,304` and the Case 04 oracle.
- Evidence: The transaction product contract says a resume against a matching terminal run at the expected revision returns `SKIP_TERMINAL` (`plan.md:255`). The same contract says terminal exact `duplicate-check` returns `SKIP_DUPLICATE` (`plan.md:260`). Case 04 requires both `duplicate-check` and the subsequent terminal `resume` to return `SKIP_DUPLICATE` (`plan.md:304`).
- Failure/rework mechanism: The operator CLI has no single specified precedence for a terminal run that is also an exact duplicate. The independent driver cannot accept both results for the same resume operation, and an implementation must either violate the generic terminal-resume contract or change the duplicate result semantics. This is a load-bearing stable result used by recovery and duplicate prevention, not a naming preference.
- Smallest required correction: Specify the precedence and preserve it across the product contract, state-machine behavior, Case 04 literal expectation, and independent oracle. The minimal coherent choice is `duplicate-check → SKIP_DUPLICATE` and matching terminal `resume → SKIP_TERMINAL`; if the plan intentionally chooses duplicate precedence for resume, revise the generic terminal-resume rule and explain why that result is safe and unambiguous. Add the chosen distinction to the result/error contract and README.

### RV10-003

- Severity: BLOCKER
- Category: AUTHORITY / SAFETY / ACCEPTANCE_COVERAGE
- Affected plan: `plan.md:101-108,238,250-257` and all transaction case commands.
- Evidence: The operator grammar renders `--config` and `--run-log` as optional for every transaction command (`plan.md:101-105`), while the prose later requires them for production invocations and requires canonical paths under the selected root (`plan.md:108`). Every transaction case that exercises mutation uses the test-only `state.json` exception. The new authority commands use a selected path under `/private/tmp/line-backup-acceptance-authority/root-a` and a state under `root-b`; because neither is one of the twelve allowed test roots, that case can be rejected by the test-root allowlist before it proves canonical-path rejection. There is no literal no-`--test-mode` transaction negative that proves missing/noncanonical config/run-log/state or a destination outside the configured backup root is rejected before any production transaction write.
- Failure/rework mechanism: The text is directionally correct but the executable contract remains ambiguous. A parser can treat the bracketed options as genuinely optional, or an acceptance run can pass only the isolated exception while the production/operator path remains untested. If authority validation is performed after deriving/opening the state lock, a mismatched-state negative can also create a lock artifact outside the selected root; `plan.md:252` does not explicitly order canonical authority validation before lock-file creation.
- Smallest required correction: Split the grammar into explicit production and test-only forms (or state directly that the bracketed options are accepted only with the exact test-mode exception). Require canonical `project_root/config/line_backup_config.json`, `project_root/state/backup_state.json`, and `project_root/state/run_log.md` plus configured-backup-root/destination containment for every production transaction command. Require authority validation before deriving/opening any lock or touching any path outside the isolated error-evidence directory. Add literal production-mode negative rows for `prepare`, `resume`, `commit`, `finalize`, and `duplicate-check` covering omitted/mismatched config, run-log, state, and outside-backup-root destination as applicable; independently hash the state, lock/control directory entries, counter, registry/owner fields, and replacement count before/after. Keep the existing bounded test-only state.json exception and omitted-root case.

### RV10-004

- Severity: MAJOR
- Category: SOURCE_CORRESPONDENCE / CLOSURE_SEMANTICS
- Affected plan: `plan.md:157-160,456-458`.
- Evidence: The source contract defines `CONFIRMED` narrowly as an authoritative exact join or one precise user fact that establishes the raw strings refer to the same source, and defines unresolved source identity as `PRIMARY_OUTCOME_STATUS=UNKNOWN` with no closure. The final closure sentence permits “exact source correspondence CONFIRMED or an explicitly Plan-rationalized equivalent” without defining that equivalent.
- Failure/rework mechanism: A later implementation or verifier could treat a plan rationale, fingerprint match, destination match, or spelling similarity as the undefined equivalent and declare closure without the required exact source proof. That would reintroduce the source-spelling false-positive the plan otherwise correctly prevents.
- Smallest required correction: Remove “or an explicitly Plan-rationalized equivalent,” or define the term exhaustively as only the two already permitted `CONFIRMED` proofs. State that no rationale can convert `UNRESOLVED`, `LEGACY_PROVENANCE_LIMITED`, or `CONTRADICTED` into exact source correspondence or closure.

## REQUIRED_PLAN_CHANGES

1. Resolve RV10-001 by aligning Cases 02/03, the transaction state contract, the fixture manifest/driver, and the independent oracle with the existing RC2 dispatch-state vocabulary, without weakening the retry barrier.
2. Resolve RV10-002 by selecting one stable terminal-resume/duplicate precedence and applying it consistently to the product contract and Case 04.
3. Resolve RV10-003 by making production versus test-only CLI grammar unambiguous, sequencing authority validation before lock/control-path creation, and adding executable production no-write authority coverage while preserving the six requested test-only authority negatives.
4. Resolve RV10-004 by making exact source correspondence the only closure basis, limited to the already defined authoritative join or precise user fact.
5. Preserve the verified Revision 10 contracts: literal verifier matrix manifest/driver and raw retention; `禎`/`楨` separation; formal-state and existing-photo read-only boundary; Cases 02/03/07/09/10B recovery and SAFE_ABORT intent preservation; Status Contract v2; baseline-delta evidence; one-ellipsis GUI scope; and Revision 11 production-download gate.

No product code or `plan.md` was edited.

FINAL_GATE: PLAN_REVISION_REQUIRED
