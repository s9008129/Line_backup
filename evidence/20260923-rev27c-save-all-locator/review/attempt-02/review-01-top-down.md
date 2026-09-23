# REVIEW 1 (top-down: target identity / geometry / fail-closed) — cycle 2, attempt-02

Reviewer note: fresh-context independent review. Reviewed plan revision: `rev27c-2`.
Date: 2026-09-23. GUI input during this review: **0**. All execution output went to
`/tmp/rev27c-review/`; the repository was read-only except for the two review files in
`review/attempt-02/`. The cycle-1 review (`review/attempt-01/`) was read as an input,
not as an approval.

## 0. Target SHA-256 verification (computed from disk at review time)

| artifact | sha256 |
|---|---|
| `PLAN-2026-09-23-rev27c-save-all-locator.md` | `906e949b34a5f48f46135b240b8b00a1df147a45d30da6e462c2fc4e5b1d8110` |
| `tools/v8/locate_save_all_menu_item.py` | `c5ad46861706a9a2c1c4d477caeda2a809c87c5488844f14a4d3efb34c668a86` |
| `tools/v8/selftest/run_selftest.py` | `c94fc4074f0cd323ee53fe09428b0d38b61af04f5993ceb344acaa02e236f462` |
| `tools/v8/selftest/results.json` | `943f293995b8ecc3f51ad9fc672c1fe899ba37312dc377d14a809ee118affe6a` |
| `replay/replay-record.json` | `2afcd7bec8f6e28826fbf0687c7dd2c604eed7b7746bc854ab2913368ac51540` |
| frozen v7 locator, attempts 02–05 (4 copies) | `ea09c1ca4b97cf2f3a1c210f43a5ae7bc026d1db12bbc12768ff510d60b4012a` each |
| `injection-supplemental/run_injection_case.py` | `cdc8fb0521d2ca9ad57534d7a791633529120f13e1c7e185fcd4e7db585ee9ee` |
| `injection-supplemental/results.json` | `36ebf7a335903a587e975447cb9d6793a25579933e1f054ae6a70aadfcd1aca4` |
| `injection-supplemental/README.md` | `377902059a032d51f2ad5e8e8756ab4fccae96112d01c7bada7a85d83075dc2d` |
| scratch (explicitly NOT bound): `fixtures/geo-a05-injected-history.json` | `842cb93330e3183cf5c3cc7cd28e69b5714084499aa994f49cdc93d7fa2f3418` |
| scratch (explicitly NOT bound): `out/c19-historical-coordinate-injection.json` | `ab4c577a9575b2e937df83f439f09eba06a9f222dc183a5f287bc5730124ba5e` |

Additional on-disk hashes verified during execution: selftest `out/c01` stdout
`c92f4151...`; supplemental `out/clean-control.json` `c92f4151...` and both injected
runs `ab4c577a...`; replay out pairs `e8f53bd3...` (attempt-05), `b802113b...`
(attempt-13), `768c5cda...` (attempt-19); attempt-05 menu frame `2f6bf83d...`;
Gate-A frozen tools v5 ellipsis `6a015ea6...`, v5 verifier `ffa82aed...`, v7 lineage
guard `cdff187e...`, detector `6ae9c250...`.

## 1. Goal baseline (plain language, reconstructed from the plan and on-disk evidence)

In attempt-05 the fresh menu was affirmatively observed and the target 「儲存全部」 was
read cleanly, but the frozen v7 locator refused with `MENU_CONTENT_UNEXPECTED` (exit 5)
and established no candidate because the **non-target** row 修改相簿名稱 was OCR-misread
as 修改相簿名般 (one glyph, conf 49.772). The owner did not authorize a manual override.

**CORE**: replace only the candidate-establishment component with an append-only,
fail-closed v8 locator that closes this false negative while keeping target identity
exact, menu identity / window geometry frame-SHA-bound, every ambiguity refusing with no
candidate, and the candidate derived solely from the current frame's own evidence.
**SUPPORTING**: the unchanged live-route definition and the menu-persistence rule
(design only). **BEST_EFFORT**: none. This round is zero GUI input; an offline ELIGIBLE
is not a live click authorization.

## 2. Method

Read fully: the plan; the v8 tool source line by line; the selftest script and all 43
cases + 9 global assertions; the supplemental test, README and results; the replay
builder and record; attempt-05's live refusal result, scope status and manifest; the
cycle-1 review; the attempt-05 route-runbook.

Ran (all offline, outputs to `/tmp`): the frozen v8 CLI on the attempt-05 frame with the
clean and decoy-injected geometry (x2 each); the three replay frames (x2 each) with the
replay builder's argv forms; the frozen selftest twice in a `/tmp` staging copy (never in
place — it rewrites its own outputs); the supplemental script twice in a `/tmp` copy;
synthetic `evaluate()` probes P1–P21; a +10 pt origin-shift geometry probe; a static
source scan; an attempt-05 manifest re-hash; and repository state checks.

## 3. Checklist 1–9 (each independently confirmed)

1. **Target exactness — PASS.** The target is matched only as an exact substring of the
   row's CJK text (tolerance 0; no similarity matcher). Probes: 儲存全郜 → NOT_FOUND(2);
   儲存全 → NOT_FOUND(2); split target → NOT_FOUND(2); selftest s03/s04/s06/s08, c05.
   Residual containment nuance (F-01) recorded.
2. **Non-target false negative closed — PASS.** Attempt-05 CLI ×2 → ELIGIBLE, exactly one
   candidate `[1297.333, 351.5]`, byte-identical output `c92f4151...` = frozen `c01`
   stdout; tiers `[EXACT, TOLERANT_1_SUB, EXACT, EXACT, EXACT]`. 2-sub row refuses
   (s11/P7); lost char refuses (s12/P19); multiple 1-sub rows pass (s10/P16).
3. **Relaxation cannot pass a wrong menu/row — PASS.** Exactly five CJK item rows in
   reference order, target as `item_rows[2]`. Probes: target physically 4th → exit 5;
   6th CJK row → exit 5; order swap (s15), wrong menu (s07/c05), duplicate context row
   (s25), band overlap → exit 7, low x-overlap → exit 3, whole-screen bbox → exit 6,
   two target rows → exit 4. No refusal case ELIGIBLE; no candidate on any refusal.
4. **Candidate from current frame only — PASS.** Source read plus +10 pt origin-shift
   probe (deterministic shift) and selftest `c04` (+7 pt) in my re-run; three replay
   frames give three frame-specific candidates; all three inputs SHA-bound to the frame.
5. **No historical-coordinate fallback — PASS.** Static scan: zero hits for decoy
   coordinates and GUI/network APIs; only tesseract subprocesses; one write site.
   Supplemental injection test re-executed in `/tmp` ×2: 11/11, `36ebf7a3...`; injected
   output `ab4c577a...` (byte-identical to the withdrawn scratch) decision-identical to
   the clean control; candidate differs from all decoys.
6. **Attempt-05 candidate unique and reproducible — PASS.** CLI ×2 byte-identical with
   one candidate; replay-form runs ×2 byte-identical to the recorded replay out files
   (`e8f53bd3`/`b802113b`/`768c5cda`); a13 candidate equals the historical v7 candidate
   (compared, not input).
7. **Negative matrix refuses — PASS.** Full frozen selftest re-run in a `/tmp` copy ×2:
   43/43 cases, 9/9 globals, `results.json` reproduced as `943f2939`, run-2 byte-identical
   (results, out files, stdout); 36 refusal-verdict + 2 refusal-class cases, none
   ELIGIBLE, none carrying a candidate.
8. **Save All at-most-once — PASS.** The locator never clicks (no input capability; one
   write site `--out`); it emits at most one candidate. Dispatch stays outside: plan §4
   keeps exactly one click, at-most-once, no retry; attempt-05 counters record
   `save_all_used 0/1`, `retry 0`, GUI input 1 (ellipsis).
9. **Chooser excluded — PASS.** Plan §4 ends at observation only (NO chooser
   interaction); §5/§8 exclude `READY_FOR_CHOOSER_GATE_B`; attempt-05 records chooser
   `NOT_OBSERVED` with chooser interaction 0.

## 4. Independent experiments (summary)

- **X01** all bound/disclosed SHAs verified from disk (table above).
- **X02** attempt-05 clean CLI ×2 → `c92f4151`, one candidate.
- **X03** attempt-05 injected CLI ×2 → `ab4c577a`, decision identical to clean, ≠ decoys.
- **X04** replay-form runs ×2 → `e8f53bd3`/`b802113b`/`768c5cda`, equal to recorded files.
- **X05** selftest in `/tmp` copy ×2 → 43/43 + 9/9, `943f2939`, fully byte-identical.
- **X06** refusal audit → no candidate anywhere in refusals.
- **X07** supplemental in `/tmp` copy ×2 → 11/11, `36ebf7a3`, out files reproduced.
- **X08** static scan → no GUI/network/coordinate tokens, one write site.
- **X09** synthetic probes P1–P21 (target/geometry/structure classes).
- **X10** +10 pt origin-shift → deterministic input-following candidate.
- **X11** attempt-05 manifest re-hash → 75/75 consistent, only the status file itself
  outside its own manifest (expected).
- **X12** attempt-05 live result matches plan §2 quotes; counters match §8.
- **X13** plan §4 chain matches route-runbook S1–S11; frozen tool SHAs match; `git status`
  shows no tracked modifications.
- **X14** not re-derived: accepted-baseline digest (outside repo scope), transient
  withdrawn selftest bytes, rev27c-1 plan bytes (see §6).

## 5. Findings (all non-blocking)

- **F-01 target containment (carried F2/R2):** a middle row containing 儲存全部 plus extra
  CJK glyphs is accepted (儲存全部相簿, 不儲存全部 → ELIGIBLE). Same as frozen v7
  containment; no CJK substitution/insertion/deletion in the target; bounded by five-row
  order + middle position + live-route gates.
- **F-02 non-CJK strip widening (carried F3/R3):** 儲存全.部 is accepted (CJK-only
  matching); limited to non-CJK noise; cannot admit a wrong CJK target.
- **F-03 documentation precision (new):** a one-glyph CJK insertion in a non-target row
  can also pass (修改相簿名和稱 → ELIGIBLE) and containment accepts any-length rows,
  while the plan/docstring phrase the boundary as length-equal windows with no
  insertions/deletions. Effective class stays near-identical non-target rows; all hard
  gates unchanged. Wording nit only.
- **F-04 untested class (new):** extra non-CJK rows inside the bbox are not counted as
  item rows (extra Latin row → ELIGIBLE); the candidate stays bounded to the exact target
  row band, so no wrong-row redirect was demonstrated; outside the enumerated matrix.
- **F-05 stale freeze counter (carried F5/R7):** `refusal_cases: 25` in
  `locator-freeze.json`; plan §0 documents it; authoritative counts re-derived
  (43 / 7 / 36 / 2 / 9) and the record is intentionally untouched.
- **F-06 cycle-1 freeze invalidation resolved (carried F6/R8):** current selftest/results
  bytes equal the rev27c-1-bound SHAs; transient bytes not on disk and not re-derived;
  `run-ledger.json` records the add/withdraw; rev27c-2 re-binds the restored bytes plus
  the supplemental test.
- **F-07 revision-delta limit (new):** rev27c-2 cannot be byte-diffed against rev27c-1
  (no snapshot); corroborated by identical locator/selftest/results/replay SHAs,
  unchanged 9-item checklist, and the unchanged live-route chain.

## 6. Residual risks / not re-derived (honest record)

- **R-01** near-identical-menu residual (disclosed in plan §2): a hypothetical five-row
  CJK menu with exact 儲存全部 in the middle and all non-target rows within the bounded
  tolerance would pass; no formal proof it cannot exist; bounded by outside gates.
- **R-02** F-01/F-02 residuals remain; v7-identical or non-CJK-only; not exercised by
  the observed menu.
- **R-03** offline ELIGIBLE ≠ live authority; menu persistence rule applies; any live
  round needs a new owner authorization citing Rev27c + the v8 SHA.
- **R-04** byte-identity holds per fixed inputs/argv (paths are echoed).
- **R-05** unknown future OCR variation refuses conservatively.
- **R-06 not re-derived:** accepted-baseline digest (57 files / 17,924,900 bytes /
  `b7debe92`) because the baseline path is outside this review's repository scope (the
  attempt-05 in-repo evidence and round ledger claim it unchanged); the transient
  withdrawn selftest bytes `0dde65b3`/`c83e2ed6`; the rev27c-1 plan text.
- **R-07** non-locator Gate A components were not executed this round (design only);
  their frozen SHAs match the runbook.

## 7. Verdict

All nine checklist items independently pass against the exact on-disk bytes this plan
binds. The v8 locator closes the attempt-05 false negative while keeping target identity
exact, menu identity and window geometry frame-SHA-bound, every ambiguity refusing, and
the candidate derived only from the current frame's evidence; the relaxed tolerance is
confined to non-target rows and bounded by structure, order, position and geometry. All
bound SHAs match; no tracked repository modifications were introduced by the round; the
supplemental injection test and the full selftest are independently reproducible. The
findings above are documentation-precision or disclosed-residual classes and do not
change the safety decision. This review approves this exact plan revision.

PLAN_APPROVED
