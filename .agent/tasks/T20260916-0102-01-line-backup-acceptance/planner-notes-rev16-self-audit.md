# Planner self-audit of Rev16 (input to the next revision; NOT normative)

- Author: Stage-01 Planner role
- Time: 2026-09-16T15:20Z (23:20 local)
- Subject: `plan.md` PLAN_REVISION 16 (CANDIDATE), 178069 bytes,
  SHA-256 `61e1676439b9bb2a5314bd68f0a7d14a0eeb4d9b11af62230e5591c50139384e`
- Status: plan.md was frozen for the in-flight independent reviews `review/attempt-20/` and
  `review/attempt-21/`. This note therefore records findings only and changes nothing. Each item is to be
  folded into PLAN_REVISION 17 together with the attempt-20/21 findings, after their gates are known.

## Method

Mechanical consistency sweep (regex/enumeration cross-checks) plus targeted reading of §16.1–§16.10 and of the
sections those subsections claim to supersede. No product code, fixture or evidence was executed or modified.

## Checked and found consistent (no action)

- No surviving `case-NN/state.json` path anywhere (`rg -c 'case-[0-9]{2}/state\.json'` → 0); §16.1's canonical
  layout is applied mechanically, including the driver-argv paragraph.
- `reconcile:` appears in exactly one grammar form, `reconcile:<relpath>:<sha256>` (3 occurrences).
- `verify.py` survives only as the explicit statement that it never existed (§16.9).
- Goal contract / `PRIMARY_OUTCOME` (§16.8, line 750) and closure/DONE (line 1199) agree on the Rev16 wording.
- New refusal classes each carry an exit code where they are introduced
  (`MISSING_DISPATCHER` 2, `INVALID_STATE_LEGACY` 4, `READBACK_UNCERTAIN` 1,
  `INVALID_VERIFICATION_EVIDENCE`/`VERIFICATION_RUN_MISMATCH` 4).
- Case-root set is stated as `-01`…`-25` in §16.1, §16.7 and the driver-argv paragraph.

## G1 — failure routing and counter oracles were not extended to rows 20–25 (semantic)

- Evidence: the acceptance-matrix section still enumerates routing only for the old rows —
  "Case 01/04/06/08/09/10/11/12 and 13–19 failures are product/test regressions; Case 02/03/05/07 failures stop
  recovery/concurrency acceptance and prohibit production use" (line 1057), and "Counter oracles: case 01 … case 19
  exactly 1; case 10A … 10B …" (line 1061). Rows 20–25 were added by §16.2–§16.7; their inline text states counter
  behaviour for 20, 21, 23, 25 (and 18's positive control) but **not** for 22 and 24, and no routing class is
  assigned to any of 20–25.
- Why it is material: which failing row is a product/test regression versus a wave-stopping recovery/concurrency
  failure is acceptance semantics. Left implicit, the implementer/verifier would have to decide it, which this
  harness forbids.
- Proposed Rev17 disposition: extend line 1057 with the explicit class of each new row
  (proposed: 20 and 23 stop recovery/duplicate-safety acceptance and prohibit production use; 21, 22, 24, 25 are
  TASK_REGRESSION rows) and extend line 1061 with the missing counter oracles
  (22: counter unchanged by all four finalize refusals, i.e. still the state's dispatch count; 24: zero counter
  lines — verify-only never dispatches).

## G2 — status fixture manifest: "18 rows" enumeration versus the nineteenth row (editorial but executable-affecting)

- Evidence: §16.7 adds "a nineteenth row `baseline-worsened` (`baseline_delta=WORSENED`)", while the canonical
  status section still says "The literal manifest enumerates the 18 rows by ID" and lists exactly eighteen IDs
  ending at `done` (line 1162). The new row's literal `--input`/`--output` paths are not stated anywhere.
- Why it matters: the manifest rows in this plan are literal absolute argv; the implementer must not invent one, and
  the two statements contradict each other numerically.
- Proposed Rev17 disposition: change the count to nineteen, append `baseline-worsened` to the ID list with its
  literal `/private/tmp/line-backup-acceptance-status/baseline-worsened.input.json` /
  `…output.json` paths and its `baseline_delta=WORSENED` oracle.

## Next use

After `review/attempt-20` and `review/attempt-21` publish their gates, fold G1/G2 together with their findings into
PLAN_REVISION 17 on the same TASK_ID, then run a fresh independent review of Rev17 (append-only, new attempt dirs).
