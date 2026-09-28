import Foundation

// MARK: - Phase B eligibility (R4 C4/C5)
//
// The one-shot Save All entitlement may only be armed by an explicit,
// machine-checkable eligibility artifact whose every required predicate is
// PASS, whose bindings match the exact run authorization, and whose
// file-checkable evidence is recomputed at the owner boundary — the reviewed
// Plan bytes, the Stage 03 handoff bytes, the frozen rule/predicate/fixture
// hashes, the reviewed implementation source digest and every predicate's
// evidence bytes. A producer label with no recomputable evidence never arms
// the entitlement. Absence of the artifact (this AB round) is refusal, never
// an implicit arm.

public enum PhaseBEligibilityError: Error, Equatable, CustomStringConvertible {
    case missingArtifact
    case notEligible(String)
    case bindingMismatch(String)
    case missingPredicate(String)
    case predicateNotPass(String, verdict: String)
    case entitlementConsumed
    case artifactOutsideRunDirectory
    case malformedBindingHash(String)
    case predicateEvidenceUnbound(String)
    case predicateSetMismatch(String)
    case evidenceUnavailable(String)
    case evidenceDigestMismatch(String)
    case canonicalEvidenceMismatch(String)
    case evidenceOutsideAllowedRoots(String)

    public var description: String {
        switch self {
        case .missingArtifact:
            return "phaseBEligibilityMissing"
        case let .notEligible(verdict):
            return "phaseBNotEligible(\(verdict))"
        case let .bindingMismatch(detail):
            return "phaseBBindingMismatch(\(detail))"
        case let .missingPredicate(identifier):
            return "phaseBPredicateMissing(\(identifier))"
        case let .predicateNotPass(identifier, verdict):
            return "phaseBPredicateNotPass(\(identifier)=\(verdict))"
        case .entitlementConsumed:
            return "phaseBEntitlementAlreadyConsumed"
        case .artifactOutsideRunDirectory:
            return "phaseBArtifactOutsideRunDirectory"
        case let .malformedBindingHash(detail):
            return "phaseBBindingNotAHash(\(detail))"
        case let .predicateEvidenceUnbound(identifier):
            return "phaseBPredicateEvidenceUnbound(\(identifier))"
        case let .predicateSetMismatch(detail):
            return "phaseBPredicateSetMismatch(\(detail))"
        case let .evidenceUnavailable(path):
            return "phaseBEvidenceUnavailable(\(path))"
        case let .evidenceDigestMismatch(detail):
            return "phaseBEvidenceDigestMismatch(\(detail))"
        case let .canonicalEvidenceMismatch(detail):
            return "phaseBCanonicalEvidenceMismatch(\(detail))"
        case let .evidenceOutsideAllowedRoots(path):
            return "phaseBEvidenceOutsideAllowedRoots(\(path))"
        }
    }
}

public struct PhaseBEligibilityPredicate: Codable, Equatable, Sendable {
    public let identifier: String
    public let verdict: String
    /// Absolute path of the exact evidence bytes the Stage 03 producer
    /// evaluated for this predicate (raw test logs, review reports, provenance
    /// outputs, refusal transcripts, ...). Validation re-reads and re-hashes
    /// them; a verdict label without bound bytes is refused.
    public let evidencePath: String
    /// SHA-256 of exactly those bytes.
    public let evidenceSHA256: String

    public init(identifier: String, verdict: String, evidencePath: String, evidenceSHA256: String) {
        self.identifier = identifier
        self.verdict = verdict
        self.evidencePath = evidencePath
        self.evidenceSHA256 = evidenceSHA256
    }
}

/// One canonical reviewed evidence binding (exact path + SHA-256) supplied by
/// the operator-reviewed configuration, never by the eligibility artifact.
public struct CanonicalEvidenceBinding: Equatable, Sendable {
    public let path: String
    public let sha256: String

    public init(path: String, sha256: String) {
        self.path = path
        self.sha256 = sha256
    }
}

/// The reviewed HEAD/diff/binary triple the artifact must declare. The
/// artifact's declaration is compared against the reviewed configuration and
/// against live recomputed observations, so a self-declared value never arms
/// the entitlement.
public struct PhaseBEligibilityReviewedBuild: Codable, Equatable, Sendable {
    public let headSHA: String
    public let pathsDiffSHA256: String
    public let binarySHA256: String

    public init(headSHA: String, pathsDiffSHA256: String, binarySHA256: String) {
        self.headSHA = headSHA
        self.pathsDiffSHA256 = pathsDiffSHA256
        self.binarySHA256 = binarySHA256
    }
}

/// The recomputation inputs that live outside the artifact itself: the
/// reviewed Plan bytes (anchored by the one-shot authorization's planSHA256),
/// the reviewed implementation source digest (recomputed from the repository
/// root with the same digest code the authorization binds) and the canonical
/// reviewed bindings for the Stage 03 handoff, the frozen rule/predicate/
/// fixture/provenance artifacts and every required predicate's evidence.
/// The canonical values come from the reviewed configuration; the artifact's
/// own declarations are compared against them and never trusted by label.
public struct PhaseBEligibilityRecomputation: Equatable, Sendable {
    public let planURL: URL
    public let recomputedImplementationSHA256: String
    /// Canonical reviewed HEAD/diff/binary values from the reviewed
    /// configuration and the live recomputed observations of the same facts.
    public let canonicalReviewedBuild: ReviewedBuildExpectations
    public let observedReviewedBuild: ReviewedBuildObservations
    public let canonicalHandoff: CanonicalEvidenceBinding
    public let canonicalFrozenArtifacts: [String: CanonicalEvidenceBinding]
    public let canonicalPredicateEvidence: [String: CanonicalEvidenceBinding]
    /// Every declared evidence path must resolve beneath one of these roots.
    public let allowedEvidenceRoots: [URL]

    public init(
        planURL: URL,
        recomputedImplementationSHA256: String,
        canonicalReviewedBuild: ReviewedBuildExpectations,
        observedReviewedBuild: ReviewedBuildObservations,
        canonicalHandoff: CanonicalEvidenceBinding,
        canonicalFrozenArtifacts: [String: CanonicalEvidenceBinding],
        canonicalPredicateEvidence: [String: CanonicalEvidenceBinding],
        allowedEvidenceRoots: [URL]
    ) {
        self.planURL = planURL
        self.recomputedImplementationSHA256 = recomputedImplementationSHA256
        self.canonicalReviewedBuild = canonicalReviewedBuild
        self.observedReviewedBuild = observedReviewedBuild
        self.canonicalHandoff = canonicalHandoff
        self.canonicalFrozenArtifacts = canonicalFrozenArtifacts
        self.canonicalPredicateEvidence = canonicalPredicateEvidence
        self.allowedEvidenceRoots = allowedEvidenceRoots
    }
}

public struct PhaseBEligibilityArtifact: Codable, Equatable, Sendable {
    public static let eligibleVerdict = "PHASE_B_ELIGIBLE"

    /// Every predicate the Plan's PHASE_B_ELIGIBILITY section requires. An
    /// artifact missing one of these, or carrying a non-PASS verdict, never
    /// arms the entitlement.
    public static let requiredPredicates: [String] = [
        "PLAN_AND_HANDOFF_BOUND",
        "IMPLEMENTATION_SOURCE_BINARY_BOUND",
        "RULES_FIXTURES_PROVENANCE_CURRENT",
        "REVIEWS_CURRENT_ISSUE_FREE",
        "V01_CAPABILITY",
        "V02_CALIBRATION",
        "V08_REPLAY_ADVERSARIAL",
        "V09_TOPIC_REVIEWS",
        "V12_TESTS",
        "V13_SAME_COMPOSITION",
        "V14_PHASE_A",
        "V15_AUTHORITY",
        "BASELINE_UNCHANGED",
        "STAGING_EMPTY_AND_CANONICAL",
        "TRIPWIRE_ARMED",
        "REFUSAL_BRANCHES_DEMONSTRATED",
        "EXPLICIT_ONE_SHOT_PHASE_B_AUTHORIZATION",
        // plan.md:257 — "reversible/revalidation budgets not exhausted". The
        // producer must bind evidence for the durable budget state; the owner
        // enforces the same condition at `reserveSaveAll`.
        "REVERSIBLE_AND_REVALIDATION_BUDGETS_NOT_EXHAUSTED",
    ]

    public let verdict: String
    public let runID: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String
    public let reviewedBuild: PhaseBEligibilityReviewedBuild
    public let goalIdentitySHA256: String
    public let stagingRunDirectory: String
    public let issuedAtISO8601: String
    /// Stage 03 execution contract (handoff.md) evaluated by the producer.
    public let handoffPath: String
    public let handoffSHA256: String
    /// Frozen rule/predicate/fixture/provenance artifacts: logical name -> path
    /// and logical name -> SHA-256 of the exact bytes.
    public let frozenArtifactPaths: [String: String]
    public let frozenArtifactSHA256: [String: String]
    public let predicates: [PhaseBEligibilityPredicate]

    public init(
        verdict: String,
        runID: String,
        planSHA256: String,
        reviewedImplementationSHA256: String,
        reviewedBuild: PhaseBEligibilityReviewedBuild,
        goalIdentitySHA256: String,
        stagingRunDirectory: String,
        issuedAtISO8601: String,
        handoffPath: String,
        handoffSHA256: String,
        frozenArtifactPaths: [String: String],
        frozenArtifactSHA256: [String: String],
        predicates: [PhaseBEligibilityPredicate]
    ) {
        self.verdict = verdict
        self.runID = runID
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        self.reviewedBuild = reviewedBuild
        self.goalIdentitySHA256 = goalIdentitySHA256
        self.stagingRunDirectory = stagingRunDirectory
        self.issuedAtISO8601 = issuedAtISO8601
        self.handoffPath = handoffPath
        self.handoffSHA256 = handoffSHA256
        self.frozenArtifactPaths = frozenArtifactPaths
        self.frozenArtifactSHA256 = frozenArtifactSHA256
        self.predicates = predicates
    }

    /// The goal identity digest uses the same key composition as the durable
    /// goal slot, so a different run ID, ledger path or session cannot move the
    /// eligibility onto a fresh identity.
    public static func goalIdentityDigest(_ authorization: ImmutableRunAuthorization) -> String {
        let key = [authorization.goal, authorization.group, authorization.album, authorization.stagingRoot]
            .joined(separator: "\u{0}")
        return EvidenceIO.sha256Hex(Data(key.utf8))
    }

    /// Structural validation: verdicts, bindings and hash well-formedness. It
    /// performs no file IO, so it can run anywhere; production additionally
    /// requires `validateWithRecomputedEvidence` at the owner boundary.
    public func validate(against authorization: ImmutableRunAuthorization, entitlementConsumed: Bool) throws {
        guard verdict == Self.eligibleVerdict else { throw PhaseBEligibilityError.notEligible(verdict) }
        guard runID == authorization.runID,
              planSHA256 == authorization.planSHA256,
              reviewedImplementationSHA256 == authorization.reviewedImplementationSHA256,
              stagingRunDirectory == authorization.stagingRunDirectory,
              !issuedAtISO8601.isEmpty else {
            throw PhaseBEligibilityError.bindingMismatch("run/plan/implementation/staging binding differs from the authorization")
        }
        guard goalIdentitySHA256 == Self.goalIdentityDigest(authorization) else {
            throw PhaseBEligibilityError.bindingMismatch("goal identity digest differs from the authorization")
        }
        guard ReviewedBuildState.isCommitHex(reviewedBuild.headSHA),
              Self.isSHA256Hex(reviewedBuild.pathsDiffSHA256),
              Self.isSHA256Hex(reviewedBuild.binarySHA256) else {
            throw PhaseBEligibilityError.malformedBindingHash("reviewed HEAD/diff/binary binding is not a well-formed hash triple")
        }
        guard !entitlementConsumed else { throw PhaseBEligibilityError.entitlementConsumed }
        guard Self.isSHA256Hex(planSHA256),
              Self.isSHA256Hex(reviewedImplementationSHA256),
              Self.isSHA256Hex(goalIdentitySHA256),
              Self.isSHA256Hex(handoffSHA256),
              !handoffPath.isEmpty,
              !frozenArtifactSHA256.isEmpty,
              Set(frozenArtifactPaths.keys) == Set(frozenArtifactSHA256.keys),
              frozenArtifactSHA256.values.allSatisfy(Self.isSHA256Hex),
              frozenArtifactPaths.values.allSatisfy({ !$0.isEmpty }) else {
            throw PhaseBEligibilityError.malformedBindingHash("artifact binding is not a well-formed path/hash pair")
        }
        for identifier in Self.requiredPredicates {
            guard let predicate = predicates.first(where: { $0.identifier == identifier }) else {
                throw PhaseBEligibilityError.missingPredicate(identifier)
            }
            guard predicate.verdict == "PASS" else {
                throw PhaseBEligibilityError.predicateNotPass(identifier, verdict: predicate.verdict)
            }
            guard Self.isSHA256Hex(predicate.evidenceSHA256), !predicate.evidencePath.isEmpty else {
                throw PhaseBEligibilityError.predicateEvidenceUnbound(identifier)
            }
        }
        // The exact required predicate set: an extra predicate would carry
        // evidence that no canonical binding covers, so it is refused rather
        // than silently ignored.
        let identifiers = Set(predicates.map(\.identifier))
        guard identifiers == Set(Self.requiredPredicates),
              predicates.count == Self.requiredPredicates.count else {
            throw PhaseBEligibilityError.predicateSetMismatch(
                predicates.map(\.identifier).sorted().joined(separator: ",")
            )
        }
    }

    /// Production recomputation: structural validation plus re-reading and
    /// re-hashing the reviewed Plan bytes, the Stage 03 handoff bytes, every
    /// frozen artifact and every predicate's evidence file, and comparing the
    /// caller-recomputed implementation source digest. Nothing here is trusted
    /// by label.
    public func validateWithRecomputedEvidence(
        against authorization: ImmutableRunAuthorization,
        entitlementConsumed: Bool,
        recomputation: PhaseBEligibilityRecomputation
    ) throws {
        try validate(against: authorization, entitlementConsumed: entitlementConsumed)
        // Canonical reviewed expectations must themselves be well-formed and
        // complete before any artifact declaration is compared against them.
        guard Self.isSHA256Hex(recomputation.canonicalHandoff.sha256),
              !recomputation.canonicalHandoff.path.isEmpty,
              !recomputation.canonicalFrozenArtifacts.isEmpty,
              recomputation.canonicalFrozenArtifacts.values.allSatisfy({ Self.isSHA256Hex($0.sha256) && !$0.path.isEmpty }),
              Set(recomputation.canonicalPredicateEvidence.keys) == Set(Self.requiredPredicates),
              recomputation.canonicalPredicateEvidence.values.allSatisfy({ Self.isSHA256Hex($0.sha256) && !$0.path.isEmpty }),
              !recomputation.allowedEvidenceRoots.isEmpty else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch("canonical reviewed expectations are missing or malformed")
        }
        guard ReviewedBuildState.isCommitHex(recomputation.canonicalReviewedBuild.reviewedHeadSHA),
              Self.isSHA256Hex(recomputation.canonicalReviewedBuild.reviewedPathsDiffSHA256),
              Self.isSHA256Hex(recomputation.canonicalReviewedBuild.reviewedBinarySHA256),
              ReviewedBuildState.isCommitHex(recomputation.observedReviewedBuild.headSHA),
              Self.isSHA256Hex(recomputation.observedReviewedBuild.reviewedPathsDiffSHA256),
              Self.isSHA256Hex(recomputation.observedReviewedBuild.binarySHA256) else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch("reviewed HEAD/diff/binary expectations are missing or malformed")
        }
        guard reviewedBuild.headSHA == recomputation.canonicalReviewedBuild.reviewedHeadSHA,
              reviewedBuild.pathsDiffSHA256 == recomputation.canonicalReviewedBuild.reviewedPathsDiffSHA256,
              reviewedBuild.binarySHA256 == recomputation.canonicalReviewedBuild.reviewedBinarySHA256 else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch("artifact HEAD/diff/binary binding differs from the reviewed configuration")
        }
        guard recomputation.observedReviewedBuild.reviewedHeadIsAncestor,
              recomputation.observedReviewedBuild.reviewedPathsDiffSHA256 == recomputation.canonicalReviewedBuild.reviewedPathsDiffSHA256,
              recomputation.observedReviewedBuild.binarySHA256 == recomputation.canonicalReviewedBuild.reviewedBinarySHA256 else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch("observed HEAD/diff/binary state does not match the reviewed configuration")
        }
        // Containment: every declared and canonical evidence path must resolve
        // beneath one of the reviewed allowed roots, so no binding can point
        // the gate at an arbitrary readable file.
        try Self.requireContained(
            paths: [handoffPath] + frozenArtifactPaths.values + predicates.map(\.evidencePath),
            within: recomputation.allowedEvidenceRoots,
            label: "artifact"
        )
        try Self.requireContained(
            paths: [recomputation.canonicalHandoff.path]
                + recomputation.canonicalFrozenArtifacts.values.map(\.path)
                + recomputation.canonicalPredicateEvidence.values.map(\.path),
            within: recomputation.allowedEvidenceRoots,
            label: "canonical"
        )
        let planSHA = try Self.fileSHA256(recomputation.planURL.path)
        guard planSHA == authorization.planSHA256, planSHA == planSHA256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("reviewed plan bytes")
        }
        guard recomputation.recomputedImplementationSHA256 == authorization.reviewedImplementationSHA256,
              recomputation.recomputedImplementationSHA256 == reviewedImplementationSHA256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("reviewed implementation source digest")
        }
        guard handoffPath == recomputation.canonicalHandoff.path,
              handoffSHA256 == recomputation.canonicalHandoff.sha256 else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch("stage 03 handoff binding differs from the reviewed configuration")
        }
        guard try Self.fileSHA256(handoffPath) == recomputation.canonicalHandoff.sha256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("stage 03 handoff bytes")
        }
        guard Set(frozenArtifactSHA256.keys) == Set(recomputation.canonicalFrozenArtifacts.keys) else {
            throw PhaseBEligibilityError.canonicalEvidenceMismatch(
                "frozen artifact name set differs from the reviewed configuration"
            )
        }
        for (name, canonical) in recomputation.canonicalFrozenArtifacts.sorted(by: { $0.key < $1.key }) {
            guard let path = frozenArtifactPaths[name], let declaredSHA = frozenArtifactSHA256[name] else {
                throw PhaseBEligibilityError.canonicalEvidenceMismatch("frozen artifact \(name) is not bound by the artifact")
            }
            guard path == canonical.path, declaredSHA == canonical.sha256 else {
                throw PhaseBEligibilityError.canonicalEvidenceMismatch("frozen artifact \(name) binding differs from the reviewed configuration")
            }
            guard try Self.fileSHA256(path) == canonical.sha256 else {
                throw PhaseBEligibilityError.evidenceDigestMismatch("frozen artifact \(name)")
            }
        }
        for identifier in Self.requiredPredicates {
            guard let predicate = predicates.first(where: { $0.identifier == identifier }) else {
                throw PhaseBEligibilityError.missingPredicate(identifier)
            }
            guard let canonical = recomputation.canonicalPredicateEvidence[identifier] else {
                throw PhaseBEligibilityError.canonicalEvidenceMismatch("predicate \(identifier) has no canonical evidence binding")
            }
            guard predicate.evidencePath == canonical.path, predicate.evidenceSHA256 == canonical.sha256 else {
                throw PhaseBEligibilityError.canonicalEvidenceMismatch("predicate \(identifier) evidence binding differs from the reviewed configuration")
            }
            guard try Self.fileSHA256(canonical.path) == canonical.sha256 else {
                throw PhaseBEligibilityError.evidenceDigestMismatch("predicate evidence \(identifier)")
            }
        }
    }

    /// Loads an eligibility artifact that must live beneath the run's evidence
    /// directory; an artifact from another run or directory cannot arm this one.
    public static func load(fileURL: URL, withinRunDirectory: URL) throws -> PhaseBEligibilityArtifact {
        let root = withinRunDirectory.resolvingSymlinksInPath().standardizedFileURL
        let file = fileURL.resolvingSymlinksInPath().standardizedFileURL
        let rootPath = root.path.hasSuffix("/") ? root.path : root.path + "/"
        guard file.path.hasPrefix(rootPath) else { throw PhaseBEligibilityError.artifactOutsideRunDirectory }
        return try JSONDecoder().decode(PhaseBEligibilityArtifact.self, from: Data(contentsOf: file))
    }

    public static func isSHA256Hex(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy { character in
            character.isNumber || ("a"..."f").contains(character)
        }
    }

    /// Every evidence path must resolve (after symlink resolution) beneath one
    /// of the reviewed roots. A path that escapes every root is refused.
    private static func requireContained(paths: [String], within roots: [URL], label: String) throws {
        let resolvedRoots = roots.map { root -> String in
            let path = root.resolvingSymlinksInPath().standardizedFileURL.path
            return path.hasSuffix("/") ? path : path + "/"
        }
        for path in paths {
            let resolved = URL(fileURLWithPath: path).resolvingSymlinksInPath().standardizedFileURL.path
            guard resolvedRoots.contains(where: { resolved.hasPrefix($0) }) else {
                throw PhaseBEligibilityError.evidenceOutsideAllowedRoots("\(label) \(path)")
            }
        }
    }

    private static func fileSHA256(_ path: String) throws -> String {
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)) else {
            throw PhaseBEligibilityError.evidenceUnavailable(path)
        }
        return EvidenceIO.sha256Hex(data)
    }
}
