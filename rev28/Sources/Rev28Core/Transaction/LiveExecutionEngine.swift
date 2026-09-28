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
    case typedStateEvidenceRejected(String)
    case evidenceFileInvalid(String)

    public var description: String {
        switch self {
        case .invalidTargetAuthorization: return "invalidTargetAuthorization"
        case .stateAlreadyStarted: return "stateAlreadyStarted"
        case .saveAllBoundaryDidNotConsumeExactlyOnce: return "saveAllBoundaryDidNotConsumeExactlyOnce"
        case .destinationBoundaryDidNotConsumeExactlyOnce: return "destinationBoundaryDidNotConsumeExactlyOnce"
        case let .invalidEvidenceDigest(stage): return "invalidEvidenceDigest(\(stage))"
        case let .typedStateEvidenceRejected(detail): return "typedStateEvidenceRejected(\(detail))"
        case let .evidenceFileInvalid(detail): return "evidenceFileInvalid(\(detail))"
        }
    }
}

/// One orchestration contract for both deterministic integration tests and the
/// real-mac adapter. Implementations may differ only in how observations and
/// OS actions are obtained; state/ledger/exactly-once semantics live here.
public protocol LiveExecutionAdapter: Sendable {
    /// Establish or re-establish one pre-Save-All state from fresh observation.
    /// For reversible states, the adapter may use guarded reversible actuation.
    /// Returns typed evidence: a projection of one observation bundle plus the
    /// retained frame artifact it references. The engine — not the adapter —
    /// decides whether that evidence proves the requested state.
    func establish(state: ExecutionState, owner: PersistentTransactionOwner) async throws -> EstablishedStateEvidence

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
        guard owner.currentState == nil else {
            throw LiveExecutionEngineError.stateAlreadyStarted
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
        var previousEpoch: UInt64?
        for (index, state) in preSaveStates.enumerated() {
            let evidence = try await adapter.establish(state: state, owner: owner)
            try Self.validateEstablishedEvidence(
                evidence,
                state: state,
                owner: owner,
                previousEpoch: previousEpoch
            )
            previousEpoch = evidence.artifact.epoch
            if index == 0 {
                try owner.initializeState(evidenceSHA256: evidence.evidenceSHA256)
            } else {
                try owner.transition(to: state, evidenceSHA256: evidence.evidenceSHA256)
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

    /// Typed, file-backed validation of one established state. The adapter's
    /// in-memory artifact must match both the requested state policy and the
    /// durable artifact bytes inside the run's evidence directory; the retained
    /// frame referenced by the artifact must exist with the recorded SHA.
    static func validateEstablishedEvidence(
        _ evidence: EstablishedStateEvidence,
        state: ExecutionState,
        owner: PersistentTransactionOwner,
        previousEpoch: UInt64?
    ) throws {
        do {
            try ExecutionStateEvidencePolicy.validate(
                artifact: evidence.artifact,
                expectedState: state,
                authorization: owner.authorization,
                previousEpoch: previousEpoch
            )
        } catch let error as StateEvidenceError {
            throw LiveExecutionEngineError.typedStateEvidenceRejected(error.description)
        }
        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory).standardizedFileURL
        let artifactData = try loadEvidenceFile(
            named: evidence.artifactName,
            runDirectory: runDirectory,
            expectedSHA256: evidence.evidenceSHA256,
            stage: "state.\(state.rawValue).artifact"
        )
        let decoded: StateEvidenceArtifact
        do {
            decoded = try JSONDecoder().decode(StateEvidenceArtifact.self, from: artifactData)
        } catch {
            throw LiveExecutionEngineError.evidenceFileInvalid("state artifact \(evidence.artifactName) does not decode")
        }
        guard decoded == evidence.artifact else {
            throw LiveExecutionEngineError.evidenceFileInvalid("state artifact \(evidence.artifactName) differs from the in-memory artifact")
        }
        _ = try loadEvidenceFile(
            named: evidence.artifact.retainedFrameName,
            runDirectory: runDirectory,
            expectedSHA256: evidence.artifact.frameSHA256,
            stage: "state.\(state.rawValue).retainedFrame"
        )
    }

    private static func loadEvidenceFile(
        named name: String,
        runDirectory: URL,
        expectedSHA256: String,
        stage: String
    ) throws -> Data {
        guard !name.isEmpty, !name.hasPrefix("."), !name.contains("/"), !name.contains("\\") else {
            throw LiveExecutionEngineError.evidenceFileInvalid("\(stage): unsafe evidence name \(name)")
        }
        let url = runDirectory.appendingPathComponent(name).standardizedFileURL
        guard url.deletingLastPathComponent().path == runDirectory.path else {
            throw LiveExecutionEngineError.evidenceFileInvalid("\(stage): evidence escapes the run directory")
        }
        let values = try? url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
        guard values?.isRegularFile == true, values?.isSymbolicLink != true else {
            throw LiveExecutionEngineError.evidenceFileInvalid("\(stage): evidence file is missing, not regular, or a symlink")
        }
        let data = try Data(contentsOf: url)
        guard EvidenceIO.sha256Hex(data) == expectedSHA256 else {
            throw LiveExecutionEngineError.evidenceFileInvalid("\(stage): evidence bytes do not match the recorded SHA")
        }
        return data
    }
}
