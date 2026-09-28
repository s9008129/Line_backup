import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

/// Composed production-path proof for `V09_CHOOSER_PREDICATE_V2_NOT_DERIVED`.
///
/// Production hash-binds the exact append-only frozen predicate + AX
/// calibration bytes in `LiveConfig` and derives the process-stable v2
/// predicate from them. This suite replays that derivation on the real frozen
/// pair, proves the raw frozen predicate alone stays refused by
/// `evaluateProduction`, and proves the derived predicate affirms a
/// calibration-shaped candidate (the earlier coverage only exercised
/// refusals).
final class ChooserPredicateProductionDerivationTests: XCTestCase {
    private static let frozenPredicateSHA256 =
        "0472aa0a364711fd357f872d93c5ad7e13b393cc267dbbc6244d47a20de6f3f2"
    private static let frozenCalibrationSHA256 =
        "13aa01a2fa5d2b2d3e52d28e17a1b421ac25e6943fda1c44a572be610ef7e569"

    private func frozenPair() throws -> (predicate: ChooserAffirmationPredicate, calibration: ChooserAXCalibrationEvidence) {
        var root = URL(fileURLWithPath: #filePath)
        for _ in 0..<4 { root.deleteLastPathComponent() }
        let frozenDirectory = root.appendingPathComponent("evidence/20260925-rev28-native-closed-loop/harness/frozen")
        let predicateBytes = try Data(contentsOf: frozenDirectory.appendingPathComponent("chooser-affirmation-predicate-v2.json"))
        let calibrationBytes = try Data(contentsOf: frozenDirectory.appendingPathComponent("chooser-ax-calibration-v2.json"))
        XCTAssertEqual(
            EvidenceIO.sha256Hex(predicateBytes), Self.frozenPredicateSHA256,
            "frozen chooser predicate drifted; production hash-binding would refuse"
        )
        XCTAssertEqual(
            EvidenceIO.sha256Hex(calibrationBytes), Self.frozenCalibrationSHA256,
            "frozen chooser AX calibration drifted; production hash-binding would refuse"
        )
        return (
            try JSONDecoder().decode(ChooserAffirmationPredicate.self, from: predicateBytes),
            try JSONDecoder().decode(ChooserAXCalibrationEvidence.self, from: calibrationBytes)
        )
    }

    private func node(_ role: String, subrole: String? = nil, title: String? = nil) -> AXNodeDump {
        AXNodeDump(
            depth: 1, role: role, subrole: subrole, title: title, description: nil,
            identifier: nil, keyEquivalent: nil, value: nil, enabled: true,
            frame: nil, attributes: [:]
        )
    }

    /// Candidate shaped exactly like the frozen calibration dump: AXWindow /
    /// AXStandardWindow with text-field, pop-up and both observed button
    /// titles, owned by the calibrated harness pid over a stable instance.
    private func calibrationShapedCandidate(defaultButtonTitle: String = "開啟") -> ChooserCandidate {
        let owner = ChooserProcessFacts(
            pid: 45_752, bundleID: "dev.rev28.harness", signingIdentity: "rev28harness-sign",
            startTimeUnix: 1_772_000_000
        )
        let nodes = [
            AXNodeDump(
                depth: 0, role: "AXWindow", subrole: "AXStandardWindow", title: "rev28 harness chooser",
                description: nil, identifier: nil, keyEquivalent: nil, value: nil, enabled: true,
                frame: CGRect(x: 133, y: 94, width: 880, height: 448), attributes: [:]
            ),
            node("AXTextField", subrole: "AXSearchField"),
            node("AXPopUpButton"),
            node("AXButton", title: "Cancel"),
            node("AXButton", title: defaultButtonTitle),
        ]
        return ChooserCandidate(
            windowID: 7_001,
            frame: CGRect(x: 133, y: 94, width: 880, height: 448),
            onScreen: true, presentInSCInventory: true, presentInCGInventory: true,
            isNewRelativeToPreDispatchInventory: true,
            owner: owner, pidReuseDetected: false,
            axNodes: nodes,
            preDispatchCensusPIDs: [owner.pid], postDispatchCensusPIDs: [owner.pid],
            preDispatchOwner: owner, postDispatchOwner: owner
        )
    }

    func testFrozenPairDerivesProcessStablePredicateAndAffirmsCalibrationShapedCandidate() throws {
        let (frozen, calibration) = try frozenPair()
        // The append-only frozen file predates the predicateVersion field and
        // button requirements; production must never run it directly.
        XCTAssertEqual(frozen.predicateVersion, 1)
        XCTAssertNil(frozen.ax.defaultButton)
        XCTAssertNil(frozen.ax.cancelButton)
        guard case .refused(.frozenPredicateMismatch, _) =
            ChooserAffirmationEvaluator.evaluateProduction(candidate: calibrationShapedCandidate(), predicate: frozen)
        else {
            return XCTFail("raw frozen v1-shaped predicate must be refused by evaluateProduction")
        }

        let derived = try ChooserProductionPredicate.derive(frozen: frozen, calibration: calibration)
        XCTAssertEqual(derived.predicateVersion, ChooserAffirmationEvaluator.processStableButtonSemanticsVersion)
        XCTAssertEqual(derived.ax.defaultButton?.titles, ["開啟"])
        XCTAssertEqual(derived.ax.cancelButton?.titles, ["Cancel"])

        XCTAssertEqual(
            ChooserAffirmationEvaluator.evaluateProduction(candidate: calibrationShapedCandidate(), predicate: derived),
            .affirmed
        )
    }

    func testDerivedPredicateStillRefusesCandidateWithoutObservedDefaultTitle() throws {
        let (frozen, calibration) = try frozenPair()
        let derived = try ChooserProductionPredicate.derive(frozen: frozen, calibration: calibration)
        guard case let .refused(.frozenPredicateMismatch, detail) = ChooserAffirmationEvaluator.evaluateProduction(
            candidate: calibrationShapedCandidate(defaultButtonTitle: "Open"), predicate: derived
        ) else {
            return XCTFail("a candidate missing the calibrated default title must be refused")
        }
        XCTAssertTrue(detail.contains("default button"), detail)
    }
}
