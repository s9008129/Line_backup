import XCTest
@testable import Rev28Core

final class VisualDiagnosticContractTests: XCTestCase {
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
        return VisualDiagnosticCapturePair(sessionID: "session", cuaFrameID: String(repeating: "a", count: 64),
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
        value = VisualDiagnosticCapturePair(sessionID: value.sessionID, cuaFrameID: value.cuaFrameID,
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
            windowScreenAssociationStatus: value.windowScreenAssociationStatus,
            bundleID: value.bundleID, pid: value.pid, processStartTimeSeconds: value.processStartTimeSeconds,
            processStartTimeMicroseconds: value.processStartTimeMicroseconds, windowID: value.windowID,
            displayID: value.displayID, widthPixels: value.widthPixels, heightPixels: value.heightPixels,
            nativeScale: value.nativeScale, pointPixelScale: value.pointPixelScale,
            cuaBoundsPoints: value.cuaBoundsPoints, sckWindowBoundsPoints: value.sckWindowBoundsPoints,
            displayBoundsPoints: value.displayBoundsPoints, captureRecord: value.captureRecord)
        XCTAssertThrowsError(try value.validated())
    }
}
