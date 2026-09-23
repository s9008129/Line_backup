# PLAN — Rev27c: append-only Save All candidate locator v8 (false-negative closure)

PLAN_REVISION: rev27c-2
TASK_CLASS: STANDARD (safety-critical locator revision; zero GUI input in this round)
REVIEW_REQUIRED: YES (two fresh independent reviews of this exact file's SHA-256
  plus the v8 locator/selftest SHAs it binds)
INDEPENDENT_ACCEPTANCE_REQUIRED: NO for this round (offline replan; verification
  is the deterministic selftest + offline replay in `tools/v8`)
E2E_REQUIRED: NO (no live GUI input is authorized in this revision)
PREPARED: 2026-09-23 (zero GUI input; repo evidence writes only)

AUTHORIZATION: ZERO_GUI_SAVE_ALL_LOCATOR_REPLAN /
REV27C-SAVE-ALL-CANDIDATE-LOCATOR-AFTER-ATTEMPT05

Bound artifact SHAs (computed from disk at plan time):

```
tools/v8/locate_save_all_menu_item.py          c5ad46861706a9a2c1c4d477caeda2a809c87c5488844f14a4d3efb34c668a86
tools/v8/selftest/run_selftest.py              c94fc4074f0cd323ee53fe09428b0d38b61af04f5993ceb344acaa02e236f462
tools/v8/selftest/results.json                 943f293995b8ecc3f51ad9fc672c1fe899ba37312dc377d14a809ee118affe6a
replay/replay-record.json                      2afcd7bec8f6e28826fbf0687c7dd2c604eed7b7746bc854ab2913368ac51540
frozen v7 locator (unmodified)                 ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a
injection-supplemental/run_injection_case.py   cdc8fb0521d2ca9ad57534d7a791633529120f13e1c7e185fcd4e7db585ee9ee
injection-supplemental/results.json            36ebf7a335903a587e975447cb9d6793a25579933e1f054ae6a70aadfcd1aca4
injection-supplemental/README.md               377902059a032d51f2ad5e8e8756ab4fccae96112d01c7bada7a85d83075dc2d
scratch, left on disk, NOT part of the frozen binding:
tools/v8/selftest/fixtures/geo-a05-injected-history.json         842cb93330e3183cf5c3cc7cd28e69b5714084499aa994f49cdc93d7fa2f3418
tools/v8/selftest/out/c19-historical-coordinate-injection.json   ab4c577a9575b2e937df83f439f09eba06a9f222dc183a5f287bc5730124ba5e
```

## 0. Revision history (rev27c-1 -> rev27c-2)

rev27c-2 changes documentation and binding only. The v8 locator itself is
unchanged (`c5ad4686...`); no design rule, gate, checklist item, exit code,
tolerance or live-route element changes.

**Trigger.** `review/attempt-01/review-01-top-down.{md,json}` returned
`PLAN_REVISION_REQUIRED`: during that review a concurrent pre-freeze
modification replaced the selftest bytes on disk (`c94fc407...`/`943f2939...`
-> `0dde65b3...`/`c83e2ed6...`, adding case c19-historical-coordinate-injection
and fixture `fixtures/geo-a05-injected-history.json`), which invalidated the
rev27c-1 freeze for the window in which it was observed — even though all nine
checklist items passed against the rev27c-1-bound bytes.

**Resolution (pre-freeze withdrawal).** Case c19 was withdrawn before freeze so
the frozen selftest bytes equal exactly what rev27c-1 bound: `run_selftest.py`
was restored byte-exactly to `c94fc407...`, and `results.json` was regenerated
by two consecutive runs of the restored script to `943f2939...` (43/43 cases
PASS, 9/9 global assertions PASS, every `out/` file byte-identical across the
two runs; `run-ledger.json` records the add/withdraw episode). The withdrawn
case's fixture (`842cb933...`) and its scratch output (`ab4c577a...`) were left
on disk per this round's zero-cleanup rule; neither is referenced by the frozen
`run_selftest.py` and neither is part of the frozen binding.

**Coverage replacement for the withdrawn case.** The negative-matrix item
"historical-coordinate injection" is covered by a supplemental offline test
(`injection-supplemental/`, bound above): the frozen v8 CLI is run on the
attempt-05 frame with the clean geometry fixture (control) and twice with the
decoy-injected fixture (historical v5 ellipsis click point `[304, 50]`,
historical v7 candidate `[1313.5, 332.333]`, app-local fallback `[42, 988]`).
Checks 11/11 PASS: ELIGIBLE with exactly one candidate; the injected run's
decision and candidate are identical to the clean control's; the candidate
equals the current-frame derivation (frame px `[1297.333, 351.5]`, screen pt
`[648.667, 175.75]`, app-local `[319.667, 134.75]`); it differs from every
decoy; the injected run is deterministic (x2 byte-identical stdout). The
supplemental run was itself executed twice with byte-identical outputs
(`results.json` `36ebf7a3...`); its injected CLI output is byte-identical to
the withdrawn case's scratch output (`ab4c577a...`), and its clean control is
byte-identical to the reviewed c01 stdout (`c92f4151...`).

**Documentation-nit correction (review-01 F5/R7, non-blocking).**
`attempt-01/locator-freeze.json` states `refusal_cases: 25`; that counter is
stale. Authoritative from `results.json`: 43 cases, 7 ELIGIBLE, 36
refusal-verdict cases, refusal-class cases 2 (c07, c08), 9/9 global assertions.
The freeze-record artifact itself is left untouched (its bytes are what the
cycle-1 reviewer inspected).

**Gate effects.** Plan review cycle 1 -> `PLAN_REVISION_REQUIRED`
(attempt-01); cycle 2 reviews this rev27c-2 file. Nothing here claims approval:
the two fresh cycle-2 reviews must independently confirm every checklist item
and the bound SHAs above.

## 1. Goal Contract (plain language)

In attempt-05 the fresh menu was affirmatively observed and the target item
「儲存全部」itself was read cleanly, but the frozen v7 Save All locator refused
(`MENU_CONTENT_UNEXPECTED`, exit 5) and no Save All candidate was established.
The owner did not authorize a manual override and did not want one: the refusal
was a **false negative** caused by an irrelevant contextual OCR typo, and the
correct fix is a reviewed, append-only locator revision that keeps every
safety property while removing the accidental dependency.

**CORE**: a new fail-closed locator (v8) that

* still requires the target「儲存全部」to be affirmatively recognized as an
  exact string — no fuzzy/similar/partial matching of the target, ever;
* still requires a fresh, frame-bound menu surface (detector verdict + bbox +
  window geometry, all SHA-bound to the SAME frame);
* derives the candidate from the current frame's own OCR rows + menu bbox +
  window rect only (no historical coordinate anywhere);
* tolerates small OCR damage in **non-target** context rows exactly where the
  safety analysis shows it is harmless, and refuses everywhere else;
* is offline-replayed against attempt-05 (must become ELIGIBLE) and against the
  earlier positive menu frames (consistency), and passes the full negative
  matrix.

**SUPPORTING**: the future live route definition and the menu-persistence rule
(design only; nothing is executed this round).
**BEST_EFFORT**: none.
Nothing in this revision authorizes ellipsis, menu, Save All, chooser or any
live GUI input; GUI input this round = 0.

## 2. Root cause (OBSERVED, from disk evidence)

`evidence/20260921-rev27-save-all/attempt-05/selftest-attempt05/result-live-positive1.json`
(frozen v7 locator, live run 1; run 2 byte-identical) recorded:

```
rows: [選擇項目- , 修改相簿名般 , 儲存全部 , 刪除相簿t , 分享相簿]
cross_check.reference_hits:
  選擇項目 -> [0] ; 修改相簿名稱 -> [] ; 儲存全部 -> [2] ; 刪除相簿 -> [3] ; 分享相簿 -> [4]
cross_check.strict_order: false ; identified_row_index: 2
verdict: MENU_CONTENT_UNEXPECTED ; reason: reference item order not found around the identified row
```

Answers to the four root-cause questions (labels OBSERVED / INFERRED / UNKNOWN):

1. **Did the locator treat the exact OCR content of every menu item as a
   necessary condition for establishing the candidate? — YES (OBSERVED).**
   v7 required, for each of the five reference items, an exact substring hit
   (`ref in row_text`) and strict top-to-bottom order before it would derive a
   candidate; `reference_hits` for 修改相簿名稱 was empty, so `strict_order`
   was false and the locator exited 5 before any geometry/candidate work.
2. **Was the target「儲存全部」itself read correctly? — YES (OBSERVED).**
   Row 2 text was `儲存全部`; the v8 replay of the same frame shows the three
   target words with confidences 96.955 / 96.985 / 96.556 and a clean band
   `[1282.667, 327.333, 1385.0, 375.667]`.
3. **Was the failure caused only by the non-target item? — YES (OBSERVED).**
   Exactly one of the five `reference_hits` was empty: 修改相簿名稱, whose row
   OCR read `修改相簿名般` (glyph 稱 -> 般, conf 49.772). The other four rows
   hit exactly. The refusal is fully explained by that single non-target glyph.
4. **Is the non-target exact text a necessary safety signal? — NO (INFERRED,
   with the residual explicitly bounded).** What actually prevents a wrong
   click is: (a) the menu surface was affirmatively detected on this frame;
   (b) the target string is exact and must occupy exactly one row inside the
   verified bbox; (c) that row must be the middle row (position 3 of 5) whose
   neighbors still match 修改相簿名稱-ish / 刪除相簿-ish; (d) the candidate must
   sit in the row's safe interior, away from row and neighbor boundaries. A
   single-glyph misread of a *neighbor* row does not change which row the
   target is, nor where that row is. Residual (UNKNOWN, recorded honestly):
   there is no formal proof that no other LINE menu could present the same
   five-row shape with 儲存全部 in the middle; the mitigation is the bounded
   tolerance (below) plus the live-route gates that sit outside the locator
   (single-ellipsis provenance, baseline tripwire, staging preflight, durable
   intent, at-most-once dispatch, post-click observation).

## 3. v8 locator design (implemented: `evidence/20260916-route/tools/v8/locate_save_all_menu_item.py`)

Append-only successor of the frozen v7 locator; v7 and every earlier frozen
tool are byte-untouched. Read-only; no GUI/input capability; no network; the
only write site is the `--out` JSON. Deterministic: identical inputs produce
byte-identical output (no timestamps, no randomness).

**HARD gates (any failure -> a precise refusal verdict; never a candidate):**

| gate | rule |
|---|---|
| frame/detector binding | detector JSON must be `detect_menu_popup / MENU_DETECTED`, its `post` must equal the passed frame path AND `post_sha256` must equal the frame's SHA-256 |
| geometry binding | geometry JSON's `frame_sha256` must equal the frame's SHA-256; window rect + capture scale must be present |
| popup shape | menu bbox must be a plausible popup: area <= 30%, width <= 50%, height <= 80% of the frame (kills whole-screen false positives) |
| bbox validity | four ascending numbers, inside the frame |
| target exactness | the target string `儲存全部` must appear (exact, no fuzzy/partial/similar) in exactly one OCR row: 0 rows -> NOT_FOUND, >1 rows -> AMBIGUOUS |
| reference structure | exactly five CJK item rows, matching the reference order 選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿 top-to-bottom; the **target row is matched with tolerance 0**, each non-target row tolerates **at most ONE substituted character** in a **length-equal** window (no insertions/deletions); the target row must be the 3rd item row |
| row geometry | every item band inside the bbox (1px rounding epsilon); adjacent bands must not overlap; target band height in [16px, 50% of bbox height]; target word centers vertically cohesive (spread <= max(8px, 25% band height)) |
| addressability | (window rect ∩ bbox ∩ frame) must exist; x-overlap between the target band and that region >= 20px; x_safe = overlap shrunk by 2px must be non-empty |
| y safe interior | y_safe = [max(band.top + edge, above.bottom + 12px), min(band.bottom - edge, below.top - 12px)], edge = max(6px, 15% band height); empty -> ROW_GEOMETRY_UNSAFE |
| placement | candidate (midpoint of x_safe / y_safe) must be inside bbox, inside the addressable region, inside y_safe, inside the target band, and clear of row edges and of both neighbor rows |

Exit codes: `0` ELIGIBLE, `2` NOT_FOUND, `3` NOT_ADDRESSABLE, `4` AMBIGUOUS,
`5` MENU_CONTENT_UNEXPECTED, `6` BAD_INPUT, `7` ROW_GEOMETRY_UNSAFE.

**Explicit anti-requirements (must remain true):**

* the target item is never fuzzy-matched — `儲存全郜`, `保存全部`, `儲存全`,
  and any partial target all refuse (selftest s03/s04/s08, replay c05);
* no historical coordinate is read, stored or preferred; the candidate is
  computed from this frame's OCR, bbox and bound window rect (selftest g07
  static scan + c04 origin-shift case);
* a non-target row with TWO or more substitutions still refuses
  (MENU_CONTENT_UNEXPECTED) — the tolerance is deliberately one glyph per row;
* ambiguity of any kind (two target rows, target split across rows, band
  overlap, bands outside the bbox, empty safe regions, disjoint window)
  refuses.

**Pre-freeze correction (recorded for review honesty).** During selftest
development the v8 draft computed `intersect(intersect(window_rect, bbox),
frame_rect)` and raised an unhandled `TypeError` when the window rect and the
menu bbox were disjoint, instead of returning the documented NOT_ADDRESSABLE.
The fix (two-stage intersection with an explicit None check) was applied
BEFORE freeze; the frozen SHA above is the fixed file, and selftest cases
c15/s22 now prove the disjoint-window class returns NOT_ADDRESSABLE (exit 3)
with no candidate. No other pre-freeze change was made.

## 4. Future live route (design; REQUIRES A NEW OWNER AUTHORIZATION)

The Rev27 Gate A chain is unchanged by this revision — the locator version
changes, no gate is skipped, weakened or merged:

```
fresh album-detail composite (frozen verifier AND lineage guard)
  -> fresh frozen v5 ellipsis locator, exactly one ellipsis click
  -> fresh menu detection on the post-click frame
  -> NEW reviewed v8 Save All locator (this revision)                     <- replaced component only
  -> accepted-baseline tripwire (57 files / 17,924,900 bytes / digest unchanged)
  -> staging preflight
  -> durable Save-All intent written
  -> exactly one Save All click (at-most-once, no retry, no fallback)
  -> resulting-surface / chooser observation only (NO chooser interaction)
  -> STOP
```

Every gate above still fails closed on its own evidence. This revision does not
authorize any part of this chain; it only replaces the candidate-establishment
component for a future round whose owner authorization explicitly cites
`REV27C` and the v8 SHA.

## 5. Menu persistence rule (recorded; no action this round)

The attempt-05 menu may still be open or may have disappeared during this
offline replan. This round must not touch LINE to check, and no future round
may reuse the attempt-05 menu or the attempt-05 offline candidate. If the menu
is gone when a future round starts, that round must fail closed, obtain a new
owner authorization, and re-establish fresh menu evidence (fresh composite ->
fresh ellipsis -> fresh detection -> fresh v8 candidate). The v8 candidate is
always derived from the frame captured in the same uninterrupted attempt.

## 6. Verification obligations for this revision (executed offline)

* `tools/v8/selftest/run_selftest.py` — 43 deterministic cases, all PASS,
  9/9 global assertions PASS, including the full negative matrix: target
  missing / misread / partial / twice / spanning rows; non-target 1-sub (single
  and multiple rows) ELIGIBLE; non-target 2-sub or length change REFUSED;
  item count 4/6 REFUSED; order swap REFUSED; band overlap, empty y-safe,
  band outside bbox, whole-screen and over-wide bbox, disjoint window,
  x-overlap below rule, empty OCR words, duplicate context row, stale frame
  SHA, wrong-frame detector, non-detection, missing bbox, bbox outside frame,
  missing frame, unparseable geometry — every one a refusal with no candidate;
* historical-coordinate injection (bound supplemental test): the decoy
  historical v5/v7 coordinates injected into the geometry input have zero
  effect on the candidate; 11/11 checks PASS and the whole supplemental test
  was executed twice with byte-identical output;
* determinism: the whole selftest ran twice; `results.json` byte-identical
  (sha256 943f2939...), every CLI case byte-identical across its two runs;
* offline replay (`replay/build-replay-record.py`, `replay/replay-record.json`
  2afcd7be...): attempt-05 -> ELIGIBLE, candidate frame px [1297.333, 351.5]
  (app-local [319.667, 134.75]); attempt-13 -> ELIGIBLE, candidate frame px
  [1313.5, 332.333] (identical to the historical v7 candidate — compared, not
  used as input); attempt-19 -> ELIGIBLE; each run twice, all byte-identical;
  attempt-05 run pairs sha e8f53bd3..., attempt-13 b802113b..., attempt-19
  768c5cda...;
* an offline ELIGIBLE verdict is NOT a live click authorization; the replay
  inputs carry `"authority": "OFFLINE REPLAY INPUT ONLY"`.

## 7. Review checklist (each item must be independently confirmed)

1. target「儲存全部」still requires affirmative exact recognition (no fuzzy);
2. non-target OCR typos cannot alone cause a false negative (attempt-05 case
   becomes ELIGIBLE; 1 substitution per non-target row tolerated);
3. relaxing non-target OCR cannot let a wrong menu or a wrong row pass
   (structure, order, target position, geometry all still hard);
4. the candidate is derived from the current frame's own evidence only;
5. no historical-coordinate fallback exists anywhere;
6. the attempt-05 replay candidate is unique and reproducible (run ×2);
7. every ambiguous case in the negative matrix REFUSES;
8. Save All stays at-most-once (dispatch is outside this locator; the locator
   produces one candidate and never clicks);
9. the chooser is not part of this revision (Gate B remains future work).

Both reviews must return `PLAN_APPROVED` for this exact plan SHA and the bound
locator/selftest SHAs before any future live authorization may cite Rev27c.

## 8. Status / handoff

This revision is offline tooling + evidence only: GUI input = 0, album-card
clicks = 0, ellipsis = 0, Save All = 0, chooser = 0, keyboard = 0, scroll = 0,
AX write = 0, downloads = 0, staging mkdir = 0, destination writes = 0, and
the accepted baseline (57 files / 17,924,900 bytes) is unchanged. When both
fresh reviews are `PLAN_APPROVED`, the attempt-05 positive replay passes, and
all negative tests pass, the project status is
`READY_FOR_REV27C_LIVE_AUTHORIZATION` — i.e. an owner may decide whether to
authorize one future live round that re-verifies the whole chain above. It is
NOT READY_TO_SAVE_ALL, NOT READY_FOR_CHOOSER_GATE_B and NOT BACKUP_COMPLETE.
