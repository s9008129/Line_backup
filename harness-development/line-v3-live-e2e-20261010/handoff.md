> 你是本輪 IMPLEMENTER。使用指定 project root，先讀取本計畫、format 3 契約、授權／免審原文、前次 E2E 報告及本輪基線。使用者已選定唯一 v3 writer、保留歷史的 schema 2→3 遷移、完整 catalog admission，並授權兩個獨立 cap=1 lifecycle 所需的 Save All 與數量；沿用授權執行。依序完成離線整合及故障驗證、來源凍結、正式遷移、明確 LINE 前景交接、第一本完整交易、實際 scroll 與第二本完整交易、報告、事後獨立 Acceptance、Planner 回饋及 Git 交付。採 root 串行實作，保存既有工作與所有失敗證據。每個副作用先核對 gate；未知 dispatch 不重送。遇到 material blocker，保存最小重現、狀態前後差異與精確決策需求，依 convergence 規則處理。最後使用另一個唯讀 helper 撰寫符合實際結果的提交訊息，再由 root 完成精準 add、commit、push。

# Frozen Plan

# LINE v3 交易整合與兩本相簿實機 E2E 計畫

Task ID: `TASK-20261010-line-v3-live-e2e`<br>
Project root: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`<br>
This frozen plan records the user-authored implementation plan supplied in the conversation on 2026-10-10, with its decisions and gates preserved below. The complete source is the user message headed “LINE v3 交易整合與兩本相簿實機 E2E 計畫”.

## Goal and current evidence

Adopt the v3 service as the only canonical writer, preserve schema-2 history through an approved schema 2→3 migration, and prove two different, previously unverified LINE albums through separate cap=1 lifecycles. The first album must reach verified content and state readback before the second begins. Between them, prove a real bounded scroll, continuous catalog identity, ordered overlap, and a newly visible eligible album. A menu candidate, a single album, fixture tests, or a download without state commit cannot satisfy the full goal.

The user-supplied plan reports the previous base as `faf5b298cf563b87baa5adf2ba9cc651a8739991`, canonical schema-2 revision 34, two historical VERIFIED records, null owner/context lock, and the 65-photo destination empty. At implementation start HEAD is its direct child `7035809c695dd7410bc919ed791914137c87174a` (“建立 LINE 相簿 v3 批次備份基礎並封鎖舊 writer”, 2026-10-10 14:52:53 +08:00). The state and config hashes match the prior report. This newer committed v3 foundation is retained; it is not rewritten or treated as a test result.

The prior report proves only menu observation and candidate geometry. It records zero Save All dispatches, zero confirmations, zero downloads, no state mutation, and no second-album scroll. Its candidate geometry used manually checked anchors and did not preserve raw CUA screenshot bytes; neither fact is promoted to automatic live evidence.

## Frozen decisions and authority

- Use v3 Store/Service as the unique production writer. Migrate the existing state exactly from schema 2 revision 34 to schema 3 revision 35 after offline gates and source freeze. Preserve original bytes, history, large integer mtimes, and every unrelated config/photo/worktree item.
- Separate a structured, source/config-bound execution grant from post-run independent Acceptance. A null Acceptance reference is permitted during execution; Acceptance remains a required closure gate.
- Check the exact mutation operation on every Store mutation. Separate fixture authority from live authority; fixtures cannot dispatch LINE actions.
- Keep `max_albums_per_run=1`; the two targets use separate lifecycles. The authorization covers at most two Save All dispatches, two chooser confirmations, and 1,000 additional reversible GUI invocations. Prior unknown counts remain UNKNOWN and earlier attempt history is not reset.
- Admit the full catalog with fresh source bindings, affirmatively grounded top and bottom, same-session identity, ordered overlap, and final catalog drift checks. A live input still needs a capture request no older than five seconds.
- Preserve intent as the at-most-once barrier. Unknown dispatch is reconciled read-only and never resent. VERIFIED, evidence, registry update, and owner/context release commit together through the approved CAS/readback path.
- Use documented CUA for every LINE input. Keep raw CUA bytes, native ScreenCaptureKit bytes and metadata, AX, Vision OCR, mappings, manifests, timestamps, hashes, and each provider identity separately. Automatically derive at least three unique distributed anchors; require max residual ≤2 source pixels, uncertainty ≥2 pixels, safe margin ≥ uncertainty+4 pixels, and an actionable intersection ≥16×16 pixels.
- Each native scroll is ≤0.25 viewport height and must have before/action/after evidence, collection continuity, ordered complete-card overlap, and a new full eligible candidate. If layout cannot support the proof after an evidenced reversible window adjustment and fresh rebinding, stop the scroll gate.
- Keep historical catalog validation distinct from live input freshness. Use `originalObservedDispatch`: commit/read back intent, consume one session token, then one uninterrupted ellipsis → native capture/menu guard → unique Save All → post-state sequence. A loaded intent never creates a token.
- Plan Review is explicitly waived by the user and is recorded as a waiver, never a PASS. Independent post-implementation Acceptance remains required. The v4.8 controller cannot directly represent this direct-to-IMPLEMENT route for a CRITICAL task; therefore native stage admission is `NOT_RUN`, and the task uses a deterministic local handoff with byte-identical contract copies. Do not invent a controller receipt or platform identity.
- Product edits are serial at the root (`max_parallel_writers=0`). Up to three read-only helpers are allowed; three actual read-only audits were used for transaction, sensor, and packet inspection. They did not write product files.

## Scope and implementation order

1. Preserve current HEAD, branch, index tree, full status listing, existing tracked diffs, ignored/untracked work, source hashes, state/config hashes, existing destination identity/inventory, and previous report hash. Keep old task packages and receipts byte-for-byte unchanged.
2. Build this new task-local package, record authorization, waiver, exact handoff copy, attempts, source inventory and all new evidence here.
3. Complete offline v3 integration and hermetic fixtures. Fix `other_entries` producer/fixture values to arrays without changing the frozen schema; assert missing-lock error codes and no side effects. Bind new fixture helpers, config, decoder and outputs to this package. Complete exact operation grants, per-mutation authorization, cumulative two-action cap, dispatch/chooser bridge, scroll evidence and two separate cap=1 lifecycle coverage.
4. Run the Python transaction/authority/project-binding/catalog/content tests, Node CUA adapter tests, and Swift sensor/Vision/ImageIO build/tests with the approved SDK/toolchain. Preserve argv, environment, stdout/stderr, exit code, hashes, and each failure/attempt. Do not migrate state before offline gates and a frozen source digest pass.
5. Recheck revision 34, hashes, history, lock and ownership. Preserve original state bytes, migrate once to revision 35 via the existing lock/CAS, then read back and prove only `schema_version`, `revision`, and `active_batch=null` changed.
6. Before any LINE foreground input, tell the user the exact target app/surface and single next action. Wait for the user's explicit handoff. Refresh and affirm group, Albums surface, process/window/session/layout, catalog and geometry. If foreground is taken back, stop input and rebind from a new capture after a new explicit handoff.
7. Run the first cap=1 album lifecycle to final verified files, state readback and release. Then re-admit the catalog, perform and prove an actual bounded scroll to a different eligible album, and run its complete independent cap=1 lifecycle. At every uncertain dispatch, stop and retain the barrier.
8. Update `E2E測試報告.md` with exact step order, tools/commands/source excerpts, expected and observed results, state deltas, side effects, hashes, attempts, unknowns and evidence paths. Have a non-contributor perform independent Acceptance on the merged result and raw evidence; then hand the report to the Planner if a Planner channel exists. If unavailable, record that handoff as incomplete.
9. Only after applicable gates and Acceptance, create the exact staged snapshot, run the named checks and `git diff --cached --check`, confirm private origin/branch, commit, push, and read back local/remote identities. Preserve all unrelated dirty and untracked work. A remote drift stops push and leaves the local commit intact.

## Gates

Each gate freezes its owner, phase, evidence source, goal criticality, evidence role, closure gate, and reuse in `plan-contract.json`. The extended fields `baseline_rule`, `failure_routing`, and `waiver_allowed` are recorded in `gate-policy.json`.

| Gate | Pass condition |
|---|---|
| G_AUTH | Correct root, execution grant, source/config binding, ownership, duplicate checks and legacy fence |
| G_OFFLINE | Actual CLI/service regression and fault tests pass on hermetic task data |
| G_MIGRATION | Exact revision 35 readback; only three authorized field changes; all history preserved |
| G_CATALOG | Complete admission, continuous ordered overlap/boundaries, and identical final catalog identities |
| G_MENU | Fresh native source, automatic anchor mapping, source-pixel residual/margins, safe row and no-command closure |
| G_FIRST | One dispatch/confirmation at most, complete files, VERIFIED/readback/release for first fingerprint |
| G_SCROLL | Actual bounded scroll after first release, continuity, full ordered overlap, new full eligible candidate |
| G_SECOND | Different fingerprint completes its own cap=1 transaction and release |
| G_PRESERVE | Old records/photos/config and unrelated preexisting work match baseline; only authorized deltas |
| G_REPORT | Complete report with every claim linked to workspace evidence and hashes/reproducible IDs |
| G_ACCEPTANCE | Independent non-contributor reviewer returns explicit PASS after merge |
| G_DELIVERY | Exact staged snapshot; checks pass; private remote and local/remote commit readback agree |
| G_PLAN_REVIEW_WAIVER | User's explicit waiver is recorded; review remains WAIVED/NOT_RUN, never PASS |

G_PRESERVE uses `BASELINE_DELTA`; all other outcome gates are `HARD_CLEAN`. Safety, content and scroll requirements cannot be waived. `NO_ELIGIBLE_TARGET`, `SCROLL_TEST_NOT_RUN`, catalog drift, unresolved intent, or a failed commit/readback remain partial/blocked, not DONE.

## Stop rules and attempts

Stop dependent action on foreground interruption, identity/mapping/scroll UNKNOWN, state drift, unexpected destination contents, unresolved intent, uncertain chooser or any unapproved side effect. Never delete or overwrite existing data. Download polling is read-only: five-second intervals, three identical inventories, up to 600 seconds, exact expected count, zero-byte/partial/unknown entries at zero, full ImageIO decode of every image, and unchanged inventory after decode. Never enter LINE after download starts.

The same root issue has at most three evidence-bearing attempts; two consecutive attempts without new information require escalation. Preserve existing attempt history and unknown counts. Record every attempt and what it taught us in `attempt-ledger.json` and the final report.

# Evidence index

- `authorization.json`: exact user scope, locked decisions, review waiver and quantity limits.
- `plan-review-waiver.json`: format-1 explicit user waiver bound to the contract hash; waiver is not a Plan Review PASS.
- `plan-contract.json` and `handoff.json`: deterministic copies; their raw SHA-256 values must match.
- `gate-policy.json`: baseline, failure routing and waiver rules not expressible in the v3 gate schema.
- `baseline/baseline.json` and files beside it: branch/HEAD/index, full pre-task status, existing diffs, state/config/destination identity and prior report hash.
- `native-admission.json`: native controller admission is NOT_RUN, with the exact routing reason and honest platform limits.
- `evidence/`: command invocations and outputs, original screenshots/manifests/OCR, hashes, offline results and live transaction evidence.
- `attempt-ledger.json`, `E2E測試報告.md`, `results/implementer.result.json`: convergence, E2E evidence and final role handoff.

The immutable v4.8.0 release and the user-selected implementation prompt are outside the project root at `/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source/` and `/Users/hsiaojohnny/.codex/prompts/v4.8.0/04_implement_prompt.md`. The release was verified; native admission remains NOT_RUN.
