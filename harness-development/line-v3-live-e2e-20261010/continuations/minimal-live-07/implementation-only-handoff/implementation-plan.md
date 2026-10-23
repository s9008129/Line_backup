# ML07 implementation-only continuation plan

## 接手 E2E Prompt

**新對話的實機執行者：請先讀本目錄 `handoff.md`、Amendment 06、本輪已審查 overlay `plan-contract.json` 及其 exact-copy `compiled-handoff.json`、E2E 報告和原始 `plan.md`／`handoff.md` 及原始 machine contract copies，再開始 LINE E2E。** 本輪只做離線 implementation/驗證，沒有 LINE/CUA 前景操作或 live sample。確認 fresh binary、grant/runtime binding、source freeze 和 formal check receipts 均相符後，先告知 app/surface 和下一個精確 capture 動作，等使用者明確交還前景；重新 fresh-capture 並確認群組、日期、張數及視窗連續性。不得用本輪 offline PASS、draft、fixture、mock、過期 frame 或猜測幾何當 live gate 證據。遵循原 plan 的 Save All at-most-once barriers、完整交易 readback、release 後 bounded scroll 和不同第二本相簿交易；未完成就如實保留 BLOCKED/PARTIAL 與停止原因。

## Goal and authority boundary

本附錄延續原 ML07 goal，補充使用者本輪明確改變的交付分工：先完成有界 e03 evidence recovery/early gates 與可離線驗證的 implementation；live D01、CUA/LINE、實機交易和兩本相簿 E2E 由新的實機對話／執行者完成。原始 `plan.md` SHA-256 `0d027dff633344fa3e05b0667b2d21e087eeec10006927f6bbe2a93ffe5df429`、`handoff.md` SHA-256 `fd5c059759a8eae9d4c8847d1516ab8a24e737b67cc27c9c7ff18bbc629410b3`，原 machine contract/handoff JSON 各 SHA-256 `84bcc6511585fe446f85c75adb6bc213222cb971a9b79ab0055c78bb3be59469` 保持原 bytes；`original-plan-contract.json` 是原 contract 的 exact copy。現有 `handoff.json` 也是歷史上的原 contract 副本，不是本輪 compiled overlay handoff；本輪 PlanReview 通過後須另建與已審 `plan-contract.json` 逐 byte 相同的 `compiled-handoff.json`。本附錄 v3 plan contract candidate SHA-256 為 `71dcb33bfa1ec7c4f06ac3182403a4687fc08b4dcf6d2f1da43868be5a63822b`；如果審閱後修改，須先固定新 hash 再通知 C。C review 是本 overlay 新要求的 task-local review，未通過前不得改產品；原 PlanReview `USER_WAIVED_NOT_RUN` 僅是原計畫歷史 waiver，不是本次 review 或任何 gate 的 PASS。原完整 LINE/D01/Save All/雙相簿/scroll/independent Acceptance gates 的 requiredness 與驗收意義保持不變；使用者另行授權把本輪 D01 前置及所有 CUA/LINE action/capture 延至新實機對話，故本輪不以未執行項目主張 gate 通過。

角色與寫入界線：`context_history` 是本輪唯一串行 Luna primary implementer，只寫 R 與下列四個非 Swift 產品路徑。`implementation_feasibility` 僅在明確 serial handoff 後擁有五個 literal Swift paths。root 是唯讀協調者，不實作。native allocation 為 0；本輪實際 native runtime capability 為 UNKNOWN/unavailable。implementation 與離線測試的 network policy 為 OFF。使用者另行授權的 Git add/commit/push 是之後由 root 明確 serial handoff 的既有 origin 發布工作，與 implementation/test network capability 分離。

## Current evidence at plan preparation

- HEAD observed previously: `0362d3e246d7a06b961f77ed345231992b4be595`, branch `v43-ab/codex-rev28`; original index was unstaged. Preserve all 11 pre-existing tracked dirty files and all unrelated untracked material. The three source dependencies `rev28/Sources/rev28ctl/PassiveCaptureDiagnostic.swift`, `rev28/Sources/Rev28Core/Composition/PassiveNativeDiagnostic.swift`, and `rev28/Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift` are existing untracked workspace files, not tracked baseline sources; this work does not add them to Git or claim a clean-checkout build. Report their exact paths and hashes in the final handoff and keep validation claims scoped to this workspace.
- e01 formal receipts remain E01 PASS (8 tests), E02 PASS (3 tests), B01 FAIL because the exact known FIFO had `S` versus `FIFO` representation. All three e01 IDs are consumed; preserve every receipt and the failure.
- e02 is frozen and pinned dependency preparation/finalization succeeded. Its one E01 call was `REFUSED` before claim, exit 2, error `FileNotFoundError: [Errno 2] No such file or directory: 'checks'`; no claim/invocation/stdout/stderr/receipt, no child launch, no e02 formal ID consumed. e02 is immutable and must not be repaired or retried.
- Read-only recovery after interruption found no `epochs/e03`, partial e03 artifact/claim, or matching active process. No formal e03 ID has been claimed.
- The latest relevant draft suite passed 17/17 with no errors/skips after correcting the family binding fixture. It is draft evidence, not a gate. The first 17-case run exposed fixture error `EVIDENCE_FREEZE_MISSING`; both outcomes are retained under `evidence/draft-e03-family-binding-01.json` and `-02.json`. The earlier 16/16 draft result is retained separately.
- Native Harness Python 3.14 is unavailable and the user chose not to repair it. A real CUA/LINE sample and native runtime behavior are unknown. Do not represent either as observed or passed.
- The new task-local C review is required before product edits. The native controller is unavailable for this continuation: do not create a native stage/invitation or claim native PASS, and do not replace it with a hand-built schema validator. Keep the prior PlanReview waiver distinct from this required overlay review.

## Bounded implementation sequence

1. Obtain C's independent read-only review of this amendment/plan. Do not edit product files before it returns. This review is scoped to the changed execution division and preservation of gates; it does not approve live UI actions or waive any requirement.
2. Complete one non-consuming e03 readiness pass: verify actual e02 immutable copies and receipt chain; reconcile full current namespace against the original anchor, exact in-scope additions and every outside-R delta; validate all physical output ancestors and producer receipts; verify the e03 dependency inputs/install plan and both family SHA bindings. Then prepare e03 solely from the seven existing local pinned wheels with task-local Python 3.13, no network/global install, materialize once, finalize the actual dependency receipt, and run e03 E01→E02→B01 once each with full tail readback. No writes during inventory pairs. A refusal/failure preserves the ID/output state and stops; no e04.
3. After early gates and tail readback pass, inspect the exact existing Python/JS/native interfaces before implementation. Implement only the four non-Swift literal product paths owned by this serial writer. Keep evidence inputs explicit and fail-closed; preserve unknown raw UI structure as unknown. Do not invent a live sample, selector, coordinate, album identity, or CUA result. Complete the five reserved Swift paths only by serial handoff to `implementation_feasibility`; it may not edit before that handoff. Root coordinates and does not implement.
   - For the five Swift files, use B's read-only design as constraints: route `native-context` in `main.swift` before any live-composition dispatch; bind passive before/after receipts to exact CUA raw AX/image refs, their SHA-256 and capture time, session/request identity, and prior-ref hash; implement bounded direct AX traversal that retains actual parent/index/focus/root-window relations plus errors, nulls, truncation and completeness. Use SCK, CG and ProcessInstance with actual AX window candidates and require a unique correlation to the CUA window, without imposing a global single-main-window assumption. Use three non-collinear actual OCR anchors for geometry mapping; date-anchor segmentation alone is not a full-card witness. The pure `AlbumVisualWitness` validator must check the complete card/container/thumbnail/control/metadata/neighbor and erosion-resistant geometry; absent facts return typed refusal. Add meaningful synthetic algorithm fixtures for valid and invalid structures, while labelling them offline only. Implement useful pass/parse paths; do not replace the pipeline with an always-REFUSED stub.
4. Run the bounded offline checks named in the frozen contract against real local schemas/store code, production check closure and build interfaces. Test meaningful success and refusal paths, transaction authority/at-most-once rules, and ensure no fixture can yield D01/live acceptance. Publish hashes, argv, environment, streams, exit codes, and actual outputs. Do not run the live CUA D01 capture or any LINE operation in this turn.
5. Update the E2E report with actual e03 and offline product facts, all failures/unknowns, no live operation, six statuses, and limits. Preserve separate core gate, required verification, and independent Acceptance status. Prepare `implementation-only-handoff/` with exact byte copies/refs to original frozen machine artifacts, a human handoff that starts with the E2E prompt above, next-action sequence, evidence paths/hashes, and outstanding live gates. Compile `compiled-handoff.json` as an exact byte copy of the reviewed overlay `plan-contract.json`; existing `handoff.json` remains clearly identified as the historical original-contract copy. The exact root-level collaboration output is `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/代理協作開發紀錄.md`, producer `collaboration_recorder`, phase `REPORT`, type `REGULAR`, lifecycle `DRAFT` mutable output at that literal path, cap 8 MiB, with actual full readback/hash. It was created as a 26,730-byte file, SHA-256 `6f67198203adb790bf8718edd08cf00f8afb6f12f18b2a534d108fe68fdfc574`. Do not pin the current mutable log in source hashes or generalize the path rule to ROOT or R.
6. Draft a detailed Git message containing intent, completed work, validation, and the next live E2E stage. Git add/commit/push are user-authorized as a separate root-controlled publication to the existing origin, after root's serial handoff; this does not expand implementation network policy. Do not disturb unrelated dirty/untracked work. Record resulting commit/push evidence if executed.

## Explicit stop conditions

Stop immediately on an unexplained namespace delta, missing/ambiguous parent identity, receipt/source-family SHA mismatch, E03 formal preflight refusal, failed formal check/tail, unknown product data boundary, or failed offline required test. Do not retry a consumed ID, add a new epoch, lower a gate, replace a writer, create a fake PASS, access LINE/CUA, or repair state/images. Return the exact evidence and decision needed to root/Planner.

## Six orthogonal statuses at plan time

- `PRIMARY_OUTCOME_STATUS`: NOT_ACHIEVED; two-album E2E not done.
- `IMPLEMENTATION_STATUS`: IN_PROGRESS; e03 recovery and offline implementation remain.
- `CORE_ACCEPTANCE_STATUS`: NOT_RUN for the full user outcome.
- `REQUIRED_VERIFICATION_STATUS`: BLOCKED pending native runtime and real E2E; `USER_WAIVED_NOT_RUN` remains visible.
- `INDEPENDENT_ACCEPTANCE_STATUS`: NOT_RUN.
- `TASK_CLOSURE_STATUS`: OPEN.

## Original gate carry-forward at plan time

All original gates remain required. These are current statuses from the report and immutable receipts, not predictions for the final implementation result. The next executor must update this table from new evidence rather than inherit a PASS from a draft.

| Original gate ID | Required | Current status | Evidence reference |
|---|---:|---|---|
| `G_BASELINE_07` | yes | FAIL (e01 B01 FIFO representation mismatch) | `epochs/e01/evidence/checks/B01-baseline-pair.receipt.json`; `epochs/e01/evidence/inventory/baseline-compare.json` |
| `G_EVIDENCE_POLICY` | yes | PARTIAL; e01 E01 passed, current recovery E01 not run | `epochs/e01/evidence/checks/E01-evidence-policy.receipt.json`; e02 preclaim refusal in `E2E測試報告.md` |
| `G_AUTH_RUNTIME` | yes | BLOCKED; required native runtime unavailable | `evidence/controller-readiness.json`; `E2E測試報告.md` |
| `G_REAL_LINK` | yes | NOT RUN; no live CUA sample | `E2E測試報告.md` current status |
| `G_OFFLINE` | yes | NOT RUN for this continuation's implementation checks | `evidence/draft-e03-family-binding-02.json` (draft only) |
| `G_CATALOG_1` | yes | NOT RUN | `E2E測試報告.md` current status |
| `G_CATALOG_2` | yes | NOT RUN | `E2E測試報告.md` current status |
| `G_MENU_1` | yes | NOT RUN | `E2E測試報告.md` current status |
| `G_MENU_2` | yes | NOT RUN | `E2E測試報告.md` current status |
| `G_FIRST` | yes | NOT RUN; no transaction or Save All | `E2E測試報告.md` current status |
| `G_SCROLL` | yes | NOT RUN | `E2E測試報告.md` current status |
| `G_SECOND` | yes | NOT RUN; no distinct second album | `E2E測試報告.md` current status |
| `G_PRESERVE_07` | yes | BLOCKED for final preservation gate; no new live transaction | `evidence/bootstrap-anchors.json`; `E2E測試報告.md` |
| `G_REPORT` | yes | IN PROGRESS; final report must reflect actual e03/offline result | `E2E測試報告.md` |
| `G_ACCEPTANCE` | yes | NOT RUN; independent Acceptance still required | `E2E測試報告.md` current status |
