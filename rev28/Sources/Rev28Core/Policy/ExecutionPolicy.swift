import Foundation

public enum ExecutionState: String, Codable, CaseIterable, Sendable {
    case appReady = "APP_READY"
    case groupReady = "GROUP_READY"
    case albumListReady = "ALBUM_LIST_READY"
    case targetAlbumLocated = "TARGET_ALBUM_LOCATED"
    case albumDetailVerified = "ALBUM_DETAIL_VERIFIED"
    case ellipsisLocated = "ELLIPSIS_LOCATED"
    case menuVerified = "MENU_VERIFIED"
    case saveAllLocated = "SAVE_ALL_LOCATED"
    case chooserVerified = "CHOOSER_VERIFIED"
    case destinationPrepared = "DESTINATION_PREPARED"
    case downloadConfirmed = "DOWNLOAD_CONFIRMED"
    case downloadInProgress = "DOWNLOAD_IN_PROGRESS"
    case filesystemStable = "FILESYSTEM_STABLE"
    case contentVerified = "CONTENT_VERIFIED"
    case finalized = "FINALIZED"
}

public enum ActionRiskClass: String, Codable, Sendable {
    case reversibleNavigation = "REVERSIBLE_NAVIGATION"
    case preSideEffectAction = "PRE_SIDE_EFFECT_ACTION"
    case irreversibleSideEffect = "IRREVERSIBLE_SIDE_EFFECT"
}

public enum ExecutionPolicyError: Error, Equatable, Sendable {
    case invalidTransition(from: ExecutionState, to: ExecutionState)
    case reversibleBudgetExhausted
    case identicalBlockerBudgetExhausted
    case candidateRevalidationExhausted
    case saveAllAlreadyDispatched
    case destinationAlreadyConfirmed
}

public enum ExecutionStateMachine {
    private static let order: [ExecutionState] = ExecutionState.allCases

    public static func validateTransition(from: ExecutionState, to: ExecutionState) throws {
        guard let index = order.firstIndex(of: from),
              index + 1 < order.count,
              order[index + 1] == to else {
            throw ExecutionPolicyError.invalidTransition(from: from, to: to)
        }
    }
}

public struct LiveDispatchBudget: Equatable, Codable, Sendable {
    public private(set) var reversibleDispatches = 0
    public private(set) var saveAllDispatches = 0
    public private(set) var destinationConfirmations = 0
    public private(set) var identicalBlockerRecoveries: [String: Int] = [:]
    public private(set) var consecutiveCandidateRevalidationFailures = 0

    public init() {}

    public mutating func consumeReversible(blockerKey: String? = nil) throws {
        guard reversibleDispatches < 12 else { throw ExecutionPolicyError.reversibleBudgetExhausted }
        if let blockerKey {
            let count = identicalBlockerRecoveries[blockerKey, default: 0]
            guard count < 3 else { throw ExecutionPolicyError.identicalBlockerBudgetExhausted }
            identicalBlockerRecoveries[blockerKey] = count + 1
        }
        reversibleDispatches += 1
    }

    public mutating func recordCandidateRevalidation(_ passed: Bool) throws {
        if passed {
            consecutiveCandidateRevalidationFailures = 0
            return
        }
        consecutiveCandidateRevalidationFailures += 1
        if consecutiveCandidateRevalidationFailures >= 2 {
            throw ExecutionPolicyError.candidateRevalidationExhausted
        }
    }

    public mutating func consumeSaveAll() throws {
        guard saveAllDispatches == 0 else { throw ExecutionPolicyError.saveAllAlreadyDispatched }
        saveAllDispatches = 1
    }

    public mutating func consumeDestinationConfirmation() throws {
        guard destinationConfirmations == 0 else { throw ExecutionPolicyError.destinationAlreadyConfirmed }
        destinationConfirmations = 1
    }
}
