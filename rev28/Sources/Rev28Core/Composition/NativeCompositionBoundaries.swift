import CoreGraphics
import Foundation

// MARK: - Native composition boundaries (plan R4 §C2)
//
// The common composition, state machine, gate evaluator, evidence validator and
// transaction authority live in Rev28Core. Only these OS-edge protocols are
// substituted by tests (injected sensors, clock, filesystem and event sink);
// substitutions below perception/predicate/state/intent decisions never change
// the state machine or the authority.

public protocol CompositionClock: Sendable {
    func monotonicNow() -> Double
    func sleep(seconds: Double) async
}

public struct SystemCompositionClock: CompositionClock {
    public init() {}

    public func monotonicNow() -> Double {
        ProcessInfo.processInfo.systemUptime
    }

    public func sleep(seconds: Double) async {
        try? await Task.sleep(nanoseconds: UInt64(max(0, seconds) * 1_000_000_000))
    }
}

/// Raw event-posting edge. The gated actuator always runs in common code; this
/// only decides whether a created event reaches the system.
public protocol ActuationBoundary: Sendable {
    func readinessObservation(identity: WindowIdentity, candidate: StructuralCandidate) async throws -> ReadinessObservation
    func revalidateDispatch(pid: Int32, windowID: UInt32, binding: SurfaceBinding) -> Bool
    func processStable(pid: Int32, binding: SurfaceBinding) -> Bool
    func postEventAccess() -> Bool
    func clickSink() -> @Sendable (CGEvent, CGEventTapLocation) -> Void
}

public enum DestinationPrimitive: String, Codable, Sendable, CaseIterable {
    case goToFolderChord
    case pathEntry
    case navigationReturn
}

public protocol ChooserBoundary: Sendable {
    /// One input-free postcondition sample. The boundary may fail, but it can
    /// never manufacture an affirmation: the strict monitor owns the verdict.
    func sample(
        preDispatchInventory: ObservationInventorySnapshot,
        predicate: ChooserAffirmationPredicate
    ) async -> StrictPostconditionObservation

    /// Fresh identity/ownership check for the affirmed panel before every
    /// subsequent primitive and before confirmation.
    func panelStillBound(pid: Int32, confirmation: ChooserAffirmation) -> Bool

    func preparePrimitive(_ primitive: DestinationPrimitive, pid: Int32, destination: URL) throws -> [String: String]
    func destinationReflected(pid: Int32, destination: URL) -> Bool
    func pressDefaultButton(pid: Int32, confirmation: ChooserAffirmation) throws -> String
    func chooserClosed(pid: Int32) -> Bool
}

public protocol FilesystemBoundary: Sendable {
    func stagingSnapshot(directory: URL, observedAt: Double) throws -> StagingSnapshot
    func directoryExists(_ url: URL) -> Bool
    func verifyBaseline(referenceFile: URL) throws -> BaselineVerificationResult
}

public struct NativeAdapterConfiguration: Sendable {
    public let targetBundleID: String
    public let targetGroup: String
    public let targetAlbumTitle: String
    public let targetAlbumCardCountText: String
    public let targetPhotoCountText: String
    public let stagingRunDirectory: URL
    public let baselineReferenceFileURL: URL
    public let chooserPredicate: ChooserAffirmationPredicate
    public let captureTimeoutSeconds: Double
    public let stagingSnapshotIntervalSeconds: Double
    public let downloadObservationLimitSeconds: Double
    public let menuReferenceRows: [String]

    public init(
        targetBundleID: String,
        targetGroup: String,
        targetAlbumTitle: String,
        targetAlbumCardCountText: String,
        targetPhotoCountText: String,
        stagingRunDirectory: URL,
        baselineReferenceFileURL: URL,
        chooserPredicate: ChooserAffirmationPredicate,
        captureTimeoutSeconds: Double = 10,
        stagingSnapshotIntervalSeconds: Double = 1,
        downloadObservationLimitSeconds: Double = 600,
        menuReferenceRows: [String] = StructuralLocators.lineAlbumMenuReference
    ) {
        self.targetBundleID = targetBundleID
        self.targetGroup = targetGroup
        self.targetAlbumTitle = targetAlbumTitle
        self.targetAlbumCardCountText = targetAlbumCardCountText
        self.targetPhotoCountText = targetPhotoCountText
        self.stagingRunDirectory = stagingRunDirectory
        self.baselineReferenceFileURL = baselineReferenceFileURL
        self.chooserPredicate = chooserPredicate
        self.captureTimeoutSeconds = captureTimeoutSeconds
        self.stagingSnapshotIntervalSeconds = stagingSnapshotIntervalSeconds
        self.downloadObservationLimitSeconds = downloadObservationLimitSeconds
        self.menuReferenceRows = menuReferenceRows
    }
}

public enum NativeAdapterError: Error, Equatable, CustomStringConvertible {
    case notAPreSaveState(String)
    case stateRefused(state: String, reason: String)
    case chooserTerminal(String)
    case destinationRefused(String)
    case stagingTerminal(String)
    case baselineRefused(String)
    case dispatchRefused(String)
    case precondition(String)

    public var description: String {
        switch self {
        case let .notAPreSaveState(state): return "notAPreSaveState(\(state))"
        case let .stateRefused(state, reason): return "stateRefused(\(state): \(reason))"
        case let .chooserTerminal(outcome): return "chooserTerminal(\(outcome))"
        case let .destinationRefused(reason): return "destinationRefused(\(reason))"
        case let .stagingTerminal(reason): return "stagingTerminal(\(reason))"
        case let .baselineRefused(reason): return "baselineRefused(\(reason))"
        case let .dispatchRefused(reason): return "dispatchRefused(\(reason))"
        case let .precondition(reason): return "precondition(\(reason))"
        }
    }
}
