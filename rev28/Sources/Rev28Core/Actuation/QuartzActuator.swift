import AppKit
import CoreGraphics
import Foundation
import ScreenCaptureKit

// MARK: - Quartz actuator (plan §ARCHITECTURE §5)
//
// One actuator code path only; screen-global points; no window-relative
// abstraction, no app-specific magic. The dispatch sequence itself is driven by
// the engine; this type performs the raw event posting and preflight.

public struct DispatchRecord: Equatable, Codable, Sendable {
    public let screenPoint: ScreenPoint
    public let windowLocalPoint: WindowLocalPoint?
    public let capturePixelPoint: CapturePixelPoint?
    public let windowID: UInt32?
    public let epoch: UInt64?
    public let frameSHA256: String?
    public let candidateSHA256: String?
    public let riskClass: String
    public let ledgerID: String?
    public let dispatchedAtISO8601: String

    public init(
        screenPoint: ScreenPoint,
        windowLocalPoint: WindowLocalPoint?,
        capturePixelPoint: CapturePixelPoint?,
        windowID: UInt32?,
        epoch: UInt64?,
        frameSHA256: String?,
        candidateSHA256: String?,
        riskClass: String,
        ledgerID: String?,
        dispatchedAtISO8601: String
    ) {
        self.screenPoint = screenPoint
        self.windowLocalPoint = windowLocalPoint
        self.capturePixelPoint = capturePixelPoint
        self.windowID = windowID
        self.epoch = epoch
        self.frameSHA256 = frameSHA256
        self.candidateSHA256 = candidateSHA256
        self.riskClass = riskClass
        self.ledgerID = ledgerID
        self.dispatchedAtISO8601 = dispatchedAtISO8601
    }
}

public enum QuartzActuatorError: Error, Equatable, Sendable, CustomStringConvertible {
    case postEventAccessDenied
    case eventCreationFailed
    case dispatchRefusedByPrecondition(String)

    public var description: String {
        switch self {
        case .postEventAccessDenied:
            return "postEventAccessDenied"
        case .eventCreationFailed:
            return "eventCreationFailed"
        case let .dispatchRefusedByPrecondition(reason):
            return "dispatchRefusedByPrecondition(\(reason))"
        }
    }
}

public enum QuartzActuator {
    public static func preflightPostEventAccess() -> Bool {
        CGPreflightPostEventAccess()
    }

    /// Requests post-event access only when the preflight says it is needed.
    static func preflightOrRequestPostEventAccess() -> Bool {
        if CGPreflightPostEventAccess() { return true }
        return CGRequestPostEventAccess()
    }

    static func postMouseMoved(to point: ScreenPoint) throws {
        guard preflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        guard let event = CGEvent(
            mouseEventSource: nil,
            mouseType: .mouseMoved,
            mouseCursorPosition: point.cgPoint,
            mouseButton: .left
        ) else { throw QuartzActuatorError.eventCreationFailed }
        event.post(tap: .cghidEventTap)
    }

    /// mouseMoved -> leftMouseDown -> short inter-event delay -> leftMouseUp.
    /// The caller owns pre/post revalidation; this function posts exactly once.
    static func postClick(
        at point: ScreenPoint,
        interEventDelayMicroseconds: UInt32 = 30_000
    ) throws {
        guard preflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        guard let move = CGEvent(
            mouseEventSource: nil,
            mouseType: .mouseMoved,
            mouseCursorPosition: point.cgPoint,
            mouseButton: .left
        ) else { throw QuartzActuatorError.eventCreationFailed }
        guard let down = CGEvent(
            mouseEventSource: nil,
            mouseType: .leftMouseDown,
            mouseCursorPosition: point.cgPoint,
            mouseButton: .left
        ) else { throw QuartzActuatorError.eventCreationFailed }
        guard let up = CGEvent(
            mouseEventSource: nil,
            mouseType: .leftMouseUp,
            mouseCursorPosition: point.cgPoint,
            mouseButton: .left
        ) else { throw QuartzActuatorError.eventCreationFailed }

        move.post(tap: .cghidEventTap)
        down.post(tap: .cghidEventTap)
        usleep(interEventDelayMicroseconds)
        up.post(tap: .cghidEventTap)
    }

    /// Posts one key chord (keyDown + keyUp) with modifiers. Used by the reviewed
    /// keyboard chooser-navigation path (⇧⌘G) only after fresh identity verification.
    static func postKeyChord(keyCode: CGKeyCode, flags: CGEventFlags) throws {
        guard preflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        guard let down = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true),
              let up = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false) else {
            throw QuartzActuatorError.eventCreationFailed
        }
        down.flags = flags
        up.flags = flags
        down.post(tap: .cghidEventTap)
        up.post(tap: .cghidEventTap)
    }

    /// Posts one Unicode string as keyboard events (chunked; the API accepts a
    /// bounded number of UTF-16 units per event). Used for the reviewed
    /// Go-to-folder path entry.
    static func postUnicodeText(_ text: String, chunkSize: Int = 20) throws {
        guard preflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        let units = Array(text.utf16)
        var index = 0
        while index < units.count {
            let end = min(index + chunkSize, units.count)
            let chunk = Array(units[index..<end])
            guard let down = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true),
                  let up = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false) else {
                throw QuartzActuatorError.eventCreationFailed
            }
            chunk.withUnsafeBufferPointer { buffer in
                down.keyboardSetUnicodeString(stringLength: buffer.count, unicodeString: buffer.baseAddress)
                up.keyboardSetUnicodeString(stringLength: buffer.count, unicodeString: buffer.baseAddress)
            }
            down.post(tap: .cghidEventTap)
            up.post(tap: .cghidEventTap)
            index = end
        }
    }

    static func postReturnKey() throws {
        try postKeyChord(keyCode: 36, flags: [])
    }

    static func postGoToFolderChord() throws {
        try postKeyChord(keyCode: 5, flags: [.maskCommand, .maskShift])
    }
}

public struct ReadinessObservation: Sendable {
    public let applicationActive: Bool
    public let targetFrontmost: Bool
    public let freshWindow: FreshWindowObservation
    public let currentEpoch: UInt64
    public let currentBinding: SurfaceBinding
    public let captureGeometry: CaptureGeometry
    public let captureImageSize: CGSize
    public let observedAtUptime: Double

    public init(applicationActive: Bool, targetFrontmost: Bool, freshWindow: FreshWindowObservation,
                currentEpoch: UInt64, currentBinding: SurfaceBinding, captureGeometry: CaptureGeometry,
                captureImageSize: CGSize, observedAtUptime: Double) {
        self.applicationActive = applicationActive
        self.targetFrontmost = targetFrontmost
        self.freshWindow = freshWindow
        self.currentEpoch = currentEpoch
        self.currentBinding = currentBinding
        self.captureGeometry = captureGeometry
        self.captureImageSize = captureImageSize
        self.observedAtUptime = observedAtUptime
    }

    public static func captureLive(identity: WindowIdentity, candidate: StructuralCandidate) async throws -> ReadinessObservation {
        let pid = pid_t(identity.process.pid)
        guard let application = NSRunningApplication(processIdentifier: pid) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target process is not running")
        }
        guard let applicationBundleID = application.bundleIdentifier,
              applicationBundleID == identity.bundleID,
              let liveProcess = ProcessInstanceID.current(pid: identity.process.pid),
              liveProcess == identity.process else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target bundle or process instance changed")
        }
        let active = application.isActive
        let frontmost = NSWorkspace.shared.frontmostApplication?.processIdentifier == pid
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        let snapshots = WindowSensor.snapshots(from: content)
        let candidates = WindowSensor.mainWindowCandidates(in: snapshots, bundleID: identity.bundleID, pid: identity.process.pid)
        guard candidates.count == 1, let window = candidates.first,
              window.windowID == identity.windowID else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("fresh SC window census is ambiguous or changed")
        }
        let cgMatches = CGWindowInventory.onScreenWindows().filter {
            $0.windowNumber == identity.windowID && $0.ownerPID == identity.process.pid && $0.layer == 0
        }
        guard cgMatches.count == 1 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("fresh CG window census is ambiguous or missing")
        }
        guard let liveWindow = content.windows.first(where: { $0.windowID == window.windowID }) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("fresh SC window handle unavailable")
        }
        let screenshotConfiguration = SCScreenshotConfiguration()
        screenshotConfiguration.includeChildWindows = false
        screenshotConfiguration.ignoreShadows = true
        screenshotConfiguration.showsCursor = false
        guard let image = try await SCScreenshotManager.captureScreenshot(
            contentFilter: SCContentFilter(desktopIndependentWindow: liveWindow),
            configuration: screenshotConfiguration
        ).sdrImage,
        FrameCaptureSupport.pngSHA256(of: image) == candidate.binding.frameSHA256,
        candidate.binding.frameSHA256 == identity.captureImageSHA256 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("candidate is not bound to the fresh live frame")
        }
        let pointPixelScale = Double(SCContentFilter(desktopIndependentWindow: liveWindow).pointPixelScale)
        guard pointPixelScale.isFinite, pointPixelScale > 0 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("live capture scale is invalid")
        }
        let fresh = FreshWindowObservation(
            bundleID: applicationBundleID,
            process: liveProcess,
            windowID: window.windowID,
            frame: window.frame,
            layer: window.windowLayer,
            isOnScreen: window.isOnScreen
        )
        return ReadinessObservation(
            applicationActive: active,
            targetFrontmost: frontmost,
            freshWindow: fresh,
            currentEpoch: identity.captureEpoch,
            currentBinding: candidate.binding,
            captureGeometry: CaptureGeometry(
                windowFrame: window.frame,
                captureBBox: window.frame,
                scale: pointPixelScale
            ),
            captureImageSize: CGSize(width: image.width, height: image.height),
            observedAtUptime: ProcessInfo.processInfo.systemUptime
        )
    }
}

public final class ReadinessPermit: @unchecked Sendable {
    fileprivate let screenPoint: ScreenPoint
    fileprivate let targetPID: Int32
    fileprivate let windowID: UInt32
    fileprivate let candidateIdentity: String
    fileprivate let binding: SurfaceBinding
    fileprivate let mintedAt: Double
    private let lock = NSLock()
    private var consumed = false

    fileprivate init(screenPoint: ScreenPoint, targetPID: Int32, windowID: UInt32, candidateIdentity: String,
                     binding: SurfaceBinding, mintedAt: Double) {
        self.screenPoint = screenPoint
        self.targetPID = targetPID
        self.windowID = windowID
        self.candidateIdentity = candidateIdentity
        self.binding = binding
        self.mintedAt = mintedAt
    }

    fileprivate func consume(now: Double) throws -> ScreenPoint {
        lock.lock()
        defer { lock.unlock() }
        guard !consumed else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("permit expired or already consumed")
        }
        consumed = true
        guard now >= mintedAt, now - mintedAt <= 1.0 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("permit expired or already consumed")
        }
        return screenPoint
    }
}

public enum DispatchReadinessGate {
    public static func mintPermit(identity: WindowIdentity, candidate: StructuralCandidate,
                                  observation: ReadinessObservation, maxFrameDeltaPt: Double = 0.5,
                                  now: Double = ProcessInfo.processInfo.systemUptime) throws -> ReadinessPermit {
        guard observation.applicationActive else { throw QuartzActuatorError.dispatchRefusedByPrecondition("application inactive") }
        guard observation.targetFrontmost else { throw QuartzActuatorError.dispatchRefusedByPrecondition("target not frontmost") }
        guard WindowIdentityValidator.isFresh(identity: identity, against: observation.freshWindow,
                                              maxFrameDeltaPt: maxFrameDeltaPt,
                                              currentEpoch: observation.currentEpoch) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("stale window identity")
        }
        guard candidate.binding == observation.currentBinding,
              candidate.binding.bundleID == identity.bundleID,
              candidate.binding.process == identity.process,
              candidate.binding.windowID == identity.windowID,
              candidate.binding.captureEpoch == identity.captureEpoch,
              candidate.binding.frameSHA256 == identity.captureImageSHA256 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("stale structural candidate")
        }
        let point = candidate.pointCapturePx
        let safe = candidate.safeRectCapturePx
        guard safe.width > 0, safe.height > 0,
              safe.contains(CGPoint(x: point.x, y: point.y)),
              point.x > Double(safe.minX) + 1, point.x < Double(safe.maxX) - 1,
              point.y > Double(safe.minY) + 1, point.y < Double(safe.maxY) - 1,
              identity.cgEntry.frame.width > 0, identity.cgEntry.frame.height > 0,
              observation.captureGeometry.scale.isFinite, observation.captureGeometry.scale > 0,
              observation.captureGeometry.captureBBox.width > 0, observation.captureGeometry.captureBBox.height > 0,
              observation.captureImageSize.width > 0, observation.captureImageSize.height > 0,
              safe.minX >= 0, safe.minY >= 0,
              safe.maxX <= observation.captureImageSize.width,
              safe.maxY <= observation.captureImageSize.height,
              point.x < Double(observation.captureImageSize.width),
              point.y < Double(observation.captureImageSize.height),
              abs(Double(observation.captureGeometry.windowFrame.minX - observation.freshWindow.frame.minX)) <= 0.5,
              abs(Double(observation.captureGeometry.windowFrame.minY - observation.freshWindow.frame.minY)) <= 0.5,
              abs(Double(observation.captureGeometry.windowFrame.width - observation.freshWindow.frame.width)) <= 0.5,
              abs(Double(observation.captureGeometry.windowFrame.height - observation.freshWindow.frame.height)) <= 0.5 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("unsafe candidate geometry")
        }
        let current = now
        guard current >= observation.observedAtUptime, current - observation.observedAtUptime <= 1.0 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("readiness observation stale")
        }
        let screen = observation.captureGeometry.screenPoint(fromCapturePixel: point)
        return ReadinessPermit(
            screenPoint: screen,
            targetPID: identity.process.pid,
            windowID: identity.windowID,
            candidateIdentity: candidate.identity,
            binding: candidate.binding,
            mintedAt: current
        )
    }
}

public enum GatedActuationIntent {
    case reversible(PersistentTransactionOwner, action: String)
    case saveAll(PersistentTransactionOwner)
}

/// Public production boundary: no event can be posted without an immediately
/// consumed permit. Tests inject a sink so refusal can be proven event-free.
public enum GatedQuartzActuator {
    public static func postClick(permit: ReadinessPermit,
                                 currentBinding: SurfaceBinding,
                                 intent: GatedActuationIntent,
                                 sink: @escaping (CGEvent, CGEventTapLocation) -> Void = { $0.post(tap: $1) },
                                 readinessCheck: @escaping (Int32, UInt32) -> Bool = { pid, windowID in
                                     guard let app = NSRunningApplication(processIdentifier: pid),
                                           app.isActive,
                                           NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { return false }
                                     return CGWindowInventory.onScreenWindows().contains {
                                         $0.windowNumber == windowID && $0.ownerPID == pid && $0.layer == 0
                                     }
                                 },
                                 processIdentityCheck: @escaping (Int32, SurfaceBinding) -> Bool = { pid, binding in
                                     guard let application = NSRunningApplication(processIdentifier: pid_t(pid)),
                                           application.bundleIdentifier == binding.bundleID,
                                           ProcessInstanceID.current(pid: pid) == binding.process else { return false }
                                     return true
                                 },
                                 postEventAccessCheck: @escaping () -> Bool = { CGPreflightPostEventAccess() },
                                 now: Double = ProcessInfo.processInfo.systemUptime) throws {
        let point = try permit.consume(now: now)
        guard permit.binding == currentBinding else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("structural candidate binding is no longer current")
        }
        switch intent {
        case .saveAll:
            guard permit.candidateIdentity == "儲存全部" else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("Save All intent does not match the bound structural candidate")
            }
        case .reversible:
            guard permit.candidateIdentity != "儲存全部" else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("Save All candidate requires irreversible owner intent")
            }
        }
        guard readinessCheck(permit.targetPID, permit.windowID) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("live target lost foreground/window readiness")
        }
        guard processIdentityCheck(permit.targetPID, permit.binding) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target bundle or process instance changed")
        }
        guard postEventAccessCheck() else { throw QuartzActuatorError.postEventAccessDenied }
        guard let move = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point.cgPoint, mouseButton: .left),
              let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point.cgPoint, mouseButton: .left),
              let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point.cgPoint, mouseButton: .left) else {
            throw QuartzActuatorError.eventCreationFailed
        }
        switch intent {
        case let .reversible(owner, action):
            try owner.recordReversibleDispatch(action: action)
        case let .saveAll(owner):
            try owner.reserveSaveAll()
            try owner.markSaveAllAttempted()
        }
        sink(move, .cghidEventTap)
        // Plan C5: readiness is revalidated after the hover and immediately
        // before mouseDown. Focus theft in that window must consume the
        // permit without ever posting a click to whatever is frontmost now.
        guard readinessCheck(permit.targetPID, permit.windowID),
              processIdentityCheck(permit.targetPID, permit.binding),
              postEventAccessCheck() else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition(
                "live target lost foreground/window readiness after the hover; mouseDown was not posted"
            )
        }
        sink(down, .cghidEventTap)
        usleep(30_000)
        sink(up, .cghidEventTap)
    }
}
