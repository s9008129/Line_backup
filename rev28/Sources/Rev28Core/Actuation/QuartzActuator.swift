import CoreGraphics
import Foundation

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
    public static func preflightOrRequestPostEventAccess() -> Bool {
        if CGPreflightPostEventAccess() { return true }
        return CGRequestPostEventAccess()
    }

    public static func postMouseMoved(to point: ScreenPoint) throws {
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
    public static func postClick(
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
    public static func postKeyChord(keyCode: CGKeyCode, flags: CGEventFlags) throws {
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
    public static func postUnicodeText(_ text: String, chunkSize: Int = 20) throws {
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

    public static func postReturnKey() throws {
        try postKeyChord(keyCode: 36, flags: [])
    }

    public static func postGoToFolderChord() throws {
        try postKeyChord(keyCode: 5, flags: [.maskCommand, .maskShift])
    }
}
