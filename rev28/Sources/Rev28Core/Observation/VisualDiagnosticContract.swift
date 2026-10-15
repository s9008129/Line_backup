import CoreGraphics
import Foundation

/// Capture-first evidence for the isolated visual-card diagnostic lane. This
/// contract deliberately has no action-capable fields or conversion to a
/// production observation.
public struct VisualDiagnosticArtifactReference: Codable, Equatable, Sendable {
    public let path: String
    public let bytes: Int
    public let sha256: String

    public init(path: String, bytes: Int, sha256: String) {
        self.path = path
        self.bytes = bytes
        self.sha256 = sha256
    }

    public func validated() throws {
        guard path.hasPrefix("harness-development/"), !path.hasPrefix("/"),
              !path.split(separator: "/").contains(".."), bytes > 0,
              sha256.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else {
            throw VisualDiagnosticContractError.invalidReference
        }
    }
}

public struct VisualDiagnosticProcessIdentity: Codable, Equatable, Sendable {
    public let bundleID: String
    public let pid: Int32
    public let startTimeSeconds: Int
    public let startTimeMicroseconds: Int

    public init(bundleID: String, pid: Int32, startTimeSeconds: Int, startTimeMicroseconds: Int) {
        self.bundleID = bundleID
        self.pid = pid
        self.startTimeSeconds = startTimeSeconds
        self.startTimeMicroseconds = startTimeMicroseconds
    }
}

public enum VisualDiagnosticAssociationStatus: String, Codable, Sendable {
    case provisional = "PROVISIONAL"
}

public struct VisualDiagnosticCapturePair: Codable, Equatable, Sendable {
    public let version: Int
    public let kind: String
    public let sessionID: String
    public let cuaFrameID: String
    public let cuaFrame: VisualDiagnosticArtifactReference
    public let cuaRequestStartedAt: String
    public let cuaRequestEndedAt: String
    public let cuaRequestStartMonotonicNanoseconds: String
    public let cuaRequestEndMonotonicNanoseconds: String
    public let sckFrameID: String
    public let sckFrame: VisualDiagnosticArtifactReference
    public let sckRequestStartedAt: String
    public let sckRequestEndedAt: String
    public let sckRequestStartMonotonicNanoseconds: String
    public let sckRequestEndMonotonicNanoseconds: String
    public let nativeInventoryStartedAt: String
    public let nativeInventoryEndedAt: String
    public let nativeInventoryStartMonotonicNanoseconds: String
    public let nativeInventoryEndMonotonicNanoseconds: String
    public let windowScreenAssociationStatus: VisualDiagnosticAssociationStatus
    public let bundleID: String
    public let pid: Int32
    public let processStartTimeSeconds: Int
    public let processStartTimeMicroseconds: Int
    public let windowID: UInt32
    public let displayID: UInt32
    public let widthPixels: Int
    public let heightPixels: Int
    public let nativeScale: Double
    public let pointPixelScale: Double
    public let cuaBoundsPoints: [Double]
    public let sckWindowBoundsPoints: [Double]
    public let displayBoundsPoints: [Double]
    public let captureRecord: CapturedFrameRecord

    public init(version: Int = 1, kind: String = "VISUAL_CARD_DIAGNOSTIC", sessionID: String,
                cuaFrameID: String, cuaFrame: VisualDiagnosticArtifactReference,
                cuaRequestStartedAt: String, cuaRequestEndedAt: String,
                cuaRequestStartMonotonicNanoseconds: String, cuaRequestEndMonotonicNanoseconds: String,
                sckFrameID: String, sckFrame: VisualDiagnosticArtifactReference,
                sckRequestStartedAt: String, sckRequestEndedAt: String,
                sckRequestStartMonotonicNanoseconds: String, sckRequestEndMonotonicNanoseconds: String,
                nativeInventoryStartedAt: String, nativeInventoryEndedAt: String,
                nativeInventoryStartMonotonicNanoseconds: String, nativeInventoryEndMonotonicNanoseconds: String,
                windowScreenAssociationStatus: VisualDiagnosticAssociationStatus = .provisional,
                bundleID: String, pid: Int32, processStartTimeSeconds: Int,
                processStartTimeMicroseconds: Int, windowID: UInt32, displayID: UInt32,
                widthPixels: Int, heightPixels: Int, nativeScale: Double, pointPixelScale: Double,
                cuaBoundsPoints: [Double], sckWindowBoundsPoints: [Double], displayBoundsPoints: [Double],
                captureRecord: CapturedFrameRecord) {
        self.version = version
        self.kind = kind
        self.sessionID = sessionID
        self.cuaFrameID = cuaFrameID
        self.cuaFrame = cuaFrame
        self.cuaRequestStartedAt = cuaRequestStartedAt
        self.cuaRequestEndedAt = cuaRequestEndedAt
        self.cuaRequestStartMonotonicNanoseconds = cuaRequestStartMonotonicNanoseconds
        self.cuaRequestEndMonotonicNanoseconds = cuaRequestEndMonotonicNanoseconds
        self.sckFrameID = sckFrameID
        self.sckFrame = sckFrame
        self.sckRequestStartedAt = sckRequestStartedAt
        self.sckRequestEndedAt = sckRequestEndedAt
        self.sckRequestStartMonotonicNanoseconds = sckRequestStartMonotonicNanoseconds
        self.sckRequestEndMonotonicNanoseconds = sckRequestEndMonotonicNanoseconds
        self.nativeInventoryStartedAt = nativeInventoryStartedAt
        self.nativeInventoryEndedAt = nativeInventoryEndedAt
        self.nativeInventoryStartMonotonicNanoseconds = nativeInventoryStartMonotonicNanoseconds
        self.nativeInventoryEndMonotonicNanoseconds = nativeInventoryEndMonotonicNanoseconds
        self.windowScreenAssociationStatus = windowScreenAssociationStatus
        self.bundleID = bundleID
        self.pid = pid
        self.processStartTimeSeconds = processStartTimeSeconds
        self.processStartTimeMicroseconds = processStartTimeMicroseconds
        self.windowID = windowID
        self.displayID = displayID
        self.widthPixels = widthPixels
        self.heightPixels = heightPixels
        self.nativeScale = nativeScale
        self.pointPixelScale = pointPixelScale
        self.cuaBoundsPoints = cuaBoundsPoints
        self.sckWindowBoundsPoints = sckWindowBoundsPoints
        self.displayBoundsPoints = displayBoundsPoints
        self.captureRecord = captureRecord
    }

    public func validated() throws {
        let cuaStarted = try Self.date(cuaRequestStartedAt)
        let cuaEnded = try Self.date(cuaRequestEndedAt)
        let sckStarted = try Self.date(sckRequestStartedAt)
        let sckEnded = try Self.date(sckRequestEndedAt)
        let inventoryStarted = try Self.date(nativeInventoryStartedAt)
        let inventoryEnded = try Self.date(nativeInventoryEndedAt)
        guard let cuaMonoStart = UInt64(cuaRequestStartMonotonicNanoseconds),
              let cuaMonoEnd = UInt64(cuaRequestEndMonotonicNanoseconds),
              let sckMonoStart = UInt64(sckRequestStartMonotonicNanoseconds),
              let sckMonoEnd = UInt64(sckRequestEndMonotonicNanoseconds),
              let inventoryMonoStart = UInt64(nativeInventoryStartMonotonicNanoseconds),
              let inventoryMonoEnd = UInt64(nativeInventoryEndMonotonicNanoseconds) else {
            throw VisualDiagnosticContractError.invalidCapturePair
        }
        guard version == 1, kind == "VISUAL_CARD_DIAGNOSTIC", !sessionID.isEmpty,
              Self.isHash(cuaFrameID), Self.isHash(sckFrameID), cuaFrame.sha256 == cuaFrameID,
              sckFrame.sha256 == sckFrameID, cuaFrameID != sckFrameID,
              cuaMonoStart <= cuaMonoEnd, cuaMonoEnd <= inventoryMonoStart,
              inventoryMonoStart <= inventoryMonoEnd, inventoryMonoEnd <= sckMonoStart, sckMonoStart <= sckMonoEnd,
              sckMonoEnd >= cuaMonoStart, sckMonoEnd - cuaMonoStart <= 5_000_000_000,
              cuaMonoEnd - cuaMonoStart <= 30_000_000_000,
              sckMonoEnd - sckMonoStart <= 30_000_000_000,
              cuaStarted <= cuaEnded, inventoryStarted <= inventoryEnded,
              inventoryStarted >= cuaEnded, inventoryEnded <= sckStarted,
              sckStarted <= sckEnded, windowScreenAssociationStatus == .provisional,
              sckEnded.timeIntervalSince(cuaStarted) <= 5,
              bundleID == "jp.naver.line.mac", pid > 0, processStartTimeSeconds > 0,
              (0..<1_000_000).contains(processStartTimeMicroseconds), windowID > 0, displayID > 0,
              widthPixels > 0, heightPixels > 0, nativeScale.isFinite, nativeScale > 0,
              pointPixelScale.isFinite, pointPixelScale > 0,
              cuaBoundsPoints.count == 4, sckWindowBoundsPoints.count == 4, displayBoundsPoints.count == 4,
              (cuaBoundsPoints + sckWindowBoundsPoints + displayBoundsPoints).allSatisfy(\.isFinite),
              cuaBoundsPoints[2] > 0, cuaBoundsPoints[3] > 0,
              sckWindowBoundsPoints[2] > 0, sckWindowBoundsPoints[3] > 0,
              displayBoundsPoints[2] > 0, displayBoundsPoints[3] > 0,
              captureRecord.captureKind == .displayRect,
              captureRecord.configuration == .fullDisplayPopup,
              captureRecord.imageWidthPx == widthPixels, captureRecord.imageHeightPx == heightPixels,
              captureRecord.validity == .valid, captureRecord.imageSHA256 == sckFrameID,
              captureRecord.scale == pointPixelScale,
              captureRecord.fullDisplayWitness?.includeMenuBar == true,
              captureRecord.fullDisplayWitness?.sourceRectAbsent == true,
              captureRecord.fullDisplayWitness?.displayID == displayID,
              captureRecord.fullDisplayWitness?.displayBoundsPoints == CGRect(x: displayBoundsPoints[0],
                y: displayBoundsPoints[1], width: displayBoundsPoints[2], height: displayBoundsPoints[3]),
              captureRecord.fullDisplayWitness?.contentRectPoints == captureRecord.fullDisplayWitness?.displayBoundsPoints,
              captureRecord.fullDisplayWitness?.imageWidthPx == widthPixels,
              captureRecord.fullDisplayWitness?.imageHeightPx == heightPixels,
              captureRecord.fullDisplayWitness?.pointPixelScale == pointPixelScale,
              captureRecord.fullDisplayWitness?.backingScaleFactor == nativeScale,
              captureRecord.expectedBBoxPt == CGRect(x: displayBoundsPoints[0], y: displayBoundsPoints[1],
                width: displayBoundsPoints[2], height: displayBoundsPoints[3]),
              captureRecord.actualBBoxPt == captureRecord.expectedBBoxPt,
              captureRecord.fullDisplayCaptureTiming?.requestStartedAtISO8601 == sckRequestStartedAt,
              captureRecord.fullDisplayCaptureTiming?.requestFinishedAtISO8601 == sckRequestEndedAt,
              captureRecord.fullDisplayCaptureTiming?.requestStartMonotonicNanoseconds == sckMonoStart,
              captureRecord.fullDisplayCaptureTiming?.requestEndMonotonicNanoseconds == sckMonoEnd else {
            throw VisualDiagnosticContractError.invalidCapturePair
        }
        try cuaFrame.validated()
        try sckFrame.validated()
    }

    private static func isHash(_ value: String) -> Bool {
        value.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil
    }

    private static func date(_ value: String) throws -> Date {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: value) else { throw VisualDiagnosticContractError.invalidTimestamp }
        return date
    }
}

public enum VisualDiagnosticAnalysisStatus: String, Codable, Sendable {
    case complete = "COMPLETE"
    case insufficient = "INSUFFICIENT"
    case notRun = "NOT_RUN"
}

public struct VisualDiagnosticCompletion: Codable, Equatable, Sendable {
    public let kind: String
    public let evidenceOnly: Bool
    public let actionable: Bool
    public let captureStatus: String
    public let analysisStatus: VisualDiagnosticAnalysisStatus
    public let actionEligibility: String
    public let pair: VisualDiagnosticCapturePair
    public let completedAt: String
    public let analysisEvidence: VisualDiagnosticArtifactReference?

    public init(pair: VisualDiagnosticCapturePair, analysisStatus: VisualDiagnosticAnalysisStatus,
                completedAt: String, analysisEvidence: VisualDiagnosticArtifactReference?) {
        self.kind = "VISUAL_CARD_DIAGNOSTIC"
        self.evidenceOnly = true
        self.actionable = false
        self.captureStatus = "CAPTURED"
        self.analysisStatus = analysisStatus
        self.actionEligibility = "INELIGIBLE"
        self.pair = pair
        self.completedAt = completedAt
        self.analysisEvidence = analysisEvidence
    }

    public func validated() throws {
        guard kind == "VISUAL_CARD_DIAGNOSTIC", evidenceOnly, !actionable,
              captureStatus == "CAPTURED", actionEligibility == "INELIGIBLE",
              !completedAt.isEmpty else { throw VisualDiagnosticContractError.actionEligibilityViolation }
        try pair.validated()
        try analysisEvidence?.validated()
    }
}

public enum VisualDiagnosticContractError: Error, Equatable {
    case invalidReference
    case invalidTimestamp
    case invalidCapturePair
    case actionEligibilityViolation
}
