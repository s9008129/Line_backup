import ApplicationServices
import CoreGraphics
import Foundation

// MARK: - Folder-chooser driver (plan §ARCHITECTURE §11)
//
// Navigation: keyboard Go-to-folder path (⇧⌘G + Unicode entry via
// `CGEventKeyboardSetUnicodeString` + Return) only after fresh chooser identity
// verification. Confirmation: exactly one action is chosen before dispatch —
// `AXPress` on the unambiguous default button, else Return — never both.
// Destination preparation steps are logged with pre/post evidence and are never
// themselves a confirmation.

public enum ChooserConfirmationAction: String, Codable, Sendable {
    case axPressDefaultButton
    case returnKey
}

public struct ChooserDriveRecord: Equatable, Codable, Sendable {
    public let panelPID: Int32
    public let destinationRequested: String
    public let navigation: String
    public let confirmationAction: ChooserConfirmationAction
    public let pressedButtonDescription: String?
    public let destinationCandidatesAfterNavigation: [String]
    public let destinationVerified: Bool
    public let atISO8601: String

    public init(
        panelPID: Int32,
        destinationRequested: String,
        navigation: String,
        confirmationAction: ChooserConfirmationAction,
        pressedButtonDescription: String?,
        destinationCandidatesAfterNavigation: [String],
        destinationVerified: Bool,
        atISO8601: String
    ) {
        self.panelPID = panelPID
        self.destinationRequested = destinationRequested
        self.navigation = navigation
        self.confirmationAction = confirmationAction
        self.pressedButtonDescription = pressedButtonDescription
        self.destinationCandidatesAfterNavigation = destinationCandidatesAfterNavigation
        self.destinationVerified = destinationVerified
        self.atISO8601 = atISO8601
    }
}

public enum FolderChooserDriverError: Error, CustomStringConvertible {
    case panelNotFound
    case goToFolderEntryMissing
    case pathEntryFailed(String)
    case defaultButtonMissing
    case pressFailed(String)
    case destinationMismatch(requested: String, observed: [String])

    public var description: String {
        switch self {
        case .panelNotFound: return "panelNotFound"
        case .goToFolderEntryMissing: return "goToFolderEntryMissing"
        case let .pathEntryFailed(reason): return "pathEntryFailed(\(reason))"
        case .defaultButtonMissing: return "defaultButtonMissing"
        case let .pressFailed(reason): return "pressFailed(\(reason))"
        case let .destinationMismatch(requested, observed):
            return "destinationMismatch(requested=\(requested), observed=\(observed))"
        }
    }
}

public enum FolderChooserDriver {
    /// The panel window: an AX window that contains both a text field and a
    /// default button — calibrated native panel shape.
    public static func panelWindow(pid: pid_t, defaultButtonTitles: [String] = []) -> AXUIElement? {
        let windows = AXDriver.windows(ofApp: pid)
        for window in windows {
            let hasTextField = AXDriver.firstDescendant(of: window, maxDepth: 6) { element in
                AXDriver.role(of: element) == (kAXTextFieldRole as String)
            } != nil
            let hasDefaultButton = defaultButtonElement(in: window, titles: defaultButtonTitles) != nil
            if hasTextField && hasDefaultButton { return window }
        }
        return nil
    }

    public static func defaultButton(pid: pid_t, titles: [String] = []) -> AXUIElement? {
        for window in AXDriver.windows(ofApp: pid) {
            if let button = defaultButtonElement(in: window, titles: titles) {
                return button
            }
        }
        return nil
    }

    private static func defaultButtonElement(in window: AXUIElement, titles: [String]) -> AXUIElement? {
        // maxDepth 12: a native NSOpenPanel presented as a sheet nests the
        // prompt button ~8-10 levels below the host window element, so a
        // shallower search silently reports defaultButtonMissing (observed
        // 2026-09-25: button titled 開啟 at depth >7 in a 144-node tree).
        AXDriver.firstDescendant(of: window, maxDepth: 12, matching: { element in
            guard AXDriver.role(of: element) == (kAXButtonRole as String) else { return false }
            if AXDriver.keyEquivalent(of: element) == "\r" { return true }
            guard !titles.isEmpty else { return false }
            let title = AXDriver.title(of: element) ?? ""
            return titles.contains(title)
        })
    }

    /// Strings the panel currently exposes that look like filesystem paths.
    public static func directoryCandidates(pid: pid_t) -> [String] {
        var candidates: [String] = []
        for window in AXDriver.windows(ofApp: pid) {
            let nodes = AXDriver.allDescendants(of: window, maxDepth: 7) { element in
                let role = AXDriver.role(of: element)
                return role == (kAXPopUpButtonRole as String)
                    || role == (kAXTextFieldRole as String)
                    || role == (kAXWindowRole as String)
            }
            for node in nodes {
                if let value = AXDriver.valueAsString(node), value.contains("/") {
                    candidates.append(value)
                }
                if let title = AXDriver.title(of: node), title.contains("/") {
                    candidates.append(title)
                }
            }
        }
        var seen = Set<String>()
        return candidates.filter { seen.insert($0).inserted }
    }

    /// Posts ⇧⌘G, updates the newly focused path field through AX when it is
    /// settable (otherwise replaces its text with Unicode keyboard events),
    /// verifies the field value, and confirms navigation with Return.
    @discardableResult
    public static func navigateToDestination(
        pid: pid_t,
        destination: URL,
        timeoutSeconds: Double = 8.0
    ) throws -> [String] {
        let target = destination.standardizedFileURL.path
        try QuartzActuator.postGoToFolderChord()
        // Wait for the entry sheet (a new focused text field appears).
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        var pathField: AXUIElement?
        while Date() < deadline {
            if let raw = AXDriver.copyAttribute(AXDriver.appElement(pid: pid), kAXFocusedUIElementAttribute as String),
               CFGetTypeID(raw) == AXUIElementGetTypeID() {
                let focused = raw as! AXUIElement
                if AXDriver.role(of: focused) == (kAXTextFieldRole as String) {
                    pathField = focused
                    break
                }
            }
            usleep(120_000)
        }
        guard let pathField else { throw FolderChooserDriverError.goToFolderEntryMissing }

        var settable = DarwinBoolean(false)
        if AXUIElementIsAttributeSettable(pathField, kAXValueAttribute as CFString, &settable) == .success,
           settable.boolValue {
            _ = AXUIElementSetAttributeValue(pathField, kAXValueAttribute as CFString, target as CFString)
        }

        if AXDriver.valueAsString(pathField) != target {
            // Native panels can prefill this field with the previous folder.
            // Replace it explicitly so the next run's path cannot be appended
            // to stale history.
            try QuartzActuator.postKeyChord(keyCode: 0, flags: [.maskCommand])
            usleep(80_000)
            try QuartzActuator.postUnicodeText(target)
        }

        var pathReflected = false
        while Date() < deadline {
            if AXDriver.valueAsString(pathField) == target {
                pathReflected = true
                break
            }
            usleep(60_000)
        }
        guard pathReflected else {
            throw FolderChooserDriverError.pathEntryFailed("focused AXTextField did not reflect the requested destination")
        }

        try QuartzActuator.postReturnKey()

        // Wait until the panel reports the destination among its path candidates.
        while Date() < deadline {
            let candidates = directoryCandidates(pid: pid)
            if candidates.contains(where: { $0 == target || $0.hasSuffix(target) || target.hasSuffix($0) }) {
                return candidates
            }
            usleep(150_000)
        }
        let observed = directoryCandidates(pid: pid)
        throw FolderChooserDriverError.destinationMismatch(requested: target, observed: observed)
    }

    /// Performs the single chosen confirmation action: `AXPress` on the
    /// unambiguous default button. Returns a description of the pressed button.
    @discardableResult
    public static func pressDefaultButton(pid: pid_t, titles: [String] = []) throws -> String {
        guard let button = defaultButton(pid: pid, titles: titles) else { throw FolderChooserDriverError.defaultButtonMissing }
        let role = AXDriver.role(of: button) ?? "?"
        let title = AXDriver.title(of: button) ?? "?"
        guard AXDriver.press(button) else { throw FolderChooserDriverError.pressFailed("AXPress on \(role) \(title) failed") }
        return "role=\(role) title=\(title)"
    }

    /// Alternative chosen confirmation action (never used together with AXPress).
    public static func confirmWithReturnKey() throws {
        try QuartzActuator.postReturnKey()
    }

    /// Post-confirmation verification: the panel's navigation state must reflect
    /// the destination (checked via AX path candidates) and the caller verifies
    /// the direct filesystem effect separately.
    public static func destinationIsReflected(pid: pid_t, destination: URL) -> Bool {
        let target = destination.standardizedFileURL.path
        return directoryCandidates(pid: pid).contains { $0 == target || $0.hasSuffix(target) || target.hasSuffix($0) }
    }
}
