import CryptoKit
import Foundation

// MARK: - Evidence plumbing (plan design rule: structured records, SHA-256,
// atomic temp+rename writes, append-only where the artifact is evidence).

public enum EvidenceIOError: Error, CustomStringConvertible {
    case alreadyExists(URL)
    case missingParent(URL)
    case writeFailed(URL, String)

    public var description: String {
        switch self {
        case let .alreadyExists(url): return "alreadyExists(\(url.path))"
        case let .missingParent(url): return "missingParent(\(url.path))"
        case let .writeFailed(url, reason): return "writeFailed(\(url.path), \(reason))"
        }
    }
}

public enum EvidenceIO {
    public static func iso8601(_ date: Date = Date()) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        formatter.timeZone = TimeZone.current
        return formatter.string(from: date)
    }

    public static func sha256Hex(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    public static func sha256Hex(ofFileAt url: URL) throws -> String {
        let data = try Data(contentsOf: url)
        return sha256Hex(data)
    }

    public static func ensureDirectory(_ url: URL) throws {
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
    }

    public static func jsonEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        return encoder
    }

    public static func encodeJSON<T: Encodable>(_ value: T) throws -> Data {
        try jsonEncoder().encode(value)
    }

    /// Atomic temp+rename. `appendOnly == true` refuses to replace an existing file.
    @discardableResult
    public static func writeAtomically(_ data: Data, to url: URL, appendOnly: Bool = true) throws -> String {
        let fm = FileManager.default
        let parent = url.deletingLastPathComponent()
        guard fm.fileExists(atPath: parent.path) else { throw EvidenceIOError.missingParent(parent) }
        if fm.fileExists(atPath: url.path), appendOnly {
            throw EvidenceIOError.alreadyExists(url)
        }
        let temp = parent.appendingPathComponent(".tmp-\(UUID().uuidString)-\(url.lastPathComponent)")
        do {
            try data.write(to: temp, options: .atomic)
            if fm.fileExists(atPath: url.path) {
                try fm.removeItem(at: url)
            }
            try fm.moveItem(at: temp, to: url)
        } catch {
            try? fm.removeItem(at: temp)
            throw EvidenceIOError.writeFailed(url, String(describing: error))
        }
        return sha256Hex(data)
    }

    /// Writes a JSON record and returns its SHA-256.
    @discardableResult
    public static func writeJSONAtomically<T: Encodable>(
        _ value: T,
        to url: URL,
        appendOnly: Bool = true
    ) throws -> String {
        let data = try encodeJSON(value)
        return try writeAtomically(data, to: url, appendOnly: appendOnly)
    }

    /// Appends one line to a log file (created if needed) and flushes to disk.
    public static func appendLine(_ line: String, to url: URL) throws {
        let fm = FileManager.default
        let parent = url.deletingLastPathComponent()
        guard fm.fileExists(atPath: parent.path) else { throw EvidenceIOError.missingParent(parent) }
        let payload = Data((line + "\n").utf8)
        if !fm.fileExists(atPath: url.path) {
            try payload.write(to: url, options: .atomic)
            return
        }
        let handle = try FileHandle(forWritingTo: url)
        defer { try? handle.close() }
        try handle.seekToEnd()
        try handle.write(contentsOf: payload)
        try handle.synchronize()
    }
}

// MARK: - Line protocol (newline-delimited JSON over stdio) used by the
// synthetic harness, the separate-process occluder helper, and the driver.

public final class LineReader {
    private let handle: FileHandle
    private let onLine: (String) -> Void
    private let queue: DispatchQueue
    private var buffer = Data()
    private var finished = false

    public init(handle: FileHandle, label: String, onLine: @escaping (String) -> Void) {
        self.handle = handle
        self.onLine = onLine
        self.queue = DispatchQueue(label: label)
    }

    public func start() {
        // Deliberate strong self-capture: callers create LineReader inline
        // (`LineReader(...).start()`), so nothing else retains it. The
        // FileHandle -> handler -> LineReader cycle keeps the reader alive for
        // as long as the stream is open, and is broken on EOF below.
        handle.readabilityHandler = { [self] fileHandle in
            let data = fileHandle.availableData
            self.queue.async {
                guard !self.finished else { return }
                if data.isEmpty {
                    self.finished = true
                    self.handle.readabilityHandler = nil
                    return
                }
                self.buffer.append(data)
                let newline = Data([0x0A])
                while let range = self.buffer.range(of: newline) {
                    let lineData = self.buffer.subdata(in: self.buffer.startIndex..<range.lowerBound)
                    self.buffer.removeSubrange(self.buffer.startIndex..<range.upperBound)
                    guard let line = String(data: lineData, encoding: .utf8) else { continue }
                    self.onLine(line)
                }
            }
        }
    }
}

public enum LineProtocol {
    public static func jsonString(_ object: [String: Any]) -> String? {
        guard JSONSerialization.isValidJSONObject(object),
              let data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]) else {
            return nil
        }
        return String(data: data, encoding: .utf8)
    }

    public static func writeJSONObject(_ object: [String: Any], to handle: FileHandle) {
        guard let string = jsonString(object) else { return }
        if let data = (string + "\n").data(using: .utf8) {
            try? handle.write(contentsOf: data)
        }
    }

    public static func decodeObject(_ line: String) -> [String: Any]? {
        guard let data = line.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: data),
              let dictionary = object as? [String: Any] else {
            return nil
        }
        return dictionary
    }
}
