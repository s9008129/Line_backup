import CoreGraphics
import Foundation

// MARK: - Structural locators (plan R5 / W3)
//
// Vision establishes text identity. Click geometry is derived from the surface
// structure around those observations and is always bound to one capture epoch.

public struct SurfaceBinding: Equatable, Codable, Sendable {
    public let windowID: UInt32
    public let captureEpoch: UInt64
    public let frameSHA256: String

    public init(windowID: UInt32, captureEpoch: UInt64, frameSHA256: String) {
        self.windowID = windowID
        self.captureEpoch = captureEpoch
        self.frameSHA256 = frameSHA256
    }
}

public struct StructuralCandidate: Equatable, Codable, Sendable {
    public let identity: String
    public let safeRectCapturePx: CGRect
    public let pointCapturePx: CapturePixelPoint
    public let binding: SurfaceBinding

    public init(identity: String, safeRectCapturePx: CGRect, pointCapturePx: CapturePixelPoint, binding: SurfaceBinding) {
        self.identity = identity
        self.safeRectCapturePx = safeRectCapturePx
        self.pointCapturePx = pointCapturePx
        self.binding = binding
    }

    public func isFresh(for current: SurfaceBinding) -> Bool {
        binding == current
    }
}

public enum StructuralLocatorRefusal: String, Codable, Sendable {
    case missingIdentity
    case ambiguousIdentity
    case referenceStructureMismatch
    case unsafeGeometry
    case staleBinding
}

public enum StructuralLocatorResult: Equatable, Sendable {
    case candidate(StructuralCandidate)
    case refused(StructuralLocatorRefusal, String)
}

public struct MenuRowObservation: Equatable, Sendable {
    public let text: String
    public let bandCapturePx: CGRect

    public init(text: String, bandCapturePx: CGRect) {
        self.text = text
        self.bandCapturePx = bandCapturePx
    }
}

public enum StructuralLocators {
    public static let lineAlbumMenuReference = [
        "選擇項目",
        "修改相簿名稱",
        "儲存全部",
        "刪除相簿",
        "分享相簿",
    ]

    /// Exact album-card identity. The count must be spatially associated with
    /// the same card (below the date title and within the supplied card bounds).
    public static func locateAlbumCard(
        items: [OcrItem],
        title: String = "2024/05/13~05/17",
        count: String = "57",
        cardBounds: CGRect,
        binding: SurfaceBinding
    ) -> StructuralLocatorResult {
        let titles = items.filter {
            OcrTextIdentity.isExactMatch($0.text, title) && cardBounds.intersects($0.boundingBoxCapturePx)
        }
        let counts = items.filter {
            OcrTextIdentity.isExactMatch($0.text, count) && cardBounds.intersects($0.boundingBoxCapturePx)
        }
        guard titles.count == 1, counts.count == 1 else {
            let cause: StructuralLocatorRefusal = (titles.count > 1 || counts.count > 1) ? .ambiguousIdentity : .missingIdentity
            return .refused(cause, "titleMatches=\(titles.count) countMatches=\(counts.count)")
        }
        let titleBox = titles[0].boundingBoxCapturePx
        let countBox = counts[0].boundingBoxCapturePx
        guard countBox.midY > titleBox.midY else {
            return .refused(.referenceStructureMismatch, "count is not below the album-date title")
        }

        // Geometry comes from the card region, not the OCR character box.
        let inset = max(4.0, min(cardBounds.width, cardBounds.height) * 0.02)
        let safe = cardBounds.insetBy(dx: inset, dy: inset)
        guard safe.width > 2, safe.height > 2 else {
            return .refused(.unsafeGeometry, "card safe interior is empty")
        }
        let point = CapturePixelPoint(x: safe.minX + min(24, safe.width / 4), y: titleBox.midY)
        guard safe.contains(CGPoint(x: point.x, y: point.y)) else {
            return .refused(.unsafeGeometry, "derived album-card point is outside safe interior")
        }
        return .candidate(StructuralCandidate(
            identity: "\(title)|\(count)",
            safeRectCapturePx: safe,
            pointCapturePx: point,
            binding: binding
        ))
    }

    /// Album detail is identity-only: exactly one group title and one count.
    /// No click candidate is produced because this check authorizes perception,
    /// not actuation.
    public static func verifyAlbumDetail(
        items: [OcrItem],
        groupTitle: String,
        countText: String = "57張照片"
    ) -> Result<Void, StructuralLocatorError> {
        let groupMatches = OcrTextIdentity.exactMatches(in: items, expected: groupTitle)
        let countMatches = OcrTextIdentity.exactMatches(in: items, expected: countText)
        guard groupMatches.count == 1 else {
            throw StructuralLocatorError(
                refusal: groupMatches.count > 1 ? .ambiguousIdentity : .missingIdentity,
                detail: "groupTitle matches=\(groupMatches.count)"
            )
        }
        guard countMatches.count == 1 else {
            throw StructuralLocatorError(
                refusal: countMatches.count > 1 ? .ambiguousIdentity : .missingIdentity,
                detail: "countText matches=\(countMatches.count)"
            )
        }
        return .success(())
    }

    /// Locates the Save All row only when the full five-row menu reference
    /// structure matches exactly and the target is unique.
    public static func locateSaveAll(
        rows: [MenuRowObservation],
        menuBounds: CGRect,
        addressableBounds: CGRect,
        binding: SurfaceBinding
    ) -> StructuralLocatorResult {
        let sorted = rows.sorted { $0.bandCapturePx.midY < $1.bandCapturePx.midY }
        let texts = sorted.map(\.text)
        guard texts == lineAlbumMenuReference else {
            if texts.filter({ $0 == "儲存全部" }).count > 1 {
                return .refused(.ambiguousIdentity, "multiple exact Save All rows")
            }
            return .refused(.referenceStructureMismatch, "observed=\(texts)")
        }
        guard sorted.count == 5, sorted[2].text == "儲存全部" else {
            return .refused(.referenceStructureMismatch, "target row is not reference index 2")
        }

        for row in sorted where !menuBounds.intersects(row.bandCapturePx) {
            return .refused(.unsafeGeometry, "row band escapes menu surface")
        }

        let target = sorted[2].bandCapturePx
        let above = sorted[1].bandCapturePx
        let below = sorted[3].bandCapturePx
        let addressable = menuBounds.intersection(addressableBounds)
        guard !addressable.isNull, addressable.width >= 8 else {
            return .refused(.unsafeGeometry, "no addressable menu overlap")
        }

        // Derive the row cell from neighboring structural bands. The OCR target
        // establishes identity; the cell boundaries establish click geometry.
        let rowTop = (above.maxY + target.minY) / 2
        let rowBottom = (target.maxY + below.minY) / 2
        let edgeInset = max(2.0, min(6.0, (rowBottom - rowTop) * 0.15))
        let safe = CGRect(
            x: addressable.minX + 2,
            y: rowTop + edgeInset,
            width: addressable.width - 4,
            height: rowBottom - rowTop - edgeInset * 2
        )
        guard safe.width > 2, safe.height > 2, menuBounds.contains(safe) else {
            return .refused(.unsafeGeometry, "Save All safe region is empty or outside menu")
        }
        let point = CapturePixelPoint(x: safe.midX, y: safe.midY)
        return .candidate(StructuralCandidate(
            identity: "儲存全部",
            safeRectCapturePx: safe,
            pointCapturePx: point,
            binding: binding
        ))
    }

    public static func revalidate(candidate: StructuralCandidate, against current: SurfaceBinding) -> StructuralLocatorResult {
        guard candidate.isFresh(for: current) else {
            return .refused(.staleBinding, "candidate capture binding differs from current frame")
        }
        return .candidate(candidate)
    }
}

public struct StructuralLocatorError: Error, Equatable, Sendable {
    public let refusal: StructuralLocatorRefusal
    public let detail: String

    public init(refusal: StructuralLocatorRefusal, detail: String) {
        self.refusal = refusal
        self.detail = detail
    }
}
