# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 29 (parallel independent review; attempt-28 not read)
- REVIEWED_PLAN_REVISION: 20
- REVIEWED_PLAN_SHA256: 4919d87148c68ea3d70cbb9abd258edbd0bfa0b55be5123f7202251e557db17c (1,744 lines / 233,123 bytes; recomputed from plan.md before any other read; identical to the task-provided hash)
- PLAN_SNAPSHOT_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-29/plan_snapshot.md (copied byte-for-byte; snapshot SHA-256 re-verified = 4919d871…)
- Repository anchor observed: HEAD 72d6ed02cf2a2bdaedb1c202d47bf85ec2226a85; worktree clean apart from untracked `review/attempt-28/` and `review/attempt-29/`
- Reviewer runtime/model: fresh Codex CLI Stage-02 session (independent context; model identity not exposed to this session)
- Read-only honored: no product code/CLI/GUI execution; no formal config/state/run-log/photo access; no plan.md edit; no commit; writes only inside attempt-29 (plan_snapshot.md, review_report.md)

## OWNER_VERDICT
（白話）目標不變：證明 Downloads 裡那 57 張確實對應「旻謙允禎成長日記 / 2024/05/13～05/17」，並讓可重用的備份流程被真實驗證。這次 Rev20 只加一件事：依你 16:00/16:01 的更正，重做一次「先進入相簿、再點相簿內部的 ⋮」的唯讀觀察，全程只送兩個輸入（各一次、不重試、不點任何選單項目、不按鍵盤、不寫任何設定/狀態），最壞情況只是畫面上多開一個選單。其餘（照片、正式資料、可重用程式）都不會被改到。若這次觀察成功，剩下的就是結案前的獨立驗收；若不成功，路線仍列為卡點，由你決定要「標記為不需要」或再開新修訂。審查結論：授權解讀合理、防護完整、可安全執行；僅發現幾處不影響安全與驗收的舊文字殘留（見 findings），不需再修計畫即可交付 Handoff。

## GOAL_BASELINE
Independent baseline reconstructed from the authoritative owner sources before adopting the Plan's framing:
1. Owner goal (standing): safely establish whether the existing 57-file destination corresponds to the exact LINE source — group 旻謙允禎成長日記, album 2024/05/13～05/17, 57 images — and leave the reusable automation path proven through the real operator entry; no photo/formal-state mutation; no silent re-download (PRIMARY_OUTCOME, plan.md:1288-1294).
2. Owner decision 2 (transcript line 5091, 2026-09-17T14:59:40.847+0800, verbatim 「1.可以 / 2.要，授權給你」): re-author a format-correct confirmation record (part 1) and continue the automatic-menu route with one further ⋮ observation under a fresh gate.
3. Owner correction (transcript lines 6206 and 6224, 16:00:03.652 and 16:01:49.779+0800, verbatim): the screen seen after attempt-04 was the album *list*, not the album itself; the ⋮ must be reached *inside* the album; the click that landed was the album-list card's ⋮; the agent "should first click into" album 2024/0513~0517.
4. Route question being answered (frozen one-shot): does one authorized ⋮ input on the located control produce a machine-observable menu — observation only, never Save-All/menu-item/chooser/state write (plan.md:1604-1634; documented reference ui-procedure.md:118-128 "identify the album-level ellipsis; open its options menu once for observation only").
5. Must-not-break: 57 files and formal config/state/registry/run-log/photos stay read-only; 禎 U+798E / 楨 U+6968 never merged; no AXPress/AX-write/guessed coordinate/OCR-only acceptance; production Save-All stays outside every wave; status fields orthogonal (§7 status contract).

## GOAL_ALIGNMENT
- A1: Rev20's scope is exactly the owner-directed correction of the route leg; it does not touch the album-data result path, the R1–R7 product contract, the fixture matrix, or the status vocabulary. PRIMARY_OUTCOME and DONE criteria are unchanged (§20.5). [VERIFIED]
- A2: The two-input gate-3 reading (one album-card metadata click that opens the target album, then one album-level ⋮ click, observation only) is traceable to the owner's verbatim direction: line 6224 "你應該先點進去「2024/0513~0517」這本相簿" is an imperative to enter the album; line 6206 states the ⋮ exists only inside the album; line 5091's 「2.要，授權給你」 authorized continuation of the ⋮ observation. The alternative (narrower) reading is recorded honestly in §20.1 and a newer owner correction can supersede at any time. Interpretation is defensible and proportionate: no input class is added beyond the two directed ones, and the album-card click is a navigation precondition (documented ALBUM_CARD_OPEN primitive: "one bound metadata click", ui-procedure.md:63), not a side effect. [VERIFIED]
- A3: No element of Rev20 expands scope: no menu item, no Save All, no chooser, no keyboard, no state/config/run-log write, no product code/CLI change, no production download, no change to E2E_REQUIRED:NO (§20.5; route section 1604-1634). [VERIFIED]
- A4: The route remains properly classified: CORE (it decides whether the reusable Save-All route is provable) with a Plan-rationalized ROUTE_NOT_NEEDED exit only under §19.3's four preconditions plus, post-attempt-05, the owner's explicit decision (§20.3). [VERIFIED]

## NECESSITY_AND_TRACEABILITY
| §20 element | Trace | Class |
|---|---|---|
| gate-3 authorization record + verbatim messages/timestamps | owner lines 6206/6224 + standing 5091; recorded in evidence/20260916-route/attempt-05/gate-3-authorization.json | CORE (authority) |
| one album-card metadata input | owner "先點進去…這本相簿"; documented ALBUM_CARD_OPEN primitive | CORE |
| album-open verification (S5) before any ⋮ input | prevents spending the ⋮ one-shot on a wrong/unverified surface; fail-closed predecessor of the click | CORE (safety) |
| one album-level ⋮ input + immediate observation | the frozen route question (attempt-03/04 pattern; ui-procedure.md:118-128) | CORE |
| v3 tools (locate_album_card.py, verify_album_open.py, locate_album_ellipsis.py) | corrected route needs a fresh-frame card point, an album-open verdict, and an album-row band ⋮ census with group-title exclusion; v2 locator cannot serve the album-level control | CORE (minimal new moving parts) |
| reused detector + v2 locator (unchanged, SHAs recorded) | attempt-04 machinery reuse; v2 locator verdict corroborating only, never the click point | SUPPORTING |
| artifact set (route-result, run-ledger FINAL, manifest, execution-rev20.md, …) | matches approved attempt-03/04 evidence pattern and workflow-routing §7.11 | CORE (provenance) |
| §20.3 closure routing (AFFIRMATIVE / owner decision) | DONE clause + §16.8 revision rules + §19.3 rationale | CORE (decision authority) |
Nothing in §20 is untraceable; no requirement was removed or relaxed. [VERIFIED]

## GATE_AND_VETO_AUDIT
- CUA_ROUTE_DECISION remains CORE / OUTCOME / HARD_CLEAN / WAIVER_ALLOWED: NO / AUTHORITY: NONE (plan.md check table). Rev20 does not create a new global veto; it narrows, not widens, the closure paths.
- ROUTE_NOT_NEEDED is not a waiver: it is a Plan-rationalized NOT_REQUIRED determination with (post-attempt-05) the owner's explicit decision plus Stage-05 re-verification of §19.3's four preconditions and attempt-05's evidence. No agent can self-waive. [VERIFIED]
- AFFIRMATIVE closes the route blocker only for the corrected route and "authorizes no menu-item activation; production Save-All remains outside every wave" (§20.3). [VERIFIED]
- Non-AFFIRMATIVE keeps the route as a scoped CORE blocker and stops; neither closure branch runs automatically. [VERIFIED]
- Failure containment: the route failure cannot rewrite the independently proven implementation/CORE facts (status contract §7.8/§7.9 preserved by the plan's fixture table and closure text). [VERIFIED]

## COUPLING_AND_FAILURE_CONTAINMENT
- The corrected leg is isolated to the route observation; no product/formal-state coupling is introduced. Evidence stays under evidence/20260916-route/attempt-05/ plus /tmp frames with bytes/SHA-256 only (privacy fence preserved).
- S5's album-open verdict is the correct narrowing point: any NO_EFFECT / TARGET_MISMATCH / INCONCLUSIVE stops before the ⋮ input, so the worst case of a mis-targeted first click cannot chain into a menu-item action; a false-positive ALBUM_OPEN_VERIFIED can at worst lead to a second click on a ⋮-shaped control (menu opens/closes) — no path exists to a menu item, chooser, or state write. Worst-case effect is bounded to non-destructive UI effects (menu open, album/photo view). [VERIFIED]
- The pre-freeze requirement (gate-3 + v3 runbook + v3 tools, committed before any input) keeps tool drift from coupling into the run. [VERIFIED]
- Per-step abort verdicts are present and fail-closed: NO_TARGET_ON_FRAME (precondition 1/S3), PERMISSION_PROMPT_OBSERVED (S2), unsafe margins / readable non-57 / missing title (S3), NO_EFFECT / TARGET_MISMATCH / INCONCLUSIVE (S5), NO_ELLIPSIS_FOUND / AMBIGUOUS_ELLIPSIS / GROUP_LEVEL_ONLY (S6); "any deviation is SAFE_ABORT" (sequence preamble). [VERIFIED, with the enumeration gap in RV-29-3]
- AFFIRMATIVE cannot come from OCR-only or human-report-only evidence: §20.2 S10 requires a new AX menu element or the frozen detector's MENU_DETECTED; I re-read the frozen detector `evidence/20260916-route/tools/detect_menu_popup.py` (SHA 6ae9c250…) and confirmed it requires both a new geometry region (≥min-w/min-h/min-pixels) and ≥2 OCR strings, fails closed on OCR error, and never yields detection from OCR alone; §19.2's precedent records owner observations verbatim as supplementary, never part of route_status. [VERIFIED]

## DESIGN_ECONOMY
- Deletion test: removing the album-card input makes the corrected target unreachable (the owner states the album-level ⋮ exists only inside the album); removing S5 re-opens the mis-target chain; removing any of the three v3 tools removes a required fresh-frame point/verdict. Each §20 moving part pays rent.
- Reuse is maximal: attempt-04's detector and v2 card-⋮ locator are reused unchanged with recorded SHAs (6ae9c250…, 8c8b6fc7… — re-verified on disk); the ledger schema, manifest pattern, runbook pattern, /tmp frame handling and notification pattern are carried over.
- No hypothetical-future work, no new subsystem, no product-boundary change; the corrected run is one bounded experiment with a hard stop.

## CRITICAL_PATH_AND_PRIORITY
- The critical path remains: finish route question → close source-correspondence basis (already built as the v1.1 record) → independent acceptance (Stage 05 attempt-06) → closure. Rev20 sequences the corrected route first, exactly where the owner's correction points. [VERIFIED]
- No priority inversion: no supporting/best-effort work is gated or expanded; CORE route/source items lead; production Save-All stays deferred.
- One stale-literal issue sits in this section (RV-29-1/RV-29-2) but is non-gating (see FINDINGS).

## REQUIREMENT_FIDELITY
- Rev20 changes are confined to the route-observation leg and its literals; §20.5's "unchanged" list (goal contract, DONE criteria, R1–R7, cases 01–25, command grammar, read-only fences, one-human-gate pattern, three separately reported results, §18.x, Rev19 records/attempt-04 artifacts) matches what I verified in the body. [VERIFIED]
- All 11 CORE checks, the 19-row executable status fixture table, waiver rules, baseline rules, Stage-04/05 snapshot fields and blocker schema are untouched. [VERIFIED]
- No out-of-scope item was introduced by §20. [VERIFIED]

## GROUNDING_AND_DRIFT
- Plan hash verified before reading; snapshot pinned; no drift between the task-provided hash and disk.
- Evidence anchors verified on disk: attempt-04 route-result.json sha 6f71c5e7… (15,747 B) with `supplemental_owner_observations` recording the three owner messages; attempt-04 run-ledger.json = df0e9c446acf127c59c5827e4d50bc37a8be5e4cbc56722e7b61734866f19dd6 (matches §20.2 precondition 3's "df0e9c44…"); v1.1 record = a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263; frozen tool SHAs match execution-rev19.md.
- Documented reference checked: ui-procedure.md (sha 3a1bc29e…) already models the album-level ellipsis, the calibration item order (Select items / Rename album / Save All / Delete album / Share album — evidence to check against the observed menu, never permission to compute a row) and one bound metadata click for ALBUM_CARD_OPEN; §20.2 aligns with it. [VERIFIED]
- Drift found: stale literals at plan.md:1398, 1403, 1415 (RV-29-1/RV-29-2) — non-gating; see FINDINGS.

## ARCHITECTURE_AND_CONTRACTS
- No architecture/control-flow change: the run is a bounded CUA observation with a fresh ledger parented to attempt-04's final ledger, one-shot budgets (album_card_input_budget=1, ellipsis_input_budget=1, app_acquisition_input_budget=0, every other class 0), click_count=1 per input, zero retry, zero conversation images. [VERIFIED]
- The frozen verdict taxonomy (route_status ∈ AFFIRMATIVE/UNKNOWN/SAFE_ABORT with per-step reason codes) stays compatible with the approved route-result schema; the route section's "Historical coordinates and OCR-only evidence cannot yield AFFIRMATIVE" remains true under §20.2 S10. [VERIFIED]
- Status vocabulary: §20.3's expected AFFIRMATIVE tuple meets workflow-routing §7.10 (PRIMARY ACHIEVED, IMPLEMENTATION COMPLETE, CORE PASS, REQUIRED_VERIFICATION PASS, INDEPENDENT PASS, no blocker → DONE) and is explicitly "re-derived by Stage 05 attempt-06, never assumed"; the disclosed axis facts (Registry=FAIL, State=LEGACY_PROVENANCE_LIMITED, product Source=UNRESOLVED) are reported as axis facts, never promoted. [VERIFIED]
- Revision/approval rules honored: Rev20 is a GUI-budget/semantic change under Rev16 §16.8 → PLAN_REVISION incremented, prior approvals invalid for Rev20, this fresh independent review required. [VERIFIED]

## DATA_SECURITY_RELIABILITY
- Read-only fences intact: no state/config/run-log write, no AXPress/AXUIElementPerformAction/AX write, no keyboard, no menu item, no chooser, no re-download, no guessed/historical coordinate (every click point current-frame-derived by frozen tools). [VERIFIED]
- Privacy: frames stay in /tmp with bytes/size/SHA-256 recorded only; zero conversation images. [VERIFIED]
- Authority: gate-3 is a third independent one-shot gate; it neither resets nor extends gate-1/2 budgets; the owner's directive is recorded verbatim with provenance. [VERIFIED]
- Reliability: fail-closed abort semantics, at-most-once inputs, immediate owner notification on any non-AFFIRMATIVE outcome (S1/S3/S5/S6 + §20.3), menu left open only because every close mechanism (Escape/click) would itself be an unauthorized input — mitigated by immediate notification (see RV-29-5 residual note). [VERIFIED]

## IMPLEMENTATION_SEQUENCE
- Pre-freeze wave (gate-3 + v3 runbook + v3 tools + self-tests) → attempt-05 run (S1–S11) → artifact set + execution-rev20.md → Stage 05 attempt-06 re-derives closure per §20.3. Sequence is unambiguous; no step depends on a stale literal.
- One sequencing precision note: §20.2 precondition 2 should state explicitly that the v3 self-tests must have passed and their summary recorded before any input (mirroring §19.2's "frozen and self-tested before the click"); currently it says "with their frozen self-tests". RV-29-6 (MINOR).

## TESTABILITY_AND_ACCEPTANCE
- AFFIRMATIVE observability: machine-observable only (AX menu element or frozen detector MENU_DETECTED = new region + ≥2 transcribed strings); detector behavior independently re-verified from source; incomplete capture / OCR-only / human-only → UNKNOWN. [VERIFIED]
- Closure testability: §20.3's two branches have explicit evidence obligations; ROUTE_NOT_NEEDED requires owner decision + §19.3 preconditions + attempt-05 evidence; a further attempt requires a new revision/gate/review. [VERIFIED]
- v4.2 status fixtures: the 19-row executable table covers canonical pre-existing debt, true implementation blocker, CORE fail/blocked/not-run/not-required, replan, baseline unavailable, baseline delta (unchanged + worsened), hard-clean debt, formal waiver preserving the original CHECK_RESULT, independent-acceptance blocked/product defect, contradictory-state rejection, legacy normalization, and DONE prerequisites. [VERIFIED]
- Stage-05/Stage-04 contract: §7.8 snapshot fields and EXECUTION_ARTIFACT_SHA256 are required; a Stage-05 environment block preserves Stage-04 facts. [VERIFIED]

## SCOPE_AND_COMPLEXITY
- Complexity budget: 3 new frozen tools + 1 reused detector + 1 reused corroborating locator + 1 new ledger + 1 runbook + 1 authorization record — proportionate to the corrected route and each justified above. No product-code scope.
- No scope creep into Save-All/download production; no fixture expansion; no status-vocabulary change. [VERIFIED]

## FINDINGS
- ID: RV-29-1 | Severity: MINOR | Category: GROUNDING
  - Affected: plan.md:1403 (Critical path item 7, "This gate permits one ellipsis GUI input only") vs §20.1/§20.2 (plan.md:49-52, 60-118) and the updated route section (plan.md:1606, 1619-1621) which authorize one directed album-card input (album_card_input_budget=1) plus one album-level ⋮ input for the corrected run. §20.4's corrected-literals list does not include the critical-path section, so this is a surviving stale literal, not a historical Rev19 description.
  - Evidence: [VERIFIED] by literal comparison; §20.1 states "Gate-3 therefore authorizes exactly: (1) one album-card metadata left click … then (2) one album-level ⋮ left click … Nothing else."
  - Failure/rework mechanism: a handoff/executor reading item 7 strictly could treat the album-card input as unauthorized and refuse or abort the corrected run (fail-closed, no safety harm, but wasted attempt/derailment). Operative §20.2 and the updated route section control, so probability is low.
  - Smallest correction: restate item 7's gate scope per §20.2 (or annotate it: "Rev20 §20.2: the corrected gate also includes the one directed album-card input"). Non-gating for this approval; carry into the next plan revision.
- ID: RV-29-2 | Severity: MINOR | Category: GROUNDING
  - Affected: plan.md:1398 ("the current revision's independent approval (Rev15 at handoff time)") and plan.md:1415 ("Fresh review of the current revision (Rev15)"). These are stale self-references; §15.6 already defines "current revision at handoff time" as the binding meaning, and §20.4 updated the closure paragraphs to 20 but not these two.
  - Evidence: [VERIFIED] by literal comparison; header/§16.8/closure section make the actual binding (current PLAN_REVISION at handoff time) unambiguous.
  - Failure/rework mechanism: confusion only; cannot authorize a Rev15-bound handoff because §16.8 and the header void earlier approvals and Stage 03/04 enforce plan-revision/hash matching.
  - Smallest correction: replace the parentheticals with "(the current revision at handoff time)" or "(20 at this writing)".
- ID: RV-29-3 | Severity: MINOR | Category: GROUNDING
  - Affected: §20.3 non-AFFIRMATIVE enumeration (plan.md:126-127) omits S5's INCONCLUSIVE and S2's PERMISSION_PROMPT_OBSERVED (both stop the run and route to the same blocker branch). The operative clause is "Non-AFFIRMATIVE", and PERMISSION_PROMPT_OBSERVED routes via SAFE_ABORT, so the routing is not wrong — only the enumeration is incomplete.
  - Evidence: [VERIFIED] by literal comparison with §20.2 S2/S5 and the sequence preamble ("any deviation is SAFE_ABORT").
  - Smallest correction: mark the list illustrative or add the two reason codes.
- ID: RV-29-4 | Severity: MINOR | Category: GROUNDING
  - Affected: §20.2 precondition 2 (plan.md:73-75) reuses the v2 card-⋮ locator as "corroborating, never blocking, and it never supplies the click point", but no step names where it runs or what exactly it corroborates (its output includes a click point).
  - Evidence: [VERIFIED] by literal comparison; the constraint prevents misuse but leaves the corroboration role unpinned.
  - Smallest correction: name the step(s) (e.g., pre-frame album-list corroboration) and state that its point is recorded only.
- ID: RV-29-5 | Severity: MINOR | Category: SECURITY
  - Affected: §20.2 S11 (plan.md:115-118): the observed album-level menu may be left open because no close input is authorized; the documented calibration procedure prefers a proven safe close (ui-procedure.md:128). The plan mitigates with immediate owner notification.
  - Evidence: [VERIFIED]; the album-level menu per the documented reference contains Save All, so the open-menu interval carries a small owner-misclick hazard.
  - Smallest correction (no authorization change): make the S11 owner notification explicit — "the menu may contain 儲存全部/Save All; please close it without activating any item (e.g., click an empty area carefully)"; optionally record the documented safe-close deviation in the route result.
- ID: RV-29-6 | Severity: MINOR | Category: TEST
  - Affected: §20.2 precondition 2 (plan.md:69-75) requires the v3 tools "with their frozen self-tests" but does not explicitly require the self-test summary to have passed and been recorded before any input (attempt-04's §19.2 wording had "frozen and self-tested before the click").
  - Evidence: [VERIFIED] by literal comparison.
  - Smallest correction: state "frozen and self-tested (summary recorded, all pass) before any input".

No BLOCKER or MAJOR findings. The three hard-boundary safety questions resolve affirmatively: (1) authorization reading defensible with the alternative recorded and owner supersession preserved; (2) every failure path stops with zero side effects and immediate notification, and AFFIRMATIVE cannot rest on OCR-only or human-only evidence; (3) worst-case targeting error is bounded to non-destructive UI effects (menu open/close, album/photo view) with no menu-item activation, chooser, or state write.

## REQUIRED_PLAN_CHANGES
None. No unresolved BLOCKER/MAJOR capable of invalidating goal alignment, implementation, safety, compatibility, rollback, or acceptance. The RV-29-1…6 MINOR items do not block Handoff and should be absorbed at the next plan revision or annotated during handoff compilation.

## RESIDUAL_MINOR_NOTES
- Route section (plan.md:1619-1621) says the "no-navigation" prohibitions are unchanged while the same bullet authorizes the directed album entry; the operative taxonomy (album_card_input_budget as a distinct class) resolves it, but the wording invites a double-take. A one-line clarification would help.
- Goal contract SUCCESS_EVIDENCE (plan.md:1302) still reads "one permitted ellipsis input in an existing ledger scope"; with three gates/ledgers this is under-specified (accurate only if read as the ellipsis input of the attempt's own frozen ledger). Suggest "the attempt's frozen ledger scope" at the next revision.
- §20.2 S7/S9 do not pin the semantics of a screen-capture failure when S2 recorded screen_scope=AVAILABLE (whether the burst is skipped, and whether the run proceeds to S8 with a window/AX-only observation). The attempt-04 contract already made screen_scope non-fatal, so the behavior is consistent with precedent, but explicit wording would remove ambiguity.
- Header field ACCEPTED_BY_USER: YES remains from earlier revisions; combined with PLAN_STATUS: CANDIDATE and the explicit "no approval exists for Rev20", this is not misleading, but the next revision could relabel it as goal-level acceptance.

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Stage 03 Handoff compiled for PLAN_REVISION 20 at SHA-256 4919d87148c68ea3d70cbb9abd258edbd0bfa0b55be5123f7202251e557db17c, carrying RV-29-1…6 as non-gating residual notes; do not edit plan.md for this approval.
