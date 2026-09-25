import AppKit
import Foundation
import Rev28Core
import Security

// Real process-identity facts for the chooser ownership clauses: bundle id (if
// the process has one), code-signing identifier (ad-hoc counts as an identity on
// arm64), and the process start time from libproc.

enum ProcessIdentity {
    static func bundleID(pid: Int32) -> String? {
        NSRunningApplication(processIdentifier: pid)?.bundleIdentifier
    }

    static func signingIdentity(pid: Int32) -> String? {
        var code: SecCode?
        let attributes: [CFString: Any] = [kSecGuestAttributePid: NSNumber(value: pid)]
        guard SecCodeCopyGuestWithAttributes(nil, attributes as CFDictionary, [], &code) == errSecSuccess,
              let guest = code else {
            return staticSigningIdentity()
        }
        var staticCode: SecStaticCode?
        guard SecCodeCopyStaticCode(guest, [], &staticCode) == errSecSuccess,
              let guestStatic = staticCode else {
            return staticSigningIdentity()
        }
        var information: CFDictionary?
        guard SecCodeCopySigningInformation(guestStatic, SecCSFlags(rawValue: kSecCSSigningInformation), &information) == errSecSuccess,
              let info = information as? [String: Any] else {
            return staticSigningIdentity()
        }
        if let identifier = info[kSecCodeInfoIdentifier as String] as? String {
            if let team = info[kSecCodeInfoTeamIdentifier as String] as? String {
                return "\(identifier)@\(team)"
            }
            return identifier
        }
        return staticSigningIdentity()
    }

    /// Fallback for processes whose guest code cannot be read: the driver's own
    /// static code identity (the harness binaries are its siblings).
    private static func staticSigningIdentity() -> String? {
        var staticCode: SecStaticCode?
        guard let executable = Bundle.main.executableURL ?? (CommandLine.arguments.first.map { URL(fileURLWithPath: $0) }),
              SecStaticCodeCreateWithPath(executable as CFURL, [], &staticCode) == errSecSuccess,
              let code = staticCode else {
            return nil
        }
        var information: CFDictionary?
        guard SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &information) == errSecSuccess,
              let info = information as? [String: Any] else {
            return nil
        }
        if let identifier = info[kSecCodeInfoIdentifier as String] as? String {
            if let cdhash = info[kSecCodeInfoUnique as String] as? Data {
                return "\(identifier)@\(cdhash.map { String(format: "%02x", $0) }.joined())"
            }
            return identifier
        }
        return nil
    }

    static func reading(pid: Int32) -> ChooserProcessFacts {
        let start = ProcessInstanceID.current(pid: pid)
        let startUnix: Double? = start.map { Double($0.startTimeSeconds) + Double($0.startTimeMicroseconds) / 1_000_000.0 }
        return ChooserProcessFacts(
            pid: pid,
            bundleID: bundleID(pid: pid),
            signingIdentity: signingIdentity(pid: pid),
            startTimeUnix: startUnix
        )
    }
}
