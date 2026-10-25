import CoreGraphics
import Foundation

/// Provenance for the complete card frame. A date OCR fragment cannot be
/// promoted to this type; the caller must supply a native AX card frame or a
/// complete card frame independently established from the retained image.
public enum AlbumCardGeometrySource: String, Codable, Sendable {
    case nativeAccessibility
    case completeVisualCard
}

public struct AlbumVisualAnchor: Equatable, Sendable {
    public let id: String
    public let boundsCapturePx: CGRect

    public init(id: String, boundsCapturePx: CGRect) {
        self.id = id
        self.boundsCapturePx = boundsCapturePx
    }
}

/// Inputs must be grounded in one fresh native/visual observation. `cardBounds`
/// describes all four edges of one card; it is never synthesized from OCR rows.
public struct AlbumCardVisualObservation: Equatable, Sendable {
    public let identity: String
    public let source: AlbumCardGeometrySource
    public let cardBoundsCapturePx: CGRect
    public let thumbnailBoundsCapturePx: CGRect?
    public let metadataBoundsCapturePx: CGRect
    public let controlBoundsCapturePx: [CGRect]
    public let anchors: [AlbumVisualAnchor]

    public init(
        identity: String,
        source: AlbumCardGeometrySource,
        cardBoundsCapturePx: CGRect,
        thumbnailBoundsCapturePx: CGRect?,
        metadataBoundsCapturePx: CGRect,
        controlBoundsCapturePx: [CGRect] = [],
        anchors: [AlbumVisualAnchor]
    ) {
        self.identity = identity
        self.source = source
        self.cardBoundsCapturePx = cardBoundsCapturePx
        self.thumbnailBoundsCapturePx = thumbnailBoundsCapturePx
        self.metadataBoundsCapturePx = metadataBoundsCapturePx
        self.controlBoundsCapturePx = controlBoundsCapturePx
        self.anchors = anchors
    }
}

public struct AlbumVisualWitness: Equatable, Sendable {
    public let identity: String
    public let source: AlbumCardGeometrySource
    public let dateRange: String
    public let photoCount: String
    public let cardBoundsCapturePx: CGRect
    public let thumbnailBoundsCapturePx: CGRect
    public let metadataBoundsCapturePx: CGRect
    public let controlBoundsCapturePx: [CGRect]
    public let anchors: [AlbumVisualAnchor]
    public let safeRectCapturePx: CGRect
    public let pointCapturePx: CapturePixelPoint
    public let binding: SurfaceBinding
}

public enum AlbumVisualWitnessRefusal: String, Error, Codable, Sendable {
    case missingCompleteCard
    case invalidGeometry
    case missingThumbnail
    case missingOrAmbiguousDate
    case missingOrAmbiguousCount
    case metadataNotAssociated
    case insufficientAnchors
    case noSafeClickArea
}

/// Builds a click witness from already observed card, thumbnail, metadata and
/// control geometry. The function is pure and refuses incomplete/cross-paired
/// evidence. It does not infer card bounds from date fragments.
public enum AlbumVisualWitnessBuilder {
    public static func derive(
        observation: AlbumCardVisualObservation,
        ocrItems: [OcrItem],
        expectedDateRange: String,
        expectedPhotoCount: String,
        binding: SurfaceBinding,
        edgeInsetPx: CGFloat = 6,
        obstacleClearancePx: CGFloat = 5,
        minimumAnchorTriangleArea: CGFloat = 36
    ) -> Result<AlbumVisualWitness, AlbumVisualWitnessRefusal> {
        let card = observation.cardBoundsCapturePx
        let metadata = observation.metadataBoundsCapturePx
        guard !observation.identity.isEmpty, valid(card), valid(metadata), card.contains(metadata) else {
            return .failure(.missingCompleteCard)
        }
        guard let thumbnail = observation.thumbnailBoundsCapturePx, valid(thumbnail), card.contains(thumbnail) else {
            return .failure(.missingThumbnail)
        }
        guard observation.controlBoundsCapturePx.allSatisfy({ valid($0) && card.contains($0) }) else {
            return .failure(.invalidGeometry)
        }
        guard edgeInsetPx >= 0, obstacleClearancePx >= 0, minimumAnchorTriangleArea > 0 else {
            return .failure(.invalidGeometry)
        }
        let anchorIDs = observation.anchors.map(\.id)
        guard observation.anchors.count >= 3,
              anchorIDs.allSatisfy({ !$0.isEmpty }), Set(anchorIDs).count == anchorIDs.count,
              observation.anchors.allSatisfy({ valid($0.boundsCapturePx) && card.contains($0.boundsCapturePx) }),
              largestTriangleArea(observation.anchors.map { CGPoint(x: $0.boundsCapturePx.midX, y: $0.boundsCapturePx.midY) }) >= minimumAnchorTriangleArea else {
            return .failure(.insufficientAnchors)
        }

        let dateMatches = ocrItems.filter { $0.text == expectedDateRange && $0.candidateCount == 1 && $0.confidence >= 0.8 }
        guard dateMatches.count == 1 else { return .failure(.missingOrAmbiguousDate) }
        let countMatches = ocrItems.filter { $0.text == expectedPhotoCount && $0.candidateCount == 1 && $0.confidence >= 0.8 }
        guard countMatches.count == 1 else { return .failure(.missingOrAmbiguousCount) }
        let dateBounds = dateMatches[0].boundingBoxCapturePx
        let countBounds = countMatches[0].boundingBoxCapturePx
        guard valid(dateBounds), valid(countBounds), metadata.contains(dateBounds), metadata.contains(countBounds),
              card.contains(dateBounds), card.contains(countBounds) else {
            return .failure(.metadataNotAssociated)
        }

        let insetCard = card.insetBy(dx: edgeInsetPx, dy: edgeInsetPx)
        guard valid(insetCard) else { return .failure(.noSafeClickArea) }
        let obstacles = ([thumbnail] + observation.controlBoundsCapturePx + [metadata, dateBounds, countBounds])
            .map { $0.insetBy(dx: -obstacleClearancePx, dy: -obstacleClearancePx) }
        guard let safe = largestClearRect(in: insetCard, excluding: obstacles) else {
            return .failure(.noSafeClickArea)
        }
        let point = CapturePixelPoint(x: Double(safe.midX), y: Double(safe.midY))
        return .success(AlbumVisualWitness(
            identity: observation.identity,
            source: observation.source,
            dateRange: expectedDateRange,
            photoCount: expectedPhotoCount,
            cardBoundsCapturePx: card,
            thumbnailBoundsCapturePx: thumbnail,
            metadataBoundsCapturePx: metadata,
            controlBoundsCapturePx: observation.controlBoundsCapturePx,
            anchors: observation.anchors,
            safeRectCapturePx: safe,
            pointCapturePx: point,
            binding: binding
        ))
    }

    private static func valid(_ rect: CGRect) -> Bool {
        rect.origin.x.isFinite && rect.origin.y.isFinite && rect.width.isFinite && rect.height.isFinite
            && rect.width > 0 && rect.height > 0
    }

    private static func largestTriangleArea(_ points: [CGPoint]) -> CGFloat {
        guard points.count >= 3 else { return 0 }
        var maximum: CGFloat = 0
        for first in 0..<(points.count - 2) {
            for second in (first + 1)..<(points.count - 1) {
                for third in (second + 1)..<points.count {
                    let a = points[first], b = points[second], c = points[third]
                    let area = abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) / 2
                    maximum = max(maximum, area)
                }
            }
        }
        return maximum
    }

    /// Finds the largest axis-aligned rectangle inside the card that avoids all
    /// expanded controls, thumbnail and metadata regions.
    private static func largestClearRect(in bounds: CGRect, excluding obstacles: [CGRect]) -> CGRect? {
        let clipped = obstacles.map { $0.intersection(bounds) }.filter { !$0.isNull && !$0.isEmpty }
        var xs = [bounds.minX, bounds.maxX]
        var ys = [bounds.minY, bounds.maxY]
        for obstacle in clipped {
            xs.append(contentsOf: [obstacle.minX, obstacle.maxX])
            ys.append(contentsOf: [obstacle.minY, obstacle.maxY])
        }
        xs = Array(Set(xs)).sorted()
        ys = Array(Set(ys)).sorted()
        var best: CGRect?
        var bestArea: CGFloat = 0
        guard xs.count <= 32, ys.count <= 32 else { return nil }
        for left in 0..<(xs.count - 1) {
            for right in (left + 1)..<xs.count {
                for top in 0..<(ys.count - 1) {
                    for bottom in (top + 1)..<ys.count {
                        let candidate = CGRect(x: xs[left], y: ys[top], width: xs[right] - xs[left], height: ys[bottom] - ys[top])
                        let area = candidate.width * candidate.height
                        guard area > bestArea,
                              !clipped.contains(where: { $0.intersects(candidate) }) else { continue }
                        best = candidate
                        bestArea = area
                    }
                }
            }
        }
        return best
    }
}
