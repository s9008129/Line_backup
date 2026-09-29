import CoreGraphics
import CryptoKit
import Foundation
import ImageIO

// MARK: - Native observation session (plan R4 §C3)
//
// One serialized session produces immutable ObservationBundles. Every bundle
// carries the retained screenshot bytes, the record of the geometry they were
// captured under, the Vision results produced from that exact image, the bound
// window/process identity, pre/post inventories, AX evidence and the tripwire
// cursor. Freshness is a property of the captured artifact, never of a caller
// flag: a new observation has new provenance, and equal pixels do not make an
// old observation fresh.

public struct ObservationInventorySnapshot: Equatable, Codable, Sendable {
    public let scWindows: [SCWindowSnapshot]
    public let cgWindows: [CGWindowSnapshot]
    public let sampledAtUptime: Double

    public init(scWindows: [SCWindowSnapshot], cgWindows: [CGWindowSnapshot], sampledAtUptime: Double) {
        self.scWindows = scWindows
        self.cgWindows = cgWindows
        self.sampledAtUptime = sampledAtUptime
    }

    public func containsFreshWindow(bundleID: String, pid: Int32, windowID: UInt32, frame: CGRect) -> Bool {
        scWindows.contains {
            $0.windowID == windowID && $0.ownerPID == pid && $0.ownerBundleID == bundleID
                && $0.isOnScreen && $0.windowLayer == 0 && $0.frame == frame
        }
    }
}

public struct AXEvidenceSnapshot: Equatable, Codable, Sendable {
    public let pid: Int32
    public let windowID: UInt32
    public let role: String?
    public let subrole: String?
    public let title: String?
    public let sampledAtUptime: Double

    public init(pid: Int32, windowID: UInt32, role: String?, subrole: String?, title: String?, sampledAtUptime: Double) {
        self.pid = pid
        self.windowID = windowID
        self.role = role
        self.subrole = subrole
        self.title = title
        self.sampledAtUptime = sampledAtUptime
    }
}

/// The OS edge of one capture. Production wraps FrameCaptureService; tests
/// inject retained synthetic frames. The boundary may not decide readiness.
public protocol ObservationBoundary: Sendable {
    func inventory() async throws -> ObservationInventorySnapshot
    func capture(
        state: CaptureGeometryState,
        requestedState: String,
        expectedBundleID: String,
        expectedPID: Int32,
        deadlineUptime: Double
    ) async throws -> ObservationCaptureResult
    func recognize(image: CGImage) async throws -> [OcrItem]
    func axEvidence(pid: Int32, windowID: UInt32) async throws -> AXEvidenceSnapshot
    func signingIdentity(pid: Int32) async -> String?
    func monotonicNow() -> Double
}

public struct ObservationCaptureResult: Sendable {
    public let image: CGImage
    public let pngData: Data
    public let configuration: CaptureConfiguration
    public let includedWindows: [SCWindowSnapshot]
    public let sourceRect: CGRect?
    public let expectedBBoxPt: CGRect
    public let actualBBoxPt: CGRect
    public let imageWidthPx: Int
    public let imageHeightPx: Int
    public let perSideSizeDeltaPt: SideDelta
    public let scale: Double
    public let backingScaleFactor: Double
    public let stateKey: String
    public let ruleID: String
    public let ruleSHA256: String?
    public let validity: FrameValidity
    public let violations: [String]
    public let identityTemplate: WindowIdentity?

    public init(
        image: CGImage,
        pngData: Data,
        configuration: CaptureConfiguration,
        includedWindows: [SCWindowSnapshot],
        sourceRect: CGRect?,
        expectedBBoxPt: CGRect,
        actualBBoxPt: CGRect,
        imageWidthPx: Int,
        imageHeightPx: Int,
        perSideSizeDeltaPt: SideDelta,
        scale: Double,
        backingScaleFactor: Double,
        stateKey: String,
        ruleID: String,
        ruleSHA256: String?,
        validity: FrameValidity,
        violations: [String],
        identityTemplate: WindowIdentity?
    ) {
        self.image = image
        self.pngData = pngData
        self.configuration = configuration
        self.includedWindows = includedWindows
        self.sourceRect = sourceRect
        self.expectedBBoxPt = expectedBBoxPt
        self.actualBBoxPt = actualBBoxPt
        self.imageWidthPx = imageWidthPx
        self.imageHeightPx = imageHeightPx
        self.perSideSizeDeltaPt = perSideSizeDeltaPt
        self.scale = scale
        self.backingScaleFactor = backingScaleFactor
        self.stateKey = stateKey
        self.ruleID = ruleID
        self.ruleSHA256 = ruleSHA256
        self.validity = validity
        self.violations = violations
        self.identityTemplate = identityTemplate
    }
}

public struct ObservationBundle: Equatable, Codable, Sendable {
    public let schemaVersion: Int
    public let sessionID: String
    public let runID: String
    public let captureID: String
    public let sequence: Int
    public let requestedState: String
    public let captureStateKey: String
    public let epoch: UInt64
    public let startedAtUptime: Double
    public let endedAtUptime: Double
    public let deadlineUptime: Double
    public let bundleID: String
    public let process: ProcessInstanceID
    public let signingIdentity: String?
    public let identity: WindowIdentity
    public let preInventory: ObservationInventorySnapshot
    public let postInventory: ObservationInventorySnapshot
    public let axEvidence: AXEvidenceSnapshot
    public let imagePNG: Data
    public let pngSHA256: String
    public let retainedImagePath: String
    public let captureConfiguration: CaptureConfiguration
    public let includedWindows: [SCWindowSnapshot]
    public let sourceRect: CGRect?
    public let expectedBBoxPt: CGRect
    public let actualBBoxPt: CGRect
    public let imageWidthPx: Int
    public let imageHeightPx: Int
    public let perSideSizeDeltaPt: SideDelta
    public let scale: Double
    public let backingScaleFactor: Double
    public let ruleID: String
    public let ruleSHA256: String?
    public let validity: FrameValidity
    public let violations: [String]
    public let ocrItems: [OcrItem]
    public let surfaceBinding: SurfaceBinding

    public var capturePixelBounds: CGRect {
        CGRect(x: 0, y: 0, width: Double(imageWidthPx), height: Double(imageHeightPx))
    }

    public func decodedRetainedImage() throws -> CGImage {
        guard let source = CGImageSourceCreateWithData(imagePNG as CFData, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw ObservationError.retainedImageUndecodable
        }
        return image
    }
}

public enum ObservationError: Error, Equatable, CustomStringConvertible {
    case sessionAlreadyAdvanced(Double)
    case captureDeadlineExceeded(Double)
    case ambiguousMainWindowCensus(Int)
    case missingMainWindow
    case processInstanceUnavailable(Int32)
    case processInstanceChanged(expected: ProcessInstanceID, actual: ProcessInstanceID)
    case emptyImage
    case pngEncodingMissing
    case pngHashMismatch(String)
    case invalidFrame([String])
    case ocrFailed(String)
    case retainedImageWriteFailed(String)
    case retainedImageUndecodable
    case authorizationMismatch(String)
    case inventorySampledAfterSessionStart(Double, Double)

    public var description: String {
        switch self {
        case let .sessionAlreadyAdvanced(now): return "sessionAlreadyAdvanced(now=\(now))"
        case let .captureDeadlineExceeded(deadline): return "captureDeadlineExceeded(deadline=\(deadline))"
        case let .ambiguousMainWindowCensus(count): return "ambiguousMainWindowCensus(\(count))"
        case .missingMainWindow: return "missingMainWindow"
        case let .processInstanceUnavailable(pid): return "processInstanceUnavailable(pid=\(pid))"
        case let .processInstanceChanged(expected, actual): return "processInstanceChanged(expected=\(expected), actual=\(actual))"
        case .emptyImage: return "emptyImage"
        case .pngEncodingMissing: return "pngEncodingMissing"
        case let .pngHashMismatch(detail): return "pngHashMismatch(\(detail))"
        case let .invalidFrame(violations): return "invalidFrame(\(violations))"
        case let .ocrFailed(detail): return "ocrFailed(\(detail))"
        case let .retainedImageWriteFailed(detail): return "retainedImageWriteFailed(\(detail))"
        case .retainedImageUndecodable: return "retainedImageUndecodable"
        case let .authorizationMismatch(detail): return "authorizationMismatch(\(detail))"
        case let .inventorySampledAfterSessionStart(inventory, started):
            return "inventorySampledAfterSessionStart(inventory=\(inventory), started=\(started))"
        }
    }
}

public enum ObservationBundleValidationError: Error, Equatable, CustomStringConvertible {
    case sessionMismatch(expected: String, actual: String)
    case runMismatch(expected: String, actual: String)
    case missingImage
    case imageHashMismatch
    case imageDimensionsInvalid
    case nonMonotonicTimes
    case deadlineExceeded
    case invalidFrame([String])
    case identityEpochMismatch
    case identityImageMismatch
    case bindingMismatch
    case staleEpoch(expected: UInt64, actual: UInt64)
    case windowNotInPostCensus
    case ocrOutsideImage(String)
    case sequenceNotPositive

    public var description: String {
        switch self {
        case let .sessionMismatch(expected, actual): return "sessionMismatch(expected=\(expected), actual=\(actual))"
        case let .runMismatch(expected, actual): return "runMismatch(expected=\(expected), actual=\(actual))"
        case .missingImage: return "missingImage"
        case .imageHashMismatch: return "imageHashMismatch"
        case .imageDimensionsInvalid: return "imageDimensionsInvalid"
        case .nonMonotonicTimes: return "nonMonotonicTimes"
        case .deadlineExceeded: return "deadlineExceeded"
        case let .invalidFrame(violations): return "invalidFrame(\(violations))"
        case .identityEpochMismatch: return "identityEpochMismatch"
        case .identityImageMismatch: return "identityImageMismatch"
        case .bindingMismatch: return "bindingMismatch"
        case let .staleEpoch(expected, actual): return "staleEpoch(expected=\(expected), actual=\(actual))"
        case .windowNotInPostCensus: return "windowNotInPostCensus"
        case let .ocrOutsideImage(detail): return "ocrOutsideImage(\(detail))"
        case .sequenceNotPositive: return "sequenceNotPositive"
        }
    }
}

public enum ObservationBundleValidator {
    public static func validate(
        _ bundle: ObservationBundle,
        expectedSessionID: String,
        expectedRunID: String,
        requireValidFrame: Bool = true
    ) throws {
        guard bundle.sessionID == expectedSessionID else {
            throw ObservationBundleValidationError.sessionMismatch(expected: expectedSessionID, actual: bundle.sessionID)
        }
        guard bundle.runID == expectedRunID else {
            throw ObservationBundleValidationError.runMismatch(expected: expectedRunID, actual: bundle.runID)
        }
        guard bundle.schemaVersion == 1 else { throw ObservationBundleValidationError.imageDimensionsInvalid }
        guard bundle.sequence >= 1 else { throw ObservationBundleValidationError.sequenceNotPositive }
        guard !bundle.imagePNG.isEmpty else { throw ObservationBundleValidationError.missingImage }
        let computed = EvidenceIO.sha256Hex(bundle.imagePNG)
        guard computed == bundle.pngSHA256 else { throw ObservationBundleValidationError.imageHashMismatch }
        guard bundle.imageWidthPx > 0, bundle.imageHeightPx > 0,
              Double(bundle.imageWidthPx) >= bundle.actualBBoxPt.width * bundle.scale - 1,
              bundle.scale.isFinite, bundle.scale > 0, bundle.backingScaleFactor > 0 else {
            throw ObservationBundleValidationError.imageDimensionsInvalid
        }
        guard bundle.startedAtUptime <= bundle.endedAtUptime, bundle.endedAtUptime <= bundle.deadlineUptime else {
            throw ObservationBundleValidationError.nonMonotonicTimes
        }
        guard bundle.preInventory.sampledAtUptime <= bundle.startedAtUptime,
              bundle.postInventory.sampledAtUptime >= bundle.endedAtUptime,
              bundle.postInventory.sampledAtUptime <= bundle.deadlineUptime else {
            throw ObservationBundleValidationError.nonMonotonicTimes
        }
        guard bundle.deadlineUptime >= bundle.endedAtUptime else {
            throw ObservationBundleValidationError.deadlineExceeded
        }
        if requireValidFrame {
            guard bundle.validity == .valid else {
                throw ObservationBundleValidationError.invalidFrame(bundle.violations)
            }
        }
        guard bundle.identity.captureEpoch == bundle.epoch else {
            throw ObservationBundleValidationError.identityEpochMismatch
        }
        guard bundle.identity.captureImageSHA256 == bundle.pngSHA256 else {
            throw ObservationBundleValidationError.identityImageMismatch
        }
        let expectedBinding = SurfaceBinding(
            bundleID: bundle.identity.bundleID,
            process: bundle.identity.process,
            windowID: bundle.identity.windowID,
            captureEpoch: bundle.epoch,
            frameSHA256: bundle.pngSHA256
        )
        guard bundle.surfaceBinding == expectedBinding,
              bundle.bundleID == bundle.identity.bundleID,
              bundle.process == bundle.identity.process else {
            throw ObservationBundleValidationError.bindingMismatch
        }
        guard bundle.postInventory.containsFreshWindow(
            bundleID: bundle.identity.bundleID,
            pid: bundle.identity.process.pid,
            windowID: bundle.identity.windowID,
            frame: bundle.identity.windowFrame
        ) else {
            throw ObservationBundleValidationError.windowNotInPostCensus
        }
        let imageBounds = CGRect(x: 0, y: 0, width: Double(bundle.imageWidthPx), height: Double(bundle.imageHeightPx))
        for item in bundle.ocrItems {
            guard imageBounds.insetBy(dx: -0.5, dy: -0.5).contains(item.boundingBoxCapturePx) else {
                throw ObservationBundleValidationError.ocrOutsideImage(item.text)
            }
            guard item.quadCapturePx.allSatisfy({ imageBounds.insetBy(dx: -0.5, dy: -0.5).contains($0.cgPoint) }) else {
                throw ObservationBundleValidationError.ocrOutsideImage(item.text)
            }
        }
    }

    public static func requireFresh(bundle: ObservationBundle, currentEpoch: UInt64) throws {
        guard bundle.epoch == currentEpoch else {
            throw ObservationBundleValidationError.staleEpoch(expected: currentEpoch, actual: bundle.epoch)
        }
    }
}

public actor NativeObservationSession {
    public let sessionID: String
    public let runID: String
    public let targetBundleID: String
    public let targetPID: Int32
    public let evidenceDirectory: URL
    private let boundary: any ObservationBoundary
    private var sequence = 0
    private var lastEndedAtUptime: Double = 0
    private var retainedImageURLs: [String: URL] = [:]
    public private(set) var currentEpoch: UInt64 = 0

    public init(
        sessionID: String,
        runID: String,
        targetBundleID: String,
        targetPID: Int32,
        evidenceDirectory: URL,
        boundary: any ObservationBoundary
    ) throws {
        self.sessionID = sessionID
        self.runID = runID
        self.targetBundleID = targetBundleID
        self.targetPID = targetPID
        self.evidenceDirectory = evidenceDirectory
        self.boundary = boundary
        try EvidenceIO.ensureDirectory(evidenceDirectory.appendingPathComponent("observations", isDirectory: true))
    }

    public func retainedImageURL(for captureID: String) -> URL? {
        retainedImageURLs[captureID]
    }

    public func observe(
        state: CaptureGeometryState,
        requestedState: String,
        timeoutSeconds: Double = 10
    ) async throws -> ObservationBundle {
        let entry = boundary.monotonicNow()
        guard entry >= lastEndedAtUptime else {
            throw ObservationError.sessionAlreadyAdvanced(entry)
        }
        let preInventory = try await boundary.inventory()
        let started = boundary.monotonicNow()
        guard preInventory.sampledAtUptime <= started else {
            throw ObservationError.inventorySampledAfterSessionStart(preInventory.sampledAtUptime, started)
        }
        let deadline = started + timeoutSeconds

        let capture = try await boundary.capture(
            state: state,
            requestedState: requestedState,
            expectedBundleID: targetBundleID,
            expectedPID: targetPID,
            deadlineUptime: deadline
        )
        let capturedAt = boundary.monotonicNow()
        guard capturedAt <= deadline else {
            throw ObservationError.captureDeadlineExceeded(deadline)
        }
        guard capture.image.width == capture.imageWidthPx, capture.image.height == capture.imageHeightPx,
              capture.image.width > 0, capture.image.height > 0 else {
            throw ObservationError.emptyImage
        }
        guard !capture.pngData.isEmpty else { throw ObservationError.pngEncodingMissing }
        let pngSHA = EvidenceIO.sha256Hex(capture.pngData)
        if let reencoded = FrameCaptureSupport.pngSHA256(of: capture.image), reencoded != pngSHA {
            throw ObservationError.pngHashMismatch("retained PNG hash and image re-encode disagree")
        }

        let template = capture.identityTemplate
        guard let template else { throw ObservationError.missingMainWindow }
        guard let liveProcess = ProcessInstanceID.current(pid: template.process.pid) else {
            throw ObservationError.processInstanceUnavailable(template.process.pid)
        }
        guard liveProcess == template.process else {
            throw ObservationError.processInstanceChanged(expected: template.process, actual: liveProcess)
        }

        let ocrItems: [OcrItem]
        do {
            ocrItems = try await boundary.recognize(image: capture.image)
        } catch {
            throw ObservationError.ocrFailed(String(describing: error))
        }

        sequence += 1
        let captureID = "\(sessionID)-\(String(format: "%04d", sequence))"
        let axEvidence = try await boundary.axEvidence(pid: template.process.pid, windowID: template.windowID)
        let signingIdentity = await boundary.signingIdentity(pid: template.process.pid)
        let postInventory = try await boundary.inventory()
        let ended = boundary.monotonicNow()
        guard ended <= deadline else { throw ObservationError.captureDeadlineExceeded(deadline) }

        currentEpoch += 1
        let epoch = currentEpoch
        var identity = template
        identity.captureEpoch = epoch
        identity.captureImageSHA256 = pngSHA

        let retainedURL = evidenceDirectory
            .appendingPathComponent("observations", isDirectory: true)
            .appendingPathComponent("\(captureID).png")
        do {
            _ = try EvidenceIO.writeAtomically(capture.pngData, to: retainedURL, appendOnly: true)
        } catch {
            throw ObservationError.retainedImageWriteFailed(String(describing: error))
        }
        retainedImageURLs[captureID] = retainedURL

        let bundle = ObservationBundle(
            schemaVersion: 1,
            sessionID: sessionID,
            runID: runID,
            captureID: captureID,
            sequence: sequence,
            requestedState: requestedState,
            captureStateKey: capture.stateKey,
            epoch: epoch,
            startedAtUptime: started,
            endedAtUptime: ended,
            deadlineUptime: deadline,
            bundleID: template.bundleID,
            process: template.process,
            signingIdentity: signingIdentity,
            identity: identity,
            preInventory: preInventory,
            postInventory: postInventory,
            axEvidence: axEvidence,
            imagePNG: capture.pngData,
            pngSHA256: pngSHA,
            retainedImagePath: retainedURL.path,
            captureConfiguration: capture.configuration,
            includedWindows: capture.includedWindows,
            sourceRect: capture.sourceRect,
            expectedBBoxPt: capture.expectedBBoxPt,
            actualBBoxPt: capture.actualBBoxPt,
            imageWidthPx: capture.imageWidthPx,
            imageHeightPx: capture.imageHeightPx,
            perSideSizeDeltaPt: capture.perSideSizeDeltaPt,
            scale: capture.scale,
            backingScaleFactor: capture.backingScaleFactor,
            ruleID: capture.ruleID,
            ruleSHA256: capture.ruleSHA256,
            validity: capture.validity,
            violations: capture.violations,
            ocrItems: ocrItems,
            surfaceBinding: SurfaceBinding(
                bundleID: template.bundleID,
                process: template.process,
                windowID: template.windowID,
                captureEpoch: epoch,
                frameSHA256: pngSHA
            )
        )
        lastEndedAtUptime = ended
        return bundle
    }
}
