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
        let left = Dictionary(grouping: cua.filter { !$0.text.isEmpty && $0.confidence >= 0.5 && $0.candidateCount == 1 }, by: \.text)
        let right = Dictionary(grouping: sck.filter { !$0.text.isEmpty && $0.confidence >= 0.5 && $0.candidateCount == 1 }, by: \.text)
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
