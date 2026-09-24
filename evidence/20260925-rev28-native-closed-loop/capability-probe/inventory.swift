import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit

_ = NSApplication.shared
let sem = DispatchSemaphore(value: 0)
Task { @MainActor in
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        print("=== SCShareableContent windows=\(content.windows.count) apps=\(content.applications.count) ===")
        for w in content.windows {
            print("SC win id=\(w.windowID) layer=\(w.windowLayer) onScreen=\(w.isOnScreen) active=\(w.isActive) app=\(w.owningApplication?.bundleIdentifier ?? "-") pid=\(w.owningApplication?.processID ?? -1) frame=\(w.frame) title=\(String((w.title ?? "").prefix(40)))")
        }
    } catch { print("SC ERROR \(error)") }
    sem.signal()
}
while sem.wait(timeout: .now() + 0.05) == .timedOut { RunLoop.main.run(until: Date().addingTimeInterval(0.05)) }

print("=== CGWindowListCopyWindowInfo ===")
if let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] {
    for e in list {
        let num = e[kCGWindowNumber as String] as? Int ?? -1
        let layer = e[kCGWindowLayer as String] as? Int ?? -999
        let owner = e[kCGWindowOwnerName as String] as? String ?? "-"
        let bounds = e[kCGWindowBounds as String] as? [String: Any] ?? [:]
        print("CG win id=\(num) layer=\(layer) owner=\(owner) bounds=\(bounds)")
    }
}
print("=== NSScreen ===")
for s in NSScreen.screens {
    print("screen frame=\(s.frame) backingScaleFactor=\(s.backingScaleFactor) deviceDescription=\(s.deviceDescription)")
}
