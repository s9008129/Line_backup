import CoreServices
import Foundation

// MARK: - Read-only FSEvents tripwire journal (plan C7)
//
// The journal only observes. It records file-level FSEvents under the monitored
// roots, classifies each path with the reviewed attribution ladder, and skips
// the engine's own declared evidence/control paths so the engine's bookkeeping
// is never reported as an unexpected write. Dropped watcher startup, a missing
// root or a stream error is surfaced as journal failure, and the composition
// refuses on journal failure instead of treating an empty journal as a clean
// tripwire.

public struct TripwireJournalFact: Equatable, Codable, Sendable {
    public let classification: TripwireClassification
    public let observedAtISO8601: String

    public init(classification: TripwireClassification, observedAtISO8601: String) {
        self.classification = classification
        self.observedAtISO8601 = observedAtISO8601
    }
}

public final class FilesystemTripwireJournal: @unchecked Sendable {
    private let scope: TripwireScope
    private let monitoredRoots: [URL]
    private let declaredPrefixes: [String]
    private let baselineSourcePrefix: String?
    private let queue = DispatchQueue(label: "rev28.tripwire.fsevents")
    private let lock = NSLock()
    private var facts: [TripwireJournalFact] = []
    private var stream: FSEventStreamRef?
    private var phase: TripwirePhase = .preDispatch
    private var running = false
    private var startupFailure: String?
    private var startedAtNanos: UInt64 = 0
    private var collectionGap: String?

    public init(
        scope: TripwireScope,
        monitoredRoots: [URL],
        declaredPrefixes: [String] = [],
        baselineSourceDirectory: URL? = nil
    ) {
        self.scope = scope
        self.monitoredRoots = monitoredRoots.map { $0.resolvingSymlinksInPath().standardizedFileURL }
        self.declaredPrefixes = declaredPrefixes.map { path in
            let standardized = URL(fileURLWithPath: path).resolvingSymlinksInPath().standardizedFileURL.path
            return standardized.hasSuffix("/") ? standardized : standardized + "/"
        }
        self.baselineSourcePrefix = baselineSourceDirectory
            .map { $0.resolvingSymlinksInPath().standardizedFileURL.path }
    }

    public var isRunning: Bool {
        lock.lock()
        defer { lock.unlock() }
        return running
    }

    public var failure: String? {
        lock.lock()
        defer { lock.unlock() }
        return startupFailure
    }

    /// Monotonic start time of the collector; 0 when it never started.
    public var startedAtMonotonicNanos: UInt64 {
        lock.lock()
        defer { lock.unlock() }
        return startedAtNanos
    }

    /// A dropped-event or rescan gap. The journal keeps observing afterwards,
    /// but a gapped window is never reported as a clean tripwire.
    public var hasCollectionGap: Bool {
        lock.lock()
        defer { lock.unlock() }
        return collectionGap != nil
    }

    /// Plan C7: the refusal detail for a post-dispatch window that is not a
    /// clean tripwire (collector failure, stopped collector or a dropped-event
    /// gap). Nil means the journal window is clean. Never returns "clean" just
    /// because no facts were recorded.
    public func postDispatchRefusalDetail() -> String? {
        lock.lock()
        defer { lock.unlock() }
        if let failure = startupFailure { return "collector failure: \(failure)" }
        guard running else { return "collector is not running after the dispatch boundary" }
        if let collectionGap { return "collection gap: \(collectionGap)" }
        return nil
    }

    /// Test seam: inject a discovered dropped-event/rescan gap so the
    /// post-dispatch refusal gate can be proven without fabricating facts.
    /// Production gaps arrive through the FSEvents callback flags.
    func injectCollectionGapForTesting(_ detail: String) {
        lock.lock()
        if collectionGap == nil { collectionGap = detail }
        lock.unlock()
    }

    public var collectionGapDetail: String? {
        lock.lock()
        defer { lock.unlock() }
        return collectionGap
    }

    /// Cumulative facts observed so far without draining them: the
    /// pre-dispatch context record is a disclosure snapshot, so the
    /// chooser/tripwire evidence still receives the same pre-dispatch facts.
    public func factsSnapshot() -> [TripwireJournalFact] {
        lock.lock()
        defer { lock.unlock() }
        return facts
    }

    /// Records the boundary between the pre-dispatch context window and the
    /// dispatch/observation window. Later events are classified post-dispatch.
    public func markDispatchBoundary() {
        lock.lock()
        phase = .postDispatch
        lock.unlock()
    }

    public func start() throws {
        lock.lock()
        let alreadyRunning = running
        lock.unlock()
        guard !alreadyRunning else { return }
        for root in monitoredRoots where !FileManager.default.fileExists(atPath: root.path) {
            throw TripwireJournalError.rootUnavailable(root.path)
        }
        let paths = monitoredRoots.map(\.path) as CFArray
        var context = FSEventStreamContext(
            version: 0,
            info: Unmanaged.passUnretained(self).toOpaque(),
            retain: nil,
            release: nil,
            copyDescription: nil
        )
        let callback: FSEventStreamCallback = { _, info, numEvents, eventPaths, eventFlags, _ in
            guard let info else { return }
            let journal = Unmanaged<FilesystemTripwireJournal>.fromOpaque(info).takeUnretainedValue()
            let paths = eventPaths.assumingMemoryBound(to: UnsafePointer<CChar>?.self)
            var observed: [String] = []
            var gap: String?
            for index in 0..<numEvents {
                if let raw = paths[index] {
                    observed.append(String(cString: raw))
                }
                let flags = eventFlags[index]
                if flags & FSEventStreamEventFlags(kFSEventStreamEventFlagUserDropped) != 0 {
                    gap = "FSEvents reported user-dropped events"
                } else if flags & FSEventStreamEventFlags(kFSEventStreamEventFlagKernelDropped) != 0 {
                    gap = "FSEvents reported kernel-dropped events"
                } else if flags & FSEventStreamEventFlags(kFSEventStreamEventFlagMustScanSubDirs) != 0 {
                    gap = gap ?? "FSEvents required a subdirectory rescan"
                }
            }
            journal.ingest(paths: observed, gap: gap)
        }
        let flags = UInt32(kFSEventStreamCreateFlagFileEvents | kFSEventStreamCreateFlagWatchRoot)
        guard let stream = FSEventStreamCreate(
            kCFAllocatorDefault,
            callback,
            &context,
            paths,
            FSEventStreamEventId(kFSEventStreamEventIdSinceNow),
            0.1,
            flags
        ) else {
            lock.lock()
            startupFailure = "FSEventStreamCreate failed"
            lock.unlock()
            throw TripwireJournalError.streamCreationFailed
        }
        FSEventStreamSetDispatchQueue(stream, queue)
        guard FSEventStreamStart(stream) else {
            FSEventStreamInvalidate(stream)
            FSEventStreamRelease(stream)
            lock.lock()
            startupFailure = "FSEventStreamStart failed"
            lock.unlock()
            throw TripwireJournalError.streamStartFailed
        }
        lock.lock()
        self.stream = stream
        running = true
        startedAtNanos = DispatchTime.now().uptimeNanoseconds
        lock.unlock()
    }

    public func stop() {
        lock.lock()
        let stream = self.stream
        self.stream = nil
        running = false
        lock.unlock()
        guard let stream else { return }
        FSEventStreamStop(stream)
        FSEventStreamInvalidate(stream)
        FSEventStreamRelease(stream)
    }

    deinit {
        stop()
    }

    /// Returns the classifications recorded since the previous drain and the
    /// wall time of the observation, preserving order.
    public func drain() -> [TripwireJournalFact] {
        lock.lock()
        defer { lock.unlock() }
        let drained = facts
        facts.removeAll()
        return drained
    }

    private func ingest(paths: [String], gap: String?) {
        let stamp = EvidenceIO.iso8601()
        if let gap {
            lock.lock()
            if collectionGap == nil { collectionGap = gap }
            lock.unlock()
        }
        var appended: [TripwireJournalFact] = []
        for path in paths {
            let standardized = URL(fileURLWithPath: path).resolvingSymlinksInPath().standardizedFileURL.path
            if declaredPrefixes.contains(where: { standardized.hasPrefix($0) }) { continue }
            let url = URL(fileURLWithPath: standardized)
            let modifiesBaseline = baselineSourcePrefix.map { standardized == $0 || standardized.hasPrefix($0 + "/") } ?? false
            lock.lock()
            let phase = self.phase
            lock.unlock()
            let event = TripwireEvent(
                path: url,
                phase: phase,
                attributableToThisRun: false,
                modifiesAcceptedBaseline: modifiesBaseline,
                writerPID: nil,
                notes: "fsevents observed path change"
            )
            let classification = TripwireClassifier.classify(event: event, scope: scope)
            appended.append(TripwireJournalFact(classification: classification, observedAtISO8601: stamp))
        }
        guard !appended.isEmpty else { return }
        lock.lock()
        facts.append(contentsOf: appended)
        lock.unlock()
    }
}

public enum TripwireJournalError: Error, Equatable, CustomStringConvertible {
    case rootUnavailable(String)
    case streamCreationFailed
    case streamStartFailed

    public var description: String {
        switch self {
        case let .rootUnavailable(path): return "tripwireRootUnavailable(\(path))"
        case .streamCreationFailed: return "tripwireStreamCreationFailed"
        case .streamStartFailed: return "tripwireStreamStartFailed"
        }
    }
}
