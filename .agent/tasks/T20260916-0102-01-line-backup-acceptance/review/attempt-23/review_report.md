# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 23
- REVIEWED_PLAN_REVISION: 17
- REVIEWED_PLAN_SHA256: 5dd7ab19ce16175fb8e091762d73a50cebb6415ab895342c00a9a015ea1b866f
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-23/plan_snapshot.md (byte-identical snapshot, same SHA-256; plan.md re-hashed before and after this review and unchanged; 1391 lines)
- Repository anchor observed: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup; plan.md:3-4 declares `TASK_ID: T20260916-0102-01-line-backup-acceptance`, `PLAN_REVISION: 17`, `PLAN_STATUS: CANDIDATE` (reviewable)
- Reviewer runtime/model: Codex CLI agent; this is the second independent reviewer for revision 17 and did not open or read `review/attempt-22/` or coordinate with any other reviewer for this revision
- Boundary compliance: read-only for plan.md and all product code; only `review/attempt-23/` was written; no product CLI/driver/test was executed; no re-download; formal state/destination/57 photos and all prior review attempts were not touched

## OWNER_VERDICT
Plain-language, for the owner:

- **Primary goal:** two results, both required and reported separately — (1) the **album-data result**: whether the existing 57 photos are a valid backup of the exact LINE album 旻謙允禎成長日記, 2024/05/13～05/17, 57 images, established read-only with no re-download; and (2) the **proven reusable automation path**: the R1–R7 repairs exercised end-to-end through the real operator CLI with rerunnable, independently verifiable evidence.
- **Essential / must not break:** the formal state and destination stay read-only; the 禎 (U+798E) and 楨 (U+6968) spellings are never merged; authority validation happens before any read or write; every fixture oracle is computed before product output; evidence is append-only and hash-bound; acceptance is independent. Each of these has a concrete data-safety reason, not paperwork.
- **Best-effort / deferred / non-gating:** bridge/menu-discovery readiness, documentation-retention health (pre-existing repository debt, disclosed and waivable with the original FAIL preserved), and any reporting convenience. No supporting item can block the core path; no production download is authorized this wave.
- **What may block everything and why:** loss or corruption of the only real state copy, a cross-root authority bypass, or an unsound finalize evidence chain. The plan's global vetoes for these each protect the real data, so they are proportionate.
- **Revision 17 verdict:** the Rev16 structure defects are genuinely repaired — one executable test-mode grammar, the acyclic verification-evidence chain v2, a single-valued legacy mutation rule, Case-20 orphan mechanics, the 19th status row, the 20–25 routing/counter oracles, and the corrected evidence roots. However, one **MAJOR** semantic contradiction survives in the legacy read contract (the Registry axis is stated two ways and the executable `legacy-record` row cannot satisfy the general sentence), plus several MINOR residuals. A handoff cannot be compiled at this hash.
- **Complexity verdict:** proportionate. Chain v2 replaced a self-referential v1 scheme with a one-direction write order; no new unjustified abstraction, dependency, or gate was introduced by Rev17.
- **Biggest remaining risk:** the album-data result may legitimately end at Filesystem PASS / Source UNRESOLVED / overall UNKNOWN because the formal state cannot prove provenance. The plan rightly refuses to convert that into a PASS; the remaining work is textual contract consistency so Stage 03/04 cannot implement the wrong reading.

## GOAL_BASELINE
Reconstructed from the authoritative user request before auditing the Plan's rationale:

- **Primary outcome (both required; reported as separate subjects):** (1) the album-data result — safely and read-only establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group 旻謙允禎成長日記, album 2024/05/13～05/17, 57 images, and otherwise stop without an ambiguous or duplicate production transaction; (2) the proven reusable automation path — the R1–R7 repairs executed end-to-end by the operator CLI with rerunnable, independently readable evidence. Neither result may be claimed from offline or fixture PASS, and paperwork is no substitute.
- **CORE (each traces to the goal or a safety/correctness obligation):** read-only formal config/state/destination and the 57 photos; the 禎 U+798E / 楨 U+6968 separation (never merged); one closed-loop transaction case (prepare → verify → commit → finalize → verify → duplicate-check → terminal resume); per-case independent oracles computed before product output; append-only hash-bound evidence; independent acceptance; no state/registry/owner mutation outside isolated fixtures.
- **SUPPORTING / non-gating:** bridge readiness, documentation-retention health (pre-existing debt, waivable, original FAIL preserved), convenience/reporting fields.
- **Global vetoes and why:** authority validation (protects the real state and destination from cross-root reads/writes), state lock/owner/registry invariants (protects at-most-once Save-All semantics), strict validation before replacement (schema integrity), the finalize verification-evidence chain (prevents an unverifiable payload from finalizing), fixture isolation. Each is a safety/correctness veto, not a completeness veto.
- **Biggest risk as the owner should hear it:** the 57 files can be valid while source provenance is not provable from the existing state; the honest outcome is then overall UNKNOWN with the source/core check BLOCKED, never a PASS.

## GOAL_ALIGNMENT
- plan.md:936 `PRIMARY_OUTCOME (Rev16 §16.8)` names exactly the two baseline results together ("(1) safely establish whether the existing 57-image destination is a valid backup … and (2) leave the reusable automation path itself proven through the real entry") and states "Neither result may be claimed from offline or fixture PASS".
- plan.md:891 keeps the album-data result as its own subject; plan.md:1385-1387 require exact source correspondence (authoritative exact join or one precise user fact) for `DONE` and explicitly preserve `UNKNOWN`/`BLOCKED` rather than downgrading or promoting: "`UNRESOLVED`, `LEGACY_PROVENANCE_LIMITED`, or `CONTRADICTED` cannot be promoted to closure." This matches the baseline's honest-UNKNOWN requirement.
- Acceptance criteria prove outcomes, not implementation completeness: Case 20 is the R1 proof (plan.md:250), the Case-01 loop proves the end-to-end path, and the real verify-only pass targets the real destination (plan.md:1007, evidence root `attempt-04`).
- No supporting artifact has become the project goal. The only top-down-adjacent issue is the over-broad legacy sentence in RV-23-1 below; that is a semantic-contract wording defect, not a misaligned objective.

## NECESSITY_AND_TRACEABILITY
- Every §17.1–§17.10 subsection names the finding it corrects, and every corrected item traces to one of: the two prior reviews (attempt-20 RV-1…RV-11, attempt-21 RV-1…RV-6) or the planner self-audit G1/G2, which name the same defects as attempt-20 RV-11/RV-7 (plan.md:17-25).
- Cases 20–25 trace to real reproduced gaps: R1 dispatch continuity (Case 20, plan.md:222), R4 finalize trust (Case 22, plan.md:277-282), R3 duplicate safety (Cases 15–17), user-fact/merge guard (Case 24), legacy read of the real state (Case 25, plan.md:362-369). All are CORE for at least one of the two required results.
- The authority rows and negatives trace to the safety invariant, not to completeness (plan.md:1162-1167).
- Documentation-retention health is correctly classified as scoped, non-blocking, waivable debt with the original FAIL preserved (plan.md:1332-1335) — no global veto without safety rationale.
- No untraceable significant work item was found in Rev17's changes.

## GATE_AND_VETO_AUDIT
- Authority-first is preserved and expanded: "Authority validation is the first filesystem operation after argument parsing, before loading state/config, deriving a lock path, creating a control directory, or touching any path outside the isolated evidence directory" (plan.md:1018); every case root is one literal `-01`…`-25` root with canonical children (plan.md:1194).
- The unjustified read-time global veto is corrected: validation scope is exactly "(i) the payload about to be replaced and (ii) every new RC2 record … reading an existing authority state is never gated by it" (plan.md:90-92, plan.md:1024). Attempt-20 RV-2 is closed.
- Mutation refusal is proportional: any mutation whose target state contains a non-strictly-valid run is refused `INVALID_STATE_LEGACY` exit 4 with no write (plan.md:358-361), matching 25b (plan.md:367-369).
- The legacy read path reports instead of refusing (plan.md:345-352), so the real formal state stays readable — necessary for the album-data result.
- One proportionality defect remains in wording: the general sentence at plan.md:99-104 / 354-358 says a tolerated-legacy run yields Registry FAIL and "Registry and Source never PASS", which would make the legitimate association-only Registry PASS impossible for matching imported records (see RV-23-1). This is an over-broad veto statement, not a new gate.

## COUPLING_AND_FAILURE_CONTAINMENT
- The four axes remain independent (Filesystem / Registry / Source / State) with overall `UNKNOWN` for unresolved provenance: "Filesystem PASS never implies registry/source/state PASS; registry/source-only defects retain filesystem PASS" (plan.md:1161); the Registry axis is association integrity only and "Provenance failures … never flip the Registry axis" (plan.md:1158).
- Failure containment is at the narrowest boundary: one canonical state per case root; writes confined to evidence-dir; authority failure has "zero state replacement, zero dispatch, zero registry mutation and only isolated error evidence" (plan.md:1027).
- Case-failure routing is now extended to 20–25 (plan.md:1243) with per-case counter oracles (plan.md:1248), closing the prior containment gap.
- The one residual collapse risk is exactly RV-23-1: the §17.3/§16.5 sentence would merge the Registry axis into the provenance axis in general, which attempt-21 RV-5 was raised to prevent. It survives re-worded.

## DESIGN_ECONOMY
- Chain v2 (plan.md:52-88) is a genuine simplification: one-direction write order (other artifacts → `result.json` carrying `verification_evidence{manifest_path, manifest_bytes}` "never a hash of itself" → `manifest.json` written last with the `result.json` entry plus `result_summary` and `result_bytes`/`result_sha256`), SHA-256 over raw bytes, no canonicalization rule, and a pinned recompute order for `commit`/`finalize`. No cycle exists.
- The single test-mode grammar deletes the former variant instead of layering: "the former 'test mode omits config/run-log' rule is deleted" (plan.md:203-205).
- The `prepare`-may-append exception is deleted rather than annotated (plan.md:104, 360-361).
- No new dependency was added; the remaining defects need only wording changes. Deletion test: no Rev17 addition could be removed without reopening a named prior finding.

## CRITICAL_PATH_AND_PRIORITY
- The CORE path is ordered correctly: R1–R7 repairs → isolated fixture harness → the real read-only pass and the closed loop, with status/paperwork support after. The plan keeps the real verify-only pass and the one closed loop as the two deciding artifacts (plan.md:891-905, 1007).
- Supporting items (bridge readiness, retention health) do not consume the critical path and cannot veto it.
- Sequencing concern for Stage 03/04: the surviving semantic contradiction (RV-23-1) sits on the legacy-read path used by the real-state evidence, so it must be fixed textually before implementation begins; it does not require re-architecting.

## REQUIREMENT_FIDELITY
- Read-only fences are intact: "The formal DATA_PROJECT_ROOT is read-only even when selected" (plan.md:1026) and "no production download is authorized in this wave" (plan.md:9).
- The exact album identity (group key with 禎 U+798E, start 2024-05-13, end 2024-05-17, 57 images) appears in the executable literals and is never merged with 楨 U+6968; plan.md:108-112 pins `raw_requested_group` byte-for-byte with "禎 U+798E is never equal to 楨 U+6968".
- No fixture back door: "No fix may change an expectation, relax an authority allowlist, or add a fixture-only back door in order to pass a test." (plan.md:748).
- No out-of-scope product behavior was smuggled into the correction wave; every change is a correction of a named finding.

## GROUNDING_AND_DRIFT
- Evidence roots are corrected and pinned: product verify-only targets `evidence/20260916-product-verify/attempt-04` (plan.md:1007; plan.md:148-149), baseline copy targets `evidence/20260916-baseline/attempt-02` (plan.md:148-149), Stage-05 acceptance at `e2e/attempt-04/` (plan.md:452), and the two-order Phase-2 wave lives under `attempt-02/order-ownership-first/` and `attempt-02/order-driver-first/` with per-driver subdirectories and their own `readback-verification.json` (plan.md:445-448; plan.md:150-153). The planned-file heading is correct (plan.md:150).
- Range drift is corrected: "the literal root set is `-01`…`-25`" (plan.md:419); every literal scanned uses `CASE_ROOT_NN` at `NN = 01…25` (plan.md:37).
- `attempt-01` references remaining in the text are read-only provenance descriptions (plan.md:149 "every `attempt-01` root stays read-only provenance", plan.md:722 Phase-0/Phase-1 record), not new write targets. Attempt-20 RV-10 and attempt-21 RV-3 are closed.
- Residual drift: the closure section still binds Stage 03 to `PLAN_REVISION=16` (plan.md:1377) and Stage 02 to "this Revision 16" (plan.md:1379), and three leftover supersession sentences name the corrected-away grammar (plan.md:220, 419, and the range sentence at plan.md:149). See RV-23-4.

## ARCHITECTURE_AND_CONTRACTS
- The verification-evidence chain is acyclic and single-direction (plan.md:52-77): `result.json` carries only `{manifest_path, manifest_bytes}` for the manifest and never a hash of itself; `manifest.json` is written last and includes the `result.json` entry plus `result_summary`, `result_bytes` and `result_sha256`; `commit`/`finalize` read the result bytes, locate the manifest beside it, require field/byte equality in both directions, re-hash every listed artifact, then apply the F3 gates; missing/malformed/mismatching is `INVALID_VERIFICATION_EVIDENCE`, another run's identity is `VERIFICATION_RUN_MISMATCH`, both exit 4 with no revision change (plan.md:71-77). The `--run-id` rule is pinned: absent → `run_id` null and "neither `commit` nor `finalize` may consume that result" (plan.md:87-88). Rows 22a–22f make the enforceable part executable (plan.md:79-81, 277-282).
- The legacy read contract is *almost* single-valued: the tolerant shapes and their `legacy_normalizations[] {run_id, kind, detail}` list are pinned (plan.md:97-104, 349-352), the `prepare`-may-append exception is deleted (plan.md:104, 360-361), and the read mapping (Filesystem PASS preserved / Registry FAIL / Source UNRESOLVED / State `LEGACY_PROVENANCE_LIMITED` / overall `UNKNOWN` / exit 4 / `INPUT_PROVENANCE_LIMITED`) is asserted for 25a (plan.md:366-369). The defect is that this mapping is stated as the general rule for every tolerated-legacy run, contradicting the association-driven Registry axis and the `legacy-record` executable row (RV-23-1).
- Public/load-bearing contracts (status semantic rows, exit codes, refusal classes, `evidence_basis == "scenario_table_non_acceptance"`) are preserved and made executable (plan.md:1343-1348).

## DATA_SECURITY_RELIABILITY
- The real copies are protected: formal state read-only, no rewrite of legacy state, no re-download, fixture isolation with literal roots, and authority failures producing only isolated error evidence (plan.md:1026-1027).
- Rollback/containment: guarded replacements, read-back before/after replacement, `READBACK_UNCERTAIN`, owner/lock release rules, and the Case-20 kill-aftermath oracle (state bytes byte-identical, no revision-2 record, only the empty lock remainder inside `CASE_ROOT_20/state/`) are all present (plan.md:234-245).
- The evidence chain's honest scope statement replaces the false v1 authorship claim ("It is not an authorship proof and does not survive a writer who may rewrite that directory", plan.md:79-81) — correct and safer.
- Residual reliability concern: RV-23-1's wording could be implemented as a real behavior (refusing Registry PASS for matching legacy records), which would weaken the verifier's ability to recognize a valid association-only match; fix the text.

## IMPLEMENTATION_SEQUENCE
- The sequence is coherent: fix the named contract defects → build isolated fixtures → run the 25-case matrix + verifier/authority/status/legacy drivers → real read-only verify pass → independent acceptance; no step depends on a later one.
- The corrected grammar removes the prior impossible step (test-mode transaction commands without canonical children), so Stage 04 can implement one grammar.
- The one sequencing risk is documentation-only: Stage 03 could bind the handoff to the stale `PLAN_REVISION=16` literal (RV-23-4) if it trusts the closure paragraph over the header hash; the SHA binding mitigates but the literal must be corrected.

## TESTABILITY_AND_ACCEPTANCE
- Every acceptance row has an independent oracle computed before product output (plan.md:1245-1246), and "A product PASS line is never an oracle" (plan.md:1248).
- Failure routing and counter oracles for 20–25 are complete and match the reproduced gaps: 20/23 stop recovery/duplicate-safety acceptance; 21/22/24/25 are product/test regressions (plan.md:1243); counters 20 = one before the kill and one after recovery, 21 = 0, 22 = untouched by all six finalize refusals, 23a/b = 0, 23c = 1, 24 = 0, 25a/b = 0 (plan.md:1248).
- Case 20 mechanics are executable as written: dispatcher is a child process, the adapter polls `os.getppid()` every 0.25 s and self-exits ≤10 s after reparenting, the driver records the observed reparenting, and a forced kill after 15 s is `orphan-forced-kill` → fixture failure/TASK_REGRESSION (plan.md:117-127, 234-239).
- The 19th status row is fully specified with the baseline-worsened tuple and routing per §7.7 rule 8: PRIMARY ACHIEVED / IMPLEMENTATION COMPLETE / CORE PASS / REQUIRED_VERIFICATION FAIL / INDEPENDENT PENDING / CLOSURE FIX_REQUIRED / blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` (plan.md:133-137, 1348), and the manifest enumerates 19 rows including `baseline-worsened` (plan.md:1348).
- Remaining testability defects are the RV-23-1 row/rule contradiction and the two MINOR oracle-claim gaps (RV-23-2, RV-23-3, RV-23-5).

## SCOPE_AND_COMPLEXITY
- Scope is the same verified wave: no new product scope, no production download, no GUI expansion; Rev17 is a corrections revision of named defects only (plan.md:17-30).
- Complexity is justified per item and two prior complexities were deleted (the append exception; the test-mode-omits-children variant). The remaining changes are wording corrections.
- No priority inversion: no supporting item consumes the critical path while CORE acceptance is unresolved.

## FINDINGS

### RV-23-1 — `MAJOR` — SEMANTIC_CONTRACT (legacy Registry axis stated two ways; executable row unsatisfiable against the general sentence)
Affected: plan.md:99-104 (§17.3), plan.md:354-358 (§16.5), against plan.md:655 (§15.4 axis rule), plan.md:1140 (matrix row `legacy-record`), plan.md:1158 (§16.8 Registry-axis rule).

Evidence for the defect:
- plan.md:99-104 / 354-358: "a tolerated-legacy or unreadable run yields Filesystem PASS preserved (an independent axis), Registry FAIL, Source UNRESOLVED, State `LEGACY_PROVENANCE_LIMITED`, overall `UNKNOWN`, exit 4 … Registry and Source never PASS; Filesystem may." and the v1 correction "Registry and Source never PASS".
- plan.md:655: "A null `verified_run_id` is the contract's imported-evidence form: Registry PASS with Source UNRESOLVED / `LEGACY_PROVENANCE_LIMITED`." Identical statement at plan.md:1158: "a null `verified_run_id` is the contract's imported-evidence form (Registry PASS, Source UNRESOLVED)."
- plan.md:1140 (executable matrix row): "| Legacy/imported record without contract_revision or binding, `verified_run_id` null | PASS | PASS | UNRESOLVED | LEGACY_PROVENANCE_LIMITED | UNKNOWN | 4 | INPUT_PROVENANCE_LIMITED | PASS |" — the second column is Registry `PASS`.

Failure/rework mechanism: a Stage-04 implementer following the general sentence must make every tolerated-legacy match yield Registry FAIL, which directly contradicts the `legacy-record` row's independent oracle (Registry PASS) and the association-only axis rule; following the row leaves the normative sentence false. This is the same axis collapse attempt-21 RV-5 required to be removed, surviving re-worded in the same document, and the plan's own claim "no … surviving contradicting literal" (plan.md:24-25) is therefore false for this item.

Smallest required correction: scope the sentence to the CASE_ROOT_25 real-state shape, where Registry FAIL is produced by the persisted 楨 U+6968 keys not matching the requested 禎 U+798E album (association mismatch), and state the general rule once: Registry is association-integrity-driven, so a matching legacy/imported entry with null `verified_run_id` (the `legacy-record` fixture) is Registry PASS / Source UNRESOLVED / `LEGACY_PROVENANCE_LIMITED`, while an unreadable or non-matching run yields Registry FAIL.

### RV-23-2 — `MINOR` — COMPATIBILITY / TEST (finalize grammar annotation claim not true of both statements)
Affected: plan.md:159-161 (§17.9), plan.md:1016 (production grammar), plan.md:1197 (case protocol).
Evidence: plan.md:159-161: "`finalize`'s `--verification-json` is outcome-conditional in both grammar statements: required for `--outcome VERIFIED`, optional for `SAFE_ABORT` …". The case-protocol statement carries the annotation ("`--verification-json` is required for `--outcome VERIFIED` and optional for `SAFE_ABORT`", plan.md:1197), but the production grammar statement still reads "`transaction finalize --project-root PATH --config PATH --run-log PATH --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --outcome VERIFIED|SAFE_ABORT --verification-json PATH --evidence-dir PATH`" (plan.md:1016) with no conditional marking.
Mechanism: a reader implementing the production form from the grammar list could require `--verification-json` for SAFE_ABORT; the §15.x rule (plan.md:411-414) and the case protocol forbid that. MINOR because the normative rule exists twice elsewhere; fix by annotating the production grammar or by narrowing the §17.9 claim.

### RV-23-3 — `MINOR` — GROUNDING (case-02/03/19 reconcile-oracle claim not present in all three oracles)
Affected: plan.md:162-163 (§17.9), plan.md:375 (§16.6).
Evidence: plan.md:162-163: "The case-02/03/19 oracles assert the persisted reference form `reconcile:<relpath>:<sha256>` for the artifact each of them produces"; plan.md:375 repeats "The case-02/03/19 oracles assert the exact persisted string form of the reference they produce." Only Case 02 does: "an `evidence` string asserted to be exactly `reconcile:reconcile.json:<sha256 of reconcile.json>`" (plan.md:1232). Case 03 asserts only "no new reconcile artifact is written, so the persisted reference is unchanged" (plan.md:1233), and Case 19's oracle contains no reconcile-reference assertion at all (plan.md:1242).
Mechanism: an over-claim that could lead Stage 04/05 to look for non-existent assertions; no unsatisfiability (the §16.6 grammar itself is pinned). Fix the claim to name Case 02 only, or add the literal assertion to Case 03/19.

### RV-23-4 — `MINOR` — HANDOFF / consistency (stale revision and supersession literals survive)
Affected: plan.md:1377, 1379, 220, 419, 149.
Evidence: "Stage 03 must create a fresh handoff bound to TASK_ID, PLAN_REVISION=16, the approved plan SHA …" (plan.md:1377) and "Stage 02 must independently review this Revision 16 and its exact hash." (plan.md:1379), against the header "PLAN_REVISION: 17" (plan.md:4). Leftover supersession sentences also survive: "every earlier line that named `CASE_ROOT_NN/state.json` or 'through -19' is superseded accordingly" (plan.md:220); "every 'through -19' phrase is superseded by 'through -25'" (plan.md:419); and the range sentence at plan.md:149.
Mechanism: Stage 03 could bind the handoff to the wrong revision literal; the supersession sentences contradict the plan's own "no new supersession layer" claim (plan.md:24-25). Fix: update the closure literals to revision 17 (or refer to "the current `PLAN_REVISION`"), and restate the leftover sentences as direct corrections.

### RV-23-5 — `MINOR` — TEST (19th status row absent from the fixture table)
Affected: plan.md:1325-1342 (table), plan.md:128-137 (§17.6), plan.md:1348 (enumeration).
Evidence: the table lists 18 rows (candidate … done) and never contains `baseline-worsened`; the nineteenth row exists only in §17.6 and the manifest enumeration: "The literal manifest enumerates the 19 rows by ID … `baseline-worsened` … expects PRIMARY `ACHIEVED`, IMPLEMENTATION `COMPLETE`, CORE `PASS`, REQUIRED_VERIFICATION `FAIL`, INDEPENDENT `PENDING`, CLOSURE `FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION`" (plan.md:1348).
Mechanism: executable content stays single-valued (enumeration + §17.6 give the full tuple), but the table/text pair still reads "18 versus 19" and invites the same drift G2 raised. Fix: add the row to the table or state explicitly that the table is the 18 pre-existing rows and §17.6 defines the 19th.

### Disposition of attempt-20 RV-1…RV-11, attempt-21 RV-1…RV-6, and planner G1/G2
| Item (prior review) | Disposition | Evidence |
|---|---|---|
| attempt-20 RV-1 — test-mode argv non-executable (MAJOR) | **Fixed** | plan.md:34-38, 201-205, 1194: one grammar `--project-root CASE_ROOT_NN --config …/config/line_backup_config.json --run-log …/state/run_log.md --state …/state/backup_state.json --test-mode`, `NN = 01…25`; `--state CASE_ROOT_NN/state.json` appears only as declared-illegal (plan.md:44, 205); five root-bearing negatives carry present-but-mismatched canonical children and the sixth missing-`--project-root` parser negative is explicitly separate (plan.md:50, 1164). |
| attempt-20 RV-2 — legacy validation stated two contradictory ways (MAJOR) | **Fixed** | plan.md:90-92, 1024: validation scope is exactly (i) payload about to be replaced (ii) new RC2 records; reading an existing authority state is never gated. No surviving "at every load" normative sentence. |
| attempt-20 RV-3 — chain v1 not implementable (MAJOR) | **Fixed** | plan.md:52-88: chain v2 as in ARCHITECTURE_AND_CONTRACTS above. |
| attempt-20 RV-4 — v1 user-fact equality anchors (MAJOR) | **Fixed** | plan.md:108-112: anchors are `app_identifier`, `raw_requested_group` (byte-for-byte; 禎 U+798E never equals 楨 U+6968) and `fingerprint` on all three fields; no `group_key` key required. |
| attempt-20 RV-5 — Case 20 false mechanism/over-broad remainder (MAJOR) | **Fixed** | plan.md:117-127, 234-245: child dispatcher, `os.getppid()` poll every 0.25 s, self-exit ≤10 s of reparenting, driver records reparenting, forced kill after 15 s = `orphan-forced-kill` fixture failure/TASK_REGRESSION, remainder scoped to `CASE_ROOT_20/state/`. |
| attempt-20 RV-6 — case-07 replacement count (MINOR) | **Fixed** | plan.md:156-158 and the Case-07 protocol: exactly two guarded replacements by the winner, zero by the loser, exactly one counter line overall. |
| attempt-20 RV-7 — status manifest count/ID list stale (MINOR) | **Fixed** | plan.md:1348: 19-row enumeration with `baseline-worsened` listed directly after `baseline-unchanged`; §17.6 (plan.md:128-137). Table residue recorded as RV-23-5 (MINOR). |
| attempt-20 RV-8 — finalize grammar unconditional (MINOR) | **Not fully fixed** (partial) | Case-protocol annotation present (plan.md:1197); production grammar still unannotated (plan.md:1016). See RV-23-2. |
| attempt-20 RV-9 — §16.6 oracle-assertion claim absent from oracles (MINOR) | **Not fully fixed** (partial) | Case 02 asserts (plan.md:1232); Case 03 (plan.md:1233) and Case 19 (plan.md:1242) do not. See RV-23-3. |
| attempt-20 RV-10 — stale roots/paths (MINOR) | **Fixed** | plan.md:148-153, 442-456, 1007: attempt-04 / attempt-02 / e2e attempt-04 / two-order dirs under attempt-02; `attempt-01` kept only as read-only provenance. |
| attempt-20 RV-11 — routing not extended to 20–25 (MINOR) | **Fixed** | plan.md:1243, 1248: routing and counter oracles for 20–25 with 20/23 as recovery/duplicate-safety stops and 21/22/24/25 as regressions. |
| attempt-21 RV-1 — chain self-reference (BLOCKER) | **Fixed** | plan.md:52-77, 277-282: acyclic v2 + rows 22a–22f. |
| attempt-21 RV-2 — grammar literals (MAJOR) | **Fixed** | Same evidence as attempt-20 RV-1. |
| attempt-21 RV-3 — evidence roots (MAJOR) | **Fixed** | plan.md:148-153, 445-448, 1007. |
| attempt-21 RV-4 — 19th status row (MAJOR) | **Fixed** (table residue MINOR) | plan.md:133-137, 1348; residue recorded as RV-23-5. |
| attempt-21 RV-5 — legacy axis collapse (MAJOR) | **Not fully fixed** (partial) | The v1 "never becomes …" sentence was corrected, but the replacement over-generalizes `Registry FAIL … Registry and Source never PASS` for tolerated-legacy runs and contradicts plan.md:655/1140/1158. See RV-23-1 (MAJOR). |
| attempt-21 RV-6 — legacy-state mutation / prepare-append exception (MAJOR) | **Fixed** | plan.md:104, 358-361: exception deleted; `INVALID_STATE_LEGACY` exit 4 with no write; 25b asserts it. |
| planner G1 — failure routing/counters for 20–25 | **Fixed** | plan.md:1243, 1248; matches attempt-20 RV-11 evidence. |
| planner G2 — 18 vs 19 rows | **Fixed** (table residue MINOR) | plan.md:1348 enumeration; residue RV-23-5. |

## REQUIRED_PLAN_CHANGES
1. **RV-23-1 (MAJOR, must fix):** make the legacy Registry axis single-valued. Rewrite plan.md:99-104 / 354-358 so the `Registry FAIL / Source UNRESOLVED / LEGACY_PROVENANCE_LIMITED / overall UNKNOWN / exit 4` tuple is scoped to (a) the CASE_ROOT_25 real-state copy (no association match for the requested 禎 U+798E album) and (b) unreadable or non-matching runs, and state that a matching legacy/imported record with null `verified_run_id` is Registry PASS / Source UNRESOLVED / `LEGACY_PROVENANCE_LIMITED` per plan.md:655/1158/1140. No other part of the mapping changes.
2. **RV-23-2 (MINOR):** annotate the production `finalize` grammar (plan.md:1016) as outcome-conditional for `--verification-json`, or narrow the "both grammar statements" claim.
3. **RV-23-3 (MINOR):** correct the case-02/03/19 reconcile-assertion claim (plan.md:162-163, 375) to match the actual oracles, or add the missing assertions.
4. **RV-23-4 (MINOR):** update the closure literals to revision 17 (plan.md:1377, 1379) and restate the leftover supersession sentences (plan.md:149, 220, 419) as direct corrections.
5. **RV-23-5 (MINOR):** add the `baseline-worsened` row to the status fixture table (plan.md:1325-1342) or state the table/§17.6 split explicitly.

## RESIDUAL_MINOR_NOTES
- After the changes above, no other surviving literal was found that contradicts a corrected item. The test-mode grammar scan across the document found no test-mode literal missing the canonical children (continuation-line hits were prose wraps; the only `--state …/state.json` occurrences are the two illegal-declaration sentences at plan.md:44 and 205).
- The plan correctly keeps the honest failure mode visible: if the formal state cannot prove provenance, `PRIMARY_OUTCOME_STATUS=UNKNOWN` with the source check BLOCKED and no `DONE` (plan.md:1387).
- E2E is declared not required with a credible rationale (plan.md:9); Stage 05 remains the independent acceptance mode per `INDEPENDENT_ACCEPTANCE_REQUIRED: YES` (plan.md:7).
- The 禎/楨 separation, oracle-before-output discipline, append-only evidence rules, and read-only fences are unchanged and consistent; no new complexity or scope was introduced by Rev17.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revision mode on the same TASK_ID (`T20260916-0102-01-line-backup-acceptance`): produce the next revision fixing RV-23-1 (MAJOR) plus RV-23-2…RV-23-5 (MINOR) in place, then obtain a fresh independent Stage 02 review bound to the new plan SHA-256; Stage 03 must not compile a handoff for this revision/hash.
