# Swift build and focused-test verification

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES, source closure only |
| `SOURCE_VALIDATED` | PARTIAL: see `SOURCE_CLOSURE_PARITY.md`; candidate has not compiled |
| `OFFLINE_BUILD_PASS` | NO |
| `RUNTIME_BOUND` | NOT_VERIFIED |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |

## One authorized invocation

The only build/test command executed in this task was:

```text
swift test --package-path <ISOLATED_WORKTREE>/rev28 --scratch-path <ISOLATED_WORKTREE>/.swift-build-closure --filter Rev28CoreTests.FrameSupportGrantProfileTests
```

It started at `2026-10-13T06:50:37.256112Z`, ended at `2026-10-13T06:50:44.555433Z`, and returned **exit code 1** before compiling package sources or running XCTest. SwiftPM rejected the package manifest while importing the Swift standard library. The selected compiler is Apple Swift 6.3.3, but inherited `SDKROOT` selected the Command Line Tools macOS SDK whose Swift interface identifies itself as built by Apple Swift 6.4. The compiler diagnostic is: “this SDK is not supported by the compiler.” The environment inspection showed Xcode 26.6/build 17F113 selected, Xcode Swift at `xcrun --find swift`, `SDKROOT` set to the Command Line Tools SDK, and Xcode's separately queried macOS SDK version 26.5. These are not a successful matching compiler/SDK pair for the invocation.

The complete raw stdout log is empty (0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Complete raw stderr is retained locally and has SHA-256 `d85ed1768a41cb79dafe94346e8e519287bfce35e709223a07e6423c04a82bbe` (9,050 bytes). It includes SwiftPM's invalid-manifest tool invocation and the standard-library/SDK mismatch diagnostics. The safe, complete log with only private worktree and ephemeral temporary-directory paths replaced is [SWIFT_BUILD_REDACTED.log](SWIFT_BUILD_REDACTED.log), 8,807 bytes, SHA-256 `8b21566b16f75048eb5deb7e41d1e0b2f6e3819c0dab5dd7176c1733b85d8c81`. No compiler diagnostic for package source was reached.

`FrameSupportGrantProfileTests` did **not** run; there is no test count or test PASS. This invocation does not prove that the source patch compiles. The only remaining executable validation in this task is blocked by the host-selected SDK/compiler mismatch. A future build would require a separately authorized invocation under a matched, explicit Xcode compiler and SDK environment; no retry, SDK override, alternate compiler, or second Swift command was attempted here.

## Source/toolchain identity

The package source-input manifest used for this invocation is in `SOURCE_CLOSURE_PARITY.md`: 86 files, 1,324,693 source bytes, 12,884 canonical manifest JSON bytes, SHA-256 `0c340e17e49fd388c24b0bd270b74b50330035b4bbc99a6154865ff165993c33`. The manifest was computed after the source patch. No `Package.swift`, `Sources/`, or `Tests/` file changed after it was computed. `SDKROOT` was inherited as the Command Line Tools SDK path while `xcode-select -p` resolved to Xcode. `xcrun --find swift` resolved to the Xcode toolchain, but the `swift` command resolved through `/usr/bin/swift`; the manifest compiler in the captured log was Xcode's `swiftc` 6.3.3. Xcode/Swift/SDK version queries were metadata reads; they did not build or execute the product binary.

The GitHub CI run for the earlier code head `a72b2bb70e938991eff58afb6fd99822e4ef8c54` is [run 38355636802](https://github.com/s9008129/Line_backup/actions/runs/38355636802). Its first reported source error was the absent `ExplicitLineSelectionWitness` at `FrameCapture.swift:113`, followed by synthesized Codable/Equatable errors. That run predates this source patch. The current head's automatic CI result is pending publication and has not been observed here.

## Limits and next review

This is source-closure work only. No formal grant was read or created, no CLI product binary was run, and no runtime-binding, LINE, producer, screenshot, AX, or GUI action occurred. `RUNTIME_BOUND=NOT_VERIFIED`, `LIVE_PRODUCER_PASS=NO`, and `GUI_AUTHORIZED=NO`. The old failed scratch build's diagnostics in the separately untracked `PassiveContextObservation.swift` remain outside this PR7 source closure; see the parity report. Do not treat this failed manifest invocation, historical focused logs, or the unchanged profile tests as evidence of a live task criterion or activation authorization.
