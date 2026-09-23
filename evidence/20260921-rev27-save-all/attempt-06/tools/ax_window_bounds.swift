// ax_window_bounds.swift — read-only AX window-bounds observation (attempt-10).
//
// Purpose: report the accessibility (AX) window list of one running application
// (position/size in screen points, title/role/subrole/minimized/main/focused)
// plus the display geometry needed to document the capture scale, WITHOUT
// sending any input event: no click, no key, no scroll, no AX write, no
// bring-to-front, no app launch. Every used API is a read-only query
// (AXUIElementCopyAttributeValue / CGDisplay* / NSScreen / NSWorkspace read).
//
// Usage: ax_window_bounds <bundle-id>
// Output: one deterministic JSON object on stdout (sorted keys).

import Foundation
import ApplicationServices
import AppKit

func axCopy(_ element: AXUIElement, _ attribute: String) -> CFTypeRef? {
    var value: CFTypeRef? = nil
    let error = AXUIElementCopyAttributeValue(element, attribute as CFString, &value)
    return error == .success ? value : nil
}

func number(_ v: Double) -> Any {
    if v.rounded() == v && abs(v) < 1e15 { return Int(v) }
    return v
}

func pointValue(_ raw: CFTypeRef?) -> [Any]? {
    guard let raw = raw, CFGetTypeID(raw) == AXValueGetTypeID() else { return nil }
    var point = CGPoint.zero
    guard AXValueGetValue(raw as! AXValue, .cgPoint, &point) else { return nil }
    return [number(Double(point.x)), number(Double(point.y))]
}

func sizeValue(_ raw: CFTypeRef?) -> [Any]? {
    guard let raw = raw, CFGetTypeID(raw) == AXValueGetTypeID() else { return nil }
    var size = CGSize.zero
    guard AXValueGetValue(raw as! AXValue, .cgSize, &size) else { return nil }
    return [number(Double(size.width)), number(Double(size.height))]
}

func boolValue(_ raw: CFTypeRef?) -> Bool? {
    guard let raw = raw, CFGetTypeID(raw) == CFBooleanGetTypeID() else { return nil }
    return CFBooleanGetValue((raw as! CFBoolean))
}

func stringValue(_ raw: CFTypeRef?) -> String? {
    guard let raw = raw, CFGetTypeID(raw) == CFStringGetTypeID() else { return nil }
    return (raw as! String)
}

let bundleId = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "jp.naver.line.mac"
let formatter = ISO8601DateFormatter()
formatter.formatOptions = [.withInternetDateTime]
formatter.timeZone = TimeZone.current

var output: [String: Any] = [:]
output["tool"] = "ax_window_bounds_readonly"
output["version"] = 2
output["bundle_id"] = bundleId
output["timestamp_local"] = formatter.string(from: Date())
output["ax_api_trusted"] = AXIsProcessTrusted()

let mainDisplay = CGMainDisplayID()
let pixelW = CGDisplayPixelsWide(mainDisplay)
let pixelH = CGDisplayPixelsHigh(mainDisplay)
let bounds = CGDisplayBounds(mainDisplay)
var displayModePixel: Any = NSNull()
if let mode = CGDisplayCopyDisplayMode(mainDisplay) {
    displayModePixel = [mode.pixelWidth, mode.pixelHeight]
}
let screenFrame: Any
let backingScale: Any
if let screen = NSScreen.main {
    screenFrame = [number(Double(screen.frame.origin.x)), number(Double(screen.frame.origin.y)),
                   number(Double(screen.frame.size.width)), number(Double(screen.frame.size.height))]
    backingScale = Double(screen.backingScaleFactor)
} else {
    screenFrame = NSNull()
    backingScale = NSNull()
}
output["display"] = [
    "main_display_id": Int(mainDisplay),
    "cg_display_pixels_wh": [pixelW, pixelH],
    "cg_display_mode_pixel_wh": displayModePixel,
    "display_bounds_points": [number(Double(bounds.origin.x)), number(Double(bounds.origin.y)),
                              number(Double(bounds.size.width)), number(Double(bounds.size.height))],
    "nsscreen_frame_points": screenFrame,
    "nsscreen_backing_scale_factor": backingScale,
    "capture_scale_note": "screencapture -x writes device pixels: frame_px = point_rect * backing_scale_factor"
]
output["frontmost_application"] = NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? NSNull()

let instances = NSRunningApplication.runningApplications(withBundleIdentifier: bundleId)
output["running"] = !instances.isEmpty
var windows: [[String: Any]] = []
if let instance = instances.first {
    output["pid"] = Int(instance.processIdentifier)
    let appElement = AXUIElementCreateApplication(instance.processIdentifier)
    output["ax_frontmost"] = boolValue(axCopy(appElement, kAXFrontmostAttribute)) ?? NSNull()
    let focusedWindowRef = axCopy(appElement, kAXFocusedWindowAttribute)
    if let rawWindows = axCopy(appElement, kAXWindowsAttribute) {
        let list = rawWindows as? [AXUIElement] ?? []
        for (index, window) in list.enumerated() {
            var record: [String: Any] = ["index": index]
            record["role"] = stringValue(axCopy(window, kAXRoleAttribute)) ?? NSNull()
            record["subrole"] = stringValue(axCopy(window, kAXSubroleAttribute)) ?? NSNull()
            record["title"] = stringValue(axCopy(window, kAXTitleAttribute)) ?? NSNull()
            record["position_points"] = pointValue(axCopy(window, kAXPositionAttribute)) ?? NSNull()
            record["size_points"] = sizeValue(axCopy(window, kAXSizeAttribute)) ?? NSNull()
            record["minimized"] = boolValue(axCopy(window, kAXMinimizedAttribute)) ?? NSNull()
            record["main"] = boolValue(axCopy(window, kAXMainAttribute)) ?? NSNull()
            record["focused"] = boolValue(axCopy(window, kAXFocusedAttribute)) ?? NSNull()
            if let focusedWindowRef = focusedWindowRef {
                record["is_ax_focused_window"] = CFEqual(window, (focusedWindowRef as! AXUIElement))
            }
            windows.append(record)
        }
    }
}
output["window_count"] = windows.count
output["windows"] = windows

let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys, .prettyPrinted])
FileHandle.standardOutput.write(data)
FileHandle.standardOutput.write("\n".data(using: .utf8)!)
