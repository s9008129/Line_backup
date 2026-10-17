import Foundation
import ImageIO
import CoreGraphics

// Read-only feasibility probe. It decodes retained images, crops the supplied
// SCK detail ROI, and measures visual patch displacement. It writes only JSON
// measurements; it never writes or displays image data and has no GUI APIs.
struct GrayImage {
    let width: Int
    let height: Int
    let pixels: [UInt8]
    subscript(_ x: Int, _ y: Int) -> UInt8 { pixels[y * width + x] }
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(2)
}

func loadImage(_ path: String) -> CGImage {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fail("IMAGE_DECODE_REFUSED") }
    return image
}

func gray(_ image: CGImage) -> GrayImage {
    let w = image.width, h = image.height
    var rgba = [UInt8](repeating: 0, count: w * h * 4)
    guard let context = CGContext(data: &rgba, width: w, height: h, bitsPerComponent: 8,
                                  bytesPerRow: w * 4, space: CGColorSpaceCreateDeviceRGB(),
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
        fail("BITMAP_CONTEXT_REFUSED")
    }
    context.interpolationQuality = .none
    context.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
    var values = [UInt8](repeating: 0, count: w * h)
    for i in 0..<(w * h) {
        let p = i * 4
        let red = Int(rgba[p]) * 54
        let green = Int(rgba[p + 1]) * 183
        let blue = Int(rgba[p + 2]) * 19
        let luminance = (red + green + blue) / 256
        values[i] = UInt8(luminance)
    }
    return GrayImage(width: w, height: h, pixels: values)
}

func crop(_ image: GrayImage, x: Int, y: Int, width: Int, height: Int) -> GrayImage? {
    guard x >= 0, y >= 0, width > 0, height > 0, x + width <= image.width, y + height <= image.height else { return nil }
    var out = [UInt8](repeating: 0, count: width * height)
    for row in 0..<height {
        let sourceStart = (y + row) * image.width + x
        let destStart = row * width
        out[destStart..<(destStart + width)] = image.pixels[sourceStart..<(sourceStart + width)]
    }
    return GrayImage(width: width, height: height, pixels: out)
}

func variance(_ image: GrayImage, cx: Int, cy: Int, half: Int) -> Double {
    var sum = 0.0, sum2 = 0.0, count = 0.0
    for y in (cy-half)...(cy+half) {
        for x in (cx-half)...(cx+half) {
            let v = Double(image[x, y]); sum += v; sum2 += v*v; count += 1
        }
    }
    return max(0, sum2 / count - (sum / count) * (sum / count))
}

func ncc(_ a: GrayImage, _ b: GrayImage, cx: Int, cy: Int, bx: Int, by: Int, half: Int) -> Double {
    let side = half * 2 + 1
    var sa = 0.0, sb = 0.0, saa = 0.0, sbb = 0.0, sab = 0.0
    for dy in 0..<side {
        for dx in 0..<side {
            let av = Double(a[cx + dx - half, cy + dy - half])
            let bv = Double(b[bx + dx - half, by + dy - half])
            sa += av; sb += bv; saa += av*av; sbb += bv*bv; sab += av*bv
        }
    }
    let n = Double(side * side)
    let numerator = sab - sa * sb / n
    let va = saa - sa * sa / n, vb = sbb - sb * sb / n
    guard va > 1, vb > 1 else { return -1 }
    return numerator / sqrt(va * vb)
}

func sparseNCC(_ a: GrayImage, _ b: GrayImage, cx: Int, cy: Int, bx: Int, by: Int, half: Int) -> Double {
    var sa = 0.0, sb = 0.0, saa = 0.0, sbb = 0.0, sab = 0.0, count = 0.0
    for dy in stride(from: -half, through: half, by: 2) {
        for dx in stride(from: -half, through: half, by: 2) {
            let av = Double(a[cx + dx, cy + dy]), bv = Double(b[bx + dx, by + dy])
            sa += av; sb += bv; saa += av*av; sbb += bv*bv; sab += av*bv; count += 1
        }
    }
    let numerator = sab - sa * sb / count
    let va = saa - sa * sa / count, vb = sbb - sb * sb / count
    guard va > 1, vb > 1 else { return -1 }
    return numerator / sqrt(va * vb)
}

struct Match: Codable {
    let x: Int
    let y: Int
    let variance: Double
    let dx: Int?
    let dy: Int?
    let peak: Double?
    let secondPeak: Double?
    let reason: String
}

struct Report: Codable {
    let method: String
    let inputCUA: String
    let inputSCK: String
    let cuaSize: [Int]
    let sckSize: [Int]
    let roi: [Int]
    let targetPoint: [Double]
    let patchSide: Int
    let searchRadius: Int
    let candidateStride: Int
    let targetInsideMatchedBounds: Bool
    let targetHullSignedMarginPx: Double?
    let targetPatch: TargetPatch
    let status: String
    let acceptedCount: Int
    let acceptedCoverage: [Int]
    let medianShift: [Double]?
    let medianDisplacementFromNativePx: Double?
    let maxLocalResidualPx: Double?
    let globalMatches: [GlobalMatch]
    let candidates: [Match]
}

struct GlobalMatch: Codable {
    let referenceX: Int
    let referenceY: Int
    let bestX: Int
    let bestY: Int
    let bestScore: Double
    let secondScore: Double
    let reason: String
}

struct TargetPatch: Codable {
    let variance: Double
    let bestDX: Int?
    let bestDY: Int?
    let peak: Double?
    let secondPeak: Double?
    let reason: String
}

func percentile50(_ values: [Int]) -> Double {
    let s = values.sorted(); return Double(s[s.count / 2])
}

func signedHullMargin(_ points: [(Double, Double)], x: Double, y: Double) -> Double? {
    let unique = Array(Set(points.map { "\($0.0),\($0.1)" })).compactMap { item -> (Double, Double)? in
        let pair = item.split(separator: ",")
        guard pair.count == 2, let px = Double(pair[0]), let py = Double(pair[1]) else { return nil }
        return (px, py)
    }.sorted { ($0.0, $0.1) < ($1.0, $1.1) }
    guard unique.count >= 3 else { return nil }
    func cross(_ o: (Double,Double), _ a: (Double,Double), _ b: (Double,Double)) -> Double {
        (a.0-o.0)*(b.1-o.1) - (a.1-o.1)*(b.0-o.0)
    }
    var lower: [(Double,Double)] = []
    for p in unique {
        while lower.count >= 2 && cross(lower[lower.count-2], lower[lower.count-1], p) <= 0 { lower.removeLast() }
        lower.append(p)
    }
    var upper: [(Double,Double)] = []
    for p in unique.reversed() {
        while upper.count >= 2 && cross(upper[upper.count-2], upper[upper.count-1], p) <= 0 { upper.removeLast() }
        upper.append(p)
    }
    let hull = Array(lower.dropLast()) + Array(upper.dropLast())
    guard hull.count >= 3 else { return nil }
    let margins = hull.indices.map { i -> Double in
        let a = hull[i], b = hull[(i + 1) % hull.count]
        let length = hypot(b.0-a.0, b.1-a.1)
        return cross(a, b, (x,y)) / length
    }
    guard !margins.isEmpty else { return nil }
    return margins.min() // hull is CCW: positive is inside, negative is outside.
}

let args = Array(CommandLine.arguments.dropFirst())
guard args.count == 9 else { fail("usage: driver CUA SCK ROI_X ROI_Y ROI_W ROI_H TARGET_X TARGET_Y MASK_MODE") }
let cuaPath = args[0], sckPath = args[1]
guard let rx = Int(args[2]), let ry = Int(args[3]), let rw = Int(args[4]), let rh = Int(args[5]),
      let tx = Double(args[6]), let ty = Double(args[7]) else { fail("ARGUMENT_REFUSED") }
let maskMode = args[8]
let cuaCG = loadImage(cuaPath), sckCG = loadImage(sckPath)
let cua = gray(cuaCG), sck = gray(sckCG)
guard let roi = crop(sck, x: rx, y: ry, width: rw, height: rh),
      cua.width == rw, cua.height == rh else { fail("DIMENSION_OR_ROI_REFUSED") }

let half = 8, radius = 8, gridStride = 16
var rows: [Match] = []
var accepted: [(x: Int, y: Int, dx: Int, dy: Int, peak: Double)] = []
for cy in Swift.stride(from: half + radius + 1, to: cua.height - half - radius - 1, by: gridStride) {
    for cx in Swift.stride(from: half + radius + 1, to: cua.width - half - radius - 1, by: gridStride) {
        // In post-menu frames the SCK popup footprint and its margin are
        // excluded; the CUA cursor/dots patch is excluded as well. Photo
        // patches may be considered only when the whole-window uniqueness
        // check below confirms they do not repeat elsewhere in the ROI.
        if maskMode == "post" && cx >= 556 && cy >= 94 && cy <= 446 {
            rows.append(Match(x: cx, y: cy, variance: variance(cua, cx: cx, cy: cy, half: half),
                              dx: nil, dy: nil, peak: nil, secondPeak: nil, reason: "SCK_POPUP_OCCLUSION_EXCLUDED"))
            continue
        }
        if maskMode == "post" && cx >= 576 && cx <= 645 && cy >= 56 && cy <= 136 {
            rows.append(Match(x: cx, y: cy, variance: variance(cua, cx: cx, cy: cy, half: half),
                              dx: nil, dy: nil, peak: nil, secondPeak: nil, reason: "CUA_CURSOR_EXCLUDED"))
            continue
        }
        let v = variance(cua, cx: cx, cy: cy, half: half)
        guard v >= 90 else {
            rows.append(Match(x: cx, y: cy, variance: v, dx: nil, dy: nil, peak: nil, secondPeak: nil, reason: "LOW_TEXTURE"))
            continue
        }
        var scores: [(Double, Int, Int)] = []
        for dy in -radius...radius {
            for dx in -radius...radius {
                scores.append((ncc(cua, roi, cx: cx, cy: cy, bx: cx + dx, by: cy + dy, half: half), dx, dy))
            }
        }
        scores.sort { $0.0 > $1.0 }
        guard let best = scores.first else { continue }
        let second = scores.first(where: { abs($0.1 - best.1) > 1 || abs($0.2 - best.2) > 1 })?.0 ?? -1
        let reason: String
        if best.0 < 0.92 { reason = "LOW_CORRELATION" }
        else if best.0 - second < 0.025 { reason = "AMBIGUOUS_PEAK" }
        else if hypot(Double(best.1), Double(best.2)) > 2 { reason = "DISPLACEMENT_OVER_2PX" }
        else { reason = "UNIQUE_MATCH"; accepted.append((cx, cy, best.1, best.2, best.0)) }
        rows.append(Match(x: cx, y: cy, variance: v, dx: best.1, dy: best.2,
                          peak: best.0, secondPeak: second, reason: reason))
    }
}

let xs = accepted.map(\.x), ys = accepted.map(\.y)
let inside = !accepted.isEmpty && tx >= Double(xs.min()!) && tx <= Double(xs.max()!) && ty >= Double(ys.min()!) && ty <= Double(ys.max()!)
let hullMargin = signedHullMargin(accepted.map { (Double($0.x), Double($0.y)) }, x: tx, y: ty)
let targetCX = Int(tx.rounded()), targetCY = Int(ty.rounded())
let targetVariance = variance(cua, cx: targetCX, cy: targetCY, half: half)
var targetPatch = TargetPatch(variance: targetVariance, bestDX: nil, bestDY: nil,
                              peak: nil, secondPeak: nil, reason: "LOW_TEXTURE")
if maskMode == "post" && targetCX >= 556 && targetCY >= 94 && targetCY <= 446 {
    targetPatch = TargetPatch(variance: targetVariance, bestDX: nil, bestDY: nil,
                              peak: nil, secondPeak: nil, reason: "SCK_POPUP_OCCLUSION")
} else if targetVariance >= 90 {
    var targetScores: [(Double, Int, Int)] = []
    for dy in -radius...radius {
        for dx in -radius...radius {
            targetScores.append((ncc(cua, roi, cx: targetCX, cy: targetCY,
                                     bx: targetCX + dx, by: targetCY + dy, half: half), dx, dy))
        }
    }
    targetScores.sort { $0.0 > $1.0 }
    if let best = targetScores.first {
        let second = targetScores.first(where: { abs($0.1-best.1) > 1 || abs($0.2-best.2) > 1 })?.0 ?? -1
        let reason = best.0 < 0.92 ? "LOW_TARGET_CORRELATION" :
            (best.0 - second < 0.025 ? "AMBIGUOUS_TARGET_PEAK" :
                (hypot(Double(best.1), Double(best.2)) > 2 ? "TARGET_SHIFT_OVER_2PX" : "TARGET_LOCAL_MATCH"))
        targetPatch = TargetPatch(variance: targetVariance, bestDX: best.1, bestDY: best.2,
                                  peak: best.0, secondPeak: second, reason: reason)
    }
}
var status = "REFUSE_INSUFFICIENT_UNIQUE_MATCHES"
var medianShift: [Double]? = nil
var medianDisplacement: Double? = nil
var maxResidualOutput: Double? = nil
if accepted.count >= 8 {
    let mx = percentile50(accepted.map(\.dx)), my = percentile50(accepted.map(\.dy))
    let maxResidual = accepted.map { hypot(Double($0.dx) - mx, Double($0.dy) - my) }.max() ?? .infinity
    medianShift = [mx, my]
    medianDisplacement = hypot(mx, my)
    maxResidualOutput = maxResidual
    status = hullMargin == nil || hullMargin! <= 0
        ? "REFUSE_TARGET_OUTSIDE_MATCH_HULL"
        : "MEASURED_ALIGNMENT_NO_VALIDATED_ERROR_BOUND"
}

// Select at most one strongest local match per 4x4 spatial cell, then check
// each template against the entire native-window ROI at half-pixel-grid
// sampling. This detects repeated thumbnails/text elsewhere in the ROI.
var selectedByCell: [String: (x: Int, y: Int, variance: Double)] = [:]
for m in accepted {
    let key = "\(min(3, m.x * 4 / cua.width))-\(min(3, m.y * 4 / cua.height))"
    let v = variance(cua, cx: m.x, cy: m.y, half: half)
    if selectedByCell[key] == nil || v > selectedByCell[key]!.variance {
        selectedByCell[key] = (m.x, m.y, v)
    }
}
var globalMatches: [GlobalMatch] = []
for item in selectedByCell.values.sorted(by: { ($0.y, $0.x) < ($1.y, $1.x) }) {
    var peaks: [(Double, Int, Int)] = []
    for gy in Swift.stride(from: half + 1, to: roi.height - half - 1, by: 2) {
        for gx in Swift.stride(from: half + 1, to: roi.width - half - 1, by: 2) {
            if maskMode == "post" && gx >= 556 && gy >= 94 && gy <= 446 { continue }
            peaks.append((sparseNCC(cua, roi, cx: item.x, cy: item.y, bx: gx, by: gy, half: half), gx, gy))
        }
    }
    peaks.sort { $0.0 > $1.0 }
    guard let best = peaks.first else { continue }
    let second = peaks.first(where: { abs($0.1 - best.1) > 2 || abs($0.2 - best.2) > 2 })?.0 ?? -1
    let reason: String
    if best.0 < 0.92 { reason = "GLOBAL_LOW_CORRELATION" }
    else if best.0 - second < 0.025 { reason = "GLOBAL_AMBIGUOUS_REPEAT" }
    else if abs(best.1 - item.x) > 2 || abs(best.2 - item.y) > 2 { reason = "GLOBAL_OFF_NATIVE_PREDICTION" }
    else { reason = "GLOBAL_UNIQUE_AT_NATIVE_PREDICTION" }
    globalMatches.append(GlobalMatch(referenceX: item.x, referenceY: item.y, bestX: best.1, bestY: best.2,
                                     bestScore: best.0, secondScore: second, reason: reason))
}

let report = Report(method: "gray-8bit-mean-normalized-cross-correlation/v3; local patch=17x17; candidate stride=16; local search=±8px; variance>=90; local peak>=0.92; nonadjacent peak gap>=0.025; whole-ROI uniqueness uses 9x9 samples at 2px stride; exact target patch checked separately; measured integer shift only (no error bound asserted)",
                    inputCUA: cuaPath, inputSCK: sckPath, cuaSize: [cua.width,cua.height],
                    sckSize: [sck.width,sck.height], roi: [rx,ry,rw,rh], targetPoint: [tx,ty],
                    patchSide: 17, searchRadius: radius, candidateStride: gridStride,
                    targetInsideMatchedBounds: inside,
                    targetHullSignedMarginPx: hullMargin, targetPatch: targetPatch,
                    status: status, acceptedCount: accepted.count,
                    acceptedCoverage: [xs.min() ?? -1, ys.min() ?? -1, xs.max() ?? -1, ys.max() ?? -1],
                    medianShift: medianShift, medianDisplacementFromNativePx: medianDisplacement,
                    maxLocalResidualPx: maxResidualOutput, globalMatches: globalMatches,
                    candidates: rows)
let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
FileHandle.standardOutput.write(try encoder.encode(report)); FileHandle.standardOutput.write(Data([0x0a]))
