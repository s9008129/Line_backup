import CoreGraphics
import XCTest
@testable import Rev28Core

final class AlbumEllipsisLocatorTests: XCTestCase {
    private let binding = SurfaceBinding(windowID: 10, captureEpoch: 9, frameSHA256: String(repeating: "e", count: 64))
    private let titleBox = CGRect(x: 15, y: 83, width: 189, height: 28)

    private func dot(_ x: Double, _ y: Double, area: Int = 4) -> EllipsisDotComponent {
        EllipsisDotComponent(center: CapturePixelPoint(x: x, y: y), area: area, width: 2, height: 2)
    }

    private func text(_ value: String, _ rect: CGRect) -> OcrItem {
        OcrItem(
            text: value,
            confidence: 1,
            candidateCount: 1,
            quadCapturePx: [],
            boundingBoxCapturePx: rect
        )
    }

    func testReviewedV5GeometryLocatesAlbumEllipsis() {
        let result = AlbumEllipsisLocator.locate(
            dots: [dot(304.5, 44), dot(304.5, 49.5), dot(304.5, 55)],
            imageSize: CGSize(width: 327, height: 643),
            ocrItems: [],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .candidate(candidate) = result else { return XCTFail("expected eligible ellipsis") }
        XCTAssertEqual(candidate.identity, "album-ellipsis")
        XCTAssertEqual(candidate.pointCapturePx.x, 304.5, accuracy: 0.001)
        XCTAssertEqual(candidate.pointCapturePx.y, 49.5, accuracy: 0.001)
    }

    func testWrongSpacingFailsClosed() {
        let result = AlbumEllipsisLocator.locate(
            dots: [dot(304.5, 40), dot(304.5, 52), dot(304.5, 64)],
            imageSize: CGSize(width: 327, height: 643),
            ocrItems: [],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .missingIdentity)
    }

    func testTwoEligibleTriplesAreAmbiguous() {
        let result = AlbumEllipsisLocator.locate(
            dots: [
                dot(280, 44), dot(280, 49.5), dot(280, 55),
                dot(304.5, 44), dot(304.5, 49.5), dot(304.5, 55),
            ],
            imageSize: CGSize(width: 327, height: 643),
            ocrItems: [],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .ambiguousIdentity)
    }

    func testTextGlyphTripleIsBlocked() {
        let result = AlbumEllipsisLocator.locate(
            dots: [dot(304.5, 44), dot(304.5, 49.5), dot(304.5, 55)],
            imageSize: CGSize(width: 327, height: 643),
            ocrItems: [text("ABC", CGRect(x: 295, y: 38, width: 20, height: 24))],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .missingIdentity)
    }

    func testTitleStripTripleIsNotEligible() {
        let result = AlbumEllipsisLocator.locate(
            dots: [dot(304.5, 88), dot(304.5, 94), dot(304.5, 100)],
            imageSize: CGSize(width: 327, height: 643),
            ocrItems: [],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .missingIdentity)
    }

    func testPixelDetectorFindsSyntheticThreeDots() throws {
        let width = 327, height = 180
        let colorSpace = CGColorSpaceCreateDeviceGray()
        guard let context = CGContext(
            data: nil, width: width, height: height, bitsPerComponent: 8,
            bytesPerRow: width, space: colorSpace, bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else { return XCTFail("context") }
        context.setFillColor(gray: 1, alpha: 1)
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        context.setFillColor(gray: 0, alpha: 1)
        // CoreGraphics user coordinates are bottom-left; detector normalizes the
        // resulting image into top-left capture coordinates.
        for y in [height - 46, height - 52, height - 58] {
            context.fill(CGRect(x: 304, y: y, width: 2, height: 2))
        }
        guard let image = context.makeImage() else { return XCTFail("image") }
        let dots = try EllipsisPixelDetector.detect(image: image)
        XCTAssertGreaterThanOrEqual(dots.count, 3)
        let near = dots.filter { abs($0.center.x - 304.5) < 2 }
        XCTAssertGreaterThanOrEqual(near.count, 3)
    }
}
