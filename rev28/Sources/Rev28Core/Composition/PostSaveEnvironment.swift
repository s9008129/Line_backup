import AppKit
import CoreGraphics
import Foundation

// MARK: - Post-Save-All OS boundary (plan C5-C7)
//
// Everything the composed adapter needs after the one guarded Save All is a
// fact this seam can supply. Common code owns the state/predicate/intent
// decisions; implementations only observe the machine (SCK/CG/AX/FSEvents,
// real staging snapshots) or post the reviewed AX/navigation primitives.

public struct ChooserCensus: Codable, Equatable, Sendable {
    public let windowIDs: [UInt32]
    public let processes: [ChooserProcessFacts]
    public let recordedAtMonotonicNanos: UInt64

    public init(windowIDs: [UInt32], processes: [ChooserProcessFacts], recordedAtMonotonicNanos: UInt64) {
        self.windowIDs = windowIDs
        self.processes = processes
        self.recordedAtMonotonicNanos = recordedAtMonotonicNanos
    }

    public var isEmpty: Bool { windowIDs.isEmpty || processes.isEmpty }
}

public struct ChooserWindowFacts: Sendable {
    public let windowID: UInt32
    public let frame: CGRect
    public let onScreen: Bool
    public let presentInSCInventory: Bool
    public let presentInCGInventory: Bool
    public let owner: ChooserProcessFacts
    public let pidReuseDetected: Bool
    public let axNodes: [AXNodeDump]
    public let preDispatchOwner: ChooserProcessFacts?
    public let postDispatchOwner: ChooserProcessFacts?

    public init(
        windowID: UInt32,
        frame: CGRect,
        onScreen: Bool,
        presentInSCInventory: Bool,
        presentInCGInventory: Bool,
        owner: ChooserProcessFacts,
        pidReuseDetected: Bool,
        axNodes: [AXNodeDump],
        preDispatchOwner: ChooserProcessFacts?,
        postDispatchOwner: ChooserProcessFacts?
    ) {
        self.windowID = windowID
        self.frame = frame
        self.onScreen = onScreen
        self.presentInSCInventory = presentInSCInventory
        self.presentInCGInventory = presentInCGInventory
        self.owner = owner
        self.pidReuseDetected = pidReuseDetected
        self.axNodes = axNodes
        self.preDispatchOwner = preDispatchOwner
        self.postDispatchOwner = postDispatchOwner
    }
}

public struct ChooserFacts: Sendable {
    public let windows: [ChooserWindowFacts]
    public let postDispatchCensusPIDs: [Int32]
    public let tripwire: [TripwireClassification]

    public init(windows: [ChooserWindowFacts], postDispatchCensusPIDs: [Int32], tripwire: [TripwireClassification]) {
        self.windows = windows
        self.postDispatchCensusPIDs = postDispatchCensusPIDs
        self.tripwire = tripwire
    }
}

public enum ChooserFactsResult: Sendable {
    case facts(ChooserFacts)
    case failed(String, tripwire: [TripwireClassification])
}

public struct PostConfirmationFacts: Sendable {
    public let chooserWindowStillOnScreen: Bool
    public let stagingSnapshot: StagingSnapshot
    public let tripwire: [TripwireClassification]

    public init(chooserWindowStillOnScreen: Bool, stagingSnapshot: StagingSnapshot, tripwire: [TripwireClassification]) {
        self.chooserWindowStillOnScreen = chooserWindowStillOnScreen
        self.stagingSnapshot = stagingSnapshot
        self.tripwire = tripwire
    }
}

/// One snapshot of the cumulative pre-dispatch tripwire context. "Clean" means
/// the journal is running, has no startup/collection failure, no dropped-event
/// gap, and the window has actually lasted its minimum. Anything else is a
/// named refusal, never an empty-but-clean tripwire.
public struct PreDispatchContextFacts: Sendable {
    public let minimumSeconds: Double
    public let observedSeconds: Double
    public let journalRunning: Bool
    public let journalFailure: String?
    public let collectionGap: String?
    public let journalStartedAtMonotonicNanos: UInt64
    public let facts: [TripwireJournalFact]

    public init(
        minimumSeconds: Double,
        observedSeconds: Double,
        journalRunning: Bool,
        journalFailure: String?,
        collectionGap: String?,
        journalStartedAtMonotonicNanos: UInt64,
        facts: [TripwireJournalFact]
    ) {
        self.minimumSeconds = minimumSeconds
        self.observedSeconds = observedSeconds
        self.journalRunning = journalRunning
        self.journalFailure = journalFailure
        self.collectionGap = collectionGap
        self.journalStartedAtMonotonicNanos = journalStartedAtMonotonicNanos
        self.facts = facts
    }

    public var isClean: Bool {
        journalRunning && journalFailure == nil && collectionGap == nil && observedSeconds >= minimumSeconds
    }

    public var refusalDetail: String {
        if let journalFailure { return "tripwire journal failed: \(journalFailure)" }
        if let collectionGap { return "tripwire collection gap: \(collectionGap)" }
        if !journalRunning { return "tripwire journal is not running" }
        return String(
            format: "pre-dispatch environmental context lasted %.1fs, below the required %.0fs",
            observedSeconds,
            minimumSeconds
        )
    }
}

public protocol PostSaveEnvironment: Sendable {
    func verifyBaseline() throws -> BaselineVerificationResult
    /// ≥`minimumSeconds` of pre-dispatch environmental context at
    /// SAVE_ALL_LOCATED with the tripwire running and gap-free.
    func preDispatchContext(minimumSeconds: Double) async throws -> PreDispatchContextFacts
    func preDispatchCensus() async throws -> ChooserCensus
    func sampleChooserFacts(preCensus: ChooserCensus) async -> ChooserFactsResult
    /// Posts the one reviewed Save All event through the gated actuator.
    func dispatchSaveAllClick(
        owner: PersistentTransactionOwner,
        permit: ReadinessPermit,
        binding: SurfaceBinding,
        postHoverRevalidation: @escaping @Sendable () async throws -> Void
    ) async throws
    func prepareDestination(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String
    func confirmDefaultButton(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String
    func postConfirmationFacts(chooserWindowIDs: [UInt32], stagingDirectory: URL) async -> PostConfirmationFacts?
    func stagingSnapshot(directory: URL) throws -> StagingSnapshot
    func tripwireObservations() -> [TripwireClassification]
    /// Refuses when a post-dispatch dropped-event window or collector failure
    /// makes the tripwire non-clean (plan C7).
    func postDispatchTripwireGate() throws
    /// Disclosure string for the tripwire evidence artifact; nil when clean.
    func tripwireCollectionGapDisclosure() -> String?
    func markDispatchBoundary()
    func monotonicNow() -> Double
    func sleep(seconds: Double) async
}

public enum PostSaveEnvironmentError: Error, Equatable, CustomStringConvertible {
    case tripwireUnavailable(String)
    case tripwireCollectionGap(String)
    case tripwireContextWindowFailed(String)

    public var description: String {
        switch self {
        case let .tripwireUnavailable(detail): return "tripwireUnavailable(\(detail))"
        case let .tripwireCollectionGap(detail): return "tripwireCollectionGap(\(detail))"
        case let .tripwireContextWindowFailed(detail): return "tripwireContextWindowFailed(\(detail))"
        }
    }
}

public struct ProductionPostSaveEnvironment: PostSaveEnvironment {
    private let baselineReferenceFile: URL
    private let journal: FilesystemTripwireJournal
    private let signingIdentity: @Sendable (Int32) -> String?

    public init(
        baselineReferenceFile: URL,
        stagingRunDirectory: URL,
        approvedRoot: URL,
        monitoredRoots: [URL],
        evidenceRunDirectory: URL,
        baselineSourceDirectory: URL?,
        signingIdentity: @escaping @Sendable (Int32) -> String?
    ) throws {
        self.baselineReferenceFile = baselineReferenceFile
        self.signingIdentity = signingIdentity
        let journal = FilesystemTripwireJournal(
            scope: TripwireScope(stagingRunDir: stagingRunDirectory, approvedRoot: approvedRoot),
            monitoredRoots: monitoredRoots,
            declaredPrefixes: [evidenceRunDirectory.path],
            baselineSourceDirectory: baselineSourceDirectory
        )
        do {
            try journal.start()
        } catch {
            throw PostSaveEnvironmentError.tripwireUnavailable(String(describing: error))
        }
        self.journal = journal
    }

    public func verifyBaseline() throws -> BaselineVerificationResult {
        try BaselineVerifier.verify(referenceFile: baselineReferenceFile)
    }

    /// Read-only readiness snapshot of the native tripwire journal for the
    /// Phase A report. It never drains the journal, so the pre-dispatch context
    /// record and any later dispatch evidence still receive every fact.
    public func tripwireReadiness() -> PhaseATripwireFacts {
        PhaseATripwireFacts(
            running: journal.isRunning,
            failure: journal.failure,
            collectionGap: journal.collectionGapDetail,
            startedAtMonotonicNanos: journal.startedAtMonotonicNanos,
            factCount: journal.factsSnapshot().count
        )
    }

    public func preDispatchContext(minimumSeconds: Double) async throws -> PreDispatchContextFacts {
        let waitCap = minimumSeconds + 30
        let recordedStart = journal.startedAtMonotonicNanos
        let startedNanos = recordedStart == 0 ? DispatchTime.now().uptimeNanoseconds : recordedStart
        while true {
            if let failure = journal.failure {
                throw PostSaveEnvironmentError.tripwireUnavailable(failure)
            }
            if journal.hasCollectionGap {
                throw PostSaveEnvironmentError.tripwireCollectionGap(
                    journal.collectionGapDetail ?? "dropped FSEvents were reported"
                )
            }
            guard journal.isRunning else {
                throw PostSaveEnvironmentError.tripwireUnavailable("journal is not running")
            }
            let nowNanos = DispatchTime.now().uptimeNanoseconds
            let elapsed = Double(nowNanos - startedNanos) / 1_000_000_000.0
            if elapsed >= minimumSeconds {
                return PreDispatchContextFacts(
                    minimumSeconds: minimumSeconds,
                    observedSeconds: elapsed,
                    journalRunning: true,
                    journalFailure: nil,
                    collectionGap: nil,
                    journalStartedAtMonotonicNanos: journal.startedAtMonotonicNanos,
                    facts: journal.factsSnapshot()
                )
            }
            guard elapsed <= waitCap else {
                throw PostSaveEnvironmentError.tripwireContextWindowFailed(
                    String(format: "context window did not reach %.0fs within the bounded wait", minimumSeconds)
                )
            }
            try? await Task.sleep(nanoseconds: 500_000_000)
        }
    }

    public func preDispatchCensus() async throws -> ChooserCensus {
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: false)
        let snapshots = WindowSensor.snapshots(from: content).filter { $0.ownerPID != nil }
        let processes = censusProcesses(pids: Set(snapshots.compactMap(\.ownerPID)))
        return ChooserCensus(
            windowIDs: snapshots.map(\.windowID).sorted(),
            processes: processes,
            recordedAtMonotonicNanos: DispatchTime.now().uptimeNanoseconds
        )
    }

    /// Plan C7: dropped events or a collector failure after the dispatch
    /// boundary can never become an empty clean tripwire; every post-dispatch
    /// gate refuses on them.
    public func postDispatchTripwireGate() throws {
        guard let detail = journal.postDispatchRefusalDetail() else { return }
        if detail.hasPrefix("collector failure") {
            throw PostSaveEnvironmentError.tripwireUnavailable(detail)
        }
        throw PostSaveEnvironmentError.tripwireCollectionGap(detail)
    }

    public func sampleChooserFacts(preCensus: ChooserCensus) async -> ChooserFactsResult {
        let tripwire = tripwireObservations()
        do {
            try postDispatchTripwireGate()
            let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: false)
            let snapshots = WindowSensor.snapshots(from: content)
            let cgWindows = CGWindowInventory.onScreenWindows()
            var windows: [ChooserWindowFacts] = []
            for snapshot in snapshots {
                guard let pid = snapshot.ownerPID else { continue }
                let inCG = cgWindows.contains { $0.windowNumber == snapshot.windowID }
                let live = ProcessInstanceID.current(pid: pid)
                let postOwner = ChooserProcessFacts(
                    pid: pid,
                    bundleID: snapshot.ownerBundleID,
                    signingIdentity: signingIdentity(pid),
                    startTimeUnix: live.map { Double($0.startTimeSeconds) + Double($0.startTimeMicroseconds) / 1_000_000.0 }
                )
                let preOwner = preCensus.processes.first { $0.pid == pid }
                let reuse = preOwner.map { pre in
                    pre.startTimeUnix != postOwner.startTimeUnix
                        || pre.bundleID != postOwner.bundleID
                        || pre.signingIdentity != postOwner.signingIdentity
                } ?? false
                windows.append(ChooserWindowFacts(
                    windowID: snapshot.windowID,
                    frame: snapshot.frame,
                    onScreen: snapshot.isOnScreen,
                    presentInSCInventory: true,
                    presentInCGInventory: inCG,
                    owner: postOwner,
                    pidReuseDetected: reuse,
                    axNodes: axNodes(pid: pid, frame: snapshot.frame),
                    preDispatchOwner: preOwner,
                    postDispatchOwner: postOwner
                ))
            }
            return .facts(ChooserFacts(
                windows: windows,
                postDispatchCensusPIDs: Set(snapshots.compactMap(\.ownerPID)).sorted(),
                tripwire: tripwire
            ))
        } catch {
            return .failed(String(describing: error), tripwire: tripwire)
        }
    }

    public func dispatchSaveAllClick(
        owner: PersistentTransactionOwner,
        permit: ReadinessPermit,
        binding: SurfaceBinding,
        postHoverRevalidation: @escaping @Sendable () async throws -> Void
    ) async throws {
        try await GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: binding,
            intent: .saveAll(owner),
            postHoverRevalidation: postHoverRevalidation
        )
    }

    public func prepareDestination(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String {
        let observed = try FolderChooserDriver.prepareDestination(
            pid: pid_t(pid),
            expectedProcess: expectedProcess,
            destination: destination,
            owner: owner,
            predicate: predicate,
            candidate: candidate
        )
        return observed.joined(separator: "\n")
    }

    public func confirmDefaultButton(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String {
        try FolderChooserDriver.confirmDefaultButton(
            pid: pid_t(pid),
            expectedProcess: expectedProcess,
            destination: destination,
            owner: owner,
            predicate: predicate,
            candidate: candidate
        )
    }

    public func postConfirmationFacts(chooserWindowIDs: [UInt32], stagingDirectory: URL) async -> PostConfirmationFacts? {
        let tripwire = tripwireObservations()
        do {
            try postDispatchTripwireGate()
            let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: false)
            let snapshots = WindowSensor.snapshots(from: content)
            let stillOnScreen = snapshots.contains { chooserWindowIDs.contains($0.windowID) && $0.isOnScreen }
            let snapshot = try StagingVerifier.snapshot(directory: stagingDirectory)
            return PostConfirmationFacts(chooserWindowStillOnScreen: stillOnScreen, stagingSnapshot: snapshot, tripwire: tripwire)
        } catch {
            return nil
        }
    }

    public func stagingSnapshot(directory: URL) throws -> StagingSnapshot {
        try StagingVerifier.snapshot(directory: directory)
    }

    public func tripwireCollectionGapDisclosure() -> String? {
        journal.postDispatchRefusalDetail()
    }

    public func tripwireObservations() -> [TripwireClassification] {
        journal.drain().map(\.classification)
    }

    public func markDispatchBoundary() {
        journal.markDispatchBoundary()
    }

    public func monotonicNow() -> Double {
        Double(DispatchTime.now().uptimeNanoseconds) / 1_000_000_000.0
    }

    public func sleep(seconds: Double) async {
        try? await Task.sleep(nanoseconds: UInt64(max(0, seconds) * 1_000_000_000))
    }

    private func censusProcesses(pids: Set<Int32>) -> [ChooserProcessFacts] {
        pids.sorted().map { pid in
            let live = ProcessInstanceID.current(pid: pid)
            let bundleID = NSRunningApplication(processIdentifier: pid_t(pid))?.bundleIdentifier
            return ChooserProcessFacts(
                pid: pid,
                bundleID: bundleID,
                signingIdentity: signingIdentity(pid),
                startTimeUnix: live.map { Double($0.startTimeSeconds) + Double($0.startTimeMicroseconds) / 1_000_000.0 }
            )
        }
    }

    private func axNodes(pid: Int32, frame: CGRect) -> [AXNodeDump] {
        for window in AXDriver.windows(ofApp: pid_t(pid)) {
            guard let windowFrame = AXDriver.frame(of: window) else { continue }
            let delta = abs(windowFrame.origin.x - frame.origin.x) + abs(windowFrame.origin.y - frame.origin.y)
            if delta <= 4, abs(windowFrame.width - frame.width) <= 4, abs(windowFrame.height - frame.height) <= 4 {
                return AXDriver.dump(element: window, pid: pid, maxDepth: 12).nodes
            }
        }
        return []
    }
}
