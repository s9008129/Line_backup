import Foundation

// MARK: - Phase B eligibility (R4 C4/C5)
//
// The one-shot Save All entitlement may only be armed by an explicit,
// machine-checkable eligibility artifact whose every required predicate is
// PASS and whose bindings match the exact run authorization. Absence of the
// artifact (this AB round) is refusal, never an implicit arm.

public enum PhaseBEligibilityError: Error, Equatable, CustomStringConvertible {
    case missingArtifact
    case notEligible(String)
    case bindingMismatch(String)
    case missingPredicate(String)
    case predicateNotPass(String, verdict: String)
    case entitlementConsumed
    case artifactOutsideRunDirectory

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
        }
    }
}

public struct PhaseBEligibilityPredicate: Codable, Equatable, Sendable {
    public let identifier: String
    public let verdict: String

    public init(identifier: String, verdict: String) {
        self.identifier = identifier
        self.verdict = verdict
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
    public let predicates: [PhaseBEligibilityPredicate]

    public init(
        verdict: String,
        runID: String,
        planSHA256: String,
        reviewedImplementationSHA256: String,
        goalIdentitySHA256: String,
        stagingRunDirectory: String,
        issuedAtISO8601: String,
        predicates: [PhaseBEligibilityPredicate]
    ) {
        self.verdict = verdict
        self.runID = runID
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        self.goalIdentitySHA256 = goalIdentitySHA256
        self.stagingRunDirectory = stagingRunDirectory
        self.issuedAtISO8601 = issuedAtISO8601
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
        for identifier in Self.requiredPredicates {
            guard let predicate = predicates.first(where: { $0.identifier == identifier }) else {
                throw PhaseBEligibilityError.missingPredicate(identifier)
            }
            guard predicate.verdict == "PASS" else {
                throw PhaseBEligibilityError.predicateNotPass(identifier, verdict: predicate.verdict)
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
}
