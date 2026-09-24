import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit

final class MarkerView: NSView {
    override var isFlipped: Bool { true }
    var markers: [(String, CGPoint, NSColor)] = [
        ("TL", CGPoint(x: 20, y: 20), .magenta),
        ("TR", CGPoint(x: 380, y: 20), .cyan),
        ("BL", CGPoint(x: 20, y: 312), .yellow),
        ("BR", CGPoint(x: 380, y: 312), .green),
    ]
    override func draw(_ dirtyRect: NSRect) {
        NSColor.white.setFill(); bounds.fill()
        for (_, p, c) in markers {
            c.setFill()
            NSRect(x: p.x - 5, y: p.y - 5, width: 10, height: 10).fill()
        }
    }
}

func clusters(_ rep: NSBitmapImageRep, _ match: (NSColor) -> Bool) -> [(Double, Double, Int)] {
    var pts: [(Int, Int)] = []
    for y in 0..<rep.pixelsHigh {
        for x in 0..<rep.pixelsWide {
            if let c = rep.colorAt(x: x, y: y), match(c) { pts.append((x, y)) }
        }
    }
    var result: [(Double, Double, Int)] = []
    var used = Array(repeating: false, count: pts.count)
    for i in 0..<pts.count where !used[i] {
        var stack = [i]; used[i] = true
        var sumX = 0, sumY = 0, n = 0
        while let k = stack.popLast() {
            sumX += pts[k].0; sumY += pts[k].1; n += 1
            for j in 0..<pts.count where !used[j] {
                if abs(pts[j].0 - pts[k].0) <= 3 && abs(pts[j].1 - pts[k].1) <= 3 { used[j] = true; stack.append(j) }
            }
        }
        result.append((Double(sumX)/Double(n), Double(sumY)/Double(n), n))
    }
    return result.filter { $0.2 > 50 }
}

final class App: NSObject, NSApplicationDelegate {
    var win: NSWindow!
    var view: MarkerView!
    func applicationDidFinishLaunching(_ n: Notification) {
        let w = NSWindow(contentRect: NSRect(x: 300, y: 260, width: 400, height: 332),
                         styleMask: [.titled, .closable], backing: .buffered, defer: false)
        win = w
        w.title = "Rev28 marker probe"
        view = MarkerView(frame: w.contentView!.bounds)
        view.autoresizingMask = [.width, .height]
        w.contentView = view
        w.makeKeyAndOrderFront(nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { self.probe() }
    }
    func probe() {
        let screenH = NSScreen.screens[0].frame.height
        let frameTL = CGRect(x: win.frame.minX, y: screenH - win.frame.maxY, width: win.frame.width, height: win.frame.height)
        print("window frameTL=\(frameTL) content size=\(view.bounds.size)")
        var expected: [(String, CGPoint)] = []
        for (name, p, _) in view.markers {
            let inWindowBL = view.convert(p, to: nil)
            let onScreenBL = win.convertPoint(toScreen: inWindowBL)
            let tl = CGPoint(x: onScreenBL.x, y: screenH - onScreenBL.y)
            expected.append((name, tl))
            print("marker \(name): viewLocal=\(p) windowTL=(\(inWindowBL.x),\(win.frame.height - inWindowBL.y)) screenTL=\(tl)")
        }
        Task { @MainActor in
            do {
                let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
                guard let mw = content.windows.first(where: { $0.windowID == CGWindowID(self.win.windowNumber) }) else { print("no window"); NSApp.terminate(nil); return }
                print("SCWindow.frame=\(mw.frame) contentRect=\((SCContentFilter(desktopIndependentWindow: mw)).contentRect)")
                // capture 1: default (no sourceRect)
                let f1 = SCContentFilter(desktopIndependentWindow: mw)
                let c1 = SCScreenshotConfiguration(); c1.includeChildWindows = false; c1.showsCursor = false
                let o1 = try await SCScreenshotManager.captureScreenshot(contentFilter: f1, configuration: c1)
                if let img = o1.sdrImage {
                    print("DEFAULT capture px=\(img.width)x\(img.height)")
                    let rep = NSBitmapImageRep(cgImage: img)
                    print("  full-frame SHA later; clusters:")
                    let mag = clusters(rep) { $0.redComponent > 0.7 && $0.blueComponent > 0.7 && $0.greenComponent < 0.4 }
                    let cy = clusters(rep) { $0.greenComponent > 0.7 && $0.blueComponent > 0.7 && $0.redComponent < 0.4 }
                    let ye = clusters(rep) { $0.redComponent > 0.7 && $0.greenComponent > 0.7 && $0.blueComponent < 0.4 }
                    let gr = clusters(rep) { $0.greenComponent > 0.5 && $0.redComponent < 0.4 && $0.blueComponent < 0.4 }
                    print("  magenta(TL) px=\(mag) cyan(TR) px=\(cy) yellow(BL) px=\(ye) green(BR) px=\(gr)")
                    try rep.representation(using: .png, properties: [:])?.write(to: URL(fileURLWithPath: "/tmp/rev28probe/markers-default.png"))
                }
                // capture 2: sourceRect = window frame in display space
                let f2 = SCContentFilter(desktopIndependentWindow: mw)
                let c2 = SCScreenshotConfiguration(); c2.includeChildWindows = false; c2.showsCursor = false; c2.sourceRect = frameTL
                let o2 = try await SCScreenshotManager.captureScreenshot(contentFilter: f2, configuration: c2)
                if let img = o2.sdrImage { print("SOURCE=frameTL capture px=\(img.width)x\(img.height)") }
                // capture 3: sourceRect = window-local 0,0,size
                let f3 = SCContentFilter(desktopIndependentWindow: mw)
                let c3 = SCScreenshotConfiguration(); c3.includeChildWindows = false; c3.showsCursor = false
                c3.sourceRect = CGRect(origin: .zero, size: frameTL.size)
                let o3 = try await SCScreenshotManager.captureScreenshot(contentFilter: f3, configuration: c3)
                if let img = o3.sdrImage { print("SOURCE=(0,0,size) capture px=\(img.width)x\(img.height)") }
            } catch { print("ERROR \(error)") }
            NSApp.terminate(nil)
        }
    }
}
let app = NSApplication.shared
let delegate = App(); app.delegate = delegate
app.setActivationPolicy(.regular); app.run()
