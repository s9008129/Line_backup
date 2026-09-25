import CryptoKit
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
    private let loadedFileDigest: String?
    private let loadedByteCount: Int

    public init(fileURL: URL) throws {
        self.fileURL = fileURL
        let fm = FileManager.default
        try fm.createDirectory(at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        if fm.fileExists(atPath: fileURL.path) {
            let data = try Data(contentsOf: fileURL)
            self.loadedFileDigest = EvidenceIO.sha256Hex(data)
            self.loadedByteCount = data.count
            let text = String(decoding: data, as: UTF8.self)
            var parsed: [LedgerEntry] = []
            for (index, line) in text.split(separator: "\n", omittingEmptySubsequences: true).enumerated() {
                let decoder = JSONDecoder()
                guard let lineData = line.data(using: .utf8),
                      let entry = try? decoder.decode(LedgerEntry.self, from: lineData) else {
                    throw IntentLedgerError.malformedLine(lineNumber: index + 1)
                }
                parsed.append(entry)
            }
            self.entries = parsed
            try Self.verify(entries: parsed)
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
        let seq = (entries.last?.seq ?? 0) + 1
        let atISO8601 = EvidenceIO.iso8601(date)
        let prev = entries.last?.selfHash
        let selfHash = Self.computeSelfHash(seq: seq, kind: kind, atISO8601: atISO8601, payload: payload, prev: prev)
        let entry = LedgerEntry(seq: seq, kind: kind, atISO8601: atISO8601, payload: payload, prev: prev, selfHash: selfHash)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let line = try encoder.encode(entry)

        if !FileManager.default.fileExists(atPath: fileURL.path) {
            try Data().write(to: fileURL, options: .atomic)
        }
        do {
            let handle = try FileHandle(forWritingTo: fileURL)
            defer { try? handle.close() }
            try handle.seekToEnd()
            try handle.write(contentsOf: line + Data("\n".utf8))
            if fsync { try handle.synchronize() }
        } catch {
            throw IntentLedgerError.ioFailure(String(describing: error))
        }
        entries.append(entry)
        return entry
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

    /// A resumed process is observe-only. Re-arming an irreversible dispatch is
    /// allowed only by an explicit fresh reviewed decision recorded after the last
    /// irreversible dispatch (`payload["armIrreversible"] == "1"`).
    public static func decide(entries: [LedgerEntry]) -> ResumeDecision {
        let dispatchCount = irreversibleDispatchCount(in: entries)
        let lastDispatchSeq = entries.last(where: { irreversibleKinds.contains($0.kind) })?.seq ?? 0
        let freshReview = entries.last(where: {
            $0.kind == freshReviewedDecisionKind
                && $0.seq > lastDispatchSeq
                && $0.payload["armIrreversible"] == "1"
        })
        if freshReview != nil {
            return ResumeDecision(
                mode: "observeOnly",
                irreversibleDispatchCount: dispatchCount,
                allowedNewIrreversibleDispatches: 1,
                reason: "fresh reviewed decision recorded after the last irreversible dispatch"
            )
        }
        return ResumeDecision(
            mode: "observeOnly",
            irreversibleDispatchCount: dispatchCount,
            allowedNewIrreversibleDispatches: 0,
            reason: "crash resume is observe-only; no fresh reviewed decision arms another irreversible dispatch"
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

public struct SaveAllEmpiricalClassRecord: Equatable, Codable, Sendable {
    public let classification: SaveAllEmpiricalClassification
    public let postconditionOutcome: String
    public let chooserAffirmed: Bool
    public let attributableFilesystemWriteObservedBeforeChooser: Bool
    public let postconditionEvidenceSHA256: String
    public let tripwireEvidenceSHA256: String

    public init(
        classification: SaveAllEmpiricalClassification,
        postconditionOutcome: String,
        chooserAffirmed: Bool,
        attributableFilesystemWriteObservedBeforeChooser: Bool,
        postconditionEvidenceSHA256: String,
        tripwireEvidenceSHA256: String
    ) {
        self.classification = classification
        self.postconditionOutcome = postconditionOutcome
        self.chooserAffirmed = chooserAffirmed
        self.attributableFilesystemWriteObservedBeforeChooser = attributableFilesystemWriteObservedBeforeChooser
        self.postconditionEvidenceSHA256 = postconditionEvidenceSHA256
        self.tripwireEvidenceSHA256 = tripwireEvidenceSHA256
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
        let classification: SaveAllEmpiricalClassification =
            chooserAffirmed && !attributableFilesystemWriteObservedBeforeChooser
            ? .preSideEffectObserved
            : .irreversibleOrIndeterminate
        return SaveAllEmpiricalClassRecord(
            classification: classification,
            postconditionOutcome: postconditionOutcome,
            chooserAffirmed: chooserAffirmed,
            attributableFilesystemWriteObservedBeforeChooser: attributableFilesystemWriteObservedBeforeChooser,
            postconditionEvidenceSHA256: postconditionEvidenceSHA256,
            tripwireEvidenceSHA256: tripwireEvidenceSHA256
        )
    }

    public func append(to ledger: IntentLedger) throws {
        try ledger.append(kind: "saveAllEmpiricalClassRecord", payload: [
            "classification": classification.rawValue,
            "postconditionOutcome": postconditionOutcome,
            "chooserAffirmed": chooserAffirmed ? "1" : "0",
            "filesystemWriteBeforeChooser": attributableFilesystemWriteObservedBeforeChooser ? "1" : "0",
            "postconditionEvidenceSHA256": postconditionEvidenceSHA256,
            "tripwireEvidenceSHA256": tripwireEvidenceSHA256,
        ])
    }
}
