import Foundation

// MARK: - Capture epoch authority for one evidence run directory
//
// Evidence artifacts are named `state-<STATE>-<epoch>.json` inside the run's
// evidence directory, so an epoch must never be issued twice for that
// directory, even by a later process. The floor is derived from the artifacts
// that are actually present instead of from a separate seed file, so the
// authority can never disagree with the append-only evidence it protects.

public enum RunEpochAuthorityError: Error, Equatable, CustomStringConvertible {
    case directoryUnavailable(URL, String)
    case writeFailed(URL, String)

    public var description: String {
        switch self {
        case let .directoryUnavailable(url, detail):
            return "directoryUnavailable(\(url.path), \(detail))"
        case let .writeFailed(url, detail):
            return "writeFailed(\(url.path), \(detail))"
        }
    }
}

public final class RunEpochAuthority: @unchecked Sendable {
    private let directory: URL
    private let lock = NSLock()
    private var nextValue: UInt64
    private var stopReason: String?

    /// Opens the authority for one run directory. `floor` is the maximum epoch
    /// named by an existing artifact, so a fresh process continues after the
    /// evidence instead of restarting at 1.
    public init(evidenceRunDirectory: URL) throws {
        let canonical = evidenceRunDirectory.resolvingSymlinksInPath().standardizedFileURL
        do {
            try EvidenceIO.ensureDirectory(canonical)
        } catch {
            throw RunEpochAuthorityError.directoryUnavailable(canonical, String(describing: error))
        }
        let derived = try Self.artifactFloor(in: canonical)
        self.directory = canonical
        self.nextValue = derived &+ 1
    }

    /// Highest epoch claimed by evidence when this authority opened (0 when the
    /// run directory was empty).
    public var floor: UInt64 {
        lock.lock()
        defer { lock.unlock() }
        return nextValue - 1
    }

    /// Next capture epoch. Never throws: on a persistent storage failure the
    /// authority refuses instead of reusing an epoch, and `nextEpoch()` returns
    /// 0 so the bundle validator rejects the observation before it is retained
    /// as evidence.
    public func nextEpoch() -> UInt64 {
        lock.lock()
        defer { lock.unlock() }
        guard stopReason == nil else { return 0 }
        do {
            // Re-derive the floor from the evidence itself before every issue:
            // an epoch already named by an artifact is never issued again.
            let claimed = try Self.artifactFloor(in: directory)
            guard claimed < nextValue else {
                stopReason = "evidence already claims epoch \(claimed); refusing to reuse an epoch"
                return 0
            }
        } catch {
            stopReason = String(describing: error)
            return 0
        }
        let value = nextValue
        nextValue += 1
        return value
    }

    /// Why this authority stopped issuing epochs, when it did.
    public var refusal: String? {
        lock.lock()
        defer { lock.unlock() }
        return stopReason
    }

    /// Maximum epoch named by `state-<STATE>-<epoch>.json` artifacts, 0 when the
    /// directory holds none.
    public static func artifactFloor(in directory: URL) throws -> UInt64 {
        let names: [String]
        do {
            names = try FileManager.default.contentsOfDirectory(atPath: directory.path)
        } catch {
            throw RunEpochAuthorityError.directoryUnavailable(directory, String(describing: error))
        }
        var floor: UInt64 = 0
        for name in names {
            guard name.hasPrefix("state-"), name.hasSuffix(".json") else { continue }
            let stem = name.dropLast(".json".count)
            guard let separator = stem.lastIndex(of: "-") else { continue }
            guard let epoch = UInt64(stem[stem.index(after: separator)...]) else { continue }
            floor = max(floor, epoch)
        }
        return floor
    }
}
