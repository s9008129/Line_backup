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
        let legacyClaim = SaveAllEmpiricalClassRecord.derive(
            postconditionOutcome: "CHOOSER_VERIFIED",
            chooserAffirmed: true,
            attributableFilesystemWriteObservedBeforeChooser: false,
            postconditionEvidenceSHA256: "placeholder",
            tripwireEvidenceSHA256: "placeholder"
        )
        XCTAssertEqual(legacyClaim.classification, .irreversibleOrIndeterminate)

        let evidenceRun = urlForEvidenceDirectory()
        try FileManager.default.createDirectory(at: evidenceRun, withIntermediateDirectories: true)
        let postconditionFile = evidenceRun.appendingPathComponent("postcondition.json")
        let tripwireFile = evidenceRun.appendingPathComponent("tripwire.json")
        let affirmation = ChooserAffirmation(
            windowID: 3, frame: .zero, ownerPID: 42, predicateID: "predicate-v2",
            affirmedAtISO8601: "2026-09-28T00:00:00Z"
        )
        try EvidenceIO.encodeJSON(PostconditionEvidenceArtifact(
            runID: "run-1", outcome: "CHOOSER_VERIFIED", chooserAffirmation: affirmation
        )).write(to: postconditionFile)
        try EvidenceIO.encodeJSON(TripwireEvidenceArtifact(
            runID: "run-1", observations: []
        )).write(to: tripwireFile)
        let preSideEffect = try SaveAllEmpiricalClassRecord.deriveValidated(
            runID: "run-1",
            postconditionEvidence: try BoundEvidenceDigest.load(fileURL: postconditionFile, withinRunDirectory: evidenceRun, runID: "run-1"),
            tripwireEvidence: try BoundEvidenceDigest.load(fileURL: tripwireFile, withinRunDirectory: evidenceRun, runID: "run-1")
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

    private func urlForEvidenceDirectory() -> URL {
        FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("run-1")
    }

    func testAnchorDetectsRollbackAndStaleWriterIsRejected() throws {
        let url = try temporaryLedger()
        let anchorURL = url.deletingLastPathComponent().appendingPathComponent("head.anchor")
        let writerA = try IntentLedger(fileURL: url)
        try writerA.append(kind: "first")

        let stale = try IntentLedger(fileURL: url)
        try writerA.append(kind: "second")
        try writerA.writeHeadAnchor(to: anchorURL)
        XCTAssertThrowsError(try stale.append(kind: "stale"))
        let data = try Data(contentsOf: url)
        let firstLineEnd = try XCTUnwrap(data.firstIndex(of: 10))
        try Data(data[...firstLineEnd]).write(to: url)
        XCTAssertThrowsError(try IntentLedger.verifyHeadAnchor(fileURL: url, anchorURL: anchorURL))
    }

    func testConcurrentLedgerWritersCannotBothAppendFromSameHead() throws {
        let url = try temporaryLedger()
        let first = try IntentLedger(fileURL: url)
        let second = try IntentLedger(fileURL: url)
        let group = DispatchGroup()
        let queue = DispatchQueue(label: "ledger-writers", attributes: .concurrent)
        let lock = NSLock()
        var successes = 0
        var failures = 0
        for ledger in [first, second] {
            group.enter()
            queue.async {
                defer { group.leave() }
                do {
                    try ledger.append(kind: "writer")
                    lock.lock(); successes += 1; lock.unlock()
                } catch {
                    lock.lock(); failures += 1; lock.unlock()
                }
            }
        }
        XCTAssertEqual(group.wait(timeout: .now() + 5), .success)
        XCTAssertEqual(successes, 1)
        XCTAssertEqual(failures, 1)
        XCTAssertEqual(try IntentLedger(fileURL: url).entries.count, 1)
    }
}
