# Swift build and focused-test verification

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES, isolated source-closure integration only |
| `SOURCE_VALIDATED` | PARTIAL: production package targets compiled in automatic CI; test target did not compile |
| `OFFLINE_BUILD_PASS` | YES for the automatic CI package build at code head `9d37c8f8c2a30655f7be095f466dd261b7df2caf`; the sole local invocation failed before source compilation |
| `FOCUSED_TEST_PASS` | NO; `FrameSupportGrantProfileTests` did not execute |
| `RUNTIME_BOUND` | NOT_VERIFIED |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
| `SOURCE_CLOSURE_UNRESOLVED` | YES for test closure; automatic CI compiled production targets but failed compiling the test target |

## One authorized local invocation

The only Swift build/test command executed in this task was:

```text
swift test --package-path <ISOLATED_WORKTREE>/rev28 --scratch-path <ISOLATED_WORKTREE>/.swift-build-closure --filter Rev28CoreTests.FrameSupportGrantProfileTests
```

It started at `2026-10-13T06:50:37.256112Z`, ended at `2026-10-13T06:50:44.555433Z`, and returned **exit code 1** before compiling package sources or running XCTest. SwiftPM rejected the package manifest while importing the Swift standard library. The selected compiler is Apple Swift 6.3.3, but inherited `SDKROOT` selected the Command Line Tools macOS SDK whose Swift interface identifies itself as built by Apple Swift 6.4. The compiler diagnostic was: “this SDK is not supported by the compiler.” Xcode 26.6/build 17F113 was selected; `xcrun --find swift` resolved to the Xcode toolchain, while the invocation inherited the Command Line Tools SDK. The separately queried Xcode macOS SDK version was 26.5. No retry, SDK override, alternate compiler, or second Swift command was attempted.

Raw stdout was 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Raw stderr was 9,050 bytes, SHA-256 `d85ed1768a41cb79dafe94346e8e519287bfce35e709223a07e6423c04a82bbe`. The safe redacted log is [SWIFT_BUILD_REDACTED.log](SWIFT_BUILD_REDACTED.log), 8,807 bytes, SHA-256 `8b21566b16f75048eb5deb7e41d1e0b2f6e3819c0dab5dd7176c1733b85d8c81`. It preserves the compiler/SDK diagnostics while replacing private workspace and ephemeral temporary paths.

`FrameSupportGrantProfileTests` did **not** run. The failed command used the earlier **86-file** source-input manifest: 1,324,693 source bytes, 12,884 manifest JSON bytes, SHA-256 `0c340e17e49fd388c24b0bd270b74b50330035b4bbc99a6154865ff165993c33`. The current candidate is a separate **88-file** manifest documented in `SOURCE_CLOSURE_PARITY.md`, SHA-256 `030ca74b6aa0426aec3a7676963928c858c0a35506b9cdc122a66989e7ae845c`; it has not been compiled locally. Do not describe the failed command as testing the current source.

## Automatic CI results

Prior-head run [38359876614](https://github.com/s9008129/Line_backup/actions/runs/38359876614) failed for code head `515a4d743a01810b105d357dc757e7f53a8f9604` because `rev28ctl/main.swift` referenced missing `PassiveCaptureDiagnostic` at lines 22, 26, 27, and 560. The current source integration addressed that existing CLI dependency and the exact Core APIs it calls.

The automatically created current-head run [38362205501](https://github.com/s9008129/Line_backup/actions/runs/38362205501), job [115178809672](https://github.com/s9008129/Line_backup/actions/runs/38362205501/job/115178809672), tested code head `9d37c8f8c2a30655f7be095f466dd261b7df2caf` via workflow merge commit `db4893b71a8b646ce9338095bd9a5a185aad06f4`. `xcrun swift build --package-path rev28` succeeded. `xcrun swift test --package-path rev28 --skip OcrEngineTests` failed while compiling tests with `rev28/Tests/Rev28CoreTests/NativeObservationSessionTests.swift:700:1: expected '}' at end of extension`. No XCTest ran; `FrameSupportGrantProfileTests` did not execute, and the adversarial matrix and historical replay were skipped. Overall run conclusion: **failure**.

Root verified the failing test file is 32,738 bytes / 699 lines, SHA-256 `628c0981a943e55d5f77b2a031e42caa1f04074b1d66ae04a39f778fd72cf696`, byte-identical to both the PR3 base and the task-start state. This parser failure predates both source-closure patches. No repair was made; implementation stops at this first further CI failure. The workflow recorded Xcode 27 / Swift 6.4 / SDK 27 metadata; its build step sets `DEVELOPER_DIR` to the Xcode application. The metadata record alone does not identify the compiler executable/version used by that build command.

The decoded job-log response was 57,061 UTF-8 bytes, SHA-256 `651b9be98732d5e8bd45eaaf95e48f1d85eba8f1e1645d9070ec33ee9e70204c`. The path-redacted and trailing-whitespace-normalized copy is [SWIFT_CI_RUN_38362205501_REDACTED.log](SWIFT_CI_RUN_38362205501_REDACTED.log), 55,463 bytes, SHA-256 `9e1bf038759ddb99cf43305f45d27e9b34472f12968374b04c03a6c8c433221f`. Diagnostic content and line ordering are retained.

## Limits and next review

This is source integration only. No formal grant was read or created, no CLI product binary was run, and no runtime binding, LINE, producer, screenshot, AX, or GUI action occurred. `SOURCE_CLOSURE_UNRESOLVED=YES` for test closure, `RUNTIME_BOUND=NOT_VERIFIED`, `LIVE_PRODUCER_PASS=NO`, and `GUI_AUTHORIZED=NO`. The local compiler/SDK mismatch and current-head test parser failure are separate. The old scratch diagnostics in the separate local `native-context` branch remain outside PR7's selected `main.swift` source closure. Neither the CI production build nor the test-compile failure establishes the original runtime criterion or grants activation authority.
