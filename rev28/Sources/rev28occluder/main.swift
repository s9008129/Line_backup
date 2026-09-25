import AppKit
import Foundation
import Rev28Core

// rev28occluder — a separate-process helper used by the synthetic harness
// (plan §SYNTHETIC_HARNESS_CALIBRATION_PLAN): an OS-level occluding app (not a
// same-process NSWindow), a focus-theft actor, a look-alike chooser owner, and
// an unrelated writer for the tripwire-attribution fixture. It only ever
// touches its own windows and files under the fixture root it is told to use.

final class OccluderWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

final class OccluderHitView: NSView {
    var onHit: ((NSPoint) -> Void)?

    override func mouseDown(with event: NSEvent) {
        onHit?(convert(event.locationInWindow, from: nil))
    }

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}

final class OccluderController: NSObject, NSApplicationDelegate {
    private var coverWindow: OccluderWindow?
    private var lookalikeWindow: OccluderWindow?
    private var coverHits = 0
    private var lookalikeHits = 0
    private var lastCoverHitLocal: NSPoint?
    private var lastLookalikeHitLocal: NSPoint?
    private let stdout = FileHandle.standardOutput
    private let startedAt = Date()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        LineReader(handle: FileHandle.standardInput, label: "rev28occluder-stdin") { [weak self] line in
            DispatchQueue.main.async { self?.handle(line: line) }
        }.start()
        emit([
            "event": "ready",
            "pid": Int(getpid()),
            "startTimeUnix": startedAt.timeIntervalSince1970,
        ])
    }

    private func screenHeight() -> CGFloat {
        NSScreen.main?.frame.height ?? 0
    }

    private func appKitFrame(topLeft rect: CGRect) -> CGRect {
        CGRect(
            x: rect.origin.x,
            y: screenHeight() - rect.origin.y - rect.height,
            width: rect.width,
            height: rect.height
        )
    }

    private func topLeftFrame(appKit window: NSWindow) -> [String: Double] {
        let frame = window.frame
        return [
            "x": Double(frame.origin.x),
            "y": Double(screenHeight() - frame.origin.y - frame.height),
            "w": Double(frame.width),
            "h": Double(frame.height),
        ]
    }

    private func rect(from params: [String: Any]) -> CGRect? {
        guard let x = (params["x"] as? NSNumber)?.doubleValue,
              let y = (params["y"] as? NSNumber)?.doubleValue,
              let w = (params["w"] as? NSNumber)?.doubleValue,
              let h = (params["h"] as? NSNumber)?.doubleValue else {
            return nil
        }
        return CGRect(x: x, y: y, width: w, height: h)
    }

    private func handle(line: String) {
        guard let object = LineProtocol.decodeObject(line), let command = object["cmd"] as? String else {
            return
        }
        let id = object["id"] as? String ?? ""
        let params = object["params"] as? [String: Any] ?? [:]

        switch command {
        case "cover":
            guard let rect = rect(from: params) else { reply(id: id, ok: false, error: "badRect"); return }
            let window = coverWindow ?? makeWindow(hitCounter: .cover)
            coverWindow = window
            window.setFrame(appKitFrame(topLeft: rect), display: true)
            window.orderFrontRegardless()
            if (params["activate"] as? NSNumber)?.boolValue == true {
                NSApp.activate(ignoringOtherApps: true)
            }
            reply(id: id, ok: true, extra: ["frameTopLeft": topLeftFrame(appKit: window)])
        case "hide":
            coverWindow?.orderOut(nil)
            reply(id: id, ok: true)
        case "activate":
            NSApp.activate(ignoringOtherApps: true)
            if let window = coverWindow {
                window.orderFrontRegardless()
            }
            reply(id: id, ok: true, extra: ["active": NSApp.isActive])
        case "lookalike":
            guard let rect = rect(from: params) else { reply(id: id, ok: false, error: "badRect"); return }
            let window = lookalikeWindow ?? makeLookalikeWindow()
            lookalikeWindow = window
            window.setFrame(appKitFrame(topLeft: rect), display: true)
            window.orderFrontRegardless()
            reply(id: id, ok: true, extra: ["windowNumber": window.windowNumber])
        case "hideLookalike":
            lookalikeWindow?.orderOut(nil)
            reply(id: id, ok: true)
        case "writeFile":
            guard let path = params["path"] as? String else { reply(id: id, ok: false, error: "badPath"); return }
            let bytes = (params["bytes"] as? NSNumber)?.intValue ?? 0
            let payload = Data(repeating: 0x41, count: max(0, bytes))
            let url = URL(fileURLWithPath: path)
            do {
                try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
                try payload.write(to: url, options: .atomic)
                reply(id: id, ok: true, extra: ["path": url.path, "bytes": payload.count])
            } catch {
                reply(id: id, ok: false, error: String(describing: error))
            }
        case "state":
            var extra: [String: Any] = [
                "pid": Int(getpid()),
                "active": NSApp.isActive,
                "coverHits": coverHits,
                "lookalikeHits": lookalikeHits,
                "coverVisible": coverWindow?.isVisible ?? false,
                "lastCoverHitLocal": lastCoverHitLocal.map { ["x": Double($0.x), "y": Double($0.y)] } ?? [:],
                "lastLookalikeHitLocal": lastLookalikeHitLocal.map { ["x": Double($0.x), "y": Double($0.y)] } ?? [:],
                "lookalikeVisible": lookalikeWindow?.isVisible ?? false,
                "startTimeUnix": startedAt.timeIntervalSince1970,
            ]
            if let window = coverWindow {
                extra["coverFrameTopLeft"] = topLeftFrame(appKit: window)
            }
            if let window = lookalikeWindow {
                extra["lookalikeFrameTopLeft"] = topLeftFrame(appKit: window)
            }
            reply(id: id, ok: true, extra: extra)
        case "hitReport":
            let reset = (params["reset"] as? NSNumber)?.boolValue ?? false
            var report: [String: Any] = ["coverHits": coverHits, "lookalikeHits": lookalikeHits]
            if let point = lastCoverHitLocal {
                report["lastCoverHitLocal"] = ["x": Double(point.x), "y": Double(point.y), "w": 0.0, "h": 0.0]
            }
            if let point = lastLookalikeHitLocal {
                report["lastLookalikeHitLocal"] = ["x": Double(point.x), "y": Double(point.y), "w": 0.0, "h": 0.0]
            }
            if reset {
                coverHits = 0
                lookalikeHits = 0
                lastCoverHitLocal = nil
                lastLookalikeHitLocal = nil
            }
            reply(id: id, ok: true, extra: report)
        case "quit":
            reply(id: id, ok: true)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { NSApp.terminate(nil) }
        default:
            reply(id: id, ok: false, error: "unknownCommand:\(command)")
        }
    }

    private enum HitCounter { case cover, lookalike }

    private func makeWindow(hitCounter: HitCounter) -> OccluderWindow {
        let window = OccluderWindow(
            contentRect: CGRect(x: 0, y: 0, width: 400, height: 300),
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )
        window.isOpaque = true
        window.hasShadow = false
        window.backgroundColor = NSColor.systemOrange
        window.level = .normal
        window.isReleasedWhenClosed = false
        let view = OccluderHitView(frame: window.contentLayoutRect)
        view.autoresizingMask = [.width, .height]
        view.onHit = { [weak self] point in
            guard let self else { return }
            switch hitCounter {
            case .cover:
                self.coverHits += 1
                self.lastCoverHitLocal = point
            case .lookalike:
                self.lookalikeHits += 1
                self.lastLookalikeHitLocal = point
            }
        }
        window.contentView = view
        return window
    }

    private func makeLookalikeWindow() -> OccluderWindow {
        let window = OccluderWindow(
            contentRect: CGRect(x: 0, y: 0, width: 420, height: 220),
            styleMask: [.titled],
            backing: .buffered,
            defer: false
        )
        window.title = "Open"
        window.isOpaque = true
        window.hasShadow = true
        window.isReleasedWhenClosed = false
        let content = NSView(frame: window.contentLayoutRect)
        let field = NSTextField(frame: CGRect(x: 20, y: 150, width: 380, height: 24))
        field.stringValue = "/tmp"
        content.addSubview(field)
        let cancel = NSButton(frame: CGRect(x: 220, y: 30, width: 90, height: 32))
        cancel.title = "取消"
        content.addSubview(cancel)
        let open = NSButton(frame: CGRect(x: 320, y: 30, width: 90, height: 32))
        open.title = "打開"
        open.keyEquivalent = "\r"
        content.addSubview(open)
        let hitView = OccluderHitView(frame: window.contentLayoutRect)
        hitView.autoresizingMask = [.width, .height]
        hitView.onHit = { [weak self] point in
            self?.lookalikeHits += 1
            self?.lastLookalikeHitLocal = point
        }
        content.addSubview(hitView)
        window.contentView = content
        return window
    }

    private func reply(id: String, ok: Bool, error: String? = nil, extra: [String: Any] = [:]) {
        var object: [String: Any] = ["id": id, "ok": ok]
        if let error { object["error"] = error }
        for (key, value) in extra { object[key] = value }
        emit(object)
    }

    private func emit(_ object: [String: Any]) {
        LineProtocol.writeJSONObject(object, to: stdout)
    }
}

let application = NSApplication.shared
let controller = OccluderController()
application.delegate = controller
application.run()
