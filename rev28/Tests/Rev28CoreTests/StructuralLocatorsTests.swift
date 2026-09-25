import CoreGraphics
import XCTest
@testable import Rev28Core

final class StructuralLocatorsTests: XCTestCase {
    private let binding = SurfaceBinding(windowID: 7, captureEpoch: 11, frameSHA256: String(repeating: "a", count: 64))

    private func item(_ text: String, _ rect: CGRect) -> OcrItem {
        OcrItem(
            text: text,
            confidence: 1,
            candidateCount: 1,
            quadCapturePx: [
                CapturePixelPoint(x: rect.minX, y: rect.minY),
                CapturePixelPoint(x: rect.maxX, y: rect.minY),
                CapturePixelPoint(x: rect.minX, y: rect.maxY),
                CapturePixelPoint(x: rect.maxX, y: rect.maxY),
            ],
            boundingBoxCapturePx: rect
        )
    }

    func testAlbumCardRequiresExactUniqueTitleAndCount() {
        let result = StructuralLocators.locateAlbumCard(
            items: [
                item("2024/05/13~05/17", CGRect(x: 20, y: 40, width: 150, height: 20)),
                item("57", CGRect(x: 20, y: 70, width: 20, height: 15)),
            ],
            cardBounds: CGRect(x: 0, y: 20, width: 300, height: 100),
            binding: binding
        )
        guard case let .candidate(candidate) = result else { return XCTFail("expected candidate") }
        XCTAssertEqual(candidate.identity, "2024/05/13~05/17|57")
        XCTAssertTrue(candidate.safeRectCapturePx.contains(CGPoint(x: candidate.pointCapturePx.x, y: candidate.pointCapturePx.y)))
    }

    func testAlbumCardDuplicateCountRefusesAmbiguity() {
        let result = StructuralLocators.locateAlbumCard(
            items: [
                item("2024/05/13~05/17", CGRect(x: 20, y: 40, width: 150, height: 20)),
                item("57", CGRect(x: 20, y: 70, width: 20, height: 15)),
                item("57", CGRect(x: 80, y: 70, width: 20, height: 15)),
            ],
            cardBounds: CGRect(x: 0, y: 20, width: 300, height: 100),
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .ambiguousIdentity)
    }

    func testAlbumDetailRejectsWrongZhenGlyph() {
        let items = [
            item("旻謙允楨成長日記", CGRect(x: 0, y: 0, width: 100, height: 20)),
            item("57張照片", CGRect(x: 0, y: 30, width: 50, height: 20)),
        ]
        switch StructuralLocators.verifyAlbumDetail(items: items, groupTitle: "旻謙允禎成長日記") {
        case .success: XCTFail("wrong glyph must not match")
        case let .failure(error): XCTAssertEqual(error.refusal, .missingIdentity)
        }
    }

    private func validRows() -> [MenuRowObservation] {
        StructuralLocators.lineAlbumMenuReference.enumerated().map { index, text in
            MenuRowObservation(
                text: text,
                bandCapturePx: CGRect(x: 40, y: 20 + CGFloat(index) * 50, width: 140, height: 24)
            )
        }
    }

    func testSaveAllRequiresFullReferenceStructure() {
        let result = StructuralLocators.locateSaveAll(
            rows: validRows(),
            menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270),
            addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270),
            binding: binding
        )
        guard case let .candidate(candidate) = result else { return XCTFail("expected candidate") }
        XCTAssertEqual(candidate.identity, "儲存全部")
        XCTAssertTrue(candidate.safeRectCapturePx.contains(CGPoint(x: candidate.pointCapturePx.x, y: candidate.pointCapturePx.y)))
    }

    func testSaveAllWrongNeighborRowFailsClosed() {
        var rows = validRows()
        rows[1] = MenuRowObservation(text: "修改名稱", bandCapturePx: rows[1].bandCapturePx)
        let result = StructuralLocators.locateSaveAll(
            rows: rows,
            menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270),
            addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270),
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .referenceStructureMismatch)
    }

    func testSaveAllDuplicateTargetFailsClosed() {
        var rows = validRows()
        rows[3] = MenuRowObservation(text: "儲存全部", bandCapturePx: rows[3].bandCapturePx)
        let result = StructuralLocators.locateSaveAll(
            rows: rows,
            menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270),
            addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270),
            binding: binding
        )
        guard case let .refused(reason, _) = result else { return XCTFail("expected refusal") }
        XCTAssertEqual(reason, .ambiguousIdentity)
    }

    func testCandidateCannotBeReusedAcrossEpoch() {
        let located = StructuralLocators.locateSaveAll(
            rows: validRows(),
            menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270),
            addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270),
            binding: binding
        )
        guard case let .candidate(candidate) = located else { return XCTFail("expected candidate") }
        let fresh = SurfaceBinding(windowID: 7, captureEpoch: 12, frameSHA256: String(repeating: "b", count: 64))
        guard case let .refused(reason, _) = StructuralLocators.revalidate(candidate: candidate, against: fresh) else {
            return XCTFail("stale candidate must refuse")
        }
        XCTAssertEqual(reason, .staleBinding)
    }
}
