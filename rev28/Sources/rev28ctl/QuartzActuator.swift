import CoreGraphics
import Foundation
import Rev28Core

// Synthetic harness-only compatibility surface. This target-local declaration
// shadows Rev28Core's gated actuator for the frozen calibration source.
enum QuartzActuator {
    static func postClick(at point: ScreenPoint, interEventDelayMicroseconds: UInt32 = 30_000) throws {
        guard CGPreflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        guard let move = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point.cgPoint, mouseButton: .left),
              let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point.cgPoint, mouseButton: .left),
              let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point.cgPoint, mouseButton: .left) else {
            throw QuartzActuatorError.eventCreationFailed
        }
        move.post(tap: .cghidEventTap)
        down.post(tap: .cghidEventTap)
        usleep(interEventDelayMicroseconds)
        up.post(tap: .cghidEventTap)
    }

    static func postKeyChord(keyCode: CGKeyCode, flags: CGEventFlags) throws {
        guard CGPreflightPostEventAccess(),
              let down = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true),
              let up = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false) else {
            throw QuartzActuatorError.eventCreationFailed
        }
        down.flags = flags
        up.flags = flags
        down.post(tap: .cghidEventTap)
        up.post(tap: .cghidEventTap)
    }

    static func postUnicodeText(_ text: String) throws {
        let units = Array(text.utf16)
        guard CGPreflightPostEventAccess() else { throw QuartzActuatorError.postEventAccessDenied }
        var index = 0
        while index < units.count {
            let end = min(index + 20, units.count)
            let chunk = Array(units[index..<end])
            guard let down = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true),
                  let up = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false) else {
                throw QuartzActuatorError.eventCreationFailed
            }
            chunk.withUnsafeBufferPointer {
                down.keyboardSetUnicodeString(stringLength: $0.count, unicodeString: $0.baseAddress)
                up.keyboardSetUnicodeString(stringLength: $0.count, unicodeString: $0.baseAddress)
            }
            down.post(tap: .cghidEventTap)
            up.post(tap: .cghidEventTap)
            index = end
        }
    }
}
