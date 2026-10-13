import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
import Rev28Core

/// Passive LINE-only command. It constructs no transaction owner or actuator.
@MainActor
enum PassiveCaptureDiagnostic {
    struct UsageError: Error {}
    static let usage = "rev28ctl capture-diagnostic --project-root <explicit-root> --output <existing-empty-root/harness-development/native-diagnostics/directory> --rulebook <project-file> --bundle-id jp.naver.line.mac --pid <fresh-pid> [--capture-profile primaryWindow|childUnion|explicitLineWindows]"

    static func run(arguments: [String]) async throws -> PassiveDiagnosticReceipt {
        let required = Set(["--project-root", "--output", "--rulebook", "--bundle-id", "--pid"])
        let values = Array(arguments.dropFirst(2))
        let allowed = required.union(["--capture-profile"])
        guard values.count == required.count * 2 || values.count == allowed.count * 2 else { throw UsageError() }
        var options: [String: String] = [:]
        for index in stride(from: 0, to: values.count, by: 2) {
            guard allowed.contains(values[index]), options[values[index]] == nil, !values[index + 1].isEmpty else { throw UsageError() }
            options[values[index]] = values[index + 1]
        }
        guard required.isSubset(of: Set(options.keys)),
              let profile = PassiveDiagnosticCaptureProfile(rawValue: options["--capture-profile"] ?? "primaryWindow"),
              let pid = Int32(options["--pid"]!), pid > 0 else { throw UsageError() }
        guard options["--bundle-id"] == PassiveNativeDiagnostic.lineBundleID else { throw PassiveDiagnosticError.refused("only LINE may be observed") }
        // All paths and the exclusive claim precede native process/permission reads.
        let output = try PassiveDiagnosticOutput(projectRoot: options["--project-root"]!, output: options["--output"]!, rulebook: options["--rulebook"]!)
        guard ProcessInfo.processInfo.environment["CI"] == nil else { throw PassiveDiagnosticError.refused("native observation disabled in CI") }
        let app = NSRunningApplication(processIdentifier: pid)
        try PassiveNativeDiagnostic.validateTarget(bundleID: options["--bundle-id"]!, pid: pid,
            observedBundleID: app?.bundleIdentifier, observedPID: app.map { Int32($0.processIdentifier) })
        guard AXIsProcessTrusted(), CGPreflightScreenCaptureAccess() else {
            throw PassiveDiagnosticError.refused("AX and screen capture preflight permissions required; no permission request is made")
        }
        guard let originalProcess = ProcessInstanceID.current(pid: pid) else { throw PassiveDiagnosticError.refused("fresh LINE process unavailable") }
        let provenance = try sourceProvenance(root: output.projectRoot)
        try output.assertUnchanged()
        let first = WindowSensor.snapshots(from: try await WindowSensor.shareableContent(onScreenWindowsOnly: true))
        let firstTargets = WindowSensor.mainWindowCandidates(in: first, bundleID: PassiveNativeDiagnostic.lineBundleID, pid: pid)
        guard firstTargets.count == 1 else { throw ObservationRefusal.targetWindowNotUnique(found: firstTargets.count) }
        let target = ObservationTarget(bundleID: PassiveNativeDiagnostic.lineBundleID, pid: pid)
        let firstIncluded = try profile.selectedWindows(in: first, target: target)
        let wasActive = app?.isActive == true
        try await Task.sleep(nanoseconds: 250_000_000)
        let second = WindowSensor.snapshots(from: try await WindowSensor.shareableContent(onScreenWindowsOnly: true))
        let secondTargets = WindowSensor.mainWindowCandidates(in: second, bundleID: PassiveNativeDiagnostic.lineBundleID, pid: pid)
        guard secondTargets.count == 1 else { throw ObservationRefusal.targetWindowNotUnique(found: secondTargets.count) }
        guard let freshApp = NSRunningApplication(processIdentifier: pid),
              ProcessInstanceID.current(pid: pid) == originalProcess else { throw PassiveDiagnosticError.refused("process/window changed in settling samples") }
        try PassiveNativeDiagnostic.validateTarget(bundleID: options["--bundle-id"]!, pid: pid,
            observedBundleID: freshApp.bundleIdentifier, observedPID: Int32(freshApp.processIdentifier))
        let secondIncluded = try profile.selectedWindows(in: second, target: target)
        if profile != .primaryWindow, firstIncluded != secondIncluded {
            throw PassiveDiagnosticError.refused("child composition changed in settling samples")
        }
        let settled = firstTargets[0].windowID == secondTargets[0].windowID && firstTargets[0].frame == secondTargets[0].frame
        let secondWasActive = freshApp.isActive
        let geometryState = CaptureGeometryState(settled: settled, activated: wasActive && secondWasActive,
            includeChildWindows: profile.configuration.includeChildWindows,
            ignoreShadows: profile.configuration.ignoreShadows)
        guard output.ruleBook.rule(for: geometryState) != nil else { throw PassiveDiagnosticError.refused("no frozen rule for measured capture state") }
        let explicitBinding: ExplicitLineRequestBinding?
        if profile == .explicitLineWindows {
            try ExplicitLineCaptureSelection.validateRuleBook(output.ruleBook, state: geometryState)
            explicitBinding = ExplicitLineRequestBinding(configuration: profile.configuration, geometryState: geometryState,
                settledSelectedWindows: secondIncluded, ruleBook: output.ruleBook)
        } else { explicitBinding = nil }
        try output.assertUnchanged()
        let source = try output.makeObservationSource(target: target, signingIdentity: { ProcessIdentity.signingIdentity(pid: $0) })
        let runID = "passive-diagnostic-\(UUID().uuidString)"
        let session = NativeObservationSession(sessionID: runID + "-session", source: source, ocr: VisionOcrEngine())
        return try await output.collect(geometryState: geometryState, provenance: provenance) {
            let bundle = try await session.capture(NativeObservationRequest(runID: runID, state: .appReady, target: target,
                configuration: profile.configuration, geometryState: geometryState, localization: .none, observationBudgetNanos: 30_000_000_000,
                explicitLineRequestBinding: explicitBinding))
            try profile.validateSettlingBinding(bundle: bundle, sampledWindows: secondIncluded)
            guard bundle.process == originalProcess, bundle.window.windowID == secondTargets[0].windowID,
                  bundle.window.windowFrame == secondTargets[0].frame,
                  NSRunningApplication(processIdentifier: pid)?.isActive == secondWasActive,
                  try sourceProvenance(root: output.projectRoot) == provenance else {
                throw PassiveDiagnosticError.refused("process, settling geometry, activation or source/binary changed during collection")
            }
            return bundle
        }
    }

    private static func sourceProvenance(root: URL) throws -> PassiveDiagnosticProvenance {
        var material = Data()
        var entries: [PassiveDiagnosticFileDigest] = []
        for relative in try ReviewedImplementationDigest.manifestPaths(repositoryRoot: root) {
            let bytes = try PassiveNativeDiagnostic.readProjectRegularFile(path: root.path + "/" + relative, projectRoot: root.path)
            material.append(Data(relative.utf8)); material.append(0); material.append(bytes); material.append(0)
            entries.append(PassiveDiagnosticFileDigest(name: relative, bytes: bytes.count, sha256: EvidenceIO.sha256Hex(bytes)))
        }
        guard let executable = Bundle.main.executableURL else { throw PassiveDiagnosticError.refused("running executable unavailable") }
        let binary = try PassiveNativeDiagnostic.readProjectRegularFile(path: executable.path, projectRoot: root.path)
        return PassiveDiagnosticProvenance(implementationSHA256: EvidenceIO.sha256Hex(material), sourceFiles: entries,
            executableSHA256: EvidenceIO.sha256Hex(binary), executableBytes: binary.count)
    }
}
