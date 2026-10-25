import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

/// Synthetic retained facts only. No native enumeration, filter or screenshot.
enum ExplicitLineTestFixture {
    static let target = ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242)
    static let state = CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true)
    static let main = NativeObservationTestWindows.lineWindow()
    static let child = SCWindowSnapshot(windowID: 11, frame: CGRect(x: 430, y: 80, width: 130, height: 160),
        windowLayer: 8, title: "synthetic candidate", isOnScreen: true, ownerPID: 4242, ownerBundleID: target.bundleID, ownerName: "LINE")
    static var windows: [SCWindowSnapshot] { [main, child] }
    static let bounds = CGRect(x: 50, y: 60, width: 510, height: 600)
    static let display = ExplicitLineDisplaySnapshot(displayID: 1, frame: CGRect(x: 0, y: 0, width: 1200, height: 900), widthPt: 1200, heightPt: 900)
    static var rules: CaptureGeometryRuleBook {
        CaptureGeometryRuleBook(ruleID: "explicitLineWindows-v3-synthetic", frozenAtISO8601: "2026-10-06T00:00:00Z",
            rules: [CaptureGeometryRules.stateKey(state): CaptureGeometryRule(maxPerSideSizeDeltaPt: 1, originPaddingPt: 0, maxOriginPaddingPt: 1)])
    }
    static var binding: ExplicitLineRequestBinding {
        ExplicitLineRequestBinding(configuration: .explicitLineWindows, geometryState: state, settledSelectedWindows: windows, ruleBook: rules)
    }
    static var witness: ExplicitLineSelectionWitness {
        ExplicitLineSelectionWitness(selectedWindowIDs: [10, 11], display: display, effectiveSourceRect: bounds,
            filterContentRect: display.frame, pointPixelScale: 1)
    }
    static var image: CGImage { FakeLineScene.plainImage(width: 510, height: 600) }
    static func frame(epoch: UInt64 = 1, scale: Double = 1, backing: Double = 1) -> CapturedFrameRecord {
        var effective = CaptureConfiguration.explicitLineWindows; effective.sourceRect = bounds
        return CapturedFrameRecord(captureKind: .explicitLineWindows, configuration: effective, includedWindows: windows,
            expectedBBoxPt: bounds, imageWidthPx: 510, imageHeightPx: 600, actualBBoxPt: bounds,
            perSideSizeDeltaPt: .zero, scale: scale, scaleSource: .pointPixelScale, backingScaleFactor: backing,
            epoch: epoch, capturedAtISO8601: "2026-10-06T00:00:00Z", imageSHA256: FrameCaptureSupport.pngSHA256(of: image)!,
            stateKey: CaptureGeometryRules.stateKey(state), validity: .valid, violations: [], identity: nil,
            explicitLineSelectionWitness: witness)
    }
    static func mutateFrame(_ frame: CapturedFrameRecord, _ mutate: (inout [String: Any]) -> Void) throws -> CapturedFrameRecord {
        var object = try JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(frame)) as! [String: Any]
        mutate(&object)
        return try JSONDecoder().decode(CapturedFrameRecord.self, from: JSONSerialization.data(withJSONObject: object))
    }
    static func rectangle(_ rect: CGRect) throws -> Any { try JSONSerialization.jsonObject(with: JSONEncoder().encode(rect)) }
    static func changedChild(id: UInt32 = 11, frame: CGRect = child.frame, layer: Int = 8, onScreen: Bool = true,
                             pid: Int32 = 4242, bundle: String = target.bundleID) -> SCWindowSnapshot {
        SCWindowSnapshot(windowID: id, frame: frame, windowLayer: layer, title: child.title, isOnScreen: onScreen,
            ownerPID: pid, ownerBundleID: bundle, ownerName: child.ownerName)
    }
}

final class ExplicitLineCaptureSelectionTests: XCTestCase {
    private typealias F = ExplicitLineTestFixture
    private func validate(_ frame: CapturedFrameRecord, binding: ExplicitLineRequestBinding? = F.binding,
                          pre: [SCWindowSnapshot] = F.windows, post: [SCWindowSnapshot] = F.windows) throws {
        try ExplicitLineCaptureSelection.validate(binding: binding, target: F.target, mainID: 10,
            preInventory: pre, postInventory: post, frame: frame)
    }
    func testLogicalSelectionIncludesExactCandidatesDespiteSDKFalse() throws {
        XCTAssertFalse(F.binding.configuration.includeChildWindows)
        XCTAssertEqual(try ExplicitLineCaptureSelection.selectedWindows(in: F.windows.reversed(), target: F.target), F.windows)
        XCTAssertEqual(try ExplicitLineCaptureSelection.union(of: F.windows), F.bounds)
        XCTAssertNoThrow(try validate(F.frame()))
    }
    func testSelectionRefusesMissingDuplicateForeignAndInvalidCandidates() throws {
        let invalid = [
            [F.main], [F.main, F.main, F.child], [F.main, F.child, F.child],
            [F.main, F.changedChild(pid: 999)], [F.main, F.changedChild(bundle: "com.other")],
            [F.main, F.changedChild(onScreen: false)], [F.main, F.changedChild(layer: 0)],
            [F.main, F.changedChild(frame: CGRect(x: 430, y: 80, width: 0, height: 160))],
            [F.main, F.changedChild(frame: CGRect(x: 430, y: 80, width: CGFloat.infinity, height: 160))],
            [F.main, F.child, F.changedChild(bundle: "com.other")]
        ]
        for inventory in invalid { XCTAssertThrowsError(try ExplicitLineCaptureSelection.selectedWindows(in: inventory, target: F.target)) }
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.selectedWindows(in: F.windows, target: ObservationTarget(bundleID: "com.other", pid: 4242)))
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.union(of: []))
    }
    func testFreshHandlesMustMatchEveryRequestedFactAndSet() throws {
        XCTAssertNoThrow(try ExplicitLineCaptureSelection.validateFreshSelection(requested: F.windows, inventory: F.windows, target: F.target, main: F.main))
        for child in [F.changedChild(id: 12), F.changedChild(layer: 9), F.changedChild(pid: 999), F.changedChild(onScreen: false),
                      F.changedChild(bundle: "com.other"), F.changedChild(frame: F.child.frame.offsetBy(dx: 1, dy: 0))] {
            XCTAssertThrowsError(try ExplicitLineCaptureSelection.validateFreshSelection(requested: F.windows,
                inventory: [F.main, child], target: F.target, main: F.main))
        }
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.validateFreshSelection(requested: [F.main], inventory: F.windows, target: F.target, main: F.main))
    }
    func testDisplayUnionRefusesOutsideCrossingMirroredNonzeroAndMalformedDisplays() throws {
        XCTAssertEqual(try ExplicitLineCaptureSelection.containingDisplay(for: F.bounds, displays: [F.display]), F.display)
        var mirror = F.display; mirror.displayID = 2
        var shifted = F.display; shifted.frame.origin.x = 1
        var negative = F.display; negative.frame.origin.x = -1
        var pointMismatch = F.display; pointMismatch.widthPt = 1201
        var invalid = F.display; invalid.frame.size.width = .infinity
        var small = F.display; small.frame.size.width = 450; small.widthPt = 450
        let second = ExplicitLineDisplaySnapshot(displayID: 2, frame: CGRect(x: 450, y: 0, width: 750, height: 900), widthPt: 750, heightPt: 900)
        for displays in [[], [F.display, mirror], [F.display, F.display], [shifted], [negative], [pointMismatch], [invalid], [small], [small, second]] {
            XCTAssertThrowsError(try ExplicitLineCaptureSelection.containingDisplay(for: F.bounds, displays: displays))
        }
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.containingDisplay(for: .zero, displays: [F.display]))
    }
    func testWitnessEffectiveFlagsCropIDsScaleAndBoundsCannotSelfCertify() throws {
        let changes: [(inout ExplicitLineSelectionWitness) -> Void] = [
            { $0.filterKind = "fullDisplay" }, { $0.selectedWindowIDs = [10] }, { $0.selectedWindowIDs = [10, 99] },
            { $0.selectedWindowIDs = [10, 11, 11] }, { $0.selectedWindowIDs = [11, 10] },
            { $0.effectiveSourceRect = F.main.frame }, { $0.filterContentRect = F.main.frame },
            { $0.pointPixelScale = 2 }, { $0.pointPixelScale = 0 }, { $0.pointPixelScale = .nan },
            { $0.includeChildWindows = true }, { $0.includeMenuBar = true }, { $0.display.frame.origin.x = -1 }
        ]
        for change in changes {
            var frame = F.frame(); var witness = F.witness; change(&witness); frame.explicitLineSelectionWitness = witness
            XCTAssertThrowsError(try validate(frame))
        }
        var noWitness = F.frame(); noWitness.explicitLineSelectionWitness = nil
        XCTAssertThrowsError(try validate(noWitness))
        XCTAssertThrowsError(try validate(F.frame(), binding: nil))
        for (scale, backing) in [(1.0, 2.0), (Double.infinity, 1.0), (1.0, 0.0), (1.0, Double.nan)] {
            XCTAssertThrowsError(try validate(F.frame(scale: scale, backing: backing)))
        }
        let mutations: [(inout [String: Any]) -> Void] = [
            { $0["captureKind"] = "window" }, { $0["stateKey"] = "forged" }, { $0["imageWidthPx"] = 600 },
            { $0["expectedBBoxPt"] = try! F.rectangle(F.main.frame) }, { $0["actualBBoxPt"] = try! F.rectangle(F.main.frame) },
            { var c = $0["configuration"] as! [String: Any]; c.removeValue(forKey: "sourceRect"); $0["configuration"] = c },
            { var c = $0["configuration"] as! [String: Any]; c["ignoreClipping"] = true; $0["configuration"] = c },
            { var c = $0["configuration"] as! [String: Any]; c["showsCursor"] = true; $0["configuration"] = c }
        ]
        for change in mutations { XCTAssertThrowsError(try validate(F.mutateFrame(F.frame(), change))) }
    }
    func testOriginalRequestTemporalSetAndFrozenRuleMustRecompute() throws {
        var cropRequest = F.binding; cropRequest.configuration.sourceRect = F.bounds
        var wrongState = F.binding; wrongState.geometryState.activated = false
        var wrongSet = F.binding; wrongSet.settledSelectedWindows = [F.main, F.changedChild(id: 12)]
        var missingSet = F.binding; missingSet.settledSelectedWindows = [F.main]
        for binding in [cropRequest, wrongState, wrongSet, missingSet] { XCTAssertThrowsError(try validate(F.frame(), binding: binding)) }
        for changed in [F.changedChild(id: 12), F.changedChild(layer: 9), F.changedChild(frame: F.child.frame.offsetBy(dx: 1, dy: 0))] {
            XCTAssertThrowsError(try validate(F.frame(), post: [F.main, changed]))
        }
        let key = CaptureGeometryRules.stateKey(F.state)
        for tolerance in [1.1, -1, Double.infinity] {
            let bad = CaptureGeometryRuleBook(ruleID: "explicitLineWindows-v3-synthetic", frozenAtISO8601: "now",
                rules: [key: CaptureGeometryRule(maxPerSideSizeDeltaPt: tolerance, originPaddingPt: 0, maxOriginPaddingPt: 1)])
            XCTAssertThrowsError(try ExplicitLineCaptureSelection.validateRuleBook(bad, state: F.state))
        }
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.validateRuleBook(CaptureGeometryRuleBook(ruleID: "legacy", frozenAtISO8601: "now", rules: F.rules.rules), state: F.state))
        var unsettled = F.state; unsettled.settled = false
        let falseStateBook = CaptureGeometryRuleBook(ruleID: "explicitLineWindows-v3-unsettled", frozenAtISO8601: "now",
            rules: [CaptureGeometryRules.stateKey(unsettled): CaptureGeometryRule(maxPerSideSizeDeltaPt: 1, originPaddingPt: 0, maxOriginPaddingPt: 1)])
        XCTAssertThrowsError(try ExplicitLineCaptureSelection.validateRuleBook(falseStateBook, state: unsettled), "a frozen false-state rule must not bypass mandatory A/A settling")
    }
}
