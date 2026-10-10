import CoreGraphics
import Foundation
import Vision

// MARK: - Vision OCR wrapper (plan §ARCHITECTURE §3)
//
// Production path: Swift `RecognizeTextRequest`, recognitionLevel .accurate,
// recognitionLanguages zh-Hant + en-US, usesLanguageCorrection = false.
// OCR establishes identity only; click geometry comes from structural rules over
// OCR boxes + surface structure, never from a raw character box.
// `禎 U+798E` and `楨 U+6968` are never normalized or merged.

public struct OcrItem: Equatable, Codable, Sendable {
    public let text: String
    public let confidence: Double
    /// Number of top candidates (>= 2 means the recognizer hesitated; callers may refuse).
    public let candidateCount: Int
    /// Quad in capture pixels, ordered topLeft, topRight, bottomLeft, bottomRight.
    public let quadCapturePx: [CapturePixelPoint]
    public let boundingBoxCapturePx: CGRect

    public init(
        text: String,
        confidence: Double,
        candidateCount: Int,
        quadCapturePx: [CapturePixelPoint],
        boundingBoxCapturePx: CGRect
    ) {
        self.text = text
        self.confidence = confidence
        self.candidateCount = candidateCount
        self.quadCapturePx = quadCapturePx
        self.boundingBoxCapturePx = boundingBoxCapturePx
    }
}

public protocol OcrPerforming: Sendable {
    func recognize(image: CGImage) async throws -> [OcrItem]
}

private enum OcrGeometry {
    static func item(
        text: String,
        confidence: Double,
        candidateCount: Int,
        topLeftNormalized: CGPoint,
        topRightNormalized: CGPoint,
        bottomLeftNormalized: CGPoint,
        bottomRightNormalized: CGPoint,
        image: CGImage
    ) -> OcrItem {
        let width = Double(image.width)
        let height = Double(image.height)

        // Vision normalized coordinates: origin bottom-left, [0, 1].
        // Capture pixels: origin top-left.
        func pixel(_ point: CGPoint) -> CapturePixelPoint {
            CapturePixelPoint(
                x: Double(point.x) * width,
                y: (1.0 - Double(point.y)) * height
            )
        }

        let topLeft = pixel(topLeftNormalized)
        let topRight = pixel(topRightNormalized)
        let bottomLeft = pixel(bottomLeftNormalized)
        let bottomRight = pixel(bottomRightNormalized)
        let xs = [topLeft.x, topRight.x, bottomLeft.x, bottomRight.x]
        let ys = [topLeft.y, topRight.y, bottomLeft.y, bottomRight.y]
        let minX = xs.min() ?? 0
        let maxX = xs.max() ?? 0
        let minY = ys.min() ?? 0
        let maxY = ys.max() ?? 0

        return OcrItem(
            text: text,
            confidence: confidence,
            candidateCount: candidateCount,
            quadCapturePx: [topLeft, topRight, bottomLeft, bottomRight],
            boundingBoxCapturePx: CGRect(
                x: minX,
                y: minY,
                width: maxX - minX,
                height: maxY - minY
            )
        )
    }
}

public struct VisionOcrEngine: OcrPerforming {
    public static let defaultLanguages: [String] = ["zh-Hant", "en-US"]

    public init() {}

    public func recognize(image: CGImage) async throws -> [OcrItem] {
        var request = RecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = Self.defaultLanguages.map { Locale.Language(identifier: $0) }
        request.usesLanguageCorrection = false

        let observations = try await request.perform(on: image)

        return observations.compactMap { observation -> OcrItem? in
            let candidates = observation.topCandidates(2)
            guard let best = candidates.first else { return nil }
            return OcrGeometry.item(
                text: best.string,
                confidence: Double(best.confidence),
                candidateCount: candidates.count,
                topLeftNormalized: observation.topLeft.cgPoint,
                topRightNormalized: observation.topRight.cgPoint,
                bottomLeftNormalized: observation.bottomLeft.cgPoint,
                bottomRightNormalized: observation.bottomRight.cgPoint,
                image: image
            )
        }
    }
}

/// Best-effort parity backend using the long-standing `VNRecognizeTextRequest`.
///
/// This is deliberately NOT production click authority. Rev28's reviewed
/// production path remains `VisionOcrEngine` / Swift `RecognizeTextRequest`.
/// The parity engine exists to distinguish an API-specific regression from a
/// hosted/runtime Vision-service failure and is useful in CI diagnostics.
public struct LegacyVisionOcrParityEngine: OcrPerforming {
    public init() {}

    public func recognize(image: CGImage) async throws -> [OcrItem] {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = VisionOcrEngine.defaultLanguages
        request.usesLanguageCorrection = false

        let handler = VNImageRequestHandler(cgImage: image, orientation: .up, options: [:])
        try handler.perform([request])

        return (request.results ?? []).compactMap { observation -> OcrItem? in
            let candidates = observation.topCandidates(2)
            guard let best = candidates.first else { return nil }
            return OcrGeometry.item(
                text: best.string,
                confidence: Double(best.confidence),
                candidateCount: candidates.count,
                topLeftNormalized: observation.topLeft,
                topRightNormalized: observation.topRight,
                bottomLeftNormalized: observation.bottomLeft,
                bottomRightNormalized: observation.bottomRight,
                image: image
            )
        }
    }
}

/// Identity comparison rule: exact equality, never fuzzy matching or merging.
///
/// Swift String equality compares canonically equivalent Unicode sequences.
/// Production identity literals and Vision results are expected to be NFC on
/// the reviewed surfaces; critically, distinct characters such as 禎 and 楨 are
/// never conflated.
public enum OcrTextIdentity {
    public static func isExactMatch(_ candidate: String, _ expected: String) -> Bool {
        candidate == expected
    }

    /// Finds items whose text exactly equals the expected identity string.
    public static func exactMatches(in items: [OcrItem], expected: String) -> [OcrItem] {
        items.filter { isExactMatch($0.text, expected) }
    }
}

/// Native window/display geometry supplies the initial CUA-pixel to full-display-pixel
/// transform. OCR matches validate that transform; they never invent it.
public struct NativeCaptureBounds: Equatable, Sendable {
    public let cuaCaptureBoundsPoints: CGRect
    public let sckWindowBoundsPoints: CGRect
    public let displayBoundsPoints: CGRect
    public let cuaSizePixels: CGSize
    public let sckSizePixels: CGSize

    public init(cuaCaptureBoundsPoints: CGRect, sckWindowBoundsPoints: CGRect, displayBoundsPoints: CGRect,
                cuaSizePixels: CGSize, sckSizePixels: CGSize) {
        self.cuaCaptureBoundsPoints = cuaCaptureBoundsPoints
        self.sckWindowBoundsPoints = sckWindowBoundsPoints
        self.displayBoundsPoints = displayBoundsPoints
        self.cuaSizePixels = cuaSizePixels
        self.sckSizePixels = sckSizePixels
    }
}

public struct AutomaticOcrAnchor: Equatable, Sendable {
    public let text: String
    public let cuaPoint: CapturePixelPoint
    public let sckPoint: CapturePixelPoint
    public let residualSourcePixels: Double
}

public struct AutomaticAnchorMapping: Equatable, Sendable {
    public let scaleX: Double
    public let scaleY: Double
    public let offsetX: Double
    public let offsetY: Double
    public let anchors: [AutomaticOcrAnchor]
    public let maximumResidualSourcePixels: Double
    public let uncertaintyPixels: Double
}

public enum AutomaticAnchorMappingError: Error, Equatable {
    case invalidNativeBounds
    case insufficientUniqueAnchors
    case anchorsNotDispersed
    case residualTooLarge(Double)
}

public enum AutomaticOcrAnchorMapper {
    public static func derive(cua: [OcrItem], sck: [OcrItem], native: NativeCaptureBounds,
                              maximumResidualPixels: Double = 2, minimumTriangleAreaFraction: Double = 0.02)
        throws -> AutomaticAnchorMapping {
        let c = native.cuaCaptureBoundsPoints, w = native.sckWindowBoundsPoints, d = native.displayBoundsPoints
        let cw = Double(native.cuaSizePixels.width), ch = Double(native.cuaSizePixels.height)
        let sw = Double(native.sckSizePixels.width), sh = Double(native.sckSizePixels.height)
        guard [cw,ch,sw,sh,Double(c.width),Double(c.height),Double(w.width),Double(w.height),Double(d.width),Double(d.height)]
            .allSatisfy({ $0.isFinite && $0 > 0 }),
            [Double(c.minX),Double(c.minY),Double(w.minX),Double(w.minY),Double(d.minX),Double(d.minY)]
                .allSatisfy({ $0.isFinite }),
            abs(c.minX-w.minX) <= 1, abs(c.minY-w.minY) <= 1,
            abs(c.width-w.width) <= 1, abs(c.height-w.height) <= 1,
            maximumResidualPixels.isFinite, maximumResidualPixels >= 0,
            minimumTriangleAreaFraction.isFinite, minimumTriangleAreaFraction > 0 else {
            throw AutomaticAnchorMappingError.invalidNativeBounds
        }
        let displayScaleX = sw / Double(d.width), displayScaleY = sh / Double(d.height)
        let scaleX = (Double(c.width) / cw) * displayScaleX
        let scaleY = (Double(c.height) / ch) * displayScaleY
        let offsetX = (Double(c.minX-d.minX)) * displayScaleX
        let offsetY = (Double(c.minY-d.minY)) * displayScaleY
        // Anchor parity with the Python authority: the authority indexes every
        // recognized item with non-empty text, confidence in [0, 1] and at least
        // one candidate. A Swift-only stricter filter could accept a capture the
        // authority later refuses, so the sets must match exactly.
        func indexable(_ item: OcrItem) -> Bool {
            !item.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                && item.confidence >= 0 && item.confidence <= 1 && item.candidateCount >= 1
        }
        let left = Dictionary(grouping: cua.filter(indexable), by: \.text)
        let right = Dictionary(grouping: sck.filter(indexable), by: \.text)
        var anchors: [AutomaticOcrAnchor] = []
        for text in Set(left.keys).intersection(right.keys).sorted() {
            guard let lhs = left[text], lhs.count == 1, let rhs = right[text], rhs.count == 1,
                  let a = lhs.first, let b = rhs.first else { continue }
            let cuaPoint = CapturePixelPoint(x: Double(a.boundingBoxCapturePx.midX), y: Double(a.boundingBoxCapturePx.midY))
            let sckPoint = CapturePixelPoint(x: Double(b.boundingBoxCapturePx.midX), y: Double(b.boundingBoxCapturePx.midY))
            let predictedX = scaleX*cuaPoint.x + offsetX
            let predictedY = scaleY*cuaPoint.y + offsetY
            let residual = hypot(predictedX-sckPoint.x, predictedY-sckPoint.y)
            anchors.append(AutomaticOcrAnchor(text: text, cuaPoint: cuaPoint, sckPoint: sckPoint,
                residualSourcePixels: residual))
        }
        guard anchors.count >= 3 else { throw AutomaticAnchorMappingError.insufficientUniqueAnchors }
        var maxTriangleArea = 0.0
        for i in 0..<(anchors.count-2) {
            for j in (i+1)..<(anchors.count-1) {
                for k in (j+1)..<anchors.count {
                    let a = anchors[i].cuaPoint, b = anchors[j].cuaPoint, c = anchors[k].cuaPoint
                    let area = abs((b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x))/2
                    maxTriangleArea = max(maxTriangleArea, area)
                }
            }
        }
        guard maxTriangleArea/(cw*ch) >= minimumTriangleAreaFraction else {
            throw AutomaticAnchorMappingError.anchorsNotDispersed
        }
        let residual = anchors.map(\.residualSourcePixels).max() ?? .infinity
        guard residual <= maximumResidualPixels else { throw AutomaticAnchorMappingError.residualTooLarge(residual) }
        return AutomaticAnchorMapping(scaleX: scaleX, scaleY: scaleY, offsetX: offsetX, offsetY: offsetY,
            anchors: anchors, maximumResidualSourcePixels: residual, uncertaintyPixels: max(2, residual))
    }
}

// MARK: - Album-support sidecar and guard evaluation
//
// The read-only `album-support` producer retains a full-display popup frame and
// writes the sidecar the Python authority validates (`observations.py`). The
// sidecar key set, the CUA/SCK anchor transform and the guard check are fixed
// here so the CLI only performs I/O. This type never dispatches GUI.

public struct AlbumSupportArtifactRef: Equatable, Codable, Sendable {
    public let path: String
    public let bytes: Int
    public let sha256: String

    public init(path: String, bytes: Int, sha256: String) {
        self.path = path
        self.bytes = bytes
        self.sha256 = sha256
    }
}

public struct AlbumSupportOcrItem: Equatable, Codable, Sendable {
    public let text: String
    public let confidence: Double
    public let candidateCount: Int
    public let bounds: [Double]

    enum CodingKeys: String, CodingKey {
        case text, confidence
        case candidateCount = "candidate_count"
        case bounds
    }

    public init(text: String, confidence: Double, candidateCount: Int, bounds: [Double]) {
        self.text = text
        self.confidence = confidence
        self.candidateCount = candidateCount
        self.bounds = bounds
    }

    public init(item: OcrItem) {
        self.init(text: item.text, confidence: item.confidence, candidateCount: item.candidateCount,
            bounds: [Double(item.boundingBoxCapturePx.minX), Double(item.boundingBoxCapturePx.minY),
                     Double(item.boundingBoxCapturePx.width), Double(item.boundingBoxCapturePx.height)])
    }
}

public struct AlbumSupportOcrArtifact: Equatable, Codable, Sendable {
    public let version: Int
    public let cuaFrameId: String
    public let sckFrameSha256: String
    public let cua: [AlbumSupportOcrItem]
    public let sck: [AlbumSupportOcrItem]

    enum CodingKeys: String, CodingKey {
        case version
        case cuaFrameId = "cua_frame_id"
        case sckFrameSha256 = "sck_frame_sha256"
        case cua, sck
    }

    public init(version: Int = 1, cuaFrameId: String, sckFrameSha256: String,
                cua: [AlbumSupportOcrItem], sck: [AlbumSupportOcrItem]) {
        self.version = version
        self.cuaFrameId = cuaFrameId
        self.sckFrameSha256 = sckFrameSha256
        self.cua = cua
        self.sck = sck
    }
}

public struct AlbumSupportNativeBinding: Equatable, Codable, Sendable {
    public let bundleId: String
    public let pid: Int32
    public let windowId: UInt32
    public let displayId: UInt32
    public let cuaCaptureBoundsPoints: [Double]
    public let sckWindowBoundsPoints: [Double]
    public let displayBoundsPoints: [Double]
    public let cuaSizePx: [Int]
    public let sckSizePx: [Int]

    enum CodingKeys: String, CodingKey {
        case bundleId = "bundle_id"
        case pid
        case windowId = "window_id"
        case displayId = "display_id"
        case cuaCaptureBoundsPoints = "cua_capture_bounds_points"
        case sckWindowBoundsPoints = "sck_window_bounds_points"
        case displayBoundsPoints = "display_bounds_points"
        case cuaSizePx = "cua_size_px"
        case sckSizePx = "sck_size_px"
    }

    public init(bundleId: String, pid: Int32, windowId: UInt32, displayId: UInt32,
                cuaCaptureBoundsPoints: [Double], sckWindowBoundsPoints: [Double],
                displayBoundsPoints: [Double], cuaSizePx: [Int], sckSizePx: [Int]) {
        self.bundleId = bundleId
        self.pid = pid
        self.windowId = windowId
        self.displayId = displayId
        self.cuaCaptureBoundsPoints = cuaCaptureBoundsPoints
        self.sckWindowBoundsPoints = sckWindowBoundsPoints
        self.displayBoundsPoints = displayBoundsPoints
        self.cuaSizePx = cuaSizePx
        self.sckSizePx = sckSizePx
    }
}

public struct AlbumSupportSidecar: Equatable, Codable, Sendable {
    public let version: Int
    public let provider: String
    public let fixture: Bool
    public let frameId: String
    public let sessionId: String
    public let pid: Int32
    public let windowId: UInt32
    public let layoutKey: String
    public let capturedAt: String
    public let sckFrame: AlbumSupportArtifactRef
    public let ocr: AlbumSupportArtifactRef
    public let nativeBinding: AlbumSupportNativeBinding
    public let uncertaintyPx: Double
    public let safeMarginPx: Double
    public let interactiveIntersectionPx: [Double]

    enum CodingKeys: String, CodingKey {
        case version, provider, fixture
        case frameId = "frame_id"
        case sessionId = "session_id"
        case pid
        case windowId = "window_id"
        case layoutKey = "layout_key"
        case capturedAt = "captured_at"
        case sckFrame = "sck_frame"
        case ocr
        case nativeBinding = "native_binding"
        case uncertaintyPx = "uncertainty_px"
        case safeMarginPx = "safe_margin_px"
        case interactiveIntersectionPx = "interactive_intersection_px"
    }

    public init(version: Int = 1, provider: String = "SCREEN_CAPTURE_KIT", fixture: Bool = false,
                frameId: String, sessionId: String, pid: Int32, windowId: UInt32, layoutKey: String,
                capturedAt: String, sckFrame: AlbumSupportArtifactRef, ocr: AlbumSupportArtifactRef,
                nativeBinding: AlbumSupportNativeBinding, uncertaintyPx: Double, safeMarginPx: Double,
                interactiveIntersectionPx: [Double]) {
        self.version = version
        self.provider = provider
        self.fixture = fixture
        self.frameId = frameId
        self.sessionId = sessionId
        self.pid = pid
        self.windowId = windowId
        self.layoutKey = layoutKey
        self.capturedAt = capturedAt
        self.sckFrame = sckFrame
        self.ocr = ocr
        self.nativeBinding = nativeBinding
        self.uncertaintyPx = uncertaintyPx
        self.safeMarginPx = safeMarginPx
        self.interactiveIntersectionPx = interactiveIntersectionPx
    }
}

public struct AlbumSupportMapping: Equatable, Sendable {
    public let scaleX: Double
    public let scaleY: Double
    public let offsetX: Double
    public let offsetY: Double

    /// The Python authority's transform
    /// `scale = (cua_bounds_points / cua_px) * (sck_px / display_points)`.
    public init?(binding: AlbumSupportNativeBinding) {
        let c = binding.cuaCaptureBoundsPoints, w = binding.sckWindowBoundsPoints, d = binding.displayBoundsPoints
        guard c.count == 4, w.count == 4, d.count == 4, binding.cuaSizePx.count == 2, binding.sckSizePx.count == 2,
              (c + w + d).allSatisfy({ $0.isFinite }),
              c[2] > 0, c[3] > 0, d[2] > 0, d[3] > 0,
              binding.cuaSizePx.allSatisfy({ $0 > 0 }), binding.sckSizePx.allSatisfy({ $0 > 0 }),
              zip(c, w).allSatisfy({ abs($0.0 - $0.1) <= 1 }) else { return nil }
        let scaleX = (c[2] / Double(binding.cuaSizePx[0])) * (Double(binding.sckSizePx[0]) / d[2])
        let scaleY = (c[3] / Double(binding.cuaSizePx[1])) * (Double(binding.sckSizePx[1]) / d[3])
        guard scaleX.isFinite, scaleY.isFinite, scaleX > 0, scaleY > 0 else { return nil }
        self.scaleX = scaleX
        self.scaleY = scaleY
        self.offsetX = (c[0] - d[0]) * (Double(binding.sckSizePx[0]) / d[2])
        self.offsetY = (c[1] - d[1]) * (Double(binding.sckSizePx[1]) / d[3])
    }

    public func mapCuaToSck(_ point: CGPoint) -> CGPoint {
        CGPoint(x: scaleX * point.x + offsetX, y: scaleY * point.y + offsetY)
    }

    public func mapSckToCua(_ point: CGPoint) -> CGPoint {
        CGPoint(x: (point.x - offsetX) / scaleX, y: (point.y - offsetY) / scaleY)
    }
}

public enum AlbumSupportRefusal: Error, Equatable, CustomStringConvertible {
    case mapUnavailable
    case saveAllRowMissingOrAmbiguous(Int)
    case pointOutsideSaveAllRow
    case safeMarginBelowUncertainty(marginPx: Double, requiredPx: Double)
    case intersectionBelowMinimum([Double])
    case intersectionPointOutside
    case invalidBounds

    public var description: String {
        switch self {
        case .mapUnavailable: return "album-support native binding cannot produce a transform"
        case let .saveAllRowMissingOrAmbiguous(count): return "album-support Save All row not unique (count=\(count))"
        case .pointOutsideSaveAllRow: return "calibrated Save All point lies outside the fresh popup Save All row"
        case let .safeMarginBelowUncertainty(marginPx, requiredPx):
            return "album-support safe margin \(marginPx) < required \(requiredPx)"
        case let .intersectionBelowMinimum(rect): return "album-support interactive intersection \(rect) is smaller than 16x16"
        case .intersectionPointOutside: return "calibrated Save All point lies outside the actionable intersection"
        case .invalidBounds: return "album-support bounds are invalid"
        }
    }
}

public enum AlbumSupportEvaluation {
    public static let saveAllText = "儲存全部"
    public static let minimumIntersectionPx: Double = 16

    public static func uniqueRow(items: [OcrItem], text: String) -> CGRect? {
        let matches = items.filter { $0.text == text }
        guard matches.count == 1, let item = matches.first else { return nil }
        return item.boundingBoxCapturePx
    }

    public static func intersection(_ lhs: [Double], _ rhs: [Double]) -> [Double]? {
        guard lhs.count == 4, rhs.count == 4, (lhs + rhs).allSatisfy({ $0.isFinite }),
              lhs[2] > 0, lhs[3] > 0, rhs[2] > 0, rhs[3] > 0 else { return nil }
        let x = max(lhs[0], rhs[0]), y = max(lhs[1], rhs[1])
        let right = min(lhs[0] + lhs[2], rhs[0] + rhs[2]), bottom = min(lhs[1] + lhs[3], rhs[1] + rhs[3])
        guard right > x, bottom > y else { return nil }
        return [x, y, right - x, bottom - y]
    }

    /// Distance from `point` to the nearest edge of `rect`; negative when the
    /// point is outside.
    public static func margin(point: CGPoint, rect: CGRect) -> Double {
        min(point.x - rect.minX, rect.maxX - point.x, point.y - rect.minY, rect.maxY - point.y)
    }

    public struct CaptureMeasurement: Equatable, Sendable {
        public let safeMarginPx: Double
        public let interactiveIntersectionPx: [Double]
        public let saveAllRowBoundsCuaPx: [Double]
    }

    /// Capture-time measurement: locate the Save All row in the popup OCR,
    /// map it back to CUA pixels, and measure the calibrated point against it.
    public static func measureCapture(
        sckItems: [OcrItem],
        mapping: AlbumSupportMapping,
        menuBoundsCuaPx: [Double],
        addressableBoundsCuaPx: [Double],
        saveAllPointCuaPx: CGPoint,
        uncertaintyPx: Double
    ) -> Result<CaptureMeasurement, AlbumSupportRefusal> {
        guard uncertaintyPx.isFinite, uncertaintyPx >= 2 else {
            return .failure(.safeMarginBelowUncertainty(marginPx: uncertaintyPx, requiredPx: 2))
        }
        guard let intersection = intersection(menuBoundsCuaPx, addressableBoundsCuaPx) else {
            return .failure(.invalidBounds)
        }
        guard intersection[2] >= minimumIntersectionPx, intersection[3] >= minimumIntersectionPx else {
            return .failure(.intersectionBelowMinimum(intersection))
        }
        let matches = sckItems.filter { $0.text == saveAllText }
        guard matches.count == 1, let row = matches.first else {
            return .failure(.saveAllRowMissingOrAmbiguous(matches.count))
        }
        let rowBounds = row.boundingBoxCapturePx
        let mappedOrigin = mapping.mapSckToCua(CGPoint(x: rowBounds.minX, y: rowBounds.minY))
        let mappedOpposite = mapping.mapSckToCua(CGPoint(x: rowBounds.maxX, y: rowBounds.maxY))
        let cuaRow = CGRect(x: min(mappedOrigin.x, mappedOpposite.x), y: min(mappedOrigin.y, mappedOpposite.y),
            width: abs(mappedOpposite.x - mappedOrigin.x), height: abs(mappedOpposite.y - mappedOrigin.y))
        let marginPx = margin(point: saveAllPointCuaPx, rect: cuaRow)
        guard marginPx > 0 else { return .failure(.pointOutsideSaveAllRow) }
        guard marginPx >= uncertaintyPx + 4 else {
            return .failure(.safeMarginBelowUncertainty(marginPx: marginPx, requiredPx: uncertaintyPx + 4))
        }
        return .success(CaptureMeasurement(safeMarginPx: marginPx, interactiveIntersectionPx: intersection,
            saveAllRowBoundsCuaPx: [Double(cuaRow.minX), Double(cuaRow.minY), Double(cuaRow.width), Double(cuaRow.height)]))
    }

    /// Guard-time check over the freshly re-OCR'd retained popup frame: the row
    /// must be unique and the calibrated point must stay inside it by the same
    /// margin. The returned point is the input point unchanged.
    public static func guardPoint(
        sckItems: [OcrItem],
        mapping: AlbumSupportMapping,
        saveAllPointCuaPx: CGPoint,
        uncertaintyPx: Double
    ) -> Result<CGPoint, AlbumSupportRefusal> {
        guard uncertaintyPx.isFinite, uncertaintyPx >= 2 else {
            return .failure(.safeMarginBelowUncertainty(marginPx: uncertaintyPx, requiredPx: 2))
        }
        let matches = sckItems.filter { $0.text == saveAllText }
        guard matches.count == 1, let row = matches.first else {
            return .failure(.saveAllRowMissingOrAmbiguous(matches.count))
        }
        let rowBounds = row.boundingBoxCapturePx
        let mappedOrigin = mapping.mapSckToCua(CGPoint(x: rowBounds.minX, y: rowBounds.minY))
        let mappedOpposite = mapping.mapSckToCua(CGPoint(x: rowBounds.maxX, y: rowBounds.maxY))
        let cuaRow = CGRect(x: min(mappedOrigin.x, mappedOpposite.x), y: min(mappedOrigin.y, mappedOpposite.y),
            width: abs(mappedOpposite.x - mappedOrigin.x), height: abs(mappedOpposite.y - mappedOrigin.y))
        let marginPx = margin(point: saveAllPointCuaPx, rect: cuaRow)
        guard marginPx > 0 else { return .failure(.pointOutsideSaveAllRow) }
        guard marginPx >= uncertaintyPx + 4 else {
            return .failure(.safeMarginBelowUncertainty(marginPx: marginPx, requiredPx: uncertaintyPx + 4))
        }
        return .success(saveAllPointCuaPx)
    }
}

/// Geometry checks for non-menu full-display frames. This measurement binds a
/// current surface/client rectangle to the retained CUA image; it does not
/// locate a control or authorize a click.
public enum NonMenuFrameSupportRefusal: Error, Equatable {
    case invalidFrame
    case invalidSurfaceBounds
    case surfaceOutsideFrame
    case intersectionTooSmall
    case uncertaintyTooSmall
    case safeMarginTooSmall
}

public enum NonMenuFrameSupportEvaluation {
    public static let minimumIntersectionPixels = 16.0

    public struct Measurement: Equatable, Sendable {
        public let intersectionPx: [Double]
        public let referencePointPx: [Double]
        public let safeMarginPx: Double
    }

    /// The surface rectangle is evidence from the same fresh observation as
    /// the retained frame. Refuse clipping or guessed geometry; the returned
    /// center is diagnostic only and is never an actuator target.
    public static func measure(surfaceBoundsPx: [Double], frameWidthPx: Int, frameHeightPx: Int,
                               uncertaintyPx: Double) -> Result<Measurement, NonMenuFrameSupportRefusal> {
        guard frameWidthPx > 0, frameHeightPx > 0,
              frameWidthPx <= 100_000, frameHeightPx <= 100_000 else { return .failure(.invalidFrame) }
        guard surfaceBoundsPx.count == 4, surfaceBoundsPx.allSatisfy({ $0.isFinite }),
              surfaceBoundsPx[2] > 0, surfaceBoundsPx[3] > 0 else { return .failure(.invalidSurfaceBounds) }
        let x = surfaceBoundsPx[0], y = surfaceBoundsPx[1], width = surfaceBoundsPx[2], height = surfaceBoundsPx[3]
        guard x >= 0, y >= 0, x + width <= Double(frameWidthPx), y + height <= Double(frameHeightPx) else {
            return .failure(.surfaceOutsideFrame)
        }
        guard width >= minimumIntersectionPixels, height >= minimumIntersectionPixels else {
            return .failure(.intersectionTooSmall)
        }
        guard uncertaintyPx.isFinite, uncertaintyPx >= 2 else { return .failure(.uncertaintyTooSmall) }
        let margin = min(width, height) / 2
        guard margin >= uncertaintyPx + 4 else { return .failure(.safeMarginTooSmall) }
        return .success(Measurement(intersectionPx: [x, y, width, height],
            referencePointPx: [x + width / 2, y + height / 2], safeMarginPx: margin))
    }
}
