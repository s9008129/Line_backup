import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit

_ = NSApplication.shared
print("NSApp initialized")

let sem = DispatchSemaphore(value: 0)
Task { @MainActor in
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let win = content.windows.first(where: { $0.owningApplication?.bundleIdentifier == "com.apple.Terminal" && $0.frame.width > 500 }) else {
            print("NO_TERMINAL_WINDOW"); sem.signal(); return
        }
        print("target windowID=\(win.windowID) frame=\(win.frame)")
        let filter = SCContentFilter(desktopIndependentWindow: win)
        print("filter created")
        print("contentRect=\(filter.contentRect) pointPixelScale=\(filter.pointPixelScale)")
        let cfg = SCScreenshotConfiguration()
        cfg.includeChildWindows = true
        cfg.showsCursor = false
        let out = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: cfg)
        print("capture returned")
        if let img = out.sdrImage {
            print("captured sdrImage px=\(img.width)x\(img.height)")
        } else { print("sdrImage=nil") }
    } catch { print("ERROR \(error)") }
    sem.signal()
}
while sem.wait(timeout: .now() + 0.05) == .timedOut {
    RunLoop.main.run(until: Date().addingTimeInterval(0.05))
}
