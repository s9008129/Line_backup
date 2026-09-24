import CoreGraphics
import Darwin
import Foundation

// MARK: - Window identity binding (plan §ARCHITECTURE §2, S-03)
//
// A window is selected by bundle + pid instance + layer + live geometry, never by
// windowID alone. A windowID is only valid inside one capture epoch; before every
// dispatch the target window is re-enumerated and re-derived. Identity never
// carries historical coordinates.

/// A process instance: pid plus the process start time, so pid reuse is rejected.
public struct ProcessInstanceID: Equatable, Hashable, Codable, Sendable, CustomStringConvertible {
    public let pid: Int32
    public let startTimeSeconds: Int64
    public let startTimeMicroseconds: Int32

    public init(pid: Int32, startTimeSeconds: Int64, startTimeMicroseconds: Int32) {
        self.pid = pid
        self.startTimeSeconds = startTimeSeconds
        self.startTimeMicroseconds = startTimeMicroseconds
    }

    public var description: String { "pid=\(pid)@\(startTimeSeconds).\(startTimeMicroseconds)" }

    /// Reads the current process instance via `proc_pidinfo(PROC_PIDTBSDINFO)`.
    /// Returns nil when the process does not exist or the info is unavailable.
    public static func current(pid: Int32) -> ProcessInstanceID? {
        var info = proc_bsdinfo()
        let size = MemoryLayout<proc_bsdinfo>.size
        let result = withUnsafeMutablePointer(to: &info) { pointer -> Int32 in
            proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, pointer, Int32(size))
        }
        guard result == Int32(size) else { return nil }
        return ProcessInstanceID(
            pid: pid,
            startTimeSeconds: Int64(info.pbi_start_tvsec),
            startTimeMicroseconds: Int32(info.pbi_start_tvusec)
        )
    }
}

/// The CGWindowList entry used for cross-checking (window id/frame/layer/owner).
public struct CGWindowEntryRecord: Equatable, Codable, Sendable {
    public let windowID: UInt32
    public let frame: CGRect
    public let layer: Int
    public let ownerPID: Int32
    public let ownerName: String

    public init(windowID: UInt32, frame: CGRect, layer: Int, ownerPID: Int32, ownerName: String) {
        self.windowID = windowID
        self.frame = frame
        self.layer = layer
        self.ownerPID = ownerPID
        self.ownerName = ownerName
    }
}

/// Read-only AX identity fields (plan §ARCHITECTURE §6). Never written here.
public struct AXIdentityRead: Equatable, Codable, Sendable {
    public let role: String?
    public let subrole: String?
    public let title: String?

    public init(role: String?, subrole: String?, title: String?) {
        self.role = role
        self.subrole = subrole
        self.title = title
    }
}

/// Full bound identity for one capture epoch of one window.
public struct WindowIdentity: Equatable, Codable, Sendable {
    public var bundleID: String
    public var process: ProcessInstanceID
    public var windowID: UInt32
    public var windowFrame: CGRect
    public var ax: AXIdentityRead
    public var cgEntry: CGWindowEntryRecord
    public var captureEpoch: UInt64
    public var captureImageSHA256: String

    public init(
        bundleID: String,
        process: ProcessInstanceID,
        windowID: UInt32,
        windowFrame: CGRect,
        ax: AXIdentityRead,
        cgEntry: CGWindowEntryRecord,
        captureEpoch: UInt64,
        captureImageSHA256: String
    ) {
        self.bundleID = bundleID
        self.process = process
        self.windowID = windowID
        self.windowFrame = windowFrame
        self.ax = ax
        self.cgEntry = cgEntry
        self.captureEpoch = captureEpoch
        self.captureImageSHA256 = captureImageSHA256
    }

    /// A perception result is only valid for the epoch it was captured in.
    public func isValidInEpoch(_ epoch: UInt64) -> Bool {
        captureEpoch == epoch
    }
}

/// A fresh enumeration result (from SC/CG/AX) to validate an existing identity against.
public struct FreshWindowObservation: Equatable, Codable, Sendable {
    public let bundleID: String
    public let process: ProcessInstanceID
    public let windowID: UInt32
    public let frame: CGRect
    public let layer: Int
    public let isOnScreen: Bool

    public init(
        bundleID: String,
        process: ProcessInstanceID,
        windowID: UInt32,
        frame: CGRect,
        layer: Int,
        isOnScreen: Bool
    ) {
        self.bundleID = bundleID
        self.process = process
        self.windowID = windowID
        self.frame = frame
        self.layer = layer
        self.isOnScreen = isOnScreen
    }
}

public enum IdentityViolation: Error, Equatable, Sendable, CustomStringConvertible {
    case bundleMismatch(expected: String, actual: String)
    case pidMismatch(expected: Int32, actual: Int32)
    case processInstanceChanged(expected: ProcessInstanceID, actual: ProcessInstanceID)
    case windowIDChanged(old: UInt32, new: UInt32)
    case windowLayerNotZero(layer: Int)
    case windowOffscreen
    case frameDeltaExceedsTolerance(maxDeltaPt: Double)
    case staleEpoch(identityEpoch: UInt64, currentEpoch: UInt64)

    public var description: String {
        switch self {
        case let .bundleMismatch(expected, actual):
            return "bundleMismatch(expected=\(expected), actual=\(actual))"
        case let .pidMismatch(expected, actual):
            return "pidMismatch(expected=\(expected), actual=\(actual))"
        case let .processInstanceChanged(expected, actual):
            return "processInstanceChanged(expected=\(expected), actual=\(actual))"
        case let .windowIDChanged(old, new):
            return "windowIDChanged(old=\(old), new=\(new))"
        case let .windowLayerNotZero(layer):
            return "windowLayerNotZero(layer=\(layer))"
        case .windowOffscreen:
            return "windowOffscreen"
        case let .frameDeltaExceedsTolerance(maxDeltaPt):
            return "frameDeltaExceedsTolerance(maxDeltaPt=\(maxDeltaPt))"
        case let .staleEpoch(identityEpoch, currentEpoch):
            return "staleEpoch(identityEpoch=\(identityEpoch), currentEpoch=\(currentEpoch))"
        }
    }
}

public enum WindowIdentityValidator {
    /// Cross-checks a bound identity against a fresh enumeration. Any violation
    /// invalidates the candidate: re-locate, never reuse coordinates.
    public static func validate(
        identity: WindowIdentity,
        against fresh: FreshWindowObservation,
        maxFrameDeltaPt: Double,
        currentEpoch: UInt64
    ) -> [IdentityViolation] {
        var violations: [IdentityViolation] = []
        if identity.bundleID != fresh.bundleID {
            violations.append(.bundleMismatch(expected: identity.bundleID, actual: fresh.bundleID))
        }
        if identity.process.pid != fresh.process.pid {
            violations.append(.pidMismatch(expected: identity.process.pid, actual: fresh.process.pid))
        } else if identity.process != fresh.process {
            violations.append(.processInstanceChanged(expected: identity.process, actual: fresh.process))
        }
        if identity.windowID != fresh.windowID {
            violations.append(.windowIDChanged(old: identity.windowID, new: fresh.windowID))
        }
        if fresh.layer != 0 {
            violations.append(.windowLayerNotZero(layer: fresh.layer))
        }
        if !fresh.isOnScreen {
            violations.append(.windowOffscreen)
        }
        let dx = abs(Double(identity.windowFrame.minX - fresh.frame.minX))
        let dy = abs(Double(identity.windowFrame.minY - fresh.frame.minY))
        let dw = abs(Double(identity.windowFrame.width - fresh.frame.width))
        let dh = abs(Double(identity.windowFrame.height - fresh.frame.height))
        if max(dx, max(dy, max(dw, dh))) > maxFrameDeltaPt {
            violations.append(.frameDeltaExceedsTolerance(maxDeltaPt: maxFrameDeltaPt))
        }
        if !identity.isValidInEpoch(currentEpoch) {
            violations.append(.staleEpoch(identityEpoch: identity.captureEpoch, currentEpoch: currentEpoch))
        }
        return violations
    }

    /// Convenience predicate: an identity is fresh only when it has no violations.
    public static func isFresh(
        identity: WindowIdentity,
        against fresh: FreshWindowObservation,
        maxFrameDeltaPt: Double,
        currentEpoch: UInt64
    ) -> Bool {
        validate(
            identity: identity,
            against: fresh,
            maxFrameDeltaPt: maxFrameDeltaPt,
            currentEpoch: currentEpoch
        ).isEmpty
    }
}
