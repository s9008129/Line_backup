import CoreGraphics
import Foundation
import ImageIO
import Rev28Core

private enum ReplayFailure: Error {
    case invalidInput(String)
}

private func require<T>(_ value: T?, _ name: String) throws -> T {
    guard let value else { throw ReplayFailure.invalidInput("missing or invalid \(name)") }
    return value
}

private func rectangle(_ values: [Double], endpoints: Bool = false) throws -> CGRect {
    guard values.count == 4 else { throw ReplayFailure.invalidInput("rectangle needs four numbers") }
    return CGRect(
        x: values[0],
        y: values[1],
        width: endpoints ? values[2] - values[0] : values[2],
        height: endpoints ? values[3] - values[1] : values[3]
    )
}

private func inside(_ value: Double, _ values: [Double]) -> Bool {
    values.count == 2 && value >= values[0] && value <= values[1]
}

private func run(root: URL) throws -> [String: Any] {
    let menuPath = root.appendingPathComponent("evidence/20260921-rev27-save-all/attempt-07/s11e-v8-locate-save-all.json")
    let menuJSON = try JSONSerialization.jsonObject(with: Data(contentsOf: menuPath)) as? [String: Any]
    let menu = try require(menuJSON, "menu fixture")
    let rowValues = try require(menu["rows"] as? [[String: Any]], "menu rows")
    let rows = try rowValues.map { row -> MenuRowObservation in
        let text = try require(row["cjk_text"] as? String, "menu row text")
        let band = try rectangle(require(row["band_frame_px"] as? [Double], "menu row band"), endpoints: true)
        return MenuRowObservation(text: text, bandCapturePx: band)
    }
    let menuBounds = try rectangle(require(
        ((menu["checks"] as? [[String: Any]])?.first { $0["name"] as? String == "popup_shape" }?["detail"] as? [String: Any])?["bbox_frame_px"] as? [Double],
        "popup bounds"
    ), endpoints: true)
    let addressableBounds = try rectangle(require(menu["addressable_region_frame_px"] as? [Double], "addressable bounds"), endpoints: true)
    let binding = SurfaceBinding(
        bundleID: "replay.rev28.fixture",
        process: ProcessInstanceID(pid: 1, startTimeSeconds: 1, startTimeMicroseconds: 0),
        windowID: 1,
        captureEpoch: 1,
        frameSHA256: try require(menu["frame_sha256"] as? String, "menu frame SHA")
    )
    let menuResult = StructuralLocators.locateSaveAll(
        rows: rows,
        menuBounds: menuBounds,
        addressableBounds: addressableBounds,
        binding: binding
    )
    let menuCandidate: StructuralCandidate
    switch menuResult {
    case let .candidate(candidate): menuCandidate = candidate
    case let .refused(reason, detail):
        throw ReplayFailure.invalidInput("current save-all locator refused: \(reason.rawValue): \(detail)")
    }
    let reviewedX = try require((menu["candidate_derivation"] as? [String: Any])?["x_safe_frame_px"] as? [Double], "reviewed x-safe range")
    let reviewedY = try require((menu["candidate_derivation"] as? [String: Any])?["y_safe_frame_px"] as? [Double], "reviewed y-safe range")
    guard inside(menuCandidate.pointCapturePx.x, reviewedX),
          inside(menuCandidate.pointCapturePx.y, reviewedY) else {
        throw ReplayFailure.invalidInput("current save-all candidate disagrees with reviewed safe geometry")
    }

    let albumPath = root.appendingPathComponent("evidence/20260916-route/attempt-12/album-card-locate-v6.json")
    let albumJSON = try JSONSerialization.jsonObject(with: Data(contentsOf: albumPath)) as? [String: Any]
    let album = try require(albumJSON, "album-card fixture")
    let titleObservation = try require(album["title"] as? [String: Any], "title observation")
    let title = try rectangle(require(titleObservation["bbox"] as? [Double], "title bbox"), endpoints: true)
    let count = try rectangle(require(album["count_box"] as? [Double], "count observation"), endpoints: true)
    let cardGeometry = try require(album["structure"] as? [String: Any], "card segmentation geometry")
    let cardTop = Double(try require(cardGeometry["above_band_bottom_row"] as? Int, "card top boundary"))
    let cardBottom = Double(try require(cardGeometry["below_band_top_row"] as? Int, "card bottom boundary"))
    let cardRegion = AlbumCardRegion(id: "attempt12-verified-card", boundsCapturePx: CGRect(x: 0, y: cardTop, width: 654, height: cardBottom - cardTop))
    let albumItems = [
        OcrItem(text: "2024/05/13~05/17", confidence: 1, candidateCount: 1, quadCapturePx: [], boundingBoxCapturePx: title),
        OcrItem(text: "57", confidence: 1, candidateCount: 1, quadCapturePx: [], boundingBoxCapturePx: count),
    ]
    let albumBinding = SurfaceBinding(
        bundleID: "replay.rev28.fixture",
        process: ProcessInstanceID(pid: 1, startTimeSeconds: 1, startTimeMicroseconds: 0),
        windowID: 2,
        captureEpoch: 1,
        frameSHA256: try require(album["frame_sha256"] as? String, "album frame SHA")
    )
    let albumResult = StructuralLocators.locateAlbumCard(items: albumItems, regions: [cardRegion], binding: albumBinding)
    let albumCandidate: StructuralCandidate
    switch albumResult {
    case let .candidate(candidate): albumCandidate = candidate
    case let .refused(reason, detail):
        throw ReplayFailure.invalidInput("current album-card locator refused: \(reason.rawValue): \(detail)")
    }
    guard cardRegion.boundsCapturePx.contains(CGPoint(x: albumCandidate.pointCapturePx.x, y: albumCandidate.pointCapturePx.y)),
          album["verdict"] as? String == "ELIGIBLE",
          (album["dispatch"] as? [String: Any])?["dispatched"] as? Bool == false else {
        throw ReplayFailure.invalidInput("current album-card locator disagrees with reviewed observation/geometry")
    }

    let pixelPath = root.appendingPathComponent("evidence/20260916-route/attempt-16/frame-s1.png")
    let source = try require(CGImageSourceCreateWithURL(pixelPath as CFURL, nil), "pixel fixture image source")
    let image = try require(CGImageSourceCreateImageAtIndex(source, 0, nil), "pixel fixture image")
    let pixelComponents = try EllipsisPixelDetector.detect(image: image)

    return [
        "save_all_locator": "candidate",
        "save_all_candidate_px": [menuCandidate.pointCapturePx.x, menuCandidate.pointCapturePx.y],
        "album_card_locator": "candidate",
        "album_card_region": cardRegion.id,
        "album_card_candidate_px": [albumCandidate.pointCapturePx.x, albumCandidate.pointCapturePx.y],
        "pixel_detector_fixture": "attempt-16/frame-s1.png",
        "pixel_detector_component_count": pixelComponents.count,
    ]
}

let args = CommandLine.arguments
guard let rootIndex = args.firstIndex(of: "--root"), args.indices.contains(rootIndex + 1) else {
    fputs("usage: rev28replay --root <repository-root>\n", stderr)
    exit(2)
}
do {
    let output = try run(root: URL(fileURLWithPath: args[rootIndex + 1], isDirectory: true))
    let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys, .fragmentsAllowed])
    print(String(decoding: data, as: UTF8.self))
} catch {
    fputs("rev28replay: \(error)\n", stderr)
    exit(1)
}
