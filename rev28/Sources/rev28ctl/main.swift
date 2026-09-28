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
        struct LiveConfig: Decodable {
            let authorization: ImmutableRunAuthorization
            let targetBundleID: String
            let targetPID: Int32
            let ledgerPath: String
            let planPath: String
            let repositoryRoot: String
        }
        struct OneShot: Decodable {
            let runID: String
            let planSHA256: String
            let reviewedImplementationSHA256: String
        }
        let configURL = URL(fileURLWithPath: configPath).standardizedFileURL
        let authURL = URL(fileURLWithPath: authorizationPath).standardizedFileURL
        let config = try JSONDecoder().decode(LiveConfig.self, from: Data(contentsOf: configURL))
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
        let process = try XCTargetProcess(pid: config.targetPID, bundleID: config.targetBundleID)
        let windows = WindowSensor.snapshots(from: try await WindowSensor.shareableContent(onScreenWindowsOnly: true))
        let matches = WindowSensor.mainWindowCandidates(in: windows, bundleID: config.targetBundleID, pid: config.targetPID)
        guard process.active, NSWorkspace.shared.frontmostApplication?.processIdentifier == pid_t(config.targetPID),
              matches.count == 1,
              let window = matches.first,
              CGWindowInventory.onScreenWindows().contains(where: {
                  $0.windowNumber == window.windowID && $0.ownerPID == config.targetPID && $0.layer == 0
              }),
              AXIsProcessTrusted() else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("live focus/window/AX preflight failed")
        }
        let ledger = try IntentLedger(fileURL: URL(fileURLWithPath: config.ledgerPath))
        let owner = try PersistentTransactionOwner(authorization: auth, ledger: ledger)
        guard command == "live-preflight" else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition(
                "live observations are present but no reviewed native frame+structural-candidate session provider was configured; no events posted"
            )
        }
        let consumedURL = authURL.appendingPathExtension("consumed")
        guard !FileManager.default.fileExists(atPath: consumedURL.path) else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("one-shot authorization already consumed")
        }
        try FileManager.default.moveItem(at: authURL, to: consumedURL)
        FileHandle.standardOutput.write(Data("preflight=passed runID=\(owner.authorization.runID) windowID=\(window.windowID) dispatch=none\n".utf8))
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("\(command) refused: \(error)\n".utf8))
        exit(77)
    }
}

FileHandle.standardError.write(Data("usage: rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>] | restart-child --ledger <path> --head-file <path> --point <name> | live-preflight|live-execute --config <json> --one-shot-authorization <json>\n".utf8))
exit(64)

private struct XCTargetProcess {
    let active: Bool

    init(pid: Int32, bundleID: String) throws {
        guard let application = NSRunningApplication(processIdentifier: pid),
              application.bundleIdentifier == bundleID else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target PID/bundle mismatch")
        }
        active = application.isActive
    }
}

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
