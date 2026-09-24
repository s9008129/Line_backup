# Plan Review Report

## REVIEW_METADATA
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- REVIEW_ATTEMPT: `05` (fresh, independent Stage-02 reviewer; no Planner transcript). Finding IDs `RV-01…` below are attempt-05-local. Review attempts 01–04 (reports/snapshots) were consulted only **after** my own goal baseline and findings were formed, and only as incorporation cross-checks — their statements are claims, not authority. An `attempt-06/` directory exists in the tree (created by another process); it was not consulted as authority and was left untouched.
- REVIEWED_PLAN_REVISION: `3`
- REVIEWED_PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828` (recomputed on disk this round; matches the review target; 513 lines)
- PLAN_SNAPSHOT_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/review/attempt-05/plan_snapshot.md` (byte copy written before the canonical plan could change; SHA-256 identical to `plan.md`)
- Repository anchor observed (all recomputed this round): HEAD `766b22c4f8bf29b9d0a46049c75309c70593d66d` == `origin/master`, ahead 0, working tree untracked-only (12 `??` entries, no tracked modifications); staging `staging/RUN-20260923-111908-01` exists with 0 entries; Issue SHA `0b3c9efa…`; probe evidence SHAs `43998519…` / `afd6c26d…`; all 20 `HISTORICAL_REPLAY_PLAN` fixture SHA prefixes resolve byte-exactly (20/20); accepted baseline realpath-resolves to the `…_to_…` spelling and is 57 files / 17,924,900 bytes; name-inclusive manifest digest `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` reproduced with the trailing-newline method (no-trailing-newline control `287d95c2…` does not match); content-multiset digest `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf` reproduced with the no-trailing-newline method (trailing-newline control `af389c83…` does not match) and set-equal to `baseline-content-multiset.json` (SHA `3c932d8c…`); environment re-checked (macOS 27.0 (26A428), Swift 6.3.3, Xcode 26.6, SDK `MacOSX26.5.sdk`; `pointPixelScale` present in SCK headers; `ignoreShadows`/`includeChildWindows` present; no `contentScale`/`scaleFactor` symbol in SCK headers; LINE 26.0.2 installed, not running).
- Reviewer runtime/model: fresh Codex CLI session (informational; the model tag is not exposed to this session).

## OWNER_VERDICT
- **Goal:** one more verified end-to-end LINE album backup of `旻謙允禎成長日記 / 2024（05/13–05/17）/ 57` using the new macOS-native closed-loop architecture, with the single authorized production run executed only after every gate passes.
- **Essentials (what carries the outcome):** native capture/window identity, Vision text identity, one reviewed coordinate transform, the closed-loop Save All postcondition (chooser directly observed — never click-return, menu-gone, or count proxies), exactly-once confirmation into a fresh staging run, and filesystem/content proof against the accepted baseline → `DUPLICATE_CONTENT_CONFIRMED`, baseline untouched.
- **Optional / deferred (correctly non-gating):** Foundation Models diagnostics, registration/feature-print comparison, AX-vs-keyboard chooser fallback, documentation/manifest deliverables.
- **Global blockers and why:** only the one-shot irreversible phase is globally interlocked; each pre-live gate (capability probe, harness freezes, replay/adversarial, seven reviews, reconnaissance, baseline preflight) protects the irreversibility or the evidence standard. No supporting/best-effort item vetoes unrelated core work; waivers are denied to agents (`WAIVER_ALLOWED: NO`).
- **Complexity verdict:** proportionate. Each module (sensor, perception, actuator, AX chooser plane, state machine + ledger, harness + W2 freezes, staging verifier, reviews) maps to an outcome or must-not-break invariant; the deletion test passes for the optional planes.
- **Biggest remaining risk:** LINE's actual chooser shape can only be confirmed at the live step (or Phase-A observation). The plan handles this with a frozen predicate, refusal-with-cause (`INDETERMINATE_CHOOSER_REFUSED` incl. `frozen_predicate_mismatch`), zero retry, and an honest indeterminate terminal state — an accepted, pre-declared cost of the one-shot budget, not a plan defect.
- **Residual nits (non-blocking):** see FINDINGS `RV-01`/`RV-02` and RESIDUAL_MINOR_NOTES.

## GOAL_BASELINE
(own summary written from the authoritative attachment `~/.codex/attachments/41a5dfc8-e350-429c-a01b-aea3a67e03fd/pasted-text-1.txt`, 782 lines, SHA-256 `101a27299d07b673698ea4661f72cd4a7fe05b3d0df0cb179a3041e9cce534e5`, **before** reading the plan's rationale/details)
- **PRIMARY:** autonomously redesign, implement, validate, review, and — only after all safety/calibration gates pass — execute exactly one Rev28 production run for `jp.naver.line.mac`, group `旻謙允禎成長日記`, album `2024/05/13～05/17`, 57 photos. Never normalize or merge `禎 U+798E` / `楨 U+6968`.
- **SUCCESS is not clicks:** correct production album identity → native visual localization → reviewed native actuation → chooser postcondition confirmed → unique staging selected → download dispatched exactly as authorized → 57 complete stable images → content verification PASS → accepted baseline unchanged → registry/evidence updated consistently → no unexplained side effect. Because an accepted 57-photo baseline already exists, matching staging content is valid end-to-end proof (`DUPLICATE_CONTENT_CONFIRMED`) and must **not** create a second accepted production copy.
- **AUTHORIZATION ENVELOPE:** single new Rev28 production run for exactly that album/group; irreversible destination confirmation ≤ 1; SIDE_EFFECTING operations ≤ 1 unless idempotent recovery is proven; no historical coordinate reuse (every live coordinate fresh-derived); reversible navigation may use a reviewed bounded budget.
- **MUST-NOT-BREAK:** existing historical accepted baseline (57 files / 17,924,900 bytes / manifest digest `b7debe92…`) is READ-ONLY; do not reset/discard/overwrite/rewrite historical evidence; no pycache; no push; Rev27e uncommitted drafts are WIP evidence, not authoritative code.
- **OPERATIONS:** solve problems autonomously from repository evidence, macOS SDK/API inspection, deterministic offline tests, synthetic UI tests, or fresh read-only observation; do not ask the human merely because a detector/test/plan/implementation needs revision; reserve human input for genuinely external requirements.
- **ADVERSARIAL:** the goal's 22 named failure scenarios (wrong window/bundle/stale ID/wrong Retina/occluder/movement/wrong row/OCR defects/false positive/click miss/focus theft/timeout/fake chooser/unexpected write/zero-byte/partial/duplicate/restart/multi-display) must be exercised before production; production only if all required reviews approve the exact frozen implementation.

## GOAL_ALIGNMENT
- `PRIMARY_OUTCOME` (§GOAL_CONTRACT / META) matches the goal: the plan's success path is the goal's success path, and `DUPLICATE_CONTENT_CONFIRMED` (not a second accepted copy) is the primary proof — exactly the goal's semantics for an already-accepted baseline.
- Acceptance proves the outcome, not implementation completeness: the two live-proof legs are (1) the chooser directly observed (§10/§11; `V-04`/`V-05`) and (2) staging content equality with the baseline (57 files / 17,924,900 B / `ee958e64…`; `V-06`/§12), with `V-07` must-not-break on the baseline. Synthetic suites are explicitly forbidden from substituting for the live leg (§VERIFICATION_AND_ACCEPTANCE, §STATUS_SEMANTICS…).
- No supporting detail became the de facto goal: the name-inclusive digest `b7debe92…` is explicitly relegated to a baseline identity/tripwire role; the content predicate excludes names — correct, because baseline filenames carry the per-download token `260907` (verified on disk) while a fresh download must carry a new token.
- The plan restates the goal's six-step closed loop and "change nothing else"; no goal item was silently dropped or expanded beyond the envelope.

## NECESSITY_AND_TRACEABILITY
- Every `CORE` requirement (R1–R5, R8–R17, R19–R22, R24, R25) traces to an explicit goal clause or must-not-break invariant (native SCK/Vision/AX/Quartz sensing+actuation, chooser postcondition, single-run envelope, baseline/evidence preservation). `SUPPORTING` items (R6, R7, R18, R23) map to goal-named evidence/completeness and stay non-vetoing for unrelated work; no `BEST_EFFORT` item blocks anything.
- `V-01…V-11` each map to a goal/verification obligation with declared `GOAL_CRITICALITY`, `EVIDENCE_ROLE`, and `CLOSURE_GATE`; no gate exists merely for schema completeness.
- Traceability gap (non-blocking): R22's phrase "registry/evidence updated consistently" (verbatim from the goal) has no named Rev28 artifact — see FINDINGS `RV-01`.

## GATE_AND_VETO_AUDIT
- Global vetoes are confined to (a) the irreversible-production interlock chain (`LIVE_RUN_INTERLOCK: YES` rows plus the Phase-A reconnaissance gate) and (b) task-closure hard-clean items (`CLOSURE_GATE: HARD_CLEAN`). Each blocking item protects safety or evidence validity; §VERIFICATION_AND_ACCEPTANCE line 445 states the interlock-vs-closure distinction and rationale explicitly.
- No `SUPPORTING`/`BEST_EFFORT` global blocker without safety rationale: replay/adversarial (`V-08`) is `SUPPORTING/NON_GATING` yet interlocked before Phase B — justified as protection of the single irreversible dispatch, and now explicitly distinguished from closure gating.
- No self-waiver path: `WAIVER_ALLOWED: NO` / `WAIVER_AUTHORITY: NONE` for every item; only the owner could define a waiver and none is planned.
- `BASELINE_REQUIRED: NO` everywhere; no broad repository-wide gate is invented; the baseline comparison is tracked as its own subject (it is the success predicate), consistent with v4.2 broad-gate guidance.
- Fail-closed semantics exist for the load-bearing anchors: unresolvable/mismatched baseline or reference → `CHECK_RESULT: BLOCKED`, no degraded comparison, no skipped tripwire (line 88, §12, envelope (f), `V-07`); frozen-rule changes → replan + fresh review, never silent extension.

## COUPLING_AND_FAILURE_CONTAINMENT
- Signals are not collapsed into one flag: chooser affirmation requires a new surface + native-panel-shaped AX semantics + unambiguous ownership (census ingredient + bundle/signing + start time, pid-reuse rejected), with refusal fixtures; window identity is multi-source with stale-ID invalidation.
- Optional planes degrade locally (Foundation Models → diagnostics only; registration → deterministic comparison; AX chooser navigation → tested keyboard fallback) without blocking the core.
- The three-level tripwire ladder `L1 ⊆ L2 ⊆ L3` (staging ⊆ approved root ⊆ `~/Downloads`) contains failure at the narrowest boundary: L1 writes are the expected primary signal; L2 attributable-but-unexpected writes are recorded and disclosed (`ATTRIBUTED_EXTERNAL_WRITE_OBSERVED`) while unattributable writes fail closed (`ABORTED_UNATTRIBUTED_FILESYSTEM_WRITE`) and any baseline modification aborts immediately; L3 separates this-run scope violations (`ABORTED_WRITE_OUTSIDE_APPROVED_ROOT`) from unrelated environmental activity (disclosed context). The ≥10 s pre-dispatch environmental baseline is a purposeful anti-false-positive control for the observed concurrent-machine-activity risk.
- No low-value adapter is a single point of failure; refusals are the default under ambiguity — an empty pre-dispatch census **widens** the refusal requirement (§11 point 3).
- One-shot containment: zero retry on either irreversible dispatch; `NOT_RUN` probe leaves work pending rather than blocked; the run may end in a scoped non-success state with all evidence preserved.

## DESIGN_ECONOMY
- Deletion test: removing Foundation Models, registration, or the AX-chooser path costs no acceptance criterion (all non-gating); removing the harness/W2 freezes, ledger, or baseline tripwires does cost safety/acceptance. The remaining complexity is the minimum that makes a one-shot irreversible run reviewable and its evidence verifiable.
- One canonical transform component with a recorded per-capture bbox/config avoids coordinate duplication; the state machine + append-only hash-chained ledger is one recovery/evidence mechanism, not several parallel ones.
- The 25-scenario matrix (22 goal-mandated + 3 labeled extensions) costs little on top of the harness and buys the goal's required coverage; extensions are explicitly labeled, not smuggled in.
- No speculative future-facing abstraction, plugin framework, or unbounded state multiplication found.

## CRITICAL_PATH_AND_PRIORITY
- Sequence fixes the CORE path first: W1 deterministic core + probe → W2 harness + freezes → W3 locators/replay → W4 policy/state/ledger/verifier → W5 adversarial → W6 docs (off critical path) → W7 conditional reconnaissance + single live run + verification + closeout.
- The irreversible live step is last among live actions and gated by an explicit chain (a)–(g); Phase A reconnaissance has zero side-effecting dispatches and cannot consume the production budget.
- No priority inversion: supporting documentation does not precede interlock gates; Stage 05 verifies CORE first and recomputes from disk.

## REQUIREMENT_FIDELITY
- Album identity, group, date range, count (57), byte total (17,924,900), manifest digest (`b7debe92…`), and the no-normalization rule (禎/楨) all reproduce exactly from the goal and from disk.
- The goal's 22 adversarial scenarios map 1:1 to `G01–G22` in goal order, plus 3 explicitly labeled extensions `X01–X03` (= 25); `G05` refined to a separate-process occluder, `G21` to crash-injection/observe-only resume, `G22` labeled fail-closed on this single-display machine. Verified against the goal text, not the plan's summary.
- Single-run fidelity: Save All dispatch = 1 and destination confirmation = 1, per operation type; exactly one confirmation action chosen before dispatch (never both `AXPress` and `Return`); a non-effect consumes the budget; **only the chosen confirmation action consumes the 1-unit budget** — navigation/preparation steps are logged with pre/post evidence and never counted as confirmation (line 284–285, attempt-04 `RV-04` incorporated).
- Out-of-scope discipline: no new album, no second accepted copy, no push, no pycache, historical evidence preserved; `CHANGE_MAP` adds only `rev28/**`, the new evidence dir, the task dir, and one `.gitignore` line.

## GROUNDING_AND_DRIFT
- **attempt-04 `RV-01` (blocking MAJOR) is fixed:** plan line 87 now spells `album-2024-05-13_to_2024-05-17_57` (hex `5f 74 6f 5f`), it realpath-resolves to the actual directory, and it matches `baseline-content-multiset.json.source_dir` verbatim. I re-ran the full consequence chain: 57 files; 17,924,900 bytes; manifest digest `b7debe92…` with trailing newline (negative control `287d95c2…` does not match); content-multiset `ee958e64…` with no trailing newline (control `af389c83…` does not match); JSON set equality holds; JSON SHA `3c932d8c…`. Line 88 adds the fail-closed resolution rule (`CHECK_RESULT: BLOCKED`, no degraded comparison, no skipped tripwire), mirrored in §12 and envelope (f) — attempt-04's required correction is present.
- All other checked repo facts reproduce: HEAD/origin/master/ahead 0/untracked-only; Issue and probe SHAs; 20/20 replay fixtures; staging empty; environment/SDK claims (`pointPixelScale` present; no `contentScale`/`scaleFactor` in SCK headers; `ignoreShadows`/`includeChildWindows` present); LINE installed 26.0.2, not running.
- Digest-method wording is now byte-exact (trailing-newline method for the manifest digest; no-trailing-newline stated for the multiset), removing attempt-04's residual ambiguity note.
- attempt-04 minors incorporated: `RV-02` canonical §7.3 enums + `CHECK_ID V-01…V-11` + `BASELINE_REQUIRED` + `WAIVER_ALLOWED`/`WAIVER_AUTHORITY` + `CHECK_RESULT: NOT_RUN` default + `LIVE_RUN_INTERLOCK` column (§441–461); `RV-03` named `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED` with ledger/final-report disclosure, never silently absorbed (§10, terminal states); `RV-04` confirmation-budget wording (line 284); `RV-05` empty-census widens refusal (§11 point 3); three-level tripwire ladder with the three named outcomes (§10).
- No drift detected beyond the two MINOR documentation items in FINDINGS.

## ARCHITECTURE_AND_CONTRACTS
- Module boundaries are coherent (sensor / identity / perception / actuator / AX plane / focus / state machine / risk classes / postcondition / chooser / filesystem / transaction), each with explicit inputs, evidence, and failure semantics; no hidden cross-layer state (state persisted atomically; ledger hash-chained; observe-only resume).
- Risk classification is pre-registered and reviewed (`REVERSIBLE_NAVIGATION` / `PRE_SIDE_EFFECT_ACTION` / `IRREVERSIBLE_SIDE_EFFECT`); Save All runs under IRREVERSIBLE semantics because the historical classification is indeterminate — conservative in the safety direction, with an explicit `saveAllEmpiricalClassRecord` for future decisions. The reconciliation-barrier supersession is a reviewed artifact (R24 / Review 9) before any new Save All.
- Contract vocabulary now uses the canonical v4.2 §7.3 enums with the plan-local interlock column; `CHECK_RESULT` defaults to `NOT_RUN` and per-item results are recorded in `execution.md`/Stage-05; the final report carries the separate v4.2 subjects with scoped blockers.
- No legacy active terminal schema conflict: v2 subjects are used, legacy evidence is preserved read-only, and `IMPLEMENTATION_BLOCKED` is reserved for unfinished product implementation.

## DATA_SECURITY_RELIABILITY
- Privacy/trust boundaries: live captures/OCR stay in the untracked evidence dir and are never pushed; TCC grants are re-verified in the executable context (`V-01`), not merely at probe time; a clipboard chooser path is not used unless AX and keyboard both fail under review.
- Data integrity: baseline is READ-ONLY; any modification → immediate abort regardless of attribution; content comparison is set-based on SHA-256 and recomputed by Stage 05 from disk, never trusting Stage-04 claims; no accepted-copy creation, never copy staging into the baseline.
- Reliability: at-most-once irreversible dispatches; bounded reversible budgets with a named abort; crash recovery resumes observe-only with ledger hash-chain continuity; bounded timeouts with named terminal states (`CHOOSER_OBSERVED_AFTER_WINDOW`, `NO_CHOOSER_OBSERVED`).
- Attribution semantics are level-specific and fail closed on unattributable writes; attributable external writes must be disclosed in the ledger and final report (attempt-04 `RV-03` incorporated). Concurrency: `G22` fail-closed on single-display; concurrent-machine risk handled by pre-dispatch baseline + census diff + disclosure.

## IMPLEMENTATION_SEQUENCE
- W1→W7 ordering is sound and matches the critical path; W2 freezes (capture per-state rule, postcondition bounds, chooser predicate, tripwire attribution) are review inputs, and post-freeze rule changes are replan + fresh review, never implementer edits — correct one-shot discipline.
- The envelope prerequisite chain (a)–(f) plus Phase-A (g) is explicit and ordered; failure at any prerequisite is a pre-live repair/replan (or a genuine external block routed to `BLOCKED_WITH_ROOT_CAUSE` after the audit threshold), not a consumed production budget.
- No sequencing defect found; the baseline-path fix that attempt-04 required before handoff is now satisfied.

## TESTABILITY_AND_ACCEPTANCE
- Acceptance is observable and recomputable: chooser direct observation (SC+AX+CG evidence), exactly-once confirmation with durable intent, staging predicate (`V-06`) with named mismatch classes, baseline tripwires (`V-07`), Stage-05 recompute-from-disk (`V-10`), final report separating the v4.2 subjects with scoped blockers.
- v4.2 §7 status-contract checks: repository-health check is `SUPPORTING/NON_GATING` (not product CORE); broad-gate policy explicit; waiverability explicit and non-self-waivable; CORE failure/not-run/blocked routing named (`NOT_RUN` → pending; `FAIL` → replan/blocked; `REVISION_REQUIRED` → repair + re-review; baseline unavailable → `CHECK_RESULT: BLOCKED`; baseline delta → abort + report); terminal taxonomy covers success, late affirmative, no-chooser, refusal-with-cause, mismatch classes, aborts, indeterminate, and `BLOCKED_WITH_ROOT_CAUSE`; contradictory state names are forbidden (§10); `DONE` prerequisites (frozen-SHA reviews, deliverable manifest, replay, adversarial, ledger, handoff, local commits, closeout audit) are stated; legacy artifacts preserved.
- Fixture obligations: canonical incident, true implementation blocker, CORE fail/blocked/not-run/not-required, replan, baseline unavailable, baseline delta, hard-clean debt, formal waiver with original result preserved, independent-acceptance pending/environment-block/product-defect, contradictory-state rejection, legacy normalization, and DONE prerequisites are either explicit at plan level (baseline unavailable/delta, waiver, CORE states, contradictory-state rule, DONE prerequisites) or explicitly routed to Stage-04 `execution.md`/Stage-05 reports — acceptable at plan level (same judgment as attempts 03/04); see RESIDUAL_MINOR_NOTES.
- The goal's "never claim BACKUP_COMPLETE from clicks/counts" is enforced by construction: `DUPLICATE_CONTENT_CONFIRMED` requires direct chooser observation plus filesystem/content equality; synthetic passes never imply live results.

## SCOPE_AND_COMPLEXITY
- Scope is bounded by the goal: one album, one group, one authorization envelope; no new dependencies beyond the goal-named macOS-native frameworks (SCK/Vision/Quartz/AX/AppKit harness); no network surface.
- Complexity budget is justified item-by-item; optional planes are cheap and degrade safely; the only imprecisions are documentation-level (`RV-01`, `RV-02`) and do not affect deliverable scope.

## FINDINGS
### RV-01
- ID: `RV-01` (attempt-05-local)
- Severity: `MINOR`
- Category: `SEMANTIC_CONTRACT`
- Affected: `plan.md` R22 (line 64) and `DELIVERABLES_MAP` (line 500+).
- Evidence: R22 requires "registry/evidence updated consistently" (carried verbatim from the goal, source line 725), but the Rev28 plan defines no "registry" artifact; `DELIVERABLES_MAP` names the "filesystem manifest + transaction/reconciliation ledger" and the evidence dir, and the legacy registry concept lives in Rev27 code (`src/line_backup_acceptance/verifier.py`), which is not this architecture. There is no Rev28 registry deliverable for the word "registry" to verify against. `[VERIFIED]`
- Failure/rework mechanism: an implementer/verifier cannot unambiguously decide what artifact constitutes "registry" in Rev28; the sub-condition could be checked as "ledger + evidence" (the likely intent, given the goal's own pairing) or could generate a spurious new deliverable. Low impact — the ledger/manifest/evidence artifacts already cover evidence consistency — but the success-condition wording is not self-mapping.
- Smallest required correction: add one clause in `DELIVERABLES_MAP` (or R22) mapping "registry/evidence" to the Rev28 ledger + manifest + evidence dir, or state explicitly that the legacy registry concept is superseded by the ledger, which carries the same consistency obligation.

### RV-02
- ID: `RV-02` (attempt-05-local)
- Severity: `MINOR`
- Category: `SEMANTIC_CONTRACT`
- Affected: `plan.md` META line 8 ("no gate is weakened").
- Evidence: revision 1→3 contains two deliberate, reviewed semantic narrowings — (a) capture-geometry exact equality (`image.px == bbox.size × scale`, ±0.5 px) → W2-frozen validated tolerance (required by attempt-02 `RV-01` after probe evidence showed bbox ≠ frame); (b) abort-on-any-unexpected-write outside staging → abort-on-unattributable-write with `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED` disclosure (deliberate; attempt-03/04 reviewed the compensating controls). My revision diff found **no** `CORE→SUPPORTING` or blocking→non-blocking class downgrades, and both narrowings are explicitly documented (§1/R9/§10) and independently reviewed. `[VERIFIED]`
- Failure/rework mechanism: a downstream reviewer could read "no gate is weakened" as proof that no semantic change occurred since revision 1 and skip re-checking the two narrowings; because the actual rules remain visible in §1/R9/§10 and were independently reviewed, the residual risk is small.
- Smallest required correction: extend the META sentence to name the two reviewed narrowings (capture tolerance; unattributed-write attribution) so the claim is precise.

## REQUIRED_PLAN_CHANGES
- None that block approval. No unresolved `BLOCKER`/`MAJOR` was found; goal alignment, implementation path, safety/rollback semantics, compatibility, and acceptance contracts are sound for this revision.
- Optional, non-blocking (fold into any future revision; do not trigger revision mode by themselves): `RV-01` one-clause mapping of "registry/evidence"; `RV-02` one-clause precision on the META claim.

## RESIDUAL_MINOR_NOTES
- Postcondition bounds (≤150 ms for 8.0 s, then ≤500 ms to a 15.0 s hard cap, ~30 s late sample) are plan-time provisional and correctly re-frozen by W2 (≥20 real-panel runs) and bound by review 4; ensure review 4 records the measured latency distribution and margin, and that post-freeze changes remain replan (the plan says so).
- §13's crash-recovery phrase "never re-dispatching an irreversible action without a fresh reviewed decision" vs the envelope's "no retry of any irreversible op": within this authorization the envelope binds (a second irreversible dispatch is out of scope; owner-only). One sentence clarifying that the envelope's rule governs would remove the tension.
- The v4.2 status-mechanics fixtures named in the review prompt's integration note are routed to Stage-04 `execution.md`/Stage-05 reports rather than enumerated at plan level; the plan binds the subjects and closure routing. Ensure those stages carry per-item `CHECK_RESULT`/`WAIVER_STATUS` and the contradictory-state rejection fixture.
- `G22` (multi-display) is correctly fail-closed on this single-display machine; no multi-display hardware proof is claimed.
- Round-2 marker-color tooling detected only magenta/yellow clusters (cyan/green empty); no load-bearing plan fact depends on it — keep marker-color detection out of production dependencies.
- The attempt-04 baseline-path typo also appeared in attempt-02's metadata; now that the plan carries the correct spelling, downstream artifacts should copy the path only from `baseline-content-multiset.json.source_dir` or the corrected plan.

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Proceed to Stage 03 Handoff for PLAN_REVISION 3 / SHA-256 63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828 (compile `handoff.md`; no replan, no further plan revision).
