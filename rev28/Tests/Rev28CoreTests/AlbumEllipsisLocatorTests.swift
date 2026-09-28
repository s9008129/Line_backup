import CoreGraphics
import Foundation
import ImageIO
import XCTest
@testable import Rev28Core

final class AlbumEllipsisLocatorTests: XCTestCase {
    private let binding = SurfaceBinding(
        bundleID: "com.example.target",
        process: ProcessInstanceID(pid: 10, startTimeSeconds: 1, startTimeMicroseconds: 0),
        windowID: 10,
        captureEpoch: 9,
        frameSHA256: String(repeating: "e", count: 64)
    )
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
        // CoreGraphics user coordinates are bottom-left. The reviewed frame puts
        // the album ellipsis at top-left y 44/49.5/55, so drawing 46/52/58 px
        // above the bottom edge must be detected at top-left y 44.5/50.5/56.5.
        for y in [height - 46, height - 52, height - 58] {
            context.fill(CGRect(x: 304, y: y, width: 2, height: 2))
        }
        guard let image = context.makeImage() else { return XCTFail("image") }
        let dots = try EllipsisPixelDetector.detect(image: image)
        XCTAssertGreaterThanOrEqual(dots.count, 3)
        let near = dots.filter { abs($0.center.x - 304.5) < 2 }
        XCTAssertGreaterThanOrEqual(near.count, 3)
        // The detector reports top-left capture rows; a bottom-up row scan
        // silently mirrors every y and breaks the title-band containment test.
        XCTAssertEqual(near.map(\.center.y).sorted(), [44.5, 50.5, 56.5], "detected rows must be top-left capture rows")
    }

    func testPixelDetectorReportsTopLeftRowsForKnownRasterRows() throws {
        let width = 40, height = 60
        var raster = [UInt8](repeating: 255, count: width * height)
        // A CGImage data provider stores row 0 as the topmost image row, so
        // these are top-left capture rows: 4, 12 and 20.
        for row in [4, 5, 12, 13, 20, 21] {
            for x in 30..<32 { raster[row * width + x] = 0 }
        }
        let image = try XCTUnwrap(Self.grayImage(raster: raster, width: width, height: height))
        let rows = try EllipsisPixelDetector.detect(image: image).map(\.center.y).sorted()
        XCTAssertEqual(rows.count, 3, "expected the three compact dots, got rows \(rows)")
        guard rows.count == 3 else { return }
        for (observed, expected) in zip(rows, [4.5, 12.5, 20.5]) {
            XCTAssertEqual(observed, expected, accuracy: 1.0, "detected row \(observed) is not top-left row \(expected)")
        }
    }

    /// End-to-end: a fresh capture whose ellipsis triple sits in the reviewed
    /// header band above the title box must locate from pixel structure alone.
    func testPixelStructureLocatesEllipsisAboveTitleBoxInFreshCapture() throws {
        let title = CGRect(x: 20, y: 100, width: 140, height: 20)
        let image = try XCTUnwrap(Self.captureImageWithTopBandEllipsis(width: 400, height: 600))
        let result = try AlbumEllipsisLocator.locate(
            image: image,
            ocrItems: [
                text("2024/05/13~05/17", title),
                text("57張照片", CGRect(x: 20, y: 140, width: 100, height: 18)),
            ],
            titleBoxCapturePx: title,
            binding: binding
        )
        guard case let .candidate(candidate) = result else {
            return XCTFail("expected an eligible ellipsis from fresh pixels, got \(result)")
        }
        XCTAssertEqual(candidate.identity, "album-ellipsis")
        XCTAssertEqual(candidate.pointCapturePx.x, 351.5, accuracy: 1.0)
        XCTAssertEqual(candidate.pointCapturePx.y, 56.5, accuracy: 1.0)
    }

    /// Real-pixel regression against the reviewed v5 ground truth recorded in
    /// `evidence/20260919-rev25-baseline/attempt-01/v5-offline-replay.json`:
    /// a fresh decode of the reviewed frame must reproduce its three dots at
    /// top-left y 44/49.5/55 and locate the same middle point.
    func testPixelDetectorReproducesReviewedV5FrameDots() throws {
        let repoRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let frameURL = repoRoot
            .appendingPathComponent("evidence/20260917-vision-reader/frames/route5r_frame_post.jpg")
        guard let source = CGImageSourceCreateWithURL(frameURL as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw XCTSkip("reviewed v5 frame fixture is unavailable at \(frameURL.path)")
        }
        XCTAssertEqual(
            try EvidenceIO.sha256Hex(ofFileAt: frameURL),
            "4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3",
            "reviewed v5 frame fixture drifted"
        )
        XCTAssertEqual(image.width, 327)
        XCTAssertEqual(image.height, 643)

        let rows = try EllipsisPixelDetector.detect(image: image)
            .filter { abs($0.center.x - 304.5) < 1.5 && $0.center.y < 70 }
            .map(\.center.y)
            .sorted()
        XCTAssertEqual(rows.count, 3, "expected the reviewed ellipsis triple at rows \(rows)")
        guard rows.count == 3 else { return }
        for (observed, expected) in zip(rows, [44.0, 49.5, 55.0]) {
            XCTAssertEqual(observed, expected, accuracy: 1.0, "reviewed dot row drifted")
        }

        let result = try AlbumEllipsisLocator.locate(
            image: image,
            ocrItems: [],
            titleBoxCapturePx: titleBox,
            binding: binding
        )
        guard case let .candidate(candidate) = result else {
            return XCTFail("reviewed v5 frame must locate, got \(result)")
        }
        XCTAssertEqual(candidate.pointCapturePx.x, 304.5, accuracy: 0.001)
        XCTAssertEqual(candidate.pointCapturePx.y, 49.5, accuracy: 0.001)
    }

    private static func grayImage(raster: [UInt8], width: Int, height: Int) -> CGImage? {
        guard let provider = CGDataProvider(data: Data(raster) as CFData) else { return nil }
        return CGImage(
            width: width,
            height: height,
            bitsPerComponent: 8,
            bitsPerPixel: 8,
            bytesPerRow: width,
            space: CGColorSpaceCreateDeviceGray(),
            bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.none.rawValue),
            provider: provider,
            decode: nil,
            shouldInterpolate: false,
            intent: .defaultIntent
        )
    }

    private static func captureImageWithTopBandEllipsis(width: Int, height: Int) -> CGImage? {
        guard let context = CGContext(
            data: nil, width: width, height: height, bitsPerComponent: 8,
            bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        // Draw in top-left capture coordinates so a drawn y is a capture row.
        context.translateBy(x: 0, y: CGFloat(height))
        context.scaleBy(x: 1, y: -1)
        context.setFillColor(CGColor(red: 0.92, green: 0.92, blue: 0.94, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        context.setFillColor(CGColor(red: 0.05, green: 0.05, blue: 0.05, alpha: 1))
        for index in 0..<3 {
            context.fill(CGRect(x: 350, y: 50 + CGFloat(index) * 5, width: 3, height: 3))
        }
        return context.makeImage()
    }
}
