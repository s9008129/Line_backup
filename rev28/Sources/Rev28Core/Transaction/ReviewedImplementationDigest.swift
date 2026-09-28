import Foundation

// MARK: - Reviewed implementation source digest (plan PHASE_B_ELIGIBILITY)
//
// One implementation of the source digest, shared by the CLI preconditions and
// the Phase B eligibility recomputation: sha256 over sorted
// (repo-relative path + NUL + file bytes + NUL) for every `.swift` file under
// the two reviewed source roots.

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

    public static func compute(repositoryRoot: URL) throws -> String {
        var paths: [URL] = []
        for relativeRoot in sourceRoots {
            let root = repositoryRoot.appendingPathComponent(relativeRoot)
            guard FileManager.default.fileExists(atPath: root.path),
                  let enumerator = FileManager.default.enumerator(
                      at: root,
                      includingPropertiesForKeys: [.isRegularFileKey]
                  ) else {
                throw ReviewedImplementationDigestError.sourceTreeUnavailable(relativeRoot)
            }
            while let url = enumerator.nextObject() as? URL {
                guard url.pathExtension == "swift" else { continue }
                paths.append(url)
            }
        }
        paths.sort { $0.path < $1.path }
        var material = Data()
        for url in paths {
            let relative = String(url.path.dropFirst(repositoryRoot.path.count + 1))
            material.append(Data(relative.utf8))
            material.append(0)
            material.append(try Data(contentsOf: url))
            material.append(0)
        }
        return EvidenceIO.sha256Hex(material)
    }
}
