import AppKit
import Foundation
import Rev28Core

// rev28harness — synthetic AppKit harness app (plan §SYNTHETIC_HARNESS_
// CALIBRATION_PLAN). Own window hierarchy with known geometry and markers: a
// main window, a custom popup (child window) with a target row surface, a real
// NSOpenPanel in directory mode, a same-process look-alike chooser window, a
// download simulator, and controlled window movement. Driven over a JSON-lines
// stdio protocol by rev28ctl. It never touches any other application.

final class HitSurfaceView: NSView {
    var onHit: ((NSPoint) -> Void)?

    override func mouseDown(with event: NSEvent) {
        onHit?(convert(event.locationInWindow, from: nil))
    }

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}

/// Flipped content view: all local coordinates are top-left origin points, the
/// same convention as the capture/screen spaces the driver reasons in.
final class HarnessMainContentView: NSView {
    var albumTitle = "旻謙允禎成長日記"
    var countText = "57張照片"
    var menuRows = ["選擇項目", "修改相簿名稱", "儲存全部", "刪除相簿", "分享相簿"]
    var onHit: ((NSPoint) -> Void)?

    override var isFlipped: Bool { true }
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    static let menuTopPt: CGFloat = 200
    static let menuRowHeightPt: CGFloat = 40
    static let menuLeftPt: CGFloat = 40
    static let menuWidthPt: CGFloat = 320

    func rowRect(_ index: Int) -> CGRect {
        CGRect(
            x: Self.menuLeftPt,
            y: Self.menuTopPt + CGFloat(index) * Self.menuRowHeightPt,
            width: Self.menuWidthPt,
            height: Self.menuRowHeightPt
        )
    }

    var rowRects: [CGRect] { menuRows.indices.map { rowRect($0) } }

    override func draw(_ dirtyRect: NSRect) {
        NSColor.white.setFill()
        bounds.fill()

        // Calibration origin marker: strongly red, at a known content-local point,
        // so the driver can measure the capture origin directly from pixels.
        NSColor.systemRed.setFill()
        CGRect(x: 4, y: 4, width: 10, height: 10).fill()

        let titleAttributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 24),
            .foregroundColor: NSColor.black,
        ]
        albumTitle.draw(at: NSPoint(x: 40, y: 40), withAttributes: titleAttributes)
        countText.draw(at: NSPoint(x: 40, y: 90), withAttributes: [
            .font: NSFont.systemFont(ofSize: 20),
            .foregroundColor: NSColor.darkGray,
        ])

        for (index, row) in menuRows.enumerated() {
            let rect = rowRect(index)
            NSColor(calibratedWhite: 0.96, alpha: 1.0).setFill()
            rect.fill()
            NSColor.black.setStroke()
            let border = NSBezierPath(rect: rect)
            border.lineWidth = 1
            border.stroke()
            let attributes: [NSAttributedString.Key: Any] = [
                .font: NSFont.systemFont(ofSize: 18),
                .foregroundColor: NSColor.black,
            ]
            let size = row.size(withAttributes: attributes)
            row.draw(
                at: NSPoint(x: rect.midX - size.width / 2, y: rect.midY - size.height / 2),
                withAttributes: attributes
            )
        }
    }

    override func mouseDown(with event: NSEvent) {
        onHit?(convert(event.locationInWindow, from: nil))
    }
}

final class PopupContentView: NSView {
    var label = "儲存全部"
    var onHit: ((NSPoint) -> Void)?

    override var isFlipped: Bool { true }
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    var rowRect: CGRect { bounds.insetBy(dx: 8, dy: 8) }

    override func draw(_ dirtyRect: NSRect) {
        NSColor(calibratedWhite: 0.90, alpha: 1.0).setFill()
        bounds.fill()
        NSColor.systemGreen.setFill()
        CGRect(x: 4, y: 4, width: 8, height: 8).fill()
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 18),
            .foregroundColor: NSColor.black,
        ]
        let size = label.size(withAttributes: attributes)
        label.draw(
            at: NSPoint(x: bounds.midX - size.width / 2, y: bounds.midY - size.height / 2),
            withAttributes: attributes
        )
    }

    override func mouseDown(with event: NSEvent) {
        onHit?(convert(event.locationInWindow, from: nil))
    }
}

final class HarnessController: NSObject, NSApplicationDelegate {
    private var mainWindow: NSWindow!
    private var popupWindow: NSWindow!
    private var mainContent: HarnessMainContentView!
    private var popupContent: PopupContentView!
    private var fakeChooserWindow: NSWindow?
    private var panel: NSOpenPanel?
    private var panelShownEmitted = false
    private var mainHits = 0
    private var popupHits = 0
    private var lastMainHitLocal: NSPoint?
    private var lastPopupHitLocal: NSPoint?
    private let stdout = FileHandle.standardOutput
    private let startedAt = Date()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        buildWindows()
        LineReader(handle: FileHandle.standardInput, label: "rev28harness-stdin") { [weak self] line in
            DispatchQueue.main.async { self?.handle(line: line) }
        }.start()
        emit([
            "event": "ready",
            "pid": Int(getpid()),
            "startTimeUnix": startedAt.timeIntervalSince1970,
        ])
    }

    private func buildWindows() {
        let contentRect = CGRect(x: 200, y: 200, width: 800, height: 600)
        mainWindow = NSWindow(
            contentRect: contentRect,
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        mainWindow.title = "rev28 harness main"
        mainWindow.isReleasedWhenClosed = false
        mainWindow.hasShadow = true
        mainContent = HarnessMainContentView(frame: CGRect(x: 0, y: 0, width: 800, height: 600))
        mainContent.autoresizingMask = [.width, .height]
        mainContent.onHit = { [weak self] point in
            self?.mainHits += 1
            self?.lastMainHitLocal = point
        }
        mainWindow.contentView = mainContent

        popupWindow = NSWindow(
            contentRect: CGRect(x: 0, y: 0, width: 240, height: 60),
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )
        popupWindow.isReleasedWhenClosed = false
        popupWindow.hasShadow = true
        popupContent = PopupContentView(frame: CGRect(x: 0, y: 0, width: 240, height: 60))
        popupContent.autoresizingMask = [.width, .height]
        popupContent.onHit = { [weak self] point in
            self?.popupHits += 1
            self?.lastPopupHitLocal = point
        }
        popupWindow.contentView = popupContent
        // The popup is the topmost surface for the routing proof: floating level
        // keeps it above another process's normal-level occluder (plan item 4).
        popupWindow.level = .floating
        popupWindow.orderOut(nil)

        mainWindow.orderFrontRegardless()
        NSApp.activate(ignoringOtherApps: true)
    }

    // MARK: - Coordinate helpers (top-left screen coordinates vs AppKit frames)

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

    private func topLeftFrame(of window: NSWindow) -> [String: Double] {
        let frame = window.frame
        return [
            "x": Double(frame.origin.x),
            "y": Double(screenHeight() - frame.origin.y - frame.height),
            "w": Double(frame.width),
            "h": Double(frame.height),
        ]
    }

    private func topLeftRect(_ rect: CGRect) -> [String: Double] {
        [
            "x": Double(rect.origin.x),
            "y": Double(rect.origin.y),
            "w": Double(rect.width),
            "h": Double(rect.height),
        ]
    }

    // MARK: - Protocol

    private func handle(line: String) {
        guard let object = LineProtocol.decodeObject(line), let command = object["cmd"] as? String else { return }
        let id = object["id"] as? String ?? ""
        let params = object["params"] as? [String: Any] ?? [:]

        switch command {
        case "state":
            reply(id: id, ok: true, extra: state())
        case "setTitle":
            mainContent.albumTitle = params["title"] as? String ?? mainContent.albumTitle
            mainContent.needsDisplay = true
            reply(id: id, ok: true)
        case "setCountText":
            mainContent.countText = params["text"] as? String ?? mainContent.countText
            mainContent.needsDisplay = true
            reply(id: id, ok: true)
        case "setMenuRows":
            if let rows = params["rows"] as? [String] {
                mainContent.menuRows = rows
                mainContent.needsDisplay = true
            }
            reply(id: id, ok: true, extra: ["rows": mainContent.menuRows])
        case "setPopupLabel":
            popupContent.label = params["label"] as? String ?? popupContent.label
            popupContent.needsDisplay = true
            reply(id: id, ok: true)
        case "activate":
            NSApp.activate(ignoringOtherApps: true)
            mainWindow.orderFrontRegardless()
            reply(id: id, ok: true, extra: ["active": NSApp.isActive])
        case "setShadows":
            let on = (params["on"] as? NSNumber)?.boolValue ?? true
            mainWindow.hasShadow = on
            popupWindow.hasShadow = on
            reply(id: id, ok: true, extra: ["hasShadow": mainWindow.hasShadow])
        case "setFrame":
            guard let x = (params["x"] as? NSNumber)?.doubleValue,
                  let y = (params["y"] as? NSNumber)?.doubleValue,
                  let w = (params["w"] as? NSNumber)?.doubleValue,
                  let h = (params["h"] as? NSNumber)?.doubleValue else {
                reply(id: id, ok: false, error: "badFrame"); return
            }
            mainWindow.setFrame(appKitFrame(topLeft: CGRect(x: x, y: y, width: w, height: h)), display: true)
            reply(id: id, ok: true, extra: state())
        case "moveBy":
            let dx = (params["dx"] as? NSNumber)?.doubleValue ?? 0
            let dy = (params["dy"] as? NSNumber)?.doubleValue ?? 0
            var frame = mainWindow.frame
            frame.origin.x += dx
            frame.origin.y -= dy // AppKit y is bottom-up; dy is top-left screen delta
            mainWindow.setFrame(frame, display: true)
            reply(id: id, ok: true, extra: state())
        case "showPopup":
            let dx = (params["dx"] as? NSNumber)?.doubleValue ?? 120
            let dy = (params["dy"] as? NSNumber)?.doubleValue ?? 80
            if popupWindow.parent == nil {
                mainWindow.addChildWindow(popupWindow, ordered: .above)
            }
            let mainTopLeft = topLeftFrame(of: mainWindow)
            let rect = CGRect(
                x: (mainTopLeft["x"] ?? 0) + dx,
                y: (mainTopLeft["y"] ?? 0) + dy,
                width: 240,
                height: 60
            )
            popupWindow.setFrame(appKitFrame(topLeft: rect), display: true)
            popupWindow.orderFrontRegardless()
            reply(id: id, ok: true, extra: state())
        case "hidePopup":
            popupWindow.orderOut(nil)
            reply(id: id, ok: true)
        case "hitReport":
            let reset = (params["reset"] as? NSNumber)?.boolValue ?? false
            var report: [String: Any] = ["mainHits": mainHits, "popupHits": popupHits]
            if let point = lastMainHitLocal {
                report["lastMainHitLocal"] = topLeftRect(CGRect(x: point.x, y: point.y, width: 0, height: 0))
            }
            if let point = lastPopupHitLocal {
                report["lastPopupHitLocal"] = topLeftRect(CGRect(x: point.x, y: point.y, width: 0, height: 0))
            }
            if reset {
                mainHits = 0
                popupHits = 0
                lastMainHitLocal = nil
                lastPopupHitLocal = nil
            }
            reply(id: id, ok: true, extra: report)
        case "showPanel":
            let delayMs = (params["delayMs"] as? NSNumber)?.intValue ?? 0
            let directory = params["directory"] as? String ?? NSTemporaryDirectory()
            let marker = params["marker"] as? String ?? "rev28-panel-commit.marker"
            let expectedDirectory = params["expectedDirectory"] as? String
            showPanel(delayMs: delayMs, directory: directory, markerName: marker, expectedDirectory: expectedDirectory)
            reply(id: id, ok: true)
        case "closePanel":
            if let panel {
                panel.cancel(nil)
                reply(id: id, ok: true)
            } else {
                reply(id: id, ok: false, error: "noPanel")
            }
        case "focusPanel":
            guard let panel, panel.isVisible else { reply(id: id, ok: false, error: "panelNotVisible"); return }
            NSApp.activate(ignoringOtherApps: true)
            panel.makeKeyAndOrderFront(nil)
            reply(id: id, ok: true, extra: ["active": NSApp.isActive, "keyWindow": panel.isKeyWindow])
        case "showFakeChooser":
            let dx = (params["dx"] as? NSNumber)?.doubleValue ?? 60
            let dy = (params["dy"] as? NSNumber)?.doubleValue ?? 60
            let window = fakeChooserWindow ?? makeFakeChooserWindow()
            fakeChooserWindow = window
            let mainTopLeft = topLeftFrame(of: mainWindow)
            let rect = CGRect(
                x: (mainTopLeft["x"] ?? 0) + dx,
                y: (mainTopLeft["y"] ?? 0) + dy,
                width: 420,
                height: 220
            )
            window.setFrame(appKitFrame(topLeft: rect), display: true)
            window.orderFrontRegardless()
            reply(id: id, ok: true, extra: ["windowNumber": window.windowNumber])
        case "hideFakeChooser":
            fakeChooserWindow?.orderOut(nil)
            reply(id: id, ok: true)
        case "writeFiles":
            handleWriteFiles(id: id, params: params)
        case "quit":
            reply(id: id, ok: true)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { NSApp.terminate(nil) }
        default:
            reply(id: id, ok: false, error: "unknownCommand:\(command)")
        }
    }

    private func state() -> [String: Any] {
        var object: [String: Any] = [
            "pid": Int(getpid()),
            "screenHeight": Double(screenHeight()),
            "active": NSApp.isActive,
            "keyWindowIsMain": mainWindow.isKeyWindow,
            "mainVisible": mainWindow.isVisible,
            "mainFrameTopLeft": topLeftFrame(of: mainWindow),
            "hasShadow": mainWindow.hasShadow,
            "mainHits": mainHits,
            "popupHits": popupHits,
            "popupVisible": popupWindow.isVisible,
            "popupRowRectLocalTopLeft": topLeftRect(popupContent.rowRect),
            "menuRowRectsLocalTopLeft": mainContent.rowRects.map { topLeftRect($0) },
            "menuRows": mainContent.menuRows,
            "albumTitle": mainContent.albumTitle,
            "countText": mainContent.countText,
            "mainWindowNumber": mainWindow.windowNumber,
            "popupWindowNumber": popupWindow.windowNumber,
            "panelVisible": panel?.isVisible ?? (mainWindow.attachedSheet?.isVisible ?? false),
            "startTimeUnix": startedAt.timeIntervalSince1970,
        ]
        if popupWindow.isVisible {
            object["popupFrameTopLeft"] = topLeftFrame(of: popupWindow)
        }
        if let panel {
            object["panelWindowNumber"] = panel.windowNumber
            object["panelKeyWindow"] = panel.isKeyWindow
            object["panelDirectory"] = panel.directoryURL?.path ?? ""
            if let url = panel.url { object["panelSelectedURL"] = url.path }
        }
        let contentRect = mainWindow.contentRect(forFrameRect: mainWindow.frame)
        object["contentOriginLocalTopLeft"] = [
            "x": Double(contentRect.minX),
            "y": Double(mainWindow.frame.height - contentRect.maxY),
        ]
        object["popupContentOriginLocalTopLeft"] = ["x": 0.0, "y": 0.0]
        let windows: [[String: Any]] = [mainWindow, popupWindow].compactMap { window in
            guard let window else { return nil }
            return [
                "number": window.windowNumber,
                "title": window.title,
                "visible": window.isVisible,
                "frameTopLeft": topLeftFrame(of: window),
            ]
        }
        object["windows"] = windows
        return object
    }

    private func showPanel(delayMs: Int, directory: String, markerName: String, expectedDirectory: String?) {
        if let panel {
            panel.cancel(nil)
            self.panel = nil
        }
        panelShownEmitted = false
        let newPanel = NSOpenPanel()
        newPanel.canChooseDirectories = true
        newPanel.canChooseFiles = false
        newPanel.allowsMultipleSelection = false
        newPanel.canCreateDirectories = true
        newPanel.directoryURL = URL(fileURLWithPath: directory)
        newPanel.title = "rev28 harness chooser"
        newPanel.prompt = "開啟"
        panel = newPanel

        DispatchQueue.main.asyncAfter(deadline: .now() + Double(delayMs) / 1000.0) { [weak self] in
            guard let self, self.panel === newPanel else { return }
            self.emit(["event": "panelWillShow", "at": Date().timeIntervalSince1970])
            // Calibrate the frozen chooser predicate against the standalone
            // NSOpenPanel window shape described by the Rev28 plan.
            newPanel.begin { [weak self] response in
                self?.handlePanelCompletion(response: response, panel: newPanel, markerName: markerName, expectedDirectory: expectedDirectory)
            }
            NSApp.activate(ignoringOtherApps: true)
            newPanel.makeKeyAndOrderFront(nil)
            self.pollPanelVisible(panel: newPanel, attempts: 300)
        }
    }

    private func pollPanelVisible(panel: NSOpenPanel, attempts: Int) {
        guard attempts > 0 else { return }
        if panel.isVisible {
            if !panelShownEmitted {
                panelShownEmitted = true
                emit([
                    "event": "panelShown",
                    "at": Date().timeIntervalSince1970,
                    "windowNumber": panel.windowNumber,
                    "keyWindow": panel.isKeyWindow,
                    "appActive": NSApp.isActive,
                ])
            }
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.02) { [weak self] in
            self?.pollPanelVisible(panel: panel, attempts: attempts - 1)
        }
    }

    private func handlePanelCompletion(response: NSApplication.ModalResponse, panel: NSOpenPanel, markerName: String, expectedDirectory: String?) {
        var extra: [String: Any] = ["event": "panelClosed", "response": Int(response.rawValue), "at": Date().timeIntervalSince1970]
        if response == .OK {
            let chosenDirectory = panel.directoryURL?.standardizedFileURL
            let selectedURL = panel.url?.standardizedFileURL
            if let chosenDirectory {
                extra["chosenDirectory"] = chosenDirectory.path
            }
            if let selectedURL {
                extra["selectedURL"] = selectedURL.path
            }
            let expectedURL = expectedDirectory.map { URL(fileURLWithPath: $0).standardizedFileURL }
            if let chosenDirectory, let expectedURL, chosenDirectory.path == expectedURL.path {
                let markerURL = expectedURL.appendingPathComponent(markerName)
                do {
                    try Data("rev28 harness panel commit".utf8).write(to: markerURL, options: .atomic)
                    extra["markerPath"] = markerURL.path
                } catch {
                    extra["markerError"] = String(describing: error)
                }
            } else {
                extra["markerSuppressed"] = "chosenDirectoryDidNotMatchExpectedRunDestination"
                extra["expectedDirectory"] = expectedURL?.path ?? ""
            }
        }
        emit(extra)
    }

    private func makeFakeChooserWindow() -> NSWindow {
        let window = NSWindow(
            contentRect: CGRect(x: 0, y: 0, width: 420, height: 220),
            styleMask: [.titled],
            backing: .buffered,
            defer: false
        )
        window.title = "Open"
        window.isReleasedWhenClosed = false
        let content = NSView(frame: CGRect(x: 0, y: 0, width: 420, height: 220))
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
        window.contentView = content
        return window
    }

    private func handleWriteFiles(id: String, params: [String: Any]) {
        guard let directory = params["directory"] as? String else {
            reply(id: id, ok: false, error: "badDirectory"); return
        }
        let mode = params["mode"] as? String ?? "normal"
        let count = (params["count"] as? NSNumber)?.intValue ?? 3
        let dirURL = URL(fileURLWithPath: directory).standardizedFileURL
        var written: [String] = []
        do {
            try FileManager.default.createDirectory(at: dirURL, withIntermediateDirectories: true)
            switch mode {
            case "normal":
                for index in 0..<count {
                    let url = dirURL.appendingPathComponent(String(format: "photo-%03d.jpg", index))
                    let payload = Data(repeating: UInt8(0x41 + index % 26), count: 4096)
                    try payload.write(to: url, options: .atomic)
                    written.append(url.path)
                }
            case "zeroByte":
                for index in 0..<count {
                    let url = dirURL.appendingPathComponent(String(format: "photo-%03d.jpg", index))
                    try Data().write(to: url, options: .atomic)
                    written.append(url.path)
                }
            case "partialSuffix":
                for index in 0..<count {
                    let url = dirURL.appendingPathComponent(String(format: "photo-%03d.jpg.partial", index))
                    try Data(repeating: 0x42, count: 1024).write(to: url, options: .atomic)
                    written.append(url.path)
                }
            case "slowGrowth":
                let url = dirURL.appendingPathComponent("photo-000.jpg")
                try Data(repeating: 0x43, count: 1024).write(to: url, options: .atomic)
                written.append(url.path)
                for step in 1...3 {
                    let payload = Data(repeating: 0x44, count: 1024)
                    DispatchQueue.main.asyncAfter(deadline: .now() + Double(step) * 0.4) {
                        if let handle = try? FileHandle(forWritingTo: url) {
                            _ = try? handle.seekToEnd()
                            try? handle.write(contentsOf: payload)
                            try? handle.close()
                            self.emit([
                                "event": "fileGrew",
                                "path": url.path,
                                "at": Date().timeIntervalSince1970,
                            ])
                        }
                    }
                }
            default:
                reply(id: id, ok: false, error: "unknownMode:\(mode)"); return
            }
            reply(id: id, ok: true, extra: ["written": written, "mode": mode])
        } catch {
            reply(id: id, ok: false, error: String(describing: error))
        }
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
