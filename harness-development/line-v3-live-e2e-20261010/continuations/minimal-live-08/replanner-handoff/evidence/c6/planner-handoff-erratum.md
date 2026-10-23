# c6 Planner handoff erratum

This separately versioned correction supersedes only the owner-release/return-to-list ordering and frame/grant key-count wording in `planner-handoff-c6.md` and the current-status prose derived from it. Preserve the original handoff and the schema-validated c6 candidate result unchanged. The c6 outcome remains BLOCKED with no gate PASS.

The earlier statement that the owner must remain held until after returning to the album list is wrong. The frozen project constitution requires the first album transaction to be verified, read back, and released before returning to the list and performing the required bounded scroll. The corrected future plan sequence is:

1. Finish the first transaction and verify its exact full catalog/state result. The admitted catalog and original session may be used for that final check only while the actual catalog age is at most 600 seconds and the existing service validation passes. Do not refresh timestamps or substitute a later catalog to make expired evidence appear fresh; on expiration or drift, preserve a typed stop.
2. Release the first owner after the successful finish/readback.
3. Then reacquire fresh detail/back/list observations, perform the real bounded 0.25-view-height scroll, and capture post-scroll evidence proving surface/window continuity, ordered overlap and a new eligible card before starting the second transaction.

This is a Planner proposal based on existing source behavior, not an observation of live LINE behavior or an implemented fix. Relevant frozen-constitution order is in the repository `AGENTS.md`, section “LINE 相簿 E2E 的必要證據與順序”. Source references: `src/line_backup_batch/observations.py` lines 609 onward (SHA256 `db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587`), `src/line_backup_batch/service.py` lines 563 onward (SHA256 `54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6`), and this Q's `live_runner.mjs` lines 465–512 and 552–573 (SHA256 `a20d37fe3c57d40bcff49c7afcd885898d1ada06ee9e6ff44b6dfb5be7d83dbd`). The JS order is finish-catalog drift check, release owner, return from the first lifecycle, then prepare and perform the post-release scroll.

The 17-count applies only to public frame keys. The V2 grant key set remains unchanged, but it is a separately defined set and must not be described as 17 keys.

No product source, grant, quota, owner, state, issue, result, or gate was changed by this erratum. `planner-handoff-c6.md` remains historical evidence and is non-authoritative for these corrected details. Use `planner-handoff-c6-post-return.md` as the current compact Planner packet.
