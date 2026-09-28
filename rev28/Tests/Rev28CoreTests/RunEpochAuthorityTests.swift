import Foundation
import XCTest
@testable import Rev28Core

final class RunEpochAuthorityTests: XCTestCase {
    private func makeDirectory() throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("rev28-epoch-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    private func write(_ name: String, in directory: URL) throws {
        try Data("{}".utf8).write(to: directory.appendingPathComponent(name))
    }

    func testFreshDirectoryIssuesFromOne() throws {
        let directory = try makeDirectory()
        let authority = try RunEpochAuthority(evidenceRunDirectory: directory)
        XCTAssertEqual(authority.floor, 0)
        XCTAssertEqual(authority.nextEpoch(), 1)
        XCTAssertEqual(authority.nextEpoch(), 2)
        XCTAssertNil(authority.refusal)
    }

    func testMissingDirectoryIsCreatedAndStartsFromOne() throws {
        let missing = FileManager.default.temporaryDirectory
            .appendingPathComponent("rev28-epoch-\(UUID().uuidString)", isDirectory: true)
        let authority = try RunEpochAuthority(evidenceRunDirectory: missing)
        XCTAssertEqual(authority.nextEpoch(), 1)
        var isDirectory: ObjCBool = false
        XCTAssertTrue(FileManager.default.fileExists(atPath: missing.path, isDirectory: &isDirectory))
        XCTAssertTrue(isDirectory.boolValue)
    }

    func testNewProcessContinuesAfterExistingEvidenceEpochs() throws {
        let directory = try makeDirectory()
        try write("state-APP_READY-1.json", in: directory)
        try write("state-SAVE_ALL_LOCATED-7.json", in: directory)
        try write("ledger.jsonl", in: directory)
        try write("state-APP_READY-notanumber.json", in: directory)
        let authority = try RunEpochAuthority(evidenceRunDirectory: directory)
        XCTAssertEqual(authority.floor, 7)
        XCTAssertEqual(authority.nextEpoch(), 8)
        XCTAssertEqual(authority.nextEpoch(), 9)
    }

    func testOutOfBandEvidenceStopsIssuingInsteadOfReusingAnEpoch() throws {
        let directory = try makeDirectory()
        let authority = try RunEpochAuthority(evidenceRunDirectory: directory)
        try write("state-GROUP_READY-1.json", in: directory)
        XCTAssertEqual(authority.nextEpoch(), 0, "an epoch already named by evidence must never be reused")
        XCTAssertNotNil(authority.refusal)
        XCTAssertEqual(authority.nextEpoch(), 0)
    }
}
