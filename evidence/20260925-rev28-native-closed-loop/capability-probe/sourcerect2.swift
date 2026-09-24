import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit
import UniformTypeIdentifiers

final class MarkerView: NSView {
    override var isFlipped: Bool { true }
    override func draw(_ dirtyRect: NSRect) {
        NSColor.white.setFill(); bounds.fill()
        NSColor.magenta.setFill()
        // three 12x12 markers
        for p in [CGPoint(x: 40, y: 40), CGPoint(x: 360, y: 40), CGPoint(x: 40, y: 240)] {
            NSRect(x: p.x - 6, y: p.y - 6, width: 12, height: 12).fill()
        }
        NSColor.cyan.setFill()
        NSRect(x: 360 - 6, y: 240 - 6, width: 12, height: 12).fill()
    }
}

final class App: NSObject, NSApplicationDelegate {
    var win: NSWindow!
    func applicationDidFinishLaunching(_ n: Notification) {
        let w = NSWindow(contentRect: NSRect(x: 240, y: 320, width: 400, height: 332),
                         styleMask: [.titled, .closable], backing: .buffered, defer: false)
        win = w
        w.title = "Rev28 source-rect probe 2"
        let v = MarkerView(frame: w.contentView!.bounds)
        v.autoresizingMask = [.width, .height]
        w.contentView = v
        w.makeKeyAndOrderFront(nil)
        DispatchQueue.main.async { self.probe() }
    }
    func probe() {
        let screenH = NSScreen.screens[0].frame.height
        let frameTL = CGRect(x: win.frame.minX, y: screenH - win.frame.maxY, width: win.frame.width, height: win.frame.height)
        let R = frameTL
        print("window frameTL=\(frameTL) sourceRect=\(R)")
        Task { @MainActor in
            do {
                let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
                guard let mw = content.windows.first(where: { $0.windowID == CGWindowID(self.win.windowNumber) }) else { print("no window"); NSApp.terminate(nil); return }
                print("SCWindow.frame=\(mw.frame)")
                let filter = SCContentFilter(desktopIndependentWindow: mw)
                let cfg = SCScreenshotConfiguration()
                cfg.includeChildWindows = false
                cfg.showsCursor = false
                cfg.sourceRect = R
                let out = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: cfg)
                guard let img = out.sdrImage else { print("nil"); NSApp.terminate(nil); return }
                print("image px=\(img.width)x\(img.height) expected px=\(Int(R.width*2))x\(Int(R.height*2))")
                if let url = URL(string: "file:///tmp/rev28probe/sourcerect2.png") {
                    let rep = NSBitmapImageRep(cgImage: img)
                    try rep.representation(using: .png, properties: [:])?.write(to: url)
                    print("wrote \(url.path)")
                }
                let rep = NSBitmapImageRep(cgImage: img)
                // ASCII map downsample 40 cols
                let cols = 60, rows = 30
                var map = ""
                for r in 0..<rows {
                    var line = ""
                    for c in 0..<cols {
                        let x = c * img.width / cols, y = r * img.height / rows
                        if let col = rep.colorAt(x: x, y: y) {
                            let red = col.redComponent, green = col.greenComponent, blue = col.blueComponent
                            if red > 0.8 && blue > 0.8 && green < 0.3 { line += "M" }
                            else if green > 0.8 && blue > 0.8 && red < 0.3 { line += "C" }
                            else if red > 0.9 && green > 0.9 && blue > 0.9 { line += "." }
                            else { line += "#" }
                        } else { line += "?" }
                    }
                    map += line + "\n"
                }
                print(map)
            } catch { print("ERROR \(error)") }
            NSApp.terminate(nil)
        }
    }
}
let app = NSApplication.shared
let delegate = App(); app.delegate = delegate
app.setActivationPolicy(.regular); app.run()
