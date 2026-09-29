import CoreGraphics
import CryptoKit
import Darwin
import Foundation
import ImageIO
import UniformTypeIdentifiers
@testable import Rev28Core

// MARK: - Native composition matrix fixture (plan R4 §C2/C5, TEST_ORDER step 4)
//
// Everything below is an injected OS-edge substitution: observations, clock,
// actuation, chooser surface and filesystem are scripted, while the state
// machine, typed evidence store, transaction authority, readiness gate, strict
// postcondition monitor, structural locators and verifiers under test are the
// real Rev28Core implementations. The scripted chooser deliberately bypasses
// predicate evaluation (that path is covered by AdversarialMatrixTests); it can
// only supply observations, never verdicts. No real LINE process, window, AX
// tree, screenshot or event sink is involved anywhere in this fixture.

enum ScriptedCompositionError: Error, CustomStringConvertible {
    case detail(String)
    case primitiveRefused(String)

    var description: String {
        switch self {
        case let .detail(detail): return detail
        case let .primitiveRefused(name): return "scripted primitive refused: \(name)"
        }
    }
}

enum MatrixFrame {
    static let imageWidth = 327
    static let imageHeight = 643
    static let windowID: UInt32 = 55
    static let windowFrame = CGRect(x: 100, y: 100, width: 327, height: 643)
    static let albumTitleBox = CGRect(x: 15, y: 83, width: 189, height: 28)
    static let groupTitleBox = CGRect(x: 15, y: 40, width: 200, height: 26)
    static let albumCountBox = CGRect(x: 30, y: 130, width: 30, height: 20)
    static let photoCountTextBox = CGRect(x: 15, y: 200, width: 90, height: 22)
    static let groupTitle = "旻謙允禎成長日記"
    static let albumTitle = "2024/05/13～05/17"
    static let albumCardCountText = "57"
    static let photoCountText = "57張照片"
    static let bundleID = "jp.naver.line.mac"

    static func menuRowBox(_ index: Int) -> CGRect {
        CGRect(x: 40, y: 300 + Double(index) * 50, width: 140, height: 24)
    }

    static func ocrItem(_ text: String, box: CGRect) -> OcrItem {
        OcrItem(text: text, confidence: 1, candidateCount: 1, quadCapturePx: [], boundingBoxCapturePx: box)
    }

    static func standardOcrItems(
        group: String = groupTitle,
        album: String = albumTitle,
        count: String = albumCardCountText,
        countText: String = photoCountText,
        includeMenuRows: Bool = true
    ) -> [OcrItem] {
        var items = [
            ocrItem(group, box: groupTitleBox),
            ocrItem(album, box: albumTitleBox),
            ocrItem(count, box: albumCountBox),
            ocrItem(countText, box: photoCountTextBox),
        ]
        if includeMenuRows {
            for (index, row) in StructuralLocators.lineAlbumMenuReference.enumerated() {
                items.append(ocrItem(row, box: menuRowBox(index)))
            }
        }
        return items
    }

    /// Synthetic frame with the three stacked ellipsis dots in the reviewed
    /// header band. The bitmap context draws in bottom-left user coordinates,
    /// so `height - 46/-52/-58` stores the 2x2 dots at capture rows 44-57 —
    /// the same top-left rows the reviewed v5 frame records (attempt-07 dots
    /// at cy 44/49.5/55 on a 327x643 capture).
    static func image(withEllipsisDots: Bool = true, height: Int = imageHeight) -> CGImage {
        let colorSpace = CGColorSpaceCreateDeviceGray()
        guard let context = CGContext(
            data: nil,
            width: imageWidth,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: imageWidth,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else { fatalError("matrix frame context unavailable") }
        context.setFillColor(gray: 1, alpha: 1)
        context.fill(CGRect(x: 0, y: 0, width: imageWidth, height: height))
        if withEllipsisDots {
            context.setFillColor(gray: 0, alpha: 1)
            for y in [height - 46, height - 52, height - 58] {
                context.fill(CGRect(x: 304, y: y, width: 2, height: 2))
            }
        }
        guard let image = context.makeImage() else { fatalError("matrix frame image unavailable") }
        return image
    }

    /// Same ImageIO call as FrameCaptureSupport.pngSHA256, so the retained PNG
    /// hash and the session's independent re-encode agree deterministically.
    static func pngData(of image: CGImage) -> Data {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(
            data,
            UTType.png.identifier as CFString,
            1,
            nil
        ) else { fatalError("matrix png destination unavailable") }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { fatalError("matrix png finalize failed") }
        return data as Data
    }

    static func windowIdentity(process: ProcessInstanceID) -> WindowIdentity {
        WindowIdentity(
            bundleID: bundleID,
            process: process,
            windowID: windowID,
            windowFrame: windowFrame,
            ax: AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: "LINE"),
            cgEntry: CGWindowEntryRecord(windowID: windowID, frame: windowFrame, layer: 0, ownerPID: process.pid, ownerName: "LINE"),
            captureEpoch: 0,
            captureImageSHA256: ""
        )
    }

    static func scWindow(
        frame: CGRect = windowFrame,
        bundleID: String = bundleID,
        pid: Int32
    ) -> SCWindowSnapshot {
        SCWindowSnapshot(
            windowID: windowID,
            frame: frame,
            windowLayer: 0,
            title: "LINE",
            isOnScreen: true,
            ownerPID: pid,
            ownerBundleID: bundleID,
            ownerName: "LINE"
        )
    }

    static func cgWindow(frame: CGRect = windowFrame, pid: Int32) -> CGWindowSnapshot {
        CGWindowSnapshot(windowNumber: windowID, frame: frame, layer: 0, ownerPID: pid, name: "LINE")
    }
}

final class ScriptedClock: CompositionClock, @unchecked Sendable {
    private let lock = NSLock()
    private var now: Double
    private var sleeps: [Double] = []

    init(start: Double = 1_000) {
        self.now = start
    }

    func monotonicNow() -> Double {
        lock.lock()
        defer { lock.unlock() }
        return now
    }

    func sleep(seconds: Double) async {
        lock.lock()
        sleeps.append(seconds)
        now += max(0, seconds)
        lock.unlock()
    }

    func advance(by seconds: Double) {
        lock.lock()
        now += seconds
        lock.unlock()
    }

    var recordedSleeps: [Double] {
        lock.lock()
        defer { lock.unlock() }
        return sleeps
    }
}

final class ScriptedObservationBoundary: ObservationBoundary, @unchecked Sendable {
    let processInstance: ProcessInstanceID
    let clock: ScriptedClock

    var captureFailure: Error?
    var invalidFrame = false
    var deadlineExceeded = false
    var omitWindowFromCensus = false
    var censusFrameOverride: CGRect?
    var censusBundleIDOverride: String?
    var signingIdentityValue: String? = "matrix-signing-identity"
    var axRoleValue: String? = "AXWindow"
    var axSubroleValue: String? = "AXStandardWindow"
    var imageProvider: ((String) -> CGImage)?
    var ocrProvider: ((String) -> [OcrItem])?

    private let lock = NSLock()
    private var _captureStates: [String] = []
    private var _lastRequestedState: String?

    init(clock: ScriptedClock, processInstance: ProcessInstanceID) {
        self.clock = clock
        self.processInstance = processInstance
    }

    var captureStates: [String] {
        lock.lock()
        defer { lock.unlock() }
        return _captureStates
    }

    var lastRequestedState: String? {
        lock.lock()
        defer { lock.unlock() }
        return _lastRequestedState
    }

    func inventory() async throws -> ObservationInventorySnapshot {
        lock.lock()
        let omit = omitWindowFromCensus
        let frameOverride = censusFrameOverride
        let bundleOverride = censusBundleIDOverride
        lock.unlock()
        let now = clock.monotonicNow()
        guard !omit else {
            return ObservationInventorySnapshot(scWindows: [], cgWindows: [], sampledAtUptime: now)
        }
        let frame = frameOverride ?? MatrixFrame.windowFrame
        let bundle = bundleOverride ?? MatrixFrame.bundleID
        return ObservationInventorySnapshot(
            scWindows: [MatrixFrame.scWindow(frame: frame, bundleID: bundle, pid: processInstance.pid)],
            cgWindows: [MatrixFrame.cgWindow(frame: frame, pid: processInstance.pid)],
            sampledAtUptime: now
        )
    }

    func capture(
        state: CaptureGeometryState,
        requestedState: String,
        expectedBundleID: String,
        expectedPID: Int32,
        deadlineUptime: Double
    ) async throws -> ObservationCaptureResult {
        lock.lock()
        _captureStates.append(requestedState)
        _lastRequestedState = requestedState
        let failure = captureFailure
        let invalid = invalidFrame
        let expired = deadlineExceeded
        let imageProvider = self.imageProvider
        lock.unlock()
        if let failure { throw failure }
        guard expectedBundleID == MatrixFrame.bundleID, expectedPID == processInstance.pid else {
            throw ScriptedCompositionError.detail("scripted capture expected identity mismatch")
        }
        if expired { clock.advance(by: 60) }
        let image = imageProvider?(requestedState) ?? MatrixFrame.image()
        let png = MatrixFrame.pngData(of: image)
        return ObservationCaptureResult(
            image: image,
            pngData: png,
            configuration: CaptureConfiguration(
                kind: state.includeChildWindows ? .windowUnionWithChildWindows : .window,
                includeChildWindows: state.includeChildWindows,
                ignoreShadows: true,
                ignoreClipping: false,
                showsCursor: false
            ),
            includedWindows: [MatrixFrame.scWindow(pid: processInstance.pid)],
            sourceRect: nil,
            expectedBBoxPt: MatrixFrame.windowFrame,
            actualBBoxPt: MatrixFrame.windowFrame,
            imageWidthPx: image.width,
            imageHeightPx: image.height,
            perSideSizeDeltaPt: .zero,
            scale: 1,
            backingScaleFactor: 1,
            stateKey: CaptureGeometryRules.stateKey(state),
            ruleID: "matrix-frozen-rule",
            ruleSHA256: nil,
            validity: invalid ? .invalid : .valid,
            violations: invalid ? ["matrix-invalid-frame"] : [],
            identityTemplate: MatrixFrame.windowIdentity(process: processInstance)
        )
    }

    func recognize(image: CGImage) async throws -> [OcrItem] {
        lock.lock()
        let state = _lastRequestedState ?? ""
        let provider = ocrProvider
        lock.unlock()
        return provider?(state) ?? MatrixFrame.standardOcrItems()
    }

    func axEvidence(pid: Int32, windowID: UInt32) async throws -> AXEvidenceSnapshot {
        AXEvidenceSnapshot(
            pid: pid,
            windowID: windowID,
            role: axRoleValue,
            subrole: axSubroleValue,
            title: "LINE",
            sampledAtUptime: clock.monotonicNow()
        )
    }

    func signingIdentity(pid: Int32) async -> String? {
        signingIdentityValue
    }

    func monotonicNow() -> Double {
        clock.monotonicNow()
    }
}

final class ScriptedActuationBoundary: ActuationBoundary, @unchecked Sendable {
    let clock: ScriptedClock
    let imageSize: CGSize

    var applicationActive = true
    var targetFrontmost = true
    var epochOffset: UInt64 = 0
    var captureGeometryWindowFrameOverride: CGRect?
    var readinessObservedAtSkewSeconds: Double = 0
    var readinessFailure: Error?
    var revalidateResults: [Bool] = []
    var processStableResults: [Bool] = []
    var postEventAccessAllowed = true

    private let lock = NSLock()
    private var _readinessCalls = 0
    private var _revalidateCalls = 0
    private var _processStableCalls = 0
    private var _revalidateConsumed = 0
    private var _processStableConsumed = 0
    private var _events: [CGEventType] = []

    init(clock: ScriptedClock, imageSize: CGSize = CGSize(width: 327, height: 643)) {
        self.clock = clock
        self.imageSize = imageSize
    }

    var postedEventTypes: [CGEventType] {
        lock.lock()
        defer { lock.unlock() }
        return _events
    }

    var mouseMovedCount: Int {
        postedEventTypes.filter { $0 == .mouseMoved }.count
    }

    var buttonEventCount: Int {
        postedEventTypes.filter { $0 == .leftMouseDown || $0 == .leftMouseUp }.count
    }

    var readinessCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _readinessCalls
    }

    var revalidateCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _revalidateCalls
    }

    var processStableCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _processStableCalls
    }

    func readinessObservation(identity: WindowIdentity, candidate: StructuralCandidate) async throws -> ReadinessObservation {
        lock.lock()
        _readinessCalls += 1
        let failure = readinessFailure
        let active = applicationActive
        let frontmost = targetFrontmost
        let offset = epochOffset
        let frames = captureGeometryWindowFrameOverride ?? identity.windowFrame
        let skew = readinessObservedAtSkewSeconds
        lock.unlock()
        if let failure { throw failure }
        return ReadinessObservation(
            applicationActive: active,
            targetFrontmost: frontmost,
            freshWindow: FreshWindowObservation(
                bundleID: identity.bundleID,
                process: identity.process,
                windowID: identity.windowID,
                frame: identity.windowFrame,
                layer: 0,
                isOnScreen: true
            ),
            currentEpoch: identity.captureEpoch + offset,
            currentBinding: candidate.binding,
            captureGeometry: CaptureGeometry(
                windowFrame: frames,
                captureBBox: CGRect(origin: .zero, size: imageSize),
                scale: 1
            ),
            captureImageSize: imageSize,
            observedAtUptime: clock.monotonicNow() + skew
        )
    }

    func revalidateDispatch(pid: Int32, windowID: UInt32, binding: SurfaceBinding) -> Bool {
        lock.lock()
        _revalidateCalls += 1
        let value = _revalidateConsumed < revalidateResults.count ? revalidateResults[_revalidateConsumed] : true
        _revalidateConsumed += 1
        lock.unlock()
        return value
    }

    func processStable(pid: Int32, binding: SurfaceBinding) -> Bool {
        lock.lock()
        _processStableCalls += 1
        let value = _processStableConsumed < processStableResults.count ? processStableResults[_processStableConsumed] : true
        _processStableConsumed += 1
        lock.unlock()
        return value
    }

    func postEventAccess() -> Bool {
        postEventAccessAllowed
    }

    func clickSink() -> @Sendable (CGEvent, CGEventTapLocation) -> Void {
        { [weak self] event, _ in
            guard let self else { return }
            self.lock.lock()
            self._events.append(event.type)
            self.lock.unlock()
        }
    }
}

final class ScriptedChooserBoundary: ChooserBoundary, @unchecked Sendable {
    enum Script {
        case affirmFirst
        case neverAffirm
        case fail(String)
        case abortingTripwire
        case affirmAfterDeadline
        case stall
    }

    let clock: ScriptedClock
    let ownerPID: Int32

    var script: Script = .affirmFirst
    var preDispatchSatisfied = true
    var panelBoundResults: [Bool] = []
    var primitiveFailureAt: DestinationPrimitive?
    var reflectedDestination = true
    var chooserClosedResult = true
    var pressFailure: Error?

    private let lock = NSLock()
    private var _sampleCalls = 0
    private var _preDispatchCalls = 0
    private var _primitiveCalls = 0
    private var _pressCalls = 0
    private var _panelBoundCalls = 0
    private var _sampleStart: Double?

    init(clock: ScriptedClock, ownerPID: Int32) {
        self.clock = clock
        self.ownerPID = ownerPID
    }

    var sampleCalls: Int {
        lock.lock()
        defer { lock.unlock() }
        return _sampleCalls
    }

    var preDispatchCalls: Int {
        lock.lock()
        defer { lock.unlock() }
        return _preDispatchCalls
    }

    var primitiveCalls: Int {
        lock.lock()
        defer { lock.unlock() }
        return _primitiveCalls
    }

    var pressCalls: Int {
        lock.lock()
        defer { lock.unlock() }
        return _pressCalls
    }

    var panelBoundCalls: Int {
        lock.lock()
        defer { lock.unlock() }
        return _panelBoundCalls
    }

    func sample(
        preDispatchInventory: ObservationInventorySnapshot,
        predicate: ChooserAffirmationPredicate
    ) async -> StrictPostconditionObservation {
        lock.lock()
        _sampleCalls += 1
        if _sampleStart == nil { _sampleStart = clock.monotonicNow() }
        let start = _sampleStart ?? clock.monotonicNow()
        let script = self.script
        let pid = ownerPID
        lock.unlock()
        let affirmation = ChooserAffirmation(
            windowID: MatrixFrame.windowID,
            frame: MatrixFrame.windowFrame,
            ownerPID: pid,
            predicateID: predicate.predicateID,
            affirmedAtISO8601: FrameCaptureSupport.iso8601Now()
        )
        switch script {
        case .affirmFirst:
            return .observed(StrictPostconditionSample(affirmation: affirmation, tripwireObservations: []))
        case .neverAffirm:
            return .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: []))
        case let .fail(detail):
            return .failed(detail, tripwireObservations: [])
        case .abortingTripwire:
            return .observed(StrictPostconditionSample(
                affirmation: nil,
                tripwireObservations: [TripwireClassification(
                    level: .l2ApprovedRoot,
                    outcome: .abortedUnattributedFilesystemWrite,
                    aborts: true,
                    path: "/tmp/matrix-scripted-abort",
                    rationale: "scripted tripwire abort"
                )]
            ))
        case .affirmAfterDeadline:
            if clock.monotonicNow() - start >= PostconditionBounds.planTime.hardCapSeconds + 0.05 {
                return .observed(StrictPostconditionSample(affirmation: affirmation, tripwireObservations: []))
            }
            return .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: []))
        case .stall:
            // Sleeps through the strict monitor's real-timer deadline race and
            // is cancelled once the monitor resolves the deadline verdict.
            try? await Task.sleep(nanoseconds: 3_600_000_000_000)
            return .observed(StrictPostconditionSample(affirmation: nil, tripwireObservations: []))
        }
    }

    func panelStillBound(pid: Int32, confirmation: ChooserAffirmation) -> Bool {
        lock.lock()
        _panelBoundCalls += 1
        let value = _panelBoundCalls <= panelBoundResults.count ? panelBoundResults[_panelBoundCalls - 1] : true
        lock.unlock()
        return value
    }

    func preparePrimitive(_ primitive: DestinationPrimitive, pid: Int32, destination: URL) throws -> [String: String] {
        lock.lock()
        _primitiveCalls += 1
        let failure = primitiveFailureAt
        lock.unlock()
        if failure == primitive { throw ScriptedCompositionError.primitiveRefused(primitive.rawValue) }
        return ["scripted": primitive.rawValue]
    }

    func destinationReflected(pid: Int32, destination: URL) -> Bool {
        reflectedDestination
    }

    func pressDefaultButton(pid: Int32, confirmation: ChooserAffirmation) throws -> String {
        lock.lock()
        _pressCalls += 1
        let failure = pressFailure
        lock.unlock()
        if let failure { throw failure }
        return "AXPressDefaultButton"
    }

    func chooserClosed(pid: Int32) -> Bool {
        chooserClosedResult
    }

    func preDispatchContextSatisfied(minimumSeconds: Double) -> Bool {
        lock.lock()
        _preDispatchCalls += 1
        let value = preDispatchSatisfied
        lock.unlock()
        return value
    }
}

final class ScriptedFilesystemBoundary: FilesystemBoundary, @unchecked Sendable {
    var snapshotSequence: [StagingSnapshot]
    var unstableAlways = false
    var baselineResult: BaselineVerificationResult?
    var baselineFailureCalls: Set<Int> = []
    var directoryExistsResult = true

    private let lock = NSLock()
    private var snapshotIndex = 0
    private var unstableTick = 0
    private var _snapshotCalls = 0
    private var _baselineCalls = 0

    init(snapshotSequence: [StagingSnapshot] = [], baselineResult: BaselineVerificationResult? = nil) {
        self.snapshotSequence = snapshotSequence
        self.baselineResult = baselineResult
    }

    var snapshotCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _snapshotCalls
    }

    var baselineCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _baselineCalls
    }

    func stagingSnapshot(directory: URL, observedAt: Double) throws -> StagingSnapshot {
        lock.lock()
        defer { lock.unlock() }
        _snapshotCalls += 1
        if unstableAlways {
            unstableTick += 1
            let at = 2_000 + Double(unstableTick) * 0.5
            let files = MatrixSnapshots.syntheticStableFiles.map {
                StagingFileRecord(name: $0.name, size: $0.size, modificationTime: at, sha256: $0.sha256, decodable: $0.decodable)
            }
            return StagingSnapshot(observedAt: at, files: files)
        }
        if snapshotIndex < snapshotSequence.count {
            let snapshot = snapshotSequence[snapshotIndex]
            snapshotIndex += 1
            return snapshot
        }
        guard let last = snapshotSequence.last else {
            throw ScriptedCompositionError.detail("scripted snapshot sequence is empty")
        }
        snapshotIndex += 1
        let extensionAt = last.observedAt + 3.0 * Double(snapshotIndex - snapshotSequence.count)
        return StagingSnapshot(
            observedAt: extensionAt,
            files: last.files,
            subdirectories: last.subdirectories,
            symlinks: last.symlinks,
            otherEntries: last.otherEntries
        )
    }

    func directoryExists(_ url: URL) -> Bool {
        directoryExistsResult
    }

    func verifyBaseline(referenceFile: URL) throws -> BaselineVerificationResult {
        lock.lock()
        _baselineCalls += 1
        let call = _baselineCalls
        let failure = baselineFailureCalls.contains(call)
        let result = baselineResult
        lock.unlock()
        if failure { throw BaselineVerificationError.referenceDigestMismatch }
        guard let result else { throw ScriptedCompositionError.detail("scripted baseline result unavailable") }
        return result
    }
}

/// Real scanning over a real staging directory with synthetic observation
/// timestamps, so stability can be proven without waiting real seconds.
final class RealScanningFilesystemBoundary: FilesystemBoundary, @unchecked Sendable {
    let referenceFile: URL

    private let lock = NSLock()
    private var tick = 0
    private var _snapshotCalls = 0
    private var _baselineCalls = 0

    init(referenceFile: URL) {
        self.referenceFile = referenceFile
    }

    var snapshotCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _snapshotCalls
    }

    var baselineCallCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return _baselineCalls
    }

    func stagingSnapshot(directory: URL, observedAt: Double) throws -> StagingSnapshot {
        let real = try StagingVerifier.snapshot(directory: directory, observedAt: observedAt)
        lock.lock()
        tick += 1
        _snapshotCalls += 1
        let syntheticAt = Date().timeIntervalSince1970 + Double(tick) * 3.0
        lock.unlock()
        return StagingSnapshot(
            observedAt: syntheticAt,
            files: real.files,
            subdirectories: real.subdirectories,
            symlinks: real.symlinks,
            otherEntries: real.otherEntries
        )
    }

    func directoryExists(_ url: URL) -> Bool {
        FileManager.default.fileExists(atPath: url.path)
    }

    func verifyBaseline(referenceFile: URL) throws -> BaselineVerificationResult {
        lock.lock()
        _baselineCalls += 1
        lock.unlock()
        return try BaselineVerifier.verify(referenceFile: referenceFile)
    }
}

struct MatrixBaselineReference {
    let sourceDirectory: String
    let fileCount: Int
    let totalBytes: UInt64
    let digest: String
    let tripwireDigest: String
    let contentMultiset: [String]

    static let relativeReferencePath = "evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json"

    static func load(repositoryRoot: URL) throws -> MatrixBaselineReference {
        let url = repositoryRoot.appendingPathComponent(relativeReferencePath)
        guard FileManager.default.fileExists(atPath: url.path) else {
            throw ScriptedCompositionError.detail("baseline reference missing at \(url.path)")
        }
        let reference = try JSONDecoder().decode(BaselineContentReference.self, from: Data(contentsOf: url))
        guard reference.file_count == StagingPolicy.rev28Accepted.expectedFileCount,
              reference.total_bytes == StagingPolicy.rev28Accepted.expectedTotalBytes,
              reference.content_multiset.count == reference.file_count,
              Set(reference.content_multiset).count == reference.file_count,
              StagingVerifier.contentMultisetDigest(reference.content_multiset)
                == StagingPolicy.rev28Accepted.expectedContentMultisetSHA256 else {
            throw ScriptedCompositionError.detail("baseline reference contract mismatch")
        }
        return MatrixBaselineReference(
            sourceDirectory: reference.source_dir,
            fileCount: reference.file_count,
            totalBytes: reference.total_bytes,
            digest: reference.name_excluded_multiset_sha256_of_sorted_list,
            tripwireDigest: ImmutableRunAuthorization.acceptedBaselineTripwireSHA256,
            contentMultiset: reference.content_multiset
        )
    }
}

enum MatrixSnapshots {
    static let syntheticStableFiles: [StagingFileRecord] = (0..<57).map { index in
        StagingFileRecord(
            name: String(format: "LINE_ALBUM_%02d.jpg", index + 1),
            size: 100,
            modificationTime: 0,
            sha256: hex64(index + 1),
            decodable: true
        )
    }

    static func duplicateFiles(_ reference: MatrixBaselineReference) -> [StagingFileRecord] {
        let hashes = reference.contentMultiset
        guard !hashes.isEmpty else { return [] }
        let base = reference.totalBytes / UInt64(hashes.count)
        let remainder = reference.totalBytes % UInt64(hashes.count)
        return hashes.enumerated().map { index, hash in
            StagingFileRecord(
                name: String(format: "LINE_ALBUM_%02d.jpg", index + 1),
                size: base + (index == hashes.count - 1 ? remainder : 0),
                modificationTime: 900,
                sha256: hash,
                decodable: true
            )
        }
    }

    static func snapshots(_ files: [StagingFileRecord], at times: [Double] = [1_000, 1_003, 1_006]) -> [StagingSnapshot] {
        times.map { StagingSnapshot(observedAt: $0, files: files) }
    }

    static func duplicateContentSnapshots(_ reference: MatrixBaselineReference) -> [StagingSnapshot] {
        snapshots(duplicateFiles(reference))
    }

    static func incompleteSnapshots(_ reference: MatrixBaselineReference) -> [StagingSnapshot] {
        snapshots(Array(duplicateFiles(reference).prefix(40)))
    }

    static func extraFilesSnapshots(_ reference: MatrixBaselineReference) -> [StagingSnapshot] {
        var files = duplicateFiles(reference)
        files.append(StagingFileRecord(
            name: "stray-extra.bin",
            size: 1,
            modificationTime: 900,
            sha256: String(repeating: "fe", count: 32),
            decodable: true
        ))
        return snapshots(files)
    }

    static func duplicateContentHashSnapshots(_ reference: MatrixBaselineReference) -> [StagingSnapshot] {
        var files = duplicateFiles(reference)
        if files.count >= 2 {
            let first = files[0]
            let last = files[files.count - 1]
            files[files.count - 1] = StagingFileRecord(
                name: last.name,
                size: first.size,
                modificationTime: first.modificationTime,
                sha256: first.sha256,
                decodable: true
            )
        }
        return snapshots(files)
    }

    static func contentMismatchSnapshots(_ reference: MatrixBaselineReference) -> [StagingSnapshot] {
        let files = duplicateFiles(reference).enumerated().map { index, file in
            StagingFileRecord(
                name: file.name,
                size: file.size,
                modificationTime: file.modificationTime,
                sha256: hex64(10_000 + index),
                decodable: true
            )
        }
        return snapshots(files)
    }

    static func cannedBaselineResult(_ reference: MatrixBaselineReference) -> BaselineVerificationResult {
        BaselineVerificationResult(
            sourceDirectory: reference.sourceDirectory,
            fileCount: reference.fileCount,
            totalBytes: reference.totalBytes,
            contentMultisetSHA256: reference.digest,
            nameInclusiveTripwireSHA256: reference.tripwireDigest,
            verifiedAtISO8601: FrameCaptureSupport.iso8601Now()
        )
    }

    private static func hex64(_ value: Int) -> String {
        let tail = String(value, radix: 16)
        return String(repeating: "0", count: max(0, 64 - tail.count)) + tail
    }
}

final class CompositionFixture {
    let repositoryRoot: URL
    let root: URL
    let stagingRoot: URL
    let stagingRunDirectory: URL
    let evidenceDirectory: URL
    let ledgerAnchorURL: URL
    let baseline: MatrixBaselineReference
    let baselineReferenceFileURL: URL
    let authorization: ImmutableRunAuthorization
    let clock: ScriptedClock
    let observation: ScriptedObservationBoundary
    let actuation: ScriptedActuationBoundary
    let chooser: ScriptedChooserBoundary
    let filesystem: any FilesystemBoundary
    let scriptedFilesystem: ScriptedFilesystemBoundary?
    let session: NativeObservationSession
    let store: NativeEvidenceStore
    let ledger: IntentLedger
    let goalSlot: GoalSlot?
    let owner: PersistentTransactionOwner
    let adapter: NativeLiveExecutionAdapter
    let configuration: NativeAdapterConfiguration

    init(
        repositoryRoot: URL,
        root: URL,
        stagingRoot: URL,
        stagingRunDirectory: URL,
        evidenceDirectory: URL,
        ledgerAnchorURL: URL,
        baseline: MatrixBaselineReference,
        baselineReferenceFileURL: URL,
        authorization: ImmutableRunAuthorization,
        clock: ScriptedClock,
        observation: ScriptedObservationBoundary,
        actuation: ScriptedActuationBoundary,
        chooser: ScriptedChooserBoundary,
        filesystem: any FilesystemBoundary,
        scriptedFilesystem: ScriptedFilesystemBoundary?,
        session: NativeObservationSession,
        store: NativeEvidenceStore,
        ledger: IntentLedger,
        goalSlot: GoalSlot?,
        owner: PersistentTransactionOwner,
        adapter: NativeLiveExecutionAdapter,
        configuration: NativeAdapterConfiguration
    ) {
        self.repositoryRoot = repositoryRoot
        self.root = root
        self.stagingRoot = stagingRoot
        self.stagingRunDirectory = stagingRunDirectory
        self.evidenceDirectory = evidenceDirectory
        self.ledgerAnchorURL = ledgerAnchorURL
        self.baseline = baseline
        self.baselineReferenceFileURL = baselineReferenceFileURL
        self.authorization = authorization
        self.clock = clock
        self.observation = observation
        self.actuation = actuation
        self.chooser = chooser
        self.filesystem = filesystem
        self.scriptedFilesystem = scriptedFilesystem
        self.session = session
        self.store = store
        self.ledger = ledger
        self.goalSlot = goalSlot
        self.owner = owner
        self.adapter = adapter
        self.configuration = configuration
    }

    var observationPID: Int32 { observation.processInstance.pid }

    func makeEngine(owner: PersistentTransactionOwner? = nil) -> LiveExecutionEngine {
        LiveExecutionEngine(owner: owner ?? self.owner, adapter: adapter)
    }

    /// A second owner over the same append-only ledger, as a restart would build.
    func secondOwner(goalSlot overrideGoalSlot: GoalSlot? = nil) throws -> PersistentTransactionOwner {
        try PersistentTransactionOwner(
            authorization: authorization,
            ledger: try IntentLedger(fileURL: ledger.fileURL),
            checkpointURL: ledgerAnchorURL,
            goalSlot: overrideGoalSlot ?? goalSlot
        )
    }

    var realImagesAvailable: Bool {
        FileManager.default.fileExists(atPath: baseline.sourceDirectory)
    }

    func copyRealImagesIntoStaging() throws {
        let source = URL(fileURLWithPath: baseline.sourceDirectory)
        let entries = try FileManager.default.contentsOfDirectory(at: source, includingPropertiesForKeys: nil)
            .filter { ["jpg", "jpeg", "png"].contains($0.pathExtension.lowercased()) }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        guard entries.count == baseline.fileCount else {
            throw ScriptedCompositionError.detail("baseline source image count \(entries.count) != \(baseline.fileCount)")
        }
        for entry in entries {
            let target = stagingRunDirectory.appendingPathComponent(entry.lastPathComponent)
            if FileManager.default.fileExists(atPath: target.path) { continue }
            try FileManager.default.copyItem(at: entry, to: target)
            try FileManager.default.setAttributes(
                [.modificationDate: Date().addingTimeInterval(-60)],
                ofItemAtPath: target.path
            )
        }
    }

    func evidenceFiles(matching prefix: String) throws -> [URL] {
        try FileManager.default.contentsOfDirectory(at: evidenceDirectory, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.hasPrefix(prefix) }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}

enum CompositionFixtureBuilder {
    static func build(
        runID: String? = nil,
        useGoalSlot: Bool = false,
        realFilesystem: Bool = false
    ) throws -> CompositionFixture {
        let fm = FileManager.default
        let repositoryRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let root = fm.temporaryDirectory
            .appendingPathComponent("rev28-matrix-\(UUID().uuidString)", isDirectory: true)
            .resolvingSymlinksInPath()
        let resolvedRunID = runID ?? "matrix-run-\(UUID().uuidString.prefix(8))"
        let stagingRoot = root.appendingPathComponent("staging", isDirectory: true)
        let stagingRunDirectory = stagingRoot.appendingPathComponent(resolvedRunID, isDirectory: true)
        let evidenceDirectory = root
            .appendingPathComponent("evidence", isDirectory: true)
            .appendingPathComponent(resolvedRunID, isDirectory: true)
        let controlRoot = root.appendingPathComponent("control", isDirectory: true)
        try fm.createDirectory(at: stagingRunDirectory, withIntermediateDirectories: true)
        try fm.createDirectory(at: evidenceDirectory, withIntermediateDirectories: true)
        try fm.createDirectory(at: controlRoot, withIntermediateDirectories: true)

        let baseline = try MatrixBaselineReference.load(repositoryRoot: repositoryRoot)
        let baselineReferenceFileURL = repositoryRoot.appendingPathComponent(MatrixBaselineReference.relativeReferencePath)
        let authorization = ImmutableRunAuthorization(
            runID: resolvedRunID,
            goal: "matrix-goal-\(resolvedRunID)",
            group: LiveExecutionEngine.targetGroup,
            album: LiveExecutionEngine.targetAlbum,
            planSHA256: String(repeating: "a1", count: 32),
            reviewedImplementationSHA256: String(repeating: "b2", count: 32),
            stagingRoot: stagingRoot,
            stagingRunDirectory: stagingRunDirectory,
            evidenceRunDirectory: evidenceDirectory
        )
        guard let processInstance = ProcessInstanceID.current(pid: getpid()) else {
            throw ScriptedCompositionError.detail("process instance unavailable for the scripted target pid")
        }

        let clock = ScriptedClock()
        let observation = ScriptedObservationBoundary(clock: clock, processInstance: processInstance)
        let actuation = ScriptedActuationBoundary(clock: clock)
        let chooser = ScriptedChooserBoundary(clock: clock, ownerPID: processInstance.pid)

        let scriptedFilesystem: ScriptedFilesystemBoundary?
        let filesystem: any FilesystemBoundary
        if realFilesystem {
            scriptedFilesystem = nil
            filesystem = RealScanningFilesystemBoundary(referenceFile: baselineReferenceFileURL)
        } else {
            let scripted = ScriptedFilesystemBoundary(
                snapshotSequence: MatrixSnapshots.duplicateContentSnapshots(baseline),
                baselineResult: MatrixSnapshots.cannedBaselineResult(baseline)
            )
            scriptedFilesystem = scripted
            filesystem = scripted
        }

        let configuration = NativeAdapterConfiguration(
            targetBundleID: MatrixFrame.bundleID,
            targetGroup: LiveExecutionEngine.targetGroup,
            targetAlbumTitle: LiveExecutionEngine.targetAlbum,
            targetAlbumCardCountText: MatrixFrame.albumCardCountText,
            targetPhotoCountText: MatrixFrame.photoCountText,
            stagingRunDirectory: stagingRunDirectory,
            baselineReferenceFileURL: baselineReferenceFileURL,
            chooserPredicate: matrixPredicate(),
            captureTimeoutSeconds: 10,
            stagingSnapshotIntervalSeconds: 0.05,
            downloadObservationLimitSeconds: 30,
            menuReferenceRows: StructuralLocators.lineAlbumMenuReference
        )

        let session = try NativeObservationSession(
            sessionID: "matrix-session-\(resolvedRunID)",
            runID: resolvedRunID,
            targetBundleID: MatrixFrame.bundleID,
            targetPID: processInstance.pid,
            evidenceDirectory: evidenceDirectory,
            boundary: observation
        )
        let store = try NativeEvidenceStore(
            runDirectory: evidenceDirectory,
            runID: resolvedRunID,
            planSHA256: authorization.planSHA256,
            reviewedImplementationSHA256: authorization.reviewedImplementationSHA256
        )
        let ledger = try IntentLedger(fileURL: root.appendingPathComponent("ledger.jsonl"))
        let goalSlot: GoalSlot?
        if useGoalSlot {
            goalSlot = try GoalSlot(
                controlRoot: controlRoot,
                identity: GoalSlotIdentity(
                    goal: authorization.goal,
                    group: authorization.group,
                    album: authorization.album,
                    stagingRunDirectory: stagingRunDirectory
                )
            )
        } else {
            goalSlot = nil
        }
        let owner = try PersistentTransactionOwner(
            authorization: authorization,
            ledger: ledger,
            checkpointURL: root.appendingPathComponent("ledger-anchor.json"),
            goalSlot: goalSlot
        )
        let adapter = try NativeLiveExecutionAdapter(
            configuration: configuration,
            session: session,
            store: store,
            observation: observation,
            actuation: actuation,
            chooser: chooser,
            filesystem: filesystem,
            clock: clock
        )
        return CompositionFixture(
            repositoryRoot: repositoryRoot,
            root: root,
            stagingRoot: stagingRoot,
            stagingRunDirectory: stagingRunDirectory,
            evidenceDirectory: evidenceDirectory,
            ledgerAnchorURL: root.appendingPathComponent("ledger-anchor.json"),
            baseline: baseline,
            baselineReferenceFileURL: baselineReferenceFileURL,
            authorization: authorization,
            clock: clock,
            observation: observation,
            actuation: actuation,
            chooser: chooser,
            filesystem: filesystem,
            scriptedFilesystem: scriptedFilesystem,
            session: session,
            store: store,
            ledger: ledger,
            goalSlot: goalSlot,
            owner: owner,
            adapter: adapter,
            configuration: configuration
        )
    }

    static func matrixPredicate() -> ChooserAffirmationPredicate {
        ChooserAffirmationPredicate(
            predicateID: "matrix-chooser-predicate-v1",
            frozenAtISO8601: FrameCaptureSupport.iso8601Now(),
            calibratedAgainst: "matrix-scripted-panel",
            ax: ChooserAXClauseSet(
                windowRole: "AXWindow",
                allowedSubroles: ["AXStandardWindow"],
                requiresTextField: true,
                textFieldRoles: ["AXTextField"],
                requiresPopUpButton: false,
                popUpButtonRoles: [],
                defaultButton: ButtonRequirement(
                    mode: .titleIn,
                    attributeName: nil,
                    attributeValue: nil,
                    titles: ["開啟"],
                    buttonRoles: ["AXButton"]
                ),
                cancelButton: ButtonRequirement(
                    mode: .titleIn,
                    attributeName: nil,
                    attributeValue: nil,
                    titles: ["Cancel", "取消"],
                    buttonRoles: ["AXButton"]
                ),
                requiresPathAffordance: false,
                pathAffordanceRoles: [],
                pathAffordanceTitles: []
            ),
            ownership: ChooserOwnershipClauseSet(
                requiresOwningPIDInCensusUnion: true,
                requiresStableProcessInstance: true,
                emptyPreCensusWidensRefusal: true
            )
        )
    }
}
