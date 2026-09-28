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

    func testExpiredSingleUsePermitPostsZeroEvents() throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        XCTAssertThrowsError(try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: candidate.binding,
            intent: .reversible(try transactionOwner(), action: "test"),
            sink: { _, _ in posted += 1 },
            now: 12
        ))
        XCTAssertEqual(posted, 0)
        XCTAssertThrowsError(try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: candidate.binding,
            intent: .reversible(try transactionOwner(), action: "test"),
            sink: { _, _ in posted += 1 },
            now: 10
        ))
        XCTAssertEqual(posted, 0)
    }

    func testFocusTheftAfterPermitMintPostsZeroEvents() throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        var checkedReadiness = false
        XCTAssertThrowsError(try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: candidate.binding,
            intent: .reversible(try transactionOwner(), action: "test"),
            sink: { _, _ in posted += 1 },
            readinessCheck: { _, _ in checkedReadiness = true; return false },
            now: 10
        ))
        XCTAssertTrue(checkedReadiness)
        XCTAssertEqual(posted, 0)
    }

    func testOcclusionAtGuardedBoundaryPostsZeroEvents() throws {
        let (identity, candidate, _, observation) = fixture()
        let permit = try DispatchReadinessGate.mintPermit(
            identity: identity, candidate: candidate, observation: observation, now: 10
        )
        var posted = 0
        var checkedReadiness = false
        XCTAssertThrowsError(try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: candidate.binding,
            intent: .reversible(try transactionOwner(), action: "test"),
            sink: { _, _ in posted += 1 },
            readinessCheck: { _, _ in checkedReadiness = true; return false },
            now: 10
        ))
        XCTAssertTrue(checkedReadiness)
        XCTAssertEqual(posted, 0)
    }

    func testStaleCandidateBindingAtGuardedBoundaryPostsZeroEvents() throws {
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
        XCTAssertThrowsError(try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: staleBinding,
            intent: .reversible(try transactionOwner(), action: "test"),
            sink: { _, _ in posted += 1 },
            now: 10
        ))
        XCTAssertEqual(posted, 0)
    }
}
