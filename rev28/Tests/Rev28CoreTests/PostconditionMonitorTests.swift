import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

final class PostconditionMonitorTests: XCTestCase {
    private final class LockedClock: @unchecked Sendable {
        private let lock = NSLock()
        private var value: Double

        init(_ value: Double = 0) {
            self.value = value
        }

        func now() -> Double {
            lock.lock()
            defer { lock.unlock() }
            return value
        }

        func advance(_ seconds: Double) {
            lock.lock()
            value += max(0, seconds)
            lock.unlock()
        }
    }

    private final class LockedCounter: @unchecked Sendable {
        private let lock = NSLock()
        private var value = 0

        func next() -> Int {
            lock.lock()
            defer { lock.unlock() }
            value += 1
            return value
        }
    }

    private func affirmation(_ id: UInt32 = 77) -> ChooserAffirmation {
        ChooserAffirmation(
            windowID: id,
            frame: CGRect(x: 10, y: 20, width: 300, height: 240),
            ownerPID: 4242,
            predicateID: "unit-test",
            affirmedAtISO8601: "2026-09-25T00:00:00Z"
        )
    }

    func testAffirmationBeforeHardCapIsVerified() async {
        let clock = LockedClock()
        let counter = LockedCounter()
        let expected = affirmation()
        let bounds = PostconditionBounds(
            fastCadenceMs: 100,
            fastPhaseSeconds: 0.5,
            slowCadenceMs: 200,
            hardCapSeconds: 1.0,
            lateForensicSampleDelaySeconds: 0.3
        )

        let outcome = await PostconditionMonitor.run(
            bounds: bounds,
            sampler: {
                counter.next() >= 3
                    ? PostconditionSample(affirmed: expected)
                    : .notAffirmed
            },
            monotonicNow: { clock.now() },
            sleep: { clock.advance($0) }
        )

        XCTAssertEqual(outcome, .chooserVerified(expected))
    }

    func testSamplerThatReturnsAffirmationAfterHardCapIsClassifiedLate() async {
        let clock = LockedClock()
        let expected = affirmation(88)
        let bounds = PostconditionBounds(
            fastCadenceMs: 100,
            fastPhaseSeconds: 0.5,
            slowCadenceMs: 200,
            hardCapSeconds: 1.0,
            lateForensicSampleDelaySeconds: 0.3
        )

        let outcome = await PostconditionMonitor.run(
            bounds: bounds,
            sampler: {
                // Models a ScreenCaptureKit/AX sampling call that began inside
                // the window but only returned affirmative evidence after it.
                clock.advance(1.1)
                return PostconditionSample(affirmed: expected)
            },
            monotonicNow: { clock.now() },
            sleep: { clock.advance($0) }
        )

        guard case let .chooserObservedAfterWindow(count, seconds, observed) = outcome else {
            return XCTFail("expected chooserObservedAfterWindow, got \(outcome)")
        }
        XCTAssertEqual(count, 1)
        XCTAssertGreaterThan(seconds, 1.0)
        XCTAssertEqual(observed, expected)
    }

    func testNoChooserProducesTimeoutAfterSingleForensicSample() async {
        let clock = LockedClock()
        let bounds = PostconditionBounds(
            fastCadenceMs: 100,
            fastPhaseSeconds: 0.5,
            slowCadenceMs: 200,
            hardCapSeconds: 1.0,
            lateForensicSampleDelaySeconds: 0.3
        )

        let outcome = await PostconditionMonitor.run(
            bounds: bounds,
            sampler: { .notAffirmed },
            monotonicNow: { clock.now() },
            sleep: { clock.advance($0) }
        )

        guard case let .noChooserObserved(count, seconds) = outcome else {
            return XCTFail("expected noChooserObserved, got \(outcome)")
        }
        XCTAssertGreaterThan(count, 1)
        XCTAssertGreaterThanOrEqual(seconds, 1.3)
    }

    func testLateForensicAffirmationIsNamedAfterWindow() async {
        let clock = LockedClock()
        let expected = affirmation(99)
        let bounds = PostconditionBounds(
            fastCadenceMs: 100,
            fastPhaseSeconds: 0.5,
            slowCadenceMs: 200,
            hardCapSeconds: 1.0,
            lateForensicSampleDelaySeconds: 0.3
        )

        let outcome = await PostconditionMonitor.run(
            bounds: bounds,
            sampler: {
                clock.now() >= 1.2
                    ? PostconditionSample(affirmed: expected)
                    : .notAffirmed
            },
            monotonicNow: { clock.now() },
            sleep: { clock.advance($0) }
        )

        guard case let .chooserObservedAfterWindow(_, seconds, observed) = outcome else {
            return XCTFail("expected chooserObservedAfterWindow, got \(outcome)")
        }
        XCTAssertGreaterThan(seconds, 1.0)
        XCTAssertEqual(observed, expected)
    }


    func testStrictMonitorNamesSingleLateForensicAffirmation() async {
        let clock = LockedClock()
        let counter = LockedCounter()
        let expected = affirmation(123)
        let bounds = PostconditionBounds(
            fastCadenceMs: 100,
            fastPhaseSeconds: 0.2,
            slowCadenceMs: 100,
            hardCapSeconds: 0.3,
            lateForensicSampleDelaySeconds: 0.2
        )
        let verdict = await StrictPostconditionMonitor.run(
            bounds: bounds,
            sampler: {
                let n = counter.next()
                return .observed(StrictPostconditionSample(
                    affirmation: n >= 4 ? expected : nil,
                    tripwireObservations: []
                ))
            },
            monotonicNow: { clock.now() },
            sleep: { clock.advance($0) }
        )
        guard case let .chooserObservedAfterWindow(observed, _, tripwire) = verdict else {
            return XCTFail("expected late forensic chooser, got \(verdict)")
        }
        XCTAssertEqual(observed, expected)
        XCTAssertEqual(tripwire, [])
    }

    func testStrictMonitorReturnsAtDeadlineWhenSamplerStalls() async {
        let bounds = PostconditionBounds(
            fastCadenceMs: 10, fastPhaseSeconds: 0.02, slowCadenceMs: 10,
            hardCapSeconds: 0.04, lateForensicSampleDelaySeconds: 30
        )
        let verdict = await StrictPostconditionMonitor.run(bounds: bounds, sampler: {
            try? await Task.sleep(nanoseconds: 500_000_000)
            return .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: []))
        })
        guard case .deadlineExceeded(sampleCount: 0, tripwire: []) = verdict else {
            return XCTFail("expected bounded deadline result, got \(verdict)")
        }
    }

    func testStrictMonitorDistinguishesObserverFailureAndTripwireAbort() async {
        let failure = await StrictPostconditionMonitor.run(sampler: { .failed("AX unavailable", tripwireObservations: []) })
        guard case .observerFailed("AX unavailable", sampleCount: 1, tripwire: []) = failure else {
            return XCTFail("expected explicit observer failure, got \(failure)")
        }

        let aborted = TripwireClassification(
            level: .l2ApprovedRoot,
            outcome: .abortedUnattributedFilesystemWrite,
            aborts: true,
            path: "/approved/unattributed",
            rationale: "test"
        )
        let verdict = await StrictPostconditionMonitor.run(sampler: {
            .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: [aborted]))
        })
        guard case .tripwireAborted(sampleCount: 1, tripwire: [aborted]) = verdict else {
            return XCTFail("expected terminal tripwire abort, got \(verdict)")
        }
    }
}
