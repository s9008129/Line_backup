import Foundation

// MARK: - Reviewed HEAD / diff / binary state (plan PHASE_B_ELIGIBILITY)
//
// The plan requires the reviewed implementation manifest to be accompanied by
// the exact HEAD/diff state and binary hash. The canonical reviewed values are
// supplied by the reviewed configuration; the observations here are recomputed
// from the repository and the running executable, so a stale head, a drifted
// reviewed file or a substituted binary can never arm the entitlement.

public enum ReviewedBuildStateError: Error, CustomStringConvertible {
    case gitUnavailable(String)
    case gitCommandFailed(arguments: [String], status: Int32, stderr: String)
    case malformedReviewedHead(String)
    case executableUnavailable(String)

    public var description: String {
        switch self {
        case let .gitUnavailable(detail):
            return "reviewedBuildGitUnavailable(\(detail))"
        case let .gitCommandFailed(arguments, status, stderr):
            return "reviewedBuildGitCommandFailed(\(arguments.joined(separator: " ")): \(status): \(stderr))"
        case let .malformedReviewedHead(value):
            return "reviewedBuildHeadNotACommit(\(value))"
        case let .executableUnavailable(path):
            return "reviewedBuildExecutableUnavailable(\(path))"
        }
    }
}

/// Canonical reviewed values from the reviewed configuration.
public struct ReviewedBuildExpectations: Equatable, Sendable {
    public let reviewedHeadSHA: String
    public let reviewedPathsDiffSHA256: String
    public let reviewedBinarySHA256: String

    public init(reviewedHeadSHA: String, reviewedPathsDiffSHA256: String, reviewedBinarySHA256: String) {
        self.reviewedHeadSHA = reviewedHeadSHA
        self.reviewedPathsDiffSHA256 = reviewedPathsDiffSHA256
        self.reviewedBinarySHA256 = reviewedBinarySHA256
    }
}

/// Facts recomputed from the live repository and the running executable.
public struct ReviewedBuildObservations: Equatable, Sendable {
    public let headSHA: String
    public let reviewedPathsDiffSHA256: String
    public let reviewedHeadIsAncestor: Bool
    public let binarySHA256: String

    public init(headSHA: String, reviewedPathsDiffSHA256: String, reviewedHeadIsAncestor: Bool, binarySHA256: String) {
        self.headSHA = headSHA
        self.reviewedPathsDiffSHA256 = reviewedPathsDiffSHA256
        self.reviewedHeadIsAncestor = reviewedHeadIsAncestor
        self.binarySHA256 = binarySHA256
    }
}

public enum ReviewedBuildState {
    public static func isCommitHex(_ value: String) -> Bool {
        (value.count == 40 || value.count == 64) && value.allSatisfy { character in
            character.isNumber || ("a"..."f").contains(character)
        }
    }

    /// Recomputed observation bundle for one eligibility check.
    public static func observe(
        repositoryRoot: URL,
        reviewedHeadSHA: String,
        executableURL: URL
    ) throws -> ReviewedBuildObservations {
        ReviewedBuildObservations(
            headSHA: try headSHA(repositoryRoot: repositoryRoot),
            reviewedPathsDiffSHA256: try reviewedPathsDiffSHA256(
                repositoryRoot: repositoryRoot,
                reviewedHeadSHA: reviewedHeadSHA
            ),
            reviewedHeadIsAncestor: try isAncestor(
                repositoryRoot: repositoryRoot,
                ancestor: reviewedHeadSHA,
                descendant: "HEAD"
            ),
            binarySHA256: try executableSHA256(at: executableURL)
        )
    }

    public static func headSHA(repositoryRoot: URL) throws -> String {
        let result = try git(["rev-parse", "HEAD"], repositoryRoot: repositoryRoot)
        guard result.status == 0 else {
            throw ReviewedBuildStateError.gitCommandFailed(
                arguments: ["rev-parse", "HEAD"],
                status: result.status,
                stderr: result.stderr
            )
        }
        let head = result.stdoutString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard isCommitHex(head) else { throw ReviewedBuildStateError.malformedReviewedHead(head) }
        return head
    }

    /// SHA-256 of the `git diff` bytes between the reviewed commit and the
    /// working tree for exactly the reviewed paths. A reviewed tree with no
    /// drift yields the SHA-256 of empty output.
    public static func reviewedPathsDiffSHA256(repositoryRoot: URL, reviewedHeadSHA: String) throws -> String {
        guard isCommitHex(reviewedHeadSHA) else {
            throw ReviewedBuildStateError.malformedReviewedHead(reviewedHeadSHA)
        }
        let arguments = [
            "-c", "core.quotepath=false",
            "diff", "--no-color", "--no-ext-diff", reviewedHeadSHA, "--",
        ] + ReviewedImplementationDigest.reviewedPaths
        let result = try git(arguments, repositoryRoot: repositoryRoot)
        guard result.status == 0 else {
            throw ReviewedBuildStateError.gitCommandFailed(
                arguments: arguments,
                status: result.status,
                stderr: result.stderr
            )
        }
        return EvidenceIO.sha256Hex(result.stdout)
    }

    /// True when the reviewed commit is the current HEAD or an ancestor of it,
    /// so evidence-only commits after the review stay valid while a rewritten
    /// history is refused.
    public static func isAncestor(repositoryRoot: URL, ancestor: String, descendant: String) throws -> Bool {
        guard isCommitHex(ancestor) else {
            throw ReviewedBuildStateError.malformedReviewedHead(ancestor)
        }
        let arguments = ["merge-base", "--is-ancestor", ancestor, descendant]
        let result = try git(arguments, repositoryRoot: repositoryRoot)
        switch result.status {
        case 0:
            return true
        case 1:
            return false
        default:
            throw ReviewedBuildStateError.gitCommandFailed(
                arguments: arguments,
                status: result.status,
                stderr: result.stderr
            )
        }
    }

    public static func executableSHA256(at url: URL) throws -> String {
        guard let data = try? Data(contentsOf: url) else {
            throw ReviewedBuildStateError.executableUnavailable(url.path)
        }
        return EvidenceIO.sha256Hex(data)
    }

    private struct GitResult {
        let status: Int32
        let stdout: Data
        let stderr: String

        var stdoutString: String { String(data: stdout, encoding: .utf8) ?? "" }
    }

    private static func git(_ arguments: [String], repositoryRoot: URL) throws -> GitResult {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = ["-C", repositoryRoot.path] + arguments
        var environment = ProcessInfo.processInfo.environment
        environment["GIT_OPTIONAL_LOCKS"] = "0"
        environment["GIT_TERMINAL_PROMPT"] = "0"
        process.environment = environment
        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr
        do {
            try process.run()
        } catch {
            throw ReviewedBuildStateError.gitUnavailable(error.localizedDescription)
        }
        let stdoutData = stdout.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderr.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return GitResult(
            status: process.terminationStatus,
            stdout: stdoutData,
            stderr: String(data: stderrData, encoding: .utf8) ?? ""
        )
    }
}
