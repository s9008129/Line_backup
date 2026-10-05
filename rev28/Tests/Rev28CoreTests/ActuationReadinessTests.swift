import CoreGraphics
import XCTest
@testable import Rev28Core

final class ActuationReadinessTests: XCTestCase {
    private func transactionOwner(checkpoint: Bool = false) throws -> PersistentTransactionOwner {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let staging = root.appendingPathComponent("staging")
        let run = staging.appendingPathComponent("run")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: "run", goal: "test", group: "group", album: "album",
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("code".utf8)),
            stagingRoot: staging, stagingRunDirectory: run
        )
        return try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl")),
            checkpointURL: checkpoint ? root.appendingPathComponent("ledger-head.anchor") : nil
        )
    }

    private func fixture(active: Bool = true, frontmost: Bool = true, epoch: UInt64 = 4, target: String = "target") -> (
        WindowIdentity, StructuralCandidate, CaptureGeometry, ReadinessObservation
    ) {
        let process = ProcessInstanceID(pid: 42, startTimeSeconds: 10, startTimeMicroseconds: 2)
        let frame = CGRect(x: 100, y: 200, width: 400, height: 300)
        let identity = WindowIdentity(
            bundleID: "com.example.target",
            process: process,
            windowID: 7,
            windowFrame: frame,
            ax: AXIdentityRead(role: "AXWindow", subrole: nil, title: nil),
            cgEntry: CGWindowEntryRecord(windowID: 7, frame: frame, layer: 0, ownerPID: 42, ownerName: "Target"),
            captureEpoch: epoch,
            captureImageSHA256: String(repeating: "a", count: 64)
        )
        let binding = SurfaceBinding(
            bundleID: identity.bundleID,
            process: identity.process,
            windowID: 7,
            captureEpoch: epoch,
            frameSHA256: identity.captureImageSHA256
        )
        let candidate = StructuralCandidate(
            identity: target,
            safeRectCapturePx: CGRect(x: 0, y: 0, width: 100, height: 100),
            pointCapturePx: CapturePixelPoint(x: 50, y: 50),
            binding: binding
        )
        let geometry = CaptureGeometry(windowFrame: frame, captureBBox: frame, scale: 1)
        let fresh = FreshWindowObservation(
            bundleID: identity.bundleID, process: process, windowID: 7, frame: frame, layer: 0, isOnScreen: true
        )
        let observation = ReadinessObservation(
            applicationActive: active,
            targetFrontmost: frontmost,
            freshWindow: fresh,
            currentEpoch: epoch,
            currentBinding: binding,
            captureGeometry: CaptureGeometry(windowFrame: frame, captureBBox: frame, scale: 1),
            captureImageSize: CGSize(width: 400, height: 300),
            observedAtUptime: 10
        )
        return (identity, candidate, geometry, observation)
    }

    func testFocusTheftRefusesPermitBeforeAnyEventCanBePosted() throws {
        let (identity, candidate, _, observation) = fixture(frontmost: false)
        XCTAssertThrowsError(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        ))
    }

    func testStaleIdentityRefusesPermit() throws {
        let (identity, candidate, _, observation) = fixture(epoch: 4)
        let stale = ReadinessObservation(
            applicationActive: true, targetFrontmost: true, freshWindow: observation.freshWindow,
            currentEpoch: 5, currentBinding: observation.currentBinding,
            captureGeometry: observation.captureGeometry,
            captureImageSize: observation.captureImageSize,
            observedAtUptime: 10
        )
        XCTAssertThrowsError(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: stale, now: 10
        ))
    }

    func testDispatchMarginConvertsOnePointAtCaptureScaleNotOnePixel() throws {
        let (identity, _, _, base) = fixture()
        func scaledObservation(_ scale: Double) -> ReadinessObservation {
            ReadinessObservation(
                applicationActive: base.applicationActive,
                targetFrontmost: base.targetFrontmost,
                freshWindow: base.freshWindow,
                currentEpoch: base.currentEpoch,
                currentBinding: base.currentBinding,
                captureGeometry: CaptureGeometry(windowFrame: base.captureGeometry.windowFrame,
                                                 captureBBox: base.captureGeometry.captureBBox,
                                                 scale: scale),
                captureImageSize: base.captureImageSize,
                observedAtUptime: base.observedAtUptime
            )
        }
        let safe = CGRect(x: 0, y: 0, width: 100, height: 100)
        func candidate(pointX: Double) -> StructuralCandidate {
            StructuralCandidate(identity: "target", safeRectCapturePx: safe,
                                pointCapturePx: CapturePixelPoint(x: pointX, y: 50),
                                binding: base.currentBinding)
        }
        // At 2x a 1 px margin is 0.5 pt: the plan's 1-point refusal must reject it.
        XCTAssertThrowsError(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate(pointX: 1), observation: scaledObservation(2), now: 10
        ))
        // Exactly 2 px is exactly 1 pt at 2x and is accepted (`>=` semantics, matching
        // CaptureGeometryRules.isDispatchable).
        XCTAssertNoThrow(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate(pointX: 2), observation: scaledObservation(2), now: 10
        ))
        // The same 2 px margin is only 2/3 pt at 3x and must be refused again.
        XCTAssertThrowsError(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate(pointX: 2), observation: scaledObservation(3), now: 10
        ))
        // At 1x the conversion is identity: exactly 1 px is exactly 1 pt.
        XCTAssertNoThrow(try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate(pointX: 1), observation: scaledObservation(1), now: 10
        ))
        // Direct invariant check in capture-pixel space.
        XCTAssertTrue(CaptureGeometryRules.isDispatchableCapturePixels(
            point: CapturePixelPoint(x: 2, y: 50), safeRect: safe, captureScale: 2
        ))
        XCTAssertFalse(CaptureGeometryRules.isDispatchableCapturePixels(
            point: CapturePixelPoint(x: 1, y: 50), safeRect: safe, captureScale: 2
        ))
        XCTAssertFalse(CaptureGeometryRules.isDispatchableCapturePixels(
            point: CapturePixelPoint(x: 50, y: 50), safeRect: safe, captureScale: .nan
        ))
    }

    func testExpiredSingleUsePermitPostsZeroEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(try transactionOwner(), action: "test"),
                postHoverRevalidation: {},
                sink: { _, _ in posted += 1 },
                now: 12
            )
            XCTFail("expired permit must refuse")
        } catch {}
        XCTAssertEqual(posted, 0)
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(try transactionOwner(), action: "test"),
                postHoverRevalidation: {},
                sink: { _, _ in posted += 1 },
                now: 10
            )
            XCTFail("single-use permit must refuse a second consumption")
        } catch {}
        XCTAssertEqual(posted, 0)
    }

    func testFocusTheftAfterPermitMintPostsZeroEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        var checkedReadiness = false
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(try transactionOwner(), action: "test"),
                postHoverRevalidation: {},
                sink: { _, _ in posted += 1 },
                readinessCheck: { _, _ in checkedReadiness = true; return false },
                now: 10
            )
            XCTFail("readiness loss must refuse")
        } catch {}
        XCTAssertTrue(checkedReadiness)
        XCTAssertEqual(posted, 0)
    }

    func testOcclusionAtGuardedBoundaryPostsZeroEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        var checkedSurface = false
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(try transactionOwner(), action: "test"),
                postHoverRevalidation: {},
                sink: { _, _ in posted += 1 },
                readinessCheck: { _, _ in true },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                addressedSurfaceCheck: { _, _, _ in checkedSurface = true; return false },
                now: 10
            )
            XCTFail("occlusion at the addressed surface must refuse before the hover")
        } catch {}
        XCTAssertTrue(checkedSurface)
        XCTAssertEqual(posted, 0)
    }

    /// Plan C5: readiness is revalidated between the hover and mouseDown. When
    /// focus is stolen in exactly that window, only the move is posted and no
    /// click event ever reaches the sink. The failed candidate revalidation is
    /// durably recorded in the owner (plan C4).
    func testFocusTheftBetweenHoverAndMouseDownPostsZeroClickEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner()
        var posted: [CGEventType] = []
        var readinessCalls = 0
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(owner, action: "test"),
                postHoverRevalidation: {},
                sink: { event, _ in posted.append(event.type) },
                readinessCheck: { _, _ in
                    readinessCalls += 1
                    return readinessCalls == 1
                },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                addressedSurfaceCheck: { _, _, _ in true },
                now: 10
            )
            XCTFail("readiness loss after the hover must refuse")
        } catch {
            guard case QuartzActuatorError.dispatchRefusedByPrecondition(let reason) = error else {
                return XCTFail("unexpected \(error)")
            }
            XCTAssertTrue(reason.contains("post-hover revalidation failed"), reason)
        }
        XCTAssertEqual(readinessCalls, 2, "readiness must be checked both before the hover and before mouseDown")
        XCTAssertEqual(posted, [.mouseMoved], "only the hover may be posted; no down/up after readiness loss")
        XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 1)
    }

    func testStaleCandidateBindingAtGuardedBoundaryPostsZeroEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let staleBinding = SurfaceBinding(
            bundleID: candidate.binding.bundleID,
            process: ProcessInstanceID(pid: candidate.binding.process.pid, startTimeSeconds: 11, startTimeMicroseconds: 0),
            windowID: candidate.binding.windowID,
            captureEpoch: candidate.binding.captureEpoch,
            frameSHA256: candidate.binding.frameSHA256
        )
        var posted = 0
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: staleBinding,
                intent: .reversible(try transactionOwner(), action: "test"),
                postHoverRevalidation: {},
                sink: { _, _ in posted += 1 },
                now: 10
            )
            XCTFail("stale binding must refuse")
        } catch {}
        XCTAssertEqual(posted, 0)
    }

    /// Plan C5: a failed post-hover revalidation — the fresh live observation
    /// no longer matches the permit's candidate/window/geometry — posts the
    /// hover only, zero down/up, and durably records the failure.
    func testFailedPostHoverRevalidationPostsZeroClickEventsAndRecordsFailure() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner()
        var posted: [CGEventType] = []
        var revalidationCalls = 0
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(owner, action: "recover-state"),
                postHoverRevalidation: {
                    revalidationCalls += 1
                    throw QuartzActuatorError.dispatchRefusedByPrecondition("window geometry changed")
                },
                sink: { event, _ in posted.append(event.type) },
                readinessCheck: { _, _ in true },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                addressedSurfaceCheck: { _, _, _ in true },
                now: 10
            )
            XCTFail("failed post-hover revalidation must refuse")
        } catch {
            guard case QuartzActuatorError.dispatchRefusedByPrecondition(let reason) = error else {
                return XCTFail("unexpected \(error)")
            }
            XCTAssertTrue(reason.contains("post-hover revalidation failed"), reason)
        }
        XCTAssertEqual(revalidationCalls, 1, "the fresh revalidation must run exactly once, after the hover")
        XCTAssertEqual(posted, [.mouseMoved], "no down/up may follow a failed post-hover revalidation")
        XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 1)
    }

    /// Plan C5: the revalidation runs between the hover and mouseDown and a
    /// passing outcome is durably recorded, so a subsequent success resets the
    /// consecutive-failure counter.
    func testSuccessfulPostHoverRevalidationRunsAfterHoverAndResetsFailures() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner()
        try owner.recordCandidateRevalidation(blockerKey: "recover-state", passed: false)
        var posted: [CGEventType] = []
        var revalidationSawMove = false
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(owner, action: "recover-state"),
                postHoverRevalidation: {
                    revalidationSawMove = posted == [.mouseMoved]
                },
                sink: { event, _ in posted.append(event.type) },
                readinessCheck: { _, _ in true },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                addressedSurfaceCheck: { _, _, _ in true },
                now: 10
            )
        } catch {
            return XCTFail("unexpected \(error)")
        }
        XCTAssertTrue(revalidationSawMove, "the revalidation must run after the hover and before mouseDown")
        XCTAssertEqual(posted, [.mouseMoved, .leftMouseDown, .leftMouseUp])
        XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 0)
    }

    /// Plan C5: the addressed/topmost surface is revalidated again after the
    /// hover; occlusion arriving in that window posts zero down/up.
    func testOcclusionBetweenHoverAndMouseDownPostsZeroClickEvents() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner()
        var posted: [CGEventType] = []
        var surfaceChecks = 0
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: candidate.binding,
                intent: .reversible(owner, action: "recover-state"),
                postHoverRevalidation: {},
                sink: { event, _ in posted.append(event.type) },
                readinessCheck: { _, _ in true },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                addressedSurfaceCheck: { _, _, _ in
                    surfaceChecks += 1
                    return surfaceChecks == 1
                },
                now: 10
            )
            XCTFail("occlusion after the hover must refuse")
        } catch {}
        XCTAssertEqual(surfaceChecks, 2, "the addressed surface must be checked before the hover and again before mouseDown")
        XCTAssertEqual(posted, [.mouseMoved])
        XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 1)
    }

    func testDurableRevalidationWriteFailureAfterHoverPostsNoMouseDown() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner()
        var posted: [CGEventType] = []
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit, currentBinding: candidate.binding,
                intent: .reversible(owner, action: "recover-state"),
                postHoverRevalidation: {
                    // Reservation succeeded. The next durable append must now fail.
                    try Data("changed after reservation".utf8).write(to: owner.ledger.fileURL)
                },
                sink: { event, _ in posted.append(event.type) },
                readinessCheck: { _, _ in true }, processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true }, addressedSurfaceCheck: { _, _, _ in true }, now: 10
            )
            XCTFail("a failed durable write must prevent mouseDown")
        } catch {}
        XCTAssertEqual(posted, [.mouseMoved])
    }

    func testLedgerAndAnchorFaultsRefuseReversibleAndSaveAllEvenWhenFailureRecordCannotPersist() async throws {
        for saveAll in [false, true] {
            for anchorFault in [false, true] {
                for visualFailure in [false, true] {
                    let (identity, candidate, _, observation) = fixture(target: saveAll ? "儲存全部" : "target")
                    let permit = try DispatchReadinessGate.mintPermit(
                        identity: identity, candidate: candidate, observation: observation, now: 10
                    )
                    let owner = try transactionOwner(checkpoint: true)
                    if saveAll {
                        try owner.initializeState(evidenceSHA256: EvidenceIO.sha256Hex(Data("app".utf8)))
                        for state in LiveExecutionEngine.preSaveStates.dropFirst() {
                            try owner.transition(to: state, evidenceSHA256: EvidenceIO.sha256Hex(Data(state.rawValue.utf8)))
                        }
                        try EligibilityTestSupport.recordEligibility(on: owner)
                    }
                    let events = MouseEvents()
                    var refused = false
                    do {
                        try await GatedQuartzActuator.postClick(
                            permit: permit, currentBinding: candidate.binding,
                            intent: saveAll ? .saveAll(owner) : .reversible(owner, action: "test"),
                            postHoverRevalidation: {
                                if anchorFault {
                                    let anchor = owner.ledger.fileURL.deletingLastPathComponent().appendingPathComponent("ledger-head.anchor")
                                    try FileManager.default.removeItem(at: anchor)
                                    try FileManager.default.createDirectory(at: anchor, withIntermediateDirectories: false)
                                } else {
                                    try Data("corruption after reservation".utf8).write(to: owner.ledger.fileURL)
                                }
                                if visualFailure {
                                    throw QuartzActuatorError.dispatchRefusedByPrecondition("candidate lost")
                                }
                            },
                            sink: { event, _ in events.append(event.type) },
                            readinessCheck: { _, _ in true }, processIdentityCheck: { _, _ in true },
                            postEventAccessCheck: { true }, addressedSurfaceCheck: { _, _, _ in true }, now: 10
                        )
                    } catch { refused = true }
                    let context = "saveAll=\(saveAll) anchorFault=\(anchorFault) visualFailure=\(visualFailure)"
                    XCTAssertTrue(refused, context)
                    XCTAssertEqual(events.values, [.mouseMoved], context)
                    if saveAll {
                        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 2, "intent/attempt remain consumed: \(context)")
                        XCTAssertThrowsError(try owner.reserveSaveAll(), context)
                    } else {
                        XCTAssertEqual(owner.reversibleDispatchCount, 1, context)
                    }
                }
            }
        }
    }

    func testOriginalPermitExpiresDuringDurableWriteAndPostsNoDown() async throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        let owner = try transactionOwner(checkpoint: true)
        let events = MouseEvents()
        do {
            try await GatedQuartzActuator.postClick(
                permit: permit, currentBinding: candidate.binding,
                intent: .reversible(owner, action: "test"), postHoverRevalidation: {},
                sink: { event, _ in events.append(event.type) },
                readinessCheck: { _, _ in true }, processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true }, addressedSurfaceCheck: { _, _, _ in true },
                clock: {
                    // The fault clock advances only after the success record is
                    // actually appended, modeling durable-I/O latency.
                    owner.ledger.entries.contains { $0.kind == "budget.revalidation" && $0.payload["passed"] == "true" } ? 12 : 10
                }
            )
            XCTFail("a new capture or successful write cannot extend the original permit")
        } catch {}
        XCTAssertEqual(events.values, [.mouseMoved])
        XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 1)
        _ = try IntentLedger.verifyHeadAnchor(
            fileURL: owner.ledger.fileURL,
            anchorURL: owner.ledger.fileURL.deletingLastPathComponent().appendingPathComponent("ledger-head.anchor")
        )
    }

    func testRetainedSessionRevalidationAcceptsRedrawButRejectsStaleMovedLostAndAmbiguousTargets() async throws {
        let scene = FakeLineScene()
        let source = FakeObservationSource(window: NativeObservationTestWindows.lineWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.imageProvider = { scene.image }
        let session = NativeObservationSession(sessionID: "readiness-session", source: source, ocr: ScriptedOcr(scene: scene))
        let request = NativeObservationRequest(
            runID: "readiness-run", state: .targetAlbumLocated,
            target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            configuration: .primaryWindow,
            geometryState: CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true),
            localization: .albumCards(title: ComposedNativeAdapter.albumTitle, count: "57"),
            observationBudgetNanos: 5_000_000_000
        )
        let original = try await session.capture(request)
        let permit = try DispatchReadinessGate.mintPermit(
            identity: original.window, candidate: XCTUnwrap(original.candidate),
            observation: ReadinessObservation(bundle: original, applicationActive: true, targetFrontmost: true), now: 100
        )
        func revalidate(_ fresh: ObservationBundle, now: Double = 100) throws {
            try DispatchReadinessGate.revalidateAfterHover(
                permit: permit, freshBundle: fresh, applicationActive: true, targetFrontmost: true, now: now
            )
        }
        XCTAssertThrowsError(try revalidate(original), "equal pixels cannot authorize a reused epoch")
        let samePixels = try await session.capture(request)
        XCTAssertEqual(samePixels.frame.imageSHA256, original.frame.imageSHA256)
        XCTAssertGreaterThan(samePixels.epoch, original.epoch)
        XCTAssertNoThrow(try revalidate(samePixels))
        scene.imageOverride = FakeLineScene.plainImage(red: 0.8)
        let redraw = try await session.capture(request)
        XCTAssertNotEqual(redraw.frame.imageSHA256, original.frame.imageSHA256)
        XCTAssertNoThrow(try revalidate(redraw), "changed pixels require fresh localization, not hash equality")
        let stale = try ReadinessObservation(bundle: original, applicationActive: true, targetFrontmost: true)
        XCTAssertEqual(stale.observedAtUptime, 100)
        XCTAssertThrowsError(try DispatchReadinessGate.mintPermit(
            identity: original.window, candidate: XCTUnwrap(original.candidate), observation: stale, now: 102
        ), "projection must preserve capture age")
        XCTAssertThrowsError(try revalidate(redraw, now: 102), "relocalization cannot renew the original permit")

        let items = scene.ocrItems
        scene.ocrOverride = items.map { item in
            guard item.text == ComposedNativeAdapter.albumTitle || item.text == "57" else { return item }
            // Card geometry spans the full row, so a horizontal OCR text shift
            // is not a target move. Move the date band's structural boundary.
            return scene.item(item.text, item.boundingBoxCapturePx.offsetBy(dx: 0, dy: 20))
        }
        let moved = try await session.capture(request)
        XCTAssertNotNil(moved.candidate)
        XCTAssertThrowsError(try revalidate(moved), "do not retarget the already-posted hover")
        scene.ocrOverride = items.filter { $0.text != "57" }
        let lost = try await session.capture(request)
        XCTAssertNil(lost.candidate)
        XCTAssertThrowsError(try revalidate(lost))
        scene.ocrOverride = items + [scene.item("57", CGRect(x: 65, y: 130, width: 30, height: 16))]
        let ambiguous = try await session.capture(request)
        XCTAssertNil(ambiguous.candidate)
        XCTAssertThrowsError(try revalidate(ambiguous))
    }

    private final class MouseEvents: @unchecked Sendable {
        private let lock = NSLock()
        private var stored: [CGEventType] = []
        var values: [CGEventType] { lock.withLock { stored } }
        func append(_ type: CGEventType) { lock.withLock { stored.append(type) } }
    }

    func testLateFailureSupersedesOnlyItsOwnSuccessAndPreservesTwoFailureAbortAfterRestart() async throws {
        for expiry in [true, false] {
            let (identity, candidate, _, observation) = fixture()
            let permit = try DispatchReadinessGate.mintPermit(
                identity: identity, candidate: candidate, observation: observation, now: 10
            )
            let owner = try transactionOwner(checkpoint: true)
            try owner.recordCandidateRevalidation(blockerKey: "previous-attempt", passed: false)
            let events = MouseEvents()
            var guardCalls = 0
            do {
                try await GatedQuartzActuator.postClick(
                    permit: permit, currentBinding: candidate.binding,
                    intent: .reversible(owner, action: "test"), postHoverRevalidation: {},
                    sink: { event, _ in events.append(event.type) },
                    readinessCheck: { _, _ in
                        guardCalls += 1
                        return expiry || guardCalls < 3
                    },
                    processIdentityCheck: { _, _ in true }, postEventAccessCheck: { true },
                    addressedSurfaceCheck: { _, _, _ in true },
                    clock: {
                        expiry && owner.ledger.entries.contains {
                            $0.kind == "budget.revalidation" && $0.payload["passed"] == "true"
                        } ? 12 : 10
                    }
                )
                XCTFail("late failure must refuse")
            } catch {}
            XCTAssertEqual(events.values, [.mouseMoved])
            XCTAssertEqual(owner.consecutiveCandidateRevalidationFailures, 2, "late failure cannot erase the previous failure")
            XCTAssertThrowsError(try owner.recordReversibleDispatch(action: "later-attempt")) {
                XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
            }
            let resumed = try PersistentTransactionOwner(
                authorization: owner.authorization, ledger: IntentLedger(fileURL: owner.ledger.fileURL),
                checkpointURL: owner.ledger.fileURL.deletingLastPathComponent().appendingPathComponent("ledger-head.anchor"),
                requireCheckpointOnResume: true
            )
            XCTAssertEqual(resumed.consecutiveCandidateRevalidationFailures, 2)
            XCTAssertThrowsError(try resumed.recordReversibleDispatch(action: "restart-attempt")) {
                XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
            }
        }
    }
}
