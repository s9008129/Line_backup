# Controller protocol blocker: c6 issue continuation

Observed 2026-10-12. This is a protocol limitation, not a product-test result.

## Facts

- Native task `TASK-4acb4326ea2a4c50ace6f333f2de8751` is CRITICAL, has the original full task contract, and still lists all required IMPLEMENT and ACCEPTANCE gates in `controller/TASK-4acb4326ea2a4c50ace6f333f2de8751/state.json`.
- Its original task-local allowed paths include Q, the adapter, Python implementation, Swift CLI/core, relevant tests, and protected state/ledger paths. The c6 issue permission is narrower (the reviewed correction is limited to `rev28/Sources/rev28ctl/main.swift` and Q).
- `c6c6b55d-865f-467b-94ba-3fd669df97ec` is a real native IMPLEMENT run with operation scope `ISSUE_CONTINUATION`; its contract validation receipt is VALID. The role selection is Luna/high from the bound turn context; backend attestation remains UNKNOWN.
- No c6 product edit, build, test, GUI input, or download occurred. Native allocation wrote the expected controller run and issue records; the issue is `CONTINUATION_CONSUMED`. Product backup state and GUI ledger were not changed.

## Source evidence

Selected Harness source is the immutable task-local copy under `runtime/resources-luna`:

- `runtime/resources-luna/tools/harness/controller.py`, SHA256 `385bbd2abd57ed305c01c7437f449833ed09cfc7e9f07add87d6352d405a8af5`: `allocate_run` lines 419–424 invokes `IssueLedger.guard_task` with the full state allowed paths and marks any permission-bearing allocation `ISSUE_CONTINUATION`; `record_result` lines 1613–1622 requires a completed PASS, enforces the permission criterion, and advances the ordinary task workflow. Lines 1631–1642 finish the issue and force WAIT_HUMAN while any issue remains pending. `_advance` lines 2260–2269 blocks every non-PASS; lines 2291–2299 marks IMPLEMENT complete and routes this CRITICAL task to independent ACCEPTANCE; required gates are checked in lines 2305–2312 and acceptance logic continues at 2313 onward.
- `runtime/resources-luna/tools/harness/escalation.py`, SHA256 `7044aa55c6cc7721205fbd95ed2643ac0debcc67701c303c563a23dbc4768451`: `IssueLedger.guard_task` lines 320–357 permits only an IMPLEMENT continuation for a `CONTINUATION_AUTHORIZED` issue and checks that every permission path fits within the run's frozen paths. It consumes the single continuation. `finish_task_run` lines 360–387 resolves only when the run is accepted and supplies verified files matching the exact issue success criterion; otherwise the issue moves to WAIT_HUMAN.
- Frozen c6 `run.json` binds the narrow continuation permission and unchanged original contract. The invitation is `runs/c6c6b55d-865f-467b-94ba-3fd669df97ec/invitation.json`, SHA256 `f0d0008a3a4c589ac09c54544d6d9901774de1082684264926a4f2711fa364e3`; run ID `c6c6b55d-865f-467b-94ba-3fd669df97ec`; nonce `d5875f7c9d864cebbf37038c26ed9d77`; contract SHA256 `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc`.
- c6 contract validation receipt `runs/c6c6b55d-865f-467b-94ba-3fd669df97ec/schema-validations/68fbd9d1f1b1820749b45b2abb41f647002ea7b3512d1ec949d26ec3ecca5fd5.json`, SHA256 `68fbd9d1f1b1820749b45b2abb41f647002ea7b3512d1ec949d26ec3ecca5fd5`, records purpose CONTRACT and verdict VALID.

## Conclusion and stopping point

The controller does not expose a supported route that both (a) consumes this narrow, single-use continuation, and (b) returns to the full original IMPLEMENT workflow with all original required evidence. Returning PARTIAL/FAIL/BLOCKED leaves the task blocked and the issue unresolved. Returning PASS for only the correction would make `finish_task_run` require the issue's exact criterion and verified files, but ordinary stage advancement would also declare IMPLEMENTATION_STATUS COMPLETE and route toward Acceptance while task gates remain missing; pending issues additionally force WAIT_HUMAN. This continuation cannot safely be used as a shortcut or relabeled as a full implementation.

Therefore c6 is held before product edits. Do not forge PASS, broaden its reviewed scope, manipulate issue state, allocate another continuation, or reuse the prior run ID. Existing issue/run evidence and budgets remain intact. Commander decision is needed on the separately drafted fresh-lineage design. This change records the protocol limitation only; it does not change the native controller, contract, gates, or product.
