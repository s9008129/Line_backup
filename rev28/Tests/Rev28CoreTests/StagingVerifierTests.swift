import XCTest
@testable import Rev28Core

final class StagingVerifierTests: XCTestCase {
    private func record(_ name: String, _ size: UInt64, _ hash: String, decodable: Bool = true, mtime: TimeInterval = 10) -> StagingFileRecord {
        StagingFileRecord(name: name, size: size, modificationTime: mtime, sha256: hash, decodable: decodable)
    }

    private var goodRecords: [StagingFileRecord] {
        [
            record("a.jpg", 10, String(repeating: "a", count: 64)),
            record("b.jpg", 20, String(repeating: "b", count: 64)),
            record("c.png", 30, String(repeating: "c", count: 64)),
        ]
    }

    private func policy(for records: [StagingFileRecord]? = nil) -> StagingPolicy {
        let records = records ?? goodRecords
        return StagingPolicy(
            expectedFileCount: 3,
            expectedTotalBytes: records.reduce(0) { $0 + $1.size },
            expectedContentMultisetSHA256: StagingVerifier.contentMultisetDigest(records.map(\.sha256))
        )
    }

    func testExactContentPredicateConfirmsDuplicate() {
        let snapshot = StagingSnapshot(observedAt: 20, files: goodRecords)
        XCTAssertEqual(StagingVerifier.verify(snapshot: snapshot, policy: policy()).outcome, .duplicateContentConfirmed)
    }

    func testZeroByteAndPartialAreIncomplete() {
        var records = goodRecords
        records[2] = record("c.jpg.partial", 0, String(repeating: "c", count: 64))
        let result = StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 20, files: records), policy: policy())
        XCTAssertEqual(result.outcome, .stagingIncomplete)
    }

    func testUndecodableIsIncomplete() {
        var records = goodRecords
        records[2] = record("c.png", 30, String(repeating: "c", count: 64), decodable: false)
        XCTAssertEqual(
            StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 20, files: records), policy: policy()).outcome,
            .stagingIncomplete
        )
    }

    func testFourthFileIsExtraFiles() {
        var records = goodRecords
        records.append(record("d.jpg", 1, String(repeating: "d", count: 64)))
        XCTAssertEqual(
            StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 20, files: records), policy: policy()).outcome,
            .stagingExtraFiles
        )
    }

    func testSubdirectoryIsExtraFiles() {
        XCTAssertEqual(
            StagingVerifier.verify(
                snapshot: StagingSnapshot(observedAt: 20, files: goodRecords, subdirectories: ["nested"]),
                policy: policy()
            ).outcome,
            .stagingExtraFiles
        )
    }

    func testDuplicateHashHasDedicatedOutcome() {
        var records = goodRecords
        records[2] = record("c.png", 30, String(repeating: "b", count: 64))
        XCTAssertEqual(
            StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 20, files: records), policy: policy()).outcome,
            .stagingDuplicateContent
        )
    }

    func testContentMismatchHasDedicatedOutcome() {
        let wrongPolicy = StagingPolicy(
            expectedFileCount: 3,
            expectedTotalBytes: 60,
            expectedContentMultisetSHA256: String(repeating: "f", count: 64)
        )
        XCTAssertEqual(
            StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 20, files: goodRecords), policy: wrongPolicy).outcome,
            .contentMismatchAgainstAcceptedBaseline
        )
    }

    func testStabilityRequiresThreeEqualSamplesSpanAndQuiescence() {
        let records = goodRecords
        let snapshots = [
            StagingSnapshot(observedAt: 20, files: records),
            StagingSnapshot(observedAt: 22, files: records),
            StagingSnapshot(observedAt: 25, files: records),
        ]
        XCTAssertTrue(StagingVerifier.isStable(snapshots: snapshots))
    }

    func testUnstableSamplesReturnNamedOutcome() {
        let records = goodRecords.map { record($0.name, $0.size, $0.sha256, mtime: 24) }
        let snapshots = [
            StagingSnapshot(observedAt: 20, files: records),
            StagingSnapshot(observedAt: 22, files: records),
            StagingSnapshot(observedAt: 25, files: records),
        ]
        XCTAssertEqual(
            StagingVerifier.verifyStableSnapshots(snapshots, policy: policy()).outcome,
            .stagingUnstable
        )
    }

    func testRecentModificationIsNotQuiescent() {
        let records = goodRecords.map { record($0.name, $0.size, $0.sha256, mtime: 24) }
        let snapshots = [
            StagingSnapshot(observedAt: 20, files: records),
            StagingSnapshot(observedAt: 22, files: records),
            StagingSnapshot(observedAt: 25, files: records),
        ]
        XCTAssertFalse(StagingVerifier.isStable(snapshots: snapshots))
    }
}
