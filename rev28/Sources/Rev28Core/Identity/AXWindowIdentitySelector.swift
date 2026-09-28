import CoreGraphics
import Foundation

// MARK: - AX window identity binding (plan C3/C6)
//
// An AX read is only evidence about *this* capture window when it is
// affirmatively tied to the window under observation. Selecting the first AX
// window of the process (or any window that merely has a non-empty role) is
// not a binding. The selector below is a pure decision over observable
// descriptors so it can be unit-tested without a live accessibility server:
//
//  1. Prefer the exact CGWindowID, when the AX element reports one.
//  2. Otherwise fall back to frame geometry against the CG entry, and only
//     when exactly one AX window matches within tolerance.
//  3. Anything else (no match, several matches, unreadable fields) refuses.
public enum AXWindowMatchMethod: String, Codable, Sendable {
    case windowNumber
    case frameGeometry
}

public struct AXWindowDescriptor: Equatable, Sendable {
    public let windowNumber: UInt32?
    public let frame: CGRect?
    public let role: String?
    public let subrole: String?
    public let title: String?

    public init(
        windowNumber: UInt32?,
        frame: CGRect?,
        role: String?,
        subrole: String?,
        title: String?
    ) {
        self.windowNumber = windowNumber
        self.frame = frame
        self.role = role
        self.subrole = subrole
        self.title = title
    }
}

public enum AXWindowIdentityError: Error, Equatable, CustomStringConvertible {
    case targetWindowNotAddressable(UInt32)
    case ambiguousAXWindowMatch(UInt32, count: Int)

    public var description: String {
        switch self {
        case let .targetWindowNotAddressable(windowID):
            return "targetWindowNotAddressable(\(windowID))"
        case let .ambiguousAXWindowMatch(windowID, count):
            return "ambiguousAXWindowMatch(\(windowID), count=\(count))"
        }
    }
}

public enum AXWindowIdentitySelector {
    public static let frameTolerancePt: CGFloat = 0.5

    public static func select(
        targetWindowID: UInt32,
        cgBounds: CGRect?,
        descriptors: [AXWindowDescriptor],
        frameTolerancePt: CGFloat = AXWindowIdentitySelector.frameTolerancePt
    ) throws -> AXIdentityRead {
        let byNumber = descriptors.filter { $0.windowNumber == targetWindowID }
        if byNumber.count > 1 {
            throw AXWindowIdentityError.ambiguousAXWindowMatch(targetWindowID, count: byNumber.count)
        }
        if let element = byNumber.first {
            return AXIdentityRead(
                role: element.role,
                subrole: element.subrole,
                title: element.title,
                matchMethod: .windowNumber
            )
        }
        guard let cgBounds else {
            throw AXWindowIdentityError.targetWindowNotAddressable(targetWindowID)
        }
        let byFrame = descriptors.filter { descriptor in
            guard let frame = descriptor.frame else { return false }
            return abs(frame.origin.x - cgBounds.origin.x) <= frameTolerancePt
                && abs(frame.origin.y - cgBounds.origin.y) <= frameTolerancePt
                && abs(frame.width - cgBounds.width) <= frameTolerancePt
                && abs(frame.height - cgBounds.height) <= frameTolerancePt
        }
        guard byFrame.count == 1, let element = byFrame.first else {
            throw AXWindowIdentityError.targetWindowNotAddressable(targetWindowID)
        }
        return AXIdentityRead(
            role: element.role,
            subrole: element.subrole,
            title: element.title,
            matchMethod: .frameGeometry
        )
    }
}
