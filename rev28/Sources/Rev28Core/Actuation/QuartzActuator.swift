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
    /// Plan C5: the exact geometry/candidate facts the permit was minted from,
    /// retained so the post-hover revalidation can prove the fresh live facts
    /// still match this permit instead of re-trusting the caller.
    fileprivate let windowFrame: CGRect
    fileprivate let capturePoint: CapturePixelPoint
    fileprivate let safeRectCapturePx: CGRect
    fileprivate let captureImageSize: CGSize
    fileprivate let mintedAt: Double
    private let lock = NSLock()
    private var consumed = false

    fileprivate init(screenPoint: ScreenPoint, targetPID: Int32, windowID: UInt32, candidateIdentity: String,
                     binding: SurfaceBinding, windowFrame: CGRect, capturePoint: CapturePixelPoint,
                     safeRectCapturePx: CGRect, captureImageSize: CGSize, mintedAt: Double) {
        self.screenPoint = screenPoint
        self.targetPID = targetPID
        self.windowID = windowID
        self.candidateIdentity = candidateIdentity
        self.binding = binding
        self.windowFrame = windowFrame
        self.capturePoint = capturePoint
        self.safeRectCapturePx = safeRectCapturePx
        self.captureImageSize = captureImageSize
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
            windowFrame: observation.captureGeometry.windowFrame,
            capturePoint: point,
            safeRectCapturePx: safe,
            captureImageSize: observation.captureImageSize,
            mintedAt: current
        )
    }

    /// Plan C5 post-hover revalidation: re-run every mint-time freshness fact
    /// (live capture bytes bound to the candidate, window identity/geometry,
    /// safe candidate) against a fresh live observation and require it to
    /// still match the exact permit that is about to click. A geometry move,
    /// occlusion, content change or candidate drift after the hover refuses
    /// before `mouseDown`, so no stale point is ever clicked.
    public static func revalidateAfterHover(
        permit: ReadinessPermit,
        freshObservation: ReadinessObservation,
        maxFrameDeltaPt: Double = 0.5,
        maxPointDeltaPt: Double = 0.5,
        now: Double = ProcessInfo.processInfo.systemUptime
    ) throws {
        guard freshObservation.applicationActive else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("application inactive after the hover")
        }
        guard freshObservation.targetFrontmost else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target not frontmost after the hover")
        }
        guard freshObservation.freshWindow.windowID == permit.windowID,
              freshObservation.freshWindow.process.pid == permit.targetPID,
              freshObservation.freshWindow.process == permit.binding.process,
              freshObservation.freshWindow.bundleID == permit.binding.bundleID,
              freshObservation.freshWindow.layer == 0,
              freshObservation.freshWindow.isOnScreen else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("live window identity changed after the hover")
        }
        guard freshObservation.currentBinding == permit.binding else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("structural candidate binding changed after the hover")
        }
        guard freshObservation.captureGeometry.scale.isFinite, freshObservation.captureGeometry.scale > 0,
              freshObservation.captureImageSize.width > 0, freshObservation.captureImageSize.height > 0 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("fresh capture geometry is invalid after the hover")
        }
        guard now >= freshObservation.observedAtUptime,
              now - freshObservation.observedAtUptime <= 1.0 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("fresh observation is stale after the hover")
        }
        let frame = freshObservation.freshWindow.frame
        guard abs(Double(frame.minX - permit.windowFrame.minX)) <= maxFrameDeltaPt,
              abs(Double(frame.minY - permit.windowFrame.minY)) <= maxFrameDeltaPt,
              abs(Double(frame.width - permit.windowFrame.width)) <= maxFrameDeltaPt,
              abs(Double(frame.height - permit.windowFrame.height)) <= maxFrameDeltaPt else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("window geometry changed after the hover")
        }
        guard permit.safeRectCapturePx.width > 0, permit.safeRectCapturePx.height > 0,
              permit.safeRectCapturePx.contains(CGPoint(x: permit.capturePoint.x, y: permit.capturePoint.y)),
              permit.safeRectCapturePx.maxX <= freshObservation.captureImageSize.width,
              permit.safeRectCapturePx.maxY <= freshObservation.captureImageSize.height else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("safe candidate geometry changed after the hover")
        }
        let freshScreenPoint = freshObservation.captureGeometry.screenPoint(fromCapturePixel: permit.capturePoint)
        guard abs(freshScreenPoint.x - permit.screenPoint.x) <= maxPointDeltaPt,
              abs(freshScreenPoint.y - permit.screenPoint.y) <= maxPointDeltaPt else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("addressed click point moved after the hover")
        }
    }
}

public enum GatedActuationIntent {
    case reversible(PersistentTransactionOwner, action: String)
    case saveAll(PersistentTransactionOwner)
}

/// Public production boundary: no event can be posted without an immediately
/// consumed permit. Tests inject a sink so refusal can be proven event-free.
public enum GatedQuartzActuator {
    /// Plan C5 live topmost-surface check: in the front-to-back on-screen
    /// window order, the first window whose bounds contain the click point
    /// must be the bound target window itself. Any window above the target at
    /// that point (occlusion, a child surface, another app) refuses.
    public static func topmostSurfaceMatchesTarget(at point: ScreenPoint, windowID: UInt32, pid: Int32) -> Bool {
        guard let raw = CGWindowListCopyWindowInfo(
            [.optionOnScreenOnly, .excludeDesktopElements],
            kCGNullWindowID
        ) as? [[String: Any]] else {
            return false
        }
        for entry in raw {
            guard let alpha = entry[kCGWindowAlpha as String] as? Double, alpha > 0 else { continue }
            guard let boundsDictionary = entry[kCGWindowBounds as String] as? [String: Any],
                  let bounds = CGRect(dictionaryRepresentation: boundsDictionary as CFDictionary) else { continue }
            guard bounds.contains(point.cgPoint) else { continue }
            let number = (entry[kCGWindowNumber as String] as? NSNumber)?.uint32Value ?? 0
            let owner = (entry[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value ?? 0
            let layer = (entry[kCGWindowLayer as String] as? NSNumber)?.intValue ?? -1
            return number == windowID && owner == pid && layer == 0
        }
        return false
    }

    public static func postClick(permit: ReadinessPermit,
                                 currentBinding: SurfaceBinding,
                                 intent: GatedActuationIntent,
                                 postHoverRevalidation: @escaping @Sendable () async throws -> Void,
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
                                 addressedSurfaceCheck: @escaping (Int32, UInt32, ScreenPoint) -> Bool = { pid, windowID, point in
                                     GatedQuartzActuator.topmostSurfaceMatchesTarget(at: point, windowID: windowID, pid: pid)
                                 },
                                 now: Double = ProcessInfo.processInfo.systemUptime) async throws {
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
        // Plan C5 pre-dispatch facts: active/frontmost target, process
        // instance, permissions and the topmost addressed surface at the
        // screen point. The same guards run again after the hover.
        func liveGuards() throws {
            guard readinessCheck(permit.targetPID, permit.windowID) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("live target lost foreground/window readiness")
            }
            guard processIdentityCheck(permit.targetPID, permit.binding) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("target bundle or process instance changed")
            }
            guard postEventAccessCheck() else { throw QuartzActuatorError.postEventAccessDenied }
            guard addressedSurfaceCheck(permit.targetPID, permit.windowID, point) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "the addressed surface at the click point is not the bound target window"
                )
            }
        }
        try liveGuards()
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
        // Plan C5: after the hover, revalidate the full fact set and the
        // candidate — the caller's fresh live observation (window
        // identity/geometry, frame-bound candidate, staleness) plus the live
        // guards — before mouseDown. Any failure consumes the permit, durably
        // records the failed candidate revalidation and posts zero down/up.
        do {
            try await postHoverRevalidation()
            try liveGuards()
        } catch {
            Self.recordRevalidationOutcome(intent: intent, passed: false)
            throw QuartzActuatorError.dispatchRefusedByPrecondition(
                "post-hover revalidation failed; mouseDown was not posted (\(error))"
            )
        }
        Self.recordRevalidationOutcome(intent: intent, passed: true)
        sink(down, .cghidEventTap)
        usleep(30_000)
        sink(up, .cghidEventTap)
    }

    /// Plan C4: persist every candidate-revalidation outcome in the owner's
    /// ledger so two consecutive failures durably abort instead of living in
    /// memory. The durable record is written before the refusal surfaces.
    static func recordRevalidationOutcome(intent: GatedActuationIntent, passed: Bool) {
        switch intent {
        case let .reversible(owner, action):
            try? owner.recordCandidateRevalidation(blockerKey: action, passed: passed)
        case let .saveAll(owner):
            try? owner.recordCandidateRevalidation(blockerKey: "saveAll", passed: passed)
        }
    }
}
