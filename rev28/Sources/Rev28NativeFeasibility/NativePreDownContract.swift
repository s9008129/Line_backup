import Foundation

/// F0 is deliberately pure: it models admission and audit facts without owning
/// a transaction, posting an event, or creating a second authority.
public enum AdmissionContext: String, CaseIterable, Sendable {
    case production
    case controlledFeasibility
}

public enum TargetKind: String, CaseIterable, Sendable {
    case albumCard
    case menuTrigger
    case saveAll
}

public enum ConstructedEventKind: String, CaseIterable, Sendable {
    case mouseMoved
    case leftMouseDown
    case leftMouseUp
}

public enum AdmissionPhase: String, CaseIterable, Sendable {
    case beforeHover
    case afterHover
}

public enum TerminalState: String, CaseIterable, Sendable {
    case refusedZeroEvent = "REFUSED_ZERO_EVENT"
    case refusedZeroClick = "REFUSED_ZERO_CLICK"
    case unknownLatchedNoReplay = "UNKNOWN_LATCHED_NO_REPLAY"
}

public enum EvidenceStatus: String, CaseIterable, Sendable {
    case present = "PRESENT"
    case absent = "ABSENT"
    case mismatch = "MISMATCH"
}

public struct ContractPoint: Equatable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public var isFinite: Bool { x.isFinite && y.isFinite }

    public func distance(to other: ContractPoint) -> Double {
        hypot(x - other.x, y - other.y)
    }
}

public struct ContractRect: Equatable, Sendable {
    public var x: Double
    public var y: Double
    public var width: Double
    public var height: Double

    public init(x: Double, y: Double, width: Double, height: Double) {
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    }

    public var maxX: Double { x + width }
    public var maxY: Double { y + height }
    public var center: ContractPoint { ContractPoint(x: x + width / 2, y: y + height / 2) }

    public var isFinite: Bool {
        x.isFinite && y.isFinite && width.isFinite && height.isFinite
            && width >= 0 && height >= 0
    }

    public func contains(_ point: ContractPoint, epsilon: Double = 1e-9) -> Bool {
        point.x >= x - epsilon && point.x <= maxX + epsilon
            && point.y >= y - epsilon && point.y <= maxY + epsilon
    }

    public func insetBy(dx: Double, dy: Double) -> ContractRect {
        ContractRect(
            x: x + dx,
            y: y + dy,
            width: max(0, width - 2 * dx),
            height: max(0, height - 2 * dy)
        )
    }
}

public struct ContractFailure: Equatable, Sendable {
    public let code: String
    public let detail: String

    public init(code: String, detail: String) {
        self.code = code
        self.detail = detail
    }
}

public struct TargetGeometry: Equatable, Sendable {
    public let kind: TargetKind
    public let witnessRectPx: ContractRect
    public let uncertaintyPx: Double
    public let selectedPointPx: ContractPoint
    public let uniqueWitness: Bool
    public let hitTestProbeCount: Int

    public init(
        kind: TargetKind,
        witnessRectPx: ContractRect,
        uncertaintyPx: Double,
        selectedPointPx: ContractPoint,
        uniqueWitness: Bool,
        hitTestProbeCount: Int
    ) {
        self.kind = kind
        self.witnessRectPx = witnessRectPx
        self.uncertaintyPx = uncertaintyPx
        self.selectedPointPx = selectedPointPx
        self.uniqueWitness = uniqueWitness
        self.hitTestProbeCount = hitTestProbeCount
    }
}

public struct TargetGeometryValidation: Equatable, Sendable {
    public let admissibleRectPx: ContractRect?
    public let failures: [ContractFailure]

    public var isValid: Bool { failures.isEmpty && admissibleRectPx != nil }
}

public struct CaptureGeometry: Equatable, Sendable {
    public let windowFramePt: ContractRect
    public let captureBBoxPt: ContractRect
    public let scale: Double

    public init(windowFramePt: ContractRect, captureBBoxPt: ContractRect, scale: Double) {
        self.windowFramePt = windowFramePt
        self.captureBBoxPt = captureBBoxPt
        self.scale = scale
    }

    public func capturePoint(fromScreen screenPoint: ContractPoint) -> ContractPoint {
        ContractPoint(
            x: (screenPoint.x - captureBBoxPt.x) * scale,
            y: (screenPoint.y - captureBBoxPt.y) * scale
        )
    }

    public func screenPoint(fromCapture capturePoint: ContractPoint) -> ContractPoint {
        ContractPoint(
            x: captureBBoxPt.x + capturePoint.x / scale,
            y: captureBBoxPt.y + capturePoint.y / scale
        )
    }
}

public struct RuntimeBinding: Equatable, Sendable {
    public let planSHA256: String
    public let sourceSHA256: String
    public let runtimeSHA256: String
    public let reviewBinding: String

    public init(planSHA256: String, sourceSHA256: String, runtimeSHA256: String, reviewBinding: String) {
        self.planSHA256 = planSHA256
        self.sourceSHA256 = sourceSHA256
        self.runtimeSHA256 = runtimeSHA256
        self.reviewBinding = reviewBinding
    }
}

public struct ProcessBinding: Equatable, Sendable {
    public let pid: Int32
    public let processInstanceToken: String
    public let bundleID: String

    public init(pid: Int32, processInstanceToken: String, bundleID: String) {
        self.pid = pid
        self.processInstanceToken = processInstanceToken
        self.bundleID = bundleID
    }
}

public struct WindowBinding: Equatable, Sendable {
    public let windowID: UInt32
    public let layer: Int
    public let framePt: ContractRect

    public init(windowID: UInt32, layer: Int, framePt: ContractRect) {
        self.windowID = windowID
        self.layer = layer
        self.framePt = framePt
    }
}

public struct DisplayBinding: Equatable, Sendable {
    public let displayID: UInt32
    public let scale: Double

    public init(displayID: UInt32, scale: Double) {
        self.displayID = displayID
        self.scale = scale
    }
}

public struct SurfaceEvidence: Equatable, Sendable {
    public let expectedWindowID: UInt32
    public let observedTopmostWindowID: UInt32
    public let expectedLayer: Int
    public let observedLayer: Int
    public let alpha: Double
    public let isOnScreen: Bool
    public let noAmbiguousWindowAbove: Bool

    public init(
        expectedWindowID: UInt32,
        observedTopmostWindowID: UInt32,
        expectedLayer: Int,
        observedLayer: Int,
        alpha: Double,
        isOnScreen: Bool,
        noAmbiguousWindowAbove: Bool
    ) {
        self.expectedWindowID = expectedWindowID
        self.observedTopmostWindowID = observedTopmostWindowID
        self.expectedLayer = expectedLayer
        self.observedLayer = observedLayer
        self.alpha = alpha
        self.isOnScreen = isOnScreen
        self.noAmbiguousWindowAbove = noAmbiguousWindowAbove
    }
}

public struct HitTestEvidence: Equatable, Sendable {
    public let selectedPointIdentifiesTarget: Bool
    public let allUncertaintyProbesIdentifyTarget: Bool
    public let probeCount: Int

    public init(
        selectedPointIdentifiesTarget: Bool,
        allUncertaintyProbesIdentifyTarget: Bool,
        probeCount: Int
    ) {
        self.selectedPointIdentifiesTarget = selectedPointIdentifiesTarget
        self.allUncertaintyProbesIdentifyTarget = allUncertaintyProbesIdentifyTarget
        self.probeCount = probeCount
    }
}

public struct AuthorizationBinding: Equatable, Sendable {
    public let authority: String
    public let authorizationID: String
    public let intentRevision: String
    public let targetBindingSHA256: String
    public let singleUse: Bool
    public let consumed: Bool
    public let expiresAtMonotonic: Double

    public init(
        authority: String,
        authorizationID: String,
        intentRevision: String,
        targetBindingSHA256: String,
        singleUse: Bool,
        consumed: Bool,
        expiresAtMonotonic: Double
    ) {
        self.authority = authority
        self.authorizationID = authorizationID
        self.intentRevision = intentRevision
        self.targetBindingSHA256 = targetBindingSHA256
        self.singleUse = singleUse
        self.consumed = consumed
        self.expiresAtMonotonic = expiresAtMonotonic
    }
}

public struct UncertaintyVector: Equatable, Sendable {
    public let localizePx: Double?
    public let transformPx: Double?
    public let motionPx: Double?
    public let serializePx: Double?
    public let allMeasured: Bool

    public init(
        localizePx: Double?,
        transformPx: Double?,
        motionPx: Double?,
        serializePx: Double?,
        allMeasured: Bool
    ) {
        self.localizePx = localizePx
        self.transformPx = transformPx
        self.motionPx = motionPx
        self.serializePx = serializePx
        self.allMeasured = allMeasured
    }

    public var totalPx: Double? {
        guard let localizePx, let transformPx, let motionPx, let serializePx else { return nil }
        let values = [localizePx, transformPx, motionPx, serializePx]
        guard values.allSatisfy({ $0.isFinite && $0 >= 0 }) else { return nil }
        return values.reduce(0, +)
    }
}

public struct ConstructedEvent: Equatable, Sendable {
    public let kind: ConstructedEventKind
    public let locationScreen: ContractPoint
    public let sourceUserData: UInt64
    public let sourcePIDField: Int32
    public let targetPIDField: Int32

    public init(
        kind: ConstructedEventKind,
        locationScreen: ContractPoint,
        sourceUserData: UInt64,
        sourcePIDField: Int32,
        targetPIDField: Int32
    ) {
        self.kind = kind
        self.locationScreen = locationScreen
        self.sourceUserData = sourceUserData
        self.sourcePIDField = sourcePIDField
        self.targetPIDField = targetPIDField
    }
}

public struct ConstructedEventSet: Equatable, Sendable {
    public let mouseMoved: ConstructedEvent
    public let leftMouseDown: ConstructedEvent
    public let leftMouseUp: ConstructedEvent

    public init(
        mouseMoved: ConstructedEvent,
        leftMouseDown: ConstructedEvent,
        leftMouseUp: ConstructedEvent
    ) {
        self.mouseMoved = mouseMoved
        self.leftMouseDown = leftMouseDown
        self.leftMouseUp = leftMouseUp
    }

    public var orderedEvents: [ConstructedEvent] { [mouseMoved, leftMouseDown, leftMouseUp] }
}

public struct PreDownAdmissionRequest: Equatable, Sendable {
    public let context: AdmissionContext
    public let runtime: RuntimeBinding
    public let targetProcess: ProcessBinding
    public let sourceProcessPID: Int32
    public let targetWindow: WindowBinding
    public let display: DisplayBinding
    public let targetBindingSHA256: String
    public let targetGeometry: TargetGeometry
    public let captureGeometry: CaptureGeometry
    public let requestedCapturePoint: ContractPoint
    public let constructedEvents: ConstructedEventSet
    public let uncertainty: UncertaintyVector
    public let surface: SurfaceEvidence
    public let hitTest: HitTestEvidence
    public let authorization: AuthorizationBinding
    public let nowMonotonic: Double
    public let preDownDeadlineMonotonic: Double

    public init(
        context: AdmissionContext,
        runtime: RuntimeBinding,
        targetProcess: ProcessBinding,
        sourceProcessPID: Int32,
        targetWindow: WindowBinding,
        display: DisplayBinding,
        targetBindingSHA256: String,
        targetGeometry: TargetGeometry,
        captureGeometry: CaptureGeometry,
        requestedCapturePoint: ContractPoint,
        constructedEvents: ConstructedEventSet,
        uncertainty: UncertaintyVector,
        surface: SurfaceEvidence,
        hitTest: HitTestEvidence,
        authorization: AuthorizationBinding,
        nowMonotonic: Double,
        preDownDeadlineMonotonic: Double
    ) {
        self.context = context
        self.runtime = runtime
        self.targetProcess = targetProcess
        self.sourceProcessPID = sourceProcessPID
        self.targetWindow = targetWindow
        self.display = display
        self.targetBindingSHA256 = targetBindingSHA256
        self.targetGeometry = targetGeometry
        self.captureGeometry = captureGeometry
        self.requestedCapturePoint = requestedCapturePoint
        self.constructedEvents = constructedEvents
        self.uncertainty = uncertainty
        self.surface = surface
        self.hitTest = hitTest
        self.authorization = authorization
        self.nowMonotonic = nowMonotonic
        self.preDownDeadlineMonotonic = preDownDeadlineMonotonic
    }
}

public struct PreDownAdmission: Equatable, Sendable {
    public let context: AdmissionContext
    public let runtime: RuntimeBinding
    public let targetProcess: ProcessBinding
    public let sourceProcessPID: Int32
    public let targetWindow: WindowBinding
    public let display: DisplayBinding
    public let targetBindingSHA256: String
    public let targetValidation: TargetGeometryValidation
    public let captureGeometry: CaptureGeometry
    public let requestedScreenPoint: ContractPoint
    public let constructedCapturePoint: ContractPoint
    public let constructionResidualPx: Double
    public let totalUncertaintyPx: Double
    public let constructedEvents: ConstructedEventSet
    public let surface: SurfaceEvidence
    public let hitTest: HitTestEvidence
    public let authorization: AuthorizationBinding
    public let evaluatedAtMonotonic: Double

    /// Only a durable project-ledger authorization can make an admission
    /// production-eligible. The controlled F1 token is evidence-only.
    public var productionEligible: Bool {
        context == .production && authorization.authority == "python_project_ledger"
    }

    public var constructedDownEventCount: Int {
        constructedEvents.orderedEvents.filter { $0.kind == .leftMouseDown }.count
    }

    public var constructedUpEventCount: Int {
        constructedEvents.orderedEvents.filter { $0.kind == .leftMouseUp }.count
    }
}

public struct PreDownRefusal: Equatable, Sendable {
    public let terminal: TerminalState
    public let failures: [ContractFailure]

    public init(terminal: TerminalState, failures: [ContractFailure]) {
        self.terminal = terminal
        self.failures = failures
    }
}

public enum PreDownDecision: Equatable, Sendable {
    case admitted(PreDownAdmission)
    case refused(PreDownRefusal)

    public var dispatchEvents: [ConstructedEvent] {
        guard case let .admitted(admission) = self else { return [] }
        return admission.constructedEvents.orderedEvents
    }
}

public enum TargetGeometryContract {
    public static func validate(_ geometry: TargetGeometry) -> TargetGeometryValidation {
        var failures: [ContractFailure] = []
        let rect = geometry.witnessRectPx
        let uncertainty = geometry.uncertaintyPx

        if !rect.isFinite {
            failures.append(ContractFailure(code: "target_rect_nonfinite", detail: "target witness rect is not finite"))
        }
        if !geometry.selectedPointPx.isFinite {
            failures.append(ContractFailure(code: "selected_point_nonfinite", detail: "selected point is not finite"))
        }
        if !uncertainty.isFinite || uncertainty < 0 {
            failures.append(ContractFailure(code: "target_uncertainty_invalid", detail: "target uncertainty must be finite and non-negative"))
        }
        if !geometry.uniqueWitness {
            failures.append(ContractFailure(code: "target_not_unique", detail: "target-specific witness is not unique"))
        }
        if geometry.hitTestProbeCount < 5 {
            failures.append(ContractFailure(code: "hit_test_probes_insufficient", detail: "selected point plus four uncertainty probes are required"))
        }

        let admissible: ContractRect
        switch geometry.kind {
        case .albumCard:
            if rect.width < 16 {
                failures.append(ContractFailure(code: "album_card_width", detail: "album-card title width must be >= 16px"))
            }
            if rect.height < (2 * uncertainty + 1) {
                failures.append(ContractFailure(code: "album_card_height", detail: "album-card title height must be >= 2u+1px"))
            }
            if geometry.selectedPointPx.distance(to: rect.center) > 1e-9 {
                failures.append(ContractFailure(code: "album_card_center", detail: "album-card click must use the verified title center"))
            }
            admissible = rect
        case .menuTrigger, .saveAll:
            let erosion = uncertainty + 4
            admissible = rect.insetBy(dx: erosion, dy: erosion)
            if admissible.width < 16 || admissible.height < 16 {
                failures.append(ContractFailure(code: "target_safe_rect_16x16", detail: "u+4-eroded target safe rect must be at least 16x16px"))
            }
        }

        if !admissible.contains(geometry.selectedPointPx) {
            failures.append(ContractFailure(code: "selected_point_outside_target", detail: "selected point is outside the target-specific admissible region"))
        }

        return TargetGeometryValidation(
            admissibleRectPx: failures.isEmpty ? admissible : nil,
            failures: failures
        )
    }
}

public enum PreDownContract {
    public static func evaluate(
        _ request: PreDownAdmissionRequest,
        phase: AdmissionPhase
    ) -> PreDownDecision {
        var failures: [ContractFailure] = []

        func requireNonEmpty(_ value: String, code: String, detail: String) {
            if value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                failures.append(ContractFailure(code: code, detail: detail))
            }
        }

        requireNonEmpty(request.runtime.planSHA256, code: "runtime_plan_hash_missing", detail: "Plan SHA-256 is missing")
        requireNonEmpty(request.runtime.sourceSHA256, code: "runtime_source_hash_missing", detail: "source SHA-256 is missing")
        requireNonEmpty(request.runtime.runtimeSHA256, code: "runtime_hash_missing", detail: "runtime SHA-256 is missing")
        requireNonEmpty(request.runtime.reviewBinding, code: "review_binding_missing", detail: "review binding is missing")
        requireNonEmpty(request.targetProcess.processInstanceToken, code: "process_instance_missing", detail: "process-instance token is missing")
        requireNonEmpty(request.targetProcess.bundleID, code: "bundle_id_missing", detail: "bundle id is missing")
        requireNonEmpty(request.targetBindingSHA256, code: "target_binding_missing", detail: "target-binding SHA-256 is missing")

        if request.targetProcess.pid <= 0 || request.sourceProcessPID <= 0 {
            failures.append(ContractFailure(code: "pid_invalid", detail: "source and target PIDs must be positive"))
        }
        if request.targetWindow.windowID == 0 {
            failures.append(ContractFailure(code: "window_id_missing", detail: "target window id is missing"))
        }
        if !request.display.scale.isFinite || request.display.scale <= 0 {
            failures.append(ContractFailure(code: "display_scale_invalid", detail: "display scale must be finite and positive"))
        }
        if !request.captureGeometry.scale.isFinite || request.captureGeometry.scale <= 0
            || !request.captureGeometry.captureBBoxPt.isFinite
            || !request.captureGeometry.windowFramePt.isFinite {
            failures.append(ContractFailure(code: "capture_geometry_invalid", detail: "capture geometry is missing or non-finite"))
        }
        if abs(request.captureGeometry.scale - request.display.scale) > 1e-9 {
            failures.append(ContractFailure(code: "display_scale_mismatch", detail: "capture scale must equal the bound display scale"))
        }

        let targetValidation = TargetGeometryContract.validate(request.targetGeometry)
        failures.append(contentsOf: targetValidation.failures)

        if !request.nowMonotonic.isFinite
            || !request.preDownDeadlineMonotonic.isFinite
            || request.nowMonotonic > request.preDownDeadlineMonotonic {
            failures.append(ContractFailure(code: "pre_down_deadline_expired", detail: "pre-down observation is outside its fixed deadline"))
        }

        let expectedAuthority: String
        switch request.context {
        case .production:
            expectedAuthority = "python_project_ledger"
        case .controlledFeasibility:
            expectedAuthority = "f1_controlled_nontransactional"
        }
        if request.authorization.authority != expectedAuthority {
            failures.append(ContractFailure(code: "authorization_authority_mismatch", detail: "authorization authority does not match the admission context"))
        }
        requireNonEmpty(request.authorization.authorizationID, code: "authorization_id_missing", detail: "authorization id is missing")
        requireNonEmpty(request.authorization.intentRevision, code: "intent_revision_missing", detail: "intent revision is missing")
        requireNonEmpty(request.authorization.targetBindingSHA256, code: "authorization_target_missing", detail: "authorization target binding is missing")
        if request.authorization.targetBindingSHA256 != request.targetBindingSHA256 {
            failures.append(ContractFailure(code: "authorization_target_mismatch", detail: "authorization target binding does not match the admission target"))
        }
        if !request.authorization.singleUse {
            failures.append(ContractFailure(code: "authorization_not_single_use", detail: "authorization is not single-use"))
        }
        if request.authorization.consumed {
            failures.append(ContractFailure(code: "authorization_consumed", detail: "authorization was already consumed"))
        }
        if !request.authorization.expiresAtMonotonic.isFinite
            || request.authorization.expiresAtMonotonic <= request.nowMonotonic {
            failures.append(ContractFailure(code: "authorization_expired", detail: "authorization is absent, stale, or expired"))
        }

        guard let requestedScreenPoint = optionalScreenPoint(for: request),
              let constructedCapturePoint = optionalConstructedCapturePoint(for: request),
              let constructionResidualPx = optionalConstructionResidualPx(for: request),
              let totalUncertaintyPx = request.uncertainty.totalPx else {
            failures.append(ContractFailure(code: "event_or_uncertainty_term_missing", detail: "constructed location or a measured uncertainty term is missing or non-finite"))
            return .refused(refusal(phase: phase, failures: uniqueFailures(failures)))
        }

        if !request.uncertainty.allMeasured {
            failures.append(ContractFailure(code: "uncertainty_not_measured", detail: "every uncertainty term must be measured"))
        }
        if totalUncertaintyPx > 2.0 {
            failures.append(ContractFailure(code: "uncertainty_exceeds_2px", detail: "U_pre_px must be <= 2px"))
        }
        if constructionResidualPx > totalUncertaintyPx {
            failures.append(ContractFailure(code: "constructed_location_outside_bound", detail: "constructed event residual exceeds U_pre_px"))
        }
        if let admissibleRect = targetValidation.admissibleRectPx,
           !admissibleRect.contains(constructedCapturePoint) {
            failures.append(ContractFailure(code: "constructed_location_outside_target", detail: "constructed event location is outside the target-specific region"))
        }
        if !request.captureGeometry.captureBBoxPt.contains(requestedScreenPoint)
            || !request.captureGeometry.windowFramePt.contains(requestedScreenPoint) {
            failures.append(ContractFailure(code: "requested_point_outside_capture", detail: "requested point is outside the frozen capture/window geometry"))
        }

        let events = request.constructedEvents.orderedEvents
        if events.map({ $0.kind }) != [.mouseMoved, .leftMouseDown, .leftMouseUp] {
            failures.append(ContractFailure(code: "constructed_event_order", detail: "constructed sequence must be move, down, up"))
        }
        if events.filter({ $0.kind == .leftMouseDown }).count != 1
            || events.filter({ $0.kind == .leftMouseUp }).count != 1 {
            failures.append(ContractFailure(code: "constructed_event_multiplicity", detail: "exactly one mouseDown and one mouseUp are required"))
        }
        let token = request.constructedEvents.leftMouseDown.sourceUserData
        if token == 0 || events.contains(where: { $0.sourceUserData != token }) {
            failures.append(ContractFailure(code: "source_token_invalid", detail: "a single non-zero source token must be used for the whole sequence"))
        }
        if events.contains(where: { $0.sourcePIDField != request.sourceProcessPID }) {
            failures.append(ContractFailure(code: "source_pid_field_mismatch", detail: "constructed source PID does not match the source process"))
        }
        if events.contains(where: { $0.targetPIDField != request.targetProcess.pid }) {
            failures.append(ContractFailure(code: "target_pid_field_mismatch", detail: "constructed target PID does not match the controlled target"))
        }
        if events.contains(where: { !$0.locationScreen.isFinite })
            || Set(events.map { "\($0.locationScreen.x),\($0.locationScreen.y)" }).count != 1 {
            failures.append(ContractFailure(code: "constructed_event_location_invalid", detail: "move/down/up must carry one finite selected point"))
        }
        if request.surface.expectedWindowID != request.targetWindow.windowID
            || request.surface.observedTopmostWindowID != request.surface.expectedWindowID
            || request.surface.expectedLayer != request.targetWindow.layer
            || request.surface.observedLayer != request.surface.expectedLayer
            || !request.surface.noAmbiguousWindowAbove {
            failures.append(ContractFailure(code: "surface_identity_mismatch", detail: "the exact expected surface is not the unambiguous topmost target"))
        }
        if !request.surface.alpha.isFinite || request.surface.alpha <= 0 || !request.surface.isOnScreen {
            failures.append(ContractFailure(code: "surface_not_addressable", detail: "expected surface is not alpha-positive and on-screen"))
        }
        if !request.hitTest.selectedPointIdentifiesTarget
            || !request.hitTest.allUncertaintyProbesIdentifyTarget
            || request.hitTest.probeCount < 5 {
            failures.append(ContractFailure(code: "hit_test_identity_mismatch", detail: "target identity does not hold across the uncertainty neighborhood"))
        }

        if !failures.isEmpty {
            return .refused(refusal(phase: phase, failures: uniqueFailures(failures)))
        }

        let admission = PreDownAdmission(
            context: request.context,
            runtime: request.runtime,
            targetProcess: request.targetProcess,
            sourceProcessPID: request.sourceProcessPID,
            targetWindow: request.targetWindow,
            display: request.display,
            targetBindingSHA256: request.targetBindingSHA256,
            targetValidation: targetValidation,
            captureGeometry: request.captureGeometry,
            requestedScreenPoint: requestedScreenPoint,
            constructedCapturePoint: constructedCapturePoint,
            constructionResidualPx: constructionResidualPx,
            totalUncertaintyPx: totalUncertaintyPx,
            constructedEvents: request.constructedEvents,
            surface: request.surface,
            hitTest: request.hitTest,
            authorization: request.authorization,
            evaluatedAtMonotonic: request.nowMonotonic
        )
        return .admitted(admission)
    }

    private static func optionalScreenPoint(for request: PreDownAdmissionRequest) -> ContractPoint? {
        guard request.requestedCapturePoint.isFinite else { return nil }
        return request.captureGeometry.screenPoint(fromCapture: request.requestedCapturePoint)
    }

    private static func optionalConstructedCapturePoint(for request: PreDownAdmissionRequest) -> ContractPoint? {
        let downLocation = request.constructedEvents.leftMouseDown.locationScreen
        guard downLocation.isFinite else { return nil }
        return request.captureGeometry.capturePoint(fromScreen: downLocation)
    }

    private static func optionalConstructionResidualPx(for request: PreDownAdmissionRequest) -> Double? {
        guard let constructedCapturePoint = optionalConstructedCapturePoint(for: request),
              request.requestedCapturePoint.isFinite else { return nil }
        let dx = abs(constructedCapturePoint.x - request.requestedCapturePoint.x)
        let dy = abs(constructedCapturePoint.y - request.requestedCapturePoint.y)
        let residual = max(dx, max(dy, constructedCapturePoint.distance(to: request.requestedCapturePoint)))
        return residual.isFinite ? residual : nil
    }

    private static func refusal(phase: AdmissionPhase, failures: [ContractFailure]) -> PreDownRefusal {
        let terminal: TerminalState = phase == .beforeHover ? .refusedZeroEvent : .refusedZeroClick
        return PreDownRefusal(terminal: terminal, failures: failures)
    }

    private static func uniqueFailures(_ failures: [ContractFailure]) -> [ContractFailure] {
        var seen = Set<String>()
        return failures.filter { seen.insert($0.code).inserted }
    }
}

public struct PostDownAuditRecord: Equatable, Sendable {
    public let mouseDownPosted: Bool
    public let tapPlacement: String
    public let tapOptions: String
    public let tapReadyBeforeFirstEvent: Bool
    public let observedSequence: [String]
    public let fieldStatuses: [String: EvidenceStatus]
    public let sourceTokenMatched: Bool
    public let expectedWindowID: UInt32
    public let deliveredWindowID: UInt32
    public let expectedControl: String
    public let activatedControl: String
    public let underlyingControlActivated: Bool

    public init(
        mouseDownPosted: Bool,
        tapPlacement: String,
        tapOptions: String,
        tapReadyBeforeFirstEvent: Bool,
        observedSequence: [String],
        fieldStatuses: [String: EvidenceStatus],
        sourceTokenMatched: Bool,
        expectedWindowID: UInt32,
        deliveredWindowID: UInt32,
        expectedControl: String,
        activatedControl: String,
        underlyingControlActivated: Bool
    ) {
        self.mouseDownPosted = mouseDownPosted
        self.tapPlacement = tapPlacement
        self.tapOptions = tapOptions
        self.tapReadyBeforeFirstEvent = tapReadyBeforeFirstEvent
        self.observedSequence = observedSequence
        self.fieldStatuses = fieldStatuses
        self.sourceTokenMatched = sourceTokenMatched
        self.expectedWindowID = expectedWindowID
        self.deliveredWindowID = deliveredWindowID
        self.expectedControl = expectedControl
        self.activatedControl = activatedControl
        self.underlyingControlActivated = underlyingControlActivated
    }
}

public enum PostDownDecision: Equatable, Sendable {
    case notStarted
    case confirmed
    case unknownLatchedNoReplay([ContractFailure])

    public var terminal: TerminalState? {
        switch self {
        case .notStarted:
            return nil
        case .confirmed:
            return nil
        case .unknownLatchedNoReplay:
            return .unknownLatchedNoReplay
        }
    }
}

public enum PostDownAuditContract {
    public static let mandatoryFields: [String] = [
        "timestamp",
        "location",
        "source_user_data",
        "source_pid",
        "target_pid",
        "window_under_pointer",
        "window_can_handle",
        "event_order",
        "chronology",
    ]

    /// Audit facts can only confirm or latch UNKNOWN. They cannot satisfy a
    /// pre-down admission, and this function never returns an admission.
    public static func assess(_ record: PostDownAuditRecord) -> PostDownDecision {
        guard record.mouseDownPosted else { return .notStarted }
        var failures: [ContractFailure] = []

        if record.tapPlacement != "tailAppendEventTap" {
            failures.append(ContractFailure(code: "tap_placement", detail: "tap was not created at tail placement"))
        }
        if record.tapOptions != "listenOnly" {
            failures.append(ContractFailure(code: "tap_options", detail: "tap is not listen-only"))
        }
        if !record.tapReadyBeforeFirstEvent {
            failures.append(ContractFailure(code: "tap_not_ready", detail: "tap was not ready before the first synthetic event"))
        }
        let expectedSequence = ConstructedEventKind.allCases.map(\.rawValue)
        if record.observedSequence != expectedSequence {
            failures.append(ContractFailure(code: "tap_event_order", detail: "tap did not observe move/down/up in order"))
        }
        for field in mandatoryFields {
            if record.fieldStatuses[field] != .present {
                failures.append(ContractFailure(code: "post_down_field_\(field)", detail: "mandatory post-down field \(field) is missing or mismatched"))
            }
        }
        if !record.sourceTokenMatched {
            failures.append(ContractFailure(code: "source_token_mismatch", detail: "tap source token does not match the constructed sequence"))
        }
        if record.deliveredWindowID != record.expectedWindowID {
            failures.append(ContractFailure(code: "delivered_window_mismatch", detail: "controlled application received the event at a different window"))
        }
        if record.activatedControl != record.expectedControl {
            failures.append(ContractFailure(code: "activated_control_mismatch", detail: "intended controlled target did not report activation"))
        }
        if record.underlyingControlActivated {
            failures.append(ContractFailure(code: "underlying_control_activated", detail: "a different/underlying controlled surface was activated"))
        }

        return failures.isEmpty ? .confirmed : .unknownLatchedNoReplay(failures)
    }
}
