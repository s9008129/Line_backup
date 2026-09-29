import Foundation

public struct LiveChooserEvidence: Sendable {
    public let postcondition: BoundEvidenceDigest
    public let tripwire: BoundEvidenceDigest

    public init(postcondition: BoundEvidenceDigest, tripwire: BoundEvidenceDigest) {
        self.postcondition = postcondition
        self.tripwire = tripwire
    }
}

public struct LiveContentEvidence: Equatable, Sendable {
    public let verification: StagingVerification
    public let evidenceSHA256: String

    public init(verification: StagingVerification, evidenceSHA256: String) {
        self.verification = verification
        self.evidenceSHA256 = evidenceSHA256
    }
}

public enum LiveExecutionOutcome: Equatable, Sendable {
    case contentVerified(StagingVerification)
    case contentRejected(StagingVerification)
    case observeOnlyResume(ExecutionState?)
}

public enum LiveExecutionEngineError: Error, Equatable, CustomStringConvertible {
    case invalidTargetAuthorization
    case stateAlreadyStarted
    case saveAllBoundaryDidNotConsumeExactlyOnce
    case destinationBoundaryDidNotConsumeExactlyOnce
    case invalidEvidenceDigest(String)

    public var description: String {
        switch self {
        case .invalidTargetAuthorization: return "invalidTargetAuthorization"
        case .stateAlreadyStarted: return "stateAlreadyStarted"
        case .saveAllBoundaryDidNotConsumeExactlyOnce: return "saveAllBoundaryDidNotConsumeExactlyOnce"
        case .destinationBoundaryDidNotConsumeExactlyOnce: return "destinationBoundaryDidNotConsumeExactlyOnce"
        case let .invalidEvidenceDigest(stage): return "invalidEvidenceDigest(\(stage))"
        }
    }
}

/// One orchestration contract for both deterministic integration tests and the
/// real-mac adapter. Implementations may differ only in how observations and
/// OS actions are obtained; state/ledger/exactly-once semantics live here.
public protocol LiveExecutionAdapter: Sendable {
    /// Establish or re-establish one pre-Save-All state from fresh observation.
    /// For reversible states, the adapter may use guarded reversible actuation.
    /// Returns the SHA-256 of evidence proving the state.
    func establish(state: ExecutionState, owner: PersistentTransactionOwner) async throws -> String

    /// Must dispatch Save All through GatedQuartzActuator with .saveAll(owner).
    /// Returns a SHA-256 evidence digest for the attempted dispatch.
    func dispatchSaveAll(owner: PersistentTransactionOwner) async throws -> String

    /// Must use StrictPostconditionMonitor + frozen chooser predicate and return
    /// bound postcondition/tripwire artifacts from this run directory.
    func observeChooser(owner: PersistentTransactionOwner) async throws -> LiveChooserEvidence

    /// Reversible chooser navigation only; no final confirmation here.
    func prepareDestination(owner: PersistentTransactionOwner) async throws -> String

    /// Must dispatch the one confirmation through GatedDestinationConfirmation.
    func confirmDestination(owner: PersistentTransactionOwner) async throws -> String

    /// Direct postcondition after confirmation: chooser closure / filesystem start.
    func observeDownloadStarted(owner: PersistentTransactionOwner) async throws -> String

    func observeDownloadInProgress(owner: PersistentTransactionOwner) async throws -> String
    func observeFilesystemStable(owner: PersistentTransactionOwner) async throws -> String

    /// Production implementation must call StagingVerifier against the authorized
    /// unique staging directory and return its evidence digest.
    func verifyContent(owner: PersistentTransactionOwner) async throws -> LiveContentEvidence
}

public struct LiveExecutionEngine {
    public static let targetGroup = "旻謙允禎成長日記"
    public static let targetAlbum = "2024/05/13～05/17"

    public let owner: PersistentTransactionOwner
    public let adapter: any LiveExecutionAdapter

    public init(owner: PersistentTransactionOwner, adapter: any LiveExecutionAdapter) {
        self.owner = owner
        self.adapter = adapter
    }

    public func run() async throws -> LiveExecutionOutcome {
        guard owner.authorization.group == Self.targetGroup,
              owner.authorization.album == Self.targetAlbum,
              owner.authorization.expectedFileCount == StagingPolicy.rev28Accepted.expectedFileCount,
              owner.authorization.expectedTotalBytes == StagingPolicy.rev28Accepted.expectedTotalBytes,
              owner.authorization.expectedContentMultisetSHA256 == StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
              owner.authorization.baselineTripwireSHA256 == ImmutableRunAuthorization.acceptedBaselineTripwireSHA256 else {
            throw LiveExecutionEngineError.invalidTargetAuthorization
        }

        if owner.isObserveOnlyResume {
            return .observeOnlyResume(owner.currentState)
        }

        let preSaveStates: [ExecutionState] = [
            .appReady,
            .groupReady,
            .albumListReady,
            .targetAlbumLocated,
            .albumDetailVerified,
            .ellipsisLocated,
            .menuVerified,
            .saveAllLocated,
        ]
        // Plan C4 verified pre-intent continuation: with zero irreversible
        // records, a restart re-establishes the current state from fresh
        // observation (recorded as `state.reverified`), then proceeds forward.
        // Nothing is reset and no backward transition is invented.
        var resumeIndex = 0
        if let currentState = owner.currentState {
            guard let index = preSaveStates.firstIndex(of: currentState) else {
                throw LiveExecutionEngineError.stateAlreadyStarted
            }
            let reverified = try await adapter.establish(state: currentState, owner: owner)
            try validateDigest(reverified, stage: "REVERIFY-\(currentState.rawValue)")
            try owner.recordStateReverification(state: currentState, evidenceSHA256: reverified)
            resumeIndex = index + 1
        }
        for (index, state) in preSaveStates.enumerated() {
            guard index >= resumeIndex else { continue }
            let evidence = try await adapter.establish(state: state, owner: owner)
            try validateDigest(evidence, stage: state.rawValue)
            if index == 0 {
                try owner.initializeState(evidenceSHA256: evidence)
            } else {
                try owner.transition(to: state, evidenceSHA256: evidence)
            }
        }

        let saveAllEvidence = try await adapter.dispatchSaveAll(owner: owner)
        try validateDigest(saveAllEvidence, stage: "SAVE_ALL_DISPATCH")
        guard owner.irreversibleOperationCounts.saveAll == 2,
              owner.irreversibleOperationCounts.destinationConfirmation == 0 else {
            throw LiveExecutionEngineError.saveAllBoundaryDidNotConsumeExactlyOnce
        }

        let chooser = try await adapter.observeChooser(owner: owner)
        try owner.recordChooserVerified(
            postconditionEvidence: chooser.postcondition,
            tripwireEvidence: chooser.tripwire
        )
        try owner.transition(to: .chooserVerified, evidenceSHA256: chooser.postcondition.sha256)

        let destinationEvidence = try await adapter.prepareDestination(owner: owner)
        try validateDigest(destinationEvidence, stage: ExecutionState.destinationPrepared.rawValue)
        try owner.transition(to: .destinationPrepared, evidenceSHA256: destinationEvidence)

        let confirmationEvidence = try await adapter.confirmDestination(owner: owner)
        try validateDigest(confirmationEvidence, stage: "DESTINATION_CONFIRMATION")
        guard owner.irreversibleOperationCounts.saveAll == 2,
              owner.irreversibleOperationCounts.destinationConfirmation == 2 else {
            throw LiveExecutionEngineError.destinationBoundaryDidNotConsumeExactlyOnce
        }

        let downloadConfirmed = try await adapter.observeDownloadStarted(owner: owner)
        try validateDigest(downloadConfirmed, stage: ExecutionState.downloadConfirmed.rawValue)
        try owner.transition(to: .downloadConfirmed, evidenceSHA256: downloadConfirmed)

        let inProgress = try await adapter.observeDownloadInProgress(owner: owner)
        try validateDigest(inProgress, stage: ExecutionState.downloadInProgress.rawValue)
        try owner.transition(to: .downloadInProgress, evidenceSHA256: inProgress)

        let stable = try await adapter.observeFilesystemStable(owner: owner)
        try validateDigest(stable, stage: ExecutionState.filesystemStable.rawValue)
        try owner.transition(to: .filesystemStable, evidenceSHA256: stable)

        let content = try await adapter.verifyContent(owner: owner)
        try validateDigest(content.evidenceSHA256, stage: ExecutionState.contentVerified.rawValue)
        guard content.verification.outcome == .duplicateContentConfirmed,
              content.verification.fileCount == owner.authorization.expectedFileCount,
              content.verification.totalBytes == owner.authorization.expectedTotalBytes,
              content.verification.contentMultisetSHA256 == owner.authorization.expectedContentMultisetSHA256 else {
            return .contentRejected(content.verification)
        }
        try owner.transition(to: .contentVerified, evidenceSHA256: content.evidenceSHA256)
        return .contentVerified(content.verification)
    }

    private func validateDigest(_ value: String, stage: String) throws {
        guard value.count == 64,
              value.allSatisfy(\.isHexDigit),
              Set(value).count > 1 else {
            throw LiveExecutionEngineError.invalidEvidenceDigest(stage)
        }
    }
}
