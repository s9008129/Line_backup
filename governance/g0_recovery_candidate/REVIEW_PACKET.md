# G0 Governance Recovery Candidate — Not Activated

## Review decision requested

Review this isolated state-machine candidate for safe issue-scope recovery and original-task reactivation. This artifact is not runtime evidence, a formal role result, an IMPLEMENT PASS, or permission to activate the mechanism. The Chief Reviewer authorized implementation in isolation only; governance activation and the separate implementation escalation remain unapproved.

## Pinned lineage and current facts

The candidate binds the existing `TASK-4acb4326ea2a4c50ace6f333f2de8751`, issue `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5`, and c6 `c6c6b55d-865f-467b-94ba-3fd669df97ec`. The accepted baseline is continuation count 1, retries 0, task BLOCKED with no next stage, issue WAIT_HUMAN, and 28 frozen required gates. G1–G3 remain NOT_RUN. c6 did not complete the local repair.

The safely reviewable original criterion text is: “Exact current contract/path and full runtime task-module closure agree in JS/Python/Swift, then the original formal build/probe/gates proceed.” Its UTF-8 SHA-256 is `9b5b171e37e828f325b004b6a8a91d7ceae6ef52b36b2a4270ce6c4f8d4db657` (142 bytes). The distinct c6 permission/analysis criterion SHA-256 is `82b1892f80e4b1b00a0386644ea875148fa0c82cbfa7cb81228b786bae6b8861`; it is retained as historical context and cannot substitute for the original criterion. The original condition is bounded runtime-binding agreement, not full IMPLEMENT completion or Acceptance.

## Candidate behavior

`candidate.py` models three separately signed transitions. Governance authorization creates one declarative permit with no command runner while preserving WAIT_HUMAN, BLOCKED, continuation 1, retries 0, the six frozen status values, and all 28 ordered gate records. An independent verifier then attests exact supplied proof bytes and operation/lineage binding. Only a parsed proof for the original criterion may resolve the issue; an authenticated rejection is terminal and leaves it WAIT_HUMAN. A separate governance action can then expose only remaining IMPLEMENT eligibility. No transition marks IMPLEMENT complete, accepts or waives gates, or creates Acceptance.

The candidate uses HMAC-SHA-256 with separate host-supplied governance and verifier trust roles. Keys are snapshotted in memory and shared IDs/material across roles are rejected. The test helper is intentionally suitable only for deterministic isolated tests. The module has no filesystem, subprocess, network, UI, or Controller integration. Candidate events retain canonical signed payload bytes and proof bytes, and each transition validates the event chain and reconstructs operation state from authenticated events.

The proof parser requires exactly three matching language results, the frozen contract and task-root boundary, a normalized in-bound module path set, a complete declared closure manifest, canonical JSON, and exact raw-byte digest/length. This validates a signed declaration's structure; it does not independently read runtime files or prove that the producer observed the real runtime.

## Source and evidence basis

Engineering base: `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`, the tracked development branch selected for this independent candidate. The candidate is newly authored under `governance/g0_recovery_candidate/`; it does not copy the Harness or modify its controller, schemas, runtime, task state, or history.

Selected local source identities used for bounded design review:

| Source | SHA-256 |
| --- | --- |
| local v4.8.0 `controller.py` | `385bbd2abd57ed305c01c7437f449833ed09cfc7e9f07add87d6352d405a8af5` |
| local v4.8.0 `escalation.py` | `7044aa55c6cc7721205fbd95ed2643ac0debcc67701c303c563a23dbc4768451` |
| local `workflow-routing.md` | `7c2251913507a8cc09b4a697576963aaf6694ffd7fd7af55a6eb2e813a690912` |
| frozen contract | `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc` |
| original task state | `17e74f0b9f00fafa770273dd5a481e3aa8c98fb1ae9d508ff21bb248956ec822` |
| frozen gate-file record | `f13f019adeb9afe5eb019f9abe579b9795834f5959e15bf404c7a51ce8c63fe0` |
| canonical 28-record gate catalog | `697821120d0eaea35e9b7bcab5c8b7ca8a99002d9e1e9184494bbf844ebc0f49` |

The [accepted source excerpts](https://github.com/s9008129/Line_backup/blob/1c147e7b61301aa8f1b813be069d32bfe003b3dd/review/g0-controller-route-20261013/CONTROLLER_DECISION_EXCERPTS.md) and [recovery decision](https://github.com/s9008129/Line_backup/blob/1c147e7b61301aa8f1b813be069d32bfe003b3dd/review/g0-controller-route-20261013/RECOVERY_DECISION.md) at immutable PR #4 source-verification commit `1c147e7b61301aa8f1b813be069d32bfe003b3dd` document the reviewed stop and unsupported route. They are design evidence, not a new execution or re-review of the original lineage. Source identities above are selected local copies and bounded design inputs. They do not establish full installed-release identity or OS enforcement. The 28-record test fixture is derived from the already reviewed public redacted whitelist; no raw task state, receipts, screenshots, AX data, or runtime dump is included.

## Verification and present boundary

The isolated deterministic suite is `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v governance.g0_recovery_candidate.tests.test_candidate` (14 tests; see [TARGETED_TEST_RESULTS.md](TARGETED_TEST_RESULTS.md)). No Controller, task allocation, retry, runtime command, LINE/UI/AX interaction, download, R2, or real recovery operation was executed.

The real canonical module path is UNBOUND. Positive proof tests use explicitly TEST_ONLY host context and synthetic fixture data. Actual producer provenance, independent observation of the full runtime closure, host trust-root provisioning, durable atomic compare-and-swap, rollback/replay protection across processes, and reviewed v4.8.0 integration are unverified. The six status values are frozen from the accepted status projection; all 28 gate records remain intact and unaccepted.

## Risks and reviewer focus

The candidate could be misused if a caller treats TEST_ONLY state or a self-declared closure as real evidence, supplies caller-controlled trust keys, or applies the returned task state without a separately reviewed integration. HMAC demonstrates possession of a configured shared key, not non-repudiation or human identity. An in-memory event chain alone cannot prevent rollback to an older snapshot. These limitations block activation. Review should focus on exact envelope binding, evidence verification, event replay/idempotency, six-status/gate immutability, and the activation prerequisites in [ACTIVATION_BOUNDARY.md](ACTIVATION_BOUNDARY.md).
