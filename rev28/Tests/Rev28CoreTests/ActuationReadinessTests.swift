import CoreGraphics
import XCTest
@testable import Rev28Core

final class ActuationReadinessTests: XCTestCase {
    private func transactionOwner() throws -> PersistentTransactionOwner {
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
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        )
    }

    private func fixture(active: Bool = true, frontmost: Bool = true, epoch: UInt64 = 4) -> (
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
            identity: "target",
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
}
