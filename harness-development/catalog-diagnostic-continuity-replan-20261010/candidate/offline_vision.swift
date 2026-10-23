// offline_vision.swift — task-local offline image helper for the LINE album catalog
// diagnostic (TASK-20261010-catalog-diagnostic-continuity-replan).
// Read-only with respect to system state: decodes saved images, builds task-local
// derivatives, runs Vision OCR on saved bytes only. It never captures the screen,
// never touches the UI, and never sends input.
//
// Subcommands:
//   offline_vision decode --input IMAGE --out NEW_DIRECTORY
//   offline_vision recognize --input IMAGE --profile PROFILES_JSON [--profile-name NAME] --roi ROI_JSON --out NEW_DIRECTORY

import Foundation
import Vision
import ImageIO
import CoreGraphics
import CryptoKit

struct ToolFailure: Error, CustomStringConvertible {
    let code: String
    let detail: String
    var description: String { "\(code): \(detail)" }
}

func fail(_ code: String, _ detail: String) throws -> Never { throw ToolFailure(code: code, detail: detail) }

func sha256Hex(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

func sha256HexFile(_ path: String) throws -> (sha: String, bytes: Int) {
    let data = try Data(contentsOf: URL(fileURLWithPath: path))
    return (sha256Hex(data), data.count)
}

func writeNewFile(_ dir: String, _ name: String, _ data: Data) throws {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(name)
    do {
        try data.write(to: url, options: [.withoutOverwriting])
    } catch {
        try fail("OUTPUT_EXISTS_OR_UNWRITABLE", "\(url.path): \(error)")
    }
}

func createNewDirectory(_ path: String) throws {
    let fm = FileManager.default
    var isDir: ObjCBool = false
    if fm.fileExists(atPath: path, isDirectory: &isDir) {
        try fail("OUTPUT_DIRECTORY_EXISTS", path)
    }
    do {
        try fm.createDirectory(atPath: path, withIntermediateDirectories: false)
    } catch {
        try fail("OUTPUT_DIRECTORY_CREATE_FAILED", "\(path): \(error)")
    }
}

func requireRegularFile(_ path: String) throws {
    let fm = FileManager.default
    let attrs: [FileAttributeKey: Any]
    do { attrs = try fm.attributesOfItem(atPath: path) }
    catch { try fail("INPUT_MISSING", path) }
    guard (attrs[.type] as? FileAttributeType) == .typeRegular else {
        try fail("INPUT_NOT_REGULAR_FILE", path)
    }
}

struct DecodedImage {
    var width: Int
    var height: Int
    var rgba: [UInt8]
    var sourceTypeId: String
    var exifOrientation: Int
    var colorspaceName: String
    var hasAlpha: Bool
    var bitsPerComponent: Int
    var bitsPerPixel: Int
    var sourceSha: String
    var sourceBytes: Int
    var sourcePath: String
}

// Canonical: RGBA8, sRGB, opaque alpha=255, top-left origin, stride = width*4.
func decodeCanonical(_ input: String) throws -> DecodedImage {
    try requireRegularFile(input)
    let url = URL(fileURLWithPath: input)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else {
        try fail("IMAGE_DECODE_FAILED", input)
    }
    let typeId = (CGImageSourceGetType(src) as String?) ?? "UNKNOWN"
    let props = (CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any]) ?? [:]
    let orientation = (props[kCGImagePropertyOrientation] as? NSNumber)?.intValue ?? 1
    guard orientation == 1 else {
        try fail("UNSUPPORTED_ORIENTATION", "EXIF orientation \(orientation) cannot be supported without guessing")
    }
    guard let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        try fail("IMAGE_DECODE_FAILED", "no image at index 0")
    }
    let w = cg.width, h = cg.height
    guard w > 0, h > 0, w <= 20000, h <= 20000 else {
        try fail("UNSUPPORTED_DIMENSIONS", "\(w)x\(h)")
    }
    guard let space = CGColorSpace(name: CGColorSpace.sRGB) else {
        try fail("SRGB_UNAVAILABLE", "no sRGB colorspace")
    }
    var rgba = [UInt8](repeating: 0, count: w * h * 4)
    let drawn: Bool = rgba.withUnsafeMutableBytes { (buf: UnsafeMutableRawBufferPointer) -> Bool in
        guard let ctx = CGContext(data: buf.baseAddress, width: w, height: h,
                                  bitsPerComponent: 8, bytesPerRow: w * 4, space: space,
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        return true
    }
    guard drawn else { try fail("CONTEXT_CREATE_FAILED", "") }
    var a = 3
    while a < rgba.count {
        guard rgba[a] == 255 else {
            try fail("NON_OPAQUE_SOURCE", "alpha!=255 at pixel \((a-3)/4); opaque capture required")
        }
        a += 4
    }
    let (sha, bytes) = try sha256HexFile(input)
    let csName = (cg.colorSpace?.name as String?) ?? "UNKNOWN"
    return DecodedImage(width: w, height: h, rgba: rgba, sourceTypeId: typeId,
                        exifOrientation: orientation, colorspaceName: csName,
                        hasAlpha: cg.alphaInfo != .none && cg.alphaInfo != .noneSkipFirst && cg.alphaInfo != .noneSkipLast,
                        bitsPerComponent: cg.bitsPerComponent, bitsPerPixel: cg.bitsPerPixel,
                        sourceSha: sha, sourceBytes: bytes, sourcePath: input)
}

func jsonData(_ obj: [String: Any]) throws -> Data {
    var data = try JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted, .sortedKeys])
    data.append(Data("\n".utf8))
    return data
}

// ---------------------------------------------------------------- decode

func runDecode(input: String, outDir: String) async throws {
    let img = try decodeCanonical(input)
    try createNewDirectory(outDir)
    try writeNewFile(outDir, "decoded.rgba", Data(img.rgba))
    let rgbaSha = sha256Hex(Data(img.rgba))
    let meta: [String: Any] = [
        "source_path": img.sourcePath,
        "source_sha256": img.sourceSha,
        "source_bytes": img.sourceBytes,
        "source_type_identifier": img.sourceTypeId,
        "exif_orientation": img.exifOrientation,
        "width": img.width,
        "height": img.height,
        "stride_bytes": img.width * 4,
        "canonical": "RGBA8 sRGB opaque alpha=255 top-left origin",
        "decoder": "ImageIO CGImageSourceCreateImageAtIndex + CGContext(premultipliedLast, sRGB)",
        "source_colorspace": img.colorspaceName,
        "source_has_alpha": img.hasAlpha,
        "source_bits_per_component": img.bitsPerComponent,
        "source_bits_per_pixel": img.bitsPerPixel,
        "decoded_rgba_sha256": rgbaSha,
        "decoded_rgba_bytes": img.rgba.count,
        "screen_capture": false,
        "ui_inputs_sent": 0,
        "method": "offline decode"
    ]
    try writeNewFile(outDir, "decode.json", try jsonData(meta))
    var summary = meta
    summary["out_dir"] = outDir
    print(String(data: try jsonData(summary), encoding: .utf8)!)
}

// ---------------------------------------------------------------- geometry

struct ROISpec { var x0: Int; var y0: Int; var x1: Int; var y1: Int }

func loadROI(_ path: String) throws -> ROISpec {
    try requireRegularFile(path)
    let data = try Data(contentsOf: URL(fileURLWithPath: path))
    guard let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        try fail("ROI_JSON_NOT_OBJECT", path)
    }
    func intField(_ k: String) throws -> Int {
        if let n = obj[k] as? NSNumber { return n.intValue }
        try fail("ROI_FIELD_MISSING", k)
    }
    return ROISpec(x0: try intField("x0"), y0: try intField("y0"), x1: try intField("x1"), y1: try intField("y1"))
}

struct OCRProfile {
    var name: String
    var api: String
    var recognitionLevel: String
    var recognitionLanguages: [String]
    var usesLanguageCorrection: Bool
    var customWords: [String]
    var automaticallyDetectsLanguage: Bool
}

func loadProfile(_ path: String, name: String?) throws -> OCRProfile {
    try requireRegularFile(path)
    let data = try Data(contentsOf: URL(fileURLWithPath: path))
    guard let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        try fail("PROFILE_JSON_NOT_OBJECT", path)
    }
    guard let profiles = obj["profiles"] as? [String: [String: Any]], !profiles.isEmpty else {
        try fail("PROFILES_MAP_MISSING", path)
    }
    let selectedName: String
    if let n = name { selectedName = n } else if profiles.count == 1 { selectedName = profiles.keys.first! }
    else { try fail("PROFILE_NAME_REQUIRED", "profiles: \(profiles.keys.sorted().joined(separator: ","))") }
    guard let p = profiles[selectedName] else {
        try fail("PROFILE_NOT_FOUND", selectedName)
    }
    return OCRProfile(
        name: selectedName,
        api: (p["api"] as? String) ?? "modern",
        recognitionLevel: (p["recognition_level"] as? String) ?? "accurate",
        recognitionLanguages: (p["recognition_languages"] as? [String]) ?? [],
        usesLanguageCorrection: (p["uses_language_correction"] as? Bool) ?? false,
        customWords: (p["custom_words"] as? [String]) ?? [],
        automaticallyDetectsLanguage: (p["automatically_detects_language"] as? Bool) ?? false)
}

func cropRGBA(_ img: DecodedImage, _ roi: ROISpec) throws -> (pixels: [UInt8], width: Int, height: Int) {
    guard roi.x0 >= 0, roi.y0 >= 0, roi.x0 < roi.x1, roi.y0 < roi.y1, roi.x1 <= img.width, roi.y1 <= img.height else {
        try fail("ROI_OUT_OF_BOUNDS", "[\(roi.x0),\(roi.y0),\(roi.x1),\(roi.y1)] image \(img.width)x\(img.height)")
    }
    let cw = roi.x1 - roi.x0, ch = roi.y1 - roi.y0
    var out = [UInt8](repeating: 0, count: cw * ch * 4)
    img.rgba.withUnsafeBufferPointer { src in
        out.withUnsafeMutableBufferPointer { dst in
            for row in 0..<ch {
                let s = ((roi.y0 + row) * img.width + roi.x0) * 4
                let d = row * cw * 4
                for i in 0..<(cw * 4) { dst[d + i] = src[s + i] }
            }
        }
    }
    return (out, cw, ch)
}

// Nearest-neighbour 2x derivative of the cropped ROI.
func scale2Nearest(_ pixels: [UInt8], _ w: Int, _ h: Int) -> [UInt8] {
    let W = w * 2, H = h * 2
    var out = [UInt8](repeating: 0, count: W * H * 4)
    pixels.withUnsafeBufferPointer { src in
        out.withUnsafeMutableBufferPointer { dst in
            for y in 0..<h {
                for x in 0..<w {
                    let s = (y * w + x) * 4
                    let r0 = (2 * y) * W * 4
                    let r1 = (2 * y + 1) * W * 4
                    for dx in 0..<2 {
                        let d0 = r0 + (2 * x + dx) * 4
                        let d1 = r1 + (2 * x + dx) * 4
                        for c in 0..<4 {
                            dst[d0 + c] = src[s + c]
                            dst[d1 + c] = src[s + c]
                        }
                    }
                }
            }
        }
    }
    return out
}

func makeCGImage(_ pixels: [UInt8], _ w: Int, _ h: Int) -> CGImage? {
    guard let space = CGColorSpace(name: CGColorSpace.sRGB) else { return nil }
    var copy = pixels
    let ctx: CGContext? = copy.withUnsafeMutableBytes { (buf: UnsafeMutableRawBufferPointer) -> CGContext? in
        CGContext(data: buf.baseAddress, width: w, height: h, bitsPerComponent: 8,
                  bytesPerRow: w * 4, space: space,
                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
    }
    return ctx?.makeImage()
}

// ---------------------------------------------------------------- recognize

struct OCRItem {
    var text: String
    var confidence: Double
    var boxDerivative: [Double]
    var boxSource: [Double]
    var candidates: [[String: Any]]
}

func runRecognize(input: String, profilesPath: String, profileName: String?, roiPath: String, outDir: String) async throws {
    let profile = try loadProfile(profilesPath, name: profileName)
    guard profile.recognitionLevel == "accurate" else {
        try fail("UNSUPPORTED_RECOGNITION_LEVEL", profile.recognitionLevel)
    }
    let roi = try loadROI(roiPath)
    let img = try decodeCanonical(input)
    let crop = try cropRGBA(img, roi)
    let der = scale2Nearest(crop.pixels, crop.width, crop.height)
    let DW = crop.width * 2, DH = crop.height * 2
    guard let derivImage = makeCGImage(der, DW, DH) else { try fail("DERIVATIVE_IMAGE_FAILED", "") }
    let derSha = sha256Hex(Data(der))

    var items: [OCRItem] = []
    var revision: Any = NSNull()
    var effectiveAutoDetect = false
    if profile.api == "modern" {
        var request = RecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = profile.recognitionLanguages.map { Locale.Language(identifier: $0) }
        request.usesLanguageCorrection = profile.usesLanguageCorrection
        request.customWords = profile.customWords
        request.automaticallyDetectsLanguage = profile.automaticallyDetectsLanguage
        effectiveAutoDetect = profile.automaticallyDetectsLanguage
        let observations: [RecognizedTextObservation]
        do { observations = try await request.perform(on: derivImage) }
        catch { try fail("VISION_MODERN_FAILED", "\(error)") }
        for observation in observations {
            let candidates = observation.topCandidates(3)
            guard let best = candidates.first else { continue }
            let pts = [observation.topLeft.cgPoint, observation.topRight.cgPoint,
                       observation.bottomLeft.cgPoint, observation.bottomRight.cgPoint]
            let xs = pts.map { Double($0.x) * Double(DW) }
            let ys = pts.map { (1 - Double($0.y)) * Double(DH) }
            let box = [xs.min()!, ys.min()!, xs.max()! - xs.min()!, ys.max()! - ys.min()!]
            items.append(OCRItem(text: best.string, confidence: Double(best.confidence),
                                 boxDerivative: box,
                                 boxSource: [Double(roi.x0) + box[0] / 2, Double(roi.y0) + box[1] / 2, box[2] / 2, box[3] / 2],
                                 candidates: candidates.map { ["text": $0.string, "confidence": Double($0.confidence)] }))
        }
        revision = String(describing: request.revision)
    } else if profile.api == "legacy" {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = profile.recognitionLanguages
        request.usesLanguageCorrection = profile.usesLanguageCorrection
        request.customWords = profile.customWords
        request.automaticallyDetectsLanguage = profile.automaticallyDetectsLanguage
        effectiveAutoDetect = profile.automaticallyDetectsLanguage
        do {
            try VNImageRequestHandler(cgImage: derivImage, options: [:]).perform([request])
        } catch { try fail("VISION_LEGACY_FAILED", "\(error)") }
        for observation in (request.results ?? []) {
            let candidates = observation.topCandidates(3)
            guard let best = candidates.first else { continue }
            let bb = observation.boundingBox
            let box = [bb.minX * Double(DW), (1 - bb.maxY) * Double(DH), bb.width * Double(DW), bb.height * Double(DH)]
            items.append(OCRItem(text: best.string, confidence: Double(best.confidence),
                                 boxDerivative: box,
                                 boxSource: [Double(roi.x0) + box[0] / 2, Double(roi.y0) + box[1] / 2, box[2] / 2, box[3] / 2],
                                 candidates: candidates.map { ["text": $0.string, "confidence": Double($0.confidence)] }))
        }
        revision = Int(request.revision)
    } else {
        try fail("UNSUPPORTED_API", profile.api)
    }

    try createNewDirectory(outDir)
    // derivative raw + png
    try writeNewFile(outDir, "derivative.rgba", Data(der))
    let pngURL = URL(fileURLWithPath: outDir).appendingPathComponent("derivative.png")
    if let dest = CGImageDestinationCreateWithURL(pngURL as CFURL, "public.png" as CFString, 1, nil) {
        CGImageDestinationAddImage(dest, derivImage, nil)
        _ = CGImageDestinationFinalize(dest)
    }
    let itemDicts: [[String: Any]] = items.map { it in
        var d: [String: Any] = ["text": it.text, "confidence": it.confidence,
                                "boxTopLeftDerivativePixels": it.boxDerivative,
                                "boxTopLeftSourcePixels": it.boxSource,
                                "candidates": it.candidates]
        // legacy historical artifacts also carry this key name; keep both spellings
        d["boxTopLeftPixels"] = it.boxDerivative
        return d
    }
    let meta: [String: Any] = [
        "api": profile.api,
        "profile_name": profile.name,
        "recognition_level": profile.recognitionLevel,
        "recognition_languages": profile.recognitionLanguages,
        "uses_language_correction": profile.usesLanguageCorrection,
        "custom_words": profile.customWords,
        "automatically_detects_language": effectiveAutoDetect,
        "requested_automatically_detects_language": profile.automaticallyDetectsLanguage,
        "api_revision": revision,
        "os_version": ProcessInfo.processInfo.operatingSystemVersionString,
        "source_path": img.sourcePath,
        "source_sha256": img.sourceSha,
        "imageWidth": img.width,
        "imageHeight": img.height,
        "roi_source_pixels": ["x0": roi.x0, "y0": roi.y0, "x1": roi.x1, "y1": roi.y1],
        "derivative_width": DW,
        "derivative_height": DH,
        "derivative_sha256": derSha,
        "scale": 2,
        "transform": "crop first (source px), then nearest-neighbour 2x; source = roi_origin + derivative/2",
        "items": itemDicts,
        "confidenceCalibration": "UNKNOWN",
        "apis_independent": false,
        "top_candidates_requested": 3,
        "screen_capture": false,
        "ui_inputs_sent": 0
    ]
    try writeNewFile(outDir, "recognize.json", try jsonData(meta))
    var summary = meta
    summary["out_dir"] = outDir
    summary["item_count"] = items.count
    print(String(data: try jsonData(summary), encoding: .utf8)!)
}

// ---------------------------------------------------------------- fixture

// Synthetic orientation fixture: four distinct corner colours so a decode bug
// that flips vertically or horizontally is visible. The file is generated by the
// offline runner (stdlib zlib PNG); this check fails closed if corners are wrong.
func runCheckFixture(input: String, expectJson: String) async throws {
    let img = try decodeCanonical(input)
    try requireRegularFile(expectJson)
    let data = try Data(contentsOf: URL(fileURLWithPath: expectJson))
    guard let expect = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        try fail("EXPECT_JSON_NOT_OBJECT", expectJson)
    }
    func corner(_ name: String) throws -> (Int, Int, Int) {
        guard let obj = expect[name] as? [String: Any],
              let x = (obj["x"] as? NSNumber)?.intValue,
              let y = (obj["y"] as? NSNumber)?.intValue,
              let want = obj["rgba"] as? [NSNumber] else { try fail("EXPECT_FIELD_MISSING", name) }
        let i = (y * img.width + x) * 4
        let got = (Int(img.rgba[i]), Int(img.rgba[i + 1]), Int(img.rgba[i + 2]))
        let expectRgba = (want[0].intValue, want[1].intValue, want[2].intValue)
        guard got == expectRgba else {
            try fail("CORNER_MISMATCH", "\(name) got \(got) want \(expectRgba)")
        }
        return got
    }
    let tl = try corner("top_left")
    let tr = try corner("top_right")
    let bl = try corner("bottom_left")
    let br = try corner("bottom_right")
    let out: [String: Any] = [
        "source_sha256": img.sourceSha,
        "source_type_identifier": img.sourceTypeId,
        "width": img.width, "height": img.height,
        "top_left": [tl.0, tl.1, tl.2],
        "top_right": [tr.0, tr.1, tr.2],
        "bottom_left": [bl.0, bl.1, bl.2],
        "bottom_right": [br.0, br.1, br.2],
        "verdict": "PASS",
        "screen_capture": false, "ui_inputs_sent": 0
    ]
    print(String(data: try jsonData(out), encoding: .utf8)!)
}

// ---------------------------------------------------------------- CLI

func argValue(_ name: String, _ args: [String]) throws -> String? {
    if let i = args.firstIndex(of: name) {
        guard i + 1 < args.count else { try fail("ARGUMENT_VALUE_MISSING", name) }
        return args[i + 1]
    }
    return nil
}

@main struct OfflineVision {
    static func main() async {
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard let sub = args.first else { try fail("SUBCOMMAND_REQUIRED", "decode|recognize") }
            switch sub {
            case "decode":
                guard let input = try argValue("--input", args), let out = try argValue("--out", args) else {
                    try fail("ARGUMENT_MISSING", "--input and --out are required")
                }
                try await runDecode(input: input, outDir: out)
            case "check-fixture":
                guard let input = try argValue("--input", args),
                      let expect = try argValue("--expect", args) else {
                    try fail("ARGUMENT_MISSING", "--input and --expect are required")
                }
                try await runCheckFixture(input: input, expectJson: expect)
            case "recognize":
                guard let input = try argValue("--input", args),
                      let profiles = try argValue("--profile", args),
                      let roi = try argValue("--roi", args),
                      let out = try argValue("--out", args) else {
                    try fail("ARGUMENT_MISSING", "--input --profile --roi --out are required")
                }
                let pname = try argValue("--profile-name", args)
                try await runRecognize(input: input, profilesPath: profiles, profileName: pname, roiPath: roi, outDir: out)
            default:
                try fail("UNKNOWN_SUBCOMMAND", sub)
            }
            exit(0)
        } catch {
            FileHandle.standardError.write(Data("ERROR \(error)\n".utf8))
            exit(1)
        }
    }
}
