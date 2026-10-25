import AppKit
import CoreGraphics
import CryptoKit
import Foundation
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

// MARK: - Capture layer with per-frame bbox/config records (plan §ARCHITECTURE §1)
//
// Every frame carries: the full explicit configuration, the included windows and
// their freshly read SCWindow frames, the expected bbox, the actual image size and
// derived bbox in points, per-side residual, scale with its independent source,
// monotonic epoch + wall time, image SHA-256, and the bound WindowIdentity.
// Invariant failures emit an INVALID record carrying the raw numbers — never a
// silent clamp and never a retry with looser numbers.

public enum CaptureKind: String, Codable, Sendable {
    /// `SCContentFilter(desktopIndependentWindow:)` with `includeChildWindows=false`.
    case window
    /// Child-window union capture: `includeChildWindows=true`; expected bbox is the
    /// union of the included windows' freshly read SCWindow frames.
    case windowUnionWithChildWindows
    /// Diagnostic-only display filter containing an explicitly bound LINE window set.
    case explicitLineWindows
    /// Whole-display corroboration capture (never primary localization). In the
    /// window observation lane this kind is refused; the only producer is the
    /// read-only full-display popup capture used by `album-support`, which
    /// includes the menu bar so an open NSMenu is composited into the frame.
    case displayRect
}

public struct CaptureConfiguration: Equatable, Codable, Sendable {
    public var kind: CaptureKind
    public var includeChildWindows: Bool
    public var ignoreShadows: Bool
    public var ignoreClipping: Bool
    public var showsCursor: Bool
    public var sourceRect: CGRect?

    public init(
        kind: CaptureKind,
        includeChildWindows: Bool,
        ignoreShadows: Bool,
        ignoreClipping: Bool,
        showsCursor: Bool,
        sourceRect: CGRect? = nil
    ) {
        self.kind = kind
        self.includeChildWindows = includeChildWindows
        self.ignoreShadows = ignoreShadows
        self.ignoreClipping = ignoreClipping
        self.showsCursor = showsCursor
        self.sourceRect = sourceRect
    }

    /// Primary capture: independent window, no child windows, no shadows, no cursor.
    public static let primaryWindow = CaptureConfiguration(
        kind: .window,
        includeChildWindows: false,
        ignoreShadows: true,
        ignoreClipping: false,
        showsCursor: false
    )

    /// Union capture for popup/sheet observation.
    public static let childUnion = CaptureConfiguration(
        kind: .windowUnionWithChildWindows,
        includeChildWindows: true,
        ignoreShadows: true,
        ignoreClipping: false,
        showsCursor: false
    )

    public static let explicitLineWindows = CaptureConfiguration(kind: .explicitLineWindows,
        includeChildWindows: false, ignoreShadows: true, ignoreClipping: false, showsCursor: false)

    /// Full-display popup capture: whole display, menu bar included, no source rect.
    /// Only `captureFullDisplayRetained` accepts this configuration.
    public static let fullDisplayPopup = CaptureConfiguration(kind: .displayRect,
        includeChildWindows: false, ignoreShadows: false, ignoreClipping: false, showsCursor: false, sourceRect: nil)
}

public enum ScaleSource: String, Codable, Sendable {
    case pointPixelScale
    case nsScreenBackingScaleFactor
}

public enum FrameValidity: String, Codable, Sendable {
    case valid
    case invalid
}

public struct CapturedFrameRecord: Equatable, Codable, Sendable {
    public let captureKind: CaptureKind
    public let configuration: CaptureConfiguration
    public let includedWindows: [SCWindowSnapshot]
    public let expectedBBoxPt: CGRect
    public let imageWidthPx: Int
    public let imageHeightPx: Int
    public let actualBBoxPt: CGRect
    public let perSideSizeDeltaPt: SideDelta
    public let scale: Double
    public let scaleSource: ScaleSource
    public let backingScaleFactor: Double
    public let epoch: UInt64
    public let capturedAtISO8601: String
    public let imageSHA256: String
    public let stateKey: String
    public let validity: FrameValidity
    public let violations: [String]
    public let identity: WindowIdentity?
    public var explicitLineSelectionWitness: ExplicitLineSelectionWitness? = nil
    public var fullDisplayWitness: FullDisplayCaptureWitness? = nil
    public var fullDisplayCaptureTiming: FullDisplayCaptureTiming? = nil
}

/// Request bounds for one native full-display screenshot. The wall-clock and
/// monotonic intervals are recorded around the ScreenCaptureKit request itself;
/// later OCR or evidence writes never refresh this capture time.
public struct FullDisplayCaptureTiming: Equatable, Codable, Sendable {
    public let requestStartedAtISO8601: String
    public let requestFinishedAtISO8601: String
    public let requestStartMonotonicNanoseconds: UInt64
    public let requestEndMonotonicNanoseconds: UInt64

    public init(requestStartedAtISO8601: String, requestFinishedAtISO8601: String,
                requestStartMonotonicNanoseconds: UInt64, requestEndMonotonicNanoseconds: UInt64) {
        self.requestStartedAtISO8601 = requestStartedAtISO8601
        self.requestFinishedAtISO8601 = requestFinishedAtISO8601
        self.requestStartMonotonicNanoseconds = requestStartMonotonicNanoseconds
        self.requestEndMonotonicNanoseconds = requestEndMonotonicNanoseconds
    }

    public var durationMilliseconds: Double {
        guard requestEndMonotonicNanoseconds >= requestStartMonotonicNanoseconds else { return .infinity }
        return Double(requestEndMonotonicNanoseconds - requestStartMonotonicNanoseconds) / 1_000_000
    }
}

public struct FullDisplayCaptureWitness: Equatable, Codable, Sendable {
    public let displayID: UInt32
    public let displayBoundsPoints: CGRect
    public let contentRectPoints: CGRect
    public let imageWidthPx: Int
    public let imageHeightPx: Int
    public let pointPixelScale: Double
    public let backingScaleFactor: Double
    public let includeMenuBar: Bool
    public let sourceRectAbsent: Bool

    public init(displayID: UInt32, displayBoundsPoints: CGRect, contentRectPoints: CGRect,
                imageWidthPx: Int, imageHeightPx: Int, pointPixelScale: Double,
                backingScaleFactor: Double, includeMenuBar: Bool, sourceRectAbsent: Bool) {
        self.displayID = displayID
        self.displayBoundsPoints = displayBoundsPoints
        self.contentRectPoints = contentRectPoints
        self.imageWidthPx = imageWidthPx
        self.imageHeightPx = imageHeightPx
        self.pointPixelScale = pointPixelScale
        self.backingScaleFactor = backingScaleFactor
        self.includeMenuBar = includeMenuBar
        self.sourceRectAbsent = sourceRectAbsent
    }
}

public enum FullDisplayCaptureRefusal: Error, Equatable, CustomStringConvertible {
    case configurationNotFullDisplayPopup
    case sourceRectPresent
    case backingScaleUnresolved
    case menuBarExcluded
    case captureTimingInvalid
    case contentRectDoesNotContainDisplay(contentRect: CGRect, displayBounds: CGRect)
    case scaleMismatch(pointPixelScale: Double, backingScaleFactor: Double)
    case imageSizeMismatch(expectedWidthPx: Int, expectedHeightPx: Int, actualWidthPx: Int, actualHeightPx: Int)

    public var description: String {
        switch self {
        case .configurationNotFullDisplayPopup: return "full-display capture requires the frozen fullDisplayPopup configuration"
        case .sourceRectPresent: return "full-display capture never crops with a sourceRect"
        case .backingScaleUnresolved: return "full-display capture has no unique independently known backing scale"
        case .menuBarExcluded: return "full-display popup capture must include the menu bar"
        case .captureTimingInvalid: return "full-display capture request has an invalid monotonic interval"
        case let .contentRectDoesNotContainDisplay(contentRect, displayBounds):
            return "full-display contentRect \(contentRect) does not contain the display \(displayBounds)"
        case let .scaleMismatch(pointPixelScale, backingScaleFactor):
            return "full-display pointPixelScale \(pointPixelScale) != backingScaleFactor \(backingScaleFactor)"
        case let .imageSizeMismatch(expectedWidthPx, expectedHeightPx, actualWidthPx, actualHeightPx):
            return "full-display image \(actualWidthPx)x\(actualHeightPx) != display*scale \(expectedWidthPx)x\(expectedHeightPx)"
        }
    }
}

public enum FullDisplayCaptureSupport {
    public struct Evaluation: Equatable, Sendable {
        public let witness: FullDisplayCaptureWitness
        public let expectedDisplayBoundsPt: CGRect
    }

    public static func expectedImageSize(displayBoundsPt: CGRect, pointPixelScale: Double) -> (width: Int, height: Int)? {
        let width = Double(displayBoundsPt.width) * pointPixelScale
        let height = Double(displayBoundsPt.height) * pointPixelScale
        guard width.isFinite, height.isFinite, width > 0, height > 0 else { return nil }
        return (Int(width.rounded()), Int(height.rounded()))
    }

    /// Fail-closed recomputation of the full-display capture claims from the
    /// observed display, filter and image. Any mismatch refuses before a record
    /// or sidecar can be written.
    public static func evaluate(
        configuration: CaptureConfiguration,
        displayBoundsPt: CGRect,
        displayID: UInt32,
        pointPixelScale: Double,
        backingScaleFactor: Double,
        includeMenuBar: Bool,
        contentRect: CGRect,
        imageWidthPx: Int,
        imageHeightPx: Int
    ) -> Result<Evaluation, FullDisplayCaptureRefusal> {
        guard configuration == .fullDisplayPopup else { return .failure(.configurationNotFullDisplayPopup) }
        guard configuration.sourceRect == nil else { return .failure(.sourceRectPresent) }
        guard pointPixelScale.isFinite, pointPixelScale > 0,
              backingScaleFactor.isFinite, backingScaleFactor > 0 else { return .failure(.backingScaleUnresolved) }
        guard includeMenuBar else { return .failure(.menuBarExcluded) }
        guard ExplicitLineCaptureSelection.validRect(contentRect), contentRect.contains(displayBoundsPt) else {
            return .failure(.contentRectDoesNotContainDisplay(contentRect: contentRect, displayBounds: displayBoundsPt))
        }
        guard pointPixelScale == backingScaleFactor else {
            return .failure(.scaleMismatch(pointPixelScale: pointPixelScale, backingScaleFactor: backingScaleFactor))
        }
        guard let expected = expectedImageSize(displayBoundsPt: displayBoundsPt, pointPixelScale: pointPixelScale),
              expected.width == imageWidthPx, expected.height == imageHeightPx else {
            let expected = expectedImageSize(displayBoundsPt: displayBoundsPt, pointPixelScale: pointPixelScale)
            return .failure(.imageSizeMismatch(expectedWidthPx: expected?.width ?? 0, expectedHeightPx: expected?.height ?? 0,
                actualWidthPx: imageWidthPx, actualHeightPx: imageHeightPx))
        }
        let witness = FullDisplayCaptureWitness(displayID: displayID, displayBoundsPoints: displayBoundsPt,
            contentRectPoints: contentRect, imageWidthPx: imageWidthPx, imageHeightPx: imageHeightPx,
            pointPixelScale: pointPixelScale, backingScaleFactor: backingScaleFactor,
            includeMenuBar: includeMenuBar, sourceRectAbsent: configuration.sourceRect == nil)
        return .success(Evaluation(witness: witness, expectedDisplayBoundsPt: displayBoundsPt))
    }
}

public enum FrameCaptureError: Error, CustomStringConvertible {
    case noImageOutput
    case pngEncodingFailed
    case backingScaleUnresolved(windowFrame: CGRect)
    case displayRectUnsupported

    public var description: String {
        switch self {
        case .noImageOutput: return "noImageOutput"
        case .pngEncodingFailed: return "pngEncodingFailed"
        case let .backingScaleUnresolved(windowFrame): return "backingScaleUnresolved(windowFrame=\(windowFrame))"
        case .displayRectUnsupported: return "displayRectUnsupported"
        }
    }
}

public enum FrameCaptureSupport {
    public static func expectedCaptureBBox(windowBBox: CGRect, sourceRect: CGRect?) -> CGRect? {
        guard let sourceRect else { return windowBBox }
        guard sourceRect.width > 0, sourceRect.height > 0,
              CGRect(origin: .zero, size: windowBBox.size).contains(sourceRect) else { return nil }
        return CGRect(
            x: windowBBox.minX + sourceRect.minX,
            y: windowBBox.minY + sourceRect.minY,
            width: sourceRect.width,
            height: sourceRect.height
        )
    }

    /// The independent backing-scale source for the display containing the
    /// window. Fail-closed: a window center resolving to more than one display
    /// (spanning or mirrored geometry) has no independently known scale, so
    /// this returns nil instead of guessing the first display (plan C3:
    /// multiple displays stay fail-closed unless separately replanned).
    public static func backingScaleFactor(forWindowFrame frame: CGRect) -> Double? {
        let center = CGPoint(x: frame.midX, y: frame.midY)
        var displayCount: UInt32 = 0
        var displays = [CGDirectDisplayID](repeating: 0, count: 16)
        guard CGGetDisplaysWithPoint(center, UInt32(displays.count), &displays, &displayCount) == .success else {
            return nil
        }
        var screenScales: [UInt32: Double] = [:]
        for screen in NSScreen.screens {
            if let number = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber {
                screenScales[number.uint32Value] = Double(screen.backingScaleFactor)
            }
        }
        return resolvedBackingScale(displayCount: displayCount, displayIDs: displays, screenScales: screenScales)
    }

    /// Pure fail-closed resolution: exactly one display must contain the
    /// window center and its scale must be independently known.
    public static func resolvedBackingScale(
        displayCount: UInt32,
        displayIDs: [CGDirectDisplayID],
        screenScales: [UInt32: Double]
    ) -> Double? {
        guard displayCount == 1,
              let displayID = displayIDs.first,
              let scale = screenScales[displayID],
              scale > 0 else { return nil }
        return scale
    }

    /// The single PNG encoding used for both retention and hashing, so the
    /// recorded image SHA always describes the retained bytes.
    public static func pngData(of image: CGImage) -> Data? {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(
            data,
            UTType.png.identifier as CFString,
            1,
            nil
        ) else { return nil }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { return nil }
        return data as Data
    }

    public static func pngSHA256(of image: CGImage) -> String? {
        guard let data = pngData(of: image) else { return nil }
        let digest = SHA256.hash(data: data)
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    public static func iso8601Now(_ date: Date = Date()) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        formatter.timeZone = TimeZone.current
        return formatter.string(from: date)
    }

    /// Union of the included windows' freshly read frames.
    public static func unionBBox(of windows: [SCWindowSnapshot], fallback: CGRect) -> CGRect {
        guard !windows.isEmpty else { return fallback }
        return windows.dropFirst().reduce(windows[0].frame) { $0.union($1.frame) }
    }
}

@MainActor
public final class FrameCaptureService {
    public private(set) var epochCounter: UInt64
    public let ruleBook: CaptureGeometryRuleBook?

    public init(ruleBook: CaptureGeometryRuleBook?, initialEpoch: UInt64 = 0) {
        self.ruleBook = ruleBook
        self.epochCounter = initialEpoch
    }

    public func nextEpoch() -> UInt64 {
        epochCounter += 1
        return epochCounter
    }

    /// Captures one window frame and returns the structured record. Geometry
    /// violation fails closed inside the record (validity == .invalid), it does not
    /// throw and never re-captures with looser numbers.
    public func capture(
        window: SCWindow,
        configuration: CaptureConfiguration,
        includedWindows: [SCWindowSnapshot],
        state: CaptureGeometryState,
        identityTemplate: WindowIdentity?
    ) async throws -> CapturedFrameRecord {
        try await captureRetained(
            window: window,
            configuration: configuration,
            includedWindows: includedWindows,
            state: state,
            identityTemplate: identityTemplate
        ).record
    }

    /// Capture that also hands back the retained image so one session can run
    /// OCR and retention over the exact bytes whose SHA the record describes.
    public func captureRetained(
        window: SCWindow,
        configuration: CaptureConfiguration,
        includedWindows: [SCWindowSnapshot],
        state: CaptureGeometryState,
        identityTemplate: WindowIdentity?,
        // Explicit capture epoch: the observation session owns the run's epoch
        // authority, so the record must carry the epoch it issued instead of
        // this service's private counter.
        epoch: UInt64? = nil
    ) async throws -> ObservationCapturedImage {
        guard configuration.kind != .explicitLineWindows else {
            throw ObservationRefusal.invalidBundle("explicit LINE capture requires all selected native handles and display")
        }
        guard configuration.kind != .displayRect else {
            throw FrameCaptureError.displayRectUnsupported
        }
        let filter = SCContentFilter(desktopIndependentWindow: window)
        let config = SCScreenshotConfiguration()
        config.includeChildWindows = configuration.includeChildWindows
        config.ignoreShadows = configuration.ignoreShadows
        config.ignoreClipping = configuration.ignoreClipping
        config.showsCursor = configuration.showsCursor
        if let sourceRect = configuration.sourceRect {
            config.sourceRect = sourceRect
        }

        let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: config)
        guard let image = output.sdrImage else {
            throw FrameCaptureError.noImageOutput
        }

        let recordedEpoch = epoch ?? nextEpoch()
        let capturedAt = FrameCaptureSupport.iso8601Now()
        let windowBBox = FrameCaptureSupport.unionBBox(of: includedWindows, fallback: window.frame)
        let expectedBBox = FrameCaptureSupport.expectedCaptureBBox(
            windowBBox: windowBBox,
            sourceRect: configuration.sourceRect
        )
        let recordedExpectedBBox = expectedBBox ?? CGRect(origin: windowBBox.origin, size: .zero)
        let pointPixelScale = Double(filter.pointPixelScale)

        guard let backingScaleFactor = FrameCaptureSupport.backingScaleFactor(forWindowFrame: window.frame) else {
            throw FrameCaptureError.backingScaleUnresolved(windowFrame: window.frame)
        }

        var violationStrings: [String] = []
        if let scaleViolation = CaptureGeometryRules.validateScale(
            pointPixelScale: pointPixelScale,
            backingScaleFactor: backingScaleFactor
        ) {
            violationStrings.append(scaleViolation.description)
        }

        let evaluation: Result<CaptureGeometryEvaluation, CaptureGeometryViolation>
        if let expectedBBox {
            evaluation = CaptureGeometryRules.evaluate(
                expectedBBox: expectedBBox,
                imageWidthPx: image.width,
                imageHeightPx: image.height,
                scale: pointPixelScale,
                ruleBook: ruleBook,
                state: state
            )
        } else {
            violationStrings.append("sourceRect is empty or outside the expected capture bounds")
            evaluation = .failure(.emptyExpectedBBox)
        }

        let actualBBox: CGRect
        let perSide: SideDelta
        let stateKey: String
        switch evaluation {
        case let .success(result):
            actualBBox = result.actualBBoxPt
            perSide = result.perSideSizeDeltaPt
            stateKey = result.stateKey
        case let .failure(violation):
            violationStrings.append(violation.description)
            actualBBox = CGRect(origin: expectedBBox?.origin ?? windowBBox.origin, size: .zero)
            perSide = .zero
            stateKey = CaptureGeometryRules.stateKey(state)
        }

        guard let imageSHA = FrameCaptureSupport.pngSHA256(of: image) else {
            throw FrameCaptureError.pngEncodingFailed
        }

        var identity = identityTemplate
        identity?.captureEpoch = recordedEpoch
        identity?.captureImageSHA256 = imageSHA

        let record = CapturedFrameRecord(
            captureKind: configuration.kind,
            configuration: configuration,
            includedWindows: includedWindows,
            expectedBBoxPt: recordedExpectedBBox,
            imageWidthPx: image.width,
            imageHeightPx: image.height,
            actualBBoxPt: actualBBox,
            perSideSizeDeltaPt: perSide,
            scale: pointPixelScale,
            scaleSource: .pointPixelScale,
            backingScaleFactor: backingScaleFactor,
            epoch: recordedEpoch,
            capturedAtISO8601: capturedAt,
            imageSHA256: imageSHA,
            stateKey: stateKey,
            validity: violationStrings.isEmpty ? .valid : .invalid,
            violations: violationStrings,
            identity: identity
        )
        return ObservationCapturedImage(image: image, record: record)
    }

    /// One full-display popup capture for the read-only `album-support`
    /// producer: `SCContentFilter(display:excludingWindows:[])` with the menu
    /// bar included and no source rect, so an open NSMenu is composited into
    /// the retained bytes. Every claim is recomputed and fails closed before a
    /// record exists; this path never dispatches GUI.
    public func captureFullDisplayRetained(
        display: SCDisplay,
        configuration: CaptureConfiguration
    ) async throws -> ObservationCapturedImage {
        let screens = NSScreen.screens.filter {
            ($0.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value == display.displayID
        }
        guard screens.count == 1, let screen = screens.first,
              screen.backingScaleFactor.isFinite, screen.backingScaleFactor > 0 else {
            throw FullDisplayCaptureRefusal.backingScaleUnresolved
        }
        let backingScale = Double(screen.backingScaleFactor)
        let filter = SCContentFilter(display: display, excludingWindows: [])
        filter.includeMenuBar = true
        let pointPixelScale = Double(filter.pointPixelScale)
        let config = SCScreenshotConfiguration()
        config.includeChildWindows = false
        config.ignoreShadows = false
        config.ignoreClipping = false
        config.showsCursor = false
        let requestStartedAt = fullDisplayCaptureUTCNow()
        let requestStartMonotonic = DispatchTime.now().uptimeNanoseconds
        let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: config)
        let requestEndMonotonic = DispatchTime.now().uptimeNanoseconds
        let requestFinishedAt = fullDisplayCaptureUTCNow()
        guard requestEndMonotonic >= requestStartMonotonic else {
            throw FullDisplayCaptureRefusal.captureTimingInvalid
        }
        guard let image = output.sdrImage else { throw FrameCaptureError.noImageOutput }
        let evaluation = FullDisplayCaptureSupport.evaluate(configuration: configuration,
            displayBoundsPt: display.frame, displayID: display.displayID, pointPixelScale: pointPixelScale,
            backingScaleFactor: backingScale, includeMenuBar: filter.includeMenuBar, contentRect: filter.contentRect,
            imageWidthPx: image.width, imageHeightPx: image.height)
        let value = try evaluation.get()

        guard let imageSHA = FrameCaptureSupport.pngSHA256(of: image) else {
            throw FrameCaptureError.pngEncodingFailed
        }
        let actual = CGRect(origin: display.frame.origin,
            size: CGSize(width: Double(image.width) / pointPixelScale, height: Double(image.height) / pointPixelScale))
        let record = CapturedFrameRecord(
            captureKind: .displayRect,
            configuration: configuration,
            includedWindows: [],
            expectedBBoxPt: display.frame,
            imageWidthPx: image.width,
            imageHeightPx: image.height,
            actualBBoxPt: actual,
            perSideSizeDeltaPt: .zero,
            scale: pointPixelScale,
            scaleSource: .pointPixelScale,
            backingScaleFactor: backingScale,
            epoch: 0,
            capturedAtISO8601: requestStartedAt,
            imageSHA256: imageSHA,
            stateKey: "full-display-popup",
            validity: .valid,
            violations: [],
            identity: nil,
            fullDisplayWitness: value.witness,
            fullDisplayCaptureTiming: FullDisplayCaptureTiming(requestStartedAtISO8601: requestStartedAt,
                requestFinishedAtISO8601: requestFinishedAt, requestStartMonotonicNanoseconds: requestStartMonotonic,
                requestEndMonotonicNanoseconds: requestEndMonotonic)
        )
        return ObservationCapturedImage(image: image, record: record)
    }

private func fullDisplayCaptureUTCNow(_ date: Date = Date()) -> String {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    formatter.timeZone = TimeZone(secondsFromGMT: 0)
    return formatter.string(from: date)
}

    /// One explicit group-filter screenshot. There is no implicit-child, desktop,
    /// app-wide, per-window composite or retry path for this diagnostic kind.
    public func captureExplicitLineRetained(windows: [SCWindow], display: SCDisplay,
        configuration: CaptureConfiguration, includedWindows: [SCWindowSnapshot],
        state: CaptureGeometryState, epoch: UInt64) async throws -> ObservationCapturedImage {
        guard configuration == .explicitLineWindows, epoch > 0, let ruleBook else {
            throw ObservationRefusal.invalidBundle("explicit LINE configuration/rulebook/epoch required")
        }
        try ExplicitLineCaptureSelection.validateRuleBook(ruleBook, state: state)
        let snapshots = windows.map { window in SCWindowSnapshot(windowID: window.windowID, frame: window.frame,
            windowLayer: window.windowLayer, title: window.title, isOnScreen: window.isOnScreen,
            ownerPID: window.owningApplication.map { Int32($0.processID) }, ownerBundleID: window.owningApplication?.bundleIdentifier,
            ownerName: window.owningApplication?.applicationName) }
        guard let main = includedWindows.first(where: { $0.windowLayer == 0 }), let pid = main.ownerPID else {
            throw ObservationRefusal.invalidBundle("explicit LINE main missing")
        }
        try ExplicitLineCaptureSelection.validateFreshSelection(requested: includedWindows, inventory: snapshots,
            target: ObservationTarget(bundleID: PassiveNativeDiagnostic.lineBundleID, pid: pid), main: main)
        let bounds = try ExplicitLineCaptureSelection.union(of: includedWindows)
        let displaySnapshot = ExplicitLineDisplaySnapshot(displayID: display.displayID, frame: display.frame,
            widthPt: display.width, heightPt: display.height)
        _ = try ExplicitLineCaptureSelection.containingDisplay(for: bounds, displays: [displaySnapshot])
        let screens = NSScreen.screens.filter {
            ($0.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value == display.displayID
        }
        guard screens.count == 1, let screen = screens.first,
              screen.backingScaleFactor.isFinite, screen.backingScaleFactor > 0 else {
            throw FrameCaptureError.backingScaleUnresolved(windowFrame: bounds)
        }
        let backing = Double(screen.backingScaleFactor)
        let filter = SCContentFilter(display: display, including: windows)
        filter.includeMenuBar = false
        let scale = Double(filter.pointPixelScale)
        guard scale.isFinite, scale > 0,
              CaptureGeometryRules.validateScale(pointPixelScale: scale, backingScaleFactor: backing) == nil,
              ExplicitLineCaptureSelection.validRect(filter.contentRect), display.frame.contains(filter.contentRect),
              filter.contentRect.contains(bounds) else { throw ObservationRefusal.invalidBundle("explicit LINE filter bounds/scale mismatch") }
        let config = SCScreenshotConfiguration()
        config.includeChildWindows = false; config.ignoreShadows = true; config.ignoreClipping = false; config.showsCursor = false
        config.sourceRect = bounds
        let effective = CaptureConfiguration(kind: .explicitLineWindows, includeChildWindows: config.includeChildWindows,
            ignoreShadows: config.ignoreShadows, ignoreClipping: config.ignoreClipping, showsCursor: config.showsCursor, sourceRect: config.sourceRect)
        let witness = ExplicitLineSelectionWitness(selectedWindowIDs: snapshots.map(\.windowID).sorted(), display: displaySnapshot,
            effectiveSourceRect: config.sourceRect, filterContentRect: filter.contentRect, pointPixelScale: scale,
            includeChildWindows: config.includeChildWindows, includeMenuBar: filter.includeMenuBar)
        let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: config)
        guard let image = output.sdrImage else { throw FrameCaptureError.noImageOutput }
        let evaluation = CaptureGeometryRules.evaluate(expectedBBox: bounds, imageWidthPx: image.width,
            imageHeightPx: image.height, scale: scale, ruleBook: ruleBook, state: state)
        let actual: CGRect
        let residual: SideDelta
        var violations: [String] = []
        switch evaluation {
        case let .success(value): actual = value.actualBBoxPt; residual = value.perSideSizeDeltaPt
        case let .failure(error): actual = CGRect(origin: bounds.origin, size: .zero); residual = .zero; violations.append(error.description)
        }
        guard let sha = FrameCaptureSupport.pngSHA256(of: image) else { throw FrameCaptureError.pngEncodingFailed }
        let record = CapturedFrameRecord(captureKind: .explicitLineWindows, configuration: effective,
            includedWindows: includedWindows, expectedBBoxPt: bounds, imageWidthPx: image.width, imageHeightPx: image.height,
            actualBBoxPt: actual, perSideSizeDeltaPt: residual, scale: scale, scaleSource: .pointPixelScale,
            backingScaleFactor: backing, epoch: epoch, capturedAtISO8601: FrameCaptureSupport.iso8601Now(), imageSHA256: sha,
            stateKey: CaptureGeometryRules.stateKey(state), validity: violations.isEmpty ? .valid : .invalid,
            violations: violations, identity: nil, explicitLineSelectionWitness: witness)
        return ObservationCapturedImage(image: image, record: record)
    }
}
