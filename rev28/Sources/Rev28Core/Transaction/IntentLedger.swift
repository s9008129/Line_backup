import CryptoKit
import Darwin
import Foundation

// MARK: - Append-only JSONL ledger with hash chaining (plan §ARCHITECTURE §13)
//
// One entry per observation/decision/dispatch/intent; intent records precede
// irreversible actions; every artifact is named by path + SHA-256. No implicit
// state across restarts: a resumed process enters read-only "observe" mode and
// never re-dispatches an irreversible action without a fresh reviewed decision.

public struct LedgerEntry: Equatable, Codable, Sendable {
    public let seq: Int
    public let kind: String
    public let atISO8601: String
    public let payload: [String: String]
    public let prev: String?
    public let selfHash: String

    public init(seq: Int, kind: String, atISO8601: String, payload: [String: String], prev: String?, selfHash: String) {
        self.seq = seq
        self.kind = kind
        self.atISO8601 = atISO8601
        self.payload = payload
        self.prev = prev
        self.selfHash = selfHash
    }
}

public enum IntentLedgerError: Error, CustomStringConvertible {
    case chainBroken(seq: Int, expectedPrev: String?, foundPrev: String?)
    case hashMismatch(seq: Int)
    case malformedLine(lineNumber: Int)
    case fileChangedSinceLoad
    case ioFailure(String)

    public var description: String {
        switch self {
        case let .chainBroken(seq, expected, found):
            return "chainBroken(seq=\(seq), expectedPrev=\(expected ?? "nil"), foundPrev=\(found ?? "nil"))"
        case let .hashMismatch(seq):
            return "hashMismatch(seq=\(seq))"
        case let .malformedLine(lineNumber):
            return "malformedLine(\(lineNumber))"
        case .fileChangedSinceLoad:
            return "fileChangedSinceLoad"
        case let .ioFailure(reason):
            return "ioFailure(\(reason))"
        }
    }
}

public final class IntentLedger {
    public let fileURL: URL
    public private(set) var entries: [LedgerEntry]
    private var loadedFileDigest: String?
    private var loadedByteCount: Int
    private let appendLock = NSLock()

    public init(fileURL: URL) throws {
        self.fileURL = fileURL
        let fm = FileManager.default
        try fm.createDirectory(at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        if fm.fileExists(atPath: fileURL.path) {
            let data = try Data(contentsOf: fileURL)
            self.loadedFileDigest = EvidenceIO.sha256Hex(data)
            self.loadedByteCount = data.count
            self.entries = try Self.decodeAndVerify(data)
        } else {
            self.loadedFileDigest = nil
            self.loadedByteCount = 0
            self.entries = []
        }
    }

    public static func computeSelfHash(
        seq: Int,
        kind: String,
        atISO8601: String,
        payload: [String: String],
        prev: String?
    ) -> String {
        var canonical = "{\"seq\":\(seq),\"kind\":\(quoted(kind)),\"at\":\(quoted(atISO8601)),\"payload\":{"
        let keys = payload.keys.sorted()
        canonical += keys.map { "\(quoted($0)):\(quoted(payload[$0] ?? ""))" }.joined(separator: ",")
        canonical += "},\"prev\":"
        canonical += prev.map(quoted) ?? "null"
        canonical += "}"
        return EvidenceIO.sha256Hex(Data(canonical.utf8))
    }

    private static func quoted(_ value: String) -> String {
        let escaped = value
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: "\\n")
        return "\"\(escaped)\""
    }

    public static func verify(entries: [LedgerEntry]) throws {
        var previousHash: String?
        for (index, entry) in entries.enumerated() {
            let expectedSeq = index + 1
            guard entry.seq == expectedSeq else {
                throw IntentLedgerError.chainBroken(seq: entry.seq, expectedPrev: "\(expectedSeq)", foundPrev: "\(entry.seq)")
            }
            guard entry.prev == previousHash else {
                throw IntentLedgerError.chainBroken(seq: entry.seq, expectedPrev: previousHash, foundPrev: entry.prev)
            }
            let recomputed = computeSelfHash(
                seq: entry.seq,
                kind: entry.kind,
                atISO8601: entry.atISO8601,
                payload: entry.payload,
                prev: entry.prev
            )
            guard recomputed == entry.selfHash else {
                throw IntentLedgerError.hashMismatch(seq: entry.seq)
            }
            previousHash = entry.selfHash
        }
    }

    public var headHash: String? { entries.last?.selfHash }

    @discardableResult
    public func append(kind: String, payload: [String: String] = [:], at date: Date = Date(), fsync: Bool = true) throws -> LedgerEntry {
        appendLock.lock()
        defer { appendLock.unlock() }
        _ = fsync // Retained for source compatibility; durability is mandatory.
        let lockURL = fileURL.appendingPathExtension("lock")
        let lockFD = open(lockURL.path, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        guard lockFD >= 0 else { throw IntentLedgerError.ioFailure("cannot open ledger lock: \(String(cString: strerror(errno)))") }
        defer { _ = flock(lockFD, LOCK_UN); _ = close(lockFD) }
        guard flock(lockFD, LOCK_EX) == 0 else { throw IntentLedgerError.ioFailure("cannot lock ledger: \(String(cString: strerror(errno)))") }

        let data = (try? Data(contentsOf: fileURL)) ?? Data()
        let expectedDigest = loadedFileDigest ?? EvidenceIO.sha256Hex(Data())
        guard EvidenceIO.sha256Hex(data) == expectedDigest else {
            throw IntentLedgerError.fileChangedSinceLoad
        }
        let diskEntries = try Self.decodeAndVerify(data)
        guard diskEntries == entries else { throw IntentLedgerError.fileChangedSinceLoad }

        let seq = (diskEntries.last?.seq ?? 0) + 1
        let atISO8601 = EvidenceIO.iso8601(date)
        let prev = diskEntries.last?.selfHash
        let selfHash = Self.computeSelfHash(seq: seq, kind: kind, atISO8601: atISO8601, payload: payload, prev: prev)
        let entry = LedgerEntry(seq: seq, kind: kind, atISO8601: atISO8601, payload: payload, prev: prev, selfHash: selfHash)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let line = try encoder.encode(entry)

        do {
            let fd = open(fileURL.path, O_CREAT | O_WRONLY | O_APPEND, S_IRUSR | S_IWUSR)
            guard fd >= 0 else { throw IntentLedgerError.ioFailure("cannot open ledger: \(String(cString: strerror(errno)))") }
            defer { _ = close(fd) }
            let bytes = Array(line + Data("\n".utf8))
            var offset = 0
            while offset < bytes.count {
                let written = bytes.withUnsafeBytes { buffer in
                    write(fd, buffer.baseAddress!.advanced(by: offset), bytes.count - offset)
                }
                guard written > 0 else { throw IntentLedgerError.ioFailure("ledger write failed: \(String(cString: strerror(errno)))") }
                offset += written
            }
            if Darwin.fsync(fd) != 0 {
                throw IntentLedgerError.ioFailure("ledger fsync failed: \(String(cString: strerror(errno)))")
            }
        } catch {
            if let ledgerError = error as? IntentLedgerError { throw ledgerError }
            throw IntentLedgerError.ioFailure(String(describing: error))
        }
        entries.append(entry)
        let newData = try Data(contentsOf: fileURL)
        loadedFileDigest = EvidenceIO.sha256Hex(newData)
        loadedByteCount = newData.count
        return entry
    }

    private static func decodeAndVerify(_ data: Data) throws -> [LedgerEntry] {
        if data.isEmpty { return [] }
        guard data.last == 10 else {
            throw IntentLedgerError.malformedLine(lineNumber: data.filter { $0 == 10 }.count + 1)
        }
        let text = String(decoding: data, as: UTF8.self)
        var parsed: [LedgerEntry] = []
        for (index, line) in text.split(separator: "\n", omittingEmptySubsequences: true).enumerated() {
            guard let lineData = line.data(using: .utf8),
                  let entry = try? JSONDecoder().decode(LedgerEntry.self, from: lineData) else {
                throw IntentLedgerError.malformedLine(lineNumber: index + 1)
            }
            parsed.append(entry)
        }
        try verify(entries: parsed)
        return parsed
    }

    /// Writes an independently stored, fsynced anchor for the current verified head.
    public func writeHeadAnchor(to url: URL) throws {
        try Self.verify(entries: entries)
        let anchor = LedgerHeadAnchor(byteCount: loadedByteCount, fileSHA256: loadedFileDigest ?? EvidenceIO.sha256Hex(Data()), headHash: headHash)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        try encoder.encode(anchor).write(to: url, options: .atomic)
        let fd = open(url.path, O_RDONLY)
        guard fd >= 0 else { throw IntentLedgerError.ioFailure("cannot open anchor for fsync") }
        defer { _ = close(fd) }
        guard Darwin.fsync(fd) == 0 else { throw IntentLedgerError.ioFailure("anchor fsync failed") }
        let directoryFD = open(url.deletingLastPathComponent().path, O_RDONLY | O_DIRECTORY)
        guard directoryFD >= 0 else { throw IntentLedgerError.ioFailure("cannot open anchor directory for fsync") }
        defer { _ = close(directoryFD) }
        guard Darwin.fsync(directoryFD) == 0 else { throw IntentLedgerError.ioFailure("anchor directory fsync failed") }
    }

    public static func verifyHeadAnchor(fileURL: URL, anchorURL: URL) throws -> LedgerHeadAnchor {
        let anchor = try JSONDecoder().decode(LedgerHeadAnchor.self, from: Data(contentsOf: anchorURL))
        let data = try Data(contentsOf: fileURL)
        guard data.count == anchor.byteCount, EvidenceIO.sha256Hex(data) == anchor.fileSHA256 else {
            throw IntentLedgerError.fileChangedSinceLoad
        }
        let parsed = try decodeAndVerify(data)
        guard parsed.last?.selfHash == anchor.headHash else { throw IntentLedgerError.fileChangedSinceLoad }
        return anchor
    }

    /// Detects concurrent modification of the ledger file since load.
    public func verifyFileUnchangedSinceLoad() throws {
        let data = try Data(contentsOf: fileURL)
        guard data.count >= loadedByteCount else { throw IntentLedgerError.fileChangedSinceLoad }
        let prefix = data.prefix(loadedByteCount)
        let prefixDigest = EvidenceIO.sha256Hex(Data(prefix))
        if let expected = loadedFileDigest {
            guard prefixDigest == expected else { throw IntentLedgerError.fileChangedSinceLoad }
        } else if loadedByteCount > 0 {
            throw IntentLedgerError.fileChangedSinceLoad
        }
    }

    public func count(kind: String) -> Int {
        entries.filter { $0.kind == kind }.count
    }
}

public struct LedgerHeadAnchor: Equatable, Codable, Sendable {
    public let byteCount: Int
    public let fileSHA256: String
    public let headHash: String?

    public init(byteCount: Int, fileSHA256: String, headHash: String?) {
        self.byteCount = byteCount
        self.fileSHA256 = fileSHA256
        self.headHash = headHash
    }
}

// MARK: - Crash-resume policy (S-01: crash resume is observe-only)

public struct ResumeDecision: Equatable, Codable, Sendable {
    public let mode: String
    public let irreversibleDispatchCount: Int
    public let allowedNewIrreversibleDispatches: Int
    public let reason: String

    public init(mode: String, irreversibleDispatchCount: Int, allowedNewIrreversibleDispatches: Int, reason: String) {
        self.mode = mode
        self.irreversibleDispatchCount = irreversibleDispatchCount
        self.allowedNewIrreversibleDispatches = allowedNewIrreversibleDispatches
        self.reason = reason
    }
}

public enum LedgerResume {
    public static let irreversibleKinds: Set<String> = ["dispatch.irreversible", "dispatch.saveAll"]
    public static let freshReviewedDecisionKind = "decision.freshReviewed"

    public static func irreversibleDispatchCount(in entries: [LedgerEntry]) -> Int {
        entries.filter { irreversibleKinds.contains($0.kind) }.count
    }

    /// A resumed process is always observe-only for irreversible operations.
    /// A review record may explain a future *new run*, but it can never re-arm
    /// the already-authorized Save All or destination confirmation in this ledger.
    public static func decide(entries: [LedgerEntry]) -> ResumeDecision {
        let dispatchCount = irreversibleDispatchCount(in: entries)
        return ResumeDecision(
            mode: "observeOnly",
            irreversibleDispatchCount: dispatchCount,
            allowedNewIrreversibleDispatches: 0,
            reason: "crash resume is permanently observe-only for irreversible operations in the same run"
        )
    }

    public static func wouldRefuseNewIrreversibleDispatch(entries: [LedgerEntry]) -> Bool {
        decide(entries: entries).allowedNewIrreversibleDispatches == 0
    }
}


// MARK: - Save All empirical risk-class record (plan §ARCHITECTURE §9)

public enum SaveAllEmpiricalClassification: String, Codable, Sendable {
    case preSideEffectObserved = "PRE_SIDE_EFFECT_OBSERVED"
    case irreversibleOrIndeterminate = "IRREVERSIBLE_OR_INDETERMINATE"
}

public struct BoundEvidenceDigest: Equatable, Sendable {
    public let runID: String
    public let runDirectory: URL
    public let fileURL: URL
    public let sha256: String

    private init(runID: String, runDirectory: URL, fileURL: URL, sha256: String) {
        self.runID = runID
        self.runDirectory = runDirectory
        self.fileURL = fileURL
        self.sha256 = sha256
    }

    public static func load(fileURL: URL, withinRunDirectory: URL, runID: String) throws -> BoundEvidenceDigest {
        let root = withinRunDirectory.resolvingSymlinksInPath().standardizedFileURL
        let file = fileURL.resolvingSymlinksInPath().standardizedFileURL
        let rootPath = root.path.hasSuffix("/") ? root.path : root.path + "/"
        guard !runID.isEmpty, root.lastPathComponent == runID, file.path.hasPrefix(rootPath) else {
            throw IntentLedgerError.ioFailure("evidence artifact is not bound beneath the authorized run directory")
        }
        let data = try Data(contentsOf: file)
        return BoundEvidenceDigest(runID: runID, runDirectory: root, fileURL: file, sha256: EvidenceIO.sha256Hex(data))
    }

    func decode<T: Decodable>(_ type: T.Type) throws -> T {
        try JSONDecoder().decode(type, from: Data(contentsOf: fileURL))
    }
}

public struct PostconditionEvidenceArtifact: Codable, Equatable, Sendable {
    public let runID: String
    public let outcome: String
    public let chooserAffirmation: ChooserAffirmation?

    public init(runID: String, outcome: String, chooserAffirmation: ChooserAffirmation?) {
        self.runID = runID
        self.outcome = outcome
        self.chooserAffirmation = chooserAffirmation
    }
}

public struct TripwireEvidenceArtifact: Codable, Equatable, Sendable {
    public let runID: String
    public let observations: [TripwireEvidenceFact]
    /// A post-dispatch dropped-event/rescan gap or collector failure is
    /// disclosed here; a gapped window is never a clean tripwire (plan C7).
    public let collectionGap: String?

    public init(runID: String, observations: [TripwireEvidenceFact], collectionGap: String? = nil) {
        self.runID = runID
        self.observations = observations
        self.collectionGap = collectionGap
    }

    public var preChooserAttributableWriteObserved: Bool {
        observations.contains { $0.occurredBeforeChooser && $0.isWrite && $0.attributableToThisRun }
    }
}

public struct TripwireEvidenceFact: Codable, Equatable, Sendable {
    public let occurredBeforeChooser: Bool
    public let isWrite: Bool
    public let attributableToThisRun: Bool
    public let aborts: Bool

    public init(occurredBeforeChooser: Bool, isWrite: Bool, attributableToThisRun: Bool, aborts: Bool) {
        self.occurredBeforeChooser = occurredBeforeChooser
        self.isWrite = isWrite
        self.attributableToThisRun = attributableToThisRun
        self.aborts = aborts
    }
}

public struct SaveAllEmpiricalClassRecord: Equatable, Codable, Sendable {
    public let classification: SaveAllEmpiricalClassification
    public let postconditionOutcome: String
    public let chooserAffirmed: Bool
    public let attributableFilesystemWriteObservedBeforeChooser: Bool
    public let postconditionEvidenceSHA256: String
    public let tripwireEvidenceSHA256: String
    public let evidenceRunID: String?
    public let evidenceDigestsValidated: Bool
    public let evidenceRunDirectory: String?
    public let postconditionEvidencePath: String?
    public let tripwireEvidencePath: String?

    init(
        classification: SaveAllEmpiricalClassification,
        postconditionOutcome: String,
        chooserAffirmed: Bool,
        attributableFilesystemWriteObservedBeforeChooser: Bool,
        postconditionEvidenceSHA256: String,
        tripwireEvidenceSHA256: String,
        evidenceRunID: String? = nil,
        evidenceDigestsValidated: Bool = false,
        evidenceRunDirectory: String? = nil,
        postconditionEvidencePath: String? = nil,
        tripwireEvidencePath: String? = nil
    ) {
        self.classification = classification
        self.postconditionOutcome = postconditionOutcome
        self.chooserAffirmed = chooserAffirmed
        self.attributableFilesystemWriteObservedBeforeChooser = attributableFilesystemWriteObservedBeforeChooser
        self.postconditionEvidenceSHA256 = postconditionEvidenceSHA256
        self.tripwireEvidenceSHA256 = tripwireEvidenceSHA256
        self.evidenceRunID = evidenceRunID
        self.evidenceDigestsValidated = evidenceDigestsValidated
        self.evidenceRunDirectory = evidenceRunDirectory
        self.postconditionEvidencePath = postconditionEvidencePath
        self.tripwireEvidencePath = tripwireEvidencePath
    }

    /// Conservative classification: Save All is eligible for a future
    /// PRE_SIDE_EFFECT review only when a chooser was affirmatively observed
    /// and there was no attributable filesystem write before that chooser.
    public static func derive(
        postconditionOutcome: String,
        chooserAffirmed: Bool,
        attributableFilesystemWriteObservedBeforeChooser: Bool,
        postconditionEvidenceSHA256: String,
        tripwireEvidenceSHA256: String
    ) -> SaveAllEmpiricalClassRecord {
        // Unbound strings/booleans are caller claims, not validated evidence.
        // The legacy entry point is retained for harness compatibility but can
        // never produce an affirmative empirical class.
        let classification: SaveAllEmpiricalClassification = .irreversibleOrIndeterminate
        return SaveAllEmpiricalClassRecord(
            classification: classification,
            postconditionOutcome: postconditionOutcome,
            chooserAffirmed: chooserAffirmed,
            attributableFilesystemWriteObservedBeforeChooser: attributableFilesystemWriteObservedBeforeChooser,
            postconditionEvidenceSHA256: postconditionEvidenceSHA256,
            tripwireEvidenceSHA256: tripwireEvidenceSHA256
        )
    }

    public static func deriveValidated(
        runID: String,
        postconditionEvidence: BoundEvidenceDigest,
        tripwireEvidence: BoundEvidenceDigest
    ) throws -> SaveAllEmpiricalClassRecord {
        let postcondition = try postconditionEvidence.decode(PostconditionEvidenceArtifact.self)
        let tripwire = try tripwireEvidence.decode(TripwireEvidenceArtifact.self)
        let postconditionOutcome = postcondition.outcome
        let chooserAffirmed = postcondition.chooserAffirmation != nil
        let attributableFilesystemWriteObservedBeforeChooser = tripwire.preChooserAttributableWriteObserved
        let validHash: (String) -> Bool = { value in
            value.count == 64 && value.allSatisfy { $0.isHexDigit } && Set(value).count > 1
        }
        let evidenceValid = !runID.isEmpty && postconditionEvidence.runID == runID
            && tripwireEvidence.runID == runID
            && postcondition.runID == runID && tripwire.runID == runID
            && postconditionEvidence.runDirectory == tripwireEvidence.runDirectory
            && validHash(postconditionEvidence.sha256) && validHash(tripwireEvidence.sha256)
        let affirmative = evidenceValid && chooserAffirmed
            && postconditionOutcome == "CHOOSER_VERIFIED"
            && postcondition.chooserAffirmation?.predicateID.isEmpty == false
            && !attributableFilesystemWriteObservedBeforeChooser
            && !tripwire.observations.contains(where: \.aborts)
        return SaveAllEmpiricalClassRecord(
            classification: affirmative ? .preSideEffectObserved : .irreversibleOrIndeterminate,
            postconditionOutcome: postconditionOutcome,
            chooserAffirmed: chooserAffirmed,
            attributableFilesystemWriteObservedBeforeChooser: attributableFilesystemWriteObservedBeforeChooser,
            postconditionEvidenceSHA256: postconditionEvidence.sha256,
            tripwireEvidenceSHA256: tripwireEvidence.sha256,
            evidenceRunID: evidenceValid ? runID : nil,
            evidenceDigestsValidated: evidenceValid,
            evidenceRunDirectory: evidenceValid ? postconditionEvidence.runDirectory.path : nil,
            postconditionEvidencePath: evidenceValid ? postconditionEvidence.fileURL.path : nil,
            tripwireEvidencePath: evidenceValid ? tripwireEvidence.fileURL.path : nil
        )
    }

    func append(to ledger: IntentLedger) throws {
        if classification == .preSideEffectObserved {
            let validHash: (String) -> Bool = { $0.count == 64 && $0.allSatisfy(\.isHexDigit) && Set($0).count > 1 }
            guard postconditionOutcome == "CHOOSER_VERIFIED", chooserAffirmed,
                  !attributableFilesystemWriteObservedBeforeChooser,
                  evidenceDigestsValidated, let evidenceRunID, !evidenceRunID.isEmpty,
                  validHash(postconditionEvidenceSHA256), validHash(tripwireEvidenceSHA256),
                  let evidenceRunDirectory, let postconditionEvidencePath, let tripwireEvidencePath else {
                throw IntentLedgerError.ioFailure("affirmative Save All class lacks validated bound evidence")
            }
            let root = URL(fileURLWithPath: evidenceRunDirectory)
            let post = try BoundEvidenceDigest.load(
                fileURL: URL(fileURLWithPath: postconditionEvidencePath), withinRunDirectory: root, runID: evidenceRunID
            )
            let tripwire = try BoundEvidenceDigest.load(
                fileURL: URL(fileURLWithPath: tripwireEvidencePath), withinRunDirectory: root, runID: evidenceRunID
            )
            guard post.sha256 == postconditionEvidenceSHA256, tripwire.sha256 == tripwireEvidenceSHA256 else {
                throw IntentLedgerError.ioFailure("Save All evidence changed after classification")
            }
            let postArtifact = try post.decode(PostconditionEvidenceArtifact.self)
            let tripwireArtifact = try tripwire.decode(TripwireEvidenceArtifact.self)
            guard postArtifact.runID == evidenceRunID, postArtifact.outcome == "CHOOSER_VERIFIED",
                  let affirmation = postArtifact.chooserAffirmation, !affirmation.predicateID.isEmpty,
                  tripwireArtifact.runID == evidenceRunID,
                  !tripwireArtifact.preChooserAttributableWriteObserved,
                  !tripwireArtifact.observations.contains(where: { $0.aborts }) else {
                throw IntentLedgerError.ioFailure("Save All artifacts contradict affirmative empirical classification")
            }
        }
        try ledger.append(kind: "saveAllEmpiricalClassRecord", payload: [
            "classification": classification.rawValue,
            "postconditionOutcome": postconditionOutcome,
            "chooserAffirmed": chooserAffirmed ? "1" : "0",
            "filesystemWriteBeforeChooser": attributableFilesystemWriteObservedBeforeChooser ? "1" : "0",
            "postconditionEvidenceSHA256": postconditionEvidenceSHA256,
            "tripwireEvidenceSHA256": tripwireEvidenceSHA256,
            "evidenceRunID": evidenceRunID ?? "",
            "evidenceDigestsValidated": evidenceDigestsValidated ? "1" : "0",
            "evidenceRunDirectory": evidenceRunDirectory ?? "",
            "postconditionEvidencePath": postconditionEvidencePath ?? "",
            "tripwireEvidencePath": tripwireEvidencePath ?? "",
        ])
    }
}
