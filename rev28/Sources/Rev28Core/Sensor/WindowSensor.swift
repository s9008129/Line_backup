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
