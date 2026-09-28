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

    private func chooserEvidence(
        authorization: ImmutableRunAuthorization,
        label: String
    ) throws -> LiveChooserEvidence {
        let runDir = URL(fileURLWithPath: authorization.evidenceRunDirectory)
        let post = runDir.appendingPathComponent("\(label)-post.json")
        let tripwire = runDir.appendingPathComponent("\(label)-tripwire.json")
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
        return LiveChooserEvidence(
            postcondition: try BoundEvidenceDigest.load(fileURL: post, withinRunDirectory: runDir, runID: authorization.runID),
            tripwire: try BoundEvidenceDigest.load(fileURL: tripwire, withinRunDirectory: runDir, runID: authorization.runID)
        )
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
        try EligibilityTestSupport.recordEligibility(on: owner)
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
        try EligibilityTestSupport.recordEligibility(on: owner)
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

    func testReserveSaveAllRefusesWhenDurableBudgetsAreExhausted() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try walkToSaveAllLocated(owner)
        try EligibilityTestSupport.recordEligibility(on: owner)
        try owner.recordCandidateRevalidation(blockerKey: "saveAll", passed: false)
        XCTAssertThrowsError(try owner.recordCandidateRevalidation(blockerKey: "saveAll", passed: false)) {
            XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
        }
        // The plan's "reversible/revalidation budgets not exhausted" entry
        // condition is rechecked durably: the two consecutive failures abort
        // the run, and the refusal must leave the one-shot entitlement
        // untouched.
        XCTAssertThrowsError(try owner.reserveSaveAll()) {
            XCTAssertEqual($0 as? PersistentTransactionError, .phaseBBudgetExhausted)
        }
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        let slot = try GoalSlot.load(directory: owner.goalSlotDirectory, authorization: authorization)
        XCTAssertEqual(slot?.entitlementConsumed, false)
    }

    func testReversibleDispatchRefusesAfterTwoConsecutiveRevalidationFailures() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try owner.recordCandidateRevalidation(blockerKey: "chooser.click", passed: false)
        try owner.recordReversibleDispatch(action: "chooser.click", blockerKey: "chooser.click")
        XCTAssertThrowsError(try owner.recordCandidateRevalidation(blockerKey: "chooser.click", passed: false)) {
            XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
        }
        // A durable abort must gate every later reversible primitive, not
        // just the caller that observed the second failure.
        XCTAssertThrowsError(try owner.recordReversibleDispatch(action: "chooser.click", blockerKey: "chooser.click")) {
            XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
        }
        XCTAssertEqual(owner.reversibleDispatchCount, 1)
        try owner.recordCandidateRevalidation(blockerKey: "chooser.click", passed: true)
        try owner.recordReversibleDispatch(action: "chooser.click", blockerKey: "chooser.click")
        XCTAssertEqual(owner.reversibleDispatchCount, 2)
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
        try EligibilityTestSupport.recordEligibility(on: owner)
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
        try owner.transition(to: .chooserVerified, evidenceSHA256: evidence("chooser-verified"))
        try owner.transition(to: .destinationPrepared, evidenceSHA256: evidence("destination-prepared"))
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

    func testChooserVerificationRequiresDispatchedSaveAllAndIsOneShot() throws {
        let (url, authorization) = try setup()
        let owner = try PersistentTransactionOwner(authorization: authorization, ledger: IntentLedger(fileURL: url))
        try walkToSaveAllLocated(owner)

        // No Save All attempt exists yet: even well-formed chooser evidence cannot
        // create a chooser history for an undispatched Save All.
        let early = try chooserEvidence(authorization: authorization, label: "early")
        XCTAssertThrowsError(try owner.recordChooserVerified(
            postconditionEvidence: early.postcondition,
            tripwireEvidence: early.tripwire
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .authorizationMismatch)
        }

        try EligibilityTestSupport.recordEligibility(on: owner)
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()
        let recorded = try chooserEvidence(authorization: authorization, label: "recorded")
        try owner.recordChooserVerified(
            postconditionEvidence: recorded.postcondition,
            tripwireEvidence: recorded.tripwire
        )

        // The verification record is one-shot: a duplicate would forge a second
        // bound chooser history for the same run.
        XCTAssertThrowsError(try owner.recordChooserVerified(
            postconditionEvidence: recorded.postcondition,
            tripwireEvidence: recorded.tripwire
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .chooserVerificationAlreadyRecorded)
        }

        // A ledger whose state advanced past SAVE_ALL_LOCATED without a recorded
        // verification cannot retroactively accept chooser evidence either.
        let (lateURL, lateAuthorization) = try setup()
        let lateOwner = try PersistentTransactionOwner(
            authorization: lateAuthorization,
            ledger: IntentLedger(fileURL: lateURL)
        )
        try walkToSaveAllLocated(lateOwner)
        try EligibilityTestSupport.recordEligibility(on: lateOwner)
        try lateOwner.reserveSaveAll()
        try lateOwner.markSaveAllAttempted()
        try lateOwner.transition(to: .chooserVerified, evidenceSHA256: evidence("chooser-verified"))
        let late = try chooserEvidence(authorization: lateAuthorization, label: "late")
        XCTAssertThrowsError(try lateOwner.recordChooserVerified(
            postconditionEvidence: late.postcondition,
            tripwireEvidence: late.tripwire
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .chooserVerificationNotPermitted)
        }
    }
}
