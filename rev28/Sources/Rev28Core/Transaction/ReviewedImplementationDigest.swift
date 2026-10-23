import Foundation

// MARK: - Reviewed implementation source digest (plan PHASE_B_ELIGIBILITY)
//
// One implementation of the reviewed implementation manifest digest, shared by
// the CLI preconditions and the Phase B eligibility recomputation: sha256 over
// sorted (repo-relative path + NUL + file bytes + NUL) for the reviewed build
// configuration (Package.swift), the production Swift under the two source
// roots and the invoked tools. The plan explicitly rejects a source-only Swift
// digest, so Package.swift and the tool files are part of the same manifest.

public enum ReviewedImplementationDigestError: Error, CustomStringConvertible {
    case sourceTreeUnavailable(String)

    public var description: String {
        switch self {
        case let .sourceTreeUnavailable(path):
            return "reviewedImplementationSourceTreeUnavailable(\(path))"
        }
    }
}

public enum ReviewedImplementationDigest {
    public static let sourceRoots = [
        "rev28/Sources/Rev28Core",
        "rev28/Sources/rev28ctl",
    ]
    /// Reviewed build configuration files that are part of the manifest.
    public static let configurationPaths = [
        "rev28/Package.swift",
    ]
    /// Reviewed invoked tools (the provenance/replay drivers) that are part of
    /// the manifest.
    public static let toolRoots = [
        "rev28/Tools",
    ]

    /// Every reviewed path the git HEAD/diff check must cover.
    public static var reviewedPaths: [String] {
        sourceRoots + configurationPaths + toolRoots
    }

    /// The exact repo-relative paths of the reviewed manifest, sorted.
    public static func manifestPaths(repositoryRoot: URL) throws -> [String] {
        let root = repositoryRoot.resolvingSymlinksInPath().standardizedFileURL
        var paths: [String] = []
        for relativeRoot in sourceRoots {
            let directory = root.appendingPathComponent(relativeRoot)
            guard FileManager.default.fileExists(atPath: directory.path),
                  let enumerator = FileManager.default.enumerator(
                      at: directory,
                      includingPropertiesForKeys: [.isRegularFileKey]
                  ) else {
                throw ReviewedImplementationDigestError.sourceTreeUnavailable(relativeRoot)
            }
            while let url = enumerator.nextObject() as? URL {
                guard url.pathExtension == "swift" else { continue }
                paths.append(try relativePath(of: url, under: relativeRoot))
            }
        }
        for relativePath in configurationPaths {
            guard FileManager.default.fileExists(atPath: root.appendingPathComponent(relativePath).path) else {
                throw ReviewedImplementationDigestError.sourceTreeUnavailable(relativePath)
            }
            paths.append(relativePath)
        }
        for relativeRoot in toolRoots {
            let directory = root.appendingPathComponent(relativeRoot)
            guard FileManager.default.fileExists(atPath: directory.path),
                  let enumerator = FileManager.default.enumerator(
                      at: directory,
                      includingPropertiesForKeys: [.isRegularFileKey]
                  ) else {
                throw ReviewedImplementationDigestError.sourceTreeUnavailable(relativeRoot)
            }
            while let url = enumerator.nextObject() as? URL {
                guard (try? url.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true else { continue }
                paths.append(try relativePath(of: url, under: relativeRoot))
            }
        }
        paths.sort()
        return paths
    }

    /// Repo-relative path derived from the reviewed root marker, so it stays
    /// correct even when the filesystem reports /private/var for /var.
    private static func relativePath(of url: URL, under relativeRoot: String) throws -> String {
        let marker = "/\(relativeRoot)/"
        guard let range = url.path.range(of: marker) else {
            throw ReviewedImplementationDigestError.sourceTreeUnavailable(url.path)
        }
        return relativeRoot + "/" + String(url.path[range.upperBound...])
    }

    public static func compute(repositoryRoot: URL) throws -> String {
        var material = Data()
        for relative in try manifestPaths(repositoryRoot: repositoryRoot) {
            material.append(Data(relative.utf8))
            material.append(0)
            material.append(try Data(contentsOf: repositoryRoot.appendingPathComponent(relative)))
            material.append(0)
        }
        return EvidenceIO.sha256Hex(material)
    }
}
