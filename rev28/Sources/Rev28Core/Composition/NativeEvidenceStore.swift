import Foundation

// MARK: - Typed, run-bound evidence for native state transitions (plan R4 §C2/C3)
//
// A high-level adapter may not declare a state valid by returning a hex digest.
// Every transition records a typed artifact that binds the run, plan and
// reviewed implementation hashes, the session/capture/epoch identity and the
// retained observation image. The digest returned to the engine is the SHA-256
// of that artifact, and the same validator can re-read it later (evidence swap
// or tamper detection).

public struct NativeStateEvidence: Codable, Equatable, Sendable {
    public let schemaVersion: Int
    public let runID: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String
    public let state: String
    public let sessionID: String
    public let captureID: String
    public let sequence: Int
    public let epoch: UInt64
    public let frameSHA256: String
    public let processPID: Int32
    public let windowID: UInt32
    public let retainedImagePath: String
    public let recordedAtUptime: Double
    public let facts: [String: String]

    public init(
        schemaVersion: Int = 1,
        runID: String,
        planSHA256: String,
        reviewedImplementationSHA256: String,
        state: String,
        sessionID: String,
        captureID: String,
        sequence: Int,
        epoch: UInt64,
        frameSHA256: String,
        processPID: Int32,
        windowID: UInt32,
        retainedImagePath: String,
        recordedAtUptime: Double,
        facts: [String: String]
    ) {
        self.schemaVersion = schemaVersion
        self.runID = runID
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        self.state = state
        self.sessionID = sessionID
        self.captureID = captureID
        self.sequence = sequence
        self.epoch = epoch
        self.frameSHA256 = frameSHA256
        self.processPID = processPID
        self.windowID = windowID
        self.retainedImagePath = retainedImagePath
        self.recordedAtUptime = recordedAtUptime
        self.facts = facts
    }
}

public enum NativeEvidenceError: Error, Equatable, CustomStringConvertible {
    case runMismatch(expected: String, actual: String)
    case authorizationBindingMismatch
    case retainedImageMissing(String)
    case retainedImageTampered(String)
    case artifactAlreadyExists(String)
    case artifactMissing(String)
    case artifactTampered(String)
    case artifactStateMismatch(expected: String, actual: String)
    case writeFailed(String)

    public var description: String {
        switch self {
        case let .runMismatch(expected, actual): return "runMismatch(expected=\(expected), actual=\(actual))"
        case .authorizationBindingMismatch: return "authorizationBindingMismatch"
        case let .retainedImageMissing(path): return "retainedImageMissing(\(path))"
        case let .retainedImageTampered(path): return "retainedImageTampered(\(path))"
        case let .artifactAlreadyExists(path): return "artifactAlreadyExists(\(path))"
        case let .artifactMissing(path): return "artifactMissing(\(path))"
        case let .artifactTampered(path): return "artifactTampered(\(path))"
        case let .artifactStateMismatch(expected, actual): return "artifactStateMismatch(expected=\(expected), actual=\(actual))"
        case let .writeFailed(detail): return "writeFailed(\(detail))"
        }
    }
}

public final class NativeEvidenceStore {
    public let runDirectory: URL
    public let runID: String
    public let planSHA256: String
    public let reviewedImplementationSHA256: String

    public init(runDirectory: URL, runID: String, planSHA256: String, reviewedImplementationSHA256: String) throws {
        let canonicalRun = runDirectory.resolvingSymlinksInPath().standardizedFileURL
        guard canonicalRun.lastPathComponent == runID else {
            throw NativeEvidenceError.runMismatch(expected: runID, actual: canonicalRun.lastPathComponent)
        }
        guard Self.isSHA256(planSHA256), Self.isSHA256(reviewedImplementationSHA256) else {
            throw NativeEvidenceError.authorizationBindingMismatch
        }
        self.runDirectory = canonicalRun
        self.runID = runID
        self.planSHA256 = planSHA256
        self.reviewedImplementationSHA256 = reviewedImplementationSHA256
        try EvidenceIO.ensureDirectory(canonicalRun)
    }

    /// Validates the bundle's retained image on disk and writes the typed,
    /// append-only state artifact. Returns the artifact SHA-256.
    public func record(state: String, bundle: ObservationBundle, facts: [String: String]) throws -> String {
        guard bundle.runID == runID else {
            throw NativeEvidenceError.runMismatch(expected: runID, actual: bundle.runID)
        }
        let imageURL = URL(fileURLWithPath: bundle.retainedImagePath).resolvingSymlinksInPath().standardizedFileURL
        let imagePath = imageURL.path
        guard FileManager.default.fileExists(atPath: imagePath) else {
            throw NativeEvidenceError.retainedImageMissing(imagePath)
        }
        guard let imageData = try? Data(contentsOf: imageURL),
              EvidenceIO.sha256Hex(imageData) == bundle.pngSHA256,
              bundle.imagePNG == imageData else {
            throw NativeEvidenceError.retainedImageTampered(imagePath)
        }
        let evidence = NativeStateEvidence(
            runID: runID,
            planSHA256: planSHA256,
            reviewedImplementationSHA256: reviewedImplementationSHA256,
            state: state,
            sessionID: bundle.sessionID,
            captureID: bundle.captureID,
            sequence: bundle.sequence,
            epoch: bundle.epoch,
            frameSHA256: bundle.pngSHA256,
            processPID: bundle.process.pid,
            windowID: bundle.identity.windowID,
            retainedImagePath: imagePath,
            recordedAtUptime: bundle.endedAtUptime,
            facts: facts
        )
        let fileName = "native-state-\(state)-\(String(format: "%04d", bundle.sequence))-\(bundle.captureID).json"
        let artifactURL = runDirectory.appendingPathComponent(fileName)
        do {
            return try EvidenceIO.writeJSONAtomically(evidence, to: artifactURL, appendOnly: true)
        } catch EvidenceIOError.alreadyExists(let url) {
            throw NativeEvidenceError.artifactAlreadyExists(url.path)
        } catch {
            throw NativeEvidenceError.writeFailed(String(describing: error))
        }
    }

    /// Re-reads an artifact and verifies it is unchanged, run-bound and of the
    /// expected state. Used by the failure matrix and by post-run verification.
    @discardableResult
    public func verifyArtifact(
        fileURL: URL,
        expectedState: String,
        expectedSHA256: String?
    ) throws -> NativeStateEvidence {
        let canonical = fileURL.resolvingSymlinksInPath().standardizedFileURL
        let rootPath = runDirectory.path.hasSuffix("/") ? runDirectory.path : runDirectory.path + "/"
        guard canonical.path.hasPrefix(rootPath) else {
            throw NativeEvidenceError.artifactMissing(canonical.path)
        }
        guard FileManager.default.fileExists(atPath: canonical.path) else {
            throw NativeEvidenceError.artifactMissing(canonical.path)
        }
        let data = try Data(contentsOf: canonical)
        if let expectedSHA256, EvidenceIO.sha256Hex(data) != expectedSHA256 {
            throw NativeEvidenceError.artifactTampered(canonical.path)
        }
        let evidence: NativeStateEvidence
        do {
            evidence = try JSONDecoder().decode(NativeStateEvidence.self, from: data)
        } catch {
            throw NativeEvidenceError.artifactTampered(canonical.path)
        }
        guard evidence.runID == runID,
              evidence.planSHA256 == planSHA256,
              evidence.reviewedImplementationSHA256 == reviewedImplementationSHA256,
              evidence.schemaVersion == 1 else {
            throw NativeEvidenceError.authorizationBindingMismatch
        }
        guard evidence.state == expectedState else {
            throw NativeEvidenceError.artifactStateMismatch(expected: expectedState, actual: evidence.state)
        }
        return evidence
    }

    private static func isSHA256(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy(\.isHexDigit) && Set(value).count > 1
    }
}
