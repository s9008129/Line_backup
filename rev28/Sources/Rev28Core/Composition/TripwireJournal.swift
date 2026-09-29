import CoreServices
import Foundation

// MARK: - Real read-only filesystem tripwire (plan R4 §C7)
//
// A cumulative FSEvents journal over the approved root, ~/Downloads and the
// accepted baseline source. FSEvents carries no writer PID evidence, so this
// collector never invents process attribution: the only attributable events are
// paths the engine itself declared in advance (its evidence/control writes).
// Dropped events, kernel-user drops, root changes or stream errors are recorded
// as first-class health facts; a caller can never turn them into a clean empty
// tripwire. Baseline-protected paths are classified as baseline modifications
// and abort regardless of attribution.

public enum TripwireJournalError: Error, Equatable, CustomStringConvertible {
    case noWatchPaths
    case watchPathMissing(String)
    case declaredSelfPathIsBaseline(String)
    case streamCreationFailed
    case streamStartFailed

    public var description: String {
        switch self {
        case .noWatchPaths: return "noWatchPaths"
        case let .watchPathMissing(path): return "watchPathMissing(\(path))"
        case let .declaredSelfPathIsBaseline(path): return "declaredSelfPathIsBaseline(\(path))"
        case .streamCreationFailed: return "streamCreationFailed"
        case .streamStartFailed: return "streamStartFailed"
        }
    }
}

public struct TripwireJournalHealth: Equatable, Codable, Sendable {
    public let startedAtUptime: Double?
    public let startEventCursor: UInt64
    public let lastEventCursor: UInt64
    public let rawEventCount: Int
    public let droppedEventFlags: Int
    public let streamErrorCount: Int
    public let rootChanged: Bool
    public let eventIDsWrapped: Bool
    public let stopped: Bool

    public var healthy: Bool {
        startedAtUptime != nil && !stopped && droppedEventFlags == 0 && streamErrorCount == 0
            && !rootChanged && !eventIDsWrapped
    }
}

public struct TripwireJournalDrain: Sendable {
    public let events: [TripwireEvent]
    public let classifications: [TripwireClassification]
    public let rawEventCount: Int
    public let droppedEventFlags: Int
    public let streamErrorCount: Int
    public let healthy: Bool
    public let lastEventCursor: UInt64
    public let observedSeconds: Double?

    public init(
        events: [TripwireEvent],
        classifications: [TripwireClassification],
        rawEventCount: Int,
        droppedEventFlags: Int,
        streamErrorCount: Int,
        healthy: Bool,
        lastEventCursor: UInt64,
        observedSeconds: Double?
    ) {
        self.events = events
        self.classifications = classifications
        self.rawEventCount = rawEventCount
        self.droppedEventFlags = droppedEventFlags
        self.streamErrorCount = streamErrorCount
        self.healthy = healthy
        self.lastEventCursor = lastEventCursor
        self.observedSeconds = observedSeconds
    }
}

public final class TripwireJournal: @unchecked Sendable {
    public let scope: TripwireScope
    public let watchPaths: [URL]
    public let declaredSelfPaths: [URL]
    public let baselineProtectedPaths: [URL]

    private let lock = NSLock()
    private let queue = DispatchQueue(label: "rev28.tripwire.journal")
    private var stream: FSEventStreamRef?
    private var pending: [(path: String, eventID: UInt64, flags: UInt32, recordedAt: Double)] = []
    private var startedAtUptime: Double?
    private var startCursor: UInt64 = FSEventStreamEventId(kFSEventStreamEventIdSinceNow)
    private var lastCursor: UInt64 = FSEventStreamEventId(kFSEventStreamEventIdSinceNow)
    private var rawEventCount = 0
    private var droppedEventFlags = 0
    private var streamErrorCount = 0
    private var rootChanged = false
    private var eventIDsWrapped = false
    private var stopped = false
    /// Set by the caller immediately before the irreversible dispatch boundary.
    private var dispatchBoundaryUptime: Double?

    public init(
        scope: TripwireScope,
        watchPaths: [URL],
        declaredSelfPaths: [URL],
        baselineProtectedPaths: [URL]
    ) throws {
        guard !watchPaths.isEmpty else { throw TripwireJournalError.noWatchPaths }
        let canonicalWatch = watchPaths.map { $0.resolvingSymlinksInPath().standardizedFileURL }
        for path in canonicalWatch where !FileManager.default.fileExists(atPath: path.path) {
            throw TripwireJournalError.watchPathMissing(path.path)
        }
        let canonicalSelf = declaredSelfPaths.map { $0.resolvingSymlinksInPath().standardizedFileURL }
        let canonicalBaseline = baselineProtectedPaths.map { $0.resolvingSymlinksInPath().standardizedFileURL }
        for selfPath in canonicalSelf {
            for baseline in canonicalBaseline where Self.isDescendant(selfPath, of: baseline) {
                throw TripwireJournalError.declaredSelfPathIsBaseline(selfPath.path)
            }
        }
        self.scope = scope
        self.watchPaths = canonicalWatch
        self.declaredSelfPaths = canonicalSelf
        self.baselineProtectedPaths = canonicalBaseline
    }

    public func start() throws {
        lock.lock()
        let alreadyStarted = stream != nil
        lock.unlock()
        guard !alreadyStarted else { return }

        var context = FSEventStreamContext(
            version: 0,
            info: Unmanaged.passUnretained(self).toOpaque(),
            retain: nil,
            release: nil,
            copyDescription: nil
        )
        let flags = FSEventStreamCreateFlags(
            kFSEventStreamCreateFlagUseCFTypes
                | kFSEventStreamCreateFlagFileEvents
                | kFSEventStreamCreateFlagWatchRoot
                | kFSEventStreamCreateFlagNoDefer
        )
        let sinceNow = FSEventStreamEventId(kFSEventStreamEventIdSinceNow)
        guard let created = FSEventStreamCreate(
            kCFAllocatorDefault,
            { _, info, numEvents, eventPaths, eventFlags, eventIDs in
                guard let info else { return }
                let journal = Unmanaged<TripwireJournal>.fromOpaque(info).takeUnretainedValue()
                let flagsPointer = eventFlags
                let idsPointer = eventIDs
                let rawPaths = unsafeBitCast(eventPaths, to: NSArray.self) as? [String] ?? []
                journal.record(paths: rawPaths, count: numEvents, flags: flagsPointer, ids: idsPointer)
            },
            &context,
            watchPaths.map(\.path) as CFArray,
            sinceNow,
            0.05,
            flags
        ) else {
            throw TripwireJournalError.streamCreationFailed
        }
        lock.lock()
        stream = created
        startCursor = FSEventsGetCurrentEventId()
        lastCursor = startCursor
        startedAtUptime = ProcessInfo.processInfo.systemUptime
        stopped = false
        lock.unlock()

        FSEventStreamSetDispatchQueue(created, queue)
        guard FSEventStreamStart(created) else {
            lock.lock()
            stream = nil
            startedAtUptime = nil
            streamErrorCount += 1
            lock.unlock()
            FSEventStreamInvalidate(created)
            FSEventStreamRelease(created)
            throw TripwireJournalError.streamStartFailed
        }
    }

    public func stop() {
        lock.lock()
        let current = stream
        stream = nil
        stopped = startedAtUptime != nil
        lock.unlock()
        guard let current else { return }
        FSEventStreamStop(current)
        FSEventStreamInvalidate(current)
        FSEventStreamRelease(current)
    }

    public func health() -> TripwireJournalHealth {
        lock.lock()
        defer { lock.unlock() }
        return TripwireJournalHealth(
            startedAtUptime: startedAtUptime,
            startEventCursor: startCursor,
            lastEventCursor: lastCursor,
            rawEventCount: rawEventCount,
            droppedEventFlags: droppedEventFlags,
            streamErrorCount: streamErrorCount,
            rootChanged: rootChanged,
            eventIDsWrapped: eventIDsWrapped,
            stopped: stopped
        )
    }

    /// Marks the irreversible dispatch boundary: later drains are post-dispatch.
    /// The first mark wins; a second call is a no-op.
    @discardableResult
    public func markDispatchBoundary() -> Double {
        lock.lock()
        defer { lock.unlock() }
        if let existing = dispatchBoundaryUptime { return existing }
        let now = ProcessInfo.processInfo.systemUptime
        dispatchBoundaryUptime = now
        return now
    }

    /// Plan C7 pre-dispatch context gate: the journal must have been streaming
    /// for at least `minimumSeconds`, with no drops, root changes or errors.
    public func preDispatchContextSatisfied(minimumSeconds: Double) -> Bool {
        lock.lock()
        let started = startedAtUptime
        let healthy = started != nil && !stopped && droppedEventFlags == 0 && streamErrorCount == 0
            && !rootChanged && !eventIDsWrapped
        lock.unlock()
        guard healthy, let started else { return false }
        let elapsed = ProcessInfo.processInfo.systemUptime - started
        guard elapsed >= minimumSeconds else { return false }
        markDispatchBoundary()
        return true
    }

    /// Drains accumulated raw events, classifies them against the frozen ladder
    /// and returns the classified facts plus health evidence. An unhealthy
    /// journal still returns the classifications already observed; the caller
    /// must treat `healthy == false` as a collector failure, never as a clean
    /// empty tripwire.
    public func drain() -> TripwireJournalDrain {
        lock.lock()
        let drained = pending
        pending = []
        let boundary = dispatchBoundaryUptime
        let rawCount = rawEventCount
        let dropped = droppedEventFlags
        let errors = streamErrorCount
        let stoppedNow = stopped
        let rootChangedNow = rootChanged
        let wrapped = eventIDsWrapped
        let started = startedAtUptime
        let cursor = lastCursor
        lock.unlock()

        let events = drained.map { raw -> TripwireEvent in
            let path = URL(fileURLWithPath: raw.path)
            let phase: TripwirePhase = (boundary.map { raw.recordedAt >= $0 } ?? false) ? .postDispatch : .preDispatch
            let selfAttributed = declaredSelfPaths.contains { Self.isDescendant(path, of: $0) }
            let modifiesBaseline = baselineProtectedPaths.contains { Self.isDescendant(path, of: $0) }
            return TripwireEvent(
                path: path,
                phase: phase,
                attributableToThisRun: selfAttributed,
                modifiesAcceptedBaseline: modifiesBaseline,
                writerPID: nil,
                notes: selfAttributed
                    ? "declared-in-advance engine control/evidence path"
                    : "fsevents path evidence only; no process attribution is claimed"
            )
        }
        let classifications = events.map { TripwireClassifier.classify(event: $0, scope: scope) }
        let healthy = started != nil && !stoppedNow && dropped == 0 && errors == 0 && !rootChangedNow && !wrapped
        return TripwireJournalDrain(
            events: events,
            classifications: classifications,
            rawEventCount: rawCount,
            droppedEventFlags: dropped,
            streamErrorCount: errors,
            healthy: healthy,
            lastEventCursor: cursor,
            observedSeconds: started.map { max(0, ProcessInfo.processInfo.systemUptime - $0) }
        )
    }

    // MARK: - FSEvents callback ingestion

    fileprivate func record(paths: [String], count: Int, flags: UnsafePointer<FSEventStreamEventFlags>, ids: UnsafePointer<FSEventStreamEventId>) {
        let now = ProcessInfo.processInfo.systemUptime
        var newDrops = 0
        var newErrors = 0
        var sawRootChange = false
        var sawWrap = false
        var entries: [(String, UInt64, UInt32, Double)] = []
        for index in 0..<count {
            let flag = flags[index]
            if flag & FSEventStreamEventFlags(kFSEventStreamEventFlagUserDropped) != 0
                || flag & FSEventStreamEventFlags(kFSEventStreamEventFlagKernelDropped) != 0
                || flag & FSEventStreamEventFlags(kFSEventStreamEventFlagMustScanSubDirs) != 0 {
                newDrops += 1
            }
            if flag & FSEventStreamEventFlags(kFSEventStreamEventFlagRootChanged) != 0 { sawRootChange = true }
            if flag & FSEventStreamEventFlags(kFSEventStreamEventFlagEventIdsWrapped) != 0 { sawWrap = true }
            if flag & FSEventStreamEventFlags(kFSEventStreamEventFlagMount) != 0
                || flag & FSEventStreamEventFlags(kFSEventStreamEventFlagUnmount) != 0 {
                newErrors += 1
            }
            guard index < paths.count else { continue }
            entries.append((paths[index], ids[index], UInt32(truncatingIfNeeded: flag), now))
        }
        lock.lock()
        pending.append(contentsOf: entries.map { (path: $0.0, eventID: $0.1, flags: $0.2, recordedAt: $0.3) })
        rawEventCount += entries.count
        droppedEventFlags += newDrops
        streamErrorCount += newErrors
        rootChanged = rootChanged || sawRootChange
        eventIDsWrapped = eventIDsWrapped || sawWrap
        if count > 0 { lastCursor = max(lastCursor, ids[count - 1]) }
        lock.unlock()
    }

    private static func isDescendant(_ url: URL, of parent: URL) -> Bool {
        let child = url.standardizedFileURL.path
        let root = parent.standardizedFileURL.path
        if root == "/" { return child.hasPrefix("/") }
        return child == root || child.hasPrefix(root.hasSuffix("/") ? root : root + "/")
    }
}
