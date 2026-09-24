import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit

_ = NSApplication.shared
let sem = DispatchSemaphore(value: 0)
Task { @MainActor in
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let win = content.windows.first(where: { $0.windowID == 70 }) else { print("NO WIN 70"); sem.signal(); return }
        let filter = SCContentFilter(desktopIndependentWindow: win)
        print("frame=\(win.frame) contentRect=\(filter.contentRect) scale=\(filter.pointPixelScale)")

        // A: SCScreenshotConfiguration with includeChildWindows = false
        let cfgA = SCScreenshotConfiguration()
        cfgA.includeChildWindows = false
        cfgA.showsCursor = false
        let outA = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: cfgA)
        print("A includeChildWindows=false px=\(outA.sdrImage.map { "\($0.width)x\($0.height)" } ?? "nil")")

        // B: SCScreenshotConfiguration with includeChildWindows = true
        let cfgB = SCScreenshotConfiguration()
        cfgB.includeChildWindows = true
        cfgB.showsCursor = false
        let outB = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: cfgB)
        print("B includeChildWindows=true px=\(outB.sdrImage.map { "\($0.width)x\($0.height)" } ?? "nil")")

        // C: legacy SCStreamConfiguration captureImage path
        let cfgC = SCStreamConfiguration()
        cfgC.showsCursor = false
        cfgC.ignoreShadowsSingleWindow = true
        cfgC.includeChildWindows = true
        let imgC = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: cfgC)
        print("C captureImage px=\(imgC.width)x\(imgC.height)")

        // D: SCStreamConfiguration with explicit pixel width/height, scaleFactor style
        let cfgD = SCStreamConfiguration()
        cfgD.showsCursor = false
        cfgD.ignoreShadowsSingleWindow = false
        let imgD = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: cfgD)
        print("D captureImage shadowsIncluded px=\(imgD.width)x\(imgD.height)")
    } catch { print("ERROR \(error)") }
    sem.signal()
}
while sem.wait(timeout: .now() + 0.05) == .timedOut { RunLoop.main.run(until: Date().addingTimeInterval(0.05)) }
