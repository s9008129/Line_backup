import CoreGraphics
import Foundation

// MARK: - Album ellipsis structural locator (Rev28 port of reviewed v5 invariants)
//
// The control is established by fresh-frame pixel structure (three vertically
// stacked compact components), then constrained by the exact album-title
// geometry. Historical coordinates are never accepted as input.

public struct EllipsisDotComponent: Equatable, Sendable {
    public let center: CapturePixelPoint
    public let area: Int
    public let width: Int
    public let height: Int

    public init(center: CapturePixelPoint, area: Int, width: Int, height: Int) {
        self.center = center
        self.area = area
        self.width = width
        self.height = height
    }
}

public struct EllipsisDetectionParameters: Equatable, Sendable {
    public let delta: UInt8
    public let flatTolerance: UInt8
    public let flatFraction: Double
    public let maxArea: Int
    public let maxSide: Int
    public let textMargin: Double
    public let headerDepth: Double

    public init(
        delta: UInt8 = 45,
        flatTolerance: UInt8 = 25,
        flatFraction: Double = 0.6,
        maxArea: Int = 16,
        maxSide: Int = 5,
        textMargin: Double = 6,
        headerDepth: Double = 60
    ) {
        self.delta = delta
        self.flatTolerance = flatTolerance
        self.flatFraction = flatFraction
        self.maxArea = maxArea
        self.maxSide = maxSide
        self.textMargin = textMargin
        self.headerDepth = headerDepth
    }

    public static let reviewedV5 = EllipsisDetectionParameters()
}

public enum EllipsisPixelDetectorError: Error, Equatable, Sendable {
    case invalidImageDimensions
    case grayscaleContextCreationFailed
}

public enum EllipsisPixelDetector {
    /// Returns compact connected components using the reviewed v5 flat-row
    /// census. The returned coordinates use the Rev28 capture-pixel top-left
    /// convention.
    public static func detect(
        image: CGImage,
        parameters: EllipsisDetectionParameters = .reviewedV5
    ) throws -> [EllipsisDotComponent] {
        let width = image.width
        let height = image.height
        guard width > 0, height > 0 else { throw EllipsisPixelDetectorError.invalidImageDimensions }

        var bytes = Data(count: width * height)
        let colorSpace = CGColorSpaceCreateDeviceGray()
        let created: Bool = bytes.withUnsafeMutableBytes { raw in
            guard let base = raw.baseAddress,
                  let context = CGContext(
                      data: base,
                      width: width,
                      height: height,
                      bitsPerComponent: 8,
                      bytesPerRow: width,
                      space: colorSpace,
                      bitmapInfo: CGImageAlphaInfo.none.rawValue
                  ) else { return false }
            // Store rows in top-left capture coordinates.
            context.translateBy(x: 0, y: CGFloat(height))
            context.scaleBy(x: 1, y: -1)
            context.interpolationQuality = .none
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard created else { throw EllipsisPixelDetectorError.grayscaleContextCreationFailed }

        return bytes.withUnsafeBytes { raw -> [EllipsisDotComponent] in
            let pixels = raw.bindMemory(to: UInt8.self)
            var marked = [Bool](repeating: false, count: width * height)

            for y in 0..<height {
                let start = y * width
                var row = Array(pixels[start..<(start + width)])
                row.sort()
                let median = row[row.count / 2]
                var flat = 0
                for x in 0..<width {
                    let value = pixels[start + x]
                    let distance = abs(Int(value) - Int(median))
                    if distance <= Int(parameters.flatTolerance) { flat += 1 }
                }
                guard Double(flat) / Double(width) >= parameters.flatFraction else { continue }
                for x in 0..<width {
                    let value = pixels[start + x]
                    if abs(Int(value) - Int(median)) >= Int(parameters.delta) {
                        marked[start + x] = true
                    }
                }
            }

            var seen = [Bool](repeating: false, count: width * height)
            var components: [EllipsisDotComponent] = []
            let neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]

            for index in 0..<marked.count where marked[index] && !seen[index] {
                var stack = [index]
                seen[index] = true
                var xs: [Int] = []
                var ys: [Int] = []

                while let current = stack.popLast() {
                    let x = current % width
                    let y = current / width
                    xs.append(x)
                    ys.append(y)
                    for (dx, dy) in neighbors {
                        let nx = x + dx
                        let ny = y + dy
                        guard nx >= 0, nx < width, ny >= 0, ny < height else { continue }
                        let next = ny * width + nx
                        if marked[next] && !seen[next] {
                            seen[next] = true
                            stack.append(next)
                        }
                    }
                }

                guard !xs.isEmpty, let minX = xs.min(), let maxX = xs.max(),
                      let minY = ys.min(), let maxY = ys.max() else { continue }
                let componentWidth = maxX - minX + 1
                let componentHeight = maxY - minY + 1
                guard xs.count <= parameters.maxArea,
                      componentWidth <= parameters.maxSide,
                      componentHeight <= parameters.maxSide else { continue }

                components.append(EllipsisDotComponent(
                    center: CapturePixelPoint(
                        x: Double(xs.reduce(0, +)) / Double(xs.count),
                        y: Double(ys.reduce(0, +)) / Double(ys.count)
                    ),
                    area: xs.count,
                    width: componentWidth,
                    height: componentHeight
                ))
            }

            return components.sorted {
                if $0.center.y == $1.center.y { return $0.center.x < $1.center.x }
                return $0.center.y < $1.center.y
            }
        }
    }
}

public enum AlbumEllipsisLocator {
    public static func locate(
        image: CGImage,
        ocrItems: [OcrItem],
        titleBoxCapturePx: CGRect,
        groupTitleBoxCapturePx: CGRect? = nil,
        binding: SurfaceBinding,
        parameters: EllipsisDetectionParameters = .reviewedV5
    ) throws -> StructuralLocatorResult {
        let dots = try EllipsisPixelDetector.detect(image: image, parameters: parameters)
        return locate(
            dots: dots,
            imageSize: CGSize(width: image.width, height: image.height),
            ocrItems: ocrItems,
            titleBoxCapturePx: titleBoxCapturePx,
            groupTitleBoxCapturePx: groupTitleBoxCapturePx,
            binding: binding,
            parameters: parameters
        )
    }

    public static func locate(
        dots: [EllipsisDotComponent],
        imageSize: CGSize,
        ocrItems: [OcrItem],
        titleBoxCapturePx: CGRect,
        groupTitleBoxCapturePx: CGRect? = nil,
        binding: SurfaceBinding,
        parameters: EllipsisDetectionParameters = .reviewedV5
    ) -> StructuralLocatorResult {
        guard imageSize.width > 0, imageSize.height > 0,
              !titleBoxCapturePx.isNull, titleBoxCapturePx.width > 0, titleBoxCapturePx.height > 0 else {
            return .refused(.unsafeGeometry, "invalid image or title geometry")
        }

        let titleBand = CGRect(
            x: titleBoxCapturePx.maxX + 2,
            y: max(0, titleBoxCapturePx.minY - 6),
            width: max(0, imageSize.width - 1 - (titleBoxCapturePx.maxX + 2)),
            height: max(0, min(imageSize.height - 1, titleBoxCapturePx.maxY + 10) - max(0, titleBoxCapturePx.minY - 6))
        )
        let headerBottom = max(0, titleBoxCapturePx.minY - 7)
        let headerTop = max(0, headerBottom - parameters.headerDepth)
        let header = CGRect(
            x: titleBoxCapturePx.maxX + 2,
            y: headerTop,
            width: max(0, imageSize.width - 1 - (titleBoxCapturePx.maxX + 2)),
            height: max(0, headerBottom - headerTop)
        )

        let triples = findTriples(dots)
        var eligible: [[EllipsisDotComponent]] = []

        for triple in triples {
            let middle = triple[1].center
            let point = CGPoint(x: middle.x, y: middle.y)
            if isBlockedByText(point: point, items: ocrItems, margin: parameters.textMargin) { continue }
            if let groupTitleBoxCapturePx,
               groupTitleBoxCapturePx.insetBy(dx: -6, dy: -6).contains(point) { continue }
            if titleBand.contains(point) { continue }
            if header.contains(point) { eligible.append(triple) }
        }

        guard !eligible.isEmpty else {
            return .refused(.missingIdentity, "no eligible album-level vertical ellipsis in reviewed header band")
        }
        guard eligible.count == 1 else {
            return .refused(.ambiguousIdentity, "eligible ellipsis triples=\(eligible.count)")
        }

        let triple = eligible[0]
        let middle = triple[1].center
        let minX = triple.map(\.center.x).min() ?? middle.x
        let maxX = triple.map(\.center.x).max() ?? middle.x
        let minY = triple.map(\.center.y).min() ?? middle.y
        let maxY = triple.map(\.center.y).max() ?? middle.y
        let rawSafe = CGRect(x: minX - 4, y: minY - 4, width: maxX - minX + 8, height: maxY - minY + 8)
        let imageBounds = CGRect(origin: .zero, size: imageSize)
        let safe = rawSafe.intersection(imageBounds)
        guard !safe.isNull, safe.width > 2, safe.height > 2,
              safe.contains(CGPoint(x: middle.x, y: middle.y)) else {
            return .refused(.unsafeGeometry, "ellipsis safe interior invalid")
        }

        return .candidate(StructuralCandidate(
            identity: "album-ellipsis",
            safeRectCapturePx: safe,
            pointCapturePx: middle,
            binding: binding
        ))
    }

    private static func findTriples(_ dots: [EllipsisDotComponent]) -> [[EllipsisDotComponent]] {
        guard dots.count >= 3 else { return [] }
        var result: [[EllipsisDotComponent]] = []
        for i in 0..<(dots.count - 2) {
            for j in (i + 1)..<(dots.count - 1) {
                for k in (j + 1)..<dots.count {
                    let a = dots[i], b = dots[j], c = dots[k]
                    guard a.center.y <= b.center.y, b.center.y <= c.center.y,
                          abs(a.center.x - b.center.x) <= 3,
                          abs(b.center.x - c.center.x) <= 3 else { continue }
                    let firstGap = b.center.y - a.center.y
                    let secondGap = c.center.y - b.center.y
                    guard firstGap >= 3, firstGap <= 10,
                          secondGap >= 3, secondGap <= 10,
                          c.center.y - a.center.y <= 24 else { continue }
                    result.append([a, b, c])
                }
            }
        }
        return result
    }

    private static func isBlockedByText(point: CGPoint, items: [OcrItem], margin: Double) -> Bool {
        items.contains { item in
            guard item.text.count >= 2,
                  item.text.rangeOfCharacter(from: .alphanumerics) != nil else { return false }
            return item.boundingBoxCapturePx.insetBy(dx: -margin, dy: -margin).contains(point)
        }
    }
}
