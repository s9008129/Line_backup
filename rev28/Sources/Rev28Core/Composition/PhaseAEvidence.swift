import CoreGraphics
import Foundation

// MARK: - Phase A evidence (plan §PHASE_A, handoff PHASE_A_REQUIREMENTS)
//
// `live-preflight` is observation-only, so Phase A may publish only what a real
// Mac/real LINE run actually observed. Every condition is derived from the raw
// run-directory artifacts plus the OS facts the caller collected; a condition
// that was not observed is UNKNOWN, never a fabricated PASS. The actual LINE
// chooser is deliberately deferred: it is a Phase B runtime gate and is stated
// as such instead of being counted as Phase A proof.

public enum PhaseAConditionStatus: String, Codable, Equatable, Sendable {
    case pass = "PASS"
    case fail = "FAIL"
    case unknown = "UNKNOWN"
}

public struct PhaseACondition: Codable, Equatable, Sendable {
    public let identifier: String
    public let status: PhaseAConditionStatus
    public let detail: String
    public let artifacts: [String]

    public init(identifier: String, status: PhaseAConditionStatus, detail: String, artifacts: [String] = []) {
        self.identifier = identifier
        self.status = status
        self.detail = detail
        self.artifacts = artifacts
    }
}

/// A fact Phase A cannot observe without pretending. It is recorded explicitly
/// so no reader can mistake it for a Phase A PASS.
public struct PhaseADeferredRuntimeGate: Codable, Equatable, Sendable {
    public let identifier: String
    public let status: PhaseAConditionStatus
    public let runtimeGate: String
    public let statement: String

    public init(identifier: String, status: PhaseAConditionStatus, runtimeGate: String, statement: String) {
        self.identifier = identifier
        self.status = status
        self.runtimeGate = runtimeGate
        self.statement = statement
    }
}

public struct PhaseAProcessFacts: Codable, Equatable, Sendable {
    public let bundleID: String?
    public let signingIdentity: String?
    public let startTimeSeconds: Int64?
    public let startTimeMicroseconds: Int32?

    public init(bundleID: String?, signingIdentity: String?, startTimeSeconds: Int64?, startTimeMicroseconds: Int32?) {
        self.bundleID = bundleID
        self.signingIdentity = signingIdentity
        self.startTimeSeconds = startTimeSeconds
        self.startTimeMicroseconds = startTimeMicroseconds
    }
}

public struct PhaseAInventoryFacts: Codable, Equatable, Sendable {
    public let sckWindowCount: Int
    public let cgWindowCount: Int
    public let axWindowCount: Int
    public let targetWindowID: UInt32
    public let targetPresentInSCK: Bool
    public let targetPresentInCG: Bool
    public let axFrameMatchesTarget: Bool

    public init(
        sckWindowCount: Int,
        cgWindowCount: Int,
        axWindowCount: Int,
        targetWindowID: UInt32,
        targetPresentInSCK: Bool,
        targetPresentInCG: Bool,
        axFrameMatchesTarget: Bool
    ) {
        self.sckWindowCount = sckWindowCount
        self.cgWindowCount = cgWindowCount
        self.axWindowCount = axWindowCount
        self.targetWindowID = targetWindowID
        self.targetPresentInSCK = targetPresentInSCK
        self.targetPresentInCG = targetPresentInCG
        self.axFrameMatchesTarget = axFrameMatchesTarget
    }
}

public struct PhaseAFrozenGeometryFacts: Codable, Equatable, Sendable {
    public let captureConfiguration: String
    public let ruleID: String
    public let settled: Bool
    public let activated: Bool
    public let includeChildWindows: Bool
    public let ignoreShadows: Bool
    public let menuBoundsCapture: CGRect
    public let addressableBoundsCapture: CGRect

    public init(
        captureConfiguration: String,
        ruleID: String,
        settled: Bool,
        activated: Bool,
        includeChildWindows: Bool,
        ignoreShadows: Bool,
        menuBoundsCapture: CGRect,
        addressableBoundsCapture: CGRect
    ) {
        self.captureConfiguration = captureConfiguration
        self.ruleID = ruleID
        self.settled = settled
        self.activated = activated
        self.includeChildWindows = includeChildWindows
        self.ignoreShadows = ignoreShadows
        self.menuBoundsCapture = menuBoundsCapture
        self.addressableBoundsCapture = addressableBoundsCapture
    }

    public var isReviewedComposition: Bool {
        settled && activated && !includeChildWindows && ignoreShadows
            && !ruleID.isEmpty
            && menuBoundsCapture.width > 0 && menuBoundsCapture.height > 0
            && addressableBoundsCapture.width > 0 && addressableBoundsCapture.height > 0
    }
}

public struct PhaseATripwireFacts: Codable, Equatable, Sendable {
    public let running: Bool
    public let failure: String?
    public let collectionGap: String?
    public let startedAtMonotonicNanos: UInt64
    public let factCount: Int

    public init(running: Bool, failure: String?, collectionGap: String?, startedAtMonotonicNanos: UInt64, factCount: Int) {
        self.running = running
        self.failure = failure
        self.collectionGap = collectionGap
        self.startedAtMonotonicNanos = startedAtMonotonicNanos
        self.factCount = factCount
    }

    public var isArmed: Bool {
        running && failure == nil && collectionGap == nil && startedAtMonotonicNanos > 0
    }
}

public struct PhaseALedgerCounts: Codable, Equatable, Sendable {
    public let saveAllIntent: Int
    public let saveAllAttempt: Int
    public let destinationIntent: Int
    public let destinationAttempt: Int
    public let ownerSaveAllCount: Int
    public let ownerDestinationCount: Int

    public init(
        saveAllIntent: Int,
        saveAllAttempt: Int,
        destinationIntent: Int,
        destinationAttempt: Int,
        ownerSaveAllCount: Int,
        ownerDestinationCount: Int
    ) {
        self.saveAllIntent = saveAllIntent
        self.saveAllAttempt = saveAllAttempt
        self.destinationIntent = destinationIntent
        self.destinationAttempt = destinationAttempt
        self.ownerSaveAllCount = ownerSaveAllCount
        self.ownerDestinationCount = ownerDestinationCount
    }

    public var isZero: Bool {
        saveAllIntent == 0 && saveAllAttempt == 0
            && destinationIntent == 0 && destinationAttempt == 0
            && ownerSaveAllCount == 0 && ownerDestinationCount == 0
    }
}

public struct PhaseAIrreversibleFacts: Codable, Equatable, Sendable {
    public let saveAllIntent: Int
    public let saveAllAttempt: Int
    public let destinationIntent: Int
    public let destinationAttempt: Int
    public let ownerSaveAllCount: Int
    public let ownerDestinationCount: Int
    public let reversibleDispatches: Int

    public init(
        saveAllIntent: Int,
        saveAllAttempt: Int,
        destinationIntent: Int,
        destinationAttempt: Int,
        ownerSaveAllCount: Int,
        ownerDestinationCount: Int,
        reversibleDispatches: Int
    ) {
        self.saveAllIntent = saveAllIntent
        self.saveAllAttempt = saveAllAttempt
        self.destinationIntent = destinationIntent
        self.destinationAttempt = destinationAttempt
        self.ownerSaveAllCount = ownerSaveAllCount
        self.ownerDestinationCount = ownerDestinationCount
        self.reversibleDispatches = reversibleDispatches
    }

    public var isZeroIrreversible: Bool {
        saveAllIntent == 0 && saveAllAttempt == 0
            && destinationIntent == 0 && destinationAttempt == 0
            && ownerSaveAllCount == 0 && ownerDestinationCount == 0
    }
}

public struct PhaseAEvidenceInputs: Sendable {
    public let authorization: ImmutableRunAuthorization
    public let targetBundleID: String
    public let targetPID: Int32
    public let liveProcess: PhaseAProcessFacts?
    public let axTrusted: Bool
    public let screenCaptureTrusted: Bool
    public let inventory: PhaseAInventoryFacts?
    public let inventoryError: String?
    public let displayScales: [Double]
    public let frozenGeometry: PhaseAFrozenGeometryFacts?
    public let baselineResult: BaselineVerificationResult?
    public let baselineError: String?
    public let stagingSnapshot: StagingSnapshot?
    public let stagingError: String?
    public let tripwire: PhaseATripwireFacts?
    public let tripwireError: String?
    public let prePanelCensus: ChooserCensus?
    public let prePanelCensusArtifactName: String?
    public let prePanelCensusError: String?
    public let preDispatchContextSHA256: String?
    public let ledgerCounts: PhaseALedgerCounts
    public let reversibleDispatches: Int
    public let preflightOutcomeArtifactName: String?

    public init(
        authorization: ImmutableRunAuthorization,
        targetBundleID: String,
        targetPID: Int32,
        liveProcess: PhaseAProcessFacts?,
        axTrusted: Bool,
        screenCaptureTrusted: Bool,
        inventory: PhaseAInventoryFacts?,
        inventoryError: String?,
        displayScales: [Double],
        frozenGeometry: PhaseAFrozenGeometryFacts?,
        baselineResult: BaselineVerificationResult?,
        baselineError: String?,
        stagingSnapshot: StagingSnapshot?,
        stagingError: String?,
        tripwire: PhaseATripwireFacts?,
        tripwireError: String?,
        prePanelCensus: ChooserCensus?,
        prePanelCensusArtifactName: String?,
        prePanelCensusError: String?,
        preDispatchContextSHA256: String?,
        ledgerCounts: PhaseALedgerCounts,
        reversibleDispatches: Int,
        preflightOutcomeArtifactName: String?
    ) {
        self.authorization = authorization
        self.targetBundleID = targetBundleID
        self.targetPID = targetPID
        self.liveProcess = liveProcess
        self.axTrusted = axTrusted
        self.screenCaptureTrusted = screenCaptureTrusted
        self.inventory = inventory
        self.inventoryError = inventoryError
        self.displayScales = displayScales
        self.frozenGeometry = frozenGeometry
        self.baselineResult = baselineResult
        self.baselineError = baselineError
        self.stagingSnapshot = stagingSnapshot
        self.stagingError = stagingError
        self.tripwire = tripwire
        self.tripwireError = tripwireError
        self.prePanelCensus = prePanelCensus
        self.prePanelCensusArtifactName = prePanelCensusArtifactName
        self.prePanelCensusError = prePanelCensusError
        self.preDispatchContextSHA256 = preDispatchContextSHA256
        self.ledgerCounts = ledgerCounts
        self.reversibleDispatches = reversibleDispatches
        self.preflightOutcomeArtifactName = preflightOutcomeArtifactName
    }
}

// MARK: - Raw run-directory facts

public struct PhaseACapturedState: Sendable {
    public let artifactName: String
    public let artifactSHA256: String
    public let artifact: StateEvidenceArtifact
    public let retainedFrameVerified: Bool
    public let retainedFrameDetail: String

    public init(
        artifactName: String,
        artifactSHA256: String,
        artifact: StateEvidenceArtifact,
        retainedFrameVerified: Bool,
        retainedFrameDetail: String
    ) {
        self.artifactName = artifactName
        self.artifactSHA256 = artifactSHA256
        self.artifact = artifact
        self.retainedFrameVerified = retainedFrameVerified
        self.retainedFrameDetail = retainedFrameDetail
    }
}

public struct PhaseAPreDispatchContext: Sendable {
    public let artifactName: String
    public let artifactSHA256: String
    public let observedSeconds: Double
    public let minimumSeconds: Double
    public let collectionGap: String?
    public let journalStartedAtMonotonicNanos: UInt64
    public let factCount: Int
    public let recordedAtISO8601: String

    public init(
        artifactName: String,
        artifactSHA256: String,
        observedSeconds: Double,
        minimumSeconds: Double,
        collectionGap: String?,
        journalStartedAtMonotonicNanos: UInt64,
        factCount: Int,
        recordedAtISO8601: String
    ) {
        self.artifactName = artifactName
        self.artifactSHA256 = artifactSHA256
        self.observedSeconds = observedSeconds
        self.minimumSeconds = minimumSeconds
        self.collectionGap = collectionGap
        self.journalStartedAtMonotonicNanos = journalStartedAtMonotonicNanos
        self.factCount = factCount
        self.recordedAtISO8601 = recordedAtISO8601
    }

    /// The reviewed minimum is 10 seconds; a record carrying a smaller minimum
    /// never counts as meeting it.
    public var effectiveMinimumSeconds: Double { max(minimumSeconds, 10) }

    public var isClean: Bool {
        collectionGap == nil && observedSeconds >= effectiveMinimumSeconds
    }
}

public struct PhaseARunArtifacts: Sendable {
    /// State artifacts sorted by epoch ascending.
    public let states: [PhaseACapturedState]
    public let preDispatchContexts: [PhaseAPreDispatchContext]
    public let malformedArtifactNames: [String]

    public init(
        states: [PhaseACapturedState],
        preDispatchContexts: [PhaseAPreDispatchContext],
        malformedArtifactNames: [String]
    ) {
        self.states = states
        self.preDispatchContexts = preDispatchContexts
        self.malformedArtifactNames = malformedArtifactNames
    }

    public var latestPerState: [String: PhaseACapturedState] {
        var map: [String: PhaseACapturedState] = [:]
        for captured in states {
            if let existing = map[captured.artifact.state], existing.artifact.epoch >= captured.artifact.epoch {
                continue
            }
            map[captured.artifact.state] = captured
        }
        return map
    }

    public var stateArtifactNames: [String] { states.map(\.artifactName) }

    public var targetWindowArtifact: StateEvidenceArtifact? {
        latestPerState[ExecutionState.saveAllLocated.rawValue]?.artifact
    }
}

// MARK: - Report

public struct PhaseAEvidenceReport: Codable, Equatable, Sendable {
    public static let currentVersion = 1

    public let reportVersion: Int
    public let runID: String
    public let generatedAtISO8601: String
    public let conditions: [PhaseACondition]
    public let deferredRuntimeGates: [PhaseADeferredRuntimeGate]
    public let irreversible: PhaseAIrreversibleFacts
    public let ledgerProvenZeroIrreversible: Bool
    /// Condition identifiers that are not PASS. Any entry prevents Phase B.
    public let phaseBPreventedBy: [String]
    public let chooserAssumptionStatement: String
    public let preflightOutcomeArtifactName: String?
    public let rawEvidenceManifestName: String

    public var allConditionsPass: Bool { phaseBPreventedBy.isEmpty }

    public var statusCounts: (pass: Int, fail: Int, unknown: Int) {
        var pass = 0, fail = 0, unknown = 0
        for condition in conditions {
            switch condition.status {
            case .pass: pass += 1
            case .fail: fail += 1
            case .unknown: unknown += 1
            }
        }
        return (pass, fail, unknown)
    }
}

public struct PhaseARawEvidenceManifest: Codable, Equatable, Sendable {
    public struct Entry: Codable, Equatable, Sendable {
        public let name: String
        public let bytes: Int
        public let sha256: String

        public init(name: String, bytes: Int, sha256: String) {
            self.name = name
            self.bytes = bytes
            self.sha256 = sha256
        }
    }

    public let manifestVersion: Int
    public let runID: String
    public let generatedAtISO8601: String
    public let entries: [Entry]

    public init(manifestVersion: Int, runID: String, generatedAtISO8601: String, entries: [Entry]) {
        self.manifestVersion = manifestVersion
        self.runID = runID
        self.generatedAtISO8601 = generatedAtISO8601
        self.entries = entries
    }
}

public struct PhaseAPublishedArtifacts: Codable, Equatable, Sendable {
    public let reportName: String
    public let reportSHA256: String
    public let manifestName: String
    public let manifestSHA256: String
    public let manifestEntryCount: Int
    public let phaseBPreventedBy: [String]
    public let passCount: Int
    public let failCount: Int
    public let unknownCount: Int

    public init(
        reportName: String,
        reportSHA256: String,
        manifestName: String,
        manifestSHA256: String,
        manifestEntryCount: Int,
        phaseBPreventedBy: [String],
        passCount: Int,
        failCount: Int,
        unknownCount: Int
    ) {
        self.reportName = reportName
        self.reportSHA256 = reportSHA256
        self.manifestName = manifestName
        self.manifestSHA256 = manifestSHA256
        self.manifestEntryCount = manifestEntryCount
        self.phaseBPreventedBy = phaseBPreventedBy
        self.passCount = passCount
        self.failCount = failCount
        self.unknownCount = unknownCount
    }
}

// MARK: - Builder

public enum PhaseAEvidenceBuilder {
    /// Every Phase A condition, in report order. All of them are always emitted.
    public static let conditionIdentifiers: [String] = [
        "REAL_PROCESS_SIGNATURE_START",
        "EXECUTABLE_CONTEXT_TCC",
        "SCK_CG_AX_INVENTORY",
        "DISPLAY_BACKING_SCALE",
        "FROZEN_CAPTURE_GEOMETRY",
        "SAME_FRAME_VISION",
        "TARGET_GROUP_DATE_COUNT_ASSOCIATION",
        "ALBUM_REVERIFICATION",
        "ELLIPSIS_AND_FIVE_ROW_MENU_LOCALIZATION",
        "POPUP_OCCLUSION_ASSUMPTIONS",
        "PRE_PANEL_CENSUS",
        "BASELINE_INTEGRITY",
        "STAGING_EVIDENCE_SEPARATION",
        "NATIVE_TRIPWIRE_READINESS",
        "PRE_DISPATCH_CONTEXT_10S",
        "LEDGER_ZERO_IRREVERSIBLE",
    ]

    public static let deferredRuntimeGateIdentifiers: [String] = ["ACTUAL_LINE_CHOOSER_OBSERVED"]

    public static let chooserAssumptionStatement =
        "chooser assumptions calibrated on real NSOpenPanel, actual LINE chooser not yet observed"

    /// Reads the raw run directory: state artifacts with their retained frames,
    /// and the pre-dispatch context records. Malformed artifacts are named, not
    /// silently skipped.
    public static func inspect(runDirectory: URL) throws -> PhaseARunArtifacts {
        let names = try FileManager.default.contentsOfDirectory(atPath: runDirectory.path).sorted()
        var states: [PhaseACapturedState] = []
        var malformed: [String] = []
        for name in names where name.hasPrefix("state-") && name.hasSuffix(".json") {
            let url = runDirectory.appendingPathComponent(name)
            guard let data = try? Data(contentsOf: url),
                  let artifact = try? JSONDecoder().decode(StateEvidenceArtifact.self, from: data) else {
                malformed.append(name)
                continue
            }
            let frameURL = runDirectory.appendingPathComponent(artifact.retainedFrameName)
            let frameSHA = try? EvidenceIO.sha256Hex(ofFileAt: frameURL)
            let verified = frameSHA != nil && frameSHA == artifact.frameSHA256
            let detail: String
            if frameSHA == nil {
                detail = "retained frame \(artifact.retainedFrameName) is missing"
            } else if verified {
                detail = "retained frame \(artifact.retainedFrameName) matches \(artifact.frameSHA256)"
            } else {
                detail = "retained frame \(artifact.retainedFrameName) does not match the recorded SHA"
            }
            states.append(PhaseACapturedState(
                artifactName: name,
                artifactSHA256: EvidenceIO.sha256Hex(data),
                artifact: artifact,
                retainedFrameVerified: verified,
                retainedFrameDetail: detail
            ))
        }
        var contexts: [PhaseAPreDispatchContext] = []
        for name in names where name.hasPrefix("pre-dispatch-context-") && name.hasSuffix(".json") && !name.contains("-refused-") {
            let url = runDirectory.appendingPathComponent(name)
            guard let data = try? Data(contentsOf: url),
                  let record = try? JSONDecoder().decode(PreDispatchContextRecord.self, from: data) else {
                malformed.append(name)
                continue
            }
            contexts.append(PhaseAPreDispatchContext(
                artifactName: name,
                artifactSHA256: EvidenceIO.sha256Hex(data),
                observedSeconds: record.observedSeconds,
                minimumSeconds: record.minimumSeconds,
                collectionGap: record.collectionGap,
                journalStartedAtMonotonicNanos: record.journalStartedAtMonotonicNanos,
                factCount: record.factCount,
                recordedAtISO8601: record.recordedAtISO8601
            ))
        }
        return PhaseARunArtifacts(
            states: states.sorted { $0.artifact.epoch < $1.artifact.epoch },
            preDispatchContexts: contexts,
            malformedArtifactNames: malformed
        )
    }

    public static func build(
        inputs: PhaseAEvidenceInputs,
        inspection: PhaseARunArtifacts,
        generatedAtISO8601: String
    ) -> PhaseAEvidenceReport {
        let latest = inspection.latestPerState
        var conditions: [PhaseACondition] = []

        // 1. Real process/signature/start, bound to every captured state.
        do {
            let artifacts = inspection.states
            if let live = inputs.liveProcess {
                let identityMatch = live.bundleID == inputs.targetBundleID
                    && live.signingIdentity?.isEmpty == false
                    && live.startTimeSeconds != nil
                    && live.startTimeMicroseconds != nil
                let boundToArtifacts = !artifacts.isEmpty && artifacts.allSatisfy { captured in
                    captured.artifact.pid == inputs.targetPID
                        && captured.artifact.bundleID == inputs.targetBundleID
                        && captured.artifact.processStartSeconds == (live.startTimeSeconds ?? -1)
                        && captured.artifact.processStartMicroseconds == (live.startTimeMicroseconds ?? -1)
                }
                let detail = "pid=\(inputs.targetPID) bundleID=\(live.bundleID ?? "nil") "
                    + "signing=\(live.signingIdentity ?? "nil") "
                    + "start=\(live.startTimeSeconds.map(String.init) ?? "nil").\(live.startTimeMicroseconds.map(String.init) ?? "nil") "
                    + "stateArtifacts=\(artifacts.count) boundToArtifacts=\(boundToArtifacts)"
                conditions.append(PhaseACondition(
                    identifier: "REAL_PROCESS_SIGNATURE_START",
                    status: identityMatch && boundToArtifacts ? .pass : .fail,
                    detail: detail,
                    artifacts: inspection.stateArtifactNames
                ))
            } else {
                conditions.append(PhaseACondition(
                    identifier: "REAL_PROCESS_SIGNATURE_START",
                    status: .fail,
                    detail: "live process facts unavailable for pid=\(inputs.targetPID)"
                ))
            }
        }

        // 2. Executable-context TCC (AX + screen recording), from this process.
        conditions.append(PhaseACondition(
            identifier: "EXECUTABLE_CONTEXT_TCC",
            status: inputs.axTrusted && inputs.screenCaptureTrusted ? .pass : .fail,
            detail: "AXIsProcessTrusted=\(inputs.axTrusted) screenCaptureGranted=\(inputs.screenCaptureTrusted)"
        ))

        // 3. SCK/CG/AX inventories agree on the target window.
        if let inventory = inputs.inventory {
            let ok = inventory.sckWindowCount > 0
                && inventory.cgWindowCount > 0
                && inventory.axWindowCount > 0
                && inventory.targetPresentInSCK
                && inventory.targetPresentInCG
                && inventory.axFrameMatchesTarget
            let detail = "sck=\(inventory.sckWindowCount) cg=\(inventory.cgWindowCount) ax=\(inventory.axWindowCount) "
                + "targetWindowID=\(inventory.targetWindowID) inSCK=\(inventory.targetPresentInSCK) "
                + "inCG=\(inventory.targetPresentInCG) axFrameMatches=\(inventory.axFrameMatchesTarget)"
            conditions.append(PhaseACondition(
                identifier: "SCK_CG_AX_INVENTORY",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [latest[ExecutionState.saveAllLocated.rawValue]?.artifactName].compactMap { $0 }
            ))
        } else {
            conditions.append(PhaseACondition(
                identifier: "SCK_CG_AX_INVENTORY",
                status: .fail,
                detail: "inventory probe unavailable: \(inputs.inventoryError ?? "not run")"
            ))
        }

        // 4. Display/backing scale, resolved for every captured window frame.
        do {
            let scales = inputs.displayScales
            let ok = scales.count == 1 && !inspection.states.isEmpty
            let rendered = scales.map { String(format: "%.2f", $0) }.joined(separator: ",")
            conditions.append(PhaseACondition(
                identifier: "DISPLAY_BACKING_SCALE",
                status: ok ? .pass : .fail,
                detail: "resolvedScales=[\(rendered)] over \(inspection.states.count) state frames"
                    + (scales.isEmpty ? " (no state frame resolved a backing scale)" : "")
            ))
        }

        // 5. Frozen capture geometry recorded from the reviewed composition.
        if let geometry = inputs.frozenGeometry {
            let framesOK = !inspection.states.isEmpty && inspection.states.allSatisfy {
                $0.artifact.windowFrame.width > 0 && $0.artifact.windowFrame.height > 0
            }
            let ok = geometry.isReviewedComposition && framesOK
            let detail = "captureConfiguration=\(geometry.captureConfiguration) ruleID=\(geometry.ruleID) "
                + "settled=\(geometry.settled) activated=\(geometry.activated) includeChildWindows=\(geometry.includeChildWindows) "
                + "ignoreShadows=\(geometry.ignoreShadows) menuBounds=\(geometry.menuBoundsCapture) "
                + "addressableBounds=\(geometry.addressableBoundsCapture) nonzeroStateFrames=\(framesOK)"
            conditions.append(PhaseACondition(
                identifier: "FROZEN_CAPTURE_GEOMETRY",
                status: ok ? .pass : .fail,
                detail: detail
            ))
        } else {
            conditions.append(PhaseACondition(
                identifier: "FROZEN_CAPTURE_GEOMETRY",
                status: .fail,
                detail: "frozen capture geometry facts were not recorded"
            ))
        }

        // 6. Same-frame Vision: every retained PNG matches its artifact hash and
        // the OCR-bearing states carry the texts the policy requires.
        do {
            let framesVerified = !inspection.states.isEmpty && inspection.states.allSatisfy(\.retainedFrameVerified)
            let ocrRequirement: [(ExecutionState, [String])] = [
                (.groupReady, [LiveExecutionEngine.targetGroup]),
                (.albumDetailVerified, [LiveExecutionEngine.targetGroup, "57張照片"]),
                (.menuVerified, StructuralLocators.lineAlbumMenuReference),
            ]
            var missing: [String] = []
            for (state, texts) in ocrRequirement {
                guard let captured = latest[state.rawValue] else {
                    missing.append("\(state.rawValue):artifact-missing")
                    continue
                }
                for text in texts where !captured.artifact.ocrTexts.contains(text) {
                    missing.append("\(state.rawValue):\(text)")
                }
            }
            let malformed = inspection.malformedArtifactNames
            let ok = framesVerified && missing.isEmpty && malformed.isEmpty
            let detail = "framesVerified=\(inspection.states.count) allVerified=\(framesVerified) "
                + "missingOcr=\(missing.isEmpty ? "none" : missing.joined(separator: ";")) "
                + "malformed=\(malformed.isEmpty ? "none" : malformed.joined(separator: ","))"
            conditions.append(PhaseACondition(
                identifier: "SAME_FRAME_VISION",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: inspection.stateArtifactNames
            ))
        }

        // 7. Exact group/date/count association plus card association.
        do {
            let suffix = ":2024/05/13~05/17|57"
            let group = latest[ExecutionState.groupReady.rawValue]
            let located = latest[ExecutionState.targetAlbumLocated.rawValue]
            let groupOK = group?.artifact.ocrTexts.contains(LiveExecutionEngine.targetGroup) == true
            let identityOK = located?.artifact.candidateRefusal == nil
                && located?.artifact.candidateIdentity?.hasSuffix(suffix) == true
            let cardOK = located.map { $0.artifact.cardRegionCount >= 1 } == true
            let ok = groupOK && identityOK && cardOK
            let detail = "groupOcr=\(groupOK ? "present" : "missing") "
                + "albumCandidate=\(located?.artifact.candidateIdentity ?? "none") expectedSuffix=\(suffix) "
                + "cardRegionCount=\(located?.artifact.cardRegionCount ?? -1)"
            conditions.append(PhaseACondition(
                identifier: "TARGET_GROUP_DATE_COUNT_ASSOCIATION",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [group?.artifactName, located?.artifactName].compactMap { $0 }
            ))
        }

        // 8. Album re-verification after navigation (fresh detail capture).
        do {
            let verified = latest[ExecutionState.albumDetailVerified.rawValue]
            let located = latest[ExecutionState.targetAlbumLocated.rawValue]
            let textsOK = verified.map {
                $0.artifact.ocrTexts.contains(LiveExecutionEngine.targetGroup)
                    && $0.artifact.ocrTexts.contains("57張照片")
            } == true
            let freshCapture = verified.map { captured in
                captured.artifact.epoch > (located?.artifact.epoch ?? 0) && captured.retainedFrameVerified
            } == true
            let ok = textsOK && freshCapture
            let detail = "detailOcr=\(textsOK ? "group+57張照片" : "missing") "
                + "epoch=\(verified?.artifact.epoch ?? 0) afterLocated=\(located?.artifact.epoch ?? 0) "
                + "retainedFrame=\(verified?.retainedFrameDetail ?? "artifact-missing")"
            conditions.append(PhaseACondition(
                identifier: "ALBUM_REVERIFICATION",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [verified?.artifactName].compactMap { $0 }
            ))
        }

        // 9. Ellipsis and the full five-row Save All menu localization.
        do {
            let reference = StructuralLocators.lineAlbumMenuReference
            let ellipsis = latest[ExecutionState.ellipsisLocated.rawValue]
            let menu = latest[ExecutionState.menuVerified.rawValue]
            let ellipsisOK = ellipsis?.artifact.candidateRefusal == nil
                && ellipsis?.artifact.candidateIdentity == "album-ellipsis"
            let observedRows = reference.filter { menu?.artifact.ocrTexts.contains($0) == true }
            let menuOK = reference.count == 5 && observedRows.count == reference.count
                && (menu?.artifact.epoch ?? 0) > (ellipsis?.artifact.epoch ?? 0)
            let ok = ellipsisOK && menuOK
            let detail = "ellipsisCandidate=\(ellipsis?.artifact.candidateIdentity ?? "none") "
                + "rowsObserved=\(observedRows.count)/\(reference.count) [\(observedRows.joined(separator: ","))] "
                + "epochs ellipsis=\(ellipsis?.artifact.epoch ?? 0) menu=\(menu?.artifact.epoch ?? 0)"
            conditions.append(PhaseACondition(
                identifier: "ELLIPSIS_AND_FIVE_ROW_MENU_LOCALIZATION",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [ellipsis?.artifactName, menu?.artifactName].compactMap { $0 }
            ))
        }

        // 10. Popup/occlusion assumptions: the menu popup is the only overlay at
        // SAVE_ALL_LOCATED and the row is localized inside the frozen surface.
        do {
            let saveAll = latest[ExecutionState.saveAllLocated.rawValue]
            let geometry = inputs.frozenGeometry
            let candidateOK = saveAll?.artifact.candidateRefusal == nil
                && saveAll?.artifact.candidateIdentity == "儲存全部"
            let boundsOK = geometry.map {
                $0.menuBoundsCapture.width > 0 && $0.menuBoundsCapture.height > 0
                    && $0.addressableBoundsCapture.width > 0 && $0.addressableBoundsCapture.height > 0
            } == true
            let frameOK = saveAll?.retainedFrameVerified == true
            let ok = candidateOK && boundsOK && frameOK
            let detail = "assumptions: the ellipsis popup is the only new surface at SAVE_ALL_LOCATED; "
                + "capture ignores shadows and child windows; the Save All row stays inside the frozen menu surface bounds; "
                + "saveAllCandidate=\(saveAll?.artifact.candidateIdentity ?? "none") frozenBounds=\(boundsOK) retainedFrame=\(saveAll?.retainedFrameDetail ?? "artifact-missing")"
            conditions.append(PhaseACondition(
                identifier: "POPUP_OCCLUSION_ASSUMPTIONS",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [saveAll?.artifactName].compactMap { $0 }
            ))
        }

        // 11. Pre-panel census: a non-empty inventory captured while no chooser
        // panel exists yet.
        if let census = inputs.prePanelCensus {
            let panelService = census.processes.first {
                ($0.bundleID ?? "").localizedCaseInsensitiveContains("openAndSavePanel")
            }
            let ok = !census.isEmpty && panelService == nil
            let detail = "windowIDs=\(census.windowIDs.count) processes=\(census.processes.count) "
                + "panelServicePresent=\(panelService != nil) recordedAt=\(census.recordedAtMonotonicNanos)"
            conditions.append(PhaseACondition(
                identifier: "PRE_PANEL_CENSUS",
                status: ok ? .pass : .fail,
                detail: detail,
                artifacts: [inputs.prePanelCensusArtifactName].compactMap { $0 }
            ))
        } else {
            conditions.append(PhaseACondition(
                identifier: "PRE_PANEL_CENSUS",
                status: .fail,
                detail: "pre-panel census unavailable: \(inputs.prePanelCensusError ?? "not run")"
            ))
        }

        // 12. Baseline integrity against the accepted reference.
        do {
            let authorization = inputs.authorization
            if let baseline = inputs.baselineResult {
                let ok = baseline.nameInclusiveTripwireSHA256 == authorization.baselineTripwireSHA256
                    && baseline.contentMultisetSHA256 == authorization.expectedContentMultisetSHA256
                    && baseline.fileCount == authorization.expectedFileCount
                    && baseline.totalBytes == authorization.expectedTotalBytes
                let detail = "files=\(baseline.fileCount)/\(authorization.expectedFileCount) "
                    + "bytes=\(baseline.totalBytes)/\(authorization.expectedTotalBytes) "
                    + "multiset=\(baseline.contentMultisetSHA256) tripwire=\(baseline.nameInclusiveTripwireSHA256) match=\(ok)"
                conditions.append(PhaseACondition(
                    identifier: "BASELINE_INTEGRITY",
                    status: ok ? .pass : .fail,
                    detail: detail
                ))
            } else {
                conditions.append(PhaseACondition(
                    identifier: "BASELINE_INTEGRITY",
                    status: .fail,
                    detail: "baseline verification unavailable: \(inputs.baselineError ?? "not run")"
                ))
            }
        }

        // 13. Empty unique staging, separated from evidence.
        do {
            let authorization = inputs.authorization
            let stagingPath = URL(fileURLWithPath: authorization.stagingRunDirectory).standardizedFileURL.path
            let evidencePath = URL(fileURLWithPath: authorization.evidenceRunDirectory).standardizedFileURL.path
            let rootPath = URL(fileURLWithPath: authorization.stagingRoot).standardizedFileURL.path
            if let snapshot = inputs.stagingSnapshot {
                let empty = snapshot.files.isEmpty && snapshot.subdirectories.isEmpty
                    && snapshot.symlinks.isEmpty && snapshot.otherEntries.isEmpty
                let underRoot = stagingPath == rootPath || stagingPath.hasPrefix(rootPath + "/")
                let disjoint = stagingPath != evidencePath
                    && !stagingPath.hasPrefix(evidencePath + "/")
                    && !evidencePath.hasPrefix(stagingPath + "/")
                let ok = empty && underRoot && disjoint
                let detail = "staging=\(stagingPath) evidence=\(evidencePath) files=\(snapshot.files.count) "
                    + "subdirs=\(snapshot.subdirectories.count) symlinks=\(snapshot.symlinks.count) "
                    + "other=\(snapshot.otherEntries.count) underStagingRoot=\(underRoot) disjoint=\(disjoint)"
                conditions.append(PhaseACondition(
                    identifier: "STAGING_EVIDENCE_SEPARATION",
                    status: ok ? .pass : .fail,
                    detail: detail
                ))
            } else {
                conditions.append(PhaseACondition(
                    identifier: "STAGING_EVIDENCE_SEPARATION",
                    status: .fail,
                    detail: "staging snapshot unavailable: \(inputs.stagingError ?? "not run")"
                ))
            }
        }

        // 14. Native tripwire readiness at publication time.
        if let tripwire = inputs.tripwire {
            let detail = "running=\(tripwire.running) failure=\(tripwire.failure ?? "none") "
                + "collectionGap=\(tripwire.collectionGap ?? "none") "
                + "startedAtMonotonicNanos=\(tripwire.startedAtMonotonicNanos) facts=\(tripwire.factCount)"
            conditions.append(PhaseACondition(
                identifier: "NATIVE_TRIPWIRE_READINESS",
                status: tripwire.isArmed ? .pass : .fail,
                detail: detail
            ))
        } else {
            conditions.append(PhaseACondition(
                identifier: "NATIVE_TRIPWIRE_READINESS",
                status: .fail,
                detail: "tripwire readiness unavailable: \(inputs.tripwireError ?? "not run")"
            ))
        }

        // 15. ≥10 s gap-free pre-dispatch context, bound to its raw artifact.
        do {
            if let digest = inputs.preDispatchContextSHA256,
               let context = inspection.preDispatchContexts.first(where: { $0.artifactSHA256 == digest }) {
                let ok = context.isClean
                let detail = "observedSeconds=\(context.observedSeconds) minimumSeconds=\(context.effectiveMinimumSeconds) "
                    + "collectionGap=\(context.collectionGap ?? "none") facts=\(context.factCount) "
                    + "artifactSHA256=\(context.artifactSHA256)"
                conditions.append(PhaseACondition(
                    identifier: "PRE_DISPATCH_CONTEXT_10S",
                    status: ok ? .pass : .fail,
                    detail: detail,
                    artifacts: [context.artifactName]
                ))
            } else {
                conditions.append(PhaseACondition(
                    identifier: "PRE_DISPATCH_CONTEXT_10S",
                    status: .fail,
                    detail: inputs.preDispatchContextSHA256 == nil
                        ? "no recorded pre-dispatch context digest"
                        : "no raw pre-dispatch context artifact matches the recorded digest"
                ))
            }
        }

        // 16. Ledger-proven zero irreversible counters.
        do {
            let counts = inputs.ledgerCounts
            let detail = "ledger intent.saveAll=\(counts.saveAllIntent) attempt.saveAll=\(counts.saveAllAttempt) "
                + "intent.destinationConfirmation=\(counts.destinationIntent) "
                + "attempt.destinationConfirmation=\(counts.destinationAttempt) "
                + "owner saveAll=\(counts.ownerSaveAllCount) destination=\(counts.ownerDestinationCount) "
                + "reversibleDispatches=\(inputs.reversibleDispatches)"
            conditions.append(PhaseACondition(
                identifier: "LEDGER_ZERO_IRREVERSIBLE",
                status: counts.isZero ? .pass : .fail,
                detail: detail,
                artifacts: [inputs.preflightOutcomeArtifactName].compactMap { $0 }
            ))
        }

        let prevented = conditions.filter { $0.status != .pass }.map(\.identifier)
        let irreversible = PhaseAIrreversibleFacts(
            saveAllIntent: inputs.ledgerCounts.saveAllIntent,
            saveAllAttempt: inputs.ledgerCounts.saveAllAttempt,
            destinationIntent: inputs.ledgerCounts.destinationIntent,
            destinationAttempt: inputs.ledgerCounts.destinationAttempt,
            ownerSaveAllCount: inputs.ledgerCounts.ownerSaveAllCount,
            ownerDestinationCount: inputs.ledgerCounts.ownerDestinationCount,
            reversibleDispatches: inputs.reversibleDispatches
        )
        let gates = [
            PhaseADeferredRuntimeGate(
                identifier: "ACTUAL_LINE_CHOOSER_OBSERVED",
                status: .unknown,
                runtimeGate: "PHASE_B",
                statement: "actual LINE chooser not yet observed; chooser predicate/observer verification is a Phase B runtime gate, not a Phase A PASS"
            ),
        ]
        return PhaseAEvidenceReport(
            reportVersion: PhaseAEvidenceReport.currentVersion,
            runID: inputs.authorization.runID,
            generatedAtISO8601: generatedAtISO8601,
            conditions: conditions,
            deferredRuntimeGates: gates,
            irreversible: irreversible,
            ledgerProvenZeroIrreversible: irreversible.isZeroIrreversible,
            phaseBPreventedBy: prevented,
            chooserAssumptionStatement: Self.chooserAssumptionStatement,
            preflightOutcomeArtifactName: inputs.preflightOutcomeArtifactName,
            rawEvidenceManifestName: PhaseAEvidencePublisher.manifestFileName
        )
    }
}

// MARK: - Publisher

public enum PhaseAEvidencePublisher {
    public static let reportFileName = "phase-a.json"
    public static let manifestFileName = "phase-a-manifest.json"

    /// Phase A evidence is append-only per run directory: an existing
    /// `phase-a.json` means this directory already carries a published Phase A,
    /// and a fresh Phase A needs a fresh run/evidence directory.
    public static func isPublished(runDirectory: URL) -> Bool {
        FileManager.default.fileExists(
            atPath: runDirectory.appendingPathComponent(reportFileName).path
        )
    }

    @discardableResult
    public static func publish(
        report: PhaseAEvidenceReport,
        runDirectory: URL,
        generatedAtISO8601: String = EvidenceIO.iso8601()
    ) throws -> PhaseAPublishedArtifacts {
        let reportSHA256 = try EvidenceIO.writeJSONAtomically(
            report,
            to: runDirectory.appendingPathComponent(reportFileName)
        )
        let manifest = PhaseARawEvidenceManifest(
            manifestVersion: 1,
            runID: report.runID,
            generatedAtISO8601: generatedAtISO8601,
            entries: try manifestEntries(runDirectory: runDirectory)
        )
        let manifestSHA256 = try EvidenceIO.writeJSONAtomically(
            manifest,
            to: runDirectory.appendingPathComponent(manifestFileName)
        )
        let counts = report.statusCounts
        return PhaseAPublishedArtifacts(
            reportName: reportFileName,
            reportSHA256: reportSHA256,
            manifestName: manifestFileName,
            manifestSHA256: manifestSHA256,
            manifestEntryCount: manifest.entries.count,
            phaseBPreventedBy: report.phaseBPreventedBy,
            passCount: counts.pass,
            failCount: counts.fail,
            unknownCount: counts.unknown
        )
    }

    public static func manifestEntries(runDirectory: URL) throws -> [PhaseARawEvidenceManifest.Entry] {
        let urls = try FileManager.default.contentsOfDirectory(
            at: runDirectory,
            includingPropertiesForKeys: [.isRegularFileKey, .fileSizeKey],
            options: []
        )
        var entries: [PhaseARawEvidenceManifest.Entry] = []
        for url in urls.sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
            let name = url.lastPathComponent
            if name == manifestFileName || name.hasPrefix(".tmp-") { continue }
            let values = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
            guard values.isRegularFile == true else { continue }
            entries.append(PhaseARawEvidenceManifest.Entry(
                name: name,
                bytes: values.fileSize ?? 0,
                sha256: try EvidenceIO.sha256Hex(ofFileAt: url)
            ))
        }
        return entries
    }
}
