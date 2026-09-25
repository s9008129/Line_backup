import Foundation
import Rev28Core

// Per-run evidence directory. Append-only by construction: every run gets a new
// timestamped directory, and every record is written atomically and refuses to
// replace an existing file.

final class EvidenceRun {
    let runID: String
    let root: URL
    private var shaEntries: [(name: String, sha: String)] = []

    init(evidenceBase: URL, prefix: String = "HARNESS") throws {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        formatter.timeZone = TimeZone.current
        let stamp = formatter.string(from: Date())
        self.runID = "\(prefix)-\(stamp)"
        self.root = evidenceBase.appendingPathComponent("runs/\(runID)")
        try EvidenceIO.ensureDirectory(root)
        try EvidenceIO.ensureDirectory(itemsDir)
        try EvidenceIO.ensureDirectory(frozenDir)
        try EvidenceIO.ensureDirectory(fixturesDir)
        try EvidenceIO.ensureDirectory(logsDir)
    }

    var itemsDir: URL { root.appendingPathComponent("items") }
    var frozenDir: URL { root.appendingPathComponent("frozen") }
    var fixturesDir: URL { root.appendingPathComponent("fixtures") }
    var logsDir: URL { root.appendingPathComponent("logs") }

    /// Canonical frozen-artifact path required by the W2 contract:
    /// `evidence/<task>/harness/frozen/`. Every frozen artifact is written both
    /// to the run's own frozen/ dir and to this canonical dir (append-only:
    /// an existing canonical file is never rewritten).
    var canonicalFrozenDir: URL { root.deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("frozen") }

    func writeItemRecord<T: Encodable>(_ name: String, _ value: T) throws -> (path: String, sha: String) {
        let url = itemsDir.appendingPathComponent(name)
        let sha = try EvidenceIO.writeJSONAtomically(value, to: url)
        shaEntries.append((name, sha))
        return (url.path, sha)
    }

    func writeFrozen<T: Encodable>(_ name: String, _ value: T) throws -> (path: String, sha: String) {
        let url = frozenDir.appendingPathComponent(name)
        let sha = try EvidenceIO.writeJSONAtomically(value, to: url)
        shaEntries.append(("frozen/\(name)", sha))
        try EvidenceIO.ensureDirectory(canonicalFrozenDir)
        let canonicalURL = canonicalFrozenDir.appendingPathComponent(name)
        let canonicalSHA = try EvidenceIO.writeJSONAtomically(value, to: canonicalURL)
        shaEntries.append(("canonical-frozen/\(name)", canonicalSHA))
        return (canonicalURL.path, canonicalSHA)
    }

    /// Append-only canonical sha256sums file, unique per run.
    func writeCanonicalSHA256Sums() throws -> String {
        try EvidenceIO.ensureDirectory(canonicalFrozenDir)
        let sorted = shaEntries.filter { $0.name.hasPrefix("canonical-frozen/") }.sorted { $0.name < $1.name }
        let body = sorted.map { "\($0.sha)  \($0.name.replacingOccurrences(of: "canonical-frozen/", with: ""))" }.joined(separator: "\n") + "\n"
        let url = canonicalFrozenDir.appendingPathComponent("sha256sums-\(runID).txt")
        return try EvidenceIO.writeAtomically(Data(body.utf8), to: url, appendOnly: true)
    }

    func recordSHA(name: String, sha: String) {
        shaEntries.append((name, sha))
    }

    func writeSHA256Sums() throws -> String {
        let sorted = shaEntries.sorted { $0.name < $1.name }
        let body = sorted.map { "\($0.sha)  \($0.name)" }.joined(separator: "\n") + "\n"
        let url = root.appendingPathComponent("sha256sums.txt")
        return try EvidenceIO.writeAtomically(Data(body.utf8), to: url, appendOnly: false)
    }
}
