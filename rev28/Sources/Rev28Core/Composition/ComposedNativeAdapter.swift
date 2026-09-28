import CoreGraphics
import Foundation

// MARK: - C2/C5 native composition
//
// The composed adapter is the only production bridge between the common engine
// and the sensors. Each state is established from one freshly captured bundle;
// at most one guarded reversible recovery action may be attempted per state,
// and every artifact it hands back is a projection of that bundle.

public enum ComposedAdapterError: Error, Equatable, CustomStringConvertible {
    case stateRefused(state: String, detail: String)
    case recoveryRefused(state: String, detail: String)
    case capabilityNotBuilt(String)

    public var description: String {
        switch self {
        case let .stateRefused(state, detail):
            return "stateRefused(state=\(state), detail=\(detail))"
        case let .recoveryRefused(state, detail):
            return "recoveryRefused(state=\(state), detail=\(detail))"
        case let .capabilityNotBuilt(stage):
            return "capabilityNotBuilt(\(stage))"
        }
    }
}

/// OS-boundary seam for the composed adapter: focus facts and event posting.
/// Real implementations call NSWorkspace/CGEvent through GatedQuartzActuator;
/// tests substitute below predicate/state decisions and record what was posted.
public protocol ActuationEnvironment: Sendable {
    func applicationActive(pid: Int32) -> Bool
    func targetFrontmost(pid: Int32) -> Bool
    func uptime() -> Double
    /// Fresh live readiness facts for one candidate, captured by the OS seam:
    /// production reads SCK/CG/process facts; tests substitute the observation.
    func readinessObservation(identity: WindowIdentity, candidate: StructuralCandidate) async throws -> ReadinessObservation
    func postReversibleClick(
        permit: ReadinessPermit,
        binding: SurfaceBinding,
        owner: PersistentTransactionOwner,
        action: String,
        postHoverRevalidation: @escaping @Sendable () async throws -> Void
    ) async throws
}

public struct ComposedAdapterConfiguration: Sendable {
    public let target: ObservationTarget
    public let captureConfiguration: CaptureConfiguration
    public let geometryState: CaptureGeometryState
    public let observationBudgetNanos: UInt64
    /// Frozen menu-surface geometry in capture pixels for the Save All row
    /// locator. Absent geometry refuses SAVE_ALL_LOCATED rather than deriving
    /// a caller-wide band from the row bands themselves.
    public let menuBoundsCapture: CGRect?
    public let addressableBoundsCapture: CGRect?
    /// Frozen/derived production chooser predicate (plan C6). The composition
    /// never edits frozen artifacts; it only evaluates with them.
    public let chooserPredicate: ChooserAffirmationPredicate
    public let baselineReferenceFile: URL

    public init(
        target: ObservationTarget,
        captureConfiguration: CaptureConfiguration = .primaryWindow,
        geometryState: CaptureGeometryState,
        observationBudgetNanos: UInt64,
        menuBoundsCapture: CGRect? = nil,
        addressableBoundsCapture: CGRect? = nil,
        chooserPredicate: ChooserAffirmationPredicate,
        baselineReferenceFile: URL
    ) {
        self.target = target
        self.captureConfiguration = captureConfiguration
        self.geometryState = geometryState
        self.observationBudgetNanos = observationBudgetNanos
        self.menuBoundsCapture = menuBoundsCapture
        self.addressableBoundsCapture = addressableBoundsCapture
        self.chooserPredicate = chooserPredicate
        self.baselineReferenceFile = baselineReferenceFile
    }
}

public struct ComposedNativeAdapter: LiveExecutionAdapter, Sendable {
    public static let albumTitle = "2024/05/13~05/17"
    public static let albumCount = "57"
    public static let albumDetailCountText = "57張照片"

    let session: NativeObservationSession
    let environment: any ActuationEnvironment
    let configuration: ComposedAdapterConfiguration
    let postSave: any PostSaveEnvironment
    let phaseBEligibility: PhaseBEligibilityArtifact?
    let phaseBEligibilityRecomputation: PhaseBEligibilityRecomputation?
    let journalBox = PostSaveJournalBox()

    public init(
        session: NativeObservationSession,
        environment: any ActuationEnvironment,
        configuration: ComposedAdapterConfiguration,
        postSave: any PostSaveEnvironment,
        phaseBEligibility: PhaseBEligibilityArtifact?,
        phaseBEligibilityRecomputation: PhaseBEligibilityRecomputation? = nil
    ) {
        self.session = session
        self.environment = environment
        self.configuration = configuration
        self.postSave = postSave
        self.phaseBEligibility = phaseBEligibility
        self.phaseBEligibilityRecomputation = phaseBEligibilityRecomputation
    }

    // MARK: - LiveExecutionAdapter

    public func establish(state: ExecutionState, owner: PersistentTransactionOwner) async throws -> EstablishedStateEvidence {
        switch state {
        case .albumDetailVerified:
            // The album detail only becomes true after exactly one reversible
            // open-album-card navigation; its proof bundle is observed with no
            // structural request, so the artifact can never smuggle a click
            // candidate into the state that authorizes navigation.
            return try await establishWithSingleRecovery(
                state: state,
                owner: owner,
                probe: .albumCards(title: Self.albumTitle, count: Self.albumCount),
                recoveryAction: "open-album-card"
            )
        case .menuVerified:
            return try await establishWithSingleRecovery(
                state: state,
                owner: owner,
                probe: .albumEllipsis(title: Self.albumTitle, groupTitle: LiveExecutionEngine.targetGroup),
                recoveryAction: "open-album-menu"
            )
        default:
            let bundle = try await observe(state: state, owner: owner, localization: localization(for: state))
            guard try evaluate(state: state, bundle: bundle) else {
                throw ComposedAdapterError.stateRefused(
                    state: state.rawValue,
                    detail: "fresh observation does not establish this state"
                )
            }
            return try persist(bundle: bundle, owner: owner)
        }
    }

    /// Verify first from a fresh observation; when the state does not hold,
    /// locate one structural candidate on the current surface, post at most one
    /// guarded reversible navigation, and re-verify from a new observation. The
    /// re-verification bundle is the only one that can become evidence.
    private func establishWithSingleRecovery(
        state: ExecutionState,
        owner: PersistentTransactionOwner,
        probe: ObservationLocalization,
        recoveryAction: String
    ) async throws -> EstablishedStateEvidence {
        let direct = try await observe(state: state, owner: owner, localization: .none)
        if try evaluate(state: state, bundle: direct) {
            return try persist(bundle: direct, owner: owner)
        }
        let probeBundle = try await observe(state: state, owner: owner, localization: probe)
        guard let candidate = probeBundle.candidate else {
            throw ComposedAdapterError.stateRefused(
                state: state.rawValue,
                detail: "no reversible structural candidate is available to recover this state"
            )
        }
        try await postReversibleClick(candidate: candidate, bundle: probeBundle, owner: owner, action: recoveryAction)
        let reVerified = try await observe(state: state, owner: owner, localization: .none)
        guard try evaluate(state: state, bundle: reVerified) else {
            throw ComposedAdapterError.stateRefused(
                state: state.rawValue,
                detail: "state is not established after one guarded reversible recovery"
            )
        }
        return try persist(bundle: reVerified, owner: owner)
    }

    // MARK: - State plans

    func localization(for state: ExecutionState) -> ObservationLocalization {
        switch state {
        case .appReady, .groupReady, .albumListReady, .albumDetailVerified, .menuVerified:
            return .none
        case .targetAlbumLocated:
            return .albumCards(title: Self.albumTitle, count: Self.albumCount)
        case .ellipsisLocated:
            return .albumEllipsis(title: Self.albumTitle, groupTitle: LiveExecutionEngine.targetGroup)
        case .saveAllLocated:
            guard let menuBounds = configuration.menuBoundsCapture,
                  let addressable = configuration.addressableBoundsCapture else {
                return .none
            }
            return .saveAllMenuRows(menuBounds: menuBounds, addressableBounds: addressable)
        default:
            return .none
        }
    }

    /// One fresh retained observation bundle for `state`. Internal so the
    /// post-Save-All capabilities share the exact same session/freshness path.
    func observe(
        state: ExecutionState,
        owner: PersistentTransactionOwner,
        localization: ObservationLocalization
    ) async throws -> ObservationBundle {
        let request = NativeObservationRequest(
            runID: owner.authorization.runID,
            state: state,
            target: configuration.target,
            configuration: configuration.captureConfiguration,
            geometryState: configuration.geometryState,
            localization: localization,
            observationBudgetNanos: configuration.observationBudgetNanos
        )
        return try await session.capture(request)
    }

    func evaluate(state: ExecutionState, bundle: ObservationBundle) throws -> Bool {
        switch state {
        case .appReady:
            guard environment.applicationActive(pid: configuration.target.pid),
                  environment.targetFrontmost(pid: configuration.target.pid) else {
                throw ComposedAdapterError.stateRefused(
                    state: state.rawValue,
                    detail: "target application is not active and frontmost"
                )
            }
            return true
        case .groupReady:
            return bundle.ocrItems.contains { $0.text == LiveExecutionEngine.targetGroup }
        case .albumListReady:
            return !StructuralLocators.segmentAlbumCards(
                items: bundle.ocrItems,
                imageBounds: Self.imageBounds(of: bundle)
            ).isEmpty
        case .targetAlbumLocated:
            return bundle.candidate != nil
        case .albumDetailVerified:
            let texts = Set(bundle.ocrItems.map(\.text))
            return texts.contains(LiveExecutionEngine.targetGroup) && texts.contains(Self.albumDetailCountText)
        case .ellipsisLocated:
            return bundle.candidate != nil
        case .menuVerified:
            let texts = Set(bundle.ocrItems.map(\.text))
            return StructuralLocators.lineAlbumMenuReference.allSatisfy { texts.contains($0) }
        case .saveAllLocated:
            guard configuration.menuBoundsCapture != nil else {
                throw ComposedAdapterError.stateRefused(
                    state: state.rawValue,
                    detail: "frozen menu-surface geometry is not calibrated"
                )
            }
            return bundle.candidate?.identity == "儲存全部"
        default:
            throw ComposedAdapterError.stateRefused(
                state: state.rawValue,
                detail: "state is not part of the pre-Save-All composition"
            )
        }
    }

    private func postReversibleClick(
        candidate: StructuralCandidate,
        bundle: ObservationBundle,
        owner: PersistentTransactionOwner,
        action: String
    ) async throws {
        guard candidate.identity != "儲存全部" else {
            throw ComposedAdapterError.recoveryRefused(
                state: bundle.state.rawValue,
                detail: "Save All candidate cannot be clicked reversibly"
            )
        }
        // Freshness facts are projections of the same retained bundle: the
        // post-capture inventory the session already validated, never
        // caller-authored flags.
        guard let post = bundle.postInventory.first(where: { $0.windowID == bundle.window.windowID }),
              post.ownerPID == bundle.process.pid else {
            throw ComposedAdapterError.recoveryRefused(
                state: bundle.state.rawValue,
                detail: "post-capture inventory lost the target window"
            )
        }
        let observation = ReadinessObservation(
            applicationActive: environment.applicationActive(pid: configuration.target.pid),
            targetFrontmost: environment.targetFrontmost(pid: configuration.target.pid),
            freshWindow: FreshWindowObservation(
                bundleID: post.ownerBundleID ?? "",
                process: bundle.process,
                windowID: post.windowID,
                frame: post.frame,
                layer: post.windowLayer,
                isOnScreen: post.isOnScreen
            ),
            currentEpoch: bundle.epoch,
            currentBinding: bundle.surfaceBinding,
            captureGeometry: CaptureGeometry(
                windowFrame: bundle.window.windowFrame,
                captureBBox: bundle.frame.actualBBoxPt,
                scale: bundle.frame.scale
            ),
            captureImageSize: CGSize(width: bundle.frame.imageWidthPx, height: bundle.frame.imageHeightPx),
            observedAtUptime: environment.uptime()
        )
        let permit = try DispatchReadinessGate.mintPermit(
            identity: bundle.window,
            candidate: candidate,
            observation: observation,
            now: environment.uptime()
        )
        // Plan C5: the post-hover revalidation re-runs the fresh live
        // observation path and requires it to still match the permit's bound
        // candidate/window/geometry before mouseDown.
        let revalidation: @Sendable () async throws -> Void = { [environment] in
            let fresh = try await environment.readinessObservation(identity: bundle.window, candidate: candidate)
            try DispatchReadinessGate.revalidateAfterHover(
                permit: permit,
                freshObservation: fresh,
                now: environment.uptime()
            )
        }
        try await environment.postReversibleClick(
            permit: permit,
            binding: bundle.surfaceBinding,
            owner: owner,
            action: action,
            postHoverRevalidation: revalidation
        )
    }

    private func persist(
        bundle: ObservationBundle,
        owner: PersistentTransactionOwner
    ) throws -> EstablishedStateEvidence {
        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let frameName = "state-\(bundle.state.rawValue)-\(bundle.epoch).png"
        let artifactName = "state-\(bundle.state.rawValue)-\(bundle.epoch).json"
        try bundle.framePNGData.write(to: runDirectory.appendingPathComponent(frameName))
        let artifact = StateEvidenceArtifact(bundle: bundle, retainedFrameName: frameName)
        let artifactData = try JSONEncoder().encode(artifact)
        try artifactData.write(to: runDirectory.appendingPathComponent(artifactName))
        return EstablishedStateEvidence(
            artifactName: artifactName,
            evidenceSHA256: EvidenceIO.sha256Hex(artifactData),
            artifact: artifact
        )
    }

    static func imageBounds(of bundle: ObservationBundle) -> CGRect {
        CGRect(
            origin: .zero,
            size: CGSize(width: bundle.frame.imageWidthPx, height: bundle.frame.imageHeightPx)
        )
    }
}
