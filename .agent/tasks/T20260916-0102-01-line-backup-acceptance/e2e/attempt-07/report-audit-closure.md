# Independent audit — closure verification of the pre-commit corrections (append-only; does NOT modify `report-audit.md`)

- Auditing role: same independent Stage-05 report auditor, continuing (read-only; no GUI; no git commit; all Python runs used `-B`; no repo file written except this one).
- Context: the audited Stage-05 deliverables were corrected in the pre-commit window (zero commits). This file verifies (1) the corrections are faithful, and (2) no other change was smuggled in. It is written append-only; `report-audit.md` (hash below) remains the audit record of the pre-correction SHA and was not touched.
- Method: `shasum -a 256` + `wc -c` on all current and `/tmp` pre-correction copies; `diff` of the pre/post copies; byte-level cell parsing of the six TEST_MATRIX rows against `plan.md` §22.6 and `handoff.md`; JSON parsing of the corrected evidence file; independent read-only destination walk; `git cat-file`-free direct recomputation.

## 0. Audited identities (independently recomputed)

| Object | Reported | Recomputed | Verdict |
|---|---|---|---|
| `e2e/attempt-07/e2e_report.md` (post-correction) | 38,483 B / `6416a5f45d2d39bc056a4729a4a4b097eab4dca801cd417d41aea8d6936aba07` | 38,483 B / `6416a5f4…a07` | MATCH |
| `e2e/attempt-07/evidence/51-baseline-compare.json` (post) | 3,542 B / `6b6c0acd4333dfeba24cf2f6a3effba7f72ea2996a251bb619981df2faf00545` | 3,542 B / `6b6c0acd…545` | MATCH |
| `result.md` (post) | 12,542 B / `bd00d9c9377a01530093e35a158280fb975f66fe493198b6ff315b21223207c0` | 12,542 B / `bd00d9c9…7c0` | MATCH |
| `/tmp/attempt-07_e2e_report_pre_correction.md` | 35,998 B / `03094c12…` | 35,998 B / `03094c12f8eaf860f8adef342836ca436a424978b018e49e5b3d502744283a91` | MATCH |
| `/tmp/attempt-07_e2e_report_pre_renderfix.md` | 37,600 B / `8e12eb1d…` | 37,600 B / `8e12eb1deb16e8e35f348636ab7a44ea67056785e80ae9ef776160dd08099af8` | MATCH |
| `e2e/attempt-07/report-audit.md` (this auditor's prior file) | must be unchanged | 22,275 B / `f78abe9cf07e95b50ba7574da3595bc9bcd074bd306a50dc17a008ceeb01e615` — unchanged | MATCH |
| pre-copies of the other corrected artifacts | — | `/tmp/51-baseline-compare-pre-corr.json` = 1,729 B / `a97588f3…`; `/tmp/result-md-pre-corr.md` = `daf5ba11e41583a5c69a733b52e2ce7010c9041096f4f75f1e0ab6199c73485e` (equals the old `result.md`) | MATCH |

## 1. Diff scope — exactly the promised changes, nothing else

**(1a) `e2e_report.md`:** `diff /tmp/attempt-07_e2e_report_pre_correction.md <current>` yields exactly 4 hunks: (i) L83 (`V22_S5_BOUND_TO_V4_READER` failure-class cell → verbatim text); (ii) L86 (`70-s2-probe-s1|s2.*` → `70-s2-probe-s1\|s2.*`); (iii)–(iv) the two added PRE_COMMIT_CORRECTION bullets (L128–133, plus a trailing blank line; file 136 → 142 lines). The `diff | wc -l` = 15 lines, fully accounted for by these 4 hunks.
- `diff /tmp/attempt-07_e2e_report_pre_renderfix.md <current>` yields exactly 2 hunks: the L86 escape and the second PRE_COMMIT_CORRECTION bullet. No other line moved. — MATCH.
- Nothing else changed: the closure tuple block, the full status tail (`PRIMARY_OUTCOME_STATUS … REPORT_PATH`), the `NEXT_ACTION` line, the STAGE_04_SNAPSHOT block, and all six rows' check-result cells were compared pre/post and are identical (the row-6 result cell differs only by the escaped `\|`, i.e. the same bytes after unescaping). — MATCH.

**(1b) `51-baseline-compare.json`:** `diff /tmp/51-baseline-compare-pre-corr.json <current>` yields only: `destination_inventory.files` `null` → `57` (+ `files_source`); `verdict.files_57` `false` → `true`; and appended top-level `prior_fields`, `correction`, `pre_commit_correction` blocks. Every pre-existing field (`byte_identical: true`, both `ab6747f2…` hashes, `pre_expected` 57/17,924,900, `bytes_17924900: true`, `captured_at_local`, argv, `cmp_argv_recorded`) is byte-unchanged. — MATCH.

**(1c) `result.md`:** `diff /tmp/result-md-pre-corr.md <current>` yields only: one inserted `PRE_COMMIT_CORRECTION` line after L5, and the durable-identities table row for `e2e/attempt-07/e2e_report.md` updated to 38,483 / `6416a5f4…`. The whole NEXT_ACTION region differs by exactly that one table row; Option A/B bullets, the blocker bullet, and the six-column tuple block are byte-identical. — MATCH.

## 2. Six-row policy columns — full byte comparison (all 48 cells)

All six TEST_MATRIX data rows were parsed cell-by-cell (unescape-aware) and compared against `plan.md` §22.6 (lines 208–213) and `handoff.md` (lines 126–131) for all 8 policy columns (`CHECK_ID | Criticality | Evidence role | Gate | Baseline | Failure classification | Waiver allowed | Authority`):
- `V22_SOURCE_RECORD_V1_1_CONFIRMED` — 8/8 byte-identical to plan and handoff.
- `V22_ROUTE_ATTEMPT_06_SINGLE_ONESHOT` — 8/8 byte-identical.
- `V22_S5_BOUND_TO_V4_READER` — 8/8 byte-identical **now** (the previously compressed cell now carries both restored fragments “(§20.2 S10, reused byte-identically per §22.3)” and “from the v4-reader requirement”).
- `V22_AFFIRMATIVE_MACHINE_OBSERVABLE_ONLY` — 8/8 byte-identical.
- `V22_PRIOR_EVIDENCE_IMMUTABLE` — 8/8 byte-identical.
- `V22_SCREEN_SCOPE_PROBE` — 8/8 byte-identical.
No space, punctuation, or wording difference remains in any of the 48 cells (0 mismatches). — MATCH.

## 3. `51` correction — verifiable source for `files = 57` / `files_57 = true`

- `evidence/20260916-baseline/attempt-01/baseline-pre.json`: `destination.entries` length = **57**, `destination.regular_files` = **57**, `destination.total_bytes` = 17,924,900 (independent parse). — MATCH.
- Independent read-only destination walk (2026-09-18): `…/album-2024-05-13_to_2024-05-17_57` = **57 files / 17,924,900 B / 0 zero-byte**, matching `56-frozen-anchors-rehash.json.destination_inventory_recheck` (57 / 17,924,900) and the corrected `files_source` note. — MATCH.
- `byte_identical: true` and both `ab6747f2…` hashes still re-verify (pre file and `/private/tmp/current.json` both `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5`, 19,005 B). — MATCH.
- The new `files_source` text is accurate: the prior `null` was indeed “not populated in this field”, never a negative observation; `prior_fields` faithfully preserves the pre-correction values. — MATCH.

## 4. `result.md` invariants — tuple, NEXT_ACTION, no route claim, table SHA

- Six-column tuple: `PRIMARY_OUTCOME_STATUS: UNKNOWN | IMPLEMENTATION_STATUS: COMPLETE | CORE_ACCEPTANCE_STATUS: BLOCKED | REQUIRED_VERIFICATION_STATUS: PASS | INDEPENDENT_ACCEPTANCE_STATUS: PASS | TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED` + `BASELINE_REGRESSION_DELTA: UNCHANGED` — all 7 lines byte-identical to the pre-correction version. — MATCH.
- NEXT_ACTION region: identical except the one authorized table-row SHA update; the block still ends with the owner-only sentence and “`ROUTE_NOT_NEEDED` was deliberately not taken by this verifier”. — MATCH.
- The route is nowhere claimed as proven: the file says “not positive route evidence … must not be read as the album-level ⋮ being proven” (item 4) and the blocker is `BLOCKED (non-AFFIRMATIVE after the single corrected route attempt)`. — MATCH.
- Durable table SHA for `e2e/attempt-07/e2e_report.md` = 38,483 / `6416a5f45d2d39bc056a4729a4a4b097eab4dca801cd417d41aea8d6936aba07` — matches the actual file byte-for-byte recomputed in §0. — MATCH.
- The inserted `PRE_COMMIT_CORRECTION` line in `result.md` cites only hashes/byte counts that were independently re-verified in §0 (pre 35,998/`03094c12…`; intermediate 37,600/`8e12eb1d…`; final 38,483/`6416a5f4…`; 51 pre 1,729/`a97588f3…`; 51 post 3,542/`6b6c0acd…`). — MATCH.

## 5. Table cell counts

Every TEST_MATRIX table line (header, separator, six data rows) parses as exactly **10 cells** after the `\|` escape (header L79, separator L80, rows L81–L86); the whole table is 8 lines × 10 cells. No other table in the report contains an unescaped in-cell `|` (the remaining pipe-bearing lines are prose outside tables, by design). — MATCH.

## 6. Observations (non-blocking; no correctness impact)

- The `result.md` PRE_COMMIT_CORRECTION line narrates the report's state as “pre 35,998 → post 37,600” before the same line then records the second (rendering-only) fix to 38,483. The 37,600 figure was the real intermediate state (verified against `/tmp/attempt-07_e2e_report_pre_renderfix.md`), so the sequence is accurate, but a reader skimming the first clause could momentarily read 37,600 as final; the second clause and this closure record resolve it.
- The report's own PRE_COMMIT_CORRECTION bullet 3 says a file “cannot embed its own final digest (self-reference)”; `result.md` does record the final digest, so the statement is technically about the file's own bytes. No hash is missing anywhere.
- The correction record is append-only in substance: nothing pre-existing was rewritten except the two cells/fields the corrections legitimately own; the pre-states are preserved both in `/tmp` copies and inside the artifacts themselves (`prior_fields`, `pre_commit_correction`, the `PRE_COMMIT_CORRECTION` bullets).

## FINAL VERDICT

**REPORT_AUDIT_PASS_AFTER_PRE_COMMIT_REPAIR** — 0 MISMATCH, 0 UNVERIFIABLE.

- The single previously raised MISMATCH (TEST_MATRIX “policy columns verbatim” vs the compressed `V22_S5_BOUND_TO_V4_READER` cell) is now fully resolved: all six rows × 8 policy columns are byte-identical to `plan.md` §22.6 and `handoff.md` (48/48 cells).
- The `51-baseline-compare.json` correction is faithful and its new values are backed by independently verifiable sources (baseline-pre `destination.entries`=57 / `regular_files`=57; read-only walk 57 / 17,924,900 B; `byte_identical`/`ab6747f2…` unchanged).
- `result.md`'s tuple, NEXT_ACTION, and no-route-claim language are unchanged; the one table SHA matches the actual file.
- Diff scope is exactly the three permitted edits plus the two correction records; no other line, cell, verdict, gate, or claim changed. Zero commits; frozen artifacts untouched.
- `report-audit.md` remains byte-unchanged (`f78abe9c…`), so the audit trail is preserved append-only.

