import CoreGraphics
import Foundation

// MARK: - Coordinate spaces
//
// Invariant 4 (plan §COORDINATE_TRANSFORM_MODEL): every conversion carries its
// scale `S` and recorded capture bbox `B`; mixed-scale usage is a type-level
// impossibility (distinct structs for each space, no implicit 2x).

/// Points in window-local space: origin at the window frame's top-left, unit = points.
public struct WindowLocalPoint: Equatable, Hashable, Codable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public init(_ p: CGPoint) {
        self.x = Double(p.x)
        self.y = Double(p.y)
    }

    public var cgPoint: CGPoint { CGPoint(x: x, y: y) }
}

/// Points in screen-global space: top-left origin, unit = points. Same space as
/// CGWindow bounds and `CGEvent` mouse locations.
public struct ScreenPoint: Equatable, Hashable, Codable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public init(_ p: CGPoint) {
        self.x = Double(p.x)
        self.y = Double(p.y)
    }

    public var cgPoint: CGPoint { CGPoint(x: x, y: y) }
}

/// Points in capture-image space: origin at the captured image's top-left, unit = pixels.
public struct CapturePixelPoint: Equatable, Hashable, Codable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public init(_ p: CGPoint) {
        self.x = Double(p.x)
        self.y = Double(p.y)
    }

    public var cgPoint: CGPoint { CGPoint(x: x, y: y) }
}

// MARK: - Conversion helpers (CGRect -> point structs)

public extension WindowLocalPoint {
    init(rectOrigin r: CGRect) { self.init(x: Double(r.minX), y: Double(r.minY)) }
}

public extension ScreenPoint {
    init(rectOrigin r: CGRect) { self.init(x: Double(r.minX), y: Double(r.minY)) }
}

/// Per-side deltas in points (top / left / bottom / right).
public struct SideDelta: Equatable, Codable, Sendable {
    public var top: Double
    public var left: Double
    public var bottom: Double
    public var right: Double

    public init(top: Double, left: Double, bottom: Double, right: Double) {
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right
    }

    public static let zero = SideDelta(top: 0, left: 0, bottom: 0, right: 0)

    public var maximum: Double { max(max(top, left), max(bottom, right)) }
}

// MARK: - Canonical transform
//
// screenPt      = windowLocalPt + W.origin
// capPx         = (screenPt − B.origin) × S
// windowLocalPt = screenPt − W.origin
// screenPt      = B.origin + capPx / S

public struct CaptureGeometry: Equatable, Sendable {
    /// `W`: the freshly read window frame in screen-global points (top-left origin).
    public let windowFrame: CGRect
    /// `B`: the actual capture bbox recorded for this frame, in screen-global points.
    public let captureBBox: CGRect
    /// `S`: the capture scale (`SCContentFilter.pointPixelScale`), cross-checked
    /// against `NSScreen.backingScaleFactor` of the display containing the window.
    public let scale: Double

    public init(windowFrame: CGRect, captureBBox: CGRect, scale: Double) {
        self.windowFrame = windowFrame
        self.captureBBox = captureBBox
        self.scale = scale
    }

    public func screenPoint(fromWindowLocal p: WindowLocalPoint) -> ScreenPoint {
        ScreenPoint(x: p.x + Double(windowFrame.minX), y: p.y + Double(windowFrame.minY))
    }

    public func windowLocalPoint(fromScreen p: ScreenPoint) -> WindowLocalPoint {
        WindowLocalPoint(x: p.x - Double(windowFrame.minX), y: p.y - Double(windowFrame.minY))
    }

    public func capturePixelPoint(fromScreen p: ScreenPoint) -> CapturePixelPoint {
        CapturePixelPoint(
            x: (p.x - Double(captureBBox.minX)) * scale,
            y: (p.y - Double(captureBBox.minY)) * scale
        )
    }

    public func screenPoint(fromCapturePixel p: CapturePixelPoint) -> ScreenPoint {
        ScreenPoint(
            x: Double(captureBBox.minX) + p.x / scale,
            y: Double(captureBBox.minY) + p.y / scale
        )
    }

    public func capturePixelPoint(fromWindowLocal p: WindowLocalPoint) -> CapturePixelPoint {
        capturePixelPoint(fromScreen: screenPoint(fromWindowLocal: p))
    }

    public func windowLocalPoint(fromCapturePixel p: CapturePixelPoint) -> WindowLocalPoint {
        windowLocalPoint(fromScreen: screenPoint(fromCapturePixel: p))
    }
}

// MARK: - Frozen per-state capture-geometry rule (RV-01)
//
// No tolerance exists without a recorded rule. A capture state with no frozen
// rule in the rule book is INVALID (fail-closed); exact equality is never
// required, and a delta beyond the frozen bound is INVALID.

/// The capture state dimensions the W2 calibration matrix freezes a rule for.
public struct CaptureGeometryState: Hashable, Codable, Sendable {
    public var settled: Bool
    public var activated: Bool
    public var includeChildWindows: Bool
    public var ignoreShadows: Bool

    public init(settled: Bool, activated: Bool, includeChildWindows: Bool, ignoreShadows: Bool) {
        self.settled = settled
        self.activated = activated
        self.includeChildWindows = includeChildWindows
        self.ignoreShadows = ignoreShadows
    }
}

/// One frozen rule. `actual size (pt) = image size (px) / S`; the residual is
/// interpreted symmetrically per side. `captureBBox.origin = expectedBBox.origin −
/// (originPaddingPt, originPaddingPt)`; padding must be within `maxOriginPaddingPt`.
public struct CaptureGeometryRule: Codable, Equatable, Sendable {
    public var maxPerSideSizeDeltaPt: Double
    public var originPaddingPt: Double
    public var maxOriginPaddingPt: Double
    public var notes: String

    public init(maxPerSideSizeDeltaPt: Double, originPaddingPt: Double, maxOriginPaddingPt: Double, notes: String = "") {
        self.maxPerSideSizeDeltaPt = maxPerSideSizeDeltaPt
        self.originPaddingPt = originPaddingPt
        self.maxOriginPaddingPt = maxOriginPaddingPt
        self.notes = notes
    }
}

public struct CaptureGeometryRuleBook: Codable, Equatable, Sendable {
    public let ruleID: String
    public let frozenAtISO8601: String
    public let rules: [String: CaptureGeometryRule]

    public init(ruleID: String, frozenAtISO8601: String, rules: [String: CaptureGeometryRule]) {
        self.ruleID = ruleID
        self.frozenAtISO8601 = frozenAtISO8601
        self.rules = rules
    }

    public func rule(for state: CaptureGeometryState) -> CaptureGeometryRule? {
        rules[CaptureGeometryRules.stateKey(state)]
    }
}

public enum CaptureGeometryViolation: Error, Equatable, Sendable, CustomStringConvertible {
    case noFrozenRule(stateKey: String)
    case invalidRule(stateKey: String, description: String)
    case emptyExpectedBBox
    case emptyImage
    case sizeDeltaExceedsTolerance(stateKey: String, perSidePt: SideDelta, allowedPerSidePt: Double)
    case originPaddingNotRepresentable(stateKey: String, paddingPt: Double, maxPaddingPt: Double)
    case scaleMismatch(pointPixelScale: Double, backingScaleFactor: Double)

    public var description: String {
        switch self {
        case let .noFrozenRule(stateKey):
            return "noFrozenRule(stateKey=\(stateKey))"
        case let .invalidRule(stateKey, description):
            return "invalidRule(stateKey=\(stateKey), \(description))"
        case .emptyExpectedBBox:
            return "emptyExpectedBBox"
        case .emptyImage:
            return "emptyImage"
        case let .sizeDeltaExceedsTolerance(stateKey, perSidePt, allowed):
            return "sizeDeltaExceedsTolerance(stateKey=\(stateKey), perSidePt=[t=\(perSidePt.top),l=\(perSidePt.left),b=\(perSidePt.bottom),r=\(perSidePt.right)], allowed=\(allowed))"
        case let .originPaddingNotRepresentable(stateKey, paddingPt, maxPaddingPt):
            return "originPaddingNotRepresentable(stateKey=\(stateKey), paddingPt=\(paddingPt), maxPaddingPt=\(maxPaddingPt))"
        case let .scaleMismatch(pointPixelScale, backingScaleFactor):
            return "scaleMismatch(pointPixelScale=\(pointPixelScale), backingScaleFactor=\(backingScaleFactor))"
        }
    }
}

public struct CaptureGeometryEvaluation: Equatable, Sendable {
    /// `B`: actual capture bbox in screen-global points, as recorded for the frame.
    public let actualBBoxPt: CGRect
    /// Symmetric per-side residual between actual size (px/S) and expected size (pt).
    public let perSideSizeDeltaPt: SideDelta
    public let originPaddingPt: Double
    public let stateKey: String
}

public enum CaptureGeometryRules {
    public static func stateKey(_ s: CaptureGeometryState) -> String {
        "settled=\(s.settled);activated=\(s.activated);includeChildWindows=\(s.includeChildWindows);ignoreShadows=\(s.ignoreShadows)"
    }

    /// Invariant 1 (validated tolerance geometry, never exact equality) +
    /// invariant 2 (origin consistency via the frozen padding rule).
    ///
    /// `expectedBBox` = the union of the freshly read `SCWindow.frame`s of the
    /// included windows. Returns the recorded actual bbox `B` for the transform.
    public static func evaluate(
        expectedBBox: CGRect,
        imageWidthPx: Int,
        imageHeightPx: Int,
        scale: Double,
        ruleBook: CaptureGeometryRuleBook?,
        state: CaptureGeometryState
    ) -> Result<CaptureGeometryEvaluation, CaptureGeometryViolation> {
        let key = stateKey(state)
        guard expectedBBox.width > 0, expectedBBox.height > 0 else {
            return .failure(.emptyExpectedBBox)
        }
        guard imageWidthPx > 0, imageHeightPx > 0, scale > 0 else {
            return .failure(.emptyImage)
        }
        guard let ruleBook, let rule = ruleBook.rule(for: state) else {
            return .failure(.noFrozenRule(stateKey: key))
        }
        guard rule.maxPerSideSizeDeltaPt >= 0, rule.maxOriginPaddingPt >= 0 else {
            return .failure(.invalidRule(stateKey: key, description: "negative tolerance/padding"))
        }
        guard rule.originPaddingPt >= 0, rule.originPaddingPt <= rule.maxOriginPaddingPt else {
            return .failure(.originPaddingNotRepresentable(
                stateKey: key,
                paddingPt: rule.originPaddingPt,
                maxPaddingPt: rule.maxOriginPaddingPt
            ))
        }

        let actualWidthPt = Double(imageWidthPx) / scale
        let actualHeightPt = Double(imageHeightPx) / scale
        let perSide = SideDelta(
            top: (actualHeightPt - Double(expectedBBox.height)) / 2.0,
            left: (actualWidthPt - Double(expectedBBox.width)) / 2.0,
            bottom: (actualHeightPt - Double(expectedBBox.height)) / 2.0,
            right: (actualWidthPt - Double(expectedBBox.width)) / 2.0
        )
        if perSide.maximum > rule.maxPerSideSizeDeltaPt {
            return .failure(.sizeDeltaExceedsTolerance(
                stateKey: key,
                perSidePt: perSide,
                allowedPerSidePt: rule.maxPerSideSizeDeltaPt
            ))
        }

        let actualBBox = CGRect(
            x: expectedBBox.minX - CGFloat(rule.originPaddingPt),
            y: expectedBBox.minY - CGFloat(rule.originPaddingPt),
            width: CGFloat(actualWidthPt),
            height: CGFloat(actualHeightPt)
        )
        return .success(CaptureGeometryEvaluation(
            actualBBoxPt: actualBBox,
            perSideSizeDeltaPt: perSide,
            originPaddingPt: rule.originPaddingPt,
            stateKey: key
        ))
    }

    /// Invariant 3: `pointPixelScale` must equal `NSScreen.backingScaleFactor` for
    /// the display containing the window; wrong-scale detection is anchored to this
    /// independent source, not to the size check alone.
    public static func validateScale(
        pointPixelScale: Double,
        backingScaleFactor: Double,
        epsilon: Double = 1e-6
    ) -> CaptureGeometryViolation? {
        if abs(pointPixelScale - backingScaleFactor) > epsilon {
            return .scaleMismatch(pointPixelScale: pointPixelScale, backingScaleFactor: backingScaleFactor)
        }
        return nil
    }

    /// Invariant 5: a point within 1 pt (default) of a safe-interior boundary is refused.
    public static func isDispatchable(
        point: WindowLocalPoint,
        safeRect: CGRect,
        minimumMarginPt: Double = 1.0
    ) -> Bool {
        guard safeRect.width > 0, safeRect.height > 0 else { return false }
        let x = point.x
        let y = point.y
        let minX = Double(safeRect.minX)
        let maxX = Double(safeRect.maxX)
        let minY = Double(safeRect.minY)
        let maxY = Double(safeRect.maxY)
        guard x > minX, x < maxX, y > minY, y < maxY else { return false }
        let margins = [x - minX, maxX - x, y - minY, maxY - y]
        return margins.min()! >= minimumMarginPt
    }
}
