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
    /// Display-rectangle corroboration capture (never primary localization).
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
    /// The independent backing-scale source for the display containing the window.
    public static func backingScaleFactor(forWindowFrame frame: CGRect) -> Double? {
        let center = CGPoint(x: frame.midX, y: frame.midY)
        var displayCount: UInt32 = 0
        var displays = [CGDirectDisplayID](repeating: 0, count: 16)
        guard CGGetDisplaysWithPoint(center, UInt32(displays.count), &displays, &displayCount) == .success,
              displayCount > 0 else {
            return nil
        }
        let displayID = displays[0]
        for screen in NSScreen.screens {
            if let number = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber,
               number.uint32Value == displayID {
                return Double(screen.backingScaleFactor)
            }
        }
        return nil
    }

    public static func pngSHA256(of image: CGImage) -> String? {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(
            data,
            UTType.png.identifier as CFString,
            1,
            nil
        ) else { return nil }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { return nil }
        let digest = SHA256.hash(data: data as Data)
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

        let epoch = nextEpoch()
        let capturedAt = FrameCaptureSupport.iso8601Now()
        let expectedBBox = FrameCaptureSupport.unionBBox(of: includedWindows, fallback: window.frame)
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

        let evaluation = CaptureGeometryRules.evaluate(
            expectedBBox: expectedBBox,
            imageWidthPx: image.width,
            imageHeightPx: image.height,
            scale: pointPixelScale,
            ruleBook: ruleBook,
            state: state
        )

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
            actualBBox = CGRect(origin: expectedBBox.origin, size: .zero)
            perSide = .zero
            stateKey = CaptureGeometryRules.stateKey(state)
        }

        guard let imageSHA = FrameCaptureSupport.pngSHA256(of: image) else {
            throw FrameCaptureError.pngEncodingFailed
        }

        var identity = identityTemplate
        identity?.captureEpoch = epoch
        identity?.captureImageSHA256 = imageSHA

        return CapturedFrameRecord(
            captureKind: configuration.kind,
            configuration: configuration,
            includedWindows: includedWindows,
            expectedBBoxPt: expectedBBox,
            imageWidthPx: image.width,
            imageHeightPx: image.height,
            actualBBoxPt: actualBBox,
            perSideSizeDeltaPt: perSide,
            scale: pointPixelScale,
            scaleSource: .pointPixelScale,
            backingScaleFactor: backingScaleFactor,
            epoch: epoch,
            capturedAtISO8601: capturedAt,
            imageSHA256: imageSHA,
            stateKey: stateKey,
            validity: violationStrings.isEmpty ? .valid : .invalid,
            violations: violationStrings,
            identity: identity
        )
    }
}
