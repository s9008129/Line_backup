# Controller route findings (redacted derivative)

The route review examined four files from the task-local selected `runtime/resources-luna` copy of immutable Harness v4.8.0. Paths in this table are relative to `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/`. Each named file hash matched its corresponding installed immutable 4.8.0 file; this does not establish full resource-tree identity or OS/network enforcement. These are source-analysis findings, not runtime or Controller execution receipts.

| Source path (repository-relative) | Original source SHA-256 | Relevant source locations | Finding |
| --- | --- | --- | --- |
| `runtime/resources-luna/tools/harness/controller.py` | `385bbd2abd57ed305c01c7437f449833ed09cfc7e9f07add87d6352d405a8af5` | 360–441, 1850–1940, 1955–1972, 2015–2043, 2239–2299 | Allocation requires an eligible task stage. Replan reconciliation rejects unresolved/exhausted issues and does not accept the current `BLOCKED` candidate. |
| `runtime/resources-luna/tools/harness/escalation.py` | `7044aa55c6cc7721205fbd95ed2643ac0debcc67701c303c563a23dbc4768451` | 154–187, 287–358, 360–387 | Lineage linking preserves the issue record; current `WAIT_HUMAN` consumed issue does not satisfy authorization or allocation guards. |
| `runtime/resources-luna/tools/harness/cli.py` | `6b05f608d582e117b18e9a4554c6f1573d2e7516d3bdf56ca48555b18f9721cd` | 299–323, 364–370, 409–453 | `resume` reads and reports state; it does not resolve STOP or allocate a stage. |
| `runtime/resources-luna/policies/v4.8.0/workflow-routing.md` | `7c2251913507a8cc09b4a697576963aaf6694ffd7fd7af55a6eb2e813a690912` | selected immutable policy | Independent Plan Review and Acceptance requirements remain applicable. |

The current issue state and attempt count are given in `route-status.redacted.json`. The identifiers above preserve task lineage; personal session/thread identifiers, invitation material, actor names, absolute user paths, and raw Controller records have been removed. The listed hashes identify the local reviewed source bytes; source copies are withheld.
