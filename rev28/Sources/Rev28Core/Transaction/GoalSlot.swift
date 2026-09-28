import Darwin
import Foundation

/// Persistent single-writer slot that binds the Rev28 one-shot irreversible
/// entitlement to the stable goal identity (goal, group, album, approved
/// staging root). Choosing a new run ID, destination, ledger path, token
/// filename or session must reuse the same slot and can never recreate the
/// entitlement (R4 C4, "no budget reset").
public struct GoalSlotRecord: Equatable, Codable, Sendable {
    public let goal: String
    public let group: String
    public let album: String
    public let stagingRoot: String
    public let stagingRunDirectory: String
    public let runID: String
    public let boundAtISO8601: String
    public let consumedAtISO8601: String?

    public init(
        goal: String,
        group: String,
        album: String,
        stagingRoot: String,
        stagingRunDirectory: String,
        runID: String,
        boundAtISO8601: String,
        consumedAtISO8601: String? = nil
    ) {
        self.goal = goal
        self.group = group
        self.album = album
        self.stagingRoot = stagingRoot
        self.stagingRunDirectory = stagingRunDirectory
        self.runID = runID
        self.boundAtISO8601 = boundAtISO8601
        self.consumedAtISO8601 = consumedAtISO8601
    }

    public var entitlementConsumed: Bool { consumedAtISO8601 != nil }
}

public enum GoalSlotError: Error, Equatable, CustomStringConvertible {
    case slotUnreadable(String)
    case goalSlotConflict(String)
    case entitlementAlreadyConsumed
    case ioFailure(String)

    public var description: String {
        switch self {
        case let .slotUnreadable(reason): return "slotUnreadable(\(reason))"
        case let .goalSlotConflict(detail): return "goalSlotConflict(\(detail))"
        case .entitlementAlreadyConsumed: return "entitlementAlreadyConsumed"
        case let .ioFailure(reason): return "ioFailure(\(reason))"
        }
    }
}

/// The slot lives at a stable location derived from the approved staging root
/// (never from a run ID or ledger path) and its file name is derived from the
/// goal identity, so no per-run choice can move or shadow it.
public enum GoalSlot {
    public static func canonicalDirectory(for authorization: ImmutableRunAuthorization) -> URL {
        URL(fileURLWithPath: authorization.stagingRoot)
            .deletingLastPathComponent()
            .appendingPathComponent("goal-slots", isDirectory: true)
    }

    public static func fileURL(in directory: URL, authorization: ImmutableRunAuthorization) -> URL {
        let key = [authorization.goal, authorization.group, authorization.album, authorization.stagingRoot]
            .joined(separator: "\u{0}")
        return directory.appendingPathComponent(EvidenceIO.sha256Hex(Data(key.utf8)) + ".goal-slot.json")
    }

    /// Creates the slot on first use. On later use the bound identity must match
    /// exactly; an existing slot is never regenerated or overwritten.
    @discardableResult
    public static func open(
        directory: URL,
        authorization: ImmutableRunAuthorization,
        now: Date = Date()
    ) throws -> GoalSlotRecord {
        try EvidenceIO.ensureDirectory(directory)
        let url = fileURL(in: directory, authorization: authorization)
        return try withLock(url) {
            if FileManager.default.fileExists(atPath: url.path) {
                return try verify(url: url, authorization: authorization)
            }
            let record = GoalSlotRecord(
                goal: authorization.goal,
                group: authorization.group,
                album: authorization.album,
                stagingRoot: authorization.stagingRoot,
                stagingRunDirectory: authorization.stagingRunDirectory,
                runID: authorization.runID,
                boundAtISO8601: EvidenceIO.iso8601(now)
            )
            try write(record, to: url)
            return record
        }
    }

    public static func load(
        directory: URL,
        authorization: ImmutableRunAuthorization
    ) throws -> GoalSlotRecord? {
        let url = fileURL(in: directory, authorization: authorization)
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        return try withLock(url) {
            try verify(url: url, authorization: authorization)
        }
    }

    /// Marks the one-shot entitlement consumed. Once consumed it stays consumed
    /// for this goal identity; there is no un-consume route.
    @discardableResult
    public static func consumeOneShotEntitlement(
        directory: URL,
        authorization: ImmutableRunAuthorization,
        now: Date = Date()
    ) throws -> GoalSlotRecord {
        try EvidenceIO.ensureDirectory(directory)
        let url = fileURL(in: directory, authorization: authorization)
        return try withLock(url) {
            guard FileManager.default.fileExists(atPath: url.path) else {
                throw GoalSlotError.slotUnreadable("goal slot missing at entitlement consumption")
            }
            let record = try verify(url: url, authorization: authorization)
            guard !record.entitlementConsumed else {
                throw GoalSlotError.entitlementAlreadyConsumed
            }
            let consumed = GoalSlotRecord(
                goal: record.goal,
                group: record.group,
                album: record.album,
                stagingRoot: record.stagingRoot,
                stagingRunDirectory: record.stagingRunDirectory,
                runID: record.runID,
                boundAtISO8601: record.boundAtISO8601,
                consumedAtISO8601: EvidenceIO.iso8601(now)
            )
            try write(consumed, to: url)
            return consumed
        }
    }

    // MARK: - Private

    private static func verify(url: URL, authorization: ImmutableRunAuthorization) throws -> GoalSlotRecord {
        guard let data = try? Data(contentsOf: url),
              let record = try? JSONDecoder().decode(GoalSlotRecord.self, from: data) else {
            throw GoalSlotError.slotUnreadable("goal slot at \(url.path) is unreadable")
        }
        let expected: [String: String] = [
            "goal": authorization.goal,
            "group": authorization.group,
            "album": authorization.album,
            "stagingRoot": authorization.stagingRoot,
            "stagingRunDirectory": authorization.stagingRunDirectory,
            "runID": authorization.runID,
        ]
        let observed: [String: String] = [
            "goal": record.goal,
            "group": record.group,
            "album": record.album,
            "stagingRoot": record.stagingRoot,
            "stagingRunDirectory": record.stagingRunDirectory,
            "runID": record.runID,
        ]
        let mismatches = expected.keys.sorted().filter { expected[$0] != observed[$0] }
        guard mismatches.isEmpty else {
            throw GoalSlotError.goalSlotConflict("bound identity mismatch: \(mismatches.joined(separator: ","))")
        }
        return record
    }

    /// Internal (not public) so the crash-window/atomicity tests can drive a
    /// repeated replace loop against a concurrent reader.
    static func write(_ record: GoalSlotRecord, to url: URL) throws {
        let parent = url.deletingLastPathComponent()
        let temp = parent.appendingPathComponent(".tmp-\(UUID().uuidString)-\(url.lastPathComponent)")
        do {
            let data = try EvidenceIO.encodeJSON(record)
            try data.write(to: temp, options: .atomic)
        } catch {
            throw GoalSlotError.ioFailure("cannot write goal slot temp file: \(error)")
        }
        let tempFD = Darwin.open(temp.path, O_RDONLY)
        guard tempFD >= 0 else { throw GoalSlotError.ioFailure("cannot open goal slot temp file for fsync") }
        guard fsync(tempFD) == 0 else {
            _ = close(tempFD)
            _ = try? FileManager.default.removeItem(at: temp)
            throw GoalSlotError.ioFailure("goal slot fsync failed")
        }
        _ = close(tempFD)
        // Atomic replace: rename(2) swaps the fsynced temp file over the
        // destination in one step, so a crash can never observe a missing or
        // partially written slot (the earlier remove+move sequence had a
        // window in which the slot did not exist).
        let installed = temp.path.withCString { source in
            url.path.withCString { destination in
                Darwin.rename(source, destination)
            }
        }
        guard installed == 0 else {
            let reason = String(cString: strerror(errno))
            _ = try? FileManager.default.removeItem(at: temp)
            throw GoalSlotError.ioFailure("cannot install goal slot atomically: \(reason)")
        }
        let directoryFD = Darwin.open(parent.path, O_RDONLY)
        guard directoryFD >= 0 else { throw GoalSlotError.ioFailure("cannot open goal-slot directory for fsync") }
        guard fsync(directoryFD) == 0 else {
            _ = close(directoryFD)
            throw GoalSlotError.ioFailure("goal-slot directory fsync failed")
        }
        _ = close(directoryFD)
    }

    private static func withLock<T>(_ url: URL, _ body: () throws -> T) throws -> T {
        let lockURL = URL(fileURLWithPath: url.path + ".lock")
        let lockFD = Darwin.open(lockURL.path, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        guard lockFD >= 0 else {
            throw GoalSlotError.ioFailure("cannot open goal-slot lock: \(String(cString: strerror(errno)))")
        }
        defer { _ = flock(lockFD, LOCK_UN); _ = close(lockFD) }
        guard flock(lockFD, LOCK_EX) == 0 else {
            throw GoalSlotError.ioFailure("cannot lock goal slot: \(String(cString: strerror(errno)))")
        }
        return try body()
    }
}
