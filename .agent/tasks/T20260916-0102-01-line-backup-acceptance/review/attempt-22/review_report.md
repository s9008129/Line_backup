# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: review/attempt-22
- REVIEWED_PLAN_REVISION: 17
- REVIEWED_PLAN_SHA256: 5dd7ab19ce16175fb8e091762d73a50cebb6415ab895342c00a9a015ea1b866f
- PLAN_SNAPSHOT_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-22/plan_snapshot.md (re-hashed: equal to the reviewed SHA; 1391 lines)
- Repository anchor observed: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup (read-only this review; `src/line_backup_acceptance/verifier.py` exists and no `verify.py`; `transaction.py:92` dispatches via child `subprocess.run`; `tests/automation_verification/` exists with `run_all.py` absent, consistent with §16.9)
- Reviewer runtime/model: Codex Stage 02 fresh-context reviewer session (informational only)
- Boundaries observed: read-only; no product CLI/driver/test/driver/pytest executed; no downloads; no GUI/AX; no writes outside `review/attempt-22/`; attempts 01–21 and 23 untouched
- PRIOR_REVIEW_CONTEXT: attempt-20 (RV-1…RV-11) and attempt-21 (RV-1 BLOCKER + RV-2…RV-6) both returned PLAN_REVISION_REQUIRED for Rev16 at SHA256 61e16764…; planner-notes-rev16-self-audit.md G1/G2 name the same defects as attempt-20 RV-11/RV-7. Rev17 at the hash above claims every item fixed in place (plan.md:22–23: "each one names the paragraphs it corrects **in place** — no new supersession layer and no surviving contradicting literal").

## OWNER_VERDICT
- Goal (plain language): produce two things together — (1) a trustworthy answer for the 57 photos of 「旻謙允禎成長日記」 (2024/05/13～05/17): are they a valid backup of the exact requested LINE source, or is that unknown; and (2) a proven, rerunnable automation path (R1–R7 repaired through the real operator entry) whose evidence can be read back independently. Neither offline/fixture PASS may stand in for the GUI path, and nothing may re-download, rewrite the formal state, or touch the 57 photos.
- Essential (CORE): single-valued executable command grammar; at-most-once dispatch with crash recovery and duplicate safety (R1–R5); exact source-identity separation (禎 U+798E vs 楨 U+6968, never merged); read-only formal state/photos; a decidable verification-evidence chain; the v4.2 status/closure contract including baseline-delta regression routing; one bounded GUI ellipsis-observation gate; independent acceptance.
- Best-effort / deferred: bridge/service diagnosis (explicitly non-gating), production Save-All/download, migration, OCR, historical cleanup (plan.md:961–967, 1062).
- What may globally block and why: source correspondence is the album-result acceptance criterion itself (plan.md:1057–1058 — it "blocks exact goal acceptance and production route" but plan.md:880 confines it to the album-attribution result, never the capability result); mutation of a non-strict legacy state is refused to protect the formal state (plan.md:356–360); `baseline_delta=WORSENED` is a must-not-break violation routed to FAIL/FIX_REQUIRED per workflow-routing §7.7 rule 8 (plan.md:131–135).
- Complexity verdict: Rev17 is net-simplifying. It deletes the `prepare`-may-append exception and the v1 self-referential chain, and it grounds Case 20 on the real child-process dispatcher. No new gate, component, or cross-layer coupling was introduced for the correction set.
- Biggest remaining risk: unchanged from the goal — the 57 files can be valid on disk while the original source namespace/provenance was never captured, so the album-data result may legitimately end UNRESOLVED / LEGACY_PROVENANCE_LIMITED unless an authoritative exact join or one precise preserved user fact resolves it. The plan keeps that outcome honest instead of papering over it.
- Verdict: approval is warranted for revision 17 at the reviewed hash. Three MINOR bookkeeping residuals survive (RV-1…RV-3 below); none can invalidate goal alignment, implementation, safety, compatibility, rollback, or acceptance, and none requires a further plan revision cycle.

## GOAL_BASELINE
Reconstructed from the authoritative request (`pasted-text-1.txt`, read before re-reading the Plan's own framing):
- Primary outcome = BOTH results required: (1) album-data result for exactly one album — LINE `jp.naver.line.mac`, group 「旻謙允禎成長日記」, album 2024/05/13～05/17, 57 expected images — established by an authoritative exact source join or one precise preserved user fact (original question, original answer, provider, time, evidence SHA-256); verify-only against the existing 57 files; never re-download. (2) proven reusable automation capability — R1–R7 reproduced and fixed through the real entry, rerunnable, independently re-readable evidence; offline/fixture PASS never masquerades as GUI end-to-end success. Three results reported separately (album data / reusable capability / task closure); completeness requires 1 and 2.
- Two blockers, only two legal solutions: source identity (never merge/normalize the two characters or infer sameness from date/count/hash) and one GUI observation gate (exactly one current-target ellipsis observation, after all non-GUI prerequisites; no menu item, Save-All, chooser, shortcuts, state writes, or downloads).
- CORE: literal executable argv; at-most-once dispatch; crash recovery; duplicate safety; source-identity separation; read-only formal config/state/run-log/57 photos; no re-download; independent acceptance; status/closure contract; baseline delta; append-only evidence.
- SUPPORTING: bridge/service (NON_GATING). BEST_EFFORT/deferred: historical cleanup, migration, OCR, production Save-All.
- Legal global blockers: source correspondence (it is the outcome), formal-state mutation protection, must-not-break baseline regression, and non-self-waivable status semantics — each with a safety/correctness rationale, not schema completeness.
- Biggest remaining risk: valid 57 files with no captured source provenance ⇒ album result may end UNKNOWN/UNRESOLVED; capability result can still pass.

## GOAL_ALIGNMENT
- plan.md:936 (PRIMARY_OUTCOME, unchanged by Rev17 per §17.10) matches the goal's two-part outcome verbatim in substance: "(1) safely establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group '旻謙允禎成長日記' … and otherwise stop without any ambiguous or duplicate production transaction; and (2) leave the reusable automation path itself proven through the real entry … Neither result may be claimed from offline or fixture PASS, and paperwork is not a substitute for either."
- Three-result separation and honest failure: plan.md:880 — legacy provenance "blocks only the album-attribution result, never the capability result"; plan.md:1391 (owner view) — "Filesystem health alone is insufficient", largest risk = valid files without source provenance.
- Rev17 introduced no goal drift: the correction blocks change literals, grammar and contracts only; §17.10 (plan.md:172–175) explicitly leaves the goal contract, R1–R7 fix contract, case semantics, human gate, read-only fences and three-result reporting unchanged.
- The two legal blocker solutions are preserved as the only ones: source resolution is restricted to an authoritative exact join or the §16.4 v1 user-fact record (plan.md:108–112, 586–592); the GUI gate remains the single bounded ellipsis observation (plan.md:1258–1271).

## NECESSITY_AND_TRACEABILITY
- R1–R7 → Cases 01–25 + verifier/authority/status fixtures; every row in the acceptance set is a negative control, an oracle for a reproduced gap, or a v4.2 routing fixture (plan.md:723–734 R-table; 1208–1210; 1316–1348).
- Case 20's new orphan mechanics serve R1 (crash in the dispatch window) and are grounded on the real code path (transaction.py:92 child `subprocess.run`), not invented behavior.
- Chain v2 fields each serve the evidence rule (rerunnable, independently readable, tamper-evident): `manifest_path`/`manifest_bytes` back-link, `result_summary`/`result_bytes`/`result_sha256` forward-link, artifacts[] per-file hashes, 22e/22f enforceable negatives (plan.md:59–79, 271–284).
- The legacy read contract serves the read-only formal-state fence while keeping the real state readable (plan.md:338–357).
- The 19th status row serves v4.2 §7.7 rule 8 (baseline-delta hard failure) and the plan's own hard-failure rule (plan.md:1313).
- Bridge/service remains explicitly SUPPORTING/NON_GATING (plan.md:961, 1062, 1310); deferred list matches the goal's prohibitions (plan.md:965–967).
- No untraceable new scope found in Rev17.

## GATE_AND_VETO_AUDIT
- Source correspondence gate: blocks only the album-attribution result and the production route (plan.md:880, 1057–1058) — it IS the user's acceptance criterion, so the veto is semantics, not completeness. Correctly does not block the capability result.
- Formal-state mutation gate: any non-strict state is refused `INVALID_STATE_LEGACY` exit 4 with no write (plan.md:356–360, 369); this protects the real data and is proportional because verification needs only reads.
- Baseline gate: WORSENED ⇒ `REQUIRED_VERIFICATION=FAIL`, `CLOSURE=FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` (plan.md:131–135) — verified against workflow-routing.md §7.7 rule 8 (policy table row 8: "required verification conclusively shows task regression/must-not-break violation → REQUIRED_VERIFICATION_STATUS: FAIL; TASK_CLOSURE_STATUS: FIX_REQUIRED"). Never conflated with the pre-existing-debt INCOMPLETE route (plan.md:1313).
- Status/closure contract: every material check carries CHECK_ID/GOAL_CRITICALITY/…/WAIVER_AUTHORITY, and "no agent can approve its own waiver" (plan.md:1291–1292); core source/data-integrity failures and fabricated provenance are non-waivable (plan.md:1373).
- No supporting/best-effort item holds a global veto: bridge readiness is NON_GATING (plan.md:1310), GUI observation is a bounded separate gate, and route evidence absence degrades to UNKNOWN/SAFE_ABORT rather than blocking offline CORE work.

## COUPLING_AND_FAILURE_CONTAINMENT
- Independent verifier axes are preserved: Filesystem PASS is kept even when Registry FAIL / Source UNRESOLVED / State LEGACY_PROVENANCE_LIMITED (plan.md:354–356), so one provenance problem does not collapse all signals into a single flag.
- Legacy failures are contained: they limit the album result and the state axis, never the capability result (plan.md:880); read-only operations report per-run `legacy_normalizations[]` and never rewrite (plan.md:346–353).
- Dispatch failures are contained per run: case roots are isolated, each case computes its oracle before product output (plan.md:1249–1250), and a Case 20 forced kill is a fixture failure/TASK_REGRESSION, never an accepted path (plan.md:238–239).
- Chain-v2 failure containment: any missing/mismatching element is `INVALID_VERIFICATION_EVIDENCE` or `VERIFICATION_RUN_MISMATCH`, exit 4, "no revision change, no registry entry, no lock leak" (plan.md:70–73); no partial finalize is possible.
- The honest-scope narrowing (plan.md:73–77) correctly refuses to over-claim: the chain proves internal consistency/completeness/post-hoc integrity, not authorship — failure is contained to what it can actually enforce, and rows 22e/22f make that enforceable part executable.

## DESIGN_ECONOMY
- Rev17 removes two defects by deletion, not by layer: the `prepare`-may-append exception is deleted (plan.md:93–96, 356–360) and the v1 self-hash chain is replaced by a one-direction back-link (plan.md:59–79). Net moving parts decrease.
- Case 20 reuses the case-02 equivalence instead of inventing a new state shape (plan.md:249–251).
- The 19th status row reuses the existing fixture pattern; its content is fully literal (plan.md:130–136, 1348).
- No new dependency, service, schema, or cross-layer coordination point was added by the correction set; §17.10 confirms the unchanged contract surface.
- The one avoidable residue is textual (RV-2/RV-3 below), not structural.

## CRITICAL_PATH_AND_PRIORITY
- Sequence fixes and proves the CORE path first: Phase 0 read-only baseline → Phase 1 archive → Phase 2 reproduce R1–R7 through the real entry → minimal repair → regression → product verify against the real destination (`evidence/20260916-product-verify/attempt-04`, plan.md:450/1008) → source-identity resolution → the single GUI gate last (plan.md:1044–1050).
- The album-result CORE work (verify-only over the real 57 files) is offline and does not wait on the GUI budget; the GUI gate is explicitly requested only after all non-GUI prerequisites (plan.md:1264–1267).
- Supporting work (bridge) consumes no critical-path capacity (plan.md:961).
- No priority inversion found: the plan never lets fixture/paperwork completion substitute for the real-entry run or the album result (plan.md:936).

## REQUIREMENT_FIDELITY
- Out-of-scope list matches the goal's hard prohibitions: "No automatic spelling merge, legacy migration, production download, bridge reinstall, TCC change, or broad historical cleanup" and "No distributed exactly-once protocol, new persistence schema, or unrelated bridge/controller refactor" (plan.md:965–967).
- No re-download path exists: verify-only is read-only; the formal state cannot be mutated by this wave; 57 photos untouched; `/private/tmp` is fixture-only.
- Authority-first rule is unchanged and single-valued (plan.md:1020): `INVALID_AUTHORITY`, exit 2, before any read/write; test-mode limited to the literal allowlisted roots `-01`…`-25`.
- Escalation conditions from the goal (same root cause twice, contradictory provenance, etc.) remain covered by the CRITICAL workflow and the plan's revision-increment rule (plan.md:1381–1383).

## GROUNDING_AND_DRIFT
- Module/grounding anchors re-verified read-only: `verifier.py` exists (no `verify.py`) — plan.md:993; dispatcher is a child process — `transaction.py:92`; `tests/automation_verification/` exists and `run_all.py` is new — plan.md:996.
- Schema claims used by §16.4/§16.5 are consistent with the skill schema at `~/.codex/skills/line-album-backup/schemas/schemas.json` (`verified_run_id` nullable; `source_kind` enum).
- Evidence roots are now single-valued and non-overlapping: product-verify `attempt-04` (plan.md:148, 1008), baseline `attempt-02` (plan.md:149, 1319), Phase-0 archive `attempt-01` (plan.md:722), and the two-order wave pinned to disjoint `attempt-02/order-ownership-first/` and `attempt-02/order-driver-first/` with per-driver readback files (plan.md:695–698).
- The planned-file heading now reads "Planned implementation files (existing modules are modified in place; `run_all.py` is new)" (plan.md:988).
- Drift residue found: stale revision literals at plan.md:1377/1379 (RV-1 below) and the un-annotated production grammar at plan.md:1016 (RV-2 below).

## ARCHITECTURE_AND_CONTRACTS
- Verification-evidence chain v2 is acyclic and decidable: result.json carries only `verification_evidence{manifest_path, manifest_bytes}` and never a hash of itself; manifest.json is written last and carries artifacts[] including result.json, plus `result_summary`, `result_bytes`, `result_sha256` (plan.md:59–68); commit/finalize recompute order is pinned before any other gate (plan.md:70–73); `--run-id` null ⇒ not consumable (plan.md:78–79).
- Legacy contract is single-valued: the prepare-may-append exception is deleted (plan.md:93–96); one read-only mapping everywhere — Filesystem PASS preserved / Registry FAIL / Source UNRESOLVED / State `LEGACY_PROVENANCE_LIMITED` / overall `UNKNOWN` / exit 4 / `failure_class=INPUT_PROVENANCE_LIMITED` (plan.md:97–99, 354–356, 364–369); `legacy_normalizations[]` pinned to `{run_id, kind, detail}` with four kinds (plan.md:102–104, 346–353); the authority §838 scope sentence is amended in place so reading an existing authority state is never gated (plan.md:90–91, 1024).
- Registry-axis coherence verified: per-run legacy/unreadable state ⇒ Registry FAIL, while the `legacy-record` association fixture with a null `verified_run_id` is the contract's imported-evidence form ⇒ Registry PASS / Source UNRESOLVED (plan.md:663, 1158). These are distinct axes, not a contradiction.
- Case 20 mechanics verified: child-process dispatcher (plan.md:224–232; transaction.py:92), adapter polls `os.getppid()` every 0.25 s and self-exits ≤10 s after reparenting (plan.md:115–118, 227–230), driver records reparenting and waits bounded, remainder claim scoped to `CASE_ROOT_20/state/` with the empty lock file only (plan.md:121–124, 234–238), forced kill after 15 s = `orphan-forced-kill` fixture failure/TASK_REGRESSION (plan.md:125–127, 235–237).
- Test-mode grammar is single-valued: canonical children + `--project-root CASE_ROOT_NN` + `--test-mode`, NN = 01…25 (plan.md:36–37, 204–205, 476–478, 1017, 1194); `--state CASE_ROOT_NN/state.json` appears only in the four places that declare it illegal or describe the historical mistake (plan.md:44, 205, 220, 1194); authority negatives carry present-but-mismatched canonical children (plan.md:1164 rows 1–5) and the missing-`--project-root` parser row is explicitly separate (plan.md:1164, sixth row; plan.md:50).

## DATA_SECURITY_RELIABILITY
- Read-only fences preserved: formal config/state/run-log and the 57 photos are read-only; the real formal state cannot be mutated (plan.md:356–360); no re-download; append-only attempts (plan.md:454).
- At-most-once dispatch and duplicate safety: R1–R3 case set with counter oracles; case 20's kill-aftermath asserts exactly one counter line and byte-identical revision-1 state with no revision-2 record and `save_all_retry_allowed=false` (plan.md:120–123, 233–236).
- Recovery: one fresh `resume --no-dispatch` reconciles the barrier (plan.md:241–246); a second resume is idempotent; commit is refused until resolution (plan.md:246–247).
- Evidence integrity: per-artifact length/SHA-256, independent oracles computed before product output, product PASS lines never accepted as oracles (plan.md:1249–1250, 1254); driver-captured stdout/stderr/exit excluded from the chain and hashed separately (plan.md:79–81).
- Authority safety: every transaction and verify-only execution requires one immutable `--project-root` and canonical children, validated before any state/config/lock/control path (plan.md:1020); missing required production options normalize to `INVALID_AUTHORITY` (plan.md:1164).
- GUI safety: exactly one ellipsis input post-gate; zero navigation/acquisition inputs; no menu/Save-All/chooser/state writes; UNKNOWN/SAFE_ABORT on ambiguity (plan.md:1264–1271).

## IMPLEMENTATION_SEQUENCE
- The acceptance manifest is single-valued: case roots `-01`…`-25` (plan.md:37, 419); the 19-row status manifest (plan.md:1348); rows 22a–22f (plan.md:271–284); 25a/25b (plan.md:364–369); counters and routing pinned for 20–25 (plan.md:138–144, 1243, 1247).
- The two-order Phase-2 wave cannot self-overwrite: disjoint durable roots plus per-order readback-verification.json (plan.md:695–698); a protocol violation is TASK_REGRESSION.
- Handoff binding rule: Stage 03 compiles the handoff for the approved `PLAN_REVISION` and its exact hash; Stage 04 stops on mismatch (plan.md:702–703).
- Residual sequencing text defect: the closure paragraph still hardcodes `PLAN_REVISION=16` (RV-1 below); per plan.md:702–703 and the Stage 03 gate this is mechanically resolvable and cannot mis-bind a handoff that still passes verification.

## TESTABILITY_AND_ACCEPTANCE
- Every claimed behavior has an executable oracle or a literal negative: 40-row verifier matrix, authority negatives, 25-case transaction matrix, 19-row status manifest, two-order Phase-2, baseline pre/post comparison, and the single GUI route experiment (plan.md:1208–1213, 1316–1348, 722–726, 1258–1271).
- v4.2 coverage required by the gate: canonical incident, implementation blocker, CORE fail/blocked/not-run/not-required (±rationale), replan, baseline unavailable, baseline-delta (now with the 19th row), hard-clean debt, formal waiver preserving the original FAIL, independent-acceptance pending/environment-block/product-defect, contradictory-state rejection, legacy normalization, DONE prerequisites — all present (plan.md:1316–1348 table; §17.6; §16.7).
- Baseline-delta routing is now correct and testable: `baseline-worsened` expects PRIMARY ACHIEVED / IMPLEMENTATION COMPLETE / CORE PASS / REQUIRED_VERIFICATION FAIL / INDEPENDENT PENDING / CLOSURE FIX_REQUIRED / blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` (plan.md:132–135, 1348).
- Chain negatives 22a–22f make the enforceable part executable, including a self-consistent forged chain (22e) and a post-manifest byte flip (22f) (plan.md:274–284).
- Acceptance remains independent: Stage 05 reads only product/Stage-04 artifacts, cannot modify product code, and offline/fixture success cannot masquerade as GUI E2E (plan.md:936, 1348's `evidence_basis == "scenario_table_non_acceptance"` rule).
- Residual test-text defect: the status fixture table still enumerates 18 rows while the manifest enumerates 19 (RV-3 below) — the 19th row's content is nonetheless fully literal in §17.6 + plan.md:1348, so no invention is required.

## REV17_CHECKLIST_VERIFICATION (a–h)
(a) In-place correction claim: all §17.1–§17.10 blocks exist at plan.md:21–175 and all named paragraphs were diffed against the Rev16 snapshot; the corrections are present at every previously-cited location (e.g., 476–481, 534–535, 587–592, 690–698, 988, 1008–1024, 1164, 1194–1204, 1227–1247, 1319, 1348). One surviving contradicting literal set remains at plan.md:1377/1379 (`PLAN_REVISION=16`, "this Revision 16") → RV-1.
(b) Test-mode grammar: CANONICAL and executable in every literal — plan.md:36–37 "`--project-root CASE_ROOT_NN --config CASE_ROOT_NN/config/line_backup_config.json --run-log CASE_ROOT_NN/state/run_log.md --state CASE_ROOT_NN/state/backup_state.json --test-mode` … `NN` = 01…25"; the illegal string occurs only in its four declaring sentences (plan.md:44, 205, 220, 1194); authority negatives carry present-but-mismatched canonical children (plan.md:1164 rows 1–5) with the missing-`--project-root` parser row explicitly separate (plan.md:1164 sixth row, plan.md:50) → PASS.
(c) Verification-evidence chain v2: acyclic — result.json carries `verification_evidence{manifest_path, manifest_bytes}` "— never a hash of itself —" (plan.md:65–66); manifest written last with the result.json entry plus `result_summary`/`result_bytes`/`result_sha256` (plan.md:67–68); commit/finalize recompute order pinned (plan.md:70–73); `--run-id` null ⇒ not consumable (plan.md:78–79); rows 22a–22f (plan.md:271–284) → PASS.
(d) Legacy contract single-valued: prepare-may-append exception deleted (plan.md:93–96, 356–360); one read-only mapping across §17.3/§16.5/25a and the verifier-contract/matrix text (plan.md:97–99, 354–356, 364–369, 663, 1158); `legacy_normalizations[]` = `{run_id, kind, detail}` with four kinds (plan.md:102–104) → PASS.
(e) Case 20 orphan mechanics: child dispatcher (plan.md:224–232; transaction.py:92); `os.getppid()` poll every 0.25 s, self-exit ≤10 s (plan.md:115–118); driver records reparenting; state-dir remainder scope (plan.md:121–124); forced kill after 15 s = TASK_REGRESSION (plan.md:125–127) → PASS.
(f) Status 19th row: expected tuple and blocker per workflow-routing §7.7 rule 8 (plan.md:132–135; policy verified); 19-row manifest enumeration lists `baseline-worsened` directly after `baseline-unchanged` (plan.md:1348); §16.7 adds the row (plan.md:415–417). Residual: the fixture table still has 18 rows → RV-3.
(g) Routing/counters for 20–25: 20/23 stop recovery/duplicate-safety acceptance, 21/22/24/25 are regressions (plan.md:138–140, 1243); counters 20 = one before kill + one after recovery, 21 = 0, 22 = setup's single line untouched by all six refusals, 23a/b = 0, 23c = 1, 24 = 0, 25a/b = 0 (plan.md:140–144, 1247) → PASS.
(h) Evidence roots/ranges/headings: product-verify `attempt-04`, baseline `attempt-02`, `attempt-01` read-only (plan.md:148–149, 450–452, 1008, 1319); ranges read `-01`…`-25` (plan.md:149, 419, 476); two-order Phase-2 dirs `attempt-02/order-ownership-first/` and `attempt-02/order-driver-first/` each with their own readback-verification.json (plan.md:150–153, 695–698); planned-file heading (plan.md:988) → PASS.

## ITEM-BY-ITEM RV/G DISPOSITION (ATTEMPT-20, ATTEMPT-21, G1/G2)
| Item | Prior severity/gist | Disposition in Rev17 | Evidence |
|---|---|---|---|
| 20-RV-1 | MAJOR — flagship argv non-executable (state.json) | FIXED | plan.md:36–37, 204–205, 476–478, 1017, 1194; illegal string only declared illegal |
| 20-RV-2 | MAJOR — legacy validation stated two contradictory ways | FIXED | plan.md:89–104, 338–360, 369; exception deleted; 25b oracle |
| 20-RV-3 | MAJOR — chain v1 not implementable (self-hash recursion) | FIXED | plan.md:59–79; 22e/22f at 271–284 |
| 20-RV-4 | MAJOR — 24a CONFIRMED oracle vs §15.2 anchors | FIXED | plan.md:105–112, 586–592; 24a–24c at 332–334 |
| 20-RV-5 | MAJOR — Case 20 false mechanism / over-broad remainder | FIXED | plan.md:115–127, 224–250; transaction.py:92 grounding |
| 20-RV-6 | MINOR — case-07 replacement count | FIXED | plan.md:1237 "exactly two guarded replacements by the winner and zero by the loser … exactly one counter line overall" |
| 20-RV-7 | MINOR — status manifest count/ID list | FIXED (count/list); table-row residual → RV-3 | plan.md:1348 enumerates 19 rows incl. `baseline-worsened` |
| 20-RV-8 | MINOR — finalize grammar unconditional at Rev16:830 & Rev16:1010 | PARTIALLY FIXED — Rev16:1010 target fixed (plan.md:1196 annotated); Rev16:830 target (plan.md:1016) still bare → RV-2 | plan.md:411–413, 1196 vs 1016; §17.9 claim at 159–161 |
| 20-RV-9 | MINOR — §16.6 oracle-assertion claim not present in oracles | FIXED (case-02 explicit; case-03 changed-artifact assertion; case-19 via the normative §17.9 statement) | plan.md:162–166, 1232–1233, 377 |
| 20-RV-10 | MINOR — stale roots/paths/attempt-01/heading | FIXED | plan.md:148–153, 419–420, 450–452, 476, 988, 1008, 1319 |
| 20-RV-11 | MINOR — routing for case failures 20–25 | FIXED | plan.md:138–140, 1243 |
| 21-RV-1 | BLOCKER — chain self-reference/mutual recursion | FIXED | plan.md:59–79 (one-direction write order; no self-hash; 22e self-consistent forgery still caught by result_summary disagreement) |
| 21-RV-2 | MAJOR — argv grammar not single-valued | FIXED | plan.md:36–37, 44, 204–205, 476–478, 1017, 1194, 1200–1203 |
| 21-RV-3 | MAJOR — evidence roots overwrite risk | FIXED | plan.md:148–149, 695–698, 1008, 1319 |
| 21-RV-4 | MAJOR — 19th row routing INCOMPLETE vs FAIL; table | FIXED for routing/literals/count; table-row residual → RV-3 | plan.md:128–136, 415–417, 1348 |
| 21-RV-5 | MAJOR — legacy overall NOT_ACHIEVED vs UNKNOWN | FIXED | plan.md:97–99, 354–357, 364–369 |
| 21-RV-6 | MAJOR — mutation of legacy state ambiguous | FIXED | plan.md:356–360, 369, 1024 |
| G1 | planner self-audit — routing/counters 20–25 | FIXED | plan.md:138–144, 1243, 1247 |
| G2 | planner self-audit — 19-row manifest count | FIXED (count/list); table-row residual → RV-3 | plan.md:1348 |

## FINDINGS
### RV-1 — MINOR — GROUNDING / HANDOFF (stale revision literals survive the "no surviving contradicting literal" claim)
- Affected: plan.md:1375–1379 "## Closure and sequencing".
- Evidence: plan.md:1377 "Stage 03 must create a fresh handoff bound to TASK_ID, PLAN_REVISION=16, the approved plan SHA …"; plan.md:1379 "Stage 02 must independently review this Revision 16 and its exact hash." The document's own META reads `PLAN_REVISION: 17` (plan.md:4) and Rev17 declares all earlier approvals invalid (plan.md:30).
- Mechanism: a Stage 03 compiler reading only this paragraph could bind the handoff to revision 16; that handoff would then fail Stage 03's own "verify the current PLAN_REVISION/hash against the latest applicable approval" gate and Stage 04's handoff↔plan consistency stop (plan.md:702–703), producing a wasted cycle rather than a wrong product artifact.
- Why MINOR: resolution is unambiguous and mechanical (§15.6's "current revision at handoff time" rule, plan.md:702–703); the failure is loud and cannot invalidate implementation, safety, or acceptance.
- Smallest correction: replace `PLAN_REVISION=16` with `PLAN_REVISION=17` (or "the current revision at handoff time") and "this Revision 16" with "this Revision 17" at plan.md:1377/1379 in the next plan edit.

### RV-2 — MINOR — COMPATIBILITY (attempt-20 RV-8 half-fix: production finalize grammar still presents `--verification-json` unconditionally)
- Affected: plan.md:1016 ("Production transaction forms (no `--test-mode`)") vs plan.md:411–413 and plan.md:1196.
- Evidence: plan.md:1016 lists "`transaction finalize … --outcome VERIFIED|SAFE_ABORT --verification-json PATH --evidence-dir PATH`" with no outcome-conditional annotation; plan.md:1196 states "`--verification-json` is required for `--outcome VERIFIED` and optional for `SAFE_ABORT`"; §17.9 claims the rule is annotated "in both grammar statements" (plan.md:159–161). Attempt-20 RV-8 named Rev16 plan.md:830 (now 1016) and Rev16 plan.md:1010 (now 1196); only the latter and §16.7 were annotated.
- Mechanism: an implementer reading the production grammar alone could make `--verification-json` required for `SAFE_ABORT` production finalize, conflicting with the case-19/10B protocol; such a divergence is detectable by the acceptance rows (case 19 finalize SAFE_ABORT without the option) but would cost a repair cycle.
- Why MINOR: the operative rule is stated twice in normative text (plan.md:411–413, 1196) and repeated in §17.9; the option is present in the grammar (not omitted); no acceptance row silently absorbs the contradiction.
- Smallest correction: append the outcome-conditional annotation to plan.md:1016 (one clause), or state there that finalize option requiredness is governed by plan.md:411–413/1196.

### RV-3 — MINOR — TEST (attempt-21 RV-4 half-fix: the status fixture table still enumerates 18 rows)
- Affected: the "Required cases:" table (plan.md:1318–1340) vs plan.md:1348 and §17.6.
- Evidence: the table lists 18 fixture rows and has no `baseline-worsened` row; plan.md:1348 "The literal manifest enumerates the 19 rows by ID … `baseline-unchanged`, `baseline-worsened`, …" and gives the 19th row's literal input/output paths and expected tuple; §17.6 (plan.md:128–136) and §16.7 (plan.md:415–417) add the row normatively. Attempt-21 RV-4's smallest correction was "add `baseline-worsened` to the fixture table and to the manifest ID count (19)"; the ID count and routing were fixed, the table row was not.
- Mechanism: an implementer building the driver manifest from the table alone could ship 18 rows and fail plan.md:1348's 19-row requirement; the reverse reading (19 rows) requires reading §17.6/1348, which are normative and complete.
- Why MINOR: the 19th row's full content (literal paths, expected tuple, blocker, routing) is already fully specified with no invention required; the manifest enumeration — the artifact the driver actually consumes — is correct.
- Smallest correction: insert the `baseline-worsened` row into the table (its content is already written in plan.md:128–136/1348), or add a one-line pointer under the table that the 19th row is specified there.

## REQUIRED_PLAN_CHANGES
None. No unresolved BLOCKER/MAJOR remains: every attempt-20 RV-1…RV-11, attempt-21 RV-1…RV-6 and planner G1/G2 defect is corrected in substance for goal alignment, implementation, safety, compatibility, and acceptance. The three residuals above (RV-1…RV-3) are non-gating MINOR text/bookkeeping items that may be folded into the next plan edit or handled mechanically without a new review cycle (they do not change any semantic contract).

## RESIDUAL_MINOR_NOTES
- RV-1: stale `PLAN_REVISION=16` / "this Revision 16" at plan.md:1377/1379 — fix in the next edit; Stage 03 must bind the handoff to revision 17 at SHA 5dd7ab19… per plan.md:702–703.
- RV-2: un-annotated production finalize grammar at plan.md:1016 — one-clause fix; governing rule is plan.md:411–413 + 1196 + §17.9.
- RV-3: status fixture table 18 rows vs 19-row manifest at plan.md:1318–1340 vs 1348 — the row's content already exists in §17.6/1348.
- Observation (no separate ID): §17.9/§16.6's statement that the case-02/03/19 oracles assert the persisted `reconcile:<relpath>:<sha256>` form is explicitly realized for case-02 (plan.md:1232) and case-03 (no-new-artifact assertion, plan.md:1233); case-19's row text does not repeat it, so Stage 04 should implement the assertion from §17.9 (plan.md:162–166) and §16.6 (plan.md:375–377). No acceptance impact.
- Note on prior approvals: Rev13–Rev16 approvals remain invalid for Rev17 (plan.md:30); this review binds approval only to revision 17 at SHA 5dd7ab19ce16175fb8e091762d73a50cebb6415ab895342c00a9a015ea1b866f.

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Stage 03 Handoff compiler on the same TASK_ID: compile `handoff.md` for PLAN_REVISION 17 at SHA-256 5dd7ab19ce16175fb8e091762d73a50cebb6415ab895342c00a9a015ea1b866f (snapshot: review/attempt-22/plan_snapshot.md), preserving GOAL_ANCHOR, the two-part PRIMARY_OUTCOME, critical path, semantic invariants, non-gating/deferred items, and stop conditions; do not re-plan, and treat plan.md:1377/1379's "16" as stale.
