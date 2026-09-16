# LINE album acceptance and reusable transaction core — revised candidate plan

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 2
PLAN_STATUS: CANDIDATE
REVIEW_REQUIRED: YES
INDEPENDENT_ACCEPTANCE_REQUIRED: YES
E2E_REQUIRED: NO
ACCEPTED_BY_USER: YES
PRIOR_REVIEW_ATTEMPT: 01
PRIOR_REVIEW_GATE: PLAN_REVISION_REQUIRED
PRIMARY_OUTCOME_STATUS: UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS

## Goal contract

PRIMARY_OUTCOME: Safely establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group '旻謙允禎成長日記', album '2024/05/13～05/17', and otherwise stop without any ambiguous or duplicate production transaction.

SUCCESS_EVIDENCE:

- A product-owned, read-only verifier process observes exactly 57 recognized images, stable complete inventories, per-file SHA-256, byte lengths, mtime, MIME/content, no zero-byte/partial/temp/hidden/unrecognized entries, no unsafe path or entry anomalies, and a precise group-scoped registry association.
- SOURCE_CORRESPONDENCE is explicit and tri-state: CONFIRMED, UNRESOLVED, or CONTRADICTED. '禎' and '楨' remain separate strings and separate keys unless authoritative evidence or one precise user fact establishes correspondence. A user fact never silently rewrites legacy records.
- State acceptance is separate from filesystem acceptance. A legacy/provenance-limited record can be reported as LEGACY_PROVENANCE_LIMITED but cannot satisfy exact source acceptance. Contradictory records are STATE_CONTRADICTED and hard-stop.
- A product-owned reusable transaction process, invoked through its actual resume/commit/duplicate entry points, proves interrupted restart behavior, no repeated side-effect dispatch, verified-fingerprint skip, unknown-dispatch barrier, compare-and-commit, read-back failure containment, terminal registry/owner release, and stale-writer rejection.
- Current runtime evidence separately establishes target acquisition, popup observation, affirmative Save-All identity, supported mapping, and chooser routing if that route is ever authorized. Observation-only is never labeled production E2E and no GUI input is sent without the ledger and explicit gate.

MUST_NOT_BREAK:

- Existing photos and formal state/config/registry/intent/run-log are read-only for this acceptance wave; no redownload of the valid 57-file destination.
- No AXPress, AXUIElementPerformAction, AX write, guessed coordinate, OCR-only acceptance, AppleScript/hidden AX workaround, or Save-All retry after uncertainty.
- Project/data-root authority remains explicit and immutable; verify-only has an empty formal-state write set; all fixture state and test destinations are isolated.
- Intent, dispatch, trigger, filesystem, source, registry, and terminal ownership remain separate evidence axes. UNKNOWN is never converted to zero or NOT_ATTEMPTED without affirmative non-dispatch proof.
- Bridge/service readiness does not become a global gate unless a direct runtime experiment proves it necessary for the selected route.
- No test passes by writing a constant to the same field it later asserts; every material test invokes the CLI/process boundary or the shared product process path and checks an independent oracle.

NON_GOALS:

- No automatic spelling merge, legacy migration, production download, bridge reinstall, TCC change, or broad historical cleanup.
- No distributed exactly-once protocol, new persistence schema, or unrelated bridge/controller refactor.
- No claim that historical GUI, build, bridge, standalone audit, or offline PASS proves current Save-All capability or source correspondence.

## Authoritative roots and implementation surface

DATA_PROJECT_ROOT: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state
DATA_CONFIG: DATA_PROJECT_ROOT/config/line_backup_config.json
DATA_STATE: DATA_PROJECT_ROOT/state/backup_state.json
DATA_RUN_LOG: DATA_PROJECT_ROOT/state/run_log.md
DATA_BACKUP_ROOT: /Users/hsiaojohnny/Downloads/LINE-Backup-PoC

The current DATA_PROJECT_ROOT contains only config/state/run_log and no existing verifier or transaction implementation. Therefore the planned product-owned deliverable is explicitly a new reusable module in the selected task workspace, not a test-only model:

IMPLEMENTATION_ROOT: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
IMPLEMENTATION_PACKAGE: IMPLEMENTATION_ROOT/src/line_backup_acceptance/
IMPLEMENTATION_CLI: 'python3 -m line_backup_acceptance'
TEST_ROOT: IMPLEMENTATION_ROOT/tests/
TEST_COMMAND: 'PYTHONPATH=src python3 -m unittest discover -s tests -p test_*.py -v'
VERIFY_COMMAND: 'PYTHONPATH=src python3 -m line_backup_acceptance verify-only --project-root DATA_PROJECT_ROOT --config DATA_CONFIG --state DATA_STATE --destination DATA_DESTINATION --group-key TARGET_GROUP_KEY --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir EVIDENCE_DIR'
TRANSACTION_COMMAND: 'PYTHONPATH=src python3 -m line_backup_acceptance transaction ...'

The CLI and transaction library are the same process boundary used by the tests. The fake dispatcher is injected only at that boundary and is an executable test double whose invocation counter and returned outcome are independently read after a subprocess restart. No formal production state is passed to a mutating test. If a later requirement demands integration with another product-owned path, that is a new architecture/contract decision requiring PLAN_REVISION 3 and review; it must not be silently inferred from the empty DATA_PROJECT_ROOT.

## Critical path

1. Preserve and index all historical failure evidence; independently reproduce the old verifier's false-positive with isolated 56 and 58 image fixtures.
2. After this revised plan is independently approved, implement the product-owned verifier CLI and structured inventory oracle.
3. Implement the product-owned transaction CLI/library with one shared serialized compare-and-commit boundary, explicit legacy normalization, and an injected fake dispatcher used only for isolated tests.
4. Run the enumerated verifier negatives, recovery/restart, duplicate, stale-writer, read-back, and status/closure cases; preserve each attempt's command, input, stdout, stderr, exit, state, counter, and manifest.
5. Run the product verifier against the real destination read-only; report filesystem, source, registry, state, and overall results separately.
6. Reconcile exact target source identity and current state/registry/intent/writer evidence. If SOURCE_CORRESPONDENCE is UNRESOLVED or CONTRADICTED, stop overall acceptance and any production route while preserving independent filesystem findings.
7. Check documented CUA capabilities and the existing action ledger. Only after offline gates, ask for one observation-only experiment if still required. Do not call it E2E. A production Save-All/download route requires a later plan revision and separate one-time production gate.

## Requirement to evidence and closure

| Requirement | Current evidence | Rev2 closure | Class | Closure gate |
|---|---|---|---|---|
| Existing destination is 57 complete images | Old verifier has 57 JPEG-looking files; new direct canonical audit has 57 stable files but is standalone | Product verifier must pass filesystem criteria only with exact count, complete canonical inventory, bytes, mtime, MIME/content, path safety, and read-back manifest | CORE / OUTCOME | HARD_CLEAN |
| Exact source correspondence | Config/state/registry use '旻謙允楨成長日記'; request is '旻謙允禎成長日記'; legacy run title UNKNOWN | Emit CONFIRMED/UNRESOLVED/CONTRADICTED with both raw strings and provenance; UNRESOLVED/CONTRADICTED blocks overall acceptance and production | CORE / OUTCOME | HARD_CLEAN |
| State/registry/intent/writer consistency | State revision 39, clean owner/context; target run is legacy, destination-bound, but title/provenance and per-file hashes are limited | Product verifier binds one exact group_key + fingerprint + destination record; reports LEGACY_PROVENANCE_LIMITED separately; transaction tests cover guarded commit/read-back | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Reusable interrupted recovery and duplicate protection | Old fixture is self-authenticating and never calls a real process | Subprocess tests call actual transaction resume/commit/duplicate paths across restart and inspect dispatch counter/state oracle | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Actual Save-All route | Historical observation did not identify Save All; current bridge/controller is observation-only | Observation-only route is a separate diagnostic/CORE outcome check; no production dispatch without affirmative evidence and gate | CORE / OUTCOME | HARD_CLEAN |
| Bridge/service | No Backup Skill/state integration in bridge/controller | Keep non-gating; only prepare a reviewed deployment if a route-specific experiment proves necessity | SUPPORTING / DIAGNOSTIC | NON_GATING |
| Independent acceptance | None for Rev2 yet | New independent review of Rev2, then Stage 05 independent acceptance of real CLI evidence; no self-approval | CORE / MUST_NOT_BREAK | HARD_CLEAN |

## Source and state outcome contract

SOURCE_CORRESPONDENCE:

- CONFIRMED: exact target group key and fingerprint are joined in one authoritative source/registry record, or a precise user fact establishes that '禎' and '楨' are the same source and independent evidence preserves that fact. The verifier must still report the original legacy key and missing provenance.
- UNRESOLVED: only spelling similarity, a destination match, a fingerprint match, or historical GUI evidence without a source join exists. Filesystem findings may be PASS, but overall source/goal acceptance is BLOCKED and no production route is allowed.
- CONTRADICTED: authoritative source/title/group evidence disagrees with the requested group or fingerprint. Overall acceptance is FAIL/BLOCKED and no production route is allowed.
- No outcome may normalize or merge the strings automatically.

STATE_ASSOCIATION:

- EXACT: one registry entry contains the same group_key, start/end/count fingerprint, and destination, with no cross-entry field mixing.
- ABSENT or AMBIGUOUS: registry acceptance FAIL; never use first match.
- LEGACY_PROVENANCE_LIMITED: legacy record is preserved and may support historical context, but cannot prove exact source correspondence or authorize dispatch.
- STATE_CONTRADICTED: inconsistent revision/owner/run/intent/registry axes are a hard failure.
- Formal state is never mutated by verify-only or by this acceptance wave.

## Verifier oracle and failure containment

The product verifier must accept explicit DATA_PROJECT_ROOT, config, state, destination, target fingerprint, and evidence directory. It must never discover/substitute roots. It must:

- Validate config schema and absolute backup_root; resolve real paths and require the destination to be an existing directory contained under the configured backup_root. Reject a symlinked destination root and any path-resolution/read error.
- Enumerate immediate entries with lstat and no symlink following. Reject symlink entries, subdirectories, special files, hidden entries (including .DS_Store/._* and __MACOSX), and every required temporary suffix: .part, .partial, .tmp, .temp, .download, .crdownload, .incomplete, .filepart.
- Require exactly 57 regular recognized image files, no zero bytes, no unrecognized regular files, and no partial/temp/hidden/other entries. Validate MIME/content with the real file command plus a deterministic content/read failure result; command failures are hard failures.
- Emit per-entry relative_path, size, mtime_ns, MIME, SHA-256, and read/error status. Canonical stability compares the complete sorted entry tuples across three samples, including metadata required by the contract, and separately compares total bytes.
- Preserve arbitrary safe filenames (including Unicode, spaces, pipes, and newlines) structurally; never serialize an unescaped delimiter line as the oracle.
- Bind registry association by a single exact group_key + complete fingerprint + destination object and reject absent, ambiguous, cross-entry, or wrong-group matches. Report filesystem, registry, source, state, and overall statuses independently.
- Write evidence only to the supplied evidence directory, with atomic artifact creation and a SHA-256/byte-length manifest. Any exception, read error, command error, malformed state, or failed read-back is nonzero and never prints an overall PASS.

## Verifier negative fixture matrix

Every case runs the product CLI in a fresh isolated project/evidence directory and records an independent expected status; no case modifies DATA_STATE.

| Fixture | Expected filesystem result | Expected overall result |
|---|---|---|
| 57 valid images, exact registry association | PASS | PASS only if source/state are also exact |
| 56 images | FAIL: count mismatch | FAIL |
| 58 images | FAIL: count mismatch | FAIL |
| Each of the eight required temp suffixes | FAIL: partial/temp | FAIL |
| .DS_Store and ._hidden image metadata | FAIL: hidden metadata | FAIL |
| Symlinked destination root | FAIL: unsafe root | FAIL |
| Symlink entry and subdirectory | FAIL: unsafe entry | FAIL |
| Destination outside backup_root | FAIL: containment | FAIL |
| Special file / unreadable entry / file-command error | FAIL: read or command error | FAIL |
| Text bytes named .jpg or MIME/content mismatch | FAIL: unrecognized content | FAIL |
| Unicode, pipe, newline, and space filenames | PASS only if safe and structurally represented | PASS only with exact association |
| mtime or bytes changed between samples | FAIL: unstable inventory | FAIL |
| Wrong group_key with same fingerprint/destination | FAIL: wrong-group registry | FAIL |
| Cross-entry group/fingerprint/destination mix or duplicate matches | FAIL: ambiguous association | FAIL |
| Legacy record without contract_revision/formula calibration | filesystem may PASS | LEGACY_PROVENANCE_LIMITED, not overall PASS |
| Contradictory state axes / stale owner / stale revision | not enough for overall | STATE_CONTRADICTED/FAIL |

The real 56/58 false-positive attempt remains the baseline regression proof; the new cases must execute the product CLI rather than the old script or a self-generated assertion.

## Transaction contract and actual process tests

The product transaction process must use an isolated state path in tests and the formal state contract's separate intent/dispatch/trigger/filesystem/terminal axes. It must:

- Acquire a same-state-directory lock, load and validate the expected schema/revision/owner/run binding, and perform a serialized compare-and-commit. Every mutating commit checks the expected revision and owner/run before writing; stale or competing writers fail closed.
- Use atomic same-directory replacement, fsync where supported, then reopen and validate the committed bytes/schema/revision. A write or read-back uncertainty becomes a durable non-terminal error; it never reopens Save-All/dispatch authority.
- On a fresh prepared intent with dispatch not started, call the injected dispatcher exactly once and persist the returned dispatch outcome. On restart, an intent already committed, returned, or unknown is never dispatched again; UNKNOWN with retry=false remains a barrier.
- Skip a fingerprint already terminally verified in the same exact group/destination association without dispatch. Do not reset a barrier merely because a new run ID or test fixture is created.
- Commit verification, registry addition, terminal run state, and owner release as one guarded state replacement; split/partial commits fail. Preserve original legacy fields during read-only normalization.
- Expose an executable CLI entry point used by subprocess tests. The fake dispatcher writes an independently observed counter and can inject returned, unknown, crash-before-commit, write-failure, read-back-uncertainty, stale-revision, owner-mismatch, and competing-writer outcomes. Tests assert counter, state bytes, revision, intent axes, registry, owner, and terminal status after a real restart.

Required process cases and next-step meaning:

| Case | Independent oracle | Result changes next step |
|---|---|---|
| Fresh prepared dispatch returns | counter=1, intent/dispatch read-back committed | permits bounded continuation to verify/commit |
| Crash after dispatch before commit, then restart | counter remains 1; no second dispatch | proves resume barrier; failure blocks if counter=2 |
| Dispatch UNKNOWN with retry=false | no repeat; UNKNOWN/barrier persists | production route remains blocked |
| Existing terminal exact fingerprint | counter=0; no dispatch; exact duplicate skipped | permits verify-only continuation only |
| Legacy normalization | raw legacy fields preserved; explicit LEGACY_PROVENANCE_LIMITED | source acceptance remains blocked |
| Stale revision / owner/run mismatch | no write and no dispatch | proves contention safety; failure is regression |
| Concurrent acquire/finalize | one guarded winner; loser observes stale/conflict | split ownership is a regression |
| Atomic write failure | no false terminal success | inspect durable error, no retry authority |
| Read-back uncertainty | no DONE/terminal claim and no dispatch retry | closure remains pending/blocked |
| Successful terminal commit | one replacement contains verification+registry+owner release | permits independent acceptance |
| Contradictory state axes | no normalization or dispatch | hard stop and replan if contract changes |

## Runtime and E2E decision

E2E_REQUIRED: NO for this acceptance wave. The primary goal is to accept or stop on an existing destination without redownloading valid 57 files, and the user has not authorized a production download. The documented C04 controller is observation-only and cannot prove a Save-All/chooser/transaction journey; labeling it E2E would be false. Stage 05 remains mandatory for independent acceptance of the real verifier/transaction CLI and the evidence package.

If offline evidence leaves the runtime route materially necessary, the only allowed observation gate is one fresh, read-only CUA session for the exact target. It may observe target binding and one transient menu after at most one already-authorized ellipsis observation; it may not click Save All, open chooser, download, or write state. An affirmative result only identifies a candidate route. A production Save-All attempt would require PLAN_REVISION 3, new independent review, an exact group/album/count/destination gate, a newly created empty destination under DATA_BACKUP_ROOT, and one atomic attempt with no retry after unknown dispatch. No existing valid 57 files may be redownloaded.

## Status and closure matrix

Every material result must preserve these orthogonal subjects:

- PRIMARY_OUTCOME_STATUS: PASS, FAIL, UNKNOWN, or BLOCKED.
- IMPLEMENTATION_STATUS: NOT_STARTED, IN_PROGRESS, COMPLETE, REPLAN_REQUIRED, or IMPLEMENTATION_BLOCKED.
- CORE_ACCEPTANCE_STATUS: PASS, FAIL, BLOCKED, or NOT_RUN.
- REQUIRED_VERIFICATION_STATUS: PASS, FAIL, BLOCKED, or NOT_RUN.
- INDEPENDENT_ACCEPTANCE_STATUS: PASS, FAIL, PENDING, or BLOCKED.
- TASK_CLOSURE_STATUS: IN_PROGRESS, DONE, or BLOCKED.

Required fixtures/assertions cover: canonical incident, implementation defect versus true implementation blocker, CORE fail/blocked/not-run, baseline unavailable and delta, replan after contract change, hard-clean debt, formal waiver preserving the original result, independent acceptance pending/environment blocked/product defect, legacy normalization, contradictory state, and every DONE prerequisite. No agent may self-waive a required gate or convert pending/blocked evidence into DONE. DONE requires exact source CONFIRMED, filesystem/registry/state CORE PASS, required verification PASS, independent acceptance PASS, and no unresolved production-route or implementation blocker.

## Sequencing, review, and stop conditions

Stage 02 must independently review this Revision 2 before implementation or handoff. Stage 03 may compile handoff only for the approved revision/hash. Stage 04 implements only the approved verifier/core wave. Stage 05 independently accepts the real CLI and evidence; it does not modify product code.

Offline read-only reconciliation, isolated fixture construction, baseline reproduction, and plan preparation are authorized now. Product code changes, external formal-state writes, GUI input, deployment, and production download are not authorized by this plan alone. Any semantic contract/gate change increments the same TASK_ID revision and repeats independent review.

STOP/ESCALATE on: unresolved or contradicted source identity; unsafe/ambiguous destination; unknown dispatch; stale/contradictory state; missing implementation surface; failed read-back; inability to run the actual CLI; absence of independent review/acceptance; or any request to reinterpret an old PASS. Do not loop on the same blocker.

## Owner view

Essential: prove whether the existing 57 files can be safely attributed to the exact requested source and prove the real recovery/deduplication behavior before any new GUI side effect. The existing destination's filesystem health is useful but not sufficient. Optional: bridge repair, OCR, historical cleanup. The whole workflow may stop on unresolved source identity, unsafe Save-All targeting, uncertain dispatch, formal-state conflict, missing actual process boundary, or missing independent acceptance because each would make the result non-decision-valid or risk a duplicate/wrong-album action. The largest remaining risk is that the 57 files are valid but their source namespace was never captured.
