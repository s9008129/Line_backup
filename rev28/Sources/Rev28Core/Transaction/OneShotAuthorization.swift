import Foundation

/// Read-only view of the one-shot Phase B authorization.
///
/// R4 C4: Phase A / live preflight must never rename the entitlement to
/// `.consumed`. Only the durable Save All reservation arms the execution, so
/// preflight only inspects whether an earlier production run already consumed
/// the authorization and leaves the file itself untouched.
public enum OneShotAuthorizationState: Equatable, Sendable {
    case available
    case alreadyConsumed
}

public enum OneShotAuthorizationGate {
    public static func markerURL(for authorizationURL: URL) -> URL {
        authorizationURL.appendingPathExtension("consumed")
    }

    public static func inspect(authorizationURL: URL) -> OneShotAuthorizationState {
        FileManager.default.fileExists(atPath: markerURL(for: authorizationURL).path)
            ? .alreadyConsumed
            : .available
    }
}
