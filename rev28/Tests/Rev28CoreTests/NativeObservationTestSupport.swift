import CoreGraphics
import Foundation
@testable import Rev28Core

/// A scripted LINE surface used by composed tests: OCR text, the retained image
/// and (via `FakeActuationEnvironment`) navigation all change together, so the
/// substitution stays below perception/predicate/state decisions.
final class FakeLineScene: @unchecked Sendable {
    enum Stage {
        case albumList
        case albumDetail
        case menuOpen
    }

    private let lock = NSLock()
    private var stage: Stage = .albumList

    var current: Stage {
        get {
            lock.lock()
            defer { lock.unlock() }
            return stage
        }
        set {
            lock.lock()
            stage = newValue
            lock.unlock()
        }
    }

    var ocrItems: [OcrItem] {
        switch current {
        case .albumList:
            return [
                item(LiveExecutionEngine.targetGroup, CGRect(x: 20, y: 20, width: 160, height: 18)),
                item("2024/05/13~05/17", CGRect(x: 20, y: 100, width: 140, height: 20)),
                item("57", CGRect(x: 20, y: 130, width: 30, height: 16)),
                item("2024/04/01~04/10", CGRect(x: 20, y: 320, width: 140, height: 20)),
            ]
        case .albumDetail:
            return [
                item(LiveExecutionEngine.targetGroup, CGRect(x: 20, y: 20, width: 160, height: 18)),
                item("2024/05/13~05/17", CGRect(x: 20, y: 100, width: 140, height: 20)),
                item("57張照片", CGRect(x: 20, y: 140, width: 100, height: 18)),
            ]
        case .menuOpen:
            let rows = StructuralLocators.lineAlbumMenuReference
            return (0..<rows.count).map { index in
                item(rows[index], CGRect(x: 220, y: 60 + CGFloat(index) * 50, width: 120, height: 24))
            }
        }
    }

    var image: CGImage {
        switch current {
        case .albumList:
            return Self.plainImage()
        case .albumDetail, .menuOpen:
            return Self.imageWithAlbumEllipsis()
        }
    }

    func item(_ text: String, _ box: CGRect) -> OcrItem {
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

    static func plainImage(width: Int = 400, height: Int = 600) -> CGImage {
        let context = makeContext(width: width, height: height)
        context.setFillColor(CGColor(red: 0.92, green: 0.92, blue: 0.94, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        return context.makeImage()!
    }

    /// Three stacked compact dots in the reviewed album-header band above the
    /// title box, so the ellipsis pixel detector finds a unique triple.
    static func imageWithAlbumEllipsis(width: Int = 400, height: Int = 600) -> CGImage {
        let context = makeContext(width: width, height: height)
        context.setFillColor(CGColor(red: 0.92, green: 0.92, blue: 0.94, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        context.setFillColor(CGColor(red: 0.05, green: 0.05, blue: 0.05, alpha: 1))
        for index in 0..<3 {
            context.fill(CGRect(x: 350, y: 50 + index * 5, width: 3, height: 3))
        }
        return context.makeImage()!
    }

    private static func makeContext(width: Int, height: Int) -> CGContext {
        let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        )!
        // Draw in top-left capture coordinates.
        context.translateBy(x: 0, y: CGFloat(height))
        context.scaleBy(x: 1, y: -1)
        return context
    }
}

final class ScriptedOcr: @unchecked Sendable, OcrPerforming {
    let scene: FakeLineScene
    var error: Error?

    init(scene: FakeLineScene) {
        self.scene = scene
    }

    func recognize(image: CGImage) async throws -> [OcrItem] {
        if let error { throw error }
        return scene.ocrItems
    }
}

final class FakeObservationSource: @unchecked Sendable, ObservationSource {
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
    var imageProvider: (@Sendable () -> CGImage)?

    private let lock = NSLock()
    private var epochCounter: UInt64 = 0
    private var now: UInt64 = 1_000
    private var enumerateCalls = 0
    private var captureCountValue = 0

    init(window: SCWindowSnapshot, bundleID: String, pid: Int32) {
        self.window = window
        self.bundleID = bundleID
        self.pid = pid
    }

    var captureCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return captureCountValue
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
        captureCountValue += 1
        lock.unlock()
        if let captureError { throw captureError }
        let image = imageProvider?() ?? FakeLineScene.plainImage()
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
}

final class FakeOcr: @unchecked Sendable, OcrPerforming {
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

final class FakeActuationEnvironment: @unchecked Sendable, ActuationEnvironment {
    var active = true
    var frontmost = true
    var uptimeValue: Double = 100
    var onClick: (@Sendable (String) -> Void)?
    private let lock = NSLock()
    private var posted: [String] = []

    var postedActions: [String] {
        lock.lock()
        defer { lock.unlock() }
        return posted
    }

    func applicationActive(pid: Int32) -> Bool { active }
    func targetFrontmost(pid: Int32) -> Bool { frontmost }
    func uptime() -> Double { uptimeValue }

    func postReversibleClick(
        permit: ReadinessPermit,
        binding: SurfaceBinding,
        owner: PersistentTransactionOwner,
        action: String
    ) throws {
        try owner.recordReversibleDispatch(action: action)
        lock.lock()
        posted.append(action)
        lock.unlock()
        onClick?(action)
    }
}

enum NativeObservationTestWindows {
    static func lineWindow() -> SCWindowSnapshot {
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
}
