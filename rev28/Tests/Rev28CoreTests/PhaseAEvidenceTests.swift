import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

/// Phase A publication is the machine-checkable record of a real
/// observation-only preflight. These tests drive the builder over synthetic
/// run directories so every PASS/FAIL branch and the append-only publication
/// are exercised without touching a live session.
final class PhaseAEvidenceTests: XCTestCase {
    private let bundleID = "jp.naver.line.mac"
    private let pid: Int32 = 4242
    private let startSeconds: Int64 = 1_700_000_000
    private let startMicroseconds: Int32 = 123_456

    private func makeRoot() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }

    private func authorization(root: URL) -> ImmutableRunAuthorization {
        ImmutableRunAuthorization(
            runID: "run-phase-a-test",
            goal: "Rev28 target album backup",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: String(repeating: "a", count: 64),
            reviewedImplementationSHA256: String(repeating: "b", count: 64),
            stagingRoot: root.appendingPathComponent("staging"),
            stagingRunDirectory: root.appendingPathComponent("staging/run-phase-a-test"),
            evidenceRunDirectory: root.appendingPathComponent("evidence")
        )
    }

    private struct StateSpec {
        let state: ExecutionState
        let ocrTexts: [String]
        let cardRegionCount: Int
        let candidateIdentity: String?
        let candidateRefusal: String?
    }

    private func defaultStateSpecs() -> [StateSpec] {
        [
            StateSpec(state: .appReady, ocrTexts: [], cardRegionCount: 0, candidateIdentity: nil, candidateRefusal: nil),
            StateSpec(state: .groupReady, ocrTexts: [LiveExecutionEngine.targetGroup], cardRegionCount: 0, candidateIdentity: nil, candidateRefusal: nil),
            StateSpec(state: .albumListReady, ocrTexts: [], cardRegionCount: 2, candidateIdentity: nil, candidateRefusal: nil),
            StateSpec(state: .targetAlbumLocated, ocrTexts: ["2024/05/13~05/17"], cardRegionCount: 3, candidateIdentity: "album-card:2024/05/13~05/17|57", candidateRefusal: nil),
            StateSpec(state: .albumDetailVerified, ocrTexts: [LiveExecutionEngine.targetGroup, "57張照片"], cardRegionCount: 0, candidateIdentity: nil, candidateRefusal: nil),
            StateSpec(state: .ellipsisLocated, ocrTexts: [], cardRegionCount: 0, candidateIdentity: "album-ellipsis", candidateRefusal: nil),
            StateSpec(state: .menuVerified, ocrTexts: StructuralLocators.lineAlbumMenuReference, cardRegionCount: 0, candidateIdentity: nil, candidateRefusal: nil),
            StateSpec(state: .saveAllLocated, ocrTexts: ["儲存全部"], cardRegionCount: 0, candidateIdentity: "儲存全部", candidateRefusal: nil),
        ]
    }

    @discardableResult
    private func writeStateArtifact(
        runDirectory: URL,
        authorization: ImmutableRunAuthorization,
        spec: StateSpec,
        epoch: UInt64,
        windowID: UInt32 = 777,
        windowFrame: CGRect = CGRect(x: 100, y: 80, width: 900, height: 620),
        pid overridePID: Int32? = nil,
        bundleID overrideBundleID: String? = nil,
        frameBytes: Data? = nil
    ) throws -> StateEvidenceArtifact {
        let frameName = "state-\(spec.state.rawValue)-\(epoch).png"
        let bytes = frameBytes ?? Data("frame-\(spec.state.rawValue)-\(epoch)".utf8)
        try bytes.write(to: runDirectory.appendingPathComponent(frameName))
        let artifact = StateEvidenceArtifact(
            runID: authorization.runID,
            state: spec.state.rawValue,
            sessionID: "session-phase-a-test",
            epoch: epoch,
            bundleID: overrideBundleID ?? bundleID,
            pid: overridePID ?? pid,
            processStartSeconds: startSeconds,
            processStartMicroseconds: startMicroseconds,
            windowID: windowID,
            windowFrame: windowFrame,
            axRole: "AXWindow",
            frameSHA256: EvidenceIO.sha256Hex(bytes),
            retainedFrameName: frameName,
            capturedAtISO8601: "2026-09-29T06:00:0\(epoch).000+08:00",
            startedAtMonotonicNanos: epoch * 1_000,
            endedAtMonotonicNanos: epoch * 1_000 + 10,
            deadlineMonotonicNanos: epoch * 1_000 + 1_000_000,
            ocrTexts: spec.ocrTexts,
            cardRegionCount: spec.cardRegionCount,
            candidateIdentity: spec.candidateIdentity,
            candidateRefusal: spec.candidateRefusal,
            localization: "observed"
        )
        try EvidenceIO.writeJSONAtomically(
            artifact,
            to: runDirectory.appendingPathComponent("state-\(spec.state.rawValue)-\(epoch).json")
        )
        return artifact
    }

    private func writePreDispatchContext(
        runDirectory: URL,
        authorization: ImmutableRunAuthorization,
        observedSeconds: Double = 10.4,
        minimumSeconds: Double = 10,
        collectionGap: String? = nil,
        name: String = "pre-dispatch-context-2026-09-29T06-01-00.000+08-00.json"
    ) throws -> String {
        let record = PreDispatchContextRecord(
            runID: authorization.runID,
            minimumSeconds: minimumSeconds,
            observedSeconds: observedSeconds,
            journalStartedAtMonotonicNanos: 5_000_000,
            collectionGap: collectionGap,
            factCount: 0,
            facts: [],
            recordedAtISO8601: "2026-09-29T06:01:00.000+08:00"
        )
        let url = runDirectory.appendingPathComponent(name)
        try EvidenceIO.writeJSONAtomically(record, to: url)
        return try EvidenceIO.sha256Hex(ofFileAt: url)
    }

    private func inventory() -> PhaseAInventoryFacts {
        PhaseAInventoryFacts(
            sckWindowCount: 12,
            cgWindowCount: 14,
            axWindowCount: 3,
            targetWindowID: 777,
            targetPresentInSCK: true,
            targetPresentInCG: true,
            axFrameMatchesTarget: true
        )
    }

    private func census() -> ChooserCensus {
        ChooserCensus(
            windowIDs: [777, 778],
            processes: [
                ChooserProcessFacts(pid: pid, bundleID: bundleID, signingIdentity: "line-signature", startTimeUnix: 1_700_000_000.1),
                ChooserProcessFacts(pid: 99, bundleID: "com.apple.finder", signingIdentity: "finder", startTimeUnix: 1_600_000_000.0),
            ],
            recordedAtMonotonicNanos: 9_000_000
        )
    }

    private func baseline() -> BaselineVerificationResult {
        BaselineVerificationResult(
            sourceDirectory: "/tmp/baseline",
            fileCount: StagingPolicy.rev28Accepted.expectedFileCount,
            totalBytes: StagingPolicy.rev28Accepted.expectedTotalBytes,
            contentMultisetSHA256: StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
            nameInclusiveTripwireSHA256: ImmutableRunAuthorization.acceptedBaselineTripwireSHA256,
            verifiedAtISO8601: "2026-09-29T06:01:30.000+08:00"
        )
    }

    private func inputs(
        authorization: ImmutableRunAuthorization,
        preDispatchContextSHA256: String,
        liveProcess: PhaseAProcessFacts? = nil,
        axTrusted: Bool = true,
        screenCaptureTrusted: Bool = true,
        inventory: PhaseAInventoryFacts? = nil,
        displayScales: [Double] = [2.0],
        baselineResult: BaselineVerificationResult? = nil,
        baselineError: String? = nil,
        stagingSnapshot: StagingSnapshot? = nil,
        tripwire: PhaseATripwireFacts? = nil,
        census: ChooserCensus? = nil,
        censusError: String? = nil,
        ledgerCounts: PhaseALedgerCounts? = nil,
        reversibleDispatches: Int = 3,
        preflightOutcomeArtifactName: String? = "preflight-outcome-test.json"
    ) -> PhaseAEvidenceInputs {
        let baselineGiven = baselineResult != nil || baselineError != nil
        let censusGiven = census != nil || censusError != nil
        return PhaseAEvidenceInputs(
            authorization: authorization,
            targetBundleID: bundleID,
            targetPID: pid,
            liveProcess: liveProcess ?? PhaseAProcessFacts(
                bundleID: bundleID,
                signingIdentity: "line-signature",
                startTimeSeconds: startSeconds,
                startTimeMicroseconds: startMicroseconds
            ),
            axTrusted: axTrusted,
            screenCaptureTrusted: screenCaptureTrusted,
            inventory: inventory ?? self.inventory(),
            inventoryError: nil,
            displayScales: displayScales,
            frozenGeometry: PhaseAFrozenGeometryFacts(
                captureConfiguration: "primaryWindow",
                ruleID: "capture-geometry-rulebook-v1",
                settled: true,
                activated: true,
                includeChildWindows: false,
                ignoreShadows: true,
                menuBoundsCapture: CGRect(x: 200, y: 40, width: 170, height: 260),
                addressableBoundsCapture: CGRect(x: 210, y: 0, width: 160, height: 600)
            ),
            baselineResult: baselineGiven ? baselineResult : self.baseline(),
            baselineError: baselineError,
            stagingSnapshot: stagingSnapshot ?? StagingSnapshot(observedAt: 1, files: []),
            stagingError: nil,
            tripwire: tripwire ?? PhaseATripwireFacts(
                running: true,
                failure: nil,
                collectionGap: nil,
                startedAtMonotonicNanos: 5_000_000,
                factCount: 0
            ),
            tripwireError: nil,
            prePanelCensus: censusGiven ? census : self.census(),
            prePanelCensusArtifactName: "pre-panel-census-test.json",
            prePanelCensusError: censusError,
            preDispatchContextSHA256: preDispatchContextSHA256,
            ledgerCounts: ledgerCounts ?? PhaseALedgerCounts(
                saveAllIntent: 0,
                saveAllAttempt: 0,
                destinationIntent: 0,
                destinationAttempt: 0,
                ownerSaveAllCount: 0,
                ownerDestinationCount: 0
            ),
            reversibleDispatches: reversibleDispatches,
            preflightOutcomeArtifactName: preflightOutcomeArtifactName
        )
    }

    /// One complete, all-PASS synthetic run directory plus its inputs.
    private func makeCompleteRun(specs: [StateSpec]? = nil) throws -> (
        root: URL,
        authorization: ImmutableRunAuthorization,
        runDirectory: URL,
        inspection: PhaseARunArtifacts,
        inputs: PhaseAEvidenceInputs,
        report: PhaseAEvidenceReport
    ) {
        let root = try makeRoot()
        let authorization = authorization(root: root)
        let runDirectory = root.appendingPathComponent("evidence")
        try FileManager.default.createDirectory(at: runDirectory, withIntermediateDirectories: true)
        var epoch: UInt64 = 1
        for spec in specs ?? defaultStateSpecs() {
            try writeStateArtifact(runDirectory: runDirectory, authorization: authorization, spec: spec, epoch: epoch)
            epoch += 1
        }
        let contextSHA = try writePreDispatchContext(runDirectory: runDirectory, authorization: authorization)
        let inspection = try PhaseAEvidenceBuilder.inspect(runDirectory: runDirectory)
        let inputs = inputs(authorization: authorization, preDispatchContextSHA256: contextSHA)
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs,
            inspection: inspection,
            generatedAtISO8601: "2026-09-29T06:02:00.000+08:00"
        )
        return (root, authorization, runDirectory, inspection, inputs, report)
    }

    private func status(_ report: PhaseAEvidenceReport, _ identifier: String) -> PhaseAConditionStatus? {
        report.conditions.first { $0.identifier == identifier }?.status
    }

    // MARK: - Complete run

    func testCompleteRunPassesEveryConditionWithZeroIrreversible() throws {
        let run = try makeCompleteRun()
        XCTAssertEqual(run.report.conditions.map(\.identifier), PhaseAEvidenceBuilder.conditionIdentifiers)
        XCTAssertEqual(run.report.phaseBPreventedBy, [])
        XCTAssertTrue(run.report.allConditionsPass)
        XCTAssertTrue(run.report.ledgerProvenZeroIrreversible)
        XCTAssertEqual(run.report.irreversible.reversibleDispatches, 3)
        XCTAssertEqual(run.report.statusCounts.pass, PhaseAEvidenceBuilder.conditionIdentifiers.count)
        XCTAssertEqual(run.report.deferredRuntimeGates.map(\.identifier), PhaseAEvidenceBuilder.deferredRuntimeGateIdentifiers)
        XCTAssertEqual(run.report.deferredRuntimeGates.first?.status, .unknown)
        XCTAssertEqual(run.report.deferredRuntimeGates.first?.runtimeGate, "PHASE_B")
        XCTAssertEqual(
            run.report.chooserAssumptionStatement,
            "chooser assumptions calibrated on real NSOpenPanel, actual LINE chooser not yet observed"
        )
    }

    func testPublicationWritesReportAndManifestCoveringEveryRawArtifact() throws {
        let run = try makeCompleteRun()
        let published = try PhaseAEvidencePublisher.publish(report: run.report, runDirectory: run.runDirectory)
        XCTAssertEqual(published.reportName, "phase-a.json")
        XCTAssertEqual(published.manifestName, "phase-a-manifest.json")
        XCTAssertEqual(published.phaseBPreventedBy, [])
        XCTAssertEqual(published.manifestEntryCount, run.inspection.states.count * 2 + 2)

        let manifestData = try Data(contentsOf: run.runDirectory.appendingPathComponent("phase-a-manifest.json"))
        let manifest = try JSONDecoder().decode(PhaseARawEvidenceManifest.self, from: manifestData)
        XCTAssertEqual(EvidenceIO.sha256Hex(manifestData), published.manifestSHA256)
        let names = manifest.entries.map(\.name)
        XCTAssertTrue(names.contains("phase-a.json"))
        XCTAssertFalse(names.contains("phase-a-manifest.json"))
        for state in run.inspection.states {
            XCTAssertTrue(names.contains(state.artifactName))
            XCTAssertTrue(names.contains(state.artifact.retainedFrameName))
        }
        for entry in manifest.entries {
            let url = run.runDirectory.appendingPathComponent(entry.name)
            XCTAssertEqual(try EvidenceIO.sha256Hex(ofFileAt: url), entry.sha256, entry.name)
        }
        XCTAssertTrue(PhaseAEvidencePublisher.isPublished(runDirectory: run.runDirectory))
    }

    func testSecondPublicationIsRefusedAppendOnly() throws {
        let run = try makeCompleteRun()
        try PhaseAEvidencePublisher.publish(report: run.report, runDirectory: run.runDirectory)
        XCTAssertThrowsError(try PhaseAEvidencePublisher.publish(report: run.report, runDirectory: run.runDirectory))
    }

    // MARK: - Single-condition failures

    func testMissingSaveAllArtifactFailsPopupConditionAndPreventsPhaseB() throws {
        let specs = defaultStateSpecs().filter { $0.state != .saveAllLocated }
        let run = try makeCompleteRun(specs: specs)
        XCTAssertEqual(status(run.report, "POPUP_OCCLUSION_ASSUMPTIONS"), .fail)
        XCTAssertTrue(run.report.phaseBPreventedBy.contains("POPUP_OCCLUSION_ASSUMPTIONS"))
    }

    func testRetainedFrameHashMismatchFailsSameFrameVision() throws {
        let run = try makeCompleteRun()
        let menu = try XCTUnwrap(run.inspection.latestPerState[ExecutionState.menuVerified.rawValue])
        try Data("corrupted".utf8).write(to: run.runDirectory.appendingPathComponent(menu.artifact.retainedFrameName))
        let inspection = try PhaseAEvidenceBuilder.inspect(runDirectory: run.runDirectory)
        let report = PhaseAEvidenceBuilder.build(
            inputs: run.inputs,
            inspection: inspection,
            generatedAtISO8601: "2026-09-29T06:03:00.000+08:00"
        )
        XCTAssertEqual(status(report, "SAME_FRAME_VISION"), .fail)
    }

    func testMalformedArtifactIsNamedNotSkipped() throws {
        let run = try makeCompleteRun()
        try Data("not-json".utf8).write(to: run.runDirectory.appendingPathComponent("state-APP_READY-99.json"))
        let inspection = try PhaseAEvidenceBuilder.inspect(runDirectory: run.runDirectory)
        XCTAssertEqual(inspection.malformedArtifactNames, ["state-APP_READY-99.json"])
        let report = PhaseAEvidenceBuilder.build(
            inputs: run.inputs,
            inspection: inspection,
            generatedAtISO8601: "2026-09-29T06:03:00.000+08:00"
        )
        XCTAssertEqual(status(report, "SAME_FRAME_VISION"), .fail)
    }

    func testBaselineMismatchFailsBaselineIntegrity() throws {
        let run = try makeCompleteRun()
        let wrong = BaselineVerificationResult(
            sourceDirectory: "/tmp/baseline",
            fileCount: 56,
            totalBytes: StagingPolicy.rev28Accepted.expectedTotalBytes,
            contentMultisetSHA256: StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
            nameInclusiveTripwireSHA256: ImmutableRunAuthorization.acceptedBaselineTripwireSHA256,
            verifiedAtISO8601: "2026-09-29T06:04:00.000+08:00"
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", baselineResult: wrong),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:04:00.000+08:00"
        )
        XCTAssertEqual(status(report, "BASELINE_INTEGRITY"), .fail)
    }

    func testBaselineErrorIsRecordedAsFail() throws {
        let run = try makeCompleteRun()
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(
                authorization: run.authorization,
                preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "",
                baselineResult: nil,
                baselineError: "nameInclusiveTripwireMismatch(value)"
            ),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:04:00.000+08:00"
        )
        let condition = try XCTUnwrap(report.conditions.first { $0.identifier == "BASELINE_INTEGRITY" })
        XCTAssertEqual(condition.status, .fail)
        XCTAssertTrue(condition.detail.contains("nameInclusiveTripwireMismatch(value)"))
    }

    func testNonEmptyStagingFailsSeparation() throws {
        let run = try makeCompleteRun()
        let snapshot = StagingSnapshot(
            observedAt: 1,
            files: [StagingFileRecord(
                name: "extra.jpg",
                size: 10,
                modificationTime: 1_700_000_000,
                sha256: String(repeating: "c", count: 64),
                decodable: true
            )]
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", stagingSnapshot: snapshot),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:05:00.000+08:00"
        )
        XCTAssertEqual(status(report, "STAGING_EVIDENCE_SEPARATION"), .fail)
    }

    func testTripwireGapFailsReadiness() throws {
        let run = try makeCompleteRun()
        let tripwire = PhaseATripwireFacts(
            running: true,
            failure: nil,
            collectionGap: "dropped FSEvents",
            startedAtMonotonicNanos: 5_000_000,
            factCount: 2
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", tripwire: tripwire),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:05:00.000+08:00"
        )
        XCTAssertEqual(status(report, "NATIVE_TRIPWIRE_READINESS"), .fail)
    }

    func testShortOrGappedPreDispatchContextFails() throws {
        let run = try makeCompleteRun()
        let gapSHA = try writePreDispatchContext(
            runDirectory: run.runDirectory,
            authorization: run.authorization,
            observedSeconds: 10.2,
            collectionGap: "gap",
            name: "pre-dispatch-context-gapped.json"
        )
        let gapped = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: gapSHA),
            inspection: try PhaseAEvidenceBuilder.inspect(runDirectory: run.runDirectory),
            generatedAtISO8601: "2026-09-29T06:05:00.000+08:00"
        )
        XCTAssertEqual(status(gapped, "PRE_DISPATCH_CONTEXT_10S"), .fail)

        let root = try makeRoot()
        let authorization = authorization(root: root)
        let runDirectory = root.appendingPathComponent("evidence")
        try FileManager.default.createDirectory(at: runDirectory, withIntermediateDirectories: true)
        var epoch: UInt64 = 1
        for spec in defaultStateSpecs() {
            try writeStateArtifact(runDirectory: runDirectory, authorization: authorization, spec: spec, epoch: epoch)
            epoch += 1
        }
        let shortSHA = try writePreDispatchContext(
            runDirectory: runDirectory,
            authorization: authorization,
            observedSeconds: 9.2
        )
        let short = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: authorization, preDispatchContextSHA256: shortSHA),
            inspection: try PhaseAEvidenceBuilder.inspect(runDirectory: runDirectory),
            generatedAtISO8601: "2026-09-29T06:05:00.000+08:00"
        )
        XCTAssertEqual(status(short, "PRE_DISPATCH_CONTEXT_10S"), .fail)
    }

    func testUnboundPreDispatchContextDigestFails() throws {
        let run = try makeCompleteRun()
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: String(repeating: "d", count: 64)),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        let condition = try XCTUnwrap(report.conditions.first { $0.identifier == "PRE_DISPATCH_CONTEXT_10S" })
        XCTAssertEqual(condition.status, .fail)
        XCTAssertTrue(condition.detail.contains("no raw pre-dispatch context artifact matches"))
    }

    func testIrreversibleLedgerRecordFailsAndIsReported() throws {
        let run = try makeCompleteRun()
        let counts = PhaseALedgerCounts(
            saveAllIntent: 1,
            saveAllAttempt: 0,
            destinationIntent: 0,
            destinationAttempt: 0,
            ownerSaveAllCount: 1,
            ownerDestinationCount: 0
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", ledgerCounts: counts),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "LEDGER_ZERO_IRREVERSIBLE"), .fail)
        XCTAssertFalse(report.ledgerProvenZeroIrreversible)
        XCTAssertEqual(report.irreversible.saveAllIntent, 1)
        XCTAssertEqual(report.irreversible.ownerSaveAllCount, 1)
    }

    func testDeniedTccFailsExecutableContext() throws {
        let run = try makeCompleteRun()
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", axTrusted: false),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "EXECUTABLE_CONTEXT_TCC"), .fail)
    }

    func testProcessMismatchFailsIdentityCondition() throws {
        let run = try makeCompleteRun()
        let live = PhaseAProcessFacts(
            bundleID: "com.example.other",
            signingIdentity: "other",
            startTimeSeconds: startSeconds,
            startTimeMicroseconds: startMicroseconds
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", liveProcess: live),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "REAL_PROCESS_SIGNATURE_START"), .fail)
    }

    func testArtifactProcessMismatchFailsIdentityCondition() throws {
        let root = try makeRoot()
        let authorization = authorization(root: root)
        let runDirectory = root.appendingPathComponent("evidence")
        try FileManager.default.createDirectory(at: runDirectory, withIntermediateDirectories: true)
        var epoch: UInt64 = 1
        for spec in defaultStateSpecs() {
            try writeStateArtifact(
                runDirectory: runDirectory,
                authorization: authorization,
                spec: spec,
                epoch: epoch,
                bundleID: spec.state == .appReady ? "com.example.other" : bundleID
            )
            epoch += 1
        }
        let contextSHA = try writePreDispatchContext(runDirectory: runDirectory, authorization: authorization)
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: authorization, preDispatchContextSHA256: contextSHA),
            inspection: try PhaseAEvidenceBuilder.inspect(runDirectory: runDirectory),
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        let condition = try XCTUnwrap(report.conditions.first { $0.identifier == "REAL_PROCESS_SIGNATURE_START" })
        XCTAssertEqual(condition.status, .fail)
        XCTAssertTrue(condition.detail.contains("boundToArtifacts=false"))
    }

    func testInventoryDisagreementFails() throws {
        let run = try makeCompleteRun()
        let mismatch = PhaseAInventoryFacts(
            sckWindowCount: 12,
            cgWindowCount: 14,
            axWindowCount: 3,
            targetWindowID: 777,
            targetPresentInSCK: true,
            targetPresentInCG: false,
            axFrameMatchesTarget: true
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", inventory: mismatch),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "SCK_CG_AX_INVENTORY"), .fail)
    }

    func testPanelServiceInCensusFailsPrePanelCensus() throws {
        let run = try makeCompleteRun()
        let panelCensus = ChooserCensus(
            windowIDs: [777],
            processes: [
                ChooserProcessFacts(
                    pid: 55,
                    bundleID: "com.apple.appkit.xpc.openAndSavePanelService",
                    signingIdentity: "panel",
                    startTimeUnix: 1_700_000_000.0
                ),
            ],
            recordedAtMonotonicNanos: 9_000_000
        )
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", census: panelCensus),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "PRE_PANEL_CENSUS"), .fail)
    }

    func testMissingCensusIsFailWithError() throws {
        let run = try makeCompleteRun()
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(
                authorization: run.authorization,
                preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "",
                census: nil,
                censusError: "shareableContentFailed"
            ),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        let condition = try XCTUnwrap(report.conditions.first { $0.identifier == "PRE_PANEL_CENSUS" })
        XCTAssertEqual(condition.status, .fail)
        XCTAssertTrue(condition.detail.contains("shareableContentFailed"))
    }

    func testMixedDisplayScalesFail() throws {
        let run = try makeCompleteRun()
        let report = PhaseAEvidenceBuilder.build(
            inputs: inputs(authorization: run.authorization, preDispatchContextSHA256: run.inputs.preDispatchContextSHA256 ?? "", displayScales: [1.0, 2.0]),
            inspection: run.inspection,
            generatedAtISO8601: "2026-09-29T06:06:00.000+08:00"
        )
        XCTAssertEqual(status(report, "DISPLAY_BACKING_SCALE"), .fail)
    }

    func testNonMatchingMenuRowsFailLocalization() throws {
        var specs = defaultStateSpecs()
        specs = specs.map { spec in
            guard spec.state == .menuVerified else { return spec }
            return StateSpec(
                state: spec.state,
                ocrTexts: ["選擇項目", "儲存全部"],
                cardRegionCount: spec.cardRegionCount,
                candidateIdentity: spec.candidateIdentity,
                candidateRefusal: spec.candidateRefusal
            )
        }
        let run = try makeCompleteRun(specs: specs)
        let condition = try XCTUnwrap(run.report.conditions.first { $0.identifier == "ELLIPSIS_AND_FIVE_ROW_MENU_LOCALIZATION" })
        XCTAssertEqual(condition.status, .fail)
        XCTAssertTrue(condition.detail.contains("rowsObserved=2/5"))
    }
}
