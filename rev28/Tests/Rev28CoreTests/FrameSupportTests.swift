import XCTest
@testable import Rev28Core

final class FrameSupportTests: XCTestCase {
    func testNonMenuSurfaceGeometryProducesDiagnosticIntersectionOnly() throws {
        let result = try NonMenuFrameSupportEvaluation.measure(surfaceBoundsPx: [40, 80, 800, 600],
            frameWidthPx: 1600, frameHeightPx: 1000, uncertaintyPx: 2).get()
        XCTAssertEqual(result.intersectionPx, [40, 80, 800, 600])
        XCTAssertEqual(result.referencePointPx, [440, 380])
        XCTAssertEqual(result.safeMarginPx, 300)
    }

    func testNonMenuSurfaceGeometryRejectsClippingAndWeakMargins() {
        XCTAssertEqual(NonMenuFrameSupportEvaluation.measure(surfaceBoundsPx: [0, 0, 101, 40],
            frameWidthPx: 100, frameHeightPx: 100, uncertaintyPx: 2), .failure(.surfaceOutsideFrame))
        XCTAssertEqual(NonMenuFrameSupportEvaluation.measure(surfaceBoundsPx: [0, 0, 20, 20],
            frameWidthPx: 100, frameHeightPx: 100, uncertaintyPx: 8), .failure(.safeMarginTooSmall))
        XCTAssertEqual(NonMenuFrameSupportEvaluation.measure(surfaceBoundsPx: [0, 0, 15, 40],
            frameWidthPx: 100, frameHeightPx: 100, uncertaintyPx: 2), .failure(.intersectionTooSmall))
    }

    func testFullDisplayTimingKeepsTheOriginalMonotonicRequestInterval() {
        let timing = FullDisplayCaptureTiming(requestStartedAtISO8601: "2026-10-10T12:00:00.000Z",
            requestFinishedAtISO8601: "2026-10-10T12:00:00.025Z",
            requestStartMonotonicNanoseconds: 1_000_000_000,
            requestEndMonotonicNanoseconds: 1_025_000_000)
        XCTAssertEqual(timing.durationMilliseconds, 25, accuracy: 0.001)
        let invalid = FullDisplayCaptureTiming(requestStartedAtISO8601: "start",
            requestFinishedAtISO8601: "end", requestStartMonotonicNanoseconds: 2,
            requestEndMonotonicNanoseconds: 1)
        XCTAssertEqual(invalid.durationMilliseconds, .infinity)
    }

    func testFullDisplayWitnessBindsTheSelectedDisplayAndWholeDisplayImage() throws {
        let result = try FullDisplayCaptureSupport.evaluate(configuration: .fullDisplayPopup,
            displayBoundsPt: CGRect(x: -120, y: 30, width: 800, height: 600), displayID: 17,
            pointPixelScale: 2, backingScaleFactor: 2, includeMenuBar: true,
            contentRect: CGRect(x: -120, y: 0, width: 800, height: 700),
            imageWidthPx: 1600, imageHeightPx: 1200).get()
        XCTAssertEqual(result.witness.displayID, 17)
        XCTAssertEqual(result.witness.displayBoundsPoints, CGRect(x: -120, y: 30, width: 800, height: 600))
        XCTAssertTrue(result.witness.includeMenuBar)
        XCTAssertTrue(result.witness.sourceRectAbsent)
    }
}
