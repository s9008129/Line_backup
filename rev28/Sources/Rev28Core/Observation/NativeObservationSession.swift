import CoreGraphics
import Foundation
import ImageIO

// MARK: - C3 native observation authority
//
// One serialized session owns every capture. A bundle is built around exactly
// one retained image and the fresh process/window inventories that surrounded
// it: OCR, structural localization and every identity decision derive from that
// same retained image. Any inconsistency is a typed refusal; an observer
// exception or a deadline breach can never become an empty successful
// observation, and an old candidate is never relabeled with a new epoch.

public enum ObservationRefusal: Error, Equatable, CustomStringConvertible {
    case sessionBusy
    case deadlineExceeded(stage: String)
    case observerFailure(stage: String, detail: String)
    case targetWindowNotUnique(found: Int)
    case identityMismatch([String])
    case inventoryChanged(String)
    case retainedImageMismatch(String)
    case invalidFrameGeometry([String])
    case invalidBundle(String)

    public var description: String {
        switch self {
        case .sessionBusy:
            return "sessionBusy"
        case let .deadlineExceeded(stage):
            return "deadlineExceeded(stage=\(stage))"
        case let .observerFailure(stage, detail):
            return "observerFailure(stage=\(stage), detail=\(detail))"
        case let .targetWindowNotUnique(found):
            return "targetWindowNotUnique(found=\(found))"
        case let .identityMismatch(violations):
            return "identityMismatch(\(violations.joined(separator: "; ")))"
        case let .inventoryChanged(detail):
            return "inventoryChanged(\(detail))"
        case let .retainedImageMismatch(detail):
            return "retainedImageMismatch(\(detail))"
        case let .invalidFrameGeometry(violations):
            return "invalidFrameGeometry(\(violations.joined(separator: "; ")))"
        case let .invalidBundle(detail):
            return "invalidBundle(\(detail))"
        }
    }
}

public struct ObservationTarget: Equatable, Codable, Sendable {
    public let bundleID: String
    public let pid: Int32

    public init(bundleID: String, pid: Int32) {
        self.bundleID = bundleID
        self.pid = pid
    }
}

/// What structural derivation the caller expects from this observation. The
/// session always records either a typed candidate or a typed refusal; a
/// localization request never silently degrades to "no candidate".
public enum ObservationLocalization: Equatable, Sendable {
    case none
    case albumCards(title: String, count: String)
    case albumEllipsis(title: String, groupTitle: String?)
    case saveAllMenuRows(menuBounds: CGRect, addressableBounds: CGRect)
}

/// One capture result from the OS boundary: the immutable image plus the
/// frame/provenance record the capture layer already computed for it.
public struct ObservationCapturedImage: @unchecked Sendable {
    public let image: CGImage
    public let record: CapturedFrameRecord

    public init(image: CGImage, record: CapturedFrameRecord) {
        self.image = image
        self.record = record
    }
}

/// The injectable OS boundary. Production substitutes real SCK/CG/AX/process
/// sources; tests substitute below perception, never above predicate or state
/// decisions.
public protocol ObservationSource: Sendable {
    func enumerateWindows() async throws -> [SCWindowSnapshot]
    func cgInventory() -> [CGWindowSnapshot]
    func captureTarget(
        window: SCWindowSnapshot,
        includedWindows: [SCWindowSnapshot],
        configuration: CaptureConfiguration,
        geometryState: CaptureGeometryState,
        epoch: UInt64
    ) async throws -> ObservationCapturedImage
    func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead
    func processInstance(pid: Int32) throws -> ProcessInstanceID
    func signingIdentity(pid: Int32) throws -> String?
    func nextEpoch() -> UInt64
    func monotonicNanos() -> UInt64
}

public struct NativeObservationRequest: Sendable {
    public let runID: String
    public let state: ExecutionState
    public let target: ObservationTarget
    public let configuration: CaptureConfiguration
    public let geometryState: CaptureGeometryState
    public let localization: ObservationLocalization
    /// Budget in the session source's monotonic clock domain. The session turns
    /// it into one absolute deadline and never extends it.
    public let observationBudgetNanos: UInt64
    public let explicitLineRequestBinding: ExplicitLineRequestBinding?

    public init(
        runID: String,
        state: ExecutionState,
        target: ObservationTarget,
        configuration: CaptureConfiguration,
        geometryState: CaptureGeometryState,
        localization: ObservationLocalization,
        observationBudgetNanos: UInt64,
        explicitLineRequestBinding: ExplicitLineRequestBinding? = nil
    ) {
        self.runID = runID
        self.state = state
        self.target = target
        self.configuration = configuration
        self.geometryState = geometryState
        self.localization = localization
        self.observationBudgetNanos = observationBudgetNanos
        self.explicitLineRequestBinding = explicitLineRequestBinding
    }
}

public struct ObservationBundle: Equatable, Sendable {
    public let runID: String
    public let sessionID: String
    public let state: ExecutionState
    public let startedAtMonotonicNanos: UInt64
    public let capturedAtMonotonicNanos: UInt64
    public let endedAtMonotonicNanos: UInt64
    public let deadlineMonotonicNanos: UInt64
    public let epoch: UInt64
    public let target: ObservationTarget
    public let process: ProcessInstanceID
    public let signingIdentity: String?
    public let postProcess: ProcessInstanceID
    public let postSigningIdentity: String?
    public let postAXIdentity: AXIdentityRead
    public let window: WindowIdentity
    public let frame: CapturedFrameRecord
    public let framePNGData: Data
    public let ocrSourceImageSHA256: String
    public let ocrItems: [OcrItem]
    public let cardRegions: [AlbumCardRegion]
    public let candidate: StructuralCandidate?
    public let candidateRefusal: StructuralLocatorRefusal?
    public let preInventory: [SCWindowSnapshot]
    public let postInventory: [SCWindowSnapshot]
    public let cgInventory: [CGWindowSnapshot]
    public let axIdentity: AXIdentityRead
    public let localization: ObservationLocalization
    public var explicitLineRequestBinding: ExplicitLineRequestBinding? = nil

    public var surfaceBinding: SurfaceBinding {
        SurfaceBinding(
            bundleID: window.bundleID,
            process: process,
            windowID: window.windowID,
            captureEpoch: epoch,
            frameSHA256: frame.imageSHA256
        )
    }

    /// Recomputes every cross-field invariant from the retained bytes. Callers
    /// must not treat a decoded bundle as valid without this check.
    public func validated() throws {
        guard !runID.isEmpty, !sessionID.isEmpty, epoch > 0 else {
            throw ObservationRefusal.invalidBundle("empty runID/sessionID or zero epoch")
        }
        guard startedAtMonotonicNanos <= capturedAtMonotonicNanos,
              capturedAtMonotonicNanos <= endedAtMonotonicNanos,
              endedAtMonotonicNanos <= deadlineMonotonicNanos else {
            throw ObservationRefusal.invalidBundle(
                "non-monotonic session timestamps or deadline breach"
            )
        }
        guard window.bundleID == target.bundleID,
              window.process.pid == target.pid,
              process == window.process else {
            throw ObservationRefusal.identityMismatch(["bundle/pid identity mismatch inside the bundle"])
        }
        guard postProcess == process,
              postSigningIdentity == signingIdentity,
              postAXIdentity == axIdentity,
              window.ax == axIdentity else {
            throw ObservationRefusal.identityMismatch(["process, signing or AX identity changed during capture"])
        }
        guard frame.epoch == epoch,
              window.captureEpoch == epoch,
              window.captureImageSHA256 == frame.imageSHA256 else {
            throw ObservationRefusal.invalidBundle("frame/identity epoch or image hash mismatch")
        }
        guard frame.validity == .valid else {
            // These are record fields, not validated PNG measurements: the
            // invalid-frame guard precedes retained-image verification.
            let recordedGeometry = "recordedFrameGeometry(imagePx=[w=\(frame.imageWidthPx),h=\(frame.imageHeightPx)], expectedPt=[w=\(frame.expectedBBoxPt.width),h=\(frame.expectedBBoxPt.height)], pointPixelScale=\(frame.scale), backingScaleFactor=\(frame.backingScaleFactor))"
            throw ObservationRefusal.invalidFrameGeometry(frame.violations + [recordedGeometry])
        }
        if frame.captureKind == .explicitLineWindows || explicitLineRequestBinding != nil {
            try ExplicitLineCaptureSelection.validate(binding: explicitLineRequestBinding, target: target,
                mainID: window.windowID, preInventory: preInventory, postInventory: postInventory, frame: frame)
        } else if frame.explicitLineSelectionWitness != nil {
            throw ObservationRefusal.invalidBundle("legacy capture cannot carry explicit LINE selection witness")
        }
        guard !framePNGData.isEmpty,
              EvidenceIO.sha256Hex(framePNGData) == frame.imageSHA256 else {
            throw ObservationRefusal.retainedImageMismatch("retained PNG bytes do not match the recorded image SHA")
        }
        guard ocrSourceImageSHA256 == frame.imageSHA256 else {
            throw ObservationRefusal.retainedImageMismatch("OCR did not run on the retained image")
        }
        guard let decoded = ObservationBundle.decodePNG(framePNGData),
              decoded.width == frame.imageWidthPx,
              decoded.height == frame.imageHeightPx else {
            throw ObservationRefusal.retainedImageMismatch("retained PNG does not decode to the recorded dimensions")
        }
        let cg = try Self.targetCGEntry(
            target: target, windowID: window.windowID,
            preInventory: preInventory, postInventory: postInventory, cgInventory: cgInventory
        )
        guard let post = postInventory.first(where: { $0.windowID == window.windowID }) else {
            throw ObservationRefusal.inventoryChanged("target missing from retained post inventory")
        }
        guard Self.framesAgree(window.windowFrame, post.frame),
              window.cgEntry.windowID == cg.windowNumber,
              window.cgEntry.ownerPID == cg.ownerPID,
              window.cgEntry.layer == cg.layer,
              window.cgEntry.frame == cg.frame else {
            throw ObservationRefusal.inventoryChanged("stored identity does not match the retained inventories")
        }
        let fresh = FreshWindowObservation(
            bundleID: post.ownerBundleID ?? "",
            process: postProcess,
            windowID: post.windowID,
            frame: post.frame,
            layer: post.windowLayer,
            isOnScreen: post.isOnScreen
        )
        let violations = WindowIdentityValidator.validate(
            identity: window,
            against: fresh,
            maxFrameDeltaPt: 0.5,
            currentEpoch: epoch
        )
        guard violations.isEmpty else {
            throw ObservationRefusal.identityMismatch(violations.map(\.description))
        }
        guard post.ownerPID == target.pid else {
            throw ObservationRefusal.inventoryChanged("post inventory owner pid mismatch")
        }
        guard axIdentity.role?.isEmpty == false else {
            throw ObservationRefusal.identityMismatch(["AX identity for the target window is unreadable"])
        }
        // Plan C3: AX evidence must be affirmatively tied to the observed
        // window. A read that cannot name its binding method is not evidence
        // about this window and is refused instead of being accepted as proof.
        guard axIdentity.isBoundToWindow else {
            throw ObservationRefusal.identityMismatch([
                "AX identity is not bound to the target window (matchMethod missing)",
            ])
        }
        switch localization {
        case .none:
            guard candidate == nil, candidateRefusal == nil else {
                throw ObservationRefusal.invalidBundle("localization=none cannot carry structural output")
            }
        case .albumCards, .albumEllipsis, .saveAllMenuRows:
            guard (candidate == nil) != (candidateRefusal == nil) else {
                throw ObservationRefusal.invalidBundle("localization must record exactly one candidate or refusal")
            }
        }
        if let candidate, candidate.binding != surfaceBinding {
            throw ObservationRefusal.invalidBundle("structural candidate is not bound to this bundle")
        }
    }

    public static func decodePNG(_ data: Data) -> CGImage? {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil) else { return nil }
        return CGImageSourceCreateImageAtIndex(source, 0, nil)
    }

    private static func validFrame(_ frame: CGRect) -> Bool {
        [frame.origin.x, frame.origin.y, frame.size.width, frame.size.height].allSatisfy(\.isFinite)
            && frame.width > 0 && frame.height > 0
    }

    private static func framesAgree(_ lhs: CGRect, _ rhs: CGRect) -> Bool {
        guard validFrame(lhs), validFrame(rhs) else { return false }
        return abs(lhs.origin.x - rhs.origin.x) <= 0.5
            && abs(lhs.origin.y - rhs.origin.y) <= 0.5
            && abs(lhs.width - rhs.width) <= 0.5
            && abs(lhs.height - rhs.height) <= 0.5
    }

    /// Checks the one explicitly retained session CG snapshot. AX's native
    /// adapter may read CG separately; this is not atomic OS acquisition.
    fileprivate static func targetCGEntry(
        target: ObservationTarget,
        windowID: UInt32,
        preInventory: [SCWindowSnapshot],
        postInventory: [SCWindowSnapshot],
        cgInventory: [CGWindowSnapshot]
    ) throws -> CGWindowSnapshot {
        let pre = WindowSensor.mainWindowCandidates(in: preInventory, bundleID: target.bundleID, pid: target.pid)
        let post = WindowSensor.mainWindowCandidates(in: postInventory, bundleID: target.bundleID, pid: target.pid)
        let cg = cgInventory.filter { $0.windowNumber == windowID }
        guard pre.count == 1, post.count == 1,
              pre[0].windowID == windowID, post[0].windowID == windowID,
              preInventory.filter({ $0.windowID == windowID }).count == 1,
              postInventory.filter({ $0.windowID == windowID }).count == 1,
              cg.count == 1, cg[0].layer == 0, cg[0].ownerPID == target.pid else {
            throw ObservationRefusal.inventoryChanged("target identity is absent, ambiguous or inconsistent across inventories")
        }
        guard framesAgree(pre[0].frame, post[0].frame),
              framesAgree(pre[0].frame, cg[0].frame),
              framesAgree(post[0].frame, cg[0].frame) else {
            throw ObservationRefusal.inventoryChanged("target geometry is invalid or differs across SCK/CG inventories")
        }
        return cg[0]
    }
}

/// One serialized native observation session. Concurrent use is refused, not
/// queued: an interleaved capture would mix epochs for a single state.
public actor NativeObservationSession {
    public let sessionID: String
    private let source: any ObservationSource
    private let ocr: any OcrPerforming
    private var captureInProgress = false
    private var completedCaptures = 0

    public init(
        sessionID: String,
        source: any ObservationSource,
        ocr: any OcrPerforming = VisionOcrEngine()
    ) {
        self.sessionID = sessionID
        self.source = source
        self.ocr = ocr
    }

    public var captureCount: Int { completedCaptures }

    public func capture(_ request: NativeObservationRequest) async throws -> ObservationBundle {
        try Task.checkCancellation()
        guard !captureInProgress else { throw ObservationRefusal.sessionBusy }
        captureInProgress = true
        defer { captureInProgress = false }

        let started = source.monotonicNanos()
        let (deadline, overflow) = started.addingReportingOverflow(request.observationBudgetNanos)
        guard !overflow, request.observationBudgetNanos > 0 else {
            throw ObservationRefusal.invalidBundle("observation deadline overflow or zero budget")
        }
        try checkDeadline(deadline, now: started, stage: "start")

        // Process lifetime brackets every native fact retained in the bundle.
        let process: ProcessInstanceID
        do {
            process = try source.processInstance(pid: request.target.pid)
        } catch let refusal as ObservationRefusal {
            throw refusal
        } catch {
            throw ObservationRefusal.observerFailure(stage: "processIdentity", detail: String(describing: error))
        }

        let preInventory: [SCWindowSnapshot]
        do {
            preInventory = try await source.enumerateWindows()
        } catch {
            throw ObservationRefusal.observerFailure(stage: "enumerateWindows", detail: String(describing: error))
        }
        let candidates = WindowSensor.mainWindowCandidates(
            in: preInventory,
            bundleID: request.target.bundleID,
            pid: request.target.pid
        )
        guard candidates.count == 1, let main = candidates.first else {
            throw ObservationRefusal.targetWindowNotUnique(found: candidates.count)
        }
        let children = WindowSensor.childWindows(of: main, in: preInventory)
        let includedWindows: [SCWindowSnapshot]
        if request.configuration.kind == .explicitLineWindows {
            guard let binding = request.explicitLineRequestBinding else {
                throw ObservationRefusal.invalidBundle("explicit LINE original request binding required")
            }
            try ExplicitLineCaptureSelection.validateRequest(binding, configuration: request.configuration,
                state: request.geometryState, target: request.target, preInventory: preInventory)
            includedWindows = try ExplicitLineCaptureSelection.selectedWindows(in: preInventory, target: request.target)
        } else {
            guard request.explicitLineRequestBinding == nil else {
                throw ObservationRefusal.invalidBundle("legacy request cannot carry explicit LINE binding")
            }
            includedWindows = request.configuration.includeChildWindows ? [main] + children : [main]
        }

        let signingIdentity: String?
        let axIdentity: AXIdentityRead
        do {
            signingIdentity = try source.signingIdentity(pid: request.target.pid)
            axIdentity = try source.readAXIdentity(pid: request.target.pid, windowID: main.windowID)
        } catch let refusal as ObservationRefusal {
            throw refusal
        } catch {
            throw ObservationRefusal.observerFailure(stage: "processIdentity", detail: String(describing: error))
        }

        let epoch = source.nextEpoch()
        let captured: ObservationCapturedImage
        do {
            captured = try await source.captureTarget(
                window: main,
                includedWindows: includedWindows,
                configuration: request.configuration,
                geometryState: request.geometryState,
                epoch: epoch
            )
        } catch {
            throw ObservationRefusal.observerFailure(stage: "captureTarget", detail: String(describing: error))
        }
        let capturedAt = source.monotonicNanos()
        try Task.checkCancellation()
        try checkDeadline(deadline, now: capturedAt, stage: "capture")

        guard let pngData = FrameCaptureSupport.pngData(of: captured.image) else {
            throw ObservationRefusal.observerFailure(stage: "retainImage", detail: "PNG encoding failed")
        }
        let imageSHA = EvidenceIO.sha256Hex(pngData)
        guard captured.record.imageSHA256 == imageSHA else {
            throw ObservationRefusal.retainedImageMismatch("capture record hash does not match the retained PNG bytes")
        }
        guard let retainedImage = ObservationBundle.decodePNG(pngData) else {
            throw ObservationRefusal.retainedImageMismatch("retained PNG failed to decode for OCR")
        }

        let ocrItems: [OcrItem]
        do {
            ocrItems = try await ocr.recognize(image: retainedImage)
        } catch {
            throw ObservationRefusal.observerFailure(stage: "ocr", detail: String(describing: error))
        }
        try Task.checkCancellation()
        try checkDeadline(deadline, now: source.monotonicNanos(), stage: "ocr")

        let postInventory: [SCWindowSnapshot]
        do {
            postInventory = try await source.enumerateWindows()
        } catch {
            throw ObservationRefusal.observerFailure(stage: "postEnumerateWindows", detail: String(describing: error))
        }
        let postSigningIdentity: String?
        let postAXIdentity: AXIdentityRead
        do {
            postSigningIdentity = try source.signingIdentity(pid: request.target.pid)
            postAXIdentity = try source.readAXIdentity(pid: request.target.pid, windowID: main.windowID)
        } catch let refusal as ObservationRefusal {
            throw refusal
        } catch {
            throw ObservationRefusal.observerFailure(stage: "postProcessIdentity", detail: String(describing: error))
        }
        let cgInventory = source.cgInventory()
        let postProcess: ProcessInstanceID
        do {
            postProcess = try source.processInstance(pid: request.target.pid)
        } catch let refusal as ObservationRefusal {
            throw refusal
        } catch {
            throw ObservationRefusal.observerFailure(stage: "postProcessIdentity", detail: String(describing: error))
        }
        guard postProcess == process, postSigningIdentity == signingIdentity, postAXIdentity == axIdentity else {
            throw ObservationRefusal.identityMismatch(["process, signing or AX identity changed during capture"])
        }
        let cgEntry = try ObservationBundle.targetCGEntry(
            target: request.target, windowID: main.windowID,
            preInventory: preInventory, postInventory: postInventory, cgInventory: cgInventory
        )

        let window = WindowIdentity(
            bundleID: request.target.bundleID,
            process: process,
            windowID: main.windowID,
            windowFrame: main.frame,
            ax: axIdentity,
            cgEntry: CGWindowEntryRecord(
                windowID: cgEntry.windowNumber,
                frame: cgEntry.frame,
                layer: cgEntry.layer,
                ownerPID: cgEntry.ownerPID,
                ownerName: main.ownerName ?? ""
            ),
            captureEpoch: epoch,
            captureImageSHA256: imageSHA
        )

        let binding = SurfaceBinding(
            bundleID: request.target.bundleID,
            process: process,
            windowID: main.windowID,
            captureEpoch: epoch,
            frameSHA256: imageSHA
        )
        let imageBounds = CGRect(
            origin: .zero,
            size: CGSize(width: captured.image.width, height: captured.image.height)
        )
        let (regions, candidate, refusal) = deriveStructure(
            localization: request.localization,
            image: retainedImage,
            ocrItems: ocrItems,
            imageBounds: imageBounds,
            binding: binding
        )

        let ended = source.monotonicNanos()
        try checkDeadline(deadline, now: ended, stage: "end")

        let bundle = ObservationBundle(
            runID: request.runID,
            sessionID: sessionID,
            state: request.state,
            startedAtMonotonicNanos: started,
            capturedAtMonotonicNanos: capturedAt,
            endedAtMonotonicNanos: ended,
            deadlineMonotonicNanos: deadline,
            epoch: epoch,
            target: request.target,
            process: process,
            signingIdentity: signingIdentity,
            postProcess: postProcess,
            postSigningIdentity: postSigningIdentity,
            postAXIdentity: postAXIdentity,
            window: window,
            frame: captured.record,
            framePNGData: pngData,
            ocrSourceImageSHA256: imageSHA,
            ocrItems: ocrItems,
            cardRegions: regions,
            candidate: candidate,
            candidateRefusal: refusal,
            preInventory: preInventory,
            postInventory: postInventory,
            cgInventory: cgInventory,
            axIdentity: axIdentity,
            localization: request.localization,
            explicitLineRequestBinding: request.explicitLineRequestBinding
        )
        try bundle.validated()
        try checkDeadline(deadline, now: source.monotonicNanos(), stage: "validation")
        completedCaptures += 1
        return bundle
    }

    private func checkDeadline(_ deadline: UInt64, now: UInt64, stage: String) throws {
        guard now <= deadline else { throw ObservationRefusal.deadlineExceeded(stage: stage) }
    }

    private func deriveStructure(
        localization: ObservationLocalization,
        image: CGImage,
        ocrItems: [OcrItem],
        imageBounds: CGRect,
        binding: SurfaceBinding
    ) -> ([AlbumCardRegion], StructuralCandidate?, StructuralLocatorRefusal?) {
        switch localization {
        case .none:
            return ([], nil, nil)
        case let .albumCards(title, count):
            let regions = StructuralLocators.segmentAlbumCards(items: ocrItems, imageBounds: imageBounds)
            switch StructuralLocators.locateAlbumCard(
                items: ocrItems,
                title: title,
                count: count,
                regions: regions,
                binding: binding
            ) {
            case let .candidate(candidate):
                return (regions, candidate, nil)
            case let .refused(refusal, _):
                return (regions, nil, refusal)
            }
        case let .albumEllipsis(title, groupTitle):
            let titleMatches = OcrTextIdentity.exactMatches(in: ocrItems, expected: title)
            guard titleMatches.count == 1 else {
                return ([], nil, titleMatches.count > 1 ? .ambiguousIdentity : .missingIdentity)
            }
            let groupBox: CGRect? = groupTitle.flatMap { expected in
                let matches = OcrTextIdentity.exactMatches(in: ocrItems, expected: expected)
                return matches.count == 1 ? matches[0].boundingBoxCapturePx : nil
            }
            if let groupTitle {
                let matches = OcrTextIdentity.exactMatches(in: ocrItems, expected: groupTitle)
                guard matches.count == 1 else {
                    return ([], nil, matches.isEmpty ? .missingIdentity : .ambiguousIdentity)
                }
            }
            do {
                switch try AlbumEllipsisLocator.locate(
                    image: image,
                    ocrItems: ocrItems,
                    titleBoxCapturePx: titleMatches[0].boundingBoxCapturePx,
                    groupTitleBoxCapturePx: groupBox,
                    binding: binding
                ) {
                case let .candidate(candidate):
                    return ([], candidate, nil)
                case let .refused(refusal, _):
                    return ([], nil, refusal)
                }
            } catch {
                return ([], nil, .unsafeGeometry)
            }
        case let .saveAllMenuRows(menuBounds, addressableBounds):
            // Locator geometry is fail-closed against the retained frame: the
            // configured menu and addressable regions must lie inside the
            // image the OCR actually ran on, so geometry captured for another
            // surface can never produce a candidate.
            guard imageBounds.contains(menuBounds), imageBounds.contains(addressableBounds) else {
                return ([], nil, .unsafeGeometry)
            }
            let rows = ocrItems
                .filter { StructuralLocators.lineAlbumMenuReference.contains($0.text) }
                .map { MenuRowObservation(text: $0.text, bandCapturePx: $0.boundingBoxCapturePx) }
            switch StructuralLocators.locateSaveAll(
                rows: rows,
                menuBounds: menuBounds,
                addressableBounds: addressableBounds,
                binding: binding
            ) {
            case let .candidate(candidate):
                return ([], candidate, nil)
            case let .refused(refusal, _):
                return ([], nil, refusal)
            }
        }
    }
}
