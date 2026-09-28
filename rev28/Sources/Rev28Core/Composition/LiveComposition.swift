import CoreGraphics
import Foundation

// MARK: - Live composition (C2/C3 assembly of the reviewed parts)
//
// One factory assembles the durable transaction authority, the serialized
// observation session and the common engine, so `live-preflight` and
// `live-execute` cannot drift apart. Every input is validated fail-closed
// before the first observation: the composition either exists as reviewed or
// it refuses without touching the target.

public enum LiveCompositionError: Error, Equatable, CustomStringConvertible {
    case invalidObservationBudget(UInt64)
    case missingFrozenGeometryRule(stateKey: String, ruleID: String)
    case invalidFrozenGeometryRule(stateKey: String, detail: String)
    case invalidLocatorGeometry(String)
    case epochAuthorityStopped(String)

    public var description: String {
        switch self {
        case let .invalidObservationBudget(budget):
            return "invalidObservationBudget(\(budget))"
        case let .missingFrozenGeometryRule(stateKey, ruleID):
            return "missingFrozenGeometryRule(stateKey=\(stateKey), ruleID=\(ruleID))"
        case let .invalidFrozenGeometryRule(stateKey, detail):
            return "invalidFrozenGeometryRule(stateKey=\(stateKey), detail=\(detail))"
        case let .invalidLocatorGeometry(detail):
            return "invalidLocatorGeometry(\(detail))"
        case let .epochAuthorityStopped(detail):
            return "epochAuthorityStopped(\(detail))"
        }
    }
}

public struct LiveCompositionConfiguration: Codable, Equatable, Sendable {
    /// Absolute observation budget per state, in the source's monotonic domain.
    public let observationBudgetNanos: UInt64
    public let captureConfiguration: CaptureConfiguration
    public let geometryState: CaptureGeometryState
    public let geometryRuleBook: CaptureGeometryRuleBook
    /// Frozen menu-surface geometry in capture pixels; absent geometry is a
    /// configuration error, never a derived band.
    public let menuBoundsCapture: CGRect
    public let addressableBoundsCapture: CGRect

    public init(
        observationBudgetNanos: UInt64,
        captureConfiguration: CaptureConfiguration,
        geometryState: CaptureGeometryState,
        geometryRuleBook: CaptureGeometryRuleBook,
        menuBoundsCapture: CGRect,
        addressableBoundsCapture: CGRect
    ) {
        self.observationBudgetNanos = observationBudgetNanos
        self.captureConfiguration = captureConfiguration
        self.geometryState = geometryState
        self.geometryRuleBook = geometryRuleBook
        self.menuBoundsCapture = menuBoundsCapture
        self.addressableBoundsCapture = addressableBoundsCapture
    }
}

public struct LiveComposition {
    public let owner: PersistentTransactionOwner
    public let engine: LiveExecutionEngine
    public let adapter: ComposedNativeAdapter
    public let session: NativeObservationSession
    public let epochAuthority: RunEpochAuthority

    public init(
        owner: PersistentTransactionOwner,
        engine: LiveExecutionEngine,
        adapter: ComposedNativeAdapter,
        session: NativeObservationSession,
        epochAuthority: RunEpochAuthority
    ) {
        self.owner = owner
        self.engine = engine
        self.adapter = adapter
        self.session = session
        self.epochAuthority = epochAuthority
    }
}

public enum LiveCompositionFactory {
    public static let minimumObservationBudgetNanos: UInt64 = 1_000_000
    public static let maximumObservationBudgetNanos: UInt64 = 120_000_000_000

    /// Validates the frozen configuration and assembles the composition around
    /// one observation source and one actuation environment.
    public static func make(
        authorization: ImmutableRunAuthorization,
        ledgerURL: URL,
        checkpointURL: URL,
        goalSlotDirectory: URL? = nil,
        configuration: LiveCompositionConfiguration,
        target: ObservationTarget,
        source: any ObservationSource,
        environment: any ActuationEnvironment,
        ocr: any OcrPerforming = VisionOcrEngine(),
        sessionID: String,
        requireCheckpointOnResume: Bool = true
    ) throws -> LiveComposition {
        try validate(configuration)
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: try IntentLedger(fileURL: ledgerURL),
            checkpointURL: checkpointURL,
            goalSlotDirectory: goalSlotDirectory,
            requireCheckpointOnResume: requireCheckpointOnResume
        )
        let session = NativeObservationSession(sessionID: sessionID, source: source, ocr: ocr)
        let adapter = ComposedNativeAdapter(
            session: session,
            environment: environment,
            configuration: ComposedAdapterConfiguration(
                target: target,
                captureConfiguration: configuration.captureConfiguration,
                geometryState: configuration.geometryState,
                observationBudgetNanos: configuration.observationBudgetNanos,
                menuBoundsCapture: configuration.menuBoundsCapture,
                addressableBoundsCapture: configuration.addressableBoundsCapture
            )
        )
        return LiveComposition(
            owner: owner,
            engine: LiveExecutionEngine(owner: owner, adapter: adapter),
            adapter: adapter,
            session: session,
            epochAuthority: try RunEpochAuthority(
                evidenceRunDirectory: URL(fileURLWithPath: authorization.evidenceRunDirectory)
            )
        )
    }

    /// Fail-closed configuration validation. The frozen rule for the configured
    /// geometry state must exist, so an uncalibrated device refuses before the
    /// first capture instead of producing INVALID frames at the boundary.
    public static func validate(_ configuration: LiveCompositionConfiguration) throws {
        let budget = configuration.observationBudgetNanos
        guard budget >= minimumObservationBudgetNanos, budget <= maximumObservationBudgetNanos else {
            throw LiveCompositionError.invalidObservationBudget(budget)
        }
        let stateKey = CaptureGeometryRules.stateKey(configuration.geometryState)
        guard let rule = configuration.geometryRuleBook.rule(for: configuration.geometryState) else {
            throw LiveCompositionError.missingFrozenGeometryRule(
                stateKey: stateKey,
                ruleID: configuration.geometryRuleBook.ruleID
            )
        }
        guard rule.maxPerSideSizeDeltaPt >= 0,
              rule.maxOriginPaddingPt >= 0,
              rule.originPaddingPt >= 0,
              rule.originPaddingPt <= rule.maxOriginPaddingPt else {
            throw LiveCompositionError.invalidFrozenGeometryRule(
                stateKey: stateKey,
                detail: "negative tolerance/padding or padding outside its bound"
            )
        }
        guard configuration.menuBoundsCapture.width > 0,
              configuration.menuBoundsCapture.height > 0 else {
            throw LiveCompositionError.invalidLocatorGeometry("menu bounds must have a positive size")
        }
        guard configuration.addressableBoundsCapture.width > 0,
              configuration.addressableBoundsCapture.height > 0 else {
            throw LiveCompositionError.invalidLocatorGeometry("addressable bounds must have a positive size")
        }
    }
}
