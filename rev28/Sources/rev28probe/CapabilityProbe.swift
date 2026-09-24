import AppKit
import ApplicationServices
import CoreGraphics
import CoreText
import Foundation
import Rev28Core
import ScreenCaptureKit

// MARK: - Structured probe record

struct TrustResults: Codable {
    let axIsProcessTrusted: Bool
    let cgPreflightScreenCaptureAccess: Bool
    let cgPreflightPostEventAccess: Bool
}

struct QuartzResults: Codable {
    let mouseEventConstructionOK: Bool
    let keyboardEventConstructionOK: Bool
    let onScreenWindowInfoCount: Int
    let windowInfoError: String?
}

struct ScreenCaptureKitResults: Codable {
    let status: String
    let windowCount: Int?
    let displayCount: Int?
    let applicationCount: Int?
    let error: String?
}

struct VisionResults: Codable {
    let status: String
    let expectedExactStringsFound: Bool
    let expectedRelaxedSubstringFound: Bool
    let recognizedStrings: [String]
    let error: String?
}

struct ProbeRecord: Codable {
    let schemaVersion: String
    let probeID: String
    let taskID: String
    let startedAtISO8601: String
    let finishedAtISO8601: String
    let hostOSVersion: String
    let hostOSBuild: String
    let processExecutablePath: String
    let pid: Int32
    let parentPID: Int32
    let argv: [String]
    let sdkPathFromEnvironment: String?
    let swiftVersionFromEnvironment: String?
    let trust: TrustResults
    let quartz: QuartzResults
    let screenCaptureKit: ScreenCaptureKitResults
    let vision: VisionResults
    let overallStatus: String
    let notes: [String]
}

// MARK: - Async-on-main helper (SCScreenshotManager requires NSApplication.shared
// plus a run loop in this process context; pump the main run loop while waiting).

final class Box<T>: @unchecked Sendable {
    var value: T?
}

func awaitMain<T>(_ work: @escaping @MainActor () async -> T) -> T {
    let box = Box<T>()
    let semaphore = DispatchSemaphore(value: 0)
    Task { @MainActor in
        box.value = await work()
        semaphore.signal()
    }
    while semaphore.wait(timeout: .now() + 0.05) == .timedOut {
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))
    }
    return box.value!
}

// MARK: - Probe CLI

enum CapabilityProbeCLI {
    static let taskID = "T20260925-0647-01-rev28-native-closed-loop"

    static func run(arguments: [String]) -> Int32 {
        let outputDirectory: URL
        if arguments.count > 1 {
            outputDirectory = URL(fileURLWithPath: arguments[1], isDirectory: true)
        } else {
            outputDirectory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath, isDirectory: true)
        }

        do {
            let record = try performProbe()
            let path = try write(record: record, into: outputDirectory)
            print("probe record written: \(path.path)")
            print("overallStatus=\(record.overallStatus)")
            print("trust ax=\(record.trust.axIsProcessTrusted) screenCapture=\(record.trust.cgPreflightScreenCaptureAccess) postEvent=\(record.trust.cgPreflightPostEventAccess)")
            print("sck status=\(record.screenCaptureKit.status) windows=\(record.screenCaptureKit.windowCount.map(String.init) ?? "nil") displays=\(record.screenCaptureKit.displayCount.map(String.init) ?? "nil")")
            print("vision status=\(record.vision.status) exactMatch=\(record.vision.expectedExactStringsFound) strings=\(record.vision.recognizedStrings)")
            return record.overallStatus == "PASS" ? 0 : 1
        } catch {
            FileHandle.standardError.write(Data("rev28probe FAILED: \(error)\n".utf8))
            return 2
        }
    }

    static func performProbe() throws -> ProbeRecord {
        let startedAt = Date()
        let environment = ProcessInfo.processInfo.environment

        // GUI context: required by SCScreenshotManager in a tool process.
        _ = NSApplication.shared

        let trust = TrustResults(
            axIsProcessTrusted: AXIsProcessTrusted(),
            cgPreflightScreenCaptureAccess: CGPreflightScreenCaptureAccess(),
            cgPreflightPostEventAccess: CGPreflightPostEventAccess()
        )

        var quartzNotes: [String] = []
        let mouseEvent = CGEvent(
            mouseEventSource: nil,
            mouseType: .mouseMoved,
            mouseCursorPosition: CGPoint(x: 0, y: 0),
            mouseButton: .left
        )
        let keyboardEvent = CGEvent(keyboardEventSource: nil, virtualKey: 0x35, keyDown: true)
        var windowInfoError: String?
        var windowInfoCount = 0
        if let windowInfo = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as? [[String: Any]] {
            windowInfoCount = windowInfo.count
        } else {
            windowInfoError = "CGWindowListCopyWindowInfo returned nil"
        }
        if mouseEvent == nil { quartzNotes.append("CGEvent mouse event construction returned nil") }
        if keyboardEvent == nil { quartzNotes.append("CGEvent keyboard event construction returned nil") }

        let quartz = QuartzResults(
            mouseEventConstructionOK: mouseEvent != nil,
            keyboardEventConstructionOK: keyboardEvent != nil,
            onScreenWindowInfoCount: windowInfoCount,
            windowInfoError: windowInfoError
        )

        let sck = awaitMain { await probeScreenCaptureKit() }
        let vision = awaitMain { await probeVision() }

        let finishedAt = Date()
        let hostVersion = ProcessInfo.processInfo.operatingSystemVersion
        let hostOSVersion = "\(hostVersion.majorVersion).\(hostVersion.minorVersion).\(hostVersion.patchVersion)"
        let build = sysctlString("kern.osversion") ?? "unknown"
        let probeID = "rev28probe-\(Int(startedAt.timeIntervalSince1970))-\(ProcessInfo.processInfo.processIdentifier)"

        var notes: [String] = [
            "TCC/trust results are evaluated by macOS for this launched binary's responsible-process context (the parent process that launched it).",
            "No mouse/keyboard events were posted; CGEvent construction was an object-creation smoke check only.",
        ]
        notes.append(contentsOf: quartzNotes)

        let overallPass = trust.axIsProcessTrusted
            && trust.cgPreflightScreenCaptureAccess
            && trust.cgPreflightPostEventAccess
            && quartz.mouseEventConstructionOK
            && sck.status == "OK"
            && vision.expectedExactStringsFound

        return ProbeRecord(
            schemaVersion: "rev28.capability-probe.v1",
            probeID: probeID,
            taskID: taskID,
            startedAtISO8601: FrameCaptureSupport.iso8601Now(startedAt),
            finishedAtISO8601: FrameCaptureSupport.iso8601Now(finishedAt),
            hostOSVersion: hostOSVersion,
            hostOSBuild: build,
            processExecutablePath: Bundle.main.executablePath ?? ProcessInfo.processInfo.arguments.first ?? "unknown",
            pid: ProcessInfo.processInfo.processIdentifier,
            parentPID: getppid(),
            argv: ProcessInfo.processInfo.arguments,
            sdkPathFromEnvironment: environment["REV28_SDK_PATH"],
            swiftVersionFromEnvironment: environment["REV28_SWIFT_VERSION"],
            trust: trust,
            quartz: quartz,
            screenCaptureKit: sck,
            vision: vision,
            overallStatus: overallPass ? "PASS" : "FAIL",
            notes: notes
        )
    }

    @MainActor
    static func probeScreenCaptureKit() async -> ScreenCaptureKitResults {
        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            return ScreenCaptureKitResults(
                status: "OK",
                windowCount: content.windows.count,
                displayCount: content.displays.count,
                applicationCount: content.applications.count,
                error: nil
            )
        } catch {
            return ScreenCaptureKitResults(
                status: "ERROR",
                windowCount: nil,
                displayCount: nil,
                applicationCount: nil,
                error: String(describing: error)
            )
        }
    }

    @MainActor
    static func probeVision() async -> VisionResults {
        guard let image = renderProbeImage() else {
            return VisionResults(
                status: "ERROR",
                expectedExactStringsFound: false,
                expectedRelaxedSubstringFound: false,
                recognizedStrings: [],
                error: "probe image rendering failed"
            )
        }
        do {
            let engine = VisionOcrEngine()
            let items = try await engine.recognize(image: image)
            let strings = items.map(\.text)
            let exact = strings.contains(where: { OcrTextIdentity.isExactMatch($0, "57張照片") })
                || strings.contains(where: { OcrTextIdentity.isExactMatch($0, "儲存全部") })
            let relaxed = strings.contains(where: { $0.contains("57") })
                || strings.contains(where: { $0.contains("儲存") })
            return VisionResults(
                status: "OK",
                expectedExactStringsFound: exact,
                expectedRelaxedSubstringFound: relaxed,
                recognizedStrings: strings,
                error: nil
            )
        } catch {
            return VisionResults(
                status: "ERROR",
                expectedExactStringsFound: false,
                expectedRelaxedSubstringFound: false,
                recognizedStrings: [],
                error: String(describing: error)
            )
        }
    }

    /// Renders the probe's own synthetic image (no screen content): white canvas,
    /// two identity strings drawn with CoreText.
    static func renderProbeImage() -> CGImage? {
        let width = 640
        let height = 320
        guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(
                  data: nil,
                  width: width,
                  height: height,
                  bitsPerComponent: 8,
                  bytesPerRow: 0,
                  space: colorSpace,
                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
              ) else { return nil }

        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))

        let font = CTFontCreateWithName("PingFangTC-Medium" as CFString, 40, nil)
        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: NSColor.black,
        ]
        func draw(_ text: String, at point: CGPoint) {
            let attributed = NSAttributedString(string: text, attributes: attributes)
            let line = CTLineCreateWithAttributedString(attributed)
            context.textPosition = point
            CTLineDraw(line, context)
        }
        draw("儲存全部", at: CGPoint(x: 40, y: 200))
        draw("57張照片", at: CGPoint(x: 40, y: 100))

        return context.makeImage()
    }

    static func write(record: ProbeRecord, into directory: URL) throws -> URL {
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd'T'HHmmssZ"
        formatter.timeZone = TimeZone.current
        let stamp = formatter.string(from: Date())
        let finalURL = directory.appendingPathComponent("probe-record-\(stamp).json")
        guard !FileManager.default.fileExists(atPath: finalURL.path) else {
            throw ProbeWriteError.alreadyExists(finalURL.path)
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(record)

        let temporaryURL = directory.appendingPathComponent(".probe-record.tmp-\(UUID().uuidString)")
        try data.write(to: temporaryURL)
        try FileManager.default.moveItem(at: temporaryURL, to: finalURL)
        return finalURL
    }

    static func sysctlString(_ name: String) -> String? {
        var size = 0
        guard sysctlbyname(name, nil, &size, nil, 0) == 0, size > 0 else { return nil }
        var buffer = [CChar](repeating: 0, count: size)
        guard sysctlbyname(name, &buffer, &size, nil, 0) == 0 else { return nil }
        return String(cString: buffer)
    }
}

enum ProbeWriteError: Error, CustomStringConvertible {
    case alreadyExists(String)

    var description: String {
        switch self {
        case let .alreadyExists(path):
            return "evidence record already exists (append-only discipline): \(path)"
        }
    }
}
