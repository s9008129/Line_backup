import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

// MARK: - Native composition matrix (plan R4 §C2/C5, TEST_ORDER step 4)
//
// Every case below drives the one production composition: the real
// LiveExecutionEngine state machine, the real NativeObservationSession evidence
// pipeline, the real PersistentTransactionOwner/IntentLedger authority, the
// real readiness gate, the real StrictPostconditionMonitor and the real
// StagingVerifier/BaselineVerifier. Only the OS-edge boundaries (sensors,
// clock, event sink, chooser surface, filesystem scan) are scripted by
// NativeCompositionTestFixture. No test here launches LINE, captures a real
// LINE window, posts a real system event or touches frozen evidence artifacts.

final class NativeCompositionMatrixTests: XCTestCase {
    private static let preSaveStates: [ExecutionState] = [
        .appReady,
        .groupReady,
        .albumListReady,
        .targetAlbumLocated,
        .albumDetailVerified,
        .ellipsisLocated,
        .menuVerified,
        .saveAllLocated,
    ]

    // MARK: - Small assertion helpers

    private func ledgerCount(_ fixture: CompositionFixture, _ kind: String) -> Int {
        fixture.ledger.count(kind: kind)
    }

    private func assertNoIrreversibleIntent(
        _ fixture: CompositionFixture,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 0, "saveAll intent/attempt", file: file, line: line)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 0, "confirmation intent/attempt", file: file, line: line)
        XCTAssertEqual(self.ledgerCount(fixture, "intent.saveAll"), 0, file: file, line: line)
        XCTAssertEqual(self.ledgerCount(fixture, "attempt.saveAll"), 0, file: file, line: line)
        XCTAssertEqual(self.ledgerCount(fixture, "intent.destinationConfirmation"), 0, file: file, line: line)
        XCTAssertEqual(self.ledgerCount(fixture, "attempt.destinationConfirmation"), 0, file: file, line: line)
    }

    private func assertEventFree(
        _ fixture: CompositionFixture,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 0, "mouseMoved events", file: file, line: line)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 0, "button events", file: file, line: line)
    }

    private func assertNoStateEvidence(
        _ fixture: CompositionFixture,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        let files = (try? fixture.evidenceFiles(matching: "native-state-")) ?? []
        XCTAssertTrue(files.isEmpty, "expected no state artifacts, saw \(files.map(\.lastPathComponent))", file: file, line: line)
    }

    private func failure(
        _ body: () async throws -> Void,
        file: StaticString = #filePath,
        line: UInt = #line
    ) async -> Error {
        do {
            try await body()
            XCTFail("expected a refusal but the call succeeded", file: file, line: line)
            return ScriptedCompositionError.detail("no refusal observed")
        } catch {
            return error
        }
    }

    private func expectDispatchRefused(
        _ error: Error,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .dispatchRefused(reason) = native else {
            XCTFail("expected NativeAdapterError.dispatchRefused, got \(error)", file: file, line: line)
            return
        }
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    private func expectStateRefused(
        _ error: Error,
        state: String,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .stateRefused(rejected, reason) = native else {
            XCTFail("expected NativeAdapterError.stateRefused, got \(error)", file: file, line: line)
            return
        }
        XCTAssertEqual(rejected, state, file: file, line: line)
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    private func expectChooserTerminal(
        _ error: Error,
        named name: String,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .chooserTerminal(outcome) = native else {
            XCTFail("expected NativeAdapterError.chooserTerminal, got \(error)", file: file, line: line)
            return
        }
        XCTAssertEqual(outcome, name, file: file, line: line)
    }

    private func expectDestinationRefused(
        _ error: Error,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .destinationRefused(reason) = native else {
            XCTFail("expected NativeAdapterError.destinationRefused, got \(error)", file: file, line: line)
            return
        }
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    private func expectBaselineRefused(
        _ error: Error,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .baselineRefused(reason) = native else {
            XCTFail("expected NativeAdapterError.baselineRefused, got \(error)", file: file, line: line)
            return
        }
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    private func expectStagingTerminal(
        _ error: Error,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let native = error as? NativeAdapterError, case let .stagingTerminal(reason) = native else {
            XCTFail("expected NativeAdapterError.stagingTerminal, got \(error)", file: file, line: line)
            return
        }
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    private func expectPermitRefused(
        _ error: Error,
        containing fragment: String = "",
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard let quartz = error as? QuartzActuatorError, case let .dispatchRefusedByPrecondition(reason) = quartz else {
            XCTFail("expected QuartzActuatorError.dispatchRefusedByPrecondition, got \(error)", file: file, line: line)
            return
        }
        if !fragment.isEmpty {
            XCTAssertTrue(reason.contains(fragment), "reason '\(reason)' does not contain '\(fragment)'", file: file, line: line)
        }
    }

    // MARK: - Drive helpers

    /// Establishes pre-Save-All states through the production adapter until
    /// `last` (inclusive), recording the real state transitions.
    private func establishPreSaveStates(
        _ fixture: CompositionFixture,
        upToAndIncluding last: ExecutionState
    ) async throws {
        for state in Self.preSaveStates {
            let evidence = try await fixture.adapter.establish(state: state, owner: fixture.owner)
            if state == .appReady {
                try fixture.owner.initializeState(evidenceSHA256: evidence)
            } else {
                try fixture.owner.transition(to: state, evidenceSHA256: evidence)
            }
            if state == last { break }
        }
    }

    /// Manual drive of the irreversible boundary and the chooser verdict.
    @discardableResult
    private func driveThroughChooser(_ fixture: CompositionFixture) async throws -> LiveChooserEvidence {
        _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner)
        let chooser = try await fixture.adapter.observeChooser(owner: fixture.owner)
        // The engine records the verified chooser on the owner before any
        // destination work; manual drives must mirror that boundary.
        try fixture.owner.recordChooserVerified(
            postconditionEvidence: chooser.postcondition,
            tripwireEvidence: chooser.tripwire
        )
        return chooser
    }

    /// Manual drive of everything after the pre-Save-All states, mirroring the
    /// engine order, and returns the content evidence.
    @discardableResult
    private func drivePostSaveAll(_ fixture: CompositionFixture) async throws -> LiveContentEvidence {
        _ = try await driveThroughChooser(fixture)
        _ = try await fixture.adapter.prepareDestination(owner: fixture.owner)
        _ = try await fixture.adapter.confirmDestination(owner: fixture.owner)
        _ = try await fixture.adapter.observeDownloadStarted(owner: fixture.owner)
        _ = try await fixture.adapter.observeDownloadInProgress(owner: fixture.owner)
        _ = try await fixture.adapter.observeFilesystemStable(owner: fixture.owner)
        return try await fixture.adapter.verifyContent(owner: fixture.owner)
    }

    private func stateName(fromStateArtifact name: String) -> String? {
        let prefix = "native-state-"
        guard name.hasPrefix(prefix) else { return nil }
        return name.dropFirst(prefix.count).split(separator: "-").first.map(String.init)
    }

    // MARK: - Closed loop

    func testClosedLoopHappyPathVerifiesContentWithIndependentCounts() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let outcome = try await fixture.makeEngine().run()

        guard case let .contentVerified(verification) = outcome else {
            return XCTFail("expected contentVerified, got \(outcome)")
        }
        XCTAssertEqual(verification.outcome, .duplicateContentConfirmed)
        XCTAssertEqual(verification.fileCount, StagingPolicy.rev28Accepted.expectedFileCount)
        XCTAssertEqual(verification.totalBytes, StagingPolicy.rev28Accepted.expectedTotalBytes)
        XCTAssertEqual(verification.contentMultisetSHA256, StagingPolicy.rev28Accepted.expectedContentMultisetSHA256)
        XCTAssertEqual(fixture.owner.currentState, .contentVerified)

        // Ledger authority: exactly one intent+attempt at each irreversible
        // boundary, and the reversible budget consumed by the reviewed path.
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(ledgerCount(fixture, "intent.saveAll"), 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.saveAll"), 1)
        XCTAssertEqual(ledgerCount(fixture, "intent.destinationConfirmation"), 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.destinationConfirmation"), 1)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 5)
        XCTAssertEqual(ledgerCount(fixture, "postcondition.chooserVerified"), 1)
        XCTAssertEqual(ledgerCount(fixture, "state.transition"), 14)

        // Independent counting sink: 3 clicks (album card, album menu, Save
        // All) = 3 mouseMoved + 6 button events, and exactly one chooser press.
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 3)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 6)
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
        XCTAssertEqual(fixture.chooser.preDispatchCalls, 1)
        XCTAssertEqual(fixture.chooser.primitiveCalls, 3)
        XCTAssertEqual(fixture.chooser.panelBoundCalls, 6)
        XCTAssertEqual(fixture.chooser.sampleCalls, 1)

        XCTAssertEqual(fixture.observation.captureStates, [
            "APP_READY",
            "GROUP_READY",
            "ALBUM_LIST_READY",
            "TARGET_ALBUM_LOCATED",
            "ALBUM_DETAIL_VERIFIED",
            "ALBUM_DETAIL_VERIFIED",
            "ELLIPSIS_LOCATED",
            "MENU_VERIFIED",
            "SAVE_ALL_LOCATED",
            "SAVE_ALL_LOCATED",
            "DESTINATION_PREPARED",
            "DESTINATION_CONFIRMATION",
            "DOWNLOAD_CONFIRMED",
            "DOWNLOAD_IN_PROGRESS",
            "FILESYSTEM_STABLE",
        ])

        // Typed evidence: every recorded state artifact re-validates through
        // the store (run/plan/session binding + state name), plus the chooser,
        // content and retained-image artifacts exist for this run.
        // 8 pre-Save-All states + SAVE_ALL_DISPATCH + DESTINATION_PREPARED +
        // DESTINATION_CONFIRMATION + DOWNLOAD_CONFIRMED + DOWNLOAD_IN_PROGRESS +
        // FILESYSTEM_STABLE; verifyContent writes the content artifact, not a state.
        let stateArtifacts = try fixture.evidenceFiles(matching: "native-state-")
        XCTAssertEqual(stateArtifacts.count, 14)
        for artifact in stateArtifacts {
            let name = stateName(fromStateArtifact: artifact.lastPathComponent)
            let state = try XCTUnwrap(name, "unparsable artifact name \(artifact.lastPathComponent)")
            XCTAssertNoThrow(try fixture.store.verifyArtifact(fileURL: artifact, expectedState: state, expectedSHA256: nil))
        }
        XCTAssertEqual(try fixture.evidenceFiles(matching: "native-content-verification.json").count, 1)
        XCTAssertEqual(try fixture.evidenceFiles(matching: "native-postcondition.json").count, 1)
        XCTAssertEqual(try fixture.evidenceFiles(matching: "native-tripwire.json").count, 1)
        let retained = try FileManager.default.contentsOfDirectory(
            at: fixture.evidenceDirectory.appendingPathComponent("observations", isDirectory: true),
            includingPropertiesForKeys: nil
        )
        XCTAssertEqual(retained.count, 15)

        try IntentLedger.verifyHeadAnchor(fileURL: fixture.ledger.fileURL, anchorURL: fixture.ledgerAnchorURL)
    }

    func testClosedLoopWithRealScanningFilesystemAndBaselineImages() async throws {
        let fixture = try CompositionFixtureBuilder.build(realFilesystem: true)
        guard fixture.realImagesAvailable else {
            throw XCTSkip("baseline source image directory is unavailable on this machine")
        }
        try fixture.copyRealImagesIntoStaging()

        let outcome = try await fixture.makeEngine().run()
        guard case let .contentVerified(verification) = outcome else {
            return XCTFail("expected contentVerified over real files, got \(outcome)")
        }
        XCTAssertEqual(verification.outcome, .duplicateContentConfirmed)
        XCTAssertEqual(verification.fileCount, StagingPolicy.rev28Accepted.expectedFileCount)
        XCTAssertEqual(verification.totalBytes, StagingPolicy.rev28Accepted.expectedTotalBytes)
        XCTAssertEqual(verification.contentMultisetSHA256, StagingPolicy.rev28Accepted.expectedContentMultisetSHA256)
        XCTAssertEqual(fixture.owner.currentState, .contentVerified)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 3)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 6)
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.saveAll"), 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.destinationConfirmation"), 1)

        let scanner = try XCTUnwrap(fixture.filesystem as? RealScanningFilesystemBoundary)
        // One download-in-progress sample plus three contiguous equal-tail
        // samples reach stability; verifyContent reuses the stable tail.
        XCTAssertEqual(scanner.snapshotCallCount, 4)
        XCTAssertEqual(scanner.baselineCallCount, 2)
    }

    // MARK: - Every pre-Save-All state refusal

    func testEveryPreSaveAllStateRefusalIsEventFreeAndRecordsNoState() async throws {
        struct PreSaveRefusal {
            let state: ExecutionState
            let expectedMoves: Int
            let expectedCaptures: Int
            let fragment: String
            let mutate: (CompositionFixture) -> Void
        }
        let refusals: [PreSaveRefusal] = [
            PreSaveRefusal(state: .appReady, expectedMoves: 0, expectedCaptures: 1, fragment: "signing identity unavailable", mutate: { fixture in
                fixture.observation.signingIdentityValue = nil
            }),
            PreSaveRefusal(state: .groupReady, expectedMoves: 0, expectedCaptures: 2, fragment: "exact group title matches=0", mutate: { fixture in
                fixture.observation.ocrProvider = { _ in MatrixFrame.standardOcrItems(group: "別のグループ") }
            }),
            PreSaveRefusal(state: .albumListReady, expectedMoves: 0, expectedCaptures: 3, fragment: "no segmented album card regions", mutate: { fixture in
                fixture.observation.ocrProvider = { _ in MatrixFrame.standardOcrItems(album: "not-a-date-range") }
            }),
            PreSaveRefusal(state: .targetAlbumLocated, expectedMoves: 0, expectedCaptures: 4, fragment: "album card refused missingIdentity", mutate: { fixture in
                fixture.observation.ocrProvider = { _ in MatrixFrame.standardOcrItems(count: "99") }
            }),
            PreSaveRefusal(state: .albumDetailVerified, expectedMoves: 1, expectedCaptures: 6, fragment: "album detail group/count continuity not proven", mutate: { fixture in
                fixture.observation.ocrProvider = { _ in MatrixFrame.standardOcrItems(countText: "99張照片") }
            }),
            PreSaveRefusal(state: .ellipsisLocated, expectedMoves: 1, expectedCaptures: 7, fragment: "ellipsis refused missingIdentity", mutate: { fixture in
                fixture.observation.imageProvider = { _ in MatrixFrame.image(withEllipsisDots: false) }
            }),
            PreSaveRefusal(state: .menuVerified, expectedMoves: 2, expectedCaptures: 8, fragment: "menu row '選擇項目' exact matches=0", mutate: { fixture in
                fixture.observation.ocrProvider = { _ in MatrixFrame.standardOcrItems(includeMenuRows: false) }
            }),
            PreSaveRefusal(state: .saveAllLocated, expectedMoves: 2, expectedCaptures: 9, fragment: "target row has no addressable horizontal overlap", mutate: { fixture in
                // MENU_VERIFIED must still pass for this case, so the failure is
                // aimed at Save All geometry: the target row keeps its identity
                // and order but has no addressable horizontal overlap.
                fixture.observation.ocrProvider = { _ in
                    MatrixFrame.standardOcrItems().map { item in
                        guard item.text == "儲存全部" else { return item }
                        return MatrixFrame.ocrItem(item.text, box: CGRect(x: 40, y: 400, width: 4, height: 24))
                    }
                }
            }),
        ]

        for refusal in refusals {
            let fixture = try CompositionFixtureBuilder.build()
            refusal.mutate(fixture)
            let index = try XCTUnwrap(Self.preSaveStates.firstIndex(of: refusal.state))
            if index > 0 {
                try await establishPreSaveStates(fixture, upToAndIncluding: Self.preSaveStates[index - 1])
            }

            let error = await failure {
                _ = try await fixture.adapter.establish(state: refusal.state, owner: fixture.owner)
            }
            expectStateRefused(error, state: refusal.state.rawValue, containing: refusal.fragment)

            if index == 0 {
                XCTAssertNil(fixture.owner.currentState, "\(refusal.state)")
            } else {
                XCTAssertEqual(fixture.owner.currentState, Self.preSaveStates[index - 1], "\(refusal.state)")
            }
            assertNoIrreversibleIntent(fixture)
            XCTAssertEqual(fixture.actuation.mouseMovedCount, refusal.expectedMoves, "moves for \(refusal.state)")
            XCTAssertEqual(fixture.actuation.buttonEventCount, refusal.expectedMoves * 2, "buttons for \(refusal.state)")
            XCTAssertEqual(fixture.owner.reversibleDispatchCount, refusal.expectedMoves, "reversible for \(refusal.state)")
            XCTAssertEqual(fixture.observation.captureStates.count, refusal.expectedCaptures, "captures for \(refusal.state)")
            XCTAssertTrue(
                try fixture.evidenceFiles(matching: "native-state-\(refusal.state.rawValue)").isEmpty,
                "refused state \(refusal.state) must not persist evidence"
            )
            XCTAssertEqual(fixture.observation.lastRequestedState, refusal.state.rawValue)
        }
    }

    // MARK: - Observation freshness / census / frame refusals

    func testObservationFreshnessFailuresRefuseBeforeAnyStateEvidence() async throws {
        struct FreshnessCase {
            let fragment: String
            let mutate: (CompositionFixture) -> Void
        }
        let cases: [FreshnessCase] = [
            FreshnessCase(fragment: "windowNotInPostCensus", mutate: { $0.observation.omitWindowFromCensus = true }),
            FreshnessCase(fragment: "windowNotInPostCensus", mutate: { $0.observation.censusFrameOverride = MatrixFrame.windowFrame.offsetBy(dx: 5, dy: 0) }),
            FreshnessCase(fragment: "windowNotInPostCensus", mutate: { $0.observation.censusBundleIDOverride = "com.example.lookalike" }),
            FreshnessCase(fragment: "invalidFrame", mutate: { $0.observation.invalidFrame = true }),
            FreshnessCase(fragment: "captureDeadlineExceeded", mutate: { $0.observation.deadlineExceeded = true }),
            FreshnessCase(fragment: "observation refused", mutate: { $0.observation.captureFailure = ScriptedCompositionError.detail("scripted capture outage") }),
        ]

        for entry in cases {
            let fixture = try CompositionFixtureBuilder.build()
            entry.mutate(fixture)
            let error = await failure {
                _ = try await fixture.adapter.establish(state: .appReady, owner: fixture.owner)
            }
            expectStateRefused(error, state: "APP_READY", containing: entry.fragment)
            XCTAssertNil(fixture.owner.currentState)
            XCTAssertEqual(fixture.observation.captureStates.count, 1)
            assertNoIrreversibleIntent(fixture)
            assertEventFree(fixture)
            assertNoStateEvidence(fixture)
        }
    }

    // MARK: - Pre-dispatch gate and permit refusals (Save All)

    func testPreDispatchTripwireGateFalseYieldsZeroIrreversibleIntent() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        fixture.chooser.preDispatchSatisfied = false
        let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "pre-dispatch tripwire context")
        XCTAssertEqual(fixture.chooser.preDispatchCalls, 1)
        XCTAssertTrue(fixture.observation.captureStates.isEmpty)
        XCTAssertEqual(fixture.chooser.sampleCalls, 0)
        XCTAssertEqual(fixture.actuation.readinessCallCount, 0)
        XCTAssertEqual(fixture.scriptedFilesystem?.baselineCallCount, 0)
        assertNoIrreversibleIntent(fixture)
        assertEventFree(fixture)
        assertNoStateEvidence(fixture)
    }

    func testPermitRefusalsPostZeroEventsAndConsumeNoIntent() async throws {
        struct PermitCase {
            let fragment: String
            let mutate: (CompositionFixture) -> Void
        }
        let cases: [PermitCase] = [
            PermitCase(fragment: "application inactive", mutate: { $0.actuation.applicationActive = false }),
            PermitCase(fragment: "target not frontmost", mutate: { $0.actuation.targetFrontmost = false }),
            PermitCase(fragment: "stale window identity", mutate: { $0.actuation.epochOffset = 1 }),
            PermitCase(fragment: "readiness observation stale", mutate: { $0.actuation.readinessObservedAtSkewSeconds = -2 }),
            PermitCase(fragment: "unsafe candidate geometry", mutate: { $0.actuation.captureGeometryWindowFrameOverride = MatrixFrame.windowFrame.offsetBy(dx: 3, dy: 0) }),
        ]
        for entry in cases {
            let fixture = try CompositionFixtureBuilder.build()
            entry.mutate(fixture)
            let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
            expectPermitRefused(error, containing: entry.fragment)
            XCTAssertEqual(fixture.actuation.readinessCallCount, 1, entry.fragment)
            XCTAssertEqual(fixture.actuation.revalidateCallCount, 0, entry.fragment)
            XCTAssertEqual(fixture.observation.captureStates, ["SAVE_ALL_LOCATED"], entry.fragment)
            assertNoIrreversibleIntent(fixture)
            assertEventFree(fixture)
            assertNoStateEvidence(fixture)
        }
    }

    func testPostMoveFocusLossConsumesIntentWithZeroButtonEvents() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        fixture.actuation.revalidateResults = [true, false]
        let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "Save All dispatch refused")
        // Intent+attempt were durably recorded before the move; the down/up pair
        // was never posted and nothing is retried.
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(ledgerCount(fixture, "intent.saveAll"), 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.saveAll"), 1)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 1)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 0)
        XCTAssertEqual(fixture.actuation.revalidateCallCount, 2)
        XCTAssertEqual(fixture.observation.captureStates, ["SAVE_ALL_LOCATED"])
        XCTAssertTrue(try fixture.evidenceFiles(matching: "native-state-").isEmpty)
        XCTAssertNil(fixture.owner.currentState)
    }

    func testPostMoveProcessChangeConsumesIntentWithZeroButtonEvents() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        fixture.actuation.processStableResults = [true, false]
        let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "Save All dispatch refused")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 1)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 0)
        XCTAssertEqual(fixture.actuation.processStableCallCount, 2)
    }

    func testPostEventAccessDenialRefusesBeforeIntentAndEvents() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        fixture.actuation.postEventAccessAllowed = false
        let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "postEventAccessDenied")
        assertNoIrreversibleIntent(fixture)
        assertEventFree(fixture)
        XCTAssertEqual(fixture.actuation.revalidateCallCount, 1)
        XCTAssertEqual(fixture.actuation.processStableCallCount, 1)
        assertNoStateEvidence(fixture)
    }

    // MARK: - Chooser verdict terminals

    func testChooserRefusalsProduceNamedTerminalsWithZeroFurtherInput() async throws {
        let expectations: [(ScriptedChooserBoundary.Script, String)] = [
            (.neverAffirm, "CHOOSER_REFUSED_NO_OBSERVATION"),
            (.fail("scripted observer outage"), "CHOOSER_OBSERVER_FAILED"),
            (.abortingTripwire, "TRIPWIRE_ABORTED"),
            (.affirmAfterDeadline, "CHOOSER_OBSERVED_AFTER_WINDOW"),
            (.stall, "CHOOSER_DEADLINE_EXCEEDED"),
        ]
        for (script, terminal) in expectations {
            let fixture = try CompositionFixtureBuilder.build()
            _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner)
            fixture.chooser.script = script
            let error = await failure { _ = try await fixture.adapter.observeChooser(owner: fixture.owner) }
            expectChooserTerminal(error, named: terminal)
            XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2, terminal)
            XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 0, terminal)
            XCTAssertNil(fixture.owner.currentState, terminal)
            XCTAssertEqual(fixture.chooser.primitiveCalls, 0, terminal)
            XCTAssertEqual(fixture.chooser.pressCalls, 0, terminal)
            XCTAssertEqual(fixture.actuation.mouseMovedCount, 1, terminal)
            XCTAssertEqual(fixture.actuation.buttonEventCount, 2, terminal)
            XCTAssertEqual(try fixture.evidenceFiles(matching: "native-chooser-terminal.json").count, 1, terminal)
            XCTAssertTrue(try fixture.evidenceFiles(matching: "native-postcondition.json").isEmpty, terminal)
            XCTAssertTrue(try fixture.evidenceFiles(matching: "native-tripwire.json").isEmpty, terminal)
        }
    }

    // MARK: - Destination preparation and the one confirmation

    func testDestinationPanelLossBeforeFirstPrimitiveIsFullyEventFree() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        fixture.chooser.panelBoundResults = [false]
        let error = await failure { _ = try await fixture.adapter.prepareDestination(owner: fixture.owner) }
        expectDestinationRefused(error, containing: "panel identity lost before primitive")
        XCTAssertEqual(fixture.chooser.primitiveCalls, 0)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 0)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 1)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 0)
    }

    func testDestinationPanelLossAfterPrimitivesKeepsReversibleNavigation() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        fixture.chooser.panelBoundResults = [true, true, true, false]
        let error = await failure { _ = try await fixture.adapter.prepareDestination(owner: fixture.owner) }
        expectDestinationRefused(error, containing: "panel identity lost after destination preparation")
        XCTAssertEqual(fixture.chooser.primitiveCalls, 3)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 3)
        XCTAssertEqual(fixture.chooser.panelBoundCalls, 4)
    }

    func testDestinationNotReflectedRefusesAfterReversibleNavigation() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        fixture.chooser.reflectedDestination = false
        let error = await failure { _ = try await fixture.adapter.prepareDestination(owner: fixture.owner) }
        expectDestinationRefused(error, containing: "reflected destination does not equal the authorized canonical staging path")
        XCTAssertEqual(fixture.chooser.primitiveCalls, 3)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 3)
    }

    func testDestinationPrimitiveRefusalStopsBeforeRemainingPrimitives() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        fixture.chooser.primitiveFailureAt = .pathEntry
        let error = await failure { _ = try await fixture.adapter.prepareDestination(owner: fixture.owner) }
        expectDestinationRefused(error, containing: "primitive pathEntry refused")
        // The reversible dispatch is recorded before the second primitive
        // (pathEntry) is invoked, and the invocation itself was attempted.
        XCTAssertEqual(fixture.chooser.primitiveCalls, 2)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 2)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 0)
    }

    func testConfirmationPreIntentReadinessLossLeavesZeroConfirmationIntent() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        _ = try await fixture.adapter.prepareDestination(owner: fixture.owner)
        fixture.chooser.panelBoundResults = [true, true, true, true, false]
        let error = await failure { _ = try await fixture.adapter.confirmDestination(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "destination confirmation refused")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(fixture.chooser.pressCalls, 0)
    }

    func testConfirmationReadinessLossAfterIntentConsumesWithoutPress() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        _ = try await fixture.adapter.prepareDestination(owner: fixture.owner)
        fixture.chooser.panelBoundResults = [true, true, true, true, true, false]
        let error = await failure { _ = try await fixture.adapter.confirmDestination(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "destination confirmation refused")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(ledgerCount(fixture, "intent.destinationConfirmation"), 1)
        XCTAssertEqual(ledgerCount(fixture, "attempt.destinationConfirmation"), 1)
        XCTAssertEqual(fixture.chooser.pressCalls, 0)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 2)

        // The consumed operation never retries: a second confirmation stays refused.
        let retry = await failure { _ = try await fixture.adapter.confirmDestination(owner: fixture.owner) }
        expectDispatchRefused(retry, containing: "destination confirmation refused")
        XCTAssertEqual(fixture.chooser.pressCalls, 0)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
    }

    func testPressFailureAfterIntentConsumesWithoutRetry() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await driveThroughChooser(fixture)
        _ = try await fixture.adapter.prepareDestination(owner: fixture.owner)
        fixture.chooser.pressFailure = ScriptedCompositionError.detail("scripted AXPress outage")
        let error = await failure { _ = try await fixture.adapter.confirmDestination(owner: fixture.owner) }
        expectDispatchRefused(error, containing: "destination confirmation refused")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
        let retry = await failure { _ = try await fixture.adapter.confirmDestination(owner: fixture.owner) }
        expectDispatchRefused(retry, containing: "destination confirmation refused")
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
    }

    // MARK: - Baseline, staging content and stability

    func testBaselineFailureAtDispatchRefusesWithZeroIrreversibleIntent() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let scripted = try XCTUnwrap(fixture.scriptedFilesystem)
        scripted.baselineFailureCalls = [1]
        let error = await failure { _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner) }
        expectBaselineRefused(error, containing: "SAVE_ALL_DISPATCH")
        assertNoIrreversibleIntent(fixture)
        assertEventFree(fixture)
        XCTAssertEqual(fixture.observation.captureStates, ["SAVE_ALL_LOCATED"])
        XCTAssertEqual(fixture.actuation.readinessCallCount, 0)
        XCTAssertEqual(scripted.baselineCallCount, 1)
        assertNoStateEvidence(fixture)
    }

    func testBaselineFailureAtContentDoesNotRedispatchOrReconfirm() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let scripted = try XCTUnwrap(fixture.scriptedFilesystem)
        scripted.baselineFailureCalls = [2]
        let error = await failure { _ = try await self.drivePostSaveAll(fixture) }
        expectBaselineRefused(error, containing: "baseline verification failed")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 1)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 2)
        XCTAssertEqual(scripted.baselineCallCount, 2)
        XCTAssertTrue(try fixture.evidenceFiles(matching: "native-content-verification.json").isEmpty)
    }

    func testStagingOutcomeVariantsAreRejectedWithoutFurtherIrreversibleInput() async throws {
        struct Variant {
            let name: String
            let outcome: StagingOutcome
            let sequence: (MatrixBaselineReference) -> [StagingSnapshot]
        }
        let variants: [Variant] = [
            Variant(name: "incomplete", outcome: .stagingIncomplete, sequence: { MatrixSnapshots.incompleteSnapshots($0) }),
            Variant(name: "extra-files", outcome: .stagingExtraFiles, sequence: { MatrixSnapshots.extraFilesSnapshots($0) }),
            Variant(name: "duplicate-hash", outcome: .stagingDuplicateContent, sequence: { MatrixSnapshots.duplicateContentHashSnapshots($0) }),
            Variant(name: "content-mismatch", outcome: .contentMismatchAgainstAcceptedBaseline, sequence: { MatrixSnapshots.contentMismatchSnapshots($0) }),
        ]
        for variant in variants {
            let fixture = try CompositionFixtureBuilder.build()
            let scripted = try XCTUnwrap(fixture.scriptedFilesystem)
            scripted.snapshotSequence = variant.sequence(fixture.baseline)
            let outcome = try await fixture.makeEngine().run()
            guard case let .contentRejected(verification) = outcome else {
                XCTFail("\(variant.name): expected contentRejected, got \(outcome)")
                continue
            }
            XCTAssertEqual(verification.outcome, variant.outcome, variant.name)
            XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2, variant.name)
            XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2, variant.name)
            XCTAssertEqual(fixture.chooser.pressCalls, 1, variant.name)
            XCTAssertEqual(fixture.actuation.mouseMovedCount, 3, variant.name)
            XCTAssertEqual(fixture.actuation.buttonEventCount, 6, variant.name)
            XCTAssertEqual(fixture.owner.currentState, .filesystemStable, variant.name)
            XCTAssertEqual(try fixture.evidenceFiles(matching: "native-content-verification.json").count, 1, variant.name)
        }
    }

    func testNeverStableStagingProducesNamedTerminalWithoutRedispatch() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        try XCTUnwrap(fixture.scriptedFilesystem).unstableAlways = true
        let error = await failure { _ = try await fixture.makeEngine().run() }
        expectStagingTerminal(error, containing: "STAGING_UNSTABLE")
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(fixture.chooser.pressCalls, 1)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, 3)
        XCTAssertEqual(fixture.actuation.buttonEventCount, 6)
        XCTAssertEqual(fixture.owner.currentState, .downloadInProgress)
    }

    // MARK: - Evidence tamper detection

    func testStateArtifactTamperIsDetectedOnReVerification() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let digest = try await fixture.adapter.establish(state: .appReady, owner: fixture.owner)
        try fixture.owner.initializeState(evidenceSHA256: digest)
        let artifacts = try fixture.evidenceFiles(matching: "native-state-APP_READY")
        XCTAssertEqual(artifacts.count, 1)
        let artifact = try XCTUnwrap(artifacts.first)
        XCTAssertNoThrow(try fixture.store.verifyArtifact(fileURL: artifact, expectedState: "APP_READY", expectedSHA256: digest))

        var tampered = try Data(contentsOf: artifact)
        tampered.append(Data("\n".utf8))
        try tampered.write(to: artifact)
        let error = await failure {
            _ = try fixture.store.verifyArtifact(fileURL: artifact, expectedState: "APP_READY", expectedSHA256: digest)
        }
        guard let native = error as? NativeEvidenceError, case .artifactTampered(_) = native else {
            return XCTFail("expected artifactTampered, got \(error)")
        }
    }

    func testRetainedImageTamperIsDetectedBeforeStateEvidenceIsWritten() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let bundle = try await fixture.session.observe(
            state: CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true),
            requestedState: "APP_READY"
        )
        let imageURL = URL(fileURLWithPath: bundle.retainedImagePath)
        XCTAssertTrue(FileManager.default.fileExists(atPath: imageURL.path))
        try Data("tampered".utf8).write(to: imageURL)
        let error = await failure { _ = try fixture.store.record(state: "APP_READY", bundle: bundle, facts: [:]) }
        guard let native = error as? NativeEvidenceError, case .retainedImageTampered(_) = native else {
            return XCTFail("expected retainedImageTampered, got \(error)")
        }
        assertNoStateEvidence(fixture)
    }

    // MARK: - Owner, restart, crash and goal-slot authority

    private func assertObserveOnlyRestart(
        _ fixture: CompositionFixture,
        expectedState: ExecutionState?,
        file: StaticString = #filePath,
        line: UInt = #line
    ) async throws {
        let second = try fixture.secondOwner()
        XCTAssertTrue(second.isObserveOnlyResume, file: file, line: line)
        let captures = fixture.observation.captureStates
        let moves = fixture.actuation.mouseMovedCount
        let buttons = fixture.actuation.buttonEventCount
        let presses = fixture.chooser.pressCalls
        // The restart owner appends through its own IntentLedger instance, so
        // read the file back instead of trusting the fixture's cached view.
        let ledgerSize = try IntentLedger(fileURL: fixture.ledger.fileURL).entries.count

        let outcome = try await fixture.makeEngine(owner: second).run()
        XCTAssertEqual(outcome, .observeOnlyResume(expectedState), file: file, line: line)
        XCTAssertEqual(fixture.observation.captureStates, captures, "restart made adapter observations", file: file, line: line)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, moves, file: file, line: line)
        XCTAssertEqual(fixture.actuation.buttonEventCount, buttons, file: file, line: line)
        XCTAssertEqual(fixture.chooser.pressCalls, presses, file: file, line: line)
        XCTAssertEqual(
            try IntentLedger(fileURL: fixture.ledger.fileURL).entries.count,
            ledgerSize,
            "restart appended ledger entries",
            file: file,
            line: line
        )
        XCTAssertThrowsError(try second.reserveSaveAll(), file: file, line: line)
    }

    func testRestartAfterSaveAllIntentOnlyIsObserveOnly() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        try fixture.owner.reserveSaveAll()
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 1)
        try await assertObserveOnlyRestart(fixture, expectedState: nil)
    }

    func testRestartAfterSaveAllIntentAndAttemptIsObserveOnly() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner)
        XCTAssertEqual(fixture.owner.irreversibleOperationCounts.saveAll, 2)
        try await assertObserveOnlyRestart(fixture, expectedState: nil)
    }

    func testRestartAfterFullClosedLoopIsObserveOnly() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        let outcome = try await fixture.makeEngine().run()
        guard case .contentVerified(_) = outcome else {
            return XCTFail("expected contentVerified, got \(outcome)")
        }
        try await assertObserveOnlyRestart(fixture, expectedState: .contentVerified)
    }

    func testSecondOwnerContinuesPreIntentHistoryWithReverification() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        try await establishPreSaveStates(fixture, upToAndIncluding: .menuVerified)
        XCTAssertEqual(fixture.owner.reversibleDispatchCount, 2)
        XCTAssertEqual(ledgerCount(fixture, "state.transition"), 7)

        let second = try fixture.secondOwner()
        XCTAssertFalse(second.isObserveOnlyResume)
        let outcome = try await fixture.makeEngine(owner: second).run()
        guard case .contentVerified(_) = outcome else {
            return XCTFail("expected contentVerified after pre-intent continuation, got \(outcome)")
        }
        XCTAssertEqual(second.currentState, .contentVerified)
        // The continuation owner writes through its own IntentLedger instance;
        // reload the ledger file for the final assertions.
        let finalLedger = try IntentLedger(fileURL: fixture.ledger.fileURL)
        XCTAssertEqual(finalLedger.count(kind: "state.reverified"), 1)
        XCTAssertEqual(
            finalLedger.entries.first(where: { $0.kind == "state.reverified" })?.payload["state"],
            ExecutionState.menuVerified.rawValue
        )
        XCTAssertEqual(finalLedger.count(kind: "state.transition"), 14)
        XCTAssertEqual(finalLedger.count(kind: "intent.saveAll"), 1)
        XCTAssertEqual(finalLedger.count(kind: "attempt.saveAll"), 1)
        XCTAssertEqual(finalLedger.count(kind: "intent.destinationConfirmation"), 1)
        XCTAssertEqual(finalLedger.count(kind: "attempt.destinationConfirmation"), 1)
        XCTAssertEqual(finalLedger.count(kind: "dispatch.reversible"), 5)
    }

    func testDifferentAuthorizationIsRefusedAgainstBoundLedger() async throws {
        let fixture = try CompositionFixtureBuilder.build()
        XCTAssertEqual(ledgerCount(fixture, "transaction.authorization"), 1)
        let other = ImmutableRunAuthorization(
            runID: "other-run",
            goal: fixture.authorization.goal,
            group: fixture.authorization.group,
            album: fixture.authorization.album,
            planSHA256: fixture.authorization.planSHA256,
            reviewedImplementationSHA256: fixture.authorization.reviewedImplementationSHA256,
            stagingRoot: fixture.stagingRoot,
            stagingRunDirectory: fixture.stagingRunDirectory
        )
        XCTAssertNotEqual(other.runID, fixture.authorization.runID)
        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: other,
            ledger: try IntentLedger(fileURL: fixture.ledger.fileURL),
            checkpointURL: fixture.ledgerAnchorURL
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .authorizationMismatch)
        }
    }

    func testGoalSlotEntitlementIsNotRearmableByNewLedgerOrRunID() async throws {
        let fixture = try CompositionFixtureBuilder.build(useGoalSlot: true)
        let slot = try XCTUnwrap(fixture.goalSlot)
        XCTAssertFalse(slot.entitlementConsumed)
        _ = try await fixture.adapter.dispatchSaveAll(owner: fixture.owner)
        XCTAssertTrue(slot.entitlementConsumed)
        XCTAssertTrue(slot.snapshot.entitlementConsumed)
        XCTAssertEqual(slot.snapshot.consumedByRunID, fixture.authorization.runID)
        XCTAssertEqual(ledgerCount(fixture, "intent.saveAll"), 1)
        let moves = fixture.actuation.mouseMovedCount
        let buttons = fixture.actuation.buttonEventCount

        let secondLedgerURL = fixture.root.appendingPathComponent("ledger-second.jsonl")
        let secondAuthorization = ImmutableRunAuthorization(
            runID: "matrix-run-second",
            goal: fixture.authorization.goal,
            group: fixture.authorization.group,
            album: fixture.authorization.album,
            planSHA256: fixture.authorization.planSHA256,
            reviewedImplementationSHA256: fixture.authorization.reviewedImplementationSHA256,
            stagingRoot: fixture.stagingRoot,
            stagingRunDirectory: fixture.stagingRunDirectory
        )
        let secondOwner = try PersistentTransactionOwner(
            authorization: secondAuthorization,
            ledger: try IntentLedger(fileURL: secondLedgerURL),
            checkpointURL: fixture.root.appendingPathComponent("ledger-second-anchor.json"),
            goalSlot: slot
        )
        XCTAssertFalse(secondOwner.isObserveOnlyResume)
        XCTAssertThrowsError(try secondOwner.reserveSaveAll()) { error in
            guard let persistent = error as? PersistentTransactionError,
                  case let .goalSlotEntitlementConsumed(detail) = persistent else {
                return XCTFail("expected goalSlotEntitlementConsumed, got \(error)")
            }
            XCTAssertTrue(detail.contains("consumed at"))
        }
        let secondLedger = try IntentLedger(fileURL: secondLedgerURL)
        XCTAssertEqual(secondLedger.count(kind: "intent.saveAll"), 0)
        XCTAssertEqual(secondLedger.count(kind: "attempt.saveAll"), 0)
        XCTAssertEqual(fixture.actuation.mouseMovedCount, moves)
        XCTAssertEqual(fixture.actuation.buttonEventCount, buttons)
    }
}
