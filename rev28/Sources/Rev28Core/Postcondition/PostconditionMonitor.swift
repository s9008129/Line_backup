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
            if let affirmation = sample.affirmed {
                return .chooserVerified(affirmation)
            }
            let elapsed = monotonicNow() - start
            if elapsed >= bounds.hardCapSeconds {
                // Plan §10 outcome routing: affirmative first observed only after
                // the hard cap (the single late forensic sample) ->
                // CHOOSER_OBSERVED_AFTER_WINDOW; no affirmative by the hard cap ->
                // NO_CHOOSER_OBSERVED (scoped indeterminate, no retry).
                let lateDelay = bounds.lateForensicSampleDelaySeconds
                await sleep(lateDelay)
                let lateSample = await sampler()
                sampleCount += 1
                if let affirmation = lateSample.affirmed {
                    return .chooserObservedAfterWindow(
                        sampleCount: sampleCount,
                        lateSampleSeconds: monotonicNow() - start,
                        affirmation: affirmation
                    )
                }
                return .noChooserObserved(
                    sampleCount: sampleCount,
                    observedSeconds: monotonicNow() - start
                )
            }
            let cadence = Double(bounds.cadenceMilliseconds(atElapsedSeconds: elapsed)) / 1000.0
            await sleep(min(cadence, max(0.001, bounds.hardCapSeconds - elapsed)))
        }
    }
}
