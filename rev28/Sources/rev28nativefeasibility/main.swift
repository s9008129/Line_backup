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

private func runG0() throws -> [String: Any] {
    let postAccess = CGPreflightPostEventAccess()
    let listenAccess = CGPreflightListenEventAccess()
    if !postAccess {
        throw ProbeFailure(stage: "F1-G0", capability: "CGPreflightPostEventAccess", detail: "false; no permission prompt or fallback permitted")
    }
    if !listenAccess {
        throw ProbeFailure(stage: "F1-G0", capability: "CGPreflightListenEventAccess", detail: "false; no permission prompt or fallback permitted")
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
    if bool(stateReply["active"]) != true {
        let activation = try harness.request("activate")
        guard bool(activation["active"]) == true else {
            throw ProbeFailure(stage: "F1-G0", capability: "controlled_window_activation", detail: "rev28harness did not become active")
        }
        stateReply = try harness.request("state")
    }
    guard let mainWindowNumber = (stateReply["mainWindowNumber"] as? NSNumber)?.uint32Value,
          let mainFrame = rect(stateReply["mainFrameTopLeft"]),
          let contentOrigin = point(stateReply["contentOriginLocalTopLeft"]),
          bool(stateReply["mainVisible"]) == true else {
        throw ProbeFailure(stage: "F1-G0", capability: "rev28harness.main_window_state", detail: "main window identity is incomplete")
    }
    guard let mainWindow = allWindows().first(where: { $0.number == mainWindowNumber && $0.ownerPID == harnessPID }) else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGWindowList.main_window", detail: "exact rev28harness window was not found")
    }
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

    let resetReply = try harness.request("hitReport", params: ["reset": true])
    guard integer(resetReply["mainHits"]) == 0, integer(resetReply["popupHits"]) == 0 else {
        throw ProbeFailure(stage: "F1-G0", capability: "controlled_hit_baseline", detail: "controlled application hit counters did not reset to zero")
    }

    let eventMask = (1 << CGEventType.mouseMoved.rawValue)
        | (1 << CGEventType.leftMouseDown.rawValue)
        | (1 << CGEventType.leftMouseUp.rawValue)
    let recorder = TapRecorder()
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
    guard let tap = CGEvent.tapCreateForPid(
        pid: harnessPID,
        place: .tailAppendEventTap,
        options: .listenOnly,
        eventsOfInterest: CGEventMask(eventMask),
        callback: callback,
        userInfo: Unmanaged.passUnretained(recorder).toOpaque()
    ) else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGEventTapCreateForPid", detail: "nil tap for exact controlled PID")
    }
    let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
    CGEvent.tapEnable(tap: tap, enable: true)
    guard CGEvent.tapIsEnabled(tap: tap) else {
        throw ProbeFailure(stage: "F1-G0", capability: "CGEventTapIsEnabled", detail: "tail/listen-only tap did not become enabled")
    }
    RunLoop.main.run(until: Date().addingTimeInterval(0.05))

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

    let scale = Double(NSScreen.main?.backingScaleFactor ?? 1)
    let displayID = CGMainDisplayID()
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
    let transformPx = roundTripAnchors.map { anchor -> Double in
        let roundTripped = captureGeometry.capturePoint(
            fromScreen: captureGeometry.screenPoint(fromCapture: anchor)
        )
        let dx = abs(roundTripped.x - anchor.x)
        let dy = abs(roundTripped.y - anchor.y)
        return max(dx, dy) * scale
    }.max() ?? 0

    let freshState = try harness.request("state")
    let freshFrame = rect(freshState["mainFrameTopLeft"]) ?? mainFrame
    let motionPoints = max(
        abs(Double(freshFrame.origin.x - mainFrame.origin.x)),
        max(abs(Double(freshFrame.origin.y - mainFrame.origin.y)),
            max(abs(Double(freshFrame.width - mainFrame.width)),
                abs(Double(freshFrame.height - mainFrame.height))))
    )
    let motionPx = motionPoints * scale
    let serializedLocations = constructedLocations.map { contractPoint($0) }
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

do {
    guard CommandLine.arguments.contains("--g0") else {
        throw ProbeFailure(stage: "F1-G0", capability: "arguments", detail: "run with --g0")
    }
    let result = try runG0()
    emitJSON(result)
    exit(result["verdict"] as? String == "F1_G0_SUPPORTED" ? 0 : 3)
} catch let failure as ProbeFailure {
    emitJSON([
        "record": "F1_G0_RESULT",
        "verdict": "F1_UNSUPPORTED",
        "first_missing_capability": failure.capability,
        "stage": failure.stage,
        "detail": failure.detail,
        "line_input": 0,
        "save_all_dispatch": 0,
        "grant_intent_ledger_calls": 0,
    ])
    exit(3)
} catch {
    emitJSON([
        "record": "F1_G0_RESULT",
        "verdict": "F1_UNSUPPORTED",
        "first_missing_capability": "unexpected_internal_failure",
        "detail": String(describing: error),
        "line_input": 0,
        "save_all_dispatch": 0,
        "grant_intent_ledger_calls": 0,
    ])
    exit(3)
}
