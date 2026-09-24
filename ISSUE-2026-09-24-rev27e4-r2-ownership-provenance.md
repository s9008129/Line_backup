# Issue: R2 activation can affirm without target-ownership provenance

**Status:** OPEN — analysis and plan review only; no classifier fix has been applied.
**Authorization context:** `REV27E4-CYCLE4-AFTER-REV27E3-REPLAN-REQUIRED`
**Repository:** `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
**Scope:** offline synthetic evidence and classifier semantics only.

## Plain-language summary

The R2 route can treat “an event that looks like the Save All menu action” as proof that the target LINE process owns the action, even when the event does not attest who owns it. The current positive fixture demonstrates this gap: it expects an affirmative while omitting both mandatory ownership facts. A separate ambiguity rule also counts raw event shapes before validating them; changing it to count only valid candidates is required by the Rev27e-4 contract, but one old fixture labeled `OTHER_APP` actually carries the target LINE PID and bundle. It must remain indeterminate as contradictory evidence, not be discarded as harmless unrelated activity.

The intended repair is to require complete, mutually consistent R2 ownership/provenance before an event enters the valid R2 candidate set, and to refuse contradictions independently of candidate counting. No production affirmative authority is being requested.

## Expected behavior

An R2 event is eligible for affirmative evidence only after all of these gates pass:

```text
RAW_R2_EVENT
→ SCHEMA_VALIDATED_R2
→ OWNERSHIP_ATTESTED_R2
→ CAUSAL_WINDOW_VALID_R2
→ VALID_R2_CANDIDATE
```

The ownership attestation must include:

- `owner_pid`: present; `type(value) is int`; positive; `bool` is rejected; equal to the expected current target PID.
- `owner_relationship`: present; exact string in the reviewed closed enum; no free-text, fuzzy interpretation, coercion, or unknown value.
- Cross-attestation of event PID, panel-service PID when applicable, owner PID, expected target PID and bundle identity, event source, event class, relationship, process identity, and dispatch observation window.
- Any missing required field or contradiction emits a fail-closed refusal and cannot produce an affirmative.

The currently reviewed taxonomy names the relationship values `LINE` and `PANEL_SERVICE_OF_TARGET`. For `LINE`, the event PID and owner PID must bind to the target process and the event bundle must match the expected target. For `PANEL_SERVICE_OF_TARGET`, the event/service PID must be in the pre-dispatch panel-service census, while the owner PID and owner bundle bind to the target; the event source/class pair must also be valid for this relationship. Mere presence of `openAndSavePanelService` is supporting evidence only, never ownership.

Only route-valid candidates enter global cardinality:

```text
len(valid_r1_candidates_in_window) + len(valid_r2_candidates_in_window) > 1
    → MULTIPLE_CANDIDATE_EVENTS
    → SAVE_ALL_ACTIVATION_OBSERVATION_INDETERMINATE
```

No route priority, first-match, or R2 override is allowed. Invalid candidates do not count, but contradictory evidence still refuses; “not counted” must never silently mean “safe to ignore.” `candidate_shaped_in_window` may remain diagnostic-only.

## Observed defect and causal chain

The reviewed cycle-3 classifier is SHA-256 `242df537438750dd084cbc4aed9d8234bb66f89d66fffe7c0eab12b1332c6010`.

1. `_validate_bundle_types` type-checks `owner_pid` only when the key is present and non-null (`tools/activation_classifier.py`, around lines 356–455). This correctly rejects many supplied malformed values but does not establish requiredness; missing and null bypass the check.
2. The event-routing loop compares `owner_pid` only if supplied and compares `shape.owner_relationship` only if supplied/non-null (around lines 842–852).
3. A matching semantic target is then appended to `candidates_r2` (around lines 900–905) without a required ownership attestation.
4. With the R2 test profile enabled and no other refusal, the candidate can reach the affirmative R2 route.

The primary gap is therefore **missing requiredness at semantic candidate admission**, not a failure of the existing finite-number or strict bool/int checks.

### Concrete fixture evidence

- `cycle3/synthetic-tests/fixtures/c05-semantic-event-r2-enabled.bundle.json` contains a `LINE` `AX_MENU_ITEM_SELECTED` event for PID 969 and target bundle `jp.naver.line.mac`, with the expected test-only affirmative. It has neither `owner_pid` nor `shape.owner_relationship`.
- The cycle-3 Review 1 blocker `R1-C3-B1` records the optional-owner defect. A corrected disposable reproduction of the panel-service variant removed the embedded expected oracle, used `PANEL_SERVICE_OF_TARGET`, a service PID, and target owner bundle, omitted both owner fields, and returned `SAVE_ALL_ACTIVATION_AFFIRMATIVELY_OBSERVED`, route `R2_DIRECT_SEMANTIC_EVENT`, with no refusal. The cycle-3 review/reproduction evidence is preserved under `evidence/20260923-rev27e-activation-observability/review/attempt-03/` and in the exact reviewed-state freeze.
- An additional read-only in-memory audit reproduced direct missing ownership, panel-service missing ownership, and panel-service null ownership as R2 affirmatives. These were offline classifier probes; no application or live observer was used.

## Related candidate-cardinality / identity contradiction

The current classifier records `candidate_shaped_in_window` before source, PID, lineage, owner, and route qualification (around lines 800–812) and later refuses if either that raw count is greater than one or the valid route counts exceed one (around line 928). This historically catches some near-valid competitors, but it also lets invalid raw shapes affect candidate cardinality. Rev27e-4 explicitly requires the global rule to count valid R1 and valid R2 candidates only, with R2 qualification complete before counting.

That change needs a separate contradiction guard. Frozen fixture `cycle3/synthetic-tests/fixtures/c91-valid-r2-unrelated-shaped-r1.bundle.json` calls its second event `lineage=OTHER_APP`, but that event has `pid=969` and `bundle_id=jp.naver.line.mac`, exactly matching the observed target identity. The current code drops `OTHER_APP` at the lineage branch before checking those contradictory identity fields (around lines 824–826). If a future implementation merely removes the raw-shape count and trusts the label, a fully attested R2 could affirm despite contradictory target evidence.

Required treatment:

- Keep the c91 R2 fully attested in the cycle-4 copy.
- Before dropping `OTHER_APP`, detect a target-PID/target-bundle contradiction and refuse with the existing taxonomy code `PROCESS_IDENTITY_MISMATCH` (or a separately reviewed, equally explicit refusal code).
- c91 remains `INDETERMINATE`, has no affirmative route, and has no production-qualifying affirmative; it need not claim `MULTIPLE_CANDIDATE_EVENTS` because it has only one valid candidate.
- Add a distinct truly unrelated `OTHER_APP` event with a different positive PID and foreign bundle consistent with that lineage. It may be dropped from valid cardinality; if paired with an otherwise valid R2, any possible affirmative remains restricted to the explicit test-only profile and must be non-production.

Other retained cross-route expectations:

- c31: two valid R1 candidates refuse globally.
- c32: cycle-4 copies give both R2 events complete valid ownership; two valid R2 candidates refuse globally.
- c89: cycle-4 copy gives its R2 event complete valid ownership; one valid R1 plus one valid R2 refuses globally.
- c90: wrong source/class on the R2-shaped event retains `CLASS_SOURCE_MISMATCH`; that invalid R2 does not count, and the result remains indeterminate because the contradiction itself refuses.

## Invariants that must remain true

- **CB-1:** finite numeric evidence validation is not weakened.
- **CB-2:** strict bool/int behavior is not weakened; bool is not an integer for PID purposes.
- **CB-3:** more than one *valid* R1/R2 candidate always refuses before route selection. This is a deliberate clarification from the prior raw-shape gate, not a route-local winner or priority rule.
- All 108 frozen cycle-3 case IDs remain in the cycle-4 corpus; the cycle-3 bytes and reviews remain immutable. Any cycle-4 fixture/oracle adjustment is recorded by case ID and reason, and exact ID-set equality is machine-checked separately from the fixture aggregate.
- Default/production profiles produce zero production-qualifying affirmatives. A fully attested R2 may affirm only under an explicit test-only profile and must report `production_qualifying_affirmative=false`.
- Re-run all Rev27e-3 scenarios and the new owner/relationship/source/service/restart/window/duplicate/multi-candidate attacks. The complete suite must have no failures and two runs must be semantically deterministic.
- Attempt-07 remains `SAVE_ALL_ACTIVATION_OBSERVATION_INDETERMINATE`; it is not retroactively reclassified.
- The production reconciliation barrier remains. This issue does not authorize live attach, LINE operation, calibration, Save All, chooser use, production retry, destination writes, cleanup, or backup-success claims.

## Current review/implementation state

- Cycle-3 exact reviewed state is frozen append-only; snapshot manifest SHA-256: `bb454824e0915d9d84b6ab39d0051fd1a13609adbed87fe9e1f49bf5eda28a22`.
- Cycle-3 outcome SHA-256 recomputed from disk: `924f8057c8701fafd0121bba7ed14d5c94bb319a281b3eb6c238a0d888f0b687`.
- Cycle-3 Review 1: `PLAN_REVISION_REQUIRED`; Review 2: `PLAN_APPROVED`; cycle-3 plan SHA-256: `e6124faa3f3b87ef990d9d5a3da0e71ee3390f7174ba4b94a4ae5598466f9a50`.
- Fresh Stage-02 attempt-01 found the valid-cardinality/case-identity/status-routing/determinism gaps. Attempt-02 found that the status-routing plan also needed explicit machine-checkable evidence fixtures. Rev27e-4 plan revision 7 is still a draft and has not been approved; its SHA at issue authoring: `ea67ec76a45f8e6a1f210ccb0193a43f09baa51dd93373f769922ecb35bfe9a1`.
- No product/classifier files have been changed for this issue. No tests were run as part of writing this report. Current Git anchor remains HEAD `9dcad7812b6e20e8f6c1d9afef2e911ade12d2dd`, `origin/master` `a9e523e7d2b91ec1775bba573003a7a1671ef945`, ahead 25.
- GUI input, LINE interaction, live attach, AX write, chooser, calibration, staging/destination write, cleanup, and push remain zero at report authoring.

## Requested independent review

Please evaluate these questions before implementation:

1. Is the causal diagnosis complete: are required owner-field checks missing at the right boundary, and are there any alternate paths that can admit an R2 event without the full attestation?
2. Does the exact ownership enum and direct-vs-panel-service PID/bundle/source/class binding establish a decision-valid relation, or does it merely validate self-asserted fields? What repository evidence is authoritative for each relation?
3. Is the c91 `OTHER_APP`/target-identity contradiction check sufficient and correctly scoped? Should another identity/source field also be cross-checked before dropping a foreign-lineage event?
4. Does valid-only global cardinality preserve the user-required CB-3 invariant while failing closed on contradictions and excluding unrelated service presence? Are c31/c32/c89/c90/c91 cycle-4 oracles coherent?
5. Are same-number PID reuse, duplicate JSON keys/attestations, and previous-process-generation ownership adequately described as tested or unresolved?
6. Is the required status-contract fixture/validator a proportionate harness acceptance obligation, and does its scope avoid creating an unnecessary runtime status framework or authorizing actual waivers?
7. Identify any missing adversarial case, hidden production path, or condition that should block the cycle-4 plan approval.

Review this issue as a root-cause and acceptance-contract document. Do not modify the frozen cycle-3 reviews, attempt-07, Rev27d, accepted baseline, or historical plans. The classifier fix remains gated on fresh plan approval.
