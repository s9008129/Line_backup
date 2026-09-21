# Review 2 — adversarial GUI / filesystem side-effect review

- Reviewed artifact: `PLAN-2026-09-21-rev27-save-all.md`
- Reviewed SHA-256: `db972849af43dc124df1834c5877aa1caa6db092c57c0539ecd3da1b3cb14052`
- Lens: adversarial — try to make the plan produce an unintended GUI input, an unintended filesystem
  write, a baseline mutation, a silent retry, or a false completion verdict. Read-only; zero GUI input.
- Plan revision provenance: superseded drafts `19238547…`, `15aebb1a…`, `25903122…`; this review binds
  **only** the SHA above. Any later edit invalidates this review.

## Attack list

- **A1 — menu auto-closes between the last check and the click.** Attack: the click then lands on
  whatever is behind the menu (album view / album list). Mitigation: final freshness gate ≤15 s with the
  click as the very next action (§5.1.8), plus an explicit miss-classification rule that records
  `SAVE_ALL_TRIGGER_NOT_OBSERVED` + `UNINTENDED_CLICK_OUTCOME`, stops, and reports (§5.4). Residual:
  a non-destructive unintended click (expected worst cases: photo viewer, album list) remains possible;
  accepted, bounded, and reported. **CONTAINED.**
- **A2 — the menu is open but its geometry/hover highlight changed.** The locator must derive the bbox
  and the candidate from the fresh frame only; text-first identification is unaffected by highlight
  deltas. **CONTAINED.**
- **A3 — a double click or a second activation.** `click_count = 1`, single click, retry 0 forever;
  the post-click stop rules forbid any second input of any kind (§5.2, §5.4). **CONTAINED.**
- **A4 — misidentification activates the wrong row.** Historical precedent exists (Rename / selection
  mode). The new pipeline is text-first with a row-set cross-check and fail-closed verdicts (§5.3);
  a wrong activation is still possible in principle, but it is contained: post-click classification →
  stop → never retry, and no data-side effect is reachable from menu rows other than via LINE's own
  dialogs, which the round must not touch. **CONTAINED.**
- **A5 — chooser gets pulled into Gate A.** §5.4 and §12 forbid every chooser interaction in Gate A
  (no confirm, no Escape, no clicks, no keyboard); the chooser is left open and handed off. **PASS.**
- **A6 — keyboard smuggling (Escape to "clean up").** `keyboard = 0` explicitly includes Escape in
  Gate A (§5.2); §5.4 repeats the prohibition. **PASS.**
- **A7 — accidental confirmation of an open chooser starts a download to an unknown default, possibly
  the baseline.** Mitigations: hands-off owner note, mandatory post-dispatch baseline tripwire, and
  Gate B's rule that a default is never accepted (explicit navigation to the frozen staging path only).
  Residual owner-side risk is documented rather than hidden. **CONTAINED.**
- **A8 — staging is not actually fresh, or a symlink escapes the authority root.** Six-check preflight
  (`realpath` equality, parent authority, pre-existence, post-`mkdir` emptiness, exclusion vs baseline,
  frozen name pattern/run-id uniqueness); any failure → zero input stop (§4). **PASS.**
- **A9 — historical coordinates reappear.** I3 bars `[39,923]`, `[304,50]`/`[305,50]`, attempt-13's
  bbox, and all formula-derived points; §5.3.6 bars literal coordinates and row arithmetic from the
  locator itself. **PASS.**
- **A10 — false completion from a 57-count or a stable sample.** C1–C8 require non-zero bytes,
  structural decode, absence of partial/extra entries, quiescence, and content-multiset comparison;
  the historical 24-sample stable zero-byte phase is cited as the concrete hazard (§8). **PASS.**
- **A11 — cleanup/delete.** No deletion or move anywhere; staging PRESERVE; I5. **PASS.**
- **A12 — duplicate protection bypassed.** Two layers (§9): pre-existing VERIFIED registry
  association + post-Gate-C content-multiset comparison against `b7debe92…`; no second registered
  destination; no copy into the formal backup. **PASS.**
- **A13 — detector pre-frame binding fails while the menu is actually open.** Verdict is fail-closed
  (STOP, no click). This can only cost a round, never safety. **PASS (fail-closed).**
- **A14 — an unexpected chooser/dialog appears after the click.** Classification is fail-closed to
  `SAVE_ALL_TRIGGER_UNKNOWN`; the round observes only (§5.4). **PASS.**
- **A15 — LINE closes/restarts mid-round; process crash; machine restart.** Failure matrix rows 18/19/20
  require stop/reconcile with no re-dispatch; UNKNOWN stays UNKNOWN (§7.3). **PASS.**
- **A16 — Gate B's clipboard paste treated as a "destination write".** It is a system-side operation,
  enumerated separately from filesystem writes; staging receives bytes only via LINE's own download
  after the single confirmation (§6). **PASS.**

## Residual risks (accepted, non-blocking)

- **R1.** Owner-side accidental confirmation of an open chooser (A7) — documented with mitigations.
- **R2.** A menu-close race producing one non-destructive unintended click (A1) — contained and
  reportable.
- **R3.** LINE's chooser default and rename behavior remain UNKNOWN; the plan never relies on either
  (explicit navigation; content-based duplicate comparison).

## Checklist (owner-mandated bullets)

| # | Requirement | Verdict |
|---|---|---|
| 1 | accepted baseline never written | PASS — plus tripwires before/after |
| 2 | fresh staging required | PASS — unique run_id, preflight fail-closed |
| 3 | Save All at-most-once | PASS |
| 4 | UNKNOWN dispatch means no retry | PASS |
| 5 | chooser not bundled into Gate A | PASS |
| 6 | keyboard forbidden unless future Gate B explicitly authorizes | PASS |
| 7 | no automatic ellipsis reopen | PASS |
| 8 | no historical menu coordinate | PASS |
| 9 | no cleanup/delete without authorization | PASS |
| 10 | 57-count alone insufficient | PASS |
| 11 | filesystem verification independent | PASS |
| 12 | duplicate protection preserved | PASS |

## Verdict

**PLAN_APPROVED**
