import CryptoKit
import Darwin
import Foundation

public struct BaselineContentReference: Codable, Sendable {
    public let source_dir: String
    public let file_count: Int
    public let total_bytes: UInt64
    public let name_excluded_multiset_sha256_of_sorted_list: String
    public let unique_content_hashes: Int
    public let content_multiset: [String]
}

public enum BaselineVerificationError: Error, Equatable, CustomStringConvertible {
    case referenceDigestMismatch
    case referenceContractMismatch
    case sourceDirectoryMissing
    case unsafeEntry(String)
    case countMismatch(Int)
    case byteCountMismatch(UInt64)
    case contentMultisetMismatch(String)
    case nameInclusiveTripwireMismatch(String)

    public var description: String {
        switch self {
        case .referenceDigestMismatch: return "referenceDigestMismatch"
        case .referenceContractMismatch: return "referenceContractMismatch"
        case .sourceDirectoryMissing: return "sourceDirectoryMissing"
        case let .unsafeEntry(name): return "unsafeEntry(\(name))"
        case let .countMismatch(count): return "countMismatch(\(count))"
        case let .byteCountMismatch(bytes): return "byteCountMismatch(\(bytes))"
        case let .contentMultisetMismatch(value): return "contentMultisetMismatch(\(value))"
        case let .nameInclusiveTripwireMismatch(value): return "nameInclusiveTripwireMismatch(\(value))"
        }
    }
}

public struct BaselineVerificationResult: Equatable, Codable, Sendable {
    public let sourceDirectory: String
    public let fileCount: Int
    public let totalBytes: UInt64
    public let contentMultisetSHA256: String
    public let nameInclusiveTripwireSHA256: String
    public let verifiedAtISO8601: String
}

public enum BaselineVerifier {
    public static let acceptedReferenceFileSHA256 =
        "3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2"

    public static func verify(
        referenceFile: URL,
        expectedReferenceFileSHA256: String = acceptedReferenceFileSHA256,
        expectedContentMultisetSHA256: String = StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
        expectedTripwireSHA256: String = ImmutableRunAuthorization.acceptedBaselineTripwireSHA256,
        expectedFileCount: Int = StagingPolicy.rev28Accepted.expectedFileCount,
        expectedTotalBytes: UInt64 = StagingPolicy.rev28Accepted.expectedTotalBytes
    ) throws -> BaselineVerificationResult {
        let referenceData = try Data(contentsOf: referenceFile)
        guard EvidenceIO.sha256Hex(referenceData) == expectedReferenceFileSHA256 else {
            throw BaselineVerificationError.referenceDigestMismatch
        }
        let reference = try JSONDecoder().decode(BaselineContentReference.self, from: referenceData)
        guard reference.file_count == expectedFileCount,
              reference.total_bytes == expectedTotalBytes,
              reference.name_excluded_multiset_sha256_of_sorted_list == expectedContentMultisetSHA256,
              reference.unique_content_hashes == expectedFileCount,
              reference.content_multiset.count == expectedFileCount,
              Set(reference.content_multiset).count == expectedFileCount else {
            throw BaselineVerificationError.referenceContractMismatch
        }

        let source = URL(fileURLWithPath: reference.source_dir)
            .resolvingSymlinksInPath().standardizedFileURL
        var rootStat = stat()
        guard source.path.withCString({ lstat($0, &rootStat) }) == 0,
              rootStat.st_mode & S_IFMT == S_IFDIR else {
            throw BaselineVerificationError.sourceDirectoryMissing
        }

        let entries = try FileManager.default.contentsOfDirectory(
            at: source,
            includingPropertiesForKeys: [.fileSizeKey],
            options: []
        ).sorted { $0.lastPathComponent < $1.lastPathComponent }

        var hashes: [String] = []
        var manifestLines: [String] = []
        var totalBytes: UInt64 = 0

        for url in entries {
            var info = stat()
            guard url.path.withCString({ lstat($0, &info) }) == 0,
                  info.st_mode & S_IFMT == S_IFREG else {
                throw BaselineVerificationError.unsafeEntry(url.lastPathComponent)
            }
            let data = try Data(contentsOf: url, options: [.mappedIfSafe])
            let hash = EvidenceIO.sha256Hex(data)
            let size = UInt64(data.count)
            hashes.append(hash)
            totalBytes += size
            manifestLines.append("\(url.lastPathComponent)\t\(size)\t\(hash)")
        }

        guard entries.count == expectedFileCount else {
            throw BaselineVerificationError.countMismatch(entries.count)
        }
        guard totalBytes == expectedTotalBytes else {
            throw BaselineVerificationError.byteCountMismatch(totalBytes)
        }
        let multiset = StagingVerifier.contentMultisetDigest(hashes)
        guard multiset == expectedContentMultisetSHA256,
              hashes.sorted() == reference.content_multiset.sorted() else {
            throw BaselineVerificationError.contentMultisetMismatch(multiset)
        }

        let manifest = manifestLines.sorted().joined(separator: "\n") + "\n"
        let tripwire = EvidenceIO.sha256Hex(Data(manifest.utf8))
        guard tripwire == expectedTripwireSHA256 else {
            throw BaselineVerificationError.nameInclusiveTripwireMismatch(tripwire)
        }

        return BaselineVerificationResult(
            sourceDirectory: source.path,
            fileCount: entries.count,
            totalBytes: totalBytes,
            contentMultisetSHA256: multiset,
            nameInclusiveTripwireSHA256: tripwire,
            verifiedAtISO8601: EvidenceIO.iso8601()
        )
    }
}
