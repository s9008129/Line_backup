import AppKit
import Foundation
import Rev28Core

// Real process-identity facts for the chooser ownership clauses: bundle id (if
// the process has one), code-signing identifier (ad-hoc counts as an identity on
// arm64), and the process start time from libproc.

enum ProcessIdentity {
    static func bundleID(pid: Int32) -> String? {
        NSRunningApplication(processIdentifier: pid)?.bundleIdentifier
    }

    static func signingIdentity(pid: Int32) -> String? {
        ProcessCodeIdentity.read(pid: pid)
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
