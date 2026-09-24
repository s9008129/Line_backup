import CoreGraphics
import XCTest
@testable import Rev28Core

final class CoordinateTransformTests: XCTestCase {
    // MARK: Transform round-trips (all spaces, scale 2.0)

    func testRoundTripsPreservePoint() throws {
        let geometry = CaptureGeometry(
            windowFrame: CGRect(x: 211, y: 29, width: 400, height: 332),
            captureBBox: CGRect(x: 211, y: 29, width: 400, height: 332),
            scale: 2.0
        )
        let samples: [WindowLocalPoint] = [
            WindowLocalPoint(x: 0, y: 0),
            WindowLocalPoint(x: 12.5, y: 33.25),
            WindowLocalPoint(x: 399.5, y: 331.75),
            WindowLocalPoint(x: 187.125, y: 0.5),
        ]
        for sample in samples {
            let screen = geometry.screenPoint(fromWindowLocal: sample)
            let capturePx = geometry.capturePixelPoint(fromWindowLocal: sample)
            let backFromScreen = geometry.windowLocalPoint(fromScreen: screen)
            let backFromCapture = geometry.windowLocalPoint(fromCapturePixel: capturePx)
            XCTAssertEqual(backFromScreen.x, sample.x, accuracy: 1e-9, "screen->window round trip x")
            XCTAssertEqual(backFromScreen.y, sample.y, accuracy: 1e-9, "screen->window round trip y")
            XCTAssertEqual(backFromCapture.x, sample.x, accuracy: 1e-9, "px->window round trip x")
            XCTAssertEqual(backFromCapture.y, sample.y, accuracy: 1e-9, "px->window round trip y")
            let screenFromPx = geometry.screenPoint(fromCapturePixel: capturePx)
            XCTAssertEqual(screenFromPx.x, screen.x, accuracy: 1e-9)
            XCTAssertEqual(screenFromPx.y, screen.y, accuracy: 1e-9)
        }
    }

    func testWindowLocalToScreenUsesWindowOriginOnly() throws {
        let geometry = CaptureGeometry(
            windowFrame: CGRect(x: 211, y: 29, width: 400, height: 332),
            captureBBox: CGRect(x: 210, y: 28, width: 402, height: 334),
            scale: 2.0
        )
        let screen = geometry.screenPoint(fromWindowLocal: WindowLocalPoint(x: 10, y: 20))
        XCTAssertEqual(screen.x, 221, accuracy: 1e-9)
        XCTAssertEqual(screen.y, 49, accuracy: 1e-9)
    }

    func testCapturePixelConversionUsesRecordedBBox() throws {
        let geometry = CaptureGeometry(
            windowFrame: CGRect(x: 100, y: 100, width: 400, height: 300),
            captureBBox: CGRect(x: 99, y: 99, width: 402, height: 302),
            scale: 2.0
        )
        let px = geometry.capturePixelPoint(fromScreen: ScreenPoint(x: 100, y: 100))
        XCTAssertEqual(px.x, 2, accuracy: 1e-9, "must use recorded bbox, not window frame")
        XCTAssertEqual(px.y, 2, accuracy: 1e-9)
    }

    // MARK: Validated tolerance geometry (never exact equality)

    private let state = CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true)

    private func ruleBook(
        maxPerSideDelta: Double,
        originPadding: Double = 0,
        maxOriginPadding: Double = 0
    ) -> CaptureGeometryRuleBook {
        CaptureGeometryRuleBook(
            ruleID: "unit-test",
            frozenAtISO8601: "2026-09-25T00:00:00+08:00",
            rules: [
                CaptureGeometryRules.stateKey(state): CaptureGeometryRule(
                    maxPerSideSizeDeltaPt: maxPerSideDelta,
                    originPaddingPt: originPadding,
                    maxOriginPaddingPt: maxOriginPadding,
                    notes: "unit test rule"
                )
            ]
        )
    }

    func testExactGeometryPassesWithinRule() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 800,
            imageHeightPx: 664,
            scale: 2.0,
            ruleBook: ruleBook(maxPerSideDelta: 1.0),
            state: state
        )
        switch result {
        case let .success(evaluation):
            XCTAssertEqual(evaluation.actualBBoxPt.minX, 100, accuracy: 1e-9)
            XCTAssertEqual(evaluation.actualBBoxPt.minY, 50, accuracy: 1e-9)
            XCTAssertEqual(evaluation.perSideSizeDeltaPt.maximum, 0, accuracy: 1e-9)
        case let .failure(violation):
            XCTFail("expected success, got \(violation)")
        }
    }

    func testSmallDeltaWithinTolerancePasses() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        // 802x668 px at scale 2 => 401x334 pt => +0.5 pt/side width, +1.0 pt/side height.
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 802,
            imageHeightPx: 668,
            scale: 2.0,
            ruleBook: ruleBook(maxPerSideDelta: 1.0),
            state: state
        )
        switch result {
        case let .success(evaluation):
            XCTAssertEqual(evaluation.perSideSizeDeltaPt.left, 0.5, accuracy: 1e-9)
            XCTAssertEqual(evaluation.perSideSizeDeltaPt.top, 1.0, accuracy: 1e-9)
        case let .failure(violation):
            XCTFail("expected success, got \(violation)")
        }
    }

    func testDeltaBeyondToleranceFailsClosed() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        // 806x670 px at scale 2 => +1.5 pt/side width, +1.5 pt/side height.
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 806,
            imageHeightPx: 670,
            scale: 2.0,
            ruleBook: ruleBook(maxPerSideDelta: 1.0),
            state: state
        )
        guard case let .failure(violation) = result else {
            return XCTFail("expected sizeDeltaExceedsTolerance")
        }
        guard case let .sizeDeltaExceedsTolerance(_, perSide, allowed) = violation else {
            return XCTFail("unexpected violation \(violation)")
        }
        XCTAssertEqual(perSide.maximum, 1.5, accuracy: 1e-9)
        XCTAssertEqual(allowed, 1.0, accuracy: 1e-9)
    }

    func testNoFrozenRuleFailsClosed() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 800,
            imageHeightPx: 664,
            scale: 2.0,
            ruleBook: nil,
            state: state
        )
        guard case let .failure(violation) = result else {
            return XCTFail("expected noFrozenRule")
        }
        guard case .noFrozenRule = violation else {
            return XCTFail("unexpected violation \(violation)")
        }
    }

    func testStateWithoutRuleFailsClosed() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        let otherState = CaptureGeometryState(settled: false, activated: true, includeChildWindows: false, ignoreShadows: true)
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 800,
            imageHeightPx: 664,
            scale: 2.0,
            ruleBook: ruleBook(maxPerSideDelta: 1.0),
            state: otherState
        )
        guard case let .failure(violation) = result else {
            return XCTFail("expected noFrozenRule for unregistered state")
        }
        guard case .noFrozenRule = violation else {
            return XCTFail("unexpected violation \(violation)")
        }
    }

    func testFrozenOriginPaddingShiftsRecordedBBox() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 800,
            imageHeightPx: 664,
            scale: 2.0,
            ruleBook: ruleBook(maxPerSideDelta: 0.0, originPadding: 1.0, maxOriginPadding: 1.0),
            state: state
        )
        switch result {
        case let .success(evaluation):
            XCTAssertEqual(evaluation.actualBBoxPt.minX, 99, accuracy: 1e-9)
            XCTAssertEqual(evaluation.actualBBoxPt.minY, 49, accuracy: 1e-9)
            XCTAssertEqual(evaluation.actualBBoxPt.width, 400, accuracy: 1e-9)
        case let .failure(violation):
            XCTFail("expected success, got \(violation)")
        }
    }

    func testPaddingBeyondMaximumFailsClosed() throws {
        let expected = CGRect(x: 100, y: 50, width: 400, height: 332)
        let badBook = CaptureGeometryRuleBook(
            ruleID: "bad",
            frozenAtISO8601: "2026-09-25T00:00:00+08:00",
            rules: [
                CaptureGeometryRules.stateKey(state): CaptureGeometryRule(
                    maxPerSideSizeDeltaPt: 1.0,
                    originPaddingPt: 4.0,
                    maxOriginPaddingPt: 1.0
                )
            ]
        )
        let result = CaptureGeometryRules.evaluate(
            expectedBBox: expected,
            imageWidthPx: 800,
            imageHeightPx: 664,
            scale: 2.0,
            ruleBook: badBook,
            state: state
        )
        guard case let .failure(violation) = result else {
            return XCTFail("expected originPaddingNotRepresentable")
        }
        guard case .originPaddingNotRepresentable = violation else {
            return XCTFail("unexpected violation \(violation)")
        }
    }

    // MARK: Independent scale check (invariant 3)

    func testScaleMismatchDetected() throws {
        XCTAssertNil(CaptureGeometryRules.validateScale(pointPixelScale: 2.0, backingScaleFactor: 2.0))
        let violation = CaptureGeometryRules.validateScale(pointPixelScale: 2.0, backingScaleFactor: 1.0)
        guard case let .scaleMismatch(point, backing)? = violation else {
            return XCTFail("expected scaleMismatch")
        }
        XCTAssertEqual(point, 2.0)
        XCTAssertEqual(backing, 1.0)
    }

    // MARK: Safe-interior margin rule (invariant 5)

    func testSafeInteriorMarginRefusesNearBoundary() throws {
        let rect = CGRect(x: 0, y: 0, width: 100, height: 50)
        XCTAssertTrue(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 50, y: 25), safeRect: rect))
        XCTAssertTrue(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 1.0, y: 25), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 0.999, y: 25), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 99.001, y: 25), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 50, y: 0.5), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 50, y: 49.5), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: -1, y: 25), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 101, y: 25), safeRect: rect))
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 50, y: 25), safeRect: .zero))
    }
}
