# Source Provenance

## Selected bytes and candidate base

The implementation branch is stacked on PR #3 head `86afa32990d089fa469d54bfdbecb1cd23e3bde8`, whose base is `v43-ab/codex-rev28` at `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`. PR #3 itself is not modified. PRs #4, #5, and #6 are not modified.

The source mismatch basis is the accepted [PR #6 runtime entry-point report](https://github.com/s9008129/Line_backup/blob/e82864812a4403adf4c4b28bc201cc3aa2b464e3/review/runtime-entrypoint-20261013/RUNTIME_ENTRYPOINT_VERIFICATION.md); the governance state is accepted in [PR #4 recovery decision](https://github.com/s9008129/Line_backup/blob/1c147e7b61301aa8f1b813be069d32bfe003b3dd/review/g0-controller-route-20261013/RECOVERY_DECISION.md). These immutable documents are cited as prior evidence; no new source/runtime state was re-investigated.

The profile helper exposes only public read-only identity fields and a static selector; construction remains private. Legacy authorization/runtime behavior remains in the legacy branch. The original minimal-live-08 tuple is recognized but explicitly refused until the canonical host authorization and CRITICAL Plan Review binding is independently verified. No speculative authorization file path or inherited waiver is accepted.

| Source | Provenance before candidate edit | SHA-256 before edit | Candidate treatment |
|---|---|---|---|
| `rev28/Sources/rev28ctl/main.swift` | Dirty tracked source in the original local worktree; PR3/base source has the same target `frameSupportVerifyGrant` function but not the local `native-context` CLI block | `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586` | Function-only grant-profile patch on PR3 source; unrelated local CLI block remains untouched locally and is not copied into the PR |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_runner.mjs` | Untracked task-local source in the original local worktree and absent from PR3 | `a20d37fe3c57d40bcff49c7afcd885898d1ada06ee9e6ff44b6dfb5be7d83dbd` | One source file added at its exact Q path; screenshot retention narrowed to a validated PNG subset; actual CUA screenshot bytes remain unknown |
| PR3/base `rev28/Sources/rev28ctl/main.swift` | Source blob at the selected PR3 head | file-content SHA-256 `4308591007c9658b25c59dbb383b702c2cad45622b77311272783827858a8ad1` | Target function was compared before applying the function-only patch |

Final candidate source hashes: `main.swift` `51a01b168336b271d8dfceba49aef28f3236c8e24d420fa586b13dac6c8904a7`; `FrameSupportGrantProfile.swift` `f3b6486de517e7d5405b38696c96c0c8194ac2280d9a2ef364eb639d6b41bb77`; focused Swift test `9e3515d63c3158ec4734c825bc890d36ce0b0a1b40657202a6b914a22df11cc3`; Q `live_runner.mjs` `cc501ef5d6f12d869c6e65bf8cdd5e108f33b0a718dd466f05f00ccfc28b4f63`; focused Node check `846abdc36add79c9996b670fd6f3ade3347cb57cde00621b431375c63db51050`. The candidate Swift target function SHA-256 is `1121892b2ced326b12c775d8bb46f07b8cb9dc5261edf0cdf1dcf2d0f432edc7`; the exact current-local original target function SHA-256 was `748dee7ad4c3e9a0303479eb1e419780712a6d2cc68c577cce3554a6c7c58a8d`.

The original Q `live_runner.mjs` source was 577 lines; the candidate file is 644 lines after the bounded retention change. A bounded privacy scan found no grant/runtime-binding records, personal paths, credentials, group/account values, screenshot bytes, or AX content. The candidate does not upload the remaining Q directory or any task evidence. Its referenced sibling modules are not included, so the candidate checkout is not a complete runnable task tree; the unit check extracts the literal production function body from this exact file rather than importing the incomplete task module graph.

## Swift build snapshot

The one build attempt used an isolated copy of the current local Swift package source closure, including its dirty and untracked `Sources/` and `Tests/`, with the then-current candidate profile helper/test and function patch overlaid. This deliberately tested the selected local package snapshot without changing the main worktree or treating the older PR3 base alone as the current Mac source. The pre-correction snapshot has 94 Swift files / 1,491,136 bytes; its reproducible manifest is the sorted list of dictionaries `{'path': relative_to(package_root), 'bytes': file_length, 'sha256': file_sha256}` for `.swift` files outside `.build`, serialized with sorted JSON keys and compact separators, SHA-256 `c23b178271d88293349c9e11263f8b29d53479b905ebceb48beecf7db2ff76de`. The build failure occurred in unrelated copied native-observation code; it was not repaired or retried.

An in-memory source projection replaced only `frameSupportVerifyGrant` in the original dirty local `main.swift` with the candidate function and verified that every byte outside the function remained identical, including the unrelated `native-context` CLI block. The original file was not written. The candidate branch omits that unrelated block. The local source SHA does not prove the installed binary was built from it. Installed binary provenance, runtime membership, screenshot format, and task-to-binary binding remain NOT VERIFIED.

Sol independently rechecked the protected Controller tree (193 entries, 402,117,612 regular-file bytes; tree SHA-256 `9d8e16b6e09579fb26565e399cbd41165737cff9587ca1468a0f11bb8410a915`) and selected `runtime/resources-luna` tree (91 entries, 1,021,640 regular-file bytes; SHA-256 `f39bb3bc22f7f5aeeb703fca041eb455c6ffb311cc2b3b12eb1d31159979fd5e`) against their initial anchors; both match. Each digest uses sorted paths relative to that selected tree root, with kind, mode, length and file/symlink-target SHA-256, serialized as compact sorted-key JSON. This is preservation evidence only, not platform enforcement or installed-release identity.

Sol independently ran the final Node check and confirmed 14 cases passed, exit 0, and the literal production function body SHA matches. Root independently confirmed the Swift source projection preserves the local `native-context` block and that the source outside the target grant function matches PR3. These are bounded source/offline checks only; they are not formal Acceptance or a live product PASS.

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES — isolated candidate only |
| `SOURCE_VALIDATED` | PARTIAL — local source diff/provenance and literal JS function checks only |
| `OFFLINE_BUILD_PASS` | NO — the one Swift build failed before tests |
| `RUNTIME_BOUND` | NO |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
