import Foundation

// MARK: - Filesystem-tripwire attribution ladder (plan §ARCHITECTURE §10, S-07)
//
// Scope ladder (outermost last): L1 = the unique staging run dir ⊆ L2 = the
// approved root ⊆ L3 = ~/Downloads. Classification is level-specific; only the
// L2 unattributable case fails closed. Carried review note RV-01 (attempt-06):
// the envelope abort item is L2 fail-closed; L3 unattributable activity stays
// non-aborting environmental context.

public enum TripwireLevel: String, Codable, Sendable {
    case l1StagingRunDir
    case l2ApprovedRoot
    case l3OutsideApprovedRoot
}

public enum TripwirePhase: String, Codable, Sendable {
    case preDispatch
    case postDispatch
}

public enum TripwireAttributionOutcome: String, Codable, Sendable {
    /// L1 — the expected primary chooser-effect signal; never aborts.
    case stagingExpectedEvidence
    /// L2 attributable-but-unexpected — non-fatal; disclosed in ledger + report.
    case attributedExternalWriteObserved
    /// L2 unattributable — fail closed, no retry.
    case abortedUnattributedFilesystemWrite
    /// L3 attributable-to-this-run write outside the approved root — scope violation.
    case abortedWriteOutsideApprovedRoot
    /// L3 unattributable activity — environmental context only; does not abort.
    case environmentalContext
    /// Any modification of the accepted baseline — immediate abort regardless of level/attribution.
    case abortedBaselineModified
    /// Pre-dispatch activity is recorded as context and never aborts by itself.
    case preDispatchContext
}

public struct TripwireScope: Equatable, Sendable {
    /// L1: the unique staging run directory (canonicalized).
    public let stagingRunDir: URL
    /// L2: the approved root.
    public let approvedRoot: URL

    public init(stagingRunDir: URL, approvedRoot: URL) {
        self.stagingRunDir = stagingRunDir
        self.approvedRoot = approvedRoot
    }
}

public struct TripwireEvent: Equatable, Sendable {
    public let path: URL
    public let phase: TripwirePhase
    public let attributableToThisRun: Bool
    public let modifiesAcceptedBaseline: Bool
    public let writerPID: Int32?
    public let notes: String

    public init(
        path: URL,
        phase: TripwirePhase,
        attributableToThisRun: Bool,
        modifiesAcceptedBaseline: Bool = false,
        writerPID: Int32? = nil,
        notes: String = ""
    ) {
        self.path = path
        self.phase = phase
        self.attributableToThisRun = attributableToThisRun
        self.modifiesAcceptedBaseline = modifiesAcceptedBaseline
        self.writerPID = writerPID
        self.notes = notes
    }
}

public struct TripwireClassification: Equatable, Codable, Sendable {
    public let level: TripwireLevel
    public let outcome: TripwireAttributionOutcome
    public let aborts: Bool
    public let path: String
    public let rationale: String

    public init(level: TripwireLevel, outcome: TripwireAttributionOutcome, aborts: Bool, path: String, rationale: String) {
        self.level = level
        self.outcome = outcome
        self.aborts = aborts
        self.path = path
        self.rationale = rationale
    }
}

public enum TripwireClassifier {
    private static func isDescendant(_ url: URL, of parent: URL) -> Bool {
        let child = url.standardizedFileURL.path
        let root = parent.standardizedFileURL.path
        if root == "/" { return child.hasPrefix("/") }
        return child == root || child.hasPrefix(root.hasSuffix("/") ? root : root + "/")
    }

    public static func level(for path: URL, scope: TripwireScope) -> TripwireLevel {
        if isDescendant(path, of: scope.stagingRunDir) { return .l1StagingRunDir }
        if isDescendant(path, of: scope.approvedRoot) { return .l2ApprovedRoot }
        return .l3OutsideApprovedRoot
    }

    public static func classify(event: TripwireEvent, scope: TripwireScope) -> TripwireClassification {
        let level = level(for: event.path, scope: scope)
        let pathString = event.path.path

        if event.modifiesAcceptedBaseline {
            return TripwireClassification(
                level: level,
                outcome: .abortedBaselineModified,
                aborts: true,
                path: pathString,
                rationale: "accepted baseline must stay byte-identical; any modification aborts immediately regardless of attribution"
            )
        }
        if event.phase == .preDispatch {
            return TripwireClassification(
                level: level,
                outcome: .preDispatchContext,
                aborts: false,
                path: pathString,
                rationale: "pre-dispatch environmental activity is context (>=10 s baseline) and never aborts by itself"
            )
        }

        switch level {
        case .l1StagingRunDir:
            return TripwireClassification(
                level: level,
                outcome: .stagingExpectedEvidence,
                aborts: false,
                path: pathString,
                rationale: "L1 writes are the expected chooser-effect signal and are evidence"
            )
        case .l2ApprovedRoot:
            if event.attributableToThisRun {
                return TripwireClassification(
                    level: level,
                    outcome: .attributedExternalWriteObserved,
                    aborts: false,
                    path: pathString,
                    rationale: "L2 attributable-but-unexpected write: non-fatal, disclosed as a side-effect observation"
                )
            }
            return TripwireClassification(
                level: level,
                outcome: .abortedUnattributedFilesystemWrite,
                aborts: true,
                path: pathString,
                rationale: "L2 unattributable write inside the approved root fails closed (no retry)"
            )
        case .l3OutsideApprovedRoot:
            if event.attributableToThisRun {
                return TripwireClassification(
                    level: level,
                    outcome: .abortedWriteOutsideApprovedRoot,
                    aborts: true,
                    path: pathString,
                    rationale: "attributable-to-this-run write outside the approved root is a scope violation"
                )
            }
            return TripwireClassification(
                level: level,
                outcome: .environmentalContext,
                aborts: false,
                path: pathString,
                rationale: "L3 unattributable activity is environmental context (concurrent-machine-activity caveat); does not abort"
            )
        }
    }
}
