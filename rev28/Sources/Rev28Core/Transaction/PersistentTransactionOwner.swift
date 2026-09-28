import Foundation

public struct ImmutableRunAuthorization: Equatable, Codable, Sendable {
    public let runID: String
    public let goal: String
    public let group: String
    public let album: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String
    public let stagingRoot: String
    public let stagingRunDirectory: String

    public init(runID: String, goal: String, group: String, album: String, planSHA256: String,
                reviewedImplementationSHA256: String, stagingRoot: URL, stagingRunDirectory: URL) {
        self.runID = runID
        self.goal = goal
        self.group = group
        self.album = album
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        self.stagingRoot = stagingRoot.resolvingSymlinksInPath().standardizedFileURL.path
        self.stagingRunDirectory = stagingRunDirectory.resolvingSymlinksInPath().standardizedFileURL.path
    }

    fileprivate var fields: [String: String] {
        ["runID": runID, "goal": goal, "group": group, "album": album,
         "planSHA256": planSHA256, "reviewedImplementationSHA256": reviewedImplementationSHA256,
         "stagingRoot": stagingRoot, "stagingRunDirectory": stagingRunDirectory]
    }

    fileprivate var isValid: Bool {
        let rootURL = URL(fileURLWithPath: stagingRoot).resolvingSymlinksInPath().standardizedFileURL
        let runURL = URL(fileURLWithPath: stagingRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        let rootType = (try? FileManager.default.attributesOfItem(atPath: rootURL.path)[.type] as? FileAttributeType)
        let runType = (try? FileManager.default.attributesOfItem(atPath: runURL.path)[.type] as? FileAttributeType)
        return !runID.isEmpty && !goal.isEmpty && !group.isEmpty && !album.isEmpty
            && Self.isSHA256(planSHA256) && Self.isSHA256(reviewedImplementationSHA256)
            && rootType == .typeDirectory && runType == .typeDirectory
            && runURL.path != rootURL.path
            && runURL.path.hasPrefix(rootURL.path.hasSuffix("/") ? rootURL.path : rootURL.path + "/")
    }

    private static func isSHA256(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy { $0.isHexDigit }
    }
}

public enum PersistentTransactionError: Error, Equatable, CustomStringConvertible {
    case invalidAuthorization
    case authorizationAlreadyBound
    case authorizationMismatch
    case irreversibleIntentAlreadyRecorded(String)
    case irreversibleAttemptAlreadyRecorded(String)

    public var description: String {
        switch self {
        case .invalidAuthorization: return "invalidAuthorization"
        case .authorizationAlreadyBound: return "authorizationAlreadyBound"
        case .authorizationMismatch: return "authorizationMismatch"
        case let .irreversibleIntentAlreadyRecorded(kind): return "irreversibleIntentAlreadyRecorded(\(kind))"
        case let .irreversibleAttemptAlreadyRecorded(kind): return "irreversibleAttemptAlreadyRecorded(\(kind))"
        }
    }
}

/// Persistent owner for the complete run. All budgets are recomputed from its
/// verified ledger; any intent consumes that irreversible operation forever.
public final class PersistentTransactionOwner {
    public let authorization: ImmutableRunAuthorization
    public let ledger: IntentLedger
    private var saveAllIntentOwnedByThisProcess = false
    private var confirmationIntentOwnedByThisProcess = false
    private let stateLock = NSRecursiveLock()

    public init(authorization: ImmutableRunAuthorization, ledger: IntentLedger) throws {
        guard authorization.isValid else { throw PersistentTransactionError.invalidAuthorization }
        self.authorization = authorization
        self.ledger = ledger
        let bindings = ledger.entries.filter { $0.kind == "transaction.authorization" }
        if let first = bindings.first {
            guard bindings.count == 1, first.payload == authorization.fields else {
                throw PersistentTransactionError.authorizationMismatch
            }
        } else {
            guard ledger.entries.isEmpty else { throw PersistentTransactionError.authorizationAlreadyBound }
            try ledger.append(kind: "transaction.authorization", payload: authorization.fields)
        }
    }

    public var irreversibleOperationCounts: (saveAll: Int, destinationConfirmation: Int) {
        (ledger.entries.filter { $0.kind == "intent.saveAll" || $0.kind == "attempt.saveAll" }.count,
         ledger.entries.filter { $0.kind == "intent.destinationConfirmation" || $0.kind == "attempt.destinationConfirmation" }.count)
    }

    public var reversibleDispatchCount: Int {
        ledger.entries.filter { $0.kind == "dispatch.reversible" }.count
    }

    public func recordReversibleDispatch(action: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard reversibleDispatchCount < 12 else { throw ExecutionPolicyError.reversibleBudgetExhausted }
        try ledger.append(kind: "dispatch.reversible", payload: binding(["action": action]))
    }

    /// Durable intent is written before the caller can post Save All. A restart
    /// sees the intent and cannot reserve or replay this operation.
    public func reserveSaveAll() throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let counts = irreversibleOperationCounts
        guard counts.saveAll == 0 else { throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll") }
        try ledger.append(kind: "intent.saveAll", payload: binding(["risk": "IRREVERSIBLE_SIDE_EFFECT"]))
        saveAllIntentOwnedByThisProcess = true
    }

    /// Must be persisted immediately before event dispatch; a crash afterwards is observe-only.
    public func markSaveAllAttempted() throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard saveAllIntentOwnedByThisProcess,
              ledger.entries.contains(where: { $0.kind == "intent.saveAll" && isBound($0) }),
              irreversibleOperationCounts.saveAll == 1 else {
            throw PersistentTransactionError.irreversibleAttemptAlreadyRecorded("saveAll")
        }
        try ledger.append(kind: "attempt.saveAll", payload: binding([:]))
        saveAllIntentOwnedByThisProcess = false
    }

    public func recordChooserVerified(
        postconditionEvidence: BoundEvidenceDigest,
        tripwireEvidence: BoundEvidenceDigest
    ) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let postconditionArtifact = try postconditionEvidence.decode(PostconditionEvidenceArtifact.self)
        let tripwireArtifact = try tripwireEvidence.decode(TripwireEvidenceArtifact.self)
        guard postconditionEvidence.runID == authorization.runID,
              tripwireEvidence.runID == authorization.runID,
              postconditionArtifact.runID == authorization.runID,
              postconditionArtifact.outcome == "CHOOSER_VERIFIED",
              let affirmation = postconditionArtifact.chooserAffirmation,
              !affirmation.predicateID.isEmpty,
              tripwireArtifact.runID == authorization.runID,
              !tripwireArtifact.preChooserAttributableWriteObserved,
              !tripwireArtifact.observations.contains(where: { $0.aborts }),
              postconditionEvidence.runDirectory.path == URL(fileURLWithPath: authorization.stagingRunDirectory).standardizedFileURL.path,
              tripwireEvidence.runDirectory == postconditionEvidence.runDirectory,
              try BoundEvidenceDigest.load(
                fileURL: postconditionEvidence.fileURL,
                withinRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory),
                runID: authorization.runID
              ).sha256 == postconditionEvidence.sha256,
              try BoundEvidenceDigest.load(
                fileURL: tripwireEvidence.fileURL,
                withinRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory),
                runID: authorization.runID
              ).sha256 == tripwireEvidence.sha256 else {
            throw PersistentTransactionError.authorizationMismatch
        }
        guard ledger.entries.contains(where: { $0.kind == "attempt.saveAll" && isBound($0) }),
              Self.validSHA256(postconditionEvidence.sha256), Self.validSHA256(tripwireEvidence.sha256) else {
            throw PersistentTransactionError.authorizationMismatch
        }
        try ledger.append(kind: "postcondition.chooserVerified", payload: binding([
            "postconditionEvidenceSHA256": postconditionEvidence.sha256,
            "tripwireEvidenceSHA256": tripwireEvidence.sha256,
        ]))
    }

    public func appendSaveAllEmpiricalRecord(_ record: SaveAllEmpiricalClassRecord) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard irreversibleOperationCounts.saveAll == 2,
              ledger.entries.contains(where: { $0.kind == "attempt.saveAll" && isBound($0) }),
              ledger.count(kind: "saveAllEmpiricalClassRecord") == 0,
              record.evidenceRunID == authorization.runID,
              record.evidenceRunDirectory == authorization.stagingRunDirectory else {
            throw PersistentTransactionError.authorizationMismatch
        }
        try record.append(to: ledger)
    }

    public func reserveDestinationConfirmation(action: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let counts = irreversibleOperationCounts
        guard counts.saveAll >= 2, counts.destinationConfirmation == 0,
              ["AXPressDefaultButton", "ReturnKey"].contains(action),
              ledger.entries.contains(where: { $0.kind == "postcondition.chooserVerified" && isBound($0) }) else {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("destinationConfirmation")
        }
        try ledger.append(kind: "intent.destinationConfirmation", payload: binding(["action": action]))
        confirmationIntentOwnedByThisProcess = true
    }

    public func markDestinationConfirmationAttempted() throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard confirmationIntentOwnedByThisProcess,
              ledger.entries.contains(where: { $0.kind == "intent.destinationConfirmation" && isBound($0) }),
              irreversibleOperationCounts.destinationConfirmation == 1,
              !ledger.entries.contains(where: { $0.kind == "attempt.destinationConfirmation" && isBound($0) }) else {
            throw PersistentTransactionError.irreversibleAttemptAlreadyRecorded("destinationConfirmation")
        }
        try ledger.append(kind: "attempt.destinationConfirmation", payload: binding([:]))
        confirmationIntentOwnedByThisProcess = false
    }

    private func binding(_ extra: [String: String]) -> [String: String] {
        authorization.fields.merging(extra) { _, new in new }
    }

    private func isBound(_ entry: LedgerEntry) -> Bool {
        authorization.fields.allSatisfy { entry.payload[$0.key] == $0.value }
    }

    private static func validSHA256(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy(\.isHexDigit) && Set(value).count > 1
    }
}
