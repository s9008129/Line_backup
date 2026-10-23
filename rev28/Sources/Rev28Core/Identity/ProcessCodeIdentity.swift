import Foundation
import Security

/// Code identity of the requested process only. Unavailable target information
/// is unknown; the calling executable can never stand in for that target.
public enum ProcessCodeIdentity {
    public static func read(pid: Int32) -> String? {
        guard pid > 0 else { return nil }
        var code: SecCode?
        let attributes: [CFString: Any] = [kSecGuestAttributePid: NSNumber(value: pid)]
        guard SecCodeCopyGuestWithAttributes(nil, attributes as CFDictionary, [], &code) == errSecSuccess,
              let guest = code else { return nil }
        var staticCode: SecStaticCode?
        guard SecCodeCopyStaticCode(guest, [], &staticCode) == errSecSuccess,
              let targetCode = staticCode else { return nil }
        var information: CFDictionary?
        guard SecCodeCopySigningInformation(targetCode, SecCSFlags(rawValue: kSecCSSigningInformation), &information) == errSecSuccess,
              let info = information as? [String: Any] else { return nil }
        return identity(in: info)
    }

    static func identity(in information: [String: Any]) -> String? {
        guard let identifier = information[kSecCodeInfoIdentifier as String] as? String,
              meaningful(identifier) else { return nil }
        guard let teamValue = information[kSecCodeInfoTeamIdentifier as String] else { return identifier }
        guard let team = teamValue as? String, meaningful(team) else { return nil }
        return "\(identifier)@\(team)"
    }

    private static func meaningful(_ value: String) -> Bool {
        !value.isEmpty && value == value.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
