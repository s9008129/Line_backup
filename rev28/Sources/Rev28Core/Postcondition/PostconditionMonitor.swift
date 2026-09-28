import CoreGraphics
import Foundation

// MARK: - Save All postcondition (plan §ARCHITECTURE §10)
//
// One bounded observation window at a single evidence standard, cadence
// <= 150 ms for the first 8.0 s and <= 500 ms up to the hard cap 15.0 s. The
// affirmative evidence is a chooser surface satisfying the frozen
// chooser-affirmation predicate, directly observed inside the window; unified
// logs / panel-process presence / menu disappearance / click-return are never
// sufficient. Plan-time bounds are re-frozen by W2 calibration (>= 20 measured
// real NSOpenPanel rounds) and bound by review 4; a hard cap that calibration
// shows to be insufficient is a replan, never a silent extension.

public struct PostconditionBounds: Equatable, Codable, Sendable {
    public var fastCadenceMs: Int
    public var fastPhaseSeconds: Double
    public var slowCadenceMs: Int
    public var hardCapSeconds: Double
    /// After the hard cap the monitor keeps exactly one late ledger sample
    /// (forensic) at this delay, then ends.
    public var lateForensicSampleDelaySeconds: Double

    public init(
        fastCadenceMs: Int,
        fastPhaseSeconds: Double,
        slowCadenceMs: Int,
        hardCapSeconds: Double,
        lateForensicSampleDelaySeconds: Double
    ) {
        self.fastCadenceMs = fastCadenceMs
        self.fastPhaseSeconds = fastPhaseSeconds
        self.slowCadenceMs = slowCadenceMs
        self.hardCapSeconds = hardCapSeconds
        self.lateForensicSampleDelaySeconds = lateForensicSampleDelaySeconds
    }

    public static let planTime = PostconditionBounds(
        fastCadenceMs: 150,
        fastPhaseSeconds: 8.0,
        slowCadenceMs: 500,
        hardCapSeconds: 15.0,
        lateForensicSampleDelaySeconds: 30.0
    )

    public func cadenceMilliseconds(atElapsedSeconds elapsed: Double) -> Int {
        elapsed < fastPhaseSeconds ? fastCadenceMs : slowCadenceMs
    }
}

public struct ChooserAffirmation: Equatable, Codable, Sendable {
    public let windowID: UInt32
    public let frame: CGRect
    public let ownerPID: Int32
    public let predicateID: String
    public let affirmedAtISO8601: String

    public init(windowID: UInt32, frame: CGRect, ownerPID: Int32, predicateID: String, affirmedAtISO8601: String) {
        self.windowID = windowID
        self.frame = frame
        self.ownerPID = ownerPID
        self.predicateID = predicateID
        self.affirmedAtISO8601 = affirmedAtISO8601
    }
}

public enum PostconditionOutcome: Equatable, Codable, Sendable {
    case chooserVerified(ChooserAffirmation)
    case noChooserObserved(sampleCount: Int, observedSeconds: Double)
    case chooserObservedAfterWindow(sampleCount: Int, lateSampleSeconds: Double, affirmation: ChooserAffirmation?)
}

public struct PostconditionSample: Sendable {
    public let affirmed: ChooserAffirmation?
    public let note: String?

    public init(affirmed: ChooserAffirmation?, note: String? = nil) {
        self.affirmed = affirmed
        self.note = note
    }

    public static let notAffirmed = PostconditionSample(affirmed: nil)
}

public enum PostconditionMonitorError: Error, CustomStringConvertible {
    case samplerFailed(String)

    public var description: String {
        switch self {
        case let .samplerFailed(reason): return "samplerFailed(\(reason))"
        }
    }
}

public enum PostconditionMonitor {
    /// Runs the bounded observation window. Each sample is verdict-eligible;
    /// the sampler itself owns capture/AX/CG evidence collection.
    ///
    /// The deadline is evaluated *after* each sampler call. This is important:
    /// a slow ScreenCaptureKit/AX sample can start before the hard cap and return
    /// after it. Such an affirmation is late evidence and must never be promoted
    /// to `chooserVerified`.
    public static func run(
        bounds: PostconditionBounds,
        sampler: @escaping @Sendable () async -> PostconditionSample,
        monotonicNow: @escaping @Sendable () -> Double = {
            Double(DispatchTime.now().uptimeNanoseconds) / 1_000_000_000.0
        },
        sleep: @escaping @Sendable (Double) async -> Void = { seconds in
            try? await Task.sleep(nanoseconds: UInt64(max(0, seconds) * 1_000_000_000))
        }
    ) async -> PostconditionOutcome {
        let start = monotonicNow()
        var sampleCount = 0

        while true {
            let sample = await sampler()
            sampleCount += 1
            let elapsed = max(0, monotonicNow() - start)

            if let affirmation = sample.affirmed {
                if elapsed <= bounds.hardCapSeconds {
                    return .chooserVerified(affirmation)
                }
                return .chooserObservedAfterWindow(
                    sampleCount: sampleCount,
                    lateSampleSeconds: elapsed,
                    affirmation: affirmation
                )
            }

            if elapsed >= bounds.hardCapSeconds {
                // Plan §10 outcome routing: affirmative first observed only after
                // the hard cap (the single late forensic sample) ->
                // CHOOSER_OBSERVED_AFTER_WINDOW; no affirmative by the hard cap ->
                // NO_CHOOSER_OBSERVED (scoped indeterminate, no retry).
                await sleep(bounds.lateForensicSampleDelaySeconds)
                let lateSample = await sampler()
                sampleCount += 1
                let lateElapsed = max(0, monotonicNow() - start)
                if let affirmation = lateSample.affirmed {
                    return .chooserObservedAfterWindow(
                        sampleCount: sampleCount,
                        lateSampleSeconds: lateElapsed,
                        affirmation: affirmation
                    )
                }
                return .noChooserObserved(
                    sampleCount: sampleCount,
                    observedSeconds: lateElapsed
                )
            }

            let cadence = Double(bounds.cadenceMilliseconds(atElapsedSeconds: elapsed)) / 1000.0
            await sleep(min(cadence, max(0.001, bounds.hardCapSeconds - elapsed)))
        }
    }
}

public struct StrictPostconditionSample: Sendable {
    public let affirmation: ChooserAffirmation?
    public let tripwireObservations: [TripwireClassification]

    public init(affirmation: ChooserAffirmation?, tripwireObservations: [TripwireClassification]) {
        self.affirmation = affirmation
        self.tripwireObservations = tripwireObservations
    }
}

public enum StrictPostconditionVerdict: Equatable, Sendable {
    case chooserVerified(ChooserAffirmation, sampleCount: Int, tripwire: [TripwireClassification])
    case noChooserObserved(sampleCount: Int, tripwire: [TripwireClassification])
    case chooserObservedAfterWindow(ChooserAffirmation, sampleCount: Int, tripwire: [TripwireClassification])
    case tripwireAborted(sampleCount: Int, tripwire: [TripwireClassification])
    case observerFailed(String, sampleCount: Int, tripwire: [TripwireClassification])
    case deadlineExceeded(sampleCount: Int, tripwire: [TripwireClassification])
}

public enum StrictPostconditionObservation: Sendable {
    case observed(StrictPostconditionSample)
    case failed(String, tripwireObservations: [TripwireClassification])
}

private final class AsyncRaceBox<Value>: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: CheckedContinuation<Value?, Never>?
    private var resolved = false
    private var operationTask: Task<Void, Never>?
    private var timerTask: Task<Void, Never>?

    init(_ continuation: CheckedContinuation<Value?, Never>) { self.continuation = continuation }

    func register(operationTask: Task<Void, Never>, timerTask: Task<Void, Never>) {
        lock.lock()
        if resolved {
            operationTask.cancel()
            timerTask.cancel()
        } else {
            self.operationTask = operationTask
            self.timerTask = timerTask
        }
        lock.unlock()
    }

    func resolve(_ value: Value?, fromOperation: Bool) {
        lock.lock()
        guard !resolved else { lock.unlock(); return }
        resolved = true
        let continuation = self.continuation
        self.continuation = nil
        let taskToCancel = fromOperation ? timerTask : operationTask
        operationTask = nil
        timerTask = nil
        lock.unlock()
        taskToCancel?.cancel()
        continuation?.resume(returning: value)
    }
}

private func valueBeforeDeadline<T: Sendable>(
    seconds: Double,
    operation: @escaping @Sendable () async -> T
) async -> T? {
    await withCheckedContinuation { continuation in
        let box = AsyncRaceBox<T>(continuation)
        let operationTask = Task.detached { box.resolve(await operation(), fromOperation: true) }
        let timerTask = Task.detached {
            if seconds > 0 { try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000)) }
            box.resolve(nil, fromOperation: false)
        }
        box.register(operationTask: operationTask, timerTask: timerTask)
    }
}

public enum StrictPostconditionMonitor {
    public static func run(
        bounds: PostconditionBounds = .planTime,
        sampler: @escaping @Sendable () async -> StrictPostconditionObservation,
        monotonicNow: @escaping @Sendable () -> Double = {
            Double(DispatchTime.now().uptimeNanoseconds) / 1_000_000_000.0
        },
        sleep: @escaping @Sendable (Double) async -> Void = { seconds in
            try? await Task.sleep(nanoseconds: UInt64(max(0, seconds) * 1_000_000_000))
        }
    ) async -> StrictPostconditionVerdict {
        let start = monotonicNow()
        let deadline = start + bounds.hardCapSeconds
        var sampleCount = 0
        var latestTripwire: [TripwireClassification] = []
        var nextSampleStart = start
        while monotonicNow() < deadline {
            let wait = nextSampleStart - monotonicNow()
            if wait > 0 { await sleep(min(wait, max(0, deadline - monotonicNow()))) }
            let sampleStart = monotonicNow()
            guard sampleStart < deadline else { break }
            let remaining = deadline - sampleStart
            guard let result = await valueBeforeDeadline(seconds: remaining, operation: sampler) else {
                return .deadlineExceeded(sampleCount: sampleCount, tripwire: latestTripwire)
            }
            sampleCount += 1
            switch result {
            case let .failed(error, tripwire):
                return .observerFailed(error, sampleCount: sampleCount, tripwire: tripwire)
            case let .observed(sample):
                latestTripwire = sample.tripwireObservations
                if sample.tripwireObservations.contains(where: { $0.aborts }) {
                    return .tripwireAborted(sampleCount: sampleCount, tripwire: latestTripwire)
                }
                let completed = monotonicNow()
                if let affirmation = sample.affirmation {
                    return completed <= deadline
                        ? .chooserVerified(affirmation, sampleCount: sampleCount, tripwire: latestTripwire)
                        : .chooserObservedAfterWindow(affirmation, sampleCount: sampleCount, tripwire: latestTripwire)
                }
                let cadence = Double(bounds.cadenceMilliseconds(atElapsedSeconds: sampleStart - start)) / 1000.0
                nextSampleStart = sampleStart + cadence
                if completed >= deadline {
                    return .deadlineExceeded(sampleCount: sampleCount, tripwire: latestTripwire)
                }
            }
        }
        return .noChooserObserved(sampleCount: sampleCount, tripwire: latestTripwire)
    }
}
