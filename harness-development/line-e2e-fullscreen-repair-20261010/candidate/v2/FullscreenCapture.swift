import AppKit
import CryptoKit
import Foundation
import CoreGraphics
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

private let taskRoot = URL(fileURLWithPath: "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-e2e-fullscreen-repair-20261010", isDirectory: true).standardizedFileURL

@main
struct FullscreenCapture {
    static func main() async {
        var parsed: Arguments?
        do {
            let args = try Arguments(CommandLine.arguments.dropFirst())
            parsed = args
            let result = try await capture(args)
            try writeJSON(result, to: args.manifest)
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys, .prettyPrinted])
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
        } catch {
            var failure: [String: Any] = [
                "verdict": "FAIL",
                "error": String(describing: error),
                "stage": "fullscreen_capture",
                "task_root": taskRoot.path
            ]
            if let parsed {
                failure["nonce"] = parsed.nonce
                failure["image_path"] = parsed.image.path
                failure["manifest_path"] = parsed.manifest.path
                failure["bundle_id"] = parsed.bundleID
                failure["allow_single_display_without_window"] = parsed.allowSingleDisplayWithoutWindow
                try? writeJSON(failure, to: parsed.manifest)
            }
            if let data = try? JSONSerialization.data(withJSONObject: failure, options: [.sortedKeys, .prettyPrinted]) {
                FileHandle.standardError.write(data)
                FileHandle.standardError.write(Data("\n".utf8))
            }
            exit(1)
        }
    }

    private static func capture(_ args: Arguments) async throws -> [String: Any] {
        let requestStart = ProcessInfo.processInfo.systemUptime
        let requestWall = iso8601(Date())
        let screenRecordingAllowedBeforeRequest = CGPreflightScreenCaptureAccess()
        let screenRecordingRequestResult: Bool? = screenRecordingAllowedBeforeRequest ? nil : CGRequestScreenCaptureAccess()
        let screenRecordingAllowedAfterRequest = CGPreflightScreenCaptureAccess()
        guard screenRecordingAllowedAfterRequest else {
            let requestDescription = screenRecordingRequestResult.map { String($0) } ?? "NOT_REQUESTED"
            throw CaptureError("screen recording permission is not granted; CGRequestScreenCaptureAccess returned \(requestDescription)")
        }
        let runningApps = NSRunningApplication.runningApplications(withBundleIdentifier: args.bundleID)
            .filter { !$0.isTerminated }
        guard let app = runningApps.sorted(by: { ($0.launchDate ?? .distantPast) > ($1.launchDate ?? .distantPast) }).first else {
            throw CaptureError("target application is not running")
        }

        let shareable = try await SCShareableContent.current
        let appWindows = shareable.windows.filter {
            $0.isOnScreen && $0.owningApplication?.bundleIdentifier == args.bundleID
        }
        let mainWindow = appWindows.max(by: { area($0.frame) < area($1.frame) })
        let display: SCDisplay
        let windowCoverage: Double?
        if let mainWindow {
            let matchingDisplays = shareable.displays.compactMap { display -> (SCDisplay, CGFloat)? in
                let intersection = display.frame.intersection(mainWindow.frame)
                guard !intersection.isNull else { return nil }
                let ratio = area(intersection) / max(area(mainWindow.frame), 1)
                return (display, ratio)
            }.sorted { $0.1 > $1.1 }
            guard let (match, coverage) = matchingDisplays.first, coverage >= 0.98 else {
                throw CaptureError("target window is not contained by one display; multi-display capture needs explicit per-display handling")
            }
            display = match
            windowCoverage = Double(coverage)
        } else {
            guard args.allowSingleDisplayWithoutWindow, shareable.displays.count == 1,
                  let onlyDisplay = shareable.displays.first else {
                throw CaptureError("ScreenCaptureKit returned no on-screen target application window; single-display fallback was not authorized or display inventory is ambiguous")
            }
            display = onlyDisplay
            windowCoverage = nil
        }

        let filter = SCContentFilter(display: display, excludingWindows: [])
        let configuration = SCScreenshotConfiguration()
        configuration.showsCursor = false
        configuration.includeChildWindows = true
        configuration.dynamicRange = .sdr
        configuration.displayIntent = .local
        configuration.contentType = UTType.png._bridgeToObjectiveC()
        let captureStart = ProcessInfo.processInfo.systemUptime
        let captureWallStart = iso8601(Date())
        let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: configuration)
        let captureEnd = ProcessInfo.processInfo.systemUptime
        let captureWallEnd = iso8601(Date())
        guard let image = output.sdrImage else {
            throw CaptureError("ScreenCaptureKit returned no SDR image")
        }
        guard image.width > 0, image.height > 0 else {
            throw CaptureError("captured image has invalid dimensions")
        }
        try ensureContained(args.image, under: taskRoot)
        try ensureAbsent(args.image)
        try FileManager.default.createDirectory(at: args.image.deletingLastPathComponent(), withIntermediateDirectories: true)
        guard let destination = CGImageDestinationCreateWithURL(args.image as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CaptureError("could not create PNG destination")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else {
            throw CaptureError("ImageIO could not finalize captured PNG")
        }
        let imageData = try Data(contentsOf: args.image, options: [.mappedIfSafe])
        guard imageData.starts(with: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]) else {
            throw CaptureError("capture output is not PNG data")
        }

        let scale = Double(filter.pointPixelScale)
        let displayRect = display.frame
        let result: [String: Any] = [
            "format_version": 1,
            "verdict": "CAPTURED",
            "provider": "ScreenCaptureKit.display",
            "nonce": args.nonce,
            "bundle_id": args.bundleID,
            "pid": app.processIdentifier,
            "application_name": app.localizedName as Any? ?? NSNull(),
            "application_path": app.bundleURL?.path as Any? ?? NSNull(),
            "application_launch_date": app.launchDate.map(iso8601) as Any? ?? NSNull(),
            "process_instance_binding": "bundle_id+pid+launch_date",
            "sck_window_inventory": shareable.windows.filter { $0.owningApplication?.bundleIdentifier == args.bundleID }.map { windowRecord($0) },
            "target_application_on_screen_window_count": appWindows.count,
            "selected_window_id": mainWindow.map { Int($0.windowID) } as Any? ?? NSNull(),
            "selected_window_frame_points": mainWindow.map { rect($0.frame) } as Any? ?? NSNull(),
            "window_binding_status": mainWindow == nil ? "NO_SCK_TARGET_WINDOW_SINGLE_DISPLAY_FALLBACK" : "SCK_TARGET_WINDOW_BOUND",
            "window_fallback_cua_observation_id": mainWindow == nil ? args.surfaceObservationID as Any : NSNull(),
            "display_id": Int(display.displayID),
            "display_frame_points": rect(displayRect),
            "display_size_points": ["width": display.width, "height": display.height],
            "display_window_coverage_ratio": windowCoverage as Any? ?? NSNull(),
            "filter_style": String(describing: filter.style),
            "filter_point_pixel_scale": scale,
            "filter_content_rect_points": rect(filter.contentRect),
            "filter_included_display_ids": filter.includedDisplays.map { Int($0.displayID) },
            "configuration": [
                "api": "SCScreenshotConfiguration",
                "display_intent": "local",
                "dynamic_range": "SDR",
                "content_type": "public.png",
                "shows_cursor": false,
                "include_child_windows": true,
                "source_rect": "unset; complete display filter",
                "destination_rect": "unset; full output surface",
                "requested_width_pixels": NSNull(),
                "requested_height_pixels": NSNull()
            ],
            "request_start_wall_utc": requestWall,
            "request_start_monotonic_seconds": requestStart,
            "capture_start_wall_utc": captureWallStart,
            "capture_start_monotonic_seconds": captureStart,
            "capture_end_wall_utc": captureWallEnd,
            "capture_end_monotonic_seconds": captureEnd,
            "capture_latency_ms": (captureEnd - captureStart) * 1000,
            "image_path": args.image.path,
            "image_width_pixels": image.width,
            "image_height_pixels": image.height,
            "image_bytes": imageData.count,
            "image_sha256": SHA256.hash(data: imageData).map { String(format: "%02x", $0) }.joined(),
            "derived_pixels_per_point": [
                "x": Double(image.width) / Double(display.width),
                "y": Double(image.height) / Double(display.height),
                "reported_filter_scale": scale
            ],
            "capture_did_not_activate_or_input": true,
            "screen_recording_preflight_before_request": screenRecordingAllowedBeforeRequest,
            "screen_recording_request_result": screenRecordingRequestResult as Any? ?? NSNull(),
            "screen_recording_preflight_after_request": screenRecordingAllowedAfterRequest
        ]
        return result
    }

    private static func windowRecord(_ window: SCWindow) -> [String: Any] {
        [
            "window_id": Int(window.windowID),
            "title": window.title as Any? ?? NSNull(),
            "frame_points": rect(window.frame),
            "on_screen": window.isOnScreen,
            "owning_bundle_id": window.owningApplication?.bundleIdentifier as Any? ?? NSNull(),
            "owning_pid": window.owningApplication?.processID as Any? ?? NSNull()
        ]
    }

    private static func rect(_ value: CGRect) -> [String: Double] {
        ["x": Double(value.origin.x), "y": Double(value.origin.y),
         "width": Double(value.width), "height": Double(value.height)]
    }

    private static func area(_ value: CGRect) -> CGFloat {
        guard !value.isNull, !value.isEmpty else { return 0 }
        return value.width * value.height
    }

    private static func iso8601(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: date)
    }

    private static func ensureContained(_ url: URL, under base: URL) throws {
        let path = url.standardizedFileURL.path
        let basePath = base.standardizedFileURL.path
        guard path.hasPrefix(basePath + "/"), !url.pathComponents.contains("..") else {
            throw CaptureError("output path is outside the task package")
        }
        var current = URL(fileURLWithPath: "/", isDirectory: true)
        for component in url.standardizedFileURL.pathComponents.dropFirst().dropLast() {
            current.appendPathComponent(component, isDirectory: true)
            if FileManager.default.fileExists(atPath: current.path) {
                let values = try current.resourceValues(forKeys: [.isSymbolicLinkKey])
                guard values.isSymbolicLink != true else { throw CaptureError("output path contains a symlink") }
            }
        }
    }

    private static func ensureAbsent(_ url: URL) throws {
        guard !FileManager.default.fileExists(atPath: url.path) else {
            throw CaptureError("refusing to overwrite an existing capture artifact")
        }
    }

    private static func writeJSON(_ value: [String: Any], to url: URL) throws {
        try ensureContained(url, under: taskRoot)
        try ensureAbsent(url)
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted])
        try data.write(to: url, options: [.withoutOverwriting])
    }
}

private struct Arguments {
    let image: URL
    let manifest: URL
    let nonce: String
    let bundleID: String
    let allowSingleDisplayWithoutWindow: Bool
    let surfaceObservationID: String

    init<S: Sequence>(_ raw: S) throws where S.Element == String {
        var values = Array(raw).makeIterator()
        var parsed: [String: String] = [:]
        var allowSingleDisplayWithoutWindow = false
        while let key = values.next() {
            if key == "--allow-single-display-no-window" {
                allowSingleDisplayWithoutWindow = true
                continue
            }
            guard key.hasPrefix("--"), let value = values.next() else { throw CaptureError("arguments must be --key value pairs") }
            parsed[String(key.dropFirst(2))] = value
        }
        guard let image = parsed["image"], let manifest = parsed["manifest"] else {
            throw CaptureError("required arguments: --image PATH --manifest PATH")
        }
        self.image = URL(fileURLWithPath: image).standardizedFileURL
        self.manifest = URL(fileURLWithPath: manifest).standardizedFileURL
        self.nonce = parsed["nonce"] ?? UUID().uuidString
        self.bundleID = parsed["bundle-id"] ?? "jp.naver.line.mac"
        self.allowSingleDisplayWithoutWindow = allowSingleDisplayWithoutWindow
        self.surfaceObservationID = parsed["surface-observation-id"] ?? "UNKNOWN"
    }
}

private struct CaptureError: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}
