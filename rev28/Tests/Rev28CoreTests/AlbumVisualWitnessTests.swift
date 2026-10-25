import CoreGraphics
import XCTest
@testable import Rev28Core

final class AlbumVisualWitnessTests: XCTestCase {
    private let binding = SurfaceBinding(
        bundleID: "jp.naver.line.mac",
        process: ProcessInstanceID(pid: 42, startTimeSeconds: 1_700_000_000, startTimeMicroseconds: 10),
        windowID: 7,
        captureEpoch: 9,
        frameSHA256: String(repeating: "a", count: 64)
    )

    private func ocr(_ text: String, _ rect: CGRect) -> OcrItem {
        let points = [
            CapturePixelPoint(x: rect.minX, y: rect.minY),
            CapturePixelPoint(x: rect.maxX, y: rect.minY),
            CapturePixelPoint(x: rect.minX, y: rect.maxY),
            CapturePixelPoint(x: rect.maxX, y: rect.maxY),
        ]
        return OcrItem(text: text, confidence: 0.99, candidateCount: 1,
                       quadCapturePx: points, boundingBoxCapturePx: rect)
    }

    private var observation: AlbumCardVisualObservation {
        AlbumCardVisualObservation(
            identity: "card-20240513-57",
            source: .completeVisualCard,
            cardBoundsCapturePx: CGRect(x: 10, y: 20, width: 320, height: 150),
            thumbnailBoundsCapturePx: CGRect(x: 20, y: 35, width: 105, height: 120),
            metadataBoundsCapturePx: CGRect(x: 140, y: 35, width: 175, height: 110),
            controlBoundsCapturePx: [CGRect(x: 285, y: 25, width: 30, height: 25)],
            anchors: [
                AlbumVisualAnchor(id: "top-left", boundsCapturePx: CGRect(x: 11, y: 21, width: 5, height: 5)),
                AlbumVisualAnchor(id: "top-right", boundsCapturePx: CGRect(x: 320, y: 21, width: 5, height: 5)),
                AlbumVisualAnchor(id: "bottom-left", boundsCapturePx: CGRect(x: 11, y: 160, width: 5, height: 5)),
            ]
        )
    }

    private var items: [OcrItem] {
        [
            ocr("2024/05/13~05/17", CGRect(x: 155, y: 65, width: 130, height: 18)),
            ocr("57", CGRect(x: 155, y: 100, width: 24, height: 16)),
        ]
    }

    func testBuildsWitnessOnlyFromCompleteCardAndKeepsSafePointInsideClearArea() {
        let result = AlbumVisualWitnessBuilder.derive(
            observation: observation,
            ocrItems: items,
            expectedDateRange: "2024/05/13~05/17",
            expectedPhotoCount: "57",
            binding: binding
        )
        guard case let .success(witness) = result else { return XCTFail("expected complete card witness: \(result)") }
        XCTAssertEqual(witness.binding, binding)
        XCTAssertTrue(witness.safeRectCapturePx.contains(CGPoint(x: witness.pointCapturePx.x, y: witness.pointCapturePx.y)))
        XCTAssertFalse(witness.safeRectCapturePx.intersects(witness.thumbnailBoundsCapturePx))
        XCTAssertFalse(witness.safeRectCapturePx.intersects(witness.metadataBoundsCapturePx))
        XCTAssertTrue(witness.cardBoundsCapturePx.contains(witness.safeRectCapturePx))
    }

    func testDateFragmentCannotReplaceMissingCompleteCardThumbnailEvidence() {
        let incomplete = AlbumCardVisualObservation(
            identity: "date-only",
            source: .completeVisualCard,
            cardBoundsCapturePx: observation.cardBoundsCapturePx,
            thumbnailBoundsCapturePx: nil,
            metadataBoundsCapturePx: observation.metadataBoundsCapturePx,
            anchors: observation.anchors
        )
        let result = AlbumVisualWitnessBuilder.derive(
            observation: incomplete,
            ocrItems: items,
            expectedDateRange: "2024/05/13~05/17",
            expectedPhotoCount: "57",
            binding: binding
        )
        guard case .failure(.missingThumbnail) = result else { return XCTFail("expected missing thumbnail refusal") }
    }

    func testCrossPairedCountOutsideMetadataRefuses() {
        let result = AlbumVisualWitnessBuilder.derive(
            observation: observation,
            ocrItems: [items[0], ocr("57", CGRect(x: 200, y: 130, width: 24, height: 16))],
            expectedDateRange: "2024/05/13~05/17",
            expectedPhotoCount: "57",
            binding: binding
        )
        guard case .failure(.metadataNotAssociated) = result else { return XCTFail("expected metadata association refusal") }
    }
}
