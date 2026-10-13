# G1 Runtime Compatibility Fix — Review Packet

## Decision scope

This is an isolated candidate for two source-identified compatibility failures. It does not activate the candidate, bind a runtime, or perform a LINE observation. The code is stacked on PR #3 because that branch contains the reviewed scroll-path dependency; PRs #3, #4, #5, and #6 remain unchanged.

The bounded source findings are recorded in the accepted [PR #6 runtime entry-point verification](https://github.com/s9008129/Line_backup/blob/e82864812a4403adf4c4b28bc201cc3aa2b464e3/review/runtime-entrypoint-20261013/RUNTIME_ENTRYPOINT_VERIFICATION.md). The accepted G0 route decision and current governance blocker are in [PR #4 recovery decision](https://github.com/s9008129/Line_backup/blob/1c147e7b61301aa8f1b813be069d32bfe003b3dd/review/g0-controller-route-20261013/RECOVERY_DECISION.md). This candidate does not reopen those decisions or claim their blockers are cleared.

The affected original lineage remains `TASK-4acb4326ea2a4c50ace6f333f2de8751`, issue `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5`, and c6 `c6c6b55d-865f-467b-94ba-3fd669df97ec`. Accepted state is G0 BLOCKED, G1–G3 NOT_RUN, original issue WAIT_HUMAN, c6 consumed 1, retries 0, with all 28 original gates retained. No state or history file was changed.

The original issue criterion is “Exact current contract/path and full runtime task-module closure agree in JS/Python/Swift, then the original formal build/probe/gates proceed.” Its UTF-8 SHA-256 is `9b5b171e37e828f325b004b6a8a91d7ceae6ef52b36b2a4270ce6c4f8d4db657`. The historical c6 analysis/permission criterion has a different hash (`82b1892f80e4b1b00a0386644ea875148fa0c82cbfa7cb81228b786bae6b8861`) and is not substituted for the issue criterion.

## Candidate changes

1. `FrameSupportGrantProfile` is a closed compile-time identity allowlist for the existing legacy profile and the original minimal-live-08 task/contract/artifact tuple. Legacy keeps any `harness-development/` grant path accepted by the prior safe-path check; its prior authorization and runtime checks remain in the legacy branch and it does not acquire a new mandatory `task_modules` list. ML08 accepts only its two exact grant filenames, then fails closed because its canonical human authorization and CRITICAL Plan Review evidence binding is unverified. This is a partial identity/source patch, not usable ML08 grant compatibility.
2. `createRetain` recognizes only PNG in the supported noninterlaced 8-bit RGB/RGBA subset before creating a screenshot file. It validates chunk CRCs/order, bounded dimensions, zlib stream consumption, output size, and scanline filter values, and derives `.png` from validated bytes. JPEG, unsupported PNG variants, malformed, truncated, or unknown bytes fail before writes. AX, receipts, and other evidence remain `.bin`. The CUA screenshot producer's actual byte format is not verified, so PNG-only retention may reject a genuine frame until authorized producer evidence establishes its format.

The full minimal-live-08 `live_runner.mjs` source was untracked in the original local workspace and absent from PR #3. The candidate adds only that one source module; no adjacent task directory or private evidence was copied. A bounded code/privacy scan found no grant, runtime binding, group/account data, personal path, screenshot, AX capture, or credential in the source. Its imports refer to sibling modules not included in this PR, so the PR checkout alone is not a runnable task tree; the focused test extracts and executes the literal `createRetain` function from this file with only pure dependencies and in-memory storage.

## Status

| Field | Result |
|---|---|
| `CODE_PATCHED` | YES — isolated candidate branch only |
| `SOURCE_VALIDATED` | PARTIAL — exact-source hash/precondition and the literal JS production function were checked; the integrated Swift CLI was not successfully compiled |
| `OFFLINE_BUILD_PASS` | NO — the single authorized isolated Swift build failed in unrelated existing copied `PassiveContextObservation.swift` code before the focused tests ran |
| `RUNTIME_BOUND` | NO — no current runtime-binding/grant was validated or created |
| `LIVE_PRODUCER_PASS` | NO — no producer was executed |
| `GUI_AUTHORIZED` | NO — this round had no GUI authority and made no CUA/UI call |

## Validation and limits

The focused Node check passed 14 bounded cases by invoking the exact `createRetain` body from the candidate source (literal function-body SHA-256 `c8a90c41255b1c1039bc1fdd584ae006f5d1f506df1808217866518a46472ba9`). It used generated RGB/RGBA PNG bytes and malformed/unsupported fixtures with in-memory storage; it did not create a CUA App or invoke host tools. It confirmed retained bytes/length/hash, `.bin` AX/other-artifact behavior, malformed PNG/JPEG/unknown rejection before writes, frame-ID refusal, readback failure, and rejection of trailing compressed input. JPEG is deliberately unsupported because the previous marker parser accepted malformed entropy.

One Swift build/test invocation was made against a temporary copy of the current local `rev28/Package.swift`, `Sources/`, and `Tests/`, overlaid with the then-current candidate patch/helper/test. The pre-correction snapshot had 94 Swift files / 1,491,136 bytes. Its reproducible manifest is the sorted list of `[relativePath, byteLength, SHA256]` triples serialized with sorted keys and compact JSON separators (excluding `.build`); SHA-256 `b5aef9170f0431e2522a60ff832da3cd5af8fd4eb3934de126451de1109c5be4`. It failed before the focused profile tests because existing copied `PassiveContextObservation.swift` has Swift 6.3 compile errors: mutating `.capture()` on an immutable temporary at line 166, `CGRect.map` called on nonoptional values at lines 279 and 285, and CoreFoundation conditional-downcast diagnostics at lines 468 and 503. The runner did not preserve a numeric process exit code or standalone full log; the observed command result was nonzero, and no exit number or log hash is claimed. No second build or test was run, and those unrelated files were not edited. The final Swift edits remain uncompiled.

The existing Q grant, runtime binding, exact Q binary, verified canonical authorization/Plan Review binding, and live caller/session remain absent or unverified. No ML08 authorization path is guessed or accepted by this patch. The current local `main.swift` contains an unrelated dirty `native-context` CLI addition; an in-memory projection replaced only the target grant function in the exact original file and confirmed the rest, including that block, byte-identical. The unrelated block is omitted from this PR.

The candidate does not establish that the available binary was built from either inspected source, that a producer emitted genuine complete closure evidence, or that the original criterion is met. It does not clear G0 or authorize G1. See [CONTRACT_COMPATIBILITY.md](CONTRACT_COMPATIBILITY.md), [IMAGE_RETENTION_FIX.md](IMAGE_RETENTION_FIX.md), [TARGETED_VALIDATION.md](TARGETED_VALIDATION.md), [SOURCE_PROVENANCE.md](SOURCE_PROVENANCE.md), and [DEPLOYMENT_AND_AUTHORITY_BOUNDARY.md](DEPLOYMENT_AND_AUTHORITY_BOUNDARY.md).

## Delivery context and next review

The candidate code and the first six-document review packet were delivered in commit `a72b2bb70e938991eff58afb6fd99822e4ef8c54` on Draft PR #7. This follow-up commit changes this review packet only; it adds no implementation, tests, grant, runtime binding, or task-state data. PR #7 remains a Draft candidate based on PR #3, not a release or activation.

The code changes in the earlier commit address two bounded source failures: a closed task/contract/artifact identity profile for `frameSupportVerifyGrant`, while retaining the legacy task-local grant path and legacy checks; and screenshot retention limited to a structurally checked noninterlaced 8-bit RGB/RGBA PNG subset with unsupported JPEG and PNG forms rejected before write. The ML08 profile intentionally stops at identity recognition and refuses because the original task’s canonical authorization and CRITICAL Plan Review evidence binding remain unverified. The actual CUA screenshot byte format is also unknown, so the PNG restriction is a conservative compatibility subset and may reject genuine frames.

Evidence remains partial. The literal production JavaScript retention function passed 14 offline cases with generated bytes and in-memory storage. The one isolated Swift package build/test attempt failed in pre-existing copied `PassiveContextObservation.swift` code before the focused Swift tests; no retry was made, and the final Swift profile/CLI edits are uncompiled. The earlier tool result did not retain a numeric exit code or standalone full log. No runtime binding, producer execution, GUI authority, or original issue criterion PASS was established.

The original lineage remains G0 BLOCKED and G1–G3 NOT_RUN; Issue `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5` remains WAIT_HUMAN; c6 `c6c6b55d-865f-467b-94ba-3fd669df97ec` remains consumed 1 with retries 0; all 28 original gates and history remain unchanged. This documentation update does not claim or perform any state transition.

Recommended next review is a bounded Chief Reviewer decision on whether and how to address the existing Swift package compile blockers before evaluating the final Swift change, plus separate verification of the canonical CRITICAL authorization binding and actual CUA screenshot format. Until those prerequisites are independently established and separately authorized, keep ML08 grant admission fail-closed and do not bind or launch a runtime, perform GUI work, or mark G1 complete. This recommendation does not authorize another build, grant creation, runtime binding, LINE session, or activation.
