import Foundation
import XCTest
@testable import Rev28Core

/// The reviewed implementation manifest now covers the build configuration,
/// the production Swift and the invoked tools, and the reviewed HEAD/diff/
/// binary state is recomputed from git and the running executable.
final class ReviewedImplementationManifestTests: XCTestCase {
    private func makeRepository() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        for directory in ["rev28/Sources/Rev28Core", "rev28/Sources/rev28ctl", "rev28/Tools"] {
            try FileManager.default.createDirectory(
                at: root.appendingPathComponent(directory),
                withIntermediateDirectories: true
            )
        }
        try Data("// package".utf8).write(to: root.appendingPathComponent("rev28/Package.swift"))
        try Data("core".utf8).write(to: root.appendingPathComponent("rev28/Sources/Rev28Core/Core.swift"))
        try Data("ctl".utf8).write(to: root.appendingPathComponent("rev28/Sources/rev28ctl/main.swift"))
        try Data("tool".utf8).write(to: root.appendingPathComponent("rev28/Tools/replay.py"))
        try Data("readme".utf8).write(to: root.appendingPathComponent("rev28/README.md"))
        return root
    }

    func testManifestIncludesConfigurationSwiftAndTools() throws {
        let root = try makeRepository()
        XCTAssertEqual(
            try ReviewedImplementationDigest.manifestPaths(repositoryRoot: root),
            [
                "rev28/Package.swift",
                "rev28/Sources/Rev28Core/Core.swift",
                "rev28/Sources/rev28ctl/main.swift",
                "rev28/Tools/replay.py",
            ]
        )
    }

    func testDigestBindsConfigurationToolsAndSourceButNotUnreviewedFiles() throws {
        let root = try makeRepository()
        let base = try ReviewedImplementationDigest.compute(repositoryRoot: root)

        try Data("// changed".utf8).write(to: root.appendingPathComponent("rev28/Package.swift"))
        XCTAssertNotEqual(base, try ReviewedImplementationDigest.compute(repositoryRoot: root))
        try Data("// package".utf8).write(to: root.appendingPathComponent("rev28/Package.swift"))

        try Data("tool2".utf8).write(to: root.appendingPathComponent("rev28/Tools/verify.py"))
        XCTAssertNotEqual(base, try ReviewedImplementationDigest.compute(repositoryRoot: root))
        try FileManager.default.removeItem(at: root.appendingPathComponent("rev28/Tools/verify.py"))

        // A file outside the reviewed manifest must not move the digest.
        try Data("readme2".utf8).write(to: root.appendingPathComponent("rev28/README.md"))
        XCTAssertEqual(base, try ReviewedImplementationDigest.compute(repositoryRoot: root))
    }
}

final class ReviewedBuildStateTests: XCTestCase {
    private func makeGitRepository() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        for directory in ["rev28/Sources/Rev28Core", "rev28/Sources/rev28ctl", "rev28/Tools"] {
            try FileManager.default.createDirectory(
                at: root.appendingPathComponent(directory),
                withIntermediateDirectories: true
            )
        }
        try Data("// package".utf8).write(to: root.appendingPathComponent("rev28/Package.swift"))
        try Data("core".utf8).write(to: root.appendingPathComponent("rev28/Sources/Rev28Core/Core.swift"))
        try Data("tool".utf8).write(to: root.appendingPathComponent("rev28/Tools/replay.py"))
        _ = try git(["init", "-q"], in: root)
        _ = try git(["add", "."], in: root)
        _ = try git(commitArguments("reviewed"), in: root)
        return root
    }

    private func commitArguments(_ message: String) -> [String] {
        ["-c", "user.name=Reviewed Build Test", "-c", "user.email=reviewed@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", message]
    }

    @discardableResult
    private func git(_ arguments: [String], in root: URL) throws -> (status: Int32, stdout: String) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = ["-C", root.path] + arguments
        var environment = ProcessInfo.processInfo.environment
        environment["GIT_OPTIONAL_LOCKS"] = "0"
        process.environment = environment
        let stdout = Pipe()
        process.standardOutput = stdout
        process.standardError = Pipe()
        try process.run()
        let data = stdout.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return (process.terminationStatus, String(data: data, encoding: .utf8) ?? "")
    }

    func testObserveBindsReviewedHeadEmptyDiffAndBinary() throws {
        let root = try makeGitRepository()
        let binary = root.appendingPathComponent("rev28ctl")
        try Data("binary-bytes".utf8).write(to: binary)

        let head = try ReviewedBuildState.headSHA(repositoryRoot: root)
        let observations = try ReviewedBuildState.observe(
            repositoryRoot: root,
            reviewedHeadSHA: head,
            executableURL: binary
        )
        XCTAssertEqual(observations.headSHA, head)
        XCTAssertTrue(observations.reviewedHeadIsAncestor)
        XCTAssertEqual(observations.reviewedPathsDiffSHA256, EvidenceIO.sha256Hex(Data()))
        XCTAssertEqual(observations.binarySHA256, EvidenceIO.sha256Hex(Data("binary-bytes".utf8)))
    }

    func testObserveDetectsReviewedPathDriftAndAcceptsEvidenceOnlyCommits() throws {
        let root = try makeGitRepository()
        let binary = root.appendingPathComponent("rev28ctl")
        try Data("binary-bytes".utf8).write(to: binary)
        let reviewed = try ReviewedBuildState.headSHA(repositoryRoot: root)

        // Evidence-only commit outside the reviewed paths: still clean.
        try Data("evidence".utf8).write(to: root.appendingPathComponent("evidence-record.json"))
        _ = try git(["add", "evidence-record.json"], in: root)
        _ = try git(commitArguments("evidence"), in: root)
        let afterEvidence = try ReviewedBuildState.observe(
            repositoryRoot: root,
            reviewedHeadSHA: reviewed,
            executableURL: binary
        )
        XCTAssertTrue(afterEvidence.reviewedHeadIsAncestor)
        XCTAssertEqual(afterEvidence.reviewedPathsDiffSHA256, EvidenceIO.sha256Hex(Data()))

        // A changed reviewed file moves the diff digest.
        try Data("drifted".utf8).write(to: root.appendingPathComponent("rev28/Sources/Rev28Core/Core.swift"))
        let drifted = try ReviewedBuildState.observe(
            repositoryRoot: root,
            reviewedHeadSHA: reviewed,
            executableURL: binary
        )
        XCTAssertNotEqual(drifted.reviewedPathsDiffSHA256, EvidenceIO.sha256Hex(Data()))
    }

    func testIsAncestorRefusesRewrittenHistory() throws {
        let root = try makeGitRepository()
        let reviewed = try ReviewedBuildState.headSHA(repositoryRoot: root)
        _ = try git(["checkout", "-q", "--orphan", "unrelated"], in: root)
        _ = try git(commitArguments("unrelated"), in: root)
        XCTAssertFalse(
            try ReviewedBuildState.isAncestor(repositoryRoot: root, ancestor: reviewed, descendant: "HEAD")
        )
    }
}
