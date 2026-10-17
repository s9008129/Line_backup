import AppKit
import ApplicationServices
import CoreGraphics
import Darwin
import Foundation
import ImageIO
import Vision

/// A bounded, read-only snapshot of one running application's accessibility
/// tree and its process/window/display identities. The snapshot is an
/// observation only; it never focuses, activates, presses, or writes to AX.
public struct PassiveContextObservation: Codable, Equatable, Sendable {
    public struct Point: Codable, Equatable, Sendable {
        public let x: Double
        public let y: Double
        public init(x: Double, y: Double) { self.x = x; self.y = y }
    }

    public struct Rect: Codable, Equatable, Sendable {
        public let x: Double
        public let y: Double
        public let width: Double
        public let height: Double
        public init(x: Double, y: Double, width: Double, height: Double) {
            self.x = x; self.y = y; self.width = width; self.height = height
        }
        public var cgRect: CGRect { CGRect(x: CGFloat(x), y: CGFloat(y), width: CGFloat(width), height: CGFloat(height)) }
    }

    public struct Process: Codable, Equatable, Sendable {
        public let bundleID: String
        public let appVersion: String?
        public let pid: Int32
        public let startTimeSeconds: Int64
        public let startTimeMicroseconds: Int32
    }

    public struct Display: Codable, Equatable, Sendable {
        public let displayID: UInt32
        public let boundsPt: Rect
        public let backingScale: Double
    }

    public struct Window: Codable, Equatable, Sendable {
        public let nodeID: String?
        public let windowNumber: UInt32?
        public let cgWindowNumber: UInt32?
        public let cgOwnerPID: Int32?
        public let cgLayer: Int?
        public let cgFramePt: Rect?
        public let title: String?
        public let role: String?
        public let subrole: String?
        public let framePt: Rect?
        public let isMain: Bool?
        public let isFocused: Bool?
        public let isOnScreen: Bool?
        public let displayIDs: [UInt32]
    }

    /// Minimal current CG z-order inventory. It deliberately excludes titles,
    /// names and AX content from other processes.
    public struct OnScreenWindow: Codable, Equatable, Sendable {
        public let ownerPID: Int32?
        public let windowNumber: UInt32?
        public let layer: Int?
        public let boundsPt: Rect?
        public let alpha: Double?
        public let isOnScreen: Bool?
        public let orderFrontToBack: Int
    }

    public struct AttributeError: Codable, Equatable, Sendable {
        public let attribute: String
        public let errorCode: Int32
    }

    public struct Node: Codable, Equatable, Sendable {
        public let id: String
        public let parentID: String?
        public let role: String?
        public let subrole: String?
        public let title: String?
        public let description: String?
        public let value: String?
        public let minimumValue: Double?
        public let maximumValue: Double?
        public let help: String?
        public let identifier: String?
        public let framePt: Rect?
        public let enabled: Bool?
        public let focused: Bool?
        public let selected: Bool?
        public let offscreen: Bool?
        public let windowNumber: UInt32?
        public let children: [String]
        public let missingAttributes: [String]
        public let nullAttributes: [String]
        public let unsupportedAttributes: [String]
        public let attributeErrors: [AttributeError]
    }

    public struct Limits: Codable, Equatable, Sendable {
        public let maxDepth: Int
        public let maxNodes: Int
        public let maxStringBytes: Int
    }

    public struct OCRItem: Codable, Equatable, Sendable {
        public let text: String
        public let confidence: Double
        public let bounds: Rect
        public let candidateCount: Int
    }

    public struct Visual: Codable, Equatable, Sendable {
        public let sourceSHA256: String
        public let width: Int
        public let height: Int
        public let recognitionLanguages: [String]
        public let ocr: [OCRItem]
        public let ellipsisComponents: [VisualDot]
    }

    public struct VisualDot: Codable, Equatable, Sendable {
        public let x: Double
        public let y: Double
        public let area: Int
        public let width: Int
        public let height: Int
    }

    public let schemaVersion: Int
    public let observedAtUnixMilliseconds: Int64
    public let target: Process
    public let frontmostPID: Int32?
    public let focusedWindowID: UInt32?
    public let windows: [Window]
    public let onScreenWindows: [OnScreenWindow]
    public let onScreenInventoryAvailable: Bool
    public let displays: [Display]
    public let nodes: [Node]
    public let complete: Bool
    public let truncated: Bool
    public let truncationReasons: [String]
    public let limits: Limits
    public let errors: [String]
    public let visual: Visual?

    public static let lineBundleID = "jp.naver.line.mac"
    public static let defaultLimits = Limits(maxDepth: 12, maxNodes: 2_000, maxStringBytes: 4_096)

    /// Finds exactly one live process with the requested bundle identifier and
    /// captures its AX tree without sending UI input. Ambiguous instances fail
    /// closed so callers must bind a fresh PID explicitly when needed.
    public static func capture(bundleID: String, limits: Limits = defaultLimits,
                               imageURL: URL? = nil, imageSHA256: String? = nil) throws -> Self {
        guard bundleID == lineBundleID else { throw CaptureError.unsupportedBundle(bundleID) }
        guard limits.maxDepth >= 0, limits.maxNodes > 0, limits.maxStringBytes > 0 else {
            throw CaptureError.invalidLimits
        }
        guard (imageURL == nil) == (imageSHA256 == nil) else { throw CaptureError.invalidImageBinding }
        let matches = NSRunningApplication.runningApplications(withBundleIdentifier: bundleID)
            .filter { !$0.isTerminated }
        guard matches.count == 1, let app = matches.first else {
            throw CaptureError.processCount(bundleID: bundleID, count: matches.count)
        }
        let pid = app.processIdentifier
        let appVersion: String? = app.bundleURL.flatMap { url in
            Bundle(url: url)?.infoDictionary?["CFBundleShortVersionString"] as? String
        }
        guard let process = ProcessInstanceID.current(pid: pid),
              NSRunningApplication(processIdentifier: pid)?.bundleIdentifier == bundleID else {
            throw CaptureError.processIdentityUnavailable(pid)
        }
        var collector = Collector(bundleID: bundleID, pid: pid, process: process, limits: limits,
                                  appVersion: appVersion, imageURL: imageURL, imageSHA256: imageSHA256)
        return try collector.capture()
    }

    public enum CaptureError: Error, CustomStringConvertible {
        case unsupportedBundle(String)
        case processCount(bundleID: String, count: Int)
        case processIdentityUnavailable(Int32)
        case invalidImageBinding
        case invalidLimits

        public var description: String {
            switch self {
            case .unsupportedBundle(let bundle): return "unsupported bundle identifier: \(bundle)"
            case .processCount(let bundle, let count): return "expected exactly one \(bundle) process; found \(count)"
            case .processIdentityUnavailable(let pid): return "process identity unavailable or changed for pid \(pid)"
            case .invalidImageBinding: return "invalid retained image path, hash, or image bytes"
            case .invalidLimits: return "native-context traversal limits must be positive"
            }
        }
    }

    private struct Collector {
        let bundleID: String
        let pid: Int32
        let process: ProcessInstanceID
        let limits: Limits
        let appVersion: String?
        let imageURL: URL?
        let imageSHA256: String?
        var nodes: [Node] = []
        var errors: [String] = []
        var truncationReasons: [String] = []
        var focusedWindowID: UInt32?
        var nextID = 0
        let deadlineNanos = DispatchTime.now().uptimeNanoseconds + 30_000_000_000

        mutating func capture() throws -> PassiveContextObservation {
            let appElement = AXUIElementCreateApplication(pid)
            AXUIElementSetMessagingTimeout(appElement, 1.0)
            traverse(appElement, parentID: nil, depth: 0)
            let displays = Self.activeDisplays()
            let windows = collectWindows(appElement, displays: displays)
            var onScreenInventoryAvailable = false
            let onScreenWindows = Self.onScreenWindowInventory(
                truncationReasons: &truncationReasons,
                available: &onScreenInventoryAvailable
            )
            if !onScreenInventoryAvailable { errors.append("CG on-screen window inventory unavailable") }
            if ProcessInstanceID.current(pid: pid) != process || NSRunningApplication(processIdentifier: pid)?.bundleIdentifier != bundleID {
                errors.append("process identity changed during observation")
            }
            if DispatchTime.now().uptimeNanoseconds >= deadlineNanos, !truncationReasons.contains("timeLimit") {
                truncationReasons.append("timeLimit")
            }
            let visual: Visual?
            do { visual = try loadVisual() }
            catch { visual = nil; errors.append("retained image OCR failed: \(error)") }
            let frontmost = NSWorkspace.shared.frontmostApplication?.processIdentifier
            let isComplete = truncationReasons.isEmpty && errors.isEmpty
            return PassiveContextObservation(
                schemaVersion: 1,
                observedAtUnixMilliseconds: Int64(Date().timeIntervalSince1970 * 1_000),
                target: Process(bundleID: bundleID, appVersion: appVersion, pid: pid,
                                startTimeSeconds: process.startTimeSeconds,
                                startTimeMicroseconds: process.startTimeMicroseconds),
                frontmostPID: frontmost,
                focusedWindowID: focusedWindowID,
                windows: windows,
                onScreenWindows: onScreenWindows,
                onScreenInventoryAvailable: onScreenInventoryAvailable,
                displays: displays,
                nodes: nodes,
                complete: isComplete,
                truncated: !truncationReasons.isEmpty,
                truncationReasons: Array(Set(truncationReasons)).sorted(),
                limits: limits,
                errors: errors,
                visual: visual
            )
        }

        mutating func collectWindows(_ app: AXUIElement, displays: [Display]) -> [Window] {
            let focused = read(app, "AXFocusedWindow")
            var result: [Window] = []
            if case .value(let value) = focused, CFGetTypeID(value) == AXUIElementGetTypeID() {
                let element = unsafeBitCast(value, to: AXUIElement.self)
                focusedWindowID = uint32(element, "AXWindowNumber") ?? AXDriver.windowNumber(of: element)
            }
            switch read(app, "AXWindows") {
            case .value(let value):
                guard let values = value as? [AXUIElement] else {
                    errors.append("AXWindows returned a non-element list")
                    return []
                }
                let cgEntries = Self.cgWindowEntries(pid: pid)
                if cgEntries.isEmpty { errors.append("CG window inventory returned no target-process windows") }
                if values.count > 128 { truncationReasons.append("windowLimit") }
                for element in values.prefix(128) {
                    let frame = rect(element)
                    let axWindowID = uint32(element, "AXWindowNumber") ?? AXDriver.windowNumber(of: element)
                    let cgEntry = axWindowID.flatMap { windowNumber in cgEntries.first(where: { $0.number == windowNumber }) }
                    let nodeMatches = axWindowID.map { number in nodes.filter { $0.role == "AXWindow" && $0.windowNumber == number } } ?? []
                    let nodeID = nodeMatches.count == 1 ? nodeMatches[0].id : nil
                    if axWindowID == nil || cgEntry == nil || nodeID == nil {
                        errors.append("AX window has no exact CG window identity binding")
                    }
                    let focusedWindow = focusedWindowID != nil && axWindowID == focusedWindowID
                    result.append(Window(
                        nodeID: nodeID,
                        windowNumber: axWindowID,
                        cgWindowNumber: cgEntry?.number,
                        cgOwnerPID: cgEntry?.ownerPID,
                        cgLayer: cgEntry?.layer,
                        cgFramePt: cgEntry.map { Rect(x: $0.frame.minX, y: $0.frame.minY, width: $0.frame.width, height: $0.frame.height) },
                        title: string(element, "AXTitle"), role: string(element, "AXRole"),
                        subrole: string(element, "AXSubrole"),
                        framePt: frame.map { Rect(x: $0.minX, y: $0.minY, width: $0.width, height: $0.height) },
                        isMain: bool(element, "AXMain"), isFocused: focusedWindow ? true : bool(element, "AXFocused"),
                        isOnScreen: cgEntry?.onScreen,
                        displayIDs: cgEntry.map { entry in displays.filter { $0.boundsPt.cgRect.intersects(entry.frame) }.map(\.displayID) } ?? []
                    ))
                }
            case .missing: errors.append("AXWindows is missing")
            case .null: errors.append("AXWindows is null")
            case .failure(let code): errors.append("AXWindows failed with error \(code)")
            }
            return result
        }

        mutating func traverse(_ element: AXUIElement, parentID: String?, depth: Int) -> String {
            guard DispatchTime.now().uptimeNanoseconds < deadlineNanos else { truncationReasons.append("timeLimit"); return "" }
            guard depth <= limits.maxDepth else { truncationReasons.append("depthLimit"); return "" }
            guard nodes.count < limits.maxNodes else { truncationReasons.append("nodeLimit"); return "" }
            let id = "ax-\(nextID)"
            nextID += 1
            var available: Set<String> = []
            var raw: CFArray?
            let namesResult = AXUIElementCopyAttributeNames(element, &raw)
            if namesResult == .success, let names = raw as? [String] { available = Set(names) }
            else { errors.append("\(id): AX attribute-name read failed (\(namesResult.rawValue))") }

            let attrs = ["AXRole", "AXSubrole", "AXTitle", "AXDescription", "AXValue", "AXMinValue", "AXMaxValue", "AXHelp", "AXIdentifier",
                         "AXEnabled", "AXFocused", "AXSelected", "AXPosition", "AXSize", "AXWindowNumber", "AXChildren"]
            var missing: [String] = []
            var nulls: [String] = []
            var unsupported: [String] = []
            var attrErrors: [AttributeError] = []
            var values: [String: CFTypeRef] = [:]
            for attribute in attrs {
                guard available.contains(attribute) else { missing.append(attribute); continue }
                switch read(element, attribute) {
                case .missing: missing.append(attribute)
                case .null: nulls.append(attribute)
                case .failure(let code) where code == AXError.attributeUnsupported.rawValue: unsupported.append(attribute)
                case .failure(let code): attrErrors.append(AttributeError(attribute: attribute, errorCode: code))
                case .value(let value): values[attribute] = value
                }
            }
            for failure in attrErrors {
                errors.append("\(id): AX \(failure.attribute) read failed (\(failure.errorCode))")
            }
            let frame = frame(from: values)
            let screenRects = NSScreen.screens.map(\.frame)
            let offscreen: Bool? = frame.map { rect in screenRects.allSatisfy { !$0.intersects(rect) } }
            let nodeIndex = nodes.count
            nodes.append(Node(
                id: id, parentID: parentID,
                role: stringValue(values["AXRole"]), subrole: stringValue(values["AXSubrole"]),
                title: stringValue(values["AXTitle"]), description: stringValue(values["AXDescription"]),
                value: stringValue(values["AXValue"]), minimumValue: numberValue(values["AXMinValue"]),
                maximumValue: numberValue(values["AXMaxValue"]), help: stringValue(values["AXHelp"]),
                identifier: stringValue(values["AXIdentifier"]),
                framePt: frame.map { Rect(x: $0.minX, y: $0.minY, width: $0.width, height: $0.height) },
                enabled: boolValue(values["AXEnabled"]), focused: boolValue(values["AXFocused"]),
                selected: boolValue(values["AXSelected"]), offscreen: offscreen,
                // LINE can omit AXWindowNumber. Use the existing exact-ID
                // reader for window nodes while retaining the raw missing attribute.
                windowNumber: (values["AXWindowNumber"] as? NSNumber)?.uint32Value
                    ?? (stringValue(values["AXRole"]) == "AXWindow" ? AXDriver.windowNumber(of: element) : nil), children: [],
                missingAttributes: missing.sorted(), nullAttributes: nulls.sorted(),
                unsupportedAttributes: unsupported.sorted(), attributeErrors: attrErrors
            ))
            guard available.contains("AXChildren") else { return id }
            if nulls.contains("AXChildren") { return id }
            guard let childValue = values["AXChildren"] else {
                errors.append("\(id): AXChildren unavailable; child traversal is incomplete")
                return id
            }
            guard CFGetTypeID(childValue) == CFArrayGetTypeID() else {
                errors.append("\(id): AXChildren did not return a child array")
                return id
            }
            guard let childElements = childValue as? [AXUIElement] else {
                errors.append("\(id): AXChildren contains unreadable child references")
                return id
            }
            var childIDs: [String] = []
            for child in childElements {
                if nodes.count >= limits.maxNodes { truncationReasons.append("nodeLimit"); break }
                if depth + 1 > limits.maxDepth { truncationReasons.append("depthLimit"); break }
                let childID = traverse(child, parentID: id, depth: depth + 1)
                if !childID.isEmpty { childIDs.append(childID) }
            }
            let old = nodes[nodeIndex]
            nodes[nodeIndex] = Node(id: old.id, parentID: old.parentID, role: old.role, subrole: old.subrole,
                                    title: old.title, description: old.description, value: old.value,
                                    minimumValue: old.minimumValue, maximumValue: old.maximumValue, help: old.help,
                                    identifier: old.identifier, framePt: old.framePt, enabled: old.enabled,
                                    focused: old.focused, selected: old.selected, offscreen: old.offscreen,
                                    windowNumber: old.windowNumber,
                                    children: childIDs, missingAttributes: old.missingAttributes,
                                    nullAttributes: old.nullAttributes, unsupportedAttributes: old.unsupportedAttributes,
                                    attributeErrors: old.attributeErrors)
            return id
        }

        enum Read { case value(CFTypeRef), missing, null, failure(Int32) }

        func read(_ element: AXUIElement, _ name: String) -> Read {
            guard DispatchTime.now().uptimeNanoseconds < deadlineNanos else {
                return .failure(AXError.cannotComplete.rawValue)
            }
            AXUIElementSetMessagingTimeout(element, 0.25)
            var value: CFTypeRef?
            let status = AXUIElementCopyAttributeValue(element, name as CFString, &value)
            if status == .noValue { return .null }
            guard status == .success else { return .failure(status.rawValue) }
            guard let value else { return .null }
            if CFGetTypeID(value) == CFNullGetTypeID() { return .null }
            return .value(value)
        }

        mutating func string(_ element: AXUIElement, _ attribute: String) -> String? {
            switch read(element, attribute) {
            case .value(let value): return stringValue(value)
            case .failure(let code) where code != AXError.attributeUnsupported.rawValue:
                errors.append("window \(attribute) read failed (\(code))")
                return nil
            case .missing, .null, .failure: return nil
            }
        }

        func bool(_ element: AXUIElement, _ attribute: String) -> Bool? {
            if case .value(let value) = read(element, attribute) { return boolValue(value) }
            return nil
        }

        func uint32(_ element: AXUIElement, _ attribute: String) -> UInt32? {
            if case .value(let value) = read(element, attribute), let number = value as? NSNumber { return number.uint32Value }
            return nil
        }

        func rect(_ element: AXUIElement) -> CGRect? {
            let position = read(element, "AXPosition")
            let size = read(element, "AXSize")
            guard case .value(let positionValue) = position,
                  case .value(let sizeValue) = size else { return nil }
            return Self.rect(position: positionValue, size: sizeValue)
        }

        func frame(from values: [String: CFTypeRef]) -> CGRect? {
            guard let position = values["AXPosition"], let size = values["AXSize"] else { return nil }
            return Self.rect(position: position, size: size)
        }

        static func rect(position: CFTypeRef, size: CFTypeRef) -> CGRect? {
            guard CFGetTypeID(position) == AXValueGetTypeID(), CFGetTypeID(size) == AXValueGetTypeID() else { return nil }
            var origin = CGPoint.zero
            var dimensions = CGSize.zero
            guard AXValueGetValue(unsafeBitCast(position, to: AXValue.self), .cgPoint, &origin),
                  AXValueGetValue(unsafeBitCast(size, to: AXValue.self), .cgSize, &dimensions),
                  origin.x.isFinite, origin.y.isFinite, dimensions.width.isFinite, dimensions.height.isFinite,
                  dimensions.width >= 0, dimensions.height >= 0 else { return nil }
            return CGRect(origin: origin, size: dimensions)
        }

        mutating func stringValue(_ value: CFTypeRef?) -> String? {
            guard let value else { return nil }
            let raw: String?
            if let string = value as? String { raw = string }
            else if let number = value as? NSNumber { raw = number.stringValue }
            else { raw = nil }
            guard let raw else { return nil }
            let bytes = Array(raw.utf8)
            guard bytes.count > limits.maxStringBytes else { return raw }
            truncationReasons.append("stringLimit")
            return String(decoding: bytes.prefix(limits.maxStringBytes), as: UTF8.self)
        }

        func numberValue(_ value: CFTypeRef?) -> Double? {
            guard let number=value as? NSNumber else { return nil }
            guard CFGetTypeID(number) != CFBooleanGetTypeID() else { return nil }
            let result=number.doubleValue
            return result.isFinite ? result : nil
        }

        func boolValue(_ value: CFTypeRef?) -> Bool? {
            (value as? NSNumber)?.boolValue
        }

        struct CGEntry {
            let number: UInt32
            let ownerPID: Int32
            let layer: Int
            let frame: CGRect
            let onScreen: Bool
        }

        static func cgWindowEntries(pid: Int32) -> [CGEntry] {
            guard let raw = CGWindowListCopyWindowInfo([.optionAll, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else { return [] }
            return raw.compactMap { item in
                guard (item[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid,
                      let number = (item[kCGWindowNumber as String] as? NSNumber)?.uint32Value,
                      let layer = (item[kCGWindowLayer as String] as? NSNumber)?.intValue,
                      let bounds = item[kCGWindowBounds as String] as? [String: Any] else { return nil }
                var frame = CGRect.zero
                guard CGRectMakeWithDictionaryRepresentation(bounds as CFDictionary, &frame) else { return nil }
                return CGEntry(number: number, ownerPID: pid, layer: layer, frame: frame,
                               onScreen: (item[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue ?? false)
            }
        }

        static func activeDisplays() -> [Display] {
            var count: UInt32 = 0
            guard CGGetActiveDisplayList(0, nil, &count) == .success, count > 0 else { return [] }
            var ids = Array(repeating: CGDirectDisplayID(0), count: Int(count))
            guard CGGetActiveDisplayList(count, &ids, &count) == .success else { return [] }
            return ids.prefix(Int(count)).map { id in
                let bounds = CGDisplayBounds(id)
                let scale = bounds.width > 0 ? Double(CGDisplayPixelsWide(id)) / bounds.width : 0
                return Display(displayID: id,
                               boundsPt: Rect(x: bounds.minX, y: bounds.minY, width: bounds.width, height: bounds.height),
                               backingScale: scale)
            }
        }

        static func onScreenWindowInventory(truncationReasons: inout [String], available: inout Bool) -> [OnScreenWindow] {
            guard let raw = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else {
                return []
            }
            available = true
            let limit = 4_096
            if raw.count > limit { truncationReasons.append("onScreenWindowLimit") }
            return raw.prefix(limit).enumerated().map { index, item in
                let owner = (item[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value
                let number = (item[kCGWindowNumber as String] as? NSNumber)?.uint32Value
                let layer = (item[kCGWindowLayer as String] as? NSNumber)?.intValue
                let alpha = (item[kCGWindowAlpha as String] as? NSNumber)?.doubleValue
                let onScreen = (item[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue
                let bounds = (item[kCGWindowBounds as String] as? [String: Any]).flatMap { dictionary -> CGRect? in
                    var rect = CGRect.zero
                    return CGRectMakeWithDictionaryRepresentation(dictionary as CFDictionary, &rect) ? rect : nil
                }
                return OnScreenWindow(
                    ownerPID: owner, windowNumber: number, layer: layer,
                    boundsPt: bounds.map { Rect(x: $0.minX, y: $0.minY, width: $0.width, height: $0.height) },
                    alpha: alpha, isOnScreen: onScreen, orderFrontToBack: index
                )
            }
        }

        mutating func loadVisual() throws -> Visual? {
            guard let imageURL, let expected = imageSHA256 else { return nil }
            let standardized = imageURL.standardizedFileURL
            let projectRoot = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            let evidenceRoots = [
                "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/evidence",
                "harness-development/line-two-album-pilot-20261014/private"
            ].map { projectRoot.appendingPathComponent($0, isDirectory: true).standardizedFileURL.path + "/" }
            guard ["png", "jpg", "jpeg"].contains(standardized.pathExtension.lowercased()),
                  evidenceRoots.contains(where: { standardized.path.hasPrefix($0) }) else {
                throw CaptureError.invalidImageBinding
            }
            try Self.rejectSymlinkComponents(standardized)
            let data = try Self.readRegularNoFollow(standardized, byteLimit: 128 * 1_024 * 1_024)
            guard expected.count == 64,
                  expected.allSatisfy({ $0.isHexDigit }),
                  EvidenceIO.sha256Hex(data).caseInsensitiveCompare(expected) == .orderedSame,
                  let source = CGImageSourceCreateWithData(data as CFData, nil),
                  let image = CGImageSourceCreateImageAtIndex(source, 0, nil),
                  image.width > 0, image.height > 0,
                  image.width <= 12_000, image.height <= 12_000,
                  image.width * image.height <= 80_000_000 else {
                throw CaptureError.invalidImageBinding
            }
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.recognitionLanguages = ["zh-Hant", "en-US"]
            request.usesLanguageCorrection = false
            try VNImageRequestHandler(cgImage: image).perform([request])
            let ocr = (request.results ?? []).compactMap { observation -> OCRItem? in
                let candidates = observation.topCandidates(2)
                guard let best = candidates.first else { return nil }
                let box = observation.boundingBox
                return OCRItem(text: best.string, confidence: Double(best.confidence),
                               bounds: Rect(x: Double(box.minX) * Double(image.width),
                                            y: Double(1 - box.maxY) * Double(image.height),
                                            width: Double(box.width) * Double(image.width),
                                            height: Double(box.height) * Double(image.height)),
                               candidateCount: candidates.count)
            }
            let dots = try EllipsisPixelDetector.detect(image: image).map {
                VisualDot(x: $0.center.x, y: $0.center.y, area: $0.area, width: $0.width, height: $0.height)
            }
            return Visual(sourceSHA256: expected.lowercased(), width: image.width, height: image.height,
                          recognitionLanguages: request.recognitionLanguages, ocr: ocr, ellipsisComponents: dots)
        }

        static func rejectSymlinkComponents(_ url: URL) throws {
            var current = URL(fileURLWithPath: "/", isDirectory: true)
            for component in url.pathComponents.dropFirst() {
                current.appendPathComponent(component)
                var info = stat()
                guard lstat(current.path, &info) == 0, (info.st_mode & S_IFMT) != S_IFLNK else {
                    throw CaptureError.invalidImageBinding
                }
            }
        }

        static func readRegularNoFollow(_ url: URL, byteLimit: Int) throws -> Data {
            let descriptor = open(url.path, O_RDONLY | O_NOFOLLOW)
            guard descriptor >= 0 else { throw CaptureError.invalidImageBinding }
            defer { _ = close(descriptor) }
            var before = stat()
            guard fstat(descriptor, &before) == 0,
                  (before.st_mode & S_IFMT) == S_IFREG,
                  before.st_size > 0, before.st_size <= off_t(byteLimit) else {
                throw CaptureError.invalidImageBinding
            }
            let expectedSize = Int(before.st_size)
            var data = Data(count: expectedSize)
            let readComplete = data.withUnsafeMutableBytes { buffer -> Bool in
                guard let base = buffer.baseAddress else { return false }
                var offset = 0
                while offset < expectedSize {
                    let count = pread(descriptor, base.advanced(by: offset), expectedSize - offset, off_t(offset))
                    guard count > 0 else { return false }
                    offset += count
                }
                var extra = UInt8(0)
                return pread(descriptor, &extra, 1, off_t(expectedSize)) == 0
            }
            var after = stat()
            guard readComplete, fstat(descriptor, &after) == 0,
                  before.st_dev == after.st_dev, before.st_ino == after.st_ino,
                  before.st_size == after.st_size,
                  before.st_mtimespec.tv_sec == after.st_mtimespec.tv_sec,
                  before.st_mtimespec.tv_nsec == after.st_mtimespec.tv_nsec else {
                throw CaptureError.invalidImageBinding
            }
            return data
        }
    }
}
