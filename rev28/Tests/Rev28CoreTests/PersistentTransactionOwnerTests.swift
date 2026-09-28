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

    func testRestartAfterSaveAllIntentCannotRearmOrDispatch() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()

        let resumed = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        XCTAssertThrowsError(try resumed.reserveSaveAll())
        XCTAssertThrowsError(try resumed.markSaveAllAttempted())
        XCTAssertEqual(resumed.irreversibleOperationCounts.saveAll, 2)
    }

    func testAuthorizationIsImmutableAndConfirmationRequiresVerifiedChooser() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()
        XCTAssertThrowsError(try owner.reserveDestinationConfirmation(action: "ReturnKey"))
        let runDir = URL(fileURLWithPath: authorization.stagingRunDirectory)
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
