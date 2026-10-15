import AppKit
import Foundation
import ImageIO
import Rev28Core
import Darwin

struct VisualDiagnosticCaptureReceipt: Codable {
    let version: Int
    let kind: String
    let evidenceOnly: Bool
    let actionable: Bool
    let pair: VisualDiagnosticCapturePair
}

struct VisualDiagnosticClockReceipt: Codable {
    let witness: VisualDiagnosticClockWitness
}

struct VisualDiagnosticClockCheckReceipt: Codable {
    let status: String
    let elapsedNanoseconds: UInt64
}

struct VisualDiagnosticAnchor: Codable {
    let text: String
    let cuaX: Double
    let cuaY: Double
    let sckX: Double
    let sckY: Double
    let residualPixels: Double
}

struct VisualDiagnosticPixelAnalysis: Codable {
    let version: Int
    let kind: String
    let evidenceOnly: Bool
    let actionable: Bool
    let capturePairSHA256: String
    let status: String
    let reason: String?
    let scaleX: Double?
    let scaleY: Double?
    let offsetX: Double?
    let offsetY: Double?
    let uncertaintyPixels: Double?
    let maximumResidualPixels: Double?
    let anchors: [VisualDiagnosticAnchor]
    let cuaOCR: [OcrItem]
    let sckOCR: [OcrItem]
}

enum VisualDiagnosticCommand {
    static func clock(arguments: [String]) throws -> VisualDiagnosticClockReceipt {
        func value(_ name: String) throws -> String {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  !arguments[i + 1].isEmpty else { throw Failure.invalidArguments(name) }
            return arguments[i + 1]
        }
        let sessionID = try value("--session-id")
        let witnessID = try value("--witness-id")
        guard UUID(uuidString: witnessID) != nil else { throw Failure.invalidArguments("--witness-id") }
        return VisualDiagnosticClockReceipt(witness: try clockWitness(sessionID: sessionID, witnessID: witnessID))
    }

    static func checkClockBracket(arguments: [String]) throws -> VisualDiagnosticClockCheckReceipt {
        func value(_ name: String) throws -> String {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  !arguments[i + 1].isEmpty else { throw Failure.invalidArguments(name) }
            return arguments[i + 1]
        }
        let sessionID = try value("--session-id")
        let witnessID = try value("--witness-id")
        func witness(_ name: String) throws -> VisualDiagnosticClockWitness {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  let data = arguments[i + 1].data(using: .utf8) else { throw Failure.invalidArguments(name) }
            return try JSONDecoder().decode(VisualDiagnosticClockWitness.self, from: data)
        }
        let elapsed = try VisualDiagnosticClockWitness.validatedBracket(
            before: witness("--before-json"), after: witness("--after-json"),
            sessionID: sessionID, witnessID: witnessID)
        return VisualDiagnosticClockCheckReceipt(status: "PASS", elapsedNanoseconds: elapsed)
    }

    private static func clockWitness(sessionID: String, witnessID: String) throws -> VisualDiagnosticClockWitness {
        var timebase = mach_timebase_info_data_t()
        guard mach_timebase_info(&timebase) == KERN_SUCCESS,
              timebase.numer > 0, timebase.denom > 0 else { throw Failure.clockUnavailable }
        let ticks = mach_continuous_time()
        let (scaled, overflow) = ticks.multipliedReportingOverflow(by: UInt64(timebase.numer))
        guard !overflow else { throw Failure.clockUnavailable }
        let continuousNanoseconds = scaled / UInt64(timebase.denom)
        let bootSessionUUID = try bootUUID()
        return VisualDiagnosticClockWitness(sessionID: sessionID, witnessID: witnessID,
            bootSessionUUID: bootSessionUUID, timebaseNumerator: timebase.numer,
            timebaseDenominator: timebase.denom, continuousNanoseconds: String(continuousNanoseconds),
            sampledAtUTC: timestamp(Date()))
    }

    private static func bootUUID() throws -> String {
        var size = 0
        guard sysctlbyname("kern.bootsessionuuid", nil, &size, nil, 0) == 0, size > 1 else {
            throw Failure.clockUnavailable
        }
        var bytes = [CChar](repeating: 0, count: size)
        let result = bytes.withUnsafeMutableBytes { raw in
            sysctlbyname("kern.bootsessionuuid", raw.baseAddress, &size, nil, 0)
        }
        guard result == 0 else { throw Failure.clockUnavailable }
        let value = String(cString: bytes)
        guard UUID(uuidString: value) != nil else { throw Failure.clockUnavailable }
        return value.lowercased()
    }

    static func run(arguments: [String]) async throws -> VisualDiagnosticCaptureReceipt {
        func value(_ name: String) throws -> String {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  !arguments[i + 1].isEmpty else { throw Failure.invalidArguments(name) }
            return arguments[i + 1]
        }
        func integer(_ name: String) throws -> Int {
            guard let result = Int(try value(name)), result > 0 else { throw Failure.invalidArguments(name) }
            return result
        }
        func nonnegativeInteger(_ name: String) throws -> Int {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  let result = Int(arguments[i + 1]), result >= 0 else { throw Failure.invalidArguments(name) }
            return result
        }
        func uint64(_ name: String) throws -> UInt64 {
            guard let result = UInt64(try value(name)) else { throw Failure.invalidArguments(name) }
            return result
        }
        func rect(_ name: String) throws -> [Double] {
            let parts = try value(name).split(separator: ",").compactMap { Double($0) }
            guard parts.count == 4, parts.allSatisfy(\.isFinite), parts[2] > 0, parts[3] > 0 else {
                throw Failure.invalidArguments(name)
            }
            return parts
        }
        let root = URL(fileURLWithPath: try value("--project-root")).standardizedFileURL.resolvingSymlinksInPath()
        let grant = try value("--grant")
        let grantSHA = try value("--grant-sha256")
        let sessionID = try value("--session-id")
        let clockWitnessID = try value("--clock-witness-id")
        guard UUID(uuidString: clockWitnessID) != nil,
              let witnessIndex = arguments.firstIndex(of: "--continuous-clock-before-cua-json"),
              witnessIndex + 1 < arguments.count,
              let witnessData = arguments[witnessIndex + 1].data(using: .utf8),
              let clockBeforeCUA = try? JSONDecoder().decode(VisualDiagnosticClockWitness.self, from: witnessData) else {
            throw Failure.invalidArguments("continuous clock witness")
        }
        try clockBeforeCUA.validated(sessionID: sessionID, witnessID: clockWitnessID)
        let outputPath = try value("--output")
        let cuaPath = try value("--cua-frame")
        let cuaFrameID = try value("--cua-frame-id")
        let cuaStartedAt = try value("--cua-request-started-at")
        let cuaEndedAt = try value("--cua-request-ended-at")
        let cuaStartMono = try uint64("--cua-request-start-monotonic-ns")
        let cuaEndMono = try uint64("--cua-request-end-monotonic-ns")
        let pid = Int32(try integer("--pid"))
        let processStart = try integer("--process-start-seconds")
        let processStartMicros = Int32(try nonnegativeInteger("--process-start-microseconds"))
        let windowID = UInt32(try integer("--window-id"))
        let displayID = UInt32(try integer("--display-id"))
        let cuaBounds = try rect("--cua-bounds")
        guard cuaFrameID.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil,
              root.path == FileManager.default.currentDirectoryPath,
              let cuaStarted = date(cuaStartedAt), let cuaEnded = date(cuaEndedAt),
              cuaStartMono <= cuaEndMono, processStartMicros < 1_000_000 else {
            throw Failure.invalidArguments("capture binding")
        }
        _ = try PilotNativeAuthority.verify(root: root, grantPath: grant, grantSHA: grantSHA,
            surface: "ALBUMS", sessionID: sessionID)
        guard NSRunningApplication(processIdentifier: pid)?.bundleIdentifier == "jp.naver.line.mac",
              let process = ProcessInstanceID.current(pid: pid),
              process.startTimeSeconds == processStart, process.startTimeMicroseconds == processStartMicros else {
            throw Failure.identityChanged
        }
        let cuaFrameRef = try artifact(path: cuaPath, root: root, expectedSHA: cuaFrameID)
        guard cuaEnded >= cuaStarted, Date() >= cuaStarted,
              Date().timeIntervalSince(cuaStarted) < 5 else { throw Failure.capturePairExpired }

        let inventoryStarted = Date()
        let inventoryStartMono = DispatchTime.now().uptimeNanoseconds
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        let windows = WindowSensor.snapshots(from: content).filter {
            $0.windowID == windowID && $0.ownerPID == pid && $0.ownerBundleID == "jp.naver.line.mac" && $0.isOnScreen
        }
        let displays = content.displays.filter { $0.displayID == displayID }
        let inventoryEndMono = DispatchTime.now().uptimeNanoseconds
        let inventoryEnded = Date()
        guard windows.count == 1, let window = windows.first, displays.count == 1,
              let display = displays.first else { throw Failure.identityChanged }
        let bounds = [Double(window.frame.minX), Double(window.frame.minY),
                      Double(window.frame.width), Double(window.frame.height)]
        guard zip(bounds, cuaBounds).allSatisfy({ abs($0.0 - $0.1) <= 1 }),
              display.frame.contains(window.frame),
              let screen = NSScreen.screens.first(where: {
                  ($0.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value == displayID
              }), screen.backingScaleFactor.isFinite, screen.backingScaleFactor > 0 else {
            throw Failure.geometryChanged
        }
        // Recheck the original CUA start after inventory and immediately before
        // dispatching SCK. The bound is never restarted after slow work.
        let service = await FrameCaptureService(ruleBook: nil)
        let clockBeforeSCK = try clockWitness(sessionID: sessionID, witnessID: clockWitnessID)
        _ = try VisualDiagnosticClockWitness.validatedBracket(before: clockBeforeCUA,
            after: clockBeforeSCK, sessionID: sessionID, witnessID: clockWitnessID)
        guard Date() >= cuaStarted, Date().timeIntervalSince(cuaStarted) < 5,
              clockBeforeSCK.bootSessionUUID == clockBeforeCUA.bootSessionUUID,
              clockBeforeSCK.timebaseNumerator == clockBeforeCUA.timebaseNumerator,
              clockBeforeSCK.timebaseDenominator == clockBeforeCUA.timebaseDenominator else {
            throw Failure.capturePairExpired
        }
        let captured = try await service.captureFullDisplayRetained(display: display, configuration: .fullDisplayPopup)
        // This independent mach_continuous_time sample is taken only after the
        // existing retained SCK service has returned.
        let clockAfterSCK = try clockWitness(sessionID: sessionID, witnessID: clockWitnessID)
        guard let timing = captured.record.fullDisplayCaptureTiming,
              timing.requestEndMonotonicNanoseconds >= timing.requestStartMonotonicNanoseconds,
              clockAfterSCK.bootSessionUUID == clockBeforeCUA.bootSessionUUID,
              clockAfterSCK.timebaseNumerator == clockBeforeCUA.timebaseNumerator,
              clockAfterSCK.timebaseDenominator == clockBeforeCUA.timebaseDenominator,
              (try? VisualDiagnosticClockWitness.validatedBracket(before: clockBeforeCUA,
                after: clockAfterSCK, sessionID: sessionID, witnessID: clockWitnessID)) != nil,
              let sckStarted = date(timing.requestStartedAtISO8601),
              let sckEnded = date(timing.requestFinishedAtISO8601),
              sckStarted >= inventoryEnded,
              sckEnded.timeIntervalSince(cuaStarted) <= 5,
              captured.record.fullDisplayWitness?.includeMenuBar == true,
              captured.record.fullDisplayWitness?.sourceRectAbsent == true,
              let png = FrameCaptureSupport.pngData(of: captured.image), png.count <= 16 * 1024 * 1024 else {
            throw Failure.capturePairExpired
        }
        guard ProcessInstanceID.current(pid: pid) == process,
              NSRunningApplication(processIdentifier: pid)?.bundleIdentifier == "jp.naver.line.mac" else {
            throw Failure.identityChanged
        }
        let sckID = EvidenceIO.sha256Hex(png)
        guard sckID != cuaFrameID else { throw Failure.ambiguousFrames }
        guard captured.record.imageSHA256 == sckID, captured.record.validity == .valid,
              captured.record.fullDisplayWitness?.displayID == displayID,
              captured.record.fullDisplayWitness?.displayBoundsPoints == display.frame,
              captured.record.fullDisplayWitness?.pointPixelScale == captured.record.scale,
              captured.record.fullDisplayWitness?.backingScaleFactor == Double(screen.backingScaleFactor),
              captured.record.expectedBBoxPt == display.frame else { throw Failure.geometryChanged }
        let output = try outputURL(outputPath, root: root)
        let frameURL = output.appendingPathComponent("sck-frame.png")
        try png.write(to: frameURL, options: .atomic)
        let persistedPNG = try Data(contentsOf: frameURL)
        guard EvidenceIO.sha256Hex(persistedPNG) == sckID,
              let source = CGImageSourceCreateWithData(persistedPNG as CFData, nil),
              let persistedImage = CGImageSourceCreateImageAtIndex(source, 0, nil),
              persistedImage.width == captured.image.width, persistedImage.height == captured.image.height else {
            throw Failure.geometryChanged
        }
        let frameRef = VisualDiagnosticArtifactReference(path: outputPath + "/sck-frame.png", bytes: png.count, sha256: sckID)
        let pair = VisualDiagnosticCapturePair(version: 2, sessionID: sessionID, cuaFrameID: cuaFrameID, cuaFrame: cuaFrameRef,
            cuaRequestStartedAt: cuaStartedAt, cuaRequestEndedAt: cuaEndedAt,
            cuaRequestStartMonotonicNanoseconds: String(cuaStartMono), cuaRequestEndMonotonicNanoseconds: String(cuaEndMono),
            sckFrameID: sckID, sckFrame: frameRef, sckRequestStartedAt: timing.requestStartedAtISO8601,
            sckRequestEndedAt: timing.requestFinishedAtISO8601,
            sckRequestStartMonotonicNanoseconds: String(timing.requestStartMonotonicNanoseconds),
            sckRequestEndMonotonicNanoseconds: String(timing.requestEndMonotonicNanoseconds),
            nativeInventoryStartedAt: Self.timestamp(inventoryStarted), nativeInventoryEndedAt: Self.timestamp(inventoryEnded),
            nativeInventoryStartMonotonicNanoseconds: String(inventoryStartMono),
            nativeInventoryEndMonotonicNanoseconds: String(inventoryEndMono),
            continuousClockBeforeCUA: clockBeforeCUA, continuousClockAfterSCK: clockAfterSCK,
            continuousClockWitnessID: clockWitnessID,
            windowScreenAssociationStatus: .provisional,
            bundleID: "jp.naver.line.mac", pid: pid, processStartTimeSeconds: processStart,
            processStartTimeMicroseconds: Int(processStartMicros), windowID: windowID, displayID: displayID,
            widthPixels: captured.image.width, heightPixels: captured.image.height,
            nativeScale: Double(screen.backingScaleFactor), pointPixelScale: captured.record.scale,
            cuaBoundsPoints: cuaBounds, sckWindowBoundsPoints: bounds,
            displayBoundsPoints: [Double(display.frame.minX), Double(display.frame.minY),
                Double(display.frame.width), Double(display.frame.height)], captureRecord: captured.record)
        try pair.validated()
        return VisualDiagnosticCaptureReceipt(version: 2, kind: "VISUAL_CARD_DIAGNOSTIC",
            evidenceOnly: true, actionable: false, pair: pair)
    }

    static func analyze(arguments: [String]) async throws -> VisualDiagnosticPixelAnalysis {
        func value(_ name: String) throws -> String {
            guard let i = arguments.firstIndex(of: name), i + 1 < arguments.count,
                  !arguments[i + 1].isEmpty else { throw Failure.invalidArguments(name) }
            return arguments[i + 1]
        }
        let root = URL(fileURLWithPath: try value("--project-root")).standardizedFileURL.resolvingSymlinksInPath()
        let receiptPath = try value("--capture-receipt")
        let receiptSHA = try value("--capture-receipt-sha256")
        guard root.path == FileManager.default.currentDirectoryPath else { throw Failure.invalidArguments("project root") }
        let (receiptRef, receiptData) = try artifactWithData(path: receiptPath, root: root, expectedSHA: receiptSHA)
        let receipt = try JSONDecoder().decode(VisualDiagnosticCaptureReceipt.self, from: receiptData)
        let pair = receipt.pair
        try pair.validated()
        guard receipt.version == 2, receipt.kind == "VISUAL_CARD_DIAGNOSTIC", receipt.evidenceOnly,
              !receipt.actionable, pair.cuaFrame.sha256 != pair.sckFrame.sha256 else {
            throw Failure.invalidArguments("typed capture receipt is invalid")
        }
        let pairSHA = receiptRef.sha256
        let (cuaRef, cuaBytes) = try artifactWithData(path: pair.cuaFrame.path, root: root,
            expectedSHA: pair.cuaFrame.sha256)
        let (sckRef, sckBytes) = try artifactWithData(path: pair.sckFrame.path, root: root,
            expectedSHA: pair.sckFrame.sha256)
        let cuaBounds = pair.cuaBoundsPoints
        let windowBounds = pair.sckWindowBoundsPoints
        let displayBounds = pair.displayBoundsPoints
        guard let cuaSource = CGImageSourceCreateWithData(cuaBytes as CFData, nil),
              let cuaImage = CGImageSourceCreateImageAtIndex(cuaSource, 0, nil),
              let sckSource = CGImageSourceCreateWithData(sckBytes as CFData, nil),
              let sckImage = CGImageSourceCreateImageAtIndex(sckSource, 0, nil) else {
            throw Failure.invalidArguments("retained source image is corrupt")
        }
        let engine = VisionOcrEngine()
        let cuaOCR = try await engine.recognize(image: cuaImage)
        let sckOCR = try await engine.recognize(image: sckImage)
        let native = NativeCaptureBounds(
            cuaCaptureBoundsPoints: CGRect(x: cuaBounds[0], y: cuaBounds[1], width: cuaBounds[2], height: cuaBounds[3]),
            sckWindowBoundsPoints: CGRect(x: windowBounds[0], y: windowBounds[1], width: windowBounds[2], height: windowBounds[3]),
            displayBoundsPoints: CGRect(x: displayBounds[0], y: displayBounds[1], width: displayBounds[2], height: displayBounds[3]),
            cuaSizePixels: CGSize(width: cuaImage.width, height: cuaImage.height),
            sckSizePixels: CGSize(width: sckImage.width, height: sckImage.height))
        do {
            let mapping = try AutomaticOcrAnchorMapper.derive(cua: cuaOCR, sck: sckOCR, native: native)
            let anchors = mapping.anchors.map { VisualDiagnosticAnchor(text: $0.text,
                cuaX: $0.cuaPoint.x, cuaY: $0.cuaPoint.y, sckX: $0.sckPoint.x, sckY: $0.sckPoint.y,
                residualPixels: $0.residualSourcePixels) }
            return VisualDiagnosticPixelAnalysis(version: 1, kind: "VISUAL_CARD_DIAGNOSTIC",
                evidenceOnly: true, actionable: false, capturePairSHA256: pairSHA, status: "COMPLETE",
                reason: nil, scaleX: mapping.scaleX, scaleY: mapping.scaleY, offsetX: mapping.offsetX,
                offsetY: mapping.offsetY, uncertaintyPixels: mapping.uncertaintyPixels,
                maximumResidualPixels: mapping.maximumResidualSourcePixels, anchors: anchors,
                cuaOCR: cuaOCR, sckOCR: sckOCR)
        } catch {
            return VisualDiagnosticPixelAnalysis(version: 1, kind: "VISUAL_CARD_DIAGNOSTIC",
                evidenceOnly: true, actionable: false, capturePairSHA256: pairSHA, status: "INSUFFICIENT",
                reason: String(describing: error), scaleX: nil, scaleY: nil, offsetX: nil, offsetY: nil,
                uncertaintyPixels: nil, maximumResidualPixels: nil, anchors: [], cuaOCR: cuaOCR, sckOCR: sckOCR)
        }
    }

    private enum Failure: Error { case invalidArguments(String), identityChanged, geometryChanged, capturePairExpired, ambiguousFrames, clockUnavailable }

    private static func date(_ value: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: value)
    }

    private static func timestamp(_ value: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: value)
    }

    private static func artifact(path: String, root: URL, expectedSHA: String) throws -> VisualDiagnosticArtifactReference {
        try artifactWithData(path: path, root: root, expectedSHA: expectedSHA).reference
    }

    private static func artifactWithData(path: String, root: URL, expectedSHA: String)
        throws -> (reference: VisualDiagnosticArtifactReference, data: Data) {
        guard path.hasPrefix("harness-development/"), !path.split(separator: "/").contains("..") else {
            throw Failure.invalidArguments("CUA artifact path")
        }
        let url = root.appendingPathComponent(path).standardizedFileURL
        guard url.path.hasPrefix(root.path + "/"), url.resolvingSymlinksInPath() == url else {
            throw Failure.invalidArguments("CUA artifact identity")
        }
        let data = try Data(contentsOf: url)
        guard data.count > 0, EvidenceIO.sha256Hex(data) == expectedSHA else { throw Failure.invalidArguments("CUA artifact hash") }
        return (VisualDiagnosticArtifactReference(path: path, bytes: data.count, sha256: expectedSHA), data)
    }

    private static func outputURL(_ path: String, root: URL) throws -> URL {
        guard path.hasPrefix(PilotNativeAuthority.directory + "/evidence/visual-diagnostic/"),
              !path.split(separator: "/").contains("..") else { throw Failure.invalidArguments("output scope") }
        let url = root.appendingPathComponent(path).standardizedFileURL
        var directory: ObjCBool = false
        guard url.path.hasPrefix(root.path + "/"), url.resolvingSymlinksInPath() == url,
              FileManager.default.fileExists(atPath: url.path, isDirectory: &directory), directory.boolValue,
              try FileManager.default.contentsOfDirectory(atPath: url.path).isEmpty else {
            throw Failure.invalidArguments("output directory must be a new empty directory")
        }
        return url
    }
}
