import Foundation
import XCTest
@testable import Rev28Core

final class OneShotAuthorizationTests: XCTestCase {
    private func temporaryDirectory() throws -> URL {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    func testInspectNeverCreatesOrConsumesTheAuthorization() throws {
        let dir = try temporaryDirectory()
        let authorization = dir.appendingPathComponent("one-shot-authorization.json")
        try Data("{}".utf8).write(to: authorization)

        XCTAssertEqual(OneShotAuthorizationGate.inspect(authorizationURL: authorization), .available)
        XCTAssertTrue(
            FileManager.default.fileExists(atPath: authorization.path),
            "inspection must not rename, move or remove the authorization"
        )
        XCTAssertFalse(
            FileManager.default.fileExists(
                atPath: OneShotAuthorizationGate.markerURL(for: authorization).path
            ),
            "inspection must not fabricate the consumed marker"
        )
    }

    func testConsumedMarkerKeepsPreflightObserveOnly() throws {
        let dir = try temporaryDirectory()
        let authorization = dir.appendingPathComponent("one-shot-authorization.json")
        try Data("{}".utf8).write(to: authorization)
        try Data("{}".utf8).write(to: OneShotAuthorizationGate.markerURL(for: authorization))

        XCTAssertEqual(OneShotAuthorizationGate.inspect(authorizationURL: authorization), .alreadyConsumed)
        XCTAssertTrue(FileManager.default.fileExists(atPath: authorization.path))
    }
}
