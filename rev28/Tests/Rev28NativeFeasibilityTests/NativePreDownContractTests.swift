import XCTest
@testable import Rev28NativeFeasibility

final class NativePreDownContractTests: XCTestCase {
    private let targetWindowID: UInt32 = 42
    private let targetPID: Int32 = 4242
    private let sourcePID: Int32 = 4343
    private let targetBinding = String(repeating: "a", count: 64)
    private let token: UInt64 = 0x4E41544631000001

    func testValidAlbumCardProducesOneMoveDownUpWithoutUniversalSafeRect() {
        let cardRect = ContractRect(x: 392, y: 295, width: 16, height: 5)
        let decision = PreDownContract.evaluate(
            makeRequest(kind: .albumCard, witnessRect: cardRect, uncertaintyPx: 2),
            phase: .beforeHover
        )

        guard case let .admitted(admission) = decision else {
            return XCTFail("valid album-card request was refused: \(decision)")
        }
        let validation = TargetGeometryContract.validate(
            TargetGeometry(
                kind: .albumCard,
                witnessRectPx: cardRect,
                uncertaintyPx: 2,
                selectedPointPx: cardRect.center,
                uniqueWitness: true,
                hitTestProbeCount: 5
            )
        )
        XCTAssertTrue(validation.isValid)
        XCTAssertEqual(validation.admissibleRectPx, cardRect)
        XCTAssertEqual(validation.admissibleRectPx?.height, 5)
        XCTAssertEqual(decision.dispatchEvents.map(\.kind), [.mouseMoved, .leftMouseDown, .leftMouseUp])
        XCTAssertEqual(admission.constructedDownEventCount, 1)
        XCTAssertEqual(admission.constructedUpEventCount, 1)
        XCTAssertFalse(admission.productionEligible)
    }

    func testMenuTriggerAndSaveAllPreserveUPlusFourAndSixteenBySixteen() {
        for kind in [TargetKind.menuTrigger, .saveAll] {
            let targetRect = ContractRect(x: 360, y: 260, width: 40, height: 40)
            let geometry = TargetGeometry(
                kind: kind,
                witnessRectPx: targetRect,
                uncertaintyPx: 2,
                selectedPointPx: targetRect.center,
                uniqueWitness: true,
                hitTestProbeCount: 5
            )
            let validation = TargetGeometryContract.validate(geometry)

            XCTAssertTrue(validation.isValid, "\(kind) should satisfy u+4 and 16x16")
            XCTAssertEqual(validation.admissibleRectPx?.width, 28)
            XCTAssertEqual(validation.admissibleRectPx?.height, 28)
        }

        let tooSmall = ContractRect(x: 360, y: 260, width: 20, height: 20)
        let validation = TargetGeometryContract.validate(
            TargetGeometry(
                kind: .saveAll,
                witnessRectPx: tooSmall,
                uncertaintyPx: 2,
                selectedPointPx: tooSmall.center,
                uniqueWitness: true,
                hitTestProbeCount: 5
            )
        )
        XCTAssertFalse(validation.isValid)
        XCTAssertTrue(validation.failures.contains { $0.code == "target_safe_rect_16x16" })
    }

    func testMissingUncertaintyTermRefusesZeroEvent() {
        let request = makeRequest(
            uncertainty: UncertaintyVector(
                localizePx: nil,
                transformPx: 0,
                motionPx: 0,
                serializePx: 0,
                allMeasured: true
            )
        )
        assertRefusedZeroEvent(PreDownContract.evaluate(request, phase: .beforeHover))
    }

    func testNonFiniteUncertaintyRefusesZeroEvent() {
        let request = makeRequest(
            uncertainty: UncertaintyVector(
                localizePx: .infinity,
                transformPx: 0,
                motionPx: 0,
                serializePx: 0,
                allMeasured: true
            )
        )
        assertRefusedZeroEvent(PreDownContract.evaluate(request, phase: .beforeHover))
    }

    func testConstructedPointOutsideTargetRefusesZeroEvent() {
        let cardRect = ContractRect(x: 392, y: 295, width: 16, height: 5)
        let request = makeRequest(
            kind: .albumCard,
            witnessRect: cardRect,
            eventScreenPoint: ContractPoint(x: 500, y: 500)
        )
        let decision = PreDownContract.evaluate(request, phase: .beforeHover)
        assertRefusedZeroEvent(decision)
        guard case let .refused(refusal) = decision else { return XCTFail("expected refusal") }
        XCTAssertTrue(refusal.failures.contains { $0.code == "constructed_location_outside_target" })
    }

    func testMissingStaleConsumedAndForeignAuthorizationRefuseZeroEvent() {
        let missing = makeRequest(
            authorization: AuthorizationBinding(
                authority: "f1_controlled_nontransactional",
                authorizationID: "",
                intentRevision: "",
                targetBindingSHA256: "",
                singleUse: true,
                consumed: false,
                expiresAtMonotonic: 200
            )
        )
        assertRefusedZeroEvent(PreDownContract.evaluate(missing, phase: .beforeHover))

        let stale = makeRequest(
            authorization: AuthorizationBinding(
                authority: "f1_controlled_nontransactional",
                authorizationID: "auth",
                intentRevision: "1",
                targetBindingSHA256: targetBinding,
                singleUse: true,
                consumed: false,
                expiresAtMonotonic: 99
            )
        )
        assertRefusedZeroEvent(PreDownContract.evaluate(stale, phase: .beforeHover))

        let consumed = makeRequest(
            authorization: AuthorizationBinding(
                authority: "f1_controlled_nontransactional",
                authorizationID: "auth",
                intentRevision: "1",
                targetBindingSHA256: targetBinding,
                singleUse: true,
                consumed: true,
                expiresAtMonotonic: 200
            )
        )
        assertRefusedZeroEvent(PreDownContract.evaluate(consumed, phase: .beforeHover))

        let foreign = makeRequest(
            authorization: AuthorizationBinding(
                authority: "f1_controlled_nontransactional",
                authorizationID: "auth",
                intentRevision: "1",
                targetBindingSHA256: String(repeating: "b", count: 64),
                singleUse: true,
                consumed: false,
                expiresAtMonotonic: 200
            )
        )
        let decision = PreDownContract.evaluate(foreign, phase: .beforeHover)
        assertRefusedZeroEvent(decision)
        guard case let .refused(refusal) = decision else { return XCTFail("expected refusal") }
        XCTAssertTrue(refusal.failures.contains { $0.code == "authorization_target_mismatch" })
    }

    func testFailureAfterHoverRefusesZeroClick() {
        let request = makeRequest(
            uncertainty: UncertaintyVector(
                localizePx: nil,
                transformPx: 0,
                motionPx: 0,
                serializePx: 0,
                allMeasured: true
            )
        )
        let decision = PreDownContract.evaluate(request, phase: .afterHover)
        guard case let .refused(refusal) = decision else { return XCTFail("expected refusal") }
        XCTAssertEqual(refusal.terminal, .refusedZeroClick)
        XCTAssertTrue(decision.dispatchEvents.isEmpty)
    }

    func testPostDownAuditIsIndependentAndCannotOverridePreDownRefusal() {
        let refused = PreDownContract.evaluate(
            makeRequest(
                uncertainty: UncertaintyVector(
                    localizePx: nil,
                    transformPx: 0,
                    motionPx: 0,
                    serializePx: 0,
                    allMeasured: true
                )
            ),
            phase: .beforeHover
        )
        assertRefusedZeroEvent(refused)

        let completeAudit = makeAudit()
        XCTAssertEqual(PostDownAuditContract.assess(completeAudit), .confirmed)
        XCTAssertTrue(refused.dispatchEvents.isEmpty)
        guard case let .refused(refusal) = refused else { return XCTFail("expected refusal") }
        XCTAssertEqual(refusal.terminal, .refusedZeroEvent)
    }

    func testMissingOrContradictoryPostDownAuditLatchesUnknownNoReplay() {
        var fields = completeFieldStatuses()
        fields.removeValue(forKey: "window_under_pointer")
        let missing = PostDownAuditRecord(
            mouseDownPosted: true,
            tapPlacement: "tailAppendEventTap",
            tapOptions: "listenOnly",
            tapReadyBeforeFirstEvent: true,
            observedSequence: ["mouseMoved", "leftMouseDown", "leftMouseUp"],
            fieldStatuses: fields,
            sourceTokenMatched: true,
            expectedWindowID: targetWindowID,
            deliveredWindowID: targetWindowID,
            expectedControl: "mainContentView",
            activatedControl: "mainContentView",
            underlyingControlActivated: false
        )
        XCTAssertTrue(isUnknown(PostDownAuditContract.assess(missing)))

        let wrongTarget = PostDownAuditRecord(
            mouseDownPosted: true,
            tapPlacement: "tailAppendEventTap",
            tapOptions: "listenOnly",
            tapReadyBeforeFirstEvent: true,
            observedSequence: ["mouseMoved", "leftMouseDown", "leftMouseUp"],
            fieldStatuses: completeFieldStatuses(),
            sourceTokenMatched: true,
            expectedWindowID: targetWindowID,
            deliveredWindowID: 99,
            expectedControl: "mainContentView",
            activatedControl: "mainContentView",
            underlyingControlActivated: false
        )
        XCTAssertTrue(isUnknown(PostDownAuditContract.assess(wrongTarget)))
    }

    func testSuccessfulProductionAdmissionStillRequiresProjectLedgerAuthority() {
        let request = makeRequest(
            context: .production,
            authorization: AuthorizationBinding(
                authority: "python_project_ledger",
                authorizationID: "ledger-auth",
                intentRevision: "7",
                targetBindingSHA256: targetBinding,
                singleUse: true,
                consumed: false,
                expiresAtMonotonic: 200
            )
        )
        guard case let .admitted(admission) = PreDownContract.evaluate(request, phase: .beforeHover) else {
            return XCTFail("production-shaped request should satisfy the pure contract")
        }
        XCTAssertTrue(admission.productionEligible)
    }

    private func makeRequest(
        kind: TargetKind = .albumCard,
        witnessRect: ContractRect = ContractRect(x: 392, y: 295, width: 16, height: 5),
        uncertaintyPx: Double = 2,
        eventScreenPoint: ContractPoint? = nil,
        uncertainty: UncertaintyVector = UncertaintyVector(
            localizePx: 0,
            transformPx: 0,
            motionPx: 0,
            serializePx: 0,
            allMeasured: true
        ),
        context: AdmissionContext = .controlledFeasibility,
        authorization: AuthorizationBinding = AuthorizationBinding(
            authority: "f1_controlled_nontransactional",
            authorizationID: "f1-auth",
            intentRevision: "1",
            targetBindingSHA256: String(repeating: "a", count: 64),
            singleUse: true,
            consumed: false,
            expiresAtMonotonic: 200
        )
    ) -> PreDownAdmissionRequest {
        let scale = 2.0
        let windowFrame = ContractRect(x: 0, y: 0, width: 800, height: 600)
        let captureGeometry = CaptureGeometry(
            windowFramePt: windowFrame,
            captureBBoxPt: windowFrame,
            scale: scale
        )
        let selectedCapturePoint = witnessRect.center
        let screenPoint = eventScreenPoint ?? captureGeometry.screenPoint(fromCapture: selectedCapturePoint)
        let events = ConstructedEventSet(
            mouseMoved: ConstructedEvent(
                kind: .mouseMoved,
                locationScreen: screenPoint,
                sourceUserData: token,
                sourcePIDField: sourcePID,
                targetPIDField: targetPID
            ),
            leftMouseDown: ConstructedEvent(
                kind: .leftMouseDown,
                locationScreen: screenPoint,
                sourceUserData: token,
                sourcePIDField: sourcePID,
                targetPIDField: targetPID
            ),
            leftMouseUp: ConstructedEvent(
                kind: .leftMouseUp,
                locationScreen: screenPoint,
                sourceUserData: token,
                sourcePIDField: sourcePID,
                targetPIDField: targetPID
            )
        )
        return PreDownAdmissionRequest(
            context: context,
            runtime: RuntimeBinding(
                planSHA256: String(repeating: "1", count: 64),
                sourceSHA256: String(repeating: "2", count: 64),
                runtimeSHA256: String(repeating: "3", count: 64),
                reviewBinding: "review-5571271859"
            ),
            targetProcess: ProcessBinding(
                pid: targetPID,
                processInstanceToken: "rev28harness-test-instance",
                bundleID: "com.macpilot.rev28harness"
            ),
            sourceProcessPID: sourcePID,
            targetWindow: WindowBinding(windowID: targetWindowID, layer: 0, framePt: windowFrame),
            display: DisplayBinding(displayID: 1, scale: scale),
            targetBindingSHA256: targetBinding,
            targetGeometry: TargetGeometry(
                kind: kind,
                witnessRectPx: witnessRect,
                uncertaintyPx: uncertaintyPx,
                selectedPointPx: witnessRect.center,
                uniqueWitness: true,
                hitTestProbeCount: 5
            ),
            captureGeometry: captureGeometry,
            requestedCapturePoint: selectedCapturePoint,
            constructedEvents: events,
            uncertainty: uncertainty,
            surface: SurfaceEvidence(
                expectedWindowID: targetWindowID,
                observedTopmostWindowID: targetWindowID,
                expectedLayer: 0,
                observedLayer: 0,
                alpha: 1,
                isOnScreen: true,
                noAmbiguousWindowAbove: true
            ),
            hitTest: HitTestEvidence(
                selectedPointIdentifiesTarget: true,
                allUncertaintyProbesIdentifyTarget: true,
                probeCount: 5
            ),
            authorization: authorization,
            nowMonotonic: 100,
            preDownDeadlineMonotonic: 101
        )
    }

    private func assertRefusedZeroEvent(
        _ decision: PreDownDecision,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        guard case let .refused(refusal) = decision else {
            return XCTFail("expected REFUSED_ZERO_EVENT", file: file, line: line)
        }
        XCTAssertEqual(refusal.terminal, .refusedZeroEvent, file: file, line: line)
        XCTAssertTrue(decision.dispatchEvents.isEmpty, file: file, line: line)
    }

    private func completeFieldStatuses() -> [String: EvidenceStatus] {
        Dictionary(uniqueKeysWithValues: PostDownAuditContract.mandatoryFields.map { ($0, .present) })
    }

    private func makeAudit() -> PostDownAuditRecord {
        PostDownAuditRecord(
            mouseDownPosted: true,
            tapPlacement: "tailAppendEventTap",
            tapOptions: "listenOnly",
            tapReadyBeforeFirstEvent: true,
            observedSequence: ["mouseMoved", "leftMouseDown", "leftMouseUp"],
            fieldStatuses: completeFieldStatuses(),
            sourceTokenMatched: true,
            expectedWindowID: targetWindowID,
            deliveredWindowID: targetWindowID,
            expectedControl: "mainContentView",
            activatedControl: "mainContentView",
            underlyingControlActivated: false
        )
    }

    private func isUnknown(_ decision: PostDownDecision) -> Bool {
        if case .unknownLatchedNoReplay = decision { return true }
        return false
    }
}
