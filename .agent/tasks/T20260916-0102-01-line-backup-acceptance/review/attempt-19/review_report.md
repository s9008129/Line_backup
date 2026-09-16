# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 19 (second, independent reviewer; did not read review/attempt-18)
- REVIEWED_PLAN_REVISION: 15 (PLAN_STATUS: CANDIDATE)
- REVIEWED_PLAN_SHA256: e22373ee04894d2625c9f8c240276b099a66ca52f7b4d6127b4028f4eb0741e4
- PLAN_BYTES: 154021; PLAN_LINES: 946 (preflight hash re-verified before and after snapshot; snapshot is byte-identical)
- PLAN_SNAPSHOT_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-19/plan-snapshot.md
- Repository anchor observed: workspace /Users/hsiaojohnny/Documents/ChatGPT/Line_backup; `git status` shows `plan.md` modified and `review/attempt-17|18|19/`, `evidence/20260916-auto-verification/`, `tests/automation_verification/` untracked, single commit `d51fd4b` (H2.1 handoff pack). `src/line_backup_acceptance/*.py` SHA-256 re-verified equal to handoff §4 (transaction.py c486edbe…, verifier.py b38ee6d5…, status.py 20a95f7c…, authority.py a98964e3…, cli.py a5bbbbf6…, common.py 59a85c47…). Schema re-read from `~/.codex/skills/line-album-backup/schemas/schemas.json`. Evidence read-back `evidence/20260916-auto-verification/attempt-01/readback-verification.json` = artifacts_checked 4859 / manifests 84 / 0 problems / verdict PASS.
- Reviewer runtime/model: Codex CLI (harness role prompt `~/.codex/prompts/02_plan_review_prompt.md`); write scope restricted to `review/attempt-19/`

## OWNER_VERDICT

Goal: the user wants a LINE album backup flow that one day runs fully automatically without human intervention; **this wave's job is to make the automation verification real** — reproduce handoff §7 R1–R7 through the true entry (`python3 -m line_backup_acceptance`), fix them, and leave rerunnable, independently re-readable evidence — explicitly *not* to add more PASS numbers or documents. Alongside that, the wave must honestly answer whether the existing 57 files are a backup of exactly the requested source group.

Essentials (CORE): formal config/state/run-log and the 57 photos stay read-only; the 禎 (U+798E) / 楨 (U+6968) strings are never merged or inferred from dates/counts/hashes; one uninterrupted dispatch window with at-most-once Save All; duplicate/refusal gating and finalize trust at the real entry; the three results (album data / reusable automation capability / overall closure) reported separately; offline or fixture PASS never reported as GUI end-to-end success.

Optional / deferred: production Save-All and download, bridge repair, migration, OCR, historical cleanup, and the single current-target ellipsis GUI observation (only after it is proven necessary; historic ellipsis credit is exhausted).

Global blockers found: none new. Two **MAJOR contract-text defects** would force Stage 04 to guess a semantic decision: (1) the persisted reconciliation reference grammar has two incompatible definitions in the same revision (§15.1 vs §15.2); (2) the only reachable user-fact path to source CONFIRMED names keys that do not exist in the preserved user-fact artifact and pins no record schema, so the DONE path for source confirmation is not implementable or testable as written. Both are fixable as text changes in one Stage 01 revision.

Complexity verdict: the plan is heavy, but the weight now sits on executable checks (19 transaction cases, 12 verifier negative rows, 11 authority rows, 18 status-routing fixtures, read-back verifier) rather than prose. I recommend two mandatory text fixes plus small coverage notes — **not** new scope, and no deletion that would weaken a goal.

Biggest remaining risk: even a perfect automation wave may leave the album-data result UNKNOWN — the preserved user fact has part 2 UNANSWERED and no authoritative machine join exists, and the plan's contract defect (RV-2) currently leaves no defined artifact that could ever turn that answer into CONFIRMED.

## GOAL_BASELINE

Authored before reading the plan's framing, from the authoritative goal source
(`~/.codex/attachments/210176d8-…/pasted-text-1.txt`, i.e. the `/goal` instruction) and `handoff.md` H2.1 §0–§14:

1. **Wave purpose (verbatim intent):** make "自動化驗證" real — reproduce and fix handoff §7 R1–R7 through the true entry, and produce rerunnable, independently verifiable tests and evidence; "而不是增加 PASS 數字或文件" (not more PASS numbers or documents).
2. **Final user goal:** fully automatic backup with no human intervention. This wave proves the process; a production Save-All/download is not part of it.
3. **Scope:** one album only — LINE app `jp.naver.line.mac`, group 「旻謙允禎成長日記」, album 2024/05/13～05/17, 57 expected images. If the existing 57 files are valid → verify-only; **never redownload for testing**.
4. **Read-only fence:** formal config, state, run-log and the 57 photos are read-only unless the user grants a separate exact gate.
5. **Three separately reported results:** (1) album-data result, (2) reusable automation capability, (3) overall closure. Complete requires 1 **and** 2; offline/fixture PASS must never masquerade as GUI E2E success.
6. **Blocker 1 — source identity:** the user asked for 「禎」; formal config/state persist 「楨」. Merging, normalizing, rewriting the canonical key, or inferring sameness from equal date/count/hash is forbidden. Legal resolutions: an authoritative exact source join, or one precise preserved user fact with original question, original answer, supplier and time, and evidence SHA-256.
7. **Blocker 2 — the single GUI observation gate:** complete all non-GUI work first, then at most one current-target ellipsis observation with immediate post evidence, then stop; it authorizes no menu item, Save All, chooser, keyboard shortcut, state write or download. Historical ellipsis credit is spent.
8. **Hard prohibitions:** nothing that can trigger admin/auth dialogs (sfltool, sudo, TCC tooling); no AXPress/AXUIElementPerformAction/AX writes, no guessed coordinates, no OCR-only pass, no sandbox workaround; no overwriting existing evidence/attempts/result.md (append-only, failed outputs preserved); never re-send Save All when the dispatch result is unknown; stop immediately on a wrong album; `/private/tmp` is not durable storage.
9. **Evidence rules:** every attempt keeps full inputs, argv/env minus secrets, stdout/stderr/exit, hashes of the tested program, independent side-effect counters, before/after state, and a SHA-256+bytes artifact manifest — all independently readable.
10. **Escalation triggers:** an unsatisfiable combination of "same uninterrupted dispatch / crash recovery / CLI-GUI transport", contradictory source or historical-intent evidence, a second failed fix of the same root cause, independent review finding new self-certification or cross-test contamination, or an undecidable bridge necessity — escalate to the named senior model with minimal reproduction, raw output, tested-version hash, failed attempts, assumptions and counterexamples, and one single question to decide.

## GOAL_ALIGNMENT

- The plan's `PRIMARY_OUTCOME` (plan.md:491) faithfully captures result 1 under the no-ambiguous/duplicate-transaction constraint, and `CORE_REQUIREMENTS` item 3 (plan.md:493+) plus the three-result section (plan.md:444) carry result 2. The Rev15 wave statement (plan.md:27–30) states the verification-real mandate.
- Gap: `PRIMARY_OUTCOME` as written omits the wave milestone the user made explicit — reproduce R1–R7 through the true entry, fix, rerunnable/re-readable evidence, no PASS-number inflation (RV-7, MINOR wording).
- Acceptance criteria prove the outcome rather than implementation completeness: real CLI invocations with independent oracles (plan.md:797–803), the axis-correct fixture matrix with exact per-axis statuses (plan.md:668–706), the real-command expectation for the current authority (plan.md:663–665), and the status-routing fixtures with `evidence_basis` oracles (plan.md:876–905).
- No supporting tool/detail has become the de facto goal: the binding grammar, source-evidence record, status contract and ownership protocol are means traced to provenance truthfulness, anti-self-certification and evidence integrity. The source-identity blocker is correctly preserved as a first-class CORE outcome, not dissolved into tooling work.
- Offline-vs-GUI truthfulness is explicit and structural: `E2E_RATIONALE` (plan.md:11–13), F5 non-acceptance labeling with a driver oracle (plan.md:236, 383, 903), and "offline or fixture PASS is never reported as GUI end-to-end success" (plan.md:456).

## NECESSITY_AND_TRACEABILITY

| Material work | Serves | Class | If removed |
|---|---|---|---|
| §15.1 one in-process dispatch window, reconciliation-only resume | R1/R2 at-most-once; user's "no double Save All" invariant | CORE | crash-orphaned intents could re-dispatch; the reproduced R1/R2 hole reopens |
| §15.2 schema-legal external binding + re-hash + negative controls | exact source correspondence; 禎/楨 separation | CORE | forged/deleted/mutated provenance could read CONFIRMED |
| §15.3 source-evidence record + refusal order | refusal classes at the true entry | CORE | MISSING/INVALID source refusals untestable; calibration truthfulness lost |
| Finalize trust (verification JSON identity + binding) | success semantics | CORE | a VERIFIED terminal state could be committed without trusted evidence |
| Verifier grounding/read-error/image-integrity rows | R5 truthfulness | CORE | truncated PNG / sample-2 read errors could still PASS |
| Driver ownership/no-default-removal protocol (§15.5) | R6b evidence integrity; rerunnability | CORE | cross-test destruction makes evidence non-reproducible (already reproduced) |
| Closed loop at the real entry (F7/case 01) | reusable capability (result 2) | CORE | no proof the product boundary works end to end |
| Status v4.2 routing fixtures (18 rows) | closure/routing contract; harness-mandated | SUPPORTING (mandated) | closure could be mis-routed/self-waived; required by the Stage-02 gate contract itself |
| `BRIDGE_READINESS` | diagnostic only | SUPPORTING/NON_GATING | localizes an observation gap, never gates |
| `DOCUMENTATION_RETENTION_HEALTH` (task-evidence scope only) | independent re-readability of evidence | SUPPORTING, HARD_CLEAN with written rationale | manifests could rot; scoped to task evidence exactly |
| GUI ellipsis observation | route evidence only if necessary | CORE-on-demand | if exact provenance is proven, `ROUTE_NOT_NEEDED` with rationale |

No significant untraceable work was found; the largest single block (status fixtures) is externally mandated by the v4.2 closure contract, not planner preference. Two items are *unimplementable as written* rather than unjustified: RV-1 and RV-2.

## GATE_AND_VETO_AUDIT

- All 11 CORE checks (plan.md:852–863) carry HARD_CLEAN gates, each with an explicit failure classification; none is justified only by schema/completeness. `SOURCE_CORRESPONDENCE` and `FORMAL_STATE_READONLY_RECONCILIATION` are non-waivable with primary-outcome/safety rationale — proportionate.
- No SUPPORTING/BEST_EFFORT item holds a global veto: `BRIDGE_READINESS` is `NON_GATING` with the rationale "non-gating unless route-specific necessity is proved"; `DOCUMENTATION_RETENTION_HEALTH` is HARD_CLEAN only inside the exact task-evidence scope with a written independence/provenance rationale, and is waiverable with a named authority (project owner, exact scope).
- Waiverability and authority are Plan-time decisions with "no agent can approve its own waiver" stated (plan.md:850) and enforced by fixtures that reject self-waiver and preserve the original FAIL (plan.md:889–890, 905, 928).
- The route gate is scoped, not global: `ROUTE_NOT_NEEDED` with explicit rationale when exact provenance is already proven (plan.md:939–941).
- Safety-critical conditions are not merely advisory: `TRANSACTION_RESUME_CORE` (repeat dispatch), `VERIFY_NEGATIVE_FIXTURES` (axis conflation) and `VERIFY_REAL_DESTINATION` (false acceptance) are CORE/HARD_CLEAN with TASK_REGRESSION classification.
- RV-3 is the one place where a safety-relevant axis rule is stated more weakly than its own matrix, so it should be tightened (one word) rather than left to Stage 04 interpretation.

## COUPLING_AND_FAILURE_CONTAINMENT

Failure-state audit against the §15.1 resume table and cases 01–19:

| Partial-failure state | Persisted shape | Legal recovery | Verdict |
|---|---|---|---|
| crash during 0→1 intent replace | no run / no run id | fresh `prepare` | contained |
| adapter dies after side effect (case 02) | rev1, intent committed, not attempted, counter=1 | `resume` → barrier (rev2) → `SAFE_ABORT` finalize | contained, no re-dispatch |
| product dies in the same window (state identical to case 02) | rev1, intent committed, not attempted, counter may be 0/1 | same row-4 barrier path | contained (RV-5: equivalence only argued in prose) |
| dispatch UNKNOWN (cases 03/19) | rev2 barrier, manual_reconciliation_required=true | `resume` idempotent; commit refused; `SAFE_ABORT` finalize → rev3 | contained |
| post-dispatch pre-commit (RETURNED) | rev2, SAVE_ALL_RETURNED | verify → commit → finalize | contained |
| storage fault after replace (case 09) | payload committed, process returned exit 1 | fresh `resume` → `SKIP_TERMINAL` | contained; uncertainty preserved in logs |
| race loser (cases 05/07) | no write, conflict class | retry after barrier release / operator decision | contained |
| READBACK_UNCERTAIN with no replacement | prior revision intact | re-run the same operation | contained |

- Every non-terminal state exits through a legal operation; no state requires a forbidden recovery (retry Save All, state rewrite, manual edit). The one true containment defect is structural: the barrier's persisted provenance link (`reconciliations[].evidence`) is defined twice with incompatible grammar (RV-1), so the read path for exactly the crash-window recovery this wave exists to close can be implemented in two mutually unintelligible ways.
- Independent signals are not collapsed: registry association, source provenance and state legacy status are separate axes with explicit non-interference rules (plan.md:210–214, 356–366, 713).
- No low-value adapter is a single point of failure: the dispatcher/adapter replaces external I/O only and its counter is the independent at-most-once oracle (plan.md:317–318, 802).

## DESIGN_ECONOMY

Concrete minimal changes that remove work without weakening the goal:

1. **Delete the second reconcile grammar.** §15.1's `reconcile:<kind>:<relpath>:<sha256>` and the "§15.2 base rules" phrase (plan.md:97) contradict §15.2's `reconcile:<relpath>:<sha256>` resolving inside the operation's own `--evidence-dir` (plan.md:120–121, 125–129). Pinning one 3-segment form removes an undefined token, an undefined resolution base, and a Stage 04/05 guessing step (RV-1).
2. **Pin the user-fact record once.** Specifying the exact key set/semantics for a CONFIRMED user-fact record (or declaring user facts evidence-only) removes an entire class of Stage 04 speculation and makes the DONE user-fact path testable (RV-2).
3. **Delete no CORE work.** The 19 transaction cases map 1:1 onto R1–R7; the 12 verifier negatives protect the source-identity oracle; the 11 authority rows keep formal state untouched; the 18 status fixtures are required by the closure contract. None of these is completeness theater.
4. **Retained cost, justified:** Rev11–Rev14 history sections are kept because reviews reference them and Stage 03/05 must detect stale approvals; deleting them in this revision would cost more than it saves. The `--pause-at`/`--barrier-file` fault flags are the only mechanism for the race-loser cases and are fault-reproduction, not safety manufacture.

## CRITICAL_PATH_AND_PRIORITY

- Correct order is preserved: Stage 03 handoff bound to the approved revision/hash → fresh Stage 04 implements F1–F7 through the real entry → case wave + real-entry loop → Stage 05 independent acceptance. Within the wave, the transaction core (cases 01–04, 13–19) and the verifier negatives protecting the source oracle are the critical path; status fixtures are closure-supporting and must not delay real-entry evidence.
- The plan fixes semantics before implementation (§15.1–§15.3 normative), which is the right priority for a crash-window/success-semantics change; no supporting item (bridge, retention, route) consumes the core path. Route work is correctly last and conditional (plan.md:822–825, 939).
- Priority inversion risk today is not in the plan's sequence but in the review loop: attempts 01–18 have not yet produced a working, verified automation path. Rev15's job is to stop that by making the remaining text defects small and explicit; RV-1/RV-2 are the only items standing between Rev15 and Stage 03.

## REQUIREMENT_FIDELITY

Attempt-17 findings F-1…F-8 re-checked against Rev15 text (verified, not trusted):

- **F-1 (F1′): closed.** §15.1 (plan.md:31–78) moves the single dispatch window inside `prepare` (rev 0→1 intent, dispatch, rev 1→2 post-dispatch record), fixes the precedence authority → adapter-flag semantic rejection → operation logic, makes `resume` reconciliation-only and idempotent, and rewrites cases 01/02/03/04/09 with the exact field names (`intent_state`, `dispatch_state`, `intent.dispatch_outcome`, `intent.trigger_outcome`, `save_all_retry_allowed`, `dispatch_evidence`). All field names exist in the schema `$defs` (verified).
- **F-2 (F2′): closed.** §15.2 (plan.md:117–166) stores the binding in schema-legal string fields only (`events[].evidence`, `verified_albums[].evidence` — both `type: string, minLength: 1` in the schema, verified), requires external re-hash at the recorded path, and pins four negative controls with Source UNRESOLVED / exit 4. Residual: RV-2 (user-fact record shape) and RV-3 (axis wording) remain.
- **F-3 (F2″): closed.** §15.3 (plan.md:167–199) pins the source-evidence record schema including a complete `$defs/calibration`, `evidence_artifacts[]`, and the refusal order MISSING_SOURCE_EVIDENCE/MISSING_DISPATCHER → INVALID_SOURCE_EVIDENCE → persisted-precondition classes, with cases 13–18 added. Residual: RV-8 (no literal MISSING_DISPATCHER row).
- **F-4 (F4′/F5′): closed.** §15.4 adds the 12 verifier rows with exact expected axes/exit/classes, corrects the legacy row to Registry PASS / Source UNRESOLVED / LEGACY_PROVENANCE_LIMITED, and asserts `evidence_basis == "scenario_table_non_acceptance"` per row. Residual: RV-3 and RV-6.
- **F-5 (F6′): closed.** §15.5 (plan.md:240–253) enumerates the ownership protocol for every driver that creates/removes shared roots; I verified the actual `rmtree`/shared-root sites correspond to the enumerated set (plus `run_phase2_r*` covering `run_phase2_r6_status_selfcert.py`), and `tests/formal_reconciliation_driver.py` only creates caller-named evidence directories and removes nothing.
- **F-6: closed.** §15.6 (plan.md:255–262) binds self-references to revision 15 and Stage 03 to the approved revision/hash. Residual: RV-4 (`increments this TASK_ID` at plan.md:936 must read `PLAN_REVISION`).
- **F-7: closed.** §15.6 restricts the part-1 user fact to the visible-title character and keeps the same-source correspondence UNRESOLVED until part 2 or a machine join.
- **F-8: closed.** Production/test grammars are separated (plan.md:571–575), adapter options remain parsed but are rejected `INVALID_INPUT` after authority validation, so the authority rows still emit `INVALID_AUTHORITY` JSON; MISSING_DISPATCHER is re-worded as adapter-pair semantic rejection.

No relaxation of expectations, authority allowlists, or fixture-only back doors was found in Rev15 text.

## GROUNDING_AND_DRIFT

Verified in the repository:

- `$defs/run` has no `owner_id`/`source_provenance` and is `additionalProperties:false` — the plan's claim is true; ownership through `active_writer_id` + `intent.owner_execution_id` is the only schema-legal route.
- `intent.dispatch_outcome` ∈ {NOT_ATTEMPTED, RETURNED, ERROR, UNKNOWN}; `intent.trigger_outcome` has the seven values the plan uses; `intent.save_all_retry_allowed` is `const: false`; `run.intent_state`/`run.dispatch_state` contain the Rev15 vocabulary used by the resume table.
- `$defs/reconciliation` requires outcome/trigger_outcome/blocking_intent_released/manual_reconciliation_required/original_observation/proof/evidence; `proof` is nullable or `$defs/dispatch_evidence`; `evidence` is a non-empty string. The barrier entry shape is schema-legal.
- `run.verification` is nullable, so terminal SAFE_ABORT can persist it null.
- `tests/formal_reconciliation_driver.py` hardcodes the expected axis set independently of product output (independent oracle, not derived from product output) — consistent with the plan's claim.
- Evidence read-back summary exists and verifies: 4859 artifacts, 84 manifests, 0 problems, PASS. Phase-2 R1 counter 1→2 is recorded and matches the reproduced gap.
- Source hashes match handoff §4 exactly (see REVIEW_METADATA).

Drift found: **RV-2** — `evidence/20260916-user-fact/source-identity-user-fact.json` records `source_correspondence_result_at_recording: UNRESOLVED`, `status: PARTIAL`, `facts.app_bundle`, `facts.album`, `facts.expected_count`, `answer.part_2: UNANSWERED`; the plan requires `source_correspondence_result: CONFIRMED`, `app_identifier` and `fingerprint` with no pinned schema for a future record. The plan elsewhere correctly acknowledges the recorded fact cannot confirm, but the CONFIRMED-capable format is nowhere defined.

## ARCHITECTURE_AND_CONTRACTS

- The product boundary is the local package + CLI `python3 -m line_backup_acceptance`, with `transaction prepare|resume|commit|finalize|duplicate-check`, and it is truthfully declared not to drive LINE's GUI; the dispatcher/adapter is external I/O (plan.md:317–318, 400–403).
- Persistence flow: guarded replacement with whole-payload schema validation before every write; single authority file; no schema extension — the binding rides in existing string fields. Authority validation is first after argument parsing (plan.md:575). Test mode is a bounded `/private/tmp` case-root exception, rejected for DATA_PROJECT_ROOT.
- Two contract defects: RV-1 (persisted reconcile reference has two normative grammars/bases) and RV-2 (user-fact record contract undefined). Both are load-bearing for safety/recovery and for the DONE path respectively; both are text-only corrections.
- Compatibility: legacy records are readable and normalized to REGISTRY PASS / SOURCE UNRESOLVED / LEGACY_PROVENANCE_LIMITED without rewriting; new runs use `contract_revision` const `1.0-rc2`; no formal state is mutated during this wave.

## DATA_SECURITY_RELIABILITY

- Formal config/state/run-log and the 57 photos stay read-only; the only writes this wave may perform are isolated fixtures, evidence, and product code after the applicable gate. No admin/auth-dialog-producing commands, no AX writes, no downloads, no `/private/tmp` as durable storage — all restated in the plan and consistent with the user's prohibitions.
- Evidence integrity: append-only attempts, per-attempt SHA-256/bytes manifests, ownership markers, no default removal, independent read-back in both orders; the read-back verifier already demonstrates 0 problems across 4859 artifacts.
- At-most-once is anchored on an independent counter, and the ambiguity barrier is one-way (`save_all_retry_allowed` const false; no retry interpretation). No secret material is recorded (argv/env cleaned per the user's evidence rules).
- Residual reliability risks: RV-1 (barrier read-path ambiguity) and RV-2 (source-confirmation path), plus the note in RESIDUAL_MINOR_NOTES on deriving `blocking_intent_released` for the SAFE_ABORT path.

## IMPLEMENTATION_SEQUENCE

- Required sequence after the fixes below: Stage 01 revision mode (same TASK_ID, PLAN_REVISION 16) → fresh independent review of the new hash → Stage 03 handoff bound to revision+hash → fresh Stage 04 → Stage 05 independent acceptance. Stage 04 may not resolve RV-1/RV-2 by itself: both change persisted/semantic contract meaning, which is a planning change.
- Stage 04's within-wave order should be: transaction core (cases 01–04, 13–19) → provenance/finalize semantics (§15.2/§15.3) → verifier negatives (§15.4) → ownership reruns (§15.5) → status fixtures. The plan's own post-fix verification plan (plan.md:405–415) already encodes the re-run expectations.
- No stop condition is hidden: the handoff↔plan hash mismatch stop is explicit (plan.md:257–260), and escalation triggers from the user's `/goal` (same-root-cause twice, self-certification/contamination, undecidable bridge necessity) are represented.

## TESTABILITY_AND_ACCEPTANCE

- Oracles are independent and pre-computed: expected values are stated per row before product execution (plan.md:787–803, plan.md:905), a product PASS line is never an oracle (plan.md:797), the verifier manifest read-back is a separate check, and the formal-reconciliation driver hardcodes its expected axes (verified in code).
- Truthfulness of PASS is structurally protected: fixture/offline results carry `evidence_basis` labeling; the status module is declared non-acceptance and may not be cited by Stage 05 (plan.md:236, 383, 903); the real-command expectation for the current authority is the specific five-axis result (plan.md:663–665); no fixture row is presented as production E2E.
- Coverage of the v4.2 required fixtures is complete (canonical incident, implementation blocker, replan, CORE not-run/blocked/fail, CORE NOT_REQUIRED ± rationale, baseline unchanged, baseline unavailable/delta, hard-clean pre-existing debt, all-required-waived, retention waiver preserving the original FAIL, Stage 05 blocked, product defect, legacy normalization, contradictory axes, DONE) — plan.md:876–905.
- Remaining test-gaps: RV-5 (product-process kill equivalence), RV-6 (SAFE_ABORT `--verification-json`), RV-8 (MISSING_DISPATCHER row). None by itself invalidates safety semantics, but each is a cheap, concrete addition.

## SCOPE_AND_COMPLEXITY

- Scope is fixed by the user to one album and one wave; Rev15 adds no new component, dependency, or schema — it is a contract/protocol revision over existing drivers. The 17-attempt history is a review-loop cost, not scope growth; the plan's own additions are the minimum needed to close attempt-17's findings.
- The complexity budget is now dominated by executable checks that each trace to R1–R7 or to the harness closure contract. The two MAJOR findings are economy defects as much as contract defects: each costs Stage 04 a speculative decision, and RV-1 additionally costs a persisted-state compatibility decision.
- Recommended simplification (no goal weakening): fix RV-1/RV-2 text, fold RV-3…RV-8 into the same revision, then stop revising and implement.

## FINDINGS

### RV-1 — The persisted reconciliation reference grammar contradicts itself (two normative forms in Rev15)
- Severity: **MAJOR**
- Category: SEMANTIC_CONTRACT
- Affected: §15.1 resume/barrier table (plan.md:97) vs §15.2 binding grammar (plan.md:120–121, 125–129)
- Evidence: plan.md:97 writes the barrier's `reconciliations[].evidence` as `reconcile:<kind>:<relpath>:<sha256>` "resolved with the §15.2 base rules"; plan.md:120–121 defines the fourth kind as `reconcile:<relpath>:<sha256>` that "always resolves inside the operation's own `--evidence-dir`" and is never a source binding; the §15.2 base-resolution bullet (plan.md:125–129) defines bases only for `join:`/`user_fact:`/`fixture:`. The `<kind>` token is defined nowhere.
- Failure mechanism: the barrier reference is the persisted provenance link of the crash-window recovery state this revision exists to close. Stage 04 must choose between a 3-segment and a 4-segment form and between two resolution bases; a writer/parser mismatch leaves the barrier's evidence unparsable or non-conformant, and because the fingerprint-barrier release precondition (case 18 positive control, plan.md:764) and any independent read-back also interpret `reconciliations[].evidence`, divergent choices can silently change release eligibility or fail Stage 05 for a state the product itself wrote.
- Smallest correction: keep only `reconcile:<relpath>:<sha256>`, state in §15.2 that reconcile references resolve exclusively inside the operation's own `--evidence-dir` and are outside the join/user_fact/fixture base table and the source-CONFIRMED rule, and delete `<kind>` plus the "§15.2 base rules" phrase from plan.md:97. Add one line to the case-02/19 oracles asserting the exact persisted string form.

### RV-2 — The user-fact path to source CONFIRMED is not implementable or testable as written
- Severity: **MAJOR**
- Category: GROUNDING / SEMANTIC_CONTRACT
- Affected: §15.2 user_fact verification (plan.md:147–153) and the DONE condition (plan.md:940)
- Evidence: the plan requires "the preserved user-fact record in the Rev13 format, recording `source_correspondence_result: CONFIRMED` with the exact question, answer, supplier and time, `raw_requested_group` equal …, `app_identifier` equal, and `fingerprint` equal". The only preserved artifact (`evidence/20260916-user-fact/source-identity-user-fact.json`) has no `source_correspondence_result` key (it has `source_correspondence_result_at_recording`), no `app_identifier` (it has `facts.app_bundle`), no `fingerprint` object (it has `facts.album` + `facts.expected_count`), `status: PARTIAL`, and `answer.part_2: UNANSWERED`. No plan section pins the field names for a future CONFIRMED record, the form of a positive part-2 answer, or how the recorded `*_at_recording` keys map. The plan also acknowledges (plan.md:151–152) that the recorded fact cannot confirm — so the only reachable legal resolution of blocker 1 has no defined artifact.
- Failure mechanism: Stage 04 cannot implement the CONFIRMED check deterministically without inventing a record schema; doing so would be a semantic contract change smuggled into implementation. Independently, DONE's "one precise user fact in the preserved user-fact evidence format" (plan.md:940) is neither satisfiable nor fixture-testable as written, so either closure is silently unreachable or a future operator writes an arbitrary JSON that the check cannot validate. Either way the wave's own honesty rule ("offline/fixture must not fake success") is at risk for the album-data result.
- Smallest correction: pin the exact user-fact record contract in §15.2 — full key set and semantics (question/answer including the part-2 answer form, supplier, time, evidence SHA-256, `app_identifier`, `fingerprint`, record version/status), state whether a new record is required (the preserved file stays evidence-only), and add one positive fixture (a CONFIRMED-shaped record that yields source CONFIRMED with `source_kind=user_attestation`). Alternative acceptable resolution: restrict CONFIRMED to an authoritative exact join and explicitly demote user_fact to evidence-only, updating plan.md:940 accordingly.

### RV-3 — Registry axis rule says "terminal run" while its own matrix requires FAIL for a terminal SAFE_ABORT link
- Severity: MINOR
- Category: SEMANTIC_CONTRACT
- Affected: §15.4 axis rule (plan.md:211) and the verifier oracle restatement (plan.md:713) vs matrix row (plan.md:705); §15.2 already says "terminal `VERIFIED`" (plan.md:148)
- Evidence: plan.md:211/713: PASS requires a non-null `verified_run_id` that "resolves to a terminal run in the same state"; plan.md:705: `verified_run_id` → terminal SAFE_ABORT run ⇒ Registry FAIL. SAFE_ABORT is terminal, so the rule as written would yield Registry PASS.
- Failure mechanism: an implementer following the rule literally produces Registry PASS for a SAFE_ABORT-linked entry, contradicting the driver oracle (row fails → TASK_REGRESSION) and the source-grounding requirement; it also re-opens exactly the R5 defect class "terminal-SAFE_ABORT `verified_run_id` accepted" that the revision claims to fix.
- Smallest correction: replace "a terminal run" with "a terminal `VERIFIED` run" in both places.

### RV-4 — Revision-increment sentence names the wrong subject
- Severity: MINOR
- Category: SEMANTIC_CONTRACT / COMPATIBILITY
- Affected: plan.md:936
- Evidence: "Any semantic contract, product-boundary, E2E, or GUI-budget change increments this TASK_ID and repeats independent review." Harness routing increments `PLAN_REVISION` on the same `TASK_ID`; a TASK_ID is not a revision counter, and this sentence is exactly what Stage 03/04 read to decide whether an approval is stale.
- Failure mechanism: a Stage 04 reader could treat the sentence as license to continue under the same revision after a semantic change, or mis-scope the next replan; low immediate risk, high confusion value because it sits in the closure section.
- Smallest correction: "increments PLAN_REVISION on the same TASK_ID, invalidates prior approvals/handoff and repeats independent review".

### RV-5 — Case 02/03 model adapter death, not product-process death in the same window (equivalence not stated)
- Severity: MINOR
- Category: TEST
- Affected: §15.1 prepare result codes (plan.md:76–78), cases 02/03 (plan.md:787–788)
- Evidence: case 02 uses `dispatcher-crash-after-side-effect.py` with the product surviving to return `DISPATCHER_CRASH_AFTER_SIDE_EFFECT` exit 1 at revision 1; no case kills the product process itself after the adapter side effect and before the 1→2 replacement.
- Failure mechanism: the two states are textually identical (revision 1, `intent_state=INTENT_COMMITTED`, `dispatch_state=NOT_ATTEMPTED`, one counter line), so row-4 recovery covers both — but the plan does not say so, leaving a reader to wonder whether a product-kill could persist a different intermediate shape (e.g. partial replacement); a test-only reviewer could also claim the crash window is untested in its hardest form.
- Smallest correction: one sentence in case 02/03 declaring the state equivalence, and optionally one driver variant that SIGKILLs the product after the counter line is observed and then runs the same fresh `resume --no-dispatch` oracle.

### RV-6 — SAFE_ABORT finalize argv leaves `--verification-json` undefined for cases 10B/19
- Severity: MINOR
- Category: TEST / COMPATIBILITY
- Affected: grammar (plan.md:571), finalize contract (plan.md:50, 345–355), cases 10B/19 (plan.md:593, 764, 795, 797)
- Evidence: the literal finalize grammar includes `--verification-json PATH` for `--outcome VERIFIED|SAFE_ABORT`, and cases 13–19 must execute "the literal … argv described in the grammar block"; but F3 specifies verification-JSON validation only for VERIFIED, and the 10B/19 oracles never state what the SAFE_ABORT verification JSON must contain or whether the file must exist.
- Failure mechanism: driver and product can disagree (required-but-ignored vs. optional vs. validated) — a classic source of "test failed for the wrong reason" churn in a wave whose point is to stop churn.
- Smallest correction: make the option outcome-conditional in the grammar (required for VERIFIED) or pin a minimal SAFE_ABORT verification JSON fixture contract for 10B/19.

### RV-7 — PRIMARY_OUTCOME omits the wave milestone the user made the purpose of this task
- Severity: MINOR
- Category: GOAL_MISALIGNMENT
- Affected: Goal contract (plan.md:491) vs the authoritative `/goal` attachment and §Three results (plan.md:444–457), Rev15 wave (plan.md:27–30)
- Evidence: the user: "把驗證做實，而不是增加 PASS 數字或文件"; the plan's `PRIMARY_OUTCOME` states only the album-attribution/no-ambiguous-transaction outcome, while result 2 (reusable automation capability, verified through the real entry with rerunnable evidence) appears only in `CORE_REQUIREMENTS` item 3 and the three-result section.
- Failure mechanism: implementers and Stage 05 read `PRIMARY_OUTCOME` first; a supporting-looking placement of the wave's actual deliverable invites priority inversion (paperwork over the real-entry path) — the failure mode this task has already been fighting across attempts.
- Smallest correction: extend `PRIMARY_OUTCOME` to name both results explicitly (album data AND a verified, rerunnable automation path through the true entry), keeping the no-ambiguity/no-duplicate constraint.

### RV-8 — No literal case row exercises the MISSING_DISPATCHER prepare refusal
- Severity: MINOR
- Category: TEST
- Affected: §15.1 (plan.md:37–39, 77–78), §15.3 refusal order (plan.md:194–199), requirement matrix (plan.md:749), cases 13–19 (plan.md:764)
- Evidence: Rev15 makes the adapter pair mandatory and pins `MISSING_DISPATCHER` exit 2 as the first-prepare refusal ("There is no production `prepare` that commits an intent nobody can dispatch"), but the literal case set covers missing-source-evidence (13) and other refusals (14–18) without a `missing-dispatcher` row; authority rows cover authority negatives only.
- Failure mechanism: the exact guarantee R1/R2 depends on ("no prepare that commits an intent nobody can dispatch") is asserted but never executed at the real entry, in a wave whose declared purpose is to make exactly such guarantees real rather than textual.
- Smallest correction: add a `missing-dispatcher` row (prepare with `--source-evidence` but without the adapter pair) to the case-13/14 root family, asserting exit 2, class `MISSING_DISPATCHER`, zero state/counter/lock delta.

## REQUIRED_PLAN_CHANGES

Mandatory before Stage 03 (both are semantic-contract corrections and require Stage 01 revision mode, same TASK_ID, PLAN_REVISION 16, then a fresh independent review of the new hash):

1. Fix RV-1: one reconcile reference grammar (`reconcile:<relpath>:<sha256>`), reconcile-only resolution inside the operation's own `--evidence-dir`, remove `<kind>` and the "§15.2 base rules" phrase from plan.md:97; add one persisted-form assertion to the relevant case oracle.
2. Fix RV-2: pin the user-fact record contract for CONFIRMED (exact keys/semantics, part-2 answer form, evidence SHA-256, `app_identifier`/`fingerprint` placement, positive fixture and `source_kind=user_attestation`), or explicitly restrict CONFIRMED to authoritative exact joins and update plan.md:940.

Strongly recommended in the same revision (cheap, no scope change): RV-3 (one word: "terminal VERIFIED run"), RV-4 (`PLAN_REVISION` wording), RV-5 (crash-window equivalence sentence ± parent-kill variant), RV-6 (outcome-conditional `--verification-json` or pinned SAFE_ABORT fixture), RV-7 (PRIMARY_OUTCOME wording), RV-8 (MISSING_DISPATCHER row).

Not required: new components, new dependencies, new schema fields, deletion of Rev11–Rev14 history, or any change to the read-only fences, the no-redownload rule, the 禎/楨 separation, or the deferred production gate.

## RESIDUAL_MINOR_NOTES

- §15.1 says `blocking_intent_released=true` is "legal only for `outcome=ABORTED_BEFORE_SAVE_ALL_DISPATCH` … which only the SAFE_ABORT finalization path may write", but does not state what evidence lets the SAFE_ABORT path derive that proof. Tighten with one sentence: the release may be written only from verified no-dispatch observations (`save_all_invocation_attempted=false`, counter delta 0) and must never be written for a run whose dispatch axis is attempted/unknown. Low risk in this wave (production dispatch is deferred; case 19 already preserves the unresolved intent), but it is the future-wave double-Save-All guard.
- Resume result label `ALREADY_RECONCILED` is also used for the healthy post-dispatch pre-commit run (plan.md:92). Harmless (no write, no dispatch) but slightly misleading in operator logs; an optional wording fix would keep result codes honest about state.
- Plan line count is 946 (the review brief said 947); no content implication, recorded for accuracy.
- The `join:` path's artifact is only partially specified (parsed content must carry `group_key`/`app_identifier`/`fingerprint`), and "authoritative exact source join" has no defined provenance criteria anywhere in this wave. Acceptable because no such artifact exists yet and RV-2's fix will define the reachable path; if a join artifact ever appears, its authority criteria must be pinned before CONFIRMED may rest on it.
- Independent verification note: this review read `review/attempt-17/review_report.md` to confirm F-1…F-8 closure, did not read `review/attempt-18/`, and wrote nothing outside `review/attempt-19/`. No product CLI, driver, download, formal state/config/photo, or GUI/computer-use tool was invoked.

FINAL_STATUS: PLAN_REVISION_REQUIRED
NEXT_ACTION: Stage 01 revision mode on TASK_ID T20260916-0102-01-line-backup-acceptance: produce PLAN_REVISION 16 that fixes RV-1 and RV-2 (mandatory) plus RV-3…RV-8 (recommended), then submit the new revision and hash to a fresh independent Stage 02 review.
