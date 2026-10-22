import XCTest
@testable import Rev28Core

final class PassiveContextObservationTests: XCTestCase {
    func testSchemaPreservesMissingNullErrorsTruncationAndProcessInstance() throws {
        let snapshot = PassiveContextObservation(
            schemaVersion: 1,
            observedAtUnixMilliseconds: 1_800_000_000_000,
            target: .init(bundleID: "jp.naver.line.mac", appVersion: "9.0.1", pid: 123, startTimeSeconds: 77, startTimeMicroseconds: 8),
            frontmostPID: 123,
            focusedWindowID: 8,
            windows: [.init(nodeID: "ax-0", windowNumber: 8, cgWindowNumber: 8, cgOwnerPID: 123, cgLayer: 0,
                            cgFramePt: .init(x: 10, y: 20, width: 300, height: 400), title: nil,
                            role: "AXWindow", subrole: nil,
                            framePt: .init(x: 10, y: 20, width: 300, height: 400), isMain: true,
                            isFocused: true, isOnScreen: true, displayIDs: [1])],
            onScreenWindows: [.init(ownerPID: 123, windowNumber: 8, layer: 0,
                                    boundsPt: .init(x: 10, y: 20, width: 300, height: 400),
                                    alpha: 1, isOnScreen: true, orderFrontToBack: 0)],
            onScreenInventoryAvailable: true,
            displays: [.init(displayID: 1, boundsPt: .init(x: 0, y: 0, width: 1_440, height: 900), backingScale: 2)],
            nodes: [.init(id: "ax-0", parentID: nil, role: "AXWindow", subrole: nil,
                          title: nil, description: nil, value: nil, minimumValue: nil, maximumValue: nil,
                          help: nil, identifier: nil,
                          framePt: nil, enabled: nil, focused: nil, selected: nil, offscreen: nil, windowNumber: 8,
                          children: [], missingAttributes: ["AXTitle"], nullAttributes: ["AXValue"], unsupportedAttributes: ["AXHelp"],
                          attributeErrors: [.init(attribute: "AXChildren", errorCode: -25204)])],
            complete: false,
            truncated: true,
            truncationReasons: ["nodeLimit"],
            limits: .init(maxDepth: 12, maxNodes: 2_000, maxStringBytes: 4_096),
            errors: ["AX tree incomplete"],
            visual: nil
        )

        let encoded = try JSONEncoder().encode(snapshot)
        let decoded = try JSONDecoder().decode(PassiveContextObservation.self, from: encoded)
        XCTAssertEqual(decoded, snapshot)
        XCTAssertEqual(decoded.target.startTimeSeconds, 77)
        XCTAssertEqual(decoded.nodes[0].missingAttributes, ["AXTitle"])
        XCTAssertEqual(decoded.nodes[0].nullAttributes, ["AXValue"])
        XCTAssertEqual(decoded.nodes[0].unsupportedAttributes, ["AXHelp"])
        XCTAssertEqual(decoded.nodes[0].attributeErrors.first?.errorCode, -25204)
        XCTAssertFalse(decoded.complete)
        XCTAssertTrue(decoded.truncated)
        XCTAssertEqual(decoded.onScreenWindows.first?.orderFrontToBack, 0)
    }
}
