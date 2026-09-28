import AppKit
import Foundation

// MARK: - Production actuation boundary (C5)
//
// Focus facts come from the live process/workspace state, and a reversible
// navigation is posted only through the gated actuator, which consumes the
// permit, re-checks live readiness/identity, and records the dispatch in the
// durable ledger before the event is posted.

public struct ProductionActuationEnvironment: ActuationEnvironment {
    public init() {}

    public func applicationActive(pid: Int32) -> Bool {
        NSRunningApplication(processIdentifier: pid_t(pid))?.isActive ?? false
    }

    public func targetFrontmost(pid: Int32) -> Bool {
        NSWorkspace.shared.frontmostApplication?.processIdentifier == pid_t(pid)
    }

    public func uptime() -> Double {
        ProcessInfo.processInfo.systemUptime
    }

    public func readinessObservation(
        identity: WindowIdentity,
        candidate: StructuralCandidate
    ) async throws -> ReadinessObservation {
        try await ReadinessObservation.captureLive(identity: identity, candidate: candidate)
    }

    public func postReversibleClick(
        permit: ReadinessPermit,
        binding: SurfaceBinding,
        owner: PersistentTransactionOwner,
        action: String,
        postHoverRevalidation: @escaping @Sendable () async throws -> Void
    ) async throws {
        try await GatedQuartzActuator.postClick(
            permit: permit,
            currentBinding: binding,
            intent: .reversible(owner, action: action),
            postHoverRevalidation: postHoverRevalidation
        )
    }
}
