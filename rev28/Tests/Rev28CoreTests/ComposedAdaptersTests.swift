import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

/// Composed tests for the native production adapter. Substitutions live below
/// perception/predicate/state decisions: the scene supplies OCR text and pixels,
/// the environment supplies focus facts and records posted events. Every state
/// proof, epoch rule, ledger record and permit decision stays in production code.
final class ComposedAdaptersTests: XCTestCase {
    private static let menuBounds = CGRect(x: 200, y: 40, width: 170, height: 260)
    private static let addressableBounds = CGRect(x: 210, y: 0, width: 160, height: 600)

    private struct Fixture {
        let root: URL
        let authorization: ImmutableRunAuthorization
        let ledgerURL: URL
        let checkpointURL: URL
        let goalSlotDirectory: URL
        let scene: FakeLineScene
        let source: FakeObservationSource
        let session: NativeObservationSession
        let environment: FakeActuationEnvironment
    }

    private func makeFixture(runID: String = "run-1") throws -> Fixture {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let stagingRoot = root.appendingPathComponent("staging", isDirectory: true)
        let run = stagingRoot.appendingPathComponent(runID, isDirectory: true)
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: runID,
            goal: "Rev28 target album backup",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: stagingRoot,
            stagingRunDirectory: run
        )
        let scene = FakeLineScene()
        let source = FakeObservationSource(
            window: NativeObservationTestWindows.lineWindow(),
            bundleID: "jp.naver.line.mac",
            pid: 4242
        )
        source.imageProvider = { scene.image }
        let environment = FakeActuationEnvironment()
        environment.onClick = { action in
            switch action {
            case "open-album-card": scene.current = .albumDetail
            case "open-album-menu": scene.current = .menuOpen
            default: XCTFail("unexpected reversible action \(action)")
            }
        }
        return Fixture(
            root: root,
            authorization: authorization,
            ledgerURL: root.appendingPathComponent("ledger.jsonl"),
            checkpointURL: root.appendingPathComponent("ledger-head.anchor"),
            goalSlotDirectory: root.appendingPathComponent("goal-slots", isDirectory: true),
            scene: scene,
            source: source,
            session: NativeObservationSession(
                sessionID: "composed-session",
                source: source,
                ocr: ScriptedOcr(scene: scene)
            ),
            environment: environment
        )
    }

    private func makeOwner(
        _ fixture: Fixture,
        requireCheckpointOnResume: Bool = false
    ) throws -> PersistentTransactionOwner {
        try PersistentTransactionOwner(
            authorization: fixture.authorization,
            ledger: try IntentLedger(fileURL: fixture.ledgerURL),
            checkpointURL: fixture.checkpointURL,
            goalSlotDirectory: fixture.goalSlotDirectory,
            requireCheckpointOnResume: requireCheckpointOnResume
        )
    }

    private func makeAdapter(
        _ fixture: Fixture,
        menuBounds: CGRect? = ComposedAdaptersTests.menuBounds,
        addressableBounds: CGRect? = ComposedAdaptersTests.addressableBounds,
        postSave: FakePostSaveEnvironment = FakePostSaveEnvironment(),
        phaseBEligibility: PhaseBEligibilityArtifact? = nil
    ) -> ComposedNativeAdapter {
        ComposedNativeAdapter(
            session: fixture.session,
            environment: fixture.environment,
            configuration: ComposedAdapterConfiguration(
                target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
                geometryState: CaptureGeometryState(
                    settled: true,
                    activated: true,
                    includeChildWindows: false,
                    ignoreShadows: true
                ),
                observationBudgetNanos: 5_000_000_000,
                menuBoundsCapture: menuBounds,
                addressableBoundsCapture: addressableBounds,
                chooserPredicate: TestChooserFixtures.predicate(),
                baselineReferenceFile: URL(fileURLWithPath: "/dev/null")
            ),
            postSave: postSave,
            phaseBEligibility: phaseBEligibility
        )
    }

    private func eligibilityArtifact(_ fixture: Fixture) -> PhaseBEligibilityArtifact {
        PhaseBEligibilityArtifact(
            verdict: PhaseBEligibilityArtifact.eligibleVerdict,
            runID: fixture.authorization.runID,
            planSHA256: fixture.authorization.planSHA256,
            reviewedImplementationSHA256: fixture.authorization.reviewedImplementationSHA256,
            goalIdentitySHA256: PhaseBEligibilityArtifact.goalIdentityDigest(fixture.authorization),
            stagingRunDirectory: fixture.authorization.stagingRunDirectory,
            issuedAtISO8601: "2026-09-29T00:00:00.000Z",
            predicates: PhaseBEligibilityArtifact.requiredPredicates.map {
                PhaseBEligibilityPredicate(identifier: $0, verdict: "PASS")
            }
        )
    }

    private func artifact(
        state: ExecutionState,
        in evidenceDirectory: URL
    ) throws -> StateEvidenceArtifact {
        let files = try FileManager.default.contentsOfDirectory(atPath: evidenceDirectory.path)
            .filter { $0.hasPrefix("state-\(state.rawValue)-") && $0.hasSuffix(".json") }
        let name = try XCTUnwrap(files.sorted().last, "missing artifact for \(state.rawValue)")
        return try JSONDecoder().decode(
            StateEvidenceArtifact.self,
            from: Data(contentsOf: evidenceDirectory.appendingPathComponent(name))
        )
    }

    // MARK: - Phase A preflight

    func testPreflightWalksEveryPreSaveStateWithGuardedRecoveriesAndZeroIrreversibleIntent() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        let engine = LiveExecutionEngine(owner: owner, adapter: makeAdapter(fixture))

        let outcome = try await engine.runPreflight()

        XCTAssertEqual(outcome.finalState, .saveAllLocated)
        XCTAssertEqual(outcome.observationsThisRun, LiveExecutionEngine.preSaveStates.count)
        XCTAssertEqual(outcome.saveAllIrreversibleRecords, 0)
        XCTAssertEqual(outcome.destinationIrreversibleRecords, 0)
        XCTAssertEqual(outcome.entitlementConsumed, false)
        XCTAssertEqual(owner.currentState, .saveAllLocated)
        XCTAssertFalse(owner.isObserveOnlyResume)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(owner.reversibleDispatchCount, 2)
        XCTAssertEqual(fixture.environment.postedActions, ["open-album-card", "open-album-menu"])
        XCTAssertEqual(fixture.source.captureCount, 12)
        let slot = try GoalSlot.load(directory: fixture.goalSlotDirectory, authorization: fixture.authorization)
        XCTAssertEqual(slot?.entitlementConsumed, false)

        // The state that authorizes navigation can never carry a click
        // candidate: its evidence is observed with no structural request.
        let evidenceDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let albumDetail = try artifact(state: .albumDetailVerified, in: evidenceDirectory)
        XCTAssertNil(albumDetail.candidateIdentity)
        XCTAssertNil(albumDetail.candidateRefusal)
        XCTAssertEqual(albumDetail.cardRegionCount, 0)
        XCTAssertTrue(albumDetail.ocrTexts.contains(ComposedNativeAdapter.albumDetailCountText))
        XCTAssertTrue(albumDetail.ocrTexts.contains(LiveExecutionEngine.targetGroup))

        // Every other proof keeps its reviewed structural identity in the artifact.
        XCTAssertEqual(
            try artifact(state: .targetAlbumLocated, in: evidenceDirectory).candidateIdentity?
                .hasSuffix(":2024/05/13~05/17|57"),
            true
        )
        XCTAssertEqual(
            try artifact(state: .ellipsisLocated, in: evidenceDirectory).candidateIdentity,
            "album-ellipsis"
        )
        XCTAssertEqual(
            try artifact(state: .saveAllLocated, in: evidenceDirectory).candidateIdentity,
            "儲存全部"
        )
    }

    func testPreflightRefusesSaveAllLocatedWhenFrozenMenuGeometryIsAbsent() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        let engine = LiveExecutionEngine(
            owner: owner,
            adapter: makeAdapter(fixture, menuBounds: nil, addressableBounds: nil)
        )

        do {
            _ = try await engine.runPreflight()
            XCTFail("SAVE_ALL_LOCATED without frozen menu geometry must refuse")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, _) = error else {
                return XCTFail("unexpected refusal \(error)")
            }
            XCTAssertEqual(state, ExecutionState.saveAllLocated.rawValue)
        }
        XCTAssertEqual(owner.currentState, .menuVerified)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
    }

    func testAppReadyRequiresFrontmostTargetAndPostsNothing() async throws {
        let fixture = try makeFixture()
        fixture.environment.frontmost = false
        let owner = try makeOwner(fixture)
        let engine = LiveExecutionEngine(owner: owner, adapter: makeAdapter(fixture))

        do {
            _ = try await engine.runPreflight()
            XCTFail("a non-frontmost target must not establish APP_READY")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, _) = error else {
                return XCTFail("unexpected refusal \(error)")
            }
            XCTAssertEqual(state, ExecutionState.appReady.rawValue)
        }
        XCTAssertNil(owner.currentState)
        XCTAssertEqual(fixture.environment.postedActions, [])
        XCTAssertEqual(fixture.source.captureCount, 1)
    }

    func testPreflightRefusesLedgerThatAlreadyRecordedIrreversibleIntent() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        try owner.ledger.append(kind: "intent.saveAll", payload: ["risk": "IRREVERSIBLE_SIDE_EFFECT"])
        try owner.ledger.writeHeadAnchor(to: fixture.checkpointURL)

        let resumed = try makeOwner(fixture, requireCheckpointOnResume: true)
        let engine = LiveExecutionEngine(owner: resumed, adapter: makeAdapter(fixture))
        do {
            _ = try await engine.runPreflight()
            XCTFail("preflight must refuse a ledger that already holds irreversible intent")
        } catch let error as LiveExecutionEngineError {
            XCTAssertEqual(error, .preflightRequiresZeroIrreversibleRecords)
        }
        XCTAssertEqual(fixture.source.captureCount, 0)
        XCTAssertEqual(fixture.environment.postedActions, [])
    }

    func testPreIntentContinuationResumesWithoutReusingEvidence() async throws {
        let fixture = try makeFixture()
        let firstOwner = try makeOwner(fixture)
        let firstAdapter = makeAdapter(fixture)
        for (index, state) in [ExecutionState.appReady, .groupReady, .albumListReady].enumerated() {
            let evidence = try await firstAdapter.establish(state: state, owner: firstOwner)
            if index == 0 {
                try firstOwner.initializeState(evidenceSHA256: evidence.evidenceSHA256)
            } else {
                try firstOwner.transition(to: state, evidenceSHA256: evidence.evidenceSHA256)
            }
        }
        let firstRunCaptures = fixture.source.captureCount
        XCTAssertEqual(firstRunCaptures, 3)
        let firstRunEvidence = firstOwner.ledger.entries
            .filter { $0.kind == "state.transition" }
            .compactMap { $0.payload["evidenceSHA256"] }

        let resumed = try makeOwner(fixture, requireCheckpointOnResume: true)
        XCTAssertTrue(resumed.isObserveOnlyResume)
        let outcome = try await LiveExecutionEngine(owner: resumed, adapter: makeAdapter(fixture)).runPreflight()

        XCTAssertEqual(outcome.finalState, .saveAllLocated)
        XCTAssertEqual(outcome.observationsThisRun, 5)
        XCTAssertEqual(outcome.entitlementConsumed, false)
        XCTAssertEqual(fixture.source.captureCount - firstRunCaptures, 9)

        let transitions = resumed.ledger.entries.filter { $0.kind == "state.transition" }
        XCTAssertEqual(transitions.count, 8)
        XCTAssertEqual(transitions.map { $0.payload["to"] ?? "" }, LiveExecutionEngine.preSaveStates.map(\.rawValue))
        XCTAssertEqual(transitions[3].payload["from"], ExecutionState.albumListReady.rawValue)
        let evidenceDigests = transitions.compactMap { $0.payload["evidenceSHA256"] }
        XCTAssertEqual(Set(evidenceDigests).count, 8)
        XCTAssertEqual(Array(evidenceDigests.prefix(3)), firstRunEvidence)

        // Resumed proofs are fresh captures with strictly greater epochs; the
        // completed states are neither re-established nor rewritten.
        let evidenceDirectory = URL(fileURLWithPath: resumed.authorization.evidenceRunDirectory)
        let epochs = try LiveExecutionEngine.preSaveStates.map { state -> UInt64 in
            let files = try FileManager.default.contentsOfDirectory(atPath: evidenceDirectory.path)
                .filter { $0.hasPrefix("state-\(state.rawValue)-") && $0.hasSuffix(".json") }
            XCTAssertEqual(files.count, 1)
            return try XCTUnwrap(UInt64(files[0].split(separator: "-").last?.replacingOccurrences(of: ".json", with: "") ?? ""))
        }
        XCTAssertEqual(epochs, epochs.sorted())
        XCTAssertEqual(epochs.first, 1)
        XCTAssertEqual(epochs[3] > epochs[2], true)
    }

    // MARK: - Irreversible boundary (fail closed without Phase B eligibility)

    func testExecuteRefusesSaveAllDispatchWithoutPhaseBEligibility() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        let postSave = FakePostSaveEnvironment()
        let engine = LiveExecutionEngine(owner: owner, adapter: makeAdapter(fixture, postSave: postSave))

        do {
            _ = try await engine.run()
            XCTFail("the composed adapter must not reach the irreversible boundary in this round")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.saveAllLocated.rawValue)
            XCTAssertTrue(detail.contains("eligibility"), detail)
        }
        XCTAssertEqual(owner.currentState, .saveAllLocated)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(fixture.environment.postedActions, ["open-album-card", "open-album-menu"])
        XCTAssertEqual(postSave.saveAllClicks, 0)
        XCTAssertEqual(postSave.dispatchBoundaryMarks, 0)
        let evidenceNames = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory).path
        )
        XCTAssertTrue(evidenceNames.filter { $0.hasPrefix("pre-dispatch-context") }.isEmpty)
        let slot = try GoalSlot.load(directory: fixture.goalSlotDirectory, authorization: fixture.authorization)
        XCTAssertEqual(slot?.entitlementConsumed, false)
    }

    private func dispatchFixture(_ fixture: Fixture) async throws
        -> (adapter: ComposedNativeAdapter, owner: PersistentTransactionOwner, postSave: FakePostSaveEnvironment) {
        let owner = try makeOwner(fixture)
        let postSave = FakePostSaveEnvironment()
        postSave.census = TestChooserFixtures.census()
        let adapter = makeAdapter(fixture, postSave: postSave, phaseBEligibility: eligibilityArtifact(fixture))
        _ = try await LiveExecutionEngine(owner: owner, adapter: adapter).runPreflight()
        return (adapter, owner, postSave)
    }

    func testSaveAllDispatchRefusesWhenThePreDispatchContextGaps() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        let postSave = FakePostSaveEnvironment()
        postSave.census = TestChooserFixtures.census()
        postSave.preDispatchContextFacts = PreDispatchContextFacts(
            minimumSeconds: 10,
            observedSeconds: 12,
            journalRunning: true,
            journalFailure: nil,
            collectionGap: "FSEvents reported kernel-dropped events",
            journalStartedAtMonotonicNanos: 1,
            facts: []
        )
        let adapter = makeAdapter(fixture, postSave: postSave, phaseBEligibility: eligibilityArtifact(fixture))
        _ = try await LiveExecutionEngine(owner: owner, adapter: adapter).runPreflight()

        do {
            _ = try await adapter.dispatchSaveAll(owner: owner)
            XCTFail("a gapped pre-dispatch context must refuse the dispatch")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.saveAllLocated.rawValue)
            XCTAssertTrue(detail.contains("collection gap"), detail)
        }
        XCTAssertEqual(postSave.saveAllClicks, 0)
        XCTAssertEqual(postSave.dispatchBoundaryMarks, 0)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        let evidenceNames = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory).path
        )
        XCTAssertEqual(evidenceNames.filter { $0.hasPrefix("pre-dispatch-context-refused-") }.count, 1)
        XCTAssertTrue(evidenceNames.filter { $0.hasPrefix("pre-dispatch-context-") && !$0.hasPrefix("pre-dispatch-context-refused-") }.isEmpty)
    }

    func testSaveAllDispatchConsumesExactlyOneGuardedClickAndRecordsEvidence() async throws {
        let fixture = try makeFixture()
        let (adapter, owner, postSave) = try await dispatchFixture(fixture)
        let digest = try await adapter.dispatchSaveAll(owner: owner)

        XCTAssertEqual(digest.count, 64)
        XCTAssertTrue(digest.allSatisfy(\.isHexDigit))
        XCTAssertEqual(postSave.saveAllClicks, 1)
        XCTAssertEqual(postSave.dispatchBoundaryMarks, 1)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(owner.currentState, .saveAllLocated)
        let slot = try GoalSlot.load(directory: fixture.goalSlotDirectory, authorization: fixture.authorization)
        XCTAssertEqual(slot?.entitlementConsumed, true)

        let evidenceDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let names = try FileManager.default.contentsOfDirectory(atPath: evidenceDirectory.path)
        XCTAssertEqual(names.filter { $0.hasPrefix("pre-dispatch-context-") && $0.hasSuffix(".json") }.count, 1)
        XCTAssertEqual(names.filter { $0.hasPrefix("chooser-pre-census-") }.count, 1)
        XCTAssertEqual(names.filter { $0.hasPrefix("saveAll-dispatch-") }.count, 1)
        let contextName = try XCTUnwrap(names.first { $0.hasPrefix("pre-dispatch-context-") && $0.hasSuffix(".json") })
        let dispatchName = try XCTUnwrap(names.first { $0.hasPrefix("saveAll-dispatch-") })
        let context = try JSONDecoder().decode(
            PreDispatchContextRecord.self,
            from: Data(contentsOf: evidenceDirectory.appendingPathComponent(contextName))
        )
        XCTAssertEqual(context.minimumSeconds, ComposedNativeAdapter.minimumPreDispatchContextSeconds)
        XCTAssertGreaterThanOrEqual(context.observedSeconds, 10)
        let dispatch = try JSONDecoder().decode(
            SaveAllDispatchRecord.self,
            from: Data(contentsOf: evidenceDirectory.appendingPathComponent(dispatchName))
        )
        XCTAssertEqual(dispatch.candidateIdentity, "儲存全部")
        XCTAssertEqual(
            dispatch.preDispatchContextSHA256,
            try EvidenceIO.sha256Hex(ofFileAt: evidenceDirectory.appendingPathComponent(contextName))
        )
        XCTAssertEqual(dispatch.saveAllRecords, 2)
        XCTAssertEqual(dispatch.destinationRecords, 0)

        // The one-shot budget is spent: a second dispatch attempt is refused
        // without any further event.
        do {
            _ = try await adapter.dispatchSaveAll(owner: owner)
            XCTFail("a consumed Save All entitlement must never dispatch twice")
        } catch {
            // refusal is required; the exact error is the ledger/slot refusal class
        }
        XCTAssertEqual(postSave.saveAllClicks, 1)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 2)
    }

    // MARK: - C6 chooser affirmation, destination, C7 download/content

    func testChooserAffirmationProducesBoundArtifactsAndNamedRefusals() async throws {
        let fixture = try makeFixture()
        let (adapter, owner, postSave) = try await dispatchFixture(fixture)
        _ = try await adapter.dispatchSaveAll(owner: owner)
        postSave.setChooserResults([.facts(TestChooserFixtures.affirmingFacts())])

        let evidence = try await adapter.observeChooser(owner: owner)

        XCTAssertEqual(evidence.postcondition.runID, fixture.authorization.runID)
        XCTAssertEqual(evidence.tripwire.runID, fixture.authorization.runID)
        XCTAssertEqual(evidence.postcondition.sha256.count, 64)
        XCTAssertEqual(evidence.tripwire.sha256.count, 64)
        let postcondition = try evidence.postcondition.decode(PostconditionEvidenceArtifact.self)
        XCTAssertEqual(postcondition.outcome, "CHOOSER_VERIFIED")
        XCTAssertEqual(postcondition.chooserAffirmation?.windowID, TestChooserFixtures.chooserWindowID)
        try owner.recordChooserVerified(
            postconditionEvidence: evidence.postcondition,
            tripwireEvidence: evidence.tripwire
        )
        try owner.transition(to: .chooserVerified, evidenceSHA256: evidence.postcondition.sha256)

        // Duplicate affirming candidates widen to refusal, never a coin flip.
        let duplicate = try makeFixture(runID: "run-duplicate-chooser")
        let (duplicateAdapter, duplicateOwner, duplicatePostSave) = try await dispatchFixture(duplicate)
        _ = try await duplicateAdapter.dispatchSaveAll(owner: duplicateOwner)
        duplicatePostSave.setChooserResults([
            .facts(
                ChooserFacts(
                    windows: [
                        TestChooserFixtures.affirmingWindow(windowID: 99),
                        TestChooserFixtures.affirmingWindow(windowID: 101),
                    ],
                    postDispatchCensusPIDs: [100],
                    tripwire: []
                )
            )
        ])
        do {
            _ = try await duplicateAdapter.observeChooser(owner: duplicateOwner)
            XCTFail("two affirming candidates must refuse")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.chooserVerified.rawValue)
            XCTAssertTrue(detail.contains("ambiguous"), detail)
        }
        XCTAssertEqual(
            duplicateOwner.ledger.entries.filter { $0.kind == "postcondition.chooserVerified" }.count,
            0
        )

        // No affirming candidate at all: a named refusal with its artifacts.
        let empty = try makeFixture(runID: "run-empty-chooser")
        let (emptyAdapter, emptyOwner, emptyPostSave) = try await dispatchFixture(empty)
        _ = try await emptyAdapter.dispatchSaveAll(owner: emptyOwner)
        emptyPostSave.setChooserResults([.facts(TestChooserFixtures.emptyFacts())])
        do {
            _ = try await emptyAdapter.observeChooser(owner: emptyOwner)
            XCTFail("no candidate must refuse")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.chooserVerified.rawValue)
            XCTAssertTrue(detail.contains("no chooser affirmed") || detail.contains("no new window"), detail)
        }
        let emptyNames = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: emptyOwner.authorization.evidenceRunDirectory).path
        )
        XCTAssertEqual(emptyNames.filter { $0.hasSuffix("-postcondition.json") }.count, 1)
        XCTAssertEqual(emptyNames.filter { $0.hasSuffix("-tripwire.json") }.count, 1)
    }

    func testDestinationPreparationAndSingleConfirmationUseTheBoundChooser() async throws {
        let fixture = try makeFixture()
        let (adapter, owner, postSave) = try await dispatchFixture(fixture)
        _ = try await adapter.dispatchSaveAll(owner: owner)
        postSave.setChooserResults([.facts(TestChooserFixtures.affirmingFacts())])
        let chooser = try await adapter.observeChooser(owner: owner)
        try owner.recordChooserVerified(
            postconditionEvidence: chooser.postcondition,
            tripwireEvidence: chooser.tripwire
        )
        try owner.transition(to: .chooserVerified, evidenceSHA256: chooser.postcondition.sha256)

        let prepared = try await adapter.prepareDestination(owner: owner)
        let confirmed = try await adapter.confirmDestination(owner: owner)

        XCTAssertEqual(prepared.count, 64)
        XCTAssertEqual(confirmed.count, 64)
        XCTAssertEqual(postSave.preparedPIDs, [TestChooserFixtures.chooserPID])
        XCTAssertEqual(postSave.preparedDestinations, [fixture.authorization.stagingRunDirectory])
        XCTAssertEqual(postSave.confirmations, 1)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 2)
        let evidenceNames = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory).path
        )
        XCTAssertEqual(evidenceNames.filter { $0.hasPrefix("destination-prepared-") }.count, 1)
        XCTAssertEqual(evidenceNames.filter { $0.hasPrefix("destination-confirmed-") }.count, 1)
    }

    func testDownloadObservationStopsAtTheCapAndProvesStabilityOtherwise() async throws {
        // (a) Never-quiescent staging refuses at the 10-minute cap.
        let capped = try makeFixture(runID: "run-download-cap")
        let (cappedAdapter, cappedOwner, cappedPostSave) = try await dispatchFixture(capped)
        cappedPostSave.stagingModificationTimesFollowClock = true
        cappedPostSave.stagingFiles = [
            StagingFileRecord(name: "part.partial", size: 1, modificationTime: 0, sha256: String(repeating: "b", count: 64), decodable: true)
        ]
        do {
            _ = try await cappedAdapter.observeDownloadInProgress(owner: cappedOwner)
            XCTFail("a never-stable staging tree must stop at the cap")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.downloadInProgress.rawValue)
            XCTAssertTrue(detail.contains("10-minute cap"), detail)
        }

        // (b) Three equal samples spanning the stability window proceed.
        let stable = try makeFixture(runID: "run-download-stable")
        let (stableAdapter, stableOwner, stablePostSave) = try await dispatchFixture(stable)
        stablePostSave.stagingFiles = [
            StagingFileRecord(name: "LINE_ALBUM_1.jpg", size: 10, modificationTime: 0, sha256: String(repeating: "a", count: 64), decodable: true)
        ]
        let inProgress = try await stableAdapter.observeDownloadInProgress(owner: stableOwner)
        let stableEvidence = try await stableAdapter.observeFilesystemStable(owner: stableOwner)
        XCTAssertEqual(stablePostSave.preparedDestinations.count, 0)
        XCTAssertEqual(stableOwner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(inProgress.count, 64)
        XCTAssertEqual(stableEvidence.count, 64)
        let names = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: stableOwner.authorization.evidenceRunDirectory).path
        )
        XCTAssertTrue(names.contains("download-progress.json"))
        XCTAssertTrue(names.contains("filesystem-stable.json"))
    }

    func testVerifyContentConfirmsExactMultisetAndRefusesBaselineChange() async throws {
        let fixture = try makeFixture(runID: "run-content")
        let (adapter, owner, postSave) = try await dispatchFixture(fixture)
        let hashes = try Self.acceptedMultisetHashes()
        XCTAssertEqual(hashes.count, StagingPolicy.rev28Accepted.expectedFileCount)
        var sizes = Array(repeating: UInt64(1), count: hashes.count - 1)
        sizes.append(StagingPolicy.rev28Accepted.expectedTotalBytes - UInt64(hashes.count - 1))
        postSave.stagingFiles = zip(hashes, sizes).enumerated().map { entry in
            StagingFileRecord(
                name: String(format: "LINE_ALBUM_20240513～0517_260907_%03d.jpg", entry.offset),
                size: entry.element.1,
                modificationTime: 0,
                sha256: entry.element.0,
                decodable: true
            )
        }
        _ = try await adapter.observeDownloadInProgress(owner: owner)

        let evidence = try await adapter.verifyContent(owner: owner)

        XCTAssertEqual(evidence.verification.outcome, .duplicateContentConfirmed)
        XCTAssertEqual(evidence.verification.fileCount, 57)
        XCTAssertEqual(evidence.verification.totalBytes, 17_924_900)
        XCTAssertEqual(evidence.verification.contentMultisetSHA256, StagingPolicy.rev28Accepted.expectedContentMultisetSHA256)
        let names = try FileManager.default.contentsOfDirectory(
            atPath: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory).path
        )
        XCTAssertTrue(names.contains("content-verification.json"))

        // An accepted baseline that changed mid-run can never yield a success
        // claim, even though the staging content itself still matches.
        postSave.baselineResult = BaselineVerificationResult(
            sourceDirectory: "/baseline",
            fileCount: StagingPolicy.rev28Accepted.expectedFileCount,
            totalBytes: StagingPolicy.rev28Accepted.expectedTotalBytes,
            contentMultisetSHA256: StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
            nameInclusiveTripwireSHA256: String(repeating: "f", count: 64),
            verifiedAtISO8601: "2026-09-29T00:00:00.000Z"
        )
        do {
            _ = try await adapter.verifyContent(owner: owner)
            XCTFail("a changed baseline must refuse the content claim")
        } catch let error as ComposedAdapterError {
            guard case let .stateRefused(state, detail) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(state, ExecutionState.contentVerified.rawValue)
            XCTAssertTrue(detail.contains("baseline"), detail)
        }
    }

    /// Reads the 57 accepted content hashes out of the frozen reference file so
    /// the success path is compared against the real multiset, not a synthetic
    /// digest that could silently drift from the policy constant.
    private static func acceptedMultisetHashes() throws -> [String] {
        var root = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { root.deleteLastPathComponent() }
        let reference = root.appendingPathComponent("evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json")
        struct Reference: Decodable {
            let content_multiset: [String]
        }
        let data = try Data(contentsOf: reference)
        return try JSONDecoder().decode(Reference.self, from: data).content_multiset
    }
}
