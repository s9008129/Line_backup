# LINE two-album pilot implementation review

This candidate addresses the single history-scoping finding from the [final PR #10 Chief review](https://github.com/s9008129/Line_backup/pull/10#issuecomment-6180046394) of HEAD `976dae00fbcc982e614d878df9f53c997e9f6e08`. That review ACCEPTED the previous checkpoint and positive non-GUI receipt3 corrections described below; they were not redesigned. It remains a non-GUI implementation awaiting independent source acceptance. The approved CAP1_SEQUENTIAL design in [PR #9](https://github.com/s9008129/Line_backup/pull/9), HEAD `cd9acdaa8e90b05e5430300106b560200fac263d`, is unchanged; its [approval](https://github.com/s9008129/Line_backup/pull/9#issuecomment-6169285475) is design only.

The Owner-attested [LINE_TWO_ALBUM_PILOT/1 profile](../../policies/line-two-album-pilot-v1.json) remains the separate project route for non-GUI engineering and genuine manually transferred external independent PR review. Sol orchestrates, Luna implements, and ChatGPT remains the External Independent Chief Reviewer. No native Controller receipt, signed provenance, model/session/nonce attestation or current GUI consent is claimed. This repair changes no policy or Harness release resource.

Fix A's root cause was capture-ordinal checkpoint naming: a fresh counter key let repeated observations of the same logical stage avoid that stage's two-attempt limit. The adapter and bounded entry now name the album, workflow phase and observation purpose explicitly. Store accepts only the fixed stage namespace, checks the A/C1/B phase and album, and persists the same key for initial capture and its single recapture. A third attempt fails before capture. A fresh adapter/session, CLI process or run identity cannot generate a fresh counter for that logical stage. Distinct legitimate stages retain separate counters; the global paired-observation ceiling remains 80. Existing ordinal keys fail closed on ledger read; this repair does not migrate or rewrite old ledgers. Observation reservations neither consume/refund input slots nor grant permission to replay an intent.

Fix B's root cause was missing positive integration coverage. The reviewed HEAD's green Node flow used a mocked CLI bridge, while Python receipt3 tests stopped at rejection paths. One new representative fixture now invokes the copied, unmodified production CLI in fresh subprocesses, without `--fixture`, authorization/root/module patches or receipt-validator mocks. It exercises project authorization, Store reservations/CAS, bounded admission, calibration2, a distinct fresh original-intent frame, receipt3, all five chooser phases, actual filesystem download evidence, `Service.dispatch`, the unchanged pinned ImageIO decoder, `Service.finalize` and exact state receipt readback. Its config and authorized lifecycle limits are both one. No Service, CLI, observation-validator, content-verifier or schema change was needed for that accepted receipt3 correction. The current correction changes only Service admission/history scoping; receipt validation remains intact.

The successful chain is:

`NEW_INTENT_COMMITTED` (actual result `ORIGINAL_INTENT_COMMITTED`) → `RECEIPT3_ACCEPTED` / `DOWNLOAD_STARTED` → `FILES_VERIFIED` → `FINALIZE_VERIFIED` → `EXACT_STATE_READBACK` → `NO_REPLAY`.

The fixture creates retained synthetic PNG/AX/OCR/geometry/manifest/classifier/support records conforming to the normal validation contracts, plus a valid newly created PNG in its isolated destination. These are explicitly synthetic records, including their provider-shaped fields; they are not real native captures, reviews, permissions or delivery receipts. Finalize runs actual ImageIO decode, hashing, stability and atomic verification code. The resulting VERIFIED inventory hash matches the fixture image and the returned state receipt equals a new Store snapshot. Calibration retains its original frames/times; the committed intent uses a separate fresh detail frame; chooser evidence preserves its original capture/action timestamps and original-context binding. Receipt3 contains no dispatch-time `SCK_MENU_GUARD_PASS`.

The same CLI fixture reserves one paired checkpoint before begin and again after begin in a new process, then observes `PROJECT_CHECKPOINT_RECAPTURE_QUOTA` on the third request; the durable count remains two. Store tests separately reopen across synthetic run identities, preserve distinct stage budgets, reject wrong album/ordinal keys and reject a retained legacy ordinal ledger. Node tests confirm explicit purpose keys reach the bridge and the bounded entry across A/C1/B.

The positive fixture also reaches these actual negative-control refusals through the copied CLI:

| Control | Observed refusal |
| --- | --- |
| Missing receipt3 | `RETAINED_RECEIPT_REQUIRED` |
| Altered receipt3 schema / forbidden legacy support field | `INVALID_DISPATCH_RECEIPT` |
| Missing or unconsumed reservation | `GUI_LEDGER_STATE` |
| Replaced download evidence reference | `INVALID_DOWNLOAD_EVIDENCE` |
| Incorrect chooser phase order | `CHOOSER_PHASE_ORDER` |
| Incorrect event order | `RECEIPT_EVENT_ORDER` |
| Invalid timestamp | `RECEIPT_EVENT_TIME` |
| Future event timestamp | `RECEIPT_EVENT_TIME_ORDER` |
| Capture older than its action boundary by more than five seconds | `CHOOSER_PHASE_STALE` |
| Incorrect destination | `CHOOSER_DISPATCH_BINDING` |
| Replacement image at the recorded path | `DOWNLOAD_FILE_CHANGED` |
| Second dispatch of the committed intent | `DISPATCH_ALREADY_RECORDED` |

For the replacement-image control, the original file is moved aside and restored with its original inode/mtime; no capture timestamp is renewed. The existing Store restart test retains its outstanding-RESERVED refusal (`PROJECT_UNKNOWN_RESERVATION`), then consumes UNKNOWN and verifies a reopened Store refuses new dispatch reservation (`PROJECT_WORKFLOW_HALTED`). These isolated ledger unit tests adapt authorization setup; the new full CLI success/negative path does not. Existing tests still cover missing-ledger initialization refusal, all 23 globally unique durable slots and a 24th refusal, no loaded-intent replay, cap1 lifecycle release, duplicate exclusion, atomic VERIFIED fences, and rejection of unchanged images, reversed order/movement, nonadjacent overlap and missing new cards. The all-23-slot test sets A/C1/B phase evidence synthetically; real autonomous release/navigation/scroll is not claimed.

Fixture construction initially exposed incorrect event timing, reservation ordering, artifact path/support bindings and a selected-frame geometry/manifest mismatch. Those fixture records were corrected; no production safety validator was weakened. All original raw attempt outputs remain private. The first positive attempt log has SHA256 `db5779b3884390e292306c2845493c2072f74de5192a6aeb9f751a3a3ff46f59`. The first combined Python run also exposed an accidental `project_cli` NameError in an older calibration test; its existing boundary-adapted route was restored. That failed output remains preserved with SHA256 `d2ff723d3c2c4bf9ea08a8b00b967c5e5136ffc8c09d26bf1449aae18ce8b28d`. The prior 11/12 subprocess dependency failure record remains unchanged (SHA256 `78a96222a254d905d1774b30be4ed5e81959066749cd49d2d44bc437d7d3ac10`).

Previously accepted HEAD `976dae00fbcc982e614d878df9f53c997e9f6e08` results: **Python 69 tests: 68 PASS / 0 FAIL / 1 SKIP; Node 30 tests: 30 PASS / 0 FAIL / 0 SKIP; both exit 0.** Python module totals are authority 33, lifecycle 1, observations 18 and coordinator 17. The historical skipped case still needs frozen operator source absent from the isolated checkout and is not counted PASS. The earlier reviewed baseline was 66 PASS / 1 SKIP across 67 Python tests and 29 Node PASS; it is preserved as prior evidence, not the current result.

The actual final selection used Python 3.13 and the existing local fixture/decoder/dependency setup. Portable command forms are:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:$PWD/tests:$DEPENDENCY_DIR" LINE_BACKUP_BATCH_TASK="$PWD/harness-development/line-v3-live-e2e-20261010" python3.13 -B -m unittest -v tests.test_batch_authority tests.test_batch_lifecycle tests.test_batch_observations tests.test_batch_coordinator
node --test tests/test_cua_adapter.mjs
```

Use a canonical macOS checkout path and the existing pinned decoder binding; do not substitute production state/config. No dependency installation or native rebuild was performed. The unchanged decoder SHA256 is `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`.

The previously accepted repair changed Store, adapter, bounded entry and two test modules. The current history correction changes only Service, the three necessary existing Python test modules and this existing review document. Store, schema, CLI, adapter, entry and profile remain at their accepted bytes. Exact current hashes are:

| Source/test file | Bytes | SHA256 |
| --- | ---: | --- |
| `src/line_backup_batch/cli.py` (unchanged) | 32128 | `9ae480cf464a0bbcfedfe19121858452fcb137b9fbbfaad26da7823941c6938c` |
| `src/line_backup_batch/service.py` | 65259 | `1697155718c2c4b69a7cae72473fb95253b7fbc2a90310f8107a235cd61d5339` |
| `src/line_backup_batch/store.py` | 55902 | `6b811edda0e5e0738ba0b36e3c2f73274dfb022a5f75f3e20092750e5fdb2beb` |
| `scripts/line_backup_cua_adapter.mjs` | 62206 | `238eae053f4dc61a89484783b2203ddb3afae1c3227406d47aa005a74590f00b` |
| `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs` | 16436 | `5eb23bcc95b0249ff5eb3ead91d17e7b0647f8bbfd9d59daa16a6ef6057df30a` |
| `tests/test_batch_authority.py` | 88060 | `e13b634739780becf3ae5b75e3d4d19de2123929ec91fa42fb0decc2e0674886` |
| `tests/test_batch_lifecycle.py` | 3066 | `8b67038e9eb54fc03674e4027a111eca0cf79782dfd9b91583e118c179eb2e66` |
| `tests/test_batch_observations.py` | 19093 | `517ec7d7dc1423cd4227ac115f56b8fcc9e9fd4e41908a72576b01ac380fdb05` |
| `tests/test_cua_adapter.mjs` | 38659 | `5ffeda6bc3178bbb4f31ebd2d819d15e6607c7a75ab97db64b7b8db05c70c0a2` |

Actual final commands, stdout, stderr and exit records remain private. Hashes identify their exact bytes:

| Retained output | Bytes | SHA256 |
| --- | ---: | --- |
| `final-python-suites-02.argv` | 453 | `af330c01b636e1855cf703c8e11793876b0ca51852f80dccc4ddf7b0c08f8257` |
| `final-python-suites-02.stdout` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-python-suites-02.stderr` | 11250 | `df09f8088bf7be01f7f4577896193036a7549f9e09d2b951be6f04908d952d79` |
| `final-python-suites-02.exit` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `final-node-suite-02.argv` | 39 | `2a2017d8609cd8511122a6a83ed4d16347ae4d681d6edf648583265ae8a8d558` |
| `final-node-suite-02.stdout` | 2609 | `ac522816a0e2355eca05d939bc6d3b473c78bd8c5540b773273cbbe3efc32555` |
| `final-node-suite-02.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-node-suite-02.exit` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

Preservation readback checked 253 original workspace files, including all 239 historical backup photos, plus 172 frozen history/candidate files: unchanged. Original workspace HEAD/index/diff, production config cap1, the two historical VERIFIED entries and their state/intents remain unchanged. Harness V4.8.0, PR #8, ML08/c6 resources and consumed attempts were not modified. Generated fixture oracles and all private grants/mappings/captures/paths stay outside Git.

The next action is Owner transfer of the new exact PR #10 HEAD to ChatGPT for independent review. Source acceptance must precede separate Mac runtime preflight: exact source/build/config/producer/decoder/callback bindings, capture/retention and input budgets, permissions, unresolved-intent checks, and one actual Owner foreground/GUI-consent handoff. The supported future sequence remains A VERIFIED/readback/CLOSED/stop/release → automatic return → genuine bounded downward scroll with retained PNG/AX displacement and ordered complete-card overlap → distinct eligible B → its independent Save All and verification. Discovery never claims a complete catalog. No mid-run human calibration or selection is permitted for unattended acceptance.

**B03 physical host/native delivery: UNKNOWN. B05 native Controller provenance: NOT_CLAIMED. Mac runtime readiness: NOT_READY. Real LINE E2E: NOT_RUN. LINE GUI actions: 0.** Fixture PASS is an engineering enabler and does not establish actual native capture/delivery, autonomous navigation or either real download. This PR is not merged or deployed.

The final history compatibility correction removes the two `prior_intents` scans over every historical run. Both initial validation and the atomic state CAS callback now reread the existing validated, task/owner-bound project ledger and match its current lifecycle batch to the active batch. Lifecycle1/phaseA permits no workflow link, regardless of resolved historical intents. Lifecycle2/phaseB requires the current ledger's verified C1, current A run and first batch, A's VERIFIED registry readback/closed lease/intent owner, a distinct target, and the exact retained C1 path/SHA and scroll count. Existing duplicate, unresolved-history, writer, lease, quota, intent, CAS and stop checks remain. No Store/schema/state migration or new policy/platform is introduced.

Focused new evidence establishes:

- An isolated prior cap1 batch actually reaches VERIFIED with an intent through existing fixture coordinator/content verification APIs, releases, and remains in history. New authorized pilot A admits with no link; the historical fingerprint is refused with `BOUNDED_TARGET_INELIGIBLE`.
- Authorized A's two-card frame has neither catalog boundary. Its manifest contains exactly one selected identity, retains the full frame, and declares `BOUNDED_CANDIDATE_ONLY` / `complete_catalog=false`. Repeat admission remains refused with unchanged state. These previously reviewed assertions were preserved in the authorized test; the old observation test that mocked project scope without a grant now asserts ungranted admission fails closed instead.
- A fixture publish hook replaces the current lifecycle batch binding after prevalidation but before the real Store CAS callback. `BOUNDED_A_LIFECYCLE_BINDING` refuses atomic admission; receipt/state/manifest remain unchanged. The hook injects fixture interference and does not mock the validator.
- The accepted copied-CLI receipt3 positive path is retained, then its fixture A is stopped/released after VERIFIED/readback/CLOSED. Existing Store phase APIs consume synthetic return/scroll reservations, retain synthetic C1, and begin distinct same-owner cap1 B. Valid current linkage admits B; missing/foreign-owner links return `BOUNDED_WORKFLOW_LINK_INVALID`, stale first-batch linkage returns `BOUNDED_A_BATCH_RELEASE_REQUIRED`, and forged A run/C1 reference returns `BOUNDED_C1_LEDGER_BINDING`. The shared ledger remains at 11 of23 slots used across B begin/admission. The unchanged all23-slot regression separately proves full ceiling conservation and refusal beyond it.
- A fixture with retained unresolved SAFE_ABORT intent, and no active batch, still refuses new cap1 begin with `UNRESOLVED_HISTORY`. The empty active-batch field is fixture history setup, not a claim that production release/reconciliation is permitted. No historical intent is removed or rearmed.

The C1 observation/proof and input-consumption facts are explicitly synthetic fixtures. They test current linkage and budget retention, not physical scroll/delivery. B's live Save All/download/VERIFIED sequence is NOT_RUN. No actual historical photos or production state were used as writable fixtures.

Current final LOCAL regressions: **Python72:71 PASS /0 FAIL /1 historical SKIP; Node30:30 PASS /0 FAIL /0 SKIP; both exit0.** Module totals are authority35/lifecycle2/observations18/coordinator17. The historical skip is preserved. Actual commands were `python3.13 -B -m unittest test_batch_authority test_batch_lifecycle test_batch_observations test_batch_coordinator` with the existing fixture/dependency environment, and `node --test tests/test_cua_adapter.mjs`. The last test-only coverage-preservation change reran Python; unchanged Node bytes retain their actual final30/30 run. No GitHub CI execution or independent runtime acceptance is claimed.

Initial fixture/regression failures and all scoped negative outputs remain private. The initial combined run exposed the old unauthorized project-scope mock; its raw stderr remains SHA256 `dc9f94b1c5724d04e7ee2ff4693bf86ceca5c0c095d8bb4743521c1749bc0b52`. Positive bounded-discovery coverage was retained under actual fixture authorization. Exact current final output hashes follow; earlier output hashes above remain historical evidence.

| Current history-repair output (private) | Bytes | SHA256 |
| --- | ---: | --- |
| `final-python-03.argv` | 133 | `c7cc09d1ff553def8f079325ce5d27ab6c06698bf78ef5c2fc63f5d95fc18372` |
| `final-python-03.stdout` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-python-03.stderr` | 184 | `1aafbd6244e02a88657374bc2624efc753060c135ba15beef5dad0b693d3c9ea` |
| `final-python-03.exit` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `final-node.argv` | 39 | `2a2017d8609cd8511122a6a83ed4d16347ae4d681d6edf648583265ae8a8d558` |
| `final-node.stdout` | 2604 | `a27549dfc997d8bac2d2bce2d09d6cc2bed4acf0c52feeda5c0b5c69f3a17abe` |
| `final-node.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-node.exit` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

One bounded Mac production config/state inspection, with final byte-preservation readback, observed only these public aggregates:

| Read-only finding | Actual result |
| --- | --- |
| State schema / revision | 3 /35; schema validation PASS |
| `max_albums_per_run` | 1 |
| Historical runs / VERIFIED entries | 2 /2 |
| Historical completed batch intents | 0 |
| Unresolved or UNKNOWN intents | 0; recorded UNKNOWN intents including completed history also0 |
| Active batch / writer / context lock | absent /absent /absent |
| Unchanged begin/history predicates | no global history blocker found |
| Corrected first-lifecycle history assessment | safe to evaluate against current history; no target invented and no admission performed |
| Actual Mac source/build/callback/permission/retention bindings | NOT_READY; not established by this aggregate inspection |

The review's defect was conditional; the production probe does not claim an old completed batch-intent row was present on this Mac. Current absence does not substitute for the regression or authorize GUI. Public findings omit private group identities, album dates, filenames and paths. Original config/state bytes,253 workspace files including239 historical photos,172 frozen artifacts, and original HEAD/index/diff remain unchanged.

Next: return the new exact PR10 HEAD for final independent source review. After approval, advance directly to separate actual Mac source/build/config/callback/producer/decoder, permissions/capture/retention, private scope/unresolved-intent and foreground readiness; no further Harness design cycle is needed. Owner-managed bounded logical-at-most-once risk policy remains explicit. Physical delivery is UNKNOWN, native Controller provenance is NOT_CLAIMED, real LINE E2E is NOT_RUN, and LINE actions are0. No merge/deploy or production mutation was performed.
