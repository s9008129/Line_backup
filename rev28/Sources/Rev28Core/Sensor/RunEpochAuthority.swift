import Darwin
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
    private let directoryDescriptor: Int32?
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
        self.directoryDescriptor = nil
        self.nextValue = derived &+ 1
    }

    /// Diagnostic-only existing-directory mode. Owns a descriptor and never
    /// resolves, creates or falls back to a pathname, even after path removal.
    public init(existingDirectoryDescriptor: Int32) throws {
        let label = URL(fileURLWithPath: "/dev/fd/\(existingDirectoryDescriptor)")
        let owned = openat(existingDirectoryDescriptor, ".", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard owned >= 0 else { throw RunEpochAuthorityError.directoryUnavailable(label, "existing directory descriptor required") }
        do {
            let derived = try Self.artifactFloor(descriptor: owned, label: label)
            guard derived < UInt64.max else { throw RunEpochAuthorityError.directoryUnavailable(label, "epoch floor exhausted") }
            directory = label; directoryDescriptor = owned; nextValue = derived + 1
        } catch { close(owned); throw error }
    }

    deinit { if let directoryDescriptor { close(directoryDescriptor) } }

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
            let claimed: UInt64
            if let directoryDescriptor {
                claimed = try Self.artifactFloor(descriptor: directoryDescriptor, label: directory)
            } else {
                claimed = try Self.artifactFloor(in: directory)
            }
            guard claimed < nextValue else {
                stopReason = "evidence already claims epoch \(claimed); refusing to reuse an epoch"
                return 0
            }
        } catch {
            stopReason = String(describing: error)
            return 0
        }
        if directoryDescriptor != nil, nextValue == UInt64.max {
            stopReason = "diagnostic epoch range exhausted"
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

    private static func artifactFloor(descriptor: Int32, label: URL) throws -> UInt64 {
        var facts = stat()
        guard fstat(descriptor, &facts) == 0, facts.st_mode & S_IFMT == S_IFDIR, facts.st_nlink > 0 else {
            throw RunEpochAuthorityError.directoryUnavailable(label, "directory unlinked or unavailable")
        }
        // APFS retains st_nlink and F_GETPATH for an open, deleted directory.
        // Corroborate a real non-symlink entry in its descriptor-relative parent
        // rather than trusting either field or resolving a pathname.
        guard try hasLinkedParentEntry(descriptor: descriptor, facts: facts, label: label) else {
            throw RunEpochAuthorityError.directoryUnavailable(label, "directory no longer has a linked parent entry")
        }
        let copy = openat(descriptor, ".", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard copy >= 0, let stream = fdopendir(copy) else {
            if copy >= 0 { close(copy) }
            throw RunEpochAuthorityError.directoryUnavailable(label, "descriptor enumeration failed")
        }
        defer { closedir(stream) }
        var floor: UInt64 = 0
        errno = 0
        while let entry = readdir(stream) {
            let name = withUnsafePointer(to: &entry.pointee.d_name) { pointer in
                pointer.withMemoryRebound(to: CChar.self, capacity: Int(MAXNAMLEN) + 1) { String(cString: $0) }
            }
            guard name.hasPrefix("state-"), name.hasSuffix(".json") else { continue }
            let stem = name.dropLast(".json".count)
            guard let separator = stem.lastIndex(of: "-"), let epoch = UInt64(stem[stem.index(after: separator)...]) else { continue }
            floor = max(floor, epoch)
        }
        guard errno == 0 else { throw RunEpochAuthorityError.directoryUnavailable(label, "descriptor enumeration error") }
        return floor
    }

    private static func hasLinkedParentEntry(descriptor: Int32, facts: stat, label: URL) throws -> Bool {
        let parent = openat(descriptor, "..", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard parent >= 0, let stream = fdopendir(parent) else {
            if parent >= 0 { close(parent) }
            throw RunEpochAuthorityError.directoryUnavailable(label, "parent descriptor unavailable")
        }
        defer { closedir(stream) }
        while true {
            errno = 0
            guard let entry = readdir(stream) else {
                guard errno == 0 else { throw RunEpochAuthorityError.directoryUnavailable(label, "parent enumeration failed") }
                return false
            }
            let name = withUnsafePointer(to: &entry.pointee.d_name) { pointer in
                pointer.withMemoryRebound(to: CChar.self, capacity: Int(MAXNAMLEN) + 1) { String(cString: $0) }
            }
            guard name != ".", name != ".." else { continue }
            var child = stat()
            if fstatat(parent, name, &child, AT_SYMLINK_NOFOLLOW) == 0,
               child.st_mode & S_IFMT == S_IFDIR, child.st_dev == facts.st_dev, child.st_ino == facts.st_ino {
                return true
            }
        }
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
