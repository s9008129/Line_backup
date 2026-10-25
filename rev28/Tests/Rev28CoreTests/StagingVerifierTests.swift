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

    func testEqualTailSpanIsMeasuredAfterLastChange() {
        let records = goodRecords
        let snapshots = [
            StagingSnapshot(observedAt: 0, files: []),
            StagingSnapshot(observedAt: 10, files: records),
            StagingSnapshot(observedAt: 10.1, files: records),
            StagingSnapshot(observedAt: 10.2, files: records),
        ]
        XCTAssertFalse(
            StagingVerifier.isStable(snapshots: snapshots),
            "a recent change followed by rapid equal samples must not borrow the older sample's elapsed time"
        )
        XCTAssertEqual(
            StagingVerifier.verifyStableSnapshots(snapshots, policy: policy()).outcome,
            .stagingUnstable
        )
    }

    func testLongEqualTailAfterOlderDifferentSampleIsStable() {
        let records = goodRecords
        let snapshots = [
            StagingSnapshot(observedAt: 0, files: []),
            StagingSnapshot(observedAt: 10, files: records),
            StagingSnapshot(observedAt: 12, files: records),
            StagingSnapshot(observedAt: 15, files: records),
        ]
        XCTAssertTrue(StagingVerifier.isStable(snapshots: snapshots))
    }

    func testSnapshotIncludesHiddenFilesAndTheyCannotConfirmContent() throws {
        let directory = try temporaryDirectory()
        try Data("hidden extra".utf8).write(to: directory.appendingPathComponent(".hidden-extra"))
        let snapshot = try StagingVerifier.snapshot(directory: directory, observedAt: 100)
        XCTAssertEqual(snapshot.files.map(\.name), [".hidden-extra"])
        let emptyPolicy = StagingPolicy(
            expectedFileCount: 0,
            expectedTotalBytes: 0,
            expectedContentMultisetSHA256: StagingVerifier.contentMultisetDigest([])
        )
        XCTAssertEqual(StagingVerifier.verify(snapshot: snapshot, policy: emptyPolicy).outcome, .stagingExtraFiles)
    }

    func testSnapshotIncludesDirectoriesAndSymlinksAndRefusesConfirmation() throws {
        let directory = try temporaryDirectory()
        let nested = directory.appendingPathComponent("nested", isDirectory: true)
        try FileManager.default.createDirectory(at: nested, withIntermediateDirectories: false)
        try Data("target".utf8).write(to: nested.appendingPathComponent("target"))
        let link = directory.appendingPathComponent("linked-target")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: nested.appendingPathComponent("target"))

        let snapshot = try StagingVerifier.snapshot(directory: directory, observedAt: 100)
        XCTAssertEqual(snapshot.subdirectories, ["nested"])
        XCTAssertEqual(snapshot.symlinks, ["linked-target"])
        XCTAssertEqual(snapshot.files.count, 0)
        let emptyPolicy = StagingPolicy(
            expectedFileCount: 0,
            expectedTotalBytes: 0,
            expectedContentMultisetSHA256: StagingVerifier.contentMultisetDigest([])
        )
        XCTAssertEqual(StagingVerifier.verify(snapshot: snapshot, policy: emptyPolicy).outcome, .stagingExtraFiles)
    }

    private func temporaryDirectory() throws -> URL {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        addTeardownBlock { try? FileManager.default.removeItem(at: directory) }
        return directory
    }
    func testBaselineVerifierRecomputesReferenceAndNameInclusiveTripwire() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let baseline = root.appendingPathComponent("baseline")
        try FileManager.default.createDirectory(at: baseline, withIntermediateDirectories: true)
        try Data("alpha".utf8).write(to: baseline.appendingPathComponent("a.jpg"))
        try Data("beta".utf8).write(to: baseline.appendingPathComponent("b.jpg"))

        let hashes = [
            EvidenceIO.sha256Hex(Data("alpha".utf8)),
            EvidenceIO.sha256Hex(Data("beta".utf8)),
        ]
        let multiset = StagingVerifier.contentMultisetDigest(hashes)
        let lines = [
            "a.jpg\t5\t\(hashes[0])",
            "b.jpg\t4\t\(hashes[1])",
        ].sorted().joined(separator: "\n") + "\n"
        let tripwire = EvidenceIO.sha256Hex(Data(lines.utf8))
        let referenceURL = root.appendingPathComponent("reference.json")
        let reference = BaselineContentReference(
            source_dir: baseline.path,
            file_count: 2,
            total_bytes: 9,
            name_excluded_multiset_sha256_of_sorted_list: multiset,
            unique_content_hashes: 2,
            content_multiset: hashes.sorted()
        )
        let referenceData = try EvidenceIO.encodeJSON(reference)
        try referenceData.write(to: referenceURL)

        let result = try BaselineVerifier.verify(
            referenceFile: referenceURL,
            expectedReferenceFileSHA256: EvidenceIO.sha256Hex(referenceData),
            expectedContentMultisetSHA256: multiset,
            expectedTripwireSHA256: tripwire,
            expectedFileCount: 2,
            expectedTotalBytes: 9
        )
        XCTAssertEqual(result.fileCount, 2)
        XCTAssertEqual(result.totalBytes, 9)
        XCTAssertEqual(result.contentMultisetSHA256, multiset)
        XCTAssertEqual(result.nameInclusiveTripwireSHA256, tripwire)
    }

    func testBaselineVerifierRejectsSymlinkExtra() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let baseline = root.appendingPathComponent("baseline")
        try FileManager.default.createDirectory(at: baseline, withIntermediateDirectories: true)
        let file = baseline.appendingPathComponent("a.jpg")
        try Data("alpha".utf8).write(to: file)
        try FileManager.default.createSymbolicLink(
            at: baseline.appendingPathComponent("link.jpg"),
            withDestinationURL: file
        )
        let hash = EvidenceIO.sha256Hex(Data("alpha".utf8))
        let multiset = StagingVerifier.contentMultisetDigest([hash])
        let line = "a.jpg\t5\t\(hash)\n"
        let reference = BaselineContentReference(
            source_dir: baseline.path,
            file_count: 1,
            total_bytes: 5,
            name_excluded_multiset_sha256_of_sorted_list: multiset,
            unique_content_hashes: 1,
            content_multiset: [hash]
        )
        let data = try EvidenceIO.encodeJSON(reference)
        let referenceURL = root.appendingPathComponent("reference.json")
        try data.write(to: referenceURL)
        XCTAssertThrowsError(try BaselineVerifier.verify(
            referenceFile: referenceURL,
            expectedReferenceFileSHA256: EvidenceIO.sha256Hex(data),
            expectedContentMultisetSHA256: multiset,
            expectedTripwireSHA256: EvidenceIO.sha256Hex(Data(line.utf8)),
            expectedFileCount: 1,
            expectedTotalBytes: 5
        ))
    }


}
