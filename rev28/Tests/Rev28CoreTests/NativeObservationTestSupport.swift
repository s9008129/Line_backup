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

    /// Substitution for the live SCK/CG freshness read: the scripted scene's
    /// window and the candidate's own binding are the fresh facts, so the
    /// production permit/geometry decisions in `mintPermit` still run.
    func readinessObservation(
        identity: WindowIdentity,
        candidate: StructuralCandidate
    ) async throws -> ReadinessObservation {
        let point = candidate.pointCapturePx
        let safe = candidate.safeRectCapturePx
        let width = max(safe.maxX, point.x) + 100
        let height = max(safe.maxY, point.y) + 100
        return ReadinessObservation(
            applicationActive: active,
            targetFrontmost: frontmost,
            freshWindow: FreshWindowObservation(
                bundleID: identity.bundleID,
                process: identity.process,
                windowID: identity.windowID,
                frame: identity.cgEntry.frame,
                layer: identity.cgEntry.layer,
                isOnScreen: true
            ),
            currentEpoch: identity.captureEpoch,
            currentBinding: candidate.binding,
            captureGeometry: CaptureGeometry(
                windowFrame: identity.cgEntry.frame,
                captureBBox: identity.cgEntry.frame,
                scale: 1
            ),
            captureImageSize: CGSize(width: width, height: height),
            observedAtUptime: uptimeValue
        )
    }

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

/// Frozen-shape v2 chooser predicate and scripted chooser facts shared by the
/// composed post-Save-All tests. The predicate is never edited by the
/// composition; only the machine facts around it are scripted.
enum TestChooserFixtures {
    static let chooserWindowID: UInt32 = 99
    static let chooserPID: Int32 = 100
    static let chooserBundleID = "com.apple.appkit.xpc.openAndSavePanelService"
    static let chooserSigning = "Developer ID Application: Apple (FAKE)"

    static func predicate() -> ChooserAffirmationPredicate {
        let defaultButton = ButtonRequirement(
            mode: .titleIn,
            attributeName: nil,
            attributeValue: nil,
            titles: ["Open"],
            buttonRoles: ["AXButton"]
        )
        let cancelButton = ButtonRequirement(
            mode: .titleIn,
            attributeName: nil,
            attributeValue: nil,
            titles: ["Cancel"],
            buttonRoles: ["AXButton"]
        )
        let clauses = ChooserAXClauseSet(
            windowRole: "AXWindow",
            allowedSubroles: ["AXStandardWindow"],
            requiresTextField: true,
            textFieldRoles: ["AXTextField"],
            requiresPopUpButton: false,
            popUpButtonRoles: [],
            defaultButton: defaultButton,
            cancelButton: cancelButton,
            requiresPathAffordance: false,
            pathAffordanceRoles: [],
            pathAffordanceTitles: []
        )
        return ChooserAffirmationPredicate(
            predicateID: "unit-test-v2",
            frozenAtISO8601: "2026-09-29T00:00:00.000Z",
            calibratedAgainst: "unit-test",
            ax: clauses,
            ownership: ChooserOwnershipClauseSet(
                requiresOwningPIDInCensusUnion: true,
                requiresStableProcessInstance: true,
                emptyPreCensusWidensRefusal: true
            ),
            predicateVersion: 2
        )
    }

    static func processFacts(pid: Int32 = chooserPID, startTime: Double = 10) -> ChooserProcessFacts {
        ChooserProcessFacts(
            pid: pid,
            bundleID: chooserBundleID,
            signingIdentity: chooserSigning,
            startTimeUnix: startTime
        )
    }

    static func census(
        windowIDs: [UInt32] = [7, 8],
        pid: Int32 = chooserPID
    ) -> ChooserCensus {
        ChooserCensus(
            windowIDs: windowIDs,
            processes: [processFacts(pid: pid)],
            recordedAtMonotonicNanos: 1
        )
    }

    static func affirmingWindow(windowID: UInt32 = chooserWindowID, pid: Int32 = chooserPID) -> ChooserWindowFacts {
        let owner = processFacts(pid: pid)
        let nodes = [
            AXNodeDump(
                depth: 0, role: "AXWindow", subrole: "AXStandardWindow", title: "Open",
                description: nil, identifier: nil, keyEquivalent: nil, value: nil,
                enabled: true, frame: CGRect(x: 0, y: 0, width: 300, height: 200), attributes: [:]
            ),
            AXNodeDump(
                depth: 1, role: "AXTextField", subrole: nil, title: nil,
                description: nil, identifier: nil, keyEquivalent: nil, value: "/tmp/destination",
                enabled: true, frame: nil, attributes: [:]
            ),
            AXNodeDump(
                depth: 1, role: "AXButton", subrole: nil, title: "Open",
                description: nil, identifier: nil, keyEquivalent: "\r", value: nil,
                enabled: true, frame: nil, attributes: [:]
            ),
            AXNodeDump(
                depth: 1, role: "AXButton", subrole: nil, title: "Cancel",
                description: nil, identifier: nil, keyEquivalent: nil, value: nil,
                enabled: true, frame: nil, attributes: [:]
            ),
        ]
        return ChooserWindowFacts(
            windowID: windowID,
            frame: CGRect(x: 0, y: 0, width: 300, height: 200),
            onScreen: true,
            presentInSCInventory: true,
            presentInCGInventory: true,
            owner: owner,
            pidReuseDetected: false,
            axNodes: nodes,
            preDispatchOwner: owner,
            postDispatchOwner: owner
        )
    }

    static func affirmingFacts(
        windowID: UInt32 = chooserWindowID,
        pid: Int32 = chooserPID,
        tripwire: [TripwireClassification] = []
    ) -> ChooserFacts {
        ChooserFacts(
            windows: [affirmingWindow(windowID: windowID, pid: pid)],
            postDispatchCensusPIDs: [pid],
            tripwire: tripwire
        )
    }

    static func emptyFacts(tripwire: [TripwireClassification] = []) -> ChooserFacts {
        ChooserFacts(windows: [], postDispatchCensusPIDs: [chooserPID], tripwire: tripwire)
    }
}

/// Test substitution below the post-Save-All OS boundary. The composition's
/// state/eligibility/predicate/intent/evidence decisions stay in production
/// code; this only scripts the machine facts and the reviewed primitives.
final class FakePostSaveEnvironment: @unchecked Sendable, PostSaveEnvironment {
    private let lock = NSLock()
    private var clock: Double = 1_000
    private var chooserIndex = 0
    private var chooserResults: [ChooserFactsResult] = []

    var sleepSecondsAdvance: Double = 3
    var baselineResult: BaselineVerificationResult?
    var preDispatchContextFacts: PreDispatchContextFacts?
    var census: ChooserCensus?
    var preDispatchCensusError: Error?
    var postConfirmationFactsResult: PostConfirmationFacts?
    var stagingFiles: [StagingFileRecord] = []
    var stagingSubdirectories: [String] = []
    /// When true every sample rewrites mtimes to "now", so quiescence can never
    /// be reached and the caller must observe the cap terminal instead.
    var stagingModificationTimesFollowClock = false
    var tripwire: [TripwireClassification] = []
    var prepareDestinationResult = "prepared"
    var prepareDestinationError: Error?
    var confirmDefaultButtonResult = "role=AXButton title=Open"
    /// Clock used to consume the readiness permit in the stub dispatch. The
    /// permit is minted from `FakeActuationEnvironment.uptimeValue`, so this
    /// must stay aligned with it or the stub would prove the expiry path.
    var readinessNow: Double = 100

    private(set) var saveAllClicks = 0
    private(set) var dispatchBoundaryMarks = 0
    private(set) var preparedDestinations: [String] = []
    private(set) var preparedPIDs: [Int32] = []
    private(set) var confirmations = 0

    func setChooserResults(_ results: [ChooserFactsResult]) {
        lock.lock(); chooserResults = results; chooserIndex = 0; lock.unlock()
    }

    func advanceClock(by seconds: Double) {
        lock.lock(); clock += seconds; lock.unlock()
    }

    var currentClock: Double {
        lock.lock(); defer { lock.unlock() }
        return clock
    }

    func verifyBaseline() throws -> BaselineVerificationResult {
        baselineResult ?? BaselineVerificationResult(
            sourceDirectory: "/baseline",
            fileCount: StagingPolicy.rev28Accepted.expectedFileCount,
            totalBytes: StagingPolicy.rev28Accepted.expectedTotalBytes,
            contentMultisetSHA256: StagingPolicy.rev28Accepted.expectedContentMultisetSHA256,
            nameInclusiveTripwireSHA256: ImmutableRunAuthorization.acceptedBaselineTripwireSHA256,
            verifiedAtISO8601: "2026-09-29T00:00:00.000Z"
        )
    }

    func preDispatchContext(minimumSeconds: Double) async throws -> PreDispatchContextFacts {
        if let facts = preDispatchContextFacts { return facts }
        return PreDispatchContextFacts(
            minimumSeconds: minimumSeconds,
            observedSeconds: minimumSeconds,
            journalRunning: true,
            journalFailure: nil,
            collectionGap: nil,
            journalStartedAtMonotonicNanos: 1,
            facts: []
        )
    }

    func preDispatchCensus() async throws -> ChooserCensus {
        if let error = preDispatchCensusError { throw error }
        return census ?? TestChooserFixtures.census()
    }

    func sampleChooserFacts(preCensus: ChooserCensus) async -> ChooserFactsResult {
        lock.lock()
        defer { lock.unlock() }
        guard !chooserResults.isEmpty else { return .facts(TestChooserFixtures.emptyFacts()) }
        let result = chooserResults[min(chooserIndex, chooserResults.count - 1)]
        chooserIndex += 1
        return result
    }

    func dispatchSaveAllClick(
        owner: PersistentTransactionOwner,
        permit: ReadinessPermit,
        binding: SurfaceBinding
    ) throws {
        lock.lock(); saveAllClicks += 1; lock.unlock()
        // Keep the production ledger semantics (durable intent + attempt before
        // dispatch) while proving the AB round posts no real event.
        try GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: binding,
            intent: .saveAll(owner),
            sink: { _, _ in },
            readinessCheck: { _, _ in true },
            processIdentityCheck: { _, _ in true },
            postEventAccessCheck: { true },
            now: readinessNow
        )
    }

    func prepareDestination(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String {
        if let error = prepareDestinationError { throw error }
        lock.lock()
        preparedDestinations.append(destination.standardizedFileURL.path)
        preparedPIDs.append(pid)
        lock.unlock()
        try owner.recordReversibleDispatch(action: "chooser.prepareDestination")
        return prepareDestinationResult
    }

    func confirmDefaultButton(
        owner: PersistentTransactionOwner,
        pid: Int32,
        expectedProcess: ProcessInstanceID,
        destination: URL,
        predicate: ChooserAffirmationPredicate,
        candidate: ChooserCandidate
    ) throws -> String {
        lock.lock(); confirmations += 1; lock.unlock()
        var pressed = "?"
        try GatedDestinationConfirmation.perform(
            owner: owner,
            action: "AXPressDefaultButton",
            readinessCheck: { true },
            dispatch: { pressed = self.confirmDefaultButtonResult }
        )
        return pressed
    }

    func postConfirmationFacts(chooserWindowIDs: [UInt32], stagingDirectory: URL) async -> PostConfirmationFacts? {
        postConfirmationFactsResult ?? PostConfirmationFacts(
            chooserWindowStillOnScreen: false,
            stagingSnapshot: snapshot(directory: stagingDirectory),
            tripwire: tripwire
        )
    }

    func stagingSnapshot(directory: URL) throws -> StagingSnapshot {
        snapshot(directory: directory)
    }

    func tripwireObservations() -> [TripwireClassification] {
        tripwire
    }

    func markDispatchBoundary() {
        lock.lock(); dispatchBoundaryMarks += 1; lock.unlock()
    }

    func monotonicNow() -> Double {
        currentClock
    }

    func sleep(seconds: Double) async {
        lock.lock()
        clock += max(0, seconds) + sleepSecondsAdvance
        lock.unlock()
    }

    private func snapshot(directory: URL) -> StagingSnapshot {
        lock.lock()
        defer { lock.unlock() }
        let files = stagingModificationTimesFollowClock
            ? stagingFiles.map { file in
                StagingFileRecord(
                    name: file.name,
                    size: file.size,
                    modificationTime: clock,
                    sha256: file.sha256,
                    decodable: file.decodable
                )
            }
            : stagingFiles
        return StagingSnapshot(
            observedAt: clock,
            files: files,
            subdirectories: stagingSubdirectories
        )
    }
}
