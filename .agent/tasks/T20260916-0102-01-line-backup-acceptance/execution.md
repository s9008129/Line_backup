# Stage 04 execution record — LINE album acceptance (Rev18 wave)

IDENTITY
- TASK_ID: `T20260916-0102-01-line-backup-acceptance`
- PLAN_REVISION: `18`
- PLAN_SHA256: `22a5e5003116051d46ae5aef8d7baf06c46f873459a219946f86719c2b8107e6` (1455 lines; re-verified at Stage 04 start and equal to both review snapshots)
- HANDOFF_SHA256: `9cf01d4eedc006cfff2217e3b610c8166cfb05c04919512e74a19f4aa20946c6` (131 lines; re-verified)
- PLAN_APPROVAL: `review/attempt-24/review_report.md` FINAL_STATUS `PLAN_APPROVED` + `review/attempt-25/review_report.md` FINAL_STATUS `PLAN_APPROVED` (dual fresh review for this exact revision/hash)
- IMPLEMENTATION_MODE: `FRESH_STAGE_04` (this session performed no GUI/AX/Computer-Use input)
- STAGE_04_ANCHOR_HEAD: `ba73bbf` (handoff commit; tree clean, no product/plan edits after `55717d5`). All Stage 04 commits below are this wave's own.
- EXECUTION_DATE: `2026-09-16/17`; runtime: `/usr/bin/python3` 3.9.6 (clang 21.0.0), `macOS-26.6.2-arm64-arm-64bit`, cwd `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`, env `LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0` (+`PYTHONPATH=src`, `PYTHONPYCACHEPREFIX=/private/tmp/...` for product calls)

## 1. Result first — six orthogonal statuses (Status Contract v2)

| Subject | Status | Basis |
|---|---|---|
| PRIMARY_OUTCOME_STATUS | `UNKNOWN` | Result (1) album-data: 57-file destination is healthy (Filesystem=PASS) but source correspondence is `UNRESOLVED`, so the album-data outcome is legally UNKNOWN with no production transaction. Result (2) reusable capability: achieved (below). Both results are CORE (plan.md:490-491, 999-1000); the combined outcome cannot be ACHIEVED while (1) is unresolved. |
| IMPLEMENTATION_STATUS | `COMPLETE` | Product package boundary + full R1–R7 repair wave + all literal drivers executed end-to-end; this execution record is the last W-EXECUTION-RECORD deliverable (handoff W1–W9). |
| CORE_ACCEPTANCE_STATUS | `BLOCKED` | 9 of 11 CORE checks PASS; `SOURCE_CORRESPONDENCE` is scoped BLOCKED/UNRESOLVED (禎 U+798E vs persisted 楨 U+6968, part 2 unanswered) and `CUA_ROUTE_DECISION` is scoped BLOCKED/UNKNOWN (no GUI input authorized in Stage 04; single human gate pending). Non-waivable, no DONE (plan.md:1449-1451). |
| REQUIRED_VERIFICATION_STATUS | `PASS` | No required-verification debt: baseline pre/post identical (`baseline_delta=UNCHANGED`), every driver executed with literal argv/stdout/stderr/exit + manifest, every durable tree independently re-read with 0 problems (workflow-routing §7.7; plan.md:1371-1395). |
| INDEPENDENT_ACCEPTANCE_STATUS | `PENDING` | Stage 05 (fresh verifier) has not yet run against this record; per §7.8 it snapshots this file's Stage 04 facts before accepting. |
| TASK_CLOSURE_STATUS | `CORE_ACCEPTANCE_BLOCKED` | Completed implementation with CORE blocked routes to CORE_ACCEPTANCE_BLOCKED — never DONE (plan.md:1445-1449; workflow-routing §7.7 rule 5). |
| BASELINE_REGRESSION_DELTA (check) | `UNCHANGED` | Named subject `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY`: pre/post byte-identical (19,005 bytes, sha256 `ab6747f2…85b5`); formal config/state/run-log/57 photos zero mutation. |

Plain-language owner view: the local backup tool and its evidence harness are now proven (the reusable automation path works end-to-end and every piece of evidence can be re-read); whether the existing 57 photos really are "this group's 2024/05/13～05/17 album" is still unproven because the visible group name character (`禎`, U+798E) differs from the name saved in the formal config/state (`楨`, U+6968) and the second half of the one user question ("are those 57 files that album's backup?") was never answered. No download, no Save-All, no state write was performed, so nothing was made worse.

## 2. Check matrix — authoritative 13 rows (plan.md:1355-1370), with Stage 04 results

Policy columns are the plan's table; `CHECK_RESULT`/`WAIVER_STATUS` are this wave's observed results. Every check additionally carries the command/scenario + evidence in §3.

| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY | CHECK_RESULT | WAIVER_STATUS |
|---|---|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | REQUIRED | old false acceptance not reproduced invalidates baseline | NO | NONE | `PASS` | NOT_ALLOWED |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | incorrect axis/exit/artifact or false acceptance is TASK_REGRESSION | NO | NONE | `PASS` | NOT_ALLOWED |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | malformed/unsafe acceptance or axis conflation is TASK_REGRESSION | NO | NONE | `PASS` | NOT_ALLOWED |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | repeat dispatch or barrier bypass is TASK_REGRESSION | NO | NONE | `PASS` | NOT_ALLOWED |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | stale/split/uncertain commit or false terminality is TASK_REGRESSION | NO | NONE | `PASS` | NOT_ALLOWED |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | formal mutation or contradiction is TASK_REGRESSION/BLOCKED | NO | NONE | `PASS` | NOT_ALLOWED |
| SOURCE_CORRESPONDENCE | CORE | OUTCOME | HARD_CLEAN | REQUIRED | missing authority is scoped BLOCKED/UNRESOLVED; contradiction is FAIL | NO | NONE | `BLOCKED` (UNRESOLVED) | NOT_ALLOWED |
| CUA_ROUTE_DECISION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | missing/ambiguous route evidence is scoped BLOCKED/UNKNOWN; no dispatch | NO | NONE | `BLOCKED` (UNKNOWN) | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | illegal enum/routing/self-waiver is TASK_REGRESSION | NO | NONE | `PASS` | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | missing independent result remains PENDING/BLOCKED | NO | NONE | `NOT_RUN` (Stage 05 PENDING) | NOT_ALLOWED |
| BASELINE_REGRESSION_DELTA | CORE | MUST_NOT_BREAK | BASELINE_DELTA | REQUIRED | new/worsened signature or silently omitted old signature | NO | NONE | `PASS` (UNCHANGED) | NOT_ALLOWED |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NONE | non-gating unless route-specific necessity is proved | YES | Project owner, exact scope | `NOT_RUN` (non-gating; no necessity proof) | NOT_REQUESTED |
| DOCUMENTATION_RETENTION_HEALTH | SUPPORTING | REPOSITORY_HEALTH | HARD_CLEAN | NONE | within task-evidence scope, missing raw records/read-back makes acceptance non-reproducible | YES | Project owner, exact scope | `PASS` | NOT_REQUESTED |

## 3. Per-check commands/scenarios, results, evidence

1. VERIFIER_FALSE_POSITIVE_REPRO — `PASS`
   - Scenario: preserved legacy verifier (`evidence/20260915-verify-only-57/verify-only.sh`, sha256 `d8eb87d4…9c7c`) executed over isolated 56- and 58-image fixtures under its own owned root; the old process accepted both as PASS.
   - Observed: 56 → legacy exit 0 / `legacy_claimed_pass=true`; 58 → legacy exit 0 / `legacy_claimed_pass=true`; `reproduction_match=true`. The fixed product CLI rejects both (`count-56`, `count-58` rows in §3.3).
   - Evidence: `evidence/20260916-acceptance/attempt-03/legacy-false-positive-summary.json` (sha256 `97489674…20b2`) + `driver-records/legacy/`; historical archive `evidence/20260916-auto-verification/attempt-01/archive-phase1/manifest.json` (sha256 `5304bd26…bbd2`).

2. VERIFY_REAL_DESTINATION — `PASS`
   - Command (exact, read-only): see §5.
   - Observed: Filesystem=`PASS` (57 regular files, 57 recognized images, 17,924,900 bytes), Registry=`FAIL`, Source=`UNRESOLVED`, State=`LEGACY_PROVENANCE_LIMITED`, Overall=`UNKNOWN`, `failure_class=INPUT_PROVENANCE_LIMITED`, `artifact_readback=PASS`, exit `4` — observed equals expected on every axis; `match=true`.
   - Evidence: `evidence/20260916-product-verify/attempt-04/reconciliation.json` (sha256 `e9d96433…a4da`), `product/result.json`, `product/manifest.json`, `process/{argv,stdout,stderr,exit-code}`.

3. VERIFY_NEGATIVE_FIXTURES — `PASS`
   - Scenario: `tests/verifier_fixture_driver.py` consumed the literal 40-row manifest and executed the real product CLI per row with an independent pre-computed oracle.
   - Observed: 40/40 `match=true` covering: valid-57; count-56/58; `.part/.partial/.tmp/.temp/.download/.crdownload/.incomplete/.filepart`; hidden metadata; symlink entry; outside-backup-root; special file; unreadable file (State=UNKNOWN, exit 1, INTERNAL_READ_ERROR); file-command error; MIME mismatch; safe filenames; mtime/bytes changed at SAMPLE_2_READY; wrong-group (CONTRADICTED); cross-entry (STATE_CONTRADICTED); `legacy-record` (Registry PASS per §16.8 axis rule, Source UNRESOLVED); duplicate registry; invalid config (exit 2); authority mismatch (no state write); artifact read-back failure; truncated PNG; JPEG missing EOI; unsupported image type; read-error-sample-2; dangling/safe-abort/non-terminal/wrong-group links; forged binding; binding deleted/mutated; fixture binding in production.
   - Evidence: `evidence/20260916-acceptance/attempt-03/verifier-summary.json` (sha256 `2571beaf…52c2`), literal manifest `verifier-fixture-rows.json` (sha256 `e189622b…43b0`), `verifier/` per-row artifacts, `driver-records/verifier/`.

4. TRANSACTION_RESUME_CORE — `PASS`
   - Scenario: 25 literal acceptance cases (Cases 01–25, `tests/acceptance_case_driver.py`, subprocess-only orchestration with independent oracles) + R1 crash-window / R2 loaded-intent / R3 preconditions drivers on real CLI subprocesses.
   - Observed: 25/25 `safe=true` and `independent_oracle_match=true`; R1 `SAFE_NO_SECOND_DISPATCH_AFTER_CRASH_WINDOW` (counter stays 1; fresh resume → RECOVERY_NO_DISPATCH/BARRIER_COMMITTED; commit → CONFLICT_UNRESOLVED_DISPATCH exit 4 zero-write); R2 no second dispatch, `--no-dispatch` performs none, loaded never-dispatched intent commits barrier + manual reconciliation; R3 a–e all fail-closed with pre/post state SHA unchanged and zero counter growth.
   - Evidence: `evidence/20260916-acceptance/attempt-03/acceptance-observation.json` (sha256 `6563228d…7513`) + `transactions/case-01…case-25/`; `evidence/20260916-auto-verification/attempt-02/order-*/phase2-r1|r2|r3/`.

5. TRANSACTION_COMMIT_CORE — `PASS`
   - Scenario: R4 finalize-trust (fabricated/fail-claim/empty/foreign-chain/tampered-chain refusals + closed loop to verify-2 PASS/PASS/CONFIRMED/EXACT exit 0), R5 storage-fault/axis rows, case-05 commit race, case-07 double prepare, case-09 READBACK_UNCERTAIN, case-10A/B finalize, case-19 unresolved dispatch, case-20 parent SIGKILL in the dispatch window, case-22a–f evidence-chain negatives, case-23a–c storage faults, case-24a–d user-fact v1, case-25a–b legacy real-state shape.
   - Observed: all refusals exact-class with zero registry writes; winner/loser race returns exact `CONFLICT_STALE_REVISION` exit 4 zero-write; duplicate/terminal path `SKIP_DUPLICATE`/`SKIP_TERMINAL`; R7 closed loop 18/18 checks true with second-destination `CONFLICT_DUPLICATE_FINGERPRINT` exit 4, counter still 1.
   - Evidence: same trees as §3.4 plus `order-*/phase2-r4|r5|r7/`.

6. FORMAL_STATE_READONLY_RECONCILIATION — `PASS`
   - Command: the FIRST_ACTION baseline argv re-run post-change (byte-for-byte) + read-only `verify-only` against the formal destination (see §5).
   - Observed: `baseline_delta=UNCHANGED` (pre and post both 19,005 bytes, sha256 `ab6747f2…85b5`); destination inventory identical (57 files / 17,924,900 bytes); no formal config/state/registry/intent/run-log/photo mutation.
   - Evidence: `evidence/20260916-baseline/attempt-02/baseline-pre.json` (+`.meta.json` sha256 `eaba57bd…1e60`), `evidence/20260916-product-verify/attempt-04/baseline-post-process/`, `reconciliation.json`.

7. SOURCE_CORRESPONDENCE — `BLOCKED` (UNRESOLVED)
   - Fact: user-fact part 1 answered — the visible LINE group is `旻謙允禎成長日記` with `禎` (U+798E); the persisted formal key is `旻謙允楨成長日記` with `楨` (U+6968). Part 2 ("are those 57 files this album's backup?") remains `UNANSWERED`.
   - Consequence: no authoritative exact join exists (Registry=FAIL; no `verified_run_id` chain), so correspondence is `UNRESOLVED`; strings were never merged/normalized and no production dispatch was attempted.
   - Evidence: `evidence/20260916-user-fact/source-identity-user-fact.json` (status `PARTIAL`, sha256 `8af8c6fc…0fa4`).

8. CUA_ROUTE_DECISION — `BLOCKED` (UNKNOWN)
   - Decision: `route_status=UNKNOWN`, `decision=SAFE_ABORT_NO_GUI_INPUT`, `production_dispatch=FORBIDDEN`, `chooser_state=NOT_ENTERED`, 0 menu/Save-All/state writes in this session; historical ledger re-checked (ellipsis 2/2 used, menu-item 0, Save-All 0, state writes 0; actions sha256 `9d6a1590…5aee`, environment sha256 `a43d23d6…2c95`).
   - Human gate (stays with the user, exact scope): `LINE jp.naver.line.mac / group 旻謙允禎成長日記 (禎 U+798E) / album 2024/05/13～05/17 / 57 images`; permits exactly one current-target ellipsis observation, then immediate post evidence and stop; forbids menu-item selection, Save All, chooser, state write, download.
   - Evidence: `evidence/20260916-route/attempt-02/route-decision.json` (sha256 `1bb31fe3…326b`) + manifest + independent read-back.

9. STATUS_CLOSURE_CONTRACT — `PASS`
   - Scenario: 19 literal rows through the real `status evaluate` CLI with an independent pre-written expectation table (six-status tuples + blockers + checks + waiver + evidence_basis), each row executed before its output was read.
   - Observed: 19/19 `match=true` including `baseline-unchanged` (READY_FOR_INDEPENDENT_ACCEPTANCE), the §18.5 19th row `baseline-worsened` (REQUIRED_VERIFICATION=FAIL / FIX_REQUIRED / blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` / delta WORSENED), `baseline-unavailable` (INCOMPLETE / INPUT_UNAVAILABLE), `canonical-preexisting-debt`, `retention-waived` (original FAIL preserved), `contradictory-axes` (Rev18 tuple), `core-not-required-rationalized` (DONE) vs `core-not-required-no-rationale` (REPLAN_REQUIRED), `done`, `stage05-blocked`, `acceptance-product-defect`, `legacy-no-source`.
   - Evidence: `evidence/20260916-acceptance/attempt-03/status-summary.json` (sha256 `e5b14e0d…7890`), `status-rows.json` (sha256 `48697c58…f3308`), `status/`, `driver-records/status/`.

10. INDEPENDENT_ACCEPTANCE — `NOT_RUN` (PENDING)
    - Stage 05 must run in a fresh session; §7.8 carry-forward snapshot is provided in §9 below. No fixture result is offered as production E2E (handoff E2E_REQUIRED=NO; plan.md:1317).

11. BASELINE_REGRESSION_DELTA — `PASS` (UNCHANGED)
    - Pre artifact: sha256 `ab6747f2…85b5`, 19,005 bytes, argv/cwd/env fingerprint + interpreter version recorded in `baseline-pre.meta.json` before any product edit; post artifact: same argv, byte-identical; no signature omitted, none new/worsened.
    - Evidence: §6 artifacts.

12. BRIDGE_READINESS — `NOT_RUN` (SUPPORTING, NON_GATING, NOT_REQUESTED)
    - No route-specific experiment proved bridge/service necessity; no TCC/reinstall/permission/bridge work was performed or attempted (explicitly out of this handoff).

13. DOCUMENTATION_RETENTION_HEALTH — `PASS`
    - Every wave root carries literal argv/stdout/stderr/exit-code records, per-attempt SHA-256/bytes manifests and an independent read-back report with 0 problems / 0 uncovered files (§6 table); `/private/tmp` was working space only.

## 4. Baseline (W-BASELINE) — pre/post, same argv

- Subject: `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY`
- Exact argv (pre, FIRST_ACTION verbatim; post identical):
  `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0 /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/authority_baseline.py --config <config> --state <state> --run-log <run_log> --destination <destination> --output /private/tmp/line-backup-acceptance-baseline/current.json`
- cwd: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`; interpreter `/usr/bin/python3` 3.9.6 (clang 21.0.0); env fingerprint `{LC_ALL:C, PATH:/usr/bin:/bin, PYTHONHASHSEED:0}`; platform `macOS-26.6.2-arm64-arm-64bit`
- Pre: copied byte-for-byte to `evidence/20260916-baseline/attempt-02/baseline-pre.json` (19,005 bytes, sha256 `ab6747f2…85b5`) with meta record `baseline-pre.meta.json` (sha256 `eaba57bd…1e60`), before any product edit.
- Post: rerun after all product/tooling changes (`evidence/20260916-product-verify/attempt-04/baseline-post-process/`), 19,005 bytes, sha256 `ab6747f2…85b5`.
- `baseline_delta=UNCHANGED` (workflow-routing §7.7 rule 8 satisfied; a WORSENED delta would have been FAIL/FIX_REQUIRED).

## 5. Formal read-only verify-only (W-REAL-DESTINATION)

- Exact command (product CLI as the only boundary):
  `PYTHONPATH=src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state --config …/config/line_backup_config.json --state …/state/backup_state.json --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir evidence/20260916-product-verify/attempt-04/product`
- Observed vs expected (all equal): Filesystem `PASS` / Registry `FAIL` / Source `UNRESOLVED` / State `LEGACY_PROVENANCE_LIMITED` / Overall `UNKNOWN` / `failure_class=INPUT_PROVENANCE_LIMITED` / `artifact_readback=PASS` / exit `4`.
- No formal mutation: pre/post baseline identical; product wrote only inside the attempt evidence dir.
- Evidence: `reconciliation.json` (match=true), `process/`, `product/`, `manifest.json` (sha256 `8788a67e…604d`), `readback-verification.json` (verdict PASS, 2 manifests / 17 artifacts / 0 problems / 0 uncovered).

## 6. Wave execution, durability and independent read-back

| Root | What ran | Result | Manifest sha256 | Read-back |
|---|---|---|---|---|
| `evidence/20260916-auto-verification/attempt-02/order-driver-first/` | R1,R2,R3,R4,R5,R6-status,R7,R6-ownership (ownership-last) | 8/8 exact safe verdicts | `3ca40f43…05c4` | PASS (37 manifests / 1 supplement / 3819 artifacts / 0 problems / 0 uncovered) |
| `evidence/20260916-auto-verification/attempt-02/order-ownership-first/` | R6-ownership first, then R1…R7 | 8/8 exact safe verdicts | `d262d041…d194` | PASS (37 manifests / 1 supplement / 3819 artifacts / 0 problems / 0 uncovered) |
| `evidence/20260916-acceptance/attempt-03/` | 25 cases + 40-row verifier + 19-row status + 11 authority negatives + legacy repro | all match | `c4f3db95…0412` | PASS (45 manifests / 4604 artifacts / 0 problems / 0 uncovered) |
| `evidence/20260916-product-verify/attempt-04/` | baseline post + formal verify-only | match=true / UNCHANGED | `8788a67e…604d` | PASS (2 manifests / 17 artifacts) |
| `evidence/20260916-route/attempt-02/` | route decision record | SAFE_ABORT_NO_GUI_INPUT | `733d5c9c…aed4` | PASS |

- Summaries: `run-all-summary.json` sha256 `aebc2b5d…92a3e`; `run-history.json` sha256 `87014375…1b533`; `acceptance-observation.json` sha256 `6563228d…7513`.
- Append-only history preserved: the first durable two-order run (`*.failed-run1-20260916T215559Z`, drivers revision `c5184ec`) is kept as-is; its 112 stale-manifest problems (2 tampered-chain + 110 case-01 manifest) and the recording-only fixes are documented in `run-history.json`. `attempt-01` roots and `/private/tmp` working roots were never overwritten.
- All Stage 04 runs happened after the FIRST_ACTION pre-baseline existed; no run preceded it.

## 7. Implementation summary (what was built), with the §15.5 protocol and expectation changes

Product (only operator boundary `src/line_backup_acceptance/`, final hashes; no formal file touched):

| Module | Bytes | SHA-256 |
|---|---:|---|
| `authority.py` | 8952 | `984318a6…2afb1` |
| `cli.py` | 5169 | `16200355…3c49c` |
| `common.py` | 34351 | `df9fe0bc…60c0` |
| `status.py` | 7921 | `00e94973…b0f9` |
| `transaction.py` | 42064 | `3e535b66…9f1` |
| `verifier.py` | 25377 | `a07ffe45…23b6` |

Repairs delivered (Rev14 F1–F7 + Rev15/16/17/18 amendments): `case-01…25` allowlist and canonical children (config/run_log/backup_state) in `authority.py`; verifier axis contract incl. image structural decode, read-error axes and artifact manifest (F4); transaction dispatch window moved into `prepare`, persisted UNKNOWN ambiguity barrier, commit compare-and-swap under lock, finalize as the only terminal path with outcome-conditional `--verification-json`, duplicate/terminal evaluators, storage-fault oracles (F1–F3, F7); binding resolution split per §16.4 (user_fact at WORK root in production / case root in test mode).

Drivers/tooling: `tests/acceptance_case_driver.py` (Cases 01–25), `tests/verifier_fixture_driver.py` + literal `tests/verifier_fixture_manifest.json` (40 rows), `tests/status_fixture_driver.py` (19 rows), `tests/authority_negative_driver.py` (11 rows), `tests/legacy_false_positive_repro.py`, `tests/run_acceptance_wave.py`, `tests/automation_verification/{run_all.py,verify_evidence.py,harness.py,fixtures.py}` and `run_phase2_r1…r7`.

§15.5 ownership protocol applied to every shared-root file in the plan's list (`acceptance_case_driver`, `verifier_fixture_driver`, `status_fixture_driver`, `authority_negative_driver`, `authority_baseline`, `test_transaction_core`, `legacy_false_positive_repro`, `harness.py`, `fixtures.py`, every `run_phase2_r*.py`, `run_all.py`, `verify_evidence.py`): marker written before any fixture content; marker-adopt (`ensure_owned_root` adopts a root carrying any same-task marker, preserving it; `KEEP_ON_RESET` + `reset_owned_content` keep all drivers' `process-records/`/`driver-records/` append-only); no default removal; `--clean-owned` removes only roots carrying its own marker; a root without a marker (or a foreign task's marker) is never touched (`RootOwnershipError`). Evidence: R6-ownership `NO_DELETION_OBSERVED` with `destroyed=[]`, `markers_changed=[]`, `probes_changed=[]`, 53 probed roots, all three invoked drivers exit 0 (both orders).

Driver expectation updates (each with reason; no expectation was relaxed):
- `run_phase2_r1/r2/r3/r4`: converted from pre-fix reproductions to post-fix safe verdicts (F1–F3, F7 contract) — required because the pre-fix behaviour is now refused by the product; every row keeps its negative scenario and adds explicit zero-write/counter assertions.
- `run_phase2_r5_verifier_gaps.py`: rewritten to the product's measured axes vs independent oracle (forged binding → UNRESOLVED/exit 4/`INPUT_PROVENANCE_LIMITED`; dangling/SAFE_ABORT/non-terminal → Registry FAIL; read error → Filesystem FAIL, Registry/Source `NOT_RUN`, State `UNKNOWN`, exit 1, `INTERNAL_READ_ERROR`; truncated PNG / missing EOI / GIF → `DECODE_ERROR`/`UNSUPPORTED_IMAGE_TYPE`). Fixture construction also had to switch to `F.make_png()`/`F.make_run()` (RC2) — recorded reason: self-built JPEG bytes are structurally undecodable and non-RC2 runs are LEGACY-limited.
- `run_phase2_r6_status_selfcert.py`: scenario-table answers must carry `evidence_basis="scenario_table_non_acceptance"`; the old "byte-identical" expectation became "orthogonal axes identical; only the scenario branch adds the label key".
- `run_phase2_r6_harness_ownership.py`: flipped from "expect deletion" to `NO_DELETION_OBSERVED` (F6′).
- `run_phase2_r7_integration.py`: post-fix closed loop (`SAFE_R7_LOOP_CLOSED_AND_DUPLICATE_REFUSED`, 18/18).
- `status_fixture_driver.py`: 18→19 rows (adds §18.5 `baseline-worsened` after `baseline-unchanged`); `contradictory-axes` expectation corrected to the Rev18 tuple `(NOT_ACHIEVED, IN_PROGRESS, FAIL, NOT_RUN, PENDING, FIX_REQUIRED)`; adds `baseline-unavailable` INCOMPLETE / `INPUT_UNAVAILABLE`; asserts `evidence_basis` on every row.
- `acceptance_case_driver.py` case 22f: after the refusal assertion, the appended-byte tamper is preserved as `evidence/22f/tamper-evidence/result.json.appended-space` and `result.json` is restored so the chain manifest stays readable in the durable tree (original/tampered bytes+SHA recorded in the case note). Same class of recording fix in R4 b3 (newline variant) — both are recording fixes: the refusal itself is still asserted, and the raw tampered bytes remain in evidence.
- `legacy_false_positive_repro.py`: behaviour unchanged (still reproduces 56/58 legacy PASS); the file adopted the ownership protocol (`--clean-owned`, no rmtree).
- W-WAVE-RUN run 1 problems and their fixes are recorded verbatim in `attempt-02/run-history.json`; no expectation was loosened to reach PASS (the fixed runs re-assert the same oracles).

Commits (this wave, all after anchor `ba73bbf`): `42bffb3` baseline-pre attempt-02 · `898c6ec` product fix · `e33851e` Cases 01–25 · `24036a1` verifier 40 rows · `81f2b81` authority 11 rows · `56d60f0` status 19 rows · `175505f` R1–R4 ownership adoption · `c5184ec` R5–R7 rewrite · `4fa8588` run_all/verify_evidence · `d0c232f` R4/R6 recording fixes · `a71b3b4` attempt-02 evidence · `e0b397f` legacy adoption + case-22f + wave runner · `1979e6f` attempt-03 evidence · `32e130a` W-REAL-DESTINATION + W-ROUTE evidence · this record committed separately (its final sha256 is recorded in its own commit message).

## 8. Documented literal divergences (recorded; no semantic change)

- `read-error-sample-2`: the authoritative §16 axis matrix (plan.md:1195 unreadable-file, plan.md:1211 read-error row) pins State=`UNKNOWN`, exit 1, `INTERNAL_READ_ERROR`, while the Rev15 §15.4 prose at plan.md:735-736 lists State `NOT_RUN`. The drivers and the product follow the matrix; exit code and failure class are identical under both readings, so this is a recorded literal divergence, not a semantic decision. No waiver was applied.
- `contradictory-axes`: the old (Rev13-era) expectation tuple was stale; corrected to the Rev18 tuple as above (plan.md §18.5/§16.7).
- Reconcile oracle narrowing (§18.3): case-02 oracle asserts the exact persisted string `reconcile:reconcile.json:<sha256>`; case-03 asserts only "no new reconcile artifact + unchanged reference". No case gained assertions.
- Registry legacy axis (§18.1): `legacy-record` row is Registry `PASS` with `verified_run_id=null`; the `CASE_ROOT_25` real-state copy never matches (楨 U+6968 ≠ 禎 U+798E) and stays Registry `FAIL`.

## 9. Scoped blockers (workflow-routing §7.6 / plan.md:1424-1437)

- BLK-01
  - id: `BLK-01-SOURCE-CORRESPONDENCE`
  - scope: CORE_ACCEPTANCE
  - subject: `SOURCE_CORRESPONDENCE`
  - result: BLOCKED (UNRESOLVED)
  - class: AUTHORITY_REQUIRED
  - task_regression_evidence: NONE
  - evidence: `evidence/20260916-user-fact/source-identity-user-fact.json` (PARTIAL; part 2 UNANSWERED) + `reconciliation.json` (Source=UNRESOLVED, Registry=FAIL)
  - next_action: user answers the single part-2 question ("are those 57 files that album's backup?"); only then may an authoritative exact join or the §16.4 CONFIRMED v1 user-fact record resolve correspondence
  - owner: user (file owner)
  - waiver_allowed: NO
- BLK-02
  - id: `BLK-02-CUA-ROUTE-DECISION`
  - scope: CORE_ACCEPTANCE
  - subject: `CUA_ROUTE_DECISION`
  - result: BLOCKED (UNKNOWN)
  - class: AUTHORITY_REQUIRED
  - task_regression_evidence: NONE
  - evidence: `evidence/20260916-route/attempt-02/route-decision.json` (SAFE_ABORT_NO_GUI_INPUT; human_gate PENDING_USER; no dispatch)
  - next_action: one explicit human gate — exactly one current-target ellipsis observation on the exact scope, then stop (no Save-All/menu/chooser/state write)
  - owner: user
  - waiver_allowed: NO
- BLK-03
  - id: `BLK-03-INDEPENDENT-ACCEPTANCE`
  - scope: INDEPENDENT_ACCEPTANCE
  - subject: Stage 05 independent acceptance of this record and the real CLI evidence
  - result: NOT_RUN (PENDING)
  - class: AUTHORITY_REQUIRED (fresh verifier session; no product-code modification)
  - task_regression_evidence: NONE
  - evidence: this file + §6 roots
  - next_action: schedule the Stage 05 session; snapshot the carry-forward fields below first
  - owner: Stage 05 verifier (separate session, orchestrated by user)
  - waiver_allowed: NO

## 10. Stage 05 carry-forward snapshot (immutable Stage 04 facts)

- STAGE_04_REPORTED_PRIMARY_OUTCOME_STATUS: `UNKNOWN`
- STAGE_04_REPORTED_IMPLEMENTATION_STATUS: `COMPLETE`
- STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS: `BLOCKED`
- STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS: `PASS`
- STAGE_04_REPORTED_INDEPENDENT_ACCEPTANCE_STATUS: `PENDING`
- STAGE_04_REPORTED_TASK_CLOSURE_STATUS: `CORE_ACCEPTANCE_BLOCKED`
- STAGE_04_REPORTED_BASELINE_DELTA: `UNCHANGED` (`ab6747f2…85b5`, 19,005 bytes pre and post)
- STAGE_04_EXECUTION_ARTIFACT: `.agent/tasks/T20260916-0102-01-line-backup-acceptance/execution.md` (SHA-256 computed from the final committed bytes and recorded in this file's own commit message; Stage 05 must recompute it)
- TASK_ID: `T20260916-0102-01-line-backup-acceptance`; PLAN_REVISION: `18`; HANDOFF_SHA256: `9cf01d4e…46c6`
- Evidence path: `evidence/20260916-auto-verification/attempt-02/`, `evidence/20260916-acceptance/attempt-03/`, `evidence/20260916-baseline/attempt-02/`, `evidence/20260916-product-verify/attempt-04/`, `evidence/20260916-route/attempt-02/`
- Recorded at: `2026-09-17` (local) / Stage 04 wave end
- Stage 05 must freshness-check this file and, per §7.8, must not downgrade proven implementation because acceptance could not run.

## 11. Next action (single, precise)

The next discriminating experiment is one explicit Human Gate for observation only — with the exact target album card already visible in LINE, allow exactly one current-target ellipsis input, capture immediate post evidence, and stop before any menu-item/Save-All/chooser input or state write. It is not download authorization. In parallel the user may answer the still-open part-2 question above; that single fact (or an authoritative exact join) is the only route to `SOURCE_CORRESPONDENCE=CONFIRMED`. Until then: PRIMARY_OUTCOME stays UNKNOWN, CORE_ACCEPTANCE stays BLOCKED, no production dispatch, no DONE.

## 12. Key artifact index (SHA-256 / bytes)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `evidence/20260916-baseline/attempt-02/baseline-pre.json` | 19005 | `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5` |
| `evidence/20260916-baseline/attempt-02/baseline-pre.meta.json` | 2137 | `eaba57bd4ac3e09aa47ae309e66999b06259b72ad48e5a176d612b13bc601e60` |
| `evidence/20260916-auto-verification/attempt-02/run-all-summary.json` | 25531 | `aebc2b5d3329779f46b26b51b2495fa5893cabc3d46b129c3264063fcee92a3e` |
| `evidence/20260916-auto-verification/attempt-02/run-history.json` | 4498 | `87014375462e3c4e90c37ecf96905b2a236b2e651fe78422b8f6bd1855d1b533` |
| `…/attempt-02/order-driver-first/manifest.json` | 280075 | `3ca40f434cf3be38f410d22748f09a209477f67ee783612475c06ebb86e605c4` |
| `…/attempt-02/order-ownership-first/manifest.json` | 280078 | `d262d0412fb1fea52ac163de48aaa4e61615405a878c5ef7941078dacddd194b` |
| `evidence/20260916-acceptance/attempt-03/acceptance-observation.json` | 73622 | `6563228d07245db88b4f22204dff47d0973cea9159476895fd52fae6bc237513` |
| `evidence/20260916-acceptance/attempt-03/verifier-summary.json` | 1358368 | `2571beaf8ed7faa8aa396c5bc8a10eea8a587d571d03225a38099dfe90fd52c2` |
| `evidence/20260916-acceptance/attempt-03/verifier-fixture-rows.json` | 112345 | `e189622b5727a4824485cbbeaac1aeea4a2b70e719da983f6f8a23d5b2d43b0e` |
| `evidence/20260916-acceptance/attempt-03/status-summary.json` | 71016 | `e5b14e0d7394c70c51cce827495ea9f187eccec1b3885291aa9240ab0e737890` |
| `evidence/20260916-acceptance/attempt-03/status-rows.json` | 39242 | `48697c5872cd45605d7246e5e83cd2a3dabfcb0540a90669c244fb95aa0f3308` |
| `evidence/20260916-acceptance/attempt-03/authority-summary.json` | 56272 | `83c50f1ccf6dc6f56b595ac3a22faf961192e88163fecbcd74957f3617c9f515` |
| `evidence/20260916-acceptance/attempt-03/legacy-false-positive-summary.json` | 1365 | `974896748a5ec2eabfed87d3a0a00d1050216acaff47303fef58fe384b5620b2` |
| `evidence/20260916-acceptance/attempt-03/manifest.json` | 433500 | `c4f3db954b27767003415fe844aea747f380c962bc77c187f1d28ce8227f0412` |
| `evidence/20260916-acceptance/attempt-03/readback-verification.json` | 317 | `d2d95ff578dc086ac32ed2788f5a3a4267cf1f3b76a9c13b3adab22f23f7a3df` |
| `evidence/20260916-product-verify/attempt-04/reconciliation.json` | 27291 | `e9d96433bdd5545bd156a80ab298c72fdcc013a8011340764dbf3f8ba4eba4da` |
| `evidence/20260916-product-verify/attempt-04/manifest.json` | 2236 | `8788a67e16f2a278a14fc4197db7ecfafc086912695512f980137d32eb2c604d` |
| `evidence/20260916-route/attempt-02/route-decision.json` | 4091 | `1bb31fe3677eb3a08052eac30fc9362243f637f0f0785ee1885265515a39326b` |
| `evidence/20260916-user-fact/source-identity-user-fact.json` | 5530 | `8af8c6fc1459bb77183f81122a23bd10799fb79060fb04f86abb792600e00fa4` |

## 13. Boundary compliance (attestation)

Formal config/state/run-log/registry/intent and the 57 photos: read-only, zero writes, zero redownloads, zero normalization; `禎` U+798E and `楨` U+6968 never merged or exchanged. No sudo/sfltool/TCC, no authorization dialogs, no GUI/AX/Computer-Use input in this session. Evidence append-only (prior attempts preserved, failed-run1 preserved); `/private/tmp` used as working space only with durable SHA-256/bytes manifests; no PASS was produced by self-written assertions, and no expectation was relaxed to reach PASS.
