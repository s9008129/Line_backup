# LINE 相簿 Agent 備份

你人工開好 LINE 相簿列表、指定保存位置並授權，Agent 使用 [專屬 Skill](.agents/skills/line-album-agent-cua/SKILL.md) 先盤點、再備份，按相簿接續中斷任務。不以群組名稱辨識，不新增控制器。啟動方式只有 [使用手冊的提示詞](docs/LINE相簿備份_使用手冊.md)；只審查 Skill 或只盤點時不下載。

往後只維護 master。必要小工具沿用現有照片驗證與持久紀錄程式；下方 acceptance CLI 是保留的舊正式驗收工具，不是日常下載入口。舊研究來源與過時檔案的保存方式見 [整理紀錄](docs/專案整理紀錄.md)。新版完整盤點與相簿級接續尚需另行實機驗證，沒有在這輪整理中執行下載。

This repository contains the reusable `line_backup_acceptance` operator CLI for the LINE album acceptance workflow. It is fail-closed by design: authority is explicit, verify-only is read-only, and transaction state is guarded by a POSIX lock plus same-directory atomic replacement and read-back.

## Operator entry points

Set `PYTHONPATH` to the repository `src` directory and invoke `/usr/bin/python3 -m line_backup_acceptance`.

`verify-only` requires explicit `--project-root`, canonical `--config` and `--state`, destination, exact group key, date fingerprint, and an evidence directory. It emits independent filesystem, registry, source, state, and overall outcomes. Test-mode pause barriers are limited to the verifier fixture root.

`transaction prepare`, `resume`, `commit`, `finalize`, and `duplicate-check` require production canonical authority paths. Test mode is bounded to the 25 literal `/private/tmp/line-backup-acceptance-case-N` roots and `state.json`; both lexical and symlink-resolved fixture paths must remain inside the selected case root. It is for deterministic adapter fixtures only.

The persisted RC2 axes are kept separate. A committed intent always has `save_all_retry_allowed=false`; uncertain or possibly dispatched work becomes `TRIGGER_UNKNOWN`/`UNKNOWN` and is never replayed. Both `commit` and `finalize --outcome VERIFIED` require the same completed-dispatch proof before verification can advance. Only terminal `finalize` can commit `VERIFIED` or `SAFE_ABORT`. `duplicate-check` returns `SKIP_DUPLICATE`, while terminal `resume` returns `SKIP_TERMINAL`.

## Acceptance drivers

The subprocess drivers in `tests/` create isolated fixtures and retain raw stdout, stderr, exit codes, state snapshots, manifests, and hashes. They do not serve as the product state machine or accept a product status line as an oracle.

No command in this package dispatches LINE Save All. Formal project state, grants and existing backup files remain outside the daily helper's write surface. The current owner-facing goal is real LINE album backup; this acceptance CLI and the daily helper do not establish that outcome by themselves.

## Daily foreground records

`PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily --help` lists the local record operations. This helper records Agent-attested foreground observations, reserves local album attempts and checks downloaded files. It does not observe or operate LINE, authorize Save All, issue runtime grants, or verify that submitted screenshot/AX evidence is genuine. Its summary explicitly reports `sensor_verified=false`, `real_line_e2e=NOT_TESTED`, and `pass_scope=AGENT_ATTESTED_ACCOUNTING_ONLY`; a bookkeeping `PASS` is not a tool PASS or formal E2E acceptance.

Only supported normalized history with matching local group UUID, full album identity, status and required photo-verification evidence can count as COMPLETED. Legacy/unsupported history stays `PROTECTED_HISTORY`: it is preserved and blocks redownload, but also blocks a completeness PASS until resolved through a supported evidence path. An explicit UNKNOWN outcome is terminal for this helper and cannot be changed to STOPPED/NOT_SENT by another ordinary outcome call.


## Workspace portability

Production `join:` and `user_fact:` binding references default to the checked-out repository root instead of an owner-specific home-directory path. Set `LINE_BACKUP_WORK_ROOT` only when the canonical binding-artifact workspace intentionally lives elsewhere.
