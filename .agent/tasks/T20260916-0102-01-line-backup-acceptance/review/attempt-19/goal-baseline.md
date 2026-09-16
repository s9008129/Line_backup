# GOAL_BASELINE (authored before reading plan framing; sources: pasted-text-1.txt + handoff.md H2.1)

PRIMARY_OUTCOME (user): LINE macOS album backup that is fully automatic (no manual intervention) --
and for THIS wave specifically: make the automation VERIFICATION real: reproduce R1-R7 through the true
entry, fix them, and leave rerunnable, independently re-readable evidence. Not more PASS numbers.

SUCCESS_EVIDENCE:
- Three separately reported results: (1) album data result for 2024/05/13~05/17 (57 files);
  (2) reusable automation capability (safe real execution path, at-most-once dispatch, crash recovery
  without re-dispatch, duplicate protection, independently verifiable); (3) overall closure = complete
  only if both 1 and 2 hold.
- Offline/fixture PASS must never masquerade as GUI E2E success.
- R1-R7 reproduced through the real entry WITHOUT predictive fault flags manufacturing safety behavior.

MUST_NOT_BREAK:
- Formal config/state/run-log + 57 photos read-only; never redownload the valid 57 (verify-only).
- 禎 (U+798E) vs 楨 (U+6968) never merged/normalized/rewritten; no inference of same group from
  date/count/hash.
- Never re-send Save All when dispatch outcome unknown; wrong album => immediate stop.
- No AXPress/AXUIElementPerformAction/AX write/guessed coords/OCR-only pass/sandbox workaround.
- No commands triggering admin/authorization dialogs (sfltool/sudo/TCC).
- Old approvals (Rev13/attempt-16, Rev14/attempt-17) invalid for a new revision. Append-only.
- One album scope only. GUI: at most ONE new current-target ellipsis observation, only via explicit
  precise user gate; nothing else (no menu/Save All/chooser/keyboard/state write/download).
- Evidence per attempt: full input, argv/env (minus secrets), stdout/stderr/exit, program hash,
  independent side-effect counter, before/after state, manifest SHA-256+bytes, durable (not /private/tmp).

NON_GOALS: other albums/groups; bridge repair unless causally proven necessary (SUPPORTING);
historical cleanup/generic frameworks (BEST_EFFORT).

CRITICAL_PATH: Phase 0 read-only baseline -> Phase 1 isolate/archive -> Phase 2 reproduce R1-R7
(true entry) -> Phase 3 CRITICAL replan for semantic fixes -> Phase 4 minimal fix -> Phase 5
risk-appropriate regression + true integration (fake adapter = external I/O only) -> Phase 6 one GUI
observation gate if needed -> Phase 7 independent acceptance + result.

ESCALATION: (a) cannot simultaneously satisfy same-uninterrupted dispatch / crash recovery / CLI-GUI
transport when safety/persistence/authority contract change is needed; (b) contradictory source/history
intent evidence; (c) same root cause fails twice; (d) independent review finds test self-certification,
production side-effect omission, cross-test contamination again; (e) bridge necessity undecidable.
