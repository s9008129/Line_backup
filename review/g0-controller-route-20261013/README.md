# G0 controller-route review package

This folder is a privacy-safe publication derivative for independent review of the original ML08 task's G0 controller-route blocker. It records documentation/source review only. G0 remains `BLOCKED`; G1–G3 remain `NOT_RUN`.

## Review files

- [Route proposal](ROUTE_PROPOSAL.md) — Route A/B findings, retained gates, and missing execution prerequisites.
- [Review packet](REVIEW_PACKET.md) — decision boundary and reviewer question.
- [Approval request](approval-request.md) — decision requested from reviewer and governance owner.
- [E2E status report](E2E測試報告.md) — current status and limits.
- [Evidence manifest](EVIDENCE_MANIFEST.md) — original source hashes, derivative hashes/sizes, ZIP hash, and withheld artifacts.
- [Redacted route status JSON](evidence/route-status.redacted.json) — lineage, both six-status projections, and all 28 gate specifications with the nine permitted metadata fields.
- [Redacted c6 admission JSON](evidence/c6-admission.redacted.json) — whitelist view of admitted result and issue/task state.
- [Redacted issue event JSONL](evidence/issue-events.redacted.jsonl) — seven whitelist event projections with source and prior-event digests; not raw-chain verification.
- [Controller source findings](evidence/controller-route-findings.redacted.md) — source paths, digests, and reviewed branches.
- [Sanitized review ZIP](G0_CONTROLLER_ROUTE_REVIEW_20261013_REDACTED.zip) — contains only the review Markdown and redacted evidence files listed in the manifest; the manifest itself is outside the ZIP to avoid self-reference.

## Source and publication precision

Controller source paths in the findings table are relative to `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/`. The selected `runtime/resources-luna` directory is a task-local copy. The hashes for the four named controller, escalation, CLI, and routing-policy files matched their corresponding installed immutable v4.8.0 files. This does not establish identity of the full resource tree, OS sandboxing, or network denial.

The original repository is private. These review files were prepared in an isolated worktree based on `b7bb666`; the original main worktree and its 18 tracked dirty paths were left untouched. GitHub PR #3 remains Draft/Open/unmerged. This package contains no raw Controller/event receipts, source-code copies, screenshots, AX, photos, backup-state payloads, local user paths, personal runtime identifiers, or credential values. Redacted JSON/JSONL is derived evidence and is not a native receipt or gate PASS.
