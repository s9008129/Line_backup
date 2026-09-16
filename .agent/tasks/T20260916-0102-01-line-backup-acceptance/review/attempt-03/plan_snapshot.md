# LINE album acceptance and reusable transaction process — revised candidate plan

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 3
PLAN_STATUS: CANDIDATE
REVIEW_REQUIRED: YES
INDEPENDENT_ACCEPTANCE_REQUIRED: YES
E2E_REQUIRED: NO
ACCEPTED_BY_USER: YES
PRIOR_REVIEW_ATTEMPT: 02
PRIOR_REVIEW_GATE: PLAN_REVISION_REQUIRED
PRIMARY_OUTCOME_STATUS: UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS

## Goal contract

PRIMARY_OUTCOME: Safely establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group '旻謙允禎成長日記', album '2024/05/13～05/17', and otherwise stop without any ambiguous or duplicate production transaction.

CORE_REQUIREMENTS:

- Prove or stop on exact source correspondence, not merely valid-looking files.
- Perform a read-only filesystem, inventory, state, registry, intent, and writer reconciliation against the existing destination.
- Deliver and test a reusable transaction process whose real operator CLI and library paths perform resume, duplicate gating, dispatch barrier handling, compare-and-commit, and terminal finalization. No test-only model is accepted as the process.
- Determine the shortest safe current-runtime Save-All route from documented capability and fresh evidence when that route is necessary; do not dispatch an ambiguous menu item.
- Independently accept the implementation/evidence package. A later production Save-All/download is not part of this wave and requires a new reviewed plan and gate.

SUCCESS_EVIDENCE:

- The product CLI emits separate filesystem, registry, source, state, and overall outcomes. Filesystem evidence contains exactly 57 recognized images, stable complete inventories, per-file SHA-256, byte lengths, mtime, MIME/content, no zero-byte/partial/temp/hidden/unrecognized entries, no unsafe path or entry anomalies, and an artifact manifest.
- SOURCE_CORRESPONDENCE is explicitly CONFIRMED, UNRESOLVED, or CONTRADICTED. '禎' and '楨' remain separate strings and keys; a user fact is recorded as evidence and never silently rewrites legacy data.
- State acceptance identifies EXACT, ABSENT, AMBIGUOUS, LEGACY_PROVENANCE_LIMITED, or STATE_CONTRADICTED without mixing fields across records.
- The same product transaction CLI used by an operator is invoked in subprocess restart/fault/race tests. Independent oracles inspect dispatch counters, state bytes/revisions, intent axes, registry, owner, and terminal status.
- Current CUA evidence, if required, names the exact target and one permitted ellipsis input in an existing ledger scope. Observation-only is never called production E2E and does not authorize Save-All.

MUST_NOT_BREAK:

- Existing photos and formal config/state/registry/intent/run-log are read-only for this wave; no redownload of the valid 57-file destination.
- No AXPress, AXUIElementPerformAction, AX write, guessed coordinate, OCR-only acceptance, AppleScript/hidden AX workaround, or Save-All retry after uncertainty.
- DATA_PROJECT_ROOT authority is explicit and immutable. Product test state, destination, evidence, and fake dispatcher counters are isolated from it.
- Intent, dispatch, trigger, filesystem, source, registry, and terminal ownership remain separate axes. UNKNOWN is never converted to zero or NOT_ATTEMPTED without affirmative non-dispatch proof.
- No test passes by writing a constant to a field and later asserting that same self-written field. Tests invoke the actual product CLI/process boundary and independently compute/check expected state and counters.
- Bridge/service readiness is supporting and non-gating unless a route-specific experiment proves it necessary.

NON_GOALS:

- No automatic spelling merge, legacy migration, production download, bridge reinstall, TCC change, or broad historical cleanup.
- No distributed exactly-once protocol, new persistence schema, or unrelated bridge/controller refactor.
- No claim that historical GUI, build, bridge, standalone audit, or offline PASS proves current Save-All capability or exact source correspondence.
- No claim that the absent formal data directory already contains an external resume/dispatch/commit implementation.

## Authoritative roots and product boundary

DATA_PROJECT_ROOT: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state
DATA_CONFIG: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json
DATA_STATE: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json
DATA_RUN_LOG: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md
DATA_BACKUP_ROOT: /Users/hsiaojohnny/Downloads/LINE-Backup-PoC
DATA_DESTINATION: /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57
TARGET_GROUP_KEY: line:jp.naver.line.mac:旻謙允禎成長日記
TARGET_GROUP_NAME: 旻謙允禎成長日記
TARGET_APP_BUNDLE: jp.naver.line.mac
TARGET_ALBUM: 2024/05/13～05/17
TARGET_EXPECTED_IMAGES: 57

Verified repository fact: DATA_PROJECT_ROOT currently contains only config/line_backup_config.json, state/backup_state.json, and state/run_log.md. It has no existing verifier, transaction library, producer, or consumer.

PRODUCT_BOUNDARY_DECISION: The task deliverable is an operator-facing reusable local product, not an acceptance-only fixture. Its product owner is the LINE album backup task deliverable; its consumers are the documented operator CLI commands below. The CLI and library are the single real process boundary for verify-only and offline resume/commit/duplicate behavior. The formal data project is an input/state authority and remains read-only. The plan makes no claim that another absent external producer already consumes this module. Any future integration with another producer is a new architecture/contract decision and requires PLAN_REVISION 4 plus independent review.

Planned implementation files, to be created only after this plan is independently approved:

- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/pyproject.toml
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/__init__.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/cli.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/verify.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/transaction.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/README.md

Packaging/build contract:

- Working directory: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Interpreter: /usr/bin/python3
- Test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_*.py' -v
- Verify command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state --config /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json --state /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-product-verify/attempt-01
- Transaction test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_transaction_*.py' -v
- Transaction subprocess entry point: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction resume --state /private/tmp/line-backup-acceptance-case/state.json --run-id RUN-CASE --dispatcher /private/tmp/line-backup-acceptance-case/dispatcher.py --dispatch-counter /private/tmp/line-backup-acceptance-case/dispatch-count.json
- No command in the acceptance artifacts may leave DATA_PROJECT_ROOT, DATA_DESTINATION, TARGET_GROUP_KEY, or EVIDENCE_DIR as an unresolved symbolic placeholder.

## Critical path

1. Preserve/index historical failure evidence and independently reproduce the old verifier's 56/58 false-positive in isolated paths.
2. After Rev3 approval, create the named product package/CLI and tests; prove the package is the only operator process boundary for the new reusable verifier/transaction deliverable.
3. Implement structured fail-closed verify-only and the state/source outcome contract.
4. Implement transaction resume/commit/duplicate paths with shared serialized compare-and-commit, deterministic fault/race injection, and real subprocess restart tests.
5. Run all verifier axis-correct negative cases, transaction cases, status/closure cases, then run the product verifier against DATA_DESTINATION without formal-state mutation.
6. Reconcile current source identity and state/registry/intent/writer evidence. Current default from existing evidence is SOURCE_CORRESPONDENCE=UNRESOLVED and STATE_ASSOCIATION=LEGACY_PROVENANCE_LIMITED; this stops exact goal acceptance while still reporting filesystem findings.
7. Check documented CUA capability and the existing ledger. If route evidence remains necessary, request exactly one fresh controlled observation gate. This gate permits one ellipsis GUI input only, never Save-All/menu-item/chooser/state writes. A later production Save-All route requires PLAN_REVISION 4, fresh review, and a separate one-time production gate.

## Requirement, current evidence, and closure

| Requirement | Current evidence | Rev3 closure | Class | Closure gate |
|---|---|---|---|---|
| Existing destination is 57 complete images | Direct canonical audit reports 57 stable images and 17,924,900 bytes; old verifier is not trustworthy | Product CLI must independently pass filesystem oracle and artifact read-back | CORE / OUTCOME | HARD_CLEAN |
| Exact source correspondence | Request uses 禎; config/state use 楨; legacy run title/provenance UNKNOWN | Emit tri-state result; unresolved/contradicted blocks exact goal acceptance and production route | CORE / OUTCOME | HARD_CLEAN |
| State/registry/intent/writer consistency | State revision 39 is clean, but target run is legacy and lacks full provenance/hash fields | Bind one exact record; report legacy limitations; transaction uses guarded revision/owner commit | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Reusable interruption/recovery/duplicate behavior | Existing fixture is self-authenticating; no actual process exists | New product CLI/library is the real deliverable and must pass subprocess restart/fault/race oracles | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Current Save-All route decision | Historical menu observation found no affirmative Save All; controller/bridge are read-only observation tools | Separate route status from offline acceptance; only controlled observation may establish candidate route | CORE / OUTCOME | HARD_CLEAN |
| Bridge/service | No backup-state integration | Non-gating; deploy only after route-specific causal proof and a later approved plan | SUPPORTING / DIAGNOSTIC | NON_GATING |
| Independent acceptance | Rev1/Rev2 reviews exist; Rev3 review pending | Fresh review of Rev3, then Stage 05 acceptance of actual CLI/evidence | CORE / MUST_NOT_BREAK | HARD_CLEAN |

## Source, registry, and legacy outcome contract

SOURCE_CORRESPONDENCE:

- CONFIRMED: one authoritative record joins exact target app/group key, complete album fingerprint, and destination, or one precise user fact establishes that the raw strings refer to the same source while preserving an immutable evidence-only record. A user fact does not rewrite config/state.
- UNRESOLVED: spelling similarity, a destination match, a fingerprint match, historical GUI evidence without a source join, or a legacy run with unknown title/provenance. Filesystem may be PASS; overall source/goal acceptance is UNKNOWN/BLOCKED and production route is forbidden.
- CONTRADICTED: authoritative title/group/source evidence differs from the requested source or fingerprint. Overall primary outcome is NOT_ACHIEVED; production route is forbidden.
- The verifier outputs both raw group strings, keys, authority/source, question/answer/timestamp for any exceptional user fact, and unchanged legacy record/run IDs.

STATE_ASSOCIATION:

- EXACT: exactly one registry object contains the same group_key, start/end/count fingerprint, and destination object; no cross-entry field mixing.
- ABSENT or AMBIGUOUS: registry CHECK_RESULT=FAIL; never use first match.
- LEGACY_PROVENANCE_LIMITED: legacy record is preserved, read-only normalization may describe missing contract_revision/formula calibration, but it cannot prove exact source or authorize dispatch.
- STATE_CONTRADICTED: inconsistent revision, owner, run, intent, dispatch, registry, or terminal axes; hard failure.
- Formal state is never mutated by verify-only, tests, or this acceptance wave.

User-fact evidence format, if the user supplies it:

- raw_requested_group, raw_persisted_group, app bundle, album/date/count;
- exact question asked and exact answer;
- supplied_by, supplied_at, evidence artifact SHA-256;
- unchanged config/state/registry/run IDs and legacy fields;
- SOURCE_CORRESPONDENCE result.
The default current result remains UNRESOLVED until this evidence exists.

## Product verifier oracle and failure containment

The product verify-only CLI receives explicit project root, config, state, destination, target key/fingerprint, and evidence directory. It never discovers, substitutes, or mutates roots. Exit semantics are fixed: exit 0 only when all required acceptance axes pass; exit 4 for a completed, safely rejected negative/blocked result; exit 1 for internal/read/command/artifact errors; exit 2 for invalid invocation/configuration. It must:

- Validate schema and absolute configured backup_root. Resolve real paths and require DATA_DESTINATION to be a real existing directory contained under the configured backup_root. Reject a symlinked destination root, symlinked ancestor that changes the resolved authority, and every resolution/read error.
- Enumerate immediate entries with lstat and no symlink following. Reject symlink entries, subdirectories, special files, hidden entries including .DS_Store and ._* and __MACOSX, and all required suffixes: .part, .partial, .tmp, .temp, .download, .crdownload, .incomplete, .filepart.
- Require exactly 57 regular recognized image files, no zero bytes, no unrecognized regular files, no partial/temp/hidden/other entries. Use real file MIME/content detection and a deterministic error path; file-command failures are hard failures.
- Emit per-entry relative_path, size, mtime_ns, MIME, SHA-256, and read/error status. Compare complete sorted entry tuples across three samples, including required metadata and bytes, and compare total bytes separately. Preserve both pre/post inventories when a deterministic mutator changes bytes or mtime between samples.
- Preserve arbitrary safe filenames including Unicode, spaces, pipes, and newlines through structured JSON; never use an unescaped delimiter line as the oracle.
- Bind registry association using one exact group_key + complete fingerprint + destination object. Reject absent, ambiguous, cross-entry, or wrong-group matches. Report filesystem, registry, source, state, and overall statuses independently.
- Write evidence only below the supplied evidence directory, atomically where possible, with a SHA-256/byte-length manifest. Any exception, read error, command error, malformed state, or artifact read-back failure is nonzero and never emits an overall PASS.

## Axis-correct verifier fixture matrix

Each row runs the product CLI in a fresh isolated project/evidence directory and independently checks the listed statuses, exit code, output schema, and artifact manifest. No row writes DATA_STATE.

| Case | Filesystem | Registry | Source | State | Overall | Exit |
|---|---|---|---|---|---|---|
| 57 valid images and exact association | PASS | PASS | CONFIRMED | EXACT | PASS | 0 |
| 56 or 58 images | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Each of eight temporary suffixes | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| .DS_Store, ._hidden, or __MACOSX | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Symlinked destination root/ancestor or symlink entry | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Destination outside backup_root | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Special file, unreadable entry, or file-command error | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 1 or 4 according to command/error classification |
| Text bytes named .jpg or MIME/content mismatch | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Safe Unicode/pipe/newline/space filenames | PASS | PASS | CONFIRMED | EXACT | PASS | 0 |
| mtime or bytes changed at a synchronization barrier | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 |
| Wrong group_key with valid files and same fingerprint/destination | PASS | FAIL | CONTRADICTED | EXACT or LEGACY | NOT_ACHIEVED | 4 |
| Cross-entry group/fingerprint/destination mix | PASS | FAIL | UNRESOLVED | STATE_CONTRADICTED | NOT_ACHIEVED | 4 |
| Legacy record without contract_revision/formula calibration | PASS | EXACT | UNRESOLVED | LEGACY_PROVENANCE_LIMITED | UNKNOWN/BLOCKED | 4 |
| Duplicate/ambiguous registry entries | PASS | FAIL | UNRESOLVED | AMBIGUOUS | NOT_ACHIEVED | 4 |
| Invalid invocation/configuration | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | UNKNOWN | 2 |

Filesystem PASS never implies registry/source/state PASS. Registry/source-only defects must retain filesystem PASS in the result.

## Transaction product contract and executable acceptance matrix

The product transaction path is the operator-facing transaction subcommand, not a fixture script:

- Prepare/read/validate, resume, dispatch boundary, commit, duplicate gate, and terminal finalization are functions in the same package and are invoked by the transaction CLI.
- Tests launch fresh subprocesses using the exact TRANSACTION_COMMAND shape with isolated state and destination paths. They do not call a test-only model or inspect only in-memory constants.
- The dispatcher adapter is an interface. Tests inject an executable dispatcher only at the final side-effect boundary; storage faults are injected separately at the product storage adapter. The default production dispatcher is not invoked in this acceptance wave.
- A same-directory exclusive guard is held across load, expected revision/owner validation, state replacement, fsync/read-back, and release. Every commit uses compare-and-commit on expected revision, run ID, owner, terminality, and immutable intent axes. A stale payload cannot commit after a competing writer.
- Atomic replacement is followed by reopening and validating schema, revision, owner, run, intent, registry, and terminal fields. Write failure or read-back uncertainty becomes a durable non-terminal result and never reopens dispatch authority.
- A fresh prepared intent with dispatch not started calls the injected dispatcher once and records the returned/unknown outcome. A restarted intent that is committed, returned, or UNKNOWN is never dispatched again; UNKNOWN with retry=false remains a barrier.
- A terminal exact fingerprint in the same group/destination skips dispatch and does not create a new run merely to reset a barrier. Terminal verification, registry addition, owner release, and revision increment are one guarded replacement.
- Legacy read normalization preserves raw fields and emits LEGACY_PROVENANCE_LIMITED; it never upgrades formula calibration or missing provenance into dispatch authority.

Each subprocess case records command, input fixture, pre-state SHA/bytes, post-state SHA/bytes, dispatch counter SHA/bytes, stdout, stderr, exit code, and evidence manifest. The test oracle is computed from the declared initial fixture and expected transition, not copied from product output.

| Case | Concrete process sequence | Independent oracle | Expected routing |
|---|---|---|---|
| Fresh returned dispatch | create isolated prepared state; subprocess transaction resume with dispatcher outcome RETURNED; subprocess commit | counter=1; revision +1; returned intent persisted; no owner loss | continue to verification |
| Crash after side effect before persistence | subprocess resume with dispatcher counter then deterministic crash boundary; fresh subprocess resume | counter=1, no second dispatch; durable barrier/uncertain state preserved | no retry; inspect/replan if contract cannot represent it |
| UNKNOWN dispatch | subprocess returns UNKNOWN with retry=false; fresh resume | counter=1; UNKNOWN/retry=false unchanged; no second dispatch | production route blocked |
| Existing terminal exact duplicate | isolated terminal verified state; subprocess duplicate/resume | counter=0; registry unchanged; owner already released | duplicate safely skipped |
| Stale revision | two processes synchronized before commit; process B commits first; process A commits stale payload | B one winner; A no write/no dispatch; bytes/revision prove loser | contention check PASS only if guarded |
| Owner/run mismatch | stale payload uses wrong owner or run ID | no write/no dispatch; explicit conflict result | hard failure of attempted mutation |
| Competing acquire/finalize | deterministic barrier holds lock; two subprocesses acquire/finalize | one guarded winner; one conflict; no split registry/owner | no race-dependent PASS |
| Storage write failure | transaction CLI storage injector fails before atomic replace | no false terminal success; durable non-terminal error; no new dispatch | implementation/core regression if terminal claimed |
| Read-back uncertainty | injector makes post-replace read-back fail/uncertain | no DONE/terminal claim; no dispatch retry; original barrier preserved | required verification pending/blocked |
| Successful terminal commit | verify result + registry + owner release through one CLI commit | one state replacement contains all fields; expected revision and read-back pass | permits independent acceptance |
| Legacy normalization | legacy state passed through read-only transaction validation | original fields byte-preserved; explicit legacy outcome | source acceptance remains unresolved |
| Contradictory axes | state has mismatched current run, intent, registry, owner, or terminal fields | no normalization or dispatch; exact contradiction output | replan if contract change is required |

Concrete subprocess test protocol:

1. A fixture builder creates only an isolated initial state and destination under /private/tmp/line-backup-acceptance-case-N; it records the exact input JSON and hashes it.
2. The test launches the product CLI with /usr/bin/python3 and the package path, then terminates or faults it only at a named boundary.
3. The restart launches the same product CLI and subcommand against the same isolated state; it does not import a separate test transaction implementation.
4. The test independently computes expected counter, allowed revision delta, intent/dispatch/trigger axes, registry, owner, terminality, and retry permission from the case specification, then compares the observed state and bytes.
5. Every fault/race case retains pre/post state and counter artifacts. A product output saying PASS cannot satisfy the test without the independent oracle.

## Runtime route, GUI gate, and truthful E2E decision

E2E_REQUIRED: NO for this wave. The primary object is an existing destination that must not be redownloaded, and no production download is authorized. A CUA/controller menu session is observation plus an ellipsis GUI input, not a full user-journey E2E; labeling it E2E would be false. Stage 05 independent acceptance remains mandatory for the real CLI, transaction process, evidence package, and route status.

Current ledger authority before any new GUI input:

- Historical action ledger: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/actions.jsonl
- Historical result says ellipsis_clicks_used=2 and ellipsis_click_budget=2; it contains no Save-All/menu-item click and no state write.
- This historical ledger cannot be extended or treated as fresh budget. A new observation needs a new run-specific ledger and one explicit user gate.

If route evidence remains necessary, the single Human Gate must authorize exactly this controlled experiment:

- App/bundle: LINE, jp.naver.line.mac.
- Raw target group: 旻謙允禎成長日記; album: 2024/05/13～05/17; expected count: 57.
- Project/data root: DATA_PROJECT_ROOT above, explicitly confirmed for this observation.
- Surface: exact target album card and its ellipsis popup/menu only.
- Permitted GUI input: exactly one current-target ellipsis input, with no guessed coordinate and no low-level AXPress/AXUIElementPerformAction; no menu-item click, Save All click, chooser interaction, keyboard shortcut, or state write.
- Immediately capture post evidence and stop. Ambiguous/missing/uncorrelated menu evidence yields ROUTE_STATUS=UNKNOWN and SAFE_ABORT.
- This gate is not production authorization. A production Save-All attempt would require PLAN_REVISION 4, fresh independent review, a newly created empty destination under DATA_BACKUP_ROOT, exact group/album/count/destination gate, and one atomic attempt with no retry after UNKNOWN. Existing valid 57 files may not be redownloaded.

Current legal closure distinction:

- Route unavailable while offline source/filesystem/state work is incomplete: preserve CORE/verification statuses as not-run or blocked; do not claim DONE.
- If exact existing source is independently proven and no side effect is needed, route may be recorded ROUTE_NOT_NEEDED with plan rationale; observation evidence is diagnostic, not E2E.
- If source remains UNRESOLVED, route remains blocked and overall primary outcome remains UNKNOWN even when filesystem is PASS.
- If a later production route is authorized, its results belong to a new plan revision and cannot retroactively change this wave's closure.

## Canonical status and blocker contract

All execution/review/acceptance artifacts must use Status Contract v2 exactly:

PRIMARY_OUTCOME_STATUS: ACHIEVED | NOT_ACHIEVED | UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | ESCALATED
CORE_ACCEPTANCE_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED | INCOMPLETE | WAIVED
INDEPENDENT_ACCEPTANCE_STATUS: NOT_REQUIRED | PENDING | PASS | FAIL | BLOCKED
TASK_CLOSURE_STATUS: IN_PROGRESS | PENDING_CORE_ACCEPTANCE | CORE_ACCEPTANCE_BLOCKED | READY_FOR_INDEPENDENT_ACCEPTANCE | PENDING_REQUIRED_VERIFICATION | FIX_REQUIRED | REPLAN_REQUIRED | IMPLEMENTATION_BLOCKED | ACCEPTANCE_BLOCKED | DONE

Every material check must include:

CHECK_ID, GOAL_CRITICALITY, EVIDENCE_ROLE, CLOSURE_GATE, BASELINE_REQUIRED, FAILURE_CLASSIFICATION_RULE, WAIVER_ALLOWED, WAIVER_AUTHORITY, CHECK_RESULT, WAIVER_STATUS.

Required verification checks and plan-time waiver policy:

| CHECK_ID | Criticality | Evidence role | Gate | Baseline | Failure classification | Waiver allowed | Authority | Check result | Waiver status |
|---|---|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | YES | old false acceptance not reproduced means baseline invalid; current task evidence preserved | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | YES | any incorrect accept/reject or missing artifact is task regression | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | any malformed/unsafe acceptance is task regression | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | repeat dispatch or barrier bypass is task regression | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | stale/split/uncertain commit or false terminality is task regression | NO | NONE | NOT_RUN | NOT_ALLOWED |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | YES | any mutation or contradiction is task regression/blocker | NO | NONE | NOT_RUN | NOT_ALLOWED |
| SOURCE_CORRESPONDENCE | CORE | OUTCOME | HARD_CLEAN | YES | missing authority is BLOCKED/UNRESOLVED; contradiction is FAIL | NO | NONE | NOT_RUN | NOT_ALLOWED |
| CUA_ROUTE_DECISION | CORE | OUTCOME | HARD_CLEAN | YES | missing/ambiguous current evidence is BLOCKED/UNKNOWN; no dispatch is permitted | NO | NONE | NOT_RUN | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | illegal enum/routing/self-waiver is task regression | NO | NONE | NOT_RUN | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | absent true independent result keeps acceptance PENDING/BLOCKED | NO | NONE | NOT_RUN | NOT_ALLOWED |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | failure is non-gating unless route-specific necessity is proved | YES | Project owner, exact scope | NOT_RUN | NOT_REQUESTED |

Agents may not self-waive required gates. A valid waiver must preserve CHECK_RESULT and include WAIVED_BY, WAIVER_SCOPE, rationale, evidence, residual risk, timestamp, and expiry/review trigger. Core source/data-integrity failures and fabricated/missing provenance are non-waivable.

Scoped blocker record required in any terminal artifact:

BLOCKERS:
  - id: unique
    scope: IMPLEMENTATION | CORE_ACCEPTANCE | REQUIRED_VERIFICATION | INDEPENDENT_ACCEPTANCE | AUTHORITY | ENVIRONMENT
    subject: exact component/check
    result: FAIL | BLOCKED | NOT_RUN
    class: TASK_REGRESSION | PRE_EXISTING_REPOSITORY_FAILURE | ENVIRONMENT_FAILURE | AUTHORITY_REQUIRED | INPUT_UNAVAILABLE | PRODUCT_DEFECT
    task_regression_evidence: evidence | NONE | UNKNOWN
    evidence: exact artifact/path/result
    next_action: one precise action
    owner: explicit role or user
    waiver_allowed: YES | NO

## Closure and sequencing

Stage 02 must independently review this Revision 3 and its exact hash. Stage 03 may compile handoff only for the approved revision/hash. Stage 04 creates the named package and runs only the approved verifier/transaction wave; it must write execution.md with the canonical six statuses, check matrix, scoped blockers, and artifact hashes. Stage 05 independently accepts the real CLI/evidence and reads immutable Stage 04 execution evidence; it does not modify product code.

The current plan is not implementation approval. Offline read-only reconciliation, isolated fixture construction, baseline reproduction, and review preparation are authorized now. Product code edits, external formal-state writes, GUI input, deployment, and production download require the applicable later gate. Any semantic contract, product-boundary, E2E, or GUI-budget change increments this TASK_ID and repeats independent review.

DONE requires: PRIMARY_OUTCOME_STATUS=ACHIEVED; IMPLEMENTATION_STATUS=COMPLETE; CORE_ACCEPTANCE_STATUS=PASS or explicitly plan-rationalized NOT_REQUIRED; REQUIRED_VERIFICATION_STATUS=PASS/NOT_REQUIRED/WAIVED; INDEPENDENT_ACCEPTANCE_STATUS=PASS/NOT_REQUIRED; exact source correspondence confirmed or an explicitly plan-rationalized equivalent closure condition; no unresolved hard blocker; in-scope final artifacts with valid hashes; unrelated user work preserved.

If source identity remains unresolved after all authorized evidence, the legally correct result is PRIMARY_OUTCOME_STATUS=UNKNOWN with CORE_ACCEPTANCE_STATUS=BLOCKED or the applicable source check blocked, not DONE. If an independent acceptance authority/tool is unavailable, preserve implementation/CORE/required-verification facts and route INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED, TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED. Never downgrade proven implementation because acceptance could not run.

## Owner view

Essential: prove whether the existing 57 files can be safely attributed to the exact requested LINE source and prove real reusable recovery/duplicate behavior before any new GUI side effect. Filesystem health alone is insufficient. The new local CLI/package is the explicit reusable product boundary for this task; it must not be confused with an absent external producer. Supporting: bridge/service diagnosis only if causal evidence proves necessity. Deferred: production Save-All/download, bridge repair, migration, OCR, and historical cleanup. The largest remaining risk is still that the 57 files are valid but the original source namespace/provenance was never captured.
