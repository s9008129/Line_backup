import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

extension NativeObservationSessionTests {
    func testAutomaticOcrAnchorsValidateNativeSckToCuaTransform() throws {
        let native = NativeCaptureBounds(cuaCaptureBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            sckWindowBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            displayBoundsPoints: CGRect(x: 0, y: 0, width: 1000, height: 800),
            cuaSizePixels: CGSize(width: 1000, height: 800), sckSizePixels: CGSize(width: 2000, height: 1600))
        let cua = [ocrItem("Group", CGRect(x: 90, y: 90, width: 20, height: 20)),
                   ocrItem("Album", CGRect(x: 790, y: 90, width: 20, height: 20)),
                   ocrItem("Save All", CGRect(x: 290, y: 690, width: 20, height: 20))]
        let sck = [ocrItem("Group", CGRect(x: 290, y: 290, width: 20, height: 20)),
                   ocrItem("Album", CGRect(x: 990, y: 290, width: 20, height: 20)),
                   ocrItem("Save All", CGRect(x: 490, y: 890, width: 20, height: 20))]
        let result = try AutomaticOcrAnchorMapper.derive(cua: cua, sck: sck, native: native)
        XCTAssertEqual(result.anchors.count, 3)
        XCTAssertEqual(result.scaleX, 1, accuracy: 0.0001)
        XCTAssertEqual(result.scaleY, 1, accuracy: 0.0001)
        XCTAssertEqual(result.offsetX, 200, accuracy: 0.0001)
        XCTAssertEqual(result.offsetY, 200, accuracy: 0.0001)
        XCTAssertLessThanOrEqual(result.maximumResidualSourcePixels, 2)
        XCTAssertEqual(result.uncertaintyPixels, 2)
    }

    func testAutomaticOcrAnchorsRejectDuplicatesAndBadResidual() throws {
        let native = NativeCaptureBounds(cuaCaptureBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            sckWindowBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            displayBoundsPoints: CGRect(x: 0, y: 0, width: 1000, height: 800),
            cuaSizePixels: CGSize(width: 1000, height: 800), sckSizePixels: CGSize(width: 2000, height: 1600))
        let cua = [ocrItem("Group", CGRect(x: 90, y: 90, width: 20, height: 20)),
                   ocrItem("Album", CGRect(x: 790, y: 90, width: 20, height: 20)),
                   ocrItem("Save All", CGRect(x: 290, y: 690, width: 20, height: 20))]
        let sck = [ocrItem("Group", CGRect(x: 290, y: 290, width: 20, height: 20)),
                   ocrItem("Album", CGRect(x: 990, y: 290, width: 20, height: 20)),
                   ocrItem("Save All", CGRect(x: 490, y: 890, width: 20, height: 20)),
                   ocrItem("Group", CGRect(x: 590, y: 590, width: 20, height: 20))]
        XCTAssertThrowsError(try AutomaticOcrAnchorMapper.derive(cua: cua, sck: sck, native: native)) {
            XCTAssertEqual($0 as? AutomaticAnchorMappingError, .insufficientUniqueAnchors)
        }
        let displaced = [sck[0], sck[1], ocrItem("Save All", CGRect(x: 510, y: 890, width: 20, height: 20))]
        XCTAssertThrowsError(try AutomaticOcrAnchorMapper.derive(cua: cua, sck: displaced, native: native)) {
            guard let mapped = $0 as? AutomaticAnchorMappingError else { return XCTFail("unexpected error: \($0)") }
            if case .residualTooLarge = mapped { return }
            XCTFail("unexpected error: \(mapped)")
        }
    }

    func testExplicitV3ValidSessionReturnsExactLogicalSetAndCountsOnce() async throws {
        let source = ExplicitSessionFakeSource()
        let session = NativeObservationSession(sessionID: "explicit-synthetic-session", source: source, ocr: FakeOcr())
        let bundle = try await session.capture(ExplicitLineTestFixture.request())
        XCTAssertEqual(source.capturedWindows, ExplicitLineTestFixture.windows)
        XCTAssertFalse(source.capturedConfiguration!.includeChildWindows)
        XCTAssertEqual(bundle.explicitLineRequestBinding, ExplicitLineTestFixture.binding)
        XCTAssertNoThrow(try bundle.validated())
        let count = await session.captureCount
        XCTAssertEqual(count, 1)
    }

    func testExplicitV3MalformedRetainedBindingsCannotReturnOrCountSuccess() async throws {
        typealias F = ExplicitLineTestFixture
        let transforms: [(CapturedFrameRecord) throws -> CapturedFrameRecord] = [
            { var f = $0; f.explicitLineSelectionWitness = nil; return f },
            { var f = $0; f.explicitLineSelectionWitness?.selectedWindowIDs = [10]; return f },
            { var f = $0; f.explicitLineSelectionWitness?.effectiveSourceRect = F.main.frame; return f },
            { var f = $0; f.explicitLineSelectionWitness?.includeChildWindows = true; return f },
            { var f = $0; f.explicitLineSelectionWitness?.includeMenuBar = true; return f },
            { var f = $0; f.explicitLineSelectionWitness?.pointPixelScale = 2; return f },
            { try F.mutateFrame($0) { $0["stateKey"] = "wrong-state" } },
            { try F.mutateFrame($0) { var c = $0["configuration"] as! [String: Any]; c.removeValue(forKey: "sourceRect"); $0["configuration"] = c } },
            { try F.mutateFrame($0) { var c = $0["configuration"] as! [String: Any]; c["ignoreClipping"] = true; $0["configuration"] = c } },
            { try F.mutateFrame($0) {
                $0["captureKind"] = "window"; $0.removeValue(forKey: "explicitLineSelectionWitness")
                $0["configuration"] = try! JSONSerialization.jsonObject(with: EvidenceIO.encodeJSON(CaptureConfiguration.primaryWindow))
            } }
        ]
        for (index, transform) in transforms.enumerated() {
            let source = ExplicitSessionFakeSource(); source.transform = transform
            let session = NativeObservationSession(sessionID: "explicit-negative-\(index)", source: source, ocr: FakeOcr())
            do { _ = try await session.capture(F.request()); XCTFail("invalid v3 source returned successful bundle: \(index)") }
            catch { XCTAssertTrue(error is ObservationRefusal, "\(error)") }
            XCTAssertEqual(source.captureCalls, 1)
            let count = await session.captureCount
            XCTAssertEqual(count, 0)
        }
    }

    func testExplicitV3OriginalRequestAndTemporalDriftRefuseBeforeSuccess() async throws {
        typealias F = ExplicitLineTestFixture
        var wrongRequest = F.binding; wrongRequest.configuration = .childUnion
        var wrongState = F.binding; wrongState.geometryState.activated = false
        for binding in [nil, wrongRequest, wrongState] as [ExplicitLineRequestBinding?] {
            let source = ExplicitSessionFakeSource()
            let session = NativeObservationSession(sessionID: "explicit-request-negative", source: source, ocr: FakeOcr())
            do { _ = try await session.capture(F.request(binding: binding)); XCTFail("invalid original request accepted") } catch {}
            XCTAssertEqual(source.captureCalls, 0)
            let count = await session.captureCount; XCTAssertEqual(count, 0)
        }
        // Coherent B/B is still different from the frozen A/A selection.
        let source = ExplicitSessionFakeSource()
        source.fake.preInventoryOverride = [F.main, F.changedChild(id: 12)]
        source.fake.postInventoryOverride = source.fake.preInventoryOverride
        let session = NativeObservationSession(sessionID: "explicit-aa-bb-negative", source: source, ocr: FakeOcr())
        do { _ = try await session.capture(F.request()); XCTFail("coherent replacement B/B accepted") } catch {}
        let count = await session.captureCount; XCTAssertEqual(count, 0)
        let postDrift = ExplicitSessionFakeSource(); postDrift.fake.postInventoryOverride = [F.main, F.changedChild(layer: 9)]
        let second = NativeObservationSession(sessionID: "explicit-post-drift", source: postDrift, ocr: FakeOcr())
        do { _ = try await second.capture(F.request()); XCTFail("post layer drift accepted") } catch {}
        let secondCount = await second.captureCount; XCTAssertEqual(secondCount, 0)
    }

    func testExplicitV3ValidationDeadlineStillPrecedesCompletionCount() async throws {
        let source = ExplicitSessionFakeSource(); source.expireAtFinalValidation = true
        let session = NativeObservationSession(sessionID: "explicit-deadline", source: source, ocr: FakeOcr())
        do { _ = try await session.capture(ExplicitLineTestFixture.request()); XCTFail("validation deadline ignored") }
        catch { XCTAssertEqual(error as? ObservationRefusal, .deadlineExceeded(stage: "validation")) }
        let count = await session.captureCount; XCTAssertEqual(count, 0)
    }
}

extension ExplicitLineTestFixture {
    static func request(binding: ExplicitLineRequestBinding? = ExplicitLineTestFixture.binding) -> NativeObservationRequest {
        NativeObservationRequest(runID: "explicit-v3-synthetic", state: .appReady, target: target, configuration: .explicitLineWindows,
            geometryState: state, localization: .none, observationBudgetNanos: 5_000_000_000, explicitLineRequestBinding: binding)
    }
    static func bundle() async throws -> ObservationBundle {
        try await NativeObservationSession(sessionID: "explicit-v3-synthetic-session", source: ExplicitSessionFakeSource(), ocr: FakeOcr()).capture(request())
    }
}

/// Local source seam retains valid process/signing/AX/CG/PNG/epoch facts while
/// malformed v3 fields exercise the actual session's successful-return boundary.
final class ExplicitSessionFakeSource: @unchecked Sendable, ObservationSource {
    let fake = FakeObservationSource(window: ExplicitLineTestFixture.main, bundleID: "jp.naver.line.mac", pid: 4242)
    var transform: ((CapturedFrameRecord) throws -> CapturedFrameRecord)?
    var expireAtFinalValidation = false
    var capturedWindows: [SCWindowSnapshot] = []
    var capturedConfiguration: CaptureConfiguration?
    var captureCalls = 0
    private var clockCalls = 0
    init() { fake.preInventoryOverride = ExplicitLineTestFixture.windows; fake.postInventoryOverride = ExplicitLineTestFixture.windows }
    func enumerateWindows() async throws -> [SCWindowSnapshot] { try await fake.enumerateWindows() }
    func cgInventory() -> [CGWindowSnapshot] { fake.cgInventory() }
    func captureTarget(window: SCWindowSnapshot, includedWindows: [SCWindowSnapshot], configuration: CaptureConfiguration,
                       geometryState: CaptureGeometryState, epoch: UInt64) async throws -> ObservationCapturedImage {
        capturedWindows = includedWindows; capturedConfiguration = configuration; captureCalls += 1
        let frame = ExplicitLineTestFixture.frame(epoch: epoch)
        return ObservationCapturedImage(image: ExplicitLineTestFixture.image, record: try transform?(frame) ?? frame)
    }
    func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead { try fake.readAXIdentity(pid: pid, windowID: windowID) }
    func processInstance(pid: Int32) throws -> ProcessInstanceID { try fake.processInstance(pid: pid) }
    func signingIdentity(pid: Int32) throws -> String? { try fake.signingIdentity(pid: pid) }
    func nextEpoch() -> UInt64 { fake.nextEpoch() }
    func monotonicNanos() -> UInt64 {
        clockCalls += 1
        return fake.monotonicNanos() + (expireAtFinalValidation && clockCalls >= 5 ? 5_000_000_001 : 0)
    }
}

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
        var invalidFrameExpectedBBox: CGRect?
        var captureError: Error?
        var captureClockAdvance: UInt64 = 0
        var onCaptureStart: (@Sendable () async -> Void)?
        var axIdentityOverride: AXIdentityRead?
        var postProcessOverride: ProcessInstanceID?
        var postSigningOverride: String?
        var postSigningUnavailable = false
        var signingUnavailable = false
        var postIdentityClockAdvance: UInt64 = 0
        var postAXIdentityOverride: AXIdentityRead?
        var postProcessError: Error?
        var postAXError: Error?
        var cgInventorySequence: [[CGWindowSnapshot]]?
        var replaceProcessDuringRead: String?

        private let lock = NSLock()
        private var epochCounter: UInt64 = 0
        private var now: UInt64 = 1_000
        private var enumerateCalls = 0
        private var processCalls = 0
        private var signingCalls = 0
        private var axCalls = 0
        private var cgCalls = 0
        private var currentProcessStart: Int64 = 7

        private func replaceProcess(at point: String) {
            lock.lock()
            defer { lock.unlock() }
            if replaceProcessDuringRead == point { currentProcessStart = 8 }
        }

        var cgReadCount: Int {
            lock.lock()
            defer { lock.unlock() }
            return cgCalls
        }

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
            if call == 1 { replaceProcess(at: "preInventory") }
            return call == 1 ? (preInventoryOverride ?? [window]) : (postInventoryOverride ?? [window])
        }

        func cgInventory() -> [CGWindowSnapshot] {
            lock.lock()
            cgCalls += 1
            let call = cgCalls
            lock.unlock()
            replaceProcess(at: "cgInventory")
            if let sequence = cgInventorySequence, !sequence.isEmpty {
                return sequence[min(call - 1, sequence.count - 1)]
            }
            return cgInventoryOverride ?? [
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
                expectedBBoxPt: invalidFrameExpectedBBox ?? window.frame,
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
                validity: invalidFrameExpectedBBox == nil ? .valid : .invalid,
                violations: invalidFrameExpectedBBox == nil ? [] : ["injected-size-mismatch"],
                identity: nil
            )
            return ObservationCapturedImage(image: image, record: record)
        }

        func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead {
            lock.lock()
            axCalls += 1
            let call = axCalls
            lock.unlock()
            if call > 1 {
                replaceProcess(at: "postAX")
                if let postAXError { throw postAXError }
                if let postAXIdentityOverride { return postAXIdentityOverride }
            }
            return axIdentityOverride ?? AXIdentityRead(
                role: "AXWindow",
                subrole: "AXStandardWindow",
                title: "LINE",
                matchMethod: .windowNumber
            )
        }

        func processInstance(pid: Int32) throws -> ProcessInstanceID {
            lock.lock()
            processCalls += 1
            let call = processCalls
            if call > 1 { now += postIdentityClockAdvance }
            let start = currentProcessStart
            lock.unlock()
            if call > 1 {
                if let postProcessError { throw postProcessError }
                if let postProcessOverride { return postProcessOverride }
            }
            return ProcessInstanceID(pid: pid, startTimeSeconds: start, startTimeMicroseconds: 0)
        }

        func signingIdentity(pid: Int32) throws -> String? {
            lock.lock()
            signingCalls += 1
            let call = signingCalls
            lock.unlock()
            if signingUnavailable { return nil }
            if call > 1 {
                replaceProcess(at: "postSigning")
                if postSigningUnavailable { return nil }
                if let postSigningOverride { return postSigningOverride }
            }
            return "Developer ID Application: Fake (ABCDE12345)"
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
        var onRecognize: (@Sendable () -> Void)?

        init(items: [OcrItem] = [], error: Error? = nil) {
            self.items = items
            self.error = error
        }

        func recognize(image: CGImage) async throws -> [OcrItem] {
            onRecognize?()
            if let error { throw error }
            return items
        }
    }

    private struct OcrFailure: Error {}
    private struct IdentityReadFailure: Error {}

    func testProcessReplacementDuringBoundaryReadsIsRefused() async throws {
        // Other native facts stay identical, including PID, signature and
        // window ID. Only the process instance changes inside a source read.
        for point in ["preInventory", "postSigning", "postAX", "cgInventory"] {
            let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
            source.replaceProcessDuringRead = point
            let session = NativeObservationSession(sessionID: "replacement-\(point)", source: source, ocr: FakeOcr())
            do {
                _ = try await session.capture(makeRequest())
                XCTFail("same-PID replacement during \(point) was accepted")
            } catch {
                guard case .identityMismatch = error as? ObservationRefusal else {
                    return XCTFail("unexpected refusal \(error)")
                }
            }
            let count = await session.captureCount
            XCTAssertEqual(count, 0, point)
        }
    }

    func testPostCaptureProcessSigningAndAXChangesAreRefused() async throws {
        for mode in ["process", "signing", "signingUnavailable", "ax"] {
            let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
            switch mode {
            case "process": source.postProcessOverride = ProcessInstanceID(pid: 4242, startTimeSeconds: 8, startTimeMicroseconds: 0)
            case "signing": source.postSigningOverride = "different-target-signature"
            case "signingUnavailable": source.postSigningUnavailable = true
            default: source.postAXIdentityOverride = AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: "another surface", matchMethod: .windowNumber)
            }
            let session = NativeObservationSession(sessionID: "post-identity-\(mode)", source: source, ocr: FakeOcr())
            do {
                _ = try await session.capture(makeRequest())
                XCTFail("\(mode) changed across capture but was accepted")
            } catch {
                guard case .identityMismatch = error as? ObservationRefusal else {
                    return XCTFail("unexpected refusal \(error)")
                }
            }
            let count = await session.captureCount
            XCTAssertEqual(count, 0)
        }
    }

    func testPostCaptureIdentityReadErrorsAreRefused() async throws {
        for mode in ["process", "ax"] {
            let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
            if mode == "process" { source.postProcessError = IdentityReadFailure() }
            else { source.postAXError = IdentityReadFailure() }
            let session = NativeObservationSession(sessionID: "post-read-error-\(mode)", source: source, ocr: FakeOcr())
            do {
                _ = try await session.capture(makeRequest())
                XCTFail("a failed post identity read was accepted")
            } catch {
                guard case .observerFailure = error as? ObservationRefusal else {
                    return XCTFail("unexpected refusal \(error)")
                }
            }
            let count = await session.captureCount
            XCTAssertEqual(count, 0)
        }
    }

    func testOneExplicitCGSnapshotIsSharedByIdentityAndBundle() async throws {
        let window = makeWindow()
        let source = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
        let first = CGWindowSnapshot(windowNumber: window.windowID, frame: window.frame, layer: 0, ownerPID: 4242, name: "LINE")
        let later = CGWindowSnapshot(windowNumber: window.windowID, frame: CGRect(x: 500, y: 60, width: 400, height: 600), layer: 0, ownerPID: 4242, name: "LINE")
        source.cgInventorySequence = [[first], [later]]
        let session = NativeObservationSession(sessionID: "one-explicit-cg", source: source, ocr: FakeOcr())
        let bundle = try await session.capture(makeRequest())
        try bundle.validated()
        XCTAssertEqual(source.cgReadCount, 1, "counts explicit source.cgInventory calls, not AX adapter internals")
        XCTAssertEqual(bundle.cgInventory, [first])
        XCTAssertEqual(bundle.window.cgEntry.frame, bundle.cgInventory[0].frame)
    }

    func testCGDuplicateAndInvalidOrDriftedGeometryAreRefused() async throws {
        let window = makeWindow()
        let valid = CGWindowSnapshot(windowNumber: window.windowID, frame: window.frame, layer: 0, ownerPID: 4242, name: "LINE")
        let frames = [
            CGRect(x: 51, y: 60, width: 400, height: 600),
            CGRect(x: CGFloat.nan, y: 60, width: 400, height: 600),
            CGRect(x: 50, y: 60, width: CGFloat.infinity, height: 600),
            CGRect(x: 50, y: 60, width: 0, height: 600),
        ]
        var inventories = [[valid, valid]]
        inventories += frames.map { [CGWindowSnapshot(windowNumber: window.windowID, frame: $0, layer: 0, ownerPID: 4242, name: "LINE")] }
        for (index, inventory) in inventories.enumerated() {
            let source = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
            source.cgInventoryOverride = inventory
            let session = NativeObservationSession(sessionID: "invalid-cg-\(index)", source: source, ocr: FakeOcr())
            do {
                _ = try await session.capture(makeRequest())
                XCTFail("ambiguous or inconsistent CG geometry was accepted: \(index)")
            } catch let refusal as ObservationRefusal {
                guard case .inventoryChanged = refusal else { return XCTFail("unexpected \(refusal)") }
            }
            let count = await session.captureCount
            XCTAssertEqual(count, 0)
        }
    }

    func testCGGeometryWithinExistingHalfPointTolerancePasses() async throws {
        let window = makeWindow()
        let source = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
        source.cgInventoryOverride = [CGWindowSnapshot(windowNumber: window.windowID, frame: CGRect(x: 50.5, y: 60, width: 400, height: 600), layer: 0, ownerPID: 4242, name: "LINE")]
        let session = NativeObservationSession(sessionID: "cg-tolerance", source: source, ocr: FakeOcr())
        let bundle = try await session.capture(makeRequest())
        try bundle.validated()
    }

    func testStableUnavailableSigningRemainsUnknown() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.signingUnavailable = true
        let session = NativeObservationSession(sessionID: "unknown-signing", source: source, ocr: FakeOcr())
        let bundle = try await session.capture(makeRequest())
        try bundle.validated()
        XCTAssertNil(bundle.signingIdentity)
        XCTAssertNil(bundle.postSigningIdentity)
        XCTAssertEqual(bundle.process, bundle.postProcess)
    }

    func testPostIdentityReadDoesNotExtendAbsoluteDeadline() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.postIdentityClockAdvance = 2_000
        let session = NativeObservationSession(sessionID: "post-identity-deadline", source: source, ocr: FakeOcr())
        do {
            _ = try await session.capture(makeRequest(budget: 1_500))
            XCTFail("post identity read time cannot extend the original deadline")
        } catch {
            guard case .deadlineExceeded = error as? ObservationRefusal else { return XCTFail("unexpected \(error)") }
        }
        let count = await session.captureCount
        XCTAssertEqual(count, 0)
    }

    func testConflictingDuplicateSCKWindowIDIsRefused() async throws {
        let window = makeWindow()
        let conflict = SCWindowSnapshot(windowID: window.windowID, frame: window.frame, windowLayer: 0, title: "another owner", isOnScreen: true, ownerPID: 9999, ownerBundleID: "another.application", ownerName: "another")
        let source = FakeObservationSource(window: window, bundleID: "jp.naver.line.mac", pid: 4242)
        source.postInventoryOverride = [window, conflict]
        let session = NativeObservationSession(sessionID: "duplicate-sck-id", source: source, ocr: FakeOcr())
        do {
            _ = try await session.capture(makeRequest())
            XCTFail("a duplicated ID with conflicting ownership is not a coherent inventory")
        } catch {
            guard case .inventoryChanged = error as? ObservationRefusal else { return XCTFail("unexpected \(error)") }
        }
        let count = await session.captureCount
        XCTAssertEqual(count, 0)
    }

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

    func testInvalidFrameRefusalPreservesRecordedDimensionsWithoutCompletingCapture() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        // Scripted record fault, not an OS capture: expected width is 93 points
        // wider than the 400-pixel image at record scale 1. The independent
        // scale remains distinct so diagnostics cannot silently conflate them.
        source.invalidFrameExpectedBBox = CGRect(x: 50, y: 60, width: 493, height: 600)
        let session = NativeObservationSession(sessionID: "invalid-frame-dimensions", source: source, ocr: FakeOcr())
        do {
            _ = try await session.capture(makeRequest())
            XCTFail("an invalid frame must still refuse")
        } catch let refusal as ObservationRefusal {
            guard case .invalidFrameGeometry(let details) = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
            XCTAssertEqual(details.first, "injected-size-mismatch")
            let description = refusal.description
            XCTAssertTrue(description.contains("recordedFrameGeometry("), description)
            XCTAssertTrue(description.contains("imagePx=[w=400,h=600]"), description)
            XCTAssertTrue(description.contains("expectedPt=[w=493.0,h=600.0]"), description)
            XCTAssertTrue(description.contains("pointPixelScale=1.0"), description)
            XCTAssertTrue(description.contains("backingScaleFactor=2.0"), description)
        }
        let captureCount = await session.captureCount
        XCTAssertEqual(captureCount, 0, "diagnostic numbers cannot make an invalid frame successful")
    }

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

    /// Plan C3: an AX read that cannot name its window binding is not evidence
    /// about the observed window and must refuse the whole observation.
    func testUnboundAXIdentityIsRefused() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        source.axIdentityOverride = AXIdentityRead(role: "AXWindow", subrole: nil, title: nil)
        let session = NativeObservationSession(sessionID: "session-unbound-ax", source: source, ocr: FakeOcr())

        do {
            let bundle = try await session.capture(makeRequest())
            try bundle.validated()
            XCTFail("an unbound AX read must refuse, not count as window evidence")
        } catch let refusal as ObservationRefusal {
            guard case .identityMismatch(let details) = refusal else {
                return XCTFail("unexpected refusal \(refusal)")
            }
            XCTAssertTrue(details.contains { $0.contains("not bound to the target window") }, "\(details)")
        }
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

    func testDeadlineIncludesOcrAndRejectsOverflowOrZeroBudget() async throws {
        let source = FakeObservationSource(window: makeWindow(), bundleID: "jp.naver.line.mac", pid: 4242)
        let ocr = FakeOcr()
        ocr.onRecognize = { source.advanceClock(by: 2_000) }
        let session = NativeObservationSession(sessionID: "ocr-deadline", source: source, ocr: ocr)
        do {
            _ = try await session.capture(makeRequest(budget: 1_500))
            XCTFail("OCR cannot extend the capture deadline")
        } catch {
            XCTAssertEqual(error as? ObservationRefusal, .deadlineExceeded(stage: "ocr"))
        }
        for budget in [UInt64(0), UInt64.max] {
            do {
                _ = try await session.capture(makeRequest(budget: budget))
                XCTFail("invalid budget \(budget) must refuse")
            } catch {
                guard case .invalidBundle = error as? ObservationRefusal else {
                    return XCTFail("unexpected \(error)")
                }
            }
        }
        let completed = await session.captureCount
        XCTAssertEqual(completed, 0)
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

extension NativeObservationSessionTests {
    private func albumSupportBinding() -> AlbumSupportNativeBinding {
        AlbumSupportNativeBinding(bundleId: "jp.naver.line.mac", pid: 42, windowId: 7, displayId: 1,
            cuaCaptureBoundsPoints: [100, 100, 500, 400], sckWindowBoundsPoints: [100, 100, 500, 400],
            displayBoundsPoints: [0, 0, 1000, 800], cuaSizePx: [1000, 800], sckSizePx: [2000, 1600])
    }

    private func albumSupportMeasure(point: CGPoint, menu: [Double], addressable: [Double],
                                     row: CGRect = CGRect(x: 500, y: 500, width: 100, height: 40),
                                     uncertainty: Double = 2)
        -> Result<AlbumSupportEvaluation.CaptureMeasurement, AlbumSupportRefusal> {
        guard let mapping = AlbumSupportMapping(binding: albumSupportBinding()) else {
            return .failure(.mapUnavailable)
        }
        return AlbumSupportEvaluation.measureCapture(sckItems: [ocrItem(AlbumSupportEvaluation.saveAllText, row)],
            mapping: mapping, menuBoundsCuaPx: menu, addressableBoundsCuaPx: addressable,
            saveAllPointCuaPx: point, uncertaintyPx: uncertainty)
    }

    func testAlbumSupportGeometryMarginRefusesBelowUncertaintyPlusFour() throws {
        let menu: [Double] = [300, 300, 100, 40], addressable: [Double] = [300, 300, 100, 40]
        switch albumSupportMeasure(point: CGPoint(x: 305, y: 320), menu: menu, addressable: addressable) {
        case .success: XCTFail("a 5 px margin must refuse below uncertainty 2 + 4")
        case let .failure(error): XCTAssertEqual(error, .safeMarginBelowUncertainty(marginPx: 5, requiredPx: 6))
        }
        switch albumSupportMeasure(point: CGPoint(x: 306, y: 320), menu: menu, addressable: addressable) {
        case let .success(value): XCTAssertEqual(value.safeMarginPx, 6, accuracy: 0.0001)
        case let .failure(error): XCTFail("a 6 px margin must pass: \(error)")
        }
    }

    func testAlbumSupportGeometryIntersectionRefusesUnderSixteenPixels() throws {
        let narrow: [Double] = [300, 300, 15, 40]
        switch albumSupportMeasure(point: CGPoint(x: 306, y: 320), menu: narrow, addressable: narrow) {
        case .success: XCTFail("a 15 px intersection must refuse")
        case let .failure(error): XCTAssertEqual(error, .intersectionBelowMinimum(narrow))
        }
        let minimal: [Double] = [300, 300, 16, 16]
        switch albumSupportMeasure(point: CGPoint(x: 306, y: 320), menu: minimal, addressable: minimal) {
        case let .success(value): XCTAssertEqual(value.interactiveIntersectionPx, minimal)
        case let .failure(error): XCTFail("a 16x16 intersection must pass: \(error)")
        }
    }

    func testAlbumSupportGuardReturnsTheCalibratedPointUnchanged() throws {
        guard let mapping = AlbumSupportMapping(binding: albumSupportBinding()) else { return XCTFail("mapping") }
        let row = ocrItem(AlbumSupportEvaluation.saveAllText, CGRect(x: 500, y: 500, width: 100, height: 40))
        let calibrated = CGPoint(x: 350, y: 320)
        switch AlbumSupportEvaluation.guardPoint(sckItems: [row], mapping: mapping,
            saveAllPointCuaPx: calibrated, uncertaintyPx: 2) {
        case let .success(confirmed):
            XCTAssertEqual(confirmed.x, calibrated.x, accuracy: 0.0001)
            XCTAssertEqual(confirmed.y, calibrated.y, accuracy: 0.0001)
        case let .failure(error): XCTFail("the guard echoed a different point: \(error)")
        }
        // A re-located row center must not be accepted as the calibrated point.
        let center = CGPoint(x: 350, y: 520)
        XCTAssertNotEqual(center.y, calibrated.y, accuracy: 0.0001)
    }

    func testAlbumSupportGuardRefusesAmbiguousOrMissingSaveAllRow() throws {
        guard let mapping = AlbumSupportMapping(binding: albumSupportBinding()) else { return XCTFail("mapping") }
        let row = ocrItem(AlbumSupportEvaluation.saveAllText, CGRect(x: 500, y: 500, width: 100, height: 40))
        switch AlbumSupportEvaluation.guardPoint(sckItems: [row, row], mapping: mapping,
            saveAllPointCuaPx: CGPoint(x: 350, y: 320), uncertaintyPx: 2) {
        case .success: XCTFail("a duplicated Save All row must refuse")
        case let .failure(error): XCTAssertEqual(error, .saveAllRowMissingOrAmbiguous(2))
        }
        switch AlbumSupportEvaluation.guardPoint(sckItems: [], mapping: mapping,
            saveAllPointCuaPx: CGPoint(x: 350, y: 320), uncertaintyPx: 2) {
        case .success: XCTFail("a missing Save All row must refuse")
        case let .failure(error): XCTAssertEqual(error, .saveAllRowMissingOrAmbiguous(0))
        }
    }

    func testSidecarParityResidualIncludesLooseConfidenceAnchors() throws {
        let native = NativeCaptureBounds(cuaCaptureBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            sckWindowBoundsPoints: CGRect(x: 100, y: 100, width: 500, height: 400),
            displayBoundsPoints: CGRect(x: 0, y: 0, width: 1000, height: 800),
            cuaSizePixels: CGSize(width: 1000, height: 800), sckSizePixels: CGSize(width: 2000, height: 1600))
        let cleanCua = [ocrItem("Group", CGRect(x: 90, y: 90, width: 20, height: 20)),
                        ocrItem("Album", CGRect(x: 790, y: 90, width: 20, height: 20)),
                        ocrItem("Save All", CGRect(x: 290, y: 690, width: 20, height: 20))]
        let cleanSck = [ocrItem("Group", CGRect(x: 290, y: 290, width: 20, height: 20)),
                        ocrItem("Album", CGRect(x: 990, y: 290, width: 20, height: 20)),
                        ocrItem("Save All", CGRect(x: 490, y: 890, width: 20, height: 20))]
        XCTAssertNoThrow(try AutomaticOcrAnchorMapper.derive(cua: cleanCua, sck: cleanSck, native: native))
        // The Python authority indexes this low-confidence item too, so a
        // Swift-only confidence filter could accept a capture the authority
        // refuses; parity must refuse it here.
        let loose = OcrItem(text: "Ghost", confidence: 0.2, candidateCount: 1,
            quadCapturePx: [], boundingBoxCapturePx: CGRect(x: 490, y: 390, width: 20, height: 20))
        let looseSck = OcrItem(text: "Ghost", confidence: 0.2, candidateCount: 1,
            quadCapturePx: [], boundingBoxCapturePx: CGRect(x: 0, y: 0, width: 20, height: 20))
        XCTAssertThrowsError(try AutomaticOcrAnchorMapper.derive(cua: cleanCua + [loose], sck: cleanSck + [looseSck], native: native)) {
            guard case .residualTooLarge = $0 as? AutomaticAnchorMappingError else {
                return XCTFail("expected residualTooLarge, got \($0)")
            }
        }
    }
}
