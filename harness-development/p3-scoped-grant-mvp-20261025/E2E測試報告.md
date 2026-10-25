# P3 scoped grant MVP — implementation handoff

Task: `P3-SCOPED-GRANT-MVP-20261025`
Worktree: `implement/p3-scoped-grant-mvp`, base/HEAD at start `838a3650f9028fa2356c4b20ee8be931f03f2441`
Plan decision: external result `CONDITIONAL_APPROVE_FOR_IMPLEMENTATION`; this implementation review remains `NOT_DONE`.
Result: `PARTIAL` — offline preparation, trusted-signature verification interface, one-time attempt reservation, receipt verification seam, ImageIO completion/readback implemented. Production trust keys are not provisioned; live Save All and the CUA receipt bridge are not connected. No LINE GUI or Save All was run.

## What changed

- `src/line_backup_batch/p3.py` adds `prepare`, `reserve`, and `finalize`. `prepare` binds group UUID, foreground/history/Owner evidence references, album identity, canonical destination mount/device/inode, current implementation commit, complete source closure, runtime manifest and executable hashes, Swift decoder hash, grant UUID, nonce, issue time, one-dispatch limit, attempt scope, and optional album-recovery evidence.
- Production authority verification accepts only Ed25519-signed claims and retrieves role keys from fixed macOS Keychain service names. Owner, reviewer and runtime receipt roles must use distinct keys. OpenSSL verifies signatures. Missing key or verifier capability fails closed. Key provisioning is not present here; keychain enrollment still needs an independently controlled trust anchor before production authority can be asserted.
- `reserve` validates all bound material, filesystem canonicality and mount/inode identity, probes exclusive create/hard-link/fsync/flock/readback, then durably burns the nonce before creating one existing `DailyRecords.intent`. Crash/ambiguous reservation blocks replay. Its result is always `dispatch_authorized=false`.
- `finalize` accepts only a runtime-signed receipt bound to nonce, attempt, group, album, destination, runtime closure, one dispatch, and `DOWNLOAD_FINISHED`; it calls the existing ImageIO verifier, records the existing manual diagnostic completion, and reads state back. It does not update formal VERIFIED state.
- `daily.py` adds `p3-prepare`, `p3-reserve`, and `p3-finalize` routing. The CLI has no fixture-verifier or user-supplied-key option.
- The manual now states the P3 and trust-channel limitations. Private raw logs are under this task package's ignored `private/logs/` directory; `.gitignore` excludes them.

## Checks and actual results

All P3 fixtures use synthetic records and files. The signature test generates a temporary Ed25519 key, mocks only the Keychain public-key lookup, and calls the real installed OpenSSL verifier; an altered signature is rejected. The 51-image tests compile and execute the existing macOS ImageIO decoder against synthetic PNGs.

| Command | Result | Private raw log (SHA-256) |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests/test_p3_scoped_authorization.py` | exit 0; 15 tests OK | `private/logs/p3-focused.log` — `24858324d5ae98e83f3ae347b4bc1a66dcded1970740113ab267fe7613a13e11` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0; 19 tests OK | `private/logs/daily-records.log` — `8a62aecede624b7117452b6a444afefe7457b8bcef131cd4dc32f973c81d89d8` |
| `node --test tests/test_cua_adapter.mjs` | exit 0; 22 tests pass | `private/logs/cua-adapter.log` — `bee03b22b28a7bc0a82d5f50b5b8a24acb5d76a6f0bc3d442ae5ef5a43368e00` |
| `SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk swift test --package-path rev28` | exit 1; 334 tests, 17 failures | `private/logs/rev28-swift-tests.log` — `d3a396d33276978e12d026217e7cadbf07baca0e7af5772d55840ed26650d87d` |

The 17 Swift failures are in `ProjectBackupBindingTests`: the required `LINE_BACKUP_INSPECTION_FIXTURES` environment variable was absent (`XCTUnwrap` at test line 15). The other 317 Swift tests passed. The six-case fixture referenced by an older report was not present in this worktree, so the run was not repeated with guessed fixture data. The P3 tests separately compiled the existing Swift ImageIO decoder successfully and exercised 51-image positive/negative cases. Per-test PASS/FAIL names and the redacted failure summary are in [test-results.txt](test-results.txt).

Coverage includes valid synthetic prepare/reserve/finalize; missing, expired, wrong-scope and tampered authority; implementation/source/runtime/Swift/JS/Skill closure mismatch; commit and destination inode/mount mismatch; invalid symlink path; fsync/hard-link failures; crash and UNKNOWN no-replay; signed recovery after STOPPED preserving partial files; completed-attempt refusal; valid/tampered Ed25519 signatures; and synthetic 51-image ImageIO accept/reject.

## Initial 51-photo handoff and live status

The preceding foreground report's private preflight for the proposed 51-photo album states that the destination volume was not mounted and the destination did not exist; group UUID, foreground evidence, review, and runtime grant were absent. It also states no photos were read and no request/Save All was issued. This implementation did not revisit that destination or inspect photos.

| Gate | Status |
|---|---|
| P3 synthetic preparation and one-time reservation | `PASS` for the stated tests only |
| Signed authority interface | `PASS` for local cryptographic verification test; trusted production key provisioning `BLOCKED` |
| CUA bridge issuing a bound runtime receipt | `NOT_IMPLEMENTED` |
| Actual destination mount/inode suitability | `NOT_RUN`; prior 51-photo preflight reported unmounted |
| Real LINE foreground / Save All / download | `NOT_RUN`; Save All remained prohibited |
| Actual 51-photo image verification | `NOT_RUN`; only synthetic 51 PNG fixtures decoded |
| Formal VERIFIED readback / release / two-album E2E | `NOT_RUN` |
| Independent implementation review | `NOT_DONE` |

## Security and completion limits

- Source/runtime hashes are checked against every Python file in the batch and acceptance packages, all Skill Markdown, the Swift decoder source, and the CUA adapter; runtime files include the actual Python, Node, OpenSSL, macOS `security`, and `image_decode` executables. Production authorization additionally requires the exact source commit to be clean and signed review/Owner claims to bind the evidence, record head, runtime, destination, expiry, grant UUID, nonce, and one-attempt scope.
- At the time of the tests, this worktree's product files were uncommitted and dirty. Production reservation rejects an uncommitted source closure as `IMPLEMENTATION_SOURCE_NOT_COMMITTED`; the test-only verifier bypass is present only inside the test file and cannot be selected by CLI.
- The CUA adapter still has no P3-issued runtime receipt integration. No code in this change clicks LINE or enables Save All. The current task-local filesystem probe ran on this host filesystem; NTFS behavior was not tested.
- During the Implementer stage there was no commit, push, PR, merge, GUI operation, download, destination cleanup, formal grant/ledger change, or Harness modification.

Source files to review: `src/line_backup_batch/p3.py`, `src/line_backup_batch/daily.py`, `tests/test_p3_scoped_authorization.py`, and `docs/LINE相簿備份_使用手冊.md`. The report and logs describe this implementation only; they do not claim production authority or LINE E2E acceptance.
