import Foundation
import Rev28Core
import AppKit
import ApplicationServices

// rev28ctl — the W2 harness driver (plan §SYNTHETIC_HARNESS_CALIBRATION_PLAN).
//
//   rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>]
//   rev28ctl restart-child --ledger <path> --head-file <path> --point <name>

let arguments = CommandLine.arguments

func optionValue(_ name: String) -> String? {
    guard let index = arguments.firstIndex(of: name), index + 1 < arguments.count else { return nil }
    return arguments[index + 1]
}

if arguments.count >= 2, arguments[1] == "harness-calibrate" {
    guard let evidencePath = optionValue("--evidence") else {
        FileHandle.standardError.write(Data("harness-calibrate: --evidence is required\n".utf8))
        exit(64)
    }
    let binaryDirectory = optionValue("--binary-dir").map { URL(fileURLWithPath: $0) }
        ?? Bundle.main.executableURL?.deletingLastPathComponent()
        ?? URL(fileURLWithPath: ".")
    let items: Set<Int> = {
        guard let value = optionValue("--items") else { return [] }
        return Set(value.split(separator: ",").compactMap { Int($0.trimmingCharacters(in: .whitespaces)) })
    }()
    let evidenceBase = URL(fileURLWithPath: evidencePath)
    do {
        let run = try EvidenceRun(evidenceBase: evidenceBase)
        let maxCells = optionValue("--max-cells").flatMap { Int($0) }
        let options = CalibrationOptions(evidenceBase: evidenceBase, binaryDirectory: binaryDirectory, items: items, maxCells: maxCells)
        let driver = HarnessCalibrationDriver(options: options, run: run)
        FileHandle.standardOutput.write(Data("runID=\(run.runID) evidence=\(run.root.path)\n".utf8))
        let code = await driver.runAll()
        exit(code)
    } catch {
        FileHandle.standardError.write(Data("harness-calibrate failed: \(error)\n".utf8))
        exit(70)
    }
}

if arguments.count >= 2, arguments[1] == "restart-child" {
    let code = RestartFixture.runChild(arguments: Array(arguments.dropFirst(2)))
    exit(code)
}

if arguments.count >= 2, ["live-preflight", "live-execute"].contains(arguments[1]) {
    let command = arguments[1]
    guard ProcessInfo.processInfo.environment["CI"] == nil else {
        FileHandle.standardError.write(Data("\(command): live execution is disabled in CI\n".utf8))
        exit(77)
    }
    guard let configPath = optionValue("--config"),
          let authorizationPath = optionValue("--one-shot-authorization") else {
        FileHandle.standardError.write(Data("\(command): requires --config and --one-shot-authorization; CI never dispatches\n".utf8))
        exit(64)
    }
    do {
        struct OneShot: Decodable {
            let runID: String
            let planSHA256: String
            let reviewedImplementationSHA256: String
        }
        let configURL = URL(fileURLWithPath: configPath).standardizedFileURL
        let authURL = URL(fileURLWithPath: authorizationPath).standardizedFileURL
        let config = try JSONDecoder().decode(LiveRunConfig.self, from: Data(contentsOf: configURL))
        let oneShot = try JSONDecoder().decode(OneShot.self, from: Data(contentsOf: authURL))
        let auth = config.authorization
        guard oneShot.runID == auth.runID,
              oneShot.planSHA256 == auth.planSHA256,
              oneShot.reviewedImplementationSHA256 == auth.reviewedImplementationSHA256,
              EvidenceIO.sha256Hex(try Data(contentsOf: URL(fileURLWithPath: config.planPath))) == auth.planSHA256,
              try ReviewedImplementationDigest.compute(repositoryRoot: URL(fileURLWithPath: config.repositoryRoot)) == auth.reviewedImplementationSHA256 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("one-shot authorization or plan digest mismatch")
        }
        guard ProcessIdentity.bundleID(pid: config.targetPID) == config.targetBundleID,
              config.targetBundleID == "jp.naver.line.mac" else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target process is not the expected LINE application")
        }
        guard AXIsProcessTrusted() else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("this process does not hold accessibility trust")
        }
        let inputs = try LiveCompositionBuilder.inputs(from: config)
        let composition = try await LiveCompositionBuilder.build(inputs: inputs)
        defer { composition.journal.stop() }

        if command == "live-preflight" {
            // Plan C4: preflight never consumes or renames the one-shot
            // entitlement and must leave every irreversible counter at zero.
            guard FileManager.default.fileExists(atPath: authURL.path) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("one-shot authorization file is missing; preflight must not consume it")
            }
            let counters = composition.owner.irreversibleOperationCounts
            guard counters.saveAll == 0, counters.destinationConfirmation == 0 else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "preflight found irreversible records: saveAll=\(counters.saveAll) confirmation=\(counters.destinationConfirmation)"
                )
            }
            guard composition.owner.goalSlot?.entitlementConsumed == false else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("one-shot execution entitlement is already consumed")
            }
            guard composition.owner.isObserveOnlyResume == false else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("ledger already contains irreversible history; this run is observe-only")
            }
            let app = NSRunningApplication(processIdentifier: pid_t(config.targetPID))
            guard app?.isActive == true,
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == pid_t(config.targetPID) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("target application is not active/frontmost for a live preflight")
            }
            let baseline = try BaselineVerifier.verify(referenceFile: inputs.baselineReferenceFile)
            let drain = composition.journal.drain()
            guard drain.healthy else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("tripwire journal is not healthy for a live preflight")
            }
            FileHandle.standardOutput.write(Data(
                "preflight=passed runID=\(auth.runID) windowID=\(composition.windowID) baselineTripwire=\(baseline.nameInclusiveTripwireSHA256) tripwireHealthy=\(drain.healthy) intent.saveAll=0 attempt.saveAll=0 intent.destinationConfirmation=0 attempt.destinationConfirmation=0 entitlement=unconsumed dispatch=none\n".utf8
            ))
            exit(0)
        }

        let outcome = try await LiveExecutionEngine(owner: composition.owner, adapter: composition.adapter).run()
        switch outcome {
        case let .contentVerified(verification):
            FileHandle.standardOutput.write(Data("live-execute=contentVerified runID=\(auth.runID) files=\(verification.fileCount) bytes=\(verification.totalBytes) outcome=\(verification.outcome.rawValue)\n".utf8))
        case let .observeOnlyResume(state):
            FileHandle.standardOutput.write(Data("live-execute=observeOnlyResume runID=\(auth.runID) state=\(state.map(\.rawValue) ?? "NONE") dispatch=none\n".utf8))
        case let .contentRejected(verification):
            FileHandle.standardError.write(Data("live-execute=contentRejected runID=\(auth.runID) detail=\(verification.detail)\n".utf8))
            exit(78)
        }
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("\(command) refused: \(error)\n".utf8))
        exit(77)
    }
}

FileHandle.standardError.write(Data("usage: rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>] | restart-child --ledger <path> --head-file <path> --point <name> | live-preflight|live-execute --config <json> --one-shot-authorization <json>\n".utf8))
exit(64)

private enum ReviewedImplementationDigest {
    static func compute(repositoryRoot: URL) throws -> String {
        let sourceRoots = [
            repositoryRoot.appendingPathComponent("rev28/Sources/Rev28Core"),
            repositoryRoot.appendingPathComponent("rev28/Sources/rev28ctl"),
        ]
        var paths: [URL] = []
        for root in sourceRoots {
            guard FileManager.default.fileExists(atPath: root.path),
                  let enumerator = FileManager.default.enumerator(at: root, includingPropertiesForKeys: [.isRegularFileKey]) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition("implementation source tree unavailable")
            }
            while let url = enumerator.nextObject() as? URL {
                guard url.pathExtension == "swift" else { continue }
                paths.append(url)
            }
        }
        paths.sort { $0.path < $1.path }
        var material = Data()
        for url in paths {
            let relative = String(url.path.dropFirst(repositoryRoot.path.count + 1))
            material.append(Data(relative.utf8))
            material.append(0)
            material.append(try Data(contentsOf: url))
            material.append(0)
        }
        return EvidenceIO.sha256Hex(material)
    }
}
