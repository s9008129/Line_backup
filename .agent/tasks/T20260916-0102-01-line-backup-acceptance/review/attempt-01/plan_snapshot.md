# LINE album acceptance and reusable transaction core — candidate plan

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 1
TASK_CLASS: CRITICAL
PLAN_STATUS: CANDIDATE
REVIEW_REQUIRED: YES
INDEPENDENT_ACCEPTANCE_REQUIRED: YES
E2E_REQUIRED: YES
ACCEPTED_BY_USER: YES
PRIMARY_OUTCOME_STATUS: UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS

## Goal contract

PRIMARY_OUTCOME: Safely establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group `旻謙允禎成長日記`, album `2024/05/13～05/17`, and otherwise perform at most one authorized production transaction without duplicate or ambiguous Save-All dispatch.

SUCCESS_EVIDENCE:

- A fresh, read-only verifier observes exactly 57 recognized images, stable complete inventories, per-file SHA-256 and byte lengths, no zero-byte/partial/temp/unrecognized entries, no unsafe path or entry anomalies, and a precise group-scoped registry association.
- The source namespace is resolved explicitly. `禎` and `楨` remain distinct until authoritative visual evidence or one user fact confirmation establishes correspondence.
- A real reusable transaction flow, not a self-written constant fixture, proves interrupted resume never repeats a side-effect action, verified fingerprints skip, unknown dispatch retains its barrier, commit/read-back failure stops, and terminal registration plus ownership release is coherent.
- The current runtime's documented and fresh evidence separately establishes target acquisition, popup observation, affirmative Save-All identification, supported coordinate mapping, and exact chooser routing. No GUI input is sent without the required ledger and explicit gate.

MUST_NOT_BREAK:

- Existing photos and formal state/config/registry/intent/run-log are read-only for this acceptance wave; no redownload of the valid 57-file destination.
- No AXPress, AXUIElementPerformAction, AX write, guessed coordinate, OCR-only acceptance, AppleScript/hidden AX workaround, or Save-All retry after uncertainty.
- Project-root authority remains explicit and immutable; verify-only has an empty formal-state write set; all fixture state is isolated from the selected production project.
- Intent, dispatch, trigger, filesystem, and terminal ownership remain separate evidence axes. Unknown is never converted to zero/NOT_ATTEMPTED without affirmative non-dispatch proof.
- Bridge/service readiness does not become a global gate unless a direct runtime experiment proves it is necessary for the selected path.

NON_GOALS:

- No automatic spelling merge, state migration, production download, bridge reinstall, TCC change, or broad historical cleanup.
- No distributed exactly-once protocol, new persistence schema, or unrelated bridge/controller refactor.
- No claim that historical GUI, build, bridge, or offline PASS proves current Save-All capability or source correspondence.

CRITICAL_PATH:

1. Preserve and index historical failure evidence; independently reproduce the verifier's false-positive mechanism in an isolated copy/fixture.
2. Implement the smallest contract-faithful verify-only path with structured inventory, fail-closed command/read errors, group/fingerprint/destination binding, and real-path containment.
3. Implement the smallest reusable transaction core against the existing state contract, with a fake dispatcher only as an injected side-effect boundary; tests must call the core's resume/commit/duplicate paths.
4. Run focused negative and recovery cases, then run the corrected verifier against the real destination without formal-state mutation.
5. Reconcile the exact target source identity and current state/registry/intent/writer evidence.
6. Check the current CUA runtime documentation and the existing action ledger; only after all offline work, request one precisely scoped observation gate if required. Production download requires a separate one-time gate.

## Requirement → evidence → gap

| Requirement | Current evidence | Gap / planned closure | Class | Closure gate |
|---|---|---|---|---|
| Existing destination is 57 complete images | `evidence/20260915-verify-only-57` has three equal inventories and 57 JPEG-looking files; raw inventory is preserved | Current script ignores `EXPECTED` in its final predicate and does not fail closed per file; rerun corrected verifier in a new attempt and compare raw inventory | CORE / OUTCOME | HARD_CLEAN |
| Exact source correspondence | Config/state/registry use `旻謙允楨成長日記`; user target is `旻謙允禎成長日記`; verified run title is UNKNOWN | Locate authoritative source evidence; otherwise one exact user fact gate; no merge | CORE / OUTCOME | HARD_CLEAN |
| State/registry/intent/writer consistency | Current state revision 39, writer/run/context null; target registry entry points to DEST; legacy verified run has UNKNOWN title and formula calibration | Correct verifier must bind group key on every registry match and report legacy provenance limits; transaction core tests must exercise live code | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Reusable interrupted recovery and duplicate protection | Old fixture only writes/asserts constants; no resume/dispatch/commit call | Add real core and isolated restart/fake-dispatch tests, preserving attempt-01/02 | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Actual Save-All path | Historical menu evidence had no affirmative current Save-All; current CUA is uninitialized | Use documented runtime capabilities plus one ledger-scoped observation only after offline gates; stop on ambiguity | CORE / OUTCOME | HARD_CLEAN |
| Bridge/service | Historical PID-only defect is supported; bridge is not proven necessary for direct CUA or verify-only | Keep supporting/non-gating; prepare deployment only if direct path experiment proves necessity and approved handoff exists | SUPPORTING / DIAGNOSTIC | NON_GATING |
| Raw commands and artifacts | Historical logs and digests preserved | New attempt directory stores exact inputs, stdout/stderr/exit, action ledger, inventory and artifact manifest | CORE / MUST_NOT_BREAK | HARD_CLEAN |

## Minimal design and semantic invariants

The verifier is a read-only command-line entry point. It receives explicit project root, destination, target fingerprint, and evidence output directory; it never discovers or substitutes a root and never mutates formal state. It uses a structured JSON inventory so arbitrary filenames cannot corrupt records. Each sample enumerates all immediate entries without following symlinks, classifies every regular file by content/MIME, hashes readable files, and treats any command/read error as a failed sample. Final filesystem PASS requires expected count, stable inventory and byte total, zero anomalies, and no unresolved path errors. Registry PASS requires exactly one matching `group_key + fingerprint + destination` association and consistent verified-run provenance; cross-group or ambiguous matches fail.

The transaction core is the actual tested process boundary for offline recovery. It loads an isolated state file, validates the target run and intent axes, injects a dispatcher callback only at the original one-shot action boundary, performs atomic same-directory state replacement plus read-back, and refuses to dispatch from a resumed intent. It does not call LINE, create photos, or alter the production registry. Terminal finalization commits verification and registry addition with owner release in one guarded replacement; a failed write/read-back is a hard stop. This is the minimum needed to test the contract, not an exactly-once guarantee.

## Material checks

| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_REQUIRED | FAILURE_CLASSIFICATION_RULE | WAIVER_ALLOWED | WAIVER_AUTHORITY |
|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | YES | Old copy accepts stable wrong-count data only if reproduced; otherwise document static mechanism | NO | NONE |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | YES | Corrected verifier must pass only if all criteria and exact state association pass | NO | NONE |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | Any accepted malformed/unsafe fixture is a task regression | NO | NONE |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | Any second fake dispatch after restart or bypass of unknown barrier is a task regression | NO | NONE |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | Split registry/owner commit or read-back uncertainty is a task regression | NO | NONE |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | YES | Any formal-state mutation or unresolved cross-record contradiction blocks closure | NO | NONE |
| CUA_CAPABILITY_MATRIX | CORE | DIAGNOSTIC | NON_GATING | YES | Missing current capability evidence keeps route UNKNOWN; does not authorize bridge deployment | NO | NONE |
| GUI_SAVE_ALL_OBSERVATION | CORE | OUTCOME | HARD_CLEAN | YES | No fresh affirmative Save-All identity/geometry means SAFE_ABORT and no dispatch | NO | NONE |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | Failure is non-gating unless direct-path necessity is proven | YES | Project owner, exact scope only |

## Plan sequencing, gates, and stop conditions

Stage 02 must independently review this revision before implementation or handoff. Stage 03 may then compile a handoff; Stage 04 implements only the approved verifier/core wave; Stage 05 independently accepts the real code and evidence. If a semantic contract or gate changes, increment this revision and repeat review.

Offline work is authorized now: read-only reconciliation, isolated fixture construction, baseline reproduction, and plan/review preparation. No GUI input or formal state write is included. After offline work, the single Human Gate, if still necessary, must name the exact runtime/provider, target group spelling, album/date/count, observation scope, and permitted input count; a separate production gate is required for any download.

## Owner view

Essential: prove whether the existing 57 files can be safely attributed to the exact requested source and prove the real recovery/deduplication behavior before any new GUI side effect. Optional: bridge repair, OCR, historical cleanup. The whole workflow may stop on unresolved source identity, unsafe Save-All targeting, uncertain dispatch, formal-state conflict, or missing independent acceptance because each would make the result non-decision-valid or risk a duplicate/wrong-album action. The largest remaining risk is that the existing verified files are valid but their source namespace was never captured, so file hashes alone cannot resolve `禎` versus `楨`.
