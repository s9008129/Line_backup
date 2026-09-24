# Plan Review Report

## REVIEW_METADATA
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- REVIEW_ATTEMPT: `review/attempt-01` (Review A, fresh context)
- REVIEWED_PLAN_REVISION: `1`
- REVIEWED_PLAN_SHA256: `5575aca5f2c8ededa3f76ff79baf6b82eecd25353457b709982eb05e6cbcbbb9`
- PLAN_SNAPSHOT_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/review/attempt-01/plan_snapshot.md` (SHA-256 identical to canonical plan at capture time, recomputed before and after this report: MATCH)
- Repository anchor observed: `git rev-parse HEAD origin/master` -> both `766b22c4f8bf29b9d0a46049c75309c70593d66d`, ahead 0; working tree contains only untracked paths (Rev27e WIP, prior evidence, this task dir) [VERIFIED]
- Issue SHA-256 observed: `0b3c9efab209bcb4c8c9b5dcaa5fa1ca6279234df0ee3cc0984da829ead67a2d` = expected [VERIFIED]
- Accepted baseline observed: 57 files, 17,924,900 bytes, recomputed digest `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` (method: sorted `relpath\tsize\tsha256` lines, SHA-256 of concatenation) = expected [VERIFIED]
- Staging observed: `staging/RUN-20260923-111908-01/` exists, 0 entries, 0 bytes, sole child of `staging/` [VERIFIED]
- Plan status at review: `READY_FOR_REVIEW` (reviewable; not INVESTIGATION_ONLY/BLOCKED)
- Reviewer runtime/model: Codex CLI fresh-context reviewer (exact model string not exposed in this environment); read-only for product code and `plan.md`; only writes: plan snapshot + this report

## OWNER_VERDICT
Goal as understood: redo the backup of LINE group-album `2024/05/13～05/17` (group `旻謙允禎成長日記`, 57 photos) through a NEW native macOS 27 route (ScreenCaptureKit capture -> Vision identity -> Quartz click -> directly observed chooser -> one exactly-once confirmation into a fresh staging folder -> filesystem/content proof), and prove the downloaded copies equal the already-accepted 57-photo baseline WITHOUT touching that baseline.

What is truly essential (CORE): native capture; exact album/group identity; one reviewed coordinate transform; a real system pointer event; direct observation of the chooser (not "click returned"); a single destination confirmation; 57 complete, stable, decodable files; content equal to the baseline (`DUPLICATE_CONTENT_CONFIRMED`); baseline unchanged; historical evidence preserved byte-identical; no retry of any irreversible action.

Optional / degrades locally (should NOT stop the core route): Vision registration/stability comparison, Foundation Models diagnostics, AX-first chooser path (falls back to a reviewed keyboard path, or stops with zero confirmation), documentation wave.

What can stop the whole thing and why: (1) the pre-live gate chain (capability proof, synthetic-harness calibration, offline replay, adversarial suite, seven topic reviews + adversarial review + barrier-supersession review) deliberately blocks the one authorized Save All — these gates exist because the single live click is irreversible-per-envelope and unverifiable except by direct postcondition; (2) if no chooser is directly observed after the one allowed Save All, the run ends honestly as a scoped indeterminate with no retry — this is the goal's own safety rule (exactly-once), pre-declared as accepted risk, and it is the right behavior even though it can end the task short of success.

Complexity verdict: large but almost entirely goal-mandated (native Swift engine, synthetic AppKit harness, locators, transform, actuator, postcondition monitor, chooser driver, state machine, ledger, verifier, 9 reviews, replay, adversarial matrix). Within it the design is economical: ONE actuator path, ONE coordinate-transform component, deterministic pure cores with thin OS edges. No significant gold-plating found; no deletion-test failure that would remove an element without harming acceptance or the safety envelope.

Biggest remaining risk: the one-shot live run depends on LINE-specific surface facts (popup child-vs-window kind, AX exposure, real chooser identity/latency) that are first proven during the live engagement itself; mitigations are reversible-navigation reconnaissance, fail-closed locators, branch-accommodating capture design, and the conservative no-retry rule. A detector false-negative (e.g., a genuine chooser not counted within the bounded postcondition window) would end the run honestly but without the end-to-end proof, and the single Save All budget cannot be recovered. Findings RV-01/RV-04/RV-05 below are the concrete pre-live items to close.

## GOAL_BASELINE
(Reconstructed from `/Users/hsiaojohnny/.codex/attachments/41a5dfc8-e350-429c-a01b-aea3a67e03fd/pasted-text-1.txt` BEFORE reading the plan.)

- PRIMARY_OUTCOME: autonomously redesign, implement, validate, review and - only after all safety/calibration gates pass - execute a single Rev28 production run of the LINE album backup for exactly `旻謙允禎成長日記 / 2024/05/13～05/17 / 57`, using the observable closed-loop contract OBSERVE PRE-STATE -> LOCATE -> ACT -> OBSERVE DIRECT POSTCONDITION -> VERIFY FILESYSTEM EFFECT. Terminal success labels: `REV28_END_TO_END_LINE_ALBUM_BACKUP_VERIFIED` (+ `DUPLICATE_CONTENT_CONFIRMED` if staging content equals the accepted baseline); `BLOCKED_WITH_ROOT_CAUSE` only for a genuinely unresolvable external dependency.
- SUCCESS_EVIDENCE: correct album identity; native visual localization; reviewed native actuation; chooser postcondition directly observed; unique staging selected; download dispatched exactly as authorized; 57 complete stable images; content verification PASS; accepted baseline unchanged; registry/evidence consistent; no unexplained side effect. A click return, menu disappearance, chooser appearance ALONE, panel-service presence, or unverified count may never be claimed as backup success.
- MUST_NOT_BREAK: accepted baseline READ_ONLY/unchanged, no second accepted copy; never normalize/merge `禎 U+798E` vs `楨 U+6968`; no reuse of historical coordinates (every live coordinate fresh-derived); Save All = 1, destination confirmation = 1, side-effecting ops = 1 (unless idempotent recovery is proven); durable intent before irreversible confirmation; no blind retry of an unknown irreversible dispatch; preserve attempt-07 and all historical evidence byte-identical; no push; no `__pycache__`/`*.pyc` additions; preserve staging.
- NON_GOALS: hidden LINE semantic-event inference as the primary success condition; fullscreen capture as primary localization source; frame-SHA as semantic identity proof; Foundation Models as production click authority; AX writes to ambiguous elements; claiming BACKUP_COMPLETE from weak signals.
- CRITICAL_PATH (smallest safe path): capability probe -> synthetic AppKit calibration (capture modes/occlusion, Vision localization, transform, Quartz routing, postcondition, AX chooser, focus theft) -> deterministic locators + one transform + state machine + risk classes + transaction policy -> seven pre-live topic reviews + adversarial review + barrier-supersession review on frozen SHAs -> single bounded live run -> filesystem/content verification -> report/ledger/commits.
- AUTONOMY ENVELOPE: autonomous research/SDK inspection/prototyping/tests/replay/plan revision/offline-failure repair; do not stop merely because a review returns REVISION_REQUIRED; do not ask the owner to choose between equivalent safe implementations; bounded live-state recovery <=3 cycles; 3 consecutive reviews on the same unresolved architectural dependency -> `BLOCKED_WITH_ROOT_CAUSE`; never weaken a safety invariant to obtain approval; human input reserved for genuinely external requirements.

## GOAL_ALIGNMENT
- [VERIFIED] The plan's `GOAL_CONTRACT` (plan lines ~24-36) reproduces the goal's primary outcome, the duplicate-content success route, the conditional single live run, and the no-human-intervention posture. No supporting tool/schema/field has been promoted into the de facto goal; the deliverables list mirrors the goal's FINAL DELIVERABLE list.
- Acceptance proves the outcome, not implementation completeness: `DEFINITION_OF_DONE` (a) requires the live run + `DUPLICATE_CONTENT_CONFIRMED` + baseline unchanged + no unexplained side effect; the plan's `STATUS_SEMANTICS_AND_CLOSURE_ROUTING` explicitly denies that a passed synthetic suite implies a live result, or that a live run without filesystem/content proof implies backup success.
- The `SAVE ALL` conservative choice (run under `IRREVERSIBLE_SIDE_EFFECT` semantics with exactly-one dispatch) is aligned: the goal requires empirical classification but permits `PRE_SIDE_EFFECT` only when PROVEN; the plan instead keeps exactly-once semantics and records the empirical classification from the run's evidence. This is strictly the safe direction and matches the authorization counters.
- The reconciliation-barrier treatment matches the goal: historical `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` is preserved (verified in `evidence/20260923-rev27d-save-all-reconciliation/semantic-classification.json`; barrier state `SAVE_ALL_RECONCILIATION_BARRIER_REMAINS` in `retry-policy.json`), superseded only by a NEW architecture + fresh scoped authorization, and gated by independent review 9 before any live dispatch.
- No goal-misalignment finding.

## NECESSITY_AND_TRACEABILITY
Every material requirement R1-R25 traces to explicit goal sections; classification audit:
- CORE (blocks the primary outcome or preserves a must-not-break invariant): R1 closed loop; R2 ScreenCaptureKit; R3 window identity; R4 Vision OCR rules; R5 structural locators; R8 Quartz actuator; R9 canonical transform; R10 synthetic harness; R11 AX plane; R12 activation/focus; R13 state machine; R14 risk classes; R15 Save All postcondition; R16 chooser/exactly-once destination; R17 filesystem completion; R18 transactional safety; R19 bounded autonomy; R20 reviews; R21 envelope; R22 success condition; R24 barrier supersession; R25 preservation/no-pycache/no-push.
- SUPPORTING with local degradation (verified by plan `DEGRADATION_AND_GATE_BEHAVIOR`): R6 registration/stability (falls back to deterministic-only comparison), R7 Foundation Models diagnostics, R23 deliverable bundle (no gate on the live outcome).
- Traceability spot-audit: closed-loop wording -> R1; `SCContentFilter(desktopIndependentWindow:)` -> R2; identity binding fields -> R3; OCR exactness `禎/楨` -> R4; ported v6/v7/v8 invariants -> R5; registration/feature prints -> R6; FM limits -> R7; `CGPreflightPostEventAccess`/`CGRequestPostEventAccess` + mouseMoved/revalidate/down/up -> R8; explicit transform record -> R9; harness proof list -> R10; AX ambiguity refusal -> R11; activation verification + focus theft -> R12; APP_READY..FINALIZED -> R13; three risk classes -> R14; bounded high-frequency postcondition -> R15; AX-first chooser + durable intent + staging preconditions -> R16; 57 files/decodable/stable/quiescence/multiset -> R17; ledger + single dispatch + no blind retry -> R18; <=3 recoveries + 3-review blocked threshold -> R19; seven reviews + adversarial -> R20; counters/envelope -> R21; success condition language -> R22; deliverable list -> R23; barrier -> R24; preservation constraints -> R25.
- No untraceable material work found. Two sub-elements are implementation conveniences rather than requirements: `rev28ctl` orchestrator and `DiagnosticHooks`; both are delivery vehicles for mandated behavior (probe/harness/live orchestration, diagnostics-only FM usage) and are cheap - acceptable.
- R19 classified CORE (goal's BOUNDED AUTONOMY section imposes must-not-break process invariants: no invariant weakening, no infinite loops) and R25 CORE (goal's preservation constraints are must-not-break evidence-integrity constraints). Both classifications carry an explicit rationale in this review; neither is "CORE only because it gates closure".
- Minor traceability gap: the goal's VISUAL STABILITY list explicitly includes "rectangle tracking"; R6's evaluation scope names registration/feature-print similarity (and the capability matrix names rectangle detection) but not tracking - see RV-07.

## GATE_AND_VETO_AUDIT
Global gates and their justification:
1. Capability probe PASS / harness calibration PASS / replay complete / adversarial suite PASS (plan `LIVE_RUN_ENVELOPE` a-d). Justified: they are the only pre-live proof that capture semantics, transforms, event routing and fail-closed detection behave as claimed on THIS machine (anchors drift; historical coordinates invalid).
2. Seven topic reviews + adversarial review + barrier-supersession review APPROVED on frozen SHAs (goal REVIEWS section; plan review 1-9). Justified and mandated verbatim by the goal.
3. Save All direct-postcondition requirement (`SAVE_ALL_POSTCONDITION_CONFIRMED` only via directly observed chooser; logs/panel-service/menu/click-return are supporting only). Justified: this is the goal's core architectural inversion (observable closed loop) - the primary decision (did the one irreversible dispatch activate the intended action?) is undefined without it.
4. Chooser identity verification before any chooser action; exactly-once confirmation with durable intent. Justified: prevents wrong-process/wrong-surface irreversible writes.
5. Staging preconditions (inside approved root, canonicalized, fresh unique run, empty at start, not baseline, no symlink escape) + baseline-unchanged abort. Justified: must-not-break data invariant.
6. Live preflight (LINE launchable, baseline unchanged, staging created empty, ledger armed, TCC re-verified). Justified: stale planning evidence is insufficient for an irreversible step.
Proportionality checks:
- No SUPPORTING/BEST_EFFORT element holds a global veto: FM, registration, and AX-chooser path all degrade locally; the AX-chooser fallback failure stops only at `CHOOSER_VERIFIED` with zero confirmation (scoped, and the confirmation budget is NOT consumed).
- The postcondition gate's failure is scoped (one run ends indeterminate); it does not disable unrelated work, which continues under bounded autonomy.
- Waivers: the plan declares "none available to the agent" - i.e. `WAIVER_AUTHORITY: NONE` for the agent, so self-waiver is impossible; the owner retains default authority. No gate is waivable by the implementing agent.
- "Ordering rule" (plan CRITICAL_PATH): only the irreversible production step has a hard prerequisite chain - consistent with v4.2 (do not let supporting completeness block unrelated steps).
v4.2 status-contract checks (required by this review template):
- canonical incident (core fixed, closure pending): the plan's status section separates PRIMARY_OUTCOME / IMPLEMENTATION / CORE_ACCEPTANCE / REQUIRED_VERIFICATION / INDEPENDENT_ACCEPTANCE / TASK_CLOSURE as subjects and forbids substituting one for another; wording hardening recommended (RV-02).
- true implementation blocker: `IMPLEMENTATION_BLOCKED` explicitly reserved for unfinished product implementation (plan STATUS_SEMANTICS section; R19).
- CORE fail/blocked/not-run/not-required: not enumerated per state in the plan text; the plan binds Stage 05 to verify CORE acceptance first and defers closeout routing to the canonical contract - see RV-08 (schema/field assignment).
- replan: repair->re-review loop and no-invariant-weakening rule stated; semantic-change escalation remains governed by the global harness rules.
- baseline unavailable / baseline-delta / hard-clean debt: no broad repository-wide gate exists in this plan (its gates are bespoke and its baselines are defined: baseline digest, staging inventory, preflight); nothing requires guessing a missing baseline. Repository-health constraints (R25) are hard must-not-break constraints with explicit evidence-integrity rationale, not closure convenience.
- formal waiver with original result preserved: no agent waivers possible; §7.5 preserved-result rule untouched.
- independent acceptance pending / environment block / product defect: DoD (b) + Stage 05 section cover the honest-terminal cases; routing deferred to §7.8 (RV-02 wording).
- contradictory-state rejection / legacy normalization: this task creates no legacy terminal schema and rewrites no historical values (DO_NOT_TOUCH list verified against attempt-07 / Rev27d artifacts, which remain unchanged on disk).
- DONE prerequisites: DoD enumerates frozen-SHA reviews, manifest, replay, adversarial results, ledger, handoff, local commits, closeout audit per the v4.2 contract; no `DONE` path exists without the live proof.
No unjustified global gate found.

## COUPLING_AND_FAILURE_CONTAINMENT
- Independent signals are not collapsed into one all-or-nothing flag: identity is a cross-checked set (bundle, pid + process start time, windowID, frame, AX role/title, CG list, capture epoch/SHA) with explicit invalidation rules; frames fail closed on bbox invariants; OCR identity vs click geometry are separated.
- Optional failures are contained at the narrowest boundary: FM diagnostics (diagnostic only), registration (deterministic fallback), AX chooser (reviewed keyboard path or zero-confirmation stop), replay divergences (recorded + hypothesized, never threshold-tweaked into agreement).
- Irreversible failure containment: side effects are confined to a fresh staging directory inside the approved root; baseline and historical evidence are read-only; tripwire watches staging + `~/Downloads`; unexpected writes abort; no blind retry; crash resume is observe-only.
- The chooser confirmation budget is not consumed on identity refusal or AX inability (stop before confirmation) - good containment.
- One coupling to keep explicit: the chooser detector's dependence on the panel-service process set (RV-04). As written, an over-tight or spoofable binding could false-negative a genuine chooser (ending the run without success) or false-positive a look-alike; the plan's own fake-chooser-fixture + reviews 4/6 are the containment, but the plan text should pin the set semantics.

## DESIGN_ECONOMY
- Deletion test on major elements: the state machine, ledger, risk classes, staging verifier, postcondition monitor, and the reviews each map directly to explicit goal sentences; removing any would fail a named acceptance or must-not-break obligation. The synthetic harness and replay are the goal's mandated proofs. No obvious removable component.
- Simplification choices are already made: ONE actuator code path (no window-relative abstraction), ONE canonical transform with type-level space separation, deterministic pure cores + thin OS edges behind protocols, atomic appends, single evidence root.
- The goal itself mandates the breadth (architecture doc, capability matrix, engine, harness, tests, replay, adversarial suite, review artifacts, manifests, ledger, handoff, commits); the plan does not visibly exceed it. Minor redundancy noted in residual notes (dual OCR wrapper parity testing).
- Complexity is concentrated at stable boundaries (sensor/actuator/chooser edges), not scattered; complexity budget verdict: acceptable.

## CRITICAL_PATH_AND_PRIORITY
- Waves W1->W7 fix and prove the CORE path first (capability/transform/identity -> harness -> locators/replay -> policy/state/ledger/verifier -> adversarial hardening -> conditional live run -> verification/closeout); SUPPORTING documentation sits in W6 near the end and does not displace core proof.
- The plan explicitly prevents local blockers from stalling unrelated steps ("any step that cannot proceed does NOT block unrelated steps; only the irreversible production step has a hard prerequisite chain").
- Review apparatus (9 gates) is goal-mandated, not noise capture; repair loops are bounded by the 3-cycle blocker rule and the no-weakening rule.
- Watch item (not inversion): the live run is the FIRST engagement with the real LINE surface; the plan's open LINE-specific capability questions are resolved there via reversible navigation before the single Save All - see RV-03.

## REQUIREMENT_FIDELITY
Coverage of the goal's key clauses (plan section -> status):
- Closed-loop primary acknowledgement (no click-return/menu/log inference): R1, §10 - covered.
- ScreenCaptureKit survey + `desktopIndependentWindow` preference + no fullscreen primary localization: R2, §1 - covered (fullscreen only corroboration/occlusion/actuation verification).
- Window identity binding + stale windowID invalidation + cross-checks: R3, §2 - covered.
- Vision OCR settings (accurate, zh-Hant + en-US, correction off), exact 禎/楨, identity/geometry separation, no raw-character-box clicks: R4, §3 - covered.
- Structural locators incl. `57張照片`, ellipsis, `儲存全部`, chooser; ported v6/v7/v8 invariants: R5, §3 - covered (v8 invariants spot-verified in tool source: `MIN_OVERLAP_PX=20`, `X_EDGE_PX=2`, `EDGE_MIN/FRACTION=6/0.15`, `NEIGHBOR_SEP_PX=12`, non-target substitution tolerance = 1, reference order `選擇項目/修改相簿名稱/儲存全部/刪除相簿/分享相簿`).
- Visual stability evaluation (registration/rectangles/feature prints/tracking): R6 - partial (tracking not named) -> RV-07.
- Foundation Models limits: R7, §4 - covered.
- Quartz actuator (preflight/request, mouseMoved+revalidate+down/up, screen-global, dispatch record): R8, §5 - covered.
- One canonical transform + explicit transform record + no implicit 2x: R9, COORDINATE_TRANSFORM_MODEL - covered (five invariants incl. bbox check + 1pt boundary refusal).
- Synthetic calibration proofs (occlusion, stable coordinates, Retina, child/popup, Quartz routing to topmost popup, postcondition, AX chooser, focus theft): R10, SYNTHETIC_HARNESS_CALIBRATION_PLAN - covered.
- AX plane semantics + ambiguity refusal: R11, §6 - covered.
- Activation/focus handling with verification and theft recovery: R12, §7 - covered.
- Persistent state machine with the goal's state list + per-transition {precondition, action, postcondition, timeout, recovery, evidence}: R13, §8 - covered.
- Risk classes incl. empirical Save All classification policy: R14, §9 - covered (conservative exactly-once choice, run evidence settles empirical class).
- Save All postcondition incl. tripwire + no blind retry: R15, §10 - covered (window bound noted in RV-01).
- Chooser AX-first + fresh identity + staging preconditions + exactly-once durable intent + keyboard/Go-to-Folder after verification: R16, §11 - covered.
- Filesystem completion (57, no subdirs/partials/zero-byte, decodable, stability, quiescence, manifest + multiset vs baseline): R17, §12 - covered (mismatch verdict undefined -> RV-05).
- Transactional safety (durable intent, single dispatch, append-only hash-chained ledger, observe-only resume): R18, §13 - covered.
- Bounded autonomy + blocked threshold + no invariant weakening: R19 - covered.
- Reviews (7 topics + adversarial, frozen SHAs): R20, REVIEW_PLAN - covered.
- Authorization envelope (counters, no historical coordinates, abort conditions): R21, LIVE_RUN_ENVELOPE - covered.
- Success condition incl. `DUPLICATE_CONTENT_CONFIRMED`, baseline unchanged, no unexplained side effect, forbidden weak claims: R22 - covered.
- Deliverables incl. live evidence conditional, manifests, ledger, handoff, local commits: R23, DELIVERABLES_MAP - covered.
- Barrier supersession reviewed before any new Save All: R24, RECONCILIATION_BARRIER_SUPERSESSION - covered.
- Preservation/no-pycache/no-push: R25, CONSTRAINTS + CHANGE_MAP - covered.
- Bounded/autonomous operation and "do not ask owner for solvable problems": RISKS item 5 + autonomy posture - covered.
No out-of-scope requirement additions found; no missing goal requirement besides RV-07's evaluation-list nuance.

## GROUNDING_AND_DRIFT
Independently re-verified this review (read-only):
- [VERIFIED] HEAD = origin/master = `766b22c4f8bf29b9d0a46049c75309c70593d66d`, ahead 0; no tracked modifications; only untracked Rev27e WIP/evidence/task dir (matches plan's anchor statement).
- [VERIFIED] Issue SHA-256 matches expected (plan's claim).
- [VERIFIED] Baseline digest + 57 files + 17,924,900 bytes recomputed = MATCH (plan's claim, including the stated digest method).
- [VERIFIED] Staging run dir exists, empty, sole child of `staging/`; plan's PRESERVE statement consistent.
- [VERIFIED] Capability probe evidence (`evidence/20260925-rev28-native-closed-loop/capability-probe/probe-metadata.json` + `probe-outputs.txt`): macOS 27.0 (26A428); Swift 6.3.3; SDK path `MacOSX26.5.sdk` (re-checked live: `xcode-select -p` -> Xcode.app, `xcrun --sdk macosx --show-sdk-path` -> MacOSX26.5.sdk); `CGPreflightScreenCaptureAccess=true`, `CGPreflightPostEventAccess=true`, `AXIsProcessTrusted=true`; `contentRect == window frame` and `pointPixelScale=2.0` in probe output; `includeChildWindows=false` -> 2294x1366 = 1147x683 pt x2; `includeChildWindows=true` -> 2294x1438 (union with child titlebar y=26..94); `captureImage` default 1920x1080; CGS_REQUIRE_INIT crash without NSApplication recorded; single display 1147x745 @2.
- [VERIFIED] LINE 26.0.2 build 3828 installed; not running now (plan's probe claim).
- [VERIFIED] v8 locator invariants cited in the plan exist in `evidence/20260916-route/tools/v8/locate_save_all_menu_item.py` (constants and reference order as cited).
- [VERIFIED] Historical success `RUN-20260907-154331-01` (Save All -> folder chooser -> Go to Folder -> one confirmation -> 0/57 download) and the failure precedents (miss; returned-without-chooser; wrong-row Rename) are grounded in `evidence/20260923-rev27d-save-all-reconciliation/historical-success-comparison.json`.
- [VERIFIED] Attempt-07 classification `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` and barrier state remain as the plan states; try-again budget historically consumed (historical_save_all_budget 1/1).
- [VERIFIED] Historical window geometry claim ([HISTORICAL] 327x643 @ (0,33); detail window [211,29]) is present in attempt-14/AX evidence; explicitly marked historical/non-reusable by the plan.
- Drift assessment: plan authored under the same anchor it states; no stale anchor detected at review time. Minor historical label typo noted in RESIDUAL_MINOR_NOTES.

## ARCHITECTURE_AND_CONTRACTS
- Module/boundary design is coherent (Sensor / Identity / Perception / Actuation / AX / Postcondition / Chooser / State / Transaction / Verify / Risk / Diagnostics + probe/harness/ctl), with pure deterministic cores and thin OS edges - testable offline and substitutable in the harness.
- Coordinate transform contract: explicit spaces (window-local pt, screen-global pt, capture px), explicit transform record (window origin, content rect, content scale/backing scale, capture dims), five checked invariants (bbox px == round(bbox pt x S); B == W when children excluded; same-epoch derivation; no implicit 2x; 1pt boundary refusal). The probe's `contentRect == frame` + scale 2.0 supports the main-window path; the union-bbox rule covers child/popup captures. Sound.
- Sensor contract handles all three LINE popup possibilities (separate SCWindow / child window / drawn in-window) with recorded inclusion sets and fail-closed bbox checks - matches the goal's "captures or independently identifies popup/child windows".
- Actuation contract: one code path, screen-global points, fresh revalidation after mouseMoved and before down/up, full dispatch record - matches goal. The topmost-hit behavior is proven in the harness (popup above main window + occluder).
- Identity contract: perception bound to epoch; pre-dispatch re-enumeration; windowID change invalidates - matches goal's "stale or replaced windowID invalidates".
- Postcondition/chooser contract: direct observation standard; panel-service-bound identity + corroborating inventories; fake-surface refusal; durable intent before confirmation; exactly-once - matches goal, with the identity-set semantics noted in RV-04.
- Ledger/state contract: hash-chained append-only JSONL; atomic state persistence; observe-only resume after crash; no irreversible re-dispatch without a fresh reviewed decision - matches goal's transactional safety.
- No contract conflicts with the v4.2 status contract were found (no new terminal schema; subjects kept orthogonal; closeout defers to §7; wording item RV-02).

## DATA_SECURITY_RELIABILITY
- Data: captures/AX reads of the owner's private LINE album are inherent to the goal and are stored only in the local evidence tree; no push and no network egress are part of the plan; baseline/staging/attempt-07 are read-only inputs; tripwire is observation-only.
- Trust boundaries: LINE-internal signals and panel-service presence are demoted to supporting/forensic evidence; only direct observation authorizes the chooser path; AX writes only on uniquely identified elements; Foundation Models output never has actuation authority.
- Permissions: TCC grants are used as-is (screen capture / post-event / accessibility), re-verified in live preflight; no request/persistence beyond `CGRequestPostEventAccess` if needed.
- Reliability: bounded timeouts + bounded recovery + terminal scoped states; no blind retry; deterministic suites must be semantically equal across two runs; crash resume observe-only; single-display constraint fails closed.
- Residual: the exactly-once live dispatch cannot be undone; containment is by construction (fresh staging dir; read-only baseline). No unexplained-side-effect tolerance: tripwire + abort.

## IMPLEMENTATION_SEQUENCE
- W1..W5 build and prove CORE offline; W6 supporting docs; W7 conditional live run, then filesystem/content verification and commits. Dependencies are explicit and match the goal's "capability + harness first" rule.
- Pre-live review loop (repair -> re-review, frozen SHAs, no invariant weakening; 3-consecutive same-dependency rule -> BLOCKED_WITH_ROOT_CAUSE) satisfies the goal's review and bounded-autonomy constraints.
- The sequence preserves "smallest complete change": CHANGE_MAP adds only `rev28/**`, the new evidence root, this task dir, and one `.gitignore` line; everything else is untouched.
- The live run consumes its counters exactly as the envelope states (Save All 1; confirmation 1; destination 1; irreversible side-effecting 1; ellipsis recovery <=3 within the reversible-navigation policy). The "ellipsis open = 1 (recovery <=3 within policy)" phrasing is slightly terse but consistent with the goal's reversible-navigation budget.

## TESTABILITY_AND_ACCEPTANCE
- Each layer has an observable acceptance instrument: unit tests for geometry/identity/locators/verifier/ledger/risk/state; harness scenarios with SHA-bound bundles; offline replay; live ledger + captures + AX reads + manifest + content comparison; Stage 05 CORE-first independent acceptance.
- Fail-closed behavior is testable: ambiguity refusal, stale-ID invalidation, wrong-scale detection, fake chooser refusal, postcondition timeout, duplicate/partial/zero-byte detection, focus theft, wrong-row/outside-click scenarios.
- Goal-mandated adversarial coverage is enumerated and matches the goal's list (count-label inconsistency -> RV-06). Determinism requirement (semantic equality across two runs) is stated.
- Status/verification planning: the plan does not assign the §7.3 field set (CHECK_ID / GOAL_CRITICALITY / EVIDENCE_ROLE / CLOSURE_GATE / BASELINE_REQUIRED / FAILURE_CLASSIFICATION_RULE / WAIVER_ALLOWED / WAIVER_AUTHORITY / CHECK_RESULT / WAIVER_STATUS) to its material checks, and does not restate broad-gate policy - no broad repo-wide gates are planned, so the obligation should be satisfied in the Stage 04/05 artifacts (RV-08).
- Two acceptance verdicts need explicit text before the live-run gate: the postcondition window/late-sample semantics (RV-01) and the content-mismatch verdict if 57 stable files arrive but the multiset differs from the baseline (RV-05).
- Stage 05 cannot pass by re-running weak checks: the plan requires the direct live evidence chain; synthetic success is explicitly non-transferable.

## SCOPE_AND_COMPLEXITY
- Scope is the goal's scope: new `rev28/` Swift package + new evidence root + this task dir (+ one `.gitignore` line). No historical artifact, tool, staging dir, baseline, or WIP file is modified. DO_NOT_TOUCH list is comprehensive and matches the goal's preservation constraints.
- Complexity is justified element-by-element (see DESIGN_ECONOMY); no hypothetical-future features detected; no dependency additions beyond system frameworks.
- Residual scope notes: dual OCR wrapper parity testing is slight redundancy; the "23" scenario label is off (matrix enumerates 25: 22 goal-named + 3 extensions) - documentation-level.

## FINDINGS
All findings below are MINOR (non-blocking); no BLOCKER/MAJOR was found.

- ID: RV-01
  - Severity: MINOR
  - Category: TEST
  - Affected plan section: `### 10. Save All postcondition` (R15); RISKS item 4
  - Evidence: plan text: "bounded high-frequency observation window (cadence <=150 ms, total <=8.0 s, plus one late sample at ~12 s for the ledger only)"; "No affirmative within the window -> NO_CHOOSER_OBSERVED -> scoped indeterminate; no retry (budget consumed)". No LINE chooser-latency datum exists in the retained evidence (attempt-07 had no chooser; the 2026-09-07 success did not record chooser latency) - [UNVERIFIED] that <=8.0 s is sufficient on this LINE/macOS combination.
  - Failure/rework mechanism: if a genuine chooser (or an equally valid reviewed resulting surface) appears only after >8.0 s, the single Save All budget is consumed and the run ends indeterminate even though the route worked; the late sample at ~12 s is explicitly not verdict-eligible, so this known case would still be classified NO_CHOOSER_OBSERVED.
  - Smallest required correction: before the live-run gate, either (a) evidence-justify the 8.0 s bound from pre-live calibration (harness-measured panel appearance latency + any historical datum) and document it in the postcondition model reviewed by review 4, or (b) give the late sample the identical direct-observation standard (same identity binding), so a directly observed chooser within a still-bounded window (e.g. <=15 s) also yields SAVE_ALL_POSTCONDITION_CONFIRMED; keep the no-retry rule unchanged.

- ID: RV-02
  - Severity: MINOR
  - Category: SEMANTIC_CONTRACT (status semantics)
  - Affected plan section: `## DEFINITION_OF_DONE`; `## STATUS_SEMANTICS_AND_CLOSURE_ROUTING`
  - Evidence: DoD's first sentence defines "Primary outcome" as "(a) completes the live run and proves DUPLICATE_CONTENT_CONFIRMED ... or (b) reaches a scoped, honestly-reported terminal state". v4.2 (§7.10) reserves `TASK_CLOSURE_STATUS: DONE` for primary outcome ACHIEVED (or an explicitly plan-defined equivalent closure condition); a scoped indeterminate is NOT achieved.
  - Failure/rework mechanism: a closeout reader could treat case (b) as "Done" (the section is titled DEFINITION_OF_DONE) and mislabel closure while the primary outcome is NOT_ACHIEVED; the plan's own status section mostly guards this but the wording invites contradiction with §7.7/§7.10 legal-state rules.
  - Smallest required correction: reword to separate "accepted terminal states for the task" from "closure/Done": state explicitly that in case (b) `PRIMARY_OUTCOME_STATUS` is NOT_ACHIEVED/UNKNOWN and `TASK_CLOSURE_STATUS` follows §7.7/§7.8 routing (e.g. CORE_ACCEPTANCE_BLOCKED / ACCEPTANCE_BLOCKED / PENDING_* as applicable) and will not be DONE unless the §7.10 conditions including primary-outcome achievement are met.

- ID: RV-03
  - Severity: MINOR
  - Category: GROUNDING (verification attribution)
  - Affected plan section: `## ENVIRONMENT_AND_CAPABILITY_MATRIX` open questions; `## IMPLEMENTATION_WAVES` W7; LIVE_RUN_ENVELOPE
  - Evidence: the plan labels LINE-specific unknowns ("popup as separate SCWindow/child/in-window", "whether AX exposes the album ellipsis / popup / Save All rows", "AX surface of the native folder chooser") as "CORE gates for the harness", but the synthetic AppKit harness cannot prove LINE-specific behavior; no explicit pre-live fresh read-only LINE reconnaissance step is scheduled (live preflight only checks launchability/baseline/staging/ledger/TCC).
  - Failure/rework mechanism: the first real LINE observation happens inside the one-shot live run; if a LINE-specific branch (e.g. popup as separate window) is mis-modeled, the run aborts before Save All (reversible states, bounded), but the reconnaissance cost lands inside the only authorized production run.
  - Smallest required correction: state each open question's resolving evidence class (synthetic harness proof vs fresh read-only LINE observation) and add an explicit read-only LINE reconnaissance step to the live-run envelope's early states (navigation is reversible and the plan already budgets ellipsis recovery <=3), with zero side effects until SAVE_ALL_LOCATED.

- ID: RV-04
  - Severity: MINOR
  - Category: TEST (postcondition/chooser identity)
  - Affected plan section: `### 10. Save All postcondition`; `### 11. Chooser automation`
  - Evidence: "AX sheet/window bound to the panel-service process whose identity is established by the fresh census + timing"; "panel ownership pid in the freshly established panel-service set". The census timing semantics (pre- vs post-dispatch, empty-set case), instance authentication (bundle ID / code signature), and pid-reuse protection are not pinned down; the look-alike refusal is delegated to the harness fixture.
  - Failure/rework mechanism: an over-tight binding can false-negative the genuine macOS 27 chooser (ending the run without success) while an under-specified binding could accept a look-alike drawn by another process - both are material on the single irreversible run.
  - Smallest required correction: define the panel-service identity set semantics explicitly (what the pre-dispatch census contains; how a post-dispatch instance is authenticated, e.g. bundle identifier / signing identity; pid-reuse handling) and calibrate the detector against the real macOS 27 panel implementation (the harness's real NSOpenPanel) in review 4/6's frozen model.

- ID: RV-05
  - Severity: MINOR
  - Category: TEST (acceptance verdict completeness)
  - Affected plan section: `### 12. Filesystem completion`; DEFINITION_OF_DONE
  - Evidence: the plan defines `Equal multiset -> DUPLICATE_CONTENT_CONFIRMED (success)` but defines no verdict/terminal state for the plausible case "exactly 57 files arrived, stable and decodable, but content multiset != baseline" (e.g. album legitimately changed since the baseline, or route-level content defect). DoD (a) requires duplicate equality; no mismatch class is named.
  - Failure/rework mechanism: an implementer facing a mismatch must improvise a terminal label/verdict, which the harness rules treat as a semantic change; conversely, an improvised "success" label would violate the goal's no-weak-claims rule.
  - Smallest required correction: add an explicit non-success terminal class (e.g. CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE -> scoped terminal + forensic report; no accepted-copy creation; owner-visible explanation) and require it to distinguish "route defect" vs "album changed since baseline" evidence before any further action.

- ID: RV-06
  - Severity: MINOR
  - Category: SCOPE (documentation consistency of a review-bound artifact)
  - Affected plan section: R20; CRITICAL_PATH step 4; ADVERSARIAL_TEST_MATRIX
  - Evidence: the goal names 22 adversarial scenarios; the matrix enumerates those 22 plus 3 extensions (stale AX after re-layout; popup in-window vs separate window; event posted while target window is inactive) = 25, but the plan says "23-scenario matrix" (CRITICAL_PATH) and "adversarial review of 23 named scenarios" (R20).
  - Failure/rework mechanism: review 8 (adversarial results) and Stage 05 acceptance bind coverage claims to this count; an ambiguous count weakens the auditability of "all named scenarios covered".
  - Smallest required correction: fix the labels to the actual matrix size (e.g. "22 goal-mandated + 3 planned extensions = 25") or enumerate the canonical scenario IDs in one numbered list that reviews bind to.

- ID: RV-07
  - Severity: MINOR
  - Category: REQUIREMENT_FIDELITY
  - Affected plan section: R6; ENVIRONMENT_AND_CAPABILITY_MATRIX (Vision row)
  - Evidence: goal's VISUAL STABILITY / REGISTRATION section asks to evaluate "image registration, rectangle detection, rectangle tracking, feature-print similarity"; R6 and the matrix name registration, rectangle detection, and feature prints but not rectangle tracking (nor an explicit rationale for omission).
  - Failure/rework mechanism: an evaluation-only deliverable (SUPPORTING) would be slightly narrower than the goal's named evaluation list, weakening traceability of the stability work; low functional impact.
  - Smallest required correction: add rectangle-tracking evaluation (or a one-line documented rationale for its omission) to R6's evaluation scope and the capability matrix.

- ID: RV-08
  - Severity: MINOR
  - Category: TEST (v4.2 verification planning schema)
  - Affected plan section: `## VERIFICATION_AND_ACCEPTANCE`; `## DEGRADATION_AND_GATE_BEHAVIOR`
  - Evidence: workflow-routing §7.3 requires every material verification item to declare EVIDENCE_ROLE and CLOSURE_GATE (plus BASELINE_REQUIRED, FAILURE_CLASSIFICATION_RULE, WAIVER_ALLOWED/AUTHORITY, CHECK_RESULT, WAIVER_STATUS); the plan lists checks and classes but does not assign these fields, and does not state the broad-gate policy class (which is effectively N/A here since no broad repo-wide gate is planned).
  - Failure/rework mechanism: downstream execution/acceptance artifacts could under-declare closure gating (e.g. treating a SUPPORTING item as blocking, or vice versa), creating avoidable status-contract churn at closeout.
  - Smallest required correction: add a compact check table (or commit to producing it in `execution.md`) assigning the §7.3 fields per material check, with the explicit statement: no broad repository-wide gates; all planned checks bespoke; agent waivers not allowed; BASELINE_DELTA not used.

## REQUIRED_PLAN_CHANGES
None. No BLOCKER or MAJOR finding exists, so approval is not conditioned on any plan edit; FINAL_STATUS binds to PLAN_REVISION 1 / SHA-256 `5575aca5f2c8ededa3f76ff79baf6b82eecd25353457b709982eb05e6cbcbbb9` (any later plan edit requires a fresh review when review is required).

Recommended (non-blocking) fold-in points:
- Resolve RV-01, RV-04, RV-05, RV-08 in the pre-live review inputs (reviews 4 and 6 for the postcondition/chooser model; the Stage 04 execution template for the §7.3 fields) so the acceptance verdict text is pinned before the live-run gate.
- Fold RV-02, RV-03, RV-06, RV-07 into the next natural plan touch or the Stage 03 handoff notes.

## RESIDUAL_MINOR_NOTES
- Historical label typo: plan VERIFIED_REPOSITORY_FACTS cites "returned-without-chooser (2025-09-08 ...)"; the evidence run ID is `RUN-20260908-124357-01` (2026-09-08). Historical label only; no behavioral impact.
- Recovery-budget interplay: `REVERSIBLE_NAVIGATION` grants <=3 recovery attempts per identical blocker, while abort conditions stop at "two consecutive failed revalidations of the same candidate". The stricter abort threshold is safe, but the plan should state explicitly that this is the deliberate cap interaction (revalidation failures are not the same class as navigation blockers).
- Dual OCR wrapper ("RecognizeTextRequest" + "VNRecognizeTextRequest" parity) is slight redundancy; keep only if the parity evidence adds real value to review 1.
- Snapshot note: `review/attempt-01/plan_snapshot.md` pre-existed with bytes identical to the canonical plan; it was re-verified byte-identical (same SHA-256) before and after this report; no evidence lost or rewritten.
- Multi-display behavior remains [UNVERIFIED] on this single-display machine and is correctly fail-closed; adversarial scenario present.
- LINE-specific surface facts remain [UNVERIFIED] until first live observation (covered by RV-03); design branches accommodate all three popup-kinds so this is a residual risk, not a plan defect.
- Attempt-07 barrier artifacts and Rev27d reconciliation evidence were observed unchanged on disk during this review (read-only spot checks); no modification by this reviewer.

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Stage 03 Handoff for this exact revision (PLAN_REVISION 1, SHA-256 5575aca5f2c8ededa3f76ff79baf6b82eecd25353457b709982eb05e6cbcbbb9); carry RV-01/RV-04/RV-05/RV-08 forward as pre-live review inputs, not as execution blockers.
