import Darwin
import Foundation
import XCTest
@testable import Rev28Core

final class PassiveNativeDiagnosticTests: XCTestCase {
    func testExplicitV3SyntheticPacketUsesActualStrictLoadAndRetainsOriginalRequest() async throws {
        typealias F = ExplicitLineTestFixture
        let (root, out, rule) = try fixture()
        try EvidenceIO.encodeJSON(F.rules).write(to: rule)
        let observed = try await F.bundle()
        let record = try PassiveNativeObservationRecord(bundle: observed, geometryState: F.state, ruleBook: F.rules)
        XCTAssertEqual(record.formatVersion, 3)
        XCTAssertEqual(record.explicitLineRequestBinding, F.binding)
        XCTAssertEqual(record.frame.configuration.sourceRect, F.bounds)
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await writer.collect(geometryState: F.state, provenance: provenance()) { observed }
        XCTAssertEqual(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256), observed)
        XCTAssertEqual(receipt.certifications, PassiveNativeDiagnostic.unknownCertifications)
        // Optional task-local artifact export for the separately rebuilt actual loader.
        if let destination = ProcessInfo.processInfo.environment["EXPLICIT_V3_SYNTHETIC_PACKET_ROOT"] {
            let retained = URL(fileURLWithPath: destination)
            try FileManager.default.copyItem(at: out, to: retained)
            try EvidenceIO.encodeJSON(receipt).write(to: retained.deletingLastPathComponent().appendingPathComponent("synthetic-v3-receipt.json"), options: .withoutOverwriting)
        }
    }

    func testExplicitV3ReanchoredTamperCannotBypassSharedBindingValidator() async throws {
        typealias F = ExplicitLineTestFixture
        let (root, out, rule) = try fixture()
        try EvidenceIO.encodeJSON(F.rules).write(to: rule)
        let observed = try await F.bundle()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await writer.collect(geometryState: F.state, provenance: provenance()) { observed }
        let recordURL = out.appendingPathComponent("observation.json")
        let manifestURL = out.appendingPathComponent("manifest.json")
        let original = try JSONSerialization.jsonObject(with: Data(contentsOf: recordURL)) as! [String: Any]
        let originalManifest = try JSONSerialization.jsonObject(with: Data(contentsOf: manifestURL)) as! [String: Any]
        let mutations: [(inout [String: Any]) -> Void] = [
            { $0["formatVersion"] = 2 }, { $0.removeValue(forKey: "explicitLineRequestBinding") },
            { var f = $0["frame"] as! [String: Any]; f.removeValue(forKey: "explicitLineSelectionWitness"); $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; var w = f["explicitLineSelectionWitness"] as! [String: Any]; w["selectedWindowIDs"] = [10, 99]; f["explicitLineSelectionWitness"] = w; $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; var w = f["explicitLineSelectionWitness"] as! [String: Any]; w["effectiveSourceRect"] = try! F.rectangle(F.main.frame); f["explicitLineSelectionWitness"] = w; $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; var c = f["configuration"] as! [String: Any]; c["includeChildWindows"] = true; f["configuration"] = c; $0["frame"] = f },
            { var b = $0["explicitLineRequestBinding"] as! [String: Any]; var c = b["configuration"] as! [String: Any]; c["sourceRect"] = try! F.rectangle(F.bounds); b["configuration"] = c; $0["explicitLineRequestBinding"] = b },
            { var b = $0["explicitLineRequestBinding"] as! [String: Any]; b["settledSelectedWindows"] = []; $0["explicitLineRequestBinding"] = b },
            { var b = $0["explicitLineRequestBinding"] as! [String: Any]; var r = b["ruleBook"] as! [String: Any]; r["ruleID"] = "legacy"; b["ruleBook"] = r; $0["explicitLineRequestBinding"] = b },
            { $0["epoch"] = 99 }, { var f = $0["frame"] as! [String: Any]; f["imageSHA256"] = String(repeating: "d", count: 64); $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; f["imageWidthPx"] = 511; $0["frame"] = f },
            { var p = $0["postProcess"] as! [String: Any]; p["pid"] = 999; $0["postProcess"] = p },
            { var w = $0["postInventory"] as! [[String: Any]]; w[1]["windowLayer"] = 9; $0["postInventory"] = w }
        ]
        for mutate in mutations {
            var changed = original; mutate(&changed)
            let bytes = try JSONSerialization.data(withJSONObject: changed)
            let record = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: bytes)
            XCTAssertThrowsError(try record.reconstruct(png: observed.framePNGData, ruleBook: F.rules))
            try bytes.write(to: recordURL)
            // First refuse the old external anchor, then refresh the synthetic
            // file digest AND anchor to reach the semantic validator itself.
            XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
            var manifest = originalManifest
            var files = manifest["files"] as! [[String: Any]]
            let index = files.firstIndex { $0["name"] as? String == "observation.json" }!
            files[index]["bytes"] = bytes.count; files[index]["sha256"] = EvidenceIO.sha256Hex(bytes)
            manifest["files"] = files
            let manifestBytes = try JSONSerialization.data(withJSONObject: manifest)
            try manifestBytes.write(to: manifestURL)
            XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: EvidenceIO.sha256Hex(manifestBytes)))
        }
        var manifest = originalManifest; manifest["formatVersion"] = 2
        let mixed = try JSONSerialization.data(withJSONObject: manifest); try mixed.write(to: manifestURL)
        try JSONSerialization.data(withJSONObject: original).write(to: recordURL)
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: EvidenceIO.sha256Hex(mixed)))
    }

    func testLegacyV1AndV2RejectForeignV3WitnessAndRequestBinding() async throws {
        typealias F = ExplicitLineTestFixture
        let witness = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(F.witness))
        let binding = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(F.binding))
        for (observed, state, rules) in [(try await bundle(), self.state, self.rules), (try await childBundle(), childState, childRules)] {
            let record = try PassiveNativeObservationRecord(bundle: observed, geometryState: state, ruleBook: rules)
            let original = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(record)) as! [String: Any]
            for addRequest in [false, true] {
                var object = original
                if addRequest { object["explicitLineRequestBinding"] = binding }
                else { var frame = object["frame"] as! [String: Any]; frame["explicitLineSelectionWitness"] = witness; object["frame"] = frame }
                let invalid = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: JSONSerialization.data(withJSONObject: object))
                XCTAssertThrowsError(try invalid.reconstruct(png: observed.framePNGData, ruleBook: rules))
            }
        }
    }
    private let state = CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true)
    private var rules: CaptureGeometryRuleBook {
        CaptureGeometryRuleBook(ruleID: "passive-test", frozenAtISO8601: "2026-10-05T00:00:00Z", rules: [
            CaptureGeometryRules.stateKey(state): CaptureGeometryRule(maxPerSideSizeDeltaPt: 0, originPaddingPt: 0, maxOriginPaddingPt: 0),
        ])
    }

    private func bundle() async throws -> ObservationBundle {
        let source = GeometryConsistentPassiveSource()
        let ocr = FakeOcr(items: [FakeLineScene().item("retained OCR", CGRect(x: 20, y: 20, width: 80, height: 20))])
        let session = NativeObservationSession(sessionID: "passive-unit-session", source: source, ocr: ocr)
        return try await session.capture(NativeObservationRequest(runID: "diagnostic-unit", state: .appReady,
            target: ObservationTarget(bundleID: PassiveNativeDiagnostic.lineBundleID, pid: 4242),
            configuration: .primaryWindow, geometryState: state, localization: .none, observationBudgetNanos: 5_000_000_000))
    }

    private func fixture() throws -> (URL, URL, URL) {
        // Foundation keeps /var despite resolvingSymlinksInPath on macOS;
        // use the actual /private/var location for no-follow path tests.
        let temporary = FileManager.default.temporaryDirectory.path
        let actualTemporary = temporary.hasPrefix("/var/") ? "/private" + temporary : temporary
        let root = URL(fileURLWithPath: actualTemporary).appendingPathComponent("passive-test-\(UUID().uuidString)")
        let output = root.appendingPathComponent("harness-development/native-diagnostics/new")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let rule = root.appendingPathComponent("rules.json")
        try EvidenceIO.encodeJSON(rules).write(to: rule)
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        return (root, output, rule)
    }

    private func provenance() -> PassiveDiagnosticProvenance {
        PassiveDiagnosticProvenance(implementationSHA256: String(repeating: "a", count: 64),
            sourceFiles: [PassiveDiagnosticFileDigest(name: "rev28/Package.swift", bytes: 1, sha256: String(repeating: "b", count: 64))],
            executableSHA256: String(repeating: "c", count: 64), executableBytes: 1)
    }

    private var childState: CaptureGeometryState {
        CaptureGeometryState(settled: true, activated: true, includeChildWindows: true, ignoreShadows: true)
    }
    private var childRules: CaptureGeometryRuleBook {
        CaptureGeometryRuleBook(ruleID: "passive-child-test", frozenAtISO8601: "2026-10-05T00:00:00Z", rules: [
            CaptureGeometryRules.stateKey(childState): CaptureGeometryRule(maxPerSideSizeDeltaPt: 0, originPaddingPt: 0, maxOriginPaddingPt: 0)])
    }
    private func childBundle(windowID: UInt32 = 11, offset: CGFloat = 0) async throws -> ObservationBundle {
        let main = NativeObservationTestWindows.lineWindow()
        let child = SCWindowSnapshot(windowID: windowID, frame: CGRect(x: 430 + offset, y: 80, width: 130, height: 160),
            windowLayer: 8, title: "synthetic child", isOnScreen: true, ownerPID: 4242,
            ownerBundleID: "jp.naver.line.mac", ownerName: "LINE")
        let fake = FakeObservationSource(window: main, bundleID: "jp.naver.line.mac", pid: 4242)
        fake.preInventoryOverride = [main, child]; fake.postInventoryOverride = [main, child]
        let bbox = main.frame.union(child.frame)
        fake.imageProvider = { FakeLineScene.plainImage(width: Int(bbox.width), height: Int(bbox.height)) }
        let source = GeometryConsistentPassiveSource(source: fake)
        let session = NativeObservationSession(sessionID: "child-unit-session", source: source, ocr: FakeOcr(items: []))
        return try await session.capture(NativeObservationRequest(runID: "child-unit", state: .appReady,
            target: ObservationTarget(bundleID: PassiveNativeDiagnostic.lineBundleID, pid: 4242),
            configuration: .childUnion, geometryState: childState, localization: .none, observationBudgetNanos: 5_000_000_000))
    }

    func testActualChildUnionBundleVersionTwoPacketRoundTrip() async throws {
        let (root, out, rule) = try fixture()
        try EvidenceIO.encodeJSON(childRules).write(to: rule)
        let observed = try await childBundle()
        let record = try PassiveNativeObservationRecord(bundle: observed, geometryState: childState, ruleBook: childRules)
        XCTAssertEqual(record.formatVersion, 2)
        XCTAssertEqual(record.certifications, PassiveNativeDiagnostic.unknownCertifications)
        XCTAssertEqual(record.frame.expectedBBoxPt, CGRect(x: 50, y: 60, width: 510, height: 600))
        let output = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await output.collect(geometryState: childState, provenance: provenance()) { observed }
        XCTAssertEqual(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256), observed)
        let manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: out.appendingPathComponent("manifest.json"))) as! [String: Any]
        XCTAssertEqual(manifest["formatVersion"] as? Int, 2)
    }

    func testChildProfileRequiresAffirmativeUniqueSnapshots() throws {
        let main = NativeObservationTestWindows.lineWindow()
        let target = ObservationTarget(bundleID: PassiveNativeDiagnostic.lineBundleID, pid: 4242)
        XCTAssertEqual(try PassiveDiagnosticCaptureProfile.primaryWindow.selectedWindows(in: [main], target: target), [main])
        XCTAssertThrowsError(try PassiveDiagnosticCaptureProfile.childUnion.selectedWindows(in: [main], target: target))
        let child = SCWindowSnapshot(windowID: 11, frame: CGRect(x: 430, y: 80, width: 130, height: 160),
            windowLayer: 8, title: "child", isOnScreen: true, ownerPID: 4242, ownerBundleID: target.bundleID, ownerName: "LINE")
        XCTAssertThrowsError(try PassiveDiagnosticCaptureProfile.childUnion.selectedWindows(in: [main, child, child], target: target))
        let invalid = SCWindowSnapshot(windowID: 11, frame: CGRect(x: 430, y: 80, width: CGFloat.infinity, height: 160),
            windowLayer: 8, title: "child", isOnScreen: true, ownerPID: 4242, ownerBundleID: target.bundleID, ownerName: "LINE")
        XCTAssertThrowsError(try PassiveDiagnosticCaptureProfile.childUnion.selectedWindows(in: [main, invalid], target: target))
        XCTAssertNil(PassiveDiagnosticCaptureProfile(rawValue: "displayRect"))
    }

    func testStableSamplesCannotAuthorizeChangedSessionChildren() async throws {
        let sampled = try await childBundle()
        let firstSample = try PassiveDiagnosticCaptureProfile.childUnion.selectedWindows(in: sampled.preInventory, target: sampled.target)
        let secondSample = try PassiveDiagnosticCaptureProfile.childUnion.selectedWindows(in: sampled.postInventory, target: sampled.target)
        XCTAssertEqual(firstSample, secondSample)
        XCTAssertNoThrow(try PassiveDiagnosticCaptureProfile.childUnion.validateSettlingBinding(bundle: sampled, sampledWindows: secondSample))
        for changed in [try await childBundle(windowID: 12), try await childBundle(offset: 2)] {
            // The new session is internally valid and stable; the sample-to-session
            // identity/geometry change still prohibits retaining a successful packet.
            XCTAssertNoThrow(try changed.validated())
            XCTAssertEqual(changed.preInventory, changed.postInventory)
            XCTAssertThrowsError(try PassiveDiagnosticCaptureProfile.childUnion.validateSettlingBinding(bundle: changed, sampledWindows: secondSample))
        }
    }

    func testVersionTwoRejectsIncompleteForeignDriftingOrMisversionedChildren() async throws {
        let observed = try await childBundle()
        let record = try PassiveNativeObservationRecord(bundle: observed, geometryState: childState, ruleBook: childRules)
        let original = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(record)) as! [String: Any]
        let mutations: [(inout [String: Any]) -> Void] = [
            { $0["formatVersion"] = 1 },
            { var f = $0["frame"] as! [String: Any]; var w = f["includedWindows"] as! [[String: Any]]; w.removeLast(); f["includedWindows"] = w; $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; var w = f["includedWindows"] as! [[String: Any]]; w.append(w[1]); f["includedWindows"] = w; $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; var w = f["includedWindows"] as! [[String: Any]]; w[1]["ownerPID"] = 999; f["includedWindows"] = w; $0["frame"] = f },
            { var w = $0["postInventory"] as! [[String: Any]]; w.removeLast(); $0["postInventory"] = w },
            { var w = $0["postInventory"] as! [[String: Any]]; w[1]["ownerBundleID"] = "com.other"; $0["postInventory"] = w },
            { var w = $0["postInventory"] as! [[String: Any]]; w[1]["windowID"] = 12; $0["postInventory"] = w },
            { var f = $0["frame"] as! [String: Any]; f["stateKey"] = "forged"; $0["frame"] = f },
            { var f = $0["frame"] as! [String: Any]; f["scale"] = 2; $0["frame"] = f },
            { $0["geometryState"] = ["settled": true, "activated": true, "includeChildWindows": false, "ignoreShadows": true] },
            { $0["certifications"] = ["phaseBPermit": "PASS"] },
        ]
        for mutate in mutations {
            var object = original; mutate(&object)
            let invalid = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: JSONSerialization.data(withJSONObject: object))
            XCTAssertThrowsError(try invalid.reconstruct(png: observed.framePNGData, ruleBook: childRules))
        }
        let primary = try await bundle()
        var versionTwoPrimary = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(PassiveNativeObservationRecord(bundle: primary, geometryState: state, ruleBook: rules))) as! [String: Any]
        versionTwoPrimary["formatVersion"] = 2
        let invalid = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: JSONSerialization.data(withJSONObject: versionTwoPrimary))
        XCTAssertThrowsError(try invalid.reconstruct(png: primary.framePNGData, ruleBook: rules))
    }

    func testExternallyReanchoredManifestVersionCannotDisagreeWithRecord() async throws {
        let (root, out, rule) = try fixture()
        try EvidenceIO.encodeJSON(childRules).write(to: rule)
        let observed = try await childBundle()
        let output = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        _ = try await output.collect(geometryState: childState, provenance: provenance()) { observed }
        let url = out.appendingPathComponent("manifest.json")
        var manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [String: Any]
        manifest["formatVersion"] = 1
        let bytes = try JSONSerialization.data(withJSONObject: manifest)
        try bytes.write(to: url)
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: EvidenceIO.sha256Hex(bytes)))
    }

    func testRetainedNativeBundleRoundTripWithExternalAnchor() async throws {
        let (root, out, rule) = try fixture()
        let observed = try await bundle()
        let output = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await output.collect(geometryState: state, provenance: provenance()) { observed }
        let loaded = try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256)
        XCTAssertEqual(loaded, observed)
        XCTAssertEqual(loaded.ocrItems.first?.text, "retained OCR")
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: out.path).sorted(), PassiveNativeDiagnostic.packetNames.sorted())
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: nil))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: String(repeating: "0", count: 64)))
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path))
    }

    func testOutputRefusalsOccurBeforeObserver() async throws {
        let (root, out, rule) = try fixture()
        var calls = 0
        let paths = [out.path + "/../new", root.appendingPathComponent("outside").path]
        for path in paths {
            do {
                let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: path, rulebook: rule.path)
                _ = try await writer.collect(geometryState: state, provenance: provenance()) { calls += 1; return try await self.bundle() }
                XCTFail("unsafe output accepted")
            } catch {}
        }
        let link = root.appendingPathComponent("harness-development/native-diagnostics/link")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: out)
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: link.path, rulebook: rule.path))
        let ruleLink = root.appendingPathComponent("rule-link")
        try FileManager.default.createSymbolicLink(at: ruleLink, withDestinationURL: rule)
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: ruleLink.path))
        let rootLink = root.deletingLastPathComponent().appendingPathComponent("passive-root-link-\(UUID().uuidString)")
        try FileManager.default.createSymbolicLink(at: rootLink, withDestinationURL: root)
        defer { try? FileManager.default.removeItem(at: rootLink) }
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: rootLink.path, output: out.path, rulebook: rule.path))
        try Data("existing".utf8).write(to: out.appendingPathComponent("existing"))
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path))
        XCTAssertEqual(calls, 0)
    }

    func testExclusiveClaimAndPartialFailureCannotBeReused() async throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path))
        enum Injected: Error { case failed }
        do { _ = try await writer.collect(geometryState: state, provenance: provenance()) { throw Injected.failed }; XCTFail() } catch {}
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: out.path), ["claim.json"])
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: String(repeating: "a", count: 64)))
        XCTAssertThrowsError(try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path))
    }

    func testSwappedOutputDirectoryRefusesBeforeObserver() async throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        try FileManager.default.moveItem(at: out, to: out.appendingPathExtension("moved"))
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: false)
        var called = false
        do { _ = try await writer.collect(geometryState: state, provenance: provenance()) { called = true; return try await self.bundle() }; XCTFail() } catch {}
        XCTAssertFalse(called)
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: out.path).isEmpty)
    }

    func testPublicationCollisionRetainsExistingBytesAndRefusesReadback() async throws {
        let (root, out, rule) = try fixture()
        let observed = try await bundle()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let collision = Data("do not overwrite".utf8)
        do {
            _ = try await writer.collect(geometryState: state, provenance: provenance()) {
                try collision.write(to: out.appendingPathComponent("observation.png"))
                return observed
            }
            XCTFail("publication overwrote another file")
        } catch {}
        XCTAssertEqual(try Data(contentsOf: out.appendingPathComponent("observation.png")), collision)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: out.path).sorted(), ["claim.json", "observation.png"])
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: String(repeating: "a", count: 64)))
    }

    func testPacketFileSymlinkCannotBeReadEvenWhenBytesMatch() async throws {
        let (root, out, rule) = try fixture()
        let observed = try await bundle()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await writer.collect(geometryState: state, provenance: provenance()) { observed }
        let original = out.appendingPathComponent("observation.png")
        let target = root.appendingPathComponent("same-image.png")
        try FileManager.default.moveItem(at: original, to: target)
        try FileManager.default.createSymbolicLink(at: original, withDestinationURL: target)
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
    }

    func testPacketTamperRefusalsAndIndependentBundleChecks() async throws {
        let (root, out, rule) = try fixture()
        let observed = try await bundle()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let receipt = try await writer.collect(geometryState: state, provenance: provenance()) { observed }
        let recordURL = out.appendingPathComponent("observation.json")
        let original = try Data(contentsOf: recordURL)
        let originalObject = try JSONSerialization.jsonObject(with: original) as! [String: Any]
        let mutations: [(inout [String: Any]) -> Void] = [
            { $0["deadlineMonotonicNanos"] = 1 },
            { $0["epoch"] = 99 },
            { var process = $0["postProcess"] as! [String: Any]; process["pid"] = 99; $0["postProcess"] = process },
            { var frame = $0["frame"] as! [String: Any]; frame["scale"] = 2; $0["frame"] = frame },
            { var frame = $0["frame"] as! [String: Any]; frame["backingScaleFactor"] = 2; $0["frame"] = frame },
            { var frame = $0["frame"] as! [String: Any]; frame["stateKey"] = "forged-rule"; $0["frame"] = frame },
            { var frame = $0["frame"] as! [String: Any]; frame["includedWindows"] = []; $0["frame"] = frame },
            { var frame = $0["frame"] as! [String: Any]; var config = frame["configuration"] as! [String: Any]; config["includeChildWindows"] = true; frame["configuration"] = config; $0["frame"] = frame },
            { $0["postInventory"] = [] },
            { $0["status"] = "PASS" },
            { $0["certifications"] = ["phaseBPermit": "PASS"] },
            { $0["ocrSourceImageSHA256"] = String(repeating: "d", count: 64) },
        ]
        for mutate in mutations {
            var object = originalObject; mutate(&object)
            let changed = try JSONSerialization.data(withJSONObject: object)
            let record = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: changed)
            XCTAssertThrowsError(try record.reconstruct(png: observed.framePNGData, ruleBook: rules))
            try changed.write(to: recordURL)
            XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
        }
        var ocr = originalObject
        var items = ocr["ocrItems"] as! [[String: Any]]; items[0]["text"] = "forged OCR"; ocr["ocrItems"] = items
        try JSONSerialization.data(withJSONObject: ocr).write(to: recordURL)
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
        items[0]["confidence"] = 0.01; ocr["ocrItems"] = items
        try JSONSerialization.data(withJSONObject: ocr).write(to: recordURL)
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
        try original.write(to: recordURL)
        try Data("wrong PNG".utf8).write(to: out.appendingPathComponent("observation.png"))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.load(directory: out.path, expectedManifestSHA256: receipt.manifestSHA256))
        let record = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: original)
        XCTAssertThrowsError(try record.reconstruct(png: Data("wrong PNG".utf8), ruleBook: rules))
    }

    func testLineOnlyFreshPIDBinding() throws {
        XCTAssertNoThrow(try PassiveNativeDiagnostic.validateTarget(bundleID: "jp.naver.line.mac", pid: 4242, observedBundleID: "jp.naver.line.mac", observedPID: 4242))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.validateTarget(bundleID: "com.other.app", pid: 4242, observedBundleID: "com.other.app", observedPID: 4242))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.validateTarget(bundleID: "jp.naver.line.mac", pid: 4242, observedBundleID: "com.other.app", observedPID: 4242))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.validateTarget(bundleID: "jp.naver.line.mac", pid: 4242, observedBundleID: "jp.naver.line.mac", observedPID: 4243))
        XCTAssertThrowsError(try PassiveNativeDiagnostic.validateTarget(bundleID: "jp.naver.line.mac", pid: 0, observedBundleID: nil, observedPID: nil))
    }

    func testConstructorGapDeletionDoesNotRecreateOutput() throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        XCTAssertThrowsError(try writer.makeObservationSource(target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            signingIdentity: { _ in nil }, beforeConstruction: { try FileManager.default.removeItem(at: out) }))
        XCTAssertFalse(FileManager.default.fileExists(atPath: out.path), "constructor recreated output after identity check")
    }

    func testConstructorGapSymlinkDoesNotCreateMissingTarget() throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let target = root.appendingPathComponent("redirect/missing/leaf")
        XCTAssertThrowsError(try writer.makeObservationSource(target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            signingIdentity: { _ in nil }, beforeConstruction: {
                try FileManager.default.removeItem(at: out)
                try FileManager.default.createSymbolicLink(at: out, withDestinationURL: target)
            }))
        XCTAssertFalse(FileManager.default.fileExists(atPath: root.appendingPathComponent("redirect").path))
        XCTAssertTrue(try out.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink == true)
    }

    func testConstructorGapAncestorSwapCannotRedirectCreation() throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let parent = out.deletingLastPathComponent()
        let moved = parent.appendingPathExtension("moved")
        let redirect = root.appendingPathComponent("redirect")
        try FileManager.default.createDirectory(at: redirect, withIntermediateDirectories: false)
        XCTAssertThrowsError(try writer.makeObservationSource(target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            signingIdentity: { _ in nil }, beforeConstruction: {
                try FileManager.default.moveItem(at: parent, to: moved)
                try FileManager.default.createSymbolicLink(at: parent, withDestinationURL: redirect)
            }))
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: redirect.path).isEmpty)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: moved.appendingPathComponent("new").path), ["claim.json"])
    }

    func testDescriptorAuthorityOwnsDescriptorAndDerivesPersistentFloor() throws {
        let (_, out, _) = try fixture()
        try Data().write(to: out.appendingPathComponent("state-APP_READY-41.json"))
        let fd = open(out.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        XCTAssertGreaterThanOrEqual(fd, 0)
        let authority = try RunEpochAuthority(existingDirectoryDescriptor: fd)
        close(fd)
        XCTAssertEqual(authority.floor, 41)
        XCTAssertEqual(authority.nextEpoch(), 42)
        try Data().write(to: out.appendingPathComponent("state-APP_READY-43.json"))
        XCTAssertEqual(authority.nextEpoch(), 0)
        XCTAssertNotNil(authority.refusal)
    }

    func testDescriptorAuthorityRejectsClosedRegularAndUnlinkedDirectories() throws {
        let (_, out, rule) = try fixture()
        XCTAssertThrowsError(try RunEpochAuthority(existingDirectoryDescriptor: -1))
        let regular = open(rule.path, O_RDONLY | O_CLOEXEC)
        defer { close(regular) }
        XCTAssertThrowsError(try RunEpochAuthority(existingDirectoryDescriptor: regular))
        let fd = open(out.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        defer { close(fd) }
        try FileManager.default.removeItem(at: out)
        XCTAssertThrowsError(try RunEpochAuthority(existingDirectoryDescriptor: fd))
        XCTAssertFalse(FileManager.default.fileExists(atPath: out.path))
    }

    func testDiagnosticSourceConstructorIsSingleUseAndReadsPinnedFloor() throws {
        let (root, out, rule) = try fixture()
        let writer = try PassiveDiagnosticOutput(projectRoot: root.path, output: out.path, rulebook: rule.path)
        let target = ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242)
        let source = try writer.makeObservationSource(target: target, signingIdentity: { _ in nil })
        XCTAssertEqual(source.nextEpoch(), 1)
        XCTAssertThrowsError(try writer.makeObservationSource(target: target, signingIdentity: { _ in nil }))
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: out.path), ["claim.json"])
    }
}

private struct GeometryConsistentPassiveSource: ObservationSource {
    let source: FakeObservationSource
    init(source: FakeObservationSource = FakeObservationSource(window: NativeObservationTestWindows.lineWindow(), bundleID: "jp.naver.line.mac", pid: 4242)) {
        self.source = source
    }
    func enumerateWindows() async throws -> [SCWindowSnapshot] { try await source.enumerateWindows() }
    func cgInventory() -> [CGWindowSnapshot] { source.cgInventory() }
    func captureTarget(window: SCWindowSnapshot, includedWindows: [SCWindowSnapshot], configuration: CaptureConfiguration, geometryState: CaptureGeometryState, epoch: UInt64) async throws -> ObservationCapturedImage {
        let result = try await source.captureTarget(window: window, includedWindows: includedWindows, configuration: configuration, geometryState: geometryState, epoch: epoch)
        let f = result.record
        let bbox = FrameCaptureSupport.unionBBox(of: includedWindows, fallback: window.frame)
        return ObservationCapturedImage(image: result.image, record: CapturedFrameRecord(captureKind: f.captureKind, configuration: f.configuration,
            includedWindows: f.includedWindows, expectedBBoxPt: bbox, imageWidthPx: f.imageWidthPx, imageHeightPx: f.imageHeightPx,
            actualBBoxPt: bbox, perSideSizeDeltaPt: f.perSideSizeDeltaPt, scale: f.scale, scaleSource: f.scaleSource,
            backingScaleFactor: 1, epoch: f.epoch, capturedAtISO8601: f.capturedAtISO8601, imageSHA256: f.imageSHA256,
            stateKey: CaptureGeometryRules.stateKey(geometryState), validity: f.validity, violations: f.violations, identity: f.identity))
    }
    func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead { try source.readAXIdentity(pid: pid, windowID: windowID) }
    func processInstance(pid: Int32) throws -> ProcessInstanceID { try source.processInstance(pid: pid) }
    func signingIdentity(pid: Int32) throws -> String? { try source.signingIdentity(pid: pid) }
    func nextEpoch() -> UInt64 { source.nextEpoch() }
    func monotonicNanos() -> UInt64 { source.monotonicNanos() }
}
