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

public struct OcrItem: Equatable, Sendable {
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
