# Review 1 — top-down transaction / data-integrity review

- Reviewed artifact: `PLAN-2026-09-21-rev27-save-all.md`
- Reviewed SHA-256: `db972849af43dc124df1834c5877aa1caa6db092c57c0539ecd3da1b3cb14052`
- Lens: top-down — goal alignment, necessity, critical path, gate/veto proportionality, failure
  containment, coupling, design economy; then bottom-up — repository grounding, contracts, sequencing,
  verification.
- Date: 2026-09-21 (read-only; zero GUI input)
- Plan revision provenance: superseded drafts `19238547…`, `15aebb1a…`, `25903122…`; this review binds
  **only** the SHA above. Any later edit invalidates this review.

## Goal baseline reconstructed from the authoritative owner instruction

Design and review the **next bounded Save-All transaction** (the first one allowed to produce a real
filesystem side effect), decomposed into separate authorization gates, with: the accepted 57-file
baseline never written; fresh staging only; Save All at-most-once with no retry on any outcome;
chooser not bundled into the Save-All dispatch authorization; filesystem verification independent and
content-based (57-count alone insufficient); duplicate protection preserved; no cleanup without
authorization; zero GUI input in the planning round itself. Both reviews must be `PLAN_APPROVED` for
the exact plan SHA before a Gate A authorization may be requested.

## Pass 1 — top-down

1. **Goal alignment.** The plan's three gates (§3) map 1:1 to the owner's Gate A/B/C decomposition; the
   plan adds no scope (no automation, no second backup copy). PASS.
2. **Necessity / critical path.** Every CORE invariant (I1–I6, §1) traces to an owner constraint or a
   concrete safety obligation; supporting items (locator self-test, reviews inside the Gate A round) are
   prerequisites, not gold-plating. PASS.
3. **Gate / veto proportionality.** Failure rows (§10) are classified STOP / RECONCILE /
   FUTURE_REVISION with no global veto invented; `keyboard unavailable → FUTURE_REVISION` is correct
   because no side effect has occurred at that point. PASS.
4. **Failure containment.** UNKNOWN dispatch → permanent barrier, no retry ever (§7.2–7.3); dispatch
   boundary defined before the call; `ABORTED_BEFORE_DISPATCH` only with proof. PASS.
5. **Design economy / coupling.** The decision not to use the live state engine substrate (§7.4) is
   justified: the fingerprint is already VERIFIED, the engine would (correctly) refuse a second
   destination, and `prepare` models a different dispatch chain. Compensating controls named; the
   alternative is explicitly framed as a replan. PASS (observation O1 below).
6. **Data integrity.** Baseline tripwire before and after the click (§5.1.6, §5.4); staging preflight
   with `realpath`/symlink/parent-authority/emptiness checks (§4); completion definition C1–C8 (§8);
   content-multiset duplicate comparison with rename handling (C7); no second VERIFIED destination; no
   copy into the formal backup (§9). PASS.
7. **At-most-once integrity.** Budgets (§5.2, §11), intent-before-dispatch (§7.1), click count 1, and
   "a returned call proves only that the call returned" (§7.2). PASS.
8. **Verification independence.** Gate C is filesystem-only and independent of the GUI round; 57-count
   explicitly insufficient with the zero-byte hazard documented from history (§8, F3). PASS.

## Pass 2 — bottom-up

1. **Repository grounding.** F5/F6 were checked against `src/line_backup_acceptance/{transaction,
   verifier}.py` this round; F3/F4 against the live `backup_state.json` (rev 39) and `run_log.md`;
   tool SHAs re-hashed (`v5/verify_album_open.py` `ffa82aed…`, `tools/detect_menu_popup.py`
   `6ae9c250…`). PASS.
2. **Contracts.** No semantic change is proposed to the state contract or engine vocabularies; the
   route ledger mirrors the contract's dispatch/trigger vocabulary mapping (§7.3). PASS.
3. **Sequencing.** Preconditions ordered so all GUI-dependent observations precede the filesystem
   preflight, and a final freshness gate (≤15 s, dispatch as the next action) re-proves the GUI state
   immediately before the click (§5.1.8). PASS.
4. **Verification plan.** Gate C criteria are executable read-only checks with bounded sampling and a
   600 s window; failure classes are explicit. PASS.

## Observations (non-blocking)

- **O1.** Route-ledger (not live-state) intent is a deliberate deviation from the engine's substrate,
  fully justified in §7.4; OD-1 keeps the owner in control of any live-state note. No integrity loss
  for this album: the fingerprint is already VERIFIED, so no untracked-dispatch exposure remains.
- **O2.** The Gate A round must budget time for freezing + reviewing the new locator before any click
  (§5.3); this is a scheduling consideration, not a design defect.
- **O3.** Defaults for OD-1 (no live-state write) and OD-3 (preserve staging) are the conservative
  choices and are acceptable absent owner action.

## Checklist (owner-mandated bullets)

| # | Requirement | Verdict |
|---|---|---|
| 1 | accepted baseline never written | PASS — I1, §5.1.6, §5.4, §9 |
| 2 | fresh staging required | PASS — §4 (unique run_id, emptiness proof, fail-closed) |
| 3 | Save All at-most-once | PASS — §5.2, §7.1–7.3, §11 |
| 4 | UNKNOWN dispatch means no retry | PASS — §7.2–7.3, §10 rows 5/6 |
| 5 | chooser not bundled into Gate A | PASS — §3, §5.4, §6, §12 |
| 6 | keyboard forbidden unless future Gate B explicitly authorizes | PASS — §5.2 (incl. Escape), §6 table |
| 7 | no automatic ellipsis reopen | PASS — §5.1.3 (`MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`) |
| 8 | no historical menu coordinate | PASS — I3, §5.3.6 (no literal coordinates/row arithmetic) |
| 9 | no cleanup/delete without authorization | PASS — I5, §9 (PRESERVE) |
| 10 | 57-count alone insufficient | PASS — §8 (C1–C8 + zero-byte hazard) |
| 11 | filesystem verification independent | PASS — §3 Gate C, §8 |
| 12 | duplicate protection preserved | PASS — §9 (two layers; content multiset; no second destination) |

## Verdict

**PLAN_APPROVED**
