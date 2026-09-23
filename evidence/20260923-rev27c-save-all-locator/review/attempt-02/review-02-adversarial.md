# REVIEW 2 (adversarial: OCR false-positive / wrong-row / tolerance abuse) — cycle 2, attempt-02

Reviewer: fresh-context independent adversarial reviewer. Reviewed plan revision:
`rev27c-2`. Date: 2026-09-23. GUI input during this review: **0**. Network: none.
Git mutations: none. The repository was read-only except for the two review files in
this directory; every execution wrote only to `/tmp/rev27c/`. The selftest and the
injection script were never run in place (mirror copies under `/tmp/rev27c/mirror2`
with symlinked tool/frames and copied fixtures), and all python was run with `-B`.

Plan SHA-256 computed from disk: `906e949b34a5f48f46135b240b8b00a1df147a45d30da6e462c2fc4e5b1d8110` (= expected).

## Goal baseline (reconstructed before judging)

The owner wants a fail-closed Save All candidate locator (v8) that closes the
attempt-05 false negative — non-target row 修改相簿名稱 OCR'd as 修改相簿名般
(one glyph, conf 49.772) broke v7's strict reference order, producing
`MENU_CONTENT_UNEXPECTED` exit 5 with no candidate even though the target row
儲存全部 was read cleanly — **without** weakening: exact (non-fuzzy) target
identity; a fresh frame-bound menu surface (detector verdict/bbox + SHA-bound
window geometry); row/geometry safety; no historical-coordinate fallback; refusal
on ambiguity; a locator that never clicks (dispatch stays outside, at-most-once);
chooser out of scope; zero GUI input in this offline replan. Success = attempted-05
offline replay ELIGIBLE with a unique candidate, the negative matrix all refusing
with no candidate, reproducible determinism, and frozen artifact SHAs.

## Bound artifacts — SHA-256 verified from disk (all match)

| artifact | SHA-256 (computed = expected) |
|---|---|
| `PLAN-2026-09-23-rev27c-save-all-locator.md` | `906e949b…b1d8110` |
| `tools/v8/locate_save_all_menu_item.py` | `c5ad4686…4c668a86` |
| `tools/v8/selftest/run_selftest.py` | `c94fc407…e236f462` |
| `tools/v8/selftest/results.json` | `943f2939…118affe6a` |
| `replay/replay-record.json` | `2afcd7be…8ac51540` |
| `injection-supplemental/run_injection_case.py` | `cdc8fb05…585ee9ee` |
| `injection-supplemental/results.json` | `36ebf7a3…fcd1aca4` |
| `injection-supplemental/README.md` | `37790205…3075dc2d` |
| frozen v7 locator, attempt-02/03/04/05 (4 files, byte-identical) | `ea09c1ca…d60b4012a` |
| scratch (NOT bound): `fixtures/geo-a05-injected-history.json` | `842cb933…a2f3418` |
| scratch (NOT bound): `out/c19-historical-coordinate-injection.json` | `ab4c577a…24ba5e` |

Supporting evidence re-derived from disk: attempt-05 frame `2f6bf83d…76c880`,
attempt-05 geometry `f746275d…6de4349`, attempt-05 detector pairB1 `c3f841cd…c6c2abd`,
attempt-13 frame `7ccb6f9e…ee0e090`, attempt-13 detector pairB1 `d1dc6257…2e87e021`,
attempt-19 frame `e321069d…f8169a2`, and `attempt-05/selftest-attempt05/result-live-positive1.json`
`7e92e252…e2773e5811f`.

## Checklist (plan §7) — 9/9 independently confirmed

1. **Target exactness — PASS.** Source: the target only matches as an exact
   substring of the row's CJK text (`TARGET_ITEM in r["cjk_text"]`,
   `locate_save_all_menu_item.py:297-306`), and `match_reference` is called with
   tolerance 0 for the target position (`:326-329`); there is no fuzzy/similar path.
   Probes: one-substituted target 儲存全郜 → NOT_FOUND; truncated 儲存全 → NOT_FOUND;
   similar 保存全部 → NOT_FOUND (selftest s03/s04/s08; g05 violations []).
2. **Non-target typo cannot alone cause a false negative — PASS.** One substituted
   character per non-target row in a length-equal window (`NON_TARGET_SUBSTITUTION_TOLERANCE=1`
   `:88`, `match_reference` `:209-226`). Frozen-CLI replay of attempt-05 ×2
   byte-identical (`e8f53bd3…`) → ELIGIBLE with tiers [EXACT, TOLERANT_1_SUB, EXACT,
   EXACT, EXACT]; selftest s09/s10/c01 ELIGIBLE. ≥2 substitutions or any length
   change still refuse (s11/s12; probes E11/F02).
3. **Relaxation cannot pass a wrong menu/row — PASS.** Hard structure gate: exactly
   five CJK item rows in reference order, target must be item row 3 (`:311-334`);
   row/band geometry (`:335-376`), addressability and y-safe interior (`:377-433`),
   placement (`:435-454`). Adversarial probes: target moved to 4th → MENU_CONTENT_UNEXPECTED
   (E09); neighbours swapped → MENU_CONTENT_UNEXPECTED (E10/E25); 6th CJK row → refuse
   (E24b/s14); duplicate context row → refuse (s25); two substitutions → refuse (E11);
   mid-row insertion → refuse (F04); band overlap → ROW_GEOMETRY_UNSAFE (F07/s16).
4. **Candidate only from current-frame evidence — PASS.** `evaluate()` consumes only
   frame size, bbox, scale, window rect and this frame's OCR words (`:232-506`); all
   three inputs SHA-bound (`:571-580`, `:590-598`). c04 origin-shift changes
   app-local accordingly (g08); independent arithmetic (E32) reproduced the candidate
   midpoint exactly.
5. **No historical-coordinate fallback — PASS.** g07 static scan: forbidden hits [] and
   exactly 1 write site; no coordinate literals in source (grep); decoy fixture
   (decoys `[304,50]`, `[1313.5,332.333]`, `[42,988]`) yields a decision and candidate
   byte-identical to the clean control (my injected-geometry reruns ×2, `ab4c577a…`,
   equal to the withdrawn c19 scratch output); bound supplemental test 11/11 PASS
   (results `36ebf7a3…` reproduced ×2 in my mirror run).
6. **Attempt-05 replay unique and reproducible — PASS.** Frozen CLI ×2 byte-identical
   (`e8f53bd3…` == replay-record run pair); exactly one candidate
   `frame_px [1297.333, 351.5]` / app-local `[319.667, 134.75]`; attempt-13 ×2
   `b802113b…` and attempt-19 ×2 `768c5cda…` also reproduced byte-identically.
7. **Every ambiguous negative-matrix case REFUSES — PASS.** 43/43 cases pass at their
   expected verdict/exit: 7 ELIGIBLE + 36 refusals (NOT_FOUND 8, NOT_ADDRESSABLE 4,
   AMBIGUOUS 2, MENU_CONTENT_UNEXPECTED 8, BAD_INPUT 10, ROW_GEOMETRY_UNSAFE 4).
   My own per-case scan of the 43 output files: **zero candidate keys on any refusal**
   (g02 leaks [] as well); my CLI refusal batch (c07/c08 → 2, c09/c10/c13/c14 → 6,
   c15/c16 → 3) leaked nothing.
8. **Save All stays at-most-once — PASS.** The tool has no GUI/input/network capability
   (imports `:61-69`; only subprocess is tesseract OCR `:121-153`; only write site is
   `--out` `:514-519`). Attempt-05 records Save All dispatch 0 of 1, second Save All 0;
   plan §8 states GUI 0 this round.
9. **Chooser not part of this revision — PASS.** No chooser code/strings in the v8 tool
   or selftest; plan keeps the chooser as future Gate B observation-only (§4/§8,
   "NOT READY_FOR_CHOOSER_GATE_B"); attempt-05 chooser NOT_OBSERVED / 0.

## Independent adversarial experiments (executed this session, outputs in `/tmp/rev27c/`)

* **Frozen v7 reproduction of the root cause**: re-ran the frozen v7 tool offline on the
  attempt-05 frame + bound detector/geometry → exit 5 `MENU_CONTENT_UNEXPECTED`, rows
  `[選擇項目-, 修改相簿名般, 儲存全部, 刪除相簿t, 分享相簿]`, no candidate; stdout SHA
  `7e92e252…` is byte-identical to the recorded live artifact
  `result-live-positive1.json`. The v7 false negative is fully reproduced offline.
* **v8 CLI replays ×2 each**: attempt-05 `e8f53bd3…`, attempt-13 `b802113b…`,
  attempt-19 `768c5cda…`, decoy-injected attempt-05 `ab4c577a…` — byte-identical per
  pair and equal to the frozen replay/supplemental records.
* **Refusal batch + leak scan**: c07/c08 NOT_FOUND 2, c09/c10/c13/c14 BAD_INPUT 6,
  c15/c16 NOT_ADDRESSABLE 3, c05/c06 5/4 — every refusal output scanned for a
  `candidate` key: none.
* **Full selftest in a /tmp mirror ×2**: results.json SHA reproduced `943f2939…`,
  stdout byte-identical ×2 (`bc9cf22f…`, 327,643 B), all 43 `out/` files byte-identical
  to the repository copies (the repository has a 44th file, the withdrawn c19 scratch,
  which the frozen runner does not reference — as plan §0 states).
* **Injection supplemental in a /tmp mirror ×2**: 11/11 PASS, results SHA reproduced
  `36ebf7a3…`; decoys present in input, absent from candidate; candidate equals the
  current-frame derivation.
* **33 synthetic `evaluate()` probes (round 1)** driving the pure decision core with
  attempt-05-shaped word boxes: all safety-relevant refusals observed with zero
  candidate leaks. Five expectation lines printed by the round-1 script are
  *probe-construction/label artifacts*, each explained: E07/E17/E26 (words merged by
  the row clusterer so the constructed "second target"/"overlap"/"spread" states were
  never actually built), E12 (the "deletion" construction re-encoded the row as the
  6-char reference itself), E14 (ASCII `X` insertion is stripped by the documented
  CJK projection). Corrected constructions were re-run in round 2.
* **13 corrected probes (round 2, F01–F12/F14)**: every expectation met, zero leaks —
  including AMBIGUOUS (target in two rows), deletion refused, mid-insertion refused,
  band overlap → ROW_GEOMETRY_UNSAFE (overlap pair reported), word-center spread →
  ROW_GEOMETRY_UNSAFE, two rows with one substitution each → ELIGIBLE, x-overlap
  boundary exactly 20.0 px accepted / 19.8 px refused.
* **Typed-malformed input probes** (M1/M2 findings below): four geometry variants with
  `window_position_points` not unpackable into two → uncaught ValueError, rc 1, empty
  stdout, no `--out` file; `chosen_bbox` of lexicographically-ordered numeric strings
  → uncaught ValueError at float(); `null` SHA / 3-element bbox / missing field stay
  clean BAD_INPUT 6.
* **Path-string binding probes**: detector binding compares the exact `post` path
  string as well as the SHA — a valid frame passed under a different spelling is
  refused BAD_INPUT 6 (fail-closed); stdout echoes argv, so byte-identity holds per
  identical argv (repo-relative geometry argument yields the same decision, different
  stdout SHA).

## Findings (all non-blocking, fail-closed)

* **M1 — typed-malformed geometry crashes instead of exit 6.** A geometry JSON whose
  `window_position_points`/`window_size_points` is present but not unpackable into two
  numbers raises an uncaught `ValueError` (rc 1, empty stdout, no output file) rather
  than the documented BAD_INPUT 6. Reproduced 3× (length 1, length 4, long string) via
  the frozen CLI. Fail-closed: no candidate, nonzero exit, no partial record. Not in
  the bound 43-case matrix (c18 only covers unparseable JSON, which is clean).
* **M2 — typed-malformed detector bbox crashes.** `chosen_bbox` whose four entries are
  numeric *strings* that pass the lexicographic ordering pre-check (`"c" > "a"`) then
  raises at `float(v)` (rc 1, no output). Narrow and fail-closed; same class as M1.
* **O1 — detector binding includes the exact path string.** Same frame + same SHA via
  a different spelling → BAD_INPUT 6. Fail-closed and deliberate (path + SHA), but the
  future live invocation must pass the detector's recorded string verbatim.
* **O2 — output echoes argv.** Byte-identity requires identical argv strings (this is
  cycle-1 F4/R5, independently re-confirmed); decisions themselves are unaffected.
* **O3 — tolerance wording nuance.** "No insertions/deletions" holds for the window
  comparison, but a non-target row with an inserted glyph at the end/before the last
  reference character can still pass (EXACT containment window or a one-substitution
  shifted window; E13/F03 ELIGIBLE). Mid-row insertions, deletions, and ≥2
  substitutions refuse (F02/F04/E11/E12-intent). Requires the exact five-row structure;
  the candidate still derives from the exact target row only.
* **O4 — documentation nit (already documented in plan §0).** `attempt-01/locator-freeze.json`
  states `refusal_cases: 25`; authoritative from `results.json`: 43 cases, 7 ELIGIBLE,
  36 refusal-verdict, refusal-class 2 (c07/c08), 9/9 global assertions. Verified both
  numbers on disk; plan §0 records the correction.

## Residual risks (carried forward unless marked new)

* RR1: a hypothetical different menu with the same five-row shape, exact 儲存全部 in the
  middle and every non-target row within one glyph would pass (plan §2.4 UNKNOWN,
  bounded by the live gates outside the locator).
* RR2: target is exact-substring containment, so a middle row containing 儲存全部 with
  extra CJK glyphs (e.g. 儲存全部備註, probe F05) is accepted; constrained by the
  exactly-five-row structure and middle position.
* RR3: non-CJK stripping inside the target occurrence (儲存全.部, 儲存全1部 accepted)
  cannot admit a wrong CJK sequence but is a widening vs v7.
* RR4: row-level insertion classes that map to a tolerated window (O3), bounded as above.
* RR5 (new): typed-malformed inputs crash with rc 1 instead of a machine-readable
  BAD_INPUT 6 record (M1/M2). Recommend a future revision add explicit type/shape
  validation and two matrix cases — note that any tool change invalidates the freeze
  and requires a new revision.
* RR6: offline ELIGIBLE confers no live authority; the attempt-05 menu may be gone; a
  future live round must re-derive fresh evidence under a new owner authorization
  citing Rev27c and the v8 SHA (plan §5).
* RR7: the accepted-baseline tripwire (57 files / 17,924,900 bytes / digest
  `b7debe92…`) was not re-derived by this review (the baseline directory is outside the
  repo); attempt-05 scope status records it UNCHANGED.
* RR8: path-spelling sensitivity (O1/O2) for future automated invocation; fail-closed.
* RR9: the withdrawn c19 scratch files remain inside `selftest/fixtures|out`; documented
  as non-binding in plan §0 and unreferenced by the frozen runner, but a naive `out/`
  scan sees a 44th eligible-looking file.

## Plan §0 statements vs disk

Verified on disk: the cycle-1 gate (`PLAN_REVISION_REQUIRED`); the add/withdraw episode
in `attempt-01/run-ledger.json` events (case c19 added at 09:43 → withdrawn at 09:45-09:47,
run_selftest restored byte-exactly to `c94fc407…`, results regenerated ×2 to `943f2939…`,
every `out/` file byte-identical across the runs); the withdrawn fixture/scratch SHAs
(`842cb933…`, `ab4c577a…`) and their absence from the frozen runner; the supplemental
test binding/decoy/11-11/determinism claims; the doc-nit correction. The intermediate
bytes named in the episode (`0dde65b3…`, `c83e2ed6…`) exist only in the ledger/plan
narrative and were not independently re-derived by me (they are overwritten); the
*current* bytes equal exactly the plan-bound SHAs, so the freeze binding is intact.

Also confirmed: `git status` shows no tracked modifications (only untracked trees,
including this review and pre-existing untracked `attempt-11` and `__pycache__` dirs,
left untouched); the attempt-05 round remains unmodified (frozen v7 = `ea09c1ca…`).
Process note: two sibling cycle-2 files (`review-01-top-down.{md,json}`) appeared under
this same `attempt-02` directory while this review was running; they were not written by
me and were not used as evidence (fresh-context independence).

## Not re-derived by this review

The accepted-baseline manifest digest (RR7); the attempt-05 live actions themselves
(impossible offline — but the frozen v7 code re-executed on the same bound inputs
reproduced the live result artifact byte-exactly); the intermediate overwritten selftest
bytes of the add/withdraw episode; cycle-1 findings F1–F6/R1–R8 were read as inputs and
independently re-confirmed where they intersect this checklist (F1–F3 semantics, F4/R5
argv echo, F5 doc-nit, F6 resolution).

## Gate rationale

All 9 checklist items independently pass; every bound SHA matches; the adversarial
probes could not produce a wrong-menu/wrong-row acceptance, a candidate on any refusal,
a historical-coordinate influence, or a nondeterministic run. The findings are
off-contract robustness gaps and wording nuances that stay fail-closed, do not touch
target exactness, structure, geometry safety, candidate derivation, dispatch discipline,
or the freeze binding, and are routed to a future revision rather than blocking this one.
This review approves this exact plan revision and its bound bytes.

PLAN_APPROVED
