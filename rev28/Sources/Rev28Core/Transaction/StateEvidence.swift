import CoreGraphics
import Foundation

// MARK: - C2/C4 typed state evidence
//
// A state is never established by an opaque digest string. Every transition in
// the common engine is validated against this typed, run-bound projection of one
// native observation bundle, plus the retained bytes it references. Adapters may
// obtain observations; they cannot manufacture semantic authority in common code.

public struct StateEvidenceArtifact: Codable, Equatable, Sendable {
    public let runID: String
    public let state: String
    public let sessionID: String
    public let epoch: UInt64
    public let bundleID: String
    public let pid: Int32
    public let processStartSeconds: Int64
    public let processStartMicroseconds: Int32
    public let windowID: UInt32
    public let windowFrame: CGRect
    public let axRole: String?
    public let frameSHA256: String
    public let retainedFrameName: String
    public let capturedAtISO8601: String
    public let startedAtMonotonicNanos: UInt64
    public let endedAtMonotonicNanos: UInt64
    public let deadlineMonotonicNanos: UInt64
    public let ocrTexts: [String]
    public let cardRegionCount: Int
    public let candidateIdentity: String?
    public let candidateRefusal: String?
    public let localization: String

    public init(
        runID: String,
        state: String,
        sessionID: String,
        epoch: UInt64,
        bundleID: String,
        pid: Int32,
        processStartSeconds: Int64,
        processStartMicroseconds: Int32,
        windowID: UInt32,
        windowFrame: CGRect,
        axRole: String?,
        frameSHA256: String,
        retainedFrameName: String,
        capturedAtISO8601: String,
        startedAtMonotonicNanos: UInt64,
        endedAtMonotonicNanos: UInt64,
        deadlineMonotonicNanos: UInt64,
        ocrTexts: [String],
        cardRegionCount: Int,
        candidateIdentity: String?,
        candidateRefusal: String?,
        localization: String
    ) {
        self.runID = runID
        self.state = state
        self.sessionID = sessionID
        self.epoch = epoch
        self.bundleID = bundleID
        self.pid = pid
        self.processStartSeconds = processStartSeconds
        self.processStartMicroseconds = processStartMicroseconds
        self.windowID = windowID
        self.windowFrame = windowFrame
        self.axRole = axRole
        self.frameSHA256 = frameSHA256
        self.retainedFrameName = retainedFrameName
        self.capturedAtISO8601 = capturedAtISO8601
        self.startedAtMonotonicNanos = startedAtMonotonicNanos
        self.endedAtMonotonicNanos = endedAtMonotonicNanos
        self.deadlineMonotonicNanos = deadlineMonotonicNanos
        self.ocrTexts = ocrTexts
        self.cardRegionCount = cardRegionCount
        self.candidateIdentity = candidateIdentity
        self.candidateRefusal = candidateRefusal
        self.localization = localization
    }

    /// A projection of one verified observation bundle. Field-by-field copying
    /// keeps the artifact's contents anchored to observations rather than to
    /// adapter-authored strings.
    public init(bundle: ObservationBundle, retainedFrameName: String) {
        self.init(
            runID: bundle.runID,
            state: bundle.state.rawValue,
            sessionID: bundle.sessionID,
            epoch: bundle.epoch,
            bundleID: bundle.window.bundleID,
            pid: bundle.process.pid,
            processStartSeconds: bundle.process.startTimeSeconds,
            processStartMicroseconds: bundle.process.startTimeMicroseconds,
            windowID: bundle.window.windowID,
            windowFrame: bundle.window.windowFrame,
            axRole: bundle.axIdentity.role,
            frameSHA256: bundle.frame.imageSHA256,
            retainedFrameName: retainedFrameName,
            capturedAtISO8601: bundle.frame.capturedAtISO8601,
            startedAtMonotonicNanos: bundle.startedAtMonotonicNanos,
            endedAtMonotonicNanos: bundle.endedAtMonotonicNanos,
            deadlineMonotonicNanos: bundle.deadlineMonotonicNanos,
            ocrTexts: bundle.ocrItems.map(\.text),
            cardRegionCount: bundle.cardRegions.count,
            candidateIdentity: bundle.candidate?.identity,
            candidateRefusal: bundle.candidateRefusal?.rawValue,
            localization: String(describing: bundle.localization)
        )
    }
}

public struct EstablishedStateEvidence: Sendable {
    public let artifactName: String
    public let evidenceSHA256: String
    public let artifact: StateEvidenceArtifact

    public init(artifactName: String, evidenceSHA256: String, artifact: StateEvidenceArtifact) {
        self.artifactName = artifactName
        self.evidenceSHA256 = evidenceSHA256
        self.artifact = artifact
    }
}

public enum StateEvidenceError: Error, Equatable, CustomStringConvertible {
    case runMismatch
    case stateMismatch(expected: String, actual: String)
    case staleEpoch(previous: UInt64, actual: UInt64)
    case missingTypedFields(String)
    case candidateRequirementFailed(state: String, detail: String)
    case unexpectedCandidate(state: String)
    case missingIdentityText(state: String, text: String)
    case nonMonotonicTimes

    public var description: String {
        switch self {
        case .runMismatch:
            return "stateEvidenceRunMismatch"
        case let .stateMismatch(expected, actual):
            return "stateEvidenceStateMismatch(expected=\(expected), actual=\(actual))"
        case let .staleEpoch(previous, actual):
            return "stateEvidenceStaleEpoch(previous=\(previous), actual=\(actual))"
        case let .missingTypedFields(detail):
            return "stateEvidenceMissingTypedFields(\(detail))"
        case let .candidateRequirementFailed(state, detail):
            return "stateEvidenceCandidateRequirementFailed(state=\(state), detail=\(detail))"
        case let .unexpectedCandidate(state):
            return "stateEvidenceUnexpectedCandidate(state=\(state))"
        case let .missingIdentityText(state, text):
            return "stateEvidenceMissingIdentityText(state=\(state), text=\(text))"
        case .nonMonotonicTimes:
            return "stateEvidenceNonMonotonicTimes"
        }
    }
}

/// The reviewed state requirements in common code. Requirements are keyed by
/// `ExecutionState`, so an adapter cannot decide which states need which proof.
public enum ExecutionStateEvidencePolicy {
    public struct Requirement: Equatable, Sendable {
        public let requiredOcrTexts: [String]
        public let exactCandidateIdentity: String?
        public let candidateIdentitySuffix: String?

        public init(
            requiredOcrTexts: [String] = [],
            exactCandidateIdentity: String? = nil,
            candidateIdentitySuffix: String? = nil
        ) {
            self.requiredOcrTexts = requiredOcrTexts
            self.exactCandidateIdentity = exactCandidateIdentity
            self.candidateIdentitySuffix = candidateIdentitySuffix
        }
    }

    public static func requirement(for state: ExecutionState) -> Requirement {
        switch state {
        case .appReady, .albumListReady:
            return Requirement()
        case .groupReady:
            return Requirement(requiredOcrTexts: [LiveExecutionEngine.targetGroup])
        case .targetAlbumLocated:
            return Requirement(candidateIdentitySuffix: ":2024/05/13~05/17|57")
        case .albumDetailVerified:
            return Requirement(requiredOcrTexts: [LiveExecutionEngine.targetGroup, "57張照片"])
        case .ellipsisLocated:
            return Requirement(exactCandidateIdentity: "album-ellipsis")
        case .menuVerified:
            return Requirement(requiredOcrTexts: StructuralLocators.lineAlbumMenuReference)
        case .saveAllLocated:
            return Requirement(exactCandidateIdentity: "儲存全部")
        case .chooserVerified, .destinationPrepared, .downloadConfirmed,
             .downloadInProgress, .filesystemStable, .contentVerified, .finalized:
            return Requirement()
        }
    }

    public static func validate(
        artifact: StateEvidenceArtifact,
        expectedState: ExecutionState,
        authorization: ImmutableRunAuthorization,
        previousEpoch: UInt64?
    ) throws {
        guard artifact.runID == authorization.runID else { throw StateEvidenceError.runMismatch }
        guard artifact.state == expectedState.rawValue else {
            throw StateEvidenceError.stateMismatch(expected: expectedState.rawValue, actual: artifact.state)
        }
        guard artifact.epoch > (previousEpoch ?? 0) else {
            throw StateEvidenceError.staleEpoch(previous: previousEpoch ?? 0, actual: artifact.epoch)
        }
        guard !artifact.sessionID.isEmpty,
              !artifact.bundleID.isEmpty,
              artifact.pid > 0,
              artifact.windowID > 0,
              artifact.axRole?.isEmpty == false,
              Self.isSHA256(artifact.frameSHA256),
              Self.isSafeEvidenceName(artifact.retainedFrameName) else {
            throw StateEvidenceError.missingTypedFields("session/window/ax/hash/retained-name")
        }
        guard artifact.startedAtMonotonicNanos <= artifact.endedAtMonotonicNanos,
              artifact.endedAtMonotonicNanos <= artifact.deadlineMonotonicNanos else {
            throw StateEvidenceError.nonMonotonicTimes
        }
        let requirement = requirement(for: expectedState)
        for text in requirement.requiredOcrTexts where !artifact.ocrTexts.contains(text) {
            throw StateEvidenceError.missingIdentityText(state: expectedState.rawValue, text: text)
        }
        if let exact = requirement.exactCandidateIdentity {
            guard artifact.candidateRefusal == nil,
                  artifact.candidateIdentity == exact else {
                throw StateEvidenceError.candidateRequirementFailed(
                    state: expectedState.rawValue,
                    detail: "expected exact candidate \(exact), observed \(artifact.candidateIdentity ?? artifact.candidateRefusal ?? "none")"
                )
            }
        } else if let suffix = requirement.candidateIdentitySuffix {
            guard artifact.candidateRefusal == nil,
                  artifact.candidateIdentity?.hasSuffix(suffix) == true else {
                throw StateEvidenceError.candidateRequirementFailed(
                    state: expectedState.rawValue,
                    detail: "expected candidate suffix \(suffix), observed \(artifact.candidateIdentity ?? artifact.candidateRefusal ?? "none")"
                )
            }
        } else {
            guard artifact.candidateIdentity == nil, artifact.candidateRefusal == nil else {
                throw StateEvidenceError.unexpectedCandidate(state: expectedState.rawValue)
            }
        }
    }

    private static func isSHA256(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy(\.isHexDigit) && Set(value).count > 1
    }

    private static func isSafeEvidenceName(_ name: String) -> Bool {
        !name.isEmpty
            && !name.hasPrefix(".")
            && !name.contains("/")
            && !name.contains("\\")
            && name != ".."
    }
}
