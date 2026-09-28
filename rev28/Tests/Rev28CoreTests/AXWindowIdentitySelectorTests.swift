import CoreGraphics
import XCTest
@testable import Rev28Core

final class AXWindowIdentitySelectorTests: XCTestCase {
    private let target: UInt32 = 77
    private let bounds = CGRect(x: 100, y: 200, width: 400, height: 600)

    private func descriptor(
        number: UInt32?,
        frame: CGRect?,
        role: String? = "AXWindow",
        subrole: String? = "AXStandardWindow",
        title: String? = "LINE"
    ) -> AXWindowDescriptor {
        AXWindowDescriptor(windowNumber: number, frame: frame, role: role, subrole: subrole, title: title)
    }

    func testExactWindowNumberBindsEvenWhenAnotherWindowSharesTheFrame() throws {
        let read = try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: bounds,
            descriptors: [
                descriptor(number: 1, frame: bounds, subrole: "AXFloatingWindow"),
                descriptor(number: target, frame: bounds),
            ]
        )
        XCTAssertEqual(read.matchMethod, .windowNumber)
        XCTAssertEqual(read.subrole, "AXStandardWindow")
        XCTAssertTrue(read.isBoundToWindow)
    }

    func testAmbiguousWindowNumberRefuses() {
        XCTAssertThrowsError(try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: bounds,
            descriptors: [
                descriptor(number: target, frame: bounds),
                descriptor(number: target, frame: bounds.offsetBy(dx: 10, dy: 0)),
            ]
        )) { error in
            guard case AXWindowIdentityError.ambiguousAXWindowMatch(let windowID, let count) = error else {
                return XCTFail("unexpected \(error)")
            }
            XCTAssertEqual(windowID, target)
            XCTAssertEqual(count, 2)
        }
    }

    func testUniqueFrameMatchIsTheBindingWhenNoWindowNumberIsAvailable() throws {
        let read = try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: bounds,
            descriptors: [
                descriptor(number: nil, frame: bounds.offsetBy(dx: 0.25, dy: -0.25)),
                descriptor(number: nil, frame: bounds.offsetBy(dx: 900, dy: 0)),
            ]
        )
        XCTAssertEqual(read.matchMethod, .frameGeometry)
    }

    func testAmbiguousOrMissingFrameMatchRefuses() {
        XCTAssertThrowsError(try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: bounds,
            descriptors: [
                descriptor(number: nil, frame: bounds),
                descriptor(number: nil, frame: bounds),
            ]
        )) { error in
            guard case AXWindowIdentityError.targetWindowNotAddressable = error else {
                return XCTFail("unexpected \(error)")
            }
        }
        XCTAssertThrowsError(try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: bounds,
            descriptors: [descriptor(number: nil, frame: bounds.offsetBy(dx: 500, dy: 0))],
            frameTolerancePt: 0.5
        )) { error in
            guard case AXWindowIdentityError.targetWindowNotAddressable = error else {
                return XCTFail("unexpected \(error)")
            }
        }
    }

    func testMissingCGBoundsAndNoWindowNumbersRefuseInsteadOfChoosingTheFirstWindow() {
        XCTAssertThrowsError(try AXWindowIdentitySelector.select(
            targetWindowID: target,
            cgBounds: nil,
            descriptors: [descriptor(number: nil, frame: bounds)]
        )) { error in
            guard case AXWindowIdentityError.targetWindowNotAddressable(let windowID) = error else {
                return XCTFail("unexpected \(error)")
            }
            XCTAssertEqual(windowID, target)
        }
    }
}
