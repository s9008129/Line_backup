import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
import ImageIO
import Rev28Core
import ScreenCaptureKit
import UniformTypeIdentifiers

// MARK: - Frozen artifact loading (read-only; frozen files are never rewritten)

enum FrozenArtifactError: Error, CustomStringConvertible {
    case missing(String)
    case checksumRecordMissing(String)
    case checksumRecordConflict(String)
    case contractViolation(String)

    var description: String {
        switch self {
        case let .missing(name): return "frozen artifact missing: \(name)"
        case let .checksumRecordMissing(name): return "no append-only sha256sums record references \(name)"
        case let .checksumRecordConflict(name): return "append-only sha256sums records disagree for \(name)"
        case let .contractViolation(detail): return "frozen artifact contract violation: \(detail)"
        }
    }
}

enum FrozenArtifacts {
    struct RuleBook {
        let ruleBook: CaptureGeometryRuleBook
        let sha256: String
    }

    struct Chooser {
        let predicate: ChooserAffirmationPredicate
        let predicateSHA256: String
        let calibrationSHA256: String
    }

    static func sha256sumsFiles(in frozenDirectory: URL) throws -> [(url: URL, entries: [String: String])] {
        let files = try FileManager.default.contentsOfDirectory(at: frozenDirectory, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.hasPrefix("sha256sums-") && $0.pathExtension == "txt" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        var records: [(url: URL, entries: [String: String])] = []
        for url in files {
            let contents = try String(contentsOf: url, encoding: .utf8)
            var entries: [String: String] = [:]
            for line in contents.split(whereSeparator: \.isNewline) {
                let columns = line.split(whereSeparator: { $0.isWhitespace })
                guard columns.count == 2 else { continue }
                let name = String(columns[1])
                guard entries[name] == nil else {
                    throw FrozenArtifactError.contractViolation("duplicate entry for \(name) in \(url.lastPathComponent)")
                }
                entries[name] = String(columns[0])
            }
            records.append((url, entries))
        }
        return records
    }

    /// Requires one artifact to be referenced by at least one append-only
    /// checksum record and never referenced with a different value.
    private static func requireChecksum(name: String, sha256: String, in records: [(url: URL, entries: [String: String])]) throws {
        let references = records.compactMap { $0.entries[name] }
        guard !references.isEmpty else { throw FrozenArtifactError.checksumRecordMissing(name) }
        guard Set(references) == [sha256] else { throw FrozenArtifactError.checksumRecordConflict(name) }
    }

    static func loadRuleBook(frozenDirectory: URL) throws -> RuleBook {
        let ruleBookName = "capture-geometry-rulebook-v1.json"
        let matrixName = "capture-matrix-v1.json"
        let ruleBookURL = frozenDirectory.appendingPathComponent(ruleBookName)
        let matrixURL = frozenDirectory.appendingPathComponent(matrixName)
        guard FileManager.default.fileExists(atPath: ruleBookURL.path) else { throw FrozenArtifactError.missing(ruleBookName) }
        guard FileManager.default.fileExists(atPath: matrixURL.path) else { throw FrozenArtifactError.missing(matrixName) }
        let ruleBookData = try Data(contentsOf: ruleBookURL)
        let matrixData = try Data(contentsOf: matrixURL)
        let ruleBookSHA = EvidenceIO.sha256Hex(ruleBookData)
        let matrixSHA = EvidenceIO.sha256Hex(matrixData)
        let records = try sha256sumsFiles(in: frozenDirectory)
        let paired = records.filter { $0.entries[ruleBookName] != nil && $0.entries[matrixName] != nil }
        guard paired.count == 1,
              paired[0].entries[ruleBookName] == ruleBookSHA,
              paired[0].entries[matrixName] == matrixSHA else {
            throw FrozenArtifactError.checksumRecordMissing("\(ruleBookName)+\(matrixName) pair")
        }
        try requireChecksum(name: ruleBookName, sha256: ruleBookSHA, in: records)
        try requireChecksum(name: matrixName, sha256: matrixSHA, in: records)

        let ruleBook = try JSONDecoder().decode(CaptureGeometryRuleBook.self, from: ruleBookData)
        let matrix = try JSONDecoder().decode(CaptureMatrixRecord.self, from: matrixData)
        var expectedKeys = Set<String>()
        for settled in [false, true] {
            for activated in [false, true] {
                for includeChildWindows in [false, true] {
                    expectedKeys.insert(CaptureGeometryRules.stateKey(CaptureGeometryState(
                        settled: settled,
                        activated: activated,
                        includeChildWindows: includeChildWindows,
                        ignoreShadows: true
                    )))
                }
            }
        }
        let validRules = ruleBook.rules.values.allSatisfy {
            $0.maxPerSideSizeDeltaPt.isFinite && $0.maxPerSideSizeDeltaPt >= 0
                && $0.originPaddingPt.isFinite && $0.originPaddingPt >= 0
                && $0.maxOriginPaddingPt.isFinite && $0.maxOriginPaddingPt >= $0.originPaddingPt
        }
        guard ruleBook.ruleID == "rev28-capture-geometry-v1",
              Set(ruleBook.rules.keys) == expectedKeys,
              validRules,
              matrix.frozenRuleCount == 8,
              matrix.shadowBearingBarredFromGeometry,
              matrix.noRuleFailClosedProved else {
            throw FrozenArtifactError.contractViolation("capture geometry rule book or matrix does not prove the frozen contract")
        }
        return RuleBook(ruleBook: ruleBook, sha256: ruleBookSHA)
    }

    /// Derives the strict runtime v2 predicate from the exact frozen v1-shaped
    /// predicate bytes plus the companion frozen AX calibration. The frozen
    /// files are never edited; a mismatch refuses `frozenPredicateMismatch`.
    static func loadChooserPredicate(frozenDirectory: URL) throws -> Chooser {
        let predicateName = "chooser-affirmation-predicate-v2.json"
        let calibrationName = "chooser-ax-calibration-v2.json"
        let predicateURL = frozenDirectory.appendingPathComponent(predicateName)
        let calibrationURL = frozenDirectory.appendingPathComponent(calibrationName)
        guard FileManager.default.fileExists(atPath: predicateURL.path) else { throw FrozenArtifactError.missing(predicateName) }
        guard FileManager.default.fileExists(atPath: calibrationURL.path) else { throw FrozenArtifactError.missing(calibrationName) }
        let predicateData = try Data(contentsOf: predicateURL)
        let calibrationData = try Data(contentsOf: calibrationURL)
        let predicateSHA = EvidenceIO.sha256Hex(predicateData)
        let calibrationSHA = EvidenceIO.sha256Hex(calibrationData)
        let records = try sha256sumsFiles(in: frozenDirectory)
        try requireChecksum(name: predicateName, sha256: predicateSHA, in: records)
        try requireChecksum(name: calibrationName, sha256: calibrationSHA, in: records)

        let base = try JSONDecoder().decode(ChooserAffirmationPredicate.self, from: predicateData)
        let calibration = try JSONDecoder().decode(ChooserAXCalibrationEvidence.self, from: calibrationData)
        let derived: ChooserAffirmationPredicate
        do {
            derived = try ChooserProductionPredicate.derive(frozen: base, calibration: calibration)
        } catch {
            throw FrozenArtifactError.contractViolation("chooser predicate derivation refused: \(error)")
        }
        guard derived.predicateVersion == ChooserAffirmationEvaluator.processStableButtonSemanticsVersion,
              derived.ax.defaultButton != nil,
              derived.ax.cancelButton != nil,
              derived.ownership.requiresOwningPIDInCensusUnion,
              derived.ownership.requiresStableProcessInstance,
              derived.ownership.emptyPreCensusWidensRefusal else {
            throw FrozenArtifactError.contractViolation("derived chooser predicate does not preserve the v2 production clauses")
        }
        return Chooser(predicate: derived, predicateSHA256: predicateSHA, calibrationSHA256: calibrationSHA)
    }
}

// MARK: - Production observation boundary (plan C2/C3)

struct ProductionObservationBoundary: ObservationBoundary {
    let ruleBook: CaptureGeometryRuleBook
    let ruleBookSHA256: String

    func inventory() async throws -> ObservationInventorySnapshot {
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        let sc = WindowSensor.snapshots(from: content)
        let cg = CGWindowInventory.onScreenWindows()
        return ObservationInventorySnapshot(
            scWindows: sc,
            cgWindows: cg,
            sampledAtUptime: ProcessInfo.processInfo.systemUptime
        )
    }

    func capture(
        state: CaptureGeometryState,
        requestedState: String,
        expectedBundleID: String,
        expectedPID: Int32,
        deadlineUptime: Double
    ) async throws -> ObservationCaptureResult {
        try await Self.captureOnMain(
            ruleBook: ruleBook,
            ruleBookSHA256: ruleBookSHA256,
            state: state,
            requestedState: requestedState,
            expectedBundleID: expectedBundleID,
            expectedPID: expectedPID
        )
    }

    /// `FrameCaptureService` is MainActor-isolated (it drives SCK capture with
    /// MainActor-held state). The whole capture path hops there once so the
    /// retained image, its record and the PNG encoding all come from the same
    /// measured capture.
    @MainActor
    private static func captureOnMain(
        ruleBook: CaptureGeometryRuleBook,
        ruleBookSHA256: String,
        state: CaptureGeometryState,
        requestedState: String,
        expectedBundleID: String,
        expectedPID: Int32
    ) async throws -> ObservationCaptureResult {
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        let snapshots = WindowSensor.snapshots(from: content)
        let candidates = WindowSensor.mainWindowCandidates(in: snapshots, bundleID: expectedBundleID, pid: expectedPID)
        guard candidates.count == 1, let main = candidates.first else {
            if candidates.isEmpty { throw ObservationError.missingMainWindow }
            throw ObservationError.ambiguousMainWindowCensus(candidates.count)
        }
        guard let liveWindow = content.windows.first(where: { $0.windowID == main.windowID }) else {
            throw ObservationError.missingMainWindow
        }
        let included = state.includeChildWindows
            ? [main] + WindowSensor.childWindows(of: main, in: snapshots)
            : [main]
        let configuration: CaptureConfiguration = state.includeChildWindows ? .childUnion : .primaryWindow
        guard configuration.ignoreShadows == state.ignoreShadows,
              configuration.includeChildWindows == state.includeChildWindows else {
            throw ObservationError.invalidFrame(["capture configuration does not match the requested geometry state"])
        }
        let identity = try Self.windowIdentity(pid: expectedPID, bundleID: expectedBundleID, window: main)
        let service = FrameCaptureService(ruleBook: ruleBook)
        let captured = try await service.captureWithImage(
            window: liveWindow,
            configuration: configuration,
            includedWindows: included,
            state: state,
            identityTemplate: identity
        )
        guard let pngData = Self.pngData(of: captured.image) else {
            throw ObservationError.pngEncodingMissing
        }
        let record = captured.record
        return ObservationCaptureResult(
            image: captured.image,
            pngData: pngData,
            configuration: record.configuration,
            includedWindows: record.includedWindows,
            sourceRect: record.configuration.sourceRect,
            expectedBBoxPt: record.expectedBBoxPt,
            actualBBoxPt: record.actualBBoxPt,
            imageWidthPx: record.imageWidthPx,
            imageHeightPx: record.imageHeightPx,
            perSideSizeDeltaPt: record.perSideSizeDeltaPt,
            scale: record.scale,
            backingScaleFactor: record.backingScaleFactor,
            stateKey: record.stateKey,
            ruleID: ruleBook.ruleID,
            ruleSHA256: ruleBookSHA256,
            validity: record.validity,
            violations: record.violations,
            identityTemplate: record.identity
        )
    }

    func recognize(image: CGImage) async throws -> [OcrItem] {
        try await VisionOcrEngine().recognize(image: image)
    }

    func axEvidence(pid: Int32, windowID: UInt32) async throws -> AXEvidenceSnapshot {
        let window = matchingAXWindow(pid: pid, windowID: windowID)
        return AXEvidenceSnapshot(
            pid: pid,
            windowID: windowID,
            role: window.flatMap { AXDriver.role(of: $0) },
            subrole: window.flatMap { AXDriver.subrole(of: $0) },
            title: window.flatMap { AXDriver.title(of: $0) },
            sampledAtUptime: ProcessInfo.processInfo.systemUptime
        )
    }

    func signingIdentity(pid: Int32) async -> String? {
        ProcessIdentity.signingIdentity(pid: pid)
    }

    func monotonicNow() -> Double {
        ProcessInfo.processInfo.systemUptime
    }

    private static func windowIdentity(pid: Int32, bundleID: String, window: SCWindowSnapshot) throws -> WindowIdentity {
        guard let process = ProcessInstanceID.current(pid: pid) else {
            throw ObservationError.processInstanceUnavailable(pid)
        }
        guard let cgEntry = CGWindowInventory.onScreenWindows().first(where: {
            $0.windowNumber == window.windowID && $0.ownerPID == pid && $0.layer == window.windowLayer
        }) else {
            throw ObservationError.invalidFrame(["window \(window.windowID) is absent from the CG census"])
        }
        let axWindow = matchingAXWindow(pid: pid, frame: window.frame)
        return WindowIdentity(
            bundleID: bundleID,
            process: process,
            windowID: window.windowID,
            windowFrame: window.frame,
            ax: AXIdentityRead(
                role: axWindow.flatMap { AXDriver.role(of: $0) },
                subrole: axWindow.flatMap { AXDriver.subrole(of: $0) },
                title: axWindow.flatMap { AXDriver.title(of: $0) }
            ),
            cgEntry: CGWindowEntryRecord(
                windowID: cgEntry.windowNumber,
                frame: cgEntry.frame,
                layer: cgEntry.layer,
                ownerPID: cgEntry.ownerPID,
                ownerName: cgEntry.name ?? ""
            ),
            captureEpoch: 0,
            captureImageSHA256: ""
        )
    }

    static func pngData(of image: CGImage) -> Data? {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(data, UTType.png.identifier as CFString, 1, nil) else {
            return nil
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { return nil }
        return data as Data
    }
}

/// Matches one live AX window to a known windowID/frame pair. The windowID is
/// not exposed through AX, so uniqueness is proven by the frame match: zero or
/// more than one candidate refuses.
func matchingAXWindow(pid: Int32, windowID: UInt32) -> AXUIElement? {
    guard let frame = CGWindowInventory.onScreenWindows().first(where: {
        $0.windowNumber == windowID && $0.ownerPID == pid
    })?.frame else { return nil }
    return matchingAXWindow(pid: pid, frame: frame)
}

func matchingAXWindow(pid: Int32, frame: CGRect) -> AXUIElement? {
    var matches: [AXUIElement] = []
    for window in AXDriver.windows(ofApp: pid) {
        guard let axFrame = AXDriver.frame(of: window) else { continue }
        let distance = Double(
            abs(axFrame.minX - frame.minX) + abs(axFrame.minY - frame.minY)
                + abs(axFrame.width - frame.width) + abs(axFrame.height - frame.height)
        )
        if distance <= 6 { matches.append(window) }
    }
    guard matches.count == 1 else { return nil }
    return matches[0]
}

// MARK: - Production actuation boundary (plan C5)

struct ProductionActuationBoundary: ActuationBoundary {
    func readinessObservation(identity: WindowIdentity, candidate: StructuralCandidate) async throws -> ReadinessObservation {
        try await ReadinessObservation.captureLive(identity: identity, candidate: candidate)
    }

    func revalidateDispatch(pid: Int32, windowID: UInt32, binding: SurfaceBinding) -> Bool {
        guard let application = NSRunningApplication(processIdentifier: pid_t(pid)),
              application.isActive,
              application.bundleIdentifier == binding.bundleID,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == pid_t(pid) else {
            return false
        }
        return CGWindowInventory.onScreenWindows().contains {
            $0.windowNumber == windowID && $0.ownerPID == pid && $0.layer == 0
        }
    }

    func processStable(pid: Int32, binding: SurfaceBinding) -> Bool {
        guard let application = NSRunningApplication(processIdentifier: pid_t(pid)),
              application.bundleIdentifier == binding.bundleID,
              ProcessInstanceID.current(pid: pid) == binding.process else {
            return false
        }
        return true
    }

    func postEventAccess() -> Bool {
        Rev28Core.QuartzActuator.preflightPostEventAccess()
    }

    func clickSink() -> @Sendable (CGEvent, CGEventTapLocation) -> Void {
        { event, tap in event.post(tap: tap) }
    }
}

// MARK: - Production chooser/destination boundary (plan C6/C7)

/// The production chooser boundary owns the real tripwire journal. Sampling is
/// input-free; affirmation is decided only by the strict monitor over predicate
/// v2 candidates with fresh SCK+CG+AX evidence and pre/post process instances.
final class ProductionChooserBoundary: @unchecked Sendable, ChooserBoundary {
    private let predicate: ChooserAffirmationPredicate
    private let journal: TripwireJournal
    private let lock = NSLock()
    private var cumulativeTripwire: [TripwireClassification] = []
    private var preDispatchWindowIDs: Set<UInt32> = []
    private var preDispatchPIDs: Set<Int32> = []
    private var preDispatchOwnerFacts: [Int32: ChooserProcessFacts] = [:]
    private var lastAffirmation: ChooserAffirmation?
    private var lastAffirmationProcess: ProcessInstanceID?
    private var pendingPathField: AXUIElement?
    /// Last SCK census observed by the sampler. Sync postcondition calls cannot
    /// await SCK, so the freshest sampled census is cached and bounded by age;
    /// stale cache refuses instead of guessing.
    private var cachedSCWindows: [UInt32: Int32] = [:]
    private var cachedSCSampledAtUptime: Double = 0
    private static let cachedCensusMaximumAgeSeconds = 2.0

    init(predicate: ChooserAffirmationPredicate, journal: TripwireJournal) {
        self.predicate = predicate
        self.journal = journal
    }

    var defaultButtonTitles: [String] { predicate.ax.defaultButton?.titles ?? [] }

    func preDispatchContextSatisfied(minimumSeconds: Double) -> Bool {
        guard journal.preDispatchContextSatisfied(minimumSeconds: minimumSeconds) else { return false }
        // Record the pre-dispatch environmental census exactly once, at the gate
        // that immediately precedes the irreversible dispatch boundary.
        lock.lock()
        defer { lock.unlock() }
        if preDispatchWindowIDs.isEmpty {
            let cg = CGWindowInventory.onScreenWindows()
            preDispatchWindowIDs = Set(cg.map(\.windowNumber))
            preDispatchPIDs = Set(cg.map(\.ownerPID))
            for pid in preDispatchPIDs {
                preDispatchOwnerFacts[pid] = ProcessIdentity.reading(pid: pid)
            }
        }
        return true
    }

    func sample(
        preDispatchInventory: ObservationInventorySnapshot,
        predicate: ChooserAffirmationPredicate
    ) async -> StrictPostconditionObservation {
        let drain = journal.drain()
        lock.lock()
        cumulativeTripwire.append(contentsOf: drain.classifications)
        let cumulative = cumulativeTripwire
        let preWindowIDs = preDispatchInventory.scWindows.isEmpty
            ? preDispatchWindowIDs
            : Set(preDispatchInventory.scWindows.map(\.windowID))
        let prePIDs = preDispatchInventory.scWindows.isEmpty
            ? preDispatchPIDs
            : Set(preDispatchInventory.scWindows.compactMap(\.ownerPID))
        let preFacts = preDispatchOwnerFacts
        lock.unlock()

        guard drain.healthy else {
            return .failed(
                "tripwire collector unhealthy (dropped=\(drain.droppedEventFlags) errors=\(drain.streamErrorCount)); no affirmation is possible",
                tripwireObservations: cumulative
            )
        }
        if cumulative.contains(where: { $0.aborts }) {
            return .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: cumulative))
        }

        do {
            let cgInventory = CGWindowInventory.onScreenWindows()
            let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
            let snapshots = WindowSensor.snapshots(from: content)
            let postPIDs = Set(snapshots.compactMap(\.ownerPID))
            let censusUnion = prePIDs.union(postPIDs)
            lock.lock()
            cachedSCWindows = Dictionary(uniqueKeysWithValues: snapshots.compactMap { snapshot in
                guard let pid = snapshot.ownerPID else { return nil }
                return (snapshot.windowID, pid)
            })
            cachedSCSampledAtUptime = ProcessInfo.processInfo.systemUptime
            lock.unlock()
            var rejectionDetails: [String] = []
            for snapshot in snapshots {
                guard let ownerPID = snapshot.ownerPID,
                      censusUnion.contains(ownerPID),
                      snapshot.isOnScreen,
                      snapshot.windowLayer == 0,
                      !preWindowIDs.contains(snapshot.windowID),
                      cgInventory.contains(where: {
                          $0.windowNumber == snapshot.windowID && $0.ownerPID == ownerPID && $0.layer == 0
                      }) else { continue }
                guard let axWindow = matchingAXWindow(pid: ownerPID, frame: snapshot.frame) else {
                    rejectionDetails.append("windowID=\(snapshot.windowID) cause=axWindowNotUniquelyMatched")
                    continue
                }
                let dump = AXDriver.dump(element: axWindow, pid: ownerPID, maxDepth: 8, maxNodes: 800)
                let owner = ProcessIdentity.reading(pid: ownerPID)
                let candidate = ChooserCandidate(
                    windowID: snapshot.windowID,
                    frame: snapshot.frame,
                    onScreen: true,
                    presentInSCInventory: true,
                    presentInCGInventory: true,
                    isNewRelativeToPreDispatchInventory: true,
                    owner: owner,
                    pidReuseDetected: false,
                    axNodes: dump.nodes,
                    preDispatchCensusPIDs: prePIDs.sorted(),
                    postDispatchCensusPIDs: postPIDs.sorted(),
                    preDispatchOwner: preFacts[ownerPID],
                    postDispatchOwner: owner
                )
                switch ChooserAffirmationEvaluator.evaluateProduction(candidate: candidate, predicate: predicate) {
                case .affirmed:
                    let affirmation = ChooserAffirmation(
                        windowID: snapshot.windowID,
                        frame: snapshot.frame,
                        ownerPID: ownerPID,
                        predicateID: predicate.predicateID,
                        affirmedAtISO8601: EvidenceIO.iso8601()
                    )
                    lock.lock()
                    lastAffirmation = affirmation
                    lastAffirmationProcess = ProcessInstanceID.current(pid: ownerPID)
                    lock.unlock()
                    return .observed(StrictPostconditionSample(affirmation: affirmation, tripwireObservations: cumulative))
                case let .refused(cause, detail):
                    rejectionDetails.append("windowID=\(snapshot.windowID) cause=\(cause.rawValue) \(detail)")
                }
            }
            return .observed(StrictPostconditionSample(
                affirmation: nil,
                tripwireObservations: cumulative
            ))
        } catch {
            return .failed("chooser sampler error: \(error)", tripwireObservations: cumulative)
        }
    }

    func panelStillBound(pid: Int32, confirmation: ChooserAffirmation) -> Bool {
        guard let liveProcess = ProcessInstanceID.current(pid: pid),
              let application = NSRunningApplication(processIdentifier: pid_t(pid)),
              application.isActive,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == pid_t(pid) else {
            return false
        }
        lock.lock()
        let cached = cachedSCWindows
        let cachedAt = cachedSCSampledAtUptime
        let affirmedProcess = lastAffirmationProcess
        lock.unlock()
        guard ProcessInfo.processInfo.systemUptime - cachedAt <= Self.cachedCensusMaximumAgeSeconds,
              cached[confirmation.windowID] == pid else {
            return false
        }
        guard affirmedProcess == nil || affirmedProcess == liveProcess else { return false }
        let cgMatches = CGWindowInventory.onScreenWindows().filter {
            $0.windowNumber == confirmation.windowID && $0.ownerPID == pid && $0.layer == 0
        }
        guard cgMatches.count == 1 else { return false }
        guard matchingAXWindow(pid: pid, frame: confirmation.frame) != nil else { return false }
        return true
    }

    func preparePrimitive(_ primitive: DestinationPrimitive, pid: Int32, destination: URL) throws -> [String: String] {
        let target = destination.standardizedFileURL.path
        switch primitive {
        case .goToFolderChord:
            try QuartzActuator.postKeyChord(keyCode: 5, flags: [.maskCommand, .maskShift])
            let deadline = Date().addingTimeInterval(8)
            var field: AXUIElement?
            while Date() < deadline {
                if let raw = AXDriver.copyAttribute(AXDriver.appElement(pid: pid), kAXFocusedUIElementAttribute as String),
                   CFGetTypeID(raw) == AXUIElementGetTypeID() {
                    let focused = raw as! AXUIElement
                    if AXDriver.role(of: focused) == (kAXTextFieldRole as String) {
                        field = focused
                        break
                    }
                }
                usleep(100_000)
            }
            guard let field else { throw FolderChooserDriverError.goToFolderEntryMissing }
            lock.lock()
            pendingPathField = field
            lock.unlock()
            return ["fieldRole": AXDriver.role(of: field) ?? "?", "fieldValue": AXDriver.valueAsString(field) ?? ""]
        case .pathEntry:
            lock.lock()
            let field = pendingPathField
            lock.unlock()
            guard let field else { throw FolderChooserDriverError.pathEntryFailed("no bound Go-to-folder field from the chord primitive") }
            var settable = DarwinBoolean(false)
            if AXUIElementIsAttributeSettable(field, kAXValueAttribute as CFString, &settable) == .success, settable.boolValue {
                _ = AXUIElementSetAttributeValue(field, kAXValueAttribute as CFString, target as CFString)
            }
            if AXDriver.valueAsString(field) != target {
                try QuartzActuator.postKeyChord(keyCode: 0, flags: [.maskCommand])
                usleep(80_000)
                try QuartzActuator.postUnicodeText(target)
            }
            let deadline = Date().addingTimeInterval(8)
            while Date() < deadline {
                if AXDriver.valueAsString(field) == target {
                    return ["fieldValue": target]
                }
                usleep(60_000)
            }
            throw FolderChooserDriverError.pathEntryFailed("bound navigation field did not reflect the exact authorized destination")
        case .navigationReturn:
            try QuartzActuator.postKeyChord(keyCode: 36, flags: [])
            return ["returnPosted": "true"]
        }
    }

    func destinationReflected(pid: Int32, destination: URL) -> Bool {
        let target = destination.standardizedFileURL.path
        return FolderChooserDriver.directoryCandidates(pid: pid).contains {
            URL(fileURLWithPath: $0).standardizedFileURL.path == target
        }
    }

    func pressDefaultButton(pid: Int32, confirmation: ChooserAffirmation) throws -> String {
        guard let window = matchingAXWindow(pid: pid, frame: confirmation.frame) else {
            throw FolderChooserDriverError.panelNotFound
        }
        let titles = defaultButtonTitles
        guard let button = AXDriver.firstDescendant(of: window, maxDepth: 12, matching: { element in
            guard AXDriver.role(of: element) == (kAXButtonRole as String) else { return false }
            if AXDriver.keyEquivalent(of: element) == "\r" { return true }
            guard !titles.isEmpty else { return false }
            return titles.contains(AXDriver.title(of: element) ?? "")
        }) else {
            throw FolderChooserDriverError.defaultButtonMissing
        }
        let detail = "role=\(AXDriver.role(of: button) ?? "?") title=\(AXDriver.title(of: button) ?? "?")"
        guard AXDriver.press(button) else { throw FolderChooserDriverError.pressFailed("AXPress failed") }
        return detail
    }

    func chooserClosed(pid: Int32) -> Bool {
        lock.lock()
        let affirmation = lastAffirmation
        let cached = cachedSCWindows
        let cachedAt = cachedSCSampledAtUptime
        lock.unlock()
        guard let affirmation else { return false }
        if ProcessInfo.processInfo.systemUptime - cachedAt <= Self.cachedCensusMaximumAgeSeconds,
           cached[affirmation.windowID] == pid {
            return false
        }
        let cgMatches = CGWindowInventory.onScreenWindows().filter {
            $0.windowNumber == affirmation.windowID && $0.ownerPID == pid && $0.layer == 0
        }
        return cgMatches.isEmpty
    }
}

// MARK: - Production filesystem boundary (plan C7)

struct ProductionFilesystemBoundary: FilesystemBoundary {
    func stagingSnapshot(directory: URL, observedAt: Double) throws -> StagingSnapshot {
        try StagingVerifier.snapshot(directory: directory, observedAt: observedAt)
    }

    func directoryExists(_ url: URL) -> Bool {
        var isDirectory = ObjCBool(false)
        let exists = FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory)
        return exists && isDirectory.boolValue
    }

    func verifyBaseline(referenceFile: URL) throws -> BaselineVerificationResult {
        try BaselineVerifier.verify(referenceFile: referenceFile)
    }
}

// MARK: - Live run configuration (one composition for preflight and execute)

struct LiveRunConfig: Decodable {
    let authorization: ImmutableRunAuthorization
    let targetBundleID: String
    let targetPID: Int32
    let ledgerPath: String
    let planPath: String
    let repositoryRoot: String
    let frozenDirectory: String?
    let baselineReferencePath: String?
    let controlRoot: String?
    let targetAlbumCardCountText: String?
    let targetPhotoCountText: String?
    let captureTimeoutSeconds: Double?
    let stagingSnapshotIntervalSeconds: Double?
    let downloadObservationLimitSeconds: Double?
    let menuReferenceRows: [String]?
}

struct LiveComposition {
    let owner: PersistentTransactionOwner
    let adapter: NativeLiveExecutionAdapter
    let session: NativeObservationSession
    let journal: TripwireJournal
    let windowID: UInt32
}

enum LiveCompositionError: Error, CustomStringConvertible {
    case refused(String)

    var description: String {
        switch self {
        case let .refused(reason): return "liveCompositionRefused(\(reason))"
        }
    }
}

enum LiveCompositionBuilder {
    struct Inputs {
        let config: LiveRunConfig
        let ledgerURL: URL
        let frozenDirectory: URL
        let baselineReferenceFile: URL
        let controlRoot: URL
    }

    static func inputs(from config: LiveRunConfig) throws -> Inputs {
        let repositoryRoot = URL(fileURLWithPath: config.repositoryRoot).standardizedFileURL
        let taskEvidence = repositoryRoot.appendingPathComponent("evidence/20260925-rev28-native-closed-loop", isDirectory: true)
        let frozenDirectory = config.frozenDirectory.map { URL(fileURLWithPath: $0) }
            ?? taskEvidence.appendingPathComponent("harness/frozen", isDirectory: true)
        let baselineReference = config.baselineReferencePath.map { URL(fileURLWithPath: $0) }
            ?? taskEvidence.appendingPathComponent("baseline-content-multiset.json")
        let ledgerURL = URL(fileURLWithPath: config.ledgerPath).standardizedFileURL
        let controlRoot = config.controlRoot.map { URL(fileURLWithPath: $0) }
            ?? ledgerURL.deletingLastPathComponent()
        return Inputs(
            config: config,
            ledgerURL: ledgerURL,
            frozenDirectory: frozenDirectory.standardizedFileURL,
            baselineReferenceFile: baselineReference.standardizedFileURL,
            controlRoot: controlRoot.standardizedFileURL
        )
    }

    /// The engine's own target contract, checked identically for preflight and
    /// execute so an ineligible authorization can never reach either phase.
    static func validateEngineTargets(_ authorization: ImmutableRunAuthorization) throws {
        guard authorization.group == LiveExecutionEngine.targetGroup,
              authorization.album == LiveExecutionEngine.targetAlbum,
              authorization.expectedFileCount == StagingPolicy.rev28Accepted.expectedFileCount,
              authorization.expectedTotalBytes == StagingPolicy.rev28Accepted.expectedTotalBytes,
              authorization.expectedContentMultisetSHA256 == StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
              authorization.baselineTripwireSHA256 == ImmutableRunAuthorization.acceptedBaselineTripwireSHA256 else {
            throw LiveCompositionError.refused("authorization does not match the reviewed engine target contract")
        }
    }

    static func validatePathSeparation(_ authorization: ImmutableRunAuthorization) throws {
        let staging = URL(fileURLWithPath: authorization.stagingRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        let evidence = URL(fileURLWithPath: authorization.evidenceRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        guard staging.path != evidence.path else {
            throw LiveCompositionError.refused("staging and evidence run directories must be distinct")
        }
        let stagingPrefix = staging.path.hasSuffix("/") ? staging.path : staging.path + "/"
        let evidencePrefix = evidence.path.hasSuffix("/") ? evidence.path : evidence.path + "/"
        guard !evidencePrefix.hasPrefix(stagingPrefix), !stagingPrefix.hasPrefix(evidencePrefix) else {
            throw LiveCompositionError.refused("staging and evidence run directories must be non-overlapping")
        }
        guard evidence.lastPathComponent == authorization.runID else {
            throw LiveCompositionError.refused("evidence run directory must end in the authorized runID")
        }
    }

    /// Field-shape validation equivalent to the owner-side `isValid`
    /// preconditions that are not already proved by `validateEngineTargets`
    /// and `validatePathSeparation` (directory structure is re-checked in
    /// `build`). The owner repeats its own full check when it is constructed;
    /// this refuses an unusable authorization before any boundary is created.
    static func validateAuthorizationFields(_ authorization: ImmutableRunAuthorization) throws {
        func isSHA256(_ value: String) -> Bool {
            value.count == 64 && value.allSatisfy { $0.isHexDigit }
        }
        guard !authorization.runID.isEmpty,
              !authorization.goal.isEmpty,
              !authorization.group.isEmpty,
              !authorization.album.isEmpty else {
            throw LiveCompositionError.refused("authorization has an empty runID/goal/group/album")
        }
        guard isSHA256(authorization.planSHA256),
              isSHA256(authorization.reviewedImplementationSHA256),
              isSHA256(authorization.expectedContentMultisetSHA256),
              isSHA256(authorization.baselineTripwireSHA256) else {
            throw LiveCompositionError.refused("authorization contains a malformed SHA-256 field")
        }
        guard authorization.expectedFileCount > 0, authorization.expectedTotalBytes > 0 else {
            throw LiveCompositionError.refused("authorization expected counts must be positive")
        }
        guard !authorization.stagingRoot.isEmpty,
              !authorization.stagingRunDirectory.isEmpty,
              !authorization.evidenceRunDirectory.isEmpty else {
            throw LiveCompositionError.refused("authorization contains an empty staging/evidence path")
        }
        let rootURL = URL(fileURLWithPath: authorization.stagingRoot).resolvingSymlinksInPath().standardizedFileURL
        let runURL = URL(fileURLWithPath: authorization.stagingRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        let rootPrefix = rootURL.path.hasSuffix("/") ? rootURL.path : rootURL.path + "/"
        guard runURL.path != rootURL.path, runURL.path.hasPrefix(rootPrefix) else {
            throw LiveCompositionError.refused("staging run directory must be nested inside the approved staging root")
        }
    }

    static func build(inputs: Inputs) async throws -> LiveComposition {
        let config = inputs.config
        let authorization = config.authorization
        try validateAuthorizationFields(authorization)
        try validateEngineTargets(authorization)
        try validatePathSeparation(authorization)

        let stagingRoot = URL(fileURLWithPath: authorization.stagingRoot).resolvingSymlinksInPath().standardizedFileURL
        let stagingRun = URL(fileURLWithPath: authorization.stagingRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        var stagingIsDirectory = ObjCBool(false)
        guard FileManager.default.fileExists(atPath: stagingRoot.path, isDirectory: &stagingIsDirectory),
              stagingIsDirectory.boolValue else {
            throw LiveCompositionError.refused("approved staging root does not exist")
        }
        guard FileManager.default.fileExists(atPath: stagingRun.path, isDirectory: &stagingIsDirectory),
              stagingIsDirectory.boolValue else {
            throw LiveCompositionError.refused("authorized staging run directory does not exist")
        }
        let stagingEntries = try FileManager.default.contentsOfDirectory(atPath: stagingRun.path)
        guard stagingEntries.isEmpty else {
            throw LiveCompositionError.refused("authorized staging run directory is not empty")
        }

        let ruleBook = try FrozenArtifacts.loadRuleBook(frozenDirectory: inputs.frozenDirectory)
        let chooserArtifacts = try FrozenArtifacts.loadChooserPredicate(frozenDirectory: inputs.frozenDirectory)
        let baseline = try BaselineVerifier.verify(referenceFile: inputs.baselineReferenceFile)
        let baselineSource = URL(fileURLWithPath: baseline.sourceDirectory).resolvingSymlinksInPath().standardizedFileURL

        let evidenceDirectory = URL(fileURLWithPath: authorization.evidenceRunDirectory).resolvingSymlinksInPath().standardizedFileURL
        var evidenceIsDirectory = ObjCBool(false)
        if FileManager.default.fileExists(atPath: evidenceDirectory.path, isDirectory: &evidenceIsDirectory), !evidenceIsDirectory.boolValue {
            throw LiveCompositionError.refused("authorized evidence run path is not a directory")
        }

        let downloads = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Downloads", isDirectory: true)
        var watchPaths = [stagingRoot, downloads, baselineSource, inputs.controlRoot]
        watchPaths.removeAll { !FileManager.default.fileExists(atPath: $0.path) }
        var seenWatch = Set<String>()
        watchPaths = watchPaths.filter { seenWatch.insert($0.resolvingSymlinksInPath().standardizedFileURL.path).inserted }
        let declaredSelfPaths = [evidenceDirectory, inputs.controlRoot, inputs.ledgerURL.deletingLastPathComponent()]
        let journal = try TripwireJournal(
            scope: TripwireScope(stagingRunDir: stagingRun, approvedRoot: stagingRoot),
            watchPaths: watchPaths,
            declaredSelfPaths: declaredSelfPaths,
            baselineProtectedPaths: [inputs.baselineReferenceFile, baselineSource]
        )
        try journal.start()

        do {
            let observationBoundary = ProductionObservationBoundary(
                ruleBook: ruleBook.ruleBook,
                ruleBookSHA256: ruleBook.sha256
            )
            let session = try NativeObservationSession(
                sessionID: "\(authorization.runID)-\(UUID().uuidString.prefix(8))",
                runID: authorization.runID,
                targetBundleID: config.targetBundleID,
                targetPID: config.targetPID,
                evidenceDirectory: evidenceDirectory,
                boundary: observationBoundary
            )
            let store = try NativeEvidenceStore(
                runDirectory: evidenceDirectory,
                runID: authorization.runID,
                planSHA256: authorization.planSHA256,
                reviewedImplementationSHA256: authorization.reviewedImplementationSHA256
            )
            let goalSlot = try GoalSlot(
                controlRoot: inputs.controlRoot,
                identity: GoalSlotIdentity(
                    goal: authorization.goal,
                    group: authorization.group,
                    album: authorization.album,
                    stagingRunDirectory: stagingRun
                )
            )
            let ledger = try IntentLedger(fileURL: inputs.ledgerURL)
            let checkpointURL = inputs.controlRoot.appendingPathComponent("ledger-head-anchor.json")
            let owner = try PersistentTransactionOwner(
                authorization: authorization,
                ledger: ledger,
                checkpointURL: checkpointURL,
                requireCheckpointOnResume: true,
                goalSlot: goalSlot
            )
            let adapterConfiguration = NativeAdapterConfiguration(
                targetBundleID: config.targetBundleID,
                targetGroup: authorization.group,
                targetAlbumTitle: authorization.album,
                targetAlbumCardCountText: config.targetAlbumCardCountText ?? "57",
                targetPhotoCountText: config.targetPhotoCountText ?? "57張照片",
                stagingRunDirectory: stagingRun,
                baselineReferenceFileURL: inputs.baselineReferenceFile,
                chooserPredicate: chooserArtifacts.predicate,
                captureTimeoutSeconds: config.captureTimeoutSeconds ?? 10,
                stagingSnapshotIntervalSeconds: config.stagingSnapshotIntervalSeconds ?? 1,
                downloadObservationLimitSeconds: config.downloadObservationLimitSeconds ?? 600,
                menuReferenceRows: config.menuReferenceRows ?? StructuralLocators.lineAlbumMenuReference
            )
            let chooserBoundary = ProductionChooserBoundary(
                predicate: chooserArtifacts.predicate,
                journal: journal
            )
            let adapter = try NativeLiveExecutionAdapter(
                configuration: adapterConfiguration,
                session: session,
                store: store,
                observation: observationBoundary,
                actuation: ProductionActuationBoundary(),
                chooser: chooserBoundary,
                filesystem: ProductionFilesystemBoundary(),
                clock: SystemCompositionClock()
            )
            let windowID = try await uniqueTargetWindowID(bundleID: config.targetBundleID, pid: config.targetPID)
            return LiveComposition(
                owner: owner,
                adapter: adapter,
                session: session,
                journal: journal,
                windowID: windowID
            )
        } catch {
            journal.stop()
            throw error
        }
    }

    static func uniqueTargetWindowID(bundleID: String, pid: Int32) async throws -> UInt32 {
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        let snapshots = WindowSensor.snapshots(from: content)
        let candidates = WindowSensor.mainWindowCandidates(in: snapshots, bundleID: bundleID, pid: pid)
        guard candidates.count == 1, let window = candidates.first else {
            throw LiveCompositionError.refused("target window census is ambiguous or empty (matches=\(candidates.count))")
        }
        return window.windowID
    }
}
