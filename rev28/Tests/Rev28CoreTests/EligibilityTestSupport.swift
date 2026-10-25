import Foundation
@testable import Rev28Core

/// Test support: build a fully bound, all-PASS eligibility artifact whose
/// file-checkable evidence actually exists on disk, so the owner-boundary
/// recomputation runs exactly as production runs it.
enum EligibilityTestSupport {
    struct Armed {
        let artifact: PhaseBEligibilityArtifact
        let recomputation: PhaseBEligibilityRecomputation
    }

    /// Writes plan/handoff/frozen/predicate evidence bytes beneath the run's
    /// evidence directory and derives every hash from the exact bytes.
    static func armed(
        for authorization: ImmutableRunAuthorization,
        verdict: String = PhaseBEligibilityArtifact.eligibleVerdict,
        issuedAtISO8601: String = "2026-09-29T00:00:00.000Z"
    ) throws -> Armed {
        guard EvidenceIO.sha256Hex(Data("plan".utf8)) == authorization.planSHA256 else {
            throw NSError(domain: "EligibilityTestSupport", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "fixture authorization planSHA256 is not sha256(\"plan\"); the fixture must bind the real plan bytes"
            ])
        }
        let evidenceRoot = URL(fileURLWithPath: authorization.evidenceRunDirectory)
            .appendingPathComponent("eligibility-fixtures", isDirectory: true)
        try FileManager.default.createDirectory(at: evidenceRoot, withIntermediateDirectories: true)

        let planURL = evidenceRoot.appendingPathComponent("plan.md")
        try Data("plan".utf8).write(to: planURL)
        let handoffURL = evidenceRoot.appendingPathComponent("handoff.md")
        try Data("handoff".utf8).write(to: handoffURL)

        let frozenNames = [
            "capture-geometry-rulebook-v1.json",
            "chooser-affirmation-predicate-v2.json",
            "chooser-ax-calibration-v2.json",
            "tripwire-attribution-ladder-v1.json",
            "ci-w2-item5-freeze-provenance-v3.json",
        ]
        var frozenPaths: [String: String] = [:]
        var frozenHashes: [String: String] = [:]
        var canonicalFrozen: [String: CanonicalEvidenceBinding] = [:]
        for name in frozenNames {
            let url = evidenceRoot.appendingPathComponent(name)
            let bytes = Data("frozen:\(name)".utf8)
            try bytes.write(to: url)
            frozenPaths[name] = url.path
            frozenHashes[name] = EvidenceIO.sha256Hex(bytes)
            canonicalFrozen[name] = CanonicalEvidenceBinding(path: url.path, sha256: EvidenceIO.sha256Hex(bytes))
        }

        var canonicalPredicates: [String: CanonicalEvidenceBinding] = [:]
        let predicates = try PhaseBEligibilityArtifact.requiredPredicates.map { identifier -> PhaseBEligibilityPredicate in
            let url = evidenceRoot.appendingPathComponent("\(identifier).evidence.json")
            let bytes = Data("evidence:\(identifier)".utf8)
            try bytes.write(to: url)
            canonicalPredicates[identifier] = CanonicalEvidenceBinding(
                path: url.path,
                sha256: EvidenceIO.sha256Hex(bytes)
            )
            return PhaseBEligibilityPredicate(
                identifier: identifier,
                verdict: "PASS",
                evidencePath: url.path,
                evidenceSHA256: EvidenceIO.sha256Hex(bytes)
            )
        }

        let artifact = PhaseBEligibilityArtifact(
            verdict: verdict,
            runID: authorization.runID,
            planSHA256: authorization.planSHA256,
            reviewedImplementationSHA256: authorization.reviewedImplementationSHA256,
            reviewedBuild: PhaseBEligibilityReviewedBuild(
                headSHA: String(repeating: "a", count: 40),
                pathsDiffSHA256: EvidenceIO.sha256Hex(Data()),
                binarySHA256: EvidenceIO.sha256Hex(Data("binary".utf8))
            ),
            goalIdentitySHA256: PhaseBEligibilityArtifact.goalIdentityDigest(authorization),
            stagingRunDirectory: authorization.stagingRunDirectory,
            issuedAtISO8601: issuedAtISO8601,
            handoffPath: handoffURL.path,
            handoffSHA256: EvidenceIO.sha256Hex(Data("handoff".utf8)),
            frozenArtifactPaths: frozenPaths,
            frozenArtifactSHA256: frozenHashes,
            predicates: predicates
        )
        return Armed(
            artifact: artifact,
            recomputation: PhaseBEligibilityRecomputation(
                planURL: planURL,
                recomputedImplementationSHA256: authorization.reviewedImplementationSHA256,
                canonicalReviewedBuild: ReviewedBuildExpectations(
                    reviewedHeadSHA: String(repeating: "a", count: 40),
                    reviewedPathsDiffSHA256: EvidenceIO.sha256Hex(Data()),
                    reviewedBinarySHA256: EvidenceIO.sha256Hex(Data("binary".utf8))
                ),
                observedReviewedBuild: ReviewedBuildObservations(
                    headSHA: String(repeating: "a", count: 40),
                    reviewedPathsDiffSHA256: EvidenceIO.sha256Hex(Data()),
                    reviewedHeadIsAncestor: true,
                    binarySHA256: EvidenceIO.sha256Hex(Data("binary".utf8))
                ),
                canonicalHandoff: CanonicalEvidenceBinding(
                    path: handoffURL.path,
                    sha256: EvidenceIO.sha256Hex(Data("handoff".utf8))
                ),
                canonicalFrozenArtifacts: canonicalFrozen,
                canonicalPredicateEvidence: canonicalPredicates,
                allowedEvidenceRoots: [URL(fileURLWithPath: authorization.evidenceRunDirectory)]
            )
        )
    }

    static func artifact(
        for authorization: ImmutableRunAuthorization,
        verdict: String = PhaseBEligibilityArtifact.eligibleVerdict,
        issuedAtISO8601: String = "2026-09-29T00:00:00.000Z"
    ) throws -> PhaseBEligibilityArtifact {
        try armed(for: authorization, verdict: verdict, issuedAtISO8601: issuedAtISO8601).artifact
    }

    static func recordEligibility(on owner: PersistentTransactionOwner) throws {
        let armed = try armed(for: owner.authorization)
        try owner.recordPhaseBEligibility(armed.artifact, recomputation: armed.recomputation)
    }
}
