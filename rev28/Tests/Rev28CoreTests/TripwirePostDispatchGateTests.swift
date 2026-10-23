import Foundation
import XCTest
@testable import Rev28Core

/// Plan C7: a post-dispatch collection gap or collector failure can never
/// become an empty clean tripwire. The gate refuses, and the durable chooser
/// record refuses a gapped tripwire artifact.
final class TripwirePostDispatchGateTests: XCTestCase {
    private func makeJournal(started: Bool = true) throws -> (journal: FilesystemTripwireJournal, root: URL) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        let journal = FilesystemTripwireJournal(
            scope: TripwireScope(stagingRunDir: root, approvedRoot: root.deletingLastPathComponent()),
            monitoredRoots: [root]
        )
        if started {
            try journal.start()
            addTeardownBlock { journal.stop() }
        }
        return (journal, root)
    }

    func testInjectedCollectionGapIsDisclosedAndRefused() throws {
        let (journal, _) = try makeJournal()
        journal.markDispatchBoundary()
        XCTAssertNil(journal.postDispatchRefusalDetail(), "a started gap-free journal is a clean window")
        journal.injectCollectionGapForTesting("FSEvents reported kernel-dropped events")
        XCTAssertTrue(journal.hasCollectionGap)
        let detail = journal.postDispatchRefusalDetail()
        XCTAssertNotNil(detail)
        XCTAssertTrue(detail!.contains("kernel-dropped"), detail!)
    }

    func testStoppedJournalIsRefusedAfterTheDispatchBoundary() throws {
        let (journal, _) = try makeJournal(started: false)
        journal.markDispatchBoundary()
        let detail = journal.postDispatchRefusalDetail()
        XCTAssertEqual(detail, "collector is not running after the dispatch boundary")
    }

    func testGappedTripwireArtifactCannotBeRecordedAsChooserEvidence() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let staging = root.appendingPathComponent("staging")
        let run = staging.appendingPathComponent("run")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: "run-gap",
            goal: "goal",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("code".utf8)),
            stagingRoot: staging,
            stagingRunDirectory: run
        )
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        )
        try owner.initializeState(evidenceSHA256: EvidenceIO.sha256Hex(Data("APP_READY".utf8)))
        for state in [
            ExecutionState.groupReady, .albumListReady, .targetAlbumLocated,
            .albumDetailVerified, .ellipsisLocated, .menuVerified, .saveAllLocated,
        ] {
            try owner.transition(to: state, evidenceSHA256: EvidenceIO.sha256Hex(Data(state.rawValue.utf8)))
        }
        try EligibilityTestSupport.recordEligibility(on: owner)
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()

        let runDir = URL(fileURLWithPath: authorization.evidenceRunDirectory)
        let post = runDir.appendingPathComponent("gapped-post.json")
        let tripwire = runDir.appendingPathComponent("gapped-tripwire.json")
        try EvidenceIO.encodeJSON(PostconditionEvidenceArtifact(
            runID: authorization.runID,
            outcome: "CHOOSER_VERIFIED",
            chooserAffirmation: ChooserAffirmation(
                windowID: 3, frame: .zero, ownerPID: 42, predicateID: "predicate-v2",
                affirmedAtISO8601: "2026-09-28T00:00:00Z"
            )
        )).write(to: post)
        try EvidenceIO.encodeJSON(TripwireEvidenceArtifact(
            runID: authorization.runID,
            observations: [],
            collectionGap: "FSEvents reported kernel-dropped events"
        )).write(to: tripwire)
        XCTAssertThrowsError(try owner.recordChooserVerified(
            postconditionEvidence: try BoundEvidenceDigest.load(fileURL: post, withinRunDirectory: runDir, runID: authorization.runID),
            tripwireEvidence: try BoundEvidenceDigest.load(fileURL: tripwire, withinRunDirectory: runDir, runID: authorization.runID)
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .authorizationMismatch)
        }
        XCTAssertFalse(owner.ledger.entries.contains { $0.kind == "postcondition.chooserVerified" })
    }
}
