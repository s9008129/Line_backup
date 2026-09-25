import Foundation
import XCTest
@testable import Rev28Core

final class IntentLedgerTests: XCTestCase {
    private func temporaryLedger() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root.appendingPathComponent("ledger.jsonl")
    }

    func testHashChainReloadsAndVerifies() throws {
        let url = try temporaryLedger()
        let ledger = try IntentLedger(fileURL: url)
        try ledger.append(kind: "intent.saveAll", payload: ["risk": "IRREVERSIBLE_SIDE_EFFECT"])
        try ledger.append(kind: "dispatch.saveAll")
        let reloaded = try IntentLedger(fileURL: url)
        XCTAssertEqual(reloaded.entries.count, 2)
        XCTAssertNoThrow(try IntentLedger.verify(entries: reloaded.entries))
    }

    func testResumeAfterIrreversibleDispatchIsObserveOnlyAndUnarmed() throws {
        let url = try temporaryLedger()
        let ledger = try IntentLedger(fileURL: url)
        try ledger.append(kind: "dispatch.saveAll")
        let decision = LedgerResume.decide(entries: ledger.entries)
        XCTAssertEqual(decision.mode, "observeOnly")
        XCTAssertEqual(decision.allowedNewIrreversibleDispatches, 0)
        XCTAssertTrue(LedgerResume.wouldRefuseNewIrreversibleDispatch(entries: ledger.entries))
    }

    func testFreshReviewedDecisionCanArmAtMostOneFutureIrreversibleDispatch() throws {
        let url = try temporaryLedger()
        let ledger = try IntentLedger(fileURL: url)
        try ledger.append(kind: "dispatch.saveAll")
        try ledger.append(kind: LedgerResume.freshReviewedDecisionKind, payload: ["armIrreversible": "1"])
        XCTAssertEqual(LedgerResume.decide(entries: ledger.entries).allowedNewIrreversibleDispatches, 1)
    }

    func testTamperedLedgerFailsReload() throws {
        let url = try temporaryLedger()
        let ledger = try IntentLedger(fileURL: url)
        try ledger.append(kind: "dispatch.saveAll")
        var text = try String(contentsOf: url, encoding: .utf8)
        text = text.replacingOccurrences(of: "dispatch.saveAll", with: "dispatch.other")
        try text.write(to: url, atomically: true, encoding: .utf8)
        XCTAssertThrowsError(try IntentLedger(fileURL: url))
    }
    func testSaveAllEmpiricalClassificationIsConservativeAndPersisted() throws {
        let preSideEffect = SaveAllEmpiricalClassRecord.derive(
            postconditionOutcome: "CHOOSER_VERIFIED",
            chooserAffirmed: true,
            attributableFilesystemWriteObservedBeforeChooser: false,
            postconditionEvidenceSHA256: String(repeating: "a", count: 64),
            tripwireEvidenceSHA256: String(repeating: "b", count: 64)
        )
        XCTAssertEqual(preSideEffect.classification, .preSideEffectObserved)

        let indeterminate = SaveAllEmpiricalClassRecord.derive(
            postconditionOutcome: "NO_CHOOSER_OBSERVED",
            chooserAffirmed: false,
            attributableFilesystemWriteObservedBeforeChooser: false,
            postconditionEvidenceSHA256: String(repeating: "c", count: 64),
            tripwireEvidenceSHA256: String(repeating: "d", count: 64)
        )
        XCTAssertEqual(indeterminate.classification, .irreversibleOrIndeterminate)

        let url = try temporaryLedger()
        let ledger = try IntentLedger(fileURL: url)
        try preSideEffect.append(to: ledger)
        XCTAssertEqual(ledger.count(kind: "saveAllEmpiricalClassRecord"), 1)
        XCTAssertEqual(ledger.entries.last?.payload["classification"], "PRE_SIDE_EFFECT_OBSERVED")
    }
}
