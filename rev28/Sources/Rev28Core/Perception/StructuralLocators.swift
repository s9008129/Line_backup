import CoreGraphics
import Foundation

// MARK: - Structural locators (plan R5 / W3)
//
// Vision establishes text identity. Click geometry is derived from the surface
// structure around those observations and is always bound to one capture epoch.

public struct SurfaceBinding: Equatable, Codable, Sendable {
    public let bundleID: String
    public let process: ProcessInstanceID
    public let windowID: UInt32
    public let captureEpoch: UInt64
    public let frameSHA256: String

    public init(bundleID: String, process: ProcessInstanceID, windowID: UInt32, captureEpoch: UInt64, frameSHA256: String) {
        self.bundleID = bundleID
        self.process = process
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

public struct AlbumCardRegion: Equatable, Sendable {
    public let id: String
    public let boundsCapturePx: CGRect

    public init(id: String, boundsCapturePx: CGRect) {
        self.id = id
        self.boundsCapturePx = boundsCapturePx
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


    /// Deterministically segments visible album metadata rows into mutually
    /// exclusive vertical card regions using date-range title anchors. The
    /// caller still has to prove exact title+count association with
    /// locateAlbumCard; segmentation alone never authorizes a click.
    public static func segmentAlbumCards(
        items: [OcrItem],
        imageBounds: CGRect
    ) -> [AlbumCardRegion] {
        guard imageBounds.width > 0, imageBounds.height > 0 else { return [] }
        let anchors = items.filter { isDateRangeTitle($0.text) }
            .sorted { $0.boundingBoxCapturePx.midY < $1.boundingBoxCapturePx.midY }
        guard !anchors.isEmpty else { return [] }

        var regions: [AlbumCardRegion] = []
        for (index, anchor) in anchors.enumerated() {
            let box = anchor.boundingBoxCapturePx
            let previousMid: CGFloat = {
                guard index > 0 else {
                    return max(imageBounds.minY, box.minY - max(24, box.height * 2))
                }
                return (anchors[index - 1].boundingBoxCapturePx.midY + box.midY) / 2
            }()
            let nextMid: CGFloat = {
                guard index + 1 < anchors.count else {
                    return min(imageBounds.maxY, box.maxY + max(72, box.height * 4))
                }
                return (box.midY + anchors[index + 1].boundingBoxCapturePx.midY) / 2
            }()
            let minY = max(imageBounds.minY, previousMid)
            let maxY = min(imageBounds.maxY, nextMid)
            guard maxY - minY >= max(40, box.height * 2) else { continue }
            regions.append(AlbumCardRegion(
                id: "date-card-\(index)-\(anchor.text)",
                boundsCapturePx: CGRect(
                    x: imageBounds.minX,
                    y: minY,
                    width: imageBounds.width,
                    height: maxY - minY
                )
            ))
        }
        return regions
    }

    private static func isDateRangeTitle(_ value: String) -> Bool {
        let normalized = value.replacingOccurrences(of: "～", with: "~")
        let parts = normalized.split(separator: "~", omittingEmptySubsequences: false)
        guard parts.count == 2 else { return false }
        func numeric(_ component: Substring, count: Int) -> Bool {
            component.count == count && !component.isEmpty && component.allSatisfy(\.isNumber)
        }
        func fullDate(_ part: Substring) -> (year: Substring, month: Substring, day: Substring)? {
            let components = part.split(separator: "/")
            guard components.count == 3,
                  numeric(components[0], count: 4),
                  numeric(components[1], count: 2),
                  numeric(components[2], count: 2) else { return nil }
            return (components[0], components[1], components[2])
        }
        guard let start = fullDate(parts[0]) else { return false }
        if fullDate(parts[1]) != nil { return true }
        // Canonical short end form (e.g. `2024/05/13~05/17`): the visible end
        // month/day inherits the explicitly stated start year. An end that is
        // earlier than the start, or any other shortened shape, is not an
        // explicitly supported representation and stays refused.
        let short = parts[1].split(separator: "/")
        guard short.count == 2,
              numeric(short[0], count: 2),
              numeric(short[1], count: 2) else { return false }
        return (short[0], short[1]) >= (start.month, start.day)
    }

    /// Exact album-card identity. The title and count must both be contained in
    /// one uniquely identified card region; a caller-wide search rectangle is
    /// not sufficient to establish their association.
    public static func locateAlbumCard(
        items: [OcrItem],
        title: String = "2024/05/13~05/17",
        count: String = "57",
        regions: [AlbumCardRegion],
        binding: SurfaceBinding
    ) -> StructuralLocatorResult {
        guard !regions.isEmpty,
              regions.allSatisfy({ !$0.id.isEmpty && $0.boundsCapturePx.width > 0 && $0.boundsCapturePx.height > 0 }),
              Set(regions.map(\.id)).count == regions.count else {
            return .refused(.unsafeGeometry, "card regions are empty, invalid, or have duplicate identities")
        }

        let titleItems = OcrTextIdentity.exactMatches(in: items, expected: title)
        let countItems = OcrTextIdentity.exactMatches(in: items, expected: count)
        guard titleItems.count == 1 else {
            return .refused(titleItems.count > 1 ? .ambiguousIdentity : .missingIdentity, "exact title matches=\(titleItems.count)")
        }
        guard countItems.count == 1 else {
            return .refused(countItems.count > 1 ? .ambiguousIdentity : .missingIdentity, "exact count matches=\(countItems.count)")
        }
        let titleItem = titleItems[0]
        let countItem = countItems[0]
        let matches = regions.filter {
            $0.boundsCapturePx.contains(titleItem.boundingBoxCapturePx)
                && $0.boundsCapturePx.contains(countItem.boundingBoxCapturePx)
                && countItem.boundingBoxCapturePx.midY > titleItem.boundingBoxCapturePx.midY
        }
        guard matches.count == 1, let region = matches.first else {
            if matches.count > 1 {
                return .refused(.ambiguousIdentity, "verified card-region matches=\(matches.count)")
            }
            return .refused(.referenceStructureMismatch, "title and exact count are not paired within one verified card region")
        }
        let cardBounds = region.boundsCapturePx
        let titleBox = titleItem.boundingBoxCapturePx

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
            identity: "\(region.id):\(title)|\(count)",
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
            return .failure(StructuralLocatorError(
                refusal: groupMatches.count > 1 ? .ambiguousIdentity : .missingIdentity,
                detail: "groupTitle matches=\(groupMatches.count)"
            ))
        }
        guard countMatches.count == 1 else {
            return .failure(StructuralLocatorError(
                refusal: countMatches.count > 1 ? .ambiguousIdentity : .missingIdentity,
                detail: "countText matches=\(countMatches.count)"
            ))
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
        let targetOverlap = addressable.intersection(target)
        guard !targetOverlap.isNull, targetOverlap.width >= 8 else {
            return .refused(.unsafeGeometry, "target row has no addressable horizontal overlap")
        }

        // Derive the row cell from neighboring structural bands. The OCR target
        // establishes identity; the cell boundaries establish click geometry.
        let rowTop = (above.maxY + target.minY) / 2
        let rowBottom = (target.maxY + below.minY) / 2
        let edgeInset = max(2.0, min(6.0, (rowBottom - rowTop) * 0.15))
        let safe = CGRect(
            x: targetOverlap.minX + 2,
            y: rowTop + edgeInset,
            width: targetOverlap.width - 4,
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
