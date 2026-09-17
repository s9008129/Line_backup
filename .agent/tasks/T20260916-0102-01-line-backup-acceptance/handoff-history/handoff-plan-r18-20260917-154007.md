# Handoff — LINE album acceptance and reusable transaction process

## TASK
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- STATUS: READY_FOR_IMPLEMENTATION
- PLAN_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md
- PLAN_REVISION: 18
- PLAN_SHA256: 22a5e5003116051d46ae5aef8d7baf06c46f873459a219946f86719c2b8107e6
- REVIEW_REQUIRED: YES
- REVIEW_REPORT: review/attempt-24/review_report.md (dual fresh review; second report review/attempt-25/review_report.md)
- REVIEWED_PLAN_REVISION: 18
- REVIEWED_PLAN_SHA256: 22a5e5003116051d46ae5aef8d7baf06c46f873459a219946f86719c2b8107e6
- INDEPENDENT_ACCEPTANCE_REQUIRED: YES
- E2E_REQUIRED: NO (plan.md:9-10, 1315-1317; a read-only verify-only pass over an existing destination is not a user-journey E2E; no production download is authorized. Fixture PASS must never be reported as production E2E.)
- ACCEPTANCE_MODE: Independent Stage 05 acceptance of the real CLI, the formal read-only verify-only result, the R1–R7 repair evidence package and the route status. No fixture result may be reported as production E2E (plan.md:1317, 1439-1447).
- Fresh Implementer required: YES
- Planner/Reviewer transcript required: NO

## GOAL_ANCHOR
PRIMARY_OUTCOME (both results CORE, plan.md:490-491, 999-1000): (1) safely establish whether the existing 57-image destination is a valid backup of the exact LINE source group '旻謙允禎成長日記' / album '2024/05/13～05/17' — otherwise stop with no ambiguous or duplicate production transaction; and (2) leave the reusable automation path itself proven through the real operator CLI — the R1–R7 repairs executed end-to-end with rerunnable, independently readable evidence. Neither result may be claimed from offline or fixture PASS; paperwork is not a substitute.
SUCCESS_EVIDENCE: product CLI emits separate Filesystem/Registry/Source/State/Overall outcomes with a SHA-256/bytes artifact manifest; SOURCE_CORRESPONDENCE is exactly CONFIRMED | UNRESOLVED | CONTRADICTED (only an authoritative exact join or one precise preserved user fact may CONFIRM); the same product transaction CLI runs in subprocess restart/fault/race tests with independent counter/state oracles (plan.md:1002-1010, 1128-1152).
MUST_NOT_BREAK (plan.md:1012-1022): formal config/state/registry/intent/run-log and the 57 photos are read-only — never redownload, rewrite, migrate, or normalize; '禎' U+798E and '楨' U+6968 stay separate strings/keys and are never merged; no AXPress/AXUIElementPerformAction/AX write/guessed coordinate/OCR-only acceptance/AppleScript-hidden-AX workaround; no Save-All retry after an UNKNOWN dispatch; DATA_PROJECT_ROOT authority stays explicit and immutable; UNKNOWN is never converted to zero/NOT_ATTEMPTED without affirmative non-dispatch proof; no test may pass by asserting a value it wrote itself.

## CRITICAL_PATH
1. Preserve/index the historical failure evidence; independently reproduce the old verifier's 56/58 false positive in isolated paths (plan.md:1008, 1108).
2. After this revision's independent approval (both Stage 02 reports above), continue the named product package/CLI and evidence repair; prove the package is the only operator process boundary for the reusable verifier/transaction deliverable (plan.md:1009-1010).
3. Implement structured fail-closed verify-only and the state/source outcome contract (plan.md:1009).
4. Implement transaction resume/commit/prepare/duplicate paths with the shared serialized compare-and-commit, deterministic fault/race injection and real subprocess restart tests (plan.md:1010).
5. Run all verifier axis-correct negatives, transaction cases 01–25, status/closure fixtures and authority negatives; then run the product verifier against DATA_DESTINATION without formal-state mutation (plan.md:1011, 1237-1313, 1347-1437).
6. Reconcile current source identity and state/registry/intent/writer evidence; current expected axes are Filesystem=PASS, Registry=FAIL, Source=UNRESOLVED, State=LEGACY_PROVENANCE_LIMITED, Overall=UNKNOWN, exit 4 — this stops exact goal acceptance while still reporting filesystem findings (plan.md:1012, 1166-1173).
7. Check documented CUA capability and the existing ledger. If route evidence remains necessary, stop at the single precise Human Gate (plan.md:937-950); it permits exactly one ellipsis GUI input and never Save-All/menu-item/chooser/state write/download. A later production Save-All requires a separate later approved revision and gate (plan.md:1315-1345).

## SEMANTIC_INVARIANTS
- Orthogonal axes, never collapsed: Filesystem / Registry / Source / State / Overall; intent / dispatch / trigger / writer / terminal ownership remain separate. Registry follows only the §16.8 axis rule (plan.md:486-489 as corrected by §18.1): a unique readable match with `verified_run_id` null (imported-evidence form, e.g. matrix `legacy-record`) is Registry PASS; the `CASE_ROOT_25` real-state copy (楨 U+6968 never matches the requested 禎 U+798E album) and any unreadable/non-matching run are Registry FAIL. Provenance failures never flip the registry axis (plan.md:434-455, 712-744).
- Stable results: exit 0 only for full pass; exit 4 completed safe rejection; exit 2 INVALID_INPUT/INVALID_CONFIGURATION/INVALID_AUTHORITY before any read/write; exit 1 internal/read/command/artifact error. Refusal classes (SKIP_DUPLICATE, SKIP_TERMINAL, CONFLICT_*, NEEDS_RECONCILIATION, MISSING_DISPATCHER, MISSING_SOURCE_EVIDENCE, INVALID_STATE_LEGACY, READBACK_UNCERTAIN, …) are fixed and may not be renamed, merged, or reordered (plan.md:1185-1236, 1237-1313).
- Validation scope: a run without contract_revision / RC2-only intent fields / full provenance is a readable LEGACY record (STATE=LEGACY_PROVENANCE_LIMITED, SOURCE=UNRESOLVED), never initialized or rewritten; validation at every load must not contradict the read-only legacy contract (plan.md:397-433).
- Finalize is the only terminal path; `--verification-json` is outcome-conditional (required for `--outcome VERIFIED`, optional for `SAFE_ABORT`); a commit refuses with `CONFLICT_UNRESOLVED_DISPATCH` exit 4 no-write unless the loaded run carries the completed successful dispatch record (plan.md:436-456, 1196, 1237-1313).
- Status Contract v2 fields stay orthogonal: PRIMARY_OUTCOME_STATUS | IMPLEMENTATION_STATUS | CORE_ACCEPTANCE_STATUS | REQUIRED_VERIFICATION_STATUS | INDEPENDENT_ACCEPTANCE_STATUS | TASK_CLOSURE_STATUS; no field rewrites another subject; `Done` means overall closure only (plan.md:1347-1353, 1439-1447).
- Baseline: `baseline_delta=WORSENED` is a must-not-break violation → REQUIRED_VERIFICATION=FAIL, closure FIX_REQUIRED, blocker BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION — never INCOMPLETE/PENDING_REQUIRED_VERIFICATION (plan.md:1395; workflow-routing §7.7 rule 8). A missing/unreadable pre-baseline is REQUIRED_VERIFICATION=INCOMPLETE, never PASS (plan.md:1380-1382).

## BEST_EFFORT_DO_NOT_GATE
- Bridge/service readiness is SUPPORTING/DIAGNOSTIC and non-gating unless a route-specific experiment proves necessity (plan.md:1011-1022, 1340-1345; check row BRIDGE_READINESS).
- DOCUMENTATION_RETENTION_HEALTH is SUPPORTING/REPOSITORY_HEALTH, waivable only by the project owner within the exact task-evidence scope (plan.md:1355-1370).
- The single GUI ellipsis observation is conditional and outside this wave; a negative or absent authorization only localizes an observation gap and is never proof that a bridge is necessary (plan.md:937-950, 1315-1345).

## DEFERRED_NOT_THIS_TASK
- Production Save-All/download, bridge repair/reinstall, TCC changes, legacy migration/normalization, OCR, historical cleanup, distributed exactly-once protocol, new persistence schema, unrelated bridge/controller refactor (plan.md:1023-1031, 1340-1345).
- Any production transaction against the formal project; any write to formal config/state/registry/run-log; any redownload of the existing 57 files (plan.md:1012, 1343).

## REPO_ANCHOR
- Project root: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Branch: master
- Anchor HEAD: 55717d5 (review attempt-24 commit; review attempt-25 = 7a583e9; planner Rev18 = 5f73207)
- Relevant dirty state: none observed at compile time (`git status --porcelain` clean)
- Drift since plan/review: none — plan.md SHA256 re-verified at 22a5e5003116051d46ae5aef8d7baf06c46f873459a219946f86719c2b8107e6, byte-identical to review/attempt-24/plan_snapshot.md and review/attempt-25/plan_snapshot.md; Stage 04 stops on any handoff↔plan mismatch.

## CURRENT_STATE_DELTA
- Product package `src/line_backup_acceptance/` exists (authority, cli, common, status, transaction, verifier); `authority.py` currently allowlists only `case-01`…`case-12` and the legacy `state.json` layout, so the Rev16/17 canonical children and case roots `-01`…`-25` are not yet implemented (plan.md:84-101, 245-280, 1237-1313).
- `tests/automation_verification/` currently has fixtures.py, harness.py, run_phase2_r1…r7 scripts and verify_evidence.py; `run_all.py` and several drivers named in plan.md §15.5 (authority_negative_driver.py exists; `status_fixture_driver.py` exists) are not yet in the tree — Stage 04 verifies the exact planned-file list before editing (plan.md:496-519).
- Durable evidence: `evidence/20260916-auto-verification/attempt-01/` holds the Phase-0 baseline, Phase-1 archive manifest and phase2-r1…r7 records; `evidence/20260916-baseline/attempt-01/` holds one baseline-pre.json. The plan's pinned Stage-04 roots `evidence/20260916-baseline/attempt-02/` and `evidence/20260916-auto-verification/attempt-02/order-*/` do not exist yet and must be created by Stage 04 without touching attempt-01 (plan.md:506-519, 783-802).
- Formal read-only default remains: SOURCE_CORRESPONDENCE=UNRESOLVED, STATE=LEGACY_PROVENANCE_LIMITED, exact expected real-command axes Filesystem=PASS / Registry=FAIL / Source=UNRESOLVED / State=LEGACY_PROVENANCE_LIMITED / Overall=UNKNOWN, exit 4 (plan.md:1166-1173).
- Residual non-gating review minors recorded at compile time (do not gate, do not reopen): RV-24-1 (plan.md:1085 call graph names a non-existent `verify.*` symbol; real entry `verifier.inspect`), RV-24-2 (plan.md:1109 critical-path item still reads "(Rev15 at handoff time)"), RV-24-3 (§18 intro says "two" attempt-22 notes while citing three). This handoff binds by PLAN_REVISION 18 + the approved SHA above, not by those sentences.

## MUST_READ_PLAN
Goal contract (`PRIMARY_OUTCOME`, `CORE_REQUIREMENTS`, `SUCCESS_EVIDENCE`, `MUST_NOT_BREAK`, `NON_GOALS`; plan.md:997-1031); authoritative roots and product boundary (plan.md:1033-1104); critical path (plan.md:1106-1114); requirement/closure table (plan.md:1116-1126); source/registry/legacy outcome contract (plan.md:1128-1152); product verifier oracle and failure containment (plan.md:1154-1164); formal config/legacy compatibility profile (plan.md:1166-1173); axis-correct fixture matrix (plan.md:1174-1235); transaction product contract and case protocol (plan.md:1237-1313); runtime route/GUI gate/truthful E2E (plan.md:1315-1345); Status Contract v2 fixtures and blockers (plan.md:1347-1437); closure and sequencing (plan.md:1439-1451); Rev14 fix contract F1–F7 and post-fix verification (plan.md:803-935); Rev15 §15.1–§15.6 normative amendments (plan.md:520-772); Rev16 §16.1–§16.10 (plan.md:235-519); Rev17 §17.1–§17.10 (plan.md:72-233); Rev18 §18.1–§18.6 (plan.md:21-70).

## SETTLED_DO_NOT_REOPEN
- Rev18 §18.1: legacy Registry axis is single-valued by the §16.8 axis rule; the former blanket "legacy → Registry FAIL" sentence is deleted (plan.md:30-39, 140-159, 397-432).
- Rev18 §18.2/§18.3/§18.4/§18.5: finalize grammar outcome-conditional in both statements; reconcile-oracle claims narrowed with no new assertion; stale literals restated as direct corrections; 19th `baseline-worsened` status row present (plan.md:41-64, 211-227, 478-481, 1395).
- Rev17 §17.1–§17.10 and Rev16 §16.1–§16.10 decisions stand as corrected; no supersession layer is added (plan.md:72-233, 235-519).
- Both Stage 02 approvals bind only Rev18 at SHA 22a5e500…107e6; any later plan edit increments PLAN_REVISION, voids this handoff and requires fresh review (plan.md:1443-1447).

## REVERIFY_ON_START
- Recompute plan.md SHA-256 and byte length; require exact match to PLAN_SHA256 above, else STOP (handoff↔plan mismatch is a stop condition).
- Re-read the two review reports and confirm their FINAL_STATUS lines are both PLAN_APPROVED for this revision/hash.
- `git status --porcelain` and `git log --oneline -5`: confirm clean tree and that no product/plan edits happened after 55717d5.
- Formal read-only facts that are mutable: DATA_CONFIG / DATA_STATE / DATA_RUN_LOG bytes and SHA-256; DATA_DESTINATION inventory (57 files, 17,924,900 bytes, per-file hashes); the CUA ledger and environment.json budget (ellipsis 2/2 used). Recapture them via the read-only baseline command before any product edit; a missing/unreadable pre-baseline is REQUIRED_VERIFICATION=INCOMPLETE, never PASS (plan.md:1377-1382).
- Case roots `-01`…`-25`, verifier/status/authority roots and `/private/tmp/line-backup-acceptance-baseline/current.json` are mutable working space: create owned roots only, never delete unowned roots, never treat `/private/tmp` as durable storage (plan.md:745-771, 1237-1313).

## TRIGGERED_POLICIES
- workflow-routing.md (§7 Status Semantics v2, §7.4 baseline, §7.6 blockers, §7.7 Stage 04 routing, §7.8 Stage 05, §7.11 artifacts)
- testing-verification.md
- debugging-recovery.md
- goal-alignment-design-economy.md
- security-privacy.md
- data-migration.md
- dependencies-contracts.md
- high-risk-change.md
- git-change-hygiene.md

## FIRST_ACTION
Run the exact read-only pre-change baseline before any product edit (plan.md:1377-1382):
`cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0 /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/authority_baseline.py --config /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json --state /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json --run-log /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --output /private/tmp/line-backup-acceptance-baseline/current.json`
then copy that exact output byte-for-byte to `evidence/20260916-baseline/attempt-02/baseline-pre.json` and record its SHA-256/byte length, argv, cwd, interpreter version and normalized environment fingerprint (never write outside evidence roots or formal paths). Only after this pre-artifact exists may product edits begin.

## IMPLEMENTATION_WAVES
Order is CORE-first; details remain in the plan.
1. W-BASELINE (CORE, prerequisite): pre-change baseline artifact above; verify `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY` pre-state (plan.md:1355-1382).
2. W-VERIFIER (CORE): fail-closed verify-only, axis contract, read errors, image structural decode, artifact manifest (plan.md:1009, 1154-1173; F4).
3. W-TRANSACTION (CORE): prepare/resume/commit/finalize/duplicate with shared lock, dispatch continuity, at-most-once, terminal finalization, storage faults (plan.md:745-771, 1237-1313; F1–F3, F7).
4. W-HARNESS (CORE): literal drivers for verifier matrix (1174-1235), transaction cases 01–25 (1237-1313), authority negatives (1164), status fixtures (1384-1437); ownership isolation per §15.5 (745-771).
5. W-WAVE-RUN (CORE): `tests/automation_verification/run_all.py` runs the whole wave in both orders (ownership-last and ownership-first) with disjoint durable roots; `verify_evidence.py` independently re-reads every manifest (plan.md:912-935).
6. W-REAL-DESTINATION (CORE): run the product verifier against DATA_DESTINATION read-only; expected axes Filesystem=PASS / Registry=FAIL / Source=UNRESOLVED / State=LEGACY_PROVENANCE_LIMITED / Overall=UNKNOWN, exit 4; no formal-state mutation (plan.md:1166-1173).
7. W-STATUS-CLOSURE (CORE): Status Contract v2 fixtures, including the 19th `baseline-worsened` row and the baseline-unavailable INCOMPLETE row (plan.md:1384-1437).
8. W-USER-FACT (CORE, blocked on user): preserve part-1 artifact; part 2 open question + single GUI observation gate stays at the one human gate after all non-GUI work (plan.md:937-970, 1439-1447).
9. W-EXECUTION-RECORD (CORE deliverable): write `execution.md` with command/input/stdout/stderr/exit evidence, check matrix, the six orthogonal statuses, scoped blockers, baseline delta and artifact hashes (workflow-routing §7.11).
- BRIDGE_READINESS and DOCUMENTATION_RETENTION_HEALTH remain SUPPORTING; the GUI observation remains BEST_EFFORT/conditional and must not be promoted into a mandatory gate.

## ACCEPTANCE_CONTRACT
Required per-check fields: CHECK_ID | COMMAND/SCENARIO | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY. The plan's authoritative 13-row policy table is plan.md:1355-1370; every check additionally carries CHECK_RESULT and WAIVER_STATUS.
- CORE first: VERIFIER_FALSE_POSITIVE_REPRO, VERIFY_REAL_DESTINATION, VERIFY_NEGATIVE_FIXTURES, TRANSACTION_RESUME_CORE, TRANSACTION_COMMIT_CORE, FORMAL_STATE_READONLY_RECONCILIATION, SOURCE_CORRESPONDENCE, CUA_ROUTE_DECISION, STATUS_CLOSURE_CONTRACT, INDEPENDENT_ACCEPTANCE, BASELINE_REGRESSION_DELTA — all HARD_CLEAN except BASELINE_REGRESSION_DELTA (BASELINE_DELTA); all WAIVER_ALLOWED=NO / WAIVER_AUTHORITY=NONE.
- Supporting: BRIDGE_READINESS (NON_GATING, waivable by project owner, exact scope), DOCUMENTATION_RETENTION_HEALTH (HARD_CLEAN within the exact task-evidence scope, waivable by project owner, exact scope; missing raw commands/stdout/stderr/exit or manifest read-back is non-reproducible provenance).
- Expected orthogonal statuses in every Stage 04/05 artifact: PRIMARY_OUTCOME_STATUS, IMPLEMENTATION_STATUS, CORE_ACCEPTANCE_STATUS, REQUIRED_VERIFICATION_STATUS, INDEPENDENT_ACCEPTANCE_STATUS, TASK_CLOSURE_STATUS; blockers use the scoped blocker record (workflow-routing §7.6, plan.md:1424-1437).
- Baseline rule: pre-change artifact SHA-256/bytes/argv/cwd/env fingerprint; post-change rerun of the same argv must show `baseline_delta=UNCHANGED`; WORSENED → FAIL/FIX_REQUIRED (plan.md:1371-1382, 1395).
- Stage 04 durable record: `execution.md` is mandatory for every material Stage 04 run with the six statuses, matrix/results, blockers, next action, evidence references, PLAN_REVISION/HANDOFF identity and artifact hashes (workflow-routing §7.11).
- Stage 05 carry-forward: before acceptance it snapshots STAGE_04_REPORTED_IMPLEMENTATION_STATUS, STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS, STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS, STAGE_04_EXECUTION_ARTIFACT_SHA256 plus TASK_ID, PLAN_REVISION, HANDOFF_SHA256, timestamp and evidence path; it must freshness-check `execution.md` and never downgrade proven implementation because acceptance could not run (workflow-routing §7.8, plan.md:1416-1423).
- Degraded-mode semantics: source UNRESOLVED/LEGACY_PROVENANCE_LIMITED keeps the album-data result UNKNOWN/BLOCKED with no DONE while still reporting filesystem findings; a route-only gap is a scoped CORE blocker unless ROUTE_NOT_NEEDED is explicitly rationalized; required-verification debt is INCOMPLETE, never PASS (plan.md:1128-1152, 1340-1345, 1439-1451).

## STOP_AND_ESCALATE_IF
- Any change to semantic validity/requiredness/enums/gating/error/fallback/precedence/authority/retry/closure meaning → stop, write escalation evidence, replan; never improvise (plan.md:1028, 1439-1447).
- Handoff↔plan revision/hash mismatch, or any plan edit after this handoff → STOP (plan.md:1441-1447).
- Any failed/uncertain authority validation, state replacement, read-back, revision/owner check or unresolved dispatch barrier → safe abort, no retry, preserve evidence (plan.md:1185-1236).
- Any 禎/楨 mismatch, missing exact-source proof, first-match/ambiguous registry match, or attempted merge/normalization → scoped CORE blocker; never merge or rewrite (plan.md:1128-1152).
- Any ambiguous runtime dispatch or undocumented Save-All/menu identity → no Save-All retry; stop at the single human gate only after all automatic work is complete, specifying the exact app/group/album/count, the permitted input and the safety purpose (plan.md:937-950).
- Bridge/service repair, TCC changes, reinstall, new permissions, deployment or production download are outside this handoff; prepare them only after route-specific causal proof and a later approved revision (plan.md:1023-1031, 1340-1345).
- A `baseline-worsened` delta is a hard failure (FIX_REQUIRED), never INCOMPLETE/PENDING_REQUIRED_VERIFICATION (plan.md:1395; workflow-routing §7.7 rule 8).

## HISTORICAL_TASK_DEPENDENCIES
- NONE for generic context. The root `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md` is historical/non-authoritative background only (it predates this TASK_ID) and must not be used as a plan or contract (plan.md:1439-1441).
- The prior handoff of this task is archived at `handoff-history/handoff-plan-r13-20260917-021523.md` (Rev13-bound, superseded by this handoff; keep as history, never execute from it).

