import CryptoKit
import Darwin
import Foundation

// MARK: - Persistent goal slot (plan R4 §C4)
//
// One durable slot per goal identity (goal/group/album/approved run path). The
// slot is deliberately independent of runID, ledger path, token filename and
// session, so none of those can re-arm an irreversible one-shot entitlement.
// A single writer holds an exclusive lock for the process lifetime; a second
// owner fails closed instead of racing.

public struct GoalSlotIdentity: Equatable, Codable, Sendable, CustomStringConvertible {
    public let goal: String
    public let group: String
    public let album: String
    public let stagingRunDirectory: String

    public init(goal: String, group: String, album: String, stagingRunDirectory: URL) {
        self.goal = goal
        self.group = group
        self.album = album
        self.stagingRunDirectory = stagingRunDirectory.resolvingSymlinksInPath().standardizedFileURL.path
    }

    public var description: String {
        "goal=\(goal) group=\(group) album=\(album) staging=\(stagingRunDirectory)"
    }

    /// Stable slot key: no runID, ledger path, token name or session component.
    public var key: String {
        var material = Data()
        for field in [goal, group, album, stagingRunDirectory] {
            material.append(Data(field.utf8))
            material.append(0)
        }
        return SHA256.hash(data: material).map { String(format: "%02x", $0) }.joined()
    }

    public func matches(_ authorization: ImmutableRunAuthorization) -> Bool {
        let runDirectory = URL(fileURLWithPath: authorization.stagingRunDirectory)
            .resolvingSymlinksInPath().standardizedFileURL.path
        return goal == authorization.goal
            && group == authorization.group
            && album == authorization.album
            && stagingRunDirectory == runDirectory
    }
}

public struct GoalSlotState: Equatable, Codable, Sendable {
    public let schemaVersion: Int
    public let identity: GoalSlotIdentity
    public var entitlementConsumed: Bool
    public var consumedAtISO8601: String?
    public var consumedByRunID: String?
    public var consumedByLedgerPath: String?

    public init(
        schemaVersion: Int = 1,
        identity: GoalSlotIdentity,
        entitlementConsumed: Bool = false,
        consumedAtISO8601: String? = nil,
        consumedByRunID: String? = nil,
        consumedByLedgerPath: String? = nil
    ) {
        self.schemaVersion = schemaVersion
        self.identity = identity
        self.entitlementConsumed = entitlementConsumed
        self.consumedAtISO8601 = consumedAtISO8601
        self.consumedByRunID = consumedByRunID
        self.consumedByLedgerPath = consumedByLedgerPath
    }
}

public enum GoalSlotError: Error, Equatable, CustomStringConvertible {
    case controlRootUnavailable(String)
    case alreadyLocked(String)
    case lockUnavailable(String)
    case slotStateCorrupt(String)
    case slotIdentityMismatch
    case entitlementAlreadyConsumed(String)
    case ioFailure(String)

    public var description: String {
        switch self {
        case let .controlRootUnavailable(path): return "controlRootUnavailable(\(path))"
        case let .alreadyLocked(detail): return "alreadyLocked(\(detail))"
        case let .lockUnavailable(detail): return "lockUnavailable(\(detail))"
        case let .slotStateCorrupt(detail): return "slotStateCorrupt(\(detail))"
        case .slotIdentityMismatch: return "slotIdentityMismatch"
        case let .entitlementAlreadyConsumed(detail): return "entitlementAlreadyConsumed(\(detail))"
        case let .ioFailure(detail): return "ioFailure(\(detail))"
        }
    }
}

public final class GoalSlot {
    public let identity: GoalSlotIdentity
    public let directoryURL: URL
    public let stateURL: URL
    private let lockURL: URL
    private var lockFD: Int32 = -1
    private let stateLock = NSLock()
    private var state: GoalSlotState

    public init(controlRoot: URL, identity: GoalSlotIdentity) throws {
        let root = controlRoot.resolvingSymlinksInPath().standardizedFileURL
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: root.path, isDirectory: &isDirectory), isDirectory.boolValue else {
            throw GoalSlotError.controlRootUnavailable(root.path)
        }
        self.identity = identity
        self.directoryURL = root.appendingPathComponent(identity.key, isDirectory: true)
        self.stateURL = directoryURL.appendingPathComponent("goal-slot.json")
        self.lockURL = directoryURL.appendingPathComponent("goal-slot.lock")
        self.state = GoalSlotState(identity: identity)
        try Self.ensureDirectoryAndFsyncParent(directoryURL)
        try acquireExclusiveLock()
        self.state = try loadOrInitializeState()
    }

    deinit {
        if lockFD >= 0 {
            _ = flock(lockFD, LOCK_UN)
            _ = close(lockFD)
        }
    }

    public var snapshot: GoalSlotState {
        stateLock.lock()
        defer { stateLock.unlock() }
        return state
    }

    public var entitlementConsumed: Bool {
        snapshot.entitlementConsumed
    }

    /// Durable, single-use consumption of the irreversible entitlement. Must be
    /// called before the ledger intent is appended: if the process dies between
    /// consumption and intent, the entitlement stays spent and the operation is
    /// fail-closed (never re-armed by a new ledger, runID, token or session).
    public func consumeEntitlement(ledgerFileURL: URL, runID: String) throws {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard !state.entitlementConsumed else {
            throw GoalSlotError.entitlementAlreadyConsumed(
                "consumed at \(state.consumedAtISO8601 ?? "?") by run \(state.consumedByRunID ?? "?")"
            )
        }
        var updated = state
        updated.entitlementConsumed = true
        updated.consumedAtISO8601 = EvidenceIO.iso8601()
        updated.consumedByRunID = runID
        updated.consumedByLedgerPath = ledgerFileURL.resolvingSymlinksInPath().standardizedFileURL.path
        try writeStateDurably(updated)
        state = updated
    }

    private func acquireExclusiveLock() throws {
        let fd = open(lockURL.path, O_CREAT | O_RDWR, 0o644)
        guard fd >= 0 else {
            throw GoalSlotError.lockUnavailable("open failed errno=\(errno)")
        }
        guard flock(fd, LOCK_EX | LOCK_NB) == 0 else {
            let holder = (try? String(contentsOf: lockURL, encoding: .utf8)) ?? ""
            _ = close(fd)
            throw GoalSlotError.alreadyLocked(holder.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        let holder = "pid=\(getpid()) acquired=\(EvidenceIO.iso8601())\n"
        _ = ftruncate(fd, 0)
        _ = lseek(fd, 0, SEEK_SET)
        FileHandle(fileDescriptor: fd, closeOnDealloc: false).write(Data(holder.utf8))
        _ = fsync(fd)
        lockFD = fd
    }

    private func loadOrInitializeState() throws -> GoalSlotState {
        let fm = FileManager.default
        if fm.fileExists(atPath: stateURL.path) {
            do {
                let decoded = try JSONDecoder().decode(GoalSlotState.self, from: Data(contentsOf: stateURL))
                guard decoded.identity == identity, decoded.schemaVersion == 1 else {
                    throw GoalSlotError.slotIdentityMismatch
                }
                return decoded
            } catch let error as GoalSlotError {
                throw error
            } catch {
                // Corrupt or unreadable slot state fails closed; it is never
                // regenerated from guesswork.
                throw GoalSlotError.slotStateCorrupt(String(describing: error))
            }
        }
        let initial = GoalSlotState(identity: identity)
        try writeStateDurably(initial)
        return initial
    }

    private func writeStateDurably(_ value: GoalSlotState) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        let data = try encoder.encode(value)
        let temp = directoryURL.appendingPathComponent(".goal-slot-tmp-\(UUID().uuidString)")
        do {
            try data.write(to: temp, options: .atomic)
            let fd = open(temp.path, O_RDONLY)
            guard fd >= 0 else { throw GoalSlotError.ioFailure("cannot open temporary slot state") }
            defer { _ = close(fd) }
            guard fsync(fd) == 0 else { throw GoalSlotError.ioFailure("slot state fsync failed") }
            if FileManager.default.fileExists(atPath: stateURL.path) {
                try FileManager.default.removeItem(at: stateURL)
            }
            try FileManager.default.moveItem(at: temp, to: stateURL)
            try Self.fsyncDirectory(directoryURL)
        } catch let error as GoalSlotError {
            try? FileManager.default.removeItem(at: temp)
            throw error
        } catch {
            try? FileManager.default.removeItem(at: temp)
            throw GoalSlotError.ioFailure(String(describing: error))
        }
    }

    private static func ensureDirectoryAndFsyncParent(_ url: URL) throws {
        let fm = FileManager.default
        if !fm.fileExists(atPath: url.path) {
            try fm.createDirectory(at: url, withIntermediateDirectories: true)
            try fsyncDirectory(url.deletingLastPathComponent())
        }
    }

    private static func fsyncDirectory(_ url: URL) throws {
        let fd = open(url.path, O_RDONLY | O_DIRECTORY)
        guard fd >= 0 else { throw GoalSlotError.ioFailure("cannot open directory \(url.path) for fsync") }
        defer { _ = close(fd) }
        guard fsync(fd) == 0 else { throw GoalSlotError.ioFailure("directory fsync failed for \(url.path)") }
    }
}
