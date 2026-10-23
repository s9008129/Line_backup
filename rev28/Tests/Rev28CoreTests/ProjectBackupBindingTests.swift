import XCTest
import CryptoKit
@testable import Rev28Core

final class ProjectBackupBindingTests: XCTestCase {
    private struct Fixture {
        let request: ProjectBackupInspectionRequest
        let config: Data
        let state: Data
        var report: Data
        let material: [ProjectBackupProducerSourceMaterial]
    }
    private func hash(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
    private func load(_ name: String = "eligible") throws -> Fixture {
        let root = try XCTUnwrap(ProcessInfo.processInfo.environment["LINE_BACKUP_INSPECTION_FIXTURES"])
        let dir = URL(fileURLWithPath: root).appendingPathComponent(name)
        let report = try Data(contentsOf: dir.appendingPathComponent("stdout.json"))
        let object = try XCTUnwrap(JSONSerialization.jsonObject(with: report) as? [String: Any])
        let request = try XCTUnwrap(object["request"] as? [String: Any])
        let source = try XCTUnwrap((object["producer"] as? [String: Any])?["source_files"] as? [[String: Any]])
        let projectRoot = try XCTUnwrap(request["project_root"] as? String)
        let material = try source.map { e -> ProjectBackupProducerSourceMaterial in
            let path = try XCTUnwrap(e["path"] as? String)
            return .init(relativePath: path, rawBytes: try Data(contentsOf: URL(fileURLWithPath: projectRoot).appendingPathComponent(path)))
        }
        return Fixture(request: .init(projectRoot: projectRoot, startDate: request["start_date"] as! String,
                                      endDate: request["end_date"] as! String, expectedImages: request["expected_images"] as! Int),
                       config: try Data(contentsOf: dir.appendingPathComponent("config.json")),
                       state: try Data(contentsOf: dir.appendingPathComponent("state.json")), report: report, material: material)
    }
    private func bind(_ f: Fixture, request: ProjectBackupInspectionRequest? = nil, config: Data? = nil,
                      state: Data? = nil, material: [ProjectBackupProducerSourceMaterial]? = nil,
                      anchor: String? = nil) throws -> ProjectBackupInspectionBinding {
        try ProjectBackupBinding.inspect(originalRequest: request ?? f.request, rawConfig: config ?? f.config,
                                         rawState: state ?? f.state, producerStdout: f.report,
                                         externalStdoutSHA256: anchor ?? hash(f.report), producerSourceMaterial: material ?? f.material)
    }
    private func mutate(_ f: inout Fixture, _ body: (inout [String: Any]) -> Void) throws {
        var o = try XCTUnwrap(JSONSerialization.jsonObject(with: f.report) as? [String: Any]); body(&o)
        f.report = try JSONSerialization.data(withJSONObject: o, options: .sortedKeys)
    }
    func testActualProducerEligibleNeverDispatches() throws {
        let b = try bind(load()); XCTAssertFalse(b.canDispatch); XCTAssertEqual(b.decision, .eligible)
    }
    func testActualProducerVerifiedNeverDispatches() throws {
        let b = try bind(load("verified")); XCTAssertFalse(b.canDispatch); XCTAssertEqual(b.decision, .skipVerified)
    }
    func testBusyUnresolvedAmbiguousAndDestinationReports() throws {
        for (name, decision) in [("busy", ProjectBackupInspectionDecision.busy), ("unresolved", .unresolved),
                                  ("ambiguous", .ambiguous), ("destination", .destinationBlocked)] {
            let b = try bind(load(name)); XCTAssertEqual(b.decision, decision); XCTAssertFalse(b.canDispatch)
        }
    }
    func testOriginalRequestForeignRootRejected() throws {
        let f = try load(); let r = ProjectBackupInspectionRequest(projectRoot: "/foreign", startDate: f.request.startDate, endDate: f.request.endDate, expectedImages: f.request.expectedImages)
        XCTAssertThrowsError(try bind(f, request: r))
    }
    func testExternalAnchorMismatchRejected() throws { XCTAssertThrowsError(try bind(load(), anchor: String(repeating: "a", count: 64))) }
    func testReanchoredForgedFlagsRejected() throws {
        for key in ["dispatch_authorized", "writer_acquired", "native_observation_performed", "state_modified"] {
            var f = try load(); try mutate(&f) { $0[key] = true }; XCTAssertThrowsError(try bind(f))
            try mutate(&f) { $0[key] = 0 }; XCTAssertThrowsError(try bind(f))
        }
    }
    func testReanchoredTargetAndAuthorityForgeryRejected() throws {
        for (container, key, value) in [("target", "proposed_destination", "/foreign" as Any), ("target", "group_key", "foreign"),
                                         ("authority", "state_revision", 999), ("authority", "state_revision", true),
                                         ("authority", "group_name", "foreign")] {
            var f = try load(); try mutate(&f) { o in var nested = o[container] as! [String: Any]; nested[key] = value; o[container] = nested }
            XCTAssertThrowsError(try bind(f))
        }
    }
    func testDigestForgeryRejected() throws {
        var f = try load(); try mutate(&f) { o in
            var a = o["authority"] as! [String: Any]; var s = a["state"] as! [String: Any]
            s["sha256"] = String(repeating: "a", count: 64); a["state"] = s; o["authority"] = a
        }; XCTAssertThrowsError(try bind(f))
    }
    func testStaleRawConfigAndStateRejected() throws {
        let f = try load(); XCTAssertThrowsError(try bind(f, config: f.config + Data(" ".utf8)))
        XCTAssertThrowsError(try bind(f, state: f.state + Data(" ".utf8)))
    }
    func testReanchoredDecisionAndFactsContradictionsRejected() throws {
        for name in ["eligible", "verified", "busy", "unresolved", "ambiguous", "destination"] {
            var f = try load(name); try mutate(&f) { $0["decision"] = "PROJECT_BUSY" == $0["decision"] as? String ? "SKIP_VERIFIED" : "PROJECT_BUSY" }
            XCTAssertThrowsError(try bind(f))
        }
        var f = try load(); try mutate(&f) { o in var s = o["state_facts"] as! [String: Any]; s["current_run_terminal"] = false; o["state_facts"] = s }
        XCTAssertThrowsError(try bind(f))
    }
    func testUnknownKeysVersionsAndRefusalRejected() throws {
        for (key, value) in [("unknown", true as Any), ("report_format_version", 2), ("kind", "REFUSAL")] {
            var f = try load(); try mutate(&f) { $0[key] = value }; XCTAssertThrowsError(try bind(f))
        }
    }
    func testUnknownContentCannotBecomeZero() throws {
        for key in ["expected_total_bytes", "expected_content_multiset_sha256"] {
            var f = try load(); try mutate(&f) { $0[key] = 0 }; XCTAssertThrowsError(try bind(f))
        }
    }
    func testSourceTamperAndMissingMaterialRejected() throws {
        let f = try load(); var material = f.material
        material[0] = .init(relativePath: material[0].relativePath, rawBytes: Data("changed".utf8))
        XCTAssertThrowsError(try bind(f, material: material)); XCTAssertThrowsError(try bind(f, material: Array(f.material.dropFirst())))
        XCTAssertThrowsError(try bind(f, material: f.material.reversed()))
    }
    func testReanchoredReducedSourceSetRejected() throws {
        var f = try load(); try mutate(&f) { o in var p = o["producer"] as! [String: Any]; p["source_files"] = Array((p["source_files"] as! [Any]).dropFirst()); o["producer"] = p }
        XCTAssertThrowsError(try bind(f, material: Array(f.material.dropFirst())))
    }
    func testDuplicateEscapedKeysAndInvalidUTF8Rejected() throws {
        var f = try load(); f.report = Data("{\"kind\":\"REPORT\",\"k\\u0069nd\":\"REPORT\"}".utf8)
        XCTAssertThrowsError(try bind(f)); f.report = Data([0xff]); XCTAssertThrowsError(try bind(f))
        let clean = try load(); XCTAssertThrowsError(try bind(clean, state: Data("{\"revision\":1,\"revision\":2}".utf8)))
    }
    func testReanchoredRawStateHistoryContradictionRejected() throws {
        var f = try load(); var s = try XCTUnwrap(JSONSerialization.jsonObject(with: f.state) as? [String: Any]); s["current_run_id"] = "dangling"
        let raw = try JSONSerialization.data(withJSONObject: s)
        try mutate(&f) { o in var a = o["authority"] as! [String: Any]; a["state"] = ["path": "state/backup_state.json", "bytes": raw.count, "sha256": hash(raw)]; o["authority"] = a }
        XCTAssertThrowsError(try bind(f, state: raw))
    }
}
