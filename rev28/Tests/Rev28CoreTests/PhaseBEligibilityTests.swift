import Foundation
import XCTest
@testable import Rev28Core

/// The Phase B eligibility artifact is the only thing that can arm the one-shot
/// Save All entitlement. These tests pin the fail-closed semantics: absence,
/// a non-PASS predicate, a stale binding or a consumed entitlement all refuse.
final class PhaseBEligibilityTests: XCTestCase {
    private func makeAuthorization(runID: String = "run-eligible") throws -> ImmutableRunAuthorization {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let stagingRoot = root.appendingPathComponent("staging", isDirectory: true)
        let run = stagingRoot.appendingPathComponent(runID, isDirectory: true)
        try FileManager.default.createDirectory(at: run, withIntermediateDirectories: true)
        return ImmutableRunAuthorization(
            runID: runID,
            goal: "Rev28 target album backup",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: EvidenceIO.sha256Hex(Data("plan".utf8)),
            reviewedImplementationSHA256: EvidenceIO.sha256Hex(Data("implementation".utf8)),
            stagingRoot: stagingRoot,
            stagingRunDirectory: run
        )
    }

    /// A structurally well-formed predicate whose declared evidence hash is a
    /// plausible 64-hex value (structural tests never read the file).
    private func predicate(_ identifier: String, verdict: String = "PASS") -> PhaseBEligibilityPredicate {
        PhaseBEligibilityPredicate(
            identifier: identifier,
            verdict: verdict,
            evidencePath: "/nonexistent/evidence/\(identifier).json",
            evidenceSHA256: EvidenceIO.sha256Hex(Data("evidence:\(identifier)".utf8))
        )
    }

    private func artifact(
        for authorization: ImmutableRunAuthorization,
        verdict: String = PhaseBEligibilityArtifact.eligibleVerdict,
        runID: String? = nil,
        planSHA256: String? = nil,
        reviewedImplementationSHA256: String? = nil,
        goalIdentitySHA256: String? = nil,
        stagingRunDirectory: String? = nil,
        predicates: [PhaseBEligibilityPredicate]? = nil
    ) -> PhaseBEligibilityArtifact {
        PhaseBEligibilityArtifact(
            verdict: verdict,
            runID: runID ?? authorization.runID,
            planSHA256: planSHA256 ?? authorization.planSHA256,
            reviewedImplementationSHA256: reviewedImplementationSHA256 ?? authorization.reviewedImplementationSHA256,
            goalIdentitySHA256: goalIdentitySHA256 ?? PhaseBEligibilityArtifact.goalIdentityDigest(authorization),
            stagingRunDirectory: stagingRunDirectory ?? authorization.stagingRunDirectory,
            issuedAtISO8601: "2026-09-29T00:00:00.000Z",
            handoffPath: "/nonexistent/handoff.md",
            handoffSHA256: EvidenceIO.sha256Hex(Data("handoff".utf8)),
            frozenArtifactPaths: ["capture-geometry-rulebook-v1.json": "/nonexistent/rulebook.json"],
            frozenArtifactSHA256: ["capture-geometry-rulebook-v1.json": EvidenceIO.sha256Hex(Data("rulebook".utf8))],
            predicates: predicates ?? PhaseBEligibilityArtifact.requiredPredicates.map { predicate($0) }
        )
    }

    func testFullyBoundAllPassArtifactValidates() throws {
        let authorization = try makeAuthorization()
        try artifact(for: authorization).validate(against: authorization, entitlementConsumed: false)
    }

    func testIneligibleVerdictRefusesEvenWithAllPredicatesPassing() throws {
        let authorization = try makeAuthorization()
        let ineligible = artifact(for: authorization, verdict: "PHASE_B_INELIGIBLE")
        XCTAssertThrowsError(try ineligible.validate(against: authorization, entitlementConsumed: false)) { error in
            XCTAssertEqual(error as? PhaseBEligibilityError, .notEligible("PHASE_B_INELIGIBLE"))
        }
    }

    func testMissingPredicateRefuses() throws {
        let authorization = try makeAuthorization()
        let missing = PhaseBEligibilityArtifact.requiredPredicates.dropLast()
        let partial = artifact(
            for: authorization,
            predicates: missing.map { predicate($0) }
        )
        XCTAssertThrowsError(try partial.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case let .missingPredicate(identifier) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(identifier, PhaseBEligibilityArtifact.requiredPredicates.last)
        }
    }

    func testNonPassPredicateRefuses() throws {
        let authorization = try makeAuthorization()
        var predicates = PhaseBEligibilityArtifact.requiredPredicates.map { predicate($0) }
        predicates[3] = predicate(predicates[3].identifier, verdict: "FAIL")
        let failed = artifact(for: authorization, predicates: predicates)
        XCTAssertThrowsError(try failed.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case let .predicateNotPass(identifier, verdict) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(identifier, PhaseBEligibilityArtifact.requiredPredicates[3])
            XCTAssertEqual(verdict, "FAIL")
        }
    }

    func testRunBindingMismatchRefuses() throws {
        let authorization = try makeAuthorization()
        let stale = artifact(for: authorization, runID: "other-run")
        XCTAssertThrowsError(try stale.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case .bindingMismatch = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
        }
        let otherPlan = artifact(for: authorization, planSHA256: EvidenceIO.sha256Hex(Data("other-plan".utf8)))
        XCTAssertThrowsError(try otherPlan.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case .bindingMismatch = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
        }
    }

    func testGoalIdentityMismatchRefuses() throws {
        let authorization = try makeAuthorization()
        let otherGoal = artifact(for: authorization, goalIdentitySHA256: String(repeating: "a", count: 64))
        XCTAssertThrowsError(try otherGoal.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case .bindingMismatch = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
        }
    }

    func testConsumedEntitlementRefuses() throws {
        let authorization = try makeAuthorization()
        XCTAssertThrowsError(
            try artifact(for: authorization).validate(against: authorization, entitlementConsumed: true)
        ) { error in
            XCTAssertEqual(error as? PhaseBEligibilityError, .entitlementConsumed)
        }
    }

    func testArtifactOutsideTheRunDirectoryNeverLoads() throws {
        let authorization = try makeAuthorization()
        let elsewhere = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: elsewhere, withIntermediateDirectories: true)
        let url = elsewhere.appendingPathComponent("eligibility.json")
        let data = try JSONEncoder().encode(artifact(for: authorization))
        try data.write(to: url)
        XCTAssertThrowsError(
            try PhaseBEligibilityArtifact.load(
                fileURL: url,
                withinRunDirectory: URL(fileURLWithPath: authorization.evidenceRunDirectory)
            )
        ) { error in
            XCTAssertEqual(error as? PhaseBEligibilityError, .artifactOutsideRunDirectory)
        }
    }

    // MARK: - Recomputed evidence (owner boundary)

    func testArtifactWithRealBoundBytesPassesRecomputation() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        try armed.artifact.validateWithRecomputedEvidence(
            against: authorization,
            entitlementConsumed: false,
            recomputation: armed.recomputation
        )
    }

    func testTamperedPredicateEvidenceRefuses() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        let target = armed.artifact.predicates[0]
        try Data("tampered".utf8).write(to: URL(fileURLWithPath: target.evidencePath))
        XCTAssertThrowsError(
            try armed.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: armed.recomputation
            )
        ) { error in
            guard case let .evidenceDigestMismatch(detail) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertTrue(detail.contains(target.identifier), detail)
        }
    }

    func testMissingPredicateEvidenceRefuses() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        let target = armed.artifact.predicates[0]
        try FileManager.default.removeItem(atPath: target.evidencePath)
        XCTAssertThrowsError(
            try armed.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: armed.recomputation
            )
        ) { error in
            guard case .evidenceUnavailable = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
        }
    }

    func testImplementationDigestMismatchRefuses() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        let lying = PhaseBEligibilityRecomputation(
            planURL: armed.recomputation.planURL,
            recomputedImplementationSHA256: EvidenceIO.sha256Hex(Data("other-implementation".utf8))
        )
        XCTAssertThrowsError(
            try armed.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: lying
            )
        ) { error in
            guard case let .evidenceDigestMismatch(detail) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertTrue(detail.contains("implementation"), detail)
        }
    }

    func testPlanBytesMismatchRefuses() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        let otherPlan = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try Data("other-plan".utf8).write(to: otherPlan)
        let recomputation = PhaseBEligibilityRecomputation(
            planURL: otherPlan,
            recomputedImplementationSHA256: armed.recomputation.recomputedImplementationSHA256
        )
        XCTAssertThrowsError(
            try armed.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: recomputation
            )
        ) { error in
            guard case let .evidenceDigestMismatch(detail) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertTrue(detail.contains("plan"), detail)
        }
    }

    func testTamperedHandoffAndFrozenArtifactRefuse() throws {
        let authorization = try makeAuthorization()
        let armed = try EligibilityTestSupport.armed(for: authorization)
        try Data("tampered-handoff".utf8).write(to: URL(fileURLWithPath: armed.artifact.handoffPath))
        XCTAssertThrowsError(
            try armed.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: armed.recomputation
            )
        ) { error in
            guard case let .evidenceDigestMismatch(detail) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertTrue(detail.contains("handoff"), detail)
        }

        let second = try EligibilityTestSupport.armed(for: authorization)
        let frozenName = second.artifact.frozenArtifactSHA256.keys.sorted()[0]
        try Data("tampered-frozen".utf8).write(to: URL(fileURLWithPath: second.artifact.frozenArtifactPaths[frozenName]!))
        XCTAssertThrowsError(
            try second.artifact.validateWithRecomputedEvidence(
                against: authorization,
                entitlementConsumed: false,
                recomputation: second.recomputation
            )
        ) { error in
            guard case let .evidenceDigestMismatch(detail) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertTrue(detail.contains(frozenName), detail)
        }
    }

    func testLabelOnlyPredicateWithoutEvidenceBoundBytesRefuses() throws {
        let authorization = try makeAuthorization()
        var predicates = PhaseBEligibilityArtifact.requiredPredicates.map { predicate($0) }
        predicates[2] = PhaseBEligibilityPredicate(
            identifier: predicates[2].identifier,
            verdict: "PASS",
            evidencePath: "",
            evidenceSHA256: ""
        )
        let labelOnly = artifact(for: authorization, predicates: predicates)
        XCTAssertThrowsError(try labelOnly.validate(against: authorization, entitlementConsumed: false)) { error in
            guard case let .predicateEvidenceUnbound(identifier) = error as? PhaseBEligibilityError else {
                return XCTFail("unexpected error \(error)")
            }
            XCTAssertEqual(identifier, PhaseBEligibilityArtifact.requiredPredicates[2])
        }
    }
}
