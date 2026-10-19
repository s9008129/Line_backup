import AppKit
import CoreGraphics
import Darwin
import Foundation
import Rev28NativeFeasibility

private let planSHA256 = "c75c11e6ab35913b8f651702dc897731930cb15a2937bb3e87ba0c41fe292bed"
private let reviewBinding = "pull/16#pullrequestreview-5571271859"
private let sourceToken: UInt64 = 0x4631473000004E41

private struct ProbeFailure: Error, CustomStringConvertible {
    let stage: String
    let capability: String
    let detail: String

    var description: String { "\(stage): \(capability): \(detail)" }
}

private struct WindowSnapshot {
    let number: UInt32
    let ownerPID: pid_t
    let layer: Int
    let alpha: Double
    let bounds: CGRect
    let onScreen: Bool
}

private struct TapEvent {
    let type: CGEventType
    let timestamp: UInt64
    let location: CGPoint
    let sourceUserData: UInt64
    let sourcePID: Int32
    let targetPID: Int32
    let windowUnderPointer: UInt32
    let windowCanHandleEvent: UInt32
}

private final class TapRecorder: @unchecked Sendable {
    private let condition = NSCondition()
    private var storage: [TapEvent] = []
    private var disabledTypes: [UInt32] = []

    func record(type: CGEventType, event: CGEvent) {
        let location = event.location
        let tapEvent = TapEvent(
            type: type,
            timestamp: event.timestamp,
            location: location,
            sourceUserData: UInt64(bitPattern: event.getIntegerValueField(.eventSourceUserData)),
            sourcePID: Int32(event.getIntegerValueField(.eventSourceUnixProcessID)),
            targetPID: Int32(event.getIntegerValueField(.eventTargetUnixProcessID)),
            windowUnderPointer: UInt32(max(0, event.getIntegerValueField(.mouseEventWindowUnderMousePointer))),
            windowCanHandleEvent: UInt32(max(0, event.getIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent)))
        )
        condition.lock()
        storage.append(tapEvent)
        condition.broadcast()
        condition.unlock()
    }

    func recordDisabled(type: CGEventType) {
        condition.lock()
        disabledTypes.append(type.rawValue)
        condition.broadcast()
        condition.unlock()
    }

    func snapshot() -> (events: [TapEvent], disabledTypes: [UInt32]) {
        condition.lock()
        defer { condition.unlock() }
        return (storage, disabledTypes)
    }

    @discardableResult
    func waitForCount(_ count: Int, timeout: TimeInterval) -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        condition.lock()
        defer { condition.unlock() }
        while storage.count < count {
            if !condition.wait(until: deadline) { break }
        }
        return storage.count >= count
    }
}

private final class JSONLineProcess: @unchecked Sendable {
    let process = Process()
    private let inputPipe = Pipe()
    private let outputPipe = Pipe()
    private let condition = NSCondition()
    private var buffer = Data()
    private var messages: [[String: Any]] = []
    private var ended = false
    private let readerQueue = DispatchQueue(label: "f1-json-line-reader")
    private var readerHandle: FileHandle?

    init(executableURL: URL) {
        process.executableURL = executableURL
        process.standardInput = inputPipe
        process.standardOutput = outputPipe
        process.standardError = FileHandle.standardError
    }

    func start() throws {
        try process.run()
        let reader = outputPipe.fileHandleForReading
        readerHandle = reader
        reader.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            self?.readerQueue.async { [weak self] in
                self?.consume(data)
            }
        }
    }

    func waitForEvent(_ name: String, timeout: TimeInterval) throws -> [String: Any] {
        try wait(timeout: timeout) { message in
            message["event"] as? String == name
        }
    }

    func request(_ command: String, params: [String: Any] = [:], timeout: TimeInterval = 5) throws -> [String: Any] {
        let id = UUID().uuidString
        let object: [String: Any] = ["id": id, "cmd": command, "params": params]
        let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        inputPipe.fileHandleForWriting.write(data)
        inputPipe.fileHandleForWriting.write(Data([0x0A]))
        let reply: [String: Any]
        do {
            reply = try wait(timeout: timeout) { message in
                message["id"] as? String == id
            }
        } catch let failure as ProbeFailure {
            throw ProbeFailure(stage: failure.stage, capability: command, detail: failure.detail)
        }
        if let ok = reply["ok"] as? Bool, !ok {
            let error = reply["error"] as? String ?? "unknownChildError"
            throw ProbeFailure(stage: "child_protocol", capability: command, detail: error)
        }
        return reply
    }

    func stop() {
        try? inputPipe.fileHandleForWriting.close()
        readerHandle?.readabilityHandler = nil
        if process.isRunning {
            process.terminate()
        }
    }

    private func wait(timeout: TimeInterval, predicate: ([String: Any]) -> Bool) throws -> [String: Any] {
        let deadline = Date().addingTimeInterval(timeout)
        condition.lock()
        defer { condition.unlock() }
        while true {
            if let index = messages.firstIndex(where: predicate) {
                return messages.remove(at: index)
            }
            if ended {
                throw ProbeFailure(stage: "child_protocol", capability: "response", detail: "child process ended before a matching response")
            }
            if !condition.wait(until: deadline) {
                throw ProbeFailure(stage: "child_protocol", capability: "response", detail: "timed out waiting for child response")
            }
        }
    }

    private func consume(_ data: Data) {
        condition.lock()
        if data.isEmpty {
            ended = true
            condition.broadcast()
            condition.unlock()
            return
        }
        buffer.append(data)
        while let newline = buffer.firstIndex(of: 0x0A) {
            let line = buffer[..<newline]
            buffer.removeSubrange(...newline)
            if !line.isEmpty,
               let object = try? JSONSerialization.jsonObject(with: Data(line)) as? [String: Any] {
                messages.append(object)
                condition.broadcast()
            }
        }
        condition.unlock()
    }
}

private func emitJSON(_ object: [String: Any]) {
    guard JSONSerialization.isValidJSONObject(object),
          let data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .withoutEscapingSlashes]) else {
        FileHandle.standardError.write(Data("F1_INTERNAL_JSON_ERROR\n".utf8))
        return
    }
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([0x0A]))
}

private func dictionary(_ any: Any?) -> [String: Any]? {
    any as? [String: Any]
}

private func number(_ any: Any?) -> Double? {
    (any as? NSNumber)?.doubleValue
}

private func integer(_ any: Any?) -> Int? {
    (any as? NSNumber)?.intValue
}

private func bool(_ any: Any?) -> Bool? {
    (any as? NSNumber)?.boolValue
}

private func point(_ any: Any?) -> CGPoint? {
    guard let value = dictionary(any),
          let x = number(value["x"]),
          let y = number(value["y"]) else { return nil }
    return CGPoint(x: x, y: y)
}

private func rect(_ any: Any?) -> CGRect? {
    guard let value = dictionary(any),
          let x = number(value["x"]),
          let y = number(value["y"]),
          let width = number(value["w"]),
          let height = number(value["h"]) else { return nil }
    return CGRect(x: x, y: y, width: width, height: height)
}

private func contractPoint(_ value: CGPoint) -> ContractPoint {
    ContractPoint(x: Double(value.x), y: Double(value.y))
}

private func contractRect(_ value: CGRect) -> ContractRect {
    ContractRect(x: Double(value.origin.x), y: Double(value.origin.y), width: Double(value.width), height: Double(value.height))
}

private func pointObject(_ value: CGPoint) -> [String: Double] {
    ["x": Double(value.x), "y": Double(value.y)]
}

private func pointObject(_ value: ContractPoint) -> [String: Double] {
    ["x": value.x, "y": value.y]
}

private func rectObject(_ value: CGRect) -> [String: Double] {
    [
        "x": Double(value.origin.x),
        "y": Double(value.origin.y),
        "w": Double(value.width),
        "h": Double(value.height),
    ]
}

private func rectObject(_ value: ContractRect) -> [String: Double] {
    ["x": value.x, "y": value.y, "w": value.width, "h": value.height]
}

private func utcTimestamp() -> String {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    return formatter.string(from: Date())
}

private func monotonicTimestamp() -> Double {
    ProcessInfo.processInfo.systemUptime
}

private func allWindows() -> [WindowSnapshot] {
    guard let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)
        as? [[String: Any]] else {
        return []
    }
    return list.compactMap { entry in
        guard let number = (entry[kCGWindowNumber as String] as? NSNumber)?.uint32Value,
              let ownerPID = (entry[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value,
              let layer = (entry[kCGWindowLayer as String] as? NSNumber)?.intValue,
              let alpha = (entry[kCGWindowAlpha as String] as? NSNumber)?.doubleValue,
              let boundsDictionary = entry[kCGWindowBounds as String] as? NSDictionary,
              let bounds = CGRect(dictionaryRepresentation: boundsDictionary) else { return nil }
        let onScreen = (entry[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue ?? true
        return WindowSnapshot(number: number, ownerPID: ownerPID, layer: layer, alpha: alpha, bounds: bounds, onScreen: onScreen)
    }
}

private func topmostWindow(at point: CGPoint, alphaPositiveOnly: Bool = true) -> WindowSnapshot? {
    allWindows().first { window in
        (!alphaPositiveOnly || window.alpha > 0) && window.bounds.contains(point)
    }
}

private func windowsAbove(target: WindowSnapshot, at point: CGPoint) -> [WindowSnapshot] {
    var result: [WindowSnapshot] = []
    for window in allWindows() {
        if window.number == target.number { break }
        if window.alpha > 0 && window.bounds.contains(point) {
            result.append(window)
        }
    }
    return result
}

private func firstMismatch(_ checks: [(String, Bool)]) -> String? {
    checks.first(where: { !$0.1 })?.0
}

private func runG0(evidenceOnly: Bool = false) throws -> [String: Any] {
    let postAccess = evidenceOnly ? false : CGPreflightPostEventAccess()
    let listenAccess = evidenceOnly ? false : CGPreflightListenEventAccess()
    if !evidenceOnly {
        if !postAccess {
            throw ProbeFailure(stage: "F1-G0", capability: "CGPreflightPostEventAccess", detail: "false; no permission prompt or fallback permitted")
        }
        if !listenAccess {
            throw ProbeFailure(stage: "F1-G0", capability: "CGPreflightListenEventAccess", detail: "false; no permission prompt or fallback permitted")
        }
    }

    let executableDirectory = Bundle.main.executableURL?.deletingLastPathComponent()
    guard let executableDirectory else {
        throw ProbeFailure(stage: "F1-G0", capability: "executable_directory", detail: "Bundle.main.executableURL is unavailable")
    }
    let harnessURL = executableDirectory.appendingPathComponent("rev28harness")
    guard FileManager.default.isExecutableFile(atPath: harnessURL.path) else {
        throw ProbeFailure(stage: "F1-G0", capability: "rev28harness", detail: "built executable not found at \(harnessURL.path)")
    }

    let harness = JSONLineProcess(executableURL: harnessURL)
    defer { harness.stop() }
    try harness.start()
    let ready = try harness.waitForEvent("ready", timeout: 8)
    guard let harnessPID = (ready["pid"] as? NSNumber)?.int32Value, harnessPID > 0 else {
        throw ProbeFailure(stage: "F1-G0", capability: "rev28harness.ready.pid", detail: "missing or invalid process id")
    }

    var stateReply = try harness.request("state")
    if !evidenceOnly, bool(stateReply["active"]) != true {
        let activation = try harness.request("activate")
        guard bool(activation["active"]) == true else {
            throw ProbeFailure(stage: "F1-G0", capability: "controlled_window_activation", detail: "rev28harness did not become active")
        }
        stateReply = try harness.request("state")
    }
    let appKitStateObservedUTC = utcTimestamp()
    let appKitStateObservedMonotonic = monotonicTimestamp()
    guard let mainWindowNumber = (stateReply["mainWindowNumber"] as? NSNumber)?.uint32Value,
          let mainFrame = rect(stateReply["mainFrameTopLeft"]),
          let contentOrigin = point(stateReply["contentOriginLocalTopLeft"]),
          bool(stateReply["mainVisible"]) == true else {
        throw ProbeFailure(stage: "F1-G0", capability: "rev28harness.main_window_state", detail: "main window identity is incomplete")
    }
    guard let mainWindow = allWindows().first(where: { $0.number == mainWindowNumber && $0.ownerPID == harnessPID }) else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGWindowList.main_window", detail: "exact rev28harness window was not found")
    }
    let cgWindowObservedUTC = utcTimestamp()
    let cgWindowObservedMonotonic = monotonicTimestamp()
    guard mainWindow.layer == 0, mainWindow.onScreen, mainWindow.alpha > 0 else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGWindowList.main_surface", detail: "controlled ordinary surface is not layer-0, on-screen, alpha-positive")
    }

    let target = CGPoint(
        x: mainFrame.origin.x + mainFrame.width * 0.62,
        y: mainFrame.origin.y + max(contentOrigin.y + 80, mainFrame.height * 0.58)
    )
    guard mainWindow.bounds.contains(target) else {
        throw ProbeFailure(stage: "F1-G0", capability: "controlled_target_point", detail: "selected point is outside the exact controlled window")
    }
    if let above = topmostWindow(at: target), above.number != mainWindow.number {
        throw ProbeFailure(stage: "F1-G0", capability: "topmostSurfaceMatchesTarget", detail: "another alpha-positive window \(above.number) is above controlled window \(mainWindow.number)")
    }
    let aboveWindows = windowsAbove(target: mainWindow, at: target)
    guard aboveWindows.isEmpty else {
        throw ProbeFailure(stage: "F1-G0", capability: "noAmbiguousWindowAbove", detail: "windows above target: \(aboveWindows.map(\.number))")
    }

    if !evidenceOnly {
        let resetReply = try harness.request("hitReport", params: ["reset": true])
        guard integer(resetReply["mainHits"]) == 0, integer(resetReply["popupHits"]) == 0 else {
            throw ProbeFailure(stage: "F1-G0", capability: "controlled_hit_baseline", detail: "controlled application hit counters did not reset to zero")
        }
    }

    var recorder: TapRecorder?
    var tap: CFMachPort?
    if !evidenceOnly {
        let eventMask = (1 << CGEventType.mouseMoved.rawValue)
            | (1 << CGEventType.leftMouseDown.rawValue)
            | (1 << CGEventType.leftMouseUp.rawValue)
        let liveRecorder = TapRecorder()
        let callback: CGEventTapCallBack = { _, type, event, userInfo in
            guard let userInfo else { return Unmanaged.passUnretained(event) }
            let recorder = Unmanaged<TapRecorder>.fromOpaque(userInfo).takeUnretainedValue()
            switch type {
            case .mouseMoved, .leftMouseDown, .leftMouseUp:
                recorder.record(type: type, event: event)
            case .tapDisabledByTimeout, .tapDisabledByUserInput:
                recorder.recordDisabled(type: type)
            default:
                break
            }
            return Unmanaged.passUnretained(event)
        }
        guard let liveTap = CGEvent.tapCreateForPid(
            pid: harnessPID,
            place: .tailAppendEventTap,
            options: .listenOnly,
            eventsOfInterest: CGEventMask(eventMask),
            callback: callback,
            userInfo: Unmanaged.passUnretained(liveRecorder).toOpaque()
        ) else {
            throw ProbeFailure(stage: "F1-G0", capability: "CGEventTapCreateForPid", detail: "nil tap for exact controlled PID")
        }
        let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, liveTap, 0)
        CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
        CGEvent.tapEnable(tap: liveTap, enable: true)
        guard CGEvent.tapIsEnabled(tap: liveTap) else {
            throw ProbeFailure(stage: "F1-G0", capability: "CGEventTapIsEnabled", detail: "tail/listen-only tap did not become enabled")
        }
        RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        recorder = liveRecorder
        tap = liveTap
    }

    func configuredEvent(type: CGEventType) throws -> CGEvent {
        guard let event = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: target, mouseButton: .left) else {
            throw ProbeFailure(stage: "F1-G0", capability: "CGEvent", detail: "event creation failed for \(type.rawValue)")
        }
        event.location = target
        event.setIntegerValueField(.eventSourceUserData, value: Int64(bitPattern: sourceToken))
        event.setIntegerValueField(.eventSourceUnixProcessID, value: Int64(getpid()))
        event.setIntegerValueField(.eventTargetUnixProcessID, value: Int64(harnessPID))
        if type == .leftMouseDown || type == .leftMouseUp {
            event.setIntegerValueField(.mouseEventClickState, value: 1)
            event.setIntegerValueField(.mouseEventButtonNumber, value: 0)
        }
        return event
    }

    let moveEvent = try configuredEvent(type: .mouseMoved)
    let downEvent = try configuredEvent(type: .leftMouseDown)
    let upEvent = try configuredEvent(type: .leftMouseUp)
    let constructedLocations = [moveEvent, downEvent, upEvent].map(\.location)
    guard constructedLocations.allSatisfy({ $0.x.isFinite && $0.y.isFinite }) else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGEventGetLocation", detail: "constructed event location is non-finite")
    }

    let mainScreen = NSScreen.main
    let scale = Double(mainScreen?.backingScaleFactor ?? 1)
    let displayID = CGMainDisplayID()
    let displayBounds = CGDisplayBounds(displayID)
    let mainScreenFrame = mainScreen?.frame ?? .zero
    let captureBBox = contractRect(mainWindow.bounds)
    let captureGeometry = CaptureGeometry(
        windowFramePt: captureBBox,
        captureBBoxPt: captureBBox,
        scale: scale
    )
    let targetCapture = captureGeometry.capturePoint(fromScreen: contractPoint(target))
    let witnessRect = ContractRect(
        x: targetCapture.x - 20,
        y: targetCapture.y - 20,
        width: 40,
        height: 40
    )

    let frameDeltaPoints = max(
        abs(Double(mainFrame.origin.x - mainWindow.bounds.origin.x)),
        max(abs(Double(mainFrame.origin.y - mainWindow.bounds.origin.y)),
            max(abs(Double(mainFrame.width - mainWindow.bounds.width)),
                abs(Double(mainFrame.height - mainWindow.bounds.height))))
    )
    let localizePx = frameDeltaPoints * scale
    let roundTripAnchors = [
        targetCapture,
        ContractPoint(x: witnessRect.x, y: witnessRect.y),
        ContractPoint(x: witnessRect.maxX, y: witnessRect.maxY),
    ]
    let roundTripEvidence: [[String: Any]] = roundTripAnchors.map { anchor in
        let screen = captureGeometry.screenPoint(fromCapture: anchor)
        let roundTripped = captureGeometry.capturePoint(fromScreen: screen)
        let dx = abs(roundTripped.x - anchor.x)
        let dy = abs(roundTripped.y - anchor.y)
        return [
            "anchor_capture_px": pointObject(anchor),
            "screen_point": pointObject(screen),
            "round_tripped_capture_px": pointObject(roundTripped),
            "residual_capture_px_before_scale": max(dx, dy),
        ]
    }
    let transformPx = roundTripAnchors.map { anchor -> Double in
        let roundTripped = captureGeometry.capturePoint(
            fromScreen: captureGeometry.screenPoint(fromCapture: anchor)
        )
        let dx = abs(roundTripped.x - anchor.x)
        let dy = abs(roundTripped.y - anchor.y)
        return max(dx, dy) * scale
    }.max() ?? 0
    let transformResidualCapturePx = roundTripEvidence.map {
        $0["residual_capture_px_before_scale"] as? Double ?? 0
    }.max() ?? 0

    let freshStateObservedUTC = utcTimestamp()
    let freshStateObservedMonotonic = monotonicTimestamp()
    let freshState = try harness.request("state")
    let freshStateReceivedUTC = utcTimestamp()
    let freshStateReceivedMonotonic = monotonicTimestamp()
    let freshFrame = rect(freshState["mainFrameTopLeft"]) ?? mainFrame
    let motionPoints = max(
        abs(Double(freshFrame.origin.x - mainFrame.origin.x)),
        max(abs(Double(freshFrame.origin.y - mainFrame.origin.y)),
            max(abs(Double(freshFrame.width - mainFrame.width)),
                abs(Double(freshFrame.height - mainFrame.height))))
    )
    let motionPx = motionPoints * scale
    let serializedLocations = constructedLocations.map { contractPoint($0) }
    let serializeEvidence: [[String: Any]] = zip(
        [ConstructedEventKind.mouseMoved, .leftMouseDown, .leftMouseUp],
        serializedLocations
    ).map { (kind, location) in
        let capture = captureGeometry.capturePoint(fromScreen: location)
        let dx = abs(capture.x - targetCapture.x)
        let dy = abs(capture.y - targetCapture.y)
        return [
            "kind": kind.rawValue,
            "location_screen_pt": pointObject(location),
            "location_capture_px": pointObject(capture),
            "residual_px": max(dx, max(dy, capture.distance(to: targetCapture))),
            "posted": false,
        ]
    }
    let serializeResidualPx = serializedLocations.map { location -> Double in
        let capture = captureGeometry.capturePoint(fromScreen: location)
        let dx = abs(capture.x - targetCapture.x)
        let dy = abs(capture.y - targetCapture.y)
        return max(dx, max(dy, capture.distance(to: targetCapture)))
    }.max() ?? 0

    let probeResidualPoints = 2.0 / max(1, scale)
    let hitProbePoints = [
        target,
        CGPoint(x: target.x - probeResidualPoints, y: target.y),
        CGPoint(x: target.x + probeResidualPoints, y: target.y),
        CGPoint(x: target.x, y: target.y - probeResidualPoints),
        CGPoint(x: target.x, y: target.y + probeResidualPoints),
    ]
    let hitTargetsMatch = hitProbePoints.allSatisfy { probe in
        topmostWindow(at: probe)?.number == mainWindow.number
    }
    let targetBinding = "f1-controlled-window-\(mainWindow.number)-point-\(Int(target.x))-\(Int(target.y))"
    let now = ProcessInfo.processInfo.systemUptime
    let events = ConstructedEventSet(
        mouseMoved: ConstructedEvent(
            kind: .mouseMoved,
            locationScreen: serializedLocations[0],
            sourceUserData: sourceToken,
            sourcePIDField: Int32(getpid()),
            targetPIDField: harnessPID
        ),
        leftMouseDown: ConstructedEvent(
            kind: .leftMouseDown,
            locationScreen: serializedLocations[1],
            sourceUserData: sourceToken,
            sourcePIDField: Int32(getpid()),
            targetPIDField: harnessPID
        ),
        leftMouseUp: ConstructedEvent(
            kind: .leftMouseUp,
            locationScreen: serializedLocations[2],
            sourceUserData: sourceToken,
            sourcePIDField: Int32(getpid()),
            targetPIDField: harnessPID
        )
    )
    let admissionRequest = PreDownAdmissionRequest(
        context: .controlledFeasibility,
        runtime: RuntimeBinding(
            planSHA256: planSHA256,
            sourceSHA256: sourceTokenHex(),
            runtimeSHA256: "f1-native-feasibility-\(getpid())",
            reviewBinding: reviewBinding
        ),
        targetProcess: ProcessBinding(
            pid: harnessPID,
            processInstanceToken: "rev28harness:\(harnessPID):\(ready["startTimeUnix"] ?? "unknown")",
            bundleID: "f1.controlled.rev28harness"
        ),
        sourceProcessPID: Int32(getpid()),
        targetWindow: WindowBinding(
            windowID: mainWindow.number,
            layer: mainWindow.layer,
            framePt: contractRect(mainWindow.bounds)
        ),
        display: DisplayBinding(displayID: displayID, scale: scale),
        targetBindingSHA256: targetBinding,
        targetGeometry: TargetGeometry(
            kind: .albumCard,
            witnessRectPx: witnessRect,
            uncertaintyPx: 2,
            selectedPointPx: targetCapture,
            uniqueWitness: true,
            hitTestProbeCount: hitProbePoints.count
        ),
        captureGeometry: captureGeometry,
        requestedCapturePoint: targetCapture,
        constructedEvents: events,
        uncertainty: UncertaintyVector(
            localizePx: localizePx,
            transformPx: transformPx,
            motionPx: motionPx,
            serializePx: serializeResidualPx,
            allMeasured: true
        ),
        surface: SurfaceEvidence(
            expectedWindowID: mainWindow.number,
            observedTopmostWindowID: topmostWindow(at: target)?.number ?? 0,
            expectedLayer: mainWindow.layer,
            observedLayer: mainWindow.layer,
            alpha: mainWindow.alpha,
            isOnScreen: mainWindow.onScreen,
            noAmbiguousWindowAbove: aboveWindows.isEmpty
        ),
        hitTest: HitTestEvidence(
            selectedPointIdentifiesTarget: topmostWindow(at: target)?.number == mainWindow.number,
            allUncertaintyProbesIdentifyTarget: hitTargetsMatch,
            probeCount: hitProbePoints.count
        ),
        authorization: AuthorizationBinding(
            authority: "f1_controlled_nontransactional",
            authorizationID: "F1-G0-\(UUID().uuidString)",
            intentRevision: "F1-G0",
            targetBindingSHA256: targetBinding,
            singleUse: true,
            consumed: false,
            expiresAtMonotonic: now + 5
        ),
        nowMonotonic: now,
        preDownDeadlineMonotonic: now + 1
    )
    let admissionDecision = PreDownContract.evaluate(admissionRequest, phase: .beforeHover)
    let admissionEvaluatedUTC = utcTimestamp()
    let admissionEvaluatedMonotonic = monotonicTimestamp()
    if evidenceOnly {
        let screenHeightPt = number(stateReply["screenHeight"]) ?? 0
        let appKitBottomLeftFrame = CGRect(
            x: mainFrame.origin.x,
            y: screenHeightPt - mainFrame.origin.y - mainFrame.height,
            width: mainFrame.width,
            height: mainFrame.height
        )
        let constructedCapturePoint = captureGeometry.capturePoint(fromScreen: serializedLocations[1])
        let constructionResidualPx = max(
            abs(constructedCapturePoint.x - targetCapture.x),
            max(
                abs(constructedCapturePoint.y - targetCapture.y),
                constructedCapturePoint.distance(to: targetCapture)
            )
        )
        let uPrePx = localizePx + transformPx + motionPx + serializeResidualPx
        let admissionOutcome: String
        let admissionTerminal: String
        let admissionFailures: [[String: String]]
        switch admissionDecision {
        case .admitted:
            admissionOutcome = "ADMITTED"
            admissionTerminal = "NONE"
            admissionFailures = []
        case let .refused(refusal):
            admissionOutcome = "REFUSED"
            admissionTerminal = refusal.terminal.rawValue
            admissionFailures = refusal.failures.map { ["code": $0.code, "detail": $0.detail] }
        }
        let rawAppKitState: [String: Any] = [
            "source": "rev28harness.state",
            "screenHeight": stateReply["screenHeight"] ?? NSNull(),
            "mainFrameTopLeft": stateReply["mainFrameTopLeft"] ?? NSNull(),
            "contentOriginLocalTopLeft": stateReply["contentOriginLocalTopLeft"] ?? NSNull(),
            "hasShadow": stateReply["hasShadow"] ?? NSNull(),
            "mainWindowNumber": stateReply["mainWindowNumber"] ?? NSNull(),
            "mainVisible": stateReply["mainVisible"] ?? NSNull(),
            "active": stateReply["active"] ?? NSNull(),
        ]
        let freshAppKitState: [String: Any] = [
            "source": "rev28harness.state.second_snapshot",
            "screenHeight": freshState["screenHeight"] ?? NSNull(),
            "mainFrameTopLeft": freshState["mainFrameTopLeft"] ?? NSNull(),
            "freshFramePresent": rect(freshState["mainFrameTopLeft"]) != nil,
        ]
        let cgWindowState: [String: Any] = [
            "source": "CGWindowListCopyWindowInfo.optionOnScreenOnly",
            "window_id": Int(mainWindow.number),
            "owner_pid": Int(mainWindow.ownerPID),
            "layer": mainWindow.layer,
            "alpha": mainWindow.alpha,
            "on_screen": mainWindow.onScreen,
            "bounds": rectObject(mainWindow.bounds),
        ]
        let displayState: [String: Any] = [
            "display_id": Int(displayID),
            "cg_display_bounds": rectObject(displayBounds),
            "main_screen_frame": rectObject(mainScreenFrame),
            "main_screen_count": NSScreen.screens.count,
            "backing_scale": scale,
            "scale_source": "NSScreen.main.backingScaleFactor",
            "window_inside_cg_main_display": displayBounds.contains(mainWindow.bounds),
            "window_display_binding": displayBounds.contains(mainWindow.bounds)
                ? "WINDOW_FRAME_INSIDE_CG_MAIN_DISPLAY"
                : "WINDOW_FRAME_CROSSES_OR_OUTSIDE_CG_MAIN_DISPLAY",
        ]
        let localizeInputs: [String: Any] = [
            "appkit_frame_bottom_left_screen_pt": rectObject(appKitBottomLeftFrame),
            "appkit_frame_provenance": "DERIVED_FROM_REV28HARNESS_MAIN_FRAME_TOP_LEFT_AND_SCREEN_HEIGHT_SAME_APPKIT_PATH",
            "appkit_frame_top_left_screen_pt": rectObject(mainFrame),
            "cgwindow_frame_top_left_screen_pt": rectObject(mainWindow.bounds),
            "delta_points": [
                "x": abs(Double(mainFrame.origin.x - mainWindow.bounds.origin.x)),
                "y": abs(Double(mainFrame.origin.y - mainWindow.bounds.origin.y)),
                "w": abs(Double(mainFrame.width - mainWindow.bounds.width)),
                "h": abs(Double(mainFrame.height - mainWindow.bounds.height)),
            ],
            "max_delta_points": frameDeltaPoints,
            "multiplier": scale,
            "formula": "max(abs(dx),abs(dy),abs(dw),abs(dh)) * backing_scale",
            "units": "capture_px",
            "value_px": localizePx,
        ]
        let transformInputs: [String: Any] = [
            "anchors_capture_px": roundTripAnchors.map { pointObject($0) },
            "round_trips": roundTripEvidence,
            "residual_capture_px_before_multiplier": transformResidualCapturePx,
            "multiplier": scale,
            "formula": "max(max(abs(dx),abs(dy)) * backing_scale) over round-trip anchors",
            "units": "capture_px",
            "value_px": transformPx,
            "source": "CaptureGeometry round trip; not independent SCK-to-CGEvent alignment evidence",
        ]
        let motionInputs: [String: Any] = [
            "first_frame_top_left_screen_pt": rectObject(mainFrame),
            "second_frame_top_left_screen_pt": freshAppKitState["mainFrameTopLeft"] ?? NSNull(),
            "second_frame_present": rect(freshState["mainFrameTopLeft"]) != nil,
            "delta_points": [
                "x": abs(Double(freshFrame.origin.x - mainFrame.origin.x)),
                "y": abs(Double(freshFrame.origin.y - mainFrame.origin.y)),
                "w": abs(Double(freshFrame.width - mainFrame.width)),
                "h": abs(Double(freshFrame.height - mainFrame.height)),
            ],
            "max_delta_points": motionPoints,
            "multiplier": scale,
            "formula": "max(abs(dx),abs(dy),abs(dw),abs(dh)) * backing_scale",
            "units": "capture_px",
            "value_px": motionPx,
            "sampling_only": true,
        ]
        let serializeInputs: [String: Any] = [
            "events": serializeEvidence,
            "constructed_locations_screen_pt": serializedLocations.map { pointObject($0) },
            "target_capture_px": pointObject(targetCapture),
            "formula": "max(dx,dy,distance) between constructed location and requested target in capture px",
            "units": "capture_px",
            "value_px": serializeResidualPx,
            "event_posting": 0,
        ]
        let evidence: [String: Any] = [
            "record": "F1_PRE_DOWN_EVIDENCE_V1",
            "verdict": "PRE_DOWN_EVIDENCE_CAPTURED",
            "captured_at_utc": utcTimestamp(),
            "timestamps": [
                "appkit_state_utc": appKitStateObservedUTC,
                "appkit_state_monotonic": appKitStateObservedMonotonic,
                "cgwindow_utc": cgWindowObservedUTC,
                "cgwindow_monotonic": cgWindowObservedMonotonic,
                "fresh_state_request_utc": freshStateObservedUTC,
                "fresh_state_request_monotonic": freshStateObservedMonotonic,
                "fresh_state_receipt_utc": freshStateReceivedUTC,
                "fresh_state_receipt_monotonic": freshStateReceivedMonotonic,
                "admission_evaluation_utc": admissionEvaluatedUTC,
                "admission_evaluation_monotonic": admissionEvaluatedMonotonic,
                "clock_units": "UTC ISO8601; monotonic seconds from ProcessInfo.systemUptime",
            ],
            "identity": [
                "harness_pid": Int(harnessPID),
                "main_window_number": Int(mainWindowNumber),
                "target_binding": targetBinding,
                "target_screen_point": pointObject(target),
                "target_capture_point": pointObject(targetCapture),
            ],
            "coordinate_contract": [
                "appkit_origin": "bottom-left screen points (derived from same rev28harness AppKit path)",
                "cgwindow_origin": "top-left screen points",
                "capture_units": "capture pixels after backing_scale",
                "backing_scale": scale,
                "sck_geometry": "NOT_USED",
                "sck_geometry_note": "captureBBox is CGWindow bounds, not an SCK frame",
            ],
            "raw_appkit_state": rawAppKitState,
            "fresh_appkit_state": freshAppKitState,
            "raw_cgwindow": cgWindowState,
            "display": displayState,
            "capture_geometry": [
                "window_frame_pt": rectObject(captureGeometry.windowFramePt),
                "capture_bbox_pt": rectObject(captureGeometry.captureBBoxPt),
                "scale": captureGeometry.scale,
                "capture_bbox_source": "COPIED_FROM_CGWINDOW_BOUNDS",
            ],
            "uncertainty": [
                "U_localize": localizeInputs,
                "U_transform": transformInputs,
                "U_motion": motionInputs,
                "U_serialize": serializeInputs,
                "U_pre_px": uPrePx,
                "contract_total_px": admissionRequest.uncertainty.totalPx.map { $0 as Any } ?? NSNull(),
                "all_measured": admissionRequest.uncertainty.allMeasured,
                "component_sum_px": [localizePx, transformPx, motionPx, serializeResidualPx],
                "construction_residual_px": constructionResidualPx,
                "threshold_px": 2.0,
            ],
            "admission": [
                "decision": admissionOutcome,
                "terminal": admissionTerminal,
                "failures": admissionFailures,
                "first_failure": admissionFailures.first ?? [String: String](),
                "phase": AdmissionPhase.beforeHover.rawValue,
            ],
            "zero_event_guarantee": [
                "events_posted": 0,
                "event_tap_created": false,
                "event_post_reachable_after_return": false,
                "fallthrough_to_g0": false,
                "preflight_post_event_access": "NOT_QUERIED",
                "preflight_listen_event_access": "NOT_QUERIED",
                "line_input": 0,
                "save_all_dispatch": 0,
                "grant_intent_ledger_calls": 0,
            ],
            "evidence_only": true,
        ]
        return evidence
    }
    guard case let .admitted(admission) = admissionDecision else {
        let failures: [String]
        if case let .refused(refusal) = admissionDecision {
            failures = refusal.failures.map { "\($0.code):\($0.detail)" }
        } else {
            failures = ["unknown admission state"]
        }
        throw ProbeFailure(stage: "F1-G0", capability: "PRE_DOWN_ADMISSION", detail: "zero_event_refusal \(failures)")
    }

    guard admission.totalUncertaintyPx <= 2.0,
          admission.constructionResidualPx <= admission.totalUncertaintyPx else {
        throw ProbeFailure(stage: "F1-G0", capability: "PRE_DOWN_2PX_BOUND", detail: "admission returned an out-of-bound state")
    }
    guard let recorder = recorder, let tap = tap else {
        throw ProbeFailure(stage: "F1-G0", capability: "F1_ACTIVE_TAP", detail: "dispatch path started without an active recorder/tap")
    }

    moveEvent.post(tap: .cghidEventTap)
    downEvent.post(tap: .cghidEventTap)
    usleep(30_000)
    upEvent.post(tap: .cghidEventTap)
    _ = recorder.waitForCount(3, timeout: 1.0)
    RunLoop.main.run(until: Date().addingTimeInterval(0.2))

    let hitReport = try harness.request("hitReport")
    let mainHits = integer(hitReport["mainHits"]) ?? 0
    let popupHits = integer(hitReport["popupHits"]) ?? 0
    let lastHitLocal = point(hitReport["lastMainHitLocal"])
    let expectedLocal = CGPoint(x: target.x - mainFrame.origin.x, y: target.y - mainFrame.origin.y - contentOrigin.y)
    let sameControl = lastHitLocal.map { hypot($0.x - expectedLocal.x, $0.y - expectedLocal.y) <= 1.0 } ?? false
    let delivered = mainHits == 1 && sameControl
    let activated = delivered && popupHits == 0

    let observed = recorder.snapshot()
    let tokenEvents = observed.events.filter { $0.sourceUserData == sourceToken }
    let expectedTypes: [CGEventType] = [.mouseMoved, .leftMouseDown, .leftMouseUp]
    let ordered = tokenEvents.map(\.type) == expectedTypes
    let timestamps = tokenEvents.map(\.timestamp)
    let timestampPresent = timestamps.count == 3 && timestamps.allSatisfy { $0 > 0 }
    let chronology = timestampPresent && zip(timestamps, timestamps.dropFirst()).allSatisfy { $0 < $1 }
    let sourcePIDMatches = tokenEvents.count == 3 && tokenEvents.allSatisfy { $0.sourcePID == Int32(getpid()) }
    let targetPIDMatches = tokenEvents.count == 3 && tokenEvents.allSatisfy { $0.targetPID == harnessPID }
    let windowFieldsMatch = tokenEvents.count == 3 && tokenEvents.allSatisfy {
        $0.windowUnderPointer == mainWindow.number && $0.windowCanHandleEvent == mainWindow.number
    }
    let locationsMatch = tokenEvents.count == 3 && tokenEvents.allSatisfy { event in
        let capture = captureGeometry.capturePoint(fromScreen: contractPoint(event.location))
        let requestedCapture = captureGeometry.capturePoint(fromScreen: admission.requestedScreenPoint)
        let dx = abs(capture.x - requestedCapture.x)
        let dy = abs(capture.y - requestedCapture.y)
        return max(dx, max(dy, capture.distance(to: requestedCapture))) <= admission.totalUncertaintyPx + 1e-9
    }

    var fieldStatuses: [String: EvidenceStatus] = [
        "timestamp": timestampPresent ? .present : .absent,
        "location": locationsMatch ? .present : .mismatch,
        "source_user_data": tokenEvents.count == 3 ? .present : .mismatch,
        "source_pid": sourcePIDMatches ? .present : .mismatch,
        "target_pid": targetPIDMatches ? .present : .mismatch,
        "window_under_pointer": windowFieldsMatch ? .present : .mismatch,
        "window_can_handle": windowFieldsMatch ? .present : .mismatch,
        "event_order": ordered ? .present : .mismatch,
        "chronology": chronology ? .present : .mismatch,
    ]
    if !ordered {
        fieldStatuses["event_order"] = .mismatch
    }
    if !observed.disabledTypes.isEmpty {
        fieldStatuses["tap_enabled"] = .mismatch
    } else {
        fieldStatuses["tap_enabled"] = .present
    }

    let audit = PostDownAuditRecord(
        mouseDownPosted: true,
        tapPlacement: "tailAppendEventTap",
        tapOptions: "listenOnly",
        tapReadyBeforeFirstEvent: true,
        observedSequence: tokenEvents.map { eventTypeName($0.type) },
        fieldStatuses: fieldStatuses,
        sourceTokenMatched: tokenEvents.count == 3,
        expectedWindowID: mainWindow.number,
        deliveredWindowID: delivered ? mainWindow.number : UInt32(0),
        expectedControl: "mainContentView",
        activatedControl: activated ? "mainContentView" : "none",
        underlyingControlActivated: popupHits > 0
    )
    let auditDecision = PostDownAuditContract.assess(audit)
    let firstMissing = firstMismatch([
        ("timestamp", timestampPresent),
        ("location", locationsMatch),
        ("source_user_data", tokenEvents.count == 3),
        ("source_pid", sourcePIDMatches),
        ("target_pid", targetPIDMatches),
        ("window_under_pointer", windowFieldsMatch),
        ("window_can_handle", windowFieldsMatch),
        ("event_order", ordered),
        ("chronology", chronology),
        ("tap_enabled", observed.disabledTypes.isEmpty),
        ("DELIVERED_TO_APP", delivered),
        ("ACTIVATED_CONTROL", activated),
    ])
    let supported = auditDecision == .confirmed && firstMissing == nil

    let rawEvents: [[String: Any]] = observed.events.map { event in
        [
            "type": eventTypeName(event.type),
            "timestamp": String(event.timestamp),
            "x": Double(event.location.x),
            "y": Double(event.location.y),
            "source_user_data": String(event.sourceUserData),
            "source_pid": Int(event.sourcePID),
            "target_pid": Int(event.targetPID),
            "window_under_pointer": Int(event.windowUnderPointer),
            "window_can_handle": Int(event.windowCanHandleEvent),
            "token_match": event.sourceUserData == sourceToken,
        ]
    }
    let output: [String: Any] = [
        "record": "F1_JSONL_EVENT_SAMPLE",
        "events": rawEvents,
        "disabled_tap_events": observed.disabledTypes.map { Int($0) },
    ]
    emitJSON(output)

    return [
        "record": "F1_G0_RESULT",
        "verdict": supported ? "F1_G0_SUPPORTED" : "F1_UNSUPPORTED",
        "first_missing_capability": firstMissing ?? "",
        "preflight_post_event_access": postAccess,
        "preflight_listen_event_access": listenAccess,
        "tap_pid": Int(harnessPID),
        "tap_placement": "tailAppendEventTap",
        "tap_options": "listenOnly",
        "tap_ready": CGEvent.tapIsEnabled(tap: tap),
        "constructed_point_x": Double(target.x),
        "constructed_point_y": Double(target.y),
        "observed_token_event_count": tokenEvents.count,
        "unrelated_event_count": observed.events.count - tokenEvents.count,
        "uncertainty_px": [
            "localize": localizePx,
            "transform": transformPx,
            "motion": motionPx,
            "serialize": serializeResidualPx,
            "total": admission.totalUncertaintyPx,
        ],
        "construction_residual_px": admission.constructionResidualPx,
        "fields": fieldStatuses.reduce(into: [String: String]()) { $0[$1.key] = $1.value.rawValue },
        "proof_classes": [
            "OBSERVED_AT_TAP": tokenEvents.count == 3 && ordered ? "PRESENT" : "ABSENT",
            "DELIVERED_TO_APP": delivered ? "PRESENT" : "ABSENT",
            "ACTIVATED_CONTROL": activated ? "PRESENT" : "ABSENT",
        ],
        "main_hits": mainHits,
        "popup_hits": popupHits,
        "post_down_terminal": auditDecision.terminal?.rawValue ?? "CONFIRMED",
        "controlled_window_number": Int(mainWindow.number),
        "controlled_window_layer": mainWindow.layer,
        "controlled_target_binding": targetBinding,
        "line_input": 0,
        "save_all_dispatch": 0,
        "grant_intent_ledger_calls": 0,
    ]
}

private func eventTypeName(_ type: CGEventType) -> String {
    switch type {
    case .mouseMoved:
        return "mouseMoved"
    case .leftMouseDown:
        return "leftMouseDown"
    case .leftMouseUp:
        return "leftMouseUp"
    case .tapDisabledByTimeout:
        return "tapDisabledByTimeout"
    case .tapDisabledByUserInput:
        return "tapDisabledByUserInput"
    default:
        return "eventType-\(type.rawValue)"
    }
}

private func sourceTokenHex() -> String {
    String(sourceToken, radix: 16)
}

let evidenceOnlyMode = CommandLine.arguments.contains("--pre-down-evidence-only")

do {
    if evidenceOnlyMode {
        let result = try runG0(evidenceOnly: true)
        emitJSON(result)
        exit(0)
    }
    guard CommandLine.arguments.contains("--g0") else {
        throw ProbeFailure(stage: "F1-G0", capability: "arguments", detail: "run with --g0 or --pre-down-evidence-only")
    }
    let result = try runG0()
    emitJSON(result)
    exit(result["verdict"] as? String == "F1_G0_SUPPORTED" ? 0 : 3)
} catch let failure as ProbeFailure {
    emitJSON(
        evidenceOnlyMode
            ? [
                "record": "F1_PRE_DOWN_EVIDENCE_V1",
                "verdict": "EVIDENCE_ONLY_INCOMPLETE",
                "first_missing_capability": failure.capability,
                "stage": failure.stage,
                "detail": failure.detail,
                "zero_event_guarantee": [
                    "events_posted": 0,
                    "event_tap_created": false,
                    "fallthrough_to_g0": false,
                    "line_input": 0,
                    "save_all_dispatch": 0,
                    "grant_intent_ledger_calls": 0,
                ],
            ]
            : [
                "record": "F1_G0_RESULT",
                "verdict": "F1_UNSUPPORTED",
                "first_missing_capability": failure.capability,
                "stage": failure.stage,
                "detail": failure.detail,
                "line_input": 0,
                "save_all_dispatch": 0,
                "grant_intent_ledger_calls": 0,
            ]
    )
    exit(3)
} catch {
    emitJSON(
        evidenceOnlyMode
            ? [
                "record": "F1_PRE_DOWN_EVIDENCE_V1",
                "verdict": "EVIDENCE_ONLY_INCOMPLETE",
                "first_missing_capability": "unexpected_internal_failure",
                "detail": String(describing: error),
                "zero_event_guarantee": [
                    "events_posted": 0,
                    "event_tap_created": false,
                    "fallthrough_to_g0": false,
                    "line_input": 0,
                    "save_all_dispatch": 0,
                    "grant_intent_ledger_calls": 0,
                ],
            ]
            : [
                "record": "F1_G0_RESULT",
                "verdict": "F1_UNSUPPORTED",
                "first_missing_capability": "unexpected_internal_failure",
                "detail": String(describing: error),
                "line_input": 0,
                "save_all_dispatch": 0,
                "grant_intent_ledger_calls": 0,
            ]
    )
    exit(3)
}
