import AppKit
import CoreGraphics
import Foundation
import ScreenCaptureKit

// MARK: - Production observation boundary (C2)
//
// Every method is a thin binding of an already reviewed sensor helper to the
// `ObservationSource` seam. The epoch authority is the run's evidence-derived
// authority, so a new process continues after the artifacts instead of
// reissuing an epoch that already names evidence.

public enum ProductionObservationSourceError: Error, Equatable, CustomStringConvertible {
    case windowHandleUnavailable(UInt32)
    case processInstanceUnavailable(Int32)
    case axIdentityUnavailable(Int32, UInt32)
    case epochAuthorityStopped(String)

    public var description: String {
        switch self {
        case let .windowHandleUnavailable(windowID):
            return "windowHandleUnavailable(\(windowID))"
        case let .processInstanceUnavailable(pid):
            return "processInstanceUnavailable(\(pid))"
        case let .axIdentityUnavailable(pid, windowID):
            return "axIdentityUnavailable(\(pid), \(windowID))"
        case let .epochAuthorityStopped(detail):
            return "epochAuthorityStopped(\(detail))"
        }
    }
}

public struct ProductionObservationSource: ObservationSource {
    public let target: ObservationTarget
    public let ruleBook: CaptureGeometryRuleBook

    private let epochAuthority: RunEpochAuthority
    private let signingIdentity: @Sendable (Int32) -> String?
    private let clock: @Sendable () -> UInt64
    private let enumerate: @Sendable () async throws -> [SCWindowSnapshot]
    private let cgInventoryProvider: @Sendable () -> [CGWindowSnapshot]

    public init(
        target: ObservationTarget,
        evidenceRunDirectory: URL,
        ruleBook: CaptureGeometryRuleBook,
        signingIdentity: @escaping @Sendable (Int32) -> String?,
        clock: @escaping @Sendable () -> UInt64 = { DispatchTime.now().uptimeNanoseconds },
        enumerate: @escaping @Sendable () async throws -> [SCWindowSnapshot] = {
            WindowSensor.snapshots(from: try await WindowSensor.shareableContent(onScreenWindowsOnly: true))
        },
        cgInventoryProvider: @escaping @Sendable () -> [CGWindowSnapshot] = {
            CGWindowInventory.onScreenWindows()
        }
    ) throws {
        self.target = target
        self.ruleBook = ruleBook
        self.epochAuthority = try RunEpochAuthority(evidenceRunDirectory: evidenceRunDirectory)
        self.signingIdentity = signingIdentity
        self.clock = clock
        self.enumerate = enumerate
        self.cgInventoryProvider = cgInventoryProvider
    }

    public func enumerateWindows() async throws -> [SCWindowSnapshot] {
        try await enumerate()
    }

    public func cgInventory() -> [CGWindowSnapshot] {
        cgInventoryProvider()
    }

    public func captureTarget(
        window: SCWindowSnapshot,
        includedWindows: [SCWindowSnapshot],
        configuration: CaptureConfiguration,
        geometryState: CaptureGeometryState,
        epoch: UInt64
    ) async throws -> ObservationCapturedImage {
        if let refusal = epochAuthority.refusal {
            throw ProductionObservationSourceError.epochAuthorityStopped(refusal)
        }
        guard epoch > 0 else {
            throw ProductionObservationSourceError.epochAuthorityStopped(
                epochAuthority.refusal ?? "the run's epoch authority issued no epoch"
            )
        }
        let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
        guard let handle = content.windows.first(where: { $0.windowID == window.windowID }) else {
            throw ProductionObservationSourceError.windowHandleUnavailable(window.windowID)
        }
        let service = await FrameCaptureService(ruleBook: ruleBook)
        return try await service.captureRetained(
            window: handle,
            configuration: configuration,
            includedWindows: includedWindows,
            state: geometryState,
            identityTemplate: nil,
            epoch: epoch
        )
    }

    /// Binds the AX read to the exact target window (plan C3): the CGWindowID
    /// when the accessibility element reports one, otherwise a unique frame
    /// match against the same CG inventory entry. Never "the first AX window".
    public func readAXIdentity(pid: Int32, windowID: UInt32) throws -> AXIdentityRead {
        let cgBounds = cgInventoryProvider().first(where: { $0.windowNumber == windowID })?.frame
        let descriptors = AXDriver.windows(ofApp: pid).map { element in
            AXWindowDescriptor(
                windowNumber: AXDriver.windowNumber(of: element),
                frame: AXDriver.frame(of: element),
                role: AXDriver.role(of: element),
                subrole: AXDriver.subrole(of: element),
                title: AXDriver.title(of: element)
            )
        }
        do {
            return try AXWindowIdentitySelector.select(
                targetWindowID: windowID,
                cgBounds: cgBounds,
                descriptors: descriptors
            )
        } catch {
            throw ProductionObservationSourceError.axIdentityUnavailable(pid, windowID)
        }
    }

    public func processInstance(pid: Int32) throws -> ProcessInstanceID {
        guard let instance = ProcessInstanceID.current(pid: pid) else {
            throw ProductionObservationSourceError.processInstanceUnavailable(pid)
        }
        return instance
    }

    public func signingIdentity(pid: Int32) throws -> String? {
        signingIdentity(pid)
    }

    public func nextEpoch() -> UInt64 {
        epochAuthority.nextEpoch()
    }

    public func monotonicNanos() -> UInt64 {
        clock()
    }
}
