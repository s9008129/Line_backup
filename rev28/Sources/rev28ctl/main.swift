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
            struct Bounds: Decodable {
                let x: Double
                let y: Double
                let width: Double
                let height: Double
                var rect: CGRect { CGRect(x: x, y: y, width: width, height: height) }
            }
            let authorization: ImmutableRunAuthorization
            let targetBundleID: String
            let targetPID: Int32
            let ledgerPath: String
            let checkpointPath: String
            let planPath: String
            let repositoryRoot: String
            let geometryRuleBookPath: String
            let menuBoundsCapture: Bounds
            let addressableBoundsCapture: Bounds
            let observationBudgetNanos: UInt64?
            let goalSlotDirectory: String?
            let sessionID: String?
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
            throw QuartzActuatorError.dispatchRefusedByPrecondition("target process is not the reviewed LINE instance")
        }
        guard AXIsProcessTrusted() else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition("accessibility permission is not granted")
        }
        // Phase A preflight is observation-only: it never renames or consumes
        // the one-shot authorization (R4 C4). Only the durable Save All
        // reservation arms the entitlement, and an authorization consumed by
        // an earlier production run keeps this process observe-only.
        if command == "live-preflight" {
            guard OneShotAuthorizationGate.inspect(authorizationURL: authURL) == .available else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "one-shot authorization already consumed; live-preflight stays observe-only"
                )
            }
        }
        let ruleBook = try JSONDecoder().decode(
            CaptureGeometryRuleBook.self,
            from: Data(contentsOf: URL(fileURLWithPath: config.geometryRuleBookPath))
        )
        let target = ObservationTarget(bundleID: config.targetBundleID, pid: config.targetPID)
        let composition = try LiveCompositionFactory.make(
            authorization: auth,
            ledgerURL: URL(fileURLWithPath: config.ledgerPath),
            checkpointURL: URL(fileURLWithPath: config.checkpointPath),
            goalSlotDirectory: config.goalSlotDirectory.map { URL(fileURLWithPath: $0) },
            configuration: LiveCompositionConfiguration(
                observationBudgetNanos: config.observationBudgetNanos ?? 5_000_000_000,
                captureConfiguration: .primaryWindow,
                geometryState: CaptureGeometryState(
                    settled: true,
                    activated: true,
                    includeChildWindows: false,
                    ignoreShadows: true
                ),
                geometryRuleBook: ruleBook,
                menuBoundsCapture: config.menuBoundsCapture.rect,
                addressableBoundsCapture: config.addressableBoundsCapture.rect
            ),
            target: target,
            source: try ProductionObservationSource(
                target: target,
                evidenceRunDirectory: URL(fileURLWithPath: auth.evidenceRunDirectory),
                ruleBook: ruleBook,
                signingIdentity: { ProcessIdentity.signingIdentity(pid: $0) }
            ),
            environment: ProductionActuationEnvironment(),
            sessionID: config.sessionID ?? "live-\(auth.runID)"
        )
        switch command {
        case "live-preflight":
            let outcome = try await composition.engine.runPreflight()
            let captures = await composition.session.captureCount
            let record = LivePreflightRecord(
                runID: auth.runID,
                finalState: outcome.finalState.rawValue,
                observationsThisRun: outcome.observationsThisRun,
                sessionCaptures: captures,
                epochFloor: composition.epochAuthority.floor,
                saveAllIrreversibleRecords: outcome.saveAllIrreversibleRecords,
                destinationIrreversibleRecords: outcome.destinationIrreversibleRecords,
                entitlementConsumed: outcome.entitlementConsumed,
                reversibleDispatches: composition.owner.reversibleDispatchCount
            )
            let stamp = EvidenceIO.iso8601().replacingOccurrences(of: ":", with: "-")
            let outcomeURL = URL(fileURLWithPath: auth.evidenceRunDirectory)
                .appendingPathComponent("preflight-outcome-\(stamp).json")
            try EvidenceIO.writeJSONAtomically(record, to: outcomeURL)
            FileHandle.standardOutput.write(Data("""
            preflight=passed runID=\(auth.runID) finalState=\(outcome.finalState.rawValue) observations=\(outcome.observationsThisRun) \
            sessionCaptures=\(captures) irreversible=0 entitlement=unconsumed outcome=\(outcomeURL.lastPathComponent)

            """.utf8))
            exit(0)
        default:
            let outcome = try await composition.engine.run()
            FileHandle.standardError.write(Data(
                "\(command): unexpected outcome \(outcome); no irreversible dispatch is authorized in this round\n".utf8
            ))
            exit(78)
        }
    } catch {
        FileHandle.standardError.write(Data("\(command) refused: \(error)\n".utf8))
        exit(77)
    }
}
FileHandle.standardError.write(Data("usage: rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>] | restart-child --ledger <path> --head-file <path> --point <name> | live-preflight|live-execute --config <json> --one-shot-authorization <json>\n".utf8))
exit(64)

/// Durable Phase A preflight outcome. Written into the run's evidence
/// directory before the command reports success.
private struct LivePreflightRecord: Codable {
    let runID: String
    let finalState: String
    let observationsThisRun: Int
    let sessionCaptures: Int
    let epochFloor: UInt64
    let saveAllIrreversibleRecords: Int
    let destinationIrreversibleRecords: Int
    let entitlementConsumed: Bool
    let reversibleDispatches: Int
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
