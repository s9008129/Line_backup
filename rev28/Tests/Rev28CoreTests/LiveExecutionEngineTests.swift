import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

final class LiveExecutionEngineTests: XCTestCase {
    private final class FakeAdapter: @unchecked Sendable, LiveExecutionAdapter {
        private let lock = NSLock()
        private(set) var saveAllMouseEvents = 0
        private(set) var confirmationPosts = 0
        var failAtState: ExecutionState?

        func establish(state: ExecutionState, owner: PersistentTransactionOwner) async throws -> String {
            if failAtState == state { throw NSError(domain: "FakeAdapter", code: 1) }
            return digest("state:\(state.rawValue)")
        }

        func dispatchSaveAll(owner: PersistentTransactionOwner) async throws -> String {
            let process = ProcessInstanceID(pid: 4242, startTimeSeconds: 1, startTimeMicroseconds: 0)
            let binding = SurfaceBinding(
                bundleID: "jp.naver.line.mac",
                process: process,
                windowID: 10,
                captureEpoch: 1,
                frameSHA256: String(repeating: "a", count: 64)
            )
            let candidate = StructuralCandidate(
                identity: "儲存全部",
                safeRectCapturePx: CGRect(x: 10, y: 10, width: 100, height: 100),
                pointCapturePx: CapturePixelPoint(x: 50, y: 50),
                binding: binding
            )
            let identity = WindowIdentity(
                bundleID: binding.bundleID,
                process: process,
                windowID: 10,
                windowFrame: CGRect(x: 0, y: 0, width: 200, height: 200),
                ax: AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: "LINE"),
                cgEntry: CGWindowEntryRecord(
                    windowID: 10,
                    frame: CGRect(x: 0, y: 0, width: 200, height: 200),
                    layer: 0,
                    ownerPID: 4242,
                    ownerName: "LINE"
                ),
                captureEpoch: 1,
                captureImageSHA256: binding.frameSHA256
            )
            let observation = ReadinessObservation(
                applicationActive: true,
                targetFrontmost: true,
                freshWindow: FreshWindowObservation(
                    bundleID: binding.bundleID,
                    process: process,
                    windowID: 10,
                    frame: identity.windowFrame,
                    layer: 0,
                    isOnScreen: true
                ),
                currentEpoch: 1,
                currentBinding: binding,
                captureGeometry: CaptureGeometry(
                    windowFrame: identity.windowFrame,
                    captureBBox: identity.windowFrame,
                    scale: 1
                ),
                captureImageSize: CGSize(width: 200, height: 200),
                observedAtUptime: 10
            )
            let permit = try DispatchReadinessGate.mintPermit(
                identity: identity,
                candidate: candidate,
                observation: observation,
                now: 10
            )
            try GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: binding,
                intent: .saveAll(owner),
                sink: { [weak self] _, _ in
                    self?.lock.lock()
                    self?.saveAllMouseEvents += 1
                    self?.lock.unlock()
                },
                readinessCheck: { _, _ in true },
                processIdentityCheck: { _, _ in true },
                postEventAccessCheck: { true },
                now: 10
            )
            return digest("save-all-dispatch")
        }

        func observeChooser(owner: PersistentTransactionOwner) async throws -> LiveChooserEvidence {
            let runDir = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
            let post = runDir.appendingPathComponent("engine-postcondition.json")
            let tripwire = runDir.appendingPathComponent("engine-tripwire.json")
            let affirmation = ChooserAffirmation(
                windowID: 99,
                frame: CGRect(x: 5, y: 5, width: 300, height: 200),
                ownerPID: 4242,
                predicateID: "predicate-v2",
                affirmedAtISO8601: "2026-09-28T00:00:00Z"
            )
            try EvidenceIO.encodeJSON(PostconditionEvidenceArtifact(
                runID: owner.authorization.runID,
                outcome: "CHOOSER_VERIFIED",
                chooserAffirmation: affirmation
            )).write(to: post)
            try EvidenceIO.encodeJSON(TripwireEvidenceArtifact(
                runID: owner.authorization.runID,
                observations: []
            )).write(to: tripwire)
            return LiveChooserEvidence(
                postcondition: try BoundEvidenceDigest.load(
                    fileURL: post,
                    withinRunDirectory: runDir,
                    runID: owner.authorization.runID
                ),
                tripwire: try BoundEvidenceDigest.load(
                    fileURL: tripwire,
                    withinRunDirectory: runDir,
                    runID: owner.authorization.runID
                )
            )
        }

        func prepareDestination(owner: PersistentTransactionOwner) async throws -> String {
            digest("destination-prepared")
        }

        func confirmDestination(owner: PersistentTransactionOwner) async throws -> String {
            try GatedDestinationConfirmation.perform(
                owner: owner,
                action: "AXPressDefaultButton",
                readinessCheck: { true },
                dispatch: { [weak self] in
                    self?.lock.lock()
                    self?.confirmationPosts += 1
                    self?.lock.unlock()
                }
            )
            return digest("destination-confirmation")
        }

        func observeDownloadStarted(owner: PersistentTransactionOwner) async throws -> String {
            digest("download-confirmed")
        }

        func observeDownloadInProgress(owner: PersistentTransactionOwner) async throws -> String {
            digest("download-in-progress")
        }

        func observeFilesystemStable(owner: PersistentTransactionOwner) async throws -> String {
            digest("filesystem-stable")
        }

        func verifyContent(owner: PersistentTransactionOwner) async throws -> LiveContentEvidence {
            LiveContentEvidence(
                verification: StagingVerification(
                    outcome: .duplicateContentConfirmed,
                    fileCount: owner.authorization.expectedFileCount,
                    totalBytes: owner.authorization.expectedTotalBytes,
                    contentMultisetSHA256: owner.authorization.expectedContentMultisetSHA256,
                    detail: "synthetic exact accepted contract"
                ),
                evidenceSHA256: digest("content-verified")
            )
        }

        private func digest(_ string: String) -> String {
            EvidenceIO.sha256Hex(Data(string.utf8))
        }
    }

    private func setup() throws -> (URL, ImmutableRunAuthorization, PersistentTransactionOwner) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let stagingRoot = root.appendingPathComponent("staging")
        let run = stagingRoot.appendingPathComponent("run-1")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let auth = ImmutableRunAuthorization(
            runID: "run-1",
            goal: "Rev28 target album backup",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: stagingRoot,
            stagingRunDirectory: run
        )
        let ledgerURL = root.appendingPathComponent("ledger.jsonl")
        let owner = try PersistentTransactionOwner(
            authorization: auth,
            ledger: IntentLedger(fileURL: ledgerURL),
            checkpointURL: root.appendingPathComponent("ledger-head.anchor")
        )
        return (ledgerURL, auth, owner)
    }

    func testValidSyntheticTransactionUsesSameGuardedBoundariesAndReachesContentVerified() async throws {
        let (_, _, owner) = try setup()
        let adapter = FakeAdapter()
        let outcome = try await LiveExecutionEngine(owner: owner, adapter: adapter).run()

        guard case let .contentVerified(verification) = outcome else {
            return XCTFail("expected contentVerified, got \(outcome)")
        }
        XCTAssertEqual(verification.outcome, .duplicateContentConfirmed)
        XCTAssertEqual(adapter.saveAllMouseEvents, 3)
        XCTAssertEqual(adapter.confirmationPosts, 1)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 2)
        XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 2)
        XCTAssertEqual(owner.currentState, .contentVerified)
    }

    func testRestartAfterIrreversibleAttemptIsObserveOnlyAndPostsNothing() async throws {
        let (ledgerURL, auth, owner) = try setup()
        let firstAdapter = FakeAdapter()
        _ = try await firstAdapter.establish(state: .appReady, owner: owner)
        try await firstAdapter.dispatchSaveAll(owner: owner)
        XCTAssertEqual(firstAdapter.saveAllMouseEvents, 3)

        let resumed = try PersistentTransactionOwner(
            authorization: auth,
            ledger: IntentLedger(fileURL: ledgerURL),
            checkpointURL: ledgerURL.deletingLastPathComponent().appendingPathComponent("ledger-head.anchor"),
            requireCheckpointOnResume: true
        )
        let secondAdapter = FakeAdapter()
        let outcome = try await LiveExecutionEngine(owner: resumed, adapter: secondAdapter).run()
        guard case .observeOnlyResume = outcome else {
            return XCTFail("restart must be observe-only")
        }
        XCTAssertEqual(secondAdapter.saveAllMouseEvents, 0)
        XCTAssertEqual(secondAdapter.confirmationPosts, 0)
    }

    func testFailureBeforeSaveAllPostsZeroIrreversibleEvents() async throws {
        let (_, _, owner) = try setup()
        let adapter = FakeAdapter()
        adapter.failAtState = .albumDetailVerified
        do {
            _ = try await LiveExecutionEngine(owner: owner, adapter: adapter).run()
            XCTFail("expected failure")
        } catch {
            XCTAssertEqual(adapter.saveAllMouseEvents, 0)
            XCTAssertEqual(adapter.confirmationPosts, 0)
            XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
            XCTAssertEqual(owner.irreversibleOperationCounts.destinationConfirmation, 0)
        }
    }

    func testWrongTargetAuthorizationIsRejectedBeforeAnyAction() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let staging = root.appendingPathComponent("staging")
        let run = staging.appendingPathComponent("run")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let auth = ImmutableRunAuthorization(
            runID: "wrong",
            goal: "wrong",
            group: "wrong group",
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("impl".utf8)),
            stagingRoot: staging,
            stagingRunDirectory: run
        )
        let owner = try PersistentTransactionOwner(
            authorization: auth,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        )
        let adapter = FakeAdapter()
        await XCTAssertThrowsErrorAsync {
            _ = try await LiveExecutionEngine(owner: owner, adapter: adapter).run()
        }
        XCTAssertEqual(adapter.saveAllMouseEvents, 0)
    }
}

private func XCTAssertThrowsErrorAsync(
    _ expression: @escaping () async throws -> Void,
    file: StaticString = #filePath,
    line: UInt = #line
) async {
    do {
        try await expression()
        XCTFail("expected error", file: file, line: line)
    } catch {
        // expected
    }
}
