import CoreGraphics
import Foundation

// MARK: - Frozen chooser-affirmation predicate (plan §ARCHITECTURE §11, S-06)
//
// The predicate is calibrated in W2 against a real NSOpenPanel on this macOS
// version; the resolved hosting shape is recorded in the frozen review set. An
// empty/indeterminate pre-dispatch census WIDENS refusal (no benefit of the
// doubt); it never relaxes the predicate. Ambiguity or a predicate mismatch is
// reported as `frozenPredicateMismatch` and must not trigger ad-hoc loosening.

/// One calibrated button requirement (the real panel's default / cancel button,
/// matched either by an exact AX attribute value discovered during calibration
/// or by observed titles when no such attribute is exposed on this macOS build).
public struct ButtonRequirement: Equatable, Codable, Sendable {
    public enum Mode: String, Codable, Sendable {
        case attributeEquals
        case titleIn
    }

    public var mode: Mode
    public var attributeName: String?
    public var attributeValue: String?
    public var titles: [String]
    public var buttonRoles: [String]

    public init(mode: Mode, attributeName: String?, attributeValue: String?, titles: [String], buttonRoles: [String]) {
        self.mode = mode
        self.attributeName = attributeName
        self.attributeValue = attributeValue
        self.titles = titles
        self.buttonRoles = buttonRoles
    }
}

public struct ChooserAXClauseSet: Equatable, Codable, Sendable {
    /// Top-level window role the candidate must expose (calibrated: AXWindow).
    public var windowRole: String
    /// Allowed top-level subroles (calibrated from the real NSOpenPanel).
    public var allowedSubroles: [String]
    public var requiresTextField: Bool
    public var textFieldRoles: [String]
    public var requiresPopUpButton: Bool
    public var popUpButtonRoles: [String]
    public var defaultButton: ButtonRequirement?
    public var cancelButton: ButtonRequirement?
    public var requiresPathAffordance: Bool
    public var pathAffordanceRoles: [String]
    /// Empty means the path affordance is matched by role only (titles were
    /// localized/unstable in calibration); non-empty means any-of title matching.
    public var pathAffordanceTitles: [String]

    public init(
        windowRole: String,
        allowedSubroles: [String],
        requiresTextField: Bool,
        textFieldRoles: [String],
        requiresPopUpButton: Bool,
        popUpButtonRoles: [String],
        defaultButton: ButtonRequirement?,
        cancelButton: ButtonRequirement?,
        requiresPathAffordance: Bool,
        pathAffordanceRoles: [String],
        pathAffordanceTitles: [String]
    ) {
        self.windowRole = windowRole
        self.allowedSubroles = allowedSubroles
        self.requiresTextField = requiresTextField
        self.textFieldRoles = textFieldRoles
        self.requiresPopUpButton = requiresPopUpButton
        self.popUpButtonRoles = popUpButtonRoles
        self.defaultButton = defaultButton
        self.cancelButton = cancelButton
        self.requiresPathAffordance = requiresPathAffordance
        self.pathAffordanceRoles = pathAffordanceRoles
        self.pathAffordanceTitles = pathAffordanceTitles
    }
}

public struct ChooserOwnershipClauseSet: Equatable, Codable, Sendable {
    /// Owning pid must belong to the freshly established panel-process set:
    /// union of the pre-dispatch and post-dispatch censuses.
    public var requiresOwningPIDInCensusUnion: Bool
    public var requiresStableProcessInstance: Bool
    public var emptyPreCensusWidensRefusal: Bool

    public init(
        requiresOwningPIDInCensusUnion: Bool,
        requiresStableProcessInstance: Bool,
        emptyPreCensusWidensRefusal: Bool
    ) {
        self.requiresOwningPIDInCensusUnion = requiresOwningPIDInCensusUnion
        self.requiresStableProcessInstance = requiresStableProcessInstance
        self.emptyPreCensusWidensRefusal = emptyPreCensusWidensRefusal
    }
}

public struct ChooserAffirmationPredicate: Equatable, Codable, Sendable {
    public let predicateID: String
    public let frozenAtISO8601: String
    public let calibratedAgainst: String
    public var ax: ChooserAXClauseSet
    public var ownership: ChooserOwnershipClauseSet

    public init(
        predicateID: String,
        frozenAtISO8601: String,
        calibratedAgainst: String,
        ax: ChooserAXClauseSet,
        ownership: ChooserOwnershipClauseSet
    ) {
        self.predicateID = predicateID
        self.frozenAtISO8601 = frozenAtISO8601
        self.calibratedAgainst = calibratedAgainst
        self.ax = ax
        self.ownership = ownership
    }
}

public struct ChooserProcessFacts: Equatable, Codable, Sendable {
    public let pid: Int32
    public let bundleID: String?
    public let signingIdentity: String?
    public let startTimeUnix: Double?

    public init(pid: Int32, bundleID: String?, signingIdentity: String?, startTimeUnix: Double?) {
        self.pid = pid
        self.bundleID = bundleID
        self.signingIdentity = signingIdentity
        self.startTimeUnix = startTimeUnix
    }
}

public struct ChooserCandidate: Sendable {
    public let windowID: UInt32
    public let frame: CGRect
    public let onScreen: Bool
    public let presentInSCInventory: Bool
    public let presentInCGInventory: Bool
    public let isNewRelativeToPreDispatchInventory: Bool
    public let owner: ChooserProcessFacts
    public let pidReuseDetected: Bool
    /// Flattened AX dump of the candidate window subtree.
    public let axNodes: [AXNodeDump]
    public let preDispatchCensusPIDs: [Int32]
    public let postDispatchCensusPIDs: [Int32]

    public init(
        windowID: UInt32,
        frame: CGRect,
        onScreen: Bool,
        presentInSCInventory: Bool,
        presentInCGInventory: Bool,
        isNewRelativeToPreDispatchInventory: Bool,
        owner: ChooserProcessFacts,
        pidReuseDetected: Bool,
        axNodes: [AXNodeDump],
        preDispatchCensusPIDs: [Int32],
        postDispatchCensusPIDs: [Int32]
    ) {
        self.windowID = windowID
        self.frame = frame
        self.onScreen = onScreen
        self.presentInSCInventory = presentInSCInventory
        self.presentInCGInventory = presentInCGInventory
        self.isNewRelativeToPreDispatchInventory = isNewRelativeToPreDispatchInventory
        self.owner = owner
        self.pidReuseDetected = pidReuseDetected
        self.axNodes = axNodes
        self.preDispatchCensusPIDs = preDispatchCensusPIDs
        self.postDispatchCensusPIDs = postDispatchCensusPIDs
    }
}

public enum ChooserRefusalCause: String, Codable, Sendable {
    case notNewWindow
    case notOnScreen
    case notInInventories
    case ownershipUnbound
    case pidReuse
    case frozenPredicateMismatch
}

public enum ChooserPredicateVerdict: Equatable, Sendable {
    case affirmed
    case refused(cause: ChooserRefusalCause, detail: String)
}

public enum ChooserAffirmationEvaluator {
    public static func evaluate(candidate: ChooserCandidate, predicate: ChooserAffirmationPredicate) -> ChooserPredicateVerdict {
        // Clause 1: new relative to the pre-dispatch inventory, on-screen, in both inventories.
        guard candidate.isNewRelativeToPreDispatchInventory else {
            return .refused(cause: .notNewWindow, detail: "candidate window is not new relative to the pre-dispatch inventory")
        }
        guard candidate.onScreen else {
            return .refused(cause: .notOnScreen, detail: "candidate window is not on-screen")
        }
        guard candidate.presentInSCInventory, candidate.presentInCGInventory else {
            return .refused(cause: .notInInventories, detail: "candidate missing from fresh SC and/or CG inventories")
        }

        // Clause 2: AX surface matches native open/save-panel semantics.
        if let mismatch = axSurfaceMismatch(candidate: candidate, clauses: predicate.ax) {
            return .refused(cause: .frozenPredicateMismatch, detail: mismatch)
        }

        // Clause 3: ownership binding.
        let censusUnion = Set(candidate.preDispatchCensusPIDs).union(candidate.postDispatchCensusPIDs)
        if predicate.ownership.requiresOwningPIDInCensusUnion, !censusUnion.contains(candidate.owner.pid) {
            return .refused(
                cause: .ownershipUnbound,
                detail: "owning pid \(candidate.owner.pid) not in pre/post panel-process census union \(censusUnion.sorted())"
            )
        }
        if predicate.ownership.requiresStableProcessInstance {
            if candidate.pidReuseDetected {
                return .refused(cause: .pidReuse, detail: "pid reuse detected for owning process")
            }
            if candidate.owner.startTimeUnix == nil || (candidate.owner.bundleID == nil && candidate.owner.signingIdentity == nil) {
                return .refused(
                    cause: .ownershipUnbound,
                    detail: "process instance not authenticated (missing start time and/or bundle/signing identity)"
                )
            }
        }
        let preCensusEmpty = candidate.preDispatchCensusPIDs.isEmpty
        if preCensusEmpty, predicate.ownership.emptyPreCensusWidensRefusal {
            // Widened refusal: with no pre-dispatch census the ownership evidence is
            // strictly weaker, so any residual ambiguity must be refused. We require
            // the strict (subrole-bound) surface match and authenticated instance.
            if let mismatch = strictSubroleMismatch(candidate: candidate, clauses: predicate.ax) {
                return .refused(
                    cause: .frozenPredicateMismatch,
                    detail: "empty pre-dispatch census widens refusal: \(mismatch)"
                )
            }
            if candidate.owner.startTimeUnix == nil {
                return .refused(
                    cause: .ownershipUnbound,
                    detail: "empty pre-dispatch census widens refusal: process instance start time unavailable"
                )
            }
        }
        return .affirmed
    }

    private static func axSurfaceMismatch(candidate: ChooserCandidate, clauses: ChooserAXClauseSet) -> String? {
        var failure: String?
        let windowNodes = candidate.axNodes.filter { $0.role == clauses.windowRole }
        guard !windowNodes.isEmpty else {
            return "no AX node with role \(clauses.windowRole) in candidate subtree"
        }
        let subroleNodes = windowNodes.filter { node in
            guard let subrole = node.subrole else { return false }
            return clauses.allowedSubroles.contains(subrole)
        }
        if subroleNodes.isEmpty {
            let observed = windowNodes.compactMap { $0.subrole }.sorted()
            return "no window subrole inside calibrated set \(clauses.allowedSubroles); observed \(observed)"
        }
        let nodes = candidate.axNodes
        if clauses.requiresTextField, !nodes.contains(where: { node in
            node.role.map { clauses.textFieldRoles.contains($0) } ?? false
        }) {
            return "no AX node with text-field role \(clauses.textFieldRoles)"
        }
        if clauses.requiresPopUpButton, !nodes.contains(where: { node in
            node.role.map { clauses.popUpButtonRoles.contains($0) } ?? false
        }) {
            return "no AX node with pop-up-button role \(clauses.popUpButtonRoles)"
        }
        if let requirement = clauses.defaultButton, !matches(requirement: requirement, nodes: nodes) {
            failure = "no default button matching calibrated requirement \(requirement)"
        }
        if let requirement = clauses.cancelButton, !matches(requirement: requirement, nodes: nodes) {
            failure = failure ?? "no cancel button matching calibrated requirement \(requirement)"
        }
        if clauses.requiresPathAffordance {
            let pathMatches = nodes.filter { node in
                guard let role = node.role, clauses.pathAffordanceRoles.contains(role) else { return false }
                if clauses.pathAffordanceTitles.isEmpty { return true }
                let title = node.title ?? node.description ?? ""
                return clauses.pathAffordanceTitles.contains(title)
            }
            if pathMatches.isEmpty {
                failure = failure ?? "no path affordance node (roles \(clauses.pathAffordanceRoles), titles \(clauses.pathAffordanceTitles))"
            }
        }
        return failure
    }

    public static func matches(requirement: ButtonRequirement, nodes: [AXNodeDump]) -> Bool {
        nodes.contains { node in
            guard let role = node.role, requirement.buttonRoles.contains(role) else { return false }
            switch requirement.mode {
            case .attributeEquals:
                guard let name = requirement.attributeName, let value = requirement.attributeValue else { return false }
                return node.attributes[name] == value
                    || (name == "AXKeyEquivalent" && node.keyEquivalent == value)
            case .titleIn:
                let title = node.title ?? node.description ?? ""
                return requirement.titles.contains(title)
            }
        }
    }

    private static func strictSubroleMismatch(candidate: ChooserCandidate, clauses: ChooserAXClauseSet) -> String? {
        let strictNodes = candidate.axNodes.filter { node in
            node.role == clauses.windowRole && node.subrole != nil && clauses.allowedSubroles.contains(node.subrole!)
        }
        guard !strictNodes.isEmpty else {
            return "candidate exposes no window node with a calibrated subrole"
        }
        return axSurfaceMismatch(candidate: candidate, clauses: clauses)
    }
}
