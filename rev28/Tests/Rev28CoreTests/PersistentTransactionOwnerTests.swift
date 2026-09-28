import Foundation
import XCTest
@testable import Rev28Core

final class PersistentTransactionOwnerTests: XCTestCase {
    private func setup() throws -> (URL, ImmutableRunAuthorization) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let staging = root.appendingPathComponent("staging")
        let run = staging.appendingPathComponent("run-1")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: "run-1",
            goal: "LINE album backup",
            group: "target group",
            album: "target album",
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: staging,
            stagingRunDirectory: run
        )
        return (root.appendingPathComponent("ledger.jsonl"), authorization)
    }

    private func evidence(_ label: String) -> String {
        EvidenceIO.sha256Hex(Data(label.utf8))
    }

    /// Save All reservation is only legal at a freshly proved SAVE_ALL_LOCATED
    /// state (R4 C4), so owner-level tests must walk the pre-dispatch states.
    private func walkToSaveAllLocated(_ owner: PersistentTransactionOwner) throws {
        try owner.initializeState(evidenceSHA256: evidence(ExecutionState.appReady.rawValue))
        for state in [
            ExecutionState.groupReady, .albumListReady, .targetAlbumLocated,
            .albumDetailVerified, .ellipsisLocated, .menuVerified, .saveAllLocated,
        ] {
            try owner.transition(to: state, evidenceSHA256: evidence(state.rawValue))
        }
    }

    func testRestartAfterSaveAllIntentCannotRearmOrDispatch() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try walkToSaveAllLocated(owner)
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()

        let resumed = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        XCTAssertTrue(resumed.isObserveOnlyResume)
        XCTAssertThrowsError(try resumed.reserveSaveAll())
        XCTAssertThrowsError(try resumed.markSaveAllAttempted())
        XCTAssertEqual(resumed.irreversibleOperationCounts.saveAll, 2)

        let runDir = URL(fileURLWithPath: authorization.evidenceRunDirectory)
        let post = runDir.appendingPathComponent("resume-post.json")
        let tripwire = runDir.appendingPathComponent("resume-tripwire.json")
        let affirmation = ChooserAffirmation(
            windowID: 3, frame: .zero, ownerPID: 42, predicateID: "predicate-v2",
            affirmedAtISO8601: "2026-09-28T00:00:00Z"
        )
        try EvidenceIO.encodeJSON(PostconditionEvidenceArtifact(
            runID: authorization.runID, outcome: "CHOOSER_VERIFIED", chooserAffirmation: affirmation
        )).write(to: post)
        try EvidenceIO.encodeJSON(TripwireEvidenceArtifact(
            runID: authorization.runID, observations: []
        )).write(to: tripwire)
        try resumed.recordChooserVerified(
            postconditionEvidence: try BoundEvidenceDigest.load(fileURL: post, withinRunDirectory: runDir, runID: authorization.runID),
            tripwireEvidence: try BoundEvidenceDigest.load(fileURL: tripwire, withinRunDirectory: runDir, runID: authorization.runID)
        )
        XCTAssertThrowsError(try resumed.reserveDestinationConfirmation(action: "AXPressDefaultButton"))
    }

    func testProductionCheckpointIsRequiredAndDetectsRollback() throws {
        let (url, authorization) = try setup()
        let checkpoint = url.deletingLastPathComponent().appendingPathComponent("ledger-head.anchor")
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: url),
            checkpointURL: checkpoint,
            requireCheckpointOnResume: true
        )
        try walkToSaveAllLocated(owner)
        try owner.reserveSaveAll()
        XCTAssertTrue(FileManager.default.fileExists(atPath: checkpoint.path))

        let data = try Data(contentsOf: url)
        let firstNewline = try XCTUnwrap(data.firstIndex(of: 10))
        try Data(data[...firstNewline]).write(to: url)

        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: url),
            checkpointURL: checkpoint,
            requireCheckpointOnResume: true
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .ledgerCheckpointInvalid)
        }
    }

    func testAuthorizationBindsAcceptedContentContract() throws {
        let (_, authorization) = try setup()
        XCTAssertEqual(authorization.expectedFileCount, 57)
        XCTAssertEqual(authorization.expectedTotalBytes, 17_924_900)
        XCTAssertEqual(
            authorization.expectedContentMultisetSHA256,
            "ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf"
        )
        XCTAssertEqual(
            authorization.baselineTripwireSHA256,
            ImmutableRunAuthorization.acceptedBaselineTripwireSHA256
        )
    }

    func testAuthorizationIsImmutableAndConfirmationRequiresVerifiedChooser() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try walkToSaveAllLocated(owner)
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()
        XCTAssertThrowsError(try owner.reserveDestinationConfirmation(action: "ReturnKey"))
        let runDir = URL(fileURLWithPath: authorization.evidenceRunDirectory)
        let post = runDir.appendingPathComponent("post.json")
        let tripwire = runDir.appendingPathComponent("tripwire.json")
        let affirmation = ChooserAffirmation(
            windowID: 3, frame: .zero, ownerPID: 42, predicateID: "predicate-v2",
            affirmedAtISO8601: "2026-09-28T00:00:00Z"
        )
        try EvidenceIO.encodeJSON(PostconditionEvidenceArtifact(
            runID: authorization.runID, outcome: "CHOOSER_VERIFIED", chooserAffirmation: affirmation
        )).write(to: post)
        try EvidenceIO.encodeJSON(TripwireEvidenceArtifact(
            runID: authorization.runID, observations: []
        )).write(to: tripwire)
        try owner.recordChooserVerified(
            postconditionEvidence: try BoundEvidenceDigest.load(fileURL: post, withinRunDirectory: runDir, runID: authorization.runID),
            tripwireEvidence: try BoundEvidenceDigest.load(fileURL: tripwire, withinRunDirectory: runDir, runID: authorization.runID)
        )
        try owner.reserveDestinationConfirmation(action: "AXPressDefaultButton")
        try owner.markDestinationConfirmationAttempted()
        XCTAssertThrowsError(try owner.reserveDestinationConfirmation(action: "ReturnKey"))

        var mismatched = authorization
        mismatched = ImmutableRunAuthorization(
            runID: mismatched.runID, goal: mismatched.goal, group: mismatched.group, album: "different",
            planSHA256: mismatched.planSHA256,
            reviewedImplementationSHA256: mismatched.reviewedImplementationSHA256,
            stagingRoot: URL(fileURLWithPath: mismatched.stagingRoot),
            stagingRunDirectory: URL(fileURLWithPath: mismatched.stagingRunDirectory)
        )
        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: mismatched, ledger: IntentLedger(fileURL: url)
        ))
    }
}
