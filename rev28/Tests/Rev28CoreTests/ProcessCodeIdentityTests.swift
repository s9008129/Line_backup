import Foundation
import Security
import XCTest
@testable import Rev28Core

final class ProcessCodeIdentityTests: XCTestCase {
    func testUnavailableTargetRemainsUnknown() {
        for pid in [Int32(-1), 0, Int32.max] {
            XCTAssertNil(ProcessCodeIdentity.read(pid: pid), "no caller signature can authorize an unavailable target")
        }
    }

    func testObservedIdentifierAndTeamArePreserved() {
        let identifier = kSecCodeInfoIdentifier as String
        let team = kSecCodeInfoTeamIdentifier as String
        XCTAssertEqual(ProcessCodeIdentity.identity(in: [identifier: "jp.naver.line.mac", team: "TEAM123"]), "jp.naver.line.mac@TEAM123")
        XCTAssertEqual(ProcessCodeIdentity.identity(in: [identifier: "ad.hoc.target"]), "ad.hoc.target")
    }

    func testMissingOrMalformedTargetIdentityIsUnknown() {
        let identifier = kSecCodeInfoIdentifier as String
        let team = kSecCodeInfoTeamIdentifier as String
        let information: [[String: Any]] = [
            [:], [identifier: ""], [identifier: "   "], [identifier: 42],
            [identifier: "target", team: ""], [identifier: "target", team: 42],
        ]
        for info in information { XCTAssertNil(ProcessCodeIdentity.identity(in: info)) }
    }
}
