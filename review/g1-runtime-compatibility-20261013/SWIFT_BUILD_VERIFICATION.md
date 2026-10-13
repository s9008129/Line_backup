# Swift build and focused-test verification

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES, isolated source-closure integration only |
| `SOURCE_VALIDATED` | PARTIAL: exact source hashes, required APIs, preserved refusal paths, and bounded dependency set checked; not compiled on this host |
| `OFFLINE_BUILD_PASS` | NO |
| `RUNTIME_BOUND` | NOT_VERIFIED |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
| `SOURCE_CLOSURE_UNRESOLVED` | YES pending automatic CI on the current source head |

## One authorized local invocation

The only Swift build/test command executed in this task was:

```text
swift test --package-path <ISOLATED_WORKTREE>/rev28 --scratch-path <ISOLATED_WORKTREE>/.swift-build-closure --filter Rev28CoreTests.FrameSupportGrantProfileTests
```

It started at `2026-10-13T06:50:37.256112Z`, ended at `2026-10-13T06:50:44.555433Z`, and returned **exit code 1** before compiling package sources or running XCTest. SwiftPM rejected the package manifest while importing the Swift standard library. The selected compiler is Apple Swift 6.3.3, but inherited `SDKROOT` selected the Command Line Tools macOS SDK whose Swift interface identifies itself as built by Apple Swift 6.4. The compiler diagnostic was: “this SDK is not supported by the compiler.” Xcode 26.6/build 17F113 was selected; `xcrun --find swift` resolved to the Xcode toolchain, while the invocation inherited the Command Line Tools SDK. The separately queried Xcode macOS SDK version was 26.5. No retry, SDK override, alternate compiler, or second Swift command was attempted.

Raw stdout was 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Raw stderr was 9,050 bytes, SHA-256 `d85ed1768a41cb79dafe94346e8e519287bfce35e709223a07e6423c04a82bbe`. The safe redacted log is [SWIFT_BUILD_REDACTED.log](SWIFT_BUILD_REDACTED.log), 8,807 bytes, SHA-256 `8b21566b16f75048eb5deb7e41d1e0b2f6e3819c0dab5dd7176c1733b85d8c81`. It preserves the compiler/SDK diagnostics while replacing private workspace and ephemeral temporary paths.

`FrameSupportGrantProfileTests` did **not** run. The failed command used the earlier **86-file** source-input manifest: 1,324,693 source bytes, 12,884 manifest JSON bytes, SHA-256 `0c340e17e49fd388c24b0bd270b74b50330035b4bbc99a6154865ff165993c33`. The current candidate is a separate **88-file** manifest documented in `SOURCE_CLOSURE_PARITY.md`, SHA-256 `030ca74b6aa0426aec3a7676963928c858c0a35506b9cdc122a66989e7ae845c`; it has not been compiled locally. Do not describe the failed command as testing the current source.

## Prior-head CI failure and source correction

Automatic CI run [38359876614](https://github.com/s9008129/Line_backup/actions/runs/38359876614) completed with failure for prior code head `515a4d743a01810b105d357dc757e7f53a8f9604`. It advanced past the earlier missing selector-witness error, then failed because `rev28/Sources/rev28ctl/main.swift` referenced `PassiveCaptureDiagnostic` at line 22, with the same missing CLI type at lines 26, 27, and 560. The deterministic tests, adversarial matrix, historical replay, and headed capability job were skipped.

The current source patch adds that existing CLI source and its exact Core diagnostic dependency. It also restores the exact source APIs the CLI invokes: explicit request/bundle binding and witness validation in `NativeObservationSession`, descriptor-bound existing-output construction and explicit-window capture in `ProductionObservationSource`, and descriptor-backed epoch-floor checks in `RunEpochAuthority`. The previously reviewed selector, fixed LINE identity, profile allowlist, authority refusal guard, and PNG-retention changes remain in place. The original B/C hashes and prior candidate-02 build record are documented in `SOURCE_CLOSURE_PARITY.md`.

No automatic CI result for the current source candidate has yet been observed. The preceding CI run verifies only the missing CLI edge on the earlier head; it does not prove this dependency closure compiles or that tests run. Once the reviewed source commit is pushed, inspect only the automatically created CI result for that exact new head. Do not manually trigger workflows. If CI reports another missing source/API or any independent failure, stop without another source-fix loop.

## Limits and next review

This is source integration only. No formal grant was read or created, no CLI product binary was run, and no runtime binding, LINE, producer, screenshot, AX, or GUI action occurred. `SOURCE_VALIDATED=PARTIAL`, `OFFLINE_BUILD_PASS=NO`, `RUNTIME_BOUND=NOT_VERIFIED`, `LIVE_PRODUCER_PASS=NO`, and `GUI_AUTHORIZED=NO`. The local compiler/SDK mismatch is distinct from the prior-head CI missing CLI dependency. The separate local `native-context` branch and its old scratch diagnostics remain outside PR7's selected `main.swift` source closure. Neither prior compilation provenance nor future deterministic CI would establish the original runtime criterion or authorize activation.
