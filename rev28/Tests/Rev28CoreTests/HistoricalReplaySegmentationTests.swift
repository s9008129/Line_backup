import CoreGraphics
import CryptoKit
import Foundation
import XCTest
@testable import Rev28Core

/// Replays pinned historical observations through the current production path
/// with actual segmentation: album card regions are derived from the recorded
/// OCR anchors instead of trusting a pre-supplied region. Fixture bytes are
/// verified against the current pinned manifest before any replay runs.
final class HistoricalReplaySegmentationTests: XCTestCase {
    private static let pinnedFixtures: [String: String] = [
        "evidence/20260916-route/attempt-12/album-card-locate-v6.json":
            "05bcea90f31587435a1c16b522938eeabc32b06788d4d85b002559eb5b036875",
        "evidence/20260916-route/attempt-16/s1-window-ocr.json":
            "ddf202f0dbc6854159b6180d55c43bccc2299ac085689774ec46ec2a3739ae0a",
    ]

    private var repositoryRoot: URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent() // Rev28CoreTests
            .deletingLastPathComponent() // Tests
            .deletingLastPathComponent() // rev28
            .deletingLastPathComponent() // repository root
    }

    private func pinnedJSON(_ relativePath: String) throws -> [String: Any] {
        let url = repositoryRoot.appendingPathComponent(relativePath)
        let data = try Data(contentsOf: url)
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        XCTAssertEqual(
            digest,
            Self.pinnedFixtures[relativePath],
            "fixture bytes must match the pinned manifest: \(relativePath)"
        )
        return try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
    }

    private func numbers(_ value: Any?) throws -> [Double] {
        let array = try XCTUnwrap(value as? [Any], "expected a numeric array")
        return try array.map { try XCTUnwrap(($0 as? NSNumber)?.doubleValue, "non-numeric value") }
    }

    private func rectangle(_ values: [Double], endpoints: Bool) throws -> CGRect {
        let values = try XCTUnwrap(values.count == 4 ? values : nil, "rectangle needs four numbers")
        return CGRect(
            x: values[0],
            y: values[1],
            width: endpoints ? values[2] - values[0] : values[2],
            height: endpoints ? values[3] - values[1] : values[3]
        )
    }

    private func item(_ text: String, _ rect: CGRect) -> OcrItem {
        OcrItem(text: text, confidence: 1, candidateCount: 1, quadCapturePx: [], boundingBoxCapturePx: rect)
    }

    private func binding(windowID: UInt32, frameSHA256: String) -> SurfaceBinding {
        SurfaceBinding(
            bundleID: "replay.rev28.fixture",
            process: ProcessInstanceID(pid: 1, startTimeSeconds: 1, startTimeMicroseconds: 0),
            windowID: windowID,
            captureEpoch: 1,
            frameSHA256: frameSHA256
        )
    }

    func testAttempt12AlbumCardSegmentationReplay() throws {
        let album = try pinnedJSON("evidence/20260916-route/attempt-12/album-card-locate-v6.json")
        let title = try XCTUnwrap(album["title"] as? [String: Any])
        let titleBox = try rectangle(try numbers(title["bbox"]), endpoints: true)
        let countBox = try rectangle(try numbers(album["count_box"]), endpoints: true)
        let frameSize = try numbers(album["frame_size"])
        let binding = binding(windowID: 2, frameSHA256: try XCTUnwrap(album["frame_sha256"] as? String))
        let items = [item("2024/05/13~05/17", titleBox), item("57", countBox)]

        let derived = StructuralLocators.segmentAlbumCards(
            items: items,
            imageBounds: CGRect(x: 0, y: 0, width: frameSize[0], height: frameSize[1])
        )
        XCTAssertFalse(derived.isEmpty, "actual segmentation must derive the album card region")
        guard case let .candidate(segmented) = StructuralLocators.locateAlbumCard(
            items: items,
            regions: derived,
            binding: binding
        ) else {
            return XCTFail("segmentation-derived album card must locate a candidate")
        }

        let structure = try XCTUnwrap(album["structure"] as? [String: Any])
        let cardTop = try XCTUnwrap(structure["above_band_bottom_row"] as? Int)
        let cardBottom = try XCTUnwrap(structure["below_band_top_row"] as? Int)
        let supplied = AlbumCardRegion(
            id: "attempt12-verified-card",
            boundsCapturePx: CGRect(x: 0, y: Double(cardTop), width: 654, height: Double(cardBottom - cardTop))
        )
        guard case let .candidate(reviewed) = StructuralLocators.locateAlbumCard(
            items: items,
            regions: [supplied],
            binding: binding
        ) else {
            return XCTFail("reviewed supplied region must locate a candidate")
        }
        XCTAssertEqual(segmented.pointCapturePx, reviewed.pointCapturePx)
        XCTAssertTrue(supplied.boundsCapturePx.contains(CGPoint(x: segmented.pointCapturePx.x, y: segmented.pointCapturePx.y)))
    }

    func testAttempt16AlbumCardSegmentationReplay() throws {
        let ocr = try pinnedJSON("evidence/20260916-route/attempt-16/s1-window-ocr.json")
        let cropSize = try numbers(ocr["crop_size"])
        let words = try XCTUnwrap(ocr["words_full"] as? [[String: Any]])
        func wordBox(_ text: String) throws -> CGRect {
            let word = try XCTUnwrap(words.first { $0["text"] as? String == text }, "missing OCR word: \(text)")
            let values = try numbers([word["x"], word["y"], word["w"], word["h"]])
            return try rectangle(values, endpoints: false)
        }
        let items = [
            item("2024/05/13~05/17", try wordBox("2024/05/13~05/17")),
            item("57", try wordBox("57")),
        ]
        let binding = binding(windowID: 3, frameSHA256: try XCTUnwrap(ocr["crop_sha256"] as? String))

        let derived = StructuralLocators.segmentAlbumCards(
            items: items,
            imageBounds: CGRect(x: 0, y: 0, width: cropSize[0], height: cropSize[1])
        )
        XCTAssertFalse(derived.isEmpty, "actual segmentation must derive a region from the S1 observation")
        guard case let .candidate(candidate) = StructuralLocators.locateAlbumCard(
            items: items,
            regions: derived,
            binding: binding
        ) else {
            return XCTFail("segmentation-derived S1 album card must locate a candidate")
        }
        XCTAssertTrue(derived[0].boundsCapturePx.contains(CGPoint(x: candidate.pointCapturePx.x, y: candidate.pointCapturePx.y)))
    }
}
