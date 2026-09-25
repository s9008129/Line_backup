import CryptoKit
import Foundation
import ImageIO

public enum StagingOutcome: String, Codable, Sendable {
    case duplicateContentConfirmed = "DUPLICATE_CONTENT_CONFIRMED"
    case stagingIncomplete = "STAGING_INCOMPLETE"
    case stagingExtraFiles = "STAGING_EXTRA_FILES"
    case stagingDuplicateContent = "STAGING_DUPLICATE_CONTENT"
    case stagingUnstable = "STAGING_UNSTABLE"
    case contentMismatchAgainstAcceptedBaseline = "CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE"
}

public struct StagingPolicy: Equatable, Codable, Sendable {
    public let expectedFileCount: Int
    public let expectedTotalBytes: UInt64
    public let expectedContentMultisetSHA256: String
    public let partialSuffixes: [String]

    public init(
        expectedFileCount: Int,
        expectedTotalBytes: UInt64,
        expectedContentMultisetSHA256: String,
        partialSuffixes: [String] = [".part", ".partial", ".tmp", ".temp", ".download", ".crdownload", ".incomplete", ".filepart"]
    ) {
        self.expectedFileCount = expectedFileCount
        self.expectedTotalBytes = expectedTotalBytes
        self.expectedContentMultisetSHA256 = expectedContentMultisetSHA256
        self.partialSuffixes = partialSuffixes
    }

    public static let rev28Accepted = StagingPolicy(
        expectedFileCount: 57,
        expectedTotalBytes: 17_924_900,
        expectedContentMultisetSHA256: "ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf"
    )
}

public struct StagingFileRecord: Equatable, Codable, Sendable {
    public let name: String
    public let size: UInt64
    public let modificationTime: TimeInterval
    public let sha256: String
    public let decodable: Bool

    public init(name: String, size: UInt64, modificationTime: TimeInterval, sha256: String, decodable: Bool) {
        self.name = name
        self.size = size
        self.modificationTime = modificationTime
        self.sha256 = sha256
        self.decodable = decodable
    }
}

public struct StagingSnapshot: Equatable, Codable, Sendable {
    public let observedAt: TimeInterval
    public let files: [StagingFileRecord]
    public let subdirectories: [String]

    public init(observedAt: TimeInterval, files: [StagingFileRecord], subdirectories: [String] = []) {
        self.observedAt = observedAt
        self.files = files
        self.subdirectories = subdirectories
    }

    public var totalBytes: UInt64 { files.reduce(0) { $0 + $1.size } }
}

public struct StagingVerification: Equatable, Codable, Sendable {
    public let outcome: StagingOutcome
    public let fileCount: Int
    public let totalBytes: UInt64
    public let contentMultisetSHA256: String?
    public let detail: String
}

public enum StagingVerifier {
    public static func contentMultisetDigest(_ hashes: [String]) -> String {
        let joined = hashes.sorted().joined(separator: "\n")
        return SHA256.hash(data: Data(joined.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    public static func verifyStableSnapshots(
        _ snapshots: [StagingSnapshot],
        policy: StagingPolicy = .rev28Accepted,
        minimumSamples: Int = 3,
        minimumSpanSeconds: Double = 4,
        quiescenceSeconds: Double = 5
    ) -> StagingVerification {
        guard let last = snapshots.last else {
            return StagingVerification(
                outcome: .stagingUnstable,
                fileCount: 0,
                totalBytes: 0,
                contentMultisetSHA256: nil,
                detail: "no staging samples"
            )
        }
        guard isStable(
            snapshots: snapshots,
            minimumSamples: minimumSamples,
            minimumSpanSeconds: minimumSpanSeconds,
            quiescenceSeconds: quiescenceSeconds
        ) else {
            return result(.stagingUnstable, last, nil, "size/mtime samples not yet stable and quiescent")
        }
        return verify(snapshot: last, policy: policy)
    }

    public static func verify(snapshot: StagingSnapshot, policy: StagingPolicy = .rev28Accepted) -> StagingVerification {
        let partials = snapshot.files.filter { file in
            let lower = file.name.lowercased()
            return policy.partialSuffixes.contains { lower.hasSuffix($0) }
        }
        let zero = snapshot.files.filter { $0.size == 0 }
        let undecodable = snapshot.files.filter { !$0.decodable }

        if !snapshot.subdirectories.isEmpty || snapshot.files.count > policy.expectedFileCount {
            return result(.stagingExtraFiles, snapshot, nil, "subdirs=\(snapshot.subdirectories.count) count=\(snapshot.files.count)")
        }
        if snapshot.files.count < policy.expectedFileCount || !partials.isEmpty || !zero.isEmpty || !undecodable.isEmpty {
            return result(.stagingIncomplete, snapshot, nil, "count=\(snapshot.files.count) partial=\(partials.count) zero=\(zero.count) undecodable=\(undecodable.count)")
        }

        let hashes = snapshot.files.map(\.sha256)
        if Set(hashes).count != hashes.count {
            return result(.stagingDuplicateContent, snapshot, contentMultisetDigest(hashes), "duplicate SHA-256 values inside staging")
        }

        let digest = contentMultisetDigest(hashes)
        guard snapshot.totalBytes == policy.expectedTotalBytes,
              digest == policy.expectedContentMultisetSHA256 else {
            return result(.contentMismatchAgainstAcceptedBaseline, snapshot, digest, "bytes=\(snapshot.totalBytes) expectedBytes=\(policy.expectedTotalBytes) digest=\(digest)")
        }

        return result(.duplicateContentConfirmed, snapshot, digest, "exact count/bytes/decodability/content multiset match")
    }

    public static func isStable(
        snapshots: [StagingSnapshot],
        minimumSamples: Int = 3,
        minimumSpanSeconds: Double = 4,
        quiescenceSeconds: Double = 5
    ) -> Bool {
        guard snapshots.count >= minimumSamples,
              let first = snapshots.first,
              let last = snapshots.last,
              last.observedAt - first.observedAt >= minimumSpanSeconds else { return false }
        struct FileStabilitySignature: Equatable {
            let name: String
            let size: UInt64
            let modificationTime: TimeInterval
        }
        let signature: (StagingSnapshot) -> [FileStabilitySignature] = {
            $0.files.sorted { $0.name < $1.name }.map {
                FileStabilitySignature(name: $0.name, size: $0.size, modificationTime: $0.modificationTime)
            }
        }
        let lastSig = signature(last)
        guard snapshots.suffix(minimumSamples).allSatisfy({ signature($0) == lastSig }) else { return false }
        let latestMtime = last.files.map(\.modificationTime).max() ?? 0
        return last.observedAt - latestMtime >= quiescenceSeconds
    }

    public static func snapshot(directory: URL, observedAt: TimeInterval = Date().timeIntervalSince1970) throws -> StagingSnapshot {
        let fm = FileManager.default
        let urls = try fm.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: [.isDirectoryKey, .fileSizeKey, .contentModificationDateKey],
            options: [.skipsHiddenFiles]
        )
        var files: [StagingFileRecord] = []
        var subdirs: [String] = []
        for url in urls {
            let values = try url.resourceValues(forKeys: [.isDirectoryKey, .fileSizeKey, .contentModificationDateKey])
            if values.isDirectory == true {
                subdirs.append(url.lastPathComponent)
                continue
            }
            let data = try Data(contentsOf: url, options: [.mappedIfSafe])
            let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
            let source = CGImageSourceCreateWithURL(url as CFURL, nil)
            let decodable = source.flatMap { CGImageSourceCreateImageAtIndex($0, 0, nil) } != nil
            files.append(StagingFileRecord(
                name: url.lastPathComponent,
                size: UInt64(values.fileSize ?? data.count),
                modificationTime: values.contentModificationDate?.timeIntervalSince1970 ?? 0,
                sha256: digest,
                decodable: decodable
            ))
        }
        return StagingSnapshot(observedAt: observedAt, files: files, subdirectories: subdirs.sorted())
    }

    private static func result(_ outcome: StagingOutcome, _ snapshot: StagingSnapshot, _ digest: String?, _ detail: String) -> StagingVerification {
        StagingVerification(outcome: outcome, fileCount: snapshot.files.count, totalBytes: snapshot.totalBytes, contentMultisetSHA256: digest, detail: detail)
    }
}
