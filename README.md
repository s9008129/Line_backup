# LINE backup acceptance package

This repository contains the reusable `line_backup_acceptance` operator CLI for the LINE album acceptance workflow. It is fail-closed by design: authority is explicit, verify-only is read-only, and transaction state is guarded by a POSIX lock plus same-directory atomic replacement and read-back.

## Operator entry points

Set `PYTHONPATH` to the repository `src` directory and invoke `/usr/bin/python3 -m line_backup_acceptance`.

`verify-only` requires explicit `--project-root`, canonical `--config` and `--state`, destination, exact group key, date fingerprint, and an evidence directory. It emits independent filesystem, registry, source, state, and overall outcomes. Test-mode pause barriers are limited to the verifier fixture root.

`transaction prepare`, `resume`, `commit`, `finalize`, and `duplicate-check` require production canonical authority paths. Test mode is bounded to the twelve literal `/private/tmp/line-backup-acceptance-case-N` roots and `state.json`; it is for deterministic adapter fixtures only.

The persisted RC2 axes are kept separate. A committed intent always has `save_all_retry_allowed=false`; uncertain or possibly dispatched work becomes `TRIGGER_UNKNOWN`/`UNKNOWN` and is never replayed. Only terminal `finalize` can commit `VERIFIED` or `SAFE_ABORT`. `duplicate-check` returns `SKIP_DUPLICATE`, while terminal `resume` returns `SKIP_TERMINAL`.

## Acceptance drivers

The subprocess drivers in `tests/` create isolated fixtures and retain raw stdout, stderr, exit codes, state snapshots, manifests, and hashes. They do not serve as the product state machine or accept a product status line as an oracle.

No command in this package dispatches LINE Save All. Formal project state and existing backup files must be treated as read-only for the Stage 04 acceptance wave.
