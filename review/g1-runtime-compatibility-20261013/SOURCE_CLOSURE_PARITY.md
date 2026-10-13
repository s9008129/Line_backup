# Swift source closure parity

**Scope:** PR7's isolated Swift package source closure only. This does not establish runtime binding, producer execution, GUI authorization, or live evidence.

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES, isolated PR7 candidate; three source paths only |
| `SOURCE_VALIDATED` | PARTIAL: original source provenance, exact-byte parity, and static dependency diff reviewed; candidate has not compiled |
| `OFFLINE_BUILD_PASS` | NO; the one authorized Swift invocation stopped before package-source compilation (see `SWIFT_BUILD_VERIFICATION.md`) |
| `RUNTIME_BOUND` | NOT_VERIFIED |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |

## Finding and bounded correction

PR7 source head before this correction was `d760e2c930a22f3951aa7e4b44233a3668b24851`; it is based on the reviewed PR3 source branch. Its `FrameCapture.swift` references `ExplicitLineSelectionWitness` at line 113 and invokes `ExplicitLineCaptureSelection` in the explicit LINE capture path. The class of witness is a real Codable/Equatable/Sendable value type with selected window IDs, display snapshot, source/filter rectangles, scale, and child/menu flags. Its adjacent validator performs fixed-target checks, unique LINE window selection, fresh inventory equality, display containment, frozen rulebook validation, effective-request binding, witness and scale checks, and retained geometry recomputation. It was not replaced by a placeholder and no fields or refusal conditions were removed.

The helper also relied on `PassiveNativeDiagnostic.lineBundleID`. That diagnostic source file is not in PR7 and is not otherwise referenced by PR7's source/test tree. The correction adds the same fixed literal `jp.naver.line.mac` as an internal constant on the existing `ObservationTarget` type and uses it in the helper and `FrameCapture`. This keeps exact LINE identity fail-closed without importing the larger diagnostic module. The package manifest already uses SwiftPM's automatic sources for `Sources/Rev28Core`; it has no source exclusion or build-flag change.

The source diff is limited to:

| Path | Change |
|---|---|
| `rev28/Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift` | Add the existing 148-line selector/witness validator. Its only content adjustment is the fixed identity reference. Candidate SHA-256 `2ca55edd625d6656ddeb41e66690ce3069ff07ab945d6211b654931002d55025` (10,408 bytes); original local source SHA-256 `5662baca0285f45859ac918d064ed404c6f14d528c4382a7598c4b2d86933e6c` (10,414 bytes). |
| `rev28/Sources/Rev28Core/Observation/NativeObservationSession.swift` | Add internal `ObservationTarget.lineBundleID = "jp.naver.line.mac"`. |
| `rev28/Sources/Rev28Core/Sensor/FrameCapture.swift` | Route the existing target check through `ObservationTarget.lineBundleID`. |

No package manifest, grant profile, authority guard, test source, `main.swift`, AX/capture flow, or runtime-binding data changed. `git diff --check` passed. The source hunk comparison and manifest were independently reviewed by Sol before the single build invocation.

## A/B/C parity and provenance

Labels: **A** is PR7's committed package source before this patch; **B** is the original dirty Mac `rev28` working source; **C** is the prior failed-build scratch copy. Hashes below identify exact files; `absent` means the path is not part of that source tree.

| Relative path | A: PR7 | B: original workspace | C: failed snapshot |
|---|---|---|---|
| `Package.swift` | `f9cefa31739ce6667e850461deefe7336b82df09de6bf204f784c666be26cc57` | same | same |
| `Sources/Rev28Core/Sensor/FrameCapture.swift` | `10b6596871d7bfc05d203ac7041a2b917d851fd7345355f1c4c9a142d568cc7e` | same | same |
| `Sources/Rev28Core/Observation/NativeObservationSession.swift` | `10178d2c0f8699fa7837358a6400bce744c6dc753aab324a5927141df702cbc2` | `9230ec99679badd7cad01d53c0c4d9811db6cd149f1aa42b0b98a3c34885e4c2` | same as B |
| `Sources/rev28ctl/main.swift` | `51a01b168336b271d8dfceba49aef28f3236c8e24d420fa586b13dac6c8904a7` | `0c67f1df199c27ea3466ef922abb60b33182c1aca50b8be7c84d25d71223d586` | `ad168dd3fa0b478746742dda4465b3467af8b37d5f3c5e98d17d2dc4cc4ca6ed` |
| `Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift` | absent before correction | `5662baca0285f45859ac918d064ed404c6f14d528c4382a7598c4b2d86933e6c` | same as B |
| `Tests/Rev28CoreTests/ExplicitLineCaptureSelectionTests.swift` | absent | `28f3946f970e3d94a35fbaa9d49336a7fa37b2e372bad90c944e84907d5e5e5a` | same as B |
| `Sources/Rev28Core/Observation/PassiveContextObservation.swift` | absent | `7803cd6b88987465c42430891906e166c14a204b3f41bbac24801f1540fc49d3` | same as B |
| `Sources/Rev28Core/Composition/PassiveNativeDiagnostic.swift` | absent | `e7b1a2546de758d87c349b0800e8626f84115bedd412a69c45aaaa71cecb7ee4` | same as B |
| `Sources/Rev28Core/Perception/AlbumVisualWitness.swift` | absent | `0ffc5d42f1dadda48cb1c239ec591c0d2e332c04c334a6c485def77d7c044213` | same as B |

An earlier ML07 implementation-only handoff identifies the selector as a pre-existing untracked Swift dependency and states that no clean-checkout build had been validated. The bounded historical `rev28-explicit-window-plan` describes this file as the pure selection/witness validator; a retained `focused-02.log` records it compiling and its `ExplicitLineCaptureSelectionTests` passing in that prior workspace. This is prior plan/test provenance, not a Git commit for the bytes, not a clean-clone build, and not formal independent acceptance of the current hash. Sol read the full source and approved this narrow closure; the external Chief's later review remains pending.

The local dirty B `main.swift` includes a `native-context` command branch that calls `PassiveContextObservation.capture`; that local candidate therefore needs the untracked `PassiveContextObservation.swift` source. PR7's A `main.swift` has no such command and A's source/test tree contains no references to `PassiveContextObservation`, `PassiveNativeDiagnostic`, or `AlbumVisualWitness` except the single identity reference addressed above. These files are intentionally excluded. The prior scratch build's `PassiveContextObservation` compiler diagnostics are therefore still unrepaired and are not evidence about the PR7 selected closure. This patch aims for the reviewed PR7 source closure only; **full Mac-workspace parity is NO**.

## Complete Swift source-input manifest

The manifest covers `Package.swift` and every regular file under `Sources/` and `Tests/` in `rev28` after the code correction. For each file, the canonical record is `{path: relative to rev28, bytes: file length, sha256: SHA-256(file bytes)}`. Records are lexically sorted by `path`, encoded as compact UTF-8 JSON with sorted object keys and separators `,` and `:`. It contains **86 entries**, **1,324,693 source bytes**, and **12,884 manifest JSON bytes**; manifest SHA-256 is `0c340e17e49fd388c24b0bd270b74b50330035b4bbc99a6154865ff165993c33`. This is the complete source/test input identity used for the one build attempt; no package source changed after it was computed.

The file list and per-file hashes represented by that manifest are:

```text
f9cefa31739ce6667e850461deefe7336b82df09de6bf204f784c666be26cc57 1972 Package.swift
94590f9a7c2ca5766e68c82ff9731cfbf9d8eeb4debc4e548372a47b80450e26 11360 Sources/Rev28Core/Actuation/AXDriver.swift
bf7bfb4d9dc3db108e962649a110dd40c999286c1398745480d1a6ff44e3b9f8 31626 Sources/Rev28Core/Actuation/QuartzActuator.swift
ecbdd6bb5ee806ed9a061c4b317747af980ac5ce0428065935bb34f461af8248 20392 Sources/Rev28Core/Chooser/ChooserAffirmationPredicate.swift
4602d0ad941cf276ecf9b6601bb0f422aee7a20894b6aaf59c0f4d880ac15bbc 25392 Sources/Rev28Core/Chooser/FolderChooserDriver.swift
e0c2282998d445adb438384835ea92c41779ae8ec73faf895fb10649c60cc688 17645 Sources/Rev28Core/Composition/ComposedNativeAdapter.swift
f0b8feb4a214812187febfaa7c2d4b770319a4823a2a5f81f1a4678699564956 8473 Sources/Rev28Core/Composition/LiveComposition.swift
e56df8319aa49255b5a9f6bb4f942db0e6a887f1e331044c6899bd1f9e96a016 46672 Sources/Rev28Core/Composition/PhaseAEvidence.swift
165f184467f2e92bad7848303dbb56ab48e482f902b2a3e472e787fabe5d9c3f 36531 Sources/Rev28Core/Composition/PostSaveComposition.swift
6d1f85ea488647de2116b29d08d7c4c3e5e6b1197e2dbd617d872de0dbe5ff2b 18972 Sources/Rev28Core/Composition/PostSaveEnvironment.swift
3e9932d1a50e2fc19f60fbd10e6bdb73c3f0544c3cb8078b98f5f81ee00e2b0c 1358 Sources/Rev28Core/Composition/ProductionActuationEnvironment.swift
6ad50045238cad28bd98fd77601872b5760e0e81aa1bf564908b8936e5bb5348 5750 Sources/Rev28Core/Composition/ProductionObservationSource.swift
e80a554e9ba8f52c447b6fcae2b107166deac79846a9801b626300241ac59258 33979 Sources/Rev28Core/Composition/ProjectBackupBinding.swift
93db7d0968cf99a94526de498d680d614e9a63822aba739591a65fa7d360d107 6609 Sources/Rev28Core/Diagnostics/DiagnosticHooks.swift
f3b6486de517e7d5405b38696c96c0c8194ac2280d9a2ef364eb639d6b41bb77 3951 Sources/Rev28Core/FrameSupportGrantProfile.swift
f9b77879cfc7abf596de4f0ab562ba8e7506bde2673844a94d37d96b4b0d564c 14431 Sources/Rev28Core/Geometry/Coordinates.swift
c1ae64a0cb942b5fe636e95c0407cba02387a8c44ef67d5cd05dc6afe49a7896 3637 Sources/Rev28Core/Identity/AXWindowIdentitySelector.swift
14e3b0d5d660c19550700cb6bd67d191af4b4dea138c5757f2079bca8e55a30c 1673 Sources/Rev28Core/Identity/ProcessCodeIdentity.swift
e9a6a82672dc0d1d2eb2b5dbff47b878bd7eb625a7d6c6fee915e23f985b7edf 8939 Sources/Rev28Core/Identity/WindowIdentity.swift
10178d2c0f8699fa7837358a6400bce744c6dc753aab324a5927141df702cbc2 26946 Sources/Rev28Core/Observation/NativeObservationSession.swift
260ad5634dd86783a9d74a063eb598f17c1ffb361328347cf106499a4cb5e240 11963 Sources/Rev28Core/Perception/AlbumEllipsisLocator.swift
d0dcab179db7311853857eeaf065339eb4f74c64976dd2b5104ef9fa280cec00 28952 Sources/Rev28Core/Perception/OcrEngine.swift
f2e1b53a32ae2319f2d007855fab935a8e2992e8760e4228dffc9b75b9455127 13525 Sources/Rev28Core/Perception/StructuralLocators.swift
154a8c4a470bd76f6d401f9b85c51b51c9efe0851133f20e005b28a3025a3f14 7016 Sources/Rev28Core/Policy/ExecutionPolicy.swift
9a62c41d80c77fc1ccae05933c39c52218a86f80c51118864e5075ed75fe34a1 13521 Sources/Rev28Core/Postcondition/PostconditionMonitor.swift
2ca55edd625d6656ddeb41e66690ce3069ff07ab945d6211b654931002d55025 10408 Sources/Rev28Core/Sensor/ExplicitLineCaptureSelection.swift
de4a9f86a97f76813d866959559fcccb245d826fb189f877ba67207ed0b829a4 31820 Sources/Rev28Core/Sensor/FrameCapture.swift
5bde1fc85cf2fe12a0fb18961a0ff8d118cdddc58e80777de9fd89b7fdc95682 4101 Sources/Rev28Core/Sensor/RunEpochAuthority.swift
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
