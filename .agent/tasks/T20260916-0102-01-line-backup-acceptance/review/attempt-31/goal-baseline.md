# GOAL_BASELINE — independently reconstructed before reading the Rev21 rationale

Sources used (authoritative, read first):
1. `handoff-vision-agent-2026-09-17.md` (H3.0) — binding handoff for this wave.
2. `GOAL-vision-agent-next-conversation.md` — the owner's `/goal` command file.
No Planner transcript, no Rev21 rationale, no prior review attempt text was used to form this baseline.

## PRIMARY_OUTCOME (this wave)
Two inseparable owner-directed goals:
- G1 (Vision replacement): replace the OCR reader actually used by the official route-verification chain
  (the three v3 tools `locate_album_card.py` / `verify_album_open.py` / `locate_album_ellipsis.py` under
  `evidence/20260916-route/tools/`) with the macOS-native Vision framework (`VNRecognizeTextRequest`,
  system frameworks only, no third-party dependency). This is a SEMANTIC change: full CRITICAL flow
  (Rev21 plan → fresh independent double review → recompiled task handoff → fresh Stage 04 → independent Stage 05).
- G2 (bounded AI-Agent acceptance test): a bounded, re-runnable, append-only-evidence agent test that proves
  (a) Vision is the more reliable reader on the key fields (date title, photo count, group name) and
  (b) re-running the frozen verification logic with the Vision reader removes the attempt-05 blocker
  (`57` misread as `75` → `TARGET_MISMATCH`) on the frozen frames, with C1–C5 as the design starting point,
  all offline, zero GUI input.

## SUCCESS_EVIDENCE (what proves the outcome)
- New versioned tools whose only semantic delta vs v3 is the reader layer; same gating rules, verdicts,
  exit codes, refusal paths; no v3/v2 byte touched; no prior evidence overwritten.
- C1–C5 executed on the four durable frozen frames with raw readings + SHA-256 evidence; C2 requires
  deterministic repeats; C4 stays `DEMONSTRATION_ONLY` and never flips the frozen attempt-05 verdict.
- v3 self-test (13 cases) re-expressed against the new tools and green; helper-unavailable fail-closed
  path exercised; bounded loop: 5 cumulative failures → stop + notify owner; no long retry.

## MUST_NOT_BREAK
- Zero GUI input in this wave; if ever needed: at-most-once, zero retry, no menu-item (Save All named),
  no chooser, no keyboard, no AX write; agent never self-authorizes.
- Zero images in the conversation (paths + SHA-256 only); captures only under /tmp or the working dir.
- Destination `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` and all
  formal config/state/run-log: read-only; the 57 photos are never re-downloaded or modified.
- `禎` (U+798E) and `楨` (U+6968) are never merged or normalized.
- No historical coordinates as input; current-frame derivation only.
- Supplementary evidence never overturns a frozen verdict (`SUPPLEMENTARY_NON_AUTHORITATIVE`).

## OWNER-RESERVED DECISION (binding; agent may not act)
Route attempt-05 closure (A: `ROUTE_NOT_NEEDED`; B: a NEW revision + NEW one-shot ⋮ observation gate).
Status quo: `STOPPED_AT_S5_TARGET_MISMATCH`, `CLOSED_AFTER_INPUT_1`, `owner_decision_required: true`;
album-card input spent 1/1; ⋮ input unspent but precondition unmet. The owner has not chosen.

## NON_GOALS / DEFERRED
- Any GUI input, any menu item, any download/Save-All, any route continuation or continuation under Rev21.
- A live screen-capture layer (per H3.0 §8.1 it is read-only-capable but non-essential; may trigger an OS
  permission prompt).
- Expanding beyond: one album, LINE `jp.naver.line.mac`, group `旻謙允禎成長日記`, album
  `2024/05/13～05/17`, expected 57.

## CRITICAL_PATH (smallest safe path)
1. Phase 0 read-only baseline (done: committed `adf1829`; SHA anchors, helper rebuild, C1/C3/C5 + 5×
   determinism sanity, durable frame preservation copies).
2. Rev21 plan (this artifact) → fresh independent double review → `PLAN_APPROVED` on the exact hash.
3. Stage 03 handoff bound to that revision/hash: v-new tool set is the official reader; frozen frame SHAs;
   C1–C5 acceptance; 5-failure stop; C4 `DEMONSTRATION_ONLY`; route stays owner-reserved; integration-level
   acceptance, never called live E2E.
4. Stage 04 fresh implementation: new reader + versioned tools (v3 logic, reader swapped), v4 self-test
   matrix green, C1–C5 with append-only raw evidence + SHA table; no GUI input, no v3 byte touched.
5. Stage 05 independent acceptance on the frozen inputs; route/album-data results must remain separately
   reported and unchanged.

## FAILURE ROUTING (owner constraints)
5 cumulative failures stop the loop with recorded evidence + owner notification (no 2-hour retries);
same-root-cause repeated failure or needed GUI authorization → stop and escalate; "three results reported
separately" (① album data ② reusable capability ③ overall closure); non-technical owner reporting.
