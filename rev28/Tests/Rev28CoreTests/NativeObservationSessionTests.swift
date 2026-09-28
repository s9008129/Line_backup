import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

final class NativeObservationSessionTests: XCTestCase {
    // MARK: - Fakes (substitutions stay below perception/predicate/state decisions)

    private final class FakeObservationSource: @unchecked Sendable, ObservationSource {
        let bundleID: String
        let pid: Int32
        let window: SCWindowSnapshot
        var preInventoryOverride: [SCWindowSnapshot]?
        var postInventoryOverride: [SCWindowSnapshot]?
        var cgInventoryOverride: [CGWindowSnapshot]?
        var recordImageSHAOverride: String?
        var captureError: Error?
        var captureClockAdvance: UInt64 = 0
        var onCaptureStart: (@Sendable () async -> Void)?

        private let lock = NSLock()
        private var epochCounter: UInt64 = 0
        private var now: UInt64 = 1_000
        private var enumerateCalls = 0

        init(window: SCWindowSnapshot, bundleID: String, pid: Int32) {
            self.window = window
            self.bundleID = bundleID
            self.pid = pid
        }

        func advanceClock(by delta: UInt64) {
            lock.lock()
            now += delta
            lock.unlock()
        }

        func enumerateWindows() async throws -> [SCWindowSnapshot] {
            lock.lock()
            enumerateCalls += 1
            let call = enumerateCalls
            lock.unlock()
            return call == 1 ? (preInventoryOverride ?? [window]) : (postInventoryOverride ?? [window])
        }

        func cgInventory() -> [CGWindowSnapshot] {
            cgInventoryOverride ?? [
                CGWindowSnapshot(windowNumber: window.windowID, frame: window.frame, layer: 0, ownerPID: pid, name: window.title)
            ]
        }

        func captureTarget(
            window: SCWindowSnapshot,
            includedWindows: [SCWindowSnapshot],
            configuration: CaptureConfiguration,
            geometryState: CaptureGeometryState,
            epoch: UInt64
        ) async throws -> ObservationCapturedImage {
            if let onCaptureStart { await onCaptureStart() }
            lock.lock()
            now += captureClockAdvance
            lock.unlock()
            if let captureError { throw captureError }
            let image = Self.makeImage(width: 400, height: 600)
            let sha = recordImageSHAOverride ?? FrameCaptureSupport.pngSHA256(of: image)!
            let record = CapturedFrameRecord(
                captureKind: configuration.kind,
                configuration: configuration,
                includedWindows: includedWindows,
                expectedBBoxPt: window.frame,
                imageWidthPx: image.width,
                imageHeightPx: image.height,
                actualBBoxPt: window.frame,
                perSideSizeDeltaPt: .zero,
                scale: 1,
                scaleSource: .pointPixelScale,
                backingScaleFactor: 2,
                epoch: epoch,
                capturedAtISO8601: "2026-09-29T00:00:00.000Z",
                imageSHA256: sha,
                stateKey: "SETTLED_ACTIVATED",
                validity: .valid,
                violations: [],
                identity: nil
            )
            return ObservationCapturedImage(image: image, record: record)
        }

        func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead {
            AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: "LINE")
        }

        func processInstance(pid: Int32) throws -> ProcessInstanceID {
            ProcessInstanceID(pid: pid, startTimeSeconds: 7, startTimeMicroseconds: 0)
        }

        func signingIdentity(pid: Int32) throws -> String? {
            "Developer ID Application: Fake (ABCDE12345)"
        }

        func nextEpoch() -> UInt64 {
            lock.lock()
            defer { lock.unlock() }
            epochCounter += 1
            return epochCounter
        }

        func monotonicNanos() -> UInt64 {
            lock.lock()
            defer { lock.unlock() }
            return now
        }

        static func makeImage(width: Int, height: Int) -> CGImage {
            let context = CGContext(
                data: nil,
                width: width,
                height: height,
                bitsPerComponent: 8,
                bytesPerRow: width * 4,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            )!
            context.setFillColor(CGColor(red: 0.2, green: 0.3, blue: 0.4, alpha: 1))
            context.fill(CGRect(x: 0, y: 0, width: width, height: height))
            return context.makeImage()!
        }
    }

    private final class FakeOcr: @unchecked Sendable, OcrPerforming {
        var items: [OcrItem]
        var error: Error?

        init(items: [OcrItem] = [], error: Error? = nil) {
            self.items = items
            self.error = error
        }

        func recognize(image: CGImage) async throws -> [OcrItem] {
            if let error { throw error }
            return items
        }
    }

    private struct OcrFailure: Error {}

    private func makeWindow() -> SCWindowSnapshot {
        SCWindowSnapshot(
            windowID: 10,
            frame: CGRect(x: 50, y: 60, width: 400, height: 600),
            windowLayer: 0,
            title: "LINE",
            isOnScreen: true,
            ownerPID: 4242,
            ownerBundleID: "jp.naver.line.mac",
            ownerName: "LINE"
        )
    }

    private func makeRequest(
        localization: ObservationLocalization = .none,
        budget: UInt64 = 1_000_000
    ) -> NativeObservationRequest {
        NativeObservationRequest(
            runID: "run-1",
            state: .appReady,
            target: ObservationTarget(bundleID: "jp.naver.line.mac", pid: 4242),
            configuration: .primaryWindow,
            geometryState: CaptureGeometryState(settled: true, activated: true, includeChildWindows: false, ignoreShadows: true),
            localization: localization,
            observationBudgetNanos: budget
        )
    }

    private func ocrItem(_ text: String, _ box: CGRect) -> OcrItem {
        OcrItem(
            text: text,
            confidence: 0.99,
            candidateCount: 1,
            quadCapturePx: [
                CapturePixelPoint(x: box.minX, y: box.minY),
                CapturePixelPoint(x: box.maxX, y: box.minY),
                CapturePixelPoint(x: box.minX, y: box.maxY),
                CapturePixelPoint(x: box.maxX, y: box.maxY),
            ],
            boundingBoxCapturePx: box
        )
    }

    // MARK: - Tests

    func testCaptureProducesValidatedBundleFromRetainedImage() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let ocr = FakeOcr(items: [ocrItem("LINE", CGRect(x: 10, y: 10, width: 40, height: 12))])
        let session = NativeObservationSession(sessionID: "session-1", source: source, ocr: ocr)

        let bundle = try await session.capture(makeRequest())

        try bundle.validated()
        XCTAssertEqual(bundle.runID, "run-1")
        XCTAssertEqual(bundle.state, .appReady)
        XCTAssertEqual(bundle.epoch, 1)
        XCTAssertEqual(bundle.window.captureImageSHA256, bundle.frame.imageSHA256)
        XCTAssertEqual(EvidenceIO.sha256Hex(bundle.framePNGData), bundle.frame.imageSHA256)
        XCTAssertEqual(bundle.ocrSourceImageSHA256, bundle.frame.imageSHA256)
        XCTAssertEqual(bundle.ocrItems.count, 1)
        XCTAssertNil(bundle.candidate)
        XCTAssertNil(bundle.candidateRefusal)
        let captureCount = await session.captureCount
        XCTAssertEqual(captureCount, 1)
    }

    func testObserverAndOcrFailuresNeverBecomeEmptySuccess() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let ocr = FakeOcr(error: OcrFailure())
        let session = NativeObservationSession(sessionID: "session-2", source: source, ocr: ocr)

        do {
            _ = try await session.capture(makeRequest())
            XCTFail("an OCR failure must refuse, not produce an empty observation")
        } catch let refusal as ObservationRefusal {
            guard case .observerFailure(let stage, _) = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
            XCTAssertEqual(stage, "ocr")
        }
        let captureCount = await session.captureCount
        XCTAssertEqual(captureCount, 0)
    }

    func testRetainedImageHashMismatchIsRefused() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.recordImageSHAOverride = String(repeating: "0", count: 64)
        let session = NativeObservationSession(sessionID: "session-3", source: source, ocr: FakeOcr())

        do {
            _ = try await session.capture(makeRequest())
            XCTFail("a record hash that does not describe the retained bytes must refuse")
        } catch let refusal as ObservationRefusal {
            guard case .retainedImageMismatch = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
        }
    }

    func testInventoryChangeAndWindowMultiplicityAreRefused() async throws {
        let window = makeWindow()
        let source = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
        source.postInventoryOverride = []
        let session = NativeObservationSession(sessionID: "session-4", source: source, ocr: FakeOcr())
        do {
            _ = try await session.capture(makeRequest())
            XCTFail("target window disappearance must refuse")
        } catch let refusal as ObservationRefusal {
            guard case .inventoryChanged = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
        }

        let ambiguous = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
        ambiguous.preInventoryOverride = [window, window]
        let ambiguousSession = NativeObservationSession(sessionID: "session-5", source: ambiguous, ocr: FakeOcr())
        do {
            _ = try await ambiguousSession.capture(makeRequest())
            XCTFail("window multiplicity must refuse")
        } catch let refusal as ObservationRefusal {
            guard case .targetWindowNotUnique(let found) = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
            XCTAssertEqual(found, 2)
        }
    }

    func testDeadlineBreachIsRefusedAfterCapture() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.captureClockAdvance = 2_000
        let session = NativeObservationSession(sessionID: "session-6", source: source, ocr: FakeOcr())

        do {
            _ = try await session.capture(makeRequest(budget: 1_500))
            XCTFail("a capture that overshoots its deadline must refuse")
        } catch let refusal as ObservationRefusal {
            guard case .deadlineExceeded = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
        }
    }

    func testConcurrentCaptureOnOneSessionIsRefused() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let gate = CaptureGate()
        source.onCaptureStart = { await gate.hold() }
        let session = NativeObservationSession(sessionID: "session-7", source: source, ocr: FakeOcr())

        let first = Task { try await session.capture(makeRequest()) }
        await gate.waitUntilEntered()
        do {
            _ = try await session.capture(makeRequest())
            XCTFail("a second concurrent capture must be refused")
        } catch let refusal as ObservationRefusal {
            guard case .sessionBusy = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
        }
        await gate.release()
        _ = try await first.value
        let captureCount = await session.captureCount
        XCTAssertEqual(captureCount, 1)
    }

    func testLocalizationRefusalIsRecordedAsTypedRefusal() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let ocr = FakeOcr(items: [ocrItem("無關文字", CGRect(x: 10, y: 10, width: 60, height: 14))])
        let session = NativeObservationSession(sessionID: "session-8", source: source, ocr: ocr)

        let bundle = try await session.capture(
            makeRequest(localization: .albumCards(title: "2024/05/13~05/17", count: "57"))
        )
        try bundle.validated()
        XCTAssertNil(bundle.candidate)
        // No date anchor at all: the segmenter cannot prove card containers.
        XCTAssertEqual(bundle.candidateRefusal, .unsafeGeometry)

        // With an anchor but no exact title/count association the refusal is a
        // missing identity, still typed and recorded.
        let anchoredOcr = FakeOcr(items: [ocrItem("2024/05/13~05/17", CGRect(x: 20, y: 100, width: 140, height: 20))])
        let anchoredSession = NativeObservationSession(sessionID: "session-8b", source: source, ocr: anchoredOcr)
        let anchored = try await anchoredSession.capture(
            makeRequest(localization: .albumCards(title: "2024/05/13~05/17", count: "57"))
        )
        try anchored.validated()
        XCTAssertNil(anchored.candidate)
        XCTAssertEqual(anchored.candidateRefusal, .missingIdentity)
    }

    func testAlbumCardLocalizationBindsCandidateToBundleEpoch() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let ocr = FakeOcr(items: [
            ocrItem("2024/05/13~05/17", CGRect(x: 20, y: 100, width: 140, height: 20)),
            ocrItem("57", CGRect(x: 20, y: 130, width: 30, height: 16)),
            ocrItem("2024/04/01~04/10", CGRect(x: 20, y: 300, width: 140, height: 20)),
        ])
        let session = NativeObservationSession(sessionID: "session-9", source: source, ocr: ocr)

        let bundle = try await session.capture(
            makeRequest(localization: .albumCards(title: "2024/05/13~05/17", count: "57"))
        )
        try bundle.validated()
        let candidate = try XCTUnwrap(bundle.candidate)
        XCTAssertTrue(candidate.identity.hasSuffix(":2024/05/13~05/17|57"))
        XCTAssertEqual(candidate.binding, bundle.surfaceBinding)
        XCTAssertEqual(candidate.binding.captureEpoch, bundle.epoch)
        XCTAssertNil(bundle.candidateRefusal)
        XCTAssertTrue(bundle.cardRegions.count >= 2)
    }
}

/// A one-shot async gate so the concurrency test can observe an in-flight capture.
private actor CaptureGate {
    private var entered = false
    private var enteredWaiters: [CheckedContinuation<Void, Never>] = []
    private var releaseContinuation: CheckedContinuation<Void, Never>?

    func hold() async {
        entered = true
        for waiter in enteredWaiters { waiter.resume() }
        enteredWaiters = []
        await withCheckedContinuation { continuation in
            releaseContinuation = continuation
        }
    }

    func waitUntilEntered() async {
        if entered { return }
        await withCheckedContinuation { continuation in
            enteredWaiters.append(continuation)
        }
    }

    func release() {
        releaseContinuation?.resume()
        releaseContinuation = nil
    }
}
