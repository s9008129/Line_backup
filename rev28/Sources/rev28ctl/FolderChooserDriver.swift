import AppKit
import ApplicationServices
import Foundation
import Rev28Core

// Compatibility surface for the byte-frozen synthetic calibration harness.
// Production callers use Rev28Core's transaction-owner confirmation path.
enum FolderChooserDriver {
    static func defaultButton(pid: pid_t, titles: [String] = []) -> AXUIElement? {
        for window in AXDriver.windows(ofApp: pid) {
            if let button = AXDriver.firstDescendant(of: window, maxDepth: 12, matching: { element in
                guard AXDriver.role(of: element) == (kAXButtonRole as String) else { return false }
                return AXDriver.keyEquivalent(of: element) == "\r"
                    || titles.contains(AXDriver.title(of: element) ?? "")
            }) { return button }
        }
        return nil
    }

    static func navigateToDestination(pid: pid_t, destination: URL, timeoutSeconds: Double = 8.0) throws -> [String] {
        let target = destination.standardizedFileURL.path
        try QuartzActuator.postKeyChord(keyCode: 5, flags: [.maskCommand, .maskShift])
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        var field: AXUIElement?
        while Date() < deadline {
            if let raw = AXDriver.copyAttribute(AXDriver.appElement(pid: pid), kAXFocusedUIElementAttribute as String),
               CFGetTypeID(raw) == AXUIElementGetTypeID() {
                let focused = raw as! AXUIElement
                if AXDriver.role(of: focused) == (kAXTextFieldRole as String) {
                    field = focused
                    break
                }
            }
            usleep(100_000)
        }
        guard let field else { throw FolderChooserDriverError.goToFolderEntryMissing }
        var settable = DarwinBoolean(false)
        if AXUIElementIsAttributeSettable(field, kAXValueAttribute as CFString, &settable) == .success, settable.boolValue {
            _ = AXUIElementSetAttributeValue(field, kAXValueAttribute as CFString, target as CFString)
        }
        if AXDriver.valueAsString(field) != target {
            try QuartzActuator.postKeyChord(keyCode: 0, flags: [.maskCommand])
            try QuartzActuator.postUnicodeText(target)
        }
        guard AXDriver.valueAsString(field) == target else {
            throw FolderChooserDriverError.pathEntryFailed("AX field does not match exact standardized destination")
        }
        try QuartzActuator.postKeyChord(keyCode: 36, flags: [])
        while Date() < deadline {
            let candidates = directoryCandidates(pid: pid)
            if candidates.contains(where: { URL(fileURLWithPath: $0).standardizedFileURL.path == target }) {
                return candidates
            }
            usleep(100_000)
        }
        throw FolderChooserDriverError.destinationMismatch(requested: target, observed: directoryCandidates(pid: pid))
    }

    static func pressDefaultButton(pid: pid_t, titles: [String] = []) throws -> String {
        for window in AXDriver.windows(ofApp: pid) {
            if let button = AXDriver.firstDescendant(of: window, maxDepth: 12, matching: { element in
                guard AXDriver.role(of: element) == (kAXButtonRole as String) else { return false }
                return AXDriver.keyEquivalent(of: element) == "\r"
                    || titles.contains(AXDriver.title(of: element) ?? "")
            }) {
                let title = AXDriver.title(of: button) ?? "?"
                guard AXDriver.press(button) else { throw FolderChooserDriverError.pressFailed("AXPress failed") }
                return "role=AXButton title=\(title)"
            }
        }
        throw FolderChooserDriverError.defaultButtonMissing
    }

    static func directoryCandidates(pid: pid_t) -> [String] {
        var candidates: [String] = []
        for window in AXDriver.windows(ofApp: pid) {
            for node in AXDriver.allDescendants(of: window, maxDepth: 7, matching: { _ in true }) {
                if let value = AXDriver.valueAsString(node), value.contains("/") { candidates.append(value) }
                if let title = AXDriver.title(of: node), title.contains("/") { candidates.append(title) }
            }
        }
        return Array(Set(candidates)).sorted()
    }

    static func destinationIsReflected(pid: pid_t, destination: URL) -> Bool {
        let target = destination.standardizedFileURL.path
        return directoryCandidates(pid: pid).contains {
            URL(fileURLWithPath: $0).standardizedFileURL.path == target
        }
    }
}
