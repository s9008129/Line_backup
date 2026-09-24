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

public struct VisionOcrEngine: OcrPerforming {
    public static let defaultLanguages: [String] = ["zh-Hant", "en-US"]

    public init() {}

    public func recognize(image: CGImage) async throws -> [OcrItem] {
        var request = RecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = Self.defaultLanguages.map { Locale.Language(identifier: $0) }
        request.usesLanguageCorrection = false

        let observations = try await request.perform(on: image)
        let width = Double(image.width)
        let height = Double(image.height)

        return observations.compactMap { observation -> OcrItem? in
            let candidates = observation.topCandidates(2)
            guard let best = candidates.first else { return nil }

            // Vision normalized coordinates: origin bottom-left, [0, 1].
            // Capture pixels: origin top-left.
            func pixel(_ point: NormalizedPoint) -> CapturePixelPoint {
                CapturePixelPoint(
                    x: Double(point.cgPoint.x) * width,
                    y: (1.0 - Double(point.cgPoint.y)) * height
                )
            }

            let topLeft = pixel(observation.topLeft)
            let topRight = pixel(observation.topRight)
            let bottomLeft = pixel(observation.bottomLeft)
            let bottomRight = pixel(observation.bottomRight)
            let xs = [topLeft.x, topRight.x, bottomLeft.x, bottomRight.x]
            let ys = [topLeft.y, topRight.y, bottomLeft.y, bottomRight.y]
            let minX = xs.min() ?? 0
            let maxX = xs.max() ?? 0
            let minY = ys.min() ?? 0
            let maxY = ys.max() ?? 0

            return OcrItem(
                text: best.string,
                confidence: Double(best.confidence),
                candidateCount: candidates.count,
                quadCapturePx: [topLeft, topRight, bottomLeft, bottomRight],
                boundingBoxCapturePx: CGRect(x: minX, y: minY, width: maxX - minX, height: maxY - minY)
            )
        }
    }
}

/// Identity comparison rule: NFC-exact equality, never normalization or merging.
public enum OcrTextIdentity {
    public static func isExactMatch(_ candidate: String, _ expected: String) -> Bool {
        candidate == expected
    }

    /// Finds items whose text exactly equals the expected identity string.
    public static func exactMatches(in items: [OcrItem], expected: String) -> [OcrItem] {
        items.filter { isExactMatch($0.text, expected) }
    }
}
