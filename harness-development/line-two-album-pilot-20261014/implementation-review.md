# LINE two-album pilot implementation review

This is the non-GUI implementation candidate for the CAP1_SEQUENTIAL design approved in [PR #9](https://github.com/s9008129/Line_backup/pull/9), exact design HEAD `cd9acdaa8e90b05e5430300106b560200fac263d`. The [Chief review](https://github.com/s9008129/Line_backup/pull/9#issuecomment-6169285475) approves the design only. Independent review of this implementation is still required.

The Owner expressly attested authority over the user-maintained project execution/release policy and authorized a new bounded `LINE_TWO_ALBUM_PILOT/1` scope. [The profile](../../policies/line-two-album-pilot-v1.json) accepts genuine Owner-transferred external independent PR review for this scope. Sol plans and orchestrates; Luna implements; ChatGPT remains the External Independent Chief Reviewer. No signed native receipt, Controller admission, model/session/nonce metadata or physical delivery guarantee is claimed. The profile authorizes non-GUI engineering now; it grants no current LINE capture or input consent.

The four source files implement a separate project grant, single-candidate bounded admission, durable global GUI reservations, and scoped navigation/calibration/receipt behavior. The bounded entry connects two independent cap1 lifecycles under one workflow owner. A must be VERIFIED, read back, CLOSED, stopped and released before C1 navigation or B admission. The configured cap stays one. B must differ from A and be a complete eligible card exposed by a verified post-A downward scroll. B receives its own lease, Save All intent and verification commit.

The fixed 23 logical input slots comprise nine per album, one return action, and four shared scroll slots. Reservations are durable before input and are never refunded. Restart, changed run identities, UNKNOWN results and ledger loss do not create a retry permission. The initialization receipt is created exclusively before the ledger; missing or unsafe retained records fail closed. These are cooperative filesystem/code safeguards, not proof of OS immutability or physical native exactly-once delivery.

Each scroll uses `app.scroll(freshViewportTarget, "down", 0.25)`. The checker compares retained PNG pixels inside the grounded viewport, retained raw AX binding, ordered adjacent suffix/prefix complete-card overlap, upward displacement beyond mapping uncertainty, and a newly visible complete card. It rejects unchanged pixels, reversed movement/order, nonadjacent overlap and missing new cards. Discovery is bounded and never asserts a complete catalog.

Calibration2 retains the prior menu identity, applicability, geometry and closure evidence. The final scoped atomic menu pair performs one original ellipsis invocation, a bounded wait and one Save All invocation. Receipt3 records that actual sequence and references calibration2; it does not invent a dispatch-time `SCK_MENU_GUARD_PASS`. Existing receipt1/2 meanings remain separate. Capture timestamps remain anchored to the original request start; retained or analyzed frames are not made newer by later processing.

The project runtime validator requires exact source/config/entry/producer/decoder bindings and concrete hashed sources covering the controlled host callbacks. Missing callback sources remain a live-readiness blocker. This PR does not establish actual hosted callback bindings, permissions, retained live evidence or current foreground ownership. Hosted retry/native duplicate-delivery guarantees remain UNKNOWN; the Owner-approved pilot evaluates logical at-most-once controls with that residual risk visible.

Existing relevant Mac working-tree changes in the four source files and selected tests were carried into an isolated implementation branch. Unrelated dirty/untracked work, including the separate local observation-normalization change, stays in the original workspace. No Harness V4.8.0 resource, PR #8, ML08/c6 history, original PR #9 artifact, production config/state or historical photo/intent was edited by this implementation workflow.

The Owner should transfer the implementation PR's exact HEAD to ChatGPT for independent source review. Only after that review, complete private runtime bindings, actual permissions/budgets, unresolved-intent checks and one explicit foreground/GUI-consent handoff may the live pilot begin. Its acceptance still requires two genuinely new LINE albums saved and fully verified without human intervention between them. Fixture and synthetic results below are engineering enablers; real LINE E2E is NOT_RUN.

Focused validation uses the five existing modules: `test_batch_authority`, `test_batch_lifecycle`, `test_batch_observations`, `test_batch_coordinator`, and `test_cua_adapter.mjs`. The Python subprocess checks now derive dependency search paths from the installed modules, so the fixture subprocess does not drop jsonschema dependencies. The original 11/12 failure record remains unchanged (SHA256 `78a96222a254d905d1774b30be4ed5e81959066749cd49d2d44bc437d7d3ac10`).

The pinned ImageIO decoder is unchanged (SHA256 `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`). Its initial isolated-checkout failures and the rejected `/tmp` alias workaround remain in private evidence. Moving the same worktree to a normal directory resolved the environment issue; no decoder, canonical-root guard, production path or original Task was changed.

The durable Store test consumes all 23 fixed slots, reopens Store across fixture-controlled A/C1/B phases, and rejects a 24th reservation. Its phase setup is synthetic; it does not prove real A release or real C1 evidence. The existing lifecycle and finalize fence tests separately exercise cap1 release and full decode/atomic VERIFIED/readback behavior. The Node entry tests exercise one and three pre-A scrolls, mandatory post-A scroll, duplicate-first-B exclusion and final receipt3 payload assertions with external mocked I/O.

The actual project grant validator, callback-source drift/missing-source refusal, nonfixture Store write path, and Service calibration2 acceptance are exercised with isolated fixture files. Only the installed-root boundary is adapted for that fixture authorization test. Receipt3 Service tests verify schema/calibration references/event ordering/times/reservation outcomes through rejection paths. **A fully accepted Service receipt3 dispatch with all five valid chooser phases and filesystem download evidence is not verified.** The Node receipt3 assertions do not erase that coverage limit.

All original raw failures and final stdout/stderr/exit records stay private and excluded from Git. Final log hashes below identify retained outputs, including empty streams. The single skipped Python case requires frozen historical operator source absent from the isolated checkout; that case is not reported PASS. No dependency installation, native rebuild, LINE capture, scroll, click, Save All or production state write was performed.

Final fixed-source results: **Python 67 tests: 66 PASS, 1 SKIP, 0 FAIL; Node 29/29 PASS; both exit 0.** Python module counts are authority 31, lifecycle 1, observations 18 and coordinator 17.

Reproduce the focused selection using the existing fixture task and installed dependency directory through environment variables (no personal path is published):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:$PWD/tests:$DEPENDENCY_DIR" LINE_BACKUP_BATCH_TASK="$PWD/harness-development/line-v3-live-e2e-20261010" python3.13 -B -m unittest -v test_batch_authority test_batch_lifecycle test_batch_observations test_batch_coordinator
node --test tests/test_cua_adapter.mjs
```

The existing fixture decoder binding must point at the unchanged local pinned binary. Test on a canonical directory path; preserve the real project root and never substitute production config/state for fixtures. This test selection was actually run locally; a fresh remote clone still needs that existing macOS fixture/decoder/dependency setup.

| Affected source/policy/test file | Bytes | SHA256 |
| --- | ---: | --- |
| `src/line_backup_batch/cli.py` | 32128 | `9ae480cf464a0bbcfedfe19121858452fcb137b9fbbfaad26da7823941c6938c` |
| `src/line_backup_batch/service.py` | 63687 | `c8cd95bc57ecc9ec4501862a166d6d0abffa1af433c6f939910727d5a75c599b` |
| `src/line_backup_batch/store.py` | 54777 | `7c4b430ffb00aa85591485f65c9ba63fe9d3b14c0653c88ac29312e6b07a17a5` |
| `scripts/line_backup_cua_adapter.mjs` | 61296 | `b38333e48e178156e095f2fcfe42ad089bad98d8d2ede256f38312363544d9f5` |
| `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs` | 16225 | `d70396fe83cd92fccc8191254c09fe5592a7391d2a55c245ff521e4f15dfcb1a` |
| `tests/test_batch_authority.py` | 38963 | `028720c593ee254e063df8d95e8c95e3637c10ebcbd221516f09ecf40abd83bc` |
| `tests/test_batch_coordinator.py` | 21416 | `ab22bce2561a22c6ccf7a76fd0118188db4597032a5a9e0c974cce9dce564476` |
| `tests/test_batch_observations.py` | 20037 | `5d20a2fa7a2291a4613716b593c4d1659a5ae163f81b6de7c3806352e61a5d3f` |
| `tests/test_cua_adapter.mjs` | 37433 | `51c85a889252c2f82aa998002c97f84987549840061bd6d73a3fc50c77fce3fb` |
| `policies/line-two-album-pilot-v1.json` | 3160 | `59d94b72f4fd59d829b56d21a494c9d83c6b91eb2513c15795a58021194a39e9` |
| `AGENTS.md` | 6729 | `0b1dbb0fcff342417950a205f42da96a0acb94786609b0c29b5b42cc78cd9fe8` |

| Retained final output (private) | Bytes | SHA256 |
| --- | ---: | --- |
| `final-authoritative-python-03.stdout` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-authoritative-python-03.stderr` | 10458 | `7ff7215d02529a3bfcad7474500e1123746b697eca1aab9d00a3293bf2362209` |
| `final-authoritative-python-03.exit` | 1 | `5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9` |
| `final-authoritative-node-03.stdout` | 2516 | `d8fcd9af327882ff65485c9c34209cd8a8ce6bbef406621a418575a937408a3f` |
| `final-authoritative-node-03.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-authoritative-node-03.exit` | 1 | `5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9` |

Preservation readback checked 253 original workspace files, including 239 historical backup photo files: unchanged. Original workspace HEAD/index/diff and production config/state are unchanged. Private evidence, grants, mappings, raw captures and photos are excluded from this PR. Harness V4.8.0 is unchanged; native Controller admission is NOT_CLAIMED; current GUI consent is NOT_GRANTED; LINE GUI actions are 0.
