import AppKit
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

public enum GatedDestinationConfirmation {
    /// Shared production/test boundary for the second irreversible operation.
    /// Intent + attempt are fsynced before dispatch; a post-intent readiness loss
    /// consumes the operation and fails closed instead of retrying.
    public static func perform(
        owner: PersistentTransactionOwner,
        action: String,
        readinessCheck: () -> Bool,
        dispatch: () throws -> Void
    ) throws {
        guard readinessCheck() else {
            throw FolderChooserDriverError.pressFailed("destination confirmation readiness failed before durable intent")
        }
        try owner.reserveDestinationConfirmation(action: action)
        try owner.markDestinationConfirmationAttempted()
        guard readinessCheck() else {
            throw FolderChooserDriverError.pressFailed("destination confirmation readiness changed after durable intent; operation remains consumed")
        }
        try dispatch()
    }
}

public enum FolderChooserDriver {
    /// Per-primitive re-acquisition and accounting boundary for destination
    /// navigation (plan C6). Production always binds the durable owner and the
    /// fresh chooser re-check; a production caller cannot supply a no-op.
    public struct DestinationPrimitiveGuard {
        /// The single AX window that satisfies the predicate's default AND
        /// cancel clauses. Missing or duplicate panels return nil, so the
        /// driver never picks the first matching window.
        public let verifiedPanel: () -> AXUIElement?
        /// Re-acquire chooser identity, process continuity and active/topmost
        /// surface without posting or recording anything.
        public let reacquire: (String) throws -> Void
        /// Re-acquire and durably account the primitive before it is posted.
        public let willPostPrimitive: (String) throws -> Void

        public init(
            verifiedPanel: @escaping () -> AXUIElement?,
            reacquire: @escaping (String) throws -> Void,
            willPostPrimitive: @escaping (String) throws -> Void
        ) {
            self.verifiedPanel = verifiedPanel
            self.reacquire = reacquire
            self.willPostPrimitive = willPostPrimitive
        }
    }

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

    static func defaultButtonElement(in window: AXUIElement, titles: [String]) -> AXUIElement? {
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

    /// Strings one window currently exposes that look like filesystem paths.
    static func directoryCandidates(inWindow window: AXUIElement) -> [String] {
        let nodes = AXDriver.allDescendants(of: window, maxDepth: 7) { element in
            let role = AXDriver.role(of: element)
            return role == (kAXPopUpButtonRole as String)
                || role == (kAXTextFieldRole as String)
                || role == (kAXWindowRole as String)
        }
        var candidates: [String] = []
        for node in nodes {
            if let value = AXDriver.valueAsString(node), value.contains("/") {
                candidates.append(value)
            }
            if let title = AXDriver.title(of: node), title.contains("/") {
                candidates.append(title)
            }
        }
        var seen = Set<String>()
        return candidates.filter { seen.insert($0).inserted }
    }

    /// Strings the app's windows currently expose that look like filesystem
    /// paths (diagnostics/evidence only; decision paths read the unique
    /// verified panel instead).
    static func directoryCandidates(pid: pid_t) -> [String] {
        var seen = Set<String>()
        return AXDriver.windows(ofApp: pid)
            .flatMap { directoryCandidates(inWindow: $0) }
            .filter { seen.insert($0).inserted }
    }

    /// Posts ⇧⌘G, updates the newly focused path field through AX when it is
    /// settable (otherwise replaces its text with Unicode keyboard events),
    /// verifies the field value, and confirms navigation with Return.
    ///
    /// Plan C6: every AX/key primitive is re-acquired and durably accounted
    /// separately through `primitiveGuard`, so a compound navigation cannot
    /// conceal a retry inside one budget record and Return is posted only while
    /// a freshly proved Go-to-folder sheet owns the field of the unique
    /// predicate-verified panel.
    @discardableResult
    static func navigateToDestination(
        pid: pid_t,
        destination: URL,
        primitiveGuard: DestinationPrimitiveGuard,
        timeoutSeconds: Double = 8.0
    ) throws -> [String] {
        let target = destination.standardizedFileURL.path

        // Primitive 1: ⇧⌘G opens the navigation sheet inside the verified panel.
        try primitiveGuard.willPostPrimitive("chooser.navigate.goToFolderChord")
        try QuartzActuator.postGoToFolderChord()

        // Wait for the entry sheet: the focused element must be a text field of
        // the unique verified panel, never "any focused text field".
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        var pathField: AXUIElement?
        while Date() < deadline {
            if let field = focusedPathFieldInVerifiedPanel(pid: pid, primitiveGuard: primitiveGuard) {
                pathField = field
                break
            }
            usleep(120_000)
        }
        guard let pathField else { throw FolderChooserDriverError.goToFolderEntryMissing }

        // The AX value write posts no events but is still an input primitive:
        // re-acquire the chooser identity and field ownership first.
        try primitiveGuard.reacquire("chooser.navigate.setPathFieldValue")
        guard fieldIsOwned(pid: pid, field: pathField, primitiveGuard: primitiveGuard) else {
            throw FolderChooserDriverError.pathEntryFailed("focused path field ownership lost before the AX value write")
        }
        var settable = DarwinBoolean(false)
        if AXUIElementIsAttributeSettable(pathField, kAXValueAttribute as CFString, &settable) == .success,
           settable.boolValue {
            // Plan C6/C6-primitives: the AX value write posts no OS event but
            // is still an input primitive, so it is re-acquired and durably
            // accounted under its reviewed semantic action name before the
            // write. A non-settable field writes nothing and is never recorded.
            try primitiveGuard.willPostPrimitive("chooser.navigate.setPathFieldValue")
            _ = AXUIElementSetAttributeValue(pathField, kAXValueAttribute as CFString, target as CFString)
        }

        if AXDriver.valueAsString(pathField) != target {
            // Native panels can prefill this field with the previous folder.
            // Replace it explicitly so the next run's path cannot be appended
            // to stale history.
            try postKeyPrimitive(
                "chooser.navigate.clearField",
                pid: pid,
                field: pathField,
                primitiveGuard: primitiveGuard,
                post: { try QuartzActuator.postKeyChord(keyCode: 0, flags: [.maskCommand]) }
            )
            usleep(80_000)
            try postKeyPrimitive(
                "chooser.navigate.enterPathText",
                pid: pid,
                field: pathField,
                primitiveGuard: primitiveGuard,
                post: { try QuartzActuator.postUnicodeText(target) }
            )
        }

        var pathReflected = false
        while Date() < deadline {
            if fieldIsOwned(pid: pid, field: pathField, primitiveGuard: primitiveGuard),
               AXDriver.valueAsString(pathField) == target {
                pathReflected = true
                break
            }
            usleep(60_000)
        }
        guard pathReflected else {
            throw FolderChooserDriverError.pathEntryFailed("focused AXTextField did not reflect the requested destination")
        }

        // Return is navigation only while the freshly proved sheet still owns
        // the verified field and the exact target value is reflected.
        guard AXDriver.valueAsString(pathField) == target else {
            throw FolderChooserDriverError.pathEntryFailed("path field no longer reflects the destination; Return refused")
        }
        try postKeyPrimitive(
            "chooser.navigate.returnKey",
            pid: pid,
            field: pathField,
            primitiveGuard: primitiveGuard,
            post: { try QuartzActuator.postReturnKey() }
        )

        // Wait until the unique verified panel reports the destination among
        // its own path candidates (never a union over all app windows).
        while Date() < deadline {
            if let panel = primitiveGuard.verifiedPanel() {
                let candidates = directoryCandidates(inWindow: panel)
                if candidates.contains(where: { URL(fileURLWithPath: $0).standardizedFileURL.path == target }) {
                    return candidates
                }
            }
            usleep(150_000)
        }
        let observed = primitiveGuard.verifiedPanel().map(directoryCandidates(inWindow:)) ?? []
        throw FolderChooserDriverError.destinationMismatch(requested: target, observed: observed)
    }

    /// One key primitive: re-acquire chooser identity/process/surface and
    /// durably account it, then prove the focused field is still the verified
    /// panel's field, then post exactly once (no concealed retry).
    private static func postKeyPrimitive(
        _ action: String,
        pid: pid_t,
        field: AXUIElement,
        primitiveGuard: DestinationPrimitiveGuard,
        post: () throws -> Void
    ) throws {
        try primitiveGuard.willPostPrimitive(action)
        guard fieldIsOwned(pid: pid, field: field, primitiveGuard: primitiveGuard) else {
            throw FolderChooserDriverError.pathEntryFailed("focused field ownership lost before \(action)")
        }
        try post()
    }

    /// The focused element must be a text field that belongs to (or is) the
    /// unique predicate-verified panel window.
    static func focusedPathFieldInVerifiedPanel(
        pid: pid_t,
        primitiveGuard: DestinationPrimitiveGuard
    ) -> AXUIElement? {
        guard let focused = focusedElement(pid: pid),
              AXDriver.role(of: focused) == (kAXTextFieldRole as String) else { return nil }
        guard fieldIsOwned(pid: pid, field: focused, primitiveGuard: primitiveGuard) else { return nil }
        return focused
    }

    static func focusedElement(pid: pid_t) -> AXUIElement? {
        guard let raw = AXDriver.copyAttribute(AXDriver.appElement(pid: pid), kAXFocusedUIElementAttribute as String),
              CFGetTypeID(raw) == AXUIElementGetTypeID() else { return nil }
        return (raw as! AXUIElement)
    }

    /// The focused field is the exact element handed out earlier and it still
    /// belongs to the currently verified unique panel.
    private static func fieldIsOwned(
        pid: pid_t,
        field: AXUIElement,
        primitiveGuard: DestinationPrimitiveGuard
    ) -> Bool {
        guard let panel = primitiveGuard.verifiedPanel(),
              let focused = focusedElement(pid: pid),
              AXDriver.role(of: focused) == (kAXTextFieldRole as String),
              CFEqual(focused, field) else { return false }
        return CFEqual(focused, panel) || AXDriver.isDescendant(focused, of: panel)
    }


    /// Production reversible destination preparation. The caller must supply the
    /// exact chooser candidate that was affirmatively observed; this method
    /// revalidates process instance, production predicate and foreground state
    /// before and after navigation. It never performs the final confirmation.
    public static func prepareDestination(
        pid: pid_t,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        owner: PersistentTransactionOwner,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> [String] {
        func chooserIsFresh() -> Bool {
            guard candidate.owner.pid == expectedProcess.pid,
                  predicate.predicateVersion >= ChooserAffirmationEvaluator.processStableButtonSemanticsVersion,
                  ChooserAffirmationEvaluator.evaluateProduction(candidate: candidate, predicate: predicate) == .affirmed,
                  let process = ProcessInstanceID.current(pid: Int32(pid)),
                  process == expectedProcess,
                  let app = NSRunningApplication(processIdentifier: pid),
                  app.isActive,
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                return false
            }
            return true
        }
        guard chooserIsFresh() else {
            throw FolderChooserDriverError.pathEntryFailed("chooser is not freshly bound before destination preparation")
        }
        // Plan C6: per-primitive re-acquisition + durable accounting. Every
        // primitive is recorded separately under its reviewed semantic action
        // name (⇧⌘G chord, ⌘A select-all, text entry, Return); a compound
        // retry therefore consumes the per-blocker ceiling visibly instead of
        // hiding inside one `chooser.prepareDestination` record.
        let primitiveGuard = DestinationPrimitiveGuard(
            verifiedPanel: { verifiedPanelWindow(pid: pid, predicate: predicate) },
            reacquire: { action in
                guard chooserIsFresh() else {
                    throw FolderChooserDriverError.pathEntryFailed("chooser identity failed re-acquisition before \(action)")
                }
            },
            willPostPrimitive: { action in
                guard chooserIsFresh() else {
                    throw FolderChooserDriverError.pathEntryFailed("chooser identity failed re-acquisition before \(action)")
                }
                try owner.recordReversibleDispatch(action: action)
            }
        )
        let observed = try navigateToDestination(
            pid: pid,
            destination: destination,
            primitiveGuard: primitiveGuard
        )
        guard chooserIsFresh(),
              destinationIsReflected(pid: pid, destination: destination, predicate: predicate) else {
            throw FolderChooserDriverError.destinationMismatch(
                requested: destination.standardizedFileURL.path,
                observed: observed
            )
        }
        return observed
    }

    /// Performs the single chosen confirmation action: `AXPress` on the
    /// unambiguous default button. Returns a description of the pressed button.
    @discardableResult
    static func pressDefaultButton(pid: pid_t, titles: [String] = []) throws -> String {
        guard let button = defaultButton(pid: pid, titles: titles) else { throw FolderChooserDriverError.defaultButtonMissing }
        let role = AXDriver.role(of: button) ?? "?"
        let title = AXDriver.title(of: button) ?? "?"
        guard AXDriver.press(button) else { throw FolderChooserDriverError.pressFailed("AXPress on \(role) \(title) failed") }
        return "role=\(role) title=\(title)"
    }

    /// Alternative chosen confirmation action (never used together with AXPress).
    static func confirmWithReturnKey() throws {
        try QuartzActuator.postReturnKey()
    }

    /// Durable, exactly-once production confirmation path. The intent and
    /// attempted action are persisted before AXPress, so an unknown result on
    /// restart cannot be repeated.
    public static func confirmDefaultButton(
        pid: pid_t,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        owner: PersistentTransactionOwner,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String {
        guard candidate.owner.pid == expectedProcess.pid,
              predicate.predicateVersion >= ChooserAffirmationEvaluator.processStableButtonSemanticsVersion,
              predicate.ax.defaultButton != nil, predicate.ax.cancelButton != nil,
              ChooserAffirmationEvaluator.evaluateProduction(candidate: candidate, predicate: predicate) == .affirmed else {
            throw FolderChooserDriverError.pressFailed("chooser does not satisfy production predicate version and process binding")
        }
        func targetIsForegroundAndStable() -> Bool {
            guard let process = ProcessInstanceID.current(pid: Int32(pid)),
                  let runningApplication = NSRunningApplication(processIdentifier: pid),
                  runningApplication.bundleIdentifier == candidate.owner.bundleID,
                  candidate.owner.startTimeUnix == Double(process.startTimeSeconds) + Double(process.startTimeMicroseconds) / 1_000_000.0,
                  process == expectedProcess,
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
                  runningApplication.isActive,
                  destinationIsReflected(pid: pid, destination: destination, predicate: predicate),
                  freshVerifiedDefaultButton(pid: pid, predicate: predicate) != nil else { return false }
            return true
        }
        var pressedTitle = "?"
        try GatedDestinationConfirmation.perform(
            owner: owner,
            action: "AXPressDefaultButton",
            readinessCheck: targetIsForegroundAndStable,
            dispatch: {
                guard let button = freshVerifiedDefaultButton(pid: pid, predicate: predicate) else {
                    throw FolderChooserDriverError.defaultButtonMissing
                }
                pressedTitle = AXDriver.title(of: button) ?? "?"
                guard AXDriver.press(button) else {
                    throw FolderChooserDriverError.pressFailed("AXPress on verified default button failed")
                }
            }
        )
        return "role=AXButton title=\(pressedTitle)"
    }

    private static func freshVerifiedDefaultButton(
        pid: pid_t,
        predicate: ChooserAffirmationPredicate
    ) -> AXUIElement? {
        guard let defaultRequirement = predicate.ax.defaultButton,
              let window = verifiedPanelWindow(pid: pid, predicate: predicate) else { return nil }
        return AXDriver.firstDescendant(of: window, maxDepth: 12, matching: { element in
            Self.matches(requirement: defaultRequirement, element: element)
        })
    }

    /// The unique panel window for the bound predicate: exactly one AX window
    /// whose dump satisfies both the default and cancel button clauses.
    /// Duplicate or missing panels return nil (never the first match).
    static func verifiedPanelWindow(
        pid: pid_t,
        predicate: ChooserAffirmationPredicate
    ) -> AXUIElement? {
        guard let defaultRequirement = predicate.ax.defaultButton,
              let cancelRequirement = predicate.ax.cancelButton else { return nil }
        let panels = AXDriver.windows(ofApp: pid).filter { window in
            let dump = AXDriver.dump(element: window, pid: Int32(pid), maxDepth: 12)
            return ChooserAffirmationEvaluator.matches(requirement: defaultRequirement, nodes: dump.nodes)
                && ChooserAffirmationEvaluator.matches(requirement: cancelRequirement, nodes: dump.nodes)
        }
        guard panels.count == 1 else { return nil }
        return panels[0]
    }

    private static func matches(requirement: ButtonRequirement, element: AXUIElement) -> Bool {
        guard let role = AXDriver.role(of: element), requirement.buttonRoles.contains(role) else { return false }
        switch requirement.mode {
        case .attributeEquals:
            guard let name = requirement.attributeName, let expected = requirement.attributeValue else { return false }
            return AXDriver.stringAttribute(element, name) == expected
                || (name == "AXKeyEquivalent" && AXDriver.keyEquivalent(of: element) == expected)
        case .titleIn:
            let title = AXDriver.title(of: element) ?? AXDriver.descriptionOf(of: element) ?? ""
            return requirement.titles.contains(title)
        }
    }

    /// Post-confirmation verification: the unique verified panel's own
    /// navigation state must reflect the destination (checked via that panel's
    /// AX path candidates, never a union over all app windows); the caller
    /// verifies the direct filesystem effect separately.
    static func destinationIsReflected(
        pid: pid_t,
        destination: URL,
        predicate: ChooserAffirmationPredicate
    ) -> Bool {
        guard let panel = verifiedPanelWindow(pid: pid, predicate: predicate) else { return false }
        let target = destination.standardizedFileURL.path
        return directoryCandidates(inWindow: panel).contains {
            URL(fileURLWithPath: $0).standardizedFileURL.path == target
        }
    }
}
