import Foundation
import AppKit
import ScreenCaptureKit

final class App: NSObject, NSApplicationDelegate {
    var main: NSWindow!
    var child: NSWindow!
    func applicationDidFinishLaunching(_ n: Notification) {
        main = NSWindow(contentRect: NSRect(x: 240, y: 320, width: 400, height: 300),
                        styleMask: [.titled, .closable], backing: .buffered, defer: false)
        main.title = "Rev28 child-union probe"
        main.makeKeyAndOrderFront(nil)
        child = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 200, height: 150),
                         styleMask: [.borderless], backing: .buffered, defer: false)
        child.backgroundColor = .systemRed
        main.addChildWindow(child, ordered: .above)
        child.setFrameOrigin(NSPoint(x: main.frame.minX + 320, y: main.frame.maxY + 40))
        NSApp.activate(ignoringOtherApps: true)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { self.run() }
    }
    func run() {
        DispatchQueue.main.async {
            let screenH = NSScreen.screens[0].frame.height
            func topLeft(_ r: NSRect) -> CGRect { CGRect(x: r.minX, y: screenH - r.maxY, width: r.width, height: r.height) }
            let mainTL = topLeft(self.main.frame), childTL = topLeft(self.child.frame)
            print("mainID=\(self.main.windowNumber) mainAppKit=\(self.main.frame) mainTopLeft=\(mainTL)")
            print("childID=\(self.child.windowNumber) childAppKit=\(self.child.frame) childTopLeft=\(childTL)")
            let union = mainTL.union(childTL)
            print("expected union (pt) = \(union)")
            Task { @MainActor in
                do {
                    let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
                    for id in [self.main.windowNumber, self.child.windowNumber] {
                        if let w = content.windows.first(where: { $0.windowID == CGWindowID(id) }) {
                            print("SC win id=\(id) frame=\(w.frame) owner=\(w.owningApplication?.bundleIdentifier ?? "-")")
                        } else { print("SC win id=\(id) NOT FOUND") }
                    }
                    guard let mw = content.windows.first(where: { $0.windowID == CGWindowID(self.main.windowNumber) }) else { print("no main"); NSApp.terminate(nil); return }
                    let filter = SCContentFilter(desktopIndependentWindow: mw)
                    print("filter contentRect=\(filter.contentRect) scale=\(filter.pointPixelScale)")
                    for (flag, shadows) in [(false, false), (true, false), (false, true), (true, true)] {
                        let cfg = SCScreenshotConfiguration()
                        cfg.includeChildWindows = flag
                        cfg.showsCursor = false
                        cfg.ignoreShadows = shadows
                        do {
                            let out = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: cfg)
                            if let img = out.sdrImage {
                                print("includeChildWindows=\(flag) ignoreShadows=\(shadows) px=\(img.width)x\(img.height) pt=\(Double(img.width)/2.0)x\(Double(img.height)/2.0)")
                            }
                        } catch { print("includeChildWindows=\(flag) ignoreShadows=\(shadows) ERROR \(error)") }
                    }
                } catch { print("ERROR \(error)") }
                NSApp.terminate(nil)
            }
        }
    }
}
let app = NSApplication.shared
let delegate = App()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
