# Evidence Manifest

This manifest contains safe hashes and candidate-local verification facts only. It does not include raw Controller state, task records, receipts, screenshots, AX data, local private paths, or runtime dumps.

## Candidate artifact identities

| Artifact | SHA-256 |
| --- | --- |
| `candidate.py` | `d3afdbf91854f4f6e9471991c6e500fd3348dbbf4c035938b81bd77803e08f2e` |
| `tests/test_candidate.py` | `b2cc30170c7c0787e6e69c73a83817ee3a713846434550357daa1cf2563deac4` |
| `tests/fixtures/gate_catalog.json` canonical record digest | `697821120d0eaea35e9b7bcab5c8b7ca8a99002d9e1e9184494bbf844ebc0f49` |
| `tests/fixtures/gate_catalog.json` file-byte SHA-256 | `cad528259a8d949edaeb1edb4b9ca197b31c48427cc812d8711cca0b4406c741` |

## Selected source and lineage anchors

The source identities and bounded interpretation are recorded in [REVIEW_PACKET.md](REVIEW_PACKET.md). Exact original lineage hashes are pinned in code. The orchestrator's final pre-publication comparison confirmed equality with the before snapshot for both protected trees: controller tree digest `9d8e16b6e09579fb26565e399cbd41165737cff9587ca1468a0f11bb8410a915` (193 entries; 402,117,612 regular-file bytes) and selected `runtime/resources-luna` tree digest `f39bb3bc22f7f5aeeb703fca041eb455c6ffb311cc2b3b12eb1d31159979fd5e` (91 entries; 1,021,640 bytes). Tree digests use sorted repository-relative entries with path, kind, mode, file length and SHA-256 (or symlink-target SHA-256), serialized as canonical JSON; mtimes are excluded. This confirms unchanged selected local trees only. It does not prove installed-release identity, controller/runtime equivalence beyond selected files, hash-chain semantics, or OS sandbox/network enforcement.

The orchestrator also confirmed the main worktree preservation anchors match before and after candidate work: branch `v43-ab/codex-rev28`, HEAD `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`, status SHA-256 `fc860490446c3578b0fb085e4fbc7407761915431cac7a288b73ab8011a914c7`, tracked-diff SHA-256 `15ca9c34ae9118804c7ac323271e358987cbcb68755764b4b00736b7b74cdb0c`, and empty staged diff SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. No main-worktree files or index entries were changed.

## Test provenance

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v governance.g0_recovery_candidate.tests.test_candidate`

Result: exit code 0; 14 tests passed. Sol independently crosschecked code hash `d3afdbf91854f4f6e9471991c6e500fd3348dbbf4c035938b81bd77803e08f2e` and test hash `b2cc30170c7c0787e6e69c73a83817ee3a713846434550357daa1cf2563deac4`, reran the exact test command (14/14), and passed review of the isolated candidate boundary. The crosscheck covered frozen six-status enforcement, immutable signed payloads, semantic event replay and operation-origin binding, strict field/path types, gate/history preservation, and privacy/scope. It is not formal independent Acceptance, product PASS, or an external Chief Reviewer verdict. Tests use only synthetic non-formal candidate fixtures. No original task/run was allocated, no retry/continuation was consumed, no Controller or Harness CLI was invoked, and no LINE/UI/AX/R2/runtime execution occurred. The test-only context is deliberately non-activating.

## Before publication

No immutable release or live runtime state was written. The isolated candidate worktree is based on `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`; its review remains bounded to these nine files. The exact publication identity is recorded by the GitHub Draft PR head and description; it does not require a later metadata-only commit.
