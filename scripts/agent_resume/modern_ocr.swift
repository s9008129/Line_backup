import Foundation
import Vision
import ImageIO

@main struct OfflineOCR {
    static func main() async throws {
        let url = URL(fileURLWithPath: CommandLine.arguments[1])
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { throw NSError(domain: "image", code: 1) }
        var request = RecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["zh-Hant", "en-US"].map { Locale.Language(identifier: $0) }
        request.usesLanguageCorrection = false
        let observations = try await request.perform(on: image)
        let items: [[String: Any]] = observations.compactMap { observation in
            let candidates = observation.topCandidates(2)
            guard let best = candidates.first else { return nil }
            let points = [observation.topLeft.cgPoint, observation.topRight.cgPoint, observation.bottomLeft.cgPoint, observation.bottomRight.cgPoint]
            let xs = points.map { Double($0.x) * Double(image.width) }
            let ys = points.map { (1 - Double($0.y)) * Double(image.height) }
            let box = [xs.min()!, ys.min()!, xs.max()! - xs.min()!, ys.max()! - ys.min()!]
            return ["text": best.string, "confidence": Double(best.confidence), "boxTopLeftPixels": box,
                    "candidates": candidates.map { ["text": $0.string, "confidence": Double($0.confidence)] }]
        }
        let result: [String: Any] = ["imageWidth": image.width, "imageHeight": image.height, "source": url.path, "items": items, "screenCapture": false, "uiInputsSent": 0, "method": "Vision RecognizeTextRequest", "confidenceCalibration": "UNKNOWN"]
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]))
        FileHandle.standardOutput.write(Data("\n".utf8))
    }
}
