# GOAL_BASELINE (independent reconstruction, attempt-30)

> Written BEFORE reading `plan.md` Rev21 rationale. Authoritative sources:
> `handoff-vision-agent-2026-09-17.md` (H3.0, binding launch handoff) and
> `GOAL-vision-agent-next-conversation.md` (owner /goal command file).

## PRIMARY_OUTCOME (two mandatory objectives)
1. **Vision replacement**: Replace the tesseract OCR reading role in the official
   verification chain — "official" = the reader actually used by the three frozen v3
   tools (`locate_album_card.py`, `verify_album_open.py`, `locate_album_ellipsis.py`)
   — with macOS-native Vision (`VNRecognizeTextRequest`). Explicitly a **semantic
   change**: must go through the full CRITICAL harness process (Rev21 plan → fresh
   double independent review → recompiled task handoff → fresh implementation →
   independent acceptance). Not allowed to edit tools directly as a "small fix" or
   to relax any fail-closed rule ad hoc.
2. **Bounded re-runnable AI-agent autonomous test**: Prove with append-only,
   re-runnable evidence that (a) the Vision reader is more reliable than tesseract on
   the key fields (date title, photo count, group name), and (b) re-running the
   frozen verification logic with Vision as reader makes the attempt-05 "75≠57"
   blocker disappear — demonstrated offline on the frozen frames first; formal
   acceptance semantics are defined by Rev21. Design starting points: C1–C5
   (all offline, zero GUI input).

## SUCCESS_EVIDENCE (owner-anchored)
- C1: post frame (`4cb8a6b4…`) → Vision reader reads count = 57, normalized, in the
  count zone under the title.
- C2: determinism — same input re-run N≥5 times reads identical each time
  (exact rule incl. whether conf jitter is allowed: Rev21 must define).
- C3: date title `2024/05/13~05/17` read correctly on both pre and post frames
  (full/half-width and `~` variant rules: Rev21 must define).
- C4: offline re-run of frozen `verify_album_open.py` with the Vision reader on the
  attempt-05 pre/post frames should reach `ALBUM_OPEN_VERIFIED`; marked
  `DEMONSTRATION_ONLY`; formal semantics by Rev21.
- C5: 1x/2x probe crops (`aea53a0d…` / `7b9d0a19…`) each read 57.
- Stage 05 independent acceptance; offline re-run is integration/contract level and
  must NOT be passed off as live E2E.
- Post-change: the existing 13-case v3 self-test (currently 13/13,
  `selftest-summary.json` SHA `17840e91…`) must be re-run with semantics updated per
  Rev21.
- Owner's reporting rule: three results reported separately — ①album data outcome,
  ②reusable capability outcome, ③overall closure; only ① AND ② both holding counts
  as complete.

## MUST_NOT_BREAK (hard prohibitions / invariants)
- Fail-closed semantics stay fail-closed; no ad-hoc threshold relaxation.
- Frozen verdicts (attempt-05 `TARGET_MISMATCH`) are NOT overturned by supplementary
  evidence ("supplementary evidence" ≠ "semantic change").
- 57 files at `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`
  never re-downloaded, never modified/deleted; official config/state/run-log read-only.
- GUI input: at-most-once, zero retry; non-explicit-AFFIRMATIVE = unauthorized.
  Never click any menu item (esp. "Save All"); no chooser; no keyboard input; no AX
  writes; any new GUI input requires a NEW explicit owner gate; agent never
  self-authorizes GUI input (incl. "one more click").
- Zero conversation images: images only to /tmp or workspace for programs; reports
  carry only paths + SHA-256 (60-image blowup history `05ffef68…`).
- 禎 U+798E must never be merged/normalized with 楨 U+6968.
- No historical coordinates as input basis; always derive from the current frame.
- No new third-party dependencies; Vision = system framework.
- Append-only evidence; never overwrite past evidence.
- No writes to `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/...` or
  `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/...`.

## OWNER-RESERVED DECISIONS (agent must not act)
- Route attempt-05 close-out choice: (A) declare `ROUTE_NOT_NEEDED`, or (B) later
  open a new one-shot gate authorizing ONE observation of the in-album ⋮ (observe
  only, no menu clicks; requires a new revision because input-② preconditions were
  never met). Until the owner answers, no action on the route.
- Owner confirms the plain-language owner view of Rev21 acceptance rules (conf
  threshold, field-location tolerance, normalization like `57張照片`→`57`,
  determinism rule) — technical correctness stays with Planner/Reviewer/Verifier.

## NON_GOALS / SCOPE FENCE
- Only this one album: LINE app `jp.naver.line.mac`, group `旻謙允禎成長日記`,
  album `2024/05/13～05/17`, expected 57 photos. No scope expansion.
- No live GUI re-run; album-card input budget is SPENT (1/1); ⋮ UNSPENT but
  precondition `ALBUM_OPEN_VERIFIED` unmet; retry budget 0.
- No re-download, no state/config/run-log writes, no menu interactions.

## CRITICAL_PATH
Rev21 plan (Goal Contract; CORE = Vision replacement + agent test; SUPPORTING /
BEST_EFFORT explicitly labeled; gating/thresholds/fail-closed/self-test-update
policy) → fresh double independent review until PLAN_APPROVED → recompiled task
handoff (old archived) with revision/hash → fresh implementation (reader swap,
self-test re-run, C1–C5, append-only evidence) → Stage 05 independent acceptance
per plan settings.

## BOUNDED-AUTONOMY / ESCALATION RULES
- Cumulative 5 failures → stop, record evidence, notify owner (no long-running
  retry).
- Escalate immediately on: semantic change beyond Rev21 authority; self-verification/
  contamination concern; same root cause failing twice consecutively; need for new
  GUI authorization; any thought of touching the 57 files or official data.
- Owner-facing communication: plainest language; result/blocker/decision first.
