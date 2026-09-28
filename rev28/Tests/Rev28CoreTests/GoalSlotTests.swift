import Foundation
import XCTest
@testable import Rev28Core

final class GoalSlotTests: XCTestCase {
    private func setup() throws -> (root: URL, authorization: ImmutableRunAuthorization) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let staging = root.appendingPathComponent("staging")
        let run = staging.appendingPathComponent("run-1")
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: "run-1",
            goal: "Rev28 target album backup",
            group: "target group",
            album: "target album",
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: staging,
            stagingRunDirectory: run
        )
        return (root, authorization)
    }

    private func evidence(_ label: String) -> String {
        EvidenceIO.sha256Hex(Data(label.utf8))
    }

    private func walkToSaveAllLocated(_ owner: PersistentTransactionOwner) throws {
        try owner.initializeState(evidenceSHA256: evidence(ExecutionState.appReady.rawValue))
        for state in [
            ExecutionState.groupReady, .albumListReady, .targetAlbumLocated,
            .albumDetailVerified, .ellipsisLocated, .menuVerified, .saveAllLocated,
        ] {
            try owner.transition(to: state, evidenceSHA256: evidence(state.rawValue))
        }
    }

    func testFreshSlotIsCreatedAndVerifiedOnReopen() throws {
        let (root, authorization) = try setup()
        let directory = root.appendingPathComponent("goal-slots")
        let created = try GoalSlot.open(directory: directory, authorization: authorization)
        XCTAssertEqual(created.runID, authorization.runID)
        XCTAssertFalse(created.entitlementConsumed)

        let reopened = try GoalSlot.open(directory: directory, authorization: authorization)
        XCTAssertEqual(reopened, created)
        XCTAssertTrue(FileManager.default.fileExists(atPath: GoalSlot.fileURL(in: directory, authorization: authorization).path))
    }

    /// The slot install must be a single atomic replace: a concurrent reader
    /// must never observe a missing or partially written slot. The earlier
    /// remove-then-move sequence failed this test by construction (the
    /// destination did not exist between the two calls).
    func testSlotReplaceIsAtomicUnderConcurrentReads() throws {
        let (root, authorization) = try setup()
        let directory = root.appendingPathComponent("goal-slots")
        let created = try GoalSlot.open(directory: directory, authorization: authorization)
        let url = GoalSlot.fileURL(in: directory, authorization: authorization)

        let reads = NSLock()
        var readFailures: [String] = []
        var reading = true
        let reader = Thread {
            while true {
                reads.lock()
                let keepGoing = reading
                reads.unlock()
                if !keepGoing { return }
                do {
                    let data = try Data(contentsOf: url)
                    _ = try JSONDecoder().decode(GoalSlotRecord.self, from: data)
                } catch {
                    reads.lock()
                    readFailures.append(String(describing: error))
                    reads.unlock()
                }
            }
        }
        reader.start()
        defer {
            reads.lock()
            reading = false
            reads.unlock()
        }
        for index in 0..<300 {
            let record = GoalSlotRecord(
                goal: created.goal,
                group: created.group,
                album: created.album,
                stagingRoot: created.stagingRoot,
                stagingRunDirectory: created.stagingRunDirectory,
                runID: "\(created.runID)-rewrite-\(index)",
                boundAtISO8601: created.boundAtISO8601
            )
            try GoalSlot.write(record, to: url)
        }
        reads.lock()
        let failures = readFailures.count
        reads.unlock()
        XCTAssertEqual(failures, 0, "concurrent reader observed a missing/partial slot \(failures) times")
        let decoded = try JSONDecoder().decode(GoalSlotRecord.self, from: Data(contentsOf: url))
        XCTAssertEqual(decoded.runID, "\(created.runID)-rewrite-299")
        let residue = try FileManager.default.contentsOfDirectory(atPath: directory.path)
            .filter { $0.hasPrefix(".tmp-") }
        XCTAssertTrue(residue.isEmpty, "temp residue left behind: \(residue)")
    }

    func testDifferentRunIdentityCannotClaimTheSameGoalSlot() throws {
        let (root, authorization) = try setup()
        let directory = root.appendingPathComponent("goal-slots")
        _ = try GoalSlot.open(directory: directory, authorization: authorization)

        let otherRun = URL(fileURLWithPath: authorization.stagingRunDirectory).deletingLastPathComponent().appendingPathComponent("run-2")
        try FileManager.default.createDirectory(at: otherRun, withIntermediateDirectories: true)
        let other = ImmutableRunAuthorization(
            runID: "run-2",
            goal: authorization.goal,
            group: authorization.group,
            album: authorization.album,
            planSHA256: authorization.planSHA256,
            reviewedImplementationSHA256: authorization.reviewedImplementationSHA256,
            stagingRoot: URL(fileURLWithPath: authorization.stagingRoot),
            stagingRunDirectory: otherRun
        )
        XCTAssertThrowsError(try GoalSlot.open(directory: directory, authorization: other)) { error in
            guard case GoalSlotError.goalSlotConflict = error else {
                return XCTFail("expected goalSlotConflict, got \(error)")
            }
        }
    }

    func testEntitlementConsumptionIsOneWay() throws {
        let (root, authorization) = try setup()
        let directory = root.appendingPathComponent("goal-slots")
        _ = try GoalSlot.open(directory: directory, authorization: authorization)

        let consumed = try GoalSlot.consumeOneShotEntitlement(directory: directory, authorization: authorization)
        XCTAssertTrue(consumed.entitlementConsumed)
        XCTAssertNotNil(consumed.consumedAtISO8601)

        XCTAssertThrowsError(try GoalSlot.consumeOneShotEntitlement(directory: directory, authorization: authorization)) { error in
            XCTAssertEqual(error as? GoalSlotError, .entitlementAlreadyConsumed)
        }
        XCTAssertEqual(try GoalSlot.load(directory: directory, authorization: authorization)?.entitlementConsumed, true)
    }

    func testReserveSaveAllRequiresSaveAllLocatedState() throws {
        let (root, authorization) = try setup()
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        )
        XCTAssertThrowsError(try owner.reserveSaveAll()) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .saveAllRequiresLocatedState)
        }
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 0)
        XCTAssertEqual(try GoalSlot.load(directory: owner.goalSlotDirectory, authorization: authorization)?.entitlementConsumed, false)
    }

    func testReserveSaveAllConsumesGoalSlotEntitlement() throws {
        let (root, authorization) = try setup()
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        )
        try walkToSaveAllLocated(owner)
        try EligibilityTestSupport.recordEligibility(on: owner)
        try owner.reserveSaveAll()
        XCTAssertEqual(try GoalSlot.load(directory: owner.goalSlotDirectory, authorization: authorization)?.entitlementConsumed, true)
    }

    func testConsumedSlotWithEmptyOrMovedLedgerCannotResetEntitlement() throws {
        let (root, authorization) = try setup()
        let ledgerURL = root.appendingPathComponent("ledger.jsonl")
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: ledgerURL)
        )
        try walkToSaveAllLocated(owner)
        try EligibilityTestSupport.recordEligibility(on: owner)
        try owner.reserveSaveAll()
        try owner.markSaveAllAttempted()

        try FileManager.default.removeItem(at: ledgerURL)
        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: ledgerURL)
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .goalSlotEntitlementConsumed)
        }
        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: root.appendingPathComponent("other-ledger.jsonl"))
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .goalSlotEntitlementConsumed)
        }
    }
}
