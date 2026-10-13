# Evidence Manifest — Runtime Entry-Point Review

## Review identity and limits

- Review branch base: `v43-ab/codex-rev28`, commit `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b` (remote base verified before creating the isolated evidence worktree).
- Classification: `PRODUCER_OR_BINDING_MISSING`.
- Source files under the original local task root Q were read from the existing user worktree, where task-root materials are untracked; they were not copied into this evidence branch. Other package/source files were read from that same current working-tree snapshot. Some inspected tracked source bytes are locally modified and some Swift source files are absent from the selected b7 base. The evidence branch deliberately remains on the verified b7 development base and contains only this report and manifest; its code is not represented as the inspected runtime snapshot.
- Evidence methods: bounded source views/searches, `shasum -a 256`, `file`, `lipo -info`, and existence checks. No source/binary execution, tests, build, Controller/Harness CLI, Python batch action, CUA call, LINE/UI/AX observation, or GUI authorization use.
- Paths below are repository-relative. No raw screenshot/AX data, grants, tokens, private absolute host path, or task-root data payload is included.

## Reviewed source identity roster

Hashes identify the exact local bytes read. Function/range names are included to support a reviewer’s bounded spot check; this is not a claim that every file in the complete runtime closure was inspected.

| Repository-relative path | SHA-256 | Relevant source locations |
|---|---|---|
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_entry.mjs` | `20f8edd5220790806c9f98e9b5770bba4aae36694a674df2239b7cc80f4abb47` | `createLiveEntry`, preflight, `probe`, `runTwoAlbums` (13–69) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_runner.mjs` | `a20d37fe3c57d40bcff49c7afcd885898d1ada06ee9e6ff44b6dfb5be7d83dbd` | contract pins (9–14), `runtimeGate` and closure inventory (70–169), Python CLI dispatch (177–224), producer hooks (262–337), runner composition (515–576) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_analyzer.mjs` | `26a797e0e63ee3afb73f1df791e9891f3488e25c138b5e65ed9cc0bbe6cfdfd1` | `native` and `analyzeCapture` (33 onward) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_classifier.mjs` | `6ca901bec3396a38444c121757cfeded0a007f0f2dcd09226cfdac839ee12653` | `createLiveClassifier.classify` (48–242) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/host_io.mjs` | `9f66016dd0288eadb0d3d170480a8fb472affe264346c3dc8ca2eeb12a001628` | process wrapper and host RPC (12–72) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/tools/host_process.py` | `45efaa44a3b514518ed3b4b0b1dfeb4bf08c0a6daa232cec45d5e82a1c8ab567` | executable allowlist/process supervision and RPC dispatch (27–85) |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/tools/native_bridge.py` | `981468e644f0953167f0fdb34239245958c800ab5c2e7234cc9b8863ccbb458e` | `CandidateController` binding and `prepare_plan` references (20–24, 60, 119–122); controller-admission path, not producer entrypoint |
| `scripts/line_backup_cua_adapter.mjs` | `d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f` | `createHostedSession.observe` (111–180), `createNavigationObserver.observe` (545–597) |
| `src/line_backup_batch/cli.py` | `f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6` | task grant/runtime binding validation (52–161), CLI dispatch and main (239–284) |
| `src/line_backup_batch/service.py` | `54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6` | transaction `Service` used by the batch CLI (29 onward) |
| `rev28/Package.swift` | `f9cefa31739ce6667e850461deefe7336b82df09de6bf204f784c666be26cc57` | `rev28ctl` executable target (4–59) |
| `rev28/Sources/rev28ctl/main.swift` | `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586` | `native-context` dispatch (35–70), `frame-support` dispatch (556–573), grant binding (978–1003), capture path (1110–1310) |
| `rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift` | `7803cd6b88987465c42430891906e166c14a204b3f41bbac24801f1540fc49d3` | process selection/context capture (145–167), AX/window/OCR collection (202–224, 520–554) |
| `rev28/Sources/Rev28Core/Observation/NativeObservationSession.swift` | `9230ec99679badd7cad01d53c0c4d9811db6cd149f1aa42b0b98a3c34885e4c2` | observation source abstraction and SCK/CG/AX identity checks (60–99, 230–329) |
| `rev28/Sources/Rev28Core/Sensor/FrameCapture.swift` | `10b6596871d7bfc05d203ac7041a2b917d851fd7345355f1c4c9a142d568cc7e` | retained full-display capture implementation (`captureFullDisplayRetained`, 501 onward) |
| `rev28/Sources/Rev28Core/Sensor/WindowSensor.swift` | `46e657fa73a6c70f0bc6cd0b7fec3de01f28ae73bec5d9e2321cff5d4bc7454c` | ScreenCaptureKit window enumeration source |
| `rev28/Sources/Rev28Core/Perception/OcrEngine.swift` | `d0dcab179db7311853857eeaf065339eb4f74c64976dd2b5104ef9fa280cec00` | OCR engine interface/production implementation (38, 95, 129) |
| `rev28/Sources/Rev28Core/Composition/ProductionObservationSource.swift` | `3745e6de06bc2bee83097b69cb6a30a481d79d631c465564c218ebed008003e6` | production observation source type (33 onward) |
| `rev28/Sources/Rev28Core/Composition/LiveComposition.swift` | `a1a3d0811decb03e94833d2271981359931d625964e6cba0a397e0d537068866` | separate Swift `live-preflight` composition factory |
| `rev28/Sources/Rev28Core/Composition/ComposedNativeAdapter.swift` | `e0c2282998d445adb438384835ea92c41779ae8ec73faf895fb10649c60cc688` | separate Swift live execution adapter |
| `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift` | `22963b60bbd54a8df890b2d7558564e9980bd8d267095af78332ba8fea1c16cf` | separate Swift preflight/execution engine |

The archived copy `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/evidence/live-first-g0-audit-20261012/raw/local-main.swift` hashes to `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586`, byte-identical to the selected `rev28/Sources/rev28ctl/main.swift`. It is an archived evidence copy, not the package source path that `runtimeGate()` inventories.

## Inspected working-tree bytes versus evidence-branch base

The following differences are why the evidence branch does not claim to contain the inspected runtime source. “Local” is the current original user working-tree byte identity used for this report; “base” is the isolated evidence worktree at b7. No source was copied or edited to reconcile them.

| Repository-relative path | Inspected local SHA-256 | Evidence-branch b7 SHA-256 |
|---|---|---|
| `scripts/line_backup_cua_adapter.mjs` | `d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f` | `bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2` |
| `src/line_backup_batch/cli.py` | `f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6` | `7aeed3f9a6e64f7a09f88ee9f2dc71793af46d4a1c70fdac1cbef258f37b17eb` |
| `rev28/Sources/rev28ctl/main.swift` | `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586` | `4308591007c9658b25c59dbb383b702c2cad45622b77311272783827858a8ad1` |
| `rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift` | `7803cd6b88987465c42430891906e166c14a204b3f41bbac24801f1540fc49d3` | Absent |
| `rev28/Sources/Rev28Core/Observation/NativeObservationSession.swift` | `9230ec99679badd7cad01d53c0c4d9811db6cd149f1aa42b0b98a3c34885e4c2` | `e3e668e31b3d4268bba3b949a95c5ad4d72e0eaf5278cbcc182d9b3d1e28acb9` |
| `rev28/Sources/Rev28Core/Composition/ProductionObservationSource.swift` | `3745e6de06bc2bee83097b69cb6a30a481d79d631c465564c218ebed008003e6` | `6ad50045238cad28bd98fd77601872b5760e0e81aa1bf564908b8936e5bb5348` |
| `rev28/Sources/Rev28Core/Composition/LiveComposition.swift` | `a1a3d0811decb03e94833d2271981359931d625964e6cba0a397e0d537068866` | `f0b8feb4a214812187febfaa7c2d4b770319a4823a2a5f81f1a4678699564956` |
| `rev28/Sources/Rev28Core/Composition/ComposedNativeAdapter.swift` | `e0c2282998d445adb438384835ea92c41779ae8ec73faf895fb10649c60cc688` | `e0c2282998d445adb438384835ea92c41779ae8ec73faf895fb10649c60cc688` |
| `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift` | `22963b60bbd54a8df890b2d7558564e9980bd8d267095af78332ba8fea1c16cf` | `22963b60bbd54a8df890b2d7558564e9980bd8d267095af78332ba8fea1c16cf` |

All Q-specific task modules in the roster are absent from the b7 branch because they are untracked task-local files in the original worktree. Other roster entries were individually hash-checked; equality or difference should be read from the exact hashes, not inferred from their path.

## Binary and binding artifact identity

| Repository-relative path | Observation | SHA-256 |
|---|---|---|
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/bin/rev28ctl` | Absent; parent `bin/` directory also absent | — |
| `harness-development/line-v3-live-e2e-20261010/bin/image_decode` | Mach-O executable, arm64; hash matches the Q runner's expected decoder SHA | `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf` |
| Python 3.13 executable named in `host_io.mjs` | Present and executable; `realpath` equals the configured path; Mach-O arm64. Absolute host path intentionally omitted. Runtime-inventory membership/hash is not verified because Q binding is absent. | `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804` |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live-grant-1.json` | Absent | — |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live-grant-2.json` | Absent | — |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/runtime-binding.json` | Absent | — |
| `rev28/.build/arm64-apple-macosx/debug/rev28ctl` | Mach-O executable, arm64; not executed; build provenance/task binding unverified | `a0a9750357b70555644a56a7b33a636a566e027e6d2998d9140ee1690083390e` |
| `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/bin/rev28ctl` | Mach-O executable, arm64; not executed; different continuation path | `9f3aed5f26394de1108f064d566e253fcdb50cf76a9dc329f05185c1ae215022` |
| `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/swift-build-26.5/arm64-apple-macosx/debug/rev28ctl` | Mach-O executable, arm64; not executed; byte-identical to the preceding different-continuation binary | `9f3aed5f26394de1108f064d566e253fcdb50cf76a9dc329f05185c1ae215022` |
| `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/controller/TASK-4acb4326ea2a4c50ace6f333f2de8751/plan-contract.json` | Present; matches source-pinned contract hash | `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc` |

All binary path observations above refer to the existing local workspace. They are hash/metadata-only observations; binary files were not copied into the evidence branch. The source-pinned Swift `frameSupportVerifyGrant` contract differs from Q's source-pinned contract; see the verification report. The conflict is established between inspected local source files only. Since binary-to-current-source provenance is unverified, this does not show that any existing binary was built from the inspected Swift source or that a binary was observed rejecting a grant. No Q grant or runtime-binding contents were available to inspect. No build was attempted: source/package and other binaries exist, but a new binary cannot resolve the missing task binding, caller, or source-level contract mismatch. This does not assert that the source cannot build.

## Runtime state and preservation provenance

- Host read-only observation: Darwin/macOS 27.0.1 on arm64; `/Applications/LINE.app` directory present. The Swift package declares tools version 6.3 and a macOS 26.0 deployment target. No build or ABI-compatibility test was performed, and the existing binary's build version/provenance was not established. This proves neither current app process/session nor Screen Recording, Accessibility, CUA, or task authority. No app UI was opened.
- Task state and lineage facts are accepted from the Chief Reviewer handoff; this review did not re-open task history or controller state.
- Root-provided pre-review preservation anchors: main branch/head `v43-ab/codex-rev28` / `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`; status SHA-256 `fc860490446c3578b0fb085e4fbc7407761915431cac7a288b73ab8011a914c7`; tracked diff SHA-256 `15ca9c34ae9118804c7ac323271e358987cbcb68755764b4b00736b7b74cdb0c`; staged diff SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Root-provided protected-tree anchors before this review: `controller/` tree SHA-256 `9d8e16b6e09579fb26565e399cbd41165737cff9587ca1468a0f11bb8410a915` (193 entries; 402,117,612 regular-file bytes); selected `runtime/resources-luna/` tree SHA-256 `f39bb3bc22f7f5aeeb703fca041eb455c6ffb311cc2b3b12eb1d31159979fd5e` (91 entries; 1,021,640 regular-file bytes).
- Root digest method: sorted subtree-relative entries containing path, kind, mode, regular-file byte length plus SHA-256 (or symlink target SHA-256); canonical JSON with sorted keys and compact separators; no mtime. Root's pre-publication recheck confirmed main branch/HEAD/status/tracked-diff/staged-diff and both protected-tree entry counts, byte totals, and digests equal the baseline anchors exactly. This is root-observed preservation evidence; it does not attest hash-chain semantics, full installed-release identity, OS enforcement, or task acceptance.

## Independent review provenance

- Sol independently confirmed the 21 unique inspected local source-file hashes, the expected producer/decoder/Python identities, and the absence of Q's expected grants, runtime binding, and producer path. Sol separately derived the `.bin`/image-extension mismatch and frame-support task/contract mismatch from the inspected source. No source or executable was run by that review.
- Sol's crosscheck does not establish binary-to-current-source provenance, equality to the evidence-branch base, a live session, GUI authorization, or a formal original-criterion/G1 PASS. It is a bounded source/evidence review only.

## Verification outcome

- `SOURCE_EXISTS`: YES.
- `BUILT_BINARY_EXISTS`: YES elsewhere; expected task-bound binary absent.
- `RUNTIME_BINDING_VERIFIED`: NO.
- `LIVE_PRODUCER_EXECUTED`: NO.
- `GUI_AUTHORIZED`: NO for this review.
- `NOT_VERIFIED`: current host caller/session, actual grant validity, complete runtime closure equality, binary-to-task provenance, real screenshot/AX producer receipt, and satisfaction of the original issue criterion.
- Tests/builds: none; not required to establish the observed missing artifacts and static path/contract mismatch. No claim of formal task acceptance or G1 pass.
