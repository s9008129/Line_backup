# LINE backup acceptance package

日常 Mac LINE 相簿備份請先閱讀 [LINE 相簿備份使用手冊](docs/LINE相簿備份_使用手冊.md)，內含可複製的多群組啟動 Prompt。操作入口為具備原生 Mac Computer Use 的 Codex Agent＋既有 Skill；下列 acceptance CLI 不會操作 LINE 或派送「儲存全部」。新群組實機驗證與正式 AUTO 驗收狀態請以手冊限制為準。

This repository contains the reusable `line_backup_acceptance` operator CLI for the LINE album acceptance workflow. It is fail-closed by design: authority is explicit, verify-only is read-only, and transaction state is guarded by a POSIX lock plus same-directory atomic replacement and read-back.

## Operator entry points

Set `PYTHONPATH` to the repository `src` directory and invoke `/usr/bin/python3 -m line_backup_acceptance`.

`verify-only` requires explicit `--project-root`, canonical `--config` and `--state`, destination, exact group key, date fingerprint, and an evidence directory. It emits independent filesystem, registry, source, state, and overall outcomes. Test-mode pause barriers are limited to the verifier fixture root.

`transaction prepare`, `resume`, `commit`, `finalize`, and `duplicate-check` require production canonical authority paths. Test mode is bounded to the 25 literal `/private/tmp/line-backup-acceptance-case-N` roots and `state.json`; both lexical and symlink-resolved fixture paths must remain inside the selected case root. It is for deterministic adapter fixtures only.

The persisted RC2 axes are kept separate. A committed intent always has `save_all_retry_allowed=false`; uncertain or possibly dispatched work becomes `TRIGGER_UNKNOWN`/`UNKNOWN` and is never replayed. Both `commit` and `finalize --outcome VERIFIED` require the same completed-dispatch proof before verification can advance. Only terminal `finalize` can commit `VERIFIED` or `SAFE_ABORT`. `duplicate-check` returns `SKIP_DUPLICATE`, while terminal `resume` returns `SKIP_TERMINAL`.

## Acceptance drivers

The subprocess drivers in `tests/` create isolated fixtures and retain raw stdout, stderr, exit codes, state snapshots, manifests, and hashes. They do not serve as the product state machine or accept a product status line as an oracle.

No command in this package dispatches LINE Save All. Formal project state and existing backup files must be treated as read-only for the Stage 04 acceptance wave.


## Workspace portability

Production `join:` and `user_fact:` binding references default to the checked-out repository root instead of an owner-specific home-directory path. Set `LINE_BACKUP_WORK_ROOT` only when the canonical binding-artifact workspace intentionally lives elsewhere.
