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
    case ledgerCheckpointRequired
    case ledgerCheckpointInvalid
    case stateAlreadyInitialized
    case stateNotInitialized
    case invalidStateEvidence
    case saveAllRequiresLocatedState
    case goalSlotEntitlementConsumed
    case chooserVerificationNotPermitted
    case chooserVerificationAlreadyRecorded
    case phaseBEligibilityRequired
    case phaseBEligibilityAlreadyRecorded
    case phaseBBudgetExhausted
    case destinationConfirmationRequiresPreparedState

    public var description: String {
        switch self {
        case .invalidAuthorization: return "invalidAuthorization"
        case .authorizationAlreadyBound: return "authorizationAlreadyBound"
        case .authorizationMismatch: return "authorizationMismatch"
        case let .irreversibleIntentAlreadyRecorded(kind): return "irreversibleIntentAlreadyRecorded(\(kind))"
        case let .irreversibleAttemptAlreadyRecorded(kind): return "irreversibleAttemptAlreadyRecorded(\(kind))"
        case .ledgerCheckpointRequired: return "ledgerCheckpointRequired"
        case .ledgerCheckpointInvalid: return "ledgerCheckpointInvalid"
        case .stateAlreadyInitialized: return "stateAlreadyInitialized"
        case .stateNotInitialized: return "stateNotInitialized"
        case .invalidStateEvidence: return "invalidStateEvidence"
        case .saveAllRequiresLocatedState: return "saveAllRequiresLocatedState"
        case .goalSlotEntitlementConsumed: return "goalSlotEntitlementConsumed"
        case .chooserVerificationNotPermitted: return "chooserVerificationNotPermitted"
        case .chooserVerificationAlreadyRecorded: return "chooserVerificationAlreadyRecorded"
        case .phaseBEligibilityRequired: return "phaseBEligibilityRequired"
        case .phaseBEligibilityAlreadyRecorded: return "phaseBEligibilityAlreadyRecorded"
        case .phaseBBudgetExhausted: return "phaseBBudgetExhausted"
        case .destinationConfirmationRequiresPreparedState: return "destinationConfirmationRequiresPreparedState"
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
    private let checkpointURL: URL?
    public let goalSlotDirectory: URL
    public let isObserveOnlyResume: Bool
    /// True once an on-disk head anchor was verified against this ledger (or
    /// written by this process after a verified/initial append).
    public private(set) var isCheckpointVerified = false
    /// True when this process *started* with irreversible intent/attempt
    /// records already in the ledger — i.e. the restart happened after the
    /// irreversible boundary. Such a session is permanently observe-only for
    /// the irreversible operations (plan C4).
    public let isPostIrreversibleResume: Bool

    public init(
        authorization: ImmutableRunAuthorization,
        ledger: IntentLedger,
        checkpointURL: URL? = nil,
        goalSlotDirectory: URL? = nil,
        requireCheckpointOnResume: Bool = false
    ) throws {
        guard authorization.isValid else { throw PersistentTransactionError.invalidAuthorization }
        self.authorization = authorization
        self.ledger = ledger
        self.checkpointURL = checkpointURL?.standardizedFileURL
        self.goalSlotDirectory = (goalSlotDirectory ?? GoalSlot.canonicalDirectory(for: authorization)).standardizedFileURL
        self.isObserveOnlyResume = !ledger.entries.isEmpty
        self.isPostIrreversibleResume = ledger.entries.contains {
            $0.kind == "intent.saveAll" || $0.kind == "attempt.saveAll"
                || $0.kind == "intent.destinationConfirmation" || $0.kind == "attempt.destinationConfirmation"
        }
        try EvidenceIO.ensureDirectory(URL(fileURLWithPath: authorization.evidenceRunDirectory))

        // The persistent goal slot binds this run's one-shot entitlement. An
        // empty ledger combined with an already-consumed entitlement is a
        // truncation/reset attempt, never a fresh transaction.
        let goalSlot = try GoalSlot.open(directory: self.goalSlotDirectory, authorization: authorization)
        if goalSlot.entitlementConsumed, ledger.entries.isEmpty {
            throw PersistentTransactionError.goalSlotEntitlementConsumed
        }

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
                // An anchor generated now is not an independent verification
                // of the resumed history; it is written for compatibility but
                // never marks the resume checkpoint-verified, so the strictly
                // gated pre-intent continuation stays unavailable here.
                try ledger.writeHeadAnchor(to: checkpointURL)
                return
            }
            do {
                _ = try IntentLedger.verifyHeadAnchor(fileURL: ledger.fileURL, anchorURL: checkpointURL)
                isCheckpointVerified = true
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


    /// The one-shot Save All boundary may be entered by a fresh session or by
    /// a strictly verified pre-intent continuation; never after any
    /// irreversible record or an unverified resume.
    private var mayEnterIrreversibleBoundary: Bool {
        !isPostIrreversibleResume && (!isObserveOnlyResume || preIntentContinuationAllowed)
    }

    public var hasIrreversibleRecords: Bool {
        irreversibleOperationCounts != (0, 0)
    }

    /// Plan C4 pre-intent continuation: a restart may resume (reacquiring every
    /// live fact) only with a verified goal slot + ledger + head anchor, zero
    /// irreversible intent/attempt records, and a durable state that is still
    /// before the irreversible boundary. Anything else is observe-only.
    public var preIntentContinuationAllowed: Bool {
        guard isCheckpointVerified, !isPostIrreversibleResume, !hasIrreversibleRecords, currentState != nil else {
            return false
        }
        let postIrreversibleStates: Set<ExecutionState> = [
            .chooserVerified, .destinationPrepared, .downloadConfirmed,
            .downloadInProgress, .filesystemStable, .contentVerified, .finalized,
        ]
        return !postIrreversibleStates.contains(currentState!)
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

    /// Durable per-identical-blocker recovery counts, recomputed from the
    /// verified ledger. LiveDispatchBudget is only ever this derived view.
    public var identicalBlockerRecoveries: [String: Int] {
        ledger.entries
            .filter { $0.kind == "budget.blocker" }
            .compactMap { $0.payload["blockerKey"] }
            .reduce(into: [String: Int]()) { $0[$1, default: 0] += 1 }
    }

    /// Consecutive candidate-revalidation failures ending at the ledger head.
    public var consecutiveCandidateRevalidationFailures: Int {
        var failures = 0
        for entry in ledger.entries.reversed() where entry.kind == "budget.revalidation" {
            guard entry.payload["passed"] == "false" else { break }
            failures += 1
        }
        return failures
    }

    public var liveDispatchBudget: LiveDispatchBudget {
        LiveDispatchBudget(
            reversibleDispatches: reversibleDispatchCount,
            saveAllDispatches: irreversibleOperationCounts.saveAll,
            destinationConfirmations: irreversibleOperationCounts.destinationConfirmation,
            identicalBlockerRecoveries: identicalBlockerRecoveries,
            consecutiveCandidateRevalidationFailures: consecutiveCandidateRevalidationFailures
        )
    }

    /// Global ceiling plus a durable per-semantic-action recovery ceiling.
    /// `blockerKey` defaults to the reviewed action grouping, so a caller
    /// cannot rename a retry to escape the per-blocker ceiling.
    public func recordReversibleDispatch(action: String, blockerKey: String? = nil) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard reversibleDispatchCount < LiveDispatchBudget.reversibleCeiling else {
            throw ExecutionPolicyError.reversibleBudgetExhausted
        }
        let key = blockerKey ?? action
        guard identicalBlockerRecoveries[key, default: 0] < LiveDispatchBudget.perIdenticalBlockerCeiling else {
            throw ExecutionPolicyError.identicalBlockerBudgetExhausted
        }
        // Plan C4 abort rule: two consecutive failed candidate revalidations
        // durably abort. The durable counter is consulted here, at the write
        // path every reversible primitive must pass, so no further input can
        // be posted from an aborted run even if a caller catches the earlier
        // refusal; only a durably recorded success resets the counter.
        guard consecutiveCandidateRevalidationFailures < LiveDispatchBudget.consecutiveRevalidationAbortThreshold else {
            throw ExecutionPolicyError.candidateRevalidationExhausted
        }
        try append(kind: "dispatch.reversible", payload: binding(["action": action]))
        try append(kind: "budget.blocker", payload: binding(["blockerKey": key]))
    }

    /// Persists one candidate revalidation outcome. Two consecutive failures
    /// abort: the second failure is durable before the error surfaces, so a
    /// restart cannot re-derive a cleared revalidation history.
    public func recordCandidateRevalidation(blockerKey: String, passed: Bool) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let consecutive = passed ? 0 : consecutiveCandidateRevalidationFailures + 1
        try append(kind: "budget.revalidation", payload: binding([
            "blockerKey": blockerKey,
            "passed": passed ? "true" : "false",
        ]))
        if consecutive >= 2 {
            throw ExecutionPolicyError.candidateRevalidationExhausted
        }
    }

    /// Persists the machine-checked Phase B eligibility decision for this run.
    /// `reserveSaveAll` refuses unless this record exists, so the one-shot
    /// entitlement can never be consumed by a caller that skipped the gate.
    /// The artifact's file-checkable evidence is recomputed here, at the owner
    /// boundary, so a producer label alone cannot arm the entitlement.
    public func recordPhaseBEligibility(
        _ artifact: PhaseBEligibilityArtifact,
        recomputation: PhaseBEligibilityRecomputation
    ) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard mayEnterIrreversibleBoundary else {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll")
        }
        guard !ledger.entries.contains(where: { $0.kind == "eligibility.phaseB" && isBound($0) }) else {
            throw PersistentTransactionError.phaseBEligibilityAlreadyRecorded
        }
        let slot = try GoalSlot.load(directory: goalSlotDirectory, authorization: authorization)
        try artifact.validateWithRecomputedEvidence(
            against: authorization,
            entitlementConsumed: slot?.entitlementConsumed ?? false,
            recomputation: recomputation
        )
        let digest = EvidenceIO.sha256Hex(try EvidenceIO.encodeJSON(artifact))
        try append(kind: "eligibility.phaseB", payload: binding([
            "artifactDigestSHA256": digest,
            "goalIdentitySHA256": artifact.goalIdentitySHA256,
            "verdict": artifact.verdict,
        ]))
    }

    /// Durable intent is written before the caller can post Save All. A restart
    /// sees the intent and cannot reserve or replay this operation.
    public func reserveSaveAll() throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        let counts = irreversibleOperationCounts
        guard mayEnterIrreversibleBoundary, counts.saveAll == 0 else {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll")
        }
        guard currentState == .saveAllLocated else {
            throw PersistentTransactionError.saveAllRequiresLocatedState
        }
        // Owner-level eligibility enforcement (R4 C4): the durable
        // machine-checked eligibility record must exist before the one-shot
        // entitlement is touched, so no adapter caller can reserve past it.
        guard ledger.entries.contains(where: { $0.kind == "eligibility.phaseB" && isBound($0) }) else {
            throw PersistentTransactionError.phaseBEligibilityRequired
        }
        // Plan PHASE_B_ELIGIBILITY: "reversible/revalidation budgets not
        // exhausted" is part of the entry conjunction. The derived durable
        // view is consulted before the one-shot entitlement is consumed, so
        // an exhausted ledger can never arm the entitlement.
        guard !liveDispatchBudget.isExhausted else {
            throw PersistentTransactionError.phaseBBudgetExhausted
        }
        do {
            try GoalSlot.consumeOneShotEntitlement(directory: goalSlotDirectory, authorization: authorization)
        } catch GoalSlotError.entitlementAlreadyConsumed {
            throw PersistentTransactionError.irreversibleIntentAlreadyRecorded("saveAll")
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
              tripwireArtifact.collectionGap == nil,
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
        // A chooser can only be validated after the one Save All intent/attempt
        // was durably dispatched from the freshly located state, and the
        // verification record itself is one-shot: a duplicate append would
        // forge a second, separately bound chooser history for this run.
        guard !ledger.entries.contains(where: { $0.kind == "postcondition.chooserVerified" && isBound($0) }) else {
            throw PersistentTransactionError.chooserVerificationAlreadyRecorded
        }
        guard currentState == .saveAllLocated else {
            throw PersistentTransactionError.chooserVerificationNotPermitted
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
        guard currentState == .destinationPrepared else {
            throw PersistentTransactionError.destinationConfirmationRequiresPreparedState
        }
        guard !isPostIrreversibleResume,
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
        isCheckpointVerified = true
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
