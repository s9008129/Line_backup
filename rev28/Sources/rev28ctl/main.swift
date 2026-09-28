import Foundation
import Rev28Core
import AppKit
import ApplicationServices
import CoreGraphics

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
            let chooserPredicatePath: String
            let chooserCalibrationPath: String
            let chooserPredicateSHA256: String
            let chooserCalibrationSHA256: String
            let baselineReferencePath: String
            let approvedRoot: String
            let tripwireRoots: [String]
            let baselineSourcePath: String?
            let phaseBEligibilityPath: String?
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
        let recomputedImplementationSHA256 = try ReviewedImplementationDigest.compute(
            repositoryRoot: URL(fileURLWithPath: config.repositoryRoot)
        )
        guard oneShot.runID == auth.runID,
              oneShot.planSHA256 == auth.planSHA256,
              oneShot.reviewedImplementationSHA256 == auth.reviewedImplementationSHA256,
              EvidenceIO.sha256Hex(try Data(contentsOf: URL(fileURLWithPath: config.planPath))) == auth.planSHA256,
              recomputedImplementationSHA256 == auth.reviewedImplementationSHA256 else {
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
        // an earlier production run keeps this process observe-only. The
        // durable authority is the goal slot + ledger, never a convenience
        // token marker: an already-consumed goal slot keeps preflight
        // observe-only.
        if command == "live-preflight" {
            let goalSlotDirectory = config.goalSlotDirectory.map { URL(fileURLWithPath: $0) }
                ?? GoalSlot.canonicalDirectory(for: auth)
            if try GoalSlot.load(directory: goalSlotDirectory, authorization: auth)?.entitlementConsumed == true {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "one-shot goal-slot entitlement already consumed; live-preflight stays observe-only"
                )
            }
            // Phase A evidence is append-only per run directory: an existing
            // report means this directory already carries a published Phase A,
            // so a fresh Phase A needs a fresh evidence/run directory.
            guard !PhaseAEvidencePublisher.isPublished(runDirectory: URL(fileURLWithPath: auth.evidenceRunDirectory)) else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "phase-a.json already published in this run directory; a fresh Phase A needs a fresh evidence/run directory"
                )
            }
        }
        let ruleBook = try JSONDecoder().decode(
            CaptureGeometryRuleBook.self,
            from: Data(contentsOf: URL(fileURLWithPath: config.geometryRuleBookPath))
        )
        let target = ObservationTarget(bundleID: config.targetBundleID, pid: config.targetPID)
        let evidenceRunDirectory = URL(fileURLWithPath: auth.evidenceRunDirectory)
        // Plan C6: the frozen predicate file is append-only evidence and is
        // never rewritten. Production re-reads the exact frozen predicate and
        // AX-calibration bytes, verifies both against the hashes bound in this
        // configuration, and derives the stricter process-stable v2 predicate
        // from them. A mismatched or unreadable pair refuses before any live
        // observation, so production can never silently run the v1 predicate
        // that `evaluateProduction` rejects.
        let frozenPredicateBytes = try Data(contentsOf: URL(fileURLWithPath: config.chooserPredicatePath))
        let calibrationBytes = try Data(contentsOf: URL(fileURLWithPath: config.chooserCalibrationPath))
        guard EvidenceIO.sha256Hex(frozenPredicateBytes) == config.chooserPredicateSHA256,
              EvidenceIO.sha256Hex(calibrationBytes) == config.chooserCalibrationSHA256 else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition(
                "chooser predicate/calibration bytes do not match the frozen hashes bound in the configuration"
            )
        }
        let frozenChooserPredicate = try JSONDecoder().decode(
            ChooserAffirmationPredicate.self,
            from: frozenPredicateBytes
        )
        let chooserCalibration = try JSONDecoder().decode(
            ChooserAXCalibrationEvidence.self,
            from: calibrationBytes
        )
        let chooserPredicate = try ChooserProductionPredicate.derive(
            frozen: frozenChooserPredicate,
            calibration: chooserCalibration
        )
        guard chooserPredicate.predicateVersion >= ChooserAffirmationEvaluator.processStableButtonSemanticsVersion else {
            throw QuartzActuatorError.dispatchRefusedByPrecondition(
                "derived chooser predicate is not a process-stable production predicate"
            )
        }
        // Eligibility is armed only by an explicit artifact beneath this run's
        // evidence directory; a configured-but-unreadable artifact refuses the
        // command instead of silently degrading to "not armed".
        let phaseBEligibility: PhaseBEligibilityArtifact?
        if let path = config.phaseBEligibilityPath {
            phaseBEligibility = try PhaseBEligibilityArtifact.load(
                fileURL: URL(fileURLWithPath: path),
                withinRunDirectory: evidenceRunDirectory
            )
        } else {
            phaseBEligibility = nil
        }
        // The eligibility artifact's file-checkable evidence is recomputed
        // here, before the artifact can reach the owner: reviewed Plan bytes,
        // the reviewed implementation source digest and (inside the owner)
        // handoff/frozen/predicate evidence bytes. A label-only artifact
        // refuses.
        try phaseBEligibility?.validateWithRecomputedEvidence(
            against: auth,
            entitlementConsumed: false,
            recomputation: PhaseBEligibilityRecomputation(
                planURL: URL(fileURLWithPath: config.planPath),
                recomputedImplementationSHA256: recomputedImplementationSHA256
            )
        )
        let postSave = try ProductionPostSaveEnvironment(
            baselineReferenceFile: URL(fileURLWithPath: config.baselineReferencePath),
            stagingRunDirectory: URL(fileURLWithPath: auth.stagingRunDirectory),
            approvedRoot: URL(fileURLWithPath: config.approvedRoot),
            monitoredRoots: config.tripwireRoots.map { URL(fileURLWithPath: $0) },
            evidenceRunDirectory: evidenceRunDirectory,
            baselineSourceDirectory: config.baselineSourcePath.map { URL(fileURLWithPath: $0) },
            signingIdentity: { ProcessIdentity.signingIdentity(pid: $0) }
        )
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
                addressableBoundsCapture: config.addressableBoundsCapture.rect,
                chooserPredicate: chooserPredicate,
                baselineReferenceFile: URL(fileURLWithPath: config.baselineReferencePath)
            ),
            target: target,
            source: try ProductionObservationSource(
                target: target,
                evidenceRunDirectory: evidenceRunDirectory,
                ruleBook: ruleBook,
                signingIdentity: { ProcessIdentity.signingIdentity(pid: $0) }
            ),
            environment: ProductionActuationEnvironment(),
            postSave: postSave,
            phaseBEligibility: phaseBEligibility,
            phaseBEligibilityRecomputation: phaseBEligibility.map { _ in
                PhaseBEligibilityRecomputation(
                    planURL: URL(fileURLWithPath: config.planPath),
                    recomputedImplementationSHA256: recomputedImplementationSHA256
                )
            },
            sessionID: config.sessionID ?? "live-\(auth.runID)"
        )
        switch command {
        case "live-preflight":
            let outcome = try await composition.engine.runPreflight()
            // Phase A: record ≥10 s of pre-dispatch environmental context at
            // SAVE_ALL_LOCATED with the tripwire running and gap-free. Zero
            // irreversible intent.
            let preDispatchContextSHA256 = try await composition.adapter.observePreDispatchContext(
                owner: composition.owner
            )
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
                reversibleDispatches: composition.owner.reversibleDispatchCount,
                preDispatchContextSHA256: preDispatchContextSHA256
            )
            let stamp = EvidenceIO.iso8601().replacingOccurrences(of: ":", with: "-")
            let outcomeURL = URL(fileURLWithPath: auth.evidenceRunDirectory)
                .appendingPathComponent("preflight-outcome-\(stamp).json")
            try EvidenceIO.writeJSONAtomically(record, to: outcomeURL)

            // Phase A publication: a per-condition PASS/FAIL/UNKNOWN report plus
            // a raw evidence manifest, all from the run directory this preflight
            // just wrote. Observation-only; the actual LINE chooser stays a
            // Phase B runtime gate and is recorded as deferred, never as PASS.
            let runDirectory = URL(fileURLWithPath: auth.evidenceRunDirectory)
            let inspection = try PhaseAEvidenceBuilder.inspect(runDirectory: runDirectory)

            var inventory: PhaseAInventoryFacts?
            var inventoryError: String?
            if let target = inspection.targetWindowArtifact {
                do {
                    let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
                    let sck = WindowSensor.snapshots(from: content)
                    let cg = CGWindowInventory.onScreenWindows()
                    let axWindows = AXDriver.windows(ofApp: pid_t(config.targetPID))
                    let axFrameMatches = axWindows.contains { element in
                        guard let frame = AXDriver.frame(of: element) else { return false }
                        return abs(frame.origin.x - target.windowFrame.origin.x) <= 4
                            && abs(frame.origin.y - target.windowFrame.origin.y) <= 4
                            && abs(frame.width - target.windowFrame.width) <= 4
                            && abs(frame.height - target.windowFrame.height) <= 4
                    }
                    inventory = PhaseAInventoryFacts(
                        sckWindowCount: sck.count,
                        cgWindowCount: cg.count,
                        axWindowCount: axWindows.count,
                        targetWindowID: target.windowID,
                        targetPresentInSCK: sck.contains { $0.windowID == target.windowID },
                        targetPresentInCG: cg.contains { $0.windowNumber == target.windowID },
                        axFrameMatchesTarget: axFrameMatches
                    )
                } catch {
                    inventoryError = String(describing: error)
                }
            } else {
                inventoryError = "no SAVE_ALL_LOCATED state artifact to bind the inventory to"
            }

            let frames = inspection.states.map(\.artifact.windowFrame)
                + (inspection.targetWindowArtifact.map { [$0.windowFrame] } ?? [])
            let displayScales = Set(frames.compactMap {
                FrameCaptureSupport.backingScaleFactor(forWindowFrame: $0)
            }).sorted()

            let frozenGeometry = PhaseAFrozenGeometryFacts(
                captureConfiguration: "primaryWindow",
                ruleID: ruleBook.ruleID,
                settled: true,
                activated: true,
                includeChildWindows: false,
                ignoreShadows: true,
                menuBoundsCapture: config.menuBoundsCapture.rect,
                addressableBoundsCapture: config.addressableBoundsCapture.rect
            )

            var baselineResult: BaselineVerificationResult?
            var baselineError: String?
            do {
                baselineResult = try postSave.verifyBaseline()
            } catch {
                baselineError = String(describing: error)
            }

            var stagingSnapshot: StagingSnapshot?
            var stagingError: String?
            do {
                stagingSnapshot = try postSave.stagingSnapshot(
                    directory: URL(fileURLWithPath: auth.stagingRunDirectory)
                )
            } catch {
                stagingError = String(describing: error)
            }

            let tripwire = postSave.tripwireReadiness()

            var prePanelCensus: ChooserCensus?
            var prePanelCensusArtifactName: String?
            var prePanelCensusError: String?
            do {
                let census = try await postSave.preDispatchCensus()
                let censusName = "pre-panel-census-\(stamp).json"
                try EvidenceIO.writeJSONAtomically(census, to: runDirectory.appendingPathComponent(censusName))
                prePanelCensus = census
                prePanelCensusArtifactName = censusName
            } catch {
                prePanelCensusError = String(describing: error)
            }

            let ledger = composition.owner.ledger
            let ownerIrreversible = composition.owner.irreversibleOperationCounts
            let phaseAInputs = PhaseAEvidenceInputs(
                authorization: auth,
                targetBundleID: config.targetBundleID,
                targetPID: config.targetPID,
                liveProcess: PhaseAProcessFacts(
                    bundleID: ProcessIdentity.bundleID(pid: config.targetPID),
                    signingIdentity: ProcessIdentity.signingIdentity(pid: config.targetPID),
                    startTimeSeconds: ProcessInstanceID.current(pid: config.targetPID)?.startTimeSeconds,
                    startTimeMicroseconds: ProcessInstanceID.current(pid: config.targetPID)?.startTimeMicroseconds
                ),
                axTrusted: AXIsProcessTrusted(),
                screenCaptureTrusted: CGPreflightScreenCaptureAccess(),
                inventory: inventory,
                inventoryError: inventoryError,
                displayScales: displayScales,
                frozenGeometry: frozenGeometry,
                baselineResult: baselineResult,
                baselineError: baselineError,
                stagingSnapshot: stagingSnapshot,
                stagingError: stagingError,
                tripwire: tripwire,
                tripwireError: nil,
                prePanelCensus: prePanelCensus,
                prePanelCensusArtifactName: prePanelCensusArtifactName,
                prePanelCensusError: prePanelCensusError,
                preDispatchContextSHA256: preDispatchContextSHA256,
                ledgerCounts: PhaseALedgerCounts(
                    saveAllIntent: ledger.count(kind: "intent.saveAll"),
                    saveAllAttempt: ledger.count(kind: "attempt.saveAll"),
                    destinationIntent: ledger.count(kind: "intent.destinationConfirmation"),
                    destinationAttempt: ledger.count(kind: "attempt.destinationConfirmation"),
                    ownerSaveAllCount: ownerIrreversible.saveAll,
                    ownerDestinationCount: ownerIrreversible.destinationConfirmation
                ),
                reversibleDispatches: composition.owner.reversibleDispatchCount,
                preflightOutcomeArtifactName: outcomeURL.lastPathComponent
            )
            let phaseAReport = PhaseAEvidenceBuilder.build(
                inputs: phaseAInputs,
                inspection: inspection,
                generatedAtISO8601: EvidenceIO.iso8601()
            )
            let published = try PhaseAEvidencePublisher.publish(report: phaseAReport, runDirectory: runDirectory)
            FileHandle.standardOutput.write(Data("""
            preflight=passed runID=\(auth.runID) finalState=\(outcome.finalState.rawValue) observations=\(outcome.observationsThisRun) \
            sessionCaptures=\(captures) irreversible=0 entitlement=unconsumed outcome=\(outcomeURL.lastPathComponent) \
            phaseA=\(published.reportName) sha256=\(published.reportSHA256) manifest=\(published.manifestName) \
            entries=\(published.manifestEntryCount) conditions=\(published.passCount)P/\(published.failCount)F/\(published.unknownCount)U \
            phaseBPreventedBy=\(published.phaseBPreventedBy.isEmpty ? "none" : published.phaseBPreventedBy.joined(separator: ","))

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
    let preDispatchContextSHA256: String
}
