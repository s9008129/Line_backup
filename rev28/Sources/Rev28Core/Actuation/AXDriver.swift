import ApplicationServices
import CoreGraphics
import Foundation

// MARK: - Accessibility plane (plan §ARCHITECTURE §6)
//
// AX reads: role, subrole, title, children, actions, focused element, window
// ownership (pid of the element). AX writes are attempted only against a
// uniquely identified element bound to the verified surface.

/// One flattened AX node fact set. Deliberately a value snapshot: AX elements are
/// not carried across boundaries.
public struct AXNodeDump: Equatable, Codable, Sendable {
    public let depth: Int
    public let role: String?
    public let subrole: String?
    public let title: String?
    public let description: String?
    public let identifier: String?
    public let keyEquivalent: String?
    public let value: String?
    public let enabled: Bool?
    public let frame: CGRect?
    /// All string-representable attributes that exist on this node (name -> value),
    /// captured during calibration so the frozen predicate names exact attributes.
    public let attributes: [String: String]

    public init(
        depth: Int,
        role: String?,
        subrole: String?,
        title: String?,
        description: String?,
        identifier: String?,
        keyEquivalent: String?,
        value: String?,
        enabled: Bool?,
        frame: CGRect?,
        attributes: [String: String]
    ) {
        self.depth = depth
        self.role = role
        self.subrole = subrole
        self.title = title
        self.description = description
        self.identifier = identifier
        self.keyEquivalent = keyEquivalent
        self.value = value
        self.enabled = enabled
        self.frame = frame
        self.attributes = attributes
    }
}

public struct AXTreeDump: Equatable, Codable, Sendable {
    public let pid: Int32
    public let capturedAtISO8601: String
    public let maxDepth: Int
    public let nodeCount: Int
    public let nodes: [AXNodeDump]

    public init(pid: Int32, capturedAtISO8601: String, maxDepth: Int, nodes: [AXNodeDump]) {
        self.pid = pid
        self.capturedAtISO8601 = capturedAtISO8601
        self.maxDepth = maxDepth
        self.nodeCount = nodes.count
        self.nodes = nodes
    }
}

public enum AXDriver {
    public static func isProcessTrusted() -> Bool {
        AXIsProcessTrusted()
    }

    public static func appElement(pid: pid_t) -> AXUIElement {
        AXUIElementCreateApplication(pid)
    }

    public static func copyAttribute(_ element: AXUIElement, _ attribute: String) -> CFTypeRef? {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(element, attribute as CFString, &value)
        guard result == .success else { return nil }
        return value
    }

    public static func stringAttribute(_ element: AXUIElement, _ attribute: String) -> String? {
        copyAttribute(element, attribute) as? String
    }

    public static func boolAttribute(_ element: AXUIElement, _ attribute: String) -> Bool? {
        (copyAttribute(element, attribute) as? NSNumber)?.boolValue
    }

    public static func role(of element: AXUIElement) -> String? { stringAttribute(element, kAXRoleAttribute as String) }
    public static func subrole(of element: AXUIElement) -> String? { stringAttribute(element, kAXSubroleAttribute as String) }
    public static func title(of element: AXUIElement) -> String? { stringAttribute(element, kAXTitleAttribute as String) }
    public static func descriptionOf(of element: AXUIElement) -> String? {
        stringAttribute(element, kAXDescriptionAttribute as String)
    }
    public static func identifier(of element: AXUIElement) -> String? {
        stringAttribute(element, kAXIdentifierAttribute as String)
    }
    public static func keyEquivalent(of element: AXUIElement) -> String? {
        stringAttribute(element, "AXKeyEquivalent")
    }
    public static func isEnabled(_ element: AXUIElement) -> Bool? {
        boolAttribute(element, kAXEnabledAttribute as String)
    }

    public static func valueAsString(_ element: AXUIElement) -> String? {
        guard let raw = copyAttribute(element, kAXValueAttribute as String) else { return nil }
        if let string = raw as? String { return string }
        if let number = raw as? NSNumber { return number.stringValue }
        return nil
    }

    public static func frame(of element: AXUIElement) -> CGRect? {
        guard let positionValue = copyAttribute(element, kAXPositionAttribute as String),
              let sizeValue = copyAttribute(element, kAXSizeAttribute as String),
              CFGetTypeID(positionValue) == AXValueGetTypeID(),
              CFGetTypeID(sizeValue) == AXValueGetTypeID() else {
            return nil
        }
        var origin = CGPoint.zero
        var size = CGSize.zero
        guard AXValueGetValue(positionValue as! AXValue, .cgPoint, &origin),
              AXValueGetValue(sizeValue as! AXValue, .cgSize, &size) else {
            return nil
        }
        return CGRect(origin: origin, size: size)
    }

    public static func children(of element: AXUIElement) -> [AXUIElement] {
        guard let raw = copyAttribute(element, kAXChildrenAttribute as String) else { return [] }
        return raw as? [AXUIElement] ?? []
    }

    public static func windows(ofApp pid: pid_t) -> [AXUIElement] {
        guard let raw = copyAttribute(appElement(pid: pid), kAXWindowsAttribute as String) else { return [] }
        return raw as? [AXUIElement] ?? []
    }

    public static func focusedWindow(ofApp pid: pid_t) -> AXUIElement? {
        guard let raw = copyAttribute(appElement(pid: pid), kAXFocusedWindowAttribute as String),
              CFGetTypeID(raw) == AXUIElementGetTypeID() else {
            return nil
        }
        return (raw as! AXUIElement)
    }

    /// Depth-limited pre-order dump of an AX element subtree.
    public static func dump(
        element: AXUIElement,
        pid: Int32,
        maxDepth: Int = 8,
        maxNodes: Int = 600
    ) -> AXTreeDump {
        var nodes: [AXNodeDump] = []
        var stack: [(AXUIElement, Int)] = [(element, 0)]
        while let (current, depth) = stack.popLast() {
            if nodes.count >= maxNodes { break }
            nodes.append(nodeDump(current, depth: depth))
            if depth < maxDepth {
                for child in children(of: current).reversed() {
                    stack.append((child, depth + 1))
                }
            }
        }
        return AXTreeDump(
            pid: pid,
            capturedAtISO8601: EvidenceIO.iso8601(),
            maxDepth: maxDepth,
            nodes: nodes
        )
    }

    public static func nodeDump(_ element: AXUIElement, depth: Int) -> AXNodeDump {
        var attributes: [String: String] = [:]
        for name in attributeNames(of: element) {
            guard let raw = copyAttribute(element, name) else { continue }
            if let string = raw as? String {
                attributes[name] = string
            } else if let number = raw as? NSNumber {
                attributes[name] = number.stringValue
            }
        }
        return AXNodeDump(
            depth: depth,
            role: role(of: element),
            subrole: subrole(of: element),
            title: title(of: element),
            description: descriptionOf(of: element),
            identifier: identifier(of: element),
            keyEquivalent: keyEquivalent(of: element),
            value: valueAsString(element),
            enabled: isEnabled(element),
            frame: frame(of: element),
            attributes: attributes
        )
    }

    public static func attributeNames(of element: AXUIElement) -> [String] {
        var names: CFArray?
        let result = AXUIElementCopyAttributeNames(element, &names)
        guard result == .success, let list = names as? [String] else { return [] }
        return list
    }

    /// Performs exactly one `AXPress` on the given element.
    @discardableResult
    public static func press(_ element: AXUIElement) -> Bool {
        AXUIElementPerformAction(element, kAXPressAction as CFString) == .success
    }

    /// First descendant (pre-order, including self) matching a predicate.
    public static func firstDescendant(
        of element: AXUIElement,
        maxDepth: Int = 8,
        matching predicate: (AXUIElement) -> Bool
    ) -> AXUIElement? {
        var stack: [(AXUIElement, Int)] = [(element, 0)]
        var visited = 0
        while let (current, depth) = stack.popLast() {
            visited += 1
            if visited > 1200 { break }
            if predicate(current) { return current }
            if depth < maxDepth {
                for child in children(of: current).reversed() {
                    stack.append((child, depth + 1))
                }
            }
        }
        return nil
    }

    public static func allDescendants(
        of element: AXUIElement,
        maxDepth: Int = 8,
        matching predicate: (AXUIElement) -> Bool
    ) -> [AXUIElement] {
        var matches: [AXUIElement] = []
        var stack: [(AXUIElement, Int)] = [(element, 0)]
        var visited = 0
        while let (current, depth) = stack.popLast() {
            visited += 1
            if visited > 2000 { break }
            if predicate(current) { matches.append(current) }
            if depth < maxDepth {
                for child in children(of: current).reversed() {
                    stack.append((child, depth + 1))
                }
            }
        }
        return matches
    }
}
