# Swift source closure parity

**Scope:** isolated PR7 Swift package source closure. This does not establish runtime binding, producer execution, GUI authorization, or live evidence.

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES, isolated PR7 candidate; two original CLI/Core source files added and three exact dependency API deltas integrated |
| `SOURCE_VALIDATED` | PARTIAL: source identities and bounded dependency closure checked against the original workspace and prior manifest; not compiled on this host |
| `OFFLINE_BUILD_PASS` | NO; the one authorized local invocation stopped before package-source compilation (see `SWIFT_BUILD_VERIFICATION.md`) |
| `RUNTIME_BOUND` | NOT_VERIFIED |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
| `SOURCE_CLOSURE_UNRESOLVED` | YES pending automatic CI for the current source head; the known 515a CLI/API gap is addressed, but no new-head build has yet been observed |

## Change and bounded source closure

PR7 code head before this patch was `515a4d743a01810b105d357dc757e7f53a8f9604`, descended from the reviewed PR3 base. Its existing `rev28ctl/main.swift` dispatches `capture-diagnostic` through `PassiveCaptureDiagnostic.run`; CI run [38359876614](https://github.com/s9008129/Line_backup/actions/runs/38359876614) failed at that first missing source reference. The earlier static survey only followed the Rev28Core library sources and missed this existing executable-target caller and its member/API dependencies. This patch integrates that already-declared source path; it does not create a new command or change `main.swift`.

The exact six-path closure is:

| Source path | Current candidate treatment | Provenance |
|---|---|---|
| `Sources/rev28ctl/PassiveCaptureDiagnostic.swift` | Added exact B/C bytes, 8,128 bytes | SHA-256 `b32029b10c9d9611656b4a1fe1debb504233b5cf8f98f8453f886edaa7f88ecc` |
| `Sources/Rev28Core/Composition/PassiveNativeDiagnostic.swift` | Added exact B/C bytes, 32,855 bytes | SHA-256 `e7b1a2546de758d87c349b0800e8626f84115bedd412a69c45aaaa71cecb7ee4` |
| `Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift` | Already present from the prior reviewed patch; exact selector/witness validator retained | Candidate SHA-256 `2ca55edd625d6656ddeb41e66690ce3069ff07ab945d6211b654931002d55025`; original B/C `5662baca0285f45859ac918d064ed404c6f14d528c4382a7598c4b2d86933e6c` |
| `Sources/Rev28Core/Observation/NativeObservationSession.swift` | Integrated the B request/bundle binding fields and strict validation/propagation; retained PR7's fixed `ObservationTarget.lineBundleID` and recorded-geometry refusal detail | B/C SHA-256 `9230ec99679badd7cad01d53c0c4d9811db6cd149f1aa42b0b98a3c34885e4c2`; candidate SHA-256 `c4a7407032a022efb2450dcace65c693100b2984924f502d9160b876fde61929` |
| `Sources/Rev28Core/Composition/ProductionObservationSource.swift` | Integrated the exact B descriptor-backed output initializer and explicit-window native capture path | B/C and candidate SHA-256 `3745e6de06bc2bee83097b69cb6a30a481d79d631c465564c218ebed008003e6` |
| `Sources/Rev28Core/Sensor/RunEpochAuthority.swift` | Integrated exact B descriptor-bound epoch floor and linked-parent-entry checks; existing pathname initializer and branch remain | B/C and candidate SHA-256 `b738df79817441240804531c033ab87f8be5b0dec78fd6683a3aa4a7c7162e3c` |

The added CLI source performs no work merely by being present in the build. If invoked, it requires explicit arguments, fixed LINE bundle identity and positive PID, claims the existing output directory, refuses when `CI` is set, checks process identity and existing AX/screen-capture preflight without requesting permissions, samples windows twice, binds the source, then uses the existing observation/session and retained-packet path. This task did **not** invoke it. No formal grant or live authorization was created, read, or inferred.

The source closure includes the selector/witness checks, `NativeObservationSession` binding and witness validation, `ProductionObservationSource` explicit-window capture, and descriptor-only `RunEpochAuthority` mode because the existing diagnostic CLI calls those exact APIs. The original pathname-based epoch initializer remains; diagnostic mode uses the descriptor constructor and does not fall back to a path. The diff retains existing refusal guards and legacy capture path. No `AlbumVisualWitness.swift`, `PassiveContextObservation.swift`, `LiveComposition` changes, passive diagnostic tests, tests, native-context command, or other dirty Mac source was copied. The separate local `native-context` branch and its old scratch diagnostics remain outside PR7's `main.swift` source closure.

This is a package-source integration only. It does not grant GUI use, run the CLI, activate runtime binding, or prove screenshot/AX output. The PNG screenshot subset repair, fixed grant profile allowlist, profile authorization guard, and focused profile test source are unchanged.

## A/B/C source identity

A is the PR7 committed source at `515a4d743a01810b105d357dc757e7f53a8f9604`; B is the original dirty Mac source; C is the prior failed-build snapshot. The exact B/C bytes for the six dependency paths above were compared to the prior source manifest. B/C are not substituted wholesale: only the named source files and dependency API hunks entered the isolated candidate. The original dirty workspace was not edited.

| Relative path | A: PR7 before this patch | B: original workspace | C: prior snapshot |
|---|---|---|---|
| `Sources/rev28ctl/main.swift` | `51a01b168336b271d8dfceba49aef28f3236c8e24d420fa586b13dac6c8904a7` | `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586` | `ad168dd3fa0b478746742dda4465b3467af8b37d5f3c5e98d17d2dc4cc4ca6ed` |
| `Sources/rev28ctl/PassiveCaptureDiagnostic.swift` | absent | `b32029b10c9d9611656b4a1fe1debb504233b5cf8f98f8453f886edaa7f88ecc` | same as B |
| `Sources/Rev28Core/Composition/PassiveNativeDiagnostic.swift` | absent | `e7b1a2546de758d87c349b0800e8626f84115bedd412a69c45aaaa71cecb7ee4` | same as B |
| `Sources/Rev28Core/Observation/NativeObservationSession.swift` | `10178d2c0f8699fa7837358a6400bce744c6dc753aab324a5927141df702cbc2` | `9230ec99679badd7cad01d53c0c4d9811db6cd149f1aa42b0b98a3c34885e4c2` | same as B |
| `Sources/Rev28Core/Composition/ProductionObservationSource.swift` | `6ad50045238cad28bd98fd77601872b5760e0e81aa1bf564908b8936e5bb5348` | `3745e6de06bc2bee83097b69cb6a30a481d79d631c465564c218ebed008003e6` | same as B |
| `Sources/Rev28Core/Sensor/RunEpochAuthority.swift` | `5bde1fc85cf2fe12a0fb18961a0ff8d118cdddc58e80777de9fd89b7fdc95682` | `b738df79817441240804531c033ab87f8be5b0dec78fd6683a3aa4a7c7162e3c` | same as B |
| `Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift` | present from prior patch | `5662baca0285f45859ac918d064ed404c6f14d528c4382a7598c4b2d86933e6c` | same as B |

### Prior source/build provenance

The local bounded review also located `harness-development/rev28-project-binding-plan/TASK-08a0bd6da5c54d03944ce2fb994ff71b/candidate-02-cli-build.json`. It records `swift build --product rev28ctl` exit code 0 and a 117-entry manifest. The manifest contains exact hashes and lengths for the six source paths above (including the selector) matching B/C. This is prior build provenance for those bytes in that earlier package snapshot; it is not a build of the current PR7 source manifest, not the failed current local invocation, not CI for this head, and not live/runtime acceptance.

## Current candidate source-input manifest

The **current isolated candidate** source manifest is a post-patch inventory, not a test/build input that was executed locally. It covers `Package.swift` and every regular file under `Sources/` and `Tests/` in `rev28`, with records `{path relative to rev28, bytes, SHA-256}`, sorted by path and encoded as compact JSON with sorted keys. It contains **88 entries**, **1,375,274 source bytes**, **13,193 manifest JSON bytes**, SHA-256 `030ca74b6aa0426aec3a7676963928c858c0a35506b9cdc122a66989e7ae845c`.

The one local Swift command used the earlier **86-entry** pre-CLI-closure manifest: 1,324,693 source bytes, 12,884 manifest bytes, SHA-256 `0c340e17e49fd388c24b0bd270b74b50330035b4bbc99a6154865ff165993c33`. That command failed during package-manifest import, before source compilation. Do not attribute it to the current 88-entry source.

```text
f9cefa31739ce6667e850461deefe7336b82df09de6bf204f784c666be26cc57 1972 Package.swift
94590f9a7c2ca5766e68c82ff9731cfbf9d8eeb4debc4e548372a47b80450e26 11360 Sources/Rev28Core/Actuation/AXDriver.swift
bf7bfb4d9dc3db108e962649a110dd40c999286c1398745480d1a6ff44e3b9f8 31626 Sources/Rev28Core/Actuation/QuartzActuator.swift
ecbdd6bb5ee806ed9a061c4b317747af980ac5ce0428065935bb34f461af8248 20392 Sources/Rev28Core/Chooser/ChooserAffirmationPredicate.swift
4602d0ad941cf276ecf9b6601bb0f422aee7a20894b6aaf59c0f4d880ac15bbc 25392 Sources/Rev28Core/Chooser/FolderChooserDriver.swift
e0c2282998d445adb438384835ea92c41779ae8ec73faf895fb10649c60cc688 17645 Sources/Rev28Core/Composition/ComposedNativeAdapter.swift
f0b8feb4a214812187febfaa7c2d4b770319a4823a2a5f81f1a4678699564956 8473 Sources/Rev28Core/Composition/LiveComposition.swift
e7b1a2546de758d87c349b0800e8626f84115bedd412a69c45aaaa71cecb7ee4 32855 Sources/Rev28Core/Composition/PassiveNativeDiagnostic.swift
e56df8319aa49255b5a9f6bb4f942db0e6a887f1e331044c6899bd1f9e96a016 46672 Sources/Rev28Core/Composition/PhaseAEvidence.swift
165f184467f2e92bad7848303dbb56ab48e482f902b2a3e472e787fabe5d9c3f 36531 Sources/Rev28Core/Composition/PostSaveComposition.swift
6d1f85ea488647de2116b29d08d7c4c3e5e6b1197e2dbd617d872de0dbe5ff2b 18972 Sources/Rev28Core/Composition/PostSaveEnvironment.swift
3e9932d1a50e2fc19f60fbd10e6bdb73c3f0544c3cb8078b98f5f81ee00e2b0c 1358 Sources/Rev28Core/Composition/ProductionActuationEnvironment.swift
3745e6de06bc2bee83097b69cb6a30a481d79d631c465564c218ebed008003e6 8574 Sources/Rev28Core/Composition/ProductionObservationSource.swift
e80a554e9ba8f52c447b6fcae2b107166deac79846a9801b626300241ac59258 33979 Sources/Rev28Core/Composition/ProjectBackupBinding.swift
93db7d0968cf99a94526de498d680d614e9a63822aba739591a65fa7d360d107 6609 Sources/Rev28Core/Diagnostics/DiagnosticHooks.swift
f3b6486de517e7d5405b38696c96c0c8194ac2280d9a2ef364eb639d6b41bb77 3951 Sources/Rev28Core/FrameSupportGrantProfile.swift
f9b77879cfc7abf596de4f0ab562ba8e7506bde2673844a94d37d96b4b0d564c 14431 Sources/Rev28Core/Geometry/Coordinates.swift
c1ae64a0cb942b5fe636e95c0407cba02387a8c44ef67d5cd05dc6afe49a7896 3637 Sources/Rev28Core/Identity/AXWindowIdentitySelector.swift
14e3b0d5d660c19550700cb6bd67d191af4b4dea138c5757f2079bca8e55a30c 1673 Sources/Rev28Core/Identity/ProcessCodeIdentity.swift
e9a6a82672dc0d1d2eb2b5dbff47b878bd7eb625a7d6c6fee915e23f985b7edf 8939 Sources/Rev28Core/Identity/WindowIdentity.swift
c4a7407032a022efb2450dcace65c693100b2984924f502d9160b876fde61929 29105 Sources/Rev28Core/Observation/NativeObservationSession.swift
260ad5634dd86783a9d74a063eb598f17c1ffb361328347cf106499a4cb5e240 11963 Sources/Rev28Core/Perception/AlbumEllipsisLocator.swift
d0dcab179db7311853857eeaf065339eb4f74c64976dd2b5104ef9fa280cec00 28952 Sources/Rev28Core/Perception/OcrEngine.swift
f2e1b53a32ae2319f2d007855fab935a8e2992e8760e4228dffc9b75b9455127 13525 Sources/Rev28Core/Perception/StructuralLocators.swift
154a8c4a470bd76f6d401f9b85c51b51c9efe0851133f20e005b28a3025a3f14 7016 Sources/Rev28Core/Policy/ExecutionPolicy.swift
9a62c41d80c77fc1ccae05933c39c52218a86f80c51118864e5075ed75fe34a1 13521 Sources/Rev28Core/Postcondition/PostconditionMonitor.swift
2ca55edd625d6656ddeb41e66690ce3069ff07ab945d6211b654931002d55025 10408 Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift
de4a9f86a97f76813d866959559fcccb245d826fb189f877ba67207ed0b829a4 31820 Sources/Rev28Core/Sensor/FrameCapture.swift
b738df79817441240804531c033ab87f8be5b0dec78fd6683a3aa4a7c7162e3c 8716 Sources/Rev28Core/Sensor/RunEpochAuthority.swift
46e657fa73a6c70f0bc6cd0b7fec3de01f28ae73bec5d9e2321cff5d4bc7454c 5433 Sources/Rev28Core/Sensor/WindowSensor.swift
b721640fbc07c43dc283b1d34824fa69768c66423fcd3fa0e4783296a9c556f9 10279 Sources/Rev28Core/Transaction/FilesystemTripwireJournal.swift
ade90b545e73322af583ba7fc7669c2be51fad2b6e512863c1a470414eae1a1f 9822 Sources/Rev28Core/Transaction/GoalSlot.swift
3f50ec9d1b2b81866f185c493a880fa0480f2d8badac8f3be6eb790ea5883260 24858 Sources/Rev28Core/Transaction/IntentLedger.swift
22963b60bbd54a8df890b2d7558564e9980bd8d267095af78332ba8fea1c16cf 17470 Sources/Rev28Core/Transaction/LiveExecutionEngine.swift
ee539a585410cb7f4c2ed0cc9bb5b3c5b047088ae97c36c1038ed4e82d93333a 31013 Sources/Rev28Core/Transaction/PersistentTransactionOwner.swift
444038f10f8d9b341b6bd3c51156854b2fb130e5636091a7def94f19930b1fd6 22990 Sources/Rev28Core/Transaction/PhaseBEligibility.swift
95a28802e92abc1bb62b8d2ecadaf6d4deb0cab14f2e7b0fdb7b3b01ec049c78 7664 Sources/Rev28Core/Transaction/ReviewedBuildState.swift
fd9dd5a21fe011eb75690355db2ebeddbcc5c3937e9d3ea4c8b0950fd59b1802 4643 Sources/Rev28Core/Transaction/ReviewedImplementationDigest.swift
2ea1815031892930a5a43bac5f0f7f41b39821f934583a1bcf0cfc0c6e4fedbb 11758 Sources/Rev28Core/Transaction/StateEvidence.swift
8bd8fea6ec2eb153181cc936bc9fb35a4ebcfdf666d33d585433ba0d8d8c7917 6732 Sources/Rev28Core/Transaction/TripwireAttribution.swift
171f88a2eabfbb74d7192b36ff8b00cdce4ba68af370f05de249c06074990058 5810 Sources/Rev28Core/Verification/BaselineVerifier.swift
d93f068d0747524ad654ab79a4b9c497628ac1daa89b45b90c49e62be5cdd208 10691 Sources/Rev28Core/Verification/StagingVerifier.swift
11ad1889ff3d82911e87b94d7e653e4678e39be62fe2830fa73f5c3973bae81c 3652 Sources/rev28ctl/EvidenceRun.swift
4bf99db5ce820e185b101179223a64120da65128119f8a0411ab69d858decec0 4526 Sources/rev28ctl/FolderChooserDriver.swift
4a3fe1c4944904a2f1a174b274fc937914dee64a5e163a0cf5a4c17e78c6d860 143034 Sources/rev28ctl/HarnessCalibration.swift
b32029b10c9d9611656b4a1fe1debb504233b5cf8f98f8453f886edaa7f88ecc 8128 Sources/rev28ctl/PassiveCaptureDiagnostic.swift
97116b4e399dc31b6528ce83425b23937b719dfb2a39c291e3f25020f9f52cb3 975 Sources/rev28ctl/ProcessIdentity.swift
3167f8b33af5f4370d95b53cc9e4d77d9bb07a745fed844ee423fc158864b5c0 4719 Sources/rev28ctl/ProcessPeer.swift
e956d4e0073cd9d5b9f0a068753be8ead2122e525b5eb349e13e0dc222c34c4c 2617 Sources/rev28ctl/QuartzActuator.swift
3228444e510eb45f88e3c6128b50d102832af939144469e3c789847e4ab8f38f 2554 Sources/rev28ctl/RawCapture.swift
e00acabe3b1a85576fb1cc4f5bfe350a7cdfeb080ffd32125aca171d81d5d9cd 3688 Sources/rev28ctl/RestartFixture.swift
51a01b168336b271d8dfceba49aef28f3236c8e24d420fa586b13dac6c8904a7 85630 Sources/rev28ctl/main.swift
49cdd5c6ac3da82b4085e2483badc219a11cb128c9d53e1f3817291edd895628 24943 Sources/rev28harness/HarnessApp.swift
d4604a32c10e1db995eb5f106637c1346319dc5fb35183c1dbcf7101b6e4c819 172 Sources/rev28harness/main.swift
e4e9376ea5814d66be6d0f46092abcb9905942fb57107908189e783648dce5c5 10289 Sources/rev28occluder/main.swift
beb5fbec0fe32f911623df1e9611ce3c4c8e2bde377a5dceafbb9790e9c819a8 12745 Sources/rev28probe/CapabilityProbe.swift
9f837a00affe1a8f0b475ca10ea488e161f7ffc796d78d1fc3e0ca2f9439931b 582 Sources/rev28probe/main.swift
cf44f4985826620f1ca7e9cc70d616b5c75755fec57b5ea282f19440be6120d3 7097 Sources/rev28replay/main.swift
a12de00ebd4c7c41f946ce8ee98942fa5ae126f13446d92cbe2b1c2e0f65f6be 3784 Tests/Rev28CoreTests/AXWindowIdentitySelectorTests.swift
d3825b625fc8444e980df1f77c839a5c5a2224932927529c587ebbf628b35187 32079 Tests/Rev28CoreTests/ActuationReadinessTests.swift
dee7a2a134e5a20d08c3e8e9dff0b897704fead81fac70e2760ed0cdd5302fea 24466 Tests/Rev28CoreTests/AdversarialMatrixTests.swift
acdb3e39570d4ee025fc82e3b0b22b443025d0a131506aa7a5201a490ca43f48 11158 Tests/Rev28CoreTests/AlbumEllipsisLocatorTests.swift
3a54327ec86f746fe3f66a059a10f18ad890a633a0435456d535c5d4ba8300a5 6021 Tests/Rev28CoreTests/ChooserPredicateProductionDerivationTests.swift
dc18fe266c83a9c7884894456a87f51bc5fd6847ccef11dff40b1ec26f91bae8 44104 Tests/Rev28CoreTests/ComposedAdaptersTests.swift
8ce4ad926019d5e5d314d544eb6cf9414ecd570e8803087b2bb680dc56e21a31 13242 Tests/Rev28CoreTests/CoordinateTransformTests.swift
a712a78dd66206f4ce92e26eb2eaff9731c3411cf0c1836ddb310b20f11c0f8f 6251 Tests/Rev28CoreTests/EligibilityTestSupport.swift
c924059b0f4b43c48a132b7ec736eeed8efba19805173de0043d789922591160 3245 Tests/Rev28CoreTests/ExecutionPolicyTests.swift
9e3515d63c3158ec4734c825bc890d36ce0b0a1b40657202a6b914a22df11cc3 3228 Tests/Rev28CoreTests/FrameSupportGrantProfileTests.swift
d899b50bbc87f8822a0f224bd3e1b75f120eb68d05b4c00908face938924a773 2664 Tests/Rev28CoreTests/FrameSupportTests.swift
8f636662c285dec42da5627372d3a014b82d6684ac17bc22928935bfc0421ca1 9252 Tests/Rev28CoreTests/GoalSlotTests.swift
32785f06c7458342a9ff7f9c0d5c14abeb960cbbef42f858a91db935f3313913 7029 Tests/Rev28CoreTests/IntentLedgerTests.swift
6574abc9b9bd3e262efc675748d550793b120cfb06b3cd9735d820b40ead029e 10816 Tests/Rev28CoreTests/LiveCompositionTests.swift
f10d2bb1fc77877d0cfe8419784bf57f14a22ee03a14a49414a84f3941b52d35 22832 Tests/Rev28CoreTests/LiveExecutionEngineTests.swift
628c0981a943e55d5f77b2a031e42caa1f04074b1d66ae04a39f778fd72cf696 32738 Tests/Rev28CoreTests/NativeObservationSessionTests.swift
713f387ea52577cc05d733cd07d2d0b59546d67df5df4b0b612e4543bae80b9e 24933 Tests/Rev28CoreTests/NativeObservationTestSupport.swift
a43b88bd76f850ced2a0a6bf4ac3a89386c87240c0b564b6bddf6b4a14c164b3 6027 Tests/Rev28CoreTests/OcrEngineTests.swift
50353604d054502a65d11375a1ea73b6380d922687f6e697ae14399e865b4790 14673 Tests/Rev28CoreTests/PersistentTransactionOwnerTests.swift
1c2c8e5188e7ad080efd636aa65d259cf69637c7a4e72381c92775999e1c88d5 33170 Tests/Rev28CoreTests/PhaseAEvidenceTests.swift
df9aabf5281fccc8694441f3fe6aacbfe159504d0c473a047b42df1a119cdd26 26152 Tests/Rev28CoreTests/PhaseBEligibilityTests.swift
9cd79315e82da5ae6c376dce3d570d2b7e6697c9941d189ad9463d9b03eefe3e 7854 Tests/Rev28CoreTests/PostconditionMonitorTests.swift
2766e2de9e265d9679097feb5517d3118a612f6f1ce7e1c05e214d261aeebcd0 1258 Tests/Rev28CoreTests/ProcessCodeIdentityTests.swift
3b39e940abc0fe1f224845f4fd173385d9bfb5542602ba0ba4ae6f32189dc1ab 8396 Tests/Rev28CoreTests/ProjectBackupBindingTests.swift
e78b97f6f79be479338aec3eb39a40be695861406a6f94c28f60fa0ac054b719 7399 Tests/Rev28CoreTests/ReviewedBuildStateTests.swift
094091fa9af19418a9579acd29fca5deb9bf6d822a23329736e82e72460fca79 2533 Tests/Rev28CoreTests/RunEpochAuthorityTests.swift
4017da7b5ce0e04af745bb047bf943aab7645a522907f1e09460d128973d8b5c 11896 Tests/Rev28CoreTests/StagingVerifierTests.swift
5c977d4835b7f6d70254c6a76570f81f392e5442e3c7d53fda508f983b1adc34 11241 Tests/Rev28CoreTests/StructuralLocatorsTests.swift
cb67b72997eecedb71edc1b4b5e1b06acc086154c03ba9a0e47a946c65dae194 4819 Tests/Rev28CoreTests/TripwirePostDispatchGateTests.swift
2911a962ca2ebcdfd3f5bef8eaccb41a8f6536d5e64f0e73b4144ea5d73da6a7 7433 Tests/Rev28CoreTests/WindowIdentityTests.swift
```
