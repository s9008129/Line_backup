import Foundation
import Rev28Core
import AppKit
import ApplicationServices
import CoreGraphics
import ImageIO

// rev28ctl — the W2 harness driver (plan §SYNTHETIC_HARNESS_CALIBRATION_PLAN).
//
//   rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>]
//   rev28ctl restart-child --ledger <path> --head-file <path> --point <name>

let arguments = CommandLine.arguments

func optionValue(_ name: String) -> String? {
    guard let index = arguments.firstIndex(of: name), index + 1 < arguments.count else { return nil }
    return arguments[index + 1]
}

if arguments.count >= 2, arguments[1] == "runtime-preflight" {
    do {
        let result = try PilotNativeAuthority.preflight()
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]))
        FileHandle.standardOutput.write(Data("\n".utf8)); exit(0)
    } catch {
        FileHandle.standardError.write(Data("runtime-preflight refused: \(error)\n".utf8)); exit(77)
    }
}

if arguments.count >= 2, arguments[1] == "capture-diagnostic" {
    do {
        let receipt = try await PassiveCaptureDiagnostic.run(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch is PassiveCaptureDiagnostic.UsageError {
        FileHandle.standardError.write(Data((PassiveCaptureDiagnostic.usage + "\n").utf8))
        exit(64)
    } catch {
        FileHandle.standardError.write(Data("capture-diagnostic refused: \(error)\n".utf8))
        exit(77)
    }
}

// Read-only context/OCR producer consumed by the hosted LINE analyzer. This
// command does not grant foreground or GUI authority; callers must obtain it
// before observing LINE, just as for the other native capture commands.
if arguments.count >= 2, arguments[1] == "native-context" {
    struct Refusal: Encodable {
        let schemaVersion = 1
        let complete = false
        let truncated = false
        let errors: [String]
    }
    do {
        guard let bundleID = optionValue("--bundle-id") else {
            throw PassiveContextObservation.CaptureError.unsupportedBundle("--bundle-id is required")
        }
        let imagePath = optionValue("--image")
        let imageSHA = optionValue("--image-sha256")
        guard (imagePath == nil) == (imageSHA == nil) else {
            throw PassiveContextObservation.CaptureError.invalidImageBinding
        }
        if let imagePath, !imagePath.hasPrefix("/") {
            throw PassiveContextObservation.CaptureError.invalidImageBinding
        }
        guard let grant = optionValue("--grant"), let root = optionValue("--project-root"),
              let hash = optionValue("--grant-sha256"), let sessionID = optionValue("--session-id") else {
            throw PassiveDiagnosticError.refused("pilot context authority arguments required")
        }
        _ = try PilotNativeAuthority.verify(root: URL(fileURLWithPath: root), grantPath: grant, grantSHA: hash,
            sessionID: sessionID)
        let observation = try PassiveContextObservation.capture(
            bundleID: bundleID,
            imageURL: imagePath.map { URL(fileURLWithPath: $0) },
            imageSHA256: imageSHA
        )
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(observation))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(observation.complete ? 0 : 77)
    } catch {
        let refusal = Refusal(errors: ["native-context refused: \(error)"])
        if let data = try? EvidenceIO.encodeJSON(refusal) {
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
        }
        FileHandle.standardError.write(Data("native-context refused: \(error)\n".utf8))
        exit(77)
    }
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
    // This legacy entry only targets the historical canonical album. Keep the
    // engine/Quartz fixture lane, but never create a second live authority.
    if command == "live-execute" {
        FileHandle.standardError.write(Data("legacy live-execute is disabled; use the canonical hosted batch service\n".utf8))
        exit(77)
    }
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
            struct EligibilityBinding: Decodable {
                let path: String
                let sha256: String
            }
            struct EligibilityCanonicalBindings: Decodable {
                let handoff: EligibilityBinding
                let frozenArtifacts: [String: EligibilityBinding]
                let predicateEvidence: [String: EligibilityBinding]
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
            let eligibilityCanonicalBindings: EligibilityCanonicalBindings?
            let reviewedHeadSHA: String?
            let reviewedPathsDiffSHA256: String?
            let reviewedBinarySHA256: String?
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
        // The canonical reviewed bindings (Stage 03 handoff, frozen rule/
        // predicate/fixture/provenance artifacts and every required
        // predicate's evidence) are supplied by the reviewed configuration,
        // never by the artifact. An artifact whose declarations differ from
        // them, or whose declared evidence escapes the reviewed roots, can
        // never arm the entitlement.
        let phaseBEligibility: PhaseBEligibilityArtifact?
        let phaseBEligibilityRecomputation: PhaseBEligibilityRecomputation?
        if let path = config.phaseBEligibilityPath {
            guard let canonical = config.eligibilityCanonicalBindings,
                  let reviewedHeadSHA = config.reviewedHeadSHA,
                  let reviewedPathsDiffSHA256 = config.reviewedPathsDiffSHA256,
                  let reviewedBinarySHA256 = config.reviewedBinarySHA256 else {
                throw QuartzActuatorError.dispatchRefusedByPrecondition(
                    "eligibility canonical reviewed bindings (handoff/frozen/predicate and reviewed HEAD/diff/binary) are required whenever an eligibility artifact is configured"
                )
            }
            let repositoryRoot = URL(fileURLWithPath: config.repositoryRoot)
            // The reviewed HEAD/diff/binary facts are recomputed live: the
            // reviewed commit must be HEAD or an ancestor of it, the reviewed
            // paths must have no diff against that commit, and the running
            // executable must hash to the reviewed binary.
            let executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
                .resolvingSymlinksInPath()
                .standardizedFileURL
            let canonicalReviewedBuild = ReviewedBuildExpectations(
                reviewedHeadSHA: reviewedHeadSHA,
                reviewedPathsDiffSHA256: reviewedPathsDiffSHA256,
                reviewedBinarySHA256: reviewedBinarySHA256
            )
            let observedReviewedBuild = try ReviewedBuildState.observe(
                repositoryRoot: repositoryRoot,
                reviewedHeadSHA: reviewedHeadSHA,
                executableURL: executableURL
            )
            let recomputation = PhaseBEligibilityRecomputation(
                planURL: URL(fileURLWithPath: config.planPath),
                recomputedImplementationSHA256: recomputedImplementationSHA256,
                canonicalReviewedBuild: canonicalReviewedBuild,
                observedReviewedBuild: observedReviewedBuild,
                canonicalHandoff: CanonicalEvidenceBinding(
                    path: canonical.handoff.path,
                    sha256: canonical.handoff.sha256
                ),
                canonicalFrozenArtifacts: canonical.frozenArtifacts.mapValues {
                    CanonicalEvidenceBinding(path: $0.path, sha256: $0.sha256)
                },
                canonicalPredicateEvidence: canonical.predicateEvidence.mapValues {
                    CanonicalEvidenceBinding(path: $0.path, sha256: $0.sha256)
                },
                allowedEvidenceRoots: [
                    repositoryRoot,
                    evidenceRunDirectory,
                ]
            )
            // The eligibility artifact's file-checkable evidence is recomputed
            // here, before the artifact can reach the owner, and compared
            // against those canonical reviewed values. A label-only or
            // self-declared artifact refuses.
            let artifact = try PhaseBEligibilityArtifact.load(
                fileURL: URL(fileURLWithPath: path),
                withinRunDirectory: evidenceRunDirectory
            )
            try artifact.validateWithRecomputedEvidence(
                against: auth,
                entitlementConsumed: false,
                recomputation: recomputation
            )
            phaseBEligibility = artifact
            phaseBEligibilityRecomputation = recomputation
        } else {
            phaseBEligibility = nil
            phaseBEligibilityRecomputation = nil
        }
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
            phaseBEligibilityRecomputation: phaseBEligibilityRecomputation,
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
            preflight=\(phaseAReport.allConditionsPass ? "passed" : "blocked") runID=\(auth.runID) finalState=\(outcome.finalState.rawValue) observations=\(outcome.observationsThisRun) \
            sessionCaptures=\(captures) irreversible=0 entitlement=unconsumed outcome=\(outcomeURL.lastPathComponent) \
            phaseA=\(published.reportName) sha256=\(published.reportSHA256) manifest=\(published.manifestName) \
            entries=\(published.manifestEntryCount) conditions=\(published.passCount)P/\(published.failCount)F/\(published.unknownCount)U \
            phaseBPreventedBy=\(published.phaseBPreventedBy.isEmpty ? "none" : published.phaseBPreventedBy.joined(separator: ","))

            """.utf8))
            exit(phaseAReport.exitCode)
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
if arguments.count >= 2, arguments[1] == "frame-support" {
    guard ProcessInfo.processInfo.environment["CI"] == nil else {
        FileHandle.standardError.write(Data("frame-support: live capture is disabled in CI\n".utf8))
        exit(77)
    }
    do {
        let receipt = try await runFrameSupportCapture(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch let error as FrameSupportCommandError {
        FileHandle.standardError.write(Data((error.description + "\n").utf8))
        exit(error.isUsage ? 64 : 77)
    } catch {
        FileHandle.standardError.write(Data("frame-support refused: \(error)\n".utf8))
        exit(77)
    }
}
if arguments.count >= 2, arguments[1] == "visual-diagnostic-capture" {
    guard ProcessInfo.processInfo.environment["CI"] == nil else {
        FileHandle.standardError.write(Data("visual-diagnostic-capture: live capture is disabled in CI\n".utf8))
        exit(77)
    }
    do {
        let receipt = try await VisualDiagnosticCommand.run(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("visual-diagnostic-capture refused: \(error)\n".utf8))
        exit(77)
    }
}
if arguments.count >= 2, arguments[1] == "visual-diagnostic-clock" {
    do {
        let receipt = try VisualDiagnosticCommand.clock(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("visual-diagnostic-clock refused: \(error)\n".utf8))
        exit(77)
    }
}
if arguments.count >= 2, arguments[1] == "visual-diagnostic-clock-check" {
    do {
        let result = try VisualDiagnosticCommand.checkClockBracket(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(result))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("visual-diagnostic-clock-check refused: \(error)\n".utf8))
        exit(77)
    }
}
if arguments.count >= 2, arguments[1] == "visual-diagnostic-analyze" {
    do {
        let analysis = try await VisualDiagnosticCommand.analyze(arguments: arguments)
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(analysis))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch {
        FileHandle.standardError.write(Data("visual-diagnostic-analyze refused: \(error)\n".utf8))
        exit(77)
    }
}
if arguments.count >= 2, ["album-support", "album-support-guard"].contains(arguments[1]) {
    let command = arguments[1]
    guard ProcessInfo.processInfo.environment["CI"] == nil else {
        FileHandle.standardError.write(Data("\(command): live capture is disabled in CI\n".utf8))
        exit(77)
    }
    do {
        if command == "album-support" {
            let receipt = try await runAlbumSupportCapture(arguments: arguments)
            FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        } else {
            let receipt = try await runAlbumSupportGuard(arguments: arguments)
            FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(receipt))
        }
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch let error as AlbumSupportCommandError {
        FileHandle.standardError.write(Data((error.description + "\n").utf8))
        exit(error.isUsage ? 64 : 77)
    } catch {
        FileHandle.standardError.write(Data("\(command) refused: \(error)\n".utf8))
        exit(77)
    }
}
FileHandle.standardError.write(Data(("usage: " + PassiveCaptureDiagnostic.usage + " | rev28ctl harness-calibrate --evidence <dir> [--items 1,2,5] [--binary-dir <dir>] | restart-child --ledger <path> --head-file <path> --point <name> | live-preflight|live-execute --config <json> --one-shot-authorization <json> | frame-support --project-root <dir> --grant <path> --grant-sha256 <sha> --output <dir> --bundle-id <id> --pid <n> --window-id <n> --display-id <n> --session-id <id> --layout-key <sha> --surface ALBUMS|ALBUM_DETAIL|FOLDER_CHOOSER --pair-frame <path> --pair-frame-id <sha> --geometry-evidence <path> --geometry-evidence-sha256 <sha> --cua-captured-at <iso> --cua-bounds <x,y,w,h> | album-support ... | album-support-guard ...\n").utf8))
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

// MARK: - Read-only `album-support` full-display popup producer
//
// Two passive subcommands used by the documented CUA bridge:
//   rev28ctl album-support ...        captures one full-display popup frame,
//                                     retains it with its OCR sidecar and
//                                     writes the Python-authority sidecar
//   rev28ctl album-support-guard ...  re-reads the retained bytes and re-OCRs
//                                     them to verify the calibrated Save All
//                                     point before any GUI dispatch
// Neither subcommand constructs an actuator, clicks, types or switches apps.

private enum AlbumSupportCommandError: Error, CustomStringConvertible {
    case usage(String)
    case refused(String)

    var isUsage: Bool {
        if case .usage = self { return true }
        return false
    }

    var description: String {
        switch self {
        case let .usage(message): return "usage: \(message)"
        case let .refused(message): return "album-support refused: \(message)"
        }
    }
}

private struct AlbumSupportClaim: Codable {
    let version: Int
    let mode: String
    let output: String
    let pairFrameId: String
    let sessionId: String
    let pid: Int32
    let windowId: UInt32
    let displayId: UInt32
    let layoutKey: String
    let claimedAt: String
    let status: String
}

private struct AlbumSupportCaptureReceipt: Codable {
    let provider: String
    let pairFrameId: String
    let popupFrameId: String
    let popupCapturedAt: String
    let popupSource: String
    let sessionId: String
    let reference: AlbumSupportArtifactRef
    let manifestReference: AlbumSupportArtifactRef
    let uncertaintyPx: Double
    let safeMarginPx: Double
    let intersectionPx: [Double]
}

private struct AlbumSupportGuardReceipt: Codable {
    let verdict: String
    let provider: String
    let pairFrameId: String
    let popupFrameId: String
    let supportSha256: String
    let actionPoint: [Double]
}

private struct AlbumSupportManifest: Codable {
    let version: Int
    let producer: String
    let mode: String
    let projectRoot: String
    let output: String
    let pairFrameId: String
    let popupFrameId: String
    let popupCapturedAt: String
    let sessionId: String
    let pid: Int32
    let windowId: UInt32
    let displayId: UInt32
    let layoutKey: String
    let captureKind: String
    let includeMenuBar: Bool
    let sourceRectAbsent: Bool
    let imageWidthPx: Int
    let imageHeightPx: Int
    let pointPixelScale: Double
    let backingScaleFactor: Double
    let contentRect: [Double]
    let displayBounds: [Double]
    let anchorTexts: [String]
    let maximumAnchorResidualPx: Double
    let safeMarginPx: Double
    let interactiveIntersectionPx: [Double]
    let sckFrame: AlbumSupportArtifactRef
    let ocr: AlbumSupportArtifactRef
    let captureRecord: CapturedFrameRecord
    let note: String
}

private struct FrameSupportCaptureReceipt: Codable {
    let provider: String
    let surface: String
    let pairFrameId: String
    let sckFrameId: String
    let sckCapturedAt: String
    let sessionId: String
    let reference: AlbumSupportArtifactRef
    let manifestReference: AlbumSupportArtifactRef
    let uncertaintyPx: Double
    let safeMarginPx: Double
    let intersectionPx: [Double]
    let captureRequestMilliseconds: Double
}

private struct FrameSupportManifest: Codable {
    let version: Int
    let producer: String
    let projectRoot: String
    let output: String
    let surface: String
    let pairFrameId: String
    let sckFrameId: String
    let sessionId: String
    let pid: Int32
    let windowId: UInt32
    let displayId: UInt32
    let layoutKey: String
    let captureKind: String
    let includeMenuBar: Bool
    let sourceRectAbsent: Bool
    let imageWidthPx: Int
    let imageHeightPx: Int
    let pointPixelScale: Double
    let backingScaleFactor: Double
    let contentRect: [Double]
    let displayBounds: [Double]
    let surfaceBoundsPx: [Double]
    let anchorTexts: [String]
    let maximumAnchorResidualPx: Double
    let uncertaintyPx: Double
    let safeMarginPx: Double
    let interactiveIntersectionPx: [Double]
    let geometryEvidence: AlbumSupportArtifactRef
    let sckFrame: AlbumSupportArtifactRef
    let ocr: AlbumSupportArtifactRef
    let support: AlbumSupportArtifactRef
    let captureRecord: CapturedFrameRecord
    let captureTiming: FullDisplayCaptureTiming
}

private enum FrameSupportCommandError: Error, CustomStringConvertible {
    case usage(String)
    case refused(String)

    var isUsage: Bool { if case .usage = self { return true }; return false }
    var description: String {
        switch self {
        case let .usage(message): return "usage: \(message)"
        case let .refused(message): return "frame-support refused: \(message)"
        }
    }
}

private func albumSupportOption(_ name: String, _ arguments: [String]) throws -> String {
    guard let value = optionValue(name) else { throw AlbumSupportCommandError.usage("\(name) is required") }
    return value
}

private func albumSupportHex(_ name: String, _ arguments: [String]) throws -> String {
    let value = try albumSupportOption(name, arguments)
    guard value.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else {
        throw AlbumSupportCommandError.refused("\(name) must be a lowercase sha256 hex string")
    }
    return value
}

private func albumSupportInt(_ name: String, _ arguments: [String]) throws -> Int {
    let value = try albumSupportOption(name, arguments)
    guard let number = Int(value), number > 0, number <= Int(Int32.max) else {
        throw AlbumSupportCommandError.refused("\(name) must be a positive 32-bit integer")
    }
    return number
}

private func albumSupportDouble(_ name: String, _ arguments: [String]) throws -> Double {
    let value = try albumSupportOption(name, arguments)
    guard let number = Double(value), number.isFinite else {
        throw AlbumSupportCommandError.refused("\(name) must be a finite number")
    }
    return number
}

private func albumSupportList(_ name: String, _ arguments: [String], count: Int) throws -> [Double] {
    let value = try albumSupportOption(name, arguments)
    let parts = value.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
    let numbers = parts.compactMap { Double($0) }
    guard parts.count == count, numbers.count == count, numbers.allSatisfy({ $0.isFinite }) else {
        throw AlbumSupportCommandError.refused("\(name) must be \(count) comma-separated finite numbers")
    }
    return numbers
}

private func albumSupportRect(_ name: String, _ arguments: [String]) throws -> [Double] {
    let values = try albumSupportList(name, arguments, count: 4)
    guard values[2] > 0, values[3] > 0 else {
        throw AlbumSupportCommandError.refused("\(name) must have a positive width and height")
    }
    return values
}

private func albumSupportPoint(_ name: String, _ arguments: [String]) throws -> [Double] {
    try albumSupportList(name, arguments, count: 2)
}

private func albumSupportDecodeImage(_ data: Data) throws -> CGImage {
    guard let source = CGImageSourceCreateWithData(data as CFData, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw AlbumSupportCommandError.refused("the retained bytes are not a decodable image")
    }
    return image
}

private func albumSupportSyncWrite(_ data: Data, to url: URL) throws {
    do {
        try data.write(to: url, options: .atomic)
        let handle = try FileHandle(forUpdating: url)
        try handle.synchronize()
        try handle.close()
    } catch {
        throw AlbumSupportCommandError.refused("cannot persist \(url.lastPathComponent): \(error)")
    }
}

private func albumSupportClaim(_ data: Data, at url: URL) throws {
    guard FileManager.default.createFile(atPath: url.path, contents: data) else {
        throw AlbumSupportCommandError.refused("the claim file already exists at \(url.lastPathComponent)")
    }
    do {
        let handle = try FileHandle(forUpdating: url)
        try handle.synchronize()
        try handle.close()
    } catch {
        throw AlbumSupportCommandError.refused("cannot synchronize the claim file: \(error)")
    }
}

private func albumSupportRectArray(_ rect: CGRect) -> [Double] {
    [Double(rect.minX), Double(rect.minY), Double(rect.width), Double(rect.height)]
}

private func frameSupportOption(_ name: String) throws -> String {
    guard let value = optionValue(name), !value.isEmpty else {
        throw FrameSupportCommandError.usage("frame-support requires \(name)")
    }
    return value
}

private func frameSupportInteger(_ name: String) throws -> Int {
    let raw = try frameSupportOption(name)
    guard let value = Int(raw), value > 0, value <= Int(Int32.max) else {
        throw FrameSupportCommandError.refused("\(name) must be a positive 32-bit integer")
    }
    return value
}

private func frameSupportList(_ name: String, count: Int) throws -> [Double] {
    let raw = try frameSupportOption(name)
    let parts = raw.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
    let values = parts.compactMap(Double.init)
    guard parts.count == count, values.count == count, values.allSatisfy(\.isFinite) else {
        throw FrameSupportCommandError.refused("\(name) must contain \(count) finite comma-separated numbers")
    }
    return values
}

private func frameSupportRef(_ raw: Any?, name: String) throws -> AlbumSupportArtifactRef {
    guard let value = raw as? [String: Any], Set(value.keys) == Set(["path", "bytes", "sha256"]),
          let path = value["path"] as? String, path.hasPrefix("harness-development/"),
          !path.split(separator: "/").contains(".."), let bytes = value["bytes"] as? Int, bytes > 0,
          let digest = value["sha256"] as? String,
          digest.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else {
        throw FrameSupportCommandError.refused("\(name) must be a bounded task artifact reference")
    }
    return AlbumSupportArtifactRef(path: path, bytes: bytes, sha256: digest)
}

private func frameSupportFileURL(root: URL, relativePath: String) throws -> URL {
    guard !relativePath.hasPrefix("/"), relativePath.hasPrefix("harness-development/"),
          !relativePath.split(separator: "/").contains(".."),
          !relativePath.split(separator: "/").contains(".") else {
        throw FrameSupportCommandError.refused("artifact paths must stay under harness-development/")
    }
    let candidate = root.appendingPathComponent(relativePath).standardizedFileURL
    guard candidate.path.hasPrefix(root.path + "/") else {
        throw FrameSupportCommandError.refused("artifact path escapes the selected project root")
    }
    var cursor = root
    for component in relativePath.split(separator: "/") {
        cursor.appendPathComponent(String(component), isDirectory: false)
        let values = try cursor.resourceValues(forKeys: [.isSymbolicLinkKey])
        guard values.isSymbolicLink != true else {
            throw FrameSupportCommandError.refused("artifact path contains a symbolic link")
        }
    }
    return candidate
}

private func frameSupportReadRef(_ ref: AlbumSupportArtifactRef, root: URL, name: String,
                                evidenceCap: Int? = 16 * 1024 * 1024) throws -> Data {
    if let evidenceCap, ref.bytes > evidenceCap {
        throw FrameSupportCommandError.refused("\(name) exceeds the \(evidenceCap / (1024 * 1024)) MiB evidence cap")
    }
    let url = try frameSupportFileURL(root: root, relativePath: ref.path)
    let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
    guard values.isRegularFile == true, values.isSymbolicLink != true else {
        throw FrameSupportCommandError.refused("\(name) must be a regular non-symlink file")
    }
    if let evidenceCap {
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        guard let fileSize = attributes[.size] as? NSNumber, fileSize.intValue == ref.bytes,
              fileSize.intValue <= evidenceCap else {
            throw FrameSupportCommandError.refused("\(name) exceeds the bounded retained-file size")
        }
    }
    let handle = try FileHandle(forReadingFrom: url)
    var data = Data()
    while let chunk = try handle.read(upToCount: 64 * 1024), !chunk.isEmpty {
        if let evidenceCap, data.count + chunk.count > evidenceCap {
            try? handle.close()
            throw FrameSupportCommandError.refused("\(name) exceeds the bounded retained-file size")
        }
        data.append(chunk)
    }
    try handle.close()
    guard data.count == ref.bytes, EvidenceIO.sha256Hex(data) == ref.sha256 else {
        throw FrameSupportCommandError.refused("\(name) bytes or SHA-256 do not match the retained reference")
    }
    return data
}

private func frameSupportReadBoundedFile(_ url: URL, name: String,
                                         cap: Int = 16 * 1024 * 1024) throws -> Data {
    let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
    guard let fileSize = attributes[.size] as? NSNumber, fileSize.intValue >= 0,
          fileSize.intValue <= cap else {
        throw FrameSupportCommandError.refused("\(name) exceeds the bounded retained-file size")
    }
    let handle = try FileHandle(forReadingFrom: url)
    var data = Data()
    while let chunk = try handle.read(upToCount: 64 * 1024), !chunk.isEmpty {
        guard data.count + chunk.count <= cap else {
            try? handle.close()
            throw FrameSupportCommandError.refused("\(name) exceeds the bounded retained-file size")
        }
        data.append(chunk)
    }
    try handle.close()
    guard data.count == fileSize.intValue else {
        throw FrameSupportCommandError.refused("\(name) changed while being read")
    }
    return data
}

private func frameSupportVerifyGrant(_ grantPath: String, grantSHA: String, root: URL,
                                    expectedSurface: String, bundleID: String) throws -> [String: Any] {
    guard grantPath.hasPrefix("harness-development/") else {
        throw FrameSupportCommandError.refused("--grant must name a task-local v2 grant")
    }
    let grantURL = try frameSupportFileURL(root: root, relativePath: grantPath)
    let grantData = try frameSupportReadBoundedFile(grantURL, name: "execution grant")
    guard grantData.count <= 16 * 1024 * 1024, EvidenceIO.sha256Hex(grantData) == grantSHA,
          let grant = try JSONSerialization.jsonObject(with: grantData) as? [String: Any] else {
        throw FrameSupportCommandError.refused("execution grant bytes or SHA-256 are invalid")
    }
    if grant["grant_version"] as? String == "line-two-album-project-grant-1" {
        guard bundleID == "jp.naver.line.mac" else {
            throw FrameSupportCommandError.refused("pilot producer is restricted to LINE")
        }
        return try PilotNativeAuthority.verify(root: root, grantPath: grantPath, grantSHA: grantSHA,
            surface: expectedSurface, sessionID: optionValue("--session-id"))
    }
    let grantKeys: Set<String> = ["grant_version", "task_id", "project_root", "fixture", "artifact_dir", "owner", "operations",
        "config_sha256", "source_sha256", "album_quota", "lifecycle_album_limit", "save_all_dispatch_limit",
        "chooser_confirmation_limit", "reversible_gui_invocation_limit", "authorization_evidence", "acceptance_evidence",
        "contract_sha256", "native_binary_sha256", "gui_ledger", "contract_path", "producer_binary", "runtime_binding", "sensor_scope"]
    let expectedContractPath = "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan-contract.json"
    let expectedContractSHA = "d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219"
    guard Set(grant.keys) == grantKeys,
          grant["grant_version"] as? String == "line-batch-execution-grant-2",
          grant["task_id"] as? String == "TASK-20261010-line-v3-live-e2e",
          grant["project_root"] as? String == root.path, grant["fixture"] as? Bool == false,
          grant["contract_path"] as? String == expectedContractPath,
          grant["contract_sha256"] as? String == expectedContractSHA,
          grant["artifact_dir"] as? String == "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03",
          (grant["operations"] as? [String])?.contains("frame_support") == true else {
        throw FrameSupportCommandError.refused("execution grant is not the frozen v2 authority for frame-support")
    }
    let contractURL = try frameSupportFileURL(root: root, relativePath: expectedContractPath)
    let contractData = try frameSupportReadBoundedFile(contractURL, name: "frozen plan contract")
    guard EvidenceIO.sha256Hex(contractData) == expectedContractSHA else {
        throw FrameSupportCommandError.refused("frozen plan contract drifted")
    }
    guard let scope = grant["sensor_scope"] as? [String: Any],
          Set(scope.keys) == Set(["bundle_id", "provider", "capture_scope", "surfaces", "menu_capture_guard"]),
          scope["bundle_id"] as? String == bundleID,
          scope["provider"] as? String == "SCREEN_CAPTURE_KIT",
          scope["capture_scope"] as? String == "FULL_DISPLAY",
          scope["menu_capture_guard"] as? Bool == true,
          (scope["surfaces"] as? [String])?.contains(expectedSurface) == true else {
        throw FrameSupportCommandError.refused("sensor scope does not authorize this LINE surface")
    }

    let runtimeRef = try frameSupportRef(grant["runtime_binding"], name: "runtime_binding")
    let runtimeData = try frameSupportReadRef(runtimeRef, root: root, name: "runtime binding")
    guard let runtime = try JSONSerialization.jsonObject(with: runtimeData) as? [String: Any],
          runtime["task_id"] as? String == (grant["task_id"] as? String),
          runtime["project_root"] as? String == root.path,
          runtime["contract_path"] as? String == expectedContractPath,
          runtime["contract_sha256"] as? String == expectedContractSHA,
          runtime["source_sha256"] as? String == (grant["source_sha256"] as? String) else {
        throw FrameSupportCommandError.refused("runtime binding is not for the frozen task contract")
    }
    guard let runtimeFiles = runtime["files"] as? [[String: Any]], !runtimeFiles.isEmpty else {
        throw FrameSupportCommandError.refused("runtime manifest has no closed file inventory")
    }
    var checkedRuntimePaths = Set<String>()
    for entry in runtimeFiles {
        guard Set(entry.keys) == Set(["path", "bytes", "sha256", "member_of"]),
              let path = entry["path"] as? String, checkedRuntimePaths.insert(path).inserted,
              let expectedBytes = entry["bytes"] as? Int, expectedBytes > 0,
              let expectedSHA = entry["sha256"] as? String,
              expectedSHA.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil,
              let members = entry["member_of"] as? [String], !members.isEmpty else {
            throw FrameSupportCommandError.refused("runtime manifest entry is malformed or duplicated")
        }
        let inputURL: URL
        if path.hasPrefix("/") {
            guard path.hasPrefix("/opt/homebrew/Cellar/python@"), members == ["python_runtime"] else {
                throw FrameSupportCommandError.refused("runtime manifest has an unauthorized external path")
            }
            inputURL = URL(fileURLWithPath: path)
            guard inputURL.standardizedFileURL.path == path,
                  (try inputURL.resourceValues(forKeys: [.isSymbolicLinkKey])).isSymbolicLink != true else {
                throw FrameSupportCommandError.refused("external runtime path is not canonical")
            }
        } else {
            inputURL = try frameSupportFileURL(root: root, relativePath: path)
        }
        let input = try frameSupportReadBoundedFile(inputURL, name: "runtime source")
        guard input.count == expectedBytes, EvidenceIO.sha256Hex(input) == expectedSHA else {
            throw FrameSupportCommandError.refused("runtime source changed after its binding was frozen")
        }
    }

    let binary = try frameSupportRef(grant["producer_binary"], name: "producer_binary")
    guard binary.path == "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/bin/rev28ctl",
          let runtimeFiles = runtime["files"] as? [[String: Any]],
          runtimeFiles.contains(where: { $0["path"] as? String == binary.path
              && $0["bytes"] as? Int == binary.bytes && $0["sha256"] as? String == binary.sha256
              && ($0["member_of"] as? [String])?.contains("producer_binary") == true }) else {
        throw FrameSupportCommandError.refused("producer binary is not bound by the runtime manifest")
    }
    let binaryURL = try frameSupportFileURL(root: root, relativePath: binary.path)
    let runningURL = URL(fileURLWithPath: CommandLine.arguments[0], relativeTo: URL(fileURLWithPath: FileManager.default.currentDirectoryPath))
        .standardizedFileURL.resolvingSymlinksInPath()
    guard runningURL == binaryURL,
          try frameSupportReadRef(binary, root: root, name: "producer binary").count == binary.bytes else {
        throw FrameSupportCommandError.refused("running rev28ctl binary does not match the grant-bound producer")
    }

    let authorizationRef = try frameSupportRef(grant["authorization_evidence"], name: "authorization_evidence")
    guard authorizationRef.path == "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/authorization.json" else {
        throw FrameSupportCommandError.refused("authorization evidence is outside this continuation")
    }
    let authorizationData = try frameSupportReadRef(authorizationRef, root: root, name: "authorization evidence")
    guard let authorization = try JSONSerialization.jsonObject(with: authorizationData) as? [String: Any],
          authorization["task_id"] as? String == (grant["task_id"] as? String),
          authorization["project_root"] as? String == root.path,
          authorization["artifact_dir"] as? String == "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03",
          authorization["contract_path"] as? String == expectedContractPath,
          authorization["source_sha256"] as? String == (grant["source_sha256"] as? String),
          authorization["contract_sha256"] as? String == expectedContractSHA,
          authorization["decision_code"] as? String == "A",
          authorization["plan_review_decision"] as? String == "USER_WAIVED_NOT_RUN",
          authorization["independent_acceptance_required"] as? Bool == true,
          authorization["album_quota"] as? Int == grant["album_quota"] as? Int,
          authorization["config_albums_per_lifecycle"] as? Int == grant["lifecycle_album_limit"] as? Int,
          authorization["save_all_dispatch_cap"] as? Int == grant["save_all_dispatch_limit"] as? Int,
          authorization["chooser_confirmation_cap"] as? Int == grant["chooser_confirmation_limit"] as? Int,
          authorization["additional_reversible_gui_invocation_cap"] as? Int == grant["reversible_gui_invocation_limit"] as? Int,
          (authorization["authorized_owners"] as? [String])?.contains(grant["owner"] as? String ?? "") == true,
          let authScope = authorization["sensor_scope"] as? [String: Any],
          authScope["bundle_id"] as? String == bundleID,
          authScope["provider"] as? String == "SCREEN_CAPTURE_KIT",
          authScope["capture_scope"] as? String == "FULL_DISPLAY",
          authScope["menu_capture_guard"] as? Bool == true,
          (authScope["surfaces"] as? [String]) == (scope["surfaces"] as? [String]) else {
        throw FrameSupportCommandError.refused("authorization evidence does not bind this grant and contract")
    }
    return grant
}

private func runFrameSupportCapture(arguments: [String]) async throws -> FrameSupportCaptureReceipt {
    let projectRootPath = try frameSupportOption("--project-root")
    let grantPath = try frameSupportOption("--grant")
    let grantSHA = try frameSupportOption("--grant-sha256")
    let outputPath = try frameSupportOption("--output")
    let bundleID = try frameSupportOption("--bundle-id")
    let sessionID = try frameSupportOption("--session-id")
    let expectedSurface = try frameSupportOption("--surface")
    let layoutKey = try frameSupportOption("--layout-key")
    let pairFramePath = try frameSupportOption("--pair-frame")
    let pairFrameID = try frameSupportOption("--pair-frame-id")
    let geometryPath = try frameSupportOption("--geometry-evidence")
    let geometrySHA = try frameSupportOption("--geometry-evidence-sha256")
    let cuaCapturedAt = try frameSupportOption("--cua-captured-at")
    let pidValue = try frameSupportInteger("--pid")
    let windowIDValue = try frameSupportInteger("--window-id")
    let displayIDValue = try frameSupportInteger("--display-id")
    let cuaBounds = try frameSupportList("--cua-bounds", count: 4)
    guard ["ALBUMS", "ALBUM_DETAIL", "FOLDER_CHOOSER"].contains(expectedSurface),
          pairFrameID.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil,
          grantSHA.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil,
          geometrySHA.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else {
        throw FrameSupportCommandError.refused("surface, frame identity, and authority hashes must be recognized")
    }

    let projectRoot = URL(fileURLWithPath: projectRootPath).standardizedFileURL.resolvingSymlinksInPath()
    let grant = try frameSupportVerifyGrant(grantPath, grantSHA: grantSHA, root: projectRoot,
        expectedSurface: expectedSurface, bundleID: bundleID)
    guard let owner = grant["owner"] as? String, !owner.isEmpty else {
        throw FrameSupportCommandError.refused("execution grant owner is missing")
    }
    let output = projectRoot.appendingPathComponent(outputPath).standardizedFileURL
    let evidencePrefix = grant["grant_version"] as? String == "line-two-album-project-grant-1"
        ? PilotNativeAuthority.directory + "/evidence/"
        : "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/"
    guard outputPath.hasPrefix(evidencePrefix),
          output.path.hasPrefix(projectRoot.path + "/"),
          !outputPath.split(separator: "/").contains("..") else {
        throw FrameSupportCommandError.refused("--output must stay under the selected project's harness-development directory")
    }
    var isDirectory: ObjCBool = false
    guard FileManager.default.fileExists(atPath: output.path, isDirectory: &isDirectory), isDirectory.boolValue,
          output.resolvingSymlinksInPath() == output else {
        throw FrameSupportCommandError.refused("--output must be an existing non-symlink directory")
    }
    guard try FileManager.default.contentsOfDirectory(atPath: output.path).isEmpty else {
        throw FrameSupportCommandError.refused("--output must be empty; use a new evidence directory for every attempt")
    }

    let pairURL = try frameSupportFileURL(root: projectRoot, relativePath: pairFramePath)
    guard let pairBytes = try pairURL.resourceValues(forKeys: [.fileSizeKey]).fileSize, pairBytes > 0 else {
        throw FrameSupportCommandError.refused("retained CUA frame has no readable file size")
    }
    let pairRef = AlbumSupportArtifactRef(path: pairFramePath, bytes: pairBytes, sha256: pairFrameID)
    let pairData = try frameSupportReadRef(pairRef, root: projectRoot, name: "retained CUA frame")
    let pairImage = try albumSupportDecodeImage(pairData)
    guard let cuaDate = albumSupportISO8601.date(from: cuaCapturedAt), abs(Date().timeIntervalSince(cuaDate)) <= 5 else {
        throw FrameSupportCommandError.refused("retained CUA frame is outside the five-second pre-capture window")
    }

    let geometryURL = try frameSupportFileURL(root: projectRoot, relativePath: geometryPath)
    guard let geometryBytes = try geometryURL.resourceValues(forKeys: [.fileSizeKey]).fileSize, geometryBytes > 0 else {
        throw FrameSupportCommandError.refused("same-capture geometry evidence has no readable file size")
    }
    let geometryRef = AlbumSupportArtifactRef(path: geometryPath, bytes: geometryBytes, sha256: geometrySHA)
    let geometryData = try frameSupportReadRef(geometryRef, root: projectRoot, name: "same-capture geometry evidence")
    guard let geometry = try JSONSerialization.jsonObject(with: geometryData) as? [String: Any],
          Set(geometry.keys) == Set(["version", "frame_id", "session_id", "surface", "pid", "window_id", "layout_key",
            "captured_at", "cua_capture_bounds_points", "surface_bounds_px", "ax_state", "layout_signature", "structure_sha256"]),
          geometry["version"] as? Int == 1, geometry["frame_id"] as? String == pairFrameID,
          geometry["session_id"] as? String == sessionID, geometry["surface"] as? String == expectedSurface,
          geometry["pid"] as? Int == pidValue, geometry["window_id"] as? Int == windowIDValue,
          geometry["layout_key"] as? String == layoutKey, geometry["captured_at"] as? String == cuaCapturedAt,
          let evidenceBounds = geometry["cua_capture_bounds_points"] as? [Double], evidenceBounds == cuaBounds,
          let surfaceBounds = geometry["surface_bounds_px"] as? [Double],
          let layout = geometry["layout_signature"] as? [String: Any],
          Set(layout.keys) == Set(["line_version", "language", "window_class", "frame_width_px", "frame_height_px", "native_scale", "structure_sha256"]),
          layout["frame_width_px"] as? Int == pairImage.width, layout["frame_height_px"] as? Int == pairImage.height,
          let structureSHA = geometry["structure_sha256"] as? String, structureSHA == layout["structure_sha256"] as? String,
          let lineVersion = layout["line_version"] as? String, !lineVersion.isEmpty,
          let language = layout["language"] as? String, !language.isEmpty,
          let windowClass = layout["window_class"] as? String, !windowClass.isEmpty,
          let nativeScale = layout["native_scale"] as? Double, nativeScale.isFinite, nativeScale > 0 else {
        throw FrameSupportCommandError.refused("same-capture geometry evidence does not bind the requested frame, surface, or layout")
    }
    let canonicalLayout = try JSONSerialization.data(withJSONObject: layout, options: [.sortedKeys, .withoutEscapingSlashes])
    guard EvidenceIO.sha256Hex(canonicalLayout) == layoutKey else {
        throw FrameSupportCommandError.refused("layout_key is not derived from the stable structural layout signature")
    }
    let axRef = try frameSupportRef(geometry["ax_state"], name: "ax_state")
    _ = try frameSupportReadRef(axRef, root: projectRoot, name: "retained AX snapshot")

    let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
    let displays = content.displays.filter { Int($0.displayID) == displayIDValue }
    guard displays.count == 1, let display = displays.first else {
        throw FrameSupportCommandError.refused("--display-id does not resolve to exactly one fresh display")
    }
    let windows = content.windows.filter { Int($0.windowID) == windowIDValue }
    guard windows.count == 1, let window = windows.first else {
        throw FrameSupportCommandError.refused("--window-id does not resolve to exactly one fresh window")
    }
    guard let app = window.owningApplication, Int(app.processID) == pidValue, app.bundleIdentifier == bundleID else {
        throw FrameSupportCommandError.refused("fresh native window owner does not match the granted LINE bundle and PID")
    }
    let windowBounds = albumSupportRectArray(window.frame)
    guard zip(windowBounds, cuaBounds).allSatisfy({ abs($0.0 - $0.1) <= 1 }),
          display.frame.contains(window.frame) else {
        throw FrameSupportCommandError.refused("CUA/window/display geometry is not a unique current alignment")
    }
    guard let clientScale = FrameCaptureSupport.backingScaleFactor(forWindowFrame: window.frame),
          clientScale.isFinite, abs(clientScale - nativeScale) <= 0.01 else {
        throw FrameSupportCommandError.refused("fresh native backing scale differs from the same-capture layout signature")
    }

    let claim = AlbumSupportClaim(version: 1, mode: "frame-support", output: outputPath, pairFrameId: pairFrameID,
        sessionId: sessionID, pid: Int32(pidValue), windowId: UInt32(windowIDValue), displayId: UInt32(displayIDValue),
        layoutKey: layoutKey, claimedAt: EvidenceIO.iso8601(), status: "CLAIMED")
    try albumSupportClaim(try EvidenceIO.encodeJSON(claim), at: output.appendingPathComponent("claim.json"))

    let cuaItems = try await VisionOcrEngine().recognize(image: pairImage)
    let service = await FrameCaptureService(ruleBook: nil)
    let captured = try await service.captureFullDisplayRetained(display: display, configuration: .fullDisplayPopup)
    guard let captureTiming = captured.record.fullDisplayCaptureTiming,
          let sckStart = albumSupportISO8601.date(from: captureTiming.requestStartedAtISO8601),
          let sckEnd = albumSupportISO8601.date(from: captureTiming.requestFinishedAtISO8601),
          captureTiming.durationMilliseconds.isFinite, captureTiming.durationMilliseconds >= 0,
          sckStart >= cuaDate, sckEnd >= sckStart, sckEnd.timeIntervalSince(cuaDate) <= 5 else {
        throw FrameSupportCommandError.refused("native full-display capture missed the original five-second freshness window")
    }
    guard let witness = captured.record.fullDisplayWitness,
          witness.includeMenuBar, witness.sourceRectAbsent,
          let sckData = FrameCaptureSupport.pngData(of: captured.image), sckData.count <= 16 * 1024 * 1024 else {
        throw FrameSupportCommandError.refused("retained full-display SCK image lacks its witness or exceeds the evidence cap")
    }
    let sckFrameSHA = EvidenceIO.sha256Hex(sckData)
    guard sckFrameSHA != pairFrameID else { throw FrameSupportCommandError.refused("CUA and SCK frame identities are ambiguous") }
    try albumSupportSyncWrite(sckData, to: output.appendingPathComponent("sck-frame.png"))
    let sckFrameRef = AlbumSupportArtifactRef(path: outputPath + "/sck-frame.png", bytes: sckData.count, sha256: sckFrameSHA)
    let sckItems = try await VisionOcrEngine().recognize(image: captured.image)
    let binding = AlbumSupportNativeBinding(bundleId: bundleID, pid: Int32(pidValue), windowId: UInt32(windowIDValue),
        displayId: UInt32(displayIDValue), cuaCaptureBoundsPoints: cuaBounds, sckWindowBoundsPoints: windowBounds,
        displayBoundsPoints: albumSupportRectArray(display.frame), cuaSizePx: [pairImage.width, pairImage.height],
        sckSizePx: [captured.image.width, captured.image.height])
    guard let mapping = AlbumSupportMapping(binding: binding) else {
        throw FrameSupportCommandError.refused("native CUA/SCK geometry cannot produce a verified transform")
    }
    let nativeBounds = NativeCaptureBounds(
        cuaCaptureBoundsPoints: CGRect(x: cuaBounds[0], y: cuaBounds[1], width: cuaBounds[2], height: cuaBounds[3]),
        sckWindowBoundsPoints: window.frame, displayBoundsPoints: display.frame,
        cuaSizePixels: CGSize(width: pairImage.width, height: pairImage.height),
        sckSizePixels: CGSize(width: captured.image.width, height: captured.image.height))
    let anchors: AutomaticAnchorMapping
    do { anchors = try AutomaticOcrAnchorMapper.derive(cua: cuaItems, sck: sckItems, native: nativeBounds) }
    catch { throw FrameSupportCommandError.refused("CUA/SCK anchor parity refused: \(error)") }
    let measurement: NonMenuFrameSupportEvaluation.Measurement
    switch NonMenuFrameSupportEvaluation.measure(surfaceBoundsPx: surfaceBounds,
        frameWidthPx: pairImage.width, frameHeightPx: pairImage.height, uncertaintyPx: anchors.uncertaintyPixels) {
    case let .success(value): measurement = value
    case let .failure(error): throw FrameSupportCommandError.refused("non-menu client geometry refused: \(error)")
    }

    let ocrArtifact = AlbumSupportOcrArtifact(cuaFrameId: pairFrameID, sckFrameSha256: sckFrameSHA,
        cua: cuaItems.map(AlbumSupportOcrItem.init(item:)), sck: sckItems.map(AlbumSupportOcrItem.init(item:)))
    let ocrData = try EvidenceIO.encodeJSON(ocrArtifact)
    guard ocrData.count <= 16 * 1024 * 1024 else { throw FrameSupportCommandError.refused("OCR evidence exceeds 16 MiB") }
    try albumSupportSyncWrite(ocrData, to: output.appendingPathComponent("sck-ocr.json"))
    let ocrRef = AlbumSupportArtifactRef(path: outputPath + "/sck-ocr.json", bytes: ocrData.count,
        sha256: EvidenceIO.sha256Hex(ocrData))
    let sidecar = AlbumSupportSidecar(frameId: pairFrameID, sessionId: sessionID, pid: Int32(pidValue),
        windowId: UInt32(windowIDValue), layoutKey: layoutKey, capturedAt: captureTiming.requestStartedAtISO8601,
        sckFrame: sckFrameRef, ocr: ocrRef, nativeBinding: binding, uncertaintyPx: anchors.uncertaintyPixels,
        safeMarginPx: measurement.safeMarginPx, interactiveIntersectionPx: measurement.intersectionPx)
    let sidecarData = try EvidenceIO.encodeJSON(sidecar)
    try albumSupportSyncWrite(sidecarData, to: output.appendingPathComponent("support.json"))
    let supportRef = AlbumSupportArtifactRef(path: outputPath + "/support.json", bytes: sidecarData.count,
        sha256: EvidenceIO.sha256Hex(sidecarData))
    let manifest = FrameSupportManifest(version: 1, producer: "rev28ctl frame-support", projectRoot: projectRoot.path,
        output: outputPath, surface: expectedSurface, pairFrameId: pairFrameID, sckFrameId: sckFrameSHA,
        sessionId: sessionID, pid: Int32(pidValue), windowId: UInt32(windowIDValue), displayId: UInt32(displayIDValue),
        layoutKey: layoutKey, captureKind: "fullDisplayFrame", includeMenuBar: witness.includeMenuBar,
        sourceRectAbsent: witness.sourceRectAbsent, imageWidthPx: captured.image.width, imageHeightPx: captured.image.height,
        pointPixelScale: witness.pointPixelScale, backingScaleFactor: witness.backingScaleFactor,
        contentRect: albumSupportRectArray(witness.contentRectPoints), displayBounds: albumSupportRectArray(display.frame),
        surfaceBoundsPx: surfaceBounds, anchorTexts: anchors.anchors.map(\.text),
        maximumAnchorResidualPx: anchors.maximumResidualSourcePixels, uncertaintyPx: anchors.uncertaintyPixels,
        safeMarginPx: measurement.safeMarginPx, interactiveIntersectionPx: measurement.intersectionPx,
        geometryEvidence: geometryRef, sckFrame: sckFrameRef, ocr: ocrRef, support: supportRef,
        captureRecord: captured.record, captureTiming: captureTiming)
    let manifestData = try EvidenceIO.encodeJSON(manifest)
    guard manifestData.count <= 16 * 1024 * 1024 else {
        throw FrameSupportCommandError.refused("frame-support manifest exceeds 16 MiB")
    }
    try albumSupportSyncWrite(manifestData, to: output.appendingPathComponent("manifest.json"))
    let manifestRef = AlbumSupportArtifactRef(path: outputPath + "/manifest.json", bytes: manifestData.count,
        sha256: EvidenceIO.sha256Hex(manifestData))
    guard Date().timeIntervalSince(cuaDate) <= 5 else {
        throw FrameSupportCommandError.refused("OCR completed after the original frame freshness window; evidence remains diagnostic")
    }
    return FrameSupportCaptureReceipt(provider: "SCREEN_CAPTURE_KIT", surface: expectedSurface,
        pairFrameId: pairFrameID, sckFrameId: sckFrameSHA, sckCapturedAt: captureTiming.requestStartedAtISO8601,
        sessionId: sessionID, reference: supportRef, manifestReference: manifestRef, uncertaintyPx: anchors.uncertaintyPixels,
        safeMarginPx: measurement.safeMarginPx, intersectionPx: measurement.intersectionPx,
        captureRequestMilliseconds: captureTiming.durationMilliseconds)
}

// A computed formatter also works before the command dispatch's terminal exit;
// a top-level stored let below that exit is never initialized by Swift.
private var albumSupportISO8601: ISO8601DateFormatter {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    formatter.timeZone = TimeZone.current
    return formatter
}

private func runAlbumSupportCapture(arguments: [String]) async throws -> AlbumSupportCaptureReceipt {
    let projectRootPath = try albumSupportOption("--project-root", arguments)
    let outputPath = try albumSupportOption("--output", arguments)
    let bundleID = try albumSupportOption("--bundle-id", arguments)
    let sessionID = try albumSupportOption("--session-id", arguments)
    let layoutKey = try albumSupportOption("--layout-key", arguments)
    let pairFramePath = try albumSupportOption("--pair-frame", arguments)
    let pairFrameID = try albumSupportHex("--pair-frame-id", arguments)
    let cuaCapturedAt = try albumSupportOption("--cua-captured-at", arguments)
    let pidValue = try albumSupportInt("--pid", arguments)
    let windowIDValue = try albumSupportInt("--window-id", arguments)
    let displayIDValue = try albumSupportInt("--display-id", arguments)
    let uncertaintyPx = try albumSupportDouble("--uncertainty-px", arguments)
    let cuaBounds = try albumSupportRect("--cua-bounds", arguments)
    let menuBounds = try albumSupportRect("--menu-bounds", arguments)
    let addressableBounds = try albumSupportRect("--addressable-bounds", arguments)
    let saveAllPoint = try albumSupportPoint("--save-all-point", arguments)
    let scope = optionValue("--capture-scope") ?? "fullDisplay"
    guard scope == "fullDisplay" else {
        throw AlbumSupportCommandError.refused("this producer only captures the full-display popup scope")
    }
    guard uncertaintyPx >= 2 else {
        throw AlbumSupportCommandError.refused("--uncertainty-px must be at least 2")
    }

    let projectRoot = URL(fileURLWithPath: projectRootPath).standardizedFileURL.resolvingSymlinksInPath()
    let output = URL(fileURLWithPath: outputPath, relativeTo: projectRoot).standardizedFileURL
    guard output.path.hasPrefix(projectRoot.path + "/") else {
        throw AlbumSupportCommandError.refused("--output must live inside the project root")
    }
    let relativeOutput = String(output.path.dropFirst(projectRoot.path.count + 1))
    if relativeOutput.hasPrefix(PilotNativeAuthority.directory + "/") || optionValue("--grant") != nil {
        guard bundleID == "jp.naver.line.mac",
              relativeOutput.hasPrefix(PilotNativeAuthority.directory + "/evidence/"),
              let grant = optionValue("--grant"), let hash = optionValue("--grant-sha256") else {
            throw AlbumSupportCommandError.refused("pilot menu capture authority required")
        }
        _ = try PilotNativeAuthority.verify(root: projectRoot, grantPath: grant, grantSHA: hash,
            surface: "ALBUM_DETAIL", sessionID: sessionID)
    }
    guard relativeOutput.hasPrefix("harness-development/") else {
        throw AlbumSupportCommandError.refused("--output must live under harness-development/")
    }
    var isDirectory: ObjCBool = false
    guard FileManager.default.fileExists(atPath: output.path, isDirectory: &isDirectory), isDirectory.boolValue else {
        throw AlbumSupportCommandError.refused("--output must be an existing empty directory")
    }
    let existing = try FileManager.default.contentsOfDirectory(atPath: output.path)
    guard existing.isEmpty else {
        throw AlbumSupportCommandError.refused("--output must be empty; refusing to reuse \(existing.count) entries")
    }

    guard !pairFramePath.hasPrefix("/"), pairFramePath.hasPrefix("harness-development/") else {
        throw AlbumSupportCommandError.refused("--pair-frame must be a harness-development relative path")
    }
    let pairData = try Data(contentsOf: projectRoot.appendingPathComponent(pairFramePath))
    guard EvidenceIO.sha256Hex(pairData) == pairFrameID else {
        throw AlbumSupportCommandError.refused("--pair-frame-id does not match the retained pair frame bytes")
    }
    let pairImage = try albumSupportDecodeImage(pairData)
    guard let cuaDate = albumSupportISO8601.date(from: cuaCapturedAt) else {
        throw AlbumSupportCommandError.refused("--cua-captured-at must be ISO8601 with fractional seconds")
    }
    guard abs(Date().timeIntervalSince(cuaDate)) <= 5 else {
        throw AlbumSupportCommandError.refused("the CUA pair frame is outside the 5 s popup window")
    }

    let claim = AlbumSupportClaim(version: 1, mode: "capture", output: relativeOutput, pairFrameId: pairFrameID,
        sessionId: sessionID, pid: Int32(pidValue), windowId: UInt32(windowIDValue), displayId: UInt32(displayIDValue),
        layoutKey: layoutKey, claimedAt: EvidenceIO.iso8601(), status: "CLAIMED")
    try albumSupportClaim(try EvidenceIO.encodeJSON(claim), at: output.appendingPathComponent("claim.json"))

    let cuaItems = try await VisionOcrEngine().recognize(image: pairImage)

    let content = try await WindowSensor.shareableContent(onScreenWindowsOnly: true)
    let displays = content.displays.filter { Int($0.displayID) == displayIDValue }
    guard displays.count == 1, let display = displays.first else {
        throw AlbumSupportCommandError.refused("--display-id does not resolve to exactly one display")
    }
    let windows = content.windows.filter { Int($0.windowID) == windowIDValue }
    guard windows.count == 1, let window = windows.first else {
        throw AlbumSupportCommandError.refused("--window-id does not resolve to exactly one window")
    }
    guard let owner = window.owningApplication, Int(owner.processID) == pidValue,
          owner.bundleIdentifier == bundleID else {
        throw AlbumSupportCommandError.refused("the LINE window owner does not match --pid/--bundle-id")
    }
    let windowBounds = albumSupportRectArray(window.frame)
    for index in 0..<4 where abs(windowBounds[index] - cuaBounds[index]) > 1 {
        throw AlbumSupportCommandError.refused("fresh SCWindow bounds drift from --cua-bounds beyond 1 pt")
    }
    guard display.frame.contains(window.frame) else {
        throw AlbumSupportCommandError.refused("the LINE window is not on --display-id")
    }

    let service = await FrameCaptureService(ruleBook: nil)
    let captured = try await service.captureFullDisplayRetained(display: display, configuration: .fullDisplayPopup)
    guard let popupData = FrameCaptureSupport.pngData(of: captured.image) else {
        throw FrameCaptureError.pngEncodingFailed
    }
    let popupSHA = EvidenceIO.sha256Hex(popupData)
    guard popupSHA != pairFrameID else {
        throw AlbumSupportCommandError.refused("popup frame bytes equal the pair frame; refusing an ambiguous identity")
    }
    try albumSupportSyncWrite(popupData, to: output.appendingPathComponent("popup.png"))
    let popupRef = AlbumSupportArtifactRef(path: relativeOutput + "/popup.png", bytes: popupData.count, sha256: popupSHA)

    let sckItems = try await VisionOcrEngine().recognize(image: captured.image)
    let binding = AlbumSupportNativeBinding(bundleId: bundleID, pid: Int32(pidValue), windowId: UInt32(windowIDValue),
        displayId: UInt32(displayIDValue), cuaCaptureBoundsPoints: cuaBounds, sckWindowBoundsPoints: windowBounds,
        displayBoundsPoints: albumSupportRectArray(display.frame), cuaSizePx: [pairImage.width, pairImage.height],
        sckSizePx: [captured.image.width, captured.image.height])
    guard let mapping = AlbumSupportMapping(binding: binding) else {
        throw AlbumSupportCommandError.refused("the native binding cannot produce the CUA/SCK transform")
    }
    let native = NativeCaptureBounds(
        cuaCaptureBoundsPoints: CGRect(x: cuaBounds[0], y: cuaBounds[1], width: cuaBounds[2], height: cuaBounds[3]),
        sckWindowBoundsPoints: window.frame, displayBoundsPoints: display.frame,
        cuaSizePixels: CGSize(width: pairImage.width, height: pairImage.height),
        sckSizePixels: CGSize(width: captured.image.width, height: captured.image.height))
    let anchorMapping: AutomaticAnchorMapping
    do {
        anchorMapping = try AutomaticOcrAnchorMapper.derive(cua: cuaItems, sck: sckItems, native: native)
    } catch {
        throw AlbumSupportCommandError.refused("OCR anchor parity refused: \(error)")
    }
    let measurement: AlbumSupportEvaluation.CaptureMeasurement
    switch AlbumSupportEvaluation.measureCapture(sckItems: sckItems, mapping: mapping,
        menuBoundsCuaPx: menuBounds, addressableBoundsCuaPx: addressableBounds,
        saveAllPointCuaPx: CGPoint(x: saveAllPoint[0], y: saveAllPoint[1]), uncertaintyPx: uncertaintyPx) {
    case let .success(value): measurement = value
    case let .failure(error): throw AlbumSupportCommandError.refused("popup guard measurement refused: \(error)")
    }

    let ocrArtifact = AlbumSupportOcrArtifact(cuaFrameId: pairFrameID, sckFrameSha256: popupSHA,
        cua: cuaItems.map { AlbumSupportOcrItem(item: $0) }, sck: sckItems.map { AlbumSupportOcrItem(item: $0) })
    let ocrData = try EvidenceIO.encodeJSON(ocrArtifact)
    try albumSupportSyncWrite(ocrData, to: output.appendingPathComponent("sck-ocr.json"))
    let ocrRef = AlbumSupportArtifactRef(path: relativeOutput + "/sck-ocr.json", bytes: ocrData.count,
        sha256: EvidenceIO.sha256Hex(ocrData))

    let capturedAt = EvidenceIO.iso8601()
    let sidecar = AlbumSupportSidecar(frameId: pairFrameID, sessionId: sessionID, pid: Int32(pidValue),
        windowId: UInt32(windowIDValue), layoutKey: layoutKey, capturedAt: capturedAt, sckFrame: popupRef,
        ocr: ocrRef, nativeBinding: binding, uncertaintyPx: uncertaintyPx,
        safeMarginPx: measurement.safeMarginPx, interactiveIntersectionPx: measurement.interactiveIntersectionPx)
    let sidecarData = try EvidenceIO.encodeJSON(sidecar)
    try albumSupportSyncWrite(sidecarData, to: output.appendingPathComponent("support.json"))
    let sidecarRef = AlbumSupportArtifactRef(path: relativeOutput + "/support.json", bytes: sidecarData.count,
        sha256: EvidenceIO.sha256Hex(sidecarData))

    let manifest = AlbumSupportManifest(version: 1, producer: "rev28ctl album-support", mode: "capture",
        projectRoot: projectRoot.path, output: relativeOutput, pairFrameId: pairFrameID, popupFrameId: popupSHA,
        popupCapturedAt: capturedAt, sessionId: sessionID, pid: Int32(pidValue), windowId: UInt32(windowIDValue),
        displayId: UInt32(displayIDValue), layoutKey: layoutKey, captureKind: "fullDisplayPopup",
        includeMenuBar: captured.record.fullDisplayWitness?.includeMenuBar ?? false,
        sourceRectAbsent: captured.record.fullDisplayWitness?.sourceRectAbsent ?? false,
        imageWidthPx: captured.image.width, imageHeightPx: captured.image.height,
        pointPixelScale: captured.record.scale, backingScaleFactor: captured.record.backingScaleFactor,
        contentRect: albumSupportRectArray(captured.record.fullDisplayWitness?.contentRectPoints ?? .zero),
        displayBounds: albumSupportRectArray(display.frame),
        anchorTexts: anchorMapping.anchors.map(\.text),
        maximumAnchorResidualPx: anchorMapping.maximumResidualSourcePixels,
        safeMarginPx: measurement.safeMarginPx, interactiveIntersectionPx: measurement.interactiveIntersectionPx,
        sckFrame: popupRef, ocr: ocrRef, captureRecord: captured.record,
        note: "full-display retained popup capture for the SCK menu guard; no GUI was dispatched")
    let manifestData = try EvidenceIO.encodeJSON(manifest)
    try albumSupportSyncWrite(manifestData, to: output.appendingPathComponent("manifest.json"))
    let manifestRef = AlbumSupportArtifactRef(path: relativeOutput + "/manifest.json", bytes: manifestData.count,
        sha256: EvidenceIO.sha256Hex(manifestData))

    return AlbumSupportCaptureReceipt(provider: "SCREEN_CAPTURE_KIT", pairFrameId: pairFrameID,
        popupFrameId: popupSHA, popupCapturedAt: capturedAt, popupSource: "SCREEN_CAPTURE_KIT_FULL_DISPLAY",
        sessionId: sessionID, reference: sidecarRef, manifestReference: manifestRef, uncertaintyPx: uncertaintyPx,
        safeMarginPx: measurement.safeMarginPx, intersectionPx: measurement.interactiveIntersectionPx)
}

private func runAlbumSupportGuard(arguments: [String]) async throws -> AlbumSupportGuardReceipt {
    let projectRootPath = try albumSupportOption("--project-root", arguments)
    let supportPath = try albumSupportOption("--support", arguments)
    let supportSHA = try albumSupportHex("--support-sha256", arguments)
    let pairFrameID = try albumSupportHex("--pair-frame-id", arguments)
    let sessionID = try albumSupportOption("--session-id", arguments)
    let layoutKey = try albumSupportOption("--layout-key", arguments)
    let pidValue = try albumSupportInt("--pid", arguments)
    let windowIDValue = try albumSupportInt("--window-id", arguments)
    let uncertaintyPx = try albumSupportDouble("--uncertainty-px", arguments)
    let saveAllPoint = try albumSupportPoint("--save-all-point", arguments)
    guard !supportPath.hasPrefix("/"), supportPath.hasPrefix("harness-development/") else {
        throw AlbumSupportCommandError.refused("--support must be a harness-development relative path")
    }
    let projectRoot = URL(fileURLWithPath: projectRootPath).standardizedFileURL.resolvingSymlinksInPath()
    let supportData = try Data(contentsOf: projectRoot.appendingPathComponent(supportPath))
    if supportPath.hasPrefix(PilotNativeAuthority.directory + "/") || optionValue("--grant") != nil {
        guard supportPath.hasPrefix(PilotNativeAuthority.directory + "/evidence/"),
              let grant = optionValue("--grant"), let hash = optionValue("--grant-sha256") else {
            throw AlbumSupportCommandError.refused("pilot menu guard authority required")
        }
        _ = try PilotNativeAuthority.verify(root: projectRoot, grantPath: grant, grantSHA: hash,
            surface: "ALBUM_DETAIL", sessionID: sessionID)
    }
    guard EvidenceIO.sha256Hex(supportData) == supportSHA else {
        throw AlbumSupportCommandError.refused("--support-sha256 does not match the retained sidecar bytes")
    }
    let sidecar = try JSONDecoder().decode(AlbumSupportSidecar.self, from: supportData)
    guard sidecar.version == 1, sidecar.provider == "SCREEN_CAPTURE_KIT", sidecar.fixture == false else {
        throw AlbumSupportCommandError.refused("the sidecar is not the live SCREEN_CAPTURE_KIT producer record")
    }
    guard sidecar.frameId == pairFrameID, sidecar.sessionId == sessionID, Int(sidecar.pid) == pidValue,
          Int(sidecar.windowId) == windowIDValue, sidecar.layoutKey == layoutKey else {
        throw AlbumSupportCommandError.refused("the sidecar identity does not match the guard request")
    }
    guard abs(sidecar.uncertaintyPx - uncertaintyPx) < 1e-9, uncertaintyPx >= 2 else {
        throw AlbumSupportCommandError.refused("the guard uncertainty does not match the retained sidecar")
    }
    guard !sidecar.sckFrame.path.hasPrefix("/"), sidecar.sckFrame.path.hasPrefix("harness-development/") else {
        throw AlbumSupportCommandError.refused("the sidecar popup path escapes harness-development/")
    }
    let popupData = try Data(contentsOf: projectRoot.appendingPathComponent(sidecar.sckFrame.path))
    guard popupData.count == sidecar.sckFrame.bytes else {
        throw AlbumSupportCommandError.refused("the retained popup byte count drifted from the sidecar")
    }
    let popupSHA = EvidenceIO.sha256Hex(popupData)
    guard popupSHA == sidecar.sckFrame.sha256 else {
        throw AlbumSupportCommandError.refused("the retained popup bytes drifted from the sidecar hash")
    }
    guard popupSHA != sidecar.frameId else {
        throw AlbumSupportCommandError.refused("the popup frame equals the pair frame")
    }
    guard let mapping = AlbumSupportMapping(binding: sidecar.nativeBinding) else {
        throw AlbumSupportCommandError.refused("the sidecar native binding cannot produce the transform")
    }
    let popupImage = try albumSupportDecodeImage(popupData)
    let sckItems = try await VisionOcrEngine().recognize(image: popupImage)
    let point = CGPoint(x: saveAllPoint[0], y: saveAllPoint[1])
    switch AlbumSupportEvaluation.guardPoint(sckItems: sckItems, mapping: mapping,
        saveAllPointCuaPx: point, uncertaintyPx: uncertaintyPx) {
    case let .success(confirmed):
        return AlbumSupportGuardReceipt(verdict: "PASS", provider: "SCREEN_CAPTURE_KIT", pairFrameId: pairFrameID,
            popupFrameId: popupSHA, supportSha256: supportSHA,
            actionPoint: [Double(confirmed.x), Double(confirmed.y)])
    case let .failure(error):
        throw AlbumSupportCommandError.refused("guard refused: \(error)")
    }
}
