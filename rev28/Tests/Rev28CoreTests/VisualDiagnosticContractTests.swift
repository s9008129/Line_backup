import XCTest
@testable import Rev28Core

final class VisualDiagnosticContractTests: XCTestCase {
    private let clockWitnessID = "11111111-2222-4333-8444-555555555555"
    private let bootSessionUUID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"

    private func clockWitness(_ nanos: String) -> VisualDiagnosticClockWitness {
        VisualDiagnosticClockWitness(sessionID: "session", witnessID: clockWitnessID,
            bootSessionUUID: bootSessionUUID, timebaseNumerator: 125, timebaseDenominator: 3,
            continuousNanoseconds: nanos, sampledAtUTC: "2026-01-01T00:00:00.000Z")
    }

    private func humanSurfaceObject(surface: String = "ALBUMS") -> [String: Any] {
        [
            "version": 1,
            "kind": "human-visual-diagnostic-surface-1",
            "execution_mode": "HUMAN_ASSISTED",
            "evidence_tag": "HUMAN_OBSERVATION",
            "requested_surface": surface,
            "actionable": false
        ]
    }

    private func json(_ object: [String: Any]) -> String {
        let data = try! JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        return String(decoding: data, as: UTF8.self)
    }

    private func XCTAssertHumanSurfaceError<T>(_ expected: HumanVisualDiagnosticSurfaceError,
                                               _ operation: () throws -> T,
                                               file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertThrowsError(try operation(), file: file, line: line) { error in
            XCTAssertEqual(error as? HumanVisualDiagnosticSurfaceError, expected, file: file, line: line)
        }
    }

    func testHumanVisualDiagnosticSurfaceAcceptsAllThreeLegalSurfaces() throws {
        for surface in HumanVisualDiagnosticSurface.allCases {
            let request = try HumanVisualDiagnosticSurfaceParser.parse(
                json: json(humanSurfaceObject(surface: surface.rawValue)))
            XCTAssertEqual(request.version, 1)
            XCTAssertEqual(request.kind, "human-visual-diagnostic-surface-1")
            XCTAssertEqual(request.executionMode, .humanAssisted)
            XCTAssertEqual(request.evidenceTag, .humanObservation)
            XCTAssertEqual(request.requestedSurface, surface)
            XCTAssertFalse(request.actionable)
        }
    }

    func testHumanVisualDiagnosticSurfaceCodableRoundTripRemainsStrict() throws {
        let request = try HumanVisualDiagnosticSurfaceParser.parse(
            json: json(humanSurfaceObject(surface: "ALBUM_DETAIL")))
        let encoded = try JSONEncoder().encode(request)
        XCTAssertEqual(try JSONDecoder().decode(HumanVisualDiagnosticSurfaceRequest.self, from: encoded), request)

        var unknown = humanSurfaceObject()
        unknown["frame_support_pass"] = true
        XCTAssertHumanSurfaceError(.forbiddenEvidenceField("frame_support_pass")) {
            try JSONDecoder().decode(HumanVisualDiagnosticSurfaceRequest.self,
                from: Data(json(unknown).utf8))
        }
    }

    func testLegacyAutomaticArgumentsKeepTheHumanSurfaceParserOutOfThePath() throws {
        XCTAssertNil(try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
            "visual-diagnostic-capture", "--project-root", "/tmp/project"
        ]))
        XCTAssertNil(try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
            "visual-diagnostic-capture", "--surface", "ALBUMS"
        ]))
    }

    func testHumanVisualDiagnosticSurfaceRejectsMissingMalformedAndUnknownFields() {
        XCTAssertHumanSurfaceError(.invalidJSON) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: "{")
        }

        var missing = humanSurfaceObject()
        missing.removeValue(forKey: "requested_surface")
        XCTAssertHumanSurfaceError(.missingField("requested_surface")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(missing))
        }

        var malformed = humanSurfaceObject()
        malformed["actionable"] = "false"
        XCTAssertHumanSurfaceError(.malformedField("actionable")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(malformed))
        }

        var malformedMode = humanSurfaceObject()
        malformedMode["execution_mode"] = ["HUMAN_ASSISTED"]
        XCTAssertHumanSurfaceError(.malformedField("execution_mode")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(malformedMode))
        }

        var booleanVersion = humanSurfaceObject()
        booleanVersion["version"] = true
        XCTAssertHumanSurfaceError(.malformedField("version")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(booleanVersion))
        }

        let floatingVersion = """
        {"version":1.0,"kind":"human-visual-diagnostic-surface-1",
        "execution_mode":"HUMAN_ASSISTED","evidence_tag":"HUMAN_OBSERVATION",
        "requested_surface":"ALBUMS","actionable":false}
        """
        XCTAssertHumanSurfaceError(.malformedField("version")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: floatingVersion)
        }

        XCTAssertHumanSurfaceError(.invalidJSON) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: "[]")
        }

        var wrongVersion = humanSurfaceObject()
        wrongVersion["version"] = 2
        XCTAssertHumanSurfaceError(.invalidVersion(2)) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(wrongVersion))
        }

        var wrongKind = humanSurfaceObject()
        wrongKind["kind"] = "human-visual-diagnostic-surface-2"
        XCTAssertHumanSurfaceError(.invalidKind("human-visual-diagnostic-surface-2")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(wrongKind))
        }

        var unknown = humanSurfaceObject()
        unknown["unexpected"] = true
        XCTAssertHumanSurfaceError(.unknownField("unexpected")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(unknown))
        }
    }

    func testHumanVisualDiagnosticSurfaceRejectsModeAndTagMixing() {
        var automaticMode = humanSurfaceObject()
        automaticMode["execution_mode"] = "AUTO"
        XCTAssertHumanSurfaceError(.mixedExecutionMode("AUTO")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(automaticMode))
        }

        var illegalMode = humanSurfaceObject()
        illegalMode["execution_mode"] = "AUTOMATIC"
        XCTAssertHumanSurfaceError(.invalidExecutionMode("AUTOMATIC")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(illegalMode))
        }

        var automaticTag = humanSurfaceObject()
        automaticTag["evidence_tag"] = "AUTO_FRAME_SUPPORT_PASS"
        XCTAssertHumanSurfaceError(.mixedEvidenceTag("AUTO_FRAME_SUPPORT_PASS")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(automaticTag))
        }

        var illegalTag = humanSurfaceObject()
        illegalTag["evidence_tag"] = "FRAME_SUPPORT_PASS"
        XCTAssertHumanSurfaceError(.invalidEvidenceTag("FRAME_SUPPORT_PASS")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(illegalTag))
        }

        let payload = json(humanSurfaceObject())
        XCTAssertHumanSurfaceError(.conflictingArgument("--surface")) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture", "--surface", "ALBUMS",
                HumanVisualDiagnosticSurfaceParser.argument, payload
            ])
        }
    }

    func testHumanVisualDiagnosticSurfaceRejectsIllegalSurfaceAndAction() {
        var illegalSurface = humanSurfaceObject()
        illegalSurface["requested_surface"] = "VIEWER"
        XCTAssertHumanSurfaceError(.invalidSurface("VIEWER")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(illegalSurface))
        }

        var actionable = humanSurfaceObject()
        actionable["actionable"] = true
        XCTAssertHumanSurfaceError(.actionableNotAllowed) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(actionable))
        }

        var click = humanSurfaceObject()
        click["click"] = ["x": 1, "y": 1]
        XCTAssertHumanSurfaceError(.forbiddenEvidenceField("click")) {
            try HumanVisualDiagnosticSurfaceParser.parse(json: json(click))
        }
    }

    func testHumanVisualDiagnosticSurfaceRejectsAutomaticPrecisionClaims() {
        for field in ["frame_support", "frame_support_pass", "classifier_pass",
                      "native_precision", "native_precision_status", "cua_returned", "e2e_pass"] {
            var claim = humanSurfaceObject()
            claim[field] = true
            XCTAssertHumanSurfaceError(.forbiddenEvidenceField(field)) {
                try HumanVisualDiagnosticSurfaceParser.parse(json: json(claim))
            }
        }
    }

    func testHumanVisualDiagnosticSurfaceRejectsDuplicateAndMissingArgument() {
        let payload = json(humanSurfaceObject())
        XCTAssertHumanSurfaceError(.duplicateArgument(HumanVisualDiagnosticSurfaceParser.argument)) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture", HumanVisualDiagnosticSurfaceParser.argument, payload,
                HumanVisualDiagnosticSurfaceParser.argument, payload
            ])
        }
        XCTAssertHumanSurfaceError(.missingArgumentValue(HumanVisualDiagnosticSurfaceParser.argument)) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture", HumanVisualDiagnosticSurfaceParser.argument
            ])
        }
        XCTAssertHumanSurfaceError(.missingArgumentValue(HumanVisualDiagnosticSurfaceParser.argument)) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture", HumanVisualDiagnosticSurfaceParser.argument, "--project-root"
            ])
        }
        XCTAssertHumanSurfaceError(.malformedArgument(HumanVisualDiagnosticSurfaceParser.argument)) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture",
                HumanVisualDiagnosticSurfaceParser.argument + "=" + payload
            ])
        }
        XCTAssertHumanSurfaceError(.conflictingArgument("--classifier-pass")) {
            try HumanVisualDiagnosticSurfaceParser.parse(arguments: [
                "visual-diagnostic-capture", "--classifier-pass", "true",
                HumanVisualDiagnosticSurfaceParser.argument, payload
            ])
        }
    }

    private func pair(sckEnd: UInt64 = 4_800_000_000) -> VisualDiagnosticCapturePair {
        let started = "2026-01-01T00:00:00.000Z"
        let cuaEnded = "2026-01-01T00:00:02.500Z"
        let sckStarted = "2026-01-01T00:00:02.600Z"
        let sckEnded = sckEnd <= 5_000_000_000
            ? "2026-01-01T00:00:04.800Z" : "2026-01-01T00:00:05.100Z"
        let timing = FullDisplayCaptureTiming(requestStartedAtISO8601: sckStarted,
            requestFinishedAtISO8601: sckEnded, requestStartMonotonicNanoseconds: 2_600_000_000,
            requestEndMonotonicNanoseconds: sckEnd)
        let witness = FullDisplayCaptureWitness(displayID: 1,
            displayBoundsPoints: CGRect(x: 0, y: 0, width: 1000, height: 800),
            contentRectPoints: CGRect(x: 0, y: 0, width: 1000, height: 800),
            imageWidthPx: 2000, imageHeightPx: 1600, pointPixelScale: 2,
            backingScaleFactor: 2, includeMenuBar: true, sourceRectAbsent: true)
        var record = CapturedFrameRecord(captureKind: .displayRect, configuration: .fullDisplayPopup,
            includedWindows: [], expectedBBoxPt: CGRect(x: 0, y: 0, width: 1000, height: 800),
            imageWidthPx: 2000, imageHeightPx: 1600, actualBBoxPt: CGRect(x: 0, y: 0, width: 1000, height: 800),
            perSideSizeDeltaPt: .zero, scale: 2, scaleSource: .pointPixelScale, backingScaleFactor: 2,
            epoch: 0, capturedAtISO8601: sckStarted, imageSHA256: String(repeating: "b", count: 64),
            stateKey: "visual-diagnostic", validity: .valid, violations: [], identity: nil)
        record.fullDisplayWitness = witness
        record.fullDisplayCaptureTiming = timing
        return VisualDiagnosticCapturePair(version: 2, sessionID: "session", cuaFrameID: String(repeating: "a", count: 64),
            cuaFrame: .init(path: "harness-development/test/cua.png", bytes: 5, sha256: String(repeating: "a", count: 64)),
            cuaRequestStartedAt: started, cuaRequestEndedAt: cuaEnded,
            cuaRequestStartMonotonicNanoseconds: "1000000000",
            cuaRequestEndMonotonicNanoseconds: "2500000000",
            sckFrameID: String(repeating: "b", count: 64),
            sckFrame: .init(path: "harness-development/test/sck.png", bytes: 9, sha256: String(repeating: "b", count: 64)),
            sckRequestStartedAt: sckStarted, sckRequestEndedAt: sckEnded,
            sckRequestStartMonotonicNanoseconds: "2600000000", sckRequestEndMonotonicNanoseconds: String(sckEnd),
            nativeInventoryStartedAt: "2026-01-01T00:00:02.510Z",
            nativeInventoryEndedAt: "2026-01-01T00:00:02.550Z",
            nativeInventoryStartMonotonicNanoseconds: "2510000000",
            nativeInventoryEndMonotonicNanoseconds: "2550000000",
            continuousClockBeforeCUA: clockWitness("1000000000"),
            continuousClockAfterSCK: clockWitness("4800000000"),
            continuousClockWitnessID: clockWitnessID,
            bundleID: "jp.naver.line.mac", pid: 42, processStartTimeSeconds: 10,
            processStartTimeMicroseconds: 0, windowID: 7, displayID: 1,
            widthPixels: 2000, heightPixels: 1600, nativeScale: 2, pointPixelScale: 2,
            cuaBoundsPoints: [0, 0, 1000, 800], sckWindowBoundsPoints: [0, 0, 1000, 800],
            displayBoundsPoints: [0, 0, 1000, 800], captureRecord: record)
    }

    func testCapturePairUsesOriginalRequestStartAndAllowsLateAnalysis() throws {
        let pair = pair()
        XCTAssertNoThrow(try pair.validated())
        let completion = VisualDiagnosticCompletion(pair: pair, analysisStatus: .insufficient,
            completedAt: "2026-01-02T00:00:00.000Z", analysisEvidence: nil)
        XCTAssertNoThrow(try completion.validated())
        XCTAssertFalse(completion.actionable)
        XCTAssertEqual(completion.actionEligibility, "INELIGIBLE")
    }

    func testCapturePairBeyondFiveSecondsIsRejected() {
        XCTAssertThrowsError(try pair(sckEnd: 5_100_000_000).validated())
    }

    func testCrossPairHashAndMissingWitnessAreRejected() throws {
        var value = pair()
        value = VisualDiagnosticCapturePair(version: value.version, sessionID: value.sessionID, cuaFrameID: value.cuaFrameID,
            cuaFrame: value.cuaFrame, cuaRequestStartedAt: value.cuaRequestStartedAt,
            cuaRequestEndedAt: value.cuaRequestEndedAt,
            cuaRequestStartMonotonicNanoseconds: value.cuaRequestStartMonotonicNanoseconds,
            cuaRequestEndMonotonicNanoseconds: value.cuaRequestEndMonotonicNanoseconds,
            sckFrameID: String(repeating: "c", count: 64), sckFrame: value.sckFrame,
            sckRequestStartedAt: value.sckRequestStartedAt, sckRequestEndedAt: value.sckRequestEndedAt,
            sckRequestStartMonotonicNanoseconds: value.sckRequestStartMonotonicNanoseconds,
            sckRequestEndMonotonicNanoseconds: value.sckRequestEndMonotonicNanoseconds,
            nativeInventoryStartedAt: value.nativeInventoryStartedAt,
            nativeInventoryEndedAt: value.nativeInventoryEndedAt,
            nativeInventoryStartMonotonicNanoseconds: value.nativeInventoryStartMonotonicNanoseconds,
            nativeInventoryEndMonotonicNanoseconds: value.nativeInventoryEndMonotonicNanoseconds,
            continuousClockBeforeCUA: value.continuousClockBeforeCUA,
            continuousClockAfterSCK: value.continuousClockAfterSCK,
            continuousClockWitnessID: value.continuousClockWitnessID,
            windowScreenAssociationStatus: value.windowScreenAssociationStatus,
            bundleID: value.bundleID, pid: value.pid, processStartTimeSeconds: value.processStartTimeSeconds,
            processStartTimeMicroseconds: value.processStartTimeMicroseconds, windowID: value.windowID,
            displayID: value.displayID, widthPixels: value.widthPixels, heightPixels: value.heightPixels,
            nativeScale: value.nativeScale, pointPixelScale: value.pointPixelScale,
            cuaBoundsPoints: value.cuaBoundsPoints, sckWindowBoundsPoints: value.sckWindowBoundsPoints,
            displayBoundsPoints: value.displayBoundsPoints, captureRecord: value.captureRecord)
        XCTAssertThrowsError(try value.validated())
    }

    func testContinuousClockRejectsDifferentDomainAndExpiredBracket() throws {
        let valid = pair()
        XCTAssertNoThrow(try valid.validated())
        let wrongDomain = VisualDiagnosticClockWitness(sessionID: "session", witnessID: clockWitnessID,
            domain: "mach_absolute_time", bootSessionUUID: bootSessionUUID,
            timebaseNumerator: 125, timebaseDenominator: 3, continuousNanoseconds: "4800000000",
            sampledAtUTC: "2026-01-01T00:00:00.000Z")
        let mismatched = VisualDiagnosticCapturePair(version: valid.version, sessionID: valid.sessionID,
            cuaFrameID: valid.cuaFrameID, cuaFrame: valid.cuaFrame,
            cuaRequestStartedAt: valid.cuaRequestStartedAt, cuaRequestEndedAt: valid.cuaRequestEndedAt,
            cuaRequestStartMonotonicNanoseconds: valid.cuaRequestStartMonotonicNanoseconds,
            cuaRequestEndMonotonicNanoseconds: valid.cuaRequestEndMonotonicNanoseconds,
            sckFrameID: valid.sckFrameID, sckFrame: valid.sckFrame,
            sckRequestStartedAt: valid.sckRequestStartedAt, sckRequestEndedAt: valid.sckRequestEndedAt,
            sckRequestStartMonotonicNanoseconds: valid.sckRequestStartMonotonicNanoseconds,
            sckRequestEndMonotonicNanoseconds: valid.sckRequestEndMonotonicNanoseconds,
            nativeInventoryStartedAt: valid.nativeInventoryStartedAt,
            nativeInventoryEndedAt: valid.nativeInventoryEndedAt,
            nativeInventoryStartMonotonicNanoseconds: valid.nativeInventoryStartMonotonicNanoseconds,
            nativeInventoryEndMonotonicNanoseconds: valid.nativeInventoryEndMonotonicNanoseconds,
            continuousClockBeforeCUA: valid.continuousClockBeforeCUA,
            continuousClockAfterSCK: wrongDomain, continuousClockWitnessID: valid.continuousClockWitnessID,
            windowScreenAssociationStatus: valid.windowScreenAssociationStatus, bundleID: valid.bundleID,
            pid: valid.pid, processStartTimeSeconds: valid.processStartTimeSeconds,
            processStartTimeMicroseconds: valid.processStartTimeMicroseconds, windowID: valid.windowID,
            displayID: valid.displayID, widthPixels: valid.widthPixels, heightPixels: valid.heightPixels,
            nativeScale: valid.nativeScale, pointPixelScale: valid.pointPixelScale,
            cuaBoundsPoints: valid.cuaBoundsPoints, sckWindowBoundsPoints: valid.sckWindowBoundsPoints,
            displayBoundsPoints: valid.displayBoundsPoints, captureRecord: valid.captureRecord)
        XCTAssertThrowsError(try mismatched.validated())

        let expired = VisualDiagnosticCapturePair(version: valid.version, sessionID: valid.sessionID,
            cuaFrameID: valid.cuaFrameID, cuaFrame: valid.cuaFrame,
            cuaRequestStartedAt: valid.cuaRequestStartedAt, cuaRequestEndedAt: valid.cuaRequestEndedAt,
            cuaRequestStartMonotonicNanoseconds: valid.cuaRequestStartMonotonicNanoseconds,
            cuaRequestEndMonotonicNanoseconds: valid.cuaRequestEndMonotonicNanoseconds,
            sckFrameID: valid.sckFrameID, sckFrame: valid.sckFrame,
            sckRequestStartedAt: valid.sckRequestStartedAt, sckRequestEndedAt: valid.sckRequestEndedAt,
            sckRequestStartMonotonicNanoseconds: valid.sckRequestStartMonotonicNanoseconds,
            sckRequestEndMonotonicNanoseconds: valid.sckRequestEndMonotonicNanoseconds,
            nativeInventoryStartedAt: valid.nativeInventoryStartedAt,
            nativeInventoryEndedAt: valid.nativeInventoryEndedAt,
            nativeInventoryStartMonotonicNanoseconds: valid.nativeInventoryStartMonotonicNanoseconds,
            nativeInventoryEndMonotonicNanoseconds: valid.nativeInventoryEndMonotonicNanoseconds,
            continuousClockBeforeCUA: clockWitness("1000000000"),
            continuousClockAfterSCK: clockWitness("6100000000"),
            continuousClockWitnessID: valid.continuousClockWitnessID,
            windowScreenAssociationStatus: valid.windowScreenAssociationStatus, bundleID: valid.bundleID,
            pid: valid.pid, processStartTimeSeconds: valid.processStartTimeSeconds,
            processStartTimeMicroseconds: valid.processStartTimeMicroseconds, windowID: valid.windowID,
            displayID: valid.displayID, widthPixels: valid.widthPixels, heightPixels: valid.heightPixels,
            nativeScale: valid.nativeScale, pointPixelScale: valid.pointPixelScale,
            cuaBoundsPoints: valid.cuaBoundsPoints, sckWindowBoundsPoints: valid.sckWindowBoundsPoints,
            displayBoundsPoints: valid.displayBoundsPoints, captureRecord: valid.captureRecord)
        XCTAssertThrowsError(try expired.validated())
    }
}
