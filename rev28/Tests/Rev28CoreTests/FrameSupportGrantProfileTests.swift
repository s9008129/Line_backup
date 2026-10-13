import XCTest
@testable import Rev28Core

final class FrameSupportGrantProfileTests: XCTestCase {
    func testLegacyIdentityPreservesSafeTaskLocalGrantPathBehavior() {
        let profile = FrameSupportGrantProfile.legacy
        XCTAssertTrue(profile.acceptsGrantPath("harness-development/another-approved-task/custom-grant.json"))
        XCTAssertFalse(profile.acceptsGrantPath("/tmp/grant.json"))
    }

    func testMinimalLive08GrantPathIsExactAndIdentityOnly() {
        let profile = FrameSupportGrantProfile.minimalLive08
        XCTAssertTrue(profile.isMinimalLive08)
        XCTAssertTrue(profile.acceptsGrantPath("\(profile.artifactDirectory)/live-grant-1.json"))
        XCTAssertFalse(profile.acceptsGrantPath("\(profile.artifactDirectory)/custom-grant.json"))
    }

    func testLegacyProfileRetainsItsExactGrantAndFourModuleAllowlist() {
        let profile = FrameSupportGrantProfile.legacy
        XCTAssertEqual(FrameSupportGrantProfile.select(taskID: profile.taskID,
            contractPath: profile.contractPath, contractSHA256: profile.contractSHA256,
            artifactDirectory: profile.artifactDirectory), profile)
        XCTAssertEqual(profile.taskModules.count, 4)
        XCTAssertTrue(profile.acceptsGrantPath("harness-development/another-approved-task/custom-grant.json"))
    }

    func testMinimalLive08ProfileBindsOriginalTaskContractAndTenModules() {
        let profile = FrameSupportGrantProfile.minimalLive08
        XCTAssertEqual(profile.taskID, "TASK-4acb4326ea2a4c50ace6f333f2de8751")
        XCTAssertEqual(profile.contractSHA256, "a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc")
        XCTAssertEqual(FrameSupportGrantProfile.select(taskID: profile.taskID,
            contractPath: profile.contractPath, contractSHA256: profile.contractSHA256,
            artifactDirectory: profile.artifactDirectory), profile)
        XCTAssertEqual(profile.taskModules.count, 10)
        XCTAssertTrue(profile.acceptsGrantPath("\(profile.artifactDirectory)/live-grant-1.json"))
        XCTAssertTrue(profile.acceptsGrantPath("\(profile.artifactDirectory)/live-grant-2.json"))
    }

    func testCrossMixedOrUnlistedTaskContractArtifactTuplesFailClosed() {
        let legacy = FrameSupportGrantProfile.legacy
        let minimal = FrameSupportGrantProfile.minimalLive08
        XCTAssertNil(FrameSupportGrantProfile.select(taskID: minimal.taskID,
            contractPath: legacy.contractPath, contractSHA256: minimal.contractSHA256,
            artifactDirectory: minimal.artifactDirectory))
        XCTAssertNil(FrameSupportGrantProfile.select(taskID: minimal.taskID,
            contractPath: minimal.contractPath, contractSHA256: legacy.contractSHA256,
            artifactDirectory: minimal.artifactDirectory))
        XCTAssertNil(FrameSupportGrantProfile.select(taskID: legacy.taskID,
            contractPath: legacy.contractPath, contractSHA256: legacy.contractSHA256,
            artifactDirectory: minimal.artifactDirectory))
        XCTAssertNil(FrameSupportGrantProfile.select(taskID: "TASK-UNLISTED",
            contractPath: minimal.contractPath, contractSHA256: minimal.contractSHA256,
            artifactDirectory: minimal.artifactDirectory))
    }
}
