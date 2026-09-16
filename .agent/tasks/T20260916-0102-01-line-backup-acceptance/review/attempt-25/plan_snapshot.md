# LINE album acceptance and reusable transaction process — revised candidate plan

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 18
PLAN_STATUS: CANDIDATE
TASK_CLASS: CRITICAL (persistent-state and safety-semantics changes: dispatch continuity, duplicate/refusal gating, provenance binding, success semantics)
REVIEW_REQUIRED: YES
INDEPENDENT_ACCEPTANCE_REQUIRED: YES
E2E_REQUIRED: NO
E2E_RATIONALE: The only user journey for this album is a read-only verify-only pass over an existing destination; no production download is authorized in this wave. Real CLI, real formal read-only data, real evidence and (if granted) one real GUI observation are used; no fixture result may be reported as production E2E.
ACCEPTED_BY_USER: YES
PRIOR_REVIEW_ATTEMPT: 22, 23
PRIOR_REVIEW_GATE: SPLIT (Rev17 at SHA256 5dd7ab19ce16175fb8e091762d73a50cebb6415ab895342c00a9a015ea1b866f; review/attempt-22 returned PLAN_APPROVED with three non-gating MINOR notes and review/attempt-23 returned PLAN_REVISION_REQUIRED with RV-23-1 MAJOR plus RV-23-2…RV-23-5; Rev18 answers attempt-23 and no approval exists for Rev18)
PRIMARY_OUTCOME_STATUS: UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: IN_PROGRESS

## Revision 18 changes

Wave: **automation verification** (same task, same wave). Rev18 answers the Stage 02 review of Rev17 —
`review/attempt-23` (gate `PLAN_REVISION_REQUIRED`; RV-23-1 MAJOR plus RV-23-2…RV-23-5) — while adopting the two
non-gating bookkeeping notes from `review/attempt-22` (`PLAN_APPROVED`) that name the same literals. §18.1–§18.5 are
normative and each one corrects its paragraphs **in place**; together with §17.1–§17.10 there is no surviving
contradicting literal. Both Rev17 reviews stay invalid for this revision, and no Stage 03 handoff may be compiled from
Rev17.

### 18.1 Legacy Registry axis made single-valued (corrects §17.3 and §16.5; attempt-23 RV-23-1)

The blanket claim "a tolerated-legacy run yields … Registry FAIL … Registry and Source never PASS" is deleted. Registry
is never forced by legacy tolerance and follows the §16.8 axis rule alone: a unique readable match with
`verified_run_id` null (the imported-evidence form, e.g. the matrix `legacy-record` row) is Registry PASS, while the
`CASE_ROOT_25` real-state copy — whose persisted 楨 U+6968 keys never match the requested 禎 U+798E album — and any
unreadable or non-matching run are Registry FAIL. Filesystem PASS is preserved (an independent axis), Source stays
UNRESOLVED, State `LEGACY_PROVENANCE_LIMITED`, overall `UNKNOWN`, exit 4, `failure_class=INPUT_PROVENANCE_LIMITED`. The
v1 sentence "A legacy or unreadable run never becomes Filesystem/Registry/Source PASS" is corrected accordingly: Source
never PASSes, Filesystem may, and Registry only by that axis rule.

### 18.2 Production finalize grammar annotated (corrects the production transaction-forms bullet; attempt-23 RV-23-2 / attempt-22 RV-2)

The production grammar statement now marks `--verification-json` outcome-conditional (required for `--outcome VERIFIED`,
optional for `SAFE_ABORT`), so §17.9's "in both grammar statements" claim is true of both statements.

### 18.3 Reconcile-oracle claim narrowed to the actual oracles (corrects §17.9 and §16.6; attempt-23 RV-23-3)

Case 02's oracle asserts the exact persisted string `reconcile:reconcile.json:<sha256 of its bytes>`; case 03's oracle
asserts only that its idempotent resume writes no new reconcile artifact and leaves the persisted reference unchanged;
the §16.6 grammar remains normative for every reconciliation reference any case writes. No case gains a new assertion
beyond what its oracle text already states.

### 18.4 Stale literals and supersession sentences restated as direct corrections (corrects the closure paragraphs and §16.1/§16.7/§17.8 wording; attempt-23 RV-23-4 / attempt-22 RV-1)

The closure paragraphs now bind Stage 03 to "the current PLAN_REVISION at handoff time (18 at this writing)" and name
"this Revision 18". The §16.1 and §16.7 sentences that read "… is superseded accordingly/by …" and the §17.8 range
sentence are restated as direct corrections ("… was corrected in place to …"), so no leftover supersession sentence
survives the "no new supersession layer" claim.

### 18.5 Nineteenth status row added to the fixture table (corrects the status fixtures table; attempt-23 RV-23-5 / attempt-22 RV-3)

The executable status fixture table gains the `baseline-worsened` row directly after the unchanged-baseline row, with
the §17.6 tuple (PRIMARY `ACHIEVED`, IMPLEMENTATION `COMPLETE`, CORE `PASS`, REQUIRED_VERIFICATION `FAIL`, INDEPENDENT
`PENDING`, CLOSURE `FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION`).

### 18.6 Unchanged by this revision

Everything else, including the goal contract and `PRIMARY_OUTCOME`, closure and `DONE`, the R1–R7 fix contract, cases
01–25 with their literals and oracles, the one human gate, the read-only fences, the three separately reported results,
and all other §17.1–§17.10 decisions.

## Revision 17 changes

Wave: **automation verification** (same task, same wave). Rev17 answers the two independent Stage 02 reviews of Rev16 —
`review/attempt-20` (GATE `PLAN_REVISION_REQUIRED`; RV-1…RV-11) and `review/attempt-21` (GATE `PLAN_REVISION_REQUIRED`;
RV-1 BLOCKER plus RV-2…RV-6) — together with the planner's own Rev16 self-audit
(`planner-notes-rev16-self-audit.md`, items G1/G2, which name the same defects as attempt-20 RV-11/RV-7). Both reviews
confirmed the goal alignment, the read-only fences, the 禎 U+798E / 楨 U+6968 separation, the oracle-before-output
discipline and §16.9's module grounding, and neither relaxed an authority rule. §17.1–§17.10 are normative, and each one
names the paragraphs it corrects **in place** — no new supersession layer and no surviving contradicting literal. Every
earlier approval (Rev13 + attempt-16, Rev14 + attempt-17, Rev15 + attempt-18/19, Rev16 + attempt-20/21) stays invalid for
this revision.

### 17.1 One executable test-mode grammar (corrects attempt-20 RV-1, attempt-21 RV-2)

Every test-mode `transaction` invocation now reads exactly `--project-root CASE_ROOT_NN --config
CASE_ROOT_NN/config/line_backup_config.json --run-log CASE_ROOT_NN/state/run_log.md --state
CASE_ROOT_NN/state/backup_state.json --test-mode` plus its operation arguments, with `NN` = 01…25.

The "test mode uses the same arguments minus `--config`/`--run-log`" sentence in §15.1 is deleted, and the corrected
literal argv replace the old ones in place: the transaction subprocess entry point, the Case-01 prepare / verify-only /
commit / finalize arguments, the closing triple, the Case-04 reference and the Case-07 pair. The four construction rules
of the transaction-acceptance section state the same three canonical children. The two Case-01 verify-only runs
additionally carry `--test-mode` and `--run-id RUN-CASE-01` (§17.2); run 2 repeats run 1's argv byte-identically except
for `--evidence-dir`. `--state CASE_ROOT_NN/state.json` is not legal in any literal, example, construction rule or
oracle.

The five root-bearing literal test-only authority negatives gain present-but-mismatched canonical children
(`--config`/`--run-log`/`--state` resolving to another allowlisted case root), so that the canonical-path mismatch is
what they exercise rather than a missing-argument path; their expected class stays `INVALID_AUTHORITY` exit 2 before any
state read or write. The missing-`--project-root` parser negative and the five production negatives are unchanged.

### 17.2 Verification-evidence chain v2 — acyclic (replaces §16.3's v1 field list; attempt-20 RV-3, attempt-21 RV-1 BLOCKER)

Write order, one direction only:

1. every other artifact of the run (`inventory-1.json`…`inventory-3.json`, plus `error.json` when one is written);
2. `result.json`, carrying `verification_evidence{manifest_path, manifest_bytes}` — never a hash of itself — plus
   `schema_version`, `mode`, `run_id` (null when `--run-id` was absent), `group_key`, `fingerprint`, `destination`,
   `filesystem_status`, `recognized_images`, `expected_images`, `overall_status`, `exit_code`, `artifact_readback`;
3. `manifest.json` written last, carrying `artifacts[]` — every artifact of that run **including `result.json`** and
   excluding only `manifest.json` itself, each entry `{path, bytes, sha256}` with `path` relative to the evidence dir —
   plus `result_summary` (the same eleven verdict fields as step 2) and `result_bytes`/`result_sha256` for the result it
   just recorded.

Hashing convention: SHA-256 over raw file bytes, lowercase hex. No serialization, canonicalization or field-exclusion
rule is needed, and `manifest_sha256` is never recorded inside `result.json`, because the write order forbids it.

`commit` and `finalize` recompute in this order before applying any other gate: read the exact bytes at the
`--verification-json` path → locate `manifest.json` beside it → validate the manifest shape → require its
`result_summary`, `result_bytes` and `result_sha256` to equal the result's fields and bytes exactly → require the
manifest's `result.json` entry to re-hash to those bytes → re-hash every other listed artifact at its recorded path →
then apply the F3 gates. Any missing, malformed or mismatching element is `INVALID_VERIFICATION_EVIDENCE`; evidence whose
`run_id`, `group_key`, `fingerprint` or `destination` belongs to another run is `VERIFICATION_RUN_MISMATCH`; both exit 4,
no revision change, no registry entry, no lock leak.

Honest scope of the guarantee (this replaces the v1 claim "A payload that merely looks like a result … cannot finalize
anything"): the chain proves internal consistency, completeness and post-hoc integrity of that verify run's evidence
directory. It is not an authorship proof and does not survive a writer who may rewrite that directory. What it does
forbid is every payload without a chain, and every chain that disagrees with its result in any field or byte. Rows 22a–d
stand, and **22e** (a self-consistent hand-authored chain whose manifest `result_summary` disagrees with its result) and
**22f** (a genuine chain with one `result.json` byte flipped after the manifest was written) make the enforceable part
executable.

`verify-only` gains optional `--run-id`: when supplied it is copied into `result.run_id`; when absent, `run_id` is null
and neither `commit` nor `finalize` may consume that result. Driver-captured `stdout.log`, `stderr.log` and `exit-code`
are never part of the chain: the manifest covers only the artifacts the product writes into that evidence directory, and
the acceptance driver hashes its own captures separately.

### 17.3 Legacy contract single-valued (§16.5 corrected in place; attempt-20 RV-2, attempt-21 RV-5/RV-6)

- Validation scope is exactly §16.5's (i) the payload about to be replaced and (ii) every new RC2 record. The authority
  section's universal "at every load … refused with no write" sentence is amended in place to that scope; reading an
  existing authority state is never gated by it.
- The `prepare`-may-append exception is **deleted**: any mutation whose target state contains at least one run that is not
  strictly valid is refused `INVALID_STATE_LEGACY` exit 4 with no write. The real formal state therefore stays readable
  and cannot be mutated by this wave, and 25b is its executable oracle.
- Read-only mapping is unified with the existing product output and the verifier-contract section: a tolerated-legacy or
  unreadable run yields Filesystem PASS preserved (an independent axis), Source UNRESOLVED, State
  `LEGACY_PROVENANCE_LIMITED`, overall `UNKNOWN`, exit 4, `failure_class=INPUT_PROVENANCE_LIMITED`. Registry is never
  forced by legacy tolerance and follows the §16.8 axis rule alone: a unique readable match with `verified_run_id` null
  (the imported-evidence form, e.g. the matrix `legacy-record` row) is Registry PASS, while the `CASE_ROOT_25`
  real-state copy (persisted 楨 U+6968 keys never match the requested 禎 U+798E album) and any unreadable or
  non-matching run are Registry FAIL (Rev18 §18.1). The v1 sentence "A legacy or unreadable run never becomes
  Filesystem/Registry/Source PASS" is corrected: Source never PASSes, Filesystem may, and Registry only by that axis
  rule.
- `legacy_normalizations[]` is pinned as an array of `{run_id, kind, detail}` with `kind ∈ {calibration.extra_keys,
  calibration.missing, contract_revision.missing, UNREADABLE_LEGACY}`; every tolerated or unreadable run appears exactly
  once, and an `UNREADABLE_LEGACY` run is additionally named in the scoped blocker. 25a asserts that exact list.

### 17.4 user_fact v1 equality anchors (§15.2 corrected in place; attempt-20 RV-4, attempt-21 MINOR-2)

For `user_fact:` the artifact must be the §16.4 v1 record, and the equality anchors are `app_identifier`,
`raw_requested_group` (byte-for-byte; 禎 U+798E is never equal to 楨 U+6968) and `fingerprint` on all three fields. No
`group_key` key is required or consulted on the record; the request's key is compared only against
`"line:" + app_identifier + ":" + raw_requested_group` reconstructed from the record. §15.2's Rev13-format clause is
replaced accordingly, and the preserved `evidence/20260916-user-fact/source-identity-user-fact.json` remains evidence
only: it can never yield `CONFIRMED`.

### 17.5 Case 20 orphan semantics (§16.2 corrected in place; attempt-20 RV-5)

The dispatcher is a child process (`subprocess.run` in `transaction.py`), so killing prepare does not kill it. The
fixture adapter is pinned to self-exit on reparenting: after writing its counter line and `dispatch-started.barrier` it
polls `os.getppid()` every 0.25 s and exits by itself within ≤10 s of the parent's death (macOS reparents the orphan, so
`getppid()` changes). The driver waits (bounded ≤10 s) for that exit, records the observed reparenting, and then asserts:
exactly one counter line and no further bytes; state bytes byte-identical to the independently hashed revision-1 bytes;
no revision-2 record; `save_all_retry_allowed=false`; and, **within `CASE_ROOT_20/state/`**, the only remainder is the
empty `.line-backup-state.lock` control file. The protocol-mandated `dispatch-started.barrier`,
`dispatch-counter.jsonl` and the driver's own process records sit outside that claim and are retained as evidence. If the
adapter is still alive after 15 s the driver kills it and records `orphan-forced-kill`; that is a fixture failure
(TASK_REGRESSION), never an accepted path.

### 17.6 The nineteenth status row (§16.7 and the status-manifest enumeration corrected in place; attempt-20 RV-7, attempt-21 RV-4, planner G2)

Row `baseline-worsened`, with the literal paths `/private/tmp/line-backup-acceptance-status/baseline-worsened.input.json`
and `/private/tmp/line-backup-acceptance-status/baseline-worsened.output.json`: a valid `baseline_artifact` (SHA-256 and
byte length), `baseline_delta=WORSENED`, and the newly appeared or worsened signature disclosed. Expected tuple: PRIMARY
`ACHIEVED`, IMPLEMENTATION `COMPLETE`, CORE `PASS`, REQUIRED_VERIFICATION `FAIL`, INDEPENDENT `PENDING`, CLOSURE
`FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` — per workflow-routing §7.7 rule 8 a worsened
baseline is a must-not-break violation, never `INCOMPLETE`/`PENDING_REQUIRED_VERIFICATION`. The manifest enumeration
reads nineteen rows and lists `baseline-worsened` directly after `baseline-unchanged`.

### 17.7 Failure routing and counter oracles for rows 20–25 (attempt-20 RV-11, planner G1)

Routing: failures of **20** and **23** stop recovery/duplicate-safety acceptance and prohibit production use (the same
class as 02/03/05/07); failures of **21, 22, 24, 25** are product/test regressions. Counter oracles: 20 — exactly one
line before the kill and still exactly one after recovery; 21 — zero; 22 — untouched by all six finalize refusals (the
setup's single dispatch line is still the only line); 23a — zero, 23b — zero, 23c — exactly one; 24 — zero (verify-only
never dispatches); 25a — zero, 25b — zero.

### 17.8 Evidence roots, ranges and headings corrected (attempt-20 RV-10, attempt-21 RV-3, MINOR-1, MINOR-3)

The product verify command targets `evidence/20260916-product-verify/attempt-04`, and the baseline copy targets
`evidence/20260916-baseline/attempt-02`; every `attempt-01` root stays read-only provenance. The former `-01`…`-19`
ranges were corrected in place to `-01`…`-25` (Rev18 §18.4). The planned-file heading reads "Planned implementation
files (existing modules are modified in place;
`run_all.py` is new)" and §16.9 remains authoritative for the file set. The two-order Phase-2 wave is pinned inside
§16.10's `attempt-02/` as `attempt-02/order-ownership-first/` and `attempt-02/order-driver-first/`, each with its own
per-driver subdirectories and its own `readback-verification.json`, so neither order can overwrite the other.

### 17.9 Minor corrections absorbed (attempt-20 RV-6, RV-8, RV-9; attempt-21 MINOR-4/5/6)

- Case 07: the winner performs exactly two guarded replacements, the loser exactly zero, and the counter gains exactly
  one line overall.
- `finalize`'s `--verification-json` is outcome-conditional in both grammar statements: required for `--outcome VERIFIED`,
  optional for `SAFE_ABORT` (when supplied it must still be a readable JSON object, and it is never consulted for
  SAFE_ABORT success).
- The case-02 oracle asserts the exact persisted reference string `reconcile:reconcile.json:<sha256 of its bytes>` and
  the case-03 oracle asserts only that its idempotent resume writes no new reconcile artifact and leaves the persisted
  reference unchanged; the §16.6 grammar stays normative for every reconciliation reference any case writes
  (Rev18 §18.3).
- The reconcile artifact is pinned: the process writes the persisted record to `<operation --evidence-dir>/reconcile.json`
  for its first reconciliation write in that directory, and `reconcile-2.json`, `reconcile-3.json`, … afterwards; the
  persisted reference is `reconcile:<that file name>:<sha256 of its bytes>`.
- `reconciliations[].original_observation` is pinned to `reference = "intent-checkpoint:<run_id>:rev<revision>"` (the
  loaded intent checkpoint's own run and revision) with `trigger_outcome="UNKNOWN"` and
  `manual_reconciliation_required=true`; the schema's free-string field is used as-is, never extended.

### 17.10 Unchanged by this revision

The goal contract and `PRIMARY_OUTCOME` (§16.8), closure and `DONE`, the R1–R7 fix contract, the substantive semantics
of cases 01–19 (with only the literal and grammar corrections named in §17.1–§17.3 and §17.9), the one human gate, the
read-only fences, and the three separately reported results.

## Revision 16 changes

Wave: **automation verification** (same task, same wave). Rev16 answers the two independent Stage 02 reviews of Rev15 —
`review/attempt-18` (GATE `PLAN_REVISION_REQUIRED`; A-RV-1 BLOCKER plus A-RV-2…A-RV-13) and `review/attempt-19`
(GATE `PLAN_REVISION_REQUIRED`; B-RV-1…B-RV-8). Both reviews confirmed every attempt-17 finding (F-1…F-8) closed and
found no goal, safety, authority or read-only-fence relaxation. §16.1–§16.10 are normative and supersede the specific
older text named in each subsection; everything else in Rev15 and the Rev14 base contract stands unchanged. Every
earlier approval (including Rev13 + attempt-16, Rev14 + attempt-17 and the attempt-18/19 reviews of Rev15) remains
invalid for this revision.

### 16.1 One canonical case-root layout and one state file (fixes A-RV-1, BLOCKER)

Every literal case root `CASE_ROOT_NN = /private/tmp/line-backup-acceptance-case-NN` (NN = 01…25) now has exactly this
fixture layout, created before the case runs:

- `CASE_ROOT_NN/config/line_backup_config.json` — the canonical 10-key config shape (`schema_version=2`,
  `backup_root=CASE_ROOT_NN/backups`, `app_identifier=jp.naver.line.mac`, the case's exact group key).
- `CASE_ROOT_NN/state/backup_state.json` — **the single authoritative state file**. Every `transaction` and every
  `verify-only` process of that case reads and writes exactly these bytes; no other state path exists.
- `CASE_ROOT_NN/state/run_log.md` — present and readable; the product never writes it.
- `CASE_ROOT_NN/input-state.json` — the fixture **source** for the pre-state only (meaning unchanged); the driver
  installs it into `state/backup_state.json` before the case's first process and never afterwards.
- `CASE_ROOT_NN/evidence/` — the case's evidence dir; `CASE_ROOT_NN/destination/`, `dispatcher-*.py`,
  `dispatch-counter.jsonl`, barriers and the §16.3 verification result live under the same root.

Transaction test mode therefore reads `--project-root CASE_ROOT_NN --config
CASE_ROOT_NN/config/line_backup_config.json --run-log CASE_ROOT_NN/state/run_log.md --state
CASE_ROOT_NN/state/backup_state.json --test-mode`. The three children are required and must equal the canonical
children exactly; `--state CASE_ROOT_NN/state.json` is no longer legal anywhere in this plan, and the former
"test mode omits config/run-log" rule is deleted. Authority validation remains the first filesystem operation.

Verifier test mode is extended from the single `/private/tmp/line-backup-acceptance-verifier` root to exactly that root
∪ `CASE_ROOT_NN` for NN = 01…25. Every other verify-only rule is unchanged (canonical children, `--test-mode` required
for fixture roots, production roots rejected in test mode, writes confined to `--evidence-dir`). The product authority
constant must therefore enumerate `-01`…`-25`; dynamic roots stay rejected.

Why this was blocking: Rev15's Case 01 ran `verify-only` against `CASE_ROOT_01/state.json` with no case config, which
the authority rule refuses (`INVALID_AUTHORITY`, exit 2, before any read). Case 01's closed loop is now executable
end-to-end: `prepare` (adapter pair) → `verify-only --test-mode` on the same canonical state (writing
`evidence/verify-1/result.json` and `evidence/verify-1/manifest.json` per §16.3) → `commit --verification-json
CASE_ROOT_01/evidence/verify-1/result.json` → `finalize --outcome VERIFIED` → `verify-only` run 2 on the same argv
(closed loop, `source_status=CONFIRMED`) → duplicate-check `SKIP_DUPLICATE` → same-fingerprint different-destination
prepare refused → terminal `resume` `SKIP_TERMINAL`. All literal Case-01 argv in this plan use this shape, and every
line that named `CASE_ROOT_NN/state.json` or "through -19" was corrected in place to the canonical children and
"through -25" (Rev17 §17.1/§17.8; Rev18 §18.4).

### 16.2 Case 20 — the real parent-SIGKILL in the dispatch window (fixes A-RV-2, B-RV-5)

`CASE_ROOT_20` (`parent-kill-in-dispatch-window`) reproduces R1 post-fix without any pre-announced fault flag:

- Adapter `CASE_ROOT_20/dispatcher-blocking.py` appends exactly one counter line to
  `CASE_ROOT_20/dispatch-counter.jsonl`, creates `CASE_ROOT_20/dispatch-started.barrier`, then blocks for up to 300 s
  waiting for `CASE_ROOT_20/release.barrier`, which the driver never creates — while polling `os.getppid()` every
  0.25 s and exiting by itself within ≤10 s of reparenting, because the dispatcher runs as a child process, not
  in-process (Rev17 §17.5).
- Driver: waits (bounded, ≤ 60 s) for `dispatch-started.barrier`; independently re-reads the state file and requires
  revision 1, `intent_state=INTENT_COMMITTED`, `dispatch_state=NOT_ATTEMPTED`, `intent.dispatch_outcome=NOT_ATTEMPTED`
  and exactly one counter line; then sends `SIGKILL` to the prepare process — the child dispatcher survives the kill and
  is observed to reparent and self-exit (§17.5; if it is still alive 15 s later the driver kills it and records
  `orphan-forced-kill`, a fixture failure and TASK_REGRESSION, never an accepted path) — and records the kill, the
  signal and the raw process artifacts.
- Kill-aftermath oracle: exactly one counter line and no further bytes; state bytes byte-identical to the independently
  hashed revision-1 bytes; no revision-2 record; `save_all_retry_allowed=false`; and, **within `CASE_ROOT_20/state/`**,
  the only remainder is the empty control file `CASE_ROOT_20/state/.line-backup-state.lock`, which is never an authority
  signal and must not block the next process (`flock` is released by process death). The protocol-mandated
  `dispatch-started.barrier`, `dispatch-counter.jsonl` and the driver's own process records sit outside that claim and
  are retained as evidence (Rev17 §17.5).
- Recovery oracle: one fresh `resume --no-dispatch` (`--expected-revision 1`, `--expected-owner-id WRITER-CASE-20`)
  returns `RECOVERY_NO_DISPATCH` exit 0 with `reconciliation_state=BARRIER_COMMITTED`, `state_replaced=true`, revision
  2, one schema-valid `reconciliations[]` entry and **no** second counter line; the following `commit
  --expected-revision 2` returns `CONFLICT_UNRESOLVED_DISPATCH` exit 4 with no write.
- Equivalence (B-RV-5): this state is byte-shaped identically to the case-02 `--crash-after-dispatch` state (revision 1,
  `INTENT_COMMITTED`, `NOT_ATTEMPTED`, one counter line) and shares the same row-4 recovery; case 20 differs only in
  that no product process survives to print a result, so the driver asserts the state and counter, never a prepare
  return code. Case 20 is the R1 proof; cases 02/03 remain the product-visible return-code proofs.

### 16.3 Verification-evidence contract and the finalize negative rows (fixes A-RV-3; the v1 field list is corrected in place by Rev17 §17.2)

`finalize --outcome VERIFIED` accepts only a verification result carrying the verifier's own acyclic evidence chain
(Rev17 §17.2 is normative):

- `result.json` written by `verify-only`, with `mode="verify_only"`, `run_id`/`group_key`/`fingerprint`/`destination`
  matching the run, `filesystem_status="PASS"`, `recognized_images == expected_images`, and a `verification_evidence`
  object `{manifest_path, manifest_bytes}` — never a hash of itself.
- `manifest.json` written last beside it (`evidence/<verify-run>/manifest.json`), listing every artifact of that verify
  run **including `result.json`** (each entry `{path, bytes, sha256}`, `path` relative to the evidence dir) plus
  `result_summary` (the same verdict fields as the result) and `result_bytes`/`result_sha256` for the result it just
  recorded.
- finalize (and commit) recompute, before any write: the sha256/bytes of the exact result bytes it read, then require the
  manifest's `result_summary`/`result_bytes`/`result_sha256` to equal the result exactly, its `result.json` entry to
  re-hash to those bytes, and every other listed artifact to re-hash at its recorded path. Any missing or mismatching
  element is refused; a result whose `run_id` is null (no `--run-id` on verify-only) is not consumable.

Refusal classes stay as F3: `INVALID_VERIFICATION_EVIDENCE` (structure/status/count/chain defects) and
`VERIFICATION_RUN_MISMATCH` (evidence belonging to another run), both exit 4, no revision change, no registry entry, no
lock leak. The chain proves internal consistency, completeness and post-hoc integrity of that verify run's evidence
directory; it is not an authorship proof and does not survive a writer who rewrites that directory. What it forbids is
every payload without a chain and every chain that disagrees with its result in any field or byte (Rev17 §17.2 replaces
the v1 "merely looks like a result" claim).

`CASE_ROOT_22` (`finalize-verification-negatives`) runs six literal sub-rows, each from a fresh isolated state at
revision 2 with a completed dispatch record: 22a hand-authored PASS/57 JSON with no evidence chain →
`INVALID_VERIFICATION_EVIDENCE` exit 4; 22b a real `verify-only` FAIL/0 result over an empty destination with a full
chain → `INVALID_VERIFICATION_EVIDENCE` exit 4; 22c `{}` → `INVALID_VERIFICATION_EVIDENCE` exit 4; 22d another run's
real result → `VERIFICATION_RUN_MISMATCH` exit 4; 22e a self-consistent hand-authored chain whose manifest
`result_summary` disagrees with its result → `INVALID_VERIFICATION_EVIDENCE` exit 4; 22f a genuine chain with one
`result.json` byte flipped after the manifest was written → `INVALID_VERIFICATION_EVIDENCE` exit 4. Every sub-row
additionally asserts unchanged state bytes, unchanged revision, unchanged registry length and one refusal artifact under
the case evidence dir.

### 16.4 The user-fact CONFIRMED record contract v1 (fixes A-RV-4 / B-RV-2, bounds the join path)

The preserved artifact `evidence/20260916-user-fact/source-identity-user-fact.json` stays exactly as it is: evidence
only (`status=PARTIAL`, part 2 `UNANSWERED`, `*_at_recording` keys, `facts.app_bundle`, no `app_identifier`, no
`fingerprint`). It can never yield `CONFIRMED` and is never rewritten.

A record supports `source_status=CONFIRMED` only in this exact v1 form, authored by the operator from the one-shot
human-gate answer, stored under the WORK root at
`evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.json` (never rewritten; a later answer is a new
versioned file):

```json
{"record_version":"1.0","kind":"source_identity_user_fact","status":"CONFIRMED",
 "source_correspondence_result":"CONFIRMED","merge_prohibited":true,
 "app_identifier":"jp.naver.line.mac",
 "raw_requested_group":"旻謙允禎成長日記","raw_persisted_group":"旻謙允楨成長日記",
 "fingerprint":{"start_date":"2024-05-13","end_date":"2024-05-17","expected_images":57},
 "question":{"text":"<the exact question asked>","asked_at_local":"<timestamp>"},
 "answer":{"raw":"<the answer verbatim>",
           "part_1":{"text":"<...>","raw":"<...>"},
           "part_2":{"text":"<...>","raw":"<...>","confirms_same_source":true,
                     "confirmed_group_string":"旻謙允禎成長日記",
                     "confirmed_album":"2024/05/13～05/17","confirmed_expected_images":57}},
 "supplied_by":"<who answered>","recorded_at_local":"<timestamp>",
 "evidence":[{"path":"/absolute/path","bytes":123,"sha256":"<64 hex>"}]}
```

Matching rules — all exact, no normalization, no similarity: `status` and `source_correspondence_result` are
`CONFIRMED`; `merge_prohibited` is `true`; `app_identifier` equals the requested app; `raw_requested_group` equals the
requested group string byte-for-byte (U+798E 禎 is never compared equal to U+6968 楨); `fingerprint` equals the request
fingerprint on all three fields; `answer.part_2.confirms_same_source` is `true` and its three confirmed values equal the
requested group string, the requested album label and the expected count; `question.text` and `answer.raw` are
non-empty; `evidence[]` is non-empty and every artifact re-hashes at its recorded absolute path to the recorded
bytes/sha256. `raw_persisted_group` is evidence-only: never used for matching, never written into any key, never a basis
for merge. A record with a missing key, an unknown key, or any failed equality yields `UNRESOLVED` (or
`INVALID_SOURCE_EVIDENCE` when it fails the record schema during `prepare`); there is no partial match.

Base resolution (supersedes the Rev15 table): `user_fact:<relpath>` resolves against the WORK root in production and
against the case `--project-root` in test mode; `join:` resolves against the WORK root (production only); `fixture:`
resolves against the case `--project-root` (test mode only). The record validation rules are identical in both modes.

The `join:` path is bounded the same way: a join artifact may yield `CONFIRMED` only when its parsed content carries
`join_authority="authoritative_exact_join"` plus the same equality anchors (app, group string, all three fingerprint
fields); no such artifact exists today and, absent `join_authority`, the result is `UNRESOLVED`.

`CASE_ROOT_24` (`user-fact-source-closure`) runs verify-only fixtures over a terminal VERIFIED run whose binding is
`user_fact:`: 24a a CONFIRMED v1 record (evidence artifact inside the case root) → `source_status=CONFIRMED`,
`source_kind=user_attestation`, Filesystem/Registry/State PASS, overall PASS, exit 0; 24b the same record with part 2
`UNANSWERED` → Source UNRESOLVED exit 4; 24c the same record with `raw_requested_group` written with 楨 → Source
UNRESOLVED exit 4 (merge guard); 24d the same record with one evidence byte mutated → Source UNRESOLVED
(`INPUT_PROVENANCE_LIMITED`) exit 4.

### 16.5 Validation scope and the read-only legacy contract (fixes A-RV-12)

Strict `$defs/run`/`$defs/state` validation applies to (i) every payload the product is about to replace and (ii) every
new RC2 record. It does **not** gate reading an existing authority state.

Read-only operations (`verify-only`, `status evaluate`, `duplicate-check`) load state under this legacy read contract,
which never rewrites anything:

- Enumerated legacy shapes are tolerated and reported per run in the result's `legacy_normalizations[]`:
  `intent.calibration` carrying extra keys (e.g. `first_row_point`, `row_step`) → `calibration.extra_keys`; a missing
  `intent.calibration` → `calibration.missing` with calibration reported `UNKNOWN`; a missing `contract_revision` →
  `contract_revision.missing` (pre-RC2). Every entry is the pinned §17.3 form `{run_id, kind, detail}`, one per affected
  run.
- Any other strict-schema deviation makes that run `UNREADABLE_LEGACY` (the fourth pinned `legacy_normalizations[]`
  kind): reported, never repaired, with the album's State axis `LEGACY_PROVENANCE_LIMITED` and the run named in the
  scoped blocker. Never a crash, never a rewrite.
- A tolerated-legacy or unreadable run yields Filesystem PASS preserved (an independent axis), Source UNRESOLVED, State
  `LEGACY_PROVENANCE_LIMITED`, overall `UNKNOWN`, exit 4 and `failure_class=INPUT_PROVENANCE_LIMITED`. Registry follows
  only the §16.8 axis rule (Rev18 §18.1): the imported-evidence form (unique readable match, `verified_run_id` null) is
  Registry PASS, while the `CASE_ROOT_25` real-state copy (楨 U+6968 keys ≠ the requested 禎 U+798E album) and any
  unreadable or non-matching run are Registry FAIL. Source never PASSes; Filesystem may. Rev17 §17.3 as corrected by
  Rev18 §18.1 replaces the former "never becomes Filesystem/Registry/Source PASS" / `NOT_ACHIEVED` wording, exactly as
  the real-state pass already specifies.

Mutation operations (`prepare`, `commit`, `finalize`, `resume`) load state strictly: any state containing at least one
run that is not strictly valid is refused `INVALID_STATE_LEGACY` exit 4 with no write — the former `prepare`-may-append
exception is deleted (Rev17 §17.3). The real formal state therefore stays readable and can never be mutated by this
wave.

`CASE_ROOT_25` (`legacy-real-state-shape`) holds a read-only copy of the real formal state's shapes — one run with the
extra calibration keys, one run without calibration, four runs without `contract_revision`, the real 楨 group key — plus
a 57-file destination: 25a `verify-only --test-mode` → Filesystem PASS / Registry FAIL (no association match for the
requested 禎 album, per the §16.8 axis rule; Rev18 §18.1) / Source UNRESOLVED / State `LEGACY_PROVENANCE_LIMITED`,
overall `UNKNOWN`, `failure_class=INPUT_PROVENANCE_LIMITED`, exit 4, state bytes unchanged, and
`legacy_normalizations[]` exactly the §17.3 array `{run_id, kind, detail}` naming every normalized or unreadable run;
25b `transaction prepare` against the same state → `INVALID_STATE_LEGACY` exit 4, no write, no counter line.

### 16.6 Dispatch-continuity details: one reconcile grammar, refusal precedence, path conversion

- **One grammar, one base** (A-RV-7 / B-RV-1): the persisted `reconciliations[].evidence` reference is exactly
  `reconcile:<relpath>:<sha256>` and always resolves inside the operation's own `--evidence-dir`; it is not a source
  binding and never participates in `source_status`. The `<kind>`-bearing form and the "§15.2 base rules" phrase are
  deleted. The case-02 oracle asserts the exact persisted string form of the reference it produces; case-03 asserts
  that its idempotent resume writes no new artifact and leaves the persisted reference unchanged (Rev18 §18.3).
- **Deterministic prepare refusal precedence** (A-RV-8): authority validation → `MISSING_SOURCE_EVIDENCE` →
  `MISSING_DISPATCHER` → `INVALID_SOURCE_EVIDENCE` → precondition refusals (`CONFLICT_ACTIVE_RUN`,
  `CONFLICT_DUPLICATE`, `CONFLICT_DUPLICATE_FINGERPRINT`, `AMBIGUOUS_FINGERPRINT`, `NEEDS_RECONCILIATION`) →
  `PREPARED`. When both `--source-evidence` and the adapter pair are absent the class is `MISSING_SOURCE_EVIDENCE`
  (record load precedes adapter-flag evaluation).
- **Binding path conversion** (A-RV-8): `binding.artifact.path` is absolute or relative to the binding base and is
  stored as a normalized POSIX `<relpath>` under that base. A path resolving outside the base, containing `..`, passing
  through a symlink, or not expressible as a normal relative path is `INVALID_SOURCE_EVIDENCE` exit 2.
- **`blocking_intent_released=true` derivation**: the SAFE_ABORT finalization path may write the release only from
  verified no-dispatch observations — `save_all_invocation_attempted=false`, `save_all_click_count=0`,
  `folder_chooser_appeared=false`, `download_started=false`, `failure_boundary` ∈ {`ELLIPSIS_CLICK`,
  `BEFORE_SAVE_ALL_INVOCATION`}, and an independently read counter delta of 0 for that run; it must never be written
  for a run whose dispatch axis is attempted or unknown.
- **Case 07 replacement count** (A-RV-5): the winner performs exactly **two** guarded replacements (intent 0→1,
  dispatch record 1→2) and the loser exactly zero; the counter gains exactly one line overall.

### 16.7 Additional literal rows and pinned pre-states

- **Case 21** (`missing-dispatcher`, B-RV-8/A-RV-8): `prepare` with `--source-evidence` but without
  `--dispatcher`/`--dispatch-counter` → `MISSING_DISPATCHER` exit 2, no write, no counter line, state bytes unchanged.
- **Case 23** (`prepare-storage-faults`, A-RV-6) with a test-only `--storage-fault-slot intent|dispatch` selector:
  23a `--storage-fault WRITE_BEFORE_REPLACE --storage-fault-slot intent` → exit 1, revision 0, zero counter lines, no
  partial write; a following fresh `prepare` returns `PREPARED` revision 2 with exactly one counter line. 23b
  `--storage-fault READBACK_UNCERTAIN_AFTER_REPLACE --storage-fault-slot intent` → the intent replacement is committed,
  the first process returns `READBACK_UNCERTAIN` exit 1 at revision 1 with zero counter lines, a fresh `resume
  --no-dispatch` returns `RECOVERY_NO_DISPATCH`/`BARRIER_COMMITTED` at revision 2, and `commit` returns
  `CONFLICT_UNRESOLVED_DISPATCH` exit 4. 23c `--storage-fault WRITE_BEFORE_REPLACE --storage-fault-slot dispatch` →
  the adapter ran (exactly one counter line) and the post-dispatch replacement failed: exit 1, revision 1,
  `dispatch_performed=true`; a fresh `resume --no-dispatch` returns `RECOVERY_NO_DISPATCH`/`BARRIER_COMMITTED` at
  revision 2 with still exactly one counter line.
- **Case 18 pre-state pinned** (A-RV-9): the historical non-terminal same-fingerprint intent carries
  `active_writer_id=null` and `context_lock=null` (no live run), so `NEEDS_RECONCILIATION` fires and
  `CONFLICT_ACTIVE_RUN` cannot.
- **Case 19 / Case 10B verification JSON** (A-RV-9 / B-RV-6): `--verification-json` is outcome-conditional — required
  for `--outcome VERIFIED`, optional for `--outcome SAFE_ABORT`; when supplied with SAFE_ABORT it must be a readable
  JSON object (`INVALID_INPUT` exit 2 otherwise) but is never consulted for success, and the canonical 10B/19 rows omit
  it. SAFE_ABORT semantics are otherwise unchanged (revision 3, no registry entry, unresolved intent preserved).
- **Status fixtures** (A-RV-10): the executable status manifest gains a nineteenth row `baseline-worsened`
  (`baseline_delta=WORSENED`) whose oracle asserts the must-not-break routing — REQUIRED_VERIFICATION `FAIL`, CLOSURE
  `FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION`, scoped blocker, no DONE (Rev17 §17.6; never
  `INCOMPLETE`/`PENDING_REQUIRED_VERIFICATION`).
- **Case numbering**: the literal root set is `-01`…`-25`; every former "through -19" phrase now reads "through -25" (corrected in place; Rev18 §18.4).

### 16.8 Wording corrections (B-RV-3, B-RV-4, B-RV-7)

- Registry axis (supersedes both §15.4 statements): PASS requires a unique readable match whose group_key, fingerprint
  and destination equal the request exactly and whose `verified_run_id`, when non-null, resolves to a same-state run
  with `workflow_outcome=VERIFIED`. A dangling id, a non-terminal run, or a terminal SAFE_ABORT run is Registry FAIL;
  `EXACT` remains a State-axis value only and never appears in the Registry column.
- `PRIMARY_OUTCOME` now names both wave results (album data result and the proven reusable automation path) as stated
  in the Goal contract; neither is optional and neither may be reported from offline or fixture PASS.
- Closure wording: any semantic contract, product-boundary, E2E or GUI-budget change increments `PLAN_REVISION` on the
  same TASK_ID, invalidates prior approvals and any handoff, and repeats independent review; it never continues under
  the same revision.

### 16.9 Planned-file list corrected (A-RV-13)

The real module set is
`src/line_backup_acceptance/{__init__,__main__,authority,cli,common,status,transaction,verifier}.py`; `verify.py` does
not exist (the verifier module is `verifier.py`, imported by `cli.py`). Every listed module already exists and is to be
modified, not created. Test tooling: `tests/automation_verification/{harness.py,fixtures.py,run_phase2_r1…r7*.py,
run_all.py,verify_evidence.py}` — `run_all.py` is the new post-fix wave runner, `verify_evidence.py` already exists and
is extended — plus the existing legacy drivers `tests/{acceptance_case_driver,verifier_fixture_driver,
status_fixture_driver,authority_baseline}.py`. `pyproject.toml` and `README.md` are created/updated as declared.

### 16.10 Post-fix durable evidence roots (A-RV-11)

- Post-fix Phase-2 wave: `evidence/20260916-auto-verification/attempt-02/` split into
  `attempt-02/order-ownership-first/` and `attempt-02/order-driver-first/` (each with per-driver subdirectories and its
  own `readback-verification.json`, Rev17 §17.8) so neither order can overwrite the other.
- Post-fix acceptance wave (the 25-case transaction matrix plus the verifier, authority, status and legacy drivers):
  `evidence/20260916-acceptance/attempt-03/`.
- Post-fix production verify-only pass over the real destination: `evidence/20260916-product-verify/attempt-04/`.
- Post-fix baseline re-snapshot: `evidence/20260916-baseline/attempt-02/`.
- Post-fix independent acceptance (Stage 05): `e2e/attempt-04/`.

No other path may be used, no attempt may overwrite an earlier attempt, and attempt-01/02 material already on disk
stays as provenance for the pre-fix reproductions.

## Revision 15 changes

Wave: **automation verification** (same task, same wave). Rev15 answers the seven minimal fixes required by
`review/attempt-17` (GATE: `PLAN_REVISION_REQUIRED`). Rev14 remains the base contract except where this section amends
it; §15.1–§15.6 are normative and supersede the corresponding Rev14 F-text and the older grammar/case/matrix text, which
is updated in place below. Nothing is relaxed: the goal contract, the read-only boundary over formal config/state/run-log
and the 57 photos, the no-redownload rule, the 禎 (U+798E) / 楨 (U+6968) string separation, and the deferral of every
production Save-All/download remain in force. Earlier approvals (including Rev13 + review/attempt-16 and Rev14 +
review/attempt-17) are not valid for this revision.

### 15.1 F1′ — one in-process dispatch window, reconciliation-only resume (fixes F‑1, F‑8)

Call surface, exact:

- Production `transaction prepare` (no `--test-mode`) requires `--project-root --config --run-log --state --run-id
  --owner-id --source-evidence --group-key --start-date --end-date --expected-images --destination --dispatcher
  --dispatch-counter --evidence-dir`. The adapter pair is mandatory: a prepare that cannot bind its own dispatch window
  is refused with `MISSING_DISPATCHER`, exit 2, before any state read or write. There is no production `prepare` that
  commits an intent nobody can dispatch.
- Test-mode `transaction prepare` (`--test-mode`, state path under `/private/tmp`, case roots `-01`…`-25`) uses the
  canonical children `--config CASE_ROOT_NN/config/line_backup_config.json --run-log CASE_ROOT_NN/state/run_log.md
  --state CASE_ROOT_NN/state/backup_state.json` (Rev17 §17.1; the former "minus `--config`/`--run-log`" rule is deleted),
  plus the test-only fault flags `--dispatcher-outcome RETURNED|UNKNOWN`, `--crash-after-dispatch`, `--pause-at`,
  `--barrier-file`, `--storage-fault`, `--storage-fault-slot`. `--source-evidence` is required and must be a test-mode
  record (§15.3). Test-only flags remain rejected without `--test-mode`.
- `transaction resume` keeps every existing parser option, so the authority rows still parse and still emit JSON result
  artifacts. Its semantics are fixed in this order: (1) authority validation, (2) adapter-flag semantic rejection,
  (3) operation logic. `resume` never dispatches in any mode. Supplying `--dispatcher`, `--dispatch-counter`,
  `--crash-after-dispatch`, or a non-default `--dispatcher-outcome` makes resume return `INVALID_INPUT`, exit 2, with no
  replacement — after authority validation (wrong-authority rows therefore still return `INVALID_AUTHORITY`) and before
  any state read. `--no-dispatch` stays accepted and is a semantic no-op; `--expected-revision`, `--expected-owner-id`
  and `--evidence-dir` stay accepted.
- `transaction commit` refuses with `CONFLICT_UNRESOLVED_DISPATCH`, exit 4, no replacement, unless the loaded run has a
  completed successful dispatch record: `intent_state=SAVE_ALL_DISPATCH_ATTEMPTED`, `dispatch_state=SAVE_ALL_RETURNED`,
  `manual_reconciliation_required=false`, `intent.dispatch_outcome=RETURNED`,
  `dispatch_evidence.save_all_click_count=1`, `dispatch_evidence.save_all_invocation_attempted=true`,
  `dispatch_evidence.failure_boundary=NONE`. This closes the R1 crash window: a crash-orphaned or ambiguity-barrier run
  can be reconciled or SAFE_ABORTed, never committed as VERIFIED.
- `transaction finalize` is unchanged except that `--outcome VERIFIED` additionally requires the §15.2 binding.

The single dispatch window, exact: `prepare` acquires the lock, validates authority and the source-evidence record,
evaluates the F2 preconditions, appends a schema-valid run (`mode=backup_one`, `workflow_outcome=IN_PROGRESS`,
`destination_initially_empty=true`, `phase=SAVE_ALL_INTENT_COMMITTED`, a `checkpoint{phase,at,evidence}` entry,
`manual_reconciliation_required=false`) and commits the intent (`intent_state=INTENT_COMMITTED`,
`dispatch_state=NOT_ATTEMPTED`, `intent.dispatch_outcome=NOT_ATTEMPTED`, `intent.trigger_outcome=NOT_APPLICABLE`,
`save_all_retry_allowed=false`, `intent.calibration` byte-identical to the record's calibration) as a guarded
replacement `revision 0→1`, then — in the same uninterrupted process, still holding the original caller's identity —
performs exactly one adapter invocation (the independent counter gains exactly one line), then commits the post-dispatch
record as a second guarded replacement `revision 1→2`: `intent_state=SAVE_ALL_DISPATCH_ATTEMPTED`,
`dispatch_state=SAVE_ALL_RETURNED`, `intent.dispatch_outcome=RETURNED`, `intent.trigger_outcome=UNKNOWN`,
`save_all_retry_allowed=false`, `phase=SAVE_ALL_DISPATCH_ATTEMPTED`, `dispatch_evidence` = the observed adapter evidence
with a `provenance` string naming the adapter identity, and one checkpoint-shaped `events[]` entry appended to the run's
`events`. Trigger stays UNKNOWN: a dispatcher return is not evidence that a download started.

Prepare result codes (exact): adapter returned → `PREPARED`, exit 0, `dispatch_performed=true`, `revision=2`.
`--dispatcher-outcome UNKNOWN` → the pre-dispatch ambiguity barrier is committed first (`revision 1→2` with the row-4
fields below), the adapter is invoked once, and prepare returns `DISPATCH_UNKNOWN`, exit 1, `revision=2`,
`dispatch_performed=true`. `--crash-after-dispatch` → the adapter appends its counter line and dies; prepare returns
`DISPATCHER_CRASH_AFTER_SIDE_EFFECT`, exit 1, `revision=1`, `dispatch_performed=true`, and the state stays at revision 1
`INTENT_COMMITTED`. Missing or invalid adapter input → `MISSING_DISPATCHER`, exit 2, no write. Every operation's result
`revision` field is the persisted revision after the operation (the reproduced hardcoded `revision=1` is a defect this
wave fixes, and each result carries `state_replaced`).

Resume is a reload/reconciliation protocol with an exact behavior table. `reconciliation_state` and `state_replaced` are
result fields in every row; "no write" means state bytes and revision are unchanged.

| Loaded position (after lock + revision check) | Result | Exit | Write | Δrev | Fields |
|---|---|---|---|---|---|
| run id not present in state | `CONFLICT_OWNER_RUN` | 4 | none | 0 | `state_replaced=false` |
| terminal run, expected revision matches | `SKIP_TERMINAL` | 0 | none | 0 | `dispatch_performed=false`, `reconciliation_state=NONE`, `state_replaced=false` (no live owner required) |
| terminal run, expected revision differs | `CONFLICT_STALE_REVISION` | 4 | none | 0 | `state_replaced=false` |
| non-terminal, never-dispatched loaded intent (`intent_state=INTENT_COMMITTED`, `dispatch_state=NOT_ATTEMPTED`, `intent.dispatch_outcome=NOT_ATTEMPTED`) | `RECOVERY_NO_DISPATCH` | 0 | exactly one guarded replacement | +1 | `reconciliation_state=BARRIER_COMMITTED`, `state_replaced=true`, `dispatch_performed=false`; persisted: `intent_state=TRIGGER_UNKNOWN`, `dispatch_state=UNKNOWN`, `intent.trigger_outcome=UNKNOWN`, `intent.dispatch_outcome=UNKNOWN`, `save_all_retry_allowed=false`, `manual_reconciliation_required=true`, non-empty `reconciliation_reason`, one schema-valid `reconciliations[]` entry and one checkpoint-shaped `events[]` entry |
| non-terminal with the barrier already persisted (`manual_reconciliation_required=true`, or any attempted/unknown dispatch axis) | `RECOVERY_NO_DISPATCH` | 0 | none | 0 | `reconciliation_state=ALREADY_RECONCILED`, `state_replaced=false`, `dispatch_performed=false` |
| non-terminal with a completed dispatch record (post-dispatch, pre-commit) | `RECOVERY_NO_DISPATCH` | 0 | none | 0 | `reconciliation_state=ALREADY_RECONCILED`, `state_replaced=false`, `dispatch_performed=false` |

The barrier's `reconciliations[]` entry is schema-valid per `$defs/reconciliation`: `outcome=EVIDENCE_RECONCILED`,
`trigger_outcome=UNKNOWN`, `blocking_intent_released=false`, `manual_reconciliation_required=true`, `proof=null`,
`original_observation` pinned to `reference="intent-checkpoint:<run_id>:rev<revision>"` naming the loaded intent
checkpoint (Rev17 §17.9), and `evidence` = a hash-bearing reference
`reconcile:<relpath>:<sha256>` that always resolves inside the reconciling process's own `--evidence-dir` and is never a
source binding (Rev16 §16.6 supersedes the `<kind>`-bearing form and the former "§15.2 base rules" phrase). `blocking_intent_released=true` is legal only for
`outcome=ABORTED_BEFORE_SAVE_ALL_DISPATCH` carrying a `$defs/non_dispatch_proof` object
(`save_all_click_count=0`, `save_all_invocation_attempted=false`, `failure_boundary` ∈ {`ELLIPSIS_CLICK`,
`BEFORE_SAVE_ALL_INVOCATION`}, `folder_chooser_appeared=false`, `download_started=false`), which only the SAFE_ABORT
finalization path may write; `prepare` releases a fingerprint barrier only on that persisted release, never on a retry
flag, an owner release or a timeout. Repeat resume is idempotent: the second call performs no write and returns the same
revision.

### 15.2 F2′/F3′ — schema-legal provenance binding, external re-hash (fixes F‑2)

Persisted form. Every committed state must validate against the versioned skill schema `schemas/schemas.json`
`$defs/state` (`additionalProperties:false`); the product validates the whole payload before every replacement, and a
payload that fails validation is refused with no write. Consequences, written down because Rev14 glossed them:

- Runs carry no `owner_id` and no `source_provenance` field (both are absent from `$defs/run` and would violate
  `additionalProperties:false`). Ownership is `state.active_writer_id` plus `intent.owner_execution_id`; the
  production-shape probe that persisted `source_provenance="test fixture"` is removed rather than relabelled.
- The binding reference is persisted in exactly two schema-legal places: the run's checkpoint-shaped `events[]` entry
  `evidence` string and the registry entry's `verified_albums[].evidence` string. No new field, no new artifact type, no
  schema extension, and `backup_state.json` stays the single authority.

Binding reference grammar (one grammar, both schema-legal places):
`join:<relpath>:<sha256>` | `user_fact:<relpath>:<sha256>` | `fixture:<relpath>:<sha256>`. A fourth kind,
`reconcile:<relpath>:<sha256>`, is used only for reconciliation evidence and is never a source binding: it always
resolves inside the operation's own `--evidence-dir`, is authored by the process, and therefore can never satisfy the
source-CONFIRMED rule below.

- Base resolution: `join:` and `user_fact:` resolve against the workspace root
  `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` (where the preserved user fact
  `evidence/20260916-user-fact/source-identity-user-fact.json` and any authoritative join artifact live); `fixture:`
  resolves against the operation's `--project-root`. `<relpath>` must be a normal relative path: no absolute form, no
  `..`, no symlink component, with realpath containment inside its base enforced.
- `fixture:` is accepted only with `--test-mode` against `/private/tmp` case roots, and its artifact must sit outside the
  operation's state path and evidence directory (the fixture binding artifact is driver-authored before product
  execution). Production verify-only, `prepare` and `finalize` treat `fixture:` as unverifiable.
- The reference always targets the *external* artifact: `prepare` records `binding.artifact{path,bytes,sha256}` from
  `--source-evidence`, must find that exact entry in `evidence_artifacts[]`, and never copies, rewrites or re-creates the
  artifact. The product's writes stay the guarded state replacement plus its same-directory temp/lock files, and the
  binding artifact is never inside that write set: it is an operator-supplied external file (workspace evidence for
  `join:`/`user_fact:`, a driver-authored fixture file for `fixture:`). A path that escapes its base, or that resolves
  inside the operation's state path or evidence directory, is refused `INVALID_SOURCE_EVIDENCE` exit 2 at `prepare` and
  reported `UNRESOLVED` by the verifier — the product can never author the bytes it later trusts.

Verification (amends Rev14 F4's source-grounding bullet). `source_status=CONFIRMED` requires all of: the entry's
`verified_run_id` resolves to a run in the same state that is terminal `VERIFIED` and whose group_key, fingerprint and
destination equal the entry's and the request's exactly; that run and the entry carry the same binding reference; and the
binding artifact is re-read **at its external recorded path** and re-hashed, with `bytes` and `sha256` equal to the
reference and to the prepare record, realpath containment proven, and parsed content matching exactly — its own
`group_key` and `app_identifier` equal the request's (UTF‑8 code-point equality; 禎 U+798E and 楨 U+6968 are never
merged, normalized or folded) and its own `fingerprint` equal to the request's; for `user_fact:` the artifact must be the
§16.4 v1 CONFIRMED record (Rev17 §17.4 replaces this clause's former Rev13-format requirement, so a record that carries no
`group_key` is correct), carrying `status` and `source_correspondence_result` `CONFIRMED`, the exact question, answer,
supplier and time, evidence artifacts that re-hash at their recorded paths, `raw_requested_group` equal to the requested
key's group string byte-for-byte, `app_identifier` equal, and `fingerprint` equal on all three fields; the request's key is
compared only against `"line:" + app_identifier + ":" + raw_requested_group` reconstructed from the record, and no
`group_key` key is required or consulted on the record. The recorded `raw_persisted_group` (the 楨 string) is evidence only: it
is never used to satisfy the equality check, never merged, and never rewritten. The user fact recorded on 2026-09-16
(part 1 answered, part 2 `UNANSWERED`, `source_correspondence_result_at_recording: UNRESOLVED`) therefore cannot
confirm the source for this album. Any missing,
unreadable, escaping, non-matching or hash-mismatched artifact, and any unresolvable reference, yields
`source_status=UNRESOLVED` (`LEGACY_PROVENANCE_LIMITED` for a pre-RC2 record or a record with a null `verified_run_id`),
never CONFIRMED; `finalize --outcome VERIFIED` then refuses with `BINDING_UNVERIFIED`, exit 4, no replacement. A bare
`source_authority`-style string, a product-authored artifact, or a hash the product computed by itself satisfies
nothing: the re-hash target is the operator-supplied external artifact whose bytes the independent driver also records
before product execution.

Required negative controls for this mechanism (rows in §15.4): forged or product-authored binding → Source UNRESOLVED,
exit 4, never CONFIRMED; delete the external artifact after a valid prepare/finalize and re-run verify-only → UNRESOLVED,
exit 4; mutate it by one byte → UNRESOLVED, exit 4; `fixture:` presented to production → UNRESOLVED, exit 4. The positive
control is the valid external binding in case 01's closing loop.

### 15.3 F2″ — the source-evidence record and the prepare refusal classes (fixes F‑3)

`--source-evidence <json>` is a required production and test-mode `prepare` input (grammar, authority paragraph and call
graph are updated in place below). Record schema, exactly; unknown keys are refused:

```
{"record_version": 1,
 "test_mode": false,
 "app_identifier": "jp.naver.line.mac",
 "group_key": "line:jp.naver.line.mac:旻謙允禎成長日記",
 "observed_title": "旻謙允禎成長日記",
 "title_confidence": "HIGH|LOW|UNKNOWN",
 "fingerprint": {"start_date": "2024-05-13", "end_date": "2024-05-17", "expected_images": 57},
 "observed_at": "<ISO-8601 UTC>",
 "calibration": {<complete $defs/calibration object>},
 "binding": {"kind": "join|user_fact|fixture",
             "artifact": {"path": "<absolute or workspace-relative>", "bytes": 0, "sha256": "<64 hex>"}},
 "evidence_artifacts": [{"path": "<absolute or workspace-relative>", "bytes": 0, "sha256": "<64 hex>"}, ...]}
```

- `calibration` must be a complete schema-shaped `$defs/calibration` object (`observed_at`, `screenshot_width`,
  `screenshot_height`, `ellipsis`, `dot_spacing`, `save_all_point`, `confidence` const `HIGH`, `evidence`) validated by
  the product; the persisted `intent.calibration` is byte-identical to it. Production never synthesizes `[1,1]`, `HIGH`
  or `"test fixture"` calibrations, and a record whose calibration is absent, incomplete or mismatched is refused. Test
  mode uses a driver-authored calibration and labels the record `test_mode: true`.
- `binding.artifact` must appear in `evidence_artifacts[]` with identical bytes and sha256; `test_mode` must be `false`
  in production and `true` in test mode with `binding.kind=fixture`; the record's group_key and fingerprint must equal
  the argv's exactly.
- Refusal order for `prepare` (after authority validation, before any state read or write): `MISSING_SOURCE_EVIDENCE`
  (no `--source-evidence`) and `MISSING_DISPATCHER` (no adapter pair) → exit 2; `INVALID_SOURCE_EVIDENCE` (unparseable,
  unknown or missing field, incomplete calibration, artifact missing/unreadable/bytes-or-hash mismatch, test-mode
  mismatch, group or fingerprint mismatch) → exit 2; then the persisted-precondition refusals → exit 4:
  `CONFLICT_ACTIVE_RUN`, `CONFLICT_DUPLICATE`, `CONFLICT_DUPLICATE_FINGERPRINT`, `AMBIGUOUS_FINGERPRINT`,
  `NEEDS_RECONCILIATION`. Every refusal writes its result artifact under `--evidence-dir`, leaves state bytes, revision,
  counter and lock untouched, and returns the exact class with no partial run record.
- `duplicate-check` shares the same evaluator and returns the same refusal classes for conflicting or unresolved
  associations (`CONFLICT_DUPLICATE_FINGERPRINT`, `AMBIGUOUS_FINGERPRINT`, `NEEDS_RECONCILIATION`, exit 4) instead of
  the previous destination-scoped `NOT_DUPLICATE` bypass; `NOT_DUPLICATE` remains only when no same-group association and
  no same-fingerprint intent or run exists at all.
- `prepare`'s result `revision` is the persisted revision (2); the reproduced hardcoded `revision=1` output is fixed.

### 15.4 F4′/F5′ — matrix and manifest additions (fixes F‑4)

Axis rule pinned: the Registry axis is association integrity only — PASS requires a unique readable match whose
group_key, fingerprint and destination equal the request exactly and whose `verified_run_id`, when non-null, resolves to
a same-state run with `workflow_outcome=VERIFIED`; absent, ambiguous, duplicated, wrong-group, dangling, non-terminal or
SAFE_ABORT-linked ids are FAIL (Rev16 §16.8 supersedes the former "terminal run" wording). A
null `verified_run_id` is the contract's imported-evidence form: Registry PASS with Source UNRESOLVED /
LEGACY_PROVENANCE_LIMITED. Provenance failures (binding absent, unreadable, escaping, hash-mismatched,
content-mismatched, `fixture:` in production) never flip the Registry axis; they drive Source UNRESOLVED and exit 4.

New verifier rows (each with its own literal root, independent oracle, artifact read-back and entry in the fixture
manifest ID list): `truncated-png`, `jpeg-missing-eoi`, `unsupported-image-type`, `read-error-sample-2`,
`dangling-verified-run-id`, `safe-abort-linked`, `wrong-group-link`, `nonterminal-linked`, `forged-binding`,
`binding-artifact-deleted`, `binding-artifact-mutated`, `fixture-binding-in-production`; and row `legacy-record` is
amended to Registry PASS / Source UNRESOLVED / LEGACY_PROVENANCE_LIMITED (its Rev14 value `EXACT` was a State-axis enum
in a Registry cell). Exact expected values are in the matrix table below.

- `truncated-png`: PNG truncated before IEND, MIME valid → Filesystem FAIL / Overall NOT_ACHIEVED / exit 4 /
  INPUT_NEGATIVE.
- `jpeg-missing-eoi`: JPEG whose segment walk ends without EOI → Filesystem FAIL / NOT_ACHIEVED / exit 4 /
  INPUT_NEGATIVE.
- `unsupported-image-type`: recognized image MIME outside JPEG/PNG → Filesystem FAIL / NOT_ACHIEVED / exit 4 /
  `UNSUPPORTED_IMAGE_TYPE`; never PASS and never a silent skip.
- `read-error-sample-2`: read error identical in samples 1–2 with a clean sample 0 (the recorded R5(c) variance) →
  Filesystem FAIL / Registry, Source, State NOT_RUN / Overall UNKNOWN / exit 1 / `INTERNAL_READ_ERROR`; never
  INPUT_NEGATIVE and never PASS.
- `dangling-verified-run-id`, `safe-abort-linked`, `nonterminal-linked`, `wrong-group-link`: Registry FAIL / Source
  UNRESOLVED (CONTRADICTED for the requested-key mismatch) / NOT_ACHIEVED / exit 4 / INPUT_NEGATIVE.
- `forged-binding`, `binding-artifact-deleted`, `binding-artifact-mutated`, `fixture-binding-in-production`: Registry
  PASS / Source UNRESOLVED / NOT_ACHIEVED / exit 4 / INPUT_PROVENANCE_LIMITED.
- F5 oracle: every status-driver row asserts the emitted `evidence_basis == "scenario_table_non_acceptance"`; a row
  whose output omits or changes that field fails the driver, so the field cannot silently disappear.

### 15.5 F6′ — driver scope for ownership isolation (fixes F‑5)

The ownership-marker/no-default-removal protocol applies to **every** driver and script that creates or removes a shared
root, not only the two that caused the reproduced destruction: `tests/acceptance_case_driver.py`,
`tests/verifier_fixture_driver.py`, `tests/status_fixture_driver.py`, `tests/authority_negative_driver.py`,
`tests/authority_baseline.py`, `tests/test_transaction_core.py`, `tests/legacy_false_positive_repro.py`,
`tests/automation_verification/harness.py`, `tests/automation_verification/fixtures.py`, every
`tests/automation_verification/run_phase2_r*.py` script, `run_all.py` and `verify_evidence.py`. Each creates only its own
literal roots (case roots `-01`…`-25`, verifier roots, status roots, authority roots, phase-2 roots), writes an ownership
marker naming the driver id, TASK_ID, root path and creation time before any fixture content, never removes or overwrites
a root that lacks its marker, and removes nothing by default — an explicit `--clean-owned` may remove only roots carrying
its own marker, and only after the read-back verifier consumed them. Evidence is durable with a SHA-256/bytes manifest
per attempt; `/private/tmp` is working space only. The read-back verifier runs the wave in both orders (ownership-last
and ownership-first) and both runs must leave every manifest independently readable, writing disjoint durable roots
`evidence/20260916-auto-verification/attempt-02/order-ownership-first/` and
`evidence/20260916-auto-verification/attempt-02/order-driver-first/` (Rev17 §17.8) so neither order can overwrite the
other; a driver that violates the protocol is a TASK_REGRESSION, not an environment failure.

### 15.6 Revision binding, self-references and part-1 wording (fixes F‑6, F‑7)

- Every "this revision" self-reference in this document now reads 15 (or the current revision at handoff time); Stage 03
  compiles the handoff for the approved `PLAN_REVISION` and its exact hash, and Stage 04 stops on any handoff↔plan
  mismatch. The Rev14 text above is preserved as history, not as the binding revision.
- The part-1 user fact resolves the visible-title character only: `旻謙允禎成長日記` is the 禎 (U+798E) string the user
  confirmed, and the strings are never merged. It does **not** establish that the 57 destination files correspond to that
  album, nor that the 楨 (U+6968) key in formal config/state is the same source: that correspondence stays `UNRESOLVED`
  until part 2 is answered or an authoritative machine join exists, and the album-data result therefore stays incomplete
  meanwhile.

## Revision 14 changes

Wave: **automation verification** (WORK/handoff.md H2.1 §7–§8). Rev13 remains the base contract. This revision adds
(a) the Phase-2 reproduction record, (b) the fix contract F1–F7 for R1–R7, (c) the post-fix verification plan,
(d) the single exact human gate, and (e) three-result closure semantics. Nothing in Rev13 is relaxed: the goal
contract, formal config/state/run-log/photo read-only boundary, no-redownload rule, string separation
(禎 U+798E / 楨 U+6968, never merged, never normalized), and the deferral of all production Save-All/download
remain in force. Any earlier approval (including Rev13 + review/attempt-16) is not valid for this revision.

### Phase-2 reproduction record (real entry, append-only evidence)

Evidence root: `evidence/20260916-auto-verification/attempt-01/` (Phase-0 baseline; Phase-1 archive manifest of all
106 `/private/tmp/line-backup-*` entries; `phase2-r1`…`phase2-r7`; `phase2-r6-ownership`). Subject program hashes in
every record equal handoff §4 (`transaction.py` c486edbe…, `verifier.py` b38ee6d5…, `status.py` 20a95f7c…,
`authority.py` a98964e3…, `cli.py` a5bbbbf6…, `common.py` 59a85c47…).

| Gap | Verdict | Key observation (each with argv/stdout/stderr/exit, program hash, counter, before/after state, manifest) |
|---|---|---|
| R1 | REPRODUCED_DUPLICATE_DISPATCH | normal-path `resume` is SIGKILLed after the dispatcher side effect (state still revision 1, INTENT_COMMITTED, no dispatch_evidence); fresh `resume` dispatches again; independent counter 1→2. |
| R2 | REPRODUCED_FRESH_PROCESS_DISPATCH | `prepare` (process A) then fresh-process `resume` (process B) dispatched once; the same fixture with `--no-dispatch` performed no dispatch: safety currently depends on the caller's flag. |
| R3 | REPRODUCED_PRECONDITION_GAPS | destination change bypasses `duplicate-check` (NOT_DUPLICATE); a historical unresolved intent does not block `prepare`; count change 57→56 bypasses; an isolated production-shaped root accepts `transaction prepare` **without** `--test-mode` and persists calibration `[1,1]`, `confidence=HIGH`, `source_provenance="test fixture"`. Ambiguity control (two entries) correctly returns CONFLICT_DUPLICATE. |
| R4 | REPRODUCED_FINALIZE_TRUSTS_JSON | `finalize` commits VERIFIED from arbitrary JSON (PASS/57, FAIL/0, `{}`, other run's JSON); the entry it writes has no `source_authority` — and the skill's registry schema forbids extra properties — so the verifier's `authoritative_exact_join` gate is unimplementable in that shape; the same state over a real 57-file destination yields verify-only `registry PASS / source UNRESOLVED / overall NOT_ACHIEVED, exit 4`. |
| R5 | REPRODUCED_WITH_VARIANCE | forged `source_authority` string → source CONFIRMED / overall PASS; dangling and terminal-SAFE_ABORT `verified_run_id` accepted; read errors identical in samples 1–2 with a clean sample 0 are misclassified as INPUT_NEGATIVE FAIL (the handoff predicted a false PASS; the actual manifestation is a misclassification — recorded as observed) because `read_error` inspects only `samples[0]`; a truncated-but-MIME-valid PNG is counted as a photo → PASS. |
| R6 | REPRODUCED_STATUS_SELF_CERTIFICATION + REPRODUCED_CROSS_TEST_DELETION | `status evaluate` returns DONE / READY_FOR_INDEPENDENT_ACCEPTANCE from zero-fact `scenario` inputs and never reads declared baseline artifacts; `tests/authority_negative_driver.py` and `tests/test_transaction_core.py` each deleted all twelve shared `/private/tmp/line-backup-acceptance-case-01..12` roots (ownership markers destroyed). |
| R7 | REPRODUCED_NON_CLOSING_LOOP_AND_DUPLICATE_BYPASS | genuine fixture transaction (adapter replaces only external I/O and owns the counter): prepare → resume (1 side effect) → commit → finalize VERIFIED; then verify-only reports source UNRESOLVED / overall NOT_ACHIEVED, and a second `prepare` for the same fingerprint at a new destination returns PREPARED. |

R1–R7 reproduction evidence is bound to the pre-fix program hashes above, is append-only, and is **not** evidence of
post-fix behaviour. R5(c) variance and the R3(e)/R4/R7 fixtures are labelled fixtures, never production E2E.

### Fix contract (F1–F7) — minimal complete repairs of the reproduced gaps

*Amended by Rev15:* §15.1 supersedes F1's flag placement and case/revision protocol, §15.2 supersedes F3's binding
storage and F4's source-grounding bullet, §15.3 supersedes F2's source-evidence paragraph, §15.4 supersedes the
matrix-coverage expectations, and §15.5 supersedes F6's driver list. Where Rev14 text and Rev15 §15 conflict, Rev15
is normative.

All fixes are implemented through the real operator boundary (`python3 -m line_backup_acceptance …`, library + CLI).
No fix may change an expectation, relax an authority allowlist, or add a fixture-only back door in order to pass a test.

**F1 — dispatch continuity and at-most-once (R1, R2).**
Contract: only the same uninterrupted caller that just completed the intent write/read-back may perform the single
original Save-All dispatch. A loaded intent never authorizes dispatch.
Design: `transaction prepare` performs the intent commit and read-back, then — in the *same process* — performs
exactly one dispatch when adapter flags (`--dispatcher`, `--dispatch-counter`, optional `--dispatcher-outcome`) are
supplied, and commits `SAVE_ALL_DISPATCH_ATTEMPTED`/`SAVE_ALL_RETURNED` (with `trigger_outcome=UNKNOWN`,
`save_all_retry_allowed=false`) afterwards. `transaction resume` becomes reconciliation-only: it never invokes a
dispatcher (adapter flags are rejected with `INVALID_INPUT` in every mode); when it loads a non-terminal
`INTENT_COMMITTED` intent it commits the ambiguity barrier (`intent_state=TRIGGER_UNKNOWN`,
`dispatch_state=UNKNOWN`, `trigger_outcome=UNKNOWN`, `dispatch_outcome=UNKNOWN`,
`manual_reconciliation_required=true`, `reconciliation_reason` non-empty) and reports
`RECOVERY_NO_DISPATCH` with `dispatch_performed=false`; `--no-dispatch` remains accepted but is semantically a no-op.
A crash between the dispatcher side effect and the barrier commit therefore leaves a loaded intent that can only be
reconciled, never re-dispatched. At-most-once is proven with the independent dispatcher counter.

**F2 — preconditions and duplicate gate (R3).**
One shared precondition evaluator is used by both `duplicate-check` and `prepare`, over the *persisted* state, before
any write:
- exact terminal association (same group_key + complete fingerprint + destination, unique) → `duplicate-check`:
  `SKIP_DUPLICATE`; `prepare`: refusal (`CONFLICT_DUPLICATE`) — a verified album is never re-prepared.
- same group_key + complete fingerprint at a *different* destination → refusal (`CONFLICT_DUPLICATE_FINGERPRINT`)
  unless an affirmative non-dispatch reconciliation for that fingerprint is persisted (contract: only exact proven
  non-dispatch plus successful resolution read-back releases a fingerprint barrier).
- same group_key + same date range with a different expected count → refusal (`AMBIGUOUS_FINGERPRINT`).
- any historical run for the same group_key + fingerprint that is non-terminal, or terminal without affirmative
  non-dispatch proof (dispatch attempted/unknown) → refusal (`NEEDS_RECONCILIATION`).
- more than one candidate association → refusal (`CONFLICT_DUPLICATE`).
- existing active run/writer/lock → refusal (`CONFLICT_ACTIVE_RUN`, already implemented).
Production `prepare` additionally requires observed-source evidence: `--source-evidence <json>` containing
`app_identifier`, `group_key`, `observed_title`, `fingerprint{start_date,end_date,expected_images}`,
`title_confidence`, `observed_at`, and `evidence_artifacts[{path,bytes,sha256}]`; missing/invalid/mismatched input →
`MISSING_SOURCE_EVIDENCE`/`INVALID_SOURCE_EVIDENCE` exit 2 with **no** state write. The intent's calibration is taken byte-identically from that record's complete schema-shaped `calibration` block
(Rev15 §15.3); production never fabricates `[1,1]`/HIGH/"test fixture", and **no run-level `source_provenance` field is
persisted anywhere** (Rev15 §15.2 — `$defs/run` forbids extra properties; test fixtures are labelled through the
schema-legal `fixture:` binding reference and the driver-authored record). Test mode keeps synthetic fixtures and
remains the only mode in which `--test-mode`-gated flags are accepted. `prepare` also requires the destination to exist, be an empty
directory, be resolved through real paths inside the configured backup root (production), and equal the intent
destination.

**F3 — finalize validation and registry provenance binding (R4, R7).**
`finalize --outcome VERIFIED` validates the supplied verification JSON before any write: it must be the product
verifier's result (`mode="verify_only"`), must match `run_id`/`group_key`/`fingerprint`/`destination` of the run, and
must carry `filesystem_status="PASS"` with `recognized_images` equal to the expected count. A JSON claiming FAIL,
an empty object, or another run's result is refused (`INVALID_VERIFICATION_EVIDENCE`/`VERIFICATION_RUN_MISMATCH`,
exit 4, no revision change, no registry entry).
For VERIFIED the run and its registry entry must carry the same **schema-legal** binding reference
(`join:`/`user_fact:`/`fixture:`) in the run's checkpoint-shaped `events[]` `evidence` string and in
`verified_albums[].evidence`, per Rev15 §15.2. `prepare` never writes a binding artifact: it records the external
artifact's path/bytes/sha256 from the source-evidence record, and `finalize`/the verifier re-read and re-hash that
external artifact at its recorded path. The registry entry keeps the schema-conformant shape (`group_key`,
`fingerprint`, `verified_run_id`, `destinations`, `source_kind`, `evidence`); `source_kind` is
`filesystem_verification` for a join-bound run and `user_attestation` for a user-fact-bound run; the terminal commit
stays one revision.

**F4 — verifier grounding, read errors, and image integrity (R5).**
- Source grounding (amended by Rev15 §15.2, which is normative): `source_status=CONFIRMED` requires the same-state
  terminal `VERIFIED` link, the exact group/fingerprint/destination match, and a binding reference whose **external**
  artifact is re-read and re-hashed at its recorded path with bytes/sha256 equality and exact content equality (no
  normalization, 禎/楨 never merged). A bare `source_authority` string, a product-authored artifact, a
  dangling/SAFE_ABORT-linked/non-terminal `verified_run_id`, a legacy or null-link imported entry, and any
  unreadable/escaping/mismatched artifact → `UNRESOLVED` (`LEGACY_PROVENANCE_LIMITED` when the record is pre-RC2 or has
  a null `verified_run_id`). `registry_status=FAIL` only for association-link defects (dangling non-null,
  non-terminal, wrong-group, absent/ambiguous/duplicate); provenance failures never flip the registry axis.
- Read errors: a `READ_ERROR` in **any** sample (not only sample 0) is an internal read/command error → overall
  `UNKNOWN`, exit 1, failure class `INTERNAL_READ_ERROR`/`INTERNAL_COMMAND_ERROR`; it is never INPUT_NEGATIVE and
  never PASS.
- Image integrity: every recognized image must additionally pass a deterministic structural decode — PNG: chunk
  walk with CRC checks, full zlib decompression of the IDAT stream, IHDR/IEND consistency; JPEG: marker-segment
  walk with length validation, SOF/SOS presence, and a terminating EOI (a truncated JPEG lacks EOI). A recognized
  image that fails structural decode → filesystem FAIL, INPUT_NEGATIVE. For image types outside JPEG/PNG the
  verifier must fail closed with a precise failure class unless a decoder is available. Residual limitation
  (a corrupted-but-structurally-closed JPEG body) is documented, not hidden.
- The verifier never discovers or substitutes roots; evidence stays under the supplied evidence directory with a
  SHA-256/bytes manifest.

**F5 — status module is not an acceptance oracle (R6a).**
`status evaluate` keeps its routing table but is declared a **non-acceptance demonstration tool**: its inputs are
facts it does not verify and its scenario table is self-certifying. It must state this in its own output
(`"evidence_basis": "scenario_table_non_acceptance"` when a scenario is used), in README, and in this plan. No
Stage-05 acceptance decision may cite status output as evidence; closure facts come from executed checks and their
manifests.

**F6 — harness ownership isolation and re-runnability (R6b).**
The invariant applies to every driver and script that creates or removes a shared root; the full enumeration is in
Rev15 §15.5, which is normative. No test or driver may delete or overwrite another test's root or evidence:
each driver creates its own roots only when missing, writes an ownership marker, never removes a root that lacks its
marker, and removes nothing by default (an explicit `--clean-owned` flag may remove only owned roots). Every driver/attempt writes durable evidence plus a
SHA-256/bytes manifest, and any order or parallel re-run must leave every manifest independently readable
(machine-checked by an independent read-back verifier). `/private/tmp` is working space only; durable copies are
required.

**F7 — integration closure and truthful product boundary (R7).**
With F2–F4 in place the real-entry fixture loop must close: new transaction (prepare with in-process dispatch,
adapter replaces only external I/O and owns the side-effect counter) → commit → finalize VERIFIED (join-bound) →
verify-only `PASS` with `source_status=CONFIRMED` over the same destination → repeat run `SKIP_DUPLICATE` with zero
dispatch → same-fingerprint different-destination `prepare` refused. README and CLI help must state the real
boundary truthfully: the CLI does not itself drive LINE's GUI; the dispatcher/adapter interface is external I/O; the
production Save-All route stays gated and is not implemented by this wave.

### Post-fix verification plan (how F1–F7 are proven)

1. The Phase-2 scripts are re-run **unchanged in intent** against the fixed build; each gap must flip to its safe
   verdict (R1/R2: counter never exceeds one and fresh processes never dispatch; R3: refusals at the real entry for
   every reproduced bypass — destination change, count change, historical unresolved intent, production prepare
   without a source-evidence record; R4: refusals + closed loop; R5: forged string no longer CONFIRMED,
   dangling/SAFE_ABORT/non-terminal links FAIL, any-sample read error → UNKNOWN exit 1, truncated PNG / JPEG
   without EOI / unsupported image type → INPUT_NEGATIVE fail-closed; R6: no cross-deletion, status labelled
   non-acceptance with the `evidence_basis` oracle; R7: loop closed, duplicate bypass refused, binding re-hashed
   externally). Negative controls must show the legitimate paths still work (in-process dispatch succeeds exactly
   once; a valid external join binding verifies and a deleted/mutated one does not; the ambiguity control still
   fails). The Rev15 rows and Cases 13–19 run in the same wave, and the wave is re-run in both orders
   (ownership-last and ownership-first) with every manifest still independently readable.
2. Expectations in legacy drivers may change **only** where Rev14/Rev15 changes the contract; each changed row is listed
   with its reason in `execution.md`. Tests are never edited to hide a defect.
3. Evidence per attempt: full argv (secrets removed), stdout/stderr/exit, program hashes, independent counters,
   before/after state, durable artifact manifest (SHA-256 + bytes); attempts are append-only; failed output is kept.
4. `tests/automation_verification/run_all.py` runs the whole wave (R6-ownership last) and
   `tests/automation_verification/verify_evidence.py` independently re-reads every manifest; both are part of the
   deliverable.
5. Stage 05 acceptance runs independently over the real CLI, the formal read-only verify-only result and the wave's
   evidence package; it does not modify product code or tests.
6. Regression breadth is risk-appropriate: the updated transaction/verifier/authority/status drivers plus the new
   wave; failure triage separates pre-existing failures from regressions.

### Human gate (exactly one request, after all non-GUI work is complete)

The gate asks the user for two things in one message and nothing else:
1. **Open fact (part 2)**, allowing 「不知道」: 「`Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`
   那 57 張，是不是就是 `旻謙允禎成長日記` 這個群組 2024/05/13～05/17 的備份？」
   The recorded answer is preserved verbatim with supplier/time/hash exactly like part 1; a 「不知道」answer keeps
   `LEGACY_PROVENANCE_LIMITED` and blocks only the album-attribution result, never the capability result.
2. **GUI observation gate**: with LINE already displaying the exact target (app `jp.naver.line.mac`, group
   `旻謙允禎成長日記`, album `2024/05/13～05/17`, 57 images), authorize exactly **one** current-target ellipsis
   observation input; capture immediate post-observation evidence and stop.
   The gate does **not** authorize: menu-item selection, Save All, chooser interaction, keyboard shortcuts, any
   state write, any download, or any production transaction. Historical ellipsis credit is exhausted (2/2); this is
   a new, explicit, one-shot authorization. A negative or absent authorization only localizes an observation gap;
   it is not proof that any bridge is necessary.

### Three separately reported results and closure semantics (Rev14)

1. **Album data result** (`PRIMARY_OUTCOME_STATUS` for the 2024/05/13～05/17 album): requires filesystem PASS,
   exact source correspondence, state/registry/intent consistency and the destination association. Part 1 of the
   recorded user fact resolves only the visible-title character (the visible group is the 禎 U+798E string the user
   confirmed; strings are never merged) — it does **not** establish that the 57 destination files correspond to that
   album, nor that the 楨-keyed (U+6968) formal namespace is the same source. That correspondence stays
   `UNRESOLVED` / `LEGACY_PROVENANCE_LIMITED` until part 2 is answered or an authoritative machine join exists (Rev15
   §15.6), and item 1 stays incomplete meanwhile. Formal config/state/run-log and the 57 photos stay read-only in
   this wave; any import/rewrite would require a new gate.
2. **Reusable automation capability** (`IMPLEMENTATION` + `CORE_ACCEPTANCE` for the process): F1–F7 implemented,
   reproducible in any order, independently re-readable, with fixture results labelled as fixtures.
3. **Overall closure** (`TASK_CLOSURE_STATUS`): `complete` only when both 1 and 2 hold. Offline or fixture PASS is
   never reported as GUI end-to-end success, and an unfinished required verification never erases proven
   implementation/CORE facts.

Status fields remain orthogonal (Rev13 §Closure and sequencing): `PRIMARY_OUTCOME_STATUS`, `IMPLEMENTATION_STATUS`,
`CORE_ACCEPTANCE_STATUS`, `REQUIRED_VERIFICATION_STATUS`, `INDEPENDENT_ACCEPTANCE_STATUS`, `TASK_CLOSURE_STATUS`.
`Done` means overall closure only.

## Revision 13 changes

This revision corrects an acceptance-matrix naming conflict identified by
independent Stage 05 attempt 02. The only literal verifier fixture in this
wave is a malformed configuration (a required key is removed), so its row is
now named `Invalid configuration` and expects the already-defined
`INVALID_CONFIGURATION` failure class with exit 2. This is an evidence and
matrix correction only: no product enum, authority rule, persistence field,
retry rule, gate, or closure meaning changes. Invalid invocation remains the
product CLI's separate `INVALID_INPUT` path and is not silently conflated with
the configuration fixture.

## Revision 12 changes

Revision 11's four corrections remain in force. Independent review attempt 13 found one further RC2 contradiction: a committed intent must already have `save_all_retry_allowed=false` before any Save-All dispatch. Cases 02/03 therefore use false in both the revision-1 prepared pre-state and the revision-2 uncertainty barrier; the revision-1 `READY` shorthand means readiness to enter the one-way barrier, not permission to retry a dispatch.

## Revision 11 changes

This revision resolves the four findings in independent review attempt 10 without changing the requested target, the formal-state read-only boundary, the no-redownload boundary, or the deferred production Save-All gate:

- RC2 recovery fixtures use only the existing `intent_state`, `dispatch_state`, `trigger_outcome`, and `dispatch_outcome` vocabulary. The pre-adapter state is `INTENT_COMMITTED` / `NOT_ATTEMPTED` / `NOT_APPLICABLE` / `NOT_ATTEMPTED` with `save_all_retry_allowed=false`; the durable uncertainty barrier is `TRIGGER_UNKNOWN` / `UNKNOWN` / `UNKNOWN` / `UNKNOWN` with `save_all_retry_allowed=false`. `READY` and `NOT_DISPATCHED` are documentation shorthand only and are never persisted or accepted as enums.
- Duplicate checking has explicit precedence: `duplicate-check` returns `SKIP_DUPLICATE`; a matching terminal `resume` returns `SKIP_TERMINAL`. Both are terminal no-dispatch outcomes, but they are not interchangeable result values.
- Production and test-only transaction grammars are separate. Production requires canonical config, state, and run-log paths plus backup-root/destination containment before lock/control-path creation; test mode is a bounded fixture-only exception. Literal production and test-only authority-negative subprocess rows are required.
- Exact source correspondence is the only source basis for closure: either an authoritative exact join or one precise user fact in the preserved evidence format (Rev16 §16.4: the CONFIRMED v1 record contract; `join:` requires `join_authority="authoritative_exact_join"`). No plan rationale, similarity, fingerprint match, legacy record, or route observation is an equivalent.

## Goal contract

PRIMARY_OUTCOME (Rev16 §16.8): the wave's two results together — (1) safely establish whether the existing 57-image destination is a valid backup of the user's exact LINE source group '旻謙允禎成長日記', album '2024/05/13～05/17', and otherwise stop without any ambiguous or duplicate production transaction; and (2) leave the reusable automation path itself proven through the real entry — the R1–R7 repairs executed end-to-end by the operator CLI with rerunnable, independently readable evidence. Neither result may be claimed from offline or fixture PASS, and paperwork is not a substitute for either.

CORE_REQUIREMENTS:

- Prove or stop on exact source correspondence, not merely valid-looking files.
- Perform a read-only filesystem, inventory, state, registry, intent, and writer reconciliation against the existing destination.
- Deliver and test a reusable transaction process whose real operator CLI and library paths perform resume, duplicate gating, dispatch barrier handling, compare-and-commit, and terminal finalization. No test-only model is accepted as the process.
- Determine the shortest safe current-runtime Save-All route from documented capability and fresh evidence when that route is necessary; do not dispatch an ambiguous menu item.
- Independently accept the implementation/evidence package. A later production Save-All/download is not part of this wave and requires a new reviewed plan and gate.

SUCCESS_EVIDENCE:

- The product CLI emits separate filesystem, registry, source, state, and overall outcomes. Filesystem evidence contains exactly 57 recognized images, stable complete inventories, per-file SHA-256, byte lengths, mtime, MIME/content, no zero-byte/partial/temp/hidden/unrecognized entries, no unsafe path or entry anomalies, and an artifact manifest.
- SOURCE_CORRESPONDENCE is explicitly CONFIRMED, UNRESOLVED, or CONTRADICTED. '禎' and '楨' remain separate strings and keys; a user fact is recorded as evidence and never silently rewrites legacy data.
- State acceptance identifies EXACT, ABSENT, AMBIGUOUS, LEGACY_PROVENANCE_LIMITED, or STATE_CONTRADICTED without mixing fields across records.
- The same product transaction CLI used by an operator is invoked in subprocess restart/fault/race tests. Independent oracles inspect dispatch counters, state bytes/revisions, intent axes, registry, owner, and terminal status.
- Current CUA evidence, if required, names the exact target and one permitted ellipsis input in an existing ledger scope. Observation-only is never called production E2E and does not authorize Save-All.

MUST_NOT_BREAK:

- Existing photos and formal config/state/registry/intent/run-log are read-only for this wave; no redownload of the valid 57-file destination.
- No AXPress, AXUIElementPerformAction, AX write, guessed coordinate, OCR-only acceptance, AppleScript/hidden AX workaround, or Save-All retry after uncertainty.
- DATA_PROJECT_ROOT authority is explicit and immutable. Product test state, destination, evidence, and fake dispatcher counters are isolated from it.
- Intent, dispatch, trigger, filesystem, source, registry, and terminal ownership remain separate axes. UNKNOWN is never converted to zero or NOT_ATTEMPTED without affirmative non-dispatch proof.
- No test passes by writing a constant to a field and later asserting that same self-written field. Tests invoke the actual product CLI/process boundary and independently compute/check expected state and counters.
- Bridge/service readiness is supporting and non-gating unless a route-specific experiment proves it necessary.

NON_GOALS:

- No automatic spelling merge, legacy migration, production download, bridge reinstall, TCC change, or broad historical cleanup.
- No distributed exactly-once protocol, new persistence schema, or unrelated bridge/controller refactor.
- No claim that historical GUI, build, bridge, standalone audit, or offline PASS proves current Save-All capability or exact source correspondence.
- No claim that the absent formal data directory already contains an external resume/dispatch/commit implementation.

## Authoritative roots and product boundary

DATA_PROJECT_ROOT: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state
DATA_CONFIG: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json
DATA_STATE: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json
DATA_RUN_LOG: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md
DATA_BACKUP_ROOT: /Users/hsiaojohnny/Downloads/LINE-Backup-PoC
DATA_DESTINATION: /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57
TARGET_GROUP_KEY: line:jp.naver.line.mac:旻謙允禎成長日記
TARGET_GROUP_NAME: 旻謙允禎成長日記
TARGET_APP_BUNDLE: jp.naver.line.mac
TARGET_ALBUM: 2024/05/13～05/17
TARGET_EXPECTED_IMAGES: 57

Verified repository fact: DATA_PROJECT_ROOT currently contains only config/line_backup_config.json, state/backup_state.json, and state/run_log.md. It has no existing verifier, transaction library, producer, or consumer.

PRODUCT_BOUNDARY_DECISION: The task deliverable is an operator-facing reusable local product, not an acceptance-only fixture. Its product owner is the LINE album backup task deliverable; its consumers are the documented operator CLI commands below. The CLI and library are the single real process boundary for verify-only and offline resume/commit/duplicate behavior. The formal data project is an input/state authority and remains read-only. The plan makes no claim that another absent external producer already consumes this module. Any future integration with another producer is a new architecture/contract decision and requires a later approved plan revision plus independent review.

Planned implementation files (existing modules are modified in place; `run_all.py` is new), created or edited only after this plan is independently approved:

- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/pyproject.toml
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/__init__.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/cli.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/verifier.py (Rev16 §16.9: the verifier module is `verifier.py`; `verify.py` never existed)
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/transaction.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src/line_backup_acceptance/status.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/ (existing legacy drivers and `tests/automation_verification/*` are modified, not created; the post-fix wave runner `tests/automation_verification/run_all.py` is new; Rev16 §16.9)
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/verifier_fixture_driver.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/authority_baseline.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/status_fixture_driver.py
- /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/README.md

Packaging/build contract:

- Working directory: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Interpreter: /usr/bin/python3
- Test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_*.py' -v
- Verify command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state --config /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json --state /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-product-verify/attempt-04
- Transaction test command: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m unittest discover -s /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests -p 'test_transaction_*.py' -v
- Transaction subprocess entry point (Rev15 §15.1; the dispatch window lives inside prepare; Rev17 §17.1 canonical children): cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction prepare --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id RUN-CASE-01 --owner-id WRITER-CASE-01 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-01/destination --source-evidence /private/tmp/line-backup-acceptance-case-01/source-evidence.json --dispatcher /private/tmp/line-backup-acceptance-case-01/dispatcher-returned.py --dispatch-counter /private/tmp/line-backup-acceptance-case-01/dispatch-counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode --dispatcher-outcome RETURNED
- No command in the acceptance artifacts may leave DATA_PROJECT_ROOT, DATA_DESTINATION, TARGET_GROUP_KEY, CASE_ROOT, or EVIDENCE_DIR as an unresolved symbolic placeholder. Recorded argv must contain literal absolute paths.

Operator CLI grammar and product call graph:

- verify-only --project-root PATH --config PATH --state PATH --destination PATH --group-key KEY --start-date ISO --end-date ISO --expected-images INT --evidence-dir PATH [--test-mode --pause-at SAMPLE_2_READY --barrier-file PATH]
- Production transaction forms (no `--test-mode`): `transaction prepare --project-root PATH --config PATH --run-log PATH --state PATH --run-id ID --owner-id ID --source-evidence PATH --group-key KEY --start-date ISO --end-date ISO --expected-images INT --destination PATH --dispatcher PATH --dispatch-counter PATH --evidence-dir PATH`; `transaction resume --project-root PATH --config PATH --run-log PATH --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --evidence-dir PATH [--no-dispatch]` (adapter options are still parsed but are rejected with `INVALID_INPUT` exit 2 after authority validation, per §15.1); `transaction commit --project-root PATH --config PATH --run-log PATH --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --verification-json PATH --evidence-dir PATH`; `transaction finalize --project-root PATH --config PATH --run-log PATH --state PATH --run-id ID --expected-revision INT --expected-owner-id ID --outcome VERIFIED|SAFE_ABORT --verification-json PATH --evidence-dir PATH` (with `--verification-json` required for `--outcome VERIFIED` and optional for `SAFE_ABORT`; Rev17 §17.9/§16.7; Rev18 §18.2); `transaction duplicate-check --project-root PATH --config PATH --run-log PATH --state PATH --group-key KEY --start-date ISO --end-date ISO --expected-images INT --destination PATH --evidence-dir PATH`.
- Test-only forms (Rev16 §16.1 supersedes this layout): the same operation-specific arguments use `--project-root /private/tmp/line-backup-acceptance-case-01` through `-25` with the canonical children `--config CASE_ROOT/config/line_backup_config.json --run-log CASE_ROOT/state/run_log.md --state CASE_ROOT/state/backup_state.json` and explicit `--test-mode`; only the declared pause, dispatcher, storage-fault and `--storage-fault-slot` flags are accepted in this form (Rev16 §16.7), and `--source-evidence` must be a test-mode record. Production commands accept the production adapter interface (`--dispatcher`, `--dispatch-counter` on `prepare` only) and never the test-only fault flags (`--dispatcher-outcome` non-default, `--crash-after-dispatch`, `--pause-at`, `--barrier-file`, `--storage-fault`).
- status evaluate --input PATH --output PATH

Authority rule: every `verify-only` execution and every `transaction` execution requires one explicit immutable `--project-root`. Authority validation is the first filesystem operation after argument parsing, before loading state/config, deriving a lock path, creating a control directory, or touching any path outside the isolated evidence directory. For verify-only, the supplied `--config` and `--state` must be byte-addressed canonical children of that root (`project_root/config/line_backup_config.json` and `project_root/state/backup_state.json`), and run_log is derived only from `project_root/state/run_log.md`; any mismatch, symlinked root/ancestor, missing canonical file, or path outside the root returns `INVALID_AUTHORITY`, exit 2, before reading or writing authority files. Verifier `--test-mode` is permitted only for the literal `/private/tmp/line-backup-acceptance-verifier` fixture root and the literal case roots `/private/tmp/line-backup-acceptance-case-01` through `-25` (Rev16 §16.1), and remains read-only. For a production transaction invocation (no `--test-mode`), `--config`, `--run-log`, and `--state` are required and must resolve respectively to `project_root/config/line_backup_config.json`, `project_root/state/run_log.md`, and `project_root/state/backup_state.json`; configured backup-root and destination containment are validated before lock/control-path creation or any mutation. `--source-evidence` must be an absolute path to a readable regular file; a missing or unreadable record is a record refusal (`MISSING_SOURCE_EVIDENCE`), not `INVALID_AUTHORITY`, while every root/state/config/run-log rule above is unchanged. Transaction option semantics are evaluated in the fixed order authority validation → record load → adapter-flag semantic rejection (`resume` with adapter options → `INVALID_INPUT`, exit 2, `prepare` without the adapter pair → `MISSING_DISPATCHER`) → precondition refusals → operation logic, all before any state read or write. The only transaction exception is an explicit `--test-mode` invocation whose project root is one literal `/private/tmp/line-backup-acceptance-case-01` through `/private/tmp/line-backup-acceptance-case-25`; it must carry the canonical children `--config project_root/config/line_backup_config.json`, `--run-log project_root/state/run_log.md` and `--state project_root/state/backup_state.json` (Rev16 §16.1 supersedes the former "omit config/run-log / state.json" form), keep all fixture state/destination/evidence beneath that root, and is rejected for DATA_PROJECT_ROOT or any non-fixture path. No alternate config/state/registry path is accepted. The formal DATA_PROJECT_ROOT is read-only even when selected. The CLI records resolved root/config/state/run-log identities in inputs and manifest; any authority mismatch has zero state replacement, zero dispatch, zero registry mutation and only isolated error evidence.

The fixed call graph is cli.main → verify.inspect_filesystem/bind_registry_state_source, or cli.main → transaction prepare/resume/commit/finalize/duplicate-check → source-evidence load/validate (prepare) → shared precondition evaluator → storage guarded compare-and-commit → dispatcher adapter once, inside prepare's uninterrupted dispatch window (resume never reaches the dispatcher). The status command calls status.evaluate. Tests invoke the CLI subprocess and never import a second transition model. The package is the operator-facing reusable product for this task; no absent external producer is claimed.

State fixture schema (input precondition only): schema_version=2; contract_revision=1.0-rc2 for new cases; revision; current_run_id; active_writer_id; context_lock; verified_albums; and runs[]. Validation scope is exactly Rev17 §17.3: every payload the product is about to replace and every new RC2 record must validate against the versioned skill schema `schemas/schemas.json` `$defs/run` / `$defs/state` (`additionalProperties:false`), and a payload that fails that scope is refused with no write; reading an existing authority state is governed only by §16.5's legacy read contract and is never gated by this sentence. A run therefore contains no `owner_id` and no `source_provenance` field (both would violate the schema): ownership is `active_writer_id` plus `intent.owner_execution_id`, and provenance is the §15.2 binding reference carried in the run's checkpoint-shaped `events[]` `evidence` string and in `verified_albums[].evidence`. Each run must contain run_id, mode, group_key, fingerprint {start_date,end_date,expected_images}, observed_title, title_confidence, destination, contract_revision, workflow_outcome, phase, checkpoint, intent_state, dispatch_state, dispatch_evidence, intent {action_id,committed_at,owner_execution_id,group_key,fingerprint,destination,calibration,save_all_retry_allowed,dispatch_outcome,trigger_outcome}, events, reconciliations, manual_reconciliation_required and reconciliation_reason. Case-01's literal initial fixture is recorded at /private/tmp/line-backup-acceptance-case-01/input-state.json with RUN-CASE-01, WRITER-CASE-01, target key line:jp.naver.line.mac:旻謙允禎成長日記, fingerprint 2024-05-13/2024-05-17/57, and destination /private/tmp/line-backup-acceptance-case-01/destination. Fixture creation establishes preconditions only; the independent oracle is computed before product execution.

Concrete case directories and command protocol:

- CASE_ROOT_01=/private/tmp/line-backup-acceptance-case-01 through CASE_ROOT_25=/private/tmp/line-backup-acceptance-case-25 (Rev16 §16.2–§16.5, §16.7) are literal paths, not runtime placeholders. Every case records the expanded argv in inputs.json.
- Case 01 is the closed-loop integration case (Rev15 §15.1/§15.2, supersedes the Rev14 prepare→resume→commit→finalize order): prepare **with the in-process dispatch adapter** (`--source-evidence` + `--dispatcher`/`--dispatch-counter` + `--dispatcher-outcome RETURNED`) → verify-only run 1 (the product verifier's JSON, which commit/finalize consume) → commit → finalize VERIFIED → verify-only run 2 (closed loop, `source_status=CONFIRMED`) → duplicate-check `SKIP_DUPLICATE` → same-fingerprint different-destination prepare refused → terminal resume `SKIP_TERMINAL`, all under CASE_ROOT_01 with the literal state, destination, source-evidence, verification, evidence, dispatcher and counter paths.
- Case 02 injects the crash window on **prepare**: dispatcher-crash-after-side-effect.py with --crash-after-dispatch leaves revision 1 INTENT_COMMITTED with one counter line, then a fresh reconciliation-only resume --no-dispatch under CASE_ROOT_02 commits the ambiguity barrier once (revision 2).
- Case 03 injects the unknown outcome on prepare: dispatcher-unknown.py with --dispatcher-outcome UNKNOWN commits the pre-dispatch barrier (revision 2), invokes the adapter once and exits 1 DISPATCH_UNKNOWN, then the fresh resume --no-dispatch is idempotent at revision 2 under CASE_ROOT_03.
- Case 04 runs duplicate-check then a terminal reconciliation resume (no adapter options) under CASE_ROOT_04; duplicate-check must return SKIP_DUPLICATE, the matching terminal resume must return SKIP_TERMINAL, both exit 0, and counter line count must remain 0. A resume carrying adapter options is a separate row and must return INVALID_INPUT exit 2 with no write.
- Case 05 launches two commit subprocesses using expected-revision 1 and expected-owner-id WRITER-CASE-05, both pause at COMMIT_BEFORE_REPLACE on literal barrier /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier; release the single barrier once, accept either winner identity, and require the other exact stale-revision conflict.
- Case 06 invokes commit with expected-owner-id WRITER-CASE-06-WRONG against current owner WRITER-CASE-06; exact result CONFLICT_OWNER_RUN and exit 4.
- Case 07 launches two `transaction prepare` subprocesses against one shared fresh state, each with a distinct run-id/owner-id and the same test-only `--pause-at ACQUIRE_BEFORE_LOCK --barrier-file /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier`; release that one barrier once, then compare one prepared winner with one exact conflict. There is no undeclared acquisition or finalization command.
- Case 08 invokes commit with --test-mode --storage-fault WRITE_BEFORE_REPLACE under CASE_ROOT_08; exact exit 1 and no replacement.
- Case 09 invokes finalize with --test-mode --storage-fault READBACK_UNCERTAIN_AFTER_REPLACE under CASE_ROOT_09, then fresh resume --no-dispatch; finalize exits 1 with READBACK_UNCERTAIN, while independent reload sees terminal VERIFIED revision 3 with released owner/context, returns SKIP_TERMINAL exit 0 and dispatches nothing.
- Case 10 invokes finalize --outcome VERIFIED under CASE_ROOT_10 and independently checks one replacement containing verification, registry, workflow_outcome, active_writer_id=null and context_lock=null. Its required subcase 10B invokes finalization with SAFE_ABORT against a separate isolated state and checks unresolved intent preservation, no registry addition and released ownership.
- Cases 11 and 12 use literal legacy and contradictory input-state.json under their case roots; duplicate-check and status evaluate only, with no normalization or dispatch.

Test-only fault flags are rejected unless --test-mode is present and the state path is under /private/tmp (the production adapter pair --dispatcher/--dispatch-counter on prepare is not a fault flag). Storage faults are separate from dispatcher faults. All process commands record stdout, stderr, exit, state/counter bytes and hashes.

## Critical path

1. Preserve/index historical failure evidence and independently reproduce the old verifier's 56/58 false-positive in isolated paths.
2. After the current revision's independent approval (Rev15 at handoff time), continue the named product package/CLI and evidence repair; prove the package is the only operator process boundary for the new reusable verifier/transaction deliverable.
3. Implement structured fail-closed verify-only and the state/source outcome contract.
4. Implement transaction resume/commit/duplicate paths with shared serialized compare-and-commit, deterministic fault/race injection, and real subprocess restart tests.
5. Run all verifier axis-correct negative cases, transaction cases, status/closure cases, then run the product verifier against DATA_DESTINATION without formal-state mutation.
6. Reconcile current source identity and state/registry/intent/writer evidence. Current default from existing evidence is SOURCE_CORRESPONDENCE=UNRESOLVED and STATE_ASSOCIATION=LEGACY_PROVENANCE_LIMITED; this stops exact goal acceptance while still reporting filesystem findings.
7. Check documented CUA capability and the existing ledger. If route evidence remains necessary, request exactly one fresh controlled observation gate. This gate permits one ellipsis GUI input only, never Save-All/menu-item/chooser/state writes. A later production Save-All route requires a separate later approved plan revision, fresh review, and a separate one-time production gate.

## Requirement, current evidence, and closure

| Requirement | Current evidence | Rev12 closure | Class | Closure gate |
|---|---|---|---|---|
| Existing destination is 57 complete images | Direct canonical audit reports 57 stable images and 17,924,900 bytes; old verifier is not trustworthy | Product CLI must independently pass filesystem oracle and artifact read-back | CORE / OUTCOME | HARD_CLEAN |
| Exact source correspondence | Request uses 禎; config/state use 楨; legacy run title/provenance UNKNOWN | Emit tri-state result; unresolved/contradicted blocks exact goal acceptance and production route | CORE / OUTCOME | HARD_CLEAN |
| State/registry/intent/writer consistency | State revision 39 is clean, but target run is legacy and lacks full provenance/hash fields | Bind one exact record; report legacy limitations; transaction uses guarded revision/owner commit | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Reusable interruption/recovery/duplicate behavior | Existing fixture is self-authenticating; no actual process exists | New product CLI/library is the real deliverable and must pass subprocess restart/fault/race oracles | CORE / MUST_NOT_BREAK | HARD_CLEAN |
| Current Save-All route decision | Historical menu observation found no affirmative Save All; controller/bridge are read-only observation tools | Separate route status from offline acceptance; only controlled observation may establish candidate route | CORE / OUTCOME | HARD_CLEAN |
| Bridge/service | No backup-state integration | Non-gating; deploy only after route-specific causal proof and a later approved plan | SUPPORTING / DIAGNOSTIC | NON_GATING |
| Independent acceptance | Rev1/Rev2/Rev3/Rev4/Rev5/Rev6/Rev7/Rev8/Rev9/Rev10 reports exist; attempts 11/12 have snapshots without reports; attempt 13 reviewed Rev11; Rev12 was approved but Stage 05 attempt 02 rejected evidence | Fresh review of the current revision (Rev15) and its exact hash, then Stage 05 acceptance of actual CLI/evidence | CORE / MUST_NOT_BREAK | HARD_CLEAN |

## Source, registry, and legacy outcome contract

SOURCE_CORRESPONDENCE:

- CONFIRMED: one authoritative record joins exact target app/group key, complete album fingerprint, and destination, or one precise user fact establishes that the raw strings refer to the same source while preserving an immutable evidence-only record. A user fact does not rewrite config/state.
- UNRESOLVED: spelling similarity, a destination match, a fingerprint match, historical GUI evidence without a source join, or a legacy run with unknown title/provenance. Filesystem may be PASS; PRIMARY_OUTCOME_STATUS is UNKNOWN and the source/core check is BLOCKED, so production route is forbidden.
- CONTRADICTED: authoritative title/group/source evidence differs from the requested source or fingerprint. Overall primary outcome is NOT_ACHIEVED; production route is forbidden.
- The verifier outputs both raw group strings, keys, authority/source, question/answer/timestamp for any exceptional user fact, and unchanged legacy record/run IDs.

STATE_ASSOCIATION:

- EXACT: exactly one registry object contains the same group_key, start/end/count fingerprint, and destination object; no cross-entry field mixing.
- ABSENT or AMBIGUOUS: registry CHECK_RESULT=FAIL; never use first match.
- LEGACY_PROVENANCE_LIMITED: legacy record is preserved, read-only normalization may describe missing contract_revision/formula calibration, but it cannot prove exact source or authorize dispatch.
- STATE_CONTRADICTED: inconsistent revision, owner, run, intent, dispatch, registry, or terminal axes; hard failure.
- Formal state is never mutated by verify-only, tests, or this acceptance wave.

User-fact evidence format, if the user supplies it:

- raw_requested_group, raw_persisted_group, app bundle, album/date/count;
- exact question asked and exact answer;
- supplied_by, supplied_at, evidence artifact SHA-256;
- unchanged config/state/registry/run IDs and legacy fields;
- SOURCE_CORRESPONDENCE result.
The default current result remains UNRESOLVED until this evidence exists.

## Product verifier oracle and failure containment

The product verify-only CLI receives explicit project root, config, state, destination, target key/fingerprint, and evidence directory. It never discovers, substitutes, or mutates roots. Exit semantics are fixed: exit 0 only when all required acceptance axes pass; exit 4 for a completed, safely rejected negative/blocked result; exit 1 for internal/read/command/artifact errors; exit 2 for invalid invocation/configuration. It must:

- Validate schema and absolute configured backup_root. Resolve real paths and require DATA_DESTINATION to be a real existing directory contained under the configured backup_root. Reject a symlinked destination root, symlinked ancestor that changes the resolved authority, and every resolution/read error.
- Enumerate immediate entries with lstat and no symlink following. Reject symlink entries, subdirectories, special files, hidden entries including .DS_Store and ._* and __MACOSX, and all required suffixes: .part, .partial, .tmp, .temp, .download, .crdownload, .incomplete, .filepart.
- Require exactly 57 regular recognized image files, no zero bytes, no unrecognized regular files, no partial/temp/hidden/other entries. Use real file MIME/content detection and a deterministic error path; file-command failures are hard failures.
- Emit per-entry relative_path, size, mtime_ns, MIME, SHA-256, and read/error status. Compare complete sorted entry tuples across three samples, including required metadata and bytes, and compare total bytes separately. Preserve both pre/post inventories when a deterministic mutator changes bytes or mtime between samples.
- Preserve arbitrary safe filenames including Unicode, spaces, pipes, and newlines through structured JSON; never use an unescaped delimiter line as the oracle.
- Bind registry association using one exact group_key + complete fingerprint + destination object. Reject absent, ambiguous, cross-entry, or wrong-group matches. Report filesystem, registry, source, state, and overall statuses independently.
- Write evidence only below the supplied evidence directory, atomically where possible, with a SHA-256/byte-length manifest. Any exception, read error, command error, malformed state, or artifact read-back failure is nonzero and never emits an overall PASS.

## Current formal config and legacy-state compatibility profile

The real verify-only command must accept the current authority without initializing or mutating it. The measured DATA_CONFIG is schema_version=2, 372 bytes, and contains exactly these required keys: schema_version, group_key, group_name, backup_root, app_identifier, max_albums_per_run, recovery_limit, poll_interval_seconds, stable_samples, max_wait_seconds. A config missing any of these required keys, with a wrong type, relative backup_root, wrong app_identifier, or invalid count/sample/wait value is INVALID_CONFIGURATION, exit 2, with filesystem/registry/source/state axes NOT_RUN and no evidence claiming PASS. The current config contains all required keys, so it is not a missing-config case.

Verify-only accepts state schema_version=2 with the current top-level authority fields active_writer_id, context_lock, current_run_id, revision, runs and verified_albums. A run without contract_revision, RC2-only intent fields, or full source title/provenance is a readable LEGACY record, not a new-run default. Missing legacy fields are represented as UNKNOWN or null with the raw run preserved; they are never initialized, rewritten, or treated as affirmative NOT_ATTEMPTED. The current target record therefore produces filesystem findings independently, but its missing contract revision/title/provenance produces STATE=LEGACY_PROVENANCE_LIMITED and SOURCE=UNRESOLVED, not an exact acceptance.

The target argument group key may validly differ from config.group_key during this read-only comparison. That is a valid config plus a source/registry mismatch, not a schema error: with the current requested 禎 key and persisted 楨 key, expected real-command axes are Filesystem=PASS, Registry=FAIL, Source=UNRESOLVED, State=LEGACY_PROVENANCE_LIMITED, Overall=UNKNOWN, exit 4. A config/schema failure is the only case that uses exit 2; an internal read/command/artifact failure uses exit 1. Mutating transaction fixtures use the complete RC2 input schema separately and cannot be used to rewrite current formal state.

## Axis-correct verifier fixture matrix

Each row runs the product CLI in a fresh isolated project/evidence directory and independently checks exact statuses, exit code, output schema, and artifact manifest read-back. No row writes DATA_STATE. Each completed row records result.json, inventory-1.json, inventory-2.json, inventory-3.json when sampling began, manifest.json, stdout.log, stderr.log, and exit-code. Internal artifact failures are a separate class and cannot claim PASS.

| Case | Filesystem | Registry | Source | State | Overall | Exit | Failure class | Artifact read-back |
|---|---|---|---|---|---|---|---|---|
| 57 valid images and exact association | PASS | PASS | CONFIRMED | EXACT | PASS | 0 | NONE | PASS |
| 56 images | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| 58 images | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .part file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .partial file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .tmp file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .temp file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .download file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .crdownload file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .incomplete file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| One .filepart file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| .DS_Store, ._hidden, or __MACOSX | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Symlinked destination root/ancestor or symlink entry | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Destination outside backup_root | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Special file | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Unreadable regular file | FAIL | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_READ_ERROR | PASS |
| file-command failure | FAIL | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_COMMAND_ERROR | PASS |
| Text bytes named .jpg or MIME/content mismatch | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Safe Unicode/pipe/newline/space filenames | PASS | PASS | CONFIRMED | EXACT | PASS | 0 | NONE | PASS |
| mtime changed at SAMPLE_2_READY barrier | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| bytes changed at SAMPLE_2_READY barrier | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Wrong group_key with valid files and same fingerprint/destination | PASS | FAIL | CONTRADICTED | EXACT | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Cross-entry group/fingerprint/destination mix | PASS | FAIL | UNRESOLVED | STATE_CONTRADICTED | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Legacy/imported record without contract_revision or binding, `verified_run_id` null | PASS | PASS | UNRESOLVED | LEGACY_PROVENANCE_LIMITED | UNKNOWN | 4 | INPUT_PROVENANCE_LIMITED | PASS |
| Duplicate registry entries | PASS | FAIL | UNRESOLVED | AMBIGUOUS | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Invalid configuration | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | UNKNOWN | 2 | INVALID_CONFIGURATION | PASS |
| Mismatched project-root/config/state authority | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | UNKNOWN | 2 | INVALID_AUTHORITY | PASS_WITH_NO_STATE_WRITE |
| Evidence manifest write/read-back failure | PASS | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_ARTIFACT_ERROR | FAIL_WITH_ERROR_ARTIFACT |
| PNG truncated before IEND (MIME valid) | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| JPEG whose segment walk ends without EOI | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Recognized image MIME outside JPEG/PNG (fail-closed) | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_ACHIEVED | 4 | UNSUPPORTED_IMAGE_TYPE | PASS |
| Read error in samples 1–2 with clean sample 0 (R5(c) variance) | FAIL | NOT_RUN | NOT_RUN | UNKNOWN | UNKNOWN | 1 | INTERNAL_READ_ERROR | PASS |
| `verified_run_id` non-null but unresolvable (dangling link) | PASS | FAIL | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| `verified_run_id` → terminal SAFE_ABORT run | PASS | FAIL | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| `verified_run_id` → non-terminal run | PASS | FAIL | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Linked run's group_key differs from the entry/request | PASS | FAIL | CONTRADICTED | STATE_CONTRADICTED | NOT_ACHIEVED | 4 | INPUT_NEGATIVE | PASS |
| Forged/product-authored binding reference | PASS | PASS | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_PROVENANCE_LIMITED | PASS |
| Binding artifact deleted after finalize | PASS | PASS | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_PROVENANCE_LIMITED | PASS |
| Binding artifact mutated by one byte after finalize | PASS | PASS | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_PROVENANCE_LIMITED | PASS |
| `fixture:` binding presented to production verify-only | PASS | PASS | UNRESOLVED | EXACT | NOT_ACHIEVED | 4 | INPUT_PROVENANCE_LIMITED | PASS |

Registry-axis rule (Rev15 §15.4): Registry is association integrity only — PASS requires a unique readable match whose group_key/fingerprint/destination equal the request exactly and whose `verified_run_id`, when non-null, resolves to a same-state run with `workflow_outcome=VERIFIED` (Rev16 §16.8 supersedes the former "terminal run" wording); absent, ambiguous, duplicated, wrong-group, dangling, non-terminal and SAFE_ABORT-linked ids are FAIL; a null `verified_run_id` is the contract's imported-evidence form (Registry PASS, Source UNRESOLVED). Provenance failures (binding absent, unreadable, escaping, hash-mismatched, content-mismatched, `fixture:` in production) never flip the Registry axis. The rows asserting Source UNRESOLVED and exit 4 for binding defects are the required negative controls of §15.2.

A row with an internal read/command/artifact error has exact UNKNOWN overall because the verifier cannot safely conclude the requested result. No alternative exit is permitted. A result-schema test rejects any value from another subject enum, such as NOT_ACHIEVED in the State axis or EXACT in the Filesystem axis. Filesystem PASS never implies registry/source/state PASS; registry/source-only defects retain filesystem PASS.

The authority negative has one literal subprocess command: `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /private/tmp/line-backup-acceptance-authority/root-a --config /private/tmp/line-backup-acceptance-authority/root-b/config/line_backup_config.json --state /private/tmp/line-backup-acceptance-authority/root-b/state/backup_state.json --destination /private/tmp/line-backup-acceptance-authority/root-a/destination --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence`. Its independently recorded pre/post hashes must show no read or write of `/private/tmp/line-backup-acceptance-authority/root-a` or `root-b` authority state/config, no registry/dispatch action, exit 2, and an error result with `INVALID_AUTHORITY`; only the isolated evidence directory may be written. The authority fixture is included in the verifier acceptance manifest alongside Cases 01–25.

The authority manifest preserves six literal test-only authority negatives, but uses only the allowlisted fixture roots so the cases reach canonical-path validation instead of being rejected by an unrelated root policy. From cwd `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` with `PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src`, the rows are: (1) `transaction prepare --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-02/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-02/state/run_log.md --state /private/tmp/line-backup-acceptance-case-02/state/backup_state.json --run-id AUTH-PREPARE --owner-id AUTH-WRITER --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-01/destination --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence/authority-prepare --test-mode`, (2) `transaction resume --project-root /private/tmp/line-backup-acceptance-case-03 --config /private/tmp/line-backup-acceptance-case-04/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-04/state/run_log.md --state /private/tmp/line-backup-acceptance-case-04/state/backup_state.json --run-id AUTH-RESUME --expected-revision 1 --expected-owner-id AUTH-WRITER --dispatcher /private/tmp/line-backup-acceptance-case-03/dispatcher.py --dispatch-counter /private/tmp/line-backup-acceptance-case-03/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-03/evidence/authority-resume --no-dispatch --test-mode`, (3) `transaction commit --project-root /private/tmp/line-backup-acceptance-case-05 --config /private/tmp/line-backup-acceptance-case-06/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-06/state/run_log.md --state /private/tmp/line-backup-acceptance-case-06/state/backup_state.json --run-id AUTH-COMMIT --expected-revision 1 --expected-owner-id AUTH-WRITER --verification-json /private/tmp/line-backup-acceptance-case-05/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-05/evidence/authority-commit --test-mode`, (4) `transaction finalize --project-root /private/tmp/line-backup-acceptance-case-07 --config /private/tmp/line-backup-acceptance-case-08/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-08/state/run_log.md --state /private/tmp/line-backup-acceptance-case-08/state/backup_state.json --run-id AUTH-FINALIZE --expected-revision 1 --expected-owner-id AUTH-WRITER --outcome SAFE_ABORT --verification-json /private/tmp/line-backup-acceptance-case-07/verification.json --evidence-dir /private/tmp/line-backup-acceptance-case-07/evidence/authority-finalize --test-mode`, and (5) `transaction duplicate-check --project-root /private/tmp/line-backup-acceptance-case-09 --config /private/tmp/line-backup-acceptance-case-10/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-10/state/run_log.md --state /private/tmp/line-backup-acceptance-case-10/state/backup_state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-09/destination --evidence-dir /private/tmp/line-backup-acceptance-case-09/evidence/authority-duplicate --test-mode`. The sixth literal parser negative omits `--project-root`: `transaction resume --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id AUTH-NO-ROOT --expected-revision 1 --expected-owner-id AUTH-WRITER --dispatcher /private/tmp/line-backup-acceptance-case-01/dispatcher.py --dispatch-counter /private/tmp/line-backup-acceptance-case-01/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence/authority-no-root --no-dispatch --test-mode`. Each expected result is `INVALID_AUTHORITY`, exit 2 before state read/write or lock creation; the independent oracle hashes the selected and mismatched fixture states before and after, verifies zero counter lines/replacements/registry-owner changes, and retains each inputs/stdout/stderr/exit/result/manifest hash.

The same manifest adds five literal production-mode negatives against `/private/tmp/line-backup-acceptance-authority/production-root` (which has canonical `config/line_backup_config.json`, `state/backup_state.json`, `state/run_log.md`, and a contained destination prepared independently): (1) `transaction prepare --project-root /private/tmp/line-backup-acceptance-authority/production-root --run-log /private/tmp/line-backup-acceptance-authority/production-root/state/run_log.md --state /private/tmp/line-backup-acceptance-authority/production-root/state/backup_state.json --run-id AUTH-PROD-PREPARE --owner-id AUTH-PROD-WRITER --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-authority/production-root/destination --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence/prod-prepare`, with `--config` omitted; (2) `transaction resume --project-root /private/tmp/line-backup-acceptance-authority/production-root --config /private/tmp/line-backup-acceptance-authority/alternate/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-authority/production-root/state/run_log.md --state /private/tmp/line-backup-acceptance-authority/production-root/state/backup_state.json --run-id AUTH-PROD-RESUME --expected-revision 1 --expected-owner-id AUTH-PROD-WRITER --dispatcher /private/tmp/line-backup-acceptance-authority/dispatcher.py --dispatch-counter /private/tmp/line-backup-acceptance-authority/counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence/prod-resume --no-dispatch`; (3) `transaction commit --project-root /private/tmp/line-backup-acceptance-authority/production-root --config /private/tmp/line-backup-acceptance-authority/production-root/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-authority/alternate/state/run_log.md --state /private/tmp/line-backup-acceptance-authority/production-root/state/backup_state.json --run-id AUTH-PROD-COMMIT --expected-revision 1 --expected-owner-id AUTH-PROD-WRITER --verification-json /private/tmp/line-backup-acceptance-authority/production-root/verification.json --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence/prod-commit`; (4) `transaction finalize --project-root /private/tmp/line-backup-acceptance-authority/production-root --config /private/tmp/line-backup-acceptance-authority/production-root/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-authority/production-root/state/run_log.md --state /private/tmp/line-backup-acceptance-authority/alternate/state/backup_state.json --run-id AUTH-PROD-FINALIZE --expected-revision 1 --expected-owner-id AUTH-PROD-WRITER --outcome SAFE_ABORT --verification-json /private/tmp/line-backup-acceptance-authority/production-root/verification.json --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence/prod-finalize`; and (5) `transaction duplicate-check --project-root /private/tmp/line-backup-acceptance-authority/production-root --config /private/tmp/line-backup-acceptance-authority/production-root/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-authority/production-root/state/run_log.md --state /private/tmp/line-backup-acceptance-authority/production-root/state/backup_state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-authority/outside-destination --evidence-dir /private/tmp/line-backup-acceptance-authority/evidence/prod-duplicate`. These five no-`--test-mode` cases must all return `INVALID_AUTHORITY`, exit 2 before config/state/lock reads or any mutation; the independently computed oracle retains pre/post hashes for every canonical authority file, alternate path, lock/control directory, counter, registry/owner fields and replacement count. A missing required production authority option is normalized to `INVALID_AUTHORITY` rather than an ordinary usage success, so all authority failures have one stable safety result. These eleven authority rows are included in the acceptance manifest and cannot be satisfied by a product PASS line.

Verifier fixture manifest and independent subprocess driver:

- `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/verifier_fixture_driver.py` consumes the literal manifest `/private/tmp/line-backup-acceptance-verifier/fixture-manifest.json` and is the only fixture orchestrator for the verifier matrix. Its exact invocation is `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/verifier_fixture_driver.py --manifest /private/tmp/line-backup-acceptance-verifier/fixture-manifest.json --evidence-dir /private/tmp/line-backup-acceptance-verifier/evidence --summary /private/tmp/line-backup-acceptance-verifier/summary.json`. The manifest enumerates every matrix row by these literal IDs: `valid-57`, `count-56`, `count-58`, `part-suffix`, `partial-suffix`, `tmp-suffix`, `temp-suffix`, `download-suffix`, `crdownload-suffix`, `incomplete-suffix`, `filepart-suffix`, `hidden-metadata`, `symlink-entry`, `outside-backup-root`, `special-file`, `unreadable-file`, `file-command-error`, `mime-mismatch`, `safe-filenames`, `mtime-at-sample-2`, `bytes-at-sample-2`, `wrong-group`, `cross-entry`, `legacy-record`, `duplicate-registry`, `invalid-config`, `authority-mismatch`, `artifact-readback-failure`, `truncated-png`, `jpeg-missing-eoi`, `unsupported-image-type`, `read-error-sample-2`, `dangling-verified-run-id`, `safe-abort-linked`, `nonterminal-linked`, `wrong-group-link`, `forged-binding`, `binding-artifact-deleted`, `binding-artifact-mutated`, and `fixture-binding-in-production`. The twelve Rev15 rows are created by the driver as isolated fixture preconditions (binding rows reuse a valid finalize then delete/mutate the external artifact at its recorded path); `read-error-sample-2` uses the declared `--test-mode --pause-at SAMPLE_2_READY` barrier with a mutator that makes the read fail from sample 2 onward.
- Each manifest row contains literal absolute `project_root`, `config`, `state`, `run_log`, `destination`, `evidence_dir`, `fixture-precondition`, `stdout`, `stderr`, `exit-code`, `result`, `manifest`, `inventory-1`, `inventory-2`, and `inventory-3` paths, the complete verify-only argv, expected Filesystem/Registry/Source/State/Overall values and exit, and the independent oracle rule. The driver creates only fixture preconditions, hashes all pre-state inputs, launches the real `line_backup_acceptance verify-only` subprocess, and independently computes count/content/containment/registry/source/state expectations before reading result output. It separately records all subprocess stdout/stderr/exit and artifact hashes/byte lengths. It never writes expected status constants into product state and never accepts a product PASS line as evidence.
- `mtime-at-sample-2` and `bytes-at-sample-2` use the declared verify-only `--test-mode --pause-at SAMPLE_2_READY --barrier-file` with literal `/private/tmp/line-backup-acceptance-verifier/<id>.barrier`; the independent driver changes the fixture only after the product reaches that barrier, releases it once, and checks the product rejects the changed inventory. `authority-mismatch` is the literal no-write command above and is included in the same manifest. `artifact-readback-failure` makes only the isolated evidence target fail and requires the product to emit a nonzero error artifact without claiming overall PASS. A missing manifest row, missing literal argv, failed independent pre-state hash, or absent read-back artifact is itself a required-verification failure.

## Transaction product contract and deterministic acceptance matrix

The operator-facing transaction CLI is the product process. The package contains no second test transaction model.

Fixed state and serialization protocol:

- For state path P, every prepare/resume/commit/finalize/duplicate operation uses the exact lock path dirname(P)/.line-backup-state.lock and POSIX flock LOCK_EX. The lock is acquired before authoritative load and held through expected-revision/owner validation, replacement, fsync/read-back and release. duplicate-check uses the same lock for its final association read.
- A commit accepts only when loaded revision equals expected-revision, current_run_id equals expected-run-id, active_writer_id equals expected-owner-id for non-terminal mutation, and immutable intent/dispatch/trigger fields equal the prepared payload. Mismatch returns one exact conflict result with exit 4, writes nothing and never dispatches.
- A prepare accepts only when the loaded state has no active current_run/owner/context lock for the requested acquisition scope. If another prepare wins first, the loser returns exactly `CONFLICT_ACTIVE_RUN`, exit 4, writes no replacement and does not create a second run/owner record. The winner identity may vary with process scheduling and is not an acceptance precondition. The deterministic, winner-independent assertion is exactly one `PREPARED`/state replacement and exactly one `CONFLICT_ACTIVE_RUN` exit 4/no replacement; the driver records whichever literal process is independently proven to own the post-state.
- A resume against a matching terminal run at the expected revision returns exactly `SKIP_TERMINAL`, exit 0, without requiring a live owner, without replacement and without dispatch. A mismatched terminal fingerprint or revision remains a conflict exit 4.
- Replacement uses a same-directory temp file, fsyncs it, os.replace, fsyncs the directory when supported, reopens and validates schema/revision/owner/run/intent/registry/terminal fields, and records available durability protection.
- The shared lock covers acquire, resume, commit, finalize, duplicate skip and cleanup. A delayed payload cannot commit after a competing winner. Deterministic barrier files, not timing or sleep, control race order.
- Storage faults are separate from dispatcher faults: WRITE_BEFORE_REPLACE fails before replacement; READBACK_UNCERTAIN_AFTER_REPLACE replaces the exact final payload and then makes the first process return `READBACK_UNCERTAIN`, exit 1, without changing that committed payload. A fresh resume with --no-dispatch reloads authoritative state, returns `SKIP_TERMINAL`, exit 0 for the already-finalized run, and never replays a prepared dispatch. The first-process uncertainty remains separately recorded in its raw logs/result.
- The injected dispatcher writes one JSON line to an independently read counter before returning or exiting. The product never reads that counter to decide success. The fake is injected only at the final side-effect adapter.
- Only finalize can set VERIFIED or final SAFE_ABORT. It commits verification, registry when applicable, workflow outcome, terminal evidence, active_writer_id=null and context_lock=null in one guarded replacement. Duplicate precedence is explicit and stable: terminal exact `duplicate-check` returns `SKIP_DUPLICATE`; a matching terminal `resume` returns `SKIP_TERMINAL`. Both are exit 0, no-replacement, no-dispatch outcomes, but a result from one operation must never be substituted for the other in an oracle or report.
- New runs use contract_revision=1.0-rc2 and preserve separate intent_state, dispatch_state, trigger_outcome, dispatch_outcome, retry permission, evidence, events and reconciliations. Legacy records are read-only normalized in reports.

Exact subprocess command grammar and case protocol:

- Case roots are literal /private/tmp/line-backup-acceptance-case-01 through /private/tmp/line-backup-acceptance-case-25 (Rev16 §16.1/§16.7). Every recorded inputs.json contains fully expanded literal argv; the documentation names, the shorthand suffix `-NN` and the `…` ellipsis below are documentation abbreviations only and are never passed to a process as variables, and the driver rejects any argv containing an ellipsis or naming a non-existent root.
- Prepare command uses transaction prepare with --project-root, the canonical children `--config CASE_ROOT_NN/config/line_backup_config.json --run-log CASE_ROOT_NN/state/run_log.md --state CASE_ROOT_NN/state/backup_state.json` (Rev17 §17.1; `--state CASE_ROOT_NN/state.json` is not legal), run-id, owner-id, --source-evidence, exact group-key, dates, count, destination, --dispatcher, --dispatch-counter and evidence-dir. Rev15 §15.1 moved the dispatch window into prepare: a prepare without the adapter pair is refused `MISSING_DISPATCHER` exit 2 with no write, and a prepare without --source-evidence is refused `MISSING_SOURCE_EVIDENCE` exit 2 with no write.
- Resume command uses transaction resume with --project-root, the same canonical children (`--config`, `--run-log`, `--state`; Rev17 §17.1), run-id, expected-revision, expected-owner-id, evidence-dir and (where a reload path is documented) --no-dispatch. Resume never dispatches in any mode: --no-dispatch is accepted and is a semantic no-op, and supplying --dispatcher, --dispatch-counter, --crash-after-dispatch or a non-default --dispatcher-outcome returns `INVALID_INPUT` exit 2 with no write, evaluated after authority validation and before any state read (Rev15 §15.1). Other test-only fault flags are accepted only for literal case roots with --test-mode.
- Commit command uses transaction commit with --project-root, the canonical children (`--config`, `--run-log`, `--state`; Rev17 §17.1), run-id, expected-revision, expected-owner-id, verification-json and evidence-dir; it refuses with `CONFLICT_UNRESOLVED_DISPATCH` exit 4 and no write unless the loaded run carries the completed successful dispatch record (§15.1). Finalization uses transaction finalize with the same --project-root and canonical children (`--config`, `--run-log`, `--state`), expected revision/owner, explicit outcome VERIFIED or SAFE_ABORT, verification-json and evidence-dir; `--verification-json` is required for `--outcome VERIFIED` and optional for `SAFE_ABORT` (Rev17 §17.9; when supplied with SAFE_ABORT it must still be a readable JSON object and is never consulted for success); --outcome VERIFIED additionally requires the §15.2 binding and the §16.3/§17.2 evidence chain, and otherwise refuses `BINDING_UNVERIFIED` or the chain's refusal class, exit 4 with no write.
- Duplicate command uses transaction duplicate-check with --project-root, the canonical children (`--config`, `--run-log`, `--state`; Rev17 §17.1), exact group-key, dates, count, destination and evidence-dir. It is read-only, and it returns the shared evaluator's refusal classes (`CONFLICT_DUPLICATE_FINGERPRINT`, `AMBIGUOUS_FINGERPRINT`, `NEEDS_RECONCILIATION`, exit 4) whenever a conflicting or unresolved same-group association or intent exists.
- Status command uses status evaluate with a literal case input and output path. It is read-only.
- The exact Case-01 prepare argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction prepare --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id RUN-CASE-01 --owner-id WRITER-CASE-01 --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-01/destination --source-evidence /private/tmp/line-backup-acceptance-case-01/source-evidence.json --dispatcher /private/tmp/line-backup-acceptance-case-01/dispatcher-returned.py --dispatch-counter /private/tmp/line-backup-acceptance-case-01/dispatch-counter.jsonl --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode --dispatcher-outcome RETURNED
- The exact Case-01 verifier argv pair is (run 1 before commit, run 2 after finalize): cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance verify-only --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --destination /private/tmp/line-backup-acceptance-case-01/destination --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --run-id RUN-CASE-01 --test-mode --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence/verify-1 ; and the byte-identical argv with --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence/verify-2 for run 2 (Rev17 §17.1/§17.2: `--test-mode` is required and `--run-id` is what makes the result consumable).
- The exact Case-01 commit argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction commit --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id RUN-CASE-01 --expected-revision 2 --expected-owner-id WRITER-CASE-01 --verification-json /private/tmp/line-backup-acceptance-case-01/evidence/verify-1/result.json --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode
- The exact Case-01 finalize argv is: cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction finalize --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id RUN-CASE-01 --expected-revision 3 --expected-owner-id WRITER-CASE-01 --outcome VERIFIED --verification-json /private/tmp/line-backup-acceptance-case-01/evidence/verify-1/result.json --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode
- The exact Case-01 closing argv triple is: (a) cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction duplicate-check --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --group-key 'line:jp.naver.line.mac:旻謙允禎成長日記' --start-date 2024-05-13 --end-date 2024-05-17 --expected-images 57 --destination /private/tmp/line-backup-acceptance-case-01/destination --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --test-mode ; (b) the otherwise identical prepare argv (therefore with the same canonical children) with --destination /private/tmp/line-backup-acceptance-case-01/destination-2 --run-id RUN-CASE-01-B --owner-id WRITER-CASE-01-B and --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence/refusal ; (c) cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 -m line_backup_acceptance transaction resume --project-root /private/tmp/line-backup-acceptance-case-01 --config /private/tmp/line-backup-acceptance-case-01/config/line_backup_config.json --run-log /private/tmp/line-backup-acceptance-case-01/state/run_log.md --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --run-id RUN-CASE-01 --expected-revision 4 --expected-owner-id WRITER-CASE-01 --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence --no-dispatch --test-mode
- The exact Case-04 duplicate argv is unchanged and uses /private/tmp/line-backup-acceptance-case-04 with the same literal group key, dates, count, destination, --test-mode and that root's canonical `--config`/`--run-log`/`--state` children (Rev17 §17.1).
- The exact Case-07 prepare argv pair is the Case-01 prepare argv with --run-id/--owner-id RUN-CASE-07-A/WRITER-CASE-07-A and RUN-CASE-07-B/WRITER-CASE-07-B, --evidence-dir evidence-a/evidence-b, --pause-at ACQUIRE_BEFORE_LOCK and --barrier-file /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier; both include --source-evidence and the adapter pair, and the dispatcher must never run for the loser.
- Cases 02/03 inject the fault on prepare (--crash-after-dispatch or --dispatcher-outcome UNKNOWN) and then use one fresh literal resume --no-dispatch as the reconciliation step. Case 05 uses barrier /private/tmp/line-backup-acceptance-case-05/commit-ready.barrier and releases it once. Case 07 uses only the single barrier /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier and has no fixed scheduler-selected winner.
- Case 08 uses commit --test-mode --storage-fault WRITE_BEFORE_REPLACE and has exact exit 1. Case 09 uses finalize --test-mode --storage-fault READBACK_UNCERTAIN_AFTER_REPLACE (with the §15.2 binding and a product-verifier JSON), exact exit 1, then a fresh resume --no-dispatch carrying no adapter options.
- Cases 11/12 use literal legacy/contradictory input JSON with status evaluate, and duplicate-check whose expected class is computed by the shared precondition evaluator; a same-fingerprint association never yields NOT_DUPLICATE. No test helper implements a transition.
- Cases 13–19 are the Rev15 refusal and unresolved-dispatch rows. Each uses its literal root /private/tmp/line-backup-acceptance-case-13 … -19 and the literal Case-01 argv shape with every `-01` replaced by its own suffix: case 13 `missing-source-evidence` (prepare without --source-evidence → `MISSING_SOURCE_EVIDENCE` exit 2, no write, no counter line); case 14 `invalid-source-evidence` (record with a mismatched fingerprint or incomplete calibration → `INVALID_SOURCE_EVIDENCE` exit 2, no write); case 15 `conflict-duplicate` (exact terminal association pre-state → duplicate-check `SKIP_DUPLICATE` exit 0 and prepare `CONFLICT_DUPLICATE` exit 4, no write); case 16 `conflict-duplicate-fingerprint` (same group+fingerprint association at a different destination → duplicate-check and prepare `CONFLICT_DUPLICATE_FINGERPRINT` exit 4, no write; the R3(a) flip); case 17 `ambiguous-fingerprint` (historical same-group same-date 56-image run → both operations `AMBIGUOUS_FINGERPRINT` exit 4, no write; the R3(c) flip); case 18 `needs-reconciliation` (historical non-terminal same-fingerprint intent → prepare `NEEDS_RECONCILIATION` exit 4, no write; positive control: the same pre-state plus a persisted schema-valid non-dispatch reconciliation with `blocking_intent_released=true` and a `$defs/non_dispatch_proof` → `PREPARED` exit 0 with exactly one counter line); case 19 `unresolved-dispatch` (prepare with --dispatcher-outcome UNKNOWN → `DISPATCH_UNKNOWN` exit 1 at revision 2; commit --expected-revision 2 → `CONFLICT_UNRESOLVED_DISPATCH` exit 4, no write; finalize --outcome SAFE_ABORT --expected-revision 2 → exit 0 revision 3, no registry entry, unresolved intent preserved). Rev16 adds literal rows 20–25: case 20 parent-SIGKILL in the dispatch window (§16.2), case 21 missing-dispatcher (§16.7), case 22 finalize verification-evidence negatives (§16.3), case 23 prepare storage faults (§16.7), case 24 user-fact CONFIRMED and merge-guard fixtures (§16.4), case 25 legacy real-state shape (§16.5).

Deterministic driver and literal case protocol:

- `tests/acceptance_case_driver.py` is only a subprocess orchestrator and independent oracle; it does not contain a transition model or write expected transition values into product state. Every case driver invocation uses literal absolute paths for `pre-state.json`, the canonical product state `CASE_ROOT/state/backup_state.json` (Rev16 §16.1), `post-state.json`, `counter.jsonl`, `result.json`, `manifest.json`, `stdout.log`, `stderr.log`, `exit-code` and `evidence/`. It writes preconditions, hashes them, invokes the real CLI argv, captures each process's raw stdout/stderr/exit, independently reads post-state/counter/result/manifest, and computes expected outcomes from the case specification before inspecting product output.
- The exact driver argv for every case is:
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 01 --case-root /private/tmp/line-backup-acceptance-case-01 --pre-state /private/tmp/line-backup-acceptance-case-01/pre-state.json --state /private/tmp/line-backup-acceptance-case-01/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-01/post-state.json --counter /private/tmp/line-backup-acceptance-case-01/counter.jsonl --result /private/tmp/line-backup-acceptance-case-01/result.json --manifest /private/tmp/line-backup-acceptance-case-01/manifest.json --stdout /private/tmp/line-backup-acceptance-case-01/stdout.log --stderr /private/tmp/line-backup-acceptance-case-01/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-01/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-01/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 02 --case-root /private/tmp/line-backup-acceptance-case-02 --pre-state /private/tmp/line-backup-acceptance-case-02/pre-state.json --state /private/tmp/line-backup-acceptance-case-02/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-02/post-state.json --counter /private/tmp/line-backup-acceptance-case-02/counter.jsonl --result /private/tmp/line-backup-acceptance-case-02/result.json --manifest /private/tmp/line-backup-acceptance-case-02/manifest.json --stdout /private/tmp/line-backup-acceptance-case-02/stdout.log --stderr /private/tmp/line-backup-acceptance-case-02/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-02/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-02/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 03 --case-root /private/tmp/line-backup-acceptance-case-03 --pre-state /private/tmp/line-backup-acceptance-case-03/pre-state.json --state /private/tmp/line-backup-acceptance-case-03/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-03/post-state.json --counter /private/tmp/line-backup-acceptance-case-03/counter.jsonl --result /private/tmp/line-backup-acceptance-case-03/result.json --manifest /private/tmp/line-backup-acceptance-case-03/manifest.json --stdout /private/tmp/line-backup-acceptance-case-03/stdout.log --stderr /private/tmp/line-backup-acceptance-case-03/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-03/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-03/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 04 --case-root /private/tmp/line-backup-acceptance-case-04 --pre-state /private/tmp/line-backup-acceptance-case-04/pre-state.json --state /private/tmp/line-backup-acceptance-case-04/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-04/post-state.json --counter /private/tmp/line-backup-acceptance-case-04/counter.jsonl --result /private/tmp/line-backup-acceptance-case-04/result.json --manifest /private/tmp/line-backup-acceptance-case-04/manifest.json --stdout /private/tmp/line-backup-acceptance-case-04/stdout.log --stderr /private/tmp/line-backup-acceptance-case-04/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-04/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-04/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 05 --case-root /private/tmp/line-backup-acceptance-case-05 --pre-state /private/tmp/line-backup-acceptance-case-05/pre-state.json --state /private/tmp/line-backup-acceptance-case-05/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-05/post-state.json --counter /private/tmp/line-backup-acceptance-case-05/counter.jsonl --result /private/tmp/line-backup-acceptance-case-05/result.json --manifest /private/tmp/line-backup-acceptance-case-05/manifest.json --stdout /private/tmp/line-backup-acceptance-case-05/stdout.log --stderr /private/tmp/line-backup-acceptance-case-05/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-05/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-05/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 06 --case-root /private/tmp/line-backup-acceptance-case-06 --pre-state /private/tmp/line-backup-acceptance-case-06/pre-state.json --state /private/tmp/line-backup-acceptance-case-06/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-06/post-state.json --counter /private/tmp/line-backup-acceptance-case-06/counter.jsonl --result /private/tmp/line-backup-acceptance-case-06/result.json --manifest /private/tmp/line-backup-acceptance-case-06/manifest.json --stdout /private/tmp/line-backup-acceptance-case-06/stdout.log --stderr /private/tmp/line-backup-acceptance-case-06/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-06/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-06/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 07 --case-root /private/tmp/line-backup-acceptance-case-07 --pre-state /private/tmp/line-backup-acceptance-case-07/pre-state.json --state /private/tmp/line-backup-acceptance-case-07/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-07/post-state.json --counter /private/tmp/line-backup-acceptance-case-07/counter.jsonl --result /private/tmp/line-backup-acceptance-case-07/result.json --manifest /private/tmp/line-backup-acceptance-case-07/manifest.json --stdout /private/tmp/line-backup-acceptance-case-07/stdout.log --stderr /private/tmp/line-backup-acceptance-case-07/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-07/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-07/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 08 --case-root /private/tmp/line-backup-acceptance-case-08 --pre-state /private/tmp/line-backup-acceptance-case-08/pre-state.json --state /private/tmp/line-backup-acceptance-case-08/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-08/post-state.json --counter /private/tmp/line-backup-acceptance-case-08/counter.jsonl --result /private/tmp/line-backup-acceptance-case-08/result.json --manifest /private/tmp/line-backup-acceptance-case-08/manifest.json --stdout /private/tmp/line-backup-acceptance-case-08/stdout.log --stderr /private/tmp/line-backup-acceptance-case-08/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-08/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-08/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 09 --case-root /private/tmp/line-backup-acceptance-case-09 --pre-state /private/tmp/line-backup-acceptance-case-09/pre-state.json --state /private/tmp/line-backup-acceptance-case-09/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-09/post-state.json --counter /private/tmp/line-backup-acceptance-case-09/counter.jsonl --result /private/tmp/line-backup-acceptance-case-09/result.json --manifest /private/tmp/line-backup-acceptance-case-09/manifest.json --stdout /private/tmp/line-backup-acceptance-case-09/stdout.log --stderr /private/tmp/line-backup-acceptance-case-09/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-09/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-09/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 10 --case-root /private/tmp/line-backup-acceptance-case-10 --pre-state /private/tmp/line-backup-acceptance-case-10/pre-state.json --state /private/tmp/line-backup-acceptance-case-10/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-10/post-state.json --counter /private/tmp/line-backup-acceptance-case-10/counter.jsonl --result /private/tmp/line-backup-acceptance-case-10/result.json --manifest /private/tmp/line-backup-acceptance-case-10/manifest.json --stdout /private/tmp/line-backup-acceptance-case-10/stdout.log --stderr /private/tmp/line-backup-acceptance-case-10/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-10/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-10/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 11 --case-root /private/tmp/line-backup-acceptance-case-11 --pre-state /private/tmp/line-backup-acceptance-case-11/pre-state.json --state /private/tmp/line-backup-acceptance-case-11/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-11/post-state.json --counter /private/tmp/line-backup-acceptance-case-11/counter.jsonl --result /private/tmp/line-backup-acceptance-case-11/result.json --manifest /private/tmp/line-backup-acceptance-case-11/manifest.json --stdout /private/tmp/line-backup-acceptance-case-11/stdout.log --stderr /private/tmp/line-backup-acceptance-case-11/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-11/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-11/evidence`
  - `cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && PYTHONPATH=/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/src /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/acceptance_case_driver.py --case-id 12 --case-root /private/tmp/line-backup-acceptance-case-12 --pre-state /private/tmp/line-backup-acceptance-case-12/pre-state.json --state /private/tmp/line-backup-acceptance-case-12/state/backup_state.json --post-state /private/tmp/line-backup-acceptance-case-12/post-state.json --counter /private/tmp/line-backup-acceptance-case-12/counter.jsonl --result /private/tmp/line-backup-acceptance-case-12/result.json --manifest /private/tmp/line-backup-acceptance-case-12/manifest.json --stdout /private/tmp/line-backup-acceptance-case-12/stdout.log --stderr /private/tmp/line-backup-acceptance-case-12/stderr.log --exit-code /private/tmp/line-backup-acceptance-case-12/exit-code --evidence-dir /private/tmp/line-backup-acceptance-case-12/evidence`
- The driver has one literal product argv array per process. Cases 01–04 and 06, 08–10, 11–12 use the exact CLI grammar above with the literal `/private/tmp/line-backup-acceptance-case-NN/...` paths, and Cases 13–19 and 20–25 use the byte-identical driver argv shape with `--case-id 13`…`--case-id 25` and every `-01` path suffix replaced by their own literal suffix (the recorded inputs.json always carries the fully expanded absolute argv; no placeholder reaches a process); Cases 05 and 07 launch the two literal argv arrays specified by the case protocol. No case uses a symbolic `CASE_ROOT`, `EVIDENCE_DIR`, or a dynamically generated command string. Every one of those literals and construction rules carries Rev17 §17.1's canonical `--config`/`--run-log`/`--state` children plus `--test-mode`; a literal or rule that omits them is invalid.

Exact process-specific protocol, expected outcome, and next-step decision:

- Case 01 runs the literal prepare / verify run 1 / commit / finalize / verify run 2 / duplicate-check / refused different-destination prepare / terminal resume argv already shown. Expected: prepare `PREPARED` exit 0 with exactly one counter line and revision 0→1→2; verify run 1 records `filesystem_status=PASS` and `recognized_images=57` and must **not** report an overall PASS (no association exists yet) while its JSON is the verifier result commit/finalize consume; commit `COMMITTED_VERIFICATION` exit 0 revision 2→3; finalize `FINALIZED` exit 0 revision 3→4 with the registry entry carrying the binding reference, `active_writer_id=null`, `context_lock=null`; verify run 2 `filesystem PASS / registry PASS / source CONFIRMED / state EXACT / overall PASS`, exit 0; duplicate-check `SKIP_DUPLICATE` exit 0; the different-destination prepare `CONFLICT_DUPLICATE_FINGERPRINT` exit 4 with unchanged state bytes and no second counter line; the terminal resume `SKIP_TERMINAL` exit 0 with no write. Any mismatch stops the wave as a transaction regression.
- Case 02 starts from a fresh schema-valid revision-0 pre-state whose destination holds the 57-image fixture, the driver-authored test-mode source-evidence record and the binding fixture artifact (hashed by the driver before execution). It runs the Case-01 prepare argv with `dispatcher-crash-after-side-effect.py` and `--crash-after-dispatch`: the intent commit is durable at revision 1 (`intent_state=INTENT_COMMITTED`, `dispatch_state=NOT_ATTEMPTED`, `intent.trigger_outcome=NOT_APPLICABLE`, `intent.dispatch_outcome=NOT_ATTEMPTED`, `save_all_retry_allowed=false`), the adapter appends exactly one counter line and dies, and prepare returns `DISPATCHER_CRASH_AFTER_SIDE_EFFECT` exit 1 at revision 1. A fresh `resume --no-dispatch` (no adapter options) returns `RECOVERY_NO_DISPATCH` exit 0 with exactly one guarded replacement (revision 1→2), the barrier fields of §15.1 row 4, one schema-valid `reconciliations[]` entry and one checkpoint-shaped `events[]` entry, `reconciliation_state=BARRIER_COMMITTED`, `state_replaced=true`, and an `evidence` string asserted to be exactly `reconcile:reconcile.json:<sha256 of reconcile.json>` per Rev17 §17.9. A second, byte-identical resume is idempotent: `RECOVERY_NO_DISPATCH` exit 0, no write, revision 2, `reconciliation_state=ALREADY_RECONCILED`. `commit --expected-revision 2` then refuses `CONFLICT_UNRESOLVED_DISPATCH` exit 4 with no write, and `finalize --outcome SAFE_ABORT --expected-revision 2` exits 0 at revision 3 with no registry addition and the unresolved barrier preserved. Otherwise recovery acceptance stops.
- Case 03 starts from the same revision-0 precondition and runs prepare with `dispatcher-unknown.py` and `--dispatcher-outcome UNKNOWN`: the pre-dispatch barrier is committed first (revision 1→2 with the row-4 fields), the adapter appends exactly one counter line, and prepare returns `DISPATCH_UNKNOWN` exit 1 at revision 2. A fresh `resume --no-dispatch` returns `RECOVERY_NO_DISPATCH` exit 0 with `reconciliation_state=ALREADY_RECONCILED` and no write (no new reconcile artifact is written, so the persisted reference is unchanged), and the commit is refused `CONFLICT_UNRESOLVED_DISPATCH`. No retry interpretation is allowed.
- Case 04 runs the exact duplicate-check argv already shown, then the terminal reconciliation resume without adapter options: `SKIP_DUPLICATE` then `SKIP_TERMINAL`, both exit 0, counter line count 0, no write. A separate row runs the same resume **with** `--dispatcher`/`--dispatch-counter` and requires `INVALID_INPUT` exit 2 with no write; the authority rows that fail authority validation still produce `INVALID_AUTHORITY` with their JSON error artifact, because authority is checked first.
- Case 05 launches two literal `transaction commit` processes at expected-revision 1 with the paused barrier, releases it once, and requires exactly one winner plus one `CONFLICT_STALE_REVISION`, one replacement only; the pre-state run must carry the completed dispatch record so the §15.1 commit precondition is satisfied.
- Case 06 runs commit with the wrong owner id: exact `CONFLICT_OWNER_RUN`, exit 4, no replacement.
- Case 07 launches the two literal prepare argv arrays above with shared state and one barrier, executes `/usr/bin/touch /private/tmp/line-backup-acceptance-case-07/acquire-ready.barrier` once, and requires exactly one `PREPARED` exit 0 and exactly one `CONFLICT_ACTIVE_RUN` exit 4, with exactly two guarded replacements by the winner and zero by the loser, exactly one counter line overall (the loser never dispatches) and no leaked lock.
- Case 08 runs commit with `--storage-fault WRITE_BEFORE_REPLACE`: exact exit 1, unchanged state bytes/revision and no terminal evidence.
- Case 09 runs finalize with `--storage-fault READBACK_UNCERTAIN_AFTER_REPLACE` (the pre-state carries the completed dispatch record and the §15.2 binding, and the verification JSON is a real product verifier result): exit 1 with `READBACK_UNCERTAIN`, the independently read state is terminal VERIFIED revision 3 with released owner/context, the fresh `resume --no-dispatch` returns `SKIP_TERMINAL` exit 0 with no adapter options and no replacement, and the counter remains 0.
- Case 10A runs the literal finalize VERIFIED argv and requires exit 0 with a replacement carrying verification, registry (with the binding reference), `workflow_outcome=VERIFIED`, `active_writer_id=null` and `context_lock=null`. Case 10B runs finalize SAFE_ABORT against a separate isolated state and requires revision 3, `workflow_outcome=SAFE_ABORT`, released ownership, preserved original intent/dispatch/trigger/dispatch-outcome values and `save_all_retry_allowed=false`, no registry addition, and terminal evidence recording the unresolved barrier; a VERIFIED registry entry or a cleared unresolved intent is a regression.
- Cases 11 and 12 run status evaluate and duplicate-check only: legacy-limited and contradictory results as their fixtures specify, with the shared evaluator's refusal class where a same-fingerprint association exists (never the destination-scoped `NOT_DUPLICATE` bypass), no normalization and no dispatch.
- Cases 13–19 execute the literal prepare/commit/finalize argv described in the grammar block, and their oracles are: 13/14 exit 2 with the exact class and zero state/counter/lock delta; 15–17 exit 4 with the exact class, unchanged state bytes and zero counter lines; 18 refusal exit 4 then `PREPARED` exit 0 with exactly one counter line for the released control; 19 `DISPATCH_UNKNOWN` exit 1 at revision 2, `CONFLICT_UNRESOLVED_DISPATCH` exit 4 no-write, then SAFE_ABORT exit 0 revision 3 with no registry entry. Every one of these rows is an independent oracle computed before product output; a product PASS line is never an oracle.
- A case is accepted only when its literal process exit(s), independently computed post-state/counter/hash oracle and manifest read-back match. Case 01/04/06/08/09/10/11/12, 13–19, 21, 22, 24 and 25 failures are product/test regressions; Case 02/03/05/07, 20 and 23 failures stop recovery/concurrency/duplicate-safety acceptance and prohibit production use (Rev17 §17.7). A pre-existing environment failure is REQUIRED_VERIFICATION=INCOMPLETE with baseline evidence, never product PASS.

- Before execution, independently hash case.json/input-state.json and record byte length. After every process, independently hash state bytes, counter lines, stdout, stderr, exit, result and manifest.
- The expected revision delta, counter line count, intent/dispatch/trigger values, registry, owner release, terminal outcome and retry permission are computed from the case specification before reading product output.
- Counter oracles: case 01 exactly 1 line total (zero on the closing duplicate/refusal/resume steps); case 02 exactly 1; case 03 exactly 1 with UNKNOWN/retry=false; case 04 and 09 exactly 0; cases 05/07 exactly one winner/one conflict with at most one counter line per prepared winner (07: exactly one overall); case 08 no replacement; cases 13–18 zero counter lines (18's positive control exactly one); case 19 exactly 1; case 10A one guarded VERIFIED replacement and case 10B one guarded SAFE_ABORT replacement preserving the unresolved intent barrier. cases 20 exactly one line before the kill and still exactly one after recovery; 21 exactly 0; 22 unchanged by all six finalize refusals (the setup's single dispatch line remains the only line); 23a exactly 0, 23b exactly 0, 23c exactly 1; 24, 25a and 25b exactly 0 (verify-only never dispatches) — Rev17 §17.7. Any deviation is TASK_REGRESSION.
- Every case retains case.json, inputs.json, pre-state.json/hash, post-state.json/hash, counter.jsonl/hash, stdout.log, stderr.log, exit-code, result.json and manifest.json. A product PASS line is never an oracle.



## Runtime route, ledger authority, GUI gate, and truthful E2E decision

E2E_REQUIRED: NO for this wave. The primary object is an existing destination that must not be redownloaded, and no production download is authorized. A CUA/controller session includes one ellipsis GUI input and is not full user-journey E2E. Stage 05 independent acceptance remains mandatory for the actual CLI, transaction process, evidence package and route status.

Authoritative historical ledger scope and budget:

- Action ledger: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/actions.jsonl, 4,219 bytes, SHA-256 9d6a159024f822003052fd7d538598d3a161f226c49ce14ea5c11d5c95c95aee. It records exactly two ellipsis inputs, no menu-item/Save-All click and no state write.
- Budget authority: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/environment.json, 4,555 bytes, SHA-256 a43d23d6166a3d2156c5e3a1ccd08cc394b8b283f9c3a2d007929db986922c95. It records the exact bundle/target and ellipsis_clicks_used=2, ellipsis_click_budget=2.
- Target scope: /Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/outputs/20260913T141849Z-menu-discovery-0d9a87b5-cef1-4815-b886-ccdb34fa803b/scope.json, 1,026 bytes, SHA-256 6bb8795ecc1beac3d8ba49c79fd032ff1f1459fb7784fc4cb000a84ae7fe5aaa.
- The historical 2/2 budget is exhausted. A new observation cannot append or reset it. A fresh run-specific ledger and one explicit user gate are required.

New run ledger and route-result schema:

- New private JSONL ledger schema_version=1 includes run_id, runtime/provider, app_bundle, raw_group, album, expected_count, project_root, parent_ledger_sha256, initial_input_counts, events, final_counts and route_result_sha256.
- Every event includes timestamp, action_class, event, gui_input, surface, target_binding_sha256, allowed_budget_before/after, menu_item_click, save_all_click, chooser_interaction, backup_state_write and evidence paths. App acquisition/navigation inputs are counted separately from the exactly-one permitted target ellipsis input; no unlisted input is allowed.
- Before the Human Gate, app acquisition and navigation are read-only and have GUI-input budgets of 0. After the gate, the user must already present the exact target album card; the controlled run has `app_acquisition_input_budget=0`, `navigation_input_budget=0`, and `ellipsis_input_budget=1`. If the exact target cannot be read in the current surface without navigation or extra input, the run records SAFE_ABORT and requests no additional action in this wave.
- New ellipsis budget is exactly 1 only after explicit authorization. The sequence is target-binding read → one current-target ellipsis input → immediate post observation → stop. No input may bring LINE to front, navigate, scroll, select an album, choose a menu item, invoke Save-All, open a chooser, or write backup state.
- route-result.json includes documented_capability_ref, runtime/provider, app_bundle, raw group, album, count, project_root, parent/new ledger SHA, target-binding SHA, pre/post observation SHAs, exact candidate text/role/subrole/bounds/owner, same-item correlation, save_all_click_count=0, menu_item_click_count=0, chooser_state, backup_state_write_count=0, route_status=AFFIRMATIVE|UNKNOWN|SAFE_ABORT, decision and reason.
- Missing, ambiguous, stale, uncorrelated or provider-mismatched evidence yields route_status=UNKNOWN and SAFE_ABORT. Historical coordinates and OCR-only evidence cannot yield AFFIRMATIVE.

The single Human Gate, if route evidence remains necessary, authorizes exactly this controlled experiment:

- App/bundle: LINE, jp.naver.line.mac.
- Raw target: 旻謙允禎成長日記; album: 2024/05/13～05/17; expected count: 57.
- Data/project root: /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state, explicitly confirmed.
- Surface: exact target album card and its ellipsis popup/menu only.
- Permitted input: exactly one current-target ellipsis input, no guessed coordinate and no low-level AXPress/AXUIElementPerformAction; no menu-item, Save-All, chooser, keyboard shortcut or state input/write.
- Capture immediate post evidence and stop. This is not production authorization.
- Production Save-All is outside this wave. Any later production route requires a separate later approved plan revision, fresh independent review, a newly created empty destination under /Users/hsiaojohnny/Downloads/LINE-Backup-PoC, exact group/album/count/destination gate and one atomic attempt with no retry after UNKNOWN. Existing valid 57 files may not be redownloaded.

Legal separation: offline CLI acceptance, controlled GUI route observation and later production Save-All are separate checks and artifacts. If exact existing source is proven and no side effect is needed, ROUTE_NOT_NEEDED may be recorded with explicit Plan rationale; otherwise route is a scoped CORE blocker. Production results cannot retroactively complete this wave.

## Canonical Status Contract v2, routing fixtures, and blockers

All execution/review/acceptance artifacts use Status Contract v2 exactly:

PRIMARY_OUTCOME_STATUS: ACHIEVED | NOT_ACHIEVED | UNKNOWN
IMPLEMENTATION_STATUS: NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | ESCALATED
CORE_ACCEPTANCE_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_REQUIRED | NOT_RUN | PASS | FAIL | BLOCKED | INCOMPLETE | WAIVED
INDEPENDENT_ACCEPTANCE_STATUS: NOT_REQUIRED | PENDING | PASS | FAIL | BLOCKED
TASK_CLOSURE_STATUS: IN_PROGRESS | PENDING_CORE_ACCEPTANCE | CORE_ACCEPTANCE_BLOCKED | READY_FOR_INDEPENDENT_ACCEPTANCE | PENDING_REQUIRED_VERIFICATION | FIX_REQUIRED | REPLAN_REQUIRED | IMPLEMENTATION_BLOCKED | ACCEPTANCE_BLOCKED | DONE

Every material check includes CHECK_ID, GOAL_CRITICALITY, EVIDENCE_ROLE, CLOSURE_GATE, BASELINE_REQUIRED, FAILURE_CLASSIFICATION_RULE, WAIVER_ALLOWED, WAIVER_AUTHORITY, CHECK_RESULT and WAIVER_STATUS. This is Plan-time policy; no agent can approve its own waiver.

| CHECK_ID | Criticality | Evidence role | Gate | Baseline | Failure classification | Waiver allowed | Authority | Check result | Waiver status |
|---|---|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | YES | old false acceptance not reproduced invalidates baseline | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | YES | incorrect axis/exit/artifact or false acceptance is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | malformed/unsafe acceptance or axis conflation is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | repeat dispatch or barrier bypass is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | stale/split/uncertain commit or false terminality is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | YES | formal mutation or contradiction is TASK_REGRESSION/BLOCKED | NO | NONE | NOT_RUN | NOT_ALLOWED |
| SOURCE_CORRESPONDENCE | CORE | OUTCOME | HARD_CLEAN | YES | missing authority is scoped BLOCKED/UNRESOLVED; contradiction is FAIL | NO | NONE | NOT_RUN | NOT_ALLOWED |
| CUA_ROUTE_DECISION | CORE | OUTCOME | HARD_CLEAN | YES | missing/ambiguous route evidence is scoped BLOCKED/UNKNOWN; no dispatch | NO | NONE | NOT_RUN | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | illegal enum/routing/self-waiver is TASK_REGRESSION | NO | NONE | NOT_RUN | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | missing independent result remains PENDING/BLOCKED | NO | NONE | NOT_RUN | NOT_ALLOWED |
| BASELINE_REGRESSION_DELTA | CORE | MUST_NOT_BREAK | BASELINE_DELTA | YES | rerunning the identical command/environment shows a new or worsened failure signature, or an old signature is silently omitted | NO | NONE | NOT_RUN | NOT_ALLOWED |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | non-gating unless route-specific necessity is proved | YES | Project owner, exact scope | NOT_RUN | NOT_REQUESTED |
| DOCUMENTATION_RETENTION_HEALTH | SUPPORTING | REPOSITORY_HEALTH | HARD_CLEAN | NO | within the exact task-evidence scope, missing raw commands, stdout/stderr/exit, or manifest/hash read-back would make independent acceptance non-reproducible and could invalidate provenance; unrelated repository documentation never enters this gate | YES | Project owner, exact scope | NOT_RUN | NOT_REQUESTED |

`BASELINE_REGRESSION_DELTA` has a pre-change artifact SHA-256, byte length, exact command argv, working directory, interpreter/environment fingerprint, and captured pre-change result/signatures. The post-change run repeats that same argv and environment; `baseline_delta=UNCHANGED` means every pre-existing signature is still disclosed with identical classification and no new/worsened signature exists, while `baseline_delta=WORSENED` is a hard failure. A baseline artifact that is absent or unreadable is `REQUIRED_VERIFICATION=INCOMPLETE`, not PASS. The baseline row is independently checked and never inferred from a product PASS line.

The named baseline subject is `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY`. Before Stage-04 edits product files, the implementer runs this exact command from cwd `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` with `LC_ALL=C`, `PATH=/usr/bin:/bin`, `PYTHONHASHSEED=0`, and `/usr/bin/python3`:

`cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0 /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/authority_baseline.py --config /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json --state /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json --run-log /Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md --destination /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57 --output /private/tmp/line-backup-acceptance-baseline/current.json`

The script is read-only and emits a canonical JSON snapshot containing every named input's byte length/SHA-256 plus the structured destination inventory, per-file byte length/SHA-256/mtime/type and aggregate count/bytes. The driver copies that exact `current.json` byte-for-byte to `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260916-baseline/attempt-02/baseline-pre.json` and records its SHA-256/byte length, command argv, cwd, interpreter version and normalized environment fingerprint before product edits. After implementation it reruns the same literal command and environment with the same fixed output path, then independently compares `baseline-pre.json` with `/private/tmp/line-backup-acceptance-baseline/current.json`; only output-file contents are allowed to differ in the command capture. A missing/unreadable/mismatched pre-artifact routes `REQUIRED_VERIFICATION=INCOMPLETE`, blocker `REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE`, next action `restore or recapture the exact pre-change baseline before acceptance`, and never PASS.

Executable status fixtures invoke status evaluate with a literal input JSON and compare all six statuses, scoped blocker, check metadata, baseline/failure class, waiver fields and closure. Required cases:

| Fixture | Primary | Implementation | Core | Required verification | Independent acceptance | Closure | Exact blocker/routing |
|---|---|---|---|---|---|---|---|
| Candidate before implementation | UNKNOWN | NOT_STARTED | NOT_RUN | NOT_RUN | PENDING | IN_PROGRESS | none |
| Approved implementation cannot continue | UNKNOWN | BLOCKED | NOT_RUN | NOT_RUN | PENDING | IMPLEMENTATION_BLOCKED | IMPLEMENTATION/BLOCKED/ENVIRONMENT_FAILURE |
| New evidence invalidates plan | UNKNOWN | ESCALATED | NOT_RUN | NOT_RUN | PENDING | REPLAN_REQUIRED | IMPLEMENTATION/BLOCKED/TASK_REGRESSION |
| Complete implementation, CORE not run | UNKNOWN | COMPLETE | NOT_RUN | NOT_RUN | PENDING | PENDING_CORE_ACCEPTANCE | CORE_ACCEPTANCE/NOT_RUN/INPUT_UNAVAILABLE |
| Complete implementation, CORE blocked | UNKNOWN | COMPLETE | BLOCKED | NOT_RUN | PENDING | CORE_ACCEPTANCE_BLOCKED | CORE_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED |
| Complete implementation, CORE fail | NOT_ACHIEVED | IN_PROGRESS | FAIL | NOT_RUN | PENDING | FIX_REQUIRED | CORE_ACCEPTANCE/FAIL/TASK_REGRESSION |
| CORE pass with unchanged baseline delta and required checks pass | ACHIEVED | COMPLETE | PASS | PASS | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | no blocker; baseline_delta=UNCHANGED |
| Baseline worsened (`baseline_delta=WORSENED`) with all other required checks passing | ACHIEVED | COMPLETE | PASS | FAIL | PENDING | FIX_REQUIRED | BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION; per workflow-routing §7.7 rule 8 a worsened baseline is a must-not-break violation, never INCOMPLETE/PENDING_REQUIRED_VERIFICATION (Rev17 §17.6) |
| Canonical incident with pre-existing hard-clean debt | ACHIEVED | COMPLETE | PASS | INCOMPLETE | PENDING | PENDING_REQUIRED_VERIFICATION | DOCUMENTATION_RETENTION_HEALTH/FAIL/PRE_EXISTING_REPOSITORY_FAILURE; aggregate INCOMPLETE is retained because a conclusive pre-existing debt is disclosed but not clean |
| CORE pass, baseline unavailable | ACHIEVED | COMPLETE | PASS | INCOMPLETE | PENDING | PENDING_REQUIRED_VERIFICATION | REQUIRED_VERIFICATION/BLOCKED/INPUT_UNAVAILABLE |
| All required items formally waived | ACHIEVED | COMPLETE | PASS | WAIVED | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | waiver APPROVED by named authority |
| Reachable waiver for scoped non-core retention debt | ACHIEVED | COMPLETE | PASS | WAIVED | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE | DOCUMENTATION_RETENTION_HEALTH original FAIL preserved; waiver APPROVED with scope/rationale/evidence/residual-risk/expiry |
| Stage 05 environment/input block | ACHIEVED | COMPLETE | PASS | PASS | BLOCKED | ACCEPTANCE_BLOCKED | INDEPENDENT_ACCEPTANCE/BLOCKED/AUTHORITY_REQUIRED |
| Acceptance finds product defect | UNKNOWN | IN_PROGRESS | PASS | PASS | FAIL | FIX_REQUIRED | INDEPENDENT_ACCEPTANCE/FAIL/PRODUCT_DEFECT |
| Legacy normalization without source proof | UNKNOWN | COMPLETE | BLOCKED | PASS | PENDING | CORE_ACCEPTANCE_BLOCKED | SOURCE_CORRESPONDENCE/BLOCKED/INPUT_UNAVAILABLE |
| Contradictory state axes | NOT_ACHIEVED | IN_PROGRESS | FAIL | NOT_RUN | PENDING | FIX_REQUIRED | CORE_ACCEPTANCE/FAIL/TASK_REGRESSION; preserve any completed Stage-04 snapshot as immutable evidence |
| CORE NOT_REQUIRED without Plan rationale | UNKNOWN | ESCALATED | NOT_REQUIRED | NOT_RUN | PENDING | REPLAN_REQUIRED | IMPLEMENTATION/BLOCKED/TASK_REGRESSION |
| CORE NOT_REQUIRED with explicit Plan rationale | ACHIEVED | COMPLETE | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | DONE | plan_rationale records that the scoped artifact has no CORE checks and the rationale is independently checked |
| All closure prerequisites satisfied | ACHIEVED | COMPLETE | PASS | PASS | PASS | DONE | none |

Every status row above is executable. The exact driver command is:

`cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup && LC_ALL=C PATH=/usr/bin:/bin PYTHONHASHSEED=0 /usr/bin/python3 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/status_fixture_driver.py --manifest /private/tmp/line-backup-acceptance-status/fixture-manifest.json --evidence-dir /private/tmp/line-backup-acceptance-status/evidence --summary /private/tmp/line-backup-acceptance-status/summary.json`

The literal manifest enumerates the 19 rows by ID, with one absolute input/output/evidence path per row under `/private/tmp/line-backup-acceptance-status/`: `candidate`, `implementation-blocked`, `replan-required`, `core-not-run`, `core-blocked`, `core-fail`, `baseline-unchanged`, `baseline-worsened`, `canonical-preexisting-debt`, `baseline-unavailable`, `all-required-waived`, `retention-waived`, `stage05-blocked`, `acceptance-product-defect`, `legacy-no-source`, `contradictory-axes`, `core-not-required-no-rationale`, `core-not-required-rationalized`, and `done`. The nineteenth row `baseline-worsened` (Rev17 §17.6) uses /private/tmp/line-backup-acceptance-status/baseline-worsened.input.json and /private/tmp/line-backup-acceptance-status/baseline-worsened.output.json and expects PRIMARY `ACHIEVED`, IMPLEMENTATION `COMPLETE`, CORE `PASS`, REQUIRED_VERIFICATION `FAIL`, INDEPENDENT `PENDING`, CLOSURE `FIX_REQUIRED`, blocker `BASELINE_REGRESSION_DELTA/FAIL/TASK_REGRESSION` with `baseline_delta=WORSENED`. For each ID, the manifest contains the full literal `status evaluate --input /private/tmp/line-backup-acceptance-status/<id>.input.json --output /private/tmp/line-backup-acceptance-status/<id>.output.json` argv, expected exit 0, all six expected statuses, scoped blocker fields, `CHECK_ID` metadata, baseline fields and waiver fields. The driver invokes that real status CLI in a subprocess, independently compares every field, and records each subprocess stdout/stderr/exit plus input/output/manifest SHA-256 and byte length. Per Rev15 §15.4 (F5 oracle), every row additionally asserts the emitted `evidence_basis == "scenario_table_non_acceptance"`; a row whose output omits or changes that field fails the driver, and no Stage-05 acceptance decision may cite status output as evidence. It never writes a product transition or fills expected values after reading output.

The baseline-unchanged fixture includes `BASELINE_REGRESSION_DELTA` with `baseline_artifact=/private/tmp/line-backup-acceptance-status/baseline-unchanged.baseline.json`, its literal command/cwd/interpreter/environment fingerprint, `baseline_delta=UNCHANGED`, and the unchanged pre-existing signature disclosed. The baseline-unavailable fixture points to `/private/tmp/line-backup-acceptance-status/missing-baseline.json` and must produce `REQUIRED_VERIFICATION=INCOMPLETE` with the scoped unavailable-input blocker. The canonical-preexisting-debt fixture preserves item-level `DOCUMENTATION_RETENTION_HEALTH CHECK_RESULT=FAIL`, class `PRE_EXISTING_REPOSITORY_FAILURE`, aggregate `INCOMPLETE`, and closure `PENDING_REQUIRED_VERIFICATION`. The retention-waived fixture preserves that original FAIL and adds `WAIVED_BY`, `WAIVER_SCOPE`, `RATIONALE`, `EVIDENCE`, `RESIDUAL_RISK`, `APPROVED_AT`, and `REVIEW_OR_EXPIRY_TRIGGER`; the independent oracle checks that the waiver never rewrites the original result. The rationalized CORE-NOT_REQUIRED fixture contains a nonempty Plan rationale in its input, while the no-rationale fixture must route REPLAN_REQUIRED.

Stage 05 must snapshot before acceptance:
STAGE_04_REPORTED_IMPLEMENTATION_STATUS
STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS
STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS
STAGE_04_EXECUTION_ARTIFACT_SHA256
It also records TASK_ID, PLAN_REVISION, HANDOFF_SHA256, execution timestamp and evidence path. A Stage 05 authority/environment blocker preserves this immutable snapshot and routes INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED, TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED.

Scoped blocker record required in every terminal artifact:

BLOCKERS:
  - id: unique
    scope: IMPLEMENTATION | CORE_ACCEPTANCE | REQUIRED_VERIFICATION | INDEPENDENT_ACCEPTANCE | AUTHORITY | ENVIRONMENT
    subject: exact component/check
    result: FAIL | BLOCKED | NOT_RUN
    class: TASK_REGRESSION | PRE_EXISTING_REPOSITORY_FAILURE | ENVIRONMENT_FAILURE | AUTHORITY_REQUIRED | INPUT_UNAVAILABLE | PRODUCT_DEFECT
    task_regression_evidence: evidence | NONE | UNKNOWN
    evidence: exact artifact/path/result
    next_action: one precise action
    owner: explicit role or user
    waiver_allowed: YES | NO

A valid waiver preserves CHECK_RESULT and includes WAIVED_BY, WAIVER_SCOPE, RATIONALE, EVIDENCE, RESIDUAL_RISK, APPROVED_AT and REVIEW_OR_EXPIRY_TRIGGER. Core source/data-integrity failures and fabricated/missing provenance are non-waivable.

## Closure and sequencing

The root /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md is historical/non-authoritative for this task because it predates this TASK_ID and revision. Stage 03 must create a fresh handoff bound to TASK_ID, the current PLAN_REVISION at handoff time (18 at this writing), the approved plan SHA, GOAL_ANCHOR, critical path, invariants, deferred/non-gating items and stop conditions.

Stage 02 must independently review this Revision 18 and its exact hash. Stage 03 may compile handoff only for the approved revision/hash. Stage 04 repairs only the approved evidence harness and reruns the verifier/transaction/status wave; it must preserve prior attempts, write execution.md with the canonical six statuses, check matrix/results, scoped blockers, Stage 04 snapshot fields and artifact hashes. Stage 05 independently accepts the real CLI/evidence, snapshots immutable Stage 04 facts and does not modify product code.

The current plan is not implementation approval. Offline read-only reconciliation, isolated fixture construction, baseline reproduction, and review preparation are authorized now. Product code edits, external formal-state writes, GUI input, deployment, and production download require the applicable later gate. Any semantic contract, product-boundary, E2E, or GUI-budget change increments PLAN_REVISION on the same TASK_ID, invalidates prior approvals and any handoff, and repeats independent review; it never continues under the same revision (Rev16 §16.8).

Canonical routing is subject-specific: implementation blockage uses IMPLEMENTATION_STATUS=BLOCKED and TASK_CLOSURE_STATUS=IMPLEMENTATION_BLOCKED; new semantic evidence uses IMPLEMENTATION_STATUS=ESCALATED and TASK_CLOSURE_STATUS=REPLAN_REQUIRED; completed implementation with CORE blocked uses TASK_CLOSURE_STATUS=CORE_ACCEPTANCE_BLOCKED; Stage 05 authority/environment blockage uses INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED and TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED; required verification debt uses INCOMPLETE, not PASS. No status field rewrites another subject.

DONE requires: PRIMARY_OUTCOME_STATUS=ACHIEVED; IMPLEMENTATION_STATUS=COMPLETE; CORE_ACCEPTANCE_STATUS=PASS or explicitly Plan-rationalized NOT_REQUIRED; REQUIRED_VERIFICATION_STATUS=PASS/NOT_REQUIRED/WAIVED; INDEPENDENT_ACCEPTANCE_STATUS=PASS/NOT_REQUIRED; exact source correspondence `CONFIRMED` based only on an authoritative exact join or one precise user fact in the preserved user-fact evidence format — Rev16 §16.4 pins that record's CONFIRMED v1 contract, and the preserved PARTIAL artifact alone can never confirm; no unresolved hard blocker; valid fresh durable artifacts; unrelated user work preserved. No plan rationale or technical similarity is an equivalent, and `UNRESOLVED`, `LEGACY_PROVENANCE_LIMITED`, or `CONTRADICTED` cannot be promoted to closure.

If source identity remains unresolved after all authorized evidence, the legally correct result is PRIMARY_OUTCOME_STATUS=UNKNOWN with the source/core check BLOCKED and no DONE. If route evidence is unavailable but exact existing provenance has already been proven and no side effect is needed, record ROUTE_NOT_NEEDED with explicit Plan rationale; otherwise route remains a scoped CORE blocker. If an independent acceptance authority/tool is unavailable, preserve implementation/CORE/required-verification facts and route INDEPENDENT_ACCEPTANCE_STATUS=BLOCKED, TASK_CLOSURE_STATUS=ACCEPTANCE_BLOCKED. Never downgrade proven implementation because acceptance could not run.

## Owner view

Essential: prove whether the existing 57 files can be safely attributed to the exact requested LINE source and prove real reusable recovery/duplicate behavior before any new GUI side effect. Filesystem health alone is insufficient. The new local CLI/package is the explicit reusable product boundary for this task; it must not be confused with an absent external producer. Supporting: bridge/service diagnosis only if causal evidence proves necessity. Deferred: production Save-All/download, bridge repair, migration, OCR, and historical cleanup. The largest remaining risk is still that the 57 files are valid but the original source namespace/provenance was never captured.
