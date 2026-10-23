import CryptoKit
import Foundation
import ImageIO
import Vision

private let taskRoot = URL(fileURLWithPath: "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-e2e-fullscreen-repair-20261010", isDirectory: true).standardizedFileURL

@main
struct VisionRegions {
    static func main() async {
        do {
            let args = try Arguments(CommandLine.arguments.dropFirst())
            let result = try await recognize(args)
            try writeJSON(result, to: args.output)
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys, .prettyPrinted])
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
        } catch {
            let failure: [String: Any] = ["verdict": "FAIL", "stage": "vision_regions", "error": String(describing: error)]
            if let data = try? JSONSerialization.data(withJSONObject: failure, options: [.sortedKeys, .prettyPrinted]) {
                FileHandle.standardError.write(data)
                FileHandle.standardError.write(Data("\n".utf8))
            }
            exit(1)
        }
    }

    private static func recognize(_ args: Arguments) async throws -> [String: Any] {
        let sourceData = try Data(contentsOf: args.input, options: [.mappedIfSafe])
        guard let source = CGImageSourceCreateWithData(sourceData as CFData, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw VisionError("input is not a decodable image")
        }
        let sourceHash = digest(sourceData)
        var results: [[String: Any]] = []
        for roi in args.rois {
            let cropRect = CGRect(x: roi.x, y: roi.y, width: roi.width, height: roi.height)
            guard roi.x >= 0, roi.y >= 0, roi.width > 0, roi.height > 0,
                  cropRect.maxX <= CGFloat(image.width), cropRect.maxY <= CGFloat(image.height) else {
                throw VisionError("ROI \(roi.name) is outside the source image")
            }
            guard let crop = image.cropping(to: cropRect) else { throw VisionError("could not crop ROI \(roi.name)") }
            let enlarged = try nearestScale(crop, factor: args.scale)
            let cropName = args.output.deletingPathExtension().appendingPathComponent("\(roi.name)-1x.png")
            let derivativeName = args.output.deletingPathExtension().appendingPathComponent("\(roi.name)-\(args.scale)x.png")
            try writePNG(crop, to: cropName)
            try writePNG(enlarged, to: derivativeName)

            let started = ProcessInfo.processInfo.systemUptime
            var request = RecognizeTextRequest(.revision3)
            request.recognitionLevel = .accurate
            request.recognitionLanguages = [Locale.Language(identifier: "zh-Hant"), Locale.Language(identifier: "en-US")]
            request.automaticallyDetectsLanguage = false
            request.usesLanguageCorrection = false
            request.customWords = []
            request.minimumTextHeightFraction = 0
            let observations = try await ImageRequestHandler(enlarged, orientation: .up).perform(request)
            let elapsed = (ProcessInfo.processInfo.systemUptime - started) * 1000
            let normalizedResults: [[String: Any]] = observations.map { observation in
                let candidates = observation.topCandidates(3).map {
                    ["text": $0.string, "confidence": Double($0.confidence)] as [String: Any]
                }
                let quad = [observation.topLeft, observation.topRight, observation.bottomRight, observation.bottomLeft].map {
                    let x = roi.x + $0.x * CGFloat(crop.width) / CGFloat(args.scale)
                    let y = roi.y + (1 - $0.y) * CGFloat(crop.height) / CGFloat(args.scale)
                    return ["x": Double(x), "y": Double(y)]
                }
                let b = observation.boundingBox.cgRect
                let box = [
                    "x": Double(roi.x + b.minX * CGFloat(crop.width) / CGFloat(args.scale)),
                    "y": Double(roi.y + (1 - b.maxY) * CGFloat(crop.height) / CGFloat(args.scale)),
                    "width": Double(b.width * CGFloat(crop.width) / CGFloat(args.scale)),
                    "height": Double(b.height * CGFloat(crop.height) / CGFloat(args.scale))
                ]
                return [
                    "uuid": observation.uuid.uuidString,
                    "vision_bbox_normalized_lower_left": ["x": Double(b.minX), "y": Double(b.minY), "width": Double(b.width), "height": Double(b.height)],
                    "source_bbox_pixels_top_left": box,
                    "source_quad_pixels_top_left": quad,
                    "top_candidates": candidates
                ]
            }
            results.append([
                "name": roi.name,
                "source_roi_pixels_top_left": ["x": roi.x, "y": roi.y, "width": roi.width, "height": roi.height],
                "source_crop_dimensions": ["width": crop.width, "height": crop.height],
                "derivative_dimensions": ["width": enlarged.width, "height": enlarged.height],
                "derivative_scale": args.scale,
                "interpolation": "nearest (.none)",
                "crop_path": cropName.path,
                "crop_sha256": digest(try Data(contentsOf: cropName)),
                "derivative_path": derivativeName.path,
                "derivative_sha256": digest(try Data(contentsOf: derivativeName)),
                "elapsed_ms": elapsed,
                "observations": normalizedResults
            ])
        }
        return [
            "format_version": 1,
            "provider": "Vision.RecognizeTextRequest",
            "input_path": args.input.path,
            "input_sha256": sourceHash,
            "input_dimensions_pixels": ["width": image.width, "height": image.height],
            "profile": [
                "revision": "revision3",
                "recognition_level": "accurate",
                "recognition_languages": ["zh-Hant", "en-US"],
                "automatically_detects_language": false,
                "uses_language_correction": false,
                "custom_words": [],
                "minimum_text_height_fraction": 0,
                "top_candidates": 3,
                "processing_scale": args.scale
            ],
            "os_version": ProcessInfo.processInfo.operatingSystemVersionString,
            "swift_compiler": "recorded separately in build receipt",
            "results": results
        ]
    }

    private static func nearestScale(_ image: CGImage, factor: Int) throws -> CGImage {
        guard factor >= 1, factor <= 4 else { throw VisionError("scale must be 1...4") }
        let width = image.width * factor
        let height = image.height * factor
        guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                                      bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                                      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
            throw VisionError("could not create scale context")
        }
        context.interpolationQuality = .none
        context.setShouldAntialias(false)
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        guard let scaled = context.makeImage() else { throw VisionError("could not finalize scale derivative") }
        return scaled
    }

    private static func writePNG(_ image: CGImage, to url: URL) throws {
        try ensureContained(url, under: taskRoot)
        guard !FileManager.default.fileExists(atPath: url.path) else { throw VisionError("refusing to overwrite \(url.path)") }
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        guard let destination = CGImageDestinationCreateWithURL(url as CFURL, "public.png" as CFString, 1, nil) else {
            throw VisionError("could not create crop PNG")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw VisionError("could not finalize crop PNG") }
    }

    private static func writeJSON(_ value: [String: Any], to url: URL) throws {
        try ensureContained(url, under: taskRoot)
        guard !FileManager.default.fileExists(atPath: url.path) else { throw VisionError("refusing to overwrite result JSON") }
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted])
        try data.write(to: url, options: [.withoutOverwriting])
    }

    private static func ensureContained(_ url: URL, under base: URL) throws {
        let path = url.standardizedFileURL.path
        let basePath = base.standardizedFileURL.path
        guard path.hasPrefix(basePath + "/"), !url.pathComponents.contains("..") else { throw VisionError("output path is outside task package") }
    }

    private static func digest(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

private struct ROI {
    let name: String
    let x: CGFloat
    let y: CGFloat
    let width: CGFloat
    let height: CGFloat
}

private struct Arguments {
    let input: URL
    let output: URL
    let rois: [ROI]
    let scale: Int

    init<S: Sequence>(_ raw: S) throws where S.Element == String {
        var values = Array(raw).makeIterator()
        var input: String?
        var output: String?
        var rois: [ROI] = []
        var scale = 2
        while let key = values.next() {
            switch key {
            case "--input": input = values.next()
            case "--output": output = values.next()
            case "--scale":
                guard let raw = values.next(), let parsed = Int(raw) else { throw VisionError("--scale requires an integer") }
                scale = parsed
            case "--roi":
                guard let raw = values.next() else { throw VisionError("--roi requires name,x,y,width,height") }
                let parts = raw.split(separator: ",", omittingEmptySubsequences: false)
                guard parts.count == 5, let x = Double(parts[1]), let y = Double(parts[2]),
                      let width = Double(parts[3]), let height = Double(parts[4]) else {
                    throw VisionError("--roi requires name,x,y,width,height")
                }
                let name = String(parts[0])
                guard !name.isEmpty, name.allSatisfy({ $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-" || $0 == "_") }) else {
                    throw VisionError("ROI name must be ASCII letters, numbers, dash, underscore")
                }
                rois.append(ROI(name: name, x: x, y: y, width: width, height: height))
            default: throw VisionError("unknown argument \(key)")
            }
        }
        guard let input, let output, !rois.isEmpty else { throw VisionError("required arguments: --input PATH --output PATH --roi name,x,y,w,h (repeatable)") }
        self.input = URL(fileURLWithPath: input).standardizedFileURL
        self.output = URL(fileURLWithPath: output).standardizedFileURL
        self.rois = rois
        self.scale = scale
    }
}

private struct VisionError: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}
