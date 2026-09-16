# Stage 03 handoff — LINE album acceptance and reusable transaction process

TASK_ID: T20260916-0102-01-line-backup-acceptance
PLAN_REVISION: 13
PLAN_SHA256: ad1ac6ac3cc5b63b5b6e1e48d8db525f556c680046abd026b7201680defb251a
PLAN_BYTES: 105280
PLAN_APPROVAL: REVIEW_ATTEMPT_16 / PLAN_APPROVED
IMPLEMENTATION_MODE: FRESH_STAGE_04
E2E_REQUIRED: NO
INDEPENDENT_ACCEPTANCE_REQUIRED: YES

## GOAL_ANCHOR

Safely establish whether the existing 57-image destination is a valid backup of the exact LINE source `jp.naver.line.mac` / group `旻謙允禎成長日記` / album `2024/05/13～05/17`. Preserve existing photos and formal state. If exact source correspondence cannot be proven, report UNKNOWN/blocked and do not create an ambiguous or duplicate production transaction.

The requested raw group uses `禎`. The canonical config and legacy state use `楨`; these are separate strings and keys. No implementation or verifier may merge, normalize, or silently rewrite them.

## CRITICAL_PATH

1. Preserve and reference the historical false-positive evidence and the self-certifying recovery-fixture evidence.
2. Create the real local operator package/CLI under the repository. Fixtures are inputs only; no test helper may be the transaction model or oracle.
3. Implement fail-closed verify-only with independent filesystem, registry, source, and state axes and artifact read-back.
4. Implement the real transaction process with serialized guarded compare-and-commit, dispatch barrier, no-retry recovery, duplicate gating, terminal finalization, storage-fault handling, and subprocess restart/race coverage.
5. Run independent verifier/status/transaction oracles, then run verify-only against the existing destination without mutating the formal project or photos.
6. Reconcile source identity and state/registry/intent/writer evidence. Current evidence starts as source `UNRESOLVED`, state association `LEGACY_PROVENANCE_LIMITED`; filesystem PASS alone cannot close the goal.
7. Check runtime capability and the historical action ledger. With the historical ellipsis budget exhausted, no new GUI observation is allowed in Stage 04. If route evidence is still CORE-required after offline proof, stop at the single precise Human Gate in the plan; do not dispatch Save All.

## AUTHORITATIVE INPUTS

- Repository: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Historical/root handoff: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/handoff.md` is non-authoritative background only.
- Formal read-only project: `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state`
- Config: `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json`
- State: `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json`
- Run log: `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md`
- Existing destination (read-only): `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`
- Requested group key: `line:jp.naver.line.mac:旻謙允禎成長日記`
- Target fingerprint: `2024-05-13` / `2024-05-17` / `57`

Before mutation, record `git status` and preserve all unrelated dirty work. Formal files and the 57 existing image files are never overwritten, normalized, moved, or redownloaded by this wave.

## IMPLEMENTATION CONTRACT

The product boundary is the real package and operator CLI, not a fixture or an absent external producer. The CLI must expose the exact plan grammar:

- `verify-only --project-root ... --config ... --state ... --destination ... --group-key ... --start-date ... --end-date ... --expected-images ... --evidence-dir ...`, with test mode only for the literal verifier fixture root and SAMPLE_2 barrier.
- Production transaction commands require explicit canonical `--project-root`, `--config`, `--run-log`, and `--state` paths. Validate root identity, canonical path identity, config backup-root, and destination containment before reading authority files, deriving/opening `.line-backup-state.lock`, creating control paths, or mutating anything. Any mismatch is `INVALID_AUTHORITY`, exit 2, with only isolated error evidence.
- Test-only transaction commands require explicit `--test-mode`, one literal case root `/private/tmp/line-backup-acceptance-case-01` through `-12`, state exactly `project_root/state.json`, no config/run-log, and all fixture paths beneath that root. Reject DATA_PROJECT_ROOT and non-fixture paths.

Use POSIX flock plus same-directory temporary replacement, fsync/read-back, expected revision/owner/run checks, and one shared compare-and-commit boundary. Never fall back to an alternate state/config/registry path.

RC2 state axes are fixed: `intent_state` values include `INTENT_COMMITTED` and `TRIGGER_UNKNOWN`; `dispatch_state` values include `NOT_ATTEMPTED` and `UNKNOWN`; `trigger_outcome` and `dispatch_outcome` preserve `NOT_APPLICABLE` or `UNKNOWN` as applicable. In Cases 02/03, prepared revision 1 is `INTENT_COMMITTED` / `NOT_ATTEMPTED` / `NOT_APPLICABLE` / `NOT_ATTEMPTED` with `save_all_retry_allowed=false`; the durable revision-2 uncertainty barrier is `TRIGGER_UNKNOWN` / `UNKNOWN` / `UNKNOWN` / `UNKNOWN` with false. `READY` and `NOT_DISPATCHED` are documentation shorthand only.

Duplicate precedence is operation-specific: exact terminal `duplicate-check` returns `SKIP_DUPLICATE`; matching terminal `resume` returns `SKIP_TERMINAL`. Both are exit 0, no replacement, and no dispatch, but they must remain distinct in result schemas and independent oracles.

Finalize is the only path to terminal `VERIFIED` or `SAFE_ABORT`. VERIFIED commits verification and registry plus terminal outcome and ownership release in one guarded replacement. SAFE_ABORT releases ownership but preserves unresolved intent, original observations, and retry=false without registry addition. A read-back uncertainty after replacement must be reported as uncertainty while a fresh no-dispatch reload recognizes the committed terminal state without replay.

## REQUIRED TEST/EVIDENCE WAVE

Implement and run the literal verifier fixture driver with the 28 IDs in plan Rev13, including count 56/58, suffix/temporary/hidden/symlink/outside/special/unreadable/command-error/mime, safe filenames, SAMPLE_2 mutation, wrong group, cross-entry, legacy, duplicate registry, invalid config, authority mismatch, and artifact read-back failure. The driver must launch the real CLI subprocess and compute expectations before reading product output. Retain literal argv, preconditions, independent pre/post hashes, stdout, stderr, exit, result, manifest, and inventory artifacts.

Implement and run the real subprocess transaction driver for Cases 01–12. The required independent assertions include:

- Case 01 normal prepare/resume/commit/finalize VERIFIED.
- Cases 02/03 one adapter counter side effect, durable false retry barrier, first-process failure/UNKNOWN, and fresh `--no-dispatch` recovery with no second dispatch.
- Case 04 duplicate-check `SKIP_DUPLICATE` and terminal resume `SKIP_TERMINAL`, counter zero.
- Case 05 one guarded commit winner and one stale-revision conflict; Case 06 owner conflict; Case 07 one prepare winner and one active-run conflict.
- Case 08 no replacement on write-before-replace fault.
- Case 09 terminal replacement survives read-back uncertainty; fresh reload is `SKIP_TERMINAL`, no dispatch.
- Case 10A atomic VERIFIED finalization; Case 10B atomic SAFE_ABORT preserving unresolved intent and no registry addition.
- Cases 11/12 legacy and contradictory inputs remain read-only and are not normalized.

Run the 11 authority negatives specified in the plan: one verify-only mismatch, six allowlisted test-only path/parser cases, and five production-mode missing/mismatched canonical authority or containment cases. Each must be independently proven no-write/no-lock/no-dispatch with exit 2 and `INVALID_AUTHORITY`.

Run the Status Contract v2 fixture driver and the exact authority baseline command from the plan before and after product verification. Required verification is incomplete if the baseline is unavailable; do not convert it to PASS by assumption.

## SOURCE AND CLOSURE RULES

Only `SOURCE_CORRESPONDENCE=CONFIRMED` can close exact source identity, and only through an authoritative exact join or one precise user fact in the preserved user-fact evidence format. Similar spelling, fingerprint, destination match, legacy record, historical GUI observation, bridge output, or plan rationale cannot substitute. `UNRESOLVED`, `LEGACY_PROVENANCE_LIMITED`, or `CONTRADICTED` remains non-closure and forbids production dispatch.

Keep Filesystem, Registry, Source, State, Overall, and the six task statuses orthogonal. A product PASS line is never an oracle. Internal command/read/artifact errors are UNKNOWN or incomplete according to the plan's stable result contract.

## STOP / ESCALATE CONDITIONS

- Any semantic change to requiredness, enum, retry, gating, result precedence, authority, fallback, or source closure: stop implementation, write escalation evidence, and replan; do not improvise.
- Any failed/uncertain authority validation, state replacement, read-back, revision/owner check, or unresolved dispatch barrier: safe abort with no retry and preserve evidence.
- Any mismatch to the requested `禎` source, any exact source proof missing, or any first-match/ambiguous registry match: report scoped CORE blocker; never merge or rewrite.
- Any ambiguous runtime dispatch or undocumented Save-All/menu identity: no Save-All retry. If a current observation is genuinely required, stop and request exactly one Human Gate after all automatic work, specifying app/group/album/count, exact permitted input, and safety purpose.
- Bridge/service repair, TCC changes, reinstallation, new permissions, deployment, and production download are outside this handoff. Prepare them only after route-specific causal proof and a later approved plan.

## DELIVERABLES AND STATUS

Stage 04 must write `execution.md` with command/input/stdout/stderr/exit evidence, check matrix, six orthogonal statuses, blockers, baseline delta, and artifact hashes. Stage 05 is mandatory independent acceptance of the actual CLI/evidence and must not modify product code. Only after all required acceptance evidence is real may the closing role write `result.md`; never claim goal complete from offline PASS or documentation completion alone.
