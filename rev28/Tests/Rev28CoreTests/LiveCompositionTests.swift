import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

/// The live composition factory is the single entry both CLI commands use, so
/// these tests exercise the same assembly the production commands build.
final class LiveCompositionTests: XCTestCase {
    private let geometryState = CaptureGeometryState(
        settled: true,
        activated: true,
        includeChildWindows: false,
        ignoreShadows: true
    )
    private let menuBounds = CGRect(x: 200, y: 40, width: 170, height: 260)
    private let addressableBounds = CGRect(x: 210, y: 0, width: 160, height: 600)

    private func ruleBook(
        for state: CaptureGeometryState,
        ruleID: String = "unit-test",
        rule: CaptureGeometryRule = CaptureGeometryRule(
            maxPerSideSizeDeltaPt: 2,
            originPaddingPt: 0,
            maxOriginPaddingPt: 4
        )
    ) -> CaptureGeometryRuleBook {
        CaptureGeometryRuleBook(
            ruleID: ruleID,
            frozenAtISO8601: "2026-09-29T00:00:00.000Z",
            rules: [CaptureGeometryRules.stateKey(state): rule]
        )
    }

    private func configuration(
        ruleBook: CaptureGeometryRuleBook? = nil,
        menuBounds: CGRect? = nil,
        budget: UInt64 = 5_000_000_000
    ) -> LiveCompositionConfiguration {
        LiveCompositionConfiguration(
            observationBudgetNanos: budget,
            captureConfiguration: .primaryWindow,
            geometryState: geometryState,
            geometryRuleBook: ruleBook ?? self.ruleBook(for: geometryState),
            menuBoundsCapture: menuBounds ?? self.menuBounds,
            addressableBoundsCapture: addressableBounds
        )
    }

    private func makeRunRoot(runID: String = "run-1") throws -> (root: URL, authorization: ImmutableRunAuthorization) {
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
        return (root, authorization)
    }

    func testValidationRefusesBudgetOutsideReviewedBounds() {
        XCTAssertThrowsError(try LiveCompositionFactory.validate(configuration(budget: 0))) { error in
            XCTAssertEqual(error as? LiveCompositionError, .invalidObservationBudget(0))
        }
        XCTAssertThrowsError(
            try LiveCompositionFactory.validate(
                configuration(budget: LiveCompositionFactory.maximumObservationBudgetNanos + 1)
            )
        ) { error in
            guard case .invalidObservationBudget = error as? LiveCompositionError else {
                return XCTFail("unexpected error \(error)")
            }
        }
    }

    func testValidationRefusesMissingFrozenRuleForTheConfiguredState() {
        let other = CaptureGeometryState(settled: false, activated: true, includeChildWindows: false, ignoreShadows: true)
        XCTAssertThrowsError(try LiveCompositionFactory.validate(configuration(ruleBook: ruleBook(for: other)))) { error in
            guard case let .missingFrozenGeometryRule(stateKey, ruleID) = error as? LiveCompositionError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(stateKey, CaptureGeometryRules.stateKey(self.geometryState))
            XCTAssertEqual(ruleID, "unit-test")
        }
    }

    func testValidationRefusesDegenerateLocatorGeometry() {
        let degenerate = CGRect(x: 200, y: 40, width: 0, height: 260)
        XCTAssertThrowsError(try LiveCompositionFactory.validate(configuration(menuBounds: degenerate))) { error in
            guard case .invalidLocatorGeometry = error as? LiveCompositionError else {
                return XCTFail("unexpected error \(error)")
            }
        }
    }

    func testValidationAcceptsTheReviewedShape() throws {
        try LiveCompositionFactory.validate(configuration())
    }

    func testFactoryRefusesUncalibratedConfigurationBeforeAnyObservation() throws {
        let (root, authorization) = try makeRunRoot()
        let scene = FakeLineScene()
        let source = FakeObservationSource(
            window: NativeObservationTestWindows.lineWindow(),
            bundleID: "jp.naver.line.mac",
            pid: 4242
        )
        source.imageProvider = { scene.image }
        let other = CaptureGeometryState(settled: false, activated: true, includeChildWindows: false, ignoreShadows: true)
        XCTAssertThrowsError(
            try LiveCompositionFactory.make(
                authorization: authorization,
                ledgerURL: root.appendingPathComponent("ledger.jsonl"),
                checkpointURL: root.appendingPathComponent("ledger-head.anchor"),
                goalSlotDirectory: root.appendingPathComponent("goal-slots", isDirectory: true),
                configuration: configuration(ruleBook: ruleBook(for: other)),
                target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
                source: source,
                environment: FakeActuationEnvironment(),
                sessionID: "composition-1"
            )
        ) { error in
            guard case .missingFrozenGeometryRule = error as? LiveCompositionError else {
                return XCTFail("unexpected error \(error)")
            }
        }
        XCTAssertEqual(source.captureCount, 0, "an uncalibrated composition must refuse before the first capture")
    }

    func testFactoryAssemblesOneCompositionThatReachesTheSaveAllBoundary() async throws {
        let (root, authorization) = try makeRunRoot()
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
        let composition = try LiveCompositionFactory.make(
            authorization: authorization,
            ledgerURL: root.appendingPathComponent("ledger.jsonl"),
            checkpointURL: root.appendingPathComponent("ledger-head.anchor"),
            goalSlotDirectory: root.appendingPathComponent("goal-slots", isDirectory: true),
            configuration: configuration(),
            target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            source: source,
            environment: environment,
            ocr: ScriptedOcr(scene: scene),
            sessionID: "composition-2"
        )

        let outcome = try await composition.engine.runPreflight()

        XCTAssertEqual(outcome.finalState, .saveAllLocated)
        XCTAssertEqual(outcome.observationsThisRun, LiveExecutionEngine.preSaveStates.count)
        XCTAssertEqual(outcome.saveAllIrreversibleRecords, 0)
        XCTAssertEqual(outcome.destinationIrreversibleRecords, 0)
        XCTAssertEqual(outcome.entitlementConsumed, false)
        XCTAssertEqual(environment.postedActions, ["open-album-card", "open-album-menu"])
        let captures = await composition.session.captureCount
        XCTAssertEqual(captures, 12)
        XCTAssertEqual(composition.epochAuthority.floor, 0)
        XCTAssertEqual(composition.owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(composition.owner.irreversibleOperationCounts.destinationConfirmation, 0)
    }

    func testFactoryAssembledExecuteStopsAtTheIrreversibleBoundary() async throws {
        let (root, authorization) = try makeRunRoot(runID: "run-2")
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
        let composition = try LiveCompositionFactory.make(
            authorization: authorization,
            ledgerURL: root.appendingPathComponent("ledger.jsonl"),
            checkpointURL: root.appendingPathComponent("ledger-head.anchor"),
            goalSlotDirectory: root.appendingPathComponent("goal-slots", isDirectory: true),
            configuration: configuration(),
            target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            source: source,
            environment: environment,
            ocr: ScriptedOcr(scene: scene),
            sessionID: "composition-3"
        )
        do {
            _ = try await composition.engine.run()
            XCTFail("the composed engine must stop at the irreversible boundary")
        } catch let error as ComposedAdapterError {
            guard case let .capabilityNotBuilt(stage) = error else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(stage, "dispatchSaveAll")
        }
        XCTAssertEqual(composition.owner.currentState, .saveAllLocated)
        XCTAssertEqual(composition.owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(composition.owner.irreversibleOperationCounts.destinationConfirmation, 0)
        XCTAssertEqual(environment.postedActions, ["open-album-card", "open-album-menu"])
    }
}
