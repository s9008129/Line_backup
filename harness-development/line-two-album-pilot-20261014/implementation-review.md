# LINE two-album pilot implementation review

This candidate addresses the two required findings from the [PR #10 Chief review](https://github.com/s9008129/Line_backup/pull/10#issuecomment-6175844888) of HEAD `5ea2dd221a400c0dc44010c66796aa59f588fd55`. It remains a non-GUI implementation awaiting independent source acceptance. The approved CAP1_SEQUENTIAL design in [PR #9](https://github.com/s9008129/Line_backup/pull/9), HEAD `cd9acdaa8e90b05e5430300106b560200fac263d`, is unchanged; its [approval](https://github.com/s9008129/Line_backup/pull/9#issuecomment-6169285475) is design only.

The Owner-attested [LINE_TWO_ALBUM_PILOT/1 profile](../../policies/line-two-album-pilot-v1.json) remains the separate project route for non-GUI engineering and genuine manually transferred external independent PR review. Sol orchestrates, Luna implements, and ChatGPT remains the External Independent Chief Reviewer. No native Controller receipt, signed provenance, model/session/nonce attestation or current GUI consent is claimed. This repair changes no policy or Harness release resource.

Fix A's root cause was capture-ordinal checkpoint naming: a fresh counter key let repeated observations of the same logical stage avoid that stage's two-attempt limit. The adapter and bounded entry now name the album, workflow phase and observation purpose explicitly. Store accepts only the fixed stage namespace, checks the A/C1/B phase and album, and persists the same key for initial capture and its single recapture. A third attempt fails before capture. A fresh adapter/session, CLI process or run identity cannot generate a fresh counter for that logical stage. Distinct legitimate stages retain separate counters; the global paired-observation ceiling remains 80. Existing ordinal keys fail closed on ledger read; this repair does not migrate or rewrite old ledgers. Observation reservations neither consume/refund input slots nor grant permission to replay an intent.

Fix B's root cause was missing positive integration coverage. The reviewed HEAD's green Node flow used a mocked CLI bridge, while Python receipt3 tests stopped at rejection paths. One new representative fixture now invokes the copied, unmodified production CLI in fresh subprocesses, without `--fixture`, authorization/root/module patches or receipt-validator mocks. It exercises project authorization, Store reservations/CAS, bounded admission, calibration2, a distinct fresh original-intent frame, receipt3, all five chooser phases, actual filesystem download evidence, `Service.dispatch`, the unchanged pinned ImageIO decoder, `Service.finalize` and exact state receipt readback. Its config and authorized lifecycle limits are both one. No Service, CLI, observation-validator, content-verifier or schema change was needed to make this chain pass.

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

Final frozen-source results: **Python 69 tests: 68 PASS / 0 FAIL / 1 SKIP; Node 30 tests: 30 PASS / 0 FAIL / 0 SKIP; both exit 0.** Python module totals are authority 33, lifecycle 1, observations 18 and coordinator 17. The historical skipped case still needs frozen operator source absent from the isolated checkout and is not counted PASS. The earlier reviewed baseline was 66 PASS / 1 SKIP across 67 Python tests and 29 Node PASS; it is preserved as prior evidence, not the current result.

The actual final selection used Python 3.13 and the existing local fixture/decoder/dependency setup. Portable command forms are:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:$PWD/tests:$DEPENDENCY_DIR" LINE_BACKUP_BATCH_TASK="$PWD/harness-development/line-v3-live-e2e-20261010" python3.13 -B -m unittest -v tests.test_batch_authority tests.test_batch_lifecycle tests.test_batch_observations tests.test_batch_coordinator
node --test tests/test_cua_adapter.mjs
```

Use a canonical macOS checkout path and the existing pinned decoder binding; do not substitute production state/config. No dependency installation or native rebuild was performed. The unchanged decoder SHA256 is `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`.

The repair changes only Store, adapter, bounded entry, the two relevant existing test modules and this review document. The other approved source/test/profile files remain at their reviewed bytes. Exact current hashes are:

| Source/test file | Bytes | SHA256 |
| --- | ---: | --- |
| `src/line_backup_batch/cli.py` (unchanged) | 32128 | `9ae480cf464a0bbcfedfe19121858452fcb137b9fbbfaad26da7823941c6938c` |
| `src/line_backup_batch/service.py` (unchanged) | 63687 | `c8cd95bc57ecc9ec4501862a166d6d0abffa1af433c6f939910727d5a75c599b` |
| `src/line_backup_batch/store.py` | 55902 | `6b811edda0e5e0738ba0b36e3c2f73274dfb022a5f75f3e20092750e5fdb2beb` |
| `scripts/line_backup_cua_adapter.mjs` | 62206 | `238eae053f4dc61a89484783b2203ddb3afae1c3227406d47aa005a74590f00b` |
| `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs` | 16436 | `5eb23bcc95b0249ff5eb3ead91d17e7b0647f8bbfd9d59daa16a6ef6057df30a` |
| `tests/test_batch_authority.py` | 77255 | `8e97c5f1de143c5dc63e0966115e0424e7f2ceca97e305de30516b7c71449896` |
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
