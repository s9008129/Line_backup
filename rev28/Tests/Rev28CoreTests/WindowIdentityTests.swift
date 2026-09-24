import CoreGraphics
import XCTest
@testable import Rev28Core

final class WindowIdentityTests: XCTestCase {
    private let process = ProcessInstanceID(pid: 4242, startTimeSeconds: 1_760_000_000, startTimeMicroseconds: 500_000)

    private func identity(
        bundleID: String = "jp.naver.line.mac",
        windowID: UInt32 = 70,
        frame: CGRect = CGRect(x: 211, y: 29, width: 327, height: 643),
        epoch: UInt64 = 7
    ) -> WindowIdentity {
        WindowIdentity(
            bundleID: bundleID,
            process: process,
            windowID: windowID,
            windowFrame: frame,
            ax: AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: "LINE"),
            cgEntry: CGWindowEntryRecord(
                windowID: windowID,
                frame: frame,
                layer: 0,
                ownerPID: process.pid,
                ownerName: "LINE"
            ),
            captureEpoch: epoch,
            captureImageSHA256: String(repeating: "a", count: 64)
        )
    }

    private func fresh(
        bundleID: String = "jp.naver.line.mac",
        process freshProcess: ProcessInstanceID? = nil,
        windowID: UInt32 = 70,
        frame: CGRect = CGRect(x: 211, y: 29, width: 327, height: 643),
        layer: Int = 0,
        isOnScreen: Bool = true
    ) -> FreshWindowObservation {
        FreshWindowObservation(
            bundleID: bundleID,
            process: freshProcess ?? process,
            windowID: windowID,
            frame: frame,
            layer: layer,
            isOnScreen: isOnScreen
        )
    }

    func testFreshIdentityHasNoViolations() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.isEmpty, "unexpected violations: \(violations)")
    }

    func testStaleWindowIDInvalidates() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(windowID: 70),
            against: fresh(windowID: 71),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.windowIDChanged(old: 70, new: 71)), "\(violations)")
    }

    func testPidReuseRejectedByStartTime() throws {
        let reused = ProcessInstanceID(pid: 4242, startTimeSeconds: 1_760_000_999, startTimeMicroseconds: 1)
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(process: reused),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.processInstanceChanged(expected: process, actual: reused)), "\(violations)")
    }

    func testBundleMismatchInvalidates() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(bundleID: "com.example.other"),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.bundleMismatch(expected: "jp.naver.line.mac", actual: "com.example.other")), "\(violations)")
    }

    func testNonZeroLayerInvalidates() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(layer: 1),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.windowLayerNotZero(layer: 1)), "\(violations)")
    }

    func testOffscreenInvalidates() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(isOnScreen: false),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.windowOffscreen), "\(violations)")
    }

    func testFrameMovementBeyondToleranceInvalidates() throws {
        let moved = CGRect(x: 213, y: 29, width: 327, height: 643)
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(frame: moved),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.frameDeltaExceedsTolerance(maxDeltaPt: 1.0)), "\(violations)")
    }

    func testFrameMovementWithinToleranceStaysValid() throws {
        let moved = CGRect(x: 211.5, y: 29.25, width: 327.2, height: 643.1)
        let violations = WindowIdentityValidator.validate(
            identity: identity(),
            against: fresh(frame: moved),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.isEmpty, "unexpected violations: \(violations)")
    }

    func testStaleEpochInvalidates() throws {
        let violations = WindowIdentityValidator.validate(
            identity: identity(epoch: 6),
            against: fresh(),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        )
        XCTAssertTrue(violations.contains(.staleEpoch(identityEpoch: 6, currentEpoch: 7)), "\(violations)")
        XCTAssertFalse(identity(epoch: 6).isValidInEpoch(7))
        XCTAssertTrue(identity(epoch: 7).isValidInEpoch(7))
    }

    func testIsFreshConvenienceMatchesViolations() throws {
        XCTAssertTrue(WindowIdentityValidator.isFresh(
            identity: identity(),
            against: fresh(),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        ))
        XCTAssertFalse(WindowIdentityValidator.isFresh(
            identity: identity(epoch: 1),
            against: fresh(),
            maxFrameDeltaPt: 1.0,
            currentEpoch: 7
        ))
    }

    func testUnionBBoxUsesAllIncludedWindows() throws {
        let main = SCWindowSnapshot(
            windowID: 70,
            frame: CGRect(x: 211, y: 29, width: 327, height: 643),
            windowLayer: 0,
            title: "LINE",
            isOnScreen: true,
            ownerPID: 4242,
            ownerBundleID: "jp.naver.line.mac",
            ownerName: "LINE"
        )
        let popup = SCWindowSnapshot(
            windowID: 71,
            frame: CGRect(x: 400, y: 29, width: 120, height: 300),
            windowLayer: 1,
            title: nil,
            isOnScreen: true,
            ownerPID: 4242,
            ownerBundleID: "jp.naver.line.mac",
            ownerName: "LINE"
        )
        let union = FrameCaptureSupport.unionBBox(of: [main, popup], fallback: .zero)
        XCTAssertEqual(union.minX, 211)
        XCTAssertEqual(union.minY, 29)
        XCTAssertEqual(union.maxX, 538)
        XCTAssertEqual(union.maxY, 672)
        XCTAssertEqual(FrameCaptureSupport.unionBBox(of: [], fallback: main.frame), main.frame)
    }

    func testDefaultConfigurationsAreExplicit() throws {
        let primary = CaptureConfiguration.primaryWindow
        XCTAssertEqual(primary.kind, .window)
        XCTAssertFalse(primary.includeChildWindows)
        XCTAssertTrue(primary.ignoreShadows, "geometry-bearing captures must bar shadow inflation")
        XCTAssertFalse(primary.showsCursor)
        let union = CaptureConfiguration.childUnion
        XCTAssertEqual(union.kind, .windowUnionWithChildWindows)
        XCTAssertTrue(union.includeChildWindows)
        XCTAssertTrue(union.ignoreShadows)
        XCTAssertFalse(union.showsCursor)
    }
}
