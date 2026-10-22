import Darwin
import Foundation

public enum PassiveDiagnosticError: Error, CustomStringConvertible {
    case refused(String)
    public var description: String { switch self { case let .refused(reason): return "passiveDiagnosticRefused(\(reason))" } }
}

public struct PassiveDiagnosticFileDigest: Codable, Equatable, Sendable {
    public let name: String
    public let bytes: Int
    public let sha256: String
    public init(name: String, bytes: Int, sha256: String) { self.name = name; self.bytes = bytes; self.sha256 = sha256 }
}

/// File hashes identify the bytes read by the collector, not OS code attestation.
public struct PassiveDiagnosticProvenance: Codable, Equatable, Sendable {
    public let implementationSHA256: String
    public let sourceFiles: [PassiveDiagnosticFileDigest]
    public let executableSHA256: String
    public let executableBytes: Int
    public let observer: String
    public let attestation: String
    public init(implementationSHA256: String, sourceFiles: [PassiveDiagnosticFileDigest], executableSHA256: String, executableBytes: Int) {
        self.implementationSHA256 = implementationSHA256; self.sourceFiles = sourceFiles
        self.executableSHA256 = executableSHA256; self.executableBytes = executableBytes
        observer = "ProductionObservationSource/NativeObservationSession/VisionOcrEngine"; attestation = "UNKNOWN"
    }
    func validated() throws {
        guard PassiveNativeDiagnostic.isSHA(implementationSHA256), PassiveNativeDiagnostic.isSHA(executableSHA256),
              executableBytes > 0, !sourceFiles.isEmpty, Set(sourceFiles.map(\.name)).count == sourceFiles.count,
              sourceFiles.allSatisfy({ !$0.name.isEmpty && $0.bytes >= 0 && PassiveNativeDiagnostic.isSHA($0.sha256) }),
              observer == "ProductionObservationSource/NativeObservationSession/VisionOcrEngine",
              attestation == "UNKNOWN" else { throw PassiveDiagnosticError.refused("invalid provenance") }
    }
}

public struct PassiveDiagnosticCardRegion: Codable, Sendable {
    public let id: String
    public let boundsCapturePx: CGRect
}

/// Explicit diagnostic profiles. Snapshot agreement bounds observation only;
/// it does not prove AX parentage, menu ownership, topmost status or occlusion.
public enum PassiveDiagnosticCaptureProfile: String, Codable, Sendable {
    case primaryWindow
    case childUnion
    case explicitLineWindows

    public var configuration: CaptureConfiguration {
        switch self {
        case .primaryWindow: return .primaryWindow
        case .childUnion: return .childUnion
        case .explicitLineWindows: return .explicitLineWindows
        }
    }
    public var formatVersion: Int {
        switch self { case .primaryWindow: return 1; case .childUnion: return 2; case .explicitLineWindows: return 3 }
    }

    static func matching(_ configuration: CaptureConfiguration) -> Self? {
        if configuration == CaptureConfiguration.primaryWindow { return .primaryWindow }
        if configuration == CaptureConfiguration.childUnion { return .childUnion }
        if configuration.kind == .explicitLineWindows, configuration.sourceRect != nil {
            var request = configuration
            request.sourceRect = nil
            if request == CaptureConfiguration.explicitLineWindows { return .explicitLineWindows }
        }
        return nil
    }

    private static func normalized(_ windows: [SCWindowSnapshot]) -> [SCWindowSnapshot] {
        windows.sorted { $0.windowID < $1.windowID }
    }
    private static func validFrame(_ frame: CGRect) -> Bool {
        [frame.minX, frame.minY, frame.width, frame.height].allSatisfy(\.isFinite)
            && frame.width > 0 && frame.height > 0
    }

    public func selectedWindows(in inventory: [SCWindowSnapshot], target: ObservationTarget) throws -> [SCWindowSnapshot] {
        if self == .explicitLineWindows { return try ExplicitLineCaptureSelection.selectedWindows(in: inventory, target: target) }
        guard target.bundleID == PassiveNativeDiagnostic.lineBundleID, target.pid > 0 else {
            throw PassiveDiagnosticError.refused("LINE diagnostic target required")
        }
        let candidates = WindowSensor.mainWindowCandidates(in: inventory, bundleID: target.bundleID, pid: target.pid)
        guard candidates.count == 1, let main = candidates.first, Self.validFrame(main.frame),
              inventory.filter({ $0.windowID == main.windowID }).count == 1 else {
            throw PassiveDiagnosticError.refused("diagnostic main window is absent, ambiguous or invalid")
        }
        guard self == .childUnion else { return [main] }
        let children = WindowSensor.childWindows(of: main, in: inventory)
        guard !children.isEmpty, Set(children.map(\.windowID)).count == children.count,
              children.allSatisfy({ child in
                  child.windowID != main.windowID && Self.validFrame(child.frame)
                      && child.ownerPID == target.pid && child.ownerBundleID == target.bundleID && child.isOnScreen
                      && inventory.filter({ $0.windowID == child.windowID }).count == 1
              }) else { throw PassiveDiagnosticError.refused("affirmative unique LINE child snapshots required") }
        return Self.normalized([main] + children)
    }

    /// Used by the CLI inside the observation closure, before publication.
    /// Samples A/A followed by a coherent but different bundle B/B refuse.
    public func validateSettlingBinding(bundle: ObservationBundle, sampledWindows: [SCWindowSnapshot]) throws {
        if self == .explicitLineWindows {
            try bundle.validated()
            guard bundle.explicitLineRequestBinding?.settledSelectedWindows == Self.normalized(sampledWindows) else {
                throw PassiveDiagnosticError.refused("explicit LINE settling binding changed before publication")
            }
            return
        }
        guard bundle.frame.configuration == configuration else {
            throw PassiveDiagnosticError.refused("capture profile changed after sampling")
        }
        guard self == .childUnion else { return }
        let pre = try selectedWindows(in: bundle.preInventory, target: bundle.target)
        let post = try selectedWindows(in: bundle.postInventory, target: bundle.target)
        guard Set(sampledWindows.map(\.windowID)).count == sampledWindows.count,
              Self.normalized(sampledWindows) == pre, pre == post,
              Self.normalized(bundle.frame.includedWindows) == pre else {
            throw PassiveDiagnosticError.refused("child composition changed between settling and retained observation")
        }
    }
}

/// Complete raw bundle projection. The actual PNG is retained separately and
/// supplied again to the original validator on every read.
public struct PassiveNativeObservationRecord: Codable, Sendable {
    public let formatVersion: Int
    public let status: String
    public let certifications: [String: String]
    public let localization: String
    public let geometryState: CaptureGeometryState
    public let runID: String
    public let sessionID: String
    public let state: ExecutionState
    public let startedAtMonotonicNanos: UInt64
    public let capturedAtMonotonicNanos: UInt64
    public let endedAtMonotonicNanos: UInt64
    public let deadlineMonotonicNanos: UInt64
    public let epoch: UInt64
    public let target: ObservationTarget
    public let process: ProcessInstanceID
    public let signingIdentity: String?
    public let postProcess: ProcessInstanceID
    public let postSigningIdentity: String?
    public let postAXIdentity: AXIdentityRead
    public let window: WindowIdentity
    public let frame: CapturedFrameRecord
    public let ocrSourceImageSHA256: String
    public let ocrItems: [OcrItem]
    public let cardRegions: [PassiveDiagnosticCardRegion]
    public let preInventory: [SCWindowSnapshot]
    public let postInventory: [SCWindowSnapshot]
    public let cgInventory: [CGWindowSnapshot]
    public let axIdentity: AXIdentityRead
    public var explicitLineRequestBinding: ExplicitLineRequestBinding? = nil

    public init(bundle: ObservationBundle, geometryState: CaptureGeometryState, ruleBook: CaptureGeometryRuleBook) throws {
        try bundle.validated()
        guard bundle.localization == .none, bundle.candidate == nil, bundle.candidateRefusal == nil else {
            throw PassiveDiagnosticError.refused("passive capture cannot carry structural authority")
        }
        guard let profile = PassiveDiagnosticCaptureProfile.matching(bundle.frame.configuration) else {
            throw PassiveDiagnosticError.refused("unsupported passive capture profile")
        }
        formatVersion = profile.formatVersion; status = "OBSERVED_VALID_BUNDLE"; certifications = PassiveNativeDiagnostic.unknownCertifications
        localization = "none"; self.geometryState = geometryState
        runID = bundle.runID; sessionID = bundle.sessionID; state = bundle.state
        startedAtMonotonicNanos = bundle.startedAtMonotonicNanos; capturedAtMonotonicNanos = bundle.capturedAtMonotonicNanos
        endedAtMonotonicNanos = bundle.endedAtMonotonicNanos; deadlineMonotonicNanos = bundle.deadlineMonotonicNanos; epoch = bundle.epoch
        target = bundle.target; process = bundle.process; signingIdentity = bundle.signingIdentity
        postProcess = bundle.postProcess; postSigningIdentity = bundle.postSigningIdentity; postAXIdentity = bundle.postAXIdentity
        window = bundle.window; frame = bundle.frame; ocrSourceImageSHA256 = bundle.ocrSourceImageSHA256; ocrItems = bundle.ocrItems
        cardRegions = bundle.cardRegions.map { PassiveDiagnosticCardRegion(id: $0.id, boundsCapturePx: $0.boundsCapturePx) }
        preInventory = bundle.preInventory; postInventory = bundle.postInventory; cgInventory = bundle.cgInventory; axIdentity = bundle.axIdentity
        explicitLineRequestBinding = bundle.explicitLineRequestBinding
        _ = try reconstruct(png: bundle.framePNGData, ruleBook: ruleBook)
    }

    public func reconstruct(png: Data, ruleBook: CaptureGeometryRuleBook) throws -> ObservationBundle {
        guard let profile = PassiveDiagnosticCaptureProfile.matching(frame.configuration),
              formatVersion == profile.formatVersion, status == "OBSERVED_VALID_BUNDLE", certifications == PassiveNativeDiagnostic.unknownCertifications,
              localization == "none", state == .appReady, cardRegions.isEmpty,
              target.bundleID == PassiveNativeDiagnostic.lineBundleID, target.pid > 0,
              frame.captureKind == profile.configuration.kind,
              geometryState.includeChildWindows == profile.configuration.includeChildWindows, geometryState.ignoreShadows,
              !frame.includedWindows.isEmpty, Set(frame.includedWindows.map(\.windowID)).count == frame.includedWindows.count,
              frame.violations.isEmpty,
              frame.scale.isFinite, frame.scale > 0, frame.backingScaleFactor.isFinite, frame.backingScaleFactor > 0,
              frame.scaleSource == .pointPixelScale, !frame.capturedAtISO8601.isEmpty,
              frame.identity == nil || frame.identity == window else {
            throw PassiveDiagnosticError.refused("unsupported or inconsistent passive record")
        }
        guard let main = frame.includedWindows.first(where: { $0.windowID == window.windowID }) else {
            throw PassiveDiagnosticError.refused("included main window absent")
        }
        if profile == .explicitLineWindows {
            guard explicitLineRequestBinding?.geometryState == geometryState,
                  explicitLineRequestBinding?.ruleBook == ruleBook else {
                throw PassiveDiagnosticError.refused("retained original state/rulebook binding mismatch")
            }
            try ExplicitLineCaptureSelection.validate(binding: explicitLineRequestBinding, target: target,
                mainID: window.windowID, preInventory: preInventory, postInventory: postInventory, frame: frame)
        } else if explicitLineRequestBinding != nil || frame.explicitLineSelectionWitness != nil {
            throw PassiveDiagnosticError.refused("legacy record cannot carry v3 request binding or witness")
        }
        let expectedWindows: [SCWindowSnapshot]
        if profile == .primaryWindow {
            guard frame.includedWindows.count == 1 else { throw PassiveDiagnosticError.refused("version1 requires one primary window") }
            expectedWindows = [main]
        } else {
            let pre = try profile.selectedWindows(in: preInventory, target: target)
            let post = try profile.selectedWindows(in: postInventory, target: target)
            guard pre == post, frame.includedWindows.sorted(by: { $0.windowID < $1.windowID }) == pre else {
                throw PassiveDiagnosticError.refused("retained child snapshots do not exactly match pre/post collection")
            }
            expectedWindows = pre
        }
        let expectedBBox = FrameCaptureSupport.unionBBox(of: expectedWindows, fallback: main.frame)
        guard main.windowID == window.windowID, main.ownerPID == target.pid, main.ownerBundleID == target.bundleID,
              main.windowLayer == 0, main.isOnScreen, preInventory.filter({ $0.windowID == main.windowID }) == [main],
              expectedBBox == frame.expectedBBoxPt, main.frame == window.windowFrame,
              [main.frame.minX, main.frame.minY, main.frame.width, main.frame.height].allSatisfy(\.isFinite),
              let rule = ruleBook.rule(for: geometryState), !ruleBook.ruleID.isEmpty,
              [rule.maxPerSideSizeDeltaPt, rule.originPaddingPt, rule.maxOriginPaddingPt].allSatisfy(\.isFinite),
              CaptureGeometryRules.validateScale(pointPixelScale: frame.scale, backingScaleFactor: frame.backingScaleFactor) == nil else {
            throw PassiveDiagnosticError.refused("capture configuration/window/scale mismatch")
        }
        let evaluation = try CaptureGeometryRules.evaluate(expectedBBox: expectedBBox, imageWidthPx: frame.imageWidthPx,
            imageHeightPx: frame.imageHeightPx, scale: frame.scale, ruleBook: ruleBook, state: geometryState).get()
        guard evaluation.actualBBoxPt == frame.actualBBoxPt, evaluation.perSideSizeDeltaPt == frame.perSideSizeDeltaPt,
              evaluation.stateKey == frame.stateKey else { throw PassiveDiagnosticError.refused("serialized geometry does not recompute") }
        let bundle = ObservationBundle(runID: runID, sessionID: sessionID, state: state,
            startedAtMonotonicNanos: startedAtMonotonicNanos, capturedAtMonotonicNanos: capturedAtMonotonicNanos,
            endedAtMonotonicNanos: endedAtMonotonicNanos, deadlineMonotonicNanos: deadlineMonotonicNanos, epoch: epoch,
            target: target, process: process, signingIdentity: signingIdentity, postProcess: postProcess,
            postSigningIdentity: postSigningIdentity, postAXIdentity: postAXIdentity, window: window, frame: frame,
            framePNGData: png, ocrSourceImageSHA256: ocrSourceImageSHA256, ocrItems: ocrItems,
            cardRegions: [], candidate: nil, candidateRefusal: nil, preInventory: preInventory, postInventory: postInventory,
            cgInventory: cgInventory, axIdentity: axIdentity, localization: .none, explicitLineRequestBinding: explicitLineRequestBinding)
        try bundle.validated()
        return bundle
    }
}

private struct PassiveDiagnosticManifest: Codable {
    let formatVersion: Int
    let status: String
    let certifications: [String: String]
    let cgCensusLimitation: String
    let files: [PassiveDiagnosticFileDigest]
}

public struct PassiveDiagnosticReceipt: Codable, Sendable {
    public let status: String
    public let directory: String
    public let manifestSHA256: String
    public let runID: String
    public let sessionID: String
    public let epoch: UInt64
    public let certifications: [String: String]
}

public enum PassiveNativeDiagnostic {
    public static let lineBundleID = "jp.naver.line.mac"
    public static let unknownCertifications = ["calibration": "UNKNOWN", "occlusion": "UNKNOWN", "currentComposer": "UNKNOWN", "phaseBPermit": "UNKNOWN"]
    public static let packetNames = ["claim.json", "observation.png", "observation.json", "rulebook.json", "provenance.json", "manifest.json"]
    static let cgLimitation = "One post-capture CG census; not atomic, not bracketing occlusion or popup ownership proof."
    static func isSHA(_ value: String) -> Bool { value.count == 64 && value.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) } }

    public static func readProjectRegularFile(path: String, projectRoot: String) throws -> Data {
        try PassiveDiagnosticFiles.validatePath(projectRoot)
        guard path.hasPrefix(projectRoot + "/") else { throw PassiveDiagnosticError.refused("file outside explicit project") }
        return try PassiveDiagnosticFiles.readAbsolute(path)
    }

    public static func validateTarget(bundleID: String, pid: Int32, observedBundleID: String?, observedPID: Int32?) throws {
        guard bundleID == lineBundleID, pid > 0, observedPID == pid, observedBundleID == lineBundleID else {
            throw PassiveDiagnosticError.refused("requires LINE bundle and fresh PID-to-bundle binding")
        }
    }

    /// The anchor must come from the original receipt/review, never this packet.
    public static func load(directory: String, expectedManifestSHA256: String?) throws -> ObservationBundle {
        guard let expectedManifestSHA256, isSHA(expectedManifestSHA256) else { throw PassiveDiagnosticError.refused("external manifest SHA256 required") }
        let fd = try PassiveDiagnosticFiles.openAbsolute(directory, directory: true)
        defer { close(fd) }
        let manifestBytes = try PassiveDiagnosticFiles.read("manifest.json", at: fd)
        guard EvidenceIO.sha256Hex(manifestBytes) == expectedManifestSHA256 else { throw PassiveDiagnosticError.refused("manifest anchor mismatch") }
        let manifest = try JSONDecoder().decode(PassiveDiagnosticManifest.self, from: manifestBytes)
        let expected = Set(packetNames).subtracting(["manifest.json"])
        guard [1, 2, 3].contains(manifest.formatVersion), manifest.status == "OBSERVED_VALID_BUNDLE", manifest.certifications == unknownCertifications,
              manifest.cgCensusLimitation == cgLimitation, Set(manifest.files.map(\.name)) == expected,
              manifest.files.count == expected.count, Set(try PassiveDiagnosticFiles.names(at: fd)) == Set(packetNames) else {
            throw PassiveDiagnosticError.refused("unsupported, incomplete or unexpected packet")
        }
        var retained: [String: Data] = [:]
        for entry in manifest.files {
            guard isSHA(entry.sha256), entry.bytes >= 0 else { throw PassiveDiagnosticError.refused("invalid file digest") }
            let bytes = try PassiveDiagnosticFiles.read(entry.name, at: fd)
            guard bytes.count == entry.bytes, EvidenceIO.sha256Hex(bytes) == entry.sha256 else { throw PassiveDiagnosticError.refused("retained file mismatch: \(entry.name)") }
            retained[entry.name] = bytes
        }
        let provenance = try JSONDecoder().decode(PassiveDiagnosticProvenance.self, from: retained["provenance.json"]!)
        try provenance.validated()
        let ruleBook = try JSONDecoder().decode(CaptureGeometryRuleBook.self, from: retained["rulebook.json"]!)
        let record = try JSONDecoder().decode(PassiveNativeObservationRecord.self, from: retained["observation.json"]!)
        guard record.formatVersion == manifest.formatVersion else { throw PassiveDiagnosticError.refused("manifest/record version mismatch") }
        return try record.reconstruct(png: retained["observation.png"]!, ruleBook: ruleBook)
    }
}

/// Claims an existing empty directory before permission checks or observer
/// construction. Files are created with openat/O_EXCL/O_NOFOLLOW and retained
/// on error. A claim is intentionally never reusable.
public final class PassiveDiagnosticOutput {
    public let projectRoot: URL
    public let directory: URL
    public let ruleBook: CaptureGeometryRuleBook
    private let ruleBytes: Data
    private let claimBytes: Data
    private let rootFD: Int32
    private let outputFD: Int32
    private var used = false
    private var sourceConstructionStarted = false
    private let lock = NSLock()

    public init(projectRoot: String, output: String, rulebook: String) throws {
        try PassiveDiagnosticFiles.validatePath(projectRoot)
        try PassiveDiagnosticFiles.validatePath(output)
        try PassiveDiagnosticFiles.validatePath(rulebook)
        guard output.hasPrefix(projectRoot + "/harness-development/native-diagnostics/"),
              rulebook.hasPrefix(projectRoot + "/") else { throw PassiveDiagnosticError.refused("output/rulebook outside explicit project boundary") }
        let r = try PassiveDiagnosticFiles.openAbsolute(projectRoot, directory: true)
        do {
            let d = try PassiveDiagnosticFiles.openAbsolute(output, directory: true)
            do {
                guard try PassiveDiagnosticFiles.names(at: d).isEmpty else { throw PassiveDiagnosticError.refused("output is not empty") }
                let bytes = try PassiveDiagnosticFiles.readAbsolute(rulebook)
                let rules = try JSONDecoder().decode(CaptureGeometryRuleBook.self, from: bytes)
                let claim = try EvidenceIO.encodeJSON(["kind": "PASSIVE_DIAGNOSTIC_ONLY", "nonce": UUID().uuidString])
                try PassiveDiagnosticFiles.write(claim, name: "claim.json", at: d)
                guard try PassiveDiagnosticFiles.names(at: d) == ["claim.json"] else { throw PassiveDiagnosticError.refused("concurrent output writer") }
                let currentRoot = try PassiveDiagnosticFiles.openAbsolute(projectRoot, directory: true)
                defer { close(currentRoot) }
                let currentOutput = try PassiveDiagnosticFiles.openAbsolute(output, directory: true)
                defer { close(currentOutput) }
                guard try PassiveDiagnosticFiles.sameFile(r, currentRoot), try PassiveDiagnosticFiles.sameFile(d, currentOutput) else {
                    throw PassiveDiagnosticError.refused("directory changed during claim")
                }
                self.projectRoot = URL(fileURLWithPath: projectRoot); directory = URL(fileURLWithPath: output)
                ruleBytes = bytes; claimBytes = claim; ruleBook = rules; rootFD = r; outputFD = d
            } catch { close(d); throw error }
        } catch { close(r); throw error }
    }
    deinit { close(rootFD); close(outputFD) }

    public func makeObservationSource(target: ObservationTarget, signingIdentity: @escaping @Sendable (Int32) -> String?) throws -> ProductionObservationSource {
        try makeObservationSource(target: target, signingIdentity: signingIdentity, beforeConstruction: {})
    }

    /// Filesystem test seam below the observer boundary. The production API
    /// exposes no hook or descriptor; construction has no pathname write.
    func makeObservationSource(target: ObservationTarget, signingIdentity: @escaping @Sendable (Int32) -> String?,
                               beforeConstruction: () throws -> Void) throws -> ProductionObservationSource {
        guard target.bundleID == PassiveNativeDiagnostic.lineBundleID, target.pid > 0 else { throw PassiveDiagnosticError.refused("LINE diagnostic target required") }
        let accepted = lock.withLock { if used || sourceConstructionStarted { return false }; sourceConstructionStarted = true; return true }
        guard accepted else { throw PassiveDiagnosticError.refused("source construction already consumed") }
        try assertUnchanged()
        try beforeConstruction()
        let source = try ProductionObservationSource(target: target, existingEvidenceDirectoryDescriptor: outputFD,
            ruleBook: ruleBook, signingIdentity: signingIdentity)
        try assertUnchanged()
        return source
    }

    public func assertUnchanged() throws {
        let r = try PassiveDiagnosticFiles.openAbsolute(projectRoot.path, directory: true)
        defer { close(r) }
        let d = try PassiveDiagnosticFiles.openAbsolute(directory.path, directory: true)
        defer { close(d) }
        guard try PassiveDiagnosticFiles.sameFile(r, rootFD), try PassiveDiagnosticFiles.sameFile(d, outputFD) else {
            throw PassiveDiagnosticError.refused("project/output directory identity changed")
        }
    }

    public func collect(geometryState: CaptureGeometryState, provenance: PassiveDiagnosticProvenance,
                        observe: () async throws -> ObservationBundle) async throws -> PassiveDiagnosticReceipt {
        let accepted = lock.withLock { if used { return false }; used = true; return true }
        guard accepted else { throw PassiveDiagnosticError.refused("collector already used") }
        try assertUnchanged()
        guard try PassiveDiagnosticFiles.names(at: outputFD) == ["claim.json"] else { throw PassiveDiagnosticError.refused("concurrent output write before observation") }
        try provenance.validated()
        let bundle = try await observe()
        try assertUnchanged()
        let record = try PassiveNativeObservationRecord(bundle: bundle, geometryState: geometryState, ruleBook: ruleBook)
        let entries: [(String, Data)] = [
            ("observation.png", bundle.framePNGData), ("observation.json", try EvidenceIO.encodeJSON(record)),
            ("rulebook.json", ruleBytes), ("provenance.json", try EvidenceIO.encodeJSON(provenance)),
        ]
        for (name, bytes) in entries { try assertUnchanged(); try PassiveDiagnosticFiles.write(bytes, name: name, at: outputFD) }
        let names = PassiveNativeDiagnostic.packetNames.filter { $0 != "manifest.json" }
        let expectedBytes = Dictionary(uniqueKeysWithValues: entries + [("claim.json", claimBytes)])
        let digests = names.map { name -> PassiveDiagnosticFileDigest in
            let data = expectedBytes[name]!
            return PassiveDiagnosticFileDigest(name: name, bytes: data.count, sha256: EvidenceIO.sha256Hex(data))
        }
        let manifest = PassiveDiagnosticManifest(formatVersion: record.formatVersion, status: "OBSERVED_VALID_BUNDLE", certifications: PassiveNativeDiagnostic.unknownCertifications,
            cgCensusLimitation: PassiveNativeDiagnostic.cgLimitation, files: digests)
        let manifestData = try EvidenceIO.encodeJSON(manifest)
        try assertUnchanged()
        try PassiveDiagnosticFiles.write(manifestData, name: "manifest.json", at: outputFD)
        let anchor = EvidenceIO.sha256Hex(manifestData)
        let readBack = try PassiveNativeDiagnostic.load(directory: directory.path, expectedManifestSHA256: anchor)
        guard readBack == bundle else { throw PassiveDiagnosticError.refused("published bundle changed on readback") }
        try assertUnchanged()
        return PassiveDiagnosticReceipt(status: "OBSERVED_VALID_BUNDLE", directory: directory.path, manifestSHA256: anchor,
            runID: bundle.runID, sessionID: bundle.sessionID, epoch: bundle.epoch, certifications: PassiveNativeDiagnostic.unknownCertifications)
    }
}

private enum PassiveDiagnosticFiles {
    static func validatePath(_ path: String) throws {
        let components = path.split(separator: "/", omittingEmptySubsequences: false)
        guard path.hasPrefix("/"), path != "/", !path.hasSuffix("/"), !path.utf8.contains(0),
              !components.dropFirst().contains(where: { $0.isEmpty || $0 == "." || $0 == ".." }) else {
            throw PassiveDiagnosticError.refused("absolute non-traversing path required")
        }
    }
    static func openAbsolute(_ path: String, directory: Bool) throws -> Int32 {
        try validatePath(path)
        let components = path.split(separator: "/")
        var current = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC)
        guard current >= 0 else { throw PassiveDiagnosticError.refused("cannot open filesystem root") }
        for (index, component) in components.enumerated() {
            let wantDirectory = directory || index < components.count - 1
            let next = openat(current, String(component), O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK | (wantDirectory ? O_DIRECTORY : 0))
            close(current)
            guard next >= 0 else { throw PassiveDiagnosticError.refused("missing, symlink or unreadable path component") }
            current = next
        }
        return current
    }
    static func names(at fd: Int32) throws -> [String] {
        // Opening '.' yields an independent directory offset; dup would share it.
        let copy = openat(fd, ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)
        guard copy >= 0, let dir = fdopendir(copy) else { if copy >= 0 { close(copy) }; throw PassiveDiagnosticError.refused("cannot enumerate output") }
        defer { closedir(dir) }
        var result: [String] = []
        errno = 0
        while let entry = readdir(dir) {
            let name = withUnsafePointer(to: &entry.pointee.d_name) { ptr in ptr.withMemoryRebound(to: CChar.self, capacity: Int(MAXNAMLEN) + 1) { String(cString: $0) } }
            if name != ".", name != ".." { result.append(name) }
        }
        guard errno == 0 else { throw PassiveDiagnosticError.refused("output enumeration failed") }
        return result.sorted()
    }
    static func sameFile(_ a: Int32, _ b: Int32) throws -> Bool {
        var lhs = stat(); var rhs = stat()
        guard fstat(a, &lhs) == 0, fstat(b, &rhs) == 0 else { throw PassiveDiagnosticError.refused("directory stat failed") }
        return lhs.st_dev == rhs.st_dev && lhs.st_ino == rhs.st_ino
    }
    static func readAbsolute(_ path: String) throws -> Data {
        let fd = try openAbsolute(path, directory: false); defer { close(fd) }
        return try readFD(fd)
    }
    static func read(_ name: String, at directory: Int32) throws -> Data {
        guard !name.isEmpty, !name.contains("/"), name != ".", name != "..", !name.utf8.contains(0) else { throw PassiveDiagnosticError.refused("unsafe file name") }
        let fd = openat(directory, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK)
        guard fd >= 0 else { throw PassiveDiagnosticError.refused("retained file missing or symlink: \(name)") }
        defer { close(fd) }
        return try readFD(fd)
    }
    static func readFD(_ fd: Int32) throws -> Data {
        var before = stat()
        guard fstat(fd, &before) == 0, before.st_mode & S_IFMT == S_IFREG, before.st_nlink == 1,
              before.st_size >= 0, before.st_size <= 64 * 1024 * 1024 else { throw PassiveDiagnosticError.refused("regular single-link file required") }
        var result = Data(); var buffer = [UInt8](repeating: 0, count: 65536)
        while true {
            let count = Darwin.read(fd, &buffer, buffer.count)
            if count < 0 { if errno == EINTR { continue }; throw PassiveDiagnosticError.refused("retained file read failed") }
            if count == 0 { break }
            result.append(contentsOf: buffer.prefix(count))
            guard result.count <= 64 * 1024 * 1024 else { throw PassiveDiagnosticError.refused("retained file too large") }
        }
        var after = stat()
        guard fstat(fd, &after) == 0, before.st_size == after.st_size, result.count == before.st_size,
              before.st_mtimespec.tv_sec == after.st_mtimespec.tv_sec, before.st_mtimespec.tv_nsec == after.st_mtimespec.tv_nsec,
              before.st_ctimespec.tv_sec == after.st_ctimespec.tv_sec, before.st_ctimespec.tv_nsec == after.st_ctimespec.tv_nsec else {
            throw PassiveDiagnosticError.refused("file changed while reading")
        }
        return result
    }
    static func write(_ data: Data, name: String, at directory: Int32) throws {
        let fd = openat(directory, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0o600)
        guard fd >= 0 else { throw PassiveDiagnosticError.refused("exclusive file creation failed: \(name)") }
        defer { close(fd) }
        try data.withUnsafeBytes { bytes in
            var offset = 0
            while offset < bytes.count {
                let n = Darwin.write(fd, bytes.baseAddress!.advanced(by: offset), bytes.count - offset)
                if n < 0, errno == EINTR { continue }
                guard n > 0 else { throw PassiveDiagnosticError.refused("partial publication: \(name)") }
                offset += n
            }
        }
        guard fsync(fd) == 0, fsync(directory) == 0 else { throw PassiveDiagnosticError.refused("publication sync failed: \(name)") }
        guard try read(name, at: directory) == data else { throw PassiveDiagnosticError.refused("publication readback mismatch: \(name)") }
    }
}
