import Foundation
import XCTest
@testable import Rev28Core

final class GoalSlotTests: XCTestCase {
    private func fixture() throws -> (controlRoot: URL, authorization: ImmutableRunAuthorization, ledgerURL: URL) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let controlRoot = root.appendingPathComponent("control")
        let stagingRoot = root.appendingPathComponent("staging")
        let run = stagingRoot.appendingPathComponent("run-1")
        try FileManager.default.createDirectory(at: controlRoot, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        let authorization = ImmutableRunAuthorization(
            runID: "run-1",
            goal: "Rev28 target album backup",
            group: "旻謙允禎成長日記",
            album: "2024/05/13～05/17",
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: stagingRoot,
            stagingRunDirectory: run
        )
        return (controlRoot, authorization, root.appendingPathComponent("ledger.jsonl"))
    }

    func testEntitlementIsSingleUseAcrossNewLedgerAndRunIdentity() throws {
        let (controlRoot, authorization, ledgerURL) = try fixture()
        let identity = GoalSlotIdentity(
            goal: authorization.goal,
            group: authorization.group,
            album: authorization.album,
            stagingRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory)
        )
        XCTAssertTrue(identity.matches(authorization))

        let firstSlot = try GoalSlot(controlRoot: controlRoot, identity: identity)
        XCTAssertFalse(firstSlot.entitlementConsumed)
        try firstSlot.consumeEntitlement(ledgerFileURL: ledgerURL, runID: authorization.runID)
        XCTAssertTrue(firstSlot.entitlementConsumed)
        XCTAssertThrowsError(try firstSlot.consumeEntitlement(ledgerFileURL: ledgerURL, runID: authorization.runID)) { error in
            guard case .entitlementAlreadyConsumed = error as? GoalSlotError else {
                return XCTFail("expected entitlementAlreadyConsumed, got \(error)")
            }
        }

        // A second owner of the same goal fails closed while the first holds the
        // exclusive lock, and a brand-new ledger path / run ID cannot re-arm the
        // spent entitlement once the lock is available again.
        XCTAssertThrowsError(try GoalSlot(controlRoot: controlRoot, identity: identity)) { error in
            guard case .alreadyLocked = error as? GoalSlotError else {
                return XCTFail("expected alreadyLocked, got \(error)")
            }
        }
        let replacementLedger = ledgerURL.deletingLastPathComponent().appendingPathComponent("other-ledger.jsonl")
        let persistedState = try JSONDecoder().decode(
            GoalSlotState.self,
            from: Data(contentsOf: firstSlot.stateURL)
        )
        XCTAssertTrue(persistedState.entitlementConsumed)
        XCTAssertEqual(persistedState.consumedByRunID, authorization.runID)
        XCTAssertEqual(
            persistedState.consumedByLedgerPath,
            ledgerURL.resolvingSymlinksInPath().standardizedFileURL.path
        )
        XCTAssertNotEqual(
            persistedState.consumedByLedgerPath,
            replacementLedger.resolvingSymlinksInPath().standardizedFileURL.path
        )
    }

    func testSecondAcquisitionAfterReleaseStillObservesConsumedState() throws {
        let (controlRoot, authorization, ledgerURL) = try fixture()
        let identity = GoalSlotIdentity(
            goal: authorization.goal,
            group: authorization.group,
            album: authorization.album,
            stagingRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory)
        )
        do {
            let slot = try GoalSlot(controlRoot: controlRoot, identity: identity)
            try slot.consumeEntitlement(ledgerFileURL: ledgerURL, runID: authorization.runID)
        }
        let second = try GoalSlot(controlRoot: controlRoot, identity: identity)
        XCTAssertTrue(second.entitlementConsumed)
        XCTAssertThrowsError(try second.consumeEntitlement(
            ledgerFileURL: ledgerURL.deletingLastPathComponent().appendingPathComponent("fresh-ledger.jsonl"),
            runID: "brand-new-run"
        ))
    }

    func testCorruptSlotStateFailsClosed() throws {
        let (controlRoot, authorization, ledgerURL) = try fixture()
        let identity = GoalSlotIdentity(
            goal: authorization.goal,
            group: authorization.group,
            album: authorization.album,
            stagingRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory)
        )
        do {
            let probe = try GoalSlot(controlRoot: controlRoot, identity: identity)
            try Data("not-json".utf8).write(to: probe.stateURL)
        }
        _ = ledgerURL
        XCTAssertThrowsError(try GoalSlot(controlRoot: controlRoot, identity: identity)) { error in
            guard case .slotStateCorrupt = error as? GoalSlotError else {
                return XCTFail("expected slotStateCorrupt, got \(error)")
            }
        }
    }

    func testGoalSlotRefusesAuthorizationMismatch() throws {
        let (controlRoot, authorization, _) = try fixture()
        let identity = GoalSlotIdentity(
            goal: authorization.goal,
            group: authorization.group,
            album: "different album",
            stagingRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory)
        )
        let slot = try GoalSlot(controlRoot: controlRoot, identity: identity)
        XCTAssertThrowsError(try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)),
            goalSlot: slot
        )) { error in
            XCTAssertEqual(error as? PersistentTransactionError, .authorizationMismatch)
        }
    }

    func testOwnerConsumesGoalSlotEntitlementBeforeTheLedgerIntent() throws {
        let (controlRoot, authorization, ledgerURL) = try fixture()
        let identity = GoalSlotIdentity(
            goal: authorization.goal,
            group: authorization.group,
            album: authorization.album,
            stagingRunDirectory: URL(fileURLWithPath: authorization.stagingRunDirectory)
        )
        let slot = try GoalSlot(controlRoot: controlRoot, identity: identity)
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: ledgerURL),
            goalSlot: slot
        )
        try owner.reserveSaveAll()
        XCTAssertTrue(slot.entitlementConsumed)
        XCTAssertEqual(owner.irreversibleOperationCounts.saveAll, 1)

        // The entitlement is spent BEFORE the intent record: a rollback of the
        // ledger cannot re-arm it.
        let lines = try XCTUnwrap(String(data: try Data(contentsOf: ledgerURL), encoding: .utf8))
            .split(separator: "\n")
            .filter { !$0.isEmpty }
        XCTAssertGreaterThanOrEqual(lines.count, 2)
        try Data((lines.dropLast().joined(separator: "\n") + "\n").utf8).write(to: ledgerURL)
        let resumed = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: IntentLedger(fileURL: ledgerURL),
            goalSlot: slot
        )
        XCTAssertThrowsError(try resumed.reserveSaveAll()) { error in
            guard case .goalSlotEntitlementConsumed = error as? PersistentTransactionError else {
                return XCTFail("expected goalSlotEntitlementConsumed, got \(error)")
            }
        }
    }
}
