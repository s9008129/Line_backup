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
        addressableBounds: CGRect? = ComposedAdaptersTests.addressableBounds
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
                addressableBoundsCapture: addressableBounds
            )
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

    // MARK: - Irreversible boundary remains unreachable

    func testExecuteStopsAtSaveAllBoundaryWithoutIrreversibleRecords() async throws {
        let fixture = try makeFixture()
        let owner = try makeOwner(fixture)
        let engine = LiveExecutionEngine(owner: owner, adapter: makeAdapter(fixture))

        do {
            _ = try await engine.run()
            XCTFail("the composed adapter must not reach the irreversible boundary in this round")
        } catch let error as ComposedAdapterError {
            guard case let .capabilityNotBuilt(stage) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(stage, "dispatchSaveAll")
        }
        XCTAssertEqual(owner.currentState, .saveAllLocated)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(fixture.environment.postedActions, ["open-album-card", "open-album-menu"])
        let slot = try GoalSlot.load(directory: fixture.goalSlotDirectory, authorization: fixture.authorization)
        XCTAssertEqual(slot?.entitlementConsumed, false)
    }
}
