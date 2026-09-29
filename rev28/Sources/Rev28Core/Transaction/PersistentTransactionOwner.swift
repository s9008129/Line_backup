import Foundation

public struct ImmutableRunAuthorization: Equatable, Codable, Sendable {
    public static let acceptedBaselineTripwireSHA256 = "b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd"

    public let runID: String
    public let goal: String
    public let group: String
    public let album: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String
    public let stagingRoot: String
    public let stagingRunDirectory: String
    public let evidenceRunDirectory: String
    public let expectedFileCount: Int
    public let expectedTotalBytes: UInt64
    public let expectedContentMultisetSHA256: String
    public let baselineTripwireSHA256: String

    public init(
        runID: String,
        goal: String,
        group: String,
        album: String,
        planSHA256: String,
        reviewedImplementationSHA256: String,
        stagingRoot: URL,
        stagingRunDirectory: URL,
        evidenceRunDirectory: URL? = nil,
        expectedFileCount: Int = StagingPolicy.rev28Accepted.expectedFileCount,
        expectedTotalBytes: UInt64 = StagingPolicy.rev28Accepted.expectedTotalBytes,
        expectedContentMultisetSHA256: String = StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
        baselineTripwireSHA256: String = ImmutableRunAuthorization.acceptedBaselineTripwireSHA256
    ) {
        self.runID = runID
        self.goal = goal
        self.group = group
        self.album = album
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        let canonicalRoot = stagingRoot.resolvingSymlinksInPath().standardizedFileURL
        let canonicalRun = stagingRunDirectory.resolvingSymlinksInPath().standardizedFileURL
        let defaultEvidence = canonicalRoot.deletingLastPathComponent()
            .appendingPathComponent("evidence", isDirectory: true)
            .appendingPathComponent(runID, isDirectory: true)
        self.stagingRoot = canonicalRoot.path
        self.stagingRunDirectory = canonicalRun.path
        self.evidenceRunDirectory = (evidenceRunDirectory ?? defaultEvidence)
            .resolvingSymlinksInPath().standardizedFileURL.path
        self.expectedFileCount = expectedFileCount
        self.expectedTotalBytes = expectedTotalBytes
        self.expectedContentMultisetSHA256 = expectedContentMultisetSHA256
        self.baselineTripwireSHA256 = baselineTripwireSHA256
    }

    fileprivate var fields: [String: String] {
        [
            "runID": runID,
            "goal": goal,
            "group": group,
            "album": album,
            "planSHA256": planSHA256,
            "reviewedImplementationSHA256": reviewedImplementationSHA256,
            "stagingRoot": stagingRoot,
            "stagingRunDirectory": stagingRunDirectory,
            "evidenceRunDirectory": evidenceRunDirectory,
            "expectedFileCount": String(expectedFileCount),
            "expectedTotalBytes": String(expectedTotalBytes),
            "expectedContentMultisetSHA256": expectedContentMultisetSHA256,
            "baselineTripwireSHA256": baselineTripwireSHA256,
        ]
    }

    fileprivate var isValid: Bool {
        let rootURL = URL(fileURLWithPath: stagingRoot).resolvingSymlinksInPath().standardizedFileURL
        let runURL = URL(fileURLWithPath: stagingRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        let evidenceURL = URL(fileURLWithPath: evidenceRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        let rootType = (try? FileManager.default.attributesOfItem(atPath: rootURL.path)[.type] as? FileAttributeType)
        let runType = (try? FileManager.default.attributesOfItem(atPath: runURL.path)[.type] as? FileAttributeType)
        let runPrefix = runURL.path.hasSuffix("/") ? runURL.path : runURL.path + "/"
        let evidencePrefix = evidenceURL.path.hasSuffix("/") ? evidenceURL.path : evidenceURL.path + "/"
        return !runID.isEmpty && !goal.isEmpty && !group.isEmpty && !album.isEmpty
            && Self.isSHA256(planSHA256) && Self.isSHA256(reviewedImplementationSHA256)
            && expectedFileCount == StagingPolicy.rev28Accepted.expectedFileCount
            && expectedTotalBytes == StagingPolicy.rev28Accepted.expectedTotalBytes
            && expectedContentMultisetSHA256 == StagingPolicy.rev28Accepted.expectedContentMultisetSHA256
            && baselineTripwireSHA256 == Self.acceptedBaselineTripwireSHA256
            && rootType == .typeDirectory && runType == .typeDirectory
            && runURL.path != rootURL.path
            && runURL.path.hasPrefix(rootURL.path.hasSuffix("/") ? rootURL.path : rootURL.path + "/")
            && evidenceURL.path != runURL.path
            && !evidenceURL.path.hasPrefix(runPrefix)
            && !runURL.path.hasPrefix(evidencePrefix)
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
    case goalSlotEntitlementConsumed(String)
    case ledgerCheckpointRequired
    case ledgerCheckpointInvalid
    case stateAlreadyInitialized
    case stateNotInitialized
    case invalidStateEvidence

    public var description: String {
        switch self {
        case .invalidAuthorization: return "invalidAuthorization"
        case .authorizationAlreadyBound: return "authorizationAlreadyBound"
        case .authorizationMismatch: return "authorizationMismatch"
        case let .irreversibleIntentAlreadyRecorded(kind): return "irreversibleIntentAlreadyRecorded(\(kind))"
        case let .irreversibleAttemptAlreadyRecorded(kind): return "irreversibleAttemptAlreadyRecorded(\(kind))"
        case let .goalSlotEntitlementConsumed(detail): return "goalSlotEntitlementConsumed(\(detail))"
        case .ledgerCheckpointRequired: return "ledgerCheckpointRequired"
        case .ledgerCheckpointInvalid: return "ledgerCheckpointInvalid"
        case .stateAlreadyInitialized: return "stateAlreadyInitialized"
        case .stateNotInitialized: return "stateNotInitialized"
        case .invalidStateEvidence: return "invalidStateEvidence"
        }
    }
}

/// Persistent owner for the complete run. All budgets are recomputed from its
/// verified ledger; any intent consumes that irreversible operation forever.
public final class PersistentTransactionOwner {
    public let authorization: ImmutableRunAuthorization
    public let ledger: IntentLedger
    /// Production compositions pass the persistent goal slot so the one-shot
    /// irreversible entitlement cannot be reset by a new ledger/runID/session.
    public let goalSlot: GoalSlot?
    private var saveAllIntentOwnedByThisProcess = false
    private var confirmationIntentOwnedByThisProcess = false
    private let stateLock = NSRecursiveLock()
    private let checkpointURL: URL?
    public let isObserveOnlyResume: Bool

    public init(
        authorization: ImmutableRunAuthorization,
        ledger: IntentLedger,
        checkpointURL: URL? = nil,
        requireCheckpointOnResume: Bool = false,
        goalSlot: GoalSlot? = nil
    ) throws {
        guard authorization.isValid else { throw PersistentTransactionError.invalidAuthorization }
        self.authorization = authorization
        self.ledger = ledger
        if let goalSlot, !goalSlot.identity.matches(authorization) {
            throw PersistentTransactionError.authorizationMismatch
        }
        self.goalSlot = goalSlot
        self.checkpointURL = checkpointURL?.standardizedFileURL
        self.isObserveOnlyResume = ledger.entries.contains { Self.isIrreversibleRecord($0.kind) }
        try EvidenceIO.ensureDirectory(URL(fileURLWithPath: authorization.evidenceRunDirectory))

        if !ledger.entries.isEmpty {
            guard let checkpointURL = self.checkpointURL else {
                if requireCheckpointOnResume { throw PersistentTransactionError.ledgerCheckpointRequired }
                let bindings = ledger.entries.filter { $0.kind == "transaction.authorization" }
                guard bindings.count == 1, bindings.first?.payload == authorization.fields else {
                    throw PersistentTransactionError.authorizationMismatch
                }
                return
            }
            guard FileManager.default.fileExists(atPath: checkpointURL.path) else {
                if requireCheckpointOnResume { throw PersistentTransactionError.ledgerCheckpointRequired }
                let bindings = ledger.entries.filter { $0.kind == "transaction.authorization" }
                guard bindings.count == 1, bindings.first?.payload == authorization.fields else {
                    throw PersistentTransactionError.authorizationMismatch
                }
                try checkpoint()
                return
            }
            do {
                _ = try IntentLedger.verifyHeadAnchor(fileURL: ledger.fileURL, anchorURL: checkpointURL)
            } catch {
                throw PersistentTransactionError.ledgerCheckpointInvalid
            }
        }

        let bindings = ledger.entries.filter { $0.kind == "transaction.authorization" }
        if let first = bindings.first {
            guard bindings.count == 1, first.payload == authorization.fields else {
                throw PersistentTransactionError.authorizationMismatch
            }
        } else {
            guard ledger.entries.isEmpty else { throw PersistentTransactionError.authorizationAlreadyBound }
            try append(kind: "transaction.authorization", payload: authorization.fields)
        }
    }


    public var currentState: ExecutionState? {
        ledger.entries.reversed().first(where: { $0.kind == "state.transition" })
            .flatMap { $0.payload["to"] }
            .flatMap(ExecutionState.init(rawValue:))
    }

    public func initializeState(evidenceSHA256: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard currentState == nil else { throw PersistentTransactionError.stateAlreadyInitialized }
        guard Self.validSHA256(evidenceSHA256) else { throw PersistentTransactionError.invalidStateEvidence }
        try append(kind: "state.transition", payload: binding([
            "from": "NONE",
            "to": ExecutionState.appReady.rawValue,
            "evidenceSHA256": evidenceSHA256,
        ]))
    }

    /// Plan C4 pre-intent continuation: a restart may re-establish the current
    /// pre-Save-All state from fresh observation. The re-observation is recorded
    /// explicitly; it is neither a backward transition nor a counter reset.
    public func recordStateReverification(state: ExecutionState, evidenceSHA256: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard !isObserveOnlyResume, currentState == state else {
            throw PersistentTransactionError.stateAlreadyInitialized
        }
        guard Self.validSHA256(evidenceSHA256) else {
            throw PersistentTransactionError.invalidStateEvidence
        }
        try append(kind: "state.reverified", payload: binding([
            "state": state.rawValue,
            "evidenceSHA256": evidenceSHA256,
        ]))
    }

    public func transition(to next: ExecutionState, evidenceSHA256: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard let current = currentState else { throw PersistentTransactionError.stateNotInitialized }
        guard Self.validSHA256(evidenceSHA256) else { throw PersistentTransactionError.invalidStateEvidence }
        try ExecutionStateMachine.validateTransition(from: current, to: next)
        try append(kind: "state.transition", payload: binding([
            "from": current.rawValue,
            "to": next.rawValue,
            "evidenceSHA256": evidenceSHA256,
        ]))
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
        try append(kind: "dispatch.reversible", payload: binding(["action": action]))
    }

    /// Durable intent is written before the caller can post Save All. A restart
    /// sees the intent and cannot reserve or replay this operation.
    public func reserveSaveAll() throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let counts = irreversibleOperationCounts
        guard !isObserveOnlyResume, counts.saveAll == 0 else {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll")
        }
        if let goalSlot {
            do {
                try goalSlot.consumeEntitlement(ledgerFileURL: ledger.fileURL, runID: authorization.runID)
            } catch let error as GoalSlotError {
                if case let .entitlementAlreadyConsumed(detail) = error {
                    throw PersistentTransactionError.goalSlotEntitlementConsumed(detail)
                }
                throw error
            }
        }
        try append(kind: "intent.saveAll", payload: binding(["risk": "IRREVERSIBLE_SIDE_EFFECT"]))
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
        try append(kind: "attempt.saveAll", payload: binding([:]))
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
              postconditionEvidence.runDirectory.path == URL(fileURLWithPath: authorization.evidenceRunDirectory).standardizedFileURL.path,
              tripwireEvidence.runDirectory == postconditionEvidence.runDirectory,
              try BoundEvidenceDigest.load(
                fileURL: postconditionEvidence.fileURL,
                withinRunDirectory: URL(fileURLWithPath: authorization.evidenceRunDirectory),
                runID: authorization.runID
              ).sha256 == postconditionEvidence.sha256,
              try BoundEvidenceDigest.load(
                fileURL: tripwireEvidence.fileURL,
                withinRunDirectory: URL(fileURLWithPath: authorization.evidenceRunDirectory),
                runID: authorization.runID
              ).sha256 == tripwireEvidence.sha256 else {
            throw PersistentTransactionError.authorizationMismatch
        }
        guard ledger.entries.contains(where: { $0.kind == "attempt.saveAll" && isBound($0) }),
              Self.validSHA256(postconditionEvidence.sha256), Self.validSHA256(tripwireEvidence.sha256) else {
            throw PersistentTransactionError.authorizationMismatch
        }
        try append(kind: "postcondition.chooserVerified", payload: binding([
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
              record.evidenceRunDirectory == authorization.evidenceRunDirectory else {
            throw PersistentTransactionError.authorizationMismatch
        }
        try record.append(to: ledger)
        try checkpoint()
    }

    public func reserveDestinationConfirmation(action: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let counts = irreversibleOperationCounts
        guard !isObserveOnlyResume,
              counts.saveAll >= 2, counts.destinationConfirmation == 0,
              ["AXPressDefaultButton", "ReturnKey"].contains(action),
              ledger.entries.contains(where: { $0.kind == "postcondition.chooserVerified" && isBound($0) }) else {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("destinationConfirmation")
        }
        try append(kind: "intent.destinationConfirmation", payload: binding(["action": action]))
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
        try append(kind: "attempt.destinationConfirmation", payload: binding([:]))
        confirmationIntentOwnedByThisProcess = false
    }

    private func append(kind: String, payload: [String: String]) throws {
        try ledger.append(kind: kind, payload: payload)
        try checkpoint()
    }

    private func checkpoint() throws {
        guard let checkpointURL else { return }
        try ledger.writeHeadAnchor(to: checkpointURL)
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

    /// Observe-only is a property of irreversible history, never of the mere
    /// presence of pre-intent records: a verified pre-intent continuation must
    /// remain able to re-observe and proceed (plan C4), while any irreversible
    /// intent/attempt permanently forces observe-only.
    private static func isIrreversibleRecord(_ kind: String) -> Bool {
        switch kind {
        case "intent.saveAll", "attempt.saveAll", "intent.destinationConfirmation", "attempt.destinationConfirmation":
            return true
        default:
            return false
        }
    }
}
