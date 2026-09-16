# LINE album acceptance and reusable transaction process — revised candidate plan

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 6
PLAN_STATUS: CANDIDATE
REVIEW_REQUIRED: YES
INDEPENDENT_ACCEPTANCE_REQUIRED: YES
E2E_REQUIRED: NO
ACCEPTED_BY_USER: YES
PRIOR_REVIEW_ATTEMPT: 06
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

PRODUCT_BOUNDARY_DECISION: The task deliverable is an operator-facing reusable local product, not an acceptance-only fixture. Its product owner is the LINE album backup task deliverable; its consumers are the documented operator CLI commands below. The CLI and library are the single real process boundary for verify-only and offline resume/commit/duplicate behavior. The formal data project is an input/state authority and remains read-only. The plan makes no claim that another absent external producer already consumes this module. Any future integration with another producer is a new architecture/contract decision and requires PLAN_REVISION 7 plus independent review.

Planned implementation files, to be created only after this plan is independently approved:

- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/pyproject.toml
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/__init__.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/cli.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/verify.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/transaction.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/README.md

Packaging/build contract:

- Working directory: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Interpreter: /usr/bin/python3
- Test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_*.py' -v
- Verify command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state --config /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json --state /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-product-verify/attempt-01
- Transaction test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_transaction_*.py' -v
- Transaction subprocess entry point: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction resume --state /private/tmp/line-backup-acceptance-case-01/state.json --run-id RUN-CASE-01 --dispatcher /private/tmp/line-backup-acceptance-case-01/dispatcher-returned.py --dispatch-counter /private/tmp/line-backup-acceptance-case-01/dispatch-counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode --dispatcher-outcome RETURNED
- No command in the acceptance artifacts may leave DATA_PROJECT_ROOT, DATA_DESTINATION, TARGET_GROUP_KEY, CASE_ROOT, or EVIDENCE_DIR as an unresolved symbolic placeholder. Recorded argv must contain literal absolute paths.

Operator CLI grammar and product call graph:

- verify-only --project-root PATH --config PATH --state PATH --destination PATH --group-key KEY --start-date ISO --end-date ISO --expected-images INT --evidence-dir PATH
- transaction prepare --state PATH --run-id ID --owner-id ID --group-key KEY --start-date ISO --end-date ISO --expected-images INT --destination PATH --evidence-dir PATH [--test-mode --pause-at ACQUIRE_BEFORE_LOCK --barrier-file PATH]
- transaction resume --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --dispatcher PATH --dispatch-counter PATH --evidence-dir PATH [--no-dispatch] [--test-mode --dispatcher-outcome RETURNED|UNKNOWN --crash-after-dispatch --pause-at NAME --barrier-file PATH]
- transaction commit --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --verification-json PATH --evidence-dir PATH [--test-mode --storage-fault WRITE_BEFORE_REPLACE|READBACK_UNCERTAIN_AFTER_REPLACE]
- transaction finalize --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --outcome VERIFIED|SAFE_ABORT --verification-json PATH --evidence-dir PATH [--test-mode --storage-fault WRITE_BEFORE_REPLACE|READBACK_UNCERTAIN_AFTER_REPLACE]
- transaction duplicate-check --state PATH --group-key KEY --start-date ISO --end-date ISO --expected-images INT --destination PATH --evidence-dir PATH
- status evaluate --input PATH --output PATH

The fixed call graph is cli.main → verify.inspect_filesystem/bind_registry_state_source, or cli.main → transaction prepare/resume/commit/finalize/duplicate-check → storage guarded compare-and-commit → dispatcher adapter only at the final side-effect boundary. The status command calls status.evaluate. Tests invoke the CLI subprocess and never import a second transition model. The package is the operator-facing reusable product for this task; no absent external producer is claimed.

State fixture schema (input precondition only): schema_version=2; contract_revision=1.0-rc2 for new cases; revision; current_run_id; active_writer_id; context_lock; verified_albums; and runs[]. Each run must contain run_id, group_key, destination, fingerprint {start_date,end_date,expected_images}, workflow_outcome, phase, intent_state, dispatch_state, owner_id, intent {intent_state,dispatch_state,trigger_outcome,dispatch_outcome,save_all_retry_allowed}, events, and reconciliations. Case-01's literal initial fixture is recorded at /private/tmp/line-backup-acceptance-case-01/input-state.json with RUN-CASE-01, WRITER-CASE-01, target key line:jp.naver.line.mac:旻謙允禎成長日記, fingerprint 2024-05-13/2024-05-17/57, and destination /private/tmp/line-backup-acceptance-case-01/destination. Fixture creation establishes preconditions only; the independent oracle is computed before product execution.

Concrete case directories and command protocol:

- CASE_ROOT_01=/private/tmp/line-backup-acceptance-case-01 through CASE_ROOT_12=/private/tmp/line-backup-acceptance-case-12 are literal paths, not runtime placeholders. Every case records the expanded argv in inputs.json.
- Case 01 runs prepare → resume RETURNED → commit → finalize VERIFIED with the literal state, verification, evidence, dispatcher and counter paths under CASE_ROOT_01.
- Case 02 runs resume with dispatcher-crash-after-side-effect.py and --crash-after-dispatch, then a fresh resume --no-dispatch under CASE_ROOT_02.
- Case 03 runs dispatcher-unknown.py with --dispatcher-outcome UNKNOWN, then fresh resume --no-dispatch under CASE_ROOT_03.
- Case 04 runs duplicate-check then resume with dispatcher-must-not-run.py under CASE_ROOT_04; expected result is SKIP_DUPLICATE and counter line count 0.
- Case 05 launches two commit subprocesses using expected-revision 1 and expected-owner-id WRITER-CASE-05, both pause at COMMIT_BEFORE_REPLACE on literal barrier /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier; release B first, then A.
- Case 06 invokes commit with expected-owner-id WRITER-CASE-06-WRONG against current owner WRITER-CASE-06; exact result CONFLICT_OWNER_RUN and exit 4.
- Case 07 launches two `transaction prepare` subprocesses against one shared fresh state, each with a distinct run-id/owner-id and the same test-only `--pause-at ACQUIRE_BEFORE_LOCK --barrier-file /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier`; release that one barrier once, then compare one prepared winner with one exact conflict. There is no undeclared acquisition or finalization command.
- Case 08 invokes commit with --test-mode --storage-fault WRITE_BEFORE_REPLACE under CASE_ROOT_08; exact exit 1 and no replacement.
- Case 09 invokes finalize with --test-mode --storage-fault READBACK_UNCERTAIN_AFTER_REPLACE under CASE_ROOT_09, then fresh resume --no-dispatch; exact exit 1 for fault and no dispatch on reload.
- Case 10 invokes finalize --outcome VERIFIED under CASE_ROOT_10 and independently checks one replacement containing verification, registry, workflow_outcome, active_writer_id=null and context_lock=null.
- Cases 11 and 12 use literal legacy and contradictory input-state.json under their case roots; duplicate-check and status evaluate only, with no normalization or dispatch.

Test-only adapter flags are rejected unless --test-mode is present and the state path is under /private/tmp. Storage faults are separate from dispatcher faults. All process commands record stdout, stderr, exit, state/counter bytes and hashes.

## Critical path

1. Preserve/index historical failure evidence and independently reproduce the old verifier's 56/58 false-positive in isolated paths.
2. After Rev6 approval, create the named product package/CLI and tests; prove the package is the only operator process boundary for the new reusable verifier/transaction deliverable.
3. Implement structured fail-closed verify-only and the state/source outcome contract.
4. Implement transaction resume/commit/duplicate paths with shared serialized compare-and-commit, deterministic fault/race injection, and real subprocess restart tests.
5. Run all verifier axis-correct negative cases, transaction cases, status/closure cases, then run the product verifier against DATA_DESTINATION without formal-state mutation.
6. Reconcile current source identity and state/registry/intent/writer evidence. Current default from existing evidence is SOURCE_CORRESPONDENCE=UNRESOLVED and STATE_ASSOCIATION=LEGACY_PROVENANCE_LIMITED; this stops exact goal acceptance while still reporting filesystem findings.
7. Check documented CUA capability and the existing ledger. If route evidence remains necessary, request exactly one fresh controlled observation gate. This gate permits one ellipsis GUI input only, never Save-All/menu-item/chooser/state writes. A later production Save-All route requires PLAN_REVISION 7, fresh review, and a separate one-time production gate.

## Requirement, current evidence, and closure

| Requirement | Current evidence | Rev6 closure | Class | Closure gate |
|---|---|---|---|---|
| Existing destination is 57 complete images | Direct canonical audit reports 57 stable images and 17,924,900 bytes; old verifier is not trustworthy | Product CLI must independently pass filesystem oracle and artifact read-back | CORE / OUTCOME | HARD_CLEAN |
| Exact source correspondence | Request uses 禎; config/state use 楨; legacy run title/provenance UNKNOWN | Emit tri-state result; unresolved/contradicted blocks exact goal acceptance and production route | CORE / OUTCOME | HARD_CLEAN |
| State/registry/intent/writer consistency | State revision 39 is clean, but target run is legacy and lacks full provenance/hash fields | Bind one exact record; report legacy limitations; transaction uses guarded revision/owner commit | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Reusable interruption/recovery/duplicate behavior | Existing fixture is self-authenticating; no actual process exists | New product CLI/library is the real deliverable and must pass subprocess restart/fault/race oracles | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Current Save-All route decision | Historical menu observation found no affirmative Save All; controller/bridge are read-only observation tools | Separate route status from offline acceptance; only controlled observation may establish candidate route | CORE / OUTCOME | HARD_CLEAN |
| Bridge/service | No backup-state integration | Non-gating; deploy only after route-specific causal proof and a later approved plan | SUPPORTING / DIAGNOSTIC | NON_GATING |
| Independent acceptance | Rev1/Rev2/Rev3/Rev4/Rev5 reviews exist; Rev6 review pending | Fresh review of Rev6, then Stage 05 acceptance of actual CLI/evidence | CORE / MUST_NOT_BREAK | HARD_CLEAN |

## Source, registry, and legacy outcome contract

SOURCE_CORRESPONDENCE:

- CONFIRMED: one authoritative record joins exact target app/group key, complete album fingerprint, and destination, or one precise user fact establishes that the raw strings refer to the same source while preserving an immutable evidence-only record. A user fact does not rewrite config/state.
- UNRESOLVED: spelling similarity, a destination match, a fingerprint match, historical GUI evidence without a source join, or a legacy run with unknown title/provenance. Filesystem may be PASS; PRIMARY_OUTCOME_STATUS is UNKNOWN and the source/core check is BLOCKED, so production route is forbidden.
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

## Current formal config and legacy-state compatibility profile

The real verify-only command must accept the current authority without initializing or mutating it. The measured DATA_CONFIG is schema_version=2, 372 bytes, and contains exactly these required keys: schema_version, group_key, group_name, backup_root, app_identifier, max_albums_per_run, recovery_limit, poll_interval_seconds, stable_samples, max_wait_seconds. A config missing any of these required keys, with a wrong type, relative backup_root, wrong app_identifier, or invalid count/sample/wait value is INVALID_CONFIGURATION, exit 2, with filesystem/registry/source/state axes NOT_RUN and no evidence claiming PASS. The current config contains all required keys, so it is not a missing-config case.

Verify-only accepts state schema_version=2 with the current top-level authority fields active_writer_id, context_lock, current_run_id, revision, runs and verified_albums. A run without contract_revision, RC2-only intent fields, or full source title/provenance is a readable LEGACY record, not a new-run default. Missing legacy fields are represented as UNKNOWN or null with the raw run preserved; they are never initialized, rewritten, or treated as affirmative NOT_ATTEMPTED. The current target record therefore produces filesystem findings independently, but its missing contract revision/title/provenance produces STATE=LEGACY_PROVENANCE_LIMITED and SOURCE=UNRESOLVED, not an exact acceptance.

The target argument group key may validly differ from config.group_key during this read-only comparison. That is a valid config plus a source/registry mismatch, not a schema error: with the current requested 禎 key and persisted 楨 key, expected real-command axes are Filesystem=PASS, Registry=FAIL, Source=UNRESOLVED, State=LEGACY_PROVENANCE_LIMITED, Overall=UNKNOWN, exit 4. A config/schema failure is the only case that uses exit 2; an internal read/command/artifact failure uses exit 1. Mutating transaction fixtures use the complete RC2 input schema separately and cannot be used to rewrite current formal state.

## Axis-correct verifier fixture matrix

Each row runs the product CLI in a fresh isolated project/evidence directory and independently checks exact statuses, exit code, output schema, and artifact manifest read-back. No row writes DATA_STATE. Each completed row records result.json, inventory-1.json, inventory-2.json, inventory-3.json when sampling began, manifest.json, stdout.log, stderr.log, and exit-code. Internal artifact failures are a separate class and cannot claim PASS.

| Case | Filesystem | Registry | Source | State | Overall | Exit | Failure class | Artifact read-back |
|---|---|---|---|---|---|---|---|---|
| 57 valid images and exact association | PASS | PASS | CONFIRMED | EXACT | PASS | 0 | NONE | PASS |
| 56 images | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| 58 images | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .part file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .partial file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .tmp file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .temp file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .download file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .crdownload file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .incomplete file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .filepart file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| .DS_Store, ._hidden, or __MACOSX | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Symlinked destination root/ancestor or symlink entry | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Destination outside backup_root | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Special file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Unreadable regular file | FAIL | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_READ_ERROR | PASS |
| file-command failure | FAIL | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_COMMAND_ERROR | PASS |
| Text bytes named .jpg or MIME/content mismatch | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Safe Unicode/pipe/newline/space filenames | PASS | PASS | CONFIRMED | EXACT | PASS | 0 | NONE | PASS |
| mtime changed at SAMPLE_2_READY barrier | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| bytes changed at SAMPLE_2_READY barrier | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Wrong group_key with valid files and same fingerprint/destination | PASS | FAIL | CONTRADICTED | EXACT | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Cross-entry group/fingerprint/destination mix | PASS | FAIL | UNRESOLVED | STATE_CONTRADICTED | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Legacy record without contract_revision/formula calibration | PASS | EXACT | UNRESOLVED | LEGACY_PROVENANCE_LIMITED | UNKNOWN | 4 | INPUT_PROVENANCE_LIMITED | PASS |
| Duplicate registry entries | PASS | FAIL | UNRESOLVED | AMBIGUOUS | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Invalid invocation/configuration | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | UNKNOWN | 2 | INVALID_INPUT | PASS |
| Evidence manifest write/read-back failure | PASS | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_ARTIFACT_ERROR | FAIL_WITH_ERROR_ARTIFACT |

A row with an internal read/command/artifact error has exact UNKNOWN overall because the verifier cannot safely conclude the requested result. No alternative exit is permitted. A result-schema test rejects any value from another subject enum, such as NOT_ACHIEVED in the State axis or EXACT in the Filesystem axis. Filesystem PASS never implies registry/source/state PASS; registry/source-only defects retain filesystem PASS.

## Transaction product contract and deterministic acceptance matrix

The operator-facing transaction CLI is the product process. The package contains no second test transaction model.

Fixed state and serialization protocol:

- For state path P, every prepare/resume/commit/finalize/duplicate operation uses the exact lock path dirname(P)/.line-backup-state.lock and POSIX flock LOCK_EX. The lock is acquired before authoritative load and held through expected-revision/owner validation, replacement, fsync/read-back and release. duplicate-check uses the same lock for its final association read.
- A commit accepts only when loaded revision equals expected-revision, current_run_id equals expected-run-id, active_writer_id equals expected-owner-id for non-terminal mutation, and immutable intent/dispatch/trigger fields equal the prepared payload. Mismatch returns one exact conflict result with exit 4, writes nothing and never dispatches.
- A prepare accepts only when the loaded state has no active current_run/owner/context lock for the requested acquisition scope. If another prepare wins first, the loser returns exactly `CONFLICT_ACTIVE_RUN`, exit 4, writes no replacement and does not create a second run/owner record. The winner identity is intentionally scheduling-independent and is recorded only after the independent post-state read.
- Replacement uses a same-directory temp file, fsyncs it, os.replace, fsyncs the directory when supported, reopens and validates schema/revision/owner/run/intent/registry/terminal fields, and records available durability protection.
- The shared lock covers acquire, resume, commit, finalize, duplicate skip and cleanup. A delayed payload cannot commit after a competing winner. Deterministic barrier files, not timing or sleep, control race order.
- Storage faults are separate from dispatcher faults: WRITE_BEFORE_REPLACE fails before replacement; READBACK_UNCERTAIN_AFTER_REPLACE replaces then returns an uncertainty result. A fresh resume with --no-dispatch reloads authoritative state and never replays a prepared dispatch.
- The injected dispatcher writes one JSON line to an independently read counter before returning or exiting. The product never reads that counter to decide success. The fake is injected only at the final side-effect adapter.
- Only finalize can set VERIFIED or final SAFE_ABORT. It commits verification, registry when applicable, workflow outcome, terminal evidence, active_writer_id=null and context_lock=null in one guarded replacement. Terminal exact duplicate-check returns SKIP_DUPLICATE and never dispatches.
- New runs use contract_revision=1.0-rc2 and preserve separate intent_state, dispatch_state, trigger_outcome, dispatch_outcome, retry permission, evidence, events and reconciliations. Legacy records are read-only normalized in reports.

Exact subprocess command grammar and case protocol:

- Case roots are literal /private/tmp/line-backup-acceptance-case-01 through /private/tmp/line-backup-acceptance-case-12. Every recorded inputs.json contains fully expanded argv; the documentation names are never passed to the process as variables.
- Prepare command uses transaction prepare with state, run-id, owner-id, exact group-key, dates, count, destination and evidence-dir.
- Resume command uses transaction resume with state, run-id, expected-revision, expected-owner-id, dispatcher, dispatch-counter and evidence-dir. --no-dispatch is required on every restart/reload path. --test-mode is accepted only for case roots and must name one explicit dispatcher outcome, pause barrier or fault.
- Commit command uses transaction commit with state, run-id, expected-revision, expected-owner-id, verification-json and evidence-dir. Finalization uses transaction finalize with the same expected revision/owner, explicit outcome VERIFIED or SAFE_ABORT, verification-json and evidence-dir.
- Duplicate command uses transaction duplicate-check with exact group-key, dates, count, destination and evidence-dir. It is read-only.
- Status command uses status evaluate with a literal case input and output path. It is read-only.
- The exact Case-01 argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction resume --state /private/tmp/line-backup-acceptance-case-01/state.json --run-id RUN-CASE-01 --expected-revision 1 --expected-owner-id WRITER-CASE-01 --dispatcher /private/tmp/line-backup-acceptance-case-01/dispatcher-returned.py --dispatch-counter /private/tmp/line-backup-acceptance-case-01/dispatch-counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode --dispatcher-outcome RETURNED.
- The exact Case-01 prepare argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction prepare --state /private/tmp/line-backup-acceptance-case-01/state.json --run-id RUN-CASE-01 --owner-id WRITER-CASE-01 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-01/destination --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence.
- The exact Case-01 commit argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction commit --state /private/tmp/line-backup-acceptance-case-01/state.json --run-id RUN-CASE-01 --expected-revision 2 --expected-owner-id WRITER-CASE-01 --verification-json /private/tmp/line-backup-acceptance-case-01/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence.
- The exact Case-01 finalize argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction finalize --state /private/tmp/line-backup-acceptance-case-01/state.json --run-id RUN-CASE-01 --expected-revision 3 --expected-owner-id WRITER-CASE-01 --outcome VERIFIED --verification-json /private/tmp/line-backup-acceptance-case-01/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence.
- The exact Case-04 duplicate argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction duplicate-check --state /private/tmp/line-backup-acceptance-case-04/state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-04/destination --evidence-dir /private/tmp/line-backup-acceptance-case-04/evidence.
- The exact Case-07 prepare argv pair is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction prepare --state /private/tmp/line-backup-acceptance-case-07/state.json --run-id RUN-CASE-07-A --owner-id WRITER-CASE-07-A --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-07/destination --evidence-dir /private/tmp/line-backup-acceptance-case-07/evidence-a --test-mode --pause-at ACQUIRE_BEFORE_LOCK --barrier-file /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier; and the identical argv with RUN-CASE-07-B, WRITER-CASE-07-B, and `--evidence-dir /private/tmp/line-backup-acceptance-case-07/evidence-b`. The independent driver starts both from the same pre-state, releases the single literal barrier once, and expects exactly one `PREPARED` result and exactly one `CONFLICT_ACTIVE_RUN` exit 4. Either A or B may win; the driver records winner/loser identities and independently proves one state replacement only.
- Cases 02/03 use dispatcher-crash-after-side-effect.py or dispatcher-unknown.py and then a fresh literal resume --no-dispatch. Case 05 uses barrier /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier and releases it once. Case 07 uses only the single barrier /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier and has no fixed scheduler-selected winner.
- Case 08 uses commit --test-mode --storage-fault WRITE_BEFORE_REPLACE and has exact exit 1. Case 09 uses finalize --test-mode --storage-fault READBACK_UNCERTAIN_AFTER_REPLACE, exact exit 1, then fresh resume --no-dispatch.
- Cases 11/12 use literal legacy/contradictory input JSON and status evaluate/duplicate-check only. No test helper implements a transition.

Deterministic driver and literal case protocol:

- `tests/acceptance_case_driver.py` is only a subprocess orchestrator and independent oracle; it does not contain a transition model or write expected transition values into product state. Every case driver invocation uses literal absolute paths for `pre-state.json`, `state.json`, `post-state.json`, `counter.jsonl`, `result.json`, `manifest.json`, `stdout.log`, `stderr.log`, `exit-code` and `evidence/`. It writes preconditions, hashes them, invokes the real CLI argv, captures each process's raw stdout/stderr/exit, independently reads post-state/counter/result/manifest, and computes expected outcomes from the case specification before inspecting product output.
- The exact driver argv for every case is:
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 01 --case-root /private/tmp/line-backup-acceptance-case-01 --pre-state /private/tmp/line-backup-acceptance-case-01/pre-state.json --state /private/tmp/line-backup-acceptance-case-01/state.json --post-state /private/tmp/line-backup-acceptance-case-01/post-state.json --counter /private/tmp/line-backup-acceptance-case-01/counter.jsonl --result /private/tmp/line-backup-acceptance-case-01/result.json --manifest /private/tmp/line-backup-acceptance-case-01/manifest.json --stdout /private/tmp/line-backup-acceptance-case-01/stdout.log --stderr /private/tmp/line-backup-acceptance-case-01/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-01/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 02 --case-root /private/tmp/line-backup-acceptance-case-02 --pre-state /private/tmp/line-backup-acceptance-case-02/pre-state.json --state /private/tmp/line-backup-acceptance-case-02/state.json --post-state /private/tmp/line-backup-acceptance-case-02/post-state.json --counter /private/tmp/line-backup-acceptance-case-02/counter.jsonl --result /private/tmp/line-backup-acceptance-case-02/result.json --manifest /private/tmp/line-backup-acceptance-case-02/manifest.json --stdout /private/tmp/line-backup-acceptance-case-02/stdout.log --stderr /private/tmp/line-backup-acceptance-case-02/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-02/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-02/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 03 --case-root /private/tmp/line-backup-acceptance-case-03 --pre-state /private/tmp/line-backup-acceptance-case-03/pre-state.json --state /private/tmp/line-backup-acceptance-case-03/state.json --post-state /private/tmp/line-backup-acceptance-case-03/post-state.json --counter /private/tmp/line-backup-acceptance-case-03/counter.jsonl --result /private/tmp/line-backup-acceptance-case-03/result.json --manifest /private/tmp/line-backup-acceptance-case-03/manifest.json --stdout /private/tmp/line-backup-acceptance-case-03/stdout.log --stderr /private/tmp/line-backup-acceptance-case-03/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-03/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-03/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 04 --case-root /private/tmp/line-backup-acceptance-case-04 --pre-state /private/tmp/line-backup-acceptance-case-04/pre-state.json --state /private/tmp/line-backup-acceptance-case-04/state.json --post-state /private/tmp/line-backup-acceptance-case-04/post-state.json --counter /private/tmp/line-backup-acceptance-case-04/counter.jsonl --result /private/tmp/line-backup-acceptance-case-04/result.json --manifest /private/tmp/line-backup-acceptance-case-04/manifest.json --stdout /private/tmp/line-backup-acceptance-case-04/stdout.log --stderr /private/tmp/line-backup-acceptance-case-04/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-04/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-04/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 05 --case-root /private/tmp/line-backup-acceptance-case-05 --pre-state /private/tmp/line-backup-acceptance-case-05/pre-state.json --state /private/tmp/line-backup-acceptance-case-05/state.json --post-state /private/tmp/line-backup-acceptance-case-05/post-state.json --counter /private/tmp/line-backup-acceptance-case-05/counter.jsonl --result /private/tmp/line-backup-acceptance-case-05/result.json --manifest /private/tmp/line-backup-acceptance-case-05/manifest.json --stdout /private/tmp/line-backup-acceptance-case-05/stdout.log --stderr /private/tmp/line-backup-acceptance-case-05/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-05/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-05/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 06 --case-root /private/tmp/line-backup-acceptance-case-06 --pre-state /private/tmp/line-backup-acceptance-case-06/pre-state.json --state /private/tmp/line-backup-acceptance-case-06/state.json --post-state /private/tmp/line-backup-acceptance-case-06/post-state.json --counter /private/tmp/line-backup-acceptance-case-06/counter.jsonl --result /private/tmp/line-backup-acceptance-case-06/result.json --manifest /private/tmp/line-backup-acceptance-case-06/manifest.json --stdout /private/tmp/line-backup-acceptance-case-06/stdout.log --stderr /private/tmp/line-backup-acceptance-case-06/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-06/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-06/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 07 --case-root /private/tmp/line-backup-acceptance-case-07 --pre-state /private/tmp/line-backup-acceptance-case-07/pre-state.json --state /private/tmp/line-backup-acceptance-case-07/state.json --post-state /private/tmp/line-backup-acceptance-case-07/post-state.json --counter /private/tmp/line-backup-acceptance-case-07/counter.jsonl --result /private/tmp/line-backup-acceptance-case-07/result.json --manifest /private/tmp/line-backup-acceptance-case-07/manifest.json --stdout /private/tmp/line-backup-acceptance-case-07/stdout.log --stderr /private/tmp/line-backup-acceptance-case-07/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-07/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-07/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 08 --case-root /private/tmp/line-backup-acceptance-case-08 --pre-state /private/tmp/line-backup-acceptance-case-08/pre-state.json --state /private/tmp/line-backup-acceptance-case-08/state.json --post-state /private/tmp/line-backup-acceptance-case-08/post-state.json --counter /private/tmp/line-backup-acceptance-case-08/counter.jsonl --result /private/tmp/line-backup-acceptance-case-08/result.json --manifest /private/tmp/line-backup-acceptance-case-08/manifest.json --stdout /private/tmp/line-backup-acceptance-case-08/stdout.log --stderr /private/tmp/line-backup-acceptance-case-08/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-08/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-08/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 09 --case-root /private/tmp/line-backup-acceptance-case-09 --pre-state /private/tmp/line-backup-acceptance-case-09/pre-state.json --state /private/tmp/line-backup-acceptance-case-09/state.json --post-state /private/tmp/line-backup-acceptance-case-09/post-state.json --counter /private/tmp/line-backup-acceptance-case-09/counter.jsonl --result /private/tmp/line-backup-acceptance-case-09/result.json --manifest /private/tmp/line-backup-acceptance-case-09/manifest.json --stdout /private/tmp/line-backup-acceptance-case-09/stdout.log --stderr /private/tmp/line-backup-acceptance-case-09/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-09/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-09/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 10 --case-root /private/tmp/line-backup-acceptance-case-10 --pre-state /private/tmp/line-backup-acceptance-case-10/pre-state.json --state /private/tmp/line-backup-acceptance-case-10/state.json --post-state /private/tmp/line-backup-acceptance-case-10/post-state.json --counter /private/tmp/line-backup-acceptance-case-10/counter.jsonl --result /private/tmp/line-backup-acceptance-case-10/result.json --manifest /private/tmp/line-backup-acceptance-case-10/manifest.json --stdout /private/tmp/line-backup-acceptance-case-10/stdout.log --stderr /private/tmp/line-backup-acceptance-case-10/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-10/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-10/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 11 --case-root /private/tmp/line-backup-acceptance-case-11 --pre-state /private/tmp/line-backup-acceptance-case-11/pre-state.json --state /private/tmp/line-backup-acceptance-case-11/state.json --post-state /private/tmp/line-backup-acceptance-case-11/post-state.json --counter /private/tmp/line-backup-acceptance-case-11/counter.jsonl --result /private/tmp/line-backup-acceptance-case-11/result.json --manifest /private/tmp/line-backup-acceptance-case-11/manifest.json --stdout /private/tmp/line-backup-acceptance-case-11/stdout.log --stderr /private/tmp/line-backup-acceptance-case-11/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-11/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-11/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 12 --case-root /private/tmp/line-backup-acceptance-case-12 --pre-state /private/tmp/line-backup-acceptance-case-12/pre-state.json --state /private/tmp/line-backup-acceptance-case-12/state.json --post-state /private/tmp/line-backup-acceptance-case-12/post-state.json --counter /private/tmp/line-backup-acceptance-case-12/counter.jsonl --result /private/tmp/line-backup-acceptance-case-12/result.json --manifest /private/tmp/line-backup-acceptance-case-12/manifest.json --stdout /private/tmp/line-backup-acceptance-case-12/stdout.log --stderr /private/tmp/line-backup-acceptance-case-12/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-12/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-12/evidence`
- The driver has one literal product argv array per process. Cases 01–04 and 06, 08–10, 11–12 use the exact CLI grammar above with the literal `/private/tmp/line-backup-acceptance-case-N/...` paths; Cases 05 and 07 launch the two literal argv arrays specified by the case protocol. No case uses a symbolic `CASE_ROOT`, `EVIDENCE_DIR`, or a dynamically generated command string.

Exact process-specific protocol, expected outcome, and next-step decision:

- Case 01 runs the literal prepare/resume/commit/finalize argv already shown, expects revisions 1→2→3→4 and final VERIFIED; any mismatch stops the implementation wave as a transaction regression, while a match permits Cases 02–04.
- Case 02 runs `transaction resume --state /private/tmp/line-backup-acceptance-case-02/state.json --run-id RUN-CASE-02 --expected-revision 1 --expected-owner-id WRITER-CASE-02 --dispatcher /private/tmp/line-backup-acceptance-case-02/dispatcher-crash-after-side-effect.py --dispatch-counter /private/tmp/line-backup-acceptance-case-02/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-02/evidence --test-mode --dispatcher-outcome RETURNED --crash-after-dispatch`, then fresh `transaction resume --state /private/tmp/line-backup-acceptance-case-02/state.json --run-id RUN-CASE-02 --expected-revision 2 --expected-owner-id WRITER-CASE-02 --dispatcher /private/tmp/line-backup-acceptance-case-02/dispatcher-crash-after-side-effect.py --dispatch-counter /private/tmp/line-backup-acceptance-case-02/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-02/evidence --no-dispatch`; counter must remain exactly 1 and the second process must not dispatch, otherwise recovery acceptance stops.
- Case 03 runs `transaction resume --state /private/tmp/line-backup-acceptance-case-03/state.json --run-id RUN-CASE-03 --expected-revision 1 --expected-owner-id WRITER-CASE-03 --dispatcher /private/tmp/line-backup-acceptance-case-03/dispatcher-unknown.py --dispatch-counter /private/tmp/line-backup-acceptance-case-03/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-03/evidence --test-mode --dispatcher-outcome UNKNOWN`, then fresh `transaction resume --state /private/tmp/line-backup-acceptance-case-03/state.json --run-id RUN-CASE-03 --expected-revision 2 --expected-owner-id WRITER-CASE-03 --dispatcher /private/tmp/line-backup-acceptance-case-03/dispatcher-unknown.py --dispatch-counter /private/tmp/line-backup-acceptance-case-03/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-03/evidence --no-dispatch`; counter must be exactly 1, dispatch_outcome UNKNOWN and retry permission false, otherwise no retry interpretation is allowed.
- Case 04 runs the exact duplicate-check argv already shown, then `transaction resume --state /private/tmp/line-backup-acceptance-case-04/state.json --run-id RUN-CASE-04 --expected-revision 7 --expected-owner-id WRITER-CASE-04 --dispatcher /private/tmp/line-backup-acceptance-case-04/dispatcher-must-not-run.py --dispatch-counter /private/tmp/line-backup-acceptance-case-04/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-04/evidence --test-mode --dispatcher-outcome RETURNED`; both results must be SKIP_DUPLICATE, exit 0 and counter line count 0, otherwise duplicate protection stops.
- Case 05 launches two literal `transaction commit --state /private/tmp/line-backup-acceptance-case-05/state.json --run-id RUN-CASE-05 --expected-revision 1 --expected-owner-id WRITER-CASE-05 --verification-json /private/tmp/line-backup-acceptance-case-05/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-05/evidence-a --test-mode --pause-at COMMIT_BEFORE_REPLACE --barrier-file /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier` and the identical argv with `--evidence-dir /private/tmp/line-backup-acceptance-case-05/evidence-b`; the driver starts both from the same pre-state, executes `/usr/bin/touch /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier` once, and requires exactly one commit winner plus one `CONFLICT_STALE_REVISION`, with one replacement only.
- Case 06 runs `transaction commit --state /private/tmp/line-backup-acceptance-case-06/state.json --run-id RUN-CASE-06 --expected-revision 1 --expected-owner-id WRITER-CASE-06-WRONG --verification-json /private/tmp/line-backup-acceptance-case-06/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-06/evidence`; exact result is CONFLICT_OWNER_RUN, exit 4 and no replacement.
- Case 07 launches the two literal prepare argv arrays above with shared state and one barrier, executes `/usr/bin/touch /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier` once, and requires exactly one PREPARED exit 0 and exactly one CONFLICT_ACTIVE_RUN exit 4. Either A or B may win; the driver records both identities and independently proves the loser did not replace state.
- Case 08 runs `transaction commit --state /private/tmp/line-backup-acceptance-case-08/state.json --run-id RUN-CASE-08 --expected-revision 1 --expected-owner-id WRITER-CASE-08 --verification-json /private/tmp/line-backup-acceptance-case-08/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-08/evidence --test-mode --storage-fault WRITE_BEFORE_REPLACE`; exact exit is 1, state bytes/revision are unchanged and no terminal evidence is emitted.
- Case 09 runs `transaction finalize --state /private/tmp/line-backup-acceptance-case-09/state.json --run-id RUN-CASE-09 --expected-revision 2 --expected-owner-id WRITER-CASE-09 --outcome VERIFIED --verification-json /private/tmp/line-backup-acceptance-case-09/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-09/evidence --test-mode --storage-fault READBACK_UNCERTAIN_AFTER_REPLACE`, then fresh `transaction resume --state /private/tmp/line-backup-acceptance-case-09/state.json --run-id RUN-CASE-09 --expected-revision 3 --expected-owner-id WRITER-CASE-09 --dispatcher /private/tmp/line-backup-acceptance-case-09/dispatcher-must-not-run.py --dispatch-counter /private/tmp/line-backup-acceptance-case-09/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-09/evidence --no-dispatch`; fault exit is 1, reload never dispatches and state remains explicitly uncertain/non-terminal.
- Case 10 runs `transaction finalize --state /private/tmp/line-backup-acceptance-case-10/state.json --run-id RUN-CASE-10 --expected-revision 2 --expected-owner-id WRITER-CASE-10 --outcome VERIFIED --verification-json /private/tmp/line-backup-acceptance-case-10/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-10/evidence`; exact exit is 0 and the independently read replacement has verification, registry, workflow_outcome=VERIFIED, active_writer_id=null and context_lock=null.
- Case 11 runs `status evaluate --input /private/tmp/line-backup-acceptance-case-11/legacy-input.json --output /private/tmp/line-backup-acceptance-case-11/result.json` and `transaction duplicate-check --state /private/tmp/line-backup-acceptance-case-11/state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-11/destination --evidence-dir /private/tmp/line-backup-acceptance-case-11/evidence`; exact result is legacy-limited/unknown with no normalization or dispatch.
- Case 12 runs `status evaluate --input /private/tmp/line-backup-acceptance-case-12/contradictory-input.json --output /private/tmp/line-backup-acceptance-case-12/result.json` and `transaction duplicate-check --state /private/tmp/line-backup-acceptance-case-12/state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-12/destination --evidence-dir /private/tmp/line-backup-acceptance-case-12/evidence`; exact result is STATE_CONTRADICTED/NOT_ACHIEVED, exit 4 and no normalization or dispatch.
- A case is accepted only when its literal process exit(s), independently computed post-state/counter/hash oracle and manifest read-back match. A pass moves to the next case; Case 01/04/06/08/09/10/11/12 failures are product/test regressions, Case 02/03 failures stop recovery acceptance, and Case 05/07 failures stop concurrency acceptance and prohibit production use. A pre-existing environment failure is REQUIRED_VERIFICATION=INCOMPLETE with baseline evidence, never product PASS.

- Before execution, independently hash case.json/input-state.json and record byte length. After every process, independently hash state bytes, counter lines, stdout, stderr, exit, result and manifest.
- The expected revision delta, counter line count, intent/dispatch/trigger values, registry, owner release, terminal outcome and retry permission are computed from the case specification before reading product output.
- Case 02 counter is exactly 1 after restart; case 03 exactly 1 with UNKNOWN/retry=false; case 04 exactly 0; case 05 and 07 exactly one winner/one conflict; case 08 no replacement; case 09 no terminal success and no dispatch on reload; case 10 one guarded terminal replacement. Any deviation is TASK_REGRESSION.
- Every case retains case.json, inputs.json, pre-state.json/hash, post-state.json/hash, counter.jsonl/hash, stdout.log, stderr.log, exit-code, result.json and manifest.json. A product PASS line is never an oracle.



## Runtime route, ledger authority, GUI gate, and truthful E2E decision

E2E_REQUIRED: NO for this wave. The primary object is an existing destination that must not be redownloaded, and no production download is authorized. A CUA/controller session includes one ellipsis GUI input and is not full user-journey E2E. Stage 05 independent acceptance remains mandatory for the actual CLI, transaction process, evidence package and route status.

Authoritative historical ledger scope and budget:

- Action ledger: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/actions.jsonl, 4,219 bytes, SHA-256 9d6a159024f822003052fd7d538598d3a161f226c49ce14ea5c11d5c95c95aee. It records exactly two ellipsis inputs, no menu-item/Save-All click and no state write.
- Budget authority: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/environment.json, 4,555 bytes, SHA-256 a43d23d6166a3d2156c5e3a1ccd08cc394b8b283f9c3a2d007929db986922c95. It records the exact bundle/target and ellipsis_clicks_used=2, ellipsis_click_budget=2.
- Target scope: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/scope.json, 1,026 bytes, SHA-256 6bb8795ecc1beac3d8ba49c79fd032ff1f1459fb7784fc4cb000a84ae7fe5aaa.
- The historical 2/2 budget is exhausted. A new observation cannot append or reset it. A fresh run-specific ledger and one explicit user gate are required.

New run ledger and route-result schema:

- New private JSONL ledger schema_version=1 includes run_id, runtime/provider, app_bundle, raw_group, album, expected_count, project_root, parent_ledger_sha256, initial_input_counts, events, final_counts and route_result_sha256.
- Every event includes timestamp, action_class, event, gui_input, surface, target_binding_sha256, allowed_budget_before/after, menu_item_click, save_all_click, chooser_interaction, backup_state_write and evidence paths. App acquisition/navigation inputs are counted separately from the exactly-one permitted target ellipsis input; no unlisted input is allowed.
- Before the Human Gate, app acquisition and navigation are read-only and have GUI-input budgets of 0. After the gate, the user must already present the exact target album card; the controlled run has `app_acquisition_input_budget=0`, `navigation_input_budget=0`, and `ellipsis_input_budget=1`. If the exact target cannot be read in the current surface without navigation or extra input, the run records SAFE_ABORT and requests no additional action in this wave.
- New ellipsis budget is exactly 1 only after explicit authorization. The sequence is target-binding read → one current-target ellipsis input → immediate post observation → stop. No input may bring LINE to front, navigate, scroll, select an album, choose a menu item, invoke Save-All, open a chooser, or write backup state.
- route-result.json includes documented_capability_ref, runtime/provider, app_bundle, raw group, album, count, project_root, parent/new ledger SHA, target-binding SHA, pre/post observation SHAs, exact candidate text/role/subrole/bounds/owner, same-item correlation, save_all_click_count=0, menu_item_click_count=0, chooser_state, backup_state_write_count=0, route_status=AFFIRMATIVE|UNKNOWN|SAFE_ABORT, decision and reason.
- Missing, ambiguous, stale, uncorrelated or provider-mismatched evidence yields route_status=UNKNOWN and SAFE_ABORT. Historical coordinates and OCR-only evidence cannot yield AFFIRMATIVE.

The single Human Gate, if route evidence remains necessary, authorizes exactly this controlled experiment:

- App/bundle: LINE, jp.naver.line.mac.
- Raw target: 旻謙允禎成長日記; album: 2024/05/13～05/17; expected count: 57.
- Data/project root: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state, explicitly confirmed.
- Surface: exact target album card and its ellipsis popup/menu only.
- Permitted input: exactly one current-target ellipsis input, no guessed coordinate and no low-level AXPress/AXUIElementPerformAction; no menu-item, Save-All, chooser, keyboard shortcut or state input/write.
- Capture immediate post evidence and stop. This is not production authorization.
- Production Save-All requires PLAN_REVISION 7, fresh independent review, a newly created empty destination under /Users/hsiaojohnny/Downloads/LINE-Backup-PoC, exact group/album/count/destination gate and one atomic attempt with no retry after UNKNOWN. Existing valid 57 files may not be redownloaded.

Legal separation: offline CLI acceptance, controlled GUI route observation and later production Save-All are separate checks and artifacts. If exact existing source is proven and no side effect is needed, ROUTE_NOT_NEEDED may be recorded with explicit Plan rationale; otherwise route is a scoped CORE blocker. Production results cannot retroactively complete this wave.

## Canonical Status Contract v2, routing fixtures, and blockers

All execution/review/acceptance artifacts use Status Contract v2 exactly:

PRIMARY_OUTCOME_STATUS: ACHIEVED | NOT_ACHIEVED | UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | ESCALATED
CORE_ACCEPTANCE_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED | INCOMPLETE | WAIVED
INDEPENDENT_ACCEPTANCE_STATUS: NOT_REQUIRED | PENDING | PASS | FAIL | BLOCKED
TASK_CLOSURE_STATUS: IN_PROGRESS | PENDING_CORE_ACCEPTANCE | CORE_ACCEPTANCE_BLOCKED | READY_FOR_INDEPENDENT_ACCEPTANCE | PENDING_REQUIRED_VERIFICATION | FIX_REQUIRED | REPLAN_REQUIRED | IMPLEMENTATION_BLOCKED | ACCEPTANCE_BLOCKED | DONE

Every material check includes CHECK_ID, GOAL_CRITICALITY, EVIDENCE_ROLE, CLOSURE_GATE, BASELINE_REQUIRED, FAILURE_CLASSIFICATION_RULE, WAIVER_ALLOWED, WAIVER_AUTHORITY, CHECK_RESULT and WAIVER_STATUS. This is Plan-time policy; no agent can approve its own waiver.

| CHECK_ID | Criticality | Evidence role | Gate | Baseline | Failure classification | Waiver allowed | Authority | Check result | Waiver status |
|---|---|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | YES | old false acceptance not reproduced invalidates baseline | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | YES | incorrect axis/exit/artifact or false acceptance is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | malformed/unsafe acceptance or axis conflation is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | repeat dispatch or barrier bypass is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | stale/split/uncertain commit or false terminality is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | YES | formal mutation or contradiction is TASK_REGRESSION/BLOCKED | NO | NONE | NOT_RUN | NOT_ALLOWED |
| SOURCE_CORRESPONDENCE | CORE | OUTCOME | HARD_CLEAN | YES | missing authority is scoped BLOCKED/UNRESOLVED; contradiction is FAIL | NO | NONE | NOT_RUN | NOT_ALLOWED |
| CUA_ROUTE_DECISION | CORE | OUTCOME | HARD_CLEAN | YES | missing/ambiguous route evidence is scoped BLOCKED/UNKNOWN; no dispatch | NO | NONE | NOT_RUN | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | illegal enum/routing/self-waiver is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | missing independent result remains PENDING/BLOCKED | NO | NONE | NOT_RUN | NOT_ALLOWED |
| BASELINE_REGRESSION_DELTA | CORE | MUST_NOT_BREAK | BASELINE_DELTA | YES | rerunning the identical command/environment shows a new or worsened failure signature, or an old signature is silently omitted | NO | NONE | NOT_RUN | NOT_ALLOWED |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | non-gating unless route-specific necessity is proved | YES | Project owner, exact scope | NOT_RUN | NOT_REQUESTED |
| DOCUMENTATION_RETENTION_HEALTH | SUPPORTING | REPOSITORY_HEALTH | HARD_CLEAN | NO | within the exact task-evidence scope, missing raw commands, stdout/stderr/exit, or manifest/hash read-back would make independent acceptance non-reproducible and could invalidate provenance; unrelated repository documentation never enters this gate | YES | Project owner, exact scope | NOT_RUN | NOT_REQUESTED |

`BASELINE_REGRESSION_DELTA` has a pre-change artifact SHA-256, byte length, exact command argv, working directory, interpreter/environment fingerprint, and captured pre-change result/signatures. The post-change run repeats that same argv and environment; `baseline_delta=UNCHANGED` means every pre-existing signature is still disclosed with identical classification and no new/worsened signature exists, while `baseline_delta=WORSENED` is a hard failure. A baseline artifact that is absent or unreadable is `REQUIRED_VERIFICATION=INCOMPLETE`, not PASS. The baseline row is independently checked and never inferred from a product PASS line.

Executable status fixtures invoke status evaluate with a literal input JSON and compare all six statuses, scoped blocker, check metadata, baseline/failure class, waiver fields and closure. Required cases:

| Fixture | Primary | Implementation | Core | Required verification | Independent acceptance | Closure | Exact blocker/routing |
|---|---|---|---|---|---|---|---|
| Candidate before implementation | UNKNOWN | NOT_STARTED | NOT_RUN | NOT_RUN | PENDING | IN_PROGRESS | none |
| Approved implementation cannot continue | UNKNOWN | BLOCKED | NOT_RUN | NOT_RUN | PENDING | IMPLEMENTATION_BLOCKED | IMPLEMENTATION/BLOCKED/ENVIRONMENT_FAILURE |
| New evidence invalidates plan | UNKNOWN | ESCALATED | NOT_RUN | NOT_RUN | PENDING | REPLAN_REQUIRED | IMPLEMENTATION/BLOCKED/TASK_REGRESSION |
| Complete implementation, CORE not run | UNKNOWN | COMPLETE | NOT_RUN | NOT_RUN | PENDING | PENDING_CORE_ACCEPTANCE | CORE_ACCEPTANCE/NOT_RUN/INPUT_UNAVAILABLE |
| Complete implementation, CORE blocked | UNKNOWN | COMPLETE | BLOCKED | NOT_RUN | PENDING | CORE_ACCEPTANCE_BLOCKED | CORE_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED |
| Complete implementation, CORE fail | NOT_ACHIEVED | IN_PROGRESS | FAIL | NOT_RUN | PENDING | FIX_REQUIRED | CORE_ACCEPTANCE/FAIL/TASK_REGRESSION |
| CORE pass with unchanged baseline delta and required checks pass | ACHIEVED | COMPLETE | PASS | PASS | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | no blocker; baseline_delta=UNCHANGED |
| Canonical incident with pre-existing hard-clean debt | ACHIEVED | COMPLETE | PASS | INCOMPLETE | PENDING | PENDING_REQUIRED_VERIFICATION | REQUIRED_VERIFICATION/BLOCKED/PRE_EXISTING_REPOSITORY_FAILURE |
| CORE pass, baseline unavailable | ACHIEVED | COMPLETE | PASS | INCOMPLETE | PENDING | PENDING_REQUIRED_VERIFICATION | REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE |
| All required items formally waived | ACHIEVED | COMPLETE | PASS | WAIVED | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | waiver APPROVED by named authority |
| Reachable waiver for scoped non-core retention debt | ACHIEVED | COMPLETE | PASS | WAIVED | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | DOCUMENTATION_RETENTION_HEALTH original FAIL preserved; waiver APPROVED with scope/rationale/evidence/residual-risk/expiry |
| Stage 05 environment/input block | ACHIEVED | COMPLETE | PASS | PASS | BLOCKED | ACCEPTANCE_BLOCKED | INDEPENDENT_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED |
| Acceptance finds product defect | UNKNOWN | IN_PROGRESS | PASS | PASS | FAIL | FIX_REQUIRED | INDEPENDENT_ACCEPTANCE/FAIL/PRODUCT_DEFECT |
| Legacy normalization without source proof | UNKNOWN | COMPLETE | BLOCKED | PASS | PENDING | CORE_ACCEPTANCE_BLOCKED | SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE |
| Contradictory state axes | NOT_ACHIEVED | IN_PROGRESS | FAIL | NOT_RUN | PENDING | FIX_REQUIRED | CORE_ACCEPTANCE/FAIL/TASK_REGRESSION; preserve any completed Stage-04 snapshot as immutable evidence |
| CORE NOT_REQUIRED without Plan rationale | UNKNOWN | ESCALATED | NOT_REQUIRED | NOT_RUN | PENDING | REPLAN_REQUIRED | IMPLEMENTATION/BLOCKED/TASK_REGRESSION |
| CORE NOT_REQUIRED with explicit Plan rationale | ACHIEVED | COMPLETE | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | DONE | plan_rationale records that the scoped artifact has no CORE checks and the rationale is independently checked |
| All closure prerequisites satisfied | ACHIEVED | COMPLETE | PASS | PASS | PASS | DONE | none |

Stage 05 must snapshot before acceptance:
STAGE_04_REPORTED_IMPLEMENTATION_STATUS
STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS
STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS
STAGE_04_EXECUTION_ARTIFACT_SHA256
It also records TASK_ID, PLAN_REVISION, HANDOFF_SHA256, execution timestamp and evidence path. A Stage 05 authority/environment blocker preserves this immutable snapshot and routes INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED, TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED.

Scoped blocker record required in every terminal artifact:

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

A valid waiver preserves CHECK_RESULT and includes WAIVED_BY, WAIVER_SCOPE, RATIONALE, EVIDENCE, RESIDUAL_RISK, APPROVED_AT and REVIEW_OR_EXPIRY_TRIGGER. Core source/data-integrity failures and fabricated/missing provenance are non-waivable.

## Closure and sequencing

The root /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md is historical/non-authoritative for this task because it predates this TASK_ID and revision. Stage 03 must create a fresh handoff bound to TASK_ID, PLAN_REVISION=6, the approved plan SHA, GOAL_ANCHOR, critical path, invariants, deferred/non-gating items and stop conditions.

Stage 02 must independently review this Revision 6 and its exact hash. Stage 03 may compile handoff only for the approved revision/hash. Stage 04 creates the named package and runs only the approved verifier/transaction/status wave; it must write execution.md with the canonical six statuses, check matrix/results, scoped blockers, Stage 04 snapshot fields and artifact hashes. Stage 05 independently accepts the real CLI/evidence, snapshots immutable Stage 04 facts and does not modify product code.

The current plan is not implementation approval. Offline read-only reconciliation, isolated fixture construction, baseline reproduction, and review preparation are authorized now. Product code edits, external formal-state writes, GUI input, deployment, and production download require the applicable later gate. Any semantic contract, product-boundary, E2E, or GUI-budget change increments this TASK_ID and repeats independent review.

Canonical routing is subject-specific: implementation blockage uses IMPLEMENTATION_STATUS=BLOCKED and TASK_CLOSURE_STATUS=IMPLEMENTATION_BLOCKED; new semantic evidence uses IMPLEMENTATION_STATUS=ESCALATED and TASK_CLOSURE_STATUS=REPLAN_REQUIRED; completed implementation with CORE blocked uses TASK_CLOSURE_STATUS=CORE_ACCEPTANCE_BLOCKED; Stage 05 authority/environment blockage uses INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED and TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED; required verification debt uses INCOMPLETE, not PASS. No status field rewrites another subject.

DONE requires: PRIMARY_OUTCOME_STATUS=ACHIEVED; IMPLEMENTATION_STATUS=COMPLETE; CORE_ACCEPTANCE_STATUS=PASS or explicitly Plan-rationalized NOT_REQUIRED; REQUIRED_VERIFICATION_STATUS=PASS/NOT_REQUIRED/WAIVED; INDEPENDENT_ACCEPTANCE_STATUS=PASS/NOT_REQUIRED; exact source correspondence CONFIRMED or an explicitly Plan-rationalized equivalent; no unresolved hard blocker; valid fresh durable artifacts; unrelated user work preserved.

If source identity remains unresolved after all authorized evidence, the legally correct result is PRIMARY_OUTCOME_STATUS=UNKNOWN with the source/core check BLOCKED and no DONE. If route evidence is unavailable but exact existing provenance has already been proven and no side effect is needed, record ROUTE_NOT_NEEDED with explicit Plan rationale; otherwise route remains a scoped CORE blocker. If an independent acceptance authority/tool is unavailable, preserve implementation/CORE/required-verification facts and route INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED, TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED. Never downgrade proven implementation because acceptance could not run.

## Owner view

Essential: prove whether the existing 57 files can be safely attributed to the exact requested LINE source and prove real reusable recovery/duplicate behavior before any new GUI side effect. Filesystem health alone is insufficient. The new local CLI/package is the explicit reusable product boundary for this task; it must not be confused with an absent external producer. Supporting: bridge/service diagnosis only if causal evidence proves necessity. Deferred: production Save-All/download, bridge repair, migration, OCR, and historical cleanup. The largest remaining risk is still that the 57 files are valid but the original source namespace/provenance was never captured.
