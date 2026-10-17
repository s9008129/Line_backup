import Foundation
import ImageIO
import CoreGraphics
import Rev28Core

@main
struct RoiFollowupDriver {
    static func load(_ path: String) -> CGImage? {
        guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else { return nil }
        return CGImageSourceCreateImageAtIndex(source, 0, nil)
    }

    static func category(_ text: String) -> String {
        if text.range(of: #"^\d{4}/\d{2}/\d{2}\s*[~～〜]\s*\d{2}/\d{2}$"#, options: .regularExpression) != nil {
            return "album-date"
        }
        if text.range(of: #"^\d{1,3}\s*張照片$"#, options: .regularExpression) != nil { return "photo-count" }
        if text.range(of: #"^\d{4}\.\d{2}\.\d{2}$"#, options: .regularExpression) != nil { return "grid-date" }
        if text == "1く" { return "ocr-uncertain-short" }
        return "other-redacted"
    }

    static func canonical(_ text: String) -> String {
        text.replacingOccurrences(of: "～", with: "~").replacingOccurrences(of: "〜", with: "~")
    }

    static func center(_ item: OcrItem) -> (Double, Double) {
        (Double(item.boundingBoxCapturePx.midX), Double(item.boundingBoxCapturePx.midY))
    }

    static func triangleArea(_ points: [(Double, Double)]) -> Double {
        guard points.count >= 3 else { return 0 }
        var largest = 0.0
        for i in 0..<(points.count - 2) {
            for j in (i + 1)..<(points.count - 1) {
                for k in (j + 1)..<points.count {
                    let a = points[i], b = points[j], c = points[k]
                    largest = max(largest, abs((b.0-a.0)*(c.1-a.1)-(b.1-a.1)*(c.0-a.0))/2)
                }
            }
        }
        return largest
    }

    static func main() async throws {
        guard CommandLine.arguments.count == 3,
              let cuaImage = load(CommandLine.arguments[1]), let sckImage = load(CommandLine.arguments[2]) else {
            print("INPUT_REFUSED")
            exit(2)
        }
        let engine = VisionOcrEngine()
        let cua = try await engine.recognize(image: cuaImage)
        let sck = try await engine.recognize(image: sckImage)
        let native = NativeCaptureBounds(
            cuaCaptureBoundsPoints: CGRect(x: 358, y: 46, width: 327, height: 643),
            sckWindowBoundsPoints: CGRect(x: 358, y: 46, width: 327, height: 643),
            displayBoundsPoints: CGRect(x: 0, y: 0, width: 1147, height: 745),
            cuaSizePixels: CGSize(width: cuaImage.width, height: cuaImage.height),
            sckSizePixels: CGSize(width: sckImage.width, height: sckImage.height))
        let scaleX = (327.0 / Double(cuaImage.width)) * (Double(sckImage.width) / 1147.0)
        let scaleY = (643.0 / Double(cuaImage.height)) * (Double(sckImage.height) / 745.0)
        let offsetX = 358.0 * (Double(sckImage.width) / 1147.0)
        let offsetY = 46.0 * (Double(sckImage.height) / 745.0)
        let roi = CGRect(x: offsetX, y: offsetY, width: 327.0 * Double(sckImage.width) / 1147.0,
                         height: 643.0 * Double(sckImage.height) / 745.0)
        func usable(_ item: OcrItem) -> Bool {
            !item.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                && item.confidence >= 0 && item.confidence <= 1 && item.candidateCount >= 1
        }
        let global = sck.filter(usable)
        let detail = global.filter { roi.contains($0.boundingBoxCapturePx) }
        print("FRAME cua=\(cuaImage.width)x\(cuaImage.height) sck=\(sckImage.width)x\(sckImage.height) ROI=\(roi)")
        print("NATIVE_MAP scale=(\(scaleX),\(scaleY)) offset=(\(offsetX),\(offsetY))")
        print("OCR_COUNTS cua=\(cua.filter(usable).count) sck_global=\(global.count) sck_detail_roi=\(detail.count)")

        func describe(_ label: String, pool: [OcrItem], canonicalize: Bool) {
            let lhs = Dictionary(grouping: cua.filter(usable), by: { canonicalize ? canonical($0.text) : $0.text })
            let rhs = Dictionary(grouping: pool, by: { canonicalize ? canonical($0.text) : $0.text })
            var rows: [(String, Double, Double, Double, Double, Double)] = []
            for key in Set(lhs.keys).intersection(rhs.keys).sorted() {
                guard let left = lhs[key], left.count == 1, let right = rhs[key], right.count == 1,
                      let a = left.first, let b = right.first else { continue }
                let p = center(a), q = center(b)
                let predicted = (scaleX*p.0+offsetX, scaleY*p.1+offsetY)
                let residual = hypot(predicted.0-q.0, predicted.1-q.1)
                rows.append((category(a.text), p.0, p.1, q.0, q.1, residual))
            }
            let area = triangleArea(rows.map { ($0.1, $0.2) })
            print("STRATEGY \(label) uniqueAnchors=\(rows.count) maxTriangle=\(area) ratio=\(area/(Double(cuaImage.width*cuaImage.height))) maxResidual=\(rows.map(\.5).max() ?? .infinity)")
            for row in rows.sorted(by: { $0.5 < $1.5 }) {
                print("ANCHOR class=\(row.0) cua=(\(row.1),\(row.2)) sck=(\(row.3),\(row.4)) residual=\(row.5)")
            }
        }

        describe("production-global-exact", pool: global, canonicalize: false)
        describe("detail-ROI-exact", pool: detail, canonicalize: false)
        describe("detail-ROI-date-separator-normalized", pool: detail, canonicalize: true)
        do {
            let mapping = try AutomaticOcrAnchorMapper.derive(cua: cua, sck: sck, native: native)
            print("PRODUCTION_DERIVE_ACCEPT anchors=\(mapping.anchors.count) residual=\(mapping.maximumResidualSourcePixels) uncertainty=\(mapping.uncertaintyPixels)")
        } catch {
            print("PRODUCTION_DERIVE_REFUSE \(error)")
        }
    }
}
