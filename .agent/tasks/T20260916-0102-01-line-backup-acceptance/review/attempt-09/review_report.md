# Plan Review Report

## REVIEW_METADATA

- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 09
- REVIEWED_PLAN_REVISION: 8
- REVIEWED_PLAN_SHA256: dffd121307c52ea37eacf0cc51be10ee368e13052d8c2459edc3a62ed9a91e4b
- REVIEWED_PLAN_BYTES: 89360
- PLAN_SNAPSHOT_PATH: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-09/plan_snapshot.md
- PLAN_SNAPSHOT_SHA256: dffd121307c52ea37eacf0cc51be10ee368e13052d8c2459edc3a62ed9a91e4b
- PLAN_SNAPSHOT_BYTES: 89360
- PLAN_SNAPSHOT_VERIFICATION: [VERIFIED] `cmp` exit 0; snapshot and canonical plan are byte-identical before judgment.
- Repository anchor: /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
- Repository instructions: [VERIFIED] no repository-local `AGENTS.md`; `/Users/hsiaojohnny/.codex/AGENTS.md` applies.
- Review mode: read-only for product code and `plan.md`; only the attempt-09 snapshot and this append-only report were created.
- Prior-result independence: [VERIFIED] attempt-08 was not treated as acceptance; revision 8 was re-read and re-evaluated from its exact snapshot.

## GOAL_BASELINE

- PRIMARY_OUTCOME: Safely establish whether `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` is a valid backup of the exact requested LINE app/group/album `jp.naver.line.mac` / `旻謙允禎成長日記` / `2024/05/13～05/17` with 57 images; otherwise stop without modifying existing photos/formal state or creating an ambiguous or duplicate production transaction.
- SUCCESS_EVIDENCE: independently observed filesystem and artifact evidence; exact source correspondence or explicit unresolved/contradicted result; non-mixing registry/intent/writer/state reconciliation; a real operator CLI for verify-only and transaction recovery/duplicate/commit/finalization; and independent acceptance.
- MUST_NOT_BREAK: preserve the existing destination and formal state; keep requested `禎` distinct from persisted `楨`; never retry uncertain Save-All; keep filesystem/source/registry/intent/dispatch/trigger/terminal axes separate; and never use self-written fixture fields or a product PASS line as the oracle.
- NON_GOALS: production download in this wave, spelling merge/migration, bridge repair/TCC work, broad historical cleanup, distributed exactly-once, and unrelated refactoring.
- CRITICAL_PATH: historical false-positive and self-certifying-fixture evidence → real fail-closed verifier → real subprocess transaction process → independent state/status oracles → current destination/source reconciliation → scoped route decision.

## CURRENT EVIDENCE

[VERIFIED] The repository currently has no product `src/`, `tests/`, `pyproject.toml`, verifier, transaction library, producer, or consumer. Existing untracked evidence, handoff material, and task artifacts predate this review and were preserved.

[VERIFIED] The selected data root contains exactly `config/line_backup_config.json`, `state/backup_state.json`, and `state/run_log.md`. Current observed anchors are: config 372 bytes, SHA-256 `390cbdcf36a88c9f134c0ecb29d39018ebadf42babfb7a264a741337499d3b3b`; state 48,146 bytes, SHA-256 `e9313a563bf298d4b1e9ae243c5d3d404ad1333f69cb71b156e68589a8ec2f59`; run log 15,950 bytes, SHA-256 `a62dd07d1df1a34fb91a11d6eec6ac8aae7146abf9eb7011b78b1d27914158bf`.

[VERIFIED] Current config is schema 2 with `group_key=...旻謙允楨成長日記`, `backup_root=/Users/hsiaojohnny/Downloads/LINE-Backup-PoC`, bundle `jp.naver.line.mac`, `max_albums_per_run=1`, `recovery_limit=1`, `stable_samples=3`, and `max_wait_seconds=600`. Current state is schema 2/revision 39 with four registry entries, five runs, and null current run/active writer/context lock. The target 57-image record is legacy (`contract_revision=null`, no title/provenance) and uses persisted `楨`, while the requested key uses `禎`; exact source correspondence remains unproven.

[VERIFIED] The current destination has 57 immediate regular files, 17,924,900 total bytes, 57 `image/jpeg` results, no hidden names, partial/temp suffixes, subdirectories, or symlinks. The preserved canonical audit records three stable inventories with 57 recognized images, zero-byte 0, partial/temp 0, unrecognized 0, and no errors. This proves filesystem condition only, not source correspondence.

[VERIFIED] The old verifier’s isolated 56-file and 58-file reproductions both show `ACTUAL_IMAGES=56/58`, `Expected images: 57`, `STABLE_INVENTORY=PASS`, `FILESYSTEM_VERIFICATION=PASS`, and process exit 0. The old script checks inventory stability and registry destination but never compares actual image count with `EXPECTED=57`; this is a valid false-positive baseline.

[VERIFIED] The historical recovery fixture’s corrected attempt exits 0, but its script writes `UNKNOWN` and `save_all_retry_allowed=false` into a new temporary state and then checks those same self-written fields. It is a contract-shape fixture, not independent crash/restart transaction evidence; the earlier jq-error attempt remains separately preserved.

[VERIFIED] The documented GUI ledger is intact: `actions.jsonl` is 4,219 bytes with SHA-256 `9d6a159024f822003052fd7d538598d3a161f226c49ce14ea5c11d5c95c95aee`; it contains 10 events, two ellipsis inputs, zero menu-item/Save-All clicks, and zero backup-state writes. Its environment authority is 4,555 bytes with SHA-256 `a43d23d6166a3d2156c5e3a1ccd08cc394b8b283f9c3a2d007929db986922c95` and an exhausted 2/2 ellipsis budget. The plan correctly treats it as historical provenance and limits any new observation to one explicitly gated ellipsis input with no Save-All, chooser, or state write.

## TOP_DOWN_REVIEW

[VERIFIED] Revision 8 remains aligned with the Goal Baseline. It keeps the requested/persisted spelling mismatch unresolved, treats filesystem PASS as insufficient source proof, preserves formal state and existing photos, defers production Save-All, and makes bridge readiness SUPPORTING/DIAGNOSTIC and NON_GATING.

[VERIFIED] The critical path and owner view prioritize false-positive reproduction, a real CLI boundary, independent transaction/status oracles, and source/state reconciliation before optional route observation. The planned lock, atomic replacement/read-back, intent barrier, independent counter, and subprocess cases each trace to data-integrity or duplicate-dispatch risk.

[VERIFIED] No unauthorized production scope is introduced. The plan explicitly defers download, migration, bridge repair, TCC changes, broad cleanup, and future producer integration; the latter is correctly identified as requiring a later revision and review.

## EARLIER_CONTRACT_REGRESSION_CHECK

[VERIFIED] Case 07 is coherent and winner-independent: two literal prepare processes, one shared acquire barrier, one winner-independent one-replacement invariant, one exact `CONFLICT_ACTIVE_RUN` loser, and post-state-derived winner identity.

[VERIFIED] Cases 02 and 03 now specify the first durable revision-2 dispatch barrier, `DISPATCH_REQUESTED`/`UNKNOWN`/retry-false fields, one independent counter line, first-process exit 1, and fresh `--no-dispatch` recovery with no second dispatch.

[VERIFIED] Case 09 now uses terminal-after-replace uncertainty: finalize returns `READBACK_UNCERTAIN` exit 1 after the exact revision-3 terminal replacement; independent reload sees `VERIFIED` with released owner/context; fresh `--no-dispatch` returns `SKIP_TERMINAL` exit 0 with no dispatch.

[VERIFIED] SAFE_ABORT 10B independently requires revision 3, released ownership, preserved original intent/dispatch/trigger/dispatch-outcome fields and retry=false, no registry addition, and terminal evidence retaining the unresolved barrier.

[VERIFIED] `BASELINE_REGRESSION_DELTA` is bound to the named subject `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY`, exact command/cwd/interpreter/environment, pre-artifact path/hash/bytes, post comparison, unchanged-versus-worsened signatures, and unavailable-baseline `INCOMPLETE` routing.

[VERIFIED] Status Contract v2 is represented with the six orthogonal statuses, scoped blocker schema, check metadata, baseline policy, failure classes, waiver fields, and 18 literal fixture IDs. The hard-clean pre-existing incident preserves item-level `FAIL`, aggregate `INCOMPLETE`, and `PENDING_REQUIRED_VERIFICATION`; waiver fixtures preserve original check results.

[VERIFIED] Literal transaction driver commands cover Cases 01–12, including Case 07’s two literal argv arrays and Case 10A/10B. The status driver has one literal manifest command and 18 literal input/output/evidence paths. No active stale revision wording was found; the only `Rev1`–`Rev7` occurrence is historical review provenance in the requirement table, while all active plan bindings say revision 8.

## FINDINGS

### RV9-001

- Severity: MAJOR
- Category: AUTHORITY / SEMANTIC_CONTRACT / SAFETY
- Affected plan: `plan.md:99-107,111,235-252,256-305`
- Evidence: Revision 8 declares an explicit immutable `--project-root` for verify-only and every transaction command, but only the verify-only path is bound to the skill’s canonical `project_root/config/line_backup_config.json`, `project_root/state/backup_state.json`, and `project_root/state/run_log.md`. Transaction grammar instead accepts `--state` as `project_root/state.json`, has no config/run-log binding, and is still called the reusable operator-facing product. The only literal no-write authority-negative command is verify-only (`plan.md:235`); no transaction command is run with a mismatched root/state, no missing-root invocation is independently checked, and no transaction pre/post state-hash oracle is specified.
- Failure/rework mechanism: A real operator transaction can be directed at an arbitrary state-only registry that is not authorized by the selected project’s config, backup-root chain, or run log. All Cases 01–12 can pass while the reusable mutating process violates the skill’s root authority/write-containment contract. The broad assertion that an authority mismatch has zero replacement/dispatch/registry mutation is not executable evidence, and a hash comparison alone would prove no write but not canonical path enforcement.
- Smallest required correction: Resolve the boundary explicitly before implementation. For the reusable/operator path, derive and validate the canonical config/state/run-log paths from the immutable selected root (and validate configured backup-root/destination containment and symlink identity); do not permit an arbitrary `project_root/state.json` authority. If isolated RC2 `state.json` fixtures remain, make that a narrowly explicit `--test-mode` exception and remove any implication that it is the production/operator authority. Add a literal authority manifest/driver covering at least prepare, resume, commit, finalize, and duplicate-check with mismatched root/state and omitted-root invocation cases; independently capture pre/post state bytes and hashes, counter lines, replacement count, registry/owner fields, exit/result, and evidence-path writes, requiring `INVALID_AUTHORITY` before state mutation. Preserve the verify-only negative and the existing isolated test-root allowlist.

### RV9-002

- Severity: MAJOR
- Category: TEST / ACCEPTANCE / PROVENANCE
- Affected plan: `plan.md:181-231,235,274-291,361-365`
- Evidence: The verifier matrix defines many required executable rows, and revision 8 says each runs the product CLI in a fresh isolated project/evidence directory, but it supplies a literal command only for the authority negative. There is no named verifier fixture manifest, verifier fixture driver, or literal per-row input/output/evidence argv in the planned file list. `acceptance_case_driver.py` is explicitly the transaction-case driver, while the only named additional drivers are `authority_baseline.py` and `status_fixture_driver.py`.
- Failure/rework mechanism: Independent acceptance can execute the transaction and status manifests yet omit or differently construct the 56/58, suffix/hidden, symlink/special-file, MIME mismatch, mutation-at-sample-2, cross-entry, legacy/duplicate, internal-error, and artifact read-back rows. That would leave the old count false-positive or axis conflation unproven despite a declarative matrix, and would make the claimed documentation/provenance retention non-reproducible.
- Smallest required correction: Add one literal verifier fixture manifest and subprocess driver, or enumerate an equally precise literal subprocess command and fixture path for every matrix row. The manifest must include fixture creation/pre-state hashes, exact product argv, expected subject-axis results/exit, independent pre-product oracle rules, result/manifest read-back checks, and retained stdout/stderr/exit/state/evidence hashes. Include the authority negative in that same manifest without replacing the transaction/status manifests.

## REVIEW_CONCLUSION

The prior authority correction is only partially closed: verify-only authority has a concrete negative oracle, but the reusable transaction boundary and its no-write authority proof remain underspecified and inconsistent with the skill’s canonical root contract. The earlier Case 07/09, Cases 02/03, SAFE_ABORT 10B, baseline, Status Contract v2, literal transaction/status manifests, source-mismatch, GUI-ledger, and scope contracts remain intact.

FINAL_GATE: PLAN_REVISION_REQUIRED

## REQUIRED_PLAN_CHANGES

1. Resolve RV9-001 by making the reusable transaction CLI honor canonical root/config/state/run-log authority, or explicitly narrow the state-only transaction path to isolated test mode and remove the reusable operator-authority claim. Add the literal transaction authority-negative/no-write oracle and preserve the verify-only authority test.
2. Resolve RV9-002 by adding a literal verifier fixture manifest/driver or complete equivalent per-row subprocess manifests with independently computed expected results and artifact read-back.
3. Preserve all verified earlier contracts, especially the `禎`/`楨` unresolved result, formal-state read-only rule, Cases 02/03/07/09, SAFE_ABORT 10B, baseline provenance, Status Contract v2, one-ellipsis GUI scope, and the no-production-download boundary.

No product code or `plan.md` was edited.
