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
    case evidenceUnavailable(String)
    case evidenceDigestMismatch(String)

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
        case let .evidenceUnavailable(path):
            return "phaseBEvidenceUnavailable(\(path))"
        case let .evidenceDigestMismatch(detail):
            return "phaseBEvidenceDigestMismatch(\(detail))"
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

/// The two recomputation inputs that live outside the artifact itself: the
/// reviewed Plan bytes (anchored by the one-shot authorization's planSHA256)
/// and the reviewed implementation source digest, recomputed from the
/// repository root with the same digest code the authorization binds.
public struct PhaseBEligibilityRecomputation: Equatable, Sendable {
    public let planURL: URL
    public let recomputedImplementationSHA256: String

    public init(planURL: URL, recomputedImplementationSHA256: String) {
        self.planURL = planURL
        self.recomputedImplementationSHA256 = recomputedImplementationSHA256
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
    ]

    public let verdict: String
    public let runID: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String
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
        let planSHA = try Self.fileSHA256(recomputation.planURL.path)
        guard planSHA == authorization.planSHA256, planSHA == planSHA256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("reviewed plan bytes")
        }
        guard recomputation.recomputedImplementationSHA256 == authorization.reviewedImplementationSHA256,
              recomputation.recomputedImplementationSHA256 == reviewedImplementationSHA256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("reviewed implementation source digest")
        }
        guard try Self.fileSHA256(handoffPath) == handoffSHA256 else {
            throw PhaseBEligibilityError.evidenceDigestMismatch("stage 03 handoff bytes")
        }
        for (name, expected) in frozenArtifactSHA256.sorted(by: { $0.key < $1.key }) {
            guard let path = frozenArtifactPaths[name] else {
                throw PhaseBEligibilityError.evidenceUnavailable("frozen artifact \(name) has no bound path")
            }
            guard try Self.fileSHA256(path) == expected else {
                throw PhaseBEligibilityError.evidenceDigestMismatch("frozen artifact \(name)")
            }
        }
        for identifier in Self.requiredPredicates {
            guard let predicate = predicates.first(where: { $0.identifier == identifier }) else {
                throw PhaseBEligibilityError.missingPredicate(identifier)
            }
            guard try Self.fileSHA256(predicate.evidencePath) == predicate.evidenceSHA256 else {
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

    private static func fileSHA256(_ path: String) throws -> String {
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)) else {
            throw PhaseBEligibilityError.evidenceUnavailable(path)
        }
        return EvidenceIO.sha256Hex(data)
    }
}
