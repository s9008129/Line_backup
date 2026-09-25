import CoreGraphics
import Foundation
import ScreenCaptureKit

// MARK: - Window enumeration (ScreenCaptureKit sensor plane, plan §ARCHITECTURE §1)
//
// Enumeration produces value snapshots so callers never carry SCWindow objects
// across boundaries; selection is by bundle + pid instance + layer + live
// geometry, never by windowID alone.

/// A Sendable snapshot of one on-screen `SCWindow`.
public struct SCWindowSnapshot: Equatable, Codable, Sendable {
    public let windowID: UInt32
    public let frame: CGRect
    public let windowLayer: Int
    public let title: String?
    public let isOnScreen: Bool
    public let ownerPID: Int32?
    public let ownerBundleID: String?
    public let ownerName: String?

    public init(
        windowID: UInt32,
        frame: CGRect,
        windowLayer: Int,
        title: String?,
        isOnScreen: Bool,
        ownerPID: Int32?,
        ownerBundleID: String?,
        ownerName: String?
    ) {
        self.windowID = windowID
        self.frame = frame
        self.windowLayer = windowLayer
        self.title = title
        self.isOnScreen = isOnScreen
        self.ownerPID = ownerPID
        self.ownerBundleID = ownerBundleID
        self.ownerName = ownerName
    }
}

public enum WindowSensor {
    /// Standard enumeration: include desktop windows off, on-screen only.
    public static func shareableContent(onScreenWindowsOnly: Bool = true) async throws -> SCShareableContent {
        try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: onScreenWindowsOnly)
    }

    public static func snapshots(from content: SCShareableContent) -> [SCWindowSnapshot] {
        content.windows.map { window in
            SCWindowSnapshot(
                windowID: window.windowID,
                frame: window.frame,
                windowLayer: window.windowLayer,
                title: window.title,
                isOnScreen: window.isOnScreen,
                ownerPID: window.owningApplication.map { Int32($0.processID) },
                ownerBundleID: window.owningApplication?.bundleIdentifier,
                ownerName: window.owningApplication?.applicationName
            )
        }
    }

    /// Candidate main windows: bundle match, owning pid match, layer 0, on-screen.
    /// Multiplicity is returned to the caller so ambiguity is refused, never resolved.
    public static func mainWindowCandidates(
        in snapshots: [SCWindowSnapshot],
        bundleID: String,
        pid: Int32,
        layer: Int = 0
    ) -> [SCWindowSnapshot] {
        snapshots.filter { snapshot in
            snapshot.isOnScreen
                && snapshot.windowLayer == layer
                && snapshot.ownerBundleID == bundleID
                && snapshot.ownerPID == pid
        }
    }

    /// Child windows of the same owning application that are on-screen and whose
    /// frame intersects the main window's frame (used by union geometry captures).
    public static func childWindows(
        of main: SCWindowSnapshot,
        in snapshots: [SCWindowSnapshot]
    ) -> [SCWindowSnapshot] {
        snapshots.filter { snapshot in
            guard snapshot.isOnScreen,
                  snapshot.windowID != main.windowID,
                  snapshot.ownerPID == main.ownerPID,
                  snapshot.ownerBundleID == main.ownerBundleID else { return false }
            return snapshot.frame.intersects(main.frame)
        }
    }
}

// MARK: - CGWindowList inventory (plan §ARCHITECTURE §10: the postcondition
// observation runs against SC and CG inventories with the same identity binding).

/// A Sendable snapshot of one on-screen `CGWindowListCopyWindowInfo` entry.
public struct CGWindowSnapshot: Equatable, Codable, Sendable {
    public let windowNumber: UInt32
    public let frame: CGRect
    public let layer: Int
    public let ownerPID: Int32
    public let name: String?

    public init(windowNumber: UInt32, frame: CGRect, layer: Int, ownerPID: Int32, name: String?) {
        self.windowNumber = windowNumber
        self.frame = frame
        self.layer = layer
        self.ownerPID = ownerPID
        self.name = name
    }
}

public enum CGWindowInventory {
    /// On-screen, desktop-elements-excluded window list, ordered front-to-back as
    /// the window server reports it.
    public static func onScreenWindows() -> [CGWindowSnapshot] {
        guard let infoList = CGWindowListCopyWindowInfo(
            [.optionOnScreenOnly, .excludeDesktopElements],
            kCGNullWindowID
        ) as? [[String: Any]] else {
            return []
        }
        return infoList.compactMap { info in
            guard let number = (info[kCGWindowNumber as String] as? NSNumber)?.uint32Value,
                  let boundsDict = info[kCGWindowBounds as String] as? [String: Any],
                  let frame = CGRect(dictionaryRepresentation: boundsDict as CFDictionary),
                  let ownerPID = (info[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value else {
                return nil
            }
            let layer = (info[kCGWindowLayer as String] as? NSNumber)?.intValue ?? 0
            let name = info[kCGWindowName as String] as? String
            return CGWindowSnapshot(
                windowNumber: number,
                frame: frame,
                layer: layer,
                ownerPID: ownerPID,
                name: name
            )
        }
    }
}
